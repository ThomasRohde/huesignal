"""Primitive atomic operations for effect composition."""

import asyncio
from dataclasses import dataclass
from typing import Any

from aiohue.v2 import HueBridgeV2

from huesignal.effects.base import validate_brightness
from huesignal.effects.colors import parse_color, rgb_to_xy


@dataclass
class PrimitiveResult:
    """Result of a primitive execution.

    Captures success/failure status per light to enable
    robust error handling in composed effects.
    """

    light_id: str
    success: bool
    error: str | None = None


@dataclass
class SetState:
    """Primitive to set light state atomically.

    Sets on/off, brightness, color, and transition parameters.
    This is the fundamental operation for all light control.

    Attributes:
        on: Whether the light should be on or off
        brightness: Brightness level (1-254), None to leave unchanged
        color: Color name or hex code, None to leave unchanged
        transition_ms: Transition duration in milliseconds
    """

    on: bool = True
    brightness: int | None = None
    color: str | None = None
    transition_ms: int = 500

    def __post_init__(self):
        """Validate parameters after initialization."""
        if self.brightness is not None:
            validate_brightness(self.brightness)
        if self.transition_ms < 0:
            raise ValueError(f"transition_ms must be >= 0, got {self.transition_ms}")

    async def execute(self, ctx: HueBridgeV2, light_id: str) -> PrimitiveResult:
        """Execute the SetState primitive on a specific light.

        Args:
            ctx: HueBridgeV2 bridge connection
            light_id: Light ID to control

        Returns:
            PrimitiveResult indicating success or failure
        """
        try:
            # Check if light exists
            if light_id not in ctx.lights:
                return PrimitiveResult(light_id=light_id, success=False, error=f"Light {light_id} not found")

            # Prepare state update
            state_update: dict[str, Any] = {"on": self.on}

            # Add brightness if specified
            # Note: Hue V2 API expects brightness as 0.0-100.0 (percentage)
            # but huesignal uses 1-254 internally for consistency with V1
            # so we need to convert: 1-254 -> 0.39-100.0
            if self.brightness is not None:
                # Convert from 1-254 range to 0.0-100.0 percentage
                brightness_pct = (self.brightness / 254.0) * 100.0
                state_update["brightness"] = brightness_pct

            # Add color if specified
            if self.color:
                try:
                    rgb = parse_color(self.color)
                    xy = rgb_to_xy(*rgb)
                    state_update["color_xy"] = xy
                except ValueError as e:
                    return PrimitiveResult(light_id=light_id, success=False, error=f"Invalid color '{self.color}': {e}")

            # Add transition time
            state_update["transition_time"] = self.transition_ms

            # Apply state update
            await ctx.lights.set_state(light_id, **state_update)

            return PrimitiveResult(light_id=light_id, success=True)

        except Exception as e:
            return PrimitiveResult(light_id=light_id, success=False, error=str(e))

    def estimated_duration_ms(self) -> int:
        """Estimate the duration of this primitive for scheduling.

        Returns:
            Estimated duration in milliseconds
        """
        # Duration is the transition time plus a small buffer for API call
        return self.transition_ms + 50


@dataclass
class Wait:
    """Primitive to wait for a specified duration.

    Used to insert pauses between other primitives in effect sequences.

    Attributes:
        duration_ms: Duration to wait in milliseconds
    """

    duration_ms: int = 500

    def __post_init__(self):
        """Validate parameters after initialization."""
        if self.duration_ms < 0:
            raise ValueError(f"duration_ms must be >= 0, got {self.duration_ms}")

    async def execute(self, ctx: HueBridgeV2, light_id: str) -> PrimitiveResult:
        """Execute the Wait primitive.

        Args:
            ctx: HueBridgeV2 bridge connection (unused but kept for signature consistency)
            light_id: Light ID (unused but kept for signature consistency)

        Returns:
            PrimitiveResult indicating success
        """
        try:
            await asyncio.sleep(self.duration_ms / 1000.0)
            return PrimitiveResult(light_id=light_id, success=True)
        except Exception as e:
            return PrimitiveResult(light_id=light_id, success=False, error=str(e))

    def estimated_duration_ms(self) -> int:
        """Estimate the duration of this primitive for scheduling.

        Returns:
            Estimated duration in milliseconds
        """
        return self.duration_ms
