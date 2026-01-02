# Recommended Patterns for Chatforge Applications

Best practices for building clean, maintainable AI applications with chatforge.

---

## The MyLLMService Pattern

### Core Idea

**Centralize all AI logic in one service class.**

Create `impl/myllmservice.py` with all your LLM and Agent methods. Keep prompts in `impl/prompts.py`.

This works with:
- ✅ Simple LLMs (`get_llm`)
- ✅ Agents (`ReActAgent`)
- ✅ Streaming, Vision, any chatforge component

###  The Problem

**Without pattern:**
```python
# Scattered across multiple files
from chatforge.services.llm.factory import get_llm
llm = get_llm("openai", "gpt-4o-mini")  # Duplicated everywhere!
```

**With pattern:**
```python
# impl/myllmservice.py - ONE place
class MyLLMService:
    def chat(self, message): ...
    def analyze(self, text): ...

# APIs just use it
llm = MyLLMService()
response = llm.chat(message)
```

---

## With LLMs (`get_llm`)

```python
# impl/myllmservice.py
from chatforge.services.llm.factory import get_llm
from langchain_core.messages import HumanMessage
from . import prompts

class MyLLMService:
    def __init__(self, default_model="gpt-4o-mini"):
        self.default_model = default_model
        self._llm_cache = {}

    def _get_llm(self, model=None):
        """Get or create cached LLM."""
        model = model or self.default_model
        if model not in self._llm_cache:
            self._llm_cache[model] = get_llm(provider="openai", model_name=model)
        return self._llm_cache[model]

    def chat(self, message, history="", model=None):
        """Generate chat response."""
        prompt = prompts.CHAT_PROMPT.format(history=history, message=message)
        llm = self._get_llm(model)
        return llm.invoke([HumanMessage(content=prompt)]).content

    def summarize(self, text, model=None):
        """Summarize text."""
        prompt = prompts.SUMMARIZE_PROMPT.format(text=text)
        llm = self._get_llm(model)
        return llm.invoke([HumanMessage(content=prompt)]).content
```

```python
# impl/prompts.py
CHAT_PROMPT = """You are helpful.

{history}

User: {message}"""

SUMMARIZE_PROMPT = """Summarize:

{text}"""
```

---

## With Agents (`ReActAgent`)

```python
# impl/myllmservice.py
from chatforge.services.agent import ReActAgent
from chatforge.services.agent.tools.base import Tool
from . import prompts

class MyLLMService:
    def __init__(self):
        self._agent = None
        self._agent_tools = []

    def _get_agent(self):
        """Get or create cached agent."""
        if not self._agent:
            self._agent = ReActAgent(
                tools=self._agent_tools,
                system_prompt=prompts.AGENT_SYSTEM_PROMPT
            )
        return self._agent

    def register_tool(self, tool: Tool):
        """Register a tool for the agent."""
        self._agent_tools.append(tool)
        self._agent = None  # Clear cache to rebuild with new tool

    def assist_with_tools(self, message, history=None, context=None):
        """Agent with tool access."""
        agent = self._get_agent()
        response, trace_id = agent.process_message(
            message,
            history or [],
            context or {}
        )
        return response
```

```python
# impl/prompts.py
AGENT_SYSTEM_PROMPT = """You are a helpful assistant with access to tools.
Use tools when needed to help the user."""
```

---

## With Both LLMs and Agents

```python
# impl/myllmservice.py
from chatforge.services.llm.factory import get_llm
from chatforge.services.agent import ReActAgent
from langchain_core.messages import HumanMessage
from . import prompts

class MyLLMService:
    def __init__(self, default_model="gpt-4o-mini"):
        self.default_model = default_model
        self._llm_cache = {}
        self._agent = None
        self._tools = []

    # LLM methods
    def _get_llm(self, model=None):
        model = model or self.default_model
        if model not in self._llm_cache:
            self._llm_cache[model] = get_llm(provider="openai", model_name=model)
        return self._llm_cache[model]

    def chat(self, message, history=""):
        """Simple chat without tools."""
        prompt = prompts.CHAT_PROMPT.format(history=history, message=message)
        llm = self._get_llm()
        return llm.invoke([HumanMessage(content=prompt)]).content

    # Agent methods
    def _get_agent(self):
        if not self._agent:
            self._agent = ReActAgent(tools=self._tools, system_prompt=prompts.AGENT_PROMPT)
        return self._agent

    def register_tool(self, tool):
        self._tools.append(tool)
        self._agent = None

    def assist_with_tools(self, message, history=None):
        """Chat with tool access."""
        agent = self._get_agent()
        response, _ = agent.process_message(message, history or [], {})
        return response
```

---

## Usage in APIs

```python
# apis/chat_api.py
from fastapi import APIRouter
from impl.myllmservice import MyLLMService

router = APIRouter()
llm = MyLLMService()

@router.post("/chat")
async def chat(request: ChatRequest):
    # Simple LLM call
    response = llm.chat(
        message=request.message,
        history=request.history
    )
    return {"response": response}

@router.post("/assist")
async def assist(request: AssistRequest):
    # Agent with tools
    response = llm.assist_with_tools(
        message=request.message,
        history=request.history
    )
    return {"response": response}
```

---

## Advantages

### 1. Centralization
All AI logic in one file. Easy to find, modify, maintain.

### 2. Reusability
```python
# Use in API
llm = MyLLMService()
api_response = llm.chat(...)

# Use in background job
llm = MyLLMService()
analysis = llm.summarize(...)

# Use in CLI
llm = MyLLMService()
result = llm.assist_with_tools(...)
```

### 3. Caching
LLM and Agent instances cached automatically.
```python
llm = MyLLMService()
llm.chat(...)  # Creates gpt-4o-mini instance
llm.chat(...)  # Reuses cached instance
```

### 4. Easy Testing
Mock once, test everywhere.
```python
from unittest.mock import Mock

mock_llm = Mock(spec=MyLLMService)
mock_llm.chat.return_value = "Mocked"

# All tests use same mock
```

### 5. Model Switching
Change globally in one place.
```python
# Development
llm = MyLLMService(default_model="gpt-4o-mini")

# Production
llm = MyLLMService(default_model="gpt-4o")
```

### 6. Separation of Concerns
- `prompts.py` = What to say
- `myllmservice.py` = How to call AI
- `apis/` = How to expose functionality

### 7. Clean APIs
```python
# ❌ Without pattern
@router.post("/summarize-chat")
async def summarize_chat(request):
    llm = get_llm("openai", "gpt-4o-mini")
    prompt = f"Summarize this conversation:\n{request.chat_history}"
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content

# ✅ With pattern
@router.post("/summarize-chat")
async def summarize_chat(request):
    myllmservice = MyLLMService()
    response = myllmservice.summarize_chat(request.chat_history)
    return response
```

---

## When to Use

### ✅ Use When:
- Building chat applications
- Have 3+ different AI use cases
- Multiple APIs/endpoints use AI
- Want easy testing
- Need model switching
- Building production apps

### ❌ Skip When:
- Single-file script
- Only 1-2 AI calls
- Quick prototype/demo

### Rule of Thumb:
- **1-2 AI calls** → Use chatforge directly
- **3+ AI calls** → Use MyLLMService pattern
- **Production app** → Always use MyLLMService

---

## File Structure

```
your_app/
├── impl/
│   ├── __init__.py
│   ├── myllmservice.py    # All AI methods (LLMs + Agents)
│   └── prompts.py          # All prompts
├── apis/
│   ├── chat_api.py         # Import MyLLMService
│   └── assist_api.py       # Import MyLLMService
└── main.py
```

---

## Best Practices

### 1. One Method Per Use Case
```python
class MyLLMService:
    def chat(...)          # For chat
    def summarize(...)      # For summarization
    def extract_keywords(...) # For extraction
    def assist_with_tools(...) # For agent tasks
```

### 2. Keep Prompts Separate
```python
# impl/prompts.py
CHAT_PROMPT = """..."""
AGENT_PROMPT = """..."""

# impl/myllmservice.py
from . import prompts
prompt = prompts.CHAT_PROMPT.format(...)
```

### 3. Allow Model Overrides
```python
def chat(self, message, model=None):
    llm = self._get_llm(model)  # Uses default if None
```

### 4. Return Simple Types
```python
# ✅ Good
def chat(...) -> str:
    return response.content

# ❌ Bad
def chat(...) -> AIMessage:
    return response  # Leaks implementation
```

### 5. Cache Instances
```python
def _get_llm(self, model=None):
    if model not in self._llm_cache:
        self._llm_cache[model] = get_llm(...)
    return self._llm_cache[model]
```

---

## Summary

The MyLLMService pattern provides:

1. **Centralization** - One place for all AI code
2. **Reusability** - Write once, use everywhere
3. **Testability** - Mock once, test everywhere
4. **Flexibility** - Easy model/provider switching
5. **Maintainability** - Clear, organized code
6. **Works with LLMs AND Agents** - Not just simple completions

Use it for any chatforge application with 3+ AI use cases or production deployments.

