"""
Mercado Libre Uruguay Scraper

Un scraper robusto para extraer información de productos de las ofertas
de Mercado Libre Uruguay usando Playwright con Camoufox.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Importaciones relativas para evitar importaciones circulares
from .simple_scraper import SimpleScraper
from .models.models import Product, ScrapingResult
from .services import ScraperService

__all__ = ["SimpleScraper", "Product", "ScrapingResult", "ScraperService"]
