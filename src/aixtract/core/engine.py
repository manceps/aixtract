"""Main extraction engine."""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO, Iterator

from aixtract.core.detector import FormatDetector
from aixtract.core.normalizer import OutputNormalizer
from aixtract.core.registry import ConverterRegistry
from aixtract.models.result import DocumentMetadata, ExtractionResult
from aixtract.models.config import ExtractionConfig

if TYPE_CHECKING:
    from aixtract.converters.base import BaseConverter


class ExtractionEngine:
    """Main document extraction engine."""

    def __init__(self, config: ExtractionConfig | None = None) -> None:
        self.config = config or ExtractionConfig()
        self._detector = FormatDetector()
        # Ensure converters are registered
        import aixtract.converters  # noqa: F401

    def extract(
        self,
        source: str | Path | BinaryIO | bytes,
        filename: str | None = None,
    ) -> ExtractionResult:
        """Extract content from a single document."""
        start_time = time.perf_counter()

        # Normalize source
        if isinstance(source, str):
            if source.startswith(('http://', 'https://')):
                return self._extract_from_url(source, filename)
            source = Path(source)

        # Get file info
        if isinstance(source, Path):
            if not source.exists():
                return self._error_result(f"File not found: {source}", filename)
            filename = filename or source.name
            file_size = source.stat().st_size
            content_bytes = source.read_bytes()
        elif isinstance(source, bytes):
            content_bytes = source
            file_size = len(source)
        else:
            content_bytes = source.read()
            file_size = len(content_bytes)

        # Check file size
        max_size = self.config.max_file_size_mb * 1024 * 1024
        if file_size > max_size:
            return self._error_result(
                f"File exceeds max size ({file_size} > {max_size})",
                filename,
            )

        # Detect format
        extension, mimetype = self._detector.detect(
            content=content_bytes, filename=filename
        )

        # Get converter
        converter = ConverterRegistry.get_converter(
            extension=extension,
            mimetype=mimetype,
            config=self.config,
        )

        if not converter:
            # Try markitdown fallback
            if self.config.markitdown_fallback:
                try:
                    from aixtract.converters._markitdown import MarkItDownBackend
                    backend = MarkItDownBackend()
                    if filename and backend.can_handle(filename):
                        import tempfile, os
                        suffix = Path(filename).suffix
                        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                            tmp.write(content_bytes)
                            tmp_path = tmp.name
                        try:
                            result = backend.convert(tmp_path)
                            result.metadata.file_size = file_size
                            result.metadata.mime_type = mimetype
                            result.metadata.extraction_time_ms = (
                                time.perf_counter() - start_time
                            ) * 1000
                            return result
                        finally:
                            os.unlink(tmp_path)
                except Exception:
                    pass

            return self._error_result(
                f"No converter for format: {extension or mimetype}",
                filename,
            )

        # Extract
        try:
            result = converter.extract(content_bytes, filename)

            # Normalize output
            result.content = OutputNormalizer.normalize_content(result.content)
            result.content_markdown = OutputNormalizer.normalize_content(
                result.content_markdown
            )

            # Update metadata
            result.metadata.file_size = file_size
            result.metadata.mime_type = mimetype
            result.metadata.extraction_time_ms = (
                time.perf_counter() - start_time
            ) * 1000

            # Generate chunks if configured
            if self.config.chunking.enabled and not result.chunks:
                from aixtract.utils.chunking import ContentChunker
                chunker = ContentChunker(
                    chunk_size=self.config.chunking.chunk_size,
                    overlap=self.config.chunking.overlap,
                )
                result.chunks = chunker.chunk(
                    result.content,
                    respect_structure=self.config.chunking.respect_sections,
                )

            return result

        except Exception as e:
            if self.config.raise_on_error:
                raise
            return self._error_result(str(e), filename)

    def extract_batch(
        self,
        sources: list[str | Path],
        show_progress: bool = True,
        skip_failed: bool = False,
    ) -> Iterator[tuple[str | Path, ExtractionResult]]:
        """Extract from multiple documents in parallel."""
        from rich.progress import Progress, SpinnerColumn, TextColumn

        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = {
                executor.submit(self.extract, src): src
                for src in sources
            }

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                disable=not show_progress,
            ) as progress:
                task = progress.add_task("Extracting...", total=len(sources))
                for future in as_completed(futures):
                    source = futures[future]
                    try:
                        result = future.result()
                    except Exception as e:
                        if skip_failed:
                            progress.advance(task)
                            continue
                        result = self._error_result(str(e), str(source))
                    progress.advance(task)
                    yield source, result

    def _extract_from_url(
        self,
        url: str,
        filename: str | None = None,
    ) -> ExtractionResult:
        """Download and extract from URL."""
        import httpx

        try:
            with httpx.Client(timeout=self.config.timeout_seconds) as client:
                response = client.get(url)
                response.raise_for_status()

                if not filename:
                    filename = Path(url).name
                    if 'content-disposition' in response.headers:
                        cd = response.headers['content-disposition']
                        if 'filename=' in cd:
                            filename = cd.split('filename=')[1].strip('"\'')

                return self.extract(response.content, filename)

        except Exception as e:
            return self._error_result(f"URL fetch failed: {e}", filename)

    def _error_result(
        self,
        error: str,
        filename: str | None,
    ) -> ExtractionResult:
        """Create error result."""
        return ExtractionResult(
            success=False,
            error=error,
            metadata=DocumentMetadata(
                filename=filename or "unknown",
            ),
        )


# Convenience function
def extract(
    source: str | Path | BinaryIO | bytes,
    filename: str | None = None,
    config: ExtractionConfig | None = None,
) -> ExtractionResult:
    """Extract content from a document.

    This is the main entry point for the library.

    Args:
        source: File path, URL, file-like object, or raw bytes
        filename: Original filename (for format detection)
        config: Extraction configuration

    Returns:
        ExtractionResult with content and metadata
    """
    engine = ExtractionEngine(config)
    return engine.extract(source, filename)
