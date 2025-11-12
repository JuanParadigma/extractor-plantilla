FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema, tesseract y python
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv \
    tesseract-ocr \
    tesseract-ocr-spa \
    tesseract-ocr-eng \
    libtesseract-dev \
    poppler-utils \
    libleptonica-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000
CMD ["python3", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "10000"]
