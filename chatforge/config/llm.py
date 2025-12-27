"""
LLM provider configuration.

Supports multiple providers: OpenAI, Anthropic, AWS Bedrock.
Provider selection is determined by LLM_PROVIDER environment variable.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """
    LLM provider configuration.

    Environment Variables:
        LLM_PROVIDER: Provider name (openai, anthropic, bedrock)
        LLM_MODEL_NAME: Model name (default: gpt-4o-mini)
        LLM_TEMPERATURE: Temperature for responses (0.0-1.0)
        LLM_VISION_MODEL_NAME: Model for image analysis
        LLM_VISION_TEMPERATURE: Temperature for vision model
        OPENAI_API_KEY: OpenAI API key
        ANTHROPIC_API_KEY: Anthropic API key
        AWS_ACCESS_KEY_ID: AWS access key for Bedrock
        AWS_SECRET_ACCESS_KEY: AWS secret key for Bedrock
        AWS_REGION: AWS region for Bedrock
    """

    # Provider selection
    provider: str = Field(
        default="openai",
        description="LLM provider: openai, anthropic, or bedrock",
    )
    model_name: str = Field(
        default="gpt-4o-mini",
        description="Model name for text generation (provider-specific)",
    )
    vision_model_name: str | None = Field(
        default=None,
        description="Model name for vision/image analysis. If not set, uses provider default.",
    )
    temperature: float = Field(
        default=0.0,
        description="Default temperature for LLM responses (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )
    vision_temperature: float = Field(
        default=0.0,
        description="Temperature for vision analysis (0.0-1.0). Lower is more deterministic.",
        ge=0.0,
        le=1.0,
    )

    # API keys use standard names (no LLM_ prefix for compatibility)
    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key",
        validation_alias="OPENAI_API_KEY",
    )
    anthropic_api_key: str | None = Field(
        default=None,
        description="Anthropic API key",
        validation_alias="ANTHROPIC_API_KEY",
    )
    aws_access_key_id: str | None = Field(
        default=None,
        description="AWS Access Key ID for Bedrock",
        validation_alias="AWS_ACCESS_KEY_ID",
    )
    aws_secret_access_key: str | None = Field(
        default=None,
        description="AWS Secret Access Key for Bedrock",
        validation_alias="AWS_SECRET_ACCESS_KEY",
    )
    aws_region: str = Field(
        default="us-east-1",
        description="AWS region",
        validation_alias="AWS_REGION",
    )

    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate LLM provider is supported."""
        allowed = ["openai", "anthropic", "bedrock"]
        if v.lower() not in allowed:
            raise ValueError(f"LLM_PROVIDER must be one of {allowed}, got '{v}'")
        return v.lower()

    def validate_credentials(self) -> None:
        """
        Validate that required credentials are present for the selected provider.

        Raises:
            ValueError: If required credentials are missing.
        """
        if self.provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        if self.provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        if self.provider == "bedrock" and not (
            self.aws_access_key_id and self.aws_secret_access_key
        ):
            raise ValueError("AWS credentials are required when LLM_PROVIDER=bedrock")


# Module-level singleton - created at import time
llm_config = LLMSettings()
