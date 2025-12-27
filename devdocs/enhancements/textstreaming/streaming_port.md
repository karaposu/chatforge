# Streaming Port: True LLM Streaming for Chatforge

This document defines the streaming architecture for Chatforge, enabling true token-by-token streaming from LLM providers to end clients.

---

## The Streaming Problem

Many chat implementations "fake" streaming by chunking completed responses:

```
Fake Streaming:
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  User    │────▶│  Agent   │────▶│   LLM    │────▶│  Agent   │
│ Request  │     │ process  │     │  (wait   │     │ response │
└──────────┘     │ message  │     │  full)   │     │ complete │
                 └──────────┘     └──────────┘     └────┬─────┘
                                                        │
                 ┌──────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  Chunk completed response into pieces (FAKE!)               │
│  for i in range(0, len(response), 50):                      │
│      yield response[i:i+50]                                 │
└─────────────────────────────────────────────────────────────┘
```

**Problems:**
- User waits for entire response before seeing anything
- No benefit of streaming latency (time-to-first-token)
- Wastes the streaming capability that LLM providers offer

---

## True Streaming Architecture

```
True Streaming:
┌──────────┐     ┌──────────┐     ┌──────────┐
│  User    │────▶│  Agent   │────▶│   LLM    │
│ Request  │     │ stream   │     │ stream() │
└──────────┘     └──────────┘     └────┬─────┘
                                       │
         ┌─────────────────────────────┘
         ▼
    Token 1 ──▶ yield ──▶ Adapter ──▶ User sees "I"
    Token 2 ──▶ yield ──▶ Adapter ──▶ User sees "I will"
    Token 3 ──▶ yield ──▶ Adapter ──▶ User sees "I will help"
    ...
    Token N ──▶ yield ──▶ Adapter ──▶ User sees full response
```

**Benefits:**
- Sub-second time-to-first-token
- Progressive rendering in UI
- Better perceived performance

---

## ReACT Streaming Challenge

ReACT agents are **iterative** - they think, act, observe, repeat:

```
Simple LLM (easy to stream):
    User ──▶ LLM ──▶ Stream tokens ──▶ Done

ReACT Agent (complex):
    User ──▶ Think ──▶ Tool Call ──▶ Observe ──▶ Think ──▶ Response
              │           │            │           │          │
              ▼           ▼            ▼           ▼          ▼
           Stream?     Emit event   Emit event  Stream?    Stream ✓
```

**Key insight:** Only the **final response** benefits from token streaming. Tool calls need the full LLM output to parse the function call.

---

## Stream Event Types

```python
# chatforge/ports/streaming.py

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StreamEventType(str, Enum):
    """Types of events emitted during streaming."""

    TOKEN = "token"           # LLM token chunk
    TOOL_CALL = "tool_call"   # Tool invocation starting
    TOOL_RESULT = "tool_result"  # Tool execution completed
    THINKING = "thinking"     # Agent reasoning (optional)
    ERROR = "error"           # Error occurred
    DONE = "done"             # Stream completed


@dataclass
class StreamEvent:
    """Event emitted during agent streaming."""

    type: StreamEventType
    content: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "type": self.type.value,
            "content": self.content,
            "metadata": self.metadata,
        }
```

---

## Streaming Port (Interface)

```python
# chatforge/ports/streaming.py

from typing import AsyncGenerator, Protocol


class StreamingPort(Protocol):
    """
    Port for streaming responses to clients.

    Implementations handle the transport-specific details
    of delivering stream events to end users.
    """

    async def stream_to_client(
        self,
        context_id: str,
        events: AsyncGenerator[StreamEvent, None],
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream events to the client.

        Args:
            context_id: Unique identifier for the conversation/request.
            events: Async generator of StreamEvent objects.

        Yields:
            Bytes to send to the client (format depends on adapter).
        """
        ...

    async def close_stream(self, context_id: str) -> None:
        """Close the stream for a context."""
        ...
```

---

## Agent Streaming Interface

```python
# chatforge/agent/engine.py

from typing import AsyncGenerator
from chatforge.ports.streaming import StreamEvent, StreamEventType


class ReActAgent:
    """ReACT agent with streaming support."""

    async def process_stream(
        self,
        message: str,
        history: list | None = None,
        context: dict | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Process message with streaming output.

        Yields StreamEvent objects as the agent works:
        - THINKING: Agent reasoning steps
        - TOOL_CALL: When invoking a tool
        - TOOL_RESULT: Tool execution results
        - TOKEN: Response tokens as they're generated
        - DONE: When processing completes
        - ERROR: If an error occurs

        Args:
            message: User message to process.
            history: Optional conversation history.
            context: Optional context dictionary.

        Yields:
            StreamEvent objects.
        """
        state = self._build_initial_state(message, history, context)

        try:
            async for event in self._graph.astream_events(state, version="v2"):
                match event["event"]:
                    case "on_chat_model_stream":
                        chunk = event["data"]["chunk"]
                        if chunk.content:
                            yield StreamEvent(
                                type=StreamEventType.TOKEN,
                                content=chunk.content,
                            )

                    case "on_tool_start":
                        yield StreamEvent(
                            type=StreamEventType.TOOL_CALL,
                            content=event["name"],
                            metadata={"input": event.get("data", {}).get("input")},
                        )

                    case "on_tool_end":
                        yield StreamEvent(
                            type=StreamEventType.TOOL_RESULT,
                            content=str(event["data"].get("output", "")),
                            metadata={"tool": event.get("name")},
                        )

            yield StreamEvent(type=StreamEventType.DONE)

        except Exception as e:
            yield StreamEvent(
                type=StreamEventType.ERROR,
                content=str(e),
            )
```

---

## Streaming Adapters

### SSE Adapter (FastAPI)

```python
# chatforge/adapters/streaming/sse.py

import json
from typing import AsyncGenerator
from chatforge.ports.streaming import StreamingPort, StreamEvent


class SSEStreamingAdapter:
    """Server-Sent Events streaming for FastAPI."""

    async def stream_to_client(
        self,
        context_id: str,
        events: AsyncGenerator[StreamEvent, None],
    ) -> AsyncGenerator[bytes, None]:
        """Convert StreamEvents to SSE format."""
        async for event in events:
            data = json.dumps(event.to_dict())
            yield f"data: {data}\n\n".encode()

    async def close_stream(self, context_id: str) -> None:
        """SSE streams close automatically."""
        pass
```

### WebSocket Adapter

```python
# chatforge/adapters/streaming/websocket.py

from typing import AsyncGenerator
from chatforge.ports.streaming import StreamingPort, StreamEvent


class WebSocketStreamingAdapter:
    """WebSocket streaming adapter."""

    def __init__(self):
        self._connections: dict[str, Any] = {}

    def register_connection(self, context_id: str, websocket) -> None:
        """Register a WebSocket connection."""
        self._connections[context_id] = websocket

    async def stream_to_client(
        self,
        context_id: str,
        events: AsyncGenerator[StreamEvent, None],
    ) -> AsyncGenerator[bytes, None]:
        """Send events via WebSocket."""
        ws = self._connections.get(context_id)
        if not ws:
            return

        async for event in events:
            await ws.send_json(event.to_dict())
            yield b""  # Satisfy generator interface

    async def close_stream(self, context_id: str) -> None:
        """Close WebSocket connection."""
        if context_id in self._connections:
            await self._connections[context_id].close()
            del self._connections[context_id]
```

### Message Update Adapter (Slack-style)

```python
# chatforge/adapters/streaming/message_update.py

from typing import AsyncGenerator, Callable, Awaitable
from chatforge.ports.streaming import StreamingPort, StreamEvent, StreamEventType


class MessageUpdateStreamingAdapter:
    """
    Streaming via message updates (for platforms like Slack).

    Accumulates tokens and periodically updates the message in-place.
    """

    def __init__(
        self,
        update_fn: Callable[[str, str], Awaitable[None]],
        update_interval: int = 10,  # Update every N tokens
    ):
        """
        Args:
            update_fn: Async function(context_id, text) to update message.
            update_interval: How often to push updates (in tokens).
        """
        self._update_fn = update_fn
        self._update_interval = update_interval

    async def stream_to_client(
        self,
        context_id: str,
        events: AsyncGenerator[StreamEvent, None],
    ) -> AsyncGenerator[bytes, None]:
        """Accumulate and update message periodically."""
        buffer = ""
        token_count = 0

        async for event in events:
            if event.type == StreamEventType.TOKEN and event.content:
                buffer += event.content
                token_count += 1

                if token_count % self._update_interval == 0:
                    await self._update_fn(context_id, buffer)

            elif event.type == StreamEventType.DONE:
                # Final update
                await self._update_fn(context_id, buffer)

            yield b""

    async def close_stream(self, context_id: str) -> None:
        """No cleanup needed."""
        pass
```

---

## FastAPI Integration

```python
# Example usage in FastAPI routes

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from chatforge.agent import ReActAgent
from chatforge.adapters.streaming import SSEStreamingAdapter

app = FastAPI()
agent = ReActAgent(...)
sse_adapter = SSEStreamingAdapter()


@app.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    """Stream chat response via SSE."""

    async def generate():
        events = agent.process_stream(
            message=request.message,
            history=request.history,
        )
        async for chunk in sse_adapter.stream_to_client(
            context_id=request.conversation_id,
            events=events,
        ):
            yield chunk

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
```

---

## Architecture Diagram

```
                    ┌─────────────────────────────────────┐
                    │           CHATCORE                   │
                    │                                      │
┌──────────┐        │   ┌─────────────────────────────┐   │
│  FastAPI │◀──SSE──│───│     StreamingPort           │   │
│  Client  │        │   │     (interface)             │   │
└──────────┘        │   └──────────────┬──────────────┘   │
                    │                  │                   │
┌──────────┐        │   ┌──────────────▼──────────────┐   │
│  Slack   │◀─update│───│      ReActAgent             │   │
│  User    │        │   │      process_stream()       │   │
└──────────┘        │   └──────────────┬──────────────┘   │
                    │                  │                   │
┌──────────┐        │   ┌──────────────▼──────────────┐   │
│WebSocket │◀──msg──│───│      LLM (streaming=True)   │   │
│  Client  │        │   │      .astream()             │   │
└──────────┘        │   └─────────────────────────────┘   │
                    │                                      │
                    └─────────────────────────────────────┘
```

The agent produces `StreamEvent` objects. Different adapters deliver them to clients via their native protocols (SSE, WebSocket, message updates).

---

## Implementation Options

### Option A: Stream Final Response Only (Simpler)

Stream only the last agent response, not intermediate tool calls:

```python
async def process_stream(self, message: str) -> AsyncGenerator[StreamEvent, None]:
    # Run ReACT loop normally (tool calls complete fully)
    state = await self._run_react_loop(message)

    # Final response - stream it
    streaming_llm = self._llm.with_config({"streaming": True})
    async for chunk in streaming_llm.astream(state["messages"]):
        yield StreamEvent(type=StreamEventType.TOKEN, content=chunk.content)

    yield StreamEvent(type=StreamEventType.DONE)
```

**Pros:** Simple, covers main use case
**Cons:** Tool calls still block

### Option B: Stream Everything with LangGraph (Recommended)

Use LangGraph's native `astream_events()` for full visibility:

```python
async def process_stream(self, message: str) -> AsyncGenerator[StreamEvent, None]:
    async for event in self._graph.astream_events(state, version="v2"):
        match event["event"]:
            case "on_chat_model_stream":
                yield StreamEvent(type=StreamEventType.TOKEN, ...)
            case "on_tool_start":
                yield StreamEvent(type=StreamEventType.TOOL_CALL, ...)
            case "on_tool_end":
                yield StreamEvent(type=StreamEventType.TOOL_RESULT, ...)

    yield StreamEvent(type=StreamEventType.DONE)
```

**Pros:** Full visibility into agent behavior, true streaming
**Cons:** More complex event handling

---

## Summary

| Component | Purpose |
|-----------|---------|
| `StreamEvent` | Dataclass for streaming events |
| `StreamEventType` | Enum of event types (TOKEN, TOOL_CALL, etc.) |
| `StreamingPort` | Protocol interface for streaming adapters |
| `SSEStreamingAdapter` | Server-Sent Events for HTTP clients |
| `WebSocketStreamingAdapter` | WebSocket for real-time apps |
| `MessageUpdateStreamingAdapter` | Edit-in-place for Slack-style platforms |
| `ReActAgent.process_stream()` | Agent method yielding StreamEvents |

---

## Files to Create

| File | Purpose |
|------|---------|
| `chatforge/ports/streaming.py` | StreamEvent, StreamEventType, StreamingPort |
| `chatforge/adapters/streaming/__init__.py` | Export adapters |
| `chatforge/adapters/streaming/sse.py` | SSE adapter |
| `chatforge/adapters/streaming/websocket.py` | WebSocket adapter |
| `chatforge/adapters/streaming/message_update.py` | Message update adapter |

---

## LangGraph Reference

```python
# LangGraph provides astream_events() for full visibility
async for event in graph.astream_events(state, version="v2"):
    print(event["event"])  # Event type
    print(event["data"])   # Event data

# Event types:
# - on_chain_start/end
# - on_chat_model_start/stream/end
# - on_tool_start/end
# - on_retriever_start/end
```

This is the foundation for true streaming in a ReACT agent.
