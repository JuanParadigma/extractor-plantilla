# Imagen base con Tesseract 4 y Python ya configurado
FROM tesseractshadow/tesseract4re:4.0.0

# Instalamos Python y dependencias
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv poppler-utils && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Verificar instalación
RUN which tesseract && tesseract --version

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
