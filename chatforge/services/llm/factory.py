"""
LLM Factory for multi-provider support using LangChain.

This module provides a factory pattern to instantiate different LLM providers
(OpenAI, Anthropic, AWS Bedrock) with a consistent interface using LangChain.
"""

from langchain_core.language_models import BaseChatModel

from chatforge.config import llm_config


def get_llm(
    provider: str | None = None,
    model_name: str | None = None,
    streaming: bool = False,
    temperature: float | None = None,
) -> BaseChatModel:
    """
    Get LLM instance based on provider configuration.

    This factory function creates the appropriate LLM instance based on the
    configured provider (OpenAI, Anthropic, or Bedrock) using LangChain's
    unified interface.

    Args:
        provider: LLM provider ('openai', 'anthropic', 'bedrock').
                 If None, uses llm_config.provider
        model_name: Model name to use. If None, uses llm_config.model_name
        streaming: Enable streaming responses (default: False)
        temperature: Model temperature for response randomness (0.0-1.0).
                    If None, uses llm_config.temperature

    Returns:
        BaseChatModel: LangChain chat model instance

    Raises:
        ValueError: If provider is not supported or credentials are missing

    Example:
        >>> llm = get_llm(provider="openai", streaming=True)
        >>> response = llm.invoke("Hello, how are you?")
    """
    provider = provider or llm_config.provider
    model_name = model_name or llm_config.model_name
    temperature = temperature if temperature is not None else llm_config.temperature

    if provider == "openai":
        return _get_openai_llm(model_name, streaming, temperature)
    if provider == "anthropic":
        return _get_anthropic_llm(model_name, streaming, temperature)
    if provider == "bedrock":
        return _get_bedrock_llm(model_name, streaming, temperature)
    raise ValueError(f"Unsupported LLM provider: {provider}. Supported: openai, anthropic, bedrock")


def get_streaming_llm(
    provider: str | None = None,
    model_name: str | None = None,
    temperature: float | None = None,
) -> BaseChatModel:
    """
    Get streaming-enabled LLM instance.

    Convenience function that always returns a streaming-enabled LLM.

    Args:
        provider: LLM provider. If None, uses llm_config.provider
        model_name: Model name. If None, uses llm_config.model_name
        temperature: Model temperature (0.0-1.0). If None, uses llm_config.temperature

    Returns:
        BaseChatModel: Streaming-enabled LLM instance

    Example:
        >>> llm = get_streaming_llm()
        >>> for chunk in llm.stream("Tell me a story"):
        ...     print(chunk.content, end="", flush=True)
    """
    return get_llm(
        provider=provider,
        model_name=model_name,
        streaming=True,
        temperature=temperature,
    )


# Default vision-capable model names by provider
DEFAULT_VISION_MODELS = {
    "openai": "gpt-4o",
    "anthropic": "claude-3-5-sonnet-latest",
    "bedrock": "anthropic.claude-3-sonnet-20240229-v1:0",
}


def get_vision_llm(
    provider: str | None = None,
    model_name: str | None = None,
    temperature: float | None = None,
) -> BaseChatModel:
    """
    Get a vision-capable LLM instance for image analysis.

    This factory function returns an LLM that supports multimodal input,
    specifically images encoded as base64 data URIs in HumanMessage content.

    Model selection priority:
    1. Explicit model_name parameter
    2. LLM_VISION_MODEL_NAME environment variable
    3. Default vision model for the provider

    Args:
        provider: LLM provider ('openai', 'anthropic', 'bedrock').
                 If None, uses llm_config.provider
        model_name: Explicit model name override. If None, uses env var or default.
        temperature: Model temperature. If None, uses llm_config.vision_temperature

    Returns:
        BaseChatModel: Vision-capable LangChain chat model

    Raises:
        ValueError: If provider doesn't support vision or credentials missing
    """
    provider = provider or llm_config.provider

    # Determine model name with priority: param > env var > default
    if model_name is None:
        model_name = llm_config.vision_model_name

    if model_name is None:
        if provider not in DEFAULT_VISION_MODELS:
            raise ValueError(
                f"Provider '{provider}' does not have a configured vision model. "
                f"Supported: {list(DEFAULT_VISION_MODELS.keys())}. "
                f"Or set LLM_VISION_MODEL_NAME environment variable."
            )
        model_name = DEFAULT_VISION_MODELS[provider]

    # Use configured temperature or default
    if temperature is None:
        temperature = llm_config.vision_temperature

    return get_llm(
        provider=provider,
        model_name=model_name,
        streaming=False,
        temperature=temperature,
    )


def supports_vision(provider: str | None = None) -> bool:
    """
    Check if a provider supports vision/image analysis.

    Args:
        provider: LLM provider to check. If None, uses configured provider.

    Returns:
        bool: True if provider supports vision capabilities
    """
    provider = provider or llm_config.provider
    return provider in DEFAULT_VISION_MODELS


def _get_openai_llm(model_name: str, streaming: bool, temperature: float):
    """Create OpenAI LLM instance."""
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as e:
        raise ImportError(
            "langchain-openai is required for OpenAI provider. "
            "Install with: pip install chatforge[openai]"
        ) from e

    if not llm_config.openai_api_key:
        raise ValueError(
            "OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
        )

    return ChatOpenAI(
        model=model_name,
        api_key=llm_config.openai_api_key,
        streaming=streaming,
        temperature=temperature,
        request_timeout=60,
        max_retries=3,
    )


def _get_anthropic_llm(model_name: str, streaming: bool, temperature: float):
    """Create Anthropic LLM instance."""
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError as e:
        raise ImportError(
            "langchain-anthropic is required for Anthropic provider. "
            "Install with: pip install chatforge[anthropic]"
        ) from e

    if not llm_config.anthropic_api_key:
        raise ValueError(
            "Anthropic API key not configured. Please set ANTHROPIC_API_KEY environment variable."
        )

    return ChatAnthropic(
        model=model_name,
        anthropic_api_key=llm_config.anthropic_api_key,
        streaming=streaming,
        temperature=temperature,
        timeout=60,
        max_retries=3,
    )


def _get_bedrock_llm(model_name: str, streaming: bool, temperature: float):
    """Create AWS Bedrock LLM instance."""
    try:
        from langchain_community.chat_models import BedrockChat
    except ImportError as e:
        raise ImportError(
            "langchain-community and boto3 are required for Bedrock provider. "
            "Install with: pip install chatforge[bedrock]"
        ) from e

    if not llm_config.aws_access_key_id or not llm_config.aws_secret_access_key:
        raise ValueError(
            "AWS credentials not configured. "
            "Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY."
        )

    return BedrockChat(
        model_id=model_name,
        streaming=streaming,
        model_kwargs={"temperature": temperature},
        region_name=llm_config.aws_region,
        credentials_profile_name=None,
    )
