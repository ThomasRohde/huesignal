"""Programs package for multi-light choreography."""

from huesignal.programs.loader import load_program
from huesignal.programs.scheduler import (
    ProgramResult,
    Scheduler,
    TrackResult,
)
from huesignal.programs.timeline import (
    Action,
    EffectAction,
    LightTrack,
    Program,
    SetAction,
    TimelineStep,
    WaitAction,
)

__all__ = [
    "Action",
    "EffectAction",
    "WaitAction",
    "SetAction",
    "TimelineStep",
    "LightTrack",
    "Program",
    "Scheduler",
    "TrackResult",
    "ProgramResult",
    "load_program",
]
