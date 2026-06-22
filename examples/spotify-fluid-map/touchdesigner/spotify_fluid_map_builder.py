"""
Build the Spotify Fluid Map V1 network in TouchDesigner.

Run this inside TouchDesigner's Python environment:

    exec(open('/absolute/path/to/spotify_fluid_map_builder.py').read())
    build()

The resulting public contract is:
    /project1/spotify_fluid_map/out1
    /project1/spotify_fluid_map/mapper/out_projector
"""

ROOT_NAME = "spotify_fluid_map"
OSC_PORT = 7000
WIDTH = 1920
HEIGHT = 1080


def _destroy_existing(parent, name):
    existing = parent.op(name)
    if existing is not None:
        existing.destroy()


def _create(parent, op_type, name, x=0, y=0, color=None):
    node = parent.create(op_type, name)
    node.nodeX = x
    node.nodeY = y
    if color is not None:
        node.color = color
    return node


def _set_par(node, name, value=None, expr=None):
    par = getattr(node.par, name, None)
    if par is None:
        node.comment = (node.comment + "\n" if node.comment else "") + "Missing par: " + name
        return
    if expr is not None:
        par.expr = expr
    else:
        par.val = value


def _connect(dst, src, index=0):
    try:
        dst.setInput(index, src)
    except Exception:
        try:
            dst.inputConnectors[index].connect(src)
        except Exception as err:
            dst.comment = (dst.comment + "\n" if dst.comment else "") + "Connect failed: " + str(err)


def _append_controls(root):
    page = root.appendCustomPage("Controls")
    page.appendToggle("Blackout", label="Blackout")[0].default = False
    page.appendToggle("Freeze", label="Freeze")[0].default = False
    page.appendToggle("Showgrid", label="Show Grid")[0].default = False
    page.appendPulse("Resetfeedback", label="Reset Feedback")
    page.appendStr("Audiodevice", label="Audio Device")[0].default = "BlackHole 2ch"
    page.appendFloat("Sensitivity", label="Sensitivity")[0].default = 1.0
    page.appendFloat("Brightness", label="Brightness")[0].default = 1.0


def _make_text(parent, name, text, x=0, y=0):
    dat = _create(parent, "textDAT", name, x, y)
    dat.text = text
    return dat


def _build_spotify_meta(root):
    comp = _create(root, "baseCOMP", "spotify_meta", -900, 350, (0.18, 0.15, 0.22))
    comp.comment = "OSC metadata from bridge/spotify_bridge.py on UDP port 7000."

    osc = _create(comp, "oscinDAT", "osc_in", -200, 100)
    _set_par(osc, "port", OSC_PORT)
    _set_par(osc, "active", True)

    callbacks = _make_text(comp, "metadata_script", METADATA_SCRIPT, 50, 100)
    meta_chop = _create(comp, "scriptCHOP", "metadata_chop", 300, 100)
    _set_par(meta_chop, "callbacks", callbacks.path)
    null_meta = _create(comp, "nullCHOP", "null_meta", 520, 100)
    _connect(null_meta, meta_chop)

    notes = _make_text(
        comp,
        "README",
        "Receives all /spotify/* OSC messages. Numeric state is exposed through null_meta.\n"
        "String metadata remains visible in osc_in and runtime/now_playing.json.",
        -200,
        -120,
    )
    notes.viewer = True
    return comp


def _build_audio(root):
    comp = _create(root, "baseCOMP", "audio_in", -900, 50, (0.12, 0.18, 0.22))
    comp.comment = "Set system output to a Multi-Output Device including BlackHole, then select BlackHole here."

    audio = _create(comp, "audiodeviceinCHOP", "audio_device_in", -250, 100)
    _set_par(audio, "driver", "default")
    _set_par(audio, "device", expr="parent(2).par.Audiodevice")
    _set_par(audio, "active", True)

    gain = _create(comp, "mathCHOP", "input_gain", -40, 100)
    _connect(gain, audio)
    _set_par(gain, "multiply", expr="parent(2).par.Sensitivity")

    null_audio = _create(comp, "nullCHOP", "null_audio", 180, 100)
    _connect(null_audio, gain)
    return comp


def _build_audio_analysis(root):
    comp = _create(root, "baseCOMP", "audio_analysis", -550, 50, (0.12, 0.22, 0.16))
    comp.comment = "Script CHOP performs lightweight FFT bands from Audio Device In."

    callbacks = _make_text(comp, "audio_analysis_script", AUDIO_ANALYSIS_SCRIPT, -200, 120)
    analysis = _create(comp, "scriptCHOP", "analysis_chop", 80, 120)
    _set_par(analysis, "callbacks", callbacks.path)
    audio_source = root.op("audio_in/null_audio")
    if audio_source:
        _connect(analysis, audio_source)

    smooth = _create(comp, "filterCHOP", "smooth", 300, 120)
    _connect(smooth, analysis)
    _set_par(smooth, "width", 0.12)

    null_audio = _create(comp, "nullCHOP", "null_audio", 520, 120)
    _connect(null_audio, smooth)
    return comp


def _build_control_bus(root):
    comp = _create(root, "baseCOMP", "control_bus", -210, 50, (0.18, 0.18, 0.12))
    comp.comment = "Merged numeric controls used by the visual network."

    merge = _create(comp, "mergeCHOP", "merge_controls", -100, 100)
    audio = root.op("audio_analysis/null_audio")
    meta = root.op("spotify_meta/null_meta")
    if audio:
        _connect(merge, audio, 0)
    if meta:
        _connect(merge, meta, 1)
    null_control = _create(comp, "nullCHOP", "null_control", 140, 100)
    _connect(null_control, merge)
    return comp


def _build_visual(root):
    comp = _create(root, "baseCOMP", "fluid_feedback", 150, 120, (0.22, 0.14, 0.18))
    comp.comment = "Fluid-ish feedback TOP chain driven by control_bus/null_control."

    ramp = _create(comp, "rampTOP", "palette_ramp", -500, 260)
    _set_par(ramp, "resolutionw", WIDTH)
    _set_par(ramp, "resolutionh", HEIGHT)

    noise = _create(comp, "noiseTOP", "driver_noise", -500, 60)
    _set_par(noise, "resolutionw", WIDTH)
    _set_par(noise, "resolutionh", HEIGHT)
    _set_par(noise, "period", expr="2.0 - op('../control_bus/null_control')['low'][0] * 1.25")
    _set_par(noise, "offsetx", expr="absTime.seconds * (0.04 + op('../control_bus/null_control')['mid'][0] * 0.12)")
    _set_par(noise, "offsety", expr="absTime.seconds * (0.03 + op('../control_bus/null_control')['high'][0] * 0.10)")
    _set_par(noise, "seed", expr="int(op('../control_bus/null_control')['track_seed'][0])")

    feedback = _create(comp, "feedbackTOP", "feedback", -250, 40)
    transform = _create(comp, "transformTOP", "feedback_motion", 0, 40)
    _connect(transform, feedback)
    _set_par(transform, "scale", expr="1.002 + op('../control_bus/null_control')['low'][0] * 0.035")
    _set_par(transform, "rotate", expr="op('../control_bus/null_control')['mid'][0] * 7")

    composite = _create(comp, "compositeTOP", "blend_noise", 250, 140)
    _connect(composite, transform, 0)
    _connect(composite, noise, 1)
    _set_par(composite, "operand", "add")

    blur = _create(comp, "blurTOP", "soften", 480, 140)
    _connect(blur, composite)
    _set_par(blur, "filter", expr="1 + op('../control_bus/null_control')['energy'][0] * 6")

    level = _create(comp, "levelTOP", "audio_level", 720, 140)
    _connect(level, blur)
    _set_par(level, "brightness1", expr="parent(2).par.Brightness + op('../control_bus/null_control')['kick'][0] * 0.18")
    _set_par(level, "gamma1", expr="1.0 - op('../control_bus/null_control')['high'][0] * 0.15")
    _set_par(level, "opacity", expr="0.92 + op('../control_bus/null_control')['snare'][0] * 0.08")

    out = _create(comp, "nullTOP", "out_visual", 960, 140)
    _connect(out, level)

    _set_par(feedback, "targettop", out.path)
    _make_text(comp, "README", VISUAL_NOTES, -500, -160)
    return comp


def _build_mapper(root):
    mapper = _create(root, "baseCOMP", "mapper", 560, 120, (0.14, 0.16, 0.24))
    mapper.comment = "Single flat projection output. Use Show Grid for setup and Blackout for safety."

    visual_in = _create(mapper, "selectTOP", "visual_in", -560, 160)
    _set_par(visual_in, "top", "../fluid_feedback/out_visual")

    corner = _create(mapper, "cornerpinTOP", "corner_pin", -340, 160)
    _connect(corner, visual_in)

    freeze_feedback = _create(mapper, "feedbackTOP", "freeze_feedback", -340, -40)
    freeze_switch = _create(mapper, "switchTOP", "freeze_switch", -80, 120)
    _connect(freeze_switch, corner, 0)
    _connect(freeze_switch, freeze_feedback, 1)
    _set_par(freeze_switch, "index", expr="1 if parent(2).par.Freeze else 0")
    _set_par(freeze_feedback, "targettop", freeze_switch.path)

    grid = _create(mapper, "checkerTOP", "test_grid", -340, -240)
    _set_par(grid, "resolutionw", WIDTH)
    _set_par(grid, "resolutionh", HEIGHT)

    blackout = _create(mapper, "constantTOP", "blackout", -340, -440)
    _set_par(blackout, "resolutionw", WIDTH)
    _set_par(blackout, "resolutionh", HEIGHT)
    _set_par(blackout, "colorr", 0)
    _set_par(blackout, "colorg", 0)
    _set_par(blackout, "colorb", 0)

    switch = _create(mapper, "switchTOP", "safety_switch", 180, 80)
    _connect(switch, freeze_switch, 0)
    _connect(switch, blackout, 1)
    _connect(switch, grid, 2)
    _set_par(
        switch,
        "index",
        expr="2 if parent(2).par.Showgrid else (1 if parent(2).par.Blackout else 0)",
    )

    out_projector = _create(mapper, "outTOP", "out_projector", 420, 80)
    _connect(out_projector, switch)

    root_out = _create(root, "outTOP", "out1", 900, 120)
    _connect(root_out, out_projector)
    return mapper


def build(parent=None):
    parent = parent or op("/project1")
    _destroy_existing(parent, ROOT_NAME)

    root = _create(parent, "baseCOMP", ROOT_NAME, 0, 0, (0.1, 0.1, 0.1))
    root.comment = "Spotify Fluid Map V1: desktop metadata + BlackHole audio + fluid projection output."
    _append_controls(root)

    _build_spotify_meta(root)
    _build_audio(root)
    _build_audio_analysis(root)
    _build_control_bus(root)
    _build_visual(root)
    _build_mapper(root)
    _make_text(root, "README", ROOT_README, -900, -260)
    return root


ROOT_README = """
Spotify Fluid Map V1

1. Run bridge/spotify_bridge.py from Terminal.
2. Route Spotify audio to BlackHole using a macOS Multi-Output Device.
3. Set Audiodevice to your BlackHole input name.
4. Use Showgrid to align the projector, Blackout for safety, and Brightness/Sensitivity to tune.
"""


VISUAL_NOTES = """
Audio mapping:
- low drives feedback scale/displacement intensity
- mid drives feedback rotation/hue motion
- high drives sharpness/brightness
- kick/snare add flash accents
- track_changed reseeds metadata/control state through the control bus
"""


METADATA_SCRIPT = r'''
def _latest_values(dat):
    values = {}
    if dat is None:
        return values
    for row in dat.rows():
        if len(row) < 2:
            continue
        path = row[0].val
        if not path.startswith('/spotify/'):
            continue
        key = path.split('/')[-1]
        values[key] = row[1].val
    return values


def _float(values, key, default=0.0):
    try:
        return float(values.get(key, default))
    except Exception:
        return default


def onCook(scriptOp):
    scriptOp.clear()
    scriptOp.numSamples = 1
    values = _latest_values(op('osc_in'))
    changed = _float(values, 'track_changed')
    seed = float(scriptOp.fetch('track_seed', 0.0))
    if changed > 0:
        seed += 1.0
        scriptOp.store('track_seed', seed)
    channels = {
        'is_playing': _float(values, 'is_playing'),
        'progress_norm': _float(values, 'progress_norm'),
        'position_sec': _float(values, 'position_sec'),
        'duration_sec': _float(values, 'duration_sec'),
        'track_changed': changed,
        'track_seed': seed,
    }
    for name, value in channels.items():
        chan = scriptOp.appendChan(name)
        chan[0] = value
    return
'''


AUDIO_ANALYSIS_SCRIPT = r'''
import math

try:
    import numpy as np
except Exception:
    np = None


def _samples_from_input(scriptOp):
    if not scriptOp.inputs:
        return []
    source = scriptOp.inputs[0]
    samples = []
    for chan in source.chans():
        try:
            samples.extend([float(v) for v in chan.vals])
        except Exception:
            for i in range(source.numSamples):
                try:
                    samples.append(float(chan[i]))
                except Exception:
                    pass
    return samples[-4096:]


def _rms(samples):
    if not samples:
        return 0.0
    return math.sqrt(sum(v * v for v in samples) / len(samples))


def _band_levels(samples, rate=48000):
    if not samples or np is None:
        rms = _rms(samples)
        return rms, rms * 0.6, rms * 0.35
    window = np.hanning(len(samples))
    spectrum = np.abs(np.fft.rfft(np.array(samples) * window))
    freqs = np.fft.rfftfreq(len(samples), 1.0 / rate)

    def band(lo, hi):
        mask = (freqs >= lo) & (freqs < hi)
        if not mask.any():
            return 0.0
        return float(np.mean(spectrum[mask]))

    low = band(20, 180)
    mid = band(180, 2200)
    high = band(2200, 9000)
    normalizer = max(low, mid, high, 1e-6)
    return low / normalizer, mid / normalizer, high / normalizer


def _pulse(scriptOp, key, value, threshold):
    prev = float(scriptOp.fetch(key, 0.0))
    scriptOp.store(key, value)
    return 1.0 if value >= threshold and prev < threshold else 0.0


def onCook(scriptOp):
    scriptOp.clear()
    scriptOp.numSamples = 1
    samples = _samples_from_input(scriptOp)
    rms = min(_rms(samples) * 8.0, 1.0)
    low, mid, high = _band_levels(samples)
    energy = min((low * 0.45 + mid * 0.35 + high * 0.20) * max(rms, 0.1), 1.0)
    channels = {
        'low': min(low, 1.0),
        'mid': min(mid, 1.0),
        'high': min(high, 1.0),
        'rms': rms,
        'energy': energy,
        'kick': _pulse(scriptOp, 'prev_low', low, 0.62),
        'snare': _pulse(scriptOp, 'prev_high', high, 0.68),
    }
    for name, value in channels.items():
        chan = scriptOp.appendChan(name)
        chan[0] = value
    return
'''


if __name__ == "__main__":
    build()
