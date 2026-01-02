"""Pytest configuration and shared fixtures."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_hue_bridge():
    """Create a mock Hue bridge for testing."""
    bridge = MagicMock()
    bridge.lights = {}
    return bridge


@pytest.fixture
def mock_light():
    """Create a mock Hue light."""
    light = MagicMock()
    light.metadata = MagicMock()
    light.metadata.name = "Test Light"
    light.is_on = True
    light.brightness = 200
    return light


@pytest.fixture
def async_mock():
    """Create an AsyncMock for testing async functions."""
    return AsyncMock()
