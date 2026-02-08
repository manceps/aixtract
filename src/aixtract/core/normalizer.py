"""Output normalization for extraction results."""
from __future__ import annotations

from aixtract.utils.markdown import clean_markdown


class OutputNormalizer:
    """Normalize extraction output across formats."""

    @staticmethod
    def normalize_content(text: str) -> str:
        """Normalize extracted text content."""
        return clean_markdown(text)

    @staticmethod
    def compute_statistics(content: str) -> dict[str, int]:
        """Compute content statistics."""
        return {
            "word_count": len(content.split()),
            "char_count": len(content),
            "line_count": content.count("\n") + 1,
        }
