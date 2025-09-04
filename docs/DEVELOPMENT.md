# 🛠️ Guía de Desarrollo - Sistema de Scraping Mercado Libre Uruguay

Esta guía contiene información técnica detallada para desarrolladores que trabajen en el sistema de scraping automatizado.

## 🗄️ Base de Datos

### Tipo de Base de Datos
- **Motor**: PostgreSQL (a través de Supabase)
- **Versión**: PostgreSQL 15+
- **Características**: JSONB, índices automáticos, UUID, timestamps

### Esquema de Tabla Principal

#### Tabla: `products`
Almacena todos los productos scrapeados:

```sql
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category TEXT NOT NULL,
    page INTEGER NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    seller TEXT NOT NULL,
    current_price DECIMAL(10, 2) NOT NULL,
    original_price DECIMAL(10, 2),
    discount_percentage TEXT,
    currency TEXT NOT NULL,
    rating DECIMAL(3, 1),
    review_count INT,
    stock_quantity TEXT,
    features JSONB NOT NULL DEFAULT '{}'::jsonb,
    images JSONB NOT NULL DEFAULT '{}'::jsonb,
    description TEXT,
    seller_location TEXT,
    shipping_method TEXT,
    brand TEXT,
    scraped_at TIMESTAMP NOT NULL,
    created_at_audit TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at_audit TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**Campos principales**:
- `id`: UUID único generado automáticamente
- `category` y `page`: Metadatos de scraping
- `features` e `images`: Datos JSONB para flexibilidad
- Timestamps de auditoría para tracking

## 🔧 Gestión de Dependencias

### Estructura con Poetry
El proyecto utiliza Poetry para gestión de dependencias en cada servicio:

#### Publisher (`publisher/pyproject.toml`)
```toml
[tool.poetry.dependencies]
python = "^3.10"
fastapi = "^0.104.1"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
pika = "^1.3.2"
pydantic = "^2.5.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
pytest-asyncio = "^0.21.1"
httpx = "^0.25.2"

[tool.poetry.scripts]
start = "uvicorn main:app --host 0.0.0.0 --port 8000"
test = "pytest tests/ -v"
```

#### Subscriber (`subscriber/pyproject.toml`)
```toml
[tool.poetry.dependencies]
python = "^3.10"
playwright = "^1.40.0"
camoufox = {extras = ["geoip"], version = "^0.4.11"}
fastapi = "^0.104.1"
pika = "^1.3.0"
supabase = "^2.18.1"
loguru = "^0.7.0"

[tool.poetry.scripts]
scrape = "scraper.cli:main"
start-api = "main:start_api"
start-listener = "message_listener:main"
```

### Comandos de gestión

#### Instalar dependencias
```bash
# En cada servicio
cd publisher && poetry install
cd subscriber && poetry install

# Instalar dependencias de desarrollo
poetry install --with dev
```

#### Agregar nueva dependencia
```bash
# Dependencia principal
poetry add nombre-paquete

# Dependencia de desarrollo
poetry add --group dev nombre-paquete

# Versión específica
poetry add "paquete==1.2.3"
```

#### Actualizar dependencias
```bash
# Actualizar todas
poetry update

# Ver dependencias desactualizadas
poetry show --outdated
```

## 🧪 Tests Unitarios

### Estructura de Tests

#### Publisher Tests
```
publisher/tests/
├── conftest.py                # Fixtures comunes
├── test_main.py              # Tests del API REST
└── test_config.py            # Tests de configuración
```

#### Subscriber Tests (Más completos)
```
subscriber/tests/
├── conftest.py                    # Fixtures globales
├── test_main.py                   # Tests del API principal
├── test_main_integration.py       # Tests de integración
├── manager/
│   ├── test_rabbitmq_manager.py   # Tests del gestor RabbitMQ
│   └── test_message_listener.py   # Tests del listener
└── scraper/
    └── test_scraper_service.py    # Tests del scraper
```

### Configuración de Pytest

#### Publisher (`publisher/pyproject.toml`)
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
python_files = ["test_*.py"]
addopts = ["-v", "--tb=short", "--strict-markers"]
markers = [
    "unit: marks tests as unit tests",
    "integration: marks tests as integration tests"
]
```

#### Subscriber (`subscriber/pyproject.toml`)
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
asyncio_mode = "auto"
markers = [
    "unit: marcador para tests unitarios",
    "integration: marcador para tests de integración",
    "performance: marcador para tests de rendimiento",
    "slow: marcador para tests que tardan más tiempo"
]
addopts = ["-v", "--strict-markers", "--tb=short", "--show-capture=no"]
```

### Comandos de Testing

#### Ejecutar tests básicos
```bash
# Publisher
cd publisher
poetry run test
# O equivalente: poetry run pytest tests/ -v

# Subscriber - Tests unitarios
cd subscriber
poetry run pytest tests/ -v

cd validation_ia
poetry run pytest tests/ -v
```

#### Tests con cobertura
```bash
# Publisher
cd publisher
poetry run pytest tests/ --cov=. --cov-report=term-missing

# Subscriber
cd subscriber
poetry run pytest tests/ -v --cov=. --cov-report=term-missing

cd validation_ia
poetry run pytest tests/ -v --cov=. --cov-report=term-missing
```

#### Tests específicos
```bash
# Por archivo
poetry run pytest tests/test_main.py -v

# Por clase
poetry run pytest tests/test_main.py::TestMainAPI -v

# Por función específica
poetry run pytest tests/test_main.py::TestMainAPI::test_root_endpoint_returns_correct_response -v

# Por marcadores
poetry run pytest -m unit -v
poetry run pytest -m "not slow" -v
```

### Tests con Docker:
```bash
# Ejecutar tests desde containers
docker exec publisher poetry run pytest
docker exec subscriber poetry run pytest tests/ -v
```

#### Modo detallado y debugging
```bash
# Con output completo
poetry run pytest tests/ -v -s

# Con debugging (se detiene en fallos)
poetry run pytest tests/ --pdb

# Solo mostrar fallos
poetry run pytest tests/ --tb=short

# Tests muy específicos con más info
poetry run pytest tests/test_main.py::test_specific -v -s --tb=long
```

### Cobertura detallada
```bash
# Cobertura con reporte HTML
poetry run pytest tests/ --cov=. --cov-report=html
# Resultado en htmlcov/index.html

# Cobertura solo de archivos específicos
poetry run pytest tests/ --cov=main --cov=manager --cov-report=term-missing

# Cobertura con límite mínimo
poetry run pytest tests/ --cov=. --cov-fail-under=80
```

## 📊 Monitoreo

### RabbitMQ Management
- URL: http://localhost:15672
- Usuario: `admin`
- Contraseña: `admin123`

### APIs
- Publisher: http://localhost:8001/docs
- Subscriber: http://localhost:8002/docs

## 💾 Persistencia de Datos

### Base de Datos: PostgreSQL (Supabase)
Los productos scrapeados se almacenan en una tabla `products` con la siguiente estructura:

- **ID único**: UUID generado automáticamente
- **Metadatos**: Categoría, página, fecha de scraping
- **Información del producto**: Título, URL, vendedor, precios
- **Características**: Rating, reviews, stock, features (JSONB)
- **Auditoría**: Timestamps de creación y actualización

## 🌍 Ambiente de Desarrollo

### Configuración inicial
```bash
# 1. Clonar proyecto
git clone <repositorio>
cd test-scrapping

# 2. Verificar Poetry instalado
poetry --version

# 3. Instalar dependencias para cada servicio
cd publisher && poetry install
cd ../subscriber && poetry install

# 4. Activar environments
cd publisher && poetry shell
# En otra terminal:
cd subscriber && poetry shell
```

### Variables de entorno

#### Publisher (`.env`)
```bash
# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASS=admin123

# API
API_HOST=0.0.0.0
API_PORT=8000
```

#### Subscriber (`.env`)
```bash
# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASS=admin123

# Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-service-key

# Scraping
MAX_WORKERS=3
BROWSER_HEADLESS=true
RATE_LIMIT_DELAY=2.0
```

### Configuración de IDE (VSCode)

#### `.vscode/settings.json`
```json
{
    "python.defaultInterpreterPath": "publisher/.venv/bin/python",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"],
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "files.associations": {
        "*.toml": "toml"
    }
}
```

## 🚀 Ejecución Local para Desarrollo

### Modo desarrollo recomendado (Poetry)

#### Terminal 1: RabbitMQ
```bash
# Desde raíz del proyecto
docker-compose up rabbitmq -d

# Verificar
docker logs rabbitmq
```

#### Terminal 2: Publisher
```bash
cd publisher
poetry install
poetry shell
poetry run start

# O directamente
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Terminal 3: Subscriber API
```bash
cd subscriber
poetry install
poetry shell
poetry run start-api

# O con recarga automática
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Terminal 4: Subscriber Listener
```bash
cd subscriber
poetry shell
poetry run start-listener

# O directamente
poetry run python message_listener.py
```

### Desarrollo con hot-reload
```bash
# Publisher con recarga automática
cd publisher
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Subscriber API con recarga automática  
cd subscriber
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Debugging
```bash
# Con pdb
poetry run python -m pdb main.py

# Con pytest debugger
poetry run pytest --pdb tests/test_main.py::test_specific

# Con logs detallados
LOG_LEVEL=DEBUG poetry run start-api
```

## 🔍 Monitoreo y Logs

### Configuración de Loguru (Subscriber)
```python
from loguru import logger

# Configuración en módulos
logger.add(
    "logs/api_{time:YYYY-MM-DD_HH-mm-ss}_{process.id}.log",
    rotation="1 hour",
    retention="7 days",
    level="INFO"
)
```

### Niveles de log recomendados
- `DEBUG`: Información detallada para debugging
- `INFO`: Información general del proceso  
- `WARNING`: Situaciones que requieren atención
- `ERROR`: Errores que no detienen la ejecución
- `CRITICAL`: Errores críticos que detienen el proceso

### Logs en tiempo real
```bash
# Ver logs de contenedores
docker logs -f rabbitmq
docker logs -f publisher
docker logs -f subscriber

# Ver logs de archivos locales
tail -f subscriber/logs/api.log
tail -f publisher/logs/api.log
```

## 🔧 Arquitectura del Código

### Patrón de Diseño
- **Arquitectura limpia**: Separación clara de responsabilidades
- **Publisher-Subscriber**: Comunicación asíncrona vía RabbitMQ
- **Inyección de dependencias**: Servicios configurables
- **Validación de datos**: Pydantic para validación automática

### Flujo de datos detallado
1. `publisher/main.py` → API REST que recibe requests
2. `publisher/` → Envía mensajes a RabbitMQ  
3. `subscriber/manager/listeners/message_listener.py` → Procesa mensajes
4. `subscriber/scraper/services/scraper_service.py` → Ejecuta scraping
5. `subscriber/database/connectors/database_connector.py` → Persiste en Supabase

### Principios SOLID aplicados
- **Single Responsibility**: Cada clase tiene una función específica
- **Open/Closed**: Extensible sin modificar código existente
- **Dependency Inversion**: Depende de abstracciones, no de concreciones

## 📊 Métricas y Monitoring

### Métricas automáticas (Subscriber)
- Tiempo de ejecución por tarea
- Número de productos scrapeados exitosamente
- Rate de errores por categoría
- Uso de cache y invalidaciones

### Logging estructurado
```python
# Subscriber
logger.info("Task completed", 
    task_id=task.id,
    products_scraped=len(products),
    execution_time="2.5s",
    category=task.request.category
)

# Publisher  
logger.info("Message sent to queue",
    queue="scraping_queue",
    routing_key="scraping", 
    message_id=msg_id
)
```

## 🚨 Troubleshooting

### Problemas comunes

#### Error de conexión a RabbitMQ
```bash
# Verificar que RabbitMQ esté corriendo
docker ps | grep rabbitmq

# Verificar logs
docker logs rabbitmq

# Reiniciar si es necesario
docker-compose restart rabbitmq
```

#### Error de conexión a Supabase
```bash
# Verificar variables en subscriber
cd subscriber
cat .env | grep SUPABASE

# Test de conexión
poetry run python -c "
from database.connectors.database_connector import DatabaseConnector
db = DatabaseConnector()
print('✅ Conexión exitosa')
"
```

#### Tests fallando
```bash
# Reinstalar dependencias
poetry install --with dev

# Verificar pytest
poetry run python -m pytest --version

# Ejecutar test simple
poetry run pytest tests/test_main.py::test_basic -v
```

#### Playwright/Camoufox issues
```bash
# Reinstalar browsers (subscriber)
cd subscriber
poetry run playwright install
poetry run camoufox --version
```

## 🎯 Mejores Prácticas de Desarrollo

### Antes de commit
1. **Ejecutar todos los tests** en ambos servicios
2. **Verificar cobertura** mínima del 80%
3. **Revisar logs** que no haya warnings
4. **Probar flujo completo** localmente

### Comandos pre-commit
```bash
# Publisher
cd publisher
poetry run pytest tests/ --cov=. --cov-fail-under=80
poetry run black .
poetry run isort .

# Subscriber  
cd subscriber
poetry run pytest tests/ --cov=. --cov-fail-under=80
poetry run black .
poetry run isort .
```

### Performance
1. **Usar rate limiting** para evitar bloqueos
2. **Implementar cache** en subscriber para evitar re-scraping
3. **Monitorear memoria** con scraping pesado
4. **Optimizar consultas** a Supabase

### Seguridad
1. **Variables de entorno** para credenciales
2. **Validar inputs** en APIs con Pydantic
3. **Rate limiting** en endpoints públicos
4. **Logs sin datos sensibles**

### Desarrollo colaborativo
1. **Branches por feature** y PRs
2. **Tests para nuevas features** antes de merge
3. **Documentar cambios** en archivos relevantes
4. **Code review** obligatorio para cambios críticos

## 🔄 Flujo de desarrollo típico

### Agregar nueva feature
```bash
# 1. Crear branch
git checkout -b feature/nueva-funcionalidad

# 2. Escribir tests primero (TDD)
cd subscriber
poetry run pytest tests/test_nueva_feature.py -v

# 3. Implementar feature
# ... código ...

# 4. Verificar tests pasan
poetry run pytest tests/ -v --cov=. --cov-report=term-missing

# 5. Probar integración completa
# ... test manual ...

# 6. Commit y push
git add .
git commit -m "feat: agregar nueva funcionalidad"
git push origin feature/nueva-funcionalidad
```

### Debugging de problemas
```bash
# 1. Reproducir problema localmente
cd subscriber
LOG_LEVEL=DEBUG poetry run start-listener

# 2. Revisar logs detallados
tail -f logs/api.log

# 3. Ejecutar tests relacionados
poetry run pytest tests/test_problema.py -v -s

# 4. Usar debugger si es necesario
poetry run python -m pdb script_problema.py
```

Esta guía cubre los aspectos esenciales para el desarrollo productivo del sistema. Para información específica de despliegue, consulta [`DEPLOYMENT.md`](DEPLOYMENT.md).
