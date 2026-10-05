"""Provider-agnostic dispatch guard (issue #735).

Enforces the repo invariant that provider differences are expressed through
capability flags / config keys, never through literal ``provider == "Name"``
branches in ``scripts/lib/``:

1. A directory sweep over ``scripts/lib/**/*.py`` (replaces the former static
   ``_TOUCHED_MODULES`` tuple, AC-14) AST-scans every module — a newly added
   lib module is covered automatically. Flagged are provider-name dispatch
   branches:
     * ``provider == "Name"`` / ``!=`` against a registered provider name, and
     * ``provider in ("Name", ...)`` / ``not in`` against an enumerated literal
       container of registered provider names.
   Comments/docstrings are ignored by design (the scan is AST-based).
2. No ``surface-version`` comparison drives dispatch in ``scripts/lib/``
   (AC-23). The one documented exception is the config-reading validator
   ``artifact_validate.artifact_v2_surface`` (spec §2.5 / AC-13), which resolves
   a provider's artifact contract from declared config values; it is keyed
   explicitly below so a writer branching on ``surface-version`` is still
   caught.
3. Every registered provider carries an explicit ``commands`` boolean in
   ``config/provider-capabilities.yaml`` — no silent else-fallback.
4. ``ai-providers.yaml has_commands`` agrees with the capability flag, and every
   commands-capable provider names a target dir + format.
5. An unsupported provider produces one explicit INFO line (not silence).
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

_LIB_DIR = _REPO_ROOT / "scripts" / "lib"

#: Documented exception (AC-23, spec §2.5 / AC-13): ``artifact_v2_surface`` is
#: the validator that resolves a provider's artifact contract from the declared
#: config values (``surface-version`` + ``frontmatter-mechanism``). Keyed by
#: (module path, enclosing function) so it stays explicit and minimal — any
#: other ``surface-version`` comparison, in this module or elsewhere, is still
#: a violation.
_SURFACE_VERSION_EXCEPTIONS = {
    ("artifact_validate.py", "artifact_v2_surface"),
}

#: Value domain of the ``surface-version`` config key.
_SURFACE_VERSION_VALUES = frozenset({"v1", "v2"})


def _lib_modules() -> list[Path]:
    """Every module under ``scripts/lib/`` (recursive), sorted by path.

    The directory sweep is deliberate: a newly added lib module is covered
    without editing this test (AC-14).
    """
    return sorted(_LIB_DIR.rglob("*.py"))


def _module_name(path: Path) -> str:
    """The module's path relative to ``scripts/lib/`` (POSIX separators)."""
    return path.relative_to(_LIB_DIR).as_posix()


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _enclosing_function(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str:
    current = parents.get(node)
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current.name
        current = parents.get(current)
    return "<module>"


def _provider_name(value: object, names: set[str]) -> bool:
    return isinstance(value, str) and value in names


def _provider_equality_operands(node: ast.Compare, names: set[str]) -> list[str]:
    """Registered provider-name literals compared with ``==``/``!=``."""
    operands = [node.left, *node.comparators]
    return sorted({
        o.value
        for o in operands
        if isinstance(o, ast.Constant) and _provider_name(o.value, names)
    })


def _provider_membership_operands(node: ast.Compare, names: set[str]) -> list[str]:
    """Registered provider names inside an enumerated literal container.

    Only the ``provider in ("Name", ...)`` shape is flagged — the literal must
    sit inside a tuple/list/set operand. A bare ``"Name" in some_dynamic_list``
    (e.g. ``"Claude" not in active_providers``) is an active-set membership
    check, not the dispatch anti-pattern this guard targets.
    """
    found: set[str] = set()
    for operand in [node.left, *node.comparators]:
        if not isinstance(operand, (ast.Tuple, ast.List, ast.Set)):
            continue
        for element in operand.elts:
            if isinstance(element, ast.Constant) and _provider_name(element.value, names):
                found.add(element.value)
    return sorted(found)


def _provider_dispatch_offenders(tree: ast.AST, module: str, names: set[str]) -> list[str]:
    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        if any(isinstance(op, (ast.Eq, ast.NotEq)) for op in node.ops):
            consts = _provider_equality_operands(node, names)
            if consts:
                offenders.append(f"scripts/lib/{module}:{node.lineno}: {consts}")
                continue
        if any(isinstance(op, (ast.In, ast.NotIn)) for op in node.ops):
            consts = _provider_membership_operands(node, names)
            if consts:
                offenders.append(f"scripts/lib/{module}:{node.lineno}: {consts}")
    return offenders


def _surface_version_dispatch_reason(node: ast.Compare) -> str | None:
    """Why ``node`` is a ``surface-version`` dispatch comparison, if it is.

    Two shapes are caught: a direct read of the ``"surface-version"`` config key
    inside the comparison (e.g. ``cfg.get("surface-version") == "v2"``), and a
    comparison against a surface-version-domain literal (``v1``/``v2``) under
    any variable name (e.g. ``surface == "v2"`` or ``sv == "v2"``). The version
    literals are otherwise unused in dispatch under ``scripts/lib/``, so this
    catches a writer that branches on the surface regardless of naming.
    """
    if any(
        isinstance(sub, ast.Constant) and sub.value == "surface-version"
        for sub in ast.walk(node)
    ):
        return "reads 'surface-version'"
    operands = [node.left, *node.comparators]
    consts = {
        o.value
        for o in operands
        if isinstance(o, ast.Constant) and isinstance(o.value, str)
    }
    if consts & _SURFACE_VERSION_VALUES:
        return "compares a surface-version value (v1/v2)"
    return None


def _surface_version_dispatch_offenders(
    tree: ast.AST, module: str, parents: dict[ast.AST, ast.AST]
) -> list[str]:
    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        if not any(
            isinstance(op, (ast.Eq, ast.NotEq, ast.In, ast.NotIn)) for op in node.ops
        ):
            continue
        reason = _surface_version_dispatch_reason(node)
        if reason is None:
            continue
        if (module, _enclosing_function(node, parents)) in _SURFACE_VERSION_EXCEPTIONS:
            continue
        offenders.append(f"scripts/lib/{module}:{node.lineno} ({reason})")
    return offenders


def _registered_providers() -> list[str]:
    data = yaml.safe_load((_REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))
    return sorted((data.get("providers") or {}).keys())


def _provider_capabilities() -> dict:
    data = yaml.safe_load((_REPO_ROOT / "config" / "provider-capabilities.yaml").read_text(encoding="utf-8"))
    return data.get("capabilities") or {}


def _provider_configs() -> dict:
    data = yaml.safe_load((_REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))
    return data.get("providers") or {}


def test_no_provider_name_dispatch_branches_in_lib():
    """AC-14: no ``provider == "Name"`` / ``provider in ("Name", ...)`` branch
    may remain anywhere under ``scripts/lib/``. AST-based so comments and
    docstrings that *mention* the anti-pattern do not false-positive."""
    names = set(_registered_providers())
    modules = _lib_modules()
    assert len(modules) > 1, f"scripts/lib sweep found only {len(modules)} modules"
    offenders: list[str] = []
    for module_path in modules:
        try:
            tree = ast.parse(module_path.read_text(encoding="utf-8"))
        except SyntaxError as exc:  # a module the guard cannot inspect
            offenders.append(f"scripts/lib/{_module_name(module_path)}: unparseable: {exc}")
            continue
        offenders.extend(_provider_dispatch_offenders(tree, _module_name(module_path), names))
    assert not offenders, (
        "Provider-name dispatch branch(es) reintroduced — dispatch via "
        "config/ai-providers.yaml capabilities (provider_has_capability) or the "
        "provider-capabilities.yaml registry instead:\n" + "\n".join(offenders)
    )


def test_lib_sweep_covers_task_modules():
    """AC-14: the sweep must cover the modules added by Tasks 1–11, proving the
    glob is live (not vacuous) and no future module can bypass the guard."""
    swept = {_module_name(path) for path in _lib_modules()}
    expected = {
        "artifact_validate.py",
        "bootstrap.py",
        "mcp_provider_config.py",
        "pipelines.py",
        "context.py",
        "consistency/artifact_contracts.py",
        "consistency/model_contracts.py",
    }
    assert expected <= swept, sorted(expected - swept)


def test_no_surface_version_dispatch_in_lib():
    """AC-23: no ``surface-version`` comparison drives dispatch in
    ``scripts/lib/``. The writer must dispatch on the resolved
    ``mcp-config.format`` value only (spec §2.5, design DECISION-7)."""
    modules = _lib_modules()
    assert len(modules) > 1, f"scripts/lib sweep found only {len(modules)} modules"
    offenders: list[str] = []
    for module_path in modules:
        try:
            tree = ast.parse(module_path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            offenders.append(f"scripts/lib/{_module_name(module_path)}: unparseable: {exc}")
            continue
        offenders.extend(
            _surface_version_dispatch_offenders(
                tree, _module_name(module_path), _parent_map(tree)
            )
        )
    assert not offenders, (
        "surface-version dispatch comparison(s) reintroduced — select the "
        "declared mcp-config.format in config data and dispatch on that value "
        "only (AC-23). Documented exception: "
        f"{sorted(_SURFACE_VERSION_EXCEPTIONS)}:\n" + "\n".join(offenders)
    )


# Synthetic snippets proving the guard is live (not vacuous). They live in the
# test module — never in ``scripts/lib/`` — so they cannot trip the sweep.
_SYNTH_PROVIDER_EQ = "def f(provider):\n    if provider == 'Claude':\n        return 1\n"
_SYNTH_PROVIDER_IN = "def f(provider):\n    if provider in ('Claude', 'Gemini'):\n        return 1\n"
_SYNTH_SURFACE_BRANCH = "def write(sv):\n    if sv == 'v2':\n        return 1\n"
_SYNTH_VALIDATOR = (
    "def artifact_v2_surface(pc):\n"
    "    surface = pc.get('surface-version', 'v1')\n"
    "    return surface == 'v2'\n"
)


def test_guard_detects_synthetic_provider_dispatch():
    """TDD pin: equality and enumerated-membership branches are both caught."""
    names = set(_registered_providers())
    assert _provider_dispatch_offenders(
        ast.parse(_SYNTH_PROVIDER_EQ), "synthetic.py", names
    )
    assert _provider_dispatch_offenders(
        ast.parse(_SYNTH_PROVIDER_IN), "synthetic.py", names
    )


def test_guard_detects_synthetic_surface_version_dispatch():
    """TDD pin: a writer branching on ``surface-version`` is caught."""
    tree = ast.parse(_SYNTH_SURFACE_BRANCH)
    assert _surface_version_dispatch_offenders(tree, "writer.py", _parent_map(tree))


def test_guard_exempts_only_documented_validator():
    """The validator exception is minimal: identical code in any other module
    (or any other function) is still reported."""
    tree = ast.parse(_SYNTH_VALIDATOR)
    parents = _parent_map(tree)
    assert not _surface_version_dispatch_offenders(tree, "artifact_validate.py", parents)
    assert _surface_version_dispatch_offenders(tree, "mcp_provider_config.py", parents)


def test_cleanup_preview_documented():
    """AC-20 (SPEC-STALE-ROLE-CLEANUP-2026-09-13, Task 8): the planning-only
    ``--cleanup-preview`` mode must be documented in the CLI reference together
    with its rc semantics (0 even for a non-empty stale set, 1 only on
    internal failure)."""
    cli_ref = (_REPO_ROOT / "docs" / "api" / "cli-reference.md").read_text(encoding="utf-8")
    assert "--cleanup-preview" in cli_ref, (
        "docs/api/cli-reference.md must document the --cleanup-preview flag"
    )
    lowered = cli_ref.lower()
    assert "exit code 0" in lowered, (
        "docs/api/cli-reference.md must state the rc-0 semantics of "
        "--cleanup-preview (a non-empty stale set still exits 0)"
    )


def test_admin_cleanup_routes_documented():
    """AC-20 (SPEC-STALE-ROLE-CLEANUP-2026-09-13, Task 8): both cleanup POST
    routes and the mandatory confirm/fingerprint handshake must be documented
    in the Admin-UI reference."""
    ref = (_REPO_ROOT / "docs" / "api" / "admin-ui-reference.md").read_text(encoding="utf-8")
    assert "/api/roles/cleanup/preview" in ref, (
        "docs/api/admin-ui-reference.md must document the preview route"
    )
    assert "/api/roles/cleanup/apply" in ref, (
        "docs/api/admin-ui-reference.md must document the apply route"
    )
    lowered = ref.lower()
    assert "confirm" in lowered, (
        "docs/api/admin-ui-reference.md must document the confirm requirement"
    )
    assert "fingerprint" in lowered, (
        "docs/api/admin-ui-reference.md must document the fingerprint check"
    )


@pytest.mark.parametrize("provider", _registered_providers())
def test_every_provider_has_explicit_commands_capability(provider):
    caps = _provider_capabilities().get(provider, {})
    assert "commands" in caps, (
        f"Provider '{provider}' has no explicit 'commands' entry in "
        "config/provider-capabilities.yaml — an absent key means the commands "
        "path silently reports unsupported (issue #735)."
    )
    assert isinstance(caps["commands"], bool), (
        f"Provider '{provider}'.commands must be a boolean, got {caps['commands']!r}"
    )


@pytest.mark.parametrize("provider", _registered_providers())
def test_every_provider_has_explicit_runtime_gate_capability(provider):
    """AC-01 (SPEC-OPENCODE-RUNTIME-GATE-2026-09-13): every registered provider
    must carry an explicit ``runtime_gate`` tier in
    ``config/provider-capabilities.yaml``, and its value must be one of the
    canonical tiers from ``scripts/lib/runtime_gate.py``. An absent key
    resolves fail-safe to ``advisory`` at runtime, but omitting it would
    silently document a weaker gate than intended — this test turns the
    omission into a failure (same obligation as ``commands``)."""
    from lib.runtime_gate import RUNTIME_GATE_TIERS

    caps = _provider_capabilities().get(provider, {})
    assert "runtime_gate" in caps, (
        f"Provider '{provider}' has no explicit 'runtime_gate' entry in "
        "config/provider-capabilities.yaml — an absent key silently resolves "
        "to 'advisory' (fail-safe), which would understate or overstate the "
        "gate. Declare one of: " + ", ".join(RUNTIME_GATE_TIERS)
    )
    assert caps["runtime_gate"] in RUNTIME_GATE_TIERS, (
        f"Provider '{provider}'.runtime_gate={caps['runtime_gate']!r} is not a "
        "canonical tier — expected one of: " + ", ".join(RUNTIME_GATE_TIERS)
    )


@pytest.mark.parametrize("provider", _registered_providers())
def test_every_provider_has_explicit_route_intent_tool_capability(provider):
    """Every registered provider must carry an explicit ``route_intent_tool``
    boolean in ``config/provider-capabilities.yaml`` (same obligation as
    ``commands``/``runtime_gate``). The runtime default is fail-safe ``false``
    — the generated definition is prompt text, not a callable tool — so an
    omission would leave the orchestrator mandate ungated. ``true`` may only be
    set after a live route_intent acceptance proof."""
    caps = _provider_capabilities().get(provider, {})
    assert "route_intent_tool" in caps, (
        f"Provider '{provider}' has no explicit 'route_intent_tool' entry in "
        "config/provider-capabilities.yaml — declare the harness contract "
        "explicitly (false until a live route_intent call is proven)."
    )
    assert isinstance(caps["route_intent_tool"], bool), (
        f"Provider '{provider}'.route_intent_tool must be a boolean, got "
        f"{caps['route_intent_tool']!r}"
    )


@pytest.mark.parametrize("provider", _registered_providers())
def test_has_commands_flag_matches_capability(provider):
    has_commands = bool(_provider_configs().get(provider, {}).get("has_commands", False))
    capability = bool(_provider_capabilities().get(provider, {}).get("commands", False))
    assert has_commands == capability, (
        f"Provider '{provider}': ai-providers.yaml has_commands={has_commands} "
        f"disagrees with provider-capabilities.yaml commands={capability} — "
        "the two registries must stay in sync (issue #735)."
    )


@pytest.mark.parametrize("provider", _registered_providers())
def test_commands_capable_provider_names_dir_and_format(provider):
    caps = _provider_capabilities().get(provider, {})
    if caps.get("commands") is not True:
        return
    pc = _provider_configs().get(provider, {})
    assert pc.get("commands_dir"), (
        f"Provider '{provider}' declares commands: true but has no commands_dir "
        "in config/ai-providers.yaml — sync would fail loudly (issue #735)."
    )
    assert pc.get("commands_format") in {"markdown", "continue", "toml"}, (
        f"Provider '{provider}' needs an explicit commands_format "
        "(markdown|continue|toml) in config/ai-providers.yaml."
    )


def _commands_capable_providers() -> list[str]:
    caps = _provider_capabilities()
    return [p for p in _registered_providers() if caps.get(p, {}).get("commands") is True]


def _commands_disabled_providers() -> list[str]:
    caps = _provider_capabilities()
    return [p for p in _registered_providers() if caps.get(p, {}).get("commands") is not True]


@pytest.mark.parametrize("provider", _commands_capable_providers())
def test_commands_capable_provider_emits_at_least_one_command(provider, tmp_path):
    """Issue #807 (F18) capability contract: every provider that declares
    ``commands: true`` must actually receive commands from a sync — no provider
    may be marked capable while the generator silently emits nothing."""
    from lib.commands import sync_commands_for_provider
    from lib.log import SyncLog

    pc = _provider_configs()[provider]
    sync_commands_for_provider(
        _REPO_ROOT, tmp_path, {}, SyncLog(), dry_run=False,
        provider=provider, provider_config=_provider_configs(), variables={},
    )
    target_dir = tmp_path / pc["commands_dir"]
    ext = pc.get("commands_ext", ".md")
    emitted = [
        f for f in target_dir.glob(f"*{ext}")
        if not f.name.startswith(".agent-meta")
    ]
    assert emitted, (
        f"Provider '{provider}' declares commands: true but sync emitted 0 "
        f"commands into '{pc['commands_dir']}' (issue #807)."
    )


@pytest.mark.parametrize("provider", _commands_disabled_providers())
def test_commands_disabled_provider_emits_nothing(provider, tmp_path):
    """A verified ``commands: false`` decision must stay fail-quiet: sync writes
    no command files anywhere under the project root."""
    from lib.commands import sync_commands_for_provider
    from lib.log import SyncLog

    sync_commands_for_provider(
        _REPO_ROOT, tmp_path, {}, SyncLog(), dry_run=False,
        provider=provider, provider_config=_provider_configs(), variables={},
    )
    written = [p for p in tmp_path.rglob("*") if p.is_file()]
    assert not written, (
        f"Provider '{provider}' has commands: false but sync wrote {written} "
        "— the capability gate leaked."
    )


def test_issue_807_verified_command_surface_decisions():
    """Regression pin for issue #807 (F18). Copilot, Mammouth and ZCode have a
    real project command surface (flipped to true). Codex and KimiCode have no
    project-scoped custom-command surface and stay false as documented
    capability decisions. Both registries must agree."""
    caps = _provider_capabilities()
    pc = _provider_configs()
    for provider in ("Copilot", "Mammouth", "ZCode"):
        assert caps[provider]["commands"] is True, provider
        assert pc[provider]["has_commands"] is True, provider
        assert pc[provider].get("commands_dir"), provider
    for provider in ("Codex", "KimiCode"):
        assert caps[provider]["commands"] is False, provider
        assert pc[provider]["has_commands"] is False, provider
        assert not pc[provider].get("commands_dir"), provider


class _LogRecorder:
    def __init__(self):
        self.events = []

    def note(self, label, detail):
        self.events.append(("note", label, detail))

    def action(self, kind, label, detail):
        self.events.append(("action", kind, label, detail))

    def skip(self, label, reason):
        self.events.append(("skip", label, reason))

    def warning(self, msg):
        self.events.append(("warning", msg))


def test_unsupported_provider_logs_explicit_note_instead_of_silence(tmp_path):
    from lib.commands import sync_commands_for_provider

    log = _LogRecorder()
    sync_commands_for_provider(
        _REPO_ROOT, tmp_path, {}, log, dry_run=True,
        provider="Codex", provider_config=_provider_configs(),
    )
    notes = [e for e in log.events if e[0] == "note" and e[1] == "commands"]
    assert notes, "unsupported provider must emit an explicit commands INFO line"
    assert "not supported" in notes[0][2]


def test_commands_capable_provider_without_dir_fails_loudly(tmp_path):
    from lib.commands import sync_commands_for_provider
    from lib.io import SyncError

    log = _LogRecorder()
    with pytest.raises(SyncError):
        sync_commands_for_provider(
            _REPO_ROOT, tmp_path, {}, log, dry_run=True,
            provider="Opencode", provider_config={"Opencode": {}},
        )


def test_context_adapter_dispatch_is_key_driven_without_provider_literals():
    """AC-12: the adapter filename dispatch is driven purely by the
    ``context_adapter`` keys, never by a provider-name branch."""
    from lib.providers import resolve_context_filename

    adapter_pc = {"context_adapter": True, "context_adapter_file": "ADAPTER.md"}
    assert (
        resolve_context_filename("AGENTS.md", "SomeFutureProvider", adapter_pc)
        == "ADAPTER.md"
    )
    direct_pc = {"context_file": "AGENTS.md"}
    assert (
        resolve_context_filename("AGENTS.md", "SomeFutureProvider", direct_pc)
        == "AGENTS.md"
    )


def test_reference_standards_seams_are_in_lib_sweep():
    """AC-14: the reference_standards production seams are covered by the
    provider-agnostic AST sweep above — no provider-name literal may creep
    into the new strip resolver call site or the consistency module."""
    swept = {_module_name(path) for path in _lib_modules()}
    for module in ("provider_transform.py", "consistency/reference_standards.py"):
        assert module in swept, module
        assert (_LIB_DIR / module).exists(), module
