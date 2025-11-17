"""Utilities for parsing numbers and normalizing OCR/text output."""

from typing import List, Optional
import re


def norm_line(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def strip_currency(value: str) -> str:
    return re.sub(r"[$]", "", value).strip()


def _clean_number_candidate(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = strip_currency(value).replace(" ", "")
    cleaned = re.sub(r"[^0-9,.\-]", "", cleaned)
    return cleaned or None


def _safe_float(value: str) -> Optional[float]:
    try:
        return float(value)
    except Exception:
        return None


def _parse_with_decimal_tail(value: str) -> Optional[float]:
    if re.search(r"[.,]\d{2}$", value):
        decimal_sep = value[-3:-2]
        normalized = value.replace(".", "").replace(",", ".") if decimal_sep == "," else value.replace(",", "")
        return _safe_float(normalized)
    return None


def _parse_with_single_separator(value: str) -> Optional[float]:
    if "," in value and "." not in value:
        return _safe_float(value.replace(",", ""))
    if "." in value and "," not in value:
        parsed = _safe_float(value)
        if parsed is not None:
            return parsed
        return _safe_float(value.replace(".", ""))
    return None


def _parse_with_last_separator(value: str) -> Optional[float]:
    matches = list(re.finditer(r"[.,]", value))
    if not matches:
        return None
    last_sep = matches[-1].group(0)
    normalized = value.replace(".", "").replace(",", ".") if last_sep == "," else value.replace(",", "")
    return _safe_float(normalized)


def _parse_plain_number(value: str) -> Optional[float]:
    return _safe_float(value)


def parse_number_smart(raw_value: Optional[str]) -> Optional[float]:
    value = _clean_number_candidate(raw_value)
    if value is None:
        return None
    strategies = (
        _parse_with_decimal_tail,
        _parse_with_single_separator,
        _parse_with_last_separator,
        _parse_plain_number,
    )
    for resolver in strategies:
        parsed = resolver(value)
        if parsed is not None:
            return parsed
    return None


RE_CUIT = re.compile(r"\b\d{2}[- ]?\d{7,8}[- ]?\d\b")
RE_FECHA = re.compile(
    r"\b(?:\d{2}[\/\-\.]\d{2}[\/\-\.]\d{2,4}|\d{4}[\/\-]\d{2}[\/\-]\d{2})(?:\s+\d{1,2}:\d{1,2}:\d{1,2})?\b"
)
RE_NUM_FACT = re.compile(r"\b\d{4}-\d{8}\b")
RE_CAE = re.compile(r"\b\d{14}\b", re.ASCII)
NUM_PURE = re.compile(r"^\s*-?\s*\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})\s*$")
NUM_ANY = re.compile(r"[-]?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})|[-]?\d+(?:[.,]\d{2})")


def _match_numeric_fragment(line: str) -> Optional[str]:
    match = NUM_PURE.search(line)
    if match:
        return match.group(0)
    match = NUM_ANY.search(line)
    if match:
        return match.group(0)
    return None


def first_amount_forward(lines: List[str], start_idx: int, max_ahead: int = 12) -> Optional[float]:
    upper_bound = min(len(lines), start_idx + max_ahead + 1)
    for idx in range(start_idx, upper_bound):
        line = lines[idx].strip()
        if not line:
            continue
        fragment = _match_numeric_fragment(line)
        if fragment:
            value = parse_number_smart(fragment)
            if value is not None:
                return value
    return None

