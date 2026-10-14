"""IC-18 no. 15 / AC-45 / AC-84: Continue prompts only for ActiveSet.roles.

``sync_prompts_for_continue`` previously filtered by the raw ``roles``
allowlist only (no activation gates), so a gate-dropped role still got a
slash-command prompt.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE = _REPO_ROOT / "tests" / "fixtures" / "active-set" / "p20" / ".meta-config" / "project.yaml"


def _sync_p20_continue(tmp_path: Path) -> Path:
    (tmp_path / ".meta-config").mkdir()
    text = _FIXTURE.read_text(encoding="utf-8").replace("- Claude", "- Continue")
    (tmp_path / ".meta-config" / "project.yaml").write_text(
        text
        + "project:\n  name: t\n  prefix: t\n"
        "provider-options:\n  Continue:\n    generate-prompts: true\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py")],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    return tmp_path / ".continue" / "prompts"


def test_p20_gate_dropped_role_gets_no_prompt(tmp_path):
    # developer_tiers gate drops senior-developer (no junior-developer in p20).
    prompts = _sync_p20_continue(tmp_path)
    assert (prompts / "developer.md").is_file()
    assert not (prompts / "senior-developer.md").exists()


def test_no_allowlist_still_applies_gates(tmp_path):
    # Without `roles:` the raw allowlist was None => every override got a
    # prompt, including roles of disabled groups (knowledge-*, se-*).
    (tmp_path / ".meta-config").mkdir()
    (tmp_path / ".meta-config" / "project.yaml").write_text(
        "ai-providers: [Continue]\nproject:\n  name: t\n  prefix: t\n"
        "provider-options:\n  Continue:\n    generate-prompts: true\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py")],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    names = {p.name for p in (tmp_path / ".continue" / "prompts").glob("*.md")}
    assert "developer.md" in names
    assert not {n for n in names if n.startswith(("knowledge-", "se-"))}
