"""
AudioCapturePort - Abstract interface for audio capture.

Provides a clean abstraction for audio input from various sources:
microphones, files, network streams, etc.

Adapters:
    SoundDeviceCaptureAdapter: Primary adapter for microphone input
    FileCaptureAdapter: Read from WAV file (testing/debugging)
    NullCaptureAdapter: Generate silence or test signals (testing)

Example:
    from chatforge.adapters.audio_capture import SoundDeviceCaptureAdapter
    from chatforge.ports.audio_capture import AudioCaptureConfig

    capture = SoundDeviceCaptureAdapter(AudioCaptureConfig(sample_rate=24000))
    capture.set_callbacks(
        on_started=lambda: print("Capturing..."),
        on_stopped=lambda: print("Stopped!"),
    )

    audio_queue = await capture.start()
    while capture.is_capturing:
        chunk = await audio_queue.get()
        process_audio(chunk)
        if should_stop:
            capture.stop()  # Sync stop
            break
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Optional, Protocol, Union


__all__ = [
    # Exceptions
    "AudioCaptureError",
    "DeviceNotFoundError",
    "DeviceInUseError",
    "UnsupportedConfigError",
    "CaptureTimeoutError",
    # Enums
    "CaptureState",
    # Dataclasses
    "AudioCaptureConfig",
    "AudioDevice",
    "CaptureMetrics",
    # Protocols
    "DeviceEnumerable",
    # Port
    "AudioCapturePort",
]


# =============================================================================
# Exceptions
# =============================================================================


class AudioCaptureError(Exception):
    """Base exception for audio capture errors."""

    pass


class DeviceNotFoundError(AudioCaptureError):
    """Requested input device not found."""

    pass


class DeviceInUseError(AudioCaptureError):
    """Device is in use by another application."""

    pass


class UnsupportedConfigError(AudioCaptureError):
    """Device doesn't support requested configuration."""

    pass


class CaptureTimeoutError(AudioCaptureError):
    """Capture operation timed out."""

    pass


# =============================================================================
# Enums
# =============================================================================


class CaptureState(Enum):
    """
    Audio capture state.

    States:
        IDLE: Not capturing
        CAPTURING: Actively capturing audio
        ERROR: Error occurred
    """

    IDLE = "idle"
    CAPTURING = "capturing"
    ERROR = "error"


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class AudioCaptureConfig:
    """
    Configuration for audio capture.

    Attributes:
        sample_rate: Sample rate in Hz (default 24000)
        channels: Number of audio channels (default 1 for mono)
        bit_depth: Bits per sample (default 16)
        chunk_duration_ms: Duration of each chunk in milliseconds (default 100)
        device_id: Device identifier - int for index, str for name match, None for default
        callback_buffer_size: Size of callback queue (drops on overflow) (default 30)
        async_buffer_size: Size of async queue (blocks on overflow) (default 30)
    """

    sample_rate: int = 24000
    channels: int = 1
    bit_depth: int = 16
    chunk_duration_ms: int = 100
    device_id: Optional[Union[int, str]] = None
    callback_buffer_size: int = 30
    async_buffer_size: int = 30

    @property
    def bytes_per_sample(self) -> int:
        """Bytes per sample (bit_depth / 8)."""
        return self.bit_depth // 8

    @property
    def bytes_per_frame(self) -> int:
        """Bytes per frame (bytes_per_sample * channels)."""
        return self.bytes_per_sample * self.channels

    @property
    def bytes_per_ms(self) -> float:
        """Bytes per millisecond of audio."""
        return self.sample_rate * self.channels * self.bytes_per_sample / 1000

    @property
    def chunk_samples(self) -> int:
        """Number of samples per chunk."""
        return int(self.sample_rate * self.chunk_duration_ms / 1000)

    @property
    def chunk_bytes(self) -> int:
        """Bytes per chunk."""
        return int(self.chunk_samples * self.channels * self.bytes_per_sample)

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.sample_rate <= 0:
            raise ValueError(f"sample_rate must be positive, got {self.sample_rate}")
        if self.channels <= 0:
            raise ValueError(f"channels must be positive, got {self.channels}")
        if self.bit_depth not in (8, 16, 24, 32):
            raise ValueError(f"bit_depth must be 8, 16, 24, or 32, got {self.bit_depth}")
        if self.chunk_duration_ms <= 0:
            raise ValueError(
                f"chunk_duration_ms must be positive, got {self.chunk_duration_ms}"
            )
        if self.callback_buffer_size <= 0:
            raise ValueError(
                f"callback_buffer_size must be positive, got {self.callback_buffer_size}"
            )
        if self.async_buffer_size <= 0:
            raise ValueError(
                f"async_buffer_size must be positive, got {self.async_buffer_size}"
            )


# =============================================================================
# Data Types
# =============================================================================


@dataclass
class AudioDevice:
    """
    Audio input device information.

    Attributes:
        id: Device index (sounddevice uses int)
        name: Human-readable device name
        channels: Maximum input channels
        sample_rates: List of supported sample rates
        is_default: Whether this is the system default device
    """

    id: int
    name: str
    channels: int
    sample_rates: List[int] = field(default_factory=list)
    is_default: bool = False


@dataclass
class CaptureMetrics:
    """
    Metrics for audio capture performance.

    Tracks chunks, bytes, timing, and buffer health.
    """

    # Chunk counts
    chunks_captured: int = 0
    chunks_dropped: int = 0

    # Buffer health
    buffer_overruns: int = 0

    # Byte counts
    total_bytes: int = 0

    # Timing
    start_time: Optional[float] = None

    @property
    def capture_duration_seconds(self) -> float:
        """
        Duration of capture session in seconds.

        Computed dynamically from start_time.
        Returns 0.0 if capture hasn't started.
        """
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    @property
    def capture_rate(self) -> float:
        """
        Capture rate in chunks per second.

        Returns 0.0 if no duration.
        """
        duration = self.capture_duration_seconds
        if duration <= 0:
            return 0.0
        return self.chunks_captured / duration

    @property
    def drop_rate(self) -> float:
        """
        Drop rate as a fraction (0.0 to 1.0).

        Returns 0.0 if no chunks captured.
        """
        total = self.chunks_captured + self.chunks_dropped
        if total <= 0:
            return 0.0
        return self.chunks_dropped / total

    @property
    def capture_health(self) -> float:
        """
        Capture health score from 0.0 to 1.0.

        1.0 = healthy (no drops or overruns)
        0.0 = unhealthy (all chunks dropped)
        """
        return 1.0 - self.drop_rate


# =============================================================================
# Protocols
# =============================================================================


class DeviceEnumerable(Protocol):
    """
    Protocol for adapters that can enumerate audio devices.

    Not all adapters support this (e.g., FileCaptureAdapter, NullCaptureAdapter).
    Only hardware-based adapters implement this protocol.
    """

    @classmethod
    def list_devices(cls) -> List[AudioDevice]:
        """
        List available audio input devices.

        Returns:
            List of available devices, empty if none found.
        """
        ...


# =============================================================================
# Port Interface
# =============================================================================


class AudioCapturePort(ABC):
    """
    Abstract interface for audio capture.

    Implementations provide audio input from various sources:
    microphones, files, test signal generators, etc.

    Thread Safety:
        - Audio callbacks run in sounddevice thread
        - Transfer loop runs in asyncio
        - State protected by threading.Event (is_capturing)
        - Callbacks fire from asyncio context

    Callback Contract:
        - on_started fires exactly ONCE when capture begins
        - on_stopped fires exactly ONCE when capture ends
        - Callbacks are wrapped in try/except to prevent crashes

    Usage:
        capture = SoundDeviceCaptureAdapter()
        capture.set_callbacks(on_started=..., on_stopped=...)

        audio_queue = await capture.start()
        while capture.is_capturing:
            chunk = await audio_queue.get()
            process_audio(chunk)
            if should_stop:
                capture.stop()  # Sync!
                break

        capture.cleanup()

    Context Manager Usage:
        async with SoundDeviceCaptureAdapter() as capture:
            audio_queue = await capture.start()
            # ... consume chunks ...
        # Automatically drains and cleans up
    """

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    @abstractmethod
    def state(self) -> CaptureState:
        """Current capture state."""
        pass

    @property
    @abstractmethod
    def config(self) -> AudioCaptureConfig:
        """Current configuration."""
        pass

    @property
    @abstractmethod
    def is_capturing(self) -> bool:
        """
        True if actively capturing audio.

        Thread-safe check for capture state.
        """
        pass

    # =========================================================================
    # Core Methods
    # =========================================================================

    @abstractmethod
    async def start(self) -> "asyncio.Queue[bytes]":
        """
        Start audio capture.

        Returns an asyncio.Queue that will receive audio chunks as bytes.
        The queue pattern provides clean stop semantics - just stop consuming
        and call stop().

        Returns:
            asyncio.Queue[bytes]: Queue that receives audio chunks

        Raises:
            AudioCaptureError: If capture cannot be started
            DeviceNotFoundError: If configured device not found
            DeviceInUseError: If device is in use

        Example:
            audio_queue = await capture.start()
            while capture.is_capturing:
                chunk = await audio_queue.get()
                process(chunk)
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """
        Stop capture immediately (sync).

        This is a SYNCHRONOUS method for use in signal handlers
        and sync cleanup code. Does not drain buffers.

        After stop(), state returns to IDLE and adapter can be reused.
        """
        pass

    @abstractmethod
    async def stop_and_drain(self) -> None:
        """
        Stop capture and drain remaining chunks (async).

        This is an ASYNCHRONOUS method that waits for the transfer
        loop to finish processing remaining chunks in the buffer.

        Use this for graceful shutdown when you want all captured
        audio to be processed.
        """
        pass

    @abstractmethod
    def get_metrics(self) -> CaptureMetrics:
        """
        Get capture performance metrics.

        Returns a snapshot of current metrics with dynamic properties
        computed at access time.
        """
        pass

    @abstractmethod
    def get_device_info(self) -> Optional[AudioDevice]:
        """
        Get info about current input device.

        Returns None if no device (e.g., FileCaptureAdapter, NullCaptureAdapter).
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """
        Release resources.

        Call this when done with the adapter to:
        - Stop any active capture
        - Close audio streams
        - Release device handles
        - Close files

        After cleanup(), the adapter can be reused by calling start() again.
        """
        pass

    # =========================================================================
    # Callbacks
    # =========================================================================

    def set_callbacks(
        self,
        on_started: Optional[Callable[[], None]] = None,
        on_stopped: Optional[Callable[[], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        on_chunk_captured: Optional[Callable[[int], None]] = None,
    ) -> None:
        """
        Set callbacks for capture events.

        Callback Contract:
            - on_started: Fires ONCE when capture starts
            - on_stopped: Fires ONCE when capture stops
            - on_error: Fires on capture error
            - on_chunk_captured: Fires after each chunk captured (arg = chunk count)

        Thread Safety:
            Callbacks fire from the asyncio context. Keep them non-blocking.
            Long operations should be dispatched to another thread.

        Args:
            on_started: Called when capture starts
            on_stopped: Called when capture stops
            on_error: Called on capture error with the exception
            on_chunk_captured: Called after chunk captured with count
        """
        self._on_started = on_started
        self._on_stopped = on_stopped
        self._on_error = on_error
        self._on_chunk_captured = on_chunk_captured

    # =========================================================================
    # Context Manager Support
    # =========================================================================

    def __enter__(self) -> "AudioCapturePort":
        """Enter sync context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit sync context manager - cleanup resources."""
        self.cleanup()

    async def __aenter__(self) -> "AudioCapturePort":
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager - drain and cleanup."""
        await self.stop_and_drain()
        self.cleanup()
