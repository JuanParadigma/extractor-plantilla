"""Normalization helpers to map vendor-specific outputs into a minimal payload."""

import re
from typing import Any, Dict, List, Optional, Tuple

FIXED_TAX_FIELDS = [
    "percepcion_iva",
    "percepcion_iibb_bs_as",
    "percepcion_ganancias",
    "percepcion_iibb_la_pampa",
    "percepcion_iibb_rio_negro",
    "percepcion_iibb_neuquen",
    "percepcion_iibb_caba",
    "percepcion_iibb_cordoba",
    "percepcion_iibb_chubut",
    "percepcion_iibb_mendoza",
    "percepcion_iibb_santa_cruz",
    "percepcion_iibb_santa_fe",
    "percepcion_iibb_tucuman",
    "percepcion_iibb_entre_rios",
    "percepcion_iibb_la_rioja",
    "impuesto_combustible",
    "impuestos_y_sellados",
    "retencion_iva",
    "retencion_iibb_pcia_bs_as",
    "retencion_ganancias",
    "retencion_iibb_pcia_rio_negro",
    "retencion_iibb_pcia_neuquen",
    "retencion_iibb_sirtac",
]

NORMALIZATION_RULES = [
    (r"\bRET(ENCI[�O]N|\.?)\b.*\bIVA\b", "retencion_iva"),
    (r"\bRET(ENCI[�O]N|\.?)\b.*\bGANANCIAS?\b", "retencion_ganancias"),
    (r"\bRET(ENCI[�O]N|\.?)\b.*\bIIBB\b.*\b(BUENOS\s*AIRES|ARBA|P\.?B\.?A)\b", "retencion_iibb_pcia_bs_as"),
    (r"\bRET(ENCI[�O]N|\.?)\b.*\bIIBB\b.*\bR[�I]O\s*NEGRO\b", "retencion_iibb_pcia_rio_negro"),
    (r"\bRET(ENCI[�O]N|\.?)\b.*\bIIBB\b.*\bNEUQU[�E]N\b", "retencion_iibb_pcia_neuquen"),
    (r"\bRET(ENCI[�O]N|\.?)\b.*\bSIRTAC\b", "retencion_iibb_sirtac"),
    (r"\bPERCEP(CCI[�O]N|\.?)\b.*\bIVA\b", "percepcion_iva"),
    (r"\bRG\s*3337\b|\bR\.?G\.?\s*3337\b|\bDGI\s*3337\b", "percepcion_iva"),
    (r"\bRG\s*2126\b|\bR\.?G\.?\s*2126\b", "percepcion_iva"),
    (r"\b(?:IB|IIBB)\s*BA\b.*\bLOC(?:AL)?\.?\b.*\bDN\b\s*B\s*70\s*[/\-]?\s*0?7\b", "percepcion_iibb_bs_as"),
    (r"\bDN\b\s*B\s*70\s*[/\-]?\s*0?7\b", "percepcion_iibb_bs_as"),
    (r"\bIIBB\b.*\b(BUENOS\s*AIRES|ARBA|P\.?B\.?A)\b", "percepcion_iibb_bs_as"),
    (r"\bIIBB\b.*\bCABA\b|\bAGIP\b", "percepcion_iibb_caba"),
    (r"\bIIBB\b.*\bNEUQU[�E]N\b|\bIB\s*(CONV\.?|CONVENIO)\s*NEUQ", "percepcion_iibb_neuquen"),
    (r"\bIIBB\b.*\bR[�I]O\s*NEGRO\b|\bRIO\s*NEG\b|\bIB\s*(CONV\.?|CONVENIO)\s*R[�I]O\s*NEG", "percepcion_iibb_rio_negro"),
    (r"\bIIBB\b.*\bLA\s*PAMPA\b", "percepcion_iibb_la_pampa"),
    (r"\bIIBB\b.*\bC[�O]RDOBA\b", "percepcion_iibb_cordoba"),
    (r"\bIIBB\b.*\bCHUBUT\b", "percepcion_iibb_chubut"),
    (r"\bIIBB\b.*\bMENDOZA\b", "percepcion_iibb_mendoza"),
    (r"\bIIBB\b.*\bSANTA\s*CRUZ\b", "percepcion_iibb_santa_cruz"),
    (r"\bIIBB\b.*\bSANTA\s*FE\b", "percepcion_iibb_santa_fe"),
    (r"\bIIBB\b.*\bTUCUM[�A]N\b", "percepcion_iibb_tucuman"),
    (r"\bIIBB\b.*\bENTRE\s*R[I�]OS\b", "percepcion_iibb_entre_rios"),
    (r"\bIIBB\b.*\bLA\s*RIOJA\b", "percepcion_iibb_la_rioja"),
    (r"\bDN\s*B70(?:/0?7)?\b|\bIB\s*BA\b", "percepcion_iibb_bs_as"),
    (r"\bPERCEP(CCI[�O]N|\.?)\b.*\bGANANCIAS?\b", "percepcion_ganancias"),
    (r"IMPUESTO\s+AL\s+COMBUSTIBLE|ITC\b", "impuesto_combustible"),
    (r"\bSELLOS\b|\bIMPUESTOS?\s+VARIOS\b|\bIMPUESTOS?\b", "impuestos_y_sellados"),
]

IVA_RATES_CANON = (27.0, 21.0, 10.5, 5.0, 2.5)


def _normalize_fixed_schema(out: Dict[str, Any]) -> Dict[str, Optional[float]]:
    fixed = {k: None for k in FIXED_TAX_FIELDS}
    items = list(out.get("percepciones_detalle") or [])
    total_perc = out.get("percepciones_total")
    if (not items) and (total_perc is not None):
        items = [{"desc": "PERCEP. IIBB", "monto": total_perc}]
    for it in items:
        desc_raw = (it.get("desc") or "").upper()
        monto = float(it.get("monto") or 0.0)
        matched_key = None
        for pattern, key in NORMALIZATION_RULES:
            if re.search(pattern, desc_raw, flags=re.I):
                matched_key = key
                break
        if matched_key:
            fixed[matched_key] = round((fixed[matched_key] or 0.0) + monto, 2)
    return fixed


def _to_iso_date(maybe_date: Optional[str]) -> Optional[str]:
    if not maybe_date:
        return None
    s = maybe_date.strip()
    m = re.fullmatch(r"(\d{2})[\/\-.](\d{2})[\/\-.](\d{4})", s)
    if m:
        dd, mm, yyyy = m.group(1), m.group(2), m.group(3)
        return f"{yyyy}-{mm}-{dd}"
    m = re.fullmatch(r"(\d{4})[\/\-](\d{2})[\/\-](\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return s


def _parse_aliquota_to_float(a) -> Optional[float]:
    if a is None:
        return None
    s = str(a).strip().replace("%", "").replace(",", ".")
    try:
        v = float(s)
        if abs(v - 10.5) < 1e-6:
            return 10.5
        if abs(v - 2.5) < 1e-6:
            return 2.5
        if abs(v - 5.0) < 1e-6:
            return 5.0
        if abs(v - 21.0) < 1e-6:
            return 21.0
        if abs(v - 27.0) < 1e-6:
            return 27.0
        return v
    except Exception:
        return None


def _sum_iva_by_rate(iva_detalle: List[Dict[str, Any]], iva_total: Optional[float]) -> Dict[str, float]:
    buckets: Dict[float, float] = {}
    for item in iva_detalle or []:
        rate = _parse_aliquota_to_float(item.get("alicuota"))
        amt = float(item.get("monto") or 0.0)
        if rate is None:
            buckets[999.0] = round((buckets.get(999.0, 0.0) + amt), 2)
        else:
            buckets[rate] = round((buckets.get(rate, 0.0) + amt), 2)
    if not buckets and iva_total:
        buckets[999.0] = round(float(iva_total or 0.0), 2)
    out: Dict[str, float] = {}
    for k, v in buckets.items():
        key = "otros" if k == 999.0 else (str(int(k)) if float(k).is_integer() else str(k))
        out[key] = v
    ordered: Dict[str, float] = {}
    for r in IVA_RATES_CANON:
        rk = str(int(r)) if float(r).is_integer() else str(r)
        if rk in out and out[rk] > 0:
            ordered[rk] = out[rk]
    for rk, v in out.items():
        if rk not in ordered and v > 0:
            ordered[rk] = v
    return ordered


def _split_perc_ret(tributos: Dict[str, Optional[float]]) -> Tuple[Dict[str, float], Dict[str, float]]:
    percepciones: Dict[str, float] = {}
    retenciones: Dict[str, float] = {}
    for k, v in (tributos or {}).items():
        if v is None or float(v) == 0.0:
            continue
        if k.startswith("percepcion_") or k in ("impuesto_combustible", "impuestos_y_sellados"):
            percepciones[k] = float(v)
        elif k.startswith("retencion_"):
            retenciones[k] = float(v)
    return percepciones, retenciones


def build_minimal_payload(full: Dict[str, Any], prefer_cuit: str = "proveedor") -> Dict[str, Any]:
    numero = full.get("numero")
    fecha = _to_iso_date(full.get("fecha"))
    cuit = (full.get("cuit_proveedor") if prefer_cuit == "proveedor" else full.get("cuit_cliente")) or ""
    total = float(full.get("total") or 0.0)

    iva_por_tasa = _sum_iva_by_rate(full.get("iva_detalle"), full.get("iva"))
    iva_total = round(sum(iva_por_tasa.values()), 2) if iva_por_tasa else float(full.get("iva") or 0.0)

    trib_norm = _normalize_fixed_schema(full)
    percepciones, retenciones = _split_perc_ret(trib_norm)
    perc_total = round(sum(percepciones.values()), 2) if percepciones else 0.0

    subtotal = full.get("subtotal")
    if subtotal is None:
        subtotal = round(total - iva_total - perc_total, 2) if total else 0.0
        if abs(subtotal) < 1e-6:
            subtotal = 0.0

    return {
        "numero": numero or "",
        "fecha": fecha or "",
        "cuit": cuit or "",
        "subtotal": round(float(subtotal or 0.0), 2),
        "total": round(total, 2),
        "iva": iva_por_tasa,
        "percepciones": percepciones,
        "retenciones": retenciones,
    }


def validate_and_repair(out: Dict[str, Any], tol: float = 0.05) -> None:
    sub = out.get("subtotal") or 0.0
    iva = out.get("iva") or 0.0
    perc = out.get("percepciones_total") or 0.0
    tot = out.get("total")
    comp = round(sub + iva + perc, 2)
    out.setdefault("warnings", [])
    if tot is None:
        out["total"] = comp
        out["warnings"].append("TOTAL estimado = SUBTOTAL + IVA + PERCEPCIONES")
    elif abs((tot or 0.0) - comp) > tol:
        out["warnings"].append(f"Diferencia contable: total({tot}) != subtotal+iva+percepciones({comp})")

