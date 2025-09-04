"""
Tests unitarios para el módulo de IA Generativa
Siguiendo el patrón AAA (Arrange, Act, Assert) orientado a TDD
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from modules.openia import AIValidator, ValidationResult
from models.models import Product


class TestAIValidator:
    """Tests para la clase AIValidator siguiendo TDD"""

    def test_init_with_valid_api_key(self):
        """Test: Inicialización exitosa con API key válida"""
        # Arrange
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            
            # Act
            validator = AIValidator()
            
            # Assert
            assert validator.model == "gpt-4-turbo-preview"
            assert validator.client is not None

    def test_init_without_api_key(self):
        """Test: Error al inicializar sin API key"""
        # Arrange
        with patch.dict('os.environ', {}, clear=True):
            
            # Act & Assert
            with pytest.raises(ValueError, match="OPENAI_API_KEY debe estar configurado"):
                AIValidator()

    def test_create_batch_prompt(self, sample_products):
        """Test: Creación correcta del prompt para validación en lote"""
        # Arrange
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            validator = AIValidator()
            
            # Act
            prompt = validator._create_batch_prompt(sample_products)
            
            # Assert
            assert "Producto ID: prod-1" in prompt
            assert "Producto ID: prod-2" in prompt
            assert "Product 1" in prompt
            assert "Product 2" in prompt
            assert "https://example.com/prod1" in prompt
            assert "https://example.com/prod2" in prompt

    def test_create_batch_prompt_with_empty_images(self, sample_products):
        """Test: Prompt con productos sin imágenes"""
        # Arrange
        sample_products[0].images = []  # Modificar el primer producto para que no tenga imágenes
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            validator = AIValidator()
            
            # Act
            prompt = validator._create_batch_prompt(sample_products)
            
            # Assert
            assert "URL Imagen: " in prompt  # Debe estar vacío pero presente

    def test_parse_validation_response_valid_json(self, sample_products):
        """Test: Parsing de respuesta JSON válida"""
        # Arrange
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            validator = AIValidator()
            json_response = '''```json
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
            
            # Act
            results = validator._parse_validation_response(json_response, sample_products)
            
            # Assert
            assert len(results) == 2
            assert results[0][0] == "prod-1"  # article_id
            assert results[0][1].is_valid is True
            assert results[1][0] == "prod-2"  # article_id
            assert results[1][1].is_valid is False
            assert "URL de imagen vacía" in results[1][1].issues

    def test_parse_validation_response_invalid_json(self, sample_products):
        """Test: Parsing de respuesta JSON inválida"""
        # Arrange
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            validator = AIValidator()
            invalid_json = "invalid json content"
            
            # Act
            results = validator._parse_validation_response(invalid_json, sample_products)
            
            # Assert
            assert len(results) == 2
            for article_id, result in results:
                assert result.is_valid is True
                assert result.confidence_score == 0.5

    def test_parse_validation_response_partial_results(self, sample_products):
        """Test: Parsing de respuesta parcial (solo algunos productos)"""
        # Arrange
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            validator = AIValidator()
            partial_json = '''```json
[
    {
        "article_id": "prod-1",
        "validation": {
            "is_valid": true,
            "issues": [],
            "suggestions": [],
            "confidence_score": 0.95
        }
    }
]
```'''
            
            # Act
            results = validator._parse_validation_response(partial_json, sample_products)
            
            # Assert
            assert len(results) == 2
            # El primer producto debe tener el resultado parseado
            assert results[0][0] == "prod-1"
            assert results[0][1].is_valid is True
            # El segundo producto debe tener resultado por defecto
            assert results[1][0] == "prod-2"
            assert results[1][1].is_valid is True
            assert results[1][1].confidence_score == 0.5

    @patch('modules.openia.OpenAI')
    def test_validate_product_batch_success(self, mock_openai, sample_products, mock_openai_response):
        """Test: Validación exitosa de lote de productos"""
        # Arrange
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = Mock(**mock_openai_response)
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            validator = AIValidator()
            
            # Act
            results = validator.validate_product_batch(sample_products)
            
            # Assert
            mock_client.chat.completions.create.assert_called_once()
            assert len(results) == 2
            assert results[0][0] == "prod-1"
            assert results[1][0] == "prod-2"

    @patch('modules.openia.OpenAI')
    def test_validate_product_batch_openai_error(self, mock_openai, sample_products):
        """Test: Manejo de error de OpenAI"""
        # Arrange
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("OpenAI API Error")
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            validator = AIValidator()
            
            # Act
            results = validator.validate_product_batch(sample_products)
            
            # Assert
            assert len(results) == 2
            for article_id, result in results:
                assert result.is_valid is True
                assert result.confidence_score == 0.5

    @patch('modules.openia.OpenAI')
    def test_validate_single_product(self, mock_openai, sample_product, mock_openai_response):
        """Test: Validación de un solo producto"""
        # Arrange
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = Mock(**mock_openai_response)
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            validator = AIValidator()
            
            # Act
            result = validator.validate_single_product(sample_product)
            
            # Assert
            mock_client.chat.completions.create.assert_called_once()
            assert isinstance(result, ValidationResult)
            assert result.is_valid is True

    def test_validate_single_product_fallback(self, sample_product):
        """Test: Fallback cuando falla la validación de un solo producto"""
        # Arrange
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            validator = AIValidator()
            
            # Mock para que falle la validación en lote
            with patch.object(validator, 'validate_product_batch', return_value=[]):
                
                # Act
                result = validator.validate_single_product(sample_product)
                
                # Assert
                assert isinstance(result, ValidationResult)
                assert result.is_valid is True
                assert result.confidence_score == 0.5

    @patch('time.sleep')  # Mock para evitar delays en tests
    def test_validate_product_batch_with_rate_limiting(self, mock_sleep, sample_products):
        """Test: Validación con rate limiting (múltiples lotes)"""
        # Arrange
        many_products = sample_products * 6  # 12 productos total
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            validator = AIValidator()
            
            # Mock para simular respuestas exitosas
            with patch.object(validator, '_validate_batch') as mock_batch:
                mock_batch.return_value = [("prod-1", ValidationResult(is_valid=True, issues=[], suggestions=[], confidence_score=0.9))]
                
                # Act
                results = validator.validate_product_batch(many_products)
                
                # Assert
                assert mock_batch.call_count == 2
                assert mock_sleep.call_count == 2


class TestValidationResult:
    """Tests para la clase ValidationResult siguiendo TDD"""

    def test_validation_result_creation(self):
        """Test: Creación de ValidationResult"""
        # Arrange
        issues = ["Issue 1", "Issue 2"]
        suggestions = ["Suggestion 1"]
        confidence_score = 0.85
        
        # Act
        result = ValidationResult(
            is_valid=True,
            issues=issues,
            suggestions=suggestions,
            confidence_score=confidence_score
        )
        
        # Assert
        assert result.is_valid is True
        assert len(result.issues) == 2
        assert len(result.suggestions) == 1
        assert result.confidence_score == 0.85

    def test_validation_result_valid_product(self):
        """Test: ValidationResult para producto válido"""
        # Arrange
        confidence_score = 0.95
        
        # Act
        result = ValidationResult(
            is_valid=True,
            issues=[],
            suggestions=[],
            confidence_score=confidence_score
        )
        
        # Assert
        assert result.is_valid is True
        assert len(result.issues) == 0
        assert len(result.suggestions) == 0
        assert result.confidence_score == 0.95

    def test_validation_result_invalid_product(self):
        """Test: ValidationResult para producto inválido"""
        # Arrange
        issues = ["Nombre vacío", "Precio inválido"]
        suggestions = ["Agregar nombre", "Verificar precio"]
        confidence_score = 0.7
        
        # Act
        result = ValidationResult(
            is_valid=False,
            issues=issues,
            suggestions=suggestions,
            confidence_score=confidence_score
        )
        
        # Assert
        assert result.is_valid is False
        assert len(result.issues) == 2
        assert len(result.suggestions) == 2
        assert result.confidence_score == 0.7


class TestProductModel:
    """Tests para el modelo Product siguiendo TDD"""

    def test_product_creation(self, sample_product):
        """Test: Creación de Product"""
        # Arrange & Act (ya está en el fixture)
        
        # Assert
        assert sample_product.article_id == "test-123"
        assert sample_product.title == "Laptop Gaming ASUS ROG"
        assert sample_product.url == "https://example.com/product"
        assert sample_product.seller == "Test Seller"
        assert sample_product.current_price == Decimal("999.99")
        assert sample_product.original_price == Decimal("1299.99")
        assert sample_product.discount_percentage == Decimal("23.1")

    def test_product_to_dict(self, sample_product):
        """Test: Conversión de Product a diccionario"""
        # Act
        product_dict = sample_product.to_dict()
        
        # Assert
        assert product_dict["title"] == "Laptop Gaming ASUS ROG"
        assert product_dict["url"] == "https://example.com/product"
        assert product_dict["seller"] == "Test Seller"
        assert product_dict["current_price"] == 999.99
        assert product_dict["original_price"] == 1299.99
        assert product_dict["discount_percentage"] == 23.1

    def test_product_with_optional_fields(self):
        """Test: Product con campos opcionales"""
        # Arrange
        article_id = "test-optional"
        title = "Test Product"
        url = "https://example.com"
        seller = "Test Seller"
        
        # Act
        product = Product(
            article_id=article_id,
            title=title,
            url=url,
            seller=seller
            # Sin campos opcionales
        )
        
        # Assert
        assert product.article_id == "test-optional"
        assert product.title == "Test Product"
        assert product.current_price is None
        assert product.original_price is None
        assert product.rating is None
        assert product.images == []
        assert product.features == []
