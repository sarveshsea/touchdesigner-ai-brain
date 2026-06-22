#!/usr/bin/env python3
"""Spotify Desktop metadata bridge for the TouchDesigner Spotify Fluid Map.

The bridge deliberately avoids Spotify's deprecated audio analysis endpoints.
It reads lightweight now-playing metadata from the local Spotify desktop app,
sends it to TouchDesigner over OSC, and writes a local runtime JSON snapshot.
"""

from __future__ import annotations

import argparse
import json
import math
import socket
import struct
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


DEFAULT_OSC_HOST = "127.0.0.1"
DEFAULT_OSC_PORT = 7000
DEFAULT_POLL_MS = 500
DEFAULT_RUNTIME_PATH = (
    Path(__file__).resolve().parents[1] / "runtime" / "now_playing.json"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def parse_float(value: str, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(result):
        return default
    return result


def normalize_text(value: str) -> str:
    return " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())


def normalize_duration_sec(value: str) -> float:
    duration = max(0.0, parse_float(value))
    if duration > 10000:
        return duration / 1000.0
    return duration


@dataclass(frozen=True)
class TrackState:
    is_playing: bool
    title: str
    artist: str
    album: str
    duration_sec: float
    position_sec: float
    progress_norm: float
    track_changed: int
    url: str
    artwork_url: str
    track_id: str
    updated_at: str

    @classmethod
    def stopped(cls, previous_track_id: str | None = None) -> "TrackState":
        track_changed = 1 if previous_track_id else 0
        return cls(
            is_playing=False,
            title="",
            artist="",
            album="",
            duration_sec=0.0,
            position_sec=0.0,
            progress_norm=0.0,
            track_changed=track_changed,
            url="",
            artwork_url="",
            track_id="",
            updated_at=utc_now(),
        )

    @classmethod
    def from_applescript_payload(
        cls, payload: str, previous_track_id: str | None
    ) -> "TrackState":
        values = parse_key_value_payload(payload)
        state = values.get("state", "stopped").lower()
        if state not in {"playing", "paused"}:
            return cls.stopped(previous_track_id)

        duration_sec = normalize_duration_sec(values.get("duration", "0"))
        position_sec = max(0.0, parse_float(values.get("position", "0")))
        progress_norm = 0.0
        if duration_sec > 0:
            progress_norm = clamp(position_sec / duration_sec, 0.0, 1.0)

        title = normalize_text(values.get("title", ""))
        artist = normalize_text(values.get("artist", ""))
        album = normalize_text(values.get("album", ""))
        url = normalize_text(values.get("url", ""))
        artwork_url = normalize_text(values.get("artwork_url", ""))
        track_id = url or "|".join([title, artist, album])
        track_changed = 1 if track_id != (previous_track_id or "") else 0

        return cls(
            is_playing=state == "playing",
            title=title,
            artist=artist,
            album=album,
            duration_sec=duration_sec,
            position_sec=position_sec,
            progress_norm=progress_norm,
            track_changed=track_changed,
            url=url,
            artwork_url=artwork_url,
            track_id=track_id,
            updated_at=utc_now(),
        )

    def to_runtime_dict(self) -> dict[str, object]:
        return asdict(self)


def parse_key_value_payload(payload: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in payload.splitlines():
        if "=" not in raw_line:
            continue
        key, value = raw_line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


class SpotifyAppleScriptProvider:
    def __init__(self) -> None:
        self.previous_track_id: str | None = None

    def get_state(self, now: float | None = None) -> TrackState:
        del now
        try:
            result = subprocess.run(
                ["osascript", "-e", SPOTIFY_APPLESCRIPT],
                check=False,
                capture_output=True,
                text=True,
                timeout=2.0,
            )
        except (OSError, subprocess.TimeoutExpired):
            state = TrackState.stopped(self.previous_track_id)
        else:
            if result.returncode != 0:
                state = TrackState.stopped(self.previous_track_id)
            else:
                state = TrackState.from_applescript_payload(
                    result.stdout, self.previous_track_id
                )
        self.previous_track_id = state.track_id
        return state


class MockSpotifyProvider:
    def __init__(self, start_time: float | None = None) -> None:
        self.start_time = time.time() if start_time is None else start_time
        self.previous_track_id: str | None = None
        self.duration = 180.0

    def get_state(self, now: float | None = None) -> TrackState:
        current = time.time() if now is None else now
        elapsed = max(0.0, current - self.start_time)
        track_index = int(elapsed // self.duration)
        position = elapsed % self.duration
        title = f"Mock Track {track_index + 1}"
        artist = "TouchDesigner AI Brain"
        album = "Spotify Fluid Map"
        track_id = f"mock:{track_index}"
        state = TrackState(
            is_playing=True,
            title=title,
            artist=artist,
            album=album,
            duration_sec=self.duration,
            position_sec=position,
            progress_norm=clamp(position / self.duration, 0.0, 1.0),
            track_changed=1 if track_id != (self.previous_track_id or "") else 0,
            url=track_id,
            artwork_url="",
            track_id=track_id,
            updated_at=utc_now(),
        )
        self.previous_track_id = state.track_id
        return state


class OscSender:
    def __init__(self, host: str, port: int) -> None:
        self.address = (host, port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_state(self, state: TrackState) -> None:
        messages = [
            ("/spotify/is_playing", int(state.is_playing)),
            ("/spotify/progress_norm", float(state.progress_norm)),
            ("/spotify/position_sec", float(state.position_sec)),
            ("/spotify/duration_sec", float(state.duration_sec)),
            ("/spotify/track_changed", int(state.track_changed)),
            ("/spotify/title", state.title),
            ("/spotify/artist", state.artist),
            ("/spotify/album", state.album),
            ("/spotify/url", state.url),
            ("/spotify/artwork_url", state.artwork_url),
        ]
        for path, value in messages:
            self.socket.sendto(encode_osc_message(path, value), self.address)

    def close(self) -> None:
        self.socket.close()


def pad_osc_string(value: str) -> bytes:
    encoded = value.encode("utf-8") + b"\0"
    padding = (4 - (len(encoded) % 4)) % 4
    return encoded + (b"\0" * padding)


def encode_osc_message(path: str, value: int | float | str) -> bytes:
    if isinstance(value, bool):
        value = int(value)
    if isinstance(value, int):
        type_tag = ",i"
        payload = struct.pack(">i", value)
    elif isinstance(value, float):
        type_tag = ",f"
        payload = struct.pack(">f", value)
    else:
        type_tag = ",s"
        payload = pad_osc_string(str(value))
    return pad_osc_string(path) + pad_osc_string(type_tag) + payload


def write_runtime_state(state: TrackState, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(state.to_runtime_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_bridge(
    provider: SpotifyAppleScriptProvider | MockSpotifyProvider,
    sender: OscSender,
    runtime_path: Path,
    poll_ms: int,
) -> None:
    interval = max(50, poll_ms) / 1000.0
    while True:
        state = provider.get_state()
        sender.send_state(state)
        write_runtime_state(state, runtime_path)
        time.sleep(interval)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--osc-host", default=DEFAULT_OSC_HOST)
    parser.add_argument("--osc-port", type=int, default=DEFAULT_OSC_PORT)
    parser.add_argument("--poll-ms", type=int, default=DEFAULT_POLL_MS)
    parser.add_argument("--runtime-path", type=Path, default=DEFAULT_RUNTIME_PATH)
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Emit simulated playback metadata instead of polling Spotify Desktop.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    provider = MockSpotifyProvider() if args.mock else SpotifyAppleScriptProvider()
    sender = OscSender(args.osc_host, args.osc_port)
    try:
        run_bridge(provider, sender, args.runtime_path, args.poll_ms)
    except KeyboardInterrupt:
        return 0


SPOTIFY_APPLESCRIPT = r'''
tell application "System Events"
    set spotifyRunning to exists (processes where name is "Spotify")
end tell

if spotifyRunning is false then
    return "state=stopped"
end if

tell application "Spotify"
    set playbackState to player state as string
    if playbackState is "stopped" then
        return "state=stopped"
    end if

    set currentTrack to current track
    set outputLines to {}
    set end of outputLines to "state=" & playbackState
    set end of outputLines to "title=" & (name of currentTrack as string)
    set end of outputLines to "artist=" & (artist of currentTrack as string)
    set end of outputLines to "album=" & (album of currentTrack as string)
    set end of outputLines to "duration=" & (duration of currentTrack as string)
    set end of outputLines to "position=" & (player position as string)
    set end of outputLines to "url=" & (spotify url of currentTrack as string)
    try
        set end of outputLines to "artwork_url=" & (artwork url of currentTrack as string)
    on error
        set end of outputLines to "artwork_url="
    end try

    set AppleScript's text item delimiters to linefeed
    set outputText to outputLines as string
    set AppleScript's text item delimiters to ""
    return outputText
end tell
'''


if __name__ == "__main__":
    sys.exit(main())
