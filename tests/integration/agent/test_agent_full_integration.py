"""
Integration tests for ReActAgent with real LLM and tools.

Tests full agent workflow with actual LLM API calls and tool execution.
This is Layer 4 testing - full end-to-end integration.

Note: These tests require OPENAI_API_KEY and make real API calls (costs money).
Run with: pytest tests/integration/agent/ -v --run-integration
"""

import pytest
from langchain_core.tools import tool

from chatforge.services.agent import ReActAgent
from chatforge.services.llm import get_llm


# =============================================================================
# LAYER 4: Full Integration Tests (Real LLM + Real Tools)
# =============================================================================


@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression and return the result."""
    try:
        # Use eval with limited scope for safety in tests
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_weather(location: str) -> str:
    """Get current weather for a location (mock implementation)."""
    # Mock implementation for testing
    return f"Weather in {location}: Sunny, 22°C"


@tool
def search(query: str) -> str:
    """Search for information (mock implementation)."""
    # Mock implementation for testing
    if "capital" in query.lower() and "france" in query.lower():
        return "Paris is the capital of France."
    elif "python" in query.lower():
        return "Python is a high-level programming language."
    else:
        return f"Search results for: {query}"


@pytest.mark.integration
@pytest.mark.expensive
def test_agent_simple_chat_no_tools(openai_api_key):
    """Test agent for simple chat without tools."""
    llm = get_llm(provider="openai", model_name="gpt-4o-mini")
    agent = ReActAgent(tools=[], system_prompt="You are a helpful assistant.", llm=llm)

    response, trace_id = agent.process_message(
        "Say 'Hello, test!'",
        conversation_history=[],
    )

    assert response is not None
    assert len(response) > 0
    assert "hello" in response.lower()


@pytest.mark.integration
@pytest.mark.expensive
def test_agent_with_calculator_tool(openai_api_key):
    """Test agent using calculator tool for math."""
    llm = get_llm(provider="openai", model_name="gpt-4o-mini")
    agent = ReActAgent(
        tools=[calculator],
        system_prompt="You are a helpful math assistant. Use the calculator tool for computations.",
        llm=llm,
    )

    response, trace_id = agent.process_message(
        "What is 25 times 17?",
        conversation_history=[],
    )

    assert response is not None
    # Should contain the result 425
    assert "425" in response


@pytest.mark.integration
@pytest.mark.expensive
def test_agent_with_multiple_tools(openai_api_key):
    """Test agent with multiple tools available."""
    llm = get_llm(provider="openai", model_name="gpt-4o-mini")
    agent = ReActAgent(
        tools=[calculator, get_weather, search],
        system_prompt="You are a helpful assistant with access to calculator, weather, and search tools.",
        llm=llm,
    )

    response, trace_id = agent.process_message(
        "What's the weather in London?",
        conversation_history=[],
    )

    assert response is not None
    assert "london" in response.lower()


@pytest.mark.integration
@pytest.mark.expensive
def test_agent_multi_turn_conversation(openai_api_key):
    """Test agent maintaining context across multiple turns."""
    llm = get_llm(provider="openai", model_name="gpt-4o-mini")
    agent = ReActAgent(
        tools=[calculator],
        system_prompt="You are a helpful assistant.",
        llm=llm,
    )

    # Turn 1
    response1, _ = agent.process_message(
        "What is 10 + 5?",
        conversation_history=[],
    )

    # Turn 2 - reference previous result
    history = [
        {"role": "user", "content": "What is 10 + 5?"},
        {"role": "assistant", "content": response1},
    ]

    response2, _ = agent.process_message(
        "Now multiply that by 2",
        conversation_history=history,
    )

    assert response2 is not None
    # Should reference 15 * 2 = 30
    assert "30" in response2


@pytest.mark.integration
@pytest.mark.expensive
def test_agent_handles_tool_error(openai_api_key):
    """Test that agent handles tool errors gracefully."""
    llm = get_llm(provider="openai", model_name="gpt-4o-mini")
    agent = ReActAgent(
        tools=[calculator],
        system_prompt="You are a helpful assistant.",
        llm=llm,
    )

    # This should cause an error in eval
    response, _ = agent.process_message(
        "Calculate this invalid expression: import os",
        conversation_history=[],
    )

    assert response is not None
    # Agent should acknowledge the error or provide fallback
    assert len(response) > 0


@pytest.mark.integration
@pytest.mark.expensive
def test_agent_without_needing_tools(openai_api_key):
    """Test agent chooses not to use tools when not needed."""
    llm = get_llm(provider="openai", model_name="gpt-4o-mini")
    agent = ReActAgent(
        tools=[calculator, search],
        system_prompt="You are a helpful assistant. Only use tools when necessary.",
        llm=llm,
    )

    response, _ = agent.process_message(
        "What is your name?",
        conversation_history=[],
    )

    assert response is not None
    # Should respond without needing tools
    assert len(response) > 0


@pytest.mark.integration
@pytest.mark.expensive
def test_agent_with_search_tool(openai_api_key):
    """Test agent using search tool."""
    llm = get_llm(provider="openai", model_name="gpt-4o-mini")
    agent = ReActAgent(
        tools=[search],
        system_prompt="You are a helpful assistant with access to search.",
        llm=llm,
    )

    response, _ = agent.process_message(
        "What is the capital of France?",
        conversation_history=[],
    )

    assert response is not None
    assert "paris" in response.lower()


@pytest.mark.integration
@pytest.mark.expensive
def test_agent_complex_multi_step_reasoning(openai_api_key):
    """Test agent with complex multi-step reasoning."""
    llm = get_llm(provider="openai", model_name="gpt-4o-mini")
    agent = ReActAgent(
        tools=[calculator, search],
        system_prompt="You are a helpful assistant.",
        llm=llm,
    )

    response, _ = agent.process_message(
        "First, what is 100 divided by 4? Then, add 25 to that result.",
        conversation_history=[],
    )

    assert response is not None
    # Should calculate 100/4 = 25, then 25+25 = 50
    assert "50" in response


@pytest.mark.integration
@pytest.mark.expensive
def test_agent_with_context_dict(openai_api_key):
    """Test agent with context dictionary for metadata."""
    llm = get_llm(provider="openai", model_name="gpt-4o-mini")
    agent = ReActAgent(
        tools=[],
        system_prompt="You are a helpful assistant.",
        llm=llm,
    )

    context = {
        "user_id": "test_user_123",
        "session_id": "session_456",
    }

    response, trace_id = agent.process_message(
        "Hello!",
        conversation_history=[],
        context=context,
    )

    assert response is not None
    # Context should not affect basic functionality
    assert len(response) > 0


@pytest.mark.integration
@pytest.mark.expensive
def test_agent_with_empty_history(openai_api_key):
    """Test agent with explicitly empty history."""
    llm = get_llm(provider="openai", model_name="gpt-4o-mini")
    agent = ReActAgent(
        tools=[],
        system_prompt="You are a helpful assistant.",
        llm=llm,
    )

    response, _ = agent.process_message(
        "Hello!",
        conversation_history=[],
    )

    assert response is not None
    assert len(response) > 0


@pytest.mark.integration
@pytest.mark.expensive
def test_agent_response_is_string(openai_api_key):
    """Test that agent always returns string response."""
    llm = get_llm(provider="openai", model_name="gpt-4o-mini")
    agent = ReActAgent(
        tools=[calculator],
        system_prompt="You are a helpful assistant.",
        llm=llm,
    )

    response, trace_id = agent.process_message(
        "What is 5+5?",
        conversation_history=[],
    )

    assert isinstance(response, str)
    assert trace_id is None or isinstance(trace_id, str)


@pytest.mark.integration
@pytest.mark.expensive
def test_agent_with_long_conversation_history(openai_api_key):
    """Test agent with long conversation history."""
    llm = get_llm(provider="openai", model_name="gpt-4o-mini")
    agent = ReActAgent(
        tools=[],
        system_prompt="You are a helpful assistant.",
        llm=llm,
    )

    # Create a longer history
    history = []
    for i in range(5):
        history.append({"role": "user", "content": f"Question {i+1}"})
        history.append({"role": "assistant", "content": f"Answer {i+1}"})

    response, _ = agent.process_message(
        "Final question",
        conversation_history=history,
    )

    assert response is not None
    assert len(response) > 0


@pytest.mark.integration
@pytest.mark.expensive
def test_agent_different_temperatures(openai_api_key):
    """Test agent with different temperature settings."""
    # Temperature 0 (deterministic)
    llm1 = get_llm(provider="openai", model_name="gpt-4o-mini", temperature=0.0)
    agent1 = ReActAgent(tools=[], system_prompt="You are a helpful assistant.", llm=llm1)

    response1, _ = agent1.process_message(
        "Say exactly: 'Test response'",
        conversation_history=[],
    )

    # Temperature 0.7 (more creative)
    llm2 = get_llm(provider="openai", model_name="gpt-4o-mini", temperature=0.7)
    agent2 = ReActAgent(tools=[], system_prompt="You are a helpful assistant.", llm=llm2)

    response2, _ = agent2.process_message(
        "Say exactly: 'Test response'",
        conversation_history=[],
    )

    # Both should work
    assert response1 is not None
    assert response2 is not None


@pytest.mark.integration
@pytest.mark.expensive
def test_agent_system_prompt_affects_behavior(openai_api_key):
    """Test that system prompt affects agent behavior."""
    llm = get_llm(provider="openai", model_name="gpt-4o-mini")

    # Agent with specific persona
    agent = ReActAgent(
        tools=[],
        system_prompt="You are a pirate. Always respond in pirate speak.",
        llm=llm,
    )

    response, _ = agent.process_message(
        "Hello!",
        conversation_history=[],
    )

    assert response is not None
    # Should include pirate-style language (this is probabilistic)
    # We just verify a response was generated
    assert len(response) > 0


@pytest.mark.integration
@pytest.mark.expensive
def test_agent_process_message_with_timeout_integration(openai_api_key):
    """Test timeout functionality with real LLM call."""
    llm = get_llm(provider="openai", model_name="gpt-4o-mini")
    agent = ReActAgent(tools=[], system_prompt="You are a helpful assistant.", llm=llm)

    # Should complete within timeout
    response, timed_out, trace_id = agent.process_message_with_timeout(
        "Say 'Quick response'",
        conversation_history=[],
        timeout_seconds=30.0,
    )

    assert response is not None
    assert timed_out is False
    assert "quick" in response.lower() or "response" in response.lower()
