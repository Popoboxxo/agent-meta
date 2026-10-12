"""Template integrity checks: stale ``based-on`` pins (AC-65, IC-32)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.consistency.frontmatter import check_based_on_stale  # noqa: E402
from lib.frontmatter import split_frontmatter  # noqa: E402
from lib.consistency import placeholders as _ph  # noqa: E402
from lib.consistency.report import Severity  # noqa: E402

_PIN = re.compile(r'^based-on:\s*["\']?([^@"\']+)@([^"\'\s]+)', re.M)


def _version(path: Path) -> str:
    block, _body = split_frontmatter(path.read_text(encoding="utf-8"))
    return str(yaml.safe_load(block.strip().strip("-")).get("version"))


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


def test_based_on_stale_pin_without_at_is_skipped(tmp_path):
    assert check_based_on_stale(_mk(tmp_path, "1-generic/dev.md")) == []


def test_based_on_stale_missing_base_is_skipped(tmp_path):
    assert check_based_on_stale(_mk(tmp_path, "1-generic/gone.md@1.0.0")) == []


def test_based_on_stale_compares_versions_as_exact_strings(tmp_path):
    """Documented boundary: ``1.0`` vs ``1.0.0`` is reported (no semver normalization)."""
    root = _mk(tmp_path, "1-generic/dev.md@2.0")
    assert len(check_based_on_stale(root)) == 1


def test_builder_known_set_real_repo_clean():
    assert _ph.check_builder_known_set(ROOT) == []


def test_builder_known_set_unregistered_builder_var_is_error(tmp_path, monkeypatch):
    monkeypatch.setattr(
        _ph, "BUILDERS",
        list(_ph.BUILDERS) + [lambda cfg, root, proj: {"BRAND_NEW_VAR": "x"}],
        raising=False)
    findings = _ph.check_builder_known_set(tmp_path)
    hits = [f for f in findings if "BRAND_NEW_VAR" in f.message]
    assert len(hits) == 1
    assert hits[0].severity is Severity.ERROR
    assert hits[0].check == "placeholders.builder-known-set"


def test_builder_known_set_unsupplied_template_placeholder_is_error(tmp_path):
    (tmp_path / "agents" / "1-generic").mkdir(parents=True)
    (tmp_path / "agents" / "1-generic" / "a.md").write_text(
        "---\nname: a\n---\nUse {{NOT_A_BUILDER_VAR}} and {{PREFIX}}.\n",
        encoding="utf-8")
    findings = _ph.check_builder_known_set(tmp_path)
    assert [f.file for f in findings if "NOT_A_BUILDER_VAR" in f.message] == [
        "agents/1-generic/a.md"]
    assert not any("'{{PREFIX}}'" in f.message for f in findings)


# --- templates.provider-literal (IC-32) ---

from lib.consistency.provider_literals import check_provider_literal  # noqa: E402


def _mk_literal_repo(tmp_path: Path, body: str, allow=()) -> Path:
    (tmp_path / "config").mkdir()
    (tmp_path / "agents" / "1-generic").mkdir(parents=True)
    (tmp_path / "config" / "ai-providers.yaml").write_text(
        "providers:\n  Acme:\n    context_file: ACME.md\n"
        "    provider_root_dirs:\n    - .acme/\n", encoding="utf-8")
    allow_yaml = "".join(f"  - '{a}'\n" for a in allow)
    (tmp_path / "config" / "active-set-references.yaml").write_text(
        "provider_literal_allow:\n" + (allow_yaml or "  []\n"), encoding="utf-8")
    (tmp_path / "agents" / "1-generic" / "a.md").write_text(body, encoding="utf-8")
    return tmp_path


def test_provider_literal_outside_example_is_warning(tmp_path):
    root = _mk_literal_repo(tmp_path, "Read .acme/rules and ACME.md.\n")
    findings = check_provider_literal(root)
    assert len(findings) == 1
    assert findings[0].check == "templates.provider-literal"
    assert findings[0].severity is Severity.WARNING
    assert ".acme/" in findings[0].message and "ACME.md" in findings[0].message


def test_provider_literal_inside_example_block_is_ignored(tmp_path):
    body = ("> **Example (provider-specific):**\n> Use .acme/ and Acme.\n\n"
            "Plain text.\n")
    assert check_provider_literal(_mk_literal_repo(tmp_path, body)) == []


def test_provider_literal_after_example_block_is_flagged(tmp_path):
    body = "> **Example (provider-specific):**\n> .acme/\n\nBack to Acme.\n"
    findings = check_provider_literal(_mk_literal_repo(tmp_path, body))
    assert len(findings) == 1 and "line 4" in findings[0].message


def test_provider_literal_allowlisted_file_is_ignored(tmp_path):
    root = _mk_literal_repo(tmp_path, "Acme here.\n", allow=["agents/1-generic/a.md"])
    assert check_provider_literal(root) == []
