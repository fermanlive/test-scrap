"""
Gestor de colas para las tareas de scraping usando RabbitMQ.
"""

import json
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
import pika
from loguru import logger

from models import ScrapingTask, ScrapingStatus, ScrapingResult


class RabbitMQManager:
    """Gestor de colas para tareas de scraping usando RabbitMQ."""
    
    def __init__(self, rabbitmq_config: Dict[str, Any]):
        """
        Inicializar el gestor de colas.
        
        Args:
            rabbitmq_config: Configuración de RabbitMQ
        """
        self.config = rabbitmq_config
        self.connection = None
        self.channel = None
        
        # Nombres de colas y exchanges
        self.tasks_queue = self.config.get("queue", "scraping_queue")
        self.results_queue = "scraping_results"
        self.failed_queue = "scraping_failed"
        self.exchange = self.config.get("exchange", "scraping_exchange")
        
        # Flag para indicar si estamos conectados
        self.connected = False
        
        # Conectar a RabbitMQ
        self._connect()
    
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
                exchange=self.exchange,
                exchange_type='direct',
                durable=True
            )
            
            # Declarar colas
            self._declare_queues()
            
            logger.info("✅ Conectado a RabbitMQ")
            self.connected = True
            
        except Exception as e:
            logger.error(f"❌ Error al conectar a RabbitMQ: {e}")
            raise
    
    def _declare_queues(self):
        """Declarar las colas necesarias."""
        try:
            # Cola principal de tareas (usar passive=True para colas existentes)
            try:
                self.channel.queue_declare(
                    queue=self.tasks_queue,
                    passive=True
                )
                logger.info(f"✅ Cola existente encontrada: {self.tasks_queue}")
            except Exception:
                # Si no existe, declarar con argumentos
                self.channel.queue_declare(
                    queue=self.tasks_queue,
                    durable=True,
                    arguments={
                        'x-message-ttl': 24 * 60 * 60 * 1000,  # 24 horas en ms
                        'x-max-length': 1000
                    }
                )
                logger.info(f"✅ Nueva cola creada: {self.tasks_queue}")
            
            # Cola de resultados
            try:
                self.channel.queue_declare(
                    queue=self.results_queue,
                    passive=True
                )
                logger.info(f"✅ Cola existente encontrada: {self.results_queue}")
            except Exception:
                # Si no existe, declarar con argumentos
                self.channel.queue_declare(
                    queue=self.results_queue,
                    durable=True,
                    arguments={
                        'x-message-ttl': 7 * 24 * 60 * 60 * 1000,  # 7 días en ms
                        'x-max-length': 1000
                    }
                )
                logger.info(f"✅ Nueva cola creada: {self.results_queue}")
            
            # Cola de tareas fallidas
            try:
                self.channel.queue_declare(
                    queue=self.failed_queue,
                    passive=True
                )
                logger.info(f"✅ Cola existente encontrada: {self.failed_queue}")
            except Exception:
                # Si no existe, declarar con argumentos
                self.channel.queue_declare(
                    queue=self.failed_queue,
                    durable=True,
                    arguments={
                        'x-message-ttl': 7 * 24 * 60 * 60 * 1000,  # 7 días en ms
                        'x-max-length': 1000
                    }
                )
                logger.info(f"✅ Nueva cola creada: {self.failed_queue}")
            
            # Binding de colas al exchange
            self.channel.queue_bind(
                exchange=self.exchange,
                queue=self.tasks_queue,
                routing_key=self.config.get("routing_key", "scraping")
            )
            
            self.channel.queue_bind(
                exchange=self.exchange,
                queue=self.results_queue,
                routing_key='result'
            )
            
            self.channel.queue_bind(
                exchange=self.exchange,
                queue=self.failed_queue,
                routing_key='failed'
            )
            
            logger.info("✅ Colas declaradas en RabbitMQ")
            
        except Exception as e:
            logger.error(f"❌ Error al declarar colas: {e}")
            raise
    
    async def add_task(self, task: ScrapingTask) -> bool:
        """
        Agregar una nueva tarea a la cola.
        
        Args:
            task: Tarea de scraping a agregar
            
        Returns:
            True si se agregó correctamente
        """
        try:
            # Convertir tarea a JSON
            task_data = task.dict()
            
            # Publicar mensaje en la cola de tareas
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=self.config.get("routing_key", "scraping"),
                body=json.dumps(task_data, default=str),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistente
                    message_id=task.id,
                    timestamp=int(datetime.utcnow().timestamp()),
                    headers={
                        'task_type': 'scraping',
                        'category': task.request.category,
                        'page': task.request.page
                    }
                )
            )
            
            logger.info(f"✅ Tarea {task.id} agregada a la cola RabbitMQ")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al agregar tarea {task.id}: {e}")
            return False
    
    async def get_task(self, task_id: str) -> Optional[ScrapingTask]:
        """
        Obtener una tarea por su ID.
        
        Args:
            task_id: ID de la tarea
            
        Returns:
            Tarea encontrada o None
        """
        try:
            # Buscar en la cola de resultados
            method_frame, header_frame, body = self.channel.basic_get(
                queue=self.results_queue,
                auto_ack=False
            )
            
            if method_frame:
                # Procesar mensaje
                task_data = json.loads(body)
                if task_data.get('id') == task_id:
                    self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                    return ScrapingTask(**task_data)
                else:
                    # Reencolar mensaje
                    self.channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=True)
            
            # También buscar en la cola de fallidas
            method_frame, header_frame, body = self.channel.basic_get(
                queue=self.failed_queue,
                auto_ack=False
            )
            
            if method_frame:
                task_data = json.loads(body)
                if task_data.get('id') == task_id:
                    self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                    return ScrapingTask(**task_data)
                else:
                    self.channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=True)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error al obtener tarea {task_id}: {e}")
            return None
    
    async def list_tasks(self, limit: int = 50, offset: int = 0) -> List[ScrapingTask]:
        """
        Listar todas las tareas.
        
        Args:
            limit: Número máximo de tareas a retornar
            offset: Número de tareas a omitir
            
        Returns:
            Lista de tareas
        """
        try:
            tasks = []
            
            # Obtener tareas de la cola de resultados
            for _ in range(limit):
                method_frame, header_frame, body = self.channel.basic_get(
                    queue=self.results_queue,
                    auto_ack=False
                )
                
                if method_frame:
                    try:
                        task_data = json.loads(body)
                        tasks.append(ScrapingTask(**task_data))
                        self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                    except Exception as e:
                        logger.warning(f"Error al parsear tarea: {e}")
                        self.channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=False)
                else:
                    break
            
            # Obtener tareas de la cola de fallidas
            for _ in range(limit - len(tasks)):
                method_frame, header_frame, body = self.channel.basic_get(
                    queue=self.failed_queue,
                    auto_ack=False
                )
                
                if method_frame:
                    try:
                        task_data = json.loads(body)
                        tasks.append(ScrapingTask(**task_data))
                        self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                    except Exception as e:
                        logger.warning(f"Error al parsear tarea fallida: {e}")
                        self.channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=False)
                else:
                    break
            
            # Aplicar offset y limit
            return tasks[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"❌ Error al listar tareas: {e}")
            return []
    
    async def update_task_status(self, task_id: str, status: ScrapingStatus) -> bool:
        """
        Actualizar el estado de una tarea.
        
        Args:
            task_id: ID de la tarea
            status: Nuevo estado
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            # Obtener la tarea actual
            task = await self.get_task(task_id)
            if not task:
                return False
            
            # Actualizar estado
            task.status = status
            
            # Publicar en la cola correspondiente
            if status == ScrapingStatus.COMPLETED:
                routing_key = 'result'
            elif status == ScrapingStatus.FAILED:
                routing_key = 'failed'
            else:
                routing_key = 'task'
            
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=json.dumps(task.dict(), default=str),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    message_id=task.id,
                    timestamp=int(datetime.utcnow().timestamp())
                )
            )
            
            logger.info(f"✅ Estado de tarea {task_id} actualizado a {status}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al actualizar estado de tarea {task_id}: {e}")
            return False
    
    async def update_task_started(self, task_id: str) -> bool:
        """Marcar una tarea como iniciada."""
        return await self.update_task_status(task_id, ScrapingStatus.PROCESSING)
    
    async def update_task_completed(self, task_id: str, result: ScrapingResult) -> bool:
        """Marcar una tarea como completada."""
        try:
            # Obtener la tarea
            task = await self.get_task(task_id)
            if not task:
                return False
            
            # Actualizar con resultado
            task.status = ScrapingStatus.COMPLETED
            task.completed_at = datetime.utcnow().isoformat()
            task.result_file = result.output_file
            
            # Publicar en cola de resultados
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key='result',
                body=json.dumps(task.dict(), default=str),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    message_id=task.id,
                    timestamp=int(datetime.utcnow().timestamp())
                )
            )
            
            logger.info(f"✅ Tarea {task_id} marcada como completada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al marcar tarea {task_id} como completada: {e}")
            return False
    
    async def update_task_failed(self, task_id: str, error_message: str) -> bool:
        """Marcar una tarea como fallida."""
        try:
            # Obtener la tarea
            task = await self.get_task(task_id)
            if not task:
                return False
            
            # Actualizar con error
            task.status = ScrapingStatus.FAILED
            task.completed_at = datetime.utcnow().isoformat()
            task.error_message = error_message
            
            # Publicar en cola de fallidas
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key='failed',
                body=json.dumps(task.dict(), default=str),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    message_id=task.id,
                    timestamp=int(datetime.utcnow().timestamp())
                )
            )
            
            logger.info(f"❌ Tarea {task_id} marcada como fallida: {error_message}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al marcar tarea {task_id} como fallida: {e}")
            return False
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de las colas.
        
        Returns:
            Diccionario con estadísticas
        """
        try:
            # Obtener información de las colas
            tasks_info = self.channel.queue_declare(
                queue=self.tasks_queue,
                passive=True
            )
            
            results_info = self.channel.queue_declare(
                queue=self.results_queue,
                passive=True
            )
            
            failed_info = self.channel.queue_declare(
                queue=self.failed_queue,
                passive=True
            )
            
            return {
                "pending": tasks_info.method.message_count,
                "completed": results_info.method.message_count,
                "failed": failed_info.method.message_count,
                "total": (tasks_info.method.message_count + 
                         results_info.method.message_count + 
                         failed_info.method.message_count)
            }
            
        except Exception as e:
            logger.error(f"❌ Error al obtener estadísticas de las colas: {e}")
            return {"pending": 0, "completed": 0, "failed": 0, "total": 0}
    
    def start_consuming(self, callback):
        """
        Iniciar el consumo de mensajes de la cola de tareas.
        
        Args:
            callback: Función a ejecutar cuando se reciba un mensaje
        """
        try:
            # Configurar QoS
            self.channel.basic_qos(prefetch_count=1)
            
            # Configurar callback para mensajes
            self.channel.basic_consume(
                queue=self.tasks_queue,
                on_message_callback=callback,
                auto_ack=False
            )
            
            logger.info(f"🎧 Iniciando consumo de mensajes de la cola: {self.tasks_queue}")
            
            # Iniciar consumo
            self.channel.start_consuming()
            
        except Exception as e:
            logger.error(f"❌ Error al iniciar consumo de mensajes: {e}")
            raise
    
    def stop_consuming(self):
        """Detener el consumo de mensajes."""
        try:
            if self.channel and self.channel.is_consuming():
                self.channel.stop_consuming()
                logger.info("⏹️ Consumo de mensajes detenido")
        except Exception as e:
            logger.error(f"❌ Error al detener consumo de mensajes: {e}")
    
    def ack_message(self, delivery_tag):
        """Confirmar recepción de un mensaje."""
        try:
            self.channel.basic_ack(delivery_tag=delivery_tag)
        except Exception as e:
            logger.error(f"❌ Error al confirmar mensaje: {e}")
    
    def nack_message(self, delivery_tag, requeue=True):
        """Rechazar un mensaje."""
        try:
            self.channel.basic_nack(delivery_tag=delivery_tag, requeue=requeue)
        except Exception as e:
            logger.error(f"❌ Error al rechazar mensaje: {e}")
    
    def close(self):
        """Cerrar conexión con RabbitMQ."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("🔌 Conexión con RabbitMQ cerrada")
    
    def __del__(self):
        """Destructor para cerrar conexión."""
        self.close()
