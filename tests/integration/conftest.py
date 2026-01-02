"""Integration test fixtures and configuration."""

import os

import pytest


def pytest_configure(config):
    """Configure pytest for integration tests."""
    # Mark integration tests
    config.addinivalue_line("markers", "integration: mark test as an integration test that requires hardware")


@pytest.fixture(scope="session")
def bridge_ip():
    """Get bridge IP from environment or skip."""
    ip = os.environ.get("HUESIGNAL_BRIDGE_IP")
    if not ip:
        pytest.skip("HUESIGNAL_BRIDGE_IP not set - skipping integration tests")
    return ip


@pytest.fixture(scope="session")
def app_key():
    """Get app key from environment or skip."""
    key = os.environ.get("HUESIGNAL_APP_KEY")
    if not key:
        pytest.skip("HUESIGNAL_APP_KEY not set - skipping integration tests")
    return key
