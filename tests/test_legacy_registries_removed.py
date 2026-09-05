from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_legacy_registry_files_deleted():
    assert not (REPO_ROOT / "config" / "mcp-registry.yaml").exists()
    assert not (REPO_ROOT / "config" / "external-tools-registry.yaml").exists()


def test_catalog_is_sole_source():
    assert (REPO_ROOT / "config" / "plugin-catalog.yaml").exists()


def test_no_source_reads_deleted_paths():
    # scan scripts/ for a live load of the deleted framework files (fixtures ok)
    offenders = []
    for py in (REPO_ROOT / "scripts").rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        for needle in ('config/mcp-registry.yaml"', 'config/external-tools-registry.yaml"'):
            if needle in text:
                offenders.append(f"{py.relative_to(REPO_ROOT)}: {needle}")
    assert not offenders, offenders
