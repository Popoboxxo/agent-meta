"""Tests for the reproducible ``AGENT_META_DATE`` resolver (#752).

A non-deterministic generation date made any committed-context drift check
(``sync.py --check``) fail every day after the last sync. The resolver prefers
``SOURCE_DATE_EPOCH``, then the CHANGELOG release date of the current version,
then falls back to today.

Run: python -m pytest tests/test_agent_meta_date.py -v
"""

import sys
from datetime import datetime
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.config import _resolve_agent_meta_date
from lib import config as config_mod


class _FixedDateTime:
    """Deterministic stand-in for `datetime` in the now() fallback tests."""

    @classmethod
    def now(cls, *a, **k):
        return datetime(2026, 7, 1)

    @classmethod
    def fromtimestamp(cls, *a, **k):
        return datetime.fromtimestamp(*a, **k)


def test_source_date_epoch_is_honored(tmp_path, monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")  # 2023-11-14T22:13:20Z
    assert _resolve_agent_meta_date(tmp_path) == "2023-11-14"


def test_changelog_release_date_used_when_env_unset(tmp_path, monkeypatch):
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    (tmp_path / "VERSION").write_text("1.2.3\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n## [1.2.3] — 2025-04-05\n", encoding="utf-8",
    )
    assert _resolve_agent_meta_date(tmp_path) == "2025-04-05"


@pytest.mark.parametrize("dash", ["—", "–", "-"])
def test_changelog_dash_variants(tmp_path, monkeypatch, dash):
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    (tmp_path / "VERSION").write_text("2.0.0\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        f"## [2.0.0] {dash} 2024-12-31\n", encoding="utf-8",
    )
    assert _resolve_agent_meta_date(tmp_path) == "2024-12-31"


def test_fallback_to_today_when_nothing_resolvable(tmp_path, monkeypatch):
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    monkeypatch.setattr(config_mod, "datetime", _FixedDateTime)
    assert _resolve_agent_meta_date(tmp_path) == "2026-07-01"


def test_version_without_exact_changelog_heading_uses_most_recent_release(tmp_path, monkeypatch):
    """VERSION bumped before its CHANGELOG heading exists must not fall back to now()."""
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    (tmp_path / "VERSION").write_text("2.0.0\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n## [1.1.0] — 2025-04-05\n\n## [1.0.0] — 2024-01-01\n",
        encoding="utf-8",
    )
    assert _resolve_agent_meta_date(tmp_path) == "2025-04-05"


def test_linked_changelog_heading_matches(tmp_path, monkeypatch):
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    (tmp_path / "VERSION").write_text("1.1.0\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        "## [1.1.0](https://example.com/releases/1.1.0) — 2025-06-07\n", encoding="utf-8",
    )
    assert _resolve_agent_meta_date(tmp_path) == "2025-06-07"


def test_leading_v_in_version_is_normalized(tmp_path, monkeypatch):
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    (tmp_path / "VERSION").write_text("v1.1.0\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("## [1.1.0] — 2025-08-09\n", encoding="utf-8")
    assert _resolve_agent_meta_date(tmp_path) == "2025-08-09"


def test_unreadable_version_falls_through_without_raising(tmp_path, monkeypatch):
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    monkeypatch.setattr(config_mod, "datetime", _FixedDateTime)
    (tmp_path / "VERSION").mkdir()  # read_text -> IsADirectoryError (OSError)
    (tmp_path / "CHANGELOG.md").write_text("## [1.1.0] — 2025-01-01\n", encoding="utf-8")
    # must not raise; falls through to the deterministic fallback
    assert _resolve_agent_meta_date(tmp_path) == "2026-07-01"


def test_malformed_source_date_epoch_falls_through(tmp_path, monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "not-an-int")
    (tmp_path / "VERSION").write_text("3.4.5\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("## [3.4.5] — 2026-01-02\n", encoding="utf-8")
    # no raise; falls through to the CHANGELOG release date
    assert _resolve_agent_meta_date(tmp_path) == "2026-01-02"
