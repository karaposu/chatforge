# Multimodal Agent Support

This document explains the current gap in Chatforge's multimodal capabilities and outlines how to add true image+text support to the agent.

---

## Current State: Two-Step Workflow

Chatforge has an `ImageAnalyzer` service that analyzes images separately from the agent:

```
Current Architecture (Two-Step):

Step 1: Pre-process images
┌──────────┐     ┌─────────────────┐     ┌────────────────┐
│  User    │────▶│  ImageAnalyzer  │────▶│  Vision LLM    │
│  uploads │     │  (standalone)   │     │  (GPT-4o)      │
│  image   │     └─────────────────┘     └───────┬────────┘
└──────────┘                                     │
                                                 ▼
                                     ┌───────────────────────┐
                                     │  Text: "I see an      │
                                     │  error dialog with... │
                                     └───────────┬───────────┘
                                                 │
Step 2: Agent uses text context                  │
┌──────────┐     ┌─────────────────┐             │
│  User    │────▶│  ReActAgent     │◀────────────┘
│ question │     │  (text only)    │  Image analysis as context
└──────────┘     └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  Agent response │
                 │  based on text  │
                 └─────────────────┘
```

### How It Works Today

```python
from chatforge.services.vision import ImageAnalyzer, ImageInfo, format_analysis_results
from chatforge.agent import ReActAgent

# Step 1: Analyze images separately
analyzer = ImageAnalyzer(llm=vision_llm)
results = await analyzer.analyze_batch(images)
image_context = format_analysis_results(results)

# Step 2: Pass text context to agent
augmented_message = f"{image_context}\n\nUser question: {user_message}"
response, trace_id = agent.process_message(augmented_message, history)
```

---

## What's Missing

The agent cannot receive images directly. It only accepts text:

```python
# agent/engine.py line 278-316
def _convert_to_messages(self, conversation_history, user_message):
    # ...
    messages.append(HumanMessage(content=content))  # content is str only
```

For true multimodal support, `HumanMessage` needs mixed content:

```python
# True multimodal (NOT currently supported):
HumanMessage(content=[
    {"type": "text", "text": "What's wrong in this screenshot?"},
    {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
])
```

---

## Why It Matters

### 1. Information Loss

Pre-analyzing images loses context. The vision LLM doesn't know what question the user will ask:

```
Two-Step Problem:

User uploads: [screenshot of error]
ImageAnalyzer: "I see a dialog box with a red X icon and text 'Connection failed'"

User asks: "What's the error code?"
Agent: "The image analysis didn't mention an error code..."

→ The analyzer didn't know to look for error codes
```

With true multimodal, the LLM sees the image AND the question together.

### 2. Conversational Context

Users expect to reference images naturally:

```
User: [uploads screenshot] "See this button? How do I make it blue?"
User: "Actually, can you also add rounded corners like in this design?" [uploads another image]
```

Two-step workflow breaks this conversational flow.

### 3. Multi-Image Reasoning

Some tasks require comparing multiple images:

```
User: [image1] [image2] "What changed between these two screenshots?"
```

Pre-analysis treats each image independently. True multimodal lets the LLM reason across images.

### 4. Cost and Latency

Two-step means two LLM calls:
1. Vision LLM for image analysis
2. Agent LLM for response

True multimodal is one call with both image and text.

---

## High-Level Implementation Plan

### Architecture Overview

```
Target Architecture (Single-Step Multimodal):

┌──────────────────┐     ┌─────────────────────────────────┐
│  User sends:     │     │         ReActAgent              │
│  - Text message  │────▶│  ┌─────────────────────────┐   │
│  - Image(s)      │     │  │  HumanMessage(content=[ │   │
└──────────────────┘     │  │    {type: "text", ...}, │   │
                         │  │    {type: "image_url"}  │   │
                         │  │  ])                     │   │
                         │  └────────────┬────────────┘   │
                         │               │                 │
                         │  ┌────────────▼────────────┐   │
                         │  │  Vision-capable LLM     │   │
                         │  │  (GPT-4o, Claude 3.5)   │   │
                         │  └────────────┬────────────┘   │
                         │               │                 │
                         │  ┌────────────▼────────────┐   │
                         │  │  Tools (if needed)      │   │
                         │  └────────────┬────────────┘   │
                         │               │                 │
                         └───────────────┼─────────────────┘
                                         ▼
                              ┌─────────────────┐
                              │  Agent response │
                              └─────────────────┘
```

### Step 1: Extend Message Types

Add multimodal content support to the messaging port:

```python
# ports/messaging.py

@dataclass
class ImageContent:
    """Image content for multimodal messages."""

    data_uri: str  # base64 data URI or URL
    detail: str = "auto"  # "auto" | "low" | "high" for OpenAI


@dataclass
class Message:
    """Platform-agnostic message with multimodal support."""

    content: str
    role: str  # "user" | "assistant"
    attachments: list[FileAttachment] = field(default_factory=list)
    images: list[ImageContent] = field(default_factory=list)  # NEW

    @property
    def is_multimodal(self) -> bool:
        """Check if message contains images."""
        return len(self.images) > 0
```

### Step 2: Update Agent Message Conversion

Modify `_convert_to_messages` to handle multimodal content:

```python
# agent/engine.py

def _convert_to_messages(
    self,
    conversation_history: list[dict],
    user_message: str,
    images: list[ImageContent] | None = None,  # NEW parameter
) -> list:
    """Convert conversation to LangChain messages with multimodal support."""
    messages = []

    for msg in conversation_history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        msg_images = msg.get("images", [])  # NEW

        if role == "user":
            if msg_images:
                # Multimodal message
                content_parts = [{"type": "text", "text": content}]
                for img in msg_images:
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {"url": img.data_uri, "detail": img.detail}
                    })
                messages.append(HumanMessage(content=content_parts))
            else:
                messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content, tool_calls=[]))

    # Current message
    if images:
        content_parts = [{"type": "text", "text": user_message}]
        for img in images:
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": img.data_uri, "detail": img.detail}
            })
        messages.append(HumanMessage(content=content_parts))
    else:
        messages.append(HumanMessage(content=user_message))

    return messages
```

### Step 3: Update process_message Signature

```python
# agent/engine.py

def process_message(
    self,
    user_message: str,
    conversation_history: list[dict[str, str]],
    context: dict[str, Any] | None = None,
    images: list[ImageContent] | None = None,  # NEW parameter
) -> tuple[str, str | None]:
    """
    Process a user message using ReACT pattern.

    Args:
        user_message: The user's text message
        conversation_history: Previous conversation messages
        context: Optional context dict
        images: Optional list of images to include with the message  # NEW

    Returns:
        Tuple of (agent_response, trace_id)
    """
    messages = self._convert_to_messages(
        conversation_history,
        user_message,
        images,  # Pass images
    )
    # ... rest of method unchanged
```

### Step 4: Ensure Vision-Capable LLM

The agent must use a vision-capable model when images are present:

```python
# agent/engine.py

def __init__(
    self,
    # ... existing params ...
    vision_llm: BaseChatModel | None = None,  # NEW: separate vision LLM
):
    self.llm = llm or get_llm(streaming=False, temperature=temperature)
    self.vision_llm = vision_llm  # For multimodal requests
    # ...

def process_message(self, user_message, history, context=None, images=None):
    # Select appropriate LLM
    if images and self.vision_llm:
        active_llm = self.vision_llm
    else:
        active_llm = self.llm

    # Use active_llm for this request
    # ...
```

### Step 5: FastAPI Integration

Update the chat endpoint to accept images:

```python
# adapters/fastapi/schemas.py

class ChatRequest(BaseModel):
    message: str
    conversation_id: str
    history: list[dict] = []
    images: list[ImageData] = []  # NEW


class ImageData(BaseModel):
    data_uri: str  # base64 or URL
    detail: str = "auto"


# adapters/fastapi/routes.py

@router.post("/chat")
async def chat(request: ChatRequest):
    images = [ImageContent(data_uri=img.data_uri, detail=img.detail)
              for img in request.images]

    response, trace_id = agent.process_message(
        user_message=request.message,
        conversation_history=request.history,
        images=images if images else None,
    )
    # ...
```

### Step 6: MessagingPort Integration (Slack, etc.)

Update messaging adapters to download and convert images:

```python
# Example: Slack adapter handling images

async def process_incoming_message(self, event):
    message = event.get("text", "")
    files = event.get("files", [])

    images = []
    for file in files:
        if file.get("mimetype", "").startswith("image/"):
            # Download and convert to base64
            image_bytes = await self.download_file(file["url_private"])
            data_uri = f"data:{file['mimetype']};base64,{base64.b64encode(image_bytes).decode()}"
            images.append(ImageContent(data_uri=data_uri))

    # Pass to agent
    response, trace_id = agent.process_message(
        user_message=message,
        conversation_history=history,
        images=images if images else None,
    )
```

---

## Migration Path

### Backward Compatibility

The changes are additive. Existing code continues to work:

```python
# Old code (still works):
agent.process_message("Hello", history)

# New code (with images):
agent.process_message("What's in this?", history, images=[img])
```

### Deprecation of ImageAnalyzer?

`ImageAnalyzer` remains useful for:
- Batch pre-processing of many images
- Caching image analyses
- Scenarios where you want the analysis text explicitly

It can coexist with multimodal agent support.

---

## Summary

| Aspect | Current State | Target State |
|--------|---------------|--------------|
| Image handling | Separate `ImageAnalyzer` service | Direct in agent |
| Message format | Text only (`str`) | Multimodal (`list[dict]`) |
| LLM calls | Two (analysis + agent) | One (multimodal) |
| Context awareness | Image analyzed without question context | Image + question together |
| Agent signature | `process_message(text, history)` | `process_message(text, history, images)` |

### Files to Modify

| File | Change |
|------|--------|
| `ports/messaging.py` | Add `ImageContent`, update `Message` |
| `agent/engine.py` | Add `images` param, update `_convert_to_messages` |
| `adapters/fastapi/schemas.py` | Add `ImageData` to request |
| `adapters/fastapi/routes.py` | Pass images to agent |
| Platform adapters | Download and convert images to base64 |

### Key Considerations

1. **Model support**: Ensure selected LLM supports vision (GPT-4o, Claude 3.5 Sonnet, Gemini Pro Vision)
2. **Image size limits**: Vision APIs have size limits (~20MB for OpenAI)
3. **Cost**: Vision tokens are more expensive than text tokens
4. **History storage**: Decide whether to store images in conversation history or just references
