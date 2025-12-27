"""
Test Anthropic LLM Adapter (Layer 2).

This module tests the Anthropic provider's LLM instantiation WITHOUT making API calls.
Tests verify that ChatAnthropic instances are created with correct parameters.

Test Strategy:
- Test with mock Anthropic credentials
- Test parameter configuration (model, temperature, streaming)
- Test missing API key validation
- Test lazy import behavior

Note: These tests require langchain-anthropic to be installed.
      Run: pip install chatforge[anthropic]
"""

import os
from unittest.mock import patch

import pytest

# Skip all tests in this module if langchain-anthropic not installed
pytest.importorskip("langchain_anthropic", reason="langchain-anthropic required for Anthropic tests")

from chatforge.services.llm.factory import _get_anthropic_llm


# =============================================================================
# INSTANTIATION TESTS
# =============================================================================

@pytest.mark.unit
def test_anthropic_llm_instantiation():
    """Test that _get_anthropic_llm creates ChatAnthropic instance with correct parameters."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "anthropic_api_key", "sk-ant-test-key"):
            llm = _get_anthropic_llm(
                model_name="claude-3-5-sonnet-20241022",
                streaming=False,
                temperature=0.0
            )

            # Verify it's a ChatAnthropic instance
            from langchain_anthropic import ChatAnthropic
            assert isinstance(llm, ChatAnthropic)

            # Verify parameters
            assert llm.model == "claude-3-5-sonnet-20241022"
            assert llm.temperature == 0.0


@pytest.mark.unit
def test_anthropic_llm_with_different_model():
    """Test Anthropic instantiation with different Claude models."""
    models = [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-latest",
        "claude-3-opus-20240229",
        "claude-3-haiku-20240307",
    ]

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"}):
        from chatforge.config import llm_config

        for model in models:
            with patch.object(llm_config, "anthropic_api_key", "sk-ant-test-key"):
                llm = _get_anthropic_llm(
                    model_name=model,
                    streaming=False,
                    temperature=0.0
                )

                from langchain_anthropic import ChatAnthropic
                assert isinstance(llm, ChatAnthropic)
                assert llm.model == model


@pytest.mark.unit
def test_anthropic_streaming_enabled():
    """Test Anthropic instantiation with streaming enabled."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "anthropic_api_key", "sk-ant-test-key"):
            llm = _get_anthropic_llm(
                model_name="claude-3-5-sonnet-20241022",
                streaming=True,
                temperature=0.0
            )

            from langchain_anthropic import ChatAnthropic
            assert isinstance(llm, ChatAnthropic)
            # streaming parameter is passed to constructor


@pytest.mark.unit
def test_anthropic_custom_temperature():
    """Test Anthropic with various temperature values."""
    test_temps = [0.0, 0.5, 0.7, 1.0]

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"}):
        from chatforge.config import llm_config

        for temp in test_temps:
            with patch.object(llm_config, "anthropic_api_key", "sk-ant-test-key"):
                llm = _get_anthropic_llm(
                    model_name="claude-3-5-sonnet-20241022",
                    streaming=False,
                    temperature=temp
                )

                from langchain_anthropic import ChatAnthropic
                assert isinstance(llm, ChatAnthropic)
                assert llm.temperature == temp


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

@pytest.mark.unit
def test_anthropic_missing_api_key_raises_error():
    """Test that missing API key raises ValueError with helpful message."""
    from chatforge.config import llm_config

    with patch.object(llm_config, "anthropic_api_key", None):
        with pytest.raises(ValueError, match="Anthropic API key not configured"):
            _get_anthropic_llm(
                model_name="claude-3-5-sonnet-20241022",
                streaming=False,
                temperature=0.0
            )


@pytest.mark.unit
def test_anthropic_empty_api_key_raises_error():
    """Test that empty API key raises ValueError."""
    from chatforge.config import llm_config

    with patch.object(llm_config, "anthropic_api_key", ""):
        with pytest.raises(ValueError, match="Anthropic API key not configured"):
            _get_anthropic_llm(
                model_name="claude-3-5-sonnet-20241022",
                streaming=False,
                temperature=0.0
            )


# =============================================================================
# LAZY IMPORT TESTS
# =============================================================================

@pytest.mark.unit
def test_anthropic_import_error_handling():
    """Test that ImportError is raised with helpful message if langchain-anthropic not installed."""
    from chatforge.config import llm_config

    with patch.object(llm_config, "anthropic_api_key", "sk-ant-test-key"):
        # Mock the import to fail
        with patch("builtins.__import__", side_effect=ImportError("No module named 'langchain_anthropic'")):
            with pytest.raises(ImportError, match="langchain-anthropic is required"):
                _get_anthropic_llm(
                    model_name="claude-3-5-sonnet-20241022",
                    streaming=False,
                    temperature=0.0
                )


# =============================================================================
# VISION MODEL TESTS
# =============================================================================

@pytest.mark.unit
def test_anthropic_vision_model_claude35_sonnet():
    """Test Anthropic with vision-capable model Claude 3.5 Sonnet."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "anthropic_api_key", "sk-ant-test-key"):
            llm = _get_anthropic_llm(
                model_name="claude-3-5-sonnet-latest",
                streaming=False,
                temperature=0.0
            )

            from langchain_anthropic import ChatAnthropic
            assert isinstance(llm, ChatAnthropic)
            assert llm.model == "claude-3-5-sonnet-latest"


@pytest.mark.unit
def test_anthropic_vision_model_claude3_opus():
    """Test Anthropic with vision-capable model Claude 3 Opus."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "anthropic_api_key", "sk-ant-test-key"):
            llm = _get_anthropic_llm(
                model_name="claude-3-opus-20240229",
                streaming=False,
                temperature=0.0
            )

            from langchain_anthropic import ChatAnthropic
            assert isinstance(llm, ChatAnthropic)
            assert llm.model == "claude-3-opus-20240229"


# =============================================================================
# CONFIGURATION TESTS
# =============================================================================

@pytest.mark.unit
def test_anthropic_timeout_configuration():
    """Test that Anthropic LLM is created with timeout configuration."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "anthropic_api_key", "sk-ant-test-key"):
            llm = _get_anthropic_llm(
                model_name="claude-3-5-sonnet-20241022",
                streaming=False,
                temperature=0.0
            )

            from langchain_anthropic import ChatAnthropic
            assert isinstance(llm, ChatAnthropic)
            # Verify timeout is set (should be 60 seconds based on factory code)
            assert llm.timeout == 60


@pytest.mark.unit
def test_anthropic_retry_configuration():
    """Test that Anthropic LLM is created with retry configuration."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "anthropic_api_key", "sk-ant-test-key"):
            llm = _get_anthropic_llm(
                model_name="claude-3-5-sonnet-20241022",
                streaming=False,
                temperature=0.0
            )

            from langchain_anthropic import ChatAnthropic
            assert isinstance(llm, ChatAnthropic)
            # Verify max_retries is set (should be 3 based on factory code)
            assert llm.max_retries == 3


# =============================================================================
# TEMPERATURE BOUNDARY TESTS
# =============================================================================

@pytest.mark.unit
def test_anthropic_temperature_boundaries():
    """Test Anthropic temperature at boundary values."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"}):
        from chatforge.config import llm_config

        # Anthropic supports 0.0 to 1.0
        for temp in [0.0, 0.5, 1.0]:
            with patch.object(llm_config, "anthropic_api_key", "sk-ant-test-key"):
                llm = _get_anthropic_llm(
                    model_name="claude-3-5-sonnet-20241022",
                    streaming=False,
                    temperature=temp
                )

                from langchain_anthropic import ChatAnthropic
                assert isinstance(llm, ChatAnthropic)
                assert llm.temperature == temp
