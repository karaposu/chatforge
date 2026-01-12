# ChamberProtocol Prompt Management System: Comprehensive Analysis

## Executive Summary

ChamberProtocol implements a **linear, single-pass prompt compilation** system where structured request data flows through multiple transformations before reaching the LLM. The system is currently HTTP-only (stateless) and compiles all context into a single prompt per request.

This document analyzes the complete prompt flow and maps it to the LDCI (Layered Dynamic Context Injection) framework for future S2S voice integration.

---

## 1. Complete Request-to-Response Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            UNITY GAME CLIENT                                 │
│                                                                             │
│  Constructs SiluetRequest with:                                            │
│  - PlayerProgress (loops, puzzles, extracted_information)                  │
│  - RoomContext (room_name, objects, active_puzzle, puzzle_solution)        │
│  - VisualContext (currently_looking_at, recent_objects_viewed)             │
│  - AICharacterResponseParameters (disclosure_level, intent, mood)          │
│  - player_input (user's message)                                           │
│  - Optional: proactive_dialog, response_constraints, language, model       │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                                        ▼ HTTP POST /chat/{chat_id}/messages/siluet
┌─────────────────────────────────────────────────────────────────────────────┐
│                      chat_api.py: chat_siluet_post()                        │
│                                                                             │
│  1. Validate JWT token (get_token_bearerAuth)                              │
│  2. Extract user_id from token.sub                                         │
│  3. Instantiate SiluetService(user_id, chat_id, request, dependencies)     │
│  4. Return service.response                                                │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      siluet_service.py: SiluetService                       │
│                                                                             │
│  __init__(user_id, chat_id, request, dependencies):                        │
│    1. Store request as self.request                                        │
│    2. Call _process_request()                                              │
│                                                                             │
│  _process_request():                                                        │
│    1. Initialize MyLLMService()                                            │
│    2. Fetch conversation history via _fetch_conversation_history()         │
│       └─ message_repo.fetch_messages(chat_id, limit=20)                    │
│    3. Format history: "Player: {msg} / Siluet: {msg}"                     │
│    4. Serialize request objects to JSON strings:                           │
│       ├─ ai_character_profile_str (manual formatting with \n)              │
│       ├─ player_progress_str = json.dumps(request.player_progress.dict()) │
│       ├─ room_context_str = json.dumps(request.room_context.dict())       │
│       ├─ visual_context_str = json.dumps(request.visual_context.dict())   │
│       ├─ char_params_str = json.dumps(request.ai_char_response_params)    │
│       └─ response_constraints_str = json.dumps(...)                        │
│    5. Call llm_service.generate_siluet_answer(...all params...)            │
│    6. Save interaction via _save_interaction()                             │
│    7. Build SiluetResponse(response=llm_response)                          │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      myllmservice.py: generate_siluet_answer()              │
│                                                                             │
│  Parameters: game_context, ai_character_profile, player_progress,          │
│              room_context, visual_context, conversation_memory,            │
│              proactive_triggers, ai_character_response_parameters,         │
│              player_input, response_constraints, language, model,          │
│              enable_audio_tags                                             │
│                                                                             │
│  1. Import StepContext from schemas                                        │
│  2. Create StepContext with all parameters                                 │
│  3. Call context.compile() → returns full_prompt string                    │
│  4. Get LLM via get_llm(provider="openai", model_name=model)              │
│  5. Invoke: llm.invoke([HumanMessage(content=full_prompt)])               │
│  6. Return response.content                                                │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      schemas.py: StepContext.compile()                      │
│                                                                             │
│  1. Check if proactive_triggers exists:                                    │
│     ├─ YES: PROACTIVE MODE                                                 │
│     │   - Clear player_input                                               │
│     │   - Use PROACTIVE_SILUET_CONSTRAINTS or provided                    │
│     │   - Build proactive generate_instruction                             │
│     └─ NO: REACTIVE MODE                                                   │
│         - Use provided constraints or get_default_constraints()            │
│         - Use GENERATE_ANSWER_INSTRUCTION                                  │
│                                                                             │
│  2. Build language_instruction if language provided                        │
│                                                                             │
│  3. If enable_audio_tags: prepend AUDIO_TAGS_INSTRUCTION                   │
│                                                                             │
│  4. Format SILUET_PROMPT_TEMPLATE with all values:                         │
│     - Apply defaults for missing fields (from prompts.py)                  │
│     - Return compiled full_prompt string                                   │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      prompts.py: SILUET_PROMPT_TEMPLATE                     │
│                                                                             │
│  Contains:                                                                  │
│  - SILUET_PROMPT_TEMPLATE (main template with {placeholders})              │
│  - GAME_CONTEXT (~3KB, game rules and lore)                                │
│  - SILUET_PROFILE (~500 chars, character identity)                         │
│  - SILUET_CHAR_GENERIC (interaction guidelines)                            │
│  - GENERATE_ANSWER_INSTRUCTION (how to respond)                            │
│  - AUDIO_TAGS_INSTRUCTION (voice emotion tags)                             │
│  - get_default_constraints() (random word limit 2-100)                     │
│  - PROACTIVE_SILUET_CONSTRAINTS (40 word limit)                            │
│                                                                             │
│  Final assembled prompt (~8-15KB) sent to LLM as single HumanMessage       │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              OpenAI API                                      │
│                                                                             │
│  Model: gpt-4o-mini (default) or gpt-4o                                    │
│  Input: Single HumanMessage with full_prompt                               │
│  Returns: AI response string                                               │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      siluet_service.py: Post-Processing                     │
│                                                                             │
│  _save_interaction(response, generation_data):                             │
│    1. Get user_participant from chat_repo                                  │
│    2. Get/create assistant_participant ("Siluet")                          │
│    3. Save player message to DB (role="user")                              │
│    4. Save AI response to DB (role="assistant")                            │
│                                                                             │
│  Build final response:                                                      │
│    self.response = SiluetResponse(response=llm_response)                   │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                                        ▼
                               Return to Unity Client
                               HTTP 200 { "response": "..." }
```

---

## 2. Context Component Transformations

### Transformation Chain by Component

| Component | Unity Client | SiluetService | MyLLMService | StepContext.compile() | Final Prompt |
|-----------|--------------|---------------|--------------|----------------------|--------------|
| **player_progress** | `PlayerProgress` Pydantic model | `json.dumps(request.player_progress.dict())` | Passed as string | Uses as-is or default | `{player_progress}` |
| **room_context** | `RoomContext` Pydantic model | `json.dumps(request.room_context.dict())` | Passed as string | Uses as-is or "No room context" | `{room_context}` |
| **visual_context** | `VisualContext` Pydantic model | `json.dumps(request.visual_context.dict())` | Passed as string | Uses as-is or "No visual context" | `{visual_context}` |
| **ai_character_profile** | `AICharacterProfile` model | Manual string formatting with `\n` | Passed as string | Uses or `SILUET_PROFILE` default | `{ai_character_profile}` |
| **char_params** | `AICharacterResponseParameters` | `json.dumps(...)` | Passed as string | Uses or default message | `{character_parameters}` |
| **conversation_memory** | N/A (from DB) | Fetched from DB, formatted as "Player: .../Siluet: ..." | Passed as string | Uses or "No previous messages." | `{conversation_memory}` |
| **response_constraints** | `ResponseConstraints` model | `json.dumps(...)` | Passed as string | Uses or random word limit | `{response_constraints}` |
| **player_input** | `str` | Passed directly | Passed as string | Uses or empty string | `{player_input}` |
| **proactive_dialog** | Optional `str` | Passed directly | Passed as string | Modifies `generate_instruction` | Changes instruction mode |
| **language** | Optional `str` | Passed directly | Passed as string | Appends language instruction | `{language_instruction}` |
| **enable_audio_tags** | `bool` | Passed directly | Passed as bool | Prepends `AUDIO_TAGS_INSTRUCTION` | Part of `{generate_instruction}` |

### Transformation Flow Diagram

```
Unity Client (Pydantic Models)
         │
         │  HTTP POST (JSON)
         ▼
SiluetService (Deserialize to Pydantic, then serialize to strings)
         │
         │  player_progress → json.dumps() → string
         │  room_context → json.dumps() → string
         │  visual_context → json.dumps() → string
         │  ai_character_profile → manual format → string
         │  conversation_memory → DB fetch + format → string
         ▼
MyLLMService (All strings)
         │
         │  Create StepContext dataclass
         ▼
StepContext.compile() (Apply defaults, format template)
         │
         │  prompts.SILUET_PROMPT_TEMPLATE.format(...)
         ▼
Full Prompt String (~8-15KB)
         │
         │  HumanMessage(content=full_prompt)
         ▼
OpenAI API
```

---

## 3. Where Defaults Are Applied

### Default Application Points

```python
# In StepContext.compile() - schemas.py:

game_context         = self.game_context or prompts.GAME_CONTEXT           # ~3KB default
ai_character_profile = self.ai_character_profile or prompts.SILUET_PROFILE # ~500 chars
player_progress      = self.player_progress or "No player progress data"
room_context         = self.room_context or "No room context"
visual_context       = self.visual_context or "No visual context"
conversation_memory  = self.conversation_memory or "No previous messages."
character_parameters = self.ai_character_response_parameters or "Maintain default personality..."
response_constraints = actual_constraints  # Random word limit if not provided
```

### Random Word Limit Selection

```python
# In prompts.py:

word_options = [2, 3, 5, 10, 15, 25, 50, 75, 100]

def get_default_constraints():
    word_limit = random.choice(word_options)  # Fresh random each request
    return f"""
 Keep responses under {word_limit} words
 Never break character or reveal this is a game
 Create atmospheric, unsettling responses"""
```

### Default Cascade Decision Tree

```
Request arrives
    │
    ├─ Has game_context? ──NO──► Use prompts.GAME_CONTEXT (3KB)
    │                     ──YES─► Use provided
    │
    ├─ Has ai_character_profile? ──NO──► Use prompts.SILUET_PROFILE
    │                             ──YES─► Use provided
    │
    ├─ Has player_progress? ──NO──► "No player progress data"
    │                        ──YES─► Use provided JSON string
    │
    ├─ Has room_context? ──NO──► "No room context"
    │                     ──YES─► Use provided JSON string
    │
    ├─ Has visual_context? ──NO──► "No visual context"
    │                       ──YES─► Use provided JSON string
    │
    ├─ Has conversation_memory? ──NO──► "No previous messages."
    │                            ──YES─► Use fetched/formatted string
    │
    ├─ Has response_constraints? ──NO──► get_default_constraints() (random)
    │                             ──YES─► Use provided
    │
    └─ Has proactive_triggers? ──YES──► PROACTIVE mode
                                ──NO───► REACTIVE mode
```

---

## 4. Final Prompt Structure Sent to LLM

### Template Structure (SILUET_PROMPT_TEMPLATE)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ === HERE IS GAME CONTEXT: ===                                           │
│     {game_context}                          ← ~3KB, rarely changes      │
│                                                                         │
│ Content: Game name, loop system, room types, Silüet's role,            │
│          player bars, puzzle types, game progression, rules            │
├─────────────────────────────────────────────────────────────────────────┤
│ === HERE IS Siluet's PROFILE: ===                                       │
│     {ai_character_profile}                  ← Character identity        │
│                                                                         │
│ Content: Core identity, name, origin story, personality state          │
├─────────────────────────────────────────────────────────────────────────┤
│ === HERE IS PLAYER'S PROGRESS AND GAMEPLAY HISTORY: ===                 │
│     {player_progress}                       ← JSON, changes over time   │
│                                                                         │
│ Content: total_loops, current_loop, rooms_completed, puzzles_solved,   │
│          extracted_information (personality, triggers, fears, data)    │
├─────────────────────────────────────────────────────────────────────────┤
│ === HERE IS ROOM-SPECIFIC CONTEXT: ===                                  │
│     {room_context}                          ← JSON, changes per room    │
│                                                                         │
│ Content: room_name, room_type, available_objects (with details),       │
│          active_puzzle, puzzle_solution (SECRET), time_in_room         │
├─────────────────────────────────────────────────────────────────────────┤
│ === HERE IS VISUAL CONTEXT & OBJECT DETECTION: ===                      │
│     {visual_context}                        ← JSON, changes constantly  │
│                                                                         │
│ Content: currently_looking_at, look_duration, recent_objects_viewed,   │
│          last_10_seconds_viewed, last_3_seconds_viewed                 │
├─────────────────────────────────────────────────────────────────────────┤
│ === HERE IS PAST CONVERSATION: ===                                      │
│     {conversation_memory}                   ← From DB, grows over time  │
│                                                                         │
│ Format: "Player: message\nSiluet: response\n..."                       │
├─────────────────────────────────────────────────────────────────────────┤
│ === HERE IS BEHAVIORAL PARAMETERS: ===                                  │
│ (!Behaviour Parameters OVERRIDE all other constraints!)                 │
│     {character_parameters}                  ← JSON, changes per request │
│                                                                         │
│ Content: puzzle_secrets_disclosure_level, conversational_intent,       │
│          conversation_energy_dynamics, power_distribution,             │
│          engagement_level, interest_level, interaction_style,          │
│          emotional_state                                               │
├─────────────────────────────────────────────────────────────────────────┤
│ === HERE IS RESPONSE CONSTRAINTS: ===                                   │
│     {response_constraints}                  ← Word limits, rules        │
│                                                                         │
│ Content: max_length (random 2-100 words), language_mix,                │
│          reveal_level, maintain_character, allow_meta_commentary       │
├─────────────────────────────────────────────────────────────────────────┤
│ === PLAYER INPUT ===                                                    │
│     {player_input}                          ← User's actual message     │
├─────────────────────────────────────────────────────────────────────────┤
│ === HERE IS PROACTIVE TRIGGER REQUEST: ===                              │
│     {proactive_triggers_section}            ← Empty in reactive mode    │
├─────────────────────────────────────────────────────────────────────────┤
│ === GENERATE RESPONSE ===                                               │
│     [AUDIO_TAGS_INSTRUCTION if enabled]                                 │
│     {generate_instruction}                  ← Mode-specific instruction │
│                                                                         │
│ REACTIVE: "Based on all context, respond as Silüet..."                 │
│ PROACTIVE: "Generate AI-INITIATED message based on this event..."      │
├─────────────────────────────────────────────────────────────────────────┤
│ === CRITICAL: RESPONSE LENGTH OVERRIDE ===                              │
│     [Question type analysis instructions]                               │
│     - Simple personal questions: MAX 1-2 words                         │
│     - Basic questions: MAX 1 sentence                                  │
│     - Complex questions: Use full context                              │
├─────────────────────────────────────────────────────────────────────────┤
│ === Give us the answer in following language: ===                       │
│     {language_instruction}                  ← EN/TR                     │
└─────────────────────────────────────────────────────────────────────────┘
```

### Estimated Token Counts

| Section | Typical Size | Notes |
|---------|--------------|-------|
| GAME_CONTEXT | ~800 tokens | Static, same every request |
| SILUET_PROFILE | ~150 tokens | Static or per-cycle |
| player_progress | ~200-500 tokens | Grows over time |
| room_context | ~300-800 tokens | Varies by room complexity |
| visual_context | ~100-300 tokens | Changes constantly |
| conversation_memory | ~200-1000 tokens | Grows, limited to 20 messages |
| character_parameters | ~200-400 tokens | Game-controlled |
| Instructions | ~300-500 tokens | With audio tags |
| **Total** | **~2500-4500 tokens** | Per request |

---

## 5. LDCI Layer Mapping to Existing System

### Current System → LDCI Layers

| ChamberProtocol Component | LDCI Layer | Authority | Stability | S2S Timing |
|---------------------------|------------|-----------|-----------|------------|
| `GAME_CONTEXT` | **L1 Base** | DIRECTIVE | STATIC | SESSION_START |
| `SILUET_PROFILE` | **L1 Base** | DIRECTIVE | STATIC | SESSION_START |
| `SILUET_CHAR_GENERIC` | **L1 Base** | DIRECTIVE | STATIC | SESSION_START |
| `player_progress` | **L2 State** | INFORMATIVE | SESSION | TURN_START |
| `room_context` | **L2 State** | INFORMATIVE | TURN | TURN_START |
| `visual_context` | **L2 State** | INFORMATIVE | TURN (rapid) | TURN_START |
| `conversation_memory` | **L2 State** | INFORMATIVE | TURN | TURN_START |
| `ai_character_response_parameters` | **L2 State** | DIRECTIVE | TURN | TURN_START |
| `response_constraints` | **L2 State** | DIRECTIVE | TURN | TURN_START |
| `player_input` | **L2 State** | INFORMATIVE | TURN | TURN_START |
| `proactive_triggers` | **L5 Proactive** | DIRECTIVE | EVENT | ASAP |
| `AUDIO_TAGS_INSTRUCTION` | **Instructions** | N/A | N/A | N/A |
| `GENERATE_ANSWER_INSTRUCTION` | **Instructions** | N/A | N/A | N/A |
| `language_instruction` | **Instructions** | N/A | N/A | N/A |

### Key Insight: Separation of Concerns

```
Current System (mixed):
┌──────────────────────────────────────────────────────────────────┐
│  SILUET_PROMPT_TEMPLATE combines:                                │
│  - Context (what AI knows about game, player, room)              │
│  - Behavior parameters (how AI should behave)                    │
│  - Instructions (how AI should respond)                          │
│  - Constraints (output rules)                                    │
│  ALL in one template, ALL compiled together                      │
└──────────────────────────────────────────────────────────────────┘

LDCI Approach (separated):
┌──────────────────────────────────────────────────────────────────┐
│  L1 Base (via get_base())                                        │
│  → Stable identity: GAME_CONTEXT + SILUET_PROFILE               │
│  → Set once at session start for S2S                            │
└──────────────────────────────────────────────────────────────────┘
                              +
┌──────────────────────────────────────────────────────────────────┐
│  L2 State (via compile() or compile_for(TURN_START))            │
│  → Dynamic context: player_progress, room_context, visual_ctx   │
│  → Injected per-turn                                            │
└──────────────────────────────────────────────────────────────────┘
                              +
┌──────────────────────────────────────────────────────────────────┐
│  L5 Proactive (via compile_for(ASAP))                           │
│  → AI-initiated: proactive_triggers                             │
│  → Injected on external events                                  │
└──────────────────────────────────────────────────────────────────┘
                              +
┌──────────────────────────────────────────────────────────────────┐
│  App-provided instructions (NOT part of ContextManager)          │
│  → How to respond, format, language, audio tags                 │
│  → Appended by app after compile()                              │
└──────────────────────────────────────────────────────────────────┘
```

### Visual Context: The S2S Challenge

In the current HTTP system, `visual_context` is included in every request. But it changes constantly (every few seconds as player looks around).

For S2S, this is the key use case for `InjectTiming.TURN_START`:

```
HTTP (current):
  Every request includes fresh visual_context
  No problem - stateless

S2S (future):
  Session starts with system_prompt (L1)
  visual_context changes 10x before user speaks
  On SPEECH_STARTED:
    └─ Inject latest visual_context via add_text_item()
    └─ AI now knows what player is looking at when asking "What is this?"
```

---

## 6. Recommendations for LDCI Integration

### Option A: Minimal Integration (Replace StepContext Only)

Replace `StepContext.compile()` with `ContextManager.compile()`:

```python
# In myllmservice.py

from chatforge.services.context import ContextManager, ContextLayer, Layer

def generate_siluet_answer(self, ...):
    context = ContextManager()

    # L1 Base
    context.add(ContextLayer(
        layer=Layer.BASE,
        content=game_context or prompts.GAME_CONTEXT,
        order=1,
    ))
    context.add(ContextLayer(
        layer=Layer.BASE,
        content=ai_character_profile or prompts.SILUET_PROFILE,
        order=2,
    ))

    # L2 State
    context.add(ContextLayer(
        layer=Layer.STATE,
        content=f"=== PLAYER PROGRESS ===\n{player_progress}",
        order=10,
    ))
    context.add(ContextLayer(
        layer=Layer.STATE,
        content=f"=== ROOM CONTEXT ===\n{room_context}",
        order=20,
    ))
    context.add(ContextLayer(
        layer=Layer.STATE,
        content=f"=== VISUAL CONTEXT ===\n{visual_context}",
        order=30,
    ))
    context.add(ContextLayer(
        layer=Layer.STATE,
        content=f"=== CONVERSATION MEMORY ===\n{conversation_memory}",
        order=40,
    ))
    context.add(ContextLayer(
        layer=Layer.STATE,
        content=f"=== CHARACTER PARAMETERS ===\n{character_parameters}",
        order=50,
    ))

    # Compile context
    compiled_context = context.compile()

    # App handles instructions separately
    instructions = build_instructions(
        audio_tags=enable_audio_tags,
        language=language,
        proactive=proactive_triggers,
        constraints=response_constraints,
    )

    full_prompt = f"{context.get_base()}\n\n{compiled_context}\n\n{instructions}\n\n{player_input}"

    # Invoke LLM
    llm = self._get_llm(model)
    response = llm.invoke([HumanMessage(content=full_prompt)])
    return response.content
```

**Pros:**
- Minimal code changes
- Immediate benefit of structured layers
- Easy rollback

**Cons:**
- Still HTTP-only
- Doesn't leverage timing metadata

---

### Option B: Full LDCI with S2S Preparation (Recommended)

Create a `SiluetContextBuilder` that prepares for future S2S:

```python
# New file: impl/context/siluet_builder.py

from chatforge.services.context import (
    ContextManager, ContextLayer, Layer, InjectTiming
)
from impl import prompts

class SiluetContextBuilder:
    """Builds LDCI context for Siluet from request data."""

    def __init__(self):
        self.context = ContextManager()

    def add_base_context(
        self,
        game_context: str = None,
        ai_profile: str = None
    ) -> "SiluetContextBuilder":
        """L1: Stable foundation - set once per session."""
        self.context.add(ContextLayer(
            layer=Layer.BASE,
            content=game_context or prompts.GAME_CONTEXT,
            inject_at=InjectTiming.SESSION_START,
            order=1,
        ))
        self.context.add(ContextLayer(
            layer=Layer.BASE,
            content=ai_profile or prompts.SILUET_PROFILE,
            inject_at=InjectTiming.SESSION_START,
            order=2,
        ))
        return self

    def add_player_progress(self, progress_json: str) -> "SiluetContextBuilder":
        """L2: Player progress - changes over session lifetime."""
        if progress_json and progress_json != "No player progress data":
            self.context.add(ContextLayer(
                layer=Layer.STATE,
                content=f"=== PLAYER PROGRESS ===\n{progress_json}",
                inject_at=InjectTiming.TURN_START,
                order=10,
            ))
        return self

    def add_room_context(self, room_json: str) -> "SiluetContextBuilder":
        """L2: Room context - changes when player moves rooms."""
        if room_json and room_json != "No room context":
            self.context.add(ContextLayer(
                layer=Layer.STATE,
                content=f"=== ROOM CONTEXT ===\n{room_json}",
                inject_at=InjectTiming.TURN_START,
                order=20,
            ))
        return self

    def add_visual_context(self, visual_json: str) -> "SiluetContextBuilder":
        """L2: Visual context - changes constantly as player looks around."""
        if visual_json and visual_json != "No visual context":
            self.context.add(ContextLayer(
                layer=Layer.STATE,
                content=f"=== VISUAL CONTEXT ===\n{visual_json}",
                inject_at=InjectTiming.TURN_START,
                order=30,
            ))
        return self

    def add_conversation_memory(self, memory: str) -> "SiluetContextBuilder":
        """L2: Conversation memory - grows over time."""
        if memory and memory != "No previous messages.":
            self.context.add(ContextLayer(
                layer=Layer.STATE,
                content=f"=== PAST CONVERSATION ===\n{memory}",
                inject_at=InjectTiming.TURN_START,
                order=40,
            ))
        return self

    def add_character_parameters(self, params_json: str) -> "SiluetContextBuilder":
        """L2: Character parameters - changes per request."""
        if params_json:
            self.context.add(ContextLayer(
                layer=Layer.STATE,
                content=f"=== BEHAVIORAL PARAMETERS ===\n{params_json}",
                inject_at=InjectTiming.TURN_START,
                order=50,
            ))
        return self

    def add_proactive_trigger(self, trigger: str) -> "SiluetContextBuilder":
        """L5: Proactive - AI-initiated speech."""
        if trigger:
            self.context.add(ContextLayer(
                layer=Layer.PROACTIVE,
                content=f"[Proactive Trigger: {trigger}]",
                inject_at=InjectTiming.ASAP,
            ))
        return self

    # --- Compilation Methods ---

    def compile_for_http(self) -> str:
        """HTTP: Return all layers compiled (timing ignored)."""
        return self.context.compile()

    def get_system_prompt(self) -> str:
        """S2S: Return base context for system_prompt."""
        return self.context.get_base()

    def get_turn_context(self) -> str:
        """S2S: Return state context for turn injection."""
        return self.context.compile_for(InjectTiming.TURN_START)

    def get_proactive_context(self) -> str:
        """S2S: Return proactive context for immediate injection."""
        return self.context.compile_for(InjectTiming.ASAP)
```

**Updated myllmservice.py:**

```python
from impl.context.siluet_builder import SiluetContextBuilder

def generate_siluet_answer(self, ...):
    # Build context using LDCI
    builder = SiluetContextBuilder()
    builder.add_base_context(game_context, ai_character_profile)
    builder.add_player_progress(player_progress)
    builder.add_room_context(room_context)
    builder.add_visual_context(visual_context)
    builder.add_conversation_memory(conversation_memory)
    builder.add_character_parameters(ai_character_response_parameters)

    if proactive_triggers:
        builder.add_proactive_trigger(proactive_triggers)

    # HTTP: Compile everything
    compiled_context = builder.compile_for_http()
    system_prompt = builder.get_system_prompt()

    # Build instructions (app's job, not LDCI)
    instructions = self._build_instructions(
        enable_audio_tags=enable_audio_tags,
        language=language,
        proactive=proactive_triggers,
        constraints=response_constraints,
    )

    # Assemble final prompt
    full_prompt = f"{system_prompt}\n\n{compiled_context}\n\n{instructions}"

    if player_input:
        full_prompt += f"\n\n=== PLAYER INPUT ===\n{player_input}"

    # Invoke LLM
    llm = self._get_llm(model)
    response = llm.invoke([HumanMessage(content=full_prompt)])
    return response.content
```

**Pros:**
- S2S-ready with timing metadata
- Clean separation of layers
- Testable context building
- Fluent builder API

**Cons:**
- More refactoring
- New abstraction to maintain

---

### Option C: Gradual Migration Path

```
Phase 1: Add ContextManager alongside StepContext
         - Use SiluetContextBuilder for new features
         - Keep StepContext for existing code
         - Test with debug logging to compare outputs

Phase 2: Migrate one context type at a time
         - Start with visual_context (changes most frequently)
         - Then room_context, player_progress, etc.
         - Verify outputs match at each step

Phase 3: Remove StepContext, use ContextManager only
         - Single source of truth
         - All context goes through LDCI
         - Ready for S2S

Phase 4: Add S2S support
         - Use compile_for(timing) for voice sessions
         - Keep HTTP using compile()
         - Inject on SPEECH_STARTED for voice
```

---

## Recommendation

**Recommended: Option B (Full LDCI with S2S Preparation)**

**Rationale:**
1. ChamberProtocol is moving toward S2S/voice (evidenced by `enable_audio_tags` feature)
2. LDCI provides the structure needed for dynamic context injection
3. The timing metadata (`InjectTiming`) will be immediately useful when S2S is added
4. Clean separation of context vs instructions aligns with LDCI design
5. The `SiluetContextBuilder` pattern is testable and maintainable

**Implementation Roadmap:**
1. Create `SiluetContextBuilder` using LDCI in `impl/context/`
2. Update `MyLLMService.generate_siluet_answer()` to use builder
3. Keep instructions separate (audio_tags, language, constraints)
4. Add tests comparing old vs new prompt outputs
5. When S2S is ready, use `compile_for(timing)` instead of `compile()`

**Success Metrics:**
- Same LLM outputs (regression test with saved prompts)
- Cleaner code (fewer string concatenations)
- Testable layers (unit test each context component)
- S2S-ready (timing metadata in place)

---

## Summary: Data Flow with LDCI

```
Unity Client (SiluetRequest)
         │
         ▼
SiluetService._process_request()
         │
         │  Serialize to strings
         ▼
SiluetContextBuilder
         │
         ├─ add_base_context()      → L1 Base (SESSION_START)
         ├─ add_player_progress()   → L2 State (TURN_START)
         ├─ add_room_context()      → L2 State (TURN_START)
         ├─ add_visual_context()    → L2 State (TURN_START)
         ├─ add_conversation_memory() → L2 State (TURN_START)
         ├─ add_character_parameters() → L2 State (TURN_START)
         └─ add_proactive_trigger() → L5 Proactive (ASAP)
         │
         ▼
┌─────────────────────────────────────┐
│  HTTP Mode:                         │
│  system_prompt = get_system_prompt()│
│  context = compile_for_http()       │
│  instructions = build_instructions()│
│  full_prompt = combine all          │
└─────────────────────────────────────┘
         │
         ▼
OpenAI API (HumanMessage)
         │
         ▼
Response → SiluetResponse

┌─────────────────────────────────────┐
│  S2S Mode (future):                 │
│  On connect:                        │
│    system_prompt = get_system_prompt()│
│  On SPEECH_STARTED:                 │
│    inject get_turn_context()        │
│  On proactive event:                │
│    inject get_proactive_context()   │
│    create_response()                │
└─────────────────────────────────────┘
```
