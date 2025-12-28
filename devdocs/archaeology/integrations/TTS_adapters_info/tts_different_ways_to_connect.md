# TTS Connection Methods: HTTP REST vs WebSocket vs gRPC

Understanding when to use each connection type for Text-to-Speech.

---

## Connection Types Overview

| Method | Latency | Persistent | Complexity | Best For |
|--------|---------|------------|------------|----------|
| **HTTP REST** | Medium | No | Simple | Standard use cases |
| **HTTP Chunked** | Medium | No | Simple | Streaming playback |
| **WebSocket** | Low | Yes | Complex | Real-time/interactive |
| **gRPC** | Low | Optional | Complex | High-throughput |

---

## HTTP REST (Standard)

**How it works:**
```
Client                          Server
   |---- POST /synthesize ------->|
   |                              | (generates full audio)
   |<----- audio bytes -----------|
```

**Characteristics:**
- One request = one complete audio response
- Connection closes after response
- Simple to implement
- Buffering required before playback

**Providers:**
- ElevenLabs (standard API)
- OpenAI (standard mode)
- Google Cloud TTS
- Azure (REST API)

**When to use:**
- Pre-generating audio files
- Batch processing
- Simple integrations
- When latency isn't critical

**Example:**
```python
async def synthesize_http(text: str) -> bytes:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.elevenlabs.io/v1/text-to-speech/voice_id",
            json={"text": text},
        )
        return response.content  # Full audio
```

---

## HTTP Chunked Streaming

**How it works:**
```
Client                          Server
   |---- POST /synthesize ------->|
   |<----- chunk 1 ---------------|  (start playing)
   |<----- chunk 2 ---------------|
   |<----- chunk 3 ---------------|
   |<----- (connection close) ----|
```

**Characteristics:**
- Still HTTP, but response streams in chunks
- Can start playback before full audio generated
- Lower perceived latency
- Connection still closes after response

**Providers:**
- ElevenLabs (streaming endpoint)
- OpenAI (with `with_streaming_response`)
- Azure (SDK streaming)

**When to use:**
- Real-time playback while generating
- Long-form content (audiobooks)
- Better UX with perceived faster response

**Example:**
```python
async def synthesize_streaming(text: str):
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "https://api.elevenlabs.io/v1/text-to-speech/voice_id/stream",
            json={"text": text},
        ) as response:
            async for chunk in response.aiter_bytes():
                yield chunk  # Play immediately
```

---

## WebSocket

**How it works:**
```
Client                          Server
   |---- WebSocket handshake ---->|
   |<--- connection established --|
   |                              |
   |---- text chunk 1 ----------->|
   |<--- audio chunk 1 -----------|
   |---- text chunk 2 ----------->|
   |<--- audio chunk 2 -----------|
   |                              |
   |---- close ------------------>|
```

**Characteristics:**
- Persistent bidirectional connection
- Lowest latency (no connection overhead per message)
- Can send text incrementally (word by word)
- More complex to implement
- Need connection management (reconnect, heartbeat)

**Providers:**
- ElevenLabs (WebSocket API for ultra-low latency)
- Azure (internal, SDK manages)

**When to use:**
- **Voice assistants** - need instant response
- **Live captioning** - real-time text-to-speech
- **Gaming** - dynamic voice generation
- **Interactive applications** - conversational AI
- When you're sending text incrementally (as LLM generates)

**Example:**
```python
import websockets

class ElevenLabsWebSocketTTS:
    def __init__(self, api_key: str, voice_id: str):
        self.url = f"wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input"
        self.api_key = api_key
        self._ws = None

    async def connect(self):
        self._ws = await websockets.connect(
            self.url,
            extra_headers={"xi-api-key": self.api_key}
        )
        # Send initial config
        await self._ws.send(json.dumps({
            "text": " ",  # Initial space
            "voice_settings": {"stability": 0.5}
        }))

    async def send_text(self, text: str):
        """Send text chunk, receive audio chunk."""
        await self._ws.send(json.dumps({"text": text}))
        response = await self._ws.recv()
        return base64.b64decode(json.loads(response)["audio"])

    async def close(self):
        if self._ws:
            await self._ws.send(json.dumps({"text": ""}))  # Signal end
            await self._ws.close()
```

---

## gRPC

**How it works:**
```
Client                          Server
   |---- gRPC stream open ------->|
   |---- SynthesizeRequest ------>|
   |<--- SynthesizeResponse 1 ----|
   |<--- SynthesizeResponse 2 ----|
   |<--- stream end --------------|
```

**Characteristics:**
- Binary protocol (protobuf) - more efficient
- Built-in streaming support
- Strong typing via proto definitions
- HTTP/2 multiplexing
- More complex setup (proto compilation)

**Providers:**
- Google Cloud TTS (primary method)
- Azure (optional)

**When to use:**
- High-throughput systems
- Already using gRPC infrastructure
- Need efficient binary protocol
- Server-to-server communication

**Example:**
```python
from google.cloud import texttospeech

async def synthesize_grpc(text: str):
    client = texttospeech.TextToSpeechAsyncClient()

    response = await client.synthesize_speech(
        input=texttospeech.SynthesisInput(text=text),
        voice=texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Neural2-A",
        ),
        audio_config=texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        ),
    )
    return response.audio_content
```

---

## Decision Matrix

| Scenario | Recommended | Why |
|----------|-------------|-----|
| Pre-generate audio files | HTTP REST | Simple, no streaming needed |
| Audiobook generation | HTTP Chunked | Stream to file, show progress |
| Voice assistant (Alexa-like) | WebSocket | Ultra-low latency, bidirectional |
| LLM + TTS pipeline | WebSocket | Send text as LLM generates |
| Batch processing 1000 files | HTTP REST | Simple, parallelizable |
| Real-time game dialogue | WebSocket | Instant response needed |
| Notification system | HTTP REST | Short, non-interactive |
| Live translation | WebSocket | Continuous streaming |
| Server-side rendering | gRPC | Efficient, typed |

---

## Latency Comparison

```
Scenario: Synthesize "Hello, how are you today?"

HTTP REST:
  Connection setup:     ~50ms
  Send request:         ~10ms
  Server processing:    ~200ms
  Receive full audio:   ~100ms
  Total to first byte:  ~360ms
  Total to complete:    ~360ms

HTTP Chunked:
  Connection setup:     ~50ms
  Send request:         ~10ms
  First chunk ready:    ~100ms  ← Can start playing
  Total to complete:    ~300ms

WebSocket (persistent):
  Send text:            ~5ms   (already connected)
  First chunk ready:    ~50ms  ← Much faster!
  Total to complete:    ~200ms
```

---

## Chatforge Implications

For Chatforge TTSPort, we currently design for HTTP (REST and chunked streaming):

```python
class TTSPort(ABC):
    async def synthesize(...) -> AudioResult:  # HTTP REST
        pass

    async def stream(...) -> AsyncIterator[bytes]:  # HTTP Chunked
        pass
```

**Future consideration** - WebSocket adapter:

```python
class WebSocketTTSPort(TTSPort):
    """Extended port for WebSocket-based TTS."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish persistent connection."""
        pass

    @abstractmethod
    async def send_incremental(self, text_chunk: str) -> AsyncIterator[bytes]:
        """Send text incrementally, receive audio incrementally."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close persistent connection."""
        pass
```

This would enable LLM streaming → TTS streaming pipeline:

```python
async def speak_as_llm_generates(prompt: str):
    llm = get_llm()
    tts = ElevenLabsWebSocketAdapter(api_key="...")

    await tts.connect()
    try:
        async for text_chunk in llm.stream(prompt):
            async for audio_chunk in tts.send_incremental(text_chunk):
                yield audio_chunk  # Play immediately
    finally:
        await tts.disconnect()
```

---

## Summary

| For v1 (now) | For v2 (future) |
|--------------|-----------------|
| HTTP REST via `synthesize()` | WebSocket adapter |
| HTTP Chunked via `stream()` | Incremental text → audio |
| Simple lifecycle (`close()`) | Full connection management |
| Covers 90% of use cases | Real-time/interactive use cases |

The current TTSPort design handles HTTP well. WebSocket support would be an extension for real-time applications like voice assistants or LLM+TTS pipelines.
