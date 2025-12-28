# ChamberProtocolAI + Chatforge Integration

How Chatforge replaces ChamberProtocolAI's LLM calls and storage.

---

## What ChamberProtocolAI Currently Has

### LLM Layer

```
llmservice (pip package)
    └── BaseLLMService
            └── MyLLMService (src/impl/myllmservice.py)
                    ├── generate_ai_answer()
                    └── generate_siluet_answer()
```

### Storage Layer

```
SQLAlchemy
    ├── Chat (id, user_id, settings, created_at)
    ├── Message (id, chat_id, user_id, message, siluet_request_data, ...)
    └── User (id, email, password_hash, ...)
```

### Database Creation Script

```python
# src/db/scripts/create_glassmind_db.py (CURRENT)
from src.db.models import Base, Chat, Message, User
from sqlalchemy import create_engine

def create_database():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
```

---

## What Changes

### 1. Database Models → Use Chatforge's

```python
# src/db/models/__init__.py (NEW)
from chatforge.adapters.storage.models.models import (
    Base,           # Shared SQLAlchemy Base
    Chat,           # Replaces your Chat
    Participant,    # NEW - links users/AI to chats
    Message,        # Replaces your Message
    Attachment,     # NEW - file uploads
    ToolCall,       # NEW - tool execution tracking
    AgentRun,       # NEW - LLM cost tracking
)
from .user import User  # Keep your auth model

__all__ = ["Base", "Chat", "Participant", "Message", "Attachment",
           "ToolCall", "AgentRun", "User"]
```

### 2. User Model → Keep Yours (Shares Base)

```python
# src/db/models/user.py (KEEP - but use Chatforge's Base)
from chatforge.adapters.storage.models.models import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON

class User(Base):
    """Your auth model - Chatforge doesn't handle authentication."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    # Game-specific fields
    subscription_tier = Column(String(20), default="free")
    game_preferences = Column(JSON, default=dict)
```

### 3. Database Creation Script → Updated

```python
# src/db/scripts/create_glassmind_db.py (NEW)
"""
Creates database with Chatforge models + User model.
Run once to set up fresh database.
"""
from sqlalchemy import create_engine
from chatforge.adapters.storage.models.models import Base
# Import User to register it with the shared Base
from src.db.models.user import User

DATABASE_URL = "sqlite:///glassmind.db"  # or your actual URL

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

**Key point:** Both Chatforge models AND your User model use the same `Base`, so `Base.metadata.create_all()` creates everything.

### 4. LLM Service → Use Chatforge

```python
# src/impl/myllmservice.py (NEW - simplified)
from chatforge.services.llm.factory import get_llm
from langchain_core.messages import HumanMessage

class MyLLMService:
    def __init__(self, default_model="gpt-4o-mini"):
        self.default_model = default_model
        self._llm_cache = {}

    def _get_llm(self, model: str = None):
        model = model or self.default_model
        if model not in self._llm_cache:
            self._llm_cache[model] = get_llm(provider="openai", model_name=model)
        return self._llm_cache[model]

    def generate_siluet_answer(self, prompt: str, model: str = None) -> str:
        llm = self._get_llm(model)
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
```

### 5. SiluetService → Updated

```python
# src/impl/services/chat/siluet_service.py (UPDATED)
from chatforge.adapters.storage.models.models import Message, Participant
from src.impl.myllmservice import MyLLMService
from src.schemas import StepContext  # Your prompt builder - unchanged

class SiluetService:
    def __init__(self, user_id: int, chat_id: int, request, session):
        self.llm_service = MyLLMService()
        self.session = session
        self.user_id = user_id
        self.chat_id = chat_id
        self.request = request

    def _process_request(self):
        # 1. Fetch history (Chatforge models)
        messages = (
            self.session.query(Message)
            .filter(Message.chat_id == self.chat_id)
            .filter(Message.deleted_at.is_(None))
            .order_by(Message.created_at.desc())
            .limit(20)
            .all()
        )
        conversation_memory_str = "\n".join([
            f"{m.sender_name}: {m.content}" for m in reversed(messages)
        ])

        # 2. Build prompt (YOUR code - unchanged)
        context = StepContext(
            conversation_memory=conversation_memory_str,
            player_input=self.request.player_input,
            room_context=json.dumps(self.request.room_context.dict()),
            visual_context=json.dumps(self.request.visual_context.dict()),
        )
        full_prompt = context.compile()

        # 3. Call LLM (Chatforge)
        llm_response = self.llm_service.generate_siluet_answer(full_prompt)

        # 4. Save messages (Chatforge models)
        player_msg = Message(
            chat_id=self.chat_id,
            sender_name="Player",
            role="user",
            content=self.request.player_input,
        )
        self.session.add(player_msg)

        ai_msg = Message(
            chat_id=self.chat_id,
            sender_name="Silüet",
            role="assistant",
            content=llm_response,
            generation_request_data={
                "prompt": full_prompt,
                "model": self.llm_service.default_model,
                "request": self.request.dict(),
            }
        )
        self.session.add(ai_msg)
        self.session.commit()

        return SiluetResponse(response=llm_response)
```

---

## Schema Mapping

```
ChamberProtocol (OLD)              Chatforge (NEW)
─────────────────                  ─────────
Chat                               Chat (enhanced)
├── id                             ├── id
├── user_id ─────────────────────► │   (via Participant with role='owner')
├── created_at                     ├── created_at
└── settings                       ├── settings
                                   ├── title (NEW)
                                   ├── system_prompt (NEW)
                                   ├── metadata_ (NEW)
                                   ├── updated_at (NEW)
                                   └── deleted_at (soft delete, NEW)

Message                            Message (enhanced)
├── id                             ├── id
├── chat_id                        ├── chat_id
├── user_id ─────────────────────► ├── participant_id
├── user_name ───────────────────► ├── sender_name
├── user_type ───────────────────► ├── role (user/assistant/system/tool)
├── message                        ├── content
├── message_format                 ├── content_format
├── message_type                   ├── message_type
├── timestamp                      ├── created_at
├── siluet_request_data ─────────► ├── generation_request_data (AI only)
└── step_context                   └── (not used - disregard)

(none)                             Participant (NEW)
                                   ├── id
                                   ├── chat_id
                                   ├── participant_type (user/assistant)
                                   ├── external_id → User.id
                                   ├── display_name
                                   └── role_in_chat (owner/member)

User (KEEP)                        (not in Chatforge - by design)
├── id
├── email
├── password_hash
└── ...auth fields
```

---

## What Stays in ChamberProtocolAI

| Component | Why It Stays |
|-----------|--------------|
| `src/db/models/user.py` | Your authentication - Chatforge doesn't own users |
| `src/impl/prompts.py` | Your prompt templates - game domain logic |
| `src/schemas.py` (`StepContext`) | Your prompt builder - just string templating |
| `SiluetRequest/Response` | Your API schemas |
| JWT auth middleware | Your security layer |

---

## What Chatforge Provides

| Component | Benefit |
|-----------|---------|
| `Chat` model | Soft delete, metadata, settings |
| `Message` model | `generation_request_data` for debugging, feedback fields |
| `Participant` model | Multi-user chats, link to your User table |
| `Attachment` model | File uploads in chat (future) |
| `ToolCall` model | Tool execution tracking (future) |
| `AgentRun` model | LLM cost tracking, debugging |
| `get_llm()` | Multi-provider support (OpenAI, Anthropic, Bedrock) |

---

## Migration Script

```python
# scripts/migrate_to_chatforge.py
"""
One-time migration from old ChamberProtocol schema to Chatforge schema.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from chatforge.adapters.storage.models.models import Base, Chat, Participant, Message
from src.db.models.user import User

OLD_DB = "sqlite:///old_glassmind.db"
NEW_DB = "sqlite:///glassmind.db"

def migrate():
    old_engine = create_engine(OLD_DB)
    new_engine = create_engine(NEW_DB)

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
            display_name=user.display_name,
            is_active=user.is_active,
        )
        new_session.add(new_user)

    # 2. Migrate chats + create participants
    old_chats = old_session.execute(text("SELECT * FROM chats")).fetchall()
    for chat in old_chats:
        new_chat = Chat(
            id=chat.id,
            settings=chat.settings if hasattr(chat, 'settings') else {},
            created_at=chat.created_at,
        )
        new_session.add(new_chat)
        new_session.flush()

        # Create owner participant (links chat to user)
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
            sender_name=msg.user_name if hasattr(msg, 'user_name') else None,
            role=msg.user_type if hasattr(msg, 'user_type') else "user",
            content=msg.message,
            content_format=getattr(msg, 'message_format', 'text'),
            message_type=getattr(msg, 'message_type', 'user'),
            generation_request_data=msg.siluet_request_data if msg.user_type == "assistant" else None,
            created_at=msg.timestamp if hasattr(msg, 'timestamp') else None,
        )
        new_session.add(new_msg)

    new_session.commit()
    print(f"Migrated {len(old_users)} users, {len(old_chats)} chats, {len(old_messages)} messages")

if __name__ == "__main__":
    migrate()
```

---

## Directory Structure After Migration

```
ChamberProtocolAI/src/
├── db/
│   ├── models/
│   │   ├── __init__.py      # Imports from Chatforge + User
│   │   └── user.py          # Your auth model (uses Chatforge's Base)
│   ├── repositories/
│   │   ├── chat_repository.py    # Updated for Chatforge models
│   │   ├── message_repository.py # Updated for Chatforge models
│   │   └── user_repository.py    # Keep as-is
│   └── scripts/
│       └── create_glassmind_db.py  # Uses Base.metadata.create_all()
├── impl/
│   ├── myllmservice.py      # Uses Chatforge's get_llm()
│   ├── prompts.py           # Unchanged - your templates
│   └── services/
│       └── chat/
│           └── siluet_service.py  # Uses Chatforge models
└── schemas.py               # StepContext unchanged
```

---

## Summary

| Before | After |
|--------|-------|
| `llmservice.BaseLLMService` | `chatforge.get_llm()` |
| Custom Chat model | `chatforge.models.Chat` |
| Custom Message model | `chatforge.models.Message` |
| `siluet_request_data` field | `Message.generation_request_data` |
| No participant concept | `chatforge.models.Participant` |
| `Base.metadata.create_all()` with your models | Same call, creates Chatforge + User tables |
