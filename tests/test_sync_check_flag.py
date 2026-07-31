"""Regression test: --check must force --dry-run so CI never gets real writes.

Run: python -m pytest tests/test_sync_check_flag.py -v
"""

import sys
from argparse import Namespace
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from sync import _normalize_check_dry_run


def test_check_without_dry_run_forces_dry_run():
    args = Namespace(check=True, dry_run=False)
    _normalize_check_dry_run(args)
    assert args.dry_run is True


def test_check_with_dry_run_stays_dry_run():
    args = Namespace(check=True, dry_run=True)
    _normalize_check_dry_run(args)
    assert args.dry_run is True


def test_no_check_leaves_dry_run_untouched():
    args = Namespace(check=False, dry_run=False)
    _normalize_check_dry_run(args)
    assert args.dry_run is False
