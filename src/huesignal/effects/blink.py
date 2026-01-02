"""Blink effect implementation."""

import asyncio

from aiohue.v2 import HueBridgeV2

from huesignal.effects.base import Effect, EffectOptions, register_effect


@register_effect
class Blink(Effect):
    """Blink effect - turns lights on and off repeatedly."""

    name = "blink"
    description = "Blink lights on and off"

    def __init__(
        self,
        bridge: HueBridgeV2,
        light_ids: list[str],
        options: EffectOptions,
        count: int = 3,
        interval_ms: int = 500,
    ):
        """Initialize blink effect.

        Args:
            bridge: HueBridgeV2 instance
            light_ids: List of light IDs to apply effect to
            options: EffectOptions for the effect
            count: Number of blinks (default 3)
            interval_ms: Time between blinks in milliseconds (default 500)
        """
        super().__init__(bridge, light_ids, options)
        self.count = count
        self.interval_ms = interval_ms

    async def _apply_effect(self) -> None:
        """Apply the blink effect to all lights.

        Blinks lights on and off count times.
        """
        interval_s = self.interval_ms / 1000.0

        # Perform blinks
        for _ in range(self.count):
            # Turn off
            for light_id in self.light_ids:
                if light_id in self.bridge.lights:
                    try:
                        await self.bridge.lights.set_state(light_id, on=False)
                    except Exception:
                        pass

            await asyncio.sleep(interval_s)

            # Turn on
            for light_id in self.light_ids:
                if light_id in self.bridge.lights:
                    try:
                        await self.bridge.lights.set_state(light_id, on=True)
                    except Exception:
                        pass

            await asyncio.sleep(interval_s)
