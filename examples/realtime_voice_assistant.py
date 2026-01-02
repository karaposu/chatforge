#!/usr/bin/env python3
"""
Realtime Voice Assistant Example

Demonstrates integration of:
- VoxStreamAdapter (AudioStreamPort) - Local mic/speaker
- OpenAIRealtimeAdapter (RealtimeVoiceAPIPort) - OpenAI Realtime API

Requirements:
    pip install voxstream

Usage:
    export OPENAI_API_KEY=your-key
    python examples/realtime_voice_assistant.py

Press Ctrl+C to stop.
"""

import asyncio
import os
import signal
import sys
from pathlib import Path

# Load .env if present
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

from chatforge.adapters.realtime import OpenAIRealtimeAdapter
from chatforge.adapters.audio import VoxStreamAdapter
from chatforge.ports.realtime_voice import (
    VoiceSessionConfig,
    VoiceEventType,
)
from chatforge.ports.audio_stream import AudioStreamConfig, VADConfig, AudioCallbacks


class VoiceAssistant:
    """
    Full-duplex voice assistant using OpenAI Realtime API.

    Features:
    - Continuous mic capture with VAD
    - Server-side turn detection
    - Barge-in support (interrupt AI while speaking)
    - Real-time audio playback
    """

    def __init__(
        self,
        api_key: str,
        voice: str = "alloy",
        system_prompt: str | None = None,
    ):
        self.api_key = api_key
        self.voice = voice
        self.system_prompt = system_prompt or (
            "You are a helpful voice assistant. "
            "Keep responses concise and conversational. "
            "Respond naturally as if having a spoken conversation."
        )

        self._running = False
        self._is_ai_speaking = False
        self._audio_adapter: VoxStreamAdapter | None = None
        self._realtime_adapter: OpenAIRealtimeAdapter | None = None

    async def start(self):
        """Start the voice assistant."""
        print("Starting voice assistant...")
        print(f"  Voice: {self.voice}")
        print(f"  System prompt: {self.system_prompt[:50]}...")
        print()

        # Audio config - must match OpenAI's expected format
        audio_config = AudioStreamConfig(
            sample_rate=24000,  # OpenAI uses 24kHz
            channels=1,        # Mono
            bit_depth=16,      # PCM16
            chunk_duration_ms=100,  # 100ms chunks
        )

        # VAD config for local speech detection (backup/barge-in)
        vad_config = VADConfig(
            enabled=True,
            energy_threshold=0.02,
            speech_start_ms=100,
            speech_end_ms=300,
        )

        # Session config for OpenAI
        session_config = VoiceSessionConfig(
            voice=self.voice,
            system_prompt=self.system_prompt,
            modalities=["audio", "text"],
            vad_mode="server",  # Let OpenAI detect speech
            vad_silence_ms=500,  # 500ms silence = end of turn
            transcription_enabled=True,
        )

        self._audio_adapter = VoxStreamAdapter(
            config=audio_config,
            vad_config=vad_config,
        )

        self._realtime_adapter = OpenAIRealtimeAdapter(
            api_key=self.api_key,
            auto_reconnect=True,
            max_reconnect_attempts=3,
        )

        self._running = True

        try:
            async with self._audio_adapter as audio:
                async with self._realtime_adapter as realtime:
                    print("Connecting to OpenAI Realtime API...")
                    await realtime.connect(session_config)
                    print("Connected!")
                    print()
                    print("=" * 50)
                    print("Voice assistant ready. Start speaking!")
                    print("Press Ctrl+C to stop.")
                    print("=" * 50)
                    print()

                    # Set up audio callbacks for barge-in
                    audio.set_callbacks(AudioCallbacks(
                        on_speech_start=self._on_local_speech_start,
                        on_playback_complete=self._on_playback_complete,
                    ))

                    # Run capture and playback loops concurrently
                    await asyncio.gather(
                        self._capture_loop(audio, realtime),
                        self._event_loop(audio, realtime),
                    )

        except asyncio.CancelledError:
            print("\nStopping...")
        finally:
            self._running = False
            print("Voice assistant stopped.")

    async def _capture_loop(self, audio: VoxStreamAdapter, realtime: OpenAIRealtimeAdapter):
        """Capture audio from mic and send to OpenAI."""
        try:
            async for chunk in audio.start_capture():
                if not self._running:
                    break

                # Send audio to OpenAI
                await realtime.send_audio(chunk)

        except asyncio.CancelledError:
            pass
        finally:
            await audio.stop_capture()

    async def _event_loop(self, audio: VoxStreamAdapter, realtime: OpenAIRealtimeAdapter):
        """Handle events from OpenAI and play audio."""
        transcript_buffer = ""
        input_transcript_buffer = ""

        try:
            async for event in realtime.events():
                if not self._running:
                    break

                match event.type:
                    # Connection events
                    case VoiceEventType.CONNECTED:
                        if event.metadata.get("reconnected"):
                            print("[Reconnected to OpenAI]")

                    case VoiceEventType.DISCONNECTED:
                        print("[Disconnected]")
                        if self._running:
                            print("[Attempting to reconnect...]")

                    case VoiceEventType.RECONNECTING:
                        attempt = event.metadata.get("attempt", "?")
                        print(f"[Reconnecting... attempt {attempt}]")

                    # Speech detection (server VAD)
                    case VoiceEventType.SPEECH_STARTED:
                        print("\n[You started speaking]")
                        # Barge-in: interrupt AI if it's speaking
                        if self._is_ai_speaking:
                            print("[Interrupting AI...]")
                            await realtime.interrupt()
                            await audio.stop_playback()
                            self._is_ai_speaking = False

                    case VoiceEventType.SPEECH_ENDED:
                        print("[You stopped speaking]")

                    # User's speech transcription
                    case VoiceEventType.INPUT_TRANSCRIPT:
                        input_transcript_buffer = event.data
                        print(f"You: {input_transcript_buffer}")

                    # AI response events
                    case VoiceEventType.RESPONSE_STARTED:
                        self._is_ai_speaking = True
                        transcript_buffer = ""

                    case VoiceEventType.TRANSCRIPT:
                        # Streaming transcript of AI's speech
                        if event.metadata.get("is_delta"):
                            # First chunk - print prefix
                            if not transcript_buffer:
                                print("\nAssistant: ", end="", flush=True)
                            transcript_buffer += event.data
                            print(event.data, end="", flush=True)
                        else:
                            # Final transcript (not delta)
                            if not transcript_buffer:
                                print(f"\nAssistant: {event.data}")

                    case VoiceEventType.AUDIO_CHUNK:
                        # Play audio through speakers
                        await audio.play(event.data)

                    case VoiceEventType.AUDIO_DONE:
                        await audio.end_playback()

                    case VoiceEventType.RESPONSE_DONE:
                        self._is_ai_speaking = False
                        print()  # Newline after transcript

                        # Show usage if available
                        if event.data and event.data.get("usage"):
                            usage = event.data["usage"]
                            tokens = usage.get("total_tokens", "?")
                            print(f"[Tokens: {tokens}]")

                    case VoiceEventType.RESPONSE_CANCELLED:
                        self._is_ai_speaking = False
                        print("\n[Response cancelled]")

                    # Errors
                    case VoiceEventType.ERROR:
                        code = event.data.get("code") if event.data else "unknown"
                        message = event.data.get("message") if event.data else "Unknown error"
                        print(f"\n[Error: {code} - {message}]")

                    # Other events (debug)
                    case _:
                        # Uncomment to see all events:
                        # print(f"[Event: {event.type.value}]")
                        pass

        except asyncio.CancelledError:
            pass

    def _on_local_speech_start(self):
        """Called when local VAD detects speech start."""
        # This is a backup for barge-in if server VAD is slow
        if self._is_ai_speaking and self._realtime_adapter:
            asyncio.create_task(self._handle_barge_in())

    async def _handle_barge_in(self):
        """Handle barge-in interrupt."""
        if self._realtime_adapter and self._audio_adapter:
            await self._realtime_adapter.interrupt()
            await self._audio_adapter.stop_playback()
            self._is_ai_speaking = False

    def _on_playback_complete(self):
        """Called when audio playback finishes."""
        self._is_ai_speaking = False

    def stop(self):
        """Stop the voice assistant."""
        self._running = False


async def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Usage: export OPENAI_API_KEY=your-key")
        sys.exit(1)

    assistant = VoiceAssistant(
        api_key=api_key,
        voice="alloy",  # Options: alloy, echo, fable, onyx, nova, shimmer
        system_prompt=(
            "You are a friendly voice assistant. "
            "Keep your responses brief and natural, as if having a conversation. "
            "Don't use lists or complex formatting - speak naturally."
        ),
    )

    # Handle Ctrl+C gracefully
    loop = asyncio.get_event_loop()

    def signal_handler():
        assistant.stop()

    loop.add_signal_handler(signal.SIGINT, signal_handler)
    loop.add_signal_handler(signal.SIGTERM, signal_handler)

    await assistant.start()


if __name__ == "__main__":
    asyncio.run(main())
