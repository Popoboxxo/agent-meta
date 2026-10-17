"""IC-18 no. 17 / AC-45 / AC-84: scout skill derivation via ActiveSet.

``sync_external_skills_for_provider`` implicitly activates the
``awesome-claude-code`` repo only when the ``agent-meta-scout`` role is
active -- decided by the sanctioned ``ActiveSet.raw_roles`` allowlist
(IC-17 addendum, D1) intersected with ``ActiveSet.has("agent-meta-scout")``.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib import skills as skills_mod  # noqa: E402
from lib.active_set import ActiveSet  # noqa: E402
from lib.log import SyncLog  # noqa: E402

_PROVIDER_CONFIG = {"Claude": {"agents_dir": ".claude/agents", "skills_dir": ".claude/skills"}}


def _active(*roles: str, raw_roles=None) -> ActiveSet:
    frozen = frozenset(roles)
    return ActiveSet(
        roles=frozen, routable=frozen, known_roles=frozen, sources={}, gates={},
        gate_dropped=(), missing_template=(), producers={}, raw_roles=raw_roles,
    )


def _ensured_repos(monkeypatch, tmp_path: Path, config: dict, active_set: ActiveSet) -> list:
    calls: list = []
    monkeypatch.setattr(
        skills_mod, "ensure_skill_repo",
        lambda _amr, _pr, repo_name, *a, **k: calls.append(repo_name),
    )
    project_root = tmp_path / "project"
    project_root.mkdir()
    skills_mod.sync_external_skills_for_provider(
        _REPO_ROOT, project_root, config, {}, SyncLog(), False, "Claude",
        _PROVIDER_CONFIG, active_set=active_set,
    )
    return calls


@pytest.mark.parametrize("allowlist", [None, ["agent-meta-scout"]])
def test_scout_not_in_active_set_does_not_enable_skill(monkeypatch, tmp_path, allowlist):
    # No allowlist (default render stays unchanged) or a gate-dropped scout
    # named in the allowlist must not pull in awesome-claude-code.
    config = {} if allowlist is None else {"roles": allowlist}
    raw = frozenset(allowlist) if allowlist is not None else None
    assert "awesome-claude-code" not in _ensured_repos(
        monkeypatch, tmp_path, config, _active("developer", raw_roles=raw))


def test_scout_in_active_set_enables_skill(monkeypatch, tmp_path):
    repos = _ensured_repos(
        monkeypatch, tmp_path, {"roles": ["agent-meta-scout"]},
        _active("developer", "agent-meta-scout",
                raw_roles=frozenset({"agent-meta-scout"})))
    assert "awesome-claude-code" in repos
