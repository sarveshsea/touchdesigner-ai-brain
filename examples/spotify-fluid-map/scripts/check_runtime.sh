#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$EXAMPLE_DIR/../.." && pwd)"
STATE_JSON="$EXAMPLE_DIR/runtime/now_playing.json"
TD_REPORT="$EXAMPLE_DIR/runtime/td_runtime_report.txt"
BRIDGE_LABEL="com.sarveshsea.spotify-fluid-map.bridge"
UID_VALUE="$(id -u)"

if [[ "${1:-}" == "--refresh-td" ]]; then
  "$SCRIPT_DIR/rebuild_touchdesigner_macos.sh" >/dev/null
fi

echo "Spotify Fluid Map runtime check"
echo "Repo: $REPO_ROOT"
echo

echo "Bridge LaunchAgent:"
if launchctl print "gui/${UID_VALUE}/${BRIDGE_LABEL}" >/tmp/spotify-fluid-map-launchctl.txt 2>/dev/null; then
  grep -E "state =|pid =|runs =" /tmp/spotify-fluid-map-launchctl.txt || true
else
  echo "  not loaded"
fi
rm -f /tmp/spotify-fluid-map-launchctl.txt
echo

echo "Spotify runtime JSON:"
if [[ -f "$STATE_JSON" ]]; then
  python3 - "$STATE_JSON" <<'PY'
import json
import sys
from pathlib import Path

state_path = Path(sys.argv[1])
state = json.loads(state_path.read_text(encoding="utf-8"))
for key in ["is_playing", "title", "artist", "album", "progress_norm", "artwork_path", "updated_at"]:
    print(f"  {key}: {state.get(key)}")
artwork = state.get("artwork_path")
if artwork:
    print(f"  artwork_exists: {Path(artwork).exists()}")
PY
else
  echo "  missing: $STATE_JSON"
fi
echo

echo "Audio devices:"
if system_profiler SPAudioDataType 2>/dev/null | grep -qi "BlackHole"; then
  echo "  BlackHole visible: yes"
else
  echo "  BlackHole visible: no"
fi
system_profiler SPAudioDataType 2>/dev/null \
  | grep -E "BlackHole|Loopback|MacBook Pro Speakers|MacBook Pro Microphone|Output Source|Input Source" || true
echo

echo "TouchDesigner report:"
if [[ -f "$TD_REPORT" ]]; then
  if stat -f "%Sm" "$TD_REPORT" >/tmp/spotify-fluid-map-td-report-time.txt 2>/dev/null; then
    echo "  snapshot: $(cat /tmp/spotify-fluid-map-td-report-time.txt)"
    rm -f /tmp/spotify-fluid-map-td-report-time.txt
  fi
  echo "  refresh: examples/spotify-fluid-map/scripts/check_runtime.sh --refresh-td"
  sed -n '1,80p' "$TD_REPORT"
else
  echo "  missing: $TD_REPORT"
  echo "  create it with: examples/spotify-fluid-map/scripts/rebuild_touchdesigner_macos.sh"
fi
