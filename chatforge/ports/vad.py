"""
VADPort - Abstract interface for Voice Activity Detection.

This port provides platform-agnostic voice activity detection that can be
used across desktop, web, and mobile applications.

Implementations handle different VAD algorithms:
- EnergyVADAdapter: Simple RMS energy threshold (fast, no dependencies)
- SileroVADAdapter: ML-based neural network (accurate, requires torch)
- AdaptiveEnergyVADAdapter: Energy-based with adaptive threshold

State Machine:
    SILENCE → SPEECH_STARTING → SPEECH → SPEECH_ENDING → SILENCE

    - SPEECH_STARTING: Accumulating speech frames (waiting for speech_start_ms)
    - SPEECH_ENDING: Accumulating silence frames (waiting for speech_end_ms)

Thread Safety:
    process_chunk() may run in audio callback thread. Implementations must:
    - Complete in <10ms
    - Minimize allocations
    - Use pre-allocated buffers

Usage:
    from chatforge.ports.vad import VADPort, VADConfig
    from chatforge.adapters.vad import EnergyVADAdapter

    vad = EnergyVADAdapter(VADConfig(energy_threshold=0.02))
    vad.set_callbacks(
        on_speech_start=lambda: print("Speaking"),
        on_speech_end=lambda: print("Done"),
    )

    for chunk in audio_stream:
        result = vad.process_chunk(chunk)
        if result.is_speaking:
            send_to_ai(chunk)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


__all__ = [
    # Exceptions
    "VADError",
    "VADConfigError",
    # Enums
    "SpeechState",
    # Data classes
    "VADConfig",
    "VADResult",
    "VADMetrics",
    # Port
    "VADPort",
]


# =============================================================================
# Exceptions
# =============================================================================


class VADError(Exception):
    """Base exception for VAD errors."""

    pass


class VADConfigError(VADError):
    """Invalid VAD configuration."""

    pass


# =============================================================================
# Enums
# =============================================================================


class SpeechState(Enum):
    """
    Voice activity detection states.

    State machine:
        SILENCE → SPEECH_STARTING → SPEECH → SPEECH_ENDING → SILENCE

    SPEECH_STARTING and SPEECH_ENDING are accumulation states where
    the VAD waits for the configured duration before transitioning.
    """

    SILENCE = "silence"
    """No speech detected."""

    SPEECH_STARTING = "speech_starting"
    """Speech detected, accumulating frames to confirm (waiting for speech_start_ms)."""

    SPEECH = "speech"
    """Confirmed speech in progress."""

    SPEECH_ENDING = "speech_ending"
    """Silence detected during speech, accumulating to confirm end (waiting for speech_end_ms)."""


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class VADConfig:
    """
    Voice Activity Detection configuration.

    Attributes:
        energy_threshold: RMS energy threshold for speech detection (0.0-1.0).
            Higher values require louder audio to trigger speech.
            Default: 0.02 (works for most environments)

        speech_start_ms: Milliseconds of consecutive speech required to
            confirm speech start. Prevents false triggers from transient sounds.
            Default: 100ms

        speech_end_ms: Milliseconds of consecutive silence required to
            confirm speech end. Prevents premature cutoff during pauses.
            Default: 500ms

        pre_buffer_ms: Milliseconds of audio to buffer before speech detection.
            This audio is available via get_pre_buffer() when speech starts,
            ensuring the beginning of speech is not lost.
            Default: 300ms

        sample_rate: Audio sample rate in Hz.
            Default: 24000 (OpenAI Realtime API standard)

        channels: Number of audio channels.
            Default: 1 (mono)

        bit_depth: Bits per sample.
            Default: 16 (PCM16)
    """

    energy_threshold: float = 0.02
    speech_start_ms: int = 100
    speech_end_ms: int = 500
    pre_buffer_ms: int = 300
    sample_rate: int = 24000
    channels: int = 1
    bit_depth: int = 16

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not 0.0 < self.energy_threshold <= 1.0:
            raise VADConfigError(
                f"energy_threshold must be between 0.0 and 1.0, got {self.energy_threshold}"
            )
        if self.speech_start_ms < 0:
            raise VADConfigError(
                f"speech_start_ms must be non-negative, got {self.speech_start_ms}"
            )
        if self.speech_end_ms < 0:
            raise VADConfigError(
                f"speech_end_ms must be non-negative, got {self.speech_end_ms}"
            )
        if self.pre_buffer_ms < 0:
            raise VADConfigError(
                f"pre_buffer_ms must be non-negative, got {self.pre_buffer_ms}"
            )
        if self.sample_rate <= 0:
            raise VADConfigError(
                f"sample_rate must be positive, got {self.sample_rate}"
            )
        if self.channels <= 0:
            raise VADConfigError(f"channels must be positive, got {self.channels}")
        if self.bit_depth not in (8, 16, 24, 32):
            raise VADConfigError(
                f"bit_depth must be 8, 16, 24, or 32, got {self.bit_depth}"
            )

    @property
    def bytes_per_second(self) -> int:
        """Calculate bytes per second of audio."""
        return self.sample_rate * self.channels * (self.bit_depth // 8)

    @property
    def bytes_per_ms(self) -> float:
        """Calculate bytes per millisecond of audio."""
        return self.bytes_per_second / 1000.0


# =============================================================================
# Result Types
# =============================================================================


@dataclass
class VADResult:
    """
    Result from processing an audio chunk.

    Attributes:
        state: Current speech state (SILENCE, SPEECH_STARTING, SPEECH, SPEECH_ENDING)
        is_speech: Whether current chunk contains speech (energy above threshold)
        is_speaking: Whether in confirmed speech state (SPEECH or transitional states)
        energy: RMS energy level of the chunk (0.0-1.0)
        state_duration_ms: Time spent in current state
    """

    state: SpeechState
    is_speech: bool
    is_speaking: bool
    energy: float
    state_duration_ms: float


@dataclass
class VADMetrics:
    """
    Performance metrics for VAD.

    Attributes:
        total_chunks: Total number of chunks processed
        speech_chunks: Chunks with energy above threshold
        silence_chunks: Chunks with energy below threshold
        speech_starting_chunks: Chunks processed in SPEECH_STARTING state
        speech_ending_chunks: Chunks processed in SPEECH_ENDING state
        transitions: Total state transitions
        speech_segments: Number of complete speech segments detected
        total_speech_ms: Total time in speech states
        total_silence_ms: Total time in silence
        avg_processing_ms: Average processing time per chunk
    """

    total_chunks: int = 0
    speech_chunks: int = 0
    silence_chunks: int = 0
    speech_starting_chunks: int = 0
    speech_ending_chunks: int = 0
    transitions: int = 0
    speech_segments: int = 0
    total_speech_ms: float = 0.0
    total_silence_ms: float = 0.0
    avg_processing_ms: float = 0.0

    # Internal tracking (not part of public interface)
    _total_processing_ms: float = field(default=0.0, repr=False)

    def record_chunk(self, processing_ms: float) -> None:
        """Record processing time for a chunk."""
        self.total_chunks += 1
        self._total_processing_ms += processing_ms
        if self.total_chunks > 0:
            self.avg_processing_ms = self._total_processing_ms / self.total_chunks


# =============================================================================
# Port Interface
# =============================================================================


class VADPort(ABC):
    """
    Abstract interface for Voice Activity Detection.

    Platform-agnostic VAD that works with any audio source.

    State Machine:
        SILENCE → SPEECH_STARTING → SPEECH → SPEECH_ENDING → SILENCE

        Transitions:
        - SILENCE + speech → SPEECH_STARTING (begin accumulating)
        - SPEECH_STARTING + speech (>= speech_start_ms) → SPEECH (confirmed, fires callback)
        - SPEECH_STARTING + silence → SILENCE (false start)
        - SPEECH + silence → SPEECH_ENDING (begin end accumulation)
        - SPEECH_ENDING + silence (>= speech_end_ms) → SILENCE (confirmed, fires callback)
        - SPEECH_ENDING + speech → SPEECH (speech resumed)

    Thread Safety:
        process_chunk() may be called from audio callback thread.
        Implementations must complete in <10ms with minimal allocations.

    Example:
        vad = EnergyVADAdapter()
        vad.set_callbacks(
            on_speech_start=lambda: print("Started"),
            on_speech_end=lambda: print("Ended"),
        )

        for chunk in audio_stream:
            result = vad.process_chunk(chunk)
            if result.is_speaking:
                send_to_ai(chunk)
    """

    # =========================================================================
    # Abstract Properties
    # =========================================================================

    @property
    @abstractmethod
    def state(self) -> SpeechState:
        """Current speech detection state."""
        ...

    @property
    @abstractmethod
    def is_speaking(self) -> bool:
        """
        Whether speech is currently active.

        Returns True when in SPEECH state (confirmed speech).
        Some implementations may also return True for SPEECH_STARTING
        and SPEECH_ENDING states.
        """
        ...

    @property
    @abstractmethod
    def config(self) -> VADConfig:
        """Current VAD configuration."""
        ...

    # =========================================================================
    # Core Methods
    # =========================================================================

    @abstractmethod
    def process_chunk(self, chunk: bytes) -> VADResult:
        """
        Process audio chunk and detect speech.

        This method runs the VAD state machine:
        1. Calculate energy of the chunk
        2. Update pre-buffer
        3. Transition states based on energy and timing
        4. Fire callbacks on state transitions
        5. Update metrics

        Args:
            chunk: PCM16 audio bytes (size may vary)

        Returns:
            VADResult with current state and metrics

        Thread Safety:
            May run in audio callback thread.
            Must complete in <10ms with minimal allocations.

        Note:
            Callbacks (on_speech_start, on_speech_end) may be fired
            during this call. Ensure callbacks are non-blocking.
        """
        ...

    @abstractmethod
    def set_callbacks(
        self,
        on_speech_start: Optional[Callable[[], None]] = None,
        on_speech_end: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Set callbacks for speech events.

        Args:
            on_speech_start: Called when speech is confirmed
                (SPEECH_STARTING → SPEECH transition).
                No arguments. Use get_pre_buffer() to get audio
                captured before speech was detected.

            on_speech_end: Called when silence is confirmed
                (SPEECH_ENDING → SILENCE transition).
                No arguments.

        Thread Safety:
            Callbacks are called from process_chunk(), which may run
            in audio callback thread. Callbacks must be non-blocking
            (queue work for processing elsewhere).
        """
        ...

    @abstractmethod
    def get_pre_buffer(self) -> bytes:
        """
        Get audio captured before speech was detected.

        The pre-buffer is a rolling window of recent audio.
        Call this in on_speech_start callback to get the audio
        leading up to the speech detection.

        Returns:
            Concatenated audio bytes from pre-buffer.
            Returns empty bytes if pre-buffer is disabled (pre_buffer_ms=0).

        Note:
            Returns a copy. The internal buffer continues rolling.
            Call reset() to clear the buffer explicitly.
        """
        ...

    @abstractmethod
    def get_metrics(self) -> VADMetrics:
        """
        Get VAD performance metrics.

        Returns:
            VADMetrics with processing statistics.

        Note:
            Metrics are cumulative since last reset().
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """
        Reset VAD state.

        Clears:
        - Current state (returns to SILENCE)
        - State duration
        - Pre-buffer
        - Energy history (if applicable)
        - Metrics

        Call between sessions or when starting fresh.
        """
        ...

    @abstractmethod
    def configure(self, config: VADConfig) -> None:
        """
        Update VAD configuration.

        Args:
            config: New configuration to apply

        Raises:
            VADConfigError: If configuration is invalid
            VADConfigError: If sample_rate is changed (not allowed after init)

        Note:
            Some settings (like energy_threshold) take effect immediately.
            Others (like sample_rate) cannot be changed after initialization.
        """
        ...
