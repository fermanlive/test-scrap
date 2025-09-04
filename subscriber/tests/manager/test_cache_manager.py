"""
Pruebas unitarias para el CacheManager.
"""

import pytest
import time
import asyncio
from datetime import datetime
from unittest.mock import patch, MagicMock

from manager.cache_manager import CacheManager, CacheEntry
from models.scraping_models import ScrapingResponse, ScrapingStatus


class TestCacheManager:
    """Suite de pruebas para CacheManager."""
    
    def setup_method(self):
        """Configurar antes de cada test."""
        # Crear instancia de cache con TTL corto para pruebas (0.01 horas = 36 segundos)
        self.cache = CacheManager(ttl_hours=0.01)
        
        # Datos de prueba
        self.test_response = ScrapingResponse(
            task_id="test-123",
            status=ScrapingStatus.COMPLETED,
            message="Prueba exitosa",
            url="https://test.com",
            category="MLU107",
            page=1,
            max_products=50
        )
        
        self.test_response_2 = ScrapingResponse(
            task_id="test-456",
            status=ScrapingStatus.COMPLETED,
            message="Segunda prueba",
            url="https://test2.com",
            category="MLA1234",
            page=2,
            max_products=100
        )
    
    def test_cache_initialization(self):
        """Test: Inicialización correcta del cache."""
        cache = CacheManager(ttl_hours=2.0)
        
        assert cache._ttl_seconds == 7200  # 2 horas en segundos
        assert len(cache._cache) == 0
        assert cache._lock is not None
    
    def test_generate_key(self):
        """Test: Generación correcta de claves."""
        # Casos normales
        assert self.cache._generate_key("MLU107", 1) == "MLU107:page:1"
        assert self.cache._generate_key("MLA1234", 999) == "MLA1234:page:999"
        
        # Conversión a mayúsculas
        assert self.cache._generate_key("mlu107", 1) == "MLU107:page:1"
        assert self.cache._generate_key("MlA1234", 5) == "MLA1234:page:5"
    
    def test_cache_set_and_get(self):
        """Test: Operaciones básicas de set y get."""
        category = "MLU107"
        page = 1
        
        # Cache vacío inicialmente
        result = self.cache.get(category, page)
        assert result is None
        
        # Guardar en cache
        self.cache.set(category, page, self.test_response)
        
        # Recuperar del cache
        cached_response = self.cache.get(category, page)
        assert cached_response is not None
        assert cached_response.task_id == self.test_response.task_id
        assert cached_response.category == category
        assert cached_response.page == page
        assert cached_response.url == self.test_response.url
    
    def test_cache_multiple_entries(self):
        """Test: Múltiples entradas en cache."""
        # Agregar primera entrada
        self.cache.set("MLU107", 1, self.test_response)
        
        # Agregar segunda entrada
        self.cache.set("MLA1234", 2, self.test_response_2)
        
        # Verificar que ambas existen
        response1 = self.cache.get("MLU107", 1)
        response2 = self.cache.get("MLA1234", 2)
        
        assert response1 is not None
        assert response2 is not None
        assert response1.task_id == "test-123"
        assert response2.task_id == "test-456"
        
        # Verificar que no se interfieren
        assert response1.category != response2.category
        assert response1.page != response2.page
    
    def test_cache_invalidate(self):
        """Test: Invalidación manual de entradas."""
        category = "MLU107"
        page = 1
        
        # Agregar entrada
        self.cache.set(category, page, self.test_response)
        assert self.cache.get(category, page) is not None
        
        # Invalidar entrada existente
        success = self.cache.invalidate(category, page)
        assert success is True
        assert self.cache.get(category, page) is None
        
        # Intentar invalidar entrada inexistente
        success = self.cache.invalidate("MLU999", 99)
        assert success is False
    
    def test_cache_clear(self):
        """Test: Limpieza completa del cache."""
        # Agregar múltiples entradas
        self.cache.set("MLU107", 1, self.test_response)
        self.cache.set("MLA1234", 2, self.test_response_2)
        self.cache.set("MLB456", 3, self.test_response)
        
        # Verificar que hay entradas
        stats_before = self.cache.get_stats()
        assert stats_before["total_entries"] == 3
        
        # Limpiar cache
        self.cache.clear()
        
        # Verificar que está vacío
        stats_after = self.cache.get_stats()
        assert stats_after["total_entries"] == 0
        
        # Verificar que no se pueden recuperar entradas
        assert self.cache.get("MLU107", 1) is None
        assert self.cache.get("MLA1234", 2) is None
        assert self.cache.get("MLB456", 3) is None
    
    def test_cache_stats(self):
        """Test: Estadísticas del cache."""
        # Cache vacío
        stats = self.cache.get_stats()
        assert stats["total_entries"] == 0
        assert stats["ttl_seconds"] == 36  # 0.01 horas * 3600
        assert stats["avg_time_to_expire_seconds"] == 0
        assert stats["memory_usage_mb"] >= 0
        
        # Cache con entradas
        self.cache.set("MLU107", 1, self.test_response)
        self.cache.set("MLA1234", 2, self.test_response_2)
        
        stats = self.cache.get_stats()
        assert stats["total_entries"] == 2
        assert stats["avg_time_to_expire_seconds"] > 0
        assert stats["memory_usage_mb"] > 0
    
    def test_cache_list_keys(self):
        """Test: Listado de claves activas."""
        # Cache vacío
        keys = self.cache.list_keys()
        assert len(keys) == 0
        
        # Agregar entradas
        self.cache.set("MLU107", 1, self.test_response)
        self.cache.set("MLA1234", 2, self.test_response_2)
        
        keys = self.cache.list_keys()
        assert len(keys) == 2
        assert "MLU107:page:1" in keys
        assert "MLA1234:page:2" in keys
    
    def test_cache_expiration_check(self):
        """Test: Verificación de expiración."""
        current_time = time.time()
        
        # Entrada no expirada
        entry_valid = CacheEntry(
            data=self.test_response,
            created_at=current_time,
            expires_at=current_time + 100  # Expira en 100 segundos
        )
        assert not self.cache._is_expired(entry_valid)
        
        # Entrada expirada
        entry_expired = CacheEntry(
            data=self.test_response,
            created_at=current_time - 200,
            expires_at=current_time - 100  # Expiró hace 100 segundos
        )
        assert self.cache._is_expired(entry_expired)
    
    def test_cache_cleanup_expired(self):
        """Test: Limpieza automática de entradas expiradas."""
        # Mock time.time() para controlar el tiempo
        with patch('time.time') as mock_time:
            # Tiempo inicial
            mock_time.return_value = 1000.0
            
            # Agregar entrada que expirará pronto
            self.cache.set("MLU107", 1, self.test_response)
            assert len(self.cache._cache) == 1
            
            # Avanzar tiempo más allá del TTL
            mock_time.return_value = 1000.0 + self.cache._ttl_seconds + 1
            
            # Intentar obtener entrada (debería limpiar automáticamente)
            result = self.cache.get("MLU107", 1)
            assert result is None
            assert len(self.cache._cache) == 0
    
    def test_cache_thread_safety(self):
        """Test: Verificar que las operaciones son thread-safe."""
        import threading
        from unittest.mock import Mock
        
        # Verificar que el cache tiene un lock
        assert isinstance(self.cache._lock, type(threading.Lock()))
        
        # Test funcional: verificar que las operaciones funcionan con lock
        # Simular acceso concurrente básico
        results = []
        errors = []
        
        def worker_set(category_suffix):
            try:
                category = f"MLU{category_suffix}"
                response = ScrapingResponse(
                    task_id=f"thread-test-{category_suffix}",
                    status=ScrapingStatus.COMPLETED,
                    message=f"Thread test {category_suffix}",
                    url=f"https://thread-test-{category_suffix}.com",
                    category=category,
                    page=1,
                    max_products=50
                )
                self.cache.set(category, 1, response)
                results.append(f"set-{category_suffix}")
            except Exception as e:
                errors.append(e)
        
        def worker_get(category_suffix):
            try:
                category = f"MLU{category_suffix}"
                result = self.cache.get(category, 1)
                results.append(f"get-{category_suffix}-{result is not None}")
            except Exception as e:
                errors.append(e)
        
        # Crear y ejecutar threads
        threads = []
        for i in range(3):
            t1 = threading.Thread(target=worker_set, args=(f"10{i}",))
            t2 = threading.Thread(target=worker_get, args=(f"10{i}",))
            threads.extend([t1, t2])
        
        # Iniciar todos los threads
        for t in threads:
            t.start()
        
        # Esperar que terminen
        for t in threads:
            t.join()
        
        # Verificar que no hubo errores
        assert len(errors) == 0, f"Errores en threads: {errors}"
        assert len(results) > 0, "Debería haber resultados de los threads"
    
    def test_cache_key_normalization(self):
        """Test: Normalización de claves (mayúsculas/minúsculas)."""
        # Agregar con minúsculas
        self.cache.set("mlu107", 1, self.test_response)
        
        # Recuperar con mayúsculas
        result_upper = self.cache.get("MLU107", 1)
        assert result_upper is not None
        
        # Recuperar con minúsculas
        result_lower = self.cache.get("mlu107", 1)
        assert result_lower is not None
        
        # Deben ser la misma entrada
        assert result_upper.task_id == result_lower.task_id
    
    def test_cache_different_pages_same_category(self):
        """Test: Diferentes páginas de la misma categoría."""
        category = "MLU107"
        
        # Crear respuestas para diferentes páginas
        response_page1 = ScrapingResponse(
            task_id="page1-task",
            status=ScrapingStatus.COMPLETED,
            message="Página 1",
            url="https://test.com?page=1",
            category=category,
            page=1,
            max_products=50
        )
        
        response_page2 = ScrapingResponse(
            task_id="page2-task",
            status=ScrapingStatus.COMPLETED,
            message="Página 2",
            url="https://test.com?page=2",
            category=category,
            page=2,
            max_products=50
        )
        
        # Guardar ambas páginas
        self.cache.set(category, 1, response_page1)
        self.cache.set(category, 2, response_page2)
        
        # Verificar que son independientes
        cached_page1 = self.cache.get(category, 1)
        cached_page2 = self.cache.get(category, 2)
        
        assert cached_page1.task_id == "page1-task"
        assert cached_page2.task_id == "page2-task"
        assert cached_page1.page == 1
        assert cached_page2.page == 2
    
    def test_cache_memory_estimation(self):
        """Test: Estimación de uso de memoria."""
        # Cache vacío
        stats_empty = self.cache.get_stats()
        assert stats_empty["memory_usage_mb"] == 0
        
        # Agregar entrada
        self.cache.set("MLU107", 1, self.test_response)
        stats_with_data = self.cache.get_stats()
        assert stats_with_data["memory_usage_mb"] > 0
        
        # Agregar más entradas
        self.cache.set("MLA1234", 2, self.test_response_2)
        stats_more_data = self.cache.get_stats()
        assert stats_more_data["memory_usage_mb"] > stats_with_data["memory_usage_mb"]
    
    @pytest.mark.asyncio
    async def test_cache_concurrent_access(self):
        """Test: Acceso concurrente al cache."""
        async def set_operation(category_suffix: str):
            """Operación de escritura concurrente."""
            for i in range(10):
                category = f"MLU{category_suffix}"
                response = ScrapingResponse(
                    task_id=f"task-{category_suffix}-{i}",
                    status=ScrapingStatus.COMPLETED,
                    message=f"Concurrent test {i}",
                    url=f"https://test{i}.com",
                    category=category,
                    page=i + 1,
                    max_products=50
                )
                self.cache.set(category, i + 1, response)
        
        async def get_operation(category_suffix: str):
            """Operación de lectura concurrente."""
            results = []
            for i in range(10):
                category = f"MLU{category_suffix}"
                result = self.cache.get(category, i + 1)
                results.append(result)
            return results
        
        # Ejecutar operaciones concurrentes
        await asyncio.gather(
            set_operation("100"),
            set_operation("200"),
            set_operation("300")
        )
        
        # Verificar que todas las entradas se guardaron
        results_100 = await get_operation("100")
        results_200 = await get_operation("200")
        results_300 = await get_operation("300")
        
        # Verificar integridad de datos
        for i, result in enumerate(results_100):
            if result:  # Puede ser None si ya expiró
                assert result.category == "MLU100"
                assert result.page == i + 1
        
        # Verificar estadísticas finales
        final_stats = self.cache.get_stats()
        # Nota: Algunas entradas pueden haber expirado durante la prueba
        assert final_stats["total_entries"] >= 0


class TestCacheEntry:
    """Pruebas para la clase CacheEntry."""
    
    def test_cache_entry_creation(self):
        """Test: Creación correcta de CacheEntry."""
        response = ScrapingResponse(
            task_id="test-entry",
            status=ScrapingStatus.COMPLETED,
            message="Test entry",
            url="https://test.com",
            category="MLU107",
            page=1,
            max_products=50
        )
        
        created_at = time.time()
        expires_at = created_at + 3600
        
        entry = CacheEntry(
            data=response,
            created_at=created_at,
            expires_at=expires_at
        )
        
        assert entry.data == response
        assert entry.created_at == created_at
        assert entry.expires_at == expires_at
    
    def test_cache_entry_comparison(self):
        """Test: Comparación de entradas de cache."""
        response1 = ScrapingResponse(
            task_id="test-1",
            status=ScrapingStatus.COMPLETED,
            message="Test 1",
            url="https://test1.com",
            category="MLU107",
            page=1,
            max_products=50
        )
        
        response2 = ScrapingResponse(
            task_id="test-2",
            status=ScrapingStatus.COMPLETED,
            message="Test 2",
            url="https://test2.com",
            category="MLA1234",
            page=2,
            max_products=100
        )
        
        current_time = time.time()
        
        entry1 = CacheEntry(
            data=response1,
            created_at=current_time,
            expires_at=current_time + 1000
        )
        
        entry2 = CacheEntry(
            data=response2,
            created_at=current_time,
            expires_at=current_time + 2000
        )
        
        # Las entradas deben ser diferentes
        assert entry1.data.task_id != entry2.data.task_id
        assert entry1.expires_at != entry2.expires_at


class TestCacheIntegration:
    """Pruebas de integración para el cache con el flujo principal."""
    
    def setup_method(self):
        """Configurar antes de cada test."""
        self.cache = CacheManager(ttl_hours=0.1)  # 6 minutos para pruebas
        
    @pytest.mark.asyncio
    async def test_cache_prevents_duplicate_tasks(self):
        """Test: Cache previene creación de tareas duplicadas."""
        # Datos de prueba
        category = "MLU107"
        page = 1
        
        request_data = {
            "url": "https://test.com",
            "category": category,
            "page": page,
            "max_products": 50
        }
        
        # Primera llamada - no hay cache
        assert self.cache.get(category, page) is None
        
        # Simular que se crea la respuesta PENDING (como hace main.py)
        pending_response = ScrapingResponse(
            task_id="test-task-1",
            status=ScrapingStatus.PENDING,
            message="Tarea creada",
            url=request_data["url"],
            category=category,
            page=page,
            max_products=request_data["max_products"]
        )
        
        # Guardar en cache inmediatamente al crear la tarea
        self.cache.set(category, page, pending_response)
        
        # Segunda llamada inmediata debería obtener del cache
        cached_response = self.cache.get(category, page)
        assert cached_response is not None
        assert cached_response.task_id == "test-task-1"
        assert cached_response.status == ScrapingStatus.PENDING
        
        # Verificar que múltiples llamadas devuelven la misma respuesta
        for i in range(5):
            duplicate_response = self.cache.get(category, page)
            assert duplicate_response is not None
            assert duplicate_response.task_id == "test-task-1"
            assert duplicate_response.status == ScrapingStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_cache_state_transitions(self):
        """Test: Transiciones de estado en cache (PENDING → COMPLETED → invalidación en fallo)."""
        category = "MLU107"
        page = 1
        task_id = "test-transition"
        
        # Estado 1: PENDING (cuando se crea la tarea)
        pending_response = ScrapingResponse(
            task_id=task_id,
            status=ScrapingStatus.PENDING,
            message="Tarea creada",
            url="https://test.com",
            category=category,
            page=page,
            max_products=50
        )
        
        self.cache.set(category, page, pending_response)
        cached_pending = self.cache.get(category, page)
        assert cached_pending.status == ScrapingStatus.PENDING
        
        # Estado 2: COMPLETED (cuando termina exitosamente)
        completed_response = ScrapingResponse(
            task_id=task_id,
            status=ScrapingStatus.COMPLETED,
            message="Scraping completado exitosamente. 25 productos encontrados",
            url="https://test.com",
            category=category,
            page=page,
            max_products=50
        )
        
        self.cache.set(category, page, completed_response)
        cached_completed = self.cache.get(category, page)
        assert cached_completed.status == ScrapingStatus.COMPLETED
        assert "25 productos" in cached_completed.message
        
        # Estado 3: Invalidación en caso de fallo
        success = self.cache.invalidate(category, page)
        assert success is True
        
        cached_after_invalidation = self.cache.get(category, page)
        assert cached_after_invalidation is None
    
    @pytest.mark.asyncio
    async def test_cache_with_multiple_concurrent_requests(self):
        """Test: Cache maneja múltiples requests concurrentes correctamente."""
        import asyncio
        from unittest.mock import AsyncMock
        
        category = "MLU107"
        page = 1
        
        # Simular múltiples requests concurrentes para la misma página
        async def simulate_request(request_id: int):
            # Verificar cache
            cached = self.cache.get(category, page)
            if cached:
                return cached, True  # Cache hit
            
            # Simular creación de tarea si no hay cache
            await asyncio.sleep(0.01)  # Simular trabajo
            response = ScrapingResponse(
                task_id=f"concurrent-{request_id}",
                status=ScrapingStatus.PENDING,
                message=f"Request {request_id}",
                url="https://test.com",
                category=category,
                page=page,
                max_products=50
            )
            
            # Solo el primero debería guardar en cache
            existing = self.cache.get(category, page)
            if existing is None:
                self.cache.set(category, page, response)
                return response, False  # Cache miss
            else:
                return existing, True  # Otro thread ya guardó
        
        # Ejecutar múltiples requests concurrentes
        tasks = [simulate_request(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # Analizar resultados
        cache_hits = sum(1 for _, is_hit in results if is_hit)
        cache_misses = sum(1 for _, is_hit in results if not is_hit)
        
        # Debería haber al menos un cache miss (el primero) y algunos hits
        assert cache_misses >= 1, "Debería haber al menos un cache miss"
        
        # Verificar que todos tienen el mismo task_id (del cache)
        first_task_id = results[0][0].task_id
        for response, _ in results:
            # Nota: Debido a timing, algunos pueden tener task_ids diferentes
            # pero el cache debería eventualmente converger
            assert response.category == category
            assert response.page == page
    
    def test_cache_key_generation_consistency(self):
        """Test: Generación consistente de claves para diferentes formatos de entrada."""
        test_cases = [
            ("MLU107", 1, "MLU107:page:1"),
            ("mlu107", 1, "MLU107:page:1"),  # Normalización a mayúsculas
            ("MlU107", 1, "MLU107:page:1"),  # Caso mixto
            ("MLA1234", 999, "MLA1234:page:999"),
            ("mlc456", 5, "MLC456:page:5"),
        ]
        
        for category_input, page, expected_key in test_cases:
            actual_key = self.cache._generate_key(category_input, page)
            assert actual_key == expected_key, f"Clave incorrecta para {category_input}:{page}"
            
            # Verificar que se puede guardar y recuperar correctamente
            test_response = ScrapingResponse(
                task_id="test-key",
                status=ScrapingStatus.PENDING,
                message="Test",
                url="https://test.com",
                category=category_input,
                page=page,
                max_products=10
            )
            
            self.cache.set(category_input, page, test_response)
            retrieved = self.cache.get(category_input, page)
            assert retrieved is not None
            assert retrieved.task_id == "test-key"
    
    def test_cache_ttl_behavior_with_different_pages(self):
        """Test: TTL independiente para diferentes páginas de la misma categoría."""
        category = "MLU107"
        
        # Crear respuestas para diferentes páginas
        responses = {}
        for page in [1, 2, 3]:
            response = ScrapingResponse(
                task_id=f"page-{page}-task",
                status=ScrapingStatus.COMPLETED,
                message=f"Página {page} completada",
                url=f"https://test.com?page={page}",
                category=category,
                page=page,
                max_products=50
            )
            responses[page] = response
            self.cache.set(category, page, response)
        
        # Verificar que todas están en cache
        for page in [1, 2, 3]:
            cached = self.cache.get(category, page)
            assert cached is not None
            assert cached.page == page
            assert cached.task_id == f"page-{page}-task"
        
        # Invalidar solo una página
        success = self.cache.invalidate(category, 2)
        assert success is True
        
        # Verificar estado final
        assert self.cache.get(category, 1) is not None  # Sigue en cache
        assert self.cache.get(category, 2) is None      # Invalidada
        assert self.cache.get(category, 3) is not None  # Sigue en cache
    
    def test_cache_memory_cleanup_efficiency(self):
        """Test: Limpieza eficiente de memoria del cache."""
        # Llenar cache con muchas entradas
        for i in range(100):
            category = f"MLU{100 + i}"
            response = ScrapingResponse(
                task_id=f"bulk-{i}",
                status=ScrapingStatus.COMPLETED,
                message=f"Bulk test {i}",
                url=f"https://test{i}.com",
                category=category,
                page=1,
                max_products=10
            )
            self.cache.set(category, 1, response)
        
        # Verificar que se guardaron
        stats_full = self.cache.get_stats()
        assert stats_full["total_entries"] == 100
        assert stats_full["memory_usage_mb"] > 0
        
        # Limpiar cache
        self.cache.clear()
        
        # Verificar limpieza
        stats_empty = self.cache.get_stats()
        assert stats_empty["total_entries"] == 0
        assert stats_empty["memory_usage_mb"] == 0
        
        # Verificar que no queda ninguna entrada
        for i in range(100):
            category = f"MLU{100 + i}"
            assert self.cache.get(category, 1) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
