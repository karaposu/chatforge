# Trace 05: WebSocket Infrastructure

The foundational WebSocket client used by real-time adapters. Handles connection lifecycle, reconnection, and message queuing.

---

## Entry Point

**File:** `chatforge/infrastructure/websocket/client.py:28`
**Class:** `WebSocketClient`

**Constructor:**
```python
def __init__(
    self,
    config: WebSocketConfig,
    reconnect_policy: ReconnectPolicy | None = None,
)
```

**Callers:**
- `OpenAIRealtimeAdapter` for voice sessions
- Future WebRTC signaling adapters
- Any real-time communication adapter

---

## Execution Path: Connection Lifecycle

```
async with WebSocketClient(config) as ws:
    │
    ├─► __aenter__()
    │   └── await connect()
    │
    ├─► connect()
    │   │
    │   ├─1─► Acquire _state_lock
    │   │
    │   ├─2─► Check state not CONNECTED or CONNECTING
    │   │     └── Already connected → return early
    │   │
    │   ├─3─► Set state = CONNECTING
    │   │
    │   ├─4─► Build connection kwargs
    │   │     ├── max_size=config.max_message_size
    │   │     ├── ping_interval=None (we do our own)
    │   │     ├── additional_headers=config.headers
    │   │     ├── subprotocols=config.subprotocols
    │   │     └── compression=config.compression
    │   │
    │   ├─5─► websockets.connect() with timeout
    │   │     └── asyncio.wait_for(..., timeout=config.connect_timeout)
    │   │     │
    │   │     ├── Timeout → WebSocketTimeoutError
    │   │     └── Error → WebSocketConnectionError
    │   │
    │   ├─6─► Set state = CONNECTED
    │   │
    │   ├─7─► Reset reconnect state
    │   │     ├── _reconnect_attempt = 0
    │   │     └── reconnect_policy.reset()
    │   │
    │   ├─8─► Start background tasks
    │   │     ├── _receive_task = create_task(_receive_loop())
    │   │     ├── _ping_task = create_task(_ping_loop()) [if ping_interval > 0]
    │   │     └── _send_task = create_task(_send_worker()) [if send queue enabled]
    │   │
    │   ├─9─► Record metrics: _metrics.on_connect()
    │   │
    │   ├─10─ Assign _ws = websocket
    │   │
    │   ├─11─ Fire callback: on_connect()
    │   │
    │   └─12─ Log: "WebSocket connected to {url} [id={connection_id}]"
    │
    │   [Connected - use the connection]
    │
    ├─► await ws.send("message")
    │   [See Send Path below]
    │
    ├─► async for msg in ws.messages():
    │   [See Receive Path below]
    │
    └─► __aexit__()
        │
        └── await disconnect()
            │
            ├─1─► Set _should_reconnect = False (prevent auto-reconnect)
            │
            ├─2─► Set state = CLOSING
            │
            ├─3─► Cancel all background tasks
            │     ├── _receive_task.cancel()
            │     ├── _ping_task.cancel()
            │     └── _send_task.cancel()
            │
            ├─4─► Close WebSocket: _ws.close(code, reason)
            │     └── With timeout: config.close_timeout
            │
            ├─5─► Set state = CLOSED
            │
            ├─6─► Record metrics: _metrics.on_disconnect()
            │
            ├─7─► Fire callback: on_disconnect(None)
            │
            └─8─► Log: "WebSocket disconnected"
```

---

## Execution Path: Send

```
send(data: str | bytes)
    │
    ├─1─► Check connected
    │     └── Not connected → raise WebSocketClosedError
    │
    ├─2─► [Send queue enabled?]
    │     │
    │     ├── [Yes - queued send]
    │     │   ├── Put data in _send_queue
    │     │   │   └── With timeout: config.send_queue_timeout
    │     │   │   └── Timeout → WebSocketBackpressureError
    │     │   │
    │     │   └── Background _send_worker() will send
    │     │
    │     └── [No - direct send]
    │         └── await _send_now(data)
    │
    └── _send_now(data)
        │
        ├── Check connected again
        │
        ├── await _ws.send(data)
        │   ├── ConnectionClosed → WebSocketClosedError
        │   └── Error → WebSocketSendError
        │
        └── Record metrics: _metrics.on_message_sent(size)

_send_worker()  [Background task when queue enabled]
    │
    └── while is_connected:
        │
        ├── data = await _send_queue.get() [1s timeout]
        │
        ├── await _send_now(data)
        │   └── WebSocketClosedError → stop worker
        │   └── Other error → log, continue
        │
        └── [On cancellation: drain remaining queue]
```

---

## Execution Path: Receive

```
messages()  [Async generator]
    │
    └── while is_connected or queue not empty:
        │
        ├── message = await _receive_queue.get() [1s timeout]
        │   └── Timeout → continue loop
        │
        └── yield message

_receive_loop()  [Background task]
    │
    └── async for message in _ws:
        │
        ├─1─► Wrap in WebSocketMessage
        │     ├── bytes → MessageType.BINARY
        │     └── str → MessageType.TEXT
        │
        ├─2─► Record metrics: _metrics.on_message_received(size)
        │
        ├─3─► Fire callback: on_message(ws_msg)
        │
        ├─4─► Queue message: _receive_queue.put_nowait(ws_msg)
        │     │
        │     └── QueueFull:
        │         ├── Log warning: "Receive queue full, dropping"
        │         ├── _metrics.on_message_dropped()
        │         └── Fire callback: on_receive_overflow(ws_msg)
        │
        └── [On disconnect/error]
            ├── ConnectionClosed → _handle_disconnect(error)
            └── Other error → _handle_disconnect(error)
```

---

## Execution Path: Reconnection

```
_handle_disconnect(error)
    │
    ├─1─► Set state = DISCONNECTED
    │
    ├─2─► Fire callback: on_disconnect(error)
    │
    └─3─► [Auto-reconnect enabled?]
        │
        └── create_task(_reconnect())

_reconnect()
    │
    ├─1─► Set state = RECONNECTING
    │
    └─2─► while _should_reconnect:
        │
        ├── _reconnect_attempt++
        │
        ├── delay = reconnect_policy.next_delay(attempt)
        │   │
        │   │   [ExponentialBackoff]
        │   │   delay = base * (factor ** (attempt - 1))
        │   │   delay = min(delay, max_delay)
        │   │   delay += random jitter
        │   │
        │   └── None → max attempts reached
        │       ├── Set state = CLOSED
        │       ├── Fire on_error(ReconnectExhausted)
        │       └── return
        │
        ├── Log: "Reconnecting in {delay}s (attempt {attempt})"
        │
        ├── Fire callback: on_reconnecting(attempt)
        │
        ├── await asyncio.sleep(delay)
        │
        └── try: await connect()
            ├── Success:
            │   ├── _metrics.on_reconnect()
            │   ├── Log: "Reconnected successfully"
            │   └── return
            │
            └── Failure:
                ├── Log warning
                ├── Fire on_error(e)
                └── continue loop
```

---

## Execution Path: Ping/Heartbeat

```
_ping_loop()  [Background task]
    │
    └── while is_connected:
        │
        ├── await asyncio.sleep(config.ping_interval)
        │
        └── if connected:
            │
            ├── pong = await _ws.ping()
            │
            └── await asyncio.wait_for(pong, timeout=config.ping_timeout)
                │
                └── Timeout:
                    ├── Log: "Ping timeout"
                    └── _handle_disconnect(WebSocketTimeoutError)
```

---

## Resource Management

| Resource | Acquisition | Release | Failure Mode |
|----------|-------------|---------|--------------|
| WebSocket connection | connect() | disconnect() | Hung if not closed |
| _receive_task | connect() | disconnect() | Must cancel |
| _ping_task | connect() | disconnect() | Must cancel |
| _send_task | connect() | disconnect() | Drains on cancel |
| _receive_queue | __init__ | Never (bounded) | Drops on overflow |
| _send_queue | __init__ | Never (bounded) | Backpressure |

**Queue limits:**
- `_receive_queue`: `config.max_queue_size` (default not shown)
- `_send_queue`: `config.send_queue_size` (if enabled)

---

## Error Path

```
Connection:
    │
    ├── Timeout → WebSocketTimeoutError
    ├── Network error → WebSocketConnectionError
    └── Already connected → return (no-op)

Send:
    │
    ├── Not connected → WebSocketClosedError
    ├── Connection closed during send → WebSocketClosedError
    ├── Queue full → WebSocketBackpressureError
    └── Other error → WebSocketSendError

Receive:
    │
    ├── Connection closed → triggers reconnect
    └── Queue full → message dropped, callback fired

Reconnect:
    │
    └── Max attempts → WebSocketReconnectExhausted
```

---

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Connect latency | 50-500ms | Network dependent |
| Send latency (queued) | <1ms | Queue put |
| Send latency (direct) | 1-50ms | Network write |
| Receive latency | <1ms | Queue get |
| Ping interval | configurable | Default 20s |
| Reconnect delay | 1-30s | Exponential backoff |

**Queued vs direct send:**
- Queued: Background worker, non-blocking, backpressure protection
- Direct: Immediate, may block on slow network

---

## Observable Effects

| Effect | Location | Trigger |
|--------|----------|---------|
| Log: "WebSocket connected to {url}" | client | connect() |
| Log: "WebSocket disconnected" | client | disconnect() |
| Log: "Reconnecting in Xs" | client | _reconnect() |
| Log: "Reconnected successfully" | client | _reconnect() success |
| Log: "Receive queue full, dropping" | client | Queue overflow |
| Callback: on_connect() | caller | Connection success |
| Callback: on_disconnect(error) | caller | Connection lost |
| Callback: on_reconnecting(attempt) | caller | Reconnect attempt |
| Metrics: messages_sent, messages_received | ConnectionMetrics | Each message |

---

## Why This Design

**Separate send queue:**
- Decouples send from network
- Backpressure protection
- Non-blocking sends

**Bounded queues:**
- Prevent unbounded memory growth
- Predictable resource usage
- Fail fast on overload

**Exponential backoff:**
- Standard reconnection pattern
- Avoids thundering herd
- Respects server load

**Callback system:**
- Event notification without coupling
- Both sync and async callbacks supported
- Error isolation (callback errors logged, not propagated)

---

## What Feels Incomplete

1. **No message ordering guarantees with queue:**
   - Messages could reorder if queue drains during reconnect
   - No sequence numbers
   - No acknowledgment

2. **No compression by default:**
   - `compression` is optional param
   - Not documented
   - WebSocket permessage-deflate could help

3. **No message fragmentation:**
   - Large messages sent whole
   - No streaming for big payloads
   - `max_message_size` is receive limit only

4. **No health check API:**
   - Ping is internal only
   - No way to check health externally
   - `ping()` method exists but not well documented

5. **No priority queue:**
   - All messages equal priority
   - Control messages wait behind data
   - Could cause latency spikes

---

## What Feels Vulnerable

1. **Receive queue overflow:**
   - Drops messages silently (with log)
   - No retry
   - Critical messages could be lost

2. **Reconnect during active session:**
   - Application state may be invalidated
   - No coordination with adapter
   - Could cause duplicate processing

3. **Callback exceptions:**
   - Caught and logged
   - But could hide important errors
   - No way to bubble up

4. **Connection ID for logging only:**
   - Good for debugging
   - But not unique across restarts
   - No persistence

5. **Send queue drain on cancel:**
   - Tries to send remaining
   - May fail if connection gone
   - Could block shutdown

---

## What Feels Bad Design

1. **Two send paths:**
   - Queued and direct
   - Caller must understand difference
   - Should be one path with options

2. **Metrics optional:**
   - `enable_metrics=True` creates ConnectionMetrics
   - But most code checks `if self._metrics:`
   - Should always have metrics (null object pattern)

3. **Serializer optional:**
   - `send_json()` works without serializer
   - But `send_obj()` requires one
   - Inconsistent API

4. **State lock granularity:**
   - Lock on state changes
   - But not on all operations
   - Could lead to races

5. **Reconnect policy external:**
   - ExponentialBackoff is separate class
   - Config has backoff settings
   - Duplication of responsibility
