# HueSignal CLI - Product Requirements Document

## Overview {#overview}
HueSignal is a Windows-first command-line tool that triggers **useful, attention-grabbing (but not gimmicky)** Philips Hue lighting effects to signal developer workflow events (tests finished, builds failed, long-running jobs completed) from scripts and coding agents running in the background on the same LAN as the Hue Bridge.

The tool is **pure CLI-driven** (no user-managed config files) and prioritizes: fast invocation, predictable targeting by light **name**, and “fire-and-forget” behavior so agents can trigger an effect and immediately continue/exit.

## Goals {#goals}
1. Trigger a named lighting effect against one or more Hue lights by **name** via a single CLI command in ≤ 1 second (typical LAN conditions).
2. Provide a `lights list` command that lists all reachable lights with their names and IDs in ≤ 2 seconds.
3. Provide at least **4** production-usable effects (e.g., blink, pulse, breathe, rainbow) with consistent flags for duration and brightness.
4. Support “fire-and-forget” execution for time-based effects (CLI returns promptly while effect continues).
5. Provide `samples` output that includes copy/paste snippets for at least **5** automation contexts (PowerShell, Python, GitHub Actions, generic “agent wrapper”, and Windows scheduled task pattern).

## Non-Goals {#non-goals}
- Building a GUI or tray application.
- Remote/cloud (out-of-LAN) Hue control.
- Hue Entertainment / streaming low-latency UDP effects (out of scope).
- User-managed config files (YAML/TOML/JSON) for state; persistent state is limited to secure credential storage.
- Complex scheduling (cron-like) beyond “run this effect now”.

## Users and Use Cases {#users-use-cases}
**Primary user:** A Windows developer who owns a Philips Hue Bridge + lights and runs local automations or coding agents.

**Secondary user:** Team members who run the same CLI from CI runners on a LAN-connected build box (optional).

**Key use cases**
- Tests finished: green pulse for pass, red blink for fail.
- Long job completed: breathing amber to indicate “come back”.
- Agent needs attention: rapid short blink on a desk lamp.
- “Quiet hours” scripting: lower brightness pulses rather than strobe.

## Assumptions and Open Questions {#assumptions-open-questions}
**Assumptions**
- Hue Bridge is reachable on the same LAN.
- Users can physically press the Bridge link button during initial auth.
- Light names are stable and mostly unique; when not unique, the CLI will require disambiguation.
- Many target lights are dimmable; some are color-capable.

**Open questions**
- Should we support selecting by **room/zone** later (even if selection is “by name” now)?
- Should the default be `--restore` (restore original state) for all effects, or only for non-trivial effects?
- Should the CLI expose a global `--bridge-ip` override, or always auto-discover when possible?

---

## Feature: Hue library selection and architecture {#feature-library-selection}
Choose and document the Hue integration approach.

### Requirements {#feature-library-selection-requirements}
1. Use `aiohue` as the primary Hue integration library (supports Hue API v2 and v1).
2. Implement network discovery using mDNS and/or the Hue discovery endpoint, avoiding UPnP.
3. Provide a documented fallback path if discovery fails (manual `--bridge-ip`).
4. Document the public rationale in `README.md`.

### Acceptance Criteria {#feature-library-selection-criteria}
- [ ] `README.md` states the chosen library (`aiohue`) and why.
- [ ] Discovery does not require UPnP.
- [ ] CLI supports `--bridge-ip` to bypass discovery.
- [ ] `pip install` succeeds on Python 3.13 on Windows.

### Implementation Notes {#feature-library-selection-notes}
- `aiohue` is an async library that supports both Hue API v2 and v1.  
  References: https://github.com/home-assistant-libs/aiohue and https://pypi.org/project/aiohue/
- Hue indicates UPnP discovery is deprecated; prefer mDNS and discovery.meethue.com:  
  Reference: https://developers.meethue.com/new-hue-api/

---

## Feature: CLI skeleton with Typer {#feature-cli-skeleton}
Create the CLI structure, global options, and help text.

### Requirements {#feature-cli-skeleton-requirements}
1. Implement a Typer app with top-level command group `huesignal`.
2. Add global options: `--bridge-ip`, `--verbose`, `--quiet`, `--json`.
3. Implement command groups: `auth`, `lights`, `effect`, `samples`.
4. Ensure predictable exit codes (0 success, non-zero error).

### Acceptance Criteria {#feature-cli-skeleton-criteria}
- [ ] `huesignal --help` shows all command groups and global options.
- [ ] `huesignal lights --help` and `huesignal effect --help` work without raising exceptions.
- [ ] Unknown commands return a non-zero exit code.
- [ ] `--quiet` suppresses non-essential output.

---

## Feature: Bridge discovery {#feature-bridge-discovery}
Discover the Hue Bridge IP on the local network (Windows).

### Requirements {#feature-bridge-discovery-requirements}
1. Implement discovery by calling the Hue discovery endpoint (`https://discovery.meethue.com/`) when internet is available.
2. Implement local mDNS discovery as a fallback (e.g., `_hue._tcp.local` via `zeroconf`).
3. If multiple bridges are found, present a selection prompt unless `--json` is set.
4. Allow bypass via `--bridge-ip`.

### Acceptance Criteria {#feature-bridge-discovery-criteria}
- [ ] With `--bridge-ip`, discovery is not executed.
- [ ] If discovery returns >1 bridge and `--json` is not set, user can select one interactively.
- [ ] If discovery fails, CLI prints a clear instruction to use `--bridge-ip`.
- [ ] `--json` returns machine-readable discovery output.

### Implementation Notes {#feature-bridge-discovery-notes}
- Keep selection deterministic: sort by IP address and/or bridge ID before presenting.
- Consider short discovery timeout (e.g., 1–2 seconds) to keep CLI snappy.

---

## Feature: Authentication (pairing) and secure credential storage {#feature-auth}
Pair with the Hue Bridge and persist the app key without user-managed config files.

### Requirements {#feature-auth-requirements}
1. Provide `huesignal auth login` that creates an app key after the user presses the Bridge link button.
2. Store the app key in Windows Credential Manager via `keyring` (default).
3. Allow `--print` to output the key to stdout for scripting instead of storing it.
4. Allow supplying credentials via env var `HUESIGNAL_APP_KEY` (takes precedence over keyring).

### Acceptance Criteria {#feature-auth-criteria}
- [ ] Successful `auth login` results in a stored credential retrievable on the next run.
- [ ] If link button wasn’t pressed, the command exits non-zero with an actionable message.
- [ ] If `HUESIGNAL_APP_KEY` is set, the CLI uses it without accessing keyring.
- [ ] `--print` outputs only the key and exits 0 on success.

### Implementation Notes {#feature-auth-notes}
- Never log secrets; redact in `--verbose`.

---

## Feature: List available lights {#feature-list-lights}
List lights, their status, and capabilities.

### Requirements {#feature-list-lights-requirements}
1. Implement `huesignal lights list` to print a table (default) of light name, ID, on/off, reachable, and color/dim support.
2. Support `--json` output to return a structured list.
3. Include a `--filter` option supporting substring match on name.
4. Provide `huesignal lights show "<name>"` for detailed info.

### Acceptance Criteria {#feature-list-lights-criteria}
- [ ] `lights list` returns at least name and ID for each light.
- [ ] `lights list --filter desk` returns only matching lights (case-insensitive).
- [ ] `lights list --json` outputs valid JSON to stdout.
- [ ] `lights show "<name>"` exits non-zero if the name is not found.

---

## Feature: Resolve lights by name {#feature-light-selection}
Select 1+ lights by name consistently across commands.

### Requirements {#feature-light-selection-requirements}
1. Accept `--light "<name>"` (repeatable) and `--lights "<name1>,<name2>"` on effect commands.
2. Match names case-insensitively.
3. If multiple lights match, require disambiguation by exact name or by ID.
4. Support `--dry-run` to show resolved targets without executing.

### Acceptance Criteria {#feature-light-selection-criteria}
- [ ] `--light "Desk Lamp"` resolves the intended light when the name exists.
- [ ] Ambiguous substring matches produce a non-zero exit code and list candidates.
- [ ] `--dry-run` prints resolved light IDs and exits 0 without changing lights.
- [ ] `--light-id <id>` works even if name matching fails.

---

## Feature: Effect command framework {#feature-effect-framework}
Shared effect options and consistent CLI UX.

### Requirements {#feature-effect-framework-requirements}
1. Implement `huesignal effect run <effect-name>` as the primary invocation.
2. Standard flags: `--duration-ms`, `--brightness 1-254`, `--color <name|hex>`, `--restore/--no-restore`.
3. Provide `huesignal effect list` to list built-in effects and parameters.
4. Validate inputs with friendly errors (range checks, unsupported color on non-color lights).

### Acceptance Criteria {#feature-effect-framework-criteria}
- [ ] `effect list` prints available effects.
- [ ] Invalid brightness (e.g., 0 or 999) returns non-zero with a clear message.
- [ ] If a color effect targets a non-color light, the CLI either downgrades safely (brightness-only) or errors (documented).
- [ ] `--duration-ms` defaults per-effect if not provided.

### Implementation Notes {#feature-effect-framework-notes}
- Prefer named colors mapped to Hue xy values or hue/sat; allow `#RRGGBB` where supported.

---

## Feature: Effect - Blink {#feature-effect-blink}
Short “look at me” notification using minimal bridge calls when possible.

### Requirements {#feature-effect-blink-requirements}
1. Provide effect name `blink`.
2. Support `--count` (default 1) and `--interval-ms` (default 500).
3. If the Hue API supports an “alert” feature for the targeted lights, use it; otherwise emulate via on/off toggles.
4. Respect `--restore`.

### Acceptance Criteria {#feature-effect-blink-criteria}
- [ ] `effect run blink --light "Desk Lamp"` causes a visible blink.
- [ ] `--count 3` triggers exactly 3 blinks (within timing tolerance).
- [ ] With `--restore`, the light returns to its original on/off + brightness.
- [ ] Command returns promptly (see fire-and-forget runner feature for time-based execution).

---

## Feature: Effect - Pulse {#feature-effect-pulse}
A short, readable pulse (brightness or color) indicating success/failure.

### Requirements {#feature-effect-pulse-requirements}
1. Provide effect name `pulse`.
2. Pulse from current brightness to `--brightness` and back (or from current color to `--color` and back when supported).
3. Support `--count` and `--interval-ms`.
4. Respect `--restore`.

### Acceptance Criteria {#feature-effect-pulse-criteria}
- [ ] `pulse` changes brightness perceptibly and returns.
- [ ] On a color-capable light, `--color green` visibly changes the light color during the pulse.
- [ ] `--count` produces repeatable pulse count.
- [ ] With `--restore`, light ends in original state.

---

## Feature: Effect - Breathe {#feature-effect-breathe}
Smooth “breathing” effect to signal long-running background activity completion.

### Requirements {#feature-effect-breathe-requirements}
1. Provide effect name `breathe`.
2. Support `--duration-ms` (total) and `--period-ms` (breath cycle).
3. Use stepped brightness changes (rate-limited) to avoid bridge overload.
4. Respect `--restore`.

### Acceptance Criteria {#feature-effect-breathe-criteria}
- [ ] `breathe` runs for approximately `--duration-ms` (±10% tolerance).
- [ ] Per-step update rate does not exceed a documented safe threshold.
- [ ] With `--restore`, light returns to pre-effect state at end.
- [ ] CLI returns promptly in fire-and-forget mode.

---

## Feature: Effect - Rainbow {#feature-effect-rainbow}
Color cycle for “interesting but still useful” alerts (e.g., deploy complete).

### Requirements {#feature-effect-rainbow-requirements}
1. Provide effect name `rainbow`.
2. Support `--duration-ms` and `--step-ms` for cycle speed.
3. If targeting non-color lights, degrade to brightness wave (documented).
4. Respect `--restore`.

### Acceptance Criteria {#feature-effect-rainbow-criteria}
- [ ] On color lights, `rainbow` cycles through multiple distinct colors.
- [ ] On non-color lights, `rainbow` produces a brightness-based alternative (or errors) consistently.
- [ ] `--step-ms` affects the perceptible speed of change.
- [ ] With `--restore`, original state is restored.

---

## Feature: Capture and restore state {#feature-restore-state}
Restore lights to original state after an effect completes.

### Requirements {#feature-restore-state-requirements}
1. Before running an effect, capture a minimal state snapshot per light (on/off, brightness, and color info when present).
2. Store snapshot in-memory for synchronous effects and serialize it for detached runner effects.
3. Restore state at end when `--restore` is enabled.
4. Provide `--no-restore` to skip restoration.

### Acceptance Criteria {#feature-restore-state-criteria}
- [ ] With `--restore`, effects end with lights matching the captured state (within device precision).
- [ ] With `--no-restore`, effects do not attempt to revert state.
- [ ] State capture does not include secrets and is safe to log in `--verbose` (redacted as needed).
- [ ] Restore failures return non-zero only if explicitly requested via `--strict-restore`.

---

## Feature: Fire-and-forget runner (detached process) {#feature-detach-runner}
Time-based effects must continue after the CLI command returns.

### Requirements {#feature-detach-runner-requirements}
1. For effects requiring a timeline (multiple updates), spawn a detached child process on Windows by default.
2. Pass necessary parameters + state snapshot to the child via a short JSON payload (argv or temp file) without user-managed config files.
3. Parent process returns as soon as child process confirms it started (best-effort).
4. Provide `--no-detach` for debugging (runs synchronously).

### Acceptance Criteria {#feature-detach-runner-criteria}
- [ ] `effect run breathe ...` returns control to the shell quickly while lights continue breathing.
- [ ] `--no-detach` blocks until effect completes.
- [ ] Detached runner does not open a new console window.
- [ ] If the runner cannot start, parent exits non-zero with a clear error.

### Implementation Notes {#feature-detach-runner-notes}
- Use `subprocess.Popen(..., creationflags=DETACHED_PROCESS|CREATE_NEW_PROCESS_GROUP)` on Windows.
- Prefer passing payload via a temp file if argv length is a concern; delete temp file after read.

---

## Feature: Samples for automation agents {#feature-samples}
Generate copy/paste usage patterns without requiring config files.

### Requirements {#feature-samples-requirements}
1. Implement `huesignal samples list` to show available sample types.
2. Implement `huesignal samples show <sample>` to print a snippet to stdout.
3. Include at least these samples: `powershell-exitcode`, `python-exitcode`, `github-actions`, `generic-agent-wrapper`, `windows-task-scheduler`.
4. Allow customizing placeholders via flags (e.g., `--light`, `--bridge-ip`).

### Acceptance Criteria {#feature-samples-criteria}
- [ ] `samples list` outputs at least 5 sample names.
- [ ] `samples show github-actions` prints a valid YAML step snippet (no external files required).
- [ ] `samples show powershell-exitcode` shows failure/success mapping using `$LASTEXITCODE`.
- [ ] Placeholders can be overridden via CLI flags.

---

## Feature: Machine-readable output and exit codes {#feature-exit-codes}
Enable scripting without fragile parsing.

### Requirements {#feature-exit-codes-requirements}
1. Provide `--json` output mode for `lights list`, `lights show`, `effect list`, and `discover`.
2. Ensure non-zero exit codes for: auth failure, no lights matched, ambiguous match, bridge unreachable.
3. Provide `--quiet` to suppress human messages (but not JSON).
4. Provide `--timeout-ms` for bridge operations.

### Acceptance Criteria {#feature-exit-codes-criteria}
- [ ] `--json` outputs valid JSON demonstrating no extra stdout text.
- [ ] Ambiguous light match returns a specific non-zero code and lists candidates to stderr.
- [ ] Bridge timeout returns non-zero within `--timeout-ms` + small overhead.
- [ ] `--quiet` suppresses tables and informational logs.

---

## Feature: Logging and diagnostics {#feature-logging}
Help debug connectivity and mapping issues.

### Requirements {#feature-logging-requirements}
1. Implement `--verbose` to show request/response summaries without secrets.
2. Provide `huesignal doctor` to check: bridge reachable, credential present, basic API call works.
3. Provide `--trace` (optional) to include stack traces for unexpected exceptions.
4. Log to stderr; keep stdout clean for data output.

### Acceptance Criteria {#feature-logging-criteria}
- [ ] `doctor` exits 0 when bridge/auth are functional, non-zero otherwise.
- [ ] `--verbose` does not print app keys or credentials.
- [ ] Errors are printed to stderr, not stdout.
- [ ] `--trace` includes a Python traceback on unexpected errors.

---

## Feature: Packaging and distribution {#feature-packaging}
Make installation straightforward on Windows.

### Requirements {#feature-packaging-requirements}
1. Provide a Python package with console script entry point `huesignal`.
2. Document recommended installs: `pipx install huesignal` and `pip install huesignal`.
3. Pin and document dependencies: `typer`, `aiohue`, `keyring`, `zeroconf` (optional for mDNS).
4. Provide a `--version` command.

### Acceptance Criteria {#feature-packaging-criteria}
- [ ] `pipx install .` creates a working `huesignal` command on Windows.
- [ ] `huesignal --version` prints a semver string and exits 0.
- [ ] `pip install .` works in a venv on Python 3.13.
- [ ] README includes a 60-second quickstart.

---

## Feature: Unit tests for core logic {#feature-tests-unit}
Confidence for name matching, payload serialization, and CLI parsing.

### Requirements {#feature-tests-unit-requirements}
1. Add unit tests for light name resolution (exact, case-insensitive, ambiguous).
2. Add unit tests for effect parameter validation (brightness ranges, durations).
3. Add unit tests for detached runner payload encode/decode.
4. Use a consistent test runner (e.g., `pytest`) and CI-friendly defaults.

### Acceptance Criteria {#feature-tests-unit-criteria}
- [ ] `pytest` passes locally with no Hue hardware required.
- [ ] Name resolution tests cover exact, partial, ambiguous, and not-found cases.
- [ ] Invalid parameter tests assert non-zero exit codes.
- [ ] Payload tests ensure round-trip equality.

---

## Feature: Integration test mode (optional) {#feature-tests-integration}
Hardware-backed smoke tests when a bridge is available.

### Requirements {#feature-tests-integration-requirements}
1. Add an opt-in integration test suite gated by env vars (`HUESIGNAL_BRIDGE_IP`, `HUESIGNAL_APP_KEY`).
2. Implement a smoke test that lists lights and toggles a single named light (safely).
3. Ensure integration tests are skipped by default.
4. Document safety warnings.

### Acceptance Criteria {#feature-tests-integration-criteria}
- [ ] Running tests without env vars skips integration tests.
- [ ] With env vars set, smoke test can list lights and perform one reversible action.
- [ ] Integration tests restore original state after running.
- [ ] Documentation warns about physical side effects.

---

## Constraints {#constraints}
### Performance {#constraints-performance}
- Prefer a single connection/session per command execution.
- Keep default timeouts short; allow override via `--timeout-ms`.
- Rate-limit effect step updates to avoid bridge overload.

### Security and Privacy {#constraints-security-privacy}
- Store credentials in Windows Credential Manager via `keyring` by default.
- Support env var credentials for CI, but never log secrets.
- Avoid writing persistent user-managed config files; temporary files (if needed) must be short-lived and deleted.

### Compliance and Auditability {#constraints-compliance}
- No regulated data; ensure logs do not include secrets.
- Provide deterministic exit codes for automation.

## Success Metrics {#success-metrics}
- ≥ 90% of time-based effect invocations return within 1 second (excluding `--no-detach`).
- `lights list` succeeds on the first try in ≥ 95% of runs on a stable LAN.
- Users can complete first-time setup (auth + first effect) in ≤ 2 minutes using the Quickstart.
- At least 5 automation samples are used successfully (validated by user feedback or dogfooding).

## Implementation Order {#implementation-order}
1. CLI skeleton + packaging basics (feature-cli-skeleton, feature-packaging)
2. Library selection + bridge connection plumbing (feature-library-selection)
3. Discovery + manual override (feature-bridge-discovery)
4. Auth + keyring storage (feature-auth)
5. Lights list/show + name resolution (feature-list-lights, feature-light-selection)
6. Effect framework + restore (feature-effect-framework, feature-restore-state)
7. Detached runner (feature-detach-runner)
8. Effects (blink → pulse → breathe → rainbow) (feature-effect-blink, feature-effect-pulse, feature-effect-breathe, feature-effect-rainbow)
9. Samples + doctor + logging polish (feature-samples, feature-logging, feature-exit-codes)
10. Tests (unit, optional integration) (feature-tests-unit, feature-tests-integration)

## Task Map (recommended) {#task-map}
| Task Title | PRD Anchor(s) | Estimated Chunk (min) |
|---|---|---:|
| Scaffold Typer CLI + global options | #feature-cli-skeleton | 30 |
| Add aiohue client wrapper + session lifecycle | #feature-library-selection | 30 |
| Implement discovery (endpoint) + `--bridge-ip` | #feature-bridge-discovery | 30 |
| Add mDNS discovery fallback (zeroconf) | #feature-bridge-discovery | 30 |
| Implement `auth login` + keyring store | #feature-auth | 30 |
| Implement `lights list` (table + json) | #feature-list-lights | 30 |
| Implement name resolver + `--dry-run` | #feature-light-selection | 30 |
| Implement effect framework + arg validation | #feature-effect-framework | 30 |
| Implement state snapshot + restore | #feature-restore-state | 30 |
| Implement detached runner process on Windows | #feature-detach-runner | 60 |
| Implement `blink` | #feature-effect-blink | 30 |
| Implement `pulse` | #feature-effect-pulse | 30 |
| Implement `breathe` (rate-limited) | #feature-effect-breathe | 60 |
| Implement `rainbow` | #feature-effect-rainbow | 60 |
| Add `samples` commands + templates | #feature-samples | 30 |
| Add `doctor` + logging modes | #feature-logging | 30 |
| Add unit tests suite | #feature-tests-unit | 60 |
| Add opt-in integration tests | #feature-tests-integration | 30 |

## References {#references}
- aiohue (GitHub): https://github.com/home-assistant-libs/aiohue
- aiohue (PyPI): https://pypi.org/project/aiohue/
- Hue “New Hue API” (discovery guidance): https://developers.meethue.com/new-hue-api/
- Hue Developer Portal: https://developers.meethue.com/
- phue2 (alternative library with CLI): https://pypi.org/project/phue2/
