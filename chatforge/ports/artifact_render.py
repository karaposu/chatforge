"""
Artifact Render Port

Defines the interface for rendering artifacts to images.
"""

from pathlib import Path
from typing import Literal, Optional, Protocol, Union

from PIL import Image

ImageFormat = Literal["bytes", "base64", "pil"]


class ArtifactRenderPort(Protocol):
    """
    Port for rendering artifacts to visual images.

    Implementations convert source artifacts (PPTX, HTML, PDF, etc.)
    into visual representations that can be analyzed or displayed.
    """

    def render(
        self,
        artifact: Union[bytes, str, Path],
        page: Optional[int] = None,
        output_format: ImageFormat = "bytes",
    ) -> Union[list[bytes], list[str], list[Image.Image]]:
        """
        Render artifact to images.

        Args:
            artifact: Source file as bytes, file path string, or Path object
            page: Optional specific page/slide index to render (0-based).
                  If None, renders all pages/slides.
            output_format: Output format for images:
                - "bytes": Raw PNG image bytes (default)
                - "base64": Base64 encoded PNG string
                - "pil": PIL Image object

        Returns:
            List of images in the specified format.
            If page is specified, returns single-item list.

        Raises:
            FileNotFoundError: If artifact path doesn't exist
            ValueError: If artifact format is not supported
            RuntimeError: If rendering fails
        """
        ...
