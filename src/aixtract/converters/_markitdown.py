"""MarkItDown integration for fallback document conversion.

Adapted from CAMEL-AI MarkItDownLoader (camel/loaders/markitdown.py)
Copyright 2023-2026 @ CAMEL-AI.org. All Rights Reserved.
Licensed under the Apache License, Version 2.0
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import ClassVar

from aixtract.models.result import DocumentMetadata, ExtractionResult
from aixtract.utils.logging import get_logger

logger = get_logger(__name__)


class MarkItDownBackend:
    """Backend converter using Microsoft's markitdown package.

    Used as a fallback when native converters are not available,
    or as the primary converter for formats without native support.
    """

    SUPPORTED_FORMATS: ClassVar[list[str]] = [
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".epub", ".html", ".htm", ".jpg", ".jpeg", ".png",
        ".mp3", ".wav", ".csv", ".json", ".xml", ".zip", ".txt",
    ]

    def __init__(self) -> None:
        from markitdown import MarkItDown
        self.converter = MarkItDown()

    def can_handle(self, file_path: str) -> bool:
        """Check if markitdown supports this format."""
        _, ext = os.path.splitext(file_path)
        return ext.lower() in self.SUPPORTED_FORMATS

    def convert(self, file_path: str | Path) -> ExtractionResult:
        """Convert a file to markdown using markitdown.

        Args:
            file_path: Path to the file to convert.

        Returns:
            ExtractionResult with markdown content.
        """
        file_path = str(file_path)

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if not self.can_handle(file_path):
            raise ValueError(
                f"Unsupported format: {file_path}. "
                f"Supported: {self.SUPPORTED_FORMATS}"
            )

        result = self.converter.convert(file_path)
        content = result.text_content

        return ExtractionResult(
            success=True,
            content=content,
            content_markdown=content,
            metadata=DocumentMetadata(
                filename=Path(file_path).name,
                file_path=Path(file_path),
                file_size=os.path.getsize(file_path),
                converter_used="markitdown",
                word_count=len(content.split()),
                char_count=len(content),
            ),
        )
