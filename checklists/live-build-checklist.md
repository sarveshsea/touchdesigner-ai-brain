# Live Build Checklist

## Before Automation

- Start from a copy of the `.toe` file.
- Confirm target TD version and license type.
- Confirm timeline is running.
- Confirm project folder is a git repo if using Embody auto `.mcp.json`.
- Confirm MCP bridge is bound to localhost only.
- Confirm no secrets are stored in parameters, DATs, or local config files.

## Before Show Use

- Test at target resolution and refresh rate.
- Verify audio input routing and fallback.
- Verify controller/MIDI/OSC routing and fallback.
- Verify blackout, freeze, bypass, and reset.
- Verify mapping calibration is saved and restorable.
- Verify logs/performance telemetry are visible outside the projection output.
- Record known-good FPS and GPU/CPU cook budgets.

## Asset Intake

For each `.tox` or `.toe`:

- source URL,
- author,
- license,
- downloaded date,
- TD version saved with,
- whether it uses Python, network, external files, or compiled plugins,
- smoke-test result,
- visual screenshot or output capture,
- decision: keep, sandbox, rewrite, or reject.

