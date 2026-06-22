"""
Starter TouchDesigner builder sketch for a reusable VJ brain network.

Run inside TouchDesigner's Python environment, ideally in a blank copied project.
This is intentionally conservative: it creates a top-level COMP structure and
labels the intended subsystems, but leaves operator-specific implementation to
Envoy/TD docs once the live MCP bridge is connected.
"""

ROOT_NAME = "brain_vj"


def _destroy_existing(parent, name):
    existing = parent.op(name)
    if existing is not None:
        existing.destroy()


def _create_base(parent, name, x, y, comment):
    comp = parent.create(baseCOMP, name)
    comp.nodeX = x
    comp.nodeY = y
    comp.comment = comment
    comp.color = (0.15, 0.15, 0.15)
    return comp


def build(parent=None):
    parent = parent or op("/project1")
    _destroy_existing(parent, ROOT_NAME)

    root = parent.create(baseCOMP, ROOT_NAME)
    root.nodeX = 0
    root.nodeY = 0
    root.comment = "Reusable audio-reactive VJ/projection mapping brain."

    _create_base(root, "audio_in", -900, 300, "Audio Device In or file fallback.")
    _create_base(root, "audio_analysis", -650, 300, "Palette audioAnalysis and signal cleanup.")
    _create_base(root, "control_bus", -400, 300, "Normalized low/mid/high/kick/snare/rhythm/manual channels.")
    _create_base(root, "scene_bank", -150, 300, "Switchable generators and media scenes.")
    _create_base(root, "fx_rack", 100, 300, "Feedback, strobe, blur, displacement, color, pixel, edge.")
    _create_base(root, "mixer", 350, 300, "Layer compositing, crossfade, keying, blend modes.")
    _create_base(root, "mapper", 600, 300, "Kantan/Stoner/ProjectorBlend/QuadReproject output path.")
    _create_base(root, "monitor", 850, 300, "Probe, logs, FPS, cook budget, TD Synapse hooks.")
    _create_base(root, "safety", 1100, 300, "Blackout, freeze, bypass, emergency reset.")

    text = root.create(textDAT, "README")
    text.text = (
        "brain_vj scaffold\\n"
        "Next step: connect Envoy MCP and replace each subsystem shell with tested operators.\\n"
        "Keep every generated network exportable as .tdn or rebuildable from Python.\\n"
    )
    text.nodeX = 0
    text.nodeY = -150

    return root


if __name__ == "__main__":
    build()

