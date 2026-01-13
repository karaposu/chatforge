"""
Profiling Data Extraction Service.

Extracts profiling data from conversations using LLM-based semantic understanding.
Implements CPDE-7 (Conversational Profiling Data Extraction - 7 Dimensions).

Note: This service extracts raw profiling data, not aggregated profiles.
Profiling (aggregation) is a separate future step.

Usage:
    from chatforge.services.profiling_data_extraction import (
        CPDE7LLMService,
        ExtractionConfig,
    )

    # Direct LLM extraction
    service = CPDE7LLMService(provider="openai", model_name="gpt-4o-mini")
    result = service.extract_core_identity(messages_text)

    # Configuration for batch processing
    config = ExtractionConfig(
        dimensions=["core_identity", "preferences_patterns"],
        batch_size=50,
    )
"""

from chatforge.services.profiling_data_extraction.config import (
    ExtractionConfig,
    CPF7_DIMENSIONS,
)
from chatforge.services.profiling_data_extraction.cpde7llmservice import CPDE7LLMService
from chatforge.services.profiling_data_extraction.models import (
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
    # Registry
    BATCH_DIMENSION_MODELS,
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
    "BatchFullExtractionResult",  # Backward compatibility alias
    "BatchAll7Output",
    "BATCH_DIMENSION_MODELS",
]
