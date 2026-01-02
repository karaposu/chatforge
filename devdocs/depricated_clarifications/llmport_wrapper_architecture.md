# LLMPort: Professional Wrapper Over LangChain
## Combining LangChain's Ecosystem with LLMService's Tracking

**Date:** 2025-12-25
**Philosophy:** Keep LangChain, add professional observability layer
**Design:** Adapted dataclasses from LLMService (GenerationRequest/Result)

---

## Core Insight

**What we DON'T want:**
- ❌ Replace LangChain (lose tools, integrations, ecosystem)
- ❌ Reimplement OpenAI/Anthropic SDKs
- ❌ Maintain our own chat models

**What we DO want:**
- ✅ Structured request/response (adapted from LLMService)
- ✅ Cost tracking per operation
- ✅ Retry tracking with detailed attempts
- ✅ Typed usage/cost (not Dict[str, Any])
- ✅ Operation categorization
- ✅ CoT chaining support
- ✅ Structured output with Pydantic

**Solution:** LLMPort as a **wrapper** around LangChain models using LLMService's proven dataclass design.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  APPLICATION LAYER                                   │
│    - SiluetService                                   │
│    - ReActAgent                                      │
│    - ChatAPI                                         │
│    ↓ uses                                            │
├─────────────────────────────────────────────────────┤
│  CHATFORGE LLMPORT (Wrapper + Tracking)             │
│                                                      │
│  LLMRequest (adapted from GenerationRequest)        │
│    - messages: List[LLMMessage]                     │
│    - model: Optional[str]                           │
│    - operation_name: "summarize", "extract"         │
│    - response_schema: Optional[PydanticModel]       │
│    - previous_response_id: Optional[str]            │
│    ↓                                                 │
│  LLMHandler (tracking + retry logic)                │
│    - Tracks attempts (AttemptInfo)                  │
│    - Calculates costs (CostBreakdown)               │
│    - Records timestamps (EventTimestamps)           │
│    ↓                                                 │
│  LangChain Adapter                                  │
│    - Converts LLMRequest → LangChain messages       │
│    - Calls LangChain model                          │
│    - Extracts usage from AIMessage                  │
│    ↓                                                 │
├─────────────────────────────────────────────────────┤
│  LANGCHAIN (Ecosystem)                              │
│    - BaseChatModel                                  │
│    - ChatOpenAI, ChatAnthropic, ChatBedrock         │
│    - Tools, Chains, Agents                          │
│    ↓                                                 │
├─────────────────────────────────────────────────────┤
│  LLM PROVIDERS                                       │
│    - OpenAI API                                     │
│    - Anthropic API                                  │
│    - AWS Bedrock                                    │
└─────────────────────────────────────────────────────┘
```

---

## Dataclasses (Adapted from LLMService)

### 1. Supporting Dataclasses

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

    Adapted from LLMService's usage Dict[str, Any] - now typed!
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

    Separated from usage for clarity (LLMService mixed them).
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

    From LLMService's InvocationAttempt - tracks each retry.
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

    @property
    def total_ms(self) -> float:
        """Total backoff time."""
        return self.retry_ms


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

### 2. LLMRequest (Adapted from GenerationRequest)

```python
"""
chatforge/llm/request.py

Adapted from LLMService's GenerationRequest.

Changes from LLMService:
- Uses messages instead of separate system_prompt/user_prompt
- Removed audio output config (not needed)
- Removed verbosity (provider-specific)
- Simplified output handling
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Type, Union, Literal
from pydantic import BaseModel as PydanticModel


@dataclass
class LLMMessage:
    """
    Single message in conversation.

    Simpler than having separate system_prompt, user_prompt fields.
    Compatible with LangChain message format.
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
    operation_name: Optional[str] = None           # ⭐ For cost analytics (from GenerationRequest)
    request_id: Optional[Union[str, int]] = None   # ⭐ For tracing (from GenerationRequest)

    # ── RETRY CONFIG ──────────────────────────────────────────
    number_of_retries: Optional[int] = None        # Override default (from GenerationRequest)

    # ── STRUCTURED OUTPUT ─────────────────────────────────────
    response_schema: Optional[Type[PydanticModel]] = None  # ⭐ Pydantic model (from GenerationRequest)
    strict_mode: bool = True                       # Strict schema validation (from GenerationRequest)

    # ── ADVANCED FEATURES ─────────────────────────────────────
    previous_response_id: Optional[str] = None     # ⭐ CoT chaining (from GenerationRequest)
    reasoning_effort: Optional[Literal["low", "medium", "high"]] = None  # GPT-5/o1 (from GenerationRequest)

    # ── FALLBACK HANDLING ─────────────────────────────────────
    fail_fallback_value: Optional[str] = None      # Return this on failure (from GenerationRequest)

    # ── METADATA ──────────────────────────────────────────────
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate request."""
        if not self.messages:
            raise ValueError("At least one message is required")
```

### 3. LLMResponse (Adapted from GenerationResult)

```python
"""
chatforge/llm/response.py

Adapted from LLMService's GenerationResult.

Changes from LLMService:
- usage is typed (TokenUsage) instead of Dict[str, Any]
- cost is typed (CostBreakdown) instead of mixed in usage
- Removed pipeline-specific fields
- Removed flat RPM/TPM fields (could add later)
- Simplified prompt tracking
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

    Adapted from LLMService's GenerationResult with improvements:
    - Typed usage/cost (not Dict)
    - Cleaner field organization
    - Removed pipeline-specific fields

    Example:
        response = await llm_handler.invoke(request)

        print(f"Content: {response.content}")
        print(f"Cost: ${response.cost.total_cost:.4f}")
        print(f"Tokens: {response.usage.total_tokens}")
        print(f"Retries: {response.retry_count}")
        print(f"Duration: {response.elapsed_ms:.0f}ms")
    """
    # ── CORE RESPONSE ─────────────────────────────────────────
    success: bool                                  # From GenerationResult
    trace_id: str                                  # UUID for this call (from GenerationResult)

    # ── CONTENT ───────────────────────────────────────────────
    content: Optional[str] = None                  # Processed content (from GenerationResult)
    raw_content: Optional[str] = None              # Initial LLM output (from GenerationResult)
    raw_response: Optional[Any] = None             # Complete response object (from GenerationResult)

    # ── MODEL ─────────────────────────────────────────────────
    model: Optional[str] = None                    # Actual model used (from GenerationResult)

    # ── USAGE & COST (TYPED - IMPROVED!) ──────────────────────
    usage: TokenUsage = field(default_factory=TokenUsage)  # ⭐ Typed! (was Dict in LLMService)
    cost: CostBreakdown = field(default_factory=CostBreakdown)  # ⭐ Separated! (was in usage)

    # ── TIMING ────────────────────────────────────────────────
    elapsed_time: Optional[float] = None           # Total seconds (from GenerationResult)
    total_invoke_duration_ms: Optional[float] = None  # LLM call duration (from GenerationResult)
    total_backoff_ms: Optional[float] = None       # Total backoff time (from GenerationResult)

    @property
    def elapsed_ms(self) -> float:
        """Total elapsed time in milliseconds."""
        if self.elapsed_time:
            return self.elapsed_time * 1000
        return self.total_invoke_duration_ms or 0.0

    # ── RETRY TRACKING ────────────────────────────────────────
    retried: Optional[bool] = None                 # Was retry needed? (from GenerationResult)
    attempt_count: Optional[int] = None            # Number of attempts (from GenerationResult)
    attempts: List[AttemptInfo] = field(default_factory=list)  # ⭐ Detailed attempt tracking

    @property
    def retry_count(self) -> int:
        """Number of retries (attempts - 1)."""
        if self.attempt_count:
            return max(0, self.attempt_count - 1)
        return max(0, len(self.attempts) - 1)

    # ── BACKOFF STATS ─────────────────────────────────────────
    backoff: BackoffStats = field(default_factory=BackoffStats)  # From GenerationResult

    # ── DETAILED TIMESTAMPS (OPTIONAL) ────────────────────────
    timestamps: Optional[EventTimestamps] = None   # From GenerationResult

    # ── TRACKING ──────────────────────────────────────────────
    request_id: Optional[Union[str, int]] = None   # From GenerationResult
    operation_name: Optional[str] = None           # For cost analytics (from GenerationResult)

    # ── ADVANCED ──────────────────────────────────────────────
    response_id: Optional[str] = None              # For CoT chaining (from GenerationResult)
    response_type: Optional[str] = None            # "text" | "json" | "audio" (from GenerationResult)

    # ── ERROR INFO ────────────────────────────────────────────
    error_message: Optional[str] = None            # From GenerationResult

    # ── METADATA ──────────────────────────────────────────────
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ── ORIGINAL REQUEST (OPTIONAL) ───────────────────────────
    generation_request: Optional[Any] = None       # Copy of LLMRequest (from GenerationResult)

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

## LLMHandler (Wrapper with Tracking)

```python
"""
chatforge/llm/handler.py

LLM handler that wraps LangChain with tracking.
Implements retry logic and cost tracking inspired by LLMService.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from tenacity import (
    Retrying, AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential
)

from chatforge.llm.request import LLMRequest, LLMMessage
from chatforge.llm.response import LLMResponse
from chatforge.llm.tracking import (
    TokenUsage, CostBreakdown, AttemptInfo, BackoffStats, EventTimestamps
)
from chatforge.llm.factory import get_llm  # Existing chatforge factory


class LLMHandler:
    """
    LLM handler wrapping LangChain with professional tracking.

    Implements patterns from LLMService:
    - Detailed attempt tracking
    - Cost calculation by model
    - Retry logic with backoff stats
    - Event timestamps

    Usage:
        handler = LLMHandler(default_model="gpt-4o-mini")

        request = LLMRequest(
            messages=[LLMMessage(role="user", content="Hello")],
            operation_name="greeting",
        )

        response = await handler.invoke(request)
    """

    # Model costs (from LLMService)
    MODEL_COSTS = {
        'gpt-4o': {
            'input': 2.5e-6,
            'output': 10e-6,
            'reasoning': 0,
        },
        'gpt-4o-mini': {
            'input': 0.15e-6,
            'output': 0.6e-6,
            'reasoning': 0,
        },
        'claude-3-5-sonnet-20241022': {
            'input': 3.0e-6,
            'output': 15.0e-6,
            'reasoning': 0,
            'cache_write': 3.75e-6,    # Anthropic prompt caching
            'cache_read': 0.3e-6,
        },
        'claude-3-5-haiku-20241022': {
            'input': 0.8e-6,
            'output': 4.0e-6,
            'reasoning': 0,
            'cache_write': 1.0e-6,
            'cache_read': 0.08e-6,
        },
        # Add more models as needed
    }

    def __init__(
        self,
        default_model: str = "gpt-4o-mini",
        default_provider: str = "openai",
        max_retries: int = 2,
        logger: Optional[logging.Logger] = None,
    ):
        self.default_model = default_model
        self.default_provider = default_provider
        self.max_retries = max_retries
        self.logger = logger or logging.getLogger(__name__)

        # Cache LangChain models
        self._model_cache: dict[str, BaseChatModel] = {}

    def _get_langchain_model(self, model: str) -> BaseChatModel:
        """Get or create LangChain model instance."""
        if model not in self._model_cache:
            # Use existing chatforge factory
            self._model_cache[model] = get_llm(
                provider=self.default_provider,
                model_name=model,
                streaming=False,
            )
        return self._model_cache[model]

    def _convert_to_langchain_messages(self, messages: List[LLMMessage]) -> List:
        """Convert LLMMessage to LangChain message format."""
        lc_messages = []

        for msg in messages:
            if msg.role == "system":
                lc_messages.append(SystemMessage(content=msg.content))
            elif msg.role == "user":
                # Handle multimodal (images)
                if msg.images:
                    # LangChain OpenAI format for images
                    content_parts = [{"type": "text", "text": msg.content}]
                    for img_b64 in msg.images:
                        content_parts.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                        })
                    lc_messages.append(HumanMessage(content=content_parts))
                else:
                    lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                lc_messages.append(AIMessage(content=msg.content))

        return lc_messages

    async def invoke(self, request: LLMRequest) -> LLMResponse:
        """
        Execute LLM request with tracking.

        Implements LLMService-style tracking:
        - AttemptInfo for each retry
        - EventTimestamps for timing
        - BackoffStats for retry metrics
        - Typed TokenUsage and CostBreakdown
        """
        trace_id = str(uuid.uuid4())
        request_received_at = datetime.now(timezone.utc)

        # Initialize timestamps
        timestamps = EventTimestamps(request_received_at=request_received_at)

        # Determine model
        model = request.model or self.default_model

        # Get LangChain model
        lc_model = self._get_langchain_model(model)

        # Convert messages
        lc_messages = self._convert_to_langchain_messages(request.messages)

        # Handle structured output (LangChain's with_structured_output)
        if request.response_schema:
            lc_model = lc_model.with_structured_output(request.response_schema)

        # Invoke with retry tracking (from LLMService pattern)
        attempts: List[AttemptInfo] = []
        final_response = None
        final_success = False
        final_error = None

        try:
            async for attempt in AsyncRetrying(
                retry=retry_if_exception_type(Exception),
                stop=stop_after_attempt(request.number_of_retries or self.max_retries),
                wait=wait_random_exponential(min=1, max=60),
                reraise=True
            ):
                with attempt:
                    attempt_num = attempt.retry_state.attempt_number
                    attempt_start = datetime.now(timezone.utc)

                    # Record LLM call start
                    if attempt_num == 1:
                        timestamps.llm_call_started_at = attempt_start

                    try:
                        # ⭐ ACTUAL LANGCHAIN CALL
                        response = await lc_model.ainvoke(lc_messages)
                        final_response = response
                        final_success = True
                    except Exception as e:
                        attempt_end = datetime.now(timezone.utc)
                        duration = (attempt_end - attempt_start).total_seconds() * 1000

                        # Calculate backoff if retry planned
                        backoff_ms = None
                        if attempt.retry_state.next_action:
                            backoff_ms = attempt.retry_state.next_action.sleep * 1000

                        attempts.append(AttemptInfo(
                            attempt_number=attempt_num,
                            started_at=attempt_start,
                            ended_at=attempt_end,
                            error_message=str(e),
                            backoff_ms=backoff_ms,
                        ))

                        self.logger.warning(
                            f"Attempt {attempt_num} failed: {e}. "
                            f"Backoff: {backoff_ms}ms"
                        )
                        raise
                    else:
                        # Success
                        attempt_end = datetime.now(timezone.utc)
                        duration = (attempt_end - attempt_start).total_seconds() * 1000

                        attempts.append(AttemptInfo(
                            attempt_number=attempt_num,
                            started_at=attempt_start,
                            ended_at=attempt_end,
                            error_message=None,
                            backoff_ms=None,
                        ))

                        # Record LLM call end (last successful attempt)
                        timestamps.llm_call_ended_at = attempt_end

        except Exception as e:
            # All retries exhausted
            final_success = False
            final_error = str(e)
            self.logger.error(f"All retries exhausted: {e}")

        # Calculate elapsed time
        response_completed_at = datetime.now(timezone.utc)
        timestamps.response_completed_at = response_completed_at
        elapsed_time = (response_completed_at - request_received_at).total_seconds()

        # Extract content and usage
        content = ""
        usage = TokenUsage()

        if final_success and final_response:
            # Extract content
            if isinstance(final_response, AIMessage):
                content = final_response.content
            else:
                # Structured output (Pydantic model)
                content = str(final_response)

            # Extract usage from response metadata
            usage = self._extract_usage(final_response)

        # Calculate cost
        cost = self._calculate_cost(model, usage)

        # Build backoff stats (from LLMService pattern)
        backoff = BackoffStats(
            retry_loops=len(attempts) - 1 if attempts else 0,
            retry_ms=sum(a.backoff_ms or 0.0 for a in attempts),
        )

        # Timestamps
        timestamps.attempts = attempts

        # Build response (adapted from GenerationResult)
        return LLMResponse(
            success=final_success,
            content=content,
            raw_content=content,  # For compatibility
            raw_response=final_response,
            model=model,
            usage=usage,
            cost=cost,
            elapsed_time=elapsed_time,
            total_invoke_duration_ms=timestamps.total_duration_ms(),
            total_backoff_ms=timestamps.total_backoff_ms(),
            retried=len(attempts) > 1,
            attempt_count=len(attempts),
            attempts=attempts,
            backoff=backoff,
            timestamps=timestamps,
            request_id=request.request_id,
            operation_name=request.operation_name,
            trace_id=trace_id,
            error_message=final_error,
            generation_request=request,  # Copy original request
        )

    def _extract_usage(self, response: Any) -> TokenUsage:
        """Extract token usage from LangChain response."""
        usage = TokenUsage()

        if isinstance(response, AIMessage):
            # LangChain AIMessage has usage_metadata
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                metadata = response.usage_metadata
                usage.input_tokens = metadata.get('input_tokens', 0)
                usage.output_tokens = metadata.get('output_tokens', 0)

                # Anthropic cache tokens
                if 'cache_creation_input_tokens' in metadata:
                    usage.cached_tokens = metadata['cache_creation_input_tokens']

            # Check response_metadata for additional info
            if hasattr(response, 'response_metadata'):
                resp_meta = response.response_metadata

                # OpenAI reasoning tokens (o1 models)
                if 'token_usage' in resp_meta:
                    token_usage = resp_meta['token_usage']
                    if 'reasoning_tokens' in token_usage:
                        usage.reasoning_tokens = token_usage['reasoning_tokens']

        return usage

    def _calculate_cost(self, model: str, usage: TokenUsage) -> CostBreakdown:
        """Calculate cost breakdown (from LLMService pattern)."""
        costs = self.MODEL_COSTS.get(model, {})

        cost = CostBreakdown()

        if costs:
            cost.input_cost = usage.input_tokens * costs.get('input', 0)
            cost.output_cost = usage.output_tokens * costs.get('output', 0)
            cost.reasoning_cost = usage.reasoning_tokens * costs.get('reasoning', 0)

            # Anthropic cache costs
            if 'cache_write' in costs:
                cost.cache_write_cost = usage.cached_tokens * costs['cache_write']
            if 'cache_read' in costs:
                # Cached tokens read are discounted
                cost.cache_read_cost = usage.cached_tokens * costs['cache_read']

        return cost
```

---

## Usage Examples

### Example 1: Simple Chat

```python
from chatforge.llm import LLMHandler, LLMRequest, LLMMessage

handler = LLMHandler(default_model="gpt-4o-mini")

# Simple request (adapted from GenerationRequest)
request = LLMRequest(
    messages=[
        LLMMessage(role="user", content="What is 2+2?"),
    ],
    operation_name="simple_math",  # ⭐ From GenerationRequest
)

response = await handler.invoke(request)

# Response (adapted from GenerationResult)
print(f"Answer: {response.content}")

# ⭐ Typed usage (not Dict!)
print(f"Input tokens: {response.usage.input_tokens}")
print(f"Output tokens: {response.usage.output_tokens}")
print(f"Total tokens: {response.usage.total_tokens}")

# ⭐ Typed cost (not mixed with usage!)
print(f"Input cost: ${response.cost.input_cost:.4f}")
print(f"Output cost: ${response.cost.output_cost:.4f}")
print(f"Total cost: ${response.cost.total_cost:.4f}")

# ⭐ Retry tracking (from GenerationResult)
print(f"Duration: {response.elapsed_ms:.0f}ms")
print(f"Retries: {response.retry_count}")
```

### Example 2: With Model Override

```python
# Use cheaper model for simple task
request = LLMRequest(
    messages=[LLMMessage(role="user", content="Say hello")],
    model="gpt-4o-mini",  # Override default
    operation_name="greeting",
)

response = await handler.invoke(request)

# Use expensive model for complex reasoning
request = LLMRequest(
    messages=[LLMMessage(role="user", content="Solve this complex problem...")],
    model="gpt-4o",  # Override to better model
    operation_name="complex_reasoning",
)

response = await handler.invoke(request)
```

### Example 3: Structured Output

```python
from pydantic import BaseModel, Field

class ExtractedData(BaseModel):
    title: str = Field(description="Article title")
    summary: str = Field(description="Brief summary")
    key_points: List[str] = Field(description="Key points")

request = LLMRequest(
    messages=[
        LLMMessage(
            role="user",
            content="Extract data from this article: ..."
        ),
    ],
    response_schema=ExtractedData,  # ⭐ From GenerationRequest
    operation_name="extraction",
)

response = await handler.invoke(request)

# response.content is JSON string (or Pydantic instance if auto-parsed)
data = ExtractedData.parse_raw(response.content)
print(data.title)
print(data.key_points)
```

### Example 4: Multimodal (Images)

```python
import base64

with open("image.png", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

request = LLMRequest(
    messages=[
        LLMMessage(
            role="user",
            content="What's in this image?",
            images=[img_b64],  # ⭐ From GenerationRequest
        ),
    ],
    model="gpt-4o",  # Vision model
    operation_name="image_analysis",
)

response = await handler.invoke(request)
```

### Example 5: Cost Tracking by Operation

```python
# Track costs by operation type (from GenerationResult pattern)
requests = [
    LLMRequest(messages=[...], operation_name="summarization"),
    LLMRequest(messages=[...], operation_name="extraction"),
    LLMRequest(messages=[...], operation_name="translation"),
]

cost_by_operation = {}

for request in requests:
    response = await handler.invoke(request)

    op_name = response.operation_name
    if op_name not in cost_by_operation:
        cost_by_operation[op_name] = 0.0

    cost_by_operation[op_name] += response.cost.total_cost

print("Cost breakdown:")
for op_name, total_cost in cost_by_operation.items():
    print(f"  {op_name}: ${total_cost:.4f}")
```

### Example 6: Retry Analysis

```python
request = LLMRequest(
    messages=[LLMMessage(role="user", content="Hello")],
    number_of_retries=5,  # ⭐ From GenerationRequest
)

response = await handler.invoke(request)

# Detailed retry tracking (from GenerationResult pattern)
if response.retried:
    print(f"Request required {response.retry_count} retries")

    for attempt in response.attempts:
        print(f"Attempt {attempt.attempt_number}:")
        print(f"  Duration: {attempt.duration_ms:.0f}ms")
        if attempt.error_message:
            print(f"  Error: {attempt.error_message}")
        if attempt.backoff_ms:
            print(f"  Backoff: {attempt.backoff_ms:.0f}ms")

# Backoff stats (from GenerationResult pattern)
print(f"Total backoff: {response.backoff.total_ms:.0f}ms")
print(f"Retry loops: {response.backoff.retry_loops}")
```

### Example 7: CoT Chaining

```python
# First request
request1 = LLMRequest(
    messages=[LLMMessage(role="user", content="What is quantum computing?")],
    model="gpt-5",  # Reasoning model
    reasoning_effort="medium",  # ⭐ From GenerationRequest
    operation_name="cot_step1",
)

response1 = await handler.invoke(request1)
print(f"Step 1 response ID: {response1.response_id}")

# Chain second request (uses reasoning from first)
request2 = LLMRequest(
    messages=[LLMMessage(role="user", content="Now explain quantum entanglement")],
    model="gpt-5",
    previous_response_id=response1.response_id,  # ⭐ CoT chaining
    reasoning_effort="low",  # Lower effort, reuse previous reasoning
    operation_name="cot_step2",
)

response2 = await handler.invoke(request2)
print(f"Step 2 used less reasoning tokens: {response2.usage.reasoning_tokens}")
```

---

## Integration with Existing Chatforge

### Keep Everything, Add Wrapper

**Before (existing code still works):**
```python
from chatforge.llm.factory import get_llm

llm = get_llm(provider="openai", model_name="gpt-4o-mini")
response = llm.invoke([HumanMessage(content="Hello")])
```

**After (new structured approach with LLMService patterns):**
```python
from chatforge.llm import LLMHandler, LLMRequest, LLMMessage

handler = LLMHandler(default_model="gpt-4o-mini")
request = LLMRequest(
    messages=[LLMMessage(role="user", content="Hello")],
    operation_name="greeting",
)
response = await handler.invoke(request)

# Now you get (from GenerationResult pattern):
print(f"Cost: ${response.cost.total_cost}")      # ⭐ Typed CostBreakdown
print(f"Tokens: {response.usage.total_tokens}")   # ⭐ Typed TokenUsage
print(f"Retries: {response.retry_count}")         # ⭐ Retry tracking
print(f"Trace ID: {response.trace_id}")           # ⭐ Tracing
```

---

## File Structure

```
chatforge/llm/
├── __init__.py
├── factory.py                  # Existing get_llm() - KEEP
├── handler.py                  # NEW: LLMHandler wrapper
├── request.py                  # NEW: LLMRequest, LLMMessage (from GenerationRequest)
├── response.py                 # NEW: LLMResponse (from GenerationResult)
├── tracking.py                 # NEW: TokenUsage, CostBreakdown, AttemptInfo, etc.
└── costs.py                    # NEW: MODEL_COSTS dictionary
```

---

## Summary

**Design:** Adapted LLMService's proven dataclasses for chatforge

**What we adapted from LLMService:**
1. ✅ **GenerationRequest** → `LLMRequest`
   - operation_name for cost tracking
   - request_id for tracing
   - response_schema for structured output
   - previous_response_id for CoT chaining
   - reasoning_effort for GPT-5

2. ✅ **GenerationResult** → `LLMResponse`
   - Typed TokenUsage (not Dict)
   - Typed CostBreakdown (separate from usage)
   - AttemptInfo list for retry tracking
   - BackoffStats for retry metrics
   - EventTimestamps for detailed timing

3. ✅ **Supporting classes:**
   - InvocationAttempt → AttemptInfo
   - BackoffStats (simplified)
   - EventTimestamps (simplified)

**What we improved:**
- ✅ Typed usage/cost (not Dict[str, Any])
- ✅ Unified messages (not separate prompts)
- ✅ Removed pipeline-specific fields
- ✅ Kept LangChain compatibility

**Result:**
```python
# Professional tracking with LangChain ecosystem
handler = LLMHandler()
request = LLMRequest(messages=[...], operation_name="summarization")
response = await handler.invoke(request)

# Automatic tracking from LLMService pattern:
# - response.cost.total_cost (typed!)
# - response.usage.total_tokens (typed!)
# - response.attempts (detailed retry info)
# - response.timestamps (full timeline)
```

This is the best of both worlds: **LangChain's ecosystem** + **LLMService's professional tracking**! 🎉
