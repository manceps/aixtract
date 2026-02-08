"""Tests for core modules in src/aixtract/core/."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from aixtract.core.registry import ConverterRegistry
from aixtract.core.detector import FormatDetector
from aixtract.core.normalizer import OutputNormalizer
from aixtract.core.engine import ExtractionEngine, extract
from aixtract.models.config import ExtractionConfig
from aixtract.models.result import ContentChunk, DocumentMetadata, ExtractionResult

# Trigger converter registration (normally done by ExtractionEngine.__init__)
import aixtract.converters  # noqa: F401


# ===========================================================================
# ConverterRegistry
# ===========================================================================


class TestConverterRegistry:
    """Tests for the ConverterRegistry."""

    def test_register_decorator_registers_a_converter(self):
        # The text converter should already be registered from imports
        assert "txt" in ConverterRegistry._converters

    def test_get_converter_finds_by_extension(self):
        converter = ConverterRegistry.get_converter(extension=".txt")
        assert converter is not None
        assert converter.name == "txt"

    def test_get_converter_finds_by_extension_without_dot(self):
        converter = ConverterRegistry.get_converter(extension="txt")
        assert converter is not None
        assert converter.name == "txt"

    def test_get_converter_finds_csv_by_extension(self):
        converter = ConverterRegistry.get_converter(extension=".csv")
        assert converter is not None
        assert converter.name == "csv"

    def test_get_converter_finds_json_by_extension(self):
        converter = ConverterRegistry.get_converter(extension=".json")
        assert converter is not None
        assert converter.name == "json"

    def test_get_converter_finds_xml_by_extension(self):
        converter = ConverterRegistry.get_converter(extension=".xml")
        assert converter is not None
        assert converter.name == "xml"

    def test_get_converter_finds_by_mimetype(self):
        converter = ConverterRegistry.get_converter(mimetype="text/plain")
        assert converter is not None
        assert converter.name == "txt"

    def test_get_converter_finds_csv_by_mimetype(self):
        converter = ConverterRegistry.get_converter(mimetype="text/csv")
        assert converter is not None
        assert converter.name == "csv"

    def test_get_converter_returns_none_for_unknown_extension(self):
        converter = ConverterRegistry.get_converter(extension=".xyzabc")
        assert converter is None

    def test_get_converter_returns_none_for_unknown_mimetype(self):
        converter = ConverterRegistry.get_converter(mimetype="application/x-unknown-type")
        assert converter is None

    def test_get_converter_respects_disabled_converters(self):
        config = ExtractionConfig(disabled_converters=["txt"])
        converter = ConverterRegistry.get_converter(extension=".txt", config=config)
        assert converter is None

    def test_get_converter_disabled_does_not_affect_other_converters(self):
        config = ExtractionConfig(disabled_converters=["txt"])
        converter = ConverterRegistry.get_converter(extension=".csv", config=config)
        assert converter is not None
        assert converter.name == "csv"

    def test_list_converters_returns_list_of_dicts(self):
        converters = ConverterRegistry.list_converters()
        assert isinstance(converters, list)
        assert len(converters) > 0
        for entry in converters:
            assert "name" in entry
            assert "extensions" in entry
            assert "mimetypes" in entry
            assert "requires" in entry

    def test_list_converters_contains_txt(self):
        converters = ConverterRegistry.list_converters()
        names = [c["name"] for c in converters]
        assert "txt" in names

    def test_get_supported_extensions_returns_list_of_strings(self):
        extensions = ConverterRegistry.get_supported_extensions()
        assert isinstance(extensions, list)
        assert len(extensions) > 0
        for ext in extensions:
            assert isinstance(ext, str)

    def test_get_supported_extensions_includes_txt(self):
        extensions = ConverterRegistry.get_supported_extensions()
        assert "txt" in extensions

    def test_get_supported_extensions_includes_csv(self):
        extensions = ConverterRegistry.get_supported_extensions()
        assert "csv" in extensions

    def test_extension_lookup_is_case_insensitive(self):
        converter = ConverterRegistry.get_converter(extension=".TXT")
        assert converter is not None
        assert converter.name == "txt"


# ===========================================================================
# FormatDetector
# ===========================================================================


class TestFormatDetector:
    """Tests for the FormatDetector."""

    def test_detect_with_filename_returns_extension(self):
        detector = FormatDetector()
        ext, mime = detector.detect(filename="document.pdf")
        assert ext == ".pdf"
        assert mime is None

    def test_detect_with_content_returns_mimetype(self):
        detector = FormatDetector()
        content = b"Hello, this is plain text content."
        ext, mime = detector.detect(content=content)
        assert ext is None
        assert mime is not None
        assert isinstance(mime, str)

    def test_detect_with_both_returns_both(self):
        detector = FormatDetector()
        content = b"Hello, this is plain text content."
        ext, mime = detector.detect(content=content, filename="note.txt")
        assert ext == ".txt"
        assert mime is not None

    def test_detect_with_neither_returns_nones(self):
        detector = FormatDetector()
        ext, mime = detector.detect()
        assert ext is None
        assert mime is None

    def test_detect_extension_is_lowercase(self):
        detector = FormatDetector()
        ext, _ = detector.detect(filename="FILE.PDF")
        assert ext == ".pdf"

    def test_detect_various_extensions(self):
        detector = FormatDetector()
        test_cases = {
            "doc.docx": ".docx",
            "data.json": ".json",
            "page.html": ".html",
            "sheet.xlsx": ".xlsx",
        }
        for filename, expected_ext in test_cases.items():
            ext, _ = detector.detect(filename=filename)
            assert ext == expected_ext, f"Expected {expected_ext} for {filename}"


# ===========================================================================
# OutputNormalizer
# ===========================================================================


class TestOutputNormalizer:
    """Tests for the OutputNormalizer."""

    def test_normalize_content_cleans_markdown(self):
        text = "Hello\n\n\n\n\nWorld"
        result = OutputNormalizer.normalize_content(text)
        # clean_markdown collapses 3+ newlines to 2
        assert "\n\n\n" not in result
        assert "Hello" in result
        assert "World" in result

    def test_normalize_content_normalizes_line_endings(self):
        text = "Line1\r\nLine2\rLine3\n"
        result = OutputNormalizer.normalize_content(text)
        assert "\r" not in result

    def test_compute_statistics_returns_correct_keys(self):
        stats = OutputNormalizer.compute_statistics("Hello world\nSecond line")
        assert "word_count" in stats
        assert "char_count" in stats
        assert "line_count" in stats

    def test_compute_statistics_word_count(self):
        stats = OutputNormalizer.compute_statistics("one two three four")
        assert stats["word_count"] == 4

    def test_compute_statistics_char_count(self):
        text = "abcde"
        stats = OutputNormalizer.compute_statistics(text)
        assert stats["char_count"] == 5

    def test_compute_statistics_line_count(self):
        text = "line1\nline2\nline3"
        stats = OutputNormalizer.compute_statistics(text)
        assert stats["line_count"] == 3

    def test_compute_statistics_single_line(self):
        stats = OutputNormalizer.compute_statistics("single line")
        assert stats["line_count"] == 1

    def test_compute_statistics_empty_string(self):
        stats = OutputNormalizer.compute_statistics("")
        assert stats["word_count"] == 0
        assert stats["char_count"] == 0
        assert stats["line_count"] == 1  # count("\n") + 1 = 0 + 1


# ===========================================================================
# ExtractionEngine
# ===========================================================================


class TestExtractionEngine:
    """Tests for the ExtractionEngine."""

    def test_init_creates_engine_with_default_config(self):
        engine = ExtractionEngine()
        assert isinstance(engine.config, ExtractionConfig)
        assert engine.config.output_format == "markdown"

    def test_init_accepts_custom_config(self):
        config = ExtractionConfig(max_file_size_mb=50)
        engine = ExtractionEngine(config)
        assert engine.config.max_file_size_mb == 50

    def test_extract_with_text_file(self, tmp_path):
        txt_file = tmp_path / "hello.txt"
        txt_file.write_text("Hello, world!")
        engine = ExtractionEngine()
        result = engine.extract(txt_file)
        assert isinstance(result, ExtractionResult)
        assert result.success is True
        assert "Hello" in result.content
        assert result.metadata.filename == "hello.txt"

    def test_extract_with_path_string(self, tmp_path):
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Test content")
        engine = ExtractionEngine()
        result = engine.extract(str(txt_file))
        assert result.success is True
        assert "Test content" in result.content

    def test_extract_with_bytes_and_filename(self):
        content = b"Bytes content here"
        engine = ExtractionEngine()
        result = engine.extract(content, filename="data.txt")
        assert result.success is True
        assert "Bytes content" in result.content
        assert result.metadata.file_size == len(content)

    def test_extract_with_nonexistent_file(self):
        engine = ExtractionEngine()
        result = engine.extract(Path("/nonexistent/path/fake.txt"))
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_extract_with_oversized_file(self, tmp_path):
        # Create a config with 0 MB limit to trigger oversize error
        config = ExtractionConfig(max_file_size_mb=0)
        engine = ExtractionEngine(config)
        txt_file = tmp_path / "big.txt"
        txt_file.write_text("a")
        result = engine.extract(txt_file)
        assert result.success is False
        assert "exceeds max size" in result.error.lower() or "max size" in result.error.lower()

    def test_extract_with_chunking_enabled(self, tmp_path):
        config = ExtractionConfig.for_llm()
        engine = ExtractionEngine(config)
        # Create a file with enough content to produce chunks
        txt_file = tmp_path / "long.txt"
        txt_file.write_text("This is a sentence with content. " * 500)
        result = engine.extract(txt_file)
        assert result.success is True
        assert len(result.chunks) > 0
        for chunk in result.chunks:
            assert isinstance(chunk, ContentChunk)

    def test_extract_populates_metadata(self, tmp_path):
        txt_file = tmp_path / "meta_test.txt"
        txt_file.write_text("Some text content")
        engine = ExtractionEngine()
        result = engine.extract(txt_file)
        assert result.metadata.file_size is not None
        assert result.metadata.file_size > 0
        assert result.metadata.mime_type is not None
        assert result.metadata.extraction_time_ms is not None
        assert result.metadata.extraction_time_ms >= 0

    def test_error_result_creates_proper_error(self):
        engine = ExtractionEngine()
        result = engine._error_result("Something went wrong", "test.pdf")
        assert result.success is False
        assert result.error == "Something went wrong"
        assert result.metadata.filename == "test.pdf"

    def test_error_result_with_none_filename(self):
        engine = ExtractionEngine()
        result = engine._error_result("Error occurred", None)
        assert result.success is False
        assert result.metadata.filename == "unknown"


# ===========================================================================
# extract() convenience function
# ===========================================================================


class TestExtractConvenience:
    """Tests for the extract() convenience function."""

    def test_extract_function_works_with_file(self, tmp_path):
        txt_file = tmp_path / "convenience.txt"
        txt_file.write_text("Convenience function test")
        result = extract(txt_file)
        assert isinstance(result, ExtractionResult)
        assert result.success is True
        assert "Convenience" in result.content

    def test_extract_function_works_with_bytes(self):
        result = extract(b"Bytes via convenience", filename="test.txt")
        assert result.success is True
        assert "Bytes" in result.content

    def test_extract_function_accepts_config(self, tmp_path):
        txt_file = tmp_path / "config.txt"
        txt_file.write_text("With config")
        config = ExtractionConfig(max_file_size_mb=50)
        result = extract(txt_file, config=config)
        assert result.success is True

    def test_extract_function_nonexistent_file(self):
        result = extract(Path("/does/not/exist.txt"))
        assert result.success is False
        assert result.error is not None
