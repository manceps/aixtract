"""Document converters - auto-registration on import."""
from aixtract.converters.base import BaseConverter


# Optional format converters - import errors are caught gracefully
def _safe_import(module: str) -> None:
    """Import a converter module, silently ignoring ImportError."""
    try:
        __import__(module, fromlist=["_"])
    except ImportError:
        pass


# Core formats (no extra dependencies beyond markitdown)
_safe_import("aixtract.converters.text")
_safe_import("aixtract.converters.archive")

# Optional format converters
_safe_import("aixtract.converters.pdf")
_safe_import("aixtract.converters.docx")
_safe_import("aixtract.converters.xlsx")
_safe_import("aixtract.converters.pptx")
_safe_import("aixtract.converters.html")
_safe_import("aixtract.converters.epub")
_safe_import("aixtract.converters.image")
_safe_import("aixtract.converters.audio")

__all__ = ["BaseConverter"]
