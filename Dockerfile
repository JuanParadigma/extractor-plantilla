# Imagen base con Python y acceso a apt-get
FROM python:3.13-slim

# Instalar dependencias del sistema necesarias para Tesseract y Poppler
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos del proyecto
COPY . .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto (Render asigna automáticamente $PORT)
EXPOSE 8000

# Comando de inicio del servidor FastAPI
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]