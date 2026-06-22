# Spotify Fluid Map V1

A personal/local TouchDesigner prototype that reacts to Spotify Desktop playback.

V1 separates the problem into two streams:

- **Metadata:** the local Spotify desktop app exposes now-playing state through AppleScript.
- **Audio:** Spotify's actual audio is captured into TouchDesigner through a macOS loopback device such as BlackHole.

This avoids Spotify's deprecated Audio Features/Audio Analysis endpoints. The visual engine analyzes the live audio signal inside TouchDesigner.

## What It Builds

Run `touchdesigner/spotify_fluid_map_builder.py` inside TouchDesigner to create a visible VJ-style patch:

- `/project1/spotify_fluid_map/out1`
- `/project1/spotify_fluid_map/mapper/out_projector`
- OSC metadata input on UDP port `7000`
- BlackHole/CoreAudio input
- native TouchDesigner audio analysis channels: `low`, `mid`, `high`, `rms`, `energy`, `kick`, `snare`
- album-art download and Movie File In TOP loading from ignored runtime artwork files
- deterministic title/artist/album hash controls for generative variation
- a 1920x1080 album-cover distortion, spectral-noise, and feedback-memory TOP network
- a single flat projection mapper with grid, blackout, and corner-pin stage

TouchDesigner Non-Commercial clamps output resolution. The builder sets the projection network to 1920x1080, but a Non-Commercial session may cook at 1280-wide until the project runs under a license that permits 1920x1080 output.

## 1. Install BlackHole

Install [BlackHole 2ch](https://github.com/ExistentialAudio/BlackHole), then restart audio apps if macOS asks.

From the repo root:

```bash
examples/spotify-fluid-map/scripts/setup_blackhole_macos.sh
```

The script uses Homebrew's `blackhole-2ch` cask and verifies whether CoreAudio can see the device. macOS will ask for your admin password because BlackHole installs a HAL audio driver under `/Library/Audio/Plug-Ins/HAL`.

Create a Multi-Output Device:

1. Open **Audio MIDI Setup**.
2. Press `+` and choose **Create Multi-Output Device**.
3. Enable your speakers/headphones and **BlackHole 2ch**.
4. Set the Multi-Output Device as the macOS sound output.
5. In TouchDesigner, set Audio Device In to **BlackHole 2ch**.

## 2. Start the Metadata Bridge

From the repo root:

```bash
examples/spotify-fluid-map/scripts/install_bridge_launchagent_macos.sh
```

Or run it in the foreground:

```bash
python3 examples/spotify-fluid-map/bridge/spotify_bridge.py \
  --osc-host 127.0.0.1 \
  --osc-port 7000 \
  --poll-ms 500
```

For testing without Spotify:

```bash
python3 examples/spotify-fluid-map/bridge/spotify_bridge.py --mock
```

The bridge writes ignored runtime state to:

```text
examples/spotify-fluid-map/runtime/now_playing.json
```

It also downloads current album artwork to ignored local files:

```text
examples/spotify-fluid-map/runtime/album_art.jpg
examples/spotify-fluid-map/runtime/artwork/*.jpg
```

Check the live local state:

```bash
examples/spotify-fluid-map/scripts/check_runtime.sh
```

Refresh the TouchDesigner network and report, then check runtime state:

```bash
examples/spotify-fluid-map/scripts/check_runtime.sh --refresh-td
```

## 3. Build the TouchDesigner Network

In TouchDesigner Textport:

```python
exec(open('/absolute/path/to/touchdesigner-ai-brain/examples/spotify-fluid-map/touchdesigner/spotify_fluid_map_builder.py').read())
build()
```

Then:

- Set `Audiodevice` on `/project1/spotify_fluid_map` to your BlackHole input name.
- Toggle `Showgrid` to align the projector.
- Toggle `Blackout` for safety.
- Use `Sensitivity`, `Brightness`, `Visualintensity`, `Coverweight`, `Feedbackdecay`, and `Grain` to tune response.

The builder intentionally leaves the creative patch visible at the top level of `/project1/spotify_fluid_map`:

- metadata lane: OSC DAT, metadata Script CHOP, smoothed metadata controls
- audio lane: BlackHole input, gain, Audio Spectrum CHOP, band slices, RMS, kick/snare triggers, smoothed audio controls
- artwork lane: album cover input, cover tone, zoom/orbit, bloom
- spectral lane: low/mid/high noise families, metadata palette ramp, cover displacement
- feedback lane: memory feedback, orbit/decay, kick/snare flash, final drift
- mapper lane: corner pin, freeze, alignment grid, blackout, final output

## 4. Fetch Community Toolkit Candidates

The repo keeps third-party TouchDesigner assets out of git, but includes a vetted local downloader:

```bash
python3 examples/spotify-fluid-map/scripts/fetch_community_toolkit.py --list
python3 examples/spotify-fluid-map/scripts/fetch_community_toolkit.py
```

Default downloads include a TD 2023 performance tox pack, RayTK 0.37, Embody/Envoy, 13 Tap Bloom, ISF tooling, VIDVOX ISF shaders, a dominant-color reference component, and a sparse subset of MaxMainio's image-processing components.

Downloaded files land in ignored runtime storage:

```text
examples/spotify-fluid-map/runtime/community/
```

See [docs/community-toolkit.md](docs/community-toolkit.md) for the audition order, license notes, and how each tool can feed album-art-driven visuals, shaders, raymarching, bloom, feedback, mapping, and future VJ controls.

Optional song metadata enrichment via MusicBrainz:

```bash
python3 examples/spotify-fluid-map/scripts/enrich_now_playing_musicbrainz.py
```

This writes ignored runtime metadata to:

```text
examples/spotify-fluid-map/runtime/song_enrichment.json
```

MusicBrainz enrichment is cache-first and separate from the live OSC bridge so the visual patch stays responsive.

## OSC Interface

The bridge sends these messages:

- `/spotify/is_playing` int
- `/spotify/progress_norm` float
- `/spotify/position_sec` float
- `/spotify/duration_sec` float
- `/spotify/track_changed` int pulse
- `/spotify/title` string
- `/spotify/artist` string
- `/spotify/album` string
- `/spotify/url` string
- `/spotify/artwork_url` string
- `/spotify/artwork_path` string
- `/spotify/title_hash` float
- `/spotify/artist_hash` float
- `/spotify/album_hash` float

## Manual Acceptance

1. Start Spotify Desktop and play a song.
2. Start the bridge.
3. Route Spotify audio to BlackHole.
4. Run the TD builder.
5. Confirm metadata reaches `/project1/spotify_fluid_map/spotify_osc`.
6. Confirm audio channels in `/project1/spotify_fluid_map/null_audio_analysis` react.
7. Confirm `/project1/spotify_fluid_map/mapper/out_projector` is nonblack and responds to `Showgrid` and `Blackout`.
8. On TouchDesigner licenses that support HD output, confirm the projector chain cooks at 1920x1080. Non-Commercial sessions may clamp to 1280-wide.

## Notes

This is for personal experimentation. For public performance, broadcast, recording, or paid installation work, switch the audio input to a rights-cleared source such as a DJ/audio-interface feed or licensed local files.
