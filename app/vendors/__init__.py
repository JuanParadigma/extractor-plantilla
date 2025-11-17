"""
Vendors package: registry + vendor-specific total extractors.
Import handlers here to auto-register them on import.
"""

from app.vendors.registry import register, REGISTRY  # re-export

# Side-effect imports to register handlers
from app.vendors import handlers_pirelli  # noqa: F401
from app.vendors import handlers_guerrini  # noqa: F401

__all__ = ["register", "REGISTRY"]
