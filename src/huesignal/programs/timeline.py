"""Timeline data structures for multi-light choreography."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


# Action base class and concrete implementations
class Action(ABC):
    """Base class for timeline actions."""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert action to dictionary representation."""
        pass


@dataclass
class EffectAction(Action):
    """Action that applies an effect to a light or lights.

    Attributes:
        effect_name: Name of the effect to apply (e.g., "pulse", "blink")
        parameters: Effect-specific parameters as key-value pairs
    """

    effect_name: str
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "type": "effect",
            "effect_name": self.effect_name,
            "parameters": self.parameters,
        }


@dataclass
class WaitAction(Action):
    """Action that waits for a specified duration.

    Attributes:
        duration_ms: Duration to wait in milliseconds
    """

    duration_ms: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "type": "wait",
            "duration_ms": self.duration_ms,
        }


@dataclass
class SetAction(Action):
    """Action that sets light state directly.

    Attributes:
        on: Whether to turn light on or off
        brightness: Brightness level (1-254), None to keep current
        color: Color in XY format (tuple), hex string, or name
        transition_ms: Transition time in milliseconds
    """

    on: bool = True
    brightness: int | None = None
    color: tuple[float, float] | str | None = None
    transition_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "type": "set",
            "on": self.on,
            "brightness": self.brightness,
            "color": self.color,
            "transition_ms": self.transition_ms,
        }


# Timeline structures
@dataclass
class TimelineStep:
    """A single step in a light track timeline.

    Attributes:
        start_ms: Start time relative to program start (milliseconds)
        duration_ms: Duration of the step (milliseconds)
        action: Action to perform at this step
    """

    start_ms: int
    duration_ms: int
    action: Action

    @property
    def end_ms(self) -> int:
        """Calculate end time of this step."""
        return self.start_ms + self.duration_ms


@dataclass
class LightTrack:
    """Timeline track for a specific light or group of lights.

    Attributes:
        light_pattern: Light name or pattern (supports wildcards like "office-*")
        steps: List of timeline steps for this track
    """

    light_pattern: str
    steps: list[TimelineStep] = field(default_factory=list)

    def duration_ms(self) -> int:
        """Calculate total duration of this track."""
        if not self.steps:
            return 0
        return max(step.end_ms for step in self.steps)


@dataclass
class Program:
    """A multi-light choreography program.

    Attributes:
        name: Program name
        description: Human-readable description
        tracks: List of light tracks in this program
    """

    name: str
    description: str
    tracks: list[LightTrack] = field(default_factory=list)

    def total_duration_ms(self) -> int:
        """Calculate total duration of the program.

        Returns the maximum end time across all tracks.
        """
        if not self.tracks:
            return 0
        return max(track.duration_ms() for track in self.tracks)
