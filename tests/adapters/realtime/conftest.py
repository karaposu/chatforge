"""Fixtures for realtime adapter tests."""

import pytest

from chatforge.adapters.realtime import MockRealtimeAdapter
from chatforge.ports.realtime_voice import VoiceSessionConfig, ToolDefinition


@pytest.fixture
def mock_adapter():
    """Create a fresh mock adapter."""
    return MockRealtimeAdapter()


@pytest.fixture
def default_config():
    """Default voice session config."""
    return VoiceSessionConfig()


@pytest.fixture
def config_with_tools():
    """Config with tool definitions."""
    return VoiceSessionConfig(
        tools=[
            ToolDefinition(
                name="get_weather",
                description="Get current weather",
                parameters={
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"},
                    },
                    "required": ["city"],
                },
            ),
        ],
    )
