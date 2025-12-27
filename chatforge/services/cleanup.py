"""
Memory Cleanup Service - Automatic memory leak prevention.

This module provides background cleanup tasks that prevent memory leaks by
periodically invoking cleanup functions across memory-intensive components.

Architecture:
    - AsyncCleanupRunner: For async applications (FastAPI, asyncio)
    - SyncCleanupRunner: For sync applications (Flask, threading-based)

Components cleaned are configurable via dependency injection.

Usage (FastAPI):
    from chatforge.services import AsyncCleanupRunner

    runner = AsyncCleanupRunner(
        cleanups={
            "storage": lambda: storage.cleanup_expired(60),
            "cache": lambda: cache.cleanup_expired(),
        },
        intervals={
            "storage": 600,  # 10 minutes
            "cache": 300,    # 5 minutes
        }
    )
    await runner.start()
    # ... app runs ...
    await runner.stop()

Usage (Sync):
    from chatforge.services import SyncCleanupRunner

    runner = SyncCleanupRunner(
        cleanups={
            "storage": lambda: asyncio.run(storage.cleanup_expired(60)),
        }
    )
    runner.start()
    # ... app runs ...
    runner.stop()
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)


@dataclass
class CleanupCycleMetrics:
    """Metrics for a single cleanup cycle."""

    timestamp: datetime
    duration_ms: float
    items_cleaned: dict[str, int] = field(default_factory=dict)
    error: str | None = None

    @property
    def total_cleaned(self) -> int:
        """Total items cleaned in this cycle."""
        return sum(self.items_cleaned.values())

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "items_cleaned": self.items_cleaned,
            "total_cleaned": self.total_cleaned,
            "error": self.error,
        }


@dataclass
class CleanupHistory:
    """Tracks cleanup cycle history with bounded storage."""

    max_size: int = 100
    cycles: deque = field(default_factory=lambda: deque(maxlen=100))
    total_cycles: int = 0

    def __post_init__(self):
        """Initialize deque with correct maxlen."""
        self.cycles = deque(maxlen=self.max_size)

    def add_cycle(self, metrics: CleanupCycleMetrics) -> None:
        """Add a new cleanup cycle to history."""
        self.cycles.append(metrics)
        self.total_cycles += 1

    def get_last(self) -> CleanupCycleMetrics | None:
        """Get the most recent cleanup cycle."""
        return self.cycles[-1] if self.cycles else None

    def get_recent(self, limit: int = 50) -> list[CleanupCycleMetrics]:
        """Get recent cleanup cycles."""
        return list(self.cycles)[-limit:]

    def get_last_24h_total(self) -> int:
        """Get total items cleaned in last 24 hours."""
        cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=24)
        return sum(c.total_cleaned for c in self.cycles if c.timestamp > cutoff)

    def get_avg_items_per_cycle(self) -> float:
        """Get average items cleaned per cycle."""
        if not self.cycles:
            return 0.0
        return sum(c.total_cleaned for c in self.cycles) / len(self.cycles)


class AsyncCleanupRunner:
    """
    Async cleanup runner for FastAPI/asyncio applications.

    Uses asyncio.create_task to schedule periodic cleanup in the background
    without blocking the event loop.

    Example:
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            runner = AsyncCleanupRunner(
                cleanups={
                    "storage": lambda: storage.cleanup_expired(60),
                }
            )
            await runner.start()
            yield
            await runner.stop()

    Attributes:
        _running: Flag indicating if cleanup is active.
        _task: Background asyncio task.
        _cleanups: Dict of component name to async cleanup function.
        _intervals: Dict of component name to cleanup interval in seconds.
        _history: Cleanup cycle history tracking.
    """

    def __init__(
        self,
        cleanups: dict[str, Callable[[], Awaitable[int]]] | None = None,
        intervals: dict[str, int] | None = None,
        default_interval: int = 600,  # 10 min
        history_size: int = 100,
    ):
        """
        Initialize async cleanup runner.

        Args:
            cleanups: Dict mapping component name to async cleanup function.
                      Each function should return the number of items cleaned.
            intervals: Dict mapping component name to cleanup interval in seconds.
                       Components not in this dict use default_interval.
            default_interval: Default cleanup interval in seconds (default: 600 = 10 min)
            history_size: Number of cleanup cycles to keep in history (default: 100)
        """
        self._running = False
        self._task: asyncio.Task | None = None
        self._cleanups = cleanups or {}
        self._intervals = intervals or {}
        self._default_interval = default_interval
        self._history = CleanupHistory(max_size=history_size)

        # Track last cleanup time per component
        self._last_cleanup: dict[str, float] = {}

        logger.info(
            f"AsyncCleanupRunner initialized with {len(self._cleanups)} cleanup functions"
        )

    def register_cleanup(
        self,
        name: str,
        cleanup_fn: Callable[[], Awaitable[int]],
        interval: int | None = None,
    ) -> None:
        """
        Register a cleanup function.

        Args:
            name: Component name (used in logging and metrics)
            cleanup_fn: Async function that returns number of items cleaned
            interval: Optional custom interval in seconds
        """
        self._cleanups[name] = cleanup_fn
        if interval is not None:
            self._intervals[name] = interval
        logger.debug(f"Registered cleanup function: {name}")

    async def start(self) -> None:
        """Start the background cleanup task."""
        if self._running:
            logger.warning("AsyncCleanupRunner already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._cleanup_loop())
        logger.info("AsyncCleanupRunner started")

    async def stop(self) -> None:
        """Stop the background cleanup task."""
        if not self._running:
            return

        self._running = False

        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

        logger.info("AsyncCleanupRunner stopped")

    @property
    def is_running(self) -> bool:
        """Check if the cleanup runner is active."""
        return self._running

    def get_last_cleanup_stats(self) -> dict | None:
        """Get statistics from the most recent cleanup cycle."""
        last = self._history.get_last()
        return last.to_dict() if last else None

    def get_cleanup_history(self, limit: int = 50) -> dict:
        """
        Get cleanup cycle history.

        Args:
            limit: Maximum cycles to return

        Returns:
            Dictionary with cycles and statistics
        """
        cycles = self._history.get_recent(limit)
        return {
            "cycles": [c.to_dict() for c in cycles],
            "total_cycles": self._history.total_cycles,
            "avg_items_per_cycle": round(self._history.get_avg_items_per_cycle(), 2),
            "last_24h_total_cleaned": self._history.get_last_24h_total(),
        }

    async def run_cleanup_cycle(self) -> CleanupCycleMetrics:
        """
        Manually trigger a cleanup cycle.

        Returns:
            CleanupCycleMetrics with results
        """
        start_time = time.time()
        items_cleaned: dict[str, int] = {}
        error = None

        for name, cleanup_fn in self._cleanups.items():
            try:
                count = await cleanup_fn()
                items_cleaned[name] = count
                if count > 0:
                    logger.info(f"Cleanup '{name}': {count} items removed")
            except Exception as e:
                logger.error(f"Cleanup '{name}' failed: {e}", exc_info=True)
                items_cleaned[name] = -1
                error = f"{name}: {e}"

        duration_ms = (time.time() - start_time) * 1000
        metrics = CleanupCycleMetrics(
            timestamp=datetime.now(tz=timezone.utc),
            duration_ms=round(duration_ms, 2),
            items_cleaned=items_cleaned,
            error=error,
        )
        self._history.add_cycle(metrics)
        return metrics

    async def _cleanup_loop(self) -> None:
        """Background loop that runs cleanup at configured intervals."""
        # Initialize last cleanup times
        current_time = time.time()
        for name in self._cleanups:
            self._last_cleanup[name] = current_time

        while self._running:
            try:
                current_time = time.time()
                cycle_start = time.time()
                items_cleaned: dict[str, int] = {}
                did_cleanup = False

                # Check which components need cleanup
                for name, cleanup_fn in self._cleanups.items():
                    interval = self._intervals.get(name, self._default_interval)
                    last = self._last_cleanup.get(name, 0)

                    if current_time - last >= interval:
                        try:
                            count = await cleanup_fn()
                            items_cleaned[name] = count
                            if count > 0:
                                logger.info(f"Cleanup '{name}': {count} items removed")
                            did_cleanup = True
                        except Exception as e:
                            logger.error(f"Cleanup '{name}' failed: {e}", exc_info=True)
                            items_cleaned[name] = -1
                        finally:
                            self._last_cleanup[name] = current_time

                # Record cycle metrics if any cleanup happened
                if did_cleanup:
                    duration_ms = (time.time() - cycle_start) * 1000
                    metrics = CleanupCycleMetrics(
                        timestamp=datetime.now(tz=timezone.utc),
                        duration_ms=round(duration_ms, 2),
                        items_cleaned=items_cleaned,
                    )
                    self._history.add_cycle(metrics)

                # Sleep for 60 seconds before next check
                await asyncio.sleep(60)

            except asyncio.CancelledError:
                logger.debug("Cleanup loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)
                await asyncio.sleep(60)


class SyncCleanupRunner:
    """
    Synchronous cleanup runner for sync applications (Flask, Slack Bolt, etc.).

    Uses threading.Timer for periodic cleanup in sync environments.

    Example:
        runner = SyncCleanupRunner(
            cleanups={
                "cache": lambda: cache.cleanup_expired(),
            }
        )
        runner.start()
        # ... app runs ...
        runner.stop()

    Attributes:
        _running: Flag indicating if cleanup is active.
        _timers: Active threading.Timer instances.
        _cleanups: Dict of component name to sync cleanup function.
        _intervals: Dict of component name to cleanup interval in seconds.
    """

    def __init__(
        self,
        cleanups: dict[str, Callable[[], int]] | None = None,
        intervals: dict[str, int] | None = None,
        default_interval: int = 600,  # 10 min
    ):
        """
        Initialize sync cleanup runner.

        Args:
            cleanups: Dict mapping component name to sync cleanup function.
                      Each function should return the number of items cleaned.
            intervals: Dict mapping component name to cleanup interval in seconds.
                       Components not in this dict use default_interval.
            default_interval: Default cleanup interval in seconds (default: 600 = 10 min)
        """
        self._running = False
        self._timers: list[threading.Timer] = []
        self._cleanups = cleanups or {}
        self._intervals = intervals or {}
        self._default_interval = default_interval
        self._lock = threading.RLock()
        self._history = CleanupHistory(max_size=100)

        logger.info(
            f"SyncCleanupRunner initialized with {len(self._cleanups)} cleanup functions"
        )

    def register_cleanup(
        self,
        name: str,
        cleanup_fn: Callable[[], int],
        interval: int | None = None,
    ) -> None:
        """
        Register a cleanup function.

        Args:
            name: Component name (used in logging and metrics)
            cleanup_fn: Sync function that returns number of items cleaned
            interval: Optional custom interval in seconds
        """
        self._cleanups[name] = cleanup_fn
        if interval is not None:
            self._intervals[name] = interval
        logger.debug(f"Registered cleanup function: {name}")

    def start(self) -> None:
        """Start periodic cleanup timers."""
        with self._lock:
            if self._running:
                logger.warning("SyncCleanupRunner already running")
                return

            self._running = True

            # Schedule initial cleanups
            for name in self._cleanups:
                interval = self._intervals.get(name, self._default_interval)
                self._schedule_cleanup(name, interval)

            logger.info("SyncCleanupRunner started")

    def stop(self) -> None:
        """Stop all cleanup timers."""
        with self._lock:
            if not self._running:
                return

            self._running = False

            # Cancel all timers
            for timer in self._timers:
                timer.cancel()

            self._timers.clear()

            logger.info("SyncCleanupRunner stopped")

    @property
    def is_running(self) -> bool:
        """Check if the cleanup runner is active."""
        return self._running

    def get_cleanup_history(self, limit: int = 50) -> dict:
        """Get cleanup cycle history."""
        cycles = self._history.get_recent(limit)
        return {
            "cycles": [c.to_dict() for c in cycles],
            "total_cycles": self._history.total_cycles,
        }

    def _schedule_cleanup(self, name: str, interval: int) -> None:
        """Schedule a cleanup for a component."""
        if not self._running:
            return

        timer = threading.Timer(
            interval, self._cleanup_and_reschedule, args=(name, interval)
        )
        timer.daemon = True
        timer.start()

        with self._lock:
            self._timers.append(timer)

    def _cleanup_and_reschedule(self, name: str, interval: int) -> None:
        """Run cleanup and reschedule next cleanup."""
        start_time = time.time()
        count = 0
        error = None

        try:
            cleanup_fn = self._cleanups.get(name)
            if cleanup_fn:
                count = cleanup_fn()
                if count > 0:
                    logger.info(f"Cleanup '{name}': {count} items removed")
        except Exception as e:
            logger.error(f"Cleanup '{name}' failed: {e}", exc_info=True)
            error = str(e)
            count = -1
        finally:
            # Record metrics
            duration_ms = (time.time() - start_time) * 1000
            metrics = CleanupCycleMetrics(
                timestamp=datetime.now(tz=timezone.utc),
                duration_ms=round(duration_ms, 2),
                items_cleaned={name: count},
                error=error,
            )
            self._history.add_cycle(metrics)

            # Reschedule next cleanup
            if self._running:
                self._schedule_cleanup(name, interval)
