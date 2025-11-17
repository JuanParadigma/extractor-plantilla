"""Load vendor detection config from YAML (names and CUIT mappings)."""

from typing import Any, Dict
import os
import yaml


def load_vendor_config(cfg_path: str) -> Dict[str, Any]:
    if not os.path.exists(cfg_path):
        return {"detect": {"names": {}, "cuits": {}}}
    with open(cfg_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    names: Dict[str, list] = {}
    cuits: Dict[str, str] = {}
    for vid, cfg in (data or {}).items():
        for name in cfg.get("detect", {}).get("names", []):
            names.setdefault(vid.upper(), []).append(name)
        for cuit in cfg.get("detect", {}).get("cuits", []):
            cuits[cuit] = vid.upper()
    return {"detect": {"names": names, "cuits": cuits}}

