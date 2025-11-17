"""
Configuración centralizada de runtime (paths OCR) y defaults de la API.
"""
import os


# Ajustes básicos para que Tesseract esté disponible en Render/Linux y Windows.
_DEFAULT_TESSDATA = os.environ.get("TESSDATA_PREFIX") or "/usr/share/tesseract-ocr/4.00/tessdata"
_EXTRA_BIN_PATHS = [
    "/usr/bin",
    "/usr/local/bin",
    "/opt/render/project/src/.apt/usr/bin",
    "/opt/render/.apt/usr/bin",
]


def apply_runtime_env() -> None:
    """
    Inyecta rutas de binarios/tesdata de Tesseract si no están ya presentes.
    No hace raise en caso de error; es defensivo.
    """
    try:
        path_parts = os.environ.get("PATH", "").split(os.pathsep)
        for p in _EXTRA_BIN_PATHS:
            if p and p not in path_parts:
                path_parts.append(p)
        os.environ["PATH"] = os.pathsep.join(path_parts)
        os.environ.setdefault("TESSDATA_PREFIX", _DEFAULT_TESSDATA)
    except Exception:
        # No frenamos la app si fallan estas asignaciones.
        pass
