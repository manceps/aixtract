"""HTML document converter.

HTML parsing pattern adapted from CAMEL-AI HtmlFile
(camel/loaders/base_io.py)
Copyright 2023-2026 @ CAMEL-AI.org. All Rights Reserved.
Licensed under the Apache License, Version 2.0
"""
from __future__ import annotations

from pathlib import Path
from typing import BinaryIO, ClassVar

from aixtract.converters.base import BaseConverter
from aixtract.core.registry import ConverterRegistry
from aixtract.models.result import DocumentMetadata, ExtractionResult


@ConverterRegistry.register
class HTMLConverter(BaseConverter):
    """Extract content from HTML documents."""

    name: ClassVar[str] = "html"
    supported_extensions: ClassVar[tuple[str, ...]] = (".html", ".htm")
    supported_mimetypes: ClassVar[tuple[str, ...]] = ("text/html",)
    requires: ClassVar[tuple[str, ...]] = ("bs4",)

    def extract(
        self,
        source: Path | BinaryIO | bytes,
        filename: str | None = None,
    ) -> ExtractionResult:
        """Extract content from HTML."""
        from bs4 import BeautifulSoup

        content_bytes, file_path = self._read_source(source)
        html_content = content_bytes.decode("utf-8", errors="replace")

        soup = BeautifulSoup(html_content, "html.parser")

        # Extract title
        title = soup.title.string if soup.title else None

        # Extract text content
        text = soup.get_text(separator="\n", strip=True)
        text = self._strip_consecutive_newlines(text)

        # Build markdown from HTML structure
        markdown_parts = []
        if title:
            markdown_parts.append(f"# {title}\n")

        for element in soup.find_all(
            ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "pre", "code"]
        ):
            tag = element.name
            if tag.startswith("h") and len(tag) == 2:
                level = int(tag[1])
                markdown_parts.append("#" * level + " " + element.get_text(strip=True))
            elif tag == "p":
                p_text = element.get_text(strip=True)
                if p_text:
                    markdown_parts.append(p_text)
            elif tag == "li":
                markdown_parts.append("- " + element.get_text(strip=True))
            elif tag in ("pre", "code"):
                markdown_parts.append(f"```\n{element.get_text()}\n```")

        content_markdown = "\n\n".join(markdown_parts) if markdown_parts else text

        metadata = DocumentMetadata(
            filename=filename or (file_path.name if file_path else "document.html"),
            file_path=file_path,
            format_detected="html",
            title=title,
            converter_used=self.name,
            word_count=len(text.split()),
            char_count=len(text),
        )

        return ExtractionResult(
            success=True,
            content=text,
            content_markdown=content_markdown,
            metadata=metadata,
        )
