"""
Test OpenAI LLM Adapter (Layer 2).

This module tests the OpenAI provider's LLM instantiation WITHOUT making API calls.
Tests verify that ChatOpenAI instances are created with correct parameters.

Test Strategy:
- Test with real OpenAI credentials (if available)
- Test parameter configuration (model, temperature, streaming)
- Test missing API key validation
- Test lazy import behavior
"""

import os
from unittest.mock import patch

import pytest

from chatforge.services.llm.factory import _get_openai_llm


# =============================================================================
# INSTANTIATION TESTS
# =============================================================================

@pytest.mark.unit
def test_openai_llm_instantiation():
    """Test that _get_openai_llm creates ChatOpenAI instance with correct parameters."""
    # Set a test API key (won't be used for API calls)
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key-for-testing"}):
        from chatforge.config import llm_config

        # Override config
        with patch.object(llm_config, "openai_api_key", "sk-test-key-for-testing"):
            llm = _get_openai_llm(
                model_name="gpt-4o-mini",
                streaming=False,
                temperature=0.0
            )

            # Verify it's a ChatOpenAI instance
            from langchain_openai import ChatOpenAI
            assert isinstance(llm, ChatOpenAI)

            # Verify parameters
            assert llm.model_name == "gpt-4o-mini"
            assert llm.temperature == 0.0
            # Note: streaming is harder to verify as it may be internal


@pytest.mark.unit
def test_openai_llm_with_different_model():
    """Test OpenAI instantiation with different model."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "openai_api_key", "sk-test-key"):
            llm = _get_openai_llm(
                model_name="gpt-4o",
                streaming=False,
                temperature=0.5
            )

            from langchain_openai import ChatOpenAI
            assert isinstance(llm, ChatOpenAI)
            assert llm.model_name == "gpt-4o"
            assert llm.temperature == 0.5


@pytest.mark.unit
def test_openai_streaming_enabled():
    """Test OpenAI instantiation with streaming enabled."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "openai_api_key", "sk-test-key"):
            llm = _get_openai_llm(
                model_name="gpt-4o-mini",
                streaming=True,
                temperature=0.0
            )

            from langchain_openai import ChatOpenAI
            assert isinstance(llm, ChatOpenAI)
            # streaming parameter is passed to constructor


@pytest.mark.unit
def test_openai_custom_temperature():
    """Test OpenAI with various temperature values."""
    test_temps = [0.0, 0.5, 0.7, 1.0, 2.0]

    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
        from chatforge.config import llm_config

        for temp in test_temps:
            with patch.object(llm_config, "openai_api_key", "sk-test-key"):
                llm = _get_openai_llm(
                    model_name="gpt-4o-mini",
                    streaming=False,
                    temperature=temp
                )

                from langchain_openai import ChatOpenAI
                assert isinstance(llm, ChatOpenAI)
                assert llm.temperature == temp


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

@pytest.mark.unit
def test_openai_missing_api_key_raises_error():
    """Test that missing API key raises ValueError with helpful message."""
    from chatforge.config import llm_config

    # Ensure no API key is set
    with patch.object(llm_config, "openai_api_key", None):
        with pytest.raises(ValueError, match="OpenAI API key not configured"):
            _get_openai_llm(
                model_name="gpt-4o-mini",
                streaming=False,
                temperature=0.0
            )


@pytest.mark.unit
def test_openai_empty_api_key_raises_error():
    """Test that empty API key raises ValueError."""
    from chatforge.config import llm_config

    with patch.object(llm_config, "openai_api_key", ""):
        with pytest.raises(ValueError, match="OpenAI API key not configured"):
            _get_openai_llm(
                model_name="gpt-4o-mini",
                streaming=False,
                temperature=0.0
            )


# =============================================================================
# LAZY IMPORT TESTS
# =============================================================================

@pytest.mark.unit
def test_openai_import_error_handling():
    """Test that ImportError is raised with helpful message if langchain-openai not installed."""
    from chatforge.config import llm_config

    with patch.object(llm_config, "openai_api_key", "sk-test-key"):
        # Mock the import to fail
        with patch("builtins.__import__", side_effect=ImportError("No module named 'langchain_openai'")):
            with pytest.raises(ImportError, match="langchain-openai is required"):
                _get_openai_llm(
                    model_name="gpt-4o-mini",
                    streaming=False,
                    temperature=0.0
                )


# =============================================================================
# VISION MODEL TESTS
# =============================================================================

@pytest.mark.unit
def test_openai_vision_model_gpt4o():
    """Test OpenAI with vision-capable model gpt-4o."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "openai_api_key", "sk-test-key"):
            llm = _get_openai_llm(
                model_name="gpt-4o",
                streaming=False,
                temperature=0.0
            )

            from langchain_openai import ChatOpenAI
            assert isinstance(llm, ChatOpenAI)
            assert llm.model_name == "gpt-4o"


@pytest.mark.unit
def test_openai_vision_model_gpt4o_mini():
    """Test OpenAI with vision-capable model gpt-4o-mini."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "openai_api_key", "sk-test-key"):
            llm = _get_openai_llm(
                model_name="gpt-4o-mini",
                streaming=False,
                temperature=0.0
            )

            from langchain_openai import ChatOpenAI
            assert isinstance(llm, ChatOpenAI)
            assert llm.model_name == "gpt-4o-mini"


# =============================================================================
# PARAMETER VALIDATION TESTS
# =============================================================================

@pytest.mark.unit
def test_openai_accepts_all_valid_models():
    """Test that OpenAI adapter accepts various valid model names."""
    valid_models = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
    ]

    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
        from chatforge.config import llm_config

        for model in valid_models:
            with patch.object(llm_config, "openai_api_key", "sk-test-key"):
                llm = _get_openai_llm(
                    model_name=model,
                    streaming=False,
                    temperature=0.0
                )

                from langchain_openai import ChatOpenAI
                assert isinstance(llm, ChatOpenAI)
                assert llm.model_name == model


@pytest.mark.unit
def test_openai_temperature_range():
    """Test that OpenAI accepts valid temperature range (0.0 to 2.0)."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
        from chatforge.config import llm_config

        # Test boundary values
        for temp in [0.0, 1.0, 2.0]:
            with patch.object(llm_config, "openai_api_key", "sk-test-key"):
                llm = _get_openai_llm(
                    model_name="gpt-4o-mini",
                    streaming=False,
                    temperature=temp
                )

                from langchain_openai import ChatOpenAI
                assert isinstance(llm, ChatOpenAI)
                assert llm.temperature == temp


# =============================================================================
# CONFIGURATION TESTS
# =============================================================================

@pytest.mark.unit
def test_openai_timeout_configuration():
    """Test that OpenAI LLM is created with timeout configuration."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "openai_api_key", "sk-test-key"):
            llm = _get_openai_llm(
                model_name="gpt-4o-mini",
                streaming=False,
                temperature=0.0
            )

            from langchain_openai import ChatOpenAI
            assert isinstance(llm, ChatOpenAI)
            # Verify timeout is set (should be 60 seconds based on factory code)
            assert llm.request_timeout == 60


@pytest.mark.unit
def test_openai_retry_configuration():
    """Test that OpenAI LLM is created with retry configuration."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
        from chatforge.config import llm_config

        with patch.object(llm_config, "openai_api_key", "sk-test-key"):
            llm = _get_openai_llm(
                model_name="gpt-4o-mini",
                streaming=False,
                temperature=0.0
            )

            from langchain_openai import ChatOpenAI
            assert isinstance(llm, ChatOpenAI)
            # Verify max_retries is set (should be 3 based on factory code)
            assert llm.max_retries == 3
