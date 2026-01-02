"""Light name resolver with disambiguation for command-line selection."""

from dataclasses import dataclass

from aiohue.v2 import HueBridgeV2


class AmbiguousLightError(Exception):
    """Raised when light name matches multiple lights."""

    def __init__(self, name: str, candidates: list[tuple]):
        self.name = name
        self.candidates = candidates
        msg = f"Ambiguous light name '{name}' matches multiple lights:\n"
        for light_id, light_name in candidates:
            msg += f"  - {light_name} (ID: {light_id})\n"
        msg += "Please use --light-id to specify the exact light ID."
        super().__init__(msg)


class LightNotFoundError(Exception):
    """Raised when light name or ID is not found."""

    def __init__(self, identifier: str):
        self.identifier = identifier
        super().__init__(f"Light not found: {identifier}")


@dataclass
class ResolvedLight:
    """Resolved light information."""

    light_id: str
    light_name: str

    def __str__(self) -> str:
        return f"{self.light_name} (ID: {self.light_id})"


def _get_light_name_from_device(bridge: HueBridgeV2, light_id: str) -> str:
    """Get light name by finding the device that contains this light.

    Args:
        bridge: HueBridgeV2 instance
        light_id: Light ID to find name for

    Returns:
        Device name or light ID if not found
    """
    # In Hue v2 API, names are stored in devices, not lights
    for device in bridge.devices.items:
        if hasattr(device, 'services'):
            for service in device.services:
                if service.rtype.value == 'light' and service.rid == light_id:
                    if hasattr(device, 'metadata'):
                        return device.metadata.name
    return light_id  # Fallback to ID if no device name found


async def resolve_light(
    bridge: HueBridgeV2,
    light_name: str | None = None,
    light_id: str | None = None,
) -> ResolvedLight:
    """Resolve a single light by name or ID.

    Args:
        bridge: HueBridgeV2 instance
        light_name: Light name to resolve (case-insensitive)
        light_id: Light ID (takes precedence over name)

    Returns:
        ResolvedLight with ID and name

    Raises:
        LightNotFoundError: If light not found
        AmbiguousLightError: If name matches multiple lights
    """
    # If light_id is provided, use it directly
    if light_id:
        # Validate the ID exists
        light = bridge.lights.get(light_id)
        if not light:
            raise LightNotFoundError(light_id)
        name = _get_light_name_from_device(bridge, light_id)
        return ResolvedLight(light_id=light_id, light_name=name)

    # If light_name is provided, match it
    if light_name:
        matches: list[tuple] = []
        light_name_lower = light_name.lower()

        # Build light ID to name mapping from devices
        for device in bridge.devices.items:
            if hasattr(device, 'services') and hasattr(device, 'metadata'):
                device_name = device.metadata.name
                for service in device.services:
                    if service.rtype.value == 'light':
                        if device_name.lower() == light_name_lower:
                            # Exact case-insensitive match
                            matches.append((service.rid, device_name))

        if len(matches) == 0:
            raise LightNotFoundError(light_name)
        elif len(matches) == 1:
            light_id, light_name_result = matches[0]
            return ResolvedLight(light_id=light_id, light_name=light_name_result)
        else:
            # Ambiguous match
            raise AmbiguousLightError(light_name, matches)

    # No identifier provided
    raise ValueError("Either light_name or light_id must be provided")


async def resolve_lights(
    bridge: HueBridgeV2,
    light_names: list[str] | None = None,
    light_ids: list[str] | None = None,
) -> list[ResolvedLight]:
    """Resolve multiple lights by names or IDs.

    Args:
        bridge: HueBridgeV2 instance
        light_names: List of light names to resolve
        light_ids: List of light IDs

    Returns:
        List of ResolvedLight objects

    Raises:
        LightNotFoundError: If any light not found
        AmbiguousLightError: If any name matches multiple lights
    """
    resolved: list[ResolvedLight] = []

    # If light_ids provided, use them
    if light_ids:
        for lid in light_ids:
            light = bridge.lights.get(lid)
            if not light:
                raise LightNotFoundError(lid)
            name = _get_light_name_from_device(bridge, lid)
            resolved.append(ResolvedLight(light_id=lid, light_name=name))
        return resolved

    # If light_names provided, resolve them
    if light_names:
        for name in light_names:
            resolved.append(await resolve_light(bridge, light_name=name))
        return resolved

    # No identifiers provided - return all lights
    for light in bridge.lights.items:
        name = _get_light_name_from_device(bridge, light.id)
        resolved.append(ResolvedLight(light_id=light.id, light_name=name))

    return resolved


def parse_light_argument(arg: str) -> list[str]:
    """Parse light argument which may be comma-separated.

    Args:
        arg: Light name or comma-separated names

    Returns:
        List of light names
    """
    return [name.strip() for name in arg.split(",") if name.strip()]
