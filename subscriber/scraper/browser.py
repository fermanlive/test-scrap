"""
Configuración del navegador con Playwright y Camoufox.
"""

import os
import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from loguru import logger

class BrowserManager:
    """Gestor del navegador con configuración anti-detección."""
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Inicializar el gestor del navegador.
        
        Args:
            headless: Si el navegador debe ejecutarse en modo headless
            timeout: Timeout en milisegundos para las operaciones
        """
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.stop()
    
    async def start(self):
        """Iniciar el navegador y crear contexto."""
        try:
            self.playwright = await async_playwright().start()
            
            # Configuración FAST simplificada
            logger.info("Iniciando navegador con configuración FAST...")
                
            # Configuración básica FAST como fallback
            browser_args = [
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-extensions",
                "--disable-plugins",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-default-apps",
                "--disable-popup-blocking",
                "--disable-notifications",
            ]
            
            # Iniciar navegador Chromium
            self.browser = await self.playwright.chromium.launch(
                headless=True,  # FAST siempre es headless
                args=browser_args
            )
            
            # Crear contexto con configuración anti-detección básica
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='es-UY',
                timezone_id='America/Montevideo',
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'es-UY,es;q=0.8,en-US;q=0.5,en;q=0.3',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0',
                }
            )
            
            # Crear nueva página
            self.page = await self.context.new_page()
            
            # Configurar timeout
            self.page.set_default_timeout(self.timeout)
            
            logger.info("Navegador iniciado exitosamente")
            
        except Exception as e:
            logger.error(f"Error al iniciar el navegador: {e}")
            await self.stop()
            raise
    
    async def navigate_to(self, url: str, wait_for_load: bool = True) -> bool:
        """
        Navegar a una URL específica.
        
        Args:
            url: URL a la que navegar
            wait_for_load: Si esperar a que la página cargue completamente
            
        Returns:
            True si la navegación fue exitosa
        """
        try:
            logger.info(f"Navegando a: {url}")
            
            response = await self.page.goto(url, wait_until='networkidle' if wait_for_load else 'domcontentloaded')
            
            if response and response.ok:
                logger.info(f"Navegación exitosa a: {url}")
                return True
            else:
                logger.error(f"Error en la respuesta HTTP: {response.status if response else 'No response'}")
                return False
                
        except Exception as e:
            logger.error(f"Error al navegar a {url}: {e}")
            return False
    
    async def wait_for_element(self, selector: str, timeout: Optional[int] = None) -> bool:
        """
        Esperar a que un elemento aparezca en la página.
        
        Args:
            selector: Selector CSS del elemento
            timeout: Timeout personalizado en milisegundos
            
        Returns:
            True si el elemento apareció
        """
        try:
            timeout = timeout or self.timeout
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            logger.warning(f"Elemento no encontrado: {selector} - Error: {e}")
            return False
    
    async def get_elements(self, selector: str):
        """
        Obtener elementos por selector CSS.
        
        Args:
            selector: Selector CSS
            
        Returns:
            Lista de elementos encontrados
        """
        try:
            return await self.page.query_selector_all(selector)
        except Exception as e:
            logger.error(f"Error al obtener elementos con selector '{selector}': {e}")
            return []
    
    async def get_element_text(self, selector: str, default: str = "") -> str:
        """
        Obtener texto de un elemento.
        
        Args:
            selector: Selector CSS del elemento
            default: Valor por defecto si no se encuentra
            
        Returns:
            Texto del elemento o valor por defecto
        """
        try:
            element = await self.page.query_selector(selector)
            if element:
                return await element.text_content() or default
            return default
        except Exception as e:
            logger.debug(f"Error al obtener texto del elemento '{selector}': {e}")
            return default
    
    async def get_element_attribute(self, selector: str, attribute: str, default: str = "") -> str:
        """
        Obtener atributo de un elemento.
        
        Args:
            selector: Selector CSS del elemento
            attribute: Nombre del atributo
            default: Valor por defecto si no se encuentra
            
        Returns:
            Valor del atributo o valor por defecto
        """
        try:
            element = await self.page.query_selector(selector)
            if element:
                return await element.get_attribute(attribute) or default
            return default
        except Exception as e:
            logger.debug(f"Error al obtener atributo '{attribute}' del elemento '{selector}': {e}")
            return default
    
    async def click_element(self, selector: str) -> bool:
        """
        Hacer clic en un elemento.
        
        Args:
            selector: Selector CSS del elemento
            
        Returns:
            True si el clic fue exitoso
        """
        try:
            await self.page.click(selector)
            return True
        except Exception as e:
            logger.error(f"Error al hacer clic en '{selector}': {e}")
            return False
    
    async def scroll_to_bottom(self, delay: float = 1.0):
        """
        Hacer scroll hasta el final de la página.
        
        Args:
            delay: Delay entre scrolls en segundos
        """
        try:
            await self.page.evaluate("""
                window.scrollTo(0, document.body.scrollHeight);
            """)
            await asyncio.sleep(delay)
        except Exception as e:
            logger.warning(f"Error al hacer scroll: {e}")
    
    async def take_screenshot(self, path: str) -> bool:
        """
        Tomar una captura de pantalla.
        
        Args:
            path: Ruta donde guardar la captura
            
        Returns:
            True si la captura fue exitosa
        """
        try:
            await self.page.screenshot(path=path)
            logger.info(f"Captura de pantalla guardada en: {path}")
            return True
        except Exception as e:
            logger.error(f"Error al tomar captura de pantalla: {e}")
            return False
    
    async def stop(self):
        """Detener el navegador y limpiar recursos."""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            
            if self.context:
                await self.context.close()
                self.context = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            
            logger.info("Navegador detenido exitosamente")
            
        except Exception as e:
            logger.error(f"Error al detener el navegador: {e}")
    
    async def is_page_loaded(self) -> bool:
        """
        Verificar si la página está completamente cargada.
        
        Returns:
            True si la página está cargada
        """
        try:
            return await self.page.evaluate("document.readyState") == "complete"
        except Exception:
            return False
    
    async def wait_for_page_load(self, timeout: Optional[int] = None):
        """
        Esperar a que la página se cargue completamente.
        
        Args:
            timeout: Timeout personalizado en milisegundos
        """
        try:
            timeout = timeout or self.timeout
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception as e:
            logger.warning(f"Timeout esperando carga de página: {e}")

    async def take_screenshot(self, path: str) -> bool:
        """
        Tomar una captura de pantalla.
        
        Args:
            path: Ruta donde guardar la captura
            
        Returns:
            True si la captura fue exitosa
        """
        try:
            await self.page.screenshot(path=path)
            logger.info(f"Captura de pantalla guardada en: {path}")
            return True
        except Exception as e:
            logger.error(f"Error al tomar captura de pantalla: {e}")
            return False