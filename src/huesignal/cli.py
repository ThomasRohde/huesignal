"""CLI structure for huesignal using Typer."""

import asyncio
import sys

import typer

from huesignal import __version__
from huesignal.auth import AuthError, get_app_key, store_app_key
from huesignal.auth import login as auth_login
from huesignal.cache import get_cache, get_default_bridge_ip, set_default_bridge_ip
from huesignal.cli_examples import EXPLAIN_TEXT
from huesignal.discovery import discover_bridges, discover_bridges_mdns
from huesignal.doctor import run_doctor
from huesignal.effects import list_effects
from huesignal.hue_client import HueClient, HueConnectionError
from huesignal.lights import list_lights, show_light
from huesignal.logging_config import setup_logging
from huesignal.samples import get_sample, list_samples

app = typer.Typer(
    help="""Philips Hue notification system for visual feedback from AI agents and automation.
    
    Use huesignal to control Hue lights for status signals, notifications, and effects.
    Perfect for coding agents to provide visual feedback on task status.
    
    Quick Start:
      huesignal auth login              # First time setup
      huesignal lights list             # Discover your lights
      huesignal effect apply pulse -l desk-light -c green -b 100  # Signal success
    
    For detailed examples: huesignal --explain
    """,
    no_args_is_help=True,
)

# Global options
bridge_ip: str | None = typer.Option(None, "--bridge-ip", help="IP address of Philips Hue bridge")
verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output")
quiet: bool = typer.Option(False, "--quiet", help="Suppress non-essential output")
json_output: bool = typer.Option(False, "--json", help="Output in JSON format")
trace: bool = typer.Option(False, "--trace", help="Enable trace mode with stack traces")
timeout_ms: int = typer.Option(30000, "--timeout-ms", help="Timeout for bridge operations in milliseconds")


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(__version__)
        raise typer.Exit()


def explain_callback(value: bool) -> None:
    """Print comprehensive usage examples for coding agents and exit."""
    if value:
        typer.echo(EXPLAIN_TEXT)
        raise typer.Exit()


class GlobalOptions:
    """Container for global CLI options."""

    def __init__(
        self,
        bridge_ip: str | None = None,
        verbose: bool = False,
        quiet: bool = False,
        json_output: bool = False,
        trace: bool = False,
        timeout_ms: int = 30000,
    ):
        self.bridge_ip = bridge_ip
        self.verbose = verbose
        self.quiet = quiet
        self.json_output = json_output
        self.trace = trace
        self.timeout_ms = timeout_ms


def get_bridge_ip(
    provided_ip: str | None = None,
    quiet: bool = False,
) -> str:
    """Get bridge IP, checking cache before discovery.

    Args:
        provided_ip: Explicitly provided bridge IP (takes precedence)
        quiet: Suppress output messages

    Returns:
        Bridge IP address

    Raises:
        typer.Exit: If no bridges found
    """
    # Use provided IP if available
    if provided_ip:
        return provided_ip

    # Check cache for default bridge IP
    cached_ip = get_default_bridge_ip()
    if cached_ip:
        if not quiet:
            typer.echo(f"Using cached bridge: {cached_ip}")
        return cached_ip

    # Perform discovery
    if not quiet:
        typer.echo("Discovering bridges...")
    bridges = asyncio.run(discover_bridges())
    if not bridges:
        if not quiet:
            typer.echo("Attempting mDNS discovery...")
        bridges = asyncio.run(discover_bridges_mdns(timeout=2.0))

    if not bridges:
        typer.secho(
            "Error: No bridges found. Please specify --bridge-ip or ensure your Hue Bridge is online.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    # Get first bridge IP
    bridge_ip = bridges[0].get("internalipaddress")
    if not quiet:
        typer.echo(f"Using bridge: {bridge_ip}")

    # Cache the discovered IP for future use
    set_default_bridge_ip(bridge_ip)

    return bridge_ip


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", callback=version_callback, is_eager=True, help="Show version and exit"
    ),
    explain: bool = typer.Option(
        False,
        "--explain",
        callback=explain_callback,
        is_eager=True,
        help="Show comprehensive usage examples and patterns for coding agents",
    ),
    bridge_ip: str | None = bridge_ip,
    verbose: bool = verbose,
    quiet: bool = quiet,
    json: bool = json_output,
    trace_mode: bool = trace,
    timeout_ms_val: int = timeout_ms,
) -> None:
    """Philips Hue notification system for visual feedback from AI agents and automation.

    Control Hue lights to provide visual signals for task status, notifications, and effects.
    Perfect for coding agents (like Copilot) to signal progress during automated workflows.

    Common Agent Patterns:
      - Task started:    huesignal effect apply pulse -l desk-light -c blue -b 0.5
      - Task complete:   huesignal effect apply pulse -l desk-light -c green -b 0.7
      - Error/blocker:   huesignal effect apply blink -l desk-light -c red --count 3

    For thorough examples and patterns, run: huesignal --explain
    """
    # Set up logging
    setup_logging(verbose=verbose, trace=trace_mode)

    if ctx.invoked_subcommand is None:
        # Store global options in context for subcommands
        ctx.obj = GlobalOptions(
            bridge_ip=bridge_ip,
            verbose=verbose,
            quiet=quiet,
            json_output=json,
            trace=trace_mode,
            timeout_ms=timeout_ms_val,
        )
        if not quiet:
            typer.echo("huesignal - Philips Hue notification system")
            typer.echo("Use 'huesignal --help' for available commands")
        sys.exit(0)
    else:
        # Store global options for subcommands
        ctx.obj = GlobalOptions(
            bridge_ip=bridge_ip,
            verbose=verbose,
            quiet=quiet,
            json_output=json,
            trace=trace_mode,
            timeout_ms=timeout_ms_val,
        )


# Command groups
auth_app = typer.Typer(
    help="""Authenticate with Philips Hue bridge.

First-time setup: Run 'huesignal auth login' to pair with your bridge.
Credentials are securely stored in Windows Credential Manager."""
)

lights_app = typer.Typer(
    help="""Control and query Hue lights.

Discover lights, toggle power, adjust brightness, and show detailed info.
Use 'huesignal lights list' to see all available lights."""
)

effect_app = typer.Typer(
    help="""Apply visual effects to lights.

Available effects: pulse, breathe, blink, rainbow.
Ideal for notifications and status signals in automated workflows.

Example: huesignal effect apply pulse -l desk-light -c green -b 0.7"""
)

samples_app = typer.Typer(
    help="""Automation templates and examples.

Pre-built templates for common automation scenarios (CI/CD, GitHub Actions, etc.).
Use 'huesignal samples list' to see available templates."""
)

cache_app = typer.Typer(
    help="""Manage cached bridge and light data.

Clear stale cache, set default bridge, or prune expired entries.
Useful when bridge IP changes or experiencing connectivity issues."""
)


@auth_app.command()
def login(
    ctx: typer.Context,
    bridge_ip: str | None = typer.Option(
        None, "--bridge-ip", help="IP address of Philips Hue bridge (auto-discovered if omitted)"
    ),
    print_key: bool = typer.Option(
        False, "--print", help="Print the app key to stdout instead of storing in credential manager"
    ),
    timeout: int = typer.Option(30, "--timeout", help="Seconds to wait for link button press (default: 30)"),
) -> None:
    """Authenticate and pair with your Philips Hue bridge.

    First-time setup command that creates and stores credentials for bridge access.

    Process:
      1. Discovers bridge automatically (or uses --bridge-ip)
      2. Prompts you to press the link button on your physical bridge
      3. Creates an app key with bridge API access
      4. Stores credentials securely in Windows Credential Manager
      5. Caches bridge IP for future commands

    Examples:
      # Auto-discover bridge and store credentials
      huesignal auth login

      # Specify bridge IP manually
      huesignal auth login --bridge-ip 192.168.1.100

      # Print key without storing (for manual credential management)
      huesignal auth login --print

      # Increase timeout for slow networks
      huesignal auth login --timeout 60

    Required: You must physically press the link button on your Hue bridge
    within the timeout period. The button is typically on top of the bridge.

    Note: This command only needs to be run once. Credentials persist across
    sessions and are automatically used by all huesignal commands.
    """
    # Discover bridge if not provided
    if not bridge_ip:
        typer.echo("Discovering bridges...")
        bridges = asyncio.run(discover_bridges())
        if not bridges:
            typer.echo("Attempting mDNS discovery...")
            bridges = asyncio.run(discover_bridges_mdns(timeout=2.0))

        if not bridges:
            typer.secho(
                "Error: No bridges found. Please specify --bridge-ip or ensure your Hue Bridge is online.",
                fg=typer.colors.RED,
            )
            raise typer.Exit(1)

        if len(bridges) == 1:
            bridge_ip = bridges[0].get("internalipaddress")
            typer.echo(f"Using bridge: {bridge_ip}")
        else:
            typer.echo("Multiple bridges found:")
            for i, bridge in enumerate(bridges):
                typer.echo(f"  {i}: {bridge.get('id')} - {bridge.get('internalipaddress')}")
            # For now, just use the first one
            bridge_ip = bridges[0].get("internalipaddress")
            typer.echo(f"Using first bridge: {bridge_ip}")

    # Start pairing process
    typer.echo(f"Press the link button on your Hue Bridge at {bridge_ip}...")

    # Get global options from context if available
    opts = getattr(ctx, "obj", None)
    json_output = opts.json_output if isinstance(opts, GlobalOptions) else False

    try:
        app_key = asyncio.run(auth_login(bridge_ip, timeout=float(timeout)))

        if json_output:
            import json

            typer.echo(
                json.dumps(
                    {
                        "success": True,
                        "bridge_ip": bridge_ip,
                        "app_key": app_key if print_key else "[stored]",
                        "message": "Successfully authenticated",
                    },
                    indent=2,
                )
            )
        elif print_key:
            # Just print the key
            typer.echo(app_key)
        else:
            # Store the key
            store_app_key(app_key)
            # Cache the bridge IP for future commands
            set_default_bridge_ip(bridge_ip)
            typer.secho("Successfully authenticated and stored credentials!", fg=typer.colors.GREEN)

    except AuthError as e:
        if json_output:
            import json

            typer.echo(json.dumps({"success": False, "error": str(e)}, indent=2))
        else:
            typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@lights_app.command(name="list")
def list_cmd(
    ctx: typer.Context,
    filter_name: str | None = typer.Option(
        None, "--filter", "-f", help="Filter lights by name substring (case-insensitive)"
    ),
) -> None:
    """List all lights available on your Hue bridge.

    Displays a formatted table with light names, IDs, status, and capabilities.
    Use this command to discover light names for use in other commands.

    Table Columns:
      - Name:        Human-readable light name
      - Short ID:    First 8 characters of light UUID
      - On:          Power state (✓ = on, ✗ = off)
      - Reachable:   Network connectivity (✓ = online, ✗ = offline)
      - Color:       Color support (✓ = supports color, ✗ = white only)
      - Brightness:  Current brightness percentage (0-100%)

    Examples:
      # List all lights
      huesignal lights list

      # Find lights matching "desk"
      huesignal lights list --filter desk
      huesignal lights list -f bedroom

      # Get JSON output for scripting
      huesignal lights list --json
      huesignal lights list --json --quiet | jq '.lights[].name'

    Use --json flag for machine-readable output in automation scripts.
    Combine with --quiet to suppress informational messages.
    """
    # Get global options from context
    opts = ctx.obj if isinstance(ctx.obj, GlobalOptions) else GlobalOptions()

    # Get bridge IP (with caching)
    bridge_ip = get_bridge_ip(opts.bridge_ip, opts.quiet)

    # Fetch lights
    try:
        lights_data = asyncio.run(list_lights(bridge_ip, filter_name, opts.json_output))
        lights = lights_data["lights"]
        count = lights_data["count"]

        if opts.json_output:
            # Output as JSON
            import json

            typer.echo(json.dumps(lights_data, indent=2))
        else:
            # Output as table
            if not lights:
                if filter_name:
                    typer.echo(f"No lights found matching filter: {filter_name}")
                else:
                    typer.echo("No lights found")
                return

            # Use Rich for nice table formatting
            from rich.console import Console
            from rich.table import Table

            console = Console()
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Name", style="white")
            table.add_column("Short ID", style="dim")
            table.add_column("On", justify="center")
            table.add_column("Reachable", justify="center")
            table.add_column("Color", justify="center")
            table.add_column("Brightness", justify="right")

            for light in lights:
                # Shorten ID to first 8 characters
                short_id = light["id"][:8]
                on_icon = "✓" if light["on"] else "✗"
                reachable_icon = "✓" if light["reachable"] else "✗"
                color_icon = "✓" if light["color_support"] else "✗"
                brightness = f"{int(light.get('brightness', 0))}%" if light.get("brightness") is not None else "-"

                # Color code the status
                on_style = "green" if light["on"] else "red"
                reachable_style = "green" if light["reachable"] else "red"
                color_style = "green" if light["color_support"] else "dim"

                table.add_row(
                    light["name"],
                    short_id,
                    f"[{on_style}]{on_icon}[/{on_style}]",
                    f"[{reachable_style}]{reachable_icon}[/{reachable_style}]",
                    f"[{color_style}]{color_icon}[/{color_style}]",
                    brightness,
                )

            console.print(f"\nFound {count} light(s):\n")
            console.print(table)
            typer.echo()

    except ValueError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)
    except HueConnectionError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"Unexpected error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@lights_app.command(name="on")
def lights_on_cmd(
    ctx: typer.Context,
    light: str = typer.Argument(..., help="Light name to turn on"),
    brightness: float | None = typer.Option(None, "--brightness", "-b", help="Brightness (0-100)"),
) -> None:
    """Turn on a light.

    Args:
        light: Name of the light to turn on
        brightness: Optional brightness level (0-100)
    """
    from huesignal.resolver import resolve_lights

    # Get global options from context
    opts = ctx.obj if isinstance(ctx.obj, GlobalOptions) else GlobalOptions()

    # Get bridge IP (with caching)
    bridge_ip = get_bridge_ip(opts.bridge_ip, opts.quiet)

    # Get credentials
    try:
        app_key = get_app_key()
        if not app_key:
            typer.secho("Error: No app key found. Please run 'huesignal auth login' first.", fg=typer.colors.RED)
            raise typer.Exit(1)
    except AuthError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)

    # Turn on light
    async def turn_on():
        async with HueClient(bridge_ip, app_key) as client:
            # Resolve light
            resolved = await resolve_lights(client.bridge, light_names=[light])
            light_id = resolved[0].light_id

            # Turn on using LightsController
            if brightness is not None:
                await client.bridge.lights.set_state(light_id, on=True, brightness=brightness)
                if opts.json_output:
                    import json

                    typer.echo(
                        json.dumps(
                            {
                                "success": True,
                                "light": light,
                                "light_id": light_id,
                                "state": "on",
                                "brightness": brightness,
                            },
                            indent=2,
                        )
                    )
                else:
                    typer.secho(f"✓ Turned on '{light}' with brightness {brightness}", fg=typer.colors.GREEN)
            else:
                await client.bridge.lights.set_state(light_id, on=True)
                if opts.json_output:
                    import json

                    typer.echo(
                        json.dumps({"success": True, "light": light, "light_id": light_id, "state": "on"}, indent=2)
                    )
                else:
                    typer.secho(f"✓ Turned on '{light}'", fg=typer.colors.GREEN)

    try:
        asyncio.run(turn_on())
    except Exception as e:
        if opts.json_output:
            import json

            typer.echo(json.dumps({"success": False, "error": str(e)}, indent=2))
        elif opts.trace:
            raise
        else:
            typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@lights_app.command(name="off")
def lights_off_cmd(
    ctx: typer.Context,
    light: str = typer.Argument(..., help="Light name to turn off"),
) -> None:
    """Turn off a light.

    Args:
        light: Name of the light to turn off
    """
    from huesignal.resolver import resolve_lights

    # Get global options from context
    opts = ctx.obj if isinstance(ctx.obj, GlobalOptions) else GlobalOptions()

    # Get bridge IP (with caching)
    bridge_ip = get_bridge_ip(opts.bridge_ip, opts.quiet)

    # Get credentials
    try:
        app_key = get_app_key()
        if not app_key:
            typer.secho("Error: No app key found. Please run 'huesignal auth login' first.", fg=typer.colors.RED)
            raise typer.Exit(1)
    except AuthError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)

    # Turn off light
    async def turn_off():
        async with HueClient(bridge_ip, app_key) as client:
            # Resolve light
            resolved = await resolve_lights(client.bridge, light_names=[light])
            light_id = resolved[0].light_id

            # Turn off using LightsController
            await client.bridge.lights.set_state(light_id, on=False)
            if opts.json_output:
                import json

                typer.echo(
                    json.dumps({"success": True, "light": light, "light_id": light_id, "state": "off"}, indent=2)
                )
            else:
                typer.secho(f"✓ Turned off '{light}'", fg=typer.colors.GREEN)

    try:
        asyncio.run(turn_off())
    except Exception as e:
        if opts.json_output:
            import json

            typer.echo(json.dumps({"success": False, "error": str(e)}, indent=2))
        elif opts.trace:
            raise
        else:
            typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@lights_app.command(name="show")
def show_light_cmd(
    ctx: typer.Context,
    light_name: str = typer.Argument(None, help="Name of the light to show"),
    light_opt: str | None = typer.Option(
        None, "--light", "-l", help="Name of the light to show (alternative to positional arg)"
    ),
) -> None:
    """Show detailed information about a specific light.

    Args:
        light_name: Name of the light to display (positional)
        light_opt: Name of the light to display (--light/-l option)
    """
    # Get global options from context
    opts = ctx.obj if isinstance(ctx.obj, GlobalOptions) else GlobalOptions()

    # Determine which light name to use
    effective_light_name = light_opt or light_name
    if not effective_light_name:
        typer.secho("Error: Light name is required (provide as argument or use --light/-l)", fg=typer.colors.RED)
        raise typer.Exit(1)

    # Get bridge IP (with caching)
    bridge_ip = get_bridge_ip(opts.bridge_ip, opts.quiet)

    # Fetch light details
    try:
        light_info = asyncio.run(show_light(bridge_ip, effective_light_name))

        if opts.json_output:
            # Output as JSON
            import json

            typer.echo(json.dumps(light_info, indent=2))
        else:
            # Output as formatted details
            typer.echo(f"\nLight: {light_info.get('name', 'Unknown')}")
            typer.echo(f"ID: {light_info.get('id', 'Unknown')}")
            typer.echo(f"Type: {light_info.get('type', 'Unknown')}")
            typer.echo(f"Model: {light_info.get('model', 'Unknown')}")
            typer.echo(f"Status: {'On' if light_info.get('on', False) else 'Off'}")
            typer.echo(f"Reachable: {'Yes' if light_info.get('reachable', False) else 'No'}")
            typer.echo(f"Brightness: {light_info.get('brightness', 'N/A')}")
            typer.echo(f"Color Support: {'Yes' if light_info.get('color_support', False) else 'No'}")
            typer.echo(f"Dim Support: {'Yes' if light_info.get('dim_support', False) else 'No'}\n")

    except ValueError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)
    except HueConnectionError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"Unexpected error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@effect_app.command(name="list")
def effect_list(ctx: typer.Context) -> None:
    """List available effects."""
    # Get global options from context
    opts = ctx.obj if isinstance(ctx.obj, GlobalOptions) else GlobalOptions()

    effects = list_effects()
    if opts.json_output:
        import json

        effect_list = [{"name": name, "description": description} for name, description in effects]
        typer.echo(json.dumps({"effects": effect_list, "count": len(effect_list)}, indent=2))
    else:
        if not effects:
            typer.echo("No effects registered.")
            return

        typer.echo("Available effects:")
        for name, description in effects:
            typer.echo(f"  {name:<25} {description}")


@effect_app.command(name="params")
def effect_params(
    ctx: typer.Context,
    effect_name: str = typer.Argument(..., help="Effect name to show parameters for"),
) -> None:
    """Show parameters for a specific effect.

    Display available parameters with their types, defaults, and descriptions.
    Use this to discover what parameters each effect accepts.

    Examples:
      huesignal effect params pulse
      huesignal effect params blink --json
    """
    from huesignal.effects import get_effect_class

    # Get global options from context
    opts = ctx.obj if isinstance(ctx.obj, GlobalOptions) else GlobalOptions()

    # Get effect class
    effect_class = get_effect_class(effect_name)
    if effect_class is None:
        typer.secho(
            f"Error: Unknown effect '{effect_name}'. Use 'effect list' to see available effects.", fg=typer.colors.RED
        )
        raise typer.Exit(1)

    # Get parameters
    params = effect_class.get_params()

    if opts.json_output:
        import json

        param_list = [
            {
                "name": p.name,
                "type": p.type.__name__ if hasattr(p.type, "__name__") else str(p.type),
                "default": p.default,
                "description": p.description,
            }
            for p in params
        ]
        typer.echo(json.dumps({"effect": effect_name, "parameters": param_list, "count": len(param_list)}, indent=2))
    else:
        if not params:
            typer.echo(f"Effect '{effect_name}' has no parameters.")
            return

        typer.echo(f"\nParameters for effect '{effect_name}':\n")
        for p in params:
            type_name = p.type.__name__ if hasattr(p.type, "__name__") else str(p.type)
            typer.echo(f"  {p.name:<20} (type: {type_name}, default: {p.default})")
            typer.echo(f"    {p.description}")
            typer.echo()


@effect_app.command()
def apply(
    ctx: typer.Context,
    effect_name: str = typer.Argument(..., help="Effect name: pulse, breathe, blink, or rainbow (see 'effect list')"),
    light: str | None = typer.Option(
        None,
        "--light",
        "-l",
        help="Target light name (omit to apply to ALL lights, or set HUESIGNAL_LIGHT_NAME env var)",
    ),
    brightness: float | None = typer.Option(
        None, "--brightness", "-b", help="Brightness: 0-100 (%), 0.0-1.0 (decimal), or 1-254 (raw)"
    ),
    color: str | None = typer.Option(
        None, "--color", "-c", help="Color: name (red, green, blue, etc.) or hex (#FF0000)"
    ),
    duration: int = typer.Option(1000, "--duration", "-d", help="Effect duration in milliseconds (default: 1000)"),
    count: int = typer.Option(1, "--count", help="Number of cycles/repeats for pulse/blink effects (default: 1)"),
    param: list[str] = typer.Option([], "--param", "-p", help="Effect parameter in key=value format (repeatable)"),
    no_restore: bool = typer.Option(
        False,
        "--no-restore",
        help="Don't restore original light state after effect (leaves light in effect's final state)",
    ),
) -> None:
    """Apply a visual effect to one or more lights.

    Create visual notifications and status signals using dynamic light effects.
    Perfect for automation workflows, CI/CD feedback, and agent status updates.

    Effects:
      pulse    - Quick flash, ideal for notifications (configurable count/brightness)
      breathe  - Smooth fade in/out, good for ambient feedback
      blink    - Rapid on/off toggle, attention-grabbing for alerts
      rainbow  - Color cycle animation, celebratory or demo

    Colors (--color / -c):
      Named: red, green, blue, yellow, orange, purple, pink, cyan, white
      Hex:   #FF0000 (red), #00FF00 (green), #0000FF (blue)
      Short: "short" (brief white flash), "long" (extended white flash)

    Brightness (--brightness / -b):
      Percentage:  0-100      (e.g., 75 = 75%)
      Decimal:     0.0-1.0    (e.g., 0.75 = 75%)
      Raw:         1-254      (Hue API values)

    Duration (--duration / -d):
      Time in milliseconds for the effect to complete.
      Shorter = faster, longer = smoother/slower.
      Typical: 500-3000ms

    Default Light:
      Set HUESIGNAL_LIGHT_NAME environment variable to target a specific light
      by default when --light is omitted. Without this, effects apply to all lights.

    Examples:
      # Single green pulse (task complete signal)
      huesignal effect apply pulse -l desk-light -c green -b 0.7

      # Three red blinks (error/blocker signal)
      huesignal effect apply blink -l desk-light -c red --count 3 -b 1.0

      # Blue pulse (task started signal)
      huesignal effect apply pulse -l desk-light -c blue -b 0.5

      # Smooth yellow breathe (warning state)
      huesignal effect apply breathe -l desk-light -c yellow -d 2000

      # Rainbow celebration (all tests pass)
      huesignal effect apply rainbow -l desk-light -d 3000

      # Apply to ALL lights (omit -l flag)
      huesignal effect apply pulse -c green -b 0.8

      # Use default light from environment
      $env:HUESIGNAL_LIGHT_NAME="desk-light"
      huesignal effect apply pulse -c green -b 0.7

      # Don't restore state (leave light in effect color)
      huesignal effect apply pulse -l desk-light -c red --no-restore

    Agent Workflow Patterns:
      Task claimed:     pulse -c blue -b 0.5
      Task complete:    pulse -c green -b 0.7
      Error/blocker:    blink -c red --count 3 -b 1.0
      Verification:     pulse -c green -b 1.0

    By default, lights restore to their original state after the effect completes.
    Use --no-restore to leave lights in the effect's final state.

    Tip: Wrap commands in '2>/dev/null || true' for graceful failures in scripts.
    """
    import os

    from huesignal.effects import EffectOptions, get_effect_class
    from huesignal.resolver import resolve_lights

    # Get global options from context
    opts = ctx.obj if isinstance(ctx.obj, GlobalOptions) else GlobalOptions()

    # Check for default light name in environment if --light not provided
    if light is None:
        default_light = os.environ.get("HUESIGNAL_LIGHT_NAME")
        if default_light:
            light = default_light
            if not opts.quiet:
                typer.echo(f"Using default light from HUESIGNAL_LIGHT_NAME: {light}")

    # Get bridge IP (with caching)
    bridge_ip = get_bridge_ip(opts.bridge_ip, opts.quiet)

    # Get credentials
    try:
        app_key = get_app_key()
        if not app_key:
            typer.secho("Error: No app key found. Please run 'huesignal auth login' first.", fg=typer.colors.RED)
            raise typer.Exit(1)
    except AuthError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)

    # Run effect
    async def run_effect():
        async with HueClient(bridge_ip, app_key) as client:
            # Resolve lights
            light_names = [light] if light else None
            resolved = await resolve_lights(client.bridge, light_names=light_names)
            light_ids = [r.light_id for r in resolved]

            if not opts.quiet:
                typer.echo(f"Applying '{effect_name}' to {len(light_ids)} light(s)")

            # Get effect class
            try:
                effect_class = get_effect_class(effect_name)
            except ValueError as e:
                typer.secho(f"Error: {e}", fg=typer.colors.RED)
                raise typer.Exit(1)

            # Create effect options
            effect_options = EffectOptions(
                duration_ms=duration,
                brightness=brightness,
                color=color,
                restore=not no_restore,
            )

            # Normalize and validate brightness if provided
            if brightness is not None:
                from huesignal.effects import normalize_brightness

                try:
                    normalized_brightness = normalize_brightness(brightness)
                    effect_options.brightness = normalized_brightness
                except ValueError as e:
                    typer.secho(f"Error: {e}", fg=typer.colors.RED)
                    raise typer.Exit(1)

            # Parse effect parameters
            effect_params = {}

            # Add backward compatibility: --count option sets 'count' param
            if count != 1:
                effect_params["count"] = count

            # Parse --param options (these override --count if both specified)
            for p in param:
                if "=" not in p:
                    typer.secho(f"Error: Invalid parameter format '{p}'. Expected key=value", fg=typer.colors.RED)
                    raise typer.Exit(1)
                key, value = p.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Try to parse value as int
                try:
                    value = int(value)
                except ValueError:
                    pass  # Keep as string if not an int

                effect_params[key] = value

            # Validate parameters against effect's declared params
            if effect_params:
                effect_param_defs = effect_class.get_params()
                valid_param_names = {p.name for p in effect_param_defs}

                for key in effect_params:
                    if key not in valid_param_names:
                        typer.secho(
                            f"Error: Unknown parameter '{key}' for effect '{effect_name}'. "
                            f"Valid parameters: {', '.join(sorted(valid_param_names))}",
                            fg=typer.colors.RED,
                        )
                        raise typer.Exit(1)

            # Create and apply effect with parameters
            effect = effect_class(client.bridge, light_ids, effect_options, **effect_params)

            failed_lights = await effect.apply()

            if opts.json_output:
                import json

                typer.echo(
                    json.dumps(
                        {
                            "success": len(failed_lights) == 0,
                            "effect": effect_name,
                            "lights_affected": len(light_ids),
                            "light_ids": light_ids,
                            "failed_lights": failed_lights,
                            "duration_ms": duration,
                            "color": color,
                            "brightness": brightness,
                            "restored": not no_restore,
                        },
                        indent=2,
                    )
                )
                if failed_lights:
                    return 2
            elif not opts.quiet:
                if failed_lights:
                    # Partial success - some lights failed to restore
                    typer.secho(
                        f"Effect applied with warnings: {len(failed_lights)} light(s) failed to restore.",
                        fg=typer.colors.YELLOW,
                    )
                    typer.echo(f"Failed light IDs: {', '.join(failed_lights)}")
                    # Non-zero exit code for partial failures
                    return 2
                else:
                    typer.secho("Effect applied successfully!", fg=typer.colors.GREEN)
            elif failed_lights:
                # Quiet mode but still need to signal partial failure
                return 2

    try:
        exit_code = asyncio.run(run_effect())
        if exit_code and exit_code != 0:
            raise typer.Exit(exit_code)
    except Exception as e:
        if opts.json_output:
            import json

            typer.echo(json.dumps({"success": False, "error": str(e)}, indent=2))
        elif opts.trace:
            raise
        else:
            typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@effect_app.command()
def play(
    ctx: typer.Context,
    program_file: str = typer.Argument(..., help="Path to YAML program file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview program without execution"),
    no_restore: bool = typer.Option(False, "--no-restore", help="Don't restore lights to original state after program"),
) -> None:
    """Execute a YAML effect program.

    Programs enable multi-light choreography with sequenced effects.
    See EFFECTS_PRD.md for YAML format documentation.

    Example:
        huesignal effect play celebration.yaml
        huesignal effect play sequence.yaml --dry-run
        huesignal effect play show.yaml --no-restore

    The program will execute all tracks in parallel with proper timing.
    Press Ctrl+C to interrupt and restore lights to original state.
    """
    from pathlib import Path

    from huesignal.effects.context import ExecutionContext
    from huesignal.programs import Scheduler, load_program

    # Get global options from context
    opts = ctx.obj if isinstance(ctx.obj, GlobalOptions) else GlobalOptions()

    # Validate file exists
    program_path = Path(program_file)
    if not program_path.exists():
        typer.secho(f"Error: Program file not found: {program_file}", fg=typer.colors.RED)
        raise typer.Exit(1)

    # Load program
    try:
        program = load_program(program_file)
        if not opts.quiet:
            typer.echo(f"Loaded program: {program.name}")
            if program.description:
                typer.echo(f"Description: {program.description}")
    except ValueError as e:
        typer.secho(f"Error loading program: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        if opts.trace:
            raise
        raise typer.Exit(1)

    # Dry-run mode: show what would happen
    if dry_run:
        typer.echo("\n[DRY RUN MODE - No effects will be applied]\n")
        typer.echo(f"Program: {program.name}")
        typer.echo(f"Total duration: {program.total_duration_ms()}ms ({program.total_duration_ms() / 1000:.1f}s)")
        typer.echo(f"Tracks: {len(program.tracks)}\n")

        for i, track in enumerate(program.tracks, 1):
            typer.echo(f"Track {i}: {track.light_pattern}")
            typer.echo(f"  Duration: {track.duration_ms()}ms")
            typer.echo(f"  Steps: {len(track.steps)}")
            for j, step in enumerate(track.steps, 1):
                action = step.action
                action_str = f"{action.__class__.__name__}"
                if hasattr(action, "effect_name"):
                    action_str = f"Effect: {action.effect_name}"
                elif hasattr(action, "duration_ms"):
                    action_str = f"Wait: {action.duration_ms}ms"
                typer.echo(f"    {j}. [{step.start_ms}ms] {action_str} ({step.duration_ms}ms)")
            typer.echo()

        return

    # Get bridge IP
    bridge_ip = get_bridge_ip(opts.bridge_ip, opts.quiet)

    # Get credentials
    try:
        app_key = get_app_key()
        if not app_key:
            typer.secho("Error: No app key found. Please run 'huesignal auth login' first.", fg=typer.colors.RED)
            raise typer.Exit(1)
    except AuthError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)

    # Execute program
    async def run_program():
        async with HueClient(bridge_ip, app_key) as client:
            # Create execution context
            ctx_exec = ExecutionContext(bridge=client.bridge)
            scheduler = Scheduler(ctx_exec)

            if not opts.quiet:
                typer.echo(f"\nExecuting program: {program.name}")
                typer.echo(f"Tracks: {len(program.tracks)}")
                typer.echo(f"Duration: {program.total_duration_ms() / 1000:.1f}s\n")

            try:
                # Execute with state restoration unless disabled
                restore = not no_restore
                result = await scheduler.run_program(program, restore_state=restore)

                # Report results
                if opts.json_output:
                    import json

                    track_data = []
                    for tr in result.track_results:
                        track_data.append(
                            {
                                "light_pattern": tr.light_pattern,
                                "light_ids": tr.light_ids,
                                "failed_lights": tr.failed_lights,
                                "errors": tr.errors,
                            }
                        )

                    output = {
                        "success": result.success,
                        "program_name": result.program_name,
                        "tracks": track_data,
                        "total_failed_lights": result.total_failed_lights,
                        "restoration_failures": result.restoration_failures,
                    }
                    typer.echo(json.dumps(output, indent=2))

                    # Exit code based on success
                    if not result.success:
                        return 2
                elif not opts.quiet:
                    # Display track results
                    for i, tr in enumerate(result.track_results, 1):
                        typer.echo(f"Track {i} ({tr.light_pattern}): {len(tr.light_ids)} light(s)")
                        if tr.failed_lights:
                            typer.secho(f"  Failed: {', '.join(tr.failed_lights)}", fg=typer.colors.YELLOW)
                        if tr.errors:
                            for error in tr.errors:
                                typer.secho(f"  Error: {error}", fg=typer.colors.RED)

                    # Final status
                    if result.success:
                        typer.secho("\nProgram completed successfully!", fg=typer.colors.GREEN)
                    else:
                        typer.secho("\nProgram completed with errors.", fg=typer.colors.YELLOW)
                        if result.total_failed_lights:
                            typer.echo(f"Failed lights: {', '.join(result.total_failed_lights)}")
                        if result.restoration_failures:
                            typer.echo(f"Restoration failures: {', '.join(result.restoration_failures)}")
                        return 2
                elif not result.success:
                    # Quiet mode but signal failure
                    return 2

            except KeyboardInterrupt:
                # Handle Ctrl+C gracefully
                if not opts.quiet:
                    typer.echo("\n\nInterrupted! Restoring lights...")

                # Restore state
                if not no_restore:
                    try:
                        restoration_failures = await ctx_exec.restore_state()
                        if restoration_failures and not opts.quiet:
                            typer.secho(
                                f"Warning: Failed to restore {len(restoration_failures)} light(s)",
                                fg=typer.colors.YELLOW,
                            )
                    except Exception as restore_err:
                        if not opts.quiet:
                            typer.secho(f"Error during restoration: {restore_err}", fg=typer.colors.RED)

                if not opts.quiet:
                    typer.echo("Interrupted.")
                raise typer.Exit(130)  # Standard exit code for Ctrl+C

    try:
        exit_code = asyncio.run(run_program())
        if exit_code and exit_code != 0:
            raise typer.Exit(exit_code)
    except KeyboardInterrupt:
        raise typer.Exit(130)
    except Exception as e:
        if opts.json_output:
            import json

            typer.echo(json.dumps({"success": False, "error": str(e)}, indent=2))
        elif opts.trace:
            raise
        else:
            typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@samples_app.command(name="list")
def samples_list(ctx: typer.Context) -> None:
    """List available automation samples."""
    # Get global options from context
    opts = ctx.obj if isinstance(ctx.obj, GlobalOptions) else GlobalOptions()

    samples = list_samples()
    if opts.json_output:
        import json

        typer.echo(json.dumps({"samples": samples, "count": len(samples)}, indent=2))
    else:
        typer.echo("Available automation samples:")
        for sample_name in samples:
            typer.echo(f"  - {sample_name}")


@samples_app.command(name="show")
def samples_show(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Sample name to show"),
) -> None:
    """Show a sample automation template.

    All samples use cached huesignal configuration (bridge IP, light name).
    Set HUESIGNAL_LIGHT_NAME environment variable for default light.

    Args:
        name: Sample name to display
    """
    # Get global options from context
    opts = ctx.obj if isinstance(ctx.obj, GlobalOptions) else GlobalOptions()

    try:
        sample = get_sample(name)
        if opts.json_output:
            import json

            typer.echo(json.dumps({"sample_name": name, "content": sample}, indent=2))
        else:
            typer.echo(sample)
    except ValueError as e:
        if opts.json_output:
            import json

            typer.echo(json.dumps({"success": False, "error": str(e)}, indent=2))
        else:
            typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command()
def doctor(
    ctx: typer.Context,
    bridge_ip: str | None = typer.Option(
        None, "--bridge-ip", help="Bridge IP to diagnose (auto-discovered if omitted)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed diagnostic information"),
) -> None:
    """Run comprehensive diagnostic checks for huesignal setup.

    Verifies your huesignal installation, bridge connectivity, authentication,
    and API access. Use this command to troubleshoot configuration issues.

    Checks Performed:
      ✓ Bridge discovery and network reachability
      ✓ Cached bridge IP validity
      ✓ Stored credentials existence and format
      ✓ API authentication and permissions
      ✓ Light enumeration and accessibility
      ✓ Basic API functionality

    Exit Codes:
      0 - All checks passed
      1 - One or more checks failed

    Examples:
      # Run diagnostics with auto-discovery
      huesignal doctor

      # Show detailed output
      huesignal doctor --verbose
      huesignal doctor -v

      # Check specific bridge
      huesignal doctor --bridge-ip 192.168.1.100

      # Silent check (use exit code only)
      huesignal doctor --quiet
      if [ $? -eq 0 ]; then echo "Ready"; fi

    Use this command:
      - After first installation
      - When commands fail with connection errors
      - After moving bridge to new IP
      - When troubleshooting authentication issues

    Common Issues:
      - "No credentials found" → Run 'huesignal auth login'
      - "Bridge not found" → Check bridge power and network
      - "API error" → Re-run 'huesignal auth login'
      - "Light not reachable" → Check light power and Zigbee network
    """
    # Get global options from context
    opts = ctx.obj if isinstance(ctx.obj, GlobalOptions) else GlobalOptions()

    try:
        status = asyncio.run(run_doctor(bridge_ip=bridge_ip, verbose=verbose))
        if opts.json_output:
            import json

            typer.echo(json.dumps(status.to_dict(), indent=2))
        else:
            typer.echo(status.report(verbose=verbose))
        if not status.all_passed:
            raise typer.Exit(1)
    except Exception as e:
        if opts.json_output:
            import json

            typer.echo(json.dumps({"success": False, "error": str(e)}, indent=2))
        else:
            typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@cache_app.command()
def clear(ctx: typer.Context) -> None:
    """Clear all cached data.

    Removes cached bridge discovery results and light lists.
    Use this if you're experiencing stale data or after moving bridges to different IPs.
    """
    # Get global options from context
    opts = ctx.obj if isinstance(ctx.obj, GlobalOptions) else GlobalOptions()

    cache = get_cache()
    cache.clear()
    if opts.json_output:
        import json

        typer.echo(json.dumps({"success": True, "message": "Cache cleared successfully"}, indent=2))
    else:
        typer.secho("Cache cleared successfully.", fg=typer.colors.GREEN)


@cache_app.command()
def info(ctx: typer.Context) -> None:
    """Show cache information.

    Displays cache location and statistics about cached data.
    """
    # Get global options from context
    opts = ctx.obj if isinstance(ctx.obj, GlobalOptions) else GlobalOptions()

    cache = get_cache()
    cache_file = cache.cache_file

    if opts.json_output:
        import json
        import time

        result = {"cache_location": str(cache_file), "exists": cache_file.exists(), "entries": []}

        if cache_file.exists():
            try:
                cache_data = cache._load_cache()
                if cache_data:
                    result["count"] = len(cache_data)
                    for key in cache_data.keys():
                        entry = cache_data[key]
                        entry_info = {"key": key}
                        if "expires_at" in entry:
                            remaining = int(entry["expires_at"] - time.time())
                            entry_info["expires_in_seconds"] = remaining
                            entry_info["expired"] = remaining <= 0
                        else:
                            entry_info["expires_in_seconds"] = None
                            entry_info["expired"] = False
                        result["entries"].append(entry_info)
                else:
                    result["count"] = 0
            except Exception as e:
                result["error"] = str(e)
        else:
            result["count"] = 0

        typer.echo(json.dumps(result, indent=2))
    else:
        typer.echo(f"Cache location: {cache_file}")

        if not cache_file.exists():
            typer.echo("Cache status: Empty (no cache file)")
            return

        try:
            cache_data = cache._load_cache()
            if not cache_data:
                typer.echo("Cache status: Empty")
                return

            typer.echo(f"Cache status: {len(cache_data)} entries")
            typer.echo("\nCached entries:")

            for key in cache_data.keys():
                entry = cache_data[key]
                if "expires_at" in entry:
                    import time

                    remaining = int(entry["expires_at"] - time.time())
                    if remaining > 0:
                        typer.echo(f"  - {key}: expires in {remaining}s")
                    else:
                        typer.echo(f"  - {key}: EXPIRED")
                else:
                    typer.echo(f"  - {key}: no expiration")

        except Exception as e:
            typer.secho(f"Error reading cache: {e}", fg=typer.colors.RED)


@cache_app.command()
def prune(ctx: typer.Context) -> None:
    """Remove expired entries from cache.

    Cleans up cache by removing entries that have exceeded their TTL.
    This can help reduce cache file size.
    """
    # Get global options from context
    opts = ctx.obj if isinstance(ctx.obj, GlobalOptions) else GlobalOptions()

    cache = get_cache()
    pruned = cache.prune_expired()

    if opts.json_output:
        import json

        typer.echo(json.dumps({"success": True, "pruned_count": pruned}, indent=2))
    else:
        if pruned > 0:
            typer.secho(f"Pruned {pruned} expired cache entries.", fg=typer.colors.GREEN)
        else:
            typer.echo("No expired entries to prune.")


@cache_app.command(name="set-bridge")
def set_bridge_cmd(
    ctx: typer.Context,
    bridge_ip: str = typer.Argument(..., help="Bridge IP address to cache as default"),
) -> None:
    """Set the default bridge IP address.

    This sets the bridge IP that will be used by default for all commands.
    Useful if you want to manually specify which bridge to use.
    """
    # Get global options from context
    opts = ctx.obj if isinstance(ctx.obj, GlobalOptions) else GlobalOptions()

    set_default_bridge_ip(bridge_ip)
    if opts.json_output:
        import json

        typer.echo(json.dumps({"success": True, "bridge_ip": bridge_ip}, indent=2))
    else:
        typer.secho(f"Set default bridge IP to: {bridge_ip}", fg=typer.colors.GREEN)


@cache_app.command(name="get-bridge")
def get_bridge_cmd(ctx: typer.Context) -> None:
    """Show the cached default bridge IP address.

    Displays the currently cached bridge IP that will be used by commands.
    """
    # Get global options from context
    opts = ctx.obj if isinstance(ctx.obj, GlobalOptions) else GlobalOptions()

    bridge_ip = get_default_bridge_ip()
    if opts.json_output:
        import json

        typer.echo(json.dumps({"bridge_ip": bridge_ip, "cached": bridge_ip is not None}, indent=2))
    else:
        if bridge_ip:
            typer.echo(f"Default bridge IP: {bridge_ip}")
        else:
            typer.echo("No default bridge IP cached.")


# Add command groups to main app
app.add_typer(auth_app, name="auth")
app.add_typer(lights_app, name="lights")
app.add_typer(effect_app, name="effect")
app.add_typer(samples_app, name="samples")
app.add_typer(cache_app, name="cache")


def cli() -> None:
    """Entry point for the CLI."""
    app()
