#!/usr/bin/env python3
"""
bump-version.py — centralised version bump for agent-meta

Updates VERSION file and all documentation files referencing the current
version to the new version.  Designed to be the single entry-point for
version bumps during releases so that no hard-coded version strings drift
out of sync.

Usage:
    python scripts/bump-version.py <new-version>
    python scripts/bump-version.py <new-version> --dry-run
    python scripts/bump-version.py <new-version> --docs-only   # skip VERSION

Examples:
    python scripts/bump-version.py 0.58.0
    python scripts/bump-version.py 0.58.0 --dry-run
"""

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _read_current_version(agent_meta_root: Path) -> str:
    """Read the current version from the VERSION file."""
    version_file = agent_meta_root / "VERSION"
    if not version_file.exists():
        print(f"  !  VERSION file not found at {version_file}", file=sys.stderr)
        sys.exit(1)
    return version_file.read_text(encoding="utf-8").strip()


def _build_pattern(old_version: str) -> re.Pattern:
    """Build a regex that matches the current version in common formats.

    Matches both ``0.X.Y`` and ``v0.X.Y`` forms, but avoids matching
    longer dotted sequences (e.g. part of a date like ``2026.05.24``)
    and does *not* match the version in CHANGELOG section headers
    like ``## [0.56.0]`` (those are historical, not current)."""
    ver = re.escape(old_version)
    # Full pattern: optional 'v' prefix, the version, NOT followed by a digit
    # (avoids matching ``0.57.10`` when bumping from ``0.57.1``).
    return re.compile(rf"(?<!\w)v?{ver}(?!\d)")


def _bump_file_content(content: str, old_version: str, new_version: str,
                       filepath: Path) -> tuple[str, int]:
    """Replace all occurrences of *old_version* with *new_version* in *content*.

    Returns ``(new_content, replacement_count)``.
    """
    pattern = _build_pattern(old_version)
    new_content, count = pattern.subn(
        lambda m: m.group(0).replace(old_version, new_version), content
    )
    return new_content, count


def _collect_doc_files(agent_meta_root: Path) -> list[Path]:
    """Collect all Markdown files under docs/ and root README.md.

    Returns a list of resolved :class:`Path` objects sorted by path.
    Skips the CHANGELOG — its section headers are historical records,
    not current-version references.
    """
    files: list[Path] = []

    # README.md at repo root
    readme = agent_meta_root / "README.md"
    if readme.exists():
        files.append(readme)

    # All Markdown files under docs/
    docs_dir = agent_meta_root / "docs"
    if docs_dir.is_dir():
        for md in sorted(docs_dir.rglob("*.md")):
            files.append(md)

    return files


def _print_diff(filepath: Path, old_content: str, new_content: str):
    """Print a simple unified-diff-style summary for --dry-run."""
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()
    for i, (old_line, new_line) in enumerate(zip(old_lines, new_lines), start=1):
        if old_line != new_line:
            print(f"--- {filepath}:{i}")
            print(f"-{old_line}")
            print(f"+{new_line}")
            print()


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Centralised version bump for agent-meta — updates "
                    "VERSION + all documentation references."
    )
    parser.add_argument(
        "new_version", metavar="NEW_VERSION",
        help="New semver version string, e.g. 0.58.0"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be changed without writing files"
    )
    parser.add_argument(
        "--docs-only", action="store_true",
        help="Only update documentation files, skip the VERSION file"
    )
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    agent_meta_root = script_path.parent.parent  # scripts/ -> repo root

    old_version = _read_current_version(agent_meta_root)
    new_version = args.new_version

    if old_version == new_version:
        print(f"  i  VERSION is already {new_version} — nothing to do")
        return

    print(f"Bumping version: {old_version} → {new_version}")
    if args.dry_run:
        print("DRY-RUN — no files will be written\n")

    # 1. Update VERSION file (unless --docs-only)
    if not args.docs_only:
        version_file = agent_meta_root / "VERSION"
        print(f"  {'[DRY-RUN]' if args.dry_run else '[UPDATE]'}  VERSION")
        if not args.dry_run:
            version_file.write_text(new_version + "\n", encoding="utf-8")

    # 2. Collect and update documentation files
    doc_files = _collect_doc_files(agent_meta_root)
    total_replacements = 0
    updated_files = 0

    for filepath in doc_files:
        old_content = filepath.read_text(encoding="utf-8")
        new_content, count = _bump_file_content(
            old_content, old_version, new_version, filepath
        )
        if count > 0:
            tag = "DRY-RUN" if args.dry_run else "UPDATE"
            print(f"  [{tag}]  {filepath.relative_to(agent_meta_root)}  ({count} replacement(s))")
            if args.dry_run:
                _print_diff(filepath, old_content, new_content)
            else:
                filepath.write_text(new_content, encoding="utf-8")
            total_replacements += count
            updated_files += 1

    # Summary
    print()
    if updated_files == 0:
        print(f"  i  No documentation files reference version {old_version}")
    else:
        tag = "Would update" if args.dry_run else "Updated"
        print(f"  {tag} {updated_files} file(s) ({total_replacements} replacement(s))")

    if not args.dry_run and not args.docs_only:
        print(f"  VERSION written: {new_version}")
        print(f"\n  Next steps:")
        print(f"    1. Review changes: git diff")
        print(f"    2. Update CHANGELOG.md (add entry for {new_version})")
        print(f"    3. Commit: git commit -am 'chore: bump version to {new_version}'")


if __name__ == "__main__":
    main()
