# Sistema de Scraping de Mercado Libre Uruguay

Sistema de scraping automatizado para Mercado Libre Uruguay con arquitectura publisher-subscriber usando RabbitMQ y persistencia en PostgreSQL (Supabase).

## 🏗️ Arquitectura

```
Publisher → RabbitMQ → Subscriber Listener → Scraper Service → PostgreSQL (Supabase)
    ↓           ↓              ↓              ↓              ↓
  API REST   Message Queue   Message      Browser         Database
  (Port 8001)                Consumer     Automation      Persistencia
```

## 🚀 Servicios

- **RabbitMQ**: Message broker (Puerto 15672 para management)
- **Publisher**: API para enviar tareas de scraping (Puerto 8001)
- **Subscriber**: API REST para consultar estado (Puerto 8002)
- **Subscriber Listener**: Worker que procesa mensajes de la cola
- **PostgreSQL (Supabase)**: Base de datos para persistir productos scrapeados

## 📋 Prerrequisitos

- Docker y Docker Compose
- Python 3.11+
- Poetry (para desarrollo local)
- Cuenta de Supabase (PostgreSQL)

## 🛠️ Instalación y Uso

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd test-scrapping
```

### 2. Configurar Base de Datos (PostgreSQL - Supabase)
```bash
# 1. Crear proyecto en Supabase
# 2. Ejecutar subscriber/database/products.sql en SQL Editor
# 3. Configurar variables de entorno en subscriber/.env
```

### 3. Levantar servicios

#### Para equipos de Mercado Libre (usando Poetry):
```bash
# 1. Levantar RabbitMQ
docker-compose up rabbitmq -d

# 2. En terminal 1 - Publisher
cd publisher
poetry install
poetry run start

# 3. En terminal 2 - Subscriber API
cd subscriber
poetry install
poetry run start-api

# 4. En terminal 3 - Subscriber Listener
cd subscriber
poetry run start-listener
```

#### Para equipos externos (usando Docker):
```bash
# Construir y levantar todos los servicios
docker-compose up -d

# O paso a paso
docker-compose up rabbitmq -d
docker-compose up publisher -d  
docker-compose up subscriber -d
```

### 4. Verificar estado de los servicios
```bash
# Verificar servicios
docker ps

# Verificar logs específicos
docker logs rabbitmq
docker logs publisher
docker logs subscriber
```

## 🧪 Testing

Ver documentación detallada en [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)

### Tests con Poetry (Recomendado para dev de MELI):
```bash
# Publisher
cd publisher && poetry run test

# Subscriber  
cd subscriber && poetry run pytest tests/ -v --cov=. --cov-report=term-missing
```

### Tests con Docker:
```bash
# Ejecutar tests desde containers
docker exec publisher poetry run pytest
docker exec subscriber poetry run pytest tests/ -v
```

## 🔧 Comandos Útiles

```bash
# Detener todos los servicios
docker-compose down

# Reconstruir servicios
docker-compose build --no-cache
docker-compose up -d

# Limpiar completamente
docker-compose down -v
docker system prune -f

# Ver logs en tiempo real
docker-compose logs -f [servicio]
```

## 📊 Monitoreo

### RabbitMQ Management
- URL: http://localhost:15672
- Usuario: `admin`
- Contraseña: `admin123`

### APIs
- Publisher: http://localhost:8001/docs
- Subscriber: http://localhost:8002/docs

## 🐛 Solución de Problemas

### El subscriber no recibe mensajes

1. **Verificar configuración de RabbitMQ**:
   - Exchange: `scraping_exchange`
   - Queue: `scraping_queue`
   - Routing Key: `scraping`

2. **Verificar que el listener esté corriendo**:
   ```bash
   make logs-listener
   ```

3. **Verificar conexión a RabbitMQ**:
   ```bash
   make test-rabbitmq
   ```

4. **Reiniciar servicios**:
   ```bash
   make restart
   ```

### Reconstruir completamente
```bash
make clean
make rebuild
```

## 📁 Estructura del Proyecto

```
├── adicionales/rabbitmq/     # Configuración de RabbitMQ
├── publisher/                 # Servicio publisher (API REST)
├── subscriber/               # Servicio subscriber + listener
│   ├── database/             # Configuración PostgreSQL/Supabase
│   ├── manager/              # Gestión de colas y workers
│   ├── scraper/              # Lógica de scraping
│   └── tests/                # Tests unitarios
├── validation_ia/            # Sistema de validación con IA
├── docs/                     # Documentación detallada
├── docker-compose.yml        # Orquestación de servicios
└── README.md                 # Este archivo
```

## 🔄 Flujo de Trabajo

1. **Publisher** recibe solicitud de scraping via API REST
2. **Publisher** envía mensaje a RabbitMQ
3. **Subscriber Listener** recibe mensaje de la cola
4. **Subscriber Listener** ejecuta scraping con Playwright/Camoufox
5. **Subscriber Listener** guarda productos en PostgreSQL (Supabase)
6. **Subscriber Listener** actualiza estado de la tarea
7. **Subscriber API** permite consultar estado y resultados

## 💾 Persistencia de Datos

### Base de Datos: PostgreSQL (Supabase)
Los productos scrapeados se almacenan en una tabla `products` con la siguiente estructura:

- **ID único**: UUID generado automáticamente
- **Metadatos**: Categoría, página, fecha de scraping
- **Información del producto**: Título, URL, vendedor, precios
- **Características**: Rating, reviews, stock, features (JSONB)
- **Auditoría**: Timestamps de creación y actualización

### Configuración de Supabase:
1. Crear proyecto en [Supabase](https://supabase.com)
2. Ejecutar [`subscriber/database/products.sql`](subscriber/database/products.sql) en SQL Editor
3. Configurar variables en `subscriber/.env`:
   ```bash
   SUPABASE_URL=https://tu-proyecto.supabase.co
   SUPABASE_KEY=tu-service-key
   ```

## 📝 Variables de Entorno

```bash
# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASS=admin123

# API
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

# Supabase (PostgreSQL)
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-service-key
```

## 📚 Documentación Detallada

Para información más completa, consulta la carpeta [`docs/`](docs/):

- 🚀 **[Guía de Despliegue](docs/DEPLOYMENT.md)**: Proceso paso a paso para poner en funcionamiento el sistema
- 🛠️ **[Guía de Desarrollo](docs/DEVELOPMENT.md)**: Información técnica para desarrolladores, tests y arquitectura
- 📖 **[Índice de Documentación](docs/README.md)**: Navegación y enlaces rápidos

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Ejecutar tests: `cd subscriber && poetry run pytest tests/ -v`
4. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
5. Push a la rama (`git push origin feature/AmazingFeature`)
6. Abrir Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.
