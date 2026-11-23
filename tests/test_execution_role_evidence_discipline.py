"""Issue #1329 (AC-3 / Contract AC-4) — no fabricated verify evidence.

Every execution role must bind success claims to an exit code it actually
observed. Without one the only admissible verdict is `partial`/unverified.
The rule is provider-neutral prose inside `<constraints>` — no provider name,
no capability logic.

Run: python3 -m pytest tests/test_execution_role_evidence_discipline.py -q
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from scripts.lib.frontmatter import _parse_frontmatter_yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = REPO_ROOT / "agents" / "1-generic"

EXECUTION_ROLES = (
    "test-executor",
    "code-reviewer",
    "e2e-tester",
    "git",
    "developer",
    "devops-engineer",
    "tester",
)

#: Canonical, single-source rule pinned into every execution-role template.
EVIDENCE_RULE = (
    "- **Measured evidence only:** claim success (tests passed, green, pass "
    "counts) only with an exit code you actually observed in this turn — "
    "without a measured exit code report the result as `partial`/unverified; "
    "never fabricate pass evidence."
)


@pytest.mark.parametrize("role", EXECUTION_ROLES)
def test_execution_role_binds_success_claims_to_measured_exit_code(role):
    text = (TEMPLATE_DIR / f"{role}.md").read_text(encoding="utf-8")
    assert text.count(EVIDENCE_RULE) == 1, (
        f"{role}.md must carry the canonical measured-evidence rule exactly once"
    )
    constraints = text.split("<constraints>", 1)
    assert len(constraints) == 2, f"{role}.md has no <constraints> section"
    assert EVIDENCE_RULE in constraints[1], (
        f"{role}.md: evidence rule must live inside <constraints>"
    )


@pytest.mark.parametrize("role", EXECUTION_ROLES)
def test_evidence_rule_did_not_change_the_tool_posture(role):
    text = (TEMPLATE_DIR / f"{role}.md").read_text(encoding="utf-8")
    fm = _parse_frontmatter_yaml(text)
    tools = fm.get("tools") or []
    assert "Bash" in tools, f"{role}.md must still declare Bash (posture frozen)"
    assert re.fullmatch(r"\d+\.\d+\.\d+", str(fm.get("version", ""))), (
        f"{role}.md needs a semantic version after the content change"
    )


def test_evidence_rule_is_provider_neutral():
    """No provider name and no capability key may leak into the prompt prose."""
    for role in EXECUTION_ROLES:
        text = (TEMPLATE_DIR / f"{role}.md").read_text(encoding="utf-8")
        section = text.split("<constraints>", 1)[1]
        assert "subagent-shell" not in section
        assert "Opencode" not in section
        assert "VERIFIED-RUNTIME" not in section
