"""
Unit tests for ReActAgent with mocked LLM.

Tests agent initialization and message processing with mock LLM.
This is Layer 2 testing - agent logic with mocked dependencies.
"""

from unittest.mock import Mock, patch

import pytest
from langchain_core.messages import AIMessage

from chatforge.services.agent import DEFAULT_SYSTEM_PROMPT, ReActAgent


# =============================================================================
# LAYER 2: Agent with Mock LLM (Isolated Agent Logic)
# =============================================================================


@pytest.mark.unit
def test_agent_initialization_with_tools(simple_tool):
    """Test creating ReActAgent with tools."""
    agent = ReActAgent(tools=[simple_tool], system_prompt="Test prompt")

    assert len(agent.tools) == 1
    assert agent.system_prompt == "Test prompt"
    assert agent.llm is not None
    assert agent.agent is not None


@pytest.mark.unit
def test_agent_initialization_without_tools_raises_error():
    """Test that ReActAgent requires tools if no pre-built agent."""
    with pytest.raises(ValueError, match="ReActAgent requires either"):
        ReActAgent()


@pytest.mark.unit
def test_agent_initialization_with_prebuilt_agent():
    """Test creating ReActAgent with pre-built agent."""
    mock_agent = Mock()
    mock_tool = Mock()
    mock_tool.name = "test_tool"

    agent = ReActAgent(agent=mock_agent, tools=[mock_tool])

    assert agent.agent == mock_agent
    assert agent.tools == [mock_tool]


@pytest.mark.unit
def test_agent_uses_default_system_prompt():
    """Test that agent uses default system prompt when none provided."""
    agent = ReActAgent(tools=[], system_prompt=None)

    assert agent.system_prompt == DEFAULT_SYSTEM_PROMPT


@pytest.mark.unit
def test_agent_uses_custom_system_prompt():
    """Test that agent uses custom system prompt when provided."""
    custom_prompt = "You are a test assistant"

    agent = ReActAgent(tools=[], system_prompt=custom_prompt)

    assert agent.system_prompt == custom_prompt


@pytest.mark.unit
def test_agent_initialization_with_mock_llm():
    """Test creating ReActAgent with mocked LLM."""
    mock_llm = Mock()

    agent = ReActAgent(tools=[], system_prompt="Test", llm=mock_llm)

    assert agent.llm == mock_llm


@pytest.mark.unit
def test_agent_initialization_with_temperature():
    """Test creating ReActAgent with custom temperature."""
    with patch("chatforge.services.agent.engine.get_llm") as mock_get_llm:
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm

        agent = ReActAgent(tools=[], system_prompt="Test", temperature=0.7)

        # Verify get_llm was called with correct temperature
        mock_get_llm.assert_called_once_with(streaming=False, temperature=0.7)
        assert agent.llm == mock_llm


@pytest.mark.unit
def test_agent_has_messaging_port_check():
    """Test has_messaging_port method."""
    # Without messaging port
    agent = ReActAgent(tools=[], system_prompt="Test")
    assert agent.has_messaging_port() is False

    # With messaging port
    mock_port = Mock()
    agent2 = ReActAgent(tools=[], system_prompt="Test", messaging_port=mock_port)
    assert agent2.has_messaging_port() is True


@pytest.mark.unit
def test_agent_process_message_basic():
    """Test basic message processing with mocked agent."""
    # Create a mock LangGraph agent
    mock_langgraph_agent = Mock()
    mock_result = {
        "messages": [
            AIMessage(content="Mock response from agent"),
        ]
    }
    mock_langgraph_agent.invoke.return_value = mock_result

    # Create ReActAgent with mock
    agent = ReActAgent(agent=mock_langgraph_agent, tools=[])

    # Process message
    response, trace_id = agent.process_message(
        "Hello",
        conversation_history=[],
    )

    assert response == "Mock response from agent"
    assert trace_id is None  # No tracing enabled
    mock_langgraph_agent.invoke.assert_called_once()


@pytest.mark.unit
def test_agent_process_message_with_history():
    """Test message processing with conversation history."""
    mock_langgraph_agent = Mock()
    mock_result = {
        "messages": [
            AIMessage(content="Response with context"),
        ]
    }
    mock_langgraph_agent.invoke.return_value = mock_result

    agent = ReActAgent(agent=mock_langgraph_agent, tools=[])

    history = [
        {"role": "user", "content": "First message"},
        {"role": "assistant", "content": "First response"},
    ]

    response, trace_id = agent.process_message(
        "Second message",
        conversation_history=history,
    )

    assert response == "Response with context"
    # Verify invoke was called
    mock_langgraph_agent.invoke.assert_called_once()


@pytest.mark.unit
def test_agent_process_message_with_context():
    """Test message processing with context dict."""
    mock_langgraph_agent = Mock()
    mock_result = {
        "messages": [AIMessage(content="Response")],
    }
    mock_langgraph_agent.invoke.return_value = mock_result

    agent = ReActAgent(agent=mock_langgraph_agent, tools=[])

    context = {
        "user_id": "user123",
        "session_id": "session456",
    }

    response, trace_id = agent.process_message(
        "Test message",
        conversation_history=[],
        context=context,
    )

    assert response == "Response"


@pytest.mark.unit
def test_agent_process_message_error_handling():
    """Test that errors in agent are caught and return error message."""
    mock_langgraph_agent = Mock()
    mock_langgraph_agent.invoke.side_effect = Exception("Test error")

    agent = ReActAgent(agent=mock_langgraph_agent, tools=[])

    response, trace_id = agent.process_message(
        "Test message",
        conversation_history=[],
    )

    assert "error" in response.lower() or "apologize" in response.lower()
    assert trace_id is None


@pytest.mark.unit
def test_agent_process_message_with_timeout_success():
    """Test message processing with timeout (success case)."""
    mock_langgraph_agent = Mock()
    mock_result = {
        "messages": [AIMessage(content="Quick response")],
    }
    mock_langgraph_agent.invoke.return_value = mock_result

    agent = ReActAgent(agent=mock_langgraph_agent, tools=[])

    response, timed_out, trace_id = agent.process_message_with_timeout(
        "Test",
        conversation_history=[],
        timeout_seconds=10.0,
    )

    assert response == "Quick response"
    assert timed_out is False
    assert trace_id is None


@pytest.mark.unit
def test_agent_process_message_with_timeout_timeout():
    """Test message processing with timeout (timeout case)."""
    import time

    mock_langgraph_agent = Mock()

    def slow_invoke(*args, **kwargs):
        time.sleep(2)  # Sleep longer than timeout
        return {"messages": [AIMessage(content="Too slow")]}

    mock_langgraph_agent.invoke.side_effect = slow_invoke

    agent = ReActAgent(agent=mock_langgraph_agent, tools=[])

    response, timed_out, trace_id = agent.process_message_with_timeout(
        "Test",
        conversation_history=[],
        timeout_seconds=0.5,  # Very short timeout
    )

    assert response is None
    assert timed_out is True
    assert trace_id is None


@pytest.mark.unit
def test_agent_messaging_port_raises_error_when_not_configured():
    """Test that async messaging methods raise error when port not configured."""
    agent = ReActAgent(tools=[], system_prompt="Test")

    # Should raise RuntimeError for all messaging port methods
    with pytest.raises(RuntimeError, match="No messaging port configured"):
        import asyncio

        asyncio.run(agent.get_conversation_history_async(Mock()))

    with pytest.raises(RuntimeError, match="No messaging port configured"):
        import asyncio

        asyncio.run(agent.send_response_async(Mock(), "test"))

    with pytest.raises(RuntimeError, match="No messaging port configured"):
        import asyncio

        asyncio.run(agent.send_typing_indicator_async(Mock()))

    with pytest.raises(RuntimeError, match="No messaging port configured"):
        import asyncio

        asyncio.run(agent.get_user_email_async("user123"))


@pytest.mark.unit
def test_agent_with_tracing_port():
    """Test agent initialization with tracing port."""
    mock_tracing = Mock()
    mock_tracing.enabled = True

    agent = ReActAgent(tools=[], system_prompt="Test", tracing=mock_tracing)

    assert agent.tracing == mock_tracing


@pytest.mark.unit
def test_agent_response_extraction_from_ai_message():
    """Test that AIMessage content is extracted correctly."""
    mock_langgraph_agent = Mock()
    mock_result = {
        "messages": [
            AIMessage(content="This is the final response"),
        ]
    }
    mock_langgraph_agent.invoke.return_value = mock_result

    agent = ReActAgent(agent=mock_langgraph_agent, tools=[])

    response, _ = agent.process_message("Test", conversation_history=[])

    assert response == "This is the final response"


@pytest.mark.unit
def test_agent_response_extraction_from_multiple_messages():
    """Test that final message is extracted when multiple messages returned."""
    mock_langgraph_agent = Mock()
    mock_result = {
        "messages": [
            AIMessage(content="First message"),
            AIMessage(content="Second message"),
            AIMessage(content="Final message"),
        ]
    }
    mock_langgraph_agent.invoke.return_value = mock_result

    agent = ReActAgent(agent=mock_langgraph_agent, tools=[])

    response, _ = agent.process_message("Test", conversation_history=[])

    # Should extract the last message
    assert response == "Final message"


@pytest.mark.unit
def test_agent_empty_tools_list():
    """Test agent with empty tools list."""
    agent = ReActAgent(tools=[], system_prompt="Test")

    assert agent.tools == []
    assert agent.agent is not None


@pytest.mark.unit
def test_agent_multiple_tools(simple_tool):
    """Test agent with multiple tools."""
    # Use the same simple_tool multiple times (just for testing structure)
    agent = ReActAgent(
        tools=[simple_tool], system_prompt="Test"
    )

    assert len(agent.tools) == 1
    assert agent.tools[0].name == "simple_tool"


@pytest.mark.unit
def test_agent_system_prompt_property():
    """Test system_prompt property."""
    prompt = "Custom system prompt"
    agent = ReActAgent(tools=[], system_prompt=prompt)

    assert agent.system_prompt == prompt

    # Verify it's a read-only property (no setter)
    # Attempting to set should raise AttributeError
    with pytest.raises(AttributeError):
        agent.system_prompt = "New prompt"


@pytest.mark.unit
def test_agent_invoke_with_context_no_tracing():
    """Test _invoke_with_context when tracing is disabled."""
    from langchain_core.messages import HumanMessage

    mock_langgraph_agent = Mock()
    mock_result = {"messages": [AIMessage(content="Response")]}
    mock_langgraph_agent.invoke.return_value = mock_result

    agent = ReActAgent(agent=mock_langgraph_agent, tools=[])

    messages = [HumanMessage(content="Test")]
    result, trace_id = agent._invoke_with_context(messages, context=None)

    assert result == mock_result
    assert trace_id is None
    mock_langgraph_agent.invoke.assert_called_once()


@pytest.mark.unit
def test_agent_invoke_with_context_with_tracing():
    """Test _invoke_with_context when tracing is enabled."""
    from unittest.mock import MagicMock
    from langchain_core.messages import HumanMessage

    mock_langgraph_agent = Mock()
    mock_result = {"messages": [AIMessage(content="Response")]}
    mock_langgraph_agent.invoke.return_value = mock_result

    # Mock tracing port with proper context manager
    mock_tracing = MagicMock()
    mock_tracing.enabled = True
    mock_tracing.get_active_trace_id.return_value = "trace-123"
    mock_span = MagicMock()
    # Make span() return a context manager
    mock_tracing.span.return_value = mock_span

    agent = ReActAgent(agent=mock_langgraph_agent, tools=[], tracing=mock_tracing)

    messages = [HumanMessage(content="Test")]
    context = {"user_id": "user123", "session_id": "session456"}

    result, trace_id = agent._invoke_with_context(messages, context=context)

    assert result == mock_result
    assert trace_id == "trace-123"
    mock_tracing.span.assert_called_once_with("chatforge_agent")
    mock_tracing.set_trace_metadata.assert_called_once()


@pytest.mark.unit
def test_agent_initialization_logs_tool_names(caplog, simple_tool):
    """Test that agent initialization logs tool names."""
    import logging

    caplog.set_level(logging.INFO)

    agent = ReActAgent(tools=[simple_tool], system_prompt="Test")

    # Check that tool name appears in logs
    assert any("simple_tool" in record.message for record in caplog.records)
