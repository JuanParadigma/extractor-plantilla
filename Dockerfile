FROM ghcr.io/tesseract-ocr/tesseract:5.4.0

# Instalar Python y dependencias
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv \
    poppler-utils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000
CMD ["python3", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "10000"]
