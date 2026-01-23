# RenderPerceptionService - High Level Design

## Overview

A generic service that enables AI systems to "see" rendered output and iteratively improve it.

---

## Core Features

### 1. Pluggable Renderers

The service should support multiple render backends via `RenderToVisualPort`:

- User provides their own adapter (Puppeteer, LibreOffice, custom)
- Service doesn't care how rendering happens
- Adapter just needs to: `data → visual (image/bytes)`

### 2. Configurable Perception

The Vision LLM step should be configurable:

- **Seed prompts** - criteria for evaluation (what to look for)
- **Output schema** - structured analysis result (Pydantic model)
- **Vision model** - which model to use (gpt-4o, claude, etc.)

### 3. Pluggable Reasoning

The reasoning step (Analysis → Changes) should be pluggable via `ReasoningPort`:

```
┌─────────────────────────────────────────┐
│           ReasoningPort                 │
│  (how to turn analysis into changes)    │
└─────────────────────────────────────────┘
          │
          ├── SimpleLLMReasoner      (one-shot, fast)
          │
          └── ReactAgentReasoner     (multi-step, tools)
```

**SimpleLLMReasoner:**
- One LLM call: analysis → proposed changes
- Fast, predictable
- Good for simple modifications
- Returns structured change instructions

**ReactAgentReasoner:**
- Multi-step agent with tools
- Can plan, edit files, run code, verify
- More powerful but slower
- Can apply changes directly via tools

### 4. Loop Control

The service should support different loop control options:

- **Max iterations** - stop after N attempts
- **Satisfaction check** - stop when criteria met (callback)
- **Require approval** - pause for human review before applying changes
- **Timeout** - stop after duration

Note: Human approval is a **loop control gate**, not a reasoning strategy. It happens *after* reasoning produces proposed changes:

```
Analysis → Reasoner → Proposed Changes → [Approval Gate?] → Apply
```

### 5. State Management

Track state across iterations:

- History of analyses
- History of changes applied
- Diff between iterations
- Convergence detection (are we making progress?)

---

## Modes of Operation

### Mode 1: Single Shot (No Loop)

Just render and analyze once. Return observations.

```
DATA → Render → Visual → Vision LLM → Analysis (done)
```

Use case: Quality check, audit, extract info from visual

### Mode 2: Iterative Loop

Full loop until satisfied or max iterations.

```
DATA → Render → Perceive → Reason → Apply Changes → (repeat)
```

Use case: Iterative fixing, enhancement, optimization

### Mode 3: Human-in-the-Loop

Pause after analysis for human approval before applying changes.

```
DATA → Render → Perceive → Reason → [HUMAN APPROVAL] → Apply Changes → (repeat)
```

Use case: Sensitive changes, learning/training, high-stakes outputs

---

## API Sketch

```python
class RenderPerceptionService:
    def __init__(
        self,
        renderer: RenderToVisualPort,
        reasoner: ReasoningPort,
        vision_llm: BaseChatModel,
    ):
        ...

    async def analyze(
        self,
        data: Any,
        perception_prompts: str | list[str],
        output_schema: type[BaseModel] | None = None,
    ) -> AnalysisResult:
        """Single shot: render and analyze once. No reasoning, no loop."""
        ...

    async def iterate(
        self,
        data: Any,
        perception_prompts: str | list[str],
        max_iterations: int = 5,
        stop_condition: Callable[[AnalysisResult], bool] | None = None,
        require_approval: bool = False,
    ) -> IterationResult:
        """Full loop: render, perceive, reason, apply, repeat."""
        ...


# Reasoning Port implementations
class SimpleLLMReasoner(ReasoningPort):
    def __init__(self, llm: BaseChatModel, prompts: str | list[str]):
        ...

    async def reason(self, analysis: AnalysisResult, data: Any) -> ProposedChanges:
        """One-shot LLM call to produce change instructions."""
        ...


class ReactAgentReasoner(ReasoningPort):
    def __init__(self, agent: Agent, tools: list[Tool]):
        ...

    async def reason(self, analysis: AnalysisResult, data: Any) -> ProposedChanges:
        """Multi-step agent that can plan and apply changes."""
        ...
```

---

## Open Questions

1. **Change application** - Who applies changes? Service or caller?
   - Option A: Service applies changes (needs to know data format)
   - Option B: Service returns changes, caller applies (more generic)

2. **Data format** - How generic should data be?
   - Option A: `Any` - fully generic, caller handles everything
   - Option B: `DataPort` - abstract interface for modifiable data

3. **Rendering scope** - Full render or incremental?
   - Some renderers support partial re-render (faster)
   - Should service support this?

4. **Multi-visual** - One visual or multiple?
   - Some outputs have multiple pages/frames
   - Analyze all? Sample? User choice?

5. **Diff visualization** - Show before/after?
   - Useful for debugging and human review
   - Add visual diff capability?

---

## Dependencies

| Dependency | Purpose |
|------------|---------|
| `RenderToVisualPort` | Adapter for rendering data to visual |
| `ReasoningPort` | Adapter for turning analysis into changes |
| `get_llm()` | LLM factory for vision model |
| Pydantic models | Structured output schemas |

---

## Status

**Not implemented** - high-level design stage.
