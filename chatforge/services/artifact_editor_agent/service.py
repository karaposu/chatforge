"""
Artifact Editor Agent Service

An LLM Agent that modifies artifacts based on freestyle instructions.
Uses adapter methods as tools to make edits.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from chatforge.adapters.artifact_editor import LibreOfficeEditorDockerServerAdapter


@dataclass
class EditResult:
    """Result of an edit operation."""
    artifact: bytes                          # The edited artifact bytes
    tool_calls: list[dict] = field(default_factory=list)  # Tool calls made during edit


class ArtifactEditorAgentService:
    """
    LLM Agent service for editing artifacts.

    Takes freestyle instructions and uses adapter methods as tools
    to autonomously make edits to artifacts.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        adapter: LibreOfficeEditorDockerServerAdapter,
        max_iterations: int = 10,
    ):
        """
        Initialize the agent service.

        Args:
            llm: A LangChain chat model with tool-calling support
            adapter: Adapter for editing artifacts
            max_iterations: Maximum tool calls per edit session
        """
        self._llm = llm
        self._adapter = adapter
        self._max_iterations = max_iterations
        self._current_artifact: Optional[bytes] = None

    def _get_tools(self):
        """Create tools from adapter methods."""
        adapter = self._adapter

        @tool
        def get_artifact_info() -> str:
            """
            Get the current artifact structure (slides, shapes, text content).
            Use this first to understand what's in the artifact before making edits.
            Returns information about all slides and shapes.
            """
            if self._current_artifact is None:
                return "Error: No artifact loaded"
            info = adapter.get_info(self._current_artifact)
            result = f"Artifact: {info.slide_count} slides\n\n"
            for slide in info.slides:
                result += f"Slide {slide.index}: {slide.shape_count} shapes\n"
                for shape in slide.shapes:
                    text_preview = ""
                    if shape.text:
                        text_preview = f' text="{shape.text[:50]}..."' if len(shape.text) > 50 else f' text="{shape.text}"'
                    result += f"  [{shape.index}] {shape.type.split('.')[-1]}{text_preview}\n"
                    result += f"      position=({shape.position['x']}, {shape.position['y']}) "
                    result += f"size=({shape.size['width']}x{shape.size['height']})\n"
            return result

        @tool
        def edit_text(slide_index: int, shape_index: int, new_text: str) -> str:
            """
            Edit the text content of a shape.

            Args:
                slide_index: Slide number (0-based)
                shape_index: Shape number within the slide (0-based)
                new_text: The new text to set
            """
            if self._current_artifact is None:
                return "Error: No artifact loaded"
            try:
                self._current_artifact = adapter.edit_text(
                    self._current_artifact, slide_index, shape_index, new_text
                )
                return f"Success: Changed text in slide {slide_index}, shape {shape_index}"
            except Exception as e:
                return f"Error: Failed to edit text - {e}. Use get_artifact_info() to check valid indices."

        @tool
        def edit_style(
            slide_index: int,
            shape_index: int,
            font_name: Optional[str] = None,
            font_size: Optional[float] = None,
            font_color: Optional[str] = None,
        ) -> str:
            """
            Edit the text style of a shape.

            Args:
                slide_index: Slide number (0-based)
                shape_index: Shape number within the slide (0-based)
                font_name: Font family name (e.g., "Arial", "Times New Roman")
                font_size: Font size in points (e.g., 24.0)
                font_color: Hex color without # (e.g., "FF0000" for red)
            """
            if self._current_artifact is None:
                return "Error: No artifact loaded"
            try:
                self._current_artifact = adapter.edit_style(
                    self._current_artifact, slide_index, shape_index,
                    font_name=font_name, font_size=font_size, font_color=font_color
                )
                changes = []
                if font_name:
                    changes.append(f"font={font_name}")
                if font_size:
                    changes.append(f"size={font_size}")
                if font_color:
                    changes.append(f"color={font_color}")
                return f"Success: Updated style ({', '.join(changes)}) in slide {slide_index}, shape {shape_index}"
            except Exception as e:
                return f"Error: Failed to edit style - {e}. Use get_artifact_info() to check valid indices."

        @tool
        def edit_position(slide_index: int, shape_index: int, x: int, y: int) -> str:
            """
            Move a shape to a new position.

            Args:
                slide_index: Slide number (0-based)
                shape_index: Shape number within the slide (0-based)
                x: X position in 1/100mm (e.g., 1000 = 10mm from left)
                y: Y position in 1/100mm (e.g., 1000 = 10mm from top)
            """
            if self._current_artifact is None:
                return "Error: No artifact loaded"
            try:
                self._current_artifact = adapter.edit_position(
                    self._current_artifact, slide_index, shape_index, x, y
                )
                return f"Success: Moved shape to ({x}, {y}) in slide {slide_index}, shape {shape_index}"
            except Exception as e:
                return f"Error: Failed to move shape - {e}. Use get_artifact_info() to check valid indices."

        @tool
        def edit_size(slide_index: int, shape_index: int, width: int, height: int) -> str:
            """
            Resize a shape.

            Args:
                slide_index: Slide number (0-based)
                shape_index: Shape number within the slide (0-based)
                width: Width in 1/100mm
                height: Height in 1/100mm
            """
            if self._current_artifact is None:
                return "Error: No artifact loaded"
            try:
                self._current_artifact = adapter.edit_size(
                    self._current_artifact, slide_index, shape_index, width, height
                )
                return f"Success: Resized shape to ({width}x{height}) in slide {slide_index}, shape {shape_index}"
            except Exception as e:
                return f"Error: Failed to resize shape - {e}. Use get_artifact_info() to check valid indices."

        @tool
        def create_textbox(
            slide_index: int,
            x: int,
            y: int,
            width: int,
            height: int,
            text: str = "",
            font_name: Optional[str] = None,
            font_size: Optional[float] = None,
            font_color: Optional[str] = None,
        ) -> str:
            """
            Create a new textbox on a slide.

            Args:
                slide_index: Slide number (0-based)
                x: X position in 1/100mm
                y: Y position in 1/100mm
                width: Width in 1/100mm
                height: Height in 1/100mm
                text: Initial text content
                font_name: Optional font family name
                font_size: Optional font size in points
                font_color: Optional hex color without #
            """
            if self._current_artifact is None:
                return "Error: No artifact loaded"
            try:
                self._current_artifact = adapter.create_textbox(
                    self._current_artifact, slide_index, x, y, width, height,
                    text=text, font_name=font_name, font_size=font_size, font_color=font_color
                )
                return f"Success: Created textbox at ({x}, {y}) on slide {slide_index}"
            except Exception as e:
                return f"Error: Failed to create textbox - {e}. Check slide_index is valid (0-based)."

        @tool
        def create_shape(
            slide_index: int,
            shape_type: str,
            x: int,
            y: int,
            width: int,
            height: int,
            fill_color: Optional[str] = None,
            line_color: Optional[str] = None,
        ) -> str:
            """
            Create a new shape on a slide.

            Args:
                slide_index: Slide number (0-based)
                shape_type: Type of shape - "rectangle", "ellipse", "line", or "connector"
                x: X position in 1/100mm
                y: Y position in 1/100mm
                width: Width in 1/100mm
                height: Height in 1/100mm
                fill_color: Optional fill color as hex without # (e.g., "FF0000")
                line_color: Optional line color as hex without #
            """
            if self._current_artifact is None:
                return "Error: No artifact loaded"
            try:
                self._current_artifact = adapter.create_shape(
                    self._current_artifact, slide_index, shape_type, x, y, width, height,
                    fill_color=fill_color, line_color=line_color
                )
                return f"Success: Created {shape_type} at ({x}, {y}) on slide {slide_index}"
            except Exception as e:
                return f"Error: Failed to create shape - {e}. Check slide_index is valid (0-based)."

        return [
            get_artifact_info,
            edit_text,
            edit_style,
            edit_position,
            edit_size,
            create_textbox,
            create_shape,
        ]

    def _get_artifact_info_str(self) -> str:
        """Get artifact structure as a string for the agent."""
        if self._current_artifact is None:
            return "No artifact loaded"
        info = self._adapter.get_info(self._current_artifact)
        result = f"Artifact: {info.slide_count} slides\n\n"
        for slide in info.slides:
            result += f"Slide {slide.index}: {slide.shape_count} shapes\n"
            for shape in slide.shapes:
                text_preview = ""
                if shape.text:
                    text_preview = f' text="{shape.text[:50]}..."' if len(shape.text) > 50 else f' text="{shape.text}"'
                result += f"  [{shape.index}] {shape.type.split('.')[-1]}{text_preview}\n"
                result += f"      position=({shape.position['x']}, {shape.position['y']}) "
                result += f"size=({shape.size['width']}x{shape.size['height']})\n"
        return result

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent."""
        return """You are an artifact editor agent. Your job is to modify presentation slides based on the given instructions.

CRITICAL RULES:
- Slide and shape indices are 0-based (first slide = 0, first shape = 0)
- Positions and sizes are in 1/100mm (e.g., 10000 = 100mm = 10cm)
- Colors are hex strings without # (e.g., "FF0000" for red, "1E88E5" for blue)
- Only edit shapes that exist - check the artifact info
- If a tool returns an error, try a different approach or skip that change

WORKFLOW - Follow this for EVERY change:
1. Call get_artifact_info() to see current structure
2. Make ONE edit using the appropriate tool
3. Call get_artifact_info() again to verify the change
4. Repeat for next change

Always re-fetch artifact info before and after each edit. Indices may change after edits.

Available tools:
- get_artifact_info(): Get current structure - CALL THIS FREQUENTLY
- edit_text(slide_index, shape_index, new_text): Change text content
- edit_style(slide_index, shape_index, font_name, font_size, font_color): Change font
- edit_position(slide_index, shape_index, x, y): Move a shape
- edit_size(slide_index, shape_index, width, height): Resize a shape
- create_textbox(slide_index, x, y, width, height, text, ...): Add new textbox
- create_shape(slide_index, shape_type, x, y, width, height, ...): Add new shape

When done, respond with "DONE" and a summary of changes made."""

    def edit(
        self,
        artifact: Union[bytes, str, Path],
        instructions: str,
    ) -> EditResult:
        """
        Edit artifact based on freestyle instructions.

        The agent interprets the instructions and uses tools to make changes.

        Args:
            artifact: Source artifact as bytes, file path, or Path object
            instructions: Freestyle text describing what changes to make

        Returns:
            EditResult with modified artifact and list of tool calls made
        """
        # Load artifact
        if isinstance(artifact, (str, Path)):
            path = Path(artifact)
            if not path.exists():
                raise FileNotFoundError(f"Artifact not found: {path}")
            self._current_artifact = path.read_bytes()
        else:
            self._current_artifact = artifact

        # Bind tools to LLM
        tools = self._get_tools()
        llm_with_tools = self._llm.bind_tools(tools)

        # Get artifact structure upfront so agent knows valid indices
        artifact_info = self._get_artifact_info_str()

        # Track tool calls
        tool_calls_log: list[dict] = []

        # Create messages
        messages = [
            SystemMessage(content=self._get_system_prompt()),
            HumanMessage(content=f"""CURRENT ARTIFACT STRUCTURE:
{artifact_info}

REQUESTED CHANGES:
{instructions}

Make the changes using the edit tools. Remember: indices are 0-based."""),
        ]

        # Agent loop
        for _ in range(self._max_iterations):
            response = llm_with_tools.invoke(messages)
            messages.append(response)

            # Check if we have tool calls
            if not response.tool_calls:
                # No more tool calls - agent is done
                break

            # Execute tool calls
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                # Find and execute the tool
                tool_fn = next((t for t in tools if t.name == tool_name), None)
                if tool_fn:
                    result = tool_fn.invoke(tool_args)
                else:
                    result = f"Error: Unknown tool {tool_name}"

                # Log the tool call
                tool_calls_log.append({
                    "tool": tool_name,
                    "args": tool_args,
                    "result": str(result),
                })

                # Add tool result to messages
                from langchain_core.messages import ToolMessage
                messages.append(ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"],
                ))

        return EditResult(
            artifact=self._current_artifact,
            tool_calls=tool_calls_log,
        )
