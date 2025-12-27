"""
SQLAlchemy ORM Models for Chatforge Storage.

This module provides SQLAlchemy models for persistent storage adapters.

Key Design Decisions:
- No User table: Chatforge doesn't own user management; links via external_id
- Participants: Both humans and AIs are first-class participants
- sender_name: Snapshot field capturing display name at send time

Example:
    from chatforge.adapters.storage.models import Chat, Participant, Message
    from chatforge.adapters.storage.models import Base  # For creating tables

    # Create all tables
    Base.metadata.create_all(engine)

For dataclass types, import from ports:
    from chatforge.ports.storage_types import MessageRecord, ChatRecord
"""

from chatforge.adapters.storage.models.models import (
    AgentRun,
    Attachment,
    Base,
    Chat,
    Message,
    Participant,
    ToolCall,
)

__all__ = [
    # SQLAlchemy models
    "Base",
    "Chat",
    "Participant",
    "Message",
    "Attachment",
    "ToolCall",
    "AgentRun",
]
