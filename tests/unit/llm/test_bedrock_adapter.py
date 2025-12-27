"""
Test AWS Bedrock LLM Adapter (Layer 2).

This module tests the Bedrock provider's LLM instantiation WITHOUT making API calls.
Tests verify that BedrockChat instances are created with correct parameters.

Test Strategy:
- Test with mock AWS credentials
- Test parameter configuration (model, temperature, streaming)
- Test missing credentials validation
- Test lazy import behavior

Note: These tests require boto3 to be installed.
      Run: pip install chatforge[bedrock]
"""

import os
from unittest.mock import patch

import pytest

# Skip all tests in this module if boto3 not installed
pytest.importorskip("boto3", reason="boto3 required for Bedrock tests")

from chatforge.services.llm.factory import _get_bedrock_llm


# =============================================================================
# INSTANTIATION TESTS
# =============================================================================

@pytest.mark.unit
def test_bedrock_llm_instantiation():
    """Test that _get_bedrock_llm creates BedrockChat instance with correct parameters."""
    with patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "AKIATEST123456",
        "AWS_SECRET_ACCESS_KEY": "test-secret-key",
        "AWS_REGION": "us-east-1"
    }):
        from chatforge.config import llm_config

        with patch.object(llm_config, "aws_access_key_id", "AKIATEST123456"), \
             patch.object(llm_config, "aws_secret_access_key", "test-secret-key"), \
             patch.object(llm_config, "aws_region", "us-east-1"):

            llm = _get_bedrock_llm(
                model_name="anthropic.claude-3-sonnet-20240229-v1:0",
                streaming=False,
                temperature=0.0
            )

            # Verify it's a BedrockChat instance
            from langchain_community.chat_models import BedrockChat
            assert isinstance(llm, BedrockChat)

            # Verify parameters
            assert llm.model_id == "anthropic.claude-3-sonnet-20240229-v1:0"


@pytest.mark.unit
def test_bedrock_llm_with_different_models():
    """Test Bedrock instantiation with different Claude models on Bedrock."""
    models = [
        "anthropic.claude-3-sonnet-20240229-v1:0",
        "anthropic.claude-3-haiku-20240307-v1:0",
        "anthropic.claude-v2",
        "anthropic.claude-instant-v1",
    ]

    with patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "AKIATEST123456",
        "AWS_SECRET_ACCESS_KEY": "test-secret-key"
    }):
        from chatforge.config import llm_config

        for model in models:
            with patch.object(llm_config, "aws_access_key_id", "AKIATEST123456"), \
                 patch.object(llm_config, "aws_secret_access_key", "test-secret-key"), \
                 patch.object(llm_config, "aws_region", "us-east-1"):

                llm = _get_bedrock_llm(
                    model_name=model,
                    streaming=False,
                    temperature=0.0
                )

                from langchain_community.chat_models import BedrockChat
                assert isinstance(llm, BedrockChat)
                assert llm.model_id == model


@pytest.mark.unit
def test_bedrock_streaming_enabled():
    """Test Bedrock instantiation with streaming enabled."""
    with patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "AKIATEST123456",
        "AWS_SECRET_ACCESS_KEY": "test-secret-key"
    }):
        from chatforge.config import llm_config

        with patch.object(llm_config, "aws_access_key_id", "AKIATEST123456"), \
             patch.object(llm_config, "aws_secret_access_key", "test-secret-key"), \
             patch.object(llm_config, "aws_region", "us-east-1"):

            llm = _get_bedrock_llm(
                model_name="anthropic.claude-3-sonnet-20240229-v1:0",
                streaming=True,
                temperature=0.0
            )

            from langchain_community.chat_models import BedrockChat
            assert isinstance(llm, BedrockChat)
            # streaming parameter is passed to constructor


@pytest.mark.unit
def test_bedrock_custom_temperature():
    """Test Bedrock with various temperature values."""
    test_temps = [0.0, 0.5, 0.7, 1.0]

    with patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "AKIATEST123456",
        "AWS_SECRET_ACCESS_KEY": "test-secret-key"
    }):
        from chatforge.config import llm_config

        for temp in test_temps:
            with patch.object(llm_config, "aws_access_key_id", "AKIATEST123456"), \
                 patch.object(llm_config, "aws_secret_access_key", "test-secret-key"), \
                 patch.object(llm_config, "aws_region", "us-east-1"):

                llm = _get_bedrock_llm(
                    model_name="anthropic.claude-3-sonnet-20240229-v1:0",
                    streaming=False,
                    temperature=temp
                )

                from langchain_community.chat_models import BedrockChat
                assert isinstance(llm, BedrockChat)
                # Temperature is in model_kwargs
                assert llm.model_kwargs["temperature"] == temp


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

@pytest.mark.unit
def test_bedrock_missing_access_key_raises_error():
    """Test that missing AWS access key raises ValueError."""
    from chatforge.config import llm_config

    with patch.object(llm_config, "aws_access_key_id", None), \
         patch.object(llm_config, "aws_secret_access_key", "test-secret"):

        with pytest.raises(ValueError, match="AWS credentials not configured"):
            _get_bedrock_llm(
                model_name="anthropic.claude-v2",
                streaming=False,
                temperature=0.0
            )


@pytest.mark.unit
def test_bedrock_missing_secret_key_raises_error():
    """Test that missing AWS secret key raises ValueError."""
    from chatforge.config import llm_config

    with patch.object(llm_config, "aws_access_key_id", "AKIATEST123456"), \
         patch.object(llm_config, "aws_secret_access_key", None):

        with pytest.raises(ValueError, match="AWS credentials not configured"):
            _get_bedrock_llm(
                model_name="anthropic.claude-v2",
                streaming=False,
                temperature=0.0
            )


@pytest.mark.unit
def test_bedrock_missing_both_credentials_raises_error():
    """Test that missing both AWS credentials raises ValueError."""
    from chatforge.config import llm_config

    with patch.object(llm_config, "aws_access_key_id", None), \
         patch.object(llm_config, "aws_secret_access_key", None):

        with pytest.raises(ValueError, match="AWS credentials not configured"):
            _get_bedrock_llm(
                model_name="anthropic.claude-v2",
                streaming=False,
                temperature=0.0
            )


# =============================================================================
# LAZY IMPORT TESTS
# =============================================================================

@pytest.mark.unit
def test_bedrock_import_error_handling():
    """Test that ImportError is raised with helpful message if langchain-community not installed."""
    from chatforge.config import llm_config

    with patch.object(llm_config, "aws_access_key_id", "AKIATEST123456"), \
         patch.object(llm_config, "aws_secret_access_key", "test-secret"):

        # Mock the import to fail
        with patch("builtins.__import__", side_effect=ImportError("No module named 'langchain_community'")):
            with pytest.raises(ImportError, match="langchain-community and boto3 are required"):
                _get_bedrock_llm(
                    model_name="anthropic.claude-v2",
                    streaming=False,
                    temperature=0.0
                )


# =============================================================================
# REGION CONFIGURATION TESTS
# =============================================================================

@pytest.mark.unit
def test_bedrock_custom_region():
    """Test Bedrock with custom AWS region."""
    regions = ["us-east-1", "us-west-2", "eu-west-1"]

    with patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "AKIATEST123456",
        "AWS_SECRET_ACCESS_KEY": "test-secret-key"
    }):
        from chatforge.config import llm_config

        for region in regions:
            with patch.object(llm_config, "aws_access_key_id", "AKIATEST123456"), \
                 patch.object(llm_config, "aws_secret_access_key", "test-secret-key"), \
                 patch.object(llm_config, "aws_region", region):

                llm = _get_bedrock_llm(
                    model_name="anthropic.claude-3-sonnet-20240229-v1:0",
                    streaming=False,
                    temperature=0.0
                )

                from langchain_community.chat_models import BedrockChat
                assert isinstance(llm, BedrockChat)
                assert llm.region_name == region


# =============================================================================
# VISION MODEL TESTS
# =============================================================================

@pytest.mark.unit
def test_bedrock_vision_model_claude3_sonnet():
    """Test Bedrock with vision-capable Claude 3 Sonnet model."""
    with patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "AKIATEST123456",
        "AWS_SECRET_ACCESS_KEY": "test-secret-key"
    }):
        from chatforge.config import llm_config

        with patch.object(llm_config, "aws_access_key_id", "AKIATEST123456"), \
             patch.object(llm_config, "aws_secret_access_key", "test-secret-key"), \
             patch.object(llm_config, "aws_region", "us-east-1"):

            llm = _get_bedrock_llm(
                model_name="anthropic.claude-3-sonnet-20240229-v1:0",
                streaming=False,
                temperature=0.0
            )

            from langchain_community.chat_models import BedrockChat
            assert isinstance(llm, BedrockChat)
            assert llm.model_id == "anthropic.claude-3-sonnet-20240229-v1:0"


# =============================================================================
# MODEL KWARGS TESTS
# =============================================================================

@pytest.mark.unit
def test_bedrock_model_kwargs_contains_temperature():
    """Test that temperature is properly set in model_kwargs."""
    with patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "AKIATEST123456",
        "AWS_SECRET_ACCESS_KEY": "test-secret-key"
    }):
        from chatforge.config import llm_config

        with patch.object(llm_config, "aws_access_key_id", "AKIATEST123456"), \
             patch.object(llm_config, "aws_secret_access_key", "test-secret-key"), \
             patch.object(llm_config, "aws_region", "us-east-1"):

            llm = _get_bedrock_llm(
                model_name="anthropic.claude-v2",
                streaming=False,
                temperature=0.7
            )

            from langchain_community.chat_models import BedrockChat
            assert isinstance(llm, BedrockChat)
            assert "temperature" in llm.model_kwargs
            assert llm.model_kwargs["temperature"] == 0.7
