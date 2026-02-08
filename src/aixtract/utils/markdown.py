"""Markdown processing utilities."""
from __future__ import annotations

import re


def clean_markdown(text: str) -> str:
    """Clean and normalize markdown text."""
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Remove excessive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Normalize whitespace
    lines = []
    for line in text.split('\n'):
        # Preserve intentional indentation (code blocks)
        if line.startswith('    ') or line.startswith('\t'):
            lines.append(line)
        else:
            lines.append(line.strip())

    return '\n'.join(lines).strip()


def escape_markdown(text: str) -> str:
    """Escape special markdown characters."""
    chars_to_escape = ['\\', '`', '*', '_', '{', '}', '[', ']', '(', ')', '#', '+', '-', '.', '!', '|']
    for char in chars_to_escape:
        text = text.replace(char, '\\' + char)
    return text


def table_to_markdown(
    headers: list[str],
    rows: list[list[str]],
    alignment: list[str] | None = None,
) -> str:
    """Convert tabular data to markdown table.

    Args:
        headers: Column headers
        rows: Table data rows
        alignment: Optional alignment ('left', 'center', 'right') per column
    """
    if not headers:
        return ""

    alignment = alignment or ['left'] * len(headers)

    # Build alignment markers
    align_map = {'left': ':---', 'center': ':---:', 'right': '---:'}
    align_row = [align_map.get(a, '---') for a in alignment]

    lines = [
        '| ' + ' | '.join(headers) + ' |',
        '| ' + ' | '.join(align_row) + ' |',
    ]

    for row in rows:
        # Pad row if needed
        padded = row + [''] * (len(headers) - len(row))
        lines.append('| ' + ' | '.join(str(cell) for cell in padded) + ' |')

    return '\n'.join(lines)


def code_block(code: str, language: str = "") -> str:
    """Wrap code in markdown code block."""
    return f"```{language}\n{code}\n```"


def heading(text: str, level: int = 1) -> str:
    """Create markdown heading."""
    level = max(1, min(6, level))
    return '#' * level + ' ' + text
