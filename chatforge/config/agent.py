"""
Agent behavior configuration.

Controls iteration limits and conversation timeouts.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    """
    Agent behavior configuration.

    Environment Variables:
        AGENT_MAX_ITERATIONS: Maximum tool iterations per request (default: 10)
        AGENT_CONVERSATION_TIMEOUT_MINUTES: Conversation TTL in minutes (default: 30)
    """

    max_iterations: int = Field(
        default=10,
        description="Maximum agent iterations",
        ge=1,
        le=50,
    )
    conversation_timeout_minutes: int = Field(
        default=30,
        description="Conversation timeout in minutes",
        ge=5,
        le=120,
    )

    model_config = SettingsConfigDict(
        env_prefix="AGENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Module-level singleton
agent_config = AgentSettings()
