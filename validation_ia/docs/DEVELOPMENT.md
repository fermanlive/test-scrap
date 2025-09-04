# 🛠️ Guía de Desarrollo - Sistema de Validación IA

Esta guía contiene información técnica detallada para desarrolladores que trabajen en el sistema de validación con IA Generativa.

## 🗄️ Base de Datos

### Tipo de Base de Datos
- **Motor**: PostgreSQL (a través de Supabase)
- **Versión**: PostgreSQL 15+
- **Características**: JSONB, índices GIN, triggers automáticos

### Esquemas de Tablas

#### Tabla: `validation_records`
Logs individuales de validación por producto:

```sql
CREATE TABLE validation_records (
    id SERIAL PRIMARY KEY,
    article_id TEXT NOT NULL,
    validation_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL CHECK (status IN ('Ok', 'issues')),
    issues JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Campos**:
- `article_id`: ID único del producto validado
- `status`: "Ok" (sin problemas) o "issues" (con problemas)
- `issues`: Array JSON con lista de problemas detectados
- `metadata`: JSON con información adicional (confidence_score, suggestions, etc.)

#### Tabla: `executions`
Registro de ejecuciones completas del proceso:

```sql
CREATE TABLE executions (
    id SERIAL PRIMARY KEY,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    status TEXT NOT NULL CHECK (status IN ('Error', 'Done', 'Not complete', 'In Progress')),
    records_status TEXT NOT NULL CHECK (records_status IN ('Ok', 'issues', 'Not started', 'Processing')),
    issues_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    total_records INTEGER NOT NULL DEFAULT 0,
    valid_records INTEGER NOT NULL DEFAULT 0,
    invalid_records INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Estados de `status`**:
- `In Progress`: Proceso ejecutándose
- `Done`: Completado exitosamente
- `Error`: Error durante la ejecución
- `Not complete`: Interrumpido o incompleto

**Estados de `records_status`**:
- `Not started`: No se ha iniciado la validación
- `Processing`: Validando productos
- `Ok`: Todos los productos válidos
- `issues`: Algunos productos con problemas

### Índices de Optimización

```sql
-- Índices básicos
CREATE INDEX idx_validation_records_article_id ON validation_records(article_id);
CREATE INDEX idx_validation_records_date ON validation_records(validation_date);
CREATE INDEX idx_validation_records_status ON validation_records(status);
CREATE INDEX idx_executions_status ON executions(status);
CREATE INDEX idx_executions_start_time ON executions(start_time);

-- Índices GIN para JSONB (consultas eficientes en JSON)
CREATE INDEX idx_validation_records_issues_gin ON validation_records USING GIN (issues);
CREATE INDEX idx_validation_records_metadata_gin ON validation_records USING GIN (metadata);
CREATE INDEX idx_executions_issues_summary_gin ON executions USING GIN (issues_summary);
```

## 📋 Modelos de Datos

### Archivo: `models/models.py`

#### Clase `Product`
Modelo principal para productos:

```python
from pydantic import BaseModel, Field
from typing import Optional

class Product(BaseModel):
    article_id: str = Field(..., description="ID único del producto")
    name: str = Field(..., description="Nombre del producto")
    original_price: float = Field(..., gt=0, description="Precio original")
    current_price: float = Field(..., gt=0, description="Precio actual")
    discount_percentage: Optional[float] = Field(None, ge=0, le=100)
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    availability: Optional[str] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    review_count: Optional[int] = Field(None, ge=0)
```

#### Validaciones Automáticas
- **Precios**: Deben ser positivos (gt=0)
- **Rating**: Rango 0-5
- **Descuento**: Rango 0-100%
- **Review count**: No negativo

## 🔧 Gestión de Dependencias

### Archivo: `pyproject.toml`

#### Dependencias principales
```toml
[tool.poetry.dependencies]
python = "^3.10"
pydantic = "^2.0.0"      # Validación de datos
supabase = "^2.0.0"      # Cliente de Supabase
openai = "^1.0.0"        # Cliente de OpenAI
python-dotenv = "^1.0.0" # Variables de entorno
loguru = "^0.7.3"        # Logging avanzado
```

#### Dependencias de desarrollo
```toml
[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"        # Framework de testing
pytest-cov = "^4.1.0"    # Cobertura de tests
pytest-mock = "^3.11.0"  # Mocking para tests
```

### Comandos de gestión

#### Agregar nueva dependencia
```bash
# Dependencia principal
poetry add nombre-paquete

# Dependencia de desarrollo
poetry add --group dev nombre-paquete

# Dependencia opcional
poetry add --optional nombre-paquete

# Versión específica
poetry add "paquete==1.2.3"
```

#### Actualizar dependencias
```bash
# Actualizar todas
poetry update

# Actualizar específica
poetry update nombre-paquete

# Ver dependencias desactualizadas
poetry show --outdated
```

## 🧪 Tests Unitarios

### Estructura de Tests
```
tests/
├── conftest.py                    # Fixtures comunes
├── test_main.py                   # Tests del script principal
└── modules/
    ├── test_openia.py            # Tests del validador IA
    └── test_database_connector.py # Tests del conector DB
```

### Configuración de Pytest

#### En `pyproject.toml`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",                    # Verbose
    "--tb=short",           # Traceback corto
    "--strict-markers",     # Marcadores estrictos
    "--disable-warnings"    # Sin warnings
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow running tests",
    "ai: Tests that require AI/OpenAI",
    "database: Tests that require database connection"
]
```

### Comandos de Testing

#### Ejecutar todos los tests
```bash
poetry run python -m pytest --cov=tests/ --cov-report=term-missing
```

#### Tests específicos
```bash
# Por archivo
poetry run python -m pytest tests/modules/test_openia.py

# Por función
poetry run python -m pytest tests/test_main.py::test_validator_init

# Por marcador
poetry run python -m pytest -m unit
poetry run python -m pytest -m "not slow"

# Con output detallado
poetry run python -m pytest -v -s

# Solo tests rápidos
poetry run python -m pytest -m "not slow and not ai and not database"
```

#### Cobertura de código
```bash
# Con reporte en terminal
poetry run python -m pytest --cov=modules --cov=main --cov-report=term-missing

# Con reporte HTML
poetry run python -m pytest --cov=modules --cov=main --cov-report=html

# Solo cobertura específica
poetry run python -m pytest --cov=modules/openia --cov-report=term-missing
```

## 🌍 Ambiente de Desarrollo

### Crear ambiente desde cero
```bash
# 1. Clonar proyecto
git clone <repositorio>
cd validation_ia

# 2. Instalar Poetry (si no está instalado)
curl -sSL https://install.python-poetry.org | python3 -

# 3. Instalar dependencias
poetry install

# 4. Activar ambiente virtual
poetry shell

# 5. Verificar instalación
poetry run python --version
poetry show
```

### Variables de entorno de desarrollo
```bash
# Copiar archivo de ejemplo
cp config.env.example .env

# Configurar variables
# .env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_KEY=tu-service-key
OPENAI_API_KEY=tu-openai-api-key

# Variables opcionales para desarrollo
DEBUG=true
LOG_LEVEL=DEBUG
BATCH_SIZE=5  # Lotes pequeños para testing
```

### Configuración de IDE

#### VSCode (`.vscode/settings.json`)
```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"],
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true
}
```

## 🚀 Ejecución Local

### Desarrollo con Poetry
```bash
# Activar ambiente
poetry shell

# Ejecutar aplicación
poetry run validate

# Con parámetros
poetry run validate --category "Electronics" --page 0

# Ejecutar con Python directamente
poetry run python main.py
```

### Desarrollo con variables de entorno
```bash
# Cargar variables y ejecutar
export $(cat .env | xargs) && python main.py

# O usando dotenv
python -c "from dotenv import load_dotenv; load_dotenv()" && python main.py
```

### Debugging
```bash
# Con pdb
poetry run python -m pdb main.py

# Con pytest debugger
poetry run python -m pytest --pdb tests/test_main.py::test_specific

# Con logs detallados
LOG_LEVEL=DEBUG poetry run validate
```

## 🔍 Monitoreo y Logs

### Configuración de Loguru
```python
from loguru import logger

# Configuración en modules/
logger.add(
    "logs/validation_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="INFO"
)
```

### Niveles de log
- `DEBUG`: Información detallada para debugging
- `INFO`: Información general del proceso
- `WARNING`: Situaciones que requieren atención
- `ERROR`: Errores que no detienen la ejecución
- `CRITICAL`: Errores críticos que detienen el proceso

## 🔧 Arquitectura del Código

### Patrón de Diseño
- **Separación de responsabilidades**: Cada módulo tiene una función específica
- **Inyección de dependencias**: Los conectores se pasan como parámetros
- **Validación de datos**: Pydantic para validación automática
- **Manejo de errores**: Try-catch con fallbacks automáticos

### Flujo de datos
1. `main.py` → Script principal y CLI
2. `modules/database_connector.py` → Comunicación con Supabase
3. `modules/openia.py` → Validación con IA
4. `models/models.py` → Definición de estructuras de datos

### Principios seguidos
- **DRY**: Don't Repeat Yourself
- **SOLID**: Especialmente Single Responsibility
- **Fail-fast**: Validación temprana de parámetros
- **Graceful degradation**: Fallback a validación básica si IA falla

## 📊 Métricas y Monitoring

### Métricas automáticas
- Tiempo de ejecución por lote
- Porcentaje de productos válidos
- Score de confianza promedio
- Errores por tipo

### Logging estructurado
```python
logger.info("Validation completed", 
    total_products=100,
    valid_products=95,
    execution_time="2.5s",
    confidence_avg=0.87
)
```

## 🚨 Troubleshooting

### Problemas comunes

#### Error de conexión a Supabase
```bash
# Verificar variables
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_KEY

# Test de conexión
poetry run python -c "from modules.database_connector import DatabaseConnector; db = DatabaseConnector(); print('✅ Conexión exitosa')"
```

#### Error de OpenAI API
```bash
# Verificar API key
echo $OPENAI_API_KEY

# Test de API
poetry run python -c "from modules.openia import AIValidator; ai = AIValidator(); print('✅ OpenAI configurado')"
```

#### Tests fallando
```bash
# Instalar dependencias de desarrollo
poetry install --with dev

# Verificar pytest
poetry run python -m pytest --version

# Ejecutar test simple
poetry run python -m pytest tests/test_main.py::test_validator_init -v
```

## 🎯 Mejores Prácticas

### Desarrollo
1. **Siempre ejecutar tests** antes de commit
2. **Usar type hints** en todas las funciones
3. **Documentar funciones** con docstrings
4. **Validar parámetros** con Pydantic
5. **Manejar excepciones** apropiadamente

### Performance
1. **Usar lotes** para procesamiento masivo
2. **Implementar rate limiting** para APIs externas
3. **Cachear resultados** cuando sea apropiado
4. **Optimizar consultas** de base de datos

### Seguridad
1. **Nunca commitear** archivos `.env`
2. **Usar variables de entorno** para credenciales
3. **Validar inputs** del usuario
4. **Rotar API keys** regularmente
