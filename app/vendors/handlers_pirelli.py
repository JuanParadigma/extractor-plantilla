# handlers_pirelli.py
import re
from typing import List, Dict, Any, Optional

from app.vendors.registry import register
from app.services.text_utils import parse_number_smart

# Matches any number including non-standard thousands like "40387,958.64"
_RE_NUM = re.compile(r'-?\d[\d,.]*\d|-?\d')

_PERCEP_KEYS = (
    'IIBB', 'PERC', 'RG DGI', 'DN B70',
    'NEUQUEN', 'RÍO NEG', 'RIO NEG', 'IB CONV', 'IB BA',
)


def _last_amount(line: str) -> Optional[float]:
    """Return the last monetary amount on line. Requires a decimal point (monetary amounts
    always have 2 decimal places in Argentine invoices); skips CAE/barcode digit strings.
    Normalizes OCR-introduced spaces inside numbers (e.g. '17591 ,280.68' → '17591,280.68')."""
    normalized = re.sub(r'(\d)\s+([,.])', r'\1\2', line)
    for m in reversed(list(_RE_NUM.finditer(normalized))):
        raw = m.group(0)
        if '.' not in raw:
            continue
        v = parse_number_smart(raw)
        if v is not None and v != 0.0:
            return v
    return None


@register("PIRELLI")
def extract_totals_pirelli(lines: List[str], out: Dict[str, Any]) -> None:
    # Pirelli OCR collapses each tax section onto a single line:
    #   SUBTOTAL [value]
    #   [label] [rate]% [base] [amount]   <- we want the LAST number
    #   [...] TOTAL FACTURA [total] [optional CAE number]
    start = max(0, len(lines) - 80)
    tail = lines[start:]

    subtotal = iva_total = percep_total = total = None
    iva_items: list = []
    percep_items: list = []

    for line in tail:
        up = line.upper()

        if 'SUBTOTAL' in up and subtotal is None:
            v = _last_amount(line)
            if v is not None:
                subtotal = v

        elif re.search(r'\bIVA\b', up) and 'RESPONSABLE' not in up and 'TOTAL' not in up:
            mrate = re.search(r'(\d{1,2}(?:[.,]\d{1,3})?)\s*%', line)
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

        elif 'TOTAL FACTURA' in up:
            v = _last_amount(line)
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
