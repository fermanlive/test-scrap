import pytest
import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
import pika
from datetime import datetime

# Agregar el directorio padre al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, get_rabbitmq_connection
from models import ScrapingRequest, PriorityLevel
from config import Config


class TestRabbitMQConnection:
    """Tests para la función get_rabbitmq_connection"""
    
    @patch('main.pika.BlockingConnection')
    @patch('main.pika.PlainCredentials')
    @patch('main.pika.ConnectionParameters')
    def test_get_rabbitmq_connection_success(self, mock_connection_params, mock_credentials, mock_connection):
        """Test conexión exitosa a RabbitMQ"""
        # Arrange
        mock_connection_instance = Mock()
        mock_connection.return_value = mock_connection_instance
        
        # Act
        result = get_rabbitmq_connection()
        
        # Assert
        assert result == mock_connection_instance
        mock_credentials.assert_called_once_with("admin", "admin123")
        mock_connection_params.assert_called_once()
        mock_connection.assert_called_once()
    
    @patch('main.pika.BlockingConnection')
    @patch('main.pika.PlainCredentials')
    @patch('main.pika.ConnectionParameters')
    def test_get_rabbitmq_connection_failure(self, mock_connection_params, mock_credentials, mock_connection):
        """Test fallo en conexión a RabbitMQ"""
        # Arrange
        mock_connection.side_effect = Exception("Connection failed")
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            get_rabbitmq_connection()
        
        assert exc_info.value.status_code == 500
        assert "Error de conexión a RabbitMQ" in str(exc_info.value.detail)


class TestPublishEndpoint:
    """Tests para el endpoint /publish"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.client = TestClient(app)
        self.valid_request = {
            "url": "https://example.com",
            "category": "MLU3312",
            "page": 1,
            "priority": "normal",
            "metadata": {"test": "data"}
        }
    
    @patch('main.get_rabbitmq_connection')
    def test_publish_success(self, mock_get_connection):
        """Test publicación exitosa de mensaje"""
        # Arrange
        mock_connection = Mock()
        mock_channel = Mock()
        mock_connection.channel.return_value = mock_channel
        mock_get_connection.return_value = mock_connection
        
        # Act
        response = self.client.post("/publish", json=self.valid_request)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "published"
        assert data["url"] == "https://example.com"
        
        # Verificar que se llamó a basic_publish
        mock_channel.basic_publish.assert_called_once()
        mock_connection.close.assert_called_once()
    
    @patch('main.get_rabbitmq_connection')
    def test_publish_with_category_and_page(self, mock_get_connection):
        """Test publicación con categoría y página"""
        # Arrange
        mock_connection = Mock()
        mock_channel = Mock()
        mock_connection.channel.return_value = mock_channel
        mock_get_connection.return_value = mock_connection
        
        request = {
            "url": "https://example.com",
            "category": "MLU312",
            "page": 3,
            "priority": "high"
        }
        
        # Act
        response = self.client.post("/publish", json=request)
        
        # Assert
        assert response.status_code == 200
        
        # Verificar que se construyó la URL correctamente
        call_args = mock_channel.basic_publish.call_args
        message_body = json.loads(call_args[1]["body"])
        assert message_body["url"] == "https://example.com?category=MLU312&page=3"
    

    @patch('main.get_rabbitmq_connection')
    def test_publish_priority_mapping(self, mock_get_connection):
        """Test mapeo correcto de prioridades"""
        # Arrange
        mock_connection = Mock()
        mock_channel = Mock()
        mock_connection.channel.return_value = mock_channel
        mock_get_connection.return_value = mock_connection
        
        priority_tests = [
            ("low", 1),
            ("normal", 5),
            ("high", 8),
            ("urgent", 10)
        ]
        
        for priority_str, expected_value in priority_tests:
            request = {
                "url": "https://example.com",
                "category": "test",
                "priority": priority_str
            }
            
            # Act
            response = self.client.post("/publish", json=request)
            
            # Assert
            assert response.status_code == 200
            
            # Verificar prioridad en el mensaje
            call_args = mock_channel.basic_publish.call_args
            message_body = json.loads(call_args[1]["body"])
            assert message_body["priority"] == expected_value
            
            # Verificar prioridad en properties
            properties = call_args[1]["properties"]
            assert properties.priority == expected_value
    
    @patch('main.get_rabbitmq_connection')
    def test_publish_rabbitmq_error(self, mock_get_connection):
        """Test error en RabbitMQ durante publicación"""
        # Arrange
        mock_get_connection.side_effect = HTTPException(status_code=500, detail="Connection failed")
        
        # Act
        response = self.client.post("/publish", json=self.valid_request)
        
        # Assert
        assert response.status_code == 500
    
    def test_publish_invalid_request(self):
        """Test request inválido"""
        # Arrange
        invalid_request = {
            "url": "invalid-url",  # URL inválida
            "category": "",  # Categoría vacía
            "page": -1  # Página negativa
        }
        
        # Act
        response = self.client.post("/publish", json=invalid_request)
        
        # Assert
        assert response.status_code == 422  # Validation error


class TestHealthEndpoint:
    """Tests para el endpoint /health"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.client = TestClient(app)
    
    @patch('main.get_rabbitmq_connection')
    def test_health_check_success(self, mock_get_connection):
        """Test health check exitoso"""
        # Arrange
        mock_connection = Mock()
        mock_channel = Mock()
        mock_connection.channel.return_value = mock_channel
        mock_get_connection.return_value = mock_connection
        
        # Mock queue info
        mock_queue_info = Mock()
        mock_queue_info.method.message_count = 5
        mock_channel.queue_declare.return_value = mock_queue_info
        
        # Act
        response = self.client.get("/health")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["rabbitmq"] == "connected"
        assert data["queue"] == Config.SCRAPING_QUEUE
        assert data["exchange"] == Config.SCRAPING_EXCHANGE
        assert data["routing_key"] == Config.SCRAPING_ROUTING_KEY
        assert data["queue_messages"] == 5
        
        mock_connection.close.assert_called_once()
    
    @patch('main.get_rabbitmq_connection')
    def test_health_check_rabbitmq_error(self, mock_get_connection):
        """Test health check con error en RabbitMQ"""
        # Arrange
        mock_get_connection.side_effect = Exception("RabbitMQ connection failed")
        
        # Act
        response = self.client.get("/health")
        
        # Assert
        assert response.status_code == 200  # Health endpoint no lanza excepción
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["rabbitmq"] == "disconnected"
        assert "RabbitMQ connection failed" in data["error"]


class TestDiagnoseEndpoint:
    """Tests para el endpoint /diagnose"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.client = TestClient(app)
    
    @patch('main.get_rabbitmq_connection')
    def test_diagnose_success(self, mock_get_connection):
        """Test diagnóstico exitoso"""
        # Arrange
        mock_connection = Mock()
        mock_channel = Mock()
        mock_connection.channel.return_value = mock_channel
        mock_get_connection.return_value = mock_connection
        
        # Mock queue info
        mock_queue_info = Mock()
        mock_queue_info.method.message_count = 10
        mock_queue_info.method.consumer_count = 2
        mock_channel.queue_declare.return_value = mock_queue_info
        
        # Act
        response = self.client.get("/diagnose")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        
        # Verificar información de la cola
        assert data["queue"]["name"] == Config.SCRAPING_QUEUE
        assert data["queue"]["exists"] is True
        assert data["queue"]["durable"] is True
        assert data["queue"]["messages"] == 10
        assert data["queue"]["consumers"] == 2
        
        # Verificar información del exchange
        assert data["exchange"]["name"] == Config.SCRAPING_EXCHANGE
        assert data["exchange"]["exists"] is True
        assert data["exchange"]["type"] == "direct"
        
        # Verificar binding
        assert data["binding"]["exchange"] == Config.SCRAPING_EXCHANGE
        assert data["binding"]["queue"] == Config.SCRAPING_QUEUE
        assert data["binding"]["routing_key"] == Config.SCRAPING_ROUTING_KEY
        assert data["binding"]["exists"] is True
        
        mock_connection.close.assert_called_once()
    
    @patch('main.get_rabbitmq_connection')
    def test_diagnose_rabbitmq_error(self, mock_get_connection):
        """Test diagnóstico con error en RabbitMQ"""
        # Arrange
        mock_get_connection.side_effect = Exception("Diagnosis failed")
        
        # Act
        response = self.client.get("/diagnose")
        
        # Assert
        assert response.status_code == 200  # Diagnose endpoint no lanza excepción
        data = response.json()
        assert data["status"] == "error"
        assert "Diagnosis failed" in data["error"]


class TestRootEndpoint:
    """Tests para el endpoint raíz /"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """Test endpoint raíz"""
        # Act
        response = self.client.get("/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Publisher Service"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
        assert data["endpoints"]["publish"] == "/publish"
        assert data["endpoints"]["health"] == "/health"


class TestStartupEvent:
    """Tests para el evento startup"""
    
    @patch('main.get_rabbitmq_connection')
    def test_startup_event_success(self, mock_get_connection):
        """Test evento startup exitoso"""
        # Arrange
        mock_connection = Mock()
        mock_channel = Mock()
        mock_connection.channel.return_value = mock_channel
        mock_get_connection.return_value = mock_connection
        
        # Act
        from main import startup_event
        import asyncio
        asyncio.run(startup_event())
        
        # Assert
        mock_get_connection.assert_called_once()
        mock_channel.queue_declare.assert_called_once_with(
            queue=Config.SCRAPING_QUEUE,
            durable=True,
            arguments={'x-max-priority': 10}
        )
        mock_channel.exchange_declare.assert_called_once_with(
            exchange=Config.SCRAPING_EXCHANGE,
            exchange_type='direct',
            durable=True
        )
        mock_channel.queue_bind.assert_called_once_with(
            exchange=Config.SCRAPING_EXCHANGE,
            queue=Config.SCRAPING_QUEUE,
            routing_key=Config.SCRAPING_ROUTING_KEY
        )
        mock_connection.close.assert_called_once()
    
    @patch('main.get_rabbitmq_connection')
    def test_startup_event_error(self, mock_get_connection):
        """Test evento startup con error"""
        # Arrange
        mock_get_connection.side_effect = Exception("Startup failed")
        
        # Act
        from main import startup_event
        import asyncio
        
        # No debería lanzar excepción, solo imprimir error
        asyncio.run(startup_event())
        
        # Assert
        mock_get_connection.assert_called_once()


class TestMessageFormatting:
    """Tests para el formato de mensajes"""
    
    @patch('main.get_rabbitmq_connection')
    def test_message_format_with_metadata(self, mock_get_connection):
        """Test formato de mensaje con metadatos"""
        # Arrange
        mock_connection = Mock()
        mock_channel = Mock()
        mock_connection.channel.return_value = mock_channel
        mock_get_connection.return_value = mock_connection
        
        client = TestClient(app)
        request = {
            "url": "https://example.com",
            "category": "test",
            "page": 2,
            "priority": "high",
            "metadata": {"key1": "value1", "key2": 123}
        }
        
        # Act
        response = client.post("/publish", json=request)
        
        # Assert
        assert response.status_code == 200
        
        # Verificar formato del mensaje
        call_args = mock_channel.basic_publish.call_args
        message_body = json.loads(call_args[1]["body"])
        
        assert message_body["url"] == "https://example.com?category=test&page=2"
        assert message_body["category"] == "test"
        assert message_body["page"] == 2
        assert message_body["priority"] == 8  # high priority
        assert message_body["metadata"] == {"key1": "value1", "key2": 123}
        assert "timestamp" in message_body
        
        # Verificar properties
        properties = call_args[1]["properties"]
        assert properties.app_id == "scraping_publisher"
        assert properties.delivery_mode == 2  # Persistente
        assert properties.priority == 8
    
    @patch('main.get_rabbitmq_connection')
    def test_message_id_generation(self, mock_get_connection):
        """Test generación de message_id"""
        # Arrange
        mock_connection = Mock()
        mock_channel = Mock()
        mock_connection.channel.return_value = mock_channel
        mock_get_connection.return_value = mock_connection
        
        client = TestClient(app)
        request = {
            "url": "https://example.com",
            "category": "test"
        }
        
        # Act
        response = client.post("/publish", json=request)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Verificar que el message_id se genera basado en el hash de la URL
        expected_message_id = f"msg_{hash('https://example.com')}"
        assert data["message_id"] == expected_message_id


class TestCORSConfiguration:
    """Tests para configuración CORS"""
    
    def test_cors_headers(self):
        """Test que CORS esté configurado correctamente"""
        # Arrange
        client = TestClient(app)
        
        # Act
        response = client.options("/publish")
        
        # Assert
        # FastAPI maneja CORS automáticamente, verificar que no hay errores
        assert response.status_code in [200, 405]  # 405 si el método no está permitido


class TestErrorHandling:
    """Tests para manejo de errores"""
    
    @patch('main.get_rabbitmq_connection')
    def test_connection_error_handling(self, mock_get_connection):
        """Test manejo de errores de conexión"""
        # Arrange
        mock_get_connection.side_effect = Exception("Network error")
        client = TestClient(app)
        
        # Act
        response = client.post("/publish", json={
            "url": "https://example.com",
            "category": "test"
        })
        
        # Assert
        assert response.status_code == 500
        assert "Network error" in response.json()["detail"]
    
    def test_validation_error_handling(self):
        """Test manejo de errores de validación"""
        # Arrange
        client = TestClient(app)
        invalid_request = {
            "url": "not-a-url",
            "category": "",
            "page": -1
        }
        
        # Act
        response = client.post("/publish", json=invalid_request)
        
        # Assert
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert len(errors) > 0  # Debe haber errores de validación


# Fixtures adicionales para tests específicos
@pytest.fixture
def mock_rabbitmq_connection():
    """Fixture para mock de conexión RabbitMQ"""
    with patch('main.get_rabbitmq_connection') as mock:
        mock_connection = Mock()
        mock_channel = Mock()
        mock_connection.channel.return_value = mock_channel
        mock.return_value = mock_connection
        yield mock, mock_connection, mock_channel


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
