#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$EXAMPLE_DIR/../.." && pwd)"
RUNTIME_DIR="$EXAMPLE_DIR/runtime"
BUILDER="$EXAMPLE_DIR/touchdesigner/spotify_fluid_map_builder.py"
STATUS_PATH="$RUNTIME_DIR/td_builder_status.txt"
ERROR_PATH="$RUNTIME_DIR/td_builder_error.txt"
REPORT_PATH="$RUNTIME_DIR/td_runtime_report.txt"

mkdir -p "$RUNTIME_DIR"
rm -f "$STATUS_PATH" "$ERROR_PATH" "$REPORT_PATH"

if ! pgrep -x TouchDesigner >/dev/null 2>&1; then
  open -a TouchDesigner
  sleep 4
fi

python3 - "$BUILDER" "$STATUS_PATH" "$ERROR_PATH" "$REPORT_PATH" <<'PY' | pbcopy
import sys

builder, status_path, error_path, report_path = sys.argv[1:5]
code = f"""
import traceback
script_path = r'{builder}'
status_path = r'{status_path}'
error_path = r'{error_path}'
report_path = r'{report_path}'
try:
    ns = {{'__file__': script_path}}
    exec(compile(open(script_path).read(), script_path, 'exec'), ns)
    root = ns['build']()
    for pane in ui.panes:
        try:
            pane.owner = root
        except Exception:
            pass
    lines = []
    lines.append('root=' + root.path)
    lines.append('top_level_children=' + str(len(root.findChildren(depth=1))))
    for path in [
        '/project1/spotify_fluid_map/out1',
        '/project1/spotify_fluid_map/mapper/out_projector',
        '/project1/spotify_fluid_map/null_projector',
        '/project1/spotify_fluid_map/album_art_in',
        '/project1/spotify_fluid_map/audio_device_in',
        '/project1/spotify_fluid_map/null_audio_analysis',
    ]:
        node = op(path)
        if node is None:
            lines.append(path + '=MISSING')
            continue
        bits = [path, node.OPType]
        try:
            bits.append(str(node.width) + 'x' + str(node.height))
        except Exception:
            pass
        for pname in ['outputresolution', 'resolutionw', 'resolutionh', 'resmult', 'file', 'device']:
            try:
                par = getattr(node.par, pname, None)
                if par is not None:
                    bits.append(pname + '=' + str(par.eval()))
            except Exception:
                pass
        lines.append(' '.join(bits))
    reported_errors = []
    reported_warnings = []
    license_warnings = []
    def _as_messages(values):
        text = str(values or '').strip()
        return [text] if text else []
    for node in root.findChildren(depth=1):
        try:
            errors = _as_messages(node.errors())
        except Exception:
            errors = []
        for message in errors:
            reported_errors.append(node.path + ': ' + message)
        try:
            warnings = _as_messages(node.warnings())
        except Exception:
            warnings = []
        for message in warnings:
            line = node.path + ': ' + message
            if 'Non-Commercial key' in message and 'Resolution limited' in message:
                license_warnings.append(line)
            else:
                reported_warnings.append(line)
        if node.comment and 'Missing par' in node.comment:
            reported_errors.append(node.path + ' comment: ' + node.comment.replace('\\n', ' | '))
    lines.append('operator_errors=' + str(len(reported_errors)))
    lines.extend(reported_errors[:80])
    lines.append('operator_warnings=' + str(len(reported_warnings)))
    lines.extend(reported_warnings[:80])
    lines.append('noncommercial_resolution_warnings=' + str(len(license_warnings)))
    try:
        rows = op('/project1/spotify_fluid_map/spotify_osc').rows()
        lines.append('osc_rows=' + str(len(rows)))
        for row in rows:
            lines.append('OSC ' + ' | '.join([cell.val for cell in row]))
    except Exception as err:
        lines.append('osc_report_error=' + str(err))
    open(report_path, 'w').write('\\n'.join(lines))
    open(status_path, 'w').write(root.path)
except Exception:
    open(error_path, 'w').write(traceback.format_exc())
    raise
"""
print("exec(" + repr(code) + ")")
PY

osascript <<'APPLESCRIPT'
tell application "TouchDesigner" to activate
delay 0.2
tell application "System Events"
  tell process "TouchDesigner"
    click menu item "Textport and DATs" of menu "Dialogs" of menu bar 1
    delay 0.4
    keystroke "v" using command down
    delay 0.2
    key code 36
  end tell
end tell
APPLESCRIPT

for _ in 1 2 3 4 5 6 7 8; do
  if [[ -f "$STATUS_PATH" || -f "$ERROR_PATH" ]]; then
    break
  fi
  sleep 1
done

if [[ -f "$ERROR_PATH" ]]; then
  echo "TouchDesigner builder failed:" >&2
  tail -120 "$ERROR_PATH" >&2
  exit 1
fi

if [[ ! -f "$STATUS_PATH" ]]; then
  echo "TouchDesigner did not write a status file. Check the Textport." >&2
  exit 1
fi

sleep 2
python3 - "$REPORT_PATH" <<'PY' | pbcopy
import sys

report_path = sys.argv[1]
code = f"""
report_path = r'{report_path}'
root = op('/project1/spotify_fluid_map')
def _messages(values):
    text = str(values or '').strip()
    return [text] if text else []
lines = []
if not root:
    lines.append('root=MISSING')
else:
    lines.append('root=' + root.path)
    lines.append('top_level_children=' + str(len(root.findChildren(depth=1))))
    for path in [
        '/project1/spotify_fluid_map/out1',
        '/project1/spotify_fluid_map/mapper/out_projector',
        '/project1/spotify_fluid_map/null_projector',
        '/project1/spotify_fluid_map/album_art_in',
        '/project1/spotify_fluid_map/audio_device_in',
        '/project1/spotify_fluid_map/null_audio_analysis',
    ]:
        node = op(path)
        if node is None:
            lines.append(path + '=MISSING')
            continue
        bits = [path, node.OPType]
        try:
            bits.append(str(node.width) + 'x' + str(node.height))
        except Exception:
            pass
        for pname in ['outputresolution', 'resolutionw', 'resolutionh', 'resmult', 'file', 'device']:
            try:
                par = getattr(node.par, pname, None)
                if par is not None:
                    bits.append(pname + '=' + str(par.eval()))
            except Exception:
                pass
        lines.append(' '.join(bits))
    errors = []
    warnings = []
    license_warnings = []
    for node in root.findChildren(depth=1):
        for message in _messages(node.errors()):
            errors.append(node.path + ': ' + message)
        for message in _messages(node.warnings()):
            line = node.path + ': ' + message
            if 'Non-Commercial key' in message and 'Resolution limited' in message:
                license_warnings.append(line)
            else:
                warnings.append(line)
    lines.append('operator_errors=' + str(len(errors)))
    lines.extend(errors[:80])
    lines.append('operator_warnings=' + str(len(warnings)))
    lines.extend(warnings[:80])
    lines.append('noncommercial_resolution_warnings=' + str(len(license_warnings)))
    try:
        rows = op('/project1/spotify_fluid_map/spotify_osc').rows()
        lines.append('osc_rows=' + str(len(rows)))
        for row in rows:
            lines.append('OSC ' + ' | '.join([cell.val for cell in row]))
    except Exception as err:
        lines.append('osc_report_error=' + str(err))
open(report_path, 'w').write('\\n'.join(lines))
"""
print("exec(" + repr(code) + ")")
PY

osascript <<'APPLESCRIPT'
tell application "TouchDesigner" to activate
delay 0.2
tell application "System Events"
  tell process "TouchDesigner"
    click menu item "Textport and DATs" of menu "Dialogs" of menu bar 1
    delay 0.4
    keystroke "v" using command down
    delay 0.2
    key code 36
  end tell
end tell
APPLESCRIPT
sleep 2

echo "TouchDesigner network rebuilt: $(cat "$STATUS_PATH")"
echo "Runtime report: $REPORT_PATH"
sed -n '1,120p' "$REPORT_PATH"
