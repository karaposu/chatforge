"""
Profiling Data Extraction Service.

Extracts profiling data from conversations using LLM-based semantic understanding.

Available Frameworks:
- CPDE-7: Conversational Profiling Data Extraction - 7 Dimensions (implemented)
- ASNE: Atomic Semantic Natural-language Extraction (future)
- CAF: Conversation Anatomy Framework (future)

Note: This service extracts raw profiling data, not aggregated profiles.
Profiling (aggregation) is a separate future step.

Usage:
    from chatforge.services.profiling_data_extraction import (
        CPDE7LLMService,
        ProfilingDataExtractor,
        BaseTriggerService,
        TriggerConfig,
    )

    # Direct LLM extraction
    service = CPDE7LLMService(provider="openai", model_name="gpt-4o-mini")
    result = await service.extract_core_identity(messages_text)

    # Pure extraction (no DB)
    extractor = ProfilingDataExtractor(service, batch_size=50)
    items = await extractor.extract_batch(messages)

    # Trigger service (provide your app's repositories)
    trigger = BaseTriggerService(
        message_repo=my_message_repo,
        extraction_repo=my_extraction_repo,
        extractor=extractor,
        config=TriggerConfig(auto_trigger_threshold=10),
    )
    result = await trigger.trigger_extraction(user_id, chat_id)
"""

# Extractor and Orchestrator (generic building blocks)
from chatforge.services.profiling_data_extraction.extractor import (
    ProfilingDataExtractor,
    ExtractedItem,
)
from chatforge.services.profiling_data_extraction.orchestrator import (
    BaseExtractionOrchestrator,
    ExtractionRepository,
)
from chatforge.services.profiling_data_extraction.trigger import (
    BaseTriggerService,
    TriggerConfig,
    TriggerResult,
    MessageRepository,
    ExtractionRepository as TriggerExtractionRepository,
)

# Re-export from CPDE-7 (primary framework)
from chatforge.services.profiling_data_extraction.cpde7 import (
    # Service
    CPDE7LLMService,
    # Config
    ExtractionConfig,
    CPF7_DIMENSIONS,
    # Batch output models
    BatchCoreIdentityOutput,
    BatchOpinionsOutput,
    BatchPreferencesOutput,
    BatchDesiresOutput,
    BatchNarrativeOutput,
    BatchEventsOutput,
    BatchEntitiesOutput,
    # Combined result
    BatchProfilingDataExtractionResult,
    BatchFullExtractionResult,
    BatchAll7Output,
    # Service-level result
    ExtractionRunResult,
    # Registry
    BATCH_DIMENSION_MODELS,
    # Targeted extraction helpers
    format_messages_with_markers,
)

__all__ = [
    # Generic building blocks
    "ProfilingDataExtractor",
    "ExtractedItem",
    "BaseExtractionOrchestrator",
    "ExtractionRepository",
    # Trigger service
    "BaseTriggerService",
    "TriggerConfig",
    "TriggerResult",
    "MessageRepository",
    "TriggerExtractionRepository",
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
    # Targeted extraction helpers
    "format_messages_with_markers",
]
