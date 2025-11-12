# Imagen base con Tesseract ya instalado
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Instalar dependencias del sistema y Python
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    tesseract-ocr \
    tesseract-ocr-spa \
    poppler-utils \
    libtesseract-dev \
    libleptonica-dev \
    && rm -rf /var/lib/apt/lists/*

# Verificamos Tesseract
RUN which tesseract && tesseract --version

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]