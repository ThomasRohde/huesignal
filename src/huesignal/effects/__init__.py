"""Effect system for controlling Hue lights."""

from huesignal.effects.base import (
    Effect,
    EffectOptions,
    get_effect_class,
    list_effects,
    register_effect,
    validate_brightness,
)
from huesignal.effects.colors import list_color_names, parse_color, rgb_to_xy
from huesignal.effects.pulse import Pulse
from huesignal.effects.rainbow import Rainbow
from huesignal.effects.breathe import BreatheEffect
from huesignal.effects.blink import Blink

__all__ = [
    "Effect",
    "EffectOptions",
    "get_effect_class",
    "list_effects",
    "register_effect",
    "validate_brightness",
    "parse_color",
    "rgb_to_xy",
    "list_color_names",
    "Pulse",
    "Rainbow",
    "BreatheEffect",
    "Blink",
]
