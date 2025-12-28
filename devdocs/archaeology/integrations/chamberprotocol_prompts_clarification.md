# ChamberProtocolAI prompts.py - Migration Clarification

**TL;DR:** `prompts.py` does NOT migrate to Chatforge. It stays in ChamberProtocolAI.

---

## What prompts.py Contains

```python
# ChamberProtocolAI/src/impl/prompts.py

SILUET_PROMPT_TEMPLATE = """
{game_context}

{siluet_profile}

{conversation_history}

{current_situation}

{player_action}

{constraints}

{response_format}
"""

GAME_CONTEXT = """
You are in a mysterious chamber filled with ancient artifacts...
[Game world lore]
"""

SILUET_PROFILE = """
You are Silüet, an enigmatic guide...
[Character personality, speech patterns, goals]
"""

def get_default_constraints():
    """Random word limits for variety."""
    return f"Respond in {random.randint(50, 150)} words."
```

---

## What StepContext.compile() Does

```python
# ChamberProtocolAI/src/schemas.py

class StepContext:
    game_context: str
    siluet_profile: str
    conversation_history: str
    current_situation: str
    player_action: str
    constraints: str
    response_format: str

    def compile(self) -> str:
        """Just string templating - fills in the slots."""
        return SILUET_PROMPT_TEMPLATE.format(
            game_context=self.game_context or GAME_CONTEXT,
            siluet_profile=self.siluet_profile or SILUET_PROFILE,
            conversation_history=self.conversation_history,
            current_situation=self.current_situation,
            player_action=self.player_action,
            constraints=self.constraints or get_default_constraints(),
            response_format=self.response_format or "Respond in character."
        )
```

This is **just string formatting** - `str.format()` with named placeholders. Nothing special.

---

## Why It Stays in ChamberProtocolAI

| Aspect | Explanation |
|--------|-------------|
| **Domain-specific** | Game lore, character personality, response formats are game logic |
| **Not reusable** | Other apps won't use Silüet's personality or Chamber's world |
| **Chatforge's scope** | Chatforge handles LLM calls and storage, not prompt authoring |
| **Separation of concerns** | App builds prompt → Chatforge sends to LLM → Chatforge stores result |

---

## The Integration Flow

```
ChamberProtocolAI                              Chatforge
─────────────────                              ─────────

1. Player sends message
        ↓
2. Build StepContext with:
   - game state
   - conversation history  ←───────────────── fetch from Message table
   - player action
        ↓
3. step_context.compile()
   → Returns compiled prompt string
        ↓
4. Call Chatforge LLM    ──────────────────→  LLM call via LangChain
        ↓                                            ↓
5. Get AI response       ←─────────────────── Response from GPT/Claude
        ↓
6. Store message         ──────────────────→  Save to Message table with
                                              generation_request_data={
                                                "prompt": compiled_prompt,
                                                "model": "gpt-4o-mini"
                                              }
        ↓
7. Return to player
```

---

## What Changes, What Stays

### Stays in ChamberProtocolAI (no changes)

```
src/impl/prompts.py          # All prompt templates
src/schemas.py               # StepContext dataclass
src/impl/services/chat/      # Game-specific service logic
```

### Uses Chatforge (new)

```python
# Before (ChamberProtocolAI's myllmservice.py)
from llmservice import BaseLLMService

class MyLLMService(BaseLLMService):
    def generate_siluet_answer(self, prompt: str) -> str:
        # Custom LLM call logic
        ...

# After (using Chatforge)
from chatforge.services.llm.factory import get_llm

class SiluetService:
    def __init__(self):
        self.llm = get_llm(provider="openai", model_name="gpt-4o-mini")

    def generate_siluet_answer(self, step_context: StepContext) -> str:
        prompt = step_context.compile()  # Still uses your prompts.py!
        response = self.llm.invoke(prompt)
        return response.content
```

---

## Summary

| Component | Location | Migration |
|-----------|----------|-----------|
| `prompts.py` | ChamberProtocolAI | **No migration** - stays as-is |
| `StepContext` | ChamberProtocolAI | **No migration** - stays as-is |
| `myllmservice.py` | ChamberProtocolAI | **Replace** with Chatforge's `get_llm()` |
| Message storage | ChamberProtocolAI | **Replace** with Chatforge's SQLAlchemy models |
| Chat/Participant models | ChamberProtocolAI | **Replace** with Chatforge's models |

**The prompt templates are your game's creative content. Chatforge is just the plumbing.**
