# Trace 11: Async Bridge Utilities

How Chatforge bridges synchronous and asynchronous code execution.

---

## Entry Point

**Location:** `utils/async_bridge.py`

**Trigger:** Code crossing sync/async boundary:
- Sync tool calling async service
- Async handler calling sync library
- LangChain tool _run() calling async implementation

**Key Functions:**
```python
run_sync(func, *args, **kwargs) → T     # Call sync from async
run_async(coro) → T                      # Call async from sync
run_with_timeout(coro, timeout) → tuple  # Async with timeout
get_executor() → ThreadPoolExecutor      # Shared thread pool
shutdown_executor() → None               # Cleanup on exit
```

---

## Execution Path

### Path A: run_sync (Sync from Async)

```
await run_sync(sync_function, arg1, arg2, kwarg=value)
├── Get running event loop
│   └── loop = asyncio.get_running_loop()
├── Get or create shared executor
│   └── executor = get_executor()  # ThreadPoolExecutor
├── Create partial function with args
│   └── partial_fn = functools.partial(func, *args, **kwargs)
├── Submit to executor and await
│   └── result = await loop.run_in_executor(executor, partial_fn)
├── Return result
```

**Thread flow:**
```
Async Task (Event Loop Thread)
    │
    ├── await run_sync(sync_fn, ...)
    │       │
    │       ├── Submit to ThreadPoolExecutor
    │       │         │
    │       │         └── Worker Thread executes sync_fn
    │       │               │
    │       │               └── Return result
    │       │
    │       └── Event loop resumes when complete
    │
    └── Continue with result
```

### Path B: run_async (Async from Sync)

```
run_async(some_coroutine())
├── Call asyncio.run(coro)
│   ├── Create new event loop
│   ├── Run coroutine to completion
│   ├── Close event loop
│   └── Return result
```

**Important constraints:**
- Cannot be called from existing async context
- Creates fresh event loop per call
- Synchronous - blocks calling thread

### Path C: Executor Lifecycle

```
get_executor(max_workers=None)
├── If max_workers provided:
│   └── Update _executor_max_workers
├── If _executor is None:
│   ├── Create ThreadPoolExecutor(
│   │   max_workers=_executor_max_workers,  # Default: 10
│   │   thread_name_prefix="chatforge_async_"
│   │ )
│   └── Log creation
├── Return _executor

shutdown_executor()
├── If _executor is not None:
│   ├── Log shutdown
│   ├── _executor.shutdown(wait=True)  # Wait for tasks
│   └── _executor = None
```

### Path D: run_with_timeout

```
await run_with_timeout(coro, timeout=5.0, timeout_message="Operation")
├── try:
│   ├── result = await asyncio.wait_for(coro, timeout=timeout)
│   └── return (result, False)  # (result, timed_out)
├── except asyncio.TimeoutError:
│   ├── Log warning with timeout_message
│   └── return (None, True)  # (None, timed_out)
```

---

## Resource Management

### ThreadPoolExecutor
- **Singleton:** One executor for entire application
- **Max workers:** 10 by default
- **Thread names:** Prefixed with `chatforge_async_`
- **Lifecycle:** Created lazily, shutdown explicitly

### Event Loops
- **run_sync:** Uses existing event loop
- **run_async:** Creates and destroys per call
- **Cost:** Loop creation ~1ms

### Memory
- Executor threads: ~1MB each (stack)
- Max 10 threads = ~10MB potential
- Idle threads may be reclaimed

---

## Error Path

### run_sync - Sync Function Raises
```python
# Exception in sync function
def sync_fn():
    raise ValueError("error")

await run_sync(sync_fn)
# → ValueError propagates to caller
```

### run_async - Coroutine Raises
```python
# Exception in coroutine
async def async_fn():
    raise ValueError("error")

run_async(async_fn())
# → ValueError propagates to caller
```

### run_async - Already in Async Context
```python
# Calling run_async from async function
async def outer():
    run_async(inner())  # Creates nested event loop

# → RuntimeError: This event loop is already running
# → Or RuntimeError: Cannot run the event loop while another loop is running
```

### Timeout
```python
result, timed_out = await run_with_timeout(slow_op(), timeout=1.0)
if timed_out:
    # result is None
    # Operation was cancelled
```

---

## Performance Characteristics

### Overhead
| Operation | Overhead |
|-----------|----------|
| run_sync (first call) | ~5ms (executor creation) |
| run_sync (subsequent) | ~0.5ms (thread dispatch) |
| run_async | ~1-5ms (event loop creation) |
| run_with_timeout | ~0.01ms (just wraps) |

### Thread Pool
| Workers | Concurrent Sync Calls |
|---------|----------------------|
| 10 (default) | 10 simultaneous |
| Custom | Up to max_workers |

### Blocking Behavior
- **run_sync:** Non-blocking (async, executor handles)
- **run_async:** Blocking (sync caller waits)
- **run_with_timeout:** Non-blocking with cancel

---

## Observable Effects

### Logging
```python
logger.debug(f"Created chatforge executor with {_executor_max_workers} workers")
logger.debug("Shutting down chatforge executor")
logger.warning(f"{timeout_message} after {timeout}s")
```

### Thread Names
```
chatforge_async_0
chatforge_async_1
...
chatforge_async_9
```

---

## Why This Design

### Shared Executor
**Choice:** Single ThreadPoolExecutor for all sync-from-async calls

**Rationale:**
- Avoids creating threads per call
- Bounded concurrency
- Reusable across components

**Trade-off:**
- Global mutable state
- Must shutdown on exit
- Can't customize per-use

### asyncio.run for run_async
**Choice:** Fresh event loop per call

**Rationale:**
- Simple and correct
- Works from any sync context
- No loop management needed

**Trade-off:**
- Cannot nest (already running loop error)
- Overhead per call
- Connections/state not reused

### Timeout Wrapper
**Choice:** Separate function for timeout

**Rationale:**
- Common pattern needed in many places
- Consistent logging
- Clear return type (result, timed_out)

**Trade-off:**
- Tuple return is unconventional
- Could use exception instead

### Lazy Executor Creation
**Choice:** Create executor on first use

**Rationale:**
- No overhead if never used
- Self-configuring
- Works without setup

**Trade-off:**
- First call slower
- Max workers set at first call

---

## What Feels Incomplete

1. **No async context detection in run_async**
   ```python
   def run_async(coro):
       return asyncio.run(coro)  # Will fail if already in async
   ```
   - Should detect and warn
   - Could use nest_asyncio in that case
   - Cryptic error currently

2. **No cancellation support**
   - run_with_timeout cancels, but no general cancel
   - Long-running sync ops can't be cancelled
   - Thread pool tasks not interruptible

3. **No priority or fairness**
   - All tasks equal priority
   - No FIFO guarantee
   - Could starve certain operations

4. **No metrics**
   - No tracking of queue depth
   - No timing statistics
   - Hard to debug bottlenecks

5. **No dynamic resizing**
   - Fixed max_workers after creation
   - Can't adapt to load
   - Restart required to change

---

## What Feels Vulnerable

1. **Global executor state**
   ```python
   _executor: ThreadPoolExecutor | None = None
   ```
   - Any code can access
   - Can be shutdown unexpectedly
   - Not thread-safe modification

2. **No shutdown registration**
   ```python
   # User must call shutdown_executor()
   # Easy to forget
   # Threads may leak
   ```
   - Should use atexit
   - Or context manager

3. **Executor exhaustion**
   ```python
   max_workers=10  # Fixed
   # 11th concurrent call blocks
   ```
   - Silent blocking
   - No warning when saturated
   - Could timeout

4. **run_async event loop conflicts**
   ```python
   # In Jupyter notebook
   run_async(coro)  # Fails - notebook has running loop
   ```
   - Common in interactive environments
   - Need nest_asyncio or alternative

5. **Thread safety of get_executor**
   ```python
   if _executor is None:
       _executor = ThreadPoolExecutor(...)  # Race condition
   ```
   - No lock
   - Concurrent calls could create multiple
   - Would leak executor

---

## What Feels Like Bad Design

1. **reset_executor for testing**
   ```python
   def reset_executor() -> None:
       """Reset the executor (for testing purposes)."""
       shutdown_executor()
   ```
   - Exposes internals for testing
   - Could be misused in production
   - Better to use dependency injection

2. **max_workers only on first call**
   ```python
   def get_executor(max_workers: int | None = None):
       if max_workers is not None:
           _executor_max_workers = max_workers
       if _executor is None:
           # Uses _executor_max_workers
   ```
   - Confusing API
   - Setting after creation is ignored
   - Should be config or error

3. **Tuple return for timeout**
   ```python
   async def run_with_timeout(...) -> tuple[T | None, bool]:
       return (result, timed_out)
   ```
   - Easy to ignore timed_out
   - result can be None for other reasons
   - Exception would be clearer

4. **No type hints on partial**
   ```python
   return await loop.run_in_executor(
       get_executor(),
       functools.partial(func, *args, **kwargs),
   )
   ```
   - Type info lost through partial
   - Return type T is not enforced
   - mypy may not catch errors

5. **Thread name prefix hardcoded**
   ```python
   thread_name_prefix="chatforge_async_"
   ```
   - Not configurable
   - In multi-tenant app, can't distinguish
   - Should be settable

6. **Module-level globals**
   ```python
   _executor: ThreadPoolExecutor | None = None
   _executor_max_workers: int = 10
   ```
   - Makes testing harder
   - Not injectable
   - Classic global state problem
