"""Structural tests for the review-agent fleet (docs/concepts/planned/review-agent-fleet.md).

Enforces design principles P1 (output contract), P3/P4 (rules index + evidence schema),
P5 (MERGE_SCORE) and P6 (explicit model tier) for the five domain reviewer roles.
"""

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS = _REPO_ROOT / "agents" / "1-generic"
RULES_DIR = _REPO_ROOT / "config" / "review-rules"
ROUTING_FILE = _REPO_ROOT / "config" / "routing" / "reviewers.yaml"

FLEET_ROLES = {
    "frontend-reviewer": "balanced",
    "backend-reviewer": "balanced",
    "database-reviewer": "powerful",
    "ui-reviewer": "balanced",
    # security-auditor is a refactor of an existing role; tier asserted below.
    "security-auditor": "powerful",
}

SEVERITY_ENUM = "CRITICAL | HIGH | MEDIUM | LOW"


def _template(role: str) -> str:
    return (AGENTS / f"{role}.md").read_text(encoding="utf-8")


def test_fleet_templates_exist_with_valid_frontmatter():
    for role in FLEET_ROLES:
        text = _template(role)
        assert text.startswith("---\n"), f"{role}: frontmatter missing"
        assert re.search(r'^name: template-.*$', text, re.M), f"{role}: name field"
        assert re.search(r'^version: "', text, re.M), f"{role}: version field"
        assert re.search(r"^description: ", text, re.M), f"{role}: description field"
        assert re.search(r"^tools:", text, re.M), f"{role}: tools field"


def test_p1_output_contract_present():
    for role in FLEET_ROLES:
        text = _template(role)
        assert "STATUS: done | partial | blocked" in text or (
            re.search(r"STATUS: done \| partial \| blocked|STATUS: done\|partial\|blocked", text)
        ), f"{role}: P1 STATUS line missing"
        assert "RESULT:" in text, f"{role}: P1 RESULT block missing"
        assert "ARTIFACTS:" in text, f"{role}: P1 ARTIFACTS block missing"


def test_p5_merge_score_defined():
    for role in FLEET_ROLES:
        text = _template(role)
        assert "MERGE_SCORE:" in text, f"{role}: P5 MERGE_SCORE missing"
        assert SEVERITY_ENUM in text or "CRITICAL | HIGH | MEDIUM | LOW" in text, (
            f"{role}: severity enum missing"
        )


def test_p3_rules_index_section():
    for role in FLEET_ROLES:
        text = _template(role)
        assert "<rules-index>" in text, f"{role}: rules-index section missing"
        domain = role.replace("-reviewer", "")
        if role == "security-auditor":
            domain = "security"
        assert (RULES_DIR / f"{domain}.yaml").exists(), f"{domain} rules index file missing"


def test_rules_indexes_cite_ids_matching_templates():
    for role in FLEET_ROLES:
        text = _template(role)
        ids_in_template = set(re.findall(r"\b(?:FE|BE|DB|UI|SEC)-0\d\b", text))
        assert ids_in_template, f"{role}: no rule ids referenced in template"
        domain = role.replace("-reviewer", "") or "security"
        if role == "security-auditor":
            domain = "security"
        index_text = (RULES_DIR / f"{domain}.yaml").read_text(encoding="utf-8")
        for rid in ids_in_template:
            assert f"id: {rid}" in index_text, f"{rid} cited by {role} but missing in {domain}.yaml"


def test_p4_evidence_fields_in_security_contract():
    text = _template("security-auditor")
    for marker in ("**Evidence:**", "**rule_id:**", "**Confidence:**", "CWE"):
        assert marker in text, f"security-auditor: P4 marker {marker!r} missing"


def test_p6_explicit_tiers_in_role_defaults():
    defaults = (_REPO_ROOT / "config" / "role-defaults.yaml").read_text(encoding="utf-8")
    for role, tier in FLEET_ROLES.items():
        entry = re.search(rf"^  {re.escape(role)}:\n(.*?)(?=^  \w|\Z)", defaults, re.M | re.S)
        assert entry, f"{role}: missing from config/role-defaults.yaml"
        assert f"model: {tier}" in entry.group(1), (
            f"{role}: expected model tier {tier!r}"
        )


def test_routing_matrix_file_structure():
    content = ROUTING_FILE.read_text(encoding="utf-8")
    assert "routes:" in content
    assert "synthesis:" in content
    for role in ("frontend-reviewer", "backend-reviewer", "database-reviewer", "ui-reviewer"):
        assert role in content, f"{role} not referenced in routing matrix"


# --- issue #514: silent return-channel truncation mitigation ------------

_MITIGATION_ROLES = ("planner", "code-reviewer", "explorer")


def test_output_guard_present_in_readonly_heavy_roles():
    for role in _MITIGATION_ROLES:
        text = (AGENTS / f"{role}.md").read_text(encoding="utf-8")
        assert "<output-guard>" in text, f"{role}: output-guard section missing"
        assert "issue #514" in text, f"{role}: truncation reference missing"
        assert "chunk" in text.lower(), f"{role}: chunked-continuation rule missing"
