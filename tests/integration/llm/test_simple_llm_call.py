"""
Test Simple LLM Calls (Layer 4: Full Integration).

This module tests actual LLM API calls end-to-end. These tests make REAL API calls
and will incur costs. They should be run selectively (not on every commit).

Test Strategy:
- Use real API keys from environment variables
- Make minimal API calls (to reduce costs)
- Use cheapest models (gpt-4o-mini, claude-3-haiku)
- Test basic functionality only (extensive testing in unit tests)
- Skip tests if API keys not available

Environment Variables Required:
- OPENAI_API_KEY: For OpenAI tests
- ANTHROPIC_API_KEY: For Anthropic tests (optional)
- AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY: For Bedrock tests (optional)

Usage:
  # Skip integration tests (default)
  pytest tests/unit/llm/

  # Run integration tests (requires API keys, costs money)
  pytest tests/integration/llm/ -v --run-integration

  # Run with verbose output
  pytest tests/integration/llm/ -v -s --run-integration
"""

import os

import pytest
from langchain_core.messages import HumanMessage


# =============================================================================
# BASIC LLM CALL TESTS
# =============================================================================

@pytest.mark.integration
@pytest.mark.expensive
def test_simple_openai_call():
    """Test simple OpenAI LLM call with gpt-4o-mini (cheapest)."""
    # Skip if no API key
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    from chatforge.services.llm.factory import get_llm

    # Use cheapest model to minimize costs
    llm = get_llm(provider="openai", model_name="gpt-4o-mini", temperature=0.0)

    # Simple test message
    message = HumanMessage(content="Say exactly: 'test successful'")

    # Make API call
    response = llm.invoke([message])

    # Verify response
    assert response is not None
    assert hasattr(response, "content")
    assert isinstance(response.content, str)
    assert len(response.content) > 0
    print(f"\nOpenAI Response: {response.content}")


@pytest.mark.integration
@pytest.mark.expensive
def test_simple_anthropic_call():
    """Test simple Anthropic LLM call with Claude 3 Haiku (cheapest)."""
    # Skip if no API key or package not installed
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")

    pytest.importorskip("langchain_anthropic", reason="langchain-anthropic required")

    from chatforge.services.llm.factory import get_llm

    # Use cheapest Claude model
    llm = get_llm(
        provider="anthropic",
        model_name="claude-3-haiku-20240307",
        temperature=0.0
    )

    message = HumanMessage(content="Say exactly: 'test successful'")
    response = llm.invoke([message])

    assert response is not None
    assert hasattr(response, "content")
    assert isinstance(response.content, str)
    assert len(response.content) > 0
    print(f"\nAnthropic Response: {response.content}")


@pytest.mark.integration
@pytest.mark.expensive
def test_simple_bedrock_call():
    """Test simple Bedrock LLM call with Claude Instant (cheapest)."""
    # Skip if no AWS credentials or package not installed
    if not (os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY")):
        pytest.skip("AWS credentials not set")

    pytest.importorskip("boto3", reason="boto3 required for Bedrock")

    from chatforge.services.llm.factory import get_llm

    # Use cheapest Bedrock Claude model
    llm = get_llm(
        provider="bedrock",
        model_name="anthropic.claude-instant-v1",
        temperature=0.0
    )

    message = HumanMessage(content="Say exactly: 'test successful'")
    response = llm.invoke([message])

    assert response is not None
    assert hasattr(response, "content")
    assert isinstance(response.content, str)
    assert len(response.content) > 0
    print(f"\nBedrock Response: {response.content}")


# =============================================================================
# STREAMING TESTS
# =============================================================================

@pytest.mark.integration
@pytest.mark.expensive
def test_streaming_openai_call():
    """Test OpenAI streaming with gpt-4o-mini."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    from chatforge.services.llm.factory import get_llm

    llm = get_llm(provider="openai", model_name="gpt-4o-mini", streaming=True)

    message = HumanMessage(content="Count from 1 to 5, one number per line.")

    # Stream response
    chunks = []
    for chunk in llm.stream([message]):
        chunks.append(chunk)
        if hasattr(chunk, "content"):
            print(f"Chunk: {chunk.content}", end="", flush=True)

    # Verify we received multiple chunks
    assert len(chunks) > 0, "Should receive at least one chunk"
    print(f"\nReceived {len(chunks)} chunks")


@pytest.mark.integration
@pytest.mark.expensive
def test_streaming_anthropic_call():
    """Test Anthropic streaming with Claude Haiku."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")

    pytest.importorskip("langchain_anthropic")

    from chatforge.services.llm.factory import get_llm

    llm = get_llm(
        provider="anthropic",
        model_name="claude-3-haiku-20240307",
        streaming=True
    )

    message = HumanMessage(content="Count from 1 to 5, one number per line.")

    chunks = []
    for chunk in llm.stream([message]):
        chunks.append(chunk)
        if hasattr(chunk, "content"):
            print(f"Chunk: {chunk.content}", end="", flush=True)

    assert len(chunks) > 0
    print(f"\nReceived {len(chunks)} chunks")


# =============================================================================
# PARAMETER VARIATION TESTS
# =============================================================================

@pytest.mark.integration
@pytest.mark.expensive
def test_openai_temperature_variation():
    """Test that temperature affects OpenAI responses."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    from chatforge.services.llm.factory import get_llm

    message = HumanMessage(content="Say 'hello' in a creative way.")

    # Test with temperature 0.0 (deterministic)
    llm_low = get_llm(provider="openai", model_name="gpt-4o-mini", temperature=0.0)
    response_low = llm_low.invoke([message])

    # Test with temperature 1.0 (more creative)
    llm_high = get_llm(provider="openai", model_name="gpt-4o-mini", temperature=1.0)
    response_high = llm_high.invoke([message])

    # Both should return valid responses
    assert response_low.content
    assert response_high.content

    print(f"\nLow temp (0.0): {response_low.content}")
    print(f"High temp (1.0): {response_high.content}")


@pytest.mark.integration
@pytest.mark.expensive
def test_openai_different_models():
    """Test that different OpenAI models work."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    from chatforge.services.llm.factory import get_llm

    models = ["gpt-4o-mini", "gpt-4o"]
    message = HumanMessage(content="Say 'test'")

    for model in models:
        llm = get_llm(provider="openai", model_name=model)
        response = llm.invoke([message])

        assert response.content
        print(f"\n{model}: {response.content}")


# =============================================================================
# CONVERSATION HISTORY TESTS
# =============================================================================

@pytest.mark.integration
@pytest.mark.expensive
def test_openai_conversation_history():
    """Test OpenAI with multi-turn conversation."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    from chatforge.services.llm.factory import get_llm
    from langchain_core.messages import AIMessage

    llm = get_llm(provider="openai", model_name="gpt-4o-mini")

    # Build conversation history
    messages = [
        HumanMessage(content="My favorite color is blue."),
        AIMessage(content="That's nice! Blue is a great color."),
        HumanMessage(content="What is my favorite color?"),
    ]

    response = llm.invoke(messages)

    # Should remember the color from earlier in conversation
    assert response.content
    assert "blue" in response.content.lower()
    print(f"\nConversation response: {response.content}")


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

@pytest.mark.integration
@pytest.mark.expensive
def test_openai_invalid_api_key():
    """Test that invalid API key raises proper error."""
    from chatforge.config import llm_config
    from chatforge.services.llm.factory import get_llm
    from unittest.mock import patch

    # Override with invalid key
    with patch.object(llm_config, "openai_api_key", "sk-invalid-key-12345"):
        llm = get_llm(provider="openai", model_name="gpt-4o-mini")
        message = HumanMessage(content="test")

        # Should raise authentication error
        with pytest.raises(Exception) as exc_info:
            llm.invoke([message])

        # Error should mention authentication/API key
        error_msg = str(exc_info.value).lower()
        assert any(word in error_msg for word in ["auth", "api", "key", "invalid", "unauthorized"])
        print(f"\nExpected error: {exc_info.value}")


# =============================================================================
# VISION LLM TESTS (if vision models supported)
# =============================================================================

@pytest.mark.integration
@pytest.mark.expensive
def test_vision_llm_text_only():
    """Test that vision LLM can handle text-only messages."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    from chatforge.services.llm.factory import get_vision_llm

    # Get vision-capable LLM
    llm = get_vision_llm(provider="openai")

    # Send text-only message (vision models should handle this)
    message = HumanMessage(content="Say 'vision test successful'")
    response = llm.invoke([message])

    assert response.content
    print(f"\nVision LLM text response: {response.content}")


# =============================================================================
# ASYNC TESTS
# =============================================================================

@pytest.mark.integration
@pytest.mark.expensive
@pytest.mark.asyncio
async def test_openai_async_call():
    """Test OpenAI async invocation with ainvoke."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    from chatforge.services.llm.factory import get_llm

    llm = get_llm(provider="openai", model_name="gpt-4o-mini")

    message = HumanMessage(content="Say 'async test successful'")

    # Use ainvoke for async call
    response = await llm.ainvoke([message])

    assert response.content
    print(f"\nAsync response: {response.content}")


@pytest.mark.integration
@pytest.mark.expensive
@pytest.mark.asyncio
async def test_openai_async_streaming():
    """Test OpenAI async streaming with astream."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    from chatforge.services.llm.factory import get_llm

    llm = get_llm(provider="openai", model_name="gpt-4o-mini", streaming=True)

    message = HumanMessage(content="Count from 1 to 3.")

    chunks = []
    async for chunk in llm.astream([message]):
        chunks.append(chunk)
        if hasattr(chunk, "content"):
            print(f"Async chunk: {chunk.content}", end="", flush=True)

    assert len(chunks) > 0
    print(f"\nReceived {len(chunks)} async chunks")


# =============================================================================
# TIMEOUT AND RETRY TESTS
# =============================================================================

@pytest.mark.integration
@pytest.mark.expensive
def test_openai_with_timeout():
    """Test that LLM respects timeout configuration."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    from chatforge.services.llm.factory import get_llm

    # LLM created with default timeout (60s from factory)
    llm = get_llm(provider="openai", model_name="gpt-4o-mini")

    # Verify timeout is set
    assert hasattr(llm, "request_timeout")
    assert llm.request_timeout == 60

    # Simple call should complete within timeout
    message = HumanMessage(content="Say 'timeout test'")
    response = llm.invoke([message])

    assert response.content
    print(f"\nTimeout test response: {response.content}")


# =============================================================================
# COST-CONSCIOUS TESTS (minimal tokens)
# =============================================================================

@pytest.mark.integration
@pytest.mark.expensive
def test_minimal_token_call():
    """Test with absolute minimal tokens to reduce costs."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    from chatforge.services.llm.factory import get_llm

    llm = get_llm(provider="openai", model_name="gpt-4o-mini", temperature=0.0)

    # Single character input and output
    message = HumanMessage(content="Hi")
    response = llm.invoke([message])

    assert response.content
    assert len(response.content) > 0

    print(f"\nMinimal token response: {response.content}")
    print(f"Response length: {len(response.content)} chars")
