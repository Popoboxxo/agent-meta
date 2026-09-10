"""Finding 1 (PR #721): CheckpointStore must resolve agent_meta_root from the
`.agent-meta/` submodule layout when the caller omits it, so a hook-less
provider in a real (non-self-hosted) project is classified Tier B (append),
not Tier A (overwrite). Regression the live-progress-channel PR set out to fix.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.checkpoint import Checkpoint, CheckpointStore  # noqa: E402
from lib.providers import resolve_agent_meta_root  # noqa: E402


def _downstream_project(tmp_path: Path) -> Path:
    """A downstream project embedding agent-meta as a `.agent-meta/` submodule
    (symlinked to the real checkout) and declaring a hook-less provider."""
    project = tmp_path / "downstream"
    project.mkdir()
    (project / ".agent-meta").symlink_to(_REPO_ROOT, target_is_directory=True)
    (project / ".meta-config").mkdir()
    (project / ".meta-config" / "project.yaml").write_text(
        "ai-providers: [Opencode]\n", encoding="utf-8"
    )
    return project


def test_agent_meta_root_defaults_to_submodule(tmp_path):
    # (a) omitting agent_meta_root resolves to the `.agent-meta/` submodule,
    # NOT the project root (which has no framework sources / provider config).
    project = _downstream_project(tmp_path)
    store = CheckpointStore(project_root=project)
    assert store.agent_meta_root == resolve_agent_meta_root(project)
    assert store.agent_meta_root == project / ".agent-meta"
    assert (store.agent_meta_root / "config" / "ai-providers.yaml").exists()


def test_hookless_provider_gets_tier_b_via_resolved_root(tmp_path):
    # (b) with the submodule auto-resolved, a hook-less provider (Opencode)
    # lands on Tier B — the append log keeps every entry instead of
    # overwriting. Two checkpoints => two rendered status tables.
    project = _downstream_project(tmp_path)
    store = CheckpointStore(project_root=project)
    store.save_checkpoint(
        "sess1", Checkpoint(task_id="t1", agent="developer", task_description="first", status="completed")
    )
    store.save_checkpoint(
        "sess1", Checkpoint(task_id="t2", agent="tester", task_description="second", status="in_progress")
    )
    content = (project / ".meta-viz" / "progress" / "current.md").read_text(encoding="utf-8")
    assert "first" in content and "second" in content
    assert content.count("| Agent | Task | Status | Pipeline/Stage |") == 2


def test_self_hosting_root_stays_project_root(tmp_path):
    # Self-hosting (no `.agent-meta/`, no framework sources): fall back to the
    # project root, preserving the pre-existing bare-tmp_path fixture behavior.
    assert resolve_agent_meta_root(tmp_path) == tmp_path
    assert resolve_agent_meta_root(_REPO_ROOT) == _REPO_ROOT


def test_trim_keeps_entry_with_forged_marker_in_task(tmp_path):
    # Finding 3: a task_description containing a literal "\n## " must not be
    # mistaken for an entry boundary during rotation.
    project = _downstream_project(tmp_path)
    store = CheckpointStore(project_root=project)
    forged = "line1\n## 2020-01-01 00:00:00 — session `fake` still-same-entry"
    store.save_checkpoint(
        "sess1", Checkpoint(task_id="t1", agent="dev", task_description=forged, status="completed")
    )
    store.save_checkpoint(
        "sess1", Checkpoint(task_id="t2", agent="dev", task_description="second", status="completed")
    )
    content = (project / ".meta-viz" / "progress" / "current.md").read_text(encoding="utf-8")
    # Exactly two REAL entries despite the forged marker inside the first task.
    from lib.checkpoint import _ENTRY_HEADER_RE  # noqa: E402
    assert len(_ENTRY_HEADER_RE.findall(content)) == 2
