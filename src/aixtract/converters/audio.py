"""Audio converter with Whisper transcription."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import BinaryIO, ClassVar

from aixtract.converters.base import BaseConverter
from aixtract.core.registry import ConverterRegistry
from aixtract.models.result import DocumentMetadata, ExtractionResult


@ConverterRegistry.register
class AudioConverter(BaseConverter):
    """Transcribe audio files using Whisper."""

    name: ClassVar[str] = "audio"
    supported_extensions: ClassVar[tuple[str, ...]] = (
        ".mp3", ".wav", ".m4a", ".flac", ".ogg",
    )
    supported_mimetypes: ClassVar[tuple[str, ...]] = (
        "audio/mpeg", "audio/wav", "audio/x-wav", "audio/flac", "audio/ogg",
    )
    requires: ClassVar[tuple[str, ...]] = ("whisper",)

    def extract(
        self,
        source: Path | BinaryIO | bytes,
        filename: str | None = None,
    ) -> ExtractionResult:
        """Transcribe audio file."""
        import whisper

        content_bytes, file_path = self._read_source(source)

        # Whisper needs a file path
        suffix = Path(filename).suffix if filename else ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content_bytes)
            tmp_path = tmp.name

        try:
            model = whisper.load_model(self.config.audio.model)
            result = model.transcribe(
                tmp_path,
                language=self.config.audio.language,
            )
        finally:
            os.unlink(tmp_path)

        text = result["text"].strip()

        return ExtractionResult(
            success=True,
            content=text,
            content_markdown=text,
            metadata=DocumentMetadata(
                filename=filename or (file_path.name if file_path else "audio.wav"),
                file_path=file_path,
                format_detected="audio",
                converter_used=self.name,
                word_count=len(text.split()),
                char_count=len(text),
                extra={
                    "language_detected": result.get("language"),
                    "whisper_model": self.config.audio.model,
                },
            ),
        )
