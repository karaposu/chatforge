# Trace 12: Configuration Loading

Pydantic-based settings loaded from environment variables. Singleton pattern for global config.

---

## Entry Point

**File:** `chatforge/config/llm.py`, `agent.py`, `storage.py`, `guardrails.py`
**Classes:** `LLMSettings`, `AgentSettings`, `StorageSettings`, `GuardrailsSettings`

**Access pattern:**
```python
from chatforge.config import llm_config, agent_config, storage_config, guardrails_config
```

**Callers:**
- `get_llm()` - reads llm_config
- `ReActAgent` - reads agent_config
- Storage adapters - read storage_config
- Middleware - reads guardrails_config

---

## Execution Path: Module Import

```
import chatforge.config
    │
    ├─► chatforge/config/__init__.py
    │   │
    │   ├── from .llm import LLMSettings, llm_config
    │   ├── from .agent import AgentSettings, agent_config
    │   ├── from .storage import StorageSettings, storage_config
    │   └── from .guardrails import GuardrailsSettings, guardrails_config
    │
    └─► Each module executes at import:
        │
        └── llm_config = LLMSettings()  # Module-level singleton

            [Inside LLMSettings() / Pydantic BaseSettings]
            │
            ├─1─► Read model_config (SettingsConfigDict)
            │     ├── env_prefix="LLM_"
            │     ├── env_file=".env"
            │     └── extra="ignore"
            │
            ├─2─► Load .env file (if exists)
            │     └── python-dotenv parses key=value pairs
            │
            ├─3─► For each field, resolve value:
            │     │
            │     └── Resolution order:
            │         1. Environment variable (LLM_PROVIDER)
            │         2. .env file value
            │         3. Field default value
            │
            ├─4─► Apply field aliases
            │     │
            │     └── validation_alias="OPENAI_API_KEY"
            │         └── Reads OPENAI_API_KEY (no prefix)
            │
            ├─5─► Run validators
            │     │
            │     └── @field_validator("provider")
            │         def validate_provider(v):
            │             if v not in ["openai", "anthropic", "bedrock"]:
            │                 raise ValueError
            │             return v.lower()
            │
            └─6─► Return configured Settings instance
```

---

## LLMSettings Fields

```python
class LLMSettings(BaseSettings):
    # Read from LLM_PROVIDER or default
    provider: str = "openai"

    # Read from LLM_MODEL_NAME or default
    model_name: str = "gpt-4o-mini"

    # Read from LLM_VISION_MODEL_NAME or None
    vision_model_name: str | None = None

    # Read from LLM_TEMPERATURE or default
    temperature: float = 0.0

    # Read from LLM_VISION_TEMPERATURE or default
    vision_temperature: float = 0.0

    # Read from OPENAI_API_KEY (no prefix - validation_alias)
    openai_api_key: str | None = None

    # Read from ANTHROPIC_API_KEY
    anthropic_api_key: str | None = None

    # Read from AWS_ACCESS_KEY_ID
    aws_access_key_id: str | None = None

    # Read from AWS_SECRET_ACCESS_KEY
    aws_secret_access_key: str | None = None

    # Read from AWS_REGION or default
    aws_region: str = "us-east-1"
```

---

## AgentSettings Fields

```python
class AgentSettings(BaseSettings):
    # env_prefix="AGENT_"

    # Read from AGENT_SYSTEM_PROMPT
    system_prompt: str = "You are a helpful assistant..."

    # Read from AGENT_MAX_TURNS
    max_turns: int = 10

    # Read from AGENT_TIMEOUT_SECONDS
    timeout_seconds: int = 120

    # ... other agent settings
```

---

## StorageSettings Fields

```python
class StorageSettings(BaseSettings):
    # env_prefix="STORAGE_"

    # Read from STORAGE_BACKEND
    backend: str = "sqlite"

    # Read from STORAGE_DATABASE_PATH
    database_path: str = "./chatforge.db"

    # Read from STORAGE_TTL_MINUTES
    ttl_minutes: int = 1440  # 24 hours

    # ... other storage settings
```

---

## Resource Management

| Resource | Acquisition | Release | Failure Mode |
|----------|-------------|---------|--------------|
| Environment read | Once at import | Never | Stale if env changes |
| .env file read | Once at import | File handle closed | FileNotFoundError (silent) |
| Singleton instance | Module-level | Never | Memory |

**Key point:** Config is frozen after import. Environment changes have no effect.

---

## Error Path

```
Import time errors:
    │
    ├── ValidationError (Pydantic)
    │   ├── Invalid field value
    │   ├── Type conversion failed
    │   └── Custom validator raised
    │   │
    │   └── Raises on import - application won't start
    │
    └── .env file errors
        └── File not found → silently ignored
        └── Parse error → silently ignored (usually)

Runtime validation:
    │
    └── llm_config.validate_credentials()
        │
        └── Explicit call to check provider-specific credentials
            └── Raises ValueError if missing
```

---

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Import time | 10-50ms | .env parsing, validation |
| Access time | <1μs | Just attribute access |
| Memory | ~1KB per settings class | Field storage |

**Negligible overhead.** Config access is instant after first import.

---

## Observable Effects

| Effect | Location | Trigger |
|--------|----------|---------|
| .env file read | Filesystem | First import |
| Environment read | OS | First import |
| ValidationError | Import | Invalid config |

**No logging.** Silent configuration loading.

---

## Why This Design

**Pydantic BaseSettings:**
- Type validation built-in
- Environment variable mapping
- .env file support
- Documentation via Field()

**Module-level singletons:**
- One source of truth
- No repeated parsing
- Consistent across application

**env_prefix per module:**
- LLM_, AGENT_, STORAGE_
- Namespace separation
- Clear ownership

**validation_alias for API keys:**
- Standard env var names (OPENAI_API_KEY)
- No custom prefix for compatibility
- Other tools use same vars

---

## What Feels Incomplete

1. **No config reloading:**
   - Singleton fixed at import
   - No way to refresh
   - Must restart for changes

2. **No config file support (besides .env):**
   - Only environment variables
   - No YAML/JSON config
   - No per-environment files

3. **No validation of API key format:**
   - Only checks if set
   - Invalid format discovered later
   - Could validate pattern

4. **No secrets management integration:**
   - Plain text in .env or env vars
   - No Vault, AWS Secrets Manager
   - Not production-ready secrets handling

5. **No computed defaults:**
   - vision_model_name defaults to None
   - Then factory picks default
   - Should be consistent

---

## What Feels Vulnerable

1. **API keys in environment:**
   - Visible in process listing
   - Logged by some systems
   - Should use secure storage

2. **No encryption at rest:**
   - .env file is plaintext
   - Anyone with file access sees keys

3. **Singleton allows global mutation:**
   - `llm_config.provider = "new"` works
   - Could corrupt shared state
   - Should be frozen/immutable

4. **ValidationError crashes import:**
   - No graceful degradation
   - Partial config not possible
   - All-or-nothing

5. **No audit trail:**
   - Where did value come from?
   - Env var or .env file or default?
   - Debugging config issues hard

---

## What Feels Bad Design

1. **Settings vs config naming:**
   - Class: `LLMSettings`
   - Singleton: `llm_config`
   - Inconsistent naming

2. **validate_credentials() is manual:**
   - Must call explicitly
   - Easy to forget
   - Should validate on access or import

3. **Extra fields ignored:**
   - `extra="ignore"` in model_config
   - Typos silently dropped
   - LLM_PROVIDR won't error

4. **No default factory for nested config:**
   - Can't have computed nested defaults
   - Everything is flat
   - Complex config awkward

5. **env_file hardcoded to ".env":**
   - Can't specify alternate file
   - No environment-specific files
   - Should be configurable
