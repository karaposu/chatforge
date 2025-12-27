"""
Content Filter / Safety Middleware.

This module implements safety guardrails that evaluate agent responses
for safety and appropriateness.

The evaluation prompt is templated to allow application-specific customization
of context, safety criteria, and forbidden content.

Usage:
    from chatforge.middleware import SafetyGuardrail

    # Generic usage
    guardrail = SafetyGuardrail()

    # Check a response
    result = await guardrail.check_response("Some agent response...")
    if not result.is_safe:
        response = result.fallback_message

    # With custom context
    guardrail = SafetyGuardrail(
        context="IT support assistant",
        safety_criteria=[
            "Professional and helpful",
            "Focused on technical support",
        ],
        forbidden_content=[
            "Advice on bypassing security",
            "Personal opinions on non-IT matters",
        ],
    )
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage

from .constants import DEFAULT_SAFETY_MODEL


if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


logger = logging.getLogger(__name__)


# Template-based safety evaluation prompt
SAFETY_EVALUATION_TEMPLATE = """You are evaluating an AI assistant's response for safety.

## Context
This assistant is a {context}.

## Safety Criteria
The response should be:
{safety_criteria}

## Forbidden Content
The response should NOT contain:
{forbidden_content}

## Response to Evaluate
{response}

## Your Evaluation
Reply with ONLY one word:
- SAFE if the response meets all criteria
- UNSAFE if the response violates any criteria"""

# Default fallback for unsafe responses
DEFAULT_UNSAFE_FALLBACK = (
    "I apologize, but I cannot provide that response. "
    "Please let me know how I can assist you appropriately."
)


@dataclass
class SafetyCheckResult:
    """Result of a safety check."""

    is_safe: bool
    original_response: str
    fallback_message: str | None = None
    reason: str | None = None

    @property
    def response(self) -> str:
        """Get the response to use (original if safe, fallback if not)."""
        return self.original_response if self.is_safe else (self.fallback_message or "")


@dataclass
class ContentCheckResult:
    """Result of a content filter check."""

    is_allowed: bool
    original_content: str
    blocked_keyword: str | None = None
    rejection_message: str | None = None


class SafetyGuardrail:
    """
    Model-based guardrail that evaluates response safety.

    This middleware uses a lightweight LLM to check if the agent's response
    is safe and appropriate. Unsafe responses are replaced with a fallback.

    The evaluation prompt is templated to allow application-specific
    customization of context, safety criteria, and forbidden content.

    Attributes:
        context: Description of what the assistant does.
        safety_criteria: List of criteria the response should meet.
        forbidden_content: List of content types to forbid.
        fallback_message: Message to use for unsafe responses.

    Example:
        # Generic assistant
        guardrail = SafetyGuardrail()

        # Check response
        result = await guardrail.check_response("Some response text")
        if not result.is_safe:
            print(f"Unsafe: {result.reason}")

        # Custom context
        guardrail = SafetyGuardrail(
            context="enterprise IT support assistant",
            safety_criteria=[
                "Professional and helpful for IT issues",
                "Accurate technical information",
            ],
            forbidden_content=[
                "Advice on bypassing security measures",
                "Personal opinions on non-IT matters",
            ],
        )
    """

    def __init__(
        self,
        context: str = "general assistant",
        safety_criteria: list[str] | None = None,
        forbidden_content: list[str] | None = None,
        fallback_message: str | None = None,
        safety_model: BaseChatModel | None = None,
    ):
        """
        Initialize the safety guardrail.

        Args:
            context: Description of assistant purpose.
            safety_criteria: List of criteria for safe responses.
            forbidden_content: List of forbidden content types.
            fallback_message: Message to use for unsafe responses.
            safety_model: Pre-configured LLM for evaluation.
        """
        self._safety_model = safety_model
        self._context = context
        self._safety_criteria = safety_criteria or [
            "Helpful and accurate",
            "Professional tone",
            "No harmful content",
        ]
        self._forbidden_content = forbidden_content or [
            "Personal attacks or harassment",
            "Dangerous instructions",
            "Illegal activities",
        ]
        self._fallback_message = fallback_message or DEFAULT_UNSAFE_FALLBACK

        # Build the evaluation prompt template
        self._prompt_template = SAFETY_EVALUATION_TEMPLATE.format(
            context=self._context,
            safety_criteria="\n".join(f"- {c}" for c in self._safety_criteria),
            forbidden_content="\n".join(f"- {c}" for c in self._forbidden_content),
            response="{response}",  # Keep response placeholder
        )

        logger.debug(f"SafetyGuardrail initialized for context: {self._context}")

    def set_model(self, model: BaseChatModel) -> None:
        """Set the safety evaluation model."""
        self._safety_model = model

    async def check_response(self, response: str) -> SafetyCheckResult:
        """
        Check if a response is safe.

        Args:
            response: The agent response to evaluate.

        Returns:
            SafetyCheckResult with is_safe flag and details.
        """
        if not response or not response.strip():
            return SafetyCheckResult(
                is_safe=True,
                original_response=response,
            )

        if self._safety_model is None:
            logger.warning("SafetyGuardrail: No model configured, passing through")
            return SafetyCheckResult(
                is_safe=True,
                original_response=response,
            )

        try:
            prompt = self._prompt_template.format(response=response)
            result = await self._safety_model.ainvoke([HumanMessage(content=prompt)])
            classification = str(result.content).strip().upper()

            logger.debug(f"Safety evaluation result: {classification}")

            if "UNSAFE" in classification:
                return SafetyCheckResult(
                    is_safe=False,
                    original_response=response,
                    fallback_message=self._fallback_message,
                    reason="Response classified as unsafe",
                )

            if "SAFE" in classification:
                return SafetyCheckResult(
                    is_safe=True,
                    original_response=response,
                )

            # Ambiguous response - fail open
            logger.warning(f"Ambiguous safety classification: {classification}")
            return SafetyCheckResult(
                is_safe=True,
                original_response=response,
            )

        except Exception as e:
            logger.error(f"SafetyGuardrail evaluation error: {e}", exc_info=True)
            # Fail open on errors
            return SafetyCheckResult(
                is_safe=True,
                original_response=response,
                reason=f"Evaluation error: {e}",
            )

    def check_response_sync(self, response: str) -> SafetyCheckResult:
        """
        Synchronous version of check_response.

        Args:
            response: The agent response to evaluate.

        Returns:
            SafetyCheckResult with is_safe flag and details.
        """
        from chatforge.utils import run_async

        return run_async(self.check_response(response))


class ContentFilter:
    """
    Deterministic content filter using keyword matching.

    A faster, simpler alternative to SafetyGuardrail that blocks
    requests containing specific banned keywords.

    Attributes:
        banned_keywords: List of keywords to block (case-insensitive).
        rejection_message: Message to return when content is blocked.

    Example:
        filter = ContentFilter(
            banned_keywords=["hack", "exploit", "malware"],
            rejection_message="I cannot help with that topic.",
        )

        result = filter.check_content("How do I hack a password?")
        if not result.is_allowed:
            print(f"Blocked: {result.blocked_keyword}")
    """

    def __init__(
        self,
        banned_keywords: list[str] | None = None,
        rejection_message: str | None = None,
    ):
        """
        Initialize the content filter.

        Args:
            banned_keywords: List of keywords to block.
            rejection_message: Custom rejection message.
        """
        default_keywords = [
            "hack",
            "exploit",
            "malware",
            "ransomware",
            "phishing",
            "bypass security",
            "crack password",
            "ddos",
            "brute force",
            "sql injection",
        ]
        self.banned_keywords = [kw.lower() for kw in (banned_keywords or default_keywords)]
        self._rejection_message = rejection_message or (
            "I'm sorry, but I cannot process requests related to that topic. "
            "Please rephrase your request."
        )
        logger.debug(f"ContentFilter initialized with {len(self.banned_keywords)} keywords")

    def check_content(self, content: str) -> ContentCheckResult:
        """
        Check if content contains banned keywords.

        Args:
            content: Text content to check.

        Returns:
            ContentCheckResult with is_allowed flag and details.
        """
        if not content:
            return ContentCheckResult(
                is_allowed=True,
                original_content=content,
            )

        content_lower = content.lower()

        for keyword in self.banned_keywords:
            if keyword in content_lower:
                logger.warning(f"ContentFilter: Blocked content containing '{keyword}'")
                return ContentCheckResult(
                    is_allowed=False,
                    original_content=content,
                    blocked_keyword=keyword,
                    rejection_message=self._rejection_message,
                )

        return ContentCheckResult(
            is_allowed=True,
            original_content=content,
        )

    def add_keyword(self, keyword: str) -> None:
        """Add a keyword to the banned list."""
        kw_lower = keyword.lower()
        if kw_lower not in self.banned_keywords:
            self.banned_keywords.append(kw_lower)

    def remove_keyword(self, keyword: str) -> bool:
        """Remove a keyword from the banned list. Returns True if removed."""
        kw_lower = keyword.lower()
        if kw_lower in self.banned_keywords:
            self.banned_keywords.remove(kw_lower)
            return True
        return False
