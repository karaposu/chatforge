"""
Utilities for bridging synchronous and asynchronous code.

This module provides consistent patterns for:
1. Running sync code from async contexts (e.g., calling sync libraries from async handlers)
2. Running async code from sync contexts (e.g., LangChain tools calling async methods)

Example usage:

    # From async context, call sync library:
    from chatforge.utils import run_sync

    async def call_sync_api(client):
        return await run_sync(client.get_data, param="value")

    # From sync context, call async code:
    from chatforge.utils import run_async

    def sync_tool_run(self):
        return run_async(self._async_implementation())
"""

from __future__ import annotations

import asyncio
import functools
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any, Callable, TypeVar


if TYPE_CHECKING:
    from collections.abc import Coroutine


logger = logging.getLogger(__name__)

T = TypeVar("T")

# Shared executor for sync operations (configured for I/O bound work)
_executor: ThreadPoolExecutor | None = None
_executor_max_workers: int = 10


def get_executor(max_workers: int | None = None) -> ThreadPoolExecutor:
    """
    Get or create shared thread pool executor.

    The executor is created lazily and reused across calls.
    Use shutdown_executor() on application shutdown to clean up.

    Args:
        max_workers: Maximum worker threads. Only used on first call.

    Returns:
        Shared ThreadPoolExecutor instance.
    """
    global _executor, _executor_max_workers

    if max_workers is not None:
        _executor_max_workers = max_workers

    if _executor is None:
        _executor = ThreadPoolExecutor(
            max_workers=_executor_max_workers,
            thread_name_prefix="chatforge_async_",
        )
        logger.debug(f"Created chatforge executor with {_executor_max_workers} workers")

    return _executor


async def run_sync(
    func: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    """
    Run a synchronous function in a thread pool without blocking the event loop.

    Use this to call synchronous libraries from async contexts.

    Example:
        result = await run_sync(sync_client.get_data, param="value")

    Args:
        func: Synchronous function to call
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function

    Returns:
        The return value of the synchronous function

    Raises:
        Any exception raised by the synchronous function
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        get_executor(),
        functools.partial(func, *args, **kwargs),
    )


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """
    Run an async coroutine from a synchronous context.

    Use this in sync functions that need to call async code.
    Creates a new event loop, runs the coroutine, then closes it.

    Example:
        def _run(self, query: str) -> str:
            return run_async(self._async_search(query))

    Args:
        coro: Async coroutine to execute

    Returns:
        The return value of the coroutine

    Raises:
        Any exception raised by the coroutine

    Note:
        This uses asyncio.run() which creates a fresh event loop.
        Do not use this if you're already in an async context - just await directly.
    """
    return asyncio.run(coro)


async def run_with_timeout(
    coro: Coroutine[Any, Any, T],
    timeout: float,
    timeout_message: str = "Operation timed out",
) -> tuple[T | None, bool]:
    """
    Run a coroutine with a timeout.

    Example:
        result, timed_out = await run_with_timeout(
            slow_operation(),
            timeout=5.0,
            timeout_message="Slow operation"
        )
        if timed_out:
            return fallback_value

    Args:
        coro: Async coroutine to execute
        timeout: Timeout in seconds
        timeout_message: Message to log on timeout

    Returns:
        Tuple of (result, timed_out)
        - result: The coroutine result, or None if timed out
        - timed_out: True if the operation timed out
    """
    try:
        result = await asyncio.wait_for(coro, timeout=timeout)
        return result, False
    except asyncio.TimeoutError:
        logger.warning(f"{timeout_message} after {timeout}s")
        return None, True


def shutdown_executor() -> None:
    """
    Shutdown the shared executor.

    Call this on application shutdown to ensure clean termination
    of background threads.

    Example:
        import atexit
        from chatforge.utils import shutdown_executor
        atexit.register(shutdown_executor)
    """
    global _executor
    if _executor is not None:
        logger.debug("Shutting down chatforge executor")
        _executor.shutdown(wait=True)
        _executor = None


def reset_executor() -> None:
    """
    Reset the executor (for testing purposes).

    This shuts down the current executor so a new one will be created
    on the next call to get_executor() or run_sync().
    """
    shutdown_executor()
