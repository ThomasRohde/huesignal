"""Breathe effect implementation - smooth breathing light effect with rate limiting."""

import asyncio
import time

from huesignal.effects.base import Effect, EffectOptions, register_effect


@register_effect
class BreatheEffect(Effect):
    """Breathe effect that cycles brightness smoothly to signal long-running job completion."""

    name = "breathe"
    description = "Smooth breathing effect for long-running job completion signal"

    def __init__(
        self,
        bridge,
        light_ids: list[str],
        options: EffectOptions,
        duration_ms: int = 4000,
        period_ms: int = 2000,
    ):
        """Initialize breathe effect.

        Args:
            bridge: HueBridgeV2 instance
            light_ids: List of light IDs to apply effect to
            options: EffectOptions for the effect
            duration_ms: Total duration of the breathe effect in milliseconds
            period_ms: Time for one complete breath cycle in milliseconds
        """
        super().__init__(bridge, light_ids, options)
        self.duration_ms = duration_ms
        self.period_ms = period_ms

    async def _apply_effect(self) -> None:
        """Apply the breathe effect with rate-limited brightness changes."""
        # Calculate parameters
        num_steps = 20  # Number of brightness steps per half-cycle
        min_brightness = 1
        max_brightness = 254

        # If brightness option is set, use it as the max
        if self.options.brightness:
            max_brightness = self.options.brightness

        # Catch current brightness for baseline
        current_brightness = 100  # Default midpoint

        # Calculate timing
        half_cycle_ms = self.period_ms / 2
        step_duration_ms = half_cycle_ms / num_steps

        # Minimum update interval to avoid bridge overload
        min_interval_ms = 50  # Rate limit: max 20 updates per second
        actual_step_duration_ms = max(step_duration_ms, min_interval_ms)

        # Adjust number of steps if we're rate limited
        adjusted_steps = max(1, int(half_cycle_ms / actual_step_duration_ms))

        # Calculate total time for one complete cycle with actual timing
        actual_cycle_ms = adjusted_steps * actual_step_duration_ms * 2

        # Number of complete cycles to fit within duration
        num_cycles = max(1, int(self.duration_ms / actual_cycle_ms))

        # Recalculate total duration to match requested duration
        total_cycles = int(self.duration_ms / actual_cycle_ms)

        start_time = time.time()
        cycle = 0

        while True:
            elapsed_ms = (time.time() - start_time) * 1000

            if elapsed_ms >= self.duration_ms:
                break

            # Fade in (low to high brightness)
            for step in range(adjusted_steps):
                elapsed_ms = (time.time() - start_time) * 1000
                if elapsed_ms >= self.duration_ms:
                    break

                # Linear interpolation from min to max
                progress = step / adjusted_steps
                brightness = int(min_brightness + (max_brightness - min_brightness) * progress)

                # Apply to all lights
                for light_id in self.light_ids:
                    await self._set_light_state(light_id, brightness=brightness, transition_time=0)

                # Wait for next step
                await asyncio.sleep(actual_step_duration_ms / 1000.0)

            # Fade out (high to low brightness)
            for step in range(adjusted_steps):
                elapsed_ms = (time.time() - start_time) * 1000
                if elapsed_ms >= self.duration_ms:
                    break

                # Linear interpolation from max to min
                progress = step / adjusted_steps
                brightness = int(max_brightness - (max_brightness - min_brightness) * progress)

                # Apply to all lights
                for light_id in self.light_ids:
                    await self._set_light_state(light_id, brightness=brightness, transition_time=0)

                # Wait for next step
                await asyncio.sleep(actual_step_duration_ms / 1000.0)

            cycle += 1
