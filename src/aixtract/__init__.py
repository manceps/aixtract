"""AIXtract - Enterprise document extraction for LLM/NLP pipelines."""
from aixtract.core.engine import ExtractionEngine, extract
from aixtract.models.config import (
    AudioConfig,
    ChunkingConfig,
    ExtractionConfig,
    OCRConfig,
)
from aixtract.models.result import (
    ContentChunk,
    DocumentMetadata,
    ExtractionResult,
    OutputFormat,
)

try:
    from aixtract._version import __version__
except ImportError:
    __version__ = "0.0.0-dev"

__all__ = [
    "__version__",
    "extract",
    "ExtractionEngine",
    "ExtractionConfig",
    "ExtractionResult",
    "DocumentMetadata",
    "ContentChunk",
    "OutputFormat",
    "ChunkingConfig",
    "OCRConfig",
    "AudioConfig",
]
