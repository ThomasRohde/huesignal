# huesignal 💡

[![PyPI version](https://badge.fury.io/py/huesignal.svg)](https://badge.fury.io/py/huesignal)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Visual feedback for AI agents and automation workflows.**

Turn your Philips Hue lights into a status dashboard. Perfect for coding agents to signal task progress, CI/CD pipelines to show build status, and developers who want ambient feedback without context-switching.

```bash
# Green pulse = task complete
huesignal effect apply pulse -l desk-light -c green -b 0.7

# Red blinks = error/blocker  
huesignal effect apply blink -l desk-light -c red --count 3
```

---

## ⚡ 60-Second Quickstart

```bash
# Install
uv pip install huesignal       # or: pip install huesignal

# Authenticate (press bridge link button when prompted)
huesignal auth login

# Discover your lights
huesignal lights list

# Signal success!
huesignal effect apply pulse -l "your-light-name" -c green
```

---

## 🎯 Why huesignal?

| Use Case | Example |
|----------|---------|
| **AI Agent Feedback** | Coding agents signal task claim (blue), completion (green), errors (red blink) |
| **CI/CD Visualization** | Build stages light up different colors as pipeline progresses |
| **Pomodoro Timer** | Breathing effect during focus, pulse when break starts |
| **Meeting Alerts** | Progressive brightness increase as meeting approaches |
| **Script Status** | Long-running scripts pulse when done or blink on failure |

---

## 📦 Installation

### Using uv (Recommended)

```bash
uv pip install huesignal
```

### From Source

```bash
git clone https://github.com/ThomasRohde/huesignal.git
cd huesignal
uv sync
uv run huesignal --version
```

### Using pip/pipx

```bash
pip install huesignal     # or: pipx install huesignal
```

---

## 🎨 Effects Reference

### Available Effects

| Effect | Description | Best For |
|--------|-------------|----------|
| `pulse` | Quick brightness flash | Notifications, task completion |
| `blink` | Rapid on/off toggle | Errors, alerts, attention-grabbing |
| `breathe` | Smooth fade in/out | Ambient status, "working" indicator |
| `rainbow` | Color cycle animation | Celebrations, demos |

### Common Options

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--light` | `-l` | Target light name | `-l desk-light` |
| `--color` | `-c` | Color (name or hex) | `-c green`, `-c "#FF5500"` |
| `--brightness` | `-b` | Brightness level | `-b 0.7` (70%), `-b 100` (100%) |
| `--duration` | `-d` | Effect duration (ms) | `-d 2000` |
| `--count` | | Repeat count (pulse/blink) | `--count 3` |
| `--no-restore` | | Keep final state | Don't restore original |

### Colors

**Named colors:** `red`, `green`, `blue`, `yellow`, `orange`, `purple`, `pink`, `cyan`, `white`, `magenta`

**Semantic colors:** `success` (green), `error` (red), `warning` (orange), `info` (blue), `working` (sky blue), `celebration` (gold)

**Hex codes:** `#FF0000`, `#00FF00`, `#0000FF`, etc.

### Brightness Formats

```bash
-b 75       # Percentage (0-100)
-b 0.75     # Decimal (0.0-1.0)  
-b 191      # Raw Hue value (1-254)
```

---

## 🤖 Agent Workflow Patterns

Perfect for AI coding agents to provide visual status:

```bash
# Task claimed - blue pulse
huesignal effect apply pulse -c blue -b 0.5 2>/dev/null || true

# Task complete - green pulse
huesignal effect apply pulse -c green -b 0.7 2>/dev/null || true

# Error/blocker - red blinks
huesignal effect apply blink -c red --count 3 -b 1.0 2>/dev/null || true

# Working/thinking - slow breathe
huesignal effect apply breathe -c working -d 3000 2>/dev/null || true

# Celebration - rainbow!
huesignal effect apply rainbow -d 5000 2>/dev/null || true
```

> **Tip:** Append `2>/dev/null || true` in scripts to gracefully handle missing bridge/lights.

### Environment Variable

Set a default light to avoid `-l` on every command:

```bash
export HUESIGNAL_LIGHT_NAME="desk-light"
huesignal effect apply pulse -c green    # Uses desk-light automatically
```

---

## 🎼 YAML Programs (Symphony of Lights)

Create choreographed multi-light sequences with YAML programs.

### Quick Start

```bash
# Run a program
huesignal run examples/celebration.yaml

# Validate without executing
huesignal run my-program.yaml --validate

# Preview timing (requires bridge)
huesignal run my-program.yaml --dry-run
```

### YAML Schema

```yaml
name: program-name              # Required: Unique identifier
description: What this does     # Optional: Human-readable description

tracks:                         # Required: List of light tracks
  - light: "light-name"         # Required: Light name or pattern (supports *)
    steps:                      # Required: Sequence of actions
      
      # Effect step - apply a visual effect
      - effect: pulse           # Effect name: pulse, blink, breathe, rainbow
        options:                # Optional: Effect-specific options
          color: green
          brightness: 200
          count: 2
        duration_ms: 1500       # Step duration in milliseconds
      
      # Wait step - pause the timeline
      - wait: 500               # Pause in milliseconds
      
      # Set step - direct state change
      - set:
          on: true              # Power state
          brightness: 150       # 1-254
          color: "#FF6600"      # Hex, name, or [x, y] tuple
          transition_ms: 300    # Fade duration
```

### Example: Celebration Sequence

```yaml
name: celebration
description: Victory dance for completed milestones

tracks:
  - light: desk-light
    steps:
      - effect: pulse
        options:
          color: success
          count: 3
        duration_ms: 2000
      - wait: 200
      - effect: rainbow
        duration_ms: 4000

  - light: ambient-light
    steps:
      - wait: 500
      - effect: breathe
        options:
          color: celebration
        duration_ms: 5000
```

See the [`examples/`](examples/) directory for more programs.

---

## 📋 Command Reference

### Authentication

```bash
huesignal auth login                    # Pair with bridge (stores credentials)
huesignal auth login --bridge-ip 192.168.1.100  # Specify bridge IP
```

### Lights

```bash
huesignal lights list                   # Show all lights with status
huesignal lights list --filter desk     # Filter by name
huesignal lights show <name>            # Detailed light info
huesignal lights on <name>              # Turn on
huesignal lights on <name> -b 50        # Turn on at 50% brightness
huesignal lights off <name>             # Turn off
```

### Effects

```bash
huesignal effect list                   # Show available effects
huesignal effect params <name>          # Show effect parameters
huesignal effect apply <name> [options] # Apply effect
huesignal effect play <file.yaml>       # Run YAML program
```

### Programs (Shorthand)

```bash
huesignal run <file.yaml>               # Execute YAML program
huesignal run <file.yaml> --validate    # Validate only (no bridge needed)
huesignal run <file.yaml> --dry-run     # Preview without execution
```

### Samples

```bash
huesignal samples list                  # List automation templates
huesignal samples show <name>           # Display a sample
```

### Utilities

```bash
huesignal doctor                        # Diagnostic checks
huesignal doctor --verbose              # Detailed diagnostics
huesignal cache clear                   # Clear cached data
huesignal --explain                     # Comprehensive usage examples
```

---

## 🧪 Testing

### Unit Tests

```bash
pytest tests/                           # Mocked, no bridge required
```

### Integration Tests

```bash
export HUESIGNAL_BRIDGE_IP="192.168.1.100"
export HUESIGNAL_APP_KEY="your-app-key"
pytest tests/integration/               # Requires real bridge
```

> ⚠️ Integration tests modify light state. Only run against your own bridge.

---

## 🔧 Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `HUESIGNAL_LIGHT_NAME` | Default light for commands when `-l` is omitted |
| `HUESIGNAL_BRIDGE_IP` | Override bridge IP (skips discovery) |
| `HUESIGNAL_APP_KEY` | Override app key (skips keyring) |

### Credential Storage

Credentials are stored securely in Windows Credential Manager (or system keyring on macOS/Linux).

---

## 📚 More Resources

- **[EFFECTS_PRD.md](EFFECTS_PRD.md)** — Technical specification for the effect programming model
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — Contribution guidelines
- **[AGENTS.md](AGENTS.md)** — Multi-agent coordination with Lodestar

---

## 🏗️ Architecture

huesignal uses **[aiohue](https://github.com/home-assistant-libs/aiohue)** for async bridge communication:

- **Full Hue API v2 support** — Latest bridge features
- **Async/await** — Non-blocking for responsive CLI
- **Battle-tested** — Powers Home Assistant

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

<p align="center">
  <strong>Make your lights dance. 💡✨</strong>
</p>
