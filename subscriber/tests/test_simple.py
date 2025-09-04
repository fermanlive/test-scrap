"""
Test simple para verificar que la configuración básica funciona.
"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


def test_can_import_main():
    """Test básico: Verificar que se puede importar main sin errores."""
    # Arrange & Act
    try:
        import main
        # Assert
        assert hasattr(main, 'app')
        assert hasattr(main, 'startup_event')
        assert hasattr(main, 'shutdown_event')
    except ImportError as e:
        pytest.fail(f"No se pudo importar main: {e}")


def test_app_creation():
    """Test básico: Verificar que la app de FastAPI se crea correctamente."""
    # Arrange - Mock de configuraciones
    mock_api_config = {
        "title": "Mercado Libre Uruguay Scraping API",
        "description": "Test Description",
        "version": "1.0.0"
    }
    
    mock_scraper_config = {
        "log_dir": "/tmp/logs"
    }
    
    # Act & Assert
    with patch('main.API_CONFIG', mock_api_config), \
         patch('main.SCRAPER_CONFIG', mock_scraper_config), \
         patch('main.logger'):
        
        import main
        assert main.app is not None
        assert main.app.title == mock_api_config["title"]


def test_basic_endpoint_without_dependencies():
    """Test básico: Verificar endpoint raíz sin dependencias."""
    # Arrange
    mock_api_config = {
        "title": "Test API",
        "description": "Test Description", 
        "version": "1.0.0"
    }
    
    mock_scraper_config = {
        "log_dir": "/tmp/logs"
    }
    
    # Act
    with patch('main.API_CONFIG', mock_api_config), \
         patch('main.SCRAPER_CONFIG', mock_scraper_config), \
         patch('main.logger'):
        
        import main
        client = TestClient(main.app)
        response = client.get("/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Mercado Libre Uruguay Scraping API"
        assert data["version"] == mock_api_config["version"]


def test_health_endpoint_basic():
    """Test básico: Verificar health endpoint básico."""
    # Arrange
    mock_api_config = {
        "title": "Test API", 
        "description": "Test Description",
        "version": "1.0.0"
    }
    
    mock_scraper_config = {
        "log_dir": "/tmp/logs"
    }
    
    # Mock de servicios como None (sin inicializar)
    with patch('main.API_CONFIG', mock_api_config), \
         patch('main.SCRAPER_CONFIG', mock_scraper_config), \
         patch('main.logger'), \
         patch('main.queue_manager', None), \
         patch('main.scraper_service', None), \
         patch('main.listener_thread', None):
        
        import main
        client = TestClient(main.app)
        
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"  # Sin servicios inicializados
        assert data["version"] == mock_api_config["version"]
        assert data["rabbitmq_connected"] is False
        assert data["scraper_available"] is False
