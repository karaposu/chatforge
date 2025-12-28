# Trace 10: Cleanup Service

How background cleanup prevents memory leaks and manages data retention.

---

## Entry Point

**Location:** `services/cleanup.py:120` - `AsyncCleanupRunner` / `SyncCleanupRunner`

**Trigger:**
- Application startup: `await runner.start()`
- Manual cleanup: `await runner.run_cleanup_cycle()`
- API endpoint: POST `/memory/cleanup`

**Key Classes:**
```python
AsyncCleanupRunner   # For async apps (FastAPI, asyncio)
SyncCleanupRunner    # For sync apps (Flask, Slack Bolt)
CleanupCycleMetrics  # Stats for one cleanup cycle
CleanupHistory       # Bounded history of cleanup cycles
```

---

## Execution Path

### Path A: Async Runner Lifecycle

```
AsyncCleanupRunner.__init__(cleanups, intervals, default_interval, history_size)
├── Store cleanup functions dict
├── Store intervals per component
├── Initialize CleanupHistory with max_size
├── Set _running = False
└── Log initialization

await runner.start()
├── Check if already running
├── Set _running = True
├── Create background task: asyncio.create_task(self._cleanup_loop())
└── Log "started"

await runner.stop()
├── Set _running = False
├── Cancel background task
├── Await task with suppress(CancelledError)
└── Log "stopped"
```

### Path B: Cleanup Loop (Async)

```
_cleanup_loop()  # Runs forever until stopped
├── Initialize last_cleanup times for all components
├── while self._running:
│   ├── current_time = time.time()
│   ├── For each (name, cleanup_fn) in cleanups:
│   │   ├── Get interval (custom or default)
│   │   ├── Check if interval elapsed since last cleanup
│   │   ├── If due:
│   │   │   ├── Call await cleanup_fn()
│   │   │   ├── Record items_cleaned[name] = count
│   │   │   ├── Log if count > 0
│   │   │   ├── Update last_cleanup[name] = current_time
│   │   │   └── On exception: log error, set count = -1
│   ├── If any cleanup happened:
│   │   ├── Create CleanupCycleMetrics
│   │   └── Add to history
│   ├── await asyncio.sleep(60)  # Check every minute
│   └── On CancelledError: break
├── Catch any exception: log and sleep(60)
```

### Path C: Manual Cleanup Cycle

```
await runner.run_cleanup_cycle()
├── start_time = time.time()
├── For each (name, cleanup_fn):
│   ├── try:
│   │   ├── count = await cleanup_fn()
│   │   ├── items_cleaned[name] = count
│   │   └── Log if count > 0
│   ├── except:
│   │   ├── Log error
│   │   ├── items_cleaned[name] = -1
│   │   └── error = f"{name}: {e}"
├── Create CleanupCycleMetrics with timing
├── Add to history
└── Return metrics
```

### Path D: Sync Runner (Threading)

```
SyncCleanupRunner.start()
├── Acquire lock
├── Set _running = True
├── For each component:
│   └── _schedule_cleanup(name, interval)  # Timer per component
└── Release lock

_schedule_cleanup(name, interval)
├── if not _running: return
├── Create threading.Timer(interval, _cleanup_and_reschedule, args=(name, interval))
├── timer.daemon = True  # Don't block shutdown
├── timer.start()
└── Add timer to _timers list

_cleanup_and_reschedule(name, interval)
├── Run cleanup function
├── Record metrics
├── if _running: _schedule_cleanup(name, interval)  # Reschedule
```

---

## Resource Management

### Background Task (Async)
- Single asyncio.Task runs cleanup loop
- Sleeps 60 seconds between checks
- Cancelled on stop()

### Timers (Sync)
- One threading.Timer per component
- Daemon threads (auto-terminate)
- Cancelled explicitly on stop()

### History Storage
```python
CleanupHistory(max_size=100)
├── deque with maxlen=100
├── Bounded memory usage
└── Old cycles automatically evicted
```

### Lock (Sync Runner)
```python
self._lock = threading.RLock()
```
- Reentrant lock for thread safety
- Protects timer management

---

## Error Path

### Cleanup Function Failure
```python
try:
    count = await cleanup_fn()
except Exception as e:
    logger.error(f"Cleanup '{name}' failed: {e}", exc_info=True)
    items_cleaned[name] = -1  # Indicate failure
    error = f"{name}: {e}"
```
- Individual failures don't stop other cleanups
- Error recorded in metrics
- -1 indicates failure in items_cleaned

### Task Cancellation
```python
except asyncio.CancelledError:
    logger.debug("Cleanup loop cancelled")
    break
```
- Clean exit on cancellation
- No error logged

### Loop-Level Exception
```python
except Exception as e:
    logger.error(f"Error in cleanup loop: {e}", exc_info=True)
    await asyncio.sleep(60)  # Continue after error
```
- Log and continue
- Don't crash the whole service

---

## Performance Characteristics

### Timing
| Operation | Duration |
|-----------|----------|
| Check cycle | ~1ms (no cleanup due) |
| Storage cleanup | 10-100ms (depends on data) |
| Sleep interval | 60 seconds |
| Default cleanup interval | 600 seconds (10 min) |

### Memory
| Component | Memory |
|-----------|--------|
| Runner instance | ~1KB |
| History (100 cycles) | ~50KB |
| Per-cycle metrics | ~500B |

### CPU
- Minimal when sleeping
- Brief spike during cleanup
- No polling, event-driven

---

## Observable Effects

### Metrics Recorded
```python
CleanupCycleMetrics(
    timestamp=datetime(...),
    duration_ms=45.2,
    items_cleaned={
        "storage": 5,
        "cache": 12,
    },
    error=None
)
```

### History Query
```python
runner.get_cleanup_history(limit=50)
→ {
    "cycles": [...],
    "total_cycles": 127,
    "avg_items_per_cycle": 8.5,
    "last_24h_total_cleaned": 204,
}
```

### Logging
```python
logger.info(f"AsyncCleanupRunner initialized with {len(cleanups)} cleanup functions")
logger.info("AsyncCleanupRunner started")
logger.info(f"Cleanup '{name}': {count} items removed")
logger.error(f"Cleanup '{name}' failed: {e}", exc_info=True)
logger.info("AsyncCleanupRunner stopped")
```

---

## Why This Design

### Configurable Cleanup Functions
**Choice:** Accept dict of name → function

**Rationale:**
- Application controls what gets cleaned
- Different components, different intervals
- Easy to add/remove

**Trade-off:**
- Functions must return int
- No standardized cleanup interface

### Per-Component Intervals
**Choice:** Intervals dict with default fallback

**Rationale:**
- Cache might need frequent cleanup
- Storage can be less frequent
- Flexibility per component

**Trade-off:**
- More configuration
- Could have conflicting cleans

### Bounded History
**Choice:** deque with maxlen for history

**Rationale:**
- Memory doesn't grow unbounded
- Old history automatically evicted
- Still queryable for debugging

**Trade-off:**
- Lose old history
- Can't analyze long-term trends

### Async vs Sync Runners
**Choice:** Two separate classes

**Rationale:**
- Async apps use asyncio patterns
- Sync apps use threading patterns
- Clean separation

**Trade-off:**
- Code duplication
- Must choose correct runner

---

## What Feels Incomplete

1. **No cleanup registration after start**
   ```python
   def register_cleanup(self, name, cleanup_fn, interval=None):
   ```
   - Can register after init
   - But not in running loop context
   - No dynamic add/remove while running

2. **No pause/resume**
   - Only start/stop
   - Can't temporarily pause
   - Must stop and restart

3. **No cleanup dependencies**
   - Components cleaned independently
   - Can't express "clean A before B"
   - Order not guaranteed

4. **No external monitoring integration**
   - History is in-memory only
   - No Prometheus metrics export
   - No alerting on failures

5. **No backpressure**
   - If cleanup is slow, next cycle waits
   - But manual trigger can overlap
   - Could have concurrent cleanups

---

## What Feels Vulnerable

1. **60-second check interval**
   ```python
   await asyncio.sleep(60)
   ```
   - Hardcoded, not configurable
   - Too slow for some use cases
   - Too frequent for others

2. **No timeout on cleanup functions**
   ```python
   count = await cleanup_fn()  # Could hang forever
   ```
   - Stuck cleanup blocks loop
   - Other components not cleaned
   - Should have timeout

3. **Timer daemon threads**
   ```python
   timer.daemon = True
   ```
   - Killed on process exit
   - Cleanup may be incomplete
   - No graceful shutdown

4. **History not persisted**
   - Lost on restart
   - Can't compare across deployments
   - No long-term debugging

5. **No cleanup locking**
   ```python
   # Manual and automatic cleanup could overlap
   await runner.run_cleanup_cycle()  # While loop is also running
   ```
   - Same component cleaned twice
   - Race conditions possible

---

## What Feels Like Bad Design

1. **-1 as error indicator**
   ```python
   items_cleaned[name] = -1  # Failure
   ```
   - Magic number
   - Could be confused with "cleaned -1 items" (nonsensical)
   - Should use None or separate error field

2. **CleanupHistory.__post_init__ recreates deque**
   ```python
   def __post_init__(self):
       self.cycles = deque(maxlen=self.max_size)
   ```
   - Overrides field default
   - Wasteful double creation
   - Should just use field(default_factory=...)

3. **get_cleanup_history returns dict, not dataclass**
   ```python
   def get_cleanup_history(self, limit=50) -> dict:
       return {
           "cycles": [...],
           "total_cycles": ...,
       }
   ```
   - Inconsistent with CleanupCycleMetrics
   - No type safety
   - Should be a proper dataclass

4. **Sync runner has different interface**
   ```python
   # AsyncCleanupRunner
   async def run_cleanup_cycle(self) -> CleanupCycleMetrics:

   # SyncCleanupRunner
   # No equivalent method!
   ```
   - Missing manual cleanup in sync runner
   - Inconsistent APIs
   - Harder to test sync path

5. **Last cleanup stats vs history**
   ```python
   def get_last_cleanup_stats(self) -> dict | None:
       last = self._history.get_last()
       return last.to_dict() if last else None
   ```
   - Returns dict instead of CleanupCycleMetrics
   - Inconsistent with internal storage
   - Loses type information

6. **Time tracking duplicated**
   ```python
   self._last_cleanup: dict[str, float] = {}  # In runner
   # Also timestamp in CleanupCycleMetrics
   ```
   - Two places tracking timing
   - Could get out of sync
   - Should derive from history
