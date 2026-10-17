"""IC-19 active-set reference checks (Task 0b.3, AC-43)."""
import sys
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

from lib.active_set import compute_active_set  # noqa: E402
from lib.consistency import active_set_refs as asr  # noqa: E402
from lib.consistency.report import Severity  # noqa: E402
from tests.active_set_render import sync_configs_parallel, synced_project  # noqa: E402

_FIX = Path(__file__).resolve().parent / "fixtures" / "active-set"
_AC43_ROLES = ("senior-developer", "validator", "bug-feature-analyzer",
               "concept-specifier", "concept-reviewer", "ideation")
_PROVIDERS = ["Claude"]


@pytest.fixture(scope="module")
def synced(tmp_path_factory):
    """A fixture project synced once per session (shared, read-only)."""
    def _get(name):
        config = yaml.safe_load(
            (_FIX / name / ".meta-config" / "project.yaml").read_text(encoding="utf-8"))
        project = synced_project(tmp_path_factory, config)
        return project, compute_active_set(config, _ROOT, project)

    return _get


def test_p10_dangling_dispatch_covers_ac43_roles(synced):
    project, active = synced("p10")
    findings = asr.check_dangling_dispatch(project, _PROVIDERS, {}, active)
    # IC-18 no. 2 (pipeline drop) removed the pipeline dispatches of bug-feature-analyzer,
    # ideation and validator; IC-18 no. 5 (tier chain) the senior-developer and concept
    # dispatches; IC-18 no. 11 / IC-30 triage (Task 1.19) the documenter route to
    # knowledge-ingestor. The AC-43 roles are still inactive on p10 -- nothing dispatches them.
    assert set(_AC43_ROLES) <= set(active.known_roles) - set(active.roles)
    assert findings == []


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


def test_dangling_dispatch_is_error_level(synced, tmp_path):
    # Task 1.20 (AC-49): the check is ERROR from phase 1 on; mentions stay INFO.
    _, active = synced("p10")
    proj = _scratch(tmp_path, "Delegiere an `validator`.\nsee `validator`\n")
    found = asr.check_dangling_dispatch(proj, _PROVIDERS, {}, active)
    assert [(f.check, f.severity) for f in found] == [
        ("active-set.dangling-dispatch", Severity.ERROR)]
    assert all(f.severity == Severity.INFO
               for f in asr.check_dangling_mention(proj, _PROVIDERS, {}, active))


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
    assert sorted((f.check, f.severity.value) for f in found) == [
        ("active-set.dangling-dispatch", Severity.ERROR.value),
        ("active-set.invalid-dispatch-phrase", Severity.WARNING.value)]


# --- Task 1.20 (AC-49): scan scope and fixture matrix x provider matrix --------

@pytest.mark.parametrize("rel", [
    ".claude/commands/x.md", ".claude/rules/x.md", ".claude/pipeline-details/x.md"])
def test_commands_rules_and_pipeline_details_are_scanned(synced, tmp_path, rel):
    _, active = synced("p10")
    target = tmp_path / rel
    target.parent.mkdir(parents=True)
    target.write_text("Delegiere an `validator`.\n", encoding="utf-8")
    found = asr.check_dangling_dispatch(tmp_path, _PROVIDERS, {}, active)
    assert [(f.file, f.severity) for f in found] == [(rel, Severity.ERROR)]


_PROVIDER_CFG = yaml.safe_load(
    (_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))["providers"]
_MATRIX_PROVIDERS = sorted(_PROVIDER_CFG)
_CAPS = yaml.safe_load(
    (_ROOT / "config" / "provider-capabilities.yaml").read_text(encoding="utf-8"))["capabilities"]

# Readers that truncate the shared ``AGENTS.md`` through a hard cap (AC-13).
# A fixture without a ``roles:`` allowlist renders every gate-enabled role,
# which grows that shared context past the strictest cap; its sync then aborts
# by design with ``context.over-hard-cap`` (Task 1.25; asserted in
# ``tests/test_dispatch_depth_and_hard_cap.py``). Such fixtures are synced over
# the uncapped providers only, so the hard-cap providers contribute no
# artifacts for them: their reference coverage comes solely from the
# allowlisted fixtures (p10/p20), not from pall/ha. The shared ``AGENTS.md``
# the all-roles fixtures do produce is still scanned once through the uncapped
# readers, so that content is covered — but not per hard-cap provider.
_SHARED_CONTEXT_HARD_CAP = {
    p for p in _MATRIX_PROVIDERS
    if _PROVIDER_CFG[p].get("context_file") == "AGENTS.md"
    and _CAPS.get(p, {}).get("context_hard_cap_bytes")}
_UNCAPPED_PROVIDERS = [p for p in _MATRIX_PROVIDERS if p not in _SHARED_CONTEXT_HARD_CAP]

# AC-49: mentions outside mention_allow must be 0 for these generated artifacts.
_MENTION_ZERO_PARTS = ("orchestrator", "pipeline-details", "commands", "prompts")


@pytest.fixture(scope="module")
def matrix(tmp_path_factory):
    """Each AC-49 fixture synced once with every registered provider (concurrently).

    All-roles fixtures (no ``roles:`` key: ``pall``, ``ha``) exceed a
    shared-context hard cap, so they are synced over ``_UNCAPPED_PROVIDERS``
    instead (see ``_SHARED_CONTEXT_HARD_CAP``); the allowlisted fixtures keep
    the full matrix.
    """
    names = ("p10", "p20", "pall", "ha")
    configs = {name: yaml.safe_load(
        (_FIX / name / ".meta-config" / "project.yaml").read_text(encoding="utf-8"))
        for name in names}
    root = tmp_path_factory.mktemp("matrix")
    allowlisted = {name: cfg for name, cfg in configs.items() if "roles" in cfg}
    all_roles = {name: cfg for name, cfg in configs.items() if "roles" not in cfg}
    projects = sync_configs_parallel(root, allowlisted, providers=_MATRIX_PROVIDERS)
    projects.update(sync_configs_parallel(root, all_roles, providers=_UNCAPPED_PROVIDERS))
    return {name: (projects[name], compute_active_set(configs[name], _ROOT, projects[name]))
            for name in names}


@pytest.mark.parametrize("name", ["p10", "p20", "pall", "ha"])
def test_ac49_no_dangling_dispatch_over_provider_matrix(matrix, name):
    project, active = matrix[name]
    found = asr.check_dangling_dispatch(project, _MATRIX_PROVIDERS, {}, active)
    assert found == [], "\n".join(f"{f.file}: {f.message}" for f in found)


@pytest.mark.parametrize("name", ["p10", "p20", "pall", "ha"])
def test_ac49_no_dangling_mention_in_orchestrator_pipelines_commands(matrix, name):
    project, active = matrix[name]
    found = [f for f in asr.check_dangling_mention(project, _MATRIX_PROVIDERS, {}, active)
             if any(part in f.file for part in _MENTION_ZERO_PARTS)]
    assert found == [], "\n".join(f"{f.file}: {f.message}" for f in found)


def test_unmanaged_user_command_is_not_scanned(synced, tmp_path):
    # Review fix: with a managed index present only sync-managed files are scanned,
    # so a user's own command can never make --doctor fail.
    _, active = synced("p10")
    commands = tmp_path / ".claude" / "commands"
    commands.mkdir(parents=True)
    (commands / "mine.md").write_text("Delegiere an `validator`.\n", encoding="utf-8")
    (commands / "managed.md").write_text("Delegiere an `validator`.\n", encoding="utf-8")
    (commands / ".agent-meta-managed").write_text("managed.md\n", encoding="utf-8")
    found = asr.check_dangling_dispatch(tmp_path, _PROVIDERS, {}, active)
    assert [f.file for f in found] == [".claude/commands/managed.md"]
