## Render Perception Loop

**A generic agentic pattern where an AI perceives and analyzes rendered visual output against defined criteria.**

---

### The Problem

Most automated pipelines that generate or edit visual content are **blind**. They modify code, data, or documents without ever seeing the result. They operate on structure alone — hoping the output looks right.

This is like editing a photo with your eyes closed.

---

### The Solution

The Render Perception Loop gives your system **semantic eyes**. By rendering output and feeding it to a vision-capable AI, your pipeline can:

- **See** what it produces
- **Understand** what's wrong
- **Iterate** until it's right

This transforms blind generation into a sighted feedback loop.

---

### Use Cases

| Use Case | What It Enables |
|----------|-----------------|
| **Iterative fixing** | Detect visual bugs, fix, re-render, verify |
| **Quality control** | Validate outputs against brand/design rules |
| **Enhancement** | "Make this look better" with visual feedback |
| **Analysis** | Extract meaning from rendered output |
| **Comparison** | Diff visual output against reference |
| **Accessibility audit** | Check contrast, readability, layout |

---

### Definition

The Render Perception Loop takes arbitrarily renderable input, renders it to a visual format (e.g., PNG), and feeds both the visual output and (optionally) the underlying structure to an AI agent — along with seed prompts that define evaluation criteria. The agent produces a text-based analysis describing what it observes.

---

### Flow

```
Seed Prompts ─────────────────────────┐
                                      │
Input ─────▶ Renderer ──▶ Visual ─────┼──▶ Agent ──▶ Text Analysis
    │                                 │
    └──▶ Structure (optional) ────────┘
```

---

### Inputs

| Input | Description |
|-------|-------------|
| **Renderable Input** | Anything that can be rendered — documents, code, data, scenes, UI state, etc. |
| **Renderer** | Converts input to visual (LibreOffice, Puppeteer, game engine, etc.) |
| **Structure** *(optional)* | Underlying data (XML, AST, DOM, JSON, source code) — helps agent understand what can be changed |
| **Seed Prompts** | Criteria for evaluation (rules, guidelines, goals) |

---

### Output

**Text Analysis** — observations, issues, scores, descriptions, or any structured understanding of the rendered output.

---

### Examples of Renderable Input

| Input | Renderer | Visual |
|-------|----------|--------|
| PPTX | LibreOffice | PNGs |
| HTML/CSS | Puppeteer | Screenshot |
| React component | Browser | Screenshot |
| LaTeX | pdflatex | PDF/PNG |
| 3D scene | Blender/Unity | Rendered frame |
| Game state | Game engine | Screenshot |
| Chart data | D3/matplotlib | Chart image |

