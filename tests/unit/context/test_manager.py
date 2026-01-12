"""
Test ContextManager class.

This module tests the ContextManager which orchestrates layered context
injection for both HTTP and S2S modalities.

Test Strategy:
- Test add() for all layer types
- Test get_base() with and without override
- Test compile() returns all layers
- Test compile_for() filters by timing
- Test get_layers_for() returns layer objects
- Test clear_*() methods
- Test order sorting
- Test edge cases
- Test HTTP vs S2S patterns
"""

import pytest

from chatforge.services.context.layer import ContextLayer
from chatforge.services.context.manager import ContextManager
from chatforge.services.context.types import (
    InjectTiming,
    Layer,
)


# =============================================================================
# INITIALIZATION TESTS
# =============================================================================


@pytest.mark.unit
def test_manager_initialization():
    """Test ContextManager initialization."""
    context = ContextManager()

    assert context.get_base() is None
    assert context.compile() == ""
    assert context.layer_counts == {
        "base": 0,
        "state": 0,
        "override": 0,
        "derived": 0,
        "proactive": 0,
    }


@pytest.mark.unit
def test_manager_repr():
    """Test ContextManager __repr__."""
    context = ContextManager()
    context.add(ContextLayer(layer=Layer.BASE, content="Base"))
    context.add(ContextLayer(layer=Layer.STATE, content="State 1"))
    context.add(ContextLayer(layer=Layer.STATE, content="State 2"))

    repr_str = repr(context)

    assert "ContextManager" in repr_str
    assert "'base': 1" in repr_str
    assert "'state': 2" in repr_str


# =============================================================================
# ADD LAYER TESTS
# =============================================================================


@pytest.mark.unit
def test_add_base_layer():
    """Test adding a BASE layer."""
    context = ContextManager()

    context.add(ContextLayer(layer=Layer.BASE, content="You are helpful."))

    assert context.get_base() == "You are helpful."
    assert context.layer_counts["base"] == 1


@pytest.mark.unit
def test_add_base_replaces_previous():
    """Test that adding BASE replaces previous base."""
    context = ContextManager()

    context.add(ContextLayer(layer=Layer.BASE, content="First base"))
    context.add(ContextLayer(layer=Layer.BASE, content="Second base"))

    assert context.get_base() == "Second base"
    assert context.layer_counts["base"] == 1


@pytest.mark.unit
def test_add_state_layer():
    """Test adding STATE layers."""
    context = ContextManager()

    context.add(ContextLayer(layer=Layer.STATE, content="State 1"))
    context.add(ContextLayer(layer=Layer.STATE, content="State 2"))

    assert context.layer_counts["state"] == 2


@pytest.mark.unit
def test_add_override_layer():
    """Test adding OVERRIDE layer."""
    context = ContextManager()

    context.add(ContextLayer(layer=Layer.OVERRIDE, content="Override content"))

    assert context.layer_counts["override"] == 1


@pytest.mark.unit
def test_add_override_replaces_previous():
    """Test that adding OVERRIDE replaces previous override."""
    context = ContextManager()

    context.add(ContextLayer(layer=Layer.OVERRIDE, content="First override"))
    context.add(ContextLayer(layer=Layer.OVERRIDE, content="Second override"))

    assert context.layer_counts["override"] == 1


@pytest.mark.unit
def test_add_derived_layer():
    """Test adding DERIVED layers."""
    context = ContextManager()

    context.add(ContextLayer(layer=Layer.DERIVED, content="Derived 1"))
    context.add(ContextLayer(layer=Layer.DERIVED, content="Derived 2"))

    assert context.layer_counts["derived"] == 2


@pytest.mark.unit
def test_add_proactive_layer():
    """Test adding PROACTIVE layers."""
    context = ContextManager()

    context.add(ContextLayer(layer=Layer.PROACTIVE, content="Proactive 1"))
    context.add(ContextLayer(layer=Layer.PROACTIVE, content="Proactive 2"))

    assert context.layer_counts["proactive"] == 2


# =============================================================================
# GET_BASE TESTS
# =============================================================================


@pytest.mark.unit
def test_get_base_empty():
    """Test get_base() when no base is set."""
    context = ContextManager()

    assert context.get_base() is None


@pytest.mark.unit
def test_get_base_returns_base_content():
    """Test get_base() returns base content."""
    context = ContextManager()
    context.add(ContextLayer(layer=Layer.BASE, content="Base content"))

    assert context.get_base() == "Base content"


@pytest.mark.unit
def test_get_base_returns_override_when_set():
    """Test get_base() returns override content when set."""
    context = ContextManager()
    context.add(ContextLayer(layer=Layer.BASE, content="Base content"))
    context.add(ContextLayer(layer=Layer.OVERRIDE, content="Override content"))

    assert context.get_base() == "Override content"


@pytest.mark.unit
def test_get_base_returns_base_after_override_cleared():
    """Test get_base() returns base after override is cleared."""
    context = ContextManager()
    context.add(ContextLayer(layer=Layer.BASE, content="Base content"))
    context.add(ContextLayer(layer=Layer.OVERRIDE, content="Override content"))

    context.clear_override()

    assert context.get_base() == "Base content"


# =============================================================================
# COMPILE TESTS
# =============================================================================


@pytest.mark.unit
def test_compile_empty():
    """Test compile() with no layers."""
    context = ContextManager()

    assert context.compile() == ""


@pytest.mark.unit
def test_compile_excludes_base():
    """Test compile() does NOT include base layer."""
    context = ContextManager()
    context.add(ContextLayer(layer=Layer.BASE, content="Base content"))
    context.add(ContextLayer(layer=Layer.STATE, content="State content"))

    result = context.compile()

    assert "Base content" not in result
    assert "State content" in result


@pytest.mark.unit
def test_compile_excludes_override():
    """Test compile() does NOT include override layer."""
    context = ContextManager()
    context.add(ContextLayer(layer=Layer.OVERRIDE, content="Override content"))
    context.add(ContextLayer(layer=Layer.STATE, content="State content"))

    result = context.compile()

    assert "Override content" not in result
    assert "State content" in result


@pytest.mark.unit
def test_compile_includes_state():
    """Test compile() includes STATE layers."""
    context = ContextManager()
    context.add(ContextLayer(layer=Layer.STATE, content="State 1"))
    context.add(ContextLayer(layer=Layer.STATE, content="State 2"))

    result = context.compile()

    assert "State 1" in result
    assert "State 2" in result


@pytest.mark.unit
def test_compile_includes_derived():
    """Test compile() includes DERIVED layers."""
    context = ContextManager()
    context.add(ContextLayer(layer=Layer.DERIVED, content="Derived insight"))

    result = context.compile()

    assert "Derived insight" in result


@pytest.mark.unit
def test_compile_includes_proactive():
    """Test compile() includes PROACTIVE layers."""
    context = ContextManager()
    context.add(ContextLayer(layer=Layer.PROACTIVE, content="Proactive message"))

    result = context.compile()

    assert "Proactive message" in result


@pytest.mark.unit
def test_compile_all_layers_combined():
    """Test compile() combines STATE, DERIVED, PROACTIVE."""
    context = ContextManager()
    context.add(ContextLayer(layer=Layer.BASE, content="Base"))
    context.add(ContextLayer(layer=Layer.STATE, content="State"))
    context.add(ContextLayer(layer=Layer.OVERRIDE, content="Override"))
    context.add(ContextLayer(layer=Layer.DERIVED, content="Derived"))
    context.add(ContextLayer(layer=Layer.PROACTIVE, content="Proactive"))

    result = context.compile()

    # Should include STATE, DERIVED, PROACTIVE
    assert "State" in result
    assert "Derived" in result
    assert "Proactive" in result

    # Should NOT include BASE, OVERRIDE
    assert "Base" not in result
    assert "Override" not in result


@pytest.mark.unit
def test_compile_respects_order():
    """Test compile() sorts layers by order."""
    context = ContextManager()
    context.add(ContextLayer(layer=Layer.STATE, content="Third", order=30))
    context.add(ContextLayer(layer=Layer.STATE, content="First", order=10))
    context.add(ContextLayer(layer=Layer.STATE, content="Second", order=20))

    result = context.compile()

    # Check order
    assert result.index("First") < result.index("Second")
    assert result.index("Second") < result.index("Third")


@pytest.mark.unit
def test_compile_order_across_layer_types():
    """Test compile() sorts by order across different layer types."""
    context = ContextManager()
    context.add(ContextLayer(layer=Layer.STATE, content="State", order=20))
    context.add(ContextLayer(layer=Layer.DERIVED, content="Derived", order=10))
    context.add(ContextLayer(layer=Layer.PROACTIVE, content="Proactive", order=30))

    result = context.compile()

    # Derived (10) < State (20) < Proactive (30)
    assert result.index("Derived") < result.index("State")
    assert result.index("State") < result.index("Proactive")


@pytest.mark.unit
def test_compile_negative_order():
    """Test compile() handles negative order values."""
    context = ContextManager()
    context.add(ContextLayer(layer=Layer.STATE, content="Zero", order=0))
    context.add(ContextLayer(layer=Layer.STATE, content="Negative", order=-10))
    context.add(ContextLayer(layer=Layer.STATE, content="Positive", order=10))

    result = context.compile()

    assert result.index("Negative") < result.index("Zero")
    assert result.index("Zero") < result.index("Positive")


@pytest.mark.unit
def test_compile_joins_with_double_newline():
    """Test compile() joins layers with double newline."""
    context = ContextManager()
    context.add(ContextLayer(layer=Layer.STATE, content="First", order=1))
    context.add(ContextLayer(layer=Layer.STATE, content="Second", order=2))

    result = context.compile()

    assert result == "First\n\nSecond"


@pytest.mark.unit
def test_compile_ignores_timing():
    """Test compile() ignores inject_at timing (for HTTP)."""
    context = ContextManager()
    context.add(ContextLayer(
        layer=Layer.STATE,
        content="Turn start",
        inject_at=InjectTiming.TURN_START,
    ))
    context.add(ContextLayer(
        layer=Layer.DERIVED,
        content="After response",
        inject_at=InjectTiming.AFTER_RESPONSE,
    ))

    result = context.compile()

    # Both should be included regardless of timing
    assert "Turn start" in result
    assert "After response" in result


# =============================================================================
# COMPILE_FOR TESTS
# =============================================================================


@pytest.mark.unit
def test_compile_for_empty():
    """Test compile_for() with no matching layers."""
    context = ContextManager()

    result = context.compile_for(InjectTiming.TURN_START)

    assert result == ""


@pytest.mark.unit
def test_compile_for_filters_by_timing():
    """Test compile_for() filters by inject_at timing."""
    context = ContextManager()
    context.add(ContextLayer(
        layer=Layer.STATE,
        content="Turn start content",
        inject_at=InjectTiming.TURN_START,
    ))
    context.add(ContextLayer(
        layer=Layer.DERIVED,
        content="After response content",
        inject_at=InjectTiming.AFTER_RESPONSE,
    ))

    turn_start = context.compile_for(InjectTiming.TURN_START)
    after_response = context.compile_for(InjectTiming.AFTER_RESPONSE)

    assert "Turn start content" in turn_start
    assert "After response content" not in turn_start

    assert "After response content" in after_response
    assert "Turn start content" not in after_response


@pytest.mark.unit
def test_compile_for_session_start():
    """Test compile_for() with SESSION_START timing."""
    context = ContextManager()
    context.add(ContextLayer(
        layer=Layer.STATE,
        content="Session init",
        inject_at=InjectTiming.SESSION_START,
    ))
    context.add(ContextLayer(
        layer=Layer.STATE,
        content="Turn start",
        inject_at=InjectTiming.TURN_START,
    ))

    result = context.compile_for(InjectTiming.SESSION_START)

    assert "Session init" in result
    assert "Turn start" not in result


@pytest.mark.unit
def test_compile_for_asap():
    """Test compile_for() with ASAP timing."""
    context = ContextManager()
    context.add(ContextLayer(
        layer=Layer.PROACTIVE,
        content="Urgent message",
        inject_at=InjectTiming.ASAP,
    ))

    result = context.compile_for(InjectTiming.ASAP)

    assert "Urgent message" in result


@pytest.mark.unit
def test_compile_for_respects_order():
    """Test compile_for() respects order within timing."""
    context = ContextManager()
    context.add(ContextLayer(
        layer=Layer.STATE,
        content="Second",
        inject_at=InjectTiming.TURN_START,
        order=20,
    ))
    context.add(ContextLayer(
        layer=Layer.STATE,
        content="First",
        inject_at=InjectTiming.TURN_START,
        order=10,
    ))

    result = context.compile_for(InjectTiming.TURN_START)

    assert result.index("First") < result.index("Second")


@pytest.mark.unit
def test_compile_for_multiple_layer_types():
    """Test compile_for() includes multiple layer types with same timing."""
    context = ContextManager()
    context.add(ContextLayer(
        layer=Layer.STATE,
        content="State content",
        inject_at=InjectTiming.TURN_START,
    ))
    context.add(ContextLayer(
        layer=Layer.DERIVED,
        content="Derived content",
        inject_at=InjectTiming.TURN_START,
    ))

    result = context.compile_for(InjectTiming.TURN_START)

    assert "State content" in result
    assert "Derived content" in result


# =============================================================================
# GET_LAYERS_FOR TESTS
# =============================================================================


@pytest.mark.unit
def test_get_layers_for_empty():
    """Test get_layers_for() with no matching layers."""
    context = ContextManager()

    layers = context.get_layers_for(InjectTiming.TURN_START)

    assert layers == []


@pytest.mark.unit
def test_get_layers_for_returns_layer_objects():
    """Test get_layers_for() returns ContextLayer objects."""
    context = ContextManager()
    context.add(ContextLayer(
        layer=Layer.STATE,
        content="Test",
        inject_at=InjectTiming.TURN_START,
    ))

    layers = context.get_layers_for(InjectTiming.TURN_START)

    assert len(layers) == 1
    assert isinstance(layers[0], ContextLayer)
    assert layers[0].content == "Test"


@pytest.mark.unit
def test_get_layers_for_filters_by_timing():
    """Test get_layers_for() filters by timing."""
    context = ContextManager()
    context.add(ContextLayer(
        layer=Layer.STATE,
        content="Turn start",
        inject_at=InjectTiming.TURN_START,
    ))
    context.add(ContextLayer(
        layer=Layer.DERIVED,
        content="After response",
        inject_at=InjectTiming.AFTER_RESPONSE,
    ))

    turn_start_layers = context.get_layers_for(InjectTiming.TURN_START)
    after_response_layers = context.get_layers_for(InjectTiming.AFTER_RESPONSE)

    assert len(turn_start_layers) == 1
    assert turn_start_layers[0].content == "Turn start"

    assert len(after_response_layers) == 1
    assert after_response_layers[0].content == "After response"


@pytest.mark.unit
def test_get_layers_for_sorted_by_order():
    """Test get_layers_for() returns layers sorted by order."""
    context = ContextManager()
    context.add(ContextLayer(
        layer=Layer.STATE,
        content="Third",
        inject_at=InjectTiming.TURN_START,
        order=30,
    ))
    context.add(ContextLayer(
        layer=Layer.STATE,
        content="First",
        inject_at=InjectTiming.TURN_START,
        order=10,
    ))
    context.add(ContextLayer(
        layer=Layer.STATE,
        content="Second",
        inject_at=InjectTiming.TURN_START,
        order=20,
    ))

    layers = context.get_layers_for(InjectTiming.TURN_START)

    assert [l.content for l in layers] == ["First", "Second", "Third"]


# =============================================================================
# HAS_LAYERS_FOR TESTS
# =============================================================================


@pytest.mark.unit
def test_has_layers_for_true():
    """Test has_layers_for() returns True when layers exist."""
    context = ContextManager()
    context.add(ContextLayer(
        layer=Layer.STATE,
        content="Test",
        inject_at=InjectTiming.TURN_START,
    ))

    assert context.has_layers_for(InjectTiming.TURN_START) is True


@pytest.mark.unit
def test_has_layers_for_false():
    """Test has_layers_for() returns False when no layers exist."""
    context = ContextManager()

    assert context.has_layers_for(InjectTiming.TURN_START) is False


@pytest.mark.unit
def test_has_layers_for_wrong_timing():
    """Test has_layers_for() returns False for different timing."""
    context = ContextManager()
    context.add(ContextLayer(
        layer=Layer.STATE,
        content="Test",
        inject_at=InjectTiming.TURN_START,
    ))

    assert context.has_layers_for(InjectTiming.AFTER_RESPONSE) is False


# =============================================================================
# CLEAR TESTS
# =============================================================================


@pytest.mark.unit
def test_clear_state():
    """Test clear_state() removes all state layers."""
    context = ContextManager()
    context.add(ContextLayer(layer=Layer.STATE, content="State 1"))
    context.add(ContextLayer(layer=Layer.STATE, content="State 2"))
    context.add(ContextLayer(layer=Layer.DERIVED, content="Derived"))

    context.clear_state()

    assert context.layer_counts["state"] == 0
    assert context.layer_counts["derived"] == 1  # Not cleared
    assert "State" not in context.compile()
    assert "Derived" in context.compile()


@pytest.mark.unit
def test_clear_override():
    """Test clear_override() removes override."""
    context = ContextManager()
    context.add(ContextLayer(layer=Layer.BASE, content="Base"))
    context.add(ContextLayer(layer=Layer.OVERRIDE, content="Override"))

    assert context.get_base() == "Override"

    context.clear_override()

    assert context.get_base() == "Base"
    assert context.layer_counts["override"] == 0


@pytest.mark.unit
def test_clear_derived():
    """Test clear_derived() removes all derived layers."""
    context = ContextManager()
    context.add(ContextLayer(layer=Layer.DERIVED, content="Derived 1"))
    context.add(ContextLayer(layer=Layer.DERIVED, content="Derived 2"))
    context.add(ContextLayer(layer=Layer.STATE, content="State"))

    context.clear_derived()

    assert context.layer_counts["derived"] == 0
    assert context.layer_counts["state"] == 1  # Not cleared


@pytest.mark.unit
def test_clear_proactive():
    """Test clear_proactive() removes all proactive layers."""
    context = ContextManager()
    context.add(ContextLayer(layer=Layer.PROACTIVE, content="Proactive 1"))
    context.add(ContextLayer(layer=Layer.PROACTIVE, content="Proactive 2"))

    context.clear_proactive()

    assert context.layer_counts["proactive"] == 0


@pytest.mark.unit
def test_clear_all():
    """Test clear_all() removes all layers except base."""
    context = ContextManager()
    context.add(ContextLayer(layer=Layer.BASE, content="Base"))
    context.add(ContextLayer(layer=Layer.STATE, content="State"))
    context.add(ContextLayer(layer=Layer.OVERRIDE, content="Override"))
    context.add(ContextLayer(layer=Layer.DERIVED, content="Derived"))
    context.add(ContextLayer(layer=Layer.PROACTIVE, content="Proactive"))

    context.clear_all()

    assert context.layer_counts == {
        "base": 1,  # Base NOT cleared
        "state": 0,
        "override": 0,
        "derived": 0,
        "proactive": 0,
    }


# =============================================================================
# HTTP PATTERN TESTS
# =============================================================================


@pytest.mark.unit
def test_http_pattern():
    """Test typical HTTP usage pattern."""
    context = ContextManager()

    # Add layers like HTTP request would
    context.add(ContextLayer(layer=Layer.BASE, content="System prompt"))
    context.add(ContextLayer(layer=Layer.STATE, content="Room context", order=10))
    context.add(ContextLayer(layer=Layer.STATE, content="Visual context", order=20))

    # HTTP: get_base() for system message, compile() for body
    system_prompt = context.get_base()
    compiled = context.compile()

    assert system_prompt == "System prompt"
    assert "Room context" in compiled
    assert "Visual context" in compiled
    assert "System prompt" not in compiled


# =============================================================================
# S2S PATTERN TESTS
# =============================================================================


@pytest.mark.unit
def test_s2s_pattern_turn_start():
    """Test typical S2S TURN_START injection pattern."""
    context = ContextManager()

    # Add layers with timing
    context.add(ContextLayer(
        layer=Layer.BASE,
        content="System prompt",
        inject_at=InjectTiming.SESSION_START,
    ))
    context.add(ContextLayer(
        layer=Layer.STATE,
        content="Room context",
        inject_at=InjectTiming.TURN_START,
    ))

    # S2S: get_base() at session start
    system_prompt = context.get_base()

    # S2S: compile_for() at turn start
    turn_context = context.compile_for(InjectTiming.TURN_START)

    assert system_prompt == "System prompt"
    assert turn_context == "Room context"


@pytest.mark.unit
def test_s2s_pattern_after_response():
    """Test typical S2S AFTER_RESPONSE injection pattern."""
    context = ContextManager()

    context.add(ContextLayer(
        layer=Layer.DERIVED,
        content="User insight",
        inject_at=InjectTiming.AFTER_RESPONSE,
    ))

    # Nothing at TURN_START
    assert context.compile_for(InjectTiming.TURN_START) == ""

    # Insight at AFTER_RESPONSE
    assert context.compile_for(InjectTiming.AFTER_RESPONSE) == "User insight"


@pytest.mark.unit
def test_s2s_proactive_pattern():
    """Test typical S2S proactive trigger pattern."""
    context = ContextManager()

    # Add proactive content
    context.add(ContextLayer(
        layer=Layer.PROACTIVE,
        content="Meeting reminder",
        inject_at=InjectTiming.ASAP,
    ))

    # Get ASAP content for immediate injection
    proactive_text = context.compile_for(InjectTiming.ASAP)

    assert proactive_text == "Meeting reminder"

    # Clear after use
    context.clear_proactive()
    assert context.compile_for(InjectTiming.ASAP) == ""


# =============================================================================
# EDGE CASES
# =============================================================================


@pytest.mark.unit
def test_empty_content_layers():
    """Test layers with empty content."""
    context = ContextManager()
    context.add(ContextLayer(layer=Layer.STATE, content=""))
    context.add(ContextLayer(layer=Layer.STATE, content="Not empty"))

    result = context.compile()

    # Empty content should be filtered out
    assert result == "Not empty"


@pytest.mark.unit
def test_many_layers():
    """Test manager with many layers."""
    context = ContextManager()

    for i in range(100):
        context.add(ContextLayer(
            layer=Layer.STATE,
            content=f"Layer {i}",
            order=i,
        ))

    assert context.layer_counts["state"] == 100

    result = context.compile()
    assert "Layer 0" in result
    assert "Layer 99" in result


@pytest.mark.unit
def test_layer_counts_property():
    """Test layer_counts property returns correct counts."""
    context = ContextManager()
    context.add(ContextLayer(layer=Layer.BASE, content="B"))
    context.add(ContextLayer(layer=Layer.STATE, content="S1"))
    context.add(ContextLayer(layer=Layer.STATE, content="S2"))
    context.add(ContextLayer(layer=Layer.DERIVED, content="D"))

    counts = context.layer_counts

    assert counts["base"] == 1
    assert counts["state"] == 2
    assert counts["override"] == 0
    assert counts["derived"] == 1
    assert counts["proactive"] == 0
