"""
Tests para el sistema de rate limiting y tolerancia a fallos.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch

from scraper.utils.rate_limiter import (
    RateLimitConfig,
    RetryConfig,
    RateLimiter,
    RetryHandler,
    ScrapingRateLimiter,
    extract_domain_from_url
)
from scraper.utils.exception_handler import (
    handle_scraping_exceptions,
    ExceptionContext,
    NavigationException,
    ExtractionException
)


class TestRateLimiter:
    """Tests para el RateLimiter."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_acquire(self):
        """Test que el rate limiter respeta los límites de tiempo."""
        config = RateLimitConfig(
            requests_per_minute=60,
            delay_between_requests=1.0,
            max_requests_per_second=1.0
        )
        rate_limiter = RateLimiter(config)
        
        start_time = time.time()
        
        # Primera petición debería pasar inmediatamente
        await rate_limiter.acquire("test.com")
        first_time = time.time()
        
        # Segunda petición debería esperar al menos 1 segundo
        await rate_limiter.acquire("test.com")
        second_time = time.time()
        
        # Verificar que pasó al menos 1 segundo
        assert second_time - first_time >= 0.9  # Margen de tolerancia
        
        rate_limiter.release()
        rate_limiter.release()
    
    @pytest.mark.asyncio
    async def test_domain_specific_limits(self):
        """Test que los límites son específicos por dominio."""
        config = RateLimitConfig(
            requests_per_minute=60,
            delay_between_requests=1.0,
            max_requests_per_second=1.0
        )
        rate_limiter = RateLimiter(config)
        
        start_time = time.time()
        
        # Petición a dominio 1
        await rate_limiter.acquire("domain1.com")
        first_time = time.time()
        
        # Petición a dominio 2 debería pasar inmediatamente
        await rate_limiter.acquire("domain2.com")
        second_time = time.time()
        
        # Verificar que no hubo delay entre dominios diferentes
        assert second_time - first_time < 0.5
        
        rate_limiter.release()
        rate_limiter.release()


class TestRetryHandler:
    """Tests para el RetryHandler."""
    
    @pytest.mark.asyncio
    async def test_retry_success_on_second_attempt(self):
        """Test que el retry funciona correctamente."""
        config = RetryConfig(max_attempts=3, base_delay=0.1)
        retry_handler = RetryHandler(config)
        
        attempt_count = 0
        
        async def failing_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise Exception("Simulated failure")
            return "success"
        
        result = await retry_handler.execute_with_retry(failing_function)
        
        assert result == "success"
        assert attempt_count == 2
    
    @pytest.mark.asyncio
    async def test_retry_max_attempts_exceeded(self):
        """Test que se lanza excepción cuando se exceden los intentos máximos."""
        config = RetryConfig(max_attempts=2, base_delay=0.1)
        retry_handler = RetryHandler(config)
        
        async def always_failing_function():
            raise Exception("Always fails")
        
        with pytest.raises(Exception, match="Always fails"):
            await retry_handler.execute_with_retry(always_failing_function)
    
    @pytest.mark.asyncio
    async def test_non_retryable_exceptions(self):
        """Test que las excepciones no reintentables se lanzan inmediatamente."""
        config = RetryConfig(max_attempts=3, base_delay=0.1)
        retry_handler = RetryHandler(config)
        
        async def function_with_value_error():
            raise ValueError("Non-retryable error")
        
        with pytest.raises(ValueError, match="Non-retryable error"):
            await retry_handler.execute_with_retry(function_with_value_error)


class TestScrapingRateLimiter:
    """Tests para el ScrapingRateLimiter."""
    
    @pytest.mark.asyncio
    async def test_execute_request_success(self):
        """Test ejecución exitosa de petición."""
        rate_limiter = ScrapingRateLimiter(RateLimitConfig())
        
        async def mock_function():
            return "success"
        
        result = await rate_limiter.execute_request(mock_function, domain="test.com")
        
        assert result == "success"
        
        stats = rate_limiter.get_stats()
        assert stats["total_requests"] == 1
        assert stats["successful_requests"] == 1
        assert stats["failed_requests"] == 0
    
    @pytest.mark.asyncio
    async def test_execute_request_failure(self):
        """Test manejo de fallos en peticiones."""
        rate_limiter = ScrapingRateLimiter(RateLimitConfig())
        
        async def failing_function():
            raise Exception("Test failure")
        
        with pytest.raises(Exception, match="Test failure"):
            await rate_limiter.execute_request(failing_function, domain="test.com")
        
        stats = rate_limiter.get_stats()
        assert stats["total_requests"] == 1
        assert stats["successful_requests"] == 0
        assert stats["failed_requests"] == 1


class TestExceptionHandler:
    """Tests para el manejo de excepciones."""
    
    @pytest.mark.asyncio
    async def test_handle_scraping_exceptions_decorator(self):
        """Test del decorador de manejo de excepciones."""
        
        @handle_scraping_exceptions(max_retries=2, default_return="default")
        async def failing_function():
            raise NavigationException("Navigation failed")
        
        result = await failing_function()
        assert result == "default"
    
    def test_exception_context(self):
        """Test del contexto de excepciones."""
        context = ExceptionContext("test_task")
        
        context.log_error("Test error")
        context.log_warning("Test warning")
        
        summary = context.get_summary()
        
        assert summary["error_count"] == 1
        assert summary["warning_count"] == 1
        assert len(summary["errors"]) == 1
        assert len(summary["warnings"]) == 1


class TestUtilityFunctions:
    """Tests para funciones utilitarias."""
    
    def test_extract_domain_from_url(self):
        """Test extracción de dominio de URL."""
        assert extract_domain_from_url("https://www.mercadolibre.com.uy/producto") == "www.mercadolibre.com.uy"
        assert extract_domain_from_url("http://example.com/path") == "example.com"
        assert extract_domain_from_url("invalid-url") == "default"
        assert extract_domain_from_url("") == "default"


@pytest.mark.asyncio
async def test_integration_rate_limiting_and_retry():
    """Test de integración entre rate limiting y retry."""
    rate_limiter = ScrapingRateLimiter(RateLimitConfig())
    
    attempt_count = 0
    
    async def flaky_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise NavigationException("Temporary failure")
        return f"Success on attempt {attempt_count}"
    
    result = await rate_limiter.execute_request(flaky_function, domain="test.com")
    
    assert result == "Success on attempt 3"
    assert attempt_count == 3
    
    stats = rate_limiter.get_stats()
    assert stats["total_requests"] == 1
    assert stats["successful_requests"] == 1


if __name__ == "__main__":
    pytest.main([__file__])
