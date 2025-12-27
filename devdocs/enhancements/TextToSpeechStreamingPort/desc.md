# TextToSpeechStreamingPort Enhancement

## Overview

The **TextToSpeechStreamingPort** provides a standardized interface for converting text to audio with **real-time streaming capabilities**. Unlike the basic TextToSpeechPort, this port yields audio chunks as they're generated, enabling immediate playback and significantly better user experience for conversational AI applications.

## Use Case

### Primary Use Cases

1. **Real-Time Conversational AI**
   - Start playing audio immediately while generation continues
   - Natural, fluid voice conversations with minimal latency
   - Phone/IVR systems with low-latency requirements
   - Live voice assistants (Alexa-style, Google Assistant-style)

2. **Long-Form Content Delivery**
   - Stream audio for long articles, documents, or stories
   - Podcast-style content generation
   - Audiobook generation with progressive playback
   - News reading applications

3. **WebSocket Voice Chat**
   - Real-time voice chat over WebSocket connections
   - Browser-based voice interfaces
   - Mobile app voice interactions
   - Multiplayer voice communication

4. **Low-Latency Applications**
   - Interactive voice response (IVR) systems
   - Customer service bots with voice
   - Gaming NPCs with voice
   - Real-time translation with audio output

### Example Scenarios

**Scenario 1: Real-Time Voice Assistant**
```python
# WebSocket voice chat
@router.websocket("/ws/voice-chat")
async def voice_chat(websocket: WebSocket):
    await websocket.accept()

    async for message_text in websocket.iter_text():
        # Agent generates response
        response = agent.process_message(message_text)

        # Stream audio chunks immediately
        async for audio_chunk in tts_streaming.synthesize_stream(
            text=response,
            voice_settings=VoiceSettings(voice_id="nova"),
            format="pcm"  # Raw audio for low latency
        ):
            # Send chunk to client as soon as available
            await websocket.send_bytes(audio_chunk)
            # User starts hearing response within ~300ms
```

**Scenario 2: Long Article Reading**
```python
# Convert long article to audio with progressive playback
article_text = fetch_article(article_id)  # 5000 words

# HTTP streaming response
async def generate_audio():
    async for chunk in tts_streaming.synthesize_stream(
        text=article_text,
        voice_settings=VoiceSettings(speed=1.1, voice_id="onyx"),
        format="mp3"
    ):
        yield chunk

# Client can start playing immediately
return StreamingResponse(
    generate_audio(),
    media_type="audio/mpeg",
    headers={
        "Cache-Control": "no-cache",
        "X-Content-Type-Options": "nosniff"
    }
)
```

**Scenario 3: Interactive Phone System**
```python
# IVR system with streaming TTS
async def handle_call(call_session):
    # Get menu options from agent
    menu_text = agent.get_ivr_menu(call_context)

    # Stream audio to caller
    async for audio_chunk in tts_streaming.synthesize_stream(
        text=menu_text,
        voice_settings=VoiceSettings(voice_id="telephony-optimized"),
        format="pcm"  # 8kHz for telephony
    ):
        await call_session.send_audio(audio_chunk)

    # Listen for DTMF input while speaking
    user_choice = await call_session.wait_for_dtmf()
```

**Scenario 4: Multi-Language Real-Time Translation**
```python
# Live translation with voice output
async def translate_and_speak(audio_input_stream):
    # Speech-to-text (user speaking)
    text = await stt.transcribe_stream(audio_input_stream)

    # Translate
    translated = translator.translate(text, target_lang="es")

    # Stream translated audio back
    async for audio_chunk in tts_streaming.synthesize_stream(
        text=translated,
        voice_settings=VoiceSettings(voice_id="es-MX-neural"),
        format="opus"
    ):
        yield audio_chunk
```

**Scenario 5: Agent with Progressive Response**
```python
# Stream audio as agent generates response
async def chat_with_streaming_voice(message: str):
    # Agent streams response token-by-token
    response_buffer = ""

    async for token in agent.stream_response(message):
        response_buffer += token

        # When we have complete sentences, start audio
        if token in ['.', '!', '?']:
            async for audio_chunk in tts_streaming.synthesize_stream(
                text=response_buffer,
                voice_settings=VoiceSettings(voice_id="alloy")
            ):
                yield audio_chunk

            response_buffer = ""  # Clear buffer
```

## Generic Fit

### Hexagonal Architecture Alignment

TextToSpeechStreamingPort follows the same hexagonal architecture pattern as other chatforge ports:

```
┌─────────────────────────────────────────────────────────────┐
│           Core Domain (Streaming Port)                      │
│                                                             │
│  TextToSpeechStreamingPort (ABC)                           │
│  - synthesize_stream(text, voice) -> AsyncIterator[bytes] │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────┴──────┐    ┌──────┴─────┐    ┌───────┴──────┐
│   OpenAI     │    │  ElevenLabs│    │    Google    │
│  Streaming   │    │  Streaming │    │  Streaming   │
│   Adapter    │    │   Adapter  │    │   Adapter    │
│              │    │            │    │              │
│ implements   │    │ implements │    │  implements  │
│synthesize_   │    │synthesize_ │    │ synthesize_  │
│  stream()    │    │  stream()  │    │   stream()   │
└──────────────┘    └────────────┘    └──────────────┘
```

### Integration with Chatforge Components

**1. Agent Streaming Output + TTS Streaming**
```python
# Combine agent streaming with TTS streaming
async def voice_agent_pipeline(message: str):
    # Agent generates response tokens
    full_response = ""
    sentence_buffer = ""

    async for token in agent.stream_tokens(message):
        full_response += token
        sentence_buffer += token

        # Synthesize complete sentences immediately
        if token in ['.', '!', '?', '\n']:
            async for audio in tts_streaming.synthesize_stream(sentence_buffer):
                yield audio

            sentence_buffer = ""
```

**2. FastAPI Streaming Response**
```python
from fastapi.responses import StreamingResponse

@router.post("/chat/voice-stream")
async def chat_voice_stream(
    request: ChatRequest,
    tts: TextToSpeechStreamingPort = Depends(get_tts_streaming)
):
    # Get agent response
    response = agent.process_message(request.message)

    # Stream audio chunks
    async def audio_generator():
        async for chunk in tts.synthesize_stream(
            text=response,
            voice_settings=VoiceSettings(voice_id=request.voice)
        ):
            yield chunk

    return StreamingResponse(
        audio_generator(),
        media_type="audio/mpeg"
    )
```

**3. WebSocket Integration**
```python
class VoiceWebSocketHandler:
    def __init__(
        self,
        agent: ReActAgent,
        tts: TextToSpeechStreamingPort,
        stt: SpeechToTextPort
    ):
        self.agent = agent
        self.tts = tts
        self.stt = stt

    async def handle_connection(self, websocket: WebSocket):
        await websocket.accept()

        try:
            async for audio_bytes in websocket.iter_bytes():
                # Speech-to-text
                text = await self.stt.transcribe(audio_bytes)

                # Agent processing
                response = self.agent.process_message(text)

                # Text-to-speech streaming
                async for audio_chunk in self.tts.synthesize_stream(response):
                    await websocket.send_bytes(audio_chunk)

        except WebSocketDisconnect:
            logger.info("Client disconnected")
```

**4. Middleware Integration (PII Protection)**
```python
# Protect PII before streaming TTS
async def safe_tts_stream(text: str):
    # Redact PII first
    safe_text = pii_detector.redact(text)

    # Stream safe audio
    async for chunk in tts_streaming.synthesize_stream(safe_text):
        yield chunk
```

**5. Observability and Tracing**
```python
class TracedStreamingTTSAdapter(TextToSpeechStreamingPort):
    def __init__(self, inner: TextToSpeechStreamingPort, tracer: Tracer):
        self.inner = inner
        self.tracer = tracer

    async def synthesize_stream(self, text: str, ...) -> AsyncIterator[bytes]:
        with self.tracer.start_span("tts.stream") as span:
            span.set_attribute("text_length", len(text))
            span.set_attribute("voice", voice_settings.voice_id)

            chunk_count = 0
            total_bytes = 0
            start_time = time.time()

            async for chunk in self.inner.synthesize_stream(text, ...):
                chunk_count += 1
                total_bytes += len(chunk)

                # Record time to first chunk (critical metric)
                if chunk_count == 1:
                    ttfb = time.time() - start_time
                    span.set_attribute("time_to_first_byte", ttfb)

                yield chunk

            span.set_attribute("chunk_count", chunk_count)
            span.set_attribute("total_bytes", total_bytes)
            span.set_attribute("duration", time.time() - start_time)
```

### Design Principles

**1. Asynchronous Iterator Pattern**
```python
# Clean, pythonic streaming API
async for audio_chunk in tts.synthesize_stream(text):
    # Process chunk immediately
    await process_chunk(audio_chunk)
```

**2. Backpressure Handling**
```python
# Adapter respects backpressure
class OpenAIStreamingAdapter(TextToSpeechStreamingPort):
    async def synthesize_stream(self, text: str, ...) -> AsyncIterator[bytes]:
        async with self.client.audio.speech.with_streaming_response.create(
            model="tts-1-hd",
            input=text,
            voice=voice_settings.voice_id,
        ) as response:
            # Yields chunks only when consumer is ready
            async for chunk in response.iter_bytes(chunk_size=4096):
                yield chunk  # Backpressure handled automatically
```

**3. Error Handling Mid-Stream**
```python
async def synthesize_stream(self, text: str, ...) -> AsyncIterator[bytes]:
    try:
        async for chunk in provider_stream:
            yield chunk
    except ProviderError as e:
        logger.error(f"TTS streaming error: {e}")
        # Optionally yield error indicator or silence
        yield generate_error_audio("Sorry, audio generation failed")
```

**4. Buffering Strategy**
```python
# Buffer chunks for optimal network transmission
async def buffered_stream(chunk_iterator, buffer_size=8192):
    buffer = bytearray()

    async for chunk in chunk_iterator:
        buffer.extend(chunk)

        # Yield when buffer reaches threshold
        if len(buffer) >= buffer_size:
            yield bytes(buffer)
            buffer.clear()

    # Yield remaining buffered data
    if buffer:
        yield bytes(buffer)
```

## Port Interface Specification

### Core Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Literal

@dataclass
class VoiceSettings:
    """Voice configuration (shared with TextToSpeechPort)."""
    voice_id: str = "default"
    speed: float = 1.0
    pitch: float = 1.0
    stability: float = 0.5

@dataclass
class StreamingMetrics:
    """Metrics for streaming TTS performance."""
    time_to_first_byte: float  # Latency to first audio chunk (ms)
    total_chunks: int
    total_bytes: int
    duration: float  # Total streaming duration (seconds)

class TextToSpeechStreamingPort(ABC):
    """
    Abstract interface for streaming text-to-speech conversion.

    Yields audio chunks as they're generated, enabling real-time playback
    with minimal latency.
    """

    @abstractmethod
    async def synthesize_stream(
        self,
        text: str,
        voice_settings: VoiceSettings | None = None,
        format: Literal["mp3", "opus", "pcm", "aac"] = "mp3",
        chunk_size: int = 4096,
    ) -> AsyncIterator[bytes]:
        """
        Stream audio chunks for the given text.

        Args:
            text: Text content to synthesize
            voice_settings: Voice configuration
            format: Audio format (opus/pcm preferred for low latency)
            chunk_size: Target size for audio chunks in bytes

        Yields:
            Audio chunks as bytes (ready for immediate playback)

        Raises:
            TTSStreamingError: If streaming fails
            ValueError: If text is invalid or too long
        """
        pass

    @abstractmethod
    def get_supported_streaming_formats(self) -> list[str]:
        """Get list of supported streaming audio formats."""
        pass

    @abstractmethod
    def get_estimated_latency(self, text_length: int) -> float:
        """
        Estimate time-to-first-byte in seconds.

        Args:
            text_length: Length of text to synthesize

        Returns:
            Estimated latency in seconds
        """
        pass
```

### Advanced Features

```python
class TextToSpeechStreamingPort(ABC):
    # ... core methods ...

    async def synthesize_stream_with_metrics(
        self,
        text: str,
        voice_settings: VoiceSettings | None = None,
        format: str = "mp3",
    ) -> tuple[AsyncIterator[bytes], StreamingMetrics]:
        """
        Stream audio with performance metrics.

        Returns:
            (audio_iterator, metrics)
        """
        pass

    async def synthesize_stream_with_timestamps(
        self,
        text: str,
        voice_settings: VoiceSettings | None = None,
    ) -> AsyncIterator[tuple[bytes, float]]:
        """
        Stream audio chunks with timing information.

        Yields:
            (audio_chunk, timestamp_offset_seconds)
        """
        pass
```

## Benefits

### User Experience Benefits
- ✅ **Immediate Feedback**: Audio starts within ~300ms instead of waiting for full generation
- ✅ **Natural Conversations**: Fluid voice interactions without awkward pauses
- ✅ **Long Content**: Listen to articles/documents while they generate
- ✅ **Lower Perceived Latency**: Users perceive faster responses

### Technical Benefits
- ✅ **Lower Memory Usage**: Process chunks instead of full audio in memory
- ✅ **Better Resource Utilization**: Generation and playback happen concurrently
- ✅ **Scalability**: Handle more concurrent users with streaming
- ✅ **Network Efficiency**: Start transmitting immediately over HTTP/WebSocket

### Developer Benefits
- ✅ **Consistent API**: Same interface across all streaming TTS providers
- ✅ **Pythonic**: Uses async iterators (natural Python pattern)
- ✅ **Composable**: Easy to add buffering, metrics, error handling
- ✅ **Testable**: Mock with simple async generators

## Performance Characteristics

### Latency Comparison

| Metric | TextToSpeechPort | TextToSpeechStreamingPort |
|--------|-----------------|---------------------------|
| Time to First Audio | 2-5 seconds | 0.3-0.8 seconds |
| Total Generation Time | 2-5 seconds | 2-5 seconds |
| Memory Usage | High (full audio) | Low (chunks) |
| User Perception | Slow | Fast |

### Streaming Format Recommendations

| Format | Latency | Quality | Use Case |
|--------|---------|---------|----------|
| **PCM** | Lowest (50-100ms) | Raw | Real-time conversations, IVR |
| **Opus** | Low (100-200ms) | High | WebRTC, voice chat |
| **MP3** | Medium (200-400ms) | Good | HTTP streaming, mobile apps |
| **AAC** | Medium (200-400ms) | High | iOS apps, HLS streaming |

### Chunk Size Trade-offs

| Chunk Size | Latency | Network Efficiency | Smoothness |
|-----------|---------|-------------------|------------|
| 1KB | Very Low | Poor (overhead) | Can stutter |
| 4KB | Low | Good | Smooth |
| 8KB | Medium | Better | Very smooth |
| 16KB+ | Higher | Best | Very smooth |

**Recommendation**: 4-8KB chunks for optimal balance

## Tradeoffs

### When to Use TextToSpeechStreamingPort

✅ **Ideal for:**
- Real-time conversations (voice assistants, chat bots)
- Long-form content (articles, books, news)
- Low-latency requirements (< 1 second to audio)
- WebSocket/streaming HTTP applications
- Phone/IVR systems
- Progressive audio playback

❌ **Not Needed for:**
- Very short responses (< 50 words) → regular port is fine
- Pre-generated audio files for caching
- Batch offline processing
- Scenarios where latency doesn't matter

### vs. TextToSpeechPort

| Aspect | Streaming Port | Regular Port |
|--------|---------------|--------------|
| **Latency** | Low (~300ms) | High (2-5s) |
| **Memory** | Low (chunks) | High (full audio) |
| **Complexity** | Higher | Lower |
| **Caching** | Harder | Easier |
| **Use Case** | Real-time | Batch/offline |
| **User Experience** | Better | Acceptable for short |

## Implementation Roadmap

### Phase 1: Core Port Definition
- [ ] Define `TextToSpeechStreamingPort` interface
- [ ] Add streaming-specific exceptions
- [ ] Define metrics dataclasses
- [ ] Add comprehensive type hints

### Phase 2: Priority Adapters
- [ ] **OpenAI Streaming Adapter** (tts-1-hd with streaming)
  - Built-in streaming support
  - Good quality, reasonable cost
  - Low latency (~400ms)
- [ ] **ElevenLabs Streaming Adapter**
  - Best quality available
  - Native streaming API
  - Low latency (~300ms)
- [ ] **Google Cloud TTS Streaming**
  - Enterprise-grade reliability
  - Multiple voice options
  - Good latency (~500ms)

### Phase 3: Integration
- [ ] WebSocket voice chat endpoint
- [ ] HTTP streaming response endpoint
- [ ] Agent + TTS streaming pipeline
- [ ] FastAPI dependencies setup

### Phase 4: Advanced Features
- [ ] Buffering middleware
- [ ] Metrics collection
- [ ] Error recovery (retry chunks)
- [ ] Format transcoding (PCM → Opus, etc.)

### Phase 5: Testing
- [ ] Unit tests with mock async iterators
- [ ] Integration tests with real providers (gated)
- [ ] Latency benchmarks
- [ ] Load testing (concurrent streams)

### Phase 6: Optimization
- [ ] Chunk size optimization
- [ ] Connection pooling
- [ ] Adaptive quality (based on network)
- [ ] Caching strategies for repeated text

## Performance Best Practices

### 1. Choose Right Format for Use Case
```python
# Real-time conversation: PCM (lowest latency)
async for chunk in tts.synthesize_stream(text, format="pcm"):
    await websocket.send_bytes(chunk)

# HTTP streaming: MP3 (good compression)
async def stream():
    async for chunk in tts.synthesize_stream(text, format="mp3"):
        yield chunk
return StreamingResponse(stream(), media_type="audio/mpeg")
```

### 2. Buffer Appropriately
```python
# Balance latency vs network overhead
OPTIMAL_CHUNK_SIZE = 4096  # 4KB

async for chunk in tts.synthesize_stream(text, chunk_size=OPTIMAL_CHUNK_SIZE):
    yield chunk
```

### 3. Handle Backpressure
```python
# Don't overwhelm slow consumers
async for chunk in tts.synthesize_stream(text):
    await asyncio.wait_for(
        consumer.send(chunk),
        timeout=5.0  # Prevent infinite blocking
    )
```

### 4. Monitor First-Byte Latency
```python
# Critical UX metric
start = time.time()
first_byte_time = None

async for chunk in tts.synthesize_stream(text):
    if first_byte_time is None:
        first_byte_time = time.time() - start
        logger.info(f"Time to first byte: {first_byte_time:.3f}s")

    yield chunk
```

## Related Enhancements

- **TextToSpeechPort**: Non-streaming variant for simple use cases
- **SpeechToTextStreamingPort**: Reverse operation (audio → text streaming)
- **AudioStreamProcessingPort**: Real-time audio effects on streams
- **VoiceActivityDetectionPort**: Detect speech boundaries in streams
- **AudioMixingPort**: Combine multiple audio streams

## References

### Provider Streaming APIs
- [OpenAI TTS Streaming](https://platform.openai.com/docs/guides/text-to-speech/streaming-real-time-audio)
- [ElevenLabs Streaming API](https://elevenlabs.io/docs/api-reference/streaming)
- [Google Cloud TTS Streaming](https://cloud.google.com/text-to-speech/docs/streaming)
- [Azure TTS WebSocket](https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/how-to-speech-synthesis)

### WebRTC & Streaming Audio
- [WebRTC Audio](https://webrtc.org/getting-started/overview)
- [Opus Codec](https://opus-codec.org/)
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)

### FastAPI Streaming
- [StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [WebSocket](https://fastapi.tiangolo.com/advanced/websockets/)
