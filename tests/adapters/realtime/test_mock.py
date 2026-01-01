"""Tests for MockRealtimeAdapter."""

import pytest

from chatforge.adapters.realtime import MockRealtimeAdapter
from chatforge.ports.realtime_voice import (
    VoiceEvent,
    VoiceEventType,
    VoiceSessionConfig,
    RealtimeSessionError,
)


class TestMockAdapterLifecycle:
    """Tests for connection lifecycle."""

    @pytest.mark.asyncio
    async def test_connect_disconnect(self, mock_adapter, default_config):
        """Test basic connect/disconnect."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)
            assert mock_adapter.is_connected()

            await mock_adapter.disconnect()
            assert not mock_adapter.is_connected()

    @pytest.mark.asyncio
    async def test_context_manager_disconnect(self, mock_adapter, default_config):
        """Test context manager disconnects on exit."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

        assert not mock_adapter.is_connected()

    @pytest.mark.asyncio
    async def test_double_connect_raises(self, mock_adapter, default_config):
        """Test connecting twice raises error."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

            with pytest.raises(RealtimeSessionError):
                await mock_adapter.connect(default_config)


class TestMockAdapterAudio:
    """Tests for audio operations."""

    @pytest.mark.asyncio
    async def test_send_audio(self, mock_adapter, default_config):
        """Test sending audio chunks."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

            await mock_adapter.send_audio(b"\x00\x01\x02")
            await mock_adapter.send_audio(b"\x03\x04\x05")

            assert len(mock_adapter.sent_audio) == 2
            assert mock_adapter.get_total_sent_audio_bytes() == 6

    @pytest.mark.asyncio
    async def test_commit_audio(self, mock_adapter, default_config):
        """Test committing audio buffer."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

            await mock_adapter.commit_audio()
            await mock_adapter.commit_audio()

            assert mock_adapter.committed_count == 2

    @pytest.mark.asyncio
    async def test_clear_audio(self, mock_adapter, default_config):
        """Test clearing audio buffer."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

            await mock_adapter.clear_audio()

            assert mock_adapter.cleared_count == 1


class TestMockAdapterEvents:
    """Tests for event streaming."""

    @pytest.mark.asyncio
    async def test_receive_audio_response(self, mock_adapter, default_config):
        """Test receiving audio response events."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

            # Queue audio response
            await mock_adapter.queue_audio_response(b"x" * 9600, chunk_size=4800)

            # Collect events
            events = []
            async for event in mock_adapter.events():
                events.append(event)
                if event.type == VoiceEventType.RESPONSE_DONE:
                    await mock_adapter.disconnect()
                    break

            types = [e.type for e in events]
            assert VoiceEventType.RESPONSE_STARTED in types
            assert VoiceEventType.AUDIO_CHUNK in types
            assert VoiceEventType.RESPONSE_DONE in types

    @pytest.mark.asyncio
    async def test_tool_call_flow(self, mock_adapter, config_with_tools):
        """Test tool calling flow."""
        async with mock_adapter:
            await mock_adapter.connect(config_with_tools)

            # Queue tool call
            await mock_adapter.queue_tool_call(
                call_id="call_123",
                name="get_weather",
                arguments={"city": "SF"},
            )

            # Handle tool call
            async for event in mock_adapter.events():
                if event.type == VoiceEventType.TOOL_CALL:
                    await mock_adapter.send_tool_result(
                        call_id=event.data["call_id"],
                        result='{"temp": 72}',
                    )
                    await mock_adapter.disconnect()
                    break

            assert len(mock_adapter.tool_results) == 1
            assert mock_adapter.tool_results[0] == ("call_123", '{"temp": 72}', False)

    @pytest.mark.asyncio
    async def test_interrupt(self, mock_adapter, default_config):
        """Test interrupting response."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

            await mock_adapter.interrupt()

            assert mock_adapter.interrupt_count == 1


class TestMockAdapterText:
    """Tests for text operations."""

    @pytest.mark.asyncio
    async def test_send_text(self, mock_adapter, default_config):
        """Test sending text messages."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

            await mock_adapter.send_text("Hello")
            await mock_adapter.send_text("World")

            assert mock_adapter.sent_text == ["Hello", "World"]

    @pytest.mark.asyncio
    async def test_add_text_item(self, mock_adapter, default_config):
        """Test adding text items without triggering response."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

            await mock_adapter.add_text_item("Context 1")
            await mock_adapter.add_text_item("Context 2")

            # add_text_item should not trigger response
            assert len(mock_adapter.response_requests) == 0
            assert mock_adapter.sent_text == ["Context 1", "Context 2"]

    @pytest.mark.asyncio
    async def test_send_text_triggers_response(self, mock_adapter, default_config):
        """Test send_text triggers response by default."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

            await mock_adapter.send_text("Hello", trigger_response=True)

            # Should have triggered response
            assert len(mock_adapter.response_requests) == 1

    @pytest.mark.asyncio
    async def test_send_text_no_trigger(self, mock_adapter, default_config):
        """Test send_text with trigger_response=False."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

            await mock_adapter.send_text("Hello", trigger_response=False)

            # Should NOT have triggered response
            assert len(mock_adapter.response_requests) == 0


class TestMockAdapterNotConnected:
    """Tests for operations when not connected."""

    @pytest.mark.asyncio
    async def test_send_audio_not_connected(self, mock_adapter):
        """Test send_audio raises when not connected."""
        with pytest.raises(RealtimeSessionError):
            await mock_adapter.send_audio(b"\x00")

    @pytest.mark.asyncio
    async def test_send_text_not_connected(self, mock_adapter):
        """Test send_text raises when not connected."""
        with pytest.raises(RealtimeSessionError):
            await mock_adapter.send_text("hello")


class TestConfigValidation:
    """Tests for VoiceSessionConfig validation."""

    def test_valid_config(self):
        """Test valid config creation."""
        config = VoiceSessionConfig(
            temperature=0.5,
            vad_threshold=0.7,
            sample_rate=24000,
        )
        assert config.temperature == 0.5
        assert config.vad_threshold == 0.7

    def test_invalid_temperature_low(self):
        """Test temperature below 0 raises error."""
        with pytest.raises(ValueError, match="temperature must be 0.0-2.0"):
            VoiceSessionConfig(temperature=-0.1)

    def test_invalid_temperature_high(self):
        """Test temperature above 2 raises error."""
        with pytest.raises(ValueError, match="temperature must be 0.0-2.0"):
            VoiceSessionConfig(temperature=2.5)

    def test_invalid_vad_threshold(self):
        """Test vad_threshold outside 0-1 raises error."""
        with pytest.raises(ValueError, match="vad_threshold must be 0.0-1.0"):
            VoiceSessionConfig(vad_threshold=1.5)

    def test_invalid_sample_rate(self):
        """Test non-positive sample_rate raises error."""
        with pytest.raises(ValueError, match="sample_rate must be positive"):
            VoiceSessionConfig(sample_rate=0)

    def test_invalid_vad_silence_ms(self):
        """Test negative vad_silence_ms raises error."""
        with pytest.raises(ValueError, match="vad_silence_ms must be non-negative"):
            VoiceSessionConfig(vad_silence_ms=-100)

    def test_invalid_max_tokens(self):
        """Test non-positive max_tokens raises error."""
        with pytest.raises(ValueError, match="max_tokens must be positive"):
            VoiceSessionConfig(max_tokens=0)


class TestMockAdapterConnectedEvent:
    """Tests for CONNECTED event emission."""

    @pytest.mark.asyncio
    async def test_connected_event_emitted(self, mock_adapter, default_config):
        """Test CONNECTED event is emitted after connect."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

            events = []
            async for event in mock_adapter.events():
                events.append(event)
                if event.type == VoiceEventType.CONNECTED:
                    await mock_adapter.disconnect()
                    break

            types = [e.type for e in events]
            assert VoiceEventType.SESSION_CREATED in types
            assert VoiceEventType.CONNECTED in types


class TestMockAdapterLatencySimulation:
    """Tests for latency simulation."""

    @pytest.mark.asyncio
    async def test_latency_simulation(self, default_config):
        """Test latency simulation works."""
        import time

        mock = MockRealtimeAdapter(simulate_latency_ms=50)

        start = time.monotonic()
        async with mock:
            await mock.connect(default_config)
        elapsed = time.monotonic() - start

        # Should have at least 50ms latency
        assert elapsed >= 0.05


class TestMockAdapterSessionUpdate:
    """Tests for session update operations."""

    @pytest.mark.asyncio
    async def test_update_session(self, mock_adapter, default_config):
        """Test session update emits event."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

            new_config = VoiceSessionConfig(voice="shimmer")
            await mock_adapter.update_session(new_config)

            # Check SESSION_UPDATED was queued
            events = []
            async for event in mock_adapter.events():
                events.append(event)
                if event.type == VoiceEventType.SESSION_UPDATED:
                    await mock_adapter.disconnect()
                    break

            types = [e.type for e in events]
            assert VoiceEventType.SESSION_UPDATED in types


class TestMockAdapterReconnection:
    """Tests for reconnection simulation."""

    @pytest.mark.asyncio
    async def test_simulate_reconnecting(self, mock_adapter, default_config):
        """Test simulating reconnection events."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

            # Simulate reconnecting
            await mock_adapter.queue_event(VoiceEvent(
                type=VoiceEventType.RECONNECTING,
                metadata={"attempt": 1},
            ))

            events = []
            async for event in mock_adapter.events():
                events.append(event)
                if event.type == VoiceEventType.RECONNECTING:
                    await mock_adapter.disconnect()
                    break

            types = [e.type for e in events]
            assert VoiceEventType.RECONNECTING in types


class TestMockAdapterCapabilities:
    """Tests for capabilities."""

    def test_capabilities(self, mock_adapter):
        """Test capabilities are correct."""
        caps = mock_adapter.get_capabilities()

        assert caps.provider_name == "mock"
        assert caps.supports_server_vad
        assert caps.supports_function_calling
        assert "mock_voice" in caps.available_voices


class TestMockAdapterReset:
    """Tests for reset functionality."""

    @pytest.mark.asyncio
    async def test_reset(self, mock_adapter, default_config):
        """Test reset clears all state."""
        async with mock_adapter:
            await mock_adapter.connect(default_config)

            # Do some operations
            await mock_adapter.send_audio(b"\x00\x01")
            await mock_adapter.send_text("Hello")
            await mock_adapter.commit_audio()

            # Reset
            mock_adapter.reset()

            assert len(mock_adapter.sent_audio) == 0
            assert len(mock_adapter.sent_text) == 0
            assert mock_adapter.committed_count == 0
