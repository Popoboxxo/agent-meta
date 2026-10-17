"""IC-15 Nr. 19 / AC-10: ``--create-ext`` must not write literal ``{{VAR}}``.

Before the fix ``templates/managed-block.md`` was rendered with ``substitute``
only, so a consumer without ``PLATFORM`` / ``RUNTIME`` / ``BUILD_COMMAND`` /
``TEST_COMMAND`` got those literal tokens written into the created extension.
The extension writer now drops every managed-block line that still carries an
unresolved ``{{VAR}}`` — the same rule ``check_unresolved_placeholder`` flags.

Red (before the fix): the created ``<prefix>-<role>-ext.md`` contains the
literal tokens. Green: only the resolved lines survive.

Run: python -m pytest tests/test_create_ext_unresolved.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.consistency import active_set_refs as asr  # noqa: E402
from lib.extensions import create_extension  # noqa: E402
from lib.log import SyncLog  # noqa: E402

_EXT_REL = ".claude/3-project"


def _create(tmp_path: Path, variables: dict) -> Path:
    create_extension(
        project_root=tmp_path,
        config={"project": {"prefix": "tp"}},
        variables=variables,
        role="developer",
        log=SyncLog(),
        dry_run=False,
        agent_meta_root=_REPO_ROOT,
    )
    return tmp_path / _EXT_REL / "tp-developer-ext.md"


def test_create_ext_drops_lines_with_unresolved_variables(tmp_path):
    """Red before the fix: the created file carried the literal tokens."""
    content = _create(tmp_path, {"PROJECT_NAME": "demo"}).read_text(encoding="utf-8")
    assert "{{PLATFORM}}" not in content
    assert "{{RUNTIME}}" not in content
    assert "{{BUILD_COMMAND}}" not in content
    assert "{{TEST_COMMAND}}" not in content
    assert asr._PLACEHOLDER_RE.findall(content) == []


def test_create_ext_keeps_resolved_values(tmp_path):
    """Resolved fields survive — the fix must not empty the whole block."""
    content = _create(
        tmp_path,
        {
            "PROJECT_NAME": "demo",
            "PLATFORM": "Windows",
            "RUNTIME": "Python 3.9",
            "BUILD_COMMAND": "make build",
            "TEST_COMMAND": "make test",
        },
    ).read_text(encoding="utf-8")
    assert "**Projekt:** demo" in content
    assert "Windows" in content
    assert "make test" in content


def test_check_unresolved_placeholder_reports_none_for_extension(tmp_path, monkeypatch):
    """The check that reports unresolved placeholders finds none in the output."""
    _create(tmp_path, {"PROJECT_NAME": "demo"})
    monkeypatch.setattr(
        asr, "_provider_cfg",
        lambda provider: {"agents_dir": _EXT_REL, "agent_ext": ".md"},
    )
    findings = asr.check_unresolved_placeholder(tmp_path, ["Claude"], {}, None)
    assert findings == [], [f.message for f in findings]
