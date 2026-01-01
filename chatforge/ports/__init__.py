"""
Chatforge Ports - Abstract interfaces for external integrations.

Ports define the contracts that adapters must implement.
The core agent logic depends only on these interfaces, enabling:
- Easy swapping of implementations
- Mock implementations for testing
- Multiple simultaneous adapters
"""

from chatforge.ports.ticketing import (
    ActionAttachment,
    ActionCustomFields,
    ActionData,
    ActionPriority,
    ActionResult,
    TicketingPort,
)
from chatforge.ports.knowledge import (
    KnowledgeMetadata,
    KnowledgePort,
    KnowledgeResult,
)
from chatforge.ports.messaging_platform_integration import (
    ConversationContext,
    FileAttachment,
    Message,
    MessagingPlatformIntegrationPort,
)
from chatforge.ports.storage import (
    # Core types
    StoragePort,
    MessageRecord,
    MessageMetadata,
    # New types
    ChatRecord,
    ChatMetadata,
    ToolCallRecord,
    AgentRunRecord,
    TokenUsage,
    # Legacy aliases (for backward compatibility)
    ConversationRecord,
    ConversationMetadata,
)
from chatforge.ports.tracing import (
    NullTracingAdapter,
    TracingPort,
)
from chatforge.ports.tts import (
    TTSPort,
    VoiceConfig,
    AudioResult,
    VoiceInfo,
    AudioFormat,
    AudioQuality,
    TTSError,
    TTSNetworkError,
    TTSAuthenticationError,
    TTSQuotaExceededError,
    TTSRateLimitError,
    TTSInvalidVoiceError,
    TTSInvalidInputError,
    TTSStreamingNotSupportedError,
)
from chatforge.ports.audio_stream import (
    AudioStreamPort,
    AudioStreamConfig,
    VADConfig,
    AudioCallbacks,
    AudioDevice,
    AudioStreamError,
    AudioStreamDeviceError,
    AudioStreamBufferError,
    AudioStreamNotInitializedError,
)
from chatforge.ports.realtime_voice import (
    # Exceptions
    RealtimeError,
    RealtimeConnectionError,
    RealtimeAuthenticationError,
    RealtimeRateLimitError,
    RealtimeProviderError,
    RealtimeSessionError,
    # Enums
    VoiceEventType,
    # Data classes
    VoiceEvent,
    VoiceSessionConfig,
    ToolDefinition,
    ProviderCapabilities,
    # Port
    RealtimeVoiceAPIPort,
)

__all__ = [
    # Messaging Platform Integration
    "MessagingPlatformIntegrationPort",
    "ConversationContext",
    "FileAttachment",
    "Message",
    # Storage
    "StoragePort",
    "MessageRecord",
    "MessageMetadata",
    "ChatRecord",
    "ChatMetadata",
    "ToolCallRecord",
    "AgentRunRecord",
    "TokenUsage",
    # Legacy aliases
    "ConversationRecord",
    "ConversationMetadata",
    # Knowledge
    "KnowledgePort",
    "KnowledgeResult",
    "KnowledgeMetadata",
    # Ticketing
    "TicketingPort",
    "ActionData",
    "ActionResult",
    "ActionPriority",
    "ActionAttachment",
    "ActionCustomFields",
    # Tracing
    "TracingPort",
    "NullTracingAdapter",
    # TTS
    "TTSPort",
    "VoiceConfig",
    "AudioResult",
    "VoiceInfo",
    "AudioFormat",
    "AudioQuality",
    "TTSError",
    "TTSNetworkError",
    "TTSAuthenticationError",
    "TTSQuotaExceededError",
    "TTSRateLimitError",
    "TTSInvalidVoiceError",
    "TTSInvalidInputError",
    "TTSStreamingNotSupportedError",
    # Audio Stream
    "AudioStreamPort",
    "AudioStreamConfig",
    "VADConfig",
    "AudioCallbacks",
    "AudioDevice",
    "AudioStreamError",
    "AudioStreamDeviceError",
    "AudioStreamBufferError",
    "AudioStreamNotInitializedError",
    # Realtime Voice
    "RealtimeVoiceAPIPort",
    "VoiceEvent",
    "VoiceEventType",
    "VoiceSessionConfig",
    "ToolDefinition",
    "ProviderCapabilities",
    "RealtimeError",
    "RealtimeConnectionError",
    "RealtimeAuthenticationError",
    "RealtimeRateLimitError",
    "RealtimeProviderError",
    "RealtimeSessionError",
]
