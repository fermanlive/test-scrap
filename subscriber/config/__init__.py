"""
Configuraciones del sistema de scraping de Mercado Libre Uruguay.
"""

from .api_config import API_CONFIG, RABBITMQ_CONFIG
from .scraper_config import SCRAPER_CONFIG, SELECTORS, RATE_LIMIT_CONFIG, RETRY_CONFIG
from .categories_config import VALID_CATEGORIES
from .monitoring_config import MONITORING_CONFIG

__all__ = [
    "API_CONFIG",
    "RABBITMQ_CONFIG", 
    "SCRAPER_CONFIG",
    "SELECTORS",
    "RATE_LIMIT_CONFIG",
    "RETRY_CONFIG",
    "VALID_CATEGORIES",
    "MONITORING_CONFIG"
]
