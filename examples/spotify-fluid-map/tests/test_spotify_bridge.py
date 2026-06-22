import importlib.util
import json
import socket
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "bridge" / "spotify_bridge.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location("spotify_bridge", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["spotify_bridge"] = module
    spec.loader.exec_module(module)
    return module


class SpotifyBridgeTests(unittest.TestCase):
    def setUp(self):
        self.bridge = load_bridge()

    def test_parse_playing_applescript_payload(self):
        payload = "\n".join(
            [
                "state=playing",
                "title=Singularity",
                "artist=Jon Hopkins",
                "album=Singularity",
                "duration=390",
                "position=42.5",
                "url=https://open.spotify.com/track/example",
                "artwork_url=https://i.scdn.co/image/example",
            ]
        )

        state = self.bridge.TrackState.from_applescript_payload(payload, previous_track_id=None)

        self.assertTrue(state.is_playing)
        self.assertEqual(state.title, "Singularity")
        self.assertEqual(state.artist, "Jon Hopkins")
        self.assertEqual(state.album, "Singularity")
        self.assertEqual(state.duration_sec, 390.0)
        self.assertEqual(state.position_sec, 42.5)
        self.assertAlmostEqual(state.progress_norm, 42.5 / 390.0)
        self.assertEqual(state.track_changed, 1)
        self.assertEqual(state.track_id, "https://open.spotify.com/track/example")

    def test_parse_stopped_payload_uses_safe_defaults(self):
        state = self.bridge.TrackState.from_applescript_payload(
            "state=stopped\nposition=0", previous_track_id="old-track"
        )

        self.assertFalse(state.is_playing)
        self.assertEqual(state.title, "")
        self.assertEqual(state.duration_sec, 0.0)
        self.assertEqual(state.progress_norm, 0.0)
        self.assertEqual(state.track_changed, 1)

    def test_mock_provider_advances_progress_and_track_change(self):
        provider = self.bridge.MockSpotifyProvider(start_time=100.0)

        first = provider.get_state(now=100.0)
        second = provider.get_state(now=101.0)

        self.assertTrue(first.is_playing)
        self.assertEqual(first.track_changed, 1)
        self.assertEqual(second.track_changed, 0)
        self.assertGreater(second.progress_norm, first.progress_norm)

    def test_write_runtime_state_creates_json(self):
        state = self.bridge.TrackState(
            is_playing=True,
            title="Test Title",
            artist="Test Artist",
            album="Test Album",
            duration_sec=120.0,
            position_sec=30.0,
            progress_norm=0.25,
            track_changed=1,
            url="https://open.spotify.com/track/test",
            artwork_url="https://i.scdn.co/image/test",
            track_id="https://open.spotify.com/track/test",
            updated_at="2026-06-22T12:00:00Z",
        )

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "runtime" / "now_playing.json"
            self.bridge.write_runtime_state(state, output)
            data = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(data["title"], "Test Title")
        self.assertEqual(data["artist"], "Test Artist")
        self.assertEqual(data["progress_norm"], 0.25)

    def test_osc_sender_emits_expected_paths(self):
        received = []
        ready = threading.Event()

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("127.0.0.1", 0))
        sock.settimeout(2.0)
        port = sock.getsockname()[1]

        def receive_packets():
            ready.set()
            deadline = time.time() + 2.0
            while time.time() < deadline and len(received) < 10:
                try:
                    data, _addr = sock.recvfrom(2048)
                except socket.timeout:
                    break
                received.append(data)

        thread = threading.Thread(target=receive_packets)
        thread.start()
        ready.wait(1.0)

        sender = self.bridge.OscSender("127.0.0.1", port)
        state = self.bridge.TrackState(
            is_playing=True,
            title="Title",
            artist="Artist",
            album="Album",
            duration_sec=180.0,
            position_sec=45.0,
            progress_norm=0.25,
            track_changed=1,
            url="spotify-url",
            artwork_url="artwork-url",
            track_id="spotify-url",
            updated_at="2026-06-22T12:00:00Z",
        )
        sender.send_state(state)
        sender.close()

        thread.join()
        sock.close()

        decoded = b"\n".join(received)
        self.assertIn(b"/spotify/is_playing", decoded)
        self.assertIn(b"/spotify/title", decoded)
        self.assertIn(b"/spotify/progress_norm", decoded)


if __name__ == "__main__":
    unittest.main()
