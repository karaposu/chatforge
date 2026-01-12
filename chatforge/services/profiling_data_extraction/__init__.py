"""
Profiling Data Extraction Service.

Extracts profiling data from conversations using LLM-based semantic understanding.
Implements CPF-7 (Conversational Profiling Framework - 7 Dimensions).

Note: This service extracts raw profiling data, not aggregated profiles.
Profiling (aggregation) is a separate future step.

Usage:
    from chatforge.services.profiling_data_extraction import (
        ExtractionConfig,
    )

    config = ExtractionConfig(
        dimensions=["core_identity", "preferences_patterns"],
        batch_size=50,
    )
"""

from chatforge.services.profiling_data_extraction.config import ExtractionConfig

__all__ = [
    "ExtractionConfig",
]
