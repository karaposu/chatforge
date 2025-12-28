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
]
