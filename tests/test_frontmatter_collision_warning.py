"""Regression test for issue #703: when two active platforms both ship a
2-platform override for the same role name, the second one silently wins
today with zero signal. collect_sources() must warn (when a log is passed)
naming the role and both competing source files."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.frontmatter import collect_sources
from lib.log import SyncLog


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_collision_between_two_platforms_is_warned(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    _write(agent_meta_root / "agents" / "2-platform" / "alpha-developer.md",
           "---\nname: developer\n---\nbody-a")
    _write(agent_meta_root / "agents" / "2-platform" / "beta-developer.md",
           "---\nname: developer\n---\nbody-b")
    log = SyncLog()

    overrides, _ = collect_sources(agent_meta_root, ["alpha", "beta"], log=log)

    assert overrides["developer"].name == "beta-developer.md"  # last-writer-wins, unchanged
    assert any(
        "developer" in w and "alpha-developer.md" in w and "beta-developer.md" in w
        for w in log.warnings
    )


def test_no_collision_when_only_one_platform_active(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    _write(agent_meta_root / "agents" / "2-platform" / "alpha-developer.md",
           "---\nname: developer\n---\nbody-a")
    log = SyncLog()

    overrides, _ = collect_sources(agent_meta_root, ["alpha"], log=log)

    assert log.warnings == []


def test_log_is_optional_and_call_sites_are_unaffected(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    _write(agent_meta_root / "agents" / "2-platform" / "alpha-developer.md",
           "---\nname: developer\n---\nbody-a")
    _write(agent_meta_root / "agents" / "2-platform" / "beta-developer.md",
           "---\nname: developer\n---\nbody-b")

    overrides, known_ext = collect_sources(agent_meta_root, ["alpha", "beta"])  # no log kwarg

    assert overrides["developer"].name == "beta-developer.md"
