"""
AudioPlaybackPort - Abstract interface for audio playback.

Provides a clean abstraction for audio output to various sinks:
speakers, files, network streams, etc.

Adapters:
    SoundDevicePlaybackAdapter: Primary adapter using buffered/batching pattern
    DirectPlaybackAdapter: Low-latency callback-based (optional)
    FileSinkAdapter: Write to WAV file
    NullPlaybackAdapter: Discard audio (testing)

Example:
    from chatforge.adapters.audio_playback import SoundDevicePlaybackAdapter
    from chatforge.ports.audio_playback import AudioPlaybackConfig

    player = SoundDevicePlaybackAdapter(AudioPlaybackConfig(sample_rate=24000))
    player.set_callbacks(
        on_started=lambda: print("Playing..."),
        on_complete=lambda: print("Done!"),
    )

    for chunk in audio_chunks:
        player.play(chunk)

    player.mark_complete()
    player.wait_until_complete_sync()
"""

import asyncio
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Optional, Protocol, Union


__all__ = [
    # Exceptions
    "AudioPlaybackError",
    "DeviceNotFoundError",
    "DeviceInUseError",
    "PlaybackTimeoutError",
    # Enums
    "PlaybackState",
    # Dataclasses
    "AudioPlaybackConfig",
    "OutputDevice",
    "PlaybackMetrics",
    # Protocols
    "DeviceEnumerable",
    # Port
    "AudioPlaybackPort",
]


# =============================================================================
# Exceptions
# =============================================================================


class AudioPlaybackError(Exception):
    """Base exception for audio playback errors."""

    pass


class DeviceNotFoundError(AudioPlaybackError):
    """Requested output device not found."""

    pass


class DeviceInUseError(AudioPlaybackError):
    """Device is in use by another application."""

    pass


class PlaybackTimeoutError(AudioPlaybackError):
    """Playback operation timed out."""

    pass


# =============================================================================
# Enums
# =============================================================================


class PlaybackState(Enum):
    """
    Audio playback state.

    States:
        IDLE: No playback active
        BUFFERING: Collecting chunks before playback starts
        PLAYING: Actively outputting audio
        DRAINING: mark_complete() called, finishing buffer
        ERROR: Error occurred
    """

    IDLE = "idle"
    BUFFERING = "buffering"
    PLAYING = "playing"
    DRAINING = "draining"
    ERROR = "error"


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class AudioPlaybackConfig:
    """
    Configuration for audio playback.

    Attributes:
        sample_rate: Sample rate in Hz (default 24000)
        channels: Number of audio channels (default 1 for mono)
        bit_depth: Bits per sample (default 16)
        device_id: Device identifier - int for index, str for name match, None for default
        min_buffer_chunks: Start playback after this many chunks (default 2)
        max_buffer_ms: Maximum buffer size in milliseconds (default 5000)
        latency: Latency preference - "low", "high", or float seconds
    """

    sample_rate: int = 24000
    channels: int = 1
    bit_depth: int = 16
    device_id: Optional[Union[int, str]] = None
    min_buffer_chunks: int = 2
    max_buffer_ms: int = 5000
    latency: Union[str, float] = "low"

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

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.sample_rate <= 0:
            raise ValueError(f"sample_rate must be positive, got {self.sample_rate}")
        if self.channels <= 0:
            raise ValueError(f"channels must be positive, got {self.channels}")
        if self.bit_depth not in (8, 16, 24, 32):
            raise ValueError(f"bit_depth must be 8, 16, 24, or 32, got {self.bit_depth}")
        if self.min_buffer_chunks < 1:
            raise ValueError(f"min_buffer_chunks must be >= 1, got {self.min_buffer_chunks}")
        if self.max_buffer_ms <= 0:
            raise ValueError(f"max_buffer_ms must be positive, got {self.max_buffer_ms}")


# =============================================================================
# Data Types
# =============================================================================


@dataclass
class OutputDevice:
    """
    Audio output device information.

    Attributes:
        id: Device index (sounddevice uses int)
        name: Human-readable device name
        channels: Maximum output channels
        sample_rates: List of supported sample rates
        is_default: Whether this is the system default device
    """

    id: int
    name: str
    channels: int
    sample_rates: List[int] = field(default_factory=list)
    is_default: bool = False


@dataclass
class PlaybackMetrics:
    """
    Metrics for audio playback performance.

    Tracks chunks, bytes, timing, and buffer health.
    """

    # Chunk counts
    chunks_received: int = 0
    chunks_played: int = 0
    chunks_buffered: int = 0

    # Byte counts
    total_bytes_received: int = 0
    total_bytes_played: int = 0

    # Buffer state
    buffer_duration_ms: float = 0.0

    # Timing
    playback_duration_seconds: float = 0.0
    first_chunk_time: Optional[float] = None
    playback_start_time: Optional[float] = None
    playback_end_time: Optional[float] = None

    # Health
    underruns: int = 0

    @property
    def initial_latency_ms(self) -> Optional[float]:
        """
        Time from first chunk received to first audio output.

        Returns None if playback hasn't started yet.
        """
        if self.first_chunk_time is not None and self.playback_start_time is not None:
            return (self.playback_start_time - self.first_chunk_time) * 1000
        return None

    @property
    def buffer_health(self) -> float:
        """
        Buffer health score from 0.0 to 1.0.

        1.0 = healthy (no underruns)
        0.0 = unhealthy (underrun on every chunk)
        """
        if self.chunks_received == 0:
            return 1.0
        return max(0.0, 1.0 - (self.underruns / self.chunks_received))


# =============================================================================
# Protocols
# =============================================================================


class DeviceEnumerable(Protocol):
    """
    Protocol for adapters that can enumerate audio devices.

    Not all adapters support this (e.g., FileSinkAdapter, NullPlaybackAdapter).
    Only hardware-based adapters implement this protocol.
    """

    @classmethod
    def list_devices(cls) -> List[OutputDevice]:
        """
        List available audio output devices.

        Returns:
            List of available devices, empty if none found.
        """
        ...


# =============================================================================
# Port Interface
# =============================================================================


class AudioPlaybackPort(ABC):
    """
    Abstract interface for audio playback.

    Implementations provide audio output to various sinks:
    speakers, files, network streams, etc.

    Thread Safety:
        - play() may be called from any thread
        - Callbacks fire from playback thread (must be non-blocking)
        - State transitions are thread-safe

    Callback Contract:
        - on_started fires exactly ONCE when first audio outputs
        - on_complete fires exactly ONCE when all audio has played
        - Callbacks are wrapped in try/except to prevent crashes

    Usage:
        player = SoundDevicePlaybackAdapter()
        player.set_callbacks(on_started=..., on_complete=...)

        for chunk in audio_chunks:
            player.play(chunk)

        player.mark_complete()
        completed = player.wait_until_complete_sync(timeout=30.0)
        player.cleanup()
    """

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    @abstractmethod
    def state(self) -> PlaybackState:
        """Current playback state."""
        pass

    @property
    @abstractmethod
    def config(self) -> AudioPlaybackConfig:
        """Current configuration."""
        pass

    @property
    @abstractmethod
    def is_playing(self) -> bool:
        """
        True if in PLAYING or DRAINING state.

        Use this for general "is audio active" checks.
        """
        pass

    @property
    @abstractmethod
    def is_actively_outputting(self) -> bool:
        """
        True if audio is actually being output right now.

        More specific than is_playing - accounts for buffer state.
        """
        pass

    @property
    @abstractmethod
    def buffer_duration_ms(self) -> float:
        """Current buffer duration in milliseconds."""
        pass

    # =========================================================================
    # Core Methods
    # =========================================================================

    @abstractmethod
    def play(self, audio_data: bytes) -> bool:
        """
        Queue audio for playback.

        Args:
            audio_data: PCM audio bytes to play

        Returns:
            True if queued successfully, False if buffer full

        Note:
            Does NOT raise exception on buffer full - returns False.
            Exceptions are reserved for unexpected errors (device disconnected, etc.)
        """
        pass

    @abstractmethod
    def mark_complete(self) -> None:
        """
        Mark that all audio has been sent.

        Call this after sending the last chunk to enable
        proper completion detection. State transitions to DRAINING.
        """
        pass

    @abstractmethod
    def stop(self, force: bool = False) -> None:
        """
        Stop playback.

        Args:
            force: If True, stop immediately discarding buffer (barge-in).
                   If False, let buffer drain naturally.

        After stop(), state returns to IDLE and adapter is ready
        for new playback session.
        """
        pass

    @abstractmethod
    def wait_until_complete_sync(self, timeout: float = 30.0) -> bool:
        """
        Wait synchronously until all queued audio has been played.

        Use this in synchronous code (like VoxStream).

        Args:
            timeout: Maximum seconds to wait

        Returns:
            True if completed, False if timeout
        """
        pass

    @abstractmethod
    async def wait_until_complete(self, timeout: float = 30.0) -> bool:
        """
        Wait asynchronously until all queued audio has been played.

        Use this in async code.

        Args:
            timeout: Maximum seconds to wait

        Returns:
            True if completed, False if timeout
        """
        pass

    @abstractmethod
    def get_metrics(self) -> PlaybackMetrics:
        """
        Get playback performance metrics.

        Returns a snapshot of current metrics.
        """
        pass

    @abstractmethod
    def get_device_info(self) -> Optional[OutputDevice]:
        """
        Get info about current output device.

        Returns None if no device (e.g., FileSinkAdapter).
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """
        Release resources.

        Call this when done with the adapter to:
        - Stop any running playback
        - Close audio streams
        - Release device handles
        - Close files

        After cleanup(), the adapter should not be used.
        """
        pass

    # =========================================================================
    # Callbacks
    # =========================================================================

    def set_callbacks(
        self,
        on_started: Optional[Callable[[], None]] = None,
        on_complete: Optional[Callable[[], None]] = None,
        on_buffer_low: Optional[Callable[[], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        on_chunk_played: Optional[Callable[[int], None]] = None,
    ) -> None:
        """
        Set callbacks for playback events.

        Callback Contract:
            - on_started: Fires ONCE when first audio starts playing
            - on_complete: Fires ONCE when all audio has been played
            - on_buffer_low: Fires when buffer is running low
            - on_error: Fires on playback error
            - on_chunk_played: Fires after each batch of chunks played (arg = chunk count)

        Thread Safety:
            Callbacks fire from the playback thread. Keep them non-blocking.
            Long operations should be dispatched to another thread.

        Args:
            on_started: Called when first audio starts playing
            on_complete: Called when all audio has been played
            on_buffer_low: Called when buffer is running low
            on_error: Called on playback error with the exception
            on_chunk_played: Called after chunks played with count
        """
        self._on_started = on_started
        self._on_complete = on_complete
        self._on_buffer_low = on_buffer_low
        self._on_error = on_error
        self._on_chunk_played = on_chunk_played

    # =========================================================================
    # Optional: Context Manager Support
    # =========================================================================

    def __enter__(self) -> "AudioPlaybackPort":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager - cleanup resources."""
        self.cleanup()
