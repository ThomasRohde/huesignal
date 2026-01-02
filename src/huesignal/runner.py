"""Detached process runner for fire-and-forget effects."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional


def run_detached(
    effect_name: str,
    parameters: Dict[str, Any],
    detach: bool = True,
) -> int:
    """
    Run an effect in a detached process (Windows) or synchronously.

    Args:
        effect_name: Name of the effect to run
        parameters: Parameters for the effect
        detach: If True, run in detached process; if False, run synchronously

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    if not detach:
        # Run synchronously (blocking)
        return run_effect_sync(effect_name, parameters)

    # Run in detached process
    try:
        # Create a temporary file to pass parameters
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"effect": effect_name, "parameters": parameters}, f)
            temp_file = f.name

        # Construct command to run huesignal in detached mode
        cmd = [
            sys.executable,
            "-m",
            "huesignal._runner",
            temp_file,
        ]

        # Create detached process (Windows-specific)
        if sys.platform == "win32":
            # Create detached process without console window
            subprocess.Popen(
                cmd,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            # On non-Windows, use subprocess.Popen with start_new_session
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

        return 0

    except Exception as e:
        print(f"Error starting detached runner: {e}", file=sys.stderr)
        return 1


def run_effect_sync(effect_name: str, parameters: Dict[str, Any]) -> int:
    """
    Run an effect synchronously (blocking).

    Args:
        effect_name: Name of the effect to run
        parameters: Parameters for the effect

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # This is a placeholder - actual effect logic would go here
        print(f"Running effect: {effect_name} with parameters: {parameters}")
        return 0
    except Exception as e:
        print(f"Error running effect: {e}", file=sys.stderr)
        return 1
