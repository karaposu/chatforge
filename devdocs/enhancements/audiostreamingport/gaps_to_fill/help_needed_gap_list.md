# AudioStreamPort: Gaps Requiring Testing or External Info

**Date:** 2025-01-01
**Scope:** Local audio I/O only

---

## Category 1: Requires Live Testing

### 1.1 VAD Pre-buffer Behavior

**Question:** How does VAD pre-buffer work exactly? Does `on_speech_end` callback provide the buffered audio?

**What we know from code:**
- `VADetector` has `get_pre_buffer()` method
- `on_speech_end` callback takes NO arguments (just `Callable[[], None]`)
- Pre-buffer is stored in `self.pre_buffer` deque

**Gap:** Need to test how to retrieve pre-buffered audio when speech ends.

**Test needed:**
```python
# Test: How to get pre-buffer audio?
vad = VADetector(
    config=VADConfig(pre_buffer_ms=300),
    on_speech_start=lambda: print("speech start"),
    on_speech_end=lambda: print("speech end")  # No audio passed!
)

# When on_speech_end fires, do we call vad.get_pre_buffer()?
```

**Impact:** Affects how we expose VAD in AudioStreamPort.

---

### 1.2 Actual End-to-End Latency

**Question:** What is the actual latency from microphone to `asyncio.Queue`?

**What we know from code:**
- REALTIME mode targets <20ms
- Uses triple-buffered capture
- Has callback → queue → async queue pipeline

**Gap:** Need to measure actual latency in practice.

**Test needed:**
```python
# Measure: Time from sound → chunk in queue
import time
vs = VoxStream(mode=ProcessingMode.REALTIME)
queue = await vs.start_capture_stream()

# Play a click, measure when it appears in queue
```

**Impact:** Affects latency guarantees we can promise.

---

### 1.3 Barge-in Behavior

**Question:** How does `interrupt_playback()` behave exactly?

- Does it stop immediately?
- Is there a fade-out?
- Does it clear the buffer completely?

**Test needed:**
```python
vs.queue_playback(long_audio)  # Queue 5 seconds
await asyncio.sleep(0.5)
vs.interrupt_playback()
# What happens? Immediate silence? Fade out?
```

**Impact:** Affects barge-in UX.

---

### 1.4 Device Disconnection Handling

**Question:** What happens if audio device is disconnected during capture?

**What we know:**
- `CaptureMetrics` tracks `buffer_overruns`
- Callback checks `status.input_overflow`

**Gap:** No explicit device disconnect handling visible in code.

**Test needed:**
- Start capture
- Unplug USB microphone
- What error/event occurs?

**Impact:** Error handling design.

---

### 1.5 Queue Backpressure

**Question:** What happens when `asyncio.Queue` is full?

**What we know from code:**
```python
# io/capture.py:100
self.audio_queue: asyncio.Queue[AudioBytes] = asyncio.Queue(maxsize=30)

# If consumer is slow, queue fills up
```

**Gap:** Need to verify behavior when queue is full.

**Impact:** Consumer must keep up or risk dropping audio.

---

## Category 2: Design Decisions Needed

### 2.1 VAD Callback Signature

**Current VoxStream:** `on_speech_end: Callable[[], None]` (no audio)

**Our proposed design:** `on_speech_end: Callable[[bytes], None]` (with audio)

**Decision needed:**
- Option A: Match VoxStream (no audio in callback, call `get_pre_buffer()` separately)
- Option B: Wrap and provide audio (adapter responsibility)
- Option C: Change AudioStreamPort interface to not pass audio

**Recommendation:** Option B - Adapter wraps and provides pre-buffer audio

---

### 2.2 Queue vs AsyncGenerator for Capture

**VoxStream returns:** `asyncio.Queue[bytes]`

**Our design proposed:** `AsyncGenerator[bytes, None]`

**Decision needed:**
- Option A: Match VoxStream (return Queue)
- Option B: Wrap Queue in AsyncGenerator (cleaner interface)

**Recommendation:** Option B - Wrap in generator for cleaner `async for` usage

```python
# Wrapper in adapter:
async def start_capture(self) -> AsyncGenerator[bytes, None]:
    queue = await self._voxstream.start_capture_stream()
    while self._capturing:
        try:
            chunk = await asyncio.wait_for(queue.get(), timeout=1.0)
            yield chunk
        except asyncio.TimeoutError:
            continue
```

---

## Category 3: Low Priority / Future

### 3.1 Echo Cancellation

**Question:** Does VoxStream handle echo cancellation?

**What we know:** Not visible in code. Likely relies on OS/hardware AEC.

**Impact:** May need external solution for voice apps.

---

### 3.2 Audio Level Monitoring

**Question:** How to get real-time audio levels for UI?

**What we know:**
- VAD calculates energy internally
- No direct `get_input_level()` method exposed in VoxStream facade

**Impact:** UI feedback (optional feature).

---

### 3.3 WebRTC Browser Audio Format

**Question:** What format does browser MediaStream API produce?

**Expected:** Float32, 48kHz, stereo (varies by browser)

**Source:** MDN Web Audio API documentation

**Impact:** WebRTCAudioAdapter conversion requirements (future adapter).

---

### 3.4 Twilio Media Streams Format

**Question:** Exact format of Twilio Media Streams audio?

**Expected:** μ-law, 8kHz, mono

**Source:** Twilio Media Streams documentation

**Impact:** TwilioAudioAdapter conversion requirements (future adapter).

---

## Summary: Blockers Before Implementation

### Must Resolve (Blockers):

| Gap | Category | Status |
|-----|----------|--------|
| VAD pre-buffer retrieval | Testing | **RESOLVED** - See `answers/vad_prebuffer.md` |
| Queue vs AsyncGenerator decision | Design | **RESOLVED** - See decision below |
| VAD callback signature | Design | **RESOLVED** - See decision below |

---

## Resolved Design Decisions

### Decision 1: VAD Callback Signature

**Decision:** AudioStreamPort callbacks WILL receive audio bytes.

```python
@dataclass
class AudioCallbacks:
    on_speech_start: Optional[Callable[[], None]] = None
    on_speech_end: Optional[Callable[[bytes], None]] = None  # Receives pre-buffer audio
```

**Rationale:** The adapter (VoxStreamAdapter) is responsible for:
1. Registering internal callbacks with VoxStream VAD
2. Calling `vad.get_pre_buffer()` when speech ends
3. Passing the audio bytes to the application callback

This is cleaner for consumers - they get the audio they need without knowing about VAD internals.

### Decision 2: Queue vs AsyncGenerator for Capture

**Decision:** Use AsyncGenerator in the port interface.

```python
async def start_capture(self) -> AsyncGenerator[bytes, None]:
    """Start capturing audio, returns async generator"""
    ...
```

**Rationale:**
- Cleaner interface: `async for chunk in port.start_capture():`
- Hides implementation detail (VoxStream returns Queue)
- Adapter wraps the queue in a generator

**Implementation in adapter:**
```python
async def start_capture(self) -> AsyncGenerator[bytes, None]:
    queue = await self._voxstream.start_capture_stream()
    while self._capturing:
        try:
            chunk = await asyncio.wait_for(queue.get(), timeout=1.0)
            yield chunk
        except asyncio.TimeoutError:
            continue
```

### Should Resolve (Important):

| Gap | Category | How to Resolve |
|-----|----------|----------------|
| Barge-in behavior | Testing | Write test script |
| Device disconnect handling | Testing | Write test script |

### Can Defer (Nice to Have):

| Gap | Category | How to Resolve |
|-----|----------|----------------|
| Echo cancellation | Research | Future enhancement |
| Audio level monitoring | Research | Future enhancement |
| WebRTC/Twilio formats | External | When implementing those adapters |

---

## Next Steps

1. **Write test script** to verify VAD pre-buffer and callback behavior
2. **Make design decisions** on callback signature and return type
3. **Update detailed_desc.md** based on resolved gaps
