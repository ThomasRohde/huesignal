"""Rainbow effect implementation."""

import asyncio

from aiohue.v2 import HueBridgeV2

from huesignal.effects.base import Effect, EffectOptions, register_effect
from huesignal.effects.colors import rgb_to_xy

# Rainbow colors in RGB
RAINBOW_COLORS = [
    (255, 0, 0),      # Red
    (255, 127, 0),    # Orange
    (255, 255, 0),    # Yellow
    (0, 255, 0),      # Green
    (0, 0, 255),      # Blue
    (75, 0, 130),     # Indigo
    (148, 0, 211),    # Violet
]


@register_effect
class Rainbow(Effect):
    """Rainbow effect - color cycle for color lights, brightness wave for others."""

    name = "rainbow"
    description = "Cycle through rainbow colors"

    def __init__(
        self,
        bridge: HueBridgeV2,
        light_ids: list[str],
        options: EffectOptions,
        step_ms: int = 100,
    ):
        """Initialize rainbow effect.

        Args:
            bridge: HueBridgeV2 instance
            light_ids: List of light IDs to apply effect to
            options: EffectOptions for the effect
            step_ms: Time between color steps in milliseconds (default 100)
        """
        super().__init__(bridge, light_ids, options)
        self.step_ms = step_ms

    async def _apply_effect(self) -> None:
        """Apply the rainbow effect to all lights.

        For color lights: cycles through rainbow colors.
        For non-color lights: performs brightness wave.
        """
        # Classify lights by color support
        color_lights = []
        non_color_lights = []

        for light_id in self.light_ids:
            light = self.bridge.lights.get(light_id)
            if light:
                # Check if light supports color
                if light.color:
                    color_lights.append(light_id)
                else:
                    non_color_lights.append(light_id)

        # Calculate duration and number of steps
        duration_ms = self.options.duration_ms
        num_steps = max(1, duration_ms // self.step_ms)
        step_duration = duration_ms / num_steps

        # Apply color cycle to color lights
        if color_lights:
            await self._apply_color_cycle(color_lights, num_steps, step_duration)

        # Apply brightness wave to non-color lights
        if non_color_lights:
            await self._apply_brightness_wave(non_color_lights, num_steps, step_duration)

    async def _apply_color_cycle(
        self, light_ids: list[str], num_steps: int, step_duration: float
    ) -> None:
        """Cycle colors on color-capable lights.

        Args:
            light_ids: List of color light IDs
            num_steps: Number of steps to cycle through
            step_duration: Duration of each step in milliseconds
        """
        colors_count = len(RAINBOW_COLORS)

        for step in range(num_steps):
            # Calculate which color to use
            color_index = (step * colors_count) // num_steps
            color_index = color_index % colors_count
            rgb = RAINBOW_COLORS[color_index]
            xy = rgb_to_xy(*rgb)

            # Apply color to all color lights
            for light_id in light_ids:
                light = self.bridge.lights.get(light_id)
                if not light:
                    continue

                try:
                    await light.set_state(
                        color=xy,
                        transition_time=int(step_duration),
                    )
                except Exception:
                    pass

            # Wait before next step
            await asyncio.sleep(step_duration / 1000.0)

    async def _apply_brightness_wave(
        self, light_ids: list[str], num_steps: int, step_duration: float
    ) -> None:
        """Create brightness wave on non-color lights.

        Args:
            light_ids: List of non-color light IDs
            num_steps: Number of steps to cycle through
            step_duration: Duration of each step in milliseconds
        """
        # Define brightness wave: ramp up then down
        min_brightness = 80
        max_brightness = 254

        for step in range(num_steps):
            # Calculate brightness (wave pattern: 0->1->0)
            progress = step / max(1, num_steps - 1)
            # Use sine-like wave: goes 0->1->0
            if progress <= 0.5:
                wave_value = progress * 2
            else:
                wave_value = 2 - progress * 2

            brightness = int(min_brightness + (max_brightness - min_brightness) * wave_value)

            # Apply brightness to all non-color lights
            for light_id in light_ids:
                light = self.bridge.lights.get(light_id)
                if not light:
                    continue

                try:
                    await light.set_state(
                        brightness=brightness,
                        transition_time=int(step_duration),
                    )
                except Exception:
                    pass

            # Wait before next step
            await asyncio.sleep(step_duration / 1000.0)
