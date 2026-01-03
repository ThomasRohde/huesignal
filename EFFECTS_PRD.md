# Effect Programming Model - Product Requirements Document

## Overview {#overview}

This PRD defines a higher-level programming model for HueSignal effects, enabling:
- Timeline-based effect sequences
- Multi-light choreography (different lights, different effects, simultaneously)
- YAML-based effect programs
- A `--play` CLI option

## Goals {#goals}

1. Abstract effect execution into composable primitives
2. Enable multi-light choreography with parallel execution
3. Support YAML-defined effect programs
4. Maintain full backward compatibility with existing CLI

## Non-Goals {#non-goals}

- Real-time streaming effects (Hue Entertainment)
- Event-driven triggers (watching for external events)
- GUI for program creation

---

## Feature: Primitive Layer {#feature-primitives}

Atomic operations that form the foundation of all effects.

### Requirements {#feature-primitives-requirements}

1. Create `primitives.py` with dataclass-based primitives: `SetState`, `Wait`
2. Each primitive has `execute(ctx, light_id)` async method
3. Each primitive has `estimated_duration_ms()` for scheduling
4. Create `PrimitiveResult` to capture success/failure per light

### Acceptance Criteria {#feature-primitives-criteria}

- [ ] `SetState` can set on/off, brightness, color, transition_ms
- [ ] `Wait` sleeps for specified duration
- [ ] All primitives are serializable (for future YAML support)
- [ ] Unit tests cover primitive execution

---

## Feature: Execution Context {#feature-context}

Shared context for effect execution including bridge connection and state management.

### Requirements {#feature-context-requirements}

1. Create `context.py` with `ExecutionContext` dataclass
2. Wraps `HueBridgeV2` bridge connection
3. Provides `capture_state()` and `restore_state()` methods
4. Tracks captured states per light for restoration

### Acceptance Criteria {#feature-context-criteria}

- [ ] Context captures state for specified light IDs
- [ ] Context restores state and returns failed light IDs
- [ ] Context is reusable across multiple effect executions

---

## Feature: Effect Parameter Introspection {#feature-effect-params}

Declarative effect parameters for CLI introspection and validation.

### Requirements {#feature-effect-params-requirements}

1. Add `EffectParam` dataclass to `base.py` with name, type, default, description
2. Add `params: ClassVar[list[EffectParam]]` to Effect base class
3. Auto-initialize effect params from `**kwargs` in constructor
4. Add `get_params()` class method for introspection

### Acceptance Criteria {#feature-effect-params-criteria}

- [ ] Effects declare their params via class-level `params` list
- [ ] CLI can introspect effect parameters without instantiation
- [ ] Invalid param values raise clear validation errors

---

## Feature: Effect Refactoring {#feature-effect-refactor}

Refactor existing effects to support primitive-based execution.

### Requirements {#feature-effect-refactor-requirements}

1. Add optional `to_primitives()` method to Effect base class
2. Refactor Pulse effect as proof of concept
3. Refactor Blink, Breathe, Rainbow effects
4. Keep `_apply_effect()` as fallback for backward compatibility

### Acceptance Criteria {#feature-effect-refactor-criteria}

- [ ] All effects declare `params` with EffectParam metadata
- [ ] All effects implement `to_primitives()` returning primitive sequences
- [ ] Existing tests continue to pass
- [ ] Effects work with both old bridge-based and new context-based initialization

---

## Feature: CLI Parameter Handling {#feature-cli-params}

Remove hardcoded effect handling, add generic parameter support.

### Requirements {#feature-cli-params-requirements}

1. Remove `if effect_name in ("pulse", "blink")` hardcoding
2. Add `--param key=value` option (repeatable) for effect-specific params
3. Add `effect params <name>` command to list effect parameters
4. Maintain backward compat with `--count` for pulse/blink

### Acceptance Criteria {#feature-cli-params-criteria}

- [ ] `effect apply pulse --param count=3` works
- [ ] `effect params pulse` shows all parameters with types/defaults
- [ ] `effect apply pulse --count 3` still works (backward compat)
- [ ] Unknown params raise helpful errors

---

## Feature: Timeline Model {#feature-timeline}

Data structures for multi-light choreography.

### Requirements {#feature-timeline-requirements}

1. Create `programs/` package with `timeline.py`
2. Define `Action` base class with `EffectAction`, `WaitAction`, `SetAction`
3. Define `TimelineStep` with start_ms, duration_ms, action
4. Define `LightTrack` with light_pattern and steps
5. Define `Program` with name, description, tracks

### Acceptance Criteria {#feature-timeline-criteria}

- [ ] Programs can represent multiple tracks (lights)
- [ ] Tracks can have independent timelines
- [ ] Light patterns support wildcards (e.g., "office-*")
- [ ] Program.total_duration_ms() calculates correctly

---

## Feature: Scheduler {#feature-scheduler}

Execute programs with proper timing and parallel light control.

### Requirements {#feature-scheduler-requirements}

1. Create `programs/scheduler.py` with `Scheduler` class
2. Resolve light patterns to light IDs
3. Execute tracks in parallel using asyncio
4. Handle timing with proper delays between steps

### Acceptance Criteria {#feature-scheduler-criteria}

- [ ] Multiple tracks execute in parallel
- [ ] Steps execute at correct relative times
- [ ] Failed lights are tracked and reported
- [ ] State restoration works across all tracks

---

## Feature: YAML Loader {#feature-yaml-loader}

Parse YAML files into Program objects.

### Requirements {#feature-yaml-loader-requirements}

1. Create `programs/loader.py` with `load_program()` function
2. Parse tracks, steps, actions from YAML
3. Validate structure and report clear errors
4. Support effect options inline

### Acceptance Criteria {#feature-yaml-loader-criteria}

- [ ] Valid YAML loads into Program object
- [ ] Invalid YAML raises descriptive errors
- [ ] Effect names are validated against registry
- [ ] Missing required fields are caught

---

## Feature: Play Command {#feature-play-command}

CLI command to execute YAML programs.

### Requirements {#feature-play-command-requirements}

1. Add `effect play <file.yaml>` command to CLI
2. Support `--dry-run` to preview without execution
3. Report execution results (success, failures)
4. Handle Ctrl+C gracefully with state restoration

### Acceptance Criteria {#feature-play-command-criteria}

- [ ] `effect play program.yaml` executes the program
- [ ] `effect play program.yaml --dry-run` shows what would happen
- [ ] Ctrl+C restores lights to original state
- [ ] Exit code reflects success/partial failure

---

## Implementation Order {#implementation-order}

1. Primitives + Context (foundation)
2. Effect Parameter Introspection (base.py changes)
3. Pulse Effect Refactoring (proof of concept)
4. Remaining Effect Refactoring (blink, breathe, rainbow)
5. CLI Parameter Handling (remove hardcoding)
6. Timeline Model (data structures)
7. Scheduler (parallel execution)
8. YAML Loader (parsing)
9. Play Command (CLI integration)

---

## Example YAML Program {#example-yaml}

```yaml
name: celebration
description: Success celebration sequence

tracks:
  - light: office-light
    steps:
      - effect: pulse
        options:
          color: green
          brightness: 254
          count: 2
        duration_ms: 2000
      - wait: 500
      - effect: rainbow
        duration_ms: 3000

  - light: bedroom-light
    steps:
      - wait: 1000
      - effect: blink
        options:
          color: blue
          count: 3
        duration_ms: 1500
      - set:
          brightness: 100
          color: white
          transition_ms: 500
```

---

## Task Map {#task-map}

| Task ID | Title | PRD Anchor(s) | Priority |
|---------|-------|---------------|----------|
| E001 | Create primitives.py with atomic operations | #feature-primitives | 1 |
| E002 | Create context.py with ExecutionContext | #feature-context | 1 |
| E003 | Add EffectParam introspection to Effect base class | #feature-effect-params | 2 |
| E004 | Refactor Pulse effect with params and to_primitives() | #feature-effect-refactor | 2 |
| E005 | Refactor Blink effect with params and to_primitives() | #feature-effect-refactor | 3 |
| E006 | Refactor Breathe effect with params and to_primitives() | #feature-effect-refactor | 3 |
| E007 | Refactor Rainbow effect with params and to_primitives() | #feature-effect-refactor | 3 |
| E008 | Add --param option and remove hardcoded effect handling | #feature-cli-params | 4 |
| E009 | Add 'effect params' command | #feature-cli-params | 4 |
| E010 | Create programs/timeline.py with data structures | #feature-timeline | 5 |
| E011 | Create programs/scheduler.py | #feature-scheduler | 5 |
| E012 | Create programs/loader.py for YAML parsing | #feature-yaml-loader | 5 |
| E013 | Add 'effect play' command | #feature-play-command | 6 |

---

## References {#references}

- Main PRD: [PRD.md](PRD.md)
- Effect base class: [src/huesignal/effects/base.py](src/huesignal/effects/base.py)
- State management: [src/huesignal/state.py](src/huesignal/state.py)
