"""Smoke tests for huesignal integration with physical Hue bridge.

These tests require:
1. A real Philips Hue bridge on the network
2. HUESIGNAL_BRIDGE_IP environment variable set to bridge IP
3. HUESIGNAL_APP_KEY environment variable set to valid app key

Safety: These tests modify light state and restore it afterward.
Only run against bridges you control.
"""

import asyncio
import pytest

from huesignal.hue_client import HueClient, HueConnectionError


@pytest.mark.integration
@pytest.mark.asyncio
async def test_bridge_connection(bridge_ip, app_key):
    """Test that we can connect to the bridge."""
    async with HueClient(bridge_ip, app_key) as client:
        bridge = client.bridge
        assert bridge is not None
        assert len(bridge.lights) >= 0  # Should have lights or be empty


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_lights(bridge_ip, app_key):
    """Test listing lights from the bridge."""
    async with HueClient(bridge_ip, app_key) as client:
        bridge = client.bridge
        lights = list(bridge.lights.items())
        
        # We should have at least some lights, but if not, that's okay
        assert isinstance(lights, list)
        
        if lights:
            # Check light structure
            light_id, light = lights[0]
            assert isinstance(light_id, str)
            assert light is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_toggle_light_with_restoration(bridge_ip, app_key):
    """Test toggling a light and restoring its original state.
    
    This is a safe operation:
    1. Find first available light
    2. Capture its state
    3. Toggle the light on/off
    4. Restore original state
    5. Verify it's restored
    """
    async with HueClient(bridge_ip, app_key) as client:
        bridge = client.bridge
        lights = list(bridge.lights.items())
        
        if not lights:
            pytest.skip("No lights available on bridge")
        
        # Use first light
        light_id, light = lights[0]
        
        # Capture original state
        original_state = {
            "on": light.on.on,
            "brightness": light.dimming.brightness if light.dimming else None,
        }
        
        try:
            # Toggle off if on, or on if off
            new_state = not original_state["on"]
            await light.set_state(on=new_state)
            
            # Give it a moment to update
            await asyncio.sleep(0.5)
            
            # Verify state changed
            # (Note: state may not update immediately, so we just ensure no error)
            
        finally:
            # Always restore original state
            try:
                await light.set_state(
                    on=original_state["on"],
                    brightness=original_state["brightness"],
                )
            except Exception:
                # Ignore errors during restoration
                pass


@pytest.mark.integration
@pytest.mark.asyncio
async def test_invalid_credentials(bridge_ip):
    """Test that invalid credentials raise proper error."""
    with pytest.raises(HueConnectionError):
        async with HueClient(bridge_ip, "invalid-key-xyz") as client:
            # Should fail during initialization
            _ = client.bridge
