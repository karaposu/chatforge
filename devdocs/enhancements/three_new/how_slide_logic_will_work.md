# How Slide Logic Will Work

## Overview

The three services work together in an iterative loop to create and refine presentation slides.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Domain App                                │
│                                                                  │
│    ┌──────────┐      ┌────────────┐      ┌──────────────┐       │
│    │  Render  │ ───► │ Perception │ ───► │ Editor Agent │       │
│    │ Service  │      │  Service   │      │   Service    │       │
│    └──────────┘      └────────────┘      └──────────────┘       │
│         │                  │                    │                │
│         │                  │                    │                │
│         ▼                  ▼                    ▼                │
│      images            analysis            modified              │
│                                            artifact              │
│                                                │                 │
│                        ◄────────────────────────                 │
│                         (loop until satisfied)                   │
└─────────────────────────────────────────────────────────────────┘
```

## The Loop

### Step 1: Render

Convert the current artifact (PPTX) into visual images.

```python
images = render_adapter.render(artifact)
# Returns: [slide_0.png, slide_1.png, ...]
```

### Step 2: Perceive

Analyze the rendered images for issues.

```python
analysis = perception_service.analyze(
    images=images,
    prompt="""
    Check each slide for:
    - Text overflow or cutoff
    - Overlapping elements
    - Poor alignment
    - Readability issues
    - Visual balance
    """
)
```

### Step 3: Decide

If satisfied, exit the loop.

```python
if analysis.satisfied:
    return artifact  # Done!
```

### Step 4: Edit

Pass feedback to the editor agent. The agent interprets the issues and makes fixes.

```python
artifact = editor_agent.edit(
    artifact=artifact,
    instructions=f"Fix these issues:\n{analysis.summary}\n\nDetails:\n{format_issues(analysis.issues)}"
)
```

The agent autonomously:
- Reads the feedback
- Decides what edits to make
- Calls adapter tools to apply changes
- Returns the modified artifact

### Step 5: Loop

Go back to Step 1 with the modified artifact.

---

## Complete Flow Example

```python
def iteratively_improve_slides(
    initial_artifact: bytes,
    analysis_prompt: str,
    max_iterations: int = 5
) -> bytes:
    """
    Iteratively improve a presentation until it meets quality criteria.
    """
    artifact = initial_artifact

    for iteration in range(max_iterations):
        # 1. Render
        images = render_adapter.render(artifact)

        # 2. Perceive
        analysis = perception_service.analyze(images, analysis_prompt)

        # 3. Check if done
        if analysis.satisfied:
            print(f"Satisfied after {iteration + 1} iterations")
            return artifact

        # 4. Edit (agent figures out what to do)
        artifact = editor_agent.edit(
            artifact=artifact,
            instructions=f"Fix these issues: {analysis.summary}"
        )

    print(f"Max iterations reached")
    return artifact
```

---

## Concrete Slide Example

### Initial State
- Slide has title "Project Timeline Presentation"
- Title is too long and overflows the text box

### Iteration 1

**Render:** Generate PNG of slide

**Perceive:**
```
Analysis:
- satisfied: false
- issues:
  - slide: 0, shape: 3
    problem: "Title text overflows container"
    suggestion: "Reduce font size or shorten text"
```

**Edit:** Agent receives feedback and acts

```
Agent thinks: Title is overflowing, I should reduce font size
Agent calls: edit_style(slide=0, shape=3, font_size=32)
Agent: Done
```

### Iteration 2

**Render:** Generate PNG of modified slide

**Perceive:**
```
Analysis:
- satisfied: true
- issues: []
- summary: "All slides meet quality criteria"
```

**Done!**

---

## Service Independence

Each service is independent and composable:

| Service | Input | Output | Knows About |
|---------|-------|--------|-------------|
| ArtifactRenderPort (adapter) | artifact | images | Nothing else |
| PerceptionService | images + prompt | analysis | Nothing else |
| ArtifactEditorAgentService | artifact + instructions | modified artifact | Has adapter tools |

The **domain app** orchestrates them. The services don't know about each other.

---

## Benefits

1. **Testable** - Each service can be tested in isolation
2. **Swappable** - Can use different backends (LibreOffice vs direct XML)
3. **Reusable** - PerceptionService works for any images, not just slides
4. **Debuggable** - Can inspect state between each step
5. **Flexible** - Domain app controls the loop logic, iterations, exit conditions
6. **Agentic** - Editor agent handles complexity of translating feedback to actions
