# huesignal

A Philips Hue notification system with CLI and daemon support. Control Hue lights with state capture, effects, and automation templates.

## 60-Second Quickstart

```bash
# Install with uv (recommended)
uv pip install huesignal

# Login to your Hue bridge
huesignal auth login

# See available commands
huesignal --help
```

That's it! You can now use huesignal to control your Hue bridge and automate light effects.

## Installation

### Using uv (Recommended)

```bash
uv pip install huesignal
```

Or install from source:

```bash
git clone https://github.com/yourusername/huesignal.git
cd huesignal
uv sync
uv run huesignal --version
```

### Using pipx

```bash
pipx install huesignal
```

### Using pip

```bash
pip install huesignal
```

## Features

- **CLI Commands**: Easy-to-use command-line interface for controlling Hue lights
- **State Capture**: Save and restore light states and scenes
- **Effects**: Apply dynamic effects and transitions to your lights
- **Automation Templates**: Predefined automation samples for common scenarios
- **Keyring Integration**: Secure credential storage using system keyring

## Library Choice

huesignal uses **[aiohue](https://github.com/home-assistant-libs/aiohue)** for bridge communication.

### Why aiohue?

- **Async/await support**: Non-blocking I/O for responsive CLI and daemon operations
- **Full v2 API coverage**: Supports latest Hue Bridge API v2 endpoints
- **Active maintenance**: Part of Home Assistant ecosystem with regular updates
- **Python native**: Pure Python library with aiohttp backend
- **Well-tested**: Battle-tested in Home Assistant and other projects

### Alternative libraries considered

- **phue**: Simpler API but synchronous only, not ideal for daemon usage
- **requests**: Too low-level for Hue-specific logic
- **huepy**: Older, less active maintenance

## Commands

```bash
# Authentication
huesignal auth login              # Login to bridge and store credentials

# Lights
huesignal lights list             # List available lights
huesignal lights toggle <light>   # Toggle a light on/off

# Effects
huesignal effect apply <name>     # Apply a named effect

# Samples
huesignal samples generate        # Generate automation template samples
```

## Requirements

- Python 3.11+
- Philips Hue Bridge (with v2 API support)

## Testing

### Unit Tests

Run unit tests with:

```bash
pytest tests/
```

Unit tests use mocked fixtures and don't require a physical Hue bridge.

### Integration Tests

Integration tests require a real Hue bridge and are opt-in via environment variables.

```bash
# Set environment variables
export HUESIGNAL_BRIDGE_IP="192.168.1.100"
export HUESIGNAL_APP_KEY="your-app-key"

# Run integration tests
pytest tests/integration/
```

**Safety Warning**: Integration tests interact with physical lights and may change their state. Always:

1. Only run against bridges you control
2. Have permission to modify the lights
3. Ensure lights are in a safe location
4. Keep the `--restore` behavior enabled (default) so lights return to original state

Integration tests are skipped if environment variables are not set, so they won't accidentally interfere with CI/CD pipelines.

## Version

Check your installed version:

```bash
huesignal --version
```

## License

MIT
