# LLMPort: Vision & Philosophy

**Date:** 2025-12-26
**Status:** Design Phase
**Goal:** Define a clean abstraction for LLM operations in chatforge

---

## The Problem

### What's Wrong Today?

Applications using LLMs face several challenges:

1. **Coupling to LangChain Framework**
   - Code depends on LangChain's `BaseChatModel`, `AIMessage`, etc.
   - Domain logic imports LangChain classes (framework dependency)
   - Testing requires mocking LangChain internals
   - **Note:** LangChain DOES provide provider abstraction (`BaseChatModel`), but you're still coupled to the LangChain framework itself

2. **Unstructured Responses**
   - LangChain returns `AIMessage` with `response_metadata: Dict[str, Any]`
   - Token usage is buried in untyped dictionaries
   - No built-in cost tracking
   - No operation categorization

3. **No Observability**
   - Can't track which operations cost how much
   - Can't measure retry attempts or failures
   - Can't trace related operations (chain-of-thought)
   - No timestamps or performance metrics

4. **Framework Lock-in**
   - Domain logic depends on LangChain classes
   - Can't easily test without LangChain infrastructure
   - Hard to migrate if LangChain changes

### Real-World Pain Points

**Example 1: Cost Tracking**
```
"How much did NPC conversations cost this month?"
→ Have to parse logs and manually calculate
```

**Example 2: Provider Switching**
```
"OpenAI raised prices, let's try Anthropic for NPCs"
→ Have to change code in 20+ places
```

**Example 3: Testing**
```
"Let's test the quest generator without calling OpenAI"
→ Have to mock LangChain internals, complex setup
```

---

## The Vision

### What is LLMPort?

**LLMPort is an interface (contract) that abstracts LLM operations.**

It's NOT:
- ❌ A new LLM client (we use LangChain)
- ❌ A replacement for OpenAI/Anthropic SDKs
- ❌ A reimplementation of chat models

It IS:
- ✅ A **contract** between your app and LLM infrastructure
- ✅ A **structured API** with typed requests and responses
- ✅ A **tracking layer** for cost, usage, and observability
- ✅ A **wrapper** around LangChain that keeps its ecosystem

### Core Principle: Separation of Concerns

```
┌──────────────────────────────────────────────────────┐
│  WHAT (Domain Logic)                                  │
│  "Generate NPC response with personality X"           │
│  "Summarize player's last 5 actions"                  │
│  "Extract quest items from conversation"             │
│                                                       │
│  → Your application code                             │
│  → Depends on LLMPort (interface)                    │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│  HOW (Infrastructure)                                 │
│  "Use OpenAI gpt-4o-mini via LangChain"              │
│  "Extract tokens from response metadata"             │
│  "Calculate cost based on model pricing"             │
│                                                       │
│  → Adapter implementations                           │
│  → Depends on LangChain, OpenAI SDK                  │
└──────────────────────────────────────────────────────┘
```

**Your domain logic knows WHAT to do, not HOW it's done.**

---

## What LLMPort Enables

### 1. Provider Independence

**Before (Tight Coupling):**
```python
class NPCController:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini")  # Locked to OpenAI!

    async def talk(self, message: str):
        response = await self.llm.ainvoke([HumanMessage(content=message)])
        return response.content
```

**After (Loose Coupling):**
```python
class NPCController:
    def __init__(self, llm: LLMPort):  # Depends on interface!
        self.llm = llm

    async def talk(self, message: str):
        request = LLMRequest(messages=[...])
        response = await self.llm.generate(request)
        return response.content
```

**Benefit:** Change provider in ONE place (composition root), not everywhere.

### 2. Structured Observability

**Before (Unstructured):**
```python
response = llm.invoke([message])
# How many tokens? → Dig into response_metadata dict
# How much did it cost? → Calculate manually
# Which operation was this? → No way to know
```

**After (Structured):**
```python
response = llm.generate(request)

print(response.usage)
# TokenUsage(input_tokens=120, output_tokens=45)

print(response.cost)
# CostBreakdown(input_cost=0.000018, output_cost=0.000027, total_cost=0.000045)

print(response.operation_name)
# "npc_conversation"
```

**Benefit:** Every LLM call includes usage, cost, and operation tracking.

### 3. Easy Testing

**Before (Hard to Test):**
```python
# Test requires:
# - Mock ChatOpenAI
# - Mock AIMessage with correct metadata structure
# - Complex setup for each test
```

**After (Easy to Test):**
```python
# Test uses simple mock:
class MockLLM(LLMPort):
    async def generate(self, request):
        return LLMResponse(
            success=True,
            content="Mock response",
            usage=TokenUsage(input_tokens=10, output_tokens=5),
            cost=CostBreakdown(total_cost=0.0)
        )

# Test domain logic in isolation:
controller = NPCController(llm=MockLLM())
response = await controller.talk("Hello")
assert "Mock response" in response
```

**Benefit:** Test domain logic without LLM API calls.

### 4. Operation Attribution

**Before:**
```
"This month we spent $47.32 on OpenAI"
→ But which features cost how much?
```

**After:**
```python
# Every request has operation_name
request = LLMRequest(
    messages=[...],
    operation_name="npc_conversation"  # Tag it!
)

# Later, analyze costs:
# - npc_conversation: $12.50 (26% of total)
# - quest_generation: $18.30 (39% of total)
# - combat_narration: $8.20 (17% of total)
# - item_description: $8.32 (18% of total)
```

**Benefit:** Know which operations cost how much.

### 5. Multi-Provider Strategy

**Before (One Provider):**
```
All operations use OpenAI gpt-4o-mini
```

**After (Strategic Provider Selection):**
```python
# Composition root
cheap_llm = OpenAILLMAdapter(model="gpt-4o-mini")  # $0.15/$0.60 per 1M tokens
smart_llm = AnthropicLLMAdapter(model="claude-3-5-sonnet")  # Expensive but good

# Different operations use different models
npc_controller = NPCController(llm=cheap_llm)  # NPCs don't need Claude
quest_engine = QuestEngine(llm=smart_llm)      # Quests need better quality
```

**Benefit:** Optimize cost vs quality per operation.

---

## Design Principles

### 1. Simple Interface

LLMPort should have ONE primary method:

```
generate(request: LLMRequest) -> LLMResponse
```

That's it. Simple, predictable, testable.

### 2. Structured Data

No `Dict[str, Any]`. Everything is typed:

- `LLMRequest` - What you want
- `LLMResponse` - What you got
- `TokenUsage` - How many tokens
- `CostBreakdown` - How much it cost

### 3. Keep LangChain Ecosystem

LLMPort is a **wrapper**, not a **replacement**:

- ✅ Keep LangChain tools
- ✅ Keep LangChain chains
- ✅ Keep LangChain agents
- ✅ Keep LangChain integrations

Just add structured tracking on top.

### 4. Progressive Disclosure

Start simple, add complexity when needed:

**Minimal:**
```python
request = LLMRequest(messages=[...])
response = llm.generate(request)
```

**With tracking:**
```python
request = LLMRequest(
    messages=[...],
    operation_name="npc_talk"
)
```

**With structured output:**
```python
request = LLMRequest(
    messages=[...],
    operation_name="extract_items",
    response_schema=ItemList  # Pydantic model
)
```

**With chain-of-thought:**
```python
request = LLMRequest(
    messages=[...],
    operation_name="reasoning_step_2",
    previous_response_id=step1_response.response_id
)
```

You only add complexity when you need it.

### 5. Composition Over Inheritance

Don't subclass LangChain models. Wrap them:

```
OpenAILLMAdapter HAS-A ChatOpenAI (composition)
NOT
OpenAILLMAdapter IS-A ChatOpenAI (inheritance)
```

**Why?** Composition is flexible. If LangChain changes, only adapters break, not your domain logic.

---

## What LLMPort is NOT

### ❌ NOT a Complete LLM Service

LLMPort is NOT trying to be:
- A full LLM platform (like LLMService)
- A model hosting service
- A prompt management system
- A fine-tuning pipeline

It's JUST an interface for calling LLMs with structured tracking.

### ✅ Streaming is Separate

LLMPort focuses on simple request/response.

Streaming is a separate interface:
```python
class LLMPort(ABC):
    async def generate(request: LLMRequest) -> LLMResponse:
        """Simple mode - most common use case"""
        ...

class LLMStreamingPort(LLMPort):
    async def generate_stream(request: LLMRequest) -> AsyncIterator[str]:
        """Streaming mode - optional capability"""
        ...
```

This follows the **Interface Segregation Principle** - clients only depend on what they need.

**Usage Example:**
```python
# Simple NPC conversations - doesn't need streaming
class NPCController:
    def __init__(self, llm: LLMPort):  # ← Basic interface
        self.llm = llm

    async def talk(self, message: str) -> str:
        response = await self.llm.generate(request)
        return response.content

# Real-time combat narration - needs streaming for live updates
class CombatNarrator:
    def __init__(self, llm: LLMStreamingPort):  # ← Streaming interface
        self.llm = llm

    async def narrate_combat(self, action: str):
        async for chunk in self.llm.generate_stream(request):
            print(chunk, end="", flush=True)  # Live updates!
```

### ❌ NOT Provider-Specific

LLMPort should work with ANY LLM provider:
- OpenAI
- Anthropic
- Google Gemini
- AWS Bedrock
- Local models (Ollama, vLLM)

The interface is provider-agnostic.

### ❌ NOT a Replacement for Domain Logic

LLMPort doesn't know about:
- NPC personalities
- Quest generation
- Combat narration

Those are YOUR domain responsibilities. LLMPort just provides a clean way to call LLMs.

---

## Success Metrics

How do we know LLMPort is successful?

### Developer Experience

**Easy to use:**
```python
# Should feel natural
request = LLMRequest(messages=[...])
response = await llm.generate(request)
print(response.content)
```

**Easy to test:**
```python
# Should be trivial to mock
mock_llm = MockLLMAdapter(response="Test response")
controller = NPCController(llm=mock_llm)
```

**Easy to swap providers:**
```python
# Before: openai_adapter
# After: anthropic_adapter
# Change ONE line, everything still works
```

### Observability

**Track costs:**
```python
total_cost = sum(r.cost.total_cost for r in all_responses)
print(f"This session cost ${total_cost:.4f}")
```

**Track usage:**
```python
total_tokens = sum(r.usage.total_tokens for r in all_responses)
print(f"Used {total_tokens:,} tokens")
```

**Track operations:**
```python
by_operation = defaultdict(float)
for r in all_responses:
    by_operation[r.operation_name] += r.cost.total_cost

# npc_conversation: $2.40
# quest_generation: $5.10
```

### Flexibility

**Support multiple providers simultaneously:**
```python
npc_llm = OpenAILLMAdapter(model="gpt-4o-mini")
quest_llm = AnthropicLLMAdapter(model="claude-3-5-sonnet")
```

**Support structured output:**
```python
request = LLMRequest(
    messages=[...],
    response_schema=QuestObjectives  # Auto-parse JSON
)
```

**Support chain-of-thought:**
```python
step1 = await llm.generate(request1)
step2_request = LLMRequest(
    messages=[...],
    previous_response_id=step1.response_id
)
```

---

## What's Next?

### Phase 1: Core Interface (Minimal)

Define:
- `LLMPort` interface
- `LLMRequest` / `LLMResponse` dataclasses
- `TokenUsage` / `CostBreakdown` dataclasses
- `OpenAILLMAdapter` implementation

Goal: Get basic structured requests working.

### Phase 2: Observability

Add:
- `operation_name` tracking
- Cost calculation per provider
- Usage aggregation

Goal: Know which operations cost how much.

### Phase 3: Advanced Features

Add:
- Retry logic (optional)
- Structured output support
- Chain-of-thought tracking
- `LLMStreamingPort` interface for streaming support

Goal: Support complex use cases without bloating the core interface.

---

## Questions to Answer

Before we implement, we need to decide:

### 1. How Simple Should LLMRequest Be?

**Option A: Minimal**
```python
@dataclass
class LLMRequest:
    messages: List[LLMMessage]
    model: Optional[str] = None
    temperature: Optional[float] = None
```

**Option B: Full-Featured**
```python
@dataclass
class LLMRequest:
    messages: List[LLMMessage]
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    operation_name: Optional[str] = None
    request_id: Optional[str] = None
    response_schema: Optional[Type[BaseModel]] = None
    previous_response_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

**Decision needed:** Start minimal, add features incrementally?

### 2. Should We Track Retries?

**Option A: No retry tracking (simple)**
- Adapter either succeeds or fails
- Retries are internal implementation detail

**Option B: Full retry tracking (complex)**
- Track every attempt
- Record backoff times
- Provide detailed failure info

**Decision needed:** Do we need retry observability?

### 3. How Much Cost Detail?

**Option A: Simple total**
```python
@dataclass
class LLMResponse:
    cost: float  # Just total
```

**Option B: Detailed breakdown**
```python
@dataclass
class CostBreakdown:
    input_cost: float
    output_cost: float
    reasoning_cost: float  # For o-series
    cache_write_cost: float  # For Anthropic
    cache_read_cost: float
```

**Decision needed:** How granular should cost tracking be?

### 4. How to Handle Streaming?

**Option A: Single interface with both methods**
```python
class LLMPort(ABC):
    async def generate(self, request) -> LLMResponse:
        pass

    async def generate_stream(self, request) -> AsyncIterator[str]:
        pass  # What if provider doesn't support streaming?
```

**Option B: Separate interfaces (Interface Segregation Principle)**
```python
class LLMPort(ABC):
    """Simple request/response"""
    async def generate(self, request) -> LLMResponse:
        pass

class LLMStreamingPort(LLMPort):
    """Streaming support - extends LLMPort"""
    async def generate_stream(self, request) -> AsyncIterator[str]:
        pass
```

**Decision:** Use **separate interfaces** (Option B)
- ✅ Not all providers support streaming
- ✅ Clients only depend on what they need
- ✅ Clear type checking (`NPCController` needs `LLMPort`, `CombatNarrator` needs `LLMStreamingPort`)
- ✅ Optional feature, explicit contract

---

## Core Philosophy

### Start Simple

- ✅ Define minimal interface first
- ✅ Add complexity only when needed
- ✅ Keep it easy to understand
- ✅ Optimize for common case (90%)

### Focus on Value

What problems are we ACTUALLY solving?
1. **Provider independence** - Switch OpenAI → Anthropic easily
2. **Structured responses** - Typed usage/cost instead of Dict[str, Any]
3. **Easy testing** - Mock LLMPort instead of LangChain internals
4. **Cost tracking** - Know which operations cost how much

Don't add features that don't solve real problems.

### Keep LangChain

LangChain is good at:
- Provider integrations (20+ providers)
- Tools ecosystem
- Chains and agents
- Community support

We're NOT replacing it. We're wrapping it with structure.

### Domain-Agnostic

LLMPort should work for:
- Games (NPCs, quests, narration)
- Customer service bots
- Code assistants
- Medical chatbots
- Any LLM application

It's infrastructure, not domain logic.

---

## Summary

**LLMPort Vision:**

> A simple, structured interface for LLM operations that provides provider independence, cost tracking, and easy testing while keeping LangChain's ecosystem benefits.

**Key Decisions:**
1. ✅ Wrap LangChain, don't replace it
2. ✅ Structured data (no Dict[str, Any])
3. ✅ Simple interface (`generate()`)
4. ✅ Progressive complexity (start minimal)
5. ✅ Streaming as separate port (`LLMStreamingPort` extends `LLMPort`)
6. ❓ Retry tracking level (simple or detailed?)
7. ❓ Cost granularity (total or breakdown?)
8. ❓ How minimal should `LLMRequest` be?

**Next Step:** Discuss and decide on the open questions, then move to implementation.
