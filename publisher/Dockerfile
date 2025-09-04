FROM python:3.11-slim

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

# Instalar Poetry y dependencias
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# Copiar código de la aplicación
COPY . .

# Exponer puerto para FastAPI
EXPOSE 8000

# Comando por defecto
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
