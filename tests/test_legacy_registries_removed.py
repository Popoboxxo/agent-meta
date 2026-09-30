from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

_SUFFIXES = (".py", ".sh", ".yaml", ".yml", ".md")
_NEEDLE = "mcp-registry.yaml"


def _scan(roots):
    offenders = []
    for root in roots:
        for path in (REPO_ROOT / root).rglob("*"):
            if not path.is_file() or path.suffix not in _SUFFIXES:
                continue
            if _NEEDLE in path.read_text(encoding="utf-8"):
                offenders.append(path.relative_to(REPO_ROOT).as_posix())
    return offenders


def test_legacy_registry_files_deleted():
    assert not (REPO_ROOT / "config" / "mcp-registry.yaml").exists()
    assert not (REPO_ROOT / "config" / "external-tools-registry.yaml").exists()


def test_catalog_is_sole_source():
    assert (REPO_ROOT / "config" / "plugin-catalog.yaml").exists()


def test_no_source_reads_deleted_paths():
    offenders = []
    for py in (REPO_ROOT / "scripts").rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        for needle in ('config/mcp-registry.yaml"', 'config/external-tools-registry.yaml"'):
            if needle in text:
                offenders.append(f"{py.relative_to(REPO_ROOT)}: {needle}")
    assert not offenders, offenders


def test_no_live_source_references_deleted_registry():
    """Hand-authored framework sources only. `tests/` and `docs/` are not
    scanned (they are not live sources; the AC-C2 tolerance list covers them),
    so no allowlist is needed here — nothing below the scan roots is excluded.
    Generated provider artifacts live in gitignored roots and are checked by
    test_generated_provider_artifacts_use_current_registry_reference."""
    scan_roots = ("scripts", "hooks", "rules", "config", "agents")
    offenders = _scan(scan_roots)
    assert not offenders, offenders


def test_generated_provider_artifacts_use_current_registry_reference():
    """Generated MCP channel artifacts (.claude/skills/, .opencode/skills/,
    .gemini/rules/) live in gitignored roots (.gitignore:13,14,16) and exist
    only after scripts/sync.py has run. On a fresh checkout the scan would be
    silently empty, so skip explicitly instead of passing vacuously; when files
    are present, assert hard."""
    generated_roots = (".claude/skills", ".opencode/skills", ".gemini/rules")
    files = [
        path
        for root in generated_roots
        for path in (REPO_ROOT / root).rglob("*")
        if path.is_file() and path.suffix in _SUFFIXES
    ]
    if not files:
        pytest.skip("generated roots absent (gitignored); run scripts/sync.py")

    offenders = []
    footer_found = False
    for path in files:
        text = path.read_text(encoding="utf-8")
        if _NEEDLE in text:
            offenders.append(path.relative_to(REPO_ROOT).as_posix())
        if "config/plugin-catalog.yaml" in text:
            footer_found = True
    assert not offenders, offenders
    assert footer_found, "no generated artifact references config/plugin-catalog.yaml"
