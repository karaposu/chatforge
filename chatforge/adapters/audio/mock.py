"""
MockAudioStreamAdapter - For testing without hardware.

Provides a mock implementation of AudioStreamPort that:
- Yields pre-recorded audio during capture
- Collects played chunks for assertions
- Allows manual triggering of VAD and error events

Usage:
    # Test with pre-recorded audio
    audio = MockAudioStreamAdapter(
        capture_audio=load_wav("test_hello.wav")
    )

    async with audio:
        async for chunk in audio.start_capture():
            process(chunk)

    # Check what was played
    assert len(audio.played_chunks) > 0
    assert audio.end_playback_called
"""

import asyncio
from typing import AsyncGenerator, Optional

from chatforge.ports.audio_stream import (
    AudioStreamPort,
    AudioStreamConfig,
    AudioDevice,
    AudioCallbacks,
    AudioStreamError,
)


__all__ = [
    "MockAudioStreamAdapter",
]


class MockAudioStreamAdapter(AudioStreamPort):
    """
    Mock AudioStreamPort for testing.

    Provides controllable audio I/O for unit tests without
    requiring actual audio hardware.

    Args:
        capture_audio: Pre-recorded audio bytes to yield during capture
        chunk_size: Size of chunks to yield (default: 4800 = 100ms at 24kHz mono 16-bit)
        capture_delay_ms: Delay between chunks to simulate real-time (default: 100ms)

    Attributes:
        played_chunks: List of chunks passed to play()
        capture_started: True if start_capture() was called
        capture_stopped: True if stop_capture() was called
        playback_stopped: True if stop_playback() was called
        end_playback_called: True if end_playback() was called

    Example:
        async def test_voice_agent():
            mock = MockAudioStreamAdapter(capture_audio=b"\\x00\\x01" * 4800)

            async with mock:
                chunks = [c async for c in mock.start_capture()]
                await mock.play(b"response_audio")
                await mock.end_playback()

            assert mock.capture_started
            assert len(mock.played_chunks) == 1
            assert mock.end_playback_called
    """

    def __init__(
        self,
        capture_audio: Optional[bytes] = None,
        chunk_size: int = 4800,  # 100ms at 24kHz mono 16-bit
        capture_delay_ms: int = 100,
    ):
        self._capture_audio = capture_audio or b""
        self._chunk_size = chunk_size
        self._capture_delay = capture_delay_ms / 1000

        self._config = AudioStreamConfig()
        self._callbacks = AudioCallbacks()
        self._capturing = False
        self._input_device: Optional[int] = None

        # Test state for assertions
        self.played_chunks: list[bytes] = []
        self.capture_started: bool = False
        self.capture_stopped: bool = False
        self.playback_stopped: bool = False
        self.end_playback_called: bool = False

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "mock"

    # =========================================================================
    # Lifecycle
    # =========================================================================

    async def __aenter__(self) -> "MockAudioStreamAdapter":
        """Enter async context (no-op for mock)."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context (no-op for mock)."""
        pass

    # =========================================================================
    # Capture
    # =========================================================================

    async def start_capture(self) -> AsyncGenerator[bytes, None]:
        """Yield pre-recorded audio in chunks."""
        if self._capturing:
            raise AudioStreamError("Already capturing.")

        self.capture_started = True
        self._capturing = True

        try:
            for i in range(0, len(self._capture_audio), self._chunk_size):
                if not self._capturing:
                    break
                chunk = self._capture_audio[i : i + self._chunk_size]
                await asyncio.sleep(self._capture_delay)  # Simulate real-time
                yield chunk
        finally:
            self._capturing = False

    async def stop_capture(self) -> None:
        """Stop audio capture."""
        self._capturing = False
        self.capture_stopped = True

    # =========================================================================
    # Playback
    # =========================================================================

    async def play(self, chunk: bytes) -> None:
        """Record played chunk for assertions."""
        self.played_chunks.append(chunk)

    async def end_playback(self) -> None:
        """Signal end of playback and trigger callback."""
        self.end_playback_called = True
        if self._callbacks.on_playback_complete:
            self._callbacks.on_playback_complete()

    async def stop_playback(self) -> None:
        """Stop playback (barge-in)."""
        self.playback_stopped = True

    # =========================================================================
    # Callbacks
    # =========================================================================

    def set_callbacks(self, callbacks: AudioCallbacks) -> None:
        """Set callbacks for audio events."""
        self._callbacks = callbacks

    # =========================================================================
    # Device Selection
    # =========================================================================

    def list_input_devices(self) -> list[AudioDevice]:
        """Return mock devices."""
        return [
            AudioDevice(id=0, name="Mock Microphone", channels=1, is_default=True),
            AudioDevice(id=1, name="Mock USB Mic", channels=2, is_default=False),
        ]

    def set_input_device(self, device_id: Optional[int]) -> None:
        """Set the input device."""
        if self._capturing:
            raise RuntimeError("Cannot change device while capturing.")
        self._input_device = device_id

    # =========================================================================
    # Configuration
    # =========================================================================

    def get_config(self) -> AudioStreamConfig:
        """Get audio configuration."""
        return self._config

    # =========================================================================
    # Test Helpers
    # =========================================================================

    def simulate_speech_start(self) -> None:
        """
        Simulate user starting to speak.

        Triggers the on_speech_start callback if set.
        """
        if self._callbacks.on_speech_start:
            self._callbacks.on_speech_start()

    def simulate_speech_end(self, audio: bytes = b"") -> None:
        """
        Simulate user stopping speaking.

        Triggers the on_speech_end callback with the provided audio
        (simulating the pre-buffer).

        Args:
            audio: Audio bytes to pass to callback (simulates pre-buffer)
        """
        if self._callbacks.on_speech_end:
            self._callbacks.on_speech_end(audio)

    def simulate_error(self, error: Exception) -> None:
        """
        Simulate an error (device disconnect, etc.).

        Triggers the on_error callback if set.

        Args:
            error: Exception to pass to callback
        """
        if self._callbacks.on_error:
            self._callbacks.on_error(error)

    def get_total_played_bytes(self) -> int:
        """
        Get total bytes played.

        Returns:
            Sum of lengths of all played chunks.
        """
        return sum(len(c) for c in self.played_chunks)

    def reset(self) -> None:
        """
        Reset all test state.

        Clears played_chunks and resets all flags to initial state.
        Useful for reusing a mock across multiple test cases.
        """
        self.played_chunks = []
        self.capture_started = False
        self.capture_stopped = False
        self.playback_stopped = False
        self.end_playback_called = False
        self._capturing = False
