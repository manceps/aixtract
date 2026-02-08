"""Token estimation utilities.

Tiktoken integration adapted from CAMEL-AI token_counting module
(camel/utils/token_counting.py)
Copyright 2023-2026 @ CAMEL-AI.org. All Rights Reserved.
Licensed under the Apache License, Version 2.0
"""
from __future__ import annotations

# Approximate characters per token for different encodings
CHARS_PER_TOKEN = {
    "cl100k_base": 4.0,
    "o200k_base": 3.8,
    "p50k_base": 4.5,
    "gpt2": 4.0,
    "llama": 3.5,
    "default": 4.0,
}


def estimate_tokens(
    text: str,
    encoding: str = "default",
) -> int:
    """Estimate token count without tiktoken dependency.

    Fast approximation blending character and word-based estimates.

    Args:
        text: Text to estimate.
        encoding: Target encoding/model family.

    Returns:
        Estimated token count.
    """
    if not text:
        return 0

    chars_per_token = CHARS_PER_TOKEN.get(encoding, 4.0)
    char_count = len(text)
    word_count = len(text.split())

    char_estimate = char_count / chars_per_token
    word_estimate = word_count * 1.3

    return int((char_estimate + word_estimate) / 2)


def count_tokens_tiktoken(text: str, model: str = "gpt-4") -> int:
    """Count tokens using tiktoken (if available).

    Encoding selection logic adapted from CAMEL's get_model_encoding().

    Args:
        text: Text to count.
        model: Model name for encoding selection.

    Returns:
        Exact token count, or estimate if tiktoken unavailable.
    """
    try:
        import tiktoken

        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            if "o1" in model or "o3" in model:
                encoding = tiktoken.get_encoding("o200k_base")
            else:
                encoding = tiktoken.get_encoding("cl100k_base")

        return len(encoding.encode(text, disallowed_special=()))
    except ImportError:
        return estimate_tokens(text)


def split_by_tokens(
    text: str,
    max_tokens: int,
    overlap_tokens: int = 0,
    encoding: str = "default",
) -> list[str]:
    """Split text into chunks by estimated token count.

    Args:
        text: Text to split.
        max_tokens: Maximum tokens per chunk.
        overlap_tokens: Overlap between chunks.
        encoding: Encoding for estimation.

    Returns:
        List of text chunks.
    """
    if not text:
        return []

    chars_per_token = CHARS_PER_TOKEN.get(encoding, 4.0)
    max_chars = int(max_tokens * chars_per_token)
    overlap_chars = int(overlap_tokens * chars_per_token)

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + max_chars, len(text))

        if end < len(text):
            for sep in [". ", ".\n", "\n\n", "\n", " "]:
                last_sep = text[start:end].rfind(sep)
                if last_sep > max_chars // 2:
                    end = start + last_sep + len(sep)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        new_start = end - overlap_chars if overlap_chars else end
        # Ensure forward progress to prevent infinite loops
        start = max(new_start, start + 1)

    return chunks
