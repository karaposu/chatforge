# Chatforge Codebase Introduction

Welcome to Chatforge. This document will help you understand how the codebase is organized and how data flows through the system.

---

## Architecture Style: Hexagonal (Ports & Adapters)

Chatforge follows **Hexagonal Architecture**, also known as "Ports and Adapters." The core idea is simple:

```
┌─────────────────────────────────────────────────────────────┐
│                        ADAPTERS                              │
│  (concrete implementations: SQLite, OpenAI, Slack, etc.)    │
│                                                              │
│    ┌─────────────────────────────────────────────────┐      │
│    │                    PORTS                         │      │
│    │  (abstract interfaces: StoragePort, LLM, etc.)  │      │
│    │                                                  │      │
│    │    ┌─────────────────────────────────────┐      │      │
│    │    │            CORE DOMAIN              │      │      │
│    │    │   (ReActAgent, business logic)      │      │      │
│    │    └─────────────────────────────────────┘      │      │
│    │                                                  │      │
│    └─────────────────────────────────────────────────┘      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Why this matters:**
- The core domain (agent logic) never imports concrete implementations
- You can swap databases, AI providers, or platforms without touching core logic
- Testing is easy: inject mock adapters instead of real ones

---

## Directory Structure

```
chatforge/
├── services/           # Core business logic (the "domain")
│   ├── agent/          # ReACT agent engine
│   ├── llm/            # LLM factory for multiple providers
│   ├── vision/         # Image analysis service
│   └── cleanup.py      # Background cleanup runners
│
├── ports/              # Abstract interfaces (the "contracts")
│   ├── storage.py      # Conversation persistence
│   ├── messaging_platform_integration.py  # Chat platforms
│   ├── knowledge.py    # Knowledge base search
│   ├── ticketing.py    # Ticket/task creation
│   └── tracing.py      # Observability
│
├── adapters/           # Concrete implementations
│   ├── storage/        # InMemory, SQLite, SQLAlchemy
│   ├── fastapi/        # REST API routes
│   └── null.py         # No-op adapters for testing
│
├── middleware/         # Security guardrails
│   ├── pii.py          # PII detection/redaction
│   ├── injection.py    # Prompt injection detection
│   └── safety.py       # Response safety checks
│
├── config/             # Configuration management
│   ├── llm.py          # LLM settings
│   ├── agent.py        # Agent settings
│   └── storage.py      # Storage settings
│
├── utils/              # Utilities
│   └── async_bridge.py # Sync/async conversion
│
└── exceptions.py       # Exception hierarchy
```

---

## Data Flow: Processing a Message

Here's how a user message flows through the system:

```
┌──────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
│  User    │────▶│  Entry Point │────▶│  Middleware │────▶│  Agent   │
│  Message │     │  (FastAPI)   │     │  (Security) │     │  Engine  │
└──────────┘     └──────────────┘     └─────────────┘     └────┬─────┘
                                                               │
                 ┌─────────────────────────────────────────────┘
                 │
                 ▼
    ┌────────────────────────────────────────────────────────────┐
    │                     REACT LOOP                              │
    │  ┌─────────┐    ┌─────────┐    ┌─────────┐                 │
    │  │ REASON  │───▶│   ACT   │───▶│ OBSERVE │──┐              │
    │  │ (LLM)   │    │ (Tools) │    │(Results)│  │              │
    │  └─────────┘    └─────────┘    └─────────┘  │              │
    │       ▲                                      │              │
    │       └──────────────────────────────────────┘              │
    │                    (repeat until done)                      │
    └────────────────────────────────────────────────────────────┘
                 │
                 ▼
    ┌────────────────────┐     ┌────────────────────┐
    │  Safety Guardrail  │────▶│  Storage Adapter   │
    │  (check response)  │     │  (save messages)   │
    └────────────────────┘     └────────────────────┘
                 │
                 ▼
           ┌──────────┐
           │ Response │
           │ to User  │
           └──────────┘
```

### Step-by-Step Breakdown

1. **Entry Point** (`adapters/fastapi/routes.py`)
   - User sends POST to `/chat` with message
   - Request is validated and session ID is assigned

2. **Conversation History** (`ports/storage.py`)
   - Previous messages are retrieved from storage
   - Provides context for the AI

3. **Middleware Pipeline** (`middleware/`)
   - PII detection: scans for sensitive data
   - Injection guard: blocks manipulation attempts
   - (These run BEFORE the message reaches the agent)

4. **Agent Processing** (`services/agent/engine.py`)
   - Message + history sent to ReACT agent
   - Agent enters reasoning loop (see below)

5. **ReACT Loop**
   - **Reason**: LLM decides what to do
   - **Act**: Execute tools if needed
   - **Observe**: Check results
   - **Repeat** until task complete or max iterations

6. **Response Safety** (`middleware/safety.py`)
   - Agent response is checked for safety
   - Unsafe responses are replaced with fallback

7. **Persistence** (`adapters/storage/`)
   - User message and agent response saved
   - Conversation continues next time

8. **Response Returned**
   - JSON with response text and trace ID

---

## Main Abstractions

### 1. Ports (Interfaces)

Ports define **what** the system needs, not **how** it's implemented.

| Port | Purpose | Key Methods |
|------|---------|-------------|
| `StoragePort` | Save/retrieve conversations | `save_message()`, `get_conversation()` |
| `MessagingPlatformIntegrationPort` | Talk to chat platforms | `send_message()`, `get_conversation_history()` |
| `KnowledgePort` | Search knowledge bases | `search()`, `get_context_for_rag()` |
| `TicketingPort` | Create tickets/tasks | `execute()`, `add_comment()` |
| `TracingPort` | Observability/tracing | `span()`, `get_active_trace_id()` |

### 2. Adapters (Implementations)

Adapters are **concrete implementations** of ports.

```python
# Example: Storage has multiple adapters
StoragePort (abstract)
    ├── InMemoryStorageAdapter   # For development/testing
    ├── SQLiteStorageAdapter     # Simple file-based
    └── SQLAlchemyStorageAdapter # Any SQL database
```

### 3. Services (Business Logic)

Services contain the core logic that uses ports.

| Service | Location | Purpose |
|---------|----------|---------|
| `ReActAgent` | `services/agent/engine.py` | Main agent that processes messages |
| `LLM Factory` | `services/llm/factory.py` | Creates LLM instances for any provider |
| `ImageAnalyzer` | `services/vision/analyzer.py` | Analyzes images with vision LLMs |
| `CleanupRunner` | `services/cleanup.py` | Background cleanup of old data |

### 4. Middleware (Security Layer)

Middleware intercepts requests/responses for security checks.

| Middleware | Purpose |
|------------|---------|
| `PIIDetector` | Find/redact personal information |
| `PromptInjectionGuard` | Block manipulation attempts |
| `SafetyGuardrail` | Ensure responses are appropriate |
| `ContentFilter` | Keyword-based blocking |

---

## Key Design Patterns

### 1. Dependency Injection

Components receive their dependencies, they don't create them.

```python
# Good: Dependencies injected
agent = ReActAgent(
    tools=[search_tool, ticket_tool],
    llm=get_llm(provider="openai"),
    messaging_port=slack_adapter,
)

# Bad: Dependencies created internally (we don't do this)
class Agent:
    def __init__(self):
        self.llm = OpenAI()  # Hardcoded - can't swap
```

### 2. Factory Pattern

Factories create objects based on configuration.

```python
# LLM Factory - same interface, different providers
llm = get_llm(provider="openai")    # Returns ChatOpenAI
llm = get_llm(provider="anthropic") # Returns ChatAnthropic
llm = get_llm(provider="bedrock")   # Returns BedrockChat

# Router Factory - creates configured FastAPI router
router = create_chat_router(
    agent=agent,
    storage=storage,
    cleanup_runner=cleanup,
)
```

### 3. Strategy Pattern

Different strategies for handling the same task.

```python
# PII handling strategies
class PIIStrategy(Enum):
    REDACT = "redact"   # Replace with [REDACTED]
    MASK = "mask"       # Show partial: ****1234
    HASH = "hash"       # Replace with hash
    BLOCK = "block"     # Raise exception
```

### 4. Template Method Pattern

Base class defines algorithm, subclasses implement specifics.

```python
# AsyncAwareTool base class
class AsyncAwareTool(BaseTool):
    def _run(self, **kwargs):       # Template: handles sync
        return run_async(self._execute_async(**kwargs))

    async def _arun(self, **kwargs): # Template: handles async
        return await self._execute_async(**kwargs)

    @abstractmethod
    async def _execute_async(self, **kwargs):  # Subclass implements
        ...
```

### 5. Protocol-Based Design

Uses Python protocols for loose coupling (duck typing with type hints).

```python
class CacheProtocol(Protocol):
    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str) -> None: ...

# Any class with get() and set() works - no inheritance needed
```

---

## Common Patterns You'll See

### Async-First with Sync Bridge

Most I/O is async, but sync wrappers exist for convenience.

```python
# Async method (preferred)
result = await guard.check_message(text)

# Sync wrapper (uses async bridge internally)
result = guard.check_message_sync(text)
```

### Configuration via Environment

Settings come from environment variables via Pydantic.

```python
# config/llm.py
class LLMSettings(BaseSettings):
    provider: str = "openai"
    model_name: str = "gpt-4o-mini"
    openai_api_key: str | None = None  # From OPENAI_API_KEY env var
```

### Dataclasses for Data Transfer

Structured data uses dataclasses, not raw dicts.

```python
@dataclass
class MessageRecord:
    content: str
    role: str  # "user" | "assistant"
    timestamp: datetime = field(default_factory=_utc_now)
```

---

## Where to Start

1. **Understand the agent**: Start with `services/agent/engine.py` - this is the heart of the system

2. **Trace a request**: Follow a message through `adapters/fastapi/routes.py` → agent → storage

3. **Read the ports**: `ports/` directory defines all the contracts

4. **Study one adapter**: Pick `adapters/storage/memory.py` - it's the simplest implementation

5. **Check middleware**: `middleware/pii.py` shows how security layers work

---

## Quick Reference: File Locations

| When you need to... | Look at... |
|---------------------|------------|
| Understand agent logic | `services/agent/engine.py` |
| Add a new tool | `services/agent/tools/base.py` |
| Change LLM provider | `services/llm/factory.py` |
| Add storage backend | `adapters/storage/` |
| Add API endpoint | `adapters/fastapi/routes.py` |
| Add security check | `middleware/` |
| Define new interface | `ports/` |
| Handle errors | `exceptions.py` |
