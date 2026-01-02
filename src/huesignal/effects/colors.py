"""Color parsing and conversion utilities for effects."""

import re

# Standard CSS/X11 color names mapped to RGB
COLOR_NAMES = {
    "red": (255, 0, 0),
    "green": (0, 128, 0),
    "blue": (0, 0, 255),
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "gray": (128, 128, 128),
    "grey": (128, 128, 128),
    "orange": (255, 165, 0),
    "purple": (128, 0, 128),
    "pink": (255, 192, 203),
    "brown": (165, 42, 42),
}


def parse_color(color_str: str) -> tuple[int, int, int]:
    """Parse color string to RGB tuple.

    Supports:
    - Color names (e.g., 'red', 'blue')
    - Hex color codes (e.g., '#FF0000', 'FF0000')

    Args:
        color_str: Color specification string

    Returns:
        RGB tuple (r, g, b) with values 0-255

    Raises:
        ValueError: If color string is invalid
    """
    color_str = color_str.strip().lower()

    # Try color name first
    if color_str in COLOR_NAMES:
        return COLOR_NAMES[color_str]

    # Try hex color
    # Remove # if present
    hex_str = color_str.lstrip("#")

    # Validate hex format
    if not re.match(r"^[0-9a-f]{6}$", hex_str):
        raise ValueError(f"Invalid color: {color_str}. Use color name (e.g., 'red') or hex code (e.g., '#FF0000')")

    # Convert hex to RGB
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)

    return (r, g, b)


def rgb_to_xy(r: int, g: int, b: int) -> tuple[float, float]:
    """Convert RGB to Philips Hue xy color space.

    Args:
        r: Red value (0-255)
        g: Green value (0-255)
        b: Blue value (0-255)

    Returns:
        XY tuple (x, y) in Hue color space
    """
    # Normalize RGB to 0.0-1.0
    r_norm = r / 255.0
    g_norm = g / 255.0
    b_norm = b / 255.0

    # Apply gamma correction
    def gamma_correct(value: float) -> float:
        if value <= 0.04045:
            return value / 12.92
        return ((value + 0.055) / 1.055) ** 2.4

    r_gamma = gamma_correct(r_norm)
    g_gamma = gamma_correct(g_norm)
    b_gamma = gamma_correct(b_norm)

    # Convert to XYZ
    x = r_gamma * 0.664511 + g_gamma * 0.154324 + b_gamma * 0.162028
    y = r_gamma * 0.283881 + g_gamma * 0.668433 + b_gamma * 0.047685
    z = r_gamma * 0.000088 + g_gamma * 0.072310 + b_gamma * 0.986039

    # Prevent division by zero
    if (x + y + z) == 0:
        return (0.0, 0.0)

    # Convert XYZ to xy
    xy_x = x / (x + y + z)
    xy_y = y / (x + y + z)

    # Clamp to valid Hue color space
    xy_x = max(0.0, min(1.0, xy_x))
    xy_y = max(0.0, min(1.0, xy_y))

    return (xy_x, xy_y)


def list_color_names() -> list[str]:
    """Get list of available color names.

    Returns:
        Sorted list of color names
    """
    return sorted(COLOR_NAMES.keys())
