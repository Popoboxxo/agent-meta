#!/usr/bin/env python3
"""Estimate token counts for agent templates (chars/4 approximation).

Usage:
    python scripts/token-counter.py [--role ROLE] [--legacy] [--modern] [--threshold N]

Flags:
    --role ROLE      Compare legacy vs modern for a specific role
    --legacy         Show counts for all 1-generic/ templates
    --modern         Show counts for all 1-generic-modern/ templates
    --threshold N    Exit 1 if any template exceeds N estimated tokens (default: 0 = disabled)

Exit codes:
    0  All within threshold (or threshold disabled)
    1  One or more templates exceed threshold
    2  Usage / file-not-found error
"""
import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LEGACY_DIR = REPO_ROOT / "agents" / "1-generic"
MODERN_DIR = REPO_ROOT / "agents" / "1-generic-modern"


def estimate_tokens(content: str) -> int:
    return max(1, len(content) // 4)


def count_file(path: Path) -> tuple[int, int]:
    """Return (char_count, token_estimate)."""
    content = path.read_text(encoding="utf-8")
    return len(content), estimate_tokens(content)


def print_row(label: str, chars: int, tokens: int, threshold: int) -> bool:
    flag = ""
    exceeded = threshold > 0 and tokens > threshold
    if exceeded:
        flag = "  ⚠ EXCEEDS THRESHOLD"
    print(f"  {label:<40} {chars:>8} chars  ~{tokens:>6} tokens{flag}")
    return exceeded


def compare_role(role: str, threshold: int) -> int:
    """Compare legacy vs modern for one role. Returns error count."""
    legacy_path = LEGACY_DIR / f"{role}.md"
    modern_path = MODERN_DIR / f"{role}.md"

    errors = 0
    print(f"\n[{role}]")

    for label, path in [("legacy (1-generic)", legacy_path), ("modern (1-generic-modern)", modern_path)]:
        if not path.exists():
            print(f"  {label}: NOT FOUND ({path})")
            continue
        chars, tokens = count_file(path)
        if print_row(label, chars, tokens, threshold):
            errors += 1

    if legacy_path.exists() and modern_path.exists():
        lc, lt = count_file(legacy_path)
        mc, mt = count_file(modern_path)
        delta_chars = mc - lc
        delta_tokens = mt - lt
        sign = "+" if delta_tokens >= 0 else ""
        print(f"  {'delta':<40} {sign}{delta_chars:>7} chars  {sign}{delta_tokens:>6} tokens")

    return errors


def show_dir(directory: Path, label: str, threshold: int) -> int:
    if not directory.exists():
        print(f"ERROR: {directory} does not exist", file=sys.stderr)
        return 1
    templates = sorted(f for f in directory.glob("*.md") if not f.name.startswith("_"))
    if not templates:
        print(f"No templates in {directory}")
        return 0

    errors = 0
    print(f"\n[{label}] ({directory.relative_to(REPO_ROOT)})")
    for path in templates:
        chars, tokens = count_file(path)
        if print_row(path.stem, chars, tokens, threshold):
            errors += 1
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Token counter for agent templates")
    parser.add_argument("--role", help="Compare legacy vs modern for a role")
    parser.add_argument("--legacy", action="store_true", help="List all 1-generic/ templates")
    parser.add_argument("--modern", action="store_true", help="List all 1-generic-modern/ templates")
    parser.add_argument("--threshold", type=int, default=0, metavar="N",
                        help="Exit 1 if any template exceeds N estimated tokens")
    args = parser.parse_args()

    if not args.role and not args.legacy and not args.modern:
        parser.print_help()
        return 2

    total_exceeded = 0

    if args.role:
        total_exceeded += compare_role(args.role, args.threshold)
    if args.legacy:
        total_exceeded += show_dir(LEGACY_DIR, "Legacy templates", args.threshold)
    if args.modern:
        total_exceeded += show_dir(MODERN_DIR, "Modern templates", args.threshold)

    print()
    if args.threshold > 0 and total_exceeded:
        print(f"WARN: {total_exceeded} template(s) exceed threshold of {args.threshold} tokens.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
