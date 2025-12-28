"""
TTS Adapters

Concrete implementations of the TTSPort interface for various
text-to-speech providers.

Available Adapters:
- ElevenLabsTTSAdapter: High-quality neural voices with cloning support
- OpenAITTSAdapter: OpenAI's TTS with style prompts

Usage:
    from chatforge.adapters.tts import ElevenLabsTTSAdapter, ElevenLabsVoiceConfig

    async with ElevenLabsTTSAdapter() as tts:
        config = ElevenLabsVoiceConfig(voice_id="voice-123")
        result = await tts.synthesize("Hello world", config)

        with open("output.mp3", "wb") as f:
            f.write(result.audio_bytes)

Environment Variables:
    ELEVENLABS_API_KEY: ElevenLabs API key
    OPENAI_API_KEY: OpenAI API key
"""

from chatforge.adapters.tts.elevenlabs import (
    ElevenLabsTTSAdapter,
    ElevenLabsVoiceConfig,
)
from chatforge.adapters.tts.openai import (
    OpenAITTSAdapter,
    OpenAIVoiceConfig,
)

__all__ = [
    "ElevenLabsTTSAdapter",
    "ElevenLabsVoiceConfig",
    "OpenAITTSAdapter",
    "OpenAIVoiceConfig",
]
