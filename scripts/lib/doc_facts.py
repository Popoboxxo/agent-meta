"""Computes the ``DOCS_*`` facts from the canonical sources (one SSoT per class).

Neutral leaf module: it knows no documentation file, reads no hand-written
prose and **writes nothing** — a path/size/mtime digest of the fact-source
directories (``FACT_SOURCE_PATHS``, exercised by ``tests/test_doc_facts.py``)
is identical before and after a call (IC-01, AC-01). Every fact that cannot be
computed yields ``""`` (fail-soft, the contract of ``_load_block_snippet``,
``config.py``); the generator must never abort a sync over a number.

Scope of this revision (plan tasks W1-2 + W1-3): the scalar formulas of the
IC-02 table, the ``volatile`` marking, the seven ``*_BLOCK`` bodies and the
gate-aware active-role set (IC-04). ``FACT_KEYS`` plus ``_FACT_COMPUTERS`` is the
sanctioned extension point; a fact that is not registered there keeps the
fail-soft default ``""``.

**``DOCS_AGENTS_ACTIVE_COUNT`` is gate-aware, never ``len(roles)`` (F13/F21).**
The number comes from :func:`compute_active_roles`, which intersects the
``roles:`` whitelist, the ``config/role-defaults.yaml`` role registry, the
generatable template universe and ``roles.resolve_activation_gates()``.
``se-component-requirements`` is listed in
``roles:`` yet is never generated because ``systems-engineering.enabled: false``
closes its activation gate — a ``len(roles)`` fallback would reproduce exactly
the F21 defect (a permanent false alarm).

**IC-04 DEVIATION (deliberate, review finding W13-4) — the template universe
comes from the framework resolver, not from an ``agents/1-generic/`` glob.**
IC-04 names ``agents/1-generic/`` as the source of the "real templates" term,
and the implementation originally did exactly that. That is a *wrong number*,
not a harmless simplification: a template that only exists as a ``based-on:``
wrapper in ``agents/2-platform/`` is never in the 1-generic glob, so the fact
came out at **53** while ``roles.resolve_active_roles(..., require_template=True)``
— the very function sync generates from — returned **58**, and the generated
trees hold 58 agent files each (``.claude/agents/*.md`` and
``.opencode/agents/*.md``, counted at the time of writing). The 5-role gap is
the ``*-expert`` family (``claude-expert``, ``continue-expert``,
``copilot-expert``, ``gemini-expert``, ``opencode-expert``). A published fact
that contradicts generated output is a defect whichever spec sentence it hides
behind, and eliminating plausible-but-wrong counts is this initiative's whole
purpose — so the implementation follows the *resolver*
(:func:`roles.resolve_template_roles`: ``collect_sources`` over
1-generic + 2-platform, minus ``WRAPPER_TEMPLATES``, minus roles with no
ROLE_MAP target) and a parity test pins the contract
(``test_active_count_parity_with_framework_resolver``). The spec sentence needs
the matching IC-04 correction; it is recorded here because the spec is not this
task's to edit.

Two further consequences of taking the universe from the resolver:

* ``config/role-defaults.yaml::roles`` (the registry) becomes an explicit leg of
  the intersection, because ``roles.resolve_active_roles`` derives its layer 1
  from the registry and not from the templates. Without it the ``roles:``-absent
  branch over-reported ``provider-expert``, a ``WRAPPER_TEMPLATES`` entry the
  universe excludes, and under-reported the ``*-expert`` family (W13-6: 62
  where the resolver answers 66; both read 66 now).
* ``agents/2-platform/`` joins ``FACT_SOURCE_PATHS`` in the test digest, so the
  no-write invariant (AC-01) covers the directory the fact now reads.

Sources read for that fact and therefore covered by the write-invariance
digest (``scripts/``, ``config/``, ``agents/1-generic/``, ``agents/2-platform/``):
``scripts/lib/roles.py`` (gates, registry, template universe),
``scripts/lib/providers.py`` (capability), ``config/role-defaults.yaml``
(``activation_groups`` + registry), ``agents/1-generic/`` and
``agents/2-platform/`` (templates). The per-call memo keeps every one of them a
single read per call.

**Consumer obligation for W2-4 (recorded, not implemented here).**
:class:`FactUnavailable` is a module-local exception, deliberately leaked (there
is no ``__all__``): it signals *a source is missing or unreadable* and nothing
else. It can therefore never express *definitional divergence* between this
module's formula and the generator's. The planned
``check_role_generation_parity`` (plan task W2-4) compares the set from
:func:`compute_active_roles` against sync's and must therefore (a) catch
:class:`FactUnavailable` explicitly and report it as *unavailable*, never as a
mismatch, and (b) pin the IC-04-vs-resolver contract above as its own
assertion. Treating a caught ``FactUnavailable`` as a parity failure would
produce a permanent false alarm — exactly the F21 failure mode this module
exists to avoid. No behaviour changes with this note.

Key count: IC-02 enumerates **22** placeholders (15 scalar + 7 ``*_BLOCK``).
AC-01 phrases this as "exactly the 23 keys listed in IC-02" — the numeral is a
stale summary (the same count-drift class the spec corrects in NF-5, NF-10 and
NEW-4), the table is the enumeration. ``FACT_KEYS`` is the single place where
the set is spelled out, so a spec correction touches **three** copies: one
line here, one row in the IC-02 table of
``docs/specs/2026-09-25-repository-documentation-consolidation.md`` and one
entry in the test oracle ``IC02_KEYS`` (``tests/test_doc_facts.py``).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import NamedTuple

from .frontmatter import parse_frontmatter_file
from .hooks import parse_hook_metadata
from .io import load_yaml_file
from .providers import provider_has_capability
from .roles import (
    is_role_enabled,
    load_roles_config,
    resolve_activation_gates,
    resolve_template_roles,
)

HOOK_EXCLUDED_DIRS: frozenset[str] = frozenset({"lib", "release-gates"})
HOOK_EXCLUDED_SUFFIXES: tuple[str, ...] = ("-impl.sh",)
AGENT_HELPER_PREFIX: str = "_"

# The enumeration order is load-bearing: the dispatcher computes the facts in
# exactly this order, and ``DOCS_REPO_FACTS_BLOCK`` is the only computer that
# reads the already-computed ``context.scalars``. It must therefore stay
# **last** — see ``_doc_repo_facts_block``.
FACT_KEYS: tuple[str, ...] = (
    "DOCS_VERSION",
    "DOCS_AGENT_TEMPLATES_COUNT",
    "DOCS_AGENTS_SE_COUNT",
    "DOCS_AGENTS_NONSE_COUNT",
    "DOCS_AGENTS_ACTIVE_COUNT",
    "DOCS_HOOKS_COUNT",
    "DOCS_HOOKS_1GENERIC_COUNT",
    "DOCS_PROVIDER_COUNT",
    "DOCS_PIPELINES_COUNT",
    "DOCS_PIPELINES_ACTIVE_COUNT",
    "DOCS_DOD_PRESET_COUNT",
    "DOCS_TIER_PRESET_COUNT",
    "DOCS_COMMAND_COUNT",
    "DOCS_SCENARIO_COUNT",
    "DOCS_DOCS_FILE_COUNT",
    "DOCS_AGENT_ROSTER_BLOCK",
    "DOCS_PIPELINES_BLOCK",
    "DOCS_HOOKS_BLOCK",
    "DOCS_PROVIDERS_BLOCK",
    "DOCS_TIER_PRESET_BLOCK",
    "DOCS_DOD_PRESET_BLOCK",
    "DOCS_REPO_FACTS_BLOCK",
)

FACT_UNAVAILABLE: str = ""

#: Fakten, die nicht in ``README.md``/``llms.txt`` gerendert werden dürfen
#: (R1/M7). Genau **ein** Faktum — ein Szenario, das hinzukommt, darf keinen
#: ``facts-hash``-Wechsel erzeugen.
VOLATILE_FACTS: frozenset[str] = frozenset({"DOCS_SCENARIO_COUNT"})

#: Fakten, deren IC-02-Formel eine API braucht, die ein späterer Wellen-Task
#: erst erzeugt. Sie bleiben bis dahin bewusst ``FACT_UNAVAILABLE`` — **kein**
#: Ersatz-Formel-Fallback (siehe Modul-Docstring, F13/F21).
PENDING_FACTS: dict[str, str] = {}
"""Facts whose computer is not implemented yet, mapped to their blocker.

Empty since plan task W1-3: ``DOCS_AGENTS_ACTIVE_COUNT`` is computed from
:func:`compute_active_roles` (IC-04). A fact listed here keeps the fail-soft
default ``""`` **and** is excluded from ``_STABLE_SCALAR_FACT_KEYS`` — a fact
block must not carry an empty row. The registry-coverage test enforces
``registered ∪ pending == FACT_KEYS`` with a disjoint intersection, so a
half-finished transition (removed here, not yet registered) fails the suite.
"""

#: Verzeichnis-Segmente, die ``DOCS_DOCS_FILE_COUNT`` nicht zählt (IC-02).
DOCS_EXCLUDED_DIR_SEGMENTS: frozenset[str] = frozenset({"archive", "_archive"})

#: Präfix der SE-Rollen (``se-*``), IC-02 ``DOCS_AGENTS_SE_COUNT``.
SE_ROLE_PREFIX: str = "se-"


AGENTS_CAPABILITY: str = "agents"
"""``config/ai-providers.yaml::capabilities`` entry that enables agent output.

Read through ``providers.provider_has_capability`` — never through a provider
name (NFA-03).
"""

PROVIDER_DECLARATION_KEYS: tuple[str, ...] = ("ai-providers", "ai-provider")
"""Config keys that name the *active* providers, in resolution order.

Mirrors ``providers.resolve_providers`` (multi-provider key first, legacy
single-provider key second) without importing its ``ValueError`` contract: a
fact must degrade, not abort.
"""

#: Präfix, das ``agents.py``-artige Template-Namen vom Rollen-Namen trennt.
TEMPLATE_NAME_PREFIX: str = "template-"

EMPTY_CELL: str = "—"

_AGENT_TEMPLATES_RELPATH = "agents/1-generic"
_TEMPLATE_UNIVERSE_RELPATHS: tuple[str, ...] = (
    "agents/1-generic",
    "agents/2-platform",
)
"""Directories that make up the template universe (see the IC-04 deviation).

``agents/2-platform/`` holds the ``based-on:`` wrapper family that the 1-generic
glob cannot see. Both must be present: a silently missing 2-platform directory
would shrink the universe by exactly the ``*-expert`` roles and produce a
plausible undercount instead of a degradation (W13-4).
"""
_COMMANDS_RELPATH = "commands/1-generic"
_SCENARIO_ASSERTS_RELPATH = "tests/scenarios/asserts"
_DOCS_RELPATH = "docs"
_VERSION_RELPATH = "VERSION"


class FactUnavailable(Exception):
    """A fact source is missing or unreadable — the fact degrades to ``""``.

    Raised by the computers and swallowed by :func:`compute_doc_facts`, which
    turns it into the fail-soft default plus exactly one ``log.debug`` entry
    (IC-01: a missing source is reported, never raised as ``SyncError``).
    """


class FactContext(NamedTuple):
    """Everything a fact implementation may read. Read-only by contract.

    ``sources`` is the **per-call** memo of the expensive source reads (YAML
    documents, frontmatter, hook globs). It is created fresh by
    :func:`compute_doc_facts` and shared by every ``_replace``-derived context
    of that one call, so ``config/role-defaults.yaml`` is parsed once per call
    instead of three times.

    It is deliberately **not** a module global: a process-lifetime cache would
    hand a second call stale data and silently render facts from a checkout
    that no longer exists on disk. Per-call scope keeps every call a pure
    function of the current filesystem state
    (``test_source_cache_is_scoped_to_one_call``).

    Cached values are shared objects — treat them as read-only, exactly like
    every other field of this context.
    """

    agent_meta_root: Path
    config: dict
    provider_config: dict | None
    log: object | None
    scalars: Mapping[str, str]
    sources: dict


_FACT_COMPUTERS: dict[str, Callable[[FactContext], str]] = {}


def _debug(log: object | None, target: str, message: str) -> None:
    """Best-effort ``log.debug(target, message)`` — never raises.

    ``log`` is duck-typed (``SyncLog`` in production, ``None`` or a stub in
    tests); IC-01 only requires that a missing source is reported, never that
    reporting itself can fail.
    """
    debug = getattr(log, "debug", None)
    if callable(debug):
        try:
            debug(target, message)
        except Exception:  # noqa: BLE001, S110 — IC-01: reporting must never raise
            pass


def _as_dict(value: object) -> dict:
    """Return a dict for mapping-like input, ``{}`` for anything else."""
    return dict(value) if isinstance(value, dict) else {}


# --------------------------------------------------------------------------
# source access (read-only, fail-soft)
# --------------------------------------------------------------------------


def _read_text(path: Path, relpath: str) -> str:
    """Return the file content or raise :class:`FactUnavailable`."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise FactUnavailable(f"cannot read {relpath}: {exc}") from exc


def _frontmatter(context: FactContext, path: Path) -> dict:
    """Memoised :func:`parse_frontmatter_file` for one call.

    The agent templates are read by four facts (three counts plus the roster
    block); without the memo the frontmatter is parsed up to four times.
    Failures are **not** cached: a raising parse must keep raising so the
    dispatcher logs the per-fact degradation every time.
    """
    key = ("frontmatter", str(path))
    if key in context.sources:
        return context.sources[key]
    data = parse_frontmatter_file(path)
    context.sources[key] = data
    return data


def _load_yaml_map(context: FactContext, path: Path, relpath: str) -> dict:
    """Load a mapping YAML file or raise :class:`FactUnavailable`.

    Memoised through ``context.sources`` for the duration of one call:
    ``config/role-defaults.yaml`` is read by the pipeline count, the pipeline
    active count and the agent roster block, and would otherwise be parsed
    three times.

    ``on_error="raise"`` is deliberate: a malformed file or a missing PyYAML
    must not silently become ``0`` — that would be exactly the unverified
    number this module exists to remove. The raised error is caught by the
    dispatcher and becomes ``""`` plus a ``log.debug`` entry. Only successful
    loads are memoised, so a failing source is retried (and re-reported) per
    fact.
    """
    key = ("yaml", str(path))
    if key in context.sources:
        return context.sources[key]
    if not path.is_file():
        raise FactUnavailable(f"source missing: {relpath}")
    data = load_yaml_file(path, on_error="raise", default={})
    result = data if isinstance(data, dict) else {}
    context.sources[key] = result
    return result


def _glob_files(root: Path, relpath: str, pattern: str) -> list[Path]:
    """Sorted non-recursive glob or raise :class:`FactUnavailable`."""
    base = root / relpath
    if not base.is_dir():
        raise FactUnavailable(f"source missing: {relpath}")
    return sorted(p for p in base.glob(pattern) if p.is_file())


def _hook_script_paths(context: FactContext) -> list[Path]:
    """All registered hook scripts (``DOCS_HOOKS_COUNT`` set, IC-01 M1).

    ``hooks/**/*.sh`` minus the ``HOOK_EXCLUDED_DIRS`` path segments and minus
    the ``HOOK_EXCLUDED_SUFFIXES`` helpers. NF-12: the suffix is ``-impl.sh``
    (hyphen); ``_impl.sh`` would match nothing. Memoised for the duration of
    one call — the ``hooks/`` tree is rglobbed by the count and by the block.
    """
    root = context.agent_meta_root
    key = ("hook-scripts",)
    if key in context.sources:
        return context.sources[key]
    hooks_root = root / "hooks"
    if not hooks_root.is_dir():
        raise FactUnavailable("source missing: hooks")
    selected = []
    for path in sorted(hooks_root.rglob("*.sh")):
        relative = path.relative_to(hooks_root)
        if HOOK_EXCLUDED_DIRS & set(relative.parts[:-1]):
            continue
        if relative.name.endswith(HOOK_EXCLUDED_SUFFIXES):
            continue
        selected.append(path)
    context.sources[key] = selected
    return selected


def _agent_template_entries(context: FactContext) -> list[tuple[str, Path]]:
    """``(frontmatter name, path)`` of every real agent template, sorted.

    IC-02: files carrying a frontmatter ``name``, without the ``_*`` helper
    prefix (``AGENT_HELPER_PREFIX``). Memoised for the duration of one call —
    the ``agents/1-generic`` frontmatter is read by three count facts and by
    the roster block.
    """
    key = ("agent-templates",)
    if key in context.sources:
        return context.sources[key]
    entries = []
    for path in _glob_files(context.agent_meta_root, _AGENT_TEMPLATES_RELPATH, "*.md"):
        if path.name.startswith(AGENT_HELPER_PREFIX):
            continue
        name = _frontmatter(context, path).get("name")
        if isinstance(name, str) and name.strip():
            entries.append((name.strip(), path))
    result = sorted(entries)
    context.sources[key] = result
    return result


def _pipeline_state(config: Mapping[str, object]) -> dict[str, bool]:
    """Pipeline name -> enabled, after merging ``quality-pipelines.overrides``.

    IC-02: only ``enabled: false`` in the project override deactivates a
    pipeline. The base set comes from ``config/role-defaults.yaml`` and is
    merged by the caller; unknown override keys are ignored (an override for a
    pipeline that does not exist must not invent one).
    """
    section = config.get("quality-pipelines")
    overrides = _as_dict(section).get("overrides")
    state: dict[str, bool] = {}
    for name, override in _as_dict(overrides).items():
        if not isinstance(name, str):
            continue
        if _as_dict(override).get("enabled") is False:
            state[name] = False
    return state


def _yaml_key_comments(path: Path, relpath: str) -> dict[str, str]:
    """Map ``key`` -> the ``#`` comment written on the same line in the source.

    ``dod-presets.yaml`` carries each preset's rationale as an inline comment
    — a hand-written rationale that ``yaml.safe_load`` discards. Reading the
    raw line keeps the block honest: nothing is invented, and a preset without
    a comment renders as :data:`EMPTY_CELL`.
    """
    comments: dict[str, str] = {}
    for line in _read_text(path, relpath).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, _, rest = stripped.partition(":")
        rest = rest.strip()
        if not rest.startswith("#"):
            continue
        comments[key.strip()] = rest.lstrip("#").strip()
    return comments


def _md_cell(value: object) -> str:
    """One Markdown table cell: whitespace-collapsed, ``|``-escaped."""
    text = " ".join(str(value if value is not None else "").split())
    return text.replace("|", "\\|") if text else EMPTY_CELL


def _md_table(headers: tuple[str, ...], rows: list[tuple[object, ...]]) -> str:
    """Deterministic Markdown table — sorted input, stable column count."""
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("|" + "|".join("---" for _ in headers) + "|")
    lines.extend(
        "| " + " | ".join(_md_cell(cell) for cell in row) + " |" for row in rows
    )
    return "\n".join(lines)


# --------------------------------------------------------------------------
# scalar computers (IC-02 table)
# --------------------------------------------------------------------------


def _doc_version(context: FactContext) -> str:
    # IC-02 names ``read_version()`` (``config.py``), but this module is a
    # neutral leaf: importing ``config`` would create a config <-> doc_facts
    # import cycle once W1-6 wires the facts into the config bridge, and
    # ``read_version()`` answers a missing VERSION file with ``"unknown"`` —
    # a fact must be the truth or ``""``, never a plausible lie. The formula
    # is identical: exact file content, ``strip()``-ed.
    return _read_text(
        context.agent_meta_root / _VERSION_RELPATH, _VERSION_RELPATH
    ).strip()


def _doc_agent_templates_count(context: FactContext) -> str:
    return str(len(_agent_template_entries(context)))


def _doc_agents_se_count(context: FactContext) -> str:
    names = [
        name
        for name, _path in _agent_template_entries(context)
        if name.startswith(SE_ROLE_PREFIX)
    ]
    return str(len(names))


def _doc_agents_nonse_count(context: FactContext) -> str:
    entries = _agent_template_entries(context)
    se = sum(1 for name, _path in entries if name.startswith(SE_ROLE_PREFIX))
    return str(len(entries) - se)


def _template_role_names(context: FactContext) -> set[str]:
    """Role names of the generatable template universe (IC-04, deviated).

    The universe is :func:`roles.resolve_template_roles` — the *same* function
    sync resolves the generated set from (``collect_sources`` over
    ``agents/1-generic/`` + ``agents/2-platform/``, minus ``WRAPPER_TEMPLATES``,
    minus roles without a ROLE_MAP target). IC-04 names ``agents/1-generic/``
    alone; that glob misses the ``based-on:`` wrapper family and reported 53
    where the generator produces 58 (see the module docstring, W13-4). A fact
    that disagrees with the generated output is a wrong number, so the resolver
    wins over the spec sentence.

    Raises :class:`FactUnavailable` when a universe directory is missing or the
    resolver fails: ``Path.glob`` on an absent directory yields an empty set
    without complaint, and an empty universe would render a plausible ``0``
    instead of degrading. The presence check runs **before** the resolver so
    ``roles._cached_template_roles`` never memoises a degraded answer for this
    root. Failures are never written to the per-call memo.

    ``OSError``/``ValueError`` from the resolver are mapped to
    :class:`FactUnavailable` (an unusable source is an unavailable fact); any
    other exception type propagates unchanged and is degraded by the dispatcher
    exactly as ``_load_yaml_map``'s are.
    """
    key = ("template-role-names",)
    if key in context.sources:
        return context.sources[key]
    root = context.agent_meta_root
    for relpath in _TEMPLATE_UNIVERSE_RELPATHS:
        if not (root / relpath).is_dir():
            raise FactUnavailable(f"source missing: {relpath}")
    try:
        names = set(resolve_template_roles(root, context.config))
    except (OSError, ValueError) as exc:
        raise FactUnavailable(f"cannot resolve the template universe: {exc}") from exc
    context.sources[key] = names
    return names


def _registry_role_names(context: FactContext) -> frozenset[str]:
    """Role names declared in ``config/role-defaults.yaml::roles``, memoised.

    The registry leg of IC-04 (W13-6). ``roles.resolve_active_roles`` derives
    its layer 1 from this table, not from the template files, so a set derived
    from templates alone over-reports on a config without ``roles:``: it admits
    ``provider-expert``, which ``collect_sources`` excludes as a
    ``WRAPPER_TEMPLATES`` entry even though role-defaults declares it.

    ``roles.load_roles_config`` answers empty tables for a **missing** file, so
    the presence check (shared with :func:`_activation_gates`, which needs the
    same document) is load-bearing: without it a missing registry would return
    an empty universe and the count would collapse to ``0`` — a wrong number
    rather than a missing one.
    """
    key = ("registry-role-names",)
    if key in context.sources:
        return context.sources[key]
    root = context.agent_meta_root
    relpath = "config/role-defaults.yaml"
    _load_yaml_map(context, root / relpath, relpath)
    registry = _as_dict(load_roles_config(root).get("roles"))
    names = frozenset(registry)
    context.sources[key] = names
    return names


def _activation_gates(context: FactContext) -> dict:
    """``roles.resolve_activation_gates`` output, memoised for one call.

    The explicit ``_load_yaml_map`` on ``config/role-defaults.yaml`` is
    load-bearing, not a redundant read: ``roles.load_roles_config`` returns
    empty tables for a **missing** file instead of raising, so
    ``resolve_activation_gates`` alone would answer ``{}`` — every role then
    passes ``is_role_enabled`` and the count would be inflated by exactly the
    gated roles. The presence check turns that into :class:`FactUnavailable`,
    and it is free: the document is already memoised for the pipeline facts.
    """
    key = ("activation-gates",)
    if key in context.sources:
        return context.sources[key]
    root = context.agent_meta_root
    relpath = "config/role-defaults.yaml"
    _load_yaml_map(context, root / relpath, relpath)
    gates = resolve_activation_gates(root, context.config)
    context.sources[key] = gates
    return gates


def _declared_provider_names(config: Mapping[str, object]) -> set[str] | None:
    """Active provider names declared by the project config, ``None`` if absent.

    Same key precedence as ``providers.resolve_providers``; deliberately not
    that function, because it raises ``ValueError`` for an unregistered name
    while a fact must degrade (IC-01).
    """
    for key in PROVIDER_DECLARATION_KEYS:
        raw = config.get(key)
        if raw is None:
            continue
        if isinstance(raw, str):
            return {raw} if raw.strip() else None
        if isinstance(raw, (list, tuple)):
            return {str(item) for item in raw if isinstance(item, str) and item.strip()}
        return None
    return None


def _agents_capable_provider(
    provider_config: Mapping[str, object] | None, config: Mapping[str, object]
) -> bool | None:
    """Whether at least one active provider declares the ``agents`` capability.

    ``True``/``False`` when the question is answerable, ``None`` when it is not
    — an absent, empty or non-overlapping provider registry. ``None`` means
    *skip the dimension*, never "no provider can produce agents": turning a
    missing registry into ``False`` would render a fabricated ``0`` and
    reproduce the F21 class of wrong number (IC-01).
    """
    registry = _as_dict(provider_config)
    if not registry:
        return None
    declared = _declared_provider_names(config)
    names = sorted(registry) if declared is None else sorted(declared & set(registry))
    if not names:
        return None
    return any(
        provider_has_capability(registry.get(name), AGENTS_CAPABILITY) for name in names
    )


def _active_roles(context: FactContext) -> set[str]:
    """IC-04: ``roles:`` ∩ registry ∩ template universe ∩ gates ∩ agents-capable.

    Every leg is an intersection, so the order is irrelevant; the result is the
    set ``roles.resolve_active_roles(..., require_template=True)`` returns for
    the same inputs (minus the provider dimension, which sync has no notion of).
    The registry and universe legs are what make the ``roles:``-absent branch
    agree with the generator as well (W13-4, W13-6).

    Raises :class:`FactUnavailable` when a source the intersection needs is
    missing or unreadable; the dispatcher turns that into ``""`` plus one
    ``log.debug`` (IC-01).
    """
    if not context.agent_meta_root.is_dir():
        raise FactUnavailable(f"root missing: {context.agent_meta_root}")
    candidates = _template_role_names(context) & _registry_role_names(context)
    whitelist = context.config.get("roles")
    if isinstance(whitelist, (list, tuple, set, frozenset)):
        candidates = candidates & {
            str(role) for role in whitelist if isinstance(role, str) and role.strip()
        }
    gates = _activation_gates(context)
    active = {
        role for role in candidates if is_role_enabled(role, context.config, gates)
    }
    if _agents_capable_provider(context.provider_config, context.config) is False:
        return set()
    return active



def compute_active_roles(
    agent_meta_root: Path,
    config: dict,
    provider_config: dict | None = None,
) -> set[str]:
    """The gate-aware active role set (IC-04) — the F13/F21 comparison set.

    = ``set(config["roles"])`` ∩ *the role-defaults registry* ∩ *the generatable
    template universe* (``roles.resolve_template_roles``) ∩ *activation-gate
    winners* ∩ *at least one active provider declares ``agents``*. The two
    middle legs are what sync's ``roles.resolve_active_roles(...,
    require_template=True)`` applies, so the set is equal to the generated one
    for the same inputs (W13-4, W13-6; see the module docstring).

    Never ``len(config["roles"])``: ``se-component-requirements`` is listed in
    ``roles:`` and never generated, because ``systems-engineering.enabled:
    false`` closes the ``se`` activation group
    (``config/role-defaults.yaml::activation_groups``).

    Fail-soft (IC-01/AC-04): a missing or unreadable source raises
    :class:`FactUnavailable` — it never returns a partially-intersected set
    that would read as a real number. The registered computer
    (``DOCS_AGENTS_ACTIVE_COUNT``) degrades it to ``""``; a caller that cannot
    degrade should report the exception rather than invent an empty set.

    ``provider_config`` is the providers mapping of ``config/ai-providers.yaml``
    (``providers.load_providers_config``). ``None``/``{}`` means "not
    available" and *skips* the capability dimension.
    """
    context = FactContext(
        agent_meta_root=Path(agent_meta_root),
        config=_as_dict(config),
        provider_config=provider_config if isinstance(provider_config, dict) else None,
        log=None,
        scalars={},
        sources={},
    )
    return _active_roles(context)


def _doc_agents_active_count(context: FactContext) -> str:
    return str(len(_active_roles(context)))


def _doc_hooks_count(context: FactContext) -> str:
    return str(len(_hook_script_paths(context)))


def _doc_hooks_1generic_count(context: FactContext) -> str:
    relpath = "hooks/1-generic"
    paths = [
        path
        for path in _glob_files(context.agent_meta_root, relpath, "*.sh")
        if not path.name.endswith(HOOK_EXCLUDED_SUFFIXES)
    ]
    return str(len(paths))


def _doc_provider_count(context: FactContext) -> str:
    data = _load_yaml_map(
        context,
        context.agent_meta_root / "config" / "ai-providers.yaml",
        "config/ai-providers.yaml",
    )
    providers = data.get("providers")
    if not isinstance(providers, dict):
        raise FactUnavailable("config/ai-providers.yaml: no 'providers' mapping")
    return str(len(providers))


def _pipeline_definitions(context: FactContext) -> dict[str, dict]:
    data = _load_yaml_map(
        context,
        context.agent_meta_root / "config" / "role-defaults.yaml",
        "config/role-defaults.yaml",
    )
    pipelines = data.get("quality_pipelines")
    if not isinstance(pipelines, dict):
        raise FactUnavailable("config/role-defaults.yaml: no 'quality_pipelines'")
    return {
        name: _as_dict(body)
        for name, body in pipelines.items()
        if isinstance(name, str)
    }


def _doc_pipelines_count(context: FactContext) -> str:
    return str(len(_pipeline_definitions(context)))


def _doc_pipelines_active_count(context: FactContext) -> str:
    pipelines = _pipeline_definitions(context)
    disabled = _pipeline_state(context.config)
    active = sum(1 for name in pipelines if disabled.get(name, True) is not False)
    return str(active)


def _doc_dod_preset_count(context: FactContext) -> str:
    data = _load_yaml_map(
        context,
        context.agent_meta_root / "config" / "dod-presets.yaml",
        "config/dod-presets.yaml",
    )
    presets = data.get("presets")
    if not isinstance(presets, dict):
        raise FactUnavailable("config/dod-presets.yaml: no 'presets' mapping")
    return str(len(presets))


def _doc_tier_preset_count(context: FactContext) -> str:
    data = _load_yaml_map(
        context,
        context.agent_meta_root / "config" / "tier-presets.yaml",
        "config/tier-presets.yaml",
    )
    return str(len(data))


def _doc_command_count(context: FactContext) -> str:
    return str(len(_glob_files(context.agent_meta_root, _COMMANDS_RELPATH, "*.md")))


def _doc_scenario_count(context: FactContext) -> str:
    return str(
        len(_glob_files(context.agent_meta_root, _SCENARIO_ASSERTS_RELPATH, "*.sh"))
    )


def _doc_docs_file_count(context: FactContext) -> str:
    base = context.agent_meta_root / _DOCS_RELPATH
    if not base.is_dir():
        raise FactUnavailable(f"source missing: {_DOCS_RELPATH}")
    count = sum(
        1
        for path in base.rglob("*.md")
        if path.is_file()
        and not (DOCS_EXCLUDED_DIR_SEGMENTS & set(path.relative_to(base).parts))
    )
    return str(count)


# --------------------------------------------------------------------------
# block computers (IC-02 table, seven *_BLOCK facts)
# --------------------------------------------------------------------------


def _doc_agent_roster_block(context: FactContext) -> str:
    root = context.agent_meta_root
    roles = _as_dict(
        _load_yaml_map(
            context, root / "config" / "role-defaults.yaml", "config/role-defaults.yaml"
        ).get("roles")
    )
    rows = []
    for name, path in _agent_template_entries(context):
        role = name.removeprefix(TEMPLATE_NAME_PREFIX)
        meta = _as_dict(roles.get(role))
        description = (
            meta.get("short_desc")
            or meta.get("description")
            or _frontmatter(context, path).get("description")
        )
        rows.append((role, description, meta.get("workflow_tier", "")))
    return _md_table(("Role", "Description", "Workflow tier"), rows)


def _doc_pipelines_block(context: FactContext) -> str:
    pipelines = _pipeline_definitions(context)
    disabled = _pipeline_state(context.config)
    rows = []
    for name, body in sorted(pipelines.items()):
        stages = body.get("stages")
        rows.append(
            (
                name,
                len(stages) if isinstance(stages, list) else 0,
                "no" if disabled.get(name, True) is False else "yes",
            )
        )
    return _md_table(("Pipeline", "Stages", "Enabled"), rows)


def _doc_hooks_block(context: FactContext) -> str:
    root = context.agent_meta_root
    rows = []
    for path in _hook_script_paths(context):
        relpath = path.relative_to(root).as_posix()
        meta = parse_hook_metadata(_read_text(path, relpath))
        rows.append(
            (
                meta.get("hook") or path.stem,
                meta.get("event", ""),
                relpath,
            )
        )
    return _md_table(("Hook", "Trigger", "Path"), rows)


def _doc_providers_block(context: FactContext) -> str:
    data = _load_yaml_map(
        context,
        context.agent_meta_root / "config" / "ai-providers.yaml",
        "config/ai-providers.yaml",
    )
    rows = []
    for provider, body in sorted(_as_dict(data.get("providers")).items()):
        meta = _as_dict(body)
        capabilities = meta.get("capabilities")
        rows.append(
            (
                provider,
                meta.get("agents_dir", ""),
                ", ".join(str(c) for c in capabilities)
                if isinstance(capabilities, list)
                else "",
            )
        )
    return _md_table(("Provider", "Directory", "Capabilities"), rows)


def _doc_tier_preset_block(context: FactContext) -> str:
    relpath = "config/tier-presets.yaml"
    data = _load_yaml_map(context, context.agent_meta_root / relpath, relpath)
    rows = []
    for preset, body in sorted(data.items()):
        meta = _as_dict(body)
        tiers = _as_dict(meta.get("tiers"))
        rows.append(
            (
                preset,
                meta.get("description", ""),
                ", ".join(f"{tier}: {model}" for tier, model in sorted(tiers.items())),
            )
        )
    return _md_table(("Preset", "Description", "Models"), rows)


def _doc_dod_preset_block(context: FactContext) -> str:
    relpath = "config/dod-presets.yaml"
    path = context.agent_meta_root / relpath
    data = _load_yaml_map(context, path, relpath)
    comments = _yaml_key_comments(path, relpath)
    presets = _as_dict(data.get("presets"))
    rows = [
        (name, comments.get(name, ""))
        for name in sorted(presets, key=str)
        if isinstance(name, str)
    ]
    return _md_table(("Preset", "Rationale"), rows)


def _doc_repo_facts_block(context: FactContext) -> str:
    """Compact fact block for ``llms.txt`` — all scalars **except** volatile
    **and pending** — 14 rows (15 scalars minus ``DOCS_SCENARIO_COUNT``; nothing
    is pending since W1-3).

    IC-02:521 says "alle obigen **ohne** volatile" (14 rows); the deviation is
    deliberate: a pending fact is ``""`` and a fact block must not carry an
    empty row.

    Reads the already-computed scalars off the context: re-running the scalar
    computers here would duplicate I/O and, worse, double the ``log.debug``
    entries of a failing fact (IC-01 observability).

    **Ordering invariant:** this computer is the only one that reads
    ``context.scalars``, and it therefore depends on ``DOCS_REPO_FACTS_BLOCK``
    being the **last** entry of :data:`FACT_KEYS` — the dispatcher fills
    ``scalars`` in :data:`FACT_KEYS` order. Reordering ``FACT_KEYS`` would
    render an empty (or partial) block *silently*, because a block computer
    never raises. ``test_repo_facts_block_must_be_last_in_fact_keys`` pins the
    invariant; do not reorder ``FACT_KEYS`` without moving this fact.
    """
    rows = [
        (name, context.scalars.get(name, FACT_UNAVAILABLE))
        for name in _STABLE_SCALAR_FACT_KEYS
    ]
    return _md_table(("Fact", "Value"), rows)


#: Sanctioned extension point. A key that is absent keeps ``FACT_UNAVAILABLE``.
_FACT_COMPUTERS.update(
    {
        "DOCS_VERSION": _doc_version,
        "DOCS_AGENT_TEMPLATES_COUNT": _doc_agent_templates_count,
        "DOCS_AGENTS_SE_COUNT": _doc_agents_se_count,
        "DOCS_AGENTS_NONSE_COUNT": _doc_agents_nonse_count,
        "DOCS_AGENTS_ACTIVE_COUNT": _doc_agents_active_count,
        "DOCS_HOOKS_COUNT": _doc_hooks_count,
        "DOCS_HOOKS_1GENERIC_COUNT": _doc_hooks_1generic_count,
        "DOCS_PROVIDER_COUNT": _doc_provider_count,
        "DOCS_PIPELINES_COUNT": _doc_pipelines_count,
        "DOCS_PIPELINES_ACTIVE_COUNT": _doc_pipelines_active_count,
        "DOCS_DOD_PRESET_COUNT": _doc_dod_preset_count,
        "DOCS_TIER_PRESET_COUNT": _doc_tier_preset_count,
        "DOCS_COMMAND_COUNT": _doc_command_count,
        "DOCS_SCENARIO_COUNT": _doc_scenario_count,
        "DOCS_DOCS_FILE_COUNT": _doc_docs_file_count,
        "DOCS_AGENT_ROSTER_BLOCK": _doc_agent_roster_block,
        "DOCS_PIPELINES_BLOCK": _doc_pipelines_block,
        "DOCS_HOOKS_BLOCK": _doc_hooks_block,
        "DOCS_PROVIDERS_BLOCK": _doc_providers_block,
        "DOCS_TIER_PRESET_BLOCK": _doc_tier_preset_block,
        "DOCS_DOD_PRESET_BLOCK": _doc_dod_preset_block,
        "DOCS_REPO_FACTS_BLOCK": _doc_repo_facts_block,
    }
)


def is_volatile(name: str) -> bool:
    """True for the facts that must not reach ``README.md``/``llms.txt`` (R1)."""
    return name in VOLATILE_FACTS


def stable_facts(facts: Mapping[str, str]) -> dict[str, str]:
    """The non-volatile projection — the IC-14 ``facts-hash`` input rule.

    Used by the renderer (W1-7) and by the index footer (W3-2): a volatile
    value must not be rendered into a hybrid file and must not move the hash.
    """
    return {name: value for name, value in facts.items() if not is_volatile(name)}


BLOCK_FACT_KEYS: tuple[str, ...] = tuple(
    name for name in FACT_KEYS if name.endswith("_BLOCK")
)

SCALAR_FACT_KEYS: tuple[str, ...] = tuple(
    name for name in FACT_KEYS if not name.endswith("_BLOCK")
)

# Excludes the pending facts on top of ``VOLATILE_FACTS``: a pending fact is
# ``""`` and a fact block must not carry an empty row (see the IC-02:521
# deviation documented on ``_doc_repo_facts_block``).
_STABLE_SCALAR_FACT_KEYS: tuple[str, ...] = tuple(
    name
    for name in SCALAR_FACT_KEYS
    if name not in VOLATILE_FACTS and name not in PENDING_FACTS
)


def compute_doc_facts(
    agent_meta_root: Path,
    config: dict,
    *,
    provider_config: dict | None = None,
    log: object | None = None,
) -> dict[str, str]:
    """Return the full ``DOCS_*`` fact dict. Never raises on a missing source.

    Guarantees (AC-01): the key set is exactly :data:`FACT_KEYS`, every value is
    a ``str``, no exception escapes — not even from a fact implementation added
    later — and nothing below ``agent_meta_root`` is written.

    A non-existent ``agent_meta_root`` yields the full key set of empty strings
    plus one ``log.debug`` entry (IC-01 error path), never a ``SyncError``.

    The per-call source memo (``FactContext.sources``) is created fresh here
    and dropped on return: the module keeps **no** module-global cache, so two
    calls in one process always re-read the sources and a change on disk
    between them is observed.
    """
    facts: dict[str, str] = dict.fromkeys(FACT_KEYS, FACT_UNAVAILABLE)
    root = Path(agent_meta_root)
    base = FactContext(
        agent_meta_root=root,
        config=_as_dict(config),
        provider_config=provider_config if isinstance(provider_config, dict) else None,
        log=log,
        scalars={},
        sources={},
    )
    if not root.is_dir():
        _debug(log, "docs", f"doc_facts: root missing: {root}")
        return facts
    scalars: dict[str, str] = {}
    for name in FACT_KEYS:
        computer = _FACT_COMPUTERS.get(name)
        if computer is None:
            continue
        context = base._replace(scalars=scalars)
        try:
            value = computer(context)
        except Exception as exc:  # noqa: BLE001 — IC-01 never-raise contract, per-fact degradation to ""
            _debug(log, "docs", f"doc_facts: {name} not computable: {exc}")
            continue
        if value is None:
            # F-4: ``str(None)`` would render the literal word "None" as prose
            # in a README block — a fact is the truth or ``""``, never a lie.
            value = FACT_UNAVAILABLE
        elif not isinstance(value, str):
            value = str(value)
        facts[name] = value
        if name in SCALAR_FACT_KEYS:
            scalars[name] = value
    return facts
