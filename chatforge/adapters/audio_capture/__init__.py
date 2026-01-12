"""
Audio Capture Adapters.

Implementations of AudioCapturePort for various audio sources.

Adapters:
    SoundDeviceCaptureAdapter: Primary adapter for microphone input
    FileCaptureAdapter: Read from WAV file (testing/debugging)
    NullCaptureAdapter: Generate silence or test signals (testing)

Example:
    from chatforge.adapters.audio_capture import SoundDeviceCaptureAdapter
    from chatforge.ports.audio_capture import AudioCaptureConfig

    capture = SoundDeviceCaptureAdapter()
    audio_queue = await capture.start()

    while capture.is_capturing:
        chunk = await audio_queue.get()
        process(chunk)
        if should_stop:
            capture.stop()

    capture.cleanup()
"""

from chatforge.adapters.audio_capture.sounddevice_adapter import (
    SoundDeviceCaptureAdapter,
)
from chatforge.adapters.audio_capture.file_adapter import FileCaptureAdapter
from chatforge.adapters.audio_capture.null_adapter import NullCaptureAdapter

__all__ = [
    "SoundDeviceCaptureAdapter",
    "FileCaptureAdapter",
    "NullCaptureAdapter",
]
