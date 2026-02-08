"""Dependency validation utilities.

Adapted from CAMEL-AI (https://github.com/camel-ai/camel)
Copyright 2023-2026 @ CAMEL-AI.org. All Rights Reserved.
Licensed under the Apache License, Version 2.0
"""
from __future__ import annotations

import functools
from typing import Any, Callable


def dependencies_required(*packages: str) -> Callable:
    """Decorator to check if required packages are installed.

    Args:
        *packages: Package names to check.

    Returns:
        Decorated function that raises ImportError if deps missing.

    Example:
        @dependencies_required('pypdf', 'pdfplumber')
        def extract_pdf(self, path): ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            missing = []
            for package in packages:
                try:
                    __import__(package.replace("-", "_"))
                except ImportError:
                    missing.append(package)
            if missing:
                raise ImportError(
                    f"Required packages not installed: {', '.join(missing)}. "
                    f"Install with: pip install {' '.join(missing)}"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator
