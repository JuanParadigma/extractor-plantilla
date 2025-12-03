FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS dev

COPY app ./app/

CMD ["uvicorn", "app.api.main:create_app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS prod

COPY app ./app/

CMD ["gunicorn", "app.api.main:create_app", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers=2", "--timeout=120"]