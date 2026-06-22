#!/usr/bin/env python3
"""Enrich the current Spotify bridge state with MusicBrainz metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


EXAMPLE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NOW_PLAYING = EXAMPLE_ROOT / "runtime" / "now_playing.json"
DEFAULT_OUTPUT = EXAMPLE_ROOT / "runtime" / "song_enrichment.json"
DEFAULT_CACHE = EXAMPLE_ROOT / "runtime" / "enrichment" / "musicbrainz_cache.json"
DEFAULT_USER_AGENT = (
    "touchdesigner-ai-brain/0.1 "
    "(https://github.com/sarveshsea/touchdesigner-ai-brain)"
)
MUSICBRAINZ_ROOT = "https://musicbrainz.org/ws/2"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_text(value: object) -> str:
    return " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())


def stable_key(parts: Iterable[object]) -> str:
    text = "\n".join(normalize_text(part).lower() for part in parts)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def load_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def as_list(value: object) -> list:
    return value if isinstance(value, list) else []


def unique_names(items: Iterable[dict]) -> list[str]:
    seen: set[str] = set()
    names: list[str] = []
    for item in items:
        name = normalize_text(item.get("name", ""))
        key = name.lower()
        if name and key not in seen:
            seen.add(key)
            names.append(name)
    return names


def best_release(recording: dict, album: str) -> dict:
    releases = as_list(recording.get("releases"))
    if not releases:
        return {}
    album_key = normalize_text(album).lower()
    if album_key:
        for release in releases:
            if normalize_text(release.get("title", "")).lower() == album_key:
                return release
    return releases[0]


def artist_names(recording: dict) -> list[str]:
    names: list[str] = []
    for credit in as_list(recording.get("artist-credit")):
        artist = credit.get("artist") or {}
        name = normalize_text(artist.get("name") or credit.get("name"))
        if name:
            names.append(name)
    return names


def artist_ids(recording: dict) -> list[str]:
    ids: list[str] = []
    for credit in as_list(recording.get("artist-credit")):
        artist = credit.get("artist") or {}
        mbid = normalize_text(artist.get("id", ""))
        if mbid:
            ids.append(mbid)
    return ids


def artist_genres(recording: dict) -> list[str]:
    genres: list[dict] = []
    for credit in as_list(recording.get("artist-credit")):
        artist = credit.get("artist") or {}
        genres.extend(as_list(artist.get("genres")))
    return unique_names(genres)


def summarize_recording(recording: dict, album: str) -> dict[str, object]:
    release = best_release(recording, album)
    return {
        "recording_mbid": normalize_text(recording.get("id", "")),
        "recording_title": normalize_text(recording.get("title", "")),
        "score": int(recording.get("score") or 0),
        "length_ms": int(recording.get("length") or 0),
        "first_release_date": normalize_text(recording.get("first-release-date", "")),
        "artists": artist_names(recording),
        "artist_mbids": artist_ids(recording),
        "release_mbid": normalize_text(release.get("id", "")),
        "release_title": normalize_text(release.get("title", "")),
        "release_date": normalize_text(release.get("date", "")),
        "release_country": normalize_text(release.get("country", "")),
        "genres": unique_names(as_list(recording.get("genres"))),
        "tags": unique_names(as_list(recording.get("tags"))),
        "artist_genres": artist_genres(recording),
    }


def fallback_enrichment(state: dict, status: str, message: str = "") -> dict[str, object]:
    return {
        "status": status,
        "message": message,
        "source": "musicbrainz",
        "track_key": track_key(state),
        "title": normalize_text(state.get("title", "")),
        "artist": normalize_text(state.get("artist", "")),
        "album": normalize_text(state.get("album", "")),
        "updated_at": utc_now(),
    }


def is_stoppable_state(state: dict) -> bool:
    return not normalize_text(state.get("title")) or not normalize_text(state.get("artist"))


def track_key(state: dict) -> str:
    return stable_key([state.get("title"), state.get("artist"), state.get("album")])


def build_query(state: dict) -> str:
    title = normalize_text(state.get("title", ""))
    artist = normalize_text(state.get("artist", ""))
    album = normalize_text(state.get("album", ""))
    terms = [f'recording:"{title}"', f'artist:"{artist}"']
    if album:
        terms.append(f'release:"{album}"')
    return " AND ".join(terms)


class MusicBrainzClient:
    def __init__(self, user_agent: str, min_interval: float = 1.1) -> None:
        self.user_agent = user_agent
        self.min_interval = min_interval
        self.last_request = 0.0

    def request_json(self, path: str, params: dict[str, str]) -> dict:
        now = time.monotonic()
        delay = self.min_interval - (now - self.last_request)
        if delay > 0 and math.isfinite(delay):
            time.sleep(delay)
        url = f"{MUSICBRAINZ_ROOT}/{path}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with urllib.request.urlopen(request, timeout=15) as response:
            self.last_request = time.monotonic()
            return json.loads(response.read().decode("utf-8"))

    def enrich(self, state: dict) -> dict[str, object]:
        search = self.request_json(
            "recording",
            {"query": build_query(state), "fmt": "json", "limit": "5"},
        )
        recordings = as_list(search.get("recordings"))
        if not recordings:
            return fallback_enrichment(state, "not-found")

        first = recordings[0]
        mbid = normalize_text(first.get("id", ""))
        lookup = first
        if mbid:
            lookup = self.request_json(
                f"recording/{mbid}",
                {
                    "inc": "artist-credits+releases+tags+genres+url-rels",
                    "fmt": "json",
                },
            )
            lookup["score"] = first.get("score", lookup.get("score", 0))
        summary = summarize_recording(lookup, normalize_text(state.get("album", "")))
        return {
            "status": "ok",
            "source": "musicbrainz",
            "track_key": track_key(state),
            "query": build_query(state),
            "title": normalize_text(state.get("title", "")),
            "artist": normalize_text(state.get("artist", "")),
            "album": normalize_text(state.get("album", "")),
            "updated_at": utc_now(),
            **summary,
        }


def enrich_state(state: dict, cache: dict, client: MusicBrainzClient) -> dict[str, object]:
    key = track_key(state)
    if is_stoppable_state(state):
        return fallback_enrichment(state, "empty")
    cached = cache.get(key)
    if isinstance(cached, dict):
        return {**cached, "status": "cached", "updated_at": utc_now()}
    result = client.enrich(state)
    cache[key] = result
    return result


def enrich_once(
    now_playing_path: Path,
    output_path: Path,
    cache_path: Path,
    client: MusicBrainzClient,
) -> dict[str, object]:
    state = load_json(now_playing_path, {})
    cache = load_json(cache_path, {})
    if not isinstance(state, dict):
        state = {}
    if not isinstance(cache, dict):
        cache = {}
    result = enrich_state(state, cache, client)
    write_json(cache_path, cache)
    write_json(output_path, result)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--now-playing", type=Path, default=DEFAULT_NOW_PLAYING)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--poll-ms", type=int, default=5000)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = MusicBrainzClient(args.user_agent)
    interval = max(1000, args.poll_ms) / 1000.0
    while True:
        result = enrich_once(args.now_playing, args.output, args.cache, client)
        print(f"{result['status']}: {result.get('artist', '')} - {result.get('title', '')}")
        if not args.watch:
            return 0
        time.sleep(interval)


if __name__ == "__main__":
    sys.exit(main())
