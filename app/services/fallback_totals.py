"""Fallback strategies to derive subtotal/iva/percepciones/total when no vendor handler is found."""

from typing import Any, Dict, List, Optional

from app.services.text_utils import first_amount_forward

_OCR_KEYWORD_FIXES = str.maketrans({"0": "O", "1": "I", "5": "S", "6": "G", "8": "B", "|": "I", "@": "A"})


def _normalize_ocr_keyword(text: str) -> str:
    return text.translate(_OCR_KEYWORD_FIXES) if text else text


def fallback_totals(lines: List[str], out: Dict[str, Any]) -> None:
    start = max(0, len(lines) - 150)
    tail = lines[start:]
    sub = iva = perc = tot = None
    iva_items: List[Dict[str, Optional[float]]] = []
    perc_items: List[Dict[str, Optional[float]]] = []

    for i, line in enumerate(tail):
        up_key = _normalize_ocr_keyword(line.upper())
        if sub is None and "SUBTOTAL" in up_key:
            v = first_amount_forward(tail, i)
            if v is not None:
                sub = v
        if "IVA" in up_key:
            v = first_amount_forward(tail, i)
            if v is not None:
                iva = (iva or 0.0) + v
                iva_items.append({"alicuota": None, "monto": v})
        if any(k in up_key for k in ["PERC", "PERCEP", "IIBB", "INGRESOS BRUTOS", "ARBA", "AGIP"]):
            v = first_amount_forward(tail, i)
            if v is not None:
                perc = (perc or 0.0) + v
                perc_items.append({"desc": line, "monto": v})
        if "TOTAL" in up_key:
            v = first_amount_forward(tail, i)
            if v is not None:
                tot = v
    out["subtotal"] = sub
    out["iva"] = iva
    out["iva_detalle"] = iva_items
    out["percepciones_total"] = perc
    out["percepciones_detalle"] = perc_items
    out["total"] = tot
    if out["total"] is None and (sub is not None):
        out["total"] = round((sub or 0.0) + (iva or 0.0) + (perc or 0.0), 2)

