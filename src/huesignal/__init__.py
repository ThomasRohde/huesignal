"""Philips Hue notification system with CLI and daemon."""

try:
    from importlib.metadata import version as get_version

    __version__ = get_version("huesignal")
except Exception:
    # Fallback for development installations
    __version__ = "0.1.3"
