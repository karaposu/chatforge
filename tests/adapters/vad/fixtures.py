"""
Test fixtures for VAD adapters.

Provides audio generation helpers for testing VAD behavior.
"""

import struct
import math
from typing import List


def generate_silence(
    duration_ms: int,
    sample_rate: int = 24000,
    channels: int = 1,
    bit_depth: int = 16,
) -> bytes:
    """
    Generate silent audio.

    Args:
        duration_ms: Duration in milliseconds
        sample_rate: Sample rate in Hz
        channels: Number of channels
        bit_depth: Bits per sample (16 only supported)

    Returns:
        PCM16 audio bytes of silence
    """
    num_samples = int(sample_rate * duration_ms / 1000) * channels
    return b"\x00\x00" * num_samples


def generate_tone(
    duration_ms: int,
    frequency: int = 440,
    amplitude: float = 0.5,
    sample_rate: int = 24000,
    channels: int = 1,
) -> bytes:
    """
    Generate a sine wave tone.

    Args:
        duration_ms: Duration in milliseconds
        frequency: Frequency in Hz
        amplitude: Amplitude 0.0-1.0
        sample_rate: Sample rate in Hz
        channels: Number of channels

    Returns:
        PCM16 audio bytes
    """
    num_samples = int(sample_rate * duration_ms / 1000)
    samples = []

    for i in range(num_samples):
        t = i / sample_rate
        value = amplitude * math.sin(2 * math.pi * frequency * t)
        # Convert to int16
        int_value = int(value * 32767)
        int_value = max(-32768, min(32767, int_value))

        for _ in range(channels):
            samples.append(int_value)

    return struct.pack(f"<{len(samples)}h", *samples)


def generate_noise(
    duration_ms: int,
    amplitude: float = 0.3,
    sample_rate: int = 24000,
    channels: int = 1,
) -> bytes:
    """
    Generate white noise.

    Args:
        duration_ms: Duration in milliseconds
        amplitude: Amplitude 0.0-1.0
        sample_rate: Sample rate in Hz
        channels: Number of channels

    Returns:
        PCM16 audio bytes
    """
    import random

    num_samples = int(sample_rate * duration_ms / 1000)
    samples = []

    for _ in range(num_samples):
        value = amplitude * (random.random() * 2 - 1)
        int_value = int(value * 32767)
        int_value = max(-32768, min(32767, int_value))

        for _ in range(channels):
            samples.append(int_value)

    return struct.pack(f"<{len(samples)}h", *samples)


def chunk_audio(
    audio: bytes,
    chunk_ms: int = 100,
    sample_rate: int = 24000,
    channels: int = 1,
    bit_depth: int = 16,
) -> List[bytes]:
    """
    Split audio into chunks.

    Args:
        audio: PCM16 audio bytes
        chunk_ms: Chunk duration in milliseconds
        sample_rate: Sample rate in Hz
        channels: Number of channels
        bit_depth: Bits per sample

    Returns:
        List of audio chunks
    """
    bytes_per_sample = bit_depth // 8
    bytes_per_chunk = int(sample_rate * chunk_ms / 1000 * channels * bytes_per_sample)

    chunks = []
    for i in range(0, len(audio), bytes_per_chunk):
        chunk = audio[i : i + bytes_per_chunk]
        if len(chunk) == bytes_per_chunk:
            chunks.append(chunk)

    return chunks


def generate_speech_sequence(
    silence_before_ms: int = 200,
    speech_ms: int = 500,
    silence_after_ms: int = 600,
    chunk_ms: int = 100,
    speech_amplitude: float = 0.5,
    sample_rate: int = 24000,
) -> List[bytes]:
    """
    Generate a sequence of chunks simulating speech.

    Creates: silence → speech → silence

    Args:
        silence_before_ms: Silence before speech
        speech_ms: Duration of speech
        silence_after_ms: Silence after speech
        chunk_ms: Chunk duration for splitting
        speech_amplitude: Amplitude of speech signal
        sample_rate: Sample rate in Hz

    Returns:
        List of audio chunks
    """
    # Generate continuous audio
    silence_before = generate_silence(silence_before_ms, sample_rate)
    speech = generate_tone(speech_ms, frequency=440, amplitude=speech_amplitude, sample_rate=sample_rate)
    silence_after = generate_silence(silence_after_ms, sample_rate)

    # Combine
    full_audio = silence_before + speech + silence_after

    # Chunk it
    return chunk_audio(full_audio, chunk_ms, sample_rate)


def generate_speech_with_pause(
    speech1_ms: int = 300,
    pause_ms: int = 200,
    speech2_ms: int = 300,
    silence_after_ms: int = 600,
    chunk_ms: int = 100,
    sample_rate: int = 24000,
) -> List[bytes]:
    """
    Generate speech with a brief pause in the middle.

    Creates: speech → pause → speech → silence

    This tests that SPEECH_ENDING doesn't falsely end on brief pauses.

    Args:
        speech1_ms: First speech segment duration
        pause_ms: Pause duration (should be < speech_end_ms to not trigger end)
        speech2_ms: Second speech segment duration
        silence_after_ms: Final silence
        chunk_ms: Chunk duration for splitting
        sample_rate: Sample rate in Hz

    Returns:
        List of audio chunks
    """
    speech1 = generate_tone(speech1_ms, frequency=440, amplitude=0.5, sample_rate=sample_rate)
    pause = generate_silence(pause_ms, sample_rate)
    speech2 = generate_tone(speech2_ms, frequency=440, amplitude=0.5, sample_rate=sample_rate)
    silence = generate_silence(silence_after_ms, sample_rate)

    full_audio = speech1 + pause + speech2 + silence

    return chunk_audio(full_audio, chunk_ms, sample_rate)
