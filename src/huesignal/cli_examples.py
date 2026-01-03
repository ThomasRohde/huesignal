"""Comprehensive CLI examples for coding agents and users."""

EXPLAIN_TEXT = r"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        huesignal - Usage Examples                            ║
║                  Complete Guide for Coding Agents & Automation               ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌─ FIRST TIME SETUP ───────────────────────────────────────────────────────────┐
│ Before using huesignal, authenticate with your Hue bridge:                   │
│                                                                               │
│   huesignal auth login                                                        │
│                                                                               │
│ This will:                                                                    │
│   1. Discover your bridge automatically                                      │
│   2. Prompt you to press the link button on the bridge                       │
│   3. Store credentials securely in Windows Credential Manager                │
│   4. Cache the bridge IP for future commands                                 │
│                                                                               │
│ Specify bridge manually (if discovery fails):                                │
│   huesignal auth login --bridge-ip 192.168.1.100                             │
│                                                                               │
│ Just print the key without storing:                                          │
│   huesignal auth login --print                                               │
└───────────────────────────────────────────────────────────────────────────────┘

┌─ DISCOVER YOUR LIGHTS ───────────────────────────────────────────────────────┐
│ List all lights on your bridge:                                              │
│   huesignal lights list                                                       │
│                                                                               │
│ Filter by name:                                                               │
│   huesignal lights list --filter desk                                         │
│                                                                               │
│ Get JSON output (for parsing in scripts):                                    │
│   huesignal lights list --json                                                │
│                                                                               │
│ Show detailed info about a specific light:                                   │
│   huesignal lights show "Desk Lamp"                                           │
│   huesignal lights show desk-light --json                                     │
└───────────────────────────────────────────────────────────────────────────────┘

┌─ BASIC LIGHT CONTROL ────────────────────────────────────────────────────────┐
│ Turn a light on:                                                              │
│   huesignal lights on desk-light                                              │
│                                                                               │
│ Turn on with specific brightness (0-100):                                    │
│   huesignal lights on desk-light --brightness 75                              │
│   huesignal lights on desk-light -b 50                                        │
│                                                                               │
│ Turn a light off:                                                             │
│   huesignal lights off desk-light                                             │
└───────────────────────────────────────────────────────────────────────────────┘

┌─ EFFECTS FOR VISUAL FEEDBACK ────────────────────────────────────────────────┐
│ List available effects:                                                       │
│   huesignal effect list                                                       │
│                                                                               │
│ PULSE - Quick flash (ideal for notifications)                                │
│   # Single green pulse at 70% brightness                                     │
│   huesignal effect apply pulse -l desk-light -c green -b 0.7                 │
│                                                                               │
│   # Three red pulses for errors/blockers                                     │
│   huesignal effect apply pulse -l desk-light -c red -b 1.0 --count 3         │
│                                                                               │
│   # Short blue pulse for "working" signal                                    │
│   huesignal effect apply pulse -l desk-light -c blue -b 0.5                  │
│                                                                               │
│ BREATHE - Smooth fade in/out (ambient feedback)                              │
│   huesignal effect apply breathe -l desk-light -c purple                      │
│                                                                               │
│ BLINK - Attention-grabbing (urgent alerts)                                   │
│   huesignal effect apply blink -l desk-light -c red --count 5                │
│                                                                               │
│ RAINBOW - Color cycle (celebratory or demo)                                  │
│   huesignal effect apply rainbow -l desk-light -d 3000                        │
│                                                                               │
│ Apply to ALL lights (omit -l flag):                                          │
│   huesignal effect apply pulse -c green -b 0.8                               │
│                                                                               │
│ Don't restore original state after effect:                                   │
│   huesignal effect apply pulse -l desk-light -c red --no-restore             │
└───────────────────────────────────────────────────────────────────────────────┘

┌─ AGENT WORKFLOW PATTERNS ────────────────────────────────────────────────────┐
│ These examples show how coding agents (like Copilot) can use huesignal       │
│ to provide real-time visual feedback during task execution.                  │
│                                                                               │
│ ON TASK CLAIM (starting work):                                               │
│   huesignal effect apply pulse -l desk-light -c blue -b 0.5 \                │
│     2>/dev/null || true                                                       │
│                                                                               │
│ ON TASK COMPLETE (finished successfully):                                    │
│   huesignal effect apply pulse -l desk-light -c green -b 0.7 \               │
│     2>/dev/null || true                                                       │
│                                                                               │
│ ON BLOCKER/ERROR (needs attention):                                          │
│   huesignal effect apply blink -l desk-light -c red -b 1.0 --count 3 \       │
│     2>/dev/null || true                                                       │
│                                                                               │
│ Note: The '2>/dev/null || true' pattern makes signals graceful:              │
│   - Errors are suppressed if huesignal isn't installed                       │
│   - Failures don't interrupt workflow                                        │
│   - Agents can use signals without requiring huesignal                       │
└───────────────────────────────────────────────────────────────────────────────┘

┌─ COLOR OPTIONS ──────────────────────────────────────────────────────────────┐
│ Named colors (recommended for clarity):                                      │
│   red, green, blue, yellow, orange, purple, pink, cyan, white                │
│                                                                               │
│ Hex colors:                                                                   │
│   --color "#FF0000"     (red)                                                 │
│   --color "#00FF00"     (green)                                               │
│   --color "#0000FF"     (blue)                                                │
│                                                                               │
│ Special values:                                                               │
│   --color short         (brief white flash)                                  │
│   --color long          (extended white flash)                               │
└───────────────────────────────────────────────────────────────────────────────┘

┌─ BRIGHTNESS OPTIONS ─────────────────────────────────────────────────────────┐
│ Brightness can be specified as:                                              │
│   - Percentage (0-100):  --brightness 75                                     │
│   - Decimal (0.0-1.0):   --brightness 0.75                                   │
│   - Raw value (1-254):   --brightness 190                                    │
│                                                                               │
│ Default brightness if not specified: 254 (maximum)                           │
└───────────────────────────────────────────────────────────────────────────────┘

┌─ DIAGNOSTICS & TROUBLESHOOTING ──────────────────────────────────────────────┐
│ Check huesignal setup and connectivity:                                      │
│   huesignal doctor                                                            │
│   huesignal doctor --verbose                                                  │
│                                                                               │
│ This checks:                                                                  │
│   - Bridge discovery and reachability                                         │
│   - Stored credentials validity                                               │
│   - API connectivity and permissions                                          │
│   - Light accessibility                                                       │
└───────────────────────────────────────────────────────────────────────────────┘

┌─ CACHE MANAGEMENT ───────────────────────────────────────────────────────────┐
│ View cache information:                                                       │
│   huesignal cache info                                                        │
│                                                                               │
│ Manually set default bridge:                                                 │
│   huesignal cache set-bridge 192.168.1.100                                    │
│                                                                               │
│ Show cached bridge IP:                                                        │
│   huesignal cache get-bridge                                                  │
│                                                                               │
│ Clear all cached data (use if experiencing stale data):                      │
│   huesignal cache clear                                                       │
│                                                                               │
│ Remove expired cache entries:                                                │
│   huesignal cache prune                                                       │
└───────────────────────────────────────────────────────────────────────────────┘

┌─ AUTOMATION SAMPLES ─────────────────────────────────────────────────────────┐
│ List available automation templates:                                         │
│   huesignal samples list                                                      │
│                                                                               │
│ Show a sample template:                                                       │
│   huesignal samples show coding-session-success                               │
│   huesignal samples show lodestar-agent                                       │
│   huesignal samples show pytest-conftest                                      │
│                                                                               │
│ Save sample to file:                                                          │
│   huesignal samples show lodestar-agent --save agent.sh                       │
│                                                                               │
│ All samples use cached config - no manual IPs needed!                        │
│ Set HUESIGNAL_LIGHT_NAME environment variable for your default light.        │
└───────────────────────────────────────────────────────────────────────────────┘

┌─ YAML PROGRAMS (Multi-Light Choreography) ───────────────────────────────────┐
│ Learn YAML program format:                                                    │
│   huesignal program format                                                    │
│                                                                               │
│ Generate starter templates:                                                   │
│   huesignal program template notification                                     │
│   huesignal program template sequence --output my-program.yaml                │
│   huesignal program template parallel                                         │
│   huesignal program template choreography                                     │
│                                                                               │
│ Execute YAML programs:                                                        │
│   huesignal run celebration.yaml                                              │
│   huesignal run examples/sunrise-wakeup.yaml                                  │
│                                                                               │
│ Validate before running:                                                      │
│   huesignal run my-program.yaml --validate                                    │
│                                                                               │
│ YAML programs enable:                                                         │
│   - Multi-light synchronization                                               │
│   - Precise timing and sequencing                                             │
│   - Parallel effect execution                                                 │
│   - Complex choreography                                                      │
│                                                                               │
│ Quick YAML example:                                                           │
│   name: notification                                                          │
│   tracks:                                                                     │
│     - light: desk-light                                                       │
│       steps:                                                                  │
│         - effect: pulse                                                       │
│           options:                                                            │
│             color: green                                                      │
│             brightness: 0.8                                                   │
│         - wait: 500                                                           │
│         - effect: breathe                                                     │
│           options:                                                            │
│             color: blue                                                       │
│                                                                               │
│ See examples/ directory for more patterns!                                    │
└───────────────────────────────────────────────────────────────────────────────┘

┌─ EFFECT DISCOVERY ───────────────────────────────────────────────────────────┐
│ See all valid colors, brightness formats, and timing:                        │
│   huesignal effect info                                                       │
│                                                                               │
│ List all available effects:                                                   │
│   huesignal effect list                                                       │
│                                                                               │
│ See parameters for a specific effect:                                        │
│   huesignal effect params pulse                                               │
│   huesignal effect params blink                                               │
│                                                                               │
│ This shows valid parameter values so you don't have to guess!                │
└───────────────────────────────────────────────────────────────────────────────┘

┌─ GLOBAL OPTIONS ─────────────────────────────────────────────────────────────┐
│ These options work with any command:                                         │
│                                                                               │
│   --bridge-ip <IP>      Override bridge IP (bypasses discovery/cache)        │
│   --verbose             Show detailed debug output                           │
│   --quiet               Suppress non-essential output                        │
│   --json                Output in machine-readable JSON format               │
│   --trace               Enable full stack traces on errors                   │
│   --timeout-ms <ms>     Set bridge operation timeout (default: 30000)        │
│   --version             Show version and exit                                │
│   --help                Show command help                                     │
│                                                                               │
│ Examples:                                                                     │
│   huesignal lights list --verbose                                             │
│   huesignal effect apply pulse -l desk-light -c green --quiet                 │
│   huesignal lights show desk-light --json | jq .                              │
└───────────────────────────────────────────────────────────────────────────────┘

┌─ ENVIRONMENT VARIABLE CONFIGURATION ─────────────────────────────────────────┐
│ Optional environment variables for agent workflows:                          │
│                                                                               │
│   HUESIGNAL_LIGHT_NAME      Default light for signals (e.g., "desk-light")   │
│   HUESIGNAL_BRIDGE_IP       Default bridge IP address                        │
│   HUESIGNAL_APP_KEY         Pre-configured app key (bypasses auth login)     │
│                                                                               │
│ Example PowerShell setup:                                                     │
│   $env:HUESIGNAL_LIGHT_NAME = "desk-light"                                    │
│   $env:HUESIGNAL_BRIDGE_IP = "192.168.1.100"                                  │
│                                                                               │
│ Example Bash setup:                                                           │
│   export HUESIGNAL_LIGHT_NAME="desk-light"                                    │
│   export HUESIGNAL_BRIDGE_IP="192.168.1.100"                                  │
└───────────────────────────────────────────────────────────────────────────────┘

┌─ SCRIPTING & AUTOMATION TIPS ────────────────────────────────────────────────┐
│ Silent operation (for background scripts):                                   │
│   huesignal effect apply pulse -l desk-light -c green --quiet                │
│                                                                               │
│ Graceful fallback (continue if huesignal unavailable):                       │
│   huesignal effect apply pulse -l desk-light -c green 2>/dev/null || true    │
│                                                                               │
│ Parse JSON output in scripts:                                                │
│   LIGHTS=$(huesignal lights list --json --quiet)                             │
│   echo $LIGHTS | jq -r '.lights[0].name'                                     │
│                                                                               │
│ Check exit codes:                                                             │
│   if huesignal doctor --quiet; then                                           │
│     echo "huesignal ready"                                                    │
│   else                                                                        │
│     echo "huesignal not configured"                                           │
│   fi                                                                          │
└───────────────────────────────────────────────────────────────────────────────┘

┌─ RECOMMENDED AGENT PATTERNS ─────────────────────────────────────────────────┐
│ These patterns are recommended for AI coding agents using Lodestar:          │
│                                                                               │
│ 1. TASK START (after lodestar_task_claim):                                   │
│    huesignal effect apply pulse -l $LIGHT -c blue -b 0.5 2>/dev/null         │
│                                                                               │
│ 2. TASK DONE (after lodestar_task_done/complete):                            │
│    huesignal effect apply pulse -l $LIGHT -c green -b 0.7 2>/dev/null        │
│                                                                               │
│ 3. ERROR/BLOCKER (on exceptions or blockers):                                │
│    huesignal effect apply blink -l $LIGHT -c red --count 3 2>/dev/null       │
│                                                                               │
│ 4. VERIFICATION (after lodestar_task_verify):                                │
│    huesignal effect apply pulse -l $LIGHT -c green -b 1.0 2>/dev/null        │
│                                                                               │
│ Why this works:                                                               │
│   - Visual feedback even when terminal is hidden/minimized                   │
│   - Non-blocking (fails silently if not configured)                          │
│   - Clear semantic meaning (blue=working, green=done, red=error)             │
│   - Compatible with any Lodestar-managed workflow                            │
└───────────────────────────────────────────────────────────────────────────────┘

┌─ COMMON WORKFLOWS ───────────────────────────────────────────────────────────┐
│ CI/CD Pipeline Success:                                                       │
│   huesignal effect apply pulse -l build-light -c green -b 0.8                │
│                                                                               │
│ CI/CD Pipeline Failure:                                                       │
│   huesignal effect apply blink -l build-light -c red --count 5               │
│                                                                               │
│ Code Review Needed:                                                           │
│   huesignal effect apply breathe -l review-light -c yellow                   │
│                                                                               │
│ Deployment In Progress:                                                       │
│   huesignal effect apply breathe -l deploy-light -c blue                     │
│                                                                               │
│ All Tests Passing:                                                            │
│   huesignal effect apply rainbow -l test-light                               │
└───────────────────────────────────────────────────────────────────────────────┘

┌─ MORE HELP ──────────────────────────────────────────────────────────────────┐
│ Command-specific help:                                                        │
│   huesignal auth --help                                                       │
│   huesignal lights --help                                                     │
│   huesignal effect --help                                                     │
│   huesignal cache --help                                                      │
│                                                                               │
│ Subcommand help:                                                              │
│   huesignal effect apply --help                                               │
│   huesignal lights list --help                                                │
│                                                                               │
│ Documentation:                                                                │
│   README.md in the repository                                                 │
│   GitHub: https://github.com/yourusername/huesignal                          │
└───────────────────────────────────────────────────────────────────────────────┘

╔══════════════════════════════════════════════════════════════════════════════╗
║  For quick reference, run: huesignal --help or huesignal <command> --help    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
