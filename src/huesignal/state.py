"""Light state capture and restoration functionality."""

import json
from dataclasses import dataclass
from typing import Any

from aiohue.v2 import HueBridgeV2


@dataclass
class LightState:
    """Captured state of a single light."""

    light_id: str
    light_name: str
    on: bool
    brightness: int
    color_temperature: int | None = None
    color_xy: tuple | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "light_id": self.light_id,
            "light_name": self.light_name,
            "on": self.on,
            "brightness": self.brightness,
            "color_temperature": self.color_temperature,
            "color_xy": self.color_xy,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LightState":
        """Create from dict."""
        return cls(**data)


@dataclass
class StateSnapshot:
    """Snapshot of all light states."""

    lights: dict[str, LightState]

    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = {light_id: light.to_dict() for light_id, light in self.lights.items()}
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> "StateSnapshot":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        lights = {light_id: LightState.from_dict(light_data) for light_id, light_data in data.items()}
        return cls(lights=lights)


def _get_light_name_from_device(bridge: HueBridgeV2, light_id: str) -> str:
    """Get light name by finding the device that contains this light."""
    for device in bridge.devices.items:
        if hasattr(device, "services"):
            for service in device.services:
                if service.rtype.value == "light" and service.rid == light_id:
                    if hasattr(device, "metadata"):
                        return device.metadata.name
    return light_id


async def capture_state(bridge: HueBridgeV2) -> StateSnapshot:
    """Capture current state of all lights.

    Args:
        bridge: HueBridgeV2 instance

    Returns:
        StateSnapshot containing all light states
    """
    lights: dict[str, LightState] = {}

    # Get all lights from bridge
    for light in bridge.lights.items:
        light_id = light.id
        state = LightState(
            light_id=light_id,
            light_name=_get_light_name_from_device(bridge, light_id),
            on=light.on.on,
            brightness=light.dimming.brightness if light.dimming else 0,
            color_temperature=None,
            color_xy=None,
        )

        # Capture color temperature if available
        if light.color_temperature:
            state.color_temperature = light.color_temperature.mirek

        # Capture color (x, y) if available
        if light.color:
            xy = light.color.xy
            if xy:
                state.color_xy = (xy.x, xy.y)

        lights[light_id] = state

    return StateSnapshot(lights=lights)


async def restore_state(bridge: HueBridgeV2, snapshot: StateSnapshot, skip_lights: list | None = None) -> list[str]:
    """Restore lights to captured state.

    Args:
        bridge: HueBridgeV2 instance
        snapshot: StateSnapshot to restore to
        skip_lights: Optional list of light IDs to skip restoration

    Returns:
        List of light IDs that failed to restore
    """
    import logging

    logger = logging.getLogger(__name__)
    skip_lights = skip_lights or []
    failed_lights = []

    for light_id, state in snapshot.lights.items():
        # Skip if in skip list
        if light_id in skip_lights:
            continue

        # Check if light still exists
        light = bridge.lights.get(light_id)
        if not light:
            continue

        light_failed = False

        # Build state update dict to apply all changes at once
        state_update = {}

        # Set on/off state
        state_update["on"] = state.on

        # Add brightness if light should be on
        if state.on and state.brightness:
            state_update["brightness"] = state.brightness

        # Add color (x, y) if available
        if state.color_xy:
            x, y = state.color_xy
            state_update["color_xy"] = (x, y)

        # Apply all state changes at once
        try:
            await bridge.lights.set_state(light_id, **state_update)
        except Exception as e:
            # Check if this is a communication issue (light physically turned off)
            error_msg = str(e).lower()
            if "communication issues" in error_msg or "not reachable" in error_msg:
                # Silently skip lights that are physically turned off
                logger.debug(f"Skipping light {light_id} ({state.light_name}): physically turned off or unreachable")
                continue
            else:
                # Log real errors
                logger.error(f"Failed to restore state for light {light_id} ({state.light_name}): {e}")
                light_failed = True

        if light_failed:
            failed_lights.append(light_id)

    return failed_lights
