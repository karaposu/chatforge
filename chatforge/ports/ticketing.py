"""
Ticketing Port - Abstract interface for ticketing/workflow systems.

This port defines the contract for ticketing platform integrations.
Implementations can include Jira, ServiceNow, Zendesk, or custom systems.

The core agent logic depends only on this interface, enabling easy
swapping of ticketing platforms without changing business logic.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypedDict


class ActionCustomFields(TypedDict, total=False):
    """
    Type-safe custom fields for actions.

    All fields are optional (total=False) to maintain flexibility.
    Applications can extend with domain-specific fields.

    Attributes:
        source_platform: Platform where action originated.
        source_context_id: Original context identifier.
        requester_department: User's department.
        affected_system: System affected by the action.
        environment: Production, staging, development, etc.
    """

    source_platform: str
    source_context_id: str
    requester_department: str
    affected_system: str
    environment: str


class ActionPriority(str, Enum):
    """Standard action priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def from_string(cls, value: str) -> "ActionPriority":
        """Convert string to priority, defaulting to MEDIUM."""
        value_lower = value.lower()
        for priority in cls:
            if priority.value == value_lower:
                return priority
        return cls.MEDIUM


@dataclass
class ActionAttachment:
    """
    File to attach to an action.

    Attributes:
        file_path: Local path to the file (temporary).
        filename: Display name for the attachment.
        mimetype: MIME type of the file.
    """

    file_path: str
    filename: str
    mimetype: str = "application/octet-stream"


@dataclass
class ActionData:
    """
    Platform-agnostic action data.

    Contains all information needed to create an action/task/ticket,
    regardless of the underlying system.

    Attributes:
        title: Brief summary of the action.
        description: Detailed description with all gathered information.
        action_type: Type of action (e.g., "support_ticket", "task", "incident").
        priority: Action priority level.
        requester_email: Email of the user requesting the action.
        category: Optional category for routing/reporting.
        attachments: Files to attach to the action.
        custom_fields: Platform-specific custom fields.
    """

    title: str
    description: str
    action_type: str = "task"
    priority: ActionPriority = ActionPriority.MEDIUM
    requester_email: str | None = None
    category: str | None = None
    attachments: list[ActionAttachment] = field(default_factory=list)
    custom_fields: ActionCustomFields = field(default_factory=dict)  # type: ignore[assignment]

    def __post_init__(self):
        """Convert string priority to enum if needed."""
        if isinstance(self.priority, str):
            self.priority = ActionPriority.from_string(self.priority)


@dataclass
class ActionResult:
    """
    Result of action creation.

    Attributes:
        action_id: Unique identifier (e.g., "TASK-12345").
        action_url: URL to view the action.
        success: Whether creation was successful.
        error: Error message if creation failed.
        attached_files: List of successfully attached filenames.
        attachment_errors: List of files that failed to attach.
    """

    action_id: str
    action_url: str
    success: bool
    error: str | None = None
    attached_files: list[str] = field(default_factory=list)
    attachment_errors: list[str] = field(default_factory=list)

    def format_message(self, success_prefix: str = "Created", failure_prefix: str = "Failed") -> str:
        """
        Format result as user-friendly message.

        Args:
            success_prefix: Prefix for successful actions.
            failure_prefix: Prefix for failed actions.

        Returns:
            Formatted message string.
        """
        if not self.success:
            return f"{failure_prefix}: {self.error}"

        message = f"{success_prefix}: {self.action_id} ({self.action_url})"

        if self.attachment_errors:
            errors = "; ".join(self.attachment_errors)
            message += f"\nSome files could not be attached: {errors}"

        return message


class TicketingPort(ABC):
    """
    Abstract port for ticketing/workflow systems.

    This interface defines the contract that all ticketing system adapters
    must implement (Jira, ServiceNow, Zendesk, etc.).

    The core agent logic depends only on this interface.
    """

    @abstractmethod
    def execute(self, data: ActionData) -> ActionResult:
        """
        Execute an action (create ticket, task, etc.).

        Args:
            data: Action data including title, description, priority, etc.

        Returns:
            ActionResult with action ID and URL if successful.
        """

    @abstractmethod
    def attach_file(self, action_id: str, file_path: str, filename: str) -> bool:
        """
        Attach a file to an existing action.

        Args:
            action_id: ID of the action to attach to.
            file_path: Local path to the file.
            filename: Display name for the attachment.

        Returns:
            True if attachment was successful.
        """

    @abstractmethod
    def get_action(self, action_id: str) -> dict[str, Any] | None:
        """
        Retrieve action information.

        Args:
            action_id: ID of the action to retrieve.

        Returns:
            Action data as dict, or None if not found.
        """

    @abstractmethod
    def add_comment(self, action_id: str, comment: str) -> bool:
        """
        Add a comment to an existing action.

        Args:
            action_id: ID of the action.
            comment: Comment text to add.

        Returns:
            True if comment was added successfully.
        """

    @abstractmethod
    def update_status(self, action_id: str, status: str) -> bool:
        """
        Update the status of an action.

        Args:
            action_id: ID of the action.
            status: New status value.

        Returns:
            True if status was updated successfully.
        """
