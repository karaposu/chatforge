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
    # Storage facade
    Storage,
    # Repository interfaces
    ChatRepository,
    MessageRepository,
    ToolCallRepository,
    AgentRunRepository,
    LLMCallRepository,
    ProfilingRepository,
)
from chatforge.domain.storage import (
    # Records
    ChatRecord,
    MessageRecord,
    ParticipantRecord,
    AttachmentRecord,
    ToolCallRecord,
    AgentRunRecord,
    LLMCallRecord,
    ProfilingDataExtractionRun,
    ExtractedProfilingData,
    # TypedDict metadata
    ChatMetadata,
    MessageMetadata,
    TokenUsage,
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
from chatforge.ports.vad import (
    # Exceptions
    VADError,
    VADConfigError,
    # Enums
    SpeechState,
    # Data classes
    VADConfig as VADPortConfig,  # Alias to avoid conflict with audio_stream.VADConfig
    VADResult,
    VADMetrics,
    # Port
    VADPort,
)
from chatforge.ports.audio_playback import (
    # Exceptions
    AudioPlaybackError,
    DeviceNotFoundError,
    DeviceInUseError,
    PlaybackTimeoutError,
    # Enums
    PlaybackState,
    # Data classes
    AudioPlaybackConfig,
    OutputDevice,
    PlaybackMetrics,
    # Protocols
    DeviceEnumerable,
    # Port
    AudioPlaybackPort,
)
from chatforge.ports.audio_capture import (
    # Exceptions
    AudioCaptureError,
    DeviceNotFoundError as CaptureDeviceNotFoundError,
    DeviceInUseError as CaptureDeviceInUseError,
    UnsupportedConfigError,
    CaptureTimeoutError,
    # Enums
    CaptureState,
    # Data classes
    AudioCaptureConfig,
    AudioDevice as CaptureAudioDevice,
    CaptureMetrics,
    # Protocols
    DeviceEnumerable as CaptureDeviceEnumerable,
    # Port
    AudioCapturePort,
)
from chatforge.ports.artifact_render import (
    ArtifactRenderPort,
    ImageFormat,
)

__all__ = [
    # Messaging Platform Integration
    "MessagingPlatformIntegrationPort",
    "ConversationContext",
    "FileAttachment",
    "Message",
    # Storage facade + repos
    "Storage",
    "ChatRepository",
    "MessageRepository",
    "ToolCallRepository",
    "AgentRunRepository",
    "LLMCallRepository",
    "ProfilingRepository",
    # Storage records
    "ChatRecord",
    "MessageRecord",
    "ParticipantRecord",
    "AttachmentRecord",
    "ToolCallRecord",
    "AgentRunRecord",
    "LLMCallRecord",
    "ProfilingDataExtractionRun",
    "ExtractedProfilingData",
    "ChatMetadata",
    "MessageMetadata",
    "TokenUsage",
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
    # VAD
    "VADPort",
    "VADPortConfig",
    "VADResult",
    "VADMetrics",
    "SpeechState",
    "VADError",
    "VADConfigError",
    # Audio Playback
    "AudioPlaybackPort",
    "AudioPlaybackConfig",
    "OutputDevice",
    "PlaybackMetrics",
    "PlaybackState",
    "DeviceEnumerable",
    "AudioPlaybackError",
    "DeviceNotFoundError",
    "DeviceInUseError",
    "PlaybackTimeoutError",
    # Audio Capture
    "AudioCapturePort",
    "AudioCaptureConfig",
    "CaptureAudioDevice",
    "CaptureMetrics",
    "CaptureState",
    "CaptureDeviceEnumerable",
    "AudioCaptureError",
    "CaptureDeviceNotFoundError",
    "CaptureDeviceInUseError",
    "UnsupportedConfigError",
    "CaptureTimeoutError",
    # Artifact Render
    "ArtifactRenderPort",
    "ImageFormat",
]
