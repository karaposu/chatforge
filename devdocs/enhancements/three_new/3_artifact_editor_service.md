# Artifact Editor Agent Service

## Purpose

An LLM Agent that modifies artifacts based on instructions.

## Responsibility

**Single job:** artifact + instructions → modified artifact

An agentic service that interprets edit instructions and uses adapter tools to apply changes.

## Interface

```python
from typing import Union
from pathlib import Path
from langchain_core.language_models import BaseChatModel

class ArtifactEditorAgentService:
    def __init__(
        self,
        llm: BaseChatModel,
        adapter: ArtifactEditorAdapter,  # Agent uses adapter methods as tools
    ):
        ...

    def edit(
        self,
        artifact: Union[bytes, str, Path],
        instructions: str,
    ) -> bytes:
        """
        Apply edits to artifact using LLM agent.

        Args:
            artifact: Original artifact as bytes, file path, or Path object
            instructions: What changes to make (freestyle text)

        Returns:
            Modified artifact bytes
        """
        ...
```

## How It Works

```
instructions (freestyle) → LLM Agent → [calls adapter tools] → modified artifact
```

The LLM Agent:
1. Receives instructions in natural language
2. Interprets what needs to be done
3. Calls adapter methods as tools to make edits
4. Returns the modified artifact

## Agent Tools (from Adapter)

The agent has access to these tools via the adapter:

| Tool | Description |
|------|-------------|
| `edit_text(slide, shape, text)` | Change text content |
| `edit_style(slide, shape, font, size, color)` | Change text styling |
| `edit_position(slide, shape, x, y)` | Move a shape |
| `edit_size(slide, shape, width, height)` | Resize a shape |
| `create_textbox(slide, x, y, w, h, text)` | Add new textbox |
| `create_shape(slide, type, x, y, w, h)` | Add new shape |
| `get_info()` | Get artifact structure (slides, shapes) |

## What It Does

- Interprets freestyle instructions
- Decides which tools to call
- Executes edits via adapter
- Handles multi-step edits autonomously

## What It Does NOT Do

- Decide if edits are needed (caller decides)
- Render or visualize anything
- Analyze content (that's PerceptionService)

## Adapters

| Artifact Type | Adapter | Backend |
|---------------|---------|---------|
| PPTX | `LibreOfficeEditorAdapter` | LibreServer `/edit/*`, `/create/*` |
| PPTX | `DirectXMLEditorAdapter` | Direct XML manipulation |
| HTML | `DOMEditorAdapter` | DOM manipulation |

## Usage

```python
from chatforge.services.llm import get_llm

editor_agent = ArtifactEditorAgentService(
    llm=get_llm(),
    adapter=LibreOfficeEditorAdapter(base_url="http://localhost:8000")
)

# Freestyle instructions - agent figures out what to do
modified_pptx = editor_agent.edit(
    artifact="presentation.pptx",
    instructions="Move the title up by 50px, change font to Arial 24pt, and add a red rectangle in the bottom right corner"
)
```

## Agent Loop Example

For instruction: *"Fix the title overflow and add a subtitle"*

```
Agent thinks: I need to check the current state first
Agent calls: get_info() → sees title at shape 3, text is long

Agent thinks: Title is overflowing, I should reduce font size
Agent calls: edit_style(slide=0, shape=3, font_size=28)

Agent thinks: Now I need to add a subtitle below it
Agent calls: create_textbox(slide=0, x=100, y=200, width=800, height=50, text="Subtitle here")

Agent: Done, returning modified artifact
```
