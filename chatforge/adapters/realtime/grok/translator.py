# chatforge/adapters/realtime/grok/translator.py
"""Translate Grok events to normalized VoiceEvent."""

import base64
import binascii
import json
import logging
from typing import Any

from chatforge.ports.realtime_voice import VoiceEvent, VoiceEventType

logger = logging.getLogger(__name__)


def _safe_base64_decode(data: str) -> bytes | None:
    """Safely decode base64 data, returning None on failure."""
    try:
        return base64.b64decode(data)
    except (ValueError, binascii.Error) as e:
        logger.warning("Invalid base64 data: %s", e)
        return None


def _safe_json_parse(s: str) -> Any:
    """Safely parse JSON, returning original string on failure."""
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return s


def translate_event(raw: dict) -> VoiceEvent | None:
    """
    Translate Grok event to VoiceEvent.

    Returns None for events we don't care about.
    """
    event_type = raw.get("type", "")

    # =========================================================================
    # Session Events
    # =========================================================================

    if event_type == "conversation.created":
        # Grok sends this first instead of session.created
        return VoiceEvent(
            type=VoiceEventType.SESSION_CREATED,
            data=raw.get("conversation"),
            raw_event=raw,
        )

    if event_type == "session.updated":
        return VoiceEvent(
            type=VoiceEventType.SESSION_UPDATED,
            data=raw.get("session"),
            raw_event=raw,
        )

    # =========================================================================
    # Audio Output Events
    # =========================================================================

    if event_type == "response.output_audio.delta":
        audio_data = _safe_base64_decode(raw.get("delta", ""))
        if audio_data is None:
            return None
        return VoiceEvent(
            type=VoiceEventType.AUDIO_CHUNK,
            data=audio_data,
            metadata={
                "response_id": raw.get("response_id"),
                "item_id": raw.get("item_id"),
                "output_index": raw.get("output_index"),
                "content_index": raw.get("content_index"),
            },
            raw_event=raw,
        )

    if event_type == "response.output_audio.done":
        return VoiceEvent(
            type=VoiceEventType.AUDIO_DONE,
            metadata={
                "response_id": raw.get("response_id"),
                "item_id": raw.get("item_id"),
            },
            raw_event=raw,
        )

    # =========================================================================
    # Audio Input Events
    # =========================================================================

    if event_type == "input_audio_buffer.committed":
        return VoiceEvent(
            type=VoiceEventType.AUDIO_COMMITTED,
            metadata={
                "item_id": raw.get("item_id"),
                "previous_item_id": raw.get("previous_item_id"),
            },
            raw_event=raw,
        )

    if event_type == "input_audio_buffer.cleared":
        return VoiceEvent(
            type=VoiceEventType.AUDIO_CLEARED,
            raw_event=raw,
        )

    if event_type == "input_audio_buffer.speech_started":
        return VoiceEvent(
            type=VoiceEventType.SPEECH_STARTED,
            metadata={"item_id": raw.get("item_id")},
            raw_event=raw,
        )

    if event_type == "input_audio_buffer.speech_stopped":
        return VoiceEvent(
            type=VoiceEventType.SPEECH_ENDED,
            metadata={"item_id": raw.get("item_id")},
            raw_event=raw,
        )

    # =========================================================================
    # Text/Transcript Events (FIXED: Both map to TRANSCRIPT with is_delta flag)
    # =========================================================================

    if event_type == "response.output_audio_transcript.delta":
        return VoiceEvent(
            type=VoiceEventType.TRANSCRIPT,
            data=raw.get("delta", ""),
            metadata={
                "response_id": raw.get("response_id"),
                "item_id": raw.get("item_id"),
                "is_delta": True,
            },
            raw_event=raw,
        )

    if event_type == "response.output_audio_transcript.done":
        # FIXED: Was TEXT_DONE, should be TRANSCRIPT with is_delta=False
        return VoiceEvent(
            type=VoiceEventType.TRANSCRIPT,
            data=raw.get("transcript", ""),
            metadata={
                "response_id": raw.get("response_id"),
                "item_id": raw.get("item_id"),
                "is_delta": False,  # Final transcript
            },
            raw_event=raw,
        )

    if event_type == "conversation.item.input_audio_transcription.completed":
        return VoiceEvent(
            type=VoiceEventType.INPUT_TRANSCRIPT,
            data=raw.get("transcript", ""),
            metadata={"item_id": raw.get("item_id")},
            raw_event=raw,
        )

    # =========================================================================
    # Response Lifecycle Events
    # =========================================================================

    if event_type == "response.created":
        response = raw.get("response", {})
        return VoiceEvent(
            type=VoiceEventType.RESPONSE_STARTED,
            metadata={"response_id": response.get("id")},
            raw_event=raw,
        )

    if event_type == "response.done":
        response = raw.get("response", {})
        return VoiceEvent(
            type=VoiceEventType.RESPONSE_DONE,
            data={
                "status": response.get("status"),
            },
            metadata={"response_id": response.get("id")},
            raw_event=raw,
        )

    if event_type == "response.output_item.added":
        return VoiceEvent(
            type=VoiceEventType.CONVERSATION_ITEM,
            data=raw.get("item"),
            metadata={"response_id": raw.get("response_id")},
            raw_event=raw,
        )

    # =========================================================================
    # Tool Calling Events
    # =========================================================================

    if event_type == "response.function_call_arguments.done":
        return VoiceEvent(
            type=VoiceEventType.TOOL_CALL,
            data={
                "call_id": raw.get("call_id"),
                "name": raw.get("name"),
                "arguments": _safe_json_parse(raw.get("arguments", "{}")),
            },
            metadata={
                "response_id": raw.get("response_id"),
                "item_id": raw.get("item_id"),
            },
            raw_event=raw,
        )

    # =========================================================================
    # Conversation Events
    # =========================================================================

    if event_type == "conversation.item.added":
        return VoiceEvent(
            type=VoiceEventType.CONVERSATION_ITEM,
            data=raw.get("item"),
            metadata={"previous_item_id": raw.get("previous_item_id")},
            raw_event=raw,
        )

    # =========================================================================
    # Error Events (Defensive handling)
    # =========================================================================

    if event_type == "error":
        # Handle both nested and flat error formats
        error = raw.get("error", raw)
        return VoiceEvent(
            type=VoiceEventType.ERROR,
            data={
                "code": error.get("code") or error.get("error_code"),
                "message": error.get("message") or error.get("error_message") or str(error),
                "type": error.get("type") or error.get("error_type"),
            },
            raw_event=raw,
        )

    # Unknown event - log at debug level and return None
    logger.debug("Unhandled Grok event: %s", event_type)
    return None
