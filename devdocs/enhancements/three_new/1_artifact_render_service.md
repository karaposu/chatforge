# Artifact Render Service

## Purpose

Converts artifacts into visual representations (images).

## Responsibility

**Single job:** artifact → images

Takes a source artifact (PPTX, HTML, JS, PDF, etc.) and produces visual output that represents how the artifact would appear when rendered.

## Interface

```python
from typing import Protocol, Optional, Union, Literal
from pathlib import Path
from PIL import Image

ImageFormat = Literal["bytes", "base64", "pil"]

class ArtifactRenderPort(Protocol):
    def render(
        self,
        artifact: Union[bytes, str, Path],
        page: Optional[int] = None,
        output_format: ImageFormat = "bytes"
    ) -> Union[list[bytes], list[str], list[Image.Image]]:
        """
        Render artifact to images.

        Args:
            artifact: Source file as bytes, file path string, or Path object
            page: Optional specific page/slide index to render.
                  If None, renders all pages/slides.
            output_format: Output format for images:
                - "bytes": Raw image bytes (default)
                - "base64": Base64 encoded string
                - "pil": PIL Image object

        Returns:
            List of images in the specified format.
            If page is specified, returns single-item list.
        """
        ...
```

## What It Does

- Accepts an artifact as bytes (PPTX, HTML, JS, PDF, etc.)
- Optionally renders a specific page/slide
- Converts to visual images in the requested format
- Returns one image per visual unit (slide, page, etc.)
- Handles format-specific rendering logic internally

## What It Does NOT Do

- Analyze or interpret the images
- Edit or modify the artifact
- Make decisions about content

## Adapters

Different adapters for different artifact types:

| Artifact Type | Adapter | Backend |
|---------------|---------|---------|
| PPTX | `LibreOfficeRenderAdapter` | Native LibreOffice UNO |
| PPTX | `LibreOfficeRenderDockerServerAdapter` | LibreServer Docker `/render` |
| HTML | `BrowserRenderAdapter` | Playwright/Puppeteer |
| PDF | `PDFRenderAdapter` | pdf2image / LibreOffice |

## Usage

```python
# Using Docker-based LibreServer
artifact_render_service = ArtifactRenderService(adapter=LibreOfficeRenderDockerServerAdapter())

# Render from file path
images = artifact_render_service.render("presentation.pptx")
# images = [bytes, bytes, ...]

# Render from bytes
images = artifact_render_service.render(pptx_bytes)
# images = [bytes, bytes, ...]

# Render specific slide as base64
images = artifact_render_service.render("presentation.pptx", page=0, output_format="base64")
# images = ["iVBORw0KGgo..."]

# Render as PIL Image for further processing
images = artifact_render_service.render(pptx_bytes, output_format="pil")
# images = [PIL.Image, PIL.Image, ...]
```
