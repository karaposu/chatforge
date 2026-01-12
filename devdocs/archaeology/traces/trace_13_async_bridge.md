# Trace 13: Async Bridge Utilities

Utilities for bridging synchronous and asynchronous code. Enables tools and middleware to work in both contexts.

---

## Entry Point

**File:** `chatforge/utils/async_bridge.py`
**Functions:**
```python
async def run_sync(func, *args, **kwargs) -> T
def run_async(coro) -> T
async def run_with_timeout(coro, timeout, message) -> tuple[T | None, bool]
def get_executor(max_workers=None) -> ThreadPoolExecutor
def shutdown_executor() -> None
```

**Callers:**
- `AsyncAwareTool._run()` - sync to async bridge
- `SafetyGuardrail.check_response_sync()` - async to sync
- `PromptInjectionGuard.check_message_sync()` - async to sync
- Any code needing async/sync interop

---

## Execution Path: run_sync (Async → Sync call)

```
await run_sync(sync_function, arg1, arg2, kwarg=value)
    │
    ├─1─► Get executor
    │     │
    │     └── get_executor()
    │         │
    │         ├── [_executor is None]
    │         │   └── Create ThreadPoolExecutor(
    │         │           max_workers=10,
    │         │           thread_name_prefix="chatforge_async_",
    │         │       )
    │         │
    │         └── Return shared _executor singleton
    │
    ├─2─► Get event loop
    │     └── loop = asyncio.get_running_loop()
    │
    ├─3─► Submit to executor
    │     │
    │     └── loop.run_in_executor(
    │             executor,
    │             functools.partial(func, *args, **kwargs),
    │         )
    │
    └─4─► Await result
        │
        └── Blocks until thread completes
            └── Returns sync function's result
```

**Use case:** Calling synchronous libraries (like boto3, requests) from async handlers without blocking the event loop.

---

## Execution Path: run_async (Sync → Async call)

```
run_async(some_coroutine())
    │
    └─► asyncio.run(coro)
        │
        ├── Create new event loop
        ├── Run coroutine to completion
        ├── Close event loop
        └── Return result
```

**Use case:** Calling async code from sync contexts (like LangChain tool `_run()`).

**Warning:** Cannot be called from within an async context. Will raise `RuntimeError: This event loop is already running`.

---

## Execution Path: run_with_timeout

```
result, timed_out = await run_with_timeout(
    slow_operation(),
    timeout=5.0,
    timeout_message="Operation timed out"
)
    │
    ├─1─► try:
    │         result = await asyncio.wait_for(coro, timeout=timeout)
    │         return (result, False)
    │
    └─2─► except asyncio.TimeoutError:
              logger.warning(f"{message} after {timeout}s")
              return (None, True)
```

**Use case:** Adding timeout to any async operation with graceful handling.

---

## Thread Pool Management

```
Shared Executor Lifecycle:
    │
    ├── get_executor() - Lazy creation
    │   │
    │   ├── First call: creates ThreadPoolExecutor
    │   └── Subsequent calls: returns same instance
    │
    ├── Application lifetime
    │   └── Threads handle sync work
    │
    └── shutdown_executor() - Clean termination
        │
        ├── executor.shutdown(wait=True)
        │   └── Wait for threads to complete
        │
        └── _executor = None
            └── Next get_executor() creates new pool
```

**Registration pattern:**
```python
import atexit
from chatforge.utils import shutdown_executor

atexit.register(shutdown_executor)  # Clean shutdown on exit
```

---

## Resource Management

| Resource | Acquisition | Release | Failure Mode |
|----------|-------------|---------|--------------|
| ThreadPoolExecutor | First `run_sync()` | `shutdown_executor()` or process exit | Thread leak |
| Worker threads | Per submitted task | After task completion | Hung thread |
| Event loop (run_async) | Per call | After call | Loop pollution |

**Default configuration:**
- `max_workers=10` - Handles I/O-bound work
- Thread names: `chatforge_async_0`, `chatforge_async_1`, ...
- No thread timeout - threads live until executor shutdown

---

## Error Path

```
run_sync errors:
    │
    └── Exception in sync function
        └── Propagates through run_in_executor
            └── Raises in awaiting coroutine

run_async errors:
    │
    ├── Called from async context
    │   └── RuntimeError: "This event loop is already running"
    │
    └── Exception in coroutine
        └── Propagates normally

run_with_timeout errors:
    │
    ├── Timeout
    │   └── Returns (None, True) - not exception
    │
    └── Exception in coroutine
        └── Propagates (not caught)
```

---

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| run_sync overhead | 10-100μs | Thread dispatch |
| run_async overhead | 1-10ms | Event loop creation |
| Thread pool startup | 50-100ms | First run_sync call |
| Max concurrent | 10 | Default max_workers |

**run_async is expensive:**
- Creates new event loop each time
- Don't use in hot paths
- Cache results if possible

---

## Observable Effects

| Effect | Location | Trigger |
|--------|----------|---------|
| Log: "Created chatforge executor with N workers" | async_bridge.py | First run_sync |
| Log: "Shutting down chatforge executor" | async_bridge.py | shutdown_executor |
| Log: "{message} after {timeout}s" | async_bridge.py | run_with_timeout timeout |
| Thread creation | OS | run_sync with empty pool |

---

## Why This Design

**Shared thread pool:**
- Reuses threads
- Bounded concurrency
- Clean shutdown

**Simple APIs:**
- run_sync: async → sync
- run_async: sync → async
- Clear semantics

**run_with_timeout utility:**
- Common pattern
- Consistent logging
- Returns tuple vs exception

**Lazy executor creation:**
- Don't pay until needed
- No startup cost if unused

---

## What Feels Incomplete

1. **No cancellation for run_sync:**
   - Once submitted, can't cancel
   - Thread runs to completion
   - Should support cancellation token

2. **No priority queue:**
   - FIFO only
   - Important work waits
   - No prioritization

3. **No timeout on run_sync:**
   - Sync function can block forever
   - run_with_timeout is async only
   - Hung threads waste pool

4. **No retry support:**
   - One attempt only
   - No exponential backoff
   - Common need unaddressed

5. **No context propagation:**
   - Thread doesn't inherit context
   - No trace propagation
   - Logging context lost

---

## What Feels Vulnerable

1. **Thread pool exhaustion:**
   - 10 threads max
   - Slow sync calls block pool
   - Other work queued

2. **run_async nested loops:**
   - Silently fails or hangs
   - No detection
   - Developer must know context

3. **No cleanup on error:**
   - Exception doesn't shutdown
   - Threads may be stuck
   - Resources leaked

4. **Global mutable state:**
   - `_executor` is global
   - Multiple calls to reset_executor() race
   - Not thread-safe

5. **No health check:**
   - Can't tell if pool is healthy
   - Dead threads not replaced
   - Silently degraded

---

## What Feels Bad Design

1. **Two functions for opposite directions:**
   - run_sync goes async → sync
   - run_async goes sync → async
   - Names suggest opposite meanings

2. **run_async uses asyncio.run:**
   - Can't use from async
   - Creates loop overhead
   - Better: nest_asyncio or detect context

3. **Executor config scattered:**
   - max_workers in function
   - Can't configure after first call
   - Should be centralized config

4. **reset_executor for testing:**
   - Exists but not robust
   - Just calls shutdown_executor
   - Name implies more

5. **No TypeVar for return:**
   - Actually has TypeVar T
   - But typing not enforced
   - run_sync returns Any in practice
