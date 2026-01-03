"""YAML program loader for multi-light choreography."""

from pathlib import Path
from typing import Any

import yaml

from huesignal.effects.base import get_effect_class
from huesignal.programs.timeline import (
    EffectAction,
    LightTrack,
    Program,
    SetAction,
    TimelineStep,
    WaitAction,
)


def load_program(path: str | Path) -> Program:
    """Load a program from a YAML file.

    Args:
        path: Path to the YAML file

    Returns:
        Parsed Program object

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the YAML is invalid or missing required fields

    Example YAML format:
        name: celebration
        description: Success celebration sequence

        tracks:
          - light: office-light
            steps:
              - effect: pulse
                options:
                  color: green
                  brightness: 254
                  count: 2
                duration_ms: 2000
              - wait: 500
              - effect: rainbow
                duration_ms: 3000
    """
    path_obj = Path(path)

    # Check file exists
    if not path_obj.exists():
        raise FileNotFoundError(f"Program file not found: {path}")

    # Load and parse YAML
    try:
        with open(path_obj, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML syntax: {e}") from e

    # Validate required top-level fields
    if not isinstance(data, dict):
        raise ValueError("YAML root must be a dictionary")

    if "name" not in data:
        raise ValueError("Missing required field: 'name'")

    if "tracks" not in data:
        raise ValueError("Missing required field: 'tracks'")

    # Parse program
    name = data["name"]
    description = data.get("description", "")

    if not isinstance(name, str):
        raise ValueError("Field 'name' must be a string")

    if not isinstance(description, str):
        raise ValueError("Field 'description' must be a string")

    # Parse tracks
    tracks_data = data["tracks"]
    if not isinstance(tracks_data, list):
        raise ValueError("Field 'tracks' must be a list")

    if not tracks_data:
        raise ValueError("Program must have at least one track")

    tracks = []
    for i, track_data in enumerate(tracks_data):
        try:
            track = _parse_track(track_data)
            tracks.append(track)
        except ValueError as e:
            raise ValueError(f"Error in track {i}: {e}") from e

    return Program(name=name, description=description, tracks=tracks)


def _parse_track(data: Any) -> LightTrack:
    """Parse a single track from YAML data.

    Args:
        data: Track data dictionary

    Returns:
        LightTrack object

    Raises:
        ValueError: If track data is invalid
    """
    if not isinstance(data, dict):
        raise ValueError("Track must be a dictionary")

    if "light" not in data:
        raise ValueError("Track missing required field: 'light'")

    light_pattern = data["light"]
    if not isinstance(light_pattern, str):
        raise ValueError("Field 'light' must be a string")

    if "steps" not in data:
        raise ValueError("Track missing required field: 'steps'")

    steps_data = data["steps"]
    if not isinstance(steps_data, list):
        raise ValueError("Field 'steps' must be a list")

    if not steps_data:
        raise ValueError("Track must have at least one step")

    # Parse steps and calculate start times
    steps = []
    current_time_ms = 0

    for i, step_data in enumerate(steps_data):
        try:
            step, duration = _parse_step(step_data, current_time_ms)
            steps.append(step)
            current_time_ms += duration
        except ValueError as e:
            raise ValueError(f"Error in step {i}: {e}") from e

    return LightTrack(light_pattern=light_pattern, steps=steps)


def _parse_step(data: Any, start_ms: int) -> tuple[TimelineStep, int]:
    """Parse a single step from YAML data.

    Args:
        data: Step data dictionary
        start_ms: Start time for this step in milliseconds

    Returns:
        Tuple of (TimelineStep, duration_ms) where duration_ms is how much time
        this step advances the timeline

    Raises:
        ValueError: If step data is invalid
    """
    if not isinstance(data, dict):
        raise ValueError("Step must be a dictionary")

    # Determine step type and parse action
    if "effect" in data:
        action, duration = _parse_effect_action(data)
    elif "wait" in data:
        action, duration = _parse_wait_action(data)
    elif "set" in data:
        action, duration = _parse_set_action(data)
    else:
        raise ValueError("Step must have one of: 'effect', 'wait', or 'set'")

    # Get explicit duration if provided (overrides inferred duration)
    if "duration_ms" in data:
        explicit_duration = data["duration_ms"]
        if not isinstance(explicit_duration, int) or explicit_duration < 0:
            raise ValueError("Field 'duration_ms' must be a non-negative integer")
        duration = explicit_duration

    step = TimelineStep(start_ms=start_ms, duration_ms=duration, action=action)
    return step, duration


def _parse_effect_action(data: dict[str, Any]) -> tuple[EffectAction, int]:
    """Parse an effect action from step data.

    Args:
        data: Step data with 'effect' field

    Returns:
        Tuple of (EffectAction, inferred_duration_ms)

    Raises:
        ValueError: If effect data is invalid or effect name is unknown
    """
    effect_name = data["effect"]
    if not isinstance(effect_name, str):
        raise ValueError("Field 'effect' must be a string")

    # Validate effect name against registry
    effect_class = get_effect_class(effect_name)
    if effect_class is None:
        raise ValueError(f"Unknown effect name: '{effect_name}'. Effect not found in registry.")

    # Parse effect options/parameters
    parameters = data.get("options", {})
    if not isinstance(parameters, dict):
        raise ValueError("Field 'options' must be a dictionary")

    # Infer duration (will be overridden if duration_ms is specified)
    inferred_duration = data.get("duration_ms", 1000)

    action = EffectAction(effect_name=effect_name, parameters=parameters)
    return action, inferred_duration


def _parse_wait_action(data: dict[str, Any]) -> tuple[WaitAction, int]:
    """Parse a wait action from step data.

    Args:
        data: Step data with 'wait' field

    Returns:
        Tuple of (WaitAction, duration_ms)

    Raises:
        ValueError: If wait data is invalid
    """
    wait_ms = data["wait"]
    if not isinstance(wait_ms, int) or wait_ms < 0:
        raise ValueError("Field 'wait' must be a non-negative integer (milliseconds)")

    action = WaitAction(duration_ms=wait_ms)
    return action, wait_ms


def _parse_set_action(data: dict[str, Any]) -> tuple[SetAction, int]:
    """Parse a set action from step data.

    Args:
        data: Step data with 'set' field

    Returns:
        Tuple of (SetAction, inferred_duration_ms)

    Raises:
        ValueError: If set data is invalid
    """
    set_data = data["set"]
    if not isinstance(set_data, dict):
        raise ValueError("Field 'set' must be a dictionary")

    # Parse set state fields
    on = set_data.get("on", True)
    brightness = set_data.get("brightness")
    color = set_data.get("color")
    transition_ms = set_data.get("transition_ms", 0)

    # Validate types
    if not isinstance(on, bool):
        raise ValueError("Field 'on' must be a boolean")

    if brightness is not None and (not isinstance(brightness, int) or brightness < 1 or brightness > 254):
        raise ValueError("Field 'brightness' must be an integer between 1 and 254")

    if color is not None and not isinstance(color, (str, list)):
        raise ValueError("Field 'color' must be a string (hex/name) or list [x, y]")

    if not isinstance(transition_ms, int) or transition_ms < 0:
        raise ValueError("Field 'transition_ms' must be a non-negative integer")

    # Convert color list to tuple if needed
    if isinstance(color, list):
        if len(color) != 2:
            raise ValueError("Field 'color' as list must have exactly 2 elements [x, y]")
        color = tuple(color)

    # Duration is the transition time
    duration = transition_ms

    action = SetAction(
        on=on,
        brightness=brightness,
        color=color,
        transition_ms=transition_ms,
    )
    return action, duration
