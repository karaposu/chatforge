"""
Test fixtures for audio capture adapters.

Provides audio generation helpers and WAV file creation for testing.
"""

import math
import struct
import tempfile
import wave
from pathlib import Path
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


def generate_audio_sequence(
    total_duration_ms: int = 1000,
    chunk_ms: int = 100,
    sample_rate: int = 24000,
) -> List[bytes]:
    """
    Generate a sequence of audio chunks.

    Args:
        total_duration_ms: Total duration in milliseconds
        chunk_ms: Chunk duration for splitting
        sample_rate: Sample rate in Hz

    Returns:
        List of audio chunks
    """
    audio = generate_tone(total_duration_ms, sample_rate=sample_rate)
    return chunk_audio(audio, chunk_ms, sample_rate)


def create_test_wav(
    path: Path,
    duration_ms: int = 1000,
    frequency: int = 440,
    sample_rate: int = 24000,
    channels: int = 1,
    bit_depth: int = 16,
) -> Path:
    """
    Create a test WAV file.

    Args:
        path: Path to write the WAV file
        duration_ms: Duration in milliseconds
        frequency: Frequency of tone in Hz
        sample_rate: Sample rate in Hz
        channels: Number of channels
        bit_depth: Bits per sample

    Returns:
        Path to created WAV file
    """
    audio = generate_tone(
        duration_ms,
        frequency=frequency,
        sample_rate=sample_rate,
        channels=channels,
    )

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(bit_depth // 8)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio)

    return path


def create_temp_wav(
    duration_ms: int = 1000,
    frequency: int = 440,
    sample_rate: int = 24000,
    channels: int = 1,
) -> Path:
    """
    Create a temporary test WAV file.

    Args:
        duration_ms: Duration in milliseconds
        frequency: Frequency of tone in Hz
        sample_rate: Sample rate in Hz
        channels: Number of channels

    Returns:
        Path to created temp WAV file
    """
    temp_dir = Path(tempfile.mkdtemp())
    wav_path = temp_dir / "test_audio.wav"
    return create_test_wav(wav_path, duration_ms, frequency, sample_rate, channels)
