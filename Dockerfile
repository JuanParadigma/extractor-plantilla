# Usa Debian completo, no slim
FROM python:3.13-bullseye

# Evita interacción en apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Instalar Tesseract, Poppler y dependencias necesarias
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libtesseract-dev \
    poppler-utils \
    libleptonica-dev \
    && rm -rf /var/lib/apt/lists/*

# Comprobación del binario (opcional pero útil para debug)
RUN which tesseract && tesseract --version

# Establecer directorio de trabajo
WORKDIR /app

# Copiar los archivos del proyecto
COPY . .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto para Uvicorn
EXPOSE 8000

# Comando de arranque
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
