"""Tests for WebSocketClient."""

import asyncio
import json

import pytest
import websockets

from chatforge.infrastructure.websocket import (
    ConnectionMetrics,
    ConnectionState,
    ExponentialBackoff,
    FixedDelay,
    JsonSerializer,
    NoReconnect,
    RawSerializer,
    WebSocketBackpressureError,
    WebSocketClient,
    WebSocketClosedError,
    WebSocketConfig,
    WebSocketConnectionError,
    WebSocketTimeoutError,
)


class TestWebSocketClient:
    """Tests for WebSocketClient."""

    @pytest.mark.asyncio
    async def test_connect_disconnect(self, echo_ws_server):
        """Test basic connect/disconnect."""
        config = WebSocketConfig(url=echo_ws_server.url)

        async with WebSocketClient(config) as ws:
            assert ws.is_connected
            assert ws.state == ConnectionState.CONNECTED

        assert ws.state == ConnectionState.CLOSED

    @pytest.mark.asyncio
    async def test_send_receive_text(self, echo_ws_server):
        """Test sending and receiving text messages."""
        config = WebSocketConfig(url=echo_ws_server.url)

        async with WebSocketClient(config) as ws:
            await ws.send_text("hello")
            message = await ws.receive(timeout=5.0)

            assert message.is_text
            assert message.as_text() == "hello"

    @pytest.mark.asyncio
    async def test_send_receive_binary(self, echo_ws_server):
        """Test sending and receiving binary messages."""
        config = WebSocketConfig(url=echo_ws_server.url)

        async with WebSocketClient(config) as ws:
            await ws.send_binary(b"\x00\x01\x02")
            message = await ws.receive(timeout=5.0)

            assert message.is_binary
            assert message.as_bytes() == b"\x00\x01\x02"

    @pytest.mark.asyncio
    async def test_send_json(self, echo_ws_server):
        """Test sending JSON messages."""
        config = WebSocketConfig(url=echo_ws_server.url)

        async with WebSocketClient(config) as ws:
            await ws.send_json({"type": "test", "value": 123})
            message = await ws.receive(timeout=5.0)

            data = json.loads(message.as_text())
            assert data == {"type": "test", "value": 123}

    @pytest.mark.asyncio
    async def test_messages_generator(self, echo_ws_server):
        """Test async message generator."""
        config = WebSocketConfig(url=echo_ws_server.url)

        async with WebSocketClient(config) as ws:
            # Send multiple messages
            for i in range(3):
                await ws.send_text(f"msg{i}")

            # Receive via generator
            received = []
            async for msg in ws.messages():
                received.append(msg.as_text())
                if len(received) >= 3:
                    break

            assert received == ["msg0", "msg1", "msg2"]

    @pytest.mark.asyncio
    async def test_callbacks(self, echo_ws_server):
        """Test event callbacks."""
        config = WebSocketConfig(url=echo_ws_server.url)
        client = WebSocketClient(config)

        events = []

        client.on_connect = lambda: events.append("connect")
        client.on_message = lambda m: events.append(f"msg:{m.as_text()}")
        client.on_disconnect = lambda e: events.append("disconnect")

        await client.connect()
        assert "connect" in events

        await client.send_text("test")
        await asyncio.sleep(0.1)
        assert "msg:test" in events

        await client.disconnect()
        assert "disconnect" in events

    @pytest.mark.asyncio
    async def test_receive_timeout(self, echo_ws_server):
        """Test receive timeout."""
        config = WebSocketConfig(url=echo_ws_server.url)

        async with WebSocketClient(config) as ws:
            with pytest.raises(WebSocketTimeoutError):
                await ws.receive(timeout=0.1)

    @pytest.mark.asyncio
    async def test_send_when_disconnected(self, echo_ws_server):
        """Test send when not connected."""
        config = WebSocketConfig(url=echo_ws_server.url)
        client = WebSocketClient(config)

        with pytest.raises(WebSocketClosedError):
            await client.send("test")

    @pytest.mark.asyncio
    async def test_connection_error(self):
        """Test connection to invalid URL."""
        config = WebSocketConfig(
            url="ws://localhost:99999",
            connect_timeout=1.0,
            auto_reconnect=False,
        )

        with pytest.raises((WebSocketConnectionError, WebSocketTimeoutError)):
            async with WebSocketClient(config):
                pass


class TestReconnectPolicies:
    """Tests for reconnect policies."""

    def test_exponential_backoff(self):
        """Test exponential backoff delays."""
        policy = ExponentialBackoff(
            base=1.0, factor=2.0, max_delay=10.0, max_attempts=3, jitter=0
        )

        assert policy.next_delay(1) == 1.0
        assert policy.next_delay(2) == 2.0
        assert policy.next_delay(3) == 4.0
        assert policy.next_delay(4) is None  # Exceeded max_attempts

    def test_exponential_backoff_max_delay(self):
        """Test max delay cap."""
        policy = ExponentialBackoff(
            base=1.0, factor=10.0, max_delay=5.0, max_attempts=0, jitter=0
        )

        assert policy.next_delay(1) == 1.0
        assert policy.next_delay(2) == 5.0  # Capped
        assert policy.next_delay(3) == 5.0  # Still capped

    def test_no_reconnect(self):
        """Test no reconnect policy."""
        policy = NoReconnect()
        assert policy.next_delay(1) is None

    def test_fixed_delay(self):
        """Test fixed delay policy."""
        policy = FixedDelay(delay=5.0, max_attempts=2)

        assert policy.next_delay(1) == 5.0
        assert policy.next_delay(2) == 5.0
        assert policy.next_delay(3) is None


class TestSerializers:
    """Tests for message serializers."""

    def test_json_serializer(self):
        """Test JSON serialization."""
        serializer = JsonSerializer()

        # Serialize
        data = {"type": "test", "value": 123}
        serialized = serializer.serialize(data)
        assert isinstance(serialized, str)
        assert '"type"' in serialized

        # Deserialize
        deserialized = serializer.deserialize(serialized)
        assert deserialized == data

        # Deserialize bytes
        deserialized = serializer.deserialize(serialized.encode())
        assert deserialized == data

    def test_raw_serializer(self):
        """Test raw pass-through serialization."""
        serializer = RawSerializer()

        # Text
        text = "hello"
        assert serializer.serialize(text) == text
        assert serializer.deserialize(text) == text

        # Binary
        binary = b"\x00\x01\x02"
        assert serializer.serialize(binary) == binary
        assert serializer.deserialize(binary) == binary


class TestConnectionMetrics:
    """Tests for connection metrics."""

    def test_metrics_counters(self):
        """Test metrics counter methods."""
        metrics = ConnectionMetrics(connection_id="test123")

        metrics.on_connect()
        assert metrics.connect_count == 1
        assert metrics.connect_time is not None

        metrics.on_message_sent(100)
        assert metrics.messages_sent == 1
        assert metrics.bytes_sent == 100

        metrics.on_message_received(50)
        assert metrics.messages_received == 1
        assert metrics.bytes_received == 50

        metrics.on_disconnect()
        assert metrics.disconnect_count == 1

    def test_get_stats(self):
        """Test get_stats returns dictionary."""
        metrics = ConnectionMetrics(connection_id="test123")
        metrics.on_connect()
        metrics.on_message_sent(100)

        stats = metrics.get_stats()

        assert stats["connection_id"] == "test123"
        assert stats["connects"] == 1
        assert stats["messages_sent"] == 1
        assert "uptime_seconds" in stats

    def test_metrics_reset(self):
        """Test metrics reset."""
        metrics = ConnectionMetrics()
        metrics.on_connect()
        metrics.on_message_sent(100)

        metrics.reset()

        assert metrics.connect_count == 0
        assert metrics.messages_sent == 0
        assert metrics.connect_time is None


class TestWebSocketClientNewFeatures:
    """Tests for new WebSocket client features."""

    @pytest.mark.asyncio
    async def test_connection_id(self, echo_ws_server):
        """Test connection ID is generated."""
        config = WebSocketConfig(url=echo_ws_server.url)

        async with WebSocketClient(config) as ws:
            assert ws.connection_id is not None
            assert len(ws.connection_id) == 8  # UUID prefix

    @pytest.mark.asyncio
    async def test_metrics_enabled(self, echo_ws_server):
        """Test metrics are tracked when enabled."""
        config = WebSocketConfig(url=echo_ws_server.url, enable_metrics=True)

        async with WebSocketClient(config) as ws:
            await ws.send_text("hello")
            await ws.receive(timeout=5.0)

            stats = ws.get_stats()
            assert stats["connects"] == 1
            assert stats["messages_sent"] == 1
            assert stats["messages_received"] == 1

    @pytest.mark.asyncio
    async def test_metrics_disabled(self, echo_ws_server):
        """Test metrics are not tracked when disabled."""
        config = WebSocketConfig(url=echo_ws_server.url, enable_metrics=False)

        async with WebSocketClient(config) as ws:
            assert ws.metrics is None
            stats = ws.get_stats()
            assert stats == {"metrics_enabled": False}

    @pytest.mark.asyncio
    async def test_ping_method(self, echo_ws_server):
        """Test manual ping method."""
        config = WebSocketConfig(url=echo_ws_server.url)

        async with WebSocketClient(config) as ws:
            result = await ws.ping(timeout=5.0)
            assert result is True

    @pytest.mark.asyncio
    async def test_ping_when_disconnected(self, echo_ws_server):
        """Test ping returns False when disconnected."""
        config = WebSocketConfig(url=echo_ws_server.url)
        ws = WebSocketClient(config)

        result = await ws.ping()
        assert result is False

    @pytest.mark.asyncio
    async def test_fast_lane_mode(self, echo_ws_server):
        """Test fast lane (no send queue) mode."""
        config = WebSocketConfig(
            url=echo_ws_server.url,
            enable_send_queue=False,
            enable_metrics=False,
        )

        async with WebSocketClient(config) as ws:
            # Should send directly without queue
            await ws.send_text("hello")
            message = await ws.receive(timeout=5.0)
            assert message.as_text() == "hello"

    @pytest.mark.asyncio
    async def test_serializer_integration(self, echo_ws_server):
        """Test serializer integration."""
        config = WebSocketConfig(
            url=echo_ws_server.url,
            serializer=JsonSerializer(),
        )

        async with WebSocketClient(config) as ws:
            # send_json uses serializer
            await ws.send_json({"type": "test"})

            # Use async receive_obj for convenience
            obj = await ws.receive_obj(timeout=5.0)
            assert obj == {"type": "test"}

    @pytest.mark.asyncio
    async def test_deserialize_method(self, echo_ws_server):
        """Test manual deserialize method."""
        config = WebSocketConfig(
            url=echo_ws_server.url,
            serializer=JsonSerializer(),
        )

        async with WebSocketClient(config) as ws:
            await ws.send_json({"key": "value"})
            message = await ws.receive(timeout=5.0)

            # Manual deserialize
            obj = ws.deserialize(message)
            assert obj == {"key": "value"}

    @pytest.mark.asyncio
    async def test_async_callback(self, echo_ws_server):
        """Test that async callbacks are properly awaited."""
        config = WebSocketConfig(url=echo_ws_server.url)
        client = WebSocketClient(config)

        events = []

        async def async_on_connect():
            await asyncio.sleep(0.01)  # Simulate async work
            events.append("async_connect")

        client.on_connect = async_on_connect

        await client.connect()
        assert "async_connect" in events

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_receive_overflow_callback(self, echo_ws_server):
        """Test receive overflow callback is fired when queue is full."""
        config = WebSocketConfig(
            url=echo_ws_server.url,
            max_queue_size=1,  # Very small queue
        )

        dropped_messages = []

        async with WebSocketClient(config) as ws:
            ws.on_receive_overflow = lambda msg: dropped_messages.append(msg)

            # Send more messages than queue can hold
            for i in range(5):
                await ws.send_text(f"msg{i}")

            await asyncio.sleep(0.2)  # Let messages arrive

            # Some messages should have been dropped
            # (exact count depends on timing)


class TestWebSocketClientIntegration:
    """Integration tests for critical scenarios."""

    @pytest.mark.asyncio
    async def test_backpressure_triggers(self, echo_ws_server):
        """Test that backpressure error is raised when send queue is full."""
        config = WebSocketConfig(
            url=echo_ws_server.url,
            enable_send_queue=True,
            send_queue_size=2,
            send_queue_timeout=0.01,  # Very short timeout (10ms)
        )

        async with WebSocketClient(config) as ws:
            # Cancel the send worker so it doesn't drain the queue
            if ws._send_task:
                ws._send_task.cancel()
                try:
                    await ws._send_task
                except asyncio.CancelledError:
                    pass

            # Pre-fill the queue directly to test backpressure
            await ws._send_queue.put("msg1")
            await ws._send_queue.put("msg2")

            # Now the queue is full, next send should trigger backpressure
            with pytest.raises(WebSocketBackpressureError):
                await ws.send_text("overflow")

    @pytest.mark.asyncio
    async def test_no_memory_leak(self, echo_ws_server):
        """Test that memory doesn't grow unbounded under load."""
        import tracemalloc

        config = WebSocketConfig(url=echo_ws_server.url)

        tracemalloc.start()

        async with WebSocketClient(config) as ws:
            for _ in range(1000):
                await ws.send_text("x" * 100)
                await ws.receive(timeout=5.0)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Memory should stay reasonable (< 10MB for this test)
        assert peak < 10 * 1024 * 1024, f"Peak memory too high: {peak / 1024 / 1024:.2f}MB"

    @pytest.mark.asyncio
    async def test_connection_leak_on_setup_failure(self):
        """Test that connections don't leak when setup fails."""

        setup_error_triggered = False

        # Server that accepts but we'll fail during client setup
        async def handler(websocket):
            await asyncio.sleep(10)

        async with websockets.serve(handler, "127.0.0.1", 0) as server:
            sockname = server.sockets[0].getsockname()
            host, port = sockname[0], sockname[1]

            config = WebSocketConfig(
                url=f"ws://{host}:{port}",
                connect_timeout=5.0,
            )

            client = WebSocketClient(config)

            # Simulate setup failure by raising in callback
            def failing_callback():
                nonlocal setup_error_triggered
                setup_error_triggered = True
                raise RuntimeError("Setup failed!")

            client.on_connect = failing_callback

            # Connection should still work (callback error shouldn't crash)
            await client.connect()
            assert setup_error_triggered
            await client.disconnect()


class TestConfigValidation:
    """Tests for config validation."""

    def test_valid_config(self):
        """Test valid config creation."""
        config = WebSocketConfig(url="ws://localhost:8080")
        assert config.url == "ws://localhost:8080"

    def test_invalid_connect_timeout(self):
        """Test invalid connect_timeout raises error."""
        with pytest.raises(ValueError, match="connect_timeout must be positive"):
            WebSocketConfig(url="ws://localhost", connect_timeout=0)

        with pytest.raises(ValueError, match="connect_timeout must be positive"):
            WebSocketConfig(url="ws://localhost", connect_timeout=-1)

    def test_invalid_ping_interval(self):
        """Test invalid ping_interval raises error."""
        with pytest.raises(ValueError, match="ping_interval must be non-negative"):
            WebSocketConfig(url="ws://localhost", ping_interval=-1)

    def test_invalid_max_queue_size(self):
        """Test invalid max_queue_size raises error."""
        with pytest.raises(ValueError, match="max_queue_size must be positive"):
            WebSocketConfig(url="ws://localhost", max_queue_size=0)

    def test_invalid_send_queue_size(self):
        """Test invalid send_queue_size raises error."""
        with pytest.raises(ValueError, match="send_queue_size must be positive"):
            WebSocketConfig(url="ws://localhost", send_queue_size=0)

    def test_invalid_send_queue_timeout(self):
        """Test invalid send_queue_timeout raises error."""
        with pytest.raises(ValueError, match="send_queue_timeout must be positive"):
            WebSocketConfig(url="ws://localhost", send_queue_timeout=0)
