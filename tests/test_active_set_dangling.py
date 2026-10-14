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
    # IC-18 no. 2 (pipeline drop): bug-feature-analyzer, ideation and validator were
    # dispatched only from pipeline blocks that are no longer rendered on p10, so they
    # leave the dangling set; the remaining AC-43 roles stay covered.
    for role in ("senior-developer", "concept-specifier", "concept-reviewer"):
        assert f"'{role}'" in text, role
    for role in ("validator", "bug-feature-analyzer", "ideation"):
        assert f"'{role}'" not in text, role
    # Pin the exact (file, role) set so heuristic drift is visible.
    pairs = {(f.file.rsplit("/", 1)[-1], f.message.split("'")[1]) for f in findings}
    assert pairs == {("documenter.md", "knowledge-ingestor")} | {
        ("orchestrator.md", r) for r in (
            "concept-architect", "concept-reviewer", "concept-specifier",
            "junior-developer", "principal-developer", "senior-developer")}
    assert len(findings) == 7


def test_p10_dangling_mention_is_info(synced):
    project, active = synced("p10")
    findings = asr.check_dangling_mention(project, _PROVIDERS, {}, active)
    assert findings and all(f.severity == Severity.INFO for f in findings)
    assert all(f.check == "active-set.dangling-mention" for f in findings)
    pairs = {(f.file.rsplit("/", 1)[-1], f.message.split("'")[1]) for f in findings}
    # Prose references (boundary lists, "Delegation (reference only)") are mentions.
    assert {("code-reviewer.md", "validator"), ("release.md", "validator"),
            ("developer.md", "validator"), ("tester.md", "se-validator")} <= pairs
    assert all("(" in f.message and "x," in f.message for f in findings)  # count + first line


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


# --- heuristics, allowlists, negatives -------------------------------------

def _scratch(tmp_path, body, name="x.md"):
    agents = tmp_path / ".claude" / "agents"
    agents.mkdir(parents=True)
    (agents / name).write_text(body, encoding="utf-8")
    return tmp_path


def _dangling_roles_of(findings):
    return sorted({f.message.split("'")[1] for f in findings})


def test_dispatch_to_active_role_is_not_a_finding(synced, tmp_path):
    _, active = synced("p10")
    proj = _scratch(tmp_path, 'background(agent="developer", prompt="x")\n'
                              "| Tier | When |\n|---|---|\n| `developer` | std |\n")
    assert asr.check_dangling_dispatch(proj, _PROVIDERS, {}, active) == []
    assert asr.check_dangling_mention(proj, _PROVIDERS, {}, active) == []


def test_arrow_and_conditional_are_not_dispatch(synced, tmp_path):
    _, active = synced("p10")
    proj = _scratch(tmp_path, "Boundary: DoD check -> `validator`\n"
                              "Condition evaluated by validator: ok\n")
    assert asr.check_dangling_dispatch(proj, _PROVIDERS, {}, active) == []
    assert _dangling_roles_of(asr.check_dangling_mention(proj, _PROVIDERS, {}, active)) == ["validator"]


def test_table_heuristic_positive_only_dispatch_columns(synced, tmp_path):
    _, active = synced("p10")
    proj = _scratch(tmp_path, "| Tier | When |\n|---|---|\n"
                              "| `senior-developer` | after `validator` fails |\n")
    found = asr.check_dangling_dispatch(proj, _PROVIDERS, {}, active)
    assert _dangling_roles_of(found) == ["senior-developer"]


def test_table_heuristic_boundary_no_dispatch_header(synced, tmp_path):
    _, active = synced("p10")
    proj = _scratch(tmp_path, "| Name | Notes |\n|---|---|\n| `senior-developer` | x |\n")
    assert asr.check_dangling_dispatch(proj, _PROVIDERS, {}, active) == []
    assert _dangling_roles_of(asr.check_dangling_mention(proj, _PROVIDERS, {}, active)) == ["senior-developer"]


def test_fanout_head_slots_are_matched(synced, tmp_path):
    _, active = synced("p10")
    proj = _scratch(tmp_path, 'FANOUT(3, validator):\n  - background(agent="ideation", prompt="x")\n')
    found = asr.check_dangling_dispatch(proj, _PROVIDERS, {}, active)
    assert _dangling_roles_of(found) == ["ideation", "validator"]


def test_placeholder_allow_suppresses(synced, tmp_path, monkeypatch):
    _, active = synced("p10")
    proj = _scratch(tmp_path, "{{FOO_BAR}} and {{BAZ}}\n")
    monkeypatch.setattr(asr, "_refs", lambda: {"placeholder_allow": ["{{FOO_BAR}}"]})
    found = asr.check_unresolved_placeholder(proj, _PROVIDERS, {}, active)
    assert [("{{BAZ}}" in f.message) for f in found] == [True]


def test_mention_allow_suppresses(synced, tmp_path, monkeypatch):
    _, active = synced("p10")
    proj = _scratch(tmp_path, "see `validator`\n")
    assert asr.check_dangling_mention(proj, _PROVIDERS, {}, active)
    monkeypatch.setattr(asr, "_refs", lambda: {"mention_allow": [".claude/agents/x.md"]})
    assert asr.check_dangling_mention(proj, _PROVIDERS, {}, active) == []


_SYNTAX = yaml.safe_load((_ROOT / "config" / "delegation-syntax.yaml").read_text(encoding="utf-8"))
_ALL_PROVIDERS = sorted(_SYNTAX["delegation_syntax"])


@pytest.mark.parametrize("provider", _ALL_PROVIDERS)
def test_every_provider_derives_a_dispatch_pattern(provider):
    fmts = asr._dispatch_formats(_ROOT, provider)
    pats = [asr._fmt_pattern(f, "validator") for f in fmts]
    assert fmts and all(pats), f"{provider}: formats {fmts}"


def test_non_dispatch_keys_conditional_item_is_unit_excluded(monkeypatch):
    monkeypatch.setattr(asr, "load_yaml_file", lambda path: {"delegation_syntax": {"P": {
        "pipeline_notation": {
            "task_fmt": "run({agent})",
            "conditional_item": "  - Condition evaluated by {agent}: {task}"}}}})
    assert asr._dispatch_formats(_ROOT, "P") == ["run({agent})"]
    pat = asr._fmt_pattern("run({agent})", "validator")
    assert pat.search("run(validator)")
    assert asr._NON_DISPATCH_KEYS == ("conditional",)


def test_conditional_line_yields_no_dispatch(synced, tmp_path):
    _, active = synced("p10")
    proj = _scratch(tmp_path, "  - Condition evaluated by validator: x\n")
    assert asr.check_dangling_dispatch(proj, _PROVIDERS, {}, active) == []


def test_phrase_patterns_positive():
    pats, invalid = asr._phrase_patterns("validator")
    assert invalid == []
    assert any(p.search("delegiere an validator") for p in pats)
    assert any(p.search("Hand off to the `validator`") for p in pats)
    assert not any(p.search("validator is nice") for p in pats)


def test_invalid_phrase_regex_is_surfaced(synced, tmp_path, monkeypatch):
    _, active = synced("p10")
    monkeypatch.setattr(asr, "_refs", lambda: {"dispatch_phrases": {"en": ["bad(", "route to"]}})
    proj = _scratch(tmp_path, "route to validator\n")
    found = asr.check_dangling_dispatch(proj, _PROVIDERS, {}, active)
    checks = sorted(f.check for f in found)
    assert checks == ["active-set.dangling-dispatch", "active-set.invalid-dispatch-phrase"]
    assert all(f.severity == Severity.WARNING for f in found)
