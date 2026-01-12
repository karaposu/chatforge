"""
Energy-based Voice Activity Detection adapters.

Provides simple, fast VAD using RMS energy thresholds.
No external dependencies beyond numpy.

Adapters:
    EnergyVADAdapter: Basic energy threshold VAD
    AdaptiveEnergyVADAdapter: Energy VAD with adaptive threshold
"""

import time
from collections import deque
from typing import Callable, Optional

import numpy as np

from chatforge.ports.vad import (
    SpeechState,
    VADConfig,
    VADConfigError,
    VADMetrics,
    VADPort,
    VADResult,
)


__all__ = ["EnergyVADAdapter", "AdaptiveEnergyVADAdapter"]


class EnergyVADAdapter(VADPort):
    """
    Energy-based Voice Activity Detection using RMS amplitude.

    Simple and fast, no external dependencies beyond numpy.
    Good for: Low-latency, resource-constrained environments.

    Algorithm:
        1. Calculate RMS energy of chunk
        2. Smooth energy using ring buffer
        3. Compare to threshold
        4. Track consecutive speech/silence duration
        5. Transition states based on timing thresholds
        6. Fire callbacks on confirmed transitions

    Thread Safety:
        process_chunk() is designed for audio callback thread:
        - Uses pre-allocated numpy buffers
        - Minimal allocations in hot path
        - Callbacks must be non-blocking

    Example:
        vad = EnergyVADAdapter(VADConfig(energy_threshold=0.02))
        vad.set_callbacks(
            on_speech_start=lambda: print("Speaking"),
            on_speech_end=lambda: print("Done"),
        )

        for chunk in audio_stream:
            result = vad.process_chunk(chunk)
    """

    # Energy history size for smoothing (prevents false triggers)
    ENERGY_HISTORY_SIZE = 5

    def __init__(self, config: Optional[VADConfig] = None) -> None:
        """
        Initialize energy-based VAD.

        Args:
            config: VAD configuration. Uses defaults if not provided.
        """
        self._config = config or VADConfig()

        # Pre-computed values for performance (must be first for other initializations)
        self._bytes_per_ms = self._config.bytes_per_ms

        # State machine
        self._state = SpeechState.SILENCE
        self._state_duration_ms: float = 0.0

        # Pre-buffer for audio before speech detection (tracks bytes, not chunks)
        if self._config.pre_buffer_ms > 0:
            self._pre_buffer_max_bytes = int(
                self._config.pre_buffer_ms * self._bytes_per_ms
            )
            self._pre_buffer: deque[bytes] = deque()
            self._pre_buffer_bytes: int = 0
        else:
            # Disabled - use None to indicate no buffering
            self._pre_buffer_max_bytes = 0
            self._pre_buffer: Optional[deque[bytes]] = None
            self._pre_buffer_bytes: int = 0

        # Energy smoothing ring buffer
        self._energy_history: deque[float] = deque(maxlen=self.ENERGY_HISTORY_SIZE)

        # Callbacks
        self._on_speech_start: Optional[Callable[[], None]] = None
        self._on_speech_end: Optional[Callable[[], None]] = None

        # Metrics
        self._metrics = VADMetrics()

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def state(self) -> SpeechState:
        """Current speech detection state."""
        return self._state

    @property
    def is_speaking(self) -> bool:
        """
        Whether speech is currently active.

        Returns True for SPEECH state only (confirmed speech).
        """
        return self._state == SpeechState.SPEECH

    @property
    def config(self) -> VADConfig:
        """Current VAD configuration."""
        return self._config

    # =========================================================================
    # Core Methods
    # =========================================================================

    def process_chunk(self, chunk: bytes) -> VADResult:
        """
        Process audio chunk and detect speech.

        Args:
            chunk: PCM16 audio bytes

        Returns:
            VADResult with current state and metrics
        """
        start_time = time.perf_counter()

        # Handle empty chunk
        if len(chunk) == 0:
            return VADResult(
                state=self._state,
                is_speech=False,
                is_speaking=self.is_speaking,
                energy=0.0,
                state_duration_ms=self._state_duration_ms,
            )

        # Calculate chunk duration from actual bytes
        chunk_duration_ms = len(chunk) / self._bytes_per_ms

        # Calculate and smooth energy
        raw_energy = self._calculate_rms(chunk)
        smoothed_energy = self._get_smoothed_energy(raw_energy)

        # Update pre-buffer (rolling window) if enabled
        if self._pre_buffer is not None:
            self._pre_buffer.append(chunk)
            self._pre_buffer_bytes += len(chunk)
            # Trim if exceeds max bytes
            while self._pre_buffer_bytes > self._pre_buffer_max_bytes and len(self._pre_buffer) > 1:
                removed = self._pre_buffer.popleft()
                self._pre_buffer_bytes -= len(removed)

        # Determine if this chunk contains speech
        is_speech = smoothed_energy > self._config.energy_threshold

        # Track old state for transition detection
        old_state = self._state

        # Run state machine
        self._update_state_machine(is_speech, chunk_duration_ms)

        # Update metrics
        self._update_metrics(chunk_duration_ms, is_speech, old_state)

        # Record processing time
        processing_ms = (time.perf_counter() - start_time) * 1000
        self._metrics.record_chunk(processing_ms)

        return VADResult(
            state=self._state,
            is_speech=is_speech,
            is_speaking=self.is_speaking,
            energy=smoothed_energy,
            state_duration_ms=self._state_duration_ms,
        )

    def set_callbacks(
        self,
        on_speech_start: Optional[Callable[[], None]] = None,
        on_speech_end: Optional[Callable[[], None]] = None,
    ) -> None:
        """Set callbacks for speech events."""
        self._on_speech_start = on_speech_start
        self._on_speech_end = on_speech_end

    def get_pre_buffer(self) -> bytes:
        """Get audio captured before speech was detected."""
        if self._pre_buffer is None or len(self._pre_buffer) == 0:
            return b""
        return b"".join(self._pre_buffer)

    def get_metrics(self) -> VADMetrics:
        """Get VAD performance metrics."""
        return self._metrics

    def reset(self) -> None:
        """Reset VAD state."""
        self._state = SpeechState.SILENCE
        self._state_duration_ms = 0.0
        if self._pre_buffer is not None:
            self._pre_buffer.clear()
            self._pre_buffer_bytes = 0
        self._energy_history.clear()
        self._metrics = VADMetrics()

    def configure(self, config: VADConfig) -> None:
        """Update VAD configuration."""
        # Validate that sample_rate hasn't changed
        if config.sample_rate != self._config.sample_rate:
            raise VADConfigError(
                f"Cannot change sample_rate after initialization "
                f"(was {self._config.sample_rate}, got {config.sample_rate})"
            )

        self._config = config

        # Recalculate derived values
        self._bytes_per_ms = config.bytes_per_ms

        # Update pre-buffer settings if needed
        if config.pre_buffer_ms > 0:
            self._pre_buffer_max_bytes = int(
                config.pre_buffer_ms * self._bytes_per_ms
            )
            if self._pre_buffer is None:
                self._pre_buffer = deque()
                self._pre_buffer_bytes = 0
            # Trim existing buffer if it exceeds new max
            while self._pre_buffer_bytes > self._pre_buffer_max_bytes and len(self._pre_buffer) > 1:
                removed = self._pre_buffer.popleft()
                self._pre_buffer_bytes -= len(removed)
        else:
            # Disable pre-buffer
            self._pre_buffer_max_bytes = 0
            self._pre_buffer = None
            self._pre_buffer_bytes = 0

    # =========================================================================
    # Internal Methods
    # =========================================================================

    def _calculate_rms(self, chunk: bytes) -> float:
        """
        Calculate RMS energy of PCM16 audio.

        Args:
            chunk: PCM16 audio bytes

        Returns:
            Normalized RMS energy (0.0-1.0)
        """
        # Convert to numpy array (creates view, minimal allocation)
        samples = np.frombuffer(chunk, dtype=np.int16).astype(np.float32)

        if len(samples) == 0:
            return 0.0

        # Normalize to [-1, 1]
        samples = samples / 32768.0

        # Calculate RMS
        rms = np.sqrt(np.mean(samples**2))

        return float(rms)

    def _get_smoothed_energy(self, energy: float) -> float:
        """
        Get smoothed energy using ring buffer.

        Smoothing helps prevent false triggers from transient sounds.

        Args:
            energy: Current raw energy value

        Returns:
            Smoothed energy (moving average)
        """
        self._energy_history.append(energy)

        if len(self._energy_history) == 0:
            return energy

        return sum(self._energy_history) / len(self._energy_history)

    def _update_state_machine(self, is_speech: bool, chunk_duration_ms: float) -> None:
        """
        Update VAD state machine based on speech detection.

        State transitions:
        - SILENCE + speech → SPEECH_STARTING
        - SPEECH_STARTING + speech (>= speech_start_ms) → SPEECH (callback)
        - SPEECH_STARTING + silence → SILENCE (false start)
        - SPEECH + silence → SPEECH_ENDING
        - SPEECH_ENDING + silence (>= speech_end_ms) → SILENCE (callback)
        - SPEECH_ENDING + speech → SPEECH (resumed)

        Args:
            is_speech: Whether current chunk contains speech
            chunk_duration_ms: Duration of current chunk in milliseconds
        """
        if self._state == SpeechState.SILENCE:
            if is_speech:
                # Speech detected - start accumulating
                self._state = SpeechState.SPEECH_STARTING
                self._state_duration_ms = chunk_duration_ms
                self._metrics.transitions += 1

        elif self._state == SpeechState.SPEECH_STARTING:
            if is_speech:
                # Continue accumulating speech
                self._state_duration_ms += chunk_duration_ms

                # Check if we've accumulated enough
                if self._state_duration_ms >= self._config.speech_start_ms:
                    self._state = SpeechState.SPEECH
                    self._state_duration_ms = 0.0
                    self._metrics.transitions += 1
                    self._metrics.speech_segments += 1

                    # Fire callback
                    if self._on_speech_start:
                        self._on_speech_start()
            else:
                # False start - return to silence
                self._state = SpeechState.SILENCE
                self._state_duration_ms = 0.0
                self._metrics.transitions += 1

        elif self._state == SpeechState.SPEECH:
            if is_speech:
                # Continue speaking
                self._state_duration_ms += chunk_duration_ms
            else:
                # Silence detected - start ending
                self._state = SpeechState.SPEECH_ENDING
                self._state_duration_ms = chunk_duration_ms
                self._metrics.transitions += 1

        elif self._state == SpeechState.SPEECH_ENDING:
            if is_speech:
                # Speech resumed - back to speaking
                self._state = SpeechState.SPEECH
                self._state_duration_ms = chunk_duration_ms
                self._metrics.transitions += 1
            else:
                # Continue accumulating silence
                self._state_duration_ms += chunk_duration_ms

                # Check if we've accumulated enough silence
                if self._state_duration_ms >= self._config.speech_end_ms:
                    self._state = SpeechState.SILENCE
                    self._state_duration_ms = 0.0
                    self._metrics.transitions += 1

                    # Fire callback
                    if self._on_speech_end:
                        self._on_speech_end()

    def _update_metrics(
        self, chunk_duration_ms: float, is_speech: bool, old_state: SpeechState
    ) -> None:
        """Update metrics based on current chunk."""
        # Count speech/silence chunks
        if is_speech:
            self._metrics.speech_chunks += 1
        else:
            self._metrics.silence_chunks += 1

        # Count state-specific chunks
        if self._state == SpeechState.SPEECH_STARTING:
            self._metrics.speech_starting_chunks += 1
        elif self._state == SpeechState.SPEECH_ENDING:
            self._metrics.speech_ending_chunks += 1

        # Track time in speech/silence
        if self._state in (
            SpeechState.SPEECH,
            SpeechState.SPEECH_STARTING,
            SpeechState.SPEECH_ENDING,
        ):
            self._metrics.total_speech_ms += chunk_duration_ms
        else:
            self._metrics.total_silence_ms += chunk_duration_ms


class AdaptiveEnergyVADAdapter(EnergyVADAdapter):
    """
    Adaptive energy-based VAD that adjusts thresholds based on ambient noise.

    Extends EnergyVADAdapter with:
    - Initial calibration period to measure noise floor
    - Continuous threshold adaptation during silence
    - Threshold set to 3x noise floor (configurable)

    Good for: Noisy environments, variable ambient conditions.

    Example:
        vad = AdaptiveEnergyVADAdapter()

        # First second calibrates noise floor
        for chunk in audio_stream:
            result = vad.process_chunk(chunk)
            if vad.is_calibrating:
                print(f"Calibrating... noise floor: {vad.noise_floor:.4f}")
            else:
                if result.is_speaking:
                    send_to_ai(chunk)
    """

    # Calibration duration
    CALIBRATION_MS = 1000  # 1 second

    # Threshold multiplier (threshold = noise_floor * multiplier)
    NOISE_MULTIPLIER = 3.0

    # Minimum threshold (even in quiet environments)
    MIN_THRESHOLD = 0.02

    # Adaptation rate (how fast threshold adjusts during silence)
    ADAPTATION_RATE = 0.001

    def __init__(self, config: Optional[VADConfig] = None) -> None:
        """
        Initialize adaptive energy VAD.

        Args:
            config: VAD configuration. Uses defaults if not provided.
        """
        super().__init__(config)

        # Adaptive state
        self._noise_floor: float = 0.0
        self._noise_samples: int = 0
        self._calibration_ms: float = 0.0
        self._is_calibrating: bool = True

    @property
    def is_calibrating(self) -> bool:
        """Whether VAD is in calibration mode."""
        return self._is_calibrating

    @property
    def noise_floor(self) -> float:
        """Current estimated noise floor."""
        return self._noise_floor

    def process_chunk(self, chunk: bytes) -> VADResult:
        """
        Process audio chunk with adaptive threshold.

        During calibration (first ~1 second):
        - Collects noise samples
        - Updates noise floor estimate
        - After calibration, sets threshold to 3x noise floor

        During normal operation:
        - Slowly adapts threshold during silence

        Args:
            chunk: PCM16 audio bytes

        Returns:
            VADResult with current state and metrics
        """
        if len(chunk) == 0:
            return super().process_chunk(chunk)

        chunk_duration_ms = len(chunk) / self._bytes_per_ms

        # During calibration, collect noise samples
        if self._is_calibrating:
            self._update_noise_floor(chunk)
            self._calibration_ms += chunk_duration_ms

            # Check if calibration is complete
            if self._calibration_ms >= self.CALIBRATION_MS:
                self._finish_calibration()

        # Normal VAD processing
        result = super().process_chunk(chunk)

        # Adapt threshold during silence (after calibration)
        if not self._is_calibrating and result.state == SpeechState.SILENCE:
            self._adapt_threshold(result.energy)

        return result

    def reset(self) -> None:
        """Reset VAD state including adaptive parameters."""
        super().reset()
        self._noise_floor = 0.0
        self._noise_samples = 0
        self._calibration_ms = 0.0
        self._is_calibrating = True

    def recalibrate(self) -> None:
        """Force recalibration of noise floor."""
        self._noise_floor = 0.0
        self._noise_samples = 0
        self._calibration_ms = 0.0
        self._is_calibrating = True

    def _update_noise_floor(self, chunk: bytes) -> None:
        """Update noise floor estimate during calibration."""
        energy = self._calculate_rms(chunk)

        # Running average
        self._noise_samples += 1
        self._noise_floor += (energy - self._noise_floor) / self._noise_samples

    def _finish_calibration(self) -> None:
        """Complete calibration and set threshold."""
        self._is_calibrating = False

        # Set threshold to 3x noise floor, with minimum
        new_threshold = max(self.MIN_THRESHOLD, self._noise_floor * self.NOISE_MULTIPLIER)

        # Update config (create new instance to avoid mutating shared config)
        self._config = VADConfig(
            energy_threshold=new_threshold,
            speech_start_ms=self._config.speech_start_ms,
            speech_end_ms=self._config.speech_end_ms,
            pre_buffer_ms=self._config.pre_buffer_ms,
            sample_rate=self._config.sample_rate,
            channels=self._config.channels,
            bit_depth=self._config.bit_depth,
        )

    def _adapt_threshold(self, current_energy: float) -> None:
        """Slowly adapt threshold during silence."""
        # Track noise floor with exponential moving average
        if current_energy < self._noise_floor:
            # Noise decreased
            self._noise_floor -= self.ADAPTATION_RATE * (
                self._noise_floor - current_energy
            )
        else:
            # Noise increased (slower adaptation)
            self._noise_floor += self.ADAPTATION_RATE * (
                current_energy - self._noise_floor
            )

        # Update threshold based on new noise floor
        new_threshold = max(self.MIN_THRESHOLD, self._noise_floor * self.NOISE_MULTIPLIER)

        # Smooth threshold update (90% old, 10% new)
        smoothed_threshold = 0.9 * self._config.energy_threshold + 0.1 * new_threshold

        # Update config
        self._config = VADConfig(
            energy_threshold=smoothed_threshold,
            speech_start_ms=self._config.speech_start_ms,
            speech_end_ms=self._config.speech_end_ms,
            pre_buffer_ms=self._config.pre_buffer_ms,
            sample_rate=self._config.sample_rate,
            channels=self._config.channels,
            bit_depth=self._config.bit_depth,
        )
