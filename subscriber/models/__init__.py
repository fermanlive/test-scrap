"""
Modelos de datos para la aplicación.
"""

from .scraping_models import (
    ScrapingRequest,
    ScrapingResponse, 
    ScrapingTask,
    ScrapingResult,
    ScrapingStatus,
    HealthCheck
)

__all__ = [
    'ScrapingRequest',
    'ScrapingResponse',
    'ScrapingTask', 
    'ScrapingResult',
    'ScrapingStatus',
    'HealthCheck'
]
