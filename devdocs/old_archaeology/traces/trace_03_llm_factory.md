# Trace 03: LLM Factory

How LLM instances are created and configured for different providers.

---

## Entry Point

**Location:** `services/llm/factory.py:13` - `get_llm()` function

**Trigger:** Any code needing an LLM instance:
- Agent initialization
- Middleware (injection guard, safety guardrail)
- Image analysis
- Direct API usage

**Function Signatures:**
```python
get_llm(provider, model_name, streaming, temperature) → BaseChatModel
get_streaming_llm(provider, model_name, temperature) → BaseChatModel
get_vision_llm(provider, model_name, temperature) → BaseChatModel
```

---

## Execution Path

### Path A: get_llm() - Standard LLM

```
get_llm(provider=None, model_name=None, streaming=False, temperature=None)
├── Resolve provider
│   └── provider = provider or llm_config.provider
├── Resolve model_name
│   └── model_name = model_name or llm_config.model_name
├── Resolve temperature
│   └── temperature = temperature if not None else llm_config.temperature
├── Dispatch to provider-specific factory
│   ├── "openai" → _get_openai_llm()
│   ├── "anthropic" → _get_anthropic_llm()
│   ├── "bedrock" → _get_bedrock_llm()
│   └── other → raise ValueError
└── Return BaseChatModel instance
```

### Path B: OpenAI Provider

```
_get_openai_llm(model_name, streaming, temperature)
├── Import langchain_openai.ChatOpenAI (lazy)
│   └── ImportError → helpful message about pip install
├── Check API key
│   └── if not llm_config.openai_api_key → ValueError
├── Create ChatOpenAI instance
│   ├── model=model_name
│   ├── api_key=llm_config.openai_api_key
│   ├── streaming=streaming
│   ├── temperature=temperature
│   ├── request_timeout=60
│   └── max_retries=3
└── Return ChatOpenAI
```

### Path C: Anthropic Provider

```
_get_anthropic_llm(model_name, streaming, temperature)
├── Import langchain_anthropic.ChatAnthropic (lazy)
│   └── ImportError → helpful message about pip install
├── Check API key
│   └── if not llm_config.anthropic_api_key → ValueError
├── Create ChatAnthropic instance
│   ├── model=model_name
│   ├── anthropic_api_key=llm_config.anthropic_api_key
│   ├── streaming=streaming
│   ├── temperature=temperature
│   ├── timeout=60
│   └── max_retries=3
└── Return ChatAnthropic
```

### Path D: Bedrock Provider

```
_get_bedrock_llm(model_name, streaming, temperature)
├── Import langchain_community.chat_models.BedrockChat (lazy)
│   └── ImportError → helpful message about pip install
├── Check AWS credentials
│   └── if not (aws_access_key_id and aws_secret_access_key) → ValueError
├── Create BedrockChat instance
│   ├── model_id=model_name
│   ├── streaming=streaming
│   ├── model_kwargs={"temperature": temperature}
│   ├── region_name=llm_config.aws_region
│   └── credentials_profile_name=None
└── Return BedrockChat
```

### Path E: Vision LLM

```
get_vision_llm(provider=None, model_name=None, temperature=None)
├── Resolve provider
│   └── provider = provider or llm_config.provider
├── Determine model name (priority order)
│   ├── 1. Explicit model_name parameter
│   ├── 2. llm_config.vision_model_name (from env)
│   └── 3. DEFAULT_VISION_MODELS[provider]
│       ├── "openai" → "gpt-4o"
│       ├── "anthropic" → "claude-3-5-sonnet-latest"
│       └── "bedrock" → "anthropic.claude-3-sonnet-20240229-v1:0"
├── Resolve temperature
│   └── temperature = temperature or llm_config.vision_temperature
├── Call get_llm(provider, model_name, streaming=False, temperature)
└── Return vision-capable LLM
```

---

## Resource Management

### Lazy Imports
- LangChain provider packages imported only when needed
- Reduces startup time and memory for unused providers
- ImportError caught with helpful installation instructions

### API Keys
- Read from environment via `llm_config` (Pydantic settings)
- Never logged or exposed in error messages
- Validated before creating instance

### Instance Creation
- New instance created on every call
- No caching or singleton pattern
- Caller responsible for instance lifecycle

### Retry Configuration
- All providers: `max_retries=3`
- All providers: `timeout=60` seconds
- Built into LangChain client wrappers

---

## Error Path

### Missing Provider Package
```python
try:
    from langchain_openai import ChatOpenAI
except ImportError as e:
    raise ImportError(
        "langchain-openai is required for OpenAI provider. "
        "Install with: pip install chatforge[openai]"
    ) from e
```

### Missing API Key
```python
if not llm_config.openai_api_key:
    raise ValueError(
        "OpenAI API key not configured. "
        "Please set OPENAI_API_KEY environment variable."
    )
```

### Unsupported Provider
```python
raise ValueError(
    f"Unsupported LLM provider: {provider}. "
    f"Supported: openai, anthropic, bedrock"
)
```

### LLM Invocation Errors (downstream)
- Rate limiting → Retried up to max_retries
- Timeout → TimeoutError after 60s
- API errors → Provider-specific exceptions propagate

---

## Performance Characteristics

### Initialization Time
| Provider | Import Time | Instance Creation |
|----------|-------------|-------------------|
| OpenAI | ~100ms (first) | ~10ms |
| Anthropic | ~100ms (first) | ~10ms |
| Bedrock | ~200ms (first, boto3) | ~50ms |

### Call Latency
| Operation | Latency Range |
|-----------|---------------|
| Simple completion | 500ms - 3s |
| Complex reasoning | 2s - 30s |
| Streaming first token | 200ms - 500ms |
| Vision analysis | 2s - 10s |

### Memory
- Each LLM instance: ~50KB base
- LangChain overhead: ~10MB (shared)
- Boto3 (Bedrock): ~20MB additional

---

## Observable Effects

### On Success
- LLM instance returned, ready for invocation
- No side effects (pure factory)
- No logging on successful creation

### On Failure
- Exception raised immediately
- Clear error message with fix instructions
- No partial state created

---

## Why This Design

### Factory Pattern
**Choice:** Functions create instances, not classes

**Rationale:**
- Simple API: `get_llm()` vs `LLMFactory().create()`
- Configuration centralized in factory
- Consistent interface regardless of provider

**Trade-off:**
- No instance reuse
- Configuration resolution on every call

### Lazy Imports
**Choice:** Import provider packages inside functions

**Rationale:**
- Don't require all providers installed
- Faster startup for unused providers
- Clear error when package missing

**Trade-off:**
- Import overhead on first call
- Not visible in static analysis

### Hardcoded Timeouts/Retries
**Choice:** 60 second timeout, 3 retries baked in

**Rationale:**
- Reasonable defaults for most use cases
- Consistent behavior across providers
- Simplifies configuration

**Trade-off:**
- Cannot tune per-operation
- May not suit all use cases (quick checks vs long analyses)

### Separate Vision LLM Function
**Choice:** `get_vision_llm()` as distinct entry point

**Rationale:**
- Vision requires specific models
- Different default models per provider
- Separate temperature setting

**Trade-off:**
- Duplication with `get_llm()`
- Could be a parameter instead

---

## What Feels Incomplete

1. **No instance caching**
   - Every call creates new instance
   - Wasteful for repeated use
   - Could cache by (provider, model, streaming, temperature) tuple

2. **No connection pooling**
   - Each LLM instance has independent HTTP client
   - High-volume usage creates many connections
   - LangChain may handle this internally

3. **No token counting**
   - Factory doesn't expose token limits
   - Caller must know model capabilities
   - Could return (llm, max_tokens) tuple

4. **No fallback support**
   - If primary provider fails, no automatic fallback
   - Must implement manually in calling code
   - Could have `get_llm_with_fallback([providers])`

---

## What Feels Vulnerable

1. **API keys in memory**
   - Keys stored in llm_config singleton
   - Accessible via `llm_config.openai_api_key`
   - Could leak in crash dumps or introspection

2. **No rate limit awareness**
   - Factory doesn't track request counts
   - Caller can exhaust API quota
   - No backpressure or queuing

3. **Timeout may be too long**
   - 60 seconds blocks calling thread/coroutine
   - For real-time apps, may want lower timeout
   - No way to interrupt stuck calls

4. **Bedrock credential exposure**
   - AWS keys in environment variables
   - Better to use IAM roles in AWS
   - Code allows direct key injection

---

## What Feels Like Bad Design

1. **Mutable global config**
   ```python
   from chatforge.config import llm_config
   # llm_config is a singleton, any code can change it
   ```
   - Settings are global mutable state
   - Thread safety unclear
   - Testing requires careful reset

2. **Inconsistent parameter names**
   ```python
   # OpenAI
   ChatOpenAI(api_key=...)

   # Anthropic
   ChatAnthropic(anthropic_api_key=...)
   ```
   - Different LangChain patterns leak through
   - Factory hides this but it's still there

3. **No validation of model names**
   ```python
   model_name = model_name or llm_config.model_name
   # Any string accepted, fails later at API call
   ```
   - Invalid model names only caught at runtime
   - Could validate against known models
   - Wastes time debugging typos

4. **supports_vision is incomplete**
   ```python
   def supports_vision(provider: str | None = None) -> bool:
       provider = provider or llm_config.provider
       return provider in DEFAULT_VISION_MODELS
   ```
   - Checks provider, not model
   - "gpt-3.5-turbo" with "openai" returns True but model lacks vision
   - Should check model name too

5. **Streaming parameter not exposed in get_vision_llm**
   ```python
   def get_vision_llm(...) -> BaseChatModel:
       return get_llm(provider, model_name, streaming=False, temperature)
   ```
   - Hardcoded streaming=False
   - Vision analysis could benefit from streaming
   - Inconsistent with get_llm flexibility
