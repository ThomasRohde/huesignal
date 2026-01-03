"""Scheduler for parallel program execution.

Executes multi-track programs with proper timing and parallel light control.
"""

import asyncio
import fnmatch
import logging
from dataclasses import dataclass, field

from huesignal.effects.base import EffectOptions, get_effect_class
from huesignal.effects.context import ExecutionContext
from huesignal.effects.primitives import SetState
from huesignal.programs.timeline import (
    EffectAction,
    LightTrack,
    Program,
    SetAction,
    TimelineStep,
    WaitAction,
)

logger = logging.getLogger(__name__)


@dataclass
class TrackResult:
    """Result of executing a single track.

    Attributes:
        light_pattern: The original light pattern from the track
        light_ids: Resolved light IDs for this track
        failed_lights: Light IDs that failed during execution
        errors: List of error messages encountered
    """

    light_pattern: str
    light_ids: list[str] = field(default_factory=lambda: [])
    failed_lights: list[str] = field(default_factory=lambda: [])
    errors: list[str] = field(default_factory=lambda: [])


@dataclass
class ProgramResult:
    """Result of executing a program.

    Attributes:
        program_name: Name of the executed program
        track_results: Results for each track
        total_failed_lights: Combined list of all failed light IDs
        restoration_failures: Light IDs that failed to restore
    """

    program_name: str
    track_results: list[TrackResult] = field(default_factory=lambda: [])
    total_failed_lights: list[str] = field(default_factory=lambda: [])
    restoration_failures: list[str] = field(default_factory=lambda: [])

    @property
    def success(self) -> bool:
        """Return True if no failures occurred."""
        return len(self.total_failed_lights) == 0 and len(self.restoration_failures) == 0


class Scheduler:
    """Scheduler for executing multi-track programs.

    Executes programs with proper timing, parallel track execution,
    and state restoration.

    Attributes:
        ctx: ExecutionContext with bridge connection and state management
    """

    def __init__(self, ctx: ExecutionContext):
        """Initialize the scheduler.

        Args:
            ctx: ExecutionContext wrapping the bridge connection
        """
        self.ctx = ctx

    def resolve_light_pattern(self, pattern: str) -> list[str]:
        """Resolve a light pattern to a list of light IDs.

        Supports wildcards (e.g., "office-*") using fnmatch.

        Args:
            pattern: Light name or pattern with wildcards

        Returns:
            List of matching light IDs
        """
        bridge = self.ctx.bridge
        matched_ids: list[str] = []

        # Build light ID to name mapping from devices
        for device in bridge.devices.items:
            if hasattr(device, "services") and hasattr(device, "metadata"):
                device_name = device.metadata.name
                for service in device.services:
                    if service.rtype.value == "light":
                        light_id = service.rid
                        # Check if pattern matches (case-insensitive)
                        if fnmatch.fnmatch(device_name.lower(), pattern.lower()):
                            matched_ids.append(light_id)

        return matched_ids

    async def _execute_set_action(
        self,
        action: SetAction,
        light_ids: list[str],
    ) -> list[str]:
        """Execute a SetAction on specified lights.

        Args:
            action: SetAction to execute
            light_ids: Light IDs to apply action to

        Returns:
            List of light IDs that failed
        """
        failed: list[str] = []

        set_state = SetState(
            on=action.on,
            brightness=action.brightness,
            color=action.color if isinstance(action.color, str) else None,
            transition_ms=action.transition_ms,
        )

        for light_id in light_ids:
            result = await set_state.execute(self.ctx.bridge, light_id)
            if not result.success:
                failed.append(light_id)
                logger.warning(f"Failed to set state on {light_id}: {result.error}")

        return failed

    async def _execute_effect_action(
        self,
        action: EffectAction,
        light_ids: list[str],
    ) -> list[str]:
        """Execute an EffectAction on specified lights.

        Args:
            action: EffectAction to execute
            light_ids: Light IDs to apply action to

        Returns:
            List of light IDs that failed
        """
        failed: list[str] = []

        effect_class = get_effect_class(action.effect_name)
        if effect_class is None:
            logger.error(f"Unknown effect: {action.effect_name}")
            return light_ids  # All lights failed for unknown effect

        # Extract effect parameters from action.parameters
        params = action.parameters.copy()

        # Build EffectOptions from params
        options = EffectOptions(
            duration_ms=params.pop("duration_ms", 500),
            brightness=params.pop("brightness", None),
            color=params.pop("color", None),
            restore=False,  # Scheduler handles state restoration
        )

        # Create effect instance with remaining params
        try:
            effect = effect_class(
                bridge=self.ctx.bridge,
                light_ids=light_ids,
                options=options,
                **params,
            )

            # Try to use primitives if available
            primitives = effect.to_primitives()
            if primitives:
                # Execute primitives for each light
                for light_id in light_ids:
                    for primitive in primitives:
                        result = await primitive.execute(self.ctx.bridge, light_id)
                        if not result.success:
                            if light_id not in failed:
                                failed.append(light_id)
                            logger.warning(f"Primitive failed on {light_id}: {result.error}")
                        # Add small delay between primitives to avoid overwhelming the bridge
                        await asyncio.sleep(0.05)
            else:
                # Fallback to _apply_effect() - using protected method intentionally
                await effect._apply_effect()  # type: ignore[attr-defined]

        except Exception as e:
            logger.error(f"Failed to execute effect {action.effect_name}: {e}")
            failed.extend(light_ids)

        return failed

    async def _execute_wait_action(self, action: WaitAction) -> None:
        """Execute a WaitAction (simple sleep).

        Args:
            action: WaitAction to execute
        """
        await asyncio.sleep(action.duration_ms / 1000.0)

    async def _execute_step(
        self,
        step: TimelineStep,
        light_ids: list[str],
    ) -> list[str]:
        """Execute a single timeline step.

        Args:
            step: TimelineStep to execute
            light_ids: Light IDs resolved for this track

        Returns:
            List of light IDs that failed
        """
        action = step.action

        if isinstance(action, SetAction):
            return await self._execute_set_action(action, light_ids)
        elif isinstance(action, EffectAction):
            return await self._execute_effect_action(action, light_ids)
        elif isinstance(action, WaitAction):
            await self._execute_wait_action(action)
            return []
        else:
            logger.warning(f"Unknown action type: {type(action)}")
            return []

    async def _execute_track(self, track: LightTrack) -> TrackResult:
        """Execute a single light track.

        Executes steps in sequence with proper timing based on start_ms.

        Args:
            track: LightTrack to execute

        Returns:
            TrackResult with execution details
        """
        result = TrackResult(light_pattern=track.light_pattern)

        # Resolve light pattern to IDs
        light_ids = self.resolve_light_pattern(track.light_pattern)
        result.light_ids = light_ids

        if not light_ids:
            result.errors.append(f"No lights matched pattern: {track.light_pattern}")
            logger.warning(f"No lights matched pattern: {track.light_pattern}")
            return result

        # Sort steps by start_ms for proper execution order
        sorted_steps = sorted(track.steps, key=lambda s: s.start_ms)

        # Track current time for relative timing
        current_time_ms = 0

        for step in sorted_steps:
            # Wait until step's start time
            wait_ms = step.start_ms - current_time_ms
            if wait_ms > 0:
                await asyncio.sleep(wait_ms / 1000.0)
                current_time_ms = step.start_ms

            # Execute the step
            failed = await self._execute_step(step, light_ids)
            result.failed_lights.extend(lid for lid in failed if lid not in result.failed_lights)

            # Advance current time by step duration
            current_time_ms += step.duration_ms

        return result

    async def run_program(
        self,
        program: Program,
        restore_state: bool = True,
    ) -> ProgramResult:
        """Execute a program with parallel track execution.

        All tracks execute in parallel using asyncio.gather.
        Each track's steps execute sequentially with proper timing.

        Args:
            program: Program to execute
            restore_state: Whether to restore light states after execution

        Returns:
            ProgramResult with execution details and failures
        """
        result = ProgramResult(program_name=program.name)

        # Collect all light IDs from all tracks for state capture
        all_light_ids: list[str] = []
        for track in program.tracks:
            light_ids = self.resolve_light_pattern(track.light_pattern)
            all_light_ids.extend(lid for lid in light_ids if lid not in all_light_ids)

        # Capture state before execution if restore is enabled
        if restore_state and all_light_ids:
            logger.debug(f"Capturing state for {len(all_light_ids)} lights")
            await self.ctx.capture_state(all_light_ids)

        try:
            # Execute all tracks in parallel
            track_tasks = [self._execute_track(track) for track in program.tracks]

            track_results = await asyncio.gather(*track_tasks, return_exceptions=True)

            # Process results
            for track_result in track_results:
                if isinstance(track_result, BaseException):
                    error_result = TrackResult(
                        light_pattern="unknown",
                        errors=[str(track_result)],
                    )
                    result.track_results.append(error_result)
                    logger.error(f"Track execution failed: {track_result}")
                else:
                    # track_result is TrackResult
                    result.track_results.append(track_result)
                    result.total_failed_lights.extend(
                        lid for lid in track_result.failed_lights if lid not in result.total_failed_lights
                    )

        finally:
            # Restore state if enabled
            if restore_state and all_light_ids:
                logger.debug(f"Restoring state for {len(all_light_ids)} lights")
                try:
                    restoration_failures = await self.ctx.restore_state()
                    result.restoration_failures = restoration_failures
                except ValueError as e:
                    logger.error(f"Failed to restore state: {e}")
                    result.restoration_failures = all_light_ids

        return result
