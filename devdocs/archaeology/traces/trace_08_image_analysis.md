# Trace 08: Image Analysis

How images are analyzed using vision-capable LLMs through the ImageAnalyzer service.

---

## Entry Point

**Location:** `services/vision/analyzer.py:124` - `ImageAnalyzer` class

**Trigger:** Application code needing to analyze images:
- Processing user-uploaded screenshots
- Analyzing error images in support flows
- Extracting text from images

**Key Methods:**
```python
analyze_image(image, prompt, use_cache) → AnalysisResult       # Single image
analyze_batch(images, parallel, max_concurrent) → list[AnalysisResult]  # Multiple images
```

**Supporting Types:**
```python
ImageInfo       # Image data container (file_id, filename, data_uri, mimetype)
AnalysisResult  # Analysis result (file_id, filename, analysis, from_cache, error)
```

---

## Execution Path

### Path A: Single Image Analysis

```
ImageAnalyzer.analyze_image(image, prompt=None, use_cache=True)
├── Check cache (if enabled and cache provided)
│   ├── cache_key = self.cache_key_fn(image)  # Default: image.file_id
│   ├── cached = self.cache.get(cache_key)
│   └── If cached: return AnalysisResult(from_cache=True, analysis=cached)
├── Build LLM messages
│   ├── SystemMessage(content=self.system_prompt)
│   ├── HumanMessage with multimodal content:
│   │   ├── {"type": "text", "text": prompt or default}
│   │   └── {"type": "image_url", "image_url": {"url": image.data_uri}}
├── Invoke vision LLM
│   └── response = await self.llm.ainvoke([system_msg, human_msg])
├── Extract analysis text
│   └── analysis = str(response.content)
├── Store in cache (if enabled)
│   └── self.cache.set(cache_key, analysis)
├── Return AnalysisResult(analysis=analysis, from_cache=False)
├── On exception:
│   ├── Log error with exc_info
│   └── Return AnalysisResult(error=str(e), analysis="")
```

### Path B: Batch Analysis (Sequential)

```
ImageAnalyzer.analyze_batch(images, parallel=False, ...)
├── Check empty images list
│   └── if not images: return []
├── Apply max_images limit (takes most recent)
│   └── images = images[-max_images:]
├── For each image in images:
│   ├── result = await self.analyze_image(image, prompt, use_cache)
│   └── results.append(result)
├── Return results in same order as input
```

### Path C: Batch Analysis (Parallel)

```
ImageAnalyzer.analyze_batch(images, parallel=True, max_concurrent=3, ...)
├── Check empty images list
├── Apply max_images limit
├── Create semaphore for concurrency limit
│   └── semaphore = asyncio.Semaphore(max_concurrent)
├── Define limited analyze function:
│   └── async def analyze_with_limit(image):
│       async with semaphore:
│           return await self.analyze_image(image, prompt, use_cache)
├── Run all analyses concurrently
│   └── results = await asyncio.gather(*[analyze_with_limit(img) for img in images])
├── Return list(results)
```

### Path D: ImageInfo Creation

```
ImageInfo(
    file_id="abc123",                           # Unique identifier
    filename="screenshot.png",                  # Display name
    data_uri="data:image/png;base64,iVBOR...",  # Base64 or URL
    mimetype="image/png",                       # MIME type
    metadata={"uploaded_by": "user123"}         # Optional metadata
)
```

**Properties:**
```python
image.is_base64  # True if data_uri starts with "data:"
```

---

## Resource Management

### Vision LLM
- Passed at construction
- Should be created via `get_vision_llm()`
- Supports OpenAI GPT-4V, Claude 3, Bedrock Claude

### Cache (Optional)
- Any object implementing `CacheProtocol`:
  ```python
  class CacheProtocol(Protocol):
      def get(self, key: str) -> str | None: ...
      def set(self, key: str, value: str) -> None: ...
  ```
- Cache key function configurable
- Default: uses `image.file_id`

### Concurrency
- Parallel batch uses `asyncio.Semaphore`
- Default max_concurrent=3
- Prevents overwhelming vision API

### Memory
- Images as base64 in data_uri
- ~1.3x file size for base64 encoding
- Kept in memory during analysis

---

## Error Path

### LLM Invocation Error
```python
except Exception as e:
    logger.error(f"Error analyzing {image.filename}: {e}", exc_info=True)
    return AnalysisResult(
        file_id=image.file_id,
        filename=image.filename,
        analysis="",
        error=str(e),
    )
```
- Returns result with error field populated
- Doesn't throw - batch continues

### Invalid Image Format
```
# Handled by LLM provider
# OpenAI: 400 error if unsupported format
# Exception caught by above handler
```

### Cache Errors
```python
# If cache.get/set raises, not caught
# Would propagate to caller
# No defensive handling
```

---

## Performance Characteristics

### Vision LLM Latency
| Image Size | Latency |
|------------|---------|
| Small (<500KB) | 2-5s |
| Medium (500KB-2MB) | 3-8s |
| Large (>2MB) | 5-15s |

### Batch Processing
| Images | Sequential | Parallel (3) |
|--------|------------|--------------|
| 3 | ~12s | ~5s |
| 6 | ~24s | ~10s |
| 10 | ~40s | ~17s |

### Cache Impact
| Operation | Time |
|-----------|------|
| Cache hit | ~0.1ms |
| Cache miss | 2-15s (LLM call) |

---

## Observable Effects

### On Successful Analysis
```python
AnalysisResult(
    file_id="abc123",
    filename="screenshot.png",
    analysis="The image shows an error dialog with the message 'Connection failed'...",
    from_cache=False,
    error=None
)
```

### On Cache Hit
```python
AnalysisResult(
    file_id="abc123",
    filename="screenshot.png",
    analysis="...",  # Cached value
    from_cache=True,  # Indicates cache hit
    error=None
)
```

### On Error
```python
AnalysisResult(
    file_id="abc123",
    filename="screenshot.png",
    analysis="",
    from_cache=False,
    error="Rate limit exceeded"
)
```

### Logging
```python
logger.debug(f"ImageAnalyzer initialized with cache={'enabled' if cache else 'disabled'}")
logger.debug(f"Cache hit for {image.filename}")
logger.info(f"Analyzing image: {image.filename}")
logger.info(f"Analysis complete for {image.filename}: {len(analysis)} chars")
logger.error(f"Error analyzing {image.filename}: {e}", exc_info=True)
logger.info(f"Starting parallel analysis of {len(images)} images (max concurrent: {max_concurrent})")
logger.info(f"Limiting to {max_images} most recent images (total: {len(images)})")
```

---

## Why This Design

### Service Pattern
**Choice:** Dedicated ImageAnalyzer service class

**Rationale:**
- Encapsulates vision LLM usage
- Configurable prompts and caching
- Reusable across application

**Trade-off:**
- Another abstraction layer
- Must instantiate and pass around

### Base64 Data URIs
**Choice:** Images as data:image/... URIs

**Rationale:**
- Standard format for vision APIs
- No separate file hosting needed
- Works with all providers

**Trade-off:**
- Large payloads (~1.3x file size)
- Must encode before use
- Memory intensive

### Optional Caching
**Choice:** Cache is injectable, not built-in

**Rationale:**
- Flexibility in cache implementation
- Can use Redis, memory, disk, etc.
- No default cache avoids side effects

**Trade-off:**
- Must wire up cache manually
- No caching out of the box
- Extra configuration

### Graceful Error Handling
**Choice:** Return error in result, don't throw

**Rationale:**
- Batch can continue after failures
- All results returned, caller decides
- No partial batch loss

**Trade-off:**
- Must check `.is_success` on each result
- Errors might be ignored

---

## What Feels Incomplete

1. **No image resizing**
   - Large images sent as-is
   - Could exceed API limits
   - Should resize to optimal size

2. **No format validation**
   - Accepts any data_uri
   - Vision APIs have format requirements
   - Fails only at API call

3. **No progress callback**
   - Batch analysis could take minutes
   - No way to report progress
   - UI can't show status

4. **No retry logic**
   - Single failure = error result
   - Could retry transient failures
   - Rate limits not handled

5. **No streaming analysis**
   - Wait for complete response
   - Could stream partial results
   - Better UX for long analyses

---

## What Feels Vulnerable

1. **Memory exhaustion**
   ```python
   images = [ImageInfo(...), ...]  # 10 x 5MB images = 65MB in memory
   ```
   - Base64 images held in memory
   - Parallel processing multiplies
   - Could OOM with many large images

2. **No image sanitization**
   - data_uri passed directly to LLM
   - Malformed URIs could cause issues
   - No validation of image content

3. **Cache key predictability**
   ```python
   cache_key_fn = lambda img: img.file_id
   ```
   - Default uses file_id directly
   - If file_id is guessable, cache can be poisoned
   - Should hash or namespace

4. **Parallel concurrency leaks**
   ```python
   semaphore = asyncio.Semaphore(max_concurrent)
   # Not passed to analyze_image, created fresh
   ```
   - Each batch call creates new semaphore
   - Concurrent batch calls don't share limit
   - Could exceed desired concurrency

5. **No timeout**
   - Vision analysis can take 15+ seconds
   - No way to cancel stuck analysis
   - Caller waits indefinitely

---

## What Feels Like Bad Design

1. **Duplicate logging in batch**
   ```python
   # analyze_image logs: "Analyzing image: {filename}"
   # analyze_batch logs: "Starting parallel analysis..."
   # Double logging for same operation
   ```
   - Redundant log messages
   - Hard to correlate in logs

2. **max_images takes from end**
   ```python
   images = images[-max_images:]  # Most recent
   ```
   - Assumes list is ordered by time
   - Not documented or enforced
   - Could be confusing

3. **format_analysis_results is standalone**
   ```python
   def format_analysis_results(results: list[AnalysisResult]) -> str:
   ```
   - Module-level function, not method
   - Inconsistent with class-based service
   - Should be method or in separate module

4. **CacheProtocol not exported**
   - Defined in analyzer.py
   - Not in __init__.py exports
   - Hard to implement cache correctly

5. **Prompt parameter overloading**
   ```python
   async def analyze_image(self, image, prompt=None, ...):
       # prompt overrides default analysis request
       # But system_prompt is separate
   ```
   - Two prompt concepts: system_prompt and prompt
   - Confusing which controls what
   - Should be clearer names

6. **No type hints for cache**
   ```python
   def __init__(self, ..., cache: CacheProtocol | None = None, ...):
   ```
   - CacheProtocol used but TYPE_CHECKING import
   - Runtime type not enforced
   - Any duck-typed object works (could be intentional)
