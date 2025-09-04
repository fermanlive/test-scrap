# 🤖 Sistema de Validación con IA Generativa

Sistema autónomo que valida la calidad y corrección de datos de scraping utilizando modelos de IA Generativa, asegurando que los datos sean completos, coherentes y precisos.

## 📁 Estructura del Proyecto

```
validation_ia/
├── main.py                    # 🚀 Entrypoint principal del sistema
├── pyproject.toml            # ⚙️  Configuración Poetry y dependencias
├── config.env.example       # 📝 Variables de entorno ejemplo
├── models/
│   └── models.py            # 📋 Modelos de datos (Product, etc.)
├── modules/
│   ├── database_connector.py # 🗄️  Conector a Supabase
│   └── openia.py            # 🧠 Validador con IA (OpenAI)
├── tests/                   # 🧪 Tests unitarios completos
└── docs/                    # 📚 Documentación detallada
```

## 🚀 Entrypoint

El sistema tiene **un único punto de entrada**:

```bash
# Usando Poetry (recomendado)
poetry run validate

# Usando Python directamente
python main.py
```

**Funcionalidad**: Valida productos desde la tabla `products` de Supabase usando IA Generativa.

## ⚡ Instalación Rápida

### 1. Crear ambiente y instalar dependencias
```bash
# Crear proyecto
poetry install

# Activar ambiente virtual
poetry shell
```

### 2. Configurar variables de entorno
```bash
cp config.env.example .env
# Editar .env con tus credenciales de Supabase y OpenAI
```

### 3. Crear base de datos
```bash
# Ejecutar docs/create_tables.sql en Supabase SQL Editor
```

### 4. Probar instalación
```bash
poetry run validate
```

## 🎮 Uso del Sistema

### Comando principal
```bash
poetry run validate
```

**Parámetros disponibles**:
- Sin parámetros: Valida todos los productos de Supabase
- `--category <nombre>`: Filtra por categoría específica
- `--page <número>`: Pagina los resultados (100 productos por página)

### Ejemplos de uso
```bash
# Validar todos los productos
poetry run validate

# Validar productos de una categoría
poetry run validate --category "Electronics"

# Validar página específica
poetry run validate --page 0

# Validar categoría específica en página 2
poetry run validate --category "Fashion" --page 2
```

## 📊 Registros del Sistema

### Base de datos Supabase
Los resultados se almacenan automáticamente en dos tablas:

1. **`validation_records`**: Logs individuales por producto
   - Estado de validación (Ok/issues)
   - Lista de problemas encontrados
   - Metadatos de confianza

2. **`executions`**: Registro de cada ejecución completa
   - Estado del proceso
   - Resumen de resultados
   - Métricas de rendimiento

### Logs en consola
El sistema muestra progreso en tiempo real:
- ✅ Productos validados correctamente
- ❌ Productos con problemas detectados
- 📊 Resumen final con estadísticas

## 🔄 Flujo del Sistema

El sistema sigue este flujo de trabajo:

1. **🚀 Inicialización**: Cargar configuración y conectar servicios
2. **📋 Obtención de datos**: Consultar productos desde Supabase
3. **🔍 Filtrado**: Aplicar filtros de categoría y paginación  
4. **🧠 Validación IA**: Procesar datos con modelo OpenAI
5. **💾 Almacenamiento**: Guardar resultados en base de datos
6. **📊 Reporte**: Mostrar resumen de ejecución

## 🎯 Casos de Uso

Este sistema está diseñado para:

### 🔍 Validación de Datos de Scraping
- **Completitud**: Verificar que no falten campos esenciales
- **Coherencia**: Validar lógica de precios y descuentos
- **Formato**: Confirmar URLs e imágenes válidas
- **Calidad**: Detectar valores atípicos o sospechosos

### 📊 Monitoreo de Calidad
- **Métricas en tiempo real**: Porcentaje de productos válidos
- **Tendencias**: Evolución de la calidad a lo largo del tiempo
- **Alertas**: Detección de problemas sistemáticos

### 🧠 Inteligencia Artificial
- **Validación avanzada**: Más allá de reglas simples
- **Sugerencias**: Recomendaciones para mejorar datos
- **Puntuación de confianza**: Nivel de certeza en la validación

## 🛠️ Configuración

### Variables de entorno requeridas
```bash
# Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_KEY=tu-service-key

# OpenAI
OPENAI_API_KEY=tu-openai-api-key
```

### Criterios de validación
El sistema verifica automáticamente:
- ✅ Nombres de productos no vacíos
- ✅ Precios positivos y coherentes
- ✅ URLs con formato válido
- ✅ Descuentos calculados correctamente
- ✅ Rangos de rating válidos (0-5)

## 🧪 Tests Unitarios

### Ejecutar todos los tests
```bash
poetry run python -m pytest --cov=tests/ --cov-report=term-missing
```

### Tests específicos
```bash
# Tests de módulos específicos
poetry run python -m pytest tests/modules/test_openia.py

# Tests con marcadores
poetry run python -m pytest -m unit
poetry run python -m pytest -m "not slow"
```

### Cobertura de tests
Los tests cubren:
- 🧠 Validador de IA (OpenAI)
- 🗄️ Conector de base de datos
- 📋 Script principal
- 🔧 Casos edge y manejo de errores

## 📚 Documentación Adicional

Para información más detallada, consulta la carpeta `docs/`:
- 🔧 **Guía de desarrollo**: Configuración avanzada y arquitectura
- 🗄️ **Esquemas de base de datos**: Estructura completa de tablas
- 🧪 **Guía de testing**: Información detallada sobre pruebas

## 🤝 Contribución

1. Fork del proyecto
2. Crear rama para tu feature
3. Ejecutar tests: `poetry run python -m pytest`
4. Commit y push
5. Crear Pull Request

## 📞 Soporte

- 📖 Documentación completa en `docs/`
- 🐛 Reportar issues en GitHub
- 🧪 Ejecutar tests para verificar configuración