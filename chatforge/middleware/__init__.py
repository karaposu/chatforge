"""
Chatforge Middleware - Security and safety guardrails.

Provides middleware components for:
- PII detection and protection
- Prompt injection detection
- Safety/content filtering

All middleware uses simple, portable APIs that only depend on langchain-core.

Usage:
    from chatforge.middleware import (
        PIIDetector,
        PromptInjectionGuard,
        SafetyGuardrail,
        ContentFilter,
    )

    # PII Detection
    pii = PIIDetector()
    result = pii.scan("My email is john@example.com")
    if result.has_pii:
        safe_text = result.redacted_text

    # Prompt Injection Detection (requires LLM)
    guard = PromptInjectionGuard(detection_model=my_llm)
    result = await guard.check_message("Ignore previous instructions")
    if result.is_injection:
        print(f"Blocked: {result.reason}")

    # Safety Guardrail (requires LLM)
    safety = SafetyGuardrail(safety_model=my_llm)
    result = await safety.check_response("Some response...")
    if not result.is_safe:
        response = result.fallback_message

    # Content Filter (no LLM needed)
    filter = ContentFilter(banned_keywords=["hack", "exploit"])
    result = filter.check_content("How do I hack?")
    if not result.is_allowed:
        print(f"Blocked: {result.blocked_keyword}")
"""

from chatforge.middleware.injection import (
    InjectionCheckResult,
    PromptInjectionGuard,
)
from chatforge.middleware.pii import (
    PIIDetector,
    PIIMatch,
    PIIRule,
    PIIScanResult,
    PIIStrategy,
    create_custom_pii_detector,
    get_default_pii_detector,
)
from chatforge.middleware.safety import (
    ContentCheckResult,
    ContentFilter,
    SafetyCheckResult,
    SafetyGuardrail,
)

__all__ = [
    # PII
    "PIIDetector",
    "PIIRule",
    "PIIMatch",
    "PIIScanResult",
    "PIIStrategy",
    "get_default_pii_detector",
    "create_custom_pii_detector",
    # Injection
    "PromptInjectionGuard",
    "InjectionCheckResult",
    # Safety
    "SafetyGuardrail",
    "SafetyCheckResult",
    "ContentFilter",
    "ContentCheckResult",
]
