"""
Configuraciones adicionales para el scraper de Mercado Libre Uruguay.
"""

import os
from pathlib import Path
from typing import Dict, Any

# Directorio base del proyecto
BASE_DIR = Path(__file__).parent.parent

# Configuraciones de selectores CSS (actualizados según la estructura real de ML)
SELECTORS = {
    "product_card": "li.ui-search-layout__item",
    "product_title": "h2.ui-search-item__title",
    "product_price": "span.andes-money-amount__fraction",
    "product_original_price": "span.andes-money-amount--previous",
    "product_discount": "span.ui-search-price__discount",
    "product_seller": "span.ui-search-item__seller-info",
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
    
    # Selectores para páginas de detalle
    "detail_title": "h1.ui-pdp-title",
    "detail_price": "span.andes-money-amount__fraction",
    "detail_original_price": "span.andes-money-amount--previous",
    "detail_discount": "span.ui-pdp-price__discount",
    "detail_seller": "span.ui-pdp-seller__name",
    "detail_rating": "span.ui-pdp-review__rating",
    "detail_reviews": "span.ui-pdp-review__amount",
    "detail_images": "img.ui-pdp-image",
    "detail_features": "div.ui-pdp-specs__table__row",
    "detail_seller_location": "span.ui-pdp-seller__location",
    "detail_shipping": "span.ui-pdp-shipping__method",
    "detail_brand": "span.ui-pdp-brand",
    "detail_condition": "span.ui-pdp-condition",
}

# Configuraciones de URLs
URLS = {
    "base": "https://www.mercadolibre.com.uy",
    "offers": "https://www.mercadolibre.com.uy/ofertas",
    "search": "https://www.mercadolibre.com.uy/search",
    "categories": "https://www.mercadolibre.com.uy/categories",
}

# Configuraciones de exportación
EXPORT_CONFIG = {
    "csv": {
        "encoding": "utf-8",
        "delimiter": ",",
        "quotechar": '"',
    },
    "json": {
        "indent": 2,
        "ensure_ascii": False,
    },
    "excel": {
        "engine": "openpyxl",
        "sheet_name": "Ofertas",
    }
}

# Configuraciones de logging
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "{asctime} | {levelname: <8} | {name}:{funcName}:{lineno} - {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": BASE_DIR / "logs" / "scraper.log",
            "mode": "a",
        },
    },
    "loggers": {
        "scraper": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False,
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
}

# Configuraciones de retry
RETRY_CONFIG = {
    "max_attempts": 3,
    "base_delay": 1.0,
    "max_delay": 60.0,
    "exponential_base": 2,
    "jitter": True,
}

# Configuraciones de rate limiting
RATE_LIMIT_CONFIG = {
    "requests_per_minute": 30,
    "delay_between_requests": 2.0,
    "burst_size": 5,
}

# Configuraciones de navegador
BROWSER_CONFIG = {
    "user_agents": [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ],
    "viewport_sizes": [
        {"width": 1920, "height": 1080},
        {"width": 1366, "height": 768},
        {"width": 1440, "height": 900},
    ],
    "timeouts": {
        "navigation": 30000,
        "element_wait": 10000,
        "page_load": 60000,
    },
}

# Configuraciones de validación
VALIDATION_CONFIG = {
    "min_title_length": 5,
    "max_title_length": 500,
    "min_price": 0,
    "max_price": 1000000,
    "min_rating": 0.0,
    "max_rating": 5.0,
    "min_review_count": 0,
    "max_review_count": 100000,
}

# Configuraciones de limpieza de datos
CLEANING_CONFIG = {
    "remove_html_tags": True,
    "normalize_whitespace": True,
    "remove_special_chars": False,
    "max_feature_length": 200,
    "max_image_urls": 10,
}

# Configuraciones de monitoreo
MONITORING_CONFIG = {
    "enable_metrics": True,
    "metrics_interval": 60,  # segundos
    "performance_thresholds": {
        "max_extraction_time": 300,  # segundos
        "min_success_rate": 80.0,    # porcentaje
        "max_error_rate": 20.0,      # porcentaje
    },
}

# Configuraciones de Camoufox - Solo perfil FAST
CAMOUFOX_CONFIG = {
    "enabled": True,
    "default_profile": "fast",
    "profiles": {
        "fast": {
            "enable_stealth": False,
            "enable_anti_detection": True,
            "enable_fingerprint_protection": False,
            "headless": True,
            "user_agent_rotation": False,
            "clear_cookies_on_start": False,
            "clear_storage_on_start": False,
        }
    }
}
