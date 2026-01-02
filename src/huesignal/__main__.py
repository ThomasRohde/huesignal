"""Main CLI entry point for huesignal."""

import sys

from huesignal.cli import cli


def main() -> int:
    """Main entry point for the huesignal CLI."""
    try:
        cli()
        return 0
    except SystemExit as e:
        # Typer may call sys.exit(), so we need to catch and re-raise
        return e.code if isinstance(e.code, int) else 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
