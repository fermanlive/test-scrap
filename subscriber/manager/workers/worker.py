"""
Worker de Celery para procesar tareas de scraping en background.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import asyncio
from loguru import logger

# Agregar el directorio del proyecto al path
sys.path.append(str(Path(__file__).parent.parent))

from celery import Celery
from config import RABBITMQ_CONFIG
from scraper.services import ScraperService
from models import ScrapingResult

# Configurar Celery con RabbitMQ
celery_app = Celery(
    "mercadolibre_scraper",
    broker=f"amqp://{RABBITMQ_CONFIG['user']}:{RABBITMQ_CONFIG['password']}@{RABBITMQ_CONFIG['host']}:{RABBITMQ_CONFIG['port']}/{RABBITMQ_CONFIG['vhost']}",
    backend=f"rpc://{RABBITMQ_CONFIG['host']}:{RABBITMQ_CONFIG['port']}"
)

# Configurar Celery
celery_app.conf.update({
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "UTC",
    "enable_utc": True,
})

# Configurar logging
logger.add(
    Path(__file__).parent.parent / "logs" / "worker.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO"
)


@celery_app.task(bind=True, name="scrape_products")
def scrape_products_task(self, url: str, max_products: int, task_id: str = None):
    """
    Tarea de Celery para ejecutar scraping de productos.
    
    Args:
        url: URL a procesar
        max_products: Número máximo de productos a extraer
        task_id: ID de la tarea (opcional)
        
    Returns:
        Resultado del scraping
    """
    try:
        logger.info(f"🚀 Worker iniciando scraping: {url} para {max_products} productos")
        
        # Crear servicio del scraper
        scraper_service = ScraperService()
        
        if not scraper_service.is_available():
            raise RuntimeError("Scraper no disponible")
        
        # Ejecutar scraping de forma asíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                scraper_service.scrape_products(url, max_products)
            )
            
            # Asignar task_id si se proporciona
            if task_id:
                result.task_id = task_id
            
            logger.info(f"✅ Worker completó scraping: {result.products_count} productos")
            return result.dict()
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"❌ Error en worker de scraping: {e}")
        
        # Crear resultado de error
        error_result = ScrapingResult(
            task_id=task_id or "",
            products_count=0,
            success_rate=0.0,
            duration=0.0,
            output_file="",
            errors=[str(e)]
        )
        
        # Marcar tarea como fallida
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "result": error_result.dict()}
        )
        
        raise


@celery_app.task(name="cleanup_old_files")
def cleanup_old_files_task(days_old: int = 7):
    """
    Tarea de Celery para limpiar archivos antiguos.
    
    Args:
        days_old: Días de antigüedad para limpiar
        
    Returns:
        Número de archivos eliminados
    """
    try:
        logger.info(f"🧹 Worker iniciando limpieza de archivos de {days_old} días")
        
        # Crear servicio del scraper
        scraper_service = ScraperService()
        
        # Ejecutar limpieza de forma asíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            deleted_count = loop.run_until_complete(
                scraper_service.cleanup_old_files(days_old)
            )
            
            logger.info(f"✅ Worker completó limpieza: {deleted_count} archivos eliminados")
            return {"deleted_count": deleted_count}
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"❌ Error en worker de limpieza: {e}")
        raise


@celery_app.task(name="get_scraping_stats")
def get_scraping_stats_task():
    """
    Tarea de Celery para obtener estadísticas del scraper.
    
    Returns:
        Estadísticas del scraper
    """
    try:
        logger.info("📊 Worker obteniendo estadísticas del scraper")
        
        # Crear servicio del scraper
        scraper_service = ScraperService()
        
        # Ejecutar obtención de estadísticas de forma asíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            stats = loop.run_until_complete(
                scraper_service.get_scraping_stats()
            )
            
            logger.info("✅ Worker obtuvo estadísticas del scraper")
            return stats
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"❌ Error en worker de estadísticas: {e}")
        raise


def start_worker():
    """Función para iniciar el worker desde Poetry."""
    try:
        logger.info("🚀 Iniciando worker de Celery...")
        
        # Iniciar worker
        celery_app.worker_main([
            "worker",
            "--loglevel=info",
            "--concurrency=1",
            "--pool=solo"
        ])
        
    except Exception as e:
        logger.error(f"❌ Error al iniciar worker: {e}")
        sys.exit(1)


if __name__ == "__main__":
    start_worker()
