"""
Formatos de salida VB6-friendly a partir del payload minimal normalizado.
"""
from typing import Any, Dict, List
import re


def _num(v) -> str:
    try:
        return str(float(v)).replace(",", ".")
    except Exception:
        return "0"


def _clean(s: str) -> str:
    return re.sub(r"[\r\n=]+", " ", str(s)).strip()


def clean_cuit(cuit: str) -> str:
    """Deja solo los dígitos del CUIT."""
    if not cuit:
        return ""
    return re.sub(r"\D", "", cuit or "")


def to_kv(minimal: Dict[str, Any]) -> str:
    """
    Convierte el payload minimal a key=value por líneas con contadores/index.
    """
    lines: List[str] = []
    lines.append("status=ok")
    lines.append("version=1")
    lines.append(f"ocr={'1' if minimal.get('ocr') else '0'}")
    lines.append(f"numero={minimal.get('numero','')}")
    lines.append(f"fecha={minimal.get('fecha','')}")
    lines.append(f"cuit={minimal.get('cuit','')}")
    lines.append(f"subtotal={_num(minimal.get('subtotal', 0))}")
    lines.append(f"total={_num(minimal.get('total', 0))}")

    # IVA por alícuota
    iva = minimal.get("iva") or {}
    iva_items = [(str(k), float(v)) for k, v in iva.items() if v and float(v) != 0.0]
    lines.append(f"iva_count={len(iva_items)}")
    order = ["27", "21", "10.5", "5", "2.5"]

    def rank(k: str) -> int:
        return order.index(k) if k in order else 999

    iva_items.sort(key=lambda x: (rank(x[0]), x[0]))
    for i, (rate, monto) in enumerate(iva_items, start=1):
        lines.append(f"iva_{i}_tasa={_clean(rate)}")
        lines.append(f"iva_{i}_monto={_num(monto)}")

    # Percepciones normalizadas
    percs = minimal.get("percepciones") or {}
    perc_items = [(k, float(v)) for k, v in percs.items() if v and float(v) != 0.0]
    perc_items.sort(key=lambda x: x[0])
    lines.append(f"percepciones_count={len(perc_items)}")
    for i, (name, monto) in enumerate(perc_items, start=1):
        lines.append(f"percepciones_{i}_clave={name}")
        lines.append(f"percepciones_{i}_monto={_num(monto)}")

    # Retenciones normalizadas
    rets = minimal.get("retenciones") or {}
    ret_items = [(k, float(v)) for k, v in rets.items() if v and float(v) != 0.0]
    ret_items.sort(key=lambda x: x[0])
    lines.append(f"retenciones_count={len(ret_items)}")
    for i, (name, monto) in enumerate(ret_items, start=1):
        lines.append(f"retenciones_{i}_clave={name}")
        lines.append(f"retenciones_{i}_monto={_num(monto)}")

    return "\n".join(lines)


def to_ini(minimal: Dict[str, Any]) -> str:
    """
    Alternativa INI por secciones (agrupa visualmente).
    """
    out: List[str] = []
    out += ["[meta]", "status=ok", "version=1", f"ocr={'1' if minimal.get('ocr') else '0'}", ""]
    out += ["[factura]"]
    out += [
        f"numero={minimal.get('numero','')}",
        f"fecha={minimal.get('fecha','')}",
        f"cuit={minimal.get('cuit','')}",
        f"total={_num(minimal.get('total', 0))}",
        "",
    ]
    out += ["[iva]"]
    iva = minimal.get("iva") or {}
    order = ["27", "21", "10.5", "5", "2.5"]
    for r in order:
        if r in iva and float(iva[r]) != 0.0:
            out.append(f"{r}={_num(iva[r])}")
    for k, v in iva.items():
        if k not in order and float(v) != 0.0:
            out.append(f"{_clean(k)}={_num(v)}")
    out.append("")

    out += ["[percepciones]"]
    for k, v in sorted((minimal.get("percepciones") or {}).items(), key=lambda x: x[0]):
        if v and float(v) != 0.0:
            out.append(f"{k}={_num(v)}")
    out.append("")

    out += ["[retenciones]"]
    for k, v in sorted((minimal.get("retenciones") or {}).items(), key=lambda x: x[0]):
        if v and float(v) != 0.0:
            out.append(f"{k}={_num(v)}")
    out.append("")
    return "\n".join(out)
