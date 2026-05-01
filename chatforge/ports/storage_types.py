"""
Backward-compatibility shim.

Records have moved to chatforge.domain.storage.records.
This file re-exports everything so existing imports don't break.
"""

from chatforge.domain.storage.records import *  # noqa: F401, F403
from chatforge.domain.storage.records import (
    AgentRunRecord,
    AttachmentRecord,
    ChatMetadata,
    ChatRecord,
    ConversationMetadata,
    ConversationRecord,
    ExtractedProfilingData,
    LLMCallRecord,
    MessageMetadata,
    MessageRecord,
    ParticipantRecord,
    ProfilingDataExtractionRun,
    TokenUsage,
    ToolCallRecord,
)
