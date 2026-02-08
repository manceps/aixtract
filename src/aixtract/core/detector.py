"""Format detection using python-magic and file extensions."""
from __future__ import annotations

from pathlib import Path

import magic


class FormatDetector:
    """Detect document format from content and extension."""

    def __init__(self) -> None:
        self._mime = magic.Magic(mime=True)

    def detect(
        self,
        content: bytes | None = None,
        filename: str | None = None,
    ) -> tuple[str | None, str | None]:
        """Detect format returning (extension, mimetype).

        Args:
            content: File content bytes for magic detection.
            filename: Filename for extension-based detection.

        Returns:
            Tuple of (extension, mimetype). Either may be None.
        """
        extension = None
        mimetype = None

        if filename:
            extension = Path(filename).suffix.lower()

        if content:
            mimetype = self._mime.from_buffer(content)

        return extension, mimetype
