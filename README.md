# TouchDesigner AI Brain

Local toolkit draft for building real-time TouchDesigner projection mapping, VJ, and audio-reactive systems with Codex.

Generated: 2026-06-22

## Current Local State

- TouchDesigner is installed and running.
- Detected TouchDesigner app version: `2023.11600`.
- Computer Use is available for UI-level interaction: app discovery, clicks, typing, keypresses, drag, scroll, and settable accessibility values.
- `gh` is authenticated as `sarveshsea`, but no existing obvious TouchDesigner/VJ repo was found in the repo scan.
- No local `.toe` or `.tox` files were found in the initial home-directory scan outside `Library`.

## Recommended Control Stack

1. **Envoy / Embody MCP** for live TouchDesigner operations.
   Use this as the primary bridge for creating operators, wiring networks, setting parameters, exporting `.tdn`, inspecting errors, and capturing TOP output.

2. **TouchDesigner Documentation MCP** for operator/API correctness.
   Use this as the reference layer so generated Python and operator chains stay aligned with current TouchDesigner docs.

3. **Computer Use** for GUI-only work.
   Use it for visual calibration panes, parameter dialogs, palette interactions, file prompts, and direct app workflows that MCP cannot reach.

4. **TD Python builder scripts** as the durable fallback.
   Every important network should be reproducible from a script or `.tdn`, not only a manually edited `.toe`.

## Repository Shape

- `docs/` - audit, architecture, setup, and workflow notes.
- `mcp/` - example MCP client config.
- `registry/` - source registry for vetted `.tox`, `.toe`, MCP, and reference projects.
- `touchdesigner/` - Python builders and reusable TD-side scripts.
- `checklists/` - live-show and security checklists.

## Next Decisions

- Pick the GitHub repo name. Suggested: `touchdesigner-ai-brain`.
- Pick visibility. Suggested: private until we add third-party asset provenance and license notes.
- Choose the primary live bridge. Suggested: Embody/Envoy first, with 8beeeaaat/touchdesigner-mcp as the simpler WebServer DAT backup.

