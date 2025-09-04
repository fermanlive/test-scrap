"""
Modelos de datos para el scraper de Mercado Libre Uruguay.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal


@dataclass
class Product:
    """Modelo para representar un producto de Mercado Libre."""
    
    # Información básica
    article_id: str
    title: str
    url: str
    seller: str
    
    # Precios y descuentos
    current_price: Optional[Decimal] = None
    original_price: Optional[Decimal] = None
    discount_percentage: Optional[Decimal] = None
    currency: str = "US$"
    
    # Ratings y reviews
    rating: Optional[float] = None
    review_count: Optional[int] = None
    
    # Disponibilidad
    stock_quantity: Optional[int] = None
    
    # Características
    features: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    description: Optional[str] = None
    
    # Información del vendedor
    seller_location: Optional[str] = None
    shipping_method: Optional[str] = None
    free_shipping: bool = False
    
    # Metadatos
    brand: Optional[str] = None
    
    # Timestamps
    scraped_at: datetime = field(default_factory=datetime.now)

    # Metadatos
    category: Optional[str] = None
    page: Optional[int] = None
    
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir el producto a un diccionario."""
        return {
            "title": self.title,
            "url": self.url,
            "seller": self.seller,
            "current_price": float(self.current_price),
            "original_price": float(self.original_price) if self.original_price else None,
            "discount_percentage": float(self.discount_percentage) if self.discount_percentage else None,
            "currency": self.currency,
            "rating": self.rating,
            "review_count": self.review_count,
            "stock_quantity": self.stock_quantity,
            "features": self.features,
            "images": self.images,
            "seller_location": self.seller_location,
            "shipping_method": self.shipping_method,
            "free_shipping": self.free_shipping,
            "brand": self.brand,
            "scraped_at": self.scraped_at.isoformat(),
        }
