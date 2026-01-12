# Chatforge Query Helpers Proposal

Should Chatforge provide query helpers alongside models? Yes, but not full repositories.

---

## The Question

Chatforge provides SQLAlchemy models (`Chat`, `Message`, `Participant`, etc.). Should it also provide query logic?

| Option | Description |
|--------|-------------|
| Models only | Apps write all their own queries |
| Full repositories | Chatforge owns session management, CRUD, everything |
| **Query helpers** | Static methods, app owns session, copy-paste friendly |

---

## Recommendation: Query Helpers

Provide a `queries.py` module with static helper methods. Apps can:
1. Use them directly
2. Wrap them in their own repositories
3. Ignore them and write their own

---

## Proposed Implementation

```python
# chatforge/adapters/storage/queries.py
"""
Common query helpers for Chatforge models.

These are static methods that take a session as the first argument.
Apps own the session - Chatforge just provides the query logic.

Usage:
    from chatforge.adapters.storage.queries import MessageQueries

    messages = MessageQueries.get_history(session, chat_id=123)
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from .models.models import Chat, Message, Participant


class ChatQueries:
    """Common chat queries."""

    @staticmethod
    def get_by_id(session: Session, chat_id: int) -> Chat | None:
        """Get a chat by ID, excluding soft-deleted."""
        return (
            session.query(Chat)
            .filter(Chat.id == chat_id)
            .filter(Chat.deleted_at.is_(None))
            .first()
        )

    @staticmethod
    def get_by_id_with_participants(session: Session, chat_id: int) -> Chat | None:
        """Get a chat with participants eagerly loaded."""
        from sqlalchemy.orm import joinedload
        return (
            session.query(Chat)
            .options(joinedload(Chat.participants))
            .filter(Chat.id == chat_id)
            .filter(Chat.deleted_at.is_(None))
            .first()
        )

    @staticmethod
    def get_user_chats(session: Session, user_external_id: str) -> list[Chat]:
        """Get all active chats where user is owner."""
        return (
            session.query(Chat)
            .join(Participant)
            .filter(Participant.external_id == user_external_id)
            .filter(Participant.role_in_chat == "owner")
            .filter(Chat.deleted_at.is_(None))
            .order_by(Chat.created_at.desc())
            .all()
        )

    @staticmethod
    def user_owns_chat(session: Session, chat_id: int, user_external_id: str) -> bool:
        """Check if user is owner of a chat. Useful for authorization."""
        return (
            session.query(Participant)
            .filter(Participant.chat_id == chat_id)
            .filter(Participant.external_id == user_external_id)
            .filter(Participant.role_in_chat == "owner")
            .first()
        ) is not None


class MessageQueries:
    """Common message queries."""

    @staticmethod
    def get_history(
        session: Session,
        chat_id: int,
        limit: int = 50,
    ) -> list[Message]:
        """
        Get recent messages for a chat, oldest first.
        Excludes soft-deleted messages.
        """
        msgs = (
            session.query(Message)
            .filter(Message.chat_id == chat_id)
            .filter(Message.deleted_at.is_(None))
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(msgs))

    @staticmethod
    def get_history_for_llm(
        session: Session,
        chat_id: int,
        limit: int = 50,
    ) -> list[dict[str, str]]:
        """
        Get history in LLM-ready format.
        Returns: [{"role": "user", "content": "..."}, ...]
        """
        msgs = MessageQueries.get_history(session, chat_id, limit)
        return [{"role": m.role, "content": m.content} for m in msgs]

    @staticmethod
    def get_last_message(session: Session, chat_id: int) -> Message | None:
        """Get the most recent message in a chat."""
        return (
            session.query(Message)
            .filter(Message.chat_id == chat_id)
            .filter(Message.deleted_at.is_(None))
            .order_by(Message.created_at.desc())
            .first()
        )

    @staticmethod
    def count(session: Session, chat_id: int) -> int:
        """Count messages in a chat."""
        return (
            session.query(Message)
            .filter(Message.chat_id == chat_id)
            .filter(Message.deleted_at.is_(None))
            .count()
        )

    @staticmethod
    def get_by_role(
        session: Session,
        chat_id: int,
        role: str,
        limit: int = 50,
    ) -> list[Message]:
        """Get messages by role (user, assistant, system, tool)."""
        return (
            session.query(Message)
            .filter(Message.chat_id == chat_id)
            .filter(Message.role == role)
            .filter(Message.deleted_at.is_(None))
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )


class ParticipantQueries:
    """Common participant queries."""

    @staticmethod
    def get_chat_participants(session: Session, chat_id: int) -> list[Participant]:
        """Get all active participants in a chat."""
        return (
            session.query(Participant)
            .filter(Participant.chat_id == chat_id)
            .filter(Participant.left_at.is_(None))
            .all()
        )

    @staticmethod
    def get_by_external_id(
        session: Session,
        chat_id: int,
        external_id: str,
    ) -> Participant | None:
        """Get a participant by their external ID."""
        return (
            session.query(Participant)
            .filter(Participant.chat_id == chat_id)
            .filter(Participant.external_id == external_id)
            .first()
        )

    @staticmethod
    def get_owner(session: Session, chat_id: int) -> Participant | None:
        """Get the owner of a chat."""
        return (
            session.query(Participant)
            .filter(Participant.chat_id == chat_id)
            .filter(Participant.role_in_chat == "owner")
            .first()
        )
```

---

## Why This Approach

| Principle | How Query Helpers Follow It |
|-----------|---------------------------|
| **Toolkit, not framework** | Static methods, no framework conventions |
| **App owns session** | Session passed as argument, not managed |
| **Copy-paste friendly** | Don't like a method? Copy and modify |
| **Not required** | Apps can ignore entirely |
| **Useful defaults** | `get_history_for_llm()` is universally needed |
| **No magic** | Just plain SQLAlchemy queries |

---

## Usage Patterns

### Pattern 1: Use Directly

```python
from chatforge.adapters.storage.queries import MessageQueries, ChatQueries

def get_chat_context(session, chat_id: int, user_id: str):
    # Authorization
    if not ChatQueries.user_owns_chat(session, chat_id, user_id):
        raise PermissionError("Not your chat")

    # Get history for LLM
    return MessageQueries.get_history_for_llm(session, chat_id)
```

### Pattern 2: Wrap in Repository

```python
from chatforge.adapters.storage.queries import MessageQueries

class MessageRepository:
    def __init__(self, session):
        self.session = session

    def get_history(self, chat_id: int, limit: int = 20) -> list[Message]:
        # Delegate to Chatforge
        return MessageQueries.get_history(self.session, chat_id, limit)

    def get_history_as_string(self, chat_id: int) -> str:
        # Your custom method
        msgs = self.get_history(chat_id)
        return "\n".join(f"{m.sender_name}: {m.content}" for m in msgs)

    def add_user_message(self, chat_id: int, content: str) -> Message:
        # Your custom method - not in Chatforge
        msg = Message(
            chat_id=chat_id,
            sender_name="Player",
            role="user",
            content=content,
        )
        self.session.add(msg)
        self.session.commit()
        return msg
```

### Pattern 3: Extend with Subclass

```python
from chatforge.adapters.storage.queries import MessageQueries

class GameMessageQueries(MessageQueries):
    """Extended queries for game-specific needs."""

    @staticmethod
    def get_ai_messages_with_prompts(session, chat_id: int) -> list[Message]:
        """Get AI messages that have generation_request_data."""
        return (
            session.query(Message)
            .filter(Message.chat_id == chat_id)
            .filter(Message.role == "assistant")
            .filter(Message.generation_request_data.isnot(None))
            .order_by(Message.created_at.desc())
            .all()
        )
```

### Pattern 4: Ignore and Write Your Own

```python
# Don't use Chatforge queries at all
class MyMessageRepository:
    def __init__(self, session):
        self.session = session

    def get_history(self, chat_id: int) -> list[Message]:
        # Your own implementation
        return (
            self.session.query(Message)
            .filter(Message.chat_id == chat_id)
            .order_by(Message.created_at.asc())  # Different ordering
            .all()
        )
```

---

## What Query Helpers Are NOT

| NOT | Because |
|-----|---------|
| Repositories | No session management, no CRUD methods |
| Required | Apps can ignore completely |
| Opinionated | Just common patterns, not "the right way" |
| Complete | Apps will have custom queries |

---

## Comparison: Repositories vs Query Helpers

```
REPOSITORIES (what we're NOT doing):
┌─────────────────────────────────────┐
│ class MessageRepository:            │
│     def __init__(self, session):    │  ← Owns session
│         self.session = session      │
│                                     │
│     def add(self, msg): ...         │  ← CRUD methods
│     def delete(self, id): ...       │
│     def get_history(self): ...      │
└─────────────────────────────────────┘

QUERY HELPERS (what we ARE doing):
┌─────────────────────────────────────┐
│ class MessageQueries:               │
│                                     │
│     @staticmethod                   │  ← No state
│     def get_history(session, ...):  │  ← Session passed in
│         ...                         │
└─────────────────────────────────────┘
```

---

## File Structure

```
chatforge/adapters/storage/
├── models/
│   ├── __init__.py
│   └── models.py          # Chat, Message, Participant, etc.
├── queries.py              # NEW: ChatQueries, MessageQueries, etc.
└── ...
```

---

## Export in __init__.py

```python
# chatforge/adapters/storage/__init__.py
from .models.models import (
    Base,
    Chat,
    Message,
    Participant,
    Attachment,
    ToolCall,
    AgentRun,
)
from .queries import (
    ChatQueries,
    MessageQueries,
    ParticipantQueries,
)

__all__ = [
    # Models
    "Base",
    "Chat",
    "Message",
    "Participant",
    "Attachment",
    "ToolCall",
    "AgentRun",
    # Query helpers
    "ChatQueries",
    "MessageQueries",
    "ParticipantQueries",
]
```

---

## Summary

| Aspect | Decision |
|--------|----------|
| Provide query logic? | Yes, as static helpers |
| Session management? | No, app owns session |
| CRUD operations? | No, just reads (queries) |
| Required? | No, optional helpers |
| Extensible? | Yes, subclass or copy |
| Philosophy | Toolkit, not framework |
