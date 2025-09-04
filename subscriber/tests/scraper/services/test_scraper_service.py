"""
Tests unitarios para ScraperService siguiendo patrón AAA y TDD.
"""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, mock_open
from datetime import datetime

from scraper.services.scraper_service import ScraperService
from models import ScrapingResult


class TestScraperServiceInitialization:
    """Tests para inicialización del ScraperService."""
    
    def test_initialization_success(self):
        """
        Test: ScraperService debe inicializarse correctamente con configuración válida
        """
        # Arrange - Configuración válida
        mock_config = {
            "base_url": "https://listado.mercadolibre.com.uy",
            "output_dir": Path("/tmp/test_output")
        }
        
        with patch('scraper.services.scraper_service.SCRAPER_CONFIG', mock_config), \
             patch('scraper.services.scraper_service.SimpleScraper') as mock_scraper:
            
            # Act - Crear instancia de ScraperService
            service = ScraperService()
            
            # Assert - Verificar inicialización
            assert service.base_url == mock_config["base_url"]
            assert service.output_dir == mock_config["output_dir"]
            assert service.scraper_class == mock_scraper
            assert service.scraper_available is True


    def test_output_directory_creation(self):
        """
        Test: Directorio de salida debe crearse si no existe
        """
        # Arrange - Mock de directorio inexistente
        mock_config = {
            "base_url": "https://listado.mercadolibre.com.uy",
            "output_dir": Path("/tmp/new_output")
        }
        
        with patch('scraper.services.scraper_service.SCRAPER_CONFIG', mock_config), \
             patch('scraper.services.scraper_service.SimpleScraper'), \
             patch.object(Path, 'mkdir') as mock_mkdir:
            
            # Act - Crear instancia
            service = ScraperService()
            
            # Assert - Verificar creación de directorio
            mock_mkdir.assert_called_once_with(exist_ok=True)


class TestScraperServiceAvailability:
    """Tests para verificación de disponibilidad."""
    
    def test_is_available_when_scraper_loaded(self):
        """
        Test: is_available debe retornar True cuando scraper está cargado
        """
        # Arrange - Scraper disponible
        mock_config = {
            "base_url": "https://listado.mercadolibre.com.uy",
            "output_dir": Path("/tmp/test_output")
        }
        
        with patch('scraper.services.scraper_service.SCRAPER_CONFIG', mock_config), \
             patch('scraper.services.scraper_service.SimpleScraper'):
            
            service = ScraperService()
            
            # Act - Verificar disponibilidad
            result = service.is_available()
            
            # Assert - Verificar que está disponible
            assert result is True


class TestScraperServiceScraping:
    """Tests para funcionalidad de scraping."""
    
    @pytest.fixture(autouse=True)
    def setup_service(self):
        """Setup del service para cada test."""
        mock_config = {
            "base_url": "https://listado.mercadolibre.com.uy",
            "output_dir": Path("/tmp/test_output")
        }
        
        with patch('scraper.services.scraper_service.SCRAPER_CONFIG', mock_config), \
             patch('scraper.services.scraper_service.SimpleScraper') as mock_scraper_class:
            
            self.mock_scraper_class = mock_scraper_class
            self.service = ScraperService()
            yield

    @pytest.mark.asyncio
    async def test_scrape_products_success(self, sample_product_list):
        """
        Test: Scraping exitoso debe retornar resultado con productos
        """
        # Arrange - Configurar scraper exitoso
        mock_scraper = AsyncMock()
        mock_scraper.scrape_listing_with_details.return_value = sample_product_list
        self.mock_scraper_class.return_value = mock_scraper
        
        url = "https://listado.mercadolibre.com.uy/notebooks"
        max_products = 10
        task_id = "test-task-123"
        
        with patch.object(self.service, '_generate_output_file') as mock_generate:
            mock_generate.return_value = Path("/tmp/output.json")
            
            # Act - Ejecutar scraping
            result = await self.service.scrape_products(url, max_products, task_id)
            
            # Assert - Verificar resultado exitoso
            assert isinstance(result, ScrapingResult)
            assert result.products_count == len(sample_product_list)
            assert result.success_rate == 100.0
            assert result.duration > 0
            assert result.output_file == "/tmp/output.json"
            assert len(result.errors) == 0
            
            # Verificar llamadas
            self.mock_scraper_class.assert_called_once_with(task_id=task_id)
            mock_scraper.scrape_listing_with_details.assert_called_once_with(url, max_products)

    @pytest.mark.asyncio
    async def test_scrape_products_no_products_found(self):
        """
        Test: Scraping sin productos debe retornar resultado con éxito 0%
        """
        # Arrange - Configurar scraper sin productos
        mock_scraper = AsyncMock()
        mock_scraper.scrape_listing_with_details.return_value = []
        self.mock_scraper_class.return_value = mock_scraper
        
        url = "https://listado.mercadolibre.com.uy/empty"
        max_products = 10
        
        with patch.object(self.service, '_generate_output_file') as mock_generate:
            mock_generate.return_value = Path("/tmp/empty.json")
            
            # Act - Ejecutar scraping sin productos
            result = await self.service.scrape_products(url, max_products)
            
            # Assert - Verificar resultado sin productos
            assert result.products_count == 0
            assert result.success_rate == 0.0
            assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_scrape_products_scraper_unavailable(self):
        """
        Test: Scraper no disponible debe lanzar RuntimeError
        """
        # Arrange - Marcar scraper como no disponible
        self.service.scraper_available = False
        
        # Act & Assert - Verificar error
        with pytest.raises(RuntimeError, match="Scraper no disponible"):
            await self.service.scrape_products("http://test.com", 10)

    @pytest.mark.asyncio
    async def test_scrape_products_scraper_exception(self):
        """
        Test: Excepción en scraper debe retornar resultado con error
        """
        # Arrange - Configurar excepción en scraper
        mock_scraper = AsyncMock()
        mock_scraper.scrape_listing_with_details.side_effect = Exception("Scraping failed")
        self.mock_scraper_class.return_value = mock_scraper
        
        url = "https://listado.mercadolibre.com.uy/error"
        max_products = 10
        
        # Act - Ejecutar scraping con error
        result = await self.service.scrape_products(url, max_products)
        
        # Assert - Verificar resultado con error
        assert result.products_count == 0
        assert result.success_rate == 0.0
        assert result.output_file == ""
        assert len(result.errors) == 1
        assert "Scraping failed" in result.errors[0]

    @pytest.mark.asyncio
    async def test_scrape_products_with_default_task_id(self, sample_product_list):
        """
        Test: Scraping sin task_id debe usar valor por defecto
        """
        # Arrange - Sin task_id específico
        mock_scraper = AsyncMock()
        mock_scraper.scrape_listing_with_details.return_value = sample_product_list
        self.mock_scraper_class.return_value = mock_scraper
        
        with patch.object(self.service, '_generate_output_file') as mock_generate:
            mock_generate.return_value = Path("/tmp/output.json")
            
            # Act - Ejecutar scraping sin task_id
            await self.service.scrape_products("http://test.com", 10)
            
            # Assert - Verificar task_id por defecto
            self.mock_scraper_class.assert_called_once_with(task_id="default")

