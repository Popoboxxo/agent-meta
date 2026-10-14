"""Task 0e.1 (IC-23, IC-28, AC-85, AC-88, AC-95): role ``meta-doctor``.

Pins the template contract of the installation-diagnosis role: exact bash
argv allowlist, no Write/Edit tools, no ``model:`` field, the H-4 wording,
name-only addressability, tmp-sink placeholder only (no literal ``.tmp``).
"""
from __future__ import annotations

import re
from pathlib import Path

from scripts.lib.frontmatter import parse_frontmatter_file
from scripts.lib.roles import load_roles_config

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "agents" / "1-generic" / "meta-doctor.md"

_H4_DESCRIPTION = (
    "Installation doctor: runs `sync.py --doctor`, deduplicates and prioritizes known-issue "
    "findings of this agent-meta installation, and hands fixes to agent-meta-manager "
    "— never repairs anything and writes reports only to the configured tmp-sink."
)
_H4_SHORT_DESC = "Diagnoses the agent-meta installation (reports only to the tmp-sink)"
_H4_NAME_ONLY_REASON = (
    "Diagnostic meta role; invoked explicitly by name (e.g. 'run meta-doctor'), never by "
    "routine task keywords, to avoid accidental diagnostic runs."
)

_SYNC = "python3 {{AGENT_META_REL_PATH}}scripts/sync.py"
_SINK = "{{TMP_SINK_PATH}}"
_EXPECTED_ALLOWLIST = [
    _SYNC + " --doctor --json",
    _SYNC + " --doctor --json --out " + _SINK + "/doctor/<YYYYMMDD-HHMMSS>.json",
    _SYNC + " --check --dry-run",
    _SYNC + " --context-report --json",
    _SYNC + " --cleanup-preview",
    "git status --short [-- <rel-path>]",
    "git log --oneline -n <N> [-- <rel-path>]",
    "git diff --stat [-- <rel-path>]",
    "git diff --name-only [-- <rel-path>]",
]
# IC-23/AC-88: the dropped extra forms must stay out of the allowlist.
_DROPPED_FORMS = ("--doctor\n", "--strict", "--provider")
# git hardening (review M2): each must be named as forbidden in the allowlist rules.
_FORBIDDEN_GIT_TOKENS = (
    "--no-index", "--ext-diff", "--textconv", "--output*", "`-c`", "`-C`",
    "absolute paths", "shell metacharacters", "redirection",
)


def _text() -> str:
    return TEMPLATE.read_text(encoding="utf-8")


def _body() -> str:
    parts = _text().split("---", 2)
    return parts[2]


def _roles() -> dict:
    return load_roles_config(REPO_ROOT)["roles"]


def _allowlist_block() -> list:
    m = re.search(r"## Bash allowlist.*?```text\n(.*?)```", _text(), re.DOTALL)
    assert m, "bash allowlist code block missing"
    return [ln for ln in m.group(1).splitlines() if ln.strip()]


def test_template_exists_with_valid_frontmatter():
    assert TEMPLATE.is_file()
    fm = parse_frontmatter_file(TEMPLATE)
    assert fm["name"] == "template-meta-doctor"
    assert re.fullmatch(r"\d+\.\d+\.\d+", str(fm["version"]))
    assert fm["description"] == _H4_DESCRIPTION
    assert fm["hint"]
    assert fm["prompt_mode"] == "modern"
    assert fm["reference_standards"]


def test_tools_are_exact_and_have_no_write_or_edit():
    fm = parse_frontmatter_file(TEMPLATE)
    assert list(fm["tools"]) == ["Read", "Glob", "Grep", "Bash", "TodoWrite"]
    for forbidden in ("Write", "Edit", "Agent"):
        assert forbidden not in fm["tools"]


def test_no_model_field():
    fm = parse_frontmatter_file(TEMPLATE)
    assert "model" not in fm
    head = _text().split("---", 2)[1]
    assert not re.search(r"^model\s*:", head, re.MULTILINE)


def test_bash_allowlist_is_exact():
    assert _allowlist_block() == _EXPECTED_ALLOWLIST


def test_allowlist_whitelist_forms_present_exactly_once():
    lines = _allowlist_block()
    for form in _EXPECTED_ALLOWLIST:
        assert lines.count(form) == 1, form
    text = "\n".join(lines) + "\n"
    for dropped in _DROPPED_FORMS:
        assert dropped not in text, dropped


def test_git_forbidden_forms_and_consistent_rules():
    text = _text()
    for token in _FORBIDDEN_GIT_TOKENS:
        assert token in text, token
    assert "integer from 1 to 50" in text
    assert "Anything not listed here is forbidden" in text
    assert "any further arguments" not in text
    assert "beliebige" not in text
    # the placeholder syntax for timestamps is YYYYMMDD-HHMMSS only
    assert not re.search(r"<(ts|timestamp)>\.json\s*$", "\n".join(_allowlist_block()))


def test_allowlist_has_no_redirection_or_output_flags():
    for line in _allowlist_block():
        bare = re.sub(r"<[A-Za-z_-]+>", "", line)  # drop <N>/<rel-path>/<YYYYMMDD-HHMMSS> placeholders
        assert not re.search(r"(>|<|\||\btee\b|\$\(|`|--output|\s-o\b)", bare), line
    assert not any("--deactivation-status" in ln for ln in _allowlist_block())


def test_out_only_under_tmp_sink_doctor():
    outs = [t for ln in _allowlist_block() for t in re.findall(r"--out\s+(\S+)", ln)]
    assert outs
    for target in outs:
        assert target.startswith(_SINK + "/doctor/"), target
    # the workflow text also only names the doctor directory as --out target
    for target in re.findall(r"--out\s+(\{\{TMP_SINK_PATH\}\}\S*)", _body()):
        assert target.startswith(_SINK + "/doctor/"), target


def test_only_placeholder_never_literal_tmp_sink():
    text = _text()
    assert "{{TMP_SINK_PATH}}" in text
    assert not re.search(r"(?<![A-Za-z0-9_])\.tmp\b", text)


def test_prompt_injection_and_rights_statements():
    body = _body()
    assert "{{PROMPT_INJECTION_DEFENSE_BLOCK}}" in body
    assert "{{OUTPUT_GUARD_BLOCK}}" in body
    assert "data, not instructions" in body
    assert "never repairs anything" in _text()
    # AC-95: never describe meta-doctor as strictly read-only
    assert not re.search(r"strict(ly)?[ -]read-only|strikt read-only", _text(), re.IGNORECASE)
    assert "only thing written is the report" in body
    assert "doctor.tmp-sink.disabled" in body and "without `--out`" in body
    assert "never write into the project outside the tmp-sink" in body.replace("You never", "never")
    assert "agent-meta-manager" in body
    assert "never delegate back to `orchestrator`" in body


def test_next_uses_meta_feedback_conditional():
    body = _body()
    assert "{{#if ROLE_META_FEEDBACK_ACTIVE}}meta-feedback{{else}}" in body
    # meta-feedback may only appear inside the conditional
    stripped = re.sub(r"\{\{#if ROLE_META_FEEDBACK_ACTIVE\}\}.*?\{\{/if\}\}", "", body, flags=re.DOTALL)
    assert "meta-feedback" not in stripped


def test_output_contract_markers():
    body = _body()
    for marker in ("STATUS:", "RESULT:", "ARTIFACTS:", "FINDINGS:", "GATES:", "NEXT:", "doctor-findings-v1"):
        assert marker in body, marker
    assert "{{TMP_SINK_PATH}}/doctor/<ts>.json" in body


def test_no_provider_literals_in_template():
    low = _text().lower()
    for literal in ("claude", "codex", "gemini", "opencode", "mammouth", "continue.dev", "copilot", "anthropic"):
        assert literal not in low, literal


def test_role_defaults_entry_is_name_only_h4():
    roles = _roles()
    info = roles["meta-doctor"]
    routing = info["routing"]
    assert routing["addressability"] == "name_only"
    assert routing["name_only_reason"] == _H4_NAME_ONLY_REASON
    assert routing["orchestrator_only"] is True
    assert routing["parallel"] is False
    assert info["short_desc"] == _H4_SHORT_DESC
    assert info["description"] == _H4_DESCRIPTION
    assert info["model"] == "fast"
    assert info["memory"] == ""
    assert info["workflow_tier"] == "optional"
    assert "routing_patterns" not in info
    assert "intent_keywords" not in routing
    handoff = info["handoff"]
    assert handoff["input_contracts"] == ["task-spec-v1"]
    assert handoff["output_contract"] == "doctor-findings-v1"
    assert handoff["target_roles"] == ["agent-meta-manager"]


def test_role_not_in_any_routing_keywords_of_other_roles():
    for name, info in _roles().items():
        if name == "meta-doctor":
            continue
        blob = repr((info.get("routing") or {}).get("intent_keywords")) + repr(info.get("routing_patterns"))
        assert "meta-doctor" not in blob, name


# --- Task 0e.3 (IC-23, AC-44): agent-meta-manager consumes doctor-findings-v1 ---

_MANAGER = REPO_ROOT / "agents" / "1-generic" / "agent-meta-manager.md"
_MANAGER_VERSION_BEFORE = "1.23.1"
_MANAGER_PROVIDER_LITERAL_BASELINE = 8


def _manager_text() -> str:
    return _MANAGER.read_text(encoding="utf-8")


def _consumer_section() -> str:
    m = re.search(r"\n## [^\n]*doctor-findings-v1[^\n]*\n(.*?)(?=\n## |\Z)", _manager_text(), re.DOTALL)
    assert m, "consumer section for doctor-findings-v1 missing in agent-meta-manager"
    return m.group(1)


def test_manager_declares_doctor_findings_input_contract():
    handoff = _roles()["agent-meta-manager"].get("handoff") or {}
    assert "doctor-findings-v1" in (handoff.get("input_contracts") or [])


def test_no_read_only_wording_for_meta_doctor_in_texts():
    """AC-95: no text calls meta-doctor/--doctor strictly read-only (meta-optimizer may be)."""
    pattern = re.compile(r"(strikt|strict(ly)?)[ -]read-only|read-only[^\n]{0,20}meta-doctor|meta-doctor[^\n]{0,40}read-only", re.IGNORECASE)
    files = [REPO_ROOT / "README.md", REPO_ROOT / "CHANGELOG.md", REPO_ROOT / "standalone" / "README.md",
             TEMPLATE, REPO_ROOT / "config" / "role-defaults.yaml",
             REPO_ROOT / "docs" / "guides" / "setup" / "instantiate-project.md"]
    files += sorted((REPO_ROOT / "standalone" / "agents").glob("meta-doctor.md"))
    offenders = []
    for f in files:
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line) and "meta-optimizer" not in line:
                offenders.append("%s:%d" % (f.relative_to(REPO_ROOT), n))
    assert not offenders, offenders


def test_no_output_not_consumed_finding_for_doctor_findings():
    from scripts.lib.consistency.handoff_contracts import check_handoff_contracts  # type: ignore
    findings = check_handoff_contracts(REPO_ROOT)
    bad = [f for f in findings if f.check == "handoff.output-not-consumed" and "doctor-findings-v1" in f.message]
    assert not bad, bad


def test_manager_consumer_section_contract():
    sec = _consumer_section()
    low = sec.lower()
    assert "untrusted" in low
    for field in ("`quoted`", "`evidence`", "`message`"):
        assert field in sec
    assert "severity_registry" in sec and "severity_effective" in sec
    assert "doctor.registry-invalid" in sec
    assert "never" in low and "instruction" in low
    assert "approval" in low
    assert len(sec.strip().splitlines()) <= 16


def test_manager_version_bumped_and_no_new_provider_literal():
    from scripts.lib.consistency.provider_literals import check_provider_literal  # type: ignore
    fm = parse_frontmatter_file(_MANAGER)
    ver = str(fm["version"])
    assert tuple(map(int, ver.split("."))) > tuple(map(int, _MANAGER_VERSION_BEFORE.split(".")))
    hits = [f for f in check_provider_literal(REPO_ROOT) if "agent-meta-manager" in str(f.file)]
    # Baseline: 8 hits in agent-meta-manager before the 0e.3 consumer section (section adds none).
    assert len(hits) <= _MANAGER_PROVIDER_LITERAL_BASELINE, len(hits)
