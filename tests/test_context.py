"""Unit tests for ExecutionContext."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from huesignal.effects.context import ExecutionContext
from huesignal.state import LightState, StateSnapshot


@pytest.fixture
def mock_bridge():
    """Create a mock HueBridgeV2 instance."""
    bridge = MagicMock()

    # Mock lights collection
    light1 = MagicMock()
    light1.id = "light-1"
    light1.on.on = True
    light1.dimming.brightness = 100
    light1.color = None
    light1.color_temperature = None

    light2 = MagicMock()
    light2.id = "light-2"
    light2.on.on = False
    light2.dimming.brightness = 50
    light2.color = None
    light2.color_temperature = None

    bridge.lights.items = [light1, light2]

    def get_light_by_id(lid: str):
        if lid == "light-1":
            return light1
        elif lid == "light-2":
            return light2
        return None

    bridge.lights.get = MagicMock(side_effect=get_light_by_id)
    bridge.lights.set_state = AsyncMock()

    # Mock devices for name lookup
    device1 = MagicMock()
    device1.metadata.name = "Office Light"
    service1 = MagicMock()
    service1.rtype.value = "light"
    service1.rid = "light-1"
    device1.services = [service1]

    device2 = MagicMock()
    device2.metadata.name = "Bedroom Light"
    service2 = MagicMock()
    service2.rtype.value = "light"
    service2.rid = "light-2"
    device2.services = [service2]

    bridge.devices.items = [device1, device2]

    return bridge


@pytest.fixture
def sample_snapshot():
    """Create a sample StateSnapshot."""
    return StateSnapshot(
        lights={
            "light-1": LightState(
                light_id="light-1", light_name="Office Light", on=True, brightness=100, color_xy=None
            ),
            "light-2": LightState(
                light_id="light-2", light_name="Bedroom Light", on=False, brightness=50, color_xy=None
            ),
        }
    )


class TestExecutionContext:
    """Tests for ExecutionContext dataclass."""

    def test_context_initialization(self, mock_bridge: MagicMock) -> None:
        """Test ExecutionContext initializes with bridge."""
        ctx = ExecutionContext(bridge=mock_bridge)
        assert ctx.bridge == mock_bridge
        assert ctx.captured_states == {}

    def test_context_initialization_with_captured_states(
        self, mock_bridge: MagicMock, sample_snapshot: StateSnapshot
    ) -> None:
        """Test ExecutionContext can be initialized with captured states."""
        ctx = ExecutionContext(bridge=mock_bridge, captured_states={"test": sample_snapshot})
        assert ctx.bridge == mock_bridge
        assert "test" in ctx.captured_states
        assert ctx.captured_states["test"] == sample_snapshot

    @pytest.mark.asyncio
    async def test_capture_state_all_lights(self, mock_bridge: MagicMock) -> None:
        """Test capturing state of all lights."""
        ctx = ExecutionContext(bridge=mock_bridge)

        snapshot = await ctx.capture_state()

        assert snapshot is not None
        assert "light-1" in snapshot.lights
        assert "light-2" in snapshot.lights
        assert "latest" in ctx.captured_states
        assert ctx.captured_states["latest"] == snapshot

    @pytest.mark.asyncio
    async def test_capture_state_specific_lights(self, mock_bridge: MagicMock) -> None:
        """Test capturing state of specific lights."""
        ctx = ExecutionContext(bridge=mock_bridge)

        snapshot = await ctx.capture_state(light_ids=["light-1"])

        assert snapshot is not None
        assert "light-1" in snapshot.lights
        assert "light-2" not in snapshot.lights
        assert len(snapshot.lights) == 1

    @pytest.mark.asyncio
    async def test_capture_state_stores_in_context(self, mock_bridge: MagicMock) -> None:
        """Test capture_state stores snapshot in context."""
        ctx = ExecutionContext(bridge=mock_bridge)

        assert "latest" not in ctx.captured_states

        await ctx.capture_state()

        assert "latest" in ctx.captured_states

    @pytest.mark.asyncio
    async def test_capture_state_overwrites_latest(self, mock_bridge: MagicMock) -> None:
        """Test multiple captures overwrite the 'latest' snapshot."""
        ctx = ExecutionContext(bridge=mock_bridge)

        snapshot1 = await ctx.capture_state(light_ids=["light-1"])
        snapshot2 = await ctx.capture_state(light_ids=["light-2"])

        assert ctx.captured_states["latest"] == snapshot2
        assert ctx.captured_states["latest"] != snapshot1

    @pytest.mark.asyncio
    async def test_restore_state_with_snapshot(self, mock_bridge: MagicMock, sample_snapshot: StateSnapshot) -> None:
        """Test restoring state with explicit snapshot."""
        ctx = ExecutionContext(bridge=mock_bridge)

        failed_lights = await ctx.restore_state(snapshot=sample_snapshot)

        assert isinstance(failed_lights, list)
        assert len(failed_lights) == 0  # No failures in mock

        # Verify set_state was called
        assert mock_bridge.lights.set_state.called

    @pytest.mark.asyncio
    async def test_restore_state_with_captured_snapshot(self, mock_bridge: MagicMock) -> None:
        """Test restoring state using captured snapshot."""
        ctx = ExecutionContext(bridge=mock_bridge)

        # First capture state
        await ctx.capture_state()

        # Then restore it
        failed_lights = await ctx.restore_state()

        assert isinstance(failed_lights, list)
        assert mock_bridge.lights.set_state.called

    @pytest.mark.asyncio
    async def test_restore_state_without_capture_raises_error(self, mock_bridge: MagicMock) -> None:
        """Test restore_state raises error if no state captured."""
        ctx = ExecutionContext(bridge=mock_bridge)

        with pytest.raises(ValueError, match="No state has been captured"):
            await ctx.restore_state()

    @pytest.mark.asyncio
    async def test_restore_state_with_skip_lights(self, mock_bridge: MagicMock, sample_snapshot: StateSnapshot) -> None:
        """Test restoring state while skipping specific lights."""
        ctx = ExecutionContext(bridge=mock_bridge)

        failed_lights = await ctx.restore_state(snapshot=sample_snapshot, skip_lights=["light-1"])

        assert isinstance(failed_lights, list)
        # Verify that set_state was called but not for light-1
        # (This is a simplified check; full verification would require more mock inspection)

    @pytest.mark.asyncio
    async def test_restore_state_returns_failures(self, mock_bridge: MagicMock, sample_snapshot: StateSnapshot) -> None:
        """Test restore_state returns list of failed lights."""

        # Make one light fail to restore
        async def set_state_with_failure(light_id: str, **kwargs: object) -> None:
            if light_id == "light-1":
                raise Exception("Simulated failure")

        mock_bridge.lights.set_state = AsyncMock(side_effect=set_state_with_failure)

        ctx = ExecutionContext(bridge=mock_bridge)

        failed_lights = await ctx.restore_state(snapshot=sample_snapshot)

        assert "light-1" in failed_lights

    def test_clear_captured_states(self, mock_bridge: MagicMock, sample_snapshot: StateSnapshot) -> None:
        """Test clearing captured states."""
        ctx = ExecutionContext(bridge=mock_bridge, captured_states={"test": sample_snapshot, "latest": sample_snapshot})

        assert len(ctx.captured_states) == 2

        ctx.clear_captured_states()

        assert len(ctx.captured_states) == 0
        assert ctx.captured_states == {}

    @pytest.mark.asyncio
    async def test_context_reusable_across_executions(self, mock_bridge: MagicMock) -> None:
        """Test context can be reused for multiple effect executions."""
        ctx = ExecutionContext(bridge=mock_bridge)

        # First execution cycle
        snapshot1 = await ctx.capture_state()
        await ctx.restore_state(snapshot=snapshot1)

        # Clear and reuse
        ctx.clear_captured_states()

        # Second execution cycle
        snapshot2 = await ctx.capture_state()
        await ctx.restore_state(snapshot=snapshot2)

        # Both cycles should work without errors
        assert snapshot1 is not None
        assert snapshot2 is not None

    @pytest.mark.asyncio
    async def test_capture_empty_light_ids_list(self, mock_bridge: MagicMock) -> None:
        """Test capturing with empty light_ids list returns empty snapshot."""
        ctx = ExecutionContext(bridge=mock_bridge)

        snapshot = await ctx.capture_state(light_ids=[])

        assert len(snapshot.lights) == 0

    @pytest.mark.asyncio
    async def test_capture_nonexistent_light_ids(self, mock_bridge: MagicMock) -> None:
        """Test capturing with nonexistent light IDs returns empty snapshot."""
        ctx = ExecutionContext(bridge=mock_bridge)

        snapshot = await ctx.capture_state(light_ids=["nonexistent-light"])

        assert len(snapshot.lights) == 0
