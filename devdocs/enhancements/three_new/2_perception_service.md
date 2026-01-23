# Perception Service

## Purpose

Analyzes visual images and extracts semantic understanding.

## Responsibility

**Single job:** images + prompt → analysis

Takes images and an analysis prompt, uses a Vision LLM to understand what's in the images, and returns structured feedback. Can optionally compare against reference images.

## Interface

```python
@dataclass
class Reference:
    """A reference image with optional description."""
    image: bytes
    text: Optional[str] = None  # What this reference represents

class PerceptionService:
    def analyze(
        self,
        images: list[bytes],
        prompt: str,
        references: Optional[list[Reference]] = None,
    ) -> AnalysisResult:
        """
        Analyze images using Vision LLM.

        Args:
            images: Target images to analyze
            prompt: What to look for / analyze
            references: Optional reference images to compare against,
                        each with optional description text

        Returns:
            Structured analysis result
        """
        ...
```

## What It Does

- Accepts images (from any source)
- Sends them to Vision LLM with the analysis prompt
- Returns structured feedback about what it sees
- Can analyze for specific criteria (design, errors, layout, etc.)

## What It Does NOT Do

- Render or produce images
- Edit anything
- Know where the images came from

## Analysis Result

```python
@dataclass
class AnalysisResult:
    satisfied: bool          # Are all criteria met?
    issues: list[Issue]      # Problems found
    summary: str             # Human-readable summary
```

## Example Prompts

- "Check if text is readable and not cut off"
- "Verify color contrast meets accessibility standards"
- "Identify any overlapping elements"
- "Assess overall visual balance and alignment"

## Usage

```python
perception = PerceptionService(vision_llm=claude_vision)

# Simple analysis (no references)
result = perception.analyze(
    images=slide_images,
    prompt="Check for text overflow, alignment issues, and readability"
)

# Analysis with reference images
result = perception.analyze(
    images=slide_images,
    prompt="Check if slides match the brand guidelines and mockup design",
    references=[
        Reference(image=brand_guide_png, text="Brand color and font guidelines"),
        Reference(image=mockup_png, text="Original mockup to match"),
        Reference(image=good_slide_png, text="Example of a well-designed slide"),
    ]
)

if not result.satisfied:
    for issue in result.issues:
        print(f"Slide {issue.location}: {issue.description}")
```
