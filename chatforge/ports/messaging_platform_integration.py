"""
Messaging Platform Integration Port - Abstract interface for external messaging platforms.

This port defines the contract for integrating with external messaging platforms
like Slack, Microsoft Teams, Discord, or other chat systems.

Use this port when chatforge is embedded INSIDE a platform (e.g., as a Slack bot).
If you're building your own chat UI, you likely don't need this - just use StoragePort.

The core agent logic depends only on this interface, not on concrete
implementations, enabling easy swapping of messaging platforms.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConversationContext:
    """
    Platform-agnostic conversation context.

    This class encapsulates all the information needed to identify and
    interact with a conversation, regardless of the underlying platform.

    Attributes:
        conversation_id: Unique identifier for the conversation thread.
        user_id: Platform-specific user identifier.
        user_email: User's email address (if available).
        platform: Name of the messaging platform ("slack", "teams", "discord", "api").
        metadata: Platform-specific extras that don't fit the generic model.
    """

    conversation_id: str
    user_id: str
    user_email: str | None = None
    platform: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Safely get metadata value."""
        return self.metadata.get(key, default)


@dataclass
class FileAttachment:
    """
    Platform-agnostic file attachment.

    Represents a file uploaded by the user that may need to be:
    - Downloaded for analysis (images, logs)
    - Attached to actions/tickets
    - Processed by the agent

    Attributes:
        file_id: Platform-specific file identifier.
        filename: Original filename with extension.
        mimetype: MIME type of the file (e.g., "image/png", "text/plain").
        download_url: URL to download the file content.
        size_bytes: File size in bytes (0 if unknown).
    """

    file_id: str
    filename: str
    mimetype: str
    download_url: str
    size_bytes: int = 0

    @property
    def is_image(self) -> bool:
        """Check if file is an image."""
        return self.mimetype.startswith("image/")

    @property
    def is_text(self) -> bool:
        """Check if file is a text file."""
        return self.mimetype.startswith("text/") or self.mimetype in (
            "application/json",
            "application/xml",
        )


@dataclass
class Message:
    """
    Platform-agnostic message.

    Attributes:
        content: Message text content.
        role: Message role ("user" or "assistant").
        attachments: List of file attachments (if any).
    """

    content: str
    role: str  # "user" | "assistant"
    attachments: list[FileAttachment] = field(default_factory=list)


class MessagingPlatformIntegrationPort(ABC):
    """
    Abstract port for integrating with external messaging platforms.

    This interface defines the contract that all messaging platform adapters
    must implement (Slack, Teams, Discord, etc.). The core agent logic depends
    only on this interface, enabling:

    - Easy swapping of messaging platforms
    - Mock implementations for testing
    - Multiple simultaneous platform support

    Use this when chatforge runs INSIDE a platform. If building your own
    chat UI, you probably don't need this - just use StoragePort directly.
    """

    @abstractmethod
    async def get_conversation_history(self, context: ConversationContext) -> list[Message]:
        """
        Retrieve conversation history from the platform.

        Args:
            context: Conversation context with platform-specific identifiers.

        Returns:
            List of Message objects in chronological order.
        """

    @abstractmethod
    async def send_message(self, context: ConversationContext, message: str) -> None:
        """
        Send a message to the conversation.

        Args:
            context: Conversation context identifying where to send.
            message: Text content to send.
        """

    @abstractmethod
    async def send_typing_indicator(self, context: ConversationContext) -> None:
        """
        Show typing indicator in the conversation.

        This provides feedback to the user that the agent is processing.

        Args:
            context: Conversation context.
        """

    @abstractmethod
    async def download_file(self, file: FileAttachment, context: ConversationContext) -> bytes:
        """
        Download file content from the platform.

        Args:
            file: File attachment with download URL.
            context: Conversation context (may be needed for auth).

        Returns:
            Raw file content as bytes.
        """

    @abstractmethod
    async def get_user_email(self, user_id: str) -> str | None:
        """
        Resolve user email from platform user ID.

        Args:
            user_id: Platform-specific user identifier.

        Returns:
            User's email address, or None if not available.
        """

    @abstractmethod
    async def get_user_display_name(self, user_id: str) -> str:
        """
        Get user's display name for personalization.

        Args:
            user_id: Platform-specific user identifier.

        Returns:
            User's display name (falls back to user_id if unavailable).
        """
