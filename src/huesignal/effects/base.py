"""Base class and utilities for effect implementations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from aiohue.v2 import HueBridgeV2

from huesignal.effects.colors import parse_color, rgb_to_xy
from huesignal.state import StateSnapshot


@dataclass
class EffectOptions:
    """Standard options for all effects."""

    duration_ms: int = 500  # Transition duration in milliseconds
    brightness: int | None = None  # 1-254
    color: str | None = None  # Color name or hex code
    restore: bool = True  # Whether to restore state after effect


def validate_brightness(value: int) -> None:
    """Validate brightness value.

    Args:
        value: Brightness value to validate

    Raises:
        ValueError: If brightness is not in range 1-254
    """
    if value < 1 or value > 254:
        raise ValueError(f"Brightness must be between 1 and 254, got {value}")


class Effect(ABC):
    """Base class for all effects."""

    name: str = "base"
    description: str = "Base effect class"

    def __init__(
        self,
        bridge: HueBridgeV2,
        light_ids: list[str],
        options: EffectOptions,
    ):
        """Initialize effect.

        Args:
            bridge: HueBridgeV2 instance
            light_ids: List of light IDs to apply effect to
            options: EffectOptions for the effect
        """
        self.bridge = bridge
        self.light_ids = light_ids
        self.options = options
        self.initial_state: StateSnapshot | None = None

        # Validate options
        if self.options.brightness is not None:
            validate_brightness(self.options.brightness)

    async def apply(self) -> None:
        """Apply the effect to the lights.

        This is the main entry point that handles:
        1. Capturing initial state if restore is enabled
        2. Applying the effect
        3. Optionally restoring state after effect completes
        """
        # Capture initial state if restore is enabled
        if self.options.restore:
            from huesignal.state import capture_state

            self.initial_state = await capture_state(self.bridge)

        try:
            # Apply the effect
            await self._apply_effect()
        finally:
            # Restore state if needed
            if self.options.restore and self.initial_state:
                from huesignal.state import restore_state

                await restore_state(self.bridge, self.initial_state)

    @abstractmethod
    async def _apply_effect(self) -> None:
        """Apply the effect implementation.

        Subclasses must implement this method.
        """
        pass

    async def _set_light_state(
        self,
        light_id: str,
        on: bool = True,
        brightness: int | None = None,
        color: str | None = None,
        transition_time: int | None = None,
    ) -> None:
        """Set light state with common parameters.

        Args:
            light_id: Light ID to modify
            on: Whether light should be on
            brightness: Brightness 1-254
            color: Color name or hex code
            transition_time: Transition time in milliseconds
        """
        if light_id not in self.bridge.lights:
            return

        light = self.bridge.lights[light_id]

        # Prepare state update
        state_update = {"on": on}

        # Add brightness if specified
        if brightness is not None:
            validate_brightness(brightness)
            state_update["brightness"] = brightness
        elif self.options.brightness is not None:
            state_update["brightness"] = self.options.brightness

        # Add color if specified
        color_to_use = color or self.options.color
        if color_to_use:
            try:
                rgb = parse_color(color_to_use)
                xy = rgb_to_xy(*rgb)
                state_update["color_xy"] = xy
            except ValueError:
                # Skip color if invalid
                pass

        # Add transition time
        if transition_time is not None:
            state_update["transition_time"] = transition_time
        else:
            state_update["transition_time"] = self.options.duration_ms

        # Apply state update
        try:
            await self.bridge.lights.set_state(light_id, **state_update)
        except Exception as e:
            # Log error but continue with other lights
            import logging

            logging.debug(f"Failed to set light state for {light_id}: {e}")


# Registry of available effects
EFFECT_REGISTRY: dict[str, type[Effect]] = {}


def register_effect(effect_class: type[Effect]) -> type[Effect]:
    """Register an effect class.

    Args:
        effect_class: Effect class to register

    Returns:
        The effect class (unchanged)
    """
    EFFECT_REGISTRY[effect_class.name] = effect_class
    return effect_class


def get_effect_class(name: str) -> type[Effect] | None:
    """Get effect class by name.

    Args:
        name: Effect name

    Returns:
        Effect class or None if not found
    """
    return EFFECT_REGISTRY.get(name)


def list_effects() -> list[tuple[str, str]]:
    """Get list of available effects.

    Returns:
        List of (name, description) tuples
    """
    return [(cls.name, cls.description) for cls in EFFECT_REGISTRY.values()]
