"""
CPDE-7: Conversational Profiling Data Extraction - 7 Dimensions.

A structured, schema-bound extraction framework that categorizes
profiling data into 7 fixed dimensions.
"""

from chatforge.services.profiling_data_extraction.cpde7.config import (
    ExtractionConfig,
    CPF7_DIMENSIONS,
)
from chatforge.services.profiling_data_extraction.cpde7.cpde7llmservice import CPDE7LLMService
from chatforge.services.profiling_data_extraction.cpde7.models import (
    # Batch output models (for structured output)
    BatchCoreIdentityOutput,
    BatchOpinionsOutput,
    BatchPreferencesOutput,
    BatchDesiresOutput,
    BatchNarrativeOutput,
    BatchEventsOutput,
    BatchEntitiesOutput,
    # Combined result
    BatchProfilingDataExtractionResult,
    BatchFullExtractionResult,  # Backward compatibility alias
    BatchAll7Output,
    # Service-level result
    ExtractionRunResult,
    # Registry
    BATCH_DIMENSION_MODELS,
)
from chatforge.services.profiling_data_extraction.cpde7.prompts import (
    build_prompt,
    build_output_model,
    DIMENSION_NAMES,
    BATCH_RESULT_TYPES,
)
from chatforge.services.profiling_data_extraction.cpde7.batch_prompts_targeted import (
    format_messages_with_markers,
    CPDE_CORE_IDENTITY_TARGETED,
    CPDE_OPINIONS_VIEWS_TARGETED,
    CPDE_PREFERENCES_PATTERNS_TARGETED,
    CPDE_DESIRES_NEEDS_TARGETED,
    CPDE_LIFE_NARRATIVE_TARGETED,
    CPDE_EVENTS_TARGETED,
    CPDE_ENTITIES_RELATIONSHIPS_TARGETED,
    CPDE_ALL_7_TARGETED,
    TARGETING_RULES,
)

__all__ = [
    # Service
    "CPDE7LLMService",
    # Config
    "ExtractionConfig",
    "CPF7_DIMENSIONS",
    # Batch models
    "BatchCoreIdentityOutput",
    "BatchOpinionsOutput",
    "BatchPreferencesOutput",
    "BatchDesiresOutput",
    "BatchNarrativeOutput",
    "BatchEventsOutput",
    "BatchEntitiesOutput",
    "BatchProfilingDataExtractionResult",
    "BatchFullExtractionResult",
    "BatchAll7Output",
    "ExtractionRunResult",
    "BATCH_DIMENSION_MODELS",
    # Prompts (Proteas)
    "build_prompt",
    "build_output_model",
    "DIMENSION_NAMES",
    "BATCH_RESULT_TYPES",
    # Targeted extraction helpers
    "format_messages_with_markers",
    # Targeted prompts
    "CPDE_CORE_IDENTITY_TARGETED",
    "CPDE_OPINIONS_VIEWS_TARGETED",
    "CPDE_PREFERENCES_PATTERNS_TARGETED",
    "CPDE_DESIRES_NEEDS_TARGETED",
    "CPDE_LIFE_NARRATIVE_TARGETED",
    "CPDE_EVENTS_TARGETED",
    "CPDE_ENTITIES_RELATIONSHIPS_TARGETED",
    "CPDE_ALL_7_TARGETED",
    "TARGETING_RULES",
]
