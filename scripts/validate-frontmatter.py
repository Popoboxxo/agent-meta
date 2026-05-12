#!/usr/bin/env python3
"""Validate frontmatter in all generated agent files.

Checks:
- name: field present and non-empty
- description: field present and non-empty
- No unresolved {{VAR}} placeholders in frontmatter
- version: field present in source templates (1-generic/, 2-platform/)

Exit 0: all checks passed
Exit 1: one or more validation errors
"""

import re
import sys
from pathlib import Path

AGENT_DIRS = [
    ".claude/agents",
    ".gemini/agents",
    ".continue/agents",
    ".opencode/agents",
]

TEMPLATE_DIRS = [
    "agents/1-generic",
    "agents/2-platform",
]

_PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")


def parse_frontmatter(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    end = content.find("\n---", 3)
    if end == -1:
        return {}
    fm = content[3:end]
    result = {}
    for line in fm.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip()] = val.strip().strip('"').strip("'")
    return result


def validate_generated_agents(root: Path) -> list[str]:
    errors = []
    for agent_dir_rel in AGENT_DIRS:
        agent_dir = root / agent_dir_rel
        if not agent_dir.exists():
            continue
        for agent_file in sorted(agent_dir.glob("*.md")):
            content = agent_file.read_text(encoding="utf-8")
            fm = parse_frontmatter(content)
            rel = str(agent_file.relative_to(root))

            if not fm.get("name"):
                errors.append(f"{rel}: missing or empty 'name:' field")

            if not fm.get("description"):
                errors.append(f"{rel}: missing or empty 'description:' field")

            # Check frontmatter section for unresolved placeholders
            end = content.find("\n---", 3)
            fm_section = content[:end + 4] if end != -1 else content[:200]
            placeholders = _PLACEHOLDER_RE.findall(fm_section)
            if placeholders:
                errors.append(f"{rel}: unresolved placeholders in frontmatter: {placeholders}")

    return errors


def validate_source_templates(root: Path) -> list[str]:
    errors = []
    for template_dir_rel in TEMPLATE_DIRS:
        template_dir = root / template_dir_rel
        if not template_dir.exists():
            continue
        for template_file in sorted(template_dir.glob("*.md")):
            if template_file.name.startswith("_"):
                continue
            content = template_file.read_text(encoding="utf-8")
            fm = parse_frontmatter(content)
            rel = str(template_file.relative_to(root))

            if not fm.get("version"):
                errors.append(f"{rel}: missing 'version:' in source template frontmatter")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    errors: list[str] = []

    errors.extend(validate_generated_agents(root))
    errors.extend(validate_source_templates(root))

    if errors:
        print(f"FRONTMATTER VALIDATION FAILED ({len(errors)} error(s)):")
        for e in errors:
            print(f"  ERROR  {e}")
        return 1

    total = sum(
        len(list((root / d).glob("*.md")))
        for d in AGENT_DIRS
        if (root / d).exists()
    )
    print(f"Frontmatter validation passed — {total} generated agent file(s) checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
