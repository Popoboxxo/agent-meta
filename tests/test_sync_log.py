"""Unit tests for lib.log.SyncLog (#574).

Regression coverage for the info() -> note() rename: the old two-positional
-argument info(target, reason) collided semantically with the stdlib
logging.info(msg, *args) API and produced 44+ PLE1205 linter false
positives. note() replaces it 1:1 with identical recorded output.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.log import SyncLog


def test_note_records_formatted_info_line():
    log = SyncLog()
    log.note("my-target", "some reason")
    assert len(log.infos) == 1
    assert "[INFO]" in log.infos[0]
    assert "my-target" in log.infos[0]
    assert "some reason" in log.infos[0]


def test_note_appends_to_infos_list_in_order():
    log = SyncLog()
    log.note("a", "first")
    log.note("b", "second")
    assert len(log.infos) == 2
    assert "first" in log.infos[0]
    assert "second" in log.infos[1]


def test_info_method_no_longer_exists():
    """info() was removed without a deprecation wrapper (#574 acceptance
    criteria) — callers must use note()."""
    log = SyncLog()
    assert not hasattr(log, "info")
