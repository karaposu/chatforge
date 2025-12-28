# Design Philosophy (From Code Analysis)

Implicit principles, patterns, and decisions evident in the codebase structure and implementation choices.

---

## Core Philosophy: Toolkit Over Framework

The most fundamental design decision visible throughout the codebase:

> **Chatforge provides building blocks, not a prescriptive structure.**

### Evidence

1. **No base application class to inherit from**
   - Users compose `ReActAgent`, storage, routes as needed
   - No `ChatforgeApp.configure()` or similar entry point

2. **All dependencies are injectable**
   ```python
   # Everything is optional or has defaults
   ReActAgent(
       tools=[],           # Optional
       system_prompt=None, # Optional
       messaging_port=None,# Optional
       tracing=None,       # Optional
       llm=None            # Falls back to factory
   )
   ```

3. **Middleware not pre-wired**
   - PII detector, injection guard, safety guardrail exist
   - Developer must explicitly wire them into routes
   - No automatic security pipeline

4. **Router is created, not inherited**
   ```python
   router = create_chat_router(agent, storage, cleanup_runner)
   app.include_router(router)  # User controls where/how
   ```

---

## Implicit Design Principles

### 1. Progressive Enhancement

**Principle:** Start simple, add complexity as needed.

**Evidence:**
- InMemory storage works without any database
- Null adapters for every optional port
- Missing tracing returns `None`, doesn't crash
- Missing storage means ephemeral conversations

**Pattern:** Every optional dependency has a sensible degraded behavior.

---

### 2. Fail-Open For Development, Fail-Closed For Production (Aspirational)

**Principle:** Don't block developers during development; require explicit hardening for production.

**Evidence:**
```python
# Current: Fail-open
except Exception as e:
    logger.error(f"Error (failing open): {e}")
    return InjectionCheckResult(is_injection=False)  # Let through
```

**Implication:** The codebase is optimized for development experience. Production hardening is the user's responsibility.

---

### 3. Configuration Over Convention

**Principle:** Make everything configurable rather than assuming conventions.

**Evidence:**
- System prompts are parameters, not files in specific locations
- Storage backends are injected, not auto-detected
- LLM provider is explicit, not inferred from environment

**Counter-Evidence (12-Factor Pattern):**
- API keys come from environment variables
- Config singletons created at import time

**Resolution:** External configuration (environment) for deployment settings; explicit parameters for business logic.

---

### 4. Interface Segregation

**Principle:** Many small interfaces rather than one large one.

**Evidence:**
- `StoragePort` has "legacy interface" (required) and "extended interface" (optional)
- Adapters can implement minimum viable functionality
- `hasattr()` checks for optional methods

```python
# Health check uses feature detection
if storage and hasattr(storage, "health_check"):
    is_healthy = await storage.health_check()
```

---

### 5. Explicit Over Implicit

**Principle:** Prefer explicit wiring over magic auto-discovery.

**Evidence:**
- Tools explicitly listed in `ReActAgent(tools=[...])`
- No plugin auto-loading from directories
- No decorator-based registration
- Adapters explicitly instantiated and injected

**Trade-off:** More boilerplate, but clear execution paths.

---

## Coding Patterns Consistently Used

### Pattern 1: Factory Functions for Complex Construction

**Usage:** LLM creation, router creation, tool creation

```python
# Factory hides complexity
llm = get_llm(provider="openai", model="gpt-4o-mini")

# User doesn't see:
# - API key validation
# - Provider-specific imports
# - Default parameter handling
```

**Locations:**
- `services/llm/factory.py`: `get_llm()`, `get_streaming_llm()`, `get_vision_llm()`
- `adapters/fastapi/routes.py`: `create_chat_router()`
- `services/agent/tools/base.py`: `create_tool()`

---

### Pattern 2: Result Objects Over Exceptions

**Usage:** Security checks, tool execution, analysis operations

```python
# Instead of raising exceptions:
result = pii_detector.scan(message)
if result.has_pii:
    # Handle detected PII

# Instead of:
try:
    pii_detector.scan(message)
except PIIFoundError as e:
    # Handle
```

**Result Types:**
- `PIIScanResult`
- `InjectionCheckResult`
- `SafetyCheckResult`
- `AnalysisResult`
- `ActionResult`

**Rationale:** Caller decides how to handle; no silent failures; type-safe handling.

---

### Pattern 3: Null Object For Optional Dependencies

**Usage:** All optional ports

```python
class NullKnowledgeAdapter(KnowledgePort):
    def search(self, query: str) -> list[KnowledgeResult]:
        return []  # Works, just empty
```

**Benefit:** Eliminates null checks throughout codebase:
```python
# No need for:
if knowledge_port is not None:
    results = knowledge_port.search(query)

# Just:
results = knowledge_port.search(query)  # Returns [] if null adapter
```

---

### Pattern 4: Async-First With Sync Wrappers

**Usage:** Middleware, tools

```python
class PromptInjectionGuard:
    async def check_message(self, message: str) -> InjectionCheckResult:
        # Primary implementation

    def check_message_sync(self, message: str) -> InjectionCheckResult:
        return run_async(self.check_message(message))
```

**Rationale:** Modern Python is async; sync wrappers for compatibility with sync contexts (tools, tests).

---

### Pattern 5: Template Method For Tool Implementation

**Usage:** All custom tools

```python
class AsyncAwareTool(BaseTool):
    def _run(self, *args, **kwargs):
        # Template: bridge to async
        return run_async(self._execute_async(*args, **kwargs))

    async def _arun(self, *args, **kwargs):
        # Template: delegate to implementation
        return await self._execute_async(*args, **kwargs)

    async def _execute_async(self, *args, **kwargs):
        raise NotImplementedError  # Subclass implements this only
```

**Benefit:** Tool authors implement one method; base handles sync/async complexity.

---

### Pattern 6: Lazy Initialization

**Usage:** Database tables, provider imports, executor creation

```python
# Tables created on first use, not construction
async def _ensure_tables(self):
    if self._tables_created:
        return
    # Create tables...

# Imports inside functions
def _get_openai_llm():
    from langchain_openai import ChatOpenAI  # Not at module level
```

**Rationale:** Faster imports, optional dependencies don't fail at load time.

---

### Pattern 7: Bounded Collections

**Usage:** History retrieval, cleanup tracking

```python
# Message history limited
messages = await storage.get_conversation(session_id, limit=50)

# Cleanup history bounded
self._history = CleanupHistory(max_cycles=100)  # Deque with maxlen
```

**Rationale:** Prevent unbounded memory growth; recency assumption.

---

## Architectural Decisions Evident in Structure

### Decision 1: Hexagonal Architecture

**Evidence:** Directory structure mirrors the pattern:
```
chatforge/
├── ports/          # Abstract interfaces (inner hexagon)
├── adapters/       # Implementations (outer hexagon)
├── services/       # Domain logic (core)
├── middleware/     # Cross-cutting concerns
└── config/         # External configuration
```

**Implication:** Services depend on ports, never on adapters. Adapters are swappable.

---

### Decision 2: LangChain/LangGraph As Foundation

**Evidence:**
- `ReActAgent` wraps `create_react_agent` from LangGraph
- LLM factory returns `BaseChatModel` from LangChain
- Message types are `HumanMessage`, `AIMessage` from LangChain

**Implication:** Chatforge is a convenience layer over LangChain, not a replacement. LangChain expertise transfers.

---

### Decision 3: Stateless Request Processing

**Evidence:**
```python
def process_message(self, message, conversation_history, ...):
    # History passed in, not stored
    # No instance state between calls
```

**Implication:**
- Horizontal scaling trivial (any instance handles any request)
- No in-memory caching of conversations
- State externalized to storage

---

### Decision 4: Client-Controlled Session Identity

**Evidence:**
```python
session_id = request.session_id or str(uuid4())
# Client provides ID; server trusts it
```

**Implication:**
- No server-side session management
- Session hijacking possible if IDs guessable
- Assumes authentication handled externally

---

### Decision 5: Security As Opt-In Middleware

**Evidence:**
- Security components exist in `middleware/`
- Not wired into routes by default
- Each has constructor for customization

**Implication:**
- Maximum flexibility for different security needs
- Risk of forgetting to enable security
- Developer responsibility, not framework guarantee

---

### Decision 6: Single-Tenant Assumption

**Evidence:**
- No tenant ID in any data structure
- Storage has no namespace concept
- Config singletons are global

**Implication:**
- One deployment = one tenant
- Multi-tenant requires wrapper or fork
- SaaS deployment would need significant work

---

## Hidden Assumptions

### Assumption 1: LLM Calls Are Reliable Enough

- No circuit breaker implementation
- Retry handled by LangChain (3 retries default)
- No fallback provider chain

### Assumption 2: Storage Is Fast

- History fetched on every request
- No caching layer (except image analysis)
- No read replicas or connection pooling

### Assumption 3: Messages Are Text

- Content stored as string
- No structured content (cards, buttons, carousels)
- Platform-specific richness lost in translation

### Assumption 4: 50 Messages Is Enough Context

- `limit=50` hardcoded for history retrieval
- No summarization of older context
- Recency bias built into system

---

## Summary

The Chatforge philosophy can be summarized as:

1. **Toolkit, not framework** — Compose pieces, don't inherit structure
2. **Progressive enhancement** — Start minimal, add complexity when needed
3. **Explicit wiring** — No magic auto-discovery; clear execution paths
4. **Fail gracefully** — Missing dependencies degrade, don't crash
5. **Async-first** — Modern Python patterns with sync compatibility
6. **Developer responsibility** — Security, scaling, monitoring are opt-in

This philosophy optimizes for:
- Fast prototyping
- Clear debugging
- Flexible deployment
- Learning curve minimization

At the cost of:
- More boilerplate
- No "batteries included" security
- Production hardening left to user
- Multi-tenant complexity not addressed
