"""Async wrapper for aiohue library with connection and session management."""

from typing import Optional

import aiohttp
from aiohue.v2 import HueBridgeV2


class HueConnectionError(Exception):
    """Raised when connection to Hue bridge fails."""


class HueClient:
    """Async wrapper for Hue bridge communication with session lifecycle management.

    This class provides an async context manager interface for connecting to a
    Philips Hue bridge using the aiohue library. It handles session creation
    and cleanup automatically.

    Example:
        async with HueClient(bridge_ip="192.168.1.100", app_key="your-app-key") as client:
            # Use client.bridge to interact with the bridge
            pass
    """

    def __init__(self, bridge_ip: str, app_key: str) -> None:
        """Initialize HueClient with bridge connection details.

        Args:
            bridge_ip: IP address of the Hue bridge
            app_key: Application key for authenticating with the bridge
        """
        self.bridge_ip = bridge_ip
        self.app_key = app_key
        self._bridge: Optional[HueBridgeV2] = None

    @property
    def bridge(self) -> HueBridgeV2:
        """Get the connected bridge instance.

        Returns:
            The HueBridgeV2 instance

        Raises:
            RuntimeError: If called outside of async context manager
        """
        if self._bridge is None:
            raise RuntimeError("HueClient must be used as an async context manager")
        return self._bridge

    async def __aenter__(self) -> "HueClient":
        """Enter async context manager - establish connection to bridge.

        Returns:
            Self for use in the context

        Raises:
            HueConnectionError: If connection to bridge fails
        """
        try:
            # Create bridge instance and initialize connection
            # HueBridgeV2 creates its own aiohttp session internally
            self._bridge = HueBridgeV2(self.bridge_ip, self.app_key)

            # Initialize the bridge connection
            await self._bridge.initialize()

            return self

        except aiohttp.ClientError as e:
            # Clean up bridge if initialization fails
            if self._bridge:
                try:
                    await self._bridge.close()
                except Exception:
                    pass
                self._bridge = None
            raise HueConnectionError(
                f"Failed to connect to Hue bridge at {self.bridge_ip}: {e}"
            ) from e
        except Exception as e:
            # Clean up bridge on any other error
            if self._bridge:
                try:
                    await self._bridge.close()
                except Exception:
                    pass
                self._bridge = None
            raise HueConnectionError(
                f"Unexpected error connecting to Hue bridge: {e}"
            ) from e

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager - cleanup bridge connection.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        # Close the bridge connection if it exists
        # This will also close the internal aiohttp session
        if self._bridge:
            try:
                await self._bridge.close()
            except Exception:
                # Ignore errors during cleanup
                pass
            finally:
                self._bridge = None
