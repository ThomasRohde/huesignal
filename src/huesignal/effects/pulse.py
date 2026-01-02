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
        import logging
        logger = logging.getLogger(__name__)
        
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
                logger.debug(f"Captured original brightness for {light_id}: {brightness}")
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

            # Wait for transition to complete plus a bit extra
            await asyncio.sleep((self.interval_ms / 1000.0) + 0.1)

            # Pulse back to original state
            for light_id in self.light_ids:
                if light_id not in self.bridge.lights:
                    continue
                original = original_states.get(light_id, {})
                
                logger.debug(f"Restoring light {light_id} to brightness: {original.get('brightness')}")

                # Restore brightness only (color is handled separately if needed)
                if "brightness" in original:
                    try:
                        await self.bridge.lights.set_state(
                            light_id, 
                            on=True, 
                            brightness=original["brightness"],
                            transition_time=self.interval_ms
                        )
                        logger.debug(f"Restored brightness to: {original['brightness']}")
                    except Exception as e:
                        logger.error(f"Failed to restore light state for {light_id}: {e}")

            # Wait for transition to complete plus a bit extra
            await asyncio.sleep((self.interval_ms / 1000.0) + 0.1)
