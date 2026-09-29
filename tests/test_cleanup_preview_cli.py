"""IC-06 ``--cleanup-preview`` (Task 6, AC-10 / AC-15 CLI flow / AC-24).

The CLI preview is the read-only half of the B-II Admin-UI removal path: it
reuses the pure planning traversal (``_resolve_sync_targets``,
``_should_skip_role``, IC-03 collectors, ``plan_agent_cleanup``) without calling
a single writer stage and emits exactly one JSON object on stdout (IC-06).

Covered here:

* ``test_preview_emits_single_json_object`` -- schema + one-object-on-stdout.
* ``test_preview_has_no_filesystem_or_network_mutation`` -- AC-10/F-04: tree is
  byte-identical, no index write/unlink/backup, no clone/submodule add even
  though an active skill references a repo that is absent.
* ``test_preview_exit_code_zero_for_nonempty_stale`` -- rc 0 for a non-empty
  stale set.
* ``test_preview_fingerprint_stable_over_canonical_stale_set`` -- IC-06 stable
  fingerprint.
* ``test_foreign_entries_carry_legacy_unmarked`` -- OQ-3/AC-10 flag semantics,
  plus the ``foreign`` derivation (``plan_agent_cleanup`` only returns stale).
* ``test_external_skill_repo_calls_gated_in_dry_run`` -- F-04 skills.py gate.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import sync  # noqa: E402
from lib.agent_sync import StaleAgentEntry  # noqa: E402
from lib.log import SyncLog  # noqa: E402


_MINIMAL_PROJECT_YAML = """\
agent-meta-version: 0.101.0
ai-providers: [Claude]
roles: [orchestrator, developer, git]
external-skills:
  reqogniloom-change-manager:
    enabled: true
project:
  name: cleanup-preview-test
  prefix: cpt
  short: cleanup-preview-test
"""

_INDEX = "developer.md\nstale-old.md\n"

_MARKERLESS = "user-authored file\n"

_BASED_ONLY = (
    "---\n"
    "name: based-only\n"
    "based-on: \"1-generic/developer.md@1.0.0\"\n"
    "---\n"
    "body\n"
)

_NON_EXTERNAL_MARKER = (
    "---\n"
    "name: legacy-gen\n"
    "generated-from: 1-generic/legacy-gen@1.0.0\n"
    "---\n"
    "body\n"
)

# One source with five old backups: the oldest is prunable (age > 30 days AND
# more than 3 newer siblings), the second-oldest has exactly 3 newer ones.
_BACKUP_NAMES = [
    "old.md.sync-backup-20200101-000000",
    "old.md.sync-backup-20200102-000000",
    "old.md.sync-backup-20200103-000000",
    "old.md.sync-backup-20200104-000000",
    "old.md.sync-backup-20200105-000000",
]


def _agents_dir(project_root: Path) -> Path:
    return project_root / ".claude" / "agents"


def _write_preview_fixture(project_root: Path) -> Path:
    """Create a project with one stale, three foreign and five backup files."""
    config_dir = project_root / ".meta-config"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "project.yaml"
    config_path.write_text(_MINIMAL_PROJECT_YAML, encoding="utf-8")

    agents = _agents_dir(project_root)
    agents.mkdir(parents=True)
    (agents / ".agent-meta-managed").write_text(_INDEX, encoding="utf-8")
    (agents / "stale-old.md").write_text("stale generated role\n", encoding="utf-8")
    (agents / "my-own.md").write_text(_MARKERLESS, encoding="utf-8")
    (agents / "based-only.md").write_text(_BASED_ONLY, encoding="utf-8")
    (agents / "legacy-gen.md").write_text(_NON_EXTERNAL_MARKER, encoding="utf-8")
    for name in _BACKUP_NAMES:
        (agents / name).write_text("backup\n", encoding="utf-8")
    return config_path


def _run_preview(project_root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py"),
         "--config", str(project_root / ".meta-config" / "project.yaml"),
         "--cleanup-preview"],
        cwd=str(project_root), capture_output=True, text=True, timeout=120,
    )


def _claude_payload(payload: dict) -> dict:
    for entry in payload["providers"]:
        if entry["provider"] == "Claude":
            return entry
    raise AssertionError("Claude provider missing from preview payload")


def _snapshot_tree(root: Path) -> dict:
    snapshot = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            snapshot[path.relative_to(root).as_posix()] = path.read_bytes()
    return snapshot


def test_preview_emits_single_json_object(tmp_path):
    """AC-10: exactly one JSON object with the IC-06 schema on stdout."""
    _write_preview_fixture(tmp_path)

    result = _run_preview(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    # json.loads() fails on any trailing/leading text => one object only.
    payload = json.loads(result.stdout)
    assert payload["version"] == 1
    assert payload["fingerprint"].startswith("sha256:")

    claude = _claude_payload(payload)
    assert set(claude) == {"provider", "stale", "foreign", "backups_to_prune"}

    stale_by_path = {entry["path"]: entry for entry in claude["stale"]}
    stale = stale_by_path[".claude/agents/stale-old.md"]
    assert set(stale) == {"path", "reason", "tracked", "adopted"}
    assert stale["reason"] == "role removed from config"
    assert stale["tracked"] is True
    assert stale["adopted"] is False

    # IC-05/N-01 gap: the preview recomputes the would-be prune set purely.
    assert claude["backups_to_prune"] == [
        ".claude/agents/old.md.sync-backup-20200101-000000"
    ]


def test_preview_has_no_filesystem_or_network_mutation(tmp_path, monkeypatch):
    """AC-10/F-04: side-effect-free even with an absent skill repo.

    The fixture activates an external skill; ``ensure_skill_repo`` would
    otherwise clone/submodule-add for its repo. The preview must neither touch
    the project tree nor run any subprocess.
    """
    _write_preview_fixture(tmp_path)
    before = _snapshot_tree(tmp_path)

    def _forbidden_run(*args, **kwargs):  # pragma: no cover - must not trigger
        raise AssertionError("preview must not run any subprocess")

    # Build the real context first (context building may probe git), then
    # forbid subprocesses for the planning traversal itself.
    args = sync._build_arg_parser().parse_args(
        ["--config", str(tmp_path / ".meta-config" / "project.yaml")])
    from lib import cli_commands

    args.dry_run = True  # keep context building read-only in the self-hosting repo
    ctx = cli_commands._build_context(args, _REPO_ROOT, SyncLog())
    assert ctx is not None

    monkeypatch.setattr(subprocess, "run", _forbidden_run)
    sync._handle_cleanup_preview(ctx)

    assert _snapshot_tree(tmp_path) == before
    assert not (tmp_path / "external").exists()


def test_preview_exit_code_zero_for_nonempty_stale(tmp_path):
    """AC-10: a non-empty stale set is a successful preview (rc 0)."""
    _write_preview_fixture(tmp_path)

    result = _run_preview(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert _claude_payload(payload)["stale"]


def test_preview_fingerprint_stable_over_canonical_stale_set():
    """IC-06: the fingerprint is order-independent over the stale set."""
    a = StaleAgentEntry(
        provider="Claude", path=".claude/agents/a.md",
        reason="role removed from config", tracked=True, adopted=False)
    b = StaleAgentEntry(
        provider="Opencode", path=".opencode/agents/b.md",
        reason="skill deactivated", tracked=False, adopted=True)

    first = sync._cleanup_fingerprint([a, b])
    assert first == sync._cleanup_fingerprint([b, a])
    assert first.startswith("sha256:")
    assert first != sync._cleanup_fingerprint([a])
    # Empty stale set still yields a stable, deterministic fingerprint.
    assert sync._cleanup_fingerprint([]) == sync._cleanup_fingerprint([])


def test_foreign_entries_carry_legacy_unmarked(tmp_path):
    """OQ-3/AC-10: marker-less (and unrecognised) foreign files are flagged."""
    _write_preview_fixture(tmp_path)

    result = _run_preview(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    claude = _claude_payload(json.loads(result.stdout))
    foreign = {entry["path"]: entry["legacy_unmarked"] for entry in claude["foreign"]}

    assert set(foreign) == {
        ".claude/agents/my-own.md",
        ".claude/agents/based-only.md",
        ".claude/agents/legacy-gen.md",
    }
    assert foreign[".claude/agents/my-own.md"] is True
    assert foreign[".claude/agents/based-only.md"] is True
    # A recognised (non-external) primary marker is NOT legacy-unmarked.
    assert foreign[".claude/agents/legacy-gen.md"] is False


_SKILL_REGISTRY = """\
repos:
  demo-repo:
    repo: https://example.invalid/demo.git
    local_path: external/demo-repo
  idle-repo:
    repo: https://example.invalid/idle.git
    local_path: external/idle-repo
skills:
  demo-skill:
    approved: true
    repo: demo-repo
    source: skills/demo
    entry: SKILL.md
    role: demo-role
    enabled-by-default: true
  idle-skill:
    approved: true
    repo: idle-repo
    source: skills/idle
    entry: SKILL.md
    role: idle-role
    planned: true
"""


def _write_skill_fixture(tmp_path: Path) -> tuple:
    agent_meta_root = tmp_path / "agent-meta"
    (agent_meta_root / "config").mkdir(parents=True)
    (agent_meta_root / "config" / "skills-registry.yaml").write_text(
        _SKILL_REGISTRY, encoding="utf-8")
    wrapper_dir = agent_meta_root / "agents" / "0-external"
    wrapper_dir.mkdir(parents=True)
    wrapper_dir.joinpath("_skill-wrapper.md").write_text(
        (_REPO_ROOT / "agents" / "0-external" / "_skill-wrapper.md").read_text(encoding="utf-8"),
        encoding="utf-8")
    project_root = tmp_path / "project"
    project_root.mkdir()
    return agent_meta_root, project_root


def test_external_skill_repo_calls_gated_in_dry_run(tmp_path, monkeypatch):
    """F-04: ``ensure_skill_repo``/``deinit_skill_repo`` are not called in dry-run."""
    from lib import skills as skills_mod

    agent_meta_root, project_root = _write_skill_fixture(tmp_path)
    calls: list = []
    monkeypatch.setattr(
        skills_mod, "ensure_skill_repo", lambda *a, **k: calls.append(("ensure",) + a))
    monkeypatch.setattr(
        skills_mod, "deinit_skill_repo", lambda *a, **k: calls.append(("deinit",) + a))

    provider_config = {
        "Claude": {"agents_dir": ".claude/agents", "skills_dir": ".claude/skills"}}

    skills_mod.sync_external_skills_for_provider(
        agent_meta_root, project_root, {}, {}, SyncLog(), dry_run=True,
        provider="Claude", provider_config=provider_config)

    assert calls == []
    assert not (project_root / "external").exists()

    skills_mod.sync_external_skills_for_provider(
        agent_meta_root, project_root, {}, {}, SyncLog(), dry_run=False,
        provider="Claude", provider_config=provider_config)

    kinds = {call[0] for call in calls}
    assert "ensure" in kinds
    assert "deinit" in kinds
