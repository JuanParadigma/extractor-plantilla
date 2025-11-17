from typing import Any, Dict, Optional

from app.services.fallback_totals import fallback_totals
from app.services.metadata_extractor import (
    detect_vendor_basic,
    detect_vendor_by_cuit,
    extract_header_common,
    extract_names_and_cuits,
)
from app.services.pdf_reader import PdfLineReader
from app.services.tax_normalizer import build_minimal_payload, validate_and_repair
from app.services.vendor_config import load_vendor_config
from app.vendors import REGISTRY


class InvoiceExtractor:
    """Coordinates PDF reading, vendor detection and normalization to minimal payload."""

    def __init__(self, reader: Optional[PdfLineReader] = None):
        self.reader = reader or PdfLineReader()

    @staticmethod
    def _build_base_out(header: Dict[str, Any], parties: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "proveedor": parties.get("proveedor"),
            "cuit_proveedor": parties.get("cuit_proveedor"),
            "cliente": parties.get("cliente"),
            "cuit_cliente": parties.get("cuit_cliente"),
            "tipo": header.get("tipo"),
            "numero": header.get("numero"),
            "fecha": header.get("fecha"),
            "cae": header.get("cae"),
            "cae_vto": header.get("cae_vto"),
            "subtotal": None,
            "iva": None,
            "iva_detalle": [],
            "percepciones_total": None,
            "percepciones_detalle": [],
            "total": None,
            "debug": {},
        }

    def extract(
        self,
        pdf_path: str,
        vendor_hint: Optional[str] = None,
        cfg_path: str = "vendors.yaml",
        use_ocr_hint: Optional[bool] = None,
    ) -> Dict[str, Any]:
        lines, used_ocr = self.reader.read(pdf_path, use_ocr_hint=use_ocr_hint)
        header = extract_header_common(lines)
        cfg = load_vendor_config(cfg_path)
        vendor_guess = (vendor_hint or "").upper() or detect_vendor_basic(lines, cfg["detect"]["names"]) or None
        parties_tuple = extract_names_and_cuits(lines, vendor_guess)
        parties = {
            "proveedor": parties_tuple[0],
            "cuit_proveedor": parties_tuple[1],
            "cliente": parties_tuple[2],
            "cuit_cliente": parties_tuple[3],
        }
        vendor = vendor_guess or detect_vendor_by_cuit(parties["cuit_proveedor"], cfg["detect"]["cuits"])

        out = self._build_base_out(header, parties)
        out["debug"] = {"vendor": vendor or "UNKNOWN", "lines_count": len(lines), "used_ocr": bool(used_ocr)}

        handler = REGISTRY.get((vendor or "").upper())
        if handler:
            handler(lines, out)
        else:
            fallback_totals(lines, out)

        validate_and_repair(out)
        minimal = build_minimal_payload(out, prefer_cuit="proveedor")
        minimal["ocr"] = bool(used_ocr)
        return minimal


def extract_from_pdf(
    pdf_path: str,
    vendor_hint: Optional[str] = None,
    cfg_path: str = "vendors.yaml",
    use_ocr_hint: Optional[bool] = None,
) -> Dict[str, Any]:
    """Compatibility wrapper used by API endpoint."""
    return InvoiceExtractor().extract(pdf_path, vendor_hint=vendor_hint, cfg_path=cfg_path, use_ocr_hint=use_ocr_hint)
