"""Tests for Pydantic models in src/aixtract/models/."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from aixtract.models.result import (
    ContentChunk,
    DocumentMetadata,
    ExtractionResult,
    OutputFormat,
)
from aixtract.models.config import (
    AudioConfig,
    ChunkingConfig,
    ExtractionConfig,
    OCRConfig,
)


# ---------------------------------------------------------------------------
# OutputFormat enum
# ---------------------------------------------------------------------------


class TestOutputFormat:
    """Tests for the OutputFormat enum."""

    def test_has_markdown_value(self):
        assert OutputFormat.MARKDOWN == "markdown"

    def test_has_json_value(self):
        assert OutputFormat.JSON == "json"

    def test_has_text_value(self):
        assert OutputFormat.TEXT == "text"

    def test_is_string_enum(self):
        assert isinstance(OutputFormat.MARKDOWN, str)
        assert isinstance(OutputFormat.JSON, str)
        assert isinstance(OutputFormat.TEXT, str)

    def test_enum_members_count(self):
        assert len(OutputFormat) == 3


# ---------------------------------------------------------------------------
# DocumentMetadata
# ---------------------------------------------------------------------------


class TestDocumentMetadata:
    """Tests for the DocumentMetadata model."""

    def test_creation_with_required_field_only(self):
        meta = DocumentMetadata(filename="test.pdf")
        assert meta.filename == "test.pdf"

    def test_optional_fields_default_to_none(self):
        meta = DocumentMetadata(filename="test.pdf")
        assert meta.file_path is None
        assert meta.file_size is None
        assert meta.mime_type is None
        assert meta.format_detected is None
        assert meta.title is None
        assert meta.author is None
        assert meta.subject is None
        assert meta.created_at is None
        assert meta.modified_at is None
        assert meta.page_count is None
        assert meta.word_count is None
        assert meta.char_count is None
        assert meta.extraction_time_ms is None
        assert meta.converter_used is None

    def test_list_fields_default_to_empty(self):
        meta = DocumentMetadata(filename="test.pdf")
        assert meta.keywords == []
        assert meta.warnings == []

    def test_extra_dict_defaults_to_empty(self):
        meta = DocumentMetadata(filename="test.pdf")
        assert meta.extra == {}

    def test_creation_with_all_fields(self):
        now = datetime.now()
        meta = DocumentMetadata(
            filename="report.pdf",
            file_path=Path("/tmp/report.pdf"),
            file_size=1024,
            mime_type="application/pdf",
            format_detected="pdf",
            title="Annual Report",
            author="Jane Doe",
            subject="Finance",
            keywords=["finance", "annual"],
            created_at=now,
            modified_at=now,
            page_count=10,
            word_count=5000,
            char_count=30000,
            extraction_time_ms=150.5,
            converter_used="pdf",
            warnings=["Low quality scan"],
            extra={"custom_key": "value"},
        )
        assert meta.filename == "report.pdf"
        assert meta.file_path == Path("/tmp/report.pdf")
        assert meta.file_size == 1024
        assert meta.mime_type == "application/pdf"
        assert meta.format_detected == "pdf"
        assert meta.title == "Annual Report"
        assert meta.author == "Jane Doe"
        assert meta.subject == "Finance"
        assert meta.keywords == ["finance", "annual"]
        assert meta.created_at == now
        assert meta.modified_at == now
        assert meta.page_count == 10
        assert meta.word_count == 5000
        assert meta.char_count == 30000
        assert meta.extraction_time_ms == 150.5
        assert meta.converter_used == "pdf"
        assert meta.warnings == ["Low quality scan"]
        assert meta.extra == {"custom_key": "value"}


# ---------------------------------------------------------------------------
# ContentChunk
# ---------------------------------------------------------------------------


class TestContentChunk:
    """Tests for the ContentChunk model."""

    def test_creation_with_required_fields(self):
        chunk = ContentChunk(
            index=0,
            content="Hello world",
            char_start=0,
            char_end=11,
        )
        assert chunk.index == 0
        assert chunk.content == "Hello world"
        assert chunk.char_start == 0
        assert chunk.char_end == 11

    def test_optional_fields_default_to_none(self):
        chunk = ContentChunk(index=0, content="text", char_start=0, char_end=4)
        assert chunk.token_count_estimate is None
        assert chunk.page_number is None
        assert chunk.section_title is None

    def test_metadata_defaults_to_empty_dict(self):
        chunk = ContentChunk(index=0, content="text", char_start=0, char_end=4)
        assert chunk.metadata == {}

    def test_creation_with_all_fields(self):
        chunk = ContentChunk(
            index=2,
            content="Some content here",
            char_start=100,
            char_end=117,
            token_count_estimate=5,
            page_number=3,
            section_title="Introduction",
            metadata={"source": "pdf"},
        )
        assert chunk.index == 2
        assert chunk.token_count_estimate == 5
        assert chunk.page_number == 3
        assert chunk.section_title == "Introduction"
        assert chunk.metadata == {"source": "pdf"}


# ---------------------------------------------------------------------------
# ExtractionResult
# ---------------------------------------------------------------------------


class TestExtractionResult:
    """Tests for the ExtractionResult model."""

    def _make_metadata(self, filename: str = "test.txt") -> DocumentMetadata:
        return DocumentMetadata(filename=filename)

    def test_creation_success(self):
        result = ExtractionResult(
            success=True,
            content="Hello world",
            content_markdown="# Hello world",
            metadata=self._make_metadata(),
        )
        assert result.success is True
        assert result.content == "Hello world"
        assert result.content_markdown == "# Hello world"
        assert result.error is None

    def test_creation_failure(self):
        result = ExtractionResult(
            success=False,
            error="File not found",
            metadata=self._make_metadata(),
        )
        assert result.success is False
        assert result.error == "File not found"
        assert result.content == ""

    def test_to_markdown_returns_content_markdown_when_set(self):
        result = ExtractionResult(
            success=True,
            content="plain text",
            content_markdown="# Markdown heading",
            metadata=self._make_metadata(),
        )
        assert result.to_markdown() == "# Markdown heading"

    def test_to_markdown_falls_back_to_content(self):
        result = ExtractionResult(
            success=True,
            content="plain text",
            content_markdown="",
            metadata=self._make_metadata(),
        )
        assert result.to_markdown() == "plain text"

    def test_to_dict_returns_model_dump(self):
        result = ExtractionResult(
            success=True,
            content="text",
            metadata=self._make_metadata(),
        )
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["success"] is True
        assert d["content"] == "text"
        assert "metadata" in d
        assert d["metadata"]["filename"] == "test.txt"

    def test_content_json_field(self):
        result = ExtractionResult(
            success=True,
            content='{"key": "val"}',
            content_json={"key": "val"},
            metadata=self._make_metadata(),
        )
        assert result.content_json == {"key": "val"}

    def test_content_json_defaults_to_none(self):
        result = ExtractionResult(
            success=True,
            content="text",
            metadata=self._make_metadata(),
        )
        assert result.content_json is None

    def test_chunks_defaults_to_empty_list(self):
        result = ExtractionResult(
            success=True,
            content="text",
            metadata=self._make_metadata(),
        )
        assert result.chunks == []

    def test_partial_content_defaults_to_false(self):
        result = ExtractionResult(
            success=True,
            content="text",
            metadata=self._make_metadata(),
        )
        assert result.partial_content is False

    # ---- get_chunks tests ----

    def test_get_chunks_splits_content(self):
        long_text = "This is a sentence. " * 200  # ~4000 chars
        result = ExtractionResult(
            success=True,
            content=long_text,
            metadata=self._make_metadata(),
        )
        chunks = result.get_chunks(chunk_size=500)
        assert len(chunks) > 1
        for chunk in chunks:
            assert isinstance(chunk, ContentChunk)
            assert chunk.content
            assert chunk.char_start >= 0
            assert chunk.char_end > chunk.char_start

    def test_get_chunks_returns_existing_chunks_if_populated(self):
        existing = [
            ContentChunk(index=0, content="pre-existing", char_start=0, char_end=12),
        ]
        result = ExtractionResult(
            success=True,
            content="This content should not be chunked",
            metadata=self._make_metadata(),
            chunks=existing,
        )
        chunks = result.get_chunks(chunk_size=10)
        assert len(chunks) == 1
        assert chunks[0].content == "pre-existing"

    def test_get_chunks_with_overlap(self):
        # Create text with clear sentence boundaries
        sentences = [f"Sentence number {i} here. " for i in range(100)]
        long_text = "".join(sentences)
        result = ExtractionResult(
            success=True,
            content=long_text,
            metadata=self._make_metadata(),
        )
        chunks = result.get_chunks(chunk_size=200, overlap=50)
        assert len(chunks) > 1
        # With overlap, later chunks should start before the previous chunk ends
        if len(chunks) >= 2:
            assert chunks[1].char_start < chunks[0].char_end

    def test_get_chunks_sentence_boundary_detection(self):
        # Use enough text and a chunk_size that is larger than the default overlap
        sentences = [f"Sentence number {i} is here. " for i in range(50)]
        text = "".join(sentences)
        result = ExtractionResult(
            success=True,
            content=text,
            metadata=self._make_metadata(),
        )
        chunks = result.get_chunks(chunk_size=300, overlap=50)
        # The chunker tries to break at sentence boundaries (". ")
        assert len(chunks) > 1
        for chunk in chunks:
            # Each chunk's content should be non-empty and stripped
            assert chunk.content.strip() == chunk.content

    def test_get_chunks_empty_content(self):
        result = ExtractionResult(
            success=True,
            content="",
            metadata=self._make_metadata(),
        )
        chunks = result.get_chunks()
        assert chunks == []

    def test_get_chunks_indices_are_sequential(self):
        long_text = "Word " * 500
        result = ExtractionResult(
            success=True,
            content=long_text,
            metadata=self._make_metadata(),
        )
        chunks = result.get_chunks(chunk_size=200)
        for i, chunk in enumerate(chunks):
            assert chunk.index == i


# ---------------------------------------------------------------------------
# OCRConfig
# ---------------------------------------------------------------------------


class TestOCRConfig:
    """Tests for the OCRConfig model."""

    def test_defaults(self):
        config = OCRConfig()
        assert config.enabled is True
        assert config.language == "eng"
        assert config.dpi == 300
        assert config.tesseract_cmd is None

    def test_custom_values(self):
        config = OCRConfig(enabled=False, language="deu", dpi=150)
        assert config.enabled is False
        assert config.language == "deu"
        assert config.dpi == 150


# ---------------------------------------------------------------------------
# AudioConfig
# ---------------------------------------------------------------------------


class TestAudioConfig:
    """Tests for the AudioConfig model."""

    def test_defaults(self):
        config = AudioConfig()
        assert config.enabled is True
        assert config.model == "base"
        assert config.language is None

    def test_custom_values(self):
        config = AudioConfig(model="large", language="en")
        assert config.model == "large"
        assert config.language == "en"


# ---------------------------------------------------------------------------
# ChunkingConfig
# ---------------------------------------------------------------------------


class TestChunkingConfig:
    """Tests for the ChunkingConfig model."""

    def test_defaults(self):
        config = ChunkingConfig()
        assert config.enabled is False
        assert config.chunk_size == 1000
        assert config.overlap == 100
        assert config.respect_sections is True

    def test_custom_values(self):
        config = ChunkingConfig(enabled=True, chunk_size=512, overlap=50)
        assert config.enabled is True
        assert config.chunk_size == 512
        assert config.overlap == 50


# ---------------------------------------------------------------------------
# ExtractionConfig
# ---------------------------------------------------------------------------


class TestExtractionConfig:
    """Tests for the ExtractionConfig model."""

    def test_defaults(self):
        config = ExtractionConfig()
        assert config.output_format == "markdown"
        assert config.markitdown_fallback is True
        assert config.max_file_size_mb == 100
        assert config.max_workers == 4
        assert config.include_metadata is True
        assert config.preserve_formatting is True
        assert config.raise_on_error is False
        assert config.continue_on_partial_failure is True
        assert config.timeout_seconds == 300
        assert config.cleanup_temp is True
        assert config.temp_dir is None

    def test_default_sub_configs(self):
        config = ExtractionConfig()
        assert isinstance(config.ocr, OCRConfig)
        assert isinstance(config.audio, AudioConfig)
        assert isinstance(config.chunking, ChunkingConfig)

    def test_disabled_converters_default_empty(self):
        config = ExtractionConfig()
        assert config.disabled_converters == []

    def test_disabled_converters_list(self):
        config = ExtractionConfig(disabled_converters=["pdf", "docx"])
        assert "pdf" in config.disabled_converters
        assert "docx" in config.disabled_converters
        assert len(config.disabled_converters) == 2

    def test_converter_options_default_empty(self):
        config = ExtractionConfig()
        assert config.converter_options == {}

    def test_for_llm_preset(self):
        config = ExtractionConfig.for_llm()
        assert config.output_format == "markdown"
        assert config.preserve_formatting is True
        assert config.chunking.enabled is True
        assert config.chunking.chunk_size == 2000
        assert config.chunking.overlap == 200

    def test_for_rag_preset(self):
        config = ExtractionConfig.for_rag()
        assert config.output_format == "text"
        assert config.preserve_formatting is False
        assert config.chunking.enabled is True
        assert config.chunking.chunk_size == 512
        assert config.chunking.overlap == 50

    def test_for_llm_preserves_other_defaults(self):
        config = ExtractionConfig.for_llm()
        assert config.max_file_size_mb == 100
        assert config.markitdown_fallback is True
        assert config.max_workers == 4

    def test_for_rag_preserves_other_defaults(self):
        config = ExtractionConfig.for_rag()
        assert config.max_file_size_mb == 100
        assert config.markitdown_fallback is True
        assert config.max_workers == 4
