#cool now in devdocs/enhancements/libreofficeadapter create step_by_step_impl_plan.md    

# LibreOffice Adapter

An adapter that implements `RenderToVisualPort` using LibreOffice to convert office documents to visual formats.

---

## What It Is

LibreOffice is an open-source office suite that can run in **headless mode** (no GUI) and convert documents via command line. This adapter wraps LibreOffice's conversion capabilities to render artifacts like PPTX, DOCX, ODP to images.

```
artifact (PPTX) → LibreOfficeAdapter → visual (PNG per slide)
```

---

## Why LibreOffice?

| Feature | Benefit |
|---------|---------|
| **Headless mode** | Runs on servers without display |
| **Wide format support** | PPTX, DOCX, ODP, ODS, ODT, PDF, etc. |
| **High fidelity** | Renders documents as users would see them |
| **Free & open source** | No licensing costs |
| **Cross-platform** | Linux, macOS, Windows |

---

## Supported Formats

### Input Artifacts

| Format | Description |
|--------|-------------|
| `.pptx` | Microsoft PowerPoint |
| `.odp` | LibreOffice Impress |
| `.docx` | Microsoft Word |
| `.odt` | LibreOffice Writer |
| `.xlsx` | Microsoft Excel |
| `.ods` | LibreOffice Calc |
| `.pdf` | PDF documents |

### Output Visuals

| Format | Use Case |
|--------|----------|
| `PNG` | Individual slides/pages as images |
| `PDF` | Full document (then convert pages to images) |
| `JPEG` | Compressed images |
| `SVG` | Vector graphics (where supported) |

---

## Core Capabilities

### 1. Slide/Page Extraction

Convert multi-page documents to individual images:

```python
adapter = LibreOfficeAdapter()

# Input: PPTX with 10 slides
# Output: List of 10 PNG images
visuals = await adapter.render(artifact=my_pptx)

# visuals[0] = slide 1 as PNG
# visuals[1] = slide 2 as PNG
# ...
```

### 2. Specific Page Selection

Render only specific pages/slides:

```python
# Render only slides 3, 5, 7
visuals = await adapter.render(
    artifact=my_pptx,
    pages=[3, 5, 7]
)
```

### 3. Resolution Control

Control output image quality:

```python
visuals = await adapter.render(
    artifact=my_pptx,
    dpi=300,  # High resolution for detailed analysis
)
```

### 4. Format Conversion

Convert between document formats:

```python
# PPTX → PDF → PNG (sometimes better fidelity)
pdf = await adapter.to_pdf(artifact=my_pptx)
visuals = await adapter.pdf_to_images(pdf)
```

---

## Implementation Approach

### Option 1: Direct CLI

Use LibreOffice's command-line interface:

```bash
# Convert PPTX to PNG
libreoffice --headless --convert-to png --outdir ./output presentation.pptx
```

```python
class LibreOfficeAdapter:
    async def render(self, artifact: Path) -> list[bytes]:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Run LibreOffice conversion
            await asyncio.create_subprocess_exec(
                "libreoffice",
                "--headless",
                "--convert-to", "png",
                "--outdir", tmpdir,
                str(artifact)
            )
            # Collect output images
            return [open(f, "rb").read() for f in sorted(Path(tmpdir).glob("*.png"))]
```

### Option 2: UNO API

Use LibreOffice's Python UNO bridge for more control:

```python
import uno
from com.sun.star.beans import PropertyValue

# More control over rendering options
# But more complex setup
```

**Recommendation:** Start with CLI approach (simpler), upgrade to UNO if needed.

---

## Interface

Implements `RenderToVisualPort`:

```python
from chatforge.ports.render_to_visual import RenderToVisualPort

class LibreOfficeAdapter(RenderToVisualPort):
    """Renders office documents to images using LibreOffice."""

    def __init__(
        self,
        libreoffice_path: str = "libreoffice",  # or soffice
        default_dpi: int = 150,
        default_format: str = "png",
    ):
        self.libreoffice_path = libreoffice_path
        self.default_dpi = default_dpi
        self.default_format = default_format

    async def render(
        self,
        artifact: Path | bytes,
        pages: list[int] | None = None,
        dpi: int | None = None,
        format: str | None = None,
    ) -> list[bytes]:
        """
        Render artifact to list of images.

        Args:
            artifact: Path to document or document bytes
            pages: Specific pages to render (1-indexed), None = all
            dpi: Resolution (default: 150)
            format: Output format (default: png)

        Returns:
            List of image bytes, one per page/slide
        """
        ...
```

---

## Considerations

### Performance

| Concern | Mitigation |
|---------|------------|
| Startup time | Keep LibreOffice instance running (connection pooling) |
| Large documents | Stream pages, render on-demand |
| Concurrent requests | Queue or pool LibreOffice processes |

### Reliability

| Concern | Mitigation |
|---------|------------|
| LibreOffice crashes | Timeout + retry logic |
| Corrupted documents | Validate input, graceful error handling |
| Missing fonts | Bundle common fonts, or specify font directory |

### Dependencies

- LibreOffice installed on system
- For Docker: use LibreOffice-enabled base image
- Consider: `libreoffice-headless` package (smaller footprint)

---

## Docker Setup

```dockerfile
FROM python:3.11-slim

# Install LibreOffice headless
RUN apt-get update && apt-get install -y \
    libreoffice-headless \
    libreoffice-writer \
    libreoffice-impress \
    libreoffice-calc \
    && rm -rf /var/lib/apt/lists/*

# Common fonts
RUN apt-get update && apt-get install -y \
    fonts-liberation \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*
```

---

## Usage with RenderPerceptionService

```python
from chatforge.adapters.render_to_visual.libreoffice import LibreOfficeAdapter
from chatforge.services.render_perception import RenderPerceptionService

# Create adapter
lo_adapter = LibreOfficeAdapter(dpi=200)

# Create service with adapter
repe_service = RenderPerceptionService(
    renderer=lo_adapter,
    vision_llm=my_vision_model,
    artifact_editor_llm=my_editor_model,
)

# Analyze a presentation
repe_result = await repe_service.analyze(
    artifact=Path("presentation.pptx"),
    analysis_prompt="Check slide alignment, font consistency, and brand colors",
)
```

---

## Status

**Not implemented** — design stage.

---

## Next Steps

1. Implement basic CLI wrapper
2. Add page selection support
3. Add resolution control
4. Add connection pooling for performance
5. Write tests with sample documents
