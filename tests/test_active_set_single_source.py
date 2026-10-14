"""Guard QG-13 (static part): no raw ``config["roles"]`` access in generators.

Spec ``docs/specs/2026-10-11-context-profiles-spec.md`` (QG-13, IC-18, F-42, AC-84):
the ungated allowlist ``config["roles"]`` must not be consumed directly; consumers
derive the active role set from ``ActiveSet``. Rule id: ``active-set.raw-roles-access``.

Ratchet semantics (same style as ``ROUTE_RATCHET`` in
``tests/test_no_role_routes_in_templates.py``):

* ``RAW_ROLES_RATCHET`` = today's hits (``module::function``). A hit that is not
  registered fails (new access); a registered entry without a hit fails (stale,
  the ratchet may only shrink). Each IC-18 PR removes its entries; AC-84 requires
  an empty registry at the end of phase 1.
* ``LEGIT_READERS`` = modules that read the allowlist/registry legitimately,
  each with a reason. They are skipped entirely.

Deviation spec vs. real state (documented, not hidden):

* Line numbers drifted: sync.py:414 -> :426, config.py:682 -> :687 (spec: four
  config.py places; real: four, at :687, :1689, :1863, :2044). The spec lists
  config.py :1681/:1688 as two sites; both are one function here (:1689 only,
  the ratchet key is per function, so one entry).
* Hits the spec does not list: ``agent_sync.py:1337`` (``config['roles']``,
  expected-agent-files logic) and ``config.py:1863`` (``available_roles`` in
  ``_build_pipeline_variables``). Both are registered as ratchet entries.
* Scanner scope: only receivers named ``config`` (AST, so comments, docstrings and
  messages such as ``agent_sync.py:569`` and the ``config.py:1347`` comment are
  no hits). Registry reads on other receivers (``role_defaults.get("roles")``,
  ``load_roles_config(...)["roles"]``, ``admin-server.py``) are not scanned.
* The legit-reader list is whole-module; ``delegation_table.py``, ``pipelines.py``
  and ``provider_transform.py`` currently have no ``config`` receiver hit and are
  kept as forward-compat exemptions per IC-18.
* Scope (widened): ``scripts/sync.py`` and ``scripts/lib/**/*.py`` (incl.
  ``consistency/``). Receivers: ``config``, ``cfg``, ``project_config``,
  ``project_cfg`` and attributes ``*.config``. Detected forms: ``x["roles"]``,
  ``x.get/pop/setdefault("roles")`` and ``"roles" in x`` / ``not in``.
  Registry receivers (``roles_cfg``, ``role_defaults``, ``data``, ``roles_config``)
  stay excluded.
* Deliberately NOT scanned: ``scripts/admin-server.py`` (``project_config.get``,
  admin UI, no generator) and ``hermes_export.py`` (export tooling).
* New hits vs. spec: ``config.py:1862`` (``"roles" in config``, same function as
  :1863, no new key). ``consistency/active_set_refs.py:212`` (``cfg.get("roles")``
  in ``check_unknown_role``) is a LEGIT reader: it only validates the raw
  allowlist against the registry (like ``config_audit.py``), no activation use.
* Known limits: alias assignment (``r = config; r["roles"]``) is not followed;
  keys are ``module::Class.method`` of the innermost function (nested functions
  of the same name inside one method share a key).
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, FrozenSet, List, Set

REPO_ROOT = Path(__file__).resolve().parents[1]

# Generator modules in scope: scripts/sync.py and scripts/lib/*.py.
SCAN_GLOBS = ("scripts/sync.py", "scripts/lib/**/*.py")

# Legit readers (IC-18 "Legitime Leser"): module path -> reason.
LEGIT_READERS: Dict[str, str] = {
    "scripts/lib/active_set.py": "implements ActiveSet; resolves and normalises the raw allowlist itself",
    "scripts/lib/roles.py": "gate/allowlist resolution (resolve_active_roles) is the sanctioned reader",
    "scripts/lib/config_audit.py": "validates the raw list against the registry, no activation consumption",
    "scripts/lib/runtime_gate.py": "reads the role registry role-defaults.yaml::roles, not the allowlist",
    "scripts/lib/consistency/active_set_refs.py": "check_unknown_role only validates the raw allowlist against the registry (like config_audit), no activation consumption",
    "scripts/lib/delegation_table.py": "Forward-Compat: reads the role registry (role-defaults.yaml::roles), not the allowlist",
    "scripts/lib/pipelines.py": "Forward-Compat: reads the role registry (role-defaults.yaml::roles), not the allowlist",
    "scripts/lib/provider_transform.py": "Forward-Compat: reads the role registry (role-defaults.yaml::roles), not the allowlist",
}

# Start registry (F-42, IC-18 no. 14-18). Format: "<module>::<function>".
RAW_ROLES_RATCHET: FrozenSet[str] = frozenset(
    {
        "scripts/lib/context.py::sync_prompts_for_continue",  # IC-18 no. 15 (:2342)
        "scripts/sync.py::_preview_expected_filenames",  # IC-18 no. 16 (:426)
        "scripts/lib/skills.py::sync_external_skills_for_provider",  # IC-18 no. 17 (:424)
        "scripts/lib/config.py::_build_platform_variables",  # IC-18 no. 18 (:1689, effort estimator)
        "scripts/lib/config.py::_build_convention_variables",  # IC-18 no. 18 (:2044)
        "scripts/lib/config.py::_build_pipeline_variables",  # not in spec F-42 (:1863 available_roles) - see docstring
        "scripts/lib/config.py::_validate_subagent_permissions",  # IC-18 no. 18 "active-role list" (spec :682, real :687)
        "scripts/lib/agent_sync.py::sync_agents_for_provider",  # not in spec F-42 (:1337)
    }
)


def _is_roles_const(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value == "roles"


CONFIG_NAMES = frozenset({"config", "cfg", "project_config", "project_cfg"})
MUTATORS = frozenset({"get", "pop", "setdefault"})


def _is_config(node: ast.AST) -> bool:
    # Project config dict only; registry dicts (role_defaults, roles_cfg, ...) are other receivers.
    if isinstance(node, ast.Name):
        return node.id in CONFIG_NAMES
    return isinstance(node, ast.Attribute) and node.attr == "config"


def scan_source(source: str, rel: str) -> Set[str]:
    """Return ``module::Class.func`` keys of raw access to the ``roles`` allowlist."""
    tree = ast.parse(source)
    hits: Set[str] = set()

    def visit(node: ast.AST, scope: str) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            scope = node.name if scope == "<module>" else f"{scope}.{node.name}"
        hit = False
        if isinstance(node, ast.Subscript):
            key = node.slice.value if isinstance(node.slice, ast.Index) else node.slice  # py3.8 compat
            hit = _is_config(node.value) and _is_roles_const(key)
        elif isinstance(node, ast.Call):
            f = node.func
            hit = (
                isinstance(f, ast.Attribute)
                and f.attr in MUTATORS
                and _is_config(f.value)
                and bool(node.args)
                and _is_roles_const(node.args[0])
            )
        elif isinstance(node, ast.Compare):
            hit = (
                _is_roles_const(node.left)
                and any(isinstance(op, (ast.In, ast.NotIn)) for op in node.ops)
                and any(_is_config(c) for c in node.comparators)
            )
        if hit:
            hits.add(f"{rel}::{scope}")
        for child in ast.iter_child_nodes(node):
            visit(child, scope)

    visit(tree, "<module>")
    return hits


def scan_repo(repo_root: Path = REPO_ROOT) -> Set[str]:
    hits: Set[str] = set()
    for pattern in SCAN_GLOBS:
        for path in sorted(repo_root.glob(pattern)):
            rel = path.relative_to(repo_root).as_posix()
            if rel in LEGIT_READERS:
                continue
            hits |= scan_source(path.read_text(encoding="utf-8"), rel)
    return hits


# --- Step 1: scanner detects an inserted hit in a fixture module -------------

def test_scanner_flags_inserted_subscript_hit_in_fixture(tmp_path):
    # [REQ-QG-13] a newly inserted config["roles"] access in a module goes red
    lib = tmp_path / "scripts" / "lib"
    lib.mkdir(parents=True)
    (lib / "new_generator.py").write_text(
        "def build(config):\n    return set(config[\"roles\"])\n", encoding="utf-8"
    )
    hits = scan_repo(tmp_path)
    assert hits == {"scripts/lib/new_generator.py::build"}
    assert hits - RAW_ROLES_RATCHET  # unregistered => guard would fail


def test_scanner_flags_inserted_get_hit_in_fixture(tmp_path):
    # [REQ-QG-13] config.get("roles") is detected as well
    lib = tmp_path / "scripts" / "lib"
    lib.mkdir(parents=True)
    (lib / "other.py").write_text(
        "def f(config):\n    return config.get('roles', [])\n", encoding="utf-8"
    )
    assert scan_repo(tmp_path) == {"scripts/lib/other.py::f"}


def test_scanner_ignores_comments_strings_and_legit_readers(tmp_path):
    # [REQ-QG-13] comments/docstrings/messages are no access; legit readers are skipped
    lib = tmp_path / "scripts" / "lib"
    lib.mkdir(parents=True)
    (lib / "clean.py").write_text(
        'def f(config):\n    """uses config["roles"] in prose"""\n'
        '    # config["roles"]\n    return "not in config[\'roles\']"\n',
        encoding="utf-8",
    )
    (lib / "active_set.py").write_text(
        "def g(config):\n    return config.get('roles')\n", encoding="utf-8"
    )
    assert scan_repo(tmp_path) == set()


# --- Step 2: ratchet against the real repository -----------------------------

def test_no_new_raw_roles_access():
    # [REQ-QG-13] every raw access must be registered in the ratchet
    new = scan_repo() - RAW_ROLES_RATCHET
    assert not new, "active-set.raw-roles-access: new raw access (use ActiveSet):\n" + "\n".join(sorted(new))


def test_ratchet_has_no_stale_entries():
    # [REQ-QG-13] ratchet may only shrink: entries without a hit must be removed
    stale = RAW_ROLES_RATCHET - scan_repo()
    assert not stale, "RAW_ROLES_RATCHET entries without a hit - remove them:\n" + "\n".join(sorted(stale))


def test_legit_readers_exist_and_have_reason():
    # [REQ-QG-13] exemption list must not rot: files exist (or are known forward-compat) with reason
    for rel, reason in LEGIT_READERS.items():
        assert reason.strip(), rel
        assert (REPO_ROOT / rel).is_file(), f"LEGIT_READERS entry without file: {rel}"
    assert not (set(LEGIT_READERS) & {k.split("::")[0] for k in RAW_ROLES_RATCHET})


def test_scanner_flags_in_pop_setdefault_and_cfg_receivers(tmp_path):
    # [REQ-QG-13] membership test, pop/setdefault, cfg/self.config receivers and nested dirs are covered
    sub = tmp_path / "scripts" / "lib" / "consistency"
    sub.mkdir(parents=True)
    (sub / "mod.py").write_text(
        "class K:\n"
        "    def a(self, config):\n        return 'roles' in config\n"
        "    def b(self, cfg):\n        return cfg.pop('roles')\n"
        "    def c(self):\n        return self.config.setdefault('roles', [])\n"
        "    def d(self, role_defaults):\n        return role_defaults.get('roles')\n",
        encoding="utf-8",
    )
    assert scan_repo(tmp_path) == {
        "scripts/lib/consistency/mod.py::K.a",
        "scripts/lib/consistency/mod.py::K.b",
        "scripts/lib/consistency/mod.py::K.c",
    }
