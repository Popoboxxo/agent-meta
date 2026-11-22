"""REQ-ID format validator (issue #1167, Phase H Task 20).

Binding format (O-H2 decision 22.11, spec SPEC-REQ-ID-FORMAT-1167-2026-11-11
IC-1): ``^REQ-[A-Z][A-Z0-9]*-\\d{2,3}$`` with ``re.fullmatch``. One uppercase
area segment without ``-``, 2 or 3 digits.

The check is silent when ``dod.req-traceability`` is off and emits one
``Severity.ERROR`` finding per malformed occurrence when it is on.

Run: python3 -m pytest tests/test_req_id_format.py -q
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib.consistency.report import Severity  # noqa: E402
from lib.consistency.req_format import REQ_ID_PATTERN, check_req_ids  # noqa: E402

#: Task 21 — agent templates whose REQ wording is gated on DOD_REQ_TRACEABILITY.
GATED_AGENTS = (
    "validator",
    "bug-feature-analyzer",
    "requirements",
    "se-requirements",
    "se-developer",
    "api-specialist",
)
#: Canonical format token (spec IC-4 / O-H2 decision \d{2,3}).
CANONICAL_FORMAT = "REQ-<AREA>-<NN>"


def _render_project(root: Path, *, traceability: bool) -> Path:
    """Sync a scratch project with either DoD state and return its root."""
    project = root / ("trace-on" if traceability else "rapid")
    (project / ".meta-config").mkdir(parents=True)
    dod_override = "dod:\n  req-traceability: true\n" if traceability else ""
    (project / ".meta-config" / "project.yaml").write_text(
        "ai-providers:\n- Claude\n"
        "dod-preset: rapid-prototyping\n"
        + dod_override
        + "systems-engineering:\n  enabled: true\n"
        + "roles:\n" + "".join(f"- {role}\n" for role in GATED_AGENTS)
        + "variables:\n  PROJECT_NAME: req-gate-probe\n  PROJECT_PREFIX: rg\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    result = subprocess.run(
        [sys.executable, str(_SCRIPTS / "sync.py"),
         "--config", str(project / ".meta-config" / "project.yaml")],
        cwd=project, capture_output=True, text=True, timeout=300,
    )
    assert result.returncode == 0, (
        f"sync failed for traceability={traceability}\n"
        f"{result.stdout[-1500:]}\n{result.stderr[-1500:]}"
    )
    return project


def _rendered_agent(project: Path, role: str) -> str:
    path = project / ".claude" / "agents" / f"{role}.md"
    assert path.is_file(), f"rendered agent missing: {path}"
    return path.read_text(encoding="utf-8")


def _run(tmp_path: Path, body: str, *, traceability: bool):
    """Write a synthetic REQUIREMENTS.md and run the check against it."""
    framework = tmp_path / "framework"
    framework.mkdir(parents=True, exist_ok=True)
    project = tmp_path / "project"
    (project / "docs").mkdir(parents=True)
    (project / "docs" / "REQUIREMENTS.md").write_text(body, encoding="utf-8")
    config = {"platforms": [], "dod": {"req-traceability": traceability}}
    return check_req_ids(framework, project, config)


def test_malformed_req_id_fails_when_traceability_on(tmp_path):
    findings = _run(tmp_path, "- REQ-1 (too few digits)\n", traceability=True)
    assert len(findings) == 1
    assert findings[0].severity is Severity.ERROR
    assert findings[0].check == "req-id.format"


def test_malformed_req_id_ignored_when_off(tmp_path):
    assert _run(tmp_path, "- REQ-1 (too few digits)\n", traceability=False) == []


def test_valid_ids_pass_both_states(tmp_path):
    # AC1: the constant is byte-identical to the binding O-H2 form.
    assert REQ_ID_PATTERN == r"^REQ-[A-Z][A-Z0-9]*-\d{2,3}$"
    body = "- REQ-CMD-01 (two digits)\n- REQ-COM-123 (three digits)\n"
    assert _run(tmp_path, body, traceability=True) == []
    assert _run(tmp_path / "off", body, traceability=False) == []


def test_multi_part_area_rejected(tmp_path):
    findings = _run(tmp_path, "- REQ-L2-AT-018 (multi-part area)\n", traceability=True)
    assert len(findings) == 1
    assert findings[0].severity is Severity.ERROR
    assert "REQ-L2-AT-018" in findings[0].message


def test_single_area_accepted(tmp_path):
    assert _run(tmp_path, "- REQ-CMD-01 (single area)\n", traceability=True) == []


def test_three_digit_accepted(tmp_path):
    assert _run(tmp_path, "- REQ-COM-123 (three digits)\n", traceability=True) == []


def test_four_digit_rejected(tmp_path):
    findings = _run(tmp_path, "- REQ-COM-1234 (four digits)\n", traceability=True)
    assert len(findings) == 1
    assert findings[0].severity is Severity.ERROR
    assert "REQ-COM-1234" in findings[0].message


# --- Task 21: render gating on DOD_REQ_TRACEABILITY -------------------------


def test_render_rapid_prototyping_has_no_req_mandate(tmp_path):
    """rapid-prototyping must render no ungated REQ mandate / old format."""
    project = _render_project(tmp_path, traceability=False)
    validator = _rendered_agent(project, "validator")
    triage = _rendered_agent(project, "bug-feature-analyzer")
    requirements = _rendered_agent(project, "requirements")

    # The commit-format mandate and the old placeholder must be gone.
    assert "(REQ-xxx): <description>" not in validator
    assert CANONICAL_FORMAT not in validator
    # Ungated triage mandates ("REQ-ID needed", "for a REQ-ID") must be gone.
    assert "(REQ-ID needed)" not in triage
    assert "for a REQ-ID, then" not in triage
    assert CANONICAL_FORMAT not in triage
    # The REQ-ID schema placeholder must not render in the minimal preset.
    assert "REQ-xxx" not in requirements
    assert CANONICAL_FORMAT not in requirements


def test_render_traceability_on_shows_canonical_format(tmp_path):
    """With traceability on, every touched agent shows the canonical format."""
    project = _render_project(tmp_path, traceability=True)
    for role in GATED_AGENTS:
        text = _rendered_agent(project, role)
        assert CANONICAL_FORMAT in text, f"{role}: canonical REQ format missing"
