"""
LibreOffice Docker Server Render Adapter

Implements ArtifactRenderPort using LibreServer Docker container.
"""

import base64
import io
from pathlib import Path
from typing import Optional, Union

import httpx
from PIL import Image

from chatforge.ports.artifact_render import ImageFormat


class LibreOfficeRenderDockerServerAdapter:
    """
    Adapter for rendering artifacts using LibreServer Docker container.

    Communicates with LibreServer via HTTP API to render PPTX files
    (and other LibreOffice-supported formats) to images.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: float = 60.0,
        dpi: int = 150,
    ):
        """
        Initialize the adapter.

        Args:
            base_url: URL of the LibreServer instance
            timeout: HTTP request timeout in seconds
            dpi: Resolution for rendered images (dots per inch)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.dpi = dpi
        self._client = httpx.Client(timeout=timeout)

    def __del__(self):
        """Cleanup HTTP client on deletion."""
        if hasattr(self, "_client"):
            self._client.close()

    def _prepare_artifact(
        self, artifact: Union[bytes, str, Path]
    ) -> tuple[str, bytes]:
        """
        Prepare artifact for upload.

        Args:
            artifact: Source file as bytes, path string, or Path object

        Returns:
            Tuple of (filename, content_bytes)

        Raises:
            FileNotFoundError: If path doesn't exist
        """
        if isinstance(artifact, (str, Path)):
            path = Path(artifact)
            if not path.exists():
                raise FileNotFoundError(f"Artifact not found: {path}")
            return path.name, path.read_bytes()
        else:
            return "document.pptx", artifact

    def _convert_output(
        self,
        image_bytes: bytes,
        output_format: ImageFormat,
    ) -> Union[bytes, str, Image.Image]:
        """
        Convert image bytes to requested output format.

        Args:
            image_bytes: Raw PNG image bytes
            output_format: Desired output format

        Returns:
            Image in the requested format
        """
        if output_format == "bytes":
            return image_bytes
        elif output_format == "base64":
            return base64.b64encode(image_bytes).decode("utf-8")
        elif output_format == "pil":
            return Image.open(io.BytesIO(image_bytes))
        else:
            raise ValueError(f"Unknown output format: {output_format}")

    def render(
        self,
        artifact: Union[bytes, str, Path],
        page: Optional[int] = None,
        output_format: ImageFormat = "bytes",
    ) -> Union[list[bytes], list[str], list[Image.Image]]:
        """
        Render artifact to images using LibreServer.

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
            RuntimeError: If rendering fails
        """
        filename, content = self._prepare_artifact(artifact)
        mime_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

        try:
            if page is not None:
                # Render single slide
                response = self._client.post(
                    f"{self.base_url}/render/slide/{page}",
                    params={"dpi": self.dpi, "format": "png"},
                    files={"file": (filename, content, mime_type)},
                )
                response.raise_for_status()
                data = response.json()

                image_bytes = base64.b64decode(data["data"])
                return [self._convert_output(image_bytes, output_format)]

            else:
                # Render all slides
                response = self._client.post(
                    f"{self.base_url}/render",
                    params={"dpi": self.dpi, "format": "png"},
                    files={"file": (filename, content, mime_type)},
                )
                response.raise_for_status()
                data = response.json()

                results = []
                for slide in data["slides"]:
                    image_bytes = base64.b64decode(slide["data"])
                    results.append(self._convert_output(image_bytes, output_format))

                return results

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"LibreServer error: {e.response.text}") from e
        except httpx.RequestError as e:
            raise RuntimeError(f"Connection error: {e}") from e

    def health_check(self) -> bool:
        """
        Check if LibreServer is healthy.

        Returns:
            True if server is healthy and LibreOffice is connected
        """
        try:
            response = self._client.get(f"{self.base_url}/health")
            response.raise_for_status()
            data = response.json()
            return data.get("status") == "healthy"
        except Exception:
            return False
