# Contributing to huesignal

Thank you for your interest in contributing to huesignal! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Project Structure](#project-structure)

## Code of Conduct

This project follows a standard code of conduct. Please be respectful and constructive in all interactions.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a new branch for your feature or bugfix
4. Make your changes
5. Run tests to ensure everything works
6. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- A Philips Hue Bridge for integration testing (optional)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/huesignal.git
cd huesignal

# Install dependencies with uv (recommended)
uv sync --all-extras --dev

# Or with pip
pip install -e ".[dev]"

# Install pre-commit hooks
uv run pre-commit install
```

## Running Tests

### Unit Tests

Unit tests don't require physical Hue hardware:

```bash
# Run all unit tests
uv run pytest tests/ --ignore=tests/integration/

# Run with coverage
uv run pytest tests/ --ignore=tests/integration/ --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_effects.py -v
```

### Integration Tests

Integration tests require a real Hue Bridge and are opt-in:

```bash
# Set environment variables
export HUESIGNAL_BRIDGE_IP="192.168.1.100"
export HUESIGNAL_APP_KEY="your-app-key"

# Run integration tests
uv run pytest tests/integration/ -v
```

**Warning**: Integration tests interact with physical lights. Only run against bridges you control.

## Code Style

This project uses:

- **[Ruff](https://github.com/astral-sh/ruff)** for linting and formatting
- **Type hints** for better code clarity (encouraged but not required)
- **Docstrings** for public APIs

### Format Code

```bash
# Format code
uv run ruff format src/ tests/

# Check formatting
uv run ruff format --check src/ tests/

# Lint code
uv run ruff check src/ tests/

# Fix auto-fixable issues
uv run ruff check --fix src/ tests/
```

### Pre-commit Hooks

Pre-commit hooks automatically run formatters and linters:

```bash
# Install hooks (one-time)
uv run pre-commit install

# Run manually on all files
uv run pre-commit run --all-files
```

## Submitting Changes

### Pull Request Process

1. **Create a branch** with a descriptive name:
   ```bash
   git checkout -b feature/add-new-effect
   git checkout -b fix/resolver-ambiguity
   ```

2. **Make your changes** with clear, focused commits:
   ```bash
   git add .
   git commit -m "Add strobe effect with rate limiting"
   ```

3. **Write or update tests** for your changes

4. **Ensure all tests pass**:
   ```bash
   uv run pytest tests/ --ignore=tests/integration/
   ```

5. **Format and lint your code**:
   ```bash
   uv run ruff format src/ tests/
   uv run ruff check src/ tests/
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/add-new-effect
   ```

7. **Open a Pull Request** on GitHub with:
   - Clear description of changes
   - Reference to related issues (if any)
   - Screenshots/examples (if applicable)

### PR Guidelines

- Keep PRs focused on a single feature or fix
- Write clear commit messages
- Update documentation if needed
- Add tests for new functionality
- Ensure CI passes

## Project Structure

```
huesignal/
├── src/huesignal/           # Main package
│   ├── __init__.py
│   ├── __main__.py          # Entry point
│   ├── cli.py               # CLI commands
│   ├── auth.py              # Authentication
│   ├── discovery.py         # Bridge discovery
│   ├── hue_client.py        # Hue API client
│   ├── lights.py            # Light operations
│   ├── resolver.py          # Light name resolution
│   ├── runner.py            # Effect runner
│   ├── state.py             # State capture/restore
│   └── effects/             # Effect implementations
│       ├── base.py
│       ├── blink.py
│       ├── pulse.py
│       ├── breathe.py
│       └── rainbow.py
├── tests/                   # Test suite
│   ├── test_effects.py
│   ├── test_resolver.py
│   └── integration/         # Hardware tests
├── pyproject.toml           # Project metadata
├── README.md                # User documentation
├── PRD.md                   # Product requirements
├── CONTRIBUTING.md          # This file
└── LICENSE                  # MIT License
```

## Adding New Effects

To add a new effect:

1. Create a new file in `src/huesignal/effects/` (e.g., `fade.py`)
2. Implement the effect class inheriting from `Effect` base class
3. Register the effect in `src/huesignal/effects/__init__.py`
4. Add tests in `tests/test_effects.py`
5. Update documentation if needed

Example effect structure:

```python
from huesignal.effects.base import Effect, EffectOptions

class FadeEffect(Effect):
    """Fade effect that gradually changes brightness."""
    
    async def apply(self, light_id: str, options: EffectOptions) -> None:
        # Implementation here
        pass
```

## Questions or Issues?

- Open an issue on GitHub for bugs or feature requests
- Check existing issues before creating a new one
- Provide clear reproduction steps for bugs

## License

By contributing to huesignal, you agree that your contributions will be licensed under the MIT License.
