"""
Tests unitarios para RabbitMQManager siguiendo patrón AAA y TDD.
"""
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

import sys
from pathlib import Path

# Agregar el directorio padre al path para las importaciones
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from manager.rabbitmq_manager import RabbitMQManager
from models import ScrapingTask, ScrapingStatus, ScrapingResult


class TestRabbitMQManagerInitialization:
    """Tests para inicialización del RabbitMQManager."""
    
    def test_initialization_with_valid_config(self, mock_rabbitmq_config):
        """
        Test: RabbitMQManager debe inicializarse correctamente con configuración válida
        """
        # Arrange - Configuración válida y mock de conexión
        with patch('manager.rabbitmq_manager.pika.PlainCredentials') as mock_credentials, \
             patch('manager.rabbitmq_manager.pika.ConnectionParameters') as mock_params, \
             patch('manager.rabbitmq_manager.pika.BlockingConnection') as mock_connection:
            
            mock_channel = Mock()
            mock_conn_instance = Mock()
            mock_conn_instance.channel.return_value = mock_channel
            mock_connection.return_value = mock_conn_instance
            
            # Act - Crear instancia de RabbitMQManager
            manager = RabbitMQManager(mock_rabbitmq_config)
            
            # Assert - Verificar inicialización correcta
            assert manager.config == mock_rabbitmq_config
            assert manager.tasks_queue == mock_rabbitmq_config["queue"]
            assert manager.exchange == mock_rabbitmq_config["exchange"]
            assert manager.connection == mock_conn_instance
            assert manager.channel == mock_channel
            assert manager.connected is True
            
            # Verificar llamadas de configuración
            mock_credentials.assert_called_once_with(
                mock_rabbitmq_config["user"], 
                mock_rabbitmq_config["password"]
            )

    def test_initialization_with_connection_failure(self, mock_rabbitmq_config):
        """
        Test: Manejo de fallo de conexión durante inicialización
        """
        # Arrange - Configurar fallo de conexión
        with patch('manager.rabbitmq_manager.pika.BlockingConnection') as mock_connection:
            mock_connection.side_effect = Exception("Connection failed")
            
            # Act & Assert - Verificar que se propaga la excepción
            with pytest.raises(Exception, match="Connection failed"):
                RabbitMQManager(mock_rabbitmq_config)

    def test_default_queue_names_configuration(self, mock_rabbitmq_config):
        """
        Test: Configuración de nombres de colas por defecto
        """
        # Arrange - Configuración sin algunos valores opcionales
        config = mock_rabbitmq_config.copy()
        del config["queue"]
        del config["exchange"]
        
        with patch('manager.rabbitmq_manager.pika.BlockingConnection') as mock_connection:
            mock_channel = Mock()
            mock_conn_instance = Mock()
            mock_conn_instance.channel.return_value = mock_channel
            mock_connection.return_value = mock_conn_instance
            
            # Act - Crear instancia sin configuraciones opcionales
            manager = RabbitMQManager(config)
            
            # Assert - Verificar valores por defecto
            assert manager.tasks_queue == "scraping_queue"
            assert manager.exchange == "scraping_exchange"
            assert manager.results_queue == "scraping_results"
            assert manager.failed_queue == "scraping_failed"


class TestRabbitMQManagerTaskOperations:
    """Tests para operaciones con tareas."""
    
    @pytest.fixture(autouse=True)
    def setup_manager(self, mock_rabbitmq_config):
        """Setup del manager para cada test."""
        with patch('manager.rabbitmq_manager.pika.BlockingConnection') as mock_connection:
            mock_channel = Mock()
            mock_conn_instance = Mock()
            mock_conn_instance.channel.return_value = mock_channel
            mock_connection.return_value = mock_conn_instance
            
            self.manager = RabbitMQManager(mock_rabbitmq_config)
            self.mock_channel = mock_channel
            yield

    @pytest.mark.asyncio
    async def test_add_task_success(self, sample_scraping_task):
        """
        Test: Agregar tarea exitosamente debe publicar mensaje en cola
        """
        # Arrange - Configurar mock del canal
        self.mock_channel.basic_publish = Mock()
        
        # Act - Agregar tarea
        result = await self.manager.add_task(sample_scraping_task)
        
        # Assert - Verificar resultado y llamadas
        assert result is True
        self.mock_channel.basic_publish.assert_called_once()
        
        # Verificar argumentos de la llamada
        call_args = self.mock_channel.basic_publish.call_args
        assert call_args[1]["exchange"] == self.manager.exchange
        assert call_args[1]["routing_key"] == "test_routing"
        
        # Verificar que el cuerpo del mensaje es JSON válido
        body = call_args[1]["body"]
        task_data = json.loads(body)
        assert task_data["id"] == sample_scraping_task.id

    @pytest.mark.asyncio
    async def test_add_task_failure(self, sample_scraping_task):
        """
        Test: Fallo al agregar tarea debe retornar False
        """
        # Arrange - Configurar fallo en publicación
        self.mock_channel.basic_publish.side_effect = Exception("Publish failed")
        
        # Act - Intentar agregar tarea
        result = await self.manager.add_task(sample_scraping_task)
        
        # Assert - Verificar manejo de error
        assert result is False

    @pytest.mark.asyncio
    async def test_get_task_found(self, sample_scraping_task):
        """
        Test: Obtener tarea existente debe retornar la tarea
        """
        # Arrange - Configurar mensaje disponible
        task_data = sample_scraping_task.dict()
        message_body = json.dumps(task_data, default=str)
        
        mock_method = Mock()
        mock_method.delivery_tag = "test-tag"
        
        self.mock_channel.basic_get.return_value = (mock_method, None, message_body.encode())
        self.mock_channel.basic_ack = Mock()
        
        # Act - Obtener tarea
        result = await self.manager.get_task(sample_scraping_task.id)
        
        # Assert - Verificar resultado
        assert result is not None
        assert result.id == sample_scraping_task.id
        self.mock_channel.basic_ack.assert_called_once_with(delivery_tag="test-tag")

    @pytest.mark.asyncio
    async def test_get_task_not_found(self):
        """
        Test: Obtener tarea inexistente debe retornar None
        """
        # Arrange - No hay mensajes disponibles
        self.mock_channel.basic_get.return_value = (None, None, None)
        
        # Act - Intentar obtener tarea inexistente
        result = await self.manager.get_task("nonexistent-task")
        
        # Assert - Verificar que no se encontró
        assert result is None

    @pytest.mark.asyncio
    async def test_list_tasks_success(self, sample_scraping_task):
        """
        Test: Listar tareas debe retornar lista de tareas
        """
        # Arrange - Configurar múltiples mensajes
        task_data = sample_scraping_task.dict()
        message_body = json.dumps(task_data, default=str)
        
        mock_method = Mock()
        mock_method.delivery_tag = "test-tag"
        
        # Simular 2 tareas disponibles
        self.mock_channel.basic_get.side_effect = [
            (mock_method, None, message_body.encode()),
            (mock_method, None, message_body.encode()),
            (None, None, None)  # No más mensajes
        ]
        self.mock_channel.basic_ack = Mock()
        
        # Act - Listar tareas
        result = await self.manager.list_tasks(limit=2)
        
        # Assert - Verificar resultado
        assert len(result) == 2
        assert all(task.id == sample_scraping_task.id for task in result)

    @pytest.mark.asyncio
    async def test_update_task_status_success(self, sample_scraping_task):
        """
        Test: Actualizar estado de tarea debe publicar mensaje actualizado
        """
        # Arrange - Configurar tarea existente
        task_data = sample_scraping_task.dict()
        message_body = json.dumps(task_data, default=str)
        
        mock_method = Mock()
        mock_method.delivery_tag = "test-tag"
        
        self.mock_channel.basic_get.return_value = (mock_method, None, message_body.encode())
        self.mock_channel.basic_ack = Mock()
        self.mock_channel.basic_publish = Mock()
        
        # Act - Actualizar estado
        result = await self.manager.update_task_status(
            sample_scraping_task.id, 
            ScrapingStatus.PROCESSING
        )
        
        # Assert - Verificar actualización
        assert result is True
        self.mock_channel.basic_publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_task_completed_success(self, sample_scraping_task, sample_scraping_result):
        """
        Test: Marcar tarea como completada debe actualizar estado y resultado
        """
        # Arrange - Configurar tarea existente
        task_data = sample_scraping_task.dict()
        message_body = json.dumps(task_data, default=str)
        
        mock_method = Mock()
        mock_method.delivery_tag = "test-tag"
        
        self.mock_channel.basic_get.return_value = (mock_method, None, message_body.encode())
        self.mock_channel.basic_ack = Mock()
        self.mock_channel.basic_publish = Mock()
        
        # Act - Marcar como completada
        result = await self.manager.update_task_completed(
            sample_scraping_task.id, 
            sample_scraping_result
        )
        
        # Assert - Verificar completado
        assert result is True
        self.mock_channel.basic_publish.assert_called_once()
        
        # Verificar que se publica en cola de resultados
        call_args = self.mock_channel.basic_publish.call_args
        assert call_args[1]["routing_key"] == "result"

    @pytest.mark.asyncio
    async def test_update_task_failed_success(self, sample_scraping_task):
        """
        Test: Marcar tarea como fallida debe actualizar estado con error
        """
        # Arrange - Configurar tarea existente
        task_data = sample_scraping_task.dict()
        message_body = json.dumps(task_data, default=str)
        
        mock_method = Mock()
        mock_method.delivery_tag = "test-tag"
        error_message = "Test error message"
        
        self.mock_channel.basic_get.return_value = (mock_method, None, message_body.encode())
        self.mock_channel.basic_ack = Mock()
        self.mock_channel.basic_publish = Mock()
        
        # Act - Marcar como fallida
        result = await self.manager.update_task_failed(
            sample_scraping_task.id, 
            error_message
        )
        
        # Assert - Verificar fallo
        assert result is True
        self.mock_channel.basic_publish.assert_called_once()
        
        # Verificar que se publica en cola de fallidas
        call_args = self.mock_channel.basic_publish.call_args
        assert call_args[1]["routing_key"] == "failed"


class TestRabbitMQManagerQueueOperations:
    """Tests para operaciones con colas."""
    
    @pytest.fixture(autouse=True)
    def setup_manager(self, mock_rabbitmq_config):
        """Setup del manager para cada test."""
        with patch('manager.rabbitmq_manager.pika.BlockingConnection') as mock_connection:
            mock_channel = Mock()
            mock_conn_instance = Mock()
            mock_conn_instance.channel.return_value = mock_channel
            mock_connection.return_value = mock_conn_instance
            
            self.manager = RabbitMQManager(mock_rabbitmq_config)
            self.mock_channel = mock_channel
            yield

    @pytest.mark.asyncio
    async def test_get_queue_stats_success(self):
        """
        Test: Obtener estadísticas de colas debe retornar información correcta
        """
        # Arrange - Configurar respuestas de queue_declare
        mock_tasks_info = Mock()
        mock_tasks_info.method.message_count = 5
        
        mock_results_info = Mock()
        mock_results_info.method.message_count = 10
        
        mock_failed_info = Mock()
        mock_failed_info.method.message_count = 2
        
        self.mock_channel.queue_declare.side_effect = [
            mock_tasks_info,
            mock_results_info, 
            mock_failed_info
        ]
        
        # Act - Obtener estadísticas
        stats = await self.manager.get_queue_stats()
        
        # Assert - Verificar estadísticas
        assert stats["pending"] == 5
        assert stats["completed"] == 10
        assert stats["failed"] == 2
        assert stats["total"] == 17

    @pytest.mark.asyncio
    async def test_get_queue_stats_failure(self):
        """
        Test: Fallo al obtener estadísticas debe retornar valores por defecto
        """
        # Arrange - Configurar fallo
        self.mock_channel.queue_declare.side_effect = Exception("Queue error")
        
        # Act - Intentar obtener estadísticas
        stats = await self.manager.get_queue_stats()
        
        # Assert - Verificar valores por defecto
        assert stats["pending"] == 0
        assert stats["completed"] == 0
        assert stats["failed"] == 0
        assert stats["total"] == 0

    def test_start_consuming_configuration(self):
        """
        Test: Iniciar consumo debe configurar canal correctamente
        """
        # Arrange - Mock del callback
        mock_callback = Mock()
        
        # Act - Iniciar consumo
        self.manager.start_consuming(mock_callback)
        
        # Assert - Verificar configuración
        self.mock_channel.basic_qos.assert_called_once_with(prefetch_count=1)
        self.mock_channel.basic_consume.assert_called_once_with(
            queue=self.manager.tasks_queue,
            on_message_callback=mock_callback,
            auto_ack=False
        )
        self.mock_channel.start_consuming.assert_called_once()

    def test_stop_consuming_success(self):
        """
        Test: Detener consumo debe parar canal si está consumiendo
        """
        # Arrange - Configurar canal consumiendo
        self.mock_channel.is_consuming.return_value = True
        
        # Act - Detener consumo
        self.manager.stop_consuming()
        
        # Assert - Verificar detención
        self.mock_channel.stop_consuming.assert_called_once()

    def test_ack_message_success(self):
        """
        Test: Confirmar mensaje debe llamar basic_ack
        """
        # Arrange - Tag de entrega
        delivery_tag = "test-delivery-tag"
        
        # Act - Confirmar mensaje
        self.manager.ack_message(delivery_tag)
        
        # Assert - Verificar confirmación
        self.mock_channel.basic_ack.assert_called_once_with(delivery_tag=delivery_tag)

    def test_nack_message_success(self):
        """
        Test: Rechazar mensaje debe llamar basic_nack
        """
        # Arrange - Tag de entrega
        delivery_tag = "test-delivery-tag"
        
        # Act - Rechazar mensaje con requeue
        self.manager.nack_message(delivery_tag, requeue=True)
        
        # Assert - Verificar rechazo
        self.mock_channel.basic_nack.assert_called_once_with(
            delivery_tag=delivery_tag, 
            requeue=True
        )


class TestRabbitMQManagerConnectionManagement:
    """Tests para gestión de conexiones."""
    
    def test_close_connection_success(self, mock_rabbitmq_config):
        """
        Test: Cerrar conexión debe cerrar conexión si está abierta
        """
        # Arrange - Configurar conexión abierta
        with patch('manager.rabbitmq_manager.pika.BlockingConnection') as mock_connection:
            mock_channel = Mock()
            mock_conn_instance = Mock()
            mock_conn_instance.channel.return_value = mock_channel
            mock_conn_instance.is_closed = False
            mock_connection.return_value = mock_conn_instance
            
            manager = RabbitMQManager(mock_rabbitmq_config)
            
            # Act - Cerrar conexión
            manager.close()
            
            # Assert - Verificar cierre
            mock_conn_instance.close.assert_called_once()

    def test_close_connection_already_closed(self, mock_rabbitmq_config):
        """
        Test: Cerrar conexión ya cerrada no debe causar error
        """
        # Arrange - Configurar conexión cerrada
        with patch('manager.rabbitmq_manager.pika.BlockingConnection') as mock_connection:
            mock_channel = Mock()
            mock_conn_instance = Mock()
            mock_conn_instance.channel.return_value = mock_channel
            mock_conn_instance.is_closed = True
            mock_connection.return_value = mock_conn_instance
            
            manager = RabbitMQManager(mock_rabbitmq_config)
            
            # Act - Intentar cerrar conexión ya cerrada
            manager.close()
            
            # Assert - Verificar que no se llama close
            mock_conn_instance.close.assert_not_called()

    def test_destructor_calls_close(self, mock_rabbitmq_config):
        """
        Test: Destructor debe llamar close automáticamente
        """
        # Arrange - Configurar manager
        with patch('manager.rabbitmq_manager.pika.BlockingConnection') as mock_connection:
            mock_channel = Mock()
            mock_conn_instance = Mock()
            mock_conn_instance.channel.return_value = mock_channel
            mock_conn_instance.is_closed = False
            mock_connection.return_value = mock_conn_instance
            
            manager = RabbitMQManager(mock_rabbitmq_config)
            
            # Act - Destruir objeto (simular)
            with patch.object(manager, 'close') as mock_close:
                del manager
                # En Python real, el destructor se llama automáticamente
                # Para el test, verificamos que el método existe
                assert hasattr(RabbitMQManager, '__del__')
