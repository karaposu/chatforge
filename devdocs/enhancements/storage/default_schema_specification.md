# Chatforge Default Schema Specification

## Overview

This document defines the default database schema for chatforge's storage system. The schema is designed to be:

1. **Comprehensive** - Covers chats, messages, tool calls, and agent runs
2. **Framework-agnostic** - No authentication logic, works with any user system
3. **Observable** - Full tracking of agentic operations for debugging and analytics
4. **Flexible** - JSON fields for extensibility without schema changes

## Design Principles

| Principle | Description |
|-----------|-------------|
| **No User Table** | Host apps own user management. Chatforge only stores `user_id` as reference |
| **Denormalized User Info** | Store `user_name` snapshot in messages for self-contained display |
| **Soft Deletes** | `deleted_at` fields for data recovery and audit trails |
| **JSON Flexibility** | `metadata` and `settings` fields for app-specific extensions |
| **Timestamps** | `created_at` and `updated_at` on all tables |

---

## Schema Diagram

```
┌─────────────────┐       ┌─────────────────┐
│     chats       │       │   agent_runs    │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │───┐   │ id (PK)         │
│ user_id         │   │   │ chat_id (FK)────│───┐
│ title           │   │   │ agent_name      │   │
│ settings (JSON) │   │   │ status          │   │
│ created_at      │   │   │ started_at      │   │
│ updated_at      │   │   │ completed_at    │   │
│ deleted_at      │   │   │ token_usage     │   │
└─────────────────┘   │   │ cost            │   │
                      │   │ final_result    │   │
                      │   │ error_message   │   │
                      │   └─────────────────┘   │
                      │                         │
                      ▼                         │
┌─────────────────────────────────┐             │
│            messages             │             │
├─────────────────────────────────┤             │
│ id (PK)                         │             │
│ chat_id (FK)────────────────────│─────────────┘
│ parent_id (FK, self-ref)        │
│ user_id                         │
│ user_name (snapshot)            │
│ role                            │
│ content                         │
│ content_format                  │
│ message_type                    │
│ transcription                   │
│ metadata (JSON)                 │
│ created_at                      │
│ deleted_at                      │
└─────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────┐
│          tool_calls             │
├─────────────────────────────────┤
│ id (PK)                         │
│ message_id (FK)                 │
│ run_id (FK, nullable)───────────│──► agent_runs
│ tool_name                       │
│ input_params (JSON)             │
│ output_data (JSON)              │
│ status                          │
│ error_message                   │
│ execution_time_ms               │
│ created_at                      │
└─────────────────────────────────┘
```

---

## Table Definitions

### 1. `chats`

The conversation container. One chat has many messages.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, Auto-increment | Unique identifier |
| `user_id` | String(64) | NOT NULL, Indexed | Owner of the chat (external reference) |
| `title` | String(255) | Nullable | Display name for the chat |
| `system_prompt` | Text | Nullable | Default system prompt for this chat |
| `settings` | JSON | DEFAULT {} | Flexible settings (model, temperature, etc.) |
| `metadata` | JSON | DEFAULT {} | App-specific data |
| `created_at` | DateTime | NOT NULL, DEFAULT now | Creation timestamp |
| `updated_at` | DateTime | NOT NULL, DEFAULT now | Last modification |
| `deleted_at` | DateTime | Nullable | Soft delete timestamp |

**Indexes:**
- `idx_chats_user_id` on `user_id`
- `idx_chats_created_at` on `created_at`
- `idx_chats_deleted_at` on `deleted_at` (for filtering active chats)

**Example `settings` JSON:**
```json
{
  "model": "gpt-4o",
  "temperature": 0.7,
  "max_tokens": 4096,
  "tags": ["support", "billing"]
}
```

---

### 2. `messages`

Individual messages within a chat. Supports threading via `parent_id`.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, Auto-increment | Unique identifier |
| `chat_id` | Integer | FK → chats.id, ON DELETE CASCADE | Parent chat |
| `parent_id` | Integer | FK → messages.id, Nullable | For threaded replies |
| `user_id` | String(64) | NOT NULL | Who sent this message |
| `user_name` | String(100) | Nullable | Display name snapshot at time of message |
| `role` | String(20) | NOT NULL | 'user', 'assistant', 'system', 'tool' |
| `content` | Text | NOT NULL | The message content |
| `content_format` | String(20) | DEFAULT 'text' | 'text', 'markdown', 'html', 'json' |
| `message_type` | String(20) | DEFAULT 'generated' | 'user', 'generated', 'fixed', 'edited' |
| `transcription` | Text | Nullable | Original voice transcription if applicable |
| `token_count` | Integer | Nullable | Token count for this message |
| `metadata` | JSON | DEFAULT {} | App-specific data (attachments, reactions, etc.) |
| `created_at` | DateTime | NOT NULL, DEFAULT now | When message was sent |
| `deleted_at` | DateTime | Nullable | Soft delete timestamp |

**Indexes:**
- `idx_messages_chat_id` on `chat_id`
- `idx_messages_parent_id` on `parent_id`
- `idx_messages_user_id` on `user_id`
- `idx_messages_created_at` on `created_at`
- `idx_messages_role` on `role`

**Role Values:**
| Role | Description |
|------|-------------|
| `user` | Human user input |
| `assistant` | AI response |
| `system` | System prompt or instructions |
| `tool` | Tool call result |

**Message Type Values:**
| Type | Description |
|------|-------------|
| `user` | Direct user input |
| `generated` | AI-generated response |
| `fixed` | Static/template message |
| `edited` | User-edited AI response |

**Example `metadata` JSON:**
```json
{
  "attachments": [
    {"type": "image", "url": "/uploads/img123.png", "name": "screenshot.png"}
  ],
  "reactions": {"thumbs_up": 2},
  "edit_history": [{"content": "original text", "edited_at": "2025-01-15T10:00:00Z"}]
}
```

---

### 3. `tool_calls`

Tracks every tool/function invocation for observability.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, Auto-increment | Unique identifier |
| `message_id` | Integer | FK → messages.id, ON DELETE CASCADE | Which message triggered this |
| `run_id` | Integer | FK → agent_runs.id, Nullable | Part of which agent run (if any) |
| `tool_name` | String(100) | NOT NULL | Name of the tool called |
| `tool_version` | String(20) | Nullable | Tool version if tracked |
| `input_params` | JSON | NOT NULL | Input parameters passed to tool |
| `output_data` | JSON | Nullable | Result returned by tool |
| `status` | String(20) | NOT NULL, DEFAULT 'pending' | 'pending', 'running', 'success', 'error', 'timeout' |
| `error_message` | Text | Nullable | Error details if failed |
| `execution_time_ms` | Integer | Nullable | How long the tool took |
| `retry_count` | Integer | DEFAULT 0 | Number of retries attempted |
| `created_at` | DateTime | NOT NULL, DEFAULT now | When tool was called |
| `completed_at` | DateTime | Nullable | When tool finished |

**Indexes:**
- `idx_tool_calls_message_id` on `message_id`
- `idx_tool_calls_run_id` on `run_id`
- `idx_tool_calls_tool_name` on `tool_name`
- `idx_tool_calls_status` on `status`
- `idx_tool_calls_created_at` on `created_at`

**Status Values:**
| Status | Description |
|--------|-------------|
| `pending` | Queued, not yet started |
| `running` | Currently executing |
| `success` | Completed successfully |
| `error` | Failed with error |
| `timeout` | Exceeded time limit |
| `cancelled` | Manually cancelled |

**Example record:**
```json
{
  "id": 42,
  "message_id": 156,
  "run_id": 12,
  "tool_name": "web_search",
  "input_params": {"query": "chatforge python framework"},
  "output_data": {"results": [{"title": "...", "url": "..."}]},
  "status": "success",
  "execution_time_ms": 1250
}
```

---

### 4. `agent_runs`

Tracks complete agent execution sessions for debugging and analytics.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, Auto-increment | Unique identifier |
| `chat_id` | Integer | FK → chats.id, ON DELETE CASCADE | Which chat this run belongs to |
| `trigger_message_id` | Integer | FK → messages.id, Nullable | Message that triggered this run |
| `agent_name` | String(100) | NOT NULL | Name/type of agent |
| `agent_version` | String(20) | Nullable | Agent version if tracked |
| `status` | String(20) | NOT NULL, DEFAULT 'running' | 'running', 'completed', 'failed', 'cancelled' |
| `input_data` | JSON | Nullable | Initial input to the agent |
| `final_result` | JSON | Nullable | Final output from the agent |
| `error_message` | Text | Nullable | Error details if failed |
| `total_steps` | Integer | DEFAULT 0 | Number of steps/iterations |
| `total_tool_calls` | Integer | DEFAULT 0 | Number of tool calls made |
| `token_usage` | JSON | DEFAULT {} | Token consumption breakdown |
| `cost` | Decimal(10,6) | Nullable | Total cost in USD |
| `started_at` | DateTime | NOT NULL, DEFAULT now | When run started |
| `completed_at` | DateTime | Nullable | When run finished |
| `metadata` | JSON | DEFAULT {} | App-specific data |

**Indexes:**
- `idx_agent_runs_chat_id` on `chat_id`
- `idx_agent_runs_agent_name` on `agent_name`
- `idx_agent_runs_status` on `status`
- `idx_agent_runs_started_at` on `started_at`

**Example `token_usage` JSON:**
```json
{
  "prompt_tokens": 1520,
  "completion_tokens": 890,
  "total_tokens": 2410,
  "by_model": {
    "gpt-4o": {"prompt": 1200, "completion": 800},
    "gpt-4o-mini": {"prompt": 320, "completion": 90}
  }
}
```

---

## SQLAlchemy Models

```python
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey,
    JSON, Numeric, Index
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class Chat(Base):
    __tablename__ = 'chats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    system_prompt = Column(Text, nullable=True)
    settings = Column(JSON, default=dict, nullable=False)
    metadata_ = Column('metadata', JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    messages = relationship('Message', back_populates='chat', cascade='all, delete-orphan')
    agent_runs = relationship('AgentRun', back_populates='chat', cascade='all, delete-orphan')

    __table_args__ = (
        Index('idx_chats_created_at', 'created_at'),
        Index('idx_chats_deleted_at', 'deleted_at'),
    )


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, ForeignKey('chats.id', ondelete='CASCADE'), nullable=False)
    parent_id = Column(Integer, ForeignKey('messages.id', ondelete='SET NULL'), nullable=True)
    user_id = Column(String(64), nullable=False)
    user_name = Column(String(100), nullable=True)
    role = Column(String(20), nullable=False)  # user, assistant, system, tool
    content = Column(Text, nullable=False)
    content_format = Column(String(20), default='text', nullable=False)
    message_type = Column(String(20), default='generated', nullable=False)
    transcription = Column(Text, nullable=True)
    token_count = Column(Integer, nullable=True)
    metadata_ = Column('metadata', JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    chat = relationship('Chat', back_populates='messages')
    parent = relationship('Message', remote_side=[id], backref='replies')
    tool_calls = relationship('ToolCall', back_populates='message', cascade='all, delete-orphan')

    __table_args__ = (
        Index('idx_messages_chat_id', 'chat_id'),
        Index('idx_messages_parent_id', 'parent_id'),
        Index('idx_messages_user_id', 'user_id'),
        Index('idx_messages_created_at', 'created_at'),
        Index('idx_messages_role', 'role'),
    )


class ToolCall(Base):
    __tablename__ = 'tool_calls'

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey('messages.id', ondelete='CASCADE'), nullable=False)
    run_id = Column(Integer, ForeignKey('agent_runs.id', ondelete='SET NULL'), nullable=True)
    tool_name = Column(String(100), nullable=False)
    tool_version = Column(String(20), nullable=True)
    input_params = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=True)
    status = Column(String(20), default='pending', nullable=False)
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    message = relationship('Message', back_populates='tool_calls')
    agent_run = relationship('AgentRun', back_populates='tool_calls')

    __table_args__ = (
        Index('idx_tool_calls_message_id', 'message_id'),
        Index('idx_tool_calls_run_id', 'run_id'),
        Index('idx_tool_calls_tool_name', 'tool_name'),
        Index('idx_tool_calls_status', 'status'),
        Index('idx_tool_calls_created_at', 'created_at'),
    )


class AgentRun(Base):
    __tablename__ = 'agent_runs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, ForeignKey('chats.id', ondelete='CASCADE'), nullable=False)
    trigger_message_id = Column(Integer, ForeignKey('messages.id', ondelete='SET NULL'), nullable=True)
    agent_name = Column(String(100), nullable=False)
    agent_version = Column(String(20), nullable=True)
    status = Column(String(20), default='running', nullable=False)
    input_data = Column(JSON, nullable=True)
    final_result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    total_steps = Column(Integer, default=0, nullable=False)
    total_tool_calls = Column(Integer, default=0, nullable=False)
    token_usage = Column(JSON, default=dict, nullable=False)
    cost = Column(Numeric(10, 6), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    metadata_ = Column('metadata', JSON, default=dict, nullable=False)

    # Relationships
    chat = relationship('Chat', back_populates='agent_runs')
    tool_calls = relationship('ToolCall', back_populates='agent_run')

    __table_args__ = (
        Index('idx_agent_runs_chat_id', 'chat_id'),
        Index('idx_agent_runs_agent_name', 'agent_name'),
        Index('idx_agent_runs_status', 'status'),
        Index('idx_agent_runs_started_at', 'started_at'),
    )
```

---

## Common Queries

### Get active chats for a user
```python
chats = session.query(Chat).filter(
    Chat.user_id == user_id,
    Chat.deleted_at.is_(None)
).order_by(Chat.updated_at.desc()).all()
```

### Get conversation history
```python
messages = session.query(Message).filter(
    Message.chat_id == chat_id,
    Message.deleted_at.is_(None)
).order_by(Message.created_at.asc()).all()
```

### Get tool calls for an agent run
```python
tool_calls = session.query(ToolCall).filter(
    ToolCall.run_id == run_id
).order_by(ToolCall.created_at.asc()).all()
```

### Analytics: Tool usage by name
```python
from sqlalchemy import func

tool_stats = session.query(
    ToolCall.tool_name,
    func.count(ToolCall.id).label('total_calls'),
    func.avg(ToolCall.execution_time_ms).label('avg_time_ms'),
    func.sum(case((ToolCall.status == 'error', 1), else_=0)).label('error_count')
).group_by(ToolCall.tool_name).all()
```

### Analytics: Agent run costs
```python
from sqlalchemy import func
from datetime import datetime, timedelta

last_30_days = datetime.utcnow() - timedelta(days=30)

cost_by_agent = session.query(
    AgentRun.agent_name,
    func.sum(AgentRun.cost).label('total_cost'),
    func.count(AgentRun.id).label('total_runs')
).filter(
    AgentRun.started_at >= last_30_days
).group_by(AgentRun.agent_name).all()
```

---

## Migration Strategy

For existing chatforge installations using the minimal 2-table schema:

### Phase 1: Add new tables
```sql
-- Add tool_calls table
CREATE TABLE tool_calls (...);

-- Add agent_runs table
CREATE TABLE agent_runs (...);
```

### Phase 2: Extend existing tables
```sql
-- Add new columns to chats
ALTER TABLE chats ADD COLUMN title VARCHAR(255);
ALTER TABLE chats ADD COLUMN system_prompt TEXT;
ALTER TABLE chats ADD COLUMN settings JSON DEFAULT '{}';
ALTER TABLE chats ADD COLUMN updated_at DATETIME;
ALTER TABLE chats ADD COLUMN deleted_at DATETIME;

-- Add new columns to messages
ALTER TABLE messages ADD COLUMN parent_id INTEGER REFERENCES messages(id);
ALTER TABLE messages ADD COLUMN user_name VARCHAR(100);
ALTER TABLE messages ADD COLUMN content_format VARCHAR(20) DEFAULT 'text';
ALTER TABLE messages ADD COLUMN message_type VARCHAR(20) DEFAULT 'generated';
ALTER TABLE messages ADD COLUMN transcription TEXT;
ALTER TABLE messages ADD COLUMN token_count INTEGER;
ALTER TABLE messages ADD COLUMN deleted_at DATETIME;
```

### Phase 3: Backfill data
```python
# Set updated_at = created_at for existing chats
session.execute(
    update(Chat).values(updated_at=Chat.created_at)
)

# Set message_type based on role
session.execute(
    update(Message)
    .where(Message.role == 'user')
    .values(message_type='user')
)
```

---

## Integration with Host Apps

### User Resolution Hook

```python
from typing import Protocol, Optional
from dataclasses import dataclass

@dataclass
class UserInfo:
    user_id: str
    display_name: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None

class UserResolver(Protocol):
    def resolve(self, user_id: str) -> Optional[UserInfo]:
        """Resolve user_id to user info from host app."""
        ...

    def validate(self, user_id: str) -> bool:
        """Check if user_id exists in host app."""
        ...

# Example implementation
class MyAppUserResolver:
    def __init__(self, db_session):
        self.session = db_session

    def resolve(self, user_id: str) -> Optional[UserInfo]:
        user = self.session.query(MyAppUser).get(user_id)
        if user:
            return UserInfo(
                user_id=str(user.id),
                display_name=user.name,
                email=user.email
            )
        return None
```

### Event Hooks for Sync

```python
from chatforge.events import on_user_deleted, on_chat_created

# Host app registers hooks
@on_user_deleted
async def handle_user_deleted(user_id: str):
    """Called when host app deletes a user."""
    # Option 1: Cascade delete
    await chatforge.delete_user_data(user_id)

    # Option 2: Anonymize
    await chatforge.anonymize_user_data(user_id)

@on_chat_created
async def handle_chat_created(chat_id: int, user_id: str):
    """Called when new chat is created."""
    # Sync to analytics, billing, etc.
    await analytics.track('chat_created', user_id=user_id)
```

---

## Summary

This schema provides:

| Feature | Table | Benefit |
|---------|-------|---------|
| Conversations | `chats` | Organize messages, store settings |
| Messages | `messages` | Full conversation history with threading |
| Tool Tracking | `tool_calls` | Debug tool issues, measure performance |
| Agent Tracking | `agent_runs` | Monitor agent behavior, track costs |
| Soft Deletes | `deleted_at` | Data recovery, audit compliance |
| Flexibility | JSON fields | Extend without migrations |
| User Integration | Hooks + Resolver | Works with any auth system |

This replaces the minimal 2-table schema with a production-ready foundation for agentic AI applications.
