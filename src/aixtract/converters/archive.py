"""ZIP archive converter."""
from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import BinaryIO, ClassVar

from aixtract.converters.base import BaseConverter
from aixtract.core.registry import ConverterRegistry
from aixtract.models.result import DocumentMetadata, ExtractionResult


@ConverterRegistry.register
class ZIPConverter(BaseConverter):
    """Extract content from ZIP archives."""

    name: ClassVar[str] = "archive"
    supported_extensions: ClassVar[tuple[str, ...]] = (".zip",)
    supported_mimetypes: ClassVar[tuple[str, ...]] = ("application/zip",)
    requires: ClassVar[tuple[str, ...]] = ()

    def extract(
        self,
        source: Path | BinaryIO | bytes,
        filename: str | None = None,
    ) -> ExtractionResult:
        """Extract content from ZIP archive."""
        content_bytes, file_path = self._read_source(source)

        text_parts = []
        markdown_parts = []
        file_list = []

        with zipfile.ZipFile(io.BytesIO(content_bytes)) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                file_list.append(info.filename)

                # Try to extract text from supported text files
                ext = Path(info.filename).suffix.lower()
                if ext in (".txt", ".md", ".csv", ".json", ".xml", ".log", ".rst"):
                    try:
                        with zf.open(info) as f:
                            content = f.read().decode("utf-8", errors="replace")
                            markdown_parts.append(
                                f"## {info.filename}\n\n{content}"
                            )
                            text_parts.append(content)
                    except Exception:
                        markdown_parts.append(
                            f"## {info.filename}\n\n*[Could not extract]*"
                        )

        content = "\n\n".join(text_parts)
        content_markdown = "\n\n".join(markdown_parts)

        if not content_markdown:
            content_markdown = "# Archive Contents\n\n" + "\n".join(
                f"- {f}" for f in file_list
            )

        return ExtractionResult(
            success=True,
            content=content or "\n".join(file_list),
            content_markdown=content_markdown,
            metadata=DocumentMetadata(
                filename=filename or (file_path.name if file_path else "archive.zip"),
                file_path=file_path,
                format_detected="zip",
                converter_used=self.name,
                extra={"file_count": len(file_list), "files": file_list},
            ),
        )
