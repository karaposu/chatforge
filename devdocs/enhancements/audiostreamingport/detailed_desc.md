# AudioStreamPort: Detailed Design

**Date:** 2025-01-01
**Status:** Ready for Implementation
**Priority:** High
**Revision:** 2 (post-critic review)

---

## Overview

**AudioStreamPort** abstracts real-time audio capture and playback across platforms, enabling voice AI applications to work on desktop, web, and phone without changing domain logic.

```
VoiceAgent (domain logic)
    │
    ▼
AudioStreamPort (interface)
    │
    ├── VoxStreamAdapter (desktop - sounddevice)
    ├── WebRTCAudioAdapter (web - WebSocket relay)
    └── TwilioAudioAdapter (phone - Media Streams)
```

---

## Port Interface

### File: `chatforge/ports/audio_stream.py`

```python
"""
AudioStreamPort - Abstract interface for real-time audio I/O.

This port enables voice applications to capture microphone input
and play audio output without coupling to specific hardware or
platform implementations.

Audio Format: PCM16, 24kHz, Mono (matches OpenAI Realtime API)

Usage:
    from chatforge.ports.audio_stream import AudioStreamPort

    class VoiceAgent:
        def __init__(self, audio: AudioStreamPort):
            self.audio = audio

        async def run(self):
            async for chunk in self.audio.start_capture():
                await self.process_audio(chunk)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator, Callable


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
    on_speech_start: Callable[[], None] | None = None
    on_speech_end: Callable[[bytes], None] | None = None
    on_playback_complete: Callable[[], None] | None = None
    on_error: Callable[[Exception], None] | None = None


# =============================================================================
# Device Info
# =============================================================================


@dataclass
class AudioDevice:
    """Information about an audio device."""
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
            RuntimeError: If already capturing or not initialized.

        Example:
            async for chunk in audio.start_capture():
                await process(chunk)
        """
        ...

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
    def set_input_device(self, device_id: int | None) -> None:
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
```

---

## VoxStream Adapter

### File: `chatforge/adapters/audio/voxstream.py`

```python
"""
VoxStreamAdapter - AudioStreamPort implementation for desktop.

Uses VoxStream library for direct microphone/speaker access
via sounddevice (PortAudio).

Requirements:
    pip install voxstream

Usage:
    from chatforge.adapters.audio import VoxStreamAdapter

    async with VoxStreamAdapter() as audio:
        async for chunk in audio.start_capture():
            print(f"Got {len(chunk)} bytes")
"""

import asyncio
from typing import AsyncGenerator

from chatforge.ports.audio_stream import (
    AudioStreamPort,
    AudioStreamConfig,
    AudioDevice,
    VADConfig,
    AudioCallbacks,
)


class VoxStreamAdapter(AudioStreamPort):
    """
    AudioStreamPort implementation using VoxStream.

    Provides low-latency audio I/O for desktop applications.

    Args:
        config: Audio stream configuration
        vad_config: Voice activity detection configuration
        mode: Processing mode ("realtime", "balanced", "quality")
    """

    def __init__(
        self,
        config: AudioStreamConfig | None = None,
        vad_config: VADConfig | None = None,
        mode: str = "realtime",
    ):
        self._config = config or AudioStreamConfig()
        self._vad_config = vad_config or VADConfig()
        self._mode = mode

        self._voxstream = None
        self._vad = None  # VADetector reference for callbacks
        self._capture_queue: asyncio.Queue | None = None
        self._callbacks = AudioCallbacks()
        self._capturing = False
        self._input_device: int | None = None

    # =========================================================================
    # Lifecycle
    # =========================================================================

    async def __aenter__(self) -> "VoxStreamAdapter":
        """Initialize VoxStream."""
        from voxstream import VoxStream
        from voxstream.config.types import ProcessingMode, VADConfig as VoxVADConfig

        mode_map = {
            "realtime": ProcessingMode.REALTIME,
            "balanced": ProcessingMode.BALANCED,
            "quality": ProcessingMode.QUALITY,
        }

        self._voxstream = VoxStream(
            mode=mode_map.get(self._mode, ProcessingMode.REALTIME),
            sample_rate=self._config.sample_rate,
        )

        # Configure VAD if enabled
        if self._vad_config.enabled:
            self._setup_vad()

        # Configure input device if set
        if self._input_device is not None:
            self._voxstream.configure_devices(input_device=self._input_device)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Cleanup VoxStream resources."""
        if self._voxstream:
            await self._voxstream.cleanup_async()
            self._voxstream = None
            self._vad = None

    # =========================================================================
    # VAD Setup (Internal)
    # =========================================================================

    def _setup_vad(self) -> None:
        """Configure VAD with internal callbacks."""
        from voxstream.voice.vad import VADetector
        from voxstream.config.types import VADConfig as VoxVADConfig

        vox_config = VoxVADConfig(
            energy_threshold=self._vad_config.energy_threshold,
            speech_start_ms=self._vad_config.speech_start_ms,
            speech_end_ms=self._vad_config.speech_end_ms,
            pre_buffer_ms=self._vad_config.pre_buffer_ms,
        )

        self._vad = VADetector(
            config=vox_config,
            on_speech_start=self._on_speech_start,
            on_speech_end=self._on_speech_end,
        )

    def _on_speech_start(self) -> None:
        """Internal callback - VoxStream passes no arguments."""
        if self._callbacks.on_speech_start:
            try:
                self._callbacks.on_speech_start()
            except Exception as e:
                self._handle_callback_error(e)

    def _on_speech_end(self) -> None:
        """Internal callback - retrieve pre-buffer and pass to user callback."""
        if self._callbacks.on_speech_end and self._vad:
            try:
                pre_buffer = self._vad.get_pre_buffer()
                if pre_buffer:
                    self._callbacks.on_speech_end(pre_buffer)
            except Exception as e:
                self._handle_callback_error(e)

    def _handle_callback_error(self, error: Exception) -> None:
        """Route callback errors to on_error handler."""
        if self._callbacks.on_error:
            self._callbacks.on_error(error)

    # =========================================================================
    # Capture
    # =========================================================================

    async def start_capture(self) -> AsyncGenerator[bytes, None]:
        """Start capturing audio from microphone."""
        if not self._voxstream:
            raise RuntimeError("Adapter not initialized. Use 'async with' context.")
        if self._capturing:
            raise RuntimeError("Already capturing.")

        self._capturing = True
        self._capture_queue = await self._voxstream.start_capture_stream()

        try:
            while self._capturing:
                try:
                    chunk = await asyncio.wait_for(
                        self._capture_queue.get(),
                        timeout=0.1  # 100ms timeout for responsive shutdown
                    )
                    # Feed to VAD if enabled
                    if self._vad:
                        self._vad.process_chunk(chunk)
                    yield chunk
                except asyncio.TimeoutError:
                    continue
        finally:
            self._capturing = False

    async def stop_capture(self) -> None:
        """Stop audio capture."""
        self._capturing = False

    # =========================================================================
    # Playback
    # =========================================================================

    async def play(self, chunk: bytes) -> None:
        """Play audio chunk (buffered)."""
        if self._voxstream:
            self._voxstream.queue_playback(chunk)

    async def end_playback(self) -> None:
        """Signal end of audio stream."""
        if self._voxstream:
            self._voxstream.mark_playback_complete()

    async def stop_playback(self) -> None:
        """Stop playback immediately (barge-in)."""
        if self._voxstream:
            self._voxstream.interrupt_playback(force=True)

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
        """List available input devices."""
        from voxstream.io.capture import DirectAudioCapture

        devices = DirectAudioCapture.list_devices()
        return [
            AudioDevice(
                id=d["index"],
                name=d["name"],
                channels=d["channels"],
                is_default=d["default"],
            )
            for d in devices
        ]

    def set_input_device(self, device_id: int | None) -> None:
        """Set the input device."""
        if self._capturing:
            raise RuntimeError("Cannot change device while capturing.")
        self._input_device = device_id
        if self._voxstream:
            self._voxstream.configure_devices(input_device=device_id)

    # =========================================================================
    # Configuration
    # =========================================================================

    def get_config(self) -> AudioStreamConfig:
        """Get audio configuration."""
        return self._config
```

---

## Mock Adapter (for Testing)

### File: `chatforge/adapters/audio/mock.py`

```python
"""
MockAudioStreamAdapter - For testing without hardware.

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
"""

import asyncio
from typing import AsyncGenerator

from chatforge.ports.audio_stream import (
    AudioStreamPort,
    AudioStreamConfig,
    AudioDevice,
    AudioCallbacks,
)


class MockAudioStreamAdapter(AudioStreamPort):
    """
    Mock AudioStreamPort for testing.

    Args:
        capture_audio: Pre-recorded audio to yield during capture
        chunk_size: Size of chunks to yield
        capture_delay_ms: Delay between chunks (simulates real-time)
    """

    def __init__(
        self,
        capture_audio: bytes | None = None,
        chunk_size: int = 4800,  # 100ms at 24kHz mono 16-bit
        capture_delay_ms: int = 100,
    ):
        self._capture_audio = capture_audio or b""
        self._chunk_size = chunk_size
        self._capture_delay = capture_delay_ms / 1000

        self._config = AudioStreamConfig()
        self._callbacks = AudioCallbacks()
        self._capturing = False
        self._input_device: int | None = None

        # For assertions in tests
        self.played_chunks: list[bytes] = []
        self.capture_started = False
        self.capture_stopped = False
        self.playback_stopped = False
        self.end_playback_called = False

    async def __aenter__(self) -> "MockAudioStreamAdapter":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    async def start_capture(self) -> AsyncGenerator[bytes, None]:
        """Yield pre-recorded audio in chunks."""
        if self._capturing:
            raise RuntimeError("Already capturing.")

        self.capture_started = True
        self._capturing = True

        try:
            for i in range(0, len(self._capture_audio), self._chunk_size):
                if not self._capturing:
                    break
                chunk = self._capture_audio[i:i + self._chunk_size]
                await asyncio.sleep(self._capture_delay)
                yield chunk
        finally:
            self._capturing = False

    async def stop_capture(self) -> None:
        self._capturing = False
        self.capture_stopped = True

    async def play(self, chunk: bytes) -> None:
        self.played_chunks.append(chunk)

    async def end_playback(self) -> None:
        self.end_playback_called = True
        if self._callbacks.on_playback_complete:
            self._callbacks.on_playback_complete()

    async def stop_playback(self) -> None:
        self.playback_stopped = True

    def set_callbacks(self, callbacks: AudioCallbacks) -> None:
        self._callbacks = callbacks

    def list_input_devices(self) -> list[AudioDevice]:
        """Return mock devices."""
        return [
            AudioDevice(id=0, name="Mock Microphone", channels=1, is_default=True),
            AudioDevice(id=1, name="Mock USB Mic", channels=2, is_default=False),
        ]

    def set_input_device(self, device_id: int | None) -> None:
        if self._capturing:
            raise RuntimeError("Cannot change device while capturing.")
        self._input_device = device_id

    def get_config(self) -> AudioStreamConfig:
        return self._config

    # =========================================================================
    # Test Helpers
    # =========================================================================

    def simulate_speech_start(self) -> None:
        """Simulate user starting to speak."""
        if self._callbacks.on_speech_start:
            self._callbacks.on_speech_start()

    def simulate_speech_end(self, audio: bytes = b"") -> None:
        """Simulate user stopping speaking."""
        if self._callbacks.on_speech_end:
            self._callbacks.on_speech_end(audio)

    def simulate_error(self, error: Exception) -> None:
        """Simulate an error (device disconnect, etc.)."""
        if self._callbacks.on_error:
            self._callbacks.on_error(error)

    def get_total_played_bytes(self) -> int:
        """Get total bytes played."""
        return sum(len(c) for c in self.played_chunks)
```

---

## Usage Examples

### Basic Capture and Playback

```python
from chatforge.adapters.audio import VoxStreamAdapter

async def main():
    async with VoxStreamAdapter() as audio:
        # Capture 5 seconds of audio
        chunks = []
        async for chunk in audio.start_capture():
            chunks.append(chunk)
            if len(chunks) >= 50:  # 50 * 100ms = 5 seconds
                await audio.stop_capture()
                break

        # Play it back
        for chunk in chunks:
            await audio.play(chunk)

        await audio.end_playback()
```

### With VAD Callbacks

```python
from chatforge.adapters.audio import VoxStreamAdapter
from chatforge.ports.audio_stream import AudioCallbacks

async def main():
    async with VoxStreamAdapter() as audio:
        # Set up callbacks
        audio.set_callbacks(AudioCallbacks(
            on_speech_start=lambda: print("User started speaking"),
            on_speech_end=lambda audio: print(f"User stopped, got {len(audio)} bytes"),
            on_playback_complete=lambda: print("Playback finished"),
            on_error=lambda e: print(f"Error: {e}"),
        ))

        # Capture and process
        async for chunk in audio.start_capture():
            # Send to AI, etc.
            pass
```

### Device Selection

```python
from chatforge.adapters.audio import VoxStreamAdapter

async def main():
    async with VoxStreamAdapter() as audio:
        # List available microphones
        devices = audio.list_input_devices()
        for d in devices:
            print(f"{d.id}: {d.name} {'(default)' if d.is_default else ''}")

        # Select a specific device
        audio.set_input_device(1)  # Use device ID 1

        # Now capture from that device
        async for chunk in audio.start_capture():
            process(chunk)
```

### VoiceAgent Integration

```python
from chatforge.ports.audio_stream import AudioStreamPort, AudioCallbacks
from chatforge.ports.realtime import RealtimeVoiceAPIPort

class VoiceAgent:
    """Voice conversation agent using AudioStreamPort."""

    def __init__(
        self,
        audio: AudioStreamPort,
        realtime: RealtimeVoiceAPIPort,
    ):
        self.audio = audio
        self.realtime = realtime

        # Wire up callbacks for barge-in
        self.audio.set_callbacks(AudioCallbacks(
            on_speech_start=self._handle_speech_start,
            on_speech_end=self._handle_speech_end,
            on_error=self._handle_error,
        ))

    async def _handle_speech_start(self):
        """User started speaking - stop AI and listen."""
        await self.audio.stop_playback()
        await self.realtime.interrupt()

    async def _handle_speech_end(self, audio: bytes):
        """User stopped speaking - trigger AI response."""
        await self.realtime.commit_audio()

    async def _handle_error(self, error: Exception):
        """Handle audio errors (device disconnect, etc.)."""
        print(f"Audio error: {error}")

    async def run(self):
        """Main conversation loop."""
        import asyncio

        async def capture_loop():
            async for chunk in self.audio.start_capture():
                await self.realtime.send_audio(chunk)

        async def playback_loop():
            async for event in self.realtime.events():
                if event.type == "audio.chunk":
                    await self.audio.play(event.data)
                elif event.type == "response.done":
                    await self.audio.end_playback()

        await asyncio.gather(capture_loop(), playback_loop())
```

### Testing Without Hardware

```python
import pytest
from chatforge.adapters.audio import MockAudioStreamAdapter
from chatforge.ports.audio_stream import AudioCallbacks

@pytest.mark.asyncio
async def test_voice_agent_plays_response():
    # Create mock with test audio
    test_audio = b"\x00\x01" * 2400  # 100ms of audio
    audio = MockAudioStreamAdapter(capture_audio=test_audio)

    async with audio:
        # Capture
        chunks = []
        async for chunk in audio.start_capture():
            chunks.append(chunk)

        # Simulate playing response
        await audio.play(b"\x00\x02" * 2400)
        await audio.end_playback()

    # Assertions
    assert audio.capture_started
    assert len(audio.played_chunks) == 1
    assert audio.get_total_played_bytes() == 4800
    assert audio.end_playback_called


@pytest.mark.asyncio
async def test_error_callback():
    audio = MockAudioStreamAdapter()
    errors = []

    async with audio:
        audio.set_callbacks(AudioCallbacks(
            on_error=lambda e: errors.append(e),
        ))

        # Simulate device disconnect
        audio.simulate_error(RuntimeError("Device disconnected"))

    assert len(errors) == 1
    assert "disconnected" in str(errors[0])
```

---

## File Structure

```
chatforge/
├── ports/
│   └── audio_stream.py          # Port interface + config classes
│
├── adapters/
│   └── audio/
│       ├── __init__.py          # Exports adapters
│       ├── voxstream.py         # VoxStreamAdapter
│       └── mock.py              # MockAudioStreamAdapter
│
└── services/
    └── audio_stream.py          # AudioStreamService (optional, for convenience)
```

---

## Service Layer (Optional)

Following the TTSService pattern:

```python
# chatforge/services/audio_stream.py

class AudioStreamService:
    """
    High-level audio streaming service.

    Usage:
        async with AudioStreamService("voxstream") as audio:
            async for chunk in audio.capture():
                process(chunk)
    """

    def __init__(self, adapter: str = "voxstream"):
        self.adapter_type = adapter
        self._adapter: AudioStreamPort | None = None

    async def __aenter__(self) -> "AudioStreamService":
        self._adapter = self._create_adapter()
        await self._adapter.__aenter__()
        return self

    async def __aexit__(self, *args) -> None:
        if self._adapter:
            await self._adapter.__aexit__(*args)

    def _create_adapter(self) -> AudioStreamPort:
        if self.adapter_type == "voxstream":
            from chatforge.adapters.audio import VoxStreamAdapter
            return VoxStreamAdapter()
        elif self.adapter_type == "mock":
            from chatforge.adapters.audio import MockAudioStreamAdapter
            return MockAudioStreamAdapter()
        else:
            raise ValueError(f"Unknown adapter: {self.adapter_type}")

    async def capture(self):
        """Start capturing audio."""
        async for chunk in self._adapter.start_capture():
            yield chunk

    async def play(self, chunk: bytes) -> None:
        """Play audio chunk."""
        await self._adapter.play(chunk)

    async def end_playback(self) -> None:
        """Signal end of playback."""
        await self._adapter.end_playback()

    # ... delegate other methods to self._adapter
```

---

## Implementation Checklist

- [ ] Create `chatforge/ports/audio_stream.py` with interface
- [ ] Create `chatforge/adapters/audio/__init__.py`
- [ ] Create `chatforge/adapters/audio/voxstream.py`
- [ ] Create `chatforge/adapters/audio/mock.py`
- [ ] Add tests in `tests/adapters/audio/`
- [ ] Optional: Create `chatforge/services/audio_stream.py`
- [ ] Update `chatforge/ports/__init__.py` exports
- [ ] Update `chatforge/adapters/__init__.py` exports

---

## Dependencies

```
# For VoxStreamAdapter
voxstream>=0.1.0

# VoxStream depends on:
sounddevice>=0.4.0
numpy>=1.20.0
```

---

## Design Decisions (Resolved)

These decisions were made based on VoxStream source code inspection. See `gaps_to_fill/answers/` for details.

### 1. VAD Callback Signature

**Decision:** Port callbacks receive audio bytes; adapter handles retrieval.

VoxStream's callbacks take NO arguments (`Callable[[], None]`). The adapter:
1. Registers internal callbacks with VoxStream VAD
2. Calls `vad.get_pre_buffer()` when speech ends
3. Passes the audio bytes to the application callback

```python
# In VoxStreamAdapter:
def _on_speech_end(self):
    """Internal callback that retrieves pre-buffer"""
    if self._vad and self._callbacks.on_speech_end:
        pre_buffer = self._vad.get_pre_buffer()
        if pre_buffer:
            self._callbacks.on_speech_end(pre_buffer)
```

### 2. Capture Return Type

**Decision:** Use `AsyncGenerator[bytes, None]` in port interface.

VoxStream returns `asyncio.Queue[bytes]`. The adapter wraps it:

```python
async def start_capture(self) -> AsyncGenerator[bytes, None]:
    queue = await self._voxstream.start_capture_stream()
    while self._capturing:
        try:
            chunk = await asyncio.wait_for(queue.get(), timeout=1.0)
            yield chunk
        except asyncio.TimeoutError:
            continue
```

Benefits:
- Cleaner interface: `async for chunk in audio.start_capture()`
- Hides implementation detail (Queue)
- Consistent with Python async patterns

### 3. Audio Format

**Confirmed:** PCM16, 24kHz, Mono matches both VoxStream and OpenAI Realtime API.
No format conversion needed when these are used together.

---

## Implementation Status

| Blocker | Status |
|---------|--------|
| VAD pre-buffer retrieval | **RESOLVED** - `vad.get_pre_buffer()` returns bytes |
| Callback signature design | **RESOLVED** - Adapter wraps and provides audio |
| Queue vs AsyncGenerator | **RESOLVED** - Use AsyncGenerator, adapter wraps Queue |
| Audio format compatibility | **RESOLVED** - PCM16, 24kHz, Mono works for all |

**Ready for implementation.** See `gaps_to_fill/` for remaining testing items (barge-in behavior, device disconnect handling).

---

## Next Steps

1. **Implement port interface** - `chatforge/ports/audio_stream.py`
2. **Implement VoxStreamAdapter** - Wire up to VoxStream library
3. **Implement MockAdapter** - For testing
4. **Write tests** - Capture, playback, VAD callbacks
5. **Integrate with VoiceAgent** - When RealtimeVoiceAPIPort is ready
