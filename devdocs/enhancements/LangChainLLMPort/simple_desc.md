# LangChainLLMPort: Simple Tracking Wrapper
## Extend LangChain, Don't Replace It

**Date:** 2025-12-26
**Status:** Design Phase
**Philosophy:** Minimal wrapper, maximum compatibility
**Approach:** Enhance LangChain models with tracking, keep existing interface

---

## The Core Idea

**Don't create a new interface. Just add tracking to LangChain models.**

```python
# Instead of this (new interface):
llm = OpenAILLMAdapter(...)  # Implements custom LLMPort
response = await llm.generate(LLMRequest(...))  # New interface

# Do this (wrap LangChain):
llm = LangChainLLMPort(ChatOpenAI(...), operation_name="npc_talk")
response = await llm.ainvoke([HumanMessage(...)])  # LangChain interface!

# But now response has extras:
print(response.usage_typed)  # ✅ Typed TokenUsage
print(response.cost)         # ✅ Calculated cost
print(response.operation_name)  # ✅ Operation tracking
```

---

## Why This is Better

### 1. **Minimal Code**

**LLMPort approach (complex):**
- Define `LLMPort` interface
- Define `LLMRequest` / `LLMResponse` dataclasses
- Create `OpenAILLMAdapter`, `AnthropicLLMAdapter`, `BedrockLLMAdapter`
- Convert between LangChain messages ↔ LLMRequest
- Convert between AIMessage ↔ LLMResponse
- **Estimated: 800+ lines of code**

**LangChainLLMPort approach (simple):**
- One wrapper class: `LangChainLLMPort`
- Adds tracking to existing AIMessage
- No message conversion
- **Estimated: 100-150 lines of code**

### 2. **Works with ALL LangChain Models**

**LLMPort approach:**
```python
# Need separate adapter for each provider
openai_llm = OpenAILLMAdapter(...)
anthropic_llm = AnthropicLLMAdapter(...)
bedrock_llm = BedrockLLMAdapter(...)
```

**LangChainLLMPort approach:**
```python
# One wrapper works with ANY LangChain model!
openai_llm = LangChainLLMPort(ChatOpenAI(...))
anthropic_llm = LangChainLLMPort(ChatAnthropic(...))
bedrock_llm = LangChainLLMPort(ChatBedrock(...))
ollama_llm = LangChainLLMPort(ChatOllama(...))  # Local models too!
```

### 3. **Zero Learning Curve**

**LLMPort approach:**
```python
# Developers have to learn new interface
request = LLMRequest(
    messages=[LLMMessage(role="user", content="Hello")],
    temperature=0.7,
    operation_name="npc_talk"
)
response = await llm.generate(request)
print(response.content)
```

**LangChainLLMPort approach:**
```python
# Developers already know LangChain
from langchain_core.messages import HumanMessage

response = await llm.ainvoke([HumanMessage(content="Hello")])
print(response.content)  # Same as before!
print(response.cost)     # Bonus: cost tracking!
```

### 4. **Keep LangChain Features**

**LLMPort approach:**
```python
# Have to reimplement every LangChain feature:
# - Streaming
# - Batching
# - Callbacks
# - Tool use
# - Structured output
# - Caching
# etc...
```

**LangChainLLMPort approach:**
```python
# Everything just works!
async for chunk in llm.astream([message]):  # ✅ Streaming
    print(chunk)

responses = await llm.abatch([msg1, msg2, msg3])  # ✅ Batching

llm_with_tools = llm.bind_tools([tool1, tool2])  # ✅ Tool use

# All LangChain features work because we're not replacing LangChain!
```

---

## What We're Adding

### Enhanced AIMessage

```python
# Standard LangChain AIMessage:
AIMessage(
    content="Hello! How can I help?",
    response_metadata={
        'token_usage': {'prompt_tokens': 10, 'completion_tokens': 8},
        'model_name': 'gpt-4o-mini',
        'finish_reason': 'stop'
    }
)

# Enhanced with LangChainLLMPort:
AIMessage(
    content="Hello! How can I help?",
    response_metadata={...},  # Same as before

    # NEW: Typed usage (not Dict[str, Any])
    usage_typed=TokenUsage(
        input_tokens=10,
        output_tokens=8,
        reasoning_tokens=0,
        cached_tokens=0
    ),

    # NEW: Calculated cost
    cost=CostBreakdown(
        input_cost=0.0000015,
        output_cost=0.0000048,
        total_cost=0.0000063
    ),

    # NEW: Operation tracking
    operation_name="npc_talk",

    # NEW: Timing
    elapsed_ms=450.2
)
```

**Key insight:** We're ADDING to AIMessage, not replacing it.

---

## Implementation

### Core Class

```python
# chatforge/llm/langchain_wrapper.py

from langchain_core.language_models import BaseChatModel
from typing import Optional, List
import time

class LangChainLLMPort:
    """
    Simple wrapper around any LangChain chat model.

    Adds:
    - Typed usage (TokenUsage instead of Dict)
    - Cost calculation
    - Operation tracking
    - Timing

    Keeps:
    - LangChain interface (.ainvoke, .astream, .batch, etc.)
    - All LangChain features (tools, callbacks, caching, etc.)
    """

    def __init__(
        self,
        base_llm: BaseChatModel,
        operation_name: Optional[str] = None,
        cost_tracker: Optional['CostTracker'] = None
    ):
        """
        Args:
            base_llm: ANY LangChain chat model (ChatOpenAI, ChatAnthropic, etc.)
            operation_name: Optional operation category for cost tracking
            cost_tracker: Optional shared cost tracker instance
        """
        self.llm = base_llm
        self.operation_name = operation_name
        self.cost_tracker = cost_tracker or CostTracker()

    async def ainvoke(self, messages, **kwargs):
        """
        Call LLM and enhance response with tracking.

        Same interface as BaseChatModel.ainvoke()
        """
        start_time = time.time()

        # Call LangChain (no changes!)
        result = await self.llm.ainvoke(messages, **kwargs)

        elapsed_ms = (time.time() - start_time) * 1000

        # Enhance result with tracking
        result.usage_typed = self._extract_typed_usage(result)
        result.cost = self._calculate_cost(result)
        result.operation_name = self.operation_name
        result.elapsed_ms = elapsed_ms

        # Track globally if tracker is provided
        if self.cost_tracker:
            self.cost_tracker.record(
                operation=self.operation_name,
                cost=result.cost,
                usage=result.usage_typed
            )

        return result

    def invoke(self, messages, **kwargs):
        """Sync version"""
        import asyncio
        return asyncio.run(self.ainvoke(messages, **kwargs))

    async def astream(self, messages, **kwargs):
        """
        Streaming with partial tracking.

        Note: Cost/usage only available in final chunk.
        """
        start_time = time.time()
        usage_accumulator = None

        async for chunk in self.llm.astream(messages, **kwargs):
            # Accumulate usage if available
            if hasattr(chunk, 'response_metadata'):
                usage_accumulator = chunk.response_metadata.get('token_usage')

            yield chunk

        # Track final usage/cost
        if usage_accumulator and self.cost_tracker:
            elapsed_ms = (time.time() - start_time) * 1000
            usage = self._extract_typed_usage_from_dict(usage_accumulator)
            cost = self._calculate_cost_from_usage(usage)

            self.cost_tracker.record(
                operation=self.operation_name,
                cost=cost,
                usage=usage
            )

    async def abatch(self, messages_list, **kwargs):
        """
        Batch processing with tracking per request.

        Returns list of enhanced AIMessages.
        """
        results = await self.llm.abatch(messages_list, **kwargs)

        # Enhance each result
        for result in results:
            result.usage_typed = self._extract_typed_usage(result)
            result.cost = self._calculate_cost(result)
            result.operation_name = self.operation_name

            if self.cost_tracker:
                self.cost_tracker.record(
                    operation=self.operation_name,
                    cost=result.cost,
                    usage=result.usage_typed
                )

        return results

    # Delegate all other methods to base_llm
    def __getattr__(self, name):
        """
        Pass through any method we don't override.

        This means ALL LangChain features work:
        - .bind_tools()
        - .with_structured_output()
        - .with_config()
        - etc.
        """
        return getattr(self.llm, name)

    def _extract_typed_usage(self, ai_message) -> 'TokenUsage':
        """Extract usage from AIMessage and convert to typed TokenUsage"""
        metadata = ai_message.response_metadata
        usage_dict = metadata.get("token_usage", {})
        return self._extract_typed_usage_from_dict(usage_dict)

    def _extract_typed_usage_from_dict(self, usage_dict: dict) -> 'TokenUsage':
        """Convert Dict[str, Any] to typed TokenUsage"""
        return TokenUsage(
            input_tokens=usage_dict.get("prompt_tokens", 0),
            output_tokens=usage_dict.get("completion_tokens", 0),
            reasoning_tokens=usage_dict.get("reasoning_tokens", 0),
            cached_tokens=usage_dict.get("cached_tokens", 0)
        )

    def _calculate_cost(self, ai_message) -> 'CostBreakdown':
        """Calculate cost based on model and usage"""
        usage = self._extract_typed_usage(ai_message)
        return self._calculate_cost_from_usage(usage)

    def _calculate_cost_from_usage(self, usage: 'TokenUsage') -> 'CostBreakdown':
        """Calculate cost from TokenUsage"""
        model_name = self.llm.model_name if hasattr(self.llm, 'model_name') else 'unknown'

        # Model pricing (per 1M tokens)
        pricing = {
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
            "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
        }

        rates = pricing.get(model_name, {"input": 0, "output": 0})

        return CostBreakdown(
            input_cost=(usage.input_tokens / 1_000_000) * rates["input"],
            output_cost=(usage.output_tokens / 1_000_000) * rates["output"],
            reasoning_cost=(usage.reasoning_tokens / 1_000_000) * rates.get("reasoning", 0),
            cache_read_cost=(usage.cached_tokens / 1_000_000) * rates.get("cache_read", 0)
        )
```

### Supporting Dataclasses

```python
# chatforge/llm/tracking.py

from dataclasses import dataclass, field
from typing import Dict, DefaultDict
from collections import defaultdict

@dataclass
class TokenUsage:
    """Typed token usage (better than Dict[str, Any])"""
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0  # For o-series models
    cached_tokens: int = 0     # For Anthropic prompt caching

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens + self.reasoning_tokens

@dataclass
class CostBreakdown:
    """Detailed cost breakdown"""
    input_cost: float = 0.0
    output_cost: float = 0.0
    reasoning_cost: float = 0.0
    cache_write_cost: float = 0.0
    cache_read_cost: float = 0.0

    @property
    def total_cost(self) -> float:
        return (
            self.input_cost +
            self.output_cost +
            self.reasoning_cost +
            self.cache_write_cost +
            self.cache_read_cost
        )

class CostTracker:
    """
    Global cost tracker for aggregating costs across operations.

    Usage:
        tracker = CostTracker()
        llm = LangChainLLMPort(ChatOpenAI(...), operation_name="npc_talk", cost_tracker=tracker)

        # After many calls...
        print(tracker.report())
    """

    def __init__(self):
        self.costs: DefaultDict[str, float] = defaultdict(float)
        self.usage: DefaultDict[str, TokenUsage] = defaultdict(lambda: TokenUsage())
        self.counts: DefaultDict[str, int] = defaultdict(int)

    def record(self, operation: str, cost: CostBreakdown, usage: TokenUsage):
        """Record a single operation"""
        op = operation or "unknown"

        self.costs[op] += cost.total_cost
        self.counts[op] += 1

        # Accumulate usage
        current = self.usage[op]
        current.input_tokens += usage.input_tokens
        current.output_tokens += usage.output_tokens
        current.reasoning_tokens += usage.reasoning_tokens
        current.cached_tokens += usage.cached_tokens

    def report(self) -> str:
        """Generate cost report"""
        lines = ["=== LLM Cost Report ==="]

        total_cost = sum(self.costs.values())
        total_calls = sum(self.counts.values())

        lines.append(f"\nTotal Cost: ${total_cost:.4f}")
        lines.append(f"Total Calls: {total_calls:,}")
        lines.append(f"Average Cost per Call: ${total_cost / total_calls:.6f}\n")

        lines.append("By Operation:")
        for op in sorted(self.costs.keys(), key=lambda x: self.costs[x], reverse=True):
            cost = self.costs[op]
            count = self.counts[op]
            usage = self.usage[op]
            pct = (cost / total_cost) * 100 if total_cost > 0 else 0

            lines.append(f"  {op}:")
            lines.append(f"    Cost: ${cost:.4f} ({pct:.1f}%)")
            lines.append(f"    Calls: {count:,}")
            lines.append(f"    Avg: ${cost / count:.6f} per call")
            lines.append(f"    Tokens: {usage.total_tokens:,}")

        return "\n".join(lines)

    def get_cost_by_operation(self, operation: str) -> float:
        """Get total cost for specific operation"""
        return self.costs.get(operation, 0.0)

    def get_usage_by_operation(self, operation: str) -> TokenUsage:
        """Get total usage for specific operation"""
        return self.usage.get(operation, TokenUsage())
```

---

## Usage Examples

### Basic Usage

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from chatforge.llm import LangChainLLMPort

# Wrap any LangChain model
base_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
llm = LangChainLLMPort(base_llm, operation_name="npc_conversation")

# Use LangChain interface (no changes!)
response = await llm.ainvoke([
    HumanMessage(content="Tell me about yourself")
])

# Access standard LangChain properties
print(response.content)  # "I am a helpful AI assistant..."

# Access enhanced tracking properties
print(response.usage_typed)
# TokenUsage(input_tokens=12, output_tokens=25, reasoning_tokens=0)

print(response.cost)
# CostBreakdown(input_cost=0.0000018, output_cost=0.000015, total_cost=0.0000168)

print(response.operation_name)
# "npc_conversation"

print(response.elapsed_ms)
# 456.2
```

### Cost Tracking Across Operations

```python
from chatforge.llm import LangChainLLMPort, CostTracker

# Shared cost tracker
tracker = CostTracker()

# Different LLMs for different operations
npc_llm = LangChainLLMPort(
    ChatOpenAI(model="gpt-4o-mini"),
    operation_name="npc_conversation",
    cost_tracker=tracker
)

quest_llm = LangChainLLMPort(
    ChatAnthropic(model="claude-3-5-sonnet-20241022"),
    operation_name="quest_generation",
    cost_tracker=tracker
)

# Use them...
await npc_llm.ainvoke([HumanMessage(content="Hi")])
await npc_llm.ainvoke([HumanMessage(content="How are you?")])
await quest_llm.ainvoke([HumanMessage(content="Generate a quest")])

# Get report
print(tracker.report())

# Output:
# === LLM Cost Report ===
#
# Total Cost: $0.0234
# Total Calls: 3
# Average Cost per Call: $0.007800
#
# By Operation:
#   quest_generation:
#     Cost: $0.0180 (76.9%)
#     Calls: 1
#     Avg: $0.018000 per call
#     Tokens: 1,250
#   npc_conversation:
#     Cost: $0.0054 (23.1%)
#     Calls: 2
#     Avg: $0.002700 per call
#     Tokens: 450
```

### Streaming with Tracking

```python
llm = LangChainLLMPort(
    ChatOpenAI(model="gpt-4o-mini"),
    operation_name="combat_narration",
    cost_tracker=tracker
)

# Streaming works normally
async for chunk in llm.astream([HumanMessage(content="Describe the battle")]):
    print(chunk.content, end="", flush=True)

# Cost is tracked automatically in the background
print(f"\nTotal narration cost so far: ${tracker.get_cost_by_operation('combat_narration'):.4f}")
```

### Works with All LangChain Features

```python
from langchain_core.tools import tool

@tool
def get_inventory() -> str:
    """Get player's inventory"""
    return "sword, shield, potion"

# Tool binding works
llm_with_tools = LangChainLLMPort(
    ChatOpenAI(model="gpt-4o-mini").bind_tools([get_inventory]),
    operation_name="npc_with_tools"
)

# Structured output works
from pydantic import BaseModel

class QuestObjectives(BaseModel):
    title: str
    objectives: list[str]

llm_with_schema = LangChainLLMPort(
    ChatOpenAI(model="gpt-4o-mini").with_structured_output(QuestObjectives),
    operation_name="quest_extraction"
)

# Everything LangChain supports, we support!
```

---

## Comparison: LLMPort vs LangChainLLMPort

| Aspect | LLMPort (Complex) | LangChainLLMPort (Simple) |
|--------|-------------------|---------------------------|
| **Code Size** | ~800 lines | ~150 lines |
| **Learning Curve** | New interface to learn | Already know LangChain |
| **Provider Support** | Need adapter per provider | Works with ALL LangChain models |
| **Features** | Have to reimplement | All LangChain features work |
| **Maintenance** | High (track LangChain changes) | Low (just wrapper) |
| **Framework Independence** | ✅ Yes | ❌ No (coupled to LangChain) |
| **Cost Tracking** | ✅ Yes | ✅ Yes |
| **Typed Usage** | ✅ Yes | ✅ Yes |
| **Operation Tracking** | ✅ Yes | ✅ Yes |
| **Streaming** | Have to implement | ✅ Works automatically |
| **Batching** | Have to implement | ✅ Works automatically |
| **Tools** | Have to implement | ✅ Works automatically |
| **Structured Output** | Have to implement | ✅ Works automatically |

---

## When to Use Which

### Use LangChainLLMPort if:

✅ You're okay depending on LangChain long-term
✅ You want minimal code and maintenance
✅ You want all LangChain features (tools, chains, agents)
✅ You just need tracking on top of LangChain
✅ **Recommended for 90% of use cases**

### Use LLMPort if:

✅ You want framework independence
✅ You might migrate away from LangChain someday
✅ You want complete control over the interface
✅ You don't need LangChain features (tools, chains)
✅ **Recommended for library authors or framework builders**

---

## For ChamberProtocolAI

**Recommendation: Use LangChainLLMPort**

Why?
1. **You're already using LangChain** - No reason to abstract it away
2. **Minimal code** - Focus on game logic, not infrastructure
3. **All features work** - Streaming, tools, etc.
4. **Easy to understand** - Team already knows LangChain

Example:
```python
# chamberprotocol/api/dependencies.py

from chatforge.llm import LangChainLLMPort, CostTracker
from langchain_openai import ChatOpenAI

# Shared cost tracker
tracker = CostTracker()

def get_npc_llm() -> LangChainLLMPort:
    """Get LLM for NPC conversations"""
    return LangChainLLMPort(
        ChatOpenAI(model="gpt-4o-mini", temperature=0.8),
        operation_name="npc_conversation",
        cost_tracker=tracker
    )

def get_quest_llm() -> LangChainLLMPort:
    """Get LLM for quest generation"""
    return LangChainLLMPort(
        ChatOpenAI(model="gpt-4o", temperature=0.7),
        operation_name="quest_generation",
        cost_tracker=tracker
    )

@app.get("/costs")
async def get_costs():
    """Cost analytics endpoint"""
    return {"report": tracker.report()}
```

---

## For Chatforge Library

**Recommendation: Provide BOTH**

```python
# chatforge/llm/__init__.py

# Simple approach (recommended for most)
from .langchain_wrapper import LangChainLLMPort

# Advanced approach (for framework independence)
from .ports import LLMPort, LLMStreamingPort
from .adapters import OpenAILLMAdapter, AnthropicLLMAdapter

# Supporting classes
from .tracking import TokenUsage, CostBreakdown, CostTracker
```

Users can choose based on their needs:
- **90% use `LangChainLLMPort`** - Simple, works great
- **10% use `LLMPort` adapters** - Need framework independence

---

## Next Steps

1. **Implement `LangChainLLMPort`** (~150 lines)
2. **Implement supporting dataclasses** (TokenUsage, CostBreakdown, CostTracker)
3. **Add model pricing database** (can start simple, expand later)
4. **Write tests**
5. **Document with examples**
6. **Consider adding `LLMPort` later if needed**

**Start simple, add complexity only if actually needed.**

---

## Summary

**LangChainLLMPort Philosophy:**

> Don't fight LangChain. Embrace it, enhance it, track it.

**One class. Minimal code. Maximum value.**

✅ Typed usage (TokenUsage)
✅ Cost tracking (CostBreakdown)
✅ Operation tracking (operation_name)
✅ All LangChain features work
✅ Works with ANY LangChain model
✅ ~150 lines of code total

**This gives us 80% of the value with 20% of the complexity.**
