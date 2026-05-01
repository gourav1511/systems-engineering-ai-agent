"""Retry helpers for async operations."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable


async def retry_async(
    func: Callable[[], Awaitable[object]],
    *,
    max_attempts: int = 3,
    base_delay_seconds: float = 1.0,
    retry_exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> object:
    """Retry an async callable with exponential backoff."""
    attempt = 1
    while True:
        try:
            return await func()
        except retry_exceptions:
            if attempt >= max_attempts:
                raise
            await asyncio.sleep(base_delay_seconds * (2 ** (attempt - 1)))
            attempt += 1