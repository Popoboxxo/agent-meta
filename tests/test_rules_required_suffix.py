"""IC-15 Nr. 3 / AC-14 (F-13): Copilot native rule files need the
``.instructions.md`` suffix plus ``applyTo``/``description`` frontmatter, and
generated agent files must carry a bare ``name:`` (no agent extension).

Red (before the fix): ``.github/instructions/<rule>.md`` without the required
suffix exists and the agent frontmatter reads ``name: orchestrator.agent``.
Green: the syncer consumes the ``rules_required_suffix`` / ``agent_ext``
capabilities (no provider literal) and routes legacy files through the managed
cleanup.

Run: python -m pytest tests/test_rules_required_suffix.py -q
"""

from __future__ import annotations

from pathlib import Path

from scripts.lib.agent_sync import _finalize_agent_content
from scripts.lib.log import SyncLog
from scripts.lib.providers import load_providers_config
from scripts.lib.rules import sync_rules

_REPO_ROOT = Path(__file__).resolve().parents[1]

_SUFFIX = ".instructions.md"
_RULES_DIR = ".github/instructions"

_PROVIDER_CONFIG = {
    "Copilot": {
        "rules_dir": _RULES_DIR,
        "rules_apply_to": "**",
        "agent_ext": ".agent.md",
    }
}


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _agent_meta_root(tmp_path: Path) -> Path:
    root = tmp_path / "agent-meta"
    _write(
        root / "config" / "provider-capabilities.yaml",
        'capabilities:\n  Copilot:\n    rules_required_suffix: ".instructions.md"\n',
    )
    _write(
        root / "rules" / "1-generic" / "branch-guard.md",
        "# Branch Guard\n\nNo code changes on main.\n",
    )
    return root


def test_sync_rules_writes_required_suffix_with_frontmatter(tmp_path):
    root = _agent_meta_root(tmp_path)
    project = tmp_path / "project"

    sync_rules(
        root, project, {}, SyncLog(), dry_run=False, variables={},
        rules_dir=_RULES_DIR, provider="Copilot", provider_config=_PROVIDER_CONFIG,
    )

    target = project / _RULES_DIR / f"branch-guard{_SUFFIX}"
    assert target.is_file()
    assert not (project / _RULES_DIR / "branch-guard.md").exists()
    text = target.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert 'applyTo: "**"' in text
    assert 'description: "No code changes on main."' in text


def test_sync_rules_managed_cleanup_removes_legacy_unsuffixed_file(tmp_path):
    root = _agent_meta_root(tmp_path)
    project = tmp_path / "project"
    rules_dir = project / _RULES_DIR
    _write(rules_dir / "branch-guard.md", "# legacy\n")
    _write(rules_dir / ".agent-meta-managed", "branch-guard.md\n")
    _write(rules_dir / "own-rule.md", "# foreign\n")  # never indexed

    sync_rules(
        root, project, {}, SyncLog(), dry_run=False, variables={},
        rules_dir=_RULES_DIR, provider="Copilot", provider_config=_PROVIDER_CONFIG,
    )

    assert (rules_dir / f"branch-guard{_SUFFIX}").is_file()
    assert not (rules_dir / "branch-guard.md").exists()
    assert (rules_dir / "own-rule.md").is_file()


def test_sync_rules_without_suffix_capability_keeps_plain_md(tmp_path):
    root = _agent_meta_root(tmp_path)
    _write(root / "config" / "provider-capabilities.yaml", "capabilities:\n  Other: {}\n")
    project = tmp_path / "project"
    provider_config = {"Other": {"rules_dir": ".rules", "agent_ext": ".md"}}

    sync_rules(
        root, project, {}, SyncLog(), dry_run=False, variables={},
        rules_dir=".rules", provider="Other", provider_config=provider_config,
    )

    assert (project / ".rules" / "branch-guard.md").is_file()
    assert not (project / ".rules" / f"branch-guard{_SUFFIX}").exists()


def test_finalize_agent_name_strips_full_agent_ext(tmp_path):
    provider_config = load_providers_config(_REPO_ROOT)
    target = tmp_path / ".github" / "agents" / "orchestrator.agent.md"
    target.parent.mkdir(parents=True, exist_ok=True)

    out = _finalize_agent_content(
        "---\nname: orchestrator\ndescription: probe\nversion: 1.0.0\n---\n\nBody.\n",
        "orchestrator",
        "orchestrator.agent.md",
        _REPO_ROOT / "agents" / "1-generic" / "orchestrator.md",
        "Copilot",
        provider_config,
        None,
        "probe",
        True,
        {},
        _REPO_ROOT,
        tmp_path,
        target,
        {},
        False,
        SyncLog(),
    )

    assert "name: orchestrator\n" in out
    assert "name: orchestrator.agent" not in out
