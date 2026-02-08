"""Filename sanitization utilities.

Adapted from CAMEL-AI (https://github.com/camel-ai/camel)
Copyright 2023-2026 @ CAMEL-AI.org. All Rights Reserved.
Licensed under the Apache License, Version 2.0
"""
from __future__ import annotations

import re


def sanitize_filename(filename: str) -> str:
    """Replace unsafe characters in filename with underscores.

    Args:
        filename: The filename to sanitize.

    Returns:
        Sanitized filename safe for filesystem use.
    """
    return re.sub(r'[^\w\-_. ]', '_', filename)
