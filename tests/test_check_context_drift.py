"""#1208: `sync.py --check` and the AGENTS.md freshness test must never disagree."""
from __future__ import annotations

import shutil
import subprocess
import sys

from tests.test_context_compact_mode import REPO_ROOT, _render_context
from tests.timeouts import SCRIPT_TIMEOUT


def test_check_and_freshness_test_agree_on_agents_md(tmp_path):
    shutil.copy(REPO_ROOT / "AGENTS.md", tmp_path / "AGENTS.md")
    committed = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    drifted = _render_context(None, tmp_path) != committed

    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "sync.py"), "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=SCRIPT_TIMEOUT,
    )
    reported = any(
        ln.startswith("[UPDATE") and "AGENTS.md" in ln for ln in res.stdout.splitlines()
    )
    assert reported == drifted, (
        f"--check reports AGENTS.md drift={reported} but render differs={drifted}"
    )
