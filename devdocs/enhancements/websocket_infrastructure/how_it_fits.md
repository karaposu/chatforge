# WebSocket Infrastructure: How It Fits

**Date:** 2025-01-01

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        DOMAIN LAYER                             │
│                                                                 │
│   VoiceAgent / ConversationService                              │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────┐                                       │
│   │ RealtimeVoiceAPIPort│  ← Abstract interface (contract)      │
│   └─────────────────────┘                                       │
│              │                                                  │
└──────────────┼──────────────────────────────────────────────────┘
               │
┌──────────────┼──────────────────────────────────────────────────┐
│              ▼                     ADAPTER LAYER                │
│   ┌─────────────────────┐                                       │
│   │OpenAIRealtimeAdapter│  ← Implements the port                │
│   └─────────────────────┘                                       │
│              │                                                  │
│              │ uses internally                                  │
│              ▼                                                  │
│   ┌─────────────────────┐                                       │
│   │   WebSocketClient   │  ← Infrastructure (hidden detail)     │
│   └─────────────────────┘                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer Responsibilities

| Layer | Knows About WebSocket? | Why |
|-------|----------------------|-----|
| Domain (VoiceAgent) | No | Talks to abstract `RealtimeVoiceAPIPort` |
| Port interface | No | Defines `send_audio()`, `events()`, not WebSocket details |
| Adapter | Yes | Implementation detail - uses `WebSocketClient` internally |
| Infrastructure | Yes | It IS the WebSocket client |

---

## Example Code Flow

### The Port (Abstract Contract)

```python
# chatforge/ports/realtime_voice.py

from abc import ABC, abstractmethod
from typing import AsyncGenerator
from dataclasses import dataclass


@dataclass
class VoiceEvent:
    """Domain event from realtime voice API."""
    type: str
    data: dict


class RealtimeVoiceAPIPort(ABC):
    """Port for realtime voice conversation APIs."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the realtime API."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection."""
        ...

    @abstractmethod
    async def send_audio(self, audio: bytes) -> None:
        """Send audio chunk to the API."""
        ...

    @abstractmethod
    async def events(self) -> AsyncGenerator[VoiceEvent, None]:
        """Receive events from the API."""
        ...

    @abstractmethod
    async def send_text(self, text: str) -> None:
        """Send text message to the API."""
        ...
```

### The Adapter (Implementation)

```python
# chatforge/adapters/realtime/openai.py

import base64
import json
from typing import AsyncGenerator

from chatforge.ports.realtime_voice import RealtimeVoiceAPIPort, VoiceEvent
from chatforge.infrastructure.websocket import (
    WebSocketClient,
    WebSocketConfig,
    JsonSerializer,
)


class OpenAIRealtimeAdapter(RealtimeVoiceAPIPort):
    """OpenAI Realtime API adapter using WebSocket infrastructure."""

    def __init__(self, api_key: str, model: str = "gpt-4o-realtime-preview"):
        self._api_key = api_key
        self._model = model
        self._ws: WebSocketClient | None = None

    async def connect(self) -> None:
        """Connect to OpenAI Realtime API."""
        config = WebSocketConfig(
            url=f"wss://api.openai.com/v1/realtime?model={self._model}",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "OpenAI-Beta": "realtime=v1",
            },
            serializer=JsonSerializer(),  # OpenAI uses JSON events
            enable_metrics=True,
        )
        self._ws = WebSocketClient(config)
        await self._ws.connect()

    async def disconnect(self) -> None:
        """Disconnect from OpenAI Realtime API."""
        if self._ws:
            await self._ws.disconnect()
            self._ws = None

    async def send_audio(self, audio: bytes) -> None:
        """Send audio chunk to OpenAI."""
        if not self._ws:
            raise RuntimeError("Not connected")

        # Translate domain concept → OpenAI protocol
        await self._ws.send_json({
            "type": "input_audio_buffer.append",
            "audio": base64.b64encode(audio).decode()
        })

    async def send_text(self, text: str) -> None:
        """Send text message to OpenAI."""
        if not self._ws:
            raise RuntimeError("Not connected")

        await self._ws.send_json({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": text}]
            }
        })

    async def events(self) -> AsyncGenerator[VoiceEvent, None]:
        """Receive events from OpenAI."""
        if not self._ws:
            raise RuntimeError("Not connected")

        async for msg in self._ws.messages():
            event = json.loads(msg.as_text())
            # Translate OpenAI protocol → domain concept
            yield VoiceEvent(
                type=event.get("type", "unknown"),
                data=event
            )

    async def __aenter__(self) -> "OpenAIRealtimeAdapter":
        await self.connect()
        return self

    async def __aexit__(self, *args) -> None:
        await self.disconnect()
```

### Usage in Domain Layer

```python
# chatforge/services/voice_agent.py

from chatforge.ports.realtime_voice import RealtimeVoiceAPIPort


class VoiceAgent:
    """Domain service that uses realtime voice API."""

    def __init__(self, realtime_api: RealtimeVoiceAPIPort):
        # Depends on PORT, not adapter - no WebSocket knowledge here!
        self._api = realtime_api

    async def have_conversation(self) -> None:
        async with self._api:
            # Send audio from microphone
            await self._api.send_audio(audio_chunk)

            # Process events
            async for event in self._api.events():
                if event.type == "response.audio.delta":
                    # Play audio
                    pass
                elif event.type == "response.text.delta":
                    # Show text
                    pass
```

---

## Multiple Adapters, Same Infrastructure

The WebSocket infrastructure can be reused across different adapters:

```python
# OpenAI Realtime
class OpenAIRealtimeAdapter(RealtimeVoiceAPIPort):
    def __init__(self, api_key: str):
        self._ws = WebSocketClient(WebSocketConfig(
            url="wss://api.openai.com/v1/realtime",
            serializer=JsonSerializer(),
        ))

# Twilio (hypothetical)
class TwilioRealtimeAdapter(RealtimeVoiceAPIPort):
    def __init__(self, account_sid: str):
        self._ws = WebSocketClient(WebSocketConfig(
            url="wss://media.twilio.com/v1/streams",
            serializer=JsonSerializer(),
        ))

# Custom WebSocket server
class CustomRealtimeAdapter(RealtimeVoiceAPIPort):
    def __init__(self, server_url: str):
        self._ws = WebSocketClient(WebSocketConfig(
            url=server_url,
            serializer=RawSerializer(),  # Binary protocol
            enable_send_queue=False,     # Fast lane for low latency
        ))
```

---

## Benefits of This Architecture

1. **Domain stays clean** - VoiceAgent doesn't know or care about WebSockets

2. **Swappable adapters** - Switch from OpenAI to Twilio without changing domain code

3. **Testable** - Mock the port interface without real WebSocket connections:
   ```python
   class MockRealtimeAdapter(RealtimeVoiceAPIPort):
       async def send_audio(self, audio: bytes) -> None:
           self.sent_audio.append(audio)  # Just record for testing
   ```

4. **Reusable infrastructure** - Same `WebSocketClient` works for any WebSocket-based API

5. **Configurable per use case** - OpenAI might need metrics, low-latency audio might need fast lane mode

---

## File Structure

```
chatforge/
├── ports/
│   └── realtime_voice.py          # Abstract port interface
├── adapters/
│   └── realtime/
│       ├── openai.py              # OpenAI implementation
│       ├── twilio.py              # Twilio implementation
│       └── mock.py                # Mock for testing
├── infrastructure/
│   └── websocket/
│       ├── client.py              # WebSocketClient
│       ├── types.py               # Config, enums
│       ├── serializers.py         # JSON, Raw, MsgPack
│       ├── metrics.py             # Connection metrics
│       ├── reconnect.py           # Backoff policies
│       └── exceptions.py          # Custom exceptions
└── services/
    └── voice_agent.py             # Domain service (no WebSocket knowledge)
```

---

## Summary

The WebSocket infrastructure is a **shared internal utility** that:
- Lives in `chatforge/infrastructure/websocket/`
- Is used by **adapters** (not ports or domain)
- Never leaks into the domain layer
- Provides reusable features (reconnection, metrics, serialization)
- Allows each adapter to configure it for their specific needs
