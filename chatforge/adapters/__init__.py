"""
Chatforge Adapters - Implementations of port interfaces.

Provides storage adapters, TTS adapters, and null/testing adapters.
"""

from chatforge.adapters.null import (
    NullKnowledgeAdapter,
    NullMessagingAdapter,
    NullTicketingAdapter,
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
    # Null/Testing
    "NullMessagingAdapter",
    "NullKnowledgeAdapter",
    "NullTicketingAdapter",
    "NullTracingAdapter",
]
