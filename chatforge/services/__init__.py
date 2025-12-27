"""
Chatforge Services - Application services and background tasks.

Provides:
- Cleanup services for memory management (async and sync)
- Vision services for image analysis

Usage:
    from chatforge.services import AsyncCleanupRunner, SyncCleanupRunner

    # For FastAPI/async applications
    runner = AsyncCleanupRunner(
        cleanups={
            "storage": lambda: storage.cleanup_expired(60),
        }
    )
    await runner.start()

    # For sync applications (Flask, Slack Bolt)
    runner = SyncCleanupRunner(
        cleanups={
            "cache": lambda: cache.cleanup_expired(),
        }
    )
    runner.start()

Vision services:
    from chatforge.services.vision import ImageAnalyzer, ImageInfo
    # See chatforge.services.vision for full usage
"""

from chatforge.services.cleanup import (
    AsyncCleanupRunner,
    CleanupCycleMetrics,
    CleanupHistory,
    SyncCleanupRunner,
)

__all__ = [
    # Cleanup
    "AsyncCleanupRunner",
    "SyncCleanupRunner",
    "CleanupCycleMetrics",
    "CleanupHistory",
]
