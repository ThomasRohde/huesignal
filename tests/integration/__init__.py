"""Integration tests for huesignal.

These tests require actual Hue bridge hardware and are gated by environment variables:
- HUESIGNAL_BRIDGE_IP: IP address of the Hue bridge
- HUESIGNAL_APP_KEY: Application key for bridge authentication

Safety warning: These tests interact with physical lights and may cause them
to change state. Always ensure you have permission to control the lights
and that the bridge is safe to test against.
"""
