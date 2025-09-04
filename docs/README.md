# 📚 Documentación del Sistema de Scraping

Documentación completa del sistema de scraping automatizado de Mercado Libre Uruguay.

## 📖 Guías Disponibles

### 🚀 [Guía de Despliegue](DEPLOYMENT.md)
**Proceso paso a paso para poner en funcionamiento el sistema**

- ✅ **Para equipos de MELI**: Despliegue con Poetry (recomendado)
- 🐳 **Para equipos externos**: Despliegue con Docker  
- 🗄️ **Configuración de PostgreSQL** (Supabase)
- 🔧 **Solución de problemas** comunes
- 📊 **Verificación y monitoreo** post-despliegue

**¿Cuándo usarla?**: Primera vez configurando el sistema o problemas de despliegue.

---

### 🛠️ [Guía de Desarrollo](DEVELOPMENT.md)  
**Información técnica para desarrolladores**

- 🧪 **Tests unitarios** con Poetry y pytest
- 📦 **Gestión de dependencias** con Poetry
- 🗄️ **Esquemas de base de datos** PostgreSQL
- 🔍 **Debugging y monitoreo** de aplicaciones
- 🎯 **Mejores prácticas** de desarrollo
- 🔧 **Arquitectura del código** y patrones

**¿Cuándo usarla?**: Desarrollo de nuevas features, debugging o contribuciones al código.

---

## 🚀 Inicio Rápido

### 1. ¿Primera vez con el sistema?
👉 **Empieza con [DEPLOYMENT.md](DEPLOYMENT.md)**

### 2. ¿Ya tienes el sistema funcionando?
👉 **Consulta [DEVELOPMENT.md](DEVELOPMENT.md)** para desarrollo

### 3. ¿Problemas específicos?
- **Errores de despliegue** → [DEPLOYMENT.md - Solución de Problemas](DEPLOYMENT.md#🚨-solución-de-problemas)
- **Tests fallando** → [DEVELOPMENT.md - Tests Unitarios](DEVELOPMENT.md#🧪-tests-unitarios)
- **Configuración de DB** → [DEPLOYMENT.md - Base de Datos](DEPLOYMENT.md#🗄️-configuración-de-base-de-datos-obligatorio)

## 🏗️ Arquitectura del Sistema

```
Publisher → RabbitMQ → Subscriber Listener → Scraper Service → PostgreSQL (Supabase)
    ↓           ↓              ↓              ↓              ↓
  API REST   Message Queue   Message      Browser         Database
  (Port 8001)                Consumer     Automation      Persistencia
```

### Componentes principales:
- **Publisher** (Puerto 8001): API REST para crear tareas de scraping
- **RabbitMQ** (Puerto 15672): Message broker para comunicación asíncrona  
- **Subscriber API** (Puerto 8002): API REST para consultar estado de tareas
- **Subscriber Listener**: Worker que procesa mensajes y ejecuta scraping
- **PostgreSQL (Supabase)**: Base de datos para persistir productos

## 📋 Enlaces Rápidos

### APIs en desarrollo
- **Publisher API**: http://localhost:8001/docs
- **Subscriber API**: http://localhost:8002/docs
- **RabbitMQ Management**: http://localhost:15672

### Comandos frecuentes
```bash
# Despliegue Poetry (MELI)
docker-compose up rabbitmq -d
cd publisher && poetry run start
cd subscriber && poetry run start-api
cd subscriber && poetry run start-listener

# Despliegue Docker (Externo)  
docker-compose up -d

# Tests
cd publisher && poetry run test
cd subscriber && poetry run pytest tests/ -v

# Ver logs
docker logs -f subscriber-listener
docker logs -f publisher
```

## 🆘 Soporte Rápido

### Problemas más comunes:

1. **"RabbitMQ connection failed"**
   - Verificar: `docker ps | grep rabbitmq`
   - Solución: `docker-compose restart rabbitmq`

2. **"Supabase connection error"**  
   - Verificar: Variables en `subscriber/.env`
   - Solución: Revisar SUPABASE_URL y SUPABASE_KEY

3. **"Tests failing"**
   - Verificar: `poetry install --with dev`
   - Solución: Reinstalar dependencias de desarrollo

4. **"No products scraped"**
   - Verificar: `docker logs subscriber-listener`
   - Solución: Revisar rate limiting y configuración de scraping

### ¿Necesitas ayuda adicional?
- 📖 Revisa las guías detalladas arriba
- 🐛 Busca en los logs específicos del servicio
- 🔄 Intenta reiniciar el componente problemático

---

**💡 Tip**: Esta documentación está organizada para ser consultada de manera progresiva. Empieza por el despliegue y luego profundiza en el desarrollo según tus necesidades.
