"""AC-01/AC-02/AC-03 (IC-01, IC-02) — the ``DOCS_*`` fact contract.

The key set is the interface: ``compute_doc_facts()`` must return exactly the
placeholders enumerated in IC-02 of
``docs/specs/2026-09-25-repository-documentation-consolidation.md`` — no extra
key, no missing key — every value a ``str``, no exception on a missing or odd
source, and no write to any fact source below ``agent_meta_root``.

AC-01 states "exactly the 23 keys listed in IC-02", but the IC-02 table
enumerates **22** placeholders (15 scalar + 7 ``*_BLOCK``); the numeral is a
stale summary that was never updated when IC-02 grew (same error class as the
spec's own NF-5/NF-10/NEW-4 count corrections). The enumerated table wins: a
factum without source, formula and target site is exactly the unverified number
this initiative exists to remove. The set is spelled out in **three** places —
``FACT_KEYS`` in ``scripts/lib/doc_facts.py``, the ``IC02_KEYS`` oracle below
and the IC-02 table in the spec — so a spec correction is a three-place change,
not a two-place one.

AC-02 is enforced as **formulas**, never as numbers: the expected side of every
assertion is re-derived here from the canonical sources, independently of the
implementation under test. Per Spec NEW-8 the old ``xfail`` snapshot is gone;
the single place in the repo tree that may hold expected *numbers* is
``config/doc-facts-expected.yaml`` (IC-23, plan task W1-5).

Independence means *not restating the production algorithm*. For
``DOCS_AGENTS_ACTIVE_COUNT`` that rule has teeth (W13-5): the first version of
``_oracle_active_roles`` mirrored the production intersection line by line,
inherited its blind spot and agreed with its wrong number. The active-role
expectation is therefore taken from the **generator's** entry point
(``roles.resolve_active_roles(..., require_template=True)``) and cross-checked
against the generated ``.md`` files on disk, so a defect in either
implementation has to be mirrored in the other to go unnoticed.

NF-12 is pinned by ``test_hook_excluded_suffixes_use_hyphen``: the rule must be
``-impl.sh`` (hyphen). With ``_impl.sh`` (underscore) it matches nothing and
``DOCS_HOOKS_COUNT`` would run to 13 instead of 11.

AC-04 (fail-soft) and AC-05 (gate-aware active roles) are W1-3. The rule behind
``FACT_SOURCE_PATHS``: a source root must be in the write-invariance digest **at
the moment the fact starts reading it** — otherwise the no-write invariant
(AC-01) is silently void for that source. ``scripts`` therefore entered the list
with the first fact that imports ``scripts/lib/roles.py``; ``knowledge`` arrives
with W1-4.
"""

from __future__ import annotations

import copy
import fnmatch
import hashlib
import re
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
import yaml

from scripts.lib import doc_facts
from scripts.lib import roles as roles_lib
from scripts.lib.doc_facts import (
    AGENT_HELPER_PREFIX,
    AGENTS_CAPABILITY,
    BLOCK_FACT_KEYS,
    FACT_KEYS,
    HOOK_EXCLUDED_DIRS,
    HOOK_EXCLUDED_SUFFIXES,
    PENDING_FACTS,
    SCALAR_FACT_KEYS,
    VOLATILE_FACTS,
    compute_active_roles,
    compute_doc_facts,
    is_volatile,
    stable_facts,
)
from scripts.lib.roles import is_role_enabled, resolve_activation_gates

REPO_ROOT = Path(__file__).resolve().parent.parent

IC02_KEYS = frozenset({
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
})

FACT_SOURCE_PATHS = (
    "VERSION",
    ".meta-config",
    "agents/1-generic",
    "agents/2-platform",
    "commands/1-generic",
    "config",
    "docs",
    "hooks",
    # Read by the ``*_BLOCK`` facts via the W1-6 snippet bridge. The digest
    # helper skips a non-existent entry, so the root is covered by the digest
    # from the moment it exists — which is exactly the moment a fact starts
    # reading it (F-2). ``scripts`` (W1-3) and ``knowledge`` (W1-4) are added
    # by the tasks that start reading them, in their own commits.
    "scripts",
    "snippets",
    "tests/scenarios/asserts",
)

#: Paths that are legitimately absent in an intermediate wave state. A fact
#: source outside this set must exist — otherwise the no-write digest is void.
OPTIONAL_FACT_SOURCE_PATHS = frozenset({"snippets"})

_PLACEHOLDER_RE = re.compile(r"\{\{(DOCS_[A-Z0-9_]+)\}\}")


def _tree_hash(root: Path) -> str:
    """Path/size/mtime digest of every fact source below ``root``.

    Content is not hashed on purpose: reading must not change the digest, and
    path/size/mtime already move on create, write, rename and delete.
    """
    digest = hashlib.sha256()
    for rel in FACT_SOURCE_PATHS:
        source = root / rel
        if source.is_file():
            entries = [(source, source.stat())]
        elif source.is_dir():
            entries = [(p, p.lstat()) for p in sorted(source.rglob("*"))]
        else:
            continue
        for path, stat in entries:
            digest.update(str(path.relative_to(root)).encode("utf-8"))
            digest.update(str(stat.st_size).encode("utf-8"))
            digest.update(str(stat.st_mtime_ns).encode("utf-8"))
    return digest.hexdigest()


# ---------------------------------------------------------------------------
# independent oracles for the AC-02 formulas
#
# Every helper below re-derives the expected side straight from the canonical
# source. None of them imports ``doc_facts`` and none of them contains a
# hardcoded number (Spec NEW-8).
# ---------------------------------------------------------------------------


def _yaml(relpath: str) -> dict:
    return yaml.safe_load((REPO_ROOT / relpath).read_text(encoding="utf-8")) or {}


def _oracle_version() -> str:
    return (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()


def _frontmatter_segment(text: str) -> str:
    """The frontmatter block of a Markdown file, ``""`` when there is none.

    M3: the oracle must not scan the whole document. A template whose *body*
    contains a line starting with ``name:`` (a YAML example, a nested role
    description) would otherwise inflate the oracle and turn the
    implementation-vs-oracle comparison into a false failure. Mirrors
    ``lib.frontmatter``: the block only exists if the file starts with ``---``,
    and it ends at the second ``---`` delimiter.
    """
    if not text.startswith("---"):
        return ""
    parts = text.split("---", 2)
    return parts[1] if len(parts) == 3 else ""


def _oracle_template_names() -> list[str]:
    names = []
    for path in sorted((REPO_ROOT / "agents" / "1-generic").glob("*.md")):
        if path.name.startswith(AGENT_HELPER_PREFIX):
            continue
        text = path.read_text(encoding="utf-8")
        match = re.search(
            r"^name:\s*(.+?)\s*$", _frontmatter_segment(text), re.MULTILINE
        )
        if match:
            names.append(match.group(1).strip("\"'"))
    return sorted(names)


def _oracle_hooks() -> list[Path]:
    hooks_root = REPO_ROOT / "hooks"
    selected = []
    for path in sorted(hooks_root.rglob("*.sh")):
        parts = path.relative_to(hooks_root).parts[:-1]
        if HOOK_EXCLUDED_DIRS & set(parts):
            continue
        if path.name.endswith(HOOK_EXCLUDED_SUFFIXES):
            continue
        selected.append(path)
    return selected


def _oracle_hooks_1generic() -> list[Path]:
    return [
        path
        for path in sorted((REPO_ROOT / "hooks" / "1-generic").glob("*.sh"))
        if not path.name.endswith(HOOK_EXCLUDED_SUFFIXES)
    ]


def _oracle_providers() -> int:
    return len(_yaml("config/ai-providers.yaml")["providers"])


def _oracle_pipelines() -> dict:
    return _yaml("config/role-defaults.yaml")["quality_pipelines"]


def _oracle_disabled_pipelines(config: dict) -> set[str]:
    overrides = (config.get("quality-pipelines") or {}).get("overrides") or {}
    return {
        name
        for name, override in overrides.items()
        if (override or {}).get("enabled") is False
    }


def _oracle_dod_presets() -> int:
    return len(_yaml("config/dod-presets.yaml")["presets"])


def _oracle_tier_presets() -> int:
    return len(_yaml("config/tier-presets.yaml"))


def _oracle_commands() -> int:
    return len(list((REPO_ROOT / "commands" / "1-generic").glob("*.md")))


@pytest.fixture(scope="module")
def repo_config() -> dict:
    """The project configuration the formulas are evaluated against.

    AC-02 parameterises over *a* fixture configuration — the formulas must hold
    for a merged project config, not for a hardcoded scenario.
    """
    return _yaml(".meta-config/project.yaml")


@pytest.fixture(scope="module")
def facts(repo_config: dict) -> dict[str, str]:
    return compute_doc_facts(REPO_ROOT, repo_config, provider_config={})


# ---------------------------------------------------------------------------
# AC-01 — key set, types, fail-soft, write invariance
# ---------------------------------------------------------------------------


def test_fact_key_set_exact():
    """AC-01: the returned key set equals the IC-02 set exactly."""
    facts = compute_doc_facts(REPO_ROOT, {}, provider_config={})
    assert set(facts) == IC02_KEYS
    assert set(facts) == set(FACT_KEYS)
    assert len(facts) == len(IC02_KEYS) == 22


def test_fact_key_names_are_docs_namespace():
    """Namespace discipline (IC-02): every key carries the ``DOCS_`` prefix and
    the block variants end in ``_BLOCK``; no built-in is claimed."""
    for key in IC02_KEYS:
        assert key.startswith("DOCS_"), key
    assert "DOCS_LANGUAGE" not in IC02_KEYS
    assert "INTERNAL_DOCS_LANGUAGE" not in IC02_KEYS


def test_all_fact_values_are_str():
    facts = compute_doc_facts(REPO_ROOT, {}, provider_config={})
    for key, value in facts.items():
        assert isinstance(value, str), f"{key} -> {type(value).__name__}"


def test_perfect_typing_of_config_arguments_is_optional():
    """``config``/``provider_config``/``log`` are duck-typed: ``None`` and a
    minimal object with ``debug`` both work."""
    for kwargs in ({}, {"config": None}, {"provider_config": None}):
        config = kwargs.pop("config", {}) or {}
        facts = compute_doc_facts(REPO_ROOT, config, **kwargs)
        assert set(facts) == IC02_KEYS
        assert all(isinstance(v, str) for v in facts.values())


def test_missing_root_is_fail_soft():
    """AC-01 error path: a non-existent root yields the full key set of empty
    strings instead of an exception (IC-01: no ``SyncError``)."""
    facts = compute_doc_facts(REPO_ROOT / "does-not-exist", {})
    assert set(facts) == IC02_KEYS
    assert all(value == "" for value in facts.values())


def test_no_write_to_agent_meta_root():
    """AC-01: no fact source below ``agent_meta_root`` changes during a call.

    The non-empty assertion keeps the test from degrading into comparing two
    empty digests: with an empty registry nothing would be read at all.
    """
    before = _tree_hash(REPO_ROOT)
    facts = compute_doc_facts(REPO_ROOT, {}, provider_config={})
    assert any(facts.values()), "no fact was computed — the digest proves nothing"
    assert _tree_hash(REPO_ROOT) == before


def test_registry_covers_every_non_pending_fact():
    """Every IC-02 key is either computed or explicitly marked pending.

    Without this, a typo in ``_FACT_COMPUTERS`` would silently degrade a fact
    to ``""`` and every other test would still pass.
    """
    assert set(doc_facts._FACT_COMPUTERS) | set(PENDING_FACTS) == set(FACT_KEYS)
    assert not set(doc_facts._FACT_COMPUTERS) & set(PENDING_FACTS)
    for marker in PENDING_FACTS.values():
        assert marker, "a pending fact must name the dependency it waits for"


def test_digest_helper_is_not_vacuous(tmp_path):
    """Negative control: the write-invariance digest really reacts.

    Without this, a wrong ``FACT_SOURCE_PATHS`` would make
    ``test_no_write_to_agent_meta_root`` compare two empty digests and pass
    forever.
    """
    empty_digest = _tree_hash(tmp_path)
    assert empty_digest == _tree_hash(tmp_path), "digest must be deterministic"

    (tmp_path / "hooks" / "1-generic").mkdir(parents=True)
    assert _tree_hash(tmp_path) != empty_digest, "new file went unnoticed"

    after_create = _tree_hash(tmp_path)
    (tmp_path / "hooks" / "1-generic" / "a.sh").write_text("#!/bin/bash\n")
    assert _tree_hash(tmp_path) != after_create, "new content went unnoticed"

    after_write = _tree_hash(tmp_path)
    (tmp_path / "hooks" / "1-generic" / "a.sh").unlink()
    assert _tree_hash(tmp_path) != after_write, "deletion went unnoticed"


def test_fact_sources_exist_in_this_checkout():
    """Guards the premise of the digest: every scoped source is present.

    ``snippets/`` is tolerated while it does not exist yet (created by W1-6);
    the digest helper skips a non-existent entry, so the root enters the digest
    exactly when it starts existing.
    """
    for rel in FACT_SOURCE_PATHS:
        if rel in OPTIONAL_FACT_SOURCE_PATHS and not (REPO_ROOT / rel).exists():
            continue
        assert (REPO_ROOT / rel).exists(), f"fact source missing: {rel}"


def test_hook_excluded_suffixes_use_hyphen():
    """NF-12: the suffix rule must be ``-impl.sh``; ``_impl.sh`` matches
    nothing and would push ``DOCS_HOOKS_COUNT`` to 13 instead of 11."""
    assert HOOK_EXCLUDED_SUFFIXES == ("-impl.sh",)
    assert "_impl.sh" not in HOOK_EXCLUDED_SUFFIXES
    helpers = sorted(p.name for p in (REPO_ROOT / "hooks").rglob("*-impl.sh"))
    assert helpers, "no *-impl.sh helper found — premise of NF-12 broken"
    for name in helpers:
        assert name.endswith(HOOK_EXCLUDED_SUFFIXES), name
        assert not name.endswith("_impl.sh"), name


def test_hook_and_agent_exclusion_constants():
    assert HOOK_EXCLUDED_DIRS == frozenset({"lib", "release-gates"})
    assert AGENT_HELPER_PREFIX == "_"
    helper = REPO_ROOT / "agents" / "1-generic" / f"{AGENT_HELPER_PREFIX}helper.md"
    assert not helper.exists(), "fixture helper must not exist as a template"
    assert list((REPO_ROOT / "agents" / "1-generic").glob(f"{AGENT_HELPER_PREFIX}*.md"))


def test_dispatch_is_provider_agnostic():
    """NFA-03: no ``if provider == "Name"`` branch in the module."""
    source = (REPO_ROOT / "scripts" / "lib" / "doc_facts.py").read_text(
        encoding="utf-8"
    )
    assert "provider ==" not in source
    assert "provider in (" not in source


# ---------------------------------------------------------------------------
# IC-01 observability — a raising computer degrades and is reported once
# ---------------------------------------------------------------------------


class _StubLog:
    """Duck-typed ``SyncLog`` stand-in that records every ``debug`` call."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def debug(self, target: str, message: str) -> None:
        self.calls.append((target, message))


def test_failing_computer_degrades_and_is_reported_once(monkeypatch):
    """F-3 / IC-01: a broken fact implementation is fail-soft *and* visible.

    Two halves that used to be unexercised: the per-fact ``except`` in the
    dispatcher and the ``_debug`` helper. Before W1-2 no test passed a ``log``
    and the registry was empty, so neither line ran.
    """

    def _boom(_context):
        raise RuntimeError("simulated source failure")

    monkeypatch.setitem(doc_facts._FACT_COMPUTERS, "DOCS_VERSION", _boom)
    log = _StubLog()
    facts = compute_doc_facts(REPO_ROOT, {}, provider_config={}, log=log)

    assert facts["DOCS_VERSION"] == ""
    assert len(log.calls) == 1, f"expected exactly one debug call, got {log.calls}"
    target, message = log.calls[0]
    assert target == "docs"
    assert "DOCS_VERSION" in message
    # The rest of the dict is unaffected — one broken source, one fact.
    assert facts["DOCS_HOOKS_COUNT"] != ""


def test_none_returning_computer_degrades_to_empty(monkeypatch):
    """F-4: a ``None`` return must not render as the literal word ``None``."""
    monkeypatch.setitem(
        doc_facts._FACT_COMPUTERS, "DOCS_VERSION", lambda _context: None
    )
    facts = compute_doc_facts(REPO_ROOT, {}, provider_config={})
    assert facts["DOCS_VERSION"] == ""
    assert "None" not in facts["DOCS_REPO_FACTS_BLOCK"]


# ---------------------------------------------------------------------------
# F13/F21 — the active-role count is deferred, never approximated
# ---------------------------------------------------------------------------


SE_ROLE: str = "se-component-requirements"


def test_active_roles_count_is_gate_aware_not_approximated(repo_config):
    """F21: ``DOCS_AGENTS_ACTIVE_COUNT`` is computed, never ``len(roles)``.

    W1-3 removed the pending marker. The number must now come from the
    gate-aware intersection; a ``len(config["roles"])`` fallback would still be
    a wrong number (it counts the roles the gate excludes) even though the key
    is registered.
    """
    assert "DOCS_AGENTS_ACTIVE_COUNT" not in PENDING_FACTS
    assert "DOCS_AGENTS_ACTIVE_COUNT" in doc_facts._FACT_COMPUTERS
    assert "DOCS_AGENTS_ACTIVE_COUNT" in doc_facts._STABLE_SCALAR_FACT_KEYS

    active = compute_active_roles(REPO_ROOT, repo_config)
    assert active, "the intersection collapsed — premise of this test broken"
    facts = compute_doc_facts(REPO_ROOT, repo_config, provider_config={})
    assert facts["DOCS_AGENTS_ACTIVE_COUNT"] == str(len(active))
    assert int(facts["DOCS_AGENTS_ACTIVE_COUNT"]) <= len(repo_config["roles"])


def test_active_count_parity_with_framework_resolver(repo_config):
    """W13-4: the fact must equal what the generator resolves, not a 1-generic glob.

    IC-04 names ``agents/1-generic/`` as the source of the "real templates"
    term. Implemented literally, the fact reported **53** while
    ``roles.resolve_active_roles(..., require_template=True)`` returned **58**
    and the generated trees held 58 agent files each — a plausible wrong number
    with no degradation signal, caused entirely by the five ``*-expert`` roles
    that exist only as ``based-on:`` wrappers in ``agents/2-platform/``.

    This is the contract that pins the deliberate IC-04 deviation recorded in
    the ``doc_facts`` module docstring: the fact's number is the generator's
    number. The expected side is re-derived (Spec NEW-8) — no literal count
    appears in this file.
    """
    resolved = roles_lib.resolve_active_roles(
        REPO_ROOT, repo_config, require_template=True, warn_sink=[]
    )
    assert resolved, "premise: the generator resolves a non-empty role set"

    facts = compute_doc_facts(REPO_ROOT, repo_config, provider_config={})
    assert facts["DOCS_AGENTS_ACTIVE_COUNT"] == str(len(resolved)), (
        "DOCS_AGENTS_ACTIVE_COUNT contradicts roles.resolve_active_roles"
    )
    assert compute_active_roles(REPO_ROOT, repo_config) == set(resolved)

    # The 2-platform wrapper family is the whole difference: it must be *in* the
    # universe, otherwise the parity above is satisfied for the wrong reason.
    platform_only = {
        role
        for role in resolved
        if not (REPO_ROOT / "agents" / "1-generic" / f"{role}.md").is_file()
    }
    assert platform_only, (
        "premise broken: no role reaches the generated set only via "
        "agents/2-platform/ — the IC-04 deviation would be untested"
    )
    assert platform_only <= roles_lib.resolve_template_roles(REPO_ROOT, repo_config)


GENERATED_AGENT_DIRS: tuple[str, ...] = (".claude/agents", ".opencode/agents")


@pytest.mark.parametrize("relpath", GENERATED_AGENT_DIRS)
def test_active_count_matches_generated_agent_files(relpath, repo_config):
    """W13-4: the fact must equal the number of agent files sync generated.

    The one leg of the evidence that is not a re-derivation at all — it counts
    the generated ``.md`` files on disk, so it cannot share a blind spot with
    either implementation. The directories are git-ignored generated output, so
    the test skips (rather than fails) on a checkout that has not been synced
    yet; the resolver parity above is the always-on half of the contract.
    """
    agents_dir = REPO_ROOT / relpath
    if not agents_dir.is_dir():
        pytest.skip(f"{relpath} is generated output and absent in this checkout")
    generated = {path.stem for path in agents_dir.glob("*.md")}
    facts = compute_doc_facts(REPO_ROOT, repo_config, provider_config={})
    assert facts["DOCS_AGENTS_ACTIVE_COUNT"] == str(len(generated)), (
        f"{relpath} holds {len(generated)} agent files — the fact must agree"
    )


def test_active_count_without_roles_key_matches_resolver(repo_config):
    """W13-6: the ``roles:``-absent branch must not drift either.

    A bare config (the ``roles:`` key removed) is a reachable input, and it was
    the second half of the same root cause: with the whitelist leg gone, the old
    1-generic glob reported **62** against the resolver's **66** — a net
    undercount of four in the dangerous direction, with no degradation signal.
    Two independent errors cancelled into one wrong number: the five
    ``*-expert`` roles were missing (-5, they live in ``agents/2-platform/``)
    and ``provider-expert`` was spuriously admitted (+1, a ``WRAPPER_TEMPLATES``
    entry the template universe excludes). The registry leg
    (``config/role-defaults.yaml::roles``) is what sync filters from, so the
    branch needs it even when no whitelist is configured.

    Note that dropping ``roles:`` does **not** simply widen the set:
    ``resolve_activation_gates`` closes the ``developer_tiers`` and ``validator``
    groups unless their roles are explicitly whitelisted, so the bare set trades
    four whitelisted roles for twelve that no whitelist mentioned. The two
    branches are genuinely different inputs, which is why both need the
    resolver-parity assertion.
    """
    bare = {key: value for key, value in repo_config.items() if key != "roles"}
    assert "roles" not in bare, "premise: the fixture config really has roles:"

    resolved = roles_lib.resolve_active_roles(
        REPO_ROOT, bare, require_template=True, warn_sink=[]
    )
    facts = compute_doc_facts(REPO_ROOT, bare, provider_config={})
    assert facts["DOCS_AGENTS_ACTIVE_COUNT"] == str(len(resolved))
    assert compute_active_roles(REPO_ROOT, bare) == set(resolved)
    assert set(resolved) != set(
        roles_lib.resolve_active_roles(
            REPO_ROOT, repo_config, require_template=True, warn_sink=[]
        )
    ), "premise: the roles:-absent branch must be a different input, not a copy"
    assert "provider-expert" not in set(resolved), (
        "provider-expert is a WRAPPER_TEMPLATES entry — collect_sources "
        "excludes it, so it can never be in the generatable universe"
    )


def _oracle_active_roles(config: dict) -> set[str]:
    """IC-04 re-derived through the **generator's** path, not a clone of ours.

    Why this is independent (AC-02, W13-5). The previous version of this oracle
    was a line-by-line restatement of ``compute_active_roles``: same
    ``agents/1-generic/`` glob, same ``removeprefix("template-")``, same
    intersection, same ``is_role_enabled`` call site. A clone inherits the blind
    spot of the code it mirrors — it agreed with the wrong **53** of W13-4 and
    would have *failed* the corrected 58 instead of catching the defect, which
    is the exact opposite of an oracle. Restating production logic cannot
    contradict it.

    This version asks a different question — *which roles does sync generate?* —
    and answers it with sync's own entry point,
    ``roles.resolve_active_roles(..., require_template=True)``. The two paths
    share no code: that one starts from
    ``config/role-defaults.yaml::roles`` (the registry) and filters it by
    whitelist, gates and the template universe; production starts from the
    intersection of three independently memoised sources. A defect would have
    to be present in both derivations simultaneously to go unnoticed, and the
    W13-4 defect was not — it lived in production's source selection alone.

    ``warn_sink=[]`` keeps the resolver's "role without template" diagnostics
    off stderr; the test asserts on the set, not on the warnings.
    """
    return set(
        roles_lib.resolve_active_roles(
            REPO_ROOT, config, require_template=True, warn_sink=[]
        )
    )


def test_se_role_excluded_by_gate_not_by_roles_list(repo_config):
    """AC-05: the SE role is dropped by the **gate**, not by the roles list.

    The distinction needs all four legs:

    1. the role **is** listed in ``roles:`` — so the roles list does not drop it;
    2. a real agent template **exists** — so the template dimension does not
       either;
    3. the activation group whose ``role_patterns`` match the role is
       **disabled** by ``systems-engineering.enabled: false``;
    4. flipping **only** that flag puts the role back into the set — the single
       changed variable, which is what makes the gate the cause.
    """
    assert SE_ROLE in repo_config["roles"], "premise: the role is whitelisted"
    template = REPO_ROOT / "agents" / "1-generic" / f"{SE_ROLE}.md"
    assert template.is_file(), "premise: a real template exists for the role"

    assert repo_config["systems-engineering"]["enabled"] is False
    gates = resolve_activation_gates(REPO_ROOT, repo_config)
    matching = {
        name: spec
        for name, spec in gates.items()
        if any(
            fnmatch.fnmatchcase(SE_ROLE, str(pattern))
            for pattern in (spec.get("role_patterns") or [])
        )
    }
    assert matching, "premise: the role belongs to at least one activation group"
    for name, spec in matching.items():
        assert spec.get("enabled") is False, f"group {name} is not closed"
    assert not is_role_enabled(SE_ROLE, repo_config, gates)

    active = compute_active_roles(REPO_ROOT, repo_config)
    assert SE_ROLE not in active, "the closed gate must exclude the role"
    assert len(active) < len(repo_config["roles"]), (
        "AC-05: the active set must be strictly smaller than the roles list"
    )

    opened = copy.deepcopy(repo_config)
    opened["systems-engineering"]["enabled"] = True
    assert SE_ROLE in compute_active_roles(REPO_ROOT, opened), (
        "flipping the gate flag alone must re-admit the role — otherwise the "
        "exclusion came from some other dimension, not from the gate"
    )


def _fact_active_count(root: Path, config: dict, provider_config: dict | None) -> str:
    """The registered fact as a string — the path the docs actually render."""
    return compute_doc_facts(root, config, provider_config=provider_config)[
        "DOCS_AGENTS_ACTIVE_COUNT"
    ]


def test_active_roles_provider_dimension_is_fail_soft(repo_config):
    """IC-04's last term degrades, it does not fabricate a ``0``.

    An absent provider registry means "unknown", so the dimension is skipped;
    a registry that is present but declares no ``agents`` capability is a
    computed empty set.
    """
    baseline = compute_active_roles(REPO_ROOT, repo_config)
    assert baseline
    assert compute_active_roles(REPO_ROOT, repo_config, None) == baseline
    assert compute_active_roles(REPO_ROOT, repo_config, {}) == baseline
    assert (
        compute_active_roles(REPO_ROOT, repo_config, {"NoSuchProvider": {}}) == baseline
    )

    registry = _yaml("config/ai-providers.yaml")["providers"]
    assert any(
        AGENTS_CAPABILITY in (entry.get("capabilities") or [])
        for entry in registry.values()
    ), "premise: at least one registered provider declares 'agents'"
    assert compute_active_roles(REPO_ROOT, repo_config, registry) == baseline

    without_agents = {name: dict(entry) for name, entry in registry.items()}
    for entry in without_agents.values():
        entry["capabilities"] = [
            cap for cap in (entry.get("capabilities") or []) if cap != AGENTS_CAPABILITY
        ]
    assert compute_active_roles(REPO_ROOT, repo_config, without_agents) == set()
    assert _fact_active_count(REPO_ROOT, repo_config, without_agents) == "0"


_FACT_TREE_COPY_PATHS: tuple[str, ...] = (
    "VERSION",
    ".meta-config",
    "agents/1-generic",
    "agents/2-platform",
    "commands/1-generic",
    "config",
    "docs",
    "hooks",
    "tests/scenarios/asserts",
)


def _copy_fact_tree(root: Path) -> Path:
    """Copy every fact source of the real checkout into ``root``.

    A copy of the *real* tree (not a synthetic fixture) is what makes AC-04
    meaningful: it proves that one missing source degrades exactly one fact
    while every other fact still resolves against genuine data.
    """
    for rel in _FACT_TREE_COPY_PATHS:
        source = REPO_ROOT / rel
        target = root / rel
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    return root


def test_missing_source_is_fail_soft(tmp_path, repo_config):
    """AC-04: a missing source degrades **that** fact to ``""``.

    ``config/ai-providers.yaml`` is the canonical example: it feeds
    ``DOCS_PROVIDER_COUNT`` and ``DOCS_PROVIDERS_BLOCK``. Both must fall back
    to ``""`` — with exactly one ``log.debug`` per degraded fact, no
    ``SyncError`` and no other fact affected.
    """
    root = _copy_fact_tree(tmp_path)
    control = compute_doc_facts(root, repo_config, provider_config={})
    # W13-7: the premise is scoped to the two facts this test is *about*. The
    # former ``all(control[key] != "" for key in FACT_KEYS)`` claimed that all 22
    # facts are computable from this tree — a claim about every other task in
    # the wave, asserted here. Any fact that legitimately degrades or is still
    # pending would break this test far from its subject. The "nothing else
    # degraded" half is asserted *relatively* further down (degraded set ==
    # exactly these two keys), which needs no completeness premise at all.
    assert control["DOCS_PROVIDER_COUNT"] != "", "premise: the source exists"
    assert control["DOCS_PROVIDERS_BLOCK"] != "", (
        "premise: the count is not the only reader of the source"
    )

    (root / "config" / "ai-providers.yaml").unlink()
    log = _StubLog()
    facts = compute_doc_facts(root, repo_config, provider_config={}, log=log)

    assert facts["DOCS_PROVIDER_COUNT"] == ""
    assert facts["DOCS_PROVIDERS_BLOCK"] == ""
    # "No other fact affected" is a *relative* claim, measured against the
    # control run — a fact that was already empty before the deletion is not
    # collateral damage (W13-7).
    subject = {"DOCS_PROVIDER_COUNT", "DOCS_PROVIDERS_BLOCK"}
    survivors = [key for key in FACT_KEYS if control[key] != "" and key not in subject]
    assert survivors, "premise: the control run computed facts that must survive"
    for key in survivors:
        assert facts[key] != "", f"{key} must survive a missing ai-providers.yaml"

    degraded = sorted(
        key for key, value in facts.items() if value == "" and control[key] != ""
    )
    assert degraded == sorted(
        {"DOCS_PROVIDER_COUNT", "DOCS_PROVIDERS_BLOCK"}
    )
    assert len(log.calls) == len(degraded), (
        f"expected one debug per degraded fact, got {log.calls}"
    )
    for target, message in log.calls:
        assert target == "docs"
        assert any(key in message for key in degraded), message


def test_active_roles_degrades_when_its_sources_are_missing(tmp_path, repo_config):
    """IC-01 for the new role path: a missing gate source yields ``""``.

    ``config/role-defaults.yaml`` is the load-bearing source. Without the
    presence check in ``_activation_gates`` the framework loader would answer
    empty tables, every role would pass the (absent) gate and the count would
    be inflated — a wrong number instead of a missing one.
    """
    root = _copy_fact_tree(tmp_path)
    control = compute_doc_facts(root, repo_config, provider_config={})
    assert control["DOCS_AGENTS_ACTIVE_COUNT"] == str(
        len(compute_active_roles(root, repo_config))
    )

    (root / "config" / "role-defaults.yaml").unlink()
    log = _StubLog()
    facts = compute_doc_facts(root, repo_config, provider_config={}, log=log)
    assert facts["DOCS_AGENTS_ACTIVE_COUNT"] == "", (
        "a missing gate source must degrade, not fall back to len(roles)"
    )
    assert any("DOCS_AGENTS_ACTIVE_COUNT" in message for _t, message in log.calls)

    with pytest.raises(doc_facts.FactUnavailable):
        compute_active_roles(root, repo_config)


@pytest.mark.parametrize("relpath", ("agents/1-generic", "agents/2-platform"))
def test_active_roles_degrades_when_templates_are_missing(
    tmp_path, repo_config, relpath
):
    """IC-01, other leg: a missing template directory yields ``""`` as well.

    ``agents/2-platform/`` is in the list since W13-4: ``Path.glob`` on an
    absent directory returns an empty set without complaint, so dropping the
    2-platform presence check would turn a missing source into a silently
    shrunken universe — a plausible undercount instead of a degradation.
    """
    root = _copy_fact_tree(tmp_path)
    shutil.rmtree(root / relpath)
    facts = compute_doc_facts(root, repo_config, provider_config={})
    assert facts["DOCS_AGENTS_ACTIVE_COUNT"] == ""
    if relpath == "agents/1-generic":
        assert facts["DOCS_AGENT_TEMPLATES_COUNT"] == ""


# ---------------------------------------------------------------------------
# AC-02 — the 13 scalar formulas
# ---------------------------------------------------------------------------


def _formula_se_plus_nonse_equals_templates(facts, config):
    return int(facts["DOCS_AGENTS_SE_COUNT"]) + int(
        facts["DOCS_AGENTS_NONSE_COUNT"]
    ) == int(facts["DOCS_AGENT_TEMPLATES_COUNT"])


def _formula_se_equals_se_prefixed_templates(facts, config):
    names = _oracle_template_names()
    return int(facts["DOCS_AGENTS_SE_COUNT"]) == sum(
        1 for name in names if name.startswith("se-")
    )


def _formula_nonse_equals_remaining_templates(facts, config):
    names = _oracle_template_names()
    expected = sum(1 for name in names if not name.startswith("se-"))
    return int(facts["DOCS_AGENTS_NONSE_COUNT"]) == expected


def _formula_provider_count_equals_providers_mapping(facts, config):
    return int(facts["DOCS_PROVIDER_COUNT"]) == _oracle_providers()


def _formula_hooks_count_equals_glob_minus_exclusions(facts, config):
    return int(facts["DOCS_HOOKS_COUNT"]) == len(_oracle_hooks())


def _formula_hooks_1generic_equals_glob_minus_impl(facts, config):
    return int(facts["DOCS_HOOKS_1GENERIC_COUNT"]) == len(_oracle_hooks_1generic())


def _formula_hooks_1generic_le_hooks_count(facts, config):
    return int(facts["DOCS_HOOKS_1GENERIC_COUNT"]) <= int(facts["DOCS_HOOKS_COUNT"])


def _formula_pipelines_active_equals_count_minus_disabled(facts, config):
    # The disabled set is intersected with the real pipeline keys: production
    # ignores an override that names a non-existent pipeline, so an unfiltered
    # subtraction would make a stale override key fail the suite (N5).
    pipelines = _oracle_pipelines()
    disabled = _oracle_disabled_pipelines(config) & set(pipelines)
    expected = len(pipelines) - len(disabled)
    return int(facts["DOCS_PIPELINES_ACTIVE_COUNT"]) == expected


def _formula_pipelines_active_le_count(facts, config):
    return int(facts["DOCS_PIPELINES_ACTIVE_COUNT"]) <= int(
        facts["DOCS_PIPELINES_COUNT"]
    )


def _formula_dod_preset_count_equals_presets(facts, config):
    return int(facts["DOCS_DOD_PRESET_COUNT"]) == _oracle_dod_presets()


def _formula_tier_preset_count_equals_top_level_keys(facts, config):
    return int(facts["DOCS_TIER_PRESET_COUNT"]) == _oracle_tier_presets()


def _formula_command_count_equals_glob(facts, config):
    return int(facts["DOCS_COMMAND_COUNT"]) == _oracle_commands()


def _formula_active_count_equals_gate_aware_intersection(facts, config):
    return int(facts["DOCS_AGENTS_ACTIVE_COUNT"]) == len(_oracle_active_roles(config))


def _formula_active_count_le_templates(facts, config):
    return int(facts["DOCS_AGENTS_ACTIVE_COUNT"]) <= int(
        facts["DOCS_AGENT_TEMPLATES_COUNT"]
    )


def _formula_active_count_le_roles_list(facts, config):
    return int(facts["DOCS_AGENTS_ACTIVE_COUNT"]) <= len(config.get("roles") or [])


def _formula_version_equals_version_file(facts, config):
    return facts["DOCS_VERSION"] == _oracle_version()


SCALAR_FORMULA_CASES = (
    ("se_plus_nonse_equals_templates", _formula_se_plus_nonse_equals_templates),
    ("se_equals_se_prefixed_templates", _formula_se_equals_se_prefixed_templates),
    ("nonse_equals_remaining_templates", _formula_nonse_equals_remaining_templates),
    (
        "provider_count_equals_providers_mapping",
        _formula_provider_count_equals_providers_mapping,
    ),
    (
        "hooks_count_equals_glob_minus_exclusions",
        _formula_hooks_count_equals_glob_minus_exclusions,
    ),
    (
        "hooks_1generic_equals_glob_minus_impl",
        _formula_hooks_1generic_equals_glob_minus_impl,
    ),
    ("hooks_1generic_le_hooks_count", _formula_hooks_1generic_le_hooks_count),
    (
        "pipelines_active_equals_count_minus_disabled",
        _formula_pipelines_active_equals_count_minus_disabled,
    ),
    ("pipelines_active_le_count", _formula_pipelines_active_le_count),
    ("dod_preset_count_equals_presets", _formula_dod_preset_count_equals_presets),
    (
        "tier_preset_count_equals_top_level_keys",
        _formula_tier_preset_count_equals_top_level_keys,
    ),
    ("command_count_equals_glob", _formula_command_count_equals_glob),
    (
        "active_count_equals_gate_aware_intersection",
        _formula_active_count_equals_gate_aware_intersection,
    ),
    ("active_count_le_templates", _formula_active_count_le_templates),
    ("active_count_le_roles_list", _formula_active_count_le_roles_list),
    ("version_equals_version_file", _formula_version_equals_version_file),
)


@pytest.mark.parametrize(
    ("formula_id", "formula"),
    SCALAR_FORMULA_CASES,
    ids=[case[0] for case in SCALAR_FORMULA_CASES],
)
def test_scalar_fact_formulas(formula_id, formula, facts, repo_config):
    """AC-02: the scalar formulas, one assertion each, no hardcoded number.

    Every expected side is re-derived from the canonical source inside the
    oracle helpers — Spec NEW-8 removed the ``xfail`` snapshot, so this file
    must not contain a single expected *count*.
    """
    assert formula(facts, repo_config), f"formula violated: {formula_id}"


# ---------------------------------------------------------------------------
# AC-03 — volatile marking
# ---------------------------------------------------------------------------


def test_volatile_fact_absent_from_hybrid_files(facts):
    """AC-03: only the scenario count is volatile, and it never reaches a
    hybrid file (``README.md``/``llms.txt``) nor moves the ``facts-hash``.

    The synthetic all-keys document is the non-vacuous half: it proves the
    renderer mechanism *would* substitute the value, so the real-file check is
    not passing merely because no placeholder exists there yet.
    """
    assert VOLATILE_FACTS == frozenset({"DOCS_SCENARIO_COUNT"})
    assert VOLATILE_FACTS <= set(FACT_KEYS)
    assert is_volatile("DOCS_SCENARIO_COUNT")
    assert facts["DOCS_SCENARIO_COUNT"] != "", "volatile fact must be computable"

    stable = stable_facts(facts)
    assert "DOCS_SCENARIO_COUNT" not in stable
    assert set(stable) == set(FACT_KEYS) - VOLATILE_FACTS
    for name, value in stable.items():
        assert value == facts[name], name

    synthetic = "".join(f"{{{{{name}}}}}\n" for name in FACT_KEYS)
    with_volatile = _PLACEHOLDER_RE.sub(
        lambda m: facts.get(m.group(1), m.group(0)), synthetic
    )
    without_volatile = _PLACEHOLDER_RE.sub(
        lambda m: stable.get(m.group(1), m.group(0)), synthetic
    )
    assert "{{DOCS_SCENARIO_COUNT}}" not in with_volatile, (
        "negative control broken — the renderer substitutes nothing"
    )
    assert "{{DOCS_SCENARIO_COUNT}}" in without_volatile
    for name in stable:
        if stable[name]:
            assert f"{{{{{name}}}}}" not in without_volatile, name

    for target in ("README.md", "llms.txt"):
        path = REPO_ROOT / target
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        rendered = _PLACEHOLDER_RE.sub(
            lambda m: stable.get(m.group(1), m.group(0)), text
        )
        for name in VOLATILE_FACTS:
            placeholder = f"{{{{{name}}}}}"
            assert rendered.count(placeholder) == text.count(
                placeholder
            ), f"{target}: volatile placeholder {name} was substituted"


# --- N1: the per-call source cache -----------------------------------------
#
# ``doc_facts`` memoises the expensive source reads (YAML documents, agent
# frontmatter, the ``hooks/`` glob) through ``FactContext.sources``. The memo
# must die with the call: a module-global cache is a silent wrong-fact
# generator, because a second sync in the same process would render the
# previous checkout's numbers. Both halves are pinned below — the cache
# collapses repeated reads *inside* one call, and it is *not* visible *across*
# two calls.

_MINIMAL_YAML_SOURCE = "config/ai-providers.yaml"


def _write_providers(root: Path, count: int) -> None:
    """Write a minimal ``config/ai-providers.yaml`` with ``count`` providers."""
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / _MINIMAL_YAML_SOURCE).write_text(
        "providers:\n"
        + "".join(f"  provider-{i}:\n    agents_dir: .p{i}\n" for i in range(count)),
        encoding="utf-8",
    )


def test_source_cache_is_scoped_to_one_call(tmp_path):
    """N1: two calls, a changed source in between — the second must see it.

    A module-global memo would return the first call's count here. The
    assertion is on a *memoised* source (a YAML document), not on
    ``DOCS_VERSION`` which is read uncached, so it really exercises
    ``FactContext.sources``.
    """
    _write_providers(tmp_path, 2)
    first = compute_doc_facts(tmp_path, {})
    assert first["DOCS_PROVIDER_COUNT"] == "2"

    _write_providers(tmp_path, 5)
    second = compute_doc_facts(tmp_path, {})
    assert second["DOCS_PROVIDER_COUNT"] == "5", (
        "a module-global source cache leaked across calls — a sync would "
        "render the previous checkout's numbers"
    )
    assert first["DOCS_PROVIDER_COUNT"] == "2", "the earlier result was mutated"


def test_source_cache_collapses_repeated_reads_within_one_call(monkeypatch):
    """N1: the memo is effective — every source is read once per call.

    ``config/role-defaults.yaml`` feeds three facts and the agent frontmatter
    four, so without the memo the dispatcher re-parses them. Asserting
    "each distinct source exactly once" also guards against a cache that
    silently stops being consulted.
    """
    yaml_paths: list[Path] = []
    frontmatter_paths: list[Path] = []
    real_yaml = doc_facts.load_yaml_file
    real_frontmatter = doc_facts.parse_frontmatter_file

    def _counting_yaml(path, *args, **kwargs):
        yaml_paths.append(Path(path))
        return real_yaml(path, *args, **kwargs)

    def _counting_frontmatter(path):
        frontmatter_paths.append(Path(path))
        return real_frontmatter(path)

    monkeypatch.setattr(doc_facts, "load_yaml_file", _counting_yaml)
    monkeypatch.setattr(doc_facts, "parse_frontmatter_file", _counting_frontmatter)

    facts = compute_doc_facts(REPO_ROOT, {})

    # non-vacuity: the counters really fired
    assert facts["DOCS_PROVIDER_COUNT"] != ""
    assert len(yaml_paths) >= 2
    assert frontmatter_paths
    assert len(yaml_paths) == len(set(yaml_paths)), (
        f"a YAML source was parsed more than once: "
        f"{[p.name for p in yaml_paths if yaml_paths.count(p) > 1]}"
    )
    assert len(frontmatter_paths) == len(set(frontmatter_paths))
    role_defaults = [p for p in yaml_paths if p.name == "role-defaults.yaml"]
    assert len(role_defaults) == 1, f"role-defaults.yaml parsed {len(role_defaults)}x"


# --- N4: the ordering contract of DOCS_REPO_FACTS_BLOCK ---------------------


def test_repo_facts_block_must_be_last_in_fact_keys(facts):
    """N4: ``DOCS_REPO_FACTS_BLOCK`` reads ``context.scalars``.

    The dispatcher fills ``scalars`` in ``FACT_KEYS`` order, so the block only
    renders if it runs last. A reordering would render an empty table *without
    raising* — the block computer degrades to ``""`` and the suite stayed green.
    """
    assert FACT_KEYS[-1] == "DOCS_REPO_FACTS_BLOCK"

    stable = doc_facts._STABLE_SCALAR_FACT_KEYS
    assert stable, "the fact block would be empty by construction"
    for name in stable:
        assert name in SCALAR_FACT_KEYS, name
        assert FACT_KEYS.index(name) < FACT_KEYS.index("DOCS_REPO_FACTS_BLOCK"), (
            f"{name} is computed after DOCS_REPO_FACTS_BLOCK"
        )


# --- N6: the content block computers are asserted ---------------------------
#
# ~180 LOC of block computers rendered into a Markdown table. A raising block
# computer degrades to ``""`` and every scalar assertion stayed green, so the
# whole render surface W1-7 depends on was unverified. Each block now gets a
# shape assertion and a non-vacuity assertion derived from the canonical
# source — never a hardcoded number (Spec NEW-8).

_CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")


def _split_md_row(line: str) -> list[str]:
    return [cell.strip() for cell in _CELL_SPLIT_RE.split(line.strip().strip("|"))]


def _parse_md_table(block: str) -> tuple[list[str], list[list[str]]]:
    """Split a ``_md_table`` block into ``(header cells, data rows)``.

    Also validates the table *shape* — a header line, an all-``---`` separator
    of the same width and a constant row width — so a malformed block fails
    with a readable message instead of a downstream renderer crash.
    """
    assert block.strip(), "empty block"
    lines = [line for line in block.splitlines() if line.strip()]
    assert len(lines) >= 2, f"table without a separator: {lines!r}"
    header = _split_md_row(lines[0])
    separator = _split_md_row(lines[1])
    assert separator == ["---"] * len(header), (
        f"separator {lines[1]!r} does not match the {len(header)} header columns"
    )
    rows = [_split_md_row(line) for line in lines[2:]]
    return header, rows


def _oracle_dod_preset_names() -> list[str]:
    return sorted(_yaml("config/dod-presets.yaml")["presets"])


def _block_row_oracles() -> dict[str, Callable[[], int]]:
    """``*_BLOCK`` fact -> the number of rows it must carry, re-derived."""
    return {
        "DOCS_AGENT_ROSTER_BLOCK": lambda: len(_oracle_template_names()),
        "DOCS_PIPELINES_BLOCK": lambda: len(_oracle_pipelines()),
        "DOCS_HOOKS_BLOCK": lambda: len(_oracle_hooks()),
        "DOCS_PROVIDERS_BLOCK": _oracle_providers,
        "DOCS_TIER_PRESET_BLOCK": _oracle_tier_presets,
        "DOCS_DOD_PRESET_BLOCK": lambda: len(_oracle_dod_preset_names()),
        "DOCS_REPO_FACTS_BLOCK": lambda: len(doc_facts._STABLE_SCALAR_FACT_KEYS),
    }


def test_every_block_fact_has_a_content_assertion():
    """N6: the row oracles must cover the block key set exhaustively.

    Without this, a new ``*_BLOCK`` fact would be added to ``FACT_KEYS`` with
    no content assertion and the block suite would stay green.
    """
    assert set(_block_row_oracles()) == set(BLOCK_FACT_KEYS)


@pytest.mark.parametrize("key", sorted(BLOCK_FACT_KEYS))
def test_block_fact_is_a_well_formed_table(facts, key):
    """N6 shape: a non-degraded block is a constant-width Markdown table."""
    assert facts[key] != "", f"{key} degraded to the fail-soft default"
    header, rows = _parse_md_table(facts[key])
    assert header and all(header), f"{key}: empty header cell in {header!r}"
    ragged = [row for row in rows if len(row) != len(header)]
    assert not ragged, f"{key}: ragged table rows {ragged[:1]!r}"
    # No empty-cell assertion here: ``_md_cell`` renders an empty value as
    # ``EMPTY_CELL`` (em-dash), so such a check could never fire. The
    # load-bearing guards are the non-degradation above and the row width.


@pytest.mark.parametrize("key", sorted(BLOCK_FACT_KEYS))
def test_block_fact_is_not_vacuous(facts, key):
    """N6 non-vacuity: the block carries one row per canonical source entry.

    The expected count is re-derived from the source the block renders, so a
    block that silently degraded to a header-only table fails here even though
    the fail-soft contract keeps it a ``str``.
    """
    expected = _block_row_oracles()[key]()
    assert expected > 0, f"oracle for {key} is empty — premise broken"
    _header, rows = _parse_md_table(facts[key])
    assert len(rows) == expected, f"{key}: {len(rows)} rows, oracle says {expected}"


def test_repo_facts_block_renders_the_stable_scalars(facts):
    """N4 + N6: the block lists exactly the non-volatile, non-pending scalars.

    The 13-row shape of the deliberate IC-02:521 deviation is asserted
    structurally (one row per stable scalar key) rather than as a literal, so
    a future scalar does not need the test edited.
    """
    stable = doc_facts._STABLE_SCALAR_FACT_KEYS
    assert "DOCS_SCENARIO_COUNT" not in stable, "volatile fact leaked into block"
    assert not set(stable) & set(PENDING_FACTS), "pending fact leaked into block"
    assert set(stable) <= set(SCALAR_FACT_KEYS)
    assert not set(stable) & set(BLOCK_FACT_KEYS)

    _header, rows = _parse_md_table(facts["DOCS_REPO_FACTS_BLOCK"])
    assert [row[0] for row in rows] == list(stable)
    rendered = dict(rows)
    for name, value in rendered.items():
        assert value == facts[name], f"{name}: block disagrees with the scalar"

