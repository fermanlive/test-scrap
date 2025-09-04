from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import pika
import json
import os
from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel

from config import Config
from models import (
    ScrapingRequest, 
    ScrapingResponse, 
    HealthResponse, 
    ErrorResponse,
    PriorityLevel
)

app = FastAPI(
    title=Config.APP_NAME,
    version=Config.APP_VERSION,
    description="Servicio publisher para scraping con RabbitMQ"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de RabbitMQ (mantener para compatibilidad)
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "admin123")



def get_rabbitmq_connection():
    """Obtener conexión a RabbitMQ"""
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials
            )
        )
        return connection
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de conexión a RabbitMQ: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Configurar RabbitMQ al iniciar"""
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # Declarar cola para scraping con prioridades
        channel.queue_declare(
            queue=Config.SCRAPING_QUEUE, 
            durable=True,
            arguments={'x-max-priority': 10}
        )
        
        # Declarar exchange
        channel.exchange_declare(
            exchange=Config.SCRAPING_EXCHANGE,
            exchange_type='direct',
            durable=True
        )
        
        # Vincular cola con exchange
        channel.queue_bind(
            exchange=Config.SCRAPING_EXCHANGE,
            queue=Config.SCRAPING_QUEUE,
            routing_key=Config.SCRAPING_ROUTING_KEY
        )
        
        connection.close()
        print(f"RabbitMQ configurado correctamente: {Config.SCRAPING_EXCHANGE} -> {Config.SCRAPING_QUEUE}")
    except Exception as e:
        print(f"Error en startup: {e}")

@app.post("/publish", response_model=ScrapingResponse)
async def publish_scraping_request(request: ScrapingRequest):
    """Publicar solicitud de scraping en la cola"""
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # Mapear prioridad a valor numérico para RabbitMQ
        priority_map = {
            PriorityLevel.LOW: 1,
            PriorityLevel.NORMAL: 5,
            PriorityLevel.HIGH: 8,
            PriorityLevel.URGENT: 10
        }

        target_url = ""

        # setting the url
        if request.category:
            target_url = f"{request.url}?category={request.category}"
            if request.page:
                target_url += f"&page={request.page}"
        else:
            target_url = request.url
        
        # Preparar mensaje
        message = {
            "url": target_url,
            "category": request.category,
            "page": request.page,
            "priority": priority_map.get(request.priority, 5),
            "metadata": request.metadata,
            "timestamp": datetime.now().isoformat()
        }
        
        # setting properties
        properties = pika.BasicProperties(
            app_id="scraping_publisher",
            delivery_mode=2,  # Persistente
            priority=priority_map.get(request.priority, 5)
        )
        
        # Publicar mensaje
        result = channel.basic_publish(
            exchange=Config.SCRAPING_EXCHANGE,
            routing_key=Config.SCRAPING_ROUTING_KEY,
            body=json.dumps(message),
            properties=properties
        )

        connection.close()
        
        

        # Verificar si el mensaje se publicó correctamente
        # basic_publish puede devolver None en algunos casos, pero eso no significa error
        # Verificamos que no haya excepciones en su lugar
        
        return ScrapingResponse(
            message_id=f"msg_{hash(request.url)}",
            status="published",
            url=request.url,
            page=request.page,
            category=request.category,
            timestamp=message["timestamp"],
            priority=request.priority
        )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/health")
async def health_check():
    """Verificar estado del servicio"""
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # Verificar que la cola existe y obtener información
        queue_info = channel.queue_declare(
            queue=Config.SCRAPING_QUEUE, 
            passive=True,
            durable=True
        )
        
        # Verificar que el exchange existe
        channel.exchange_declare(
            exchange=Config.SCRAPING_EXCHANGE,
            exchange_type='direct',
            passive=True
        )
        
        connection.close()
        
        return {
            "status": "healthy", 
            "rabbitmq": "connected",
            "queue": Config.SCRAPING_QUEUE,
            "exchange": Config.SCRAPING_EXCHANGE,
            "routing_key": Config.SCRAPING_ROUTING_KEY,
            "queue_messages": queue_info.method.message_count
        }
    except Exception as e:
        return {"status": "unhealthy", "rabbitmq": "disconnected", "error": str(e)}

@app.get("/diagnose")
async def diagnose_rabbitmq():
    """Diagnóstico detallado de RabbitMQ"""
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # Verificar cola
        queue_info = channel.queue_declare(
            queue=Config.SCRAPING_QUEUE, 
            passive=True,
            durable=True
        )
        
        # Verificar exchange
        channel.exchange_declare(
            exchange=Config.SCRAPING_EXCHANGE,
            exchange_type='direct',
            passive=True
        )
        
        # Verificar bindings
        bindings = channel.queue_bind(
            exchange=Config.SCRAPING_EXCHANGE,
            queue=Config.SCRAPING_QUEUE,
            routing_key=Config.SCRAPING_ROUTING_KEY,
            passive=True
        )
        
        connection.close()
        
        return {
            "status": "ok",
            "queue": {
                "name": Config.SCRAPING_QUEUE,
                "exists": True,
                "durable": True,
                "messages": queue_info.method.message_count,
                "consumers": queue_info.method.consumer_count
            },
            "exchange": {
                "name": Config.SCRAPING_EXCHANGE,
                "exists": True,
                "type": "direct"
            },
            "binding": {
                "exchange": Config.SCRAPING_EXCHANGE,
                "queue": Config.SCRAPING_QUEUE,
                "routing_key": Config.SCRAPING_ROUTING_KEY,
                "exists": True
            }
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "service": "Publisher Service",
        "version": "1.0.0",
        "endpoints": {
            "publish": "/publish",
            "health": "/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
