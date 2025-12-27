# TextToSpeechPort Enhancement

## Overview

The **TextToSpeechPort** provides a standardized interface for converting text responses into audio files. This port enables voice output capabilities for chatforge applications, making conversational AI accessible through audio channels.

## Use Case

### Primary Use Cases

1. **Accessibility Features**
   - Convert chat responses to audio for visually impaired users
   - Provide audio alternatives for text content
   - Enable hands-free interaction with AI assistants

2. **Pre-Generated Audio Responses**
   - Generate audio files for short, complete messages
   - Create downloadable voice responses
   - Cache frequently used responses as audio files

3. **Batch Audio Generation**
   - Convert multiple text responses to audio offline
   - Generate audio versions of documentation or help content
   - Create audio datasets for testing or training

4. **Simple Voice Applications**
   - Basic voice assistants with short responses
   - Notification systems (email reads, alerts)
   - Educational content delivery

### Example Scenarios

**Scenario 1: Accessible Chat Interface**
```python
# User asks a question via text
user_message = "What's the weather forecast for today?"

# Agent generates response
response = agent.process_message(user_message)
# "Today's forecast shows sunny skies with a high of 75°F..."

# Convert to audio for accessibility
audio_bytes = await tts.synthesize(
    text=response,
    voice_settings=VoiceSettings(voice_id="en-US-neural-female"),
    format="mp3"
)

# Return both text and audio
return {
    "text": response,
    "audio": base64.encode(audio_bytes),
    "audio_url": "/api/audio/response-123.mp3"
}
```

**Scenario 2: Email Summary Bot**
```python
# Generate email summary
summary = agent.summarize_emails(user_emails)

# Convert to audio for commute listening
audio = await tts.synthesize(summary, format="mp3")

# Send audio file to user
send_email_with_attachment(user_email, "Daily Summary.mp3", audio)
```

**Scenario 3: Documentation Audio**
```python
# Generate audio versions of help articles
for article in help_articles:
    content = article.get_text_content()

    audio = await tts.synthesize(
        text=content,
        voice_settings=VoiceSettings(speed=0.9),  # Slower for clarity
        format="wav"
    )

    save_audio(f"audio/help/{article.id}.wav", audio)
```

## Generic Fit

### Hexagonal Architecture Alignment

The TextToSpeechPort follows chatforge's hexagonal architecture pattern, enabling clean separation between:

1. **Core Domain Logic** (Port Interface)
   - Defines WHAT text-to-speech should do
   - Abstract interface independent of any TTS provider
   - Located in `chatforge/ports/tts_port.py`

2. **Infrastructure Adapters** (Implementations)
   - Defines HOW text-to-speech is implemented
   - Provider-specific adapters (OpenAI, Google, Azure, ElevenLabs, local models)
   - Located in `chatforge/adapters/tts/`

```
┌──────────────────────────────────────────────────┐
│           Core Domain (Port)                     │
│                                                  │
│  TextToSpeechPort (ABC)                         │
│  - synthesize(text, voice, format) -> bytes     │
│                                                  │
└──────────────────────────────────────────────────┘
                       ▲
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────┴──────┐ ┌────┴─────┐ ┌─────┴──────┐
│   OpenAI     │ │  Google  │ │ ElevenLabs │
│  TTS Adapter │ │TTS Adapter│ │ TTS Adapter│
│              │ │          │ │            │
│ implements   │ │implements│ │ implements │
│ synthesize() │ │synthesize│ │ synthesize │
└──────────────┘ └──────────┘ └────────────┘
```

### Integration Points

**1. Agent Output Pipeline**
```python
# Agent generates response
agent_response = agent.process_message(user_input)

# Optional: Convert to audio
if user_preferences.audio_enabled:
    audio = await tts.synthesize(agent_response)
    response_data["audio"] = audio

return response_data
```

**2. FastAPI Routes**
```python
from chatforge.ports import TextToSpeechPort

@router.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    tts: TextToSpeechPort = Depends(get_tts_service)
):
    # Process message
    response = agent.process_message(request.message)

    # Add audio if requested
    result = {"text": response}
    if request.include_audio:
        result["audio"] = await tts.synthesize(response)

    return result
```

**3. Dependency Injection**
```python
# Swap providers without changing application code
def create_app(tts_provider: str = "openai"):
    if tts_provider == "openai":
        tts = OpenAITTSAdapter(api_key=config.openai_api_key)
    elif tts_provider == "elevenlabs":
        tts = ElevenLabsTTSAdapter(api_key=config.elevenlabs_api_key)
    elif tts_provider == "local":
        tts = LocalTTSAdapter(model_path="models/tts/")

    return FastAPI(dependencies=[Depends(lambda: tts)])
```

### Design Principles

**1. Provider Agnostic**
- Application code doesn't depend on specific TTS services
- Easy to switch providers (cost, quality, latency tradeoffs)
- Test with mock adapter, deploy with production adapter

**2. Configuration Driven**
```python
# config.py
class TTSConfig(BaseSettings):
    provider: Literal["openai", "google", "azure", "elevenlabs", "local"]
    default_voice: str = "alloy"  # OpenAI voice
    default_format: Literal["mp3", "wav", "pcm"] = "mp3"
    default_speed: float = 1.0

# Factory pattern
def get_tts_adapter(config: TTSConfig) -> TextToSpeechPort:
    if config.provider == "openai":
        return OpenAITTSAdapter(...)
    # ...
```

**3. Composable with Middleware**
```python
# PII protection before TTS
response = agent.process_message(message)
safe_response = pii_detector.redact(response)  # Remove sensitive data
audio = await tts.synthesize(safe_response)
```

**4. Observable and Traceable**
```python
class TracedTTSAdapter(TextToSpeechPort):
    def __init__(self, inner: TextToSpeechPort, tracer: Tracer):
        self.inner = inner
        self.tracer = tracer

    async def synthesize(self, text: str, ...) -> bytes:
        with self.tracer.start_span("tts.synthesize") as span:
            span.set_attribute("text_length", len(text))
            span.set_attribute("voice", voice_settings.voice_id)

            audio = await self.inner.synthesize(text, ...)

            span.set_attribute("audio_size", len(audio))
            return audio
```

## Port Interface Specification

### Core Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

@dataclass
class VoiceSettings:
    """Configuration for voice characteristics."""
    voice_id: str = "default"
    speed: float = 1.0      # 0.25 to 4.0
    pitch: float = 1.0      # Provider-dependent
    stability: float = 0.5  # For providers like ElevenLabs

class TextToSpeechPort(ABC):
    """
    Abstract interface for text-to-speech conversion.

    Converts text into complete audio files. For streaming audio,
    use TextToSpeechStreamingPort instead.
    """

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice_settings: VoiceSettings | None = None,
        format: Literal["mp3", "wav", "pcm", "opus"] = "mp3",
    ) -> bytes:
        """
        Convert text to audio bytes.

        Args:
            text: Text content to synthesize
            voice_settings: Voice configuration (uses default if None)
            format: Audio format for output

        Returns:
            Complete audio file as bytes

        Raises:
            TTSError: If synthesis fails
            ValueError: If text is invalid or too long
        """
        pass

    @abstractmethod
    def get_supported_voices(self) -> list[str]:
        """Get list of available voice IDs."""
        pass

    @abstractmethod
    def get_supported_formats(self) -> list[str]:
        """Get list of supported audio formats."""
        pass
```

## Benefits

### For Users
- ✅ Audio accessibility for all chat responses
- ✅ Hands-free interaction with AI assistants
- ✅ Multi-modal experience (text + audio)

### For Developers
- ✅ Clean abstraction over multiple TTS providers
- ✅ Easy testing with mock adapters
- ✅ Flexible provider switching without code changes
- ✅ Consistent API across different TTS services

### For Applications
- ✅ Voice-enabled chatbots
- ✅ Accessible web applications
- ✅ Audio content generation
- ✅ Multi-channel support (text, voice, both)

## Tradeoffs

### When to Use TextToSpeechPort

✅ **Good for:**
- Short responses (< 500 words)
- Complete messages that don't change
- Downloadable audio files
- Batch audio generation
- Caching responses as audio

❌ **Not Ideal for:**
- Long responses (> 1000 words) → use streaming
- Real-time conversations → use streaming
- Low-latency requirements → use streaming
- Partial response playback → use streaming

### vs. TextToSpeechStreamingPort

| Feature | TextToSpeechPort | StreamingPort |
|---------|-----------------|---------------|
| Latency | Higher (wait for complete audio) | Lower (start playing immediately) |
| Memory | Higher (full audio in memory) | Lower (process chunks) |
| Use Case | Short messages, downloads | Long responses, real-time |
| Complexity | Simpler | More complex |
| Caching | Easy | Harder |

## Implementation Roadmap

### Phase 1: Core Port Definition
- [ ] Define `TextToSpeechPort` interface
- [ ] Define `VoiceSettings` dataclass
- [ ] Define custom exceptions (`TTSError`, etc.)
- [ ] Add type hints and documentation

### Phase 2: Adapter Implementations
- [ ] OpenAI TTS adapter (tts-1, tts-1-hd models)
- [ ] Google Cloud TTS adapter
- [ ] Azure TTS adapter
- [ ] ElevenLabs adapter
- [ ] Local TTS adapter (Piper, Coqui)

### Phase 3: Integration
- [ ] Factory pattern for provider selection
- [ ] Configuration management (pydantic settings)
- [ ] FastAPI route integration
- [ ] Agent output pipeline integration

### Phase 4: Testing
- [ ] Unit tests for port interface
- [ ] Adapter tests with mocked APIs
- [ ] Integration tests with real TTS APIs (gated)
- [ ] Performance benchmarks

### Phase 5: Documentation & Examples
- [ ] API reference documentation
- [ ] Usage examples
- [ ] Provider comparison guide
- [ ] Migration guide

## Related Enhancements

- **TextToSpeechStreamingPort**: Streaming variant for real-time audio
- **SpeechToTextPort**: Reverse operation (audio → text)
- **AudioProcessingPort**: Audio effects and post-processing
- **VoiceActivityDetection**: Detect speech in audio streams

## References

### TTS Provider APIs
- [OpenAI TTS API](https://platform.openai.com/docs/guides/text-to-speech)
- [Google Cloud TTS](https://cloud.google.com/text-to-speech)
- [Azure Cognitive Services TTS](https://azure.microsoft.com/en-us/services/cognitive-services/text-to-speech/)
- [ElevenLabs API](https://elevenlabs.io/docs/api-reference)
- [Piper TTS (Local)](https://github.com/rhasspy/piper)

### Related Standards
- [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)
- [SSML (Speech Synthesis Markup Language)](https://www.w3.org/TR/speech-synthesis/)
