"""
Artifact Editor Adapters

Adapters for editing artifacts (PPTX, HTML, etc.).
"""

from chatforge.adapters.artifact_editor.libreoffice_docker import (
    LibreOfficeEditorDockerServerAdapter,
)

__all__ = [
    "LibreOfficeEditorDockerServerAdapter",
]
