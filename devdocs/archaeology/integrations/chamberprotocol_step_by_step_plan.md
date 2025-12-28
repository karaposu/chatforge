# ChamberProtocolAI → Chatforge: Step-by-Step Migration Plan

A practical, sequential guide to migrating ChamberProtocolAI to use Chatforge for LLM calls and storage.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MIGRATION SUMMARY                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  REPLACE                          │  KEEP                               │
│  ─────────                        │  ────                               │
│  • llmservice package             │  • prompts.py (your templates)      │
│  • Custom Chat model              │  • StepContext (prompt builder)     │
│  • Custom Message model           │  • User model (your auth)           │
│  • Custom db creation script      │  • JWT middleware                   │
│                                   │  • API endpoints structure          │
│                                   │  • Repository pattern               │
├─────────────────────────────────────────────────────────────────────────┤
│  ESTIMATED TIME: ~3.5 hours (fresh DB) or ~4 hours (with migration)    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

Before starting, ensure you have:

- [ ] Access to ChamberProtocolAI codebase
- [ ] Access to Chatforge codebase (local clone)
- [ ] Backup of current database
- [ ] Test environment ready

---

## Phase 1: Install Chatforge

Install Chatforge as an editable package in ChamberProtocolAI's virtual environment.

### Step 1.1: Install Chatforge

```bash
# From ChamberProtocolAI directory
cd /path/to/ChamberProtocolAI

# Activate your virtual environment
source .venv/bin/activate

# Install Chatforge as editable package
cd /path/to/chatforge
pip install -e .

# Return to ChamberProtocolAI
cd /path/to/ChamberProtocolAI
```

### Step 1.2: Verify Installation

```bash
python -c "
from chatforge.adapters.storage.models.models import Base, Chat, Message, Participant
from chatforge.services.llm.factory import get_llm
print('Chatforge installed successfully!')
"
```

**That's it for Phase 1!** No copying files, no config issues.

---

## Phase 2: Database Models

### Step 2.1: Update User Model to Use Chatforge's Base

**File:** `src/db/models/user.py`

```python
# BEFORE
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class User(Base):
    ...

# AFTER
from chatforge.adapters.storage.models.models import Base  # Use Chatforge's Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from datetime import datetime, timezone

class User(Base):
    """User model for ChamberProtocolAI authentication."""
    __tablename__ = "users"

    # Keep all your existing User fields - this entire model is yours
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    subscription_tier = Column(String(20), default="free", nullable=False)
    game_preferences = Column(JSON, default=dict, nullable=False)
    # ... any other fields you have
```

### Step 2.2: Update Models __init__.py

**File:** `src/db/models/__init__.py`

```python
# BEFORE
from .base import Base
from .chat import Chat
from .message import Message
from .user import User

# AFTER
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

### Step 2.3: Delete Old Model Files

```bash
# These are now provided by Chatforge
rm src/db/models/chat.py      # Replaced by Chatforge Chat
rm src/db/models/message.py   # Replaced by Chatforge Message
rm src/db/models/base.py      # Using Chatforge's Base
```

**Verify:**
```bash
python -c "from src.db.models import Base, Chat, Message, Participant, User; print('OK')"
```

---

## Phase 3: Database Creation Script

### Step 3.1: Update create_glassmind_db.py

**File:** `src/db/scripts/create_glassmind_db.py`

```python
# BEFORE
from src.db.models import Base, Chat, Message, User
from sqlalchemy import create_engine

def create_database():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)

# AFTER
"""
Creates database with Chatforge models + User model.
Run once to set up fresh database.
"""
import os
from sqlalchemy import create_engine
from chatforge.adapters.storage.models.models import Base

# Import User to register it with the shared Base
from src.db.models.user import User

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///glassmind.db")


def create_database():
    """Create all tables using Chatforge's Base."""
    engine = create_engine(DATABASE_URL)

    # This creates ALL tables registered with Base:
    # - chats (from Chatforge)
    # - participants (from Chatforge)
    # - messages (from Chatforge)
    # - attachments (from Chatforge)
    # - tool_calls (from Chatforge)
    # - agent_runs (from Chatforge)
    # - users (from your User model)
    Base.metadata.create_all(engine)

    print("Database created with tables:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")


def drop_database():
    """Drop all tables (use with caution!)."""
    engine = create_engine(DATABASE_URL)
    Base.metadata.drop_all(engine)
    print("All tables dropped.")


if __name__ == "__main__":
    create_database()
```

**Verify:**
```bash
python -c "
from sqlalchemy import create_engine
from chatforge.adapters.storage.models.models import Base
from src.db.models.user import User

engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
print('Tables:', [t.name for t in Base.metadata.sorted_tables])
"
# Should print: ['chats', 'participants', 'messages', 'attachments', 'tool_calls', 'agent_runs', 'users']
```

---

## Phase 4: Repositories

### Step 4.1: Update ChatRepository

**File:** `src/db/repositories/chat_repository.py`

```python
from chatforge.adapters.storage.models.models import Chat, Participant
from sqlalchemy.orm import Session
from datetime import datetime, timezone


class ChatRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        user_id: int,
        title: str = None,
        settings: dict = None,
    ) -> Chat:
        """Create a new chat with the user as owner."""
        chat = Chat(
            title=title,
            settings=settings or {},
        )
        self.session.add(chat)
        self.session.flush()  # Get chat.id

        # Create owner participant (links to your User table)
        owner = Participant(
            chat_id=chat.id,
            participant_type="user",
            external_id=str(user_id),
            display_name="Player",
            role_in_chat="owner",
        )

        # Create AI participant
        ai = Participant(
            chat_id=chat.id,
            participant_type="assistant",
            external_id="siluet",
            display_name="Silüet",
            role_in_chat="member",
        )

        self.session.add_all([owner, ai])
        self.session.commit()
        return chat

    def get_by_id(self, chat_id: int) -> Chat | None:
        """Get chat by ID, excluding soft-deleted."""
        return (
            self.session.query(Chat)
            .filter(Chat.id == chat_id)
            .filter(Chat.deleted_at.is_(None))
            .first()
        )

    def get_user_chats(self, user_id: int) -> list[Chat]:
        """Get all active chats owned by a user."""
        return (
            self.session.query(Chat)
            .join(Participant)
            .filter(Participant.external_id == str(user_id))
            .filter(Participant.role_in_chat == "owner")
            .filter(Chat.deleted_at.is_(None))
            .order_by(Chat.created_at.desc())
            .all()
        )

    def user_owns_chat(self, chat_id: int, user_id: int) -> bool:
        """Check if user owns a chat. Used for authorization."""
        return (
            self.session.query(Participant)
            .filter(Participant.chat_id == chat_id)
            .filter(Participant.external_id == str(user_id))
            .filter(Participant.role_in_chat == "owner")
            .first()
        ) is not None

    def soft_delete(self, chat_id: int) -> bool:
        """Soft delete a chat."""
        chat = self.get_by_id(chat_id)
        if chat:
            chat.deleted_at = datetime.now(timezone.utc)
            self.session.commit()
            return True
        return False
```

### Step 4.2: Update MessageRepository

**File:** `src/db/repositories/message_repository.py`

```python
from chatforge.adapters.storage.models.models import Message
from sqlalchemy.orm import Session
from datetime import datetime, timezone


class MessageRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_user_message(
        self,
        chat_id: int,
        content: str,
        sender_name: str = "Player",
    ) -> Message:
        """Add a message from the user."""
        msg = Message(
            chat_id=chat_id,
            sender_name=sender_name,
            role="user",
            content=content,
            message_type="user",
        )
        self.session.add(msg)
        self.session.commit()
        return msg

    def add_ai_message(
        self,
        chat_id: int,
        content: str,
        generation_data: dict = None,
        sender_name: str = "Silüet",
    ) -> Message:
        """Add a message from the AI with optional debug data."""
        msg = Message(
            chat_id=chat_id,
            sender_name=sender_name,
            role="assistant",
            content=content,
            message_type="generated",
            generation_request_data=generation_data,
        )
        self.session.add(msg)
        self.session.commit()
        return msg

    def get_history(self, chat_id: int, limit: int = 20) -> list[Message]:
        """Get recent messages, oldest first."""
        messages = (
            self.session.query(Message)
            .filter(Message.chat_id == chat_id)
            .filter(Message.deleted_at.is_(None))
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(messages))

    def get_history_as_string(self, chat_id: int, limit: int = 20) -> str:
        """Get history formatted for prompt building."""
        messages = self.get_history(chat_id, limit)
        return "\n".join(f"{m.sender_name}: {m.content}" for m in messages)

    def get_history_for_llm(self, chat_id: int, limit: int = 20) -> list[dict]:
        """Get history in LLM-ready format."""
        messages = self.get_history(chat_id, limit)
        return [{"role": m.role, "content": m.content} for m in messages]
```

### Step 4.3: UserRepository (No Changes)

**File:** `src/db/repositories/user_repository.py`

Keep as-is. It uses your `User` model, not Chatforge's.

---

## Phase 5: LLM Service

### Step 5.1: Update MyLLMService

**File:** `src/impl/myllmservice.py`

```python
# BEFORE
from llmservice import BaseLLMService

class MyLLMService(BaseLLMService):
    def __init__(self):
        super().__init__(
            default_model_name="gpt-4.1-nano",
            max_rpm=500,
            max_concurrent_requests=200
        )

    def generate_siluet_answer(self, ...):
        # Complex logic
        ...

# AFTER
from chatforge.services.llm.factory import get_llm
from langchain_core.messages import HumanMessage


class MyLLMService:
    """LLM service using Chatforge's get_llm() factory."""

    def __init__(self, default_model: str = "gpt-4o-mini"):
        self.default_model = default_model
        self._llm_cache = {}

    def _get_llm(self, model: str = None):
        """Get or create cached LLM instance."""
        model = model or self.default_model
        if model not in self._llm_cache:
            self._llm_cache[model] = get_llm(provider="openai", model_name=model)
        return self._llm_cache[model]

    def generate_siluet_answer(self, prompt: str, model: str = None) -> str:
        """Generate AI response for the given prompt."""
        llm = self._get_llm(model)
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
```

**Verify:**
```bash
python -c "
from src.impl.myllmservice import MyLLMService
svc = MyLLMService()
print('LLM service initialized with model:', svc.default_model)
"
```

---

## Phase 6: Services

### Step 6.1: Update SiluetService

**File:** `src/impl/services/chat/siluet_service.py`

```python
from src.db.repositories.chat_repository import ChatRepository
from src.db.repositories.message_repository import MessageRepository
from src.impl.myllmservice import MyLLMService
from src.schemas import StepContext, SiluetResponse  # Your schemas - UNCHANGED


class SiluetService:
    def __init__(self, user_id: int, chat_id: int, request, session):
        self.chat_repo = ChatRepository(session)
        self.message_repo = MessageRepository(session)
        self.llm_service = MyLLMService()
        self.user_id = user_id
        self.chat_id = chat_id
        self.request = request

    def _process_request(self):
        # Authorization check
        if not self.chat_repo.user_owns_chat(self.chat_id, self.user_id):
            raise PermissionError("User does not own this chat")

        # 1. Get history (repository provides formatted string)
        history_str = self.message_repo.get_history_as_string(self.chat_id)

        # 2. Build prompt (YOUR code - unchanged)
        context = StepContext(
            conversation_memory=history_str,
            player_input=self.request.player_input,
            room_context=self.request.room_context,
            visual_context=self.request.visual_context,
            # ... other context fields
        )
        prompt = context.compile()  # Uses your prompts.py - UNCHANGED

        # 3. Call LLM (Chatforge)
        response = self.llm_service.generate_siluet_answer(prompt)

        # 4. Save messages (Chatforge models via repository)
        self.message_repo.add_user_message(self.chat_id, self.request.player_input)
        self.message_repo.add_ai_message(
            self.chat_id,
            response,
            generation_data={
                "prompt": prompt,
                "model": self.llm_service.default_model,
                "request": self.request.dict(),
            },
        )

        return SiluetResponse(response=response)
```

---


---

## Phase 8: Cleanup

### Step 8.1: Update Dependencies

**File:** `pyproject.toml`

```toml
[project]
dependencies = [
    # REMOVE this
    # "llmservice",  # No longer needed

    # Chatforge is installed via pip install -e, so no need to list it here
    # But ensure these are present (Chatforge needs them):
    "sqlalchemy>=2.0",
    "langchain-core",
    "langchain-openai",
    "pydantic-settings",
    # ...
]
```

### Step 8.2: Remove Unused Files

```bash
# Old model files (now using Chatforge)
rm -f src/db/models/chat.py
rm -f src/db/models/message.py
rm -f src/db/models/base.py

# Old LLM operations model (replaced by AgentRun)
rm -f src/db/models/llm_operations.py
```

### Step 8.3: Update Imports Throughout Codebase

Search and replace any remaining imports:

```bash
# Find files still importing old models
grep -r "from src.db.models.chat import" src/
grep -r "from src.db.models.message import" src/
grep -r "from llmservice import" src/
```

---

## Phase 9: Testing

### Step 9.1: Unit Tests

```bash
# Run existing tests (update if needed)
pytest tests/unit/ -v
```

### Step 9.2: Integration Test

```python
# tests/integration/test_chatforge_integration.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from chatforge.adapters.storage.models.models import Base, Chat, Message
from src.db.models.user import User
from src.db.repositories.chat_repository import ChatRepository
from src.db.repositories.message_repository import MessageRepository


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_create_chat_with_participants(session):
    repo = ChatRepository(session)
    chat = repo.create(user_id=1, title="Test Chat")

    assert chat.id is not None
    assert len(chat.participants) == 2  # Owner + AI


def test_message_flow(session):
    chat_repo = ChatRepository(session)
    msg_repo = MessageRepository(session)

    chat = chat_repo.create(user_id=1)

    msg_repo.add_user_message(chat.id, "Hello")
    msg_repo.add_ai_message(chat.id, "Hi there!", generation_data={"prompt": "test"})

    history = msg_repo.get_history(chat.id)
    assert len(history) == 2
    assert history[0].role == "user"
    assert history[1].role == "assistant"
    assert history[1].generation_request_data == {"prompt": "test"}
```

### Step 9.3: Manual Testing

```bash
# Start the server
uvicorn src.main:app --reload

# Test endpoints
curl -X POST http://localhost:8000/api/chat/create \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"

curl -X POST http://localhost:8000/api/chat/1/message \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"player_input": "Hello Silüet"}'
```

---

## Verification Checklist

### Installation
- [ ] Chatforge installed via `pip install -e .`
- [ ] `from chatforge...` imports work

### Models
- [ ] `User` model uses Chatforge's `Base`
- [ ] `src/db/models/__init__.py` exports Chatforge models + User
- [ ] Old model files deleted

### Database
- [ ] `create_glassmind_db.py` creates all tables
- [ ] *(Skip if fresh DB)* Migration script works
- [ ] Participants created for each chat

### Repositories
- [ ] `ChatRepository` creates Participants
- [ ] `MessageRepository` uses `generation_request_data`
- [ ] `UserRepository` unchanged

### LLM Service
- [ ] Uses `get_llm()` from Chatforge
- [ ] Returns correct response format

### Services
- [ ] `SiluetService` uses repositories
- [ ] Prompt building unchanged (`StepContext.compile()`)
- [ ] Messages saved with correct fields

### Tests
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing successful

---

## Rollback Plan

If something goes wrong:

```bash
# 1. Restore old database
cp old_glassmind.db glassmind.db

# 2. Revert code changes
git checkout -- src/

# 3. Uninstall Chatforge
pip uninstall chatforge
```

---

## Summary

| Phase | Files Changed | Time |
|-------|---------------|------|
| 1. Install Chatforge | (pip install) | 5 min |
| 2. Models | `user.py`, `__init__.py` | 20 min |
| 3. DB Script | `create_glassmind_db.py` | 15 min |
| 4. Repositories | `chat_repository.py`, `message_repository.py` | 45 min |
| 5. LLM Service | `myllmservice.py` | 20 min |
| 6. Services | `siluet_service.py` | 30 min |
| 7. Migration | *(SKIP if fresh DB)* | 0 min |
| 8. Cleanup | Remove old files | 15 min |
| 9. Testing | Tests | 60 min |
| **Total** | | **~3.5 hours** |

---

## Final Directory Structure

```
ChamberProtocolAI/src/
├── db/
│   ├── models/
│   │   ├── __init__.py         # Imports from chatforge
│   │   └── user.py             # Your auth model (uses Chatforge Base)
│   ├── repositories/
│   │   ├── chat_repository.py  # Updated
│   │   ├── message_repository.py  # Updated
│   │   └── user_repository.py  # Unchanged
│   └── scripts/
│       └── create_glassmind_db.py  # Updated
├── impl/
│   ├── myllmservice.py         # Uses chatforge.services.llm.factory
│   ├── prompts.py              # Unchanged
│   └── services/
│       └── chat/
│           └── siluet_service.py  # Updated
└── schemas.py                  # StepContext unchanged
```

---

## What You Keep (Unchanged)

```
src/impl/prompts.py          # Your prompt templates
src/schemas.py               # StepContext dataclass
src/auth/                    # JWT middleware
src/api/                     # FastAPI routes (structure)
src/db/repositories/user_repository.py  # User auth queries
```

## What Chatforge Gives You

```
✅ Multi-provider LLM support (OpenAI, Anthropic, Bedrock)
✅ Soft delete for chats and messages
✅ Participant model for multi-user support
✅ generation_request_data for debugging prompts
✅ Attachment model for file uploads (future)
✅ ToolCall model for tool tracking (future)
✅ AgentRun model for cost tracking (future)
✅ Feedback fields (thumbs_up/down)
```

---

## Import Reference

All Chatforge imports use the package directly:

```python
# Models
from chatforge.adapters.storage.models.models import (
    Base,
    Chat,
    Participant,
    Message,
    Attachment,
    ToolCall,
    AgentRun,
)

# LLM Factory
from chatforge.services.llm.factory import get_llm

# Config (if needed)
from chatforge.config import llm_config
```
