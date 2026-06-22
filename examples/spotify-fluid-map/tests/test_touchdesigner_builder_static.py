import re
import unittest
from pathlib import Path


BUILDER_PATH = (
    Path(__file__).resolve().parents[1]
    / "touchdesigner"
    / "spotify_fluid_map_builder.py"
)


class TouchDesignerBuilderStaticTests(unittest.TestCase):
    def test_custom_parameter_expressions_call_eval(self):
        source = BUILDER_PATH.read_text(encoding="utf-8")
        unsafe = []
        for match in re.finditer(r"parent\(\)\.par\.[A-Za-z_][A-Za-z0-9_]*", source):
            tail = source[match.end() : match.end() + 7]
            if not tail.startswith(".eval("):
                unsafe.append(match.group(0))

        self.assertEqual([], unsafe)

    def test_custom_parameter_setup_does_not_set_default_only(self):
        source = BUILDER_PATH.read_text(encoding="utf-8")

        self.assertNotIn("].default =", source)


if __name__ == "__main__":
    unittest.main()
