# Voice & Realtime API Support

This document explores how Chatforge could be enhanced to support real-time voice conversations using OpenAI's Realtime API and similar technologies.

---

## What is OpenAI's Realtime API?

OpenAI's Realtime API (released late 2024) enables **voice-to-voice conversations** with GPT-4o:

```
Traditional Flow (Text):
User types ──▶ Text ──▶ LLM ──▶ Text ──▶ User reads

Realtime API Flow (Voice):
User speaks ──▶ Audio ──▶ GPT-4o ──▶ Audio ──▶ User hears
                          (speech-to-speech, no intermediate text)
```

### Key Features

| Feature | Description |
|---------|-------------|
| **Native speech-to-speech** | Audio in, audio out (not speech→text→LLM→text→speech) |
| **Low latency** | ~300ms response time |
| **WebSocket-based** | Persistent bidirectional connection |
| **Function calling** | Tools work with voice conversations |
| **Interruption handling** | User can interrupt the AI mid-response |
| **Multiple voices** | Several voice options (alloy, echo, shimmer, etc.) |

---

## Current Chatforge Architecture vs Voice

```
Current Chatforge (Text-Based):

┌──────────┐     ┌─────────────────┐     ┌─────────────┐
│  Client  │────▶│  HTTP/SSE       │────▶│  ReActAgent │
│  (text)  │     │  Request        │     │  (text LLM) │
└──────────┘     └─────────────────┘     └─────────────┘
     ▲                                          │
     │                                          │
     └──────────────── Text Response ───────────┘


Voice Realtime (Bidirectional Audio):

┌──────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Client  │◀═══▶│  WebSocket      │◀═══▶│  Realtime API   │
│  (audio) │     │  (persistent)   │     │  (GPT-4o audio) │
└──────────┘     └─────────────────┘     └─────────────────┘
     │                   │                       │
     │    Audio chunks   │    Audio + Events     │
     └───────────────────┴───────────────────────┘
```

### Key Differences

| Aspect | Current (Text) | Voice Realtime |
|--------|----------------|----------------|
| Protocol | HTTP/SSE | WebSocket |
| Data format | JSON text | Audio chunks + JSON events |
| Connection | Request/response | Persistent session |
| Latency model | Time-to-first-token | Continuous streaming |
| Interruption | N/A | User can interrupt |

---

## Why Voice Matters

### 1. Accessibility
Voice interfaces are essential for:
- Users with visual impairments
- Hands-free scenarios (driving, cooking)
- Users who find typing difficult

### 2. Natural Interaction
Voice is often faster and more natural than typing, especially for:
- Complex explanations
- Brainstorming sessions
- Quick questions

### 3. Enterprise Use Cases
- **IT Support**: "My computer is making a weird noise" (user holds phone to speaker)
- **Customer Service**: Voice bots for call centers
- **Field Workers**: Hands-free assistance while working

---

## High-Level Implementation Plan

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         CHATCORE                                 │
│                                                                  │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │  RealtimeVoiceAPIPort   │    │  ReActAgent     │    │  Tools      │ │
│  │  (interface)    │───▶│  (orchestrator) │───▶│  (existing) │ │
│  └────────┬────────┘    └─────────────────┘    └─────────────┘ │
│           │                                                      │
│  ┌────────▼────────┐                                            │
│  │  Adapters:      │                                            │
│  │  - OpenAI       │                                            │
│  │  - Deepgram     │                                            │
│  │  - ElevenLabs   │                                            │
│  │  - Azure        │                                            │
│  └─────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
         │
         │ WebSocket
         ▼
┌─────────────────┐
│  Client App     │
│  (web/mobile)   │
│  - Mic input    │
│  - Speaker out  │
└─────────────────┘
```

### Step 1: Define Realtime Port

```python
# chatforge/ports/realtime.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import AsyncGenerator, Callable


class RealtimeEventType(str, Enum):
    """Events in a realtime session."""

    # Session lifecycle
    SESSION_CREATED = "session.created"
    SESSION_UPDATED = "session.updated"
    SESSION_ENDED = "session.ended"

    # Audio events
    AUDIO_BUFFER_APPEND = "audio.buffer.append"
    AUDIO_BUFFER_COMMIT = "audio.buffer.commit"
    AUDIO_BUFFER_CLEAR = "audio.buffer.clear"

    # Transcription
    TRANSCRIPT_PARTIAL = "transcript.partial"
    TRANSCRIPT_FINAL = "transcript.final"

    # Response events
    RESPONSE_STARTED = "response.started"
    RESPONSE_AUDIO_DELTA = "response.audio.delta"
    RESPONSE_AUDIO_DONE = "response.audio.done"
    RESPONSE_TEXT_DELTA = "response.text.delta"
    RESPONSE_DONE = "response.done"

    # Tool events
    TOOL_CALL_STARTED = "tool_call.started"
    TOOL_CALL_ARGUMENTS = "tool_call.arguments"
    TOOL_CALL_DONE = "tool_call.done"

    # User events
    USER_INTERRUPTED = "user.interrupted"

    # Errors
    ERROR = "error"


@dataclass
class RealtimeEvent:
    """Event in a realtime session."""

    type: RealtimeEventType
    data: dict
    timestamp: float | None = None


@dataclass
class RealtimeSessionConfig:
    """Configuration for a realtime session."""

    voice: str = "alloy"  # Voice to use for responses
    instructions: str = ""  # System instructions
    input_audio_format: str = "pcm16"  # Audio format for input
    output_audio_format: str = "pcm16"  # Audio format for output
    turn_detection: str = "server_vad"  # Voice activity detection mode
    temperature: float = 0.7
    max_response_tokens: int = 4096


class RealtimeVoiceAPIPort(ABC):
    """
    Port for realtime voice conversations.

    This interface defines the contract for realtime voice adapters.
    Implementations handle WebSocket connections and audio streaming.
    """

    @abstractmethod
    async def create_session(
        self,
        config: RealtimeSessionConfig,
        tools: list[dict] | None = None,
    ) -> str:
        """
        Create a new realtime session.

        Args:
            config: Session configuration.
            tools: Optional list of tool definitions for function calling.

        Returns:
            Session ID.
        """
        ...

    @abstractmethod
    async def send_audio(
        self,
        session_id: str,
        audio_chunk: bytes,
    ) -> None:
        """
        Send audio chunk to the session.

        Args:
            session_id: Active session ID.
            audio_chunk: Raw audio bytes (PCM16).
        """
        ...

    @abstractmethod
    async def commit_audio(self, session_id: str) -> None:
        """
        Signal end of user audio input.

        Args:
            session_id: Active session ID.
        """
        ...

    @abstractmethod
    async def cancel_response(self, session_id: str) -> None:
        """
        Cancel current response (user interrupted).

        Args:
            session_id: Active session ID.
        """
        ...

    @abstractmethod
    async def send_tool_result(
        self,
        session_id: str,
        tool_call_id: str,
        result: str,
    ) -> None:
        """
        Send tool execution result back to the session.

        Args:
            session_id: Active session ID.
            tool_call_id: ID of the tool call.
            result: Tool execution result as string.
        """
        ...

    @abstractmethod
    def subscribe_events(
        self,
        session_id: str,
    ) -> AsyncGenerator[RealtimeEvent, None]:
        """
        Subscribe to events from the session.

        Args:
            session_id: Active session ID.

        Yields:
            RealtimeEvent objects as they occur.
        """
        ...

    @abstractmethod
    async def close_session(self, session_id: str) -> None:
        """
        Close the realtime session.

        Args:
            session_id: Session ID to close.
        """
        ...
```

### Step 2: OpenAI Realtime Adapter

```python
# chatforge/adapters/realtime/openai.py

import asyncio
import json
import websockets
from chatforge.ports.realtime import (
    RealtimeVoiceAPIPort,
    RealtimeEvent,
    RealtimeEventType,
    RealtimeSessionConfig,
)


class OpenAIRealtimeAdapter(RealtimeVoiceAPIPort):
    """
    OpenAI Realtime API adapter.

    Implements the RealtimeVoiceAPIPort using OpenAI's WebSocket-based
    Realtime API for voice conversations with GPT-4o.
    """

    REALTIME_URL = "wss://api.openai.com/v1/realtime"
    MODEL = "gpt-4o-realtime-preview-2024-12-17"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._sessions: dict[str, websockets.WebSocketClientProtocol] = {}
        self._event_queues: dict[str, asyncio.Queue] = {}

    async def create_session(
        self,
        config: RealtimeSessionConfig,
        tools: list[dict] | None = None,
    ) -> str:
        """Create WebSocket connection and initialize session."""

        url = f"{self.REALTIME_URL}?model={self.MODEL}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1",
        }

        ws = await websockets.connect(url, extra_headers=headers)

        # Wait for session.created event
        response = await ws.recv()
        event = json.loads(response)
        session_id = event["session"]["id"]

        # Store connection
        self._sessions[session_id] = ws
        self._event_queues[session_id] = asyncio.Queue()

        # Configure session
        await ws.send(json.dumps({
            "type": "session.update",
            "session": {
                "voice": config.voice,
                "instructions": config.instructions,
                "input_audio_format": config.input_audio_format,
                "output_audio_format": config.output_audio_format,
                "turn_detection": {"type": config.turn_detection},
                "temperature": config.temperature,
                "max_response_output_tokens": config.max_response_tokens,
                "tools": tools or [],
            }
        }))

        # Start event listener
        asyncio.create_task(self._listen_events(session_id, ws))

        return session_id

    async def _listen_events(self, session_id: str, ws) -> None:
        """Background task to listen for events."""
        try:
            async for message in ws:
                event_data = json.loads(message)
                event = RealtimeEvent(
                    type=RealtimeEventType(event_data.get("type", "error")),
                    data=event_data,
                )
                await self._event_queues[session_id].put(event)
        except websockets.exceptions.ConnectionClosed:
            await self._event_queues[session_id].put(
                RealtimeEvent(type=RealtimeEventType.SESSION_ENDED, data={})
            )

    async def send_audio(self, session_id: str, audio_chunk: bytes) -> None:
        """Send audio chunk to session."""
        import base64
        ws = self._sessions[session_id]
        await ws.send(json.dumps({
            "type": "input_audio_buffer.append",
            "audio": base64.b64encode(audio_chunk).decode(),
        }))

    async def commit_audio(self, session_id: str) -> None:
        """Commit audio buffer (user finished speaking)."""
        ws = self._sessions[session_id]
        await ws.send(json.dumps({"type": "input_audio_buffer.commit"}))

    async def cancel_response(self, session_id: str) -> None:
        """Cancel current response."""
        ws = self._sessions[session_id]
        await ws.send(json.dumps({"type": "response.cancel"}))

    async def send_tool_result(
        self,
        session_id: str,
        tool_call_id: str,
        result: str,
    ) -> None:
        """Send tool result back."""
        ws = self._sessions[session_id]
        await ws.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": tool_call_id,
                "output": result,
            }
        }))
        # Trigger response generation
        await ws.send(json.dumps({"type": "response.create"}))

    async def subscribe_events(
        self,
        session_id: str,
    ) -> AsyncGenerator[RealtimeEvent, None]:
        """Yield events from session."""
        queue = self._event_queues[session_id]
        while True:
            event = await queue.get()
            yield event
            if event.type == RealtimeEventType.SESSION_ENDED:
                break

    async def close_session(self, session_id: str) -> None:
        """Close WebSocket connection."""
        if session_id in self._sessions:
            await self._sessions[session_id].close()
            del self._sessions[session_id]
            del self._event_queues[session_id]
```

### Step 3: Voice Agent Coordinator

```python
# chatforge/agent/voice.py

from chatforge.ports.realtime import (
    RealtimeVoiceAPIPort,
    RealtimeEvent,
    RealtimeEventType,
    RealtimeSessionConfig,
)


class VoiceAgent:
    """
    Voice-enabled agent using Realtime API.

    Coordinates between the Realtime API and existing Chatforge tools.
    """

    def __init__(
        self,
        realtime: RealtimeVoiceAPIPort,
        tools: list,  # Same tools as ReActAgent
        system_prompt: str = "",
        voice: str = "alloy",
    ):
        self.realtime = realtime
        self.tools = tools
        self.system_prompt = system_prompt
        self.voice = voice
        self._session_id: str | None = None

    async def start_session(self) -> str:
        """Start a new voice session."""

        # Convert tools to OpenAI function format
        tool_definitions = [
            {
                "type": "function",
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.args_schema.schema() if tool.args_schema else {},
            }
            for tool in self.tools
        ]

        config = RealtimeSessionConfig(
            voice=self.voice,
            instructions=self.system_prompt,
        )

        self._session_id = await self.realtime.create_session(
            config=config,
            tools=tool_definitions,
        )

        return self._session_id

    async def handle_audio_stream(
        self,
        audio_chunks: AsyncGenerator[bytes, None],
    ) -> AsyncGenerator[bytes, None]:
        """
        Handle bidirectional audio streaming.

        Args:
            audio_chunks: Incoming audio from user microphone.

        Yields:
            Audio chunks to play on user speakers.
        """
        if not self._session_id:
            raise RuntimeError("No active session. Call start_session() first.")

        # Start audio sender task
        async def send_audio():
            async for chunk in audio_chunks:
                await self.realtime.send_audio(self._session_id, chunk)

        sender_task = asyncio.create_task(send_audio())

        # Process events and yield audio responses
        async for event in self.realtime.subscribe_events(self._session_id):
            match event.type:
                case RealtimeEventType.RESPONSE_AUDIO_DELTA:
                    # Yield audio chunk to play
                    import base64
                    audio = base64.b64decode(event.data.get("delta", ""))
                    yield audio

                case RealtimeEventType.TOOL_CALL_DONE:
                    # Execute tool and send result
                    tool_name = event.data.get("name")
                    tool_args = event.data.get("arguments", {})
                    call_id = event.data.get("call_id")

                    result = await self._execute_tool(tool_name, tool_args)
                    await self.realtime.send_tool_result(
                        self._session_id,
                        call_id,
                        result,
                    )

                case RealtimeEventType.USER_INTERRUPTED:
                    # User interrupted, cancel current response
                    await self.realtime.cancel_response(self._session_id)

                case RealtimeEventType.SESSION_ENDED:
                    break

        sender_task.cancel()

    async def _execute_tool(self, name: str, args: dict) -> str:
        """Execute a tool by name."""
        for tool in self.tools:
            if tool.name == name:
                result = await tool.ainvoke(args)
                return str(result)
        return f"Unknown tool: {name}"

    async def end_session(self) -> None:
        """End the voice session."""
        if self._session_id:
            await self.realtime.close_session(self._session_id)
            self._session_id = None
```

### Step 4: FastAPI WebSocket Endpoint

```python
# chatforge/adapters/fastapi/voice_routes.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from chatforge.agent.voice import VoiceAgent
from chatforge.adapters.realtime import OpenAIRealtimeAdapter

router = APIRouter(prefix="/voice", tags=["voice"])


@router.websocket("/session")
async def voice_session(websocket: WebSocket):
    """
    WebSocket endpoint for voice conversations.

    Client sends: Raw audio chunks (PCM16)
    Server sends: Audio response chunks (PCM16)
    """
    await websocket.accept()

    # Create voice agent
    realtime = OpenAIRealtimeAdapter(api_key=settings.OPENAI_API_KEY)
    agent = VoiceAgent(
        realtime=realtime,
        tools=get_tools(),
        system_prompt="You are a helpful voice assistant...",
        voice="alloy",
    )

    try:
        # Start session
        session_id = await agent.start_session()
        await websocket.send_json({"type": "session.started", "session_id": session_id})

        # Audio stream from client
        async def receive_audio():
            while True:
                try:
                    data = await websocket.receive_bytes()
                    yield data
                except WebSocketDisconnect:
                    break

        # Stream audio responses to client
        async for audio_chunk in agent.handle_audio_stream(receive_audio()):
            await websocket.send_bytes(audio_chunk)

    except WebSocketDisconnect:
        pass
    finally:
        await agent.end_session()
```

---

## Client-Side Requirements

Voice chat requires client-side audio handling:

```javascript
// Example: Browser client

class VoiceChatClient {
  constructor(wsUrl) {
    this.ws = new WebSocket(wsUrl);
    this.audioContext = new AudioContext({ sampleRate: 24000 });
    this.mediaStream = null;
  }

  async start() {
    // Get microphone access
    this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });

    // Create audio processor
    const source = this.audioContext.createMediaStreamSource(this.mediaStream);
    const processor = this.audioContext.createScriptProcessor(4096, 1, 1);

    processor.onaudioprocess = (e) => {
      const pcm16 = this.floatToPCM16(e.inputBuffer.getChannelData(0));
      this.ws.send(pcm16);
    };

    source.connect(processor);
    processor.connect(this.audioContext.destination);

    // Handle incoming audio
    this.ws.onmessage = async (event) => {
      if (event.data instanceof Blob) {
        const audioData = await event.data.arrayBuffer();
        this.playAudio(audioData);
      }
    };
  }

  floatToPCM16(float32Array) {
    const buffer = new ArrayBuffer(float32Array.length * 2);
    const view = new DataView(buffer);
    for (let i = 0; i < float32Array.length; i++) {
      const s = Math.max(-1, Math.min(1, float32Array[i]));
      view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
    return buffer;
  }

  playAudio(pcm16Data) {
    // Convert PCM16 to float and play via Web Audio API
    // ...
  }

  stop() {
    this.mediaStream?.getTracks().forEach(track => track.stop());
    this.ws.close();
  }
}
```

---

## Alternative Providers

OpenAI isn't the only option. Chatforge could support multiple realtime providers:

| Provider | Capabilities | Notes |
|----------|--------------|-------|
| **OpenAI Realtime** | Voice-to-voice, function calling | Native GPT-4o, lowest latency |
| **Deepgram** | STT + TTS | High-quality transcription |
| **ElevenLabs** | TTS with voice cloning | Best voice quality |
| **Azure Speech** | STT + TTS | Enterprise features |
| **Twilio** | Phone integration | Call center use cases |

A hybrid approach is possible:

```
Hybrid Voice Pipeline:

User speaks ──▶ Deepgram STT ──▶ Text ──▶ Chatforge Agent ──▶ Text ──▶ ElevenLabs TTS ──▶ Audio
```

This is more flexible but higher latency than OpenAI's native speech-to-speech.

---

## Summary

| Aspect | Current Chatforge | With Voice Support |
|--------|------------------|-------------------|
| Input | Text | Text + Audio |
| Output | Text/SSE | Text + Audio stream |
| Protocol | HTTP/SSE | HTTP + WebSocket |
| Connection | Stateless requests | Persistent sessions |
| Tools | ✅ Supported | ✅ Same tools work |
| Latency | TTFT ~1-2s | ~300ms response |

### Files to Create

| File | Purpose |
|------|---------|
| `chatforge/ports/realtime.py` | RealtimeVoiceAPIPort interface, events |
| `chatforge/adapters/realtime/__init__.py` | Export adapters |
| `chatforge/adapters/realtime/openai.py` | OpenAI Realtime adapter |
| `chatforge/agent/voice.py` | VoiceAgent coordinator |
| `chatforge/adapters/fastapi/voice_routes.py` | WebSocket endpoint |

### Key Considerations

1. **Cost**: Realtime API is more expensive than text ($0.06/min audio)
2. **Complexity**: WebSocket session management is more complex than HTTP
3. **Client requirements**: Needs browser audio APIs or mobile SDK
4. **Tool compatibility**: Existing tools work, but responses should be voice-friendly
5. **Fallback**: Should gracefully fall back to text if audio fails
