#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

CASK="blackhole-2ch"
PKG_ID="audio.existential.BlackHole2ch"
DRIVER_PATH="/Library/Audio/Plug-Ins/HAL/BlackHole2ch.driver"

has_blackhole_device() {
  system_profiler SPAudioDataType 2>/dev/null | grep -qi "BlackHole"
}

has_blackhole_driver() {
  [[ -d "$DRIVER_PATH" ]] || pkgutil --pkgs 2>/dev/null | grep -qi "^${PKG_ID}$"
}

print_audio_devices() {
  system_profiler SPAudioDataType 2>/dev/null \
    | grep -E "BlackHole|Loopback|MacBook Pro Speakers|MacBook Pro Microphone|Output Source|Input Source" || true
}

echo "Spotify Fluid Map: BlackHole setup"
echo "Example: $EXAMPLE_DIR"
echo

if has_blackhole_device; then
  echo "BlackHole is already visible to CoreAudio."
  print_audio_devices
  exit 0
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required for this setup script." >&2
  exit 1
fi

echo "BlackHole is not visible to CoreAudio yet."
echo "Installing/reinstalling ${CASK}. macOS will ask for your password because HAL audio drivers install under /Library."
echo

if brew list --cask "$CASK" >/dev/null 2>&1 && ! has_blackhole_driver; then
  brew reinstall --cask "$CASK"
else
  brew install --cask "$CASK"
fi

echo
echo "Refreshing CoreAudio. This may ask for the same admin password."
sudo killall coreaudiod 2>/dev/null || true
sleep 4

if has_blackhole_device; then
  echo "BlackHole is visible to CoreAudio."
  print_audio_devices
  echo
  echo "Opening Audio MIDI Setup. Create a Multi-Output Device with your speakers/headphones plus BlackHole 2ch."
  open -b com.apple.audio.AudioMIDISetup || true
  exit 0
fi

echo "BlackHole still is not visible to CoreAudio."
echo "Homebrew's cask notes say a reboot may be required after install."
echo "After reboot, run:"
echo "  $0"
exit 2
