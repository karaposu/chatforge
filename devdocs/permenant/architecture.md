# Chatforge Architecture: Layered Abstraction for AI Applications

Chatforge provides a **layered abstraction system** that goes beyond traditional hexagonal architecture. Instead of forcing developers into a single abstraction level, it offers three dimensions of control for building AI-powered applications.

## The Three Layers

```
┌─────────────────────────────────────────────────────────────┐
│                       SERVICES                              │
│                  (Batteries-included)                       │
│                                                             │
│   from chatforge.services import TTSService                 │
│                                                             │
│   async with TTSService("openai") as tts:                   │
│       result = await tts.generate("Hello!")                 │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                         PORTS                               │
│                  (Unified contracts)                        │
│                                                             │
│   from chatforge.ports import TTSPort, VoiceConfig          │
│                                                             │
│   async def speak(tts: TTSPort, text: str):                 │
│       config = VoiceConfig(voice_id="nova")                 │
│       return await tts.synthesize(text, config)             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                       ADAPTERS                              │
│                  (Provider-specific)                        │
│                                                             │
│   from chatforge.adapters.tts import ElevenLabsTTSAdapter   │
│   from chatforge.adapters.tts import ElevenLabsVoiceConfig  │
│                                                             │
│   config = ElevenLabsVoiceConfig(                           │
│       voice_id="rachel",                                    │
│       stability=0.7,                                        │
│       similarity_boost=0.8,                                 │
│   )                                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Why Three Layers?

### Services: For Rapid Development

**When to use:** You want things to just work.

```python
from chatforge.services import TTSService

# That's it. One import, done.
async with TTSService() as tts:
    audio = await tts.generate("Welcome to our app!")
```

Services are perfect for:
- Prototyping and MVPs
- Standard use cases with sensible defaults
- Teams who want to focus on product, not infrastructure
- Applications where provider-specific features aren't critical

The service handles provider selection, configuration, error handling, and resource management. You focus on your application logic.

### Ports: For Flexibility and Testing

**When to use:** You need provider-agnostic code or easy testing.

```python
from chatforge.ports import TTSPort, VoiceConfig, AudioQuality

class NotificationService:
    def __init__(self, tts: TTSPort):  # Inject any TTS provider
        self.tts = tts

    async def send_audio_notification(self, message: str) -> bytes:
        config = VoiceConfig(voice_id="default")
        result = await self.tts.synthesize(
            message,
            config,
            quality=AudioQuality.STANDARD
        )
        return result.audio_bytes
```

Ports are perfect for:
- Writing testable code (inject mocks easily)
- Building libraries that shouldn't lock users to a provider
- Switching providers without changing business logic
- Teams practicing dependency injection and clean architecture

The port defines **what** you can do. The adapter defines **how** it's done.

### Adapters: For Full Control

**When to use:** You need provider-specific features or maximum control.

```python
from chatforge.adapters.tts import ElevenLabsTTSAdapter, ElevenLabsVoiceConfig

async with ElevenLabsTTSAdapter() as tts:
    # Access ElevenLabs-specific features
    config = ElevenLabsVoiceConfig(
        voice_id="21m00Tcm4TlvDq8ikWAM",
        stability=0.5,              # ElevenLabs-specific
        similarity_boost=0.75,      # ElevenLabs-specific
        style_exaggeration=0.3,     # ElevenLabs-specific
    )

    result = await tts.synthesize(
        text="Hello with fine-tuned voice settings!",
        config=config,
        model="eleven_multilingual_v2",  # Specific model
    )
```

Adapters are perfect for:
- Accessing provider-specific features (voice cloning, custom models)
- Performance optimization for a specific provider
- Building custom adapters for unsupported providers
- Applications deeply integrated with one provider's ecosystem

## The Three Dimensions

Chatforge's architecture enables control across three dimensions:

### 1. Abstraction Level

Choose your layer based on needs:

| Need | Layer | Example |
|------|-------|---------|
| "Just make it talk" | Service | `TTSService().generate("Hi")` |
| "I want to swap providers" | Port | `tts: TTSPort` in function signature |
| "I need voice cloning" | Adapter | `ElevenLabsVoiceConfig(clone_id=...)` |

### 2. Provider Choice

Swap implementations without architectural changes:

```python
# Same code, different providers
async with TTSService("openai") as tts:
    await tts.generate("Hello from OpenAI")

async with TTSService("elevenlabs") as tts:
    await tts.generate("Hello from ElevenLabs")

# Future: add more providers without changing app code
async with TTSService("azure") as tts:
    await tts.generate("Hello from Azure")
```

### 3. Composition

Combine capabilities to build complex AI applications:

```python
from chatforge.services import TTSService
from chatforge.services.vision import ImageAnalyzer
from chatforge.services.llm import get_chat_llm

class VoiceAssistant:
    """Combines LLM, Vision, and TTS capabilities."""

    def __init__(self):
        self.llm = get_chat_llm()
        self.vision = ImageAnalyzer(llm=self.llm)
        self.tts_provider = "openai"

    async def describe_and_speak(self, image_path: str) -> bytes:
        # Analyze image with vision
        analysis = await self.vision.analyze_image(image_path)

        # Generate audio description
        async with TTSService(self.tts_provider) as tts:
            audio = await tts.generate(analysis.text)

        return audio.audio_bytes
```

## Practical Examples

### Example 1: Quick Prototype

You're building a demo and need TTS working in 5 minutes:

```python
from chatforge.services import TTSService

async def main():
    async with TTSService() as tts:
        result = await tts.generate("Demo is ready!")
        with open("demo.mp3", "wb") as f:
            f.write(result.audio_bytes)
```

### Example 2: Multi-Provider Application

You want to offer users a choice of TTS providers:

```python
from chatforge.services import TTSService

async def generate_speech(text: str, provider: str = "openai") -> bytes:
    async with TTSService(provider) as tts:
        result = await tts.generate(text)
        return result.audio_bytes

# User settings determine provider
audio = await generate_speech("Hello!", user.preferred_tts_provider)
```

### Example 3: Testable Business Logic

You're building a production system with proper testing:

```python
from chatforge.ports import TTSPort, VoiceConfig

class AnnouncementService:
    def __init__(self, tts: TTSPort):
        self.tts = tts

    async def create_announcement(self, message: str) -> bytes:
        config = VoiceConfig(voice_id="announcer")
        result = await self.tts.synthesize(message, config)
        return result.audio_bytes

# In tests: inject a mock
class MockTTS(TTSPort):
    async def synthesize(self, text, config, **kwargs):
        return AudioResult(audio_bytes=b"fake", ...)

service = AnnouncementService(tts=MockTTS())
```

### Example 4: Provider-Specific Features

You need ElevenLabs voice cloning for a specific use case:

```python
from chatforge.adapters.tts import ElevenLabsTTSAdapter, ElevenLabsVoiceConfig

async def clone_voice_demo(clone_voice_id: str, text: str):
    async with ElevenLabsTTSAdapter() as tts:
        config = ElevenLabsVoiceConfig(
            voice_id=clone_voice_id,
            stability=0.3,           # Lower for more expressiveness
            similarity_boost=0.9,    # Higher for voice matching
        )
        result = await tts.synthesize(text, config)
        return result.audio_bytes
```

## Building New Adapters

The layered architecture makes it easy to add new providers:

```python
from chatforge.ports import TTSPort, VoiceConfig, AudioResult

class AzureTTSAdapter(TTSPort):
    """Azure Cognitive Services TTS adapter."""

    async def synthesize(
        self,
        text: str,
        config: VoiceConfig,
        **kwargs
    ) -> AudioResult:
        # Implement Azure-specific logic
        azure_client = self._get_client()
        audio = await azure_client.synthesize(text, voice=config.voice_id)

        return AudioResult(
            audio_bytes=audio,
            format=AudioFormat.MP3,
            ...
        )
```

Your new adapter automatically works with:
- Any code written against `TTSPort`
- The `TTSService` (after registration)
- Existing composition patterns

## Summary

| Layer | Import From | Use When |
|-------|-------------|----------|
| **Services** | `chatforge.services` | Rapid development, standard use cases |
| **Ports** | `chatforge.ports` | Testing, provider-agnostic code, clean architecture |
| **Adapters** | `chatforge.adapters` | Provider-specific features, full control |

The power of this architecture is **choice**. Start with services for speed, drop to ports for flexibility, use adapters for control. Mix and match as your application evolves.

```python
# Start simple
from chatforge.services import TTSService

# Grow into clean architecture
from chatforge.ports import TTSPort

# Access advanced features when needed
from chatforge.adapters.tts import ElevenLabsTTSAdapter
```

Your code, your choice, your level of abstraction.
