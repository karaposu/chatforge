"""OpenAI Realtime API message factory."""

import base64
from typing import Any

from chatforge.ports.realtime_voice import VoiceSessionConfig, ToolDefinition


# =============================================================================
# Client → Server Messages
# =============================================================================


def session_update(config: VoiceSessionConfig) -> dict:
    """Create session.update message."""
    session = {
        "modalities": config.modalities,
        "temperature": config.temperature,
    }

    # Voice
    if config.voice != "default":
        session["voice"] = config.voice

    # Instructions
    if config.system_prompt:
        session["instructions"] = config.system_prompt

    # Max tokens
    if config.max_tokens:
        session["max_response_output_tokens"] = config.max_tokens

    # Audio format
    session["input_audio_format"] = config.input_format
    session["output_audio_format"] = config.output_format

    # Transcription
    if config.transcription_enabled:
        session["input_audio_transcription"] = {
            "model": config.transcription_model or "whisper-1"
        }

    # Turn detection (VAD)
    # "server" = use server-side VAD
    # "client" = client handles VAD, disable server VAD
    # "none" = no VAD, manual commit required
    if config.vad_mode == "server":
        session["turn_detection"] = {
            "type": "server_vad",
            "threshold": config.vad_threshold,
            "prefix_padding_ms": config.vad_prefix_ms,
            "silence_duration_ms": config.vad_silence_ms,
            "create_response": True,
        }
    else:  # "client" or "none" - disable server VAD
        session["turn_detection"] = None

    # Tools
    if config.tools:
        session["tools"] = [_tool_to_openai(t) for t in config.tools]
        session["tool_choice"] = config.tool_choice

    # Provider-specific overrides
    if config.provider_options:
        session.update(config.provider_options)

    return {"type": "session.update", "session": session}


def input_audio_buffer_append(audio: bytes) -> dict:
    """Create input_audio_buffer.append message."""
    return {
        "type": "input_audio_buffer.append",
        "audio": base64.b64encode(audio).decode("ascii"),
    }


def input_audio_buffer_commit() -> dict:
    """Create input_audio_buffer.commit message."""
    return {"type": "input_audio_buffer.commit"}


def input_audio_buffer_clear() -> dict:
    """Create input_audio_buffer.clear message."""
    return {"type": "input_audio_buffer.clear"}


def conversation_item_create_message(text: str) -> dict:
    """Create text message item."""
    return {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": text}],
        },
    }


def conversation_item_create_tool_result(
    call_id: str,
    output: str,
    is_error: bool = False
) -> dict:
    """Create function call output item."""
    item = {
        "type": "function_call_output",
        "call_id": call_id,
        "output": output,
    }
    # Include error status if this is an error response
    # OpenAI uses this to know the tool failed
    if is_error:
        item["error"] = True
    return {
        "type": "conversation.item.create",
        "item": item,
    }


def response_create(instructions: str | None = None) -> dict:
    """Create response.create message."""
    msg = {"type": "response.create"}
    if instructions:
        msg["response"] = {"instructions": instructions}
    return msg


def response_cancel(response_id: str | None = None) -> dict:
    """Create response.cancel message."""
    msg = {"type": "response.cancel"}
    if response_id:
        msg["response_id"] = response_id
    return msg


# =============================================================================
# Helpers
# =============================================================================


def _tool_to_openai(tool: ToolDefinition) -> dict:
    """Convert ToolDefinition to OpenAI format."""
    return {
        "type": "function",
        "name": tool.name,
        "description": tool.description,
        "parameters": tool.parameters,
    }
