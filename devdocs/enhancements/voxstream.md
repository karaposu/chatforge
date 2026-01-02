Deep Analysis: VoxStream Adapter Architecture

  Problem Analysis

  Core Challenge

  The VoxStream adapter suffers from state desynchronization - multiple components track their own view of audio state, leading to race conditions, timing bugs, and brittle workarounds.

  What We've Observed

  | Issue               | Symptom                                       | Root Cause                               |
  |---------------------|-----------------------------------------------|------------------------------------------|
  | "Already capturing" | VoxStream thinks it's capturing when we don't | Two sources of truth                     |
  | Barge-in fails      | Audio playing but is_playing=False            | API state ≠ audio state                  |
  | PortAudio errors    | AUHAL -50 during mode switch                  | No hardware transition abstraction       |
  | "No audio recorded" | 0 chunks captured                             | UI says "Recording" before capture ready |

  The Fundamental Problem

  Current Architecture (Broken):

  VoiceSession._state.is_playing  ──┐
                                    ├──► Which one is true?
  VoxStreamAdapter._capturing     ──┤
                                    │
  VoxStream.is_playing            ──┤
                                    │
  VoxStream internal state        ──┘

  We're managing 4+ sources of truth with delays and hope.

  ---
  Multi-Dimensional Analysis

  Technical Perspective

  The State Machine Gap

  VoxStream exposes low-level operations but no state machine:

  # What VoxStream provides:
  await voxstream.start_capture_stream()  # Returns queue, but when is it "ready"?
  voxstream.stop_capture_stream()          # Async, but when is it "done"?
  voxstream.is_playing                     # Property, but no "finished" event

  # What's missing:
  # - State: IDLE → STARTING → CAPTURING → STOPPING → IDLE
  # - Events: on_capture_ready, on_capture_stopped
  # - Atomics: switch_to_capture() that handles transitions

  The Async Generator Problem

  async def start_capture(self) -> AsyncGenerator[bytes, None]:
      # When does this "start"? 
      # - When function is called? No, it's a generator
      # - When first awaited? Sort of
      # - When first chunk yields? Actually ready here

      queue = await self._voxstream.start_capture_stream()  # (1) Queue created
      # ... 100-200ms passes ...
      chunk = await queue.get()  # (2) First chunk arrives - NOW we're ready
      yield chunk

  The gap between (1) and (2) is where our bugs live.

  User Perspective

  The UX Timeline Problem

  User presses ENTER
      │
      ▼
  "Recording..." displayed     ◄── User thinks they can speak
      │
      ▼
  [100ms] interrupt() if playing
      │
      ▼
  [100ms] settle delay
      │
      ▼
  [150ms] stop_capture wait
      │
      ▼
  [100ms] start_capture_stream()
      │
      ▼
  [150ms] first chunk arrives    ◄── ACTUALLY ready to record
      │
      ▼
  User already pressed ENTER to stop (0 chunks)

  600ms of dead time where user thinks they're recording but aren't.

  System Perspective

  PortAudio Hardware Constraints

  ┌─────────────────────────────────────────────────┐
  │              macOS Audio System                  │
  ├─────────────────────────────────────────────────┤
  │  CoreAudio (AUHAL)                              │
  │    │                                            │
  │    ├── Output Device (speakers/headphones)     │
  │    │     └── Must release before...            │
  │    │                                            │
  │    └── Input Device (microphone)               │
  │          └── ...can acquire for capture        │
  │                                                 │
  │  Error -50: "Device busy" or "Invalid state"   │
  └─────────────────────────────────────────────────┘

  The AUHAL error indicates we're not respecting hardware transition time.

  ---
  Solution Options

  Option 1: Enhanced Adapter Layer (Minimal VoxStream Changes)

  Description: Add a state machine and callbacks in VoxStreamAdapter without modifying VoxStream library.

  class CaptureState(Enum):
      IDLE = "idle"
      STARTING = "starting"
      READY = "ready"       # First chunk received
      STOPPING = "stopping"

  class VoxStreamAdapter(AudioStreamPort):
      def __init__(self, ...):
          self._capture_state = CaptureState.IDLE
          self._capture_ready_event = asyncio.Event()

          # Callbacks
          self.on_capture_ready: Callable[[], None] | None = None
          self.on_playback_complete: Callable[[], None] | None = None

      async def start_capture(self) -> AsyncGenerator[bytes, None]:
          self._capture_state = CaptureState.STARTING
          self._capture_ready_event.clear()

          queue = await self._voxstream.start_capture_stream()

          first_chunk = True
          async for chunk in self._iterate_queue(queue):
              if first_chunk:
                  self._capture_state = CaptureState.READY
                  self._capture_ready_event.set()
                  if self.on_capture_ready:
                      self.on_capture_ready()
                  first_chunk = False
              yield chunk

      async def wait_for_capture_ready(self, timeout: float = 2.0) -> bool:
          """Wait until capture is actually receiving audio."""
          try:
              await asyncio.wait_for(
                  self._capture_ready_event.wait(),
                  timeout=timeout
              )
              return True
          except asyncio.TimeoutError:
              return False

      async def switch_to_capture(self) -> AsyncGenerator[bytes, None]:
          """Atomic: stop playback, wait for hardware, start capture."""
          # Stop playback
          if self._voxstream.is_playing:
              self._voxstream.interrupt_playback(force=True)
              await self._wait_for_playback_stop()

          # Start capture
          return self.start_capture()

  Pros:
  - No changes to VoxStream library
  - Can implement immediately
  - Addresses immediate pain points

  Cons:
  - Still working around VoxStream limitations
  - Playback completion detection is hacky (polling)
  - Doesn't fix fundamental VoxStream issues

  Risk: Medium - may need adjustment as we discover more edge cases

  ---
  Option 2: VoxStream State Machine Enhancement

  Description: Modify VoxStream library to add proper state machine and events.

  # In VoxStream library:

  class AudioState(Enum):
      IDLE = "idle"
      CAPTURE_STARTING = "capture_starting"
      CAPTURING = "capturing"
      PLAYBACK_BUFFERING = "playback_buffering"
      PLAYING = "playing"
      PLAYBACK_DRAINING = "playback_draining"

  class VoxStream:
      def __init__(self):
          self._state = AudioState.IDLE
          self._state_lock = asyncio.Lock()
          self._state_changed = asyncio.Condition()

          # Event callbacks
          self.on_state_changed: Callable[[AudioState, AudioState], None] | None = None
          self.on_capture_ready: Callable[[], None] | None = None
          self.on_playback_complete: Callable[[], None] | None = None

      @property
      def state(self) -> AudioState:
          return self._state

      async def _set_state(self, new_state: AudioState):
          async with self._state_lock:
              old_state = self._state
              self._state = new_state
              if self.on_state_changed:
                  self.on_state_changed(old_state, new_state)
              async with self._state_changed:
                  self._state_changed.notify_all()

      async def wait_for_state(
          self, 
          target: AudioState, 
          timeout: float = 5.0
      ) -> bool:
          """Wait until specific state is reached."""
          async with self._state_changed:
              try:
                  await asyncio.wait_for(
                      self._state_changed.wait_for(lambda: self._state == target),
                      timeout=timeout
                  )
                  return True
              except asyncio.TimeoutError:
                  return False

      async def start_capture_stream(self) -> asyncio.Queue:
          await self._set_state(AudioState.CAPTURE_STARTING)
          queue = await self._internal_start_capture()
          # State transitions to CAPTURING when first chunk arrives
          return queue

      async def stop_capture_stream(self) -> None:
          await self._set_state(AudioState.IDLE)
          await self._internal_stop_capture()
          # Blocks until hardware is actually stopped

  Pros:
  - Fixes problems at the source
  - Clean API for all consumers
  - Single source of truth
  - Proper async/await semantics

  Cons:
  - Requires VoxStream library changes
  - More complex implementation
  - Need to maintain library

  Risk: Low-Medium - well-understood patterns, but more work

  ---
  Option 3: Event-Driven Architecture with Message Bus

  Description: Decouple components using an event bus pattern.

  class AudioEvent(Enum):
      CAPTURE_REQUESTED = "capture_requested"
      CAPTURE_STARTED = "capture_started"
      CAPTURE_READY = "capture_ready"      # First chunk
      CAPTURE_STOPPED = "capture_stopped"
      PLAYBACK_STARTED = "playback_started"
      PLAYBACK_CHUNK = "playback_chunk"
      PLAYBACK_COMPLETE = "playback_complete"
      INTERRUPT_REQUESTED = "interrupt_requested"

  class AudioEventBus:
      def __init__(self):
          self._subscribers: dict[AudioEvent, list[Callable]] = {}
          self._state = AudioState.IDLE

      def subscribe(self, event: AudioEvent, callback: Callable):
          self._subscribers.setdefault(event, []).append(callback)

      async def emit(self, event: AudioEvent, data: Any = None):
          for callback in self._subscribers.get(event, []):
              if asyncio.iscoroutinefunction(callback):
                  await callback(data)
              else:
                  callback(data)

  # Usage in VoiceSession:
  class VoiceSession:
      def __init__(self, audio: AudioStreamPort, ...):
          self._bus = AudioEventBus()

          # React to audio events
          self._bus.subscribe(AudioEvent.CAPTURE_READY, self._on_capture_ready)
          self._bus.subscribe(AudioEvent.PLAYBACK_COMPLETE, self._on_playback_complete)

      async def _on_capture_ready(self, _):
          # Now safe to show "Recording..." to user
          self._ui_state = "recording"

  Pros:
  - Complete decoupling
  - Easy to add new behaviors
  - Testable (can mock events)
  - Scales to complex scenarios

  Cons:
  - More infrastructure code
  - Indirection can make debugging harder
  - Overkill for current needs?

  Risk: Medium - architectural change, may be over-engineering

  ---
  Option 4: Synchronization Primitives Approach

  Description: Use proper concurrency primitives to coordinate state.

  class VoxStreamAdapter(AudioStreamPort):
      def __init__(self):
          # Synchronization primitives
          self._capture_ready = asyncio.Event()
          self._capture_stopped = asyncio.Event()
          self._playback_complete = asyncio.Event()
          self._mode_lock = asyncio.Lock()  # Prevent concurrent mode switches

      async def start_capture_and_wait(
          self, 
          timeout: float = 2.0
      ) -> AsyncGenerator[bytes, None]:
          """Start capture and wait until it's actually ready."""
          async with self._mode_lock:  # Exclusive access during transition
              self._capture_ready.clear()
              self._capture_stopped.clear()

              gen = self._start_capture_internal()

              # Wait for first chunk or timeout
              try:
                  await asyncio.wait_for(
                      self._capture_ready.wait(),
                      timeout=timeout
                  )
              except asyncio.TimeoutError:
                  raise AudioStreamError("Capture failed to start")

              return gen

      async def stop_and_wait(self, timeout: float = 1.0) -> None:
          """Stop capture and wait until hardware is idle."""
          async with self._mode_lock:
              self._capturing = False
              await self._voxstream.stop_capture_stream()

              try:
                  await asyncio.wait_for(
                      self._capture_stopped.wait(),
                      timeout=timeout
                  )
              except asyncio.TimeoutError:
                  self._log("Warning: stop_capture timed out")

  Pros:
  - Uses proven concurrency patterns
  - Clear synchronization points
  - mode_lock prevents race conditions
  - Events provide reliable signaling

  Cons:
  - Still need to detect when VoxStream is "done"
  - Requires careful deadlock avoidance
  - More complex than current approach

  Risk: Low - well-established patterns

  ---
  Recommendation

  Phased Approach: Option 1 → Option 2

  Phase 1 (Immediate): Enhanced Adapter Layer

  Implement Option 1 to fix immediate issues:

  # VoxStreamAdapter additions:

  class VoxStreamAdapter(AudioStreamPort):
      def __init__(self, ...):
          # ... existing ...
          self._capture_ready_event = asyncio.Event()
          self._mode_lock = asyncio.Lock()

      @property
      def is_capture_ready(self) -> bool:
          """True if capture is active and receiving chunks."""
          return self._capturing and self._capture_ready_event.is_set()

      async def start_capture(self) -> AsyncGenerator[bytes, None]:
          async with self._mode_lock:
              self._capture_ready_event.clear()
              # ... existing start logic ...

              first_chunk = True
              while self._capturing:
                  chunk = await queue.get()
                  if first_chunk:
                      self._capture_ready_event.set()
                      self._log("Capture ready - first chunk received")
                      first_chunk = False
                  yield chunk

      async def wait_for_capture_ready(self, timeout: float = 2.0) -> bool:
          try:
              await asyncio.wait_for(
                  self._capture_ready_event.wait(),
                  timeout=timeout
              )
              return True
          except asyncio.TimeoutError:
              return False

      async def interrupt_and_switch_to_capture(self) -> AsyncGenerator[bytes, None]:
          """Atomic barge-in operation."""
          async with self._mode_lock:
              # Stop playback
              if self._voxstream.is_playing:
                  self._voxstream.interrupt_playback(force=True)
                  # Poll until not playing (VoxStream limitation)
                  for _ in range(20):  # 2 seconds max
                      if not self._voxstream.is_playing:
                          break
                      await asyncio.sleep(0.1)

              # Small hardware settle time
              await asyncio.sleep(0.05)  # 50ms

              # Start capture
              return await self.start_capture()

  Phase 2 (Later): VoxStream Library Enhancement

  Once patterns are proven in adapter, push them down to VoxStream:

  1. Add AudioState enum and state machine
  2. Add state change callbacks
  3. Make stop_capture_stream() properly awaitable (returns when done, not when started stopping)
  4. Add on_playback_complete callback

  Implementation Roadmap

  Week 1:
  ├── Add is_capture_ready property
  ├── Add wait_for_capture_ready() method  
  ├── Add _mode_lock for thread safety
  └── Add interrupt_and_switch_to_capture()

  Week 2:
  ├── Update TurnBasedMode to use new methods
  ├── Update VoiceSession interrupt() to use atomic switch
  ├── Remove arbitrary delays (replace with events)
  └── Test barge-in scenarios

  Week 3:
  ├── Add on_capture_ready callback
  ├── Update UI to show "Preparing..." → "Recording..."
  └── Handle edge cases (timeout, errors)

  Future:
  ├── Push state machine to VoxStream library
  ├── Add proper playback completion detection
  └── Consider full-duplex support

  Success Metrics

  1. Zero "Already capturing" errors - Mode lock prevents races
  2. Barge-in works reliably - Atomic switch handles transitions
  3. No PortAudio errors - Proper hardware settle time
  4. "Recording" means recording - UI waits for is_capture_ready

  ---
  Alternative Perspectives

  Contrarian View: Are We Over-Engineering?

  The current system "works" with delays. Users can:
  - Wait a beat before speaking after pressing ENTER
  - Press ENTER again if barge-in fails

  Is the complexity of a state machine worth it for edge cases?

  Counter-argument: Voice UX must feel instant. 600ms delays and occasional failures feel broken. Voice assistants like Siri/Alexa don't have visible delays.

  Future Consideration: WebRTC

  If VoxTerm ever needs:
  - Browser support
  - Remote audio
  - Echo cancellation

  Consider replacing VoxStream with WebRTC-based audio, which handles these state machine issues internally.

  Hardware Diversity

  The PortAudio errors are macOS-specific. Linux/Windows may have different quirks. The state machine approach creates a place to handle platform-specific timing.

  ---
  Confidence Assessment

  | Aspect             | Confidence | Notes                            |
  |--------------------|------------|----------------------------------|
  | Problem diagnosis  | 95%        | Clear pattern in logs and fixes  |
  | Phase 1 solution   | 85%        | Proven patterns, may need tuning |
  | Phase 2 solution   | 70%        | Depends on VoxStream internals   |
  | Timeline estimates | 60%        | Unknown unknowns in audio        |

  The core insight - state desynchronization - is high confidence. The specific implementation may need iteration as we discover more edge cases.