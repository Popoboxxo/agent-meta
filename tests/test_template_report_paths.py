"""Guard long-report instructions in generic templates (SR-C-01 / C-01).

Read-only reviewers cannot write files, so they must follow the #514
truncation-guard contract (compact summary + chunking, persistence by a
write-capable role). Write-capable auditors persist long reports inside
the repo-containment area (`.tmp/`) without a provider-specific path.
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
def test_writable_auditor_reports_into_repo_tmp(role):
    text = _read(role)
    assert re.search(r"`\.tmp/[a-z0-9-]+-<topic>\.md`", text)
