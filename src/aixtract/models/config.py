"""Extraction configuration."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class OCRConfig(BaseModel):
    """OCR configuration for image extraction."""

    enabled: bool = True
    language: str = "eng"
    tesseract_cmd: str | None = None
    dpi: int = 300


class AudioConfig(BaseModel):
    """Audio transcription configuration."""

    enabled: bool = True
    model: Literal["tiny", "base", "small", "medium", "large"] = "base"
    language: str | None = None


class ChunkingConfig(BaseModel):
    """Content chunking configuration."""

    enabled: bool = False
    chunk_size: int = 1000
    overlap: int = 100
    respect_sections: bool = True


class ExtractionConfig(BaseModel):
    """Main extraction configuration."""

    # Output settings
    output_format: Literal["markdown", "json", "text"] = "markdown"
    include_metadata: bool = True
    preserve_formatting: bool = True

    # Processing options
    ocr: OCRConfig = Field(default_factory=OCRConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)

    # File handling
    max_file_size_mb: int = 100
    temp_dir: Path | None = None
    cleanup_temp: bool = True

    # Error handling
    raise_on_error: bool = False
    continue_on_partial_failure: bool = True

    # Performance
    timeout_seconds: int = 300
    max_workers: int = 4

    # Plugin options
    disabled_converters: list[str] = Field(default_factory=list)
    converter_options: dict[str, dict[str, Any]] = Field(default_factory=dict)

    # MarkItDown fallback
    markitdown_fallback: bool = True

    @classmethod
    def for_llm(cls) -> "ExtractionConfig":
        """Preset for LLM ingestion."""
        return cls(
            output_format="markdown",
            preserve_formatting=True,
            chunking=ChunkingConfig(enabled=True, chunk_size=2000, overlap=200),
        )

    @classmethod
    def for_rag(cls) -> "ExtractionConfig":
        """Preset for RAG pipelines."""
        return cls(
            output_format="text",
            preserve_formatting=False,
            chunking=ChunkingConfig(enabled=True, chunk_size=512, overlap=50),
        )
