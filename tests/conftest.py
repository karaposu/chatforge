"""
Shared pytest fixtures for chatforge tests.

This module provides common fixtures used across all test files.
"""

import os
from typing import Any
from unittest.mock import MagicMock, Mock

import pytest


# =============================================================================
# PYTEST HOOKS
# =============================================================================

def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests (makes real API calls, costs money)",
    )
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="Run end-to-end tests",
    )
    parser.addoption(
        "--run-stress",
        action="store_true",
        default=False,
        help="Run stress/load tests (very slow)",
    )


def pytest_collection_modifyitems(config, items):
    """Skip tests based on command line options."""
    # Skip integration tests by default
    if not config.getoption("--run-integration"):
        skip_integration = pytest.mark.skip(reason="Need --run-integration option to run")
        skip_expensive = pytest.mark.skip(reason="Need --run-integration option to run (costs money)")

        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
            if "expensive" in item.keywords:
                item.add_marker(skip_expensive)

    # Skip E2E tests by default
    if not config.getoption("--run-e2e"):
        skip_e2e = pytest.mark.skip(reason="Need --run-e2e option to run")
        for item in items:
            if "e2e" in item.keywords:
                item.add_marker(skip_e2e)

    # Skip stress tests by default
    if not config.getoption("--run-stress"):
        skip_stress = pytest.mark.skip(reason="Need --run-stress option to run")
        for item in items:
            if "stress" in item.keywords:
                item.add_marker(skip_stress)


# =============================================================================
# LLM FIXTURES
# =============================================================================

@pytest.fixture
def mock_llm_config():
    """Mock llm_config with default test settings."""
    mock_config = Mock()
    mock_config.provider = "openai"
    mock_config.model_name = "gpt-4o-mini"
    mock_config.temperature = 0.0
    mock_config.streaming = False
    mock_config.openai_api_key = "sk-test-key"
    mock_config.anthropic_api_key = None
    mock_config.aws_access_key_id = None
    mock_config.aws_secret_access_key = None
    return mock_config


@pytest.fixture
def mock_llm():
    """
    Mock BaseChatModel for testing without API calls.

    Returns a MagicMock configured to behave like LangChain's BaseChatModel.
    """
    llm = MagicMock()
    llm.model_name = "gpt-4o-mini"
    llm.temperature = 0.0
    llm.streaming = False

    # Mock invoke method
    def mock_invoke(messages, **kwargs):
        mock_response = Mock()
        mock_response.content = "This is a test response"
        return mock_response

    llm.invoke = Mock(side_effect=mock_invoke)
    llm.ainvoke = Mock(side_effect=mock_invoke)

    return llm


@pytest.fixture
def openai_api_key():
    """
    Provide OpenAI API key from environment or skip test.

    Use @pytest.mark.integration decorator on tests that need this.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.startswith("sk-test"):
        pytest.skip("OPENAI_API_KEY not set or is placeholder")
    return api_key


@pytest.fixture
def anthropic_api_key():
    """
    Provide Anthropic API key from environment or skip test.

    Use @pytest.mark.integration decorator on tests that need this.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")
    return api_key


# =============================================================================
# STORAGE FIXTURES
# =============================================================================

@pytest.fixture
async def in_memory_storage():
    """InMemoryStorageAdapter instance for testing."""
    from chatforge.adapters.storage import InMemoryStorageAdapter

    adapter = InMemoryStorageAdapter()
    yield adapter
    # Cleanup not needed for in-memory


@pytest.fixture
async def sqlite_storage_temp(tmp_path):
    """SQLiteStorageAdapter with temporary database."""
    from chatforge.adapters.storage import SQLiteStorageAdapter

    db_path = tmp_path / "test.db"
    adapter = SQLiteStorageAdapter(database_path=str(db_path))
    await adapter.setup()

    yield adapter

    await adapter.close()


# =============================================================================
# AGENT FIXTURES
# =============================================================================

@pytest.fixture
def mock_agent():
    """Mock ReActAgent for testing without LLM."""
    agent = MagicMock()

    def mock_process_message(message, history=None, context=None):
        return f"Mock response to: {message}", "trace-123"

    agent.process_message = Mock(side_effect=mock_process_message)

    return agent


@pytest.fixture
def simple_tool():
    """Simple test tool for agent testing."""
    from chatforge.services.agent.tools import AsyncAwareTool
    from pydantic import BaseModel, Field

    class SimpleToolInput(BaseModel):
        query: str = Field(description="Query string")

    class SimpleTool(AsyncAwareTool):
        name: str = "simple_tool"
        description: str = "A simple test tool"
        args_schema: type[BaseModel] = SimpleToolInput

        async def _execute_async(self, query: str, **kwargs) -> str:
            return f"Result for: {query}"

    return SimpleTool()


# =============================================================================
# UTILITY FIXTURES
# =============================================================================

@pytest.fixture
def clean_env(monkeypatch):
    """Clean environment variables for isolated tests."""
    # Clear LLM-related env vars
    env_vars = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "LLM_PROVIDER",
        "LLM_MODEL_NAME",
    ]

    for var in env_vars:
        monkeypatch.delenv(var, raising=False)
