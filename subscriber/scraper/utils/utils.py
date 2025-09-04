"""
Utilidades para el scraper de Mercado Libre Uruguay.
"""

import re
from decimal import Decimal
from typing import Optional


def normalize_price(price_text: str) -> Optional[Decimal]:
    """
    Normalizar texto de precio a Decimal.
    
    Args:
        price_text: Texto del precio (ej: "1.234,56" o "1234.56")
        
    Returns:
        Precio normalizado como Decimal o None si no se puede parsear
    """
    if not price_text:
        return None
    
    try:
        # Remover caracteres no numéricos excepto punto y coma
        cleaned = re.sub(r'[^\d.,]', '', price_text.strip())
        
        # Si hay coma, asumir formato europeo (1.234,56)
        if ',' in cleaned and '.' in cleaned:
            # Reemplazar punto por nada y coma por punto
            cleaned = cleaned.replace('.', '').replace(',', '.')
        elif ',' in cleaned:
            # Solo coma, asumir que es el separador decimal
            cleaned = cleaned.replace(',', '.')
        
        return Decimal(cleaned)
    except (ValueError, TypeError):
        return None


def extract_discount_percentage(original_price: Decimal, current_price: Decimal) -> Optional[Decimal]:
    """
    Calcular porcentaje de descuento.
    
    Args:
        original_price: Precio original
        current_price: Precio actual
        
    Returns:
        Porcentaje de descuento o None si no hay descuento
    """
    if not original_price or not current_price or original_price <= current_price:
        return None
    
    try:
        discount = ((original_price - current_price) / original_price) * 100
        return round(discount, 2)
    except (ZeroDivisionError, TypeError):
        return None


def extract_rating(rating_text: str) -> Optional[float]:
    """
    Extraer rating numérico del texto.
    
    Args:
        rating_text: Texto del rating (ej: "4.5", "4,5", "4.5/5")
        
    Returns:
        Rating como float o None si no se puede parsear
    """
    if not rating_text:
        return None
    
    try:
        # Buscar patrón de rating (ej: 4.5, 4,5, 4.5/5)
        match = re.search(r'(\d+[,.]?\d*)', rating_text.strip())
        if match:
            rating_str = match.group(1).replace(',', '.')
            rating = float(rating_str)
            # Validar que esté en rango 0-5
            if 0 <= rating <= 5:
                return round(rating, 1)
        return None
    except (ValueError, TypeError):
        return None


def extract_review_count(review_text: str) -> Optional[int]:
    """
    Extraer número de reviews del texto.
    
    Args:
        review_text: Texto de reviews (ej: "123 opiniones", "1.234")
        
    Returns:
        Número de reviews como int o None si no se puede parsear
    """
    if not review_text:
        return None
    
    try:
        # Buscar números en el texto
        match = re.search(r'(\d+(?:\.\d+)?)', review_text.strip())
        if match:
            # Remover puntos de miles
            number_str = match.group(1).replace('.', '')
            return int(number_str)
        return None
    except (ValueError, TypeError):
        return None


def clean_text(text: str) -> str:
    """
    Limpiar y normalizar texto.
    
    Args:
        text: Texto a limpiar
        
    Returns:
        Texto limpio
    """
    if not text:
        return ""
    
    # Remover espacios extra y saltos de línea
    cleaned = re.sub(r'\s+', ' ', text.strip())
    
    # Remover caracteres especiales problemáticos
    cleaned = re.sub(r'[\r\n\t]', ' ', cleaned)
    
    return cleaned.strip()
