"""
Tests unitarios para el script principal
Siguiendo el patrón AAA (Arrange, Act, Assert) orientado a TDD
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from decimal import Decimal

from main import ValidatorIA
from models.models import Product


class TestValidatorIA:
    """Tests para la clase ValidatorIA siguiendo TDD"""

    def test_init(self, mock_supabase_client):
        """Test: Inicialización exitosa de ValidatorIA"""
        # Arrange
        with patch('modules.database_connector.create_client', return_value=mock_supabase_client):
            with patch('modules.openia.OpenAI'):
                with patch.dict('os.environ', {
                    'SUPABASE_URL': 'https://test.supabase.co',
                    'SUPABASE_KEY': 'test-key',
                    'OPENAI_API_KEY': 'test-openai-key'
                }):
                    
                    # Act
                    validator = ValidatorIA()
                    
                    # Assert
                    assert validator.db_connector is not None
                    assert validator.ai_validator is not None

    def test_get_products_from_supabase_success(self, mock_supabase_client, mock_supabase_product):
        """Test: Obtención exitosa de productos de Supabase"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [mock_supabase_product]
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = mock_response
        
        with patch('modules.database_connector.create_client', return_value=mock_supabase_client):
            with patch('modules.openia.OpenAI'):
                with patch.dict('os.environ', {
                    'SUPABASE_URL': 'https://test.supabase.co',
                    'SUPABASE_KEY': 'test-key',
                    'OPENAI_API_KEY': 'test-openai-key'
                }):
                    validator = ValidatorIA()
                    
                    # Act
                    products = validator.get_products_from_supabase()
                    
                    # Assert
                    assert len(products) == 1
                    assert products[0]["id"] == "uuid-123"
                    assert products[0]["title"] == "Test Product"

    def test_get_products_from_supabase_with_category(self, mock_supabase_client, mock_supabase_product):
        """Test: Obtención de productos con filtro de categoría"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [mock_supabase_product]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        with patch('modules.database_connector.create_client', return_value=mock_supabase_client):
            with patch('modules.openia.OpenAI'):
                with patch.dict('os.environ', {
                    'SUPABASE_URL': 'https://test.supabase.co',
                    'SUPABASE_KEY': 'test-key',
                    'OPENAI_API_KEY': 'test-openai-key'
                }):
                    validator = ValidatorIA()
                    
                    # Act
                    products = validator.get_products_from_supabase(category="Test Brand")
                    
                    # Assert
                    assert len(products) == 1
                    mock_supabase_client.table.return_value.select.return_value.eq.assert_called_with("brand", "Test Brand")

    def test_get_products_from_supabase_with_page(self, mock_supabase_client, mock_supabase_product):
        """Test: Obtención de productos con paginación"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [mock_supabase_product]
        mock_supabase_client.table.return_value.select.return_value.range.return_value.execute.return_value = mock_response
        
        with patch('modules.database_connector.create_client', return_value=mock_supabase_client):
            with patch('modules.openia.OpenAI'):
                with patch.dict('os.environ', {
                    'SUPABASE_URL': 'https://test.supabase.co',
                    'SUPABASE_KEY': 'test-key',
                    'OPENAI_API_KEY': 'test-openai-key'
                }):
                    validator = ValidatorIA()
                    
                    # Act
                    products = validator.get_products_from_supabase(page=1)
                    
                    # Assert
                    assert len(products) == 1
                    mock_supabase_client.table.return_value.select.return_value.range.assert_called_with(100, 199)

    def test_get_products_from_supabase_empty(self, mock_supabase_client):
        """Test: Obtención de productos cuando no hay datos"""
        # Arrange
        mock_response = Mock()
        mock_response.data = []
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = mock_response
        
        with patch('modules.database_connector.create_client', return_value=mock_supabase_client):
            with patch('modules.openia.OpenAI'):
                with patch.dict('os.environ', {
                    'SUPABASE_URL': 'https://test.supabase.co',
                    'SUPABASE_KEY': 'test-key',
                    'OPENAI_API_KEY': 'test-openai-key'
                }):
                    validator = ValidatorIA()
                    
                    # Act
                    products = validator.get_products_from_supabase()
                    
                    # Assert
                    assert len(products) == 0

    def test_convert_supabase_product_to_product_data_success(self, mock_supabase_client, mock_supabase_product):
        """Test: Conversión exitosa de producto de Supabase a Product"""
        # Arrange
        with patch('modules.database_connector.create_client', return_value=mock_supabase_client):
            with patch('modules.openia.OpenAI'):
                with patch.dict('os.environ', {
                    'SUPABASE_URL': 'https://test.supabase.co',
                    'SUPABASE_KEY': 'test-key',
                    'OPENAI_API_KEY': 'test-openai-key'
                }):
                    validator = ValidatorIA()
                    
                    # Act
                    product = validator.convert_supabase_product_to_product_data(mock_supabase_product)
                    
                    # Assert
                    assert product is not None
                    assert product.article_id == "uuid-123"
                    assert product.title == "Test Product"
                    assert product.url == "https://example.com/product"
                    assert product.seller == "Test Seller"
                    assert product.current_price == 100.00
                    assert product.original_price == 120.00
                    assert product.discount_percentage == 16.67
                    assert product.currency == "US$"
                    assert product.rating == 4.5
                    assert product.review_count == 50
                    assert product.stock_quantity == 10
                    assert product.features == ["Feature 1", "Feature 2"]
                    assert len(product.images) == 1
                    assert product.images[0] == "https://example.com/main.jpg"
                    assert product.description == "Test description"
                    assert product.category == "Electronics"
                    assert product.brand == "Test Brand"
                    assert product.seller_location == "Montevideo"
                    assert product.shipping_method == "Standard"
                    assert product.free_shipping is False
                    assert product.page == 1

    def test_convert_supabase_product_to_product_data_with_empty_images(self, mock_supabase_client):
        """Test: Conversión de producto sin imágenes"""
        # Arrange
        supabase_product = {
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
            "features": [],
            "images": {},  # Sin imágenes
            "description": "Test description",
            "category": "Electronics",
            "brand": "Test Brand",
            "seller_location": "Montevideo",
            "shipping_method": "Standard",
            "free_shipping": False,
            "scraped_at": "2024-01-01T12:00:00Z",
            "page": 1
        }
        
        with patch('modules.database_connector.create_client', return_value=mock_supabase_client):
            with patch('modules.openia.OpenAI'):
                with patch.dict('os.environ', {
                    'SUPABASE_URL': 'https://test.supabase.co',
                    'SUPABASE_KEY': 'test-key',
                    'OPENAI_API_KEY': 'test-openai-key'
                }):
                    validator = ValidatorIA()
                    
                    # Act
                    product = validator.convert_supabase_product_to_product_data(supabase_product)
                    
                    # Assert
                    assert product is not None
                    assert product.images == []  # Debe ser lista vacía

    def test_convert_supabase_product_to_product_data_error(self, mock_supabase_client):
        """Test: Manejo de error en conversión de producto"""
        # Arrange
        invalid_product = {
            "id": "uuid-123",
            # Faltan campos requeridos
        }
        
        with patch('modules.database_connector.create_client', return_value=mock_supabase_client):
            with patch('modules.openia.OpenAI'):
                with patch.dict('os.environ', {
                    'SUPABASE_URL': 'https://test.supabase.co',
                    'SUPABASE_KEY': 'test-key',
                    'OPENAI_API_KEY': 'test-openai-key'
                }):
                    validator = ValidatorIA()
                    
                    # Act
                    product = validator.convert_supabase_product_to_product_data(invalid_product)
                    
                    # Assert
                    assert product is None

    @patch('modules.openia.OpenAI')
    def test_run_validation_process_success(self, mock_openai, mock_supabase_client, mock_supabase_product, sample_products):
        """Test: Proceso de validación exitoso"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [mock_supabase_product]
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = mock_response
        
        # Mock para OpenAI
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content='{"article_id": "test-123", "validation": {"is_valid": true, "issues": [], "suggestions": [], "confidence_score": 0.95}}'))]
        )
        
        # Mock para creación de registros
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = Mock(data=[{"id": 1}])
        
        with patch('modules.database_connector.create_client', return_value=mock_supabase_client):
            with patch.dict('os.environ', {
                'SUPABASE_URL': 'https://test.supabase.co',
                'SUPABASE_KEY': 'test-key',
                'OPENAI_API_KEY': 'test-openai-key'
            }):
                validator = ValidatorIA()
                
                # Act
                result = validator.run_validation_process()
                
                # Assert
                assert result is not None
                assert result["execution_id"] == 1
                assert result["total_products"] == 1

    @patch('modules.openia.OpenAI')
    def test_run_validation_process_no_products(self, mock_openai, mock_supabase_client):
        """Test: Proceso de validación sin productos"""
        # Arrange
        mock_response = Mock()
        mock_response.data = []
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = mock_response
        
        with patch('modules.database_connector.create_client', return_value=mock_supabase_client):
            with patch.dict('os.environ', {
                'SUPABASE_URL': 'https://test.supabase.co',
                'SUPABASE_KEY': 'test-key',
                'OPENAI_API_KEY': 'test-openai-key'
            }):
                validator = ValidatorIA()
                
                # Act
                result = validator.run_validation_process()
                
                # Assert
                assert result is None

    @patch('modules.openia.OpenAI')
    def test_run_validation_process_with_issues(self, mock_openai, mock_supabase_client, mock_supabase_product):
        """Test: Proceso de validación con productos que tienen issues"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [mock_supabase_product]
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = mock_response
        
        # Mock para OpenAI con respuesta que indica issues
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content='{"article_id": "uuid-123", "validation": {"is_valid": false, "issues": ["URL de imagen vacía"], "suggestions": ["Agregar imagen"], "confidence_score": 0.8}}'))]
        )
        
        # Mock para creación de registros
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = Mock(data=[{"id": 1}])
        
        with patch('modules.database_connector.create_client', return_value=mock_supabase_client):
            with patch.dict('os.environ', {
                'SUPABASE_URL': 'https://test.supabase.co',
                'SUPABASE_KEY': 'test-key',
                'OPENAI_API_KEY': 'test-openai-key'
            }):
                validator = ValidatorIA()
                
                # Act
                result = validator.run_validation_process()
                
                # Assert
                assert result is not None
                assert result["execution_id"] == 1
                assert result["total_products"] == 1
                assert result["valid_count"] == 0
                assert result["invalid_count"] == 1
                assert result["success_rate"] == 0.0

    @patch('modules.openia.OpenAI')
    def test_run_validation_process_error(self, mock_openai, mock_supabase_client, mock_supabase_product):
        """Test: Manejo de error en proceso de validación"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [mock_supabase_product, "error"]
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = mock_response
        
        # Mock para que falle la validación con IA
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("OpenAI API Error")
        
        # Mock para creación de registros
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = Mock(data=[{"id": 1}])
        
        with patch('modules.database_connector.create_client', return_value=mock_supabase_client):
            with patch.dict('os.environ', {
                'SUPABASE_URL': 'https://test.supabase.co',
                'SUPABASE_KEY': 'test-key',
                'OPENAI_API_KEY': 'test-openai-key'
            }):
            
                # Act & Assert
                validator = ValidatorIA()
                result = validator.run_validation_process()
                
                # Assert
                assert result is None
