"""
Artifact Editor Agent Service

An LLM Agent that modifies artifacts based on freestyle instructions.
"""

from chatforge.services.artifact_editor_agent.service import (
    ArtifactEditorAgentService,
    EditResult,
)

__all__ = [
    "ArtifactEditorAgentService",
    "EditResult",
]
