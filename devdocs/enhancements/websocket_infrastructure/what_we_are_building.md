# WebSocket Infrastructure: What We Are Building

**Date:** 2025-01-01
**Updated:** 2026-01-01 (post-critical analysis)

---

## What We Are Building

A reusable, production-ready WebSocket client infrastructure for chatforge that will power multiple adapters requiring persistent WebSocket connections.

```
┌────────────────────────────────────────────────────┐
│            WebSocketClient                         │
│                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │ Reconnection │  │  Serializers │  │ Metrics  │ │
│  │   Policies   │  │  JSON/Raw    │  │ Tracking │ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
│                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │  Send Queue  │  │ Backpressure │  │  Ping/   │ │
│  │   + Worker   │  │  Handling    │  │  Pong    │ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
│                                                    │
│         Built on: websockets library               │
└────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   OpenAI     │ │   Twilio     │ │   Custom     │
│   Realtime   │ │   Streams    │ │   WebSocket  │
│   Adapter    │ │   Adapter    │ │   Adapter    │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## Why Building This Is a Good Idea

### 1. Multiple Consumers Need It

| Planned Adapter | WebSocket Usage |
|-----------------|-----------------|
| OpenAI Realtime API | Real-time voice/text streaming |
| Twilio Media Streams | Phone call audio |
| WebRTC Signaling | Peer connection setup |
| Custom voice servers | Any WebSocket-based API |

Building once, using everywhere.

### 2. The Alternative Is Worse

**Without shared infrastructure:**
```python
# OpenAI adapter - implements its own WebSocket handling
class OpenAIRealtimeAdapter:
    async def connect(self):
        self._ws = await websockets.connect(...)
        # Custom reconnection logic
        # Custom error handling
        # Custom ping/pong
        # ... 200 lines

# Twilio adapter - duplicates everything
class TwilioAdapter:
    async def connect(self):
        self._ws = await websockets.connect(...)
        # Same reconnection logic, copy-pasted
        # Same error handling, copy-pasted
        # Same ping/pong, copy-pasted
        # ... 200 lines (duplicated)
```

**With shared infrastructure:**
```python
class OpenAIRealtimeAdapter:
    async def connect(self):
        self._ws = WebSocketClient(config)  # Done
        await self._ws.connect()

class TwilioAdapter:
    async def connect(self):
        self._ws = WebSocketClient(config)  # Done
        await self._ws.connect()
```

### 3. Production Concerns Are Hard

These things are easy to get wrong:

| Concern | Naive Approach | Our Infrastructure |
|---------|---------------|-------------------|
| Reconnection | `while True: try connect` | Exponential backoff with jitter |
| Network hiccups | Connection drops silently | Ping/pong heartbeat detection |
| Memory growth | Unbounded queues | Backpressure with timeout |
| Debugging | `print("connected")` | Metrics, connection ID, structured logging |
| Thundering herd | All clients reconnect at once | Jitter prevents stampede |

### 4. Consistency Across Adapters

All WebSocket-based adapters will have:
- Same reconnection behavior
- Same error types
- Same logging patterns
- Same metrics format
- Same configuration style

This makes the codebase predictable and maintainable.

### 5. Testability

```python
# Easy to test adapters without real WebSocket servers
class MockWebSocketClient:
    async def send(self, data):
        self.sent.append(data)

    async def messages(self):
        for msg in self.fake_messages:
            yield msg

# Inject mock in tests
adapter = OpenAIRealtimeAdapter(ws_client=MockWebSocketClient())
```

---

## Common Pitfalls to Avoid

> **14 pitfalls identified** through critical analysis. Each includes the bad pattern, why it's problematic, and the correct solution.

### 1. Reconnection Without Backoff

**Bad:**
```python
async def reconnect(self):
    while True:
        try:
            await self.connect()
            break
        except:
            await asyncio.sleep(1)  # Fixed delay
```

**Problem:** If server is down, all clients hammer it every second. When it comes back up, thundering herd kills it again.

**Good:**
```python
async def reconnect(self):
    delay = self.policy.next_delay(attempt)  # Exponential + jitter
    await asyncio.sleep(delay)
    await self.connect()
```

### 2. Unbounded Queues

**Bad:**
```python
self._queue = asyncio.Queue()  # No max size

async def on_message(self, msg):
    await self._queue.put(msg)  # Always succeeds, memory grows forever
```

**Problem:** If consumer is slow, queue grows unbounded → OOM crash.

**Good:**
```python
self._queue = asyncio.Queue(maxsize=1000)

async def send(self, data):
    try:
        await asyncio.wait_for(self._queue.put(data), timeout=1.0)
    except asyncio.TimeoutError:
        raise WebSocketBackpressureError("Queue full")
```

### 3. Silent Connection Death

**Bad:**
```python
# No ping/pong, connection silently dies
async def receive_loop(self):
    async for msg in self._ws:
        yield msg
    # Connection died, we never notice until next send fails
```

**Problem:** TCP connections can die without FIN packet (network issues, firewall timeout). You won't know until you try to send.

**Good:**
```python
async def ping_loop(self):
    while self.is_connected:
        await asyncio.sleep(20)
        pong = await self._ws.ping()
        await asyncio.wait_for(pong, timeout=10)  # Detect death
```

### 4. Blocking the Event Loop

**Bad:**
```python
async def send(self, data):
    serialized = json.dumps(data)  # Fine
    compressed = zlib.compress(serialized.encode())  # BLOCKS event loop!
    await self._ws.send(compressed)
```

**Problem:** CPU-bound operations block the entire async event loop.

**Good:**
```python
async def send(self, data):
    serialized = json.dumps(data)
    # Run CPU-bound work in thread pool
    compressed = await asyncio.to_thread(zlib.compress, serialized.encode())
    await self._ws.send(compressed)
```

### 5. Swallowing Exceptions

**Bad:**
```python
async def receive_loop(self):
    try:
        async for msg in self._ws:
            self.on_message(msg)
    except:
        pass  # Swallowed! No idea what went wrong
```

**Good:**
```python
async def receive_loop(self):
    try:
        async for msg in self._ws:
            self.on_message(msg)
    except websockets.ConnectionClosed as e:
        logger.info(f"Connection closed: code={e.code} reason={e.reason}")
        await self._handle_disconnect(e)
    except Exception as e:
        logger.error(f"Receive error: {e}", exc_info=True)
        await self._handle_disconnect(e)
```

### 6. Race Conditions on State

**Bad:**
```python
async def connect(self):
    if self._state == CONNECTING:  # Check
        return
    self._state = CONNECTING  # Set - race condition!
```

**Problem:** Two concurrent `connect()` calls can both pass the check.

**Good:**
```python
async def connect(self):
    async with self._state_lock:  # Atomic check-and-set
        if self._state == CONNECTING:
            return
        self._state = CONNECTING
```

### 7. Forgetting to Cancel Tasks

**Bad:**
```python
async def disconnect(self):
    await self._ws.close()
    # Forgot to cancel receive_loop and ping_loop tasks!
```

**Problem:** Background tasks keep running, accessing closed connection.

**Good:**
```python
async def disconnect(self):
    for task in [self._receive_task, self._ping_task, self._send_task]:
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    await self._ws.close()
```

### 8. Leaking Connections

**Bad:**
```python
async def connect(self):
    self._ws = await websockets.connect(url)
    # If next line raises, connection is leaked!
    await self._setup_session()
```

**Good:**
```python
async def connect(self):
    ws = None
    try:
        ws = await websockets.connect(url)

        # All setup happens here
        self._receive_task = asyncio.create_task(self._receive_loop())
        self._ping_task = asyncio.create_task(self._ping_loop())

        # Only assign after ALL setup succeeds
        self._ws = ws

    except Exception:
        if ws:
            await ws.close()  # Clean up on failure
        raise
```

---

### 9. Silent Message Drops

**Bad:**
```python
except asyncio.QueueFull:
    logger.warning("Queue full, dropping message")
    # Message silently dropped - no callback, no metric!
```

**Problem:** Caller has no way to know messages are being lost.

**Good:**
```python
except asyncio.QueueFull:
    logger.warning("Queue full, dropping message")
    if self._metrics:
        self._metrics.on_message_dropped()  # Track it
    await self._fire_callback(self.on_receive_overflow, msg)  # Notify caller
```

---

### 10. Background Workers Dying Silently

**Bad:**
```python
async def _send_worker(self):
    while self.is_connected:
        data = await self._send_queue.get()
        await self._send_now(data)  # If this raises, worker dies!
```

**Problem:** One bad message kills the entire send worker. Connection appears alive but sends fail.

**Good:**
```python
async def _send_worker(self):
    while self.is_connected:
        try:
            data = await self._send_queue.get()
            await self._send_now(data)
        except WebSocketClosedError:
            break  # Expected, stop gracefully
        except Exception as e:
            logger.warning(f"Send error: {e}")
            await self._fire_callback(self.on_error, e)  # Notify, but continue
```

---

### 11. Sync-Only Callbacks

**Bad:**
```python
def _fire_callback(self, callback, *args):
    if callback:
        callback(*args)  # What if callback is async?
```

**Problem:** User's async callbacks won't work.

**Good:**
```python
async def _fire_callback(self, callback, *args):
    if callback:
        result = callback(*args)
        if asyncio.iscoroutine(result):
            await result  # Handle async callbacks
```

---

### 12. Wrong Time Functions

**Bad:**
```python
self.connect_time = time.time()
uptime = time.time() - self.connect_time
```

**Problem:** `time.time()` can jump backwards (NTP sync). Duration calculations become wrong.

**Good:**
```python
self.connect_time = time.monotonic()  # Monotonic clock
uptime = time.monotonic() - self.connect_time
```

---

### 13. Recording Metrics at Wrong Time

**Bad:**
```python
async def _reconnect(self):
    if self._metrics:
        self._metrics.on_reconnect()  # BEFORE attempting!

    await self.connect()  # This might fail!
```

**Problem:** Metrics count attempts, not successes. Dashboard shows false reconnections.

**Good:**
```python
async def _reconnect(self):
    try:
        await self.connect()
        # Record AFTER success
        if self._metrics:
            self._metrics.on_reconnect()
    except Exception:
        pass  # Don't count failed attempts as reconnects
```

---

### 14. No Configuration Validation

**Bad:**
```python
@dataclass
class WebSocketConfig:
    ping_interval: float = 20.0  # What if negative?
    max_queue_size: int = 1000   # What if 0?
```

**Problem:** Invalid config causes subtle bugs at runtime.

**Good:**
```python
@dataclass
class WebSocketConfig:
    ping_interval: float = 20.0
    max_queue_size: int = 1000

    def __post_init__(self):
        if self.ping_interval < 0:
            raise ValueError("ping_interval must be non-negative")
        if self.max_queue_size <= 0:
            raise ValueError("max_queue_size must be positive")
```

---

### Pitfall Summary Table

| # | Pitfall | Consequence | Solution |
|---|---------|-------------|----------|
| 1 | Reconnection without backoff | Thundering herd | Exponential backoff + jitter |
| 2 | Unbounded queues | OOM crash | maxsize + timeout |
| 3 | Silent connection death | Undetected failures | Ping/pong heartbeat |
| 4 | Blocking event loop | Frozen async loop | `asyncio.to_thread()` |
| 5 | Swallowing exceptions | Hidden bugs | Log + handle properly |
| 6 | Race conditions on state | Concurrent corruption | `asyncio.Lock` |
| 7 | Forgetting to cancel tasks | Resource leaks | Cancel all on disconnect |
| 8 | Leaking connections | Socket exhaustion | Assign `_ws` last, close on error |
| 9 | Silent message drops | Data loss unnoticed | Callback + metric |
| 10 | Workers dying silently | Dead sends | Catch + notify, continue |
| 11 | Sync-only callbacks | Async callbacks fail | Check `iscoroutine()` |
| 12 | Wrong time functions | Clock jumps break uptime | `time.monotonic()` |
| 13 | Metrics at wrong time | False metrics | Record after success |
| 14 | No config validation | Runtime surprises | `__post_init__` |

---

## How to Determine Things Are Good

### 1. Unit Tests Pass

```bash
pytest tests/infrastructure/websocket/ -v
```

Minimum coverage:
- [ ] Connect/disconnect lifecycle
- [ ] Send/receive text and binary
- [ ] Reconnection with backoff
- [ ] Timeout handling
- [ ] Queue full (backpressure)
- [ ] Callbacks fire correctly (sync AND async)
- [ ] Metrics are tracked
- [ ] Receive overflow callback fires
- [ ] Connection leak prevention (setup failure)
- [ ] Config validation rejects bad values

### 2. Integration Test with Real Server

```python
@pytest.mark.integration
async def test_echo_server_roundtrip():
    async with WebSocketClient(config) as ws:
        await ws.send_text("hello")
        msg = await ws.receive(timeout=5.0)
        assert msg.as_text() == "hello"
```

### 3. Reconnection Actually Works

```python
@pytest.mark.integration
async def test_reconnection_on_server_restart():
    ws = WebSocketClient(config)
    await ws.connect()

    # Simulate server going down
    await stop_test_server()
    await asyncio.sleep(0.5)

    # Restart server
    await start_test_server()

    # Wait for reconnection
    await asyncio.sleep(5)

    assert ws.is_connected
    assert ws.get_stats()["reconnects"] >= 1
```

### 4. No Memory Leaks Under Load

```python
@pytest.mark.load
async def test_no_memory_leak():
    import tracemalloc
    tracemalloc.start()

    async with WebSocketClient(config) as ws:
        for _ in range(10000):
            await ws.send_text("x" * 1000)
            await ws.receive(timeout=1.0)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Should not grow significantly
    assert peak < 50 * 1024 * 1024  # 50MB max
```

### 5. Backpressure Works

```python
async def test_backpressure_triggers():
    config = WebSocketConfig(
        url=slow_server_url,
        send_queue_size=10,
        send_queue_timeout=0.1,
    )

    async with WebSocketClient(config) as ws:
        # Fill the queue
        for _ in range(10):
            await ws.send_text("msg")

        # Next one should fail with backpressure
        with pytest.raises(WebSocketBackpressureError):
            await ws.send_text("overflow")
```

### 6. Metrics Are Accurate

```python
async def test_metrics_accuracy():
    async with WebSocketClient(config) as ws:
        await ws.send_text("hello")
        await ws.receive(timeout=5.0)

        stats = ws.get_stats()

        assert stats["connects"] == 1
        assert stats["messages_sent"] == 1
        assert stats["messages_received"] == 1
        assert stats["bytes_sent"] == 5  # "hello"
        assert stats["messages_dropped"] == 0  # No overflow
        assert "uptime_seconds" in stats
```

### 6b. Async Callbacks Work

```python
async def test_async_callback():
    client = WebSocketClient(config)
    events = []

    async def async_on_connect():
        await asyncio.sleep(0.01)  # Simulate async work
        events.append("connected")

    client.on_connect = async_on_connect

    await client.connect()
    assert "connected" in events  # Async callback was awaited
    await client.disconnect()
```

### 6c. Overflow Notification Works

```python
async def test_receive_overflow_callback():
    config = WebSocketConfig(
        url=server_url,
        max_queue_size=1,  # Tiny queue
    )

    dropped = []

    async with WebSocketClient(config) as ws:
        ws.on_receive_overflow = lambda msg: dropped.append(msg)

        # Flood with messages
        for i in range(10):
            await ws.send_text(f"msg{i}")

        await asyncio.sleep(0.2)

    # Some messages should have triggered overflow callback
    assert len(dropped) > 0
```

### 7. Works with Real APIs

```python
@pytest.mark.integration
async def test_openai_realtime_handshake():
    """Verify we can connect to OpenAI Realtime API."""
    config = WebSocketConfig(
        url="wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview",
        headers={
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
            "OpenAI-Beta": "realtime=v1",
        },
    )

    async with WebSocketClient(config) as ws:
        # Should receive session.created event
        msg = await ws.receive(timeout=10.0)
        event = json.loads(msg.as_text())
        assert event["type"] == "session.created"
```

### 8. Code Quality Checks

```bash
# Type checking
mypy chatforge/infrastructure/websocket/

# Linting
ruff check chatforge/infrastructure/websocket/

# No TODOs or FIXMEs left
grep -r "TODO\|FIXME" chatforge/infrastructure/websocket/
```

---

## Success Criteria Summary

| Criterion | How to Verify |
|-----------|---------------|
| All tests pass | `pytest tests/infrastructure/websocket/ -v` |
| No type errors | `mypy chatforge/infrastructure/websocket/` |
| Reconnection works | Integration test with server restart |
| Backpressure works | Test queue overflow scenario |
| No memory leaks | Load test with tracemalloc |
| Metrics accurate | Compare stats to actual operations |
| Works with OpenAI | Integration test with real API |
| Code is clean | Linting passes, no TODOs |
| **Async callbacks** | Test both sync and async callbacks work |
| **Overflow notification** | Test on_receive_overflow callback fires |
| **No connection leaks** | Test setup failure doesn't leak connections |
| **Config validates** | Test invalid config raises ValueError |

---

## When Is It Done?

The infrastructure is complete when:

1. **All adapters can use it** - OpenAI, Twilio, custom servers
2. **Production concerns are handled** - Reconnection, metrics, backpressure
3. **Tests prove it works** - Unit, integration, and load tests pass
4. **Code is maintainable** - Types, docs, clean architecture
5. **It's actually used** - At least one adapter (OpenAI Realtime) is built on it
