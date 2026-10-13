"""IC-19 active-set reference checks (Task 0b.3, AC-43)."""
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

from lib.active_set import compute_active_set  # noqa: E402
from lib.consistency import active_set_refs as asr  # noqa: E402
from lib.consistency.report import Severity  # noqa: E402

_FIX = Path(__file__).resolve().parent / "fixtures" / "active-set"
_AC43_ROLES = ("senior-developer", "validator", "bug-feature-analyzer",
               "concept-specifier", "concept-reviewer", "ideation")
_PROVIDERS = ["Claude"]


@pytest.fixture(scope="module")
def synced(tmp_path_factory):
    """Sync a fixture into a scratch project once per fixture name."""
    cache = {}

    def _get(name):
        if name in cache:
            return cache[name]
        project = tmp_path_factory.mktemp(name) / name
        (project / ".meta-config").mkdir(parents=True)
        cfg_text = (_FIX / name / ".meta-config" / "project.yaml").read_text(encoding="utf-8")
        (project / ".meta-config" / "project.yaml").write_text(cfg_text, encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=project, check=True)
        res = subprocess.run(
            [sys.executable, str(_ROOT / "scripts" / "sync.py"), "--config",
             str(project / ".meta-config" / "project.yaml"), "--init"],
            cwd=project, capture_output=True, text=True, timeout=300)
        assert res.returncode == 0, res.stdout[-1500:] + res.stderr[-1500:]
        config = yaml.safe_load(cfg_text)
        active = compute_active_set(config, _ROOT, project)
        cache[name] = (project, active)
        return cache[name]

    return _get


def test_p10_dangling_dispatch_covers_ac43_roles(synced):
    project, active = synced("p10")
    findings = asr.check_dangling_dispatch(project, _PROVIDERS, {}, active)
    assert findings and all(f.severity == Severity.WARNING for f in findings)
    assert all(f.check == "active-set.dangling-dispatch" for f in findings)
    text = " ".join(f.message for f in findings)
    for role in _AC43_ROLES:
        assert f"'{role}'" in text, role


def test_p10_dangling_mention_is_info(synced):
    project, active = synced("p10")
    findings = asr.check_dangling_mention(project, _PROVIDERS, {}, active)
    assert findings and all(f.severity == Severity.INFO for f in findings)
    assert all(f.check == "active-set.dangling-mention" for f in findings)


def test_p20_gate_dropped_reports_senior_developer(synced):
    project, active = synced("p20")
    findings = asr.check_gate_dropped(project, _PROVIDERS, {}, active)
    assert any(f.check == "active-set.gate-dropped" and "senior-developer" in f.message
               and "developer_tiers" in f.message for f in findings)
    assert all(f.severity == Severity.WARNING for f in findings)


def test_pall_unresolved_placeholder_extra_donts(synced):
    project, active = synced("pall")
    findings = asr.check_unresolved_placeholder(project, _PROVIDERS, {}, active)
    assert any(f.check == "active-set.unresolved-placeholder"
               and "{{EXTRA_DONTS}}" in f.message for f in findings)
    assert all(f.severity == Severity.WARNING for f in findings)


def test_unknown_role_in_allowlist(synced, tmp_path):
    project, active = synced("p10")
    scratch = tmp_path / "proj"
    (scratch / ".meta-config").mkdir(parents=True)
    (scratch / ".meta-config" / "project.yaml").write_text(
        "roles:\n- orchestrator\n- no-such-role\n", encoding="utf-8")
    findings = asr.check_unknown_role(scratch, _PROVIDERS, {}, active)
    assert [f.check for f in findings] == ["active-set.unknown-role"]
    assert "no-such-role" in findings[0].message
    assert asr.check_unknown_role(project, _PROVIDERS, {}, active) == []


def test_missing_dispatch_pattern_is_reported_not_silent(synced, monkeypatch):
    project, active = synced("p10")
    monkeypatch.setattr(asr, "_dispatch_formats", lambda root, provider: [])
    findings = asr.check_dangling_dispatch(project, _PROVIDERS, {}, active)
    assert [f.check for f in findings] == ["active-set.dispatch-pattern-missing"]
    assert findings[0].severity == Severity.WARNING
    assert "Claude" in findings[0].message


def test_module_has_no_provider_branch_or_print():
    src = (_ROOT / "scripts" / "lib" / "consistency" / "active_set_refs.py").read_text(encoding="utf-8")
    assert "provider ==" not in src and "print(" not in src
