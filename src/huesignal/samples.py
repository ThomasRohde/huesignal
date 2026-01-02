"""Automation templates for huesignal integration.

All samples use cached bridge/light information where possible.
Use HUESIGNAL_LIGHT_NAME environment variable for default light.
"""

SAMPLES: dict[str, str] = {
    "coding-session-success": """# PowerShell: Signal successful coding session completion
# Uses cached bridge/light info - no manual IP needed
# Set HUESIGNAL_LIGHT_NAME env var for your preferred light

huesignal effect apply pulse -c green -b 0.8 2>$null
if ($LASTEXITCODE -eq 0) {{
    Write-Host "✓ Coding session complete - signal sent"
}} else {{
    Write-Host "⚠ huesignal not configured (run: huesignal auth login)"
}}""",
    "coding-session-error": """# PowerShell: Signal error/blocker during coding session
# Bright red blinks to grab attention when something needs review

huesignal effect apply blink -c red --count 3 2>$null
if ($LASTEXITCODE -eq 0) {{
    Write-Host "⚠ Error signal sent - check your Hue light"
}} else {{
    Write-Host "⚠ huesignal not configured"
}}""",
    "git-commit-hook": """#!/bin/bash
# Git post-commit hook - signal successful commit
# Place in .git/hooks/post-commit and chmod +x

# Uses cached config - gracefully skips if not set up
huesignal effect apply pulse -c green -b 0.7 2>/dev/null || true

exit 0""",
    "github-actions": """# GitHub Actions workflow - signal build result
# Uses secrets for authentication
name: Build with Hue Notifications

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run build
        run: npm run build
      
      - name: Signal success
        if: success()
        run: |
          pip install huesignal
          huesignal effect apply pulse -c green -b 0.8
        env:
          HUESIGNAL_APP_KEY: ${{{{ secrets.HUE_APP_KEY }}}}
          HUESIGNAL_BRIDGE_IP: ${{{{ secrets.HUE_BRIDGE_IP }}}}
          HUESIGNAL_LIGHT_NAME: build-light
      
      - name: Signal failure
        if: failure()
        run: huesignal effect apply blink -c red --count 5
        env:
          HUESIGNAL_APP_KEY: ${{{{ secrets.HUE_APP_KEY }}}}
          HUESIGNAL_BRIDGE_IP: ${{{{ secrets.HUE_BRIDGE_IP }}}}
          HUESIGNAL_LIGHT_NAME: build-light""",
    "pytest-conftest": """# pytest conftest.py - signal test results
# Add to your project's conftest.py file
import subprocess
import pytest

@pytest.hookimpl(hookwrapper=True)
def pytest_sessionfinish(session, exitstatus):
    yield
    
    # Signal based on test results
    if exitstatus == 0:
        # All tests passed - green pulse
        subprocess.run(
            ["huesignal", "effect", "apply", "pulse", "-c", "green", "-b", "0.7"],
            capture_output=True
        )
    else:
        # Tests failed - red blinks
        subprocess.run(
            ["huesignal", "effect", "apply", "blink", "-c", "red", "--count", "3"],
            capture_output=True
        )""",
    "lodestar-agent": """#!/bin/bash
# Lodestar agent workflow with visual feedback
# Uses cached huesignal config - no hardcoded IPs

AGENT_ID="my-agent"
LIGHT="${{HUESIGNAL_LIGHT_NAME:-desk-light}}"

# Function to signal events (graceful if huesignal not installed)
signal_event() {{
    local effect="$1"
    shift
    huesignal effect apply "$effect" "$@" 2>/dev/null || true
}}

# Start coding session
echo "Starting agent session..."
signal_event breathe -c blue -d 1000

# Claim a task
TASK_ID=$(lodestar_task_next | jq -r '.candidates[0].taskId')
lodestar_task_claim --task-id "$TASK_ID" --agent-id "$AGENT_ID"

# Signal task claimed
signal_event pulse -c white -b 0.5

# Do the work...
# ... your implementation here ...

# Mark task done
lodestar_task_done --task-id "$TASK_ID" --agent-id "$AGENT_ID"

# Signal completion
signal_event pulse -c green -b 0.8

echo "✓ Task $TASK_ID complete with visual confirmation" """,
    "vscode-task": """// VS Code tasks.json - Signal task completion
// Add to .vscode/tasks.json
{{
  "version": "2.0.0",
  "tasks": [
    {{
      "label": "Build with Signal",
      "type": "shell",
      "command": "npm run build && huesignal effect apply pulse -c green -b 0.8 || huesignal effect apply blink -c red --count 3",
      "problemMatcher": [],
      "presentation": {{
        "reveal": "always",
        "panel": "new"
      }}
    }},
    {{
      "label": "Test with Signal",
      "type": "shell",
      "command": "npm test && huesignal effect apply pulse -c green -b 0.7 || huesignal effect apply blink -c red --count 3",
      "problemMatcher": []
    }}
  ]
}}""",
    "python-script-wrapper": """#!/usr/bin/env python3
# Python wrapper - signal script execution result
# Uses cached huesignal config automatically
import subprocess
import sys

def signal(effect: str, color: str, **kwargs):
    \"\"\"Send huesignal (gracefully fails if not configured).\"\"\"
    cmd = ["huesignal", "effect", "apply", effect, "-c", color]
    for key, value in kwargs.items():
        cmd.extend([f"--{key.replace('_', '-')}", str(value)])
    
    subprocess.run(cmd, capture_output=True)

# Your script logic
try:
    # ... your code here ...
    result = do_work()
    
    # Signal success
    signal("pulse", "green", b=0.8)
    print("✓ Work complete - signal sent")
    sys.exit(0)
    
except Exception as e:
    # Signal error
    signal("blink", "red", count=3)
    print(f"✗ Error: {{e}}")
    sys.exit(1)

def do_work():
    # Placeholder for actual work
    return True""",
}


def get_sample(name: str) -> str:
    """Get a sample template.

    Args:
        name: Sample name

    Returns:
        Sample template (uses cached config, no placeholders needed)
    """
    if name not in SAMPLES:
        raise ValueError(f"Unknown sample: {name}")

    return SAMPLES[name]


def list_samples() -> list[str]:
    """Get list of available sample names.

    Returns:
        List of sample names
    """
    return list(SAMPLES.keys())
