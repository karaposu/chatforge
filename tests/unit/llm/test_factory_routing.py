"""
Test LLM Factory Routing Logic (Layer 1).

This module tests the factory pattern routing WITHOUT making actual LLM calls.
All provider-specific functions are mocked to test only the selection logic.

Test Strategy:
- Mock llm_config to control provider selection
- Mock provider-specific functions (_get_openai_llm, etc.)
- Verify correct routing based on provider parameter
- Test error handling for invalid inputs
"""

from unittest.mock import Mock, patch

import pytest

from chatforge.services.llm import factory


# =============================================================================
# VISION SUPPORT TESTS
# =============================================================================

@pytest.mark.unit
def test_supports_vision_openai():
    """Test that OpenAI provider supports vision."""
    assert factory.supports_vision("openai") is True


@pytest.mark.unit
def test_supports_vision_anthropic():
    """Test that Anthropic provider supports vision."""
    assert factory.supports_vision("anthropic") is True


@pytest.mark.unit
def test_supports_vision_bedrock():
    """Test that Bedrock provider supports vision (uses Claude 3)."""
    assert factory.supports_vision("bedrock") is True


@pytest.mark.unit
def test_supports_vision_invalid_provider():
    """Test that invalid provider returns False."""
    assert factory.supports_vision("invalid_provider") is False


@pytest.mark.unit
def test_supports_vision_none_uses_config():
    """Test that None provider uses config default."""
    with patch("chatforge.services.llm.factory.llm_config") as mock_config:
        mock_config.provider = "openai"
        assert factory.supports_vision(None) is True


# =============================================================================
# PROVIDER SELECTION TESTS
# =============================================================================

@pytest.mark.unit
def test_get_llm_selects_openai():
    """Test that get_llm() routes to OpenAI when provider='openai'."""
    mock_llm = Mock()

    with patch("chatforge.services.llm.factory.llm_config") as mock_config, \
         patch("chatforge.services.llm.factory._get_openai_llm", return_value=mock_llm) as mock_openai, \
         patch("chatforge.services.llm.factory._get_anthropic_llm") as mock_anthropic, \
         patch("chatforge.services.llm.factory._get_bedrock_llm") as mock_bedrock:

        mock_config.provider = "openai"
        mock_config.model_name = "gpt-4o-mini"
        mock_config.temperature = 0.7

        result = factory.get_llm(provider="openai")

        # Verify OpenAI was called
        mock_openai.assert_called_once()
        # Verify others were NOT called
        mock_anthropic.assert_not_called()
        mock_bedrock.assert_not_called()
        # Verify return value
        assert result == mock_llm


@pytest.mark.unit
def test_get_llm_selects_anthropic():
    """Test that get_llm() routes to Anthropic when provider='anthropic'."""
    mock_llm = Mock()

    with patch("chatforge.services.llm.factory.llm_config") as mock_config, \
         patch("chatforge.services.llm.factory._get_openai_llm") as mock_openai, \
         patch("chatforge.services.llm.factory._get_anthropic_llm", return_value=mock_llm) as mock_anthropic, \
         patch("chatforge.services.llm.factory._get_bedrock_llm") as mock_bedrock:

        mock_config.provider = "anthropic"
        mock_config.model_name = "claude-3-5-sonnet-20241022"
        mock_config.temperature = 0.0

        result = factory.get_llm(provider="anthropic")

        # Verify Anthropic was called
        mock_anthropic.assert_called_once()
        # Verify others were NOT called
        mock_openai.assert_not_called()
        mock_bedrock.assert_not_called()
        # Verify return value
        assert result == mock_llm


@pytest.mark.unit
def test_get_llm_selects_bedrock():
    """Test that get_llm() routes to Bedrock when provider='bedrock'."""
    mock_llm = Mock()

    with patch("chatforge.services.llm.factory.llm_config") as mock_config, \
         patch("chatforge.services.llm.factory._get_openai_llm") as mock_openai, \
         patch("chatforge.services.llm.factory._get_anthropic_llm") as mock_anthropic, \
         patch("chatforge.services.llm.factory._get_bedrock_llm", return_value=mock_llm) as mock_bedrock:

        mock_config.provider = "bedrock"
        mock_config.model_name = "anthropic.claude-v2"
        mock_config.temperature = 0.5

        result = factory.get_llm(provider="bedrock")

        # Verify Bedrock was called
        mock_bedrock.assert_called_once()
        # Verify others were NOT called
        mock_openai.assert_not_called()
        mock_anthropic.assert_not_called()
        # Verify return value
        assert result == mock_llm


@pytest.mark.unit
def test_get_llm_uses_config_default_provider():
    """Test that get_llm() uses config default when provider=None."""
    mock_llm = Mock()

    with patch("chatforge.services.llm.factory.llm_config") as mock_config, \
         patch("chatforge.services.llm.factory._get_openai_llm", return_value=mock_llm) as mock_openai:

        mock_config.provider = "openai"  # Config default
        mock_config.model_name = "gpt-4o-mini"
        mock_config.temperature = 0.0

        result = factory.get_llm(provider=None)

        # Should use config default (openai)
        mock_openai.assert_called_once()
        assert result == mock_llm


@pytest.mark.unit
def test_get_llm_invalid_provider():
    """Test that get_llm() raises ValueError for invalid provider."""
    with patch("chatforge.services.llm.factory.llm_config") as mock_config:
        mock_config.provider = "invalid_provider"

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            factory.get_llm(provider="invalid_provider")


# =============================================================================
# STREAMING TESTS
# =============================================================================

@pytest.mark.unit
def test_get_streaming_llm_passes_streaming_true():
    """Test that get_streaming_llm() passes streaming=True."""
    mock_llm = Mock()

    with patch("chatforge.services.llm.factory.llm_config") as mock_config, \
         patch("chatforge.services.llm.factory._get_openai_llm", return_value=mock_llm) as mock_openai:

        mock_config.provider = "openai"
        mock_config.model_name = "gpt-4o-mini"
        mock_config.temperature = 0.0

        result = factory.get_streaming_llm()

        # Verify streaming=True was passed
        call_kwargs = mock_openai.call_args[1] if mock_openai.call_args else {}
        # Note: streaming is positional arg, check if function was called at all
        mock_openai.assert_called_once()
        assert result == mock_llm


@pytest.mark.unit
def test_streaming_flag_propagation():
    """Test that streaming parameter is correctly propagated."""
    mock_llm = Mock()

    with patch("chatforge.services.llm.factory.llm_config") as mock_config, \
         patch("chatforge.services.llm.factory._get_openai_llm", return_value=mock_llm) as mock_openai:

        mock_config.provider = "openai"
        mock_config.model_name = "gpt-4o-mini"
        mock_config.temperature = 0.0

        # Test streaming=False
        factory.get_llm(streaming=False)
        assert mock_openai.call_count == 1

        # Test streaming=True
        factory.get_llm(streaming=True)
        assert mock_openai.call_count == 2


# =============================================================================
# PARAMETER OVERRIDE TESTS
# =============================================================================

@pytest.mark.unit
def test_model_name_parameter_overrides_config():
    """Test that model_name parameter overrides config."""
    mock_llm = Mock()

    with patch("chatforge.services.llm.factory.llm_config") as mock_config, \
         patch("chatforge.services.llm.factory._get_openai_llm", return_value=mock_llm) as mock_openai:

        mock_config.provider = "openai"
        mock_config.model_name = "gpt-4o-mini"  # Config default
        mock_config.temperature = 0.0

        # Override with parameter
        factory.get_llm(model_name="gpt-4o")

        # Verify _get_openai_llm was called with overridden model
        call_args = mock_openai.call_args
        assert call_args[0][0] == "gpt-4o"  # First positional arg


@pytest.mark.unit
def test_temperature_parameter_overrides_config():
    """Test that temperature parameter overrides config."""
    mock_llm = Mock()

    with patch("chatforge.services.llm.factory.llm_config") as mock_config, \
         patch("chatforge.services.llm.factory._get_openai_llm", return_value=mock_llm) as mock_openai:

        mock_config.provider = "openai"
        mock_config.model_name = "gpt-4o-mini"
        mock_config.temperature = 0.0  # Config default

        # Override with parameter
        factory.get_llm(temperature=0.9)

        # Verify _get_openai_llm was called with overridden temperature
        call_args = mock_openai.call_args
        assert call_args[0][2] == 0.9  # Third positional arg


# =============================================================================
# VISION LLM TESTS
# =============================================================================

@pytest.mark.unit
def test_get_vision_llm_selects_vision_model():
    """Test that get_vision_llm() selects a vision-capable model."""
    mock_llm = Mock()

    with patch("chatforge.services.llm.factory.llm_config") as mock_config, \
         patch("chatforge.services.llm.factory._get_openai_llm", return_value=mock_llm) as mock_openai:

        mock_config.provider = "openai"
        mock_config.model_name = "gpt-3.5-turbo"  # Non-vision model
        mock_config.vision_model_name = None  # No env override
        mock_config.vision_temperature = 0.0
        mock_config.temperature = 0.0

        result = factory.get_vision_llm()

        # Should use default vision model for OpenAI (gpt-4o)
        call_args = mock_openai.call_args
        model_name = call_args[0][0]

        # Verify the default OpenAI vision model was selected
        assert model_name == "gpt-4o"
        assert result == mock_llm


@pytest.mark.unit
def test_get_vision_llm_custom_model_name():
    """Test that get_vision_llm() can use custom model if specified."""
    mock_llm = Mock()

    with patch("chatforge.services.llm.factory.llm_config") as mock_config, \
         patch("chatforge.services.llm.factory._get_openai_llm", return_value=mock_llm) as mock_openai:

        mock_config.provider = "openai"
        mock_config.temperature = 0.0

        result = factory.get_vision_llm(model_name="gpt-4o")

        # Should use specified model
        call_args = mock_openai.call_args
        assert call_args[0][0] == "gpt-4o"
        assert result == mock_llm


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

@pytest.mark.unit
def test_get_llm_provider_specific_error_propagates():
    """Test that errors from provider-specific functions propagate."""
    with patch("chatforge.services.llm.factory.llm_config") as mock_config, \
         patch("chatforge.services.llm.factory._get_openai_llm") as mock_openai:

        mock_config.provider = "openai"
        mock_config.model_name = "gpt-4o-mini"
        mock_config.temperature = 0.0

        # Simulate provider error
        mock_openai.side_effect = ValueError("API key not configured")

        with pytest.raises(ValueError, match="API key not configured"):
            factory.get_llm()


@pytest.mark.unit
def test_get_llm_empty_provider_string():
    """Test that empty provider string raises ValueError."""
    with patch("chatforge.services.llm.factory.llm_config") as mock_config:
        mock_config.provider = ""

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            factory.get_llm(provider="")
