"""
Configuración de pytest y fixtures comunes para tests
"""

import pytest
import os
from unittest.mock import Mock, patch
from datetime import datetime
from decimal import Decimal

from models.models import Product
from modules.openia import ValidationResult


@pytest.fixture
def sample_product():
    """Fixture que proporciona un producto de ejemplo válido"""
    return Product(
        article_id="test-123",
        title="Laptop Gaming ASUS ROG",
        url="https://example.com/product",
        seller="Test Seller",
        current_price=Decimal("999.99"),
        original_price=Decimal("1299.99"),
        discount_percentage=Decimal("23.1"),
        currency="US$",
        rating=4.5,
        review_count=127,
        stock_quantity=10,
        features=["Gaming", "RTX 4060"],
        images=["https://example.com/image1.jpg"],
        description="Laptop gaming de alto rendimiento",
        category="Electronics",
        brand="ASUS",
        seller_location="Montevideo",
        shipping_method="Express",
        free_shipping=True,
        scraped_at=datetime.now(),
        page=1
    )


@pytest.fixture
def invalid_product():
    """Fixture que proporciona un producto con problemas de validación"""
    return Product(
        article_id="test-456",
        title="",  # Nombre vacío
        url="invalid-url",  # URL inválida
        seller="Test Seller",
        current_price=Decimal("200.00"),
        original_price=Decimal("100.00"),  # Precio actual mayor que original
        discount_percentage=Decimal("150.0"),  # Descuento imposible
        currency="US$",
        rating=6.5,  # Rating fuera de rango
        review_count=-5,  # Número negativo
        stock_quantity=0,
        features=[],
        images=[],  # Sin imágenes
        description="",
        category="",
        brand="",
        seller_location="",
        shipping_method="",
        free_shipping=False,
        scraped_at=datetime.now(),
        page=1
    )


@pytest.fixture
def sample_products():
    """Fixture que proporciona una lista de productos de ejemplo"""
    return [
        Product(
            article_id="prod-1",
            title="Product 1",
            url="https://example.com/prod1",
            seller="Seller 1",
            current_price=Decimal("100.00"),
            original_price=Decimal("120.00"),
            discount_percentage=Decimal("16.67"),
            currency="US$",
            rating=4.0,
            review_count=50,
            stock_quantity=5,
            features=["Feature 1"],
            images=["https://example.com/img1.jpg"],
            description="Description 1",
            category="Category 1",
            brand="Brand 1",
            seller_location="Location 1",
            shipping_method="Standard",
            free_shipping=False,
            scraped_at=datetime.now(),
            page=1
        ),
        Product(
            article_id="prod-2",
            title="Product 2",
            url="https://example.com/prod2",
            seller="Seller 2",
            current_price=Decimal("200.00"),
            original_price=Decimal("250.00"),
            discount_percentage=Decimal("20.00"),
            currency="US$",
            rating=4.5,
            review_count=75,
            stock_quantity=10,
            features=["Feature 2"],
            images=["https://example.com/img2.jpg"],
            description="Description 2",
            category="Category 2",
            brand="Brand 2",
            seller_location="Location 2",
            shipping_method="Express",
            free_shipping=True,
            scraped_at=datetime.now(),
            page=1
        )
    ]


@pytest.fixture
def mock_validation_result():
    """Fixture que proporciona un resultado de validación de ejemplo"""
    return ValidationResult(
        is_valid=True,
        issues=[],
        suggestions=[],
        confidence_score=0.95
    )


@pytest.fixture
def mock_invalid_validation_result():
    """Fixture que proporciona un resultado de validación con issues"""
    return ValidationResult(
        is_valid=False,
        issues=["Nombre del producto está vacío", "URL inválida"],
        suggestions=["Agregar nombre del producto", "Verificar formato de URL"],
        confidence_score=0.7
    )


@pytest.fixture
def mock_openai_response():
    """Fixture que simula una respuesta de OpenAI"""
    return {
        "choices": [
            {
                "message": {
                    "content": '''```json
[
    {
        "article_id": "prod-1",
        "validation": {
            "is_valid": true,
            "issues": [],
            "suggestions": [],
            "confidence_score": 0.95
        }
    },
    {
        "article_id": "prod-2",
        "validation": {
            "is_valid": false,
            "issues": ["URL de imagen vacía"],
            "suggestions": ["Agregar URL de imagen"],
            "confidence_score": 0.8
        }
    }
]
```'''
                }
            }
        ]
    }


@pytest.fixture
def mock_supabase_product():
    """Fixture que simula un producto de Supabase"""
    return {
        "id": "uuid-123",
        "title": "Test Product",
        "url": "https://example.com/product",
        "seller": "Test Seller",
        "current_price": 100.00,
        "original_price": 120.00,
        "discount_percentage": 16.67,
        "currency": "US$",
        "rating": 4.5,
        "review_count": 50,
        "stock_quantity": 10,
        "features": ["Feature 1", "Feature 2"],
        "images": {
            "main": "https://example.com/main.jpg",
            "secondary": "https://example.com/secondary.jpg"
        },
        "description": "Test description",
        "category": "Electronics",
        "brand": "Test Brand",
        "seller_location": "Montevideo",
        "shipping_method": "Standard",
        "free_shipping": False,
        "scraped_at": "2024-01-01T12:00:00Z",
        "page": 1
    }


@pytest.fixture
def mock_supabase_client():
    """Fixture que simula el cliente de Supabase"""
    mock_client = Mock()
    mock_table = Mock()
    mock_select = Mock()
    mock_insert = Mock()
    mock_update = Mock()
    
    # Configurar la cadena de métodos
    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_table.insert.return_value = mock_insert
    mock_table.update.return_value = mock_update
    
    # Configurar respuestas
    mock_select.eq.return_value = mock_select
    mock_select.range.return_value = mock_select
    mock_select.execute.return_value = Mock(data=[{"id": "test-1", "title": "Test"}])
    
    mock_insert.execute.return_value = Mock(data=[{"id": 1}])
    mock_update.eq.return_value = mock_update
    mock_update.execute.return_value = Mock(data=[{"id": 1}])
    
    return mock_client


@pytest.fixture
def mock_env_vars():
    """Fixture que simula variables de entorno"""
    return {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test-key",
        "OPENAI_API_KEY": "test-openai-key"
    }


@pytest.fixture(autouse=True)
def setup_test_env(mock_env_vars):
    """Fixture que configura el entorno de pruebas automáticamente"""
    with patch.dict(os.environ, mock_env_vars):
        yield
