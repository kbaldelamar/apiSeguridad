FROM python:3.11.7-slim@sha256:d48a0a16bba7d81d08b3b6b82fea47591ca7096d8fc091fcd11a0a2c1f7a9fa4

# Establecer un usuario no root
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Instalar dependencias del sistema necesarias para MariaDB
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmariadb-dev \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requerimientos
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Cambiar permisos
RUN chown -R appuser:appuser /app

# Cambiar al usuario no root
USER appuser

# Exponer puerto para la API
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 