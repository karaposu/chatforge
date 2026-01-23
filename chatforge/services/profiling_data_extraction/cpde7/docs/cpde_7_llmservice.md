# CPDE7LLMService: Reusable LLM Extraction Infrastructure

## Overview

`CPDE7LLMService` is a centralized LLM service that encapsulates all CPDE-7 extraction logic. It follows the [MyLLMService pattern](../../../../devdocs/myllmservice.md) - one class with one method per extraction dimension.

**Key insight:** The CPDE-7 extraction logic is **static**:
- 7 fixed dimensions
- Fixed prompts per dimension
- Fixed output schemas per dimension

This makes it perfect for a reusable service class that lives in chatforge.

---

## Why This Belongs in Chatforge

| Aspect | Why Chatforge |
|--------|---------------|
| **Reusability** | Any app using chatforge can extract profiling data |
| **Static logic** | Prompts and dimensions don't change per-app |
| **Infrastructure** | Like `get_llm()`, it's foundational tooling |
| **Consistency** | Same extraction behavior across all consumers |
| **Maintenance** | Update prompts once, all apps benefit |

**Analogy:** Just like `get_llm()` abstracts LLM providers, `CPDE7LLMService` abstracts profiling extraction.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Application                          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         ProfilingDataExtractionService               │   │
│  │         (Orchestration: storage, runs, batching)     │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         │ uses                               │
└─────────────────────────┼───────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────┐
│                         ▼                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              CPDE7LLMService                          │   │
│  │              (Pure LLM extraction)                    │   │
│  │                                                       │   │
│  │  extract_core_identity()                              │   │
│  │  extract_opinions_views()                             │   │
│  │  extract_preferences_patterns()                       │   │
│  │  extract_desires_needs()                              │   │
│  │  extract_life_narrative()                             │   │
│  │  extract_events()                                     │   │
│  │  extract_entities()                                   │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         │ uses                               │
│  ┌──────────────────────▼───────────────────────────────┐   │
│  │              get_llm() + prompts.py                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│                       CHATFORGE                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Separation of Concerns

| Component | Responsibility |
|-----------|----------------|
| **`CPDE7LLMService`** | Pure extraction: target + context → LLM → structured result |
| **`ProfilingDataExtractionService`** | Orchestration: storage, run tracking, windowing, saves |
| **`prompts.py`** | Static prompt templates |
| **`models.py`** | Pydantic models for LLM output |

**CPDE7LLMService knows nothing about:**
- Storage
- Extraction runs
- Batching strategies
- Message sources

**It only knows:**
- How to format prompts
- How to call LLMs
- How to parse responses

---

## Interface Design

```python
# chatforge/services/profiling_data_extraction/cpde7llmservice.py

class CPDE7LLMService:
    """
    Centralized LLM service for CPDE-7 profiling data extraction.

    Follows the MyLLMService pattern: one method per dimension,
    cached LLM instances, clean interface.

    Example:
        service = CPDE7LLMService()

        result = service.extract_core_identity(
            target_message="I'm a 34-year-old software engineer at Google",
            context_messages="[Previous conversation for reference]",
        )
        # Returns: CoreIdentityResult with extracted identity facts
    """

    def __init__(self, default_model: str = "gpt-4o-mini"):
        self.default_model = default_model
        self._llm_cache = {}

    def _get_llm(self, model: str = None):
        """Get or create cached LLM instance."""
        model = model or self.default_model
        if model not in self._llm_cache:
            self._llm_cache[model] = get_llm(
                provider="openai",
                model_name=model,
                temperature=0.0,
            )
        return self._llm_cache[model]

    # =========================================================================
    # Dimension Extraction Methods
    # =========================================================================

    def extract_core_identity(
        self,
        target_message: str,
        context_messages: str = "",
        model: str = None,
    ) -> CoreIdentityResult:
        """Extract identity facts (who they ARE)."""
        ...

    def extract_opinions_views(
        self,
        target_message: str,
        context_messages: str = "",
        model: str = None,
    ) -> OpinionsViewsResult:
        """Extract non-ephemeral opinions and beliefs."""
        ...

    def extract_preferences_patterns(
        self,
        target_message: str,
        context_messages: str = "",
        model: str = None,
    ) -> PreferencesResult:
        """Extract stable preferences and behavioral patterns."""
        ...

    def extract_desires_needs(
        self,
        target_message: str,
        context_messages: str = "",
        model: str = None,
    ) -> DesiresNeedsResult:
        """Extract wants, needs, wishes, hopes."""
        ...

    def extract_life_narrative(
        self,
        target_message: str,
        context_messages: str = "",
        model: str = None,
    ) -> LifeNarrativeResult:
        """Extract biographical elements and life story."""
        ...

    def extract_events(
        self,
        target_message: str,
        context_messages: str = "",
        model: str = None,
    ) -> EventsResult:
        """Extract significant events and occurrences."""
        ...

    def extract_entities(
        self,
        target_message: str,
        context_messages: str = "",
        model: str = None,
    ) -> EntitiesResult:
        """Extract people, organizations, places, relationships."""
        ...

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    def extract_all(
        self,
        target_message: str,
        context_messages: str = "",
        dimensions: list[str] = None,
        model: str = None,
    ) -> dict[str, Any]:
        """
        Extract all (or specified) dimensions at once.

        Args:
            target_message: The message to extract from
            context_messages: Previous messages for reference
            dimensions: Which dimensions to extract (default: all 7)
            model: LLM model override

        Returns:
            Dict mapping dimension name to extraction result
        """
        ...
```

---

## Usage Patterns

### Pattern 1: Direct Use (Simple)

```python
from chatforge.services.profiling_data_extraction import CPDE7LLMService

service = CPDE7LLMService()

# Extract single dimension
identity = service.extract_core_identity(
    target_message="I'm a software engineer living in Seattle",
    context_messages="",
)

# Extract multiple dimensions
results = service.extract_all(
    target_message="I'm a software engineer. I hate meetings.",
    dimensions=["core_identity", "opinions_views"],
)
```

### Pattern 2: Used by ProfilingDataExtractionService

```python
# Inside ProfilingDataExtractionService

class ProfilingDataExtractionService:
    def __init__(
        self,
        llm_service: CPDE7LLMService | None = None,
        storage: StoragePort | None = None,
    ):
        self.llm_service = llm_service or CPDE7LLMService()
        self.storage = storage

    async def _extract_single_message(
        self,
        target: MessageRecord,
        context: list[MessageRecord],
        config: ExtractionConfig,
    ) -> list[ExtractedProfilingData]:
        """Extract from one message using CPDE7LLMService."""

        # Format messages
        target_str = f"[{target.sender_name}]: {target.content}"
        context_str = self._format_context(context)

        # Call LLM service for each dimension
        results = []
        for dimension in config.dimensions:
            method = getattr(self.llm_service, f"extract_{dimension}")
            extraction = method(
                target_message=target_str,
                context_messages=context_str,
            )
            if extraction.has_content:
                results.append(self._to_extracted_data(extraction, target))

        return results
```

### Pattern 3: Standalone Analysis

```python
# Use without any storage or orchestration
# Good for one-off analysis, debugging, testing

from chatforge.services.profiling_data_extraction import CPDE7LLMService

service = CPDE7LLMService(default_model="gpt-4o")

# Analyze a conversation snippet
conversation = """
User: I've been at Google for 3 years now. The Seattle weather is rough.
User: I really want to move back to Austin but the job is too good.
User: My wife Sarah thinks we should stay another year.
"""

for line in conversation.strip().split("\n"):
    if line.startswith("User:"):
        message = line.replace("User:", "").strip()

        # Extract all dimensions
        results = service.extract_all(target_message=message)

        print(f"Message: {message}")
        for dim, data in results.items():
            if data.has_content:
                print(f"  {dim}: {data.items}")
```

---

## Benefits of This Pattern

### 1. Reusability

```python
# App 1: Full extraction service with storage
service = ProfilingDataExtractionService(
    llm_service=CPDE7LLMService(),
    storage=storage_port,
)

# App 2: Simple analysis without storage
llm = CPDE7LLMService()
identity = llm.extract_core_identity(message)

# App 3: Custom pipeline
llm = CPDE7LLMService(default_model="gpt-4o")
# Build your own orchestration around it
```

### 2. Testability

```python
# Mock the LLM service for testing
from unittest.mock import Mock

mock_llm_service = Mock(spec=CPDE7LLMService)
mock_llm_service.extract_core_identity.return_value = CoreIdentityResult(
    has_identity_content=True,
    items=[{"aspect": "profession", "state_value": "engineer"}]
)

# Inject mock
service = ProfilingDataExtractionService(llm_service=mock_llm_service)
```

### 3. Model Flexibility

```python
# Development: cheap model
dev_service = CPDE7LLMService(default_model="gpt-4o-mini")

# Production: best model
prod_service = CPDE7LLMService(default_model="gpt-4o")

# Per-call override
result = service.extract_core_identity(
    target_message=message,
    model="gpt-4o",  # Override for this call
)
```

### 4. Cached LLM Instances

```python
service = CPDE7LLMService()

# First call: creates gpt-4o-mini instance
service.extract_core_identity(msg1)

# Second call: reuses cached instance
service.extract_opinions_views(msg2)

# Different model: creates new instance
service.extract_events(msg3, model="gpt-4o")
```

---

## File Structure

```
chatforge/services/profiling_data_extraction/
├── __init__.py              # Exports
├── config.py                # ExtractionConfig
├── prompts.py               # Dimension prompts (static)
├── models.py                # Pydantic output models
├── cpde7llmservice.py       # ← LLM extraction service
├── service.py               # Orchestration service
└── docs/
    ├── cpde-7.md            # Framework spec
    ├── cpde_7_llmservice.md # This file
    └── ...
```

---

## Relationship to ProfilingDataExtractionService

```
CPDE7LLMService                    ProfilingDataExtractionService
─────────────────                  ──────────────────────────────
• Pure LLM extraction              • Orchestration layer
• Stateless                        • Stateful (runs, storage)
• Takes strings                    • Takes MessageRecords
• Returns Pydantic models          • Returns ExtractedProfilingData
• No storage knowledge             • Uses StoragePort
• Reusable by anyone               • Uses CPDE7LLMService internally
• One method per dimension         • Handles batching/windowing
```

**ProfilingDataExtractionService is a consumer of CPDE7LLMService**, not a replacement.

---

## Summary

`CPDE7LLMService` provides:

1. **Centralized extraction logic** - All 7 dimensions in one place
2. **Reusable infrastructure** - Any chatforge user can extract profiling data
3. **Clean interface** - One method per dimension, simple inputs/outputs
4. **Testability** - Easy to mock for testing
5. **Flexibility** - Model switching, per-call overrides
6. **Performance** - Cached LLM instances

It follows the proven MyLLMService pattern, making CPDE-7 extraction a first-class citizen of chatforge infrastructure.
