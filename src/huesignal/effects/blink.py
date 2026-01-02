"""Blink effect implementation."""

import asyncio
from typing import Optional

from huesignal.hue_client import HueClient


async def blink(
    client: HueClient,
    light_ids: list,
    count: int = 1,
    interval_ms: int = 500,
    restore: bool = False,
) -> None:
    """
    Blink lights.

    Args:
        client: HueClient instance
        light_ids: List of light IDs to blink
        count: Number of blinks (default 1)
        interval_ms: Interval between blinks in milliseconds (default 500)
        restore: If True, restore original state after effect
    """
    interval_s = interval_ms / 1000.0

    # Store original states if restore is enabled
    original_states = {}
    if restore:
        for light_id in light_ids:
            light = client.bridge.lights.get(light_id)
            if light:
                original_states[light_id] = {"on": light.is_on, "brightness": light.brightness}

    # Perform blinks
    for _ in range(count):
        # Turn off
        for light_id in light_ids:
            light = client.bridge.lights.get(light_id)
            if light:
                await light.set_state(on=False)

        await asyncio.sleep(interval_s)

        # Turn on
        for light_id in light_ids:
            light = client.bridge.lights.get(light_id)
            if light:
                await light.set_state(on=True)

        await asyncio.sleep(interval_s)

    # Restore original state if requested
    if restore:
        for light_id, state in original_states.items():
            light = client.bridge.lights.get(light_id)
            if light:
                await light.set_state(on=state["on"], brightness=state["brightness"])
