"""Test suite for opencode-generated agent files.

Validates that agent frontmatter contains correctly mapped permissions,
especially the `task` permission required for subagent delegation.

Run: python tests/test_opencode_agents.py
"""

import re
import sys
from pathlib import Path


def _split_frontmatter(content: str) -> tuple[str, str]:
    """Split content into (frontmatter_block, body)."""
    if not content.startswith("---"):
        return "", content
    end = content.find("\n---", 3)
    if end == -1:
        return "", content
    return content[: end + 4], content[end + 4:]


def _extract_yaml_permissions(fm: str) -> dict[str, str]:
    """Extract permission key/value pairs from opencode frontmatter.

    Handles block form:
      permission:
        key: value
        key: value
    """
    perms: dict[str, str] = {}
    block = re.search(
        r"^permission:\s*\n((?:  .+\n?)+)",
        fm,
        flags=re.MULTILINE,
    )
    if block:
        for line in block.group(1).strip().splitlines():
            stripped = line.strip()
            if ":" in stripped:
                key, val = stripped.split(":", 1)
                perms[key.strip()] = val.strip().strip('"').strip("'")
    return perms


AGENTS_DIR = Path(__file__).resolve().parent.parent / ".opencode" / "agents"

# Roles that are expected to have a `task` permission because they delegate.
# ideation/tester/developer are workers by design (anti-recursion guard) — they
# refer to other roles in text but never dispatch via tool calls. developer's
# dead `Agent` tool grant was removed across 1-generic and all 2-platform
# full-replacement overrides (see CHANGELOG.md [Unreleased] / Änderung).
DELEGATING_ROLES = {
    "orchestrator",
    "feature",
    "agent-meta-manager",
}

# Map template tool names to expected opencode permission keys
EXPECTED_PERMISSION_MAPPINGS = {
    "Agent": "task",
    "TodoWrite": "todowrite",
    "Bash": "bash",
    "Read": "read",
    "Write": "edit",
    "Edit": "edit",
    "Glob": "glob",
    "Grep": "grep",
    "WebFetch": "webfetch",
    "WebSearch": "websearch",
}


def check_all_agents_have_permissions() -> list[str]:
    """Every generated opencode agent (except ping-test) must have a permission block."""
    errors = []
    for path in sorted(AGENTS_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        fm, _ = _split_frontmatter(content)
        name_match = re.search(r"^name:\s*(.+)$", fm, flags=re.MULTILINE)
        name = name_match.group(1).strip() if name_match else path.stem

        if name == "ping-test":
            continue  # intentionally minimal

        perms = _extract_yaml_permissions(fm)
        if not perms:
            errors.append(f"{name}: missing 'permission:' frontmatter block")

    return errors


def check_delegating_roles_have_task() -> list[str]:
    """Roles that delegate must have task permission set to allow."""
    errors = []
    for path in sorted(AGENTS_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        fm, _ = _split_frontmatter(content)
        name_match = re.search(r"^name:\s*(.+)$", fm, flags=re.MULTILINE)
        name = name_match.group(1).strip() if name_match else path.stem

        if name not in DELEGATING_ROLES:
            continue

        perms = _extract_yaml_permissions(fm)
        if perms.get("task") != "allow":
            errors.append(
                f"{name}: must have permission 'task: allow' for subagent delegation, got: {perms.get('task', 'MISSING')}"
            )

    return errors


def check_no_claude_tool_names_in_permissions() -> list[str]:
    """No PascalCase Claude tool names should leak into opencode permission values."""
    errors = []
    for path in sorted(AGENTS_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        fm, _ = _split_frontmatter(content)
        perms = _extract_yaml_permissions(fm)

        for key in perms:
            if key in EXPECTED_PERMISSION_MAPPINGS:
                errors.append(
                    f"{path.stem}: unmapped Claude tool name '{key}' found in opencode permission block"
                )

    return errors


def check_orchestrator_can_delegate() -> list[str]:
    """Orchestrator specifically needs task + todowrite permissions."""
    errors = []
    path = AGENTS_DIR / "orchestrator.md"
    if not path.exists():
        errors.append("orchestrator.md not found in .opencode/agents/")
        return errors

    content = path.read_text(encoding="utf-8")
    fm, _ = _split_frontmatter(content)
    perms = _extract_yaml_permissions(fm)

    if perms.get("task") != "allow":
        errors.append("orchestrator: missing permission 'task: allow' — cannot delegate to subagents")
    if perms.get("todowrite") != "allow":
        errors.append("orchestrator: missing permission 'todowrite: allow' — cannot manage todos")

    return errors


def check_no_deprecated_tools_field() -> list[str]:
    """Opencode agents must not use the deprecated 'tools:' frontmatter field."""
    errors = []
    for path in sorted(AGENTS_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        fm, _ = _split_frontmatter(content)
        if re.search(r"^tools:", fm, flags=re.MULTILINE):
            errors.append(f"{path.stem}: uses deprecated 'tools:' frontmatter field")
    return errors


def check_parallel_pattern_uses_task() -> list[str]:
    """The parallel execution pattern in orchestrator must reference `task`, not `Agent`."""
    errors = []
    path = AGENTS_DIR / "orchestrator.md"
    if not path.exists():
        return errors

    body = path.read_text(encoding="utf-8")
    if "`Agent`-Tool" in body or "`Agent` Tool" in body:
        errors.append(
            "orchestrator: body still references Claude 'Agent' tool instead of opencode 'task'"
        )

    return errors


def _skip_unless_generated():
    """Skip pytest runs when the Opencode provider output is not present."""
    import pytest
    if not AGENTS_DIR.exists():
        pytest.skip("no .opencode/agents directory — Opencode provider not generated")


def test_all_agents_have_permissions():
    _skip_unless_generated()
    assert check_all_agents_have_permissions() == []


def test_delegating_roles_have_task():
    _skip_unless_generated()
    assert check_delegating_roles_have_task() == []


def test_no_claude_tool_names_in_permissions():
    _skip_unless_generated()
    assert check_no_claude_tool_names_in_permissions() == []


def test_orchestrator_can_delegate():
    _skip_unless_generated()
    assert check_orchestrator_can_delegate() == []


def test_no_deprecated_tools_field():
    _skip_unless_generated()
    assert check_no_deprecated_tools_field() == []


def test_parallel_pattern_uses_task():
    _skip_unless_generated()
    assert check_parallel_pattern_uses_task() == []


def run_all() -> int:
    """Run all tests and print a summary."""
    all_errors: list[str] = []
    tests = [
        ("All agents have permissions", check_all_agents_have_permissions),
        ("Delegating roles have task", check_delegating_roles_have_task),
        ("No deprecated tools field", check_no_deprecated_tools_field),
        ("No Claude tool names remain", check_no_claude_tool_names_in_permissions),
        ("Orchestrator can delegate", check_orchestrator_can_delegate),
        ("Parallel pattern uses task", check_parallel_pattern_uses_task),
    ]

    print("=" * 60)
    print("Opencode Agent Frontmatter Tests")
    print("=" * 60)

    for label, fn in tests:
        errors = fn()
        status = "PASS" if not errors else "FAIL"
        print(f"  [{status}] {label}")
        for err in errors:
            print(f"         ! {err}")
        all_errors.extend(errors)

    print("=" * 60)
    if not all_errors:
        print("All tests passed.")
        return 0
    print(f"FAILED: {len(all_errors)} error(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(run_all())
