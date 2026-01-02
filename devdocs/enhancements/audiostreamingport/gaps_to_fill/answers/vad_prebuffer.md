# VAD Pre-buffer Behavior: Resolved

**Date:** 2025-01-01
**Source:** VoxStream `voice/vad.py` source code inspection
**Status:** RESOLVED

---

## Questions Answered

### 1. How does VAD pre-buffer work?

**Answer:** The pre-buffer is a deque that stores recent audio chunks.

From `voice/vad.py:113-115`:
```python
self.pre_buffer = collections.deque(maxlen=max(1, int(self.config.pre_buffer_ms / 20)))  # Assuming 20ms chunks
self.pre_buffer_bytes = bytearray()
self.max_prebuffer_size = int(self.audio_config.sample_rate * self.config.pre_buffer_ms / 1000 * 2)  # 16-bit samples
```

- Uses a **fixed-size deque** (FIFO)
- Maxlen based on `pre_buffer_ms / 20` (assumes 20ms chunks)
- For 300ms pre-buffer with 20ms chunks: maxlen = 15 chunks

---

### 2. How to retrieve pre-buffered audio?

**Answer:** Call `get_pre_buffer()` method on the VADetector instance.

From `voice/vad.py:138-146`:
```python
def get_pre_buffer(self) -> Optional[AudioBytes]:
    """Get the pre-buffer containing recent audio before speech detection"""
    if self.config.pre_buffer_ms <= 0:
        return None

    # Return concatenated prebuffer
    if self.pre_buffer:
        return bytes(b''.join(self.pre_buffer))
    return None
```

**Key behavior:**
- Returns `Optional[bytes]` (None if disabled or empty)
- Concatenates all buffered chunks into single bytes object
- Returns a **COPY** - does NOT clear the buffer

---

### 3. When is audio added to pre-buffer?

**Answer:** Every chunk is added during `process_chunk()` before VAD processing.

From `voice/vad.py:175-176`:
```python
if self.config.pre_buffer_ms > 0:
    self.pre_buffer.append(audio_chunk)
```

Audio is always buffered (when enabled), not just during silence. The deque's maxlen naturally evicts old chunks.

---

### 4. Does get_pre_buffer() clear the buffer?

**Answer:** **NO** - it returns a copy.

The buffer is only cleared in `reset()`:
```python
# voice/vad.py:284-285
if hasattr(self, 'pre_buffer'):
    self.pre_buffer.clear()
```

---

### 5. How does on_speech_end callback access pre-buffer?

**Answer:** The callback receives NO arguments. To get pre-buffer audio:

**Option A: Closure with VAD reference**
```python
vad_ref = None

def on_speech_end():
    if vad_ref:
        pre_buffer = vad_ref.get_pre_buffer()
        # Use pre_buffer bytes...

vad = VADetector(config=config, on_speech_end=on_speech_end)
vad_ref = vad  # Capture reference
```

**Option B: Class method with self.vad**
```python
class AudioProcessor:
    def __init__(self):
        self.vad = VADetector(
            config=config,
            on_speech_end=self._on_speech_end
        )

    def _on_speech_end(self):
        pre_buffer = self.vad.get_pre_buffer()
        # Use pre_buffer bytes...
```

---

## Design Implications for AudioStreamPort

### Adapter Implementation

The VoxStreamAdapter needs to:
1. Hold reference to VADetector instance
2. In on_speech_end callback, call `vad.get_pre_buffer()` to get audio
3. Pass the pre-buffer audio to the application callback

```python
class VoxStreamAdapter(AudioStreamPort):
    def __init__(self):
        self._vad: Optional[VADetector] = None
        self._speech_callback: Optional[Callable[[bytes], None]] = None

    def _on_speech_end(self):
        """Internal callback that retrieves pre-buffer"""
        if self._vad and self._speech_callback:
            pre_buffer = self._vad.get_pre_buffer()
            if pre_buffer:
                self._speech_callback(pre_buffer)

    def set_callbacks(self, callbacks: AudioCallbacks):
        self._speech_callback = callbacks.on_speech_end
```

### Design Decision Made

**Decision:** Option B from `help_needed_gap_list.md` - Adapter wraps and provides pre-buffer audio

The adapter is responsible for:
1. Registering internal callbacks with VoxStream VAD
2. Calling `get_pre_buffer()` when speech ends
3. Passing the audio bytes to the application callback

This keeps the port interface clean (`on_speech_end(audio: bytes)`) while handling VoxStream's implementation details in the adapter.

---

## Summary

| Question | Answer |
|----------|--------|
| Pre-buffer storage | `collections.deque` with maxlen |
| How to retrieve | `vad.get_pre_buffer()` returns `Optional[bytes]` |
| When audio added | Every `process_chunk()` call |
| Clears on retrieve? | No, returns copy |
| Callback has audio? | No, need VAD reference to call `get_pre_buffer()` |

**Blocker Resolved:** VAD pre-buffer behavior is now understood. The adapter design is clear.
