"""IC-10 context budget and reachability checks (AC-08, SPEC-CONTEXT-PROFILES-2026-10-11).

Two layers:

* synthetic projects pin each check's rule (caps, markers, unread channels);
* freshly synced provider-matrix projects pin AC-08: the known defects are
  reported as WARNINGs. The numbers below were measured against the real state
  (``sync.py --init`` of a single-provider project, 2026-10-13):

  - preset ``default``: ``use-lazy-rules`` lists 15 skills, none of them is
    generated for Codex/Mammouth/Gemini/Continue (their skills directories are
    empty) -> 15 ``context.dangling-pointer`` rows each (AC-08 requires >= 10)
    plus one for the "Uebrige Regeln (Lazy-Load)" pointer when it is rendered.
  - preset ``lazy``: Gemini embeds only 11 of its 19 rules in AGENTS.md, had no
    rules read channel (``rules_read_channels: []``) and no lazy skills, so
    exactly 8 rules were lost -> 8 ``context.rule-unreachable`` (AC-08 "die 8
    verlorenen Gemini-lazy-Rules"). The lost set is a2a-delegation-gates,
    issue-lifecycle, lifecycle-tasks, the three se-cascade-* rules,
    session-conclusion and submodule-protection. Fixed by IC-15 Nr. 2 (skills
    channel); the AC-08 tests reproduce the defect by removing the skills.

Run: python3 -m pytest tests/test_context_budget_checks.py -q
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import context_report as cr  # noqa: E402
from lib.active_set import compute_active_set  # noqa: E402
from lib.consistency import context_budget as cb  # noqa: E402
from lib.consistency.report import Severity  # noqa: E402
from lib.providers import load_provider_capabilities, load_providers_config  # noqa: E402
from tests.test_ac01_render_identity import _make_project, _run_sync  # noqa: E402

# Runtime: the default-preset matrix renders only Gemini, Claude and Codex (each synced
# project costs ~10 s). Mammouth/Continue share the same empty-skills-dir defect
# (measured in the docstring above) but are not re-rendered here.
DEFAULT_MATRIX = ["Gemini", "Claude", "Codex"]
LAZY_TABLE_SKILLS = 15
GEMINI_LOST_LAZY_RULES = {
    "a2a-delegation-gates", "issue-lifecycle", "lifecycle-tasks",
    "se-cascade-adr-standard", "se-cascade-artifact-taxonomy",
    "se-cascade-review-lifecycle", "session-conclusion", "submodule-protection",
}


def _make_lazy_project(root: Path, provider: str) -> Path:
    project = root / (provider + "-lazy")
    (project / ".meta-config").mkdir(parents=True)
    (project / ".meta-config" / "project.yaml").write_text(
        'agent-meta-version: "2.0.0-beta.1"\n'
        f"ai-providers:\n- {provider}\n"
        "dod-preset: rapid-prototyping\nrules-preset: lazy\n"
        "variables:\n  PROJECT_NAME: matrix\n  PROJECT_PREFIX: mx\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    result = _run_sync(project, "--init")
    assert result.returncode == 0, result.stdout[-1000:] + result.stderr[-1000:]
    return project


@pytest.fixture(scope="module")
def mappings():
    return cr.merge_provider_mappings(
        load_providers_config(REPO_ROOT, {}), load_provider_capabilities(REPO_ROOT))


@pytest.fixture(scope="module")
def default_projects(tmp_path_factory):
    root = tmp_path_factory.mktemp("budget-default")
    return {p: _make_project(root, p) for p in DEFAULT_MATRIX}


@pytest.fixture(scope="module")
def lazy_projects(tmp_path_factory):
    root = tmp_path_factory.mktemp("budget-lazy")
    return {p: _make_lazy_project(root, p) for p in ("Gemini", "Claude")}


def _active_set(project: Path):
    config = yaml.safe_load((project / ".meta-config" / "project.yaml").read_text(encoding="utf-8"))
    return compute_active_set(config, REPO_ROOT, project)


def _run(check, project: Path, provider: str, mappings):
    return check(project, [provider], mappings, _active_set(project))


ALL_CHECKS = [
    cb.check_over_hard_cap, cb.check_over_soft_cap, cb.check_dangling_pointer,
    cb.check_rule_unreachable, cb.check_unread_channel, cb.check_marker_in_rule,
]


# --- AC-08: known defects on real synced projects ---------------------------

@pytest.mark.parametrize("provider", ["Gemini", "Codex"])
def test_ac08_missing_skills_are_reported(default_projects, mappings, provider):
    findings = _run(cb.check_dangling_pointer, default_projects[provider], provider, mappings)
    skills = [f for f in findings if "lazy table names skill" in f.message]
    assert len(skills) >= 10
    assert len(skills) == LAZY_TABLE_SKILLS
    assert {f.check for f in findings} == {"context.dangling-pointer"}
    assert all(f.severity is Severity.WARNING for f in findings)
    assert {f.file for f in skills}  # each finding names the artifact carrying the pointer


def _without_skills(project: Path, tmp_path: Path, mappings) -> Path:
    """Copy of a synced Gemini project with its skills dir removed (pre-IC-15 Nr. 2 state)."""
    copy = tmp_path / "gemini-no-skills"
    shutil.copytree(project, copy)
    shutil.rmtree(copy / mappings["Gemini"]["skills_dir"], ignore_errors=True)
    return copy


def test_ac08_lazy_pointer_without_any_skill_is_reported(lazy_projects, mappings, tmp_path):
    # the "Uebrige Regeln (Lazy-Load)" pointer is only rendered with rules-preset lazy.
    # IC-15 Nr. 2 writes the lazy skills now; the defect is reproduced by removing them.
    assert not [f for f in _run(cb.check_dangling_pointer, lazy_projects["Gemini"], "Gemini", mappings)
                if "lazy-load pointer" in f.message]
    project = _without_skills(lazy_projects["Gemini"], tmp_path, mappings)
    findings = _run(cb.check_dangling_pointer, project, "Gemini", mappings)
    assert any("lazy-load pointer promises rule skills" in f.message for f in findings)


def test_ac08_gemini_lazy_preset_loses_eight_rules(lazy_projects, mappings, tmp_path):
    # Fixed by IC-15 Nr. 2: the 8 lazy rules reach Gemini as skills.
    assert _run(cb.check_rule_unreachable, lazy_projects["Gemini"], "Gemini", mappings) == []
    project = _without_skills(lazy_projects["Gemini"], tmp_path, mappings)
    findings = _run(cb.check_rule_unreachable, project, "Gemini", mappings)
    assert {Path(f.file).stem for f in findings} == GEMINI_LOST_LAZY_RULES
    assert len(findings) == 8
    assert all(f.check == "context.rule-unreachable" and f.severity is Severity.WARNING
               for f in findings)


def test_ac08_default_preset_gemini_has_no_unreachable_rule(default_projects, mappings):
    assert _run(cb.check_rule_unreachable, default_projects["Gemini"], "Gemini", mappings) == []


def test_ac08_claude_native_rules_dir_is_reachable(lazy_projects, mappings):
    assert _run(cb.check_rule_unreachable, lazy_projects["Claude"], "Claude", mappings) == []


def test_unread_channel_flags_gemini_rules_dir_not_claude(default_projects, mappings):
    gemini = _run(cb.check_unread_channel, default_projects["Gemini"], "Gemini", mappings)
    assert [f.file for f in gemini] == [".gemini/rules"]
    assert _run(cb.check_unread_channel, default_projects["Claude"], "Claude", mappings) == []


def test_dangling_pointer_clears_once_skills_exist(default_projects, mappings, tmp_path):
    project = tmp_path / "gemini"
    shutil.copytree(default_projects["Gemini"], project)
    table = (project / ".gemini" / "rules" / "use-lazy-rules.md").read_text(encoding="utf-8")
    skills = cb._lazy_table_skills(table)
    assert len(skills) == LAZY_TABLE_SKILLS
    for skill in skills:
        target = project / ".gemini" / "skills" / skill
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    assert _run(cb.check_dangling_pointer, project, "Gemini", mappings) == []


def test_checks_never_raise_error_severity(default_projects, mappings):
    assert set(cb.PHASE0_SEVERITY) == set(cb.SPEC_SEVERITY)
    assert all(level is Severity.WARNING for level in cb.PHASE0_SEVERITY.values())
    for check in ALL_CHECKS:
        for provider, project in default_projects.items():
            for finding in _run(check, project, provider, mappings):
                assert finding.severity in (Severity.WARNING, Severity.INFO)


def test_severity_comes_from_central_table(monkeypatch):
    monkeypatch.setitem(cb.PHASE0_SEVERITY, "context.over-hard-cap", Severity.ERROR)
    assert cb._warn("context.over-hard-cap", "f", "m").severity is Severity.ERROR
    assert cb.SPEC_SEVERITY["context-profile.marker-in-rule"] is Severity.ERROR


# --- synthetic projects: rule of each check --------------------------------

def _caps(**overrides) -> dict:
    caps = {"context_file": "ENTRY.md", "has_rules": True, "rules_dir": "rules"}
    caps.update(overrides)
    return {"P": caps}


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_hard_cap_boundary(tmp_path):
    _write(tmp_path / "ENTRY.md", "x" * 100)
    caps = _caps(context_hard_cap_bytes=101)
    assert cb.check_over_hard_cap(tmp_path, ["P"], caps, None) == []
    caps = _caps(context_hard_cap_bytes=100)
    findings = cb.check_over_hard_cap(tmp_path, ["P"], caps, None)
    assert [f.check for f in findings] == ["context.over-hard-cap"]
    assert findings[0].severity is Severity.WARNING


def test_soft_cap_bytes_chars_lines(tmp_path):
    _write(tmp_path / "ENTRY.md", "äö\n" * 10)  # 30 chars, 50 bytes, 10 lines
    assert cb.check_over_soft_cap(tmp_path, ["P"], _caps(context_soft_cap_bytes=50), None) == []
    assert len(cb.check_over_soft_cap(tmp_path, ["P"], _caps(context_soft_cap_bytes=49), None)) == 1
    # 50 bytes > cap 30, but 30 chars <= cap -> the file is read and no finding results
    assert cb.check_over_soft_cap(tmp_path, ["P"], _caps(context_soft_cap_chars=30), None) == []
    assert len(cb.check_over_soft_cap(tmp_path, ["P"], _caps(context_soft_cap_chars=29), None)) == 1
    assert cb.check_over_soft_cap(tmp_path, ["P"], _caps(context_soft_cap_lines=10), None) == []
    assert len(cb.check_over_soft_cap(tmp_path, ["P"], _caps(context_soft_cap_lines=9), None)) == 1


def test_caps_absent_means_no_finding(tmp_path):
    _write(tmp_path / "ENTRY.md", "x" * 1000)
    assert cb.check_over_hard_cap(tmp_path, ["P"], _caps(), None) == []
    assert cb.check_over_soft_cap(tmp_path, ["P"], _caps(), None) == []


def test_marker_in_rule_source_and_generated(tmp_path):
    _write(tmp_path / "rules" / "a.md", "# A\n{{#if CONTEXT_PROFILE_COMPACT}}x\n")
    _write(tmp_path / "rules" / "b.md", "# B\nclean\n")
    findings = cb.check_marker_in_rule(tmp_path, ["P"], _caps(), None)
    assert [f.file for f in findings] == ["rules/a.md"]
    assert findings[0].check == "context-profile.marker-in-rule"


def test_unread_channel_skills_dir_and_exemption(tmp_path, monkeypatch):
    _write(tmp_path / "rules" / "a.md", "# A\n")
    _write(tmp_path / "sk" / "x" / "SKILL.md", "# x\n")
    caps = _caps(rules_read_channels=[], skills_dir="sk", skills_discovery_dirs=["other"])
    findings = cb.check_unread_channel(tmp_path, ["P"], caps, None)
    assert sorted(f.file for f in findings) == ["rules", "sk"]
    monkeypatch.setattr(cb, "_intentional_unread", lambda: ["rules", "sk"])
    assert cb.check_unread_channel(tmp_path, ["P"], caps, None) == []


def test_rule_reachable_via_skills_channel(tmp_path):
    _write(tmp_path / "ENTRY.md", "# entry\n")
    _write(tmp_path / "rules" / "a.md", "# A\n")
    caps = _caps(rules_read_channels=["embedded", "skills"], skills_dir="sk")
    assert len(cb.check_rule_unreachable(tmp_path, ["P"], caps, None)) == 1
    _write(tmp_path / "sk" / "a" / "SKILL.md", "# A\n")
    assert cb.check_rule_unreachable(tmp_path, ["P"], caps, None) == []


def test_module_has_no_provider_literal_and_stays_small():
    source = (REPO_ROOT / "scripts" / "lib" / "consistency" / "context_budget.py").read_text(encoding="utf-8")
    assert len(source.splitlines()) <= 600
    assert not re.search(r"\bprovider\w*\s*(==|!=|in)\s*[\(\[\"']", source)
    registered = yaml.safe_load((REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))["providers"]
    for name in registered:
        assert not re.search(r"[\"']%s[\"']" % re.escape(name), source), name


def test_first_heading_edge_cases():
    assert cb._first_heading("---\nname: x\n---\n\n# Title\nbody\n") == "# Title"
    assert cb._first_heading("plain first line\nsecond\n") == "plain first line"
    assert cb._first_heading("") == ""
    assert cb._normalize_heading("## Title ") == "Title"


def test_duplicate_heading_does_not_mask_unembedded_rule(tmp_path):
    _write(tmp_path / "ENTRY.md", "# Shared\nbody of rule a\n")
    _write(tmp_path / "rules" / "a.md", "# Shared\nbody of rule a\n")
    _write(tmp_path / "rules" / "b.md", "# Shared\nbody of rule b\n")
    findings = cb.check_rule_unreachable(tmp_path, ["P"], _caps(rules_read_channels=[]), None)
    assert [Path(f.file).stem for f in findings] == ["b"]


def test_intentional_unread_accepts_dict_entries(monkeypatch):
    monkeypatch.setattr(cb, "_load_anchor_list", lambda key: [{"glob": "a/*", "reason": "r"}, "b", {"x": 1}])
    assert cb._intentional_unread() == ["a/*", "b"]


# --- IC-33: declared-surface-empty / legacy-artifact-present (AC-67) --------

def _empty_surface_caps(**overrides) -> dict:
    return _caps(skills_dir="sk", commands_dir="cmd", settings_file="set.json",
                 **{"mcp-config": {"committed-file": "mcp.json"}}, **overrides)


def test_surface_target_key_mapping():
    assert cb.surface_target_key("skills") == "skills_dir"
    assert cb.surface_target_key("commands") == "commands_dir"
    assert cb.surface_target_key("mcp") == "mcp-config.committed-file"
    assert cb.surface_target_key("settings") == "settings_file"
    for surface in ("agents", "rules", "context_file", "workspace_agents_autoload", ""):
        assert cb.surface_target_key(surface) is None


def test_declared_surface_empty_reports_all_four_surfaces(tmp_path):
    findings = cb.check_declared_surface_empty(tmp_path, ["P"], _empty_surface_caps(), None)
    assert {f.file for f in findings} == {"sk", "cmd", "set.json", "mcp.json"}
    assert {f.check for f in findings} == {"context.declared-surface-empty"}
    assert all(f.severity is Severity.WARNING and f.message.startswith("P: ") for f in findings)
    assert cb.SPEC_SEVERITY["context.declared-surface-empty"] is Severity.ERROR


def test_declared_surface_empty_clears_with_artifacts(tmp_path):
    _write(tmp_path / "sk" / "x" / "SKILL.md", "# x\n")
    _write(tmp_path / "cmd" / "c.md", "# c\n")
    _write(tmp_path / "set.json", "{}")
    _write(tmp_path / "mcp.json", "{}")
    assert cb.check_declared_surface_empty(tmp_path, ["P"], _empty_surface_caps(), None) == []


def test_declared_surface_empty_negative_cases(tmp_path):
    (tmp_path / "sk").mkdir()  # directory without SKILL.md still counts as empty
    (tmp_path / "cmd").mkdir()
    caps = _caps(skills_dir="sk", commands_dir="cmd")
    assert {f.file for f in cb.check_declared_surface_empty(tmp_path, ["P"], caps, None)} == {"sk", "cmd"}
    # no target key declared -> nothing declared; inactive provider -> not checked
    assert cb.check_declared_surface_empty(tmp_path, ["P"], _caps(skills_dir=None, commands_dir=""), None) == []
    assert cb.check_declared_surface_empty(tmp_path, [], caps, None) == []


def test_declared_surface_empty_intentional_empty_suppresses(tmp_path, monkeypatch):
    entries = [{"provider_capability": "skills", "reason": "r"},
               {"provider_capability": "commands", "reason": ""},  # reason is mandatory
               {"provider_capability": "mcp"}, "settings"]
    monkeypatch.setattr(cb, "_load_anchor_list",
                        lambda key: entries if key == "intentional_empty" else [])
    findings = cb.check_declared_surface_empty(tmp_path, ["P"], _empty_surface_caps(), None)
    assert {f.file for f in findings} == {"cmd", "set.json", "mcp.json"}


def test_legacy_artifact_present(tmp_path):
    caps = _caps(legacy_artifacts=[".old/settings.json", "gone.txt"])
    assert cb.check_legacy_artifact_present(tmp_path, ["P"], caps, None) == []
    _write(tmp_path / ".old" / "settings.json", "{}")
    (finding,) = cb.check_legacy_artifact_present(tmp_path, ["P"], caps, None)
    assert finding.check == "context.legacy-artifact-present"
    assert finding.file == ".old/settings.json" and finding.severity is Severity.WARNING
    assert cb.SPEC_SEVERITY["context.legacy-artifact-present"] is Severity.WARNING
    assert cb.check_legacy_artifact_present(tmp_path, [], caps, None) == []
    assert cb.check_legacy_artifact_present(tmp_path, ["P"], _caps(), None) == []


def test_legacy_artifact_real_mammouth_capability(tmp_path, mappings):
    _write(tmp_path / ".mammouth" / "settings.json", "{}")
    findings = cb.check_legacy_artifact_present(tmp_path, ["Mammouth"], mappings, None)
    assert [f.file for f in findings] == [".mammouth/settings.json"]


@pytest.mark.parametrize("provider", ["Codex", "Mammouth", "Continue"])
def test_ac67_matrix_reports_missing_skills(provider, mappings, tmp_path):
    # AC-67: declared but empty skills directories of Codex/Mammouth/Continue
    # (no skills are generated for them, see the module docstring)
    findings = cb.check_declared_surface_empty(tmp_path, [provider], mappings, None)
    assert mappings[provider]["skills_dir"] in {f.file for f in findings}


def test_ac67_matrix_codex_real_sync(default_projects, mappings):
    findings = _run(cb.check_declared_surface_empty, default_projects["Codex"], "Codex", mappings)
    assert ".agents/skills" in {f.file for f in findings}
    assert _run(cb.check_legacy_artifact_present, default_projects["Codex"], "Codex", mappings) == []
