# Storage Architecture Analysis

**Date**: 2024-12-26
**Status**: Proposed
**Decision**: Pending

---

## Problem Analysis

### Core Challenges

**Challenge 1: Schema Design**
Current schema is minimal (2 tables). Should it be expanded to include proper user, chat, message entities with richer fields?

**Challenge 2: Integration Problem**
Apps using chatforge often have their own database with existing user tables, schemas, and ORM models. How does chatforge fit in?

### Current Schema

```sql
-- conversations table
CREATE TABLE conversations (
    conversation_id TEXT PRIMARY KEY,
    user_id TEXT,
    platform TEXT DEFAULT 'api',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata TEXT DEFAULT '{}'
);

-- messages table
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
);
```

### Key Stakeholders

| Stakeholder | Needs |
|-------------|-------|
| **Greenfield apps** | Quick start, sensible defaults, no config |
| **Existing apps** | Integration with their schema, no duplication |
| **Enterprise** | Multi-tenant, audit, compliance, FK integrity |
| **Microservices** | Loose coupling, eventual consistency |

### Critical Tension

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   EASE OF USE  ◄──────────────────────►  FLEXIBILITY        │
│                                                             │
│   "Just works"          vs          "Fits my schema"        │
│   Default tables                    Custom tables           │
│   Quick start                       Full control            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Scenario Analysis

### Scenario A: Greenfield App
```
New app → Uses chatforge → Happy with default schema → Done
```
**Current chatforge handles this well ✅**

### Scenario B: Existing App with Users Table
```python
# App already has:
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String)
    org_id = Column(Integer, ForeignKey("orgs.id"))

# Wants to add chat, but:
# - Don't want duplicate user data
# - Want FK from messages → users
# - Want to query: "all messages from org X"
```
**Current chatforge: ❌ user_id is just a string, no FK integrity**

### Scenario C: Enterprise Multi-Tenant SaaS
```python
# Complex schema:
# - tenants table (isolation boundary)
# - orgs table (billing unit)
# - users table (with org_id, tenant_id)
# - audit_logs table (compliance)

# Requirements:
# - Messages must have tenant_id for RLS
# - Audit every message save/delete
# - Custom retention policies per tenant
```
**Current chatforge: ❌ No tenant awareness, no audit hooks**

### Scenario D: Microservices
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ User Service│     │ Chat Service│     │ Analytics   │
│             │     │ (chatforge) │     │ Service     │
│ owns users  │     │ owns chats  │     │ needs data  │
└─────────────┘     └─────────────┘     └─────────────┘
      │                    │                    │
      └────── No direct FK ─────────┘          │
                           │                    │
                           └─── Events? ────────┘
```
**Current chatforge: ⚠️ Works, but no event system for sync**

---

## Solution Options

### Option 1: Improve Default Schema (Minimal Change)

Keep current approach but enhance the schema:

```sql
-- Enhanced schema
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    external_id TEXT UNIQUE,          -- App's user ID
    display_name TEXT,
    email TEXT,
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    title TEXT,
    platform TEXT DEFAULT 'api',
    status TEXT DEFAULT 'active',     -- active, archived, deleted
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT                   -- Soft delete
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT REFERENCES conversations(id),
    user_id TEXT REFERENCES users(id),
    role TEXT NOT NULL,
    content_type TEXT DEFAULT 'text', -- text, image, file, tool_call
    content TEXT NOT NULL,
    parent_id INTEGER REFERENCES messages(id),  -- Threading
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    edited_at TEXT,
    deleted_at TEXT                   -- Soft delete
);

CREATE TABLE attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER REFERENCES messages(id),
    file_type TEXT,
    file_name TEXT,
    file_url TEXT,
    file_size INTEGER,
    created_at TEXT NOT NULL
);
```

**Pros:**
- ✅ Better data model
- ✅ Soft deletes for compliance
- ✅ Message threading support
- ✅ Attachment support
- ✅ Backward compatible (mostly)

**Cons:**
- ❌ Still chatforge's schema, not app's
- ❌ Still no FK to app's user table
- ❌ Data duplication if app has users

**Verdict:** Good for greenfield, doesn't solve integration problem.

---

### Option 2: Custom Adapter Pattern (Current, Document Better)

The `StoragePort` interface already supports this! Apps implement their own adapter:

```python
# App implements StoragePort with their own schema
class MyAppStorageAdapter(StoragePort):
    def __init__(self, db_session, user_model, message_model):
        self.db = db_session
        self.User = user_model
        self.Message = message_model

    async def save_message(
        self,
        conversation_id: str,
        message: MessageRecord,
        user_id: str | None = None,
    ) -> None:
        # Map chatforge's MessageRecord to app's model
        db_message = self.Message(
            thread_id=conversation_id,      # App uses "thread_id"
            author_id=user_id,              # FK to app's users
            body=message.content,           # App uses "body"
            message_type=message.role,
            tool_data=message.metadata.get("tool_calls"),
            created_at=message.created_at,
        )
        self.db.add(db_message)
        await self.db.commit()

    async def get_conversation(
        self,
        conversation_id: str,
        limit: int = 50,
    ) -> list[MessageRecord]:
        # Query app's tables, return chatforge's MessageRecord
        db_messages = await self.db.query(self.Message)\
            .filter(self.Message.thread_id == conversation_id)\
            .order_by(self.Message.created_at.desc())\
            .limit(limit)\
            .all()

        return [
            MessageRecord(
                content=m.body,
                role=m.message_type,
                created_at=m.created_at,
                metadata={"tool_calls": m.tool_data} if m.tool_data else {},
            )
            for m in reversed(db_messages)
        ]
```

**Pros:**
- ✅ Full flexibility
- ✅ App uses own tables
- ✅ FK integrity with app's schema
- ✅ No data duplication
- ✅ Works with any ORM

**Cons:**
- ❌ Requires implementing full StoragePort (6 methods)
- ❌ Easy to make mistakes
- ❌ No out-of-box experience
- ❌ Boilerplate for each app

**Verdict:** Most flexible, but high friction for developers.

---

### Option 3: Adapter Base Classes (Reduce Boilerplate)

Provide ORM-specific base classes that reduce boilerplate:

```python
# chatforge/adapters/storage/sqlalchemy_base.py

from sqlalchemy.ext.asyncio import AsyncSession

class SQLAlchemyStorageAdapter(StoragePort):
    """
    Base adapter for SQLAlchemy. Subclass and configure table mappings.

    Example:
        class MyStorageAdapter(SQLAlchemyStorageAdapter):
            class Config:
                conversation_model = MyConversation
                message_model = MyMessage

                # Column mappings (chatforge name -> your column name)
                conversation_mapping = {
                    "conversation_id": "id",
                    "user_id": "owner_id",
                    "updated_at": "last_activity",
                }
                message_mapping = {
                    "content": "body",
                    "role": "sender_type",
                    "conversation_id": "thread_id",
                }
    """

    class Config:
        conversation_model = None  # Override in subclass
        message_model = None
        conversation_mapping = {}
        message_mapping = {}

    def __init__(self, session: AsyncSession):
        self.session = session
        self._validate_config()

    async def save_message(self, conversation_id, message, user_id=None):
        # Generic implementation using Config mappings
        model = self.Config.message_model
        mapping = self.Config.message_mapping

        data = {
            mapping.get("content", "content"): message.content,
            mapping.get("role", "role"): message.role,
            mapping.get("conversation_id", "conversation_id"): conversation_id,
            mapping.get("created_at", "created_at"): message.created_at,
        }

        instance = model(**data)
        self.session.add(instance)
        await self.session.commit()
```

**Usage:**
```python
# App just provides configuration, not full implementation
class MyStorageAdapter(SQLAlchemyStorageAdapter):
    class Config:
        conversation_model = MyThread
        message_model = MyMessage
        message_mapping = {
            "content": "body",
            "role": "sender_type",
            "conversation_id": "thread_id",
        }

# Use it
storage = MyStorageAdapter(session=db_session)
```

**Pros:**
- ✅ Much less boilerplate than Option 2
- ✅ Declarative configuration
- ✅ Works with existing models
- ✅ Can override specific methods if needed

**Cons:**
- ❌ Need base class per ORM (SQLAlchemy, Django, Tortoise)
- ❌ Mapping config can get complex
- ❌ Edge cases may need custom methods

**Verdict:** Good balance of flexibility and ease of use.

---

### Option 4: User Resolver Interface (Hybrid)

Chatforge owns messages/conversations, but user info comes from app:

```python
# chatforge/ports/user_resolver.py

class UserResolver(ABC):
    """Interface for resolving user information from app's user system."""

    @abstractmethod
    async def get_user(self, user_id: str) -> UserInfo | None:
        """Get user info by ID."""

    @abstractmethod
    async def validate_user(self, user_id: str) -> bool:
        """Check if user exists and is active."""

    @abstractmethod
    async def get_user_display_name(self, user_id: str) -> str:
        """Get display name for UI."""

@dataclass
class UserInfo:
    id: str
    display_name: str
    email: str | None = None
    metadata: dict = field(default_factory=dict)
```

**App implements:**
```python
class MyAppUserResolver(UserResolver):
    def __init__(self, db_session):
        self.db = db_session

    async def get_user(self, user_id: str) -> UserInfo | None:
        user = await self.db.query(User).get(user_id)
        if not user:
            return None
        return UserInfo(
            id=str(user.id),
            display_name=user.name,
            email=user.email,
        )

    async def validate_user(self, user_id: str) -> bool:
        user = await self.db.query(User).get(user_id)
        return user is not None and user.is_active
```

**Chatforge uses it:**
```python
storage = SQLiteStorageAdapter(
    database_path="./chat.db",
    user_resolver=MyAppUserResolver(db_session),  # Inject!
)

# Before saving message, validate user exists
async def save_message(self, conv_id, message, user_id):
    if user_id and not await self.user_resolver.validate_user(user_id):
        raise ValueError(f"User {user_id} not found")
    # ... save message
```

**Pros:**
- ✅ User data stays in app's domain
- ✅ Chatforge doesn't duplicate user data
- ✅ Loose coupling
- ✅ Works for microservices (resolver can call user service API)

**Cons:**
- ❌ Still no FK integrity (user_id is string in chatforge tables)
- ❌ Can't do JOIN queries across user + messages
- ❌ N+1 problem when loading user info for messages

**Verdict:** Good for microservices, less ideal for monoliths.

---

### Option 5: Event Hooks (Eventual Consistency)

Chatforge emits events, apps sync to their schema:

```python
# chatforge/events.py

class StorageEvents:
    """Event hooks for storage operations."""

    def __init__(self):
        self._listeners = defaultdict(list)

    def on(self, event: str):
        """Decorator to register event listener."""
        def decorator(fn):
            self._listeners[event].append(fn)
            return fn
        return decorator

    async def emit(self, event: str, data: dict):
        """Emit event to all listeners."""
        for listener in self._listeners[event]:
            await listener(data)

# Events emitted:
# - message_saved(conversation_id, message, user_id)
# - message_deleted(conversation_id, message_id)
# - conversation_created(conversation_id, user_id)
# - conversation_deleted(conversation_id)
```

**App subscribes:**
```python
from chatforge.events import storage_events

@storage_events.on("message_saved")
async def sync_to_analytics(data):
    """Sync message to analytics database."""
    await analytics_db.insert({
        "event": "chat_message",
        "user_id": data["user_id"],
        "conversation_id": data["conversation_id"],
        "timestamp": data["message"].created_at,
        "word_count": len(data["message"].content.split()),
    })

@storage_events.on("message_saved")
async def update_user_activity(data):
    """Update user's last activity timestamp."""
    await app_db.users.update(
        {"id": data["user_id"]},
        {"last_chat_at": datetime.now()}
    )
```

**Pros:**
- ✅ Decoupled - chatforge doesn't know about app
- ✅ Multiple listeners per event
- ✅ Good for analytics, audit, sync
- ✅ Works for microservices (emit to message queue)

**Cons:**
- ❌ Eventual consistency (not immediate)
- ❌ Data duplication (chatforge + app tables)
- ❌ Error handling complexity
- ❌ Debugging across systems is hard

**Verdict:** Excellent for cross-cutting concerns, not primary storage.

---

### Option 6: No Default Tables (BYOT - Bring Your Own Tables)

Chatforge provides logic only, NO default tables:

```python
# Chatforge requires you to define storage
from chatforge.storage import AbstractStorage

# You MUST implement
class MyStorage(AbstractStorage):
    ...

# No built-in SQLite/InMemory adapters
# Framework, not batteries-included
```

**Pros:**
- ✅ Forces proper integration
- ✅ No "wrong" default to migrate away from

**Cons:**
- ❌ Terrible onboarding experience
- ❌ Can't just `pip install chatforge` and go
- ❌ Every user writes boilerplate

**Verdict:** Too extreme, kills adoption.

---

## Recommended Architecture

### Layered Flexibility Model

```
┌─────────────────────────────────────────────────────────────────┐
│                     LAYER 4: Event Hooks                        │
│         (Optional: Sync to analytics, audit, etc.)              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 3: ORM Base Classes                    │
│    SQLAlchemyStorageAdapter, DjangoStorageAdapter, etc.         │
│         (For apps with existing schemas)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 2: StoragePort                         │
│         Abstract interface (already exists!)                    │
│      Custom adapters implement this directly                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  LAYER 1: Built-in Adapters                     │
│        InMemoryStorageAdapter, SQLiteStorageAdapter             │
│              (Quick start, sensible defaults)                   │
└─────────────────────────────────────────────────────────────────┘
```

### User Journey by Complexity

| App Type | Recommended Approach |
|----------|----------------------|
| **Prototype/Demo** | `InMemoryStorageAdapter` |
| **Simple app** | `SQLiteStorageAdapter` (improved schema) |
| **App with existing DB** | `SQLAlchemyStorageAdapter` base + config |
| **Enterprise** | Custom `StoragePort` implementation |
| **Microservices** | `StoragePort` + `UserResolver` + Event hooks |

---

## Implementation Roadmap

### Phase 1: Improve Default Schema (Quick Win)
- Add soft deletes (`deleted_at`)
- Add message threading (`parent_id`)
- Add `content_type` field
- Better indexes
- Update `SQLiteStorageAdapter`

**Effort**: 1-2 days

### Phase 2: Add UserResolver Interface
- Define `UserResolver` port
- Optional injection into storage adapters
- Validate users before saving messages
- Resolve user info for display

**Effort**: 1 day

### Phase 3: Add ORM Base Classes
- `SQLAlchemyStorageAdapter` base class
- Declarative column mapping config
- Document with examples

**Effort**: 2-3 days

### Phase 4: Add Event Hooks
- Define event types
- Add emit calls to storage adapters
- Support sync and async listeners
- Optional message queue integration

**Effort**: 1-2 days

### Phase 5: Django/Other ORM Support
- `DjangoStorageAdapter` base class
- Integration with Django User model
- Django management commands for cleanup

**Effort**: 2-3 days

---

## Decision Matrix

| Approach | Ease of Use | Flexibility | FK Integrity | Effort |
|----------|-------------|-------------|--------------|--------|
| **Improve Default Schema** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ❌ | Low |
| **Custom Adapter (current)** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | High |
| **ORM Base Classes** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ | Medium |
| **User Resolver** | ⭐⭐⭐ | ⭐⭐⭐ | ❌ | Low |
| **Event Hooks** | ⭐⭐⭐ | ⭐⭐⭐⭐ | N/A | Low |
| **BYOT (No defaults)** | ⭐ | ⭐⭐⭐⭐⭐ | ✅ | N/A |

---

## Final Recommendations

### For Question 1 (Schema Improvement)

**Yes, improve the default schema:**
- Add soft deletes (`deleted_at`)
- Add threading (`parent_id`)
- Add `content_type` field
- Keep it simple - don't over-engineer

The default is for simple apps; complex apps use custom adapters.

### For Question 2 (Integration)

**Implement the Layered Flexibility Model:**

1. **Keep `StoragePort`** as the core abstraction (it's correct!)
2. **Add `SQLAlchemyStorageAdapter` base class** for easy integration
3. **Add `UserResolver` interface** for user validation
4. **Add event hooks** for cross-cutting concerns
5. **Document patterns** for enterprise integration

### Key Insight

> The current design is actually good - `StoragePort` IS the integration point.
> What's missing is:
> - Helper base classes to reduce boilerplate
> - Clear documentation of integration patterns
> - Event hooks for advanced use cases

---

## Example: Complete Integration

```python
# 1. App defines their models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String)

class ChatThread(Base):
    __tablename__ = "chat_threads"
    id = Column(String, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True)
    thread_id = Column(String, ForeignKey("chat_threads.id"))
    author_id = Column(Integer, ForeignKey("users.id"))
    body = Column(Text)
    sender_type = Column(String)  # "user" or "assistant"
    created_at = Column(DateTime)

# 2. App configures chatforge adapter
class MyStorageAdapter(SQLAlchemyStorageAdapter):
    class Config:
        conversation_model = ChatThread
        message_model = ChatMessage
        conversation_mapping = {
            "conversation_id": "id",
            "user_id": "owner_id",
        }
        message_mapping = {
            "content": "body",
            "role": "sender_type",
            "conversation_id": "thread_id",
        }

# 3. App implements user resolver
class MyUserResolver(UserResolver):
    async def validate_user(self, user_id: str) -> bool:
        user = await db.query(User).get(int(user_id))
        return user is not None

# 4. Use it
storage = MyStorageAdapter(
    session=db_session,
    user_resolver=MyUserResolver(),
)

agent = ReActAgent(llm=llm, tools=[], storage=storage)
```

This approach gives apps full control while reducing boilerplate.
