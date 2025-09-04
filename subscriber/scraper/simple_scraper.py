#!/usr/bin/env python3
"""
Scraper simplificado para Mercado Libre Uruguay.
Extrae el listado base y luego navega a cada URL para obtener características adicionales.
"""
from ast import Str
import re
import asyncio
import sys
from pathlib import Path
from typing import List, Optional, Dict
from decimal import Decimal

# Agregar el directorio del proyecto al path
sys.path.append(str(Path(__file__).parent))

from .browser import BrowserManager
from .models.models import Product
from utils import normalize_price,  extract_rating, extract_review_count, clean_text
from .utils.rate_limiter import scraping_rate_limiter, extract_domain_from_url
from .utils.exception_handler import (
    handle_scraping_exceptions, 
    ExceptionContext, 
    NavigationException,
    ExtractionException
)

from loguru import logger
from dotenv import load_dotenv
import os

# Cargar el archivo .env
load_dotenv()



class SimpleScraper:
    """Scraper simplificado para extraer listado de productos y características adicionales."""
    
    def __init__(self, task_id: str):
        """Inicializar el scraper."""
        self.task_id = task_id
        self.exception_context = ExceptionContext(task_id)
        
        # Selectores CSS para el listado
        self.selectors = {
            "product_card": "div.andes-card",
            "product_title": "h3.poly-component__title-wrapper",
            "product_price": "div.ui-pdp-price__second-line span.andes-money-amount__fraction",
            "product_original_price": "s.andes-money-amount span.andes-money-amount__fraction",
            "product_discount": "span.andes-money-amount__discount",
            "product_seller": "span.poly-component__seller",
            "product_rating": "span.ui-pdp-review__rating",
            "product_reviews": "span.total-opinion",
            "product_image": "img.poly-component__picture",
            "product_link": "a.poly-component__title",
            "product_stock": "span.ui-pdp-buybox__quantity__available",
        }
        
        # Selectores CSS para páginas de detalle
        self.detail_selectors = {
            "features": "tr.andes-table__row.ui-vpp-striped-specs__row",
            "seller_location": "span.ui-pdp-seller__location",
            "warranty": "span.ui-pdp-warranty",
            "shipping_info": "p.ui-pdp-color--BLACK",
            "stock_detail": "span.ui-pdp-buybox__quantity__available",
            "description": "p.ui-pdp-description__content",
            "additional_images": "img.ui-pdp-image ui-pdp-gallery__figure__image",
            "shipping_method": "div.ui-pdp-color--BLACK.ui-pdp-family--REGULAR.ui-pdp-media__title",
        }
        self.detail_login = {
            "login_button": "a[data-link-id='login']",
            "login_text": "h1.andes-typography",
            "email_input": "input[type='email']",
            "password_input": "input[type='password']",
            "login_continue": "button[type='submit']",
            "button_change_account": "button.andes-typography",
            "user_name": "span.nav-header-username",
        }
    
    async def scrape_listing_with_details(self, url: str, max_products: int = 20, category: str = None, page: int = None) -> List[Product]:
        """
        Extraer listado de productos y luego características adicionales de cada uno.
        
        Args:
            url: URL de la página de listado
            max_products: Número máximo de productos a extraer
            
        Returns:
            Lista de productos con características completas
        """
        products = []
        
        async with BrowserManager(headless=True) as browser:
            try:
                # Navegar a la URL del listado con rate limiting
                domain = extract_domain_from_url(url)
                navigation_success = await scraping_rate_limiter.execute_request(
                    browser.navigate_to, 
                    domain=domain,
                    url=url
                )
                
                if not navigation_success:
                    logger.error(f"Task {self.task_id} - No se pudo navegar a: {url}")
                    return products
                
                # Esperar a que carguen los productos
                await browser.wait_for_element(self.selectors["product_card"], timeout=10000)
                
                product_elements = await browser.get_elements(self.selectors["product_card"])
                logger.info(f"Task {self.task_id} - Encontrados {len(product_elements)} productos en el listado")
                
                # Extraer datos básicos de cada producto
                for i, element in enumerate(product_elements[:max_products]):
                    try:
                        product = await self._extract_product_basic(element)
                        if product:
                            products.append(product)
                            logger.info(f"Task {self.task_id} - Producto {i+1} extraído del listado: {product.title[:50]}...")
                        
                        # Delay entre extracciones
                        if i < len(product_elements) - 1:
                            await asyncio.sleep(1.0)
                            
                    except Exception as e:
                        logger.error(f"Task {self.task_id} - Error al extraer producto {i+1} del listado: {e}")
                        continue
                
                logger.info(f"Task {self.task_id} - Listado base extraído: {len(products)} productos")
                
                # Ahora navegar a cada producto para extraer características adicionales
                logger.info(f"Task {self.task_id} - Iniciando extracción de características adicionales...")

                # Do login before extracting details
                await self._login(browser=browser)

                await asyncio.sleep(1)
                
                for i, product in enumerate(products):
                    try:
                        if product.url:
                            logger.info(f"Task {self.task_id} - Extrayendo detalles de producto {i+1}/{len(products)}: {product.title[:50]}...")
                            
                            # Extraer características adicionales con rate limiting
                            product_domain = extract_domain_from_url(product.url)
                            await scraping_rate_limiter.execute_request(
                                self._extract_product_details,
                                domain=product_domain,
                                product=product,
                                browser=browser
                            )
                            
                            # add category and page to the product
                            product.category = category
                            product.page = page
                        else:
                            logger.warning(f"Task {self.task_id} - Producto {i+1} sin URL, saltando...")
                            
                    except Exception as e:
                        logger.error(f"Task {self.task_id} - Error al extraer detalles del producto {i+1}: {e}")
                        continue
                
                logger.info(f"Task {self.task_id} - Extracción completa finalizada: {len(products)} productos con características completas")
                
            except Exception as e:
                logger.error(f"Task {self.task_id} - Error en el scraping: {e}")
        
        return products
    
    async def _login(self, browser):
        # search the login button and click it
        logger.info(f"Task {self.task_id} - Iniciando sesión...")
        if await self._validate_login_success(browser):
            logger.info(f"Task {self.task_id} - We are already logged in")
            return True
        
        logger.info(f"Task {self.task_id} - Identificando el botón de login...")
        login_button = await browser.get_elements(self.detail_login["login_button"])
        if login_button:
            logger.info(f"Task {self.task_id} - Botón de login encontrado: {login_button}")
            
            # Usar directamente el elemento encontrado en lugar del selector
            try:
                await login_button[0].click()
                logger.info(f"Task {self.task_id} - Click en botón de login exitoso")
                await asyncio.sleep(2)  # Esperar a que se procese el click
            except Exception as e:
                logger.error(f"Task {self.task_id} - Error al hacer click en el botón de login: {e}")
                return RuntimeError(f"Task {self.task_id} - Error al hacer click en el botón de login: {e}")

        # validate if we are in the login page
        login_text = await browser.get_element_text(self.detail_login["login_text"])
        keywords = ["Ingresa", "e-mail", "telefono", "iniciar sesión"]
        if any(keyword in login_text for keyword in keywords):
            logger.debug(f"Task {self.task_id} - We are in the login page") 
            # set the email input
            email_input = await browser.get_elements(self.detail_login["email_input"])
            if email_input:
                email, password = await self._extract_credentials()
                await email_input[0].type(email)
                await asyncio.sleep(1)
                # take_screenshot of the page
                # await browser.take_screenshot("login_page.png")
                await browser.click_element(self.detail_login["login_continue"])
                await asyncio.sleep(1)
                # validate if we are in the second step of the login

                if not await self._validate_login_second_step(browser):
                    logger.error(f"Task {self.task_id} - We are not in the second step of the login")
                    return RuntimeError(f"Task {self.task_id} - We are not in the second step of the login")
                await asyncio.sleep(1)
                await browser.wait_for_element(self.detail_login["password_input"], timeout=10000)
                # set the password input
                password_input = await browser.get_elements(self.detail_login["password_input"])
                logger.debug(f"Task {self.task_id} - looking for password input: {password_input}")
                if password_input:
                    await password_input[0].type(password)
                    # await browser.take_screenshot("password_input.png")
                    await asyncio.sleep(1)
                    await browser.click_element(self.detail_login["login_continue"])
                    await asyncio.sleep(1)
                    # validate if we are in the login success
                    if not await self._validate_login_success(browser):
                        logger.error(f"Task {self.task_id} - We are not in the login success")
                        return RuntimeError(f"Task {self.task_id} - We are not in the login success")
                    #await browser.take_screenshot("login_success.png")
                    logger.info(f"Task {self.task_id} - Login success")
                    return True
        logger.error(f"Task {self.task_id} - No se encontró el botón de login")
        return RuntimeError(f"Task {self.task_id} - We are not in the login page")



    async def _validate_login_success(self, browser):
        # Validate if the page has the user name
        logger.debug(f"Task {self.task_id} - Validando el login success")
        user_name = await browser.get_element_text(self.detail_login["user_name"])
        logger.debug(f"Task {self.task_id} - User name found: {user_name}")
        await asyncio.sleep(10)
        if user_name == "Test":
            return True
        return False
        
    async def _validate_login_second_step(self, browser):
        # Validate if the text "Ingresa tu contraseña de Mercado Libre", 
        logger.debug(f"Task {self.task_id} - Validating login step 2")
        await asyncio.sleep(1)
        await browser.wait_for_element(self.detail_login["login_text"], timeout=10000)
        login_text = await browser.get_element_text(self.detail_login["login_text"])
        keywords = ["Ingresa tu contraseña de Mercado Libre", "Ingresa tu e-mail o teléfono para iniciar sesión"]
        if any(keyword in login_text for keyword in keywords):
            logger.debug(f"Task {self.task_id} - We are in the second step of the login")
            return True
        
        # Validate if exist the button "Cambiar cuenta" and validate if the text is "Cambiar cuenta"
        button_change_account = await browser.get_elements(self.detail_login["button_change_account"])
        if button_change_account:
            # validate the text of the button
            text_button_change_account = await button_change_account[0].text_content()
            if "Cambiar cuenta" in text_button_change_account:
                logger.debug(f"Task {self.task_id} - We are in the second step of the login")
                return True
            
        logger.error(f"Task {self.task_id} - We are not in the second step of the login")
        
        return False


    async def _extract_product_basic(self, element) -> Optional[Product]:
        """
        Extraer datos básicos de un producto del listado.
        
        Args:
            element: Elemento DOM del producto
            
        Returns:
            Producto con datos básicos o None si hay error
        """
        try:
            # Extraer datos básicos
            title = await self._extract_title(element)
            if not title:
                return None
            
            url = await self._extract_url(element)
            seller = await self._extract_seller(element)
            
            # Setear producto base
            product = Product(
                title=title,
                url=url,
                seller=seller,
            )
            
            return product
            
        except Exception as e:
            logger.error(f"Task {self.task_id} - Error al extraer producto básico: {e}")
            return None
    
    @handle_scraping_exceptions(max_retries=2, default_return=None)
    async def _extract_product_details(self, product: Product, browser: BrowserManager):
        """
        Extraer características adicionales navegando a la página del producto.
        
        Args:
            product: Producto al que extraer detalles
            browser: Gestor del navegador
        """
        try:
            if not product.url:
                logger.warning(f"Task {self.task_id} - Producto sin URL, saltando extracción de detalles")
                return
            
            # Crear nueva página para el detalle
            detail_page = await browser.context.new_page()
            
            try:
                # Navegar al detalle del producto
                logger.debug(f"Task {self.task_id} - Navegando a: {product.url}")
                response = await detail_page.goto(product.url, wait_until='domcontentloaded', timeout=30000)
                
                if not response or not response.ok:
                    logger.warning(f"Task {self.task_id} - No se pudo cargar la página de detalle: {product.url} (Status: {response.status if response else 'No response'})")
                    return
                
                # Esperar a que cargue la página
                await detail_page.wait_for_load_state("domcontentloaded", timeout=10000)
                

                # Extraer datos adicionales del detalle
                product.original_price = await self._extract_original_price(detail_page)

                product.current_price = await self._extract_current_price(detail_page)

                product.discount_percentage = await self._extract_discount(detail_page)

                product.rating = await self._extract_rating(detail_page)


                # Extraer características principales
                features = await self._extract_detailed_features(detail_page)
                if features:
                    product.features = features
                    logger.debug(f"Task {self.task_id} -  Extracted {len(features)} features")
                
                
                # Extraer información de stock detallada
                stock_quantity = await self._extract_stock_info(detail_page)
                if stock_quantity:
                    product.stock_quantity = stock_quantity
                    logger.debug(f"Task {self.task_id} - Stock: {stock_quantity}")
                
                # Extraer marca
                brand = await self._extract_brand(product)
                if brand:
                    product.brand = brand
                    logger.debug(f"Task {self.task_id} - Brand: {brand}")
                
                # Extraer imágenes adicionales
                additional_images = await self._extract_additional_images(detail_page)
                if additional_images:
                    product.images.extend(additional_images)
                    logger.debug(f"Task {self.task_id} - Extracted {len(additional_images)} additional images")
                
                # Extraer descripción
                description = await self._extract_description(detail_page)
                if description:
                    product.description = description
                    logger.debug(f"Task {self.task_id} - Description extracted")

                review_count = await self._extract_review_count(detail_page)
                if review_count:
                    product.review_count = review_count
                    logger.debug(f"Task {self.task_id} - Extracted {review_count} reviews")
                
                stock_quantity = await self._extract_stock_info(detail_page)
                if stock_quantity:
                    product.stock_quantity = stock_quantity
                    logger.debug(f"Task {self.task_id} - Extracted {stock_quantity} stock")

                shipping_method = await self._extract_shipping(detail_page)
                if shipping_method:
                    product.shipping_method = shipping_method
                    logger.debug(f"Task {self.task_id} - Extracted {shipping_method} shipping method")
            
                logger.info(f"Task {self.task_id} - Details extracted for: {product.title[:50]}...")
                
            finally:
                await detail_page.close()
                
        except Exception as e:
            logger.warning(f"Task {self.task_id} - Error al extraer detalles del producto: {e}")
    
    async def _extract_detailed_features(self, page) -> Dict[str, str]:
        """Extraer características detalladas del producto."""
        try:
            features = {}
            feature_rows = await page.query_selector_all(self.detail_selectors["features"])
            
            if not feature_rows:
                logger.debug(f"Task {self.task_id} - No se encontraron filas de características")
                return features
            
            for row in feature_rows[:15]:  # Limitar a 15 características
                try:
                    # Extraer el nombre de la característica (th)
                    feature_name_elem = await row.query_selector("th.andes-table__header")
                    if not feature_name_elem:
                        continue
                    
                    feature_name = await feature_name_elem.text_content()
                    if not feature_name or len(feature_name.strip()) < 2:
                        continue
                    
                    # Extraer el valor de la característica (td)
                    feature_value_elem = await row.query_selector("td.andes-table__column")
                    if not feature_value_elem:
                        continue
                    
                    feature_value = await feature_value_elem.text_content()
                    if not feature_value or len(feature_value.strip()) < 2:
                        continue
                    
                    features[clean_text(feature_name)] = clean_text(feature_value)
                    
                except Exception as e:  
                    logger.debug(f"Task {self.task_id} - Error al procesar fila de característica: {e}")
                    continue
            
            return features
            
        except Exception as e:
            logger.warning(f"Task {self.task_id} - Error al extraer características detalladas: {e}")
            return {}
    
    async def _extract_seller_location(self, page) -> str:
        """Extraer ubicación del vendedor."""
        try:
            location_elem = await page.query_selector(self.detail_selectors["seller_location"])
            if location_elem:
                text = await location_elem.text_content()
                if text:
                    return clean_text(text)
            return ""
            
        except Exception as e:
            logger.debug(f"Task {self.task_id} - Error al extraer ubicación del vendedor: {e}")
            return ""
    
    async def _extract_stock_info(self, page) -> str:
        """Extraer información de stock del producto."""
        try:
            
            stock_elem = await page.query_selector(self.detail_selectors["stock_detail"])
            if stock_elem:
                text = await stock_elem.text_content()
                # extract the number from the text
                if text:
                    quantity_stock = text.replace("(", "").replace(")", "")
                    return quantity_stock
                return None
            
        except Exception as e:
            logger.debug(f"Task {self.task_id} - Error al extraer información de stock: {e}")
            return None
    
    async def _extract_brand(self, product: Product) -> str:
        """Extraer marca del producto."""
        try:
            logger.debug(product.features)
            # extract the brand from detailed features
            brand = product.features.get("Marca")
            if brand:
                return brand
            return ""
            
        except Exception as e:
            logger.debug(f"Task {self.task_id} - Error al extraer marca: {e}")
            return ""
    
    
    async def _extract_additional_images(self, page) -> List[str]:
        """Extraer imágenes adicionales del producto."""
        try:
            img_elements = await page.query_selector_all(self.detail_selectors["additional_images"])
            images = []
            
            for img in img_elements:
                src = await img.get_attribute("src")
                if src:
                    if src.startswith("//"):
                        src = f"https:{src}"
                    elif src.startswith("/"):
                        src = f"https://www.mercadolibre.com.uy{src}"
                    images.append(src)
            
            return images
            
        except Exception as e:
            logger.debug(f"Task {self.task_id} - Error al extraer imágenes adicionales: {e}")
            return []
    
    async def _extract_description(self, page) -> str:
        """Extraer descripción del producto."""
        try:
            desc_elem = await page.query_selector(self.detail_selectors["description"])
            if desc_elem:
                text = await desc_elem.text_content()
                if text:
                    return clean_text(text)
            return ""
            
        except Exception as e:
            logger.debug(f"Task {self.task_id} - Error al extraer descripción: {e}")
            return ""
    
    # ... (resto de métodos de extracción básica se mantienen igual)
    async def _extract_title(self, element) -> str:
        """Extraer título del producto."""
        title_elem = await element.query_selector(self.selectors["product_title"])
        if title_elem:
            text = await title_elem.text_content()
            return clean_text(text) if text else ""
        return ""
    
    async def _extract_url(self, element) -> str:
        """Extraer URL del producto."""
        link_elem = await element.query_selector(self.selectors["product_link"])
        if link_elem:
            url = await link_elem.get_attribute("href")
            if url and not url.startswith("http"):
                url = f"https://www.mercadolibre.com.uy{url}"
            return url or ""
        return ""
    
    async def _extract_seller(self, element) -> str:
        """Extraer información del vendedor."""
        seller_elem = await element.query_selector(self.selectors["product_seller"])
        if seller_elem:
            text = await seller_elem.text_content()
            if text:
                # Limpiar texto del vendedor
                text = text.replace("por", "").replace("vendido por", "").replace("Por ", "").strip()
                return clean_text(text)
        return "Vendedor no especificado"
    
    async def _extract_current_price(self, element) -> Optional[Decimal]:
        """Extraer precio actual del producto."""
        price_elem = await element.query_selector(self.selectors["product_price"])
        if price_elem:
            text = await price_elem.text_content()
            return normalize_price(text) if text else None
        return None
    
    async def _extract_original_price(self, element) -> Optional[Decimal]:
        """Extraer precio original del producto."""
        price_elem = await element.query_selector(self.selectors["product_original_price"])
        if price_elem:
            text = await price_elem.text_content()
            return normalize_price(text) if text else None
        return None
    
    async def _extract_discount(self, element) -> Optional[Decimal]:
        """Extraer porcentaje de descuento."""
        discount_elem = await element.query_selector(self.selectors["product_discount"])
        if discount_elem:
            text = await discount_elem.text_content()
            return text
        return None
    
    async def _extract_rating(self, element) -> Optional[float]:
        """Extraer rating del producto."""
        rating_elem = await element.query_selector(self.selectors["product_rating"])
        if rating_elem:
            text = await rating_elem.text_content()
            return extract_rating(text) if text else None
        return None
    
    async def _extract_review_count(self, element) -> Optional[int]:
        """Extraer número de reviews."""
        review_elem = await element.query_selector(self.selectors["product_reviews"])
        print(review_elem)
        if review_elem:
            text = await review_elem.text_content()
            return extract_review_count(text) if text else None
        return None
    
    async def _extract_images(self, element) -> List[str]:
        """Extraer URLs de imágenes del producto."""
        img_elements = await element.query_selector_all(self.selectors["product_image"])
        images = []
        
        for img in img_elements:
            src = await img.get_attribute("src")
            if src:
                # Convertir URLs relativas a absolutas
                if src.startswith("//"):
                    src = f"https:{src}"
                elif src.startswith("/"):
                    src = f"https://www.mercadolibre.com.uy{src}"
                images.append(src)
        
        return images
    
    async def _extract_shipping(self, element) -> str:
        """Extraer método de envío."""
        shipping_elem = await element.query_selector(self.detail_selectors["shipping_method"])
        if shipping_elem:
            text = await shipping_elem.text_content()
            return clean_text(text) if text else ""
        return ""
    
    async def _extract_credentials(self) -> tuple[str, str]:
        """Extrae las variables de entorno para el login, se encuenta en el archivo .env"""
        user_id = os.getenv("TEST_USER")
        password = os.getenv("TEST_PASSWORD")
        if not user_id:
            raise ValueError(f"Task {self.task_id} - TEST_USER no está definida en el archivo .env")
        if not password:
            raise ValueError(f"Task {self.task_id} - TEST_PASSWORD no está definida en el archivo .env")
        return user_id, password
    
# Función main solo para uso directo del script
def run_main(url: str, max_products: int = 50, task_id: str = None, category: str = None, page: int = None):
    """Función wrapper para ejecutar main de forma segura."""
    async def main():
        """Función principal."""

        # Crear scraper y extraer productos con detalles
        scraper = SimpleScraper(task_id=task_id)
        products = await scraper.scrape_listing_with_details(url, max_products=max_products, category=category, page=page)
        
        # Mostrar resultados
        print(f"Task {task_id} - Total de productos extraídos: {len(products)}")
        print(f"Task {task_id} - Scraping completo finalizado!")

        return products

    # Solo ejecutar si se llama directamente, no al importar
    return asyncio.run(main())
