"""Sync-time artifact-contract gate + exit-code policy (plan Task 3).

Spec anchor: SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30, §2.1/§2.2 and §5
(three-tier signal + exit codes); acceptance AC-13 (sync end) + AC-3a.

Covers:

* ``_finalize_agent_content`` validates the finalized artifact against the
  provider's declared contract before it is written and logs a
  ``[WARN] artifact-contract: <file>: <message>`` line (fail-soft, rc 0).
* The singleton constraint is injected into the body **before** provider
  serialization, so a Codex ``.codex/agents/*.toml`` document parses with
  ``tomllib`` and carries the singleton inside ``developer_instructions``
  (finding D1/N1).
* The allow-list is the v2 silent-drop guard: it is enforced on the v2 surface
  only (via the shared ``artifact_validate.resolve_artifact_contract`` used by
  both the sync-time warning and ``consistency/artifact_contracts``), so the v1
  tree keeps its byte shape.
* ``artifact-validation: false`` (per provider, Task 5) disables the check for
  that provider only; an absent flag is treated as enabled.
* The read-only ``--check``/``--validate`` gate fails loud (rc 1) when a
  generated artifact violates the declared contract, while a normal sync stays
  rc 0. A registry that cannot be loaded also yields an ERROR finding instead of
  silently passing.

Run: python3 -m pytest tests/test_sync_validation_gate.py -q
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SYNC_PY = _REPO_ROOT / "scripts" / "sync.py"
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib import agent_sync  # noqa: E402
from lib.consistency.report import Severity  # noqa: E402
from lib.log import SyncLog  # noqa: E402
from lib.providers import load_providers_config  # noqa: E402


# ---------------------------------------------------------------------------
# Unit: _finalize_agent_content wiring
# ---------------------------------------------------------------------------

_SAMPLE_AGENT = (
    "---\n"
    "name: developer\n"
    "description: unit probe\n"
    "model: probe-model\n"
    "---\n"
    "\n"
    "Body content.\n"
)


def _probe_pc(surface: str = "v2", allowed: list | None = None) -> dict:
    return {
        "Probe": {
            "agents_dir": ".probe/agents",
            "agent_ext": ".md",
            "surface-version": surface,
            "agent-transform": {
                "frontmatter-mechanism": "provider-md",
                "allowed-fields": allowed if allowed is not None else ["name", "description"],
                "reject-fields": [],
            },
        }
    }


def _finalize(content: str, provider_config: dict, provider: str, project_root: Path,
              *, filename: str = "developer.md", can_spawn: bool = True,
              log: SyncLog | None = None) -> tuple[str, SyncLog]:
    log = log or SyncLog()
    target = project_root / f".{provider.lower()}" / "agents" / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    out = agent_sync._finalize_agent_content(
        content,
        "developer",
        filename,
        _REPO_ROOT / "agents" / "1-generic" / "developer.md",
        provider,
        provider_config,
        None,
        "unit probe",
        can_spawn,
        {},
        _REPO_ROOT,
        project_root,
        target,
        {},
        False,
        log,
    )
    return out, log


def test_finalize_warns_on_v2_allowlist_violation(tmp_path: Path) -> None:
    _out, log = _finalize(_SAMPLE_AGENT, _probe_pc("v2"), "Probe", tmp_path)

    artifact_warnings = [w for w in log.warnings if "artifact-contract" in w]
    assert artifact_warnings, "expected an artifact-contract warning"
    assert any("'model' is not in allowed-fields" in w for w in artifact_warnings)
    assert all(".probe/agents/developer.md" in w for w in artifact_warnings)


def test_finalize_does_not_enforce_allowlist_on_v1_surface(tmp_path: Path) -> None:
    _out, log = _finalize(_SAMPLE_AGENT, _probe_pc("v1"), "Probe", tmp_path)

    assert [w for w in log.warnings if "artifact-contract" in w] == []


def test_finalize_respects_artifact_validation_false(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        agent_sync,
        "load_provider_capabilities",
        lambda _root: {"Probe": {"artifact-validation": False, "artifact-validation-reason": "probe"}},
    )

    _out, log = _finalize(_SAMPLE_AGENT, _probe_pc("v2"), "Probe", tmp_path)

    assert [w for w in log.warnings if "artifact-contract" in w] == []


def test_finalize_absent_artifact_validation_flag_is_enabled(tmp_path: Path) -> None:
    _out, log = _finalize(_SAMPLE_AGENT, _probe_pc("v2"), "Probe", tmp_path)

    assert [w for w in log.warnings if "artifact-contract" in w]


def test_finalize_codex_toml_singleton_inside_developer_instructions(tmp_path: Path) -> None:
    provider_config = load_providers_config(_REPO_ROOT)
    out, _log = _finalize(
        "---\nname: developer\ndescription: unit probe\n---\n\nBody.\n",
        provider_config,
        "Codex",
        tmp_path,
        filename="developer.toml",
        can_spawn=True,
    )

    doc = tomllib.loads(out)
    assert "Singleton-Regel" in doc["developer_instructions"]


# ---------------------------------------------------------------------------
# Unit: collect_artifact_findings (the read-only --check/--validate gate)
# ---------------------------------------------------------------------------


def test_collect_artifact_findings_scans_active_providers(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        agent_sync, "load_providers_config", lambda _root: _probe_pc("v2")
    )
    agents_dir = tmp_path / ".probe" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "bad.md").write_text(
        "---\nname: bad\ndescription: probe\nmodel: x\n---\nBody.\n", encoding="utf-8"
    )
    (agents_dir / "good.md").write_text(
        "---\nname: good\ndescription: probe\n---\nBody.\n", encoding="utf-8"
    )

    findings = agent_sync.collect_artifact_findings(
        _REPO_ROOT, tmp_path, {"ai-providers": ["Probe"]}
    )

    assert [rel for rel, _finding in findings] == [".probe/agents/bad.md"]
    assert "not in allowed-fields" in findings[0][1].message


def test_collect_artifact_findings_clean_tree_is_empty(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        agent_sync, "load_providers_config", lambda _root: _probe_pc("v2")
    )
    agents_dir = tmp_path / ".probe" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "good.md").write_text(
        "---\nname: good\ndescription: probe\n---\nBody.\n", encoding="utf-8"
    )

    assert agent_sync.collect_artifact_findings(
        _REPO_ROOT, tmp_path, {"ai-providers": ["Probe"]}
    ) == []


def test_collect_artifact_findings_registry_failure_fails_loud(monkeypatch, tmp_path: Path) -> None:
    """A registry-load failure must not silently disable the fail-loud gate."""

    def _boom(_root):
        raise RuntimeError("registry exploded")

    monkeypatch.setattr(agent_sync, "load_providers_config", _boom)

    findings = agent_sync.collect_artifact_findings(
        _REPO_ROOT, tmp_path, {"ai-providers": ["Probe"]}
    )

    assert findings, "a registry failure must yield a finding, not an empty pass"
    _rel, finding = findings[0]
    assert finding.severity == Severity.ERROR
    assert finding.check == "artifact-contract"
    assert "could not be loaded" in finding.message


# ---------------------------------------------------------------------------
# Integration: real sync.py CLI against a self-hosting scratch checkout
# ---------------------------------------------------------------------------

_HEAVY_IGNORE = shutil.ignore_patterns(
    ".git",
    ".venv",
    ".tmp",
    "graphify-out",
    "external",
    "node_modules",
    ".pytest_cache",
    ".ruff_cache",
    ".opencode",
    "__pycache__",
    "*.pyc",
)

_PROJECT_YAML = """\
agent-meta-version: 0.101.0
ai-providers: [Opencode]
dod-preset: rapid-prototyping
roles: [orchestrator, developer, git]
project:
  name: artifact-gate
  prefix: ag
  short: artifact-gate
variables:
  PROJECT_NAME: artifact-gate
  PROJECT_DESCRIPTION: artifact-contract gate probe
  PROJECT_GOAL: prove the --check/--validate exit codes
  GIT_PLATFORM: GitHub
  GIT_REMOTE_URL: https://github.com/example/artifact-gate
  GIT_MAIN_BRANCH: main
rules-preset: default
speech-mode: full
tier-preset: Normal
max-parallel-agents: 2
conventions-preset: default
"""


def _make_self_hosting_scratch(tmp_path: Path) -> Path:
    """Copy the repo and narrow Opencode's contract to the v2 surface."""
    dest = tmp_path / "meta-copy"
    shutil.copytree(_REPO_ROOT, dest, ignore=_HEAVY_IGNORE)

    config_path = dest / "config" / "ai-providers.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    opencode = config["providers"]["Opencode"]
    opencode["surface-version"] = "v2"
    opencode["agent-transform"]["allowed-fields"] = ["name", "description"]
    config_path.write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    (dest / ".meta-config").mkdir(exist_ok=True)
    (dest / ".meta-config" / "project.yaml").write_text(_PROJECT_YAML, encoding="utf-8")
    return dest


def _run_scratch_sync(project_root: Path, *extra_args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(project_root / "scripts" / "sync.py"), *extra_args],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )


def test_scratch_normal_sync_warns_and_check_validate_fail(tmp_path: Path) -> None:
    scratch = _make_self_hosting_scratch(tmp_path)

    # A normal sync stays fail-soft (rc 0) and logs the warning.
    normal = _run_scratch_sync(scratch)
    assert normal.returncode == 0, normal.stdout + normal.stderr
    assert "artifact-contract:" in normal.stdout + normal.stderr

    # The fail-soft path is WARNING-level and lands in sync.log's WARNINGS
    # section (spec §5), not just the stderr `!` line.
    sync_log_text = (scratch / "sync.log").read_text(encoding="utf-8")
    assert "WARNINGS" in sync_log_text
    assert "[WARN]   artifact-contract:" in sync_log_text

    # The read-only gates fail loud on the same generated artifacts.
    validate = _run_scratch_sync(scratch, "--validate")
    assert validate.returncode == 1, validate.stdout + validate.stderr
    assert "artifact-contract" in validate.stderr

    check = _run_scratch_sync(scratch, "--check")
    assert check.returncode == 1, check.stdout + check.stderr
    assert "artifact-contract" in check.stderr
