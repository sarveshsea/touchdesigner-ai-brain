# Agent Instructions

This repository is for TouchDesigner real-time projection mapping, VJ, and music-reactive systems.

## Operating Rules

1. Prefer live MCP control through Envoy when available.
2. Use TouchDesigner documentation lookup before inventing operator or parameter names.
3. Keep every meaningful network reproducible through `.tdn`, `.tox`, or Python builder scripts.
4. Treat `.toe` and `.tox` files as executable artifacts.
5. Record source, license, version, and smoke-test notes for every third-party asset.
6. For show-critical work, verify no operator errors, output resolution, FPS, audio/control inputs, and emergency blackout.

## Control Priority

1. Envoy/Embody MCP for live network edits.
2. TouchDesigner docs MCP for reference.
3. Python builder scripts through Textport/DAT.
4. Computer Use for GUI tasks and visual calibration.

## Security

- Bind local automation bridges to localhost.
- Never commit secrets from DATs, parameters, `.env`, or MCP configs.
- Do not run unknown community assets in a production `.toe`; smoke-test in a sandbox copy first.

