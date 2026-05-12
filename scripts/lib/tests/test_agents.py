"""Unit tests for scripts/lib/agents.py — frontmatter injection and composition."""

import pytest
from lib.agents import (
    extract_frontmatter_field,
    build_frontmatter,
    inject_model_field,
    inject_memory_field,
    inject_permission_mode_field,
    inject_temperature_field,
    inject_max_tokens_field,
    target_filename,
    role_from_platform_file,
    apply_patch,
)
from lib.log import SyncLog


@pytest.fixture
def log():
    return SyncLog()


# ---------------------------------------------------------------------------
# extract_frontmatter_field
# ---------------------------------------------------------------------------

AGENT_WITH_FRONTMATTER = "---\nname: developer\nversion: 2.1.0\ndescription: Test\n---\n\nBody.\n"


def test_extract_name():
    assert extract_frontmatter_field(AGENT_WITH_FRONTMATTER, "name") == "developer"


def test_extract_version():
    assert extract_frontmatter_field(AGENT_WITH_FRONTMATTER, "version") == "2.1.0"


def test_extract_missing_field_returns_none():
    assert extract_frontmatter_field(AGENT_WITH_FRONTMATTER, "model") is None


def test_extract_no_frontmatter_returns_none():
    assert extract_frontmatter_field("No frontmatter here.", "name") is None


# ---------------------------------------------------------------------------
# build_frontmatter
# ---------------------------------------------------------------------------

def test_build_frontmatter_updates_name():
    content = "---\nname: old\ndescription: old\n---\nBody."
    result = build_frontmatter(content, "new-name", "New description")
    assert "name: new-name" in result


def test_build_frontmatter_name_field_present():
    content = "---\nname: developer\ndescription: A description\n---\nBody."
    result = build_frontmatter(content, "developer", "A description")
    assert "name: developer" in result
    assert "description:" in result


def test_build_frontmatter_adds_generated_from():
    content = "---\nname: dev\ndescription: d\n---\nBody."
    result = build_frontmatter(content, "dev", "d", generated_from="1-generic/dev.md@1.0.0")
    assert "generated-from" in result
    assert "1-generic/dev.md@1.0.0" in result


# ---------------------------------------------------------------------------
# inject_model_field
# ---------------------------------------------------------------------------

def test_inject_model_inserts_after_name():
    content = "---\nname: developer\ndescription: d\n---\nBody."
    result = inject_model_field(content, "claude-sonnet-4-6")
    assert "model: claude-sonnet-4-6" in result


def test_inject_model_updates_existing():
    content = "---\nname: developer\nmodel: claude-haiku-4-5\ndescription: d\n---\nBody."
    result = inject_model_field(content, "claude-sonnet-4-6")
    assert "model: claude-sonnet-4-6" in result
    assert "claude-haiku-4-5" not in result


def test_inject_model_empty_removes_field():
    content = "---\nname: developer\nmodel: claude-sonnet-4-6\ndescription: d\n---\nBody."
    result = inject_model_field(content, "")
    assert "model:" not in result


# ---------------------------------------------------------------------------
# inject_memory_field
# ---------------------------------------------------------------------------

def test_inject_memory_inserts():
    content = "---\nname: developer\nmodel: claude-sonnet-4-6\ndescription: d\n---\nBody."
    result = inject_memory_field(content, "project")
    assert "memory: project" in result


def test_inject_memory_updates_existing():
    content = "---\nname: developer\nmemory: local\ndescription: d\n---\nBody."
    result = inject_memory_field(content, "project")
    assert "memory: project" in result
    assert "local" not in result


def test_inject_memory_empty_removes_field():
    content = "---\nname: developer\nmemory: project\ndescription: d\n---\nBody."
    result = inject_memory_field(content, "")
    assert "memory:" not in result


# ---------------------------------------------------------------------------
# inject_permission_mode_field
# ---------------------------------------------------------------------------

def test_inject_permission_mode_inserts():
    content = "---\nname: validator\nmemory: project\ndescription: d\n---\nBody."
    result = inject_permission_mode_field(content, "plan")
    assert "permissionMode: plan" in result


def test_inject_permission_mode_empty_removes():
    content = "---\nname: validator\npermissionMode: plan\ndescription: d\n---\nBody."
    result = inject_permission_mode_field(content, "")
    assert "permissionMode:" not in result


# ---------------------------------------------------------------------------
# inject_temperature_field
# ---------------------------------------------------------------------------

def test_inject_temperature_inserts():
    content = "---\nname: developer\nmodel: m\ndescription: d\n---\nBody."
    result = inject_temperature_field(content, "0.2")
    assert "temperature: 0.2" in result


def test_inject_temperature_updates():
    content = "---\nname: developer\ntemperature: 0.7\ndescription: d\n---\nBody."
    result = inject_temperature_field(content, "0.2")
    assert "temperature: 0.2" in result
    assert "0.7" not in result


def test_inject_temperature_empty_removes():
    content = "---\nname: developer\ntemperature: 0.2\ndescription: d\n---\nBody."
    result = inject_temperature_field(content, "")
    assert "temperature:" not in result


# ---------------------------------------------------------------------------
# inject_max_tokens_field
# ---------------------------------------------------------------------------

def test_inject_max_tokens_inserts():
    content = "---\nname: developer\ntemperature: 0.2\ndescription: d\n---\nBody."
    result = inject_max_tokens_field(content, "8192")
    assert "maxTokens: 8192" in result


def test_inject_max_tokens_empty_removes():
    content = "---\nname: developer\nmaxTokens: 8192\ndescription: d\n---\nBody."
    result = inject_max_tokens_field(content, "")
    assert "maxTokens:" not in result


# ---------------------------------------------------------------------------
# target_filename
# ---------------------------------------------------------------------------

def test_target_filename_known_role():
    role_map = {"developer": "developer", "git": "git"}
    assert target_filename("developer", role_map) == "developer.md"


def test_target_filename_unknown_role():
    role_map = {"developer": "developer"}
    assert target_filename("nonexistent", role_map) is None


# ---------------------------------------------------------------------------
# role_from_platform_file
# ---------------------------------------------------------------------------

def test_role_from_platform_file_matches():
    result = role_from_platform_file("claude-developer.md", ["claude"])
    assert result == "developer"


def test_role_from_platform_file_no_match():
    result = role_from_platform_file("developer.md", ["claude"])
    assert result is None


def test_role_from_platform_file_no_platform():
    result = role_from_platform_file("developer.md", [])
    assert result is None


# ---------------------------------------------------------------------------
# apply_patch
# ---------------------------------------------------------------------------

AGENT_WITH_SECTION = """---
name: test
description: t
---

## Section A

Content A.

## Section B

Content B.
"""


def test_patch_append_after(log):
    patch = {
        "op": "append-after",
        "anchor": "## Section A",
        "content": "## Section A-Extra\n\nExtra content.\n",
    }
    result = apply_patch(AGENT_WITH_SECTION, patch, log, "test.md")
    assert "## Section A-Extra" in result
    assert result.index("## Section A-Extra") > result.index("## Section A")


def test_patch_replace(log):
    patch = {
        "op": "replace",
        "anchor": "## Section A",
        "content": "## Section A\n\nReplaced content.\n",
    }
    result = apply_patch(AGENT_WITH_SECTION, patch, log, "test.md")
    assert "Replaced content." in result
    assert "Content A." not in result


def test_patch_delete(log):
    patch = {"op": "delete", "anchor": "## Section A"}
    result = apply_patch(AGENT_WITH_SECTION, patch, log, "test.md")
    assert "## Section A" not in result
    assert "Content A." not in result
    assert "## Section B" in result


def test_patch_append_to_end(log):
    patch = {"op": "append", "content": "\n## Appended\n\nNew content.\n"}
    result = apply_patch(AGENT_WITH_SECTION, patch, log, "test.md")
    assert result.endswith("## Appended\n\nNew content.\n")


def test_patch_unknown_op_does_nothing(log):
    patch = {"op": "unknown-op", "anchor": "## Section A", "content": "x"}
    result = apply_patch(AGENT_WITH_SECTION, patch, log, "test.md")
    assert result == AGENT_WITH_SECTION
