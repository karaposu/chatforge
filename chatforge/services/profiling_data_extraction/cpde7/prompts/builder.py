"""
CPDE-7 Prompt Builder using Proteas.

Builds extraction prompts for any combination of dimensions.
"""

from typing import Iterator

from pydantic import BaseModel, create_model
from proteas import Proteas, PromptTemplateUnit, generate_combinations, count_combinations

from chatforge.services.profiling_data_extraction.cpde7.prompts.dimension_units import (
    DIMENSION_UNITS,
    DIMENSION_NAMES,
    HEADER_UNIT,
    MESSAGES_UNIT,
    INSTRUCTIONS_UNIT,
)
from chatforge.services.profiling_data_extraction.cpde7.models import (
    BatchCoreIdentityResult,
    BatchOpinionsResult,
    BatchPreferencesResult,
    BatchDesiresResult,
    BatchNarrativeResult,
    BatchEventsResult,
    BatchEntitiesResult,
)


# =============================================================================
# Batch Result Types Registry
# =============================================================================

BATCH_RESULT_TYPES: dict[str, type[BaseModel]] = {
    "core_identity": BatchCoreIdentityResult,
    "opinions_views": BatchOpinionsResult,
    "preferences_patterns": BatchPreferencesResult,
    "desires_needs": BatchDesiresResult,
    "life_narrative": BatchNarrativeResult,
    "events": BatchEventsResult,
    "entities_relationships": BatchEntitiesResult,
}
"""Maps dimension names to their batch result Pydantic models."""


def build_prompt(
    dimensions: list[str],
    messages: str,
) -> str:
    """
    Build an extraction prompt for the specified dimensions.

    Args:
        dimensions: List of dimension names to extract
        messages: The messages to analyze

    Returns:
        The complete prompt string

    Example:
        prompt = build_prompt(
            dimensions=["core_identity", "events"],
            messages="Message ID: msg_001\\nContent: I'm 34 years old..."
        )
    """
    if not dimensions:
        raise ValueError("At least one dimension must be specified")

    # Validate dimensions
    for dim in dimensions:
        if dim not in DIMENSION_UNITS:
            raise ValueError(f"Unknown dimension: {dim}. Valid: {DIMENSION_NAMES}")

    # Build prompt using Proteas
    p = Proteas()

    # Add header
    p.add(HEADER_UNIT)

    # Add selected dimension units
    for dim in dimensions:
        p.add(DIMENSION_UNITS[dim])

    # Add messages placeholder
    p.add(MESSAGES_UNIT)

    # Add instructions
    p.add(INSTRUCTIONS_UNIT)

    # Compile with messages
    return p.compile(messages=messages)


def build_output_model(dimensions: list[str]) -> type[BaseModel]:
    """
    Create a Pydantic model with exactly the requested dimensions.

    This model is used internally for the LLM structured output call.
    The user-facing result is always BatchProfilingDataExtractionResult.

    Args:
        dimensions: List of dimension names to include

    Returns:
        Dynamically created Pydantic model class

    Raises:
        ValueError: If dimensions is empty or contains invalid dimension names

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
    # The ... (Ellipsis) means the field is required
    fields = {
        dim: (BATCH_RESULT_TYPES[dim], ...)
        for dim in dimensions
    }

    return create_model("DynamicExtractionOutput", **fields)


def build_all_combinations(
    min_size: int = 2,
    max_size: int = 6,
) -> Iterator[tuple[tuple[str, ...], Proteas]]:
    """
    Generate Proteas instances for all dimension combinations.

    This generates prompts for the "middle" combinations (2-6 dimensions).
    Single dimension and all-7 prompts already exist as static prompts.

    Args:
        min_size: Minimum number of dimensions (default: 2)
        max_size: Maximum number of dimensions (default: 6)

    Yields:
        Tuples of (dimension_names, proteas_instance)

    Example:
        for names, p in build_all_combinations():
            prompt = p.compile(messages="...")
            print(f"Combination {names}: {len(prompt)} chars")
    """
    # Get dimension units as a list
    dimension_units = list(DIMENSION_UNITS.values())

    # Base units that are always included
    base_units = [HEADER_UNIT, MESSAGES_UNIT, INSTRUCTIONS_UNIT]

    # Generate all combinations
    yield from generate_combinations(
        units=dimension_units,
        min_size=min_size,
        max_size=max_size,
        base_units=base_units,
    )


def count_dimension_combinations(
    min_size: int = 2,
    max_size: int = 6,
) -> int:
    """
    Count how many dimension combinations will be generated.

    Args:
        min_size: Minimum number of dimensions
        max_size: Maximum number of dimensions

    Returns:
        Total number of combinations
    """
    return count_combinations(n=7, min_size=min_size, max_size=max_size)


# =============================================================================
# Testing / Verification
# =============================================================================

def verify_all_combinations() -> dict:
    """
    Generate all 119 combinations and verify they work.

    Returns:
        Dictionary with statistics about the generated combinations.
    """
    test_messages = """
Message ID: msg_001
Content: I'm a 34-year-old software engineer living in Seattle.

Message ID: msg_002
Content: I think remote work is the future.
"""

    stats = {
        "total": 0,
        "by_size": {},
        "sample_prompts": [],
    }

    for names, p in build_all_combinations(min_size=2, max_size=6):
        size = len(names)

        # Count by size
        if size not in stats["by_size"]:
            stats["by_size"][size] = 0
        stats["by_size"][size] += 1
        stats["total"] += 1

        # Store a few sample prompts
        if len(stats["sample_prompts"]) < 3:
            prompt = p.compile(messages=test_messages)
            stats["sample_prompts"].append({
                "dimensions": names,
                "prompt_length": len(prompt),
            })

    return stats


if __name__ == "__main__":
    # Quick verification
    print("Verifying all 119 combinations...")
    stats = verify_all_combinations()

    print(f"\nTotal combinations: {stats['total']}")
    print("\nBy size:")
    for size, count in sorted(stats["by_size"].items()):
        print(f"  {size} dimensions: {count} combinations")

    print("\nSample prompts:")
    for sample in stats["sample_prompts"]:
        print(f"  {sample['dimensions']}: {sample['prompt_length']} chars")
