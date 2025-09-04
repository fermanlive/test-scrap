"""
Configuración del scraper para Mercado Libre Uruguay.
"""

import os
from pathlib import Path

# Directorio base del proyecto
BASE_DIR = Path(__file__).parent.parent

# Configuración del scraper
SCRAPER_CONFIG = {
    "base_url": "https://www.mercadolibre.com.uy/ofertas",
    "log_dir": BASE_DIR / "logs",
    "output_dir": BASE_DIR / "output",
    "max_workers": int(os.getenv("MAX_WORKERS", "3")),
    "max_retries": int(os.getenv("MAX_RETRIES", "3")),
    "retry_delay": int(os.getenv("RETRY_DELAY", "5")),
    "browser_headless": os.getenv("BROWSER_HEADLESS", "true").lower() == "true",
    "browser_timeout": int(os.getenv("BROWSER_TIMEOUT", "30000")),
    "rate_limit_delay": float(os.getenv("RATE_LIMIT_DELAY", "2.0")),
    "max_products": int(os.getenv("MAX_PRODUCTS", "3"))
}

# Configuración de selectores CSS
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
    "product_shipping": "span.ui-search-item__shipping"
}

# Configuración de rate limiting
RATE_LIMIT_CONFIG = {
    "requests_per_minute": 30,
    "delay_between_requests": 1.0,  # 1 segundo entre requests
    "burst_size": 5,
    "max_requests_per_second": 1.0,  # Máximo 1 request por segundo
    "jitter": True,
    "max_concurrent": 3,
}

# Configuración de retry
RETRY_CONFIG = {
    "max_attempts": 3,
    "base_delay": 1.0,
    "max_delay": 60.0,
    "exponential_base": 2.0,
    "jitter": True,
}

# Configuración de manejo de excepciones
EXCEPTION_CONFIG = {
    "max_retries": 3,
    "navigation_retry_delay": 1.0,
    "extraction_retry_delay": 0.5,
    "rate_limit_retry_delay": 2.0,
    "log_errors": True,
}
