# Design Concepts

Concepts related to architectural patterns, design decisions, and structural organization.

---

## Foundational Patterns

### 1. Dependency Injection
Components receive their dependencies through constructor parameters rather than creating them internally. Enables testing with mocks and swapping implementations without code changes.

| Status | Location |
|--------|----------|
| Implemented | `ReActAgent.__init__(llm, tools, messaging_port, tracing)`, `create_chat_router(agent, storage, cleanup_runner)` |

---

### 2. Factory Pattern
Factory functions create configured instances, hiding construction complexity. Allows consistent configuration and provider selection through unified interface.

| Status | Location |
|--------|----------|
| Implemented | `get_llm()` in `services/llm/factory.py`, `create_chat_router()` in `adapters/fastapi/routes.py`, `create_tool()` in `services/agent/tools/base.py` |

---

### 3. Strategy Pattern
Interchangeable algorithms for the same operation. Client code works with strategy interface, implementation varies.

| Status | Location |
|--------|----------|
| Implemented | `PIIStrategy` enum (REDACT, MASK, HASH, BLOCK) in `middleware/pii.py:48` |

---

### 4. Template Method Pattern
Base class defines algorithm skeleton; subclasses override specific steps. Reduces duplication while allowing customization.

| Status | Location |
|--------|----------|
| Implemented | `AsyncAwareTool._run()` and `_arun()` are template methods; subclasses implement `_execute_async()` |

---

### 5. Null Object Pattern
Objects that do nothing but satisfy interface requirements. Eliminates null checks throughout codebase.

| Status | Location |
|--------|----------|
| Implemented | `NullMessagingAdapter`, `NullKnowledgeAdapter`, `NullTicketingAdapter` in `adapters/null.py`; `NullTracingAdapter` in `ports/tracing.py` |

---

## Separation Concerns

### 6. Port-Adapter Separation
Ports (in `ports/`) define abstract contracts. Adapters (in `adapters/`) provide implementations. Services (in `services/`) contain business logic that depends only on ports.

| Status | Location |
|--------|----------|
| Implemented | Clear directory structure; services import from ports, not adapters |

---

### 7. Configuration-Code Separation
Settings come from environment/config files via Pydantic Settings, not hardcoded. Code reads from config objects.

| Status | Location |
|--------|----------|
| Mostly Implemented | `config/` package provides settings; some hardcoded values remain (timeouts, intervals) |

---

### 8. Sync-Async Separation
Async methods are primary; sync wrappers provided for compatibility. Clear naming: `check_message()` vs `check_message_sync()`.

| Status | Location |
|--------|----------|
| Partially Implemented | Middleware has both; Knowledge/Ticketing ports are sync-only; Storage is async-only |

---

## Interface Design

### 9. Optional Dependencies Pattern
Most constructor parameters are optional with sensible defaults. Minimal required configuration for basic usage.

| Status | Location |
|--------|----------|
| Implemented | `ReActAgent(tools=[], system_prompt=None, messaging_port=None, tracing=None, llm=None)` |

**Hidden Philosophy:** Chatforge aims for "works out of the box" with progressive enhancement. Users add complexity as needed.

---

### 10. Layered Interface Design
Storage port has "legacy interface" (required, simple) and "extended interface" (optional, full-featured). Adapters can implement minimum viable functionality.

| Status | Location |
|--------|----------|
| Implemented | `ports/storage.py` - required methods are abstract; extended methods raise NotImplementedError by default |

**Impact:** Reduces barrier to creating new adapters. Basic adapter can skip observability features.

---

### 11. Result Objects Over Exceptions
Methods return result objects with success/failure status rather than throwing exceptions for expected failures. Caller decides how to handle.

| Status | Location |
|--------|----------|
| Implemented | `PIIScanResult`, `InjectionCheckResult`, `SafetyCheckResult`, `AnalysisResult`, `ActionResult` |

---

## Extensibility Patterns

### 12. Plugin Architecture (Implicit)
Tools, adapters, and middleware are swappable. No explicit plugin registration, but architecture allows extension.

| Status | Location |
|--------|----------|
| Architecturally Supported | List of tools passed to agent; adapters injected; middleware manually composed |

**Missing:** No plugin discovery, no lifecycle hooks, no extension points beyond constructor injection.

---

### 13. Configurable Prompts
System prompts for agent, safety guardrail, injection guard are all injectable. Allows domain-specific customization.

| Status | Location |
|--------|----------|
| Implemented | `ReActAgent(system_prompt=...)`, `SafetyGuardrail(context=..., safety_criteria=...)`, `PromptInjectionGuard(context=..., legitimate_requests=...)` |

---

## Error Handling Design

### 14. Graceful Degradation
System continues functioning with reduced capability rather than failing entirely. Missing optional dependencies don't crash startup.

| Status | Location |
|--------|----------|
| Implemented | No storage → no history; No tracing → None for trace_id; No messaging port → RuntimeError only when used |

**Hidden Philosophy:** Development experience prioritized. Partial configuration is valid.

---

### 15. Error Context Preservation
Exceptions include original error, service name, and context. Enables debugging across abstraction layers.

| Status | Location |
|--------|----------|
| Implemented | `AdapterError(message, original_error, service_name)` in `exceptions.py` |

---

## Data Design

### 16. Immutable Data Transfer
Dataclasses for data structures encourage immutability. No setters, explicit construction.

| Status | Location |
|--------|----------|
| Mostly Implemented | Most dataclasses are effectively immutable; some have mutable default factories |

**Exception:** `CleanupHistory.cycles` is mutable deque; `ContentFilter.banned_keywords` can be modified via `add_keyword()`.

---

### 17. Explicit Optional Fields
Optional fields use `| None` type hints and have default values. No implicit nullability.

| Status | Location |
|--------|----------|
| Implemented | Throughout codebase: `user_id: str | None = None` |

---

### 18. Metadata Extensibility
Records include `metadata: dict` fields for application-specific data. Core doesn't interpret, just passes through.

| Status | Location |
|--------|----------|
| Implemented | `MessageRecord.metadata`, `ConversationRecord.metadata`, `ChatRecord.metadata` |

---

## Implicit Design Decisions (Hidden in Code)

### 19. Single Agent Per Request
Each `process_message()` call is independent. No agent state persists between calls. Conversation continuity via external history only.

| Status | Location |
|--------|----------|
| Implemented | `process_message()` takes `conversation_history` parameter; no instance state |

**Implication:** Horizontal scaling is trivial—any instance can handle any request. But no in-memory conversation caching.

---

### 20. Client-Controlled Session Identity
Session IDs come from client request, not server-generated tokens. Server trusts client to maintain session boundaries.

| Status | Location |
|--------|----------|
| Implemented | `session_id = request.session_id or str(uuid4())` in routes |

**Security Implication:** Anyone who knows a session_id can access that conversation. No authentication layer exists.

---

### 21. Platform-Agnostic Message Model
Messages are reduced to `{role, content}` regardless of source. Platform-specific features (reactions, threads, formatting) are lost in translation.

| Status | Location |
|--------|----------|
| Implemented | `_convert_to_messages()` strips to role/content only |

**Trade-off:** Simplicity over fidelity. Works for basic chat; loses richness for advanced platforms.

---

### 22. Tool Error as Response Content
Tool execution errors become string responses, not exceptions. Agent sees "Error: ..." and can reason about it.

| Status | Location |
|--------|----------|
| Implemented by LangGraph | ToolNode catches exceptions and returns error messages |

**Implication:** Agent might retry, explain the error to user, or try alternative approach. Self-healing behavior.

---

### 23. Two-Phase Message Persistence
User message and agent response saved as separate operations. Not transactional—failure after first save leaves partial state.

| Status | Location |
|--------|----------|
| Implemented | `routes.py:154-161` - two separate `save_message()` calls |

**Risk:** If agent responds but save fails, user gets response but server forgets. History diverges.

---

### 24. Bounded History Loading
Only last N messages loaded (default 50). Prevents unbounded memory growth. Assumes older context is less relevant.

| Status | Location |
|--------|----------|
| Implemented | `limit=50` in `get_conversation()` calls |

**Impact:** Very long conversations lose early context. LLM has recency bias built in.

---

### 25. Fail-Fast on Missing API Keys
API key validation happens at LLM creation, not application startup. Allows starting without all providers configured.

| Status | Location |
|--------|----------|
| Implemented | `_get_openai_llm()` checks `llm_config.openai_api_key` inside function |

**Trade-off:** Development convenience vs. production reliability. Bad key discovered at first use, not deploy time.

---

### 26. No Request Correlation
Requests don't have correlation IDs. Logging happens per-component. Tracing only if explicitly enabled.

| Status | Location |
|--------|----------|
| Not Implemented | No `X-Request-ID` handling; trace_id only with TracingPort |

**Impact on Debugging:** Hard to correlate logs across components for single request. Manual trace_id helps but optional.

---

### 27. Synchronous Agent Invocation in Async Route
Agent's `process_message()` is sync (returns, not awaits). Called from async route without `run_in_executor`. Blocks event loop during LLM call.

| Status | Location |
|--------|----------|
| Implemented (Potential Issue) | `routes.py:145` - `response, trace_id = agent.process_message(...)` |

**Implication:** Under load, long LLM calls block other requests. Should either make agent async or use executor.

---

### 28. Health Check as Capability Probe
Health endpoint checks storage health, but only if storage has `health_check()` method. Gracefully handles missing capability.

| Status | Location |
|--------|----------|
| Implemented | `routes.py:364` - `if storage and hasattr(storage, "health_check")` |

**Pattern:** Feature detection for optional interface methods. Duck typing in practice.
