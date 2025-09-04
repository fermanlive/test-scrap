# Arquitectura Limpia - Subscriber

## Estructura de Módulos

La aplicación ha sido reorganizada siguiendo principios de arquitectura limpia con los siguientes módulos:

### 📁 `manager/`
**Gestión de colas y mensajería**
- `rabbitmq_manager.py` - Gestor de colas RabbitMQ
- `listeners/` - Listeners de mensajes
  - `message_listener.py` - Listener principal de mensajes
- `workers/` - Workers para procesamiento
  - `worker.py` - Worker de Celery para tareas en background

### 📁 `database/`
**Capa de acceso a datos**
- `connectors/` - Conectores de base de datos
  - `database_connector.py` - Conector principal a la base de datos
- `repositories/` - Repositorios de datos (preparado para futuras implementaciones)

### 📁 `scraper/`
**Lógica de negocio de scraping**
- `services/` - Servicios de scraping
  - `scraper_service.py` - Servicio principal de scraping
- `simple_scraper.py` - Scraper base (existente)
- `models/` - Modelos específicos del scraper (existente)
- `utils/` - Utilidades del scraper (existente)

### 📁 `models/`
**Modelos de datos (dataclasses)**
- `scraping_models.py` - Modelos Pydantic para la API

### 📁 `config/`
**Configuración de la aplicación** (sin cambios)
- Archivos de configuración existentes

## Importaciones Actualizadas

### Antes:
```python
from models import ScrapingRequest
from rabbitmq_manager import RabbitMQManager
from scraper_service import ScraperService
from database.database_connector import DatabaseConnector
```

### Después:
```python
from models import ScrapingRequest
from manager import RabbitMQManager
from scraper.services import ScraperService
from database import DatabaseConnector
```

## Beneficios de la Nueva Arquitectura

1. **Separación de responsabilidades**: Cada módulo tiene una responsabilidad específica
2. **Facilidad de mantenimiento**: Código organizado por funcionalidad
3. **Escalabilidad**: Fácil agregar nuevos servicios o conectores
4. **Testabilidad**: Módulos independientes más fáciles de testear
5. **Reutilización**: Componentes pueden ser reutilizados en otros proyectos

## Estructura de Archivos

```
subscriber/
├── manager/                    # Gestión de colas y mensajería
│   ├── __init__.py
│   ├── rabbitmq_manager.py
│   ├── listeners/
│   │   ├── __init__.py
│   │   └── message_listener.py
│   └── workers/
│       ├── __init__.py
│       └── worker.py
├── database/                   # Acceso a datos
│   ├── __init__.py
│   ├── connectors/
│   │   ├── __init__.py
│   │   └── database_connector.py
│   └── repositories/
│       └── __init__.py
├── scraper/                    # Lógica de scraping
│   ├── __init__.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── scraper_service.py
│   ├── simple_scraper.py
│   ├── models/
│   └── utils/
├── models/                     # Modelos de datos
│   ├── __init__.py
│   └── scraping_models.py
├── config/                     # Configuración
├── main.py                     # Punto de entrada
└── ARCHITECTURE.md            # Este archivo
```

## Uso

La aplicación mantiene la misma funcionalidad, pero ahora con una estructura más limpia y organizada. Todas las importaciones han sido actualizadas para usar la nueva estructura modular.
