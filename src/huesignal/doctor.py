"""Diagnostic checks for huesignal."""

import asyncio
from typing import Optional

from huesignal.auth import get_app_key
from huesignal.discovery import discover_bridges, discover_bridges_mdns
from huesignal.hue_client import HueClient, HueConnectionError
from huesignal.logging_config import get_logger

logger = get_logger()


class DoctorStatus:
    """Status of doctor checks."""

    def __init__(self):
        self.checks = []
        self.all_passed = True

    def add_check(self, name: str, passed: bool, message: str) -> None:
        """Add a check result."""
        self.checks.append({"name": name, "passed": passed, "message": message})
        if not passed:
            self.all_passed = False

    def report(self, verbose: bool = False) -> str:
        """Generate a report of all checks."""
        lines = ["=== huesignal Doctor Report ===\n"]

        for check in self.checks:
            status = "✓ PASS" if check["passed"] else "✗ FAIL"
            lines.append(f"{status}: {check['name']}")
            if verbose and check["message"]:
                lines.append(f"       {check['message']}")

        lines.append("")
        if self.all_passed:
            lines.append("All checks passed!")
        else:
            lines.append("Some checks failed. See above for details.")

        return "\n".join(lines)


async def run_doctor(bridge_ip: Optional[str] = None, verbose: bool = False) -> DoctorStatus:
    """
    Run diagnostic checks on the huesignal setup.

    Args:
        bridge_ip: Optional bridge IP to test
        verbose: Print verbose output

    Returns:
        DoctorStatus with results of all checks
    """
    status = DoctorStatus()
    logger.debug("Starting doctor checks")

    # Check 1: Credentials
    app_key = get_app_key()
    if app_key:
        status.add_check("Credentials", True, "App key found")
        logger.debug("App key found in keyring or environment")
    else:
        status.add_check("Credentials", False, "No app key found. Run 'huesignal auth login' first")
        logger.debug("No app key found")
        return status  # Can't proceed without credentials

    # Check 2: Bridge discovery
    if not bridge_ip:
        logger.debug("Discovering bridges...")
        bridges = await discover_bridges()
        if not bridges:
            logger.debug("meethue.com discovery failed, trying mDNS...")
            bridges = await discover_bridges_mdns(timeout=2.0)

        if bridges:
            bridge_ip = bridges[0].get("internalipaddress")
            status.add_check("Bridge Discovery", True, f"Found bridge at {bridge_ip}")
            logger.debug(f"Bridge discovered: {bridge_ip}")
        else:
            status.add_check(
                "Bridge Discovery",
                False,
                "No bridges found. Specify --bridge-ip manually",
            )
            logger.debug("Bridge discovery failed")
            return status  # Can't proceed without bridge IP
    else:
        status.add_check("Bridge IP", True, f"Using specified bridge: {bridge_ip}")
        logger.debug(f"Using specified bridge: {bridge_ip}")

    # Check 3: Bridge connectivity
    try:
        logger.debug(f"Testing connection to bridge at {bridge_ip}...")
        async with HueClient(bridge_ip, app_key) as client:
            # Try to fetch lights to verify connection works
            lights = client.bridge.lights
            light_count = len(lights) if lights else 0
            status.add_check("Bridge Connectivity", True, f"Connected successfully ({light_count} lights found)")
            logger.debug(f"Successfully connected to bridge. Found {light_count} lights.")
    except HueConnectionError as e:
        status.add_check("Bridge Connectivity", False, f"Connection failed: {str(e)}")
        logger.debug(f"Connection failed: {e}")
    except Exception as e:
        status.add_check("Bridge Connectivity", False, f"Unexpected error: {str(e)}")
        logger.debug(f"Unexpected error during connection: {e}")

    logger.debug("Doctor checks completed")
    return status
