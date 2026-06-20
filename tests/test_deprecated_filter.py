"""Test suite for deprecated-template filtering (REQ-GEN-01).

Validates that templates with `deprecated: true` in their YAML frontmatter
are excluded from generation, while absent/false fields keep the template
active (backward-compatible default).

Run: python tests/test_deprecated_filter.py
"""

from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.agents import is_deprecated_template, collect_sources  # noqa: E402


# ---------------------------------------------------------------------------
# is_deprecated_template — unit checks
# ---------------------------------------------------------------------------

def check_deprecated_true() -> list[str]:
    """`deprecated: true` must be detected as deprecated."""
    errors: list[str] = []
    content = "---\nname: foo\ndeprecated: true\n---\n\n# Foo\n"
    if not is_deprecated_template(content):
        errors.append("deprecated: true was not detected")
    return errors


def check_deprecated_false() -> list[str]:
    """`deprecated: false` must NOT be treated as deprecated."""
    errors: list[str] = []
    content = "---\nname: foo\ndeprecated: false\n---\n\n# Foo\n"
    if is_deprecated_template(content):
        errors.append("deprecated: false was wrongly treated as deprecated")
    return errors


def check_deprecated_absent() -> list[str]:
    """Missing `deprecated` field defaults to active (backward-compat)."""
    errors: list[str] = []
    content = "---\nname: foo\nversion: 1.0.0\n---\n\n# Foo\n"
    if is_deprecated_template(content):
        errors.append("absent deprecated field was wrongly treated as deprecated")
    return errors


def check_no_frontmatter() -> list[str]:
    """Content without frontmatter must be treated as active."""
    errors: list[str] = []
    if is_deprecated_template("# Just a heading\n"):
        errors.append("content without frontmatter was wrongly treated as deprecated")
    return errors


# ---------------------------------------------------------------------------
# collect_sources — integration check
# ---------------------------------------------------------------------------

def check_se_orchestrator_excluded() -> list[str]:
    """se-orchestrator template has deprecated: true and must be filtered out."""
    errors: list[str] = []
    overrides, _ = collect_sources(_REPO_ROOT, platforms=[])
    if "se-orchestrator" in overrides:
        errors.append(
            "se-orchestrator (deprecated: true) was NOT filtered out of collect_sources"
        )
    # Sanity: a known active generic role must still be present.
    if "orchestrator" not in overrides:
        errors.append("orchestrator (active) is unexpectedly missing from collect_sources")
    return errors


def check_template_file_still_present() -> list[str]:
    """The deprecated template file itself must remain on disk (not deleted)."""
    errors: list[str] = []
    template = _REPO_ROOT / "agents" / "1-generic" / "se-orchestrator.md"
    if not template.exists():
        errors.append(f"deprecated template file missing: {template}")
    return errors


CHECKS = [
    ("deprecated: true detected", check_deprecated_true),
    ("deprecated: false active", check_deprecated_false),
    ("absent field active", check_deprecated_absent),
    ("no frontmatter active", check_no_frontmatter),
    ("se-orchestrator excluded", check_se_orchestrator_excluded),
    ("template file preserved", check_template_file_still_present),
]


# pytest-discoverable wrappers
def test_deprecated_true():
    assert check_deprecated_true() == []


def test_deprecated_false():
    assert check_deprecated_false() == []


def test_deprecated_absent():
    assert check_deprecated_absent() == []


def test_no_frontmatter():
    assert check_no_frontmatter() == []


def test_se_orchestrator_excluded():
    assert check_se_orchestrator_excluded() == []


def test_template_file_preserved():
    assert check_template_file_still_present() == []


def main() -> int:
    failures = 0
    for label, check in CHECKS:
        errs = check()
        if errs:
            failures += 1
            print(f"  FAIL  {label}")
            for e in errs:
                print(f"          {e}")
        else:
            print(f"  ok    {label}")
    if failures:
        print(f"\n{failures} check(s) failed.")
        return 1
    print(f"\nAll {len(CHECKS)} checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
