"""
Mock helpers for chatforge tests.

Provides utilities for creating mock objects and test data.
"""

from typing import Any
from unittest.mock import Mock


def create_mock_llm(
    model_name: str = "gpt-4o-mini",
    temperature: float = 0.0,
    streaming: bool = False,
    response_text: str = "Mock response",
) -> Mock:
    """
    Create a mock LLM instance.

    Args:
        model_name: Model identifier
        temperature: Temperature setting
        streaming: Whether streaming is enabled
        response_text: Text to return from invoke()

    Returns:
        Mock configured to behave like BaseChatModel
    """
    llm = Mock()
    llm.model_name = model_name
    llm.temperature = temperature
    llm.streaming = streaming

    # Mock response
    mock_response = Mock()
    mock_response.content = response_text

    llm.invoke = Mock(return_value=mock_response)
    llm.ainvoke = Mock(return_value=mock_response)

    return llm


def create_mock_config(**overrides: Any) -> Mock:
    """
    Create a mock configuration object.

    Args:
        **overrides: Key-value pairs to override defaults

    Returns:
        Mock config with default values and overrides
    """
    defaults = {
        "provider": "openai",
        "model_name": "gpt-4o-mini",
        "temperature": 0.0,
        "streaming": False,
        "openai_api_key": "sk-test-key",
        "anthropic_api_key": None,
        "aws_access_key_id": None,
        "aws_secret_access_key": None,
        "aws_region": "us-east-1",
    }

    defaults.update(overrides)

    config = Mock()
    for key, value in defaults.items():
        setattr(config, key, value)

    return config


def create_mock_message(
    role: str = "user",
    content: str = "Test message",
    **metadata: Any,
) -> dict[str, Any]:
    """
    Create a mock message dict.

    Args:
        role: Message role (user, assistant, system)
        content: Message content
        **metadata: Additional metadata fields

    Returns:
        Message dictionary
    """
    message = {
        "role": role,
        "content": content,
    }

    if metadata:
        message.update(metadata)

    return message


def create_mock_conversation_history(num_messages: int = 3) -> list[dict[str, str]]:
    """
    Create a mock conversation history.

    Args:
        num_messages: Number of messages to generate

    Returns:
        List of alternating user/assistant messages
    """
    history = []

    for i in range(num_messages):
        if i % 2 == 0:
            history.append(create_mock_message("user", f"User message {i // 2 + 1}"))
        else:
            history.append(create_mock_message("assistant", f"Assistant response {i // 2 + 1}"))

    return history
