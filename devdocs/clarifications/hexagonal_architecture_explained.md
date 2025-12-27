# Hexagonal Architecture: Where Does the Application Live?

## The Question

> "Where does the main application live exactly? It just uses ports? In the example of ChamberProtocol using chatforge, where do the operations match exactly? Like okay, we use LLMPort and StoragePort, where are they connected? And how are they connected?"

## TL;DR Answer

1. **The "main application" (domain logic) lives in the CORE** - it's YOUR business logic that uses ports
2. **Ports are ABSTRACT INTERFACES** - they live at the boundary between core and adapters
3. **Adapters IMPLEMENT ports** - they live in the outer layer (infrastructure)
4. **Ports are CONNECTED at the COMPOSITION ROOT** - typically at application startup (dependency injection)

---

## The Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     INFRASTRUCTURE                           │
│  (Frameworks, Databases, APIs, CLI, Web Servers)            │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              ADAPTERS (Implementations)             │    │
│  │  OpenAILLMAdapter, SQLiteStorageAdapter, etc.      │    │
│  │                                                      │    │
│  │  ┌──────────────────────────────────────────┐      │    │
│  │  │         PORTS (Interfaces)                │      │    │
│  │  │  LLMPort, StoragePort, AgentPort          │      │    │
│  │  │                                            │      │    │
│  │  │  ┌────────────────────────────────┐      │      │    │
│  │  │  │    CORE (Domain Logic)          │      │      │    │
│  │  │  │  YOUR APPLICATION LIVES HERE    │      │      │    │
│  │  │  │                                  │      │      │    │
│  │  │  │  - ChamberGame                  │      │      │    │
│  │  │  │  - NPCController                │      │      │    │
│  │  │  │  - ConversationManager          │      │      │    │
│  │  │  │  - QuestEngine                  │      │      │    │
│  │  │  │                                  │      │      │    │
│  │  │  └────────────────────────────────┘      │      │    │
│  │  │                                            │      │    │
│  │  └──────────────────────────────────────────┘      │    │
│  │                                                      │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer-by-Layer Breakdown

### Layer 1: CORE (Domain Logic) - This is YOUR Application

**Location:** `chamberprotocol/core/` or `chamberprotocol/domain/`

**What lives here:**
- Business logic specific to YOUR application (game logic, NPC behavior, quest system)
- Domain models (NPCState, Conversation, Quest, GameWorld)
- Use cases / application services (ConversationManager, NPCController)
- **NO framework dependencies** (no FastAPI, no LangChain, no SQLite)
- **NO implementation details** (doesn't know about OpenAI or Anthropic)

**Example - ChamberProtocolAI Core:**
```python
# chamberprotocol/core/npc_controller.py
from chatforge.ports import LLMPort, StoragePort  # ← Uses ports (interfaces only)

class NPCController:
    """
    CORE APPLICATION LOGIC - knows WHAT to do, not HOW.
    Uses ports (interfaces) without knowing the implementation.
    """

    def __init__(
        self,
        llm: LLMPort,           # ← Depends on INTERFACE, not implementation
        storage: StoragePort,   # ← Depends on INTERFACE, not implementation
    ):
        self.llm = llm
        self.storage = storage

    async def talk_to_npc(
        self,
        npc_id: str,
        player_message: str
    ) -> str:
        """
        Business logic: Handle NPC conversation.

        This is YOUR domain logic - specific to the game.
        It doesn't know if we're using OpenAI or Anthropic.
        It doesn't know if we're using SQLite or Redis.
        """
        # 1. Load conversation history
        history = await self.storage.load_conversation(npc_id)

        # 2. Build LLM request with game-specific context
        npc_personality = self._get_npc_personality(npc_id)
        messages = [
            LLMMessage(role="system", content=npc_personality),
            *history,
            LLMMessage(role="user", content=player_message)
        ]

        request = LLMRequest(
            messages=messages,
            temperature=0.8,  # Higher for creative NPC responses
            operation_name=f"npc_talk_{npc_id}"
        )

        # 3. Get LLM response via port
        response = await self.llm.generate(request)

        # 4. Save conversation via port
        await self.storage.save_message(npc_id, player_message, response.content)

        return response.content

    def _get_npc_personality(self, npc_id: str) -> str:
        """Domain logic - NPC personality system"""
        # This is CORE game logic
        personalities = {
            "merchant": "You are a cheerful merchant in a fantasy tavern...",
            "guard": "You are a stern but fair city guard..."
        }
        return personalities.get(npc_id, "You are a friendly NPC")
```

**Key Point:** The core has **ZERO knowledge** of:
- Which LLM provider (OpenAI? Anthropic? Local model?)
- Which database (SQLite? PostgreSQL? Redis?)
- Which framework (FastAPI? Flask? CLI?)

---

### Layer 2: PORTS (Interfaces/Contracts)

**Location:** `chatforge/ports/`

**What lives here:**
- Abstract base classes (Python ABCs)
- Type definitions
- Contracts that adapters must fulfill
- **NO implementation** - just method signatures

**Example - LLMPort:**
```python
# chatforge/ports/llm_port.py
from abc import ABC, abstractmethod
from chatforge.llm.request import LLMRequest
from chatforge.llm.response import LLMResponse

class LLMPort(ABC):
    """
    PORT (Interface) - defines WHAT operations are available.

    Any adapter implementing this MUST provide these methods.
    The core depends on THIS interface, not on any specific adapter.
    """

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate LLM response from request"""
        pass

    @abstractmethod
    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """Stream LLM response chunks"""
        pass
```

**Example - StoragePort:**
```python
# chatforge/ports/storage_port.py
from abc import ABC, abstractmethod
from typing import List

class StoragePort(ABC):
    """PORT for conversation storage"""

    @abstractmethod
    async def save_message(self, conversation_id: str, role: str, content: str) -> None:
        pass

    @abstractmethod
    async def load_conversation(self, conversation_id: str) -> List[Message]:
        pass
```

**Key Point:** Ports are **CONTRACTS** - they define behavior without implementation.

---

### Layer 3: ADAPTERS (Implementations)

**Location:** `chatforge/adapters/`

**What lives here:**
- Concrete implementations of ports
- Framework/library integrations (LangChain, OpenAI SDK, SQLite)
- Infrastructure concerns (HTTP clients, database connections)

**Example - OpenAI LLM Adapter:**
```python
# chatforge/adapters/llm/openai_adapter.py
from chatforge.ports import LLMPort
from chatforge.llm.request import LLMRequest
from chatforge.llm.response import LLMResponse
from langchain_openai import ChatOpenAI

class OpenAILLMAdapter(LLMPort):
    """
    ADAPTER - implements LLMPort using OpenAI + LangChain.

    This is where we deal with infrastructure:
    - LangChain library
    - OpenAI API
    - Error handling
    - Cost calculation
    """

    def __init__(self, api_key: str, default_model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.default_model = default_model

    async def generate(self, request: LLMRequest) -> LLMResponse:
        # Convert LLMRequest → LangChain messages
        langchain_messages = self._convert_messages(request.messages)

        # Create LangChain ChatOpenAI instance
        llm = ChatOpenAI(
            model=request.model or self.default_model,
            temperature=request.temperature or 0.7,
            api_key=self.api_key
        )

        # Invoke LangChain
        result = await llm.ainvoke(langchain_messages)

        # Convert LangChain response → LLMResponse
        return LLMResponse(
            success=True,
            content=result.content,
            model=request.model or self.default_model,
            usage=self._extract_usage(result),
            cost=self._calculate_cost(result)
        )
```

**Example - SQLite Storage Adapter:**
```python
# chatforge/adapters/storage/sqlite_adapter.py
from chatforge.ports import StoragePort
import aiosqlite

class SQLiteStorageAdapter(StoragePort):
    """ADAPTER - implements StoragePort using SQLite"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def save_message(self, conversation_id: str, role: str, content: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
                (conversation_id, role, content)
            )
            await db.commit()

    async def load_conversation(self, conversation_id: str) -> List[Message]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT role, content FROM messages WHERE conversation_id = ?",
                (conversation_id,)
            )
            rows = await cursor.fetchall()
            return [Message(role=row[0], content=row[1]) for row in rows]
```

**Key Point:** Adapters contain **ALL infrastructure details** - the core never touches them directly.

---

## THE MAGIC: Where Ports Get Connected (Composition Root)

### What is the Composition Root?

The **composition root** is the SINGLE PLACE where:
1. Adapters are instantiated
2. Adapters are injected into the core
3. The application is assembled

**Location:** Typically in:
- `main.py` (for CLI apps)
- `app.py` or `server.py` (for web servers)
- `__init__.py` of the application package
- Dependency injection container (FastAPI dependencies, etc.)

---

### Example 1: Simple Main Function (Composition Root)

```python
# chamberprotocol/main.py
import asyncio
from chatforge.adapters.llm import OpenAILLMAdapter
from chatforge.adapters.storage import SQLiteStorageAdapter
from chamberprotocol.core.npc_controller import NPCController

async def main():
    """
    COMPOSITION ROOT - where everything gets wired together.

    This is the ONLY place that knows:
    - We're using OpenAI (not Anthropic)
    - We're using SQLite (not PostgreSQL)
    - How to connect them to the core
    """

    # 1. Instantiate adapters (infrastructure layer)
    llm_adapter = OpenAILLMAdapter(
        api_key="sk-...",
        default_model="gpt-4o-mini"
    )

    storage_adapter = SQLiteStorageAdapter(
        db_path="./game_data.db"
    )

    # 2. Inject adapters into core (dependency injection)
    npc_controller = NPCController(
        llm=llm_adapter,        # ← Port connected!
        storage=storage_adapter # ← Port connected!
    )

    # 3. Run application logic
    response = await npc_controller.talk_to_npc(
        npc_id="merchant",
        player_message="Do you have any healing potions?"
    )

    print(f"NPC: {response}")

if __name__ == "__main__":
    asyncio.run(main())
```

**What happened here?**
1. `OpenAILLMAdapter` implements `LLMPort`
2. `SQLiteStorageAdapter` implements `StoragePort`
3. `NPCController` (core) receives them via constructor injection
4. NPCController doesn't know it's talking to OpenAI or SQLite - it only knows the **interfaces** (ports)

---

### Example 2: FastAPI with Dependency Injection (Composition Root)

```python
# chamberprotocol/api/app.py
from fastapi import FastAPI, Depends
from chatforge.adapters.llm import OpenAILLMAdapter
from chatforge.adapters.storage import SQLiteStorageAdapter
from chatforge.ports import LLMPort, StoragePort
from chamberprotocol.core.npc_controller import NPCController

app = FastAPI()

# ═══════════════════════════════════════════════════════════
# COMPOSITION ROOT - Dependency Injection Functions
# ═══════════════════════════════════════════════════════════

def get_llm_adapter() -> LLMPort:
    """Factory function - creates LLM adapter"""
    return OpenAILLMAdapter(
        api_key=os.getenv("OPENAI_API_KEY"),
        default_model="gpt-4o-mini"
    )

def get_storage_adapter() -> StoragePort:
    """Factory function - creates storage adapter"""
    return SQLiteStorageAdapter(db_path="./game_data.db")

def get_npc_controller(
    llm: LLMPort = Depends(get_llm_adapter),
    storage: StoragePort = Depends(get_storage_adapter)
) -> NPCController:
    """Factory function - creates core application with injected adapters"""
    return NPCController(llm=llm, storage=storage)

# ═══════════════════════════════════════════════════════════
# API Routes - Use core via dependency injection
# ═══════════════════════════════════════════════════════════

@app.post("/npc/talk")
async def talk_to_npc(
    npc_id: str,
    message: str,
    controller: NPCController = Depends(get_npc_controller)  # ← Injected!
):
    """
    API endpoint - receives pre-wired NPCController.

    The controller already has OpenAI + SQLite adapters injected.
    The endpoint doesn't know or care about implementation details.
    """
    response = await controller.talk_to_npc(npc_id, message)
    return {"npc_response": response}
```

**What happened here?**
1. `get_llm_adapter()` and `get_storage_adapter()` are the **composition root**
2. FastAPI's `Depends()` handles dependency injection
3. The route handler receives a **fully-wired** `NPCController`
4. If you want to switch from OpenAI to Anthropic, you only change `get_llm_adapter()`

---

## Tracing the Operation Flow

### Question: "Where do operations match exactly?"

Let's trace a complete request through the hexagonal architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER INPUT (Infrastructure Layer)                            │
│    HTTP POST /npc/talk                                          │
│    { "npc_id": "merchant", "message": "Got any potions?" }      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. FASTAPI ROUTE HANDLER (Adapter/Infrastructure Layer)         │
│    async def talk_to_npc(...)                                   │
│    - Receives HTTP request                                      │
│    - FastAPI injects NPCController via Depends()                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. NPC CONTROLLER (CORE - Domain Logic)                         │
│    await controller.talk_to_npc(npc_id, message)                │
│    - Loads conversation history via storage.load_conversation() │
│    - Builds LLM request with NPC personality                    │
│    - Calls llm.generate(request) ◄── Uses LLMPort interface     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. LLM PORT (Interface Boundary)                                │
│    LLMPort.generate(request: LLMRequest) -> LLMResponse         │
│    - Abstract method defined in chatforge/ports/llm_port.py     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. OPENAI LLM ADAPTER (Infrastructure Implementation)           │
│    class OpenAILLMAdapter(LLMPort):                             │
│    - Converts LLMRequest → LangChain messages                   │
│    - Creates ChatOpenAI instance                                │
│    - Calls await llm.ainvoke(messages) ◄── LangChain library    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. LANGCHAIN + OPENAI API (External Service)                    │
│    - LangChain makes HTTP request to OpenAI                     │
│    - OpenAI returns: "I have 3 healing potions for 50 gold..."  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. OPENAI ADAPTER (Return Path)                                 │
│    - Receives LangChain response                                │
│    - Extracts usage, cost                                       │
│    - Returns LLMResponse(content="I have 3 healing potions...") │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. NPC CONTROLLER (CORE - Domain Logic)                         │
│    - Receives LLMResponse                                       │
│    - Saves conversation via storage.save_message()              │
│    - Returns response.content to caller                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. STORAGE PORT (Interface Boundary)                            │
│    StoragePort.save_message(conversation_id, role, content)     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 10. SQLITE STORAGE ADAPTER (Infrastructure Implementation)      │
│     - Opens SQLite connection                                   │
│     - Executes INSERT query                                     │
│     - Commits transaction                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 11. FASTAPI ROUTE HANDLER (Return Path)                         │
│     - Receives response string from controller                  │
│     - Returns JSON: {"npc_response": "I have 3 healing potions"}│
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Insights

### 1. The Core is Framework-Agnostic

```python
# chamberprotocol/core/npc_controller.py
# NO imports of:
# - fastapi
# - langchain
# - openai
# - aiosqlite
# - pydantic (except for dataclasses)

# ONLY imports:
from chatforge.ports import LLMPort, StoragePort  # Interfaces only!
```

### 2. Ports are the Contracts

```python
# The core depends on THIS:
llm: LLMPort  # Interface

# NOT on this:
llm: OpenAILLMAdapter  # Concrete implementation ❌
```

### 3. Composition Root Wires Everything

```python
# This is the ONLY place that knows implementation details:
npc_controller = NPCController(
    llm=OpenAILLMAdapter(...),      # ← Concrete adapter
    storage=SQLiteStorageAdapter(...)  # ← Concrete adapter
)
```

### 4. Easy to Swap Implementations

**Want to switch from OpenAI to Anthropic?**

```python
# Before:
def get_llm_adapter() -> LLMPort:
    return OpenAILLMAdapter(api_key="sk-...")

# After (ONE line change in composition root):
def get_llm_adapter() -> LLMPort:
    return AnthropicLLMAdapter(api_key="sk-ant-...")  # ← Changed!

# NPCController (core) doesn't change at all!
```

**Want to switch from SQLite to PostgreSQL?**

```python
# Before:
def get_storage_adapter() -> StoragePort:
    return SQLiteStorageAdapter(db_path="./game.db")

# After:
def get_storage_adapter() -> StoragePort:
    return PostgreSQLStorageAdapter(connection_string="postgresql://...")

# NPCController (core) doesn't change at all!
```

---

## Directory Structure Example

```
chamberprotocol/
├── core/                          # ← YOUR APPLICATION LOGIC
│   ├── __init__.py
│   ├── npc_controller.py          # Uses LLMPort, StoragePort
│   ├── quest_engine.py            # Uses StoragePort
│   └── combat_system.py           # Pure domain logic
│
├── api/                           # ← COMPOSITION ROOT for FastAPI
│   ├── __init__.py
│   ├── app.py                     # FastAPI app + DI setup
│   └── routes/
│       └── npc_routes.py
│
├── cli/                           # ← COMPOSITION ROOT for CLI
│   └── main.py                    # CLI entry point + DI setup
│
└── config/
    └── settings.py

chatforge/                         # ← LIBRARY (provides ports + adapters)
├── ports/                         # ← INTERFACES
│   ├── __init__.py
│   ├── llm_port.py                # LLMPort (ABC)
│   ├── storage_port.py            # StoragePort (ABC)
│   └── agent_port.py              # AgentPort (ABC)
│
├── adapters/                      # ← IMPLEMENTATIONS
│   ├── llm/
│   │   ├── openai_adapter.py      # Implements LLMPort with OpenAI
│   │   ├── anthropic_adapter.py   # Implements LLMPort with Anthropic
│   │   └── bedrock_adapter.py     # Implements LLMPort with Bedrock
│   │
│   ├── storage/
│   │   ├── sqlite_adapter.py      # Implements StoragePort with SQLite
│   │   ├── postgres_adapter.py    # Implements StoragePort with PostgreSQL
│   │   └── redis_adapter.py       # Implements StoragePort with Redis
│   │
│   └── agent/
│       ├── simple_chat_adapter.py # Implements AgentPort (simple chat)
│       └── react_adapter.py       # Implements AgentPort (ReAct pattern)
│
└── llm/                           # ← DATA MODELS
    ├── request.py                 # LLMRequest dataclass
    ├── response.py                # LLMResponse dataclass
    └── tracking.py                # TokenUsage, CostBreakdown, etc.
```

---

## Summary: Answering Your Question

> "Where does the main application live exactly?"

**Answer:** The main application (domain logic) lives in the **CORE** (`chamberprotocol/core/`). It uses **ports** (interfaces) defined in `chatforge/ports/`.

> "Where are ports connected?"

**Answer:** Ports are connected at the **COMPOSITION ROOT** - typically in `main.py`, `app.py`, or FastAPI dependency injection functions.

> "How are they connected?"

**Answer:** Via **dependency injection** - adapters (implementations) are passed to the core's constructor:

```python
# Composition root
llm_adapter = OpenAILLMAdapter(...)  # Concrete implementation
core_logic = NPCController(llm=llm_adapter)  # Injected via constructor

# Core logic uses the interface
async def talk_to_npc(self, ...):
    response = await self.llm.generate(request)  # ← Calls via LLMPort interface
```

**The beauty of hexagonal architecture:**
- Core depends on **interfaces** (ports), not **implementations** (adapters)
- Adapters can be swapped without changing the core
- Testing is easy - mock the ports, test the core in isolation
- Business logic is decoupled from infrastructure
