# Chatforge + VoxStream: High-Level Architecture

*Multi-platform voice AI with swappable audio backends.*

**Note**: This document covers `AudioStreamPort` for real-time streaming audio.
For batch/file-based audio operations, see `chatforge_audioport.md`.

---

## The Goal

Build a voice AI application that runs on:
- **Desktop/CLI** (Python native)
- **Web Browser** (React/Vue app)
- **Phone Calls** (Twilio/telephony)

With the **same core logic** for all platforms.

---

## The Problem

Each platform handles audio differently:

| Platform | Audio Source | Audio Destination | Format |
|----------|--------------|-------------------|--------|
| Desktop | Microphone via sounddevice | Speakers via sounddevice | PCM16 24kHz |
| Web | Browser MediaStream API | Browser Web Audio API | Float32 48kHz |
| Phone | Twilio Media Streams | Twilio Media Streams | μ-law 8kHz |

Without abstraction, you'd write three different apps.

---

## The Solution: AudioStreamPort Abstraction

```
┌─────────────────────────────────────────────────────────────────┐
│                      YOUR VOICE APP                              │
│                                                                  │
│   "I don't care WHERE audio comes from or goes to.              │
│    I just process voice conversations."                          │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    VoiceAgent                            │   │
│   │                                                          │   │
│   │  - Receives audio chunks                                 │   │
│   │  - Detects speech (VAD)                                  │   │
│   │  - Sends to AI                                           │   │
│   │  - Plays responses                                       │   │
│   │  - Handles barge-in                                      │   │
│   └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              │ Uses interfaces, not concrete     │
│                              │ implementations                   │
│                              ▼                                   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    AudioStreamPort                             │   │
│   │                    (Interface)                           │   │
│   │                                                          │   │
│   │  async start_capture() -> AsyncGenerator[bytes]          │   │
│   │  async play_audio(chunk: bytes) -> None                  │   │
│   │  async stop_playback() -> None                           │   │
│   │  set_vad_callback(on_speech_start, on_speech_end)        │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                               │
                               │ Implemented by
                               ▼
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│   VoxStream   │      │    WebRTC     │      │    Twilio     │
│   Adapter     │      │    Adapter    │      │    Adapter    │
│               │      │               │      │               │
│  ┌─────────┐  │      │  ┌─────────┐  │      │  ┌─────────┐  │
│  │VoxStream│  │      │  │WebSocket│  │      │  │ Twilio  │  │
│  │ Library │  │      │  │  Relay  │  │      │  │  Media  │  │
│  └─────────┘  │      │  └─────────┘  │      │  │ Streams │  │
│       │       │      │       │       │      │  └─────────┘  │
│       ▼       │      │       ▼       │      │       │       │
│  sounddevice  │      │   Browser     │      │   Phone       │
│  (PortAudio)  │      │   (JS APIs)   │      │   Network     │
└───────────────┘      └───────────────┘      └───────────────┘
        │                      │                      │
        ▼                      ▼                      ▼
   Microphone             User's               Phone Call
   & Speakers             Browser              (PSTN/SIP)
```

---

## How It Works

### 1. Define the AudioStreamPort Interface

```python
# chatforge/ports/audio_stream.py

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Callable

class AudioStreamPort(ABC):
    """
    Abstract interface for audio I/O.

    Implementations handle platform-specific details.
    The VoiceAgent only sees this interface.
    """

    @abstractmethod
    async def start_capture(self) -> AsyncGenerator[bytes, None]:
        """
        Start capturing audio.

        Yields:
            Audio chunks as bytes (PCM16, 24kHz, mono).
            Implementations convert from native format.
        """
        ...

    @abstractmethod
    async def stop_capture(self) -> None:
        """Stop audio capture."""
        ...

    @abstractmethod
    async def play_audio(self, chunk: bytes) -> None:
        """
        Play audio chunk.

        Args:
            chunk: Audio as bytes (PCM16, 24kHz, mono).
            Implementations convert to native format.
        """
        ...

    @abstractmethod
    async def stop_playback(self) -> None:
        """Stop current playback immediately (for barge-in)."""
        ...

    @abstractmethod
    def set_vad_callbacks(
        self,
        on_speech_start: Callable[[], None],
        on_speech_end: Callable[[], None],
    ) -> None:
        """Register voice activity detection callbacks."""
        ...

    @abstractmethod
    def get_audio_level(self) -> float:
        """Get current input audio level (0.0 to 1.0)."""
        ...
```

---

### 2. Implement Platform-Specific Adapters

#### VoxStream Adapter (Desktop/CLI)

```python
# chatforge/adapters/audio/voxstream_adapter.py

from voxstream import VoxStream
from voxstream.config.types import ProcessingMode
from chatforge.ports.audio_stream import AudioStreamPort

class VoxStreamAudioAdapter(AudioStreamPort):
    """
    AudioStreamPort implementation for desktop applications.

    Uses VoxStream for direct microphone/speaker access
    via sounddevice (PortAudio).
    """

    def __init__(self, sample_rate: int = 24000):
        self.voxstream = VoxStream(
            mode=ProcessingMode.REALTIME,
            sample_rate=sample_rate,
        )

    async def start_capture(self) -> AsyncGenerator[bytes, None]:
        async for chunk in self.voxstream.capture_stream():
            yield chunk

    async def stop_capture(self) -> None:
        await self.voxstream.stop_capture()

    async def play_audio(self, chunk: bytes) -> None:
        self.voxstream.play_audio(chunk)

    async def stop_playback(self) -> None:
        self.voxstream.interrupt_playback()

    def set_vad_callbacks(self, on_speech_start, on_speech_end):
        self.voxstream.set_vad_callbacks(
            on_speech_start=on_speech_start,
            on_speech_end=on_speech_end,
        )

    def get_audio_level(self) -> float:
        return self.voxstream.get_input_level()
```

#### WebRTC Adapter (Web Browser)

```python
# chatforge/adapters/audio/webrtc_adapter.py

from chatforge.ports.audio_stream import AudioStreamPort

class WebRTCAudioAdapter(AudioStreamPort):
    """
    AudioStreamPort implementation for web browsers.

    Browser captures audio via MediaStream API and sends
    to server via WebSocket. Server relays to this adapter.

    Audio flow:
    Browser Mic → WebSocket → Server → This Adapter → VoiceAgent
    VoiceAgent → This Adapter → WebSocket → Browser → Speakers
    """

    def __init__(self, websocket, sample_rate: int = 24000):
        self.ws = websocket
        self.sample_rate = sample_rate
        self._speech_start_callback = None
        self._speech_end_callback = None

    async def start_capture(self) -> AsyncGenerator[bytes, None]:
        async for message in self.ws:
            if message["type"] == "audio":
                # Browser sends base64-encoded PCM16
                audio = base64.b64decode(message["data"])
                yield audio
            elif message["type"] == "vad":
                # Browser can do VAD too
                if message["state"] == "speech_start":
                    if self._speech_start_callback:
                        self._speech_start_callback()
                elif message["state"] == "speech_end":
                    if self._speech_end_callback:
                        self._speech_end_callback()

    async def stop_capture(self) -> None:
        await self.ws.send_json({"type": "stop_capture"})

    async def play_audio(self, chunk: bytes) -> None:
        await self.ws.send_bytes(chunk)

    async def stop_playback(self) -> None:
        await self.ws.send_json({"type": "stop_playback"})

    def set_vad_callbacks(self, on_speech_start, on_speech_end):
        self._speech_start_callback = on_speech_start
        self._speech_end_callback = on_speech_end

    def get_audio_level(self) -> float:
        # Browser tracks this, we'd need to poll
        return 0.0
```

#### Twilio Adapter (Phone Calls)

```python
# chatforge/adapters/audio/twilio_adapter.py

from chatforge.ports.audio_stream import AudioStreamPort

class TwilioAudioAdapter(AudioStreamPort):
    """
    AudioStreamPort implementation for phone calls via Twilio.

    Twilio Media Streams send μ-law 8kHz audio.
    We convert to/from PCM16 24kHz for the VoiceAgent.

    Audio flow:
    Phone → Twilio → Media Stream WebSocket → This Adapter
    This Adapter → Media Stream WebSocket → Twilio → Phone
    """

    def __init__(self, media_stream_ws):
        self.ws = media_stream_ws
        self.stream_sid = None

    async def start_capture(self) -> AsyncGenerator[bytes, None]:
        async for message in self.ws:
            data = json.loads(message)

            if data["event"] == "start":
                self.stream_sid = data["start"]["streamSid"]

            elif data["event"] == "media":
                # Twilio sends base64 μ-law audio
                mulaw = base64.b64decode(data["media"]["payload"])
                pcm16 = self._mulaw_to_pcm16(mulaw)
                pcm16_resampled = self._resample_8k_to_24k(pcm16)
                yield pcm16_resampled

    async def play_audio(self, chunk: bytes) -> None:
        # Convert 24kHz PCM16 to 8kHz μ-law for Twilio
        pcm16_8k = self._resample_24k_to_8k(chunk)
        mulaw = self._pcm16_to_mulaw(pcm16_8k)

        await self.ws.send_json({
            "event": "media",
            "streamSid": self.stream_sid,
            "media": {
                "payload": base64.b64encode(mulaw).decode()
            }
        })

    async def stop_playback(self) -> None:
        await self.ws.send_json({
            "event": "clear",
            "streamSid": self.stream_sid,
        })

    def _mulaw_to_pcm16(self, mulaw: bytes) -> bytes:
        # μ-law to PCM16 conversion
        ...

    def _pcm16_to_mulaw(self, pcm16: bytes) -> bytes:
        # PCM16 to μ-law conversion
        ...
```

---

### 3. Write Platform-Agnostic Voice Logic

```python
# chatforge/agent/voice_agent.py

class VoiceAgent:
    """
    Voice conversation agent.

    Uses AudioStreamPort for audio I/O - doesn't know or care
    whether audio comes from microphone, browser, or phone.
    """

    def __init__(
        self,
        audio: AudioStreamPort,          # Any audio backend
        realtime: RealtimeVoiceAPIPort,    # AI API connection
        tools: list = None,
    ):
        self.audio = audio
        self.realtime = realtime
        self.tools = tools or []

        # Wire up VAD
        self.audio.set_vad_callbacks(
            on_speech_start=self._handle_speech_start,
            on_speech_end=self._handle_speech_end,
        )

    async def _handle_speech_start(self):
        """User started talking - stop AI and listen."""
        await self.audio.stop_playback()
        await self.realtime.cancel_response()

    async def _handle_speech_end(self):
        """User stopped talking - trigger AI response."""
        await self.realtime.commit_audio()

    async def run(self):
        """Main conversation loop."""

        # Task 1: Capture audio and send to AI
        async def capture_loop():
            async for chunk in self.audio.start_capture():
                await self.realtime.send_audio(chunk)

        # Task 2: Receive AI responses and play
        async def playback_loop():
            async for event in self.realtime.events():
                if event.type == "audio":
                    await self.audio.play_audio(event.data)
                elif event.type == "tool_call":
                    result = await self._execute_tool(event)
                    await self.realtime.send_tool_result(result)

        # Run both concurrently
        await asyncio.gather(capture_loop(), playback_loop())
```

---

### 4. Deploy to Any Platform

```python
# ===== Desktop App (voxterm) =====
from chatforge.adapters.audio import VoxStreamAudioAdapter
from chatforge.adapters.realtime import OpenAIRealtimeAdapter
from chatforge.agent import VoiceAgent

audio = VoxStreamAudioAdapter()
realtime = OpenAIRealtimeAdapter(api_key=os.environ["OPENAI_API_KEY"])
agent = VoiceAgent(audio=audio, realtime=realtime, tools=my_tools)

await agent.run()


# ===== Web App (FastAPI + React) =====
from chatforge.adapters.audio import WebRTCAudioAdapter

@app.websocket("/voice")
async def voice_endpoint(websocket: WebSocket):
    await websocket.accept()

    audio = WebRTCAudioAdapter(websocket)
    realtime = OpenAIRealtimeAdapter(api_key=os.environ["OPENAI_API_KEY"])
    agent = VoiceAgent(audio=audio, realtime=realtime, tools=my_tools)

    await agent.run()


# ===== Phone Call (Twilio) =====
from chatforge.adapters.audio import TwilioAudioAdapter

@app.websocket("/twilio-media-stream")
async def twilio_endpoint(websocket: WebSocket):
    await websocket.accept()

    audio = TwilioAudioAdapter(websocket)
    realtime = OpenAIRealtimeAdapter(api_key=os.environ["OPENAI_API_KEY"])
    agent = VoiceAgent(audio=audio, realtime=realtime, tools=my_tools)

    await agent.run()
```

---

## The Full Picture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           DEPLOYMENT OPTIONS                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                  │
│  │   Desktop   │    │     Web     │    │    Phone    │                  │
│  │    (CLI)    │    │  (Browser)  │    │   (Twilio)  │                  │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                  │
│         │                  │                  │                          │
│         ▼                  ▼                  ▼                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                  │
│  │  VoxStream  │    │   WebRTC    │    │   Twilio    │                  │
│  │   Adapter   │    │   Adapter   │    │   Adapter   │                  │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                  │
│         │                  │                  │                          │
│         └──────────────────┼──────────────────┘                          │
│                            │                                             │
│                            ▼                                             │
│                    ┌───────────────┐                                     │
│                    │   AudioStreamPort   │                                     │
│                    │  (Interface)  │                                     │
│                    └───────┬───────┘                                     │
│                            │                                             │
├────────────────────────────│─────────────────────────────────────────────┤
│                            ▼                                             │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                        SHARED CORE                                 │  │
│  │                                                                    │  │
│  │   ┌─────────────────────────────────────────────────────────┐     │  │
│  │   │                     VoiceAgent                           │     │  │
│  │   │                                                          │     │  │
│  │   │  - Capture audio → Send to AI                            │     │  │
│  │   │  - Receive AI audio → Play                               │     │  │
│  │   │  - Handle VAD (barge-in, turn-taking)                    │     │  │
│  │   │  - Execute tools                                         │     │  │
│  │   └─────────────────────────────────────────────────────────┘     │  │
│  │                            │                                       │  │
│  │                            ▼                                       │  │
│  │   ┌─────────────────────────────────────────────────────────┐     │  │
│  │   │                   RealtimeVoiceAPIPort                           │     │  │
│  │   │                   (Interface)                            │     │  │
│  │   └─────────────────────────────────────────────────────────┘     │  │
│  │                            │                                       │  │
│  └────────────────────────────│───────────────────────────────────────┘  │
│                               │                                          │
├───────────────────────────────│──────────────────────────────────────────┤
│                               ▼                                          │
│                    ┌─────────────────────┐                               │
│                    │   OpenAI Realtime   │                               │
│                    │      Adapter        │                               │
│                    └──────────┬──────────┘                               │
│                               │                                          │
│                               ▼                                          │
│                    ┌─────────────────────┐                               │
│                    │   OpenAI Realtime   │                               │
│                    │        API          │                               │
│                    │   (GPT-4o Audio)    │                               │
│                    └─────────────────────┘                               │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Package Responsibilities

| Package | Responsibility | Used By |
|---------|----------------|---------|
| **VoxStream** | Hardware audio I/O (mic/speaker via sounddevice) | VoxStreamAdapter |
| **Chatforge** | Ports, adapters, VoiceAgent, tool execution | All apps |
| **Voxon** | Sessions, memory, conversation orchestration | Apps needing persistence |

---

## Why This Architecture?

### 1. Write Once, Deploy Everywhere
```python
# Same VoiceAgent code for all platforms
agent = VoiceAgent(audio=any_adapter, realtime=openai, tools=tools)
```

### 2. Testable Without Hardware
```python
# Mock adapter for tests
class MockAudioAdapter(AudioStreamPort):
    def __init__(self, test_audio: bytes):
        self.test_audio = test_audio

    async def start_capture(self):
        yield self.test_audio  # Fake audio

    async def play_audio(self, chunk):
        self.played.append(chunk)  # Capture for assertions

# Test without microphone
audio = MockAudioAdapter(load_test_wav("hello.wav"))
agent = VoiceAgent(audio=audio, realtime=mock_realtime)
await agent.run()
assert "Hello" in mock_realtime.received_text
```

### 3. Swap Backends at Runtime
```python
# User preference determines backend
if user.prefers_browser:
    audio = WebRTCAudioAdapter(websocket)
elif user.prefers_phone:
    audio = TwilioAudioAdapter(media_stream)
else:
    audio = VoxStreamAudioAdapter()

# Same agent regardless
agent = VoiceAgent(audio=audio, ...)
```

### 4. Add New Platforms Easily
```python
# Future: Mobile app via React Native
class ReactNativeAudioAdapter(AudioStreamPort):
    """Bridge to React Native audio module."""
    ...

# Future: Discord bot
class DiscordVoiceAdapter(AudioStreamPort):
    """Discord voice channel integration."""
    ...
```

---

## Latency Impact

| Component | Latency | Notes |
|-----------|---------|-------|
| AudioStreamPort interface call | <1ms | Just a method call |
| VoxStream capture | 10-20ms | Hardware buffer |
| Format conversion | 1-2ms | Only for Twilio (μ-law) |
| WebSocket relay | 5-20ms | Only for WebRTC/Twilio |
| OpenAI network | 100-200ms | Dominant factor |
| OpenAI processing | 50-100ms | Model inference |
| **Total round-trip** | **280-500ms** | Acceptable for voice |

The abstraction adds ~5-10ms. Worth it for multi-platform support.

---

## Summary

| Approach | When to Use |
|----------|-------------|
| **Direct VoxStream** (no abstraction) | Single platform, maximum control |
| **AudioStreamPort abstraction** (this doc) | Multi-platform real-time voice |
| **Full Chatforge hexagonal** | Enterprise, multiple AI providers |

**For voice apps targeting desktop + web + phone: Use AudioStreamPort abstraction.**

VoxStream becomes one of several audio backends, all sharing the same VoiceAgent logic.

---

## Related Documents

| Document | Topic |
|----------|-------|
| `chatforge_audioport.md` | AudioPort for batch/file-based audio (transcription, TTS files) |
| `chatforge_compatibility_analysis.md` | Detailed latency and integration analysis |
