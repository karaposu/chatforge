# LDCI ContextManager - Step-by-Step Implementation Guide

## Overview

This document provides a complete implementation roadmap for the **Layered Dynamic Context Injection (LDCI)** system in Chatforge, based on design decisions from `ldci_generic.md` and resolutions from `high_level_issues.md`.

---

## Part 1: Design Foundation

### 1.1 What LDCI Is (and Isn't)

**LDCI IS:**
- Context injection framework
- Modality-agnostic (HTTP, WebSocket, S2S)
- Layer-based organization (5 layers)
- Compile-time assembly for HTTP
- Event-driven injection for persistent connections

**LDCI IS NOT:**
- Conversation state manager (history is app's job)
- Storage system
- LLM abstraction
- User input handler (for realtime modalities)

### 1.2 The 5 Layers

| Layer | Name | Purpose | Stability | Authority |
|-------|------|---------|-----------|-----------|
| L1 | Base | AI identity, rules | Static | Directive |
| L2 | State | Current situation | Per-turn | Informative |
| L3 | Override | Full context replacement | On-demand | Directive |
| L4 | Derived | Background insights | Async | Suggestive |
| L5 | Proactive | App-orchestrated AI initiative | Event-driven | Varies |

### 1.3 Key Design Decisions

| Decision | Outcome |
|----------|---------|
| `compile()` returns | STRING (not structured object) |
| `compile()` for HTTP | Returns ALL layers as string (timing ignored) |
| `compile_for(timing)` for S2S | Returns matching layers as string (convenience) |
| `get_layers_for(timing)` for S2S | Returns matching ContextLayer objects (for injectors) |
| L1 in compile() | No - accessed via `get_base()` separately |
| History ownership | App's responsibility |
| Proactive triggers | App-orchestrated, AI never spontaneously decides |
| Authority | Design-time organization, not runtime |
| Order control | Via `order` parameter when adding context |
| Injection timing | Via `inject_at` parameter on ContextLayer |
| Compile-time flags | Supported (e.g., `audio_tags=True`) |

---

## Part 2: Architecture

### 2.1 Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Application                              │
│                                                                  │
│  # Create layers as first-class objects                          │
│  base = ContextLayer(layer=Layer.BASE, content=system_prompt)    │
│  room = ContextLayer(layer=Layer.STATE, content=room_ctx, order=10)│
│  visual = ContextLayer(layer=Layer.STATE, content=vis_ctx, order=20)│
│                                                                  │
│  # Add to context manager                                        │
│  context = ContextManager()                                      │
│  context.add(base)                                               │
│  context.add(room)                                               │
│  context.add(visual)                                             │
│                                                                  │
│  # HTTP: compile and use                                         │
│  compiled = context.compile(audio_tags=True)                     │
│  final_prompt = f"{compiled}\n\nRespond in {language}"          │
│                                                                  │
│  # Persistent: app handles injection timing                      │
│  await port.add_text_item(context.compile())                     │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │   HTTP   │   │ WebSocket│   │   S2S    │
        │  (no     │   │  (events │   │  (events │
        │  binding)│   │  + inject│   │  + inject│
        └──────────┘   └──────────┘   └──────────┘
```

### 2.2 File Structure

```
chatforge/services/context/
├── __init__.py           # Public API exports (ContextManager, ContextLayer, Layer, etc.)
├── types.py              # Core types (Layer, Authority, Stability, InjectTiming, CompileOptions)
├── layer.py              # ContextLayer dataclass
├── manager.py            # ContextManager (main orchestrator)
├── compiler.py           # Compilation logic (compile() implementation)
└── injectors/            # Port-aware injection helpers
    ├── __init__.py       # ContextInjector Protocol
    └── realtime.py       # RealtimeContextInjector for S2S
```

**Design is intentionally minimal:**
- Core: ContextManager, ContextLayer, types (always needed)
- Optional: ContextInjector (only for S2S when you want layer-level control)
- No bindings needed (app/injector handles port interaction)
- State is just lists in ContextManager (no separate state class)

---

## Part 3: Type Definitions

### 3.1 Core Enums

```python
# types.py

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

class Layer(Enum):
    """The 5 context layers."""
    BASE = "base"           # L1
    STATE = "state"         # L2
    OVERRIDE = "override"   # L3
    DERIVED = "derived"     # L4
    PROACTIVE = "proactive" # L5


class Authority(Enum):
    """How the AI should treat this context (design-time)."""
    DIRECTIVE = "directive"       # Must follow
    INFORMATIVE = "informative"   # Should consider
    SUGGESTIVE = "suggestive"     # May incorporate


class Stability(Enum):
    """How often context changes (informational)."""
    STATIC = "static"             # Never changes
    SESSION = "session"           # Once per session
    TURN = "turn"                 # Every turn
    EVENT = "event"               # On external event


class InjectTiming(Enum):
    """
    WHEN a layer should be injected (for S2S/persistent connections).

    HTTP ignores this - compile() returns all layers.
    S2S uses compile_for(timing) to get layers for specific moments.
    """
    SESSION_START = "session_start"     # Once when session begins
    TURN_START = "turn_start"           # Before each user turn (SPEECH_STARTED)
    AFTER_RESPONSE = "after_response"   # After AI response completes (RESPONSE_DONE)
    SCHEDULED = "scheduled"             # Every N turns or N seconds
    ASAP = "asap"                       # Inject as soon as possible
    ON_EVENT = "on_event"               # On specific external event
```

### 3.2 ContextLayer

ContextLayer is a first-class object created before adding to ContextManager. This allows:
- Reuse and storage of layers
- Clear metadata in one place
- Type safety and validation
- Easy testing (create, inspect, then add)

```python
# layer.py

from dataclasses import dataclass, field
from typing import Optional
import time

@dataclass
class ContextLayer:
    """A piece of context with metadata."""

    # Required
    layer: Layer              # Which layer (STATE, DERIVED, etc.)
    content: str              # The actual context string

    # Injection timing (for S2S - when should this layer be injected?)
    inject_at: InjectTiming = InjectTiming.TURN_START

    # Ordering (for multiple items in same timing/layer)
    order: int = 0

    # Metadata (informational, not runtime)
    authority: Authority = Authority.INFORMATIVE
    stability: Stability = Stability.TURN

    # Tracking
    timestamp: float = field(default_factory=time.time)
    source: str = "app"

    def render(self, options: "CompileOptions") -> str:
        """Render content, potentially modified by compile options."""
        # Subclasses or custom layers can override
        return self.content


# Usage: Create layer with timing info
room_layer = ContextLayer(
    layer=Layer.STATE,
    content=room_context,
    inject_at=InjectTiming.TURN_START,  # Inject when user starts speaking
    order=10
)
context.add(room_layer)

# Derived insight - inject after AI responds
insight_layer = ContextLayer(
    layer=Layer.DERIVED,
    content=user_insight,
    inject_at=InjectTiming.AFTER_RESPONSE,
)
context.add(insight_layer)
```

### 3.3 CompileOptions

```python
# types.py (continued)

@dataclass
class CompileOptions:
    """Options passed to compile() that affect layer rendering."""

    # Feature flags that layers can react to
    audio_tags: bool = False
    verbose: bool = True

    # Custom flags (extensible)
    custom: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get custom flag value."""
        return self.custom.get(key, default)
```

### 3.4 Configuration

```python
# types.py (continued)

@dataclass
class ContextConfig:
    """Configuration for ContextManager."""

    # Layer enablement
    state_enabled: bool = True
    override_enabled: bool = True
    derived_enabled: bool = False
    proactive_enabled: bool = False

    # Derived layer settings
    derived_max_queue: int = 10

    # Proactive settings
    proactive_conflict: str = "queue"  # queue, drop, interrupt

    # Optional providers
    history_provider: Optional[Callable[[], List[Any]]] = None
```

---

## Part 4: ContextManager Implementation

### 4.1 Core Class

```python
# manager.py

from typing import Dict, List, Optional, AsyncIterator, Any
from dataclasses import dataclass, field
import asyncio

from .types import Layer, CompileOptions, ContextConfig
from .layer import ContextLayer
from .compiler import compile_layers

class ContextManager:
    """
    Orchestrates layered context injection.

    Usage:
        # Create layers
        base = ContextLayer(layer=Layer.BASE, content="You are...")
        room = ContextLayer(layer=Layer.STATE, content=room_ctx, order=10)

        # Add to manager
        context = ContextManager()
        context.add(base)
        context.add(room)

        # Compile (returns L2-L5, not L1)
        compiled = context.compile(audio_tags=True)

        # Access L1 separately
        system_prompt = context.get_base()
    """

    def __init__(self, config: Optional[ContextConfig] = None):
        self._config = config or ContextConfig()

        # L1: Base (single layer)
        self._base: Optional[ContextLayer] = None

        # L2: State (multiple, ordered)
        self._state: List[ContextLayer] = []

        # L3: Override (replaces base when set)
        self._override: Optional[ContextLayer] = None

        # L4: Derived (multiple, ordered)
        self._derived: List[ContextLayer] = []

        # L5: Proactive (multiple, ordered)
        self._proactive: List[ContextLayer] = []

    # ─────────────────────────────────────────────────────────────
    # Core: Add Layer
    # ─────────────────────────────────────────────────────────────

    def add(self, layer: ContextLayer) -> None:
        """Add a context layer."""
        if layer.layer == Layer.BASE:
            self._base = layer
        elif layer.layer == Layer.STATE:
            self._state.append(layer)
        elif layer.layer == Layer.OVERRIDE:
            self._override = layer
        elif layer.layer == Layer.DERIVED:
            self._derived.append(layer)
        elif layer.layer == Layer.PROACTIVE:
            self._proactive.append(layer)

    # ─────────────────────────────────────────────────────────────
    # L1: Base Context
    # ─────────────────────────────────────────────────────────────

    def get_base(self) -> Optional[str]:
        """
        Get L1 base context for session initialization.
        Returns override content if set, otherwise base content.
        """
        if self._override:
            return self._override.content
        return self._base.content if self._base else None

    # ─────────────────────────────────────────────────────────────
    # Layer Management
    # ─────────────────────────────────────────────────────────────

    def clear_state(self) -> None:
        """Clear all L2 state context (for new turn)."""
        self._state.clear()

    def clear_override(self) -> None:
        """Clear L3 override (restore base)."""
        self._override = None

    def clear_derived(self) -> None:
        """Clear L4 derived context."""
        self._derived.clear()

    def clear_proactive(self) -> None:
        """Clear L5 proactive context."""
        self._proactive.clear()

    # ─────────────────────────────────────────────────────────────
    # Compilation
    # ─────────────────────────────────────────────────────────────

    def compile(self, **options) -> str:
        """
        Compile ALL layers (L2-L5) into a single string.

        Used for HTTP where timing doesn't matter - all context
        is assembled before the request.

        L1 is NOT included - access via get_base() separately.

        Args:
            **options: Compile-time flags (audio_tags, verbose, etc.)

        Returns:
            Compiled context string (L2 + L4 + L5, ordered)
        """
        compile_opts = CompileOptions(**options)

        # Collect all layers to compile (NOT L1, NOT L3)
        layers: List[ContextLayer] = []

        # L2: State
        layers.extend(self._state)

        # L4: Derived
        layers.extend(self._derived)

        # L5: Proactive
        layers.extend(self._proactive)

        # Sort by order
        layers.sort(key=lambda x: x.order)

        # Render each layer
        parts = [layer.render(compile_opts) for layer in layers]

        return "\n\n".join(parts)

    def get_layers_for(self, timing: InjectTiming) -> List[ContextLayer]:
        """
        Get layer objects matching the specified timing.

        Use this when you want to work with layer objects directly,
        e.g., with a ContextInjector or custom injection logic.

        Args:
            timing: Which injection timing to filter for

        Returns:
            List of ContextLayer objects matching timing, sorted by order

        Example:
            layers = context.get_layers_for(InjectTiming.TURN_START)
            for layer in layers:
                await injector.inject(layer)
        """
        layers: List[ContextLayer] = []

        for layer in self._state:
            if layer.inject_at == timing:
                layers.append(layer)

        for layer in self._derived:
            if layer.inject_at == timing:
                layers.append(layer)

        for layer in self._proactive:
            if layer.inject_at == timing:
                layers.append(layer)

        layers.sort(key=lambda x: x.order)
        return layers

    def compile_for(self, timing: InjectTiming, **options) -> str:
        """
        Compile only layers matching the specified timing.

        Convenience method that calls get_layers_for() and compiles to string.
        Use get_layers_for() if you need the layer objects directly.

        Args:
            timing: Which injection timing to filter for
            **options: Compile-time flags (audio_tags, verbose, etc.)

        Returns:
            Compiled context string for layers matching timing

        Example:
            # On SPEECH_STARTED event
            text = context.compile_for(InjectTiming.TURN_START)
            await port.add_text_item(text)

            # On RESPONSE_DONE event
            text = context.compile_for(InjectTiming.AFTER_RESPONSE)
            if text:
                await port.add_text_item(text)
        """
        compile_opts = CompileOptions(**options)
        layers = self.get_layers_for(timing)
        parts = [layer.render(compile_opts) for layer in layers]
        return "\n\n".join(parts)
```

### 4.2 No Port Binding Needed

ContextManager stays pure - it manages layers and provides compilation. The app (or injector) handles actual injection.

**HTTP Pattern:**
```python
# HTTP: compile() returns ALL layers (timing ignored)
compiled = context.compile(audio_tags=True)
system_prompt = context.get_base()

response = llm.invoke([
    SystemMessage(content=system_prompt),
    *history,
    HumanMessage(content=compiled + "\n" + user_input)
])
```

**S2S Patterns (three options):**

```python
# Option A: compile_for() - convenience, returns string
async for event in port.events():
    if event.type == "speech_started":
        text = context.compile_for(InjectTiming.TURN_START)
        if text:
            await port.add_text_item(text)

# Option B: ContextInjector - handles injection with layer objects
injector = RealtimeContextInjector(port)
async for event in port.events():
    if event.type == "speech_started":
        await injector.inject_for(context, InjectTiming.TURN_START)

# Option C: get_layers_for() - full control with layer objects
async for event in port.events():
    if event.type == "speech_started":
        layers = context.get_layers_for(InjectTiming.TURN_START)
        for layer in layers:
            # Custom formatting, logging, error handling per layer
            await port.add_text_item(f"[{layer.layer.name}] {layer.content}")
```

**Why no bind pattern?**
- Keeps ContextManager simple (just manages layers)
- App/injector controls injection explicitly
- Same ContextManager for all modalities
- Easier to test and reason about
- Flexibility: use strings OR layer objects

**HTTP vs S2S:**

| Modality | Method | Returns |
|----------|--------|---------|
| HTTP | `compile()` | String (all layers) |
| S2S | `compile_for(timing)` | String (filtered) |
| S2S | `get_layers_for(timing)` | List[ContextLayer] (for injectors) |

### 4.3 Optional: ContextInjector

For S2S, you can optionally use a `ContextInjector` that works with layer objects directly:

```python
# chatforge/services/context/injectors/realtime.py

class ContextInjector(Protocol):
    """Protocol for injecting context layers into a port."""

    async def inject(self, layer: ContextLayer) -> None:
        """Inject a single layer."""
        ...

    async def inject_all(self, layers: List[ContextLayer]) -> None:
        """Inject multiple layers."""
        ...

    async def inject_for(self, context: ContextManager, timing: InjectTiming) -> None:
        """Inject all layers matching timing from context manager."""
        ...


class RealtimeContextInjector:
    """Inject context into RealtimeVoiceAPIPort."""

    def __init__(self, port: RealtimeVoiceAPIPort):
        self._port = port

    async def inject(self, layer: ContextLayer) -> None:
        """Inject a single layer as text item."""
        await self._port.add_text_item(layer.content)

    async def inject_all(self, layers: List[ContextLayer]) -> None:
        """Inject multiple layers."""
        for layer in layers:
            await self.inject(layer)

    async def inject_for(self, context: ContextManager, timing: InjectTiming) -> None:
        """Inject all layers matching timing."""
        layers = context.get_layers_for(timing)
        await self.inject_all(layers)
```

**When to use ContextInjector:**
- You want per-layer error handling
- You want custom formatting per layer type
- You want logging/observability per layer
- You're building a reusable injection pattern

**When to use compile_for() directly:**
- Simple cases where string output is enough
- You don't need per-layer control

---

## Part 5: Usage Patterns

### 5.1 HTTP Usage (ChamberProtocol style)

```python
from chatforge.services.context import ContextManager, ContextLayer, Layer

# At request entry point
def handle_request(request: SiluetRequest):
    context = ContextManager()

    # L1: Base (static identity)
    base = ContextLayer(
        layer=Layer.BASE,
        content=GAME_CONTEXT + SILUET_PROFILE
    )
    context.add(base)

    # L2: State (current situation)
    room = ContextLayer(
        layer=Layer.STATE,
        content=request.room_context,
        order=10
    )
    visual = ContextLayer(
        layer=Layer.STATE,
        content=request.visual_context,
        order=20
    )
    response_params = ContextLayer(
        layer=Layer.STATE,
        content=request.ai_character_response_parameters,
        order=30
    )
    context.add(room)
    context.add(visual)
    context.add(response_params)

    # L5: Proactive (if this is proactive trigger)
    if request.proactive_dialog:
        proactive = ContextLayer(
            layer=Layer.PROACTIVE,
            content=request.proactive_dialog
        )
        context.add(proactive)

    # Compile L2-L5
    compiled = context.compile(audio_tags=request.enable_audio_tags)

    # App builds final request
    system_prompt = context.get_base()  # L1
    history = fetch_history(chat_id)     # App's job

    # Mechanical instruction (not LDCI)
    final_prompt = f"{compiled}\n\nRespond in {request.language}."

    # Call LLM
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        *history,
        HumanMessage(content=final_prompt + "\n" + request.player_input)
    ])

    return response
```

### 5.2 S2S Voice Usage

```python
from chatforge.services.context import (
    ContextManager, ContextLayer, Layer, InjectTiming, ContextConfig
)

async def voice_session(port: RealtimeVoiceAPIPort):
    # Create context manager
    context = ContextManager(ContextConfig(
        derived_enabled=True,
        proactive_enabled=True,
    ))

    # L1: Base - inject at session start
    base = ContextLayer(
        layer=Layer.BASE,
        content="You are a helpful voice assistant.",
        inject_at=InjectTiming.SESSION_START
    )
    context.add(base)

    # L2: State - inject at turn start
    room_state = ContextLayer(
        layer=Layer.STATE,
        content=get_room_context(),
        inject_at=InjectTiming.TURN_START,
        order=10
    )
    context.add(room_state)

    # Connect port with L1
    await port.connect(VoiceSessionConfig(
        system_prompt=context.get_base(),
    ))

    # Background task for L4 derived (inject after response)
    async def profile_analyzer():
        while True:
            await asyncio.sleep(30)
            insight = analyze_conversation(port.get_history())
            derived = ContextLayer(
                layer=Layer.DERIVED,
                content=insight,
                inject_at=InjectTiming.AFTER_RESPONSE  # Inject after AI finishes
            )
            context.add(derived)

    asyncio.create_task(profile_analyzer())

    # App handles event loop - uses compile_for() with timing
    async for event in port.events():
        if event.type == "speech_started":
            # Inject only TURN_START layers
            text = context.compile_for(InjectTiming.TURN_START)
            if text:
                await port.add_text_item(text)

        if event.type == "response_done":
            # Inject only AFTER_RESPONSE layers (derived insights)
            text = context.compile_for(InjectTiming.AFTER_RESPONSE)
            if text:
                await port.add_text_item(text)
            # Clear derived after injection
            context.clear_derived()

        if event.type == "user_location_changed":
            # Update L2 state dynamically
            context.clear_state()
            location = ContextLayer(
                layer=Layer.STATE,
                content=f"User is now at {event.location}",
                inject_at=InjectTiming.TURN_START
            )
            context.add(location)

        # Handle tool calls, etc.
        ...
```

### 5.3 Proactive Trigger (S2S)

```python
# External event triggers proactive
async def on_meeting_reminder(meeting: Meeting):
    # L5: Add proactive context with ASAP timing
    proactive = ContextLayer(
        layer=Layer.PROACTIVE,
        content=f"User has a meeting starting in 5 minutes: {meeting.title}",
        inject_at=InjectTiming.ASAP  # Inject immediately
    )
    context.add(proactive)

    # App triggers response (not LDCI's job)
    # For proactive, we use compile_for(ASAP) or just compile() the proactive layer
    text = context.compile_for(InjectTiming.ASAP)
    await port.add_text_item(text)
    await port.create_response()

    # Clear proactive after use
    context.clear_proactive()
```

### 5.4 Convenience Helpers (Optional)

Apps can create factory functions to reduce boilerplate:

```python
# App-level helper functions with timing defaults
def state(content: str, order: int = 0) -> ContextLayer:
    return ContextLayer(
        layer=Layer.STATE,
        content=content,
        inject_at=InjectTiming.TURN_START,
        order=order
    )

def derived(content: str) -> ContextLayer:
    return ContextLayer(
        layer=Layer.DERIVED,
        content=content,
        inject_at=InjectTiming.AFTER_RESPONSE
    )

def proactive(content: str) -> ContextLayer:
    return ContextLayer(
        layer=Layer.PROACTIVE,
        content=content,
        inject_at=InjectTiming.ASAP
    )

# Usage becomes more concise
context.add(state(room_context, order=10))
context.add(state(visual_context, order=20))
context.add(derived(user_insight))
```

These helpers are **app's responsibility**, not part of core LDCI - keeps the core simple while allowing apps to add ergonomics as needed.

---

## Part 6: Migration from Current Implementation

### 6.1 Changes from 7-Layer to 5-Layer

| Old (7 layers) | New (5 layers) | Notes |
|----------------|----------------|-------|
| L1 Base | L1 Base | Same |
| L2 Dynamic | L2 State | Renamed |
| L3 Override | L3 Override | Same |
| L4 Derived | L4 Derived | Same |
| L5 Retrieval | *Removed* | Tools are port concern |
| L6 Extraction | *Removed* | Tools are port concern |
| L7 Proactive | L5 Proactive | Renumbered |

### 6.2 API Changes

| Old | New | Reason |
|-----|-----|--------|
| `set_dynamic_provider()` | `context.add(ContextLayer(layer=Layer.STATE, ...))` | Explicit layer objects |
| `set_base(content)` | `context.add(ContextLayer(layer=Layer.BASE, content=...))` | Consistent pattern |
| `compile()` returns structured | `compile()` returns STRING | Simplicity |
| `LayerConfig.retrieval_tools` | *Removed* | Tools on port |
| N/A | `compile(audio_tags=True)` | Compile-time flags |
| N/A | `compile_for(InjectTiming.TURN_START)` | Timing-based compilation for S2S (string) |
| N/A | `get_layers_for(InjectTiming.TURN_START)` | Get layer objects for S2S (for injectors) |
| N/A | `context.get_base()` | L1 not in compile() |
| N/A | `ContextLayer.inject_at` | When to inject (for S2S) |
| N/A | `InjectTiming` enum | SESSION_START, TURN_START, AFTER_RESPONSE, etc. |
| N/A | `ContextInjector` (optional) | Layer-level injection for S2S |

### 6.3 Migration Steps

1. Create `types.py` - Define Layer, Authority, Stability, InjectTiming, CompileOptions
2. Create `layer.py` - Define ContextLayer dataclass with inject_at field
3. Create `manager.py` - Implement ContextManager with add(), get_base(), compile(), compile_for()
4. Create `compiler.py` - Implement compile logic (filter by timing, sort by order, render, join)
5. Update `__init__.py` - Export public API (ContextManager, ContextLayer, Layer, InjectTiming, etc.)
6. Update existing usage - Migrate to ContextLayer-first pattern with timing
7. Update tests - Use new API with explicit layer objects and timing

---

## Part 7: Open Questions (Defer)

### 7.1 L6 Emphasis Layer?

For static content that needs body placement (like `response_constraints`).

**Decision:** Defer. Use L2 State for now. Revisit if pattern becomes common.

### 7.2 Conversation Awareness?

Should LDCI have read access to history via provider?

**Decision:** Defer. Keep pure for now. Add `history_provider` in v2 if needed.

### 7.3 Output Instructions?

Should compile() accept language/format options?

**Decision:** No. Mechanical instructions are app's job (append after compile).

---

## Part 8: Testing Strategy

### 8.1 Unit Tests

```python
from chatforge.services.context import ContextManager, ContextLayer, Layer, InjectTiming

def test_compile_returns_all_layers():
    """compile() returns ALL layers regardless of inject_at (for HTTP)."""
    context = ContextManager()

    context.add(ContextLayer(
        layer=Layer.STATE,
        content="turn_start_content",
        inject_at=InjectTiming.TURN_START
    ))
    context.add(ContextLayer(
        layer=Layer.DERIVED,
        content="after_response_content",
        inject_at=InjectTiming.AFTER_RESPONSE
    ))

    result = context.compile()

    # Both included regardless of timing
    assert "turn_start_content" in result
    assert "after_response_content" in result

def test_compile_for_filters_by_timing():
    """compile_for() returns only layers matching timing (for S2S)."""
    context = ContextManager()

    context.add(ContextLayer(
        layer=Layer.STATE,
        content="turn_start_content",
        inject_at=InjectTiming.TURN_START
    ))
    context.add(ContextLayer(
        layer=Layer.DERIVED,
        content="after_response_content",
        inject_at=InjectTiming.AFTER_RESPONSE
    ))

    # Only TURN_START
    turn_start = context.compile_for(InjectTiming.TURN_START)
    assert "turn_start_content" in turn_start
    assert "after_response_content" not in turn_start

    # Only AFTER_RESPONSE
    after_response = context.compile_for(InjectTiming.AFTER_RESPONSE)
    assert "after_response_content" in after_response
    assert "turn_start_content" not in after_response

def test_compile_respects_order():
    context = ContextManager()

    state1 = ContextLayer(layer=Layer.STATE, content="state1", order=10)
    state2 = ContextLayer(layer=Layer.STATE, content="state2", order=5)

    context.add(state1)
    context.add(state2)

    result = context.compile()

    assert result.index("state2") < result.index("state1")  # order=5 comes first

def test_get_base_returns_override_when_set():
    context = ContextManager()

    base = ContextLayer(layer=Layer.BASE, content="original")
    override = ContextLayer(layer=Layer.OVERRIDE, content="override")

    context.add(base)
    context.add(override)

    assert context.get_base() == "override"

def test_compile_excludes_base():
    context = ContextManager()

    context.add(ContextLayer(layer=Layer.BASE, content="base"))
    context.add(ContextLayer(layer=Layer.STATE, content="state"))

    result = context.compile()

    assert "base" not in result
    assert "state" in result

def test_compile_for_returns_empty_when_no_match():
    context = ContextManager()

    context.add(ContextLayer(
        layer=Layer.STATE,
        content="turn_start_only",
        inject_at=InjectTiming.TURN_START
    ))

    # No AFTER_RESPONSE layers
    result = context.compile_for(InjectTiming.AFTER_RESPONSE)

    assert result == ""

def test_get_layers_for_returns_layer_objects():
    """get_layers_for() returns ContextLayer objects for injectors."""
    context = ContextManager()

    context.add(ContextLayer(
        layer=Layer.STATE,
        content="state1",
        inject_at=InjectTiming.TURN_START,
        order=10
    ))
    context.add(ContextLayer(
        layer=Layer.DERIVED,
        content="derived1",
        inject_at=InjectTiming.TURN_START,
        order=5
    ))
    context.add(ContextLayer(
        layer=Layer.DERIVED,
        content="after_response",
        inject_at=InjectTiming.AFTER_RESPONSE
    ))

    # Get TURN_START layers
    layers = context.get_layers_for(InjectTiming.TURN_START)

    assert len(layers) == 2
    assert all(isinstance(l, ContextLayer) for l in layers)
    assert layers[0].content == "derived1"  # order=5 first
    assert layers[1].content == "state1"    # order=10 second

    # Get AFTER_RESPONSE layers
    after_layers = context.get_layers_for(InjectTiming.AFTER_RESPONSE)
    assert len(after_layers) == 1
    assert after_layers[0].content == "after_response"

def test_clear_state_removes_only_state_layers():
    context = ContextManager()

    context.add(ContextLayer(layer=Layer.BASE, content="base"))
    context.add(ContextLayer(layer=Layer.STATE, content="state"))
    context.add(ContextLayer(layer=Layer.DERIVED, content="derived"))

    context.clear_state()

    result = context.compile()
    assert "state" not in result
    assert "derived" in result
    assert context.get_base() == "base"
```

### 8.2 Integration Tests

```python
async def test_s2s_timing_based_injection():
    """Test timing-based injection pattern for S2S."""
    port = MockRealtimePort()
    context = ContextManager()

    # L1: Base (session start)
    context.add(ContextLayer(
        layer=Layer.BASE,
        content="base prompt",
        inject_at=InjectTiming.SESSION_START
    ))

    # L2: State (turn start)
    context.add(ContextLayer(
        layer=Layer.STATE,
        content="room context",
        inject_at=InjectTiming.TURN_START
    ))

    # L4: Derived (after response)
    context.add(ContextLayer(
        layer=Layer.DERIVED,
        content="user insight",
        inject_at=InjectTiming.AFTER_RESPONSE
    ))

    # App connects with L1
    await port.connect(system_prompt=context.get_base())

    # Simulate SPEECH_STARTED - inject TURN_START layers
    turn_start_text = context.compile_for(InjectTiming.TURN_START)
    await port.add_text_item(turn_start_text)

    # Verify only state context injected
    assert "room context" in port.injected_texts[-1]
    assert "user insight" not in port.injected_texts[-1]

    # Simulate RESPONSE_DONE - inject AFTER_RESPONSE layers
    after_response_text = context.compile_for(InjectTiming.AFTER_RESPONSE)
    if after_response_text:
        await port.add_text_item(after_response_text)

    # Verify derived context injected separately
    assert "user insight" in port.injected_texts[-1]

async def test_http_ignores_timing():
    """Test that HTTP uses compile() which ignores timing."""
    context = ContextManager()

    context.add(ContextLayer(
        layer=Layer.STATE,
        content="state1",
        inject_at=InjectTiming.TURN_START
    ))
    context.add(ContextLayer(
        layer=Layer.DERIVED,
        content="derived1",
        inject_at=InjectTiming.AFTER_RESPONSE
    ))

    # HTTP: compile() returns ALL layers
    compiled = context.compile()

    assert "state1" in compiled
    assert "derived1" in compiled

async def test_proactive_trigger_pattern():
    """Test app-orchestrated proactive trigger with ASAP timing."""
    port = MockRealtimePort()
    context = ContextManager()

    # Add proactive context with ASAP timing
    context.add(ContextLayer(
        layer=Layer.PROACTIVE,
        content="Meeting reminder: Team standup in 5 minutes",
        inject_at=InjectTiming.ASAP
    ))

    # App triggers the response using compile_for(ASAP)
    text = context.compile_for(InjectTiming.ASAP)
    await port.add_text_item(text)
    await port.create_response()

    assert "Meeting reminder" in port.injected_texts[-1]
    assert port.response_triggered
```

---

## Summary

This implementation guide provides a complete roadmap for the LDCI ContextManager:

1. **5 Layers** - Base, State, Override, Derived, Proactive
2. **ContextLayer-first** - Create layer objects, then add to manager
3. **Injection timing** - `inject_at` on each layer (SESSION_START, TURN_START, AFTER_RESPONSE, ASAP)
4. **compile() for HTTP** - Returns ALL layers as string (timing ignored)
5. **compile_for(timing) for S2S** - Returns matching layers as string (convenience)
6. **get_layers_for(timing) for S2S** - Returns layer objects (for injectors/custom)
7. **L1 not in compile()** - Access via `get_base()`
8. **Order control** - Multiple items per layer, sorted by order
9. **Compile-time flags** - `compile(audio_tags=True)`
10. **No port binding** - App/injector controls injection
11. **Optional ContextInjector** - For S2S when you need layer-level control
12. **History is app's job** - LDCI doesn't own it
13. **Proactive is app-orchestrated** - LDCI provides context, app triggers

### Core API Summary

```python
# Create layers with timing info
state_layer = ContextLayer(
    layer=Layer.STATE,
    content="room context",
    inject_at=InjectTiming.TURN_START,  # When to inject (for S2S)
    order=10
)

# Add to manager
context = ContextManager()
context.add(state_layer)

# Access L1 for initialization
system_prompt = context.get_base()

# HTTP: compile() returns ALL layers (timing ignored)
compiled = context.compile(audio_tags=True)

# S2S Option A: compile_for() returns string
text = context.compile_for(InjectTiming.TURN_START)

# S2S Option B: get_layers_for() returns layer objects
layers = context.get_layers_for(InjectTiming.TURN_START)

# S2S Option C: Use ContextInjector
injector = RealtimeContextInjector(port)
await injector.inject_for(context, InjectTiming.TURN_START)
```

### HTTP vs S2S Pattern

```python
# HTTP: All at once (timing ignored)
compiled = context.compile()
# Use in request...

# S2S Option A: compile_for() convenience
async for event in port.events():
    if event.type == "speech_started":
        await port.add_text_item(context.compile_for(InjectTiming.TURN_START))

# S2S Option B: ContextInjector (layer-level control)
injector = RealtimeContextInjector(port)
async for event in port.events():
    if event.type == "speech_started":
        await injector.inject_for(context, InjectTiming.TURN_START)

# S2S Option C: Manual with layer objects
async for event in port.events():
    if event.type == "speech_started":
        for layer in context.get_layers_for(InjectTiming.TURN_START):
            await port.add_text_item(layer.content)
```

The design is intentionally minimal. Start with core features, add complexity only when proven necessary.
