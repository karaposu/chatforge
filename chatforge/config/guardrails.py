"""
Guardrails configuration for agent security and safety.

Provides toggles for content moderation, prompt injection detection,
PII protection, and output safety filtering.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GuardrailsSettings(BaseSettings):
    """
    Guardrails configuration for agent security and safety.

    Environment Variables:
        # OpenAI Moderation
        GUARDRAILS_MODERATION_ENABLED: Enable OpenAI Moderation (default: true)
        GUARDRAILS_MODERATION_MODEL: Moderation model (default: omni-moderation-latest)
        GUARDRAILS_MODERATION_CHECK_INPUT: Check user input (default: true)
        GUARDRAILS_MODERATION_CHECK_OUTPUT: Check agent output (default: true)
        GUARDRAILS_MODERATION_CHECK_TOOL_RESULTS: Check tool results (default: false)
        GUARDRAILS_MODERATION_EXIT_BEHAVIOR: end, error, or replace (default: end)
        GUARDRAILS_MODERATION_VIOLATION_MESSAGE: Custom violation message

        # Prompt Injection Guard
        GUARDRAILS_PROMPT_INJECTION_ENABLED: Enable prompt injection detection (default: true)
        GUARDRAILS_PROMPT_INJECTION_MODEL: Model for detection (default: gpt-4o-mini)

        # PII Detection
        GUARDRAILS_PII_ENABLED: Enable PII detection/redaction (default: true)

        # Content Filter (output safety)
        GUARDRAILS_CONTENT_FILTER_ENABLED: Enable safety filter (default: true)
        GUARDRAILS_SAFETY_MODEL: Model for safety evaluation (default: gpt-4o-mini)
    """

    # ==========================================================================
    # OpenAI Moderation
    # ==========================================================================
    moderation_enabled: bool = Field(
        default=True,
        description="Enable OpenAI Moderation middleware",
    )
    moderation_model: str = Field(
        default="omni-moderation-latest",
        description="OpenAI moderation model: omni-moderation-latest, text-moderation-latest, etc.",
    )
    moderation_check_input: bool = Field(
        default=True,
        description="Check user input messages before model call",
    )
    moderation_check_output: bool = Field(
        default=True,
        description="Check model output messages after model call",
    )
    moderation_check_tool_results: bool = Field(
        default=False,
        description="Check tool result messages before model call",
    )
    moderation_exit_behavior: str = Field(
        default="end",
        description="How to handle violations: 'end' (stop), 'error' (raise), 'replace' (continue)",
    )
    moderation_violation_message: str = Field(
        default=(
            "I cannot process this request as it was flagged for: {categories}. "
            "Please rephrase your request."
        ),
        description="Custom violation message. Supports: {categories}, {category_scores}, {original_content}",
    )

    # ==========================================================================
    # Prompt Injection Guard
    # ==========================================================================
    prompt_injection_enabled: bool = Field(
        default=True,
        description="Enable LLM-based prompt injection detection",
    )
    prompt_injection_model: str = Field(
        default="gpt-4o-mini",
        description="Model for prompt injection detection (should be fast and cost-effective)",
    )

    # ==========================================================================
    # PII Detection
    # ==========================================================================
    pii_enabled: bool = Field(
        default=True,
        description="Enable PII detection and protection (email, credit cards, phone, IP, API keys)",
    )

    # ==========================================================================
    # Content Filter (output safety)
    # ==========================================================================
    content_filter_enabled: bool = Field(
        default=True,
        description="Enable model-based content/safety filtering for agent responses",
    )
    safety_model: str = Field(
        default="gpt-4o-mini",
        description="Model to use for safety evaluation (should be fast and cost-effective)",
    )

    model_config = SettingsConfigDict(
        env_prefix="GUARDRAILS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_any_enabled(self) -> bool:
        """Check if any guardrail is enabled."""
        return (
            self.pii_enabled
            or self.content_filter_enabled
            or self.moderation_enabled
            or self.prompt_injection_enabled
        )

    @property
    def is_input_protection_enabled(self) -> bool:
        """Check if any input protection guardrail is enabled."""
        return self.pii_enabled or self.moderation_enabled or self.prompt_injection_enabled


# Module-level singleton
guardrails_config = GuardrailsSettings()
