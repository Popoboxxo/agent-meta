"""Unit tests for the context-file topology consistency check (AC-19).

``check_context_topology_consistency`` validates the ``context_file`` topology
configuration — the enum, the adapter-capability registry invariants, the core
reference of each ``per-provider`` adapter and orphaned adapters in ``unified``.
All findings are WARNINGs; the check never raises.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from scripts.lib.consistency.context_topology import (
    check_context_topology_consistency,
)
from scripts.lib.consistency.report import Severity

# A cooperative layout: one provider whose adapter file is distinct from its
# normal context file (the synthetic "future provider" shape).
DIRECT = {
    "Provider": {"context_file": "AGENTS.md"},
}


def _finder(findings, check):
    return [f for f in findings if f.check == check]


def test_invalid_enum_warns():
    """An out-of-enum context_file.topology resolves fail-safe — warn about it."""
    with tempfile.TemporaryDirectory() as tmp:
        findings = check_context_topology_consistency(
            Path(tmp),
            config={"context_file": {"topology": "garbage"}},
            provider_config=DIRECT,
        )
        assert [f.severity for f in findings] == [Severity.WARNING]
        assert findings[0].check == "context.topology"
        assert "garbage" in findings[0].message


def test_adapter_file_collision_warns():
    """Two adapter-capable providers must not share one adapter file."""
    providers = {
        "Alpha": {
            "context_file": "A.md",
            "context_adapter": True,
            "context_adapter_file": "SHARED.adapter.md",
            "context_adapter_import": "@{core}",
            "context_adapter_import_supported": True,
        },
        "Beta": {
            "context_file": "B.md",
            "context_adapter": True,
            "context_adapter_file": "SHARED.adapter.md",
            "context_adapter_import": "@{core}",
            "context_adapter_import_supported": True,
        },
    }
    with tempfile.TemporaryDirectory() as tmp:
        findings = check_context_topology_consistency(
            Path(tmp),
            config={"context_file": {"topology": "per-provider"}},
            provider_config=providers,
        )
        collisions = _finder(findings, "context.adapter_collision")
        assert len(collisions) == 1
        assert collisions[0].severity == Severity.WARNING
        assert "SHARED.adapter.md" in collisions[0].message
        # Valid imports must not add a core-reference finding.
        assert _finder(findings, "context.adapter_core_reference") == []


def test_missing_core_reference_warns():
    """A per-provider adapter whose import renders no core reference warns."""
    providers = {
        "Provider": {
            "context_file": "AGENTS.md",
            "context_adapter": True,
            "context_adapter_file": "ADAPTER.md",
            "context_adapter_import": "see the docs",
            "context_adapter_import_supported": True,
        },
    }
    with tempfile.TemporaryDirectory() as tmp:
        findings = check_context_topology_consistency(
            Path(tmp),
            config={"context_file": {"topology": "per-provider"}},
            provider_config=providers,
        )
        core = _finder(findings, "context.adapter_core_reference")
        assert len(core) == 1
        assert core[0].severity == Severity.WARNING
        assert "AGENTS.md" in core[0].message


def test_orphaned_adapter_in_unified_warns():
    """An existing dedicated adapter file without an index entry is orphaned."""
    providers = {
        "Provider": {
            "context_file": "FUTURE.md",
            "context_adapter": True,
            "context_adapter_file": "FUTURE.adapter.md",
        },
    }
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "FUTURE.adapter.md").write_text("orphan\n", encoding="utf-8")
        findings = check_context_topology_consistency(
            root,
            config={"context_file": {"topology": "unified"}},
            provider_config=providers,
        )
        orphans = _finder(findings, "context.adapter_orphan")
        assert len(orphans) == 1
        assert orphans[0].severity == Severity.WARNING
        assert orphans[0].file == "FUTURE.adapter.md"


def test_consistent_config_has_no_finding():
    """A valid per-provider adapter (file == context file) yields no finding."""
    providers = {
        "Provider": {
            "context_file": "CLAUDE.md",
            "context_adapter": True,
            "context_adapter_file": "CLAUDE.md",
            "context_adapter_import": "@{core}",
            "context_adapter_import_supported": True,
        },
    }
    with tempfile.TemporaryDirectory() as tmp:
        findings = check_context_topology_consistency(
            Path(tmp),
            config={"context_file": {"topology": "per-provider", "core_file": "AGENTS.md"}},
            provider_config=providers,
        )
        assert findings == []
