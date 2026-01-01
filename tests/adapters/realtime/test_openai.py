"""Tests for OpenAIRealtimeAdapter.

These are integration tests that require a real API key.
Set OPENAI_API_KEY environment variable to run.
"""

import os
import pytest

from chatforge.adapters.realtime import OpenAIRealtimeAdapter
from chatforge.ports.realtime_voice import (
    VoiceEventType,
    VoiceSessionConfig,
    RealtimeAuthenticationError,
    RealtimeSessionError,
)


# Skip all tests if no API key
pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set"
)


@pytest.fixture
def api_key():
    """Get API key from environment."""
    return os.environ["OPENAI_API_KEY"]


@pytest.fixture
def adapter(api_key):
    """Create OpenAI adapter."""
    return OpenAIRealtimeAdapter(api_key=api_key)


class TestOpenAIAdapterLifecycle:
    """Integration tests for connection lifecycle."""

    @pytest.mark.asyncio
    async def test_connect_disconnect(self, adapter):
        """Test basic connect/disconnect."""
        async with adapter:
            await adapter.connect(VoiceSessionConfig())
            assert adapter.is_connected()

            # Should receive session created event
            async for event in adapter.events():
                if event.type == VoiceEventType.SESSION_CREATED:
                    break

            await adapter.disconnect()
            assert not adapter.is_connected()

    @pytest.mark.asyncio
    async def test_invalid_api_key(self):
        """Test authentication error with bad key."""
        adapter = OpenAIRealtimeAdapter(api_key="invalid-key")

        async with adapter:
            with pytest.raises(RealtimeAuthenticationError):
                await adapter.connect(VoiceSessionConfig())


class TestOpenAIAdapterCapabilities:
    """Tests for capabilities."""

    def test_capabilities(self, adapter):
        """Test capabilities are correct."""
        caps = adapter.get_capabilities()

        assert caps.provider_name == "openai"
        assert caps.supports_server_vad
        assert caps.supports_function_calling
        assert "alloy" in caps.available_voices


class TestOpenAIAdapterMetrics:
    """Tests for metrics."""

    @pytest.mark.asyncio
    async def test_metrics_after_connection(self, adapter):
        """Test metrics are tracked."""
        async with adapter:
            await adapter.connect(VoiceSessionConfig())

            stats = adapter.get_stats()
            assert stats.get("connects", 0) >= 1

            await adapter.disconnect()


class TestOpenAIAdapterSessionUpdate:
    """Tests for session update validation."""

    @pytest.mark.asyncio
    async def test_cannot_change_model_mid_session(self, adapter):
        """Test changing model mid-session raises error."""
        async with adapter:
            await adapter.connect(VoiceSessionConfig(model="gpt-4o-realtime-preview"))

            with pytest.raises(RealtimeSessionError, match="Cannot change model"):
                await adapter.update_session(VoiceSessionConfig(model="different-model"))

            await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_cannot_change_input_format(self, adapter):
        """Test changing input format mid-session raises error."""
        async with adapter:
            await adapter.connect(VoiceSessionConfig(input_format="pcm16"))

            with pytest.raises(RealtimeSessionError, match="Cannot change input format"):
                await adapter.update_session(VoiceSessionConfig(input_format="g711_ulaw"))

            await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_cannot_change_output_format(self, adapter):
        """Test changing output format mid-session raises error."""
        async with adapter:
            await adapter.connect(VoiceSessionConfig(output_format="pcm16"))

            with pytest.raises(RealtimeSessionError, match="Cannot change output format"):
                await adapter.update_session(VoiceSessionConfig(output_format="g711_alaw"))

            await adapter.disconnect()


class TestOpenAIAdapterTextInput:
    """Tests for text input operations."""

    @pytest.mark.asyncio
    async def test_send_text_with_auto_response(self, adapter):
        """Test send_text triggers response by default."""
        async with adapter:
            await adapter.connect(VoiceSessionConfig())

            # send_text should work and trigger response
            await adapter.send_text("Hello")

            # Should receive response events
            async for event in adapter.events():
                if event.type == VoiceEventType.RESPONSE_STARTED:
                    # Got response, cancel and exit
                    await adapter.interrupt()
                    break

            await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_add_text_item_no_auto_response(self, adapter):
        """Test add_text_item doesn't trigger response."""
        async with adapter:
            await adapter.connect(VoiceSessionConfig())

            # add_text_item should not trigger response
            await adapter.add_text_item("Context 1")
            await adapter.add_text_item("Context 2")

            # Now explicitly trigger response
            await adapter.create_response()

            # Should receive response
            async for event in adapter.events():
                if event.type == VoiceEventType.RESPONSE_STARTED:
                    await adapter.interrupt()
                    break

            await adapter.disconnect()
