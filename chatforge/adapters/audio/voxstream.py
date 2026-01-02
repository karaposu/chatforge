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
from typing import AsyncGenerator, Optional, TYPE_CHECKING

from chatforge.ports.audio_stream import (
    AudioStreamPort,
    AudioStreamConfig,
    AudioDevice,
    VADConfig,
    AudioCallbacks,
    AudioStreamError,
    AudioStreamNotInitializedError,
)

if TYPE_CHECKING:
    from voxstream.config.types import AudioState


__all__ = [
    "VoxStreamAdapter",
]


class VoxStreamAdapter(AudioStreamPort):
    """
    AudioStreamPort implementation using VoxStream.

    Provides low-latency audio I/O for desktop applications.

    Args:
        config: Audio stream configuration
        vad_config: Voice activity detection configuration
        mode: Processing mode ("realtime", "balanced", "quality")
        debug: Enable debug logging

    Example:
        async with VoxStreamAdapter() as audio:
            audio.set_callbacks(AudioCallbacks(
                on_speech_start=lambda: print("Speaking..."),
                on_speech_end=lambda audio: print(f"Got {len(audio)} bytes"),
            ))

            async for chunk in audio.start_capture():
                await process(chunk)
    """

    def __init__(
        self,
        config: Optional[AudioStreamConfig] = None,
        vad_config: Optional[VADConfig] = None,
        mode: str = "realtime",
        debug: bool = False,
    ):
        self._config = config or AudioStreamConfig()
        self._vad_config = vad_config or VADConfig()
        self._mode = mode
        self._debug = debug

        self._voxstream = None
        self._vad = None  # VADetector reference for callbacks
        self._callbacks = AudioCallbacks()
        self._input_device: Optional[int] = None
        # Note: We use VoxStream's state machine instead of manual _capturing flag

    def _log(self, message: str, data=None):
        """Debug log helper - writes to /tmp/voxterm_debug.log."""
        if self._debug:
            import time
            from datetime import datetime
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            line = f"[{ts}] [VoxStreamAdapter] {message}"
            if data is not None:
                if isinstance(data, bytes):
                    line += f" ({len(data)} bytes)"
                else:
                    line += f" | {data}"
            # Write to file to avoid interfering with TUI
            try:
                with open("/tmp/voxterm_debug.log", "a") as f:
                    f.write(line + "\n")
            except Exception:
                pass  # Ignore logging errors

    def enable_debug(self, enabled: bool = True):
        """Enable or disable debug logging."""
        self._debug = enabled

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "voxstream"

    @property
    def is_playing(self) -> bool:
        """Check if audio playback is active (any playback state)."""
        if self._voxstream:
            from voxstream.config.types import AudioState
            return self._voxstream.state in (
                AudioState.PLAYBACK_STARTING,
                AudioState.PLAYBACK_BUFFERING,
                AudioState.PLAYING,
                AudioState.PLAYBACK_DRAINING,
            )
        return False

    @property
    def audio_state(self) -> Optional["AudioState"]:
        """Get current VoxStream audio state (for debugging)."""
        if self._voxstream:
            return self._voxstream.state
        return None

    def _is_capture_active(self) -> bool:
        """Check if capture is active using VoxStream's state machine."""
        if not self._voxstream:
            return False
        from voxstream.config.types import AudioState
        return self._voxstream.state in (
            AudioState.CAPTURE_STARTING,
            AudioState.CAPTURING,
        )

    # =========================================================================
    # Config Conversion
    # =========================================================================

    def _to_vox_stream_config(self):
        """Convert our AudioStreamConfig to VoxStream's StreamConfig."""
        from voxstream.config.types import StreamConfig as VoxStreamConfig

        return VoxStreamConfig(
            sample_rate=self._config.sample_rate,
            channels=self._config.channels,
            bit_depth=self._config.bit_depth,
            chunk_duration_ms=self._config.chunk_duration_ms,
        )

    # =========================================================================
    # Lifecycle
    # =========================================================================

    async def __aenter__(self) -> "VoxStreamAdapter":
        """Initialize VoxStream."""
        from voxstream import VoxStream
        from voxstream.config.types import ProcessingMode

        mode_map = {
            "realtime": ProcessingMode.REALTIME,
            "balanced": ProcessingMode.BALANCED,
            "quality": ProcessingMode.QUALITY,
        }

        # Create VoxStream with proper config object
        self._voxstream = VoxStream(
            mode=mode_map.get(self._mode, ProcessingMode.REALTIME),
            config=self._to_vox_stream_config(),
        )

        # Configure VAD if enabled
        if self._vad_config.enabled:
            self._setup_vad()

        # Configure input device if set
        if self._input_device is not None:
            self._voxstream.configure_devices(input_device=self._input_device)

        # Setup state callbacks for debugging
        if self._debug:
            self._voxstream.set_state_callback(self._on_state_changed)

        # Setup error callback to route errors to our callback
        self._voxstream.set_error_callback(self._on_voxstream_error)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Cleanup VoxStream resources."""
        if self._voxstream:
            # Ensure clean state before cleanup
            try:
                await self._voxstream.ensure_idle(timeout=2.0)
            except Exception as e:
                self._log(f"ensure_idle failed during cleanup: {e}")

            # Clear all callbacks before cleanup
            self._voxstream.clear_callbacks()

            await self._voxstream.cleanup_async()
            self._voxstream = None
            self._vad = None

    # =========================================================================
    # VAD Setup (Internal)
    # =========================================================================

    def _setup_vad(self) -> None:
        """Configure VAD with internal callbacks."""
        from voxstream.voice.vad import VADetector
        from voxstream.config.types import VADConfig as VoxVADConfig, VADType

        # Map our 'enabled' field to VoxStream's 'type' field
        vox_config = VoxVADConfig(
            type=VADType.ENERGY_BASED,  # Our enabled=True means use energy-based VAD
            energy_threshold=self._vad_config.energy_threshold,
            speech_start_ms=self._vad_config.speech_start_ms,
            speech_end_ms=self._vad_config.speech_end_ms,
            pre_buffer_ms=self._vad_config.pre_buffer_ms,
        )

        # Pass audio_config for correct byte/sample calculations
        self._vad = VADetector(
            config=vox_config,
            audio_config=self._to_vox_stream_config(),
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
    # VoxStream State Callbacks
    # =========================================================================

    def _on_state_changed(self, old_state, new_state) -> None:
        """Handle VoxStream state changes (for debugging)."""
        self._log(f"VoxStream state: {old_state.value} -> {new_state.value}")

    def _on_voxstream_error(self, reason: str) -> None:
        """Handle VoxStream errors and route to our callback."""
        self._log(f"VoxStream error: {reason}")
        if self._callbacks.on_error:
            self._callbacks.on_error(AudioStreamError(reason))

    # =========================================================================
    # Capture
    # =========================================================================

    async def start_capture(self) -> AsyncGenerator[bytes, None]:
        """Start capturing audio from microphone."""
        self._log("start_capture() called", {
            "is_capture_active": self._is_capture_active(),
            "has_voxstream": self._voxstream is not None,
            "state": self._voxstream.state.value if self._voxstream else None,
        })

        if not self._voxstream:
            raise AudioStreamNotInitializedError(
                "Adapter not initialized. Use 'async with' context."
            )

        # Use VoxStream's state machine to check if already capturing
        if self._is_capture_active():
            self._log("ERROR: Already capturing!")
            raise AudioStreamError("Already capturing.")

        # Ensure we're in IDLE state before starting capture
        # This handles the case where playback is still active
        from voxstream.config.types import AudioState
        if self._voxstream.state != AudioState.IDLE:
            self._log(f"Not idle (state={self._voxstream.state.value}), calling ensure_idle()...")
            await self._voxstream.ensure_idle(timeout=2.0)
            self._log(f"ensure_idle() complete, state={self._voxstream.state.value}")

        self._log("Starting capture stream...")
        queue = await self._voxstream.start_capture_stream()
        self._log("Capture stream started", {"state": self._voxstream.state.value})

        chunk_count = 0
        try:
            # Use VoxStream's state machine for loop condition (single source of truth)
            while self._is_capture_active():
                try:
                    chunk = await asyncio.wait_for(
                        queue.get(),
                        timeout=0.1,  # 100ms timeout for responsive shutdown
                    )
                    chunk_count += 1
                    if chunk_count == 1:
                        self._log("First chunk from voxstream", chunk)
                    # Feed to VAD if enabled
                    if self._vad:
                        self._vad.process_chunk(chunk)
                    yield chunk
                except asyncio.TimeoutError:
                    continue
        finally:
            self._log(f"start_capture() generator exiting, total chunks: {chunk_count}")

    async def stop_capture(self) -> None:
        """Stop audio capture."""
        self._log("stop_capture() called", {
            "is_capture_active": self._is_capture_active(),
            "state": self._voxstream.state.value if self._voxstream else None,
        })

        if self._voxstream:
            try:
                self._log("Calling voxstream.stop_capture_stream()...")
                await self._voxstream.stop_capture_stream()
                self._log("voxstream.stop_capture_stream() completed", {
                    "state": self._voxstream.state.value
                })
            except Exception as e:
                self._log(f"voxstream.stop_capture_stream() error: {e}")

        self._log("stop_capture() done")

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

        # Wire playback completion callback to VoxStream using new API
        if self._voxstream and callbacks.on_playback_complete:
            self._voxstream.set_playback_complete_callback(
                callbacks.on_playback_complete
            )

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

    def set_input_device(self, device_id: Optional[int]) -> None:
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
