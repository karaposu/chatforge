# Ultra-Think Analysis: LLMService Patterns for Chatforge LLMPort
## Comprehensive Design Pattern Extraction and Adaptation Strategy

**Date:** 2025-12-25
**Objective:** Analyze LLMService architecture to extract proven design patterns for chatforge's LLMPort implementation

---

## Problem Analysis

### Current Chatforge State

**What exists:**
- ✅ `get_llm()` factory returning LangChain's `BaseChatModel`
- ✅ Basic provider selection (OpenAI, Anthropic, Bedrock)
- ✅ Storage ports (well-designed)
- ✅ Messaging/Tracing ports

**What's missing:**
- ❌ **No LLMPort abstraction** - Tightly coupled to LangChain
- ❌ **No structured request/response** - Uses raw LangChain messages
- ❌ **No RPM/TPM rate limiting** - No client-side rate control
- ❌ **No cost tracking** - Can't track spend per operation
- ❌ **No detailed attempt tracking** - Can't debug retries
- ❌ **No multimodal support structure** - Images/audio handled ad-hoc
- ❌ **No structured output support** - No Pydantic schema integration
- ❌ **No CoT chaining** - Can't chain reasoning across calls

**Core Problem:**
Chatforge depends on external library interfaces instead of defining its own contracts. This makes it hard to:
1. Track costs and rate limits
2. Mock for testing
3. Add new providers
4. Support advanced features (structured output, CoT)

---

## LLMService Architecture Analysis

### 1. Request/Response Dataclasses

#### GenerationRequest (schemas.py:277-327)

```python
@dataclass
class GenerationRequest:
    # ── RUNTIME & PLUMBING ────────────────────────────────────
    model: Optional[str] = None                    # ⭐ Model override
    operation_name: Optional[str] = None           # ⭐ Track operation type
    request_id: Optional[Union[str,int]] = None    # ⭐ Unique request ID
    number_of_retries: Optional[int] = None        # ⭐ Retry config

    # ── RESULT HANDLING ───────────────────────────────────────
    output_type: Literal["json", "str"] = "str"
    fail_fallback_value: Optional[str] = None

    # ── CHAT/MULTIMODAL FIELDS ────────────────────────────────
    system_prompt: Optional[str] = None            # System message
    user_prompt: Optional[str] = None              # User message
    assistant_text: Optional[str] = None           # Seed assistant
    input_audio_b64: Optional[str] = None          # Base64 WAV
    images: Optional[List[str]] = None             # List of base64 PNG/JPG
    tool_call: Optional[Dict[str, any]] = None     # Tool/function stub

    # ── OUTPUT FORMAT ─────────────────────────────────────────
    output_data_format: Literal["text", "audio", "both"] = "text"
    audio_output_config: Optional[Dict[str, any]] = None

    # ── ADVANCED FEATURES ─────────────────────────────────────
    previous_response_id: Optional[str] = None     # ⭐ CoT chaining
    reasoning_effort: Optional[Literal["low", "medium", "high"]] = None  # ⭐ GPT-5
    verbosity: Optional[Literal["low", "medium", "high"]] = None

    # ── STRUCTURED OUTPUT ─────────────────────────────────────
    response_schema: Optional[Type[PydanticModel]] = None  # ⭐ Pydantic schema
    strict_mode: bool = True                       # ⭐ Strict validation
    parse_response: bool = True                    # ⭐ Auto-parse
```

**Key Features:**
- ✅ Comprehensive multimodal support (text + images + audio)
- ✅ Model override per-request
- ✅ Operation tracking for analytics
- ✅ Structured output with Pydantic schemas
- ✅ CoT chaining support
- ✅ Validation in `__post_init__`

#### GenerationResult (schemas.py:452-581)

```python
@dataclass
class GenerationResult:
    # ── CORE RESPONSE ─────────────────────────────────────────
    success: bool
    trace_id: str                                  # ⭐ UUID for tracing
    content: Optional[Any] = None                  # Processed content
    raw_content: Optional[str] = None              # Initial LLM output
    raw_response: Optional[Any] = None             # Complete raw response
    model: Optional[str] = None                    # Model used

    # ── RETRY/TIMING ──────────────────────────────────────────
    retried: Optional[bool] = None                 # ⭐ Was retry needed?
    attempt_count: Optional[int] = None            # ⭐ Number of attempts
    total_invoke_duration_ms: Optional[float] = None  # ⭐ Invoke time
    total_backoff_ms: Optional[float] = None       # ⭐ Backoff time
    elapsed_time: Optional[float] = None           # Total seconds

    # ── USAGE & COSTS ─────────────────────────────────────────
    usage: Dict[str, Any] = field(default_factory=dict)  # ⭐ Tokens + costs

    # ── RPM/TPM TRACKING ──────────────────────────────────────
    rpm_at_the_beginning: Optional[int] = None     # ⭐ RPM before request
    rpm_at_the_end: Optional[int] = None           # ⭐ RPM after request
    rpm_waited: Optional[bool] = None              # ⭐ Did we wait for RPM?
    rpm_wait_loops: Optional[int] = None           # ⭐ RPM wait loops
    rpm_waited_ms: Optional[int] = None            # ⭐ RPM wait time

    tpm_at_the_beginning: Optional[int] = None     # ⭐ TPM before request
    tpm_at_the_end: Optional[int] = None           # ⭐ TPM after request
    tpm_waited: Optional[bool] = None              # ⭐ Did we wait for TPM?
    tpm_wait_loops: Optional[int] = None           # ⭐ TPM wait loops
    tpm_waited_ms: Optional[int] = None            # ⭐ TPM wait time

    # ── DETAILED TRACKING ─────────────────────────────────────
    backoff: BackoffStats = field(default_factory=BackoffStats)
    timestamps: Optional[EventTimestamps] = None   # ⭐ Full timeline

    # ── SPECIAL FEATURES ──────────────────────────────────────
    response_id: Optional[str] = None              # ⭐ For CoT chaining
    generation_request: Optional[GenerationRequest] = None  # ⭐ Copy of request

    # ── HELPER METHODS ────────────────────────────────────────
    def get_audio_data(self) -> Optional[bytes]   # ⭐ Extract audio
    def get_audio_transcript(self) -> Optional[str]
    def save_audio(self, filepath: str) -> bool
```

**Key Features:**
- ✅ Detailed retry tracking (attempts, backoff, duration)
- ✅ RPM/TPM wait metrics (essential for debugging rate limits)
- ✅ Usage tracking with costs
- ✅ Full timeline via EventTimestamps
- ✅ Helper methods for multimodal data
- ✅ Pretty-print via `__str__`

#### BackoffStats (schemas.py:41-61)

```python
@dataclass(slots=True)
class BackoffStats:
    # ── CLIENT-SIDE GATES ──────────────────────────────────────
    rpm_loops: int = 0                             # ⭐ RPM wait loops
    rpm_ms: int = 0                                # ⭐ RPM wait time
    tpm_loops: int = 0                             # ⭐ TPM wait loops
    tpm_ms: int = 0                                # ⭐ TPM wait time

    # ── SERVER/RETRY LAYER ─────────────────────────────────────
    retry_loops: int = 0                           # ⭐ Retry attempts
    retry_ms: int = 0                              # ⭐ Retry backoff time

    # ── CONVENIENCE HELPERS ────────────────────────────────────
    @property
    def client_ms(self) -> int:
        return self.rpm_ms + self.tpm_ms

    @property
    def total_ms(self) -> int:
        return self.client_ms + self.retry_ms
```

**Key Insight:** Separates client-side rate limiting (RPM/TPM) from server-side retries (429 errors).

#### EventTimestamps (schemas.py:125-236)

```python
@dataclass
class EventTimestamps:
    generation_requested_at: Optional[datetime] = None
    generation_enqueued_at: Optional[datetime] = None
    generation_dequeued_at: Optional[datetime] = None

    # ... many processing stage timestamps ...

    attempts: List[InvocationAttempt] = field(default_factory=list)

    def total_duration_ms(self) -> float
    def invoke_durations_ms(self) -> List[float]
    def total_backoff_ms(self) -> float
    def postprocessing_duration_ms(self) -> float
    def to_dict(self) -> Dict[str, Any]           # ⭐ Serialization
```

**Key Insight:** Comprehensive timeline tracking for performance debugging.

#### InvocationAttempt (schemas.py:64-79)

```python
@dataclass
class InvocationAttempt:
    attempt_number: int
    invoke_start_at: datetime
    invoke_end_at: datetime
    backoff_after_ms: Optional[int] = None         # ⭐ Backoff duration
    error_message: Optional[str] = None            # ⭐ Error details

    def duration_ms(self) -> float
    def backoff_ms(self) -> float
```

**Key Insight:** Per-attempt granular tracking for debugging retry behavior.

---

### 2. Provider Abstraction Pattern

#### BaseLLMProvider (providers/base.py:13-148)

```python
class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    @classmethod
    @abstractmethod
    def supports_model(cls, model_name: str) -> bool:
        """Check if this provider supports the given model."""
        pass

    @abstractmethod
    def convert_request(self, request: LLMCallRequest) -> Any:
        """Convert LLMCallRequest to provider-specific payload."""
        pass

    @abstractmethod
    def _invoke_impl(self, payload: Any) -> Tuple[Any, bool, Optional[ErrorType]]:
        """Core synchronous invoke logic."""
        # Returns: (response, success_flag, error_type)
        pass

    @abstractmethod
    async def _invoke_async_impl(self, payload: Any) -> Tuple[Any, bool, Optional[ErrorType]]:
        """Core asynchronous invoke logic."""
        pass

    @abstractmethod
    def extract_usage(self, response: Any) -> Dict[str, Any]:
        """Extract usage metadata from response."""
        # Must return: input_tokens, output_tokens, total_tokens
        pass

    @abstractmethod
    def calculate_cost(self, model: str, usage: Dict[str, Any]) -> Dict[str, float]:
        """Calculate costs based on usage."""
        # Returns: input_cost, output_cost, reasoning_cost, total_cost
        pass
```

**Key Features:**
- ✅ Clear separation of concerns
- ✅ Sync + async support
- ✅ Error type enumeration
- ✅ Usage extraction abstracted
- ✅ Cost calculation per provider

#### ResponsesAPIProvider Implementation (providers/new_openai_provider.py:17-444)

**Model Costs (lines 21-91):**
```python
class ResponsesAPIProvider(BaseLLMProvider):
    MODEL_COSTS = {
        'gpt-4o': {
            'input_token_cost': 2.5e-6,
            'output_token_cost': 10e-6,
            'reasoning_token_cost': 0
        },
        'gpt-5': {
            'input_token_cost': 30e-6,
            'output_token_cost': 60e-6,
            'reasoning_token_cost': 45e-6          # ⭐ Separate reasoning cost
        },
        # ... more models
    }
```

**Request Conversion (lines 131-195):**
```python
def convert_request(self, request: LLMCallRequest) -> Dict[str, Any]:
    """Convert to Responses API format."""
    input_content = self._build_input(request)

    payload = {
        "model": request.model_name or self.model_name,
        "input": input_content,
    }

    # Add instructions (system prompt)
    if request.system_prompt:
        payload["instructions"] = request.system_prompt

    # Add reasoning control for GPT-5
    if self.is_reasoning_model:
        payload["reasoning"] = {"effort": request.reasoning_effort or "medium"}

    # Add previous_response_id for CoT chaining
    if request.previous_response_id:
        payload["previous_response_id"] = request.previous_response_id

    # Handle structured output with Pydantic schema
    if request.response_schema:
        payload["text"] = {
            "format": self._build_json_schema(request.response_schema, request.strict_mode)
        }

    return payload
```

**Multimodal Input Building (lines 197-247):**
```python
def _build_input(self, request: LLMCallRequest) -> Any:
    """Build input - string or messages array."""

    # Simple text
    if request.user_prompt and not (request.images or request.input_audio_b64):
        return request.user_prompt  # Simple string

    # Multimodal
    messages = []
    content = []

    if request.user_prompt:
        content.append({"type": "input_text", "text": request.user_prompt})

    if request.images:
        for img_b64 in request.images:
            content.append({
                "type": "input_image",
                "image": {"data": img_b64}
            })

    if request.input_audio_b64:
        content.append({
            "type": "input_audio",
            "audio": {"data": request.input_audio_b64, "format": "wav"}
        })

    messages.append({"role": "user", "content": content})
    return messages
```

**Structured Output (lines 284-340):**
```python
def _build_json_schema(self, schema_model: Type, strict: bool = True) -> Dict:
    """Convert Pydantic model to JSON Schema."""
    from pydantic import BaseModel

    if not issubclass(schema_model, BaseModel):
        raise ValueError("response_schema must be Pydantic BaseModel")

    schema = schema_model.model_json_schema(mode='serialization')

    if strict:
        schema['additionalProperties'] = False
        self._set_additional_properties_false(schema)  # Recursive

    return {
        "type": "json_schema",
        "name": schema_model.__name__.lower(),
        "schema": schema,
        "strict": strict
    }
```

**Usage Extraction (lines 383-421):**
```python
def extract_usage(self, response: Any) -> Dict[str, Any]:
    """Extract usage from Responses API response."""
    usage = {}

    if hasattr(response, 'usage'):
        usage['input_tokens'] = getattr(response.usage, 'input_tokens', 0)
        usage['output_tokens'] = getattr(response.usage, 'output_tokens', 0)
        usage['reasoning_tokens'] = getattr(response.usage, 'reasoning_tokens', 0)
        usage['total_tokens'] = (
            usage['input_tokens'] +
            usage['output_tokens'] +
            usage['reasoning_tokens']
        )

    # Store response_id for CoT chaining
    if hasattr(response, 'id'):
        usage['response_id'] = response.id

    return usage
```

**Cost Calculation (lines 423-444):**
```python
def calculate_cost(self, model: str, usage: Dict[str, Any]) -> Dict[str, float]:
    """Calculate costs including reasoning tokens."""
    costs = self.MODEL_COSTS.get(model, {
        'input_token_cost': 0,
        'output_token_cost': 0,
        'reasoning_token_cost': 0
    })

    input_cost = usage.get('input_tokens', 0) * costs['input_token_cost']
    output_cost = usage.get('output_tokens', 0) * costs['output_token_cost']
    reasoning_cost = usage.get('reasoning_tokens', 0) * costs.get('reasoning_token_cost', 0)

    return {
        'input_cost': input_cost,
        'output_cost': output_cost,
        'reasoning_cost': reasoning_cost,
        'total_cost': input_cost + output_cost + reasoning_cost
    }
```

---

### 3. Retry Logic with Detailed Tracking

#### LLMHandler (llm_handler.py:66-142)

```python
def process_call_request(self, request: LLMCallRequest) -> InvokeResponseData:
    """Main entry point with retry logic."""
    payload = self.provider.convert_request(request)

    attempts = []
    final_response = None
    final_success = False
    final_error_type = None

    try:
        for attempt in Retrying(
            retry=retry_if_exception_type((httpx.HTTPStatusError, RateLimitError)),
            stop=stop_after_attempt(self.max_retries),
            wait=wait_random_exponential(min=1, max=60),
            reraise=True
        ):
            with attempt:
                n = attempt.retry_state.attempt_number
                start = _now_dt()

                try:
                    resp, success, error_type = self.provider._invoke_impl(payload)
                    final_response = resp
                    final_success = success
                    final_error_type = error_type
                except Exception as e:
                    end = _now_dt()
                    backoff = None
                    if attempt.retry_state.next_action:
                        backoff = timedelta(seconds=attempt.retry_state.next_action.sleep)

                    attempts.append(InvocationAttempt(
                        attempt_number=n,
                        invoke_start_at=start,
                        invoke_end_at=end,
                        backoff_after_ms=backoff,
                        error_message=str(e)
                    ))
                    raise
                else:
                    end = _now_dt()
                    attempts.append(InvocationAttempt(
                        attempt_number=n,
                        invoke_start_at=start,
                        invoke_end_at=end,
                        backoff_after_ms=None,
                        error_message=None
                    ))

        usage = self._build_usage_metadata(final_response, final_success)

        return InvokeResponseData(
            success=final_success,
            response=final_response,
            attempts=attempts,
            usage=usage,
            error_type=final_error_type
        )
    except Exception as final_exc:
        # All retries exhausted
        usage = self._init_empty_usage()
        return InvokeResponseData(
            success=False,
            response=None,
            attempts=attempts,
            usage=usage,
            error_type=final_error_type
        )
```

**Key Features:**
- ✅ Uses tenacity for retry logic
- ✅ Tracks each attempt with timestamps
- ✅ Records backoff duration
- ✅ Captures error messages per attempt
- ✅ Returns comprehensive InvokeResponseData

---

### 4. Generation Engine Pattern

#### GenerationEngine (generation_engine.py:22-410)

**Flow:**
1. `generate_output(GenerationRequest) -> GenerationResult`
2. Records `generation_requested_at`
3. Converts GenerationRequest → LLMCallRequest
4. Calls `llm_handler.process_call_request()`
5. Builds GenerationResult with timestamps
6. Records `generation_completed_at`
7. Calculates elapsed_time

**Key Methods:**
```python
async def generate_output_async(self, generation_request: GenerationRequest) -> GenerationResult:
    generation_requested_at = _now_dt()

    llm_call_request = self._convert_to_llm_call_request(generation_request)

    generation_result = await self._execute_llm_call_async(
        llm_call_request,
        generation_request.request_id,
        generation_request.operation_name
    )

    generation_result.generation_request = generation_request

    if generation_result.timestamps is None:
        generation_result.timestamps = EventTimestamps()
    generation_result.timestamps.generation_requested_at = generation_requested_at

    generation_result.content = generation_result.raw_content

    generation_completed_at = _now_dt()
    generation_result.timestamps.generation_completed_at = generation_completed_at
    generation_result.elapsed_time = (generation_completed_at - generation_requested_at).total_seconds()

    return generation_result
```

**Structured Output Support (lines 278-386):**
```python
def process_with_schema(self, content: str, schema: Type, instructions: str = None, **kwargs) -> Any:
    """Process with guaranteed structured output using Pydantic schema."""
    from pydantic import BaseModel

    if not issubclass(schema, BaseModel):
        raise ValueError("Schema must be Pydantic BaseModel")

    request = GenerationRequest(
        user_prompt=content,
        system_prompt=instructions or f"Extract data according to {schema.__name__} schema",
        response_schema=schema,
        reasoning_effort=kwargs.get('reasoning_effort', 'low'),
        model=kwargs.get('model'),
        **{k: v for k, v in kwargs.items() if k not in ['reasoning_effort', 'model']}
    )

    result = self.generate_output(request)

    if result.success and result.response_type == "json":
        data = json.loads(result.content) if isinstance(result.content, str) else result.content
        return schema(**data)  # Return Pydantic instance
    else:
        raise ValueError(f"Generation failed: {result.error_message}")
```

---

## Solution Options: Adapting Patterns to Chatforge

### Option 1: Full LLMService Clone (High Fidelity)

**Description:** Directly port LLMService's dataclasses and architecture to chatforge.

**Structure:**
```
chatforge/
├── ports/
│   └── llm.py                          # LLMPort interface
├── adapters/
│   └── llm/
│       ├── base.py                     # BaseLLMProvider
│       ├── openai_adapter.py           # OpenAI implementation
│       ├── anthropic_adapter.py        # Anthropic implementation
│       └── langchain_adapter.py        # Wrapper for existing LangChain
├── schemas/
│   ├── llm_request.py                  # LLMRequest (like GenerationRequest)
│   ├── llm_response.py                 # LLMResponse (like GenerationResult)
│   ├── backoff_stats.py                # BackoffStats
│   ├── timestamps.py                   # EventTimestamps
│   └── invocation_attempt.py           # InvocationAttempt
└── llm/
    ├── handler.py                      # LLMHandler (retry logic)
    └── factory.py                      # get_llm_port()
```

**Pros:**
- ✅ Proven architecture (battle-tested in LLMService)
- ✅ Comprehensive tracking (RPM/TPM, costs, retries)
- ✅ Easy to port (copy-paste with modifications)

**Cons:**
- ❌ Heavy - lots of dataclasses
- ❌ May be overkill for simple use cases
- ❌ Tight coupling to LLMService patterns

**Implementation Complexity:** High (2-3 weeks)

---

### Option 2: Simplified LLMPort (Minimal Viable)

**Description:** Extract only essential patterns, simplify dataclasses.

**Structure:**
```python
# chatforge/ports/llm.py

@dataclass
class LLMRequest:
    """Simplified request."""
    messages: List[LLMMessage]                # Required
    model: Optional[str] = None               # Override model
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    response_schema: Optional[Type] = None    # Structured output
    metadata: Dict[str, Any] = field(default_factory=dict)  # operation_name, etc.

@dataclass
class LLMResponse:
    """Simplified response."""
    content: str
    model: str
    usage: TokenUsage                         # input_tokens, output_tokens, total_tokens
    cost: float                               # Total cost in USD
    success: bool
    attempts: int                             # Retry count
    elapsed_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)  # response_id, etc.

class LLMPort(ABC):
    @abstractmethod
    async def invoke(self, request: LLMRequest) -> LLMResponse:
        pass

    @abstractmethod
    def supports_model(self, model: str) -> bool:
        pass
```

**Pros:**
- ✅ Simple to understand and use
- ✅ Quick to implement (1 week)
- ✅ Covers 80% of use cases

**Cons:**
- ❌ Less detailed tracking
- ❌ No RPM/TPM built-in
- ❌ Missing some advanced features

**Implementation Complexity:** Low (1 week)

---

### Option 3: Hybrid Approach (Recommended)

**Description:** Core patterns from LLMService, but simplified and optional detailed tracking.

**Structure:**
```python
# chatforge/ports/llm/request.py

@dataclass
class LLMRequest:
    # ── CORE (Required) ───────────────────────────────────────
    messages: List[LLMMessage]                     # Multimodal messages

    # ── OVERRIDES (Optional) ──────────────────────────────────
    model: Optional[str] = None                    # Override default model
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

    # ── ADVANCED (Optional) ───────────────────────────────────
    response_schema: Optional[Type] = None         # Pydantic schema
    previous_response_id: Optional[str] = None     # CoT chaining

    # ── TRACKING (Optional) ───────────────────────────────────
    request_id: Optional[str] = None               # For tracing
    operation_name: Optional[str] = None           # For analytics
    metadata: Dict[str, Any] = field(default_factory=dict)

# chatforge/ports/llm/response.py

@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0                      # For GPT-5/o-series
    total_tokens: int = 0

@dataclass
class CostBreakdown:
    input_cost: float = 0.0
    output_cost: float = 0.0
    reasoning_cost: float = 0.0
    total_cost: float = 0.0

@dataclass
class AttemptInfo:
    """Optional detailed attempt tracking."""
    attempt_number: int
    duration_ms: float
    error: Optional[str] = None

@dataclass
class LLMResponse:
    # ── CORE (Always Present) ─────────────────────────────────
    content: str                                   # Response text
    model: str                                     # Model used
    success: bool                                  # Success flag

    # ── USAGE & COST ──────────────────────────────────────────
    usage: TokenUsage
    cost: CostBreakdown

    # ── TIMING ────────────────────────────────────────────────
    elapsed_ms: float                              # Total duration

    # ── RETRY INFO (Optional) ─────────────────────────────────
    attempts: List[AttemptInfo] = field(default_factory=list)

    # ── ADVANCED (Optional) ───────────────────────────────────
    response_id: Optional[str] = None              # For CoT chaining
    raw_response: Optional[Any] = None             # For audio/multimodal

    # ── TRACKING (Optional) ───────────────────────────────────
    request_id: Optional[str] = None
    operation_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

# chatforge/ports/llm/port.py

class LLMPort(ABC):
    """LLM port interface."""

    @abstractmethod
    async def invoke(self, request: LLMRequest) -> LLMResponse:
        """Execute LLM call asynchronously."""
        pass

    @abstractmethod
    def invoke_sync(self, request: LLMRequest) -> LLMResponse:
        """Execute LLM call synchronously."""
        pass

    @abstractmethod
    def supports_model(self, model: str) -> bool:
        """Check if model is supported."""
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """List available models."""
        pass

# chatforge/adapters/llm/base.py

class BaseLLMAdapter(LLMPort):
    """Base class for LLM adapters."""

    MODEL_COSTS = {}  # Override in subclass

    @abstractmethod
    def _convert_request(self, request: LLMRequest) -> Any:
        """Convert to provider-specific format."""
        pass

    @abstractmethod
    async def _invoke_impl(self, payload: Any) -> Tuple[Any, bool]:
        """Provider-specific invoke."""
        pass

    def _extract_usage(self, response: Any) -> TokenUsage:
        """Extract usage from response."""
        pass

    def _calculate_cost(self, model: str, usage: TokenUsage) -> CostBreakdown:
        """Calculate cost."""
        costs = self.MODEL_COSTS.get(model, {})
        return CostBreakdown(
            input_cost=usage.input_tokens * costs.get('input', 0),
            output_cost=usage.output_tokens * costs.get('output', 0),
            reasoning_cost=usage.reasoning_tokens * costs.get('reasoning', 0),
            total_cost=...
        )
```

**Pros:**
- ✅ Best of both worlds (simple + detailed when needed)
- ✅ Structured output support
- ✅ CoT chaining support
- ✅ Cost tracking built-in
- ✅ Optional detailed tracking (attempts, backoff)

**Cons:**
- ⚠️ Medium complexity
- ⚠️ Need to decide what's optional vs required

**Implementation Complexity:** Medium (1.5-2 weeks)

---

## Recommendation: Hybrid Approach

### Rationale

1. **Proven Patterns:** LLMService's architecture is battle-tested
2. **Flexibility:** Optional detailed tracking for debugging without forcing complexity
3. **Future-Proof:** Supports advanced features (CoT, structured output)
4. **Cost-Aware:** Built-in cost tracking (critical for production)

### Implementation Roadmap

#### Phase 1: Core Infrastructure (Week 1)

**Day 1-2: Dataclasses**
- `LLMMessage` with multimodal content
- `LLMRequest` dataclass
- `LLMResponse` with `TokenUsage` and `CostBreakdown`
- `AttemptInfo` for retry tracking

**Day 3-4: LLMPort Interface**
- Define `LLMPort` ABC
- `invoke()` and `invoke_sync()` methods
- `supports_model()`, `get_available_models()`

**Day 5: BaseLLMAdapter**
- Base class with common logic
- `_convert_request()` abstract
- `_extract_usage()` and `_calculate_cost()` helpers

#### Phase 2: Provider Implementations (Week 2)

**Day 6-7: OpenAILLMAdapter**
- Implement `_convert_request()` for OpenAI Chat Completions
- Multimodal support (images via data URIs)
- Structured output via `response_format`
- Cost calculation

**Day 8-9: AnthropicLLMAdapter**
- Implement for Anthropic Messages API
- Multimodal support (images via base64)
- Prompt caching support
- Cost calculation with cached tokens

**Day 10: LangChainLLMAdapter**
- Wrapper for existing LangChain models (backward compatibility)
- Extract usage from AIMessage metadata

#### Phase 3: Advanced Features (Days 11-14)

**Day 11: Structured Output**
- Pydantic schema conversion
- Strict mode support
- Auto-parsing

**Day 12: CoT Chaining**
- `previous_response_id` support
- `response_id` extraction
- Chain state management

**Day 13: Retry Logic with Tracking**
- tenacity integration
- `AttemptInfo` population
- Backoff tracking

**Day 14: Testing & Documentation**
- Unit tests for all adapters
- Contract tests (like StoragePort)
- Usage examples
- Migration guide from old `get_llm()`

---

## Key Decisions

### 1. RPM/TPM Rate Limiting

**Question:** Should chatforge implement client-side RPM/TPM limiting?

**LLMService Approach:**
- Tracks RPM/TPM in `GenerationResult`
- Client-side gating (wait before call if limit reached)
- Exposed via `rpm_waited`, `tpm_waited` fields

**Recommendation for Chatforge:**
- **Phase 1:** Don't implement (rely on server-side rate limiting)
- **Phase 2:** Add optional `RateLimiter` class (can be injected into adapter)
- **Rationale:** Most users don't need it, adds complexity

**If implementing later:**
```python
class RateLimiter:
    def __init__(self, rpm: int, tpm: int):
        self.rpm_limit = rpm
        self.tpm_limit = tpm
        self.rpm_window = []
        self.tpm_window = []

    async def acquire(self, estimated_tokens: int) -> Dict[str, int]:
        """Wait if needed, return wait_ms."""
        # Implementation here
        return {"rpm_waited_ms": 0, "tpm_waited_ms": 0}

# Usage in adapter
class OpenAILLMAdapter(BaseLLMAdapter):
    def __init__(self, rate_limiter: Optional[RateLimiter] = None):
        self.rate_limiter = rate_limiter

    async def invoke(self, request: LLMRequest) -> LLMResponse:
        if self.rate_limiter:
            wait_stats = await self.rate_limiter.acquire(estimated_tokens=1000)
        # ... rest of invoke
```

### 2. LangChain vs Direct SDK

**Question:** Should we support both LangChain and direct SDK providers?

**LLMService Approach:**
- Uses direct SDKs (OpenAI SDK, not langchain_openai)
- Full control over request/response format

**Recommendation for Chatforge:**
- **Primary:** Direct SDK adapters (OpenAILLMAdapter using `openai` SDK)
- **Secondary:** LangChainLLMAdapter for backward compatibility
- **Rationale:** Direct SDKs give more control, lower abstraction overhead

**File Structure:**
```
chatforge/adapters/llm/
├── base.py                    # BaseLLMAdapter
├── openai_adapter.py          # Uses openai SDK
├── anthropic_adapter.py       # Uses anthropic SDK
├── bedrock_adapter.py         # Uses boto3
└── langchain_adapter.py       # Wrapper for LangChain models (legacy)
```

### 3. Multimodal Content Structure

**Question:** Use separate `ImageContent`/`AudioContent` or unified `ContentPart`?

**LLMService Approach:**
- Simple: `images: List[str]` (base64) and `input_audio_b64: str`
- Provider converts to API-specific format

**Previous Chatforge Proposal:**
- Dataclasses: `TextContent`, `ImageContent`, `AudioContent`

**Recommendation:**
- **Use LLMService approach** (simpler)
- Conversion happens in adapter's `_convert_request()`

**Reasoning:**
```python
# LLMService style (simpler)
LLMRequest(
    messages=[
        LLMMessage(
            role="user",
            content="What's in this image?",
            images=["base64data1", "base64data2"]
        )
    ]
)

# vs. Dataclass style (more verbose)
LLMRequest(
    messages=[
        LLMMessage(
            role="user",
            content=[
                TextContent(text="What's in this image?"),
                ImageContent(type="image_base64", data="base64data1"),
                ImageContent(type="image_base64", data="base64data2"),
            ]
        )
    ]
)
```

**Decision:** Use LLMService style for simplicity. Adapter handles conversion.

### 4. Async-First or Sync-First?

**Question:** Should LLMPort be async-first or support both equally?

**LLMService Approach:**
- Both sync and async
- Separate `_invoke_impl()` and `_invoke_async_impl()`

**Recommendation:**
- **Async-first:** Primary interface is `async def invoke()`
- **Sync wrapper:** `def invoke_sync()` uses `asyncio.run()`
- **Rationale:** Modern Python is async, easier to wrap async → sync than reverse

```python
class LLMPort(ABC):
    @abstractmethod
    async def invoke(self, request: LLMRequest) -> LLMResponse:
        """Primary async interface."""
        pass

    def invoke_sync(self, request: LLMRequest) -> LLMResponse:
        """Sync wrapper."""
        return asyncio.run(self.invoke(request))
```

---

## Alternative Perspectives

### Contrarian View: Keep it Simple

**Argument:** LLMService is over-engineered for chatforge's needs. Just add model/temperature overrides to existing `get_llm()`.

**Counter:**
1. Cost tracking is essential for production
2. Structured output is becoming standard
3. Retry tracking crucial for debugging
4. Future features (CoT, multimodal) need structure

**Compromise:** Start with Option 2 (Simplified), add details later if needed.

### Future Considerations

1. **Streaming Support:** LLMService doesn't show streaming. Chatforge needs it.
   - Solution: Add `async def stream(request: LLMRequest) -> AsyncIterator[str]`

2. **Tool Use:** ReActAgent handles tools, but should LLMPort support function calling?
   - Solution: Add `tools: Optional[List[Tool]]` to LLMRequest
   - Response includes `tool_calls: Optional[List[ToolCall]]`

3. **Prompt Caching:** Anthropic's prompt caching saves costs
   - Solution: Add `cache_control: Optional[Dict]` to LLMMessage

4. **Model Capabilities:** How to query what a model supports?
   - Solution: `adapter.get_model_info(model_name) -> ModelInfo`

---

## Success Metrics

1. **Backward Compatibility:** Existing chatforge code works with minimal changes
2. **Cost Visibility:** All LLM calls report costs
3. **Testability:** Can mock LLMPort easily
4. **Provider Flexibility:** Can add new provider in <1 day
5. **Performance:** No more than 10% overhead vs direct SDK calls

---

## Areas for Further Research

1. **RPM/TPM Implementation:** Study LLMService's actual rate limiter code
2. **Streaming with Retries:** How to handle retry logic for streams?
3. **Batch Requests:** Should LLMPort support batch?
4. **Cost Budgets:** Should there be budget enforcement at port level?

---

## Conclusion

The **Hybrid Approach (Option 3)** provides the best balance:
- Adopts proven patterns from LLMService
- Keeps interface simple for common cases
- Provides detailed tracking when needed
- Supports advanced features (CoT, structured output, multimodal)

**Next Steps:**
1. Review and approve this analysis
2. Create detailed design doc for Phase 1
3. Implement core dataclasses (LLMRequest, LLMResponse)
4. Implement LLMPort interface
5. Create OpenAILLMAdapter as reference implementation
