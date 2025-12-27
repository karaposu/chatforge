"""
PII Detection Middleware.

This module provides PII (Personally Identifiable Information) detection
and redaction capabilities using regex patterns.

Supported PII Types:
- email: Email addresses
- credit_card: Credit card numbers
- phone: Phone numbers
- ip: IP addresses
- ssn: Social Security Numbers
- api_key: API keys (various providers)

Usage:
    from chatforge.middleware import PIIDetector

    detector = PIIDetector()
    result = detector.scan("Contact me at john@example.com")

    if result.has_pii:
        print(f"Found PII: {result.detected_types}")
        safe_text = result.redacted_text
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from .constants import (
    COMBINED_API_KEY_PATTERN,
    CREDIT_CARD_PATTERN,
    EMAIL_PATTERN,
    IP_PATTERN,
    PHONE_PATTERN,
    SSN_PATTERN,
)


logger = logging.getLogger(__name__)


class PIIStrategy(str, Enum):
    """Strategy for handling detected PII."""

    REDACT = "redact"  # Replace with [REDACTED]
    MASK = "mask"  # Show partial (e.g., ****1234)
    HASH = "hash"  # Replace with hash
    BLOCK = "block"  # Raise exception


@dataclass
class PIIMatch:
    """A single PII match."""

    pii_type: str
    value: str
    start: int
    end: int
    replacement: str | None = None


@dataclass
class PIIScanResult:
    """Result of a PII scan."""

    original_text: str
    matches: list[PIIMatch] = field(default_factory=list)
    redacted_text: str | None = None
    blocked: bool = False
    block_reason: str | None = None

    @property
    def has_pii(self) -> bool:
        """Check if any PII was detected."""
        return len(self.matches) > 0

    @property
    def detected_types(self) -> list[str]:
        """Get list of detected PII types."""
        return list(set(m.pii_type for m in self.matches))


@dataclass
class PIIRule:
    """Configuration for a PII detection rule."""

    pii_type: str
    pattern: str | re.Pattern
    strategy: PIIStrategy = PIIStrategy.REDACT
    replacement_text: str = "[REDACTED]"
    mask_chars: int = 4  # For MASK strategy, how many chars to show


class PIIDetector:
    """
    PII detection and redaction using regex patterns.

    This detector scans text for various types of PII and can
    redact, mask, hash, or block content containing sensitive data.

    Example:
        detector = PIIDetector()

        # Scan text
        result = detector.scan("My email is john@example.com")
        if result.has_pii:
            print(f"Found: {result.detected_types}")
            print(f"Safe: {result.redacted_text}")

        # Add custom pattern
        detector.add_rule(PIIRule(
            pii_type="employee_id",
            pattern=r"EMP-\\d{6}",
            strategy=PIIStrategy.REDACT,
        ))
    """

    def __init__(self, rules: list[PIIRule] | None = None):
        """
        Initialize the PII detector.

        Args:
            rules: Optional list of custom rules. If None, uses default rules.
        """
        self._rules: list[PIIRule] = []

        if rules is not None:
            for rule in rules:
                self.add_rule(rule)
        else:
            self._add_default_rules()

        logger.debug(f"PIIDetector initialized with {len(self._rules)} rules")

    def _add_default_rules(self) -> None:
        """Add default PII detection rules."""
        default_rules = [
            PIIRule(
                pii_type="email",
                pattern=EMAIL_PATTERN,
                strategy=PIIStrategy.REDACT,
                replacement_text="[EMAIL REDACTED]",
            ),
            PIIRule(
                pii_type="credit_card",
                pattern=CREDIT_CARD_PATTERN,
                strategy=PIIStrategy.MASK,
                mask_chars=4,
            ),
            PIIRule(
                pii_type="phone",
                pattern=PHONE_PATTERN,
                strategy=PIIStrategy.REDACT,
                replacement_text="[PHONE REDACTED]",
            ),
            PIIRule(
                pii_type="ip",
                pattern=IP_PATTERN,
                strategy=PIIStrategy.REDACT,
                replacement_text="[IP REDACTED]",
            ),
            PIIRule(
                pii_type="ssn",
                pattern=SSN_PATTERN,
                strategy=PIIStrategy.REDACT,
                replacement_text="[SSN REDACTED]",
            ),
            PIIRule(
                pii_type="api_key",
                pattern=COMBINED_API_KEY_PATTERN,
                strategy=PIIStrategy.BLOCK,
            ),
        ]

        for rule in default_rules:
            self.add_rule(rule)

    def add_rule(self, rule: PIIRule) -> None:
        """Add a PII detection rule."""
        # Compile pattern if string
        if isinstance(rule.pattern, str):
            rule.pattern = re.compile(rule.pattern, re.IGNORECASE)
        self._rules.append(rule)

    def remove_rule(self, pii_type: str) -> bool:
        """Remove a rule by PII type. Returns True if removed."""
        original_len = len(self._rules)
        self._rules = [r for r in self._rules if r.pii_type != pii_type]
        return len(self._rules) < original_len

    def scan(self, text: str) -> PIIScanResult:
        """
        Scan text for PII.

        Args:
            text: Text to scan.

        Returns:
            PIIScanResult with matches and optionally redacted text.
        """
        if not text:
            return PIIScanResult(original_text=text, redacted_text=text)

        matches: list[PIIMatch] = []
        blocked = False
        block_reason = None

        for rule in self._rules:
            pattern = rule.pattern if isinstance(rule.pattern, re.Pattern) else re.compile(rule.pattern)

            for match in pattern.finditer(text):
                value = match.group()

                # Determine replacement
                if rule.strategy == PIIStrategy.BLOCK:
                    blocked = True
                    block_reason = f"Blocked PII type: {rule.pii_type}"
                    replacement = rule.replacement_text
                elif rule.strategy == PIIStrategy.MASK:
                    # Show last N characters
                    if len(value) > rule.mask_chars:
                        replacement = "*" * (len(value) - rule.mask_chars) + value[-rule.mask_chars:]
                    else:
                        replacement = "*" * len(value)
                elif rule.strategy == PIIStrategy.HASH:
                    replacement = f"[{hashlib.sha256(value.encode()).hexdigest()[:8]}]"
                else:  # REDACT
                    replacement = rule.replacement_text

                matches.append(
                    PIIMatch(
                        pii_type=rule.pii_type,
                        value=value,
                        start=match.start(),
                        end=match.end(),
                        replacement=replacement,
                    )
                )

        # Build redacted text (replace in reverse order to preserve positions)
        redacted_text = text
        for match in sorted(matches, key=lambda m: m.start, reverse=True):
            redacted_text = (
                redacted_text[: match.start]
                + (match.replacement or "[REDACTED]")
                + redacted_text[match.end :]
            )

        return PIIScanResult(
            original_text=text,
            matches=matches,
            redacted_text=redacted_text,
            blocked=blocked,
            block_reason=block_reason,
        )

    def redact(self, text: str) -> str:
        """
        Convenience method to scan and return redacted text.

        Args:
            text: Text to redact.

        Returns:
            Redacted text.

        Raises:
            ValueError: If blocked PII is detected.
        """
        result = self.scan(text)
        if result.blocked:
            raise ValueError(result.block_reason)
        return result.redacted_text or text

    def contains_pii(self, text: str) -> bool:
        """Check if text contains any PII."""
        return self.scan(text).has_pii


def get_default_pii_detector() -> PIIDetector:
    """Get a PII detector with default rules."""
    return PIIDetector()


def create_custom_pii_detector(
    pii_types: list[str] | None = None,
    custom_patterns: dict[str, str] | None = None,
) -> PIIDetector:
    """
    Create a customized PII detector.

    Args:
        pii_types: List of default PII types to include.
                   Options: email, credit_card, phone, ip, ssn, api_key
        custom_patterns: Dict of custom patterns {name: regex_pattern}

    Returns:
        Configured PIIDetector.

    Example:
        detector = create_custom_pii_detector(
            pii_types=["email", "phone"],
            custom_patterns={
                "employee_id": r"EMP-\\d{6}",
            }
        )
    """
    detector = PIIDetector(rules=[])

    # Add selected default rules
    if pii_types:
        default_patterns = {
            "email": (EMAIL_PATTERN, PIIStrategy.REDACT, "[EMAIL REDACTED]"),
            "credit_card": (CREDIT_CARD_PATTERN, PIIStrategy.MASK, None),
            "phone": (PHONE_PATTERN, PIIStrategy.REDACT, "[PHONE REDACTED]"),
            "ip": (IP_PATTERN, PIIStrategy.REDACT, "[IP REDACTED]"),
            "ssn": (SSN_PATTERN, PIIStrategy.REDACT, "[SSN REDACTED]"),
            "api_key": (COMBINED_API_KEY_PATTERN, PIIStrategy.BLOCK, None),
        }

        for pii_type in pii_types:
            if pii_type in default_patterns:
                pattern, strategy, replacement = default_patterns[pii_type]
                rule = PIIRule(
                    pii_type=pii_type,
                    pattern=pattern,
                    strategy=strategy,
                )
                if replacement:
                    rule.replacement_text = replacement
                detector.add_rule(rule)

    # Add custom patterns
    if custom_patterns:
        for name, pattern in custom_patterns.items():
            detector.add_rule(
                PIIRule(
                    pii_type=name,
                    pattern=pattern,
                    strategy=PIIStrategy.REDACT,
                    replacement_text=f"[{name.upper()} REDACTED]",
                )
            )

    return detector
