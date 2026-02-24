# Usamos una imagen liviana de Python
FROM python:3.12-slim

# Evita que Python genere archivos .pyc y permite ver logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalamos dependencias del sistema necesarias para MariaDB
RUN apt-get update && apt-get install -y \
    gcc \
    libmariadb-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copiamos los requerimientos e instalamos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código del proyecto
COPY . .

# Creamos la carpeta de uploads por si acaso
RUN mkdir -p uploads

# Exponemos el puerto del servidor SCEE
EXPOSE 5000

# El comando por defecto (se sobreescribirá en el compose para el worker)
CMD ["python", "src/main_server.py"]