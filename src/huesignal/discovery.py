"""Bridge discovery for Philips Hue."""

import asyncio
import logging

import httpx
from zeroconf import ServiceBrowser, Zeroconf

from .cache import get_cache

logger = logging.getLogger(__name__)

# Cache TTL for bridge discovery (60 seconds - bridges rarely change)
BRIDGE_CACHE_TTL = 60


async def discover_bridges(use_cache: bool = True) -> list[dict[str, str]]:
    """
    Discover Philips Hue bridges using meethue.com discovery endpoint.

    Args:
        use_cache: If True, check cache before making network request (default: True).

    Returns:
        List of bridge info dicts with 'id' and 'internalipaddress' keys.
        Returns empty list if discovery fails or no internet is available.
    """
    # Check cache first
    if use_cache:
        cache = get_cache()
        cached = cache.get("bridges")
        if cached is not None:
            logger.debug(f"Using cached bridge discovery result: {len(cached)} bridge(s)")
            return cached

    # Perform network discovery
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get("https://discovery.meethue.com/")
            response.raise_for_status()
            bridges = response.json()

            # Cache the result if successful and non-empty
            if bridges and use_cache:
                cache = get_cache()
                cache.set("bridges", bridges, ttl=BRIDGE_CACHE_TTL)
                logger.debug(f"Cached bridge discovery result: {len(bridges)} bridge(s)")

            return bridges
    except (TimeoutError, httpx.RequestError, httpx.HTTPError):
        # No internet or endpoint unavailable - return empty list
        return []
    except Exception:
        # Other errors (JSON parsing, etc.) - return empty list
        return []


async def discover_bridges_mdns(timeout: float = 1.0, use_cache: bool = True) -> list[dict[str, str]]:
    """
    Discover Philips Hue bridges using mDNS (Zeroconf).

    Args:
        timeout: Timeout in seconds for discovery (default 1.0).
        use_cache: If True, check cache before performing mDNS scan (default: True).

    Returns:
        List of bridge info dicts with 'id' and 'internalipaddress' keys.
        Returns empty list if no bridges found or discovery fails.
    """
    # Check cache first
    if use_cache:
        cache = get_cache()
        cached = cache.get("bridges_mdns")
        if cached is not None:
            logger.debug(f"Using cached mDNS discovery result: {len(cached)} bridge(s)")
            return cached

    class BridgeListener:
        def __init__(self):
            self.bridges = []

        def add_service(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
            info = zeroconf.get_service_info(service_type, name)
            if info and info.addresses:
                # Convert IPv4 address bytes to string
                import ipaddress
                ip = str(ipaddress.IPv4Address(info.addresses[0]))
                # Extract bridge ID from service name if possible
                # Hue services are typically named like "Philips Hue - XXXX" or similar
                bridge_id = name.split("-")[-1].strip() if "-" in name else name
                self.bridges.append({"id": bridge_id, "internalipaddress": ip})

        def remove_service(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
            pass

        def update_service(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
            pass

    try:
        zeroconf = Zeroconf()
        listener = BridgeListener()
        ServiceBrowser(zeroconf, "_hue._tcp.local.", listener)

        # Wait for discovery with timeout
        await asyncio.sleep(timeout)

        zeroconf.close()
        bridges = listener.bridges

        # Cache the result if successful and non-empty
        if bridges and use_cache:
            cache = get_cache()
            cache.set("bridges_mdns", bridges, ttl=BRIDGE_CACHE_TTL)
            logger.debug(f"Cached mDNS discovery result: {len(bridges)} bridge(s)")

        return bridges
    except Exception:
        # Any error in mDNS discovery - return empty list
        return []
