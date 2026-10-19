"""Task 27 / 2e.1 (IC-26, IC-27, AC-79, AC-59, AC-91): role ``meta-optimizer``.

Pins the read-only proposal role: exactly ``Read, Glob, Grep, TodoWrite``, no
``model:`` field, no write/execute/apply instruction of its own (the executing
step belongs to ``agent-meta-manager``), the H-4 wording, name-only
addressability, the IC-26 output-contract markers, the mandatory
"not applicable" labeling and the verbatim-warning rule.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from scripts.lib.frontmatter import parse_frontmatter_file
from scripts.lib.roles import load_roles_config
from scripts.lib.standalone import _CONDITIONAL_FALSE_FLAGS

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "agents" / "1-generic" / "meta-optimizer.md"

_H4_DESCRIPTION = (
    "Read-only config optimizer: reads a `sync.py --optimize-config` proposal and "
    "presents token-compact, evidence-backed variants of the project config with "
    "mandatory warnings — never edits or applies anything."
)
_H4_SHORT_DESC = "Proposes compact project-config variants (proposal only)"
_H4_NAME_ONLY_REASON = (
    "Config optimization meta role; produces proposals only and is invoked "
    "explicitly by name, never by routine task keywords."
)
_NOT_APPLICABLE = "nicht anwendbar — manuelle Nutzeränderung bzw. Framework-Issue"
_EXPECTED_TOOLS = ["Read", "Glob", "Grep", "TodoWrite"]


def _text() -> str:
    return TEMPLATE.read_text(encoding="utf-8")


def _body() -> str:
    return _text().split("---", 2)[2]


def _roles() -> dict:
    return load_roles_config(REPO_ROOT)["roles"]


def test_template_exists_with_valid_frontmatter():
    assert TEMPLATE.is_file()
    fm = parse_frontmatter_file(TEMPLATE)
    assert fm["name"] == "template-meta-optimizer"
    assert fm["version"] == "1.0.0"
    assert fm["prompt_mode"] == "modern"
    assert fm["description"] == _H4_DESCRIPTION
    assert fm["hint"] == _H4_SHORT_DESC
    assert fm["reference_standards"] == ["Clean Code: separation of concerns"]


def test_tools_are_exact_and_have_no_write_execute_or_agent():
    fm = parse_frontmatter_file(TEMPLATE)
    assert list(fm["tools"]) == _EXPECTED_TOOLS
    for forbidden in ("Bash", "Write", "Edit", "Agent"):
        assert forbidden not in fm["tools"], forbidden


def test_no_model_field():
    fm = parse_frontmatter_file(TEMPLATE)
    assert "model" not in fm
    head = _text().split("---", 2)[1]
    assert not re.search(r"^model\s*:", head, re.MULTILINE)


def test_required_placeholders_and_extension_pointer():
    text = _text()
    body = _body()
    assert (
        "> **Extension:** If `{{EXTENSION_DIR}}/{{PREFIX}}-meta-optimizer-ext.md` "
        "exists → read and apply immediately."
    ) in text
    for placeholder in (
        "{{PROJECT_CONTEXT}}",
        "{{PROJECT_GOAL}}",
        "{{PROMPT_INJECTION_DEFENSE_BLOCK}}",
        "{{OUTPUT_GUARD_BLOCK}}",
    ):
        assert placeholder in body, placeholder


def test_output_contract_markers():
    body = _body()
    for marker in (
        "STATUS:",
        "RESULT:",
        "ARTIFACTS: none",
        "PROPOSALS:",
        "PROOF:",
        "NEXT:",
        "config-patch-proposal-v1",
    ):
        assert marker in body, marker
    # IC-26: PROOF reports level, byte-equality, roundtrip and the scope note.
    for proof_field in ("level_reached", "byte_equal_files/files_compared",
                        "roundtrip ok/nok", "scope_note"):
        assert proof_field in body, proof_field
    # AC-91: the PROPOSALS contract block carries the exact German hint label,
    # not an English "not applicable — manuelle …" variant an LLM might emit.
    contract = re.search(r"```\n(STATUS:.*?)```", body, re.DOTALL)
    assert contract, "output-contract fenced block missing"
    block = contract.group(1)
    assert "PROPOSALS:" in block
    assert _NOT_APPLICABLE in block
    assert "not applicable — manuelle" not in block


def test_no_write_or_execute_instruction_of_its_own():
    text = _text()
    body = _body()
    low = text.lower()
    assert "```bash" not in text and "```sh" not in text
    assert "bash allowlist" not in low
    assert "no write or edit tools" in low
    assert "strictly read-only" in low
    assert "you never edit" in low and "you never apply" in low
    assert "you execute nothing" in low or "executes nothing" in low
    # No tool-use instruction that would grant this role a writer/executor.
    assert not re.search(r"\b(use|using) the (write|edit)\b", low)
    # Every execution/apply mention in the body is scoped to agent-meta-manager.
    for line in body.splitlines():
        if ("sync.py --" in line or "--dry-run" in line
                or "--apply-config-patch" in line or "--preview" in line):
            assert "agent-meta-manager" in line, line


def test_hint_labeling_and_verbatim_warnings():
    text = _text()
    body = _body()
    assert _NOT_APPLICABLE in text
    assert "NON-DETERMINISTIC" in body
    assert "applicable: false" in body
    assert re.search(r"only candidates with `?applicable: true`?", body, re.IGNORECASE)
    assert "approval list" in body.lower()
    # Hint candidates keep their ID for reference; own proposals carry no OPT-ID.
    assert "keep their id only for reference" in body.lower()
    assert "no opt-id" in body.lower()
    # warnings are taken verbatim from Candidate.warnings
    assert "wörtlich" in body
    # variable-removal note (IC-26 step 5)
    assert "Bei späterer Reaktivierung" in body


def test_credential_statement():
    text = _text()
    low = text.lower()
    assert "never quote credential values" in low
    assert "credential keys" in low
    # credential keys must not appear even as hints
    assert "even as hints" in low


def test_proposal_content_is_data_not_instructions():
    body = _body()
    assert "data, not instructions" in body


def test_role_defaults_entry_is_name_only_h4():
    info = _roles()["meta-optimizer"]
    assert info["model"] == "balanced"
    assert info["memory"] == ""
    assert info["workflow_tier"] == "optional"
    assert info["description"] == _H4_DESCRIPTION
    assert info["short_desc"] == _H4_SHORT_DESC

    routing = info["routing"]
    assert routing["addressability"] == "name_only"
    assert routing["name_only_reason"] == _H4_NAME_ONLY_REASON
    assert routing["orchestrator_only"] is True
    assert routing["parallel"] is False
    assert "routing_patterns" not in info
    assert "intent_keywords" not in routing

    handoff = info["handoff"]
    assert handoff["input_contracts"] == ["task-spec-v1"]
    assert handoff["output_contract"] == "config-patch-proposal-v1"
    assert handoff["target_roles"] == ["agent-meta-manager"]


def test_standalone_conditionals_are_registered():
    """A-F-2: every {{#if VAR}}/{{#unless VAR}} must be a literal standalone flag."""
    found = re.findall(r"\{\{#(?:if|unless)\s+([A-Z0-9_]+)", _text())
    missing = [var for var in found if var not in _CONDITIONAL_FALSE_FLAGS]
    assert not missing, f"unregistered standalone conditional flags: {missing}"


def test_role_not_in_any_routing_keywords_of_other_roles():
    for name, info in _roles().items():
        if name == "meta-optimizer":
            continue
        blob = repr(info.get("routing_patterns")) + repr(
            (info.get("routing") or {}).get("intent_keywords")
        )
        assert "meta-optimizer" not in blob, name


def test_no_provider_literals_in_template():
    low = _text().lower()
    for literal in (
        "claude", "codex", "gemini", "opencode", "mammouth", "continue.dev",
        "copilot", "anthropic",
    ):
        assert literal not in low, literal


# --- Task 29 / 2e.3 (IC-27, AC-59 Consumer): agent-meta-manager consumes config-patch-proposal-v1 ---


def test_manager_declares_config_patch_proposal_input_contract():
    handoff = _roles()["agent-meta-manager"].get("handoff") or {}
    assert "config-patch-proposal-v1" in (handoff.get("input_contracts") or [])


def test_no_output_not_consumed_finding_for_config_patch_proposal():
    from scripts.lib.consistency.handoff_contracts import check_handoff_contracts  # type: ignore
    findings = check_handoff_contracts(REPO_ROOT)
    bad = [f for f in findings if f.check == "handoff.output-not-consumed" and "config-patch-proposal-v1" in f.message]
    assert not bad, bad


def test_config_patch_proposal_schema_exists_and_pins_the_contract():
    schema_path = REPO_ROOT / "schemas" / "handoffs" / "config-patch-proposal.schema.json"
    assert schema_path.is_file(), schema_path
    data = json.loads(schema_path.read_text(encoding="utf-8"))

    assert data["$schema"] == "http://json-schema.org/draft-07/schema#"
    assert data["type"] == "object"
    assert "config-patch-proposal-v1" in data["title"]
    assert "config-patch-proposal-v1" in data["description"]

    # Top-level contract markers: STATUS / RESULT / PROPOSALS / PROOF / NEXT.
    assert set(data["required"]) == {"st", "rs", "pr", "pf", "nx"}
    assert data["properties"]["st"]["enum"] == ["done", "partial", "failed"]
    assert data["properties"]["ar"]["maxItems"] == 0

    # The two sub-objects are reachable without resolving a $ref.
    proposal = data["definitions"]["proposal"]
    proof = data["definitions"]["proof"]
    assert proposal["type"] == "object"
    assert proof["type"] == "object"

    assert set(proposal["required"]) == {
        "id", "kind", "sc", "dt", "ap", "al", "pl", "mk", "wn", "yb", "ib", "vr", "ra",
    }
    assert proposal["properties"]["kind"]["enum"] == [
        "no-effect",
        "dead-variable-content-loss",
        "duplicate-value",
        "relocate-to-ext",
        "relocate-to-doc",
        "semantic-merge",
        "inactive-scope",
        "structural-simplify",
        "info-only",
    ]
    assert proposal["properties"]["sc"]["enum"] == [
        "variables",
        "roles",
        "providers",
        "auto_commit",
        "hooks",
        "repo_containment",
        "orchestrator",
        "structural-other",
    ]
    assert proposal["properties"]["al"]["enum"] == ["confirm", "confirm-runtime"]
    assert proposal["properties"]["pl"]["enum"] == ["none", "L0", "L1", "L2", "L3"]
    assert proposal["properties"]["mk"]["items"]["enum"] == [
        "runtime-reader",
        "refilled-by-defaults",
        "inactive-scope",
        "reactivation-loss-warning",
    ]
    assert proposal["properties"]["id"]["pattern"] == "^OPT-[a-z-]+:.+$"
    assert proposal["properties"]["dt"]["type"] == "boolean"
    assert proposal["properties"]["ap"]["type"] == "boolean"

    assert set(proof["required"]) == {"lvl", "beq", "cmp", "rto", "snt"}
    assert proof["properties"]["lvl"]["enum"] == ["none", "L0", "L1", "L2", "L3"]
    assert proof["properties"]["rto"]["enum"] == ["ok", "nok"]
    assert proof["properties"]["beq"]["minimum"] == 0
    assert proof["properties"]["cmp"]["minimum"] == 0


def test_config_patch_proposal_stays_a_phase_2_contract():
    roles = _roles()
    producers = [
        name
        for name, info in roles.items()
        if (info.get("handoff") or {}).get("output_contract") == "config-patch-proposal-v1"
    ]
    assert producers == ["meta-optimizer"]
    # Phase 0 / 0e roles must neither produce nor consume the phase-2 contract.
    for phase0_role in ("meta-doctor", "template-auditor"):
        info = roles.get(phase0_role) or {}
        handoff = info.get("handoff") or {}
        assert handoff.get("output_contract") != "config-patch-proposal-v1", phase0_role
        assert "config-patch-proposal-v1" not in (handoff.get("input_contracts") or []), phase0_role

