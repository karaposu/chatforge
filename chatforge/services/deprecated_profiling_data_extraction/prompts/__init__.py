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
