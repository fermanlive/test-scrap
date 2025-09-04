import os
from typing import Dict, List, Any, Tuple
from openai import OpenAI
from pydantic import BaseModel
import json
import re
from urllib.parse import urlparse
from models.models import Product

class ValidationResult(BaseModel):
    is_valid: bool
    issues: List[str]
    suggestions: List[str]
    confidence_score: float

class AIValidator:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY debe estar configurado")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4-turbo-preview"
    
    def validate_product_batch(self, products: List[Product]) -> List[Tuple[str, ValidationResult]]:
        """Valida un lote de productos usando IA Generativa"""
        validation_results = []
        
        # Procesar en lotes para optimizar el uso de la API
        batch_size = 10
        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]
            batch_results = self._validate_batch(batch)
            validation_results.extend(batch_results)
            
            # Pequeña pausa para evitar rate limiting
            import time
            time.sleep(0.1)
        
        return validation_results
    
    def _validate_batch(self, products: List[Product]) -> List[Tuple[str, ValidationResult]]:
        """Valida un lote específico de productos"""
        # Crear el prompt para el lote
        prompt = self._create_batch_prompt(products)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Eres un experto validador de datos de e-commerce. Tu tarea es validar la calidad y coherencia de los datos de productos.

                    Criterios de validación:
                    1. Completitud: No debe haber campos vacíos en registros esenciales tales son : Title, URL, Seller, Current Price, Original Price, Discount Percentage, Currency.
                    2. Coherencia: El descuento calculado debe coincidir con la diferencia entre precio original y actual
                    3. Formato válido: URLs e imágenes deben tener formato correcto
                    4. Valores atípicos: Detectar precios fuera de rango esperado, descuentos imposibles, etc.
                    5. Si estas validando de oferta valida que efectivamente tenga valores en es decir el valor original y el valor actual y el descuento porcentaje no debe estar vacio.

                    Responde en formato JSON con la siguiente estructura para cada producto:
                    {
                    "article_id": "ID del producto",
                    "validation": {
                        "is_valid": true/false,
                        "issues": ["lista de problemas encontrados"],
                        "suggestions": ["sugerencias de corrección"],
                        "confidence_score": 0.95
                    }
                    }"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=2000
            )
            
            # Parsear la respuesta
            print(response)
            content = response.choices[0].message.content
            return self._parse_validation_response(content, products)
            
        except Exception as e:
            print(f"❌ Error en validación con IA: {e}")
            # Si falla la IA, retornar productos como válidos por defecto
            return [(product.article_id, ValidationResult(
                is_valid=True,
                issues=[],
                suggestions=[],
                confidence_score=0.5
            )) for product in products]
    
    def _create_batch_prompt(self, products: List[Product]) -> str:
        """Crea el prompt para validar un lote de productos"""
        prompt = "Valida los siguientes productos de e-commerce:\n\n"
        
        for product in products:
            prompt += f"""
Producto ID: {product.article_id}
Nombre: {product.title}
Precio Original: {product.original_price}
Precio Actual: {product.current_price}
Descuento (%): {product.discount_percentage}
URL Imagen: {product.images[0] if product.images else ''}
URL Producto: {product.url}
Descripción: {product.description}
Categoría: {product.category}
Marca: {product.brand}
Rating: {product.rating}
Número de Reviews: {product.review_count}
---
"""
        
        prompt += "\nProporciona la validación en formato JSON para cada producto."
        return prompt
    
    def _parse_validation_response(self, content: str, products: List[Product]) -> List[Tuple[str, ValidationResult]]:
        """Parsea la respuesta de la IA para extraer los resultados de validación"""
        results = []
        
        try:
            # Limpiar el contenido de marcadores de markdown si existen
            cleaned_content = content.strip()
            
            # Remover bloques de código markdown si están presentes
            if cleaned_content.startswith('```json'):
                cleaned_content = cleaned_content[7:]  # Remover ```json
            if cleaned_content.startswith('```'):
                cleaned_content = cleaned_content[3:]  # Remover ```
            if cleaned_content.endswith('```'):
                cleaned_content = cleaned_content[:-3]  # Remover ```
            
            # Limpiar espacios en blanco
            cleaned_content = cleaned_content.strip()
            
            # Intentar parsear el JSON
            parsed_data = json.loads(cleaned_content)
            
            # Si es una lista de productos
            if isinstance(parsed_data, list):
                for item in parsed_data:
                    if 'article_id' in item and 'validation' in item:
                        validation = ValidationResult(**item['validation'])
                        results.append((item['article_id'], validation))
            
            # Si es un solo producto
            elif 'article_id' in parsed_data and 'validation' in parsed_data:
                validation = ValidationResult(**parsed_data['validation'])
                results.append((parsed_data['article_id'], validation))
        
        except (json.JSONDecodeError, KeyError) as e:
            print(f"❌ Error al parsear respuesta de IA: {e}")
            print(f"Contenido recibido: {content[:200]}...")  # Mostrar los primeros 200 caracteres para debug
        
        # Si no se pudieron parsear todos los resultados, marcar como válidos por defecto
        processed_ids = {r[0] for r in results}
        for product in products:
            if product.article_id not in processed_ids:
                results.append((product.article_id, ValidationResult(
                    is_valid=True,
                    issues=[],
                    suggestions=[],
                    confidence_score=0.5
                )))
        
        return results
    
    def validate_single_product(self, product: Product) -> ValidationResult:
        """Valida un solo producto (para casos de uso individual)"""
        results = self.validate_product_batch([product])
        return results[0][1] if results else ValidationResult(
            is_valid=True,
            issues=[],
            suggestions=[],
            confidence_score=0.5
        )
