"""
Módulo de cache en memoria para evitar tareas duplicadas de scraping.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from threading import Lock
from loguru import logger

from models.scraping_models import ScrapingResponse


@dataclass
class CacheEntry:
    """Entrada del cache con datos y timestamp."""
    data: ScrapingResponse
    created_at: float
    expires_at: float


class CacheManager:
    """
    Administrador de cache en memoria para respuestas de scraping.
    
    Evita crear tareas duplicadas validando combinaciones de page+category
    y guarda ScrapingResponse por máximo 1 hora.
    """
    
    def __init__(self, ttl_hours: float = 1.0):
        """
        Inicializar el cache manager.
        
        Args:
            ttl_hours: Tiempo de vida del cache en horas (default: 1 hora)
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._ttl_seconds = ttl_hours * 3600  # Convertir horas a segundos
        
        logger.info(f"CacheManager inicializado con TTL de {ttl_hours} hora(s)")
    
    def _generate_key(self, category: str, page: int) -> str:
        """
        Generar clave única para la combinación category+page.
        
        Args:
            category: Código de categoría (ej: MLU107)
            page: Número de página
            
        Returns:
            Clave única para el cache
        """
        return f"{category.upper()}:page:{page}"
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """
        Verificar si una entrada del cache ha expirado.
        
        Args:
            entry: Entrada del cache a verificar
            
        Returns:
            True si la entrada ha expirado, False en caso contrario
        """
        return time.time() > entry.expires_at
    
    def _cleanup_expired(self):
        """Limpiar entradas expiradas del cache."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items() 
            if current_time > entry.expires_at
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"Cache cleanup: eliminadas {len(expired_keys)} entradas expiradas")
    
    def get(self, category: str, page: int) -> Optional[ScrapingResponse]:
        """
        Obtener respuesta del cache si existe y no ha expirado.
        
        Args:
            category: Código de categoría
            page: Número de página
            
        Returns:
            ScrapingResponse si existe en cache, None en caso contrario
        """
        key = self._generate_key(category, page)
        
        with self._lock:
            # Limpiar entradas expiradas
            self._cleanup_expired()
            
            # Buscar en cache
            if key in self._cache:
                entry = self._cache[key]
                if not self._is_expired(entry):
                    logger.info(f"Cache HIT para {key}")
                    return entry.data
                else:
                    # Eliminar entrada expirada
                    del self._cache[key]
                    logger.debug(f"Entrada expirada eliminada: {key}")
            
            logger.debug(f"Cache MISS para {key}")
            return None
    
    def set(self, category: str, page: int, response: ScrapingResponse):
        """
        Guardar respuesta en el cache.
        
        Args:
            category: Código de categoría
            page: Número de página
            response: Respuesta de scraping a cachear
        """
        key = self._generate_key(category, page)
        current_time = time.time()
        expires_at = current_time + self._ttl_seconds
        
        entry = CacheEntry(
            data=response,
            created_at=current_time,
            expires_at=expires_at
        )
        
        with self._lock:
            self._cache[key] = entry
            
        expires_datetime = datetime.fromtimestamp(expires_at)
        logger.info(f"Cache SET para {key}, expira: {expires_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def invalidate(self, category: str, page: int) -> bool:
        """
        Invalidar (eliminar) entrada específica del cache.
        
        Args:
            category: Código de categoría
            page: Número de página
            
        Returns:
            True si se eliminó una entrada, False si no existía
        """
        key = self._generate_key(category, page)
        
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.info(f"Cache invalidado para {key}")
                return True
            
            logger.debug(f"No se encontró entrada para invalidar: {key}")
            return False
    
    def clear(self):
        """Limpiar todo el cache."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache limpiado completamente, {count} entradas eliminadas")
    
    def get_stats(self) -> Dict[str, any]:
        """
        Obtener estadísticas del cache.
        
        Returns:
            Diccionario con estadísticas del cache
        """
        with self._lock:
            # Limpiar expiradas para estadísticas precisas
            self._cleanup_expired()
            
            total_entries = len(self._cache)
            current_time = time.time()
            
            # Calcular tiempo promedio hasta expiración
            if total_entries > 0:
                avg_time_to_expire = sum(
                    entry.expires_at - current_time 
                    for entry in self._cache.values()
                ) / total_entries
            else:
                avg_time_to_expire = 0
            
            return {
                "total_entries": total_entries,
                "ttl_seconds": self._ttl_seconds,
                "avg_time_to_expire_seconds": avg_time_to_expire,
                "memory_usage_mb": sum(
                    len(str(entry.data.dict())) for entry in self._cache.values()
                ) / (1024 * 1024)  # Estimación aproximada
            }
    
    def list_keys(self) -> list[str]:
        """
        Listar todas las claves activas en el cache.
        
        Returns:
            Lista de claves en el cache
        """
        with self._lock:
            self._cleanup_expired()
            return list(self._cache.keys())


# Instancia global del cache manager
cache_manager = CacheManager()
