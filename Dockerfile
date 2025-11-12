FROM python:3.11-bullseye


ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libtesseract-dev \
    poppler-utils \
    libleptonica-dev \
    && rm -rf /var/lib/apt/lists/*

# Verificamos que realmente se instaló
RUN which tesseract && tesseract --version

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
