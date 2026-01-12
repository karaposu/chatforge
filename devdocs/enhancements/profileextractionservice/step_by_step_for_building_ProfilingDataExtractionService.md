# Step-by-Step Guide: Building ProfilingDataExtractionService

## Executive Summary

This document provides a comprehensive implementation guide for `ProfilingDataExtractionService`, analyzed for compatibility with the existing Chatforge architecture.

**Service Purpose:** Extract profiling data (CPF-7 dimensions) from user conversations using LLM-based semantic understanding.

**Key Design Decisions:**
- Follow `ImageAnalyzer` pattern (best async service pattern in codebase)
- Use LangChain `BaseChatModel` via `get_llm()` factory
- **Pydantic structured output** for guaranteed schema compliance (no JSON parsing risk)
- Storage-optional design (works without persistence)
- Format-agnostic `data` field (schema doesn't depend on CPF-7 structure)

---

## Prerequisites Checklist

| Component | Location | Status |
|-----------|----------|--------|
| `ProfilingDataExtractionRun` dataclass | `ports/storage_types.py` | DONE |
| `ExtractedProfilingData` dataclass | `ports/storage_types.py` | DONE |
| StoragePort extension methods (6) | `ports/storage.py` | DONE |
| SQLAlchemy models | `adapters/storage/models/models.py` | DONE |
| SQLAlchemy adapter methods | `adapters/storage/sqlalchemy.py` | DONE |
| `ExtractionConfig` | `services/profiling_data_extraction/config.py` | DONE |
| CPF-7 Prompts | `services/profiling_data_extraction/prompts.py` | DEFERRED (depends on CPF-7 spec) |
| **ProfilingDataExtractionService** | `services/profiling_data_extraction/service.py` | TODO |

---

## Compatibility Analysis

### 1. LLM Integration

**Factory Function:**
```python
from chatforge.services.llm import get_llm

llm = get_llm(
    provider="openai",        # or "anthropic", "bedrock"
    model_name="gpt-4o-mini", # cost-effective for extraction
    streaming=False,          # structured output requires non-streaming
    temperature=0.0,          # deterministic extraction
)
```

**Compatibility Concerns:**

| Concern | Risk | Mitigation |
|---------|------|------------|
| Provider differences | Low | Pydantic structured output works across providers |
| Token limits | High | Batch messages, track token counts |
| Rate limiting | Medium | Retry with backoff (already in factory) |
| Cost control | High | Track model_used, log token usage |

**Recommendation:** Use `gpt-4o-mini` or `claude-3-haiku` for extraction - good quality at low cost.

### 2. Structured Output (Pydantic)

**Why Pydantic:**
- LLMs return structured data directly as Pydantic models
- No JSON parsing, no format inconsistencies
- Schema validation built-in
- Works with OpenAI, Anthropic, and other providers via LangChain

**Pattern:**
```python
from pydantic import BaseModel, Field
from langchain_core.language_models import BaseChatModel

class ExtractedFact(BaseModel):
    """A single extracted fact from conversation."""
    dimension: str = Field(description="CPF-7 dimension")
    fact_type: str = Field(description="Type of fact (e.g., profession, preference)")
    value: str = Field(description="The extracted information")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")
    source_quote: str = Field(description="Exact quote from conversation")

class ExtractionResponse(BaseModel):
    """LLM extraction response."""
    facts: list[ExtractedFact] = Field(default_factory=list)

# Use with_structured_output for guaranteed schema
structured_llm = llm.with_structured_output(ExtractionResponse)
response: ExtractionResponse = await structured_llm.ainvoke(messages)
# response.facts is already a list of ExtractedFact objects
```

**Benefits:**
- No JSON parsing code needed
- Type-safe extraction
- Validation errors caught automatically
- Empty response = empty list (no special handling)

### 3. Storage Integration

**Pattern:** Storage is optional (dependency injection with None fallback)

```python
def __init__(
    self,
    storage: StoragePort | None = None,
    ...
):
    self.storage = storage  # Can be None
```

**Compatibility Concerns:**

| Concern | Risk | Mitigation |
|---------|------|------------|
| Adapter doesn't implement extended methods | Medium | Check method exists, graceful fallback |
| Transaction failures mid-batch | Medium | Use extraction run status tracking |
| ID type differences (int vs str) | Low | Already handled in dataclasses |

**Recommendation:** Always check `if self.storage:` before storage operations.

### 4. Message Format

**From StoragePort:**
```python
messages: list[MessageRecord]  # Has .content, .role, .sender_name, .id
```

**To LLM (LangChain format):**
```python
from langchain_core.messages import SystemMessage, HumanMessage

llm_messages = [
    SystemMessage(content=system_prompt),
    HumanMessage(content=formatted_conversation),
]
```

**Compatibility Concerns:**

| Concern | Risk | Mitigation |
|---------|------|------------|
| Missing sender_name | Low | Fallback to role |
| Empty content | Low | Filter out empty messages |
| Very long messages | Medium | Truncate or split |
| Special characters | Low | LLM handles well |

---

## Implementation Steps

### Step 1: Create Pydantic Models

**File:** `chatforge/services/profiling_data_extraction/models.py`

```python
"""
Pydantic models for structured LLM output.

These models define the schema for LLM extraction responses.
Used with LangChain's with_structured_output() for guaranteed schema compliance.
"""

from pydantic import BaseModel, Field


class ExtractedFact(BaseModel):
    """A single piece of extracted profiling data."""

    dimension: str = Field(
        description="CPF-7 dimension: core_identity, opinions_views, "
        "preferences_patterns, desires_needs, life_narrative, events, "
        "entities_relationships"
    )
    fact_type: str = Field(
        description="Specific type within dimension (e.g., 'profession', "
        "'preference', 'belief', 'goal')"
    )
    value: str = Field(
        description="The extracted information as a concise statement"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score: 1.0 = explicit statement, "
        "0.5 = somewhat implied, <0.5 = uncertain"
    )
    source_quote: str = Field(
        description="Exact quote from the conversation that supports this fact"
    )


class ExtractionResponse(BaseModel):
    """Complete extraction response from LLM."""

    facts: list[ExtractedFact] = Field(
        default_factory=list,
        description="List of extracted facts. Empty if nothing found."
    )
```

**Note:** The schema here is a placeholder. The actual fields will be defined when CPF-7 spec is complete. The service code doesn't depend on specific fields - it just passes the Pydantic model to `with_structured_output()`.

### Step 2: Create Service Class

**File:** `chatforge/services/profiling_data_extraction/service.py`

```python
"""
Profiling Data Extraction Service.

Extracts profiling data from conversations using LLM-based semantic understanding.
Uses Pydantic structured output for guaranteed schema compliance.
"""

import logging
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from chatforge.ports.storage import StoragePort
from chatforge.ports.storage_types import (
    ExtractedProfilingData,
    MessageRecord,
    ProfilingDataExtractionRun,
)
from chatforge.services.llm import get_llm
from chatforge.services.profiling_data_extraction.config import ExtractionConfig
from chatforge.services.profiling_data_extraction.models import (
    ExtractedFact,
    ExtractionResponse,
)

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# Placeholder prompt - will be replaced when CPF-7 is complete
DEFAULT_SYSTEM_PROMPT = """Extract profiling information that the user reveals about themselves.
Only extract explicit statements, not inferences.
Include exact source quotes for traceability."""


class ProfilingDataExtractionService:
    """
    Service for extracting profiling data from user conversations.

    Uses LLM with Pydantic structured output to extract structured
    profiling data (CPF-7 dimensions) from conversations.

    Example:
        service = ProfilingDataExtractionService(
            storage=storage_port,
        )

        results, run = await service.extract_for_user(
            user_id="user-123",
            config=ExtractionConfig(dimensions=["core_identity"]),
        )
    """

    def __init__(
        self,
        llm: BaseChatModel | None = None,
        storage: StoragePort | None = None,
        system_prompt: str | None = None,
        response_model: type = ExtractionResponse,
    ):
        """
        Initialize the extraction service.

        Args:
            llm: LangChain chat model. If None, uses get_llm() with defaults.
            storage: StoragePort for persistence. Optional.
            system_prompt: Custom system prompt. Uses default if None.
            response_model: Pydantic model for structured output.
        """
        base_llm = llm or get_llm(temperature=0.0, streaming=False)
        self.structured_llm = base_llm.with_structured_output(response_model)
        self.storage = storage
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self._model_name = getattr(base_llm, "model_name", "unknown")

        logger.info(
            f"ProfilingDataExtractionService initialized "
            f"(model={self._model_name}, storage={'yes' if storage else 'no'})"
        )

    # =========================================================================
    # Public API
    # =========================================================================

    async def extract_for_user(
        self,
        user_id: str,
        chat_id: int | str | None = None,
        config: ExtractionConfig | None = None,
        since_message_id: int | str | None = None,
    ) -> tuple[list[ExtractedProfilingData], ProfilingDataExtractionRun]:
        """
        Extract profiling data for a user.

        Args:
            user_id: User to extract for.
            chat_id: Specific chat to extract from. None = all user's chats.
            config: Extraction configuration. Uses defaults if None.
            since_message_id: For incremental extraction - only process newer messages.

        Returns:
            Tuple of (extracted_data_list, extraction_run_record)

        Raises:
            ValueError: If no storage configured and can't fetch messages.
        """
        config = config or ExtractionConfig()

        # Create extraction run
        run = ProfilingDataExtractionRun(
            user_id=user_id,
            chat_id=chat_id,
            status="running",
            config=asdict(config),
            model_used=self._model_name,
            started_at=_utc_now(),
        )

        if self.storage:
            run = await self.storage.create_extraction_run(run)

        try:
            # Get messages
            messages = await self._get_messages(
                user_id=user_id,
                chat_id=chat_id,
                since_message_id=since_message_id,
                limit=config.batch_size * 10,
            )

            if len(messages) < config.min_messages_for_extraction:
                logger.info(
                    f"Skipping extraction: {len(messages)} messages "
                    f"< min {config.min_messages_for_extraction}"
                )
                run.status = "completed"
                run.message_count = len(messages)
                run.completed_at = _utc_now()
                if self.storage:
                    await self.storage.update_extraction_run(run.id, {
                        "status": "completed",
                        "message_count": len(messages),
                        "completed_at": run.completed_at,
                    })
                return [], run

            # Extract in batches
            results = await self._extract_batches(
                messages=messages,
                config=config,
                run=run,
            )

            # Update run as completed
            run.status = "completed"
            run.message_count = len(messages)
            run.message_id_range = {
                "first": messages[0].id if messages else None,
                "last": messages[-1].id if messages else None,
            }
            run.completed_at = _utc_now()
            run.duration_ms = int(
                (run.completed_at - run.started_at).total_seconds() * 1000
            )

            if self.storage:
                await self.storage.update_extraction_run(run.id, {
                    "status": run.status,
                    "message_count": run.message_count,
                    "message_id_range": run.message_id_range,
                    "completed_at": run.completed_at,
                    "duration_ms": run.duration_ms,
                })
                if results:
                    await self.storage.save_extracted_profiling_data(results)

            logger.info(
                f"Extraction completed: {len(results)} facts from "
                f"{len(messages)} messages in {run.duration_ms}ms"
            )

            return results, run

        except Exception as e:
            logger.error(f"Extraction failed: {e}", exc_info=True)
            run.status = "failed"
            run.error = str(e)
            run.completed_at = _utc_now()

            if self.storage and run.id:
                await self.storage.update_extraction_run(run.id, {
                    "status": "failed",
                    "error": str(e),
                    "completed_at": run.completed_at,
                })

            raise

    async def extract_from_messages(
        self,
        messages: list[MessageRecord],
        user_id: str,
        config: ExtractionConfig | None = None,
    ) -> list[ExtractedProfilingData]:
        """
        Extract profiling data from provided messages.

        Use this when you already have messages and don't need
        storage integration.

        Args:
            messages: Messages to extract from.
            user_id: User ID for the extracted data.
            config: Extraction configuration.

        Returns:
            List of extracted profiling data.
        """
        config = config or ExtractionConfig()

        if len(messages) < config.min_messages_for_extraction:
            return []

        # Create a dummy run for tracking (not persisted)
        run = ProfilingDataExtractionRun(
            user_id=user_id,
            status="running",
            config=asdict(config),
            model_used=self._model_name,
            started_at=_utc_now(),
        )

        return await self._extract_batches(messages, config, run)

    # =========================================================================
    # Internal Methods
    # =========================================================================

    async def _get_messages(
        self,
        user_id: str,
        chat_id: int | str | None,
        since_message_id: int | str | None,
        limit: int,
    ) -> list[MessageRecord]:
        """Get messages for extraction."""
        if not self.storage:
            raise ValueError(
                "Cannot fetch messages without storage. "
                "Use extract_from_messages() instead."
            )

        return await self.storage.get_messages_for_extraction(
            user_id=user_id,
            chat_id=chat_id,
            since_message_id=since_message_id,
            limit=limit,
        )

    async def _extract_batches(
        self,
        messages: list[MessageRecord],
        config: ExtractionConfig,
        run: ProfilingDataExtractionRun,
    ) -> list[ExtractedProfilingData]:
        """Extract from messages in batches."""
        results: list[ExtractedProfilingData] = []

        for batch in self._batch_messages(messages, config.batch_size):
            batch_results = await self._extract_single_batch(
                batch=batch,
                config=config,
                run=run,
            )
            results.extend(batch_results)

        return results

    async def _extract_single_batch(
        self,
        batch: list[MessageRecord],
        config: ExtractionConfig,
        run: ProfilingDataExtractionRun,
    ) -> list[ExtractedProfilingData]:
        """Extract profiling data from a single batch of messages."""
        # Format conversation
        conversation = self._format_conversation(batch)

        # Build LLM messages
        llm_messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"Extract profiling data:\n\n{conversation}"),
        ]

        # Call LLM with structured output
        try:
            response: ExtractionResponse = await self.structured_llm.ainvoke(
                llm_messages
            )
        except Exception as e:
            logger.warning(f"LLM call failed for batch: {e}")
            return []

        # Convert to ExtractedProfilingData
        results = []
        for fact in response.facts:
            # Filter by confidence threshold
            if fact.confidence < config.confidence_threshold:
                continue

            # Filter by requested dimensions
            if fact.dimension not in config.dimensions:
                continue

            results.append(ExtractedProfilingData(
                extraction_run_id=run.id,
                user_id=run.user_id,
                chat_id=run.chat_id,
                source_message_ids=[m.id for m in batch],
                source_quotes=[fact.source_quote],
                data=fact.model_dump(),  # Pydantic model to dict
            ))

        return results

    def _format_conversation(self, messages: list[MessageRecord]) -> str:
        """Format messages for LLM consumption."""
        lines = []
        for msg in messages:
            sender = msg.sender_name or msg.role or "Unknown"
            content = msg.content or ""
            if content.strip():
                lines.append(f"[{sender}]: {content}")
        return "\n\n".join(lines)

    def _batch_messages(
        self,
        messages: list[MessageRecord],
        batch_size: int,
    ):
        """Yield batches of messages."""
        for i in range(0, len(messages), batch_size):
            yield messages[i:i + batch_size]
```

### Step 3: Update Package Exports

**File:** `chatforge/services/profiling_data_extraction/__init__.py`

```python
"""
Profiling Data Extraction Service.

Extracts profiling data from conversations using LLM-based semantic understanding.
Implements CPF-7 (Conversational Profiling Framework - 7 Dimensions).

Note: This service extracts raw profiling data, not aggregated profiles.
Profiling (aggregation) is a separate future step.

Usage:
    from chatforge.services.profiling_data_extraction import (
        ExtractionConfig,
        ProfilingDataExtractionService,
    )

    service = ProfilingDataExtractionService(
        storage=storage_port,
    )

    results, run = await service.extract_for_user(
        user_id="user-123",
        config=ExtractionConfig(dimensions=["core_identity"]),
    )
"""

from chatforge.services.profiling_data_extraction.config import (
    CPF7_DIMENSIONS,
    ExtractionConfig,
)
from chatforge.services.profiling_data_extraction.models import (
    ExtractedFact,
    ExtractionResponse,
)
from chatforge.services.profiling_data_extraction.service import (
    ProfilingDataExtractionService,
)

__all__ = [
    # Config
    "CPF7_DIMENSIONS",
    "ExtractionConfig",
    # Pydantic models
    "ExtractedFact",
    "ExtractionResponse",
    # Service
    "ProfilingDataExtractionService",
]
```

### Step 4: Create Tests

**File:** `tests/unit/profiling_data_extraction/test_service.py`

```python
"""Tests for ProfilingDataExtractionService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from chatforge.ports.storage_types import MessageRecord
from chatforge.services.profiling_data_extraction import (
    ExtractionConfig,
    ExtractionResponse,
    ExtractedFact,
    ProfilingDataExtractionService,
)


class TestProfilingDataExtractionService:
    """Tests for the extraction service."""

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM with structured output."""
        llm = MagicMock()
        llm.model_name = "test-model"
        # Mock with_structured_output to return a mock structured LLM
        structured_llm = MagicMock()
        structured_llm.ainvoke = AsyncMock()
        llm.with_structured_output = MagicMock(return_value=structured_llm)
        return llm

    @pytest.fixture
    def mock_storage(self):
        """Create a mock storage port."""
        storage = MagicMock()
        storage.create_extraction_run = AsyncMock()
        storage.update_extraction_run = AsyncMock()
        storage.save_extracted_profiling_data = AsyncMock()
        storage.get_messages_for_extraction = AsyncMock()
        return storage

    @pytest.fixture
    def sample_messages(self) -> list[MessageRecord]:
        """Sample messages for testing."""
        return [
            MessageRecord(
                id=1,
                chat_id=100,
                role="user",
                sender_name="Alice",
                content="I'm a software engineer working at Google.",
            ),
            MessageRecord(
                id=2,
                chat_id=100,
                role="assistant",
                sender_name="Bot",
                content="That's interesting!",
            ),
            MessageRecord(
                id=3,
                chat_id=100,
                role="user",
                sender_name="Alice",
                content="I really prefer Python over Java.",
            ),
        ]

    def test_init_with_defaults(self):
        """Service initializes with defaults."""
        with patch(
            "chatforge.services.profiling_data_extraction.service.get_llm"
        ) as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.with_structured_output = MagicMock(return_value=MagicMock())
            mock_get_llm.return_value = mock_llm

            service = ProfilingDataExtractionService()
            assert service.storage is None
            mock_get_llm.assert_called_once()

    def test_init_with_injected_dependencies(self, mock_llm, mock_storage):
        """Service accepts injected dependencies."""
        service = ProfilingDataExtractionService(
            llm=mock_llm,
            storage=mock_storage,
        )
        assert service.storage is mock_storage
        mock_llm.with_structured_output.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_from_messages(self, mock_llm, sample_messages):
        """Extract from provided messages."""
        # Setup structured LLM response
        structured_llm = mock_llm.with_structured_output.return_value
        structured_llm.ainvoke.return_value = ExtractionResponse(
            facts=[
                ExtractedFact(
                    dimension="core_identity",
                    fact_type="profession",
                    value="software engineer at Google",
                    confidence=0.95,
                    source_quote="I'm a software engineer working at Google.",
                )
            ]
        )

        service = ProfilingDataExtractionService(llm=mock_llm)

        results = await service.extract_from_messages(
            messages=sample_messages,
            user_id="test-user",
            config=ExtractionConfig(min_messages_for_extraction=1),
        )

        assert len(results) == 1
        assert results[0].data["dimension"] == "core_identity"
        assert results[0].user_id == "test-user"

    @pytest.mark.asyncio
    async def test_skips_low_confidence(self, mock_llm, sample_messages):
        """Filters out low-confidence extractions."""
        structured_llm = mock_llm.with_structured_output.return_value
        structured_llm.ainvoke.return_value = ExtractionResponse(
            facts=[
                ExtractedFact(
                    dimension="core_identity",
                    fact_type="guess",
                    value="x",
                    confidence=0.3,
                    source_quote="...",
                ),
                ExtractedFact(
                    dimension="core_identity",
                    fact_type="profession",
                    value="y",
                    confidence=0.8,
                    source_quote="...",
                ),
            ]
        )

        service = ProfilingDataExtractionService(llm=mock_llm)

        results = await service.extract_from_messages(
            messages=sample_messages,
            user_id="test-user",
            config=ExtractionConfig(
                confidence_threshold=0.5,
                min_messages_for_extraction=1,
            ),
        )

        assert len(results) == 1
        assert results[0].data["value"] == "y"

    @pytest.mark.asyncio
    async def test_filters_by_dimensions(self, mock_llm, sample_messages):
        """Only extracts requested dimensions."""
        structured_llm = mock_llm.with_structured_output.return_value
        structured_llm.ainvoke.return_value = ExtractionResponse(
            facts=[
                ExtractedFact(
                    dimension="core_identity",
                    fact_type="profession",
                    value="x",
                    confidence=0.9,
                    source_quote="...",
                ),
                ExtractedFact(
                    dimension="preferences_patterns",
                    fact_type="preference",
                    value="y",
                    confidence=0.9,
                    source_quote="...",
                ),
            ]
        )

        service = ProfilingDataExtractionService(llm=mock_llm)

        results = await service.extract_from_messages(
            messages=sample_messages,
            user_id="test-user",
            config=ExtractionConfig(
                dimensions=["core_identity"],  # Only this one
                min_messages_for_extraction=1,
            ),
        )

        assert len(results) == 1
        assert results[0].data["dimension"] == "core_identity"

    @pytest.mark.asyncio
    async def test_handles_empty_response(self, mock_llm, sample_messages):
        """Handles empty extraction gracefully."""
        structured_llm = mock_llm.with_structured_output.return_value
        structured_llm.ainvoke.return_value = ExtractionResponse(facts=[])

        service = ProfilingDataExtractionService(llm=mock_llm)

        results = await service.extract_from_messages(
            messages=sample_messages,
            user_id="test-user",
            config=ExtractionConfig(min_messages_for_extraction=1),
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_handles_llm_error(self, mock_llm, sample_messages):
        """Handles LLM errors gracefully."""
        structured_llm = mock_llm.with_structured_output.return_value
        structured_llm.ainvoke.side_effect = Exception("API error")

        service = ProfilingDataExtractionService(llm=mock_llm)

        results = await service.extract_from_messages(
            messages=sample_messages,
            user_id="test-user",
            config=ExtractionConfig(min_messages_for_extraction=1),
        )

        # Should return empty, not raise
        assert results == []

    @pytest.mark.asyncio
    async def test_skips_when_too_few_messages(self, mock_llm):
        """Skips extraction when below min_messages_for_extraction."""
        service = ProfilingDataExtractionService(llm=mock_llm)

        results = await service.extract_from_messages(
            messages=[MessageRecord(id=1, content="Hi")],
            user_id="test-user",
            config=ExtractionConfig(min_messages_for_extraction=5),
        )

        assert results == []
        # LLM should not be called
        structured_llm = mock_llm.with_structured_output.return_value
        structured_llm.ainvoke.assert_not_called()
```

---

## Error Handling Strategy

### Error Categories

| Category | Example | Handling |
|----------|---------|----------|
| **LLM Errors** | API timeout, rate limit | Log warning, return empty for batch, continue |
| **Validation Errors** | Pydantic validation failed | Handled by structured output, returns valid model |
| **Storage Errors** | DB connection failed | Let exception propagate, mark run as failed |
| **Missing Storage** | extract_for_user without storage | Raise ValueError immediately |

### Run Status Flow

```
pending → running → completed
                  ↘ failed (with error message)
```

### Graceful Degradation

```python
# Storage optional
if self.storage:
    await self.storage.save_extracted_profiling_data(results)

# LLM failures don't stop extraction
try:
    response = await self.structured_llm.ainvoke(messages)
except Exception as e:
    logger.warning(f"LLM call failed: {e}")
    return []  # Empty results for this batch, continue with next
```

---

## Testing Strategy

### Unit Tests (Mock LLM + Storage)

| Test | Purpose |
|------|---------|
| `test_init_with_defaults` | Verify default initialization |
| `test_extract_from_messages` | Core extraction flow |
| `test_skips_low_confidence` | Confidence filtering |
| `test_filters_by_dimensions` | Dimension filtering |
| `test_handles_empty_response` | Empty extraction |
| `test_handles_llm_error` | Error resilience |
| `test_skips_when_too_few_messages` | Min messages check |

### Integration Tests (Real LLM, Mock Storage)

| Test | Purpose |
|------|---------|
| `test_real_extraction` | End-to-end with real LLM |
| `test_batch_processing` | Multiple batches |
| `test_incremental_extraction` | since_message_id works |

---

## Performance Considerations

### Batching Strategy

```python
# Default: 50 messages per batch
# Trade-off: Larger batches = fewer LLM calls but more context
config = ExtractionConfig(batch_size=50)
```

### Token Estimation

```python
# Rough estimate: 4 chars = 1 token
# 50 messages × 200 chars avg = 10,000 chars = 2,500 tokens
# Plus system prompt ~500 tokens
# Total: ~3,000 tokens per batch (well under 4k limits)
```

### Cost Control

- Use `gpt-4o-mini` (~$0.15/1M input tokens) for extraction
- Track `model_used` in extraction runs for cost attribution
- Log token usage if available from response

---

## Deferred: CPF-7 Prompts

**Status:** Will be implemented when CPF-7 specification is complete.

**Location:** `chatforge/services/profiling_data_extraction/prompts.py`

**What's needed:**
- Detailed system prompt with CPF-7 dimension definitions
- Examples of what to extract for each dimension
- Rules for confidence scoring
- Edge case handling instructions

**Current placeholder:**
```python
DEFAULT_SYSTEM_PROMPT = """Extract profiling information that the user reveals about themselves.
Only extract explicit statements, not inferences.
Include exact source quotes for traceability."""
```

---

## Future Enhancements (Out of Scope)

1. **Parallel batch processing** - Process multiple batches concurrently
2. **Streaming extraction** - Extract as messages come in
3. **Caching** - Cache extraction results by message hash
4. **Confidence calibration** - Adjust thresholds based on model
5. **Multi-language support** - Handle non-English conversations

---

## Summary: Build Order

| Step | File | Status |
|------|------|--------|
| 1 | `models.py` - Pydantic models | TODO |
| 2 | `service.py` - Main service | TODO |
| 3 | `__init__.py` - Update exports | TODO |
| 4 | Unit tests | TODO |
| 5 | `prompts.py` - CPF-7 prompts | DEFERRED (depends on CPF-7 spec) |

**Estimated Implementation:**
- Service: ~200 lines
- Models: ~40 lines
- Tests: ~150 lines
