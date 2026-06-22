#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$EXAMPLE_DIR/../.." && pwd)"
RUNTIME_DIR="$EXAMPLE_DIR/runtime"
LOG_DIR="$EXAMPLE_DIR/logs"
BRIDGE_SCRIPT="$EXAMPLE_DIR/bridge/spotify_bridge.py"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"
LABEL="com.sarveshsea.spotify-fluid-map.bridge"
PLIST_PATH="$RUNTIME_DIR/${LABEL}.plist"
UID_VALUE="$(id -u)"

mkdir -p "$RUNTIME_DIR" "$LOG_DIR"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "python3 was not found. Set PYTHON_BIN=/path/to/python3 and retry." >&2
  exit 1
fi

cat >"$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${PYTHON_BIN}</string>
    <string>-u</string>
    <string>${BRIDGE_SCRIPT}</string>
    <string>--osc-host</string>
    <string>127.0.0.1</string>
    <string>--osc-port</string>
    <string>7000</string>
    <string>--poll-ms</string>
    <string>500</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${REPO_ROOT}</string>
  <key>RunAtLoad</key>
  <true/>
  <key>StandardOutPath</key>
  <string>${LOG_DIR}/spotify_bridge.launchd.out.log</string>
  <key>StandardErrorPath</key>
  <string>${LOG_DIR}/spotify_bridge.launchd.err.log</string>
</dict>
</plist>
PLIST

launchctl bootout "gui/${UID_VALUE}/${LABEL}" 2>/dev/null || true
launchctl bootstrap "gui/${UID_VALUE}" "$PLIST_PATH"
launchctl kickstart -k "gui/${UID_VALUE}/${LABEL}"
sleep 2

echo "Bridge LaunchAgent loaded from:"
echo "  $PLIST_PATH"
launchctl print "gui/${UID_VALUE}/${LABEL}" | grep -E "state =|pid =|runs =" || true
