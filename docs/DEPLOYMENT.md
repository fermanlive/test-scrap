# 🚀 Guía de Despliegue - Sistema de Scraping Mercado Libre Uruguay

Esta guía detalla el proceso paso a paso para desplegar el sistema de scraping en diferentes entornos.

## 📋 Prerrequisitos

### Software requerido
- **Docker** y **Docker Compose** (v2.0+)
- **Python 3.11+** (para desarrollo local)
- **Poetry** (para equipos de Mercado Libre)
- **Git** para clonación del repositorio

### Servicios externos
- **Cuenta de Supabase** (PostgreSQL como servicio)
- **Acceso a red** para scraping de Mercado Libre Uruguay

## 🗄️ Configuración de Base de Datos (OBLIGATORIO)

### 1. Crear proyecto en Supabase
1. Ir a [supabase.com](https://supabase.com)
2. Crear nuevo proyecto
3. Anotar la **URL del proyecto** y **Service Key**

### 2. Crear tabla de productos
1. Ir al **SQL Editor** en Supabase
2. Ejecutar el siguiente script:

```sql
-- Crear tabla products
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

-- Crear índices para optimización
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_page ON products(page);
CREATE INDEX idx_products_scraped_at ON products(scraped_at);
CREATE INDEX idx_products_features_gin ON products USING GIN (features);
CREATE INDEX idx_products_images_gin ON products USING GIN (images);
```

### 3. Configurar variables de entorno
Crear archivo `subscriber/.env`:
```bash
# Supabase Configuration
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-service-key-aqui

# RabbitMQ Configuration  
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASS=admin123

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

# Scraping Configuration
MAX_WORKERS=3
BROWSER_HEADLESS=true
RATE_LIMIT_DELAY=2.0
```

## 🏢 Opción A: Despliegue para Equipos de Mercado Libre (Poetry)

**Recomendado para desarrollo y testing interno**

### Paso 1: Preparación del entorno
```bash
# Clonar repositorio
git clone <repository-url>
cd test-scrapping

# Verificar Poetry instalado
poetry --version
# Si no está instalado: curl -sSL https://install.python-poetry.org | python3 -
```

### Paso 2: Desplegar RabbitMQ (Primer servicio)
```bash
# Levantar solo RabbitMQ con Docker
docker-compose up rabbitmq -d

# Verificar que esté corriendo
docker ps | grep rabbitmq
docker logs rabbitmq

# El management UI estará en: http://localhost:15672
# Usuario: admin, Contraseña: admin123
```

### Paso 3: Desplegar Publisher (Segundo servicio)
```bash
# Terminal 1 - Publisher
cd publisher

# Instalar dependencias
poetry install

# Activar entorno virtual
poetry shell

# Ejecutar servicio
poetry run start
# O alternativamente: poetry run uvicorn main:app --host 0.0.0.0 --port 8000

# El Publisher API estará en: http://localhost:8001
```

### Paso 4: Desplegar Subscriber (Último servicio)
```bash
# Terminal 2 - Subscriber API
cd subscriber

# Instalar dependencias
poetry install

# Verificar archivo .env configurado
cat .env

# Activar entorno virtual  
poetry shell

# Ejecutar API
poetry run start-api
# O alternativamente: poetry run uvicorn main:app --host 0.0.0.0 --port 8000

# El Subscriber API estará en: http://localhost:8002
```

### Paso 5: Iniciar Listener (Componente crítico)
```bash
# Terminal 3 - Subscriber Listener
cd subscriber

# Activar entorno virtual
poetry shell

# Iniciar listener de mensajes
poetry run start-listener
# O alternativamente: poetry run python message_listener.py

# Este proceso debe mantenerse corriendo para procesar tareas
```

### Verificación del despliegue Poetry
```bash
# Verificar todos los servicios
curl http://localhost:8001/docs  # Publisher docs
curl http://localhost:8002/docs  # Subscriber docs
curl http://localhost:8001/      # Publisher health
curl http://localhost:8002/health # Subscriber health

# Verificar RabbitMQ management
open http://localhost:15672
```

## 🐳 Opción B: Despliegue con Docker (Equipos Externos)

**Recomendado para equipos fuera de Mercado Libre o entornos de producción**

### Paso 1: Preparación
```bash
# Clonar repositorio
git clone <repository-url>
cd test-scrapping

# Verificar Docker
docker --version
docker-compose --version
```

### Paso 2: Configuración de variables
```bash
# Configurar Supabase en subscriber/.env (ver sección anterior)
# Verificar archivo env.docker si es necesario
cat env.docker
```

### Paso 3: Despliegue completo automatizado
```bash
# Opción más simple - Todo de una vez
docker-compose up -d

# Verificar todos los servicios levantados
docker ps
```

### Paso 4: Despliegue paso a paso (recomendado)
```bash
# 1. Primero RabbitMQ (base del sistema)
docker-compose up rabbitmq -d

# Esperar que esté listo (30-60 segundos)
docker logs rabbitmq

# 2. Luego Publisher (depende de RabbitMQ)
docker-compose up publisher -d

# Verificar Publisher
docker logs publisher

# 3. Después Subscriber API (depende de RabbitMQ)
docker-compose up subscriber -d

# Verificar Subscriber
docker logs subscriber

# 4. Finalmente Subscriber Listener (procesamiento)
docker-compose up subscriber-listener -d

# Verificar Listener
docker logs subscriber-listener
```

### Verificación del despliegue Docker
```bash
# Ver estado de todos los contenedores
docker ps

# Ver logs en tiempo real
docker-compose logs -f

# Ver logs específicos
docker logs -f rabbitmq
docker logs -f publisher  
docker logs -f subscriber
docker logs -f subscriber-listener

# Verificar APIs
curl http://localhost:8001/docs  # Publisher
curl http://localhost:8002/docs  # Subscriber
```

## ✅ Verificación del Sistema Completo

### 1. Health Check de servicios
```bash
# Publisher health
curl http://localhost:8001/

# Subscriber health  
curl http://localhost:8002/health

# RabbitMQ management
open http://localhost:15672
```

### 2. Test de conectividad RabbitMQ
```bash
# Verificar colas en RabbitMQ Management UI
# Debe mostrar exchange: scraping_exchange
# Debe mostrar queue: scraping_queue
```

### 3. Test de base de datos
```bash
# Si usas Poetry (desde subscriber/)
poetry run python -c "
from database.connectors.database_connector import DatabaseConnector
db = DatabaseConnector()
print('✅ Conexión a Supabase exitosa')
"

# Si usas Docker
docker exec subscriber python -c "
from database.connectors.database_connector import DatabaseConnector
db = DatabaseConnector()
print('✅ Conexión a Supabase exitosa')
"
```

### 4. Test de scraping completo
```bash
# Crear tarea de prueba
curl -X POST "http://localhost:8002/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "electronics",
    "page": 0,
    "max_products": 10
  }'

# Verificar tarea creada (usar el task_id devuelto)
curl "http://localhost:8002/tasks/{task_id}"

# Verificar en Supabase que se guardaron productos
```

## 🔧 Comandos de Gestión

### Comandos comunes Docker
```bash
# Ver estado
docker ps
docker-compose ps

# Ver logs
docker-compose logs -f [servicio]

# Reiniciar servicio específico
docker-compose restart [servicio]

# Detener todo
docker-compose down

# Detener y limpiar volúmenes
docker-compose down -v

# Reconstruir imágenes
docker-compose build --no-cache
docker-compose up -d
```

### Comandos comunes Poetry
```bash
# Reiniciar servicios (Ctrl+C y luego)
cd publisher && poetry run start
cd subscriber && poetry run start-api  
cd subscriber && poetry run start-listener

# Ver logs en archivos
tail -f subscriber/logs/api.log
tail -f publisher/logs/api.log

# Reinstalar dependencias
poetry install --with dev
```

## 🚨 Solución de Problemas

### Problema: RabbitMQ no inicia
```bash
# Verificar puerto no está ocupado
lsof -i :5672
lsof -i :15672

# Limpiar volúmenes y reiniciar
docker-compose down -v
docker-compose up rabbitmq -d
```

### Problema: Subscriber no se conecta a RabbitMQ
```bash
# Verificar variables de entorno
cat subscriber/.env | grep RABBITMQ

# Verificar que RabbitMQ esté accesible
docker logs rabbitmq | grep "Server startup complete"

# Reiniciar subscriber
docker-compose restart subscriber subscriber-listener
```

### Problema: Error de conexión a Supabase
```bash
# Verificar credenciales
cat subscriber/.env | grep SUPABASE

# Test manual de conexión
docker exec subscriber python -c "
import os
print('URL:', os.getenv('SUPABASE_URL'))
print('KEY:', os.getenv('SUPABASE_KEY')[:10] + '...')
"
```

### Problema: Scraping falla
```bash
# Verificar logs del listener
docker logs subscriber-listener | tail -50

# Verificar si Playwright está instalado
docker exec subscriber-listener playwright --version

# Reiniciar listener
docker-compose restart subscriber-listener
```

### Problema: Tests fallan
```bash
# Poetry - verificar dependencias
cd publisher && poetry install --with dev
cd subscriber && poetry install --with dev

# Docker - reconstruir con dependencias de test
docker-compose build --no-cache
```

## 📊 Monitoreo Post-Despliegue

### URLs importantes
- **Publisher API**: http://localhost:8001/docs
- **Subscriber API**: http://localhost:8002/docs  
- **RabbitMQ Management**: http://localhost:15672
- **Supabase Dashboard**: https://app.supabase.com

### Métricas a monitorear
1. **RabbitMQ**: Cola `scraping_queue` debe procesar mensajes
2. **Supabase**: Tabla `products` debe recibir datos
3. **APIs**: Health endpoints deben retornar OK
4. **Logs**: Sin errores críticos en los servicios

### Logs importantes
```bash
# Logs que indican funcionamiento correcto
docker logs publisher | grep "Uvicorn running"
docker logs subscriber | grep "Uvicorn running"  
docker logs subscriber-listener | grep "Iniciando escucha"
docker logs rabbitmq | grep "Server startup complete"
```

## 🔄 Flujo de Trabajo Post-Despliegue

### 1. Crear tarea de scraping
```bash
curl -X POST "http://localhost:8002/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "electronics",
    "page": 0,
    "max_products": 50
  }'
```

### 2. Monitorear progreso
```bash
# Ver tasks en progreso
curl "http://localhost:8002/tasks"

# Ver task específica
curl "http://localhost:8002/tasks/{task_id}"

# Ver datos en Supabase
# SELECT * FROM products ORDER BY created_at_audit DESC LIMIT 10;
```

### 3. Mantenimiento regular
```bash
# Limpiar logs antiguos (si aplica)
find . -name "*.log" -mtime +7 -delete

# Restart periódico de listeners (recomendado)
docker-compose restart subscriber-listener

# Backup de datos importantes en Supabase
```

## 🎯 Recomendaciones de Producción

### Para equipos de MELI
1. **Usar Poetry** para mayor control de dependencias
2. **Monitorear logs** activamente durante scraping
3. **Rate limiting** adecuado para no ser bloqueados
4. **Backup regular** de datos en Supabase

### Para equipos externos
1. **Docker en producción** es más estable
2. **Configurar restart policies** en docker-compose
3. **Usar reverse proxy** (nginx) si es necesario
4. **Monitoreo con herramientas externas** (Grafana, etc.)

Esta guía cubre los escenarios más comunes de despliegue. Para desarrollo avanzado, consulta [`DEVELOPMENT.md`](DEVELOPMENT.md).
