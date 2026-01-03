"""Execution context for effect execution."""

from dataclasses import dataclass, field

from aiohue.v2 import HueBridgeV2

from huesignal.state import StateSnapshot, capture_state, restore_state


@dataclass
class ExecutionContext:
    """Shared context for effect execution.

    Wraps the bridge connection and provides state management
    for capturing and restoring light states during effect execution.

    Attributes:
        bridge: HueBridgeV2 bridge connection
        captured_states: Dictionary mapping light IDs to their captured states
    """

    bridge: HueBridgeV2
    captured_states: dict[str, StateSnapshot] = field(default_factory=dict)

    async def capture_state(self, light_ids: list[str] | None = None) -> StateSnapshot:
        """Capture current state of specified lights.

        If light_ids is None, captures state of all lights on the bridge.
        The captured state is stored in the context for later restoration.

        Args:
            light_ids: Optional list of light IDs to capture. If None, captures all lights.

        Returns:
            StateSnapshot containing captured light states
        """
        # Capture full state from bridge
        full_snapshot = await capture_state(self.bridge)

        # If specific light IDs requested, filter the snapshot
        if light_ids is not None:
            filtered_lights = {
                light_id: state for light_id, state in full_snapshot.lights.items() if light_id in light_ids
            }
            snapshot = StateSnapshot(lights=filtered_lights)
        else:
            snapshot = full_snapshot

        # Store captured state keyed by a snapshot identifier
        # For simplicity, we use "latest" as the key
        # Future enhancement could support multiple named snapshots
        self.captured_states["latest"] = snapshot

        return snapshot

    async def restore_state(
        self, snapshot: StateSnapshot | None = None, skip_lights: list[str] | None = None
    ) -> list[str]:
        """Restore lights to captured state.

        If snapshot is None, restores to the most recently captured state
        stored in the context.

        Args:
            snapshot: StateSnapshot to restore. If None, uses most recent capture.
            skip_lights: Optional list of light IDs to skip during restoration.

        Returns:
            List of light IDs that failed to restore

        Raises:
            ValueError: If snapshot is None and no state has been captured
        """
        # Use provided snapshot or fall back to latest captured state
        if snapshot is None:
            if "latest" not in self.captured_states:
                raise ValueError("No state has been captured. Call capture_state() first.")
            snapshot = self.captured_states["latest"]

        # Restore state using the state module
        failed_lights = await restore_state(self.bridge, snapshot, skip_lights)

        return failed_lights

    def clear_captured_states(self) -> None:
        """Clear all captured states from the context.

        Useful for resetting the context between effect executions.
        """
        self.captured_states.clear()
