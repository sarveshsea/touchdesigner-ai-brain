import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


EXAMPLE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = EXAMPLE_ROOT / "scripts" / "fetch_community_toolkit.py"
REGISTRY_PATH = EXAMPLE_ROOT / "community" / "community_toolkit.json"


def load_fetcher():
    spec = importlib.util.spec_from_file_location("fetch_community_toolkit", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["fetch_community_toolkit"] = module
    spec.loader.exec_module(module)
    return module


class CommunityToolkitTests(unittest.TestCase):
    def setUp(self):
        self.fetcher = load_fetcher()
        self.registry = self.fetcher.load_json(REGISTRY_PATH)

    def test_registry_ids_are_unique(self):
        ids = [entry["id"] for entry in self.registry["entries"]]

        self.assertEqual(len(ids), len(set(ids)))

    def test_default_selection_excludes_optional_entries(self):
        selected = self.fetcher.select_entries(self.registry["entries"], only=[], include_all=False)
        ids = {entry["id"] for entry in selected}

        self.assertIn("raytk-td2023", ids)
        self.assertIn("td-toxes-performance-pack", ids)
        self.assertNotIn("okvj-shared", ids)
        self.assertNotIn("geopix", ids)

    def test_only_selection_rejects_unknown_ids(self):
        with self.assertRaises(ValueError):
            self.fetcher.select_entries(self.registry["entries"], only=["missing"], include_all=False)

    def test_safe_child_rejects_path_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            with self.assertRaises(ValueError):
                self.fetcher.safe_child(root, "../outside")


if __name__ == "__main__":
    unittest.main()
