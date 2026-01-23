# Render Perception Loop — Terminology

## Core Concepts

| Term | Definition |
|------|------------|
| **artifact** | The source material that gets rendered (PPTX, HTML, LaTeX, etc.). This is what the Artifact Editor LLM modifies. |
| **visual** | The rendered output — an image, screenshot, or PNG. What the Vision LLM sees. |
| **analysis_prompt** | Domain-specific criteria for evaluating the visual. Tells the Vision LLM what to look for. |
| **context** | Surrounding/situational information provided to the Vision LLM (previous pages, brand guidelines, document metadata). |

---

## Components

| Term | Definition |
|------|------------|
| **Visual Analyzer** | Component that handles render → perceive. Takes artifact + analysis_prompt, outputs AnalysisResult. |
| **Artifact Editor LLM** | LLM that fixes the artifact based on analysis feedback. Takes artifact + AnalysisResult + (optionally) visual, outputs fixed artifact. |
| **RenderPerceptionService (RePeSe)** | The main service that orchestrates the loop. Composes Visual Analyzer and Artifact Editor LLM. |
| **RenderToVisualPort** | Port (interface) for rendering artifact to visual. Adapters: PuppeteerAdapter, LibreOfficeAdapter, etc. |

---

## Models

| Term | Definition |
|------|------------|
| **AnalysisResult** | Structured output from perception. Contains observations, issues, satisfied flag, confidence score. |
| **output_schema** | Pydantic model defining the structure of AnalysisResult. Application-specific. |

---

## Service API

| Term | Definition |
|------|------------|
| **repe_service** | Instance of RenderPerceptionService. |
| **repe_result** | Return value from `iterate()` or `analyze()`. |
| **analyze()** | Single-shot method: render → perceive. No loop. |
| **iterate()** | Full loop method: render → perceive → reason → apply → repeat. Requires reasoner. |
| **analyze_rolling()** | Rolling window analysis for large visual sets. |

---

## Loop Control

| Term | Definition |
|------|------------|
| **artifact_editor** | LLM that fixes the artifact. Optional — if not provided, caller owns the loop and editing. |
| **satisfied** | Boolean flag indicating the visual meets criteria. Termination signal. |
| **max_iterations** | Safety ceiling to prevent infinite loops. |
| **stop_condition** | Callback function that defines custom termination logic. |

---

## Multi-Visual

| Term | Definition |
|------|------------|
| **rolling window** | Technique for analyzing many visuals by processing them in overlapping batches with accumulated context. |
| **window_size** | How many visuals per batch in rolling window analysis. |
| **step** | How many visuals to advance between windows. Overlap = window_size - step. |
| **context_accumulator** | Function that summarizes previous window analyses into context for the next window. |

---

## Flow Summary

```
artifact → [render] → visual → [perceive] → AnalysisResult
                                                   │
                                                   ▼
                                          ┌─────────────────┐
                                          │ Artifact Editor LLM │ ← artifact + visual (optional)
                                          │      (LLM)      │
                                          └────────┬────────┘
                                                   │
                                                   ▼
                                            fixed artifact
                                                   │
                         ┌─────────────────────────┘
                         ▼
            loop until satisfied
```

---

## Naming Conventions

| Variable | Type |
|----------|------|
| `repe_service` | RenderPerceptionService |
| `repe_result` | IterationResult / AnalysisResult |
| `artifact` | The source being edited |
| `visual` | Rendered image |
| `analysis_prompt` | Perception criteria |
| `context` | Surrounding information |
