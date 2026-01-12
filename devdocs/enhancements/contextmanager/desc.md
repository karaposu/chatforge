# LDCI (Layered Dynamic Context Injection)

## Overview

A modality-agnostic context management framework implementing 5-layer dynamic context injection for LLM conversations.

**Location:** `chatforge/services/context/`

**Problem Solved:** Managing context in real-time and streaming LLM applications requires coordination across different injection timings. HTTP requests inject all context at once, but S2S (Speech-to-Speech) sessions freeze context at session start. Applications need a unified way to manage context that works across both modalities.

**Solution:** A `ContextManager` library that manages layers, provides compilation, and supports injection timing metadata for S2S. The app controls when and how context is injected.

**Key Principle:** ContextManager is a **library** (you call it), not a framework (it calls you).

---

## The 5-Layer Model

### Layer Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                         LLM SESSION                                 │
│                                                                     │
│  INJECTION LAYERS                                                   │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐         │
│  │ L1     │ │ L2     │ │ L3     │ │ L4     │ │ L5       │         │
│  │ Base   │ │ State  │ │Override│ │ Derived│ │ Proactive│         │
│  └────────┘ └────────┘ └────────┘ └────────┘ └──────────┘         │
│                                                                     │
│  Timing: SESSION_START | TURN_START | ON-DEMAND | AFTER_RESPONSE | ASAP │
│                                                                     │
│  TOOL-BASED (Separate from LDCI - Port Concern)                    │
│  ┌─────────────────┐ ┌─────────────────┐                          │
│  │ Retrieval       │ │ Extraction      │                          │
│  │ AI asks → gets  │ │ AI learns → out │                          │
│  └─────────────────┘ └─────────────────┘                          │
└────────────────────────────────────────────────────────────────────┘
```

### Layer Definitions

| Layer | Name | Purpose | S2S Timing | HTTP |
|-------|------|---------|------------|------|
| 1 | **Base** | Stable foundation (character, rules) | SESSION_START (system_prompt) | get_base() |
| 2 | **State** | Per-turn dynamic context | TURN_START (add_text_item) | compile() |
| 3 | **Override** | Full context replacement | ON-DEMAND (session.update) | Replaces get_base() |
| 4 | **Derived** | Background-computed insights | AFTER_RESPONSE (add_text_item) | compile() |
| 5 | **Proactive** | App-triggered AI speech | ASAP (add_text_item + create_response) | N/A |

### What About Tools (Retrieval/Extraction)?

Tools are a **port concern**, not LDCI. They work alongside context injection:
- **Retrieval**: AI-initiated tool calls to fetch external data
- **Extraction**: AI-initiated tool calls to store learned information

These are configured on the port, not the ContextManager.

---

## Core Components

### 1. Layer (enum)

```python
class Layer(Enum):
    BASE = "base"           # L1: Stable foundation
    STATE = "state"         # L2: Per-turn dynamic state
    OVERRIDE = "override"   # L3: Full replacement
    DERIVED = "derived"     # L4: Background insights
    PROACTIVE = "proactive" # L5: App-triggered speech
```

### 2. InjectTiming (enum)

When a layer should be injected (for S2S):

```python
class InjectTiming(Enum):
    SESSION_START = "session_start"     # Once when session begins
    TURN_START = "turn_start"           # Before each user turn
    AFTER_RESPONSE = "after_response"   # After AI response completes
    SCHEDULED = "scheduled"             # Every N turns or N seconds
    ASAP = "asap"                       # Inject immediately
    ON_EVENT = "on_event"               # On specific external event
```

### 3. ContextLayer (dataclass)

Carries a piece of context with metadata:

```python
@dataclass
class ContextLayer:
    # Required
    layer: Layer              # BASE, STATE, OVERRIDE, DERIVED, PROACTIVE
    content: str              # The actual context string

    # Injection timing (for S2S)
    inject_at: InjectTiming = InjectTiming.TURN_START

    # Ordering (for multiple items in same timing)
    order: int = 0

    # Metadata (informational)
    authority: Authority = Authority.INFORMATIVE
    stability: Stability = Stability.TURN
    timestamp: float = field(default_factory=time.time)
    source: str = "app"
```

### 4. ContextManager (class)

Manages layers and provides compilation. **NO binding to ports.**

```python
class ContextManager:
    """
    Modality-agnostic context manager.

    This is a LIBRARY - you call it, it doesn't call you.
    Does NOT know about ports, events, or injection timing execution.
    """

    def add(self, layer: ContextLayer) -> None:
        """Add a context layer."""

    def get_base(self) -> Optional[str]:
        """Get L1 base context (or override if set)."""

    def compile(self, **options) -> str:
        """Compile ALL layers to string (for HTTP, timing ignored)."""

    def compile_for(self, timing: InjectTiming, **options) -> str:
        """Compile layers matching timing to string (for S2S convenience)."""

    def get_layers_for(self, timing: InjectTiming) -> List[ContextLayer]:
        """Get layer objects matching timing (for injectors/custom)."""

    def clear_state(self) -> None:
        """Clear L2 state layers."""

    def clear_derived(self) -> None:
        """Clear L4 derived layers."""

    def clear_proactive(self) -> None:
        """Clear L5 proactive layers."""

    def clear_override(self) -> None:
        """Clear L3 override."""
```

### 5. ContextInjector (optional, for S2S)

Separate component that handles injection. NOT part of ContextManager.

```python
class ContextInjector(Protocol):
    async def inject(self, layer: ContextLayer) -> None
    async def inject_all(self, layers: List[ContextLayer]) -> None
    async def inject_for(self, context: ContextManager, timing: InjectTiming) -> None

class RealtimeContextInjector:
    """Injector for RealtimeVoiceAPIPort."""

    def __init__(self, port: RealtimeVoiceAPIPort):
        self._port = port

    async def inject(self, layer: ContextLayer) -> None:
        await self._port.add_text_item(layer.content)

    async def inject_for(self, context: ContextManager, timing: InjectTiming) -> None:
        layers = context.get_layers_for(timing)
        for layer in layers:
            await self.inject(layer)
```

---

## Module Structure

```
chatforge/services/context/
├── __init__.py              # Public exports
├── manager.py               # ContextManager class
├── types.py                 # Layer, InjectTiming, ContextLayer, etc.
├── state.py                 # Internal state management
└── injectors/               # Port-aware injection helpers
    ├── __init__.py          # ContextInjector Protocol
    └── realtime.py          # RealtimeContextInjector
```

---

## Usage Examples

### HTTP (Text-to-Text)

```python
from chatforge.services.context import ContextManager, ContextLayer, Layer

context = ContextManager()

# Add layers
context.add(ContextLayer(layer=Layer.BASE, content=system_prompt))
context.add(ContextLayer(layer=Layer.STATE, content=room_context, order=10))
context.add(ContextLayer(layer=Layer.STATE, content=visual_context, order=20))

# Compile ALL layers (timing ignored for HTTP)
compiled = context.compile(audio_tags=True)

# App builds request
response = llm.invoke([
    SystemMessage(content=context.get_base()),
    *history,
    HumanMessage(content=compiled + "\n" + user_input)
])
```

### S2S Option A: compile_for() Convenience

```python
from chatforge.services.context import (
    ContextManager, ContextLayer, Layer, InjectTiming
)

context = ContextManager()

# L1: Base - session start
context.add(ContextLayer(
    layer=Layer.BASE,
    content=SILUET_PROFILE + GAME_RULES,
    inject_at=InjectTiming.SESSION_START
))

# L2: State - each turn
context.add(ContextLayer(
    layer=Layer.STATE,
    content=room_context,
    inject_at=InjectTiming.TURN_START,
    order=10
))

# Connect with L1
await port.connect(VoiceSessionConfig(
    system_prompt=context.get_base()
))

# Event loop - inject L2 at turn start
async for event in port.events():
    if event.type == "speech_started":
        text = context.compile_for(InjectTiming.TURN_START)
        if text:
            await port.add_text_item(text)

    if event.type == "response_done":
        text = context.compile_for(InjectTiming.AFTER_RESPONSE)
        if text:
            await port.add_text_item(text)
```

### S2S Option B: ContextInjector

```python
from chatforge.services.context.injectors import RealtimeContextInjector

context = ContextManager()
# ... add layers ...

injector = RealtimeContextInjector(port)

async for event in port.events():
    if event.type == "speech_started":
        await injector.inject_for(context, InjectTiming.TURN_START)
```

### S2S Option C: Manual with Layer Objects

```python
context = ContextManager()
# ... add layers ...

async for event in port.events():
    if event.type == "speech_started":
        for layer in context.get_layers_for(InjectTiming.TURN_START):
            # Custom handling per layer
            await port.add_text_item(layer.content)
```

### Proactive AI Speech (L5)

```python
# App decides to make AI speak
context.add(ContextLayer(
    layer=Layer.PROACTIVE,
    content="Meeting reminder: Your 3pm meeting starts in 5 minutes.",
    inject_at=InjectTiming.ASAP
))

# App triggers
await port.add_text_item(context.compile_for(InjectTiming.ASAP))
await port.create_response()

# Clean up
context.clear_proactive()
```

---

## Layer Selection Guide

```
Does your app need...                          Use Layer(s)
─────────────────────────────────────────────────────────────────
A character/persona/rules?                     → L1 (Base) ✓ Always
State that changes during conversation?        → L2 (State)
Testing specific scenarios / mode switch?      → L3 (Override)
Background ML/analytics insights?              → L4 (Derived)
AI should speak without user input?            → L5 (Proactive)
Too much context to pre-inject (RAG)?          → Tools (port concern)
Remember things across sessions?               → Tools (port concern)
```

---

## HTTP vs S2S Comparison

| Aspect | HTTP | S2S |
|--------|------|-----|
| Context timing | Per-request | Per-session (with updates) |
| Compilation | `compile()` → all layers | `compile_for(timing)` → filtered |
| Base context | `get_base()` → SystemMessage | `get_base()` → system_prompt at connect |
| History | App manages | Port manages (persistent connection) |
| Proactive | Not supported | `add_text_item()` + `create_response()` |

**Same ContextManager API. Different injection patterns.**

---

## Design Principles

### 1. ContextManager is Pure
- Stores layers
- Compiles to string
- Filters by timing

Does NOT:
- Know about ports
- Handle events
- Control injection timing

### 2. compile() Returns STRING

```python
compiled = context.compile()  # Returns string, not structured object
```

App decides what to do with the string.

### 3. Timing Lives on ContextLayer

Each layer knows WHEN it should be injected (for S2S):

```python
layer = ContextLayer(
    layer=Layer.STATE,
    content="room context",
    inject_at=InjectTiming.TURN_START,
    order=10
)
```

### 4. History is App's Job

ContextManager doesn't manage history. App handles it:
- HTTP: App provides history to LLM
- S2S: Port manages history via persistent connection

### 5. Proactive is App-Orchestrated

"Proactive" is always triggered by the app, never spontaneously by AI:

```python
# App decides to trigger proactive
await port.add_text_item(context.compile_for(InjectTiming.ASAP))
await port.create_response()
```

---

## Implementation Phases

### Phase 1: Core Types
- [ ] `types.py` - Layer, InjectTiming, Authority, Stability enums
- [ ] `types.py` - ContextLayer dataclass

### Phase 2: ContextManager
- [ ] `manager.py` - ContextManager class
- [ ] `add()`, `get_base()`, `compile()`
- [ ] `compile_for()`, `get_layers_for()`
- [ ] `clear_*()` methods

### Phase 3: Testing
- [ ] Unit tests for ContextManager
- [ ] Integration tests with mock port

### Phase 4: Optional Injector
- [ ] `injectors/realtime.py` - RealtimeContextInjector
- [ ] Protocol definition in `injectors/__init__.py`

---

## Open Questions (Resolved)

| Question | Resolution |
|----------|------------|
| ContextLayer generic or per-type? | Generic with `layer: Layer` enum |
| How does ContextManager know about events? | It doesn't. App controls timing. |
| Should compile() be on ContextManager? | Yes, returns string |
| Binding pattern? | No. App/injector handles injection. |
| History ownership? | App's responsibility |
| Proactive trigger? | App-orchestrated, AI never spontaneously decides |
| What about tools (Retrieval/Extraction)? | Port concern, not LDCI layers |
