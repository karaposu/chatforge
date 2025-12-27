"""
Constants for Middleware Module.

This module defines:
- Regular expressions for PII detection
- Default configuration values
"""

from __future__ import annotations


# =============================================================================
# PII DETECTION PATTERNS
# =============================================================================

# Email pattern
EMAIL_PATTERN = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

# Credit card patterns (major card types)
# Supports formats: 4532123456789010, 4532-1234-5678-9010, 4532 1234 5678 9010
_SEP = r"[-\s]?"  # Optional separator (dash or space)
CREDIT_CARD_PATTERN = (
    r"(?:"
    # Visa: 13 or 16 digits starting with 4
    rf"4[0-9]{{3}}{_SEP}[0-9]{{4}}{_SEP}[0-9]{{4}}{_SEP}[0-9]{{4}}|"
    rf"4[0-9]{{3}}{_SEP}[0-9]{{4}}{_SEP}[0-9]{{4}}{_SEP}[0-9]|"
    # MasterCard: 16 digits starting with 51-55
    rf"5[1-5][0-9]{{2}}{_SEP}[0-9]{{4}}{_SEP}[0-9]{{4}}{_SEP}[0-9]{{4}}|"
    # American Express: 15 digits starting with 34 or 37
    rf"3[47][0-9]{{2}}{_SEP}[0-9]{{6}}{_SEP}[0-9]{{5}}|"
    # Discover: 16 digits starting with 6011 or 65
    rf"6011{_SEP}[0-9]{{4}}{_SEP}[0-9]{{4}}{_SEP}[0-9]{{4}}|"
    rf"65[0-9]{{2}}{_SEP}[0-9]{{4}}{_SEP}[0-9]{{4}}{_SEP}[0-9]{{4}}"
    r")"
)

# Phone number patterns (various formats)
PHONE_PATTERN = (
    r"(?:\+?1[-.\s]?)?"  # Optional country code
    r"(?:\(?\d{3}\)?[-.\s]?)"  # Area code
    r"\d{3}[-.\s]?\d{4}"  # Main number
)

# IP address pattern (IPv4)
IP_PATTERN = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"

# Social Security Number pattern (US)
SSN_PATTERN = r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b"

# API key patterns (common formats)
API_KEY_PATTERNS = {
    "openai": r"sk-[a-zA-Z0-9]{32,}",
    "anthropic": r"sk-ant-[a-zA-Z0-9\-]{32,}",
    "slack_bot": r"xoxb-[a-zA-Z0-9\-]+",
    "slack_app": r"xapp-[a-zA-Z0-9\-]+",
    "generic_api_key": r"(?:api[_-]?key|apikey|api_secret)[=:\s]+['\"]?[a-zA-Z0-9\-_]{20,}['\"]?",
}

# Combined API key pattern for blocking
COMBINED_API_KEY_PATTERN = "|".join(f"(?:{p})" for p in API_KEY_PATTERNS.values())

# =============================================================================
# DEFAULT CONFIGURATION
# =============================================================================

# Default model for safety evaluation (fast and cost-effective)
DEFAULT_SAFETY_MODEL = "gpt-4o-mini"

# PII types to protect by default
DEFAULT_PII_TYPES = [
    "email",
    "credit_card",
    "ip",
]

# PII strategies
PII_STRATEGY_REDACT = "redact"
PII_STRATEGY_MASK = "mask"
PII_STRATEGY_HASH = "hash"
PII_STRATEGY_BLOCK = "block"
