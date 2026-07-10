#!/usr/bin/env python3
"""Validate Modern Mode agent templates (6-block XML structure).

Usage:
    python scripts/validate-modern-templates.py [--role ROLE] [--all] [--strict]

Exit codes:
    0  All checks passed
    1  Validation errors found
    2  Usage / file-not-found error
"""
import argparse
import re
import sys
from pathlib import Path

REQUIRED_BLOCKS = ["persona", "workflow", "context", "tools", "output_contract", "constraints"]
EXPECTED_ORDER = REQUIRED_BLOCKS  # must appear in this order

REPO_ROOT = Path(__file__).resolve().parent.parent
MODERN_DIR = REPO_ROOT / "agents" / "1-generic-modern"

REQUIRED_FRONTMATTER = ["name", "version", "description", "prompt_mode"]


def _check_frontmatter(content: str, strict: bool) -> list[str]:
    errors = []
    if not content.startswith("---"):
        errors.append("Missing YAML frontmatter")
        return errors
    end = content.find("\n---", 3)
    if end == -1:
        errors.append("Unclosed YAML frontmatter")
        return errors
    fm = content[3:end]
    for field in REQUIRED_FRONTMATTER:
        if not re.search(rf"^{field}:", fm, re.MULTILINE):
            errors.append(f"Missing frontmatter field: {field}")
    prompt_mode = re.search(r"^prompt_mode:\s*(.+)$", fm, re.MULTILINE)
    if prompt_mode and prompt_mode.group(1).strip() != "modern":
        errors.append(f"prompt_mode must be 'modern', got: {prompt_mode.group(1).strip()}")
    if strict:
        version = re.search(r"^version:\s*[\"']?(\d+)\.", fm, re.MULTILINE)
        if version and int(version.group(1)) < 3:
            errors.append("Modern templates require major version >= 3")
    return errors


def _check_xml_blocks(content: str, strict: bool) -> list[str]:
    errors = []
    found_blocks = []
    for block in REQUIRED_BLOCKS:
        open_tag = f"<{block}>"
        close_tag = f"</{block}>"
        if open_tag not in content:
            errors.append(f"Missing opening tag: {open_tag}")
        elif close_tag not in content:
            errors.append(f"Missing closing tag: {close_tag}")
        else:
            found_blocks.append(block)

    if strict and len(found_blocks) == len(REQUIRED_BLOCKS):
        # Only match block-level opening tags (preceded by newline or start of string)
        positions = []
        for b in found_blocks:
            import re as _re
            m = _re.search(rf'(?:^|\n)<{b}>', content)
            if m:
                positions.append((m.start(), b))
        positions.sort()
        actual_order = [b for _, b in positions]
        if actual_order != EXPECTED_ORDER:
            errors.append(
                f"Wrong block order. Expected: {EXPECTED_ORDER}, Got: {actual_order}"
            )

    if strict:
        if "{{#if " in content:
            errors.append("Modern templates must not use {{#if}} — use pre-resolved block variables")
        if "{{#unless " in content:
            errors.append("Modern templates must not use {{#unless}}")

    return errors


def validate_file(path: Path, strict: bool) -> list[str]:
    if not path.exists():
        return [f"File not found: {path}"]
    content = path.read_text(encoding="utf-8")
    errors = _check_frontmatter(content, strict)
    errors += _check_xml_blocks(content, strict)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Modern Mode agent templates")
    parser.add_argument("--role", help="Validate a single role (e.g. 'developer')")
    parser.add_argument("--all", action="store_true", dest="all_roles", help="Validate all templates in 1-generic-modern/")
    parser.add_argument("--strict", action="store_true", help="Enable strict checks (order, version, no conditionals)")
    args = parser.parse_args()

    if not args.role and not args.all_roles:
        parser.print_help()
        return 2

    targets: list[Path] = []
    if args.role:
        targets.append(MODERN_DIR / f"{args.role}.md")
    if args.all_roles:
        if not MODERN_DIR.exists():
            print(f"ERROR: {MODERN_DIR} does not exist", file=sys.stderr)
            return 2
        targets.extend(sorted(MODERN_DIR.glob("*.md")))
        targets = [t for t in targets if not t.name.startswith("_")]

    if not targets:
        print("No templates to validate.")
        return 0

    total_errors = 0
    for path in targets:
        errors = validate_file(path, args.strict)
        rel = path.relative_to(REPO_ROOT)
        if errors:
            print(f"\nFAIL: {rel}")
            for e in errors:
                print(f"  - {e}")
            total_errors += len(errors)
        else:
            print(f"OK:   {rel}")

    if total_errors:
        print(f"\n{total_errors} error(s) found.")
        return 1

    print(f"\nAll {len(targets)} template(s) passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
