"""
Audio Playback Adapters.

Provides implementations of AudioPlaybackPort for various audio output sinks.

Adapters:
    SoundDevicePlaybackAdapter: Primary adapter using buffered/batching pattern (requires sounddevice)
    FileSinkAdapter: Write audio to WAV file
    NullPlaybackAdapter: Discard audio (for testing)

Example:
    from chatforge.adapters.audio_playback import SoundDevicePlaybackAdapter
    from chatforge.ports.audio_playback import AudioPlaybackConfig

    player = SoundDevicePlaybackAdapter(AudioPlaybackConfig(sample_rate=24000))
    player.set_callbacks(
        on_started=lambda: print("Playing..."),
        on_complete=lambda: print("Done!"),
    )

    for chunk in audio_chunks:
        player.play(chunk)

    player.mark_complete()
    player.wait_until_complete_sync()
    player.cleanup()
"""

from chatforge.adapters.audio_playback.sounddevice_adapter import SoundDevicePlaybackAdapter
from chatforge.adapters.audio_playback.file_sink import FileSinkAdapter
from chatforge.adapters.audio_playback.null_adapter import NullPlaybackAdapter

__all__ = [
    "SoundDevicePlaybackAdapter",
    "FileSinkAdapter",
    "NullPlaybackAdapter",
]
