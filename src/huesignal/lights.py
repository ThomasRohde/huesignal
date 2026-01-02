"""Lights management for Philips Hue."""

import logging

from aiohue.v2 import HueBridgeV2

from huesignal.auth import get_app_key
from huesignal.cache import get_cache
from huesignal.hue_client import HueClient

logger = logging.getLogger(__name__)

# Cache TTL for light list (30 seconds - lights change more frequently than bridges)
LIGHT_LIST_CACHE_TTL = 30


def _get_light_info_from_device(bridge: HueBridgeV2, light_id: str) -> tuple[str, bool]:
    """Get light name and reachability by finding the device that contains this light.

    Returns:
        Tuple of (device_name, is_reachable)
    """
    for device in bridge.devices.items:
        if hasattr(device, "services"):
            for service in device.services:
                if service.rtype.value == "light" and service.rid == light_id:
                    device_name = device.metadata.name if hasattr(device, "metadata") else "Unknown"

                    # Check connectivity status from zigbee_connectivity service
                    is_reachable = True  # Default to true
                    if hasattr(bridge, "zigbee_connectivity"):
                        for conn_service in device.services:
                            if conn_service.rtype.value == "zigbee_connectivity":
                                zigbee_conn = bridge.zigbee_connectivity.get(conn_service.rid)
                                if zigbee_conn:
                                    # In v2 API, status "connected" means reachable
                                    is_reachable = getattr(zigbee_conn, "status", None) == "connected"
                                break

                    return device_name, is_reachable
    return "Unknown", False


def _get_light_name_from_device(bridge: HueBridgeV2, light_id: str) -> str:
    """Get light name by finding the device that contains this light."""
    name, _ = _get_light_info_from_device(bridge, light_id)
    return name


async def list_lights(
    bridge_ip: str,
    filter_name: str | None = None,
    json_output: bool = False,
    use_cache: bool = True,
) -> dict:
    """
    List lights from the Hue Bridge.

    Args:
        bridge_ip: IP address of the Hue bridge
        filter_name: Optional substring to filter light names (case-insensitive)
        json_output: If True, return JSON-serializable data; if False, return formatted table
        use_cache: If True, use cached data if available (default: True)

    Returns:
        Dictionary with lights data or formatted output

    Raises:
        HueConnectionError: If unable to connect to bridge
    """
    # Check cache first (only if not filtering, since filtering can be done on cached data)
    cache_key = f"lights:{bridge_ip}"
    if use_cache:
        cache = get_cache()
        cached = cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Using cached light list for {bridge_ip}: {len(cached)} light(s)")
            # Apply filter to cached data if needed
            if filter_name:
                filtered = [light for light in cached if filter_name.lower() in light["name"].lower()]
                return {"lights": filtered, "count": len(filtered)}
            return {"lights": cached, "count": len(cached)}

    app_key = get_app_key()
    if not app_key:
        raise ValueError("No app key found. Please run 'huesignal auth login' first.")

    async with HueClient(bridge_ip, app_key) as client:
        lights = client.bridge.lights

        # Build complete light list
        all_lights = []
        for light in lights.items:
            light_name, is_reachable = _get_light_info_from_device(client.bridge, light.id)

            # Extract light info
            light_info = {
                "id": light.id,
                "name": light_name,
                "on": light.is_on if hasattr(light, "is_on") else False,
                "reachable": is_reachable,
                "color_support": bool(light.supports_color) if hasattr(light, "supports_color") else False,
                "dim_support": bool(light.supports_dimming) if hasattr(light, "supports_dimming") else False,
                "brightness": light.brightness if hasattr(light, "brightness") else None,
                "type": getattr(light, "type", "Unknown"),
                "model": light.owner.rid if hasattr(light, "owner") else "Unknown",
            }
            all_lights.append(light_info)

        # Cache the complete list
        if use_cache and all_lights:
            cache = get_cache()
            cache.set(cache_key, all_lights, ttl=LIGHT_LIST_CACHE_TTL)
            logger.debug(f"Cached light list for {bridge_ip}: {len(all_lights)} light(s)")

        # Apply filter if requested
        if filter_name:
            filtered_lights = [light for light in all_lights if filter_name.lower() in light["name"].lower()]
            return {"lights": filtered_lights, "count": len(filtered_lights)}

        return {"lights": all_lights, "count": len(all_lights)}


async def show_light(bridge_ip: str, light_name: str, use_cache: bool = True) -> dict:
    """
    Get detailed information about a specific light.

    Args:
        bridge_ip: IP address of the Hue bridge
        light_name: Name of the light to show (exact or partial match)
        use_cache: If True, use cached data if available (default: True)

    Returns:
        Dictionary with detailed light information

    Raises:
        ValueError: If light not found
        HueConnectionError: If unable to connect to bridge
    """
    # Try to find the light in cache first
    if use_cache:
        cache_key = f"lights:{bridge_ip}"
        cache = get_cache()
        cached_lights = cache.get(cache_key)

        if cached_lights is not None:
            logger.debug("Using cached light list for show_light")
            # Search for exact match first
            for light in cached_lights:
                if light_name.lower() == light["name"].lower():
                    logger.debug(f"Found light in cache (exact match): {light['name']}")
                    return light

            # Try partial match
            for light in cached_lights:
                if light_name.lower() in light["name"].lower():
                    logger.debug(f"Found light in cache (partial match): {light['name']}")
                    return light

            # Not found in cache - fall through to API call

    # Fetch from bridge if not in cache or cache miss
    app_key = get_app_key()
    if not app_key:
        raise ValueError("No app key found. Please run 'huesignal auth login' first.")

    async with HueClient(bridge_ip, app_key) as client:
        lights = client.bridge.lights

        # Find light by name (case-insensitive, partial match)
        target_light = None
        target_light_name = None
        for light in lights.items:
            light_name_attr = _get_light_name_from_device(client.bridge, light.id)
            if light_name.lower() == light_name_attr.lower():
                target_light = light
                target_light_name = light_name_attr
                break

        if not target_light:
            # Try partial match if exact match not found
            for light in lights.items:
                light_name_attr = _get_light_name_from_device(client.bridge, light.id)
                if light_name.lower() in light_name_attr.lower():
                    target_light = light
                    target_light_name = light_name_attr
                    break

        if not target_light:
            raise ValueError(f"Light not found: {light_name}")

        # Get reachability
        _, is_reachable = _get_light_info_from_device(client.bridge, target_light.id)

        # Extract detailed light info
        light_info = {
            "id": target_light.id,
            "name": target_light_name,
            "on": target_light.is_on if hasattr(target_light, "is_on") else False,
            "reachable": is_reachable,
            "color_support": bool(target_light.supports_color) if hasattr(target_light, "supports_color") else False,
            "dim_support": bool(target_light.supports_dimming) if hasattr(target_light, "supports_dimming") else False,
            "brightness": target_light.brightness if hasattr(target_light, "brightness") else None,
            "type": target_light.type if hasattr(target_light, "type") else "Unknown",
            "model": target_light.owner.rid if hasattr(target_light, "owner") else "Unknown",
        }

        return light_info
