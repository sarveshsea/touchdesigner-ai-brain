"""
Build the Spotify Fluid Map V1 network in TouchDesigner.

Run this inside TouchDesigner's Python environment:

    exec(open('/absolute/path/to/spotify_fluid_map_builder.py').read())
    build()

The resulting public contract is:
    /project1/spotify_fluid_map/out1
    /project1/spotify_fluid_map/mapper/out_projector
"""

from pathlib import Path


ROOT_NAME = "spotify_fluid_map"
OSC_PORT = 7000
WIDTH = 1920
HEIGHT = 1080


def _infer_example_dir():
    script_file = globals().get("__file__")
    if script_file:
        return Path(script_file).resolve().parents[1]
    return Path.cwd() / "examples" / "spotify-fluid-map"


EXAMPLE_DIR = _infer_example_dir()
DEFAULT_ARTWORK_PATH = EXAMPLE_DIR / "runtime" / "album_art.jpg"


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
    if str(op_type).endswith("TOP"):
        for par_name, value in (
            ("outputresolution", "custom"),
            ("resolutionw", WIDTH),
            ("resolutionh", HEIGHT),
            ("resmult", False),
        ):
            par = getattr(node.par, par_name, None)
            if par is not None:
                par.val = value
    return node


def _make_label(parent, name, text, x, y):
    dat = _create(parent, "textDAT", name, x, y)
    dat.text = text
    dat.viewer = True
    dat.nodeWidth = 220
    dat.nodeHeight = 80
    return dat


def _set_par(node, name, value=None, expr=None):
    par = getattr(node.par, name, None)
    if par is None:
        node.comment = (node.comment + "\n" if node.comment else "") + "Missing par: " + name
        return
    if expr is not None:
        par.expr = expr
    else:
        par.val = value


def _set_top_resolution(node, width=WIDTH, height=HEIGHT):
    _set_par(node, "outputresolution", "custom")
    _set_par(node, "resolutionw", width)
    _set_par(node, "resolutionh", height)
    _set_par(node, "resmult", False)


def _connect(dst, src, index=0):
    try:
        dst.setInput(index, src)
    except Exception:
        try:
            dst.inputConnectors[index].connect(src)
        except Exception as err:
            dst.comment = (dst.comment + "\n" if dst.comment else "") + "Connect failed: " + str(err)


def _append_controls(root):
    page = root.appendCustomPage("Performance")
    page.appendToggle("Blackout", label="Blackout")[0].default = False
    page.appendToggle("Freeze", label="Freeze")[0].default = False
    page.appendToggle("Showgrid", label="Show Grid")[0].default = False
    page.appendPulse("Resetfeedback", label="Reset Feedback")
    page.appendStr("Audiodevice", label="Audio Device")[0].default = "BlackHole 2ch"
    page.appendFloat("Sensitivity", label="Sensitivity")[0].default = 1.0
    page.appendFloat("Brightness", label="Brightness")[0].default = 1.0
    page.appendFloat("Visualintensity", label="Visual Intensity")[0].default = 1.0
    page.appendFloat("Coverweight", label="Cover Weight")[0].default = 0.72
    page.appendFloat("Feedbackdecay", label="Feedback Decay")[0].default = 0.94
    page.appendFloat("Grain", label="Grain")[0].default = 0.28


def _osc_string_expr(path, fallback):
    safe_fallback = str(fallback).replace("\\", "\\\\").replace("'", "\\'")
    safe_path = path.replace("'", "\\'")
    return (
        "next((r[1].val for r in op('spotify_osc').rows() "
        f"if len(r) > 1 and r[0].val == '{safe_path}'), "
        f"r'{safe_fallback}') or r'{safe_fallback}'"
    )


def _build_metadata_lane(root):
    _make_label(
        root,
        "label_01_metadata",
        "01 SPOTIFY METADATA\nOSC on :7000 -> numeric controls + artwork path",
        -1100,
        500,
    )
    osc = _create(root, "oscinDAT", "spotify_osc", -820, 520, (0.18, 0.15, 0.22))
    _set_par(osc, "port", OSC_PORT)
    _set_par(osc, "active", True)

    script = _create(root, "textDAT", "metadata_to_controls_script", -560, 520)
    script.text = METADATA_SCRIPT
    meta = _create(root, "scriptCHOP", "spotify_meta_chop", -300, 520, (0.18, 0.15, 0.22))
    _set_par(meta, "callbacks", script.path)
    _set_par(meta, "timeslice", False)

    smooth = _create(root, "filterCHOP", "metadata_smooth", -80, 520, (0.18, 0.15, 0.22))
    _connect(smooth, meta)
    _set_par(smooth, "width", 0.08)

    null_meta = _create(root, "nullCHOP", "null_spotify_meta", 150, 520, (0.18, 0.15, 0.22))
    _connect(null_meta, smooth)
    return null_meta


def _build_audio_lane(root):
    _make_label(
        root,
        "label_02_audio",
        "02 BLACKHOLE AUDIO\nAudio Device In -> FFT bands, pulses, smoothed energy",
        -1100,
        260,
    )
    audio = _create(root, "audiodeviceinCHOP", "audio_device_in", -820, 280, (0.12, 0.18, 0.22))
    _set_par(audio, "driver", "default")
    _set_par(audio, "device", expr="parent().par.Audiodevice")
    _set_par(audio, "active", True)

    gain = _create(root, "mathCHOP", "audio_gain", -600, 280, (0.12, 0.18, 0.22))
    _connect(gain, audio)
    _set_par(gain, "gain", expr="parent().par.Sensitivity")

    script = _create(root, "textDAT", "audio_analysis_script", -600, 100)
    script.text = AUDIO_ANALYSIS_SCRIPT

    analysis = _create(root, "scriptCHOP", "audio_analysis_chop", -360, 280, (0.12, 0.22, 0.16))
    _connect(analysis, gain)
    _set_par(analysis, "callbacks", script.path)
    _set_par(analysis, "timeslice", False)

    smooth = _create(root, "filterCHOP", "audio_smooth", -120, 280, (0.12, 0.22, 0.16))
    _connect(smooth, analysis)
    _set_par(smooth, "width", 0.12)

    null_audio = _create(root, "nullCHOP", "null_audio_analysis", 140, 280, (0.12, 0.22, 0.16))
    _connect(null_audio, smooth)
    return null_audio


def _build_control_bus(root, null_meta, null_audio):
    _make_label(
        root,
        "label_03_control",
        "03 CONTROL BUS\nmetadata hashes + progress + audio bands",
        370,
        390,
    )
    merge = _create(root, "mergeCHOP", "merge_control_signals", 400, 280, (0.18, 0.18, 0.12))
    _connect(merge, null_audio, 0)
    _connect(merge, null_meta, 1)

    null_control = _create(root, "nullCHOP", "null_control", 650, 280, (0.18, 0.18, 0.12))
    _connect(null_control, merge)
    return null_control


def _build_artwork_lane(root):
    _make_label(
        root,
        "label_04_artwork",
        "04 ALBUM ART ENGINE\ncover file -> zoom, smear, warp, color memory",
        -1100,
        20,
    )
    art = _create(root, "moviefileinTOP", "album_art_in", -820, 40, (0.20, 0.16, 0.12))
    _set_top_resolution(art)
    _set_par(art, "file", expr=_osc_string_expr("/spotify/artwork_path", DEFAULT_ARTWORK_PATH))
    _set_par(art, "play", True)

    art_level = _create(root, "levelTOP", "album_art_tone", -580, 40, (0.20, 0.16, 0.12))
    _connect(art_level, art)
    _set_par(art_level, "brightness1", expr="0.75 + op('null_control')['energy'][0] * 0.35")
    _set_par(art_level, "contrast", expr="1.05 + op('null_control')['mid'][0] * 0.45")
    _set_par(art_level, "opacity", expr="parent().par.Coverweight")

    art_zoom = _create(root, "transformTOP", "album_art_zoom_orbit", -340, 40, (0.20, 0.16, 0.12))
    _connect(art_zoom, art_level)
    _set_par(art_zoom, "sx", expr="1.0 + op('null_control')['low'][0] * 0.22")
    _set_par(art_zoom, "sy", expr="1.0 + op('null_control')['low'][0] * 0.22")
    _set_par(
        art_zoom,
        "rotate",
        expr="(op('null_control')['artist_hash'][0] - 0.5) * 18 + op('null_control')['progress_norm'][0] * 12",
    )
    _set_par(art_zoom, "tx", expr="(op('null_control')['title_hash'][0] - 0.5) * 0.12")
    _set_par(art_zoom, "ty", expr="(op('null_control')['album_hash'][0] - 0.5) * 0.12")

    art_soft = _create(root, "blurTOP", "album_art_soft_bloom", -100, 40, (0.20, 0.16, 0.12))
    _connect(art_soft, art_zoom)
    _set_par(art_soft, "size", expr="1.0 + op('null_control')['rms'][0] * 10")

    null_art = _create(root, "nullTOP", "null_album_art_engine", 140, 40, (0.20, 0.16, 0.12))
    _connect(null_art, art_soft)
    return null_art


def _build_spectral_texture_lane(root):
    _make_label(
        root,
        "label_05_spectral",
        "05 SPECTRAL TEXTURE\nlow/mid/high drive noise families and palette movement",
        -1100,
        -220,
    )
    low_noise = _create(root, "noiseTOP", "low_flow_noise", -820, -160, (0.12, 0.20, 0.18))
    _set_top_resolution(low_noise)
    _set_par(low_noise, "period", expr="1.8 - op('null_control')['low'][0] * 1.1")
    _set_par(low_noise, "tx", expr="absTime.seconds * (0.04 + op('null_control')['low'][0] * 0.18)")
    _set_par(low_noise, "ty", expr="op('null_control')['progress_norm'][0] * 2.0")
    _set_par(low_noise, "seed", expr="int(op('null_control')['track_seed'][0] * 11 + op('null_control')['artist_hash'][0] * 900)")

    mid_noise = _create(root, "noiseTOP", "mid_thread_noise", -820, -360, (0.12, 0.20, 0.18))
    _set_top_resolution(mid_noise)
    _set_par(mid_noise, "period", expr="0.9 + op('null_control')['mid'][0] * 0.65")
    _set_par(mid_noise, "tx", expr="absTime.seconds * (0.12 + op('null_control')['mid'][0] * 0.22)")
    _set_par(mid_noise, "ty", expr="absTime.seconds * -0.08")
    _set_par(mid_noise, "seed", expr="int(op('null_control')['track_seed'][0] * 17 + op('null_control')['title_hash'][0] * 1200)")

    high_noise = _create(root, "noiseTOP", "high_grain_noise", -820, -560, (0.12, 0.20, 0.18))
    _set_top_resolution(high_noise)
    _set_par(high_noise, "period", expr="0.28 + parent().par.Grain")
    _set_par(high_noise, "tx", expr="absTime.seconds * (0.28 + op('null_control')['high'][0] * 0.8)")
    _set_par(high_noise, "seed", expr="int(op('null_control')['track_seed'][0] * 23 + op('null_control')['album_hash'][0] * 1600)")

    palette = _create(root, "rampTOP", "metadata_palette_ramp", -560, -560, (0.16, 0.12, 0.20))
    _set_top_resolution(palette)
    _set_par(palette, "phase", expr="op('null_control')['progress_norm'][0] + op('null_control')['artist_hash'][0]")

    low_warp = _create(root, "displaceTOP", "cover_low_displace", -560, -120, (0.12, 0.20, 0.18))
    _connect(low_warp, root.op("null_album_art_engine"), 0)
    _connect(low_warp, low_noise, 1)
    _set_par(low_warp, "displaceweightx", expr="0.04 + op('null_control')['low'][0] * 0.42")
    _set_par(low_warp, "displaceweighty", expr="0.04 + op('null_control')['low'][0] * 0.42")

    mid_warp = _create(root, "displaceTOP", "cover_mid_shear", -320, -180, (0.12, 0.20, 0.18))
    _connect(mid_warp, low_warp, 0)
    _connect(mid_warp, mid_noise, 1)
    _set_par(mid_warp, "displaceweightx", expr="0.025 + op('null_control')['mid'][0] * 0.25")
    _set_par(mid_warp, "displaceweighty", expr="0.025 + op('null_control')['mid'][0] * 0.25")

    grain_blend = _create(root, "compositeTOP", "grain_over_cover", -80, -260, (0.12, 0.20, 0.18))
    _connect(grain_blend, mid_warp, 0)
    _connect(grain_blend, high_noise, 1)
    _set_par(grain_blend, "operand", "add")

    palette_blend = _create(root, "compositeTOP", "palette_over_cover", 160, -260, (0.16, 0.12, 0.20))
    _connect(palette_blend, grain_blend, 0)
    _connect(palette_blend, palette, 1)
    _set_par(palette_blend, "operand", "screen")

    null_texture = _create(root, "nullTOP", "null_spectral_texture", 420, -260, (0.16, 0.12, 0.20))
    _connect(null_texture, palette_blend)
    return null_texture


def _build_feedback_lane(root, texture):
    _make_label(
        root,
        "label_06_feedback",
        "06 FLUID MEMORY\nfeedback, orbit, bloom, kick/snare flashes",
        -1100,
        -760,
    )
    memory = _create(root, "feedbackTOP", "feedback_memory", -820, -760, (0.22, 0.14, 0.18))

    memory_motion = _create(root, "transformTOP", "feedback_orbit", -580, -760, (0.22, 0.14, 0.18))
    _connect(memory_motion, memory)
    _set_par(memory_motion, "sx", expr="1.003 + op('null_control')['low'][0] * 0.045")
    _set_par(memory_motion, "sy", expr="1.003 + op('null_control')['low'][0] * 0.045")
    _set_par(memory_motion, "rotate", expr="(op('null_control')['mid'][0] - 0.5) * 8")
    _set_par(memory_motion, "tx", expr="(op('null_control')['artist_hash'][0] - 0.5) * 0.018")
    _set_par(memory_motion, "ty", expr="(op('null_control')['title_hash'][0] - 0.5) * 0.018")

    memory_decay = _create(root, "levelTOP", "feedback_decay", -340, -760, (0.22, 0.14, 0.18))
    _connect(memory_decay, memory_motion)
    _set_par(memory_decay, "opacity", expr="parent().par.Feedbackdecay")
    _set_par(memory_decay, "brightness1", expr="0.98 + op('null_control')['kick'][0] * 0.1")

    composite = _create(root, "compositeTOP", "cover_into_memory", -100, -620, (0.22, 0.14, 0.18))
    _connect(composite, memory_decay, 0)
    _connect(composite, texture, 1)
    _set_par(composite, "operand", "add")

    bloom = _create(root, "blurTOP", "energy_bloom", 140, -620, (0.22, 0.14, 0.18))
    _connect(bloom, composite)
    _set_par(bloom, "size", expr="1.0 + op('null_control')['energy'][0] * 12")

    flash = _create(root, "levelTOP", "kick_snare_flash", 380, -620, (0.22, 0.14, 0.18))
    _connect(flash, bloom)
    _set_par(flash, "brightness1", expr="parent().par.Brightness + op('null_control')['kick'][0] * 0.4")
    _set_par(flash, "contrast", expr="1.0 + op('null_control')['snare'][0] * 0.55")
    _set_par(flash, "opacity", expr="0.9 + parent().par.Visualintensity * 0.1")

    final_motion = _create(root, "transformTOP", "final_micro_drift", 620, -620, (0.22, 0.14, 0.18))
    _connect(final_motion, flash)
    _set_par(final_motion, "sx", expr="1.0 + op('null_control')['rms'][0] * 0.018")
    _set_par(final_motion, "sy", expr="1.0 + op('null_control')['rms'][0] * 0.018")
    _set_par(final_motion, "rotate", expr="op('null_control')['progress_norm'][0] * 3")

    null_visual = _create(root, "nullTOP", "null_visual", 860, -620, (0.22, 0.14, 0.18))
    _connect(null_visual, final_motion)
    _set_par(memory, "top", null_visual.path)
    return null_visual


def _build_visible_mapper_lane(root, visual):
    _make_label(
        root,
        "label_07_mapper",
        "07 PROJECTOR SAFETY\ncorner pin, freeze, grid, blackout, final output",
        -1100,
        -1020,
    )
    corner = _create(root, "cornerpinTOP", "corner_pin_projector", -820, -1040, (0.14, 0.16, 0.24))
    _connect(corner, visual)

    freeze_feedback = _create(root, "feedbackTOP", "freeze_buffer", -580, -1220, (0.14, 0.16, 0.24))
    freeze_switch = _create(root, "switchTOP", "freeze_switch", -580, -1040, (0.14, 0.16, 0.24))
    _connect(freeze_switch, corner, 0)
    _connect(freeze_switch, freeze_feedback, 1)
    _set_par(freeze_switch, "index", expr="1 if parent().par.Freeze else 0")
    _set_par(freeze_feedback, "top", freeze_switch.path)

    grid_cell = _create(root, "rectangleTOP", "mapper_grid_cell", -820, -1440, (0.14, 0.16, 0.24))
    _set_top_resolution(grid_cell, 160, 90)
    _set_par(grid_cell, "sizeunit", "fraction")
    _set_par(grid_cell, "sizex", 1.0)
    _set_par(grid_cell, "sizey", 1.0)
    _set_par(grid_cell, "fillalpha", 0.0)
    _set_par(grid_cell, "borderwidth", 2.0)
    _set_par(grid_cell, "borderr", 0.0)
    _set_par(grid_cell, "borderg", 0.9)
    _set_par(grid_cell, "borderb", 1.0)
    _set_par(grid_cell, "bgcolorr", 0.02)
    _set_par(grid_cell, "bgcolorg", 0.02)
    _set_par(grid_cell, "bgcolorb", 0.02)

    grid = _create(root, "tileTOP", "mapper_alignment_grid", -580, -1440, (0.14, 0.16, 0.24))
    _connect(grid, grid_cell)
    _set_top_resolution(grid)
    _set_par(grid, "repeatx", 12)
    _set_par(grid, "repeaty", 12)

    blackout = _create(root, "constantTOP", "blackout_black", -580, -1640, (0.14, 0.16, 0.24))
    _set_top_resolution(blackout)
    _set_par(blackout, "colorr", 0)
    _set_par(blackout, "colorg", 0)
    _set_par(blackout, "colorb", 0)

    safety = _create(root, "switchTOP", "safety_switch", -320, -1040, (0.14, 0.16, 0.24))
    _connect(safety, freeze_switch, 0)
    _connect(safety, blackout, 1)
    _connect(safety, grid, 2)
    _set_par(safety, "index", expr="2 if parent().par.Showgrid else (1 if parent().par.Blackout else 0)")

    projector = _create(root, "nullTOP", "null_projector", -80, -1040, (0.14, 0.16, 0.24))
    _connect(projector, safety)

    root_out = _create(root, "outTOP", "out1", 160, -1040, (0.14, 0.16, 0.24))
    _connect(root_out, projector)

    mapper = _create(root, "baseCOMP", "mapper", 160, -1240, (0.14, 0.16, 0.24))
    mapper.comment = "Compatibility contract: /project1/spotify_fluid_map/mapper/out_projector selects the visible top-level projector output."
    select = _create(mapper, "selectTOP", "projector_in", -200, 100)
    _set_par(select, "top", "../null_projector")
    out_projector = _create(mapper, "outTOP", "out_projector", 40, 100)
    _connect(out_projector, select)
    return projector


def build(parent=None):
    parent = parent or op("/project1")
    _destroy_existing(parent, ROOT_NAME)

    root = _create(parent, "baseCOMP", ROOT_NAME, 0, 0, (0.08, 0.08, 0.08))
    root.comment = "Spotify Fluid Map V1: visible album-art VJ patch driven by Spotify metadata, BlackHole audio, and projection safety controls."
    _append_controls(root)

    _make_label(root, "README", ROOT_README, -1100, 760)
    null_meta = _build_metadata_lane(root)
    null_audio = _build_audio_lane(root)
    _build_control_bus(root, null_meta, null_audio)
    null_art = _build_artwork_lane(root)
    texture = _build_spectral_texture_lane(root)
    visual = _build_feedback_lane(root, texture)
    _build_visible_mapper_lane(root, visual)

    root.viewer = True
    return root


ROOT_README = """
Spotify Fluid Map V1.1

This is intentionally visible: OSC, audio analysis, album-art texture, spectral noise,
feedback memory, and projector safety live as readable top-level lanes.

Bridge output:
- runtime/now_playing.json
- runtime/artwork/*.jpg
- OSC /spotify/* metadata and deterministic title/artist/album hashes
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
        values[path.split('/')[-1]] = row[1].val
    return values


def _float(values, key, default=0.0):
    try:
        return float(values.get(key, default))
    except Exception:
        return default


def onCook(scriptOp):
    try:
        scriptOp.isTimeSlice = False
    except Exception:
        pass
    scriptOp.clear()
    scriptOp.numSamples = 1
    values = _latest_values(op('spotify_osc'))
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
        'title_hash': _float(values, 'title_hash'),
        'artist_hash': _float(values, 'artist_hash'),
        'album_hash': _float(values, 'album_hash'),
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
    try:
        scriptOp.isTimeSlice = False
    except Exception:
        pass
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
