"""
API principal para el sistema de scraping de Mercado Libre Uruguay.
"""

import asyncio
import uuid
import threading
import re
from datetime import datetime
from typing import List, Dict, Any
import sys
from pathlib import Path

# Agregar el directorio del proyecto al path para importar el scraper
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from models import (
    ScrapingRequest, ScrapingResponse, ScrapingTask, 
    ScrapingResult, HealthCheck, ScrapingStatus
)
from config import (
    API_CONFIG, SCRAPER_CONFIG, 
    MONITORING_CONFIG, RABBITMQ_CONFIG
)
from manager import RabbitMQManager, cache_manager
from scraper.services import ScraperService

# Configurar logging
logger.add(
    SCRAPER_CONFIG["log_dir"] / "api.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO"
)

# Patrón de validación para categorías de Mercado Libre Uruguay
# Formato: ML + una letra + 3 a 4 números consecutivos (ej: MLU107, MLA1234)
CATEGORY_PATTERN = re.compile(r'^ML[A-Z]\d{3,4}$')

def validate_category(category: str) -> bool:
    """
    Valida que una categoría siga el patrón ML[A-Z][0-9]{3,4}
    
    Args:
        category: Código de categoría a validar
        
    Returns:
        True si la categoría es válida, False en caso contrario
    """
    return bool(CATEGORY_PATTERN.match(category.upper()))

# Crear aplicación FastAPI
app = FastAPI(
    title=API_CONFIG["title"],
    description=API_CONFIG["description"],
    version=API_CONFIG["version"],
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancias globales
queue_manager: RabbitMQManager = None
scraper_service: ScraperService = None
listener_thread: threading.Thread = None
listener_running: bool = False


@app.on_event("startup")
async def startup_event():
    """Inicializar servicios al arrancar la API."""
    global queue_manager, scraper_service, listener_thread
    
    try:
        # Inicializar servicios
        queue_manager = RabbitMQManager(RABBITMQ_CONFIG)
        scraper_service = ScraperService()
        
        # Iniciar listener de mensajes en hilo separado
        listener_thread = threading.Thread(
            target=start_message_listener,
            daemon=True,
            name="MessageListener"
        )
        listener_thread.start()
        
        logger.info("🚀 API iniciada correctamente")
        logger.info("🎧 Listener de mensajes iniciado en background")
        
    except Exception as e:
        logger.error(f"❌ Error al inicializar la API: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cerrar conexiones al apagar la API."""
    global listener_running
    
    # Detener listener
    stop_message_listener()
    
    # Cerrar conexiones
    if queue_manager:
        queue_manager.close()
        logger.info("🔌 Conexiones cerradas")
    
    logger.info("🔌 API cerrada correctamente")


@app.get("/", response_model=Dict[str, str])
async def root():
    """Endpoint raíz de la API."""
    return {
        "message": "Mercado Libre Uruguay Scraping API",
        "version": API_CONFIG["version"],
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Verificar el estado de salud del sistema."""
    try:
        rabbitmq_connected = queue_manager.connected if queue_manager else False
        scraper_available = scraper_service.is_available() if scraper_service else False
        listener_active = listener_running if listener_thread else False
        
        return HealthCheck(
            status="healthy" if rabbitmq_connected and scraper_available and listener_active else "unhealthy",
            timestamp=datetime.utcnow().isoformat(),
            version=API_CONFIG["version"],
            rabbitmq_connected=rabbitmq_connected,
            scraper_available=scraper_available
        )
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return HealthCheck(
            status="unhealthy",
            timestamp=datetime.utcnow().isoformat(),
            version=API_CONFIG["version"],
            rabbitmq_connected=False,
            scraper_available=False
        )


@app.get("/listener/status")
async def get_listener_status():
    """Obtener el estado del listener de mensajes."""
    return {
        "listener_running": listener_running,
        "listener_thread_alive": listener_thread.is_alive() if listener_thread else False,
        "listener_thread_name": listener_thread.name if listener_thread else None,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/scrape", response_model=ScrapingResponse)
async def create_scraping_task(
    request: ScrapingRequest,
    background_tasks: BackgroundTasks
):
    """
    Crear una nueva tarea de scraping.
    
    Args:
        request: Solicitud de scraping con categoría, página y cantidad de productos
        background_tasks: Tareas en background de FastAPI
    
    Returns:
        Respuesta con ID de tarea y estado
    """
    try:
        # Validar categoría usando patrón regex
        if not validate_category(request.category):
            raise HTTPException(
                status_code=400,
                detail=f"Categoría inválida. Debe seguir el patrón ML[A-Z][0-9]{{3,4}} (ej: MLU107, MLA1234)"
            )
        
        # Verificar cache antes de crear nueva tarea
        cached_response = cache_manager.get(request.category, request.page)
        if cached_response:
            logger.info(f"Devolviendo respuesta desde cache para {request.category}:page:{request.page}")
            return cached_response
        
        # Generar URL de Mercado Libre
        url = f"{SCRAPER_CONFIG['base_url']}?category={request.category}&page={request.page}"
        
        # Crear tarea
        task_id = str(uuid.uuid4())
        task = ScrapingTask(
            id=task_id,
            request=request,
            status=ScrapingStatus.PENDING,
            created_at=datetime.now().isoformat()
        )
        
        # Guardar tarea en RabbitMQ
        await queue_manager.add_task(task)
        
        # Agregar tarea de scraping en background
        background_tasks.add_task(
            process_scraping_task,
            task_id,
            request,
            url
        )
        
        logger.info(f"✅ Tarea de scraping creada: {task_id} para {request.category} página {request.page}")
        
        # Crear respuesta y guardar inmediatamente en cache para evitar tareas duplicadas
        pending_response = ScrapingResponse(
            task_id=task_id,
            status=ScrapingStatus.PENDING,
            message="Tarea de scraping creada exitosamente",
            url=url,
            category=request.category,
            page=request.page,
            max_products=request.max_products
        )
        
        # Guardar respuesta PENDING en cache para evitar duplicados
        cache_manager.set(request.category, request.page, pending_response)
        logger.info(f"📦 Respuesta PENDING guardada en cache para {request.category}:page:{request.page}")
        
        return pending_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear tarea de scraping: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@app.get("/tasks/{task_id}", response_model=ScrapingTask)
async def get_task_status(task_id: str):
    """
    Obtener el estado de una tarea de scraping.
    
    Args:
        task_id: ID de la tarea
    
    Returns:
        Estado actual de la tarea
    """
    try:
        task = await queue_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener estado de tarea {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@app.get("/tasks", response_model=List[ScrapingTask])
async def list_tasks(limit: int = 50, offset: int = 0):
    """
    Listar todas las tareas de scraping.
    
    Args:
        limit: Número máximo de tareas a retornar
        offset: Número de tareas a omitir
    
    Returns:
        Lista de tareas
    """
    try:
        tasks = await queue_manager.list_tasks(limit=limit, offset=offset)
        return tasks
        
    except Exception as e:
        logger.error(f"Error al listar tareas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@app.get("/categories")
async def get_categories():
    """
    Obtener información sobre el patrón de categorías válidas.
    
    Returns:
        Información sobre el formato de categorías aceptadas
    """
    return {
        "pattern": "ML[A-Z][0-9]{3,4}",
        "description": "Categorías de Mercado Libre con formato ML + letra + 3-4 números",
        "examples": ["MLU107", "MLA1234", "MLC456", "MLB7890"],
        "regex": CATEGORY_PATTERN.pattern
    }


@app.get("/cache/stats")
async def get_cache_stats():
    """
    Obtener estadísticas del cache en memoria.
    
    Returns:
        Estadísticas del cache
    """
    try:
        stats = cache_manager.get_stats()
        return {
            "cache_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error al obtener estadísticas del cache: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@app.get("/cache/keys")
async def get_cache_keys():
    """
    Listar todas las claves activas en el cache.
    
    Returns:
        Lista de claves en el cache
    """
    try:
        keys = cache_manager.list_keys()
        return {
            "active_keys": keys,
            "total_count": len(keys),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error al listar claves del cache: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

async def process_scraping_task(task_id: str, request: ScrapingRequest, url: str):
    """
    Procesar una tarea de scraping en background.
    
    Args:
        task_id: ID de la tarea
        request: Solicitud de scraping
        url: URL a procesar
    """
    try:
        # Actualizar estado a procesando
        await queue_manager.update_task_status(task_id, ScrapingStatus.PROCESSING)
        await queue_manager.update_task_started(task_id)
        
        logger.info(f"🚀 Iniciando scraping para tarea {task_id}: {url}")
        
        # Ejecutar scraping
        result = await scraper_service.scrape_products(
            url=url,
            max_products=request.max_products
        )
        
        # Actualizar estado a completado
        await queue_manager.update_task_completed(task_id, result)
        
        # Actualizar cache con respuesta exitosa
        completed_response = ScrapingResponse(
            task_id=task_id,
            status=ScrapingStatus.COMPLETED,
            message=f"Scraping completado exitosamente. {result.products_count} productos encontrados",
            url=url,
            category=request.category,
            page=request.page,
            max_products=request.max_products
        )
        
        # Actualizar entrada en cache de PENDING a COMPLETED
        cache_manager.set(request.category, request.page, completed_response)
        
        logger.info(f"✅ Scraping completado para tarea {task_id}: {result.products_count} productos. Cache actualizado a COMPLETED")
        
    except Exception as e:
        logger.error(f"❌ Error en scraping para tarea {task_id}: {e}")
        
        # Invalidar cache en caso de fallo para permitir reintentos
        cache_manager.invalidate(request.category, request.page)
        logger.info(f"🗑️ Cache invalidado para {request.category}:page:{request.page} debido a fallo")
        
        # Actualizar estado a fallido
        await queue_manager.update_task_failed(task_id, str(e))


def start_message_listener():
    """Iniciar el listener de mensajes en un hilo separado."""
    global listener_running
    
    try:
        logger.info("🎧 Iniciando listener de mensajes...")
        
        # Crear instancia del listener
        from manager.listeners import MessageListener
        listener = MessageListener()
        
        listener_running = True
        
        # Iniciar escucha (esto bloqueará el hilo)
        listener.start_listening()
        
    except Exception as e:
        logger.error(f"❌ Error en listener: {e}")
        listener_running = False


def stop_message_listener():
    """Detener el listener de mensajes."""
    global listener_running
    listener_running = False
    logger.info("⏹️ Listener de mensajes detenido")


def start_api():
    """Función para iniciar la API desde Poetry."""
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=API_CONFIG["host"],
        port=API_CONFIG["port"],
        reload=API_CONFIG["debug"],
        log_level="info"
    )


if __name__ == "__main__":
    start_api()
