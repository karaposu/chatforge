# Render Perception Loop Service


A generic agentic pattern where an AI perceives and analyzes rendered visual output against defined criteria.

---

## The Problem

Most automated pipelines that generate or edit visual content are **blind**. They modify code, data, or documents without ever seeing the result. They operate on structure alone — hoping the output looks right.

This is like editing a photo with your eyes closed.

---

## The Solution

The Render Perception Loop gives your system **semantic eyes**. By rendering output and feeding it to a vision-capable AI, your pipeline can:

- **See** what it produces
- **Understand** what's wrong
- **Iterate** until it's right

This transforms blind generation into a sighted feedback loop.



Artifact → Rendering Algorithm → Visual → analysis_prompt → analysis

---

## Use Cases

### 1. Render→Perceive (Artifact to Visual)

When visuals are **constructed via algorithm** (rendering engine, compiler), the artifact is just instructions. The rendered output is the reality.

```
Artifact → Rendering Algorithm → Visual (what users actually see)
```

| Artifact | Render Algorithm | Visual |
|----------|------------------|--------|
| HTML/CSS | Browser engine | Webpage |
| PPTX XML | LibreOffice | Slide |
| LaTeX | TeX compiler | Document |

Analyzing HTML tells you what you *intended*. Analyzing the screenshot tells you what *actually happened*.

### 2. Perceive Only (Direct Visual Input)

When input is already visual, skip the render step:

- **Image analysis** — extract information from photos, diagrams
- **Quality audit** — check uploaded images against criteria
- **Visual comparison** — compare screenshots to reference
- **Screenshot understanding** — parse UI state from captures

For these, use a pass-through renderer or call perceive directly.

---

## Two Core Components

The Render Perception Service (RePeSe) consists of two main components:

1. **Visual Analyzer** - Render artifact to visual, then perceive with Vision LLM
2. **Artifact Editor LLM** - LLM that fixes the artifact based on analysis feedback

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RENDER PERCEPTION LOOP                               │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │                    ┌───────────────────────┐                        │   │
│  │                    │                       │                        │   │
│  │                    │       ARTIFACT        │◄───────────────────┐   │   │
│  │                    │   (source of truth)   │                    │   │   │
│  │                    │                       │                    │   │   │
│  │                    └───────────┬───────────┘                    │   │   │
│  │                                │                                │   │   │
│  │                                ▼                                │   │   │
│  │  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐                 │   │   │
│  │         VISUAL ANALYZER (render)                                │   │   │
│  │  │                                           │                  │   │   │
│  │      ┌───────────────────────────────────┐                      │   │   │
│  │  │   │       RenderToVisualPort          │   │                  │   │   │
│  │      │  (Puppeteer, LibreOffice, etc.)   │                      │   │   │
│  │  │   └───────────────────────────────────┘   │                  │   │   │
│  │                                                                 │   │   │
│  │  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘                 │   │   │
│  │                                │                                │   │   │
│  │                                ▼                                │   │   │
│  │                    ┌───────────────────────┐                    │   │   │
│  │                    │                       │                    │   │   │
│  │                    │    VISUAL OUTPUT      │                    │   │   │
│  │                    │   (PNG, Screenshot)   │                    │   │   │
│  │                    │                       │                    │   │   │
│  │                    └───────────┬───────────┘                    │   │   │
│  │                                │                                │   │   │
│  │                                ▼                                │   │   │
│  │  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐                 │   │   │
│  │        VISUAL ANALYZER (perceive)                               │   │   │
│  │  │                                           │                  │   │   │
│  │      ┌───────────────────────────────────┐        Seed          │   │   │
│  │  │   │         Vision LLM                │◄──┐   Prompts        │   │   │
│  │      │   (analyzes visual + structure)   │   │  (criteria)      │   │   │
│  │  │   └───────────────┬───────────────────┘   │                  │   │   │
│  │                      │                       │                  │   │   │
│  │  │                   ▼                       │                  │   │   │
│  │      ┌───────────────────────────────────┐                      │   │   │
│  │  │   │       Analysis Result             │   │                  │   │   │
│  │      │  (issues, fixes, observations)    │                      │   │   │
│  │  │   └───────────────┬───────────────────┘   │                  │   │   │
│  │                      │                                          │   │   │
│  │  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘                 │   │   │
│  │                      │                                          │   │   │
│  │                      ▼                                          │   │   │
│  │          ┌───────────────────────┐                              │   │   │
│  │          │   Artifact Editor LLM     │──────────────────────────────┘   │   │
│  │          │       (LLM)           │                                  │   │
│  │          └───────────────────────┘                                  │   │
│  │                                                                     │   │
│  │                         LOOP UNTIL SATISFIED                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Summary

| Component | Responsibility | Key Element |
|-----------|----------------|-------------|
| **Visual Analyzer** | Render artifact to visual, analyze with Vision LLM | `RenderToVisualPort` + Vision LLM |
| **Artifact Editor LLM** | Fix the artifact based on analysis feedback | LLM that understands artifact format |

The loop continues until the analysis indicates satisfaction (no issues found, criteria met, etc.).

---

## Architecture

### Components

| Component | Name | Description |
|-----------|------|-------------|
| Service | `RenderPerceptionService` | Orchestrates the loop |
| Port | `RenderToVisualPort` | Abstract interface for renderers |
| Adapters | `PuppeteerAdapter`, `LibreOfficeAdapter`, etc. | Concrete renderer implementations |
| LLM | Vision-capable model via `get_llm()` | Analyzes rendered output |
| Models | `AnalysisResult`, etc. | Pydantic models for structured output |

### Structure

```
chatforge/
├── services/
│   └── render_perception/
│       ├── __init__.py
│       ├── service.py          # RenderPerceptionService
│       └── models.py           # AnalysisResult, etc.
├── ports/
│   └── render_to_visual.py     # RenderToVisualPort protocol
└── adapters/
    └── render_to_visual/
        ├── puppeteer.py        # PuppeteerAdapter
        └── libreoffice.py      # LibreOfficeAdapter
```

---

## Flow

```
                                                       analysis_prompt
                                                         (criteria)
                                                              │
                                                              ▼
┌──────────┐      ┌────────────────────┐      ┌────────┐      ┌────────────┐      ┌──────────┐
│ ARTIFACT │ ───▶ │ RenderToVisualPort │ ───▶ │ Visual │ ───▶ │ Vision LLM │ ───▶ │ Analysis │
└──────────┘      └────────────────────┘      └────────┘      └────────────┘      └──────────┘
     ▲                  (render)               (PNG/img)        (perceive)         (observations)
     │                                                                                   │
     │                                                                                   ▼
     │                                                                          ┌─────────────────┐
     │                                                                          │ Artifact Editor LLM │
     │                                                                          │      (LLM)      │
     │                                                                          └─────────────────┘
     │                                                                                   │
     │          ┌─────────────────┐                                                      │
     └───────── │ fixed artifact  │ ◄────────────────────────────────────────────────────┘
                └─────────────────┘
                      (loop)
```

---

## Inputs

| Input | Description |
|-------|-------------|
| **artifact** | Anything that can be rendered — documents, code, slides, scenes, UI state, etc. |
| **RenderToVisualPort** | Converts artifact to visual (LibreOffice, Puppeteer, game engine, etc.) |
| **analysis_prompt** | Criteria for evaluation (rules, guidelines, goals) |
| **context** *(optional)* | Surrounding/situational information (previous pages, brand guidelines, etc.) |

---

## Output

**Text Analysis** — observations, issues, scores, descriptions, or any structured understanding of the rendered output.

---

## Example Artifacts

| Artifact | Adapter | Visual Output |
|----------|---------|---------------|
| PPTX | LibreOfficeAdapter | PNGs |
| HTML/CSS | PuppeteerAdapter | Screenshot |
| React component | PuppeteerAdapter | Screenshot |
| LaTeX | LatexAdapter | PDF/PNG |
| 3D scene | BlenderAdapter | Rendered frame |
| Chart data | MatplotlibAdapter | Chart image |

---

## Status

**Not implemented** - concept stage.
