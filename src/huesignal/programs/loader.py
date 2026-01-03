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
        raise ValueError(
            "YAML root must be a dictionary.\n"
            "Expected format:\n"
            "  name: my-program\n"
            "  tracks: [...]\n"
            "\nUse 'huesignal program format' for complete reference."
        )

    if "name" not in data:
        raise ValueError(
            "Missing required field: 'name'\n"
            "Add a program name at the top of your YAML file:\n"
            "  name: my-program\n"
            "\nUse 'huesignal program template notification' for a starter template."
        )

    if "tracks" not in data:
        raise ValueError(
            "Missing required field: 'tracks'\n"
            "Add at least one track definition:\n"
            "  tracks:\n"
            "    - light: desk-light\n"
            "      steps: [...]\n"
            "\nUse 'huesignal program template notification' for a starter template."
        )

    # Parse program
    name: str = data["name"]  # type: ignore[assignment]
    description: str = data.get("description", "")  # type: ignore[assignment]

    if not isinstance(name, str):
        raise ValueError("Field 'name' must be a string")

    if not isinstance(description, str):
        raise ValueError("Field 'description' must be a string")

    # Parse tracks
    tracks_data: list[Any] = data["tracks"]  # type: ignore[assignment]
    if not isinstance(tracks_data, list):
        raise ValueError("Field 'tracks' must be a list")

    if not tracks_data:
        raise ValueError("Program must have at least one track")

    tracks: list[LightTrack] = []
    for i, track_data in enumerate(tracks_data):  # type: ignore[arg-type]
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
        raise ValueError(
            "Track must be a dictionary.\n"
            "Expected format:\n"
            "  - light: desk-light\n"
            "    steps: [...]\n"
            "\nUse 'huesignal program format' for complete reference."
        )

    if "light" not in data:
        raise ValueError(
            "Track missing required field: 'light'\n"
            "Specify which light this track controls:\n"
            "  - light: desk-light\n"
            "    steps: [...]\n"
            "\nUse 'huesignal lights list' to see available light names."
        )

    light_pattern: str = data["light"]  # type: ignore[assignment]
    if not isinstance(light_pattern, str):
        raise ValueError(
            "Field 'light' must be a string (light name).\n"
            "Example:\n"
            "  light: desk-light\n"
            "\nUse 'huesignal lights list' to see available names."
        )

    if "steps" not in data:
        raise ValueError(
            "Track missing required field: 'steps'\n"
            "Add a list of steps for this track:\n"
            "  steps:\n"
            "    - effect: pulse\n"
            "      options:\n"
            "        color: green\n"
            "\nUse 'huesignal program format' for all step types."
        )

    steps_data: list[Any] = data["steps"]  # type: ignore[assignment]
    if not isinstance(steps_data, list):
        raise ValueError("Field 'steps' must be a list")

    if not steps_data:
        raise ValueError("Track must have at least one step")

    # Parse steps and calculate start times
    # Steps can have explicit start_ms for parallel execution
    steps: list[TimelineStep] = []
    current_time_ms = 0

    for i, step_data in enumerate(steps_data):  # type: ignore[arg-type]
        try:
            step, timeline_advance = _parse_step(step_data, current_time_ms)
            steps.append(step)
            # Only advance timeline if step doesn't have explicit start_ms
            # (timeline_advance will be 0 for explicitly positioned steps)
            current_time_ms += timeline_advance
        except ValueError as e:
            raise ValueError(f"Error in step {i}: {e}") from e

    return LightTrack(light_pattern=light_pattern, steps=steps)


def _parse_step(data: Any, current_time_ms: int) -> tuple[TimelineStep, int]:
    """Parse a single step from YAML data.

    Args:
        data: Step data dictionary
        current_time_ms: Current timeline position in milliseconds

    Returns:
        Tuple of (TimelineStep, timeline_advance) where timeline_advance is how
        much time this step advances the timeline. If start_ms is explicit,
        timeline_advance is 0 (step doesn't advance sequential timeline).

    Raises:
        ValueError: If step data is invalid

    Note:
        Steps can specify explicit `start_ms` for parallel execution within a track.
        When start_ms is provided, the step starts at that absolute time and does
        not advance the sequential timeline. This enables parallel steps:

        steps:
          - start_ms: 0
            effect: pulse
            duration_ms: 2000
          - start_ms: 0          # Runs in parallel with above!
            effect: breathe
            duration_ms: 2000
          - effect: rainbow      # Starts at 0ms (after parallel steps)
            duration_ms: 1000
    """
    if not isinstance(data, dict):
        raise ValueError("Step must be a dictionary")

    # Check for explicit start_ms (enables parallel execution)
    explicit_start_ms: int | None = None
    if "start_ms" in data:
        explicit_start_ms = data["start_ms"]  # type: ignore[assignment]
        if not isinstance(explicit_start_ms, int) or explicit_start_ms < 0:
            raise ValueError("Field 'start_ms' must be a non-negative integer")

    # Determine step type and parse action
    if "effect" in data:
        action, duration = _parse_effect_action(data)  # type: ignore[arg-type]
    elif "wait" in data:
        action, duration = _parse_wait_action(data)  # type: ignore[arg-type]
    elif "set" in data:
        action, duration = _parse_set_action(data)  # type: ignore[arg-type]
    else:
        raise ValueError(
            "Step must have one of: 'effect', 'wait', or 'set'\n"
            "\n"
            "Effect step:\n"
            "  - effect: pulse\n"
            "    options:\n"
            "      color: green\n"
            "\n"
            "Wait step:\n"
            "  - wait: 500\n"
            "\n"
            "Set step:\n"
            "  - set:\n"
            "      on: true\n"
            "      brightness: 200\n"
            "\n"
            "Use 'huesignal program format' for complete reference."
        )

    # Get explicit duration if provided (overrides inferred duration)
    if "duration_ms" in data:
        explicit_duration: int = data["duration_ms"]  # type: ignore[assignment]
        if not isinstance(explicit_duration, int) or explicit_duration < 0:
            raise ValueError("Field 'duration_ms' must be a non-negative integer")
        duration = explicit_duration

    # Determine actual start time and timeline advance
    if explicit_start_ms is not None:
        # Explicit positioning: use provided start_ms, don't advance timeline
        start_ms = explicit_start_ms
        timeline_advance = 0
    else:
        # Sequential: use current timeline position, advance by duration
        start_ms = current_time_ms
        timeline_advance = duration

    step = TimelineStep(start_ms=start_ms, duration_ms=duration, action=action)
    return step, timeline_advance


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
        raise ValueError(
            f"Unknown effect name: '{effect_name}'\n"
            "\n"
            "Available effects: pulse, breathe, blink, rainbow\n"
            "\n"
            "Example:\n"
            "  - effect: pulse\n"
            "    options:\n"
            "      color: green\n"
            "      brightness: 0.8\n"
            "\n"
            "Use 'huesignal effect list' to see all effects.\n"
            "Use 'huesignal effect params <name>' for effect-specific parameters."
        )

    # Parse effect options/parameters
    parameters: dict[str, Any] = data.get("options", {})  # type: ignore[assignment]

    # Infer duration (will be overridden if duration_ms is specified)
    inferred_duration: int = data.get("duration_ms", 1000)

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
        raise ValueError(
            "Field 'wait' must be a non-negative integer (milliseconds)\n"
            "\n"
            "Example:\n"
            "  - wait: 500     # Pause for 500 milliseconds\n"
            "  - wait: 1000    # Pause for 1 second\n"
            "\n"
            "Typical range: 100-2000ms"
        )

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
    on: bool = set_data.get("on", True)  # type: ignore[assignment]
    brightness: int | None = set_data.get("brightness")  # type: ignore[assignment]
    color: str | list[Any] | None = set_data.get("color")  # type: ignore[assignment]
    transition_ms: int = set_data.get("transition_ms", 0)  # type: ignore[assignment]

    # Validate types
    if not isinstance(on, bool):
        raise ValueError("Field 'on' must be a boolean")

    if brightness is not None and (not isinstance(brightness, int) or brightness < 1 or brightness > 254):
        raise ValueError(
            "Field 'brightness' must be an integer between 1 and 254\n"
            "\n"
            "Example:\n"
            "  set:\n"
            "    brightness: 127  # Half brightness (1-254 range)\n"
            "    brightness: 200  # ~80% brightness\n"
            "\n"
            "Use 'huesignal effect info' for brightness format reference."
        )

    if color is not None and not isinstance(color, (str, list)):
        raise ValueError("Field 'color' must be a string (hex/name) or list [x, y]")

    if not isinstance(transition_ms, int) or transition_ms < 0:
        raise ValueError("Field 'transition_ms' must be a non-negative integer")

    # Convert color list to tuple if needed
    color_final: str | tuple[Any, Any] | None = None
    if isinstance(color, list):
        if len(color) != 2:  # type: ignore[arg-type]
            raise ValueError("Field 'color' as list must have exactly 2 elements [x, y]")
        color_final = tuple(color)  # type: ignore[assignment]
    elif isinstance(color, str):
        color_final = color

    # Duration is the transition time
    duration = transition_ms

    action = SetAction(
        on=on,
        brightness=brightness,
        color=color_final,
        transition_ms=transition_ms,
    )
    return action, duration
