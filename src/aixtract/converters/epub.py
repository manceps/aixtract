"""EPUB document converter."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import BinaryIO, ClassVar

from aixtract.converters.base import BaseConverter
from aixtract.core.registry import ConverterRegistry
from aixtract.models.result import DocumentMetadata, ExtractionResult


@ConverterRegistry.register
class EPUBConverter(BaseConverter):
    """Extract content from EPUB ebooks."""

    name: ClassVar[str] = "epub"
    supported_extensions: ClassVar[tuple[str, ...]] = (".epub",)
    supported_mimetypes: ClassVar[tuple[str, ...]] = ("application/epub+zip",)
    requires: ClassVar[tuple[str, ...]] = ("ebooklib", "bs4")

    def extract(
        self,
        source: Path | BinaryIO | bytes,
        filename: str | None = None,
    ) -> ExtractionResult:
        """Extract content from EPUB."""
        import ebooklib
        from bs4 import BeautifulSoup
        from ebooklib import epub

        content_bytes, file_path = self._read_source(source)

        # ebooklib needs a file path, write to temp if needed
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as tmp:
            tmp.write(content_bytes)
            tmp_path = tmp.name

        try:
            book = epub.read_epub(tmp_path)
        finally:
            os.unlink(tmp_path)

        # Extract metadata
        title = book.get_metadata("DC", "title")
        author = book.get_metadata("DC", "creator")

        text_parts = []
        markdown_parts = []

        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_content(), "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            if text:
                text_parts.append(text)
                markdown_parts.append(text)

        content = "\n\n".join(text_parts)
        content_markdown = "\n\n".join(markdown_parts)

        metadata = DocumentMetadata(
            filename=filename or (file_path.name if file_path else "book.epub"),
            file_path=file_path,
            format_detected="epub",
            title=title[0][0] if title else None,
            author=author[0][0] if author else None,
            page_count=len(text_parts),
            converter_used=self.name,
            word_count=len(content.split()),
            char_count=len(content),
        )

        return ExtractionResult(
            success=True,
            content=content,
            content_markdown=content_markdown,
            metadata=metadata,
        )
