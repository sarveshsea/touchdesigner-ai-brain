# Toolkit Audit

This audit focuses on tools that help Codex build and debug TouchDesigner networks for projection mapping, VJ performance, and music-reactive visuals.

## Recommendation

Use **Embody/Envoy as the live build bridge**, **bottobot's TouchDesigner docs MCP as the reference bridge**, and **Computer Use as the UI fallback**.

That stack gives us:

- live network creation and inspection,
- accurate operator/API lookup,
- versionable network snapshots,
- GUI access for the parts of TD that are inherently visual,
- a repeatable workflow that does not depend on hand-clicked node graphs.

## Live Build Bridges

### Embody / Envoy

Source: https://github.com/dylanroscover/Embody

Status: strongest candidate.

Why it matters:

- Envoy is embedded inside the `.toe` file and exposes a localhost MCP server.
- It advertises 49 tools for creating operators, wiring, setting parameters, code execution, error inspection, TOP capture, batch operations, logging, and `.tdn` import/export.
- The `.tdn` format makes networks text-readable and diffable, which is exactly what an AI coding workflow needs.
- The project documents a localhost-only design and main-thread execution queue, which are important safety properties for TouchDesigner.

Risks:

- It can execute arbitrary Python inside TouchDesigner.
- It is a powerful local automation bridge, so it should be used only with trusted projects.
- Our installed TD version is `2023.11600`; we should smoke-test the current Embody release before adopting it as the default.

Verdict: **Primary choice**.

### 8beeeaaat/touchdesigner-mcp

Source: https://github.com/8beeeaaat/touchdesigner-mcp

Status: strong backup.

Why it matters:

- Bridges AI agents to TouchDesigner through the WebServer DAT.
- Exposes tools for node creation, deletion, parameter updates, project querying, node errors, and arbitrary Python execution.
- Has Codex-oriented installation notes and an MCP bundle flow.

Risks:

- Depends on a separate MCP server plus TD-side WebServer DAT component.
- Less focused on versionable network state than Embody's `.tdn` workflow.
- Same arbitrary-code-execution trust boundary.

Verdict: **Backup/secondary bridge**.

### Lostfound ClaudeBridge.tox

Source: https://derivative.ca/community-post/asset/simple-mcp-server-tox-connect-claude-and-touchdesigner/74528

Status: interesting, but not first pick.

Why it matters:

- A Derivative community asset posted May 04, 2026.
- Advertises a simple drag/drop `.tox` bridge that connects Claude to TouchDesigner.

Risks:

- Download is routed through Patreon.
- Public technical details are sparse compared with Embody and 8beeeaaat.
- It appears Claude Desktop-oriented rather than Codex-oriented.

Verdict: **Evaluate later if it has source/auditable code**.

### bottobot/touchdesigner-mcp-server

Source: https://github.com/bottobot/touchdesigner-mcp-server

Status: reference layer, not a live build bridge.

Why it matters:

- Provides operator documentation, Python API references, tutorials, workflow patterns, and version-aware lookup.
- Good guardrail against hallucinated operator names and stale Python/API assumptions.

Risks:

- It does not directly control a live TouchDesigner network.
- The maintainer notes that models may forget to call the tool unless the workflow strongly enforces it.

Verdict: **Use alongside Envoy**.

## Built-In Derivative Palette and Docs

### Palette Browser and OP Snippets

Source: https://docs.derivative.ca/Learn_TouchDesigner

Derivative documents OP Snippets as over 1000 functioning examples and the Palette Browser as the built-in component/media library. These should be treated as the canonical first-party component base.

Priority items to study:

- `audioAnalysis` - low/mid/high, kick, snare, rhythm, spectral centroid, and density channels.
- `moviePlayer` / `movieEngine` - reusable playback, cueing, speed, scrubbing, and audio output.
- `kantanMapper` - 2D projection mapping and masking.
- `camSchnappr` - 3D-model-based projector alignment.
- `projectorBlend` - blended projector arrays.
- `stoner` - manual image/mesh warping.
- `quadReproject` - pixel-perfect outputs for LED screens and pixel arrays.
- `particlesGpu`, `feedback`, `opticalFlow`, `multiMix`, `bloom`, `chromaKey`, `vectorScope`, `waveformMonitor`, `probe`.

## Derivative Community Assets to Track

### Strobber Tox

Source: https://derivative.ca/community-post/asset/strobber-tox-%E2%94%83-top-effector-audio-reactive/71752

Audio-reactive TOP effects for glitch/strobe workflows. The author states it is functional with TouchDesigner 2023, which matches this local machine better than 2025-only assets.

Verdict: **Good candidate for VJ effects library**.

### TD Synapse

Source: https://derivative.ca/community-post/asset/td-synapse/74347

Drop-in performance telemetry over WebSocket to a browser UI. Useful for installations and live contexts where the TD render window must stay clean.

Verdict: **Useful for monitoring**.

### MaxMainio TD_ Components

Source: https://derivative.ca/community-post/asset/repository-custom-touchdesigner-components/72852

Large image-processing component repository with docs for edge detectors, histograms, mapping, morphology, and SDFs. The author explicitly describes it as unfinished/living, so each component needs local smoke testing.

Verdict: **Useful source library, audit before show use**.

### TouchDesigner Fulldome Simulator TOX

Source: https://derivative.ca/community-post/asset/touchdesigner-fulldome-simulator-tox-beta/72740

Lightweight dome preview component. Useful if we move from flat projection mapping to planetarium/immersive dome layouts.

Risk: built in TD 2022 and not fully tested in later versions.

Verdict: **Prototype candidate**.

### RayTK

Sources:

- https://derivative.ca/community-post/asset/raytk-raymarching-masses/63620
- https://github.com/t3kt/raytk

Raymarching toolkit for TouchDesigner networks. Excellent for generative VJ worlds and volumetric-looking material. Version matters: newer RayTK releases may target TD 2025 experimental builds, so the local TD 2023 install needs a compatible release.

Verdict: **High creative value, version-gate carefully**.

## Security Notes

- Treat every `.tox` and `.toe` as executable local code.
- Prefer source-available tools with a GitHub repo and clear license.
- Keep MCP bridges bound to localhost.
- Do not expose Envoy/WebServer DAT ports to the LAN unless intentionally designing a secured show-control network.
- Never store API keys inside TD parameters or DATs committed to git.
- Vendor third-party assets with source URL, downloaded date, license, TD version, and smoke-test notes.

## Adoption Order

1. Create local git repo and commit this toolkit.
2. Install Embody into a blank TD project.
3. Enable Envoy and verify localhost MCP connection.
4. Export a trivial network to `.tdn`.
5. Use Codex to build a small audio-reactive TOP chain.
6. Add bottobot docs MCP as a reference server.
7. Add vetted `.tox` assets one at a time with smoke-test notes.
8. Build a house VJ template: audio input, analysis, cueable scenes, effects rack, mixer, mapping output, telemetry, emergency blackout.

