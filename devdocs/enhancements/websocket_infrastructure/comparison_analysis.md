# WebSocket Infrastructure: Comparison Analysis

**Date:** 2025-01-01
**Compared Against:**
- `voiceai/voxengine/connections/websocket_connection.py`
- `realtimevoiceapi/realtimevoiceapi/connections/websocket_connection.py`
- `realtimevoiceapi/realtimevoiceapi/connections/client.py`

---

## Summary

| Concept | Existing Code | Our Design | Status |
|---------|---------------|------------|--------|
| Connection states | ✅ | ✅ | Covered |
| Reconnection with backoff | ✅ | ✅ | Covered |
| Message queue | ✅ | ✅ | Covered |
| Async context manager | ✅ | ✅ | Covered |
| Event callbacks | ✅ | ✅ | Covered |
| Ping/pong heartbeat | ✅ | ✅ | Covered |
| **Pluggable serializers** | ✅ | ❌ | **Missing** |
| **Fast/Big lane pattern** | ✅ | ❌ | **Missing** |
| **Connection metrics** | ✅ | ❌ | **Missing** |
| **SSL context config** | ✅ | ❌ | **Missing** |
| **Compression support** | ✅ | ❌ | **Missing** |
| **Send worker (queued sends)** | ✅ | ❌ | **Missing** |
| **Backpressure handling** | ✅ | ❌ | **Missing** |
| **Connection ID** | ✅ | ❌ | **Missing** |
| **get_stats() method** | ✅ | ❌ | **Missing** |
| **Manual ping() method** | ✅ | ❌ | **Missing** |
| **Sync handler support** | ✅ | ❌ | **Missing** |

---

## Good Ideas We Should Adopt

### 1. Pluggable Serializers (High Value)

**Their approach:**
```python
class SerializationFormat(Enum):
    JSON = "json"
    MSGPACK = "msgpack"
    PROTOBUF = "protobuf"
    RAW = "raw"

class MessageSerializer(Protocol):
    def serialize(self, data: Any) -> Union[str, bytes]: ...
    def deserialize(self, data: Union[str, bytes]) -> Any: ...

class JsonSerializer:
    def serialize(self, data: Any) -> str:
        return json.dumps(data)
    def deserialize(self, data: Union[str, bytes]) -> Any:
        return json.loads(data)
```

**Why it's good:**
- OpenAI Realtime uses JSON for events
- Some protocols might use msgpack or protobuf
- Separates serialization concern from connection

**Recommendation:** Add to our design.

---

### 2. Fast Lane / Big Lane Pattern (Medium Value)

**Their approach:**
```python
class FastLaneConnection(WebSocketConnection):
    """Optimized for low latency - no queue, no metrics, no reconnect"""
    def __init__(self, url, headers):
        config = ConnectionConfig(
            enable_message_queue=False,
            enable_metrics=False,
            auto_reconnect=False,
        )

class BigLaneConnection(WebSocketConnection):
    """Full features - queue, metrics, reconnect"""
    def __init__(self, url, headers):
        config = ConnectionConfig(
            enable_message_queue=True,
            enable_metrics=True,
            auto_reconnect=True,
        )
```

**Why it's good:**
- Some use cases need minimal latency (audio streaming)
- Others need reliability (control messages)
- Configurable rather than one-size-fits-all

**Recommendation:** Add optional flags to `WebSocketConfig`:
- `enable_send_queue: bool = True`
- `enable_metrics: bool = True`

---

### 3. Connection Metrics (Medium Value)

**Their approach:**
```python
class ConnectionMetrics:
    def __init__(self):
        self.connect_count = 0
        self.messages_sent = 0
        self.bytes_sent = 0
        self.last_activity_time = None
        self.connect_time = None

    def get_stats(self) -> Dict[str, Any]:
        return {
            "connects": self.connect_count,
            "messages_sent": self.messages_sent,
            "uptime_seconds": time.time() - self.connect_time,
            "idle_seconds": time.time() - self.last_activity_time,
        }
```

**Why it's good:**
- Debugging connection issues
- Monitoring in production
- Understanding usage patterns

**Recommendation:** Add optional `ConnectionMetrics` class.

---

### 4. Send Worker Pattern (Medium Value)

**Their approach:**
```python
async def _send_worker(self) -> None:
    """Background worker for queued sends"""
    while self.state == ConnectionState.CONNECTED:
        data = await self.send_queue.get()
        await self._send_now(data)
```

**Why it's good:**
- Decouples send calls from actual sending
- Allows backpressure handling
- Smoother message flow

**Our current approach:**
- We send immediately in `send()`, no background worker
- Queue is only for receiving, not sending

**Recommendation:** Add optional send queue with worker.

---

### 5. Backpressure Handling (High Value)

**Their approach:**
```python
async def send(self, data: Any) -> None:
    if self.send_queue is not None:
        try:
            await asyncio.wait_for(
                self.send_queue.put(data),
                timeout=1.0
            )
        except asyncio.TimeoutError:
            raise ConnectionError("Send queue full - backpressure")
```

**Why it's good:**
- Prevents unbounded memory growth
- Signals when consumer is overwhelmed
- Allows caller to handle backpressure

**Recommendation:** Add to our send queue implementation.

---

### 6. Manual ping() Method (Low Value)

**Their approach:**
```python
async def ping(self) -> bool:
    """Send ping to test connection"""
    try:
        pong = await self.websocket.ping()
        await asyncio.wait_for(pong, timeout=5.0)
        return True
    except:
        return False
```

**Why it's good:**
- Test connection health on-demand
- Useful before sending important messages

**Recommendation:** Add as convenience method.

---

### 7. SSL Context Configuration (Low Value for Now)

**Their approach:**
```python
def _create_ssl_context(self) -> ssl.SSLContext:
    context = ssl.create_default_context()
    # Can be customized
    return context
```

**Why it's good:**
- Some servers need custom SSL settings
- Certificate pinning for security

**Recommendation:** Add optional `ssl_context` to config (low priority).

---

### 8. Compression Support (Low Value)

**Their approach:**
```python
self.websocket = await websockets.connect(
    self.config.url,
    compression=self.config.compression  # e.g., "deflate"
)
```

**Why it's good:**
- Reduces bandwidth for text-heavy protocols
- Built into websockets library

**Recommendation:** Add optional `compression` to config (low priority).

---

## Ideas We Already Have That They Don't

| Our Feature | Notes |
|-------------|-------|
| Async generator for messages | `async for msg in ws.messages()` |
| Multiple reconnect policies | `ExponentialBackoff`, `NoReconnect`, `FixedDelay` |
| Jitter in backoff | Prevents thundering herd |
| `on_reconnecting` callback | Know when reconnecting |
| `WebSocketMessage` wrapper | Type-safe message handling |
| Proper exception hierarchy | Specific exception types |

---

## From client.py (Higher-Level Patterns)

The `client.py` is a higher-level OpenAI Realtime client built on top of WebSocket. Not directly applicable to our infrastructure layer, but interesting patterns:

### Event Dispatcher Pattern
```python
class EventDispatcher:
    def on(self, event_type: str, handler: Callable): ...
    def off(self, event_type: str, handler: Callable): ...
    async def dispatch(self, event: RealtimeEvent): ...
```

**Assessment:** This is a higher-level concern. Our `on_message` callback is sufficient for infrastructure. The adapter layer can implement event dispatching.

### Decorator Pattern for Event Handlers
```python
@client.on_event("response.text.delta")
async def handle_text(event_data):
    pass
```

**Assessment:** Nice API, but belongs in the adapter/port layer, not infrastructure.

---

## Recommended Updates to Our Design

### Priority 1 (Should Add)

1. **Pluggable Serializers**
   - Add `MessageSerializer` protocol
   - Add `JsonSerializer`, `RawSerializer`
   - Add `serializer` param to config

2. **Backpressure Handling**
   - Add timeout to queue.put()
   - Raise specific exception when queue full

3. **Connection Metrics** (optional)
   - Add `ConnectionMetrics` class
   - Add `enable_metrics` config flag
   - Add `get_stats()` method

### Priority 2 (Nice to Have)

4. **Send Queue with Worker**
   - Add `enable_send_queue` config flag
   - Add background send worker task

5. **Manual ping() Method**
   - Add `ping() -> bool` method

6. **Connection ID**
   - Generate unique ID on connect
   - Useful for logging

### Priority 3 (Low Priority)

7. **SSL Context Config**
   - Add optional `ssl_context` to config

8. **Compression Support**
   - Add optional `compression` to config

---

## Updated Design Additions

### Serializers

```python
# chatforge/infrastructure/websocket/serializers.py

from typing import Any, Protocol, Union
import json

class MessageSerializer(Protocol):
    """Protocol for message serialization."""
    def serialize(self, data: Any) -> Union[str, bytes]: ...
    def deserialize(self, data: Union[str, bytes]) -> Any: ...

class JsonSerializer:
    """JSON serialization."""
    def serialize(self, data: Any) -> str:
        return json.dumps(data)

    def deserialize(self, data: Union[str, bytes]) -> Any:
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        return json.loads(data)

class RawSerializer:
    """Pass-through (no serialization)."""
    def serialize(self, data: Any) -> Any:
        return data

    def deserialize(self, data: Any) -> Any:
        return data
```

### Updated Config

```python
@dataclass
class WebSocketConfig:
    url: str
    headers: dict[str, str] = field(default_factory=dict)

    # ... existing fields ...

    # NEW: Performance tuning
    enable_send_queue: bool = True      # False for low-latency "fast lane"
    enable_metrics: bool = True         # False to disable metrics
    send_queue_timeout: float = 1.0     # Backpressure timeout

    # NEW: Serialization
    serializer: MessageSerializer = None  # None = raw bytes

    # NEW: Optional
    compression: str | None = None      # e.g., "deflate"
```

### Metrics

```python
# chatforge/infrastructure/websocket/metrics.py

import time
from dataclasses import dataclass, field

@dataclass
class ConnectionMetrics:
    """Track connection statistics."""
    connect_count: int = 0
    disconnect_count: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    connect_time: float | None = None
    last_activity_time: float | None = None

    def on_connect(self) -> None:
        self.connect_count += 1
        self.connect_time = time.time()

    def on_disconnect(self) -> None:
        self.disconnect_count += 1

    def on_message_sent(self, size: int) -> None:
        self.messages_sent += 1
        self.bytes_sent += size
        self.last_activity_time = time.time()

    def on_message_received(self, size: int) -> None:
        self.messages_received += 1
        self.bytes_received += size
        self.last_activity_time = time.time()

    def get_stats(self) -> dict:
        stats = {
            "connects": self.connect_count,
            "disconnects": self.disconnect_count,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
        }
        if self.connect_time:
            stats["uptime_seconds"] = time.time() - self.connect_time
        if self.last_activity_time:
            stats["idle_seconds"] = time.time() - self.last_activity_time
        return stats
```

---

## Conclusion

Our design covers the core functionality well but is missing some useful features from the existing code:

| Missing Feature | Impact | Effort |
|-----------------|--------|--------|
| Pluggable serializers | High - flexibility | Low |
| Backpressure handling | High - reliability | Low |
| Connection metrics | Medium - debugging | Low |
| Send queue with worker | Medium - performance | Medium |
| Manual ping() | Low - convenience | Low |

**Recommendation:** Update `step_by_step_implementation.md` to include serializers, backpressure, and optional metrics before implementing.
