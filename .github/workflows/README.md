# 🧪 GitHub Actions - Pruebas Unitarias

## 📊 Resumen

Este workflow ejecuta pruebas unitarias automatizadas para los tres módulos principales del proyecto con cobertura mínima del 80%.

## 🎯 Características Principales

### ✅ **Módulos Cubiertos**
- **Publisher**: Servicio FastAPI con RabbitMQ
- **Subscriber**: Scraper con Playwright y RabbitMQ  
- **Validation IA**: Sistema de validación con OpenAI

### ⚡ **Triggers**
- Se activa en **Pull Requests** hacia `main` o `develop`
- Solo cuando hay cambios en:
  - `publisher/**`
  - `subscriber/**` 
  - `validation_ia/**`
  - `.github/workflows/test.yml`

### 🔒 **Aislamiento de Entornos**
- Cada módulo ejecuta en job independiente
- Virtual environments separados con Poetry
- Cachés específicos por módulo
- Working directories aislados

### 📈 **Cobertura de Código**
- **Mínimo requerido**: 80% por módulo
- Reportes XML para Codecov
- Falla si no alcanza el mínimo
- Comentarios automáticos en PR con resumen

## 🏗️ **Configuración por Módulo**

### 📦 **Publisher Job**
```yaml
- Python 3.10
- Poetry para dependencias
- FastAPI + Pika (RabbitMQ)
- Pruebas básicas sin servicios externos
```

### 🕷️ **Subscriber Job**  
```yaml
- Python 3.10 + dependencias del sistema
- Servicio RabbitMQ (test:test@localhost:5672)
- Playwright con Chromium
- Exclusión de tests lentos (-m "not slow")
- Variables mockeadas para entorno
```

### 🤖 **Validation IA Job**
```yaml
- Python 3.10
- Variables de OpenAI y Supabase mockeadas
- Exclusión de tests reales (-m "not ai and not database")
- Solo pruebas unitarias aisladas
```

## 📋 **Reportes Generados**

### 📊 **Cobertura**
- Reportes XML por módulo
- Subida automática a Codecov
- Flags específicos: `publisher`, `subscriber`, `validation-ia`

### 📝 **Resultados de Pruebas**
- JUnit XML para cada módulo
- Test Reporter con visualización detallada
- Comentarios automáticos en PR

### 💬 **Comentario de Resumen**
El workflow genera un comentario automático en el PR con:
- Estado de cada módulo (✅/❌)
- Cobertura mínima requerida
- Criterios de calidad aplicados
- Mensaje de éxito o fallo general

## 🚀 **Optimizaciones Implementadas**

### ⚡ **Performance**
- Caché de dependencias Poetry
- Exclusión de tests lentos en CI
- Solo instalación de browsers necesarios (Chromium)

### 🔒 **Seguridad**
- Mocks para APIs externas (OpenAI, Supabase)
- Variables de entorno controladas
- Sin credenciales reales en CI

### 🎯 **Confiabilidad**
- Health checks para servicios
- Timeouts configurados
- Manejo de errores por job independiente

## 🔧 **Mantenimiento**

### 📦 **Dependencias**
Las dependencias se actualizan automáticamente desde `poetry.lock` de cada módulo.

### 🏷️ **Marcadores de Pruebas**
- `slow`: Tests excluidos en CI
- `ai`: Tests que requieren OpenAI real
- `database`: Tests con base de datos real
- `integration`: Tests de integración completa

### 📊 **Métricas**
- Tiempo de ejecución típico: 5-8 minutos
- Cobertura objetivo: ≥80% por módulo
- Tolerancia a fallos: Job independiente por módulo

---

## 🆘 **Solución de Problemas**

### ❌ **Fallo de Cobertura**
Si un módulo no alcanza 80%:
1. Revisar el reporte detallado en el comentario del PR
2. Agregar tests para líneas no cubiertas
3. Verificar que los tests estén correctamente marcados

### 🐛 **Fallo de Dependencias**
Si fallan las instalaciones:
1. Verificar `poetry.lock` actualizado
2. Revisar compatibilidad de versiones
3. Limpiar caché si es necesario

### 🔧 **Servicios No Disponibles**
Si RabbitMQ falla en subscriber:
1. Health checks automáticos detectan el problema
2. Revisar configuración de puertos
3. Verificar credenciales de test
