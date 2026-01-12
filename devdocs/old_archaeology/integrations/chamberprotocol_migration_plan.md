# ChamberProtocolAI Migration to Chatforge Storage

**Goal:** Replace ChamberProtocolAI's db models with Chatforge's SQLAlchemy models, adding only a User table for authentication.

---

## Schema Mapping

### What ChamberProtocol Has → What Chatforge Provides

```
ChamberProtocol                     Chatforge
───────────────                     ─────────
Chat                                Chat (enhanced)
├── id                              ├── id
├── user_id ──────────────────────► │   (via Participant with role='owner')
├── created_at                      ├── created_at
└── settings                        ├── settings
                                    ├── title (NEW)
                                    ├── system_prompt (NEW)
                                    ├── metadata_ (NEW)
                                    ├── updated_at (NEW)
                                    └── deleted_at (soft delete, NEW)

Message                             Message (enhanced)
├── id                              ├── id
├── chat_id                         ├── chat_id
├── user_id ──────────────────────► ├── participant_id → Participant.external_id
├── user_name ────────────────────► ├── sender_name (snapshot)
├── user_type ────────────────────► ├── role (user/assistant/system/tool)
├── message                         ├── content
├── message_format                  ├── content_format
├── message_type                    ├── message_type
├── timestamp                       ├── created_at
├── transcription                   ├── transcription
├── siluet_request_data ──────────► ├── generation_request_data (JSON, AI messages only)
└── step_context ─────────────────► └── (not used - disregard)

(missing)                           Participant (NEW)
                                    ├── id
                                    ├── chat_id
                                    ├── participant_type (user/assistant/agent)
                                    ├── external_id → User.id
                                    ├── display_name
                                    └── role_in_chat (owner/member)

LlmOperations                       AgentRun (enhanced)
├── user_id                         ├── chat_id (better context)
├── operation_type                  ├── agent_name
└── usage_data                      ├── token_usage
                                    ├── cost
                                    ├── status
                                    └── total_steps, total_tool_calls

User (keep your own)                (Not in Chatforge - by design)
├── id
├── email
├── password_hash
└── ...auth fields
```

---

## Migration Steps

### Step 1: Add User Model to ChamberProtocolAI (Keep Separate)

Chatforge deliberately doesn't include a User model (see docstring: "No User table: Chatforge doesn't own user management; links via external_id").

Create a minimal User model in ChamberProtocolAI:

```python
# src/db/models/user.py (ChamberProtocolAI - KEEP THIS)
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from chatforge.adapters.storage.models.models import Base  # Share the Base!
from datetime import datetime, timezone

class User(Base):
    """User model for ChamberProtocolAI authentication."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    # Add any ChamberProtocol-specific fields
    subscription_tier = Column(String(20), default="free", nullable=False)
    game_preferences = Column(JSON, default=dict, nullable=False)
```

### Step 2: Import Chatforge Models

```python
# src/db/models/__init__.py (ChamberProtocolAI)
from chatforge.adapters.storage.models.models import (
    Base,
    Chat,
    Participant,
    Message,
    Attachment,
    ToolCall,
    AgentRun,
)
from .user import User  # Your auth model

__all__ = [
    "Base",
    "Chat",
    "Participant",
    "Message",
    "Attachment",
    "ToolCall",
    "AgentRun",
    "User",
]
```

### Step 3: Update Repositories to Use Chatforge Models

```python
# src/db/repositories/chat_repository.py (ChamberProtocolAI - UPDATED)
from chatforge.adapters.storage.models.models import Chat, Participant
from datetime import datetime, timezone

class ChatRepository:
    def __init__(self, session):
        self.session = session

    def create_chat(self, *, user_id: int, settings: dict = None, title: str = None) -> Chat:
        """Create a new chat with the user as owner."""
        chat = Chat(
            title=title,
            settings=settings or {},
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(chat)
        self.session.flush()  # Get chat.id

        # Create owner participant
        participant = Participant(
            chat_id=chat.id,
            participant_type="user",
            external_id=str(user_id),  # Link to your User table
            display_name="Player",  # Or fetch from User table
            role_in_chat="owner",
        )
        self.session.add(participant)

        # Create AI participant
        ai_participant = Participant(
            chat_id=chat.id,
            participant_type="assistant",
            external_id="siluet",
            display_name="Silüet",
            role_in_chat="member",
        )
        self.session.add(ai_participant)

        self.session.commit()
        return chat

    def get_chat_by_id(self, chat_id: int) -> Chat | None:
        return self.session.query(Chat).filter(Chat.id == chat_id).first()

    def get_chats_by_user(self, user_id: int) -> list[Chat]:
        """Get all chats where user is a participant."""
        return (
            self.session.query(Chat)
            .join(Participant)
            .filter(Participant.external_id == str(user_id))
            .filter(Participant.role_in_chat == "owner")
            .filter(Chat.deleted_at.is_(None))  # Respect soft delete
            .order_by(Chat.created_at.desc())
            .all()
        )

    def user_owns_chat(self, chat_id: int, user_id: int) -> bool:
        """Check if user owns a chat."""
        return (
            self.session.query(Participant)
            .filter(Participant.chat_id == chat_id)
            .filter(Participant.external_id == str(user_id))
            .filter(Participant.role_in_chat == "owner")
            .first()
        ) is not None
```

```python
# src/db/repositories/message_repository.py (ChamberProtocolAI - UPDATED)
from chatforge.adapters.storage.models.models import Message, Participant
from datetime import datetime, timezone

class MessageRepository:
    def __init__(self, session):
        self.session = session

    def insert_message(
        self,
        *,
        chat_id: int,
        user_id: int,
        user_type: str,  # "user" or "assistant"
        user_name: str,
        message: str,
        message_format: str = "text",
        message_type: str = "generated",
        siluet_request_data: dict = None,  # Game-specific
        step_context: str = None,  # Game-specific
    ) -> Message:
        """Insert a message using Chatforge schema."""

        # Find or get participant
        participant = (
            self.session.query(Participant)
            .filter(Participant.chat_id == chat_id)
            .filter(Participant.external_id == str(user_id) if user_type == "user" else "siluet")
            .first()
        )

        msg = Message(
            chat_id=chat_id,
            participant_id=participant.id if participant else None,
            sender_name=user_name,  # Snapshot
            role=user_type,  # "user" or "assistant"
            content=message,
            content_format=message_format,
            message_type=message_type,
            # For AI messages, store the full prompt for debugging
            generation_request_data=siluet_request_data if user_type == "assistant" else None,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(msg)
        self.session.commit()
        return msg

    def fetch_messages(self, *, chat_id: int, limit: int = 50, offset: int = 0) -> list[Message]:
        return (
            self.session.query(Message)
            .filter(Message.chat_id == chat_id)
            .filter(Message.deleted_at.is_(None))  # Respect soft delete
            .order_by(Message.created_at.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def fetch_last_n(self, *, chat_id: int, n: int) -> list[Message]:
        rows = (
            self.session.query(Message)
            .filter(Message.chat_id == chat_id)
            .filter(Message.deleted_at.is_(None))
            .order_by(Message.created_at.desc())
            .limit(n)
            .all()
        )
        rows.reverse()  # Oldest first
        return rows
```

### Step 4: Update Services (Minimal Changes)

```python
# src/impl/services/chat/siluet_service.py - Access LLM request data for debugging
def _fetch_conversation_history(self) -> list[Message]:
    messages = message_repo.fetch_messages(chat_id=self.chat_id, limit=limit)

    for msg in messages:
        # For AI messages, access the original LLM request data for debugging
        if msg.role == "assistant" and msg.generation_request_data:
            original_prompt = msg.generation_request_data.get("prompt")
            # ... use for debugging/analysis

    return messages
```

### Step 5: Database Migration Script

```python
# scripts/migrate_to_chatforge_schema.py
"""
Migration script to move from ChamberProtocol schema to Chatforge schema.
Run this once to migrate existing data.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from chatforge.adapters.storage.models.models import Base, Chat, Participant, Message
from db.models.user import User

OLD_DB_URL = "sqlite:///old_chamber.db"
NEW_DB_URL = "sqlite:///new_chamber.db"

def migrate():
    old_engine = create_engine(OLD_DB_URL)
    new_engine = create_engine(NEW_DB_URL)

    # Create new schema
    Base.metadata.create_all(new_engine)

    OldSession = sessionmaker(bind=old_engine)
    NewSession = sessionmaker(bind=new_engine)

    old_session = OldSession()
    new_session = NewSession()

    # 1. Migrate users (copy as-is)
    old_users = old_session.execute(text("SELECT * FROM users")).fetchall()
    for user in old_users:
        new_user = User(
            id=user.id,
            email=user.email,
            password_hash=user.password_hash,
            # ... other fields
        )
        new_session.add(new_user)

    # 2. Migrate chats
    old_chats = old_session.execute(text("SELECT * FROM chats")).fetchall()
    for chat in old_chats:
        new_chat = Chat(
            id=chat.id,
            settings=chat.settings,
            created_at=chat.created_at,
        )
        new_session.add(new_chat)
        new_session.flush()

        # Create owner participant
        owner = Participant(
            chat_id=chat.id,
            participant_type="user",
            external_id=str(chat.user_id),
            display_name="Player",
            role_in_chat="owner",
        )
        new_session.add(owner)

        # Create AI participant
        ai = Participant(
            chat_id=chat.id,
            participant_type="assistant",
            external_id="siluet",
            display_name="Silüet",
            role_in_chat="member",
        )
        new_session.add(ai)

    # 3. Migrate messages
    old_messages = old_session.execute(text("SELECT * FROM messages")).fetchall()
    for msg in old_messages:
        new_msg = Message(
            id=msg.id,
            chat_id=msg.chat_id,
            sender_name=msg.user_name,
            role=msg.user_type,  # "user" or "assistant"
            content=msg.message,
            content_format=msg.message_format or "text",
            message_type=msg.message_type or "generated",
            transcription=msg.transcription,
            # Store LLM request data for AI messages only
            generation_request_data=msg.siluet_request_data if msg.user_type == "assistant" else None,
            created_at=msg.timestamp,
        )
        new_session.add(new_msg)

    new_session.commit()
    print(f"Migrated {len(old_chats)} chats, {len(old_messages)} messages")

if __name__ == "__main__":
    migrate()
```

---

## New Schema Advantages

After migration, ChamberProtocolAI gains:

| Feature | Benefit |
|---------|---------|
| **Soft delete** (`deleted_at`) | Recover deleted chats, audit trail |
| **Participant model** | Multi-player support, different roles |
| **Attachments** | File uploads in chat |
| **ToolCall tracking** | If you add game tools later |
| **AgentRun** | LLM cost tracking, debugging |
| **Threading** (`parent_id`) | Reply chains in chat |
| **Token counting** | Per-message token tracking |
| **Feedback** (`thumbs_up/down`) | Player feedback on AI responses |
| **generation_request_data** | Store full LLM prompt for debugging AI responses |

---

## Directory Structure After Migration

```
ChamberProtocolAI/src/
├── db/
│   ├── models/
│   │   ├── __init__.py      # Imports from chatforge + User
│   │   └── user.py          # Only custom model you own
│   └── repositories/
│       ├── chat_repository.py    # Updated for Chatforge models
│       ├── message_repository.py # Updated for Chatforge models
│       └── user_repository.py    # Keep as-is
```

---

## Dependency Updates

```toml
# pyproject.toml
[project]
dependencies = [
    "chatforge @ git+https://github.com/yourorg/chatforge.git",  # Or path
    "sqlalchemy>=2.0",
    "fastapi",
    # ... other deps
]
```

---

## Summary

**What changes:**
- Import Chatforge models instead of defining your own
- Store game-specific data in `Message.metadata_`
- Use `Participant` for user/AI identity
- Keep your own `User` model for auth

**What stays the same:**
- Repository pattern
- Service layer logic
- API endpoints
- Authentication

**Effort:** ~4-6 hours for migration + testing
