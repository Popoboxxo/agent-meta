"""Static Admin-UI contract for the ``context-profile`` switch (2a.8, AC-86).

The opt-in profile switch is a top-level ``project.yaml`` key
(``context-profile``): ``viewProject`` renders it in its own panel and the
shared Save button PUTs exactly this section — no new endpoint, no new route.
``compact`` stays opt-in and UNVERIFIED until AC-25 (package 2f), so the help
text says so; a missing or non-``compact`` value keeps ``full`` (AC-35
byte-identity).
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
UI = (REPO_ROOT / "docs" / "ui" / "admin-ui.html").read_text(encoding="utf-8")
SERVER = (REPO_ROOT / "scripts" / "admin-server.py").read_text(encoding="utf-8")


def test_context_profile_section_is_writable() -> None:
    block = re.search(
        r"PROJECT_WRITABLE_SECTIONS: frozenset\[str\] = frozenset\(\{(.*?)\}\)",
        SERVER, flags=re.DOTALL)
    assert block, "PROJECT_WRITABLE_SECTIONS not found in scripts/admin-server.py"
    assert '"context-profile"' in block.group(1), (
        "context-profile must be a writable project.yaml section, otherwise the "
        "Admin UI Save button gets HTTP 400"
    )


def test_profile_defaults_to_full_on_missing_key() -> None:
    assert 'data["context-profile"] === "compact" ? "compact" : "full"' in UI, (
        "a missing or non-'compact' context-profile value must default to "
        "'full' (AC-35 byte-identity)"
    )


def test_profile_rendered_as_full_compact_dropdown() -> None:
    assert '"Context profile", ["full", "compact"], contextProfile' in UI, (
        "context-profile must render as a full|compact dropdown"
    )


def test_profile_persisted_as_own_section() -> None:
    assert '["context-profile", contextProfile],' in UI, (
        "viewProject's Save must persist the context-profile section"
    )


def test_help_text_states_opt_in_unverified_and_scope() -> None:
    assert "Opt-in, UNVERIFIED bis AC-25" in UI
    assert "context-profile.unverified" in UI
    assert "AC-35" in UI
    assert "provider-overrides.<Provider>.context-profile" in UI
