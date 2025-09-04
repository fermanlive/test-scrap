"""
Configuración global para tests del publisher service
"""
import pytest
import sys
import os

# Agregar el directorio padre al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="session")
def test_config():
    """Fixture para configuración de tests"""
    return {
        "test_url": "https://example.com",
        "test_category": "electronics",
        "test_page": 1
    }

@pytest.fixture
def sample_scraping_request():
    """Fixture para request de scraping válido"""
    from models import ScrapingRequest, PriorityLevel
    return ScrapingRequest(
        url="https://example.com",
        category="electronics",
        page=1,
        priority=PriorityLevel.NORMAL,
        metadata={"test": "data"}
    )
