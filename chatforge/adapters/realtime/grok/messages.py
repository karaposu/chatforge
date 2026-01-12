# chatforge/adapters/realtime/grok/messages.py
"""Grok Realtime API message factory."""

import base64
import json
import logging
from typing import Any

from chatforge.ports.realtime_voice import VoiceSessionConfig, ToolDefinition

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

# Grok native voices only - don't try to map OpenAI voices
GROK_VOICES = {"ara", "rex", "sal", "eve", "leo"}

# Valid sample rates for PCM audio
VALID_SAMPLE_RATES = {8000, 16000, 21050, 24000, 32000, 44100, 48000}

# Built-in Grok tool types (not function type)
BUILTIN_TOOLS = {"web_search", "x_search", "file_search"}

# =============================================================================
# Mapping Functions
# =============================================================================


def _map_voice(voice: str) -> str:
    """Map voice name to Grok voice."""
    normalized = voice.lower()
    if normalized in GROK_VOICES:
        return normalized.capitalize()
    if normalized == "default":
        return "Ara"
    logger.warning("Unknown voice '%s', using default 'Ara'", voice)
    return "Ara"


def _map_audio_format(format_str: str, sample_rate: int) -> dict:
    """Map audio format string to Grok format object."""
    type_map = {
        "pcm16": "audio/pcm",
        "pcm": "audio/pcm",
        "g711_ulaw": "audio/pcmu",
        "g711_alaw": "audio/pcma",
    }
    audio_type = type_map.get(format_str, "audio/pcm")

    result = {"type": audio_type}

    if audio_type == "audio/pcm":
        # Validate and adjust sample rate
        if sample_rate not in VALID_SAMPLE_RATES:
            closest = min(VALID_SAMPLE_RATES, key=lambda x: abs(x - sample_rate))
            logger.warning(
                "Invalid sample rate %d, using closest valid rate %d",
                sample_rate, closest
            )
            sample_rate = closest
        result["rate"] = sample_rate
    elif audio_type in ("audio/pcmu", "audio/pcma"):
        # G.711 is always 8kHz
        if sample_rate != 8000:
            logger.warning(
                "G.711 format always uses 8kHz sample rate, ignoring %d",
                sample_rate
            )

    return result


def _warn_ignored_parameters(config: VoiceSessionConfig) -> None:
    """Log warnings for parameters that Grok doesn't support."""
    if config.temperature != 0.8:  # default
        logger.warning("Grok API does not support temperature parameter, ignoring")
    if config.max_tokens:
        logger.warning("Grok API does not support max_tokens parameter, ignoring")
    if config.tool_choice != "auto":
        logger.warning("Grok API does not support tool_choice parameter, ignoring")
    if not config.transcription_enabled:
        logger.warning("Grok API always transcribes, cannot disable transcription")
    if config.transcription_model:
        logger.warning("Grok API does not support transcription_model, ignoring")
    if config.vad_threshold != 0.5:  # default
        logger.warning("Grok API does not support VAD threshold configuration")
    if config.vad_prefix_ms != 300:  # default
        logger.warning("Grok API does not support VAD prefix configuration")
    if config.vad_silence_ms != 500:  # default
        logger.warning("Grok API does not support VAD silence configuration")


# =============================================================================
# Client -> Server Messages
# =============================================================================


def session_update(config: VoiceSessionConfig) -> dict:
    """Create session.update message for Grok."""
    # Warn about ignored parameters
    _warn_ignored_parameters(config)

    session = {
        "voice": _map_voice(config.voice),
        "audio": {
            "input": {"format": _map_audio_format(config.input_format, config.sample_rate)},
            "output": {"format": _map_audio_format(config.output_format, config.sample_rate)},
        },
    }

    # Instructions (system prompt)
    if config.system_prompt:
        session["instructions"] = config.system_prompt

    # Turn detection (VAD)
    # Note: Both "client" and "none" map to null (manual mode)
    if config.vad_mode == "server":
        session["turn_detection"] = {"type": "server_vad"}
    else:
        session["turn_detection"] = None

    # Tools (with built-in tool support)
    if config.tools:
        session["tools"] = [_tool_to_grok(t) for t in config.tools]

    # Apply provider-specific options (escape hatch)
    if config.provider_options:
        session.update(config.provider_options)

    return {"type": "session.update", "session": session}


def input_audio_buffer_append(audio: bytes) -> dict:
    """Create input_audio_buffer.append message."""
    return {
        "type": "input_audio_buffer.append",
        "audio": base64.b64encode(audio).decode("ascii"),
    }


def input_audio_buffer_commit(vad_mode: str = "server") -> dict:
    """
    Create audio commit message.

    IMPORTANT: Grok uses different commit messages depending on VAD mode:
    - Server VAD: conversation.item.commit
    - Manual/Client VAD: input_audio_buffer.commit
    """
    if vad_mode in ("client", "none"):
        # Manual VAD mode uses input_audio_buffer.commit
        return {"type": "input_audio_buffer.commit"}
    else:
        # Server VAD uses conversation.item.commit
        return {"type": "conversation.item.commit"}


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
    # If error, wrap in error structure so AI knows it failed
    if is_error:
        output = json.dumps({"error": output})

    return {
        "type": "conversation.item.create",
        "item": {
            "type": "function_call_output",
            "call_id": call_id,
            "output": output,
        },
    }


def response_create(
    instructions: str | None = None,
    modalities: list[str] | None = None
) -> dict:
    """Create response.create message."""
    msg: dict = {
        "type": "response.create",
        "response": {
            "modalities": modalities or ["text", "audio"],
        },
    }
    if instructions:
        msg["response"]["instructions"] = instructions
    return msg


def response_cancel(response_id: str | None = None) -> dict:
    """
    Create response.cancel message.

    WARNING: Not documented in Grok API - may not be supported.
    """
    msg = {"type": "response.cancel"}
    if response_id:
        msg["response_id"] = response_id
    return msg


# =============================================================================
# Helpers
# =============================================================================


def _tool_to_grok(tool: ToolDefinition) -> dict:
    """Convert ToolDefinition to Grok format."""
    # Check for built-in Grok tools
    if tool.name in BUILTIN_TOOLS:
        result = {"type": tool.name}

        # Add tool-specific parameters
        if tool.name == "x_search" and tool.parameters.get("allowed_x_handles"):
            result["allowed_x_handles"] = tool.parameters["allowed_x_handles"]
        elif tool.name == "file_search":
            if tool.parameters.get("vector_store_ids"):
                result["vector_store_ids"] = tool.parameters["vector_store_ids"]
            if tool.parameters.get("max_num_results"):
                result["max_num_results"] = tool.parameters["max_num_results"]

        return result

    # Regular function tool
    return {
        "type": "function",
        "name": tool.name,
        "description": tool.description,
        "parameters": tool.parameters,
    }
