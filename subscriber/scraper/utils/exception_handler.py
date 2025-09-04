"""
Manejo robusto de excepciones para el scraper.
"""

import asyncio
import functools
from typing import Callable, Any, Optional
from loguru import logger


class ScrapingException(Exception):
    """Excepción base para errores de scraping."""
    pass


class NavigationException(ScrapingException):
    """Excepción para errores de navegación."""
    pass


class ExtractionException(ScrapingException):
    """Excepción para errores de extracción de datos."""
    pass


class RateLimitException(ScrapingException):
    """Excepción para errores de rate limiting."""
    pass


def handle_scraping_exceptions(
    max_retries: int = 3,
    default_return: Any = None,
    log_errors: bool = True
):
    """
    Decorador para manejar excepciones de scraping de manera robusta.
    
    Args:
        max_retries: Número máximo de reintentos
        default_return: Valor a retornar en caso de error
        log_errors: Si registrar errores en el log
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                        
                except NavigationException as e:
                    if log_errors:
                        logger.error(f"Error de navegación en intento {attempt + 1}: {e}")
                    last_exception = e
                    if attempt < max_retries:
                        await asyncio.sleep(1.0 * (attempt + 1))  # Backoff lineal
                        continue
                    break
                    
                except ExtractionException as e:
                    if log_errors:
                        logger.warning(f"Error de extracción en intento {attempt + 1}: {e}")
                    last_exception = e
                    if attempt < max_retries:
                        await asyncio.sleep(0.5 * (attempt + 1))  # Backoff más rápido
                        continue
                    break
                    
                except RateLimitException as e:
                    if log_errors:
                        logger.warning(f"Rate limit alcanzado en intento {attempt + 1}: {e}")
                    last_exception = e
                    if attempt < max_retries:
                        await asyncio.sleep(2.0 * (attempt + 1))  # Backoff más lento
                        continue
                    break
                    
                except Exception as e:
                    if log_errors:
                        logger.error(f"Error inesperado en intento {attempt + 1}: {type(e).__name__}: {e}")
                    last_exception = e
                    if attempt < max_retries:
                        await asyncio.sleep(1.0 * (attempt + 1))
                        continue
                    break
            
            # Si llegamos aquí, todos los intentos fallaron
            if log_errors and last_exception:
                logger.error(f"Todos los {max_retries + 1} intentos fallaron. Último error: {last_exception}")
            
            return default_return
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except NavigationException as e:
                    if log_errors:
                        logger.error(f"Error de navegación en intento {attempt + 1}: {e}")
                    last_exception = e
                    if attempt < max_retries:
                        import time
                        time.sleep(1.0 * (attempt + 1))
                        continue
                    break
                    
                except ExtractionException as e:
                    if log_errors:
                        logger.warning(f"Error de extracción en intento {attempt + 1}: {e}")
                    last_exception = e
                    if attempt < max_retries:
                        import time
                        time.sleep(0.5 * (attempt + 1))
                        continue
                    break
                    
                except RateLimitException as e:
                    if log_errors:
                        logger.warning(f"Rate limit alcanzado en intento {attempt + 1}: {e}")
                    last_exception = e
                    if attempt < max_retries:
                        import time
                        time.sleep(2.0 * (attempt + 1))
                        continue
                    break
                    
                except Exception as e:
                    if log_errors:
                        logger.error(f"Error inesperado en intento {attempt + 1}: {type(e).__name__}: {e}")
                    last_exception = e
                    if attempt < max_retries:
                        import time
                        time.sleep(1.0 * (attempt + 1))
                        continue
                    break
            
            # Si llegamos aquí, todos los intentos fallaron
            if log_errors and last_exception:
                logger.error(f"Todos los {max_retries + 1} intentos fallaron. Último error: {last_exception}")
            
            return default_return
        
        # Retornar el wrapper apropiado
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def safe_extract(func: Callable, default: Any = None, log_errors: bool = True) -> Any:
    """
    Ejecutar una función de extracción de manera segura.
    
    Args:
        func: Función a ejecutar
        default: Valor por defecto en caso de error
        log_errors: Si registrar errores
        
    Returns:
        Resultado de la función o valor por defecto
    """
    try:
        if asyncio.iscoroutinefunction(func):
            return asyncio.run(func())
        else:
            return func()
    except Exception as e:
        if log_errors:
            logger.debug(f"Error en extracción segura: {e}")
        return default


class ExceptionContext:
    """Contexto para manejar excepciones de manera centralizada."""
    
    def __init__(self, task_id: str = None):
        self.task_id = task_id
        self.errors = []
        self.warnings = []
    
    def log_error(self, message: str, exception: Exception = None):
        """Registrar un error."""
        error_msg = f"Task {self.task_id} - {message}" if self.task_id else message
        if exception:
            error_msg += f": {type(exception).__name__}: {exception}"
        
        logger.error(error_msg)
        self.errors.append(error_msg)
    
    def log_warning(self, message: str, exception: Exception = None):
        """Registrar una advertencia."""
        warning_msg = f"Task {self.task_id} - {message}" if self.task_id else message
        if exception:
            warning_msg += f": {type(exception).__name__}: {exception}"
        
        logger.warning(warning_msg)
        self.warnings.append(warning_msg)
    
    def get_summary(self) -> dict:
        """Obtener resumen de errores y advertencias."""
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings)
        }
