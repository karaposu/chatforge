# Trace 01: ReActAgent.process_message

The primary entry point for text-based AI conversations. This is the core reasoning loop that powers all chat interactions.

---

## Entry Point

**File:** `chatforge/services/agent/engine.py:198`
**Method:** `ReActAgent.process_message()`

**Signature:**
```python
def process_message(
    self,
    user_message: str,
    conversation_history: list[dict[str, str]],
    context: dict[str, Any] | None = None,
    return_metadata: bool = False,
) -> tuple[str, str | None] | tuple[str, str | None, dict[str, Any]]
```

**Callers:**
- Application code (directly)
- `process_message_with_timeout()` (wraps this with ThreadPoolExecutor)
- Test suites

---

## Execution Path

```
process_message(user_message, conversation_history, context)
    │
    ├─1─► _convert_to_messages(conversation_history, user_message)
    │     │
    │     ├── Iterate conversation_history
    │     │   └── Convert each {role, content} dict to LangChain message
    │     │       ├── "user" → HumanMessage(content)
    │     │       └── "assistant" → AIMessage(content, tool_calls=[])
    │     │                         ↑ Empty tool_calls to avoid OpenAI validation errors
    │     │
    │     └── Append HumanMessage(user_message) for current input
    │         └── Return list[BaseMessage]
    │
    ├─2─► _invoke_with_context(messages, context)
    │     │
    │     ├── Check if tracing is enabled (self.tracing.enabled)
    │     │   │
    │     │   ├── [No tracing] ──────────────────────────────────┐
    │     │   │                                                   │
    │     │   └── [Tracing enabled]                               │
    │     │       │                                               │
    │     │       ├── Create span: tracing.span("chatforge_agent")│
    │     │       │                                               │
    │     │       ├── Set trace metadata (user_id, session_id)    │
    │     │       │                                               │
    │     │       └── Set span inputs (user_message)              │
    │     │                                                       │
    │     └──────────────────────────────────────────────────────┘
    │                           │
    │     ┌─────────────────────┘
    │     ▼
    │     self.agent.invoke({"messages": messages}, config={})
    │     │
    │     │   [Inside LangGraph ReACT Agent - external library]
    │     │   ┌─────────────────────────────────────────────────────┐
    │     │   │ 1. Send messages to LLM                             │
    │     │   │ 2. LLM decides: respond directly OR call tools      │
    │     │   │ 3. If tool call:                                    │
    │     │   │    a. Execute tool via ToolNode                     │
    │     │   │    b. Append tool result to messages                │
    │     │   │    c. Loop back to step 1                           │
    │     │   │ 4. Return final messages when LLM stops calling     │
    │     │   └─────────────────────────────────────────────────────┘
    │     │
    │     └── Return (result_dict, trace_id)
    │
    ├─3─► Extract metadata from result
    │     │
    │     ├── Count tool invocations
    │     │   └── For each message with tool_calls:
    │     │       └── Log tool name, args, id
    │     │
    │     └── Store in metadata dict:
    │         - tool_call_count
    │         - tool_calls (list of {name, args, id})
    │         - message_count
    │
    ├─4─► Extract final response
    │     │
    │     └── result["messages"][-1].content
    │
    └─5─► Return (response, trace_id) or (response, trace_id, metadata)
```

---

## Resource Management

| Resource | Acquisition | Release | Failure Mode |
|----------|-------------|---------|--------------|
| LLM API connection | Per-invoke (no pooling) | Immediate after response | HTTP timeout, API error |
| Trace span | Context manager in `_invoke_with_context` | Automatic on exit | Silently ignored if tracing fails |
| Thread (timeout mode) | ThreadPoolExecutor.submit | Future.result() or timeout | Thread may linger if agent hangs |

**Memory:**
- Conversation history loaded into memory
- All messages held in memory during processing
- No streaming - full response buffered

**Thread Safety:**
- Method is synchronous (blocking)
- Safe to call from multiple threads
- LangGraph agent itself is thread-safe

---

## Error Path

```
Exception during processing
    │
    ├── Catch all exceptions
    │
    ├── Log error with traceback: logger.error(..., exc_info=True)
    │
    └── Return graceful fallback:
        ("I apologize, but I encountered an error...", trace_id)

        Note: trace_id may be None if error occurred before tracing initialized
```

**Specific error scenarios:**

1. **LLM API Error (rate limit, auth, network):**
   - Bubbles up from LangChain
   - Caught by top-level handler
   - Returns generic error message

2. **Tool Execution Error:**
   - Handled by LangGraph's ToolNode with error handling
   - Error message returned to LLM as tool result
   - LLM may retry or acknowledge error

3. **Message Conversion Error:**
   - Rare - basic dict/list operations
   - Would bubble up as generic exception

---

## Performance Characteristics

| Metric | Typical Value | Notes |
|--------|---------------|-------|
| Latency | 1-30s | Dominated by LLM API calls |
| Memory | 10KB-1MB | Depends on conversation length |
| CPU | Minimal | Waiting on I/O |
| Concurrency | Safe | But blocking, ties up thread |

**Bottlenecks:**
1. LLM API response time (network + inference)
2. Tool execution time (if tools used)
3. Multiple LLM round-trips for complex reasoning

**Scaling concerns:**
- Blocking call - needs thread per concurrent request
- No connection pooling for LLM API
- Full conversation loaded per call

---

## Observable Effects

| Effect | Location | Trigger |
|--------|----------|---------|
| Log: "Processing message with N messages" | engine.py | Start of processing |
| Log: "Tool invoked: X with args: Y" | engine.py | Each tool call |
| Log: "Total tool invocations: N" | engine.py | After all tools |
| Log: "Agent final response: ..." | engine.py | Completion |
| Trace span: "chatforge_agent" | TracingPort | If tracing enabled |
| LLM API call | External | Via LangChain |

**No side effects on:**
- Storage (caller must save messages)
- External systems (unless tools do)
- Conversation history (input is not modified)

---

## Why This Design

**LangGraph delegation:**
- Uses `create_react_agent` from LangGraph prebuilt
- Avoids reimplementing ReACT loop
- Benefits from LangGraph's robustness and updates

**Empty tool_calls on AIMessage:**
- OpenAI requires tool_calls to be followed by tool responses
- Reconstructed history from storage doesn't have tool responses
- Setting `tool_calls=[]` prevents validation errors

**Sync-first design:**
- LangGraph's invoke is sync
- Simpler mental model
- `process_message_with_timeout` adds async-like behavior

**Tracing optional:**
- Port pattern allows null adapter
- No overhead when disabled
- Clean separation of concerns

---

## What Feels Incomplete

1. **No streaming support:**
   - Response comes all at once
   - Long responses feel slow
   - No partial updates for UI

2. **No conversation memory management:**
   - Full history passed each time
   - No automatic truncation for context limits
   - Caller responsible for managing history size

3. **No retry logic:**
   - Single attempt to LLM
   - Transient errors cause failure
   - No exponential backoff

4. **Limited metadata:**
   - No token usage tracking
   - No latency breakdown
   - No cost estimation

---

## What Feels Vulnerable

1. **Memory unbounded:**
   - Large conversation histories loaded fully
   - No limit on message count
   - Could OOM with very long conversations

2. **Timeout behavior (process_message_with_timeout):**
   - Uses ThreadPoolExecutor
   - On timeout, thread keeps running
   - No way to cancel in-flight LLM call
   - Resource leak if frequent timeouts

3. **Error messages reveal nothing:**
   - Generic "encountered an error" response
   - No way for user to know what went wrong
   - No correlation ID for debugging

4. **Tracing span not closed on some errors:**
   - If exception before context manager enters
   - trace_id captured but span may be incomplete

---

## What Feels Bad Design

1. **Sync blocking in async world:**
   - Modern Python favors async
   - Blocking ties up thread
   - `process_message_with_timeout` is a workaround, not a solution

2. **Mixed return types:**
   - Returns 2-tuple or 3-tuple based on `return_metadata`
   - Caller must know what to expect
   - Should be single return type with optional fields

3. **Context dict is untyped:**
   - `context: dict[str, Any] | None`
   - No schema for what keys are expected
   - Easy to pass wrong keys

4. **Trace ID handling:**
   - Returns None if tracing disabled
   - Caller must handle None case
   - Could return empty string or "no-trace" sentinel

5. **Tool calls logged but not structured:**
   - Tool execution details only in logs
   - Not returned in metadata unless `return_metadata=True`
   - Should always be available for debugging
