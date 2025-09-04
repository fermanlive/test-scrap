"""
Utilidades para el scraper de Mercado Libre Uruguay.
"""

import re
import json
import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from decimal import Decimal, InvalidOperation
from datetime import datetime
import pandas as pd
from loguru import logger


def normalize_price(price_text: str, currency: str = "UYU") -> Optional[Decimal]:
    """
    Normalizar el texto del precio a un valor decimal.
    
    Args:
        price_text: Texto del precio (ej: "$1,234.56" o "1.234,56")
        currency: Moneda del precio
        
    Returns:
        Precio normalizado como Decimal o None si no se puede parsear
    """
    if not price_text:
        return None
    
    try:
        # Remover símbolos de moneda y espacios
        cleaned = re.sub(r'[^\d.,]', '', price_text.strip())
        
        # Detectar formato (punto o coma como separador decimal)
        if ',' in cleaned and '.' in cleaned:
            # Formato europeo: 1.234,56
            if cleaned.rfind(',') > cleaned.rfind('.'):
                cleaned = cleaned.replace('.', '').replace(',', '.')
            # Formato americano: 1,234.56
            else:
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            # Solo coma, asumir separador decimal
            cleaned = cleaned.replace(',', '.')
        
        return Decimal(cleaned)
    except (InvalidOperation, ValueError) as e:
        logger.warning(f"No se pudo parsear el precio: {price_text} - Error: {e}")
        return None


def extract_discount_percentage(discount_text: str) -> Optional[Decimal]:
    """
    Extraer el porcentaje de descuento del texto.
    
    Args:
        discount_text: Texto del descuento (ej: "25% OFF", "31% de descuento")
        
    Returns:
        Porcentaje de descuento como Decimal o None
    """
    if not discount_text:
        return None
    
    try:
        # Buscar patrones como "25% OFF", "31% de descuento", etc.
        match = re.search(r'(\d+(?:\.\d+)?)\s*%', discount_text)
        if match:
            return Decimal(match.group(1))
        return None
    except (ValueError, InvalidOperation) as e:
        logger.warning(f"No se pudo extraer el descuento: {discount_text} - Error: {e}")
        return None


def extract_rating(rating_text: str) -> Optional[float]:
    """
    Extraer el rating numérico del texto.
    
    Args:
        rating_text: Texto del rating (ej: "4.6", "4,6")
        
    Returns:
        Rating como float o None
    """
    if not rating_text:
        return None
    
    try:
        # Buscar números decimales
        match = re.search(r'(\d+(?:[.,]\d+)?)', rating_text)
        if match:
            rating_str = match.group(1).replace(',', '.')
            rating = float(rating_str)
            # Validar que esté en rango válido (0-5)
            if 0 <= rating <= 5:
                return rating
        return None
    except (ValueError, TypeError) as e:
        logger.warning(f"No se pudo extraer el rating: {rating_text} - Error: {e}")
        return None


def extract_review_count(review_text: str) -> Optional[int]:
    """
    Extraer el número de reviews del texto.
    
    Args:
        review_text: Texto de reviews (ej: "(123)", "123 opiniones")
        
    Returns:
        Número de reviews como int o None
    """
    if not review_text:
        return None
    
    try:
        # Buscar números en paréntesis o seguidos de "opiniones"
        match = re.search(r'\(?(\d+(?:[.,]\d+)?)\)?', review_text)
        if match:
            count_str = match.group(1).replace(',', '')
            return int(float(count_str))
        return None
    except (ValueError, TypeError) as e:
        logger.warning(f"No se pudo extraer el número de reviews: {review_text} - Error: {e}")
        return None


def clean_text(text: str) -> str:
    """
    Limpiar y normalizar texto extraído.
    
    Args:
        text: Texto a limpiar
        
    Returns:
        Texto limpio y normalizado
    """
    if not text:
        return ""
    
    # Remover espacios extra y saltos de línea
    cleaned = re.sub(r'\s+', ' ', text.strip())
    # Remover caracteres especiales problemáticos
    cleaned = re.sub(r'[\r\n\t]', '', cleaned)
    
    return cleaned


def ensure_directory(path: str) -> Path:
    """
    Asegurar que el directorio existe, creándolo si es necesario.
    
    Args:
        path: Ruta del directorio
        
    Returns:
        Path object del directorio
    """
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def export_to_csv(products: List[Dict[str, Any]], output_path: str) -> str:
    """
    Exportar productos a formato CSV.
    
    Args:
        products: Lista de productos como diccionarios
        output_path: Ruta del archivo de salida
        
    Returns:
        Ruta del archivo generado
    """
    if not products:
        logger.warning("No hay productos para exportar")
        return ""
    
    ensure_directory(os.path.dirname(output_path))
    
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            if products:
                fieldnames = products[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(products)
        
        logger.info(f"Productos exportados a CSV: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error al exportar a CSV: {e}")
        raise


def export_to_json(products: List[Dict[str, Any]], output_path: str) -> str:
    """
    Exportar productos a formato JSON.
    
    Args:
        products: Lista de productos como diccionarios
        output_path: Ruta del archivo de salida
        
    Returns:
        Ruta del archivo generado
    """
    if not products:
        logger.warning("No hay productos para exportar")
        return ""
    
    ensure_directory(os.path.dirname(output_path))
    
    try:
        with open(output_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(products, jsonfile, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Productos exportados a JSON: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error al exportar a JSON: {e}")
        raise


def export_to_excel(products: List[Dict[str, Any]], output_path: str) -> str:
    """
    Exportar productos a formato Excel.
    
    Args:
        products: Lista de productos como diccionarios
        output_path: Ruta del archivo de salida
        
    Returns:
        Ruta del archivo generado
    """
    if not products:
        logger.warning("No hay productos para exportar")
        return ""
    
    try:
        ensure_directory(os.path.dirname(output_path))
        
        df = pd.DataFrame(products)
        df.to_excel(output_path, index=False, engine='openpyxl')
        
        logger.info(f"Productos exportados a Excel: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error al exportar a Excel: {e}")
        raise


def export_products(products: List[Dict[str, Any]], output_path: str, format_type: str = "csv") -> str:
    """
    Exportar productos en el formato especificado.
    
    Args:
        products: Lista de productos como diccionarios
        output_path: Ruta del archivo de salida
        format_type: Tipo de formato (csv, json, excel)
        
    Returns:
        Ruta del archivo generado
    """
    format_type = format_type.lower()
    
    if format_type == "csv":
        return export_to_csv(products, output_path)
    elif format_type == "json":
        return export_to_json(products, output_path)
    elif format_type == "excel":
        return export_to_excel(products, output_path)
    else:
        raise ValueError(f"Formato no soportado: {format_type}")


def generate_filename(prefix: str = "ofertas", format_type: str = "csv") -> str:
    """
    Generar nombre de archivo con timestamp.
    
    Args:
        prefix: Prefijo del nombre del archivo
        format_type: Tipo de formato del archivo
        
    Returns:
        Nombre del archivo generado
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{format_type}"


def safe_get_text(element, selector: str, default: str = "") -> str:
    """
    Obtener texto de un elemento de forma segura.
    
    Args:
        element: Elemento del DOM
        selector: Selector CSS
        default: Valor por defecto si no se encuentra
        
    Returns:
        Texto extraído o valor por defecto
    """
    try:
        found_element = element.query_selector(selector)
        if found_element:
            return clean_text(found_element.text_content() or "")
        return default
    except Exception as e:
        logger.debug(f"Error al extraer texto con selector '{selector}': {e}")
        return default


def safe_get_attribute(element, selector: str, attribute: str, default: str = "") -> str:
    """
    Obtener atributo de un elemento de forma segura.
    
    Args:
        element: Elemento del DOM
        selector: Selector CSS
        attribute: Nombre del atributo
        default: Valor por defecto si no se encuentra
        
    Returns:
        Valor del atributo o valor por defecto
    """
    try:
        found_element = element.query_selector(selector)
        if found_element:
            return found_element.get_attribute(attribute) or default
        return default
    except Exception as e:
        logger.debug(f"Error al extraer atributo '{attribute}' con selector '{selector}': {e}")
        return default
