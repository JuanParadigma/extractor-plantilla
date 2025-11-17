"""PDF readers: plain text extraction (fitz) and OCR (pdf2image + pytesseract)."""

from typing import Any, List, Optional, Tuple
import os
import platform
import shutil

from app.services.text_utils import norm_line


def _import_fitz():
    try:
        import fitz as _fitz
        return _fitz
    except Exception:
        return None


def _import_pdf2image():
    try:
        from pdf2image import convert_from_path as _convert
        return _convert
    except Exception:
        return None


def _import_pillow_image():
    try:
        from PIL import Image as _image
        return _image
    except Exception:
        return None


fitz = _import_fitz()
convert_from_path = _import_pdf2image()
Image = _import_pillow_image()
POPPLER_PATH = os.environ.get("POPPLER_PATH")


def _resolve_tesseract_path() -> Optional[str]:
    """Heuristics to locate tesseract."""
    candidates = []
    env_path = os.environ.get("TESSERACT_CMD")
    if env_path:
        candidates.append(env_path)
    if platform.system() == "Windows":
        candidates.append(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    else:
        candidates.extend(
            [
                "/usr/bin/tesseract",
                "/usr/local/bin/tesseract",
                "/opt/render/project/src/.apt/usr/bin/tesseract",
                "/opt/render/.apt/usr/bin/tesseract",
            ]
        )
        auto_path = shutil.which("tesseract")
        if auto_path:
            candidates.append(auto_path)
    seen = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        if os.path.exists(candidate):
            return candidate
    return None


def _load_pytesseract() -> Tuple[Optional[Any], Optional[Any]]:
    try:
        import pytesseract as _pytesseract
    except Exception:
        return None, None
    tess_path = _resolve_tesseract_path()
    if tess_path:
        _pytesseract.pytesseract.tesseract_cmd = tess_path
        try:
            from pytesseract import image_to_data as _image_to_data  # type: ignore
        except Exception:
            _image_to_data = None
        return _pytesseract, _image_to_data
    return None, None


pytesseract, image_to_data = _load_pytesseract()


def _normalize_non_empty(lines: List[str]) -> List[str]:
    normalized: List[str] = []
    for line in lines:
        cleaned = norm_line(line)
        if cleaned:
            normalized.append(cleaned)
    return normalized


def read_pdf_text(pdf_path: str) -> List[str]:
    """Extracts text without OCR using fitz."""
    if fitz is None:
        return []
    try:
        raw_lines: List[str] = []
        with fitz.open(pdf_path) as doc:
            for page in doc:
                txt = page.get_text("text")
                if txt:
                    raw_lines.extend(txt.splitlines())
        return _normalize_non_empty(raw_lines)
    except Exception:
        return []


def _ocr_dependencies_ready() -> bool:
    return convert_from_path is not None and pytesseract is not None and Image is not None


def _convert_pdf_to_images(pdf_path: str, dpi: int) -> List[Any]:
    if not convert_from_path or not Image:
        return []
    try:
        kwargs = {"dpi": dpi}
        if POPPLER_PATH:
            kwargs["poppler_path"] = POPPLER_PATH
        return convert_from_path(pdf_path, **kwargs)
    except Exception:
        return []


def _flush_buffer(buffer: List[str], collector: List[str]) -> None:
    if not buffer:
        return
    line = norm_line(" ".join(buffer))
    if line:
        collector.append(line)


def _extract_lines_with_data(image: Any) -> List[str]:
    if pytesseract is None:
        return []
    try:
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, lang="spa+eng")
    except Exception:
        return _extract_lines_with_string(image)
    text_lines: List[str] = []
    total_tokens = len(data.get("text", []))
    current_line: Optional[int] = None
    buffer: List[str] = []
    for idx in range(total_tokens):
        token = data["text"][idx].strip()
        conf_raw = data["conf"][idx]
        try:
            confidence = int(conf_raw)
        except Exception:
            confidence = -1
        if confidence < 0 or not token:
            continue
        line_num = data.get("line_num", [1] * total_tokens)[idx]
        if current_line is None:
            current_line = line_num
        if line_num != current_line:
            _flush_buffer(buffer, text_lines)
            buffer = [token]
            current_line = line_num
        else:
            buffer.append(token)
    _flush_buffer(buffer, text_lines)
    return text_lines


def _extract_lines_with_string(image: Any) -> List[str]:
    if pytesseract is None:
        return []
    try:
        txt = pytesseract.image_to_string(image, lang="spa+eng")
    except Exception:
        return []
    return _normalize_non_empty(txt.splitlines())


def _extract_lines_from_image(image: Any) -> List[str]:
    if pytesseract is None:
        return []
    if image_to_data is not None:
        return _extract_lines_with_data(image)
    return _extract_lines_with_string(image)


def ocr_pdf_to_lines(pdf_path: str, dpi: int = 300) -> List[str]:
    if not _ocr_dependencies_ready():
        return []
    images = _convert_pdf_to_images(pdf_path, dpi)
    text_lines: List[str] = []
    for image in images:
        text_lines.extend(_extract_lines_from_image(image))
    return text_lines


class PdfLineReader:
    """Encapsulates PDF to text/OCR decisions."""

    def __init__(self, prefer_ocr: bool = True, dpi: int = 300):
        self.prefer_ocr = prefer_ocr
        self.dpi = dpi

    def read(self, pdf_path: str, use_ocr_hint: Optional[bool] = None) -> Tuple[List[str], bool]:
        prefer_ocr = self.prefer_ocr if use_ocr_hint is None else bool(use_ocr_hint)
        if prefer_ocr:
            lines = ocr_pdf_to_lines(pdf_path, dpi=self.dpi)
            used_ocr = True
            if not lines:
                lines = read_pdf_text(pdf_path)
                used_ocr = False
        else:
            lines = read_pdf_text(pdf_path)
            used_ocr = False
            if not lines:
                lines = ocr_pdf_to_lines(pdf_path, dpi=self.dpi)
                used_ocr = True if lines else False
        return lines, used_ocr

