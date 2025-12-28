# ChamberProtocolAI Repository Changes

How ChamberProtocolAI's repository layer should change when using Chatforge models.

---

## Current Repository Structure

```
ChamberProtocolAI/src/db/repositories/
├── chat_repository.py      # Chat CRUD
├── message_repository.py   # Message CRUD
└── user_repository.py      # User auth (keep as-is)
```

---

## Should We Keep Repositories?

**Yes.** Repositories provide:

| Benefit | Example |
|---------|---------|
| Query abstraction | `get_history()` vs raw SQLAlchemy |
| Authorization logic | `user_owns_chat()` |
| Business helpers | `get_history_as_string()` for prompts |
| Testability | Mock repositories in unit tests |
| Single responsibility | Services focus on logic, not queries |

---

## Updated Repositories

### chat_repository.py

```python
# src/db/repositories/chat_repository.py
from chatforge.adapters.storage.models.models import Chat, Participant
from sqlalchemy.orm import Session


class ChatRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        user_id: int,
        title: str = None,
        settings: dict = None,
    ) -> Chat:
        """
        Create a new chat with the user as owner.
        Also creates Participant records for user and AI.
        """
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
        """Get chat by ID, or None if not found."""
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
        """Check if user is the owner of a chat. Used for authorization."""
        return (
            self.session.query(Participant)
            .filter(Participant.chat_id == chat_id)
            .filter(Participant.external_id == str(user_id))
            .filter(Participant.role_in_chat == "owner")
            .first()
        ) is not None

    def soft_delete(self, chat_id: int) -> bool:
        """Soft delete a chat. Returns True if found and deleted."""
        from datetime import datetime, timezone

        chat = self.get_by_id(chat_id)
        if chat:
            chat.deleted_at = datetime.now(timezone.utc)
            self.session.commit()
            return True
        return False

    def update_settings(self, chat_id: int, settings: dict) -> Chat | None:
        """Update chat settings."""
        chat = self.get_by_id(chat_id)
        if chat:
            chat.settings = {**chat.settings, **settings}
            self.session.commit()
        return chat
```

### message_repository.py

```python
# src/db/repositories/message_repository.py
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
        """
        Add a message from the AI.

        Args:
            chat_id: The chat this message belongs to
            content: The AI's response text
            generation_data: Debug data (prompt, model, etc.)
            sender_name: Display name for the AI
        """
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
        """
        Get recent messages for a chat, oldest first.
        Excludes soft-deleted messages.
        """
        messages = (
            self.session.query(Message)
            .filter(Message.chat_id == chat_id)
            .filter(Message.deleted_at.is_(None))
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(messages))  # Oldest first

    def get_history_as_string(self, chat_id: int, limit: int = 20) -> str:
        """
        Get history formatted for prompt building.
        Returns: "Player: hello\nSilüet: hi there\n..."
        """
        messages = self.get_history(chat_id, limit)
        return "\n".join(f"{m.sender_name}: {m.content}" for m in messages)

    def get_history_for_llm(self, chat_id: int, limit: int = 20) -> list[dict]:
        """
        Get history in LLM-ready format.
        Returns: [{"role": "user", "content": "..."}, ...]
        """
        messages = self.get_history(chat_id, limit)
        return [{"role": m.role, "content": m.content} for m in messages]

    def get_last_message(self, chat_id: int) -> Message | None:
        """Get the most recent message in a chat."""
        return (
            self.session.query(Message)
            .filter(Message.chat_id == chat_id)
            .filter(Message.deleted_at.is_(None))
            .order_by(Message.created_at.desc())
            .first()
        )

    def count_messages(self, chat_id: int) -> int:
        """Count total messages in a chat."""
        return (
            self.session.query(Message)
            .filter(Message.chat_id == chat_id)
            .filter(Message.deleted_at.is_(None))
            .count()
        )

    def soft_delete(self, message_id: int) -> bool:
        """Soft delete a message."""
        msg = self.session.query(Message).filter(Message.id == message_id).first()
        if msg:
            msg.deleted_at = datetime.now(timezone.utc)
            self.session.commit()
            return True
        return False
```

### user_repository.py (unchanged)

```python
# src/db/repositories/user_repository.py
# This stays the same - it uses your User model, not Chatforge's
from src.db.models.user import User
from sqlalchemy.orm import Session


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, user_id: int) -> User | None:
        return self.session.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> User | None:
        return self.session.query(User).filter(User.email == email).first()

    def create(self, email: str, password_hash: str, display_name: str = None) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            display_name=display_name,
        )
        self.session.add(user)
        self.session.commit()
        return user

    # ... rest of your auth methods
```

---

## Usage in Services

```python
# src/impl/services/chat/siluet_service.py
from src.db.repositories.chat_repository import ChatRepository
from src.db.repositories.message_repository import MessageRepository
from src.impl.myllmservice import MyLLMService
from src.schemas import StepContext


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

        # 2. Build prompt (your domain logic)
        context = StepContext(
            conversation_memory=history_str,
            player_input=self.request.player_input,
            room_context=self.request.room_context,
            visual_context=self.request.visual_context,
        )
        prompt = context.compile()

        # 3. Call LLM
        response = self.llm_service.generate_siluet_answer(prompt)

        # 4. Save messages (repository handles details)
        self.message_repo.add_user_message(self.chat_id, self.request.player_input)
        self.message_repo.add_ai_message(
            self.chat_id,
            response,
            generation_data={
                "prompt": prompt,
                "model": "gpt-4o-mini",
                "request": self.request.dict(),
            },
        )

        return SiluetResponse(response=response)
```

---

## What Changed vs What Stayed

| Repository | Changes |
|------------|---------|
| `ChatRepository` | Uses `Chat` + `Participant` from Chatforge. Creates both when making a chat. |
| `MessageRepository` | Uses `Message` from Chatforge. Uses `generation_request_data` instead of `siluet_request_data`. |
| `UserRepository` | **No changes** - uses your `User` model |

---

## New Helper Methods

These are new methods you get by using Chatforge models:

| Method | What it does |
|--------|--------------|
| `get_history_for_llm()` | Returns `[{"role": "user", "content": "..."}]` format |
| `soft_delete()` | Uses `deleted_at` instead of hard delete |
| `chat.settings` | JSON field for chat configuration |
| `message.generation_request_data` | Store full prompt for debugging |

---

## Testing Repositories

```python
# tests/test_message_repository.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from chatforge.adapters.storage.models.models import Base, Chat, Message
from src.db.repositories.message_repository import MessageRepository


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create a test chat
    chat = Chat(id=1, settings={})
    session.add(chat)
    session.commit()

    yield session
    session.close()


def test_add_and_get_messages(session):
    repo = MessageRepository(session)

    repo.add_user_message(chat_id=1, content="Hello")
    repo.add_ai_message(chat_id=1, content="Hi there!")

    history = repo.get_history(chat_id=1)

    assert len(history) == 2
    assert history[0].role == "user"
    assert history[1].role == "assistant"


def test_get_history_as_string(session):
    repo = MessageRepository(session)

    repo.add_user_message(chat_id=1, content="Hello")
    repo.add_ai_message(chat_id=1, content="Hi!")

    result = repo.get_history_as_string(chat_id=1)

    assert result == "Player: Hello\nSilüet: Hi!"
```

---

## Summary

| Aspect | Decision |
|--------|----------|
| Keep repository pattern? | **Yes** - good abstraction |
| What changes? | Import Chatforge models instead of custom ones |
| New concepts? | `Participant` for user/AI identity, `generation_request_data` for debug |
| UserRepository? | **Unchanged** - uses your own User model |
