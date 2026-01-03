# huesignal Examples

A collection of YAML programs demonstrating huesignal's choreography capabilities.

## Quick Start

```bash
# Run any example
huesignal run examples/celebration.yaml

# Validate without executing (no bridge needed)
huesignal run examples/celebration.yaml --validate

# Preview timing
huesignal run examples/celebration.yaml --dry-run
```

## Available Programs

| Program | Description | Duration |
|---------|-------------|----------|
| [celebration.yaml](celebration.yaml) | Victory burst with rainbow finale | ~7 seconds |
| [sunrise-wakeup.yaml](sunrise-wakeup.yaml) | Gentle dawn simulation | ~15 seconds |
| [focus-mode.yaml](focus-mode.yaml) | Ambient breathing for deep work | ~33 seconds |
| [build-pipeline.yaml](build-pipeline.yaml) | CI/CD stage visualization | ~12 seconds |
| [alert-cascade.yaml](alert-cascade.yaml) | Critical event attention sequence | ~9 seconds |
| [agent-workflow.yaml](agent-workflow.yaml) | Complete AI agent task cycle | ~16 seconds |
| [meeting-countdown.yaml](meeting-countdown.yaml) | Progressive urgency timer | ~20 seconds |
| [symphony.yaml](symphony.yaml) | Multi-light coordinated choreography | ~9 seconds |
| [parallel-demo.yaml](parallel-demo.yaml) | Parallel step execution demo | ~5 seconds |

## Customizing

All examples use `PC` as the light name. Replace with your light name:

```yaml
tracks:
  - light: your-light-name   # ← Change this
    steps:
      ...
```

Or use patterns to target multiple lights:

```yaml
tracks:
  - light: "office-*"        # All lights starting with "office-"
```

## Parallel Execution

Use `start_ms` to run multiple effects at the same time on one light:

```yaml
steps:
  - start_ms: 0              # Both start at time 0
    effect: pulse
    duration_ms: 2000
  - start_ms: 0              # Runs in parallel!
    effect: breathe
    duration_ms: 2000
```

See [parallel-demo.yaml](parallel-demo.yaml) for a complete example.

## Creating Your Own

See the [YAML Schema](../README.md#yaml-schema) section in the main README for full documentation.

## Tips

- **Shorter durations** = snappier, more energetic
- **Longer transitions** = smoother, more relaxed
- **Multiple tracks** = multi-light choreography (run in parallel)
- **wait steps** = create drama and anticipation
