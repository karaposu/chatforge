"""
PRAGMA: Conversational Act Analysis.

Analyzes what people DO in conversation — their involvement, control moves,
substance, and intent — separately from what they SAY (content extraction).

Usage:
    from pragma.config import PragmaConfig
    from pragma.models import PragmaMessageResult, PragmaConversationResult
"""

from pragma.config import PragmaConfig, PRAGMA_DIMENSIONS
from pragma.models import (
    # Per-message outputs
    EIOutput,
    IntentOutput,
    DensityOutput,
    InvestmentOutput,
    DialogicFunctionOutput,
    PragmaMessageResult,
    # Per-segment
    SegmentAggregation,
    DynamicsProfileOutput,
    # Interpretation
    MessageTensionOutput,
    SegmentTensionOutput,
    # APT
    APTInferenceOutput,
    APTProfileOutput,
    # Behavioral
    BehavioralProfileOutput,
    # Combined
    PragmaConversationResult,
)

__all__ = [
    # Config
    "PragmaConfig",
    "PRAGMA_DIMENSIONS",
    # Per-message
    "EIOutput",
    "IntentOutput",
    "DensityOutput",
    "InvestmentOutput",
    "DialogicFunctionOutput",
    "PragmaMessageResult",
    # Per-segment
    "SegmentAggregation",
    "DynamicsProfileOutput",
    # Interpretation
    "MessageTensionOutput",
    "SegmentTensionOutput",
    # APT
    "APTInferenceOutput",
    "APTProfileOutput",
    # Behavioral
    "BehavioralProfileOutput",
    # Combined
    "PragmaConversationResult",
]