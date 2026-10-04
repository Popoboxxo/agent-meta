"""F05 regression (issue #803): ``--dry-run`` must not touch the working tree.

The audit found that a dry run created ``.gitmodules`` and populated
``external/awesome-claude-code`` (56 of 57 reported files) and even moved a
skill repo's HEAD via ``git checkout``. Root cause: ``ensure_skill_repo()`` —
the only helper that runs ``git submodule add`` / ``git clone`` /
``git checkout`` against a skill repo — had no ``dry_run`` parameter, so its
safety depended entirely on a caller-side ``if not dry_run:``. The
awesome-claude-code deinit call additionally escaped even that call-site gate.

Covered here:

* ``test_ensure_skill_repo_dry_run_no_git_call`` -- the mutating helper itself
  refuses to run in dry-run (defense in depth, mirroring ``write_checked``).
  Fails before the fix: without the parameter/early-return, a missing target
  repo triggers ``git clone`` / ``git submodule add``.
* ``test_sync_external_skills_dry_run_never_deinits_awesome_claude_code`` --
  the awesome-claude-code deinit call site is gated in dry-run (F04 invariant
  applied consistently, not just to the inactive-repos loop).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib import skills as skills_mod  # noqa: E402
from lib.log import SyncLog  # noqa: E402


_SKILL_REGISTRY = """\
repos:
  awesome-claude-code:
    repo: https://example.invalid/awesome.git
    local_path: external/awesome-claude-code
    pinned_commit: deadbeefdeadbeefdeadbeefdeadbeefdeadbeef
    enabled: true
  demo-repo:
    repo: https://example.invalid/demo.git
    local_path: external/demo-repo
skills:
  demo-skill:
    approved: true
    repo: demo-repo
    source: skills/demo
    entry: SKILL.md
    role: demo-role
"""


def _write_registry(agent_meta_root: Path) -> None:
    (agent_meta_root / "config").mkdir(parents=True, exist_ok=True)
    (agent_meta_root / "config" / "skills-registry.yaml").write_text(
        _SKILL_REGISTRY, encoding="utf-8"
    )


def test_ensure_skill_repo_dry_run_no_git_call(tmp_path, monkeypatch):
    """``ensure_skill_repo(dry_run=True)`` is a no-op: no subprocess, no target dir.

    Before the fix this helper had no ``dry_run`` parameter, so calling it (as
    the dispatch site does when the caller's gate is missing) attempted a real
    ``git clone`` into ``external/<repo>`` and created the working-tree state
    reported by F05.
    """
    agent_meta_root = tmp_path / "agent-meta"
    (agent_meta_root / "config").mkdir(parents=True)
    project_root = tmp_path / "project"
    project_root.mkdir()

    calls: list = []
    monkeypatch.setattr(
        skills_mod.subprocess, "run",
        lambda *a, **k: calls.append(a) or (_ for _ in ()).throw(
            AssertionError(f"subprocess.run must not be called in dry-run: {a}")
        ),
    )

    skills_mod.ensure_skill_repo(
        agent_meta_root, project_root, "demo-repo",
        {"repo": "https://example.invalid/demo.git",
         "local_path": "external/demo-repo"},
        "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
        SyncLog(),
        dry_run=True,
    )

    assert calls == []
    assert not (project_root / "external" / "demo-repo").exists()
    assert not (agent_meta_root / "external" / "demo-repo").exists()


def test_sync_external_skills_dry_run_never_deinits_awesome_claude_code(
    tmp_path, monkeypatch,
):
    """The awesome-claude-code deinit call site is dry-run gated.

    Before the fix this branch (enabled repo, scout role absent) called
    ``deinit_skill_repo()`` even in dry-run — the inactive-repos loop was gated
    but this trailing branch was not, so the F04 invariant held only by luck of
    the callee's internal guard.
    """
    agent_meta_root = tmp_path / "agent-meta"
    _write_registry(agent_meta_root)
    wrapper_dir = agent_meta_root / "agents" / "0-external"
    wrapper_dir.mkdir(parents=True)
    (wrapper_dir / "_skill-wrapper.md").write_text(
        (_REPO_ROOT / "agents" / "0-external" / "_skill-wrapper.md").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )
    project_root = tmp_path / "project"
    project_root.mkdir()

    calls: list = []
    monkeypatch.setattr(
        skills_mod, "ensure_skill_repo",
        lambda *a, **k: calls.append(("ensure",) + a),
    )
    monkeypatch.setattr(
        skills_mod, "deinit_skill_repo",
        lambda *a, **k: calls.append(("deinit",) + a),
    )

    provider_config = {
        "Claude": {"agents_dir": ".claude/agents", "skills_dir": ".claude/skills"}
    }

    # Empty roles -> "agent-meta-scout" absent -> the trailing acc branch is
    # entered in a real sync. It must stay silent in dry-run.
    skills_mod.sync_external_skills_for_provider(
        agent_meta_root, project_root, {"roles": []}, {}, SyncLog(),
        dry_run=True, provider="Claude", provider_config=provider_config,
    )

    assert calls == []
    assert not (project_root / "external").exists()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
