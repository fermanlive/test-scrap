"""
Listener de mensajes para RabbitMQ que procesa tareas de scraping.
"""

import json
import sys
from datetime import datetime
from typing import Dict, Any
import pika
from loguru import logger

from models import ScrapingTask, ScrapingStatus, ScrapingResponse
from scraper.services import ScraperService
from config import RABBITMQ_CONFIG
from scraper.simple_scraper import run_main
from scraper.models.models import Product
from typing import List
from database.connectors import DatabaseConnector
from manager.cache_manager import cache_manager

class MessageListener:
    """Listener de mensajes de RabbitMQ para tareas de scraping."""
    
    def __init__(self):
        """Inicializar el listener."""
        self.connection = None
        self.channel = None
        self.scraper_service = ScraperService()
        self.running = False
        
        # Configuración de RabbitMQ
        self.config = RABBITMQ_CONFIG
        self.queue_name = self.config["queue"]
        self.exchange_name = self.config["exchange"]
        self.routing_key = self.config["routing_key"]
        self.database_connector = DatabaseConnector()
        
        logger.info(f"🎧 Inicializando listener para cola: {self.queue_name}")
    
    def _connect(self):
        """Establecer conexión con RabbitMQ."""
        try:
            # Crear conexión
            credentials = pika.PlainCredentials(
                self.config["user"], 
                self.config["password"]
            )
            
            parameters = pika.ConnectionParameters(
                host=self.config["host"],
                port=self.config["port"],
                virtual_host=self.config["vhost"],
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declarar exchange
            self.channel.exchange_declare(
                exchange=self.exchange_name,
                exchange_type='direct',
                durable=True
            )
            
            # Declarar cola (usar passive=True para colas existentes)
            try:
                self.channel.queue_declare(
                    queue=self.queue_name,
                    passive=True
                )
                logger.info(f"✅ Cola existente encontrada: {self.queue_name}")
            except Exception:
                # Si no existe, declarar con argumentos
                self.channel.queue_declare(
                    queue=self.queue_name,
                    durable=True,
                    arguments={
                        'x-message-ttl': 24 * 60 * 60 * 1000,  # 24 horas en ms
                        'x-max-length': 1000
                    }
                )
                logger.info(f"✅ Nueva cola creada: {self.queue_name}")
            
            # Binding de cola al exchange
            self.channel.queue_bind(
                exchange=self.exchange_name,
                queue=self.queue_name,
                routing_key=self.routing_key
            )
            
            # Configurar QoS
            self.channel.basic_qos(prefetch_count=1)
            
            logger.info("✅ Conectado a RabbitMQ")
            
        except Exception as e:
            logger.error(f"❌ Error al conectar a RabbitMQ: {e}")
            raise
    
    def _process_message(self, ch, method, properties, body):
        """
        Procesar un mensaje recibido.
        
        Args:
            ch: Canal de RabbitMQ
            method: Método de entrega
            properties: Propiedades del mensaje
            body: Cuerpo del mensaje
        """
        try:
            logger.info(f"Mensaje recibido: {properties.message_id if hasattr(properties, 'message_id') else 'N/A'}")
            
            # Parsear mensaje
            message_data = json.loads(body)
            logger.info(f"Contenido del mensaje: {message_data}")
            
            # Adaptar formato del mensaje según su estructura
            adapted_message = self._adapt_message_format(message_data)
            
            # Crear tarea
            task = ScrapingTask(**adapted_message)
            logger.info(f"Task {task.id} - Procesando tarea: {task.id}")
            
            # Verificar cache antes de procesar
            category = task.request.category
            page = task.request.page
            
            cached_response = cache_manager.get(category, page)
            if cached_response:
                logger.info(f"Task {task.id} - ⚡ Cache HIT para {category}:page:{page}. Omitiendo procesamiento")
                # Confirmar mensaje ya que está en cache
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.info(f"Task {task.id} - Mensaje confirmado (desde cache)")
                return
            
            logger.info(f"Task {task.id} - 🔍 Cache MISS para {category}:page:{page}. Procediendo con scraping")
            
            # Procesar tarea de forma síncrona (pika no es async)
            self._process_task_sync(task)
            
            # Confirmar recepción del mensaje
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
            logger.info(f"Task {task.id} - Mensaje confirmado")
            
        except Exception as e:
            logger.error(f"Task {task.id} - Error al procesar mensaje: {e}")
            
            # Rechazar mensaje y reencolarlo
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            logger.error(f"Task {task.id} - Mensaje reencolado")
    
    def _adapt_message_format(self, message_data: dict) -> dict:
        """
        Adaptar el formato del mensaje para que sea compatible con ScrapingTask.
        
        Args:
            message_data: Mensaje original
            
        Returns:
            Mensaje adaptado
        """
        # Si el mensaje ya tiene el formato correcto, retornarlo tal como está
        if all(key in message_data for key in ['id', 'request', 'status', 'created_at']):
            return message_data
        
        # Si es un mensaje del publisher (formato antiguo), adaptarlo
        if 'url' in message_data and 'category' in message_data:
            logger.info("🔄 Adaptando formato de mensaje del publisher")
            
            # Generar ID único si no existe
            task_id = message_data.get('id', f"auto-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
            
            # Crear estructura de request
            request_data = {
                "url": message_data.get('url', ''),
                "category": message_data.get('category', ''),
                "page": message_data.get('page', 1),
                "max_products": message_data.get('metadata', {}).get('max_products', 50)
            }
            
            # Crear mensaje adaptado
            adapted_message = {
                "id": task_id,
                "request": request_data,
                "status": ScrapingStatus.PENDING,
                "created_at": message_data.get('timestamp', datetime.now().isoformat())
            }
            
            logger.info(f"✅ Mensaje adaptado: {adapted_message}")
            return adapted_message
        
        # Si no se puede adaptar, lanzar error
        raise ValueError(f"Formato de mensaje no reconocido: {message_data}")
    
    def _process_task_sync(self, task: ScrapingTask):
        """
        Procesar una tarea de scraping de forma síncrona.
        
        Args:
            task: Tarea a procesar
        """
        try:
            logger.info(f"🚀 Iniciando procesamiento de tarea: {task.id}")
            
            # Verificar si el scraper está disponible
            if not self.scraper_service.is_available():
                raise RuntimeError("Scraper no disponible")
            
            # Por ahora solo loguear la tarea
            logger.info(f"Tarea recibida: ID={task.id}, URL={task.request.url}, Max Products={task.request.max_products}")
            
            list_products = run_main(   
                url=task.request.url,
                max_products=task.request.max_products,
                task_id=task.id,
                category=task.request.category,
                page=task.request.page
            )

            success = self._save_products(list_products, task_id = task.id)
            
            if success:
                # Guardar respuesta exitosa en cache
                completed_response = ScrapingResponse(
                    task_id=task.id,
                    status=ScrapingStatus.COMPLETED,
                    message=f"Scraping completado exitosamente por MessageListener. {len(list_products)} productos encontrados",
                    url=task.request.url,
                    category=task.request.category,
                    page=task.request.page,
                    max_products=task.request.max_products
                )
                
                cache_manager.set(task.request.category, task.request.page, completed_response)
                logger.info(f"Task {task.id} - 📦 Cache actualizado a COMPLETED para {task.request.category}:page:{task.request.page}")

        except Exception as e:
            logger.error(f"Task {task.id} - Error en tarea: {e}")
            
            # Invalidar cache en caso de fallo para permitir reintentos
            cache_manager.invalidate(task.request.category, task.request.page)
            logger.info(f"Task {task.id} - 🗑️ Cache invalidado para {task.request.category}:page:{task.request.page} debido a fallo")
    
    def _save_products(self, products: List[Product], task_id: str):
        """Guardar productos en la base de datos."""
        logger.info(f"Task {task_id} - Guardando productos en la base de datos: {len(products)}")
        try:
            self.database_connector.insert_products(products)
        except Exception as e:
            logger.error(f"Task {task_id} - Error al insertar {len(products)} productos en la base de datos: {e}")
            return False
        logger.info(f"Task {task_id} - Productos guardados en la base de datos: {len(products)}")
        return True
    
    def start_listening(self):
        """Iniciar la escucha de mensajes."""
        try:
            self._connect()
            
            # Configurar callback para mensajes
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self._process_message,
                auto_ack=False
            )
            
            logger.info(f"🎧 Iniciando escucha de mensajes en cola: {self.queue_name}")
            self.running = True
            
            # Iniciar consumo
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("⏹️ Interrupción del usuario, deteniendo listener...")
            self.stop_listening()
        except Exception as e:
            logger.error(f"❌ Error en listener: {e}")
            self.stop_listening()
    
    def stop_listening(self):
        """Detener la escucha de mensajes."""
        try:
            self.running = False
            
            if self.channel and self.channel.is_consuming():
                self.channel.stop_consuming()
                logger.info("⏹️ Escucha de mensajes detenida")
            
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("🔌 Conexión con RabbitMQ cerrada")
                
        except Exception as e:
            logger.error(f"❌ Error al detener listener: {e}")


def main():
    """Función principal para ejecutar el listener."""
    listener = MessageListener()
    
    try:
        listener.start_listening()
    except Exception as e:
        logger.error(f"❌ Error fatal en listener: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
