"""Guard long-report instructions in generic templates (SR-C-01 / C-01).

Read-only reviewers cannot write files, so they must follow the #514
truncation-guard contract (compact summary + chunking, persistence by a
write-capable role). Write-capable auditors persist long reports into the
configured tmp sink (`{{TMP_SINK_PATH}}/`) without a provider-specific path.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
GENERIC = ROOT / "agents" / "1-generic"

READ_ONLY_REVIEWERS = [
    "backend-reviewer",
    "database-reviewer",
    "ui-reviewer",
    "frontend-reviewer",
]
WRITABLE_AUDITORS = [
    "ai-security-guardian",
    "app-lifecycle-governor",
    "prompt-governor",
    "security-auditor",
]
SE_ROLES = [
    "se-architect",
    "se-component-requirements",
    "se-critic",
    "se-developer",
    "se-integration-and-test-manager",
    "se-interface-mgr",
    "se-junior-developer",
    "se-requirements",
    "se-senior-developer",
    "se-termination",
    "se-validator",
    "se-verifier",
]
ATOMIC_WRITE_ROLES = SE_ROLES + ["test-executor"]


def _read(role):
    return (GENERIC / f"{role}.md").read_text(encoding="utf-8")


def _frontmatter_tools(text):
    fm = text.split("---", 2)[1]
    match = re.search(r"^tools:\n((?:\s+-\s+\S+\n)+)", fm, re.MULTILINE)
    assert match, "tools list missing in frontmatter"
    return re.findall(r"-\s+(\S+)", match.group(1))


def test_no_provider_tmp_path_in_agents():
    hits = [
        str(p.relative_to(ROOT))
        for p in (ROOT / "agents").rglob("*.md")
        if "/tmp/opencode" in p.read_text(encoding="utf-8")
    ]
    assert hits == []


@pytest.mark.parametrize("role", READ_ONLY_REVIEWERS)
def test_read_only_reviewer_uses_514_contract(role):
    text = _read(role)
    assert "write-capable role" in text
    assert "chunk k/n" in text
    # No instruction to write a report file itself.
    assert not re.search(r"\bwrite (?:the )?(?:full )?report to\b", text)
    assert not re.search(r"\bfile under\b", text)
    assert "report file path" not in text


@pytest.mark.parametrize("role", READ_ONLY_REVIEWERS)
def test_read_only_reviewer_has_no_write_tools(role):
    tools = _frontmatter_tools(_read(role))
    assert not {"Write", "Edit", "Bash"} & set(tools)


@pytest.mark.parametrize("role", WRITABLE_AUDITORS)
def test_writable_auditor_reports_into_configured_sink(role):
    """AC-02: writable auditors write long reports into the configured tmp sink."""
    text = _read(role)
    assert "{{TMP_SINK_PATH}}/" in text
    assert not re.search(r"`\.tmp/[a-z0-9-]+-<topic>\.md`", text)


def _atomic_write_blocks(text):
    """Return the atomic-write paragraphs (blank-line separated blocks)."""
    return [block for block in re.split(r"\n[ \t]*\n", text) if "Atomic write" in block]


@pytest.mark.parametrize("role", ATOMIC_WRITE_ROLES)
def test_atomic_write_names_tmp_sink(role):
    """AC-22: the atomic-write/scratch instruction names the configured sink."""
    text = _read(role)
    assert "{{TMP_SINK_PATH}}" in text
    blocks = _atomic_write_blocks(text)
    for block in blocks:
        assert "{{TMP_SINK_PATH}}" in block, (
            f"{role}: atomic-write instruction does not name the configured sink"
        )
        vague = re.search(r"to a temporary file|temp \u2192 rename", block)
        assert not vague, (
            f"{role}: atomic-write instruction stays vague: "
            f"{block.strip().splitlines()[0]}"
        )
