"""
Null Adapters - No-op implementations for testing and development.

These adapters implement port interfaces but do nothing.
Useful for:
- Testing components in isolation
- Development without external services
- Placeholder implementations
"""

from typing import AsyncGenerator, Optional

from chatforge.ports import (
    ActionData,
    ActionResult,
    ConversationContext,
    FileAttachment,
    KnowledgePort,
    KnowledgeResult,
    Message,
    MessagingPlatformIntegrationPort,
    TicketingPort,
    AudioStreamPort,
    AudioStreamConfig,
    AudioDevice,
    AudioCallbacks,
)


class NullMessagingAdapter(MessagingPlatformIntegrationPort):
    """
    Null implementation of MessagingPlatformIntegrationPort.

    All operations are no-ops that return empty/default values.
    """

    async def get_conversation_history(self, context: ConversationContext) -> list[Message]:
        """Return empty history."""
        return []

    async def send_message(self, context: ConversationContext, message: str) -> None:
        """No-op."""

    async def send_typing_indicator(self, context: ConversationContext) -> None:
        """No-op."""

    async def download_file(self, file: FileAttachment, context: ConversationContext) -> bytes:
        """Return empty bytes."""
        return b""

    async def get_user_email(self, user_id: str) -> str | None:
        """Return None."""
        return None

    async def get_user_display_name(self, user_id: str) -> str:
        """Return user_id as display name."""
        return user_id


class NullKnowledgeAdapter(KnowledgePort):
    """
    Null implementation of KnowledgePort.

    Returns empty results for all queries.
    """

    def search(self, query: str, limit: int = 5) -> list[KnowledgeResult]:
        """Return empty results."""
        return []

    def get_context_for_rag(self, query: str, max_tokens: int = 1000) -> str:
        """Return empty context."""
        return ""

    def get_page_content(self, page_id: str) -> str | None:
        """Return None."""
        return None


class NullTicketingAdapter(TicketingPort):
    """
    Null implementation of TicketingPort.

    Returns successful results without actually creating tickets.
    """

    def execute(self, data: ActionData) -> ActionResult:
        """Return fake successful result."""
        return ActionResult(
            action_id="NULL-0000",
            action_url="https://example.com/null",
            success=True,
        )

    def attach_file(self, action_id: str, file_path: str, filename: str) -> bool:
        """Return True without attaching."""
        return True

    def get_action(self, action_id: str) -> dict | None:
        """Return None."""
        return None

    def add_comment(self, action_id: str, comment: str) -> bool:
        """Return True without adding comment."""
        return True

    def update_status(self, action_id: str, status: str) -> bool:
        """Return True without updating status."""
        return True


class NullAudioStreamAdapter(AudioStreamPort):
    """
    Null implementation of AudioStreamPort.

    No-op audio adapter for testing without audio hardware.
    Useful when audio features are disabled but code expects an adapter.
    """

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "null"

    async def __aenter__(self) -> "NullAudioStreamAdapter":
        """Enter async context (no-op)."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context (no-op)."""
        pass

    async def start_capture(self) -> AsyncGenerator[bytes, None]:
        """Yield nothing - immediately returns."""
        return
        yield  # Make it a generator

    async def stop_capture(self) -> None:
        """No-op."""
        pass

    async def play(self, chunk: bytes) -> None:
        """Discard audio."""
        pass

    async def end_playback(self) -> None:
        """No-op."""
        pass

    async def stop_playback(self) -> None:
        """No-op."""
        pass

    def set_callbacks(self, callbacks: AudioCallbacks) -> None:
        """No-op - callbacks never fire."""
        pass

    def list_input_devices(self) -> list[AudioDevice]:
        """Return empty list."""
        return []

    def set_input_device(self, device_id: Optional[int]) -> None:
        """No-op."""
        pass

    def get_config(self) -> AudioStreamConfig:
        """Return default config."""
        return AudioStreamConfig()
