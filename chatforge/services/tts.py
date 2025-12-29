"""
TTS Service - Text-to-Speech service with provider abstraction.

This service provides a simple, unified interface for text-to-speech
that hides the complexity of different TTS providers.

Features:
- Multiple TTS providers (ElevenLabs, OpenAI)
- Simple API with sensible defaults
- Streaming support
- Provider-agnostic configuration

Usage:
    from chatforge.services import TTSService

    # Simple usage with defaults
    async with TTSService() as tts:
        result = await tts.generate("Hello world!")
        with open("output.mp3", "wb") as f:
            f.write(result.audio_bytes)

    # With specific provider and voice
    async with TTSService(provider="elevenlabs") as tts:
        result = await tts.generate(
            "Hello world!",
            voice_id="21m00Tcm4TlvDq8ikWAM",
            quality="high",
        )

    # Streaming
    async with TTSService() as tts:
        async for chunk in tts.stream("Long text here..."):
            audio_buffer.write(chunk)
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, AsyncIterator, Literal

from chatforge.ports.tts import (
    AudioFormat,
    AudioQuality,
    AudioResult,
    TTSPort,
    VoiceConfig,
)

if TYPE_CHECKING:
    pass


logger = logging.getLogger(__name__)


# Provider type
ProviderType = Literal["elevenlabs", "openai"]

# Quality type for simpler API
QualityType = Literal["low", "standard", "high"]

# Default voices per provider
DEFAULT_VOICES: dict[ProviderType, str] = {
    "elevenlabs": "21m00Tcm4TlvDq8ikWAM",  # Rachel
    "openai": "nova",
}

# Quality mapping
QUALITY_MAP: dict[QualityType, AudioQuality] = {
    "low": AudioQuality.LOW,
    "standard": AudioQuality.STANDARD,
    "high": AudioQuality.HIGH,
}


class TTSService:
    """
    High-level TTS service with provider abstraction.

    This service provides a simple API for text-to-speech that works
    with any supported provider. Just change the provider string to
    switch implementations.

    Example:
        # OpenAI (default)
        async with TTSService() as tts:
            result = await tts.generate("Hello!")

        # ElevenLabs
        async with TTSService("elevenlabs") as tts:
            result = await tts.generate("Hello!")

        # With options
        async with TTSService("openai") as tts:
            result = await tts.generate(
                "Hello!",
                voice_id="alloy",
                quality="high",
                output_format="mp3",
            )
    """

    def __init__(
        self,
        provider: ProviderType = "openai",
        api_key: str | None = None,
    ):
        """
        Initialize the TTS service.

        Args:
            provider: TTS provider ("openai" or "elevenlabs")
            api_key: Optional API key (uses env var if not provided)
        """
        self.provider = provider
        self.api_key = api_key
        self._adapter: TTSPort | None = None

        logger.debug(f"TTSService initialized with provider={provider}")

    async def __aenter__(self) -> "TTSService":
        """Enter async context and initialize adapter."""
        self._adapter = self._create_adapter()
        await self._adapter.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context and cleanup adapter."""
        if self._adapter:
            await self._adapter.__aexit__(exc_type, exc_val, exc_tb)
            self._adapter = None

    def _create_adapter(self) -> TTSPort:
        """Create the appropriate adapter based on provider."""
        if self.provider == "elevenlabs":
            from chatforge.adapters.tts import ElevenLabsTTSAdapter

            return ElevenLabsTTSAdapter(
                api_key=self.api_key or os.getenv("ELEVENLABS_API_KEY")
            )
        else:
            from chatforge.adapters.tts import OpenAITTSAdapter

            return OpenAITTSAdapter(
                api_key=self.api_key or os.getenv("OPENAI_API_KEY")
            )

    def _ensure_adapter(self) -> TTSPort:
        """Ensure adapter is initialized."""
        if self._adapter is None:
            raise RuntimeError(
                "TTSService must be used as async context manager: "
                "async with TTSService() as tts: ..."
            )
        return self._adapter

    async def generate(
        self,
        text: str,
        *,
        voice_id: str | None = None,
        quality: QualityType = "standard",
        output_format: Literal["mp3", "wav", "ogg", "pcm"] = "mp3",
        model: str | None = None,
    ) -> AudioResult:
        """
        Generate speech from text.

        Args:
            text: Text to synthesize
            voice_id: Voice ID (uses provider default if not specified)
            quality: Audio quality ("low", "standard", "high")
            output_format: Output format ("mp3", "wav", "ogg", "pcm")
            model: Optional model override

        Returns:
            AudioResult with audio bytes and metadata

        Example:
            result = await tts.generate("Hello world!")
            print(f"Generated {len(result.audio_bytes)} bytes")
        """
        adapter = self._ensure_adapter()

        # Use default voice if not specified
        voice = voice_id or DEFAULT_VOICES[self.provider]
        config = VoiceConfig(voice_id=voice)

        # Map quality and format
        audio_quality = QUALITY_MAP[quality]
        audio_format = self._map_format(output_format)

        logger.info(
            f"Generating TTS: provider={self.provider}, voice={voice}, "
            f"quality={quality}, format={output_format}, chars={len(text)}"
        )

        result = await adapter.synthesize(
            text=text,
            config=config,
            output_format=audio_format,
            quality=audio_quality,
            model=model,
        )

        logger.info(f"TTS complete: {len(result.audio_bytes)} bytes")
        return result

    async def stream(
        self,
        text: str,
        *,
        voice_id: str | None = None,
        quality: QualityType = "standard",
        output_format: Literal["mp3", "wav", "ogg", "pcm"] = "mp3",
        model: str | None = None,
    ) -> AsyncIterator[bytes]:
        """
        Stream speech generation.

        Args:
            text: Text to synthesize
            voice_id: Voice ID (uses provider default if not specified)
            quality: Audio quality ("low", "standard", "high")
            output_format: Output format ("mp3", "wav", "ogg", "pcm")
            model: Optional model override

        Yields:
            Audio data chunks as bytes

        Example:
            async for chunk in tts.stream("Hello world!"):
                audio_buffer.write(chunk)
        """
        adapter = self._ensure_adapter()

        voice = voice_id or DEFAULT_VOICES[self.provider]
        config = VoiceConfig(voice_id=voice)
        audio_quality = QUALITY_MAP[quality]
        audio_format = self._map_format(output_format)

        logger.info(
            f"Streaming TTS: provider={self.provider}, voice={voice}, "
            f"chars={len(text)}"
        )

        async for chunk in adapter.stream(
            text=text,
            config=config,
            output_format=audio_format,
            quality=audio_quality,
            model=model,
        ):
            yield chunk

    async def list_voices(self) -> list[dict]:
        """
        List available voices for the current provider.

        Returns:
            List of voice info dicts with 'id', 'name', 'description'

        Example:
            voices = await tts.list_voices()
            for v in voices:
                print(f"{v['name']} ({v['id']})")
        """
        adapter = self._ensure_adapter()

        voices = await adapter.list_voices()

        return [
            {
                "id": v.voice_id,
                "name": v.name,
                "description": v.description,
                "language": v.language,
                "gender": v.gender,
            }
            for v in voices
        ]

    @staticmethod
    def _map_format(format_str: str) -> AudioFormat:
        """Map string format to AudioFormat enum."""
        format_map = {
            "mp3": AudioFormat.MP3,
            "wav": AudioFormat.WAV,
            "ogg": AudioFormat.OGG_OPUS,
            "pcm": AudioFormat.PCM,
        }
        return format_map.get(format_str, AudioFormat.MP3)

    @property
    def default_voice(self) -> str:
        """Get the default voice for the current provider."""
        return DEFAULT_VOICES[self.provider]
