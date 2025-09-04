from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional
from enum import Enum

class PriorityLevel(str, Enum):
    """Niveles de prioridad para las tareas de scraping"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class ScrapingRequest(BaseModel):
    """Modelo para solicitudes de scraping"""
    url: str = Field(..., description="URL a scrapear")
    category: str = Field(..., description="Categoría del contenido")
    page: int = Field(default=1, description="Página a scrapear")
    priority: PriorityLevel = Field(default=PriorityLevel.NORMAL, description="Prioridad de la tarea")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos adicionales")
    
    @validator('url')
    def validate_url(cls, v):
        """Validar que la URL sea válida"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('La URL debe comenzar con http:// o https://')
        return v
    
    @validator('category')
    def validate_category(cls, v):
        """Validar que la categoría no esté vacía"""
        if not v.strip():
            raise ValueError('La categoría no puede estar vacía')
        return v.strip()
    
    @validator('page')
    def validate_page(cls, v):
        """Validar que la página sea un numero entero positivo """
        if v is not None and v <= 0:
            raise ValueError('La página debe ser un número entero positivo')
        return v

class ScrapingResponse(BaseModel):
    """Modelo para respuestas de scraping"""
    message_id: str = Field(..., description="ID único del mensaje")
    status: str = Field(..., description="Estado de la publicación")
    url: str = Field(..., description="URL que se va a scrapear")
    timestamp: str = Field(..., description="Timestamp de la publicación")
    priority: PriorityLevel = Field(..., description="Prioridad asignada")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg_12345",
                "status": "published",
                "url": "https://ejemplo.com",
                "timestamp": "2024-01-01T00:00:00Z",
                "priority": "normal"
            }
        }

class HealthResponse(BaseModel):
    """Modelo para respuestas de salud del servicio"""
    status: str = Field(..., description="Estado del servicio")
    service: str = Field(..., description="Nombre del servicio")
    version: str = Field(..., description="Versión del servicio")
    rabbitmq: str = Field(..., description="Estado de conexión con RabbitMQ")
    timestamp: str = Field(..., description="Timestamp de la verificación")

class ErrorResponse(BaseModel):
    """Modelo para respuestas de error"""
    error: str = Field(..., description="Descripción del error")
    detail: Optional[str] = Field(None, description="Detalles adicionales del error")
    timestamp: str = Field(..., description="Timestamp del error")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "Error de validación",
                "detail": "La URL proporcionada no es válida",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }

class ScrapingMetadata(BaseModel):
    """Modelo para metadatos de scraping"""
    max_products: Optional[int] = Field(None, description="Número máximo de productos a extraer")
    headless: bool = Field(default=True, description="Ejecutar en modo headless")
    profile: str = Field(default="stealth", description="Perfil de navegación")
    delay: float = Field(default=2.0, description="Delay entre requests en segundos")
    timeout: int = Field(default=30000, description="Timeout del navegador en ms")
    output_format: str = Field(default="json", description="Formato de salida")
    
    @validator('max_products')
    def validate_max_products(cls, v):
        """Validar número máximo de productos"""
        if v is not None and v <= 0:
            raise ValueError('El número máximo de productos debe ser mayor a 0')
        return v
    
    @validator('delay')
    def validate_delay(cls, v):
        """Validar delay entre requests"""
        if v < 0:
            raise ValueError('El delay no puede ser negativo')
        return v
    
    @validator('timeout')
    def validate_timeout(cls, v):
        """Validar timeout del navegador"""
        if v <= 0:
            raise ValueError('El timeout debe ser mayor a 0')
        return v
