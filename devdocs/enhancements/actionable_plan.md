# Actionable Plan: Chatforge Voice Integration

*Porting realtimevoiceapi to Chatforge with stable intermediate forms.*

---

## Philosophy

**Stable Intermediate Form**: Every step produces a working, testable state. Never break what's running.

```
realtimevoiceapi (works)
    → Chatforge + mocks (works)
    → Chatforge + VoxStream (works)
    → ChatTerm (works)
    → VoxTerm (works)
```

---

## Current State

### What Exists and Works

| Component | Location | Status |
|-----------|----------|--------|
| **realtimevoiceapi** | `/Users/ns/Desktop/projects/realtimevoiceapi/` | Working voice client |
| **VoxStream** | `/Users/ns/Desktop/projects/voxstream/` | Working audio I/O |
| **Chatforge** | `/Users/ns/Desktop/chatbackend_new/chatforge/` | Working text agent |
| **VoiceEngine** | `/Users/ns/Desktop/projects/voiceai/voxengine/` | Working (uses VoxStream) |

### What We're Building

```
┌─────────────────────────────────────────────────────────────────┐
│                        TARGET STATE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   chatterm ─────┐                                               │
│   (text CLI)    │                                               │
│                 ▼                                               │
│            ┌─────────────────────────────────────────┐          │
│            │              chatforge                    │          │
│            │  ┌─────────────────────────────────┐    │          │
│            │  │ ReActAgent (text) │ VoiceAgent  │    │          │
│            │  └─────────────────────────────────┘    │          │
│            │  ┌─────────────────────────────────┐    │          │
│            │  │ MessagingPort │ AudioStreamPort │    │          │
│            │  │ StoragePort   │ RealtimeVoiceAPIPort    │    │          │
│            │  │ TicketingPort    │                 │    │          │
│            │  └─────────────────────────────────┘    │          │
│            └─────────────────────────────────────────┘          │
│                 ▲                  ▲                            │
│   voxterm ──────┘                  │                            │
│   (voice CLI)                      │                            │
│                              ┌─────┴─────┐                      │
│                              │ voxstream │                      │
│                              └───────────┘                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 0: Preparation (Day 1)

### 0.1 Audit realtimevoiceapi

**Goal**: Identify exactly what to port.

**Tasks**:
- [ ] List all files in `realtimevoiceapi/` with line counts
- [ ] Identify core abstractions to keep:
  - `WebSocketConnection` → internal utility
  - `MessageFactory` → OpenAI adapter internal
  - `ProviderCapabilities` → simplify for Chatforge
  - Event types → normalize to `VoiceEventType`
- [ ] Identify what to discard:
  - FastLane/BigLane split (use single balanced mode)
  - Complex EventBus (overkill)
  - StreamOrchestrator (future feature)

**Output**: `port_inventory.md` listing what goes where.

### 0.2 Set Up Development Environment

**Tasks**:
- [ ] Create feature branch in chatforge: `feature/voice-integration`
- [ ] Create feature branch in voxstream: `feature/chatforge-adapter`
- [ ] Set up test runners for both projects
- [ ] Verify realtimevoiceapi still runs (baseline)

**Validation**: Run existing realtimevoiceapi demo.

---

## Phase 1: Chatforge + Mock Audio (Days 2-4)

**Goal**: Add AudioStreamPort and RealtimeVoiceAPIPort with mock adapters. No real audio yet.

### 1.1 Create AudioStreamPort Interface

**File**: `chatforge/ports/audio_stream.py`

**Tasks**:
- [ ] Define `AudioStreamPort` abstract class
- [ ] Define methods:
  - `start_capture() -> AsyncGenerator[bytes, None]`
  - `stop_capture() -> None`
  - `play_chunk(chunk: bytes) -> None`
  - `stop_playback() -> None`
  - `set_vad_callbacks(on_start, on_end) -> None`
  - `get_input_level() -> float`
  - `is_playing() -> bool`
- [ ] Add to `chatforge/ports/__init__.py`

**Validation**: Import works, no runtime errors.

### 1.2 Create MockAudioStreamAdapter

**File**: `chatforge/adapters/audio/mock.py`

**Tasks**:
- [ ] Implement `MockAudioStreamAdapter(AudioStreamPort)`
- [ ] Support queuing fake audio chunks
- [ ] Support triggering fake VAD events
- [ ] Track all played audio for assertions

```python
class MockAudioStreamAdapter(AudioStreamPort):
    def queue_capture_chunk(self, chunk: bytes): ...
    def trigger_speech_start(self): ...
    def trigger_speech_end(self): ...
    def get_played_audio(self) -> list[bytes]: ...
```

**Validation**: Unit tests pass with mock.

### 1.3 Create RealtimeVoiceAPIPort Interface

**File**: `chatforge/ports/realtime.py`

**Tasks**:
- [ ] Define `VoiceEventType` enum
- [ ] Define `VoiceEvent` dataclass
- [ ] Define `VoiceSessionConfig` dataclass
- [ ] Define `ProviderCapabilities` dataclass
- [ ] Define `RealtimeVoiceAPIPort` abstract class with methods:
  - `connect(config) -> None`
  - `disconnect() -> None`
  - `send_audio(chunk) -> None`
  - `commit_audio() -> None`
  - `interrupt() -> None`
  - `send_tool_result(call_id, result) -> None`
  - `events() -> AsyncGenerator[VoiceEvent, None]`
  - `get_capabilities() -> ProviderCapabilities`

**Validation**: Import works, type hints correct.

### 1.4 Create MockRealtimeAdapter

**File**: `chatforge/adapters/realtime/mock.py`

**Tasks**:
- [ ] Implement `MockRealtimeAdapter(RealtimeVoiceAPIPort)`
- [ ] Support queuing fake events
- [ ] Support scripted conversations
- [ ] Track sent audio and tool results

```python
class MockRealtimeAdapter(RealtimeVoiceAPIPort):
    def queue_event(self, event: VoiceEvent): ...
    def queue_audio_response(self, audio: bytes): ...
    def queue_tool_call(self, name, args): ...
    def get_sent_audio(self) -> list[bytes]: ...
```

**Validation**: Unit tests pass with mock.

### 1.5 Create Basic VoiceAgent

**File**: `chatforge/agent/voice.py`

**Tasks**:
- [ ] Create `VoiceAgentConfig` dataclass
- [ ] Create `VoiceAgent` class
- [ ] Implement `start()` and `stop()`
- [ ] Implement capture → send audio loop
- [ ] Implement receive events → play audio loop
- [ ] Implement barge-in (interrupt on speech start)
- [ ] Wire VAD callbacks

**Validation**: Integration test with mocks:
```python
async def test_voice_agent_with_mocks():
    audio = MockAudioStreamAdapter()
    realtime = MockRealtimeAdapter()
    agent = VoiceAgent(audio, realtime)

    audio.queue_capture_chunk(b"hello")
    realtime.queue_audio_response(b"response")

    await agent.start()
    # Assert audio was sent, response was played
```

### 1.6 Phase 1 Milestone

**Deliverable**: Chatforge with working voice ports and mocks.

**Tests**:
- [ ] `test_audio_stream_port_interface.py`
- [ ] `test_realtime_port_interface.py`
- [ ] `test_voice_agent_with_mocks.py`
- [ ] `test_voice_agent_barge_in.py`
- [ ] `test_voice_agent_tool_calls.py`

**Validation Command**:
```bash
cd chatforge && pytest tests/voice/ -v
```

---

## Phase 2: OpenAI Realtime Adapter (Days 5-7)

**Goal**: Port realtimevoiceapi OpenAI client to Chatforge adapter.

### 2.1 Port WebSocket Utility

**Source**: `realtimevoiceapi/connections/websocket_connection.py`
**Target**: `chatforge/adapters/realtime/openai/websocket.py`

**Tasks**:
- [ ] Copy `WebSocketConnection` class
- [ ] Simplify: remove BigLane metrics, queue options
- [ ] Keep: connection state machine, reconnect logic
- [ ] Keep: ping/pong handling

**Validation**: Unit test WebSocket connect/send/receive.

### 2.2 Port Message Factory

**Source**: `realtimevoiceapi/core/message_protocol.py`
**Target**: `chatforge/adapters/realtime/openai/messages.py`

**Tasks**:
- [ ] Copy `MessageFactory` static methods
- [ ] Keep only methods we need:
  - `session_update()`
  - `input_audio_buffer_append()`
  - `input_audio_buffer_commit()`
  - `input_audio_buffer_clear()`
  - `response_create()`
  - `response_cancel()`
  - `conversation_item_create()` (for tool results)

**Validation**: Unit test message format matches OpenAI spec.

### 2.3 Create Event Translator

**File**: `chatforge/adapters/realtime/openai/translator.py`

**Tasks**:
- [ ] Create `OpenAIEventTranslator` class
- [ ] Map OpenAI events to `VoiceEventType`:
  - `response.audio.delta` → `AUDIO_CHUNK`
  - `response.text.delta` → `TEXT_CHUNK`
  - `input_audio_buffer.speech_started` → `SPEECH_STARTED`
  - `response.function_call_arguments.done` → `TOOL_CALL`
  - etc.
- [ ] Handle base64 decoding for audio

**Validation**: Unit test each event type translation.

### 2.4 Create OpenAI Realtime Adapter

**File**: `chatforge/adapters/realtime/openai/adapter.py`

**Tasks**:
- [ ] Create `OpenAIRealtimeAdapter(RealtimeVoiceAPIPort)`
- [ ] Implement `connect()` with session configuration
- [ ] Implement `send_audio()` with base64 encoding
- [ ] Implement `events()` generator with translation
- [ ] Implement `interrupt()` for barge-in
- [ ] Implement `send_tool_result()`
- [ ] Implement `get_capabilities()`

**Validation**: Integration test against OpenAI API:
```python
async def test_openai_adapter_real_api():
    adapter = OpenAIRealtimeAdapter(api_key=os.environ["OPENAI_API_KEY"])
    await adapter.connect(VoiceSessionConfig())

    # Send audio, receive events
    await adapter.send_audio(test_audio)
    async for event in adapter.events():
        if event.type == VoiceEventType.AUDIO_CHUNK:
            assert len(event.data) > 0
            break
```

### 2.5 Phase 2 Milestone

**Deliverable**: Chatforge can talk to OpenAI Realtime API.

**Tests**:
- [ ] `test_openai_websocket.py` (mocked)
- [ ] `test_openai_messages.py`
- [ ] `test_openai_translator.py`
- [ ] `test_openai_adapter_mocked.py`
- [ ] `test_openai_adapter_integration.py` (real API, optional)

**Validation Command**:
```bash
cd chatforge && pytest tests/adapters/realtime/ -v
# Integration test (requires API key):
cd chatforge && pytest tests/adapters/realtime/ -v -m integration
```

---

## Phase 3: VoxStream Adapter (Days 8-10)

**Goal**: Create VoxStream adapter for AudioStreamPort.

### 3.1 Create VoxStream Adapter

**File**: `chatforge/adapters/audio/voxstream.py`

**Tasks**:
- [ ] Create `VoxStreamAdapter(AudioStreamPort)`
- [ ] Initialize VoxStream with REALTIME mode
- [ ] Implement `start_capture()` wrapping `voxstream.capture_stream()`
- [ ] Implement `play_chunk()` wrapping `voxstream.play_audio()`
- [ ] Implement `stop_playback()` wrapping `voxstream.interrupt_playback()`
- [ ] Implement VAD callbacks wrapping `voxstream.set_vad_callbacks()`
- [ ] Implement `get_input_level()` and `is_playing()`

**Validation**: Manual test with real microphone.

### 3.2 Integration Test: VoiceAgent + VoxStream + Mock Realtime

**File**: `tests/integration/test_voice_agent_voxstream.py`

**Tasks**:
- [ ] Test VoiceAgent with real VoxStream, mock RealtimeVoiceAPIPort
- [ ] Verify audio capture works
- [ ] Verify audio playback works
- [ ] Verify VAD callbacks fire

**Validation**: Speak into mic, hear playback of queued audio.

### 3.3 Integration Test: Full Voice Loop

**File**: `tests/integration/test_full_voice_loop.py`

**Tasks**:
- [ ] Test VoiceAgent with real VoxStream + real OpenAI
- [ ] Speak "Hello", get audio response
- [ ] Test barge-in (interrupt while AI speaking)

**Validation**: Have a short conversation with AI.

### 3.4 Phase 3 Milestone

**Deliverable**: Chatforge with real audio I/O.

**Demo Script**:
```python
# demo_voice.py
import asyncio
from chatforge.agent.voice import VoiceAgent, VoiceAgentConfig
from chatforge.adapters.audio.voxstream import VoxStreamAdapter
from chatforge.adapters.realtime.openai import OpenAIRealtimeAdapter

async def main():
    agent = VoiceAgent(
        audio=VoxStreamAdapter(),
        realtime=OpenAIRealtimeAdapter(api_key="..."),
        config=VoiceAgentConfig(
            system_prompt="You are a helpful assistant.",
            voice="alloy",
        ),
    )

    print("Starting voice agent... Press Ctrl+C to stop.")
    await agent.start()

    # Run until interrupted
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await agent.stop()

asyncio.run(main())
```

**Validation Command**:
```bash
python demo_voice.py
# Speak, get response, test barge-in
```

---

## Phase 4: ChatTerm (Days 11-13)

**Goal**: Create text CLI for Chatforge.

### 4.1 Set Up ChatTerm Package

**Structure**:
```
chatterm/
├── pyproject.toml
├── chatterm/
│   ├── __init__.py
│   ├── __main__.py
│   ├── app.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── prompt.py
│   │   └── output.py
│   └── commands/
│       ├── __init__.py
│       └── handlers.py
└── tests/
```

**Tasks**:
- [ ] Create package structure
- [ ] Set up `pyproject.toml` with dependencies:
  - `chatforge`
  - `prompt-toolkit`
  - `rich`
  - `click`

### 4.2 Implement Core App

**File**: `chatterm/app.py`

**Tasks**:
- [ ] Create `ChatTermApp` class
- [ ] Implement REPL loop with prompt-toolkit
- [ ] Implement streaming output with rich
- [ ] Implement command history
- [ ] Implement `/help`, `/clear`, `/exit` commands

### 4.3 Implement CLI Entry Point

**File**: `chatterm/__main__.py`

**Tasks**:
- [ ] Create click CLI with options:
  - `--model` (default: gpt-4o)
  - `--system` (system prompt)
  - `--verbose` (debug output)
- [ ] Wire up Chatforge ReActAgent
- [ ] Start ChatTermApp

### 4.4 Phase 4 Milestone

**Deliverable**: Working text CLI.

**Validation Command**:
```bash
pip install -e ./chatterm
chatterm --model gpt-4o
# Type messages, get responses
```

---

## Phase 5: VoxTerm (Days 14-17)

**Goal**: Create voice CLI for Chatforge.

### 5.1 Set Up VoxTerm Package

**Structure**:
```
voxterm/
├── pyproject.toml
├── voxterm/
│   ├── __init__.py
│   ├── __main__.py
│   ├── app.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── display.py
│   │   └── meters.py
│   └── commands/
│       ├── __init__.py
│       └── handlers.py
└── tests/
```

**Tasks**:
- [ ] Create package structure
- [ ] Set up `pyproject.toml` with dependencies:
  - `chatforge`
  - `voxstream`
  - `rich`
  - `click`

### 5.2 Implement Voice Display

**File**: `voxterm/ui/display.py`

**Tasks**:
- [ ] Create live-updating terminal UI
- [ ] Show status: "Listening", "Processing", "Speaking"
- [ ] Show audio level meter
- [ ] Show transcript (user and assistant)

### 5.3 Implement Core App

**File**: `voxterm/app.py`

**Tasks**:
- [ ] Create `VoxTermApp` class
- [ ] Initialize VoiceAgent with VoxStream + OpenAI
- [ ] Subscribe to VoiceAgent events
- [ ] Update display on events
- [ ] Handle keyboard commands while voice runs

### 5.4 Implement CLI Entry Point

**File**: `voxterm/__main__.py`

**Tasks**:
- [ ] Create click CLI with options:
  - `--voice` (AI voice: alloy, echo, etc.)
  - `--system` (system prompt)
  - `--input-device` (microphone)
  - `--output-device` (speaker)
- [ ] Wire up VoiceAgent
- [ ] Start VoxTermApp

### 5.5 Implement Hybrid Mode

**Tasks**:
- [ ] Accept keyboard input alongside voice
- [ ] `/mute` - temporarily disable mic
- [ ] `/unmute` - re-enable mic
- [ ] `/text <message>` - send text instead of voice
- [ ] `/voice <name>` - change AI voice

### 5.6 Phase 5 Milestone

**Deliverable**: Working voice CLI.

**Validation Command**:
```bash
pip install -e ./voxterm
voxterm --voice alloy
# Speak, see transcript, hear response
```

---

## Phase 6: Tool Calling (Days 18-20)

**Goal**: Enable tool/function calling in VoiceAgent.

### 6.1 Wire TicketingPort to VoiceAgent

**Tasks**:
- [ ] Add `actions: TicketingPort` to VoiceAgent
- [ ] On `TOOL_CALL` event, execute via TicketingPort
- [ ] Send result back via `send_tool_result()`
- [ ] Wait for continued response

### 6.2 Add Tools to VoxTerm

**Tasks**:
- [ ] Add `--tools` option to VoxTerm CLI
- [ ] Support loading tools from config file
- [ ] Built-in tools: get_weather, search_web, etc.

### 6.3 Test Tool Calling

**Validation**:
```bash
voxterm --tools tools.yaml
# Say: "What's the weather in San Francisco?"
# Agent calls get_weather, speaks result
```

---

## Phase 7: Polish & Documentation (Days 21-25)

### 7.1 Error Handling

**Tasks**:
- [ ] Handle WebSocket disconnects gracefully
- [ ] Handle audio device errors
- [ ] Show user-friendly error messages
- [ ] Add retry logic where appropriate

### 7.2 Configuration

**Tasks**:
- [ ] Support config files (`~/.chatterm/config.yaml`)
- [ ] Support environment variables
- [ ] Support profiles (work, personal, etc.)

### 7.3 Documentation

**Tasks**:
- [ ] README for chatforge voice features
- [ ] README for chatterm
- [ ] README for voxterm
- [ ] Examples directory

### 7.4 Release Preparation

**Tasks**:
- [ ] Version bump all packages
- [ ] Update changelogs
- [ ] Test pip install from scratch
- [ ] Publish to PyPI (or private registry)

---

## Success Criteria

### Phase 1: Mocks Work
```bash
pytest chatforge/tests/voice/ -v  # All pass
```

### Phase 2: OpenAI Works
```bash
pytest chatforge/tests/adapters/realtime/ -v  # All pass
python -c "from chatforge.adapters.realtime.openai import OpenAIRealtimeAdapter"
```

### Phase 3: Real Audio Works
```bash
python demo_voice.py  # Can have conversation
```

### Phase 4: ChatTerm Works
```bash
chatterm  # Can chat via text
```

### Phase 5: VoxTerm Works
```bash
voxterm  # Can chat via voice
```

### Phase 6: Tools Work
```bash
voxterm --tools tools.yaml  # Can use tools via voice
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| OpenAI API changes | Pin API version, abstract in adapter |
| VoxStream bugs | VoiceEngine as fallback validator |
| Audio device issues | Good error messages, device selection |
| Latency problems | Profile each phase, optimize hot paths |
| Scope creep | Strict phase gates, MVP mindset |

---

## Timeline Summary

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| 0. Preparation | 1 day | Inventory, branches |
| 1. Mocks | 3 days | AudioStreamPort, RealtimeVoiceAPIPort, VoiceAgent with mocks |
| 2. OpenAI Adapter | 3 days | Working OpenAI Realtime integration |
| 3. VoxStream Adapter | 3 days | Real audio I/O |
| 4. ChatTerm | 3 days | Text CLI |
| 5. VoxTerm | 4 days | Voice CLI |
| 6. Tools | 3 days | Function calling |
| 7. Polish | 5 days | Error handling, docs, release |
| **Total** | **~25 days** | Full voice-enabled Chatforge ecosystem |

---

## Quick Start Commands

```bash
# Phase 0: Setup
git -C /Users/ns/Desktop/chatbackend_new/chatforge checkout -b feature/voice-integration
git -C /Users/ns/Desktop/projects/voxstream checkout -b feature/chatforge-adapter

# Phase 1: Test mocks
cd /Users/ns/Desktop/chatbackend_new/chatforge
pytest tests/voice/ -v

# Phase 3: Test real audio
python demo_voice.py

# Phase 4: Run ChatTerm
pip install -e ./chatterm && chatterm

# Phase 5: Run VoxTerm
pip install -e ./voxterm && voxterm
```

---

## Related Documents

| Document | Topic |
|----------|-------|
| `how_can_chatforge_should_implement_voice_connection.md` | RealtimeVoiceAPIPort design |
| `chatforge_voxstream_high_level.md` | AudioStreamPort design |
| `chatforge_should_implement.md` | Full enhancement list |
| `chatforge_and_voxterm.md` | CLI architecture |
| `what_is_missing_in_voxstream.md` | VoxStream gaps |
