"""#1198: single-brace known variables are flagged; runtime placeholders are not."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.consistency import placeholders as ph  # noqa: E402


def _mk(tmp_path, text):
    d = tmp_path / "agents" / "1-generic"
    d.mkdir(parents=True)
    (d / "a.md").write_text(text, encoding="utf-8")
    return tmp_path


def test_known_single_brace_is_error(tmp_path):
    f = ph.check_single_brace_known_vars(_mk(tmp_path, "Dir {SE_BASE_DIR}/x\n"))
    assert [x.file for x in f] == ["agents/1-generic/a.md"]
    assert f[0].check == "placeholders.single-brace"


def test_runtime_placeholders_and_double_brace_ignored(tmp_path):
    root = _mk(tmp_path, "{parent_path} {FolderName} {{SE_BASE_DIR}} `{SE_BASE_DIR}`\n")
    assert ph.check_single_brace_known_vars(root) == []


def test_real_repo_clean():
    assert ph.check_single_brace_known_vars(ROOT) == []
