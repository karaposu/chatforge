# Introduction to the ChatForge Codebase

**Status Notice**: This codebase is under heavy development and is not currently in a working state. This document describes the intended architecture and design patterns.

---

## Welcome!

If you're reading this, you're about to work on ChatForge - a framework for building production-grade AI chat agents. This guide will help you understand how the codebase is structured, how data flows through the system, and the key architectural decisions that shape the code.

## The Big Picture: What Are We Building?

ChatForge is a **framework**, not an application. Think of it like FastAPI or Django - it provides the infrastructure and patterns for building AI chatbots that can:
- Have intelligent conversations
- Search knowledge bases
- Create tasks/tickets
- Analyze images
- Integrate with messaging platforms (Slack, Teams, etc.)
- Stay safe and secure

The goal is to let developers build custom AI assistants by plugging in their own tools and integrations, without worrying about all the plumbing.

---

## Core Architectural Pattern: Hexagonal Architecture (Ports & Adapters)

This is the **most important** concept to understand about this codebase.

### The Problem It Solves

Traditional layered architectures couple business logic to infrastructure (databases, APIs, etc.). When you want to switch from PostgreSQL to MongoDB, or from Slack to Teams, you have to rewrite your core logic.

### Our Solution: Ports & Adapters

```
┌─────────────────────────────────────────────────────────┐
│                    ADAPTERS (Outer)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │  FastAPI │  │  Slack   │  │  SQLite  │  │ OpenAI │ │
│  │ Adapter  │  │ Adapter  │  │ Adapter  │  │Adapter │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬────┘ │
│       │             │               │            │      │
│ ┌─────▼─────────────▼───────────────▼────────────▼───┐ │
│ │              PORTS (Interfaces)                     │ │
│ │  MessagingPort  │ StoragePort │ LLM Interface      │ │
│ └─────────────────────┬─────────────────────────────┘  │
│                       │                                 │
│ ┌─────────────────────▼─────────────────────────────┐  │
│ │         DOMAIN LOGIC (Core/Inner)                 │  │
│ │  - ReActAgent (agent reasoning)                   │  │
│ │  - Tools (search, create, analyze)                │  │
│ │  - Business rules                                 │  │
│ │  - Middleware (safety, PII)                       │  │
│ └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Key Principles:**
1. **Domain logic** (center) knows nothing about databases, APIs, or frameworks
2. **Ports** (interfaces) define what the domain needs (e.g., "I need to store messages")
3. **Adapters** (outer layer) implement ports for specific technologies (e.g., "Here's how to store in SQLite")
4. **Dependencies point inward** - adapters depend on ports, not vice versa

### Why This Matters

- Want to switch from OpenAI to Anthropic? Just swap the adapter.
- Want to test without a database? Use the in-memory adapter.
- Want to add Discord support? Write a new messaging adapter.
- **Zero changes to your core business logic.**

---

## Main Abstractions (The Ports)

These are the key interfaces that define how the system works. Think of them as "contracts" that adapters must fulfill.

### 1. **MessagingPort** (`src/ports/messaging.py`)
**Purpose**: Platform-agnostic messaging (send/receive messages)

**Responsibilities:**
- Get conversation history
- Send messages
- Show typing indicators
- Download file attachments
- Resolve user info

**Why It Exists:** So your agent can work with Slack, Teams, Discord, or a REST API without knowing which one it is.

**Example Adapters:** (Not yet implemented)
- `SlackMessagingAdapter`
- `TeamsMessagingAdapter`
- `APIMessagingAdapter` (for HTTP requests)

---

### 2. **StoragePort** (`src/ports/storage.py`)
**Purpose**: Conversation persistence and history management

**Responsibilities:**
- Save messages to conversation history
- Retrieve conversation with message limit
- Delete conversations (compliance, TTL)
- List user's conversations
- Cleanup expired data

**Why It Exists:** Your agent needs memory. This port defines "what" storage does, not "how."

**Current Adapters:**
- `InMemoryStorageAdapter` - Development/testing (data lost on restart)
- `SQLiteStorageAdapter` - File-based persistence

**Future Adapters:** PostgreSQL, Redis, DynamoDB

---

### 3. **TicketingPort** (`src/ports/action.py`)
**Purpose**: Creating tasks/tickets in external systems

**Responsibilities:**
- Execute actions (create ticket, task, incident)
- Attach files to actions
- Add comments to existing actions
- Update action status
- Get action information

**Why It Exists:** So your agent can create Jira tickets, ServiceNow incidents, or custom tasks without knowing the specific system.

**Example Adapters:** (Not yet implemented)
- `JiraActionAdapter`
- `ServiceNowActionAdapter`
- `ZendeskActionAdapter`

---

### 4. **KnowledgePort** (`src/ports/knowledge.py`)
**Purpose**: Searching knowledge bases for RAG (Retrieval Augmented Generation)

**Responsibilities:**
- Search knowledge base
- Get formatted context for RAG injection
- Retrieve specific pages
- Format results for display or prompts

**Why It Exists:** So your agent can search Notion, Confluence, SharePoint, or custom docs using the same interface.

**Example Adapters:** (Not yet implemented)
- `NotionKnowledgeAdapter`
- `ConfluenceKnowledgeAdapter`
- `SharePointKnowledgeAdapter`

---

### 5. **TracingPort** (`src/ports/tracing.py`)
**Purpose**: Observability and tracing (MLflow, Langsmith, etc.)

**Responsibilities:**
- Create trace spans
- Log user feedback
- Track LLM invocations
- Link traces to platform messages

**Why It Exists:** Production observability without coupling to specific tracing systems.

**Example Adapters:** (Not yet implemented)
- `MLflowTracingAdapter`
- `LangsmithTracingAdapter`
- `NullTracingAdapter` (no-op for development)

---

## Data Flow Paths

Understanding how data moves through the system is crucial. Here are the main flows:

### Flow 1: Incoming Message (FastAPI REST API)

```
1. HTTP POST /chat
   ↓
2. FastAPI route handler (src/adapters/fastapi/routes.py)
   ↓
3. Validate request (Pydantic schemas)
   ↓
4. Retrieve conversation history (StoragePort)
   ↓
5. Build context dict (user_id, session_id, metadata)
   ↓
6. ReActAgent.process_message(message, history, context)
   ↓
7. [AGENT PROCESSING - see Flow 2]
   ↓
8. Save user message to storage (StoragePort)
   ↓
9. Save agent response to storage (StoragePort)
   ↓
10. Return ChatResponse with trace_id
```

**Key Files:**
- `src/adapters/fastapi/routes.py` - REST endpoints
- `src/adapters/fastapi/schemas.py` - Request/response models
- `src/ports/storage.py` - Storage interface

---

### Flow 2: Agent Processing (The Brain)

```
1. ReActAgent receives: message, history, context
   ↓
2. Convert history to LangChain message format
   ↓
3. Apply middleware (optional):
   - Prompt injection detection
   - PII detection/redaction
   - Content filtering
   ↓
4. Create tracing span (if enabled)
   ↓
5. Invoke LangGraph ReACT agent
   ↓
   ┌────────────────────────────────────┐
   │   LangGraph ReACT Loop:           │
   │                                    │
   │   a. LLM reasons about what to do │
   │   b. Decides to use a tool OR     │
   │      respond to user              │
   │   c. If tool: execute tool        │
   │   d. Observe tool result          │
   │   e. Repeat until done            │
   └────────────────────────────────────┘
   ↓
6. Extract final response
   ↓
7. Apply safety guardrails (optional):
   - Safety check on response
   - PII redaction in response
   ↓
8. Return (response, trace_id)
```

**Key Files:**
- `src/adapters/agent/engine.py` - ReActAgent implementation
- `src/middleware/injection.py` - Prompt injection guard
- `src/middleware/pii.py` - PII detection
- `src/middleware/safety.py` - Safety guardrails

---

### Flow 3: Tool Execution

```
1. Agent decides to use a tool
   ↓
2. LangGraph invokes tool._arun() or tool._run()
   ↓
3. AsyncAwareTool base class routes to _execute_async()
   ↓
4. Tool implementation runs business logic:
   - May call a Port (e.g., KnowledgePort.search())
   ↓
5. Port interface delegates to concrete Adapter
   ↓
6. Adapter makes external API call/database query
   ↓
7. Adapter returns standardized result
   ↓
8. Tool formats result for LLM
   ↓
9. Result returned to agent
   ↓
10. Agent reasons about result and decides next step
```

**Key Files:**
- `src/tools/base.py` - AsyncAwareTool base class
- Individual tool implementations (future)

---

### Flow 4: LLM Provider Selection

```
1. Code calls get_llm() factory
   ↓
2. Factory reads config (environment variables)
   ↓
3. Based on LLM_PROVIDER:
   - "openai" → ChatOpenAI instance
   - "anthropic" → ChatAnthropic instance
   - "bedrock" → BedrockChat instance
   ↓
4. Returns BaseChatModel (LangChain interface)
   ↓
5. All code uses BaseChatModel methods:
   - .invoke() - synchronous
   - .ainvoke() - async
   - .stream() - streaming
```

**Key Files:**
- `src/llm/factory.py` - LLM factory
- `src/config/llm.py` - LLM configuration

---

### Flow 5: Memory Management & Cleanup

```
Background Process (AsyncCleanupRunner):

Every N seconds:
   ↓
1. Check if cleanup is needed for each component
   ↓
2. Call registered cleanup functions:
   - storage.cleanup_expired(ttl_minutes)
   - cache.cleanup_expired()
   ↓
3. Track metrics (items cleaned, duration)
   ↓
4. Store in cleanup history (bounded queue)
   ↓
5. Log warnings if cleanup is slow
```

**Key Files:**
- `src/services/cleanup.py` - Cleanup runners (async & sync)

---

## Top-Level Design Patterns

Beyond hexagonal architecture, several patterns are used throughout the codebase:

### 1. **Factory Pattern**

Used for creating complex objects with multiple configuration options.

**Example: LLM Factory** (`src/llm/factory.py`)
```python
# Instead of:
if provider == "openai":
    llm = ChatOpenAI(api_key=..., model=..., temperature=...)
elif provider == "anthropic":
    llm = ChatAnthropic(api_key=..., model=..., temperature=...)
# ... etc.

# We have:
llm = get_llm()  # Reads config, returns correct instance
```

**Benefits:**
- Configuration centralized
- Easy to add new providers
- Testing becomes easier (mock the factory)

---

### 2. **Template Method Pattern**

Used in `AsyncAwareTool` base class.

**The Problem:** Every tool needs both sync and async entry points for LangChain compatibility, leading to code duplication.

**The Solution:**
```python
class AsyncAwareTool(BaseTool):
    # Subclass implements ONLY this:
    async def _execute_async(self, **kwargs) -> str:
        # Actual tool logic here
        ...

    # Base class provides these automatically:
    def _run(self, **kwargs) -> str:
        return run_async(self._execute_async(**kwargs))

    async def _arun(self, **kwargs) -> str:
        return await self._execute_async(**kwargs)
```

**Benefits:**
- Single source of truth for tool logic
- No code duplication
- Consistent async bridging

---

### 3. **Dependency Injection**

Components receive dependencies through constructors, not global state.

**Example:**
```python
# Bad (global state):
agent = ReActAgent()
agent.process_message(...)  # Uses global storage, global LLM

# Good (dependency injection):
storage = InMemoryStorageAdapter()
llm = get_llm(provider="openai")
tracing = NullTracingAdapter()

agent = ReActAgent(
    tools=my_tools,
    llm=llm,
    messaging_port=None,
    tracing=tracing,
)

router = create_chat_router(
    agent=agent,
    storage=storage,
    cleanup_runner=cleanup_runner,
)
```

**Benefits:**
- Easy testing (inject mocks)
- Clear dependencies
- No hidden state
- Components are isolated

---

### 4. **Strategy Pattern**

Used for middleware components that can be swapped.

**Example: Safety Middleware**
```python
# Different strategies for handling unsafe content:
class SafetyGuardrail:
    # Uses LLM to evaluate safety
    async def check_response(self, response) -> SafetyCheckResult:
        ...

class ContentFilter:
    # Uses keyword matching
    def check_content(self, content) -> ContentCheckResult:
        ...

# Choose based on requirements:
if need_smart_checking:
    guardrail = SafetyGuardrail(...)
else:
    guardrail = ContentFilter(...)
```

---

### 5. **Observer Pattern (Implicit)**

Used in cleanup services and tracing.

**Example: Cleanup History**
```python
# CleanupHistory observes cleanup cycles
cleanup_runner = AsyncCleanupRunner(...)
await cleanup_runner.run_cleanup_cycle()  # Automatically tracked
history = cleanup_runner.get_cleanup_history()  # Retrieve observations
```

---

### 6. **Builder Pattern (via Pydantic)**

Configuration is built using Pydantic settings with environment variables.

**Example:**
```python
# Settings automatically built from environment
class LLMSettings(BaseSettings):
    provider: str = "openai"
    model_name: str = "gpt-4"
    temperature: float = 0.0

    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        env_file=".env",
    )

# Auto-loads from LLM_PROVIDER, LLM_MODEL_NAME, etc.
llm_config = LLMSettings()
```

---

## Directory Structure & Organization

```
chatforge/
├── src/
│   ├── adapters/          # Concrete implementations (outer layer)
│   │   ├── agent/         # Agent implementations
│   │   │   ├── engine.py  # ReActAgent (main agent)
│   │   │   └── state.py   # LangGraph state definitions
│   │   ├── fastapi/       # REST API adapter
│   │   │   ├── routes.py  # Endpoint handlers
│   │   │   └── schemas.py # Request/response models
│   │   ├── storage/       # Storage adapters
│   │   │   ├── memory.py  # In-memory storage
│   │   │   └── sqlite.py  # SQLite storage
│   │   └── null.py        # Null adapters (testing)
│   │
│   ├── ports/             # Interfaces (contracts)
│   │   ├── action.py      # Action/task system interface
│   │   ├── knowledge.py   # Knowledge base interface
│   │   ├── messaging.py   # Messaging platform interface
│   │   ├── storage.py     # Storage interface
│   │   └── tracing.py     # Tracing interface
│   │
│   ├── middleware/        # Request/response processing
│   │   ├── injection.py   # Prompt injection detection
│   │   ├── pii.py         # PII detection/redaction
│   │   ├── safety.py      # Safety guardrails
│   │   └── constants.py   # Shared patterns/constants
│   │
│   ├── services/          # Domain services
│   │   ├── cleanup.py     # Memory management
│   │   └── vision/        # Image analysis
│   │       └── analyzer.py
│   │
│   ├── tools/             # Agent tools (future)
│   │   └── base.py        # AsyncAwareTool base class
│   │
│   ├── llm/               # LLM abstraction
│   │   └── factory.py     # LLM provider factory
│   │
│   ├── config/            # Configuration
│   │   ├── llm.py         # LLM settings
│   │   ├── storage.py     # Storage settings
│   │   ├── agent.py       # Agent settings
│   │   └── guardrails.py  # Guardrail settings
│   │
│   ├── utils/             # Utilities
│   │   └── async_bridge.py # Sync/async bridging
│   │
│   └── exceptions.py      # Exception hierarchy
│
└── pyproject.toml         # Project metadata & dependencies
```

**Organizational Principles:**

1. **Ports** define interfaces (what can be done)
2. **Adapters** implement interfaces (how it's done)
3. **Middleware** processes data in/out
4. **Services** contain business logic
5. **Config** centralizes settings
6. **Utils** provide cross-cutting utilities

---

## Key Concepts for New Engineers

### 1. **Ports vs Adapters**

- **Port** = Interface (abstract, what)
- **Adapter** = Implementation (concrete, how)

If you want to add a new integration:
1. Check if a port exists for that capability
2. If yes, implement an adapter for that port
3. If no, create a new port, then implement an adapter

### 2. **The Agent is the Orchestrator**

The `ReActAgent` (`src/adapters/agent/engine.py`) is the brain:
- Receives user messages
- Maintains conversation context
- Decides which tools to use
- Generates responses

Everything else is either:
- **Input** to the agent (messages, history, tools)
- **Output** from the agent (responses, actions)
- **Infrastructure** supporting the agent (storage, tracing, middleware)

### 3. **Tools Are Extensions**

When you want the agent to do something new:
1. Create a tool that inherits from `AsyncAwareTool`
2. Implement `_execute_async()` with the logic
3. Register the tool with the agent
4. The agent will automatically know when to use it (via LLM reasoning)

### 4. **Middleware is Optional but Powerful**

Middleware runs before/after agent processing:
- **Before**: Prompt injection detection, content filtering, PII redaction
- **After**: Safety checks, response filtering

You can chain multiple middleware components.

### 5. **Configuration Over Code**

Most behavior is controlled via environment variables:
```bash
# LLM provider
LLM_PROVIDER=openai
LLM_MODEL_NAME=gpt-4

# Storage
STORAGE_CLEANUP_ENABLED=true
STORAGE_CACHE_CLEANUP_INTERVAL_SECONDS=900

# Agent
AGENT_MAX_ITERATIONS=10
AGENT_CONVERSATION_TIMEOUT_MINUTES=30
```

This makes it easy to:
- Switch between development and production
- Test different configurations
- Deploy without code changes

---

## Common Patterns You'll See

### Pattern: Async/Sync Bridging

Many components need to work in both sync and async contexts:

```python
# Async context (FastAPI)
result = await storage.get_conversation(conv_id)

# Sync context (LangChain tools)
result = run_async(storage.get_conversation(conv_id))
```

**Key file**: `src/utils/async_bridge.py`

---

### Pattern: Type-Safe Configuration

Using Pydantic for type-safe, validated configuration:

```python
class MySettings(BaseSettings):
    api_key: str  # Required
    timeout: int = 30  # Optional with default
    max_retries: int = Field(default=3, ge=1, le=10)  # Validated

    model_config = SettingsConfigDict(
        env_prefix="MY_",
        env_file=".env",
    )
```

---

### Pattern: Dataclass for Data Transfer

Structured data uses `@dataclass`:

```python
@dataclass
class MessageRecord:
    content: str
    role: str
    created_at: datetime = field(default_factory=_utc_now)
    metadata: MessageMetadata = field(default_factory=dict)
```

**Benefits:**
- Type hints
- Default values
- Auto-generated `__init__`, `__repr__`, etc.

---

### Pattern: Protocol for Duck Typing

When you need an interface without forcing inheritance:

```python
class CacheProtocol(Protocol):
    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str) -> None: ...

# Any object with get/set methods works:
def use_cache(cache: CacheProtocol):
    value = cache.get("key")
```

---

## Testing Philosophy (Implied by Architecture)

While tests aren't written yet, the architecture enables:

### 1. **Unit Testing**
Mock ports to test components in isolation:
```python
def test_agent():
    mock_storage = MockStorageAdapter()
    mock_llm = MockLLM()

    agent = ReActAgent(tools=[], llm=mock_llm)
    response = agent.process_message("test", [])

    assert response == "expected"
```

### 2. **Integration Testing**
Use in-memory adapters for fast integration tests:
```python
def test_full_flow():
    storage = InMemoryStorageAdapter()
    agent = ReActAgent(...)
    router = create_chat_router(agent, storage)

    # Test full HTTP → Agent → Storage flow
```

### 3. **Adapter Testing**
Test each adapter independently against its port interface:
```python
def test_storage_adapter_compliance():
    adapter = SQLiteStorageAdapter(":memory:")

    # Test all StoragePort methods
    await adapter.save_message(...)
    messages = await adapter.get_conversation(...)
    assert len(messages) == 1
```

---

## Common Gotchas & Tips

### 1. **Always Use Ports, Never Adapters Directly**

❌ Bad:
```python
from chatforge.adapters.storage.sqlite import SQLiteStorageAdapter
storage = SQLiteStorageAdapter(...)
```

✅ Good:
```python
from chatforge.ports import StoragePort
from chatforge.adapters import InMemoryStorageAdapter

storage: StoragePort = InMemoryStorageAdapter()
```

**Why:** Using the port type means you can swap adapters easily.

---

### 2. **Async All the Way (When Possible)**

The codebase prefers async:
- FastAPI is async
- LangChain supports async
- Storage adapters are async

Only use sync when required (e.g., LangChain tool `_run()` method).

---

### 3. **Configuration Hierarchy**

Settings are loaded in this order:
1. Default values in code
2. `.env` file
3. Environment variables (highest priority)

This lets you:
- Commit sensible defaults
- Override locally with `.env`
- Override in production with env vars

---

### 4. **Error Handling is Structured**

Use the exception hierarchy (`src/exceptions.py`):

```python
from chatforge.exceptions import AdapterError, ToolExecutionError

try:
    result = external_api.call()
except ExternalAPIError as e:
    raise AdapterError(
        message=f"API call failed: {e}",
        original_error=e,
        service_name="MyAPI",
    ) from e
```

This creates a clear error trail and better logging.

---

### 5. **Type Hints Are Mandatory**

All functions should have type hints:

```python
# Good
async def save_message(
    self,
    conversation_id: str,
    message: MessageRecord,
    user_id: str | None = None,
) -> None:
    ...

# Bad (no type hints)
async def save_message(conversation_id, message, user_id=None):
    ...
```

**Why:** Better IDE support, catches bugs early, serves as documentation.

---

## Where to Start as a New Engineer

### If You're Adding a New Integration:

1. **Identify the port** - Does one exist? (messaging, storage, action, knowledge?)
2. **Create an adapter** - Implement the port interface
3. **Add configuration** - Environment variables for API keys, endpoints, etc.
4. **Register with agent** - Make the agent aware of your adapter

**Example:** Adding Slack support
- Port: `MessagingPort` (already exists)
- Adapter: Create `SlackMessagingAdapter` in `src/adapters/messaging/`
- Config: Add `SlackSettings` in `src/config/`
- Register: Inject into agent/router

---

### If You're Adding a New Tool:

1. **Inherit from** `AsyncAwareTool` (`src/tools/base.py`)
2. **Implement** `_execute_async()` with your logic
3. **Define** Pydantic input schema
4. **Register** with the agent's tools list

**Example:** Adding a "search documentation" tool
- Create `SearchDocsTool(AsyncAwareTool)`
- Use `KnowledgePort` to search
- Return formatted results
- Add to agent tools list

---

### If You're Fixing a Bug:

1. **Identify the layer** - Is it in a port, adapter, service, or middleware?
2. **Check dependencies** - Is the port configured? Is the adapter initialized?
3. **Look at logs** - Structured logging throughout
4. **Write a test** - Reproduce the bug, fix it, ensure test passes

---

### If You're Refactoring:

1. **Preserve ports** - Don't change port interfaces without updating all adapters
2. **Update adapters** - All adapters must match port interfaces
3. **Check injection** - Ensure dependencies are properly injected
4. **Run type checker** - Use `mypy` or similar to catch type issues

---

## Future Architecture Considerations

As the codebase develops, keep these principles in mind:

### 1. **Ports Should Be Stable**

Once a port is defined and adapters exist, changing it is expensive. Design ports carefully:
- Think about future use cases
- Make methods focused and cohesive
- Use optional parameters for flexibility
- Document expected behavior clearly

### 2. **Adapters Should Be Isolated**

Each adapter should:
- Have its own configuration
- Handle its own errors
- Not depend on other adapters
- Be testable independently

### 3. **Business Logic Stays in the Core**

Never put business logic in adapters. Adapters translate between external systems and internal models.

**Example:**
- ❌ Adapter validates ticket format (business rule)
- ✅ Adapter converts to/from API format (translation)

### 4. **Middleware Should Be Composable**

Middleware should be stackable and independent:

```python
# Should be able to combine any middleware
pipeline = [
    PromptInjectionGuard(...),
    ContentFilter(...),
    PIIDetector(...),
    SafetyGuardrail(...),
]
```

---

## Conclusion

ChatForge is built on solid architectural principles:
- **Hexagonal Architecture** for flexibility and testability
- **Dependency Injection** for clarity and modularity
- **Port/Adapter Pattern** for swappable integrations
- **Type Safety** for reliability and maintainability

As you work in this codebase:
1. **Respect the boundaries** - Keep ports, adapters, and core logic separate
2. **Follow the patterns** - Consistency makes the code easier to understand
3. **Think about flexibility** - Could this be swapped? Could it be tested?
4. **Document decisions** - Especially deviations from established patterns

Welcome to the team, and happy coding! 🚀

---

## Quick Reference

### Key Files to Bookmark

- `src/adapters/agent/engine.py` - Main agent logic
- `src/ports/` - All interface definitions
- `src/llm/factory.py` - LLM provider setup
- `src/exceptions.py` - Error types
- `src/utils/async_bridge.py` - Async/sync utilities

### Common Commands (Future)

```bash
# Run tests
pytest

# Type checking
mypy src/

# Linting
ruff check src/

# Format code
ruff format src/
```

### Environment Variables Cheat Sheet

```bash
# LLM Configuration
LLM_PROVIDER=openai|anthropic|bedrock
LLM_MODEL_NAME=gpt-4o
LLM_TEMPERATURE=0.0
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Storage
STORAGE_CLEANUP_ENABLED=true
STORAGE_CACHE_CLEANUP_INTERVAL_SECONDS=900

# Agent
AGENT_MAX_ITERATIONS=10
AGENT_CONVERSATION_TIMEOUT_MINUTES=30
```
