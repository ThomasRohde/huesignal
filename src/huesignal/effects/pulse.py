"""Pulse effect implementation."""

import asyncio

from aiohue.v2 import HueBridgeV2

from huesignal.effects.base import Effect, EffectOptions, register_effect


@register_effect
class Pulse(Effect):
    """Pulse effect - smooth brightness or color changes."""

    name = "pulse"
    description = "Pulse brightness or color changes"

    def __init__(
        self,
        bridge: HueBridgeV2,
        light_ids: list[str],
        options: EffectOptions,
        count: int = 1,
        interval_ms: int = 500,
    ):
        """Initialize pulse effect.

        Args:
            bridge: HueBridgeV2 instance
            light_ids: List of light IDs to apply effect to
            options: EffectOptions for the effect
            count: Number of pulse cycles (default 1)
            interval_ms: Time for each pulse transition in milliseconds (default 500)
        """
        super().__init__(bridge, light_ids, options)
        self.count = count
        self.interval_ms = interval_ms

    async def _apply_effect(self) -> None:
        """Apply the pulse effect to all lights.

        Pulses from current state to target brightness/color and back,
        repeated count times.
        """
        # Capture original state for each light
        original_states: dict[str, dict] = {}
        for light_id in self.light_ids:
            light = self.bridge.lights.get(light_id)
            if light:
                # Store original brightness
                brightness = light.dimming.brightness if light.dimming else 0
                original_states[light_id] = {
                    "brightness": brightness,
                }
                # Store original color as XY tuple if available
                if light.color:
                    xy = light.color.xy
                    if xy:
                        original_states[light_id]["color_xy"] = (xy.x, xy.y)

        # Perform pulse cycles
        for _ in range(self.count):
            # Pulse out to target state
            for light_id in self.light_ids:
                await self._set_light_state(
                    light_id,
                    brightness=self.options.brightness,
                    color=self.options.color,
                    transition_time=self.interval_ms,
                )

            await asyncio.sleep(self.interval_ms / 1000.0)

            # Pulse back to original state
            for light_id in self.light_ids:
                light = self.bridge.lights.get(light_id)
                if not light:
                    continue
                original = original_states.get(light_id, {})

                # Prepare state update for original brightness/color
                state_update = {}
                if "brightness" in original:
                    state_update["brightness"] = original["brightness"]
                if "color_xy" in original:
                    x, y = original["color_xy"]
                    state_update["color"] = (x, y)

                # Apply transition time
                state_update["transition_time"] = self.interval_ms

                # Apply state update
                try:
                    await light.set_state(**state_update)
                except Exception:
                    # Ignore errors on individual lights
                    pass

            await asyncio.sleep(self.interval_ms / 1000.0)
