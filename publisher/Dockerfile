FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY pyproject.toml poetry.lock ./

# Instalar Poetry
RUN pip install poetry

# Configurar Poetry para no crear entorno virtual
RUN poetry config virtualenvs.create false

# Instalar dependencias
RUN poetry install --no-root 

# Copiar código de la aplicación
COPY . .

# Exponer puerto para FastAPI
EXPOSE 8002

# Comando por defecto
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
