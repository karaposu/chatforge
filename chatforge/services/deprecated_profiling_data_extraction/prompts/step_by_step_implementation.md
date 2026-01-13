# Step-by-Step Implementation Guide

This guide outlines the implementation steps to add the configurable extraction system with two strategies (per-dimension and combined).

---

## Current State

### Already Implemented

| Component | Location | Status |
|-----------|----------|--------|
| Proteas library | `~/Desktop/projects/proteas/` | Done |
| Dimension units | `prompts/dimension_units.py` | Done |
| `build_prompt()` | `prompts/builder.py` | Done |
| Static prompts | `batch_prompts.py` | Done |
| Batch models | `models.py` | Done |
| Individual extract methods | `cpde7llmservice.py` | Done |
| `extract_all_7()` | `cpde7llmservice.py` | Done |
| `extract_dimension()` | `cpde7llmservice.py` | Done |

### Needs Implementation

| Component | Location | Status |
|-----------|----------|--------|
| Rename `BatchFullExtractionResult` | `models.py` | TODO |
| Add `BATCH_RESULT_TYPES` registry | `prompts/builder.py` | TODO |
| Add `build_output_model()` | `prompts/builder.py` | TODO |
| Add `extract_dimensions()` | `cpde7llmservice.py` | TODO |
| Add `_extract_per_dimension()` | `cpde7llmservice.py` | TODO |
| Add `_extract_combined()` | `cpde7llmservice.py` | TODO |
| Update exports | `prompts/__init__.py` | TODO |
| Tests | `extraction_tests/` | TODO |

---

## Step 1: Rename Model in `models.py`

**File:** `chatforge/services/profiling_data_extraction/models.py`

**Task:** Rename `BatchFullExtractionResult` to `BatchProfilingDataExtractionResult`

```python
# Before
class BatchFullExtractionResult(BaseModel):
    ...

# After
class BatchProfilingDataExtractionResult(BaseModel):
    """Result container for profiling data extraction.

    All 7 dimension fields are optional:
    - None = dimension was not requested
    - has_content=False = requested but nothing found
    - has_content=True = requested and data found
    """
    core_identity: BatchCoreIdentityResult | None = None
    opinions_views: BatchOpinionsResult | None = None
    preferences_patterns: BatchPreferencesResult | None = None
    desires_needs: BatchDesiresResult | None = None
    life_narrative: BatchNarrativeResult | None = None
    events: BatchEventsResult | None = None
    entities_relationships: BatchEntitiesResult | None = None
```

**Also:** Update any existing references to `BatchFullExtractionResult` in the codebase.

---

## Step 2: Add `BATCH_RESULT_TYPES` Registry in `builder.py`

**File:** `chatforge/services/profiling_data_extraction/prompts/builder.py`

**Task:** Add registry mapping dimension names to their result types

```python
from chatforge.services.profiling_data_extraction.models import (
    BatchCoreIdentityResult,
    BatchOpinionsResult,
    BatchPreferencesResult,
    BatchDesiresResult,
    BatchNarrativeResult,
    BatchEventsResult,
    BatchEntitiesResult,
)

BATCH_RESULT_TYPES = {
    "core_identity": BatchCoreIdentityResult,
    "opinions_views": BatchOpinionsResult,
    "preferences_patterns": BatchPreferencesResult,
    "desires_needs": BatchDesiresResult,
    "life_narrative": BatchNarrativeResult,
    "events": BatchEventsResult,
    "entities_relationships": BatchEntitiesResult,
}
```

---

## Step 3: Add `build_output_model()` in `builder.py`

**File:** `chatforge/services/profiling_data_extraction/prompts/builder.py`

**Task:** Add function to create dynamic Pydantic models for LLM calls

```python
from pydantic import BaseModel, create_model

def build_output_model(dimensions: list[str]) -> type[BaseModel]:
    """
    Create a Pydantic model with exactly the requested dimensions.

    This model is used internally for the LLM structured output call.
    The user-facing result is always BatchProfilingDataExtractionResult.

    Args:
        dimensions: List of dimension names to include

    Returns:
        Dynamically created Pydantic model class

    Example:
        model = build_output_model(["core_identity", "events"])
        # Creates model with only core_identity and events fields
    """
    if not dimensions:
        raise ValueError("At least one dimension must be specified")

    # Validate dimensions
    for dim in dimensions:
        if dim not in BATCH_RESULT_TYPES:
            raise ValueError(f"Unknown dimension: {dim}. Valid: {list(BATCH_RESULT_TYPES.keys())}")

    # Build fields dict for create_model
    fields = {
        dim: (BATCH_RESULT_TYPES[dim], ...)
        for dim in dimensions
    }

    return create_model("DynamicExtractionOutput", **fields)
```

---

## Step 4: Update Exports in `prompts/__init__.py`

**File:** `chatforge/services/profiling_data_extraction/prompts/__init__.py`

**Task:** Export new functions (show complete file)

```python
"""
CPDE-7 Prompt Generation using Proteas.

This module uses Proteas to dynamically generate extraction prompts
for any combination of the 7 dimensions.
"""

from chatforge.services.profiling_data_extraction.prompts.dimension_units import (
    DIMENSION_UNITS,
    DIMENSION_NAMES,
    HEADER_UNIT,
    MESSAGES_UNIT,
    INSTRUCTIONS_UNIT,
    get_dimension_unit,
)
from chatforge.services.profiling_data_extraction.prompts.builder import (
    build_prompt,
    build_output_model,
    build_all_combinations,
    BATCH_RESULT_TYPES,
)

__all__ = [
    # Dimension units
    "DIMENSION_UNITS",
    "DIMENSION_NAMES",
    "HEADER_UNIT",
    "MESSAGES_UNIT",
    "INSTRUCTIONS_UNIT",
    "get_dimension_unit",
    # Builder functions
    "build_prompt",
    "build_output_model",
    "build_all_combinations",
    "BATCH_RESULT_TYPES",
]
```

---

## Step 5: Add `_extract_per_dimension()` in Service

**File:** `chatforge/services/profiling_data_extraction/cpde7llmservice.py`

**Task:** Add private method for per-dimension strategy

```python
async def _extract_per_dimension(
    self,
    messages: str,
    dimensions: list[str],
    parallel: bool = False
) -> BatchProfilingDataExtractionResult:
    """
    Extract dimensions with separate LLM call per dimension.

    Args:
        messages: Formatted message text
        dimensions: List of dimensions to extract
        parallel: Run calls in parallel if True

    Returns:
        BatchProfilingDataExtractionResult with requested dimensions populated
    """
    pde_result = BatchProfilingDataExtractionResult()

    if parallel:
        tasks = [self.extract_dimension(messages, dim) for dim in dimensions]
        outputs = await asyncio.gather(*tasks)
        for dim, output in zip(dimensions, outputs):
            inner = getattr(output, dim)
            setattr(pde_result, dim, inner)
    else:
        for dim in dimensions:
            output = await self.extract_dimension(messages, dim)
            inner = getattr(output, dim)
            setattr(pde_result, dim, inner)

    return pde_result
```

---

## Step 6: Add `_extract_combined()` in Service

**File:** `chatforge/services/profiling_data_extraction/cpde7llmservice.py`

**Task:** Add private method for combined strategy

**Note:** Imports are at file top (see Step 8), not inside the method.

```python
async def _extract_combined(
    self,
    messages: str,
    dimensions: list[str]
) -> BatchProfilingDataExtractionResult:
    """
    Extract dimensions with single LLM call using combined prompt.

    Uses Proteas to build a prompt with only the requested dimensions.

    Args:
        messages: Formatted message text
        dimensions: List of dimensions to extract

    Returns:
        BatchProfilingDataExtractionResult with requested dimensions populated
    """
    # Build prompt with Proteas
    prompt = build_prompt(dimensions=dimensions, messages=messages)

    # Create dynamic model for LLM response
    output_model = build_output_model(dimensions)

    # Single LLM call
    structured_llm = self._get_llm().with_structured_output(output_model)
    llm_response = await structured_llm.ainvoke([HumanMessage(content=prompt)])

    # Map to BatchProfilingDataExtractionResult
    pde_result = BatchProfilingDataExtractionResult()
    for dim in dimensions:
        setattr(pde_result, dim, getattr(llm_response, dim))

    return pde_result
```

---

## Step 7: Add `extract_dimensions()` Public Method

**File:** `chatforge/services/profiling_data_extraction/cpde7llmservice.py`

**Task:** Add unified public interface

**Note:** Uses `DIMENSION_NAMES` from prompts module instead of defining a new list.

```python
from typing import Literal
from chatforge.services.profiling_data_extraction.prompts import DIMENSION_NAMES

async def extract_dimensions(
    self,
    messages: str,
    dimensions: list[str],
    strategy: Literal["per_dimension", "combined"] = "combined",
    parallel: bool = False
) -> BatchProfilingDataExtractionResult:
    """
    Extract selected dimensions using specified strategy.

    Args:
        messages: Formatted message text with Message ID and Content
        dimensions: List of dimensions to extract (at least one required)
        strategy:
            - "per_dimension": Separate LLM call per dimension
            - "combined": Single LLM call with combined prompt (uses Proteas)
        parallel: Run per-dimension calls in parallel (only for "per_dimension")

    Returns:
        BatchProfilingDataExtractionResult with requested dimensions populated,
        non-requested dimensions are None.

    Raises:
        ValueError: If dimensions is empty or contains invalid dimension names.

    Example:
        pde_result = await service.extract_dimensions(
            messages=messages,
            dimensions=["core_identity", "events"],
            strategy="combined"
        )

        if pde_result.core_identity is not None:
            print(pde_result.core_identity.items)
    """
    # Validate dimensions not empty
    if not dimensions:
        raise ValueError("At least one dimension must be specified")

    # Validate dimension names
    for dim in dimensions:
        if dim not in DIMENSION_NAMES:
            raise ValueError(f"Invalid dimension: {dim}. Valid: {DIMENSION_NAMES}")

    # Special case: all 7 dimensions with combined strategy
    # Use existing optimized extract_all_7()
    if strategy == "combined" and set(dimensions) == set(DIMENSION_NAMES):
        all_7_result = await self.extract_all_7(messages)
        # Convert BatchAll7Output to BatchProfilingDataExtractionResult
        pde_result = BatchProfilingDataExtractionResult(
            core_identity=all_7_result.core_identity,
            opinions_views=all_7_result.opinions_views,
            preferences_patterns=all_7_result.preferences_patterns,
            desires_needs=all_7_result.desires_needs,
            life_narrative=all_7_result.life_narrative,
            events=all_7_result.events,
            entities_relationships=all_7_result.entities_relationships,
        )
        return pde_result

    # Route to appropriate strategy
    if strategy == "per_dimension":
        return await self._extract_per_dimension(messages, dimensions, parallel)
    else:
        return await self._extract_combined(messages, dimensions)
```

---

## Step 8: Update Imports in Service

**File:** `chatforge/services/profiling_data_extraction/cpde7llmservice.py`

**Task:** Add necessary imports at top of file

```python
import asyncio
from typing import Literal

from chatforge.services.profiling_data_extraction.models import (
    # ... existing imports
    BatchProfilingDataExtractionResult,  # Add this (renamed from BatchFullExtractionResult)
)

from chatforge.services.profiling_data_extraction.prompts import (
    build_prompt,
    build_output_model,
    DIMENSION_NAMES,
)
```

---

## Step 9: Write Tests

**File:** `chatforge/services/profiling_data_extraction/extraction_tests/test_extract_dimensions.py` (new)

**Task:** Create test file for new functionality

```python
import pytest
from chatforge.services.profiling_data_extraction import CPDE7LLMService

# Test messages
TEST_MESSAGES = """
Message ID: msg_001
Content: I'm a 34-year-old software engineer living in Seattle.

Message ID: msg_002
Content: I think remote work is the future.
"""

@pytest.fixture
def service():
    return CPDE7LLMService(provider="openai", model_name="gpt-4o-mini")

class TestExtractDimensions:
    """Tests for extract_dimensions() method."""

    @pytest.mark.asyncio
    async def test_per_dimension_sequential(self, service):
        """Test per-dimension strategy with sequential execution."""
        pde_result = await service.extract_dimensions(
            messages=TEST_MESSAGES,
            dimensions=["core_identity", "opinions_views"],
            strategy="per_dimension",
            parallel=False
        )

        # Requested dimensions should not be None
        assert pde_result.core_identity is not None
        assert pde_result.opinions_views is not None

        # Non-requested should be None
        assert pde_result.events is None
        assert pde_result.entities_relationships is None

    @pytest.mark.asyncio
    async def test_per_dimension_parallel(self, service):
        """Test per-dimension strategy with parallel execution."""
        pde_result = await service.extract_dimensions(
            messages=TEST_MESSAGES,
            dimensions=["core_identity", "events"],
            strategy="per_dimension",
            parallel=True
        )

        assert pde_result.core_identity is not None
        assert pde_result.events is not None
        assert pde_result.opinions_views is None

    @pytest.mark.asyncio
    async def test_combined_strategy(self, service):
        """Test combined strategy with Proteas."""
        pde_result = await service.extract_dimensions(
            messages=TEST_MESSAGES,
            dimensions=["core_identity", "opinions_views"],
            strategy="combined"
        )

        assert pde_result.core_identity is not None
        assert pde_result.opinions_views is not None
        assert pde_result.events is None

    @pytest.mark.asyncio
    async def test_combined_all_7_uses_static_prompt(self, service):
        """Test that all 7 dimensions uses extract_all_7()."""
        pde_result = await service.extract_dimensions(
            messages=TEST_MESSAGES,
            dimensions=[
                "core_identity", "opinions_views", "preferences_patterns",
                "desires_needs", "life_narrative", "events", "entities_relationships"
            ],
            strategy="combined"
        )

        # All dimensions should be populated
        assert pde_result.core_identity is not None
        assert pde_result.opinions_views is not None
        assert pde_result.preferences_patterns is not None
        assert pde_result.desires_needs is not None
        assert pde_result.life_narrative is not None
        assert pde_result.events is not None
        assert pde_result.entities_relationships is not None

    @pytest.mark.asyncio
    async def test_invalid_dimension_raises_error(self, service):
        """Test that invalid dimension name raises ValueError."""
        with pytest.raises(ValueError, match="Invalid dimension"):
            await service.extract_dimensions(
                messages=TEST_MESSAGES,
                dimensions=["invalid_dimension"],
                strategy="combined"
            )

    @pytest.mark.asyncio
    async def test_empty_dimensions_raises_error(self, service):
        """Test that empty dimensions list raises ValueError."""
        with pytest.raises(ValueError, match="At least one dimension"):
            await service.extract_dimensions(
                messages=TEST_MESSAGES,
                dimensions=[],
                strategy="combined"
            )

    @pytest.mark.asyncio
    async def test_single_dimension(self, service):
        """Test extraction with single dimension."""
        pde_result = await service.extract_dimensions(
            messages=TEST_MESSAGES,
            dimensions=["core_identity"],
            strategy="combined"
        )

        assert pde_result.core_identity is not None
        # All other dimensions should be None
        assert pde_result.opinions_views is None
        assert pde_result.events is None

    @pytest.mark.asyncio
    async def test_result_semantics(self, service):
        """Test None vs has_content=False distinction."""
        pde_result = await service.extract_dimensions(
            messages=TEST_MESSAGES,
            dimensions=["core_identity"],
            strategy="combined"
        )

        # Requested dimension is not None
        assert pde_result.core_identity is not None

        # Check has_content and items exist
        assert hasattr(pde_result.core_identity, 'has_content')
        assert hasattr(pde_result.core_identity, 'items')

        # Non-requested is None (not has_content=False)
        assert pde_result.events is None
```

---

## Step 10: Update Notebook for Testing (Optional)

**File:** `chatforge/services/profiling_data_extraction/extraction_tests/notebooks/cpde_test2.ipynb`

**Task:** Add cells to test new `extract_dimensions()` method

```python
# Test extract_dimensions with combined strategy
pde_result = await cpde_service.extract_dimensions(
    messages=test_messages,
    dimensions=["core_identity", "events", "entities_relationships"],
    strategy="combined"
)

print("Combined strategy (1 LLM call):")
print(f"  core_identity: {pde_result.core_identity is not None}")
print(f"  events: {pde_result.events is not None}")
print(f"  opinions_views: {pde_result.opinions_views}")  # Should be None
```

---

## Implementation Order

1. **Step 1** - Rename model (models.py)
2. **Step 2** - Add BATCH_RESULT_TYPES (builder.py)
3. **Step 3** - Add build_output_model() (builder.py)
4. **Step 4** - Update exports (prompts/__init__.py)
5. **Step 8** - Update imports in service (cpde7llmservice.py) - do this before adding methods
6. **Step 5** - Add _extract_per_dimension() (cpde7llmservice.py)
7. **Step 6** - Add _extract_combined() (cpde7llmservice.py)
8. **Step 7** - Add extract_dimensions() (cpde7llmservice.py)
9. **Step 9** - Write tests
10. **Step 10** - Update notebook (optional)

---

## Verification Checklist

After implementation, verify:

- [ ] `BatchProfilingDataExtractionResult` renamed in models.py
- [ ] `build_output_model()` works for 1-6 dimensions
- [ ] `extract_dimensions()` with `strategy="per_dimension"` works (sequential)
- [ ] `extract_dimensions()` with `strategy="per_dimension", parallel=True` works
- [ ] `extract_dimensions()` with `strategy="combined"` works
- [ ] All 7 dimensions with combined strategy uses `extract_all_7()`
- [ ] Non-requested dimensions return `None`
- [ ] Requested but empty dimensions return `has_content=False, items=[]`
- [ ] Invalid dimension names raise `ValueError`
- [ ] All existing tests still pass
- [ ] New tests pass
