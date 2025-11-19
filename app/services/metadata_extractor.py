"""Extraction helpers for header fields, vendor detection and CUIT/name parsing."""
import re
from typing import Any, Dict, List, Optional, Tuple

from app.services.text_utils import RE_CAE, RE_CUIT, RE_FECHA, RE_NUM_FACT


def _find_invoice_type(lines: List[str]) -> Optional[str]:
    for line in lines[:200]:
        match = re.search(r"\bFactura\s*([ABC])\b", line, re.I)
        if match:
            return match.group(1).upper()
        stripped = line.strip()
        if re.fullmatch(r"[ABC]", stripped, re.I):
            return stripped.upper()
    return None

def _find_invoice_number(lines: List[str]) -> Optional[str]:
    number = None
    for line in lines:
        match = RE_NUM_FACT.search(line)
        if match:
            number = match.group(0)
    return number


def _find_first_date(lines: List[str]) -> Optional[str]:
    for line in lines:
        match = RE_FECHA.search(line)
        if match:
            return match.group(0)
    return None

def _date_from_neighbors(lines: List[str], idx: int) -> Optional[str]:
    match = RE_FECHA.search(lines[idx])
    if match:
        return match.group(0)
    upper = min(idx + 3, len(lines))
    for neighbor in range(idx + 1, upper):
        match = RE_FECHA.search(lines[neighbor])
        if match:
            return match.group(0)
    return None

def _extract_cae_data(lines: List[str]) -> Tuple[Optional[str], Optional[str]]:
    cae = None
    cae_vto = None
    for idx, line in enumerate(lines):
        upper_line = line.upper()
        if "CAE" not in upper_line:
            continue
        match = RE_CAE.search(line) or RE_CAE.search(line.replace("CAE", ""))
        if match:
            cae = match.group(0)
        if any(keyword in upper_line for keyword in ("VTO", "VENC")):
            cae_vto = _date_from_neighbors(lines, idx)
    return cae, cae_vto

def extract_header_common(lines: List[str]) -> Dict[str, Any]:
    header: Dict[str, Any] = {"tipo": None, "numero": None, "fecha": None, "cae": None, "cae_vto": None}
    header["tipo"] = _find_invoice_type(lines)
    header["numero"] = _find_invoice_number(lines)
    header["fecha"] = _find_first_date(lines)
    cae, cae_vto = _extract_cae_data(lines)
    header["cae"] = cae
    header["cae_vto"] = cae_vto
    return header

def _collect_cuit_positions(lines: List[str]) -> List[Tuple[int, str]]:
    positions: List[Tuple[int, str]] = []
    for idx, line in enumerate(lines):
        for match in RE_CUIT.finditer(line):
            positions.append((idx, match.group(0)))
    positions.sort(key=lambda item: item[0])
    return positions

def _guess_client_name(lines: List[str], idx: int) -> Optional[str]:
    lower = max(0, idx - 5)
    keywords = r"(ALVAREZ|NEUM[A?]TIC|S\.A\.|SRL|RESPONSABLE|CLIENTE)"
    for line_idx in range(lower, idx + 1):
        candidate = lines[line_idx].strip()
        if not candidate:
            continue
        if re.search(keywords, candidate, re.I) or candidate.isupper():
            return candidate
    return None

VENDOR_REGEX = {
    "GUERRINI": r"GUERRINI\s+NEUM[A?]TICOS?\s*S\.?A\.?",
    "PIRELLI": r"PIRELLI\s+NEUM[A?]TICOS?\s*S\.?A\.?I\.?C\.?",
}

def _guess_vendor_name(lines: List[str], vendor: Optional[str]) -> Optional[str]:
    if not vendor:
        return None
    pattern = VENDOR_REGEX.get(vendor.upper())
    if not pattern:
        return None
    for line in (line.strip() for line in lines[:80]):
        if re.search(pattern, line, re.I):
            return line
    return None

def extract_names_and_cuits(
    lines: List[str], vendor: Optional[str]
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    proveedor = None
    cliente = None
    cuit_prov = None
    cuit_cli = None
    cuit_positions = _collect_cuit_positions(lines)
    if cuit_positions:
        cuit_prov = cuit_positions[0][1]
        rest = [c for c in cuit_positions if c[1] != cuit_prov]
        if rest:
            idx, cuit_cli = rest[-1]
            cliente = _guess_client_name(lines, idx)
    proveedor = _guess_vendor_name(lines, vendor)
    return proveedor, cuit_prov, cliente, cuit_cli

def detect_vendor_basic(lines: List[str], name_keywords: Dict[str, List[str]]) -> Optional[str]:
    header = " ".join(lines[:120]).upper()
    for vid, keywords in name_keywords.items():
        for keyword in keywords:
            if keyword.upper() in header:
                return vid
    return None

def detect_vendor_by_cuit(cuit: Optional[str], cuit_map: Dict[str, str]) -> Optional[str]:
    if not cuit:
        return None
    return cuit_map.get(cuit)