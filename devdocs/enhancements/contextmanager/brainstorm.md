# LDCI Framework - Design Brainstorm

## The Core Problem

We need a framework that:
1. Works across all modalities (T2T HTTP, T2T WebSocket, S2S Voice)
2. Keeps ContextManager simple (just manages layers)
3. Lets app/injector control injection timing
4. Manages the 5 layers with timing metadata for S2S

---

## Key Design Decisions

### 1. ContextManager is Pure (No Binding)

ContextManager only:
- Stores layers
- Compiles to string
- Filters by timing

It does NOT:
- Know about ports
- Handle events
- Control injection timing

```
ContextManager = Library (you call it)
NOT Framework (it calls you)
```

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
    inject_at=InjectTiming.TURN_START,  # When to inject
    order=10
)
```

### 4. HTTP vs S2S

| Modality | How it works |
|----------|--------------|
| HTTP | `compile()` returns ALL layers (timing ignored) |
| S2S | `compile_for(timing)` or `get_layers_for(timing)` filters by timing |

### 5. History is App's Job

ContextManager doesn't manage history. App handles it:

```python
# HTTP
response = llm.invoke([
    SystemMessage(content=context.get_base()),
    *history,  # App provides
    HumanMessage(content=compiled + "\n" + user_input)
])

# S2S
# History managed by the persistent connection
```

### 6. Proactive is App-Orchestrated

"Proactive" is always faked. The app decides WHEN to trigger:

```python
# App decides to make AI speak
proactive = ContextLayer(
    layer=Layer.PROACTIVE,
    content="Meeting reminder...",
    inject_at=InjectTiming.ASAP
)
context.add(proactive)

# App triggers
await port.add_text_item(context.compile_for(InjectTiming.ASAP))
await port.create_response()
```

---

## Components

### 1. ContextLayer (dataclass)

Carries a piece of context with metadata.

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

### 3. ContextManager (class)

Manages layers and provides compilation. NO binding to ports.

```python
class ContextManager:
    def add(self, layer: ContextLayer) -> None
        """Add a context layer."""

    def get_base(self) -> Optional[str]
        """Get L1 base context (or override if set)."""

    def compile(self, **options) -> str
        """Compile ALL layers to string (for HTTP, timing ignored)."""

    def compile_for(self, timing: InjectTiming, **options) -> str
        """Compile layers matching timing to string (for S2S convenience)."""

    def get_layers_for(self, timing: InjectTiming) -> List[ContextLayer]
        """Get layer objects matching timing (for injectors/custom)."""

    def clear_state(self) -> None
    def clear_derived(self) -> None
    def clear_proactive(self) -> None
    def clear_override(self) -> None
```

### 4. ContextInjector (optional, for S2S)

Separate component that handles injection. NOT part of ContextManager.

```python
class ContextInjector(Protocol):
    async def inject(self, layer: ContextLayer) -> None
    async def inject_all(self, layers: List[ContextLayer]) -> None
    async def inject_for(self, context: ContextManager, timing: InjectTiming) -> None

class RealtimeContextInjector:
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

## How It Works Across Modalities

### T2T HTTP (Stateless)

```python
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

**Key insight:** No timing matters. All layers compiled at once.

---

### S2S Voice (Realtime, Bidirectional)

```python
context = ContextManager()

# L1: Base - session start
context.add(ContextLayer(
    layer=Layer.BASE,
    content="You are a helpful assistant.",
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

# S2S Option A: compile_for() convenience
async for event in port.events():
    if event.type == "speech_started":
        text = context.compile_for(InjectTiming.TURN_START)
        if text:
            await port.add_text_item(text)

# S2S Option B: ContextInjector
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

**Key insight:** Different layers injected at different times. App controls timing.

---

## Why No Binding Pattern?

We considered having ContextManager wrap the event stream:

```python
# REJECTED: ContextManager wraps events
async for event in context.process_events():
    # ContextManager intercepts and injects automatically
    ...
```

**Problems:**
1. HTTP has no events - doesn't fit the pattern
2. Hidden magic - injection happens invisibly
3. Tight coupling to event types (VoiceEventType)
4. Framework pattern (it calls you) instead of library (you call it)

**Solution: Keep it simple**

```python
# ACCEPTED: App controls everything
async for event in port.events():
    if event.type == "speech_started":
        await port.add_text_item(context.compile_for(InjectTiming.TURN_START))
```

Same pattern for HTTP and S2S. App controls timing. ContextManager stays pure.

---

## Summary

| Component | Responsibility | Knows about ports? |
|-----------|----------------|--------------------|
| **ContextLayer** | Carry context + timing metadata | No |
| **ContextManager** | Store layers, compile | No |
| **ContextInjector** | Inject layers to port (optional) | Yes |

**The key insight:** ContextManager is a library, not a framework. It manages layers and compiles. App/injector handles the rest.

---

## API Summary

```python
# Create layers with timing
layer = ContextLayer(
    layer=Layer.STATE,
    content="...",
    inject_at=InjectTiming.TURN_START,
    order=10
)

# Add to manager
context = ContextManager()
context.add(layer)

# HTTP: compile() returns ALL layers
compiled = context.compile()

# S2S: Three options
text = context.compile_for(InjectTiming.TURN_START)  # String
layers = context.get_layers_for(InjectTiming.TURN_START)  # Objects
await injector.inject_for(context, InjectTiming.TURN_START)  # Via injector

# L1 accessed separately
system_prompt = context.get_base()
```

---

## Open Questions (Resolved)

| Question | Resolution |
|----------|------------|
| ContextLayer generic or per-type? | Generic with `layer: Layer` enum |
| How does ContextManager know about events? | It doesn't. App controls timing. |
| Should compile() be on ContextManager? | Yes, returns string |
| How to handle authority in injection? | Informational metadata, not runtime |
| Binding pattern? | No. App/injector handles injection. |
| History ownership? | App's responsibility |
| Proactive trigger? | App-orchestrated, AI never spontaneously decides |
