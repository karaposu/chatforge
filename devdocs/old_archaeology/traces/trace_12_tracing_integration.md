# Trace 12: Tracing Integration

How Chatforge integrates with observability platforms for tracing and debugging.

---

## Entry Point

**Location:** `ports/tracing.py:25` - `TracingPort` protocol

**Trigger:**
- Agent initialization with tracing enabled
- Each message processing creates a trace span
- Feedback logging links to traces

**Key Interface:**
```python
class TracingPort(Protocol):
    enabled: bool                              # Is tracing active?
    invoke_with_span(llm, messages, span_name) # LLM call with tracing
    span(name, inputs) → context manager       # Create a span
    get_active_trace_id() → str | None         # Current trace ID
    set_trace_metadata(metadata) → bool        # Add metadata to trace
    log_feedback(context_id, is_positive, ...) # User feedback
    set_platform_context_on_trace(...)         # Link to platform message
```

---

## Execution Path

### Path A: Agent with Tracing (in ReActAgent)

```
ReActAgent.__init__(..., tracing=my_tracing_adapter)
├── Store tracing port
├── Later in process_message:
│   ├── Check if tracing enabled
│   └── If enabled, wrap invocation in span
```

### Path B: Process Message with Tracing

```
ReActAgent.process_message(user_message, history, context)
├── _invoke_with_context(messages, context)
│   ├── Check if tracing enabled
│   │   └── if not tracing or not tracing.enabled:
│   │       └── Invoke directly, return (result, None)
│   ├── Create parent span
│   │   └── with tracing.span("chatforge_agent") as span:
│   ├── Get trace ID
│   │   └── trace_id = tracing.get_active_trace_id()
│   ├── Set user/session metadata
│   │   └── tracing.set_trace_metadata({"user_id": ..., "session_id": ...})
│   ├── Set inputs on span
│   │   └── span.set_inputs({"user_message": ...})
│   ├── Invoke agent
│   │   └── result = self.agent.invoke({"messages": messages}, config={})
│   ├── Set outputs on span
│   │   └── span.set_outputs({"response": ...})
│   └── Return (result, trace_id)
```

### Path C: NullTracingAdapter (No-op)

```
NullTracingAdapter.span(name, inputs)
├── yield None  # No span created
└── No-op on exit

NullTracingAdapter.get_active_trace_id()
└── return None

NullTracingAdapter.set_trace_metadata(metadata)
└── return False  # Nothing happened

NullTracingAdapter.log_feedback(...)
└── return False  # Not logged
```

### Path D: Typical MLflow/Langsmith Implementation

```
# Hypothetical MLflowTracingAdapter

def span(self, name, inputs):
    with mlflow.start_span(name) as span:
        if inputs:
            span.set_inputs(inputs)
        yield span
    # Span auto-closed

def get_active_trace_id(self):
    return mlflow.get_current_active_span().request_id

def log_feedback(self, context_id, is_positive, user_id, rationale):
    # Find trace by context_id
    trace = self._lookup_trace_by_context(context_id)
    if trace:
        mlflow.log_feedback(
            trace_id=trace.id,
            score=1.0 if is_positive else 0.0,
            comment=rationale,
            user_id=user_id
        )
        return True
    return False
```

---

## Resource Management

### Trace Context
- Automatically propagated within span context manager
- Thread-local or context-var based (implementation-dependent)
- Cleaned up when span exits

### Span Lifecycle
```python
with tracing.span("operation") as span:
    # Span is active
    # Nested operations inherit context
    pass
# Span is closed, data flushed
```

### No Built-in Batching
- Each span potentially creates network call
- Implementations should batch/buffer internally
- High volume could be expensive

---

## Error Path

### Tracing Disabled
```python
if not tracing or not tracing.enabled:
    agent_result = self.agent.invoke(...)
    return agent_result, None  # No trace_id
```
- Silent fallback
- No error thrown
- Returns None for trace_id

### Span Context Errors
```python
# If span() raises, exception propagates
# No defensive handling in agent code
# Could crash processing
```

### Feedback Logging Failure
```python
def log_feedback(...) -> bool:
    # Returns False on failure
    # Caller can check but might ignore
```

---

## Performance Characteristics

### Overhead (Approximate)
| Operation | Null Adapter | Real Adapter |
|-----------|--------------|--------------|
| span() creation | ~0.01ms | ~0.1-1ms |
| set_inputs/outputs | ~0.01ms | ~0.1ms |
| get_active_trace_id | ~0.01ms | ~0.05ms |
| log_feedback | ~0.01ms | ~10-100ms (network) |

### Memory
- Null adapter: negligible
- Real adapter: depends on buffering strategy
- Trace data accumulates until flushed

### Network
- Real adapters make API calls
- May batch multiple spans
- Async flush preferred

---

## Observable Effects

### Trace Created
```
Trace ID: abc123-def456
├── Span: chatforge_agent
│   ├── Inputs: {"user_message": "Hello"}
│   ├── Outputs: {"response": "Hi there!"}
│   ├── Metadata: {"user_id": "user@example.com", "session_id": "sess-789"}
│   └── Duration: 1234ms
```

### Feedback Logged
```
Feedback for trace abc123:
├── Score: 1.0 (positive)
├── User: user@example.com
└── Comment: "Helpful response"
```

### Logging (in ReActAgent)
```python
logger.debug(f"Set trace metadata: user={user_id}, session={session_id}")
logger.debug(f"Agent execution traced with ID: {trace_id}")
```

---

## Why This Design

### Protocol-Based Interface
**Choice:** TracingPort as Protocol, not ABC

**Rationale:**
- Structural subtyping (duck typing)
- No inheritance required
- Easy to adapt existing tracing clients

**Trade-off:**
- Less explicit contract
- No abstract method enforcement
- Could miss methods

### Optional Tracing
**Choice:** Tracing is injectable and optional

**Rationale:**
- Not all apps need tracing
- Avoids MLflow/Langsmith dependency
- Performance when disabled

**Trade-off:**
- Must check enabled everywhere
- Easy to forget tracing setup
- Runtime discovery of issues

### Null Object Pattern
**Choice:** NullTracingAdapter for disabled state

**Rationale:**
- No if-checks needed
- Always valid to call
- Clean code

**Trade-off:**
- Silent no-ops
- Can mask configuration errors
- Returns False for operations

### Context-Based Trace ID
**Choice:** Trace ID from active context

**Rationale:**
- Works with nested spans
- Automatic propagation
- Standard tracing pattern

**Trade-off:**
- Relies on context management
- Thread-local issues possible
- Hard to debug

---

## What Feels Incomplete

1. **No concrete implementation**
   - Only NullTracingAdapter exists
   - No MLflow, Langsmith, or OpenTelemetry adapter
   - Must build from scratch

2. **No span attributes/tags**
   ```python
   span.set_inputs(...)
   span.set_outputs(...)
   # But no span.set_attribute("key", "value")
   ```
   - Limited to inputs/outputs
   - Can't add custom dimensions
   - Standard tracing supports more

3. **No child spans**
   - Single chatforge_agent span
   - Tool calls not traced separately
   - Lost granularity

4. **No error recording**
   ```python
   # No span.record_exception(e)
   # Errors not captured in traces
   ```
   - Errors only in logs
   - Not correlated with traces
   - Debugging harder

5. **invoke_with_span not used**
   ```python
   def invoke_with_span(self, llm, messages, span_name, ...):
   ```
   - Defined in interface
   - Not called by agent code
   - Seemingly dead interface

---

## What Feels Vulnerable

1. **Span not in try-finally**
   ```python
   with tracing.span("chatforge_agent") as span:
       # If exception here, span may not close properly
       result = self.agent.invoke(...)
   ```
   - Context manager should handle
   - But implementation could leak
   - No explicit error handling

2. **Trace ID returned to user**
   ```python
   return ChatResponse(
       response=response,
       session_id=session_id,
       trace_id=trace_id,  # Exposed in API
   )
   ```
   - Internal ID visible externally
   - Could be used for reconnaissance
   - May leak system info

3. **set_trace_metadata accepts any dict**
   ```python
   def set_trace_metadata(self, metadata: dict[str, str]) -> bool:
   ```
   - No validation
   - Could overflow trace storage
   - PII could be logged

4. **Platform context exposure**
   ```python
   def set_platform_context_on_trace(self, trace_id, platform_context):
   ```
   - Links internal traces to external platforms
   - If trace is public, context exposed
   - Privacy concern

5. **No auth on feedback**
   ```python
   def log_feedback(self, context_id, is_positive, user_id, rationale):
   ```
   - user_id is just a string
   - No verification user owns the trace
   - Could fake feedback

---

## What Feels Like Bad Design

1. **@runtime_checkable Protocol**
   ```python
   @runtime_checkable
   class TracingPort(Protocol):
   ```
   - Allows isinstance checks
   - But Protocol is for static typing
   - Mixing runtime and static concepts

2. **abstractmethod on Protocol**
   ```python
   @property
   @abstractmethod
   def enabled(self) -> bool:
   ```
   - Protocol methods don't need @abstractmethod
   - It's implied by Protocol
   - Redundant decorator

3. **NullTracingAdapter not implementing Protocol**
   ```python
   class NullTracingAdapter:  # No explicit Protocol inheritance
   ```
   - Duck typing works
   - But explicit is better
   - Type checker may miss issues

4. **invoke_with_span vs span**
   ```python
   def invoke_with_span(self, llm, messages, span_name, ...):
   def span(self, name, inputs):
   ```
   - Two ways to create spans
   - invoke_with_span is specialized for LLM
   - Confusing which to use

5. **Boolean returns for mutations**
   ```python
   def set_trace_metadata(...) -> bool:
   def log_feedback(...) -> bool:
   ```
   - Returns True/False for success
   - But no error information
   - Should raise or return detailed result

6. **span context manager yields Any**
   ```python
   @contextmanager
   def span(self, name, inputs) -> Generator[Any, None, None]:
   ```
   - Yields implementation-specific span
   - Caller must know type
   - No common interface for span operations
