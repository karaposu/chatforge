"""Fixtures for WebSocket tests."""

import asyncio

import pytest
import websockets


@pytest.fixture
async def echo_ws_server():
    """Echo WebSocket server for testing."""

    async def echo_handler(websocket):
        async for message in websocket:
            await websocket.send(message)

    async with websockets.serve(echo_handler, "127.0.0.1", 0) as server:
        # Use first socket's address (should be IPv4)
        sockname = server.sockets[0].getsockname()
        host, port = sockname[0], sockname[1]
        yield type("Server", (), {"url": f"ws://{host}:{port}"})()


@pytest.fixture
async def slow_ws_server():
    """Slow WebSocket server that doesn't read messages quickly."""

    async def slow_handler(websocket):
        # Just wait, don't read messages
        await asyncio.sleep(60)

    async with websockets.serve(slow_handler, "127.0.0.1", 0) as server:
        sockname = server.sockets[0].getsockname()
        host, port = sockname[0], sockname[1]
        yield type("Server", (), {"url": f"ws://{host}:{port}"})()
