# handlers_guerrini.py
import re
from typing import List, Dict, Any, Tuple, Optional

from app.vendors.registry import register
from app.services.text_utils import NUM_PURE, NUM_ANY, parse_number_smart


def _extract_totals_numeric(lines: List[str], out: Dict[str, Any]) -> bool:
    idx_sub = None
    for i in range(len(lines) - 1, -1, -1):
        if re.search(r'\bSUBTOTAL\b', lines[i].upper()):
            idx_sub = i
            break
    if idx_sub is None:
        return False
    window = lines[idx_sub: min(len(lines), idx_sub + 60)]
    numeric_lines: List[Tuple[int, float]] = []
    for j, line in enumerate(window):
        if NUM_PURE.match(line):
            v = parse_number_smart(line)
            if v is not None:
                numeric_lines.append((j, v))
    values = [v for _, v in numeric_lines[:4]]
    if len(values) < 2:
        return False

    subtotal = values[0]
    iva = values[1]
    percep = values[2] if len(values) >= 3 else 0.0
    total = values[3] if len(values) >= 4 else round(subtotal + iva + percep, 2)

    out["subtotal"] = subtotal
    out["iva"] = iva
    out["iva_detalle"] = [{"alicuota": "21.00", "monto": iva}]
    out["percepciones_total"] = percep
    out["percepciones_detalle"] = [] if len(values) < 3 else [{"desc": "PERCEP. IIBB", "monto": percep}]
    out["total"] = total
    return True


def _amount_from_line(line: str, prefer_last: bool = False) -> Optional[float]:
    """
    Busca el numero despues de los dos puntos (o el primero/ultimo disponible).
    Soporta lineas OCR como 'IVA 21.00: 0.00' o 'TOTAL: 169,000.00 ... 0800 222 6678'.
    """
    segment = line
    if ':' in line:
        segment = line.split(':')[-1]
    matches = list(NUM_ANY.finditer(segment))
    if not matches:
        matches = list(NUM_ANY.finditer(line))
    if not matches:
        return None
    idx = -1 if prefer_last else 0
    return parse_number_smart(matches[idx].group(0))


def _extract_totals_ocr(lines: List[str], out: Dict[str, Any]) -> bool:
    idx_sub = None
    for i in range(len(lines) - 1, -1, -1):
        if 'SUBTOTAL' in lines[i].upper():
            idx_sub = i
            break
    if idx_sub is None:
        return False

    window = lines[idx_sub: min(len(lines), idx_sub + 80)]
    subtotal = iva = perc = total = None
    perc_desc = None

    for line in window:
        up = line.upper()
        if subtotal is None and 'SUBTOTAL' in up:
            subtotal = _amount_from_line(line)
            continue
        if 'IVA' in up and 'RESPONSABLE' not in up:
            cand = _amount_from_line(line, prefer_last=True)
            if cand is not None:
                iva = cand
            continue
        if any(k in up for k in ('PERC', 'PERCEP', 'IIBB', 'INGRESOS BRUTOS', 'ARBA', 'AGIP')):
            cand = _amount_from_line(line, prefer_last=True)
            if cand is not None:
                perc = cand
                perc_desc = line.strip()
            continue
        if 'TOTAL' in up:
            total = _amount_from_line(line)
            break

    if subtotal is None and iva is None and perc is None and total is None:
        return False

    if subtotal is not None:
        out["subtotal"] = subtotal
    if iva is not None:
        out["iva"] = iva
        out["iva_detalle"] = [{"alicuota": "21.00", "monto": iva}]
    if perc is not None:
        out["percepciones_total"] = perc
        out["percepciones_detalle"] = [{"desc": perc_desc or "PERCEP. IIBB", "monto": perc}]
    if total is not None:
        out["total"] = total
    elif subtotal is not None:
        out["total"] = round((subtotal or 0.0) + (iva or 0.0) + (perc or 0.0), 2)
    return True


@register("GUERRINI")
def extract_totals_guerrini(lines: List[str], out: Dict[str, Any]) -> None:
    used_ocr = bool((out.get("debug") or {}).get("used_ocr"))
    if used_ocr:
        handled = _extract_totals_ocr(lines, out)
        if not handled:
            _extract_totals_numeric(lines, out)
    else:
        handled = _extract_totals_numeric(lines, out)
        if not handled:
            _extract_totals_ocr(lines, out)
