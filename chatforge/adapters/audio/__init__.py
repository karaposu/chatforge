"""
Audio Stream Adapters - Implementations of AudioStreamPort.

Provides adapters for real-time audio capture and playback:
- VoxStreamAdapter: Desktop audio via sounddevice
- MockAudioStreamAdapter: Testing without hardware
"""

from chatforge.adapters.audio.voxstream import VoxStreamAdapter
from chatforge.adapters.audio.mock import MockAudioStreamAdapter

__all__ = [
    "VoxStreamAdapter",
    "MockAudioStreamAdapter",
]
