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
    _SYNC + " --doctor",
    _SYNC + " --doctor --json",
    _SYNC + " --doctor --json --strict",
    _SYNC + " --doctor --json --provider <P>",
    _SYNC + " --doctor --json --out " + _SINK + "/doctor/<YYYYMMDD-HHMMSS>.json",
    _SYNC + " --check --dry-run",
    _SYNC + " --context-report --json",
    _SYNC + " --cleanup-preview",
    "git status",
    "git log",
    "git diff",
]


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


def test_allowlist_has_no_redirection_or_output_flags():
    for line in _allowlist_block():
        bare = re.sub(r"<[A-Za-z_-]+>", "", line)  # drop <P>/<YYYYMMDD-HHMMSS> placeholders
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
    assert "not strictly read-only" in body
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
