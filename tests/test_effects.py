"""Unit tests for effects validation and serialization."""


import pytest

from huesignal.effects.base import (
    EffectOptions,
    validate_brightness,
)
from huesignal.effects.colors import parse_color, rgb_to_xy


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
