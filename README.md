# Extractor de Facturas (MVP)

Servicio FastAPI que recibe PDFs de facturas argentinas, detecta proveedor/cliente y normaliza los importes e identificadores a un payload minimo listo para la API de integracion.

## Stack

- Python 3.11+ (recomendado)
- FastAPI + Uvicorn (`app/api/main.py`, `server.py`)
- Pipelines de lectura PDF/OCR (`app/services/pdf_reader.py`) con PyMuPDF, pdf2image, Pillow y pytesseract
- Normalizador fiscal (`app/services/extractor.py`, `tax_normalizer.py`) y handlers especificos por proveedor (`app/vendors`, `vendors.yaml`)
- Dockerfile y `render.yaml` listos para despliegue en Render.com

## Instalacion

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Dependencias nativas: Tesseract OCR debe estar instalado y expuesto en `PATH`. `app/config.py` anade rutas comunes para Linux/Render/Windows, pero puedes forzar `TESSDATA_PREFIX` y `PATH` segun tu entorno.

## Uso local

1. Crear archivo `vendors.yaml` (ya existe un ejemplo) con los proveedores soportados y reglas de deteccion.
2. Ejecutar el servidor:

```bash
uvicorn server:app --reload --port 8000
```

3. Probar la API:

```bash
curl -X POST "http://localhost:8000/extract?format=json" \
  -F "vendor=DESCONOCIDO" \
  -F "use_ocr=true" \
  -F "file=@/ruta/a/factura.pdf"
```

Respuestas posibles (`OutFmt` en `app/models.py`):
- `format=json` (default) -> payload JSON minimal
- `format=kv` -> `key=value` por linea (`app/formatters.py`)
- `format=ini` -> bloque estilo `.ini`

Endpoints:
- `GET /health` -> `{"status":"ok"}`
- `POST /extract` -> procesa el PDF (solo PDFs, validado en `app/api/main.py`)

## Flujo de extraccion

1. `PdfLineReader.read` abre el PDF; si es necesario aplica OCR.
2. `metadata_extractor.extract_header_common` y `extract_names_and_cuits` generan cabecera y partes.
3. `detect_vendor_basic` (por nombre) o `detect_vendor_by_cuit` (por CUIT) decide el handler apropiado. Tambien se puede forzar con `vendor_hint` (param Form `vendor`).
4. `_build_base_out` crea un esqueleto con proveedor, cliente, numero, CAE y placeholders para montos.
5. Handler especifico (`app/vendors/REGISTRY`) llena importes y tributos; si no existe se usa `fallback_totals`.
6. `validate_and_repair` y `build_minimal_payload` consolidan la salida y retornan el resultado con `ocr=True/False`.

El wrapper `extract_from_pdf` en `app/services/extractor.py` se usa tanto desde la API como desde scripts standalone.

## Configuracion de proveedores

- `vendors.yaml` define claves (`detect.names` + `detect.cuits`) utilizadas por `load_vendor_config`.
- Para sumar un proveedor:
  1. Registrar su clave en `vendors.yaml`.
  2. Implementar handler en `app/vendors/<proveedor>.py` y exportarlo en `REGISTRY`.
  3. Ajustar tests/manuales para cubrir el PDF correspondiente.

## Despliegue

- **Docker**: `docker build -t extractor .` y luego `docker run -p 8000:8000 extractor`.
- **Render**: usar `render.yaml` para aprovisionar un servicio web; asegurate de exponer `/usr/bin/tesseract` o instalarlo en el build command.

## Troubleshooting

- _"Archivo vacio"_: la API devuelve 400 si `Uploads.save_temp_pdf` no logra persistir el archivo.
- _OCR lento_: desactivar `use_ocr` para PDFs que ya contienen texto seleccionable; la API acepta `true/false/null`.
- _CUITs mal formateados_: los CUIT se normalizan con `clean_cuit`, pero requieren ser detectados en `metadata_extractor`.

## Proximos pasos sugeridos

- Anadir pruebas unitarias/smoke para `InvoiceExtractor`.
- Documentar nuevos proveedores directamente en `vendors.yaml` a medida que se agreguen.
