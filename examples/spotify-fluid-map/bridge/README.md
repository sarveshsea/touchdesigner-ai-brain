# Spotify Bridge

Stdlib-only bridge from Spotify Desktop to TouchDesigner OSC.

```bash
python3 spotify_bridge.py --osc-host 127.0.0.1 --osc-port 7000 --poll-ms 500
```

Use `--mock` to emit fake playback metadata without Spotify running.

The script sends OSC over UDP and writes `../runtime/now_playing.json`, which is ignored by git.
