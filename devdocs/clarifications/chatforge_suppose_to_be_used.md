# How Chatforge is Supposed to Be Used
## A Practical Guide to Hexagonal Architecture with Chatforge

---

## Table of Contents

1. [What is Chatforge?](#what-is-chatforge)
2. [Hexagonal Architecture: What Does It Allow?](#hexagonal-architecture-what-does-it-allow)
3. [Why You Need Domain-Specific Adapters](#why-you-need-domain-specific-adapters)
4. [What is the Composition Root?](#what-is-the-composition-root)
5. [Backend Code Organization](#backend-code-organization)
6. [Complete Example: ChamberProtocolAI](#complete-example-chamberprotocolai)
7. [Common Mistakes to Avoid](#common-mistakes-to-avoid)
8. [Testing Strategy](#testing-strategy)

---

## What is Chatforge?

**Chatforge is NOT your application. Chatforge is a LIBRARY that provides infrastructure components.**

Think of chatforge as a toolbox:
- 🔌 **Ports** (interfaces) - Contracts for LLM, Storage, Agent, etc.
- 🔧 **Adapters** (implementations) - OpenAI, Anthropic, SQLite, PostgreSQL, etc.
- 📦 **Data Models** - LLMRequest, LLMResponse, TokenUsage, etc.

**Your application (e.g., ChamberProtocolAI) uses chatforge, but contains its own domain logic.**

```
┌─────────────────────────────────────────────────────┐
│        YOUR APPLICATION (ChamberProtocolAI)         │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  Domain Logic (NPCs, Quests, Combat)       │    │
│  │  - NPCController                           │    │
│  │  - QuestEngine                             │    │
│  │  - CombatSystem                            │    │
│  └────────────────────────────────────────────┘    │
│                      ▲                              │
│                      │ uses                         │
│                      │                              │
│  ┌────────────────────────────────────────────┐    │
│  │         Chatforge Library                   │    │
│  │  - LLMPort, StoragePort                    │    │
│  │  - OpenAIAdapter, SQLiteAdapter            │    │
│  │  - LLMRequest, LLMResponse                 │    │
│  └────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

---

## Hexagonal Architecture: What Does It Allow?

Hexagonal architecture (also called Ports & Adapters) allows you to:

### 1. **Swap Infrastructure Without Changing Domain Logic**

**Example:** Switch from OpenAI to Anthropic

```python
# Before (using OpenAI)
def create_llm() -> LLMPort:
    return OpenAILLMAdapter(api_key="sk-...")

# After (using Anthropic) - ONE line change
def create_llm() -> LLMPort:
    return AnthropicLLMAdapter(api_key="sk-ant-...")

# Your NPCController code doesn't change at all!
# It depends on LLMPort (interface), not OpenAIAdapter (implementation)
```

### 2. **Test Domain Logic in Isolation**

```python
# Production: Use real OpenAI
npc_controller = NPCController(llm=OpenAILLMAdapter(...))

# Testing: Use mock LLM (fast, free, deterministic)
npc_controller = NPCController(llm=MockLLMAdapter(
    mock_response="I have healing potions for 50 gold"
))

# Same NPCController, different infrastructure!
```

### 3. **Defer Infrastructure Decisions**

You can build your entire game logic (NPC conversations, quest system, combat) **before** deciding:
- Which LLM provider to use (OpenAI? Anthropic? Local model?)
- Which database to use (SQLite? PostgreSQL? MongoDB?)
- Which deployment platform (AWS? GCP? On-premise?)

Your core logic depends on **interfaces** (LLMPort, StoragePort), not implementations.

### 4. **Prevent Vendor Lock-In**

```python
# Your domain logic:
class NPCController:
    def __init__(self, llm: LLMPort):  # ← Depends on interface
        self.llm = llm

# NOT like this:
class NPCController:
    def __init__(self):
        self.llm = ChatOpenAI(...)  # ← Locked to OpenAI! ❌
```

If OpenAI raises prices or shuts down, you can switch to another provider by changing **one file** (composition root), not hundreds of files.

### 5. **Allow Multiple Implementations to Coexist**

```python
# Use different LLM providers for different purposes
class GameEngine:
    def __init__(
        self,
        npc_llm: LLMPort,      # Cheap model for NPCs (gpt-4o-mini)
        quest_llm: LLMPort,    # Smart model for quest generation (claude-3.5-sonnet)
        combat_llm: LLMPort    # Fast local model for combat narration
    ):
        self.npc_controller = NPCController(llm=npc_llm)
        self.quest_engine = QuestEngine(llm=quest_llm)
        self.combat_system = CombatSystem(llm=combat_llm)
```

Each component uses the same **interface** (LLMPort) but different **implementations**.

### 6. **Enable Progressive Enhancement**

Start simple, add complexity later:

```python
# Week 1: Start with in-memory storage (fast, simple)
storage = InMemoryStorageAdapter()

# Week 4: Switch to SQLite (persistent, still simple)
storage = SQLiteStorageAdapter(db_path="./game.db")

# Week 12: Switch to PostgreSQL (scalable, production-ready)
storage = PostgreSQLStorageAdapter(connection_string="postgresql://...")

# Your domain logic never changes!
```

---

## Why You Need Domain-Specific Adapters

### The Common Mistake

Many developers think: "Chatforge has OpenAILLMAdapter, so I'll just use it directly!"

```python
# ❌ WRONG: Using chatforge adapters directly in domain logic
class NPCController:
    def __init__(self):
        from chatforge.adapters.llm import OpenAILLMAdapter
        self.llm = OpenAILLMAdapter(api_key="sk-...")
```

**Problem:** This couples your domain logic to chatforge's adapter. What if:
- You need to add custom logic (e.g., log every NPC conversation to analytics)
- You need to apply NPC-specific prompts/formatting
- You want to A/B test different providers per NPC type

### The Correct Approach: Domain-Specific Adapters

**Create adapters in YOUR application that wrap chatforge adapters:**

```python
# chamberprotocol/adapters/npc_llm_adapter.py
from chatforge.ports import LLMPort
from chatforge.adapters.llm import OpenAILLMAdapter
from chamberprotocol.core.analytics import log_npc_interaction

class NPCLLMAdapter(LLMPort):
    """
    Domain-specific adapter for NPC conversations.

    Wraps chatforge's LLM adapter with game-specific logic:
    - Adds NPC personality context
    - Logs interactions to analytics
    - Applies content filtering
    """

    def __init__(self, base_llm: LLMPort, analytics_service: AnalyticsService):
        self.base_llm = base_llm  # Chatforge adapter (OpenAI, Anthropic, etc.)
        self.analytics = analytics_service

    async def generate(self, request: LLMRequest) -> LLMResponse:
        # Add game-specific context
        request = self._add_npc_context(request)

        # Call base LLM (chatforge adapter)
        response = await self.base_llm.generate(request)

        # Log to analytics (domain logic)
        await self.analytics.log_npc_interaction(
            npc_id=request.metadata.get("npc_id"),
            player_message=request.messages[-1].content,
            npc_response=response.content,
            cost=response.cost.total_cost
        )

        # Apply content filtering (domain logic)
        response.content = self._filter_inappropriate_content(response.content)

        return response

    def _add_npc_context(self, request: LLMRequest) -> LLMRequest:
        """Add game-specific NPC personality system message"""
        # Domain logic: Get NPC personality from game state
        npc_id = request.metadata.get("npc_id")
        personality = self._get_npc_personality(npc_id)

        # Prepend system message
        request.messages.insert(0, LLMMessage(
            role="system",
            content=personality
        ))
        return request
```

**Benefits:**
1. ✅ Domain logic (NPC personalities, analytics) stays in your application
2. ✅ Chatforge remains a generic library
3. ✅ You can still swap OpenAI for Anthropic (just change base_llm)
4. ✅ Testing is easier (mock NPCLLMAdapter, not chatforge internals)

### When to Create Domain-Specific Adapters

**Create a domain adapter when you need:**
- **Custom preprocessing** - Add context, format prompts, inject system messages
- **Custom postprocessing** - Parse responses, extract structured data, apply filters
- **Domain-specific tracking** - Log to analytics, track domain metrics
- **Business rules** - Content filtering, rate limiting per user type, cost controls
- **Error handling** - Retry logic specific to your use case
- **A/B testing** - Route to different providers based on experiments

**Example use cases:**
```python
# Different adapters for different domain needs:
NPCLLMAdapter          # NPC conversations (add personality, log interactions)
QuestGeneratorAdapter  # Quest generation (structured output, validation)
CombatNarratorAdapter  # Combat narration (low latency, streaming)
PlayerCommandAdapter   # Player commands (intent classification, tool use)
```

---

## What is the Composition Root?

### Definition

The **composition root** is the **single place** in your application where:
1. You instantiate all adapters (infrastructure)
2. You wire them together (dependency injection)
3. You hand the composed object graph to your application

It's called the **"root"** because it's at the top of your application startup - the entry point where all dependencies are resolved.

### Why Only ONE Composition Root?

**Good** ✅ - One composition root
```python
# main.py (composition root)
def main():
    # 1. Create adapters
    openai = OpenAILLMAdapter(...)
    analytics = AnalyticsService(...)

    # 2. Compose domain adapters
    npc_llm = NPCLLMAdapter(base_llm=openai, analytics=analytics)

    # 3. Compose domain logic
    npc_controller = NPCController(llm=npc_llm)

    # 4. Run application
    app.run(npc_controller)
```

**Bad** ❌ - Multiple composition points scattered
```python
# npc_controller.py
class NPCController:
    def __init__(self):
        self.llm = OpenAILLMAdapter(...)  # ← Composition here! Bad!

# quest_engine.py
class QuestEngine:
    def __init__(self):
        self.llm = OpenAILLMAdapter(...)  # ← Composition here! Bad!
```

**Why is scattered composition bad?**
- Hard to test (can't inject mocks)
- Hard to configure (settings scattered everywhere)
- Hard to change (must modify every class)
- Impossible to reuse (tightly coupled)

### Composition Root Examples

#### Example 1: Simple CLI Application

```python
# chamberprotocol/cli/main.py
import asyncio
from chatforge.adapters.llm import OpenAILLMAdapter
from chatforge.adapters.storage import SQLiteStorageAdapter
from chamberprotocol.adapters import NPCLLMAdapter
from chamberprotocol.core import NPCController, AnalyticsService

async def main():
    """
    COMPOSITION ROOT for CLI application.

    This is THE ONLY PLACE that knows:
    - We're using OpenAI
    - We're using SQLite
    - How everything is wired together
    """

    # ═══════════════════════════════════════════════════════
    # 1. INFRASTRUCTURE LAYER - Create chatforge adapters
    # ═══════════════════════════════════════════════════════
    base_llm = OpenAILLMAdapter(
        api_key=os.getenv("OPENAI_API_KEY"),
        default_model="gpt-4o-mini"
    )

    storage = SQLiteStorageAdapter(
        db_path="./game_data.db"
    )

    # ═══════════════════════════════════════════════════════
    # 2. DOMAIN SERVICES
    # ═══════════════════════════════════════════════════════
    analytics = AnalyticsService(storage=storage)

    # ═══════════════════════════════════════════════════════
    # 3. DOMAIN ADAPTERS - Wrap chatforge adapters
    # ═══════════════════════════════════════════════════════
    npc_llm = NPCLLMAdapter(
        base_llm=base_llm,
        analytics=analytics
    )

    # ═══════════════════════════════════════════════════════
    # 4. CORE DOMAIN LOGIC - Inject all dependencies
    # ═══════════════════════════════════════════════════════
    npc_controller = NPCController(
        llm=npc_llm,
        storage=storage
    )

    # ═══════════════════════════════════════════════════════
    # 5. RUN APPLICATION
    # ═══════════════════════════════════════════════════════
    print("Welcome to Chamber Protocol!")
    while True:
        npc_id = input("NPC ID: ")
        message = input("You: ")

        response = await npc_controller.talk_to_npc(npc_id, message)
        print(f"NPC: {response}")

if __name__ == "__main__":
    asyncio.run(main())
```

#### Example 2: FastAPI Application with Dependency Injection

```python
# chamberprotocol/api/app.py
from fastapi import FastAPI, Depends
from chatforge.ports import LLMPort, StoragePort
from chatforge.adapters.llm import OpenAILLMAdapter
from chatforge.adapters.storage import PostgreSQLStorageAdapter
from chamberprotocol.adapters import NPCLLMAdapter
from chamberprotocol.core import NPCController, AnalyticsService

app = FastAPI()

# ═══════════════════════════════════════════════════════════════
# COMPOSITION ROOT - Dependency Injection Functions
# ═══════════════════════════════════════════════════════════════

# --- Infrastructure Layer (Chatforge Adapters) ---

def get_base_llm() -> LLMPort:
    """Create base LLM adapter (chatforge)"""
    return OpenAILLMAdapter(
        api_key=os.getenv("OPENAI_API_KEY"),
        default_model="gpt-4o-mini"
    )

def get_storage() -> StoragePort:
    """Create storage adapter (chatforge)"""
    return PostgreSQLStorageAdapter(
        connection_string=os.getenv("DATABASE_URL")
    )

# --- Domain Services ---

def get_analytics(storage: StoragePort = Depends(get_storage)) -> AnalyticsService:
    """Create analytics service"""
    return AnalyticsService(storage=storage)

# --- Domain Adapters ---

def get_npc_llm(
    base_llm: LLMPort = Depends(get_base_llm),
    analytics: AnalyticsService = Depends(get_analytics)
) -> NPCLLMAdapter:
    """Create domain-specific NPC LLM adapter"""
    return NPCLLMAdapter(base_llm=base_llm, analytics=analytics)

# --- Core Domain Logic ---

def get_npc_controller(
    llm: NPCLLMAdapter = Depends(get_npc_llm),
    storage: StoragePort = Depends(get_storage)
) -> NPCController:
    """Create NPC controller with all dependencies injected"""
    return NPCController(llm=llm, storage=storage)

# ═══════════════════════════════════════════════════════════════
# API ROUTES - Use domain logic via dependency injection
# ═══════════════════════════════════════════════════════════════

@app.post("/npc/talk")
async def talk_to_npc(
    npc_id: str,
    message: str,
    controller: NPCController = Depends(get_npc_controller)  # ← Fully wired!
):
    """
    API endpoint receives a fully-composed NPCController.

    It doesn't know or care about:
    - Which LLM provider we're using
    - Which database we're using
    - How analytics works

    All of that is handled in the composition root above.
    """
    response = await controller.talk_to_npc(npc_id, message)
    return {"npc_response": response}


@app.get("/health")
async def health_check(
    storage: StoragePort = Depends(get_storage)
):
    """Health check - can access infrastructure directly if needed"""
    await storage.ping()  # Check database connection
    return {"status": "healthy"}
```

**Key insight:** The dependency injection functions (`get_base_llm`, `get_npc_llm`, etc.) **ARE** the composition root. FastAPI calls them automatically.

### Composition Root Rules

1. **ONE composition root per application** (CLI, API, etc.)
2. **Composition root knows EVERYTHING** (all concrete implementations)
3. **Rest of the code knows NOTHING** (only interfaces)
4. **All dependencies flow ONE WAY** (from composition root → core)

---

## Backend Code Organization

### Directory Structure for Maximum Cohesion

```
chamberprotocol/                    # Your application root
│
├── pyproject.toml                  # Dependencies
├── .env                            # Environment variables (API keys, DB URLs)
├── .env.example                    # Example environment config
│
├── chamberprotocol/                # Main package
│   │
│   ├── __init__.py
│   │
│   ├── core/                       # ⭐ DOMAIN LOGIC (No framework dependencies!)
│   │   ├── __init__.py
│   │   ├── npc_controller.py       # NPC conversation logic
│   │   ├── quest_engine.py         # Quest generation logic
│   │   ├── combat_system.py        # Combat resolution logic
│   │   ├── world_state.py          # Game world state management
│   │   └── analytics.py            # Analytics service
│   │
│   ├── models/                     # 📦 DOMAIN MODELS (Pure dataclasses)
│   │   ├── __init__.py
│   │   ├── npc.py                  # NPC, NPCPersonality, NPCState
│   │   ├── quest.py                # Quest, QuestStage, QuestReward
│   │   ├── player.py               # Player, Inventory, Stats
│   │   └── world.py                # Location, Region, WorldEvent
│   │
│   ├── adapters/                   # 🔧 DOMAIN-SPECIFIC ADAPTERS
│   │   ├── __init__.py
│   │   ├── npc_llm_adapter.py      # Wraps chatforge LLM for NPC logic
│   │   ├── quest_llm_adapter.py    # Wraps chatforge LLM for quest generation
│   │   ├── combat_narrator.py      # Wraps chatforge LLM for combat narration
│   │   └── game_storage_adapter.py # Wraps chatforge storage for game state
│   │
│   ├── api/                        # 🌐 FASTAPI APPLICATION (Composition root)
│   │   ├── __init__.py
│   │   ├── app.py                  # FastAPI app + DI setup (COMPOSITION ROOT!)
│   │   ├── dependencies.py         # Dependency injection functions
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── npc_routes.py       # POST /npc/talk, GET /npc/{id}
│   │   │   ├── quest_routes.py     # POST /quest/generate, GET /quest/{id}
│   │   │   └── health_routes.py    # GET /health
│   │   └── middleware/
│   │       ├── auth_middleware.py  # Authentication
│   │       └── rate_limit.py       # Rate limiting
│   │
│   ├── cli/                        # 🖥️ CLI APPLICATION (Composition root)
│   │   ├── __init__.py
│   │   └── main.py                 # CLI entry point (COMPOSITION ROOT!)
│   │
│   ├── config/                     # ⚙️ CONFIGURATION
│   │   ├── __init__.py
│   │   └── settings.py             # Pydantic settings (from .env)
│   │
│   └── utils/                      # 🛠️ SHARED UTILITIES
│       ├── __init__.py
│       ├── logger.py               # Logging setup
│       └── exceptions.py           # Custom exceptions
│
├── tests/                          # 🧪 TESTS (Mirror source structure)
│   ├── conftest.py                 # Shared fixtures
│   ├── unit/
│   │   ├── core/
│   │   │   ├── test_npc_controller.py
│   │   │   ├── test_quest_engine.py
│   │   │   └── test_combat_system.py
│   │   └── adapters/
│   │       ├── test_npc_llm_adapter.py
│   │       └── test_quest_llm_adapter.py
│   ├── integration/
│   │   ├── test_npc_conversation_flow.py
│   │   └── test_quest_generation_flow.py
│   └── e2e/
│       └── test_full_game_session.py
│
├── migrations/                     # 📊 DATABASE MIGRATIONS (Alembic)
│   ├── versions/
│   └── env.py
│
├── scripts/                        # 📜 UTILITY SCRIPTS
│   ├── seed_database.py            # Populate initial data
│   └── benchmark_llm.py            # Performance testing
│
└── docs/                           # 📚 DOCUMENTATION
    ├── architecture.md
    ├── api_reference.md
    └── deployment.md
```

### Layer Responsibilities

#### 1. Core (`chamberprotocol/core/`)

**Purpose:** Business logic, domain rules, use cases

**Rules:**
- ✅ Can import from: `models/`, `chatforge.ports`, standard library
- ❌ CANNOT import from: `adapters/`, `api/`, `cli/`, `chatforge.adapters`
- ❌ NO framework dependencies (FastAPI, SQLAlchemy, LangChain)
- ❌ NO direct API calls, file I/O, database queries

**Example:**
```python
# chamberprotocol/core/npc_controller.py
from chatforge.ports import LLMPort, StoragePort  # ← Interfaces only!
from chamberprotocol.models import NPC, NPCState

class NPCController:
    def __init__(self, llm: LLMPort, storage: StoragePort):
        self.llm = llm
        self.storage = storage

    async def talk_to_npc(self, npc_id: str, message: str) -> str:
        # Pure business logic - no infrastructure details!
        pass
```

#### 2. Models (`chamberprotocol/models/`)

**Purpose:** Domain entities, value objects

**Rules:**
- ✅ Pure dataclasses with no external dependencies
- ✅ Business validation logic (`__post_init__`, validators)
- ❌ NO persistence logic (no database save/load)
- ❌ NO framework dependencies

**Example:**
```python
# chamberprotocol/models/npc.py
from dataclasses import dataclass
from enum import Enum

class NPCPersonality(Enum):
    FRIENDLY = "friendly"
    HOSTILE = "hostile"
    MYSTERIOUS = "mysterious"

@dataclass
class NPC:
    id: str
    name: str
    personality: NPCPersonality

    def __post_init__(self):
        if not self.name:
            raise ValueError("NPC must have a name")
```

#### 3. Adapters (`chamberprotocol/adapters/`)

**Purpose:** Domain-specific wrappers around chatforge adapters

**Rules:**
- ✅ Can import from: `chatforge.ports`, `chatforge.adapters`, `core/`, `models/`
- ✅ Add domain-specific logic (analytics, logging, formatting)
- ✅ Implement chatforge ports (LLMPort, StoragePort, etc.)

**Example:**
```python
# chamberprotocol/adapters/npc_llm_adapter.py
from chatforge.ports import LLMPort
from chatforge.llm.request import LLMRequest
from chatforge.llm.response import LLMResponse

class NPCLLMAdapter(LLMPort):
    def __init__(self, base_llm: LLMPort, analytics: AnalyticsService):
        self.base_llm = base_llm  # Chatforge adapter
        self.analytics = analytics

    async def generate(self, request: LLMRequest) -> LLMResponse:
        # Add domain logic
        request = self._add_npc_personality(request)
        response = await self.base_llm.generate(request)
        await self.analytics.log_interaction(request, response)
        return response
```

#### 4. API (`chamberprotocol/api/`)

**Purpose:** FastAPI routes, HTTP layer, composition root

**Rules:**
- ✅ Defines HTTP endpoints
- ✅ Handles request/response serialization
- ✅ **Contains composition root** (dependency injection)
- ✅ Can import from: `core/`, `adapters/`, `models/`, `chatforge`

**Example:**
```python
# chamberprotocol/api/app.py
from fastapi import FastAPI, Depends
from chamberprotocol.api.dependencies import get_npc_controller

app = FastAPI()

@app.post("/npc/talk")
async def talk(
    npc_id: str,
    message: str,
    controller = Depends(get_npc_controller)  # ← Composition root!
):
    return await controller.talk_to_npc(npc_id, message)
```

#### 5. CLI (`chamberprotocol/cli/`)

**Purpose:** Command-line interface, composition root

**Rules:**
- ✅ **Contains composition root** for CLI mode
- ✅ Can import from: `core/`, `adapters/`, `models/`, `chatforge`

**Example:**
```python
# chamberprotocol/cli/main.py
async def main():
    # Composition root for CLI
    llm = OpenAILLMAdapter(...)
    controller = NPCController(llm=llm)

    # CLI loop
    while True:
        message = input("You: ")
        response = await controller.talk_to_npc("merchant", message)
        print(f"NPC: {response}")
```

---

## Complete Example: ChamberProtocolAI

### Step-by-Step Implementation

#### Step 1: Define Domain Models

```python
# chamberprotocol/models/npc.py
from dataclasses import dataclass
from enum import Enum

class NPCMood(Enum):
    HAPPY = "happy"
    NEUTRAL = "neutral"
    ANGRY = "angry"

@dataclass
class NPC:
    id: str
    name: str
    personality: str  # System prompt
    mood: NPCMood = NPCMood.NEUTRAL

    def get_system_prompt(self) -> str:
        mood_modifier = {
            NPCMood.HAPPY: "You are in a cheerful mood.",
            NPCMood.NEUTRAL: "",
            NPCMood.ANGRY: "You are irritated and short-tempered."
        }
        return f"{self.personality}\n{mood_modifier[self.mood]}"
```

#### Step 2: Define Core Domain Logic

```python
# chamberprotocol/core/npc_controller.py
from chatforge.ports import LLMPort, StoragePort
from chatforge.llm.request import LLMRequest, LLMMessage
from chamberprotocol.models import NPC, NPCMood

class NPCController:
    """Core domain logic for NPC conversations"""

    def __init__(self, llm: LLMPort, storage: StoragePort):
        self.llm = llm
        self.storage = storage

    async def talk_to_npc(self, npc: NPC, player_message: str) -> str:
        """
        Business logic: Handle NPC conversation.

        This is framework-agnostic - no OpenAI, FastAPI, or SQLite code here!
        """
        # 1. Load conversation history
        conversation_id = f"npc_{npc.id}"
        history = await self.storage.load_conversation(conversation_id)

        # 2. Build LLM request with game context
        messages = [
            LLMMessage(role="system", content=npc.get_system_prompt()),
            *history,
            LLMMessage(role="user", content=player_message)
        ]

        request = LLMRequest(
            messages=messages,
            temperature=0.8,  # Higher for creative NPC responses
            max_tokens=150,
            operation_name=f"npc_talk_{npc.id}",
            metadata={"npc_id": npc.id, "npc_name": npc.name}
        )

        # 3. Generate response via LLM port
        response = await self.llm.generate(request)

        # 4. Save conversation via storage port
        await self.storage.save_message(
            conversation_id=conversation_id,
            role="user",
            content=player_message
        )
        await self.storage.save_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response.content
        )

        # 5. Update NPC mood based on conversation (domain logic)
        npc.mood = self._determine_mood(player_message, response.content)

        return response.content

    def _determine_mood(self, player_msg: str, npc_response: str) -> NPCMood:
        """Domain logic: Determine NPC mood from conversation"""
        # Simplified - in real game, use sentiment analysis
        if "thank you" in player_msg.lower():
            return NPCMood.HAPPY
        elif any(word in player_msg.lower() for word in ["attack", "fight", "die"]):
            return NPCMood.ANGRY
        return NPCMood.NEUTRAL
```

#### Step 3: Create Domain-Specific Adapter

```python
# chamberprotocol/adapters/npc_llm_adapter.py
from chatforge.ports import LLMPort
from chatforge.llm.request import LLMRequest
from chatforge.llm.response import LLMResponse
from chamberprotocol.core.analytics import AnalyticsService

class NPCLLMAdapter(LLMPort):
    """Domain-specific LLM adapter for NPC conversations"""

    def __init__(self, base_llm: LLMPort, analytics: AnalyticsService):
        self.base_llm = base_llm  # Chatforge adapter (OpenAI, Anthropic, etc.)
        self.analytics = analytics

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Add NPC-specific tracking and analytics"""

        # Call base LLM
        response = await self.base_llm.generate(request)

        # Log analytics (domain-specific logic)
        await self.analytics.log_npc_interaction(
            npc_id=request.metadata.get("npc_id"),
            npc_name=request.metadata.get("npc_name"),
            player_message=request.messages[-1].content,
            npc_response=response.content,
            tokens_used=response.usage.total_tokens,
            cost=response.cost.total_cost,
            model=response.model
        )

        return response

    async def generate_stream(self, request: LLMRequest):
        """Streaming not needed for NPCs"""
        raise NotImplementedError("NPCs don't support streaming")
```

#### Step 4: Composition Root (FastAPI)

```python
# chamberprotocol/api/dependencies.py
"""Composition root - dependency injection for FastAPI"""

from functools import lru_cache
from chatforge.ports import LLMPort, StoragePort
from chatforge.adapters.llm import OpenAILLMAdapter
from chatforge.adapters.storage import SQLiteStorageAdapter
from chamberprotocol.adapters import NPCLLMAdapter
from chamberprotocol.core import NPCController, AnalyticsService
from chamberprotocol.config import settings

# ═══════════════════════════════════════════════════════════════
# Infrastructure Layer (Singletons)
# ═══════════════════════════════════════════════════════════════

@lru_cache()
def get_base_llm() -> LLMPort:
    """Create base LLM adapter (chatforge) - singleton"""
    return OpenAILLMAdapter(
        api_key=settings.OPENAI_API_KEY,
        default_model=settings.DEFAULT_LLM_MODEL
    )

@lru_cache()
def get_storage() -> StoragePort:
    """Create storage adapter (chatforge) - singleton"""
    return SQLiteStorageAdapter(
        db_path=settings.DATABASE_PATH
    )

# ═══════════════════════════════════════════════════════════════
# Domain Services (Singletons)
# ═══════════════════════════════════════════════════════════════

@lru_cache()
def get_analytics() -> AnalyticsService:
    """Create analytics service - singleton"""
    return AnalyticsService(storage=get_storage())

# ═══════════════════════════════════════════════════════════════
# Domain Adapters (Per-request)
# ═══════════════════════════════════════════════════════════════

def get_npc_llm() -> NPCLLMAdapter:
    """Create NPC LLM adapter with injected dependencies"""
    return NPCLLMAdapter(
        base_llm=get_base_llm(),
        analytics=get_analytics()
    )

# ═══════════════════════════════════════════════════════════════
# Core Domain Logic (Per-request)
# ═══════════════════════════════════════════════════════════════

def get_npc_controller() -> NPCController:
    """Create NPC controller with all dependencies injected"""
    return NPCController(
        llm=get_npc_llm(),
        storage=get_storage()
    )
```

```python
# chamberprotocol/api/app.py
from fastapi import FastAPI, Depends
from chamberprotocol.api.dependencies import get_npc_controller
from chamberprotocol.core import NPCController
from chamberprotocol.models import NPC, NPCMood

app = FastAPI(title="Chamber Protocol AI")

@app.post("/npc/talk")
async def talk_to_npc(
    npc_id: str,
    message: str,
    controller: NPCController = Depends(get_npc_controller)
):
    """Talk to an NPC"""
    # Load NPC from database (simplified)
    npc = NPC(
        id=npc_id,
        name="Merchant Bob",
        personality="You are a cheerful merchant in a fantasy tavern.",
        mood=NPCMood.NEUTRAL
    )

    response = await controller.talk_to_npc(npc, message)

    return {
        "npc_id": npc.id,
        "npc_name": npc.name,
        "npc_mood": npc.mood.value,
        "response": response
    }
```

#### Step 5: Configuration

```python
# chamberprotocol/config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings from environment"""

    # LLM Configuration
    OPENAI_API_KEY: str
    DEFAULT_LLM_MODEL: str = "gpt-4o-mini"

    # Database Configuration
    DATABASE_PATH: str = "./chamber_game.db"

    # Application Configuration
    DEBUG: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
```

```bash
# .env
OPENAI_API_KEY=sk-...
DEFAULT_LLM_MODEL=gpt-4o-mini
DATABASE_PATH=./chamber_game.db
DEBUG=true
```

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Using Chatforge Adapters Directly in Core

```python
# BAD ❌
class NPCController:
    def __init__(self):
        from chatforge.adapters.llm import OpenAILLMAdapter
        self.llm = OpenAILLMAdapter(...)  # ← Tight coupling!
```

**Fix:** Use dependency injection with interfaces
```python
# GOOD ✅
class NPCController:
    def __init__(self, llm: LLMPort):  # ← Depends on interface
        self.llm = llm
```

### ❌ Mistake 2: Multiple Composition Roots

```python
# BAD ❌ - Composition scattered everywhere
# file1.py
llm = OpenAILLMAdapter(...)

# file2.py
llm = OpenAILLMAdapter(...)

# file3.py
llm = OpenAILLMAdapter(...)
```

**Fix:** One composition root
```python
# GOOD ✅ - Single composition root
# dependencies.py
@lru_cache()
def get_llm() -> LLMPort:
    return OpenAILLMAdapter(...)  # Created once, reused everywhere
```

### ❌ Mistake 3: Framework Dependencies in Core

```python
# BAD ❌
from fastapi import HTTPException

class NPCController:
    async def talk_to_npc(self, ...):
        if not npc_id:
            raise HTTPException(400, "Missing NPC ID")  # ← FastAPI in core!
```

**Fix:** Use domain exceptions
```python
# GOOD ✅
class NPCNotFoundError(Exception):
    pass

class NPCController:
    async def talk_to_npc(self, ...):
        if not npc_id:
            raise NPCNotFoundError(f"NPC {npc_id} not found")

# Convert to HTTP error in API layer
@app.post("/npc/talk")
async def talk(npc_id: str, controller = Depends(get_npc_controller)):
    try:
        return await controller.talk_to_npc(npc_id, message)
    except NPCNotFoundError as e:
        raise HTTPException(404, str(e))
```

### ❌ Mistake 4: Skipping Domain Adapters

```python
# BAD ❌ - Using chatforge adapter directly
controller = NPCController(llm=OpenAILLMAdapter(...))  # No domain logic!
```

**Fix:** Wrap in domain adapter
```python
# GOOD ✅
base_llm = OpenAILLMAdapter(...)
npc_llm = NPCLLMAdapter(base_llm=base_llm, analytics=analytics)
controller = NPCController(llm=npc_llm)  # Domain-specific logic included!
```

---

## Testing Strategy

### Unit Tests: Test Core in Isolation

```python
# tests/unit/core/test_npc_controller.py
import pytest
from chamberprotocol.core import NPCController
from chamberprotocol.models import NPC, NPCMood

class MockLLM(LLMPort):
    """Mock LLM for testing"""
    async def generate(self, request):
        return LLMResponse(
            success=True,
            content="I have healing potions for 50 gold.",
            trace_id="test"
        )

class MockStorage(StoragePort):
    """Mock storage for testing"""
    async def save_message(self, *args): pass
    async def load_conversation(self, *args): return []

@pytest.mark.asyncio
async def test_npc_conversation():
    # Arrange
    controller = NPCController(
        llm=MockLLM(),
        storage=MockStorage()
    )
    npc = NPC(id="merchant", name="Bob", personality="Friendly merchant")

    # Act
    response = await controller.talk_to_npc(npc, "Do you have potions?")

    # Assert
    assert "potions" in response.lower()
    assert npc.mood == NPCMood.NEUTRAL
```

### Integration Tests: Test with Real Adapters

```python
# tests/integration/test_npc_flow.py
@pytest.mark.integration
@pytest.mark.asyncio
async def test_npc_conversation_with_real_llm():
    # Use real chatforge adapters
    llm = OpenAILLMAdapter(api_key=os.getenv("OPENAI_API_KEY"))
    storage = SQLiteStorageAdapter(db_path=":memory:")

    controller = NPCController(llm=llm, storage=storage)
    npc = NPC(id="merchant", name="Bob", personality="Friendly merchant")

    response = await controller.talk_to_npc(npc, "Hello!")

    assert response  # Got a response
    assert len(response) > 0
```

---

## Summary: The Golden Rules

1. **Chatforge is a LIBRARY, not your application** - It provides ports and adapters
2. **Core depends on INTERFACES (ports), not IMPLEMENTATIONS (adapters)** - Enables swapping
3. **Create DOMAIN-SPECIFIC ADAPTERS** - Wrap chatforge adapters with your business logic
4. **ONE COMPOSITION ROOT** - Wire everything together in one place (main.py or dependencies.py)
5. **Keep core FRAMEWORK-AGNOSTIC** - No FastAPI, LangChain, or SQLAlchemy in core/
6. **Test core in ISOLATION** - Use mocks, test domain logic independently

This architecture allows you to:
- ✅ Swap LLM providers (OpenAI → Anthropic)
- ✅ Swap databases (SQLite → PostgreSQL)
- ✅ Test easily (mock ports)
- ✅ Deploy anywhere (CLI, API, AWS Lambda)
- ✅ Evolve independently (core vs infrastructure)
