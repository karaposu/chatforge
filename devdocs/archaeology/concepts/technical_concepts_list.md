# Technical Concepts

Concepts related to implementation, infrastructure, and code-level patterns.

---

## Core Architecture

### 1. Hexagonal Architecture (Ports & Adapters)
The foundational architectural pattern separating core domain logic from infrastructure concerns. Core services depend on abstract ports (interfaces), while adapters provide concrete implementations for specific technologies.

| Status | Location |
|--------|----------|
| Implemented | `ports/` defines interfaces; `adapters/` provides implementations; `services/` contains domain logic |

---

### 2. LangGraph/LangChain Integration
The AI orchestration layer using LangGraph's `create_react_agent` for ReACT pattern execution. LangChain provides the unified LLM interface (`BaseChatModel`) and message types (`HumanMessage`, `AIMessage`).

| Status | Location |
|--------|----------|
| Implemented | `services/agent/engine.py` uses LangGraph; `services/llm/factory.py` uses LangChain |

---

### 3. Async-First Design
Most I/O operations are async, with sync wrappers provided for compatibility. Storage, messaging, LLM calls, and middleware checks are all async by default.

| Status | Location |
|--------|----------|
| Partially Implemented | Storage is fully async; middleware has both; some ports (Knowledge, Ticketing) are sync |

---

## Data Layer

### 4. Storage Abstraction
Conversation persistence abstracted through `StoragePort` interface. Implementations can vary from in-memory (development) to SQLite (simple) to SQLAlchemy (production databases).

| Status | Location |
|--------|----------|
| Implemented | `ports/storage.py` defines interface; `adapters/storage/` has InMemory, SQLite, SQLAlchemy |

#### 4.1 Lazy Table Initialization
Database tables created on first operation, not at adapter construction. Avoids blocking imports and allows adapter creation before async context is available.

| Status | Location |
|--------|----------|
| Implemented | `adapters/storage/sqlite.py:52` - `_ensure_tables()` pattern |

#### 4.2 Extended Storage Interface
Optional advanced methods (`create_chat`, `log_tool_call`, `start_agent_run`) for full observability. Simple adapters can skip these; full-featured adapters implement them.

| Status | Location |
|--------|----------|
| Interface Defined, Not Implemented | `ports/storage.py:195+` methods raise `NotImplementedError` |

---

### 5. Message Format Transformation
Conversion between application message format (`dict` with role/content) and LangChain format (`HumanMessage`, `AIMessage`). Critical for maintaining LLM API compatibility.

| Status | Location |
|--------|----------|
| Implemented | `services/agent/engine.py:311-349` - `_convert_to_messages()` |

**Hidden Consideration:** AIMessage created with `tool_calls=[]` to prevent OpenAI API errors when reconstructing history from external platforms that don't store tool call details.

---

## LLM Integration

### 6. Multi-Provider LLM Factory
Factory pattern creating LLM instances for different providers (OpenAI, Anthropic, Bedrock) with unified configuration. Provider-specific packages imported lazily to avoid dependency bloat.

| Status | Location |
|--------|----------|
| Implemented | `services/llm/factory.py` with `get_llm()`, `get_streaming_llm()`, `get_vision_llm()` |

#### 6.1 Lazy Provider Imports
LangChain provider packages (`langchain-openai`, `langchain-anthropic`) imported inside factory functions, not at module level. Reduces startup time and allows optional dependencies.

| Status | Location |
|--------|----------|
| Implemented | Each `_get_*_llm()` function has try/except ImportError |

#### 6.2 Vision Model Defaults
Separate defaults for vision-capable models per provider. Recognizes that standard models and vision models may differ.

| Status | Location |
|--------|----------|
| Implemented | `DEFAULT_VISION_MODELS` dict in `services/llm/factory.py:89` |

---

## Execution Model

### 7. ReACT Agent Loop
Reason-Act-Observe pattern for autonomous task completion. Agent reasons about next step, optionally executes tools, observes results, and repeats until done.

| Status | Location |
|--------|----------|
| Implemented | `services/agent/engine.py` wraps LangGraph's `create_react_agent` |

#### 7.1 Tool Invocation Tracking
Metadata collection during agent execution: tool names, arguments, call counts. Enables debugging and analytics without modifying tool implementations.

| Status | Location |
|--------|----------|
| Implemented | `services/agent/engine.py:263-282` iterates result messages for tool_calls |

---

### 8. AsyncAwareTool Pattern
Base class eliminating sync/async code duplication in tools. Subclasses implement only `_execute_async()`; base provides `_run()` and `_arun()` wrappers automatically.

| Status | Location |
|--------|----------|
| Implemented | `services/agent/tools/base.py:43` - `AsyncAwareTool` class |

**Hidden Consideration:** `**kwargs` in signature catches LangGraph config parameters that would otherwise cause errors. Not documented but essential for compatibility.

---

## Sync/Async Bridging

### 9. Shared Thread Pool Executor
Global `ThreadPoolExecutor` for running sync code from async contexts. Lazy creation, reusable across calls, explicit shutdown required.

| Status | Location |
|--------|----------|
| Implemented | `utils/async_bridge.py` - `get_executor()`, `shutdown_executor()` |

#### 9.1 Event Loop Per Sync Call
`run_async()` uses `asyncio.run()` which creates/destroys event loop per call. Simple but has ~1-5ms overhead and cannot be nested.

| Status | Location |
|--------|----------|
| Implemented | `utils/async_bridge.py:104` - known limitation |

**Hidden Consideration:** Fails with "event loop already running" in Jupyter notebooks. No workaround provided; users must use `nest_asyncio` externally.

---

## Configuration

### 10. Environment-Driven Configuration
Pydantic Settings classes reading from environment variables. Follows 12-factor app principles. Singletons created at import time.

| Status | Location |
|--------|----------|
| Implemented | `config/llm.py`, `config/agent.py`, `config/storage.py` |

#### 10.1 Provider-Specific API Keys
Separate environment variables for each LLM provider (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `AWS_*`). Validation happens at LLM creation, not startup.

| Status | Location |
|--------|----------|
| Implemented | `config/llm.py` - `LLMSettings` class |

---

## Background Processing

### 11. Cleanup Runners
Background task management for periodic cleanup operations. Async version uses `asyncio.create_task`; sync version uses `threading.Timer`. Configurable per-component intervals.

| Status | Location |
|--------|----------|
| Implemented | `services/cleanup.py` - `AsyncCleanupRunner`, `SyncCleanupRunner` |

#### 11.1 Cleanup History Tracking
Bounded deque storing cleanup cycle metrics (duration, items cleaned, errors). Enables monitoring and debugging without unbounded memory growth.

| Status | Location |
|--------|----------|
| Implemented | `services/cleanup.py:84` - `CleanupHistory` class |

---

## Type System

### 12. Dataclass Data Transfer Objects
Structured data uses `@dataclass` for type safety and IDE support. Preferred over raw dicts for messages, records, results.

| Status | Location |
|--------|----------|
| Implemented | `ports/storage_types.py`, `middleware/pii.py`, `services/vision/analyzer.py` |

#### 12.1 Protocol-Based Interfaces
Python `Protocol` for structural subtyping (duck typing with type hints). Allows adapters without inheritance requirement.

| Status | Location |
|--------|----------|
| Implemented | `ports/tracing.py:25` - `TracingPort` as Protocol |

#### 12.2 TypedDict for Metadata
`TypedDict` with `total=False` for optional structured metadata. Provides type hints without runtime enforcement.

| Status | Location |
|--------|----------|
| Implemented | `ports/knowledge.py:18` - `KnowledgeMetadata` |

---

## Error Handling

### 13. Structured Exception Hierarchy
Custom exceptions with context: `ChatforgeError` base, then `AdapterError`, `ToolExecutionError`, `ConfigurationError`, `ValidationError`, `MiddlewareError`, `AgentError`.

| Status | Location |
|--------|----------|
| Implemented | `exceptions.py` - full hierarchy defined |

#### 13.1 User vs Internal Error Messages
`ToolExecutionError` separates `user_message` (safe to show) from `internal_message` (for logging). Prevents leaking implementation details.

| Status | Location |
|--------|----------|
| Implemented | `exceptions.py:131` - dual message pattern |

---

### 14. Fail-Open Error Pattern
Security middleware returns "safe" on errors rather than blocking. Prioritizes availability over security. Errors are logged for investigation.

| Status | Location |
|--------|----------|
| Implemented (Controversial) | `middleware/injection.py:252`, `middleware/safety.py:243` |

**Hidden Assumption:** This assumes monitoring is in place to catch failures. In practice, silent fail-open could allow attacks during outages.

---

## API Layer

### 15. Router Factory Pattern
`create_chat_router()` creates configured FastAPI router with injected dependencies. Avoids global state in route definitions.

| Status | Location |
|--------|----------|
| Implemented | `adapters/fastapi/routes.py:67` |

#### 15.1 Server-Sent Events Streaming
`/chat/stream` endpoint uses SSE for streaming responses. Currently simulates streaming by chunking complete response.

| Status | Location |
|--------|----------|
| Partially Implemented | `adapters/fastapi/routes.py:188` - TODO: true streaming |

---

## Observability

### 16. Tracing Port
Abstract interface for observability platforms (MLflow, Langsmith, OpenTelemetry). Context manager for spans, trace ID propagation, feedback logging.

| Status | Location |
|--------|----------|
| Interface Only | `ports/tracing.py` defines protocol; only `NullTracingAdapter` exists |

#### 16.1 Trace-Based Feedback Loop
`log_feedback()` links user feedback (thumbs up/down) to traces. Enables RLHF-style improvement workflows.

| Status | Location |
|--------|----------|
| Interface Only | `ports/tracing.py:126` - method defined but unused |

---

## Implicit Technical Concepts (Hidden in Code)

### 17. Session ID Generation
Client can provide session_id or server generates UUID. Enables stateless server while maintaining conversation continuity.

| Status | Location |
|--------|----------|
| Implemented | `adapters/fastapi/routes.py:123` - `session_id = request.session_id or str(uuid4())` |

**Implication:** Session IDs are user-controllable and not validated. Privacy/security depends on ID unpredictability.

---

### 18. Per-Operation Database Connections
SQLite adapter opens/closes connection for each operation. No connection pooling. Simple but has overhead.

| Status | Location |
|--------|----------|
| Implemented | `adapters/storage/sqlite.py` - `async with aiosqlite.connect()` in each method |

**Trade-off:** Simplicity over performance. For high-throughput, connection pooling would be needed.

---

### 19. Reverse-Order Regex Replacement
PII redaction replaces matches from end to start of string. Preserves character positions during multiple replacements.

| Status | Location |
|--------|----------|
| Implemented | `middleware/pii.py:247` - `sorted(matches, key=lambda m: m.start, reverse=True)` |

**Why:** Forward replacement shifts positions, corrupting subsequent replacements.

---

### 20. Message Chronology Inversion
Storage retrieves messages newest-first (for LIMIT efficiency) then reverses for chronological order. Optimization detail hidden from callers.

| Status | Location |
|--------|----------|
| Implemented | `adapters/storage/sqlite.py:176` - `messages.reverse()` |

---

### 21. Hardcoded Operational Parameters
Various magic numbers baked into code: 60s cleanup check interval, 10 executor workers, 50 message history limit, 60s LLM timeout, 3 retries.

| Status | Location |
|--------|----------|
| Implemented But Not Configurable | Scattered throughout codebase |

**Impact on Scalability:** These work for development but may need tuning for production. Currently requires code changes.
