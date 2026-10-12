"""Template integrity checks: stale ``based-on`` pins (AC-65, IC-32)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.consistency.frontmatter import check_based_on_stale  # noqa: E402
from lib.consistency.report import Severity  # noqa: E402

_PIN = re.compile(r'^based-on:\s*["\']?([^@"\']+)@([^"\'\s]+)', re.M)


def _version(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return str(yaml.safe_load(text.split("---")[1]).get("version"))


def _expected_stale(root: Path) -> set:
    out = set()
    for f in sorted((root / "agents" / "2-platform").glob("*.md")):
        m = _PIN.search(f.read_text(encoding="utf-8"))
        if not m:
            continue
        base = root / "agents" / m.group(1)
        if base.exists() and _version(base) != m.group(2):
            out.add(f.name)
    return out


def test_based_on_stale_matches_computed_deviations():
    findings = check_based_on_stale(ROOT)
    assert {Path(f.file).name for f in findings} == _expected_stale(ROOT)
    assert all(f.severity is Severity.WARNING for f in findings)
    assert all(f.check == "frontmatter.based-on-stale" for f in findings)


def _mk(tmp_path: Path, pin: str) -> Path:
    (tmp_path / "agents" / "1-generic").mkdir(parents=True)
    (tmp_path / "agents" / "2-platform").mkdir(parents=True)
    (tmp_path / "agents" / "1-generic" / "dev.md").write_text(
        '---\nname: dev\nversion: "2.0.0"\n---\nbody\n', encoding="utf-8")
    (tmp_path / "agents" / "2-platform" / "x-dev.md").write_text(
        f'---\nname: x-dev\nversion: "1.0.0"\nbased-on: "{pin}"\n---\nbody\n',
        encoding="utf-8")
    return tmp_path


def test_based_on_stale_fixture_outdated_pin(tmp_path):
    findings = check_based_on_stale(_mk(tmp_path, "1-generic/dev.md@1.0.0"))
    assert len(findings) == 1
    assert findings[0].check == "frontmatter.based-on-stale"
    assert findings[0].severity is Severity.WARNING


def test_based_on_stale_fixture_current_pin(tmp_path):
    assert check_based_on_stale(_mk(tmp_path, "1-generic/dev.md@2.0.0")) == []
