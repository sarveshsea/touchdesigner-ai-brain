# Architecture

## Mental Model

The toolkit should behave like a production assistant for TouchDesigner, not a loose pile of prompts.

Codex should be able to:

1. inspect the current project,
2. understand the intended show/installation,
3. generate or modify TD networks,
4. verify that operators cook without errors,
5. capture visual output,
6. save a text representation of the network,
7. explain what changed in performance terms.

## Layers

### 1. Intent Layer

Plain-language briefs for the thing being built:

- venue or projection surface,
- projector count and resolution,
- audio source,
- controller source,
- visual style,
- latency budget,
- show-control constraints,
- fail-safe behavior.

### 2. Reference Layer

The agent uses Derivative docs, OP Snippets, and the docs MCP before creating unfamiliar operators.

Required habit:

- Ask docs MCP for operator/par names when uncertain.
- Prefer Palette components when they match the job.
- Record every third-party `.tox` with source and TD version.

### 3. Build Layer

Primary:

- Envoy MCP tools: create operators, connect operators, set parameters, execute Python, export/import `.tdn`, inspect errors, capture TOPs.

Fallback:

- TD Python builder scripts pasted/run through Textport or a DAT.

GUI-only:

- Computer Use for palette UI, dialogs, parameter windows, calibration views, and screenshot-guided work.

### 4. Project Layer

Recommended project folder:

```text
show-name/
  show-name.toe
  .mcp.json
  AGENTS.md
  README.md
  externalized/
  assets/
    footage/
    audio/
    models/
    calibration/
  td/
    builders/
    scripts/
    shaders/
  tox/
    first_party/
    third_party/
  tdn/
  docs/
    cue_sheet.md
    mapping_notes.md
    performance_budget.md
    asset_manifest.md
```

### 5. Verification Layer

Minimum verification for every generated network:

- no operator errors,
- TOP output is non-black unless expected,
- FPS/cook times acceptable,
- output resolution matches target,
- audio/control channels are present,
- mapping output has a bypass/blackout path,
- changes are exported to `.tdn` or scripted form.

## First House Template

Build a reusable `/project1/brain_vj` COMP with:

- `audio_in` - Audio Device In CHOP or file fallback.
- `audio_analysis` - Palette `audioAnalysis`.
- `control_bus` - normalized CHOP channels for low/mid/high/kick/snare/rhythm/manual controls.
- `scene_bank` - switchable visual scenes.
- `fx_rack` - feedback, strobe, bloom, displacement, color, pixel, blur, edge.
- `mixer` - crossfade and layer compositing.
- `mapper` - Kantan/Corner Pin/Stoner/Projector Blend path depending on setup.
- `monitor` - probe/TD Synapse hooks.
- `safety` - blackout, freeze, bypass, show FPS, emergency reset.

