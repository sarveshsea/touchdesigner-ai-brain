# TouchDesigner AI Brain

A public, practical toolkit for helping AI coding agents build real-time TouchDesigner systems: projection mapping, VJ rigs, audio-reactive visuals, interactive installations, and show-control workflows.

The goal is not to replace TouchDesigner craft. The goal is to give an AI assistant enough structure, documentation, safety checks, and live-control surfaces to become useful inside a real TD session.

## What This Is

TouchDesigner is visual, live, and stateful. That makes it awkward for normal coding agents, which are happiest when they can read and edit text files. This repo is a bridge between those worlds.

It collects:

- a recommended MCP/control stack for live TouchDesigner automation,
- an audit of current TouchDesigner AI/MCP tools and useful community components,
- a project architecture for VJ and projection mapping work,
- a source registry for vetted `.tox`, `.toe`, MCP, and reference projects,
- checklists for show-readiness and third-party asset intake,
- starter TD Python builder scripts that can scaffold reusable networks.

## The Core Idea

Use multiple control layers, each for the part it is best at:

| Layer | Tooling | Best For |
| --- | --- | --- |
| Live build bridge | [Embody / Envoy](https://github.com/dylanroscover/Embody) | Creating operators, wiring networks, setting parameters, exporting `.tdn`, inspecting errors, capturing output |
| Reference bridge | [TouchDesigner Documentation MCP](https://github.com/bottobot/touchdesigner-mcp-server) | Operator/API lookup, version-aware guidance, Python docs, workflow patterns |
| GUI fallback | Computer-use automation | Palette UI, dialogs, calibration views, visual verification, parameter panes |
| Durable fallback | TD Python builder scripts | Reproducible scaffolds, repair scripts, Textport/DAT execution |

For live work, the most promising path is:

1. Run TouchDesigner.
2. Add an embedded MCP bridge such as Envoy.
3. Let the AI inspect and edit the live network through MCP.
4. Export important networks as `.tdn`, `.tox`, or Python so changes are reviewable and repeatable.

## Why This Matters

Projection mapping and VJ projects are rarely just a single cool visual. They need a whole system:

- audio analysis,
- controller/MIDI/OSC input,
- scene banks,
- effects racks,
- media playback,
- real-time monitoring,
- projector calibration,
- emergency blackout and bypass paths,
- versioned patches that can survive show pressure.

This repo is a starting point for building that system with an AI assistant that can reason about the patch, modify it, and verify it.

## Repository Map

```text
.
├── AGENTS.md                         # Agent behavior rules for this repo
├── checklists/
│   └── live-build-checklist.md       # Show and asset safety checklist
├── docs/
│   ├── architecture.md               # Proposed AI + TD project architecture
│   └── toolkit-audit.md              # Current MCP/tool/component audit
├── mcp/
│   └── .mcp.example.json             # Example local MCP client config
├── registry/
│   └── sources.yml                   # Vetted source registry
└── touchdesigner/
    └── brain_vj_builder.py           # Starter TD Python scaffold
```

## Quick Start

Clone the repo:

```bash
git clone https://github.com/sarveshsea/touchdesigner-ai-brain.git
cd touchdesigner-ai-brain
```

Review the audit:

```bash
open docs/toolkit-audit.md
```

Copy the MCP example config into the format your AI client expects:

```bash
cp mcp/.mcp.example.json .mcp.json
```

Then install and enable your chosen TouchDesigner MCP bridge. The current recommendation is [Embody / Envoy](https://github.com/dylanroscover/Embody) as the primary live-control layer, with [8beeeaaat/touchdesigner-mcp](https://github.com/8beeeaaat/touchdesigner-mcp) as a simpler WebServer DAT backup.

## Starter Network Scaffold

The first script in `touchdesigner/brain_vj_builder.py` creates a top-level `brain_vj` COMP with subsystem shells:

- `audio_in`
- `audio_analysis`
- `control_bus`
- `scene_bank`
- `fx_rack`
- `mixer`
- `mapper`
- `monitor`
- `safety`

Inside TouchDesigner's Python environment:

```python
exec(open('/path/to/touchdesigner-ai-brain/touchdesigner/brain_vj_builder.py').read())
build()
```

This is intentionally a scaffold. The next step is to replace each subsystem shell with tested operators through Envoy, TD Python, or manually curated `.tox` components.

## Useful First-Party TouchDesigner Areas

Derivative's built-in Palette and docs are the first stop before pulling in community components:

- [Palette components](https://docs.derivative.ca/Category:Palette)
- [Projection mapping](https://docs.derivative.ca/Projection_Mapping)
- `audioAnalysis`
- `moviePlayer` / `movieEngine`
- `kantanMapper`
- `camSchnappr`
- `projectorBlend`
- `stoner`
- `quadReproject`
- `particlesGpu`
- `feedback`
- `opticalFlow`
- `probe`

## Community Components To Evaluate

These are not vendored here yet. They are tracked as candidates in `registry/sources.yml` and should be smoke-tested before show use:

- [Strobber Tox](https://derivative.ca/community-post/asset/strobber-tox-%E2%94%83-top-effector-audio-reactive/71752)
- [TD Synapse](https://derivative.ca/community-post/asset/td-synapse/74347)
- [MaxMainio TD_ Components](https://github.com/MaxMainio/TD_)
- [RayTK](https://github.com/t3kt/raytk)
- [TouchDesigner Fulldome Simulator TOX](https://derivative.ca/community-post/asset/touchdesigner-fulldome-simulator-tox-beta/72740)

## Safety Model

Treat `.toe`, `.tox`, and MCP bridges as executable local code.

Before adopting any third-party asset:

- record its source URL, author, license, and download date,
- note the TouchDesigner version it was saved with,
- inspect whether it uses Python, networking, compiled plugins, or external files,
- smoke-test in a blank project,
- verify operator errors, FPS, output resolution, and crash behavior,
- only then move it into a production show file.

For MCP bridges:

- bind to localhost whenever possible,
- do not expose TD automation ports to the LAN unless you are intentionally designing a secured show-control network,
- do not store API keys or credentials in DATs, parameters, `.env`, or committed MCP config files.

## Roadmap

- Add a full Envoy setup guide for Codex and other MCP clients.
- Add a minimal audio-reactive TOP network builder.
- Add a VJ house template with scene bank, effects rack, mixer, output mapper, and safety controls.
- Add smoke-test templates for `.tox` intake.
- Add `.tdn` examples once a live Envoy project is connected.
- Add visual verification notes for projection mapping and output capture.
- Build a public compatibility matrix for TD versions, MCP tools, and community components.

## Contributing

Contributions are welcome, especially:

- reproducible TD Python builders,
- `.tdn` examples,
- safe MCP setup notes,
- projection mapping workflow notes,
- component audit reports,
- performance test results,
- links to source-available `.tox` tools with clear licenses.

Please avoid committing binary show files unless they are small, source-clear, and intentionally part of an example.

## License

MIT. See [LICENSE](LICENSE).

TouchDesigner is a product of Derivative. This project is independent and community-oriented.
