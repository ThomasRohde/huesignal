"""Unit tests for effects validation and serialization."""

import pytest

from huesignal.effects.base import (
    EffectOptions,
    EffectParam,
    validate_brightness,
)
from huesignal.effects.colors import parse_color, rgb_to_xy
from huesignal.effects.pulse import Pulse


class TestEffectParam:
    """Tests for EffectParam dataclass."""

    def test_effect_param_creation(self):
        """Test creating an EffectParam."""
        param = EffectParam(name="count", type=int, default=1, description="Number of cycles")
        assert param.name == "count"
        assert param.type is int
        assert param.default == 1
        assert param.description == "Number of cycles"

    def test_effect_param_with_string_type(self):
        """Test EffectParam with string type."""
        param = EffectParam(name="color", type=str, default="red", description="Color to use")
        assert param.type is str
        assert param.default == "red"

    def test_effect_param_with_none_default(self):
        """Test EffectParam with None as default."""
        param = EffectParam(name="optional_value", type=int, default=None, description="Optional parameter")
        assert param.default is None


class TestEffectParamsIntrospection:
    """Tests for effect parameter introspection."""

    def test_pulse_has_params(self):
        """Test that Pulse effect declares params."""
        assert hasattr(Pulse, "params")
        assert isinstance(Pulse.params, list)
        assert len(Pulse.params) > 0

    def test_pulse_params_structure(self):
        """Test Pulse params have correct structure."""
        params = Pulse.params

        # Check we have count and interval_ms
        param_names = [p.name for p in params]
        assert "count" in param_names
        assert "interval_ms" in param_names

    def test_pulse_count_param(self):
        """Test Pulse count parameter definition."""
        params = Pulse.params
        count_param = next(p for p in params if p.name == "count")

        assert count_param.type is int
        assert count_param.default == 1
        assert "cycle" in count_param.description.lower()

    def test_pulse_interval_param(self):
        """Test Pulse interval_ms parameter definition."""
        params = Pulse.params
        interval_param = next(p for p in params if p.name == "interval_ms")

        assert interval_param.type is int
        assert interval_param.default == 500
        assert "millisecond" in interval_param.description.lower()

    def test_get_params_classmethod(self):
        """Test get_params() class method works without instantiation."""
        params = Pulse.get_params()

        assert isinstance(params, list)
        assert len(params) > 0
        assert all(isinstance(p, EffectParam) for p in params)

    def test_get_params_returns_class_params(self):
        """Test get_params() returns the class-level params list."""
        params = Pulse.get_params()
        assert params is Pulse.params


class TestToPrimitives:
    """Tests for to_primitives() effect conversion."""

    def test_pulse_to_primitives_returns_list(self):
        """Test Pulse.to_primitives() returns a list."""
        from unittest.mock import MagicMock

        mock_bridge = MagicMock()
        options = EffectOptions()
        pulse = Pulse(bridge=mock_bridge, light_ids=["light-1"], options=options)

        primitives = pulse.to_primitives()

        assert isinstance(primitives, list)
        assert len(primitives) > 0

    def test_pulse_to_primitives_count_one(self):
        """Test Pulse with count=1 generates correct number of primitives."""
        from unittest.mock import MagicMock

        mock_bridge = MagicMock()
        options = EffectOptions()
        pulse = Pulse(bridge=mock_bridge, light_ids=["light-1"], options=options, count=1)

        primitives = pulse.to_primitives()

        # One cycle = 2 SetState + 2 Wait = 4 primitives
        assert len(primitives) == 4

    def test_pulse_to_primitives_count_three(self):
        """Test Pulse with count=3 generates correct number of primitives."""
        from unittest.mock import MagicMock

        mock_bridge = MagicMock()
        options = EffectOptions()
        pulse = Pulse(bridge=mock_bridge, light_ids=["light-1"], options=options, count=3)

        primitives = pulse.to_primitives()

        # Three cycles = 3 * (2 SetState + 2 Wait) = 12 primitives
        assert len(primitives) == 12

    def test_pulse_to_primitives_types(self):
        """Test Pulse to_primitives returns SetState and Wait primitives."""
        from unittest.mock import MagicMock

        from huesignal.effects.primitives import SetState, Wait

        mock_bridge = MagicMock()
        options = EffectOptions()
        pulse = Pulse(bridge=mock_bridge, light_ids=["light-1"], options=options, count=1)

        primitives = pulse.to_primitives()

        # Check primitive types
        assert isinstance(primitives[0], SetState)  # Pulse down
        assert isinstance(primitives[1], Wait)  # Wait
        assert isinstance(primitives[2], SetState)  # Pulse up
        assert isinstance(primitives[3], Wait)  # Wait

    def test_pulse_to_primitives_brightness_sequence(self):
        """Test Pulse to_primitives creates correct brightness sequence."""
        from unittest.mock import MagicMock

        mock_bridge = MagicMock()
        options = EffectOptions(brightness=200)
        pulse = Pulse(bridge=mock_bridge, light_ids=["light-1"], options=options, count=1)

        primitives = pulse.to_primitives()

        # First SetState should dim to 1
        assert primitives[0].brightness == 1
        # Third primitive (second SetState) should go to target brightness
        assert primitives[2].brightness == 200

    def test_pulse_to_primitives_with_color(self):
        """Test Pulse to_primitives includes color."""
        from unittest.mock import MagicMock

        from huesignal.effects.primitives import SetState

        mock_bridge = MagicMock()
        options = EffectOptions(color="blue")
        pulse = Pulse(bridge=mock_bridge, light_ids=["light-1"], options=options)

        primitives = pulse.to_primitives()

        # Both SetState primitives should have the color
        set_states = [p for p in primitives if isinstance(p, SetState)]
        assert all(s.color == "blue" for s in set_states)

    def test_pulse_to_primitives_custom_interval(self):
        """Test Pulse to_primitives respects custom interval_ms."""
        from unittest.mock import MagicMock

        from huesignal.effects.primitives import SetState, Wait

        mock_bridge = MagicMock()
        options = EffectOptions()
        pulse = Pulse(bridge=mock_bridge, light_ids=["light-1"], options=options, interval_ms=1000)

        primitives = pulse.to_primitives()

        # SetState primitives should use the interval
        set_states = [p for p in primitives if isinstance(p, SetState)]
        assert all(s.transition_ms == 1000 for s in set_states)

        # Wait primitives should be interval + buffer
        waits = [p for p in primitives if isinstance(p, Wait)]
        assert all(w.duration_ms == 1100 for w in waits)


class TestValidateBrightness:
    """Tests for brightness validation."""

    def test_valid_brightness_minimum(self):
        """Test valid minimum brightness."""
        validate_brightness(1)  # Should not raise

    def test_valid_brightness_maximum(self):
        """Test valid maximum brightness."""
        validate_brightness(254)  # Should not raise

    def test_valid_brightness_midrange(self):
        """Test valid midrange brightness."""
        validate_brightness(127)  # Should not raise

    def test_invalid_brightness_zero(self):
        """Test brightness value of 0 raises ValueError."""
        with pytest.raises(ValueError, match="Brightness must be between 1 and 254"):
            validate_brightness(0)

    def test_invalid_brightness_negative(self):
        """Test negative brightness raises ValueError."""
        with pytest.raises(ValueError, match="Brightness must be between 1 and 254"):
            validate_brightness(-1)

    def test_invalid_brightness_too_high(self):
        """Test brightness above 254 raises ValueError."""
        with pytest.raises(ValueError, match="Brightness must be between 1 and 254"):
            validate_brightness(255)

    def test_invalid_brightness_way_too_high(self):
        """Test very high brightness raises ValueError."""
        with pytest.raises(ValueError, match="Brightness must be between 1 and 254"):
            validate_brightness(999)


class TestEffectOptions:
    """Tests for EffectOptions dataclass."""

    def test_effect_options_defaults(self):
        """Test EffectOptions with default values."""
        options = EffectOptions()
        assert options.duration_ms == 500
        assert options.brightness is None
        assert options.color is None
        assert options.restore is True

    def test_effect_options_custom_values(self):
        """Test EffectOptions with custom values."""
        options = EffectOptions(
            duration_ms=2000,
            brightness=200,
            color="red",
            restore=False,
        )
        assert options.duration_ms == 2000
        assert options.brightness == 200
        assert options.color == "red"
        assert options.restore is False

    def test_effect_options_brightness_not_validated_in_constructor(self):
        """Test EffectOptions does not validate brightness in constructor (validation happens in Effect)."""
        # EffectOptions is just a dataclass and doesn't validate brightness
        # Validation happens when creating an Effect instance
        options = EffectOptions(brightness=0)
        assert options.brightness == 0

    def test_effect_options_brightness_valid(self):
        """Test EffectOptions accepts valid brightness."""
        options = EffectOptions(brightness=150)
        assert options.brightness == 150


class TestParseColor:
    """Tests for color parsing."""

    def test_parse_color_by_name_red(self):
        """Test parsing color by name."""
        rgb = parse_color("red")
        assert rgb == (255, 0, 0)

    def test_parse_color_by_name_green(self):
        """Test parsing green color by name."""
        rgb = parse_color("green")
        assert rgb == (0, 128, 0)

    def test_parse_color_by_name_blue(self):
        """Test parsing blue color by name."""
        rgb = parse_color("blue")
        assert rgb == (0, 0, 255)

    def test_parse_color_case_insensitive(self):
        """Test color name parsing is case insensitive."""
        rgb1 = parse_color("red")
        rgb2 = parse_color("RED")
        rgb3 = parse_color("Red")
        assert rgb1 == rgb2 == rgb3

    def test_parse_color_hex_with_hash(self):
        """Test parsing hex color with # prefix."""
        rgb = parse_color("#FF0000")
        assert rgb == (255, 0, 0)

    def test_parse_color_hex_without_hash(self):
        """Test parsing hex color without # prefix."""
        rgb = parse_color("FF0000")
        assert rgb == (255, 0, 0)

    def test_parse_color_hex_lowercase(self):
        """Test parsing hex color with lowercase."""
        rgb = parse_color("#ff00ff")
        assert rgb == (255, 0, 255)

    def test_parse_color_invalid_hex(self):
        """Test invalid hex color raises ValueError."""
        with pytest.raises(ValueError):
            parse_color("#GGGGGG")

    def test_parse_color_invalid_format(self):
        """Test invalid color format raises ValueError."""
        with pytest.raises(ValueError):
            parse_color("notacolor")

    def test_parse_color_whitespace(self):
        """Test parsing color with whitespace."""
        rgb = parse_color("  red  ")
        assert rgb == (255, 0, 0)


class TestRgbToXy:
    """Tests for RGB to XY color space conversion."""

    def test_rgb_to_xy_red(self):
        """Test converting red to XY."""
        x, y = rgb_to_xy(255, 0, 0)
        assert isinstance(x, float)
        assert isinstance(y, float)
        assert 0 <= x <= 1
        assert 0 <= y <= 1

    def test_rgb_to_xy_green(self):
        """Test converting green to XY."""
        x, y = rgb_to_xy(0, 255, 0)
        assert isinstance(x, float)
        assert isinstance(y, float)
        assert 0 <= x <= 1
        assert 0 <= y <= 1

    def test_rgb_to_xy_blue(self):
        """Test converting blue to XY."""
        x, y = rgb_to_xy(0, 0, 255)
        assert isinstance(x, float)
        assert isinstance(y, float)
        assert 0 <= x <= 1
        assert 0 <= y <= 1

    def test_rgb_to_xy_white(self):
        """Test converting white to XY."""
        x, y = rgb_to_xy(255, 255, 255)
        assert isinstance(x, float)
        assert isinstance(y, float)
        assert 0 <= x <= 1
        assert 0 <= y <= 1

    def test_rgb_to_xy_black(self):
        """Test converting black (0,0,0) to XY."""
        x, y = rgb_to_xy(0, 0, 0)
        # Black should map to 0,0
        assert x == 0.0
        assert y == 0.0

    def test_rgb_to_xy_clamped(self):
        """Test that XY values are clamped to 0-1 range."""
        # Test with various RGB values
        for r in [0, 127, 255]:
            for g in [0, 127, 255]:
                for b in [0, 127, 255]:
                    x, y = rgb_to_xy(r, g, b)
                    assert 0.0 <= x <= 1.0, f"X out of range for RGB({r},{g},{b}): {x}"
                    assert 0.0 <= y <= 1.0, f"Y out of range for RGB({r},{g},{b}): {y}"
