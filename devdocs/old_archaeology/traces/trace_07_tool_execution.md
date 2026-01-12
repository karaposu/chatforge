# Trace 07: Tool Execution

How agent tools are defined, invoked, and how they bridge sync/async boundaries.

---

## Entry Point

**Location:** `services/agent/tools/base.py:43` - `AsyncAwareTool` class

**Trigger:**
1. Tool definition by developer subclassing `AsyncAwareTool`
2. Agent invokes tool during ReACT loop
3. Direct tool invocation via `tool.run()` or `tool.arun()`

**Key Components:**
```python
AsyncAwareTool          # Base class with sync/async bridging
create_tool(name, description, func)  # Factory function
```

---

## Execution Path

### Path A: Tool Definition

```
class MyTool(AsyncAwareTool):
    name: str = "my_tool"
    description: str = "Does something useful"
    args_schema: type[BaseModel] = MyToolInput  # Pydantic model

    async def _execute_async(self, query: str, limit: int = 5, **kwargs) -> str:
        # All tool logic goes here
        result = await some_async_operation(query, limit)
        return f"Found: {result}"
```

**Inheritance chain:**
```
AsyncAwareTool
    └── extends BaseTool (LangChain)
        └── Provides _run() and _arun() entry points
```

### Path B: Sync Invocation (_run)

```
tool._run(**kwargs)
├── Import run_async from chatforge.utils
├── Call _execute_async(**kwargs)
├── run_async creates new event loop
├── Event loop runs coroutine to completion
├── Return result
└── Event loop destroyed
```

**Code path:**
```python
def _run(self, **kwargs: Any) -> str:
    from chatforge.utils import run_async
    return run_async(self._execute_async(**kwargs))
```

### Path C: Async Invocation (_arun)

```
await tool._arun(**kwargs)
├── Directly await _execute_async(**kwargs)
├── No event loop creation
├── Return result
```

**Code path:**
```python
async def _arun(self, **kwargs: Any) -> str:
    return await self._execute_async(**kwargs)
```

### Path D: Agent Tool Invocation (LangGraph)

```
ReACT Agent Loop
├── LLM decides to use tool
│   └── Response includes tool_calls with name and args
├── LangGraph ToolNode receives call
├── ToolNode calls tool.invoke() or tool.ainvoke()
│   └── Which internally calls _run() or _arun()
├── Tool executes _execute_async()
├── Result returned to ToolNode
├── ToolNode creates ToolMessage with result
└── Agent continues reasoning with tool result
```

### Path E: Factory Function (create_tool)

```
create_tool(name, description, func, args_schema=None)
├── Define dynamic subclass of AsyncAwareTool
│   ├── Set name and description as class attributes
│   └── Implement _execute_async to call provided func
├── If args_schema provided, set on class
├── Instantiate and return tool
```

**Code:**
```python
def create_tool(name, description, func, args_schema=None):
    class DynamicTool(AsyncAwareTool):
        name: str = name
        description: str = description

        async def _execute_async(self, **kwargs):
            return await func(**kwargs)

    if args_schema:
        DynamicTool.args_schema = args_schema

    return DynamicTool()
```

---

## Resource Management

### Event Loop (Sync Path)
```python
# In run_async (utils/async_bridge.py)
def run_async(coro):
    return asyncio.run(coro)  # Creates new loop, runs, destroys
```
- New event loop per sync call
- Destroyed after execution
- Not suitable for high-frequency sync calls

### Thread Pool (run_sync, opposite direction)
```python
# For calling sync code from async context
async def run_sync(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(get_executor(), partial(func, *args, **kwargs))
```
- Shared ThreadPoolExecutor (10 workers default)
- Reused across calls
- Must be shutdown on exit

### Memory
- Tool instances are typically long-lived
- Created once, reused for agent lifetime
- Kwargs are per-invocation

---

## Error Path

### Tool Execution Error
```
_execute_async raises Exception
├── Sync path: run_async propagates exception
├── Async path: exception propagates directly
├── LangGraph catches in ToolNode
├── Creates error ToolMessage
└── Agent sees error, may retry or report
```

### Import Error (LangChain integration)
```
Tool registration with agent
├── If tool doesn't subclass BaseTool correctly
├── LangChain validation fails
└── Agent creation raises error
```

### Argument Validation
```
Tool with args_schema receives invalid args
├── Pydantic validation runs
├── ValidationError raised
├── Propagates to agent
└── Agent sees validation error in result
```

---

## Performance Characteristics

### Invocation Overhead
| Path | Overhead |
|------|----------|
| Async (_arun) | ~0.01ms |
| Sync (_run) | ~1-5ms (event loop creation) |
| With validation | +~0.1ms (Pydantic) |

### Tool Execution Time
- Depends entirely on tool implementation
- Network calls: 100ms - 30s
- Local computation: <1ms
- Database queries: 10-100ms

### Memory
- Tool instance: ~1KB base
- Args schema: ~1KB per
- Execution context: varies with implementation

---

## Observable Effects

### On Successful Execution
- Tool returns string result
- Result passed to agent as ToolMessage
- Agent incorporates into reasoning

### On Error
- Exception type and message captured
- Error shown to agent
- Agent may retry or report to user

### Logging (in ReActAgent)
```python
logger.info(f"Tool invoked: {tool_name} with args: {tool_args}")
logger.debug(f"Tool result received: {str(msg.content)[:200]}...")
```

---

## Why This Design

### Single Implementation Point
**Choice:** Only `_execute_async` is implemented by subclasses

**Rationale:**
- DRY: No duplicate sync/async logic
- Single source of truth for tool behavior
- Base class handles bridging

**Trade-off:**
- Must be async even if logic is sync
- Sync tools wrapped in async unnecessarily

### Kwargs for Parameters
**Choice:** `**kwargs` passed through all layers

**Rationale:**
- Flexibility for any parameter combination
- LangGraph passes extra config kwargs
- Subclass defines specific params

**Trade-off:**
- No type checking at base class level
- Must use args_schema for validation

### Factory Function
**Choice:** `create_tool()` for simple tools

**Rationale:**
- Quick tool creation without class definition
- Good for simple operations
- Reduces boilerplate

**Trade-off:**
- Dynamic class creation is less explicit
- Harder to debug
- Limited customization

### Event Loop Per Call (Sync)
**Choice:** `asyncio.run()` for each sync invocation

**Rationale:**
- Simple and correct
- No shared state between calls
- Works from any sync context

**Trade-off:**
- Expensive for frequent calls
- Cannot reuse connections/sessions across calls
- ~1-5ms overhead per call

---

## What Feels Incomplete

1. **No retry logic**
   - Tool fails once, agent sees error
   - No automatic retry with backoff
   - Must implement in each tool

2. **No timeout handling**
   - Tools can run forever
   - Agent waits indefinitely
   - Should have configurable timeout

3. **No result caching**
   - Same tool call with same args → repeated work
   - Could cache recent results
   - Especially for idempotent tools

4. **No parallel tool execution**
   - Agent executes tools sequentially
   - Could parallelize independent calls
   - LangGraph may support this elsewhere

5. **No tool execution metrics**
   - No timing recorded
   - No success/failure counts
   - Must add manually

---

## What Feels Vulnerable

1. **Unbounded execution time**
   ```python
   async def _execute_async(self, **kwargs):
       await external_api()  # Could hang forever
   ```
   - No timeout wrapper
   - Agent stuck waiting
   - User frustrated

2. **Event loop per sync call**
   ```python
   return asyncio.run(coro)
   ```
   - `asyncio.run()` can't nest
   - If called from existing async context, fails
   - Hard to debug

3. **Dynamic class in create_tool**
   ```python
   class DynamicTool(AsyncAwareTool):
       name: str = name  # Captures outer name
   ```
   - Closure captures variables
   - If func is mutable, behavior changes
   - Debugging shows "DynamicTool"

4. **No input sanitization**
   - Tool receives raw kwargs from agent
   - Agent is fed by user input
   - Indirect injection possible

5. **Error message exposure**
   ```python
   # Exception propagates to agent
   # Agent might show to user
   ```
   - Internal errors visible to user
   - Stack traces might leak info
   - Should sanitize errors

---

## What Feels Like Bad Design

1. **Import inside _run**
   ```python
   def _run(self, **kwargs: Any) -> str:
       from chatforge.utils import run_async  # Import here
       return run_async(self._execute_async(**kwargs))
   ```
   - Import on every call
   - Small overhead but unnecessary
   - Should import at module level

2. **Type hints say str but could be any**
   ```python
   async def _execute_async(self, **kwargs: Any) -> str:
   ```
   - Return type is str
   - But nothing enforces this
   - Agent expects string, could break

3. **No async version of create_tool validation**
   ```python
   if args_schema:
       DynamicTool.args_schema = args_schema
   ```
   - Set after class definition
   - Could use class body instead
   - Feels hacky

4. **kwargs catch-all in signature**
   ```python
   async def _execute_async(self, query: str, limit: int = 5, **kwargs):
   ```
   - **kwargs required to catch LangGraph config
   - But documentation doesn't explain this
   - Easy to forget and break

5. **No base implementation**
   ```python
   @abstractmethod
   async def _execute_async(self, **kwargs: Any) -> str:
       ...
   ```
   - Just `...` body
   - Could raise NotImplementedError for clarity
   - Or provide default behavior

6. **Mixing class and instance attributes**
   ```python
   class MyTool(AsyncAwareTool):
       name: str = "my_tool"  # Class attribute
   ```
   - Pydantic model pattern
   - But not using Pydantic for tool itself
   - Inconsistent with typical Python patterns
