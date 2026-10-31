"""Static AST guard: hook test modules isolate ``cwd`` and bound every call.

IC-6 of ``SPEC-test-hygiene-945``. This module never spawns a process and
never writes into the repository: it parses the nine P1 hook-test modules with
:mod:`ast` and reports missing isolation keywords.

Rules, applied to every ``subprocess.run`` / ``call`` / ``check_output`` /
``check_call`` / ``Popen`` call in :data:`SCAN_SET`:

1. ``cwd=`` must be present and must not be the literal ``None``.
2. ``timeout=`` must be present and must not be the literal ``None``.
   ``Popen`` is exempt -- it has no ``timeout`` parameter and is allowlisted
   in P3/IC-11 (the scan set contains no ``Popen`` today).
3. ``cwd`` must not bind the checkout itself (``cwd=str(_REPO_ROOT)``): the
   only allowed project roots are ``tmp_path`` fixtures and the containment
   decoy (ADR-3).
4. Imports are resolved (``import subprocess as sp``,
   ``from subprocess import run``). A ``**kwargs`` spread that cannot be
   resolved fails closed with a finding.
5. No module may create its project root at import time with
   ``tempfile.mkdtemp`` or register ``atexit`` cleanup at module level -- the
   root belongs to a module-scoped fixture (IC-3).

Non-assurance: the guard proves keyword presence, not that ``cwd`` points at
a ``tmp_path`` directory (ADR-3, the runtime tests and the CI digest carry
that) and not that a timeout value is sensible. It also does not prove that
the nine modules are *executed* under the fixture, only that the call sites
carry the keywords.
"""

import ast
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

#: The nine P1 hook-test modules (IC-6 scan set), relative to the repo root.
SCAN_SET = (
    "tests/test_orchestrator_guard_hook.py",
    "tests/test_hook_common_lib.py",
    "tests/test_graphify_guard_hooks.py",
    "tests/test_dod_push_check_hook.py",
    "tests/test_artifact_freshness_hook.py",
    "tests/test_pre_release_check_hook.py",
    "tests/test_auto_github_release_hook.py",
    "tests/test_release_gate_checksums.py",
    "tests/test_repo_containment_hook.py",
)

_SUBPROCESS_CALLS = frozenset({"run", "call", "check_output", "check_call", "Popen"})
_TIMEOUT_EXEMPT = frozenset({"Popen"})
_REPO_ROOT_FALLBACK_NAMES = frozenset({"_REPO_ROOT", "REPO_ROOT"})
_ROOT_WRAPPERS = frozenset({"str", "os.fspath", "Path", "PurePath"})
_LINE_PATTERN = re.compile(r":(\d+): ")


def _is_none_literal(node):
    """True for the literal ``None`` (never for a name that happens to be it)."""
    return isinstance(node, ast.Constant) and node.value is None


def _mentions_name(node, name):
    """True when *node* contains a ``Name`` load of *name* (e.g. ``__file__``)."""
    return any(
        isinstance(child, ast.Name) and child.id == name for child in ast.walk(node)
    )


def _collect_aliases(tree):
    """Resolve the import spellings used by the scan set (and by the tests)."""
    module_aliases = set()
    call_aliases = {}
    tempfile_aliases = set()
    atexit_aliases = set()
    special_aliases = {}
    star_imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound = alias.asname or alias.name
                if alias.name == "subprocess":
                    module_aliases.add(bound)
                elif alias.name == "tempfile":
                    tempfile_aliases.add(bound)
                elif alias.name == "atexit":
                    atexit_aliases.add(bound)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            if node.module == "subprocess":
                for alias in node.names:
                    if alias.name == "*":
                        star_imports.append(node)
                    elif alias.name in _SUBPROCESS_CALLS:
                        call_aliases[alias.asname or alias.name] = alias.name
            elif node.module == "tempfile":
                for alias in node.names:
                    if alias.name in {"mkdtemp", "TemporaryDirectory"}:
                        special_aliases[alias.asname or alias.name] = (
                            "tempfile." + alias.name
                        )
            elif node.module == "atexit":
                for alias in node.names:
                    if alias.name == "register":
                        special_aliases[alias.asname or alias.name] = "atexit.register"

    return (
        module_aliases,
        call_aliases,
        tempfile_aliases,
        atexit_aliases,
        special_aliases,
        star_imports,
    )


def _collect_repo_root_names(tree):
    """Names bound to the checkout root (any module-level ``...__file__...``)."""
    names = set(_REPO_ROOT_FALLBACK_NAMES)
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if value is not None and _mentions_name(value, "__file__"):
                for target in targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)
    return names


def _binds_repo_root(node, repo_root_names):
    """True for ``_REPO_ROOT`` and ``str(_REPO_ROOT)``-style wrappers."""
    if isinstance(node, ast.Name):
        return node.id in repo_root_names
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in _ROOT_WRAPPERS
        and node.args
    ):
        return _binds_repo_root(node.args[0], repo_root_names)
    return False


class _GuardVisitor(ast.NodeVisitor):
    """Walk the AST once, tracking the enclosing function for finding text."""

    def __init__(self, filename, aliases, repo_root_names):
        (
            self.module_aliases,
            self.call_aliases,
            self.tempfile_aliases,
            self.atexit_aliases,
            self.special_aliases,
            self.star_imports,
        ) = aliases
        self.filename = filename
        self.repo_root_names = repo_root_names
        self.findings = []
        self._scope = ["<module>"]

    # -- scope tracking -------------------------------------------------
    def visit_FunctionDef(self, node):
        self._scope.append(node.name)
        self.generic_visit(node)
        self._scope.pop()

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    # -- checks ---------------------------------------------------------
    def visit_Call(self, node):
        kind = self._classify(node.func)
        if kind is not None:
            self._check_subprocess_call(node, kind)
        else:
            self._check_import_time_call(node)
        self.generic_visit(node)

    def _classify(self, func):
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if (
                func.value.id in self.module_aliases
                and func.attr in _SUBPROCESS_CALLS
            ):
                return func.attr
        if isinstance(func, ast.Name):
            return self.call_aliases.get(func.id)
        return None

    def _special_target(self, func):
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id in self.tempfile_aliases and func.attr in {
                "mkdtemp",
                "TemporaryDirectory",
            }:
                return "tempfile." + func.attr
            if func.value.id in self.atexit_aliases and func.attr == "register":
                return "atexit.register"
        if isinstance(func, ast.Name):
            return self.special_aliases.get(func.id)
        return None

    def _add(self, node, message):
        self.findings.append(
            "{}:{}: {}: {}".format(
                self.filename, node.lineno, self._scope[-1], message
            )
        )

    def _check_subprocess_call(self, node, kind):
        label = "subprocess.{}()".format(kind)
        keywords = {kw.arg: kw.value for kw in node.keywords if kw.arg is not None}
        spread = any(kw.arg is None for kw in node.keywords)

        if spread:
            # Fail closed: an unresolvable spread may hide cwd=/timeout=.
            self._add(
                node,
                "{} passes **kwargs; cwd=/timeout= cannot be verified "
                "(fail closed)".format(label),
            )
            return

        if "cwd" not in keywords:
            self._add(node, "{} is missing cwd=".format(label))
        elif _is_none_literal(keywords["cwd"]):
            self._add(node, "{} passes cwd=None".format(label))
        elif _binds_repo_root(keywords["cwd"], self.repo_root_names):
            self._add(
                node,
                "{} passes cwd bound to the checkout; use a fixture or the "
                "decoy root (ADR-3)".format(label),
            )

        if kind in _TIMEOUT_EXEMPT:
            return
        if "timeout" not in keywords:
            self._add(node, "{} is missing timeout=".format(label))
        elif _is_none_literal(keywords["timeout"]):
            self._add(node, "{} passes timeout=None".format(label))

    def _check_import_time_call(self, node):
        if len(self._scope) != 1:
            return
        target = self._special_target(node.func)
        if target in {"tempfile.mkdtemp", "tempfile.TemporaryDirectory"}:
            self._add(
                node,
                "import-time {}() creates a project root; bind it in a "
                "module-scoped fixture (IC-3)".format(target),
            )
        elif target == "atexit.register":
            self._add(
                node,
                "import-time atexit.register() leaks cleanup; bind the root "
                "in a module-scoped fixture (IC-3)",
            )

    def collect_star_imports(self):
        for node in self.star_imports:
            self._add(
                node,
                "star-import from subprocess defeats alias resolution "
                "(fail closed)",
            )


def find_violations_in_source(source, filename="<source>"):
    """Return the guard findings for *source* (empty list == clean)."""
    tree = ast.parse(source, filename=filename)
    aliases = _collect_aliases(tree)
    visitor = _GuardVisitor(filename, aliases, _collect_repo_root_names(tree))
    visitor.collect_star_imports()
    visitor.visit(tree)
    return sorted(visitor.findings, key=lambda finding: _line_of(finding))


def _line_of(finding):
    """Sort key: the ``:<line>: `` fragment of a finding (0 if absent)."""
    match = _LINE_PATTERN.search(finding)
    return int(match.group(1)) if match else 0


def find_violations(module_path):
    """Return the guard findings for a module file (empty list == clean)."""
    path = Path(module_path)
    return find_violations_in_source(
        path.read_text(encoding="utf-8"), filename=str(path)
    )


@pytest.mark.parametrize("module", SCAN_SET)
def test_every_call_sets_cwd(module):
    findings = find_violations(REPO_ROOT / module)
    assert findings == [], "hook calls without cwd=:\n" + "\n".join(findings)


@pytest.mark.parametrize("module", SCAN_SET)
def test_every_call_sets_non_none_timeout(module):
    findings = find_violations(REPO_ROOT / module)
    assert findings == [], "hook calls without timeout=:\n" + "\n".join(findings)


# --- Scanner self-tests (string sources only; no repo write, no hook run) ---


def test_missing_timeout_is_reported():
    source = (
        "import subprocess\n"
        "def run_it():\n"
        "    return subprocess.run(['echo'], cwd='/tmp/project')\n"
    )
    findings = find_violations_in_source(source, filename="synthetic.py")
    assert len(findings) == 1, findings
    assert "synthetic.py:3: run_it:" in findings[0]
    assert "missing timeout=" in findings[0]


def test_timeout_none_is_reported():
    source = (
        "import subprocess\n"
        "def run_it():\n"
        "    return subprocess.run(['echo'], cwd='/tmp/project', timeout=None)\n"
    )
    findings = find_violations_in_source(source, filename="synthetic.py")
    assert len(findings) == 1, findings
    assert "passes timeout=None" in findings[0]


def test_alias_import_is_resolved():
    source = (
        "import subprocess as sp\n"
        "def run_it():\n"
        "    return sp.run(['echo'], cwd='/tmp/project')\n"
    )
    findings = find_violations_in_source(source, filename="synthetic.py")
    assert len(findings) == 1, findings
    assert "subprocess.run() is missing timeout=" in findings[0]


def test_from_import_is_resolved():
    source = (
        "from subprocess import run\n"
        "def run_it():\n"
        "    return run(['echo'], cwd='/tmp/project')\n"
    )
    findings = find_violations_in_source(source, filename="synthetic.py")
    assert len(findings) == 1, findings
    assert "subprocess.run() is missing timeout=" in findings[0]


def test_kwargs_spread_fails_closed():
    source = (
        "import subprocess\n"
        "def run_it(**kwargs):\n"
        "    return subprocess.run(['echo'], **kwargs)\n"
    )
    findings = find_violations_in_source(source, filename="synthetic.py")
    assert len(findings) == 1, findings
    assert "**kwargs" in findings[0]
    assert "fail closed" in findings[0]


def test_popen_is_exempt_from_the_timeout_rule_but_needs_cwd():
    exempt = (
        "import subprocess\n"
        "def start():\n"
        "    return subprocess.Popen(['echo'], cwd='/tmp/project')\n"
    )
    assert find_violations_in_source(exempt, filename="synthetic.py") == []

    missing = (
        "import subprocess\n"
        "def start():\n"
        "    return subprocess.Popen(['echo'])\n"
    )
    findings = find_violations_in_source(missing, filename="synthetic.py")
    assert len(findings) == 1, findings
    assert "subprocess.Popen() is missing cwd=" in findings[0]
    assert "timeout" not in findings[0]


def test_scan_set_lists_nine_existing_modules():
    assert len(SCAN_SET) == 9
    assert len(set(SCAN_SET)) == 9
    for module in SCAN_SET:
        assert module.startswith("tests/"), module
        assert (REPO_ROOT / module).is_file(), module


def test_guard_has_teeth_on_a_stripped_real_module(tmp_path):
    source = (REPO_ROOT / "tests" / "test_pre_release_check_hook.py").read_text(
        encoding="utf-8"
    )
    stripped = source.replace("timeout=SCRIPT_TIMEOUT,", "")
    assert "timeout=SCRIPT_TIMEOUT" not in stripped
    target = tmp_path / "test_pre_release_check_hook.py"
    target.write_text(stripped, encoding="utf-8")

    findings = find_violations(target)
    assert len(findings) == 1, findings
    assert str(target) in findings[0]
    assert "_run_dispatcher" in findings[0]
    assert "missing timeout=" in findings[0]
