import os
from typing import Annotated, Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from app.config import apply_runtime_env
from app.models import Vendor, OutFmt
from app.formatters import to_kv, to_ini, clean_cuit
from app.api.uploads import Uploads

apply_runtime_env()

from app.services.extractor import extract_from_pdf  # noqa: E402


def create_app() -> FastAPI:
    app = FastAPI(title="Factura Extractor API v6", version="1.2.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    @app.post("/extract", response_model=None)
    async def extract_invoice(
        file: Annotated[UploadFile, File(...)],
        vendor: Annotated[Vendor, Form(...)],
        fmt: Annotated[OutFmt, Query(alias="format")] = OutFmt.json,
        use_ocr: Annotated[Optional[bool], Form()] = None,
    ) -> Response:
        filename = (file.filename or "").lower()
        if not filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF por el momento.")

        tmp_path = None
        try:
            tmp_path = Uploads.save_temp_pdf(file)
            if not tmp_path or os.path.getsize(tmp_path) == 0:
                raise HTTPException(status_code=400, detail="Archivo vacío.")

            minimal = extract_from_pdf(
                tmp_path,
                vendor_hint=vendor.value,
                cfg_path="vendors.yaml",
                use_ocr_hint=use_ocr,
            )

            if "cuit" in minimal:
                minimal["cuit"] = clean_cuit(minimal["cuit"])

            if fmt == OutFmt.json:
                return JSONResponse(minimal)
            if fmt == OutFmt.kv:
                return PlainTextResponse(content=to_kv(minimal), media_type="text/plain; charset=utf-8")
            if fmt == OutFmt.ini:
                return PlainTextResponse(content=to_ini(minimal), media_type="text/ini; charset=utf-8")
            return JSONResponse(minimal)
        finally:
            if tmp_path:
                Uploads.cleanup_temp_file(tmp_path)

    return app


app = create_app()
