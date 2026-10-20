"""``inactive-scope`` candidates and their reactivation warning (Task 24 / 2d.5, AC-83).

Binding: ``docs/plans/2026-10-17-context-profiles-phase2-plan.md`` Task 24 and
``docs/specs/2026-10-11-context-profiles-spec.md`` AC-83 (line 2319 ff.) plus
the Mark definition ``inactive-scope``/``reactivation-loss-warning`` (spec
lines 500-517, 1415-1417).

A variable that is only referenced by roles which are *inactive* in the current
Active Set is not ``no-effect``: at some later reactivation the value is gone.
The optimizer must classify it as ``inactive-scope`` (``deterministic: False``),
mark it with ``reactivation-loss-warning`` and carry the mandatory German
warning that starts with "Bei späterer Reaktivierung ..." and names the
inactive role(s). After accepting/removing the value and re-activating the
role, the next sync reports ``active-set.unresolved-placeholder`` (the value is
not in ``_VARIABLE_FALLBACKS``) exactly as the warning announces.

The fixture below is derived from ``tests/fixtures/active-set/p10`` (study
10.2/AC-43): the same ten-role subset, but with ``tester`` *and* ``documenter``
removed. Both are the only p10 roles that reference ``{{TEST_COMMANDS}}``
(``test-executor``/``e2e-tester`` are not part of p10 at all), so adding
``variables.TEST_COMMANDS`` makes it inactive-scope in this active set.

Run: .venv-1/bin/python -m pytest tests/test_meta_optimizer_inactive_scope.py -q
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNC = REPO_ROOT / "scripts" / "sync.py"
P10_CONFIG = REPO_ROOT / "tests" / "fixtures" / "active-set" / "p10" / ".meta-config" / "project.yaml"
SINK_SUBDIR = ("scratch", "out", "meta-optimizer")
RUN_TIMEOUT = 900

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import meta_optimizer as mo  # noqa: E402
from lib.active_set import compute_active_set  # noqa: E402

TEST_COMMANDS_PATH = "variables.TEST_COMMANDS"
REACTIVATION_MARK = "reactivation-loss-warning"
INACTIVE_MARK = "inactive-scope"


# --- fixture ---------------------------------------------------------------

def _p10_without_testers_text() -> str:
    """p10 subset minus ``tester``/``documenter``, with ``TEST_COMMANDS`` set.

    Derived from the binding p10 fixture instead of duplicating the role list,
    so a future change to p10 cannot silently diverge from this test.
    """
    data = yaml.safe_load(P10_CONFIG.read_text(encoding="utf-8"))
    data["roles"] = [role for role in data["roles"] if role not in ("tester", "documenter")]
    assert "tester" not in data["roles"] and "documenter" not in data["roles"]
    # The optimizer is read-only outside the repo-containment tmp-sink; the same
    # setup the refill/runner tests use for their subprocess projects.
    data["repo_containment"] = {"tmp-sink": {"enabled": True, "path": "scratch/out"}}
    data["variables"] = {
        # Referenced by active roles -> effective, never a candidate.
        "PROJECT_NAME": "inactivefixturetoken",
        # Referenced only by the removed roles -> inactive-scope.
        "TEST_COMMANDS": "pytest tests/",
    }
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def _write_project(tmp_path: Path, text: str) -> Path:
    (tmp_path / ".meta-config").mkdir(parents=True, exist_ok=True)
    cfg = tmp_path / ".meta-config" / "project.yaml"
    cfg.write_text(text, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True)
    return cfg


def _run(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SYNC), "--config", ".meta-config/project.yaml", *args],
        cwd=str(root), capture_output=True, text=True, timeout=RUN_TIMEOUT,
    )


def _run_dirs(root: Path) -> list:
    base = root.joinpath(*SINK_SUBDIR)
    return sorted(p for p in base.iterdir() if p.is_dir()) if base.is_dir() else []


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# --- unit: candidate classification ---------------------------------------

def test_inactive_scope_candidate_carries_german_reactivation_warning(tmp_path):
    """AC-83: ``TEST_COMMANDS`` with inactive ``tester`` is not ``no-effect``."""
    cfg = _write_project(tmp_path, _p10_without_testers_text())
    text = cfg.read_text(encoding="utf-8")
    config = yaml.safe_load(text)
    active = compute_active_set(config, REPO_ROOT, tmp_path, warn_sink=[])

    proposal = mo.collect_candidates(
        tmp_path, REPO_ROOT, config, text, active, work_dir=tmp_path / "work")

    candidate = next(
        c for c in proposal.candidates if c.yaml_path == TEST_COMMANDS_PATH)
    assert candidate.kind == INACTIVE_MARK
    assert candidate.deterministic is False
    assert {INACTIVE_MARK, REACTIVATION_MARK} <= set(candidate.marks)

    warning = " ".join(candidate.warnings)
    assert "Bei späterer Reaktivierung" in warning
    assert "tester" in warning
    assert "unaufgelöst" in warning

    # AC-83, second sentence of the "Falle": it is NOT a no-effect candidate.
    assert not any(
        c.kind == "no-effect" and c.yaml_path == TEST_COMMANDS_PATH
        for c in proposal.candidates)


def test_reactivation_warning_announces_framework_default_for_fallback_names():
    """``_VARIABLE_FALLBACKS`` names announce the framework default (AC-83)."""
    from lib.config import _VARIABLE_FALLBACKS

    assert "PROJECT_GOAL" in _VARIABLE_FALLBACKS

    fallback_warning = mo._reactivation_warning(
        ("tester",), has_fallback=True)
    assert fallback_warning.startswith("Bei späterer Reaktivierung")
    assert "tester" in fallback_warning
    assert "Framework-Default" in fallback_warning
    assert "unaufgelöst" not in fallback_warning

    unresolved_warning = mo._reactivation_warning(
        ("tester",), has_fallback=False)
    assert unresolved_warning.startswith("Bei späterer Reaktivierung")
    assert "unaufgelöst" in unresolved_warning


# --- end-to-end: apply, reactivate, re-sync (AC-83) -----------------------

def test_apply_then_reactivation_reports_unresolved_placeholder(tmp_path):
    """AC-83: accepted removal + reactivated role -> unresolved-placeholder."""
    root = tmp_path
    cfg = _write_project(root, _p10_without_testers_text())

    # 1) Baseline sync renders the p10-like active set.
    baseline = _run(root)
    assert baseline.returncode == 0, baseline.stdout[-1500:] + baseline.stderr[-2000:]

    # 2) Optimizer proposal.
    optimized = _run(root, "--optimize-config", "--json")
    assert optimized.returncode == 0, optimized.stdout[-1500:] + optimized.stderr[-2000:]
    proposal_path = _run_dirs(root)[-1] / "proposal.json"
    proposal = _load(proposal_path)

    candidate = next(
        c for c in proposal["candidates"] if c["yaml_path"] == TEST_COMMANDS_PATH)
    assert candidate["kind"] == INACTIVE_MARK
    assert candidate["deterministic"] is False
    assert candidate["applicable"] is True
    assert {INACTIVE_MARK, REACTIVATION_MARK} <= set(candidate["marks"])
    warning = " ".join(candidate["warnings"])
    assert "Bei späterer Reaktivierung" in warning
    assert "tester" in warning
    assert "unaufgelöst" in warning
    assert not any(
        c["kind"] == "no-effect" and c["yaml_path"] == TEST_COMMANDS_PATH
        for c in proposal["candidates"])

    # 3) Preview (dry run), then apply bound to the shown preview.
    accept_id = candidate["id"]
    preview_run = _run(
        root, "--apply-config-patch", str(proposal_path),
        "--accept", accept_id, "--dry-run", "--json")
    assert preview_run.returncode == 0, preview_run.stdout[-1500:] + preview_run.stderr[-2000:]
    preview_path = sorted(root.joinpath(*SINK_SUBDIR).glob("*/preview.json"))[-1]

    applied = _run(
        root, "--apply-config-patch", str(proposal_path),
        "--accept", accept_id, "--preview", str(preview_path), "--json")
    assert applied.returncode == 0, applied.stdout[-1500:] + applied.stderr[-2000:]
    after_apply = cfg.read_text(encoding="utf-8")
    assert "TEST_COMMANDS" not in after_apply

    # 4) Re-activate the role that references the removed value.
    data = yaml.safe_load(after_apply)
    data["roles"] = list(data.get("roles") or []) + ["tester"]
    cfg.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")

    # 5) Re-sync: the warning is now observable as an unresolved placeholder.
    resynced = _run(root)
    assert resynced.returncode == 0, resynced.stdout[-1500:] + resynced.stderr[-2000:]
    log = (root / "sync.log").read_text(encoding="utf-8")
    assert "active-set.unresolved-placeholder" in log
    assert "{{TEST_COMMANDS}}" in log

    tester_artifact = root / ".claude" / "agents" / "tester.md"
    assert tester_artifact.is_file(), sorted(
        p.name for p in (root / ".claude" / "agents").glob("*.md"))
    # TEST_COMMANDS is not in _VARIABLE_FALLBACKS -> placeholder stays unresolved.
    assert "{{TEST_COMMANDS}}" in tester_artifact.read_text(encoding="utf-8")
