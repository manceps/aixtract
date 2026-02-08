"""Text-based format converters (CSV, JSON, XML, TXT).

JSON/TXT parsing patterns adapted from CAMEL-AI
(camel/loaders/base_io.py)
Copyright 2023-2026 @ CAMEL-AI.org. All Rights Reserved.
Licensed under the Apache License, Version 2.0
"""
from __future__ import annotations

import csv
import io
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import BinaryIO, ClassVar

from aixtract.converters.base import BaseConverter
from aixtract.core.registry import ConverterRegistry
from aixtract.models.result import DocumentMetadata, ExtractionResult


@ConverterRegistry.register
class TXTConverter(BaseConverter):
    """Extract content from plain text files."""

    name: ClassVar[str] = "txt"
    supported_extensions: ClassVar[tuple[str, ...]] = (".txt", ".md", ".rst", ".log")
    supported_mimetypes: ClassVar[tuple[str, ...]] = ("text/plain",)
    requires: ClassVar[tuple[str, ...]] = ()

    def extract(
        self,
        source: Path | BinaryIO | bytes,
        filename: str | None = None,
    ) -> ExtractionResult:
        content_bytes, file_path = self._read_source(source)
        text = content_bytes.decode("utf-8", errors="replace")
        text = self._strip_consecutive_newlines(text)

        return ExtractionResult(
            success=True,
            content=text.strip(),
            content_markdown=text.strip(),
            metadata=DocumentMetadata(
                filename=filename or (file_path.name if file_path else "document.txt"),
                file_path=file_path,
                format_detected="txt",
                converter_used=self.name,
                word_count=len(text.split()),
                char_count=len(text),
            ),
        )


@ConverterRegistry.register
class CSVConverter(BaseConverter):
    """Extract content from CSV files."""

    name: ClassVar[str] = "csv"
    supported_extensions: ClassVar[tuple[str, ...]] = (".csv", ".tsv")
    supported_mimetypes: ClassVar[tuple[str, ...]] = ("text/csv",)
    requires: ClassVar[tuple[str, ...]] = ()

    def extract(
        self,
        source: Path | BinaryIO | bytes,
        filename: str | None = None,
    ) -> ExtractionResult:
        content_bytes, file_path = self._read_source(source)
        text = content_bytes.decode("utf-8", errors="replace")

        # Detect TSV by filename or content
        is_tsv = False
        if filename and filename.lower().endswith(".tsv"):
            is_tsv = True
        elif file_path and file_path.suffix.lower() == ".tsv":
            is_tsv = True

        delimiter = "\t" if is_tsv else ","
        reader = csv.reader(io.StringIO(text), delimiter=delimiter)
        rows = list(reader)

        if not rows:
            return ExtractionResult(
                success=True,
                content="",
                content_markdown="",
                metadata=DocumentMetadata(
                    filename=filename or "data.csv",
                    format_detected="csv",
                    converter_used=self.name,
                ),
            )

        # Build markdown table
        headers = rows[0]
        md_lines = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
        ]
        for row in rows[1:]:
            padded = row + [""] * (len(headers) - len(row))
            md_lines.append("| " + " | ".join(padded) + " |")

        content_markdown = "\n".join(md_lines)
        content = "\n".join(["\t".join(row) for row in rows])

        return ExtractionResult(
            success=True,
            content=content,
            content_markdown=content_markdown,
            metadata=DocumentMetadata(
                filename=filename or (file_path.name if file_path else "data.csv"),
                file_path=file_path,
                format_detected="csv",
                converter_used=self.name,
                extra={"row_count": len(rows) - 1, "column_count": len(headers)},
            ),
        )


@ConverterRegistry.register
class JSONConverter(BaseConverter):
    """Extract content from JSON files."""

    name: ClassVar[str] = "json"
    supported_extensions: ClassVar[tuple[str, ...]] = (".json",)
    supported_mimetypes: ClassVar[tuple[str, ...]] = ("application/json",)
    requires: ClassVar[tuple[str, ...]] = ()

    def extract(
        self,
        source: Path | BinaryIO | bytes,
        filename: str | None = None,
    ) -> ExtractionResult:
        content_bytes, file_path = self._read_source(source)
        text = content_bytes.decode("utf-8", errors="replace")

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            return ExtractionResult(
                success=False,
                error=f"Invalid JSON: {e}",
                metadata=DocumentMetadata(
                    filename=filename or (file_path.name if file_path else "data.json"),
                    file_path=file_path,
                    format_detected="json",
                    converter_used=self.name,
                ),
            )

        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        content_markdown = f"```json\n{formatted}\n```"

        return ExtractionResult(
            success=True,
            content=formatted,
            content_markdown=content_markdown,
            content_json=data if isinstance(data, dict) else {"data": data},
            metadata=DocumentMetadata(
                filename=filename or (file_path.name if file_path else "data.json"),
                file_path=file_path,
                format_detected="json",
                converter_used=self.name,
            ),
        )


@ConverterRegistry.register
class XMLConverter(BaseConverter):
    """Extract content from XML files."""

    name: ClassVar[str] = "xml"
    supported_extensions: ClassVar[tuple[str, ...]] = (".xml",)
    supported_mimetypes: ClassVar[tuple[str, ...]] = ("application/xml", "text/xml")
    requires: ClassVar[tuple[str, ...]] = ()

    def extract(
        self,
        source: Path | BinaryIO | bytes,
        filename: str | None = None,
    ) -> ExtractionResult:
        content_bytes, file_path = self._read_source(source)
        text = content_bytes.decode("utf-8", errors="replace")

        try:
            root = ET.fromstring(text)
        except ET.ParseError as e:
            return ExtractionResult(
                success=False,
                error=f"Invalid XML: {e}",
                metadata=DocumentMetadata(
                    filename=filename or (file_path.name if file_path else "data.xml"),
                    file_path=file_path,
                    format_detected="xml",
                    converter_used=self.name,
                ),
            )

        text_parts: list[str] = []
        self._extract_text(root, text_parts)
        content = "\n".join(text_parts)

        content_markdown = f"```xml\n{text}\n```"

        return ExtractionResult(
            success=True,
            content=content,
            content_markdown=content_markdown,
            metadata=DocumentMetadata(
                filename=filename or (file_path.name if file_path else "data.xml"),
                file_path=file_path,
                format_detected="xml",
                converter_used=self.name,
            ),
        )

    def _extract_text(self, element: ET.Element, parts: list[str]) -> None:
        """Recursively extract text from XML elements."""
        if element.text and element.text.strip():
            parts.append(element.text.strip())
        for child in element:
            self._extract_text(child, parts)
        if element.tail and element.tail.strip():
            parts.append(element.tail.strip())
