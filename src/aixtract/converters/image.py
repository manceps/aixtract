"""Image converter with OCR support."""
from __future__ import annotations

import io
from pathlib import Path
from typing import BinaryIO, ClassVar

from aixtract.converters.base import BaseConverter
from aixtract.core.registry import ConverterRegistry
from aixtract.models.result import DocumentMetadata, ExtractionResult


@ConverterRegistry.register
class ImageConverter(BaseConverter):
    """Extract text from images using OCR."""

    name: ClassVar[str] = "image"
    supported_extensions: ClassVar[tuple[str, ...]] = (
        ".png", ".jpg", ".jpeg", ".tiff", ".bmp",
    )
    supported_mimetypes: ClassVar[tuple[str, ...]] = (
        "image/png", "image/jpeg", "image/tiff", "image/bmp",
    )
    requires: ClassVar[tuple[str, ...]] = ("PIL", "pytesseract")

    def extract(
        self,
        source: Path | BinaryIO | bytes,
        filename: str | None = None,
    ) -> ExtractionResult:
        """Extract text from image using OCR."""
        import pytesseract
        from PIL import Image

        content_bytes, file_path = self._read_source(source)

        if self.config.ocr.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.config.ocr.tesseract_cmd

        image = Image.open(io.BytesIO(content_bytes))
        text = pytesseract.image_to_string(
            image,
            lang=self.config.ocr.language,
        )

        width, height = image.size

        return ExtractionResult(
            success=True,
            content=text.strip(),
            content_markdown=text.strip(),
            metadata=DocumentMetadata(
                filename=filename or (file_path.name if file_path else "image.png"),
                file_path=file_path,
                format_detected="image",
                converter_used=self.name,
                word_count=len(text.split()),
                char_count=len(text),
                extra={
                    "width": width,
                    "height": height,
                    "ocr_language": self.config.ocr.language,
                },
            ),
        )
