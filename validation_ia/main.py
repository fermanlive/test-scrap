#!/usr/bin/env python3
"""
Script principal para ejecutar el sistema de validación con IA Generativa
Valida datos de scraping almacenados en Supabase
"""

import os
import argparse
from datetime import datetime
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

from modules.database_connector import DatabaseConnector, ValidationRecord, ExecutionRecord
from modules.openia import AIValidator
from models.models import Product

# Cargar variables de entorno
load_dotenv()


class ValidatorIA:

    def __init__(self):
        self.db_connector = DatabaseConnector()
        self.ai_validator = AIValidator()

    def get_products_from_supabase(self, category: str = None, page: int = None, page_size: int = 100):
        """Obtiene productos de la tabla products en Supabase"""
        try:
            query = self.db_connector.client.table("products").select("*")
            
            # Aplicar filtros si se proporcionan
            if category:
                query = query.eq("brand", category)  # Asumiendo que brand es la categoría
            
            # Aplicar paginación si se proporciona
            if page is not None:
                offset = page * page_size
                query = query.range(offset, offset + page_size - 1)
            
            result = query.execute()
            
            if not result.data:
                print(f"❌ No se encontraron productos para category={category}, page={page}")
                return []
            
            print(f"📦 Obtenidos {len(result.data)} productos de Supabase")
            return result.data
            
        except Exception as e:
            print(f"❌ Error al obtener productos de Supabase: {e}")
            return []

    def convert_supabase_product_to_product_data(self, supabase_product: Dict[str, Any]) -> Optional[Product]:
        """Convierte un producto de Supabase al formato Product"""
        try:
            # Validar campos requeridos
            required_fields = ['id', 'title', 'url', 'seller']
            for field in required_fields:
                if not supabase_product.get(field):
                    raise ValueError(f"Campo requerido '{field}' está vacío o no existe")
            
            # Extraer la primera imagen si existe
            images = supabase_product.get('images', {})
            first_image = ""
            if images and isinstance(images, dict):
                # Buscar la primera URL de imagen disponible
                for key, value in images.items():
                    if isinstance(value, str) and value.startswith('http'):
                        first_image = value
                        break
            
            return Product(
                article_id=supabase_product.get('id'),
                title=supabase_product.get('title'),
                url=supabase_product.get('url'),
                seller=supabase_product.get('seller'),
                current_price=supabase_product.get('current_price', 0),
                original_price=supabase_product.get('original_price', 0),
                discount_percentage=supabase_product.get('discount_percentage', 0),
                currency=supabase_product.get('currency', ''),
                rating=supabase_product.get('rating', 0),
                review_count=supabase_product.get('review_count', 0),
                stock_quantity=supabase_product.get('stock_quantity', 0),
                features=supabase_product.get('features', []),
                images=[first_image] if first_image else [],
                description=supabase_product.get('description', ''),
                category=supabase_product.get('category', ''),
                brand=supabase_product.get('brand', ''),
                seller_location=supabase_product.get('seller_location', ''),
                shipping_method=supabase_product.get('shipping_method', ''),
                free_shipping=supabase_product.get('free_shipping', False),
                scraped_at=datetime.now(),
                page=supabase_product.get('page', 0)
            )
            
        except Exception as e:
            print(f"❌ Error al convertir producto {supabase_product.get('id', 'unknown')}: {e}")
            return None

    def run_validation_process(self, category: str = None, page: int = None):
        """Ejecuta el proceso de validación completo"""
        try:
            print("🚀 Iniciando sistema de validación con IA Generativa...")
            
            # Obtener productos de Supabase
            print("📥 Obteniendo productos de Supabase...")
            supabase_products = self.get_products_from_supabase(category, page)
            
            if not supabase_products:
                print("❌ No hay productos para validar")
                return None
            
            # Convertir productos al formato Product
            print("🔄 Convirtiendo productos...")
            products = []
            for supabase_product in supabase_products:
                product_data = self.convert_supabase_product_to_product_data(supabase_product)
                if product_data:
                    products.append(product_data)
            
            if not products:
                print("❌ No se pudieron convertir productos válidos")
                return None
            
            print(f"✅ {len(products)} productos convertidos exitosamente")
            
            # Crear registro de ejecución
            print("📝 Creando registro de ejecución...")
            execution_record = ExecutionRecord(
                id=0,
                start_time=datetime.now(),
                end_time=None,
                status="Not complete",
                records_status="Not started",
                issues_summary={},
                total_records=len(products),
                valid_records=0,
                invalid_records=0
            )
            
            execution_id = self.db_connector.create_execution_record(execution_record)
            print(f"✅ Ejecución registrada con ID: {execution_id}")
            
            # Actualizar estado a "en progreso"
            self.db_connector.update_execution_record(execution_id, {
                "status": "In Progress",
                "records_status": "Processing"
            })
            
            print("🤖 Iniciando validación con IA Generativa...")
            
            # Validar productos usando IA
            validation_results = self.ai_validator.validate_product_batch(products)
            
            print("📊 Procesando resultados de validación...")
            
            # Procesar resultados y crear registros de validación
            valid_count = 0
            invalid_count = 0
            issues_summary = {}
            
            for article_id, result in validation_results:
                # Encontrar el producto correspondiente
                product = None
                for p in products:
                    if str(p.article_id) == article_id:
                        product = p
                        break
                
                if not product:
                    # Si no se encuentra, usar el primer producto
                    product = products[0] if products else None
                
                # Crear registro de validación individual
                validation_record = ValidationRecord(
                    id=0,
                    article_id=product.article_id if product else article_id,
                    validation_date=datetime.now(),
                    status="Ok" if result.is_valid else "issues",
                    issues=result.issues,
                    metadata={
                        "suggestions": result.suggestions,
                        "confidence_score": result.confidence_score,
                        "validation_method": "AI_Generative",
                        "category": category,
                        "page": page
                    }
                )
                
                self.db_connector.create_validation_record(validation_record)
                
                # Contar resultados
                if result.is_valid:
                    valid_count += 1
                else:
                    invalid_count += 1
                    issues_summary[product.article_id if product else article_id] = result.issues
            
            # Determinar estado final
            records_status = "Ok" if invalid_count == 0 else "issues"
            final_status = "Done"
            
            # Actualizar registro de ejecución
            self.db_connector.update_execution_record(execution_id, {
                "end_time": datetime.now().isoformat(),
                "status": final_status,
                "records_status": records_status,
                "issues_summary": issues_summary,
                "valid_records": valid_count,
                "invalid_records": invalid_count
            })
            
            # Mostrar resumen
            print("\n" + "=" * 80)
            print("🎯 VALIDACIÓN COMPLETADA")
            print("=" * 80)
            print(f"📊 Resumen de ejecución {execution_id}:")
            print(f"   • Categoría: {category or 'Todas'}")
            print(f"   • Página: {page or 'Todas'}")
            print(f"   • Total de productos: {len(products)}")
            print(f"   • ✅ Válidos: {valid_count}")
            print(f"   • ❌ Con issues: {invalid_count}")
            print(f"   • 📈 Porcentaje de éxito: {(valid_count/len(products)*100):.1f}%")
            
            if issues_summary:
                print(f"\n🚨 Productos con issues:")
                for article_id, issues in issues_summary.items():
                    print(f"   • {article_id}: {len(issues)} problemas")
                    for issue in issues[:3]:  # Mostrar solo los primeros 3 issues
                        print(f"     - {issue}")
                    if len(issues) > 3:
                        print(f"     ... y {len(issues) - 3} más")
            
            print(f"\n💾 Resultados almacenados en la base de datos")
            print(f"   • Ejecución ID: {execution_id}")
            print(f"   • Estado: {final_status}")
            print(f"   • Status de registros: {records_status}")
            
            return {
                "execution_id": execution_id,
                "category": category,
                "page": page,
                "total_products": len(products),
                "valid_count": valid_count,
                "invalid_count": invalid_count,
                "success_rate": valid_count/len(products)*100
            }
            
        except Exception as e:
            print(f"❌ Error en el proceso de validación: {e}")
            
            # Intentar actualizar estado de error si es posible
            try:
                if 'execution_id' in locals():
                    self.db_connector.update_execution_record(execution_id, {
                        "end_time": datetime.now().isoformat(),
                        "status": "Error",
                        "records_status": "Error"
                    })
            except:
                pass
            
            return None


def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(
        description="Sistema de Validación con IA Generativa para datos de scraping en Supabase"
    )
    
    parser.add_argument(
        "--category", "-c",
        type=str,
        help="Categoría/brand específica a validar (opcional)"
    )
    
    parser.add_argument(
        "--page", "-p",
        type=int,
        help="Número de página a validar (opcional)"
    )
    
    args = parser.parse_args()
    
    print("🔍 Sistema de Validación con IA Generativa")
    print("=" * 80)
    
    # Crear instancia del validador
    validator = ValidatorIA()
    
    try:
        category = args.category
        page = args.page
        
        if category:
            print(f"🎯 Validando categoría: {category}")
        else:
            print("🎯 Validación completa (todas las categorías)")
            
        if page is not None:
            print(f"📄 Validando página: {page}")
        else:
            print("📄 Validación completa (todas las páginas)")
        
        result = validator.run_validation_process(category, page)
        
        if result:
            print(f"\n🎉 ¡Validación completada exitosamente!")
            print(f"   Tasa de éxito: {result['success_rate']:.1f}%")
            print(f"   Ejecución ID: {result['execution_id']}")
        else:
            print("\n❌ La validación falló")
            
    except KeyboardInterrupt:
        print("\n⏹️  Validación interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")


if __name__ == "__main__":
    main()
