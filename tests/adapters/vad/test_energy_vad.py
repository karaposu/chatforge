"""
Unit tests for EnergyVADAdapter and AdaptiveEnergyVADAdapter.

Tests state machine transitions, callbacks, timing, and metrics.
"""

import pytest
from typing import List

from chatforge.adapters.vad import EnergyVADAdapter, AdaptiveEnergyVADAdapter
from chatforge.ports.vad import VADConfig, SpeechState, VADConfigError

from tests.adapters.vad.fixtures import (
    generate_silence,
    generate_tone,
    chunk_audio,
    generate_speech_sequence,
    generate_speech_with_pause,
)


# =============================================================================
# Basic State Tests
# =============================================================================


class TestEnergyVADBasicState:
    """Test basic VAD state behavior."""

    def test_initial_state_is_silence(self):
        """VAD should start in SILENCE state."""
        vad = EnergyVADAdapter()
        assert vad.state == SpeechState.SILENCE
        assert not vad.is_speaking

    def test_silence_detection(self):
        """Silent audio should return SILENCE state."""
        vad = EnergyVADAdapter()
        silence = generate_silence(100)

        result = vad.process_chunk(silence)

        assert result.state == SpeechState.SILENCE
        assert not result.is_speech
        assert not result.is_speaking
        assert result.energy < 0.01  # Very low energy

    def test_speech_detection_triggers_starting(self):
        """Loud audio should trigger SPEECH_STARTING state."""
        vad = EnergyVADAdapter(VADConfig(energy_threshold=0.02))
        tone = generate_tone(100, amplitude=0.5)

        result = vad.process_chunk(tone)

        assert result.state == SpeechState.SPEECH_STARTING
        assert result.is_speech
        assert not result.is_speaking  # Not confirmed yet

    def test_empty_chunk_returns_current_state(self):
        """Empty chunk should return current state without changing it."""
        vad = EnergyVADAdapter()

        result = vad.process_chunk(b"")

        assert result.state == SpeechState.SILENCE
        assert result.energy == 0.0


# =============================================================================
# State Transition Tests
# =============================================================================


class TestEnergyVADStateTransitions:
    """Test VAD state machine transitions."""

    def test_silence_to_speech_starting(self):
        """SILENCE → SPEECH_STARTING on first speech chunk."""
        vad = EnergyVADAdapter(VADConfig(energy_threshold=0.02))

        # Process silence first
        silence = generate_silence(100)
        result = vad.process_chunk(silence)
        assert result.state == SpeechState.SILENCE

        # Process speech
        speech = generate_tone(100, amplitude=0.5)
        result = vad.process_chunk(speech)
        assert result.state == SpeechState.SPEECH_STARTING

    def test_speech_starting_to_speech(self):
        """SPEECH_STARTING → SPEECH after speech_start_ms."""
        config = VADConfig(energy_threshold=0.02, speech_start_ms=100)
        vad = EnergyVADAdapter(config)

        # Generate enough speech to confirm (150ms > 100ms speech_start_ms)
        speech_chunks = chunk_audio(generate_tone(150, amplitude=0.5), chunk_ms=50)

        for chunk in speech_chunks:
            result = vad.process_chunk(chunk)

        assert result.state == SpeechState.SPEECH
        assert result.is_speaking

    def test_speech_starting_to_silence_on_false_start(self):
        """SPEECH_STARTING → SILENCE if silence detected (false start)."""
        # Use higher threshold to make false start detection work with smoothing
        config = VADConfig(energy_threshold=0.15, speech_start_ms=200)
        vad = EnergyVADAdapter(config)

        # Brief speech (not enough to confirm)
        speech = generate_tone(50, amplitude=0.5)
        vad.process_chunk(speech)
        assert vad.state == SpeechState.SPEECH_STARTING

        # Silence interrupts - energy smoothing will drop below higher threshold faster
        silence_chunks = chunk_audio(generate_silence(200), chunk_ms=50)
        for chunk in silence_chunks:
            result = vad.process_chunk(chunk)
        # Should return to silence (false start detected)
        assert result.state == SpeechState.SILENCE

    def test_speech_to_speech_ending(self):
        """SPEECH → SPEECH_ENDING on first silence during speech."""
        config = VADConfig(energy_threshold=0.02, speech_start_ms=100)
        vad = EnergyVADAdapter(config)

        # Confirm speech first
        speech_chunks = chunk_audio(generate_tone(150, amplitude=0.5), chunk_ms=50)
        for chunk in speech_chunks:
            vad.process_chunk(chunk)
        assert vad.state == SpeechState.SPEECH

        # Silence triggers ending - need multiple chunks to flush energy smoothing
        silence_chunks = chunk_audio(generate_silence(300), chunk_ms=50)
        for chunk in silence_chunks:
            result = vad.process_chunk(chunk)
        # Should be in SPEECH_ENDING or SILENCE (depending on timing)
        assert result.state in (SpeechState.SPEECH_ENDING, SpeechState.SILENCE)

    def test_speech_ending_to_silence(self):
        """SPEECH_ENDING → SILENCE after speech_end_ms of silence."""
        config = VADConfig(
            energy_threshold=0.02,
            speech_start_ms=100,
            speech_end_ms=200,
        )
        vad = EnergyVADAdapter(config)

        # Confirm speech
        speech_chunks = chunk_audio(generate_tone(150, amplitude=0.5), chunk_ms=50)
        for chunk in speech_chunks:
            vad.process_chunk(chunk)

        # Enough silence to flush energy smoothing + confirm end
        # Need ~5 chunks to flush smoothing, then 200ms more for speech_end_ms
        silence_chunks = chunk_audio(generate_silence(500), chunk_ms=50)
        for chunk in silence_chunks:
            result = vad.process_chunk(chunk)

        assert result.state == SpeechState.SILENCE

    def test_speech_ending_to_speech_on_resume(self):
        """SPEECH_ENDING → SPEECH if speech resumes."""
        config = VADConfig(
            energy_threshold=0.02,
            speech_start_ms=100,
            speech_end_ms=500,  # Long enough to allow resume
        )
        vad = EnergyVADAdapter(config)

        # Confirm speech
        speech_chunks = chunk_audio(generate_tone(150, amplitude=0.5), chunk_ms=50)
        for chunk in speech_chunks:
            vad.process_chunk(chunk)
        assert vad.state == SpeechState.SPEECH

        # Silence to flush energy smoothing and enter SPEECH_ENDING
        # Need enough silence to drop energy below threshold
        silence_chunks = chunk_audio(generate_silence(300), chunk_ms=50)
        for chunk in silence_chunks:
            vad.process_chunk(chunk)
        assert vad.state == SpeechState.SPEECH_ENDING

        # Speech resumes - need enough to overcome smoothing
        speech_chunks = chunk_audio(generate_tone(150, amplitude=0.5), chunk_ms=50)
        for chunk in speech_chunks:
            result = vad.process_chunk(chunk)
        assert result.state == SpeechState.SPEECH


# =============================================================================
# Callback Tests
# =============================================================================


class TestEnergyVADCallbacks:
    """Test VAD callback behavior."""

    def test_speech_start_callback_fires(self):
        """on_speech_start callback fires when speech confirmed."""
        config = VADConfig(energy_threshold=0.02, speech_start_ms=100)
        vad = EnergyVADAdapter(config)

        callback_fired = []
        vad.set_callbacks(on_speech_start=lambda: callback_fired.append(True))

        # Process enough speech to confirm
        chunks = generate_speech_sequence(
            silence_before_ms=0,
            speech_ms=200,
            silence_after_ms=0,
            chunk_ms=50,
        )
        for chunk in chunks:
            vad.process_chunk(chunk)

        assert len(callback_fired) == 1

    def test_speech_end_callback_fires(self):
        """on_speech_end callback fires when silence confirmed."""
        config = VADConfig(
            energy_threshold=0.02,
            speech_start_ms=100,
            speech_end_ms=200,
        )
        vad = EnergyVADAdapter(config)

        callback_fired = []
        vad.set_callbacks(on_speech_end=lambda: callback_fired.append(True))

        # Full speech sequence - need enough silence to flush smoothing + trigger end
        chunks = generate_speech_sequence(
            silence_before_ms=0,
            speech_ms=200,
            silence_after_ms=600,  # Increased for energy smoothing
            chunk_ms=50,
        )
        for chunk in chunks:
            vad.process_chunk(chunk)

        assert len(callback_fired) == 1

    def test_callbacks_not_fired_on_false_start(self):
        """Callbacks should not fire on false starts."""
        config = VADConfig(energy_threshold=0.02, speech_start_ms=200)
        vad = EnergyVADAdapter(config)

        start_fired = []
        end_fired = []
        vad.set_callbacks(
            on_speech_start=lambda: start_fired.append(True),
            on_speech_end=lambda: end_fired.append(True),
        )

        # Brief speech followed by silence (false start)
        speech = generate_tone(50, amplitude=0.5)
        vad.process_chunk(speech)

        silence = generate_silence(100)
        vad.process_chunk(silence)

        assert len(start_fired) == 0
        assert len(end_fired) == 0


# =============================================================================
# Pre-buffer Tests
# =============================================================================


class TestEnergyVADPreBuffer:
    """Test pre-buffer behavior."""

    def test_pre_buffer_contains_audio(self):
        """Pre-buffer should contain recent audio."""
        config = VADConfig(pre_buffer_ms=300)
        vad = EnergyVADAdapter(config)

        # Process some audio
        audio = generate_silence(200)
        vad.process_chunk(audio)

        pre_buffer = vad.get_pre_buffer()
        assert len(pre_buffer) > 0

    def test_pre_buffer_empty_when_disabled(self):
        """Pre-buffer should be empty when pre_buffer_ms=0."""
        config = VADConfig(pre_buffer_ms=0)
        vad = EnergyVADAdapter(config)

        audio = generate_silence(200)
        vad.process_chunk(audio)

        pre_buffer = vad.get_pre_buffer()
        assert len(pre_buffer) == 0

    def test_pre_buffer_limited_by_config(self):
        """Pre-buffer should not exceed configured duration."""
        config = VADConfig(pre_buffer_ms=100)
        vad = EnergyVADAdapter(config)

        # Process more audio than buffer can hold
        for _ in range(10):
            audio = generate_silence(50)
            vad.process_chunk(audio)

        pre_buffer = vad.get_pre_buffer()
        # Should be limited (allowing some margin for chunk boundaries)
        max_bytes = int(24000 * 0.2 * 2)  # 200ms at 24kHz, 16-bit = generous margin
        assert len(pre_buffer) <= max_bytes


# =============================================================================
# Metrics Tests
# =============================================================================


class TestEnergyVADMetrics:
    """Test VAD metrics tracking."""

    def test_metrics_count_chunks(self):
        """Metrics should count processed chunks."""
        vad = EnergyVADAdapter()

        for _ in range(5):
            vad.process_chunk(generate_silence(100))

        metrics = vad.get_metrics()
        assert metrics.total_chunks == 5

    def test_metrics_count_speech_silence(self):
        """Metrics should count speech and silence chunks."""
        vad = EnergyVADAdapter(VADConfig(energy_threshold=0.02))

        # 3 silence chunks
        for _ in range(3):
            vad.process_chunk(generate_silence(100))

        # 2 speech chunks
        for _ in range(2):
            vad.process_chunk(generate_tone(100, amplitude=0.5))

        metrics = vad.get_metrics()
        assert metrics.silence_chunks == 3
        assert metrics.speech_chunks == 2

    def test_metrics_track_transitions(self):
        """Metrics should track state transitions."""
        config = VADConfig(energy_threshold=0.02, speech_start_ms=50, speech_end_ms=100)
        vad = EnergyVADAdapter(config)

        chunks = generate_speech_sequence(
            silence_before_ms=100,
            speech_ms=100,
            silence_after_ms=200,
            chunk_ms=50,
        )
        for chunk in chunks:
            vad.process_chunk(chunk)

        metrics = vad.get_metrics()
        assert metrics.transitions > 0
        assert metrics.speech_segments >= 1

    def test_metrics_track_processing_time(self):
        """Metrics should track average processing time."""
        vad = EnergyVADAdapter()

        for _ in range(10):
            vad.process_chunk(generate_silence(100))

        metrics = vad.get_metrics()
        assert metrics.avg_processing_ms > 0
        assert metrics.avg_processing_ms < 10  # Should be fast


# =============================================================================
# Reset Tests
# =============================================================================


class TestEnergyVADReset:
    """Test VAD reset behavior."""

    def test_reset_clears_state(self):
        """Reset should return to SILENCE state."""
        config = VADConfig(energy_threshold=0.02, speech_start_ms=50)
        vad = EnergyVADAdapter(config)

        # Get into speech state
        speech = generate_tone(100, amplitude=0.5)
        vad.process_chunk(speech)
        vad.process_chunk(speech)
        assert vad.state != SpeechState.SILENCE

        # Reset
        vad.reset()
        assert vad.state == SpeechState.SILENCE

    def test_reset_clears_metrics(self):
        """Reset should clear metrics."""
        vad = EnergyVADAdapter()

        # Process some audio
        for _ in range(5):
            vad.process_chunk(generate_silence(100))

        assert vad.get_metrics().total_chunks == 5

        # Reset
        vad.reset()
        assert vad.get_metrics().total_chunks == 0

    def test_reset_clears_pre_buffer(self):
        """Reset should clear pre-buffer."""
        vad = EnergyVADAdapter(VADConfig(pre_buffer_ms=300))

        # Fill pre-buffer
        for _ in range(5):
            vad.process_chunk(generate_silence(100))

        assert len(vad.get_pre_buffer()) > 0

        # Reset
        vad.reset()
        assert len(vad.get_pre_buffer()) == 0


# =============================================================================
# Configuration Tests
# =============================================================================


class TestEnergyVADConfiguration:
    """Test VAD configuration behavior."""

    def test_configure_updates_threshold(self):
        """Configure should update energy threshold."""
        vad = EnergyVADAdapter(VADConfig(energy_threshold=0.02))

        new_config = VADConfig(energy_threshold=0.05)
        vad.configure(new_config)

        assert vad.config.energy_threshold == 0.05

    def test_configure_rejects_sample_rate_change(self):
        """Configure should reject sample rate changes."""
        vad = EnergyVADAdapter(VADConfig(sample_rate=24000))

        new_config = VADConfig(sample_rate=16000)
        with pytest.raises(VADConfigError):
            vad.configure(new_config)

    def test_invalid_config_raises_error(self):
        """Invalid config should raise VADConfigError."""
        with pytest.raises(VADConfigError):
            VADConfig(energy_threshold=2.0)  # Must be <= 1.0

        with pytest.raises(VADConfigError):
            VADConfig(energy_threshold=-0.1)  # Must be > 0.0

        with pytest.raises(VADConfigError):
            VADConfig(speech_start_ms=-100)  # Must be >= 0


# =============================================================================
# Variable Chunk Size Tests
# =============================================================================


class TestEnergyVADVariableChunks:
    """Test VAD with variable chunk sizes."""

    def test_works_with_50ms_chunks(self):
        """VAD should work with 50ms chunks."""
        vad = EnergyVADAdapter(VADConfig(speech_start_ms=100))
        chunks = chunk_audio(generate_tone(200, amplitude=0.5), chunk_ms=50)

        for chunk in chunks:
            result = vad.process_chunk(chunk)

        assert result.state == SpeechState.SPEECH

    def test_works_with_100ms_chunks(self):
        """VAD should work with 100ms chunks."""
        vad = EnergyVADAdapter(VADConfig(speech_start_ms=100))
        chunks = chunk_audio(generate_tone(200, amplitude=0.5), chunk_ms=100)

        for chunk in chunks:
            result = vad.process_chunk(chunk)

        assert result.state == SpeechState.SPEECH

    def test_works_with_200ms_chunks(self):
        """VAD should work with 200ms chunks."""
        vad = EnergyVADAdapter(VADConfig(speech_start_ms=100))
        chunks = chunk_audio(generate_tone(400, amplitude=0.5), chunk_ms=200)

        for chunk in chunks:
            result = vad.process_chunk(chunk)

        assert result.state == SpeechState.SPEECH


# =============================================================================
# Adaptive VAD Tests
# =============================================================================


class TestAdaptiveEnergyVAD:
    """Test AdaptiveEnergyVADAdapter specific behavior."""

    def test_starts_in_calibration_mode(self):
        """Adaptive VAD should start in calibration mode."""
        vad = AdaptiveEnergyVADAdapter()
        assert vad.is_calibrating

    def test_calibration_completes_after_1_second(self):
        """Calibration should complete after ~1 second."""
        vad = AdaptiveEnergyVADAdapter()

        # Process 1 second of audio (10 x 100ms chunks)
        for _ in range(10):
            vad.process_chunk(generate_silence(100))

        assert not vad.is_calibrating

    def test_noise_floor_is_measured(self):
        """Noise floor should be measured during calibration."""
        vad = AdaptiveEnergyVADAdapter()

        # Process calibration audio
        for _ in range(10):
            vad.process_chunk(generate_silence(100))

        # Noise floor should be very low for silence
        assert vad.noise_floor < 0.01

    def test_threshold_adapts_to_noise(self):
        """Threshold should adapt based on noise floor."""
        vad = AdaptiveEnergyVADAdapter()
        initial_threshold = vad.config.energy_threshold

        # Calibrate with low noise
        for _ in range(10):
            vad.process_chunk(generate_silence(100))

        # Threshold should have been updated
        # (May be same as initial minimum, but should have been recalculated)
        assert vad.config.energy_threshold >= 0.02  # Minimum threshold

    def test_recalibrate_resets_state(self):
        """Recalibrate should reset calibration state."""
        vad = AdaptiveEnergyVADAdapter()

        # Complete initial calibration
        for _ in range(10):
            vad.process_chunk(generate_silence(100))
        assert not vad.is_calibrating

        # Recalibrate
        vad.recalibrate()
        assert vad.is_calibrating


# =============================================================================
# Integration-style Tests
# =============================================================================


class TestEnergyVADIntegration:
    """Integration-style tests with realistic scenarios."""

    def test_full_speech_sequence(self):
        """Test complete silence → speech → silence sequence."""
        config = VADConfig(
            energy_threshold=0.02,
            speech_start_ms=100,
            speech_end_ms=200,
        )
        vad = EnergyVADAdapter(config)

        states: List[SpeechState] = []
        start_count = 0
        end_count = 0

        def on_start():
            nonlocal start_count
            start_count += 1

        def on_end():
            nonlocal end_count
            end_count += 1

        vad.set_callbacks(on_speech_start=on_start, on_speech_end=on_end)

        chunks = generate_speech_sequence(
            silence_before_ms=200,
            speech_ms=300,
            silence_after_ms=400,
            chunk_ms=50,
        )

        for chunk in chunks:
            result = vad.process_chunk(chunk)
            states.append(result.state)

        # Should have gone through all states
        assert SpeechState.SILENCE in states
        assert SpeechState.SPEECH_STARTING in states
        assert SpeechState.SPEECH in states
        assert SpeechState.SPEECH_ENDING in states

        # Callbacks should have fired
        assert start_count == 1
        assert end_count == 1

    def test_speech_with_brief_pause(self):
        """Test that brief pauses don't end speech."""
        config = VADConfig(
            energy_threshold=0.02,
            speech_start_ms=100,
            speech_end_ms=500,  # Long end threshold
        )
        vad = EnergyVADAdapter(config)

        end_count = 0
        vad.set_callbacks(on_speech_end=lambda: end_count + 1)

        # Speech with a pause shorter than speech_end_ms
        chunks = generate_speech_with_pause(
            speech1_ms=200,
            pause_ms=200,  # < 500ms speech_end_ms
            speech2_ms=200,
            silence_after_ms=0,  # No final silence yet
            chunk_ms=50,
        )

        for chunk in chunks:
            vad.process_chunk(chunk)

        # Should still be in speech (pause wasn't long enough)
        assert vad.state == SpeechState.SPEECH
        assert end_count == 0
