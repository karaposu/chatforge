"""
Test ContextLayer dataclass.

This module tests the ContextLayer dataclass which is the fundamental
unit of context in LDCI.

Test Strategy:
- Test creation with required fields
- Test default values
- Test all field combinations
- Test render() method
- Test __repr__()
- Test edge cases
"""

import time

import pytest

from chatforge.services.context.layer import ContextLayer
from chatforge.services.context.types import (
    Authority,
    CompileOptions,
    InjectTiming,
    Layer,
    Stability,
)


# =============================================================================
# CREATION TESTS
# =============================================================================


@pytest.mark.unit
def test_create_layer_minimal():
    """Test creating ContextLayer with only required fields."""
    layer = ContextLayer(
        layer=Layer.STATE,
        content="Test content",
    )

    assert layer.layer == Layer.STATE
    assert layer.content == "Test content"


@pytest.mark.unit
def test_create_layer_with_all_fields():
    """Test creating ContextLayer with all fields."""
    layer = ContextLayer(
        layer=Layer.STATE,
        content="Test content",
        inject_at=InjectTiming.TURN_START,
        order=10,
        authority=Authority.DIRECTIVE,
        stability=Stability.TURN,
        source="test",
    )

    assert layer.layer == Layer.STATE
    assert layer.content == "Test content"
    assert layer.inject_at == InjectTiming.TURN_START
    assert layer.order == 10
    assert layer.authority == Authority.DIRECTIVE
    assert layer.stability == Stability.TURN
    assert layer.source == "test"


@pytest.mark.unit
def test_create_base_layer():
    """Test creating a BASE layer."""
    layer = ContextLayer(
        layer=Layer.BASE,
        content="You are a helpful assistant.",
        inject_at=InjectTiming.SESSION_START,
    )

    assert layer.layer == Layer.BASE
    assert layer.inject_at == InjectTiming.SESSION_START


@pytest.mark.unit
def test_create_state_layer():
    """Test creating a STATE layer."""
    layer = ContextLayer(
        layer=Layer.STATE,
        content="User is in the kitchen.",
        inject_at=InjectTiming.TURN_START,
        order=10,
    )

    assert layer.layer == Layer.STATE
    assert layer.inject_at == InjectTiming.TURN_START
    assert layer.order == 10


@pytest.mark.unit
def test_create_override_layer():
    """Test creating an OVERRIDE layer."""
    layer = ContextLayer(
        layer=Layer.OVERRIDE,
        content="Test scenario: user is angry.",
    )

    assert layer.layer == Layer.OVERRIDE


@pytest.mark.unit
def test_create_derived_layer():
    """Test creating a DERIVED layer."""
    layer = ContextLayer(
        layer=Layer.DERIVED,
        content="User seems frustrated based on recent messages.",
        inject_at=InjectTiming.AFTER_RESPONSE,
        authority=Authority.SUGGESTIVE,
    )

    assert layer.layer == Layer.DERIVED
    assert layer.inject_at == InjectTiming.AFTER_RESPONSE
    assert layer.authority == Authority.SUGGESTIVE


@pytest.mark.unit
def test_create_proactive_layer():
    """Test creating a PROACTIVE layer."""
    layer = ContextLayer(
        layer=Layer.PROACTIVE,
        content="Remind user about upcoming meeting.",
        inject_at=InjectTiming.ASAP,
    )

    assert layer.layer == Layer.PROACTIVE
    assert layer.inject_at == InjectTiming.ASAP


# =============================================================================
# DEFAULT VALUES TESTS
# =============================================================================


@pytest.mark.unit
def test_default_inject_at():
    """Test default inject_at is TURN_START."""
    layer = ContextLayer(layer=Layer.STATE, content="Test")

    assert layer.inject_at == InjectTiming.TURN_START


@pytest.mark.unit
def test_default_order():
    """Test default order is 0."""
    layer = ContextLayer(layer=Layer.STATE, content="Test")

    assert layer.order == 0


@pytest.mark.unit
def test_default_authority():
    """Test default authority is INFORMATIVE."""
    layer = ContextLayer(layer=Layer.STATE, content="Test")

    assert layer.authority == Authority.INFORMATIVE


@pytest.mark.unit
def test_default_stability():
    """Test default stability is TURN."""
    layer = ContextLayer(layer=Layer.STATE, content="Test")

    assert layer.stability == Stability.TURN


@pytest.mark.unit
def test_default_source():
    """Test default source is 'app'."""
    layer = ContextLayer(layer=Layer.STATE, content="Test")

    assert layer.source == "app"


@pytest.mark.unit
def test_timestamp_auto_generated():
    """Test that timestamp is auto-generated."""
    before = time.time()
    layer = ContextLayer(layer=Layer.STATE, content="Test")
    after = time.time()

    assert before <= layer.timestamp <= after


# =============================================================================
# RENDER TESTS
# =============================================================================


@pytest.mark.unit
def test_render_returns_content():
    """Test render() returns content."""
    layer = ContextLayer(layer=Layer.STATE, content="Test content")

    assert layer.render() == "Test content"


@pytest.mark.unit
def test_render_with_options():
    """Test render() accepts options."""
    layer = ContextLayer(layer=Layer.STATE, content="Test content")
    options = CompileOptions(verbose=True)

    assert layer.render(options) == "Test content"


@pytest.mark.unit
def test_render_with_none_options():
    """Test render() works with None options."""
    layer = ContextLayer(layer=Layer.STATE, content="Test content")

    assert layer.render(None) == "Test content"


@pytest.mark.unit
def test_render_empty_content():
    """Test render() with empty content."""
    layer = ContextLayer(layer=Layer.STATE, content="")

    assert layer.render() == ""


@pytest.mark.unit
def test_render_multiline_content():
    """Test render() with multiline content."""
    content = """Line 1
Line 2
Line 3"""
    layer = ContextLayer(layer=Layer.STATE, content=content)

    assert layer.render() == content


# =============================================================================
# __REPR__ TESTS
# =============================================================================


@pytest.mark.unit
def test_repr_short_content():
    """Test __repr__ with short content."""
    layer = ContextLayer(layer=Layer.STATE, content="Short", order=5)

    repr_str = repr(layer)

    assert "layer=state" in repr_str
    assert "inject_at=turn_start" in repr_str
    assert "order=5" in repr_str
    assert "Short" in repr_str


@pytest.mark.unit
def test_repr_long_content_truncated():
    """Test __repr__ truncates long content."""
    long_content = "x" * 100
    layer = ContextLayer(layer=Layer.STATE, content=long_content)

    repr_str = repr(layer)

    # Should be truncated with "..."
    assert "..." in repr_str
    # Should not contain full content
    assert long_content not in repr_str


@pytest.mark.unit
def test_repr_exactly_50_chars():
    """Test __repr__ with exactly 50 char content (not truncated)."""
    content = "x" * 50
    layer = ContextLayer(layer=Layer.STATE, content=content)

    repr_str = repr(layer)

    # 50 chars should not be truncated
    assert "..." not in repr_str


@pytest.mark.unit
def test_repr_51_chars_truncated():
    """Test __repr__ with 51 char content (truncated)."""
    content = "x" * 51
    layer = ContextLayer(layer=Layer.STATE, content=content)

    repr_str = repr(layer)

    # 51 chars should be truncated
    assert "..." in repr_str


# =============================================================================
# EDGE CASES
# =============================================================================


@pytest.mark.unit
def test_layer_with_special_characters():
    """Test layer with special characters in content."""
    content = "Hello <world> & 'test' \"quotes\""
    layer = ContextLayer(layer=Layer.STATE, content=content)

    assert layer.content == content
    assert layer.render() == content


@pytest.mark.unit
def test_layer_with_unicode():
    """Test layer with unicode content."""
    content = "Hello 世界 🌍 مرحبا"
    layer = ContextLayer(layer=Layer.STATE, content=content)

    assert layer.content == content
    assert layer.render() == content


@pytest.mark.unit
def test_layer_with_very_long_content():
    """Test layer with very long content."""
    content = "x" * 100000  # 100K characters
    layer = ContextLayer(layer=Layer.STATE, content=content)

    assert layer.content == content
    assert len(layer.render()) == 100000


@pytest.mark.unit
def test_layer_negative_order():
    """Test layer with negative order value."""
    layer = ContextLayer(layer=Layer.STATE, content="Test", order=-10)

    assert layer.order == -10


@pytest.mark.unit
def test_layer_large_order():
    """Test layer with large order value."""
    layer = ContextLayer(layer=Layer.STATE, content="Test", order=999999)

    assert layer.order == 999999


@pytest.mark.unit
def test_layer_immutability():
    """Test that layer fields can be modified (dataclass is mutable by default)."""
    layer = ContextLayer(layer=Layer.STATE, content="Original")

    # Dataclass is mutable
    layer.content = "Modified"
    assert layer.content == "Modified"

    layer.order = 100
    assert layer.order == 100


# =============================================================================
# COMPARISON TESTS
# =============================================================================


@pytest.mark.unit
def test_layers_equality():
    """Test that identical layers are equal."""
    layer1 = ContextLayer(layer=Layer.STATE, content="Test", order=10)
    layer2 = ContextLayer(layer=Layer.STATE, content="Test", order=10)

    # Note: timestamps will differ, so they won't be fully equal
    # but we can compare specific fields
    assert layer1.layer == layer2.layer
    assert layer1.content == layer2.content
    assert layer1.order == layer2.order


@pytest.mark.unit
def test_layers_different_content():
    """Test that layers with different content are not equal."""
    layer1 = ContextLayer(layer=Layer.STATE, content="Test 1")
    layer2 = ContextLayer(layer=Layer.STATE, content="Test 2")

    assert layer1.content != layer2.content


@pytest.mark.unit
def test_layers_different_types():
    """Test that layers of different types are not equal."""
    layer1 = ContextLayer(layer=Layer.STATE, content="Test")
    layer2 = ContextLayer(layer=Layer.DERIVED, content="Test")

    assert layer1.layer != layer2.layer


# =============================================================================
# CONCATENATION TESTS (__add__ / __radd__)
# =============================================================================


@pytest.mark.unit
def test_add_two_layers():
    """Test layer + layer concatenation."""
    layer1 = ContextLayer(layer=Layer.STATE, content="First")
    layer2 = ContextLayer(layer=Layer.STATE, content="Second")

    result = layer1 + layer2

    assert result == "First\n\nSecond"


@pytest.mark.unit
def test_add_layer_and_string():
    """Test layer + string concatenation."""
    layer = ContextLayer(layer=Layer.STATE, content="Content")

    result = layer + " suffix"

    assert result == "Content suffix"


@pytest.mark.unit
def test_radd_string_and_layer():
    """Test string + layer concatenation."""
    layer = ContextLayer(layer=Layer.STATE, content="Content")

    result = "prefix" + layer

    assert result == "prefix\n\nContent"


@pytest.mark.unit
def test_add_multiple_layers():
    """Test chaining multiple layers."""
    layer1 = ContextLayer(layer=Layer.STATE, content="A")
    layer2 = ContextLayer(layer=Layer.STATE, content="B")
    layer3 = ContextLayer(layer=Layer.STATE, content="C")

    result = layer1 + layer2 + layer3

    assert result == "A\n\nB\n\nC"


@pytest.mark.unit
def test_add_empty_layer():
    """Test concatenating with empty content."""
    layer1 = ContextLayer(layer=Layer.STATE, content="Content")
    layer2 = ContextLayer(layer=Layer.STATE, content="")

    result = layer1 + layer2

    assert result == "Content\n\n"


# =============================================================================
# PREFIX TESTS
# =============================================================================


@pytest.mark.unit
def test_render_with_prefix():
    """Test render() prepends prefix to content."""
    layer = ContextLayer(
        layer=Layer.STATE,
        content="Room description here",
        prefix="=== ROOM CONTEXT ===",
    )

    result = layer.render()

    assert result == "=== ROOM CONTEXT ===\nRoom description here"


@pytest.mark.unit
def test_render_without_prefix():
    """Test render() returns content when no prefix."""
    layer = ContextLayer(layer=Layer.STATE, content="Just content")

    result = layer.render()

    assert result == "Just content"


@pytest.mark.unit
def test_render_empty_prefix():
    """Test render() with empty string prefix."""
    layer = ContextLayer(layer=Layer.STATE, content="Content", prefix="")

    result = layer.render()

    assert result == "Content"


# =============================================================================
# DEFAULT TESTS
# =============================================================================


@pytest.mark.unit
def test_render_with_default_when_content_empty():
    """Test render() uses default when content is empty."""
    layer = ContextLayer(
        layer=Layer.STATE,
        content="",
        default="Default content here",
    )

    result = layer.render()

    assert result == "Default content here"


@pytest.mark.unit
def test_render_content_over_default():
    """Test render() prefers content over default."""
    layer = ContextLayer(
        layer=Layer.STATE,
        content="Actual content",
        default="Default content",
    )

    result = layer.render()

    assert result == "Actual content"


@pytest.mark.unit
def test_render_empty_when_no_content_and_no_default():
    """Test render() returns empty string when both are empty."""
    layer = ContextLayer(layer=Layer.STATE, content="", default="")

    result = layer.render()

    assert result == ""


@pytest.mark.unit
def test_render_prefix_with_default():
    """Test render() applies prefix to default content."""
    layer = ContextLayer(
        layer=Layer.STATE,
        content="",
        default="Fallback content",
        prefix="=== SECTION ===",
    )

    result = layer.render()

    assert result == "=== SECTION ===\nFallback content"


@pytest.mark.unit
def test_render_prefix_not_applied_when_empty():
    """Test render() doesn't add prefix when content is empty and no default."""
    layer = ContextLayer(
        layer=Layer.STATE,
        content="",
        default="",
        prefix="=== HEADER ===",
    )

    result = layer.render()

    assert result == ""


# =============================================================================
# COMBINED PREFIX + DEFAULT + ORDER TESTS
# =============================================================================


@pytest.mark.unit
def test_layer_with_all_formatting_options():
    """Test layer with prefix, default, and order."""
    layer = ContextLayer(
        layer=Layer.STATE,
        content="Player progress data",
        prefix="=== PLAYER PROGRESS ===",
        default="No progress data",
        order=10,
    )

    assert layer.prefix == "=== PLAYER PROGRESS ==="
    assert layer.default == "No progress data"
    assert layer.order == 10
    assert layer.render() == "=== PLAYER PROGRESS ===\nPlayer progress data"
