"""
Test context types (enums and dataclasses).

This module tests the fundamental types used in the LDCI context system:
- Layer enum
- InjectTiming enum
- Authority enum
- Stability enum
- CompileOptions dataclass
"""

import pytest

from chatforge.services.context.types import (
    Authority,
    CompileOptions,
    InjectTiming,
    Layer,
    Stability,
)


# =============================================================================
# LAYER ENUM TESTS
# =============================================================================


@pytest.mark.unit
def test_layer_enum_values():
    """Test Layer enum has all expected values."""
    assert Layer.BASE.value == "base"
    assert Layer.STATE.value == "state"
    assert Layer.OVERRIDE.value == "override"
    assert Layer.DERIVED.value == "derived"
    assert Layer.PROACTIVE.value == "proactive"


@pytest.mark.unit
def test_layer_enum_count():
    """Test Layer enum has exactly 5 layers."""
    assert len(Layer) == 5


@pytest.mark.unit
def test_layer_enum_from_string():
    """Test creating Layer from string value."""
    assert Layer("base") == Layer.BASE
    assert Layer("state") == Layer.STATE
    assert Layer("override") == Layer.OVERRIDE
    assert Layer("derived") == Layer.DERIVED
    assert Layer("proactive") == Layer.PROACTIVE


@pytest.mark.unit
def test_layer_enum_invalid_value():
    """Test that invalid value raises ValueError."""
    with pytest.raises(ValueError):
        Layer("invalid")


# =============================================================================
# INJECT_TIMING ENUM TESTS
# =============================================================================


@pytest.mark.unit
def test_inject_timing_enum_values():
    """Test InjectTiming enum has all expected values."""
    assert InjectTiming.SESSION_START.value == "session_start"
    assert InjectTiming.TURN_START.value == "turn_start"
    assert InjectTiming.AFTER_RESPONSE.value == "after_response"
    assert InjectTiming.SCHEDULED.value == "scheduled"
    assert InjectTiming.ASAP.value == "asap"
    assert InjectTiming.ON_EVENT.value == "on_event"


@pytest.mark.unit
def test_inject_timing_enum_count():
    """Test InjectTiming enum has exactly 6 timing options."""
    assert len(InjectTiming) == 6


@pytest.mark.unit
def test_inject_timing_from_string():
    """Test creating InjectTiming from string value."""
    assert InjectTiming("session_start") == InjectTiming.SESSION_START
    assert InjectTiming("turn_start") == InjectTiming.TURN_START
    assert InjectTiming("after_response") == InjectTiming.AFTER_RESPONSE


# =============================================================================
# AUTHORITY ENUM TESTS
# =============================================================================


@pytest.mark.unit
def test_authority_enum_values():
    """Test Authority enum has all expected values."""
    assert Authority.DIRECTIVE.value == "directive"
    assert Authority.INFORMATIVE.value == "informative"
    assert Authority.SUGGESTIVE.value == "suggestive"


@pytest.mark.unit
def test_authority_enum_count():
    """Test Authority enum has exactly 3 options."""
    assert len(Authority) == 3


# =============================================================================
# STABILITY ENUM TESTS
# =============================================================================


@pytest.mark.unit
def test_stability_enum_values():
    """Test Stability enum has all expected values."""
    assert Stability.STATIC.value == "static"
    assert Stability.SESSION.value == "session"
    assert Stability.TURN.value == "turn"
    assert Stability.EVENT.value == "event"


@pytest.mark.unit
def test_stability_enum_count():
    """Test Stability enum has exactly 4 options."""
    assert len(Stability) == 4


# =============================================================================
# COMPILE_OPTIONS TESTS
# =============================================================================


@pytest.mark.unit
def test_compile_options_defaults():
    """Test CompileOptions default values."""
    options = CompileOptions()

    assert options.verbose is True
    assert options.custom == {}


@pytest.mark.unit
def test_compile_options_custom_values():
    """Test CompileOptions with custom values."""
    options = CompileOptions(verbose=False, custom={"key": "value"})

    assert options.verbose is False
    assert options.custom == {"key": "value"}


@pytest.mark.unit
def test_compile_options_get_custom():
    """Test CompileOptions.get() method for custom flags."""
    options = CompileOptions(custom={"audio_tags": True, "debug": False})

    assert options.get("audio_tags") is True
    assert options.get("debug") is False
    assert options.get("non_existent") is None
    assert options.get("non_existent", "default") == "default"


@pytest.mark.unit
def test_compile_options_get_missing_key():
    """Test CompileOptions.get() with missing key."""
    options = CompileOptions()

    assert options.get("missing") is None
    assert options.get("missing", "fallback") == "fallback"
