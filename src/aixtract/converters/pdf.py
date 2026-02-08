"""PDF document converter."""
from __future__ import annotations

from pathlib import Path
from typing import BinaryIO, ClassVar

from aixtract.converters.base import BaseConverter
from aixtract.core.registry import ConverterRegistry
from aixtract.models.result import DocumentMetadata, ExtractionResult


@ConverterRegistry.register
class PDFConverter(BaseConverter):
    """Extract text and metadata from PDF documents."""

    name: ClassVar[str] = "pdf"
    supported_extensions: ClassVar[tuple[str, ...]] = (".pdf",)
    supported_mimetypes: ClassVar[tuple[str, ...]] = ("application/pdf",)
    requires: ClassVar[tuple[str, ...]] = ("pypdf", "pdfplumber")

    def extract(
        self,
        source: Path | BinaryIO | bytes,
        filename: str | None = None,
    ) -> ExtractionResult:
        """Extract content from PDF."""
        import io

        import pdfplumber
        from pypdf import PdfReader

        content_bytes, file_path = self._read_source(source)

        # Extract metadata with pypdf
        pdf_reader = PdfReader(io.BytesIO(content_bytes))
        info = pdf_reader.metadata or {}

        metadata = DocumentMetadata(
            filename=filename or (file_path.name if file_path else "document.pdf"),
            file_path=file_path,
            format_detected="pdf",
            title=info.get("/Title"),
            author=info.get("/Author"),
            subject=info.get("/Subject"),
            page_count=len(pdf_reader.pages),
            converter_used=self.name,
        )

        # Extract text with pdfplumber (better for tables)
        text_parts = []
        markdown_parts = []

        with pdfplumber.open(io.BytesIO(content_bytes)) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text() or ""
                text_parts.append(page_text)

                # Build markdown with page markers
                markdown_parts.append(f"<!-- Page {i} -->\n")
                markdown_parts.append(page_text)

                # Extract tables
                tables = page.extract_tables()
                for table in tables:
                    if table:
                        markdown_parts.append(self._table_to_markdown(table))

        content = "\n\n".join(text_parts)
        content_markdown = "\n\n".join(markdown_parts)

        # Update metadata
        metadata.word_count = len(content.split())
        metadata.char_count = len(content)

        return ExtractionResult(
            success=True,
            content=content,
            content_markdown=content_markdown,
            metadata=metadata,
        )

    def _table_to_markdown(self, table: list[list[str | None]]) -> str:
        """Convert table to markdown format."""
        if not table or not table[0]:
            return ""

        lines = []
        # Header
        header = [str(cell or "") for cell in table[0]]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("| " + " | ".join(["---"] * len(header)) + " |")

        # Rows
        for row in table[1:]:
            cells = [str(cell or "") for cell in row]
            lines.append("| " + " | ".join(cells) + " |")

        return "\n".join(lines)
