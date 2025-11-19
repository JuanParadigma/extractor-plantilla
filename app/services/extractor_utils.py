"""
Backwards-compatible shim for extraction helpers.

Real implementations live in smaller modules:
- pdf_reader: IO/OCR
- metadata_extractor: header + CUIT/name/vendor detection
- text_utils: numeric parsing and text normalization
"""

from app.services.pdf_reader import ocr_pdf_to_lines, read_pdf_text
from app.services.metadata_extractor import (
    detect_vendor_basic,
    detect_vendor_by_cuit,
    extract_header_common,
    extract_names_and_cuits,
)
from app.services.text_utils import (
    NUM_ANY,
    NUM_PURE,
    RE_CAE,
    RE_CUIT,
    RE_FECHA,
    RE_NUM_FACT,
    first_amount_forward,
    norm_line,
    parse_number_smart,
    strip_currency,
)

__all__ = [
    "ocr_pdf_to_lines",
    "read_pdf_text",
    "detect_vendor_basic",
    "detect_vendor_by_cuit",
    "extract_header_common",
    "extract_names_and_cuits",
    "NUM_ANY",
    "NUM_PURE",
    "RE_CAE",
    "RE_CUIT",
    "RE_FECHA",
    "RE_NUM_FACT",
    "first_amount_forward",
    "norm_line",
    "parse_number_smart",
    "strip_currency",
]