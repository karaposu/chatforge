"""
Chatforge Services - Application services and background tasks.

Provides:
- Cleanup services for memory management (async and sync)
- Vision services for image analysis
- TTS services for text-to-speech

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

TTS services:
    from chatforge.services import TTSService

    async with TTSService() as tts:
        result = await tts.generate("Hello world!")

    # With different provider
    async with TTSService("elevenlabs") as tts:
        result = await tts.generate("Hello!", voice_id="rachel")
"""

from chatforge.services.cleanup import (
    AsyncCleanupRunner,
    CleanupCycleMetrics,
    CleanupHistory,
    SyncCleanupRunner,
)
from chatforge.services.tts import TTSService

__all__ = [
    # Cleanup
    "AsyncCleanupRunner",
    "SyncCleanupRunner",
    "CleanupCycleMetrics",
    "CleanupHistory",
    # TTS
    "TTSService",
]
