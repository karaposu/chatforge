Asynchronous Python Rate Limiting Libraries

Several mature libraries provide async/await–compatible rate limiting. Top options include token-bucket or leaky-bucket limiters, many with decorators or context-manager interfaces, and support for in‑memory or distributed backends. For example, Throttled-py (532★) is a high-performance library supporting both sync and async code, multiple algorithms (token bucket, leaky bucket, fixed/sliding window, GCRA), and Redis/in‑memory backends
github.com
. A Throttled-py limiter can be used in async code like:

from throttled.asyncio import RateLimiterType, Throttled, rate_limiter

# Token-bucket: 1000 tokens per second, burst up to 1000.
throttle = Throttled(using=RateLimiterType.TOKEN_BUCKET.value,
                     quota=rate_limiter.per_sec(1000, burst=1000))
async def call_api():
    result = await throttle.limit("/ping", cost=1)  # returns RateLimitResult
    return result.limited


This enforces the rate per “key” (here "/ping") and supports decorators or context managers as well
github.com
github.com
. Throttled-py is ideal for high-throughput scenarios (e.g. thousands of calls/sec), and can use Redis to share limits across processes. Its docs and GitHub repo provide full examples and explain sync vs async usage
github.com
github.com
.

PyrateLimiter (★)

PyrateLimiter (≈600★) is a mature rate-limiter supporting sync and async, with multiple backends (in-memory, SQLite, Redis) and advanced features. You define Rate(limit, duration) objects and attach them to buckets. For example, to allow 5 requests every 2 seconds:

from pyrate_limiter import Duration, Rate, Limiter

limiter = Limiter(Rate(5, Duration.SECOND * 2))
for i in range(6):
    limiter.try_acquire(str(i))  # blocks until available
    print(f"Acquired permit {i}")
# In non-blocking mode:
success = limiter.try_acquire(str(i), blocking=False) 


This enforces 5 acquisitions per 2-second window
github.com
. PyrateLimiter also provides decorators and transports for aiohttp/httpx (e.g. AsyncRateLimiterTransport) so you can easily wrap API calls. It excels in cases needing durable persistence (e.g. Redis or SQLite) or complex multi-rate limits (e.g. per-second and per-minute limits at once). See its Quickstart and HTTPX examples
github.com
github.com
.

aiolimiter (★)

aiolimiter is a simple, lightweight leaky-bucket limiter for asyncio. It provides an AsyncLimiter(max_rate, time_period) context manager. For example:

from aiolimiter import AsyncLimiter

limiter = AsyncLimiter(100, time_period=60)  # 100 calls per 60 seconds
async with limiter:
    # this block runs at most 100 times per minute
    await call_api()


You can also await limiter.acquire() directly to block until a slot is free
aiolimiter.readthedocs.io
. aiolimiter is fast and precise (counts “capacity” units), supports fractional consumption, and is ideal for in-process rate limiting (e.g. to throttle async API calls in an application)
aiolimiter.readthedocs.io
aiolimiter.readthedocs.io
. It has no external dependencies and works out-of-the-box on any asyncio event loop.

limiter (alexdelorenzo/limiter) (★)

limiter uses a token-bucket algorithm with thread- and async-safety. You create a Limiter(rate, capacity, consume) instance and use it as a decorator or async context manager. For example:

from limiter import Limiter
limit_downloads = Limiter(rate=2, capacity=5, consume=2)

@limit_downloads
async def download_image(url: str) -> bytes:
    async with ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.read()


This enforces an average of 2 tokens/second and allows bursts (capacity=5)
github.com
. The same Limiter can be reused for multiple functions or blocks (even switching buckets)
github.com
github.com
. It supports async decorators and async with limiter:, so it can be dropped into any async workflow. Its small footprint and built-in jitter make it a good general-purpose limiter.

asynciolimiter (neonious/asynciolimiter)

asynciolimiter provides three algorithms (regular, strict, leaky bucket) with async wait() and wrap() methods. For example, to limit 1 call per 3 seconds:

import asyncio
from asynciolimiter import Limiter

rate_limiter = Limiter(1/3)  # 1 call per 3 seconds on average
async def request():
    await rate_limiter.wait()
    print("hello")
asyncio.run(asyncio.gather(*(request() for _ in range(10))))


This scheduler ensures calls are paced correctly
asynciolimiter.readthedocs.io
. It’s easy to use for simple rate limits and has configurable burst (max_burst) if needed. Although less feature-rich than throttled-py, it’s a lightweight choice when you just need plain request-per-second limiting in async code
asynciolimiter.readthedocs.io
.

asyncio-throttle (hallazzang/asyncio-throttle)

A very minimalist limiter, asyncio-throttle provides a Throttler(rate_limit, period) context manager. E.g.:

from asyncio_throttle import Throttler

throttler = Throttler(rate_limit=500, period=60)  # 500 calls per 60s
async with throttler:
    await send_request()


This will block as needed to enforce the given rate
pypi.org
. It’s simple (no decorators), suitable for light use, and thread-safe. Use-case: easily throttling async tasks in a loop or across a few coroutines without a heavier dependency
pypi.org
.

ratelimit-io (bagowix/ratelimit-io)

ratelimit-io is a bidirectional Redis-based limiter. It lets you declare incoming or outgoing limits and handles 429 errors automatically. In async mode you can do:

from ratelimit_io import RatelimitIO, LimitSpec
from redis.asyncio import Redis

redis = Redis(host="localhost", port=6379)
async_limiter = RatelimitIO(backend=redis,
                           default_limit=LimitSpec(requests=10, seconds=60))

@async_limiter
async def fetch_data():
    return "Request succeeded!"
await fetch_data()  # respects 10req/min limit


Or use it as a context manager (async with limiter:) or call await limiter.a_wait(key) before requests
github.com
. This library shines in distributed setups (Redis-backed, atomic via Lua scripts) and frameworks: it includes middleware examples for FastAPI/Django/Flask that return proper 429 responses. It’s ideal when you need global rate limits across processes or detailed control of incoming vs outgoing limits
github.com
.

redis-rate-limiters (otovo/redis-rate-limiters)

This library provides AsyncSemaphore and AsyncTokenBucket classes backed by Redis. For example, to allow 5 concurrent requests (semaphore) or 100 requests/minute (token bucket) per key:

from redis.asyncio import Redis
from limiters import AsyncTokenBucket

limiter = AsyncTokenBucket(
    name="foo", capacity=5,
    refill_frequency=1, refill_amount=1,
    max_sleep=30,
    connection=Redis.from_url("redis://localhost:6379"))
async with limiter:
    await client.get("https://api.example.com")


This enforces a token-bucket limit across all clients using the same Redis key
github.com
github.com
. Likewise, AsyncSemaphore(name, capacity) enforces concurrent-access limits
github.com
. Because it uses Redis and Lua scripts, it’s robust and atomic, making it suitable for high-reliability distributed systems (e.g. multiple web servers coordinating limits). Its interface (context managers) is pluggable into any async code. (A sync version also exists for thread/process code.)

limits (alisaifee/limits)

limits is a battle-tested library (587★) underlying Flask-Limiter, supporting many strategies (fixed window, moving/sliding window, leaky bucket) and backends (Redis, Memcached, MongoDB). It offers identical APIs in sync or async mode. Example usage (sync):

from limits import strategies, RateLimitItemPerMinute
from limits.storage import MemoryStorage

storage = MemoryStorage()
strategy = strategies.FixedWindowRateLimiter(storage)
one_per_min = RateLimitItemPerMinute(1, 1)
if strategy.hit(one_per_min, "ns", "foo"):
    print("allowed")
else:
    print("rate limited")


This will allow 1 request/min for key "foo" in namespace "ns"
github.com
. The same can be done asynchronously by using limits.aio variants. This library is ideal if you need flexible window strategies or existing support for many backends. It also provides utilities to parse rate strings (e.g. "10/minute") and query remaining quota and reset times. See its documentation for decorators and async examples.

Sources: Official docs and GitHub repos for each library (see cited lines) confirm async support, usage patterns, and features
github.com
github.com
aiolimiter.readthedocs.io
github.com
asynciolimiter.readthedocs.io
pypi.org
github.com
github.com
github.com
. These libraries are actively maintained and widely used in Python projects for rate-limiting API calls.