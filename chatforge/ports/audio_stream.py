"""
AudioStreamPort - Abstract interface for real-time audio I/O.

This port enables voice applications to capture microphone input
and play audio output without coupling to specific hardware or
platform implementations.

Audio Format: PCM16, 24kHz, Mono (matches OpenAI Realtime API)

Implementations handle platform-specific details:
- VoxStreamAdapter: Desktop via sounddevice
- WebRTCAudioAdapter: Web via WebSocket relay
- TwilioAudioAdapter: Phone via Media Streams

Usage:
    from chatforge.ports.audio_stream import AudioStreamPort, AudioCallbacks

    async with VoxStreamAdapter() as audio:
        audio.set_callbacks(AudioCallbacks(
            on_speech_start=handle_speech_start,
            on_speech_end=handle_speech_end,
        ))

        async for chunk in audio.start_capture():
            await send_to_ai(chunk)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator, Callable, Optional


__all__ = [
    # Exceptions
    "AudioStreamError",
    "AudioStreamDeviceError",
    "AudioStreamBufferError",
    "AudioStreamNotInitializedError",
    # Data classes
    "AudioStreamConfig",
    "VADConfig",
    "AudioCallbacks",
    "AudioDevice",
    # Port
    "AudioStreamPort",
]


# =============================================================================
# Exceptions
# =============================================================================


class AudioStreamError(Exception):
    """Base exception for AudioStreamPort."""

    pass


class AudioStreamDeviceError(AudioStreamError):
    """Device not found, disconnected, or unavailable."""

    pass


class AudioStreamBufferError(AudioStreamError):
    """Buffer overflow or underflow."""

    pass


class AudioStreamNotInitializedError(AudioStreamError):
    """Adapter used before entering async context."""

    pass


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class AudioStreamConfig:
    """
    Configuration for audio streaming.

    Attributes:
        sample_rate: Audio sample rate in Hz (default: 24000 for OpenAI compatibility)
        channels: Number of audio channels (1=mono, 2=stereo)
        bit_depth: Bits per sample (16 for PCM16)
        chunk_duration_ms: Duration of each audio chunk in milliseconds
    """

    sample_rate: int = 24000
    channels: int = 1
    bit_depth: int = 16
    chunk_duration_ms: int = 100

    @property
    def bytes_per_chunk(self) -> int:
        """Calculate bytes per chunk based on config."""
        samples_per_chunk = int(self.sample_rate * self.chunk_duration_ms / 1000)
        bytes_per_sample = self.bit_depth // 8
        return samples_per_chunk * self.channels * bytes_per_sample


@dataclass
class VADConfig:
    """
    Voice Activity Detection configuration.

    Attributes:
        enabled: Whether VAD is enabled
        energy_threshold: Audio energy threshold for speech detection (0.0-1.0)
        speech_start_ms: Milliseconds of speech before confirming start
        speech_end_ms: Milliseconds of silence before confirming end
        pre_buffer_ms: Milliseconds of audio to include before speech start
    """

    enabled: bool = True
    energy_threshold: float = 0.02
    speech_start_ms: int = 100
    speech_end_ms: int = 500
    pre_buffer_ms: int = 300


# =============================================================================
# Callbacks
# =============================================================================


@dataclass
class AudioCallbacks:
    """
    Callbacks for audio events.

    Attributes:
        on_speech_start: Called when user starts speaking
        on_speech_end: Called when user stops speaking (receives pre-buffer audio)
        on_playback_complete: Called when playback finishes
        on_error: Called when an error occurs (device disconnect, etc.)
    """

    on_speech_start: Optional[Callable[[], None]] = None
    on_speech_end: Optional[Callable[[bytes], None]] = None
    on_playback_complete: Optional[Callable[[], None]] = None
    on_error: Optional[Callable[[Exception], None]] = None


# =============================================================================
# Device Info
# =============================================================================


@dataclass
class AudioDevice:
    """
    Information about an audio device.

    Attributes:
        id: Device identifier
        name: Human-readable device name
        channels: Number of audio channels supported
        is_default: Whether this is the system default device
    """

    id: int
    name: str
    channels: int
    is_default: bool


# =============================================================================
# Port Interface
# =============================================================================


class AudioStreamPort(ABC):
    """
    Abstract interface for real-time audio capture and playback.

    Implementations handle platform-specific details:
    - VoxStreamAdapter: Desktop via sounddevice
    - WebRTCAudioAdapter: Web via WebSocket relay
    - TwilioAudioAdapter: Phone via Media Streams

    Audio Format:
        All audio is PCM16, 24kHz, Mono. Adapters handle format
        conversion internally if their platform uses different formats.

    Example:
        async with VoxStreamAdapter() as audio:
            audio.set_callbacks(AudioCallbacks(
                on_speech_start=handle_speech_start,
                on_speech_end=handle_speech_end,
                on_error=handle_error,
            ))

            async for chunk in audio.start_capture():
                await send_to_ai(chunk)
    """

    # =========================================================================
    # Format Constants
    # =========================================================================

    SAMPLE_RATE: int = 24000
    CHANNELS: int = 1
    FORMAT: str = "pcm16"

    # =========================================================================
    # Abstract Properties
    # =========================================================================

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier (e.g., 'voxstream', 'mock')."""
        pass

    # =========================================================================
    # Lifecycle
    # =========================================================================

    @abstractmethod
    async def __aenter__(self) -> "AudioStreamPort":
        """Enter async context and initialize resources."""
        ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context and cleanup resources."""
        ...

    # =========================================================================
    # Capture
    # =========================================================================

    @abstractmethod
    async def start_capture(self) -> AsyncGenerator[bytes, None]:
        """
        Start capturing audio from input device.

        Yields:
            Audio chunks as bytes (PCM16, 24kHz, mono).
            Chunk size determined by AudioStreamConfig.chunk_duration_ms.

        Raises:
            AudioStreamNotInitializedError: If not initialized (use 'async with').
            AudioStreamError: If already capturing.
            AudioStreamDeviceError: If device not available.

        Example:
            async for chunk in audio.start_capture():
                await process(chunk)
        """
        ...
        # Make this a generator
        yield b""

    @abstractmethod
    async def stop_capture(self) -> None:
        """Stop audio capture."""
        ...

    # =========================================================================
    # Playback
    # =========================================================================

    @abstractmethod
    async def play(self, chunk: bytes) -> None:
        """
        Play an audio chunk.

        Audio is buffered for smooth playback. Call end_playback()
        after sending all chunks to ensure complete playback.

        Args:
            chunk: Audio data as bytes (PCM16, 24kHz, mono)
        """
        ...

    @abstractmethod
    async def end_playback(self) -> None:
        """
        Signal that no more chunks will be sent.

        Call after sending all chunks to ensure buffered audio
        plays completely. Triggers on_playback_complete callback.
        """
        ...

    @abstractmethod
    async def stop_playback(self) -> None:
        """
        Stop playback immediately (barge-in).

        Clears any buffered audio. Use when user interrupts.
        """
        ...

    # =========================================================================
    # Callbacks
    # =========================================================================

    @abstractmethod
    def set_callbacks(self, callbacks: AudioCallbacks) -> None:
        """
        Set callbacks for audio events.

        Args:
            callbacks: AudioCallbacks with event handlers
        """
        ...

    # =========================================================================
    # Device Selection
    # =========================================================================

    @abstractmethod
    def list_input_devices(self) -> list[AudioDevice]:
        """
        List available input devices (microphones).

        Returns:
            List of AudioDevice with id, name, channels, is_default.
        """
        ...

    @abstractmethod
    def set_input_device(self, device_id: Optional[int]) -> None:
        """
        Set the input device to use for capture.

        Args:
            device_id: Device ID from list_input_devices(), or None for default.

        Raises:
            ValueError: If device_id is invalid.
            RuntimeError: If called while capturing.
        """
        ...

    # =========================================================================
    # Configuration
    # =========================================================================

    @abstractmethod
    def get_config(self) -> AudioStreamConfig:
        """Get current audio configuration."""
        ...
