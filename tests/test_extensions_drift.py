"""#1269 part 1: hash-based drift protection for extension blocks."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from lib.extensions import update_extensions  # noqa: E402
from lib.log import SyncLog  # noqa: E402
from lib.managed_block import has_drift  # noqa: E402

EXT = ".claude/3-project"
VARS = {"PROJECT_NAME": "P"}


def _setup(tmp_path, name, content=None):
    d = tmp_path / EXT
    d.mkdir(parents=True)
    f = d / name
    if content is not None:
        f.write_text(content, encoding="utf-8")
    return f


def _run(tmp_path, **kw):
    log = SyncLog()
    res = update_extensions(tmp_path, VARS, log, False, ROOT, **kw)
    return log, res


def _fresh(tmp_path):
    f = _setup(tmp_path, "am-developer-ext.md", "<!-- agent-meta:managed-begin -->\nold\n"
               "<!-- agent-meta:managed-end -->\n\nMine\n")
    return f


def test_happy_legacy_marker_upgraded_with_hash(tmp_path):
    f = _fresh(tmp_path)
    _run(tmp_path)
    text = f.read_text(encoding="utf-8")
    assert "managed-begin v=" in text and "Mine" in text
    assert not has_drift(text)
    # second run is a no-op
    before = text
    _run(tmp_path)
    assert f.read_text(encoding="utf-8") == before


def test_drift_skips_unless_force(tmp_path):
    f = _fresh(tmp_path)
    _run(tmp_path)
    edited = f.read_text(encoding="utf-8").replace("Project-specific additions", "Hand additions")
    f.write_text(edited, encoding="utf-8")
    _, drifted = _run(tmp_path)
    assert drifted == [f.name] and f.read_text(encoding="utf-8") == edited
    _run(tmp_path, force=True)
    assert "Hand additions" not in f.read_text(encoding="utf-8")


def test_missing_marker_warns_and_does_not_prepend(tmp_path):
    f = _setup(tmp_path, "am-developer-ext.md", "just mine\n")
    _, drifted = _run(tmp_path)
    assert f.read_text(encoding="utf-8") == "just mine\n" and drifted == [f.name]


def test_orphan_role_warns(tmp_path):
    _setup(tmp_path, "am-nonexistent-role-ext.md", "x\n")
    log, _ = _run(tmp_path)
    assert any("orphan" in str(w) for w in log.warnings)


def test_role_filter_only_touches_that_role(tmp_path):
    a = _setup(tmp_path, "am-developer-ext.md", "<!-- agent-meta:managed-begin -->\nold\n"
               "<!-- agent-meta:managed-end -->\n")
    b = a.parent / "am-tester-ext.md"
    b.write_text(a.read_text(encoding="utf-8"), encoding="utf-8")
    _run(tmp_path, role="tester")
    assert "v=" in b.read_text(encoding="utf-8")
    assert "v=" not in a.read_text(encoding="utf-8")


def test_cli_flags_and_check_exit(tmp_path):
    import sync  # noqa: F401  (argparse wiring importable)
    p = sync._build_arg_parser().parse_args(["--update-ext", "--check", "--force", "--role", "x"])
    assert p.update_ext and p.check and p.force and p.role == "x"


def test_role_filter_is_not_suffix_overmatching(tmp_path):
    a = _setup(tmp_path, "am-senior-developer-ext.md", "<!-- agent-meta:managed-begin -->\nold\n"
               "<!-- agent-meta:managed-end -->\n")
    _run(tmp_path, role="developer")
    assert "v=" not in a.read_text(encoding="utf-8")


def test_role_without_match_warns(tmp_path):
    _setup(tmp_path, "am-developer-ext.md", "x\n")
    log, _ = _run(tmp_path, role="tester")
    assert any("no extension file matches" in str(w) for w in log.warnings)


def test_validate_rejects_provider_and_out_but_allows_strict():
    import pytest
    import sync
    parser = sync._build_arg_parser()
    sync._validate_doctor_flags(parser, parser.parse_args(["--validate", "--strict"]))
    for extra in (["--provider", "Claude"], ["--out", "x"]):
        with pytest.raises(SystemExit):
            sync._validate_doctor_flags(parser, parser.parse_args(["--validate", *extra]))
