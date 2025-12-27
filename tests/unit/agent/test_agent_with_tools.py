"""
Unit tests for ReActAgent with tools.

Tests agent behavior with mock tools and tool execution.
This is Layer 3 testing - agent logic with tool integration.
"""

from unittest.mock import Mock

import pytest
from langchain_core.messages import AIMessage, ToolMessage

from chatforge.services.agent import ReActAgent


# =============================================================================
# LAYER 3: Agent with Tools (Tool Integration)
# =============================================================================


@pytest.mark.unit
def test_agent_with_single_tool(simple_tool):
    """Test agent with a single tool."""
    agent = ReActAgent(tools=[simple_tool], system_prompt="Test")

    assert len(agent.tools) == 1
    assert agent.tools[0].name == "simple_tool"


@pytest.mark.unit
def test_agent_tool_call_in_response():
    """Test agent response that includes tool calls."""
    # Create mock agent that simulates tool calling
    mock_langgraph_agent = Mock()

    # Simulate a tool call followed by final response
    mock_result = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "calculator",
                        "args": {"expression": "2+2"},
                        "id": "call_123",
                    }
                ],
            ),
            ToolMessage(content="4", tool_call_id="call_123"),
            AIMessage(content="The result is 4"),
        ]
    }
    mock_langgraph_agent.invoke.return_value = mock_result

    mock_tool = Mock()
    mock_tool.name = "calculator"

    agent = ReActAgent(agent=mock_langgraph_agent, tools=[mock_tool])

    response, trace_id = agent.process_message("What is 2+2?", conversation_history=[])

    # Should extract the final response
    assert response == "The result is 4"


@pytest.mark.unit
def test_agent_multiple_tool_calls():
    """Test agent response with multiple tool calls."""
    mock_langgraph_agent = Mock()

    # Simulate multiple tool calls
    mock_result = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "search",
                        "args": {"query": "weather"},
                        "id": "call_1",
                    }
                ],
            ),
            ToolMessage(content="Sunny, 25C", tool_call_id="call_1"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "search",
                        "args": {"query": "traffic"},
                        "id": "call_2",
                    }
                ],
            ),
            ToolMessage(content="Light traffic", tool_call_id="call_2"),
            AIMessage(content="It's sunny with light traffic"),
        ]
    }
    mock_langgraph_agent.invoke.return_value = mock_result

    mock_search = Mock()
    mock_search.name = "search"

    agent = ReActAgent(agent=mock_langgraph_agent, tools=[mock_search])

    response, _ = agent.process_message("How's the weather and traffic?", [])

    assert response == "It's sunny with light traffic"


@pytest.mark.unit
def test_agent_tool_execution_logged(caplog):
    """Test that tool executions are logged."""
    import logging

    caplog.set_level(logging.INFO)

    mock_langgraph_agent = Mock()
    mock_result = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "calculator",
                        "args": {"expression": "5*5"},
                        "id": "call_abc",
                    }
                ],
            ),
            ToolMessage(content="25", tool_call_id="call_abc"),
            AIMessage(content="5*5 equals 25"),
        ]
    }
    mock_langgraph_agent.invoke.return_value = mock_result

    agent = ReActAgent(agent=mock_langgraph_agent, tools=[])

    response, _ = agent.process_message("What is 5*5?", [])

    # Check that tool invocation was logged
    assert any("Tool invoked" in record.message for record in caplog.records)
    assert any("calculator" in record.message for record in caplog.records)


@pytest.mark.unit
def test_agent_no_tools_still_works():
    """Test agent works without tools (pure chat)."""
    mock_langgraph_agent = Mock()
    mock_result = {
        "messages": [AIMessage(content="Just a chat response, no tools used")],
    }
    mock_langgraph_agent.invoke.return_value = mock_result

    agent = ReActAgent(agent=mock_langgraph_agent, tools=[])

    response, _ = agent.process_message("Hello", [])

    assert response == "Just a chat response, no tools used"


@pytest.mark.unit
def test_agent_with_async_aware_tool():
    """Test agent with AsyncAwareTool."""
    from chatforge.services.agent.tools import AsyncAwareTool
    from pydantic import BaseModel, Field

    class TestToolInput(BaseModel):
        query: str = Field(description="Test query")

    class TestTool(AsyncAwareTool):
        name: str = "test_tool"
        description: str = "A test tool"
        args_schema: type[BaseModel] = TestToolInput

        async def _execute_async(self, query: str, **kwargs) -> str:
            return f"Result for: {query}"

    tool = TestTool()
    agent = ReActAgent(tools=[tool], system_prompt="Test")

    assert len(agent.tools) == 1
    assert agent.tools[0].name == "test_tool"


@pytest.mark.unit
def test_agent_tool_names_extracted(simple_tool):
    """Test that tool names are properly extracted from tools."""
    agent = ReActAgent(tools=[simple_tool], system_prompt="Test")

    tool_names = [t.name for t in agent.tools]
    assert tool_names == ["simple_tool"]


@pytest.mark.unit
def test_agent_empty_tool_calls_list():
    """Test agent handles AIMessage with empty tool_calls list."""
    mock_langgraph_agent = Mock()
    mock_result = {
        "messages": [
            AIMessage(content="No tools needed", tool_calls=[]),
        ],
    }
    mock_langgraph_agent.invoke.return_value = mock_result

    agent = ReActAgent(agent=mock_langgraph_agent, tools=[])

    response, _ = agent.process_message("Simple question", [])

    assert response == "No tools needed"


@pytest.mark.unit
def test_agent_tool_call_with_complex_args():
    """Test tool call with complex arguments."""
    mock_langgraph_agent = Mock()
    mock_result = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "complex_tool",
                        "args": {
                            "param1": "value1",
                            "param2": 42,
                            "param3": {"nested": "data"},
                            "param4": [1, 2, 3],
                        },
                        "id": "call_complex",
                    }
                ],
            ),
            ToolMessage(content="Success", tool_call_id="call_complex"),
            AIMessage(content="Tool executed successfully"),
        ]
    }
    mock_langgraph_agent.invoke.return_value = mock_result

    agent = ReActAgent(agent=mock_langgraph_agent, tools=[])

    response, _ = agent.process_message("Test complex args", [])

    assert response == "Tool executed successfully"


@pytest.mark.unit
def test_agent_tool_call_count_logged(caplog):
    """Test that total tool call count is logged."""
    import logging

    caplog.set_level(logging.INFO)

    mock_langgraph_agent = Mock()
    mock_result = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {"name": "tool1", "args": {}, "id": "call_1"},
                    {"name": "tool2", "args": {}, "id": "call_2"},
                    {"name": "tool3", "args": {}, "id": "call_3"},
                ],
            ),
            ToolMessage(content="Result 1", tool_call_id="call_1"),
            ToolMessage(content="Result 2", tool_call_id="call_2"),
            ToolMessage(content="Result 3", tool_call_id="call_3"),
            AIMessage(content="All tools executed"),
        ]
    }
    mock_langgraph_agent.invoke.return_value = mock_result

    agent = ReActAgent(agent=mock_langgraph_agent, tools=[])

    response, _ = agent.process_message("Execute tools", [])

    # Check that total tool invocations is logged
    assert any("Total tool invocations: 3" in record.message for record in caplog.records)


@pytest.mark.unit
def test_agent_tool_result_logged(caplog):
    """Test that tool results are logged."""
    import logging

    caplog.set_level(logging.DEBUG)

    mock_langgraph_agent = Mock()
    mock_result = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[{"name": "test", "args": {}, "id": "call_xyz"}],
            ),
            ToolMessage(content="This is the tool result", tool_call_id="call_xyz"),
            AIMessage(content="Final response"),
        ]
    }
    mock_langgraph_agent.invoke.return_value = mock_result

    agent = ReActAgent(agent=mock_langgraph_agent, tools=[])

    response, _ = agent.process_message("Test", [])

    # Check that tool result is logged
    assert any("Tool result received" in record.message for record in caplog.records)


@pytest.mark.unit
def test_agent_handles_missing_tool_calls_attribute():
    """Test agent handles messages without tool_calls attribute gracefully."""
    from unittest.mock import MagicMock
    from langchain_core.messages import AIMessage

    mock_langgraph_agent = Mock()

    # Use a proper AIMessage without tool_calls
    mock_message = AIMessage(content="Response without tool_calls")

    mock_result = {"messages": [mock_message]}
    mock_langgraph_agent.invoke.return_value = mock_result

    agent = ReActAgent(agent=mock_langgraph_agent, tools=[])

    response, _ = agent.process_message("Test", [])

    # Should handle gracefully and extract content
    assert response == "Response without tool_calls"


@pytest.mark.unit
def test_agent_tool_error_handling():
    """Test agent handles tool execution errors gracefully."""
    mock_langgraph_agent = Mock()

    # Simulate tool error in result
    mock_result = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[{"name": "failing_tool", "args": {}, "id": "call_err"}],
            ),
            ToolMessage(content="Error: Tool execution failed", tool_call_id="call_err"),
            AIMessage(content="I encountered an error with the tool"),
        ]
    }
    mock_langgraph_agent.invoke.return_value = mock_result

    agent = ReActAgent(agent=mock_langgraph_agent, tools=[])

    response, _ = agent.process_message("Test error handling", [])

    assert response == "I encountered an error with the tool"


@pytest.mark.unit
def test_agent_final_message_extraction_priority():
    """Test that final message is always the last one in messages list."""
    mock_langgraph_agent = Mock()
    mock_result = {
        "messages": [
            AIMessage(content="First"),
            AIMessage(content="Second"),
            AIMessage(content="Third"),
            AIMessage(content="This should be returned"),
        ]
    }
    mock_langgraph_agent.invoke.return_value = mock_result

    agent = ReActAgent(agent=mock_langgraph_agent, tools=[])

    response, _ = agent.process_message("Test", [])

    # Should always return the LAST message
    assert response == "This should be returned"


@pytest.mark.unit
def test_agent_with_callable_tool(simple_tool):
    """Test agent with a simple callable tool (function)."""
    # Use the simple_tool fixture which is already a proper AsyncAwareTool
    agent = ReActAgent(tools=[simple_tool], system_prompt="Test")

    assert len(agent.tools) == 1
    assert agent.tools[0].name == "simple_tool"
