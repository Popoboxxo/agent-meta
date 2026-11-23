"""Regression tests for issue #1203: --label / --labels flag collision.

`--label` is the backup-archive description flag.  #1188 proposes a
`--labels` taxonomy flag; with argparse abbreviation enabled the two could
silently resolve to the same action.  These tests lock in unambiguous parsing
and the explicit `--backup-label` alias that reserves `--labels`.

Run: python -m pytest tests/test_sync_label_collision.py -v
"""

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from sync import _build_arg_parser  # noqa: E402


def test_backup_label_exact_flag_still_parses():
    """Backward compatibility: existing `--label TEXT` users are unaffected."""
    args = _build_arg_parser().parse_args(["--label", "release-42"])
    assert args.label == "release-42"


def test_labels_token_does_not_silently_bind_to_label_action():
    """`--labels` must never be swallowed as an abbreviation of `--label`."""
    with pytest.raises(SystemExit) as exc:
        _build_arg_parser().parse_args(["--labels", "bug"])
    assert exc.value.code == 2


def test_backup_label_alias_parses():
    """Unambiguous alias points at the same destination as `--label`."""
    args = _build_arg_parser().parse_args(["--backup-label", "release-42"])
    assert args.label == "release-42"


def test_backup_and_label_still_compose():
    """Backup mode plus description remains a valid combination."""
    args = _build_arg_parser().parse_args(
        ["--backup", "claude", "--label", "nightly"]
    )
    assert args.backup == ["claude"]
    assert args.label == "nightly"
