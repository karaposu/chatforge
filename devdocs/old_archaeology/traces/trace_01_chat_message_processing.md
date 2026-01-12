# Trace 01: Chat Message Processing

The primary interaction path through Chatforge - from HTTP request to response.

---

## Entry Point

**Location:** `adapters/fastapi/routes.py:121` - `chat()` function

**Trigger:** HTTP POST to `/chat` endpoint with JSON body:
```python
{
    "message": str,           # User's message
    "session_id": str | None, # Conversation identifier
    "user_id": str | None,    # User identifier
    "user_email": str | None, # User email
    "metadata": dict | None   # Additional context
}
```

**Initial State:**
- Request validated by Pydantic schema `ChatRequest`
- Session ID generated if not provided: `str(uuid4())`
- User ID defaults to `"anonymous"` if not provided

---

## Execution Path

### Step 1: Session Initialization
```
chat() → session_id = request.session_id or str(uuid4())
       → user_id = request.user_id or "anonymous"
```

**What happens:**
- Session ID ensures conversation continuity
- Anonymous user ID allows tracking without authentication

### Step 2: Conversation History Retrieval
```
chat() → storage.get_conversation(session_id, limit=50)
       → Returns list[MessageRecord]
       → Converted to [{"role": str, "content": str}, ...]
```

**What happens:**
- If `storage` is None, history is empty list
- Storage adapter fetches last 50 messages
- Messages returned in chronological order (oldest first)

**Data transformation:**
```python
# From storage
conv: list[MessageRecord]  # Each has .role, .content, .timestamp, .metadata

# To agent format
history: list[dict[str, str]]  # Simplified to {"role": "user/assistant", "content": "..."}
```

### Step 3: Context Building
```
chat() → context = {
           "user_id": user_id,
           "session_id": session_id,
           "user_email": request.user_email,  # if provided
           **request.metadata                  # merged in
       }
```

**What happens:**
- Context dict assembled for agent and tracing
- Metadata from request merged (allows custom fields)

### Step 4: Agent Processing
```
chat() → agent.process_message(request.message, history, context=context)
       → Returns (response: str, trace_id: str | None)
```

**What happens inside `process_message`:**

1. **Message Conversion** (`engine.py:311-349`):
   ```python
   messages = self._convert_to_messages(history, user_message)
   # Converts to LangChain format:
   # - "user" → HumanMessage
   # - "assistant" → AIMessage (with tool_calls=[] to avoid OpenAI errors)
   ```

2. **Tracing Setup** (`engine.py:351-413`):
   ```python
   if tracing and tracing.enabled:
       with tracing.span("chatforge_agent") as span:
           trace_id = tracing.get_active_trace_id()
           # Set user/session metadata
           # Invoke agent within trace context
   else:
       # Direct invocation without tracing
   ```

3. **ReACT Loop** (LangGraph's `create_react_agent`):
   ```
   while not done:
       REASON: LLM decides next action
       ACT: Execute tool if needed
       OBSERVE: Check tool result
       REPEAT or RESPOND
   ```

4. **Tool Tracking**:
   ```python
   for msg in result["messages"]:
       if hasattr(msg, "tool_calls") and msg.tool_calls:
           # Log each tool invocation
           # Track in metadata dict
   ```

5. **Response Extraction**:
   ```python
   final_message = result["messages"][-1]
   response = final_message.content  # String response
   ```

### Step 5: Message Persistence
```
chat() → storage.save_message(session_id, MessageRecord(user_message))
       → storage.save_message(session_id, MessageRecord(response))
```

**What happens:**
- Both user message and agent response saved atomically
- Conversation updated_at timestamp refreshed
- Creates conversation record if first message

### Step 6: Response Assembly
```
chat() → return ChatResponse(
           response=response,
           session_id=session_id,
           trace_id=trace_id
       )
```

**What happens:**
- Response serialized to JSON
- HTTP 200 returned with structured response

---

## Resource Management

### Memory
- **Conversation history:** Loaded into memory, limited to 50 messages
- **Message objects:** Created per-request, garbage collected after response
- **LangChain messages:** Created during conversion, released after agent invocation

### Database Connections
- **Per-operation connections:** SQLite adapter opens/closes per call
- **No connection pooling:** Each save_message is independent
- **Transaction scope:** Each operation is its own transaction

### Thread Pool
- **Agent processing:** Runs in main async event loop
- **Tool execution:** May use `run_async` bridge for sync tools

---

## Error Path

### Request Validation Error
```
FastAPI → 422 Unprocessable Entity
        → Pydantic validation details in response
```

### Storage Error (History Retrieval)
```
storage.get_conversation() raises
→ Exception bubbles to chat()
→ HTTPException(500, "Error processing request: ...")
→ Logged with exc_info=True
```

### Agent Processing Error
```
agent.process_message() raises
→ Caught in engine.py:299-309
→ Returns ("I apologize, but I encountered an error...", trace_id)
→ Graceful degradation, not HTTP error
```

### Storage Error (Persistence)
```
storage.save_message() raises
→ Exception bubbles to chat()
→ HTTPException(500, "Error processing request: ...")
→ Response already generated but not saved
→ USER GETS RESPONSE but it's not persisted
```

---

## Performance Characteristics

### Latency Components
1. **Storage read:** ~1-10ms (SQLite), higher for remote DBs
2. **Message conversion:** ~0.1ms (in-memory transformation)
3. **LLM call:** 500ms - 30s (dominant factor)
4. **Tool execution:** Variable, 0ms to minutes depending on tool
5. **Storage write:** ~1-10ms per message (2 writes)

### Bottlenecks
- **LLM inference:** Cannot be parallelized within single request
- **Sequential tool calls:** ReACT loop is sequential by design
- **Storage writes:** Two sequential writes per request

### Scalability
- **Horizontal:** Stateless request handling allows multiple instances
- **Storage:** Single SQLite file is bottleneck; use PostgreSQL for scale
- **LLM:** Rate limited by provider

---

## Observable Effects

### On Success
1. User message persisted to storage
2. Agent response persisted to storage
3. Conversation updated_at timestamp refreshed
4. Trace recorded (if tracing enabled)
5. HTTP 200 with response body

### On Partial Failure
1. Agent error → User gets error message, nothing persisted
2. Storage write error → User gets response but conversation state lost

### Logging
- `INFO`: Chat processed with session_id and trace_id
- `INFO`: Tool invocations with names and args
- `DEBUG`: Message counts, response previews
- `ERROR`: Any exceptions with full stack trace

---

## Why This Design

### Session-Based Conversations
**Choice:** Client provides session_id, server generates if missing

**Rationale:**
- Allows stateless API - no server-side session management
- Client controls conversation boundaries
- Simple scaling - any instance can handle any session

**Trade-off:**
- No server-side session validation
- Client can create unlimited sessions

### Graceful Error Handling in Agent
**Choice:** Agent catches errors and returns friendly message

**Rationale:**
- User experience: no cryptic errors
- Partial success: even with tool failures, response returned
- Debugging: trace_id links to full execution log

**Trade-off:**
- Masks underlying issues from user
- May return incomplete information

### Sequential Storage Writes
**Choice:** Save user message, then save agent response separately

**Rationale:**
- Atomic operations are simpler
- Mirrors conversation flow
- Easy to reason about

**Trade-off:**
- Two round trips to storage
- Possible inconsistency if second write fails

---

## What Feels Incomplete

1. **No input middleware integration**
   - PII detection and injection guard exist but aren't wired into routes
   - Must be manually added by application developer
   - Routes are "clean" but unprotected by default

2. **No response middleware integration**
   - SafetyGuardrail exists but not called in routes
   - Agent responses go directly to user
   - Unsafe content could slip through

3. **No retry logic**
   - LLM failures are not retried
   - Storage failures are not retried
   - Single point of failure per operation

4. **Streaming is simulated**
   - `/chat/stream` endpoint exists but chunks pre-generated response
   - TODO comment in code acknowledges this
   - Not true token-by-token streaming

---

## What Feels Vulnerable

1. **No rate limiting**
   - Endpoint accepts unlimited requests
   - No per-user or per-session throttling
   - Denial of wallet via LLM cost exhaustion

2. **No input validation beyond schema**
   - Message length not limited
   - No content filtering before agent
   - Very long messages → high LLM costs

3. **Session ID is user-controlled**
   - Can access any conversation by guessing session_id
   - No authentication required
   - Privacy concern if session_ids are predictable

4. **Storage write failure loses data**
   - If save fails after agent responds, conversation state diverges
   - User has response but server forgot about it
   - Next request will have incomplete history

---

## What Feels Like Bad Design

1. **Direct attribute access on `conv`**
   ```python
   history = [{"role": m.role, "content": m.content} for m in conv.messages]
   ```
   - Code assumes `conv` has `.messages` but `get_conversation` returns `list[MessageRecord]`
   - This is actually a bug - `conv` IS the list, not a container with `.messages`
   - Would fail at runtime

2. **Context dict mutation**
   ```python
   context.update(request.metadata)
   ```
   - Metadata could overwrite user_id or session_id
   - No validation of metadata keys
   - Potential for confusion

3. **Storage optionality**
   - Routes work without storage, but silently lose history
   - No warning that conversations won't persist
   - May confuse developers during testing

4. **Tight coupling to specific response format**
   - Assumes `result["messages"][-1]` is always the response
   - Breaks if LangGraph changes output format
   - No validation of agent output structure
