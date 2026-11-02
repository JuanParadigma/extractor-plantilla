# handlers_prometeon.py
import re
from typing import List, Dict, Any, Optional

from app.vendors.registry import register
from app.services.text_utils import parse_number_smart

# Matches numbers in European format: "8.510.392,00", "421.229,93", "20.475,00"
_RE_NUM = re.compile(r'-?\d[\d,.]*\d|-?\d')

_PERCEP_KEYS = (
    'IIBB', 'PERC', 'RG DGI', 'DN B70',
    'NEUQUEN', 'RÍO NEG', 'RIO NEG', 'IB CONV', 'IB BA',
)


def _normalize_ocr_spaces(text: str) -> str:
    """Fix OCR artifact spaces inside numbers: '75.791 .023,33' → '75.791.023,33'"""
    return re.sub(r'(\d)\s+([,.])', r'\1\2', text)


def _first_amount_after(line: str, keyword: str) -> Optional[float]:
    """Extract first monetary amount (with at least one separator) after keyword on line."""
    norm = _normalize_ocr_spaces(line)
    idx = norm.upper().find(keyword.upper())
    if idx == -1:
        return None
    after = norm[idx + len(keyword):]
    for m in _RE_NUM.finditer(after):
        raw = m.group(0)
        if ',' not in raw and '.' not in raw:
            continue
        v = parse_number_smart(raw)
        if v is not None and v > 0:
            return v
    return None


def _last_amount(line: str) -> Optional[float]:
    """Last monetary amount on line (must have at least one separator)."""
    norm = _normalize_ocr_spaces(line)
    for m in reversed(list(_RE_NUM.finditer(norm))):
        raw = m.group(0)
        if ',' not in raw and '.' not in raw:
            continue
        v = parse_number_smart(raw)
        if v is not None and v > 0:
            return v
    return None


@register("PROMETEON")
def extract_totals_prometeon(lines: List[str], out: Dict[str, Any]) -> None:
    # Prometeon format (last page, European numbers with . thousands and , decimal):
    #   IMPORTE NETO [subtotal]      ← total net before taxes
    #   IVA [rate]% [iva_amount]     ← rate and amount on same line
    #   [percep label] [rate]% [amount]   ← optional, label+rate+amount on same line
    #   TOTAL PESOS [total]
    start = max(0, len(lines) - 60)
    tail = lines[start:]

    subtotal = iva_total = percep_total = total = None
    iva_items: list = []
    percep_items: list = []

    for line in tail:
        up = line.upper()

        if 'IMPORTE NETO' in up and subtotal is None:
            v = _first_amount_after(line, 'IMPORTE NETO')
            if v is not None:
                subtotal = v

        elif re.search(r'\bIVA\b', up) and 'RESPONSABLE' not in up:
            mrate = re.search(r'(\d{1,2}(?:[.,]\d{1,2})?)\s*%', line)
            alic = mrate.group(1).replace(',', '.') if mrate else None
            v = _last_amount(line)
            if v is not None:
                iva_total = (iva_total or 0.0) + v
                iva_items.append({"alicuota": alic, "monto": v})

        elif any(k in up for k in _PERCEP_KEYS):
            v = _last_amount(line)
            if v is not None:
                percep_total = (percep_total or 0.0) + v
                percep_items.append({"desc": line.strip(), "monto": v})

        elif 'TOTAL PESOS' in up:
            v = _first_amount_after(line, 'TOTAL PESOS')
            if v is not None:
                total = v

    out["subtotal"] = subtotal
    out["iva"] = round(iva_total, 2) if iva_total is not None else None
    out["iva_detalle"] = iva_items
    out["percepciones_total"] = round(percep_total, 2) if percep_total is not None else None
    out["percepciones_detalle"] = percep_items
    out["total"] = total

    if out["total"] is None and subtotal is not None:
        out["total"] = round(subtotal + (out["iva"] or 0.0) + (out["percepciones_total"] or 0.0), 2)
