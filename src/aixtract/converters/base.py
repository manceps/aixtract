"""Base converter interface."""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO, ClassVar

if TYPE_CHECKING:
    from aixtract.models.config import ExtractionConfig
    from aixtract.models.result import ExtractionResult


class BaseConverter(ABC):
    """Abstract base class for document converters."""

    # Class attributes for registration
    name: ClassVar[str]
    supported_extensions: ClassVar[tuple[str, ...]]
    supported_mimetypes: ClassVar[tuple[str, ...]]

    # Optional dependencies
    requires: ClassVar[tuple[str, ...]] = ()

    def __init__(self, config: "ExtractionConfig | None" = None) -> None:
        from aixtract.models.config import ExtractionConfig
        self.config = config or ExtractionConfig()
        self._validate_dependencies()

    def _validate_dependencies(self) -> None:
        """Check if required packages are available."""
        missing = []
        for package in self.requires:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing.append(package)

        if missing:
            raise ImportError(
                f"Converter '{self.name}' requires: {', '.join(missing)}. "
                f"Install with: pip install aixtract[{self.name}]"
            )

    @abstractmethod
    def extract(
        self,
        source: Path | BinaryIO | bytes,
        filename: str | None = None,
    ) -> "ExtractionResult":
        """Extract content from document."""
        ...

    @classmethod
    def can_handle(cls, extension: str, mimetype: str | None = None) -> bool:
        """Check if converter can handle this file type."""
        ext = extension.lower().lstrip('.')
        if ext in [e.lstrip('.') for e in cls.supported_extensions]:
            return True
        if mimetype and mimetype in cls.supported_mimetypes:
            return True
        return False

    def _read_source(
        self,
        source: Path | BinaryIO | bytes,
    ) -> tuple[bytes, Path | None]:
        """Read source into bytes."""
        if isinstance(source, bytes):
            return source, None
        elif isinstance(source, Path):
            return source.read_bytes(), source
        else:
            # File-like object
            return source.read(), None

    @staticmethod
    def _strip_consecutive_newlines(text: str) -> str:
        """Collapse 3+ consecutive newlines to double newlines.

        Preserves paragraph breaks (double newlines) while removing
        excessive blank lines. Adapted from CAMEL base_io.py.
        """
        return re.sub(r"\n{3,}", "\n\n", text)
