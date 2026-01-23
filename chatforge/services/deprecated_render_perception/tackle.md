# Implementation Approach

## When Render→Perceive Matters

This service is valuable when the **visual output is the source of truth**, not the underlying artifact.

### The Problem

Some data formats only reveal their true form after rendering:

| Data | Render Algorithm | Visual Output |
|------|------------------|---------------|
| HTML/CSS | Browser engine | Webpage |
| PPTX XML | PowerPoint/LibreOffice | Slide |
| LaTeX | TeX compiler | PDF/Document |
| React JSX | React renderer | UI component |
| SVG/Canvas | Graphics engine | Image |

You can't fully understand these by analyzing the source alone:
- CSS interactions cause unexpected layouts
- Font rendering varies
- Overflow, clipping, z-index only visible after render
- Browser quirks and edge cases

### The Insight

When the visual is **constructed via an algorithm** (rendering engine, compiler, layout engine), the artifact is just instructions. The **rendered output is the reality**.

```
Artifact (instructions) → Rendering Algorithm → Visual (reality)
        ↑                                              ↑
    What you write                              What users see
```

Analyzing HTML tells you what you *intended*. Analyzing the screenshot tells you what *actually happened*.

### When to Use This Service

✅ **Good fit:**
- Visual output is the primary deliverable (presentations, webpages, documents)
- Rendering algorithm is non-trivial (layout engines, compilers)
- Visual correctness matters (alignment, consistency, readability)

❌ **Not needed:**
- No rendering step (plain text, JSON data)
- Visual form is trivial/predictable

---

## Unified Service with Optional Orchestration

The `artifact_editor` parameter determines the mode:

```python
# Full loop mode - service orchestrates everything
repe_service = RenderPerceptionService(
    renderer=my_renderer,
    vision_llm=vision_model,
    artifact_editor=my_editor_llm,  # Provided → iterate() available
)

repe_result = await repe_service.iterate(artifact, analysis_prompt, max_iterations=5)
# Inside iterate():
#   1. render: artifact → visual (via RenderToVisualPort)
#   2. perceive: visual + analysis_prompt → AnalysisResult (via Vision LLM)
#   3. check: if satisfied or max_iterations reached → return
#   4. edit: Artifact Editor LLM receives artifact + AnalysisResult + visual → fixed artifact
#   5. goto 1
#
# Output (repe_result):
#   - final_artifact: the artifact after all iterations
#   - iterations: list of each iteration's analysis
#   - total_iterations: how many loops ran
#   - satisfied: whether termination was due to satisfaction (vs max_iterations)
```

```python
# Minimal mode - caller orchestrates
repe_service = RenderPerceptionService(
    renderer=my_renderer,
    vision_llm=vision_model,
    # No artifact_editor → caller owns the loop
)

while not satisfied:
    analysis = await repe_service.analyze(artifact, analysis_prompt)  # render + perceive only
    artifact = await my_editor.fix(artifact, analysis)                # caller edits
```

---

## Available Methods

| Method       | Requires artifact_editor? | What it does                          |
|--------------|---------------------------|---------------------------------------|
| `analyze()`  | No                        | Single shot: render → perceive        |
| `iterate()`  | Yes                       | Full loop: render → perceive → edit → repeat |

Calling `iterate()` without an artifact_editor raises an error.

---

## Why This Design?

**Progressive enhancement** - start simple, upgrade when needed:

1. Use `analyze()` for one-shot perception (quality checks, audits)
2. Add `artifact_editor` when you want the service to run the full loop

**Caller choice** - flexibility vs convenience:

- Want full control? Don't provide artifact_editor, run your own loop
- Want convenience? Provide artifact_editor, call `iterate()`

Both modes share the same render + perceive core. The loop is just optional orchestration on top.

---

## Loop Termination: When to Stop?

The loop needs to know when iteration is "enough". Several mechanisms:

### 1. Max Iterations (Safety Net)

```python
await repe_service.iterate(artifact, analysis_prompt, max_iterations=5)
```

Always have a ceiling. Prevents infinite loops.

### 2. Satisfaction Signal from Analysis

The perception step can include a satisfaction check in the analysis output:

```python
class AnalysisResult(BaseModel):
    issues: list[Issue]
    satisfied: bool  # "Is the output acceptable?"

# Loop stops when: analysis.satisfied == True or no issues found
```

This means the **perception prompt** does double duty:
- Analyze what's wrong
- Determine if we're done

### 3. Explicit Stop Condition (Callback)

```python
await repe_service.iterate(
    artifact,
    analysis_prompt,
    stop_condition=lambda analysis: len(analysis.issues) == 0
)
```

Caller defines what "done" means.

---

## Who Decides Termination?

The **Visual Analyzer** (perceive step) decides termination, not the Artifact Editor LLM.

```
perceive → analysis.satisfied? → if yes, stop → else, Artifact Editor LLM fixes → repeat
```

The Artifact Editor LLM's job is just "given these issues, fix the artifact" — not "should we continue?"

---

## Recommended Design

```python
class AnalysisResult(BaseModel):
    observations: list[str]      # What was seen
    issues: list[Issue]          # What's wrong
    satisfied: bool              # Should we stop?
    confidence: float            # How sure (0-1)

# Default stop condition
def default_stop(analysis: AnalysisResult) -> bool:
    return analysis.satisfied or len(analysis.issues) == 0
```

The perception prompt should always assess satisfaction:

```
"Analyze this rendered output. Identify any issues with [criteria].
Also determine: is the output acceptable? (satisfied: true/false)"
```

This keeps termination logic in the **perceive** step. The Artifact Editor LLM just fixes what's broken.

---

## Multi-Visual Inputs

Some inputs produce multiple visuals (PPTX → many slides, PDF → many pages).

### Two Approaches

| Approach | How it works | Use case |
|----------|--------------|----------|
| **Caller loops** | Pass one visual at a time | Per-page analysis |
| **Pass all together** | Service receives multiple visuals | Holistic/cross-page analysis |

### Per-Visual Analysis (Caller Loops)

```python
for slide in extract_slides(my_pptx):
    repe_result = await repe_service.analyze(
        artifact=slide,
        analysis_prompt="Check alignment...",
        output_schema=SlideAnalysis,
    )
```

Good for: independent page-by-page checks.

### Holistic Analysis (Multiple Visuals)

```python
repe_result = await repe_service.analyze(
    artifact=[slide1, slide2, slide3],  # All together
    analysis_prompt="Check font consistency ACROSS all slides",
    output_schema=DeckAnalysis,
)
# Vision LLM sees all images, can compare
```

Good for: cross-page consistency, overall flow, comparative analysis.

**Recommendation:** Support both. If `artifact` yields multiple visuals, pass all to Vision LLM in one call. Caller decides granularity by what they pass in.

---

## Rolling Window for Large Inputs

Passing 1000 images at once isn't feasible (context limits, cost). But we still need holistic analysis across many visuals.

**Solution:** Rolling window with accumulated context.

### How It Works

```
Images: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, ...]

Window 1: [1, 2, 3, 4, 5]
    → analyze
    → summary₁ (accumulated context)

Window 2: [4, 5, 6, 7, 8]  (overlap for continuity)
    → analyze (with summary₁ as context)
    → summary₂

Window 3: [7, 8, 9, 10]
    → analyze (with summary₂ as context)
    → summary₃

Final: aggregate all window analyses
```

### Parameters

| Parameter | Purpose |
|-----------|---------|
| `window_size` | How many visuals per batch (e.g., 5) |
| `step` | How many to advance (e.g., 3 → overlap of 2) |
| `context_accumulator` | Function to summarize previous windows |

### Context Evolution

```python
# Window 1: no prior context
context = "Document: Annual Report"

# Window 2: prior context accumulated
context = """
Document: Annual Report

Previous analysis (slides 1-5):
- Intro section established blue theme
- Font: Helvetica throughout
- Issue: logo misaligned on slide 3
"""

# Window 3: more accumulated
context = """
Document: Annual Report

Previous analysis (slides 1-8):
- Intro: blue theme, Helvetica
- Data section: charts introduced
- Issues found: logo (slide 3), axis labels (slide 7)
"""
```

### Use Cases

- **Long presentations** — 100+ slide PPTX
- **Video analysis** — frame-by-frame with temporal context
- **Multi-page documents** — lengthy PDF reports
- **Sequential streams** — any ordered visual sequence

### API Sketch

```python
async def analyze_rolling(
    self,
    visuals: list[Any],           # All visuals (or iterator)
    analysis_prompt: str | list[str],
    output_schema: type[BaseModel] | None = None,
    window_size: int = 5,
    step: int = 3,                # Overlap = window_size - step
    base_context: str | None = None,
    context_accumulator: Callable[[str, AnalysisResult], str] | None = None,
) -> RollingAnalysisResult:
    """
    Analyze many visuals using rolling windows.

    Each window is analyzed with accumulated context from previous windows.
    Enables holistic analysis across large visual sets.
    """
    ...

class RollingAnalysisResult(BaseModel):
    window_analyses: list[AnalysisResult]  # Per-window results
    accumulated_context: str               # Final accumulated context
    aggregated_issues: list[Issue]         # All issues across windows
    satisfied: bool                        # Overall satisfaction
```

### Trade-offs

| Aspect | Rolling Window | Pass All Together |
|--------|----------------|-------------------|
| Scale | Handles thousands | Limited by context window |
| Speed | Slower (sequential) | Faster (one call) |
| Cross-visual awareness | Via accumulated context | Full visibility |
| Memory | Low | High |

Rolling window is slower but scales to any size while maintaining holistic awareness through context accumulation.

---

## Surrounding Context

A single visual often needs context to be interpreted correctly:

- Previous/next pages (what came before, what comes after)
- Document metadata (position, purpose)
- External guidelines (brand rules, style guide)

### The Problem

Analyzing slide 5 in isolation:
- Doesn't know it should match slide 1's intro style
- Doesn't know it references a chart from slide 3
- Doesn't know brand guidelines require specific fonts

### The Solution

Add `context` parameter for surrounding/situational information:

```python
repe_result = await repe_service.analyze(
    artifact=slide_5,
    analysis_prompt="Check alignment, consistency with brand and surrounding slides",
    output_schema=SlideAnalysis,
    context="""
    Document: Q4 Quarterly Report
    Position: Slide 5 of 12

    Previous slides:
    - Slide 1: Title slide (Helvetica Bold, blue header)
    - Slides 2-4: Problem statement (bullet format)

    Next slides:
    - Slides 6-10: Solutions
    - Slides 11-12: Summary

    Brand guidelines:
    - Font: Helvetica only
    - Primary color: #0052CC
    - Logo placement: bottom right

    This slide should: Transition from problem to solution
    """
)
```

### What Vision LLM Receives

1. **Visual** — the rendered image
2. **Context** — surrounding/situational text (optional)
3. **Analysis Prompt** — what to evaluate (criteria)

### Updated Method Signature

```python
async def analyze(
    self,
    artifact: Any,
    analysis_prompt: str | list[str],
    output_schema: type[BaseModel] | None = None,
    context: str | None = None,  # Surrounding/situational context
) -> AnalysisResult:
    """
    Single shot: render → perceive.

    Args:
        artifact: Input to render (single item or list for multi-visual)
        analysis_prompt: Evaluation criteria (what to look for)
        output_schema: Pydantic model for structured output
        context: Textual context for interpretation (previous pages, guidelines, etc.)
    """
    ...
```

This allows per-visual analysis with full awareness of the bigger picture.
