"""Extraction result models."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class OutputFormat(str, Enum):
    """Supported output formats."""
    MARKDOWN = "markdown"
    JSON = "json"
    TEXT = "text"


class DocumentMetadata(BaseModel):
    """Document metadata extracted during processing."""

    filename: str
    file_path: Path | None = None
    file_size: int | None = None
    mime_type: str | None = None
    format_detected: str | None = None

    # Document properties
    title: str | None = None
    author: str | None = None
    subject: str | None = None
    keywords: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    modified_at: datetime | None = None

    # Content statistics
    page_count: int | None = None
    word_count: int | None = None
    char_count: int | None = None

    # Processing info
    extraction_time_ms: float | None = None
    converter_used: str | None = None
    warnings: list[str] = Field(default_factory=list)

    # Custom metadata
    extra: dict[str, Any] = Field(default_factory=dict)


class ContentChunk(BaseModel):
    """A chunk of extracted content for RAG pipelines."""

    index: int
    content: str
    char_start: int
    char_end: int
    token_count_estimate: int | None = None

    # Source tracking
    page_number: int | None = None
    section_title: str | None = None

    # Embedding-ready
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractionResult(BaseModel):
    """Complete extraction result."""

    success: bool
    content: str = ""
    content_markdown: str = ""
    content_json: dict[str, Any] | None = None

    metadata: DocumentMetadata
    chunks: list[ContentChunk] = Field(default_factory=list)

    # Error handling
    error: str | None = None
    partial_content: bool = False

    def to_markdown(self) -> str:
        """Return content as markdown string."""
        return self.content_markdown or self.content

    def to_dict(self) -> dict[str, Any]:
        """Return full result as dictionary."""
        return self.model_dump()

    def get_chunks(
        self,
        chunk_size: int = 1000,
        overlap: int = 100,
    ) -> list[ContentChunk]:
        """Split content into chunks with optional overlap."""
        if self.chunks:
            return self.chunks

        text = self.content
        chunks = []
        start = 0
        index = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))

            # Try to break at sentence boundary
            if end < len(text):
                for sep in ['. ', '.\n', '\n\n', '\n', ' ']:
                    last_sep = text[start:end].rfind(sep)
                    if last_sep > chunk_size // 2:
                        end = start + last_sep + len(sep)
                        break

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(ContentChunk(
                    index=index,
                    content=chunk_text,
                    char_start=start,
                    char_end=end,
                ))
                index += 1

            start = end - overlap if overlap and end < len(text) else end

        return chunks
