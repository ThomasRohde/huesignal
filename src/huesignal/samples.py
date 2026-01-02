"""Automation templates for huesignal integration."""

SAMPLES: dict[str, str] = {
    "powershell-exitcode": """# PowerShell script that sets exit code based on huesignal success
if (huesignal --bridge-ip {bridge_ip} effect apply pulse --light {light_id} -c green -b 0.7) {{
    exit 0
}} else {{
    exit 1
}}""",
    "python-exitcode": """#!/usr/bin/env python3
# Python script that calls huesignal and propagates exit code
import subprocess
import sys

result = subprocess.run(
    ["huesignal", "--bridge-ip", "{bridge_ip}", "effect", "apply", "pulse", "--light", "{light_id}", "-c", "green", "-b", "0.7"],
    capture_output=True
)
sys.exit(result.returncode)""",
    "github-actions": """# GitHub Actions workflow step for Hue notifications
- name: Notify via Philips Hue
  if: success()
  run: |
    huesignal --bridge-ip {bridge_ip} effect apply pulse --light {light_id} -c green -b 0.7
  env:
    HUE_APP_KEY: ${{{{ secrets.HUE_APP_KEY }}}}""",
    "generic-agent-wrapper": """#!/bin/bash
# Generic wrapper for running tasks with Hue notifications
BRIDGE_IP="{bridge_ip}"
LIGHT_ID="{light_id}"

# Signal task start
huesignal --bridge-ip "$BRIDGE_IP" effect apply pulse --light "$LIGHT_ID" -c blue -b 0.5

# Run the actual task
"$@"
TASK_EXIT=$?

# Signal task completion
if [ $TASK_EXIT -eq 0 ]; then
    huesignal --bridge-ip "$BRIDGE_IP" effect apply pulse --light "$LIGHT_ID" -c green -b 0.7
else
    huesignal --bridge-ip "$BRIDGE_IP" effect apply blink --light "$LIGHT_ID" -c red --count 3 -b 1.0
fi

exit $TASK_EXIT""",
    "windows-task-scheduler": """REM Windows Task Scheduler batch script
REM Run this as scheduled task to trigger Hue effects

@echo off
setlocal enabledelayedexpansion

set BRIDGE_IP={bridge_ip}
set LIGHT_ID={light_id}

REM Check time and trigger appropriate effect
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)

REM Morning effect (08:00 AM)
if !mytime! geq 0800 if !mytime! lss 0900 (
    huesignal --bridge-ip !BRIDGE_IP! effect apply breathe --light !LIGHT_ID! -c yellow -d 2000
    exit /b 0
)

REM Evening effect (6:00 PM)
if !mytime! geq 1800 if !mytime! lss 1900 (
    huesignal --bridge-ip !BRIDGE_IP! effect apply breathe --light !LIGHT_ID! -c orange -d 2000
    exit /b 0
)

exit /b 0""",
}


def get_sample(name: str, bridge_ip: str = "192.168.1.100", light_id: str = "1") -> str:
    """Get a sample template with placeholder values substituted.

    Args:
        name: Sample name
        bridge_ip: Bridge IP address to substitute
        light_id: Light ID to substitute

    Returns:
        Sample template with placeholders replaced
    """
    if name not in SAMPLES:
        raise ValueError(f"Unknown sample: {name}")

    template = SAMPLES[name]
    return template.format(bridge_ip=bridge_ip, light_id=light_id)


def list_samples() -> list[str]:
    """Get list of available sample names.

    Returns:
        List of sample names
    """
    return list(SAMPLES.keys())
