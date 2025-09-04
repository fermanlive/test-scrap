"""
Modelos de datos para la API de scraping.
"""

from typing import Optional, List
from pydantic import BaseModel, validator
import re
from enum import Enum


class ScrapingStatus(str, Enum):
    """Estados posibles de una tarea de scraping."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ScrapingRequest(BaseModel):
    """Modelo para solicitudes de scraping."""
    url: str
    category: str
    page: int
    max_products: int
    
    @validator('url')
    def validate_url(cls, v):
        """Validar que la URL sea válida."""
        if not v or not v.startswith('http'):
            raise ValueError('La URL debe ser válida y comenzar con http/https')
        return v
    
    @validator('category')
    def validate_category(cls, v):
        """Validar formato de categoría ML[A-Z][0-9]{3,4}."""
        if not re.match(r'^ML[A-Z]\d{3,4}$', v.upper()):
            raise ValueError('La categoría debe tener el formato ML[A-Z][0-9]{3,4} (ej: MLU107, MLA1234)')
        return v.upper()
    
    @validator('page')
    def validate_page(cls, v):
        """Validar número de página."""
        if v < 1:
            raise ValueError('La página debe ser mayor a 0')
        return v
    
    @validator('max_products')
    def validate_max_products(cls, v):
        """Validar cantidad máxima de productos."""
        if v < 1 or v > 1000:
            raise ValueError('La cantidad de productos debe estar entre 1 y 1000')
        return v


class ScrapingResponse(BaseModel):
    """Modelo para respuestas de scraping."""
    task_id: str
    status: ScrapingStatus
    message: str
    url: str
    category: str
    page: int
    max_products: int


class ScrapingTask(BaseModel):
    """Modelo para tareas de scraping en cola."""
    id: str
    request: ScrapingRequest
    status: ScrapingStatus
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    result_file: Optional[str] = None


class ScrapingResult(BaseModel):
    """Modelo para resultados de scraping."""
    task_id: str
    products_count: int
    success_rate: float
    duration: float
    output_file: str
    errors: List[str] = []


class HealthCheck(BaseModel):
    """Modelo para verificación de salud del sistema."""
    status: str
    timestamp: str
    version: str
    rabbitmq_connected: bool
    scraper_available: bool
