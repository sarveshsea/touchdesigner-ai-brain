import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "enrich_now_playing_musicbrainz.py"
)


def load_enricher():
    spec = importlib.util.spec_from_file_location("enrich_musicbrainz", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["enrich_musicbrainz"] = module
    spec.loader.exec_module(module)
    return module


class FakeMusicBrainzClient:
    def __init__(self):
        self.calls = 0

    def enrich(self, state):
        self.calls += 1
        return {
            "status": "ok",
            "source": "musicbrainz",
            "track_key": "fake-key",
            "title": state["title"],
            "artist": state["artist"],
            "album": state["album"],
            "recording_mbid": "recording-id",
            "genres": ["electronic"],
            "tags": ["idm"],
            "updated_at": "2026-06-22T12:00:00Z",
        }


class MusicBrainzEnrichmentTests(unittest.TestCase):
    def setUp(self):
        self.enricher = load_enricher()

    def test_summarize_recording_extracts_genres_artists_and_release(self):
        recording = {
            "id": "recording-id",
            "score": 100,
            "title": "Singularity",
            "length": 389000,
            "first-release-date": "2018-05-04",
            "genres": [{"name": "tech house"}],
            "tags": [{"name": "ambient"}, {"name": "ambient"}],
            "artist-credit": [
                {
                    "name": "Jon Hopkins",
                    "artist": {
                        "id": "artist-id",
                        "name": "Jon Hopkins",
                        "genres": [{"name": "electronic"}],
                    },
                }
            ],
            "releases": [
                {
                    "id": "release-id",
                    "title": "Singularity",
                    "date": "2018-05-04",
                    "country": "XW",
                }
            ],
        }

        summary = self.enricher.summarize_recording(recording, "Singularity")

        self.assertEqual(summary["recording_mbid"], "recording-id")
        self.assertEqual(summary["release_mbid"], "release-id")
        self.assertEqual(summary["artists"], ["Jon Hopkins"])
        self.assertEqual(summary["artist_mbids"], ["artist-id"])
        self.assertEqual(summary["genres"], ["tech house"])
        self.assertEqual(summary["tags"], ["ambient"])
        self.assertEqual(summary["artist_genres"], ["electronic"])

    def test_enrich_state_uses_cache_by_track_key(self):
        state = {"title": "Track", "artist": "Artist", "album": "Album"}
        key = self.enricher.track_key(state)
        cache = {
            key: {
                "status": "ok",
                "source": "musicbrainz",
                "track_key": key,
                "title": "Track",
                "artist": "Artist",
            }
        }
        client = FakeMusicBrainzClient()

        result = self.enricher.enrich_state(state, cache, client)

        self.assertEqual(result["status"], "cached")
        self.assertEqual(client.calls, 0)

    def test_empty_state_returns_empty_without_client_call(self):
        client = FakeMusicBrainzClient()

        result = self.enricher.enrich_state({"title": "", "artist": ""}, {}, client)

        self.assertEqual(result["status"], "empty")
        self.assertEqual(client.calls, 0)


if __name__ == "__main__":
    unittest.main()
