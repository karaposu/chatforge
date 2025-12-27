"""
Test Content Filter Middleware.

This module tests the ContentFilter component which uses simple keyword matching
to block content containing banned words.

Test Strategy:
- Test keyword detection (case-insensitive)
- Test default and custom keywords
- Test adding/removing keywords
- Test edge cases (empty content, no matches)
- Test real-world scenarios

Note: ContentFilter has NO dependencies (pure keyword matching), so all tests are fast.
"""

import pytest

from chatforge.middleware import ContentCheckResult, ContentFilter


# =============================================================================
# BASIC KEYWORD DETECTION TESTS
# =============================================================================

@pytest.mark.unit
def test_default_keywords_block_hack():
    """Test that default keywords block 'hack'."""
    filter = ContentFilter()

    result = filter.check_content("How do I hack a password?")

    assert result.is_allowed is False
    assert result.blocked_keyword == "hack"
    assert result.rejection_message is not None


@pytest.mark.unit
def test_case_insensitive_matching():
    """Test that keyword matching is case-insensitive."""
    filter = ContentFilter(banned_keywords=["forbidden"])

    test_cases = [
        "This contains FORBIDDEN word",
        "This contains forbidden word",
        "This contains FoRbIdDeN word",
    ]

    for text in test_cases:
        result = filter.check_content(text)
        assert result.is_allowed is False, f"Failed for: {text}"
        assert result.blocked_keyword == "forbidden"


@pytest.mark.unit
def test_allowed_content():
    """Test that content without banned keywords is allowed."""
    filter = ContentFilter()

    result = filter.check_content("How do I improve security on my system?")

    assert result.is_allowed is True
    assert result.blocked_keyword is None
    assert result.original_content == "How do I improve security on my system?"


@pytest.mark.unit
def test_multiple_banned_keywords():
    """Test detection when content contains multiple banned keywords."""
    filter = ContentFilter(banned_keywords=["hack", "exploit", "malware"])

    result = filter.check_content("Can I hack and exploit malware?")

    # Should detect first match
    assert result.is_allowed is False
    assert result.blocked_keyword in ["hack", "exploit", "malware"]


# =============================================================================
# CUSTOM KEYWORDS TESTS
# =============================================================================

@pytest.mark.unit
def test_custom_keywords():
    """Test creating filter with custom keywords."""
    filter = ContentFilter(banned_keywords=["forbidden", "restricted", "blocked"])

    # Should block custom keywords
    result = filter.check_content("This is a forbidden topic")
    assert result.is_allowed is False
    assert result.blocked_keyword == "forbidden"

    # Should not block default keywords (we overrode them)
    result = filter.check_content("How do I hack this?")
    assert result.is_allowed is True


@pytest.mark.unit
def test_empty_keywords_uses_defaults():
    """Test that empty keyword list falls back to defaults."""
    # NOTE: ContentFilter uses `banned_keywords or default_keywords`,
    # so [] is falsy and defaults are used
    filter = ContentFilter(banned_keywords=[])

    # Should still use default keywords ([] is falsy)
    result = filter.check_content("hack exploit malware")
    assert result.is_allowed is False
    assert result.blocked_keyword in ["hack", "exploit", "malware"]


@pytest.mark.unit
def test_custom_rejection_message():
    """Test custom rejection message."""
    custom_message = "This topic is not allowed in our system."
    filter = ContentFilter(
        banned_keywords=["forbidden"],
        rejection_message=custom_message,
    )

    result = filter.check_content("forbidden content")

    assert result.is_allowed is False
    assert result.rejection_message == custom_message


# =============================================================================
# ADD/REMOVE KEYWORDS TESTS
# =============================================================================

@pytest.mark.unit
def test_add_keyword():
    """Test dynamically adding keywords."""
    filter = ContentFilter(banned_keywords=[])

    # Should be allowed initially
    result = filter.check_content("This contains newkeyword")
    assert result.is_allowed is True

    # Add keyword
    filter.add_keyword("newkeyword")

    # Should now be blocked
    result = filter.check_content("This contains newkeyword")
    assert result.is_allowed is False
    assert result.blocked_keyword == "newkeyword"


@pytest.mark.unit
def test_add_keyword_case_insensitive():
    """Test that added keywords are stored lowercase."""
    filter = ContentFilter(banned_keywords=[])

    filter.add_keyword("UPPERCASE")

    # Should block regardless of case
    for text in ["uppercase", "UPPERCASE", "UpPeRcAsE"]:
        result = filter.check_content(text)
        assert result.is_allowed is False


@pytest.mark.unit
def test_add_duplicate_keyword():
    """Test that adding duplicate keyword doesn't create duplicates."""
    filter = ContentFilter(banned_keywords=["test"])

    filter.add_keyword("test")
    filter.add_keyword("TEST")

    # Should only have one instance
    assert filter.banned_keywords.count("test") == 1


@pytest.mark.unit
def test_remove_keyword():
    """Test removing keywords."""
    filter = ContentFilter(banned_keywords=["remove_me", "keep_me"])

    # Remove keyword
    removed = filter.remove_keyword("remove_me")

    assert removed is True
    assert "remove_me" not in filter.banned_keywords
    assert "keep_me" in filter.banned_keywords

    # Should no longer block
    result = filter.check_content("Contains remove_me")
    assert result.is_allowed is True


@pytest.mark.unit
def test_remove_nonexistent_keyword():
    """Test removing keyword that doesn't exist."""
    filter = ContentFilter(banned_keywords=["test"])

    removed = filter.remove_keyword("nonexistent")

    assert removed is False
    assert len(filter.banned_keywords) == 1


@pytest.mark.unit
def test_remove_keyword_case_insensitive():
    """Test that keyword removal is case-insensitive."""
    filter = ContentFilter(banned_keywords=["test"])

    # Remove with different case
    removed = filter.remove_keyword("TEST")

    assert removed is True
    assert "test" not in filter.banned_keywords


# =============================================================================
# EDGE CASES
# =============================================================================

@pytest.mark.unit
def test_empty_content():
    """Test checking empty content."""
    filter = ContentFilter()

    result = filter.check_content("")

    assert result.is_allowed is True
    assert result.blocked_keyword is None


@pytest.mark.unit
def test_none_content():
    """Test checking None content."""
    filter = ContentFilter()

    result = filter.check_content(None)

    assert result.is_allowed is True


@pytest.mark.unit
def test_whitespace_only_content():
    """Test content with only whitespace."""
    filter = ContentFilter()

    result = filter.check_content("   \n\t  ")

    assert result.is_allowed is True


@pytest.mark.unit
def test_keyword_as_substring():
    """Test that keywords match as substrings."""
    filter = ContentFilter(banned_keywords=["hack"])

    # "hack" is part of "hacker"
    result = filter.check_content("He is a hacker")

    assert result.is_allowed is False
    assert result.blocked_keyword == "hack"


@pytest.mark.unit
def test_multi_word_keyword():
    """Test multi-word banned keywords."""
    filter = ContentFilter(banned_keywords=["bypass security"])

    result = filter.check_content("How do I bypass security measures?")

    assert result.is_allowed is False
    assert result.blocked_keyword == "bypass security"


# =============================================================================
# DEFAULT KEYWORDS TESTS
# =============================================================================

@pytest.mark.unit
def test_default_keywords_comprehensive():
    """Test all default keywords are working."""
    filter = ContentFilter()  # Uses defaults

    # Test a sample of default keywords
    test_cases = {
        "hack": "How to hack WiFi",
        "exploit": "Find exploits in system",
        "malware": "Download malware samples",
        "ransomware": "Create ransomware",
        "phishing": "Phishing techniques",
        "ddos": "Launch ddos attack",
    }

    for keyword, text in test_cases.items():
        result = filter.check_content(text)
        assert result.is_allowed is False, f"Failed to block: {keyword}"
        assert result.blocked_keyword == keyword


# =============================================================================
# CONTENT CHECK RESULT TESTS
# =============================================================================

@pytest.mark.unit
def test_check_result_allowed_structure():
    """Test ContentCheckResult structure when allowed."""
    result = ContentCheckResult(
        is_allowed=True,
        original_content="Test content",
    )

    assert result.is_allowed is True
    assert result.original_content == "Test content"
    assert result.blocked_keyword is None
    assert result.rejection_message is None


@pytest.mark.unit
def test_check_result_blocked_structure():
    """Test ContentCheckResult structure when blocked."""
    result = ContentCheckResult(
        is_allowed=False,
        original_content="Bad content",
        blocked_keyword="bad",
        rejection_message="Content blocked",
    )

    assert result.is_allowed is False
    assert result.original_content == "Bad content"
    assert result.blocked_keyword == "bad"
    assert result.rejection_message == "Content blocked"


# =============================================================================
# REAL-WORLD SCENARIO TESTS
# =============================================================================

@pytest.mark.unit
def test_chat_message_filtering():
    """Test filtering of chat messages."""
    filter = ContentFilter()

    # Legitimate IT question
    result = filter.check_content("How do I configure firewall rules?")
    assert result.is_allowed is True

    # Suspicious request
    result = filter.check_content("How do I hack into the firewall?")
    assert result.is_allowed is False


@pytest.mark.unit
def test_programming_discussion():
    """Test that legitimate programming discussion is allowed."""
    filter = ContentFilter()

    # Legitimate security discussion
    legitimate_texts = [
        "I'm studying cybersecurity and want to learn about penetration testing",
        "What are best practices for secure password storage?",
        "How does HTTPS encryption work?",
    ]

    for text in legitimate_texts:
        result = filter.check_content(text)
        assert result.is_allowed is True, f"Incorrectly blocked: {text}"


@pytest.mark.unit
def test_malicious_request_patterns():
    """Test detection of malicious request patterns."""
    filter = ContentFilter()

    malicious_texts = [
        "How to hack someone's email account",
        "Best malware for stealing data",
        "SQL injection tutorial for beginners",
        "DDoS tools download",
    ]

    for text in malicious_texts:
        result = filter.check_content(text)
        assert result.is_allowed is False, f"Failed to block: {text}"


@pytest.mark.unit
def test_domain_specific_filter():
    """Test creating domain-specific content filter."""
    # Education platform filter
    education_filter = ContentFilter(
        banned_keywords=["cheat", "plagiarize", "essay mill", "homework answers"],
        rejection_message="Academic integrity policies prohibit this request.",
    )

    result = education_filter.check_content("Where can I buy essay mill services?")

    assert result.is_allowed is False
    assert result.blocked_keyword == "essay mill"
    assert "Academic integrity" in result.rejection_message


@pytest.mark.unit
def test_corporate_environment_filter():
    """Test content filter for corporate environment."""
    corporate_filter = ContentFilter(
        banned_keywords=[
            "competitor secrets",
            "insider trading",
            "confidential leak",
        ],
        rejection_message="This request violates company policy.",
    )

    result = corporate_filter.check_content("How do I access competitor secrets?")

    assert result.is_allowed is False
    assert result.blocked_keyword == "competitor secrets"


@pytest.mark.unit
def test_special_characters_in_keywords():
    """Test keywords with special characters."""
    filter = ContentFilter(banned_keywords=["test-keyword", "test_keyword"])

    # Should match exactly
    result = filter.check_content("This contains test-keyword")
    assert result.is_allowed is False

    result = filter.check_content("This contains test_keyword")
    assert result.is_allowed is False


@pytest.mark.unit
def test_unicode_content():
    """Test filtering of Unicode content."""
    filter = ContentFilter(banned_keywords=["forbidden", "禁止"])  # Chinese for "forbidden"

    # ASCII
    result = filter.check_content("This is forbidden")
    assert result.is_allowed is False

    # Unicode
    result = filter.check_content("这是禁止的内容")  # "This is forbidden content" in Chinese
    assert result.is_allowed is False


@pytest.mark.unit
def test_long_content_performance():
    """Test that filter performs well with long content."""
    filter = ContentFilter(banned_keywords=["hack"])

    # Long content with keyword near the end
    long_content = "This is a very long text. " * 1000 + "hack password"

    result = filter.check_content(long_content)

    assert result.is_allowed is False
    assert result.blocked_keyword == "hack"


@pytest.mark.unit
def test_filter_modification_workflow():
    """Test realistic workflow of modifying filter over time."""
    # Start with minimal filter
    filter = ContentFilter(banned_keywords=["test1"])

    # Add keywords as needed
    filter.add_keyword("test2")
    filter.add_keyword("test3")

    assert "test1" in filter.banned_keywords
    assert "test2" in filter.banned_keywords
    assert "test3" in filter.banned_keywords

    # Remove deprecated keyword
    filter.remove_keyword("test1")

    assert "test1" not in filter.banned_keywords
    assert "test2" in filter.banned_keywords

    # Verify filtering works
    result = filter.check_content("Contains test2")
    assert result.is_allowed is False
