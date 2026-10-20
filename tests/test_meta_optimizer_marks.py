"""Runtime-reader marks and the ``confirm-runtime`` gate (Task 25 / 2d.6, AC-81).

Binding: ``docs/plans/2026-10-17-context-profiles-phase2-plan.md`` Task 25,
``docs/specs/2026-10-11-context-profiles-spec.md`` AC-81 (line 2312), IC-24
runtime-reader definition (spec lines 1427-1430) and the Mark definition
(lines 500-503).

Every key from ``config/runtime-config-readers.yaml`` carries the Mark
``runtime-reader``, ``approval_level: confirm-runtime`` and the mandatory German
text ``Wird zur Laufzeit von <Leser> gelesen; der Beweis (IC-25) deckt dieses
Verhalten nicht ab.`` -- for *every* candidate kind, including ``info-only``
hints. Non-variable runtime keys (``repo_containment``, ``orchestrator``) get an
``info-only`` hint when no producer emitted a candidate. Credential keys take
precedence and are excluded completely. A ``confirm-runtime`` candidate is only
applied when it is also listed in ``accept_runtime_ids`` (otherwise
``rejected: needs-runtime-confirmation``).

Run: .venv-1/bin/python -m pytest tests/test_meta_optimizer_marks.py -q
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SINK_SUBDIR = ("scratch", "out", "meta-optimizer")

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import meta_optimizer as mo  # noqa: E402
from lib.active_set import compute_active_set  # noqa: E402

TOKEN = "adminuisecrettokenvalue1234567890"
RUNTIME_MARK = "runtime-reader"
CONFIRM_RUNTIME = "confirm-runtime"
REFILL_MARK = "refilled-by-defaults"

TEST_TIMEOUT_PATH = "variables.TEST_TIMEOUT"
TEST_COMMAND_PATH = "variables.TEST_COMMAND"
DOD_READER = "hooks/1-generic/dod-push-check.sh"
REPO_READER = "hooks/1-generic/repo-containment-impl.sh"
ORCHESTRATOR_READER = "hooks/1-generic/orchestrator-guard-impl.sh"


def _mandatory_text(reader: str) -> str:
    return (
        "Wird zur Laufzeit von {} gelesen; der Beweis (IC-25) deckt dieses "
        "Verhalten nicht ab.".format(reader)
    )


# --- fixture ---------------------------------------------------------------

def _fixture_text() -> str:
    version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    return (
        "# Runtime-reader fixture (Task 25 / 2d.6).\n"
        'agent-meta-version: "' + version + '"\n'
        "ai-providers:\n"
        "- Claude\n"
        "dod-preset: rapid-prototyping\n"
        "project:\n"
        "  name: marksfixture\n"
        "  prefix: mk\n"
        "repo_containment:\n"
        "  tmp-sink:\n"
        "    enabled: true\n"
        "    path: scratch/out\n"
        "orchestrator:\n"
        "  strict: true\n"
        "admin-ui:\n"
        "  token: " + TOKEN + "\n"
        "variables:\n"
        "  PROJECT_NAME: marksfixturetoken\n"
        "  TEST_COMMAND: pytest tests/\n"
        '  TEST_TIMEOUT: "600"\n'
    )


def _init_project(root: Path, text: str) -> Path:
    (root / ".meta-config").mkdir(parents=True, exist_ok=True)
    cfg = root / ".meta-config" / "project.yaml"
    cfg.write_text(text, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=str(root), check=True)
    return cfg


def _proposal(root: Path):
    text = _fixture_text()
    cfg = _init_project(root, text)
    config = yaml.safe_load(text)
    active = compute_active_set(config, REPO_ROOT, root, warn_sink=[])
    proposal = mo.collect_candidates(root, REPO_ROOT, config, text, active)
    return cfg, config, proposal


def _candidate(proposal, path: str):
    matches = [c for c in proposal.candidates if c.yaml_path == path]
    assert matches, sorted(c.yaml_path for c in proposal.candidates)
    return matches[0]


# --- (a) API-level classification -----------------------------------------

def test_runtime_reader_candidates_carry_mark_approval_and_reader_text(tmp_path):
    """AC-81: every runtime key names its reader and needs ``confirm-runtime``."""
    _cfg, _config, proposal = _proposal(tmp_path)

    # Applicable removal candidate (registered runtime reader, unreferenced).
    removable = _candidate(proposal, TEST_TIMEOUT_PATH)
    assert removable.kind == "no-effect"
    assert removable.applicable is True
    assert RUNTIME_MARK in removable.marks
    assert removable.approval_level == CONFIRM_RUNTIME
    assert removable.deterministic is False
    assert _mandatory_text(DOD_READER) in removable.warnings

    # Always rendered -> no removal candidate, but still an info-only hint.
    rendered = _candidate(proposal, TEST_COMMAND_PATH)
    assert rendered.kind == "info-only"
    assert rendered.applicable is False
    assert rendered.hunks == ()
    assert RUNTIME_MARK in rendered.marks
    assert rendered.approval_level == CONFIRM_RUNTIME
    assert _mandatory_text(DOD_READER) in rendered.warnings

    # Non-variable runtime keys get an explicit hint (AC-81 clause).
    containment = _candidate(proposal, "repo_containment")
    assert containment.kind == "info-only"
    assert containment.applicable is False
    assert containment.hunks == ()
    assert {RUNTIME_MARK, REFILL_MARK} <= set(containment.marks)
    assert containment.approval_level == CONFIRM_RUNTIME
    assert _mandatory_text(REPO_READER) in containment.warnings
    assert mo._REFILL_WARNING in containment.warnings

    orchestrator = _candidate(proposal, "orchestrator")
    assert orchestrator.kind == "info-only"
    assert orchestrator.applicable is False
    assert RUNTIME_MARK in orchestrator.marks
    assert orchestrator.approval_level == CONFIRM_RUNTIME
    assert _mandatory_text(ORCHESTRATOR_READER) in orchestrator.warnings


def test_credential_keys_are_excluded_before_the_runtime_mark(tmp_path):
    """AC-89 precedence: no candidate/hint below ``admin-ui.token``, no value."""
    _cfg, _config, proposal = _proposal(tmp_path)
    payload = json.dumps(mo._proposal_dict(proposal))

    for candidate in proposal.candidates:
        assert candidate.yaml_path not in ("admin-ui", "admin-ui.token",
                                           "admin-ui.token-file")
        assert not candidate.yaml_path.startswith("admin-ui.")
    assert TOKEN not in payload


def test_runtime_reader_warning_joins_multiple_readers_sorted():
    """Multiple readers: sorted, distinct, comma-joined."""
    warning = mo._runtime_reader_warning(("z/reader.sh", "a/reader.sh", "z/reader.sh"))
    assert warning == _mandatory_text("a/reader.sh, z/reader.sh")


# --- (b) direct helper robustness -----------------------------------------

def test_removable_candidate_falls_back_to_framework_registry():
    """Direct helper callers get the reader names without passing a map."""
    text = _fixture_text()

    containment = mo._removable_candidate(
        text, "repo_containment", "no-effect", rationale="x",
        runtime_reader=True, credential_lines={})
    assert containment.approval_level == CONFIRM_RUNTIME
    assert RUNTIME_MARK in containment.marks
    assert _mandatory_text(REPO_READER) in containment.warnings

    orchestrator = mo._removable_candidate(
        text, "orchestrator.strict", "no-effect", rationale="x",
        runtime_reader=True, credential_lines={})
    assert orchestrator.approval_level == CONFIRM_RUNTIME
    assert _mandatory_text(ORCHESTRATOR_READER) in orchestrator.warnings

    guarded = mo._refill_guard(
        containment, mo.refill_keys(REPO_ROOT, yaml.safe_load(text)))
    assert RUNTIME_MARK in guarded.marks
    assert REFILL_MARK in guarded.marks
    assert guarded.approval_level == CONFIRM_RUNTIME
    assert _mandatory_text(REPO_READER) in guarded.warnings


# --- (c) application gate --------------------------------------------------

def _write_proposal(proposal, path: Path) -> Path:
    path.write_text(json.dumps(mo._proposal_dict(proposal)), encoding="utf-8")
    return path


def test_confirm_runtime_requires_accept_runtime(tmp_path):
    """Without ``accept_runtime_ids`` -> ``needs-runtime-confirmation``."""
    cfg, _config, proposal = _proposal(tmp_path)
    candidate = _candidate(proposal, TEST_TIMEOUT_PATH)
    assert candidate.approval_level == CONFIRM_RUNTIME
    proposal_path = _write_proposal(proposal, tmp_path / "proposal.json")
    before = cfg.read_bytes()

    report = mo.apply_config_patch(
        tmp_path, REPO_ROOT, proposal_path, (candidate.id,), dry_run=True)

    assert report.exit_code == 1, report
    assert (candidate.id, mo.REJECT_NEEDS_RUNTIME) in report.rejected
    assert report.applied_ids == ()
    assert cfg.read_bytes() == before


def test_confirm_runtime_is_applied_with_accept_runtime(tmp_path):
    """With ``accept_runtime_ids`` the existing applier accepts the candidate."""
    cfg, _config, proposal = _proposal(tmp_path)
    candidate = _candidate(proposal, TEST_TIMEOUT_PATH)
    proposal_path = _write_proposal(proposal, tmp_path / "proposal.json")
    before = cfg.read_bytes()

    report = mo.apply_config_patch(
        tmp_path, REPO_ROOT, proposal_path, (candidate.id,),
        accept_runtime_ids=(candidate.id,), dry_run=True)

    assert report.exit_code == 0, (report, report.errors)
    assert candidate.id in report.applied_ids
    assert report.rejected == ()
    assert cfg.read_bytes() == before  # dry run never writes the config
    assert report.preview_path is not None
    assert Path(report.preview_path).is_file()
    assert Path(report.preview_path).parent.parent == tmp_path.joinpath(*SINK_SUBDIR)
