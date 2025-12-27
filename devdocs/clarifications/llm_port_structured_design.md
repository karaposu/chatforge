# LLMPort Structured Design
## Proper Message and Response Handling

**Problem:** Original LLMPort design too simplistic for multimodal content, model selection, and metadata.

---

## 1. Message Content Structure

```python
"""
chatforge/ports/llm/content.py

Structured content types for LLM messages.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class ContentType(Enum):
    """Types of content in LLM messages."""
    TEXT = "text"
    IMAGE_URL = "image_url"
    IMAGE_BASE64 = "image_base64"
    AUDIO_URL = "audio_url"
    AUDIO_BASE64 = "audio_base64"
    # Future: VIDEO, DOCUMENT, etc.


@dataclass
class TextContent:
    """Plain text content."""
    type: Literal["text"] = "text"
    text: str = ""


@dataclass
class ImageContent:
    """Image content (URL or base64)."""
    type: Literal["image_url", "image_base64"]

    # For image_url type
    url: str | None = None

    # For image_base64 type
    base64_data: str | None = None
    media_type: str = "image/png"  # image/png, image/jpeg, etc.

    # Optional detail level (for OpenAI)
    detail: Literal["auto", "low", "high"] = "auto"


@dataclass
class AudioContent:
    """Audio content (URL or base64)."""
    type: Literal["audio_url", "audio_base64"]

    url: str | None = None
    base64_data: str | None = None
    media_type: str = "audio/wav"  # audio/wav, audio/mp3, etc.


# Union type for all content types
ContentPart = TextContent | ImageContent | AudioContent
```

---

## 2. Message Structure

```python
"""
chatforge/ports/llm/message.py

LLM message with support for multimodal content.
"""

from dataclasses import dataclass, field
from typing import Literal
from chatforge.ports.llm.content import ContentPart, TextContent


@dataclass
class LLMMessage:
    """
    LLM message supporting multimodal content.

    Examples:
        # Simple text message
        msg = LLMMessage(
            role="user",
            content="What's in this image?"
        )

        # Text + image (URL)
        msg = LLMMessage(
            role="user",
            content=[
                TextContent(text="What's in this image?"),
                ImageContent(type="image_url", url="https://example.com/pic.jpg")
            ]
        )

        # Text + multiple images (base64)
        msg = LLMMessage(
            role="user",
            content=[
                TextContent(text="Compare these two images"),
                ImageContent(type="image_base64", base64_data="iVBORw0KGgoAAAANSUhEUg...", media_type="image/png"),
                ImageContent(type="image_base64", base64_data="iVBORw0KGgoAAAANSUhEUg...", media_type="image/png"),
            ]
        )

        # Assistant message with tool calls
        msg = LLMMessage(
            role="assistant",
            content="I'll search for that information.",
            tool_calls=[
                {"id": "call_abc123", "name": "search", "arguments": {"query": "weather"}}
            ]
        )
    """

    role: Literal["system", "user", "assistant", "tool"]

    # Content can be:
    # 1. Simple string (text-only)
    # 2. List of ContentPart (multimodal)
    content: str | list[ContentPart]

    # Optional fields
    name: str | None = None  # For function/tool messages
    tool_calls: list[dict] | None = None  # For assistant messages with tool calls
    tool_call_id: str | None = None  # For tool response messages

    # Metadata
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Normalize content to list of ContentPart."""
        # If content is a simple string, convert to TextContent
        if isinstance(self.content, str):
            self._text_content = self.content
            self._content_parts = [TextContent(text=self.content)]
        else:
            # Content is already list of ContentPart
            self._content_parts = self.content
            # Extract text for backward compatibility
            text_parts = [part.text for part in self.content if isinstance(part, TextContent)]
            self._text_content = " ".join(text_parts) if text_parts else ""

    def get_text_content(self) -> str:
        """Get text content only (for backward compatibility)."""
        return self._text_content

    def get_content_parts(self) -> list[ContentPart]:
        """Get all content parts."""
        return self._content_parts

    def has_images(self) -> bool:
        """Check if message contains images."""
        return any(isinstance(part, ImageContent) for part in self._content_parts)

    def has_audio(self) -> bool:
        """Check if message contains audio."""
        return any(isinstance(part, AudioContent) for part in self._content_parts)

    def is_multimodal(self) -> bool:
        """Check if message has non-text content."""
        return len(self._content_parts) > 1 or (
            len(self._content_parts) == 1 and not isinstance(self._content_parts[0], TextContent)
        )
```

---

## 3. Response Structure

```python
"""
chatforge/ports/llm/response.py

LLM response with comprehensive metadata.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TokenUsage:
    """Token usage information."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    # Optional: provider-specific details
    cached_tokens: int = 0  # For Anthropic prompt caching
    reasoning_tokens: int = 0  # For OpenAI o1 models

    def __post_init__(self):
        """Calculate total if not provided."""
        if self.total_tokens == 0:
            self.total_tokens = self.prompt_tokens + self.completion_tokens


@dataclass
class LLMResponse:
    """
    LLM response with metadata.

    Example:
        response = LLMResponse(
            content="The weather is sunny.",
            model="gpt-4o-mini",
            usage=TokenUsage(prompt_tokens=15, completion_tokens=8),
            finish_reason="stop",
        )
    """

    # Main response content
    content: str

    # Model information
    model: str  # Actual model used (e.g., "gpt-4o-mini-2024-07-18")
    provider: str | None = None  # "openai", "anthropic", "bedrock"

    # Token usage
    usage: TokenUsage | None = None

    # Tool calls (if LLM wants to call tools)
    tool_calls: list[dict] | None = None

    # Finish reason
    finish_reason: str | None = None  # "stop", "length", "tool_calls", "content_filter"

    # Metadata (provider-specific)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Response ID (for tracing)
    response_id: str | None = None

    def get_total_tokens(self) -> int:
        """Get total tokens used (0 if no usage data)."""
        return self.usage.total_tokens if self.usage else 0

    def has_tool_calls(self) -> bool:
        """Check if response contains tool calls."""
        return bool(self.tool_calls)
```

---

## 4. Revised LLMPort Interface

```python
"""
chatforge/ports/llm/port.py

LLMPort interface with structured messages and responses.
"""

from abc import ABC, abstractmethod
from typing import Iterator, AsyncIterator, Any

from chatforge.ports.llm.message import LLMMessage
from chatforge.ports.llm.response import LLMResponse


class LLMPort(ABC):
    """
    Port interface for LLM interactions with structured messages.

    Example Usage:
        # Initialize with default model
        llm = OpenAILLMAdapter(
            api_key="sk-...",
            default_model="gpt-4o-mini",
            default_temperature=0.7,
        )

        # Simple text call
        response = await llm.ainvoke([
            LLMMessage(role="user", content="Hello!")
        ])
        print(response.content)  # "Hi there!"
        print(response.usage.total_tokens)  # 25

        # Override model for specific call
        response = await llm.ainvoke(
            messages=[LLMMessage(role="user", content="Complex task")],
            model="gpt-4o",  # Override default
            temperature=0.0,  # Override default
        )

        # Vision: text + image
        response = await llm.ainvoke([
            LLMMessage(
                role="user",
                content=[
                    TextContent(text="What's in this image?"),
                    ImageContent(type="image_url", url="https://example.com/cat.jpg"),
                ]
            )
        ])

        # Streaming
        async for chunk in llm.astream([LLMMessage(role="user", content="Tell me a story")]):
            print(chunk, end="", flush=True)
    """

    @abstractmethod
    def invoke(
        self,
        messages: list[LLMMessage],
        model: str | None = None,  # ⭐ Override default model
        temperature: float | None = None,  # ⭐ Override default temperature
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Synchronous LLM call with structured messages.

        Args:
            messages: List of LLMMessage objects (can include multimodal content)
            model: Override the default model for this call
            temperature: Override the default temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters

        Returns:
            LLMResponse with content, usage, and metadata

        Example:
            response = llm.invoke(
                messages=[LLMMessage(role="user", content="Hello")],
                model="gpt-4o",  # Use specific model
                temperature=0.9,
                max_tokens=100,
            )
        """
        pass

    @abstractmethod
    async def ainvoke(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Async version of invoke."""
        pass

    @abstractmethod
    def stream(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        """
        Streaming LLM call (synchronous iterator).

        Args:
            messages: List of LLMMessage objects
            model: Override default model
            temperature: Override default temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters

        Yields:
            str: Content chunks as they arrive

        Example:
            for chunk in llm.stream([LLMMessage(role="user", content="Tell a story")]):
                print(chunk, end="", flush=True)
        """
        pass

    @abstractmethod
    async def astream(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Async streaming LLM call."""
        pass

    @abstractmethod
    def supports_vision(self, model: str | None = None) -> bool:
        """
        Check if model supports vision (images).

        Args:
            model: Model to check (uses default if None)

        Returns:
            True if model can process images
        """
        pass

    @abstractmethod
    def supports_tools(self, model: str | None = None) -> bool:
        """
        Check if model supports tool/function calling.

        Args:
            model: Model to check (uses default if None)
        """
        pass

    @abstractmethod
    def supports_audio(self, model: str | None = None) -> bool:
        """
        Check if model supports audio input.

        Args:
            model: Model to check (uses default if None)
        """
        pass

    @abstractmethod
    def get_default_model(self) -> str:
        """Get the default model name."""
        pass

    @abstractmethod
    def get_provider(self) -> str:
        """Get the provider name (e.g., 'openai', 'anthropic')."""
        pass

    @abstractmethod
    def get_available_models(self) -> list[str]:
        """
        Get list of available models for this provider.

        Returns:
            List of model names

        Example:
            models = llm.get_available_models()
            # ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', ...]
        """
        pass
```

---

## 5. Example Implementation: OpenAILLMAdapter

```python
"""
chatforge/adapters/llm/openai_adapter.py

OpenAI implementation with structured messages.
"""

from openai import OpenAI, AsyncOpenAI
from chatforge.ports.llm import LLMPort, LLMMessage, LLMResponse, TokenUsage
from chatforge.ports.llm.content import TextContent, ImageContent


class OpenAILLMAdapter(LLMPort):
    """OpenAI LLM adapter with multimodal support."""

    # Model capabilities
    VISION_MODELS = {"gpt-4o", "gpt-4o-mini", "gpt-4-turbo"}
    TOOL_MODELS = {"gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"}

    def __init__(
        self,
        api_key: str,
        default_model: str = "gpt-4o-mini",
        default_temperature: float = 0.7,
        organization: str | None = None,
    ):
        """
        Initialize OpenAI adapter.

        Args:
            api_key: OpenAI API key
            default_model: Default model to use (can be overridden per call)
            default_temperature: Default temperature (can be overridden per call)
            organization: Optional organization ID
        """
        self.client = OpenAI(api_key=api_key, organization=organization)
        self.async_client = AsyncOpenAI(api_key=api_key, organization=organization)
        self.default_model = default_model
        self.default_temperature = default_temperature

    async def ainvoke(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Async invoke with structured messages."""

        # Use provided values or defaults
        actual_model = model or self.default_model
        actual_temperature = temperature if temperature is not None else self.default_temperature

        # Convert LLMMessage to OpenAI format
        openai_messages = self._convert_to_openai_format(messages)

        # Prepare API call parameters
        api_params = {
            "model": actual_model,
            "messages": openai_messages,
            "temperature": actual_temperature,
        }

        if max_tokens:
            api_params["max_tokens"] = max_tokens

        # Add any extra kwargs
        api_params.update(kwargs)

        # Call OpenAI API
        response = await self.async_client.chat.completions.create(**api_params)

        # Convert to LLMResponse
        choice = response.choices[0]

        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            provider="openai",
            usage=TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            ),
            tool_calls=choice.message.tool_calls if hasattr(choice.message, "tool_calls") else None,
            finish_reason=choice.finish_reason,
            response_id=response.id,
            metadata={
                "created": response.created,
                "system_fingerprint": response.system_fingerprint,
            },
        )

    def invoke(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Sync invoke (same as ainvoke but synchronous)."""
        actual_model = model or self.default_model
        actual_temperature = temperature if temperature is not None else self.default_temperature

        openai_messages = self._convert_to_openai_format(messages)

        api_params = {
            "model": actual_model,
            "messages": openai_messages,
            "temperature": actual_temperature,
        }

        if max_tokens:
            api_params["max_tokens"] = max_tokens

        api_params.update(kwargs)

        response = self.client.chat.completions.create(**api_params)

        choice = response.choices[0]

        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            provider="openai",
            usage=TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            ),
            tool_calls=choice.message.tool_calls if hasattr(choice.message, "tool_calls") else None,
            finish_reason=choice.finish_reason,
            response_id=response.id,
        )

    async def astream(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ):
        """Async streaming."""
        actual_model = model or self.default_model
        actual_temperature = temperature if temperature is not None else self.default_temperature

        openai_messages = self._convert_to_openai_format(messages)

        api_params = {
            "model": actual_model,
            "messages": openai_messages,
            "temperature": actual_temperature,
            "stream": True,
        }

        if max_tokens:
            api_params["max_tokens"] = max_tokens

        api_params.update(kwargs)

        stream = await self.async_client.chat.completions.create(**api_params)

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def stream(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ):
        """Sync streaming."""
        actual_model = model or self.default_model
        actual_temperature = temperature if temperature is not None else self.default_temperature

        openai_messages = self._convert_to_openai_format(messages)

        api_params = {
            "model": actual_model,
            "messages": openai_messages,
            "temperature": actual_temperature,
            "stream": True,
        }

        if max_tokens:
            api_params["max_tokens"] = max_tokens

        api_params.update(kwargs)

        stream = self.client.chat.completions.create(**api_params)

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _convert_to_openai_format(self, messages: list[LLMMessage]) -> list[dict]:
        """
        Convert LLMMessage to OpenAI message format.

        Handles:
        - Simple text messages
        - Multimodal messages (text + images)
        - Tool calls and responses
        """
        openai_messages = []

        for msg in messages:
            openai_msg = {"role": msg.role}

            # Handle multimodal content
            if msg.is_multimodal():
                content_parts = []

                for part in msg.get_content_parts():
                    if isinstance(part, TextContent):
                        content_parts.append({
                            "type": "text",
                            "text": part.text,
                        })

                    elif isinstance(part, ImageContent):
                        if part.type == "image_url":
                            content_parts.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": part.url,
                                    "detail": part.detail,
                                },
                            })

                        elif part.type == "image_base64":
                            # OpenAI format: data:image/png;base64,iVBORw0KG...
                            data_uri = f"data:{part.media_type};base64,{part.base64_data}"
                            content_parts.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": data_uri,
                                    "detail": part.detail,
                                },
                            })

                openai_msg["content"] = content_parts

            else:
                # Simple text message
                openai_msg["content"] = msg.get_text_content()

            # Handle tool calls (for assistant messages)
            if msg.tool_calls:
                openai_msg["tool_calls"] = msg.tool_calls

            # Handle tool responses
            if msg.tool_call_id:
                openai_msg["tool_call_id"] = msg.tool_call_id

            if msg.name:
                openai_msg["name"] = msg.name

            openai_messages.append(openai_msg)

        return openai_messages

    def supports_vision(self, model: str | None = None) -> bool:
        """Check if model supports vision."""
        check_model = model or self.default_model
        return check_model in self.VISION_MODELS

    def supports_tools(self, model: str | None = None) -> bool:
        """Check if model supports tools."""
        check_model = model or self.default_model
        return check_model in self.TOOL_MODELS

    def supports_audio(self, model: str | None = None) -> bool:
        """OpenAI doesn't support audio in chat completions yet."""
        return False

    def get_default_model(self) -> str:
        return self.default_model

    def get_provider(self) -> str:
        return "openai"

    def get_available_models(self) -> list[str]:
        """Get available OpenAI models."""
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
        ]
```

---

## 6. Usage Examples

### Example 1: Simple Text Message

```python
from chatforge.ports.llm import LLMMessage
from chatforge.adapters.llm import OpenAILLMAdapter

llm = OpenAILLMAdapter(
    api_key="sk-...",
    default_model="gpt-4o-mini",
    default_temperature=0.7,
)

# Simple call
response = await llm.ainvoke([
    LLMMessage(role="user", content="What is 2+2?")
])

print(response.content)  # "2 + 2 equals 4."
print(response.usage.total_tokens)  # 25
print(response.model)  # "gpt-4o-mini-2024-07-18"
```

### Example 2: Text + Image (URL)

```python
from chatforge.ports.llm.content import TextContent, ImageContent

response = await llm.ainvoke([
    LLMMessage(
        role="user",
        content=[
            TextContent(text="What's in this image?"),
            ImageContent(
                type="image_url",
                url="https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png"
            ),
        ]
    )
])

print(response.content)  # "The image shows a demonstration of PNG transparency..."
```

### Example 3: Text + Multiple Images (Base64)

```python
import base64

# Load images
with open("image1.png", "rb") as f:
    img1_b64 = base64.b64encode(f.read()).decode()

with open("image2.png", "rb") as f:
    img2_b64 = base64.b64encode(f.read()).decode()

response = await llm.ainvoke([
    LLMMessage(
        role="user",
        content=[
            TextContent(text="Compare these two images and tell me the differences."),
            ImageContent(type="image_base64", base64_data=img1_b64, media_type="image/png"),
            ImageContent(type="image_base64", base64_data=img2_b64, media_type="image/png"),
        ]
    )
])

print(response.content)  # Comparison analysis
```

### Example 4: Override Model Per-Call

```python
# Initialize with cheap model as default
llm = OpenAILLMAdapter(
    api_key="sk-...",
    default_model="gpt-4o-mini",  # Cheap for most calls
    default_temperature=0.7,
)

# Simple question - use default (gpt-4o-mini)
response1 = await llm.ainvoke([
    LLMMessage(role="user", content="What's 2+2?")
])
print(response1.model)  # "gpt-4o-mini"

# Complex reasoning - override with better model
response2 = await llm.ainvoke(
    messages=[
        LLMMessage(role="user", content="Solve this complex physics problem...")
    ],
    model="gpt-4o",  # ⭐ Override for this call only
    temperature=0.0,
)
print(response2.model)  # "gpt-4o"
```

### Example 5: ChamberProtocolAI Use Case

```python
from chatforge.ports.llm import LLMMessage
from chatforge.ports.llm.content import TextContent

class SiluetService:
    def __init__(self, llm: LLMPort):
        self.llm = llm

    async def process_request(self, request):
        # Build dynamic system prompt with random word limit
        random_words = random.randint(2, 100)
        system_prompt = self._build_silüet_prompt(
            personality=request.personality,
            word_limit=random_words,
            emotion_tag=request.emotion_tag,
        )

        # Get history
        history = await self.storage.get_conversation(request.chat_id)

        # Build messages
        messages = [
            LLMMessage(role="system", content=system_prompt),
        ]

        for msg in history:
            messages.append(
                LLMMessage(role=msg.role, content=msg.content)
            )

        messages.append(
            LLMMessage(role="user", content=request.user_message)
        )

        # Call LLM with specific model and temperature
        response = await self.llm.ainvoke(
            messages=messages,
            model="claude-3-5-sonnet-20241022",  # ⭐ Specify model
            temperature=0.8,  # ⭐ Specify temperature
            max_tokens=500,
        )

        # Extract emotion tag from response
        emotion_tag = self._extract_emotion_tag(response.content)

        return {
            "content": response.content,
            "emotion_tag": emotion_tag,
            "tokens_used": response.usage.total_tokens,
        }
```

---

## 7. Key Improvements

### ✅ Multimodal Support
- Text + images (URL or base64)
- Text + audio (future)
- Multiple images per message

### ✅ Flexible Model Selection
- Default model at initialization
- Override per-call for specific needs
- Check capabilities per model (`supports_vision(model="gpt-4o")`)

### ✅ Structured Responses
- Full metadata (tokens, model, finish reason)
- Provider-specific details
- Response IDs for tracing

### ✅ Content Type Safety
- `TextContent`, `ImageContent`, `AudioContent` dataclasses
- Type hints for all content
- Clear structure for adapters to implement

### ✅ Backward Compatible
- Simple string content still works (`LLMMessage(role="user", content="text")`)
- Automatically converted to `TextContent`

---

## Summary

**Original design issues:**
- ❌ `invoke(messages) -> str` loses metadata
- ❌ No multimodal support
- ❌ Model fixed at initialization

**New structured design:**
- ✅ `invoke(messages, model=..., temperature=...) -> LLMResponse`
- ✅ Multimodal content (text + images + audio)
- ✅ Override model/temperature per call
- ✅ Rich response metadata (tokens, finish reason, etc.)
- ✅ Type-safe content parts

This gives chatforge the flexibility needed for real-world LLM applications!
