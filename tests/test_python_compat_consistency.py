"""Tests for lib.consistency.python_compat (Python-3.9-floor syntax hazards).

Issue #674 roadmap review: check_py39_union_syntax only scanned
scripts/lib/, so the same PEP 604 mistake slipped into tests/ unnoticed;
a second, previously undetected hazard (a backslash inside an f-string
expression, invalid before Python 3.12) also broke the CI matrix. Both
checks now scan scripts/lib/ AND tests/ — pinned here so a future
regression on either scan scope or detection logic is caught locally
instead of only in CI's 3.9/3.11 matrix jobs.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import lib.consistency.python_compat as python_compat  # noqa: E402
from lib.consistency.python_compat import (  # noqa: E402
    check_fstring_backslash_hazard,
    check_py39_union_syntax,
)


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestPy39UnionSyntax:
    def test_flags_union_annotation_in_scripts_lib(self, tmp_path: Path) -> None:
        _write(tmp_path, "scripts/lib/foo.py", "def f(x: int | None) -> None:\n    pass\n")
        findings = check_py39_union_syntax(tmp_path)
        assert len(findings) == 1
        assert findings[0].check == "python.py39-union-syntax"
        assert findings[0].file == "scripts/lib/foo.py"

    def test_flags_union_annotation_in_tests(self, tmp_path: Path) -> None:
        """The scope gap this check used to have (issue #674 roadmap review)."""
        _write(tmp_path, "tests/test_foo.py", "def f(x: int | None) -> None:\n    pass\n")
        findings = check_py39_union_syntax(tmp_path)
        assert len(findings) == 1
        assert findings[0].file == "tests/test_foo.py"

    def test_future_import_silences_it(self, tmp_path: Path) -> None:
        _write(
            tmp_path, "tests/test_foo.py",
            "from __future__ import annotations\n\ndef f(x: int | None) -> None:\n    pass\n",
        )
        assert check_py39_union_syntax(tmp_path) == []

    def test_runtime_bitwise_or_is_not_flagged(self, tmp_path: Path) -> None:
        """Plain ``|`` outside an annotation (dict-merge, bitwise-or) is untouched."""
        _write(tmp_path, "tests/test_foo.py", "def f():\n    return {'a': 1} | {'b': 2}\n")
        assert check_py39_union_syntax(tmp_path) == []


class TestFstringBackslashHazard:
    def test_flags_backslash_inside_fstring_expression(self, tmp_path: Path) -> None:
        _write(
            tmp_path, "tests/test_foo.py",
            "def f():\n    assert 'p' == f\"p {r'C:\\\\x'}\"\n",
        )
        findings = check_fstring_backslash_hazard(tmp_path)
        assert len(findings) == 1
        assert findings[0].check == "python.fstring-backslash-expr"
        assert findings[0].file == "tests/test_foo.py"

    def test_scans_scripts_lib_too(self, tmp_path: Path) -> None:
        _write(
            tmp_path, "scripts/lib/foo.py",
            "def f():\n    return f\"p {r'C:\\\\x'}\"\n",
        )
        findings = check_fstring_backslash_hazard(tmp_path)
        assert len(findings) == 1
        assert findings[0].file == "scripts/lib/foo.py"

    def test_backslash_in_literal_text_is_not_flagged(self, tmp_path: Path) -> None:
        """A backslash in the f-string's plain text (outside {...}) is legal on every version."""
        _write(tmp_path, "tests/test_foo.py", "def f(name):\n    return f'C:\\\\x {name}'\n")
        assert check_fstring_backslash_hazard(tmp_path) == []

    def test_clean_fstring_expression_is_not_flagged(self, tmp_path: Path) -> None:
        _write(tmp_path, "tests/test_foo.py", "def f(name):\n    return f'hello {name}'\n")
        assert check_fstring_backslash_hazard(tmp_path) == []

    def test_flags_via_syntaxerror_on_pre_312_interpreters(self, tmp_path, monkeypatch) -> None:
        """On Python < 3.12 this hazard IS a SyntaxError -- ast.parse() never
        produces a tree to inspect at all. This suite's own interpreter may
        be 3.12+ (where the pattern parses fine), so the real 3.9/3.11
        behavior is simulated here instead of relying on the local Python
        version (issue #674 roadmap: this exact gap made the check pass
        locally while failing on CI's 3.9/3.11 matrix jobs)."""
        _write(tmp_path, "tests/test_foo.py", "def f():\n    pass\n")

        def _raise(*_args, **_kwargs):
            raise SyntaxError("f-string expression part cannot include a backslash")

        monkeypatch.setattr(python_compat.ast, "parse", _raise)
        findings = check_fstring_backslash_hazard(tmp_path)
        assert len(findings) == 1
        assert findings[0].check == "python.fstring-backslash-expr"

    def test_unrelated_syntax_error_is_not_flagged(self, tmp_path, monkeypatch) -> None:
        """A SyntaxError with a different message is out of this check's scope."""
        _write(tmp_path, "tests/test_foo.py", "def f():\n    pass\n")

        def _raise(*_args, **_kwargs):
            raise SyntaxError("invalid syntax")

        monkeypatch.setattr(python_compat.ast, "parse", _raise)
        assert check_fstring_backslash_hazard(tmp_path) == []
