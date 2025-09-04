"""
Configuración de la API para el sistema de scraping de Mercado Libre Uruguay.
"""

import os
from pathlib import Path

# Directorio base del proyecto
BASE_DIR = Path(__file__).parent.parent

# Configuración de la API
API_CONFIG = {
    "title": "Mercado Libre Uruguay Scraping API",
    "description": "API para scraping automatizado de productos de Mercado Libre Uruguay",
    "version": "1.0.0",
    "host": os.getenv("API_HOST", "0.0.0.0"),
    "port": int(os.getenv("API_PORT", "8000")),
    "debug": os.getenv("API_DEBUG", "false").lower() == "true"
}

# Configuración de RabbitMQ
RABBITMQ_CONFIG = {
    "host": os.getenv("RABBITMQ_HOST", "localhost"),
    "port": int(os.getenv("RABBITMQ_PORT", "5672")),
    "user": os.getenv("RABBITMQ_USER", "admin"),
    "password": os.getenv("RABBITMQ_PASS", "admin123"),
    "vhost": os.getenv("RABBITMQ_VHOST", "/"),
    "queue": os.getenv("SCRAPING_QUEUE", "scraping_queue"),
    "exchange": os.getenv("SCRAPING_EXCHANGE", "scraping_exchange"),
    "routing_key": os.getenv("SCRAPING_ROUTING_KEY", "scraping")
}

# Configuración del scraper
SCRAPER_CONFIG = {
    "base_url": "https://www.mercadolibre.com.uy/ofertas",
    "log_dir": BASE_DIR / "logs",
    "output_dir": BASE_DIR / "output",
    "max_workers": int(os.getenv("MAX_WORKERS", "3")),
    "max_retries": int(os.getenv("MAX_RETRIES", "3")),
    "retry_delay": int(os.getenv("RETRY_DELAY", "5")),
    "browser_headless": os.getenv("BROWSER_HEADLESS", "true").lower() == "true",
    "browser_timeout": int(os.getenv("BROWSER_TIMEOUT", "30000")),
    "rate_limit_delay": float(os.getenv("RATE_LIMIT_DELAY", "2.0"))
}

# Configuración de monitoreo
MONITORING_CONFIG = {
    "enable_metrics": os.getenv("ENABLE_METRICS", "true").lower() == "true",
    "metrics_interval": int(os.getenv("METRICS_INTERVAL", "60")),
    "performance_thresholds": {
        "max_extraction_time": int(os.getenv("MAX_EXTRACTION_TIME", "300")),
        "min_success_rate": float(os.getenv("MIN_SUCCESS_RATE", "80.0")),
        "max_error_rate": float(os.getenv("MAX_ERROR_RATE", "20.0"))
    }
}
