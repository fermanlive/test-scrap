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


@dataclass
class ScrapingResult:
    """Resultado del proceso de scraping."""
    
    products: List[Product]
    total_products: int
    successful_scrapes: int
    failed_scrapes: int
    start_time: datetime
    end_time: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calcular la tasa de éxito del scraping."""
        if self.total_products == 0:
            return 0.0
        return (self.successful_scrapes / self.total_products) * 100
    
    @property
    def duration(self) -> Optional[float]:
        """Calcular la duración del scraping en segundos."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir el resultado a un diccionario."""
        return {
            "total_products": self.total_products,
            "successful_scrapes": self.successful_scrapes,
            "failed_scrapes": self.failed_scrapes,
            "success_rate": self.success_rate,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "errors": self.errors,
            "products": [product.to_dict() for product in self.products],
        }


@dataclass
class ScrapingConfig:
    """Configuración para el proceso de scraping."""
    
    # URLs
    base_url: str = "https://www.mercadolibre.com.uy"
    offers_url: str = "https://www.mercadolibre.com.uy/ofertas"
    
    # Configuración del navegador
    headless: bool = False
    timeout: int = 30000
    viewport_width: int = 1920
    viewport_height: int = 1080
    
    # Configuración del scraper
    max_products: int = 100
    delay_between_requests: float = 2.0
    retry_attempts: int = 3
    
    # Configuración de salida
    output_format: str = "csv"
    output_dir: str = "output"
    
    # Selectores CSS (actualizados según la estructura real de ML)
    selectors: Dict[str, str] = field(default_factory=lambda: {
        "product_card": "li.ui-search-layout__item",
        "product_title": "h2.ui-search-item__title",
        "product_price": "span.andes-money-amount__fraction",
        "product_original_price": "span.andes-money-amount--previous",
        "product_discount": "span.ui-search-price__discount",
        "product_seller": "span.andes-money-amount__cents",
        "product_rating": "span.ui-search-reviews__rating-number",
        "product_reviews": "span.ui-search-reviews__amount",
        "product_image": "img.ui-search-result-image__element",
        "product_link": "a.ui-search-item__group__element",
        "product_features": "div.ui-search-item__group--attributes",
        "product_stock": "span.ui-search-item__stock",
        "product_shipping": "span.ui-search-item__shipping",
        
        # Selectores adicionales para información específica
        "product_condition": "span.ui-search-item__condition",
        "product_location": "span.ui-search-item__location",
        "product_installments": "span.ui-search-item__installments",
        "product_mercadopago": "span.ui-search-item__mercadopago",
        "product_official_store": "span.ui-search-item__official-store",
        "product_highlight": "span.ui-search-item__highlight",
        "product_badge": "span.ui-search-item__badge",
        "product_promotion": "span.ui-search-item__promotion",
    })
