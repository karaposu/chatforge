# New Slides Workflow: Complete Guide

## Overview

This document explains how to use the three services together to iteratively improve presentation slides.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│   ┌──────────────┐    ┌─────────────────┐    ┌───────────────┐  │
│   │   Render     │───►│   Perception    │───►│ Editor Agent  │  │
│   │   Adapter    │    │    Service      │    │   Service     │  │
│   └──────────────┘    └─────────────────┘    └───────────────┘  │
│          │                    │                      │          │
│          │                    │                      │          │
│       images              analysis              modified        │
│                                                 artifact        │
│                                                     │           │
│          ◄──────────────────────────────────────────┘           │
│                      (loop until satisfied)                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **LibreServer Docker running:**
   ```bash
   cd devdocs/enhancements/libreofficeadapter/LibreServer
   docker-compose up -d
   ```

2. **Required packages:**
   ```bash
   pip install httpx pillow langchain-anthropic  # or langchain-openai
   ```

---

## Step 1: Initialize Services

```python
from chatforge.adapters import (
    LibreOfficeRenderDockerServerAdapter,
    LibreOfficeEditorDockerServerAdapter,
)
from chatforge.services.perception import PerceptionService
from chatforge.services.artifact_editor_agent import ArtifactEditorAgentService
from chatforge.services.llm import get_llm, get_vision_llm

# Initialize adapters
render_adapter = LibreOfficeRenderDockerServerAdapter(
    base_url="http://localhost:8000",
    dpi=150,
)

editor_adapter = LibreOfficeEditorDockerServerAdapter(
    base_url="http://localhost:8000",
)

# Initialize services
perception_service = PerceptionService(
    vision_llm=get_vision_llm(),
)

editor_agent = ArtifactEditorAgentService(
    llm=get_llm(),
    adapter=editor_adapter,
)
```

---

## Step 2: The Improvement Loop

```python
from chatforge.services.perception import Reference

def improve_slides(
    artifact_path: str,
    analysis_prompt: str,
    max_iterations: int = 5,
    references: list[Reference] = None,
) -> bytes:
    """
    Iteratively improve slides until they meet quality criteria.

    Args:
        artifact_path: Path to the PPTX file
        analysis_prompt: What to check for (quality criteria)
        max_iterations: Maximum improvement cycles
        references: Optional reference images for comparison

    Returns:
        Improved artifact as bytes
    """
    # Load initial artifact
    with open(artifact_path, "rb") as f:
        artifact = f.read()

    for iteration in range(max_iterations):
        print(f"\n=== Iteration {iteration + 1} ===")

        # Step 1: Render
        print("Rendering slides...")
        images = render_adapter.render(artifact, output_format="bytes")
        print(f"  Rendered {len(images)} slides")

        # Step 2: Perceive
        print("Analyzing slides...")
        analysis = perception_service.analyze(
            images=images,
            prompt=analysis_prompt,
            references=references,
        )
        print(f"  Satisfied: {analysis.satisfied}")
        print(f"  Issues: {len(analysis.issues)}")

        # Step 3: Check if done
        if analysis.satisfied:
            print(f"\n✓ All criteria met after {iteration + 1} iterations!")
            return artifact

        # Step 4: Edit
        print("Fixing issues...")
        instructions = format_issues_for_agent(analysis)
        artifact = editor_agent.edit(
            artifact=artifact,
            instructions=instructions,
        )
        print("  Edits applied")

    print(f"\n⚠ Max iterations ({max_iterations}) reached")
    return artifact


def format_issues_for_agent(analysis) -> str:
    """Convert analysis result to instructions for the editor agent."""
    lines = ["Fix the following issues:\n"]

    for issue in analysis.issues:
        lines.append(f"- {issue.location}: {issue.description}")
        if issue.suggestion:
            lines.append(f"  Suggestion: {issue.suggestion}")

    if analysis.summary:
        lines.append(f"\nSummary: {analysis.summary}")

    return "\n".join(lines)
```

---

## Step 3: Usage Examples

### Basic Usage

```python
# Improve slides with basic quality checks
improved = improve_slides(
    artifact_path="presentation.pptx",
    analysis_prompt="""
    Check each slide for:
    - Text overflow or cutoff
    - Overlapping elements
    - Poor alignment
    - Readability issues (font too small, low contrast)
    - Visual balance
    """,
)

# Save result
with open("improved_presentation.pptx", "wb") as f:
    f.write(improved)
```

### With Reference Images

```python
from chatforge.services.perception import Reference

# Load reference images
with open("brand_guidelines.png", "rb") as f:
    brand_guide = f.read()

with open("approved_mockup.png", "rb") as f:
    mockup = f.read()

# Improve with brand comparison
improved = improve_slides(
    artifact_path="presentation.pptx",
    analysis_prompt="""
    Compare slides against the reference images and check:
    - Colors match the brand guidelines
    - Fonts are consistent with the mockup
    - Layout follows the approved design
    - Logo placement is correct
    """,
    references=[
        Reference(image=brand_guide, text="Brand color and font guidelines"),
        Reference(image=mockup, text="Approved mockup design"),
    ],
)
```

### Custom Criteria

```python
# Check specific business requirements
improved = improve_slides(
    artifact_path="quarterly_report.pptx",
    analysis_prompt="""
    Verify each slide meets these requirements:
    - All charts have visible axis labels
    - Numbers are formatted with proper units
    - Company logo appears in bottom right
    - Slide numbers are visible
    - No placeholder text remains
    """,
    max_iterations=3,
)
```

---

## Complete Example Script

```python
#!/usr/bin/env python
"""
Complete example: Iteratively improve a presentation.
"""

from pathlib import Path
from chatforge.adapters import (
    LibreOfficeRenderDockerServerAdapter,
    LibreOfficeEditorDockerServerAdapter,
)
from chatforge.services.perception import PerceptionService, Reference
from chatforge.services.artifact_editor_agent import ArtifactEditorAgentService
from chatforge.services.llm import get_llm, get_vision_llm


def main():
    # --- Setup ---
    render_adapter = LibreOfficeRenderDockerServerAdapter()
    editor_adapter = LibreOfficeEditorDockerServerAdapter()
    perception = PerceptionService(vision_llm=get_vision_llm())
    editor = ArtifactEditorAgentService(llm=get_llm(), adapter=editor_adapter)

    # --- Load artifact ---
    artifact_path = Path("my_presentation.pptx")
    artifact = artifact_path.read_bytes()

    # --- Define quality criteria ---
    analysis_prompt = """
    Check each slide for:
    1. Text overflow - any text cut off or extending beyond its container
    2. Alignment - elements should be properly aligned
    3. Readability - font size at least 18pt, good contrast
    4. Spacing - adequate margins and padding
    5. Consistency - similar elements styled consistently
    """

    # --- Improvement loop ---
    max_iterations = 5

    for i in range(max_iterations):
        print(f"\n{'='*50}")
        print(f"Iteration {i + 1}/{max_iterations}")
        print('='*50)

        # Render
        images = render_adapter.render(artifact)
        print(f"Rendered {len(images)} slides")

        # Analyze
        result = perception.analyze(images, analysis_prompt)

        print(f"Satisfied: {result.satisfied}")
        if result.issues:
            print("Issues found:")
            for issue in result.issues:
                print(f"  - [{issue.severity}] {issue.location}: {issue.description}")

        # Done?
        if result.satisfied:
            print("\n✅ All quality criteria met!")
            break

        # Fix issues
        instructions = "\n".join([
            f"- {issue.location}: {issue.description}"
            for issue in result.issues
        ])

        print(f"\nAsking editor agent to fix {len(result.issues)} issues...")
        artifact = editor.edit(artifact, f"Fix these issues:\n{instructions}")
        print("Edits complete")

    # --- Save result ---
    output_path = Path("improved_presentation.pptx")
    output_path.write_bytes(artifact)
    print(f"\nSaved to: {output_path}")

    # --- Optional: Save final renders for review ---
    final_images = render_adapter.render(artifact)
    for i, img in enumerate(final_images):
        Path(f"final_slide_{i}.png").write_bytes(img)
    print(f"Saved {len(final_images)} final slide images")


if __name__ == "__main__":
    main()
```

---

## How Each Service Contributes

| Step | Service | Input | Output |
|------|---------|-------|--------|
| Render | `LibreOfficeRenderDockerServerAdapter` | PPTX bytes | PNG images |
| Perceive | `PerceptionService` | Images + prompt | Analysis (satisfied, issues) |
| Edit | `ArtifactEditorAgentService` | PPTX + instructions | Modified PPTX |

---

## Tips

1. **Start with clear criteria**: The more specific your analysis prompt, the better the results.

2. **Use references when possible**: Brand guidelines or mockups help ensure consistency.

3. **Limit iterations**: Set a reasonable max (3-5) to avoid infinite loops.

4. **Save intermediate results**: For debugging, save renders after each iteration.

5. **Check the agent's work**: The editor agent logs what changes it makes.

---

## Troubleshooting

### LibreServer not responding
```bash
# Check if Docker is running
docker ps | grep libreserver

# Restart if needed
docker-compose restart
```

### Agent not making expected changes
- Check that the adapter can connect: `adapter.get_info(artifact)`
- Look at agent's tool calls in the response
- Make instructions more specific

### Perception not finding obvious issues
- Increase render DPI for better image quality
- Make analysis prompt more specific
- Check that images are being passed correctly

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                     Your Application                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐  │
│  │ Render Adapter │  │  Perception    │  │ Editor Agent  │  │
│  │                │  │   Service      │  │   Service     │  │
│  │ render()       │  │ analyze()      │  │ edit()        │  │
│  └───────┬────────┘  └───────┬────────┘  └───────┬───────┘  │
│          │                   │                   │          │
└──────────┼───────────────────┼───────────────────┼──────────┘
           │                   │                   │
           ▼                   ▼                   ▼
    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │ LibreServer  │    │  Vision LLM  │    │     LLM      │
    │   Docker     │    │  (Claude/    │    │  + Adapter   │
    │  /render     │    │   GPT-4V)    │    │    Tools     │
    └──────────────┘    └──────────────┘    └──────────────┘
```

The three services are independent and composable. Your application orchestrates them in a loop until the presentation meets your quality criteria.
