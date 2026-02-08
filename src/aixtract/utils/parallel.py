"""Parallel processing utilities.

Batch processing pattern adapted from CAMEL-AI MarkItDownLoader
(camel/loaders/markitdown.py)
Copyright 2023-2026 @ CAMEL-AI.org. All Rights Reserved.
Licensed under the Apache License, Version 2.0
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Iterator, TypeVar

T = TypeVar("T")
R = TypeVar("R")


def process_batch(
    items: list[T],
    processor: Callable[[T], R],
    max_workers: int = 4,
    skip_failed: bool = False,
) -> Iterator[tuple[T, R | Exception]]:
    """Process items in parallel using ThreadPoolExecutor.

    Pattern adapted from CAMEL MarkItDownLoader.convert_files().

    Args:
        items: Items to process.
        processor: Function to apply to each item.
        max_workers: Maximum concurrent workers.
        skip_failed: If True, skip failed items silently.

    Yields:
        Tuples of (item, result_or_exception).
    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(processor, item): item
            for item in items
        }

        for future in as_completed(futures):
            item = futures[future]
            try:
                result = future.result()
                yield item, result
            except Exception as e:
                if not skip_failed:
                    yield item, e
