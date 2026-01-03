"""Blink effect implementation."""

import asyncio
from typing import Any, ClassVar

from aiohue.v2 import HueBridgeV2

from huesignal.effects.base import Effect, EffectOptions, EffectParam, register_effect


@register_effect
class Blink(Effect):
    """Blink effect - turns lights on and off repeatedly."""

    name = "blink"
    description = "Blink lights on and off"
    params: ClassVar[list[EffectParam]] = [
        EffectParam(name="count", type=int, default=3, description="Number of blinks"),
        EffectParam(name="interval_ms", type=int, default=500, description="Time between blinks in milliseconds"),
    ]

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

    def to_primitives(self) -> list[Any]:
        """Convert blink effect to sequence of primitives.

        Returns:
            List of SetState and Wait primitives that implement the blink effect.
        """
        from huesignal.effects.primitives import SetState, Wait

        primitives: list[Any] = []
        interval_s = self.interval_ms / 1000.0

        for _ in range(self.count):
            # Blink OFF
            primitives.append(
                SetState(
                    on=False,
                    brightness=None,
                    color=None,
                    transition_ms=0,  # Instant transition for blink effect
                )
            )
            primitives.append(Wait(duration_ms=self.interval_ms))

            # Blink ON with color/brightness from options
            primitives.append(
                SetState(
                    on=True,
                    brightness=self.options.brightness,
                    color=self.options.color,
                    transition_ms=0,  # Instant transition for blink effect
                )
            )
            primitives.append(Wait(duration_ms=self.interval_ms))

        return primitives

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

            # Turn on with color/brightness from options
            for light_id in self.light_ids:
                await self._set_light_state(
                    light_id,
                    on=True,
                    brightness=self.options.brightness,
                    color=self.options.color,
                    transition_time=0,  # Instant transition for blink effect
                )

            await asyncio.sleep(interval_s)
