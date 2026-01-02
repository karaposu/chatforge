# Adapting LLMService Dataclasses for Chatforge LLMPort

**Question:** Can we use `GenerationRequest` and `GenerationResult` directly in chatforge?

**Answer:** YES - with modifications! Their design is excellent, we just need to:
1. Remove LLMService-specific fields we don't need
2. Adapt for LangChain compatibility
3. Simplify overly complex parts

---

## Analysis: GenerationRequest

### What's Great (KEEP)

```python
# From LLMService schemas.py:277-327
@dataclass
class GenerationRequest:
    # ── RUNTIME ───────────────────────────────────────────────
    model: Optional[str] = None                    # ✅ KEEP
    operation_name: Optional[str] = None           # ✅ KEEP (for cost tracking)
    request_id: Optional[Union[str,int]] = None    # ✅ KEEP (for tracing)
    number_of_retries: Optional[int] = None        # ✅ KEEP

    # ── RESULT HANDLING ───────────────────────────────────────
    output_type: Literal["json", "str"] = "str"    # ⚠️ SIMPLIFY
    fail_fallback_value: Optional[str] = None      # ⚠️ MAYBE

    # ── MULTIMODAL ────────────────────────────────────────────
    system_prompt: Optional[str] = None            # ✅ KEEP
    user_prompt: Optional[str] = None              # ✅ KEEP
    assistant_text: Optional[str] = None           # ✅ KEEP (seed message)
    input_audio_b64: Optional[str] = None          # ✅ KEEP
    images: Optional[List[str]] = None             # ✅ KEEP (base64)
    tool_call: Optional[Dict[str, any]] = None     # ✅ KEEP

    # ── ADVANCED ──────────────────────────────────────────────
    previous_response_id: Optional[str] = None     # ✅ KEEP (CoT chaining)
    reasoning_effort: Optional[Literal["low", "medium", "high"]] = None  # ✅ KEEP
    response_schema: Optional[Type[PydanticModel]] = None  # ✅ KEEP
    strict_mode: bool = True                       # ✅ KEEP
```

### What to Remove/Change

```python
# REMOVE - Too specific to LLMService's pipeline system
output_data_format: Literal["text", "audio", "both"] = "text"  # ❌ REMOVE
audio_output_config: Optional[Dict[str, any]] = None           # ❌ REMOVE
verbosity: Optional[Literal["low", "medium", "high"]] = None   # ❌ REMOVE
parse_response: bool = True                                    # ❌ REMOVE

# CHANGE - Simplify to just need messages (like LangChain)
# Instead of system_prompt, user_prompt separately,
# Use messages: List[LLMMessage]
```

---

## Analysis: GenerationResult

### What's Great (KEEP)

```python
# From LLMService schemas.py:452-489
@dataclass
class GenerationResult:
    # ── CORE ──────────────────────────────────────────────────
    success: bool                                  # ✅ KEEP
    trace_id: str                                  # ✅ KEEP
    content: Optional[Any] = None                  # ✅ KEEP
    raw_content: Optional[str] = None              # ✅ KEEP
    raw_response: Optional[Any] = None             # ✅ KEEP
    model: Optional[str] = None                    # ✅ KEEP

    # ── RETRY TRACKING ────────────────────────────────────────
    retried: Optional[bool] = None                 # ✅ KEEP
    attempt_count: Optional[int] = None            # ✅ KEEP
    total_invoke_duration_ms: Optional[float] = None  # ✅ KEEP
    total_backoff_ms: Optional[float] = None       # ✅ KEEP

    # ── USAGE & COST ──────────────────────────────────────────
    usage: Dict[str, Any] = field(default_factory=dict)  # ✅ KEEP
    elapsed_time: Optional[float] = None           # ✅ KEEP

    # ── TRACKING ──────────────────────────────────────────────
    request_id: Optional[Union[str, int]] = None   # ✅ KEEP
    operation_name: Optional[str] = None           # ✅ KEEP
    response_id: Optional[str] = None              # ✅ KEEP (CoT)

    # ── DETAILED TRACKING ─────────────────────────────────────
    backoff: BackoffStats = field(default_factory=BackoffStats)  # ✅ KEEP
    timestamps: Optional[EventTimestamps] = None   # ✅ KEEP
```

### What to Remove/Change

```python
# REMOVE - Pipeline-specific
pipeline_steps_results: List[PipelineStepResult] = field(default_factory=list)  # ❌ REMOVE
formatted_prompt: Optional[str] = None             # ❌ REMOVE
unformatted_prompt: Optional[str] = None           # ❌ REMOVE

# SIMPLIFY - Keep concept but structure differently
# Instead of flat RPM/TPM fields, use a nested RateLimitStats dataclass
rpm_at_the_beginning: Optional[int] = None         # ⚠️ SIMPLIFY
rpm_at_the_end: Optional[int] = None               # ⚠️ SIMPLIFY
rpm_waited: Optional[bool] = None                  # ⚠️ SIMPLIFY
rpm_wait_loops: Optional[int] = None               # ⚠️ SIMPLIFY
rpm_waited_ms: Optional[int] = None                # ⚠️ SIMPLIFY
# ... same for TPM                                 # ⚠️ SIMPLIFY

# CHANGE - Make usage typed instead of Dict[str, Any]
usage: Dict[str, Any]  # ❌ CHANGE to TokenUsage dataclass
```

---

## Adapted Dataclasses for Chatforge

### 1. LLMRequest (Adapted from GenerationRequest)

```python
"""
chatforge/llm/request.py

Adapted from LLMService's GenerationRequest.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Type, Union, Literal
from pydantic import BaseModel as PydanticModel


@dataclass
class LLMMessage:
    """
    Single message in conversation.

    Simpler than having separate system_prompt, user_prompt fields.
    """
    role: Literal["system", "user", "assistant"]
    content: str

    # Optional multimodal content
    images: Optional[List[str]] = None             # Base64 encoded images
    audio: Optional[str] = None                    # Base64 encoded audio

    # Optional metadata
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None

    def __post_init__(self):
        """Validate role."""
        if self.role not in ("system", "user", "assistant"):
            raise ValueError(f"Invalid role: {self.role}")


@dataclass
class LLMRequest:
    """
    LLM request with comprehensive configuration.

    Adapted from LLMService's GenerationRequest with these changes:
    - Uses messages instead of separate system_prompt/user_prompt
    - Removed audio output config (not needed for chatforge)
    - Removed verbosity (provider-specific)
    - Simplified output handling

    Example:
        request = LLMRequest(
            messages=[
                LLMMessage(role="system", content="You are helpful"),
                LLMMessage(role="user", content="Hello"),
            ],
            model="gpt-4o-mini",
            operation_name="greeting",
            temperature=0.7,
        )
    """
    # ── CORE (Required) ───────────────────────────────────────
    messages: List[LLMMessage]

    # ── MODEL CONFIG (Optional overrides) ─────────────────────
    model: Optional[str] = None                    # Override default model
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None

    # ── TRACKING (Optional but recommended) ───────────────────
    operation_name: Optional[str] = None           # ⭐ For cost analytics
    request_id: Optional[Union[str, int]] = None   # ⭐ For tracing

    # ── RETRY CONFIG ──────────────────────────────────────────
    number_of_retries: Optional[int] = None        # Override default

    # ── STRUCTURED OUTPUT ─────────────────────────────────────
    response_schema: Optional[Type[PydanticModel]] = None  # ⭐ Pydantic model
    strict_mode: bool = True                       # Strict schema validation

    # ── ADVANCED FEATURES ─────────────────────────────────────
    previous_response_id: Optional[str] = None     # ⭐ CoT chaining (GPT-5)
    reasoning_effort: Optional[Literal["low", "medium", "high"]] = None  # GPT-5/o1

    # ── FALLBACK HANDLING ─────────────────────────────────────
    fail_fallback_value: Optional[str] = None      # Return this on failure

    # ── METADATA ──────────────────────────────────────────────
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate request."""
        if not self.messages:
            raise ValueError("At least one message is required")
```

### 2. Supporting Dataclasses

```python
"""
chatforge/llm/tracking.py

Tracking dataclasses adapted from LLMService.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class TokenUsage:
    """
    Token usage breakdown.

    Replaces GenerationResult's usage Dict[str, Any] with typed structure.
    """
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0                      # For GPT-5/o-series
    cached_tokens: int = 0                         # For Anthropic prompt caching

    @property
    def total_tokens(self) -> int:
        """Total tokens (excluding cached)."""
        return self.input_tokens + self.output_tokens + self.reasoning_tokens


@dataclass
class CostBreakdown:
    """
    Cost breakdown by token type.

    Computed from TokenUsage using model pricing.
    """
    input_cost: float = 0.0
    output_cost: float = 0.0
    reasoning_cost: float = 0.0
    cache_write_cost: float = 0.0                  # Anthropic
    cache_read_cost: float = 0.0                   # Anthropic

    @property
    def total_cost(self) -> float:
        """Total cost in USD."""
        return (
            self.input_cost +
            self.output_cost +
            self.reasoning_cost +
            self.cache_write_cost +
            self.cache_read_cost
        )

    def __str__(self) -> str:
        """Pretty print."""
        return f"${self.total_cost:.4f}"


@dataclass
class AttemptInfo:
    """
    Information about a single invocation attempt.

    From LLMService's InvocationAttempt.
    """
    attempt_number: int
    started_at: datetime
    ended_at: datetime
    error_message: Optional[str] = None
    backoff_ms: Optional[float] = None             # Backoff after this attempt

    @property
    def duration_ms(self) -> float:
        """Duration in milliseconds."""
        return (self.ended_at - self.started_at).total_seconds() * 1000


@dataclass
class BackoffStats:
    """
    Backoff statistics (from LLMService).

    Simplified - we don't implement RPM/TPM client-side limiting yet,
    so only track server-side retry backoff.
    """
    retry_loops: int = 0                           # Number of retries
    retry_ms: float = 0.0                          # Total backoff time

    # Future: Add RPM/TPM tracking if needed
    # rpm_loops: int = 0
    # rpm_ms: float = 0.0
    # tpm_loops: int = 0
    # tpm_ms: float = 0.0


@dataclass
class EventTimestamps:
    """
    Optional detailed timestamp tracking (from LLMService).

    Simplified - only core timestamps, not full pipeline.
    """
    request_received_at: Optional[datetime] = None
    llm_call_started_at: Optional[datetime] = None
    llm_call_ended_at: Optional[datetime] = None
    response_completed_at: Optional[datetime] = None

    attempts: List[AttemptInfo] = field(default_factory=list)

    def total_duration_ms(self) -> float:
        """Total duration from request to completion."""
        if self.response_completed_at and self.request_received_at:
            return (
                self.response_completed_at - self.request_received_at
            ).total_seconds() * 1000
        return 0.0

    def total_backoff_ms(self) -> float:
        """Total backoff time across all attempts."""
        return sum(a.backoff_ms or 0.0 for a in self.attempts)
```

### 3. LLMResponse (Adapted from GenerationResult)

```python
"""
chatforge/llm/response.py

Adapted from LLMService's GenerationResult.
"""

from dataclasses import dataclass, field
from typing import Optional, Any, Union, List, Dict
from chatforge.llm.tracking import (
    TokenUsage, CostBreakdown, AttemptInfo, BackoffStats, EventTimestamps
)


@dataclass
class LLMResponse:
    """
    LLM response with comprehensive tracking.

    Adapted from LLMService's GenerationResult with these changes:
    - usage is typed (TokenUsage) instead of Dict[str, Any]
    - cost is typed (CostBreakdown) instead of mixed in usage
    - Removed pipeline-specific fields
    - Removed RPM/TPM flat fields (could add RateLimitStats later)
    - Simplified prompt tracking

    Example:
        response = await llm_handler.invoke(request)

        print(f"Content: {response.content}")
        print(f"Cost: ${response.cost.total_cost:.4f}")
        print(f"Tokens: {response.usage.total_tokens}")
        print(f"Retries: {response.retry_count}")
        print(f"Duration: {response.elapsed_ms:.0f}ms")
    """
    # ── CORE RESPONSE ─────────────────────────────────────────
    success: bool
    trace_id: str                                  # UUID for this call

    # ── CONTENT ───────────────────────────────────────────────
    content: Optional[str] = None                  # Processed content
    raw_content: Optional[str] = None              # Initial LLM output
    raw_response: Optional[Any] = None             # Complete response object

    # ── MODEL ─────────────────────────────────────────────────
    model: Optional[str] = None                    # Actual model used

    # ── USAGE & COST (TYPED) ──────────────────────────────────
    usage: TokenUsage = field(default_factory=TokenUsage)
    cost: CostBreakdown = field(default_factory=CostBreakdown)

    # ── TIMING ────────────────────────────────────────────────
    elapsed_time: Optional[float] = None           # Total seconds (for compatibility)
    total_invoke_duration_ms: Optional[float] = None  # LLM call duration
    total_backoff_ms: Optional[float] = None       # Total backoff time

    @property
    def elapsed_ms(self) -> float:
        """Total elapsed time in milliseconds."""
        if self.elapsed_time:
            return self.elapsed_time * 1000
        return self.total_invoke_duration_ms or 0.0

    # ── RETRY TRACKING ────────────────────────────────────────
    retried: Optional[bool] = None                 # Was retry needed?
    attempt_count: Optional[int] = None            # Number of attempts
    attempts: List[AttemptInfo] = field(default_factory=list)

    @property
    def retry_count(self) -> int:
        """Number of retries (attempts - 1)."""
        if self.attempt_count:
            return max(0, self.attempt_count - 1)
        return max(0, len(self.attempts) - 1)

    # ── BACKOFF STATS ─────────────────────────────────────────
    backoff: BackoffStats = field(default_factory=BackoffStats)

    # ── DETAILED TIMESTAMPS (OPTIONAL) ────────────────────────
    timestamps: Optional[EventTimestamps] = None

    # ── TRACKING ──────────────────────────────────────────────
    request_id: Optional[Union[str, int]] = None
    operation_name: Optional[str] = None           # For cost analytics

    # ── ADVANCED ──────────────────────────────────────────────
    response_id: Optional[str] = None              # For CoT chaining
    response_type: Optional[str] = None            # "text" | "json" | "audio"

    # ── ERROR INFO ────────────────────────────────────────────
    error_message: Optional[str] = None

    # ── METADATA ──────────────────────────────────────────────
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ── ORIGINAL REQUEST (OPTIONAL) ───────────────────────────
    generation_request: Optional[Any] = None       # Copy of LLMRequest

    def __str__(self) -> str:
        """Pretty print for logs."""
        lines = [
            f"LLMResponse(success={self.success})",
            f"  Model: {self.model}",
            f"  Tokens: {self.usage.total_tokens}",
            f"  Cost: {self.cost}",
            f"  Duration: {self.elapsed_ms:.0f}ms",
            f"  Retries: {self.retry_count}",
        ]

        if self.operation_name:
            lines.append(f"  Operation: {self.operation_name}")

        if self.error_message:
            lines.append(f"  Error: {self.error_message}")

        return "\n".join(lines)
```

---

## Comparison: Before vs After

### GenerationRequest → LLMRequest

**Kept:**
- ✅ `model`, `operation_name`, `request_id`
- ✅ Multimodal support (`images`, `audio`)
- ✅ Structured output (`response_schema`, `strict_mode`)
- ✅ CoT chaining (`previous_response_id`)
- ✅ Retry config (`number_of_retries`)
- ✅ Validation in `__post_init__`

**Changed:**
- ✅ Separate `system_prompt`, `user_prompt` → Unified `messages: List[LLMMessage]`
- ✅ Better matches LangChain's message model

**Removed:**
- ❌ `output_data_format` (too specific)
- ❌ `audio_output_config` (not needed yet)
- ❌ `verbosity` (provider-specific)
- ❌ `parse_response` (implicit in response_schema)

### GenerationResult → LLMResponse

**Kept:**
- ✅ All core fields (`success`, `content`, `model`, `trace_id`)
- ✅ Retry tracking (`retried`, `attempt_count`, `attempts`)
- ✅ Timing (`elapsed_time`, `total_invoke_duration_ms`)
- ✅ `BackoffStats`, `EventTimestamps`
- ✅ `response_id` for CoT

**Changed:**
- ✅ `usage: Dict[str, Any]` → `usage: TokenUsage` (typed!)
- ✅ Cost fields extracted to `cost: CostBreakdown` (cleaner!)
- ✅ `attempts` list uses `AttemptInfo` dataclass

**Removed:**
- ❌ `pipeline_steps_results` (not needed)
- ❌ `formatted_prompt`, `unformatted_prompt` (not needed)
- ❌ Flat RPM/TPM fields (could add `RateLimitStats` later if needed)

---

## Benefits of This Approach

### 1. Proven Design
✅ LLMService's dataclasses are battle-tested
✅ Comprehensive tracking built-in
✅ Clear field organization

### 2. Type Safety
✅ `TokenUsage` dataclass instead of `Dict[str, Any]`
✅ `CostBreakdown` dataclass for costs
✅ IDE autocomplete works
✅ Easier to test

### 3. Extensibility
✅ Can add RPM/TPM tracking later (add `RateLimitStats`)
✅ Can add more detailed timestamps
✅ Can add provider-specific metadata

### 4. Clean Separation
✅ Request = what you want
✅ Response = what you got + how it went
✅ Tracking classes = reusable components

---

## Usage Example

```python
from chatforge.llm import LLMHandler, LLMRequest, LLMMessage

handler = LLMHandler(default_model="gpt-4o-mini")

# Create request (adapted from GenerationRequest)
request = LLMRequest(
    messages=[
        LLMMessage(role="system", content="You are helpful"),
        LLMMessage(role="user", content="What is 2+2?"),
    ],
    model="gpt-4o-mini",
    operation_name="simple_math",  # ⭐ From GenerationRequest
    temperature=0.7,
    request_id="req-123",          # ⭐ From GenerationRequest
)

# Invoke
response = await handler.invoke(request)

# Response (adapted from GenerationResult)
print(f"Success: {response.success}")
print(f"Content: {response.content}")
print(f"Model: {response.model}")

# ⭐ Typed usage (not Dict!)
print(f"Input tokens: {response.usage.input_tokens}")
print(f"Output tokens: {response.usage.output_tokens}")
print(f"Total tokens: {response.usage.total_tokens}")

# ⭐ Typed cost (not mixed with usage!)
print(f"Input cost: ${response.cost.input_cost:.4f}")
print(f"Output cost: ${response.cost.output_cost:.4f}")
print(f"Total cost: ${response.cost.total_cost:.4f}")

# ⭐ Retry info (from GenerationResult)
print(f"Retried: {response.retried}")
print(f"Attempt count: {response.attempt_count}")
for attempt in response.attempts:
    print(f"  Attempt {attempt.attempt_number}: {attempt.duration_ms:.0f}ms")

# ⭐ Timing (from GenerationResult)
print(f"Total duration: {response.elapsed_ms:.0f}ms")
print(f"Backoff time: {response.total_backoff_ms:.0f}ms")

# ⭐ Tracking (from GenerationResult)
print(f"Trace ID: {response.trace_id}")
print(f"Operation: {response.operation_name}")
```

---

## Summary

**Question:** Can we use GenerationRequest/Result?

**Answer:** YES! With smart adaptations:

1. **Keep the excellent design:**
   - Comprehensive field coverage
   - Multimodal support
   - Structured output support
   - Detailed tracking

2. **Make it better:**
   - Type usage/cost (not Dict)
   - Simplify message handling
   - Remove unnecessary fields

3. **Make it chatforge-compatible:**
   - Works with LangChain
   - Matches hexagonal architecture
   - Easy to extend

This gives us **LLMService's professional tracking** with **chatforge's architecture**! 🎉
