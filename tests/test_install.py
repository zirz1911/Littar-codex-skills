import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPO_ROOT / "install.py"


class InstallScriptTest(unittest.TestCase):
    def test_installs_selected_skill_into_all_codex_locations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            home = temp_path / "home"
            target = temp_path / "target"
            home.mkdir()
            target.mkdir()

            env = os.environ.copy()
            env["HOME"] = str(home)

            subprocess.run(
                [
                    "python3",
                    str(INSTALLER),
                    str(target),
                    "--only",
                    "tmux",
                ],
                check=True,
                cwd=REPO_ROOT,
                env=env,
            )

            self.assertTrue((target / ".agents" / "skills" / "tmux" / "SKILL.md").is_file())
            self.assertTrue((target / ".claude" / "skills" / "tmux" / "SKILL.md").is_file())
            self.assertTrue((home / ".codex" / "skills" / "tmux" / "SKILL.md").is_file())

            lock = json.loads((target / "skills-lock.json").read_text(encoding="utf-8"))
            self.assertEqual(lock["skills"]["tmux"]["source"], "Littar-codex-skills")


if __name__ == "__main__":
    unittest.main()
