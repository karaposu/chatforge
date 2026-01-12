# Rate Limiter Infrastructure

## Overview

A generic, domain-agnostic rate limiter for controlling the frequency of operations. Used by adapters to respect external API quotas and prevent resource exhaustion.

---

## Part 1: Design Principles

### What Makes a Good Rate Limiter?

A rate limiter should be:

1. **Generic** - Works for any operation, not tied to HTTP or specific APIs
2. **Composable** - Multiple limiters can be combined
3. **Observable** - Exposes metrics for monitoring
4. **Non-blocking option** - Both blocking and try-acquire modes
5. **Fair** - FIFO ordering for waiters (optional)
6. **Efficient** - O(1) operations, minimal memory

### Core Abstraction

The rate limiter answers one question: **"Can I do this operation now?"**

```python
class RateLimiter(ABC):
    """Abstract rate limiter interface."""

    @abstractmethod
    async def acquire(self, permits: int = 1) -> None:
        """
        Acquire permits, waiting if necessary.

        Args:
            permits: Number of permits to acquire

        Raises:
            asyncio.CancelledError: If cancelled while waiting
        """
        ...

    @abstractmethod
    def try_acquire(self, permits: int = 1) -> bool:
        """
        Try to acquire permits without waiting.

        Args:
            permits: Number of permits to acquire

        Returns:
            True if permits were acquired, False otherwise
        """
        ...

    @abstractmethod
    async def acquire_with_timeout(
        self,
        permits: int = 1,
        timeout: float = None,
    ) -> bool:
        """
        Acquire permits with timeout.

        Args:
            permits: Number of permits to acquire
            timeout: Maximum time to wait in seconds

        Returns:
            True if permits were acquired, False if timeout
        """
        ...
```

### Why Not Use Existing Libraries?

| Library | Issue |
|---------|-------|
| `aiolimiter` | Good, but no composability or metrics |
| `limits` | Sync-only, designed for web frameworks |
| `ratelimit` | Decorator-only, no programmatic control |

A custom implementation gives us:
- Async-native design
- Composable limiters (chain, combine)
- Built-in metrics
- Chatforge-specific features (see Part 2)

---

## Part 2: Algorithm Choice

### Token Bucket (Recommended)

**How it works:**
- Bucket holds tokens (up to `capacity`)
- Tokens added at constant rate (`refill_rate`)
- Operations consume tokens
- If not enough tokens, wait or reject

```
Capacity: 10 tokens
Refill: 2 tokens/second

Time 0:    [■■■■■■■■■■] 10/10  ← Full
Request 3: [■■■■■■■□□□] 7/10   ← Consumed 3
Time +1s:  [■■■■■■■■■□] 9/10   ← Refilled 2
Request 5: [■■■■□□□□□□] 4/10   ← Consumed 5
```

**Pros:**
- Allows bursts (up to capacity)
- Smooth rate over time
- Simple to understand
- O(1) operations

**Cons:**
- Burst at start can overwhelm services
- Requires tuning two parameters

### Leaky Bucket

**How it works:**
- Fixed-size queue of pending requests
- Requests "leak" out at constant rate
- New requests added to queue (or rejected if full)

```
Queue capacity: 5
Leak rate: 2/second

Requests arrive: [R1][R2][R3][R4][R5]
                  ↓   ↓   ↓   ↓   ↓
Queue:          [■■■■■]
                  ↓ (leak 2/sec)
Output:         R1, R2 ... R3, R4 ... R5
```

**Pros:**
- Perfectly smooth output rate
- No bursting

**Cons:**
- Adds latency (queuing)
- Can drop requests if queue full
- Less intuitive

### Sliding Window

**How it works:**
- Count requests in rolling time window
- Reject if count exceeds limit

```
Window: 1 second
Limit: 10 requests

Time 0.0-1.0: [■■■■■■■■■■] 10 requests ← At limit
Time 0.5-1.5: [■■■■■□□□□□] 5 requests  ← Window slid, room for more
```

**Pros:**
- Precise rate control
- No burst at window boundaries

**Cons:**
- Memory overhead (store timestamps)
- More complex implementation

### Recommendation: Token Bucket

For chatforge, **token bucket** is the best choice:
- Simple and efficient
- Allows controlled bursting (good for real-time audio)
- Well-understood by developers
- Easy to configure per API's limits

---

## Part 3: Implementation

### Core Token Bucket

```python
import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RateLimiterConfig:
    """Configuration for token bucket rate limiter."""

    rate: float
    """Tokens added per second."""

    capacity: int
    """Maximum tokens in bucket."""

    initial_tokens: Optional[int] = None
    """Starting tokens. Defaults to capacity."""

    name: str = "default"
    """Name for metrics and logging."""


@dataclass
class RateLimiterMetrics:
    """Metrics for rate limiter observation."""

    total_acquisitions: int = 0
    """Total successful acquisitions."""

    total_rejections: int = 0
    """Total try_acquire rejections."""

    total_wait_time_ms: float = 0.0
    """Cumulative time spent waiting."""

    current_tokens: float = 0.0
    """Current token count (snapshot)."""

    waiters: int = 0
    """Current number of waiters."""


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter.

    Allows controlled bursting while maintaining average rate.
    Thread-safe for single-threaded async (asyncio).

    Example:
        limiter = TokenBucketRateLimiter(
            RateLimiterConfig(rate=10, capacity=20)
        )

        # Blocking acquire
        await limiter.acquire()
        do_operation()

        # Non-blocking
        if limiter.try_acquire():
            do_operation()
        else:
            handle_rate_limited()

        # With timeout
        if await limiter.acquire_with_timeout(timeout=1.0):
            do_operation()
    """

    def __init__(self, config: RateLimiterConfig) -> None:
        self._config = config
        self._tokens = config.initial_tokens or config.capacity
        self._last_refill = time.monotonic()
        self._waiters: list[asyncio.Event] = []
        self._metrics = RateLimiterMetrics()
        self._lock = asyncio.Lock()

    @property
    def config(self) -> RateLimiterConfig:
        """Current configuration."""
        return self._config

    def get_metrics(self) -> RateLimiterMetrics:
        """Get current metrics snapshot."""
        self._refill()
        self._metrics.current_tokens = self._tokens
        self._metrics.waiters = len(self._waiters)
        return self._metrics

    async def acquire(self, permits: int = 1) -> None:
        """Acquire permits, waiting if necessary."""
        async with self._lock:
            self._refill()

            while self._tokens < permits:
                # Calculate wait time
                needed = permits - self._tokens
                wait_time = needed / self._config.rate

                # Create waiter
                event = asyncio.Event()
                self._waiters.append(event)

                try:
                    # Release lock while waiting
                    self._lock.release()
                    start = time.monotonic()

                    await asyncio.sleep(wait_time)

                    self._metrics.total_wait_time_ms += (
                        (time.monotonic() - start) * 1000
                    )

                    await self._lock.acquire()
                    self._refill()
                finally:
                    if event in self._waiters:
                        self._waiters.remove(event)

            self._tokens -= permits
            self._metrics.total_acquisitions += 1

    def try_acquire(self, permits: int = 1) -> bool:
        """Try to acquire permits without waiting."""
        self._refill()

        if self._tokens >= permits:
            self._tokens -= permits
            self._metrics.total_acquisitions += 1
            return True

        self._metrics.total_rejections += 1
        return False

    async def acquire_with_timeout(
        self,
        permits: int = 1,
        timeout: float = None,
    ) -> bool:
        """Acquire permits with timeout."""
        if timeout is None:
            await self.acquire(permits)
            return True

        try:
            await asyncio.wait_for(
                self.acquire(permits),
                timeout=timeout,
            )
            return True
        except asyncio.TimeoutError:
            self._metrics.total_rejections += 1
            return False

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_refill

        # Add tokens for elapsed time
        new_tokens = elapsed * self._config.rate
        self._tokens = min(self._config.capacity, self._tokens + new_tokens)
        self._last_refill = now
```

### Composable Limiters

Multiple limiters can be combined:

```python
class CompositeRateLimiter:
    """
    Combines multiple rate limiters.

    All limiters must allow the operation for it to proceed.
    Useful for respecting multiple limits (per-second + per-minute).

    Example:
        # OpenAI: 50 req/sec AND 10000 req/day
        per_second = TokenBucketRateLimiter(
            RateLimiterConfig(rate=50, capacity=50)
        )
        per_day = TokenBucketRateLimiter(
            RateLimiterConfig(rate=10000/86400, capacity=10000)
        )

        limiter = CompositeRateLimiter([per_second, per_day])
        await limiter.acquire()
    """

    def __init__(self, limiters: list[TokenBucketRateLimiter]) -> None:
        self._limiters = limiters

    async def acquire(self, permits: int = 1) -> None:
        """Acquire from all limiters."""
        for limiter in self._limiters:
            await limiter.acquire(permits)

    def try_acquire(self, permits: int = 1) -> bool:
        """Try to acquire from all limiters (atomic)."""
        # Check all first
        for limiter in self._limiters:
            if not limiter.try_acquire(permits):
                return False
        return True


class KeyedRateLimiter:
    """
    Per-key rate limiting.

    Creates separate limiters for different keys (users, API keys, etc.).

    Example:
        limiter = KeyedRateLimiter(
            factory=lambda: TokenBucketRateLimiter(
                RateLimiterConfig(rate=10, capacity=20)
            )
        )

        await limiter.acquire("user_123")
        await limiter.acquire("user_456")  # Independent limit
    """

    def __init__(
        self,
        factory: Callable[[], TokenBucketRateLimiter],
        max_keys: int = 10000,
    ) -> None:
        self._factory = factory
        self._limiters: dict[str, TokenBucketRateLimiter] = {}
        self._max_keys = max_keys

    async def acquire(self, key: str, permits: int = 1) -> None:
        """Acquire permits for a specific key."""
        limiter = self._get_or_create(key)
        await limiter.acquire(permits)

    def _get_or_create(self, key: str) -> TokenBucketRateLimiter:
        if key not in self._limiters:
            if len(self._limiters) >= self._max_keys:
                # Evict oldest (simple LRU would be better)
                oldest = next(iter(self._limiters))
                del self._limiters[oldest]

            self._limiters[key] = self._factory()

        return self._limiters[key]
```

---

## Part 4: Chatforge-Specific Features

### 1. API-Aware Presets

Pre-configured limiters for common APIs:

```python
class APIRateLimits:
    """Pre-configured rate limits for common APIs."""

    @staticmethod
    def openai_realtime() -> TokenBucketRateLimiter:
        """OpenAI Realtime API limits."""
        return TokenBucketRateLimiter(
            RateLimiterConfig(
                rate=50,           # 50 events/second
                capacity=100,      # Allow burst of 100
                name="openai_realtime",
            )
        )

    @staticmethod
    def openai_chat() -> CompositeRateLimiter:
        """OpenAI Chat API limits (tiered)."""
        return CompositeRateLimiter([
            # RPM limit
            TokenBucketRateLimiter(
                RateLimiterConfig(rate=500/60, capacity=500, name="openai_rpm")
            ),
            # TPM limit (approximate, actual is token-based)
            TokenBucketRateLimiter(
                RateLimiterConfig(rate=30000/60, capacity=30000, name="openai_tpm")
            ),
        ])

    @staticmethod
    def elevenlabs_tts() -> TokenBucketRateLimiter:
        """ElevenLabs TTS API limits."""
        return TokenBucketRateLimiter(
            RateLimiterConfig(
                rate=2,            # 2 requests/second
                capacity=5,        # Small burst
                name="elevenlabs",
            )
        )

    @staticmethod
    def anthropic_claude() -> TokenBucketRateLimiter:
        """Anthropic Claude API limits."""
        return TokenBucketRateLimiter(
            RateLimiterConfig(
                rate=50/60,        # 50 RPM
                capacity=10,       # Allow small burst
                name="anthropic",
            )
        )
```

### 2. Audio-Optimized Rate Limiter

For real-time audio, we need predictable timing:

```python
class AudioRateLimiter(TokenBucketRateLimiter):
    """
    Rate limiter optimized for audio streaming.

    Features:
    - Prioritizes consistent timing over strict rate
    - Pre-acquires permits to reduce jitter
    - Warns on potential underrun
    """

    def __init__(
        self,
        config: RateLimiterConfig,
        chunk_duration_ms: float = 20.0,
    ) -> None:
        super().__init__(config)
        self._chunk_duration_ms = chunk_duration_ms
        self._underrun_callback: Optional[Callable[[], None]] = None

    def set_underrun_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for underrun warnings."""
        self._underrun_callback = callback

    async def acquire_for_audio(self) -> None:
        """
        Acquire permit for audio chunk.

        Warns if wait time would cause audio underrun.
        """
        self._refill()

        if self._tokens < 1:
            needed = 1 - self._tokens
            wait_time_ms = (needed / self._config.rate) * 1000

            if wait_time_ms > self._chunk_duration_ms:
                # Would cause underrun
                if self._underrun_callback:
                    self._underrun_callback()

        await self.acquire(1)
```

### 3. Adaptive Rate Limiter

Adjusts rate based on API response headers:

```python
class AdaptiveRateLimiter(TokenBucketRateLimiter):
    """
    Rate limiter that adapts based on API feedback.

    Reads rate limit headers from responses and adjusts accordingly.

    Supported headers:
    - X-RateLimit-Limit
    - X-RateLimit-Remaining
    - X-RateLimit-Reset
    - Retry-After
    """

    async def acquire_and_track(
        self,
        response_headers: Optional[dict] = None,
    ) -> None:
        """Acquire and optionally update from response headers."""
        await self.acquire()

        if response_headers:
            self._update_from_headers(response_headers)

    def _update_from_headers(self, headers: dict) -> None:
        """Update rate limit from response headers."""
        # Check for rate limit info
        remaining = headers.get("X-RateLimit-Remaining")
        reset = headers.get("X-RateLimit-Reset")
        retry_after = headers.get("Retry-After")

        if retry_after:
            # We hit the limit, back off
            self._tokens = 0
            # Could also adjust rate here

        if remaining is not None:
            # Sync our token count with server's view
            self._tokens = min(self._tokens, int(remaining))
```

### 4. Context Manager Support

Clean usage pattern:

```python
class RateLimitedContext:
    """
    Context manager for rate-limited operations.

    Example:
        async with rate_limited(limiter, permits=1):
            await api.call()
    """

    def __init__(
        self,
        limiter: TokenBucketRateLimiter,
        permits: int = 1,
        timeout: Optional[float] = None,
    ) -> None:
        self._limiter = limiter
        self._permits = permits
        self._timeout = timeout

    async def __aenter__(self) -> None:
        if self._timeout:
            acquired = await self._limiter.acquire_with_timeout(
                self._permits,
                self._timeout,
            )
            if not acquired:
                raise RateLimitExceededError("Timeout waiting for rate limit")
        else:
            await self._limiter.acquire(self._permits)

    async def __aexit__(self, *args) -> None:
        pass  # Nothing to release


def rate_limited(
    limiter: TokenBucketRateLimiter,
    permits: int = 1,
    timeout: float = None,
) -> RateLimitedContext:
    """Create rate-limited context manager."""
    return RateLimitedContext(limiter, permits, timeout)
```

### 5. Decorator Support

For simple function wrapping:

```python
def rate_limit(
    limiter: TokenBucketRateLimiter,
    permits: int = 1,
):
    """
    Decorator for rate-limited functions.

    Example:
        @rate_limit(api_limiter)
        async def call_api():
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            await limiter.acquire(permits)
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

---

## Part 5: Usage in Chatforge Adapters

### RealtimeVoiceAPIPort Adapter

```python
class OpenAIRealtimeAdapter(RealtimeVoiceAPIPort):
    """OpenAI Realtime API adapter with rate limiting."""

    def __init__(
        self,
        api_key: str,
        rate_limiter: TokenBucketRateLimiter = None,
    ) -> None:
        self._api_key = api_key
        self._rate_limiter = rate_limiter or APIRateLimits.openai_realtime()
        self._ws: Optional[WebSocketClient] = None

    async def send_audio(self, chunk: bytes) -> None:
        """Send audio chunk with rate limiting."""
        await self._rate_limiter.acquire()

        message = {
            "type": "input_audio_buffer.append",
            "audio": base64.b64encode(chunk).decode(),
        }
        await self._ws.send_json(message)

    async def send_text(self, text: str) -> None:
        """Send text with rate limiting."""
        await self._rate_limiter.acquire()

        message = {
            "type": "conversation.item.create",
            "item": {"type": "message", "content": [{"type": "text", "text": text}]},
        }
        await self._ws.send_json(message)
```

### TTSPort Adapter

```python
class ElevenLabsTTSAdapter(TTSPort):
    """ElevenLabs TTS adapter with rate limiting."""

    def __init__(
        self,
        api_key: str,
        rate_limiter: TokenBucketRateLimiter = None,
    ) -> None:
        self._api_key = api_key
        self._rate_limiter = rate_limiter or APIRateLimits.elevenlabs_tts()

    async def synthesize(self, text: str, voice: VoiceConfig) -> AudioResult:
        """Synthesize text with rate limiting."""
        async with rate_limited(self._rate_limiter):
            response = await self._http.post(
                f"/text-to-speech/{voice.voice_id}",
                json={"text": text},
            )
            return AudioResult(audio=response.content)

    async def synthesize_stream(
        self,
        text: str,
        voice: VoiceConfig,
    ) -> AsyncIterator[bytes]:
        """Stream synthesis with rate limiting."""
        async with rate_limited(self._rate_limiter):
            async with self._http.stream(
                "POST",
                f"/text-to-speech/{voice.voice_id}/stream",
                json={"text": text},
            ) as response:
                async for chunk in response.aiter_bytes():
                    yield chunk
```

### Shared Limiter Registry

```python
class RateLimiterRegistry:
    """
    Central registry for rate limiters.

    Allows sharing limiters across adapters for the same API.

    Example:
        registry = RateLimiterRegistry()

        # Both adapters share the same OpenAI limit
        realtime = OpenAIRealtimeAdapter(
            rate_limiter=registry.get("openai")
        )
        chat = OpenAIChatAdapter(
            rate_limiter=registry.get("openai")
        )
    """

    def __init__(self) -> None:
        self._limiters: dict[str, TokenBucketRateLimiter] = {}

    def register(
        self,
        name: str,
        limiter: TokenBucketRateLimiter,
    ) -> None:
        """Register a named limiter."""
        self._limiters[name] = limiter

    def get(self, name: str) -> Optional[TokenBucketRateLimiter]:
        """Get a limiter by name."""
        return self._limiters.get(name)

    def get_or_create(
        self,
        name: str,
        factory: Callable[[], TokenBucketRateLimiter],
    ) -> TokenBucketRateLimiter:
        """Get or create a limiter."""
        if name not in self._limiters:
            self._limiters[name] = factory()
        return self._limiters[name]
```

---

## Part 6: File Structure

```
chatforge/infrastructure/
├── __init__.py
├── websocket/           # Existing
│   └── ...
└── rate_limiter/        # NEW
    ├── __init__.py
    ├── base.py          # RateLimiter ABC, Config, Metrics
    ├── token_bucket.py  # TokenBucketRateLimiter
    ├── composite.py     # CompositeRateLimiter, KeyedRateLimiter
    ├── presets.py       # APIRateLimits
    ├── audio.py         # AudioRateLimiter
    ├── adaptive.py      # AdaptiveRateLimiter
    └── registry.py      # RateLimiterRegistry

tests/infrastructure/
└── rate_limiter/
    ├── test_token_bucket.py
    ├── test_composite.py
    └── test_presets.py
```

---

## Summary

| Component | Purpose |
|-----------|---------|
| `TokenBucketRateLimiter` | Core algorithm, generic |
| `CompositeRateLimiter` | Combine multiple limits |
| `KeyedRateLimiter` | Per-key (user/API key) limits |
| `APIRateLimits` | Presets for OpenAI, ElevenLabs, etc. |
| `AudioRateLimiter` | Optimized for real-time audio |
| `AdaptiveRateLimiter` | Adjusts from response headers |
| `RateLimiterRegistry` | Share limiters across adapters |

The design is **generic first** (token bucket works for anything), then **specialized** for chatforge's voice AI use cases (audio optimization, API presets).
