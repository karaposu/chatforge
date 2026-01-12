"""Tests for GrokRealtimeAdapter.

Unit tests can run without API key.
Integration tests require XAI_API_KEY environment variable.
"""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from chatforge.adapters.realtime import GrokRealtimeAdapter
from chatforge.adapters.realtime.grok import messages
from chatforge.ports.realtime_voice import (
    VoiceEventType,
    VoiceSessionConfig,
    RealtimeSessionError,
    ToolDefinition,
)


# =============================================================================
# Unit Tests (no API key required)
# =============================================================================


class TestGrokAdapterConstruction:
    """Unit tests for adapter construction."""

    def test_requires_api_key_or_token(self):
        """Test that either api_key or ephemeral_token is required."""
        with pytest.raises(ValueError, match="Either api_key or ephemeral_token"):
            GrokRealtimeAdapter()

    def test_accepts_api_key(self):
        """Test construction with API key."""
        adapter = GrokRealtimeAdapter(api_key="test-key")
        assert adapter._auth_token == "test-key"

    def test_accepts_ephemeral_token(self):
        """Test construction with ephemeral token."""
        adapter = GrokRealtimeAdapter(ephemeral_token="eph-token")
        assert adapter._auth_token == "eph-token"

    def test_ephemeral_token_takes_precedence(self):
        """Test ephemeral token is preferred over API key."""
        adapter = GrokRealtimeAdapter(
            api_key="api-key",
            ephemeral_token="eph-token"
        )
        assert adapter._auth_token == "eph-token"

    def test_default_settings(self):
        """Test default constructor settings."""
        adapter = GrokRealtimeAdapter(api_key="test")
        assert adapter._connect_timeout == 30.0
        assert adapter._auto_reconnect is True
        assert adapter._max_reconnect_attempts == 5
        assert adapter._enable_metrics is True

    def test_custom_settings(self):
        """Test custom constructor settings."""
        adapter = GrokRealtimeAdapter(
            api_key="test",
            connect_timeout=60.0,
            auto_reconnect=False,
            max_reconnect_attempts=3,
            enable_metrics=False,
        )
        assert adapter._connect_timeout == 60.0
        assert adapter._auto_reconnect is False
        assert adapter._max_reconnect_attempts == 3
        assert adapter._enable_metrics is False


class TestGrokAdapterProperties:
    """Unit tests for adapter properties."""

    def test_provider_name(self):
        """Test provider_name returns 'grok'."""
        adapter = GrokRealtimeAdapter(api_key="test")
        assert adapter.provider_name == "grok"

    def test_is_connected_initially_false(self):
        """Test is_connected is False before connection."""
        adapter = GrokRealtimeAdapter(api_key="test")
        assert adapter.is_connected() is False


class TestGrokAdapterCapabilities:
    """Unit tests for capabilities."""

    def test_capabilities(self):
        """Test capabilities are correct for Grok."""
        adapter = GrokRealtimeAdapter(api_key="test")
        caps = adapter.get_capabilities()

        assert caps.provider_name == "grok"
        assert caps.supports_server_vad is True
        assert caps.supports_function_calling is True
        assert caps.supports_interruption is False  # Not documented
        assert caps.supports_transcription is True
        assert caps.supports_input_transcription is True
        assert caps.supports_conversation_reset is False  # Not documented
        assert "Ara" in caps.available_voices
        assert "Rex" in caps.available_voices
        assert caps.available_models == []  # Single implicit model

    def test_all_grok_voices_available(self):
        """Test all Grok voices are in capabilities."""
        adapter = GrokRealtimeAdapter(api_key="test")
        caps = adapter.get_capabilities()

        expected_voices = {"Ara", "Rex", "Sal", "Eve", "Leo"}
        assert set(caps.available_voices) == expected_voices


class TestGrokAdapterStats:
    """Unit tests for stats."""

    def test_stats_empty_before_connection(self):
        """Test get_stats returns empty dict before connection."""
        adapter = GrokRealtimeAdapter(api_key="test")
        assert adapter.get_stats() == {}


class TestGrokAdapterResetConversation:
    """Unit tests for reset_conversation."""

    @pytest.mark.asyncio
    async def test_reset_conversation_not_implemented(self):
        """Test reset_conversation raises NotImplementedError."""
        adapter = GrokRealtimeAdapter(api_key="test")

        with pytest.raises(NotImplementedError, match="does not support conversation reset"):
            await adapter.reset_conversation()


class TestGrokAdapterSessionNotConnected:
    """Unit tests for operations when not connected."""

    @pytest.mark.asyncio
    async def test_send_audio_not_connected(self):
        """Test send_audio raises when not connected."""
        adapter = GrokRealtimeAdapter(api_key="test")

        with pytest.raises(RealtimeSessionError, match="Not connected"):
            await adapter.send_audio(b"\x00\x01")

    @pytest.mark.asyncio
    async def test_commit_audio_not_connected(self):
        """Test commit_audio raises when not connected."""
        adapter = GrokRealtimeAdapter(api_key="test")

        with pytest.raises(RealtimeSessionError, match="Not connected"):
            await adapter.commit_audio()

    @pytest.mark.asyncio
    async def test_send_text_not_connected(self):
        """Test send_text raises when not connected."""
        adapter = GrokRealtimeAdapter(api_key="test")

        with pytest.raises(RealtimeSessionError, match="Not connected"):
            await adapter.send_text("Hello")

    @pytest.mark.asyncio
    async def test_create_response_not_connected(self):
        """Test create_response raises when not connected."""
        adapter = GrokRealtimeAdapter(api_key="test")

        with pytest.raises(RealtimeSessionError, match="Not connected"):
            await adapter.create_response()


class TestGrokAdapterCommitAudioVADMode:
    """Unit tests for VAD-aware commit_audio behavior."""

    @pytest.mark.asyncio
    async def test_commit_uses_server_vad_message(self):
        """Test commit uses conversation.item.commit for server VAD."""
        adapter = GrokRealtimeAdapter(api_key="test")
        adapter._config = VoiceSessionConfig(vad_mode="server")

        # Mock the websocket
        mock_ws = MagicMock()
        mock_ws.is_connected = True
        mock_ws.send_json = AsyncMock()
        adapter._ws = mock_ws

        await adapter.commit_audio()

        # Should use conversation.item.commit
        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["type"] == "conversation.item.commit"

    @pytest.mark.asyncio
    async def test_commit_uses_client_vad_message(self):
        """Test commit uses input_audio_buffer.commit for client VAD."""
        adapter = GrokRealtimeAdapter(api_key="test")
        adapter._config = VoiceSessionConfig(vad_mode="client")

        mock_ws = MagicMock()
        mock_ws.is_connected = True
        mock_ws.send_json = AsyncMock()
        adapter._ws = mock_ws

        await adapter.commit_audio()

        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["type"] == "input_audio_buffer.commit"

    @pytest.mark.asyncio
    async def test_commit_uses_none_vad_message(self):
        """Test commit uses input_audio_buffer.commit for none VAD."""
        adapter = GrokRealtimeAdapter(api_key="test")
        adapter._config = VoiceSessionConfig(vad_mode="none")

        mock_ws = MagicMock()
        mock_ws.is_connected = True
        mock_ws.send_json = AsyncMock()
        adapter._ws = mock_ws

        await adapter.commit_audio()

        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["type"] == "input_audio_buffer.commit"


class TestGrokAdapterCreateResponseModalities:
    """Unit tests for create_response modalities handling."""

    @pytest.mark.asyncio
    async def test_create_response_uses_config_modalities(self):
        """Test create_response passes modalities from config."""
        adapter = GrokRealtimeAdapter(api_key="test")
        adapter._config = VoiceSessionConfig(modalities=["text"])

        mock_ws = MagicMock()
        mock_ws.is_connected = True
        mock_ws.send_json = AsyncMock()
        adapter._ws = mock_ws

        await adapter.create_response()

        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["response"]["modalities"] == ["text"]

    @pytest.mark.asyncio
    async def test_create_response_default_modalities(self):
        """Test create_response uses default modalities without config."""
        adapter = GrokRealtimeAdapter(api_key="test")
        adapter._config = None  # No config

        mock_ws = MagicMock()
        mock_ws.is_connected = True
        mock_ws.send_json = AsyncMock()
        adapter._ws = mock_ws

        await adapter.create_response()

        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["response"]["modalities"] == ["text", "audio"]


class TestGrokAdapterToolResult:
    """Unit tests for send_tool_result."""

    @pytest.mark.asyncio
    async def test_send_tool_result_success(self):
        """Test send_tool_result without error."""
        adapter = GrokRealtimeAdapter(api_key="test")

        mock_ws = MagicMock()
        mock_ws.is_connected = True
        mock_ws.send_json = AsyncMock()
        adapter._ws = mock_ws

        await adapter.send_tool_result("call_123", '{"result": "sunny"}', is_error=False)

        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["item"]["output"] == '{"result": "sunny"}'

    @pytest.mark.asyncio
    async def test_send_tool_result_error(self):
        """Test send_tool_result wraps error in JSON."""
        adapter = GrokRealtimeAdapter(api_key="test")

        mock_ws = MagicMock()
        mock_ws.is_connected = True
        mock_ws.send_json = AsyncMock()
        adapter._ws = mock_ws

        await adapter.send_tool_result("call_123", "Something went wrong", is_error=True)

        call_args = mock_ws.send_json.call_args[0][0]
        import json
        output = json.loads(call_args["item"]["output"])
        assert output == {"error": "Something went wrong"}


class TestGrokAdapterInterrupt:
    """Unit tests for interrupt behavior."""

    @pytest.mark.asyncio
    async def test_interrupt_logs_warning(self, caplog):
        """Test interrupt logs warning about unsupported operation."""
        adapter = GrokRealtimeAdapter(api_key="test")

        mock_ws = MagicMock()
        mock_ws.is_connected = True
        mock_ws.send_json = AsyncMock()
        adapter._ws = mock_ws

        await adapter.interrupt()

        assert "may not be supported" in caplog.text

    @pytest.mark.asyncio
    async def test_cancel_response_logs_warning(self, caplog):
        """Test cancel_response logs warning about unsupported operation."""
        adapter = GrokRealtimeAdapter(api_key="test")

        mock_ws = MagicMock()
        mock_ws.is_connected = True
        mock_ws.send_json = AsyncMock()
        adapter._ws = mock_ws

        await adapter.cancel_response("resp_123")

        assert "may not be supported" in caplog.text


class TestGrokAdapterContextManager:
    """Unit tests for async context manager."""

    @pytest.mark.asyncio
    async def test_context_manager_enter_exit(self):
        """Test async context manager works."""
        async with GrokRealtimeAdapter(api_key="test") as adapter:
            assert adapter is not None
            assert isinstance(adapter, GrokRealtimeAdapter)


# =============================================================================
# Integration Tests (require XAI_API_KEY)
# =============================================================================


# Skip all integration tests if no API key
pytestmark_integration = pytest.mark.skipif(
    not os.environ.get("XAI_API_KEY"),
    reason="XAI_API_KEY not set"
)


@pytest.fixture
def xai_api_key():
    """Get xAI API key from environment."""
    return os.environ.get("XAI_API_KEY")


@pytest.fixture
def grok_adapter(xai_api_key):
    """Create Grok adapter with API key."""
    if not xai_api_key:
        pytest.skip("XAI_API_KEY not set")
    return GrokRealtimeAdapter(api_key=xai_api_key)


@pytest.mark.skipif(not os.environ.get("XAI_API_KEY"), reason="XAI_API_KEY not set")
class TestGrokAdapterIntegrationLifecycle:
    """Integration tests for connection lifecycle."""

    @pytest.mark.asyncio
    async def test_connect_disconnect(self, grok_adapter):
        """Test basic connect/disconnect."""
        async with grok_adapter:
            await grok_adapter.connect(VoiceSessionConfig(voice="Ara"))
            assert grok_adapter.is_connected()

            await grok_adapter.disconnect()
            assert not grok_adapter.is_connected()

    @pytest.mark.asyncio
    async def test_connect_with_system_prompt(self, grok_adapter):
        """Test connection with system prompt."""
        async with grok_adapter:
            config = VoiceSessionConfig(
                voice="Ara",
                system_prompt="You are a helpful assistant.",
            )
            await grok_adapter.connect(config)
            assert grok_adapter.is_connected()


@pytest.mark.skipif(not os.environ.get("XAI_API_KEY"), reason="XAI_API_KEY not set")
class TestGrokAdapterIntegrationText:
    """Integration tests for text operations."""

    @pytest.mark.asyncio
    async def test_send_text_gets_response(self, grok_adapter):
        """Test send_text triggers AI response."""
        async with grok_adapter:
            await grok_adapter.connect(VoiceSessionConfig(voice="Ara"))

            await grok_adapter.send_text("Say hello in one word.")

            # Collect events until response done
            events = []
            async for event in grok_adapter.events():
                events.append(event)
                if event.type == VoiceEventType.RESPONSE_DONE:
                    break
                # Timeout safety
                if len(events) > 100:
                    break

            # Should have received audio and transcript
            event_types = {e.type for e in events}
            assert VoiceEventType.RESPONSE_STARTED in event_types
            assert VoiceEventType.AUDIO_CHUNK in event_types or VoiceEventType.TRANSCRIPT in event_types


@pytest.mark.skipif(not os.environ.get("XAI_API_KEY"), reason="XAI_API_KEY not set")
class TestGrokAdapterIntegrationTranscript:
    """Integration tests for transcript handling."""

    @pytest.mark.asyncio
    async def test_transcript_events_have_is_delta(self, grok_adapter):
        """Test transcript events include is_delta metadata."""
        async with grok_adapter:
            await grok_adapter.connect(VoiceSessionConfig(voice="Ara"))

            await grok_adapter.send_text("Say 'test' and nothing else.")

            transcript_events = []
            async for event in grok_adapter.events():
                if event.type == VoiceEventType.TRANSCRIPT:
                    transcript_events.append(event)
                if event.type == VoiceEventType.RESPONSE_DONE:
                    break
                if len(transcript_events) > 50:
                    break

            # All transcript events should have is_delta
            for event in transcript_events:
                assert "is_delta" in event.metadata


@pytest.mark.skipif(not os.environ.get("XAI_API_KEY"), reason="XAI_API_KEY not set")
class TestGrokAdapterIntegrationEphemeralToken:
    """Integration tests for ephemeral token support."""

    @pytest.mark.asyncio
    async def test_ephemeral_token_creation(self, xai_api_key):
        """Test creating adapter with ephemeral token."""
        adapter = await GrokRealtimeAdapter.with_ephemeral_token(xai_api_key)

        # Token should be different from original API key
        assert adapter._auth_token is not None
        assert adapter._auth_token != xai_api_key

    @pytest.mark.asyncio
    async def test_ephemeral_token_connection(self, xai_api_key):
        """Test connecting with ephemeral token."""
        adapter = await GrokRealtimeAdapter.with_ephemeral_token(xai_api_key)

        async with adapter:
            await adapter.connect(VoiceSessionConfig(voice="Ara"))
            assert adapter.is_connected()
