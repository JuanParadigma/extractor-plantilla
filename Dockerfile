# Imagen base liviana con Python y Debian
FROM python:3.13-slim

# Evita prompts interactivos de apt
ENV DEBIAN_FRONTEND=noninteractive

# Instala dependencias del sistema necesarias para Tesseract y Poppler
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-spa \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copia el código y requirements
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Variables de entorno para pytesseract
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata
ENV PATH="/usr/bin:$PATH"

# Expone el puerto para Render
EXPOSE 8000

# Comando de arranque
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
