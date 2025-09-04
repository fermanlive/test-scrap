FROM python:3.10-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y \
    google-chrome-stable \
    fonts-ipafont-gothic \
    fonts-wqy-zenhei \
    fonts-thai-tlwg \
    fonts-kacst \
    fonts-freefont-ttf \
    libxss1 \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY pyproject.toml poetry.lock ./

# Instalar Poetry
RUN pip install poetry

# Configurar Poetry para no crear entorno virtual
RUN poetry config virtualenvs.create false

# Instalar dependencias
RUN poetry install --only=main

# Copiar código fuente
COPY . .

# Instalar Playwright
RUN playwright install chromium
RUN playwright install-deps

# Crear directorios necesarios
RUN mkdir -p logs output

# Exponer puerto
EXPOSE 8000

# Comando por defecto (API)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

