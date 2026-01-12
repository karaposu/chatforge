# Trace 09: Tool Execution Pattern (AsyncAwareTool)

The abstraction for agent tools that handles sync/async bridging. Enables tools to be called from both sync and async contexts.

---

## Entry Point

**File:** `chatforge/services/agent/tools/base.py:47`
**Class:** `AsyncAwareTool` (extends LangChain's `BaseTool`)

**Primary Methods:**
```python
def _run(self, **kwargs) -> Any           # Called by LangChain (sync)
async def _arun(self, **kwargs) -> Any    # Called by LangChain (async)
async def _execute_async(self, **kwargs) -> Any  # User implements this
```

**Callers:**
- LangGraph's ToolNode (via LangChain tool interface)
- Direct tool invocation in tests
- Agent orchestration

---

## Execution Path: LangGraph Tool Invocation

```
ReActAgent calls tool via LangGraph
    │
    ├─► LangGraph ToolNode receives tool_call from LLM
    │   {
    │     "name": "search_knowledge",
    │     "arguments": {"query": "how to reset password"}
    │   }
    │
    ├─► ToolNode looks up tool by name
    │
    ├─► ToolNode calls tool._run(**arguments) [sync context]
    │   │
    │   │   [Inside AsyncAwareTool._run]
    │   │
    │   └─► _run(self, **kwargs)
    │       │
    │       └── return run_async(self._arun(**kwargs))
    │           │
    │           │   [run_async from chatforge.utils.async_bridge]
    │           │
    │           └── asyncio.run(coro)
    │               │
    │               ├── Create new event loop
    │               ├── Run coroutine to completion
    │               └── Close event loop
    │
    │       OR (if already in async context)
    │
    └─► ToolNode calls await tool._arun(**arguments) [async context]
        │
        │   [Inside AsyncAwareTool._arun]
        │
        └─► _arun(self, **kwargs)
            │
            └── return await self._execute_async(**kwargs)
```

---

## Execution Path: _execute_async (User Implementation)

```
_execute_async(self, query: str) -> str
    │
    ├─► [User's tool logic]
    │   │
    │   ├── Access ports (knowledge, ticketing, etc.)
    │   │
    │   ├── Call external APIs
    │   │
    │   └── Format result for LLM
    │
    └─► Return string result (or structured data)
```

**Example: Knowledge Search Tool**
```python
class KnowledgeSearchTool(AsyncAwareTool):
    name = "search_knowledge"
    description = "Search the knowledge base for information"
    knowledge_port: KnowledgePort

    async def _execute_async(self, query: str) -> str:
        results = self.knowledge_port.search(query)
        return self.knowledge_port.format_search_results(results)
```

---

## Tool Schema Definition

```python
class MyToolInput(BaseModel):
    """Input schema for my tool."""
    query: str = Field(description="The search query")
    limit: int = Field(default=5, description="Max results")

class MyTool(AsyncAwareTool):
    name: str = "my_tool"
    description: str = "Does something useful"
    args_schema: type[BaseModel] = MyToolInput

    async def _execute_async(self, query: str, limit: int = 5) -> str:
        # kwargs come from args_schema
        ...
```

---

## Resource Management

| Resource | Acquisition | Release | Failure Mode |
|----------|-------------|---------|--------------|
| Event loop (sync path) | asyncio.run() | Immediate | Loop per call |
| Thread pool | run_sync() if needed | Shared executor | Thread leak |
| Tool ports | Constructor injection | Never | Held reference |

**Critical:** `_run()` creates new event loop each call. Cannot be used if already in async context.

---

## Error Path

```
Tool execution error:
    │
    ├─► Exception in _execute_async
    │   │
    │   └── Exception propagates to LangGraph ToolNode
    │       │
    │       ├── ToolNode has handle_tool_error=True:
    │       │   └── Error message returned to LLM as tool result
    │       │       └── LLM can retry or acknowledge error
    │       │
    │       └── ToolNode has handle_tool_error=False:
    │           └── Exception bubbles up, agent fails
    │
    └─► Event loop error (nested loop):
        │
        └── RuntimeError: "This event loop is already running"
            │
            └── Happens if _run() called from async context
                └── Should use _arun() instead
```

---

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| _run() overhead | 1-10ms | Event loop creation |
| _arun() overhead | <1ms | Direct await |
| Tool latency | Varies | Depends on implementation |

**Event loop creation:**
- `asyncio.run()` creates new loop
- Overhead per sync call
- Adds up with many tool calls

---

## Observable Effects

| Effect | Location | Trigger |
|--------|----------|---------|
| Log: "Tool invoked: X" | engine.py | ReActAgent logs tool calls |
| External API calls | Tool implementation | _execute_async |
| Port interactions | Tool implementation | _execute_async |

**No logging in base class.** Tools should log their own activity.

---

## Why This Design

**Unified implementation:**
- Write once in `_execute_async`
- Works from sync or async
- No duplication

**LangChain compatibility:**
- Extends BaseTool
- Works with LangGraph
- Inherits tool protocol

**Args schema via Pydantic:**
- Type validation
- Description for LLM
- Default values

---

## What Feels Incomplete

1. **No retry logic:**
   - Tool fails once, done
   - No exponential backoff
   - Transient errors cause failure

2. **No timeout:**
   - Tool can run forever
   - No way to cancel
   - Agent hangs on slow tools

3. **No result validation:**
   - Any return value accepted
   - No schema for output
   - LLM may not understand result

4. **No caching:**
   - Same args hit tool each time
   - No memoization
   - Wasteful for repeated queries

5. **No metrics:**
   - No latency tracking
   - No error rate
   - No usage stats

---

## What Feels Vulnerable

1. **Event loop nesting:**
   - `_run()` can't be called from async
   - Silent failure mode
   - Hard to debug

2. **Tool output injection:**
   - Tool result sent to LLM
   - Malicious result could manipulate LLM
   - No output sanitization

3. **Port access unrestricted:**
   - Tools have direct port access
   - No permission model
   - One tool could abuse another's port

4. **Exception details exposed:**
   - Error message goes to LLM
   - Could reveal system details
   - Should sanitize error messages

---

## What Feels Bad Design

1. **Three method names:**
   - `_run`, `_arun`, `_execute_async`
   - Confusing which to implement
   - Should be single name

2. **BaseTool inheritance deep:**
   - LangChain's BaseTool is complex
   - Many inherited behaviors
   - Hard to understand full behavior

3. **args_schema separate from method:**
   - Schema defined as class attribute
   - Method params must match
   - No enforcement

4. **No dependency injection pattern:**
   - Ports assigned as attributes
   - Must set after construction
   - Should be constructor params

5. **Sync bridge creates event loops:**
   - Expensive
   - Pollutes with many loops
   - Should use shared loop
