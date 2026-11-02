# handlers_pirelli.py
import re
from typing import List, Dict, Any, Optional

from app.vendors.registry import register
from app.services.text_utils import parse_number_smart

_RE_NUM = re.compile(r'-?\d[\d,.]*\d|-?\d')

_PERCEP_KEYS = (
    'IIBB', 'PERC', 'RG DGI', 'DN B70',
    'NEUQUEN', 'RÍO NEG', 'RIO NEG', 'IB CONV', 'IB BA',
)

# Used to stop forward lookahead when scanning for amounts in fitz multi-line layout
_SECTION_BREAKS = (
    'SUBTOTAL', 'IVA', 'TOTAL FACTURA', 'REMITO',
    'IB CONV', 'IB BA', 'PERC', 'IIBB', 'RG DGI', 'DN B70',
    'NEUQUEN', 'RÍO NEG', 'RIO NEG',
)


def _last_amount(line: str) -> Optional[float]:
    """Last monetary amount on line (requires decimal point; skips CAE/barcode strings)."""
    normalized = re.sub(r'(\d)\s+([,.])', r'\1\2', line)
    for m in reversed(list(_RE_NUM.finditer(normalized))):
        raw = m.group(0)
        if '.' not in raw:
            continue
        v = parse_number_smart(raw)
        if v is not None and v != 0.0:
            return v
    return None


def _next_amount(lines: List[str], i: int) -> Optional[float]:
    """
    Last monetary amount on line i, or on the following lines if line i has none.
    Handles both OCR (single-line) and fitz (multi-line) layouts:
      OCR:  'SUBTOTAL 40387,958.64'                    → found on same line
      fitz: 'SUBTOTAL' / '40387,958.64'                → found on next line
      fitz: 'IVA ventas.' / '21.000 %' / base / amount → last of next 4 lines
    Stops scanning when a new section keyword is encountered.
    """
    v = _last_amount(lines[i])
    if v is not None:
        return v
    last_v = None
    for j in range(i + 1, min(i + 5, len(lines))):
        up = lines[j].upper()
        if any(s in up for s in _SECTION_BREAKS):
            break
        vj = _last_amount(lines[j])
        if vj is not None:
            last_v = vj
    return last_v


def _find_rate(lines: List[str], i: int) -> Optional[str]:
    """Rate % on line i or on the next 2 lines (fitz splits rate onto its own line)."""
    for j in range(i, min(i + 3, len(lines))):
        m = re.search(r'(\d{1,2}(?:[.,]\d{1,3})?)\s*%', lines[j])
        if m:
            return m.group(1).replace(',', '.')
    return None


@register("PIRELLI")
def extract_totals_pirelli(lines: List[str], out: Dict[str, Any]) -> None:
    start = max(0, len(lines) - 80)
    tail = lines[start:]

    subtotal = iva_total = percep_total = total = None
    iva_items: list = []
    percep_items: list = []

    for idx, line in enumerate(tail):
        up = line.upper()

        if 'SUBTOTAL' in up and subtotal is None:
            v = _next_amount(tail, idx)
            if v is not None:
                subtotal = v

        elif re.search(r'\bIVA\b', up) and 'RESPONSABLE' not in up and 'TOTAL' not in up:
            alic = _find_rate(tail, idx)
            v = _next_amount(tail, idx)
            if v is not None:
                iva_total = (iva_total or 0.0) + v
                iva_items.append({"alicuota": alic, "monto": v})

        elif any(k in up for k in _PERCEP_KEYS):
            v = _next_amount(tail, idx)
            if v is not None:
                percep_total = (percep_total or 0.0) + v
                percep_items.append({"desc": line.strip(), "monto": v})

        elif 'TOTAL FACTURA' in up:
            v = _next_amount(tail, idx)
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
