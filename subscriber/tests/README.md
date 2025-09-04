# Tests Unitarios y de Integración - Main.py

Este directorio contiene tests completos para `main.py` siguiendo metodología **TDD (Test-Driven Development)** y el patrón **AAA (Arrange, Act, Assert)**.

## 📋 Estructura de Tests

### `conftest.py`
Configuración global de fixtures y mocks para todos los tests:
- **Fixtures de modelos**: `sample_scraping_request`, `sample_scraping_task`, etc.
- **Mocks de servicios**: `mock_rabbitmq_manager`, `mock_scraper_service`
- **Configuraciones mock**: `mock_api_config`, `mock_valid_categories`

### `test_main.py`
Tests unitarios principales organizados en clases:

#### `TestMainAPI`
Tests para endpoints de la API REST:
- ✅ `test_root_endpoint_returns_correct_response`
- ✅ `test_health_check_healthy_when_all_services_available`
- ✅ `test_health_check_unhealthy_when_rabbitmq_disconnected`
- ✅ `test_health_check_unhealthy_when_scraper_unavailable`
- ✅ `test_health_check_handles_exceptions_gracefully`
- ✅ `test_listener_status_returns_correct_information`
- ✅ `test_get_categories_returns_valid_categories`
- ✅ `test_create_scraping_task_with_valid_request`
- ✅ `test_create_scraping_task_with_invalid_category`
- ✅ `test_create_scraping_task_handles_queue_manager_failure`
- ✅ `test_get_task_status_with_existing_task`
- ✅ `test_get_task_status_with_nonexistent_task`
- ✅ `test_get_task_status_handles_queue_manager_failure`
- ✅ `test_list_tasks_with_default_parameters`
- ✅ `test_list_tasks_with_custom_parameters`
- ✅ `test_list_tasks_handles_queue_manager_failure`

#### `TestBackgroundTasks`
Tests para procesamiento en background:
- ✅ `test_process_scraping_task_successful_execution`
- ✅ `test_process_scraping_task_handles_scraper_failure`

#### `TestMessageListener`
Tests para message listener:
- ✅ `test_start_message_listener_initializes_correctly`
- ✅ `test_start_message_listener_handles_exceptions`
- ✅ `test_stop_message_listener_updates_flag`

#### `TestStartupShutdown`
Tests para eventos del ciclo de vida:
- ✅ `test_startup_event_initializes_services`
- ✅ `test_startup_event_handles_initialization_failure`
- ✅ `test_shutdown_event_closes_connections`

#### `TestStartAPI`
Tests para inicialización de la API:
- ✅ `test_start_api_calls_uvicorn_with_correct_config`

### `test_main_integration.py`
Tests de integración entre componentes:

#### `TestMainIntegration`
Tests de flujos completos:
- ✅ `test_complete_scraping_workflow_integration`
- ✅ `test_health_check_integration_with_all_components`
- ✅ `test_error_handling_integration_across_components`
- ✅ `test_listener_status_integration_with_threading`
- ✅ `test_categories_integration_with_validation`
- ✅ `test_background_task_integration`

#### `TestMainPerformance`
Tests de rendimiento y carga:
- ✅ `test_multiple_concurrent_requests_performance`
- ✅ `test_health_check_response_time_consistency`
- ✅ `test_large_task_list_pagination_performance`

## 🧪 Metodología TDD

### Patrón AAA (Arrange, Act, Assert)

Cada test sigue estrictamente el patrón AAA:

```python
def test_example_following_aaa_pattern(self):
    """
    Test: Descripción clara de lo que se está probando
    
    """
    # Arrange - Configurar datos y mocks necesarios
    expected_value = "expected"
    mock_service.setup_method.return_value = expected_value
    
    # Act - Ejecutar la funcionalidad que se está probando
    result = service_under_test.method_to_test()
    
    # Assert - Verificar que el resultado es el esperado
    assert result == expected_value
    mock_service.setup_method.assert_called_once()
```

### Ciclo TDD

1. **🔴 Red**: Escribir test que falle inicialmente
2. **🟢 Green**: Implementar código mínimo para que pase
3. **🔄 Refactor**: Mejorar el código manteniendo los tests verdes

## 🛠️ Tecnologías Utilizadas

- **pytest**: Framework principal de testing
- **pytest-asyncio**: Para tests asíncronos
- **FastAPI TestClient**: Para tests de endpoints
- **unittest.mock**: Para mocking y patching
- **fixtures**: Para reutilización de datos de prueba

## 🚀 Ejecutar Tests

### Todos los tests:
```bash
poetry run pytest tests/test_main.py -v
```

### Tests específicos:
```bash
# Solo tests unitarios
poetry run pytest tests/test_main.py::TestMainAPI -v

# Solo tests de integración
poetry run pytest tests/test_main_integration.py -v

# Test específico
poetry run pytest tests/test_main.py::TestMainAPI::test_root_endpoint_returns_correct_response -v
```

### Con cobertura:
```bash
poetry run pytest tests/test_main.py --cov=main --cov-report=html
```

### En modo verbose:
```bash
poetry run pytest tests/test_main.py -v -s
```

## 📊 Cobertura de Tests

Los tests cubren:

### ✅ Endpoints HTTP
- `GET /` - Endpoint raíz
- `GET /health` - Health check
- `GET /listener/status` - Estado del listener
- `POST /scrape` - Crear tarea de scraping
- `GET /tasks/{task_id}` - Obtener tarea específica
- `GET /tasks` - Listar tareas
- `GET /categories` - Obtener categorías

### ✅ Funciones de Background
- `process_scraping_task` - Procesamiento de tareas
- `start_message_listener` - Iniciar listener
- `stop_message_listener` - Detener listener

### ✅ Eventos del Ciclo de Vida
- `startup_event` - Inicialización de servicios
- `shutdown_event` - Cierre de conexiones
- `start_api` - Inicialización con uvicorn

### ✅ Manejo de Errores
- Errores de validación (400)
- Recursos no encontrados (404)
- Errores internos (500)
- Excepciones en servicios

### ✅ Casos Edge
- Servicios no disponibles
- Fallos de conectividad
- Datos inválidos
- Condiciones de concurrencia

## 🔧 Mocks y Fixtures

### Principales Mocks:
- **RabbitMQManager**: Gestión de colas
- **ScraperService**: Servicio de scraping
- **MessageListener**: Listener de mensajes
- **Threading**: Sistema de hilos
- **UUID**: Generación de IDs únicos

### Fixtures Reutilizables:
- `sample_scraping_request`: Request válido
- `sample_scraping_task`: Tarea de ejemplo
- `mock_api_config`: Configuración de API
- `mock_valid_categories`: Categorías válidas

## 📈 Beneficios de esta Estructura

1. **Cobertura Completa**: Cubre todos los endpoints y funcionalidades
2. **Mantenibilidad**: Tests organizados y bien documentados
3. **Reutilización**: Fixtures y mocks reutilizables
4. **Aislamiento**: Cada test es independiente
5. **Performance**: Tests de rendimiento incluidos
6. **Integración**: Tests que verifican interacciones entre componentes
7. **Documentación**: Cada test documenta el comportamiento esperado

## 🔍 Casos de Uso Cubiertos

- ✅ Creación exitosa de tareas de scraping
- ✅ Validación de categorías inválidas
- ✅ Manejo de errores del queue manager
- ✅ Verificación del estado de salud del sistema
- ✅ Procesamiento en background de tareas
- ✅ Gestión del ciclo de vida de la aplicación
- ✅ Manejo de fallos en servicios externos
- ✅ Paginación de listas grandes
- ✅ Requests concurrentes
- ✅ Integración entre componentes
