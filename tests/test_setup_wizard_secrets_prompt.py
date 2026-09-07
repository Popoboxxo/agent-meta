"""Setup wizard must offer (not silently default) typical secret-pattern
.gitignore entries (issue #682 §4.3)."""

import sys
from pathlib import Path
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.setup import run_setup_wizard  # noqa: E402

_EXPECTED_SECRET_PATTERNS = [".env*", "*.pem", "*.key", "credentials*.json", "secret*.y*ml"]


def _run_wizard(tmp_path, answers):
    """Run the wizard with a scripted sequence of `input()` answers."""
    with patch("lib.setup._QUESTIONARY_AVAILABLE", False), \
         patch("sys.stdin.isatty", return_value=True), \
         patch("builtins.input", side_effect=answers):
        return run_setup_wizard(
            agent_meta_root=_REPO_ROOT,
            project_root=tmp_path,
            target_config=tmp_path / "project.yaml",
            dry_run=True,
        )

def test_accepting_recommended_default_adds_secret_patterns(tmp_path):
    # name, prefix, short, providers(list->empty=default), git platform,
    # remote, branch, secrets-question(yes/default), optional-config(no)
    answers = ["my-proj", "mp", "", "", "", "", "", "", "no"]
    config = _run_wizard(tmp_path, answers)
    assert config.get("gitignore", {}).get("custom_entries") == _EXPECTED_SECRET_PATTERNS


def test_declining_leaves_gitignore_block_absent(tmp_path):
    answers = ["my-proj", "mp", "", "", "", "", "", "no", "no"]
    config = _run_wizard(tmp_path, answers)
    assert "gitignore" not in config
