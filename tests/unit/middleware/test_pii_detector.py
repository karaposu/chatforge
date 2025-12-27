"""
Test PII Detection Middleware.

This module tests the PIIDetector component which uses pure regex patterns
to detect and redact personally identifiable information.

Test Strategy:
- Test each PII type detection (email, credit card, phone, SSN, IP, API keys)
- Test all redaction strategies (REDACT, MASK, HASH, BLOCK)
- Test custom rules and patterns
- Test edge cases and boundary conditions
- Test helper functions

Note: PIIDetector has NO dependencies (pure regex), so all tests are fast.
"""

import hashlib
import re

import pytest

from chatforge.middleware import (
    PIIDetector,
    PIIMatch,
    PIIRule,
    PIIScanResult,
    PIIStrategy,
    create_custom_pii_detector,
    get_default_pii_detector,
)


# =============================================================================
# BASIC PII DETECTION TESTS
# =============================================================================

@pytest.mark.unit
def test_email_detection():
    """Test that emails are detected."""
    detector = PIIDetector()

    text = "Contact me at john.doe@example.com for details."
    result = detector.scan(text)

    assert result.has_pii
    assert "email" in result.detected_types
    assert len(result.matches) == 1
    assert result.matches[0].value == "john.doe@example.com"
    assert "[EMAIL REDACTED]" in result.redacted_text


@pytest.mark.unit
def test_multiple_emails():
    """Test detection of multiple emails."""
    detector = PIIDetector()

    text = "Email john@example.com or jane@test.org"
    result = detector.scan(text)

    assert result.has_pii
    assert len(result.matches) == 2
    assert result.matches[0].value == "john@example.com"
    assert result.matches[1].value == "jane@test.org"


@pytest.mark.unit
def test_credit_card_detection():
    """Test that credit card numbers are detected and masked."""
    detector = PIIDetector()

    # Visa card (16 digits, no spaces)
    # Note: Some credit cards may also match phone patterns
    text = "Card number: 4532123456789012"
    result = detector.scan(text)

    assert result.has_pii
    assert "credit_card" in result.detected_types

    # Find the credit card match specifically
    cc_matches = [m for m in result.matches if m.pii_type == "credit_card"]
    assert len(cc_matches) > 0
    assert cc_matches[0].value == "4532123456789012"

    # Credit cards use MASK strategy by default (show last 4 digits)
    # Verify masked value exists somewhere in redacted text
    assert "9012" in result.redacted_text


@pytest.mark.unit
def test_phone_number_detection():
    """Test phone number detection in various formats."""
    detector = PIIDetector()

    test_cases = [
        "123-456-7890",
        "(123) 456-7890",
        "123.456.7890",
        "1234567890",
    ]

    for phone in test_cases:
        result = detector.scan(f"Call me at {phone}")
        assert result.has_pii, f"Failed to detect: {phone}"
        assert "phone" in result.detected_types


@pytest.mark.unit
def test_ssn_detection():
    """Test Social Security Number detection."""
    detector = PIIDetector()

    test_cases = [
        "123-45-6789",
        "123.45.6789",
        "123 45 6789",
    ]

    for ssn in test_cases:
        result = detector.scan(f"SSN: {ssn}")
        assert result.has_pii, f"Failed to detect: {ssn}"
        assert "ssn" in result.detected_types


@pytest.mark.unit
def test_ip_address_detection():
    """Test IP address detection."""
    detector = PIIDetector()

    text = "Server IP is 192.168.1.100"
    result = detector.scan(text)

    assert result.has_pii
    assert "ip" in result.detected_types
    assert result.matches[0].value == "192.168.1.100"
    assert "[IP REDACTED]" in result.redacted_text


@pytest.mark.unit
def test_api_key_detection_and_blocking():
    """Test that API keys are detected and BLOCK strategy is applied."""
    detector = PIIDetector()

    text = "My key is sk-1234567890abcdefghijklmnopqrstuvwxyz"
    result = detector.scan(text)

    assert result.has_pii
    assert "api_key" in result.detected_types
    assert result.blocked is True
    assert "Blocked PII type: api_key" in result.block_reason


@pytest.mark.unit
def test_anthropic_api_key_detection():
    """Test Anthropic API key pattern detection."""
    detector = PIIDetector()

    # Anthropic key format: sk-ant-[32+ chars]
    text = "Key: sk-ant-api03-1234567890abcdefghijklmnopqrstuvwxyz"
    result = detector.scan(text)

    assert result.has_pii
    assert "api_key" in result.detected_types
    assert result.blocked is True


# =============================================================================
# REDACTION STRATEGY TESTS
# =============================================================================

@pytest.mark.unit
def test_redact_strategy():
    """Test REDACT strategy replaces with placeholder."""
    detector = PIIDetector(rules=[
        PIIRule(
            pii_type="test",
            pattern=r"SECRET\d+",
            strategy=PIIStrategy.REDACT,
            replacement_text="[REDACTED]",
        )
    ])

    result = detector.scan("The code is SECRET123")

    assert result.has_pii
    assert result.redacted_text == "The code is [REDACTED]"


@pytest.mark.unit
def test_mask_strategy():
    """Test MASK strategy shows partial data."""
    detector = PIIDetector(rules=[
        PIIRule(
            pii_type="test",
            pattern=r"\d{16}",
            strategy=PIIStrategy.MASK,
            mask_chars=4,
        )
    ])

    result = detector.scan("Card: 1234567890123456")

    assert result.has_pii
    # Should show last 4 digits
    assert "************3456" in result.redacted_text


@pytest.mark.unit
def test_mask_strategy_short_value():
    """Test MASK strategy with value shorter than mask_chars."""
    detector = PIIDetector(rules=[
        PIIRule(
            pii_type="test",
            pattern=r"\d+",
            strategy=PIIStrategy.MASK,
            mask_chars=4,
        )
    ])

    result = detector.scan("PIN: 12")

    assert result.has_pii
    # Value too short, should mask all
    assert "**" in result.redacted_text


@pytest.mark.unit
def test_hash_strategy():
    """Test HASH strategy replaces with hash."""
    detector = PIIDetector(rules=[
        PIIRule(
            pii_type="test",
            pattern=r"SECRET",
            strategy=PIIStrategy.HASH,
        )
    ])

    result = detector.scan("The word is SECRET")

    assert result.has_pii
    # Should contain a hash (8 char hex)
    assert re.search(r"\[[0-9a-f]{8}\]", result.redacted_text)

    # Verify hash is consistent
    expected_hash = hashlib.sha256("SECRET".encode()).hexdigest()[:8]
    assert f"[{expected_hash}]" in result.redacted_text


@pytest.mark.unit
def test_block_strategy():
    """Test BLOCK strategy sets blocked flag."""
    detector = PIIDetector(rules=[
        PIIRule(
            pii_type="forbidden",
            pattern=r"FORBIDDEN",
            strategy=PIIStrategy.BLOCK,
        )
    ])

    result = detector.scan("This contains FORBIDDEN word")

    assert result.has_pii
    assert result.blocked is True
    assert "forbidden" in result.block_reason


# =============================================================================
# MULTIPLE PII TYPES TESTS
# =============================================================================

@pytest.mark.unit
def test_multiple_pii_types_in_text():
    """Test detection of multiple PII types in one text."""
    detector = PIIDetector()

    text = "Contact john@example.com at 123-456-7890 or IP 192.168.1.1"
    result = detector.scan(text)

    assert result.has_pii
    assert len(result.matches) == 3
    assert set(result.detected_types) == {"email", "phone", "ip"}


@pytest.mark.unit
def test_overlapping_patterns_handled():
    """Test that overlapping matches are handled correctly."""
    detector = PIIDetector()

    # Email contains @ which might match other patterns
    text = "Email: test@192.168.1.1.com"
    result = detector.scan(text)

    assert result.has_pii
    # Should detect email (and possibly IP within it)
    assert "email" in result.detected_types


@pytest.mark.unit
def test_redaction_preserves_order():
    """Test that multiple redactions maintain text structure."""
    detector = PIIDetector()

    text = "Email john@test.com, phone 123-456-7890, IP 10.0.0.1"
    result = detector.scan(text)

    assert result.has_pii
    # Redacted text should preserve structure
    assert "[EMAIL REDACTED]" in result.redacted_text
    assert "[PHONE REDACTED]" in result.redacted_text
    assert "[IP REDACTED]" in result.redacted_text

    # Commas should be preserved
    assert "," in result.redacted_text


# =============================================================================
# CUSTOM RULES TESTS
# =============================================================================

@pytest.mark.unit
def test_add_custom_rule():
    """Test adding custom PII detection rule."""
    detector = PIIDetector(rules=[])  # Empty detector

    detector.add_rule(PIIRule(
        pii_type="employee_id",
        pattern=r"EMP-\d{6}",
        strategy=PIIStrategy.REDACT,
        replacement_text="[EMPLOYEE ID]",
    ))

    result = detector.scan("Employee EMP-123456 submitted report")

    assert result.has_pii
    assert "employee_id" in result.detected_types
    assert "[EMPLOYEE ID]" in result.redacted_text


@pytest.mark.unit
def test_remove_rule():
    """Test removing a PII detection rule."""
    detector = PIIDetector()

    # Remove email detection
    removed = detector.remove_rule("email")

    assert removed is True

    # Email should no longer be detected
    result = detector.scan("Contact john@example.com")

    # Should not detect email anymore
    assert "email" not in result.detected_types


@pytest.mark.unit
def test_remove_nonexistent_rule():
    """Test removing a rule that doesn't exist."""
    detector = PIIDetector()

    removed = detector.remove_rule("nonexistent_type")

    assert removed is False


@pytest.mark.unit
def test_custom_replacement_text():
    """Test custom replacement text."""
    detector = PIIDetector(rules=[
        PIIRule(
            pii_type="custom",
            pattern=r"CUSTOM\d+",
            strategy=PIIStrategy.REDACT,
            replacement_text="<CUSTOM_REDACTED>",
        )
    ])

    result = detector.scan("Value: CUSTOM123")

    assert "<CUSTOM_REDACTED>" in result.redacted_text


# =============================================================================
# EDGE CASES
# =============================================================================

@pytest.mark.unit
def test_empty_text():
    """Test scanning empty text."""
    detector = PIIDetector()

    result = detector.scan("")

    assert result.has_pii is False
    assert len(result.matches) == 0
    assert result.redacted_text == ""


@pytest.mark.unit
def test_no_pii_detected():
    """Test text with no PII."""
    detector = PIIDetector()

    result = detector.scan("This is just normal text with no sensitive data.")

    assert result.has_pii is False
    assert len(result.matches) == 0
    assert result.redacted_text == result.original_text


@pytest.mark.unit
def test_whitespace_only_text():
    """Test text with only whitespace."""
    detector = PIIDetector()

    result = detector.scan("   \n\t  ")

    assert result.has_pii is False


@pytest.mark.unit
def test_case_insensitive_detection():
    """Test that patterns are case insensitive."""
    detector = PIIDetector(rules=[
        PIIRule(
            pii_type="test",
            pattern=r"secret",
            strategy=PIIStrategy.REDACT,
        )
    ])

    # Test different cases
    for text in ["secret", "SECRET", "SeCrEt"]:
        result = detector.scan(text)
        assert result.has_pii, f"Failed for case: {text}"


# =============================================================================
# CONVENIENCE METHODS TESTS
# =============================================================================

@pytest.mark.unit
def test_redact_convenience_method():
    """Test the redact() convenience method."""
    detector = PIIDetector()

    redacted = detector.redact("Email me at test@example.com")

    assert "test@example.com" not in redacted
    assert "[EMAIL REDACTED]" in redacted


@pytest.mark.unit
def test_redact_raises_on_blocked():
    """Test that redact() raises exception when blocked PII detected."""
    detector = PIIDetector()

    with pytest.raises(ValueError, match="Blocked PII type"):
        detector.redact("API key: sk-1234567890abcdefghijklmnopqrstuvwxyz")


@pytest.mark.unit
def test_contains_pii():
    """Test the contains_pii() convenience method."""
    detector = PIIDetector()

    assert detector.contains_pii("Email: test@example.com") is True
    assert detector.contains_pii("No sensitive data here") is False


# =============================================================================
# HELPER FUNCTIONS TESTS
# =============================================================================

@pytest.mark.unit
def test_get_default_pii_detector():
    """Test get_default_pii_detector() helper."""
    detector = get_default_pii_detector()

    assert isinstance(detector, PIIDetector)

    # Should detect common PII types
    result = detector.scan("Email: test@example.com")
    assert result.has_pii


@pytest.mark.unit
def test_create_custom_detector_with_selected_types():
    """Test create_custom_pii_detector() with selected PII types."""
    detector = create_custom_pii_detector(pii_types=["email", "phone"])

    # Should detect email and phone
    result = detector.scan("Email test@example.com, phone 123-456-7890")
    assert "email" in result.detected_types
    assert "phone" in result.detected_types

    # Should NOT detect credit card (not in selected types)
    result = detector.scan("Card: 4532123456789012")
    assert "credit_card" not in result.detected_types


@pytest.mark.unit
def test_create_custom_detector_with_custom_patterns():
    """Test create_custom_pii_detector() with custom patterns."""
    detector = create_custom_pii_detector(
        pii_types=[],
        custom_patterns={
            "employee_id": r"EMP-\d{6}",
            "project_code": r"PROJ-[A-Z]{3}",
        }
    )

    result = detector.scan("Employee EMP-123456 on PROJ-ABC")

    assert "employee_id" in result.detected_types
    assert "project_code" in result.detected_types
    assert "[EMPLOYEE_ID REDACTED]" in result.redacted_text
    assert "[PROJECT_CODE REDACTED]" in result.redacted_text


@pytest.mark.unit
def test_create_custom_detector_combined():
    """Test create_custom_pii_detector() with both default and custom."""
    detector = create_custom_pii_detector(
        pii_types=["email"],
        custom_patterns={"custom": r"CUSTOM\d+"}
    )

    result = detector.scan("Email test@example.com and CUSTOM123")

    assert "email" in result.detected_types
    assert "custom" in result.detected_types


# =============================================================================
# PIIScanResult PROPERTY TESTS
# =============================================================================

@pytest.mark.unit
def test_scan_result_has_pii_property():
    """Test PIIScanResult.has_pii property."""
    # With matches
    result = PIIScanResult(
        original_text="test",
        matches=[PIIMatch("email", "test@example.com", 0, 16)],
    )
    assert result.has_pii is True

    # Without matches
    result = PIIScanResult(original_text="test", matches=[])
    assert result.has_pii is False


@pytest.mark.unit
def test_scan_result_detected_types_property():
    """Test PIIScanResult.detected_types property."""
    result = PIIScanResult(
        original_text="test",
        matches=[
            PIIMatch("email", "test@example.com", 0, 16),
            PIIMatch("phone", "123-456-7890", 20, 32),
            PIIMatch("email", "another@test.com", 35, 51),
        ],
    )

    detected = result.detected_types

    # Should return unique types
    assert set(detected) == {"email", "phone"}
    assert len(detected) == 2


# =============================================================================
# PATTERN COMPILATION TESTS
# =============================================================================

@pytest.mark.unit
def test_rule_with_string_pattern():
    """Test that string patterns are compiled."""
    detector = PIIDetector(rules=[
        PIIRule(
            pii_type="test",
            pattern="TEST\\d+",  # String pattern
            strategy=PIIStrategy.REDACT,
        )
    ])

    result = detector.scan("Value: TEST123")

    assert result.has_pii
    assert result.matches[0].value == "TEST123"


@pytest.mark.unit
def test_rule_with_compiled_pattern():
    """Test that pre-compiled patterns work."""
    pattern = re.compile(r"TEST\d+", re.IGNORECASE)

    detector = PIIDetector(rules=[
        PIIRule(
            pii_type="test",
            pattern=pattern,
            strategy=PIIStrategy.REDACT,
        )
    ])

    result = detector.scan("Value: TEST123")

    assert result.has_pii


# =============================================================================
# REAL-WORLD SCENARIO TESTS
# =============================================================================

@pytest.mark.unit
def test_customer_support_message():
    """Test realistic customer support message with multiple PII types."""
    detector = PIIDetector()

    message = """
    Customer inquiry from john.doe@example.com:

    My credit card 4532123456789012 was charged twice.
    Please call me at (555) 123-4567 to resolve.

    Account ID: 192.168.1.100 (internal reference)
    """

    result = detector.scan(message)

    assert result.has_pii
    assert "email" in result.detected_types
    assert "credit_card" in result.detected_types
    assert "phone" in result.detected_types
    assert "ip" in result.detected_types

    # Verify redacted text doesn't contain original PII
    assert "john.doe@example.com" not in result.redacted_text
    assert "4532123456789012" not in result.redacted_text


@pytest.mark.unit
def test_log_file_with_api_keys():
    """Test log file containing API keys (should block)."""
    detector = PIIDetector()

    log_entry = """
    [2024-12-25 10:30:00] INFO: API request initiated
    [2024-12-25 10:30:01] DEBUG: Using key sk-1234567890abcdefghijklmnopqrstuvwxyz
    [2024-12-25 10:30:02] INFO: Request successful
    """

    result = detector.scan(log_entry)

    assert result.has_pii
    assert result.blocked is True
    assert "api_key" in result.detected_types


@pytest.mark.unit
def test_email_with_multiple_recipients():
    """Test email text with multiple recipients."""
    detector = PIIDetector()

    email = """
    To: alice@company.com, bob@company.com, charlie@example.org
    CC: support@company.com

    Please contact me at my personal email: personal@gmail.com
    """

    result = detector.scan(email)

    assert result.has_pii
    # Should detect all 5 email addresses
    assert len([m for m in result.matches if m.pii_type == "email"]) == 5
