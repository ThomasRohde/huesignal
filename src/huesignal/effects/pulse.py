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
                # Store original on/off state
                was_on = light.on.on
                # Store original brightness
                brightness = light.dimming.brightness if light.dimming else 100
                original_states[light_id] = {
                    "was_on": was_on,
                    "brightness": brightness,
                }
                logger.debug(f"Captured original state for {light_id}: on={was_on}, brightness={brightness}")
                # Store original color as XY tuple if available
                if light.color:
                    xy = light.color.xy
                    if xy:
                        original_states[light_id]["color_xy"] = (xy.x, xy.y)

        # Perform pulse cycles
        for _ in range(self.count):
            # Pulse DOWN first (go dim with target color)
            for light_id in self.light_ids:
                await self._set_light_state(
                    light_id,
                    on=True,
                    brightness=1,
                    color=self.options.color,
                    transition_time=self.interval_ms,
                )

            # Wait for transition to complete
            await asyncio.sleep((self.interval_ms / 1000.0) + 0.1)

            # Pulse UP to target brightness/color
            target_brightness = self.options.brightness if self.options.brightness else 254
            for light_id in self.light_ids:
                await self._set_light_state(
                    light_id,
                    on=True,
                    brightness=target_brightness,
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

                logger.debug(f"Restoring light {light_id} to original state")

                # Restore to original on/off state and brightness
                try:
                    was_on = original.get("was_on", True)
                    brightness = original.get("brightness", 100)

                    if was_on:
                        # Light was on - restore brightness
                        await self.bridge.lights.set_state(
                            light_id, on=True, brightness=brightness, transition_time=self.interval_ms
                        )
                    else:
                        # Light was off - turn it back off
                        await self.bridge.lights.set_state(light_id, on=False, transition_time=self.interval_ms)
                    logger.debug(f"Restored to: on={was_on}, brightness={brightness}")
                except Exception as e:
                    # Only log if not a communication issue (physically off light)
                    if "communication issues" not in str(e).lower():
                        logger.error(f"Failed to restore light state for {light_id}: {e}")

            # Wait for transition to complete plus a bit extra
            await asyncio.sleep((self.interval_ms / 1000.0) + 0.1)
