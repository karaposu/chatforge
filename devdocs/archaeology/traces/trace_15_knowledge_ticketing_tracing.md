# Trace 15: Knowledge, Ticketing, and Tracing Ports

Remaining domain ports for knowledge retrieval, ticketing integration, and observability.

---

## KnowledgePort

**File:** `chatforge/ports/knowledge.py:73`
**Interface:** `KnowledgePort` (Abstract Base Class)

### Methods

```python
def search(query: str, limit: int = 5) -> list[KnowledgeResult]
def get_context_for_rag(query: str, max_tokens: int = 1000) -> str
def get_page_content(page_id: str) -> str | None
```

### Execution Path: RAG Integration

```
User asks question
    │
    ├─► knowledge.search(query)
    │   │
    │   └── Search knowledge base (Notion, Confluence, etc.)
    │       │
    │       └── Return list[KnowledgeResult]
    │           ├── title: str
    │           ├── content: str
    │           ├── url: str | None
    │           ├── relevance_score: float
    │           ├── source: str
    │           └── metadata: KnowledgeMetadata
    │
    ├─► Format for RAG injection
    │   │
    │   └── context = knowledge.get_context_for_rag(query, max_tokens=1000)
    │       │
    │       ├── Search internally
    │       ├── Format results
    │       └── Return string for system prompt
    │
    └─► Inject into agent
        │
        └── System prompt: "Use this context: {context}"
```

### Data Types

```python
class KnowledgeResult:
    title: str
    content: str
    url: str | None
    relevance_score: float  # 0.0 - 1.0
    source: str             # "notion", "confluence", etc.
    metadata: KnowledgeMetadata | None

class KnowledgeMetadata(TypedDict, total=False):
    page_id: str
    database_id: str
    last_edited: str
    created_by: str
    tags: list[str]
    category: str
```

### What Feels Incomplete

1. **Sync-only methods** - No async variants
2. **No vector search support** - Just text search implied
3. **No chunking for large pages** - `get_page_content` returns all
4. **No write operations** - Read-only interface
5. **max_tokens is approximate** - No tokenizer integration

---

## TicketingPort

**File:** `chatforge/ports/ticketing.py:151`
**Interface:** `TicketingPort` (Abstract Base Class)

### Methods

```python
def execute(data: ActionData) -> ActionResult
def attach_file(action_id: str, file_path: str, filename: str) -> bool
def get_action(action_id: str) -> dict[str, Any] | None
def add_comment(action_id: str, comment: str) -> bool
def update_status(action_id: str, status: str) -> bool
```

### Execution Path: Ticket Creation

```
Agent decides to create ticket
    │
    ├─► Build ActionData
    │   │
    │   └── ActionData(
    │           title="Reset password for user@co.com",
    │           description="User reported...",
    │           action_type="support_ticket",
    │           priority=ActionPriority.HIGH,
    │           requester_email="user@co.com",
    │           category="access",
    │           attachments=[ActionAttachment(...)],
    │           custom_fields={...},
    │       )
    │
    ├─► Execute via port
    │   │
    │   └── result = ticketing.execute(data)
    │       │
    │       └── ActionResult(
    │               action_id="TICKET-1234",
    │               action_url="https://jira.example.com/...",
    │               success=True,
    │               attached_files=["log.txt"],
    │           )
    │
    └─► Return result to agent/user
        │
        └── "Created ticket TICKET-1234"
```

### Data Types

```python
class ActionPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ActionAttachment:
    file_path: str    # Local temp file
    filename: str     # Display name
    mimetype: str

class ActionData:
    title: str
    description: str
    action_type: str = "task"
    priority: ActionPriority = ActionPriority.MEDIUM
    requester_email: str | None
    category: str | None
    attachments: list[ActionAttachment]
    custom_fields: ActionCustomFields
```

### What Feels Incomplete

1. **Sync-only methods** - No async
2. **No search/list** - Can't query existing tickets
3. **No transition validation** - Any status accepted
4. **No bulk operations** - One ticket at a time
5. **No webhook/event support** - Polling only

---

## TracingPort

**File:** `chatforge/ports/tracing.py:25`
**Interface:** `TracingPort` (Protocol, not ABC)

### Methods

```python
@property
def enabled(self) -> bool
def invoke_with_span(llm, messages, span_name, inputs, ...) -> Any
@contextmanager
def span(name: str, inputs: dict) -> Generator[Any, None, None]
def get_active_trace_id() -> str | None
def set_trace_metadata(metadata: dict[str, str]) -> bool
def log_feedback(context_id, is_positive, user_id, rationale) -> bool
def set_platform_context_on_trace(trace_id, platform_context) -> bool
```

### Execution Path: Traced LLM Call

```
ReActAgent processing
    │
    ├─► Check tracing enabled
    │   │
    │   └── if tracing.enabled:
    │       │
    │       └── with tracing.span("chatforge_agent", inputs={...}):
    │           │
    │           ├── Set metadata
    │           │   └── tracing.set_trace_metadata({
    │           │           "user_id": "U123",
    │           │           "session_id": "S456",
    │           │       })
    │           │
    │           ├── Invoke LLM with span
    │           │   └── result = tracing.invoke_with_span(
    │           │           llm=self.llm,
    │           │           messages=messages,
    │           │           span_name="agent_reasoning",
    │           │       )
    │           │
    │           └── Get trace ID
    │               └── trace_id = tracing.get_active_trace_id()
    │
    └─► After response, link feedback
        │
        └── tracing.set_platform_context_on_trace(
                trace_id,
                {"slack_message_id": "M789"},
            )
```

### NullTracingAdapter

```python
class NullTracingAdapter:
    """No-op implementation when tracing disabled."""

    @property
    def enabled(self) -> bool:
        return False

    def invoke_with_span(self, llm, messages, ...):
        return llm.invoke(messages)  # Just invoke, no span

    @contextmanager
    def span(self, name, inputs=None):
        yield None  # No-op context manager

    def get_active_trace_id(self):
        return None

    # Other methods return False/None
```

### What Feels Incomplete

1. **No metrics integration** - Only traces, no counters/gauges
2. **No sampling** - All-or-nothing tracing
3. **No async variants** - Sync context managers
4. **No parent span management** - Flat spans only shown
5. **No export configuration** - Implementation handles

---

## Common Patterns Across Ports

### Null Object Pattern

All three ports have null implementations:
- `NullKnowledgeAdapter` - Returns empty results
- `NullTicketingAdapter` - Returns fake success
- `NullTracingAdapter` - No-ops everything

### Sync vs Async

| Port | Style | Rationale |
|------|-------|-----------|
| KnowledgePort | Sync | Often CPU-bound search |
| TicketingPort | Sync | Legacy API compatibility |
| TracingPort | Sync | Context manager pattern |

Should all be async for consistency.

### Error Handling

| Port | Pattern | Issue |
|------|---------|-------|
| KnowledgePort | Exceptions bubble | No defined exceptions |
| TicketingPort | Returns bool/None | Silent failures |
| TracingPort | Returns bool | Silent failures |

Inconsistent - should define port-specific exceptions.

---

## What Feels Vulnerable

1. **KnowledgePort search injection:**
   - User query passed directly to search
   - No sanitization
   - Could exploit search backend

2. **TicketingPort creates with user input:**
   - Title/description from agent
   - Could contain malicious content
   - No validation in port

3. **TracingPort stores sensitive data:**
   - Messages logged to trace
   - PII could be captured
   - No automatic redaction

4. **Custom fields are dict[str, Any]:**
   - No schema validation
   - Could inject unexpected types
   - Backend may error

---

## What Feels Bad Design

1. **Three different null patterns:**
   - NullKnowledge returns []
   - NullTicketing returns fake success
   - NullTracing returns False
   - Inconsistent

2. **KnowledgeMetadata is TypedDict:**
   - But optional (total=False)
   - Weak typing
   - Should be dataclass

3. **TracingPort is Protocol, others are ABC:**
   - Mixed patterns
   - TracingPort uses @runtime_checkable
   - Inconsistent interface style

4. **format_message in ActionResult:**
   - Business logic in data class
   - Should be separate
   - Mixing concerns

5. **No version/compatibility:**
   - Ports evolve
   - No way to check version
   - Breaking changes unclear
