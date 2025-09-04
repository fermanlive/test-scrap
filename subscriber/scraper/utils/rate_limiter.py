"""
Sistema de Rate Limiting y Retry Logic para el scraper.
"""

import asyncio
import random
import time
from typing import Callable, Any, Optional
from dataclasses import dataclass
from urllib.parse import urlparse
from loguru import logger


@dataclass
class RateLimitConfig:
    """Configuración para rate limiting."""
    requests_per_minute: int = 30
    delay_between_requests: float = 1.0  # 1 segundo entre requests
    burst_size: int = 5
    jitter: bool = True
    max_concurrent: int = 3
    max_requests_per_second: float = 1.0  # Máximo 1 request por segundo


@dataclass
class RetryConfig:
    """Configuración para retry logic."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


class RateLimiter:
    """Controla la velocidad de las peticiones para evitar bloqueos."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.last_request_time = 0.0
        self.request_count = 0
        self.minute_start = time.time()
        self.semaphore = asyncio.Semaphore(config.max_concurrent)
        self.domain_limits = {}  # Límites por dominio
    
    async def acquire(self, domain: str = "default"):
        """Adquirir permiso para hacer una petición."""
        await self.semaphore.acquire()
        
        # Inicializar límites del dominio si no existen
        if domain not in self.domain_limits:
            self.domain_limits[domain] = {
                "last_request_time": 0.0,
                "request_count": 0,
                "minute_start": time.time()
            }
        
        domain_limit = self.domain_limits[domain]
        current_time = time.time()
        time_since_last = current_time - domain_limit["last_request_time"]
        
        # Verificar límite por minuto para el dominio
        if current_time - domain_limit["minute_start"] >= 60:
            domain_limit["request_count"] = 0
            domain_limit["minute_start"] = current_time
        
        if domain_limit["request_count"] >= self.config.requests_per_minute:
            # Esperar hasta el siguiente minuto
            wait_time = 60 - (current_time - domain_limit["minute_start"])
            logger.info(f"Rate limit alcanzado para dominio {domain}. Esperando {wait_time:.1f} segundos...")
            await asyncio.sleep(wait_time)
            domain_limit["request_count"] = 0
            domain_limit["minute_start"] = time.time()
        
        # Verificar límite de 1 request por segundo
        min_delay = 1.0 / self.config.max_requests_per_second
        if time_since_last < min_delay:
            delay = min_delay - time_since_last
            if self.config.jitter:
                delay += random.uniform(0, 0.2)  # Jitter reducido para mayor precisión
            logger.debug(f"Rate limiting para {domain}: esperando {delay:.2f}s")
            await asyncio.sleep(delay)
        
        # Actualizar tiempos del dominio
        domain_limit["last_request_time"] = time.time()
        domain_limit["request_count"] += 1
        
        # Actualizar contadores globales
        self.last_request_time = time.time()
        self.request_count += 1
    
    def release(self):
        """Liberar el semáforo después de una petición."""
        self.semaphore.release()


class RetryHandler:
    """Maneja reintentos con backoff exponencial."""
    
    def __init__(self, config: RetryConfig):
        self.config = config
        # Excepciones que no deben reintentarse
        self.non_retryable_exceptions = (
            ValueError,
            TypeError,
            AttributeError,
            KeyError,
            ImportError
        )
    
    async def execute_with_retry(
        self, 
        func: Callable, 
        *args, 
        **kwargs
    ) -> Any:
        """
        Ejecutar una función con reintentos automáticos.
        
        Args:
            func: Función a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos nombrados
            
        Returns:
            Resultado de la función
            
        Raises:
            Exception: Si todos los reintentos fallan
        """
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                if attempt > 1:
                    logger.info(f"✅ Operación exitosa en el intento {attempt}")
                
                return result
                
            except Exception as e:
                last_exception = e
                logger.warning(f"❌ Intento {attempt} falló: {type(e).__name__}: {e}")
                
                # Verificar si la excepción no debe reintentarse
                if isinstance(e, self.non_retryable_exceptions):
                    logger.error(f"🚫 Excepción no reintentable: {type(e).__name__}")
                    raise e
                
                if attempt < self.config.max_attempts:
                    delay = self._calculate_delay(attempt)
                    logger.info(f"🔄 Reintentando en {delay:.1f} segundos...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"💥 Todos los {self.config.max_attempts} intentos fallaron")
        
        # Si llegamos aquí, todos los intentos fallaron
        raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calcular delay para el siguiente intento."""
        delay = self.config.base_delay * (self.config.exponential_base ** (attempt - 1))
        
        # Aplicar jitter si está habilitado
        if self.config.jitter:
            delay *= random.uniform(0.5, 1.5)
        
        # Limitar delay máximo
        return min(delay, self.config.max_delay)


class ScrapingRateLimiter:
    """Rate limiter específico para scraping con métricas."""
    
    def __init__(self, config: RateLimitConfig, retry_config: RetryConfig = None):
        self.rate_limiter = RateLimiter(config)
        self.retry_handler = RetryHandler(retry_config or DEFAULT_RETRY_CONFIG)
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limited_requests": 0,
            "total_wait_time": 0.0,
            "start_time": time.time()
        }
    
    async def execute_request(
        self, 
        func: Callable, 
        domain: str = "default",
        *args, 
        **kwargs
    ) -> Any:
        """
        Ejecutar una petición con rate limiting y retry.
        
        Args:
            func: Función a ejecutar
            domain: Dominio para aplicar rate limiting específico
            *args: Argumentos posicionales
            **kwargs: Argumentos nombrados
            
        Returns:
            Resultado de la función
        """
        start_time = time.time()
        
        try:
            # Adquirir permiso del rate limiter para el dominio específico
            await self.rate_limiter.acquire(domain)
            
            # Ejecutar con retry
            result = await self.retry_handler.execute_with_retry(func, *args, **kwargs)
            
            # Actualizar estadísticas
            self.stats["total_requests"] += 1
            self.stats["successful_requests"] += 1
            
            return result
            
        except Exception as e:
            self.stats["total_requests"] += 1
            self.stats["failed_requests"] += 1
            raise e
        
        finally:
            # Liberar rate limiter
            self.rate_limiter.release()
            
            # Actualizar tiempo de espera
            wait_time = time.time() - start_time
            self.stats["total_wait_time"] += wait_time
    
    def get_stats(self) -> dict:
        """Obtener estadísticas del rate limiter."""
        elapsed_time = time.time() - self.stats["start_time"]
        
        return {
            **self.stats,
            "elapsed_time": elapsed_time,
            "requests_per_minute": (self.stats["total_requests"] / elapsed_time) * 60 if elapsed_time > 0 else 0,
            "success_rate": (self.stats["successful_requests"] / self.stats["total_requests"] * 100) if self.stats["total_requests"] > 0 else 0,
            "average_wait_time": self.stats["total_wait_time"] / self.stats["total_requests"] if self.stats["total_requests"] > 0 else 0
        }
    
    def reset_stats(self):
        """Reiniciar estadísticas."""
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limited_requests": 0,
            "total_wait_time": 0.0,
            "start_time": time.time()
        }


# Configuraciones predefinidas
DEFAULT_RATE_LIMIT_CONFIG = RateLimitConfig(
    requests_per_minute=30,
    delay_between_requests=1.0,  # 1 segundo entre requests
    burst_size=5,
    jitter=True,
    max_concurrent=3,
    max_requests_per_second=1.0  # Máximo 1 request por segundo
)

DEFAULT_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True
)

def extract_domain_from_url(url: str) -> str:
    """
    Extraer el dominio de una URL.
    
    Args:
        url: URL de la cual extraer el dominio
        
    Returns:
        Dominio extraído o 'default' si hay error
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.hostname
        return domain if domain else "default"
    except Exception:
        return "default"


# Instancia global para uso en el scraper
scraping_rate_limiter = ScrapingRateLimiter(DEFAULT_RATE_LIMIT_CONFIG)
