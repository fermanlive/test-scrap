"""
Servicio que integra con el scraper existente de Mercado Libre Uruguay.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import json
from loguru import logger

# Agregar el directorio del proyecto al path para importar el scraper
sys.path.append(str(Path(__file__).parent.parent))

from models import ScrapingResult
from config import SCRAPER_CONFIG
from scraper.simple_scraper import SimpleScraper
from scraper.utils.rate_limiter import scraping_rate_limiter

class ScraperService:
    """Servicio que integra con el scraper existente."""
    
    def __init__(self):
        """Inicializar el servicio del scraper."""
        self.base_url = SCRAPER_CONFIG["base_url"]
        self.output_dir = SCRAPER_CONFIG["output_dir"]
        self.output_dir.mkdir(exist_ok=True)
        
        # Verificar que el scraper esté disponible
        try:
            # Solo verificar que la clase se pueda importar
            self.scraper_class = SimpleScraper
            self.scraper_available = True
            logger.info("✅ Scraper disponible")
        except ImportError as e:
            logger.error(f"❌ Error al importar scraper: {e}")
            self.scraper_available = False
    
    def is_available(self) -> bool:
        """
        Verificar si el scraper está disponible.
        
        Returns:
            True si el scraper está disponible
        """
        return self.scraper_available
    
    async def scrape_products(self, url: str, max_products: int, task_id: str = None) -> ScrapingResult:
        """
        Ejecutar scraping de productos.
        
        Args:
            url: URL a procesar
            max_products: Número máximo de productos a extraer
            task_id: ID de la tarea para logging
            
        Returns:
            Resultado del scraping
        """
        if not self.scraper_available:
            raise RuntimeError("Scraper no disponible")
        
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"🚀 Iniciando scraping de {url} para {max_products} productos")
            
            # Crear instancia del scraper
            scraper = self.scraper_class(task_id=task_id or "default")
            
            # Ejecutar scraping
            products = await scraper.scrape_listing_with_details(url, max_products)
            
            # Calcular duración
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Generar archivo de salida
            output_file = self._generate_output_file(products, url)
            
            # Calcular tasa de éxito
            success_rate = 100.0 if products else 0.0
            
            logger.info(f"✅ Scraping completado: {len(products)} productos en {duration:.2f}s")
            
            return ScrapingResult(
                task_id="",  # Se asignará desde el caller
                products_count=len(products),
                success_rate=success_rate,
                duration=duration,
                output_file=str(output_file),
                errors=[]
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"❌ Error en scraping: {e}")
            
            return ScrapingResult(
                task_id="",
                products_count=0,
                success_rate=0.0,
                duration=duration,
                output_file="",
                errors=[str(e)]
            )
    
    def _generate_output_file(self, products: List, url: str) -> Path:
        """
        Generar archivo de salida con los productos extraídos.
        
        Args:
            products: Lista de productos extraídos
            url: URL procesada
            
        Returns:
            Ruta del archivo generado
        """
        try:
            # Generar nombre de archivo único
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"scraping_{timestamp}.json"
            output_path = self.output_dir / filename
            
            # Convertir productos a formato serializable
            serializable_products = []
            for product in products:
                try:
                    # Convertir el producto a diccionario
                    if hasattr(product, 'to_dict'):
                        product_dict = product.to_dict()
                    elif hasattr(product, '__dict__'):
                        product_dict = product.__dict__
                    else:
                        product_dict = str(product)
                    
                    serializable_products.append(product_dict)
                except Exception as e:
                    logger.warning(f"Error al serializar producto: {e}")
                    serializable_products.append({"error": str(e), "raw": str(product)})
            
            # Crear estructura de datos completa
            output_data = {
                "metadata": {
                    "url": url,
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_products": len(products),
                    "scraper_version": "1.0.0"
                },
                "products": serializable_products
            }
            
            # Guardar archivo JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"💾 Archivo de salida generado: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Error al generar archivo de salida: {e}")
            # Crear archivo de error
            error_filename = f"error_{timestamp}.json"
            error_path = self.output_dir / error_filename
            
            error_data = {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "url": url
            }
            
            with open(error_path, 'w', encoding='utf-8') as f:
                json.dump(error_data, f, ensure_ascii=False, indent=2)
            
            return error_path
    
    async def get_scraping_stats(self) -> dict:
        """
        Obtener estadísticas del scraper.
        
        Returns:
            Diccionario con estadísticas
        """
        try:
            # Contar archivos de salida
            json_files = list(self.output_dir.glob("*.json"))
            total_files = len(json_files)
            
            # Contar archivos por tipo
            success_files = len([f for f in json_files if "scraping_" in f.name])
            error_files = len([f for f in json_files if "error_" in f.name])
            
            # Calcular tamaño total
            total_size = sum(f.stat().st_size for f in json_files)
            
            return {
                "total_files": total_files,
                "success_files": success_files,
                "error_files": error_files,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "output_directory": str(self.output_dir)
            }
            
        except Exception as e:
            logger.error(f"❌ Error al obtener estadísticas: {e}")
            return {
                "total_files": 0,
                "success_files": 0,
                "error_files": 0,
                "total_size_mb": 0,
                "output_directory": str(self.output_dir),
                "error": str(e)
            }
    
    async def cleanup_old_files(self, days_old: int = 7) -> int:
        """
        Limpiar archivos antiguos.
        
        Args:
            days_old: Días de antigüedad para limpiar
            
        Returns:
            Número de archivos eliminados
        """
        try:
            deleted_count = 0
            current_time = datetime.utcnow()
            
            for file_path in self.output_dir.glob("*.json"):
                try:
                    # Obtener tiempo de modificación
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    days_diff = (current_time - mtime).days
                    
                    if days_diff > days_old:
                        file_path.unlink()
                        deleted_count += 1
                        logger.debug(f"🗑️ Archivo eliminado: {file_path}")
                        
                except Exception as e:
                    logger.warning(f"Error al procesar archivo {file_path} para limpieza: {e}")
                    continue
            
            logger.info(f"🧹 Limpiados {deleted_count} archivos antiguos")
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Error al limpiar archivos: {e}")
            return 0
    
    async def get_rate_limiter_stats(self) -> dict:
        """
        Obtener estadísticas del rate limiter.
        
        Returns:
            Diccionario con estadísticas del rate limiter
        """
        try:
            return scraping_rate_limiter.get_stats()
        except Exception as e:
            logger.error(f"❌ Error al obtener estadísticas del rate limiter: {e}")
            return {"error": str(e)}
