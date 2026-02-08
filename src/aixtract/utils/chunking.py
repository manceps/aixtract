"""Content chunking utilities.

Code-aware chunking adapted from CAMEL-AI CodeChunker
(camel/utils/chunker/code_chunker.py)
Copyright 2023-2026 @ CAMEL-AI.org. All Rights Reserved.
Licensed under the Apache License, Version 2.0
"""
from __future__ import annotations

import re
from typing import Callable

from aixtract.models.result import ContentChunk
from aixtract.utils.tokens import estimate_tokens


class ContentChunker:
    """Chunk text content while respecting structure.

    Supports both document structure (headings, paragraphs) and
    code structure (functions, classes).

    Args:
        chunk_size: Maximum tokens per chunk.
        overlap: Number of overlapping characters between chunks.
        token_counter: Optional custom token counting function.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        overlap: int = 100,
        token_counter: Callable[[str], int] | None = None,
    ) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.count_tokens = token_counter or estimate_tokens

        # Heading pattern for documents
        self.heading_pattern = re.compile(r"^#{1,6}\s+.+$", re.MULTILINE)
        # Code structure pattern (adapted from CAMEL CodeChunker)
        self.struct_pattern = re.compile(
            r"^\s*(?:(def|class|function)\s+\w+|"
            r"(public|private|protected)\s+[\w<>]+\s+\w+\s*\(|"
            r"\b(interface|enum|namespace)\s+\w+|"
            r"#\s*(region|endregion)\b)"
        )

    def chunk(self, content: str, respect_structure: bool = True) -> list[ContentChunk]:
        """Split content into chunks.

        Args:
            content: Text content to chunk.
            respect_structure: If True, avoid splitting at structure boundaries.

        Returns:
            List of ContentChunk objects.
        """
        if not content:
            return []

        if not respect_structure:
            return self._simple_chunk(content)

        return self._structure_aware_chunk(content)

    def _simple_chunk(self, content: str) -> list[ContentChunk]:
        """Simple chunking with sentence boundary respect."""
        chunks = []
        start = 0
        index = 0

        while start < len(content):
            chars_per_token = 4.0
            end = min(start + int(self.chunk_size * chars_per_token), len(content))

            if end < len(content):
                for sep in [". ", ".\n", "\n\n", "\n", " "]:
                    last_sep = content[start:end].rfind(sep)
                    if last_sep > (end - start) // 2:
                        end = start + last_sep + len(sep)
                        break

            chunk_text = content[start:end].strip()
            if chunk_text:
                chunks.append(ContentChunk(
                    index=index,
                    content=chunk_text,
                    char_start=start,
                    char_end=end,
                    token_count_estimate=self.count_tokens(chunk_text),
                ))
                index += 1

            start = end - self.overlap if self.overlap and end < len(content) else end

        return chunks

    def _structure_aware_chunk(self, content: str) -> list[ContentChunk]:
        """Chunk respecting document/code structure.

        Logic adapted from CAMEL CodeChunker.chunk().
        """
        chunks_text: list[str] = []
        current_chunk: list[str] = []
        current_tokens = 0
        struct_buffer: list[str] = []
        struct_tokens = 0

        for line in content.splitlines(keepends=True):
            line_tokens = self.count_tokens(line)

            # Handle oversized lines by splitting them
            if line_tokens > self.chunk_size:
                if current_chunk:
                    chunks_text.append("".join(current_chunk))
                    current_chunk = []
                    current_tokens = 0
                # Split the oversized line using simple sentence-boundary logic
                chars_per_token = 4.0
                max_chars = int(self.chunk_size * chars_per_token)
                pos = 0
                while pos < len(line):
                    end = min(pos + max_chars, len(line))
                    if end < len(line):
                        for sep in [". ", ".\n", "\n\n", "\n", " "]:
                            last_sep = line[pos:end].rfind(sep)
                            if last_sep > max_chars // 2:
                                end = pos + last_sep + len(sep)
                                break
                    chunks_text.append(line[pos:end])
                    pos = end
                continue

            # Check if this is a structure boundary
            is_struct = bool(
                self.struct_pattern.match(line) or self.heading_pattern.match(line)
            )

            if is_struct:
                if struct_buffer:
                    if current_tokens + struct_tokens <= self.chunk_size:
                        current_chunk.extend(struct_buffer)
                        current_tokens += struct_tokens
                    else:
                        if current_chunk:
                            chunks_text.append("".join(current_chunk))
                        current_chunk = struct_buffer.copy()
                        current_tokens = struct_tokens
                    struct_buffer = []
                    struct_tokens = 0

                struct_buffer.append(line)
                struct_tokens += line_tokens
            else:
                if struct_buffer:
                    struct_buffer.append(line)
                    struct_tokens += line_tokens
                else:
                    if current_tokens + line_tokens > self.chunk_size:
                        chunks_text.append("".join(current_chunk))
                        current_chunk = [line]
                        current_tokens = line_tokens
                    else:
                        current_chunk.append(line)
                        current_tokens += line_tokens

        # Flush remaining
        if struct_buffer:
            if current_tokens + struct_tokens <= self.chunk_size:
                current_chunk.extend(struct_buffer)
            else:
                if current_chunk:
                    chunks_text.append("".join(current_chunk))
                current_chunk = struct_buffer

        if current_chunk:
            chunks_text.append("".join(current_chunk))

        # Convert to ContentChunk objects
        result = []
        char_offset = 0
        chunk_index = 0
        for raw_text in chunks_text:
            original_len = len(raw_text)
            stripped = raw_text.strip()
            if stripped:
                result.append(ContentChunk(
                    index=chunk_index,
                    content=stripped,
                    char_start=char_offset,
                    char_end=char_offset + original_len,
                    token_count_estimate=self.count_tokens(stripped),
                ))
                chunk_index += 1
            char_offset += original_len

        return result
