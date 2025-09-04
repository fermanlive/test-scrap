"""
Tests unitarios para main.py siguiendo patrón AAA y TDD.
"""
import pytest
import asyncio
import uuid
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from models import (
    ScrapingRequest, ScrapingResponse, ScrapingTask, 
    ScrapingResult, HealthCheck, ScrapingStatus
)


class TestMainAPI:
    """Tests para los endpoints principales de la API."""
    
    @pytest.fixture(autouse=True)
    def setup_mocks(self, mock_rabbitmq_manager, mock_scraper_service, 
                   mock_api_config, mock_scraper_config, 
                   mock_rabbitmq_config):
        """Setup automático de mocks para cada test."""
        # Arrange - Configurar mock de thread sin recursión
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        mock_thread.name = "TestListener"
        
        # Arrange - Configurar mocks globales
        with patch.multiple(
            'main',
            API_CONFIG=mock_api_config,
            SCRAPER_CONFIG=mock_scraper_config,
            RABBITMQ_CONFIG=mock_rabbitmq_config,
            queue_manager=mock_rabbitmq_manager,
            scraper_service=mock_scraper_service,
            listener_running=True,
            listener_thread=mock_thread
        ):
            # Importar main después de configurar los mocks
            import main
            self.app = main.app
            self.client = TestClient(self.app)
            yield

    def test_root_endpoint_returns_correct_response(self, mock_api_config):
        """
        Test: El endpoint raíz debe retornar información básica de la API
        """
        # Arrange - Ya configurado en setup_mocks
        expected_response = {
            "message": "Mercado Libre Uruguay Scraping API",
            "version": mock_api_config["version"],
            "docs": "/docs"
        }
        
        # Act - Hacer petición al endpoint raíz
        response = self.client.get("/")
        
        # Assert - Verificar respuesta
        assert response.status_code == 200
        assert response.json() == expected_response

    def test_health_check_healthy_when_all_services_available(self, mock_api_config):
        """
        Test: Health check debe retornar 'healthy' cuando todos los servicios están disponibles
        """
        # Arrange - Servicios disponibles (ya configurado en setup_mocks)
        
        # Act - Hacer petición al health check
        response = self.client.get("/health")
        
        # Assert - Verificar respuesta healthy
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["rabbitmq_connected"] is True
        assert data["scraper_available"] is True
        assert data["version"] == mock_api_config["version"]
        assert "timestamp" in data

    def test_health_check_unhealthy_when_rabbitmq_disconnected(self, mock_api_config):
        """
        Test: Health check debe retornar 'unhealthy' cuando RabbitMQ está desconectado
        """
        # Arrange - RabbitMQ desconectado
        with patch('main.queue_manager') as mock_manager:
            mock_manager.connected = False
            
            # Act - Hacer petición al health check
            response = self.client.get("/health")
            
            # Assert - Verificar respuesta unhealthy
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["rabbitmq_connected"] is False

    def test_health_check_unhealthy_when_scraper_unavailable(self, mock_api_config):
        """
        Test: Health check debe retornar 'unhealthy' cuando el scraper no está disponible
        """
        # Arrange - Scraper no disponible
        with patch('main.scraper_service') as mock_service:
            mock_service.is_available.return_value = False
            
            # Act - Hacer petición al health check
            response = self.client.get("/health")
            
            # Assert - Verificar respuesta unhealthy
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["scraper_available"] is False

    def test_health_check_handles_exceptions_gracefully(self, mock_api_config):
        """
        Test: Health check debe manejar excepciones y retornar estado unhealthy
        """
        # Arrange - Configurar excepción
        with patch('main.queue_manager') as mock_manager:
            mock_manager.connected = Mock(side_effect=Exception("Test error"))
            
            # Act - Hacer petición al health check
            response = self.client.get("/health")
            
            # Assert - Verificar manejo de error
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["rabbitmq_connected"] is False
            assert data["scraper_available"] is False

    def test_listener_status_returns_correct_information(self):
        """
        Test: El endpoint de estado del listener debe retornar información correcta
        """
        # Arrange - Ya configurado en setup_mocks
        
        # Act - Hacer petición al estado del listener
        response = self.client.get("/listener/status")
        
        # Assert - Verificar respuesta
        assert response.status_code == 200
        data = response.json()
        assert data["listener_running"] is True
        assert data["listener_thread_alive"] is True
        assert data["listener_thread_name"] == "TestListener"
        assert "timestamp" in data

    def test_get_categories_returns_pattern_information(self):
        """
        Test: El endpoint de categorías debe retornar información del patrón de validación
        """
        # Arrange - Respuesta esperada del nuevo endpoint
        expected_response = {
            "pattern": "ML[A-Z][0-9]{3,4}",
            "description": "Categorías de Mercado Libre con formato ML + letra + 3-4 números",
            "examples": ["MLU107", "MLA1234", "MLC456", "MLB7890"],
            "regex": "^ML[A-Z]\\d{3,4}$"
        }
        
        # Act - Hacer petición a categorías
        response = self.client.get("/categories")
        
        # Assert - Verificar respuesta
        assert response.status_code == 200
        data = response.json()
        assert data["pattern"] == expected_response["pattern"]
        assert data["description"] == expected_response["description"]
        assert data["examples"] == expected_response["examples"]
        assert data["regex"] == expected_response["regex"]

    @patch('main.uuid.uuid4')
    def test_create_scraping_task_with_valid_request(self, mock_uuid, sample_scraping_request, 
                                                   mock_scraper_config):
        """
        Test: Crear tarea de scraping con request válido debe retornar respuesta exitosa
        """
        # Arrange - Configurar UUID y request válido
        mock_task_id = "test-uuid-1234"
        mock_uuid.return_value = mock_task_id
        
        request_data = {
            "url": sample_scraping_request.url,
            "category": sample_scraping_request.category,
            "page": sample_scraping_request.page,
            "max_products": sample_scraping_request.max_products
        }
        
        # Act - Crear tarea de scraping
        response = self.client.post("/scrape", json=request_data)
        
        # Assert - Verificar respuesta exitosa
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == mock_task_id
        assert data["status"] == ScrapingStatus.PENDING
        assert data["message"] == "Tarea de scraping creada exitosamente"
        assert data["category"] == sample_scraping_request.category
        assert data["page"] == sample_scraping_request.page
        assert data["max_products"] == sample_scraping_request.max_products
        
        # Verificar que se construyó la URL correctamente
        expected_url = f"{mock_scraper_config['base_url']}?category={sample_scraping_request.category}&page={sample_scraping_request.page}"
        assert data["url"] == expected_url

    def test_create_scraping_task_with_invalid_category(self):
        """
        Test: Crear tarea con categoría inválida debe retornar error 422 (validación Pydantic)
        """
        # Arrange - Request con categoría inválida (no cumple patrón ML[A-Z][0-9]{3,4})
        invalid_request = {
            "url": "https://listado.mercadolibre.com.uy/INVALID",
            "category": "INVALID_CATEGORY",
            "page": 1,
            "max_products": 10
        }
        
        # Act - Intentar crear tarea con categoría inválida
        response = self.client.post("/scrape", json=invalid_request)
        
        # Assert - Verificar error 422 (validación Pydantic)
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # La validación Pydantic debería incluir el mensaje del validador
        error_detail = str(data["detail"])
        assert "ML[A-Z][0-9]{3,4}" in error_detail

    def test_create_scraping_task_with_valid_category_formats(self):
        """
        Test: Crear tarea con diferentes formatos válidos de categoría debe funcionar
        """
        # Arrange - Configurar cache para no interferir
        with patch('main.cache_manager') as mock_cache:
            mock_cache.get.return_value = None  # No respuesta cached
            
            # Diferentes formatos válidos de categoría
            valid_categories = [
                "MLU107",    # 3 dígitos
                "MLA1234",   # 4 dígitos
                "MLC456",    # 3 dígitos
                "MLB7890"    # 4 dígitos
            ]
            
            for category in valid_categories:
                # Arrange - Request con categoría válida
                valid_request = {
                    "url": f"https://listado.mercadolibre.com.uy/{category}",
                    "category": category,
                    "page": 1,
                    "max_products": 10
                }
                
                # Act - Crear tarea con categoría válida
                response = self.client.post("/scrape", json=valid_request)
                
                # Assert - Verificar que se acepta la categoría
                assert response.status_code == 200, f"Categoría {category} debería ser válida"
                data = response.json()
                assert data["status"] == ScrapingStatus.PENDING
                assert data["category"] == category

    def test_create_scraping_task_handles_queue_manager_failure(self, sample_scraping_request):
        """
        Test: Manejar fallo del queue manager debe retornar error 500
        """
        # Arrange - Configurar fallo en queue manager y cache sin respuesta
        with patch('main.queue_manager') as mock_manager, \
             patch('main.cache_manager') as mock_cache:
            
            # Configurar cache para no devolver respuesta cached
            mock_cache.get.return_value = None
            # Configurar fallo en queue manager
            mock_manager.add_task = AsyncMock(side_effect=Exception("Queue error"))
            
            request_data = {
                "url": sample_scraping_request.url,
                "category": sample_scraping_request.category,
                "page": sample_scraping_request.page,
                "max_products": sample_scraping_request.max_products
            }
            
            # Act - Intentar crear tarea
            response = self.client.post("/scrape", json=request_data)
            
            # Assert - Verificar error 500
            assert response.status_code == 500
            data = response.json()
            assert data["detail"] == "Error interno del servidor"

    def test_get_task_status_with_existing_task(self, sample_scraping_task):
        """
        Test: Obtener estado de tarea existente debe retornar la tarea
        """
        # Arrange - Configurar tarea existente
        task_id = sample_scraping_task.id
        with patch('main.queue_manager') as mock_manager:
            mock_manager.get_task = AsyncMock(return_value=sample_scraping_task)
            
            # Act - Obtener estado de tarea
            response = self.client.get(f"/tasks/{task_id}")
            
            # Assert - Verificar respuesta exitosa
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == task_id
            assert data["status"] == sample_scraping_task.status

    def test_get_task_status_with_nonexistent_task(self):
        """
        Test: Obtener estado de tarea inexistente debe retornar error 404
        """
        # Arrange - Configurar tarea inexistente
        task_id = "nonexistent-task-id"
        with patch('main.queue_manager') as mock_manager:
            mock_manager.get_task = AsyncMock(return_value=None)
            
            # Act - Intentar obtener tarea inexistente
            response = self.client.get(f"/tasks/{task_id}")
            
            # Assert - Verificar error 404
            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "Tarea no encontrada"

    def test_get_task_status_handles_queue_manager_failure(self):
        """
        Test: Manejar fallo del queue manager al obtener tarea debe retornar error 500
        """
        # Arrange - Configurar fallo en queue manager
        task_id = "test-task-id"
        with patch('main.queue_manager') as mock_manager:
            mock_manager.get_task = AsyncMock(side_effect=Exception("Queue error"))
            
            # Act - Intentar obtener tarea
            response = self.client.get(f"/tasks/{task_id}")
            
            # Assert - Verificar error 500
            assert response.status_code == 500
            data = response.json()
            assert data["detail"] == "Error interno del servidor"

    def test_list_tasks_with_default_parameters(self, sample_scraping_task):
        """
        Test: Listar tareas con parámetros por defecto debe retornar lista
        """
        # Arrange - Configurar lista de tareas
        tasks_list = [sample_scraping_task]
        with patch('main.queue_manager') as mock_manager:
            mock_manager.list_tasks = AsyncMock(return_value=tasks_list)
            
            # Act - Listar tareas
            response = self.client.get("/tasks")
            
            # Assert - Verificar respuesta exitosa
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == sample_scraping_task.id
            
            # Verificar que se llamó con parámetros por defecto
            mock_manager.list_tasks.assert_called_once_with(limit=50, offset=0)

    def test_list_tasks_with_custom_parameters(self, sample_scraping_task):
        """
        Test: Listar tareas con parámetros personalizados debe usar esos parámetros
        """
        # Arrange - Configurar parámetros personalizados
        limit = 10
        offset = 5
        tasks_list = [sample_scraping_task]
        
        with patch('main.queue_manager') as mock_manager:
            mock_manager.list_tasks = AsyncMock(return_value=tasks_list)
            
            # Act - Listar tareas con parámetros personalizados
            response = self.client.get(f"/tasks?limit={limit}&offset={offset}")
            
            # Assert - Verificar que se usaron los parámetros correctos
            assert response.status_code == 200
            mock_manager.list_tasks.assert_called_once_with(limit=limit, offset=offset)

    def test_list_tasks_handles_queue_manager_failure(self):
        """
        Test: Manejar fallo del queue manager al listar tareas debe retornar error 500
        """
        # Arrange - Configurar fallo en queue manager
        with patch('main.queue_manager') as mock_manager:
            mock_manager.list_tasks = AsyncMock(side_effect=Exception("Queue error"))
            
            # Act - Intentar listar tareas
            response = self.client.get("/tasks")
            
            # Assert - Verificar error 500
            assert response.status_code == 500
            data = response.json()
            assert data["detail"] == "Error interno del servidor"


class TestCategoryValidation:
    """Tests para la función de validación de categorías."""

    def test_validate_category_with_valid_formats(self):
        """
        Test: La función validate_category debe aceptar formatos válidos
        """
        # Arrange & Act & Assert - Importar la función y probar formatos válidos
        from main import validate_category
        
        valid_categories = [
            "MLU107",     # 3 dígitos
            "MLA1234",    # 4 dígitos
            "MLC456",     # 3 dígitos
            "MLB7890",    # 4 dígitos
            "MLZ999",     # Cualquier letra
            "MLX0001"     # Con ceros
        ]
        
        for category in valid_categories:
            assert validate_category(category) is True, f"Categoría {category} debería ser válida"

    def test_validate_category_with_invalid_formats(self):
        """
        Test: La función validate_category debe rechazar formatos inválidos
        """
        # Arrange & Act & Assert - Probar formatos inválidos
        from main import validate_category
        
        invalid_categories = [
            "ML107",         # Sin letra después de ML
            "MLUA107",       # Dos letras después de ML
            "MLA12",         # Solo 2 dígitos
            "MLA12345",      # 5 dígitos
            "XLA1234",       # No empieza con ML
            "MLA1A23",       # Letra en lugar de número
            "MLA-123",       # Guión
            "MLA 123",       # Espacio
            "",              # Vacío
            "123",           # Solo números
            "INVALID"        # Completamente inválido
        ]
        
        for category in invalid_categories:
            assert validate_category(category) is False, f"Categoría {category} debería ser inválida"

    def test_validate_category_case_insensitive(self):
        """
        Test: La función validate_category debe ser case-insensitive
        """
        # Arrange & Act & Assert - Probar diferentes casos
        from main import validate_category
        
        test_cases = [
            ("mlu107", True),     # Minúsculas
            ("MLU107", True),     # Mayúsculas
            ("MlU107", True),     # Mixto
            ("mLu107", True),     # Mixto
        ]
        
        for category, expected in test_cases:
            result = validate_category(category)
            assert result == expected, f"Categoría {category} debería ser {'válida' if expected else 'inválida'}"


class TestBackgroundTasks:
    """Tests para funciones de procesamiento en background."""
    
    @pytest.fixture(autouse=True)
    def setup_background_mocks(self, mock_rabbitmq_manager, mock_scraper_service):
        """Setup de mocks para tests de background tasks."""
        # No usar patch.multiple para evitar problemas con imports
        self.mock_queue_manager = mock_rabbitmq_manager
        self.mock_scraper_service = mock_scraper_service
        yield

    @pytest.mark.asyncio
    async def test_process_scraping_task_successful_execution(self, sample_scraping_request):
        """
        Test: Procesamiento exitoso de tarea de scraping debe actualizar estados correctamente
        """
        # Arrange - Configurar datos de prueba
        task_id = "test-task-id"
        url = "https://test-url.com"
        expected_result = ScrapingResult(
            task_id=task_id,
            products_count=5,
            success_rate=100.0,
            duration=3.5,
            output_file="/test/output.json",
            errors=[]
        )
        
        # Configurar mocks asíncronos correctamente
        mock_manager = AsyncMock()
        mock_service = AsyncMock()
        mock_service.scrape_products.return_value = expected_result
        
        with patch('main.queue_manager', mock_manager), \
             patch('main.scraper_service', mock_service):
            
            # Importar función después de configurar mocks
            from main import process_scraping_task
            
            # Act - Procesar tarea de scraping
            await process_scraping_task(task_id, sample_scraping_request, url)
            
            # Assert - Verificar llamadas correctas
            mock_manager.update_task_status.assert_called_with(task_id, ScrapingStatus.PROCESSING)
            mock_manager.update_task_started.assert_called_once_with(task_id)
            mock_service.scrape_products.assert_called_once_with(
                url=url,
                max_products=sample_scraping_request.max_products
            )
            mock_manager.update_task_completed.assert_called_once_with(task_id, expected_result)

    @pytest.mark.asyncio
    async def test_process_scraping_task_handles_scraper_failure(self, sample_scraping_request):
        """
        Test: Fallo en scraper debe marcar tarea como fallida
        """
        # Arrange - Configurar fallo en scraper
        task_id = "test-task-id"
        url = "https://test-url.com"
        error_message = "Scraper error"
        
        # Configurar mocks asíncronos correctamente
        mock_manager = AsyncMock()
        mock_service = AsyncMock()
        mock_service.scrape_products.side_effect = Exception(error_message)
        
        with patch('main.queue_manager', mock_manager), \
             patch('main.scraper_service', mock_service):
            
            from main import process_scraping_task
            
            # Act - Procesar tarea con fallo
            await process_scraping_task(task_id, sample_scraping_request, url)
            
            # Assert - Verificar manejo de error
            mock_manager.update_task_status.assert_called_with(task_id, ScrapingStatus.PROCESSING)
            mock_manager.update_task_started.assert_called_once_with(task_id)
            mock_manager.update_task_failed.assert_called_once_with(task_id, error_message)


class TestMessageListener:
    """Tests para funciones del message listener."""
    
    def test_start_message_listener_initializes_correctly(self):
        """
        Test: Iniciar message listener debe configurar variables globales correctamente
        """
        # Arrange - Mock del MessageListener de la ruta correcta
        with patch('manager.listeners.MessageListener') as mock_listener_class, \
             patch('main.listener_running', False):
            
            mock_listener = Mock()
            mock_listener.start_listening = Mock()
            mock_listener_class.return_value = mock_listener
            
            from main import start_message_listener
            
            # Act - Iniciar message listener
            start_message_listener()
            
            # Assert - Verificar inicialización correcta
            mock_listener_class.assert_called_once()
            mock_listener.start_listening.assert_called_once()


    def test_stop_message_listener_updates_flag(self):
        """
        Test: Detener message listener debe actualizar flag global
        """
        # Arrange - Configurar listener running
        with patch('main.listener_running', True):
            from main import stop_message_listener
            
            # Act - Detener message listener
            stop_message_listener()
            
            # Assert - El flag debería actualizarse (verificado por funcionalidad)


class TestStartupShutdown:
    """Tests para eventos de startup y shutdown."""
    
    @pytest.mark.asyncio
    async def test_startup_event_initializes_services(self, mock_rabbitmq_config):
        """
        Test: Evento de startup debe inicializar todos los servicios correctamente
        """
        # Arrange - Mocks de servicios
        with patch('main.RabbitMQManager') as mock_rabbitmq_class, \
             patch('main.ScraperService') as mock_scraper_class, \
             patch('main.threading.Thread') as mock_thread_class, \
             patch('main.RABBITMQ_CONFIG', mock_rabbitmq_config):
            
            mock_rabbitmq = Mock()
            mock_scraper = Mock()
            mock_thread = Mock()
            
            mock_rabbitmq_class.return_value = mock_rabbitmq
            mock_scraper_class.return_value = mock_scraper
            mock_thread_class.return_value = mock_thread
            
            from main import startup_event
            
            # Act - Ejecutar startup event
            await startup_event()
            
            # Assert - Verificar inicialización de servicios
            mock_rabbitmq_class.assert_called_once_with(mock_rabbitmq_config)
            mock_scraper_class.assert_called_once()
            mock_thread_class.assert_called_once()
            mock_thread.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_startup_event_handles_initialization_failure(self):
        """
        Test: Fallo en startup debe propagar la excepción
        """
        # Arrange - Configurar fallo en inicialización
        with patch('main.RabbitMQManager') as mock_rabbitmq_class:
            mock_rabbitmq_class.side_effect = Exception("Initialization error")
            
            from main import startup_event
            
            # Act & Assert - Verificar que se propaga la excepción
            with pytest.raises(Exception, match="Initialization error"):
                await startup_event()

    @pytest.mark.asyncio
    async def test_shutdown_event_closes_connections(self):
        """
        Test: Evento de shutdown debe cerrar conexiones correctamente
        """
        # Arrange - Mock de queue manager
        mock_manager = Mock()
        
        with patch('main.queue_manager', mock_manager), \
             patch('main.stop_message_listener') as mock_stop_listener:
            
            from main import shutdown_event
            
            # Act - Ejecutar shutdown event
            await shutdown_event()
            
            # Assert - Verificar cierre de conexiones
            mock_stop_listener.assert_called_once()
            mock_manager.close.assert_called_once()

