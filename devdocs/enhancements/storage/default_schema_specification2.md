# Chatforge Default Schema Specification v2

## Overview

This document defines the refined database schema for chatforge's storage system, featuring a **participant-centric architecture** that:

1. **Decouples chat participation from authentication** - Host apps own users, chatforge owns participants
2. **Supports multi-party chats** - Multiple humans and/or AIs in one conversation
3. **Treats AI as first-class citizen** - AI assistants are participants, not just responders
4. **Uses snapshots for historical accuracy** - Message sender names are captured at send time

---

## Core Concepts

### Participant vs User

| Concept | Owned By | Purpose |
|---------|----------|---------|
| **User** | Host app | Authentication, profiles, billing |
| **Participant** | Chatforge | Chat membership, roles, settings |

A participant references a host app's user (or AI) via `external_id` without chatforge owning user management.

### Snapshot Fields

A **snapshot** is a copy of a value captured at a specific moment:

```python
# When message is created:
message.sender_name = participant.display_name  # Copy, not link

# Later, if participant changes name:
participant.display_name = "New Name"
# message.sender_name still holds the old name (historical accuracy)
```

This is like an invoice storing the price at purchase time, not linking to current price.

---

## Schema Diagram

```
┌─────────────────────────┐
│         chats           │
├─────────────────────────┤
│ id (PK)                 │
│ title                   │
│ chat_type               │  ← 'direct', 'group', 'ai_workspace'
│ settings (JSON)         │
│ created_at              │
│ updated_at              │
│ deleted_at              │
└───────────┬─────────────┘
            │
            │ 1:N
            ▼
┌─────────────────────────────────┐
│         participants            │
├─────────────────────────────────┤
│ id (PK)                         │
│ chat_id (FK)                    │
│ participant_type                │  ← 'user', 'assistant', 'agent', 'bot'
│ external_id                     │  ← Reference to host system
│ display_name                    │  ← Current name (mutable)
│ role_in_chat                    │  ← 'owner', 'admin', 'member', 'observer'
│ settings (JSON)                 │
│ joined_at                       │
│ left_at                         │
│ is_active                       │
└───────────┬─────────────────────┘
            │
            │ 1:N
            ▼
┌─────────────────────────────────┐
│          messages               │
├─────────────────────────────────┤
│ id (PK)                         │
│ chat_id (FK)                    │
│ participant_id (FK)             │  ← Who sent it (entity)
│ sender_name                     │  ← Snapshot of display_name at send time
│ role                            │  ← LLM role: 'user', 'assistant', 'system', 'tool'
│ message_type                    │  ← 'user', 'generated', 'fixed', 'edited'
│ content                         │
│ content_format                  │
│ transcription                   │  ← Original voice input if applicable
│ parent_id (FK, self-ref)        │
│ token_count                     │
│ attachment_id (FK, nullable)    │  ← Reference to attachments table
│ thumbs_up_count                 │
│ thumbs_down_count               │
│ text_feedback                   │
│ metadata (JSON)                 │
│ created_at                      │
│ deleted_at                      │
└───────────┬─────────────────────┘
            │
    ┌───────┴───────┐
    │               │
    │ 1:N           │ N:1
    ▼               ▼
┌───────────────┐  ┌─────────────────────────┐
│  tool_calls   │  │       attachments       │
├───────────────┤  ├─────────────────────────┤
│ id (PK)       │  │ id (PK)                 │
│ message_id    │  │ file_name               │
│ run_id        │  │ file_type               │
│ tool_name     │  │ file_size               │
│ input_params  │  │ storage_path            │
│ output_data   │  │ storage_type            │
│ status        │  │ thumbnail_path          │
│ ...           │  │ uploaded_by (FK)        │
└───────────────┘  │ metadata (JSON)         │
                   │ created_at              │
                   └─────────────────────────┘

┌─────────────────────────────────┐
│         agent_runs              │
├─────────────────────────────────┤
│ id (PK)                         │
│ chat_id (FK)                    │
│ participant_id (FK)             │  ← Which AI participant ran
│ trigger_message_id (FK)         │
│ status                          │
│ total_steps                     │
│ total_tool_calls                │
│ token_usage (JSON)              │
│ cost                            │
│ started_at                      │
│ completed_at                    │
└─────────────────────────────────┘
```

---

## Table Definitions

### 1. `chats`

Conversation container. Ownership is determined by participants with `role_in_chat='owner'`.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK | Unique identifier |
| `title` | String(255) | Nullable | Display name |
| `chat_type` | String(20) | DEFAULT 'direct' | 'direct', 'group', 'ai_workspace' |
| `settings` | JSON | DEFAULT {} | Model config, system prompt, etc. |
| `metadata` | JSON | DEFAULT {} | App-specific data |
| `created_at` | DateTime | NOT NULL | Creation timestamp |
| `updated_at` | DateTime | NOT NULL | Last activity |
| `deleted_at` | DateTime | Nullable | Soft delete |

**Note:** No `user_id` - ownership is via participants.

---

### 2. `participants`

A participant in a chat - can be human, AI, agent, or bot.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK | Unique identifier |
| `chat_id` | Integer | FK → chats.id | Which chat |
| `participant_type` | String(20) | NOT NULL | 'user', 'assistant', 'agent', 'bot', 'system' |
| `external_id` | String(128) | NOT NULL | Reference to host system |
| `display_name` | String(100) | NOT NULL | Current display name |
| `avatar_url` | String(500) | Nullable | Profile image |
| `role_in_chat` | String(20) | DEFAULT 'member' | 'owner', 'admin', 'member', 'observer' |
| `settings` | JSON | DEFAULT {} | Participant-specific settings |
| `joined_at` | DateTime | NOT NULL | When joined |
| `left_at` | DateTime | Nullable | When left (null = still active) |
| `is_active` | Boolean | DEFAULT true | Currently participating |
| `metadata` | JSON | DEFAULT {} | App-specific data |

**Indexes:**
- `idx_participants_chat_id` on `chat_id`
- `idx_participants_external_id` on `external_id`
- `idx_participants_chat_external` on `(chat_id, external_id)` UNIQUE

**participant_type values:**

| Type | Description | Example external_id |
|------|-------------|---------------------|
| `user` | Human user | Host app's user ID: `"user-123"` |
| `assistant` | LLM AI assistant | Model identifier: `"gpt-4o"` |
| `agent` | Autonomous AI agent | Agent name: `"research-agent"` |
| `bot` | Non-LLM bot/integration | Bot identifier: `"slack-notifier"` |
| `system` | System-generated | `"system"` |

**role_in_chat values:**

| Role | Permissions |
|------|-------------|
| `owner` | Full control, can delete chat |
| `admin` | Can manage participants |
| `member` | Can send messages |
| `observer` | Read-only access |

---

### 3. `messages`

Individual message in a conversation.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK | Unique identifier |
| `chat_id` | Integer | FK → chats.id | Parent chat |
| `participant_id` | Integer | FK → participants.id | Who sent it |
| `sender_name` | String(100) | NOT NULL | Snapshot of display_name at send time |
| `role` | String(20) | NOT NULL | LLM role: 'user', 'assistant', 'system', 'tool' |
| `message_type` | String(20) | DEFAULT 'generated' | 'user', 'generated', 'fixed', 'edited' |
| `content` | Text | NOT NULL | Message content |
| `content_format` | String(20) | DEFAULT 'text' | 'text', 'markdown', 'html' |
| `transcription` | Text | Nullable | Original voice transcription |
| `parent_id` | Integer | FK → messages.id | For threading |
| `token_count` | Integer | Nullable | Token count |
| `attachment_id` | Integer | FK → attachments.id, Nullable | File attachment |
| `thumbs_up_count` | Integer | DEFAULT 0 | Positive feedback count |
| `thumbs_down_count` | Integer | DEFAULT 0 | Negative feedback count |
| `text_feedback` | Text | Nullable | Written feedback on message |
| `metadata` | JSON | DEFAULT {} | Additional data |
| `created_at` | DateTime | NOT NULL | When sent |
| `deleted_at` | DateTime | Nullable | Soft delete |

**message_type values:**

| Type | Description |
|------|-------------|
| `user` | Direct user input |
| `generated` | AI-generated response |
| `fixed` | Static/template message |
| `edited` | User-edited AI response |

**Key design decisions:**

1. **`participant_id`** - Links to the participant entity (for joins, queries)
2. **`sender_name`** - Snapshot of `participant.display_name` (for historical accuracy)
3. **`role`** - LLM conversation role (also used for UI styling)
4. **Feedback fields** - `thumbs_up_count`, `thumbs_down_count`, `text_feedback` for RLHF and quality tracking

**No `sender_type`** - When needed, join to `participant.participant_type`

---

### 4. `attachments`

File attachments for messages.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK | Unique identifier |
| `file_name` | String(255) | NOT NULL | Original file name |
| `file_type` | String(50) | NOT NULL | MIME type |
| `file_size` | Integer | NOT NULL | Size in bytes |
| `storage_path` | String(500) | NOT NULL | Path/URL to stored file |
| `storage_type` | String(20) | DEFAULT 'local' | 'local', 's3', 'gcs', 'azure' |
| `thumbnail_path` | String(500) | Nullable | Thumbnail for images/videos |
| `metadata` | JSON | DEFAULT {} | Dimensions, duration, etc. |
| `uploaded_by` | Integer | FK → participants.id | Who uploaded |
| `created_at` | DateTime | NOT NULL | Upload timestamp |

**Note:** A message can have one attachment via `message.attachment_id`. For multiple attachments per message, use a join table or store attachment IDs in `message.metadata`.

---

### 6. `tool_calls`

Tool invocation tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK | Unique identifier |
| `message_id` | Integer | FK → messages.id | Triggering message |
| `run_id` | Integer | FK → agent_runs.id, Nullable | Part of which run |
| `tool_name` | String(100) | NOT NULL | Tool name |
| `tool_version` | String(20) | Nullable | Version if tracked |
| `input_params` | JSON | NOT NULL | Parameters |
| `output_data` | JSON | Nullable | Result |
| `status` | String(20) | DEFAULT 'pending' | Status |
| `error_message` | Text | Nullable | Error details |
| `execution_time_ms` | Integer | Nullable | Duration |
| `retry_count` | Integer | DEFAULT 0 | Retry attempts |
| `created_at` | DateTime | NOT NULL | When called |
| `completed_at` | DateTime | Nullable | When finished |

---

### 7. `agent_runs`

Agent execution session tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK | Unique identifier |
| `chat_id` | Integer | FK → chats.id | Which chat |
| `participant_id` | Integer | FK → participants.id | Which AI participant |
| `trigger_message_id` | Integer | FK → messages.id, Nullable | Triggering message |
| `agent_name` | String(100) | NOT NULL | Agent name |
| `agent_version` | String(20) | Nullable | Version |
| `status` | String(20) | DEFAULT 'running' | Status |
| `input_data` | JSON | Nullable | Initial input |
| `final_result` | JSON | Nullable | Final output |
| `error_message` | Text | Nullable | Error details |
| `total_steps` | Integer | DEFAULT 0 | Reasoning steps |
| `total_tool_calls` | Integer | DEFAULT 0 | Tool calls made |
| `token_usage` | JSON | DEFAULT {} | Token breakdown |
| `cost` | Decimal(10,6) | Nullable | USD cost |
| `started_at` | DateTime | NOT NULL | Start time |
| `completed_at` | DateTime | Nullable | End time |
| `metadata` | JSON | DEFAULT {} | App-specific |

---

## SQLAlchemy Models

```python
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean,
    ForeignKey, JSON, Numeric, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def _utc_now():
    return datetime.now(timezone.utc)


class Chat(Base):
    __tablename__ = 'chats'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=True)
    chat_type = Column(String(20), default='direct')
    settings = Column(JSON, default=dict)
    metadata_ = Column('metadata', JSON, default=dict)
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    participants = relationship('Participant', back_populates='chat', cascade='all, delete-orphan')
    messages = relationship('Message', back_populates='chat', cascade='all, delete-orphan')
    agent_runs = relationship('AgentRun', back_populates='chat', cascade='all, delete-orphan')

    def get_owner(self):
        """Get the participant with owner role."""
        for p in self.participants:
            if p.role_in_chat == 'owner' and p.is_active:
                return p
        return None


class Participant(Base):
    """
    A participant in a chat - human, AI, agent, or bot.

    Decouples chat participation from authentication:
    - Host app owns users (auth, profiles)
    - Chatforge owns participants (membership, roles)
    """
    __tablename__ = 'participants'

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chats.id', ondelete='CASCADE'), nullable=False)

    # What type of participant
    participant_type = Column(String(20), nullable=False)
    # 'user', 'assistant', 'agent', 'bot', 'system'

    # Reference to external system (host app's user ID or AI identifier)
    external_id = Column(String(128), nullable=False)

    # Display info
    display_name = Column(String(100), nullable=False)
    avatar_url = Column(String(500), nullable=True)

    # Role in this chat
    role_in_chat = Column(String(20), default='member')
    # 'owner', 'admin', 'member', 'observer'

    # Participant-specific settings
    settings = Column(JSON, default=dict)
    # For AI: {"model": "gpt-4o", "temperature": 0.7}
    # For users: {"notifications": true}

    # Lifecycle
    joined_at = Column(DateTime, default=_utc_now)
    left_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    metadata_ = Column('metadata', JSON, default=dict)

    # Relationships
    chat = relationship('Chat', back_populates='participants')
    messages = relationship('Message', back_populates='participant')
    agent_runs = relationship('AgentRun', back_populates='participant')

    __table_args__ = (
        Index('idx_participants_chat_id', 'chat_id'),
        Index('idx_participants_external_id', 'external_id'),
        Index('idx_participants_chat_external', 'chat_id', 'external_id', unique=True),
    )

    @property
    def is_human(self) -> bool:
        return self.participant_type == 'user'

    @property
    def is_ai(self) -> bool:
        return self.participant_type in ('assistant', 'agent')


class Attachment(Base):
    """File attachment for messages."""
    __tablename__ = 'attachments'

    id = Column(Integer, primary_key=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # MIME type
    file_size = Column(Integer, nullable=False)  # Bytes
    storage_path = Column(String(500), nullable=False)
    storage_type = Column(String(20), default='local')  # 'local', 's3', 'gcs', 'azure'
    thumbnail_path = Column(String(500), nullable=True)
    metadata_ = Column('metadata', JSON, default=dict)
    uploaded_by = Column(Integer, ForeignKey('participants.id'), nullable=True)
    created_at = Column(DateTime, default=_utc_now)

    # Relationships
    uploader = relationship('Participant')
    messages = relationship('Message', back_populates='attachment')


class Message(Base):
    """
    An immutable record of something said in a chat.

    The sender_name is a snapshot of participant.display_name at send time,
    like an email From header - part of the message, not a reference.
    """
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chats.id', ondelete='CASCADE'), nullable=False)
    parent_id = Column(Integer, ForeignKey('messages.id', ondelete='SET NULL'), nullable=True)

    # Who sent it
    participant_id = Column(Integer, ForeignKey('participants.id', ondelete='CASCADE'), nullable=False)
    sender_name = Column(String(100), nullable=False)  # Snapshot at send time

    # Content
    role = Column(String(20), nullable=False)  # LLM role: 'user', 'assistant', 'system', 'tool'
    message_type = Column(String(20), default='generated')  # 'user', 'generated', 'fixed', 'edited'
    content = Column(Text, nullable=False)
    content_format = Column(String(20), default='text')
    transcription = Column(Text, nullable=True)  # Voice transcription

    # Attachment
    attachment_id = Column(Integer, ForeignKey('attachments.id', ondelete='SET NULL'), nullable=True)

    # Feedback
    thumbs_up_count = Column(Integer, default=0)
    thumbs_down_count = Column(Integer, default=0)
    text_feedback = Column(Text, nullable=True)

    # Metadata
    token_count = Column(Integer, nullable=True)
    metadata_ = Column('metadata', JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=_utc_now)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    chat = relationship('Chat', back_populates='messages')
    participant = relationship('Participant', back_populates='messages')
    parent = relationship('Message', remote_side=[id], backref='replies')
    attachment = relationship('Attachment', back_populates='messages')
    tool_calls = relationship('ToolCall', back_populates='message', cascade='all, delete-orphan')

    __table_args__ = (
        Index('idx_messages_chat_id', 'chat_id'),
        Index('idx_messages_participant_id', 'participant_id'),
        Index('idx_messages_created_at', 'created_at'),
    )

    def to_llm_format(self) -> dict:
        """Convert to format for LLM API."""
        return {"role": self.role, "content": self.content}


class ToolCall(Base):
    __tablename__ = 'tool_calls'

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey('messages.id', ondelete='CASCADE'), nullable=False)
    run_id = Column(Integer, ForeignKey('agent_runs.id', ondelete='SET NULL'), nullable=True)

    tool_name = Column(String(100), nullable=False)
    tool_version = Column(String(20), nullable=True)
    input_params = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=True)

    status = Column(String(20), default='pending')
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    retry_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=_utc_now)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    message = relationship('Message', back_populates='tool_calls')
    agent_run = relationship('AgentRun', back_populates='tool_calls')

    __table_args__ = (
        Index('idx_tool_calls_message_id', 'message_id'),
        Index('idx_tool_calls_run_id', 'run_id'),
        Index('idx_tool_calls_status', 'status'),
    )


class AgentRun(Base):
    __tablename__ = 'agent_runs'

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chats.id', ondelete='CASCADE'), nullable=False)
    participant_id = Column(Integer, ForeignKey('participants.id', ondelete='SET NULL'), nullable=True)
    trigger_message_id = Column(Integer, ForeignKey('messages.id', ondelete='SET NULL'), nullable=True)

    agent_name = Column(String(100), nullable=False)
    agent_version = Column(String(20), nullable=True)
    status = Column(String(20), default='running')

    input_data = Column(JSON, nullable=True)
    final_result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    total_steps = Column(Integer, default=0)
    total_tool_calls = Column(Integer, default=0)
    token_usage = Column(JSON, default=dict)
    cost = Column(Numeric(10, 6), nullable=True)

    started_at = Column(DateTime, default=_utc_now)
    completed_at = Column(DateTime, nullable=True)
    metadata_ = Column('metadata', JSON, default=dict)

    # Relationships
    chat = relationship('Chat', back_populates='agent_runs')
    participant = relationship('Participant', back_populates='agent_runs')
    tool_calls = relationship('ToolCall', back_populates='agent_run')

    __table_args__ = (
        Index('idx_agent_runs_chat_id', 'chat_id'),
        Index('idx_agent_runs_participant_id', 'participant_id'),
        Index('idx_agent_runs_status', 'status'),
    )
```

---

## Usage Examples

### Example 1: Simple 1:1 Chat with AI

```python
# Create chat
chat = Chat(title="My Assistant", chat_type="direct")
session.add(chat)
session.flush()

# Add human participant
human = Participant(
    chat_id=chat.id,
    participant_type="user",
    external_id=str(current_user.id),  # Host app's user ID
    display_name=current_user.name,
    role_in_chat="owner"
)

# Add AI participant
ai = Participant(
    chat_id=chat.id,
    participant_type="assistant",
    external_id="gpt-4o",
    display_name="Assistant",
    role_in_chat="member",
    settings={"model": "gpt-4o", "temperature": 0.7}
)

session.add_all([human, ai])
session.commit()
```

### Example 2: Sending a Message

```python
# Human sends a message
message = Message(
    chat_id=chat.id,
    participant_id=human.id,
    sender_name=human.display_name,  # Snapshot!
    role="user",
    content="Hello, how are you?"
)
session.add(message)

# AI responds
response = Message(
    chat_id=chat.id,
    participant_id=ai.id,
    sender_name=ai.display_name,  # Snapshot!
    role="assistant",
    content="I'm doing well, thank you!"
)
session.add(response)
session.commit()
```

### Example 3: Group Chat with Multiple Users + AI

```python
chat = Chat(title="Project Discussion", chat_type="group")

# Multiple humans
alice = Participant(chat_id=chat.id, participant_type="user",
                    external_id="user-alice", display_name="Alice",
                    role_in_chat="owner")

bob = Participant(chat_id=chat.id, participant_type="user",
                  external_id="user-bob", display_name="Bob",
                  role_in_chat="member")

# AI assistant for the group
assistant = Participant(chat_id=chat.id, participant_type="assistant",
                        external_id="gpt-4o", display_name="Project AI",
                        role_in_chat="member")

session.add_all([chat, alice, bob, assistant])
```

### Example 4: Multi-Agent Conversation

```python
chat = Chat(title="Research Analysis", chat_type="ai_workspace")

# Researcher agent
researcher = Participant(
    chat_id=chat.id,
    participant_type="agent",
    external_id="researcher-agent",
    display_name="Researcher",
    role_in_chat="owner",
    settings={"model": "claude-3-opus", "tools": ["web_search", "arxiv"]}
)

# Critic agent
critic = Participant(
    chat_id=chat.id,
    participant_type="agent",
    external_id="critic-agent",
    display_name="Critic",
    role_in_chat="member",
    settings={"model": "gpt-4o", "system_prompt": "Challenge assumptions"}
)

session.add_all([chat, researcher, critic])
```

### Example 5: Agent Handoff

```python
# AI couldn't help, escalate to human
ai_participant.is_active = False
ai_participant.left_at = datetime.now(timezone.utc)

# Human agent joins
human_agent = Participant(
    chat_id=chat.id,
    participant_type="user",
    external_id="support-agent-456",
    display_name="Sarah (Support)",
    role_in_chat="admin"
)
session.add(human_agent)
session.commit()
```

---

## Common Queries

### Get active participants in a chat

```python
participants = session.query(Participant).filter(
    Participant.chat_id == chat_id,
    Participant.is_active == True
).all()
```

### Get conversation history with sender info

```python
messages = session.query(Message).filter(
    Message.chat_id == chat_id,
    Message.deleted_at.is_(None)
).order_by(Message.created_at).all()

for msg in messages:
    # Uses snapshot (historical accuracy)
    print(f"{msg.sender_name}: {msg.content}")

    # Or join for current name
    print(f"{msg.participant.display_name}: {msg.content}")
```

### Get chat owner

```python
owner = session.query(Participant).filter(
    Participant.chat_id == chat_id,
    Participant.role_in_chat == "owner",
    Participant.is_active == True
).first()
```

### Get all chats for a user (by external_id)

```python
chats = session.query(Chat).join(Participant).filter(
    Participant.external_id == user_id,
    Participant.is_active == True,
    Chat.deleted_at.is_(None)
).all()
```

---

## Key Design Decisions

### 1. No User Table

Chatforge doesn't own user management. Host apps reference their users via `external_id`.

### 2. Participants for Ownership

Instead of `chat.user_id`, ownership is determined by `participant.role_in_chat = 'owner'`.

### 3. Snapshot for sender_name

`message.sender_name` captures the participant's name at send time. This provides historical accuracy without complex joins.

### 4. Role vs Participant Type

| Field | Purpose |
|-------|---------|
| `participant.participant_type` | What KIND of entity (user, assistant, agent, bot) |
| `message.role` | LLM conversation role (user, assistant, system, tool) |

They often align but are conceptually different.

### 5. Soft Deletes

`deleted_at` fields enable data recovery and audit trails without permanent deletion.

---

## Migration from v1 Schema

If migrating from the original schema (with `user_id` on chats/messages):

```sql
-- 1. Create participants table
CREATE TABLE participants (...);

-- 2. Migrate chat owners to participants
INSERT INTO participants (chat_id, participant_type, external_id, display_name, role_in_chat)
SELECT id, 'user', user_id, user_id, 'owner' FROM chats WHERE user_id IS NOT NULL;

-- 3. Migrate message senders to participants (deduplicated)
INSERT INTO participants (chat_id, participant_type, external_id, display_name, role_in_chat)
SELECT DISTINCT chat_id,
       CASE WHEN role = 'user' THEN 'user' ELSE 'assistant' END,
       user_id, user_id, 'member'
FROM messages
WHERE NOT EXISTS (
    SELECT 1 FROM participants p
    WHERE p.chat_id = messages.chat_id AND p.external_id = messages.user_id
);

-- 4. Add participant_id to messages
ALTER TABLE messages ADD COLUMN participant_id INTEGER REFERENCES participants(id);

-- 5. Populate participant_id
UPDATE messages SET participant_id = (
    SELECT p.id FROM participants p
    WHERE p.chat_id = messages.chat_id AND p.external_id = messages.user_id
);

-- 6. Add sender_name (copy from participant for historical data)
ALTER TABLE messages ADD COLUMN sender_name VARCHAR(100);
UPDATE messages SET sender_name = (
    SELECT p.display_name FROM participants p WHERE p.id = messages.participant_id
);

-- 7. Drop old columns (after verification)
ALTER TABLE chats DROP COLUMN user_id;
ALTER TABLE messages DROP COLUMN user_id;
```

---

## Summary

**7 tables:**

```
chats
├── participants (who's in the chat)
│   └── attachments (files uploaded by participants)
├── messages (what they said)
│   ├── tool_calls (tools used)
│   └── attachments (files attached to messages)
└── agent_runs (AI execution sessions)
    └── tool_calls (tools used in run)
```

**This schema provides:**

| Feature | How |
|---------|-----|
| Multi-user chats | Multiple participants per chat |
| Multi-AI chats | AI assistants are participants |
| Ownership | `role_in_chat = 'owner'` |
| Historical accuracy | `sender_name` snapshot |
| Host app integration | `external_id` references |
| Audit trail | `joined_at`, `left_at`, `deleted_at` |
| Flexibility | JSON settings per participant |
| Voice support | `transcription` field |
| File attachments | `attachments` table |
| User feedback | `thumbs_up_count`, `thumbs_down_count`, `text_feedback` |
| Message types | `message_type`: user, generated, fixed, edited |
| Tool tracking | `tool_calls` table |
| Agent tracking | `agent_runs` table with costs |
