"""
LibreOffice Docker Server Editor Adapter

Adapter for editing artifacts using LibreServer Docker container.
"""

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import httpx


@dataclass
class ShapeInfo:
    """Information about a shape in a slide."""
    index: int
    type: str
    name: Optional[str]
    text: Optional[str]
    position: dict
    size: dict


@dataclass
class SlideInfo:
    """Information about a slide."""
    index: int
    shape_count: int
    shapes: list[ShapeInfo]


@dataclass
class ArtifactInfo:
    """Information about an artifact (presentation)."""
    filename: str
    slide_count: int
    slides: list[SlideInfo]


class LibreOfficeEditorDockerServerAdapter:
    """
    Adapter for editing artifacts using LibreServer Docker container.

    Provides methods to read and modify PPTX files via HTTP API.
    These methods are used as tools by ArtifactEditorAgentService.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: float = 60.0,
    ):
        """
        Initialize the adapter.

        Args:
            base_url: URL of the LibreServer instance
            timeout: HTTP request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)
        self._current_artifact: Optional[bytes] = None

    def __del__(self):
        if hasattr(self, "_client"):
            self._client.close()

    def _prepare_artifact(
        self, artifact: Union[bytes, str, Path]
    ) -> tuple[str, bytes]:
        """Prepare artifact for upload."""
        if isinstance(artifact, (str, Path)):
            path = Path(artifact)
            if not path.exists():
                raise FileNotFoundError(f"Artifact not found: {path}")
            return path.name, path.read_bytes()
        else:
            return "document.pptx", artifact

    def _make_request(
        self,
        endpoint: str,
        artifact: Union[bytes, str, Path],
        data: Optional[dict] = None,
    ) -> dict:
        """Make a request to LibreServer."""
        filename, content = self._prepare_artifact(artifact)
        mime_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

        response = self._client.post(
            f"{self.base_url}{endpoint}",
            data=data or {},
            files={"file": (filename, content, mime_type)},
        )
        response.raise_for_status()
        return response.json()

    def get_info(self, artifact: Union[bytes, str, Path]) -> ArtifactInfo:
        """
        Get artifact structure (slides, shapes, text content).

        Args:
            artifact: Source file as bytes, file path, or Path object

        Returns:
            ArtifactInfo with slides and shapes
        """
        data = self._make_request("/info", artifact)

        slides = []
        for slide_data in data["slides"]:
            shapes = [
                ShapeInfo(
                    index=s["index"],
                    type=s["type"],
                    name=s.get("name"),
                    text=s.get("text"),
                    position=s["position"],
                    size=s["size"],
                )
                for s in slide_data["shapes"]
            ]
            slides.append(SlideInfo(
                index=slide_data["index"],
                shape_count=slide_data["shape_count"],
                shapes=shapes,
            ))

        return ArtifactInfo(
            filename=data["filename"],
            slide_count=data["slide_count"],
            slides=slides,
        )

    def edit_text(
        self,
        artifact: Union[bytes, str, Path],
        slide_index: int,
        shape_index: int,
        new_text: str,
    ) -> bytes:
        """
        Edit text content of a shape.

        Args:
            artifact: Source artifact
            slide_index: Slide index (0-based)
            shape_index: Shape index (0-based)
            new_text: New text content

        Returns:
            Modified artifact as bytes
        """
        data = self._make_request(
            "/edit/text",
            artifact,
            {
                "slide_index": slide_index,
                "shape_index": shape_index,
                "new_text": new_text,
            },
        )
        return base64.b64decode(data["document"])

    def edit_style(
        self,
        artifact: Union[bytes, str, Path],
        slide_index: int,
        shape_index: int,
        font_name: Optional[str] = None,
        font_size: Optional[float] = None,
        font_color: Optional[str] = None,
    ) -> bytes:
        """
        Edit text style of a shape.

        Args:
            artifact: Source artifact
            slide_index: Slide index (0-based)
            shape_index: Shape index (0-based)
            font_name: Font family (e.g., "Arial")
            font_size: Font size in points
            font_color: Hex color (e.g., "FF0000" for red)

        Returns:
            Modified artifact as bytes
        """
        form_data = {
            "slide_index": slide_index,
            "shape_index": shape_index,
        }
        if font_name is not None:
            form_data["font_name"] = font_name
        if font_size is not None:
            form_data["font_size"] = font_size
        if font_color is not None:
            form_data["color"] = font_color

        data = self._make_request("/edit/style", artifact, form_data)
        return base64.b64decode(data["document"])

    def edit_position(
        self,
        artifact: Union[bytes, str, Path],
        slide_index: int,
        shape_index: int,
        x: int,
        y: int,
    ) -> bytes:
        """
        Move a shape to a new position.

        Args:
            artifact: Source artifact
            slide_index: Slide index (0-based)
            shape_index: Shape index (0-based)
            x: X position in 1/100mm
            y: Y position in 1/100mm

        Returns:
            Modified artifact as bytes
        """
        data = self._make_request(
            "/edit/position",
            artifact,
            {
                "slide_index": slide_index,
                "shape_index": shape_index,
                "x": x,
                "y": y,
            },
        )
        return base64.b64decode(data["document"])

    def edit_size(
        self,
        artifact: Union[bytes, str, Path],
        slide_index: int,
        shape_index: int,
        width: int,
        height: int,
    ) -> bytes:
        """
        Resize a shape.

        Args:
            artifact: Source artifact
            slide_index: Slide index (0-based)
            shape_index: Shape index (0-based)
            width: Width in 1/100mm
            height: Height in 1/100mm

        Returns:
            Modified artifact as bytes
        """
        data = self._make_request(
            "/edit/size",
            artifact,
            {
                "slide_index": slide_index,
                "shape_index": shape_index,
                "width": width,
                "height": height,
            },
        )
        return base64.b64decode(data["document"])

    def create_textbox(
        self,
        artifact: Union[bytes, str, Path],
        slide_index: int,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str = "",
        font_name: Optional[str] = None,
        font_size: Optional[float] = None,
        font_color: Optional[str] = None,
    ) -> bytes:
        """
        Create a new textbox on a slide.

        Args:
            artifact: Source artifact
            slide_index: Slide index (0-based)
            x, y: Position in 1/100mm
            width, height: Size in 1/100mm
            text: Initial text content
            font_name, font_size, font_color: Optional styling

        Returns:
            Modified artifact as bytes
        """
        form_data = {
            "slide_index": slide_index,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "text": text,
        }
        if font_name is not None:
            form_data["font_name"] = font_name
        if font_size is not None:
            form_data["font_size"] = font_size
        if font_color is not None:
            form_data["font_color"] = font_color

        data = self._make_request("/create/textbox", artifact, form_data)
        return base64.b64decode(data["document"])

    def create_shape(
        self,
        artifact: Union[bytes, str, Path],
        slide_index: int,
        shape_type: str,
        x: int,
        y: int,
        width: int,
        height: int,
        fill_color: Optional[str] = None,
        line_color: Optional[str] = None,
    ) -> bytes:
        """
        Create a new shape on a slide.

        Args:
            artifact: Source artifact
            slide_index: Slide index (0-based)
            shape_type: "rectangle", "ellipse", "line", "connector"
            x, y: Position in 1/100mm
            width, height: Size in 1/100mm
            fill_color: Fill color as hex
            line_color: Line color as hex

        Returns:
            Modified artifact as bytes
        """
        form_data = {
            "slide_index": slide_index,
            "shape_type": shape_type,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
        }
        if fill_color is not None:
            form_data["fill_color"] = fill_color
        if line_color is not None:
            form_data["line_color"] = line_color

        data = self._make_request("/create/shape", artifact, form_data)
        return base64.b64decode(data["document"])
