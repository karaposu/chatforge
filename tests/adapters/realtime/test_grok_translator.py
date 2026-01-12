"""Unit tests for Grok translator module."""

import base64
import pytest

from chatforge.adapters.realtime.grok.translator import translate_event
from chatforge.ports.realtime_voice import VoiceEventType


class TestSessionEvents:
    """Tests for session lifecycle events."""

    def test_conversation_created(self):
        """Test conversation.created maps to SESSION_CREATED."""
        raw = {
            "type": "conversation.created",
            "conversation": {"id": "conv_123"},
        }
        event = translate_event(raw)

        assert event.type == VoiceEventType.SESSION_CREATED
        assert event.data == {"id": "conv_123"}
        assert event.raw_event == raw

    def test_session_updated(self):
        """Test session.updated maps to SESSION_UPDATED."""
        raw = {
            "type": "session.updated",
            "session": {"voice": "Ara"},
        }
        event = translate_event(raw)

        assert event.type == VoiceEventType.SESSION_UPDATED
        assert event.data == {"voice": "Ara"}


class TestAudioOutputEvents:
    """Tests for audio output events."""

    def test_audio_delta(self):
        """Test response.output_audio.delta maps to AUDIO_CHUNK."""
        audio_bytes = b"\x00\x01\x02\x03"
        raw = {
            "type": "response.output_audio.delta",
            "delta": base64.b64encode(audio_bytes).decode("ascii"),
            "response_id": "resp_123",
            "item_id": "item_456",
            "output_index": 0,
            "content_index": 0,
        }
        event = translate_event(raw)

        assert event.type == VoiceEventType.AUDIO_CHUNK
        assert event.data == audio_bytes
        assert event.metadata["response_id"] == "resp_123"
        assert event.metadata["item_id"] == "item_456"

    def test_audio_delta_invalid_base64(self, caplog):
        """Test invalid base64 in audio delta returns None."""
        raw = {
            "type": "response.output_audio.delta",
            "delta": "not-valid-base64!!!",
        }
        event = translate_event(raw)

        assert event is None
        assert "Invalid base64" in caplog.text

    def test_audio_done(self):
        """Test response.output_audio.done maps to AUDIO_DONE."""
        raw = {
            "type": "response.output_audio.done",
            "response_id": "resp_123",
            "item_id": "item_456",
        }
        event = translate_event(raw)

        assert event.type == VoiceEventType.AUDIO_DONE
        assert event.metadata["response_id"] == "resp_123"
        assert event.metadata["item_id"] == "item_456"


class TestAudioInputEvents:
    """Tests for audio input events."""

    def test_audio_committed(self):
        """Test input_audio_buffer.committed maps to AUDIO_COMMITTED."""
        raw = {
            "type": "input_audio_buffer.committed",
            "item_id": "item_123",
            "previous_item_id": "item_122",
        }
        event = translate_event(raw)

        assert event.type == VoiceEventType.AUDIO_COMMITTED
        assert event.metadata["item_id"] == "item_123"
        assert event.metadata["previous_item_id"] == "item_122"

    def test_audio_cleared(self):
        """Test input_audio_buffer.cleared maps to AUDIO_CLEARED."""
        raw = {"type": "input_audio_buffer.cleared"}
        event = translate_event(raw)

        assert event.type == VoiceEventType.AUDIO_CLEARED

    def test_speech_started(self):
        """Test speech_started maps to SPEECH_STARTED."""
        raw = {
            "type": "input_audio_buffer.speech_started",
            "item_id": "item_123",
        }
        event = translate_event(raw)

        assert event.type == VoiceEventType.SPEECH_STARTED
        assert event.metadata["item_id"] == "item_123"

    def test_speech_stopped(self):
        """Test speech_stopped maps to SPEECH_ENDED."""
        raw = {
            "type": "input_audio_buffer.speech_stopped",
            "item_id": "item_123",
        }
        event = translate_event(raw)

        assert event.type == VoiceEventType.SPEECH_ENDED
        assert event.metadata["item_id"] == "item_123"


class TestTranscriptEvents:
    """Tests for transcript events - critical fix verification."""

    def test_transcript_delta(self):
        """Test transcript delta maps to TRANSCRIPT with is_delta=True."""
        raw = {
            "type": "response.output_audio_transcript.delta",
            "delta": "Hello ",
            "response_id": "resp_123",
            "item_id": "item_456",
        }
        event = translate_event(raw)

        assert event.type == VoiceEventType.TRANSCRIPT
        assert event.data == "Hello "
        assert event.metadata["is_delta"] is True
        assert event.metadata["response_id"] == "resp_123"

    def test_transcript_done(self):
        """Test transcript done maps to TRANSCRIPT with is_delta=False (NOT TEXT_DONE)."""
        raw = {
            "type": "response.output_audio_transcript.done",
            "transcript": "Hello, how can I help you?",
            "response_id": "resp_123",
            "item_id": "item_456",
        }
        event = translate_event(raw)

        # CRITICAL: Should be TRANSCRIPT, not TEXT_DONE
        assert event.type == VoiceEventType.TRANSCRIPT
        assert event.data == "Hello, how can I help you?"
        assert event.metadata["is_delta"] is False
        assert event.metadata["response_id"] == "resp_123"

    def test_input_transcription_completed(self):
        """Test input transcription maps to INPUT_TRANSCRIPT."""
        raw = {
            "type": "conversation.item.input_audio_transcription.completed",
            "transcript": "What's the weather?",
            "item_id": "item_123",
        }
        event = translate_event(raw)

        assert event.type == VoiceEventType.INPUT_TRANSCRIPT
        assert event.data == "What's the weather?"
        assert event.metadata["item_id"] == "item_123"


class TestResponseLifecycleEvents:
    """Tests for response lifecycle events."""

    def test_response_created(self):
        """Test response.created maps to RESPONSE_STARTED."""
        raw = {
            "type": "response.created",
            "response": {"id": "resp_123"},
        }
        event = translate_event(raw)

        assert event.type == VoiceEventType.RESPONSE_STARTED
        assert event.metadata["response_id"] == "resp_123"

    def test_response_done(self):
        """Test response.done maps to RESPONSE_DONE."""
        raw = {
            "type": "response.done",
            "response": {
                "id": "resp_123",
                "status": "completed",
            },
        }
        event = translate_event(raw)

        assert event.type == VoiceEventType.RESPONSE_DONE
        assert event.data["status"] == "completed"
        assert event.metadata["response_id"] == "resp_123"

    def test_output_item_added(self):
        """Test output_item.added maps to CONVERSATION_ITEM."""
        raw = {
            "type": "response.output_item.added",
            "item": {"id": "item_123", "type": "message"},
            "response_id": "resp_123",
        }
        event = translate_event(raw)

        assert event.type == VoiceEventType.CONVERSATION_ITEM
        assert event.data["id"] == "item_123"
        assert event.metadata["response_id"] == "resp_123"


class TestToolCallingEvents:
    """Tests for tool/function calling events."""

    def test_function_call_arguments_done(self):
        """Test function_call_arguments.done maps to TOOL_CALL."""
        raw = {
            "type": "response.function_call_arguments.done",
            "call_id": "call_123",
            "name": "get_weather",
            "arguments": '{"city": "Tokyo"}',
            "response_id": "resp_123",
            "item_id": "item_456",
        }
        event = translate_event(raw)

        assert event.type == VoiceEventType.TOOL_CALL
        assert event.data["call_id"] == "call_123"
        assert event.data["name"] == "get_weather"
        assert event.data["arguments"] == {"city": "Tokyo"}
        assert event.metadata["response_id"] == "resp_123"

    def test_function_call_invalid_json_arguments(self):
        """Test invalid JSON arguments are kept as string."""
        raw = {
            "type": "response.function_call_arguments.done",
            "call_id": "call_123",
            "name": "get_weather",
            "arguments": "not-valid-json",
        }
        event = translate_event(raw)

        assert event.type == VoiceEventType.TOOL_CALL
        assert event.data["arguments"] == "not-valid-json"


class TestConversationEvents:
    """Tests for conversation item events."""

    def test_conversation_item_added(self):
        """Test conversation.item.added maps to CONVERSATION_ITEM."""
        raw = {
            "type": "conversation.item.added",
            "item": {"id": "item_123", "type": "message"},
            "previous_item_id": "item_122",
        }
        event = translate_event(raw)

        assert event.type == VoiceEventType.CONVERSATION_ITEM
        assert event.data["id"] == "item_123"
        assert event.metadata["previous_item_id"] == "item_122"


class TestErrorEvents:
    """Tests for error event handling."""

    def test_error_nested_format(self):
        """Test nested error format parsing."""
        raw = {
            "type": "error",
            "error": {
                "code": "invalid_request",
                "message": "Bad request",
                "type": "validation_error",
            },
        }
        event = translate_event(raw)

        assert event.type == VoiceEventType.ERROR
        assert event.data["code"] == "invalid_request"
        assert event.data["message"] == "Bad request"
        assert event.data["type"] == "validation_error"

    def test_error_flat_format(self):
        """Test flat error format parsing (defensive)."""
        # Note: "type" is reserved for event type, so flat errors use error_*
        raw = {
            "type": "error",
            "error": {
                "error_code": "rate_limited",
                "error_message": "Too many requests",
                "error_type": "rate_limit",
            }
        }
        event = translate_event(raw)

        assert event.type == VoiceEventType.ERROR
        assert event.data["code"] == "rate_limited"
        assert event.data["message"] == "Too many requests"
        assert event.data["type"] == "rate_limit"

    def test_error_minimal_format(self):
        """Test minimal error format with fallback."""
        raw = {
            "type": "error",
            "error": {"something": "unexpected"},
        }
        event = translate_event(raw)

        assert event.type == VoiceEventType.ERROR
        # Should have stringified error as fallback
        assert "unexpected" in event.data["message"]


class TestUnknownEvents:
    """Tests for unknown event handling."""

    def test_unknown_event_returns_none(self, caplog):
        """Test unknown event types return None."""
        import logging
        # Enable DEBUG level to capture the log message
        with caplog.at_level(logging.DEBUG):
            raw = {"type": "some.unknown.event"}
            event = translate_event(raw)

            assert event is None
            assert "Unhandled Grok event" in caplog.text

    def test_empty_type_returns_none(self):
        """Test empty type returns None."""
        raw = {"type": ""}
        event = translate_event(raw)

        assert event is None

    def test_missing_type_returns_none(self):
        """Test missing type returns None."""
        raw = {"data": "something"}
        event = translate_event(raw)

        assert event is None


class TestEventMetadata:
    """Tests for event metadata consistency."""

    def test_all_events_have_raw_event(self):
        """Test all events include raw_event for debugging."""
        events_to_test = [
            {"type": "conversation.created", "conversation": {}},
            {"type": "session.updated", "session": {}},
            {"type": "input_audio_buffer.cleared"},
            {"type": "response.created", "response": {}},
            {"type": "response.done", "response": {}},
            {"type": "error", "error": {"message": "test"}},
        ]

        for raw in events_to_test:
            event = translate_event(raw)
            assert event is not None, f"Event should not be None for {raw['type']}"
            assert event.raw_event == raw, f"raw_event missing for {raw['type']}"

    def test_events_have_timestamps(self):
        """Test all events have timestamps."""
        raw = {"type": "conversation.created", "conversation": {}}
        event = translate_event(raw)

        assert event.timestamp is not None
        assert event.timestamp > 0
