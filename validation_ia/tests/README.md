# Tests Unitarios - Sistema de Validación IA

Este directorio contiene todos los tests unitarios del sistema de validación de datos de scraping usando IA Generativa.

## Estructura de Tests

```
tests/
├── __init__.py
├── conftest.py                    # Configuración y fixtures comunes
├── test_main.py                   # Tests del script principal
├── modules/
│   ├── __init__.py
│   ├── test_openia.py            # Tests del módulo de IA
│   └── test_database_connector.py # Tests del conector de base de datos
└── README.md                      # Este archivo
```

## Patrón AAA (Arrange, Act, Assert)

Todos los tests siguen el patrón **AAA** (Arrange, Act, Assert) orientado a TDD:

- **Arrange**: Preparar los datos y mocks necesarios
- **Act**: Ejecutar la función/método que se está probando
- **Assert**: Verificar que el resultado es el esperado

### Ejemplo:

```python
def test_validation_result_creation(self):
    """Test: Creación de ValidationResult"""
    # Arrange
    issues = ["Issue 1", "Issue 2"]
    suggestions = ["Suggestion 1"]
    confidence_score = 0.85
    
    # Act
    result = ValidationResult(
        is_valid=True,
        issues=issues,
        suggestions=suggestions,
        confidence_score=confidence_score
    )
    
    # Assert
    assert result.is_valid is True
    assert len(result.issues) == 2
    assert len(result.suggestions) == 1
    assert result.confidence_score == 0.85
```

## Marcadores de Tests

Los tests están organizados con marcadores para facilitar su ejecución:

- `@pytest.mark.unit`: Tests unitarios básicos
- `@pytest.mark.integration`: Tests de integración
- `@pytest.mark.slow`: Tests que tardan más tiempo
- `@pytest.mark.ai`: Tests que requieren IA/OpenAI
- `@pytest.mark.database`: Tests que requieren conexión a base de datos

## Ejecución de Tests

### Usando el script de tests:

```bash
# Ejecutar todos los tests
./run_tests.sh

# Ejecutar con output detallado
./run_tests.sh -v

# Ejecutar con reporte de cobertura
./run_tests.sh -c

# Ejecutar solo tests rápidos (sin slow/ai/database)
./run_tests.sh -f

# Ejecutar solo tests unitarios
./run_tests.sh --unit

# Ejecutar solo tests de integración
./run_tests.sh --integration

# Ejecutar un test específico
./run_tests.sh -t test_main.py::TestValidatorIA::test_init

# Ver marcadores disponibles
./run_tests.sh -m
```

### Usando pytest directamente:

```bash
# Ejecutar todos los tests
poetry run pytest

# Ejecutar con output detallado
poetry run pytest -v

# Ejecutar con cobertura
poetry run pytest --cov=modules --cov=main --cov-report=html

# Ejecutar tests específicos
poetry run pytest tests/modules/test_openia.py

# Ejecutar tests con marcador específico
poetry run pytest -m unit
poetry run pytest -m "not slow"
```

## Fixtures Comunes

El archivo `conftest.py` contiene fixtures reutilizables:

- `sample_product`: Producto de ejemplo válido
- `invalid_product`: Producto con problemas de validación
- `sample_products`: Lista de productos de ejemplo
- `mock_validation_result`: Resultado de validación de ejemplo
- `mock_invalid_validation_result`: Resultado con issues
- `mock_openai_response`: Respuesta simulada de OpenAI
- `mock_supabase_product`: Producto simulado de Supabase
- `mock_supabase_client`: Cliente simulado de Supabase
- `mock_env_vars`: Variables de entorno simuladas

## Cobertura de Tests

Los tests cubren:

### Módulo de IA (`test_openia.py`):
- ✅ Inicialización del validador
- ✅ Creación de prompts para validación
- ✅ Parsing de respuestas JSON
- ✅ Validación de productos en lote
- ✅ Manejo de errores de OpenAI
- ✅ Rate limiting
- ✅ Validación de productos individuales

### Conector de Base de Datos (`test_database_connector.py`):
- ✅ Inicialización del conector
- ✅ Creación de registros de validación
- ✅ Creación de registros de ejecución
- ✅ Actualización de registros
- ✅ Consulta de registros por artículo
- ✅ Consulta de ejecuciones por ID
- ✅ Manejo de casos de error

### Script Principal (`test_main.py`):
- ✅ Inicialización del validador principal
- ✅ Obtención de productos de Supabase
- ✅ Filtrado por categoría y página
- ✅ Conversión de productos de Supabase
- ✅ Proceso completo de validación
- ✅ Manejo de errores
- ✅ Tests de integración del script principal

## Mejores Prácticas

1. **Nombres descriptivos**: Los nombres de los tests describen claramente qué se está probando
2. **Un test por comportamiento**: Cada test verifica un comportamiento específico
3. **Mocks apropiados**: Se usan mocks para dependencias externas (OpenAI, Supabase)
4. **Fixtures reutilizables**: Los datos de prueba se comparten entre tests
5. **Patrón AAA**: Todos los tests siguen el patrón Arrange-Act-Assert
6. **Marcadores**: Los tests están marcados para facilitar su ejecución selectiva

## Debugging de Tests

Si un test falla:

1. Ejecuta el test específico con output detallado:
   ```bash
   poetry run pytest -v -s tests/modules/test_openia.py::TestAIValidator::test_init_with_valid_api_key
   ```

2. Usa el debugger de pytest:
   ```bash
   poetry run pytest --pdb tests/modules/test_openia.py::TestAIValidator::test_init_with_valid_api_key
   ```

3. Verifica que las dependencias estén instaladas:
   ```bash
   poetry install --with dev
   ```

## Contribución

Al agregar nuevos tests:

1. Sigue el patrón AAA
2. Usa fixtures existentes cuando sea posible
3. Agrega marcadores apropiados
4. Documenta el propósito del test
5. Asegúrate de que el test sea determinístico
6. Verifica que la cobertura se mantenga alta
