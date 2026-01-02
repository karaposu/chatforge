# The MyLLMService Pattern: Clean LLM Integration

A service layer pattern for organizing all LLM-related methods in one place, making your codebase cleaner and more maintainable.

---

## The Problem

When building applications with multiple LLM use cases, you often end up with:

```python
# ❌ BAD: LLM logic scattered everywhere

# In chat_api.py
from chatforge.services.llm.factory import get_llm
llm = get_llm("openai", "gpt-4o-mini")
response = llm.invoke([HumanMessage(content=prompt)])

# In analysis_api.py
from chatforge.services.llm.factory import get_llm
llm = get_llm("openai", "gpt-4o-mini")  # Duplicate setup
response = llm.invoke([HumanMessage(content=analysis_prompt)])

# In game_api.py
from chatforge.services.llm.factory import get_llm
llm = get_llm("openai", "gpt-4o-mini")  # More duplication
response = llm.invoke([HumanMessage(content=game_prompt)])
```

**Issues:**
- LLM setup code duplicated everywhere
- Hard to switch models globally
- No caching of LLM instances
- Prompt management scattered across files
- Testing requires mocking in every file

---

## The Solution: MyLLMService

Create **one service class** that contains all your LLM methods. Import it anywhere via dependency injection.

```python
# ✅ GOOD: All LLM logic in one place

# impl/myllmservice.py
class MyLLMService:
    def generate_ai_answer(self, chat_history, user_msg):
        # LLM logic here

    def generate_siluet_answer(self, game_context, player_input):
        # Game-specific LLM logic

    def analyze_sentiment(self, text):
        # Analysis logic

# APIs just import and use
from impl.myllmservice import MyLLMService

llm = MyLLMService()
response = llm.generate_ai_answer(history, msg)
```

---

## Full Implementation

### Step 1: Create the Service Class

```python
# impl/myllmservice.py
"""
LLM service using Chatforge's get_llm() factory.

All LLM-related methods live here for easy reuse across the codebase.
"""
import logging
from dotenv import load_dotenv

load_dotenv()  # Load .env before using Chatforge

from chatforge.services.llm.factory import get_llm
from langchain_core.messages import HumanMessage
from . import prompts

logger = logging.getLogger(__name__)


class MyLLMService:
    """Centralized LLM service for all application LLM needs."""

    def __init__(self, default_model: str = "gpt-4o-mini"):
        """
        Initialize the LLM service.

        Args:
            default_model: Model to use when not specified
        """
        self.default_model = default_model
        self._llm_cache = {}

    def _get_llm(self, model: str = None):
        """
        Get or create cached LLM instance.

        This avoids recreating LLM instances on every call.
        """
        model = model or self.default_model
        if model not in self._llm_cache:
            self._llm_cache[model] = get_llm(
                provider="openai",
                model_name=model
            )
        return self._llm_cache[model]

    def generate_ai_answer(
        self,
        chat_history: str,
        user_msg: str = None,
        model: str = None,
    ) -> str:
        """
        Generate a simple AI answer based on chat history.

        Args:
            chat_history: Formatted conversation history
            user_msg: Latest user message
            model: Optional model override

        Returns:
            str: AI response text
        """
        user_prompt = prompts.GENERATE_AI_ANSWER_PROMPT.format(
            chat_history=chat_history,
            user_msg=user_msg,
        )

        llm = self._get_llm(model)
        response = llm.invoke([HumanMessage(content=user_prompt)])
        return response.content

    def generate_siluet_answer(
        self,
        game_context: str = None,
        ai_character_profile: str = None,
        player_progress: str = None,
        room_context: str = None,
        visual_context: str = None,
        conversation_memory: str = None,
        proactive_triggers: str = None,
        ai_character_response_parameters: str = None,
        player_input: str = None,
        response_constraints: str = None,
        language: str = None,
        model: str = None,
        enable_audio_tags: bool = False,
    ) -> str:
        """
        Generate game AI response with rich context.

        This method demonstrates how domain-specific logic
        can be encapsulated in a service method.

        Args:
            game_context: Game world information
            ai_character_profile: NPC personality and state
            player_progress: Player history and patterns
            room_context: Current scene details
            visual_context: What player sees
            conversation_memory: Recent dialogue
            proactive_triggers: AI-initiated dialogue triggers
            ai_character_response_parameters: Mood, style, emotion
            player_input: The actual player message
            response_constraints: Generation rules
            language: Language code (e.g., 'EN', 'TR')
            model: LLM model override
            enable_audio_tags: Include ElevenLabs audio tags

        Returns:
            str: NPC response text
        """
        from schemas import StepContext

        # Create structured context
        context = StepContext(
            game_context=game_context,
            ai_character_profile=ai_character_profile,
            player_progress=player_progress,
            room_context=room_context,
            visual_context=visual_context,
            conversation_memory=conversation_memory,
            proactive_triggers=proactive_triggers,
            ai_character_response_parameters=ai_character_response_parameters,
            player_input=player_input,
            response_constraints=response_constraints,
            language=language,
            enable_audio_tags=enable_audio_tags,
        )

        # Compile complete prompt from context
        full_prompt = context.compile()

        # Call LLM
        llm = self._get_llm(model)
        response = llm.invoke([HumanMessage(content=full_prompt)])
        return response.content

    def generate_with_prompt(self, prompt: str, model: str = None) -> str:
        """
        Generate response for any arbitrary prompt.

        Simple wrapper for direct LLM calls.

        Args:
            prompt: The full prompt text
            model: LLM model to use

        Returns:
            str: The LLM response
        """
        llm = self._get_llm(model)
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
```

---

## Usage Patterns

### Pattern 1: Direct Instantiation

```python
# In your API or business logic
from impl.myllmservice import MyLLMService

llm_service = MyLLMService()
response = llm_service.generate_ai_answer(
    chat_history=history,
    user_msg=message
)
```

### Pattern 2: Constructor Injection

```python
# chatbackend.py
from impl.myllmservice import MyLLMService

class ChatBackend:
    def __init__(
        self,
        my_llm_service: Optional[MyLLMService] = None,
    ):
        # Inject or create
        self.llm = my_llm_service or MyLLMService()

    def produce_ai_response(self):
        history = self.generate_chat_history(n=4)

        # Clean, simple usage
        response = self.llm.generate_ai_answer(
            chat_history=history,
            user_msg=self.last_message.message,
        )
        return response
```

### Pattern 3: Dependency Injection Container (Future)

```python
# core/containers.py
from dependency_injector import containers, providers
from impl.myllmservice import MyLLMService

class Services(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Add LLM service to container
    llm_service = providers.Singleton(
        MyLLMService,
        default_model=config.default_llm_model
    )

    # Other services can depend on it
    chat_service = providers.Factory(
        ChatService,
        llm_service=llm_service
    )

# In your API
def get_services(request: Request) -> Services:
    return request.app.state.services

@router.post("/chat")
async def chat(
    request: ChatRequest,
    services: Services = Depends(get_services)
):
    llm = services.llm_service()
    response = llm.generate_ai_answer(...)
```

---

## Benefits

### 1. **Centralization**
All LLM logic in one file. Easy to find, easy to modify.

### 2. **Reusability**
Write once, use everywhere. No duplication.

```python
# Use in API
llm = MyLLMService()
api_response = llm.generate_ai_answer(...)

# Use in background job
llm = MyLLMService()
analysis = llm.analyze_sentiment(...)

# Use in CLI
llm = MyLLMService()
result = llm.generate_with_prompt(...)
```

### 3. **Easy Testing**
Mock once, test everywhere.

```python
# tests/test_chat_api.py
from unittest.mock import Mock

mock_llm = Mock(spec=MyLLMService)
mock_llm.generate_ai_answer.return_value = "Mocked response"

chat_backend = ChatBackend(my_llm_service=mock_llm)
result = chat_backend.produce_ai_response()

assert result == "Mocked response"
```

### 4. **Model Switching**
Change model globally in one place.

```python
# Development
llm = MyLLMService(default_model="gpt-4o-mini")

# Production
llm = MyLLMService(default_model="gpt-4o")

# All methods use the specified model
```

### 5. **Caching**
LLM instances cached automatically.

```python
# First call creates gpt-4o-mini instance
response1 = llm.generate_ai_answer(...)

# Second call reuses cached instance
response2 = llm.generate_siluet_answer(...)

# Different model creates new instance
response3 = llm.generate_with_prompt(..., model="gpt-4o")
```

### 6. **Domain Logic Encapsulation**
Complex prompt assembly hidden inside methods.

```python
# Instead of this in your API:
game_prompt = f"""
Game Context: {game_context}
Player: {player_input}
NPC Profile: {ai_profile}
... (50 more lines)
"""
llm = get_llm(...)
response = llm.invoke(...)

# You write this:
response = llm.generate_siluet_answer(
    game_context=game_context,
    player_input=player_input,
    ai_character_profile=ai_profile,
)
```

---

## Comparison: Before & After

### Before (Scattered)

```python
# chat_api.py
from chatforge.services.llm.factory import get_llm
from langchain_core.messages import HumanMessage

def chat_endpoint(request):
    llm = get_llm("openai", "gpt-4o-mini")
    prompt = f"History: {history}\nUser: {request.message}"
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content

# game_api.py
from chatforge.services.llm.factory import get_llm
from langchain_core.messages import HumanMessage

def game_endpoint(request):
    llm = get_llm("openai", "gpt-4o-mini")  # Duplicate!
    prompt = compile_game_prompt(request)
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content

# analysis_api.py
from chatforge.services.llm.factory import get_llm
from langchain_core.messages import HumanMessage

def analyze_endpoint(request):
    llm = get_llm("openai", "gpt-4o-mini")  # More duplication!
    prompt = f"Analyze: {request.text}"
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content
```

**Issues:**
- 3 files import LLM code
- 3x duplicate setup
- No caching
- Hard to test
- Hard to change models

### After (Centralized)

```python
# impl/myllmservice.py
class MyLLMService:
    def generate_chat_response(self, history, message):
        # Implementation once

    def generate_game_response(self, context):
        # Implementation once

    def analyze_text(self, text):
        # Implementation once

# chat_api.py
from impl.myllmservice import MyLLMService

def chat_endpoint(request):
    llm = MyLLMService()
    return llm.generate_chat_response(history, request.message)

# game_api.py
from impl.myllmservice import MyLLMService

def game_endpoint(request):
    llm = MyLLMService()
    return llm.generate_game_response(request.context)

# analysis_api.py
from impl.myllmservice import MyLLMService

def analyze_endpoint(request):
    llm = MyLLMService()
    return llm.analyze_text(request.text)
```

**Benefits:**
- ✅ One import
- ✅ No duplication
- ✅ Automatic caching
- ✅ Easy to test
- ✅ Easy to switch models

---

## Best Practices

### 1. **One Method Per Use Case**

```python
class MyLLMService:
    def generate_chat_response(...)  # For chat
    def generate_summary(...)         # For summarization
    def extract_keywords(...)         # For extraction
    def translate_text(...)           # For translation
```

Each method encapsulates its domain logic.

### 2. **Keep Prompts Separate**

```python
# impl/prompts.py
GENERATE_AI_ANSWER_PROMPT = """
You are a helpful assistant.

Chat History:
{chat_history}

User Message:
{user_msg}

Respond naturally and helpfully.
"""

# impl/myllmservice.py
from . import prompts

class MyLLMService:
    def generate_ai_answer(self, chat_history, user_msg):
        prompt = prompts.GENERATE_AI_ANSWER_PROMPT.format(
            chat_history=chat_history,
            user_msg=user_msg
        )
        # ...
```

### 3. **Allow Model Overrides**

```python
def generate_ai_answer(
    self,
    chat_history: str,
    model: str = None,  # Optional override
) -> str:
    llm = self._get_llm(model)  # Uses default if None
```

### 4. **Return Simple Types**

```python
# ✅ GOOD - Return strings, dicts, simple types
def generate_ai_answer(...) -> str:
    return response.content

# ❌ BAD - Don't return LangChain objects
def generate_ai_answer(...) -> AIMessage:
    return response  # Leaks implementation details
```

### 5. **Document Parameters**

```python
def generate_siluet_answer(
    self,
    game_context: str = None,        # What it is
    player_input: str = None,        # Clear names
    enable_audio_tags: bool = False, # Explicit defaults
) -> str:
    """
    Generate game AI response.

    Args:
        game_context: Game world information
        player_input: The actual player message
        enable_audio_tags: Include ElevenLabs TTS tags

    Returns:
        str: NPC response text
    """
```

---

## When to Use This Pattern

### ✅ **Use When:**
- You have 3+ different LLM use cases
- Multiple APIs/endpoints use LLMs
- You want centralized testing
- You need easy model switching
- Team members share LLM logic

### ❌ **Don't Use When:**
- Tiny project with 1 LLM call
- Each use case is completely unique
- No code reuse needed

---

## Integration with Chatforge

MyLLMService is a **wrapper around chatforge's factory**:

```python
from chatforge.services.llm.factory import get_llm

class MyLLMService:
    def _get_llm(self, model: str = None):
        # Uses chatforge underneath
        return get_llm(provider="openai", model_name=model)
```

**Benefits of this approach:**
- Chatforge handles provider abstraction
- Easy to switch providers (OpenAI, Anthropic, AWS Bedrock)
- Your app code stays clean and simple

---

## Real-World Example: ChamberProtocolAI

ChamberProtocolAI uses this pattern for a game with an AI NPC named Silüet:

```python
# Game needs multiple LLM operations:
# 1. Character dialogue
# 2. Context-aware responses
# 3. Audio tag generation
# 4. Multi-language support

# All live in MyLLMService:
class MyLLMService:
    def generate_siluet_answer(
        self,
        game_context, ai_character_profile, player_progress,
        room_context, visual_context, conversation_memory,
        player_input, language, enable_audio_tags
    ):
        # Complex game AI logic encapsulated here

    def generate_ai_answer(self, chat_history, user_msg):
        # Simple chat for debugging/testing

# Used throughout the game:
llm = MyLLMService()

# In dialogue system
npc_response = llm.generate_siluet_answer(
    game_context=context,
    player_input=input,
    language="EN"
)

# In debug console
debug_response = llm.generate_ai_answer(
    chat_history=history,
    user_msg=command
)
```

---

## Summary

**The MyLLMService pattern provides:**

1. **Centralization** - One place for all LLM code
2. **Reusability** - Write once, use everywhere
3. **Testability** - Mock once, test everywhere
4. **Flexibility** - Easy model switching
5. **Maintainability** - Clear, organized code
6. **Performance** - Automatic caching

**It makes your codebase:**
- Cleaner (no scattered LLM setup)
- Easier to test (single mock point)
- More maintainable (centralized logic)
- More flexible (easy to change models/providers)

**Start using it when:**
- You have 3+ LLM use cases
- Multiple files need LLM access
- You want professional, maintainable code

---

## Further Reading

- [Chatforge LLM Factory Documentation](../README.md)
- [Dependency Injection in Python](https://python-dependency-injector.ets-labs.org/)
- [Service Layer Pattern](https://martinfowler.com/eaaCatalog/serviceLayer.html)
