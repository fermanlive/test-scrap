import os
from typing import Optional

class Config:
    """Configuración del servicio publisher"""
    
    # Configuración de FastAPI
    APP_NAME = "Publisher Service"
    APP_VERSION = "1.0.0"
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", "8000"))
    APP_DEBUG = os.getenv("APP_DEBUG", "false").lower() == "true"
    
    # Configuración de RabbitMQ
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
    RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
    RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
    RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "admin123")
    RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/")
    
    # Configuración de colas
    SCRAPING_QUEUE = os.getenv("SCRAPING_QUEUE", "scraping_queue")
    SCRAPING_EXCHANGE = os.getenv("SCRAPING_EXCHANGE", "scraping_exchange")
    SCRAPING_ROUTING_KEY = os.getenv("SCRAPING_ROUTING_KEY", "scraping")
    
    # Configuración de logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configuración de seguridad
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    API_KEY_HEADER = os.getenv("API_KEY_HEADER", "X-API-Key")
    API_KEY = os.getenv("API_KEY", "")
    
    # Configuración de rate limiting
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  # 1 hora
    
    @classmethod
    def get_rabbitmq_url(cls) -> str:
        """Obtener URL de conexión a RabbitMQ"""
        return f"amqp://{cls.RABBITMQ_USER}:{cls.RABBITMQ_PASS}@{cls.RABBITMQ_HOST}:{cls.RABBITMQ_PORT}/{cls.RABBITMQ_VHOST}"
    
    @classmethod
    def validate(cls) -> bool:
        """Validar configuración"""
        required_vars = [
            "RABBITMQ_HOST",
            "RABBITMQ_PORT",
            "RABBITMQ_USER",
            "RABBITMQ_PASS"
        ]
        
        for var in required_vars:
            if not getattr(cls, var):
                return False
        
        return True
