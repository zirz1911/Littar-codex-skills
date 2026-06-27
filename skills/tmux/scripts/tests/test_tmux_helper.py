import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tmux_helper.py"
SPEC = importlib.util.spec_from_file_location("tmux_helper", MODULE_PATH)
tmux_helper = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(tmux_helper)


class TmuxHelperTests(unittest.TestCase):
    def test_parse_list_output_maps_tmux_fields(self):
        raw = "0\t0\t1\t%2\tcodex-aarch64-a\t/dev/ttys004\t/tmp\tTitle"
        panes = tmux_helper.parse_list_output(raw)
        self.assertEqual(
            panes,
            [
                {
                    "session": "0",
                    "window": "0",
                    "active": True,
                    "pane_id": "%2",
                    "command": "codex-aarch64-a",
                    "tty": "/dev/ttys004",
                    "path": "/tmp",
                    "title": "Title",
                }
            ],
        )

    def test_detect_codex_state_finds_typed_but_not_submitted_prompt(self):
        capture = "› $wrap\n\n  gpt-5.4 medium · ~/repo"
        state = tmux_helper.detect_codex_state(capture)
        self.assertEqual(state["mode"], "typed")
        self.assertTrue(state["looks_like_codex"])


if __name__ == "__main__":
    unittest.main()
