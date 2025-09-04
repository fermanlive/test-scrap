#!/usr/bin/env python3
"""
Ejemplo de uso del sistema de rate limiting y tolerancia a fallos.
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
sys.path.append(str(Path(__file__).parent.parent))

from scraper.utils.rate_limiter import (
    scraping_rate_limiter, 
    extract_domain_from_url,
    RateLimitConfig,
    RetryConfig
)
from scraper.utils.exception_handler import (
    handle_scraping_exceptions,
    ExceptionContext,
    NavigationException,
    ExtractionException
)
from loguru import logger


async def simulate_web_request(url: str) -> dict:
    """
    Simular una petición web que puede fallar.
    """
    domain = extract_domain_from_url(url)
    logger.info(f"🌐 Simulando petición a {domain}")
    
    # Simular delay de red
    await asyncio.sleep(0.5)
    
    # Simular fallo ocasional
    import random
    if random.random() < 0.3:  # 30% de probabilidad de fallo
        raise NavigationException(f"Error simulado de navegación para {url}")
    
    return {
        "url": url,
        "domain": domain,
        "status": "success",
        "data": f"Datos extraídos de {url}"
    }


@handle_scraping_exceptions(max_retries=3, default_return=None)
async def extract_product_data(url: str) -> dict:
    """
    Extraer datos de un producto con manejo de excepciones.
    """
    logger.info(f"📦 Extrayendo datos del producto: {url}")
    
    # Simular extracción que puede fallar
    await asyncio.sleep(0.2)
    
    import random
    if random.random() < 0.2:  # 20% de probabilidad de fallo
        raise ExtractionException(f"Error simulado de extracción para {url}")
    
    return {
        "title": f"Producto de {extract_domain_from_url(url)}",
        "price": "100.00",
        "url": url
    }


async def demonstrate_rate_limiting():
    """
    Demostrar el sistema de rate limiting.
    """
    logger.info("🚀 Iniciando demostración de rate limiting")
    
    urls = [
        "https://www.mercadolibre.com.uy/producto1",
        "https://www.mercadolibre.com.uy/producto2",
        "https://www.mercadolibre.com.uy/producto3",
        "https://www.mercadolibre.com.uy/producto4",
        "https://www.mercadolibre.com.uy/producto5",
    ]
    
    results = []
    
    for i, url in enumerate(urls):
        try:
            logger.info(f"📋 Procesando URL {i+1}/{len(urls)}")
            
            # Usar el rate limiter para la petición
            result = await scraping_rate_limiter.execute_request(
                simulate_web_request,
                domain=extract_domain_from_url(url),
                url=url
            )
            
            if result:
                results.append(result)
                logger.info(f"✅ Petición exitosa: {result['domain']}")
            else:
                logger.warning(f"⚠️ Petición falló: {url}")
                
        except Exception as e:
            logger.error(f"❌ Error procesando {url}: {e}")
    
    logger.info(f"📊 Procesadas {len(results)} peticiones exitosas de {len(urls)}")
    return results


async def demonstrate_exception_handling():
    """
    Demostrar el manejo de excepciones.
    """
    logger.info("🛡️ Iniciando demostración de manejo de excepciones")
    
    exception_context = ExceptionContext("demo_task")
    
    urls = [
        "https://www.mercadolibre.com.uy/producto1",
        "https://www.mercadolibre.com.uy/producto2",
        "https://www.mercadolibre.com.uy/producto3",
    ]
    
    results = []
    
    for url in urls:
        try:
            # Extraer datos con manejo automático de excepciones
            result = await extract_product_data(url)
            
            if result:
                results.append(result)
                logger.info(f"✅ Datos extraídos: {result['title']}")
            else:
                exception_context.log_warning(f"No se pudieron extraer datos de {url}")
                
        except Exception as e:
            exception_context.log_error(f"Error procesando {url}", e)
    
    # Mostrar resumen de excepciones
    summary = exception_context.get_summary()
    logger.info(f"📈 Resumen de excepciones: {summary['error_count']} errores, {summary['warning_count']} advertencias")
    
    return results


async def demonstrate_statistics():
    """
    Demostrar las estadísticas del rate limiter.
    """
    logger.info("📊 Obteniendo estadísticas del rate limiter")
    
    stats = scraping_rate_limiter.get_stats()
    
    logger.info("📈 Estadísticas del Rate Limiter:")
    logger.info(f"  • Total de peticiones: {stats['total_requests']}")
    logger.info(f"  • Peticiones exitosas: {stats['successful_requests']}")
    logger.info(f"  • Peticiones fallidas: {stats['failed_requests']}")
    logger.info(f"  • Tasa de éxito: {stats['success_rate']:.1f}%")
    logger.info(f"  • Peticiones por minuto: {stats['requests_per_minute']:.1f}")
    logger.info(f"  • Tiempo promedio de espera: {stats['average_wait_time']:.2f}s")
    logger.info(f"  • Tiempo transcurrido: {stats['elapsed_time']:.1f}s")


async def main():
    """
    Función principal de demostración.
    """
    logger.info("🎯 Iniciando demostración completa del sistema")
    
    try:
        # Demostrar rate limiting
        await demonstrate_rate_limiting()
        
        # Demostrar manejo de excepciones
        await demonstrate_exception_handling()
        
        # Mostrar estadísticas
        await demonstrate_statistics()
        
        logger.info("🎉 Demostración completada exitosamente")
        
    except Exception as e:
        logger.error(f"💥 Error en la demostración: {e}")


if __name__ == "__main__":
    # Configurar logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
        level="INFO"
    )
    
    # Ejecutar demostración
    asyncio.run(main())
