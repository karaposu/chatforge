"""
Test LLM Interface Conformance (Layer 3).

This module tests that LLMs returned by the factory conform to LangChain's
BaseChatModel protocol. We verify the interface contracts without making API calls.

Test Strategy:
- Test that returned objects are BaseChatModel instances
- Test that required methods exist (invoke, ainvoke, stream, etc.)
- Test that attributes are properly set
- Test interface consistency across providers

Note: These are interface tests - we verify methods exist and have correct
      signatures, but we don't actually call them (no API calls).
"""

from unittest.mock import patch

import pytest


# =============================================================================
# BASECHATMODEL CONFORMANCE TESTS
# =============================================================================

@pytest.mark.unit
def test_openai_llm_is_base_chat_model():
    """Test that OpenAI LLM is a BaseChatModel instance."""
    from chatforge.services.llm.factory import get_llm

    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "openai_api_key", "sk-test-key"):
            llm = get_llm(provider="openai", model_name="gpt-4o-mini")

            # Verify it's a BaseChatModel
            from langchain_core.language_models import BaseChatModel
            assert isinstance(llm, BaseChatModel)


@pytest.mark.unit
def test_anthropic_llm_is_base_chat_model():
    """Test that Anthropic LLM is a BaseChatModel instance."""
    pytest.importorskip("langchain_anthropic", reason="langchain-anthropic required")

    from chatforge.services.llm.factory import get_llm

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "anthropic_api_key", "sk-ant-test-key"):
            llm = get_llm(provider="anthropic", model_name="claude-3-5-sonnet-20241022")

            from langchain_core.language_models import BaseChatModel
            assert isinstance(llm, BaseChatModel)


@pytest.mark.unit
def test_bedrock_llm_is_base_chat_model():
    """Test that Bedrock LLM is a BaseChatModel instance."""
    pytest.importorskip("boto3", reason="boto3 required for Bedrock")

    from chatforge.services.llm.factory import get_llm

    with patch.dict("os.environ", {
        "AWS_ACCESS_KEY_ID": "AKIATEST123456",
        "AWS_SECRET_ACCESS_KEY": "test-secret-key"
    }):
        from chatforge.config import llm_config

        with patch.object(llm_config, "aws_access_key_id", "AKIATEST123456"), \
             patch.object(llm_config, "aws_secret_access_key", "test-secret-key"), \
             patch.object(llm_config, "aws_region", "us-east-1"):

            llm = get_llm(provider="bedrock", model_name="anthropic.claude-v2")

            from langchain_core.language_models import BaseChatModel
            assert isinstance(llm, BaseChatModel)


# =============================================================================
# METHOD EXISTENCE TESTS
# =============================================================================

@pytest.mark.unit
def test_llm_has_invoke_method():
    """Test that LLM has invoke() method."""
    from chatforge.services.llm.factory import get_llm

    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "openai_api_key", "sk-test-key"):
            llm = get_llm(provider="openai")

            # Verify invoke method exists
            assert hasattr(llm, "invoke")
            assert callable(llm.invoke)


@pytest.mark.unit
def test_llm_has_ainvoke_method():
    """Test that LLM has ainvoke() method for async support."""
    from chatforge.services.llm.factory import get_llm

    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "openai_api_key", "sk-test-key"):
            llm = get_llm(provider="openai")

            # Verify ainvoke method exists (async variant)
            assert hasattr(llm, "ainvoke")
            assert callable(llm.ainvoke)


@pytest.mark.unit
def test_llm_has_stream_method():
    """Test that LLM has stream() method."""
    from chatforge.services.llm.factory import get_llm

    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "openai_api_key", "sk-test-key"):
            llm = get_llm(provider="openai")

            # Verify stream method exists
            assert hasattr(llm, "stream")
            assert callable(llm.stream)


@pytest.mark.unit
def test_llm_has_astream_method():
    """Test that LLM has astream() method for async streaming."""
    from chatforge.services.llm.factory import get_llm

    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "openai_api_key", "sk-test-key"):
            llm = get_llm(provider="openai")

            # Verify astream method exists
            assert hasattr(llm, "astream")
            assert callable(llm.astream)


@pytest.mark.unit
def test_llm_has_bind_method():
    """Test that LLM has bind() method for parameter binding."""
    from chatforge.services.llm.factory import get_llm

    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "openai_api_key", "sk-test-key"):
            llm = get_llm(provider="openai")

            # Verify bind method exists
            assert hasattr(llm, "bind")
            assert callable(llm.bind)


@pytest.mark.unit
def test_llm_has_with_retry_method():
    """Test that LLM has with_retry() method."""
    from chatforge.services.llm.factory import get_llm

    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "openai_api_key", "sk-test-key"):
            llm = get_llm(provider="openai")

            # Verify with_retry method exists
            assert hasattr(llm, "with_retry")
            assert callable(llm.with_retry)


# =============================================================================
# INTERFACE CONSISTENCY TESTS
# =============================================================================

@pytest.mark.unit
def test_all_providers_have_consistent_interface():
    """Test that all providers return LLMs with consistent interface."""
    from chatforge.services.llm.factory import get_llm

    # Define expected methods that all LLMs should have
    expected_methods = [
        "invoke",
        "ainvoke",
        "stream",
        "astream",
        "bind",
        "with_retry",
    ]

    # Test OpenAI
    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "openai_api_key", "sk-test-key"):
            openai_llm = get_llm(provider="openai")

            for method in expected_methods:
                assert hasattr(openai_llm, method), f"OpenAI LLM missing {method}"
                assert callable(getattr(openai_llm, method)), f"OpenAI {method} not callable"

    # Test Anthropic (if available)
    try:
        pytest.importorskip("langchain_anthropic")

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test-key"}):
            with patch.object(llm_config, "anthropic_api_key", "sk-ant-test-key"):
                anthropic_llm = get_llm(provider="anthropic")

                for method in expected_methods:
                    assert hasattr(anthropic_llm, method), f"Anthropic LLM missing {method}"
                    assert callable(getattr(anthropic_llm, method)), f"Anthropic {method} not callable"
    except ImportError:
        pytest.skip("langchain-anthropic not installed")


# =============================================================================
# STREAMING LLM INTERFACE TESTS
# =============================================================================

@pytest.mark.unit
def test_streaming_llm_has_same_interface():
    """Test that streaming LLM has same interface as non-streaming."""
    from chatforge.services.llm.factory import get_llm

    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "openai_api_key", "sk-test-key"):
            # Get both streaming and non-streaming LLMs
            regular_llm = get_llm(provider="openai", streaming=False)
            streaming_llm = get_llm(provider="openai", streaming=True)

            # Both should be BaseChatModel
            from langchain_core.language_models import BaseChatModel
            assert isinstance(regular_llm, BaseChatModel)
            assert isinstance(streaming_llm, BaseChatModel)

            # Both should have same methods
            expected_methods = ["invoke", "ainvoke", "stream", "astream"]
            for method in expected_methods:
                assert hasattr(regular_llm, method)
                assert hasattr(streaming_llm, method)


# =============================================================================
# VISION LLM INTERFACE TESTS
# =============================================================================

@pytest.mark.unit
def test_vision_llm_has_same_interface():
    """Test that vision LLM has same interface as regular LLM."""
    from chatforge.services.llm.factory import get_llm, get_vision_llm

    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "openai_api_key", "sk-test-key"), \
             patch.object(llm_config, "vision_model_name", None), \
             patch.object(llm_config, "vision_temperature", 0.0):

            regular_llm = get_llm(provider="openai")
            vision_llm = get_vision_llm(provider="openai")

            # Both should be BaseChatModel
            from langchain_core.language_models import BaseChatModel
            assert isinstance(regular_llm, BaseChatModel)
            assert isinstance(vision_llm, BaseChatModel)

            # Both should have same interface
            expected_methods = ["invoke", "ainvoke", "stream", "astream"]
            for method in expected_methods:
                assert hasattr(regular_llm, method)
                assert hasattr(vision_llm, method)


# =============================================================================
# ATTRIBUTE TESTS
# =============================================================================

@pytest.mark.unit
def test_llm_has_model_name_attribute():
    """Test that LLM has model_name or model attribute."""
    from chatforge.services.llm.factory import get_llm

    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "openai_api_key", "sk-test-key"):
            llm = get_llm(provider="openai", model_name="gpt-4o-mini")

            # OpenAI uses model_name
            assert hasattr(llm, "model_name")
            assert llm.model_name == "gpt-4o-mini"


@pytest.mark.unit
def test_llm_has_temperature_attribute():
    """Test that LLM has temperature attribute."""
    from chatforge.services.llm.factory import get_llm

    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "openai_api_key", "sk-test-key"):
            llm = get_llm(provider="openai", temperature=0.7)

            # All LLMs should have temperature
            assert hasattr(llm, "temperature")
            assert llm.temperature == 0.7


# =============================================================================
# RUNNABLE INTERFACE TESTS
# =============================================================================

@pytest.mark.unit
def test_llm_is_runnable():
    """Test that LLM implements Runnable interface (LangChain LCEL)."""
    from chatforge.services.llm.factory import get_llm

    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "openai_api_key", "sk-test-key"):
            llm = get_llm(provider="openai")

            # BaseChatModel extends Runnable
            from langchain_core.runnables import Runnable
            assert isinstance(llm, Runnable)


@pytest.mark.unit
def test_llm_has_pipe_method():
    """Test that LLM has pipe() method for chaining (LCEL)."""
    from chatforge.services.llm.factory import get_llm

    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "openai_api_key", "sk-test-key"):
            llm = get_llm(provider="openai")

            # Runnable interface includes pipe
            assert hasattr(llm, "pipe")
            assert callable(llm.pipe)
