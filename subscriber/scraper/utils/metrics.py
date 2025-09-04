"""
Sistema de métricas y monitoreo para el scraper.
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from loguru import logger


@dataclass
class ScrapingMetrics:
    """Métricas de scraping para un job específico."""
    job_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Métricas de productos
    total_products_found: int = 0
    products_extracted: int = 0
    products_failed: int = 0
    
    # Métricas de tiempo
    total_extraction_time: float = 0.0
    average_product_time: float = 0.0
    
    # Métricas de errores
    total_errors: int = 0
    error_types: Dict[str, int] = None
    
    # Métricas de rate limiting
    total_requests: int = 0
    rate_limited_requests: int = 0
    average_request_time: float = 0.0
    
    # Métricas de categoría
    category_id: str = ""
    page_number: int = 1
    
    def __post_init__(self):
        if self.error_types is None:
            self.error_types = {}
    
    def add_error(self, error_type: str):
        """Agregar un error del tipo especificado."""
        self.total_errors += 1
        self.error_types[error_type] = self.error_types.get(error_type, 0) + 1
    
    def finish(self):
        """Marcar el job como finalizado y calcular métricas finales."""
        self.end_time = datetime.now()
        
        if self.products_extracted > 0:
            self.average_product_time = self.total_extraction_time / self.products_extracted
        
        if self.total_requests > 0:
            self.average_request_time = self.total_extraction_time / self.total_requests
    
    def get_success_rate(self) -> float:
        """Calcular tasa de éxito."""
        if self.total_products_found == 0:
            return 0.0
        return (self.products_extracted / self.total_products_found) * 100
    
    def get_error_rate(self) -> float:
        """Calcular tasa de error."""
        if self.total_products_found == 0:
            return 0.0
        return (self.products_failed / self.total_products_found) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para serialización."""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        data['success_rate'] = self.get_success_rate()
        data['error_rate'] = self.get_error_rate()
        data['duration'] = (self.end_time - self.start_time).total_seconds() if self.end_time else 0
        return data


class MetricsCollector:
    """Recolector de métricas para el scraper."""
    
    def __init__(self, output_dir: str = "output/metrics"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_job: Optional[ScrapingMetrics] = None
        self.job_history: List[ScrapingMetrics] = []
        
        # Métricas globales
        self.global_stats = {
            "total_jobs": 0,
            "total_products_extracted": 0,
            "total_errors": 0,
            "total_extraction_time": 0.0,
            "start_time": datetime.now()
        }
    
    def start_job(self, job_id: str, category_id: str = "", page_number: int = 1) -> ScrapingMetrics:
        """Iniciar un nuevo job de scraping."""
        self.current_job = ScrapingMetrics(
            job_id=job_id,
            start_time=datetime.now(),
            category_id=category_id,
            page_number=page_number
        )
        
        logger.info(f"🚀 Iniciando job {job_id} - Categoría: {category_id}, Página: {page_number}")
        return self.current_job
    
    def finish_job(self):
        """Finalizar el job actual."""
        if self.current_job:
            self.current_job.finish()
            self.job_history.append(self.current_job)
            
            # Actualizar estadísticas globales
            self.global_stats["total_jobs"] += 1
            self.global_stats["total_products_extracted"] += self.current_job.products_extracted
            self.global_stats["total_errors"] += self.current_job.total_errors
            self.global_stats["total_extraction_time"] += self.current_job.total_extraction_time
            
            # Log de resumen
            logger.info(f"✅ Job {self.current_job.job_id} finalizado:")
            logger.info(f"   📊 Productos extraídos: {self.current_job.products_extracted}")
            logger.info(f"   ⏱️  Tiempo total: {self.current_job.total_extraction_time:.2f}s")
            logger.info(f"   🎯 Tasa de éxito: {self.current_job.get_success_rate():.1f}%")
            logger.info(f"   ❌ Errores: {self.current_job.total_errors}")
            
            self.current_job = None
    
    def update_product_count(self, found: int = 0, extracted: int = 0, failed: int = 0):
        """Actualizar contadores de productos."""
        if self.current_job:
            self.current_job.total_products_found += found
            self.current_job.products_extracted += extracted
            self.current_job.products_failed += failed
    
    def add_extraction_time(self, time_taken: float):
        """Agregar tiempo de extracción."""
        if self.current_job:
            self.current_job.total_extraction_time += time_taken
    
    def add_error(self, error_type: str):
        """Agregar un error."""
        if self.current_job:
            self.current_job.add_error(error_type)
    
    def update_request_metrics(self, total: int = 0, rate_limited: int = 0):
        """Actualizar métricas de requests."""
        if self.current_job:
            self.current_job.total_requests += total
            self.current_job.rate_limited_requests += rate_limited
    
    def get_current_job_stats(self) -> Optional[Dict[str, Any]]:
        """Obtener estadísticas del job actual."""
        if self.current_job:
            return self.current_job.to_dict()
        return None
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas globales."""
        elapsed_time = (datetime.now() - self.global_stats["start_time"]).total_seconds()
        
        return {
            **self.global_stats,
            "elapsed_time": elapsed_time,
            "average_job_time": self.global_stats["total_extraction_time"] / self.global_stats["total_jobs"] if self.global_stats["total_jobs"] > 0 else 0,
            "products_per_minute": (self.global_stats["total_products_extracted"] / elapsed_time) * 60 if elapsed_time > 0 else 0,
            "start_time": self.global_stats["start_time"].isoformat()
        }
    
    def save_metrics(self, filename: Optional[str] = None):
        """Guardar métricas en archivo JSON."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scraping_metrics_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        metrics_data = {
            "current_job": self.get_current_job_stats(),
            "global_stats": self.get_global_stats(),
            "job_history": [job.to_dict() for job in self.job_history[-10:]]  # Últimos 10 jobs
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📊 Métricas guardadas en: {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Error al guardar métricas: {e}")
    
    def print_summary(self):
        """Imprimir resumen de métricas en consola."""
        if not self.current_job:
            logger.info("📊 No hay job activo")
            return
        
        print("\n" + "="*60)
        print("📊 RESUMEN DE MÉTRICAS DEL SCRAPING")
        print("="*60)
        
        # Job actual
        print(f"🆔 Job ID: {self.current_job.job_id}")
        print(f"🏷️  Categoría: {self.current_job.category_id}")
        print(f"📄 Página: {self.current_job.page_number}")
        print(f"⏰ Inicio: {self.current_job.start_time.strftime('%H:%M:%S')}")
        
        if self.current_job.end_time:
            duration = (self.current_job.end_time - self.current_job.start_time).total_seconds()
            print(f"⏱️  Duración: {duration:.2f} segundos")
        
        # Productos
        print(f"\n📦 PRODUCTOS:")
        print(f"   Encontrados: {self.current_job.total_products_found}")
        print(f"   Extraídos: {self.current_job.products_extracted}")
        print(f"   Fallidos: {self.current_job.products_failed}")
        print(f"   Tasa de éxito: {self.current_job.get_success_rate():.1f}%")
        
        # Tiempo
        print(f"\n⏱️  TIEMPO:")
        print(f"   Total extracción: {self.current_job.total_extraction_time:.2f}s")
        if self.current_job.products_extracted > 0:
            print(f"   Promedio por producto: {self.current_job.average_product_time:.2f}s")
        
        # Errores
        if self.current_job.total_errors > 0:
            print(f"\n❌ ERRORES ({self.current_job.total_errors}):")
            for error_type, count in self.current_job.error_types.items():
                print(f"   {error_type}: {count}")
        
        # Requests
        if self.current_job.total_requests > 0:
            print(f"\n🌐 REQUESTS:")
            print(f"   Total: {self.current_job.total_requests}")
            print(f"   Rate limited: {self.current_job.rate_limited_requests}")
            if self.current_job.average_request_time > 0:
                print(f"   Tiempo promedio: {self.current_job.average_request_time:.2f}s")
        
        print("="*60)


# Instancia global del recolector de métricas
metrics_collector = MetricsCollector()
