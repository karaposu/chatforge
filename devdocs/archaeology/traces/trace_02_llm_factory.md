# Trace 02: LLM Factory (get_llm)

The factory pattern for instantiating LLM providers. Abstracts away provider-specific initialization.

---

## Entry Point

**File:** `chatforge/services/llm/factory.py:13`
**Method:** `get_llm()`

**Signature:**
```python
def get_llm(
    provider: str | None = None,
    model_name: str | None = None,
    streaming: bool = False,
    temperature: float | None = None,
) -> BaseChatModel
```

**Variants:**
- `get_streaming_llm()` - Convenience wrapper, always streaming=True
- `get_vision_llm()` - Returns vision-capable model

**Callers:**
- `ReActAgent.__init__()` - When no LLM provided
- Application code directly
- Middleware (SafetyGuardrail, PromptInjectionGuard)

---

## Execution Path

```
get_llm(provider, model_name, streaming, temperature)
    │
    ├─1─► Resolve defaults from llm_config singleton
    │     │
    │     ├── provider = provider or llm_config.provider     # "openai"
    │     ├── model_name = model_name or llm_config.model_name  # "gpt-4o-mini"
    │     └── temperature = temperature ?? llm_config.temperature  # 0.0
    │
    ├─2─► Route to provider-specific factory
    │     │
    │     ├── [openai] ──► _get_openai_llm(model_name, streaming, temperature)
    │     │   │
    │     │   ├── Import langchain_openai.ChatOpenAI (lazy)
    │     │   │   └── ImportError → raise with install instructions
    │     │   │
    │     │   ├── Check llm_config.openai_api_key
    │     │   │   └── None → raise ValueError("OPENAI_API_KEY not configured")
    │     │   │
    │     │   └── Return ChatOpenAI(
    │     │           model=model_name,
    │     │           api_key=llm_config.openai_api_key,
    │     │           streaming=streaming,
    │     │           temperature=temperature,
    │     │           request_timeout=60,
    │     │           max_retries=3,
    │     │       )
    │     │
    │     ├── [anthropic] ──► _get_anthropic_llm(...)
    │     │   │
    │     │   ├── Import langchain_anthropic.ChatAnthropic (lazy)
    │     │   ├── Check llm_config.anthropic_api_key
    │     │   └── Return ChatAnthropic(
    │     │           model=model_name,
    │     │           anthropic_api_key=...,
    │     │           streaming=streaming,
    │     │           temperature=temperature,
    │     │           timeout=60,
    │     │           max_retries=3,
    │     │       )
    │     │
    │     └── [bedrock] ──► _get_bedrock_llm(...)
    │         │
    │         ├── Import langchain_community.chat_models.BedrockChat (lazy)
    │         ├── Check AWS credentials (access_key_id, secret_access_key)
    │         └── Return BedrockChat(
    │                 model_id=model_name,
    │                 streaming=streaming,
    │                 model_kwargs={"temperature": temperature},
    │                 region_name=llm_config.aws_region,
    │             )
    │
    └─3─► Return BaseChatModel instance
```

**get_vision_llm path:**
```
get_vision_llm(provider, model_name, temperature)
    │
    ├── Resolve provider from llm_config.provider
    │
    ├── Model selection priority:
    │   1. Explicit model_name parameter
    │   2. llm_config.vision_model_name (from env LLM_VISION_MODEL_NAME)
    │   3. DEFAULT_VISION_MODELS[provider]
    │       - openai: "gpt-4o"
    │       - anthropic: "claude-3-5-sonnet-latest"
    │       - bedrock: "anthropic.claude-3-sonnet-20240229-v1:0"
    │
    ├── Temperature from llm_config.vision_temperature if not provided
    │
    └── Call get_llm(provider, model_name, streaming=False, temperature)
```

---

## Resource Management

| Resource | Acquisition | Release | Failure Mode |
|----------|-------------|---------|--------------|
| LangChain module | Lazy import on first call | Never (stays loaded) | ImportError if missing |
| LLM instance | Created fresh each call | GC'd when no references | None - stateless |
| API connection | Per-request (inside LangChain) | After each request | Timeout, auth errors |

**Key insight:** No connection pooling or caching. Each `get_llm()` call creates a new instance. LangChain handles connection reuse internally per-request.

---

## Error Path

```
1. ImportError (missing optional dependency)
    │
    └── Raise ImportError with install instructions:
        "langchain-openai is required for OpenAI provider.
         Install with: pip install chatforge[openai]"

2. ValueError (missing credentials)
    │
    └── Raise ValueError with specific message:
        "OpenAI API key not configured. Please set OPENAI_API_KEY"

3. ValueError (unsupported provider)
    │
    └── Raise ValueError:
        "Unsupported LLM provider: X. Supported: openai, anthropic, bedrock"
```

**Note:** Credential validation happens at factory time, not at use time. If API key is set but invalid, error occurs on first `.invoke()` call, not here.

---

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Factory call latency | <1ms | Just instantiation |
| Memory per instance | ~1KB | LLM client is lightweight |
| Import latency | 100-500ms | First call only, LangChain loading |

**No caching:** Each call creates new instance. If calling repeatedly with same params, caller should cache the result.

---

## Observable Effects

| Effect | Location | Trigger |
|--------|----------|---------|
| Module import | sys.modules | First call per provider |
| Environment read | llm_config | At import time of config module |
| No logging | - | Factory is silent |

**Side effects:** None. Pure factory function.

---

## Why This Design

**Lazy imports:**
- Don't load langchain_openai unless using OpenAI
- Reduces startup time if only using one provider
- Allows optional dependencies

**Singleton config:**
- `llm_config` created at module import
- Environment variables read once
- Consistent across all factory calls

**Explicit credentials check:**
- Fail fast with clear message
- Don't wait for first API call to discover missing key

**Hardcoded defaults:**
- `request_timeout=60` - Reasonable for LLM calls
- `max_retries=3` - Handle transient failures
- No configuration exposed for these

---

## What Feels Incomplete

1. **No instance caching:**
   - Same params create new instance each time
   - Caller must manage caching
   - Could have `@lru_cache` or similar

2. **No credential validation:**
   - Only checks if key is set
   - Doesn't verify key is valid
   - Invalid key discovered late

3. **No model validation:**
   - Accepts any model_name string
   - Invalid model discovered at invoke time
   - Could validate against known models

4. **No logging:**
   - Silent factory
   - No visibility into what's being created
   - Debug logging would help

---

## What Feels Vulnerable

1. **Credentials in memory:**
   - API keys loaded into llm_config singleton
   - Stay in memory for process lifetime
   - Could be dumped in crash reports

2. **No key rotation support:**
   - Config read once at import
   - Changing env var has no effect
   - Must restart process to pick up new keys

3. **Provider defaults hardcoded:**
   - `request_timeout=60` may not suit all use cases
   - No way to configure retries
   - Should be configurable via env or params

4. **Bedrock credentials:**
   - AWS credentials checked but not AWS session
   - Could have expired session tokens
   - No IAM role support (only access keys)

---

## What Feels Bad Design

1. **Mixed concerns:**
   - Factory does config resolution AND instantiation
   - Should separate config lookup from creation
   - Makes testing harder

2. **Singleton config global:**
   - `llm_config` is module-level singleton
   - Can't have different configs in same process
   - Makes multi-tenant scenarios hard

3. **No interface for LLM wrapper:**
   - Returns raw LangChain `BaseChatModel`
   - No Chatforge abstraction layer
   - Tightly couples to LangChain internals

4. **Inconsistent timeout params:**
   - OpenAI: `request_timeout`
   - Anthropic: `timeout`
   - Should normalize these

5. **Vision model selection magic:**
   - Three-level priority is confusing
   - Should be explicit parameter or config
   - `DEFAULT_VISION_MODELS` dict is hidden knowledge
