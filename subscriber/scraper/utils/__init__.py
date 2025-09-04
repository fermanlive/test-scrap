"""
Utilidades para el scraper de Mercado Libre Uruguay.
"""

from .utils import (
    normalize_price,
    extract_discount_percentage,
    extract_rating,
    extract_review_count,
    clean_text
)

__all__ = [
    "normalize_price",
    "extract_discount_percentage", 
    "extract_rating",
    "extract_review_count",
    "clean_text"
]
