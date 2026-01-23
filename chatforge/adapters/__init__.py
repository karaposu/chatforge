"""
Chatforge Adapters - Implementations of port interfaces.

Provides storage adapters, TTS adapters, and null/testing adapters.
"""

from chatforge.adapters.null import (
    NullKnowledgeAdapter,
    NullMessagingAdapter,
    NullTicketingAdapter,
    NullAudioStreamAdapter,
)
from chatforge.adapters.storage import (
    InMemoryStorageAdapter,
    SQLiteStorageAdapter,
)
from chatforge.adapters.tts import (
    ElevenLabsTTSAdapter,
    ElevenLabsVoiceConfig,
    OpenAITTSAdapter,
    OpenAIVoiceConfig,
)
from chatforge.adapters.audio import VoxStreamAdapter, MockAudioStreamAdapter
from chatforge.adapters.artifact_render import LibreOfficeRenderDockerServerAdapter
from chatforge.adapters.artifact_editor import LibreOfficeEditorDockerServerAdapter
from chatforge.ports import NullTracingAdapter

__all__ = [
    # Storage
    "InMemoryStorageAdapter",
    "SQLiteStorageAdapter",
    # TTS
    "ElevenLabsTTSAdapter",
    "ElevenLabsVoiceConfig",
    "OpenAITTSAdapter",
    "OpenAIVoiceConfig",
    # Audio
    "VoxStreamAdapter",
    "MockAudioStreamAdapter",
    # Artifact Render
    "LibreOfficeRenderDockerServerAdapter",
    # Artifact Editor
    "LibreOfficeEditorDockerServerAdapter",
    # Null/Testing
    "NullMessagingAdapter",
    "NullKnowledgeAdapter",
    "NullTicketingAdapter",
    "NullTracingAdapter",
    "NullAudioStreamAdapter",
]
