# Sistema de Rate Limiting y Tolerancia a Fallos

Este documento describe el sistema implementado para manejar rate limiting y tolerancia a fallos en el scraper de Mercado Libre.

## Características Implementadas

### 1. Rate Limiting por Dominio

- **Límite de 1 request por segundo** por dominio
- **Límite de 30 requests por minuto** por dominio
- **Control de concurrencia** con semáforos
- **Jitter aleatorio** para evitar patrones predecibles

### 2. Retry Logic con Backoff Exponencial

- **Máximo 3 intentos** por operación
- **Backoff exponencial** con base 2.0
- **Jitter aleatorio** para distribuir la carga
- **Delay máximo** de 60 segundos
- **Excepciones no reintentables** (ValueError, TypeError, etc.)

### 3. Manejo Robusto de Excepciones

- **Excepciones específicas** para diferentes tipos de errores
- **Contexto de excepciones** para tracking centralizado
- **Decoradores** para manejo automático de errores
- **Logging detallado** de errores y advertencias

## Configuración

### Rate Limiting

```python
RATE_LIMIT_CONFIG = {
    "requests_per_minute": 30,
    "delay_between_requests": 1.0,  # 1 segundo entre requests
    "burst_size": 5,
    "max_requests_per_second": 1.0,  # Máximo 1 request por segundo
    "jitter": True,
    "max_concurrent": 3,
}
```

### Retry Logic

```python
RETRY_CONFIG = {
    "max_attempts": 3,
    "base_delay": 1.0,
    "max_delay": 60.0,
    "exponential_base": 2.0,
    "jitter": True,
}
```

### Manejo de Excepciones

```python
EXCEPTION_CONFIG = {
    "max_retries": 3,
    "navigation_retry_delay": 1.0,
    "extraction_retry_delay": 0.5,
    "rate_limit_retry_delay": 2.0,
    "log_errors": True,
}
```

## Uso

### Rate Limiter Básico

```python
from scraper.utils.rate_limiter import scraping_rate_limiter, extract_domain_from_url

# Ejecutar una petición con rate limiting
domain = extract_domain_from_url("https://www.mercadolibre.com.uy")
result = await scraping_rate_limiter.execute_request(
    my_function,
    domain=domain,
    arg1=value1,
    arg2=value2
)
```

### Decorador de Manejo de Excepciones

```python
from scraper.utils.exception_handler import handle_scraping_exceptions

@handle_scraping_exceptions(max_retries=3, default_return=None)
async def my_scraping_function():
    # Tu código de scraping aquí
    pass
```

### Contexto de Excepciones

```python
from scraper.utils.exception_handler import ExceptionContext

exception_context = ExceptionContext(task_id="task_123")

try:
    # Operación que puede fallar
    pass
except Exception as e:
    exception_context.log_error("Error en operación", e)

# Obtener resumen
summary = exception_context.get_summary()
```

## Estadísticas

El sistema proporciona estadísticas detalladas:

```python
# Obtener estadísticas del rate limiter
stats = scraping_rate_limiter.get_stats()

# Estadísticas incluyen:
# - total_requests: Total de peticiones realizadas
# - successful_requests: Peticiones exitosas
# - failed_requests: Peticiones fallidas
# - requests_per_minute: Tasa actual de peticiones
# - success_rate: Porcentaje de éxito
# - average_wait_time: Tiempo promedio de espera
```

## Excepciones Específicas

### NavigationException
- Errores de navegación web
- Timeouts de página
- Errores de red

### ExtractionException
- Errores al extraer datos
- Elementos no encontrados
- Errores de parsing

### RateLimitException
- Límites de velocidad alcanzados
- Bloqueos temporales

## Mejores Prácticas

1. **Siempre usar el rate limiter** para peticiones web
2. **Aplicar decoradores de excepciones** a funciones críticas
3. **Monitorear estadísticas** regularmente
4. **Configurar timeouts apropiados** para cada operación
5. **Usar contextos de excepciones** para tracking centralizado

## Monitoreo

El sistema registra automáticamente:
- ✅ Operaciones exitosas
- ❌ Errores y fallos
- 🔄 Reintentos automáticos
- ⏱️ Tiempos de espera
- 📊 Estadísticas de rendimiento

## Variables de Entorno

```bash
# Configuración de rate limiting
RATE_LIMIT_DELAY=1.0
MAX_REQUESTS_PER_SECOND=1.0
MAX_CONCURRENT_REQUESTS=3

# Configuración de retry
MAX_RETRIES=3
RETRY_BASE_DELAY=1.0
RETRY_MAX_DELAY=60.0

# Configuración del navegador
BROWSER_TIMEOUT=30000
BROWSER_HEADLESS=true
```

## Troubleshooting

### Rate Limit Alcanzado
- Verificar configuración de `max_requests_per_second`
- Aumentar `delay_between_requests` si es necesario
- Revisar logs para patrones de peticiones

### Muchos Reintentos
- Verificar conectividad de red
- Revisar selectores CSS
- Aumentar timeouts si es necesario

### Errores de Navegación
- Verificar que el sitio web esté disponible
- Revisar configuración del navegador
- Comprobar headers y user agents
