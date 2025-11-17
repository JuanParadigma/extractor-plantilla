from enum import Enum


class Vendor(str, Enum):
    GUERRINI = "GUERRINI"
    PIRELLI = "PIRELLI"


class OutFmt(str, Enum):
    json = "json"        # JSON minimal normalizado
    kv = "kv"            # VB6-friendly key=value (plano)
    ini = "ini"          # INI por secciones
