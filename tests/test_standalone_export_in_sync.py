"""The committed standalone/ export must match what --render-standalone produces.

The export is generated from agents/1-generic and had drifted unnoticed (15 roles
missing) because nothing gated it. Read-only: uses --check, never writes.
"""

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent


def test_standalone_export_is_up_to_date():
    result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py"), "--render-standalone", "--check"],
        cwd=_REPO_ROOT, capture_output=True, text=True, timeout=300,
    )
    assert result.returncode == 0, (
        "standalone/ is stale -- run `python scripts/sync.py --render-standalone` and commit:\n"
        + result.stdout[-1500:]
    )
