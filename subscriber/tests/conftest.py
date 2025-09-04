"""
Configuración global para tests.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime

from models import (
    ScrapingRequest, ScrapingResponse, ScrapingTask, 
    ScrapingResult, HealthCheck, ScrapingStatus
)
# Importar Product solo si está disponible
try:
    from scraper.models.models import Product
except ImportError:
    # Crear una clase Product simple para tests
    class Product:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)


@pytest.fixture
def event_loop():
    """Fixture para el event loop de asyncio."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_rabbitmq_manager():
    """Mock del RabbitMQManager."""
    manager = Mock()
    manager.connected = True
    manager.add_task = AsyncMock(return_value=True)
    manager.get_task = AsyncMock(return_value=None)
    manager.list_tasks = AsyncMock(return_value=[])
    manager.update_task_status = AsyncMock(return_value=True)
    manager.update_task_started = AsyncMock(return_value=True)
    manager.update_task_completed = AsyncMock(return_value=True)
    manager.update_task_failed = AsyncMock(return_value=True)
    manager.close = Mock()
    return manager


@pytest.fixture
def mock_scraper_service():
    """Mock del ScraperService."""
    service = Mock()
    service.is_available = Mock(return_value=True)
    service.scrape_products = AsyncMock(return_value=ScrapingResult(
        task_id="test-task-id",
        products_count=10,
        success_rate=100.0,
        duration=5.5,
        output_file="/test/output.json",
        errors=[]
    ))
    return service


@pytest.fixture
def sample_scraping_request():
    """Muestra de ScrapingRequest válida."""
    return ScrapingRequest(
        url="https://listado.mercadolibre.com.uy/MLU1144",
        category="MLU1144",
        page=1,
        max_products=10
    )


@pytest.fixture  
def sample_scraping_task():
    """Muestra de ScrapingTask válida."""
    return ScrapingTask(
        id="test-task-id",
        request=ScrapingRequest(
            url="https://listado.mercadolibre.com.uy/MLU1144",
            category="MLU1144", 
            page=1,
            max_products=10
        ),
        status=ScrapingStatus.PENDING,
        created_at=datetime.utcnow().isoformat()
    )


@pytest.fixture
def sample_scraping_response():
    """Muestra de ScrapingResponse válida."""
    return ScrapingResponse(
        task_id="test-task-id",
        status=ScrapingStatus.PENDING,
        message="Tarea de scraping creada exitosamente",
        url="https://listado.mercadolibre.com.uy/MLU1144",
        category="MLU1144",
        page=1,
        max_products=10
    )


@pytest.fixture
def mock_api_config():
    """Mock de configuración de API."""
    return {
        "title": "Test API",
        "description": "Test Description", 
        "version": "1.0.0",
        "host": "localhost",
        "port": 8000,
        "debug": True
    }


@pytest.fixture
def mock_scraper_config():
    """Mock de configuración del scraper."""
    from pathlib import Path
    return {
        "base_url": "https://listado.mercadolibre.com.uy",
        "log_dir": Path("/tmp/logs"),
        "output_dir": Path("/tmp/output")
    }





@pytest.fixture
def mock_rabbitmq_config():
    """Mock de configuración de RabbitMQ."""
    return {
        "host": "localhost",
        "port": 5672,
        "user": "test_user",
        "password": "test_password", 
        "vhost": "/",
        "queue": "test_queue",
        "exchange": "test_exchange",
        "routing_key": "test_routing"
    }


# ==================== MANAGER MODULE FIXTURES ====================

@pytest.fixture
def mock_pika_connection():
    """Mock de conexión pika."""
    connection = Mock()
    channel = Mock()
    connection.channel.return_value = channel
    channel.queue_declare.return_value = Mock(method=Mock(message_count=0))
    channel.basic_get.return_value = (None, None, None)
    return connection, channel


@pytest.fixture
def sample_product():
    """Muestra de Product válido."""
    return Product(
        title="Notebook Dell Inspiron 15",
        url="https://articulo.mercadolibre.com.uy/MLU-123456789",
        seller="TechStore",
        current_price=45990.0,
        original_price=52990.0,
        currency="UYU",
        rating=4.5,
        review_count=150,
        seller_location="Montevideo",
        shipping_method="Envío gratis",
        free_shipping=True,
        features=["RAM: 8GB", "Storage: 256GB SSD"],
        images=["https://http2.mlstatic.com/test-image.jpg"]
    )


@pytest.fixture  
def sample_product_list(sample_product):
    """Lista de productos de muestra."""
    products = []
    for i in range(3):
        product = Product(
            title=f"Producto {i+1}",
            url=f"https://articulo.mercadolibre.com.uy/MLU-12345678{i}",
            seller=f"Seller{i+1}",
            current_price=1000.0 * (i+1),
            original_price=1200.0 * (i+1),
            currency="UYU",
            rating=4.0 + i * 0.1,
            review_count=100 + i * 10,
            seller_location="Montevideo",
            shipping_method="Envío gratis",
            free_shipping=True,
            features=[f"Feature {i+1}"],
            images=[f"https://http2.mlstatic.com/test-image-{i}.jpg"]
        )
        products.append(product)
    return products


# ==================== SCRAPER MODULE FIXTURES ====================

@pytest.fixture
def mock_browser_manager():
    """Mock del BrowserManager."""
    browser = Mock()
    browser.get_page = AsyncMock()
    browser.close = AsyncMock()
    return browser


@pytest.fixture
def mock_rate_limiter():
    """Mock del RateLimiter."""
    limiter = Mock()
    limiter.acquire = AsyncMock()
    limiter.release = Mock()
    limiter.get_stats.return_value = {
        "total_requests": 10,
        "successful_requests": 8,
        "failed_requests": 2,
        "average_delay": 1.5
    }
    return limiter


@pytest.fixture
def mock_database_connector():
    """Mock del DatabaseConnector."""
    connector = Mock()
    connector.insert_products = Mock(return_value=True)
    connector.get_products = Mock(return_value=[])
    connector.close = Mock()
    return connector


@pytest.fixture
def sample_scraping_result(sample_product_list):
    """Resultado de scraping de muestra."""
    return ScrapingResult(
        task_id="test-task-123",
        products_count=len(sample_product_list),
        success_rate=100.0,
        duration=15.5,
        output_file="/tmp/test_output.json",
        errors=[]
    )
