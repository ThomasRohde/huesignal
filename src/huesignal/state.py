"""Light state capture and restoration functionality."""

import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from aiohue.v2 import HueBridgeV2
from aiohue.v2.models.light import Light


@dataclass
class LightState:
    """Captured state of a single light."""

    light_id: str
    light_name: str
    on: bool
    brightness: int
    color_temperature: Optional[int] = None
    color_xy: Optional[tuple] = None

    def to_dict(self) -> Dict[str, Any]:
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
    def from_dict(cls, data: Dict[str, Any]) -> "LightState":
        """Create from dict."""
        return cls(**data)


@dataclass
class StateSnapshot:
    """Snapshot of all light states."""

    lights: Dict[str, LightState]

    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = {
            light_id: light.to_dict()
            for light_id, light in self.lights.items()
        }
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> "StateSnapshot":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        lights = {
            light_id: LightState.from_dict(light_data)
            for light_id, light_data in data.items()
        }
        return cls(lights=lights)


def _get_light_name_from_device(bridge: HueBridgeV2, light_id: str) -> str:
    """Get light name by finding the device that contains this light."""
    for device in bridge.devices.items:
        if hasattr(device, 'services'):
            for service in device.services:
                if service.rtype.value == 'light' and service.rid == light_id:
                    if hasattr(device, 'metadata'):
                        return device.metadata.name
    return light_id


async def capture_state(bridge: HueBridgeV2) -> StateSnapshot:
    """Capture current state of all lights.

    Args:
        bridge: HueBridgeV2 instance

    Returns:
        StateSnapshot containing all light states
    """
    lights: Dict[str, LightState] = {}

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


async def restore_state(
    bridge: HueBridgeV2, snapshot: StateSnapshot, skip_lights: Optional[list] = None
) -> None:
    """Restore lights to captured state.

    Args:
        bridge: HueBridgeV2 instance
        snapshot: StateSnapshot to restore to
        skip_lights: Optional list of light IDs to skip restoration
    """
    skip_lights = skip_lights or []

    for light_id, state in snapshot.lights.items():
        # Skip if in skip list
        if light_id in skip_lights:
            continue

        # Check if light still exists
        light = bridge.lights.get(light_id)
        if not light:
            continue

        # Restore on/off state
        try:
            await light.set_state(on=state.on)
        except Exception:
            # Ignore errors for individual lights
            pass

        # Restore brightness if light is on
        if state.on and state.brightness:
            try:
                await light.set_state(brightness=state.brightness)
            except Exception:
                pass

        # Restore color temperature if available
        if state.color_temperature:
            try:
                await light.set_state(color_temperature=state.color_temperature)
            except Exception:
                pass

        # Restore color (x, y) if available
        if state.color_xy:
            try:
                x, y = state.color_xy
                await light.set_state(color=(x, y))
            except Exception:
                pass
