"""
Tests unitarios para MessageListener siguiendo patrón AAA y TDD.
"""
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from manager.listeners.message_listener import MessageListener
from models import ScrapingTask, ScrapingStatus


class TestMessageListenerInitialization:
    """Tests para inicialización del MessageListener."""
    
    def test_initialization_success(self, mock_rabbitmq_config):
        """
        Test: MessageListener debe inicializarse correctamente
        """
        # Arrange - Mock de configuraciones
        with patch('manager.listeners.message_listener.RABBITMQ_CONFIG', mock_rabbitmq_config), \
             patch('manager.listeners.message_listener.ScraperService') as mock_scraper, \
             patch('manager.listeners.message_listener.DatabaseConnector') as mock_db:
            
            mock_scraper_instance = Mock()
            mock_scraper.return_value = mock_scraper_instance
            
            mock_db_instance = Mock()
            mock_db.return_value = mock_db_instance
            
            # Act - Crear instancia de MessageListener
            listener = MessageListener()
            
            # Assert - Verificar inicialización
            assert listener.connection is None
            assert listener.channel is None
            assert listener.running is False
            assert listener.scraper_service == mock_scraper_instance
            assert listener.database_connector == mock_db_instance
            assert listener.config == mock_rabbitmq_config
            assert listener.queue_name == mock_rabbitmq_config["queue"]

    def test_initialization_with_scraper_service_failure(self, mock_rabbitmq_config):
        """
        Test: Manejo de fallo al inicializar ScraperService
        """
        # Arrange - Configurar fallo en ScraperService
        with patch('manager.listeners.message_listener.RABBITMQ_CONFIG', mock_rabbitmq_config), \
             patch('manager.listeners.message_listener.ScraperService') as mock_scraper, \
             patch('manager.listeners.message_listener.DatabaseConnector'):
            
            mock_scraper.side_effect = Exception("ScraperService error")
            
            # Act & Assert - Verificar que se propaga la excepción
            with pytest.raises(Exception, match="ScraperService error"):
                MessageListener()


class TestMessageListenerConnection:
    """Tests para conexión con RabbitMQ."""
    
    @pytest.fixture(autouse=True)
    def setup_listener(self, mock_rabbitmq_config):
        """Setup del listener para cada test."""
        with patch('manager.listeners.message_listener.RABBITMQ_CONFIG', mock_rabbitmq_config), \
             patch('manager.listeners.message_listener.ScraperService'), \
             patch('manager.listeners.message_listener.DatabaseConnector'):
            
            self.listener = MessageListener()
            yield

    def test_connect_success(self):
        """
        Test: Conexión exitosa debe configurar canal y colas
        """
        # Arrange - Mock de pika
        with patch('manager.listeners.message_listener.pika.PlainCredentials') as mock_creds, \
             patch('manager.listeners.message_listener.pika.ConnectionParameters') as mock_params, \
             patch('manager.listeners.message_listener.pika.BlockingConnection') as mock_conn:
            
            mock_channel = Mock()
            mock_connection = Mock()
            mock_connection.channel.return_value = mock_channel
            mock_conn.return_value = mock_connection
            
            # Configurar queue_declare para simular cola existente
            mock_channel.queue_declare.return_value = Mock()
            
            # Act - Establecer conexión
            self.listener._connect()
            
            # Assert - Verificar configuración
            assert self.listener.connection == mock_connection
            assert self.listener.channel == mock_channel
            
            # Verificar llamadas de configuración
            mock_creds.assert_called_once()
            mock_params.assert_called_once()
            mock_channel.exchange_declare.assert_called_once()
            mock_channel.basic_qos.assert_called_once_with(prefetch_count=1)

    def test_connect_failure(self):
        """
        Test: Fallo de conexión debe propagar excepción
        """
        # Arrange - Configurar fallo de conexión
        with patch('manager.listeners.message_listener.pika.BlockingConnection') as mock_conn:
            mock_conn.side_effect = Exception("Connection failed")
            
            # Act & Assert - Verificar propagación de excepción
            with pytest.raises(Exception, match="Connection failed"):
                self.listener._connect()

    def test_queue_declaration_existing_queue(self):
        """
        Test: Declaración de cola existente debe usar passive=True
        """
        # Arrange - Configurar cola existente
        with patch('manager.listeners.message_listener.pika.BlockingConnection') as mock_conn:
            mock_channel = Mock()
            mock_connection = Mock()
            mock_connection.channel.return_value = mock_channel
            mock_conn.return_value = mock_connection
            
            # Simular que la cola existe
            mock_channel.queue_declare.return_value = Mock()
            
            # Act - Conectar
            self.listener._connect()
            
            # Assert - Verificar llamada con passive=True primero
            calls = mock_channel.queue_declare.call_args_list
            first_call = calls[0]
            assert first_call[1]["passive"] is True

    def test_queue_declaration_new_queue(self):
        """
        Test: Crear nueva cola si no existe debe usar argumentos específicos
        """
        # Arrange - Configurar cola inexistente
        with patch('manager.listeners.message_listener.pika.BlockingConnection') as mock_conn:
            mock_channel = Mock()
            mock_connection = Mock()
            mock_connection.channel.return_value = mock_channel
            mock_conn.return_value = mock_connection
            
            # Simular que la cola no existe en primera llamada
            mock_channel.queue_declare.side_effect = [
                Exception("Queue not found"),  # Primera llamada falla
                Mock()  # Segunda llamada exitosa
            ]
            
            # Act - Conectar
            self.listener._connect()
            
            # Assert - Verificar segunda llamada con argumentos
            calls = mock_channel.queue_declare.call_args_list
            second_call = calls[1]
            assert second_call[1]["durable"] is True
            assert "arguments" in second_call[1]


class TestMessageListenerMessageProcessing:
    """Tests para procesamiento de mensajes."""
    
    @pytest.fixture(autouse=True)
    def setup_listener(self, mock_rabbitmq_config, sample_scraping_task):
        """Setup del listener para cada test."""
        with patch('manager.listeners.message_listener.RABBITMQ_CONFIG', mock_rabbitmq_config), \
             patch('manager.listeners.message_listener.ScraperService') as mock_scraper, \
             patch('manager.listeners.message_listener.DatabaseConnector') as mock_db:
            
            self.mock_scraper_service = Mock()
            mock_scraper.return_value = self.mock_scraper_service
            
            self.mock_db_connector = Mock()
            mock_db.return_value = self.mock_db_connector
            
            self.listener = MessageListener()
            self.sample_task = sample_scraping_task
            yield

    def test_process_message_valid_task(self, sample_product_list):
        """
        Test: Procesamiento de mensaje válido debe ejecutar scraping
        """
        # Arrange - Configurar mensaje válido y mocks
        task_data = self.sample_task.dict()
        message_body = json.dumps(task_data).encode()
        
        mock_channel = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = "test-tag"
        mock_properties = Mock()
        
        # Configurar run_main para retornar productos
        with patch('manager.listeners.message_listener.run_main') as mock_run_main:
            mock_run_main.return_value = sample_product_list
            self.mock_db_connector.insert_products.return_value = True
            
            # Act - Procesar mensaje
            self.listener._process_message(mock_channel, mock_method, mock_properties, message_body)
            
            # Assert - Verificar procesamiento
            mock_run_main.assert_called_once_with(
                url=self.sample_task.request.url,
                max_products=self.sample_task.request.max_products,
                task_id=self.sample_task.id,
                category=self.sample_task.request.category,
                page=self.sample_task.request.page
            )
            
            # Verificar que se guardaron los productos
            self.mock_db_connector.insert_products.assert_called_once_with(sample_product_list)
            
            # Verificar confirmación del mensaje
            mock_channel.basic_ack.assert_called_once_with(delivery_tag="test-tag")

    def test_save_products_success(self, sample_product_list):
        """
        Test: Guardar productos exitosamente debe retornar True
        """
        # Arrange - Configurar éxito en inserción
        self.mock_db_connector.insert_products.return_value = True
        task_id = "test-task-123"
        
        # Act - Guardar productos
        result = self.listener._save_products(sample_product_list, task_id)
        
        # Assert - Verificar éxito
        assert result is True
        self.mock_db_connector.insert_products.assert_called_once_with(sample_product_list)

    def test_save_products_failure(self, sample_product_list):
        """
        Test: Fallo al guardar productos debe retornar False
        """
        # Arrange - Configurar fallo en inserción
        self.mock_db_connector.insert_products.side_effect = Exception("Database error")
        task_id = "test-task-123"
        
        # Act - Intentar guardar productos
        result = self.listener._save_products(sample_product_list, task_id)
        
        # Assert - Verificar fallo
        assert result is False


class TestMessageListenerMessageAdaptation:
    """Tests para adaptación de formatos de mensaje."""
    
    @pytest.fixture(autouse=True)
    def setup_listener(self, mock_rabbitmq_config):
        """Setup del listener para cada test."""
        with patch('manager.listeners.message_listener.RABBITMQ_CONFIG', mock_rabbitmq_config), \
             patch('manager.listeners.message_listener.ScraperService'), \
             patch('manager.listeners.message_listener.DatabaseConnector'):
            
            self.listener = MessageListener()
            yield

    def test_adapt_message_format_correct_format(self, sample_scraping_task):
        """
        Test: Mensaje con formato correcto no debe ser modificado
        """
        # Arrange - Mensaje con formato correcto
        message_data = sample_scraping_task.dict()
        
        # Act - Adaptar mensaje
        result = self.listener._adapt_message_format(message_data)
        
        # Assert - Verificar que no se modifica
        assert result == message_data

    def test_adapt_message_format_old_publisher_format(self):
        """
        Test: Mensaje en formato de publisher debe ser adaptado
        """
        # Arrange - Mensaje en formato antiguo del publisher
        old_format_message = {
            "url": "https://listado.mercadolibre.com.uy/MLU1144",
            "category": "MLU1144",
            "page": 1,
            "metadata": {"max_products": 25},
            "timestamp": "2023-01-01T10:00:00"
        }
        
        # Act - Adaptar mensaje
        result = self.listener._adapt_message_format(old_format_message)
        
        # Assert - Verificar adaptación
        assert "id" in result
        assert "request" in result
        assert "status" in result
        assert "created_at" in result
        
        assert result["request"]["url"] == old_format_message["url"]
        assert result["request"]["category"] == old_format_message["category"]
        assert result["request"]["page"] == old_format_message["page"]
        assert result["request"]["max_products"] == 25
        assert result["status"] == ScrapingStatus.PENDING

    def test_adapt_message_format_old_format_with_defaults(self):
        """
        Test: Mensaje antiguo sin metadatos debe usar valores por defecto
        """
        # Arrange - Mensaje sin metadatos
        old_format_message = {
            "url": "https://listado.mercadolibre.com.uy/MLU1144",
            "category": "MLU1144"
        }
        
        # Act - Adaptar mensaje
        result = self.listener._adapt_message_format(old_format_message)
        
        # Assert - Verificar valores por defecto
        assert result["request"]["page"] == 1
        assert result["request"]["max_products"] == 50
        assert "id" in result

    def test_adapt_message_format_unrecognized_format(self):
        """
        Test: Mensaje con formato no reconocido debe lanzar error
        """
        # Arrange - Mensaje con formato desconocido
        unknown_format = {
            "unknown_field": "unknown_value"
        }
        
        # Act & Assert - Verificar error
        with pytest.raises(ValueError, match="Formato de mensaje no reconocido"):
            self.listener._adapt_message_format(unknown_format)


class TestMessageListenerLifecycle:
    """Tests para ciclo de vida del listener."""
    
    @pytest.fixture(autouse=True)
    def setup_listener(self, mock_rabbitmq_config):
        """Setup del listener para cada test."""
        with patch('manager.listeners.message_listener.RABBITMQ_CONFIG', mock_rabbitmq_config), \
             patch('manager.listeners.message_listener.ScraperService'), \
             patch('manager.listeners.message_listener.DatabaseConnector'):
            
            self.listener = MessageListener()
            yield

    def test_start_listening_success(self):
        """
        Test: Iniciar escucha debe configurar conexión y consumo
        """
        # Arrange - Mock de conexión exitosa
        with patch.object(self.listener, '_connect') as mock_connect:
            mock_channel = Mock()
            self.listener.channel = mock_channel
            
            # Act - Iniciar escucha
            self.listener.start_listening()
            
            # Assert - Verificar configuración
            mock_connect.assert_called_once()
            mock_channel.basic_consume.assert_called_once_with(
                queue=self.listener.queue_name,
                on_message_callback=self.listener._process_message,
                auto_ack=False
            )
            mock_channel.start_consuming.assert_called_once()
            assert self.listener.running is True

    def test_start_listening_keyboard_interrupt(self):
        """
        Test: Interrupción por teclado debe detener listener gracefully
        """
        # Arrange - Configurar interrupción
        with patch.object(self.listener, '_connect'), \
             patch.object(self.listener, 'stop_listening') as mock_stop:
            
            mock_channel = Mock()
            mock_channel.start_consuming.side_effect = KeyboardInterrupt()
            self.listener.channel = mock_channel
            
            # Act - Iniciar escucha con interrupción
            self.listener.start_listening()
            
            # Assert - Verificar detención graceful
            mock_stop.assert_called_once()

    def test_start_listening_connection_error(self):
        """
        Test: Error de conexión debe detener listener
        """
        # Arrange - Configurar error de conexión
        with patch.object(self.listener, '_connect') as mock_connect, \
             patch.object(self.listener, 'stop_listening') as mock_stop:
            
            mock_connect.side_effect = Exception("Connection error")
            
            # Act - Iniciar escucha con error
            self.listener.start_listening()
            
            # Assert - Verificar detención por error
            mock_stop.assert_called_once()

    def test_stop_listening_success(self):
        """
        Test: Detener escucha debe cerrar conexiones correctamente
        """
        # Arrange - Configurar listener activo
        mock_channel = Mock()
        mock_channel.is_consuming.return_value = True
        
        mock_connection = Mock()
        mock_connection.is_closed = False
        
        self.listener.channel = mock_channel
        self.listener.connection = mock_connection
        self.listener.running = True
        
        # Act - Detener escucha
        self.listener.stop_listening()
        
        # Assert - Verificar detención
        assert self.listener.running is False
        mock_channel.stop_consuming.assert_called_once()
        mock_connection.close.assert_called_once()

    def test_stop_listening_already_stopped(self):
        """
        Test: Detener listener ya detenido no debe causar errores
        """
        # Arrange - Listener sin conexiones activas
        self.listener.channel = None
        self.listener.connection = None
        
        # Act - Detener listener ya detenido
        self.listener.stop_listening()
        
        # Assert - No debe haber errores
        assert self.listener.running is False


class TestMessageListenerIntegration:
    """Tests de integración para MessageListener."""
    
    def test_main_function_creates_and_starts_listener(self, mock_rabbitmq_config):
        """
        Test: Función main debe crear e iniciar listener
        """
        # Arrange - Mock de MessageListener
        with patch('manager.listeners.message_listener.RABBITMQ_CONFIG', mock_rabbitmq_config), \
             patch('manager.listeners.message_listener.MessageListener') as mock_listener_class:
            
            mock_listener = Mock()
            mock_listener_class.return_value = mock_listener
            
            # Importar main después de configurar mocks
            from manager.listeners.message_listener import main
            
            # Act - Ejecutar función main
            main()
            
            # Assert - Verificar creación e inicio
            mock_listener_class.assert_called_once()
            mock_listener.start_listening.assert_called_once()

    def test_main_function_handles_fatal_error(self, mock_rabbitmq_config):
        """
        Test: Función main debe manejar errores fatales
        """
        # Arrange - Configurar error fatal
        with patch('manager.listeners.message_listener.RABBITMQ_CONFIG', mock_rabbitmq_config), \
             patch('manager.listeners.message_listener.MessageListener') as mock_listener_class, \
             patch('sys.exit') as mock_exit:
            
            mock_listener = Mock()
            mock_listener.start_listening.side_effect = Exception("Fatal error")
            mock_listener_class.return_value = mock_listener
            
            from manager.listeners.message_listener import main
            
            # Act - Ejecutar main con error
            main()
            
            # Assert - Verificar manejo de error
            mock_exit.assert_called_once_with(1)


class TestMessageListenerCache:
    """Tests para la integración del cache en MessageListener."""
    
    def setup_method(self):
        """Configurar antes de cada test."""
        self.mock_rabbitmq_config = {
            'host': 'localhost',
            'port': 5672,
            'username': 'test',
            'password': 'test',
            'queue': 'test_queue'
        }
    
    @pytest.fixture(autouse=True)
    def setup_listener_mocks(self):
        """Setup automático de mocks para evitar conexiones reales a Supabase."""
        with patch('manager.listeners.message_listener.DatabaseConnector') as mock_db_class, \
             patch('manager.listeners.message_listener.ScraperService') as mock_scraper_class:
            
            # Mock del DatabaseConnector para evitar conexión a Supabase
            mock_db_class.return_value = Mock()
            # Mock del ScraperService
            mock_scraper_class.return_value = Mock()
            yield
        
    def test_cache_hit_skips_processing(self, mock_rabbitmq_config):
        """Test: Cache hit debe omitir el procesamiento del mensaje."""
        from manager.cache_manager import CacheManager
        from models import ScrapingResponse
        
        # Arrange
        with patch('manager.listeners.message_listener.RABBITMQ_CONFIG', mock_rabbitmq_config):
            listener = MessageListener()
            
            # Mock cache con respuesta existente
            mock_cache = Mock(spec=CacheManager)
            cached_response = ScrapingResponse(
                task_id="cached-task",
                status=ScrapingStatus.COMPLETED,
                message="Desde cache",
                url="https://test.com",
                category="MLU5725",
                page=1,
                max_products=50
            )
            mock_cache.get.return_value = cached_response
            
            # Preparar mensaje de prueba
            message_data = {
                "url": "https://test.com",
                "category": "MLU5725",
                "page": 1,
                "metadata": {"max_products": 50}
            }
            body = json.dumps(message_data).encode()
            
            # Mock de objetos de RabbitMQ
            mock_ch = Mock()
            mock_method = Mock()
            mock_method.delivery_tag = "test_tag"
            mock_properties = Mock()
            mock_properties.message_id = "test_message_id"
        
        # Act
        with patch('manager.listeners.message_listener.cache_manager', mock_cache):
            with patch.object(listener, '_process_task_sync') as mock_process:
                listener._process_message(mock_ch, mock_method, mock_properties, body)
        
        # Assert
        mock_cache.get.assert_called_once_with("MLU5725", 1)
        mock_process.assert_not_called()  # No debe procesar la tarea
        mock_ch.basic_ack.assert_called_once_with(delivery_tag="test_tag")
    
    def test_cache_miss_processes_task(self, mock_rabbitmq_config):
        """Test: Cache miss debe procesar la tarea normalmente."""
        from manager.cache_manager import CacheManager
        
        # Arrange
        with patch('manager.listeners.message_listener.RABBITMQ_CONFIG', mock_rabbitmq_config):
            listener = MessageListener()
            
            # Mock cache sin respuesta
            mock_cache = Mock(spec=CacheManager)
            mock_cache.get.return_value = None
            
            # Preparar mensaje de prueba
            message_data = {
                "url": "https://test.com",
                "category": "MLU5725",
                "page": 1,
                "metadata": {"max_products": 50}
            }
            body = json.dumps(message_data).encode()
            
            # Mock de objetos de RabbitMQ
            mock_ch = Mock()
            mock_method = Mock()
            mock_method.delivery_tag = "test_tag"
            mock_properties = Mock()
            mock_properties.message_id = "test_message_id"
        
        # Act
        with patch('manager.listeners.message_listener.cache_manager', mock_cache):
            with patch.object(listener, '_process_task_sync') as mock_process:
                listener._process_message(mock_ch, mock_method, mock_properties, body)
        
        # Assert
        mock_cache.get.assert_called_once_with("MLU5725", 1)
        mock_process.assert_called_once()  # Debe procesar la tarea
        mock_ch.basic_ack.assert_called_once_with(delivery_tag="test_tag")
    
    def test_successful_processing_updates_cache(self, mock_rabbitmq_config):
        """Test: Procesamiento exitoso debe actualizar el cache."""
        from manager.cache_manager import CacheManager
        from models import ScrapingRequest
        from scraper.models.models import Product
        
        # Arrange
        with patch('manager.listeners.message_listener.RABBITMQ_CONFIG', mock_rabbitmq_config):
            listener = MessageListener()
            
            mock_cache = Mock(spec=CacheManager)
            
            # Crear tarea de prueba
            request = ScrapingRequest(
                url="https://test.com",
                category="MLU5725",
                page=1,
                max_products=50
            )
            
            task = ScrapingTask(
                id="test-task",
                request=request,
                status=ScrapingStatus.PENDING,
                created_at=datetime.now().isoformat()
            )
            
            # Mock productos de resultado
            from decimal import Decimal
            mock_products = [
                Product(
                    title="Test Product 1",
                    url="https://test1.com",
                    seller="Test Seller 1",
                    current_price=Decimal("100.0"),
                    category="MLU5725",
                    page=1
                ),
                Product(
                    title="Test Product 2",
                    url="https://test2.com",
                    seller="Test Seller 2",
                    current_price=Decimal("200.0"),
                    category="MLU5725",
                    page=1
                )
            ]
        
        # Act
        with patch('manager.listeners.message_listener.cache_manager', mock_cache):
            with patch('manager.listeners.message_listener.run_main', return_value=mock_products):
                with patch.object(listener, '_save_products', return_value=True):
                    with patch.object(listener.scraper_service, 'is_available', return_value=True):
                        listener._process_task_sync(task)
        
        # Assert
        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args
        category, page, response = call_args[0]
        
        assert category == "MLU5725"
        assert page == 1
        assert response.status == ScrapingStatus.COMPLETED
        assert "2 productos encontrados" in response.message
        assert response.task_id == "test-task"
    
    def test_failed_processing_invalidates_cache(self, mock_rabbitmq_config):
        """Test: Procesamiento fallido debe invalidar el cache."""
        from manager.cache_manager import CacheManager
        from models import ScrapingRequest
        
        # Arrange
        with patch('manager.listeners.message_listener.RABBITMQ_CONFIG', mock_rabbitmq_config):
            listener = MessageListener()
            
            mock_cache = Mock(spec=CacheManager)
            
            # Crear tarea de prueba
            request = ScrapingRequest(
                url="https://test.com",
                category="MLU5725",
                page=1,
                max_products=50
            )
            
            task = ScrapingTask(
                id="test-task",
                request=request,
                status=ScrapingStatus.PENDING,
                created_at=datetime.now().isoformat()
            )
        
        # Act
        with patch('manager.listeners.message_listener.cache_manager', mock_cache):
            with patch('manager.listeners.message_listener.run_main', side_effect=Exception("Test error")):
                with patch.object(listener.scraper_service, 'is_available', return_value=True):
                    listener._process_task_sync(task)
        
        # Assert
        mock_cache.invalidate.assert_called_once_with("MLU5725", 1)
        mock_cache.set.assert_not_called()  # No debe guardar en cache si falla
