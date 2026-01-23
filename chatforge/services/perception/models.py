"""
Perception Service Models

Data classes for perception analysis.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Reference:
    """
    A reference image with optional description.

    Used to provide context for comparison during analysis.
    """
    image: bytes
    text: Optional[str] = None


@dataclass
class Issue:
    """
    An issue found during analysis.
    """
    location: str  # e.g., "slide 0", "shape 3", "top-left region"
    description: str
    severity: str = "medium"  # "low", "medium", "high"
    suggestion: Optional[str] = None


@dataclass
class AnalysisResult:
    """
    Result of perception analysis.
    """
    satisfied: bool
    issues: list[Issue] = field(default_factory=list)
    summary: str = ""
    raw_response: Optional[str] = None  # Original LLM response for debugging
