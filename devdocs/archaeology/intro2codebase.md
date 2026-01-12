# Introduction to the Chatforge Codebase

Welcome to Chatforge! This document will help you understand how the codebase is designed - the patterns, abstractions, and how data flows through the system.

---

## The Core Design Philosophy

Chatforge follows **Hexagonal Architecture** (also called "Ports and Adapters"). The key idea is simple:

> **Your business logic should never know about the outside world.**

The agent doesn't know if it's talking to SQLite or PostgreSQL. The voice system doesn't know if audio comes from a microphone or a WebRTC stream. Everything external is abstracted behind interfaces.

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOUR APPLICATION                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      CORE DOMAIN                           │  │
│  │     ReActAgent  •  LLM Factory  •  Business Logic          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                         PORTS (Interfaces)                       │
│    ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│    │ Storage  │ │ Realtime │ │   TTS    │ │ Messaging│         │
│    │   Port   │ │Voice Port│ │   Port   │ │   Port   │   ...   │
│    └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘         │
│         │            │            │            │                 │
│                         ADAPTERS (Implementations)               │
│    ┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐         │
│    │ SQLite   │ │ OpenAI   │ │ElevenLabs│ │  Slack   │         │
│    │ Adapter  │ │ Adapter  │ │ Adapter  │ │ Adapter  │   ...   │
│    └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                    EXTERNAL SYSTEMS
        (Databases, APIs, Hardware, Platforms)
```

---

## Main Abstractions

### 1. Ports (The Contracts)

**Location:** `chatforge/ports/`

Ports are abstract interfaces that define *what* capabilities the system needs, without saying *how* they work. Each port is a Python ABC (Abstract Base Class).

| Port | Purpose | Key Methods |
|------|---------|-------------|
| `StoragePort` | Conversation persistence | `save_message()`, `get_conversation()`, `cleanup_expired()` |
| `RealtimeVoiceAPIPort` | Real-time AI voice | `connect()`, `send_audio()`, `events()`, `interrupt()` |
| `AudioCapturePort` | Microphone input | `start_capture()`, `stop_capture()` |
| `AudioPlaybackPort` | Speaker output | `play()`, `stop_playback()` |
| `TTSPort` | Text-to-speech | `synthesize()`, `stream()` |
| `VADPort` | Voice activity detection | `process_audio()`, `reset()` |
| `MessagingPlatformIntegrationPort` | External chat platforms | `send_message()`, `get_conversation_history()` |
| `KnowledgePort` | RAG/search | `search()` |
| `TicketingPort` | Ticket systems | `create_ticket()`, `update_ticket()` |
| `TracingPort` | Observability | `span()`, `set_trace_metadata()` |

**Key Principle:** The core agent only imports from `ports/`. It never imports from `adapters/`.

### 2. Adapters (The Implementations)

**Location:** `chatforge/adapters/`

Adapters implement ports for specific technologies. You can swap adapters without changing application code.

```
StoragePort
├── InMemoryStorageAdapter    # RAM-based, ephemeral
├── SQLiteStorageAdapter      # File-based SQLite
└── SQLAlchemyStorageAdapter  # Full ORM for production DBs

RealtimeVoiceAPIPort
├── OpenAIRealtimeAdapter     # OpenAI Realtime API
└── MockRealtimeAdapter       # Testing without API calls

AudioCapturePort
├── SounddeviceAdapter        # Local microphone via sounddevice
├── FileAdapter               # Read from audio file
└── NullAdapter               # Testing (no-op)
```

**Null Adapters:** Every port has a "null" adapter for testing - it implements the interface but does nothing. This lets you test components in isolation.

### 3. Services (The Business Logic)

**Location:** `chatforge/services/`

Services contain the core logic that uses ports. They don't know *which* adapter is behind the port.

| Service | Purpose |
|---------|---------|
| `ReActAgent` | The reasoning agent (think → act → observe loop) |
| `LLM Factory` | Creates LLM instances for different providers |
| `TTS Service` | High-level text-to-speech orchestration |
| `Vision Analyzer` | Image analysis using vision models |

### 4. Middleware (The Safety Layer)

**Location:** `chatforge/middleware/`

Middleware intercepts data before/after processing to enforce security:

| Middleware | When | What |
|------------|------|------|
| `PIIDetector` | Before storage/send | Scans for emails, credit cards, SSNs, API keys |
| `PromptInjectionGuard` | Before agent | Detects manipulation attempts |
| `SafetyGuardrail` | After agent | Validates response safety |
| `ContentFilter` | Either | Keyword/pattern blocking |

### 5. Infrastructure (The Plumbing)

**Location:** `chatforge/infrastructure/`

Low-level building blocks used by adapters:

| Component | Purpose |
|-----------|---------|
| `WebSocketClient` | Async WebSocket with reconnection, heartbeat, backpressure |
| `ConnectionMetrics` | Track connection health and stats |
| `ExponentialBackoff` | Retry policies for reconnection |

### 6. Configuration (The Settings)

**Location:** `chatforge/config/`

Pydantic-based settings loaded from environment variables:

| Config | Controls |
|--------|----------|
| `llm_config` | Provider, model, temperature, API keys |
| `agent_config` | System prompt, timeouts |
| `storage_config` | Database path, TTL |
| `guardrails_config` | Enable/disable safety features |

Each has both a class (`LLMSettings`) and a singleton instance (`llm_config`).

---

## Data Flow Paths

### Flow 1: Text Chat Message

```
User Input
    │
    ▼
┌─────────────────────┐
│ Middleware Layer    │◄── PIIDetector scans input
│ (Pre-processing)    │◄── PromptInjectionGuard checks
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ ReActAgent          │
│  ┌───────────────┐  │
│  │ 1. THINK      │  │◄── LLM decides what to do
│  │ 2. ACT        │  │◄── Execute tools if needed
│  │ 3. OBSERVE    │  │◄── See results
│  │ 4. REPEAT     │  │◄── Until done
│  └───────────────┘  │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ Middleware Layer    │◄── SafetyGuardrail validates
│ (Post-processing)   │
└─────────────────────┘
    │
    ├──────────────────┐
    ▼                  ▼
Response          StoragePort
to User           (save to DB)
```

**Key points:**
- Agent uses `LLM Factory` to get the AI model
- Tools are executed via `BaseTool` subclasses
- Storage happens through `StoragePort` (SQLite, memory, etc.)

### Flow 2: Voice Conversation

```
Microphone                                          Speaker
    │                                                  ▲
    ▼                                                  │
┌──────────────────┐                      ┌──────────────────┐
│ AudioCapturePort │                      │AudioPlaybackPort │
│  (sounddevice)   │                      │  (sounddevice)   │
└──────────────────┘                      └──────────────────┘
    │                                                  ▲
    ▼                                                  │
┌──────────────────┐                      ┌──────────────────┐
│ VADPort          │                      │ Audio Chunks     │
│ (detect speech)  │                      │ from AI          │
└──────────────────┘                      └──────────────────┘
    │                                                  ▲
    ▼                                                  │
┌───────────────────────────────────────────────────────────────┐
│                    RealtimeVoiceAPIPort                       │
│                    (OpenAI Realtime API)                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│  │ send_audio()│───▶│  WebSocket  │◀───│  events()   │       │
│  └─────────────┘    │  Connection │    └─────────────┘       │
│                     └─────────────┘                          │
└───────────────────────────────────────────────────────────────┘
```

**Key points:**
- Bidirectional: capture and playback happen concurrently
- Server-side VAD: OpenAI detects when you start/stop speaking
- Barge-in: User can interrupt AI mid-sentence via `interrupt()`
- Events are streamed via async generator: `async for event in realtime.events()`

### Flow 3: Tool Execution

```
Agent decides to use a tool
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                        AsyncAwareTool                        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │   _run()    │───▶│  async      │◀───│   _arun()   │      │
│  │ (sync call) │    │  bridge     │    │ (async call)│      │
│  └─────────────┘    └─────────────┘    └─────────────┘      │
│                            │                                 │
│                            ▼                                 │
│                   _execute_async()                           │
│              (your tool implementation)                      │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
Tool interacts with external systems via Ports
(TicketingPort, KnowledgePort, etc.)
    │
    ▼
Result returned to Agent
```

**Key points:**
- Tools inherit from `AsyncAwareTool` - you only write `_execute_async()`
- The base class handles sync/async bridging automatically
- Tools can use any port to interact with external systems

---

## Top-Level Design Patterns

### 1. Dependency Injection

Components receive their dependencies, they don't create them:

```python
# ✅ Good - dependencies injected
agent = ReActAgent(
    tools=[search_tool, ticket_tool],
    messaging_port=slack_adapter,
    tracing=langfuse_adapter,
)

# ❌ Bad - hard-coded dependencies
class Agent:
    def __init__(self):
        self.storage = SQLiteStorage("./db.sqlite")  # Locked in!
```

This enables testing (inject mocks) and flexibility (swap implementations).

### 2. Async Context Managers

Resources that need setup/cleanup use async context managers:

```python
async with OpenAIRealtimeAdapter(api_key=key) as realtime:
    await realtime.connect(config)
    # ... use realtime ...
# Automatically disconnected and cleaned up
```

This pattern ensures resources are always properly released.

### 3. Event-Driven Streaming

Long-running operations emit events rather than returning all-at-once:

```python
# Voice events
async for event in realtime.events():
    match event.type:
        case VoiceEventType.AUDIO_CHUNK:
            await speaker.play(event.data)
        case VoiceEventType.TRANSCRIPT:
            print(f"AI said: {event.data}")

# Audio capture
async for chunk in audio.start_capture():
    await realtime.send_audio(chunk)
```

This enables real-time processing without buffering entire streams.

### 4. Configuration via Environment

All settings come from environment variables with sensible defaults:

```python
# In code
llm_config.provider      # "openai" (default) or from LLM_PROVIDER
llm_config.model_name    # from LLM_MODEL_NAME or default
llm_config.openai_api_key # from OPENAI_API_KEY

# Pydantic validates and provides type safety
class LLMSettings(BaseSettings):
    provider: str = "openai"
    model_name: str = "gpt-4o-mini"
```

No config files to manage, easy deployment.

### 5. Normalized Events

Different providers return different event formats. Adapters translate to normalized types:

```python
# OpenAI sends: {"type": "response.audio.delta", "delta": "base64..."}
# Adapter translates to:
VoiceEvent(
    type=VoiceEventType.AUDIO_CHUNK,
    data=decoded_bytes,
    metadata={"response_id": "..."},
)
```

Your code works with `VoiceEventType.AUDIO_CHUNK` regardless of provider.

### 6. Fail-Safe Middleware

Security middleware "fails open" rather than crashing:

```python
try:
    result = await guard.check_message(msg)
except Exception as e:
    # Don't block the user if check fails
    logger.error(f"Check failed: {e}")
    return InjectionCheckResult(is_injection=False, ...)
```

This prevents security components from becoming availability risks.

---

## Directory Map

```
chatforge/
├── __init__.py          # Public API exports
├── ports/               # Abstract interfaces (contracts)
│   ├── storage.py       # Conversation persistence
│   ├── realtime_voice.py # Voice AI
│   ├── audio_capture.py # Microphone input
│   └── ...
├── adapters/            # Concrete implementations
│   ├── storage/         # SQLite, in-memory
│   ├── realtime/        # OpenAI, mock
│   ├── audio_capture/   # sounddevice, file, null
│   └── ...
├── services/            # Business logic
│   ├── agent/           # ReActAgent
│   ├── llm/             # LLM factory
│   └── ...
├── middleware/          # Security layer
│   ├── pii.py           # PII detection
│   ├── injection.py     # Prompt injection guard
│   └── safety.py        # Content safety
├── config/              # Settings
│   ├── llm.py
│   ├── agent.py
│   └── ...
├── infrastructure/      # Low-level components
│   └── websocket/       # WebSocket client
└── utils/               # Helpers
    └── async_bridge.py  # Sync/async utilities
```

---

## Quick Reference: Adding New Components

### Adding a new Port:
1. Create `chatforge/ports/my_thing.py`
2. Define ABC with abstract methods
3. Export in `chatforge/ports/__init__.py`

### Adding a new Adapter:
1. Create `chatforge/adapters/my_thing/my_impl.py`
2. Implement the port interface
3. Export in `chatforge/adapters/__init__.py`

### Adding a new Tool:
1. Subclass `AsyncAwareTool`
2. Define `name`, `description`, `args_schema`
3. Implement `_execute_async()`

### Adding new Middleware:
1. Create `chatforge/middleware/my_check.py`
2. Follow pattern: input → check → result dataclass
3. Export in `chatforge/middleware/__init__.py`

---

## Summary

| Concept | What it does | Where to find it |
|---------|--------------|------------------|
| **Ports** | Define contracts (interfaces) | `chatforge/ports/` |
| **Adapters** | Implement ports for specific tech | `chatforge/adapters/` |
| **Services** | Business logic using ports | `chatforge/services/` |
| **Middleware** | Security interception | `chatforge/middleware/` |
| **Config** | Environment-based settings | `chatforge/config/` |
| **Infrastructure** | Low-level building blocks | `chatforge/infrastructure/` |

The architecture ensures:
- **Testability**: Inject mocks for any external system
- **Flexibility**: Swap providers without code changes
- **Clarity**: Clear boundaries between layers
- **Safety**: Security as a cross-cutting concern

When in doubt, remember: **the core domain never imports from adapters**.
