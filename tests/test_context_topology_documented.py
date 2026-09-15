"""Documentation guard for the ``context_file.topology`` switch (Task 14).

Plan: ``docs/plans/2026-09-13-context-file-modes.md`` → Task 14 (AC-10/AC-11 docs).
Trace anchor: ``SPEC-CONTEXT-FILE-MODES-2026-09-13``.

The topology axis (``unified`` / ``per-provider``) must be discoverable where a
developer looks for context-file behavior: the provider overview
(``docs/providers/multi-provider.md``) and the context-block inventory
(``docs/guides/context-block-inventory.md``). Both must name the switch, its two
modes, and the distinction from the density ``context_file.mode``; the
Gemini/Antigravity fallback (c) must be documented with the F-RULESLOC spike
reference. These are documentation assertions only — no behavioral coupling.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

_DOCS = (
    REPO_ROOT / "docs" / "providers" / "multi-provider.md",
    REPO_ROOT / "docs" / "guides" / "context-block-inventory.md",
)

_SPIKE = "docs/spikes/2026-09-14-f-rulesloc-gemini-rules-channel.md"
_TRACE_ANCHOR = "SPEC-CONTEXT-FILE-MODES-2026-09-13"


def test_topology_switch_documented():
    """Both docs name the switch, both modes and the density distinction."""
    for path in _DOCS:
        content = path.read_text(encoding="utf-8")
        assert "context_file.topology" in content, path
        assert "unified" in content, path
        assert "per-provider" in content, path
        assert "context_file.mode" in content, path
        assert "Dichte" in content or "density" in content, path


def test_fallback_c_documented():
    """The Gemini/Antigravity fallback (c) and its F-RULESLOC verdict."""
    multi_provider = _DOCS[0].read_text(encoding="utf-8")
    inventory = _DOCS[1].read_text(encoding="utf-8")

    assert "Fallback (c)" in multi_provider, "fallback (c) must be documented"
    assert _SPIKE in multi_provider, "the F-RULESLOC spike must be referenced"
    assert _TRACE_ANCHOR in multi_provider, "the trace anchor must be present"

    assert "Fallback (c)" in inventory, "fallback (c) must be documented"
    assert _SPIKE in inventory, "the F-RULESLOC spike must be referenced"
