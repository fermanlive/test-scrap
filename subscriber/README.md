# API de Scraping - Mercado Libre Uruguay

API REST para el sistema de scraping escalable de Mercado Libre Uruguay, que recibe colas de valores y utiliza el scraper existente.

## 🚀 Características

- **API REST**: Endpoints para crear y monitorear tareas de scraping
- **Cola de Tareas**: Sistema de colas usando Redis para manejar múltiples solicitudes
- **Procesamiento Asíncrono**: Tareas de scraping ejecutadas en background
- **Validaciones**: Validación automática de categorías y parámetros
- **Monitoreo**: Endpoints de salud y estadísticas del sistema
- **Integración**: Utiliza el scraper existente de la carpeta `scraper`

## 📋 Requisitos

- Python 3.8+
- Redis
- Poetry (para gestión de dependencias)

## 🛠️ Instalación

1. **Instalar dependencias con Poetry:**
   ```bash
   cd listener
   poetry install
   ```

2. **Configurar variables de entorno:**
   ```bash
   cp env.example .env
   # Editar .env con tus configuraciones
   ```

3. **Iniciar Redis:**
   ```bash
   # En macOS con Homebrew
   brew services start redis
   
   # O manualmente
   redis-server
   ```

## 🚀 Uso

### Iniciar la API

```bash
# Con Poetry
poetry run start-api

# O manualmente
poetry run python -m listener.main
```

### Iniciar el Worker (opcional)

```bash
# Con Poetry
poetry run start-worker

# O manualmente
poetry run python -m listener.worker
```

## 📡 Endpoints de la API

### 1. Crear Tarea de Scraping

```http
POST /scrape
Content-Type: application/json

{
  "category": "MLU5725",
  "page": 1,
  "max_products": 20
}
```

**Respuesta:**
```json
{
  "task_id": "uuid-1234-5678",
  "status": "pending",
  "message": "Tarea de scraping creada exitosamente",
  "url": "https://www.mercadolibre.com.uy/ofertas?category=MLU5725&page=1",
  "category": "MLU5725",
  "page": 1,
  "max_products": 20
}
```

### 2. Verificar Estado de Tarea

```http
GET /tasks/{task_id}
```

**Respuesta:**
```json
{
  "id": "uuid-1234-5678",
  "request": {
    "category": "MLU5725",
    "page": 1,
    "max_products": 20
  },
  "status": "completed",
  "created_at": "2024-01-15T10:30:00",
  "started_at": "2024-01-15T10:30:05",
  "completed_at": "2024-01-15T10:32:15",
  "result_file": "/path/to/output/scraping_20240115_103215.json"
}
```

### 3. Listar Tareas

```http
GET /tasks?limit=10&offset=0
```

### 4. Verificar Salud del Sistema

```http
GET /health
```

### 5. Obtener Categorías Válidas

```http
GET /categories
```

## 🏷️ Categorías Válidas

| Código | Nombre |
|--------|--------|
| MLU5725 | Accesorios para Vehículos |
| MLU1512 | Agro |
| MLU1403 | Alimentos y Bebidas |
| MLU107 | Animales y Mascotas |

## 🔧 Configuración

### Variables de Entorno

- `API_HOST`: Host de la API (default: 0.0.0.0)
- `API_PORT`: Puerto de la API (default: 8000)
- `REDIS_HOST`: Host de Redis (default: localhost)
- `REDIS_PORT`: Puerto de Redis (default: 6379)
- `MAX_CONCURRENT_TASKS`: Máximo de tareas concurrentes (default: 3)
- `DEFAULT_MAX_PRODUCTS`: Productos por defecto (default: 20)

### Archivos de Configuración

- `config.py`: Configuración principal de la API
- `models.py`: Modelos de datos Pydantic
- `queue_manager.py`: Gestión de colas con Redis
- `scraper_service.py`: Integración con el scraper existente

## 📊 Monitoreo

### Logs

Los logs se guardan en:
- API: `logs/api.log`
- Worker: `logs/worker.log`

### Métricas

- Estado de tareas (pending, processing, completed, failed)
- Estadísticas de la cola
- Tiempo de ejecución
- Tasa de éxito

## 🔄 Flujo de Trabajo

1. **Cliente envía solicitud** → `POST /scrape`
2. **API valida parámetros** → Categoría, página, cantidad
3. **Se crea tarea** → Se guarda en Redis con estado "pending"
4. **Se ejecuta scraping** → En background usando el scraper existente
5. **Se actualiza estado** → "processing" → "completed" o "failed"
6. **Cliente consulta estado** → `GET /tasks/{task_id}`

## 🚨 Manejo de Errores

- **Validación de entrada**: Categorías y parámetros
- **Reintentos automáticos**: Para fallos temporales
- **Logging detallado**: Para debugging y monitoreo
- **Estados de tarea**: Seguimiento completo del ciclo de vida

## 🔒 Seguridad

- Validación de entrada con Pydantic
- Rate limiting configurable
- Logs estructurados sin información sensible
- Manejo seguro de errores

## 📈 Escalabilidad

- Cola de tareas con Redis
- Procesamiento asíncrono
- Workers independientes
- Configuración de concurrencia

## 🧪 Testing

```bash
# Ejecutar tests
poetry run pytest

# Con coverage
poetry run pytest --cov=listener
```

## 📝 Ejemplos de Uso

### Python con requests

```python
import requests

# Crear tarea de scraping
response = requests.post("http://localhost:8000/scrape", json={
    "category": "MLU5725",
    "page": 1,
    "max_products": 20
})

task_id = response.json()["task_id"]

# Verificar estado
status = requests.get(f"http://localhost:8000/tasks/{task_id}")
print(status.json())
```

### cURL

```bash
# Crear tarea
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{"category": "MLU5725", "page": 1, "max_products": 20}'

# Verificar estado
curl "http://localhost:8000/tasks/{task_id}"
```

## 🤝 Contribución

1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la misma licencia que el proyecto principal.

## 🆘 Soporte

Para soporte técnico o preguntas:
- Crear un issue en el repositorio
- Revisar la documentación de la API en `/docs`
- Consultar los logs del sistema
