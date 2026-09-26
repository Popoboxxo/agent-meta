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
with W1-4, whose IC-03 staleness resolver is the first reader of
``knowledge/wiki/``.

W1-4 adds the IC-03 resolver and its ``test_v7_missing_and_stale_derived_from``
coverage. The V7 **check** itself is W2-3 and is deliberately *not* implemented
here — the resolver only has to produce the machine state the check will consume,
and it must be able to name ``missing-derived-from`` and ``stale-source``
without a single ``SyncError``. Two properties get their own pinned tests
because they are the ones a future refactor would break silently: the resolver is
**not** wired into ``_FACT_COMPUTERS`` (no IC-02 fact consumes it yet), and the
``status:stale-upstream`` marker is **extracted from the Langfassung**, never
read from the hand-maintained wiki tag and never from the ``ARCHITECTURE.md``
stub that loses its prose after W4 (Spec A12, M-5/M-7).

**PLAN DEBT (F7) — the IC-03 block below is split out at W2-1.** This file
carries the IC-02 fact contract *and* the IC-03 wiki-staleness contract, and the
plan keeps naming it for W2-1, W2-2, W2-6 and W8-4, so it only grows from here.
W1-4 already extracted the shared fixture helper (``_derived_page``) to stop the
duplication, but the file itself is past comfortable review size. **W2-1 owns
the split**: move the whole IC-03 staleness block — everything from the
``WIKI_ROOT_RELPATH`` constants down to the end of this file, including the
``stale_upstream_status`` cases — into a new
``tests/test_doc_facts_wiki_staleness.py`` with its own module docstring, and
leave the IC-02 fact contract here. Do not do that split before W2-1: the new
file does not exist yet, and creating it here would hand W2-1 a half-moved
block. Nothing about the assertions changes in the move — this is a file
boundary, not a behaviour change.
"""

from __future__ import annotations

import copy
import fnmatch
import hashlib
import os
import re
import shutil
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from scripts.lib import config as config_lib
from scripts.lib import doc_facts
from scripts.lib import roles as roles_lib
from scripts.lib.consistency import docs as docs_lib
from scripts.lib.consistency import placeholders as placeholders_lib
from scripts.lib.doc_facts import (
    AGENT_HELPER_PREFIX,
    AGENTS_CAPABILITY,
    ARCHITECTURE_STUB_RELPATH,
    BLOCK_FACT_KEYS,
    DERIVED_AT_KEY,
    DERIVED_FROM_KEY,
    FACT_KEYS,
    HOOK_EXCLUDED_DIRS,
    HOOK_EXCLUDED_SUFFIXES,
    LANGFASSUNG_RELPATHS,
    PENDING_FACTS,
    SCALAR_FACT_KEYS,
    STALE_UPSTREAM_STATUS,
    VOLATILE_FACTS,
    WIKI_AGE_PREFIX,
    WIKI_ARCHITECTURE_TYPE,
    WIKI_FRESH,
    WIKI_MISSING_DERIVED_FROM,
    WIKI_STALE_SOURCE,
    compute_active_roles,
    compute_doc_facts,
    compute_wiki_staleness,
    is_volatile,
    stable_facts,
    stale_upstream_status,
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
    # reading it (F-2). ``scripts`` joined in W1-3, ``knowledge`` in W1-4, each
    # in the commit that started reading it.
    "scripts",
    "snippets",
    # F-2 (W1-4): the IC-03 staleness resolver is the first reader of the
    # knowledge bundle, so ``knowledge`` enters the digest **in this commit**.
    # The governing rule: a fact's source root must be covered by the
    # write-invariance digest at the moment the fact starts reading it —
    # otherwise the AC-01 no-write invariant is silently void for that source.
    # ``knowledge/sources/`` is immutable raw data (NG-2) and is never written;
    # the resolver reads ``knowledge/wiki/`` only.
    "knowledge",
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


# ---------------------------------------------------------------------------
# W1-6 (IC-11) — the snippet bridge and the DOCS_ placeholder namespace
# ---------------------------------------------------------------------------

DOCS_SNIPPET_DIR = REPO_ROOT / "snippets" / "docs"

#: IC-11 enumerates exactly six (file stem, variable stem) pairs. Spelled out
#: here as a literal so a seventh snippet has to be a deliberate spec change.
IC11_SNIPPETS: tuple[tuple[str, str], ...] = (
    ("repo-facts", "DOCS_REPO_FACTS"),
    ("agent-roster", "DOCS_AGENT_ROSTER"),
    ("pipelines", "DOCS_PIPELINES"),
    ("hooks", "DOCS_HOOKS"),
    ("providers", "DOCS_PROVIDERS"),
    ("tier-presets", "DOCS_TIER_PRESET"),
)

_DOCS_FRONTMATTER_RE = re.compile(r"\A---\r?\n(?P<fm>.*?)\r?\n---(?:\r?\n|\Z)", re.DOTALL)


def _docs_snippet_body(path: Path) -> str:
    """Re-derive the inlined body from the file, independently of config.py.

    Same contract as ``config.py:_load_block_snippet`` (frontmatter strip, CRLF
    normalisation, ``strip("\\n")``) but re-stated here, so the assertion does
    not pass by calling the implementation under test.
    """
    text = path.read_text(encoding="utf-8")
    match = _DOCS_FRONTMATTER_RE.match(text)
    assert match is not None, f"{path.name} has no YAML frontmatter"
    return text[match.end():].replace("\r\n", "\n").replace("\r", "\n").strip("\n")


def test_docs_snippet_inlining_contract():
    """AC-25 (IC-11): frontmatter in, frontmatter-free variable out.

    Both halves are proven per snippet: the file on disk carries its own YAML
    frontmatter, and ``variables[var]`` is that body without the frontmatter,
    CRLF-normalised and without a leading/trailing newline. ``QUALITY_PIPELINES_BLOCK``
    is asserted byte-equal to its source file to pin the no-regression half.
    """
    variables: dict = {}
    config_lib._build_snippet_variables(variables, REPO_ROOT)

    for stem, var_stem in IC11_SNIPPETS:
        path = DOCS_SNIPPET_DIR / f"{stem}.md"
        var = f"{var_stem}_BLOCK"
        assert path.is_file(), f"missing snippet {path}"
        raw = path.read_text(encoding="utf-8")
        assert raw.startswith("---"), f"{path.name} lost its frontmatter on disk"
        assert "\n---" in raw, f"{path.name} frontmatter is not terminated"
        body = _docs_snippet_body(path)
        assert body, f"{path.name} has an empty body after the frontmatter"

        value = variables[var]
        assert value == body, f"{var}: inlined value != frontmatter-free body"
        assert not value.startswith("---"), f"{var} still starts with frontmatter"
        assert "\r" not in value, f"{var} is not CRLF-normalised"
        assert value == value.strip("\n"), f"{var} has a leading/trailing newline"
        for key in ("snippet:", "version:", "language:", "runtime:"):
            assert key not in value, f"{var} leaked frontmatter key {key!r}"
        assert f"{{{{{var}}}}}" in body, f"{path.name} does not reference {var}"

    # AC-25, no-regression half: the pre-existing orchestrator block is untouched.
    quality = (REPO_ROOT / "snippets" / "orchestrator" / "quality-pipelines.md").read_text(
        encoding="utf-8"
    )
    assert variables["QUALITY_PIPELINES_BLOCK"] == quality

    # The bridge is additive: exactly the six files of IC-11 exist, and the DoD
    # preset block has no snippet target (open gap, fail-soft per IC-01).
    assert len(sorted(DOCS_SNIPPET_DIR.glob("*.md"))) == 6, sorted(
        DOCS_SNIPPET_DIR.glob("*.md")
    )
    assert not (DOCS_SNIPPET_DIR / "dod-presets.md").exists()
    assert variables.get("DOCS_DOD_PRESET_BLOCK", "") == ""

    # R12: the docs snippets must not touch the built-in language variables.
    for name in ("DOCS_LANGUAGE", "INTERNAL_DOCS_LANGUAGE"):
        assert name not in variables
        assert name in placeholders_lib._BUILTIN_VARS


def test_docs_prefix_registered_in_placeholders():
    """AC-06 (IC-06): ``^DOCS_`` is a dynamic prefix, so a DOCS_ name is known.

    Asserted three ways: the anchored regex from IC-06 is registered, every
    block/scalar fact name matches it, and ``check_placeholders`` produces **no**
    ``placeholders.unknown`` finding for a template using ``{{DOCS_PROVIDERS_BLOCK}}``.
    The lowercase near-miss keeps the prefix from degrading to a bare ``^DOCS_``.
    """
    assert any(p.pattern == r"^DOCS_[A-Z0-9_]+$" for p in placeholders_lib._DYNAMIC_PREFIXES)

    matched = [
        name for name in IC02_KEYS
        if any(p.match(name) for p in placeholders_lib._DYNAMIC_PREFIXES)
    ]
    assert set(matched) == set(IC02_KEYS), sorted(set(IC02_KEYS) - set(matched))
    assert not any(p.match("docs_providers_block") for p in placeholders_lib._DYNAMIC_PREFIXES)

    body = "---\nname: doc-fact-consumer\n---\n\n{{DOCS_PROVIDERS_BLOCK}}\n"
    findings = placeholders_lib.check_placeholders(
        Path("agents/1-generic/developer.md"), body, REPO_ROOT
    )
    assert not [f for f in findings if f.check == "placeholders.unknown"], [
        (f.check, f.severity, f.message) for f in findings
    ]

    # DOCS_LANGUAGE stays a built-in (R12) — the prefix does not take it over.
    assert "DOCS_LANGUAGE" in placeholders_lib._BUILTIN_VARS
    assert "INTERNAL_DOCS_LANGUAGE" in placeholders_lib._BUILTIN_VARS


# --------------------------------------------------------------------------
# IC-03 — the wiki staleness resolver (W1-4)
# --------------------------------------------------------------------------
#
# The expected side is always re-derived from a synthetic wiki built in
# ``tmp_path`` or from the frontmatter itself — never from a hand-written
# expected-value table (Spec NEW-8: the only place in the tree that may hold
# expected *numbers* is ``config/doc-facts-expected.yaml``, W1-5). The
# ``mtime``/``derived-at`` pair is set with ``os.utime`` so the
# ``stale-source`` verdict is produced by the filesystem, not by a stubbed
# comparator.

WIKI_ROOT_RELPATH = "knowledge/wiki"
LANGFASSUNG_RELPATH = LANGFASSUNG_RELPATHS[0]
LEGACY_LANGFASSUNG_RELPATH = LANGFASSUNG_RELPATHS[-1]

STALE_DECLARATION = (
    "> Repo version: 9.9.9 — content last substantively reviewed: 2026-01-01 "
    "(predates several releases; a full architecture re-review is due — marker)"
)
FRESH_DECLARATION = (
    "> Repo version: 9.9.9 — content last substantively reviewed: 2026-01-01"
)


def _wiki_page(
    root: Path,
    relpage: str,
    frontmatter: dict,
    *,
    body: str = "# page\n",
) -> Path:
    """Write a Markdown page with YAML frontmatter below ``root``."""
    page = root / relpage
    page.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---"]
    for key, value in frontmatter.items():
        if isinstance(value, (list, tuple)):
            rendered = "[" + ", ".join(f'"{item}"' for item in value) + "]"
        elif isinstance(value, bool):
            rendered = "true" if value else "false"
        elif isinstance(value, (int, float)):
            rendered = str(value)
        else:
            rendered = f'"{value}"'
        lines.append(f"{key}: {rendered}")
    lines += ["---", "", body]
    page.write_text("\n".join(lines), encoding="utf-8")
    return page


def _make_project(root: Path, *, langfassung_body: str | None = STALE_DECLARATION) -> Path:
    """A minimal project root: ``knowledge/wiki/concepts/`` + a Langfassung."""
    (root / WIKI_ROOT_RELPATH / "concepts").mkdir(parents=True, exist_ok=True)
    if langfassung_body is not None:
        langfassung = root / LANGFASSUNG_RELPATH
        langfassung.parent.mkdir(parents=True, exist_ok=True)
        langfassung.write_text(
            f"# Langfassung\n\n{langfassung_body}\n", encoding="utf-8"
        )
    return root


def _set_mtime(path: Path, moment: datetime) -> None:
    epoch = moment.timestamp()
    os.utime(path, (epoch, epoch))


def _days_ago(days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)


SOURCE_RELPATH = "docs/source.md"
"""The canonical ``derived-from`` target of the IC-03 fixtures."""

_ABSENT = object()
"""Sentinel: write **no** ``derived-at`` key — not an *unusable* one."""


def _write_source(
    root: Path,
    relpath: str = SOURCE_RELPATH,
    mtime: datetime | None = None,
) -> Path:
    """Create ``relpath`` under ``root`` with a **pinned** mtime.

    ``stale-source`` is a filesystem comparison, so a fixture that left the mtime
    at "now" would answer differently depending on how fast the suite runs. The
    call is idempotent, so one source can back several pages.
    """
    source = root / relpath
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("# source\n", encoding="utf-8")
    if mtime is not None:
        _set_mtime(source, mtime)
    return source


def _derived_page(
    root: Path,
    name: str,
    derived_at: object = _ABSENT,
    *,
    source_mtime: datetime,
    derived_from: str | None = None,
) -> Path:
    """The IC-03 fixture in one call: a dated source plus an Architecture page.

    Spelling out "write a source, stamp its mtime, declare a page" in every test
    is what grew this block past review size (F7), so each test now states only
    its own premise: when the source changed (``source_mtime``), when the page
    was derived (``derived_at``, or ``_ABSENT`` to omit the key) and which
    ``derived-from`` spelling to use. Expected values are never passed in — Spec
    NEW-8 keeps every assertion re-deriving its own expectation from the same two
    timestamps.

    A fixture with a genuinely different shape (the real ``knowledge/sources/``
    page with its extra ``resource:`` key) stays explicit rather than growing a
    knob here.
    """
    _write_source(root, SOURCE_RELPATH, source_mtime)
    frontmatter: dict = {
        "type": WIKI_ARCHITECTURE_TYPE,
        DERIVED_FROM_KEY: SOURCE_RELPATH if derived_from is None else derived_from,
    }
    if derived_at is not _ABSENT:
        frontmatter[DERIVED_AT_KEY] = (
            derived_at.isoformat() if isinstance(derived_at, datetime) else derived_at
        )
    return _wiki_page(root / WIKI_ROOT_RELPATH / "concepts", name, frontmatter)


def test_v7_missing_and_stale_derived_from(tmp_path):
    """AC-10 shape, resolver half: both V7 inputs are named by the resolver.

    IC-03's rule: a ``type: Architecture`` page **without** ``derived-from`` is
    ``missing-derived-from``; a page whose ``derived-from`` target was modified
    **after** its ``derived-at`` is ``stale-source``. The finding text W2-3 will
    render has to come out of these two values, so they must carry the reason
    themselves — a bare boolean would force the check to re-derive the
    distinction.

    The V7 check is **not** implemented here (W2-3); this pins the state the
    check consumes.
    """
    root = _make_project(tmp_path)
    concepts = tmp_path / WIKI_ROOT_RELPATH / "concepts"

    _wiki_page(
        concepts,
        "no-provenance.md",
        {"type": WIKI_ARCHITECTURE_TYPE, "title": "no provenance"},
    )

    derived_at = _days_ago(10)
    _derived_page(
        root, "stale.md", derived_at,
        source_mtime=derived_at + timedelta(days=1),
    )

    states = compute_wiki_staleness(tmp_path / WIKI_ROOT_RELPATH, root)

    assert states["concepts/no-provenance.md"] == WIKI_MISSING_DERIVED_FROM
    assert states["concepts/stale.md"] == WIKI_STALE_SOURCE
    assert WIKI_MISSING_DERIVED_FROM != WIKI_STALE_SOURCE, (
        "the two V7 reasons must be distinguishable values, not one boolean"
    )


def test_resolver_states_are_exactly_the_four_documented_values():
    """IC-03: the value domain is closed — no fifth state can leak out.

    The four are ``""`` / ``missing-derived-from`` / ``stale-source`` /
    ``age-<n>d``. A closed domain is what lets W2-3 map values to severities
    with an exhaustive match instead of a default branch.
    """
    states = compute_wiki_staleness(REPO_ROOT / WIKI_ROOT_RELPATH, REPO_ROOT)
    assert states, "premise: the real wiki has pages"
    allowed = {WIKI_FRESH, WIKI_MISSING_DERIVED_FROM, WIKI_STALE_SOURCE}
    for relpage, value in states.items():
        assert isinstance(value, str), relpage
        assert value in allowed or re.fullmatch(rf"{WIKI_AGE_PREFIX}\d+d", value), (
            f"{relpage}: undocumented state {value!r}"
        )
        assert value != "age-0d", (
            f"{relpage}: a zero age is the absence of an observation"
        )


def test_resolver_reports_every_wiki_page_exactly_once():
    """The key set is the wiki page set, re-derived from disk (not a count)."""
    wiki = REPO_ROOT / WIKI_ROOT_RELPATH
    expected = {
        p.relative_to(wiki).as_posix() for p in wiki.rglob("*.md") if p.is_file()
    }
    assert expected, "premise: the real wiki has pages"
    states = compute_wiki_staleness(wiki, REPO_ROOT)
    assert set(states) == expected
    assert all(key == key.strip() and "\\" not in key for key in states), (
        "keys must be relative POSIX paths, not absolute or platform-specific"
    )


def test_missing_derived_from_is_only_reported_for_architecture_pages(tmp_path):
    """A page that never claimed a provenance must not be given a finding.

    ``missing-derived-from`` is a statement about a *duty* that
    ``knowledge/schema.md`` imposes on ``type: Architecture`` pages. Applying it
    to every page would turn "has no provenance" into a repo-wide alarm — the
    permanent-false-alarm shape (F21) this module exists to avoid.
    """
    root = _make_project(tmp_path)
    concepts = tmp_path / WIKI_ROOT_RELPATH / "concepts"
    for page_type in ("Concept", "Guide", "API Reference", "Plan", "Spec"):
        _wiki_page(concepts, f"{page_type}.md", {"type": page_type})
    _wiki_page(
        concepts, "arch.md", {"type": WIKI_ARCHITECTURE_TYPE}
    )

    states = compute_wiki_staleness(tmp_path / WIKI_ROOT_RELPATH, root)
    assert states["concepts/arch.md"] == WIKI_MISSING_DERIVED_FROM
    for page_type in ("Concept", "Guide", "API Reference", "Plan", "Spec"):
        assert states[f"concepts/{page_type}.md"] == WIKI_FRESH, page_type


def test_stale_source_is_the_mtime_comparison_against_derived_at(tmp_path):
    """The verdict is the *filesystem* comparison, not a date heuristic.

    Two pages, same ``derived-from``, opposite ``derived-at``: one whose source
    is newer must be ``stale-source``, one whose source is older must not. If
    the implementation compared the source mtime against ``now`` instead, both
    would answer the same and the first assertion would pass alone.
    """
    root = _make_project(tmp_path)
    pivot = _days_ago(30)
    _derived_page(
        root, "newer-source.md", pivot - timedelta(days=1), source_mtime=pivot
    )
    _derived_page(
        root, "older-source.md", pivot + timedelta(days=1), source_mtime=pivot
    )

    states = compute_wiki_staleness(tmp_path / WIKI_ROOT_RELPATH, root)
    assert states["concepts/newer-source.md"] == WIKI_STALE_SOURCE
    assert states["concepts/older-source.md"] != WIKI_STALE_SOURCE


def test_age_state_is_derived_from_derived_at_not_hardcoded(tmp_path):
    """``age-<n>d`` is a whole-day observation, computed from ``derived-at``.

    Per Spec NEW-8 the expected ``n`` is re-derived here from the same
    ``derived-at`` the fixture writes, not written as a literal.
    """
    root = _make_project(tmp_path)
    ages = (3, 40)
    for age in ages:
        derived_at = _days_ago(age)
        _derived_page(
            root, f"age-{age}.md", derived_at,
            source_mtime=derived_at - timedelta(days=1),
        )

    states = compute_wiki_staleness(tmp_path / WIKI_ROOT_RELPATH, root)
    for age in ages:
        value = states[f"concepts/age-{age}.md"]
        assert value == f"{WIKI_AGE_PREFIX}{age}d", (
            f"age {age}: got {value!r} — the day count is not re-derived"
        )


def test_age_state_is_not_reported_for_a_sub_day_derivation(tmp_path):
    """A derivation from today is fresh, not ``age-0d``.

    ``age-0d`` would be indistinguishable from a real measurement, and a check
    that renders it as a status would report a staleness that does not exist.
    """
    root = _make_project(tmp_path)
    now = datetime.now(timezone.utc)
    _derived_page(root, "today.md", now, source_mtime=now - timedelta(hours=2))

    states = compute_wiki_staleness(tmp_path / WIKI_ROOT_RELPATH, root)
    assert states["concepts/today.md"] == WIKI_FRESH


def test_stale_source_wins_over_the_age_observation(tmp_path):
    """Precedence: a stale source is a *status*, the age is only an observation.

    Without an explicit precedence the page carrying both facts could render as
    ``age-12d`` and the V7 check would never see the ``stale-source`` it needs.
    """
    root = _make_project(tmp_path)
    derived_at = _days_ago(12)
    _derived_page(
        root, "both.md", derived_at, source_mtime=derived_at + timedelta(days=1)
    )

    states = compute_wiki_staleness(tmp_path / WIKI_ROOT_RELPATH, root)
    assert states["concepts/both.md"] == WIKI_STALE_SOURCE


def test_missing_derived_from_target_is_fail_soft(tmp_path):
    """IC-01: a missing source is ``""`` plus exactly one ``log.debug``.

    The forbidden outcomes are named explicitly because each is a plausible
    wrong answer: a ``SyncError`` would abort a sync over a documentation
    annotation, and ``0``/``age-0d`` would render a fabricated measurement.
    """
    root = _make_project(tmp_path)
    concepts = tmp_path / WIKI_ROOT_RELPATH / "concepts"
    _wiki_page(
        concepts,
        "gone.md",
        {
            "type": WIKI_ARCHITECTURE_TYPE,
            DERIVED_FROM_KEY: "docs/does-not-exist.md",
            DERIVED_AT_KEY: _days_ago(5).isoformat(),
        },
    )

    log = _StubLog()
    states = compute_wiki_staleness(tmp_path / WIKI_ROOT_RELPATH, root, log=log)

    assert states["concepts/gone.md"] == WIKI_FRESH
    assert states["concepts/gone.md"] not in ("0", "age-0d")
    assert len(log.calls) == 1, f"expected exactly one debug call: {log.calls}"
    target, message = log.calls[0]
    assert target == "docs"
    assert "concepts/gone.md" in message
    assert "does-not-exist" in message, "the message must name the missing source"


def test_unusable_derived_at_is_fail_soft_and_never_epoch(tmp_path):
    """An unparsable ``derived-at`` degrades; it must not become ``epoch``.

    Falling back to the epoch would make the page look ~56 years stale and turn
    the resolver into the repo's loudest false alarm.
    """
    root = _make_project(tmp_path)
    source_mtime = _days_ago(5)
    for name, derived_at in (("garbage", "not-a-date"), ("absent", _ABSENT)):
        _derived_page(root, f"{name}.md", derived_at, source_mtime=source_mtime)

    log = _StubLog()
    states = compute_wiki_staleness(tmp_path / WIKI_ROOT_RELPATH, root, log=log)

    for name in ("garbage", "absent"):
        value = states[f"concepts/{name}.md"]
        assert value == WIKI_FRESH, f"{name}: {value!r}"
        assert not value.startswith(WIKI_AGE_PREFIX), f"{name}: fabricated age"
    assert len(log.calls) == 2, f"one debug per unusable page: {log.calls}"
    assert all(DERIVED_AT_KEY in message for _t, message in log.calls)


def test_missing_wiki_root_is_fail_soft_and_yields_no_pages(tmp_path):
    """A missing ``wiki_root`` is an empty map plus one debug, never a raise."""
    log = _StubLog()
    states = compute_wiki_staleness(tmp_path / "no-such-wiki", tmp_path, log=log)
    assert states == {}
    assert len(log.calls) == 1
    assert log.calls[0][0] == "docs"


def test_resolver_writes_nothing_under_either_root(tmp_path):
    """The resolver is a pure reader — including under ``knowledge/``.

    ``knowledge/sources/`` is immutable raw data (NG-2); nothing in this module
    may write there. The digest is taken over both roots before and after.
    """

    def _digest(*roots: Path) -> str:
        acc = hashlib.sha256()
        for root in roots:
            for path in sorted(root.rglob("*")) if root.exists() else []:
                stat = path.lstat()
                acc.update(str(path).encode("utf-8"))
                acc.update(str(stat.st_size).encode("utf-8"))
                acc.update(str(stat.st_mtime_ns).encode("utf-8"))
        return acc.hexdigest()

    root = _make_project(tmp_path)
    (root / "knowledge" / "sources").mkdir(parents=True, exist_ok=True)
    (root / "knowledge" / "sources" / "immutable.md").write_text(
        "# raw\n", encoding="utf-8"
    )
    concepts = root / WIKI_ROOT_RELPATH / "concepts"
    _wiki_page(concepts, "arch.md", {"type": WIKI_ARCHITECTURE_TYPE})

    wiki = root / WIKI_ROOT_RELPATH
    before = _digest(wiki, root / "knowledge" / "sources")
    compute_wiki_staleness(wiki, root)
    assert _digest(wiki, root / "knowledge" / "sources") == before


def test_resolver_is_not_registered_as_a_fact_computer():
    """W1-4 scope: no IC-02 fact consumes the resolver yet (that is W2-3).

    Registering it would claim a ``DOCS_*`` placeholder the IC-02 table does not
    enumerate and would put a per-wiki-page value into the fact dict, where
    every value is a single scalar.
    """
    assert compute_wiki_staleness not in doc_facts._FACT_COMPUTERS.values()
    assert stale_upstream_status not in doc_facts._FACT_COMPUTERS.values()
    assert not any("wiki" in name.lower() for name in FACT_KEYS), (
        "an IC-02 placeholder would need a spec row; W1-4 adds none"
    )
    assert set(FACT_KEYS) == IC02_KEYS, "the fact key set must not have grown"


def test_resolver_has_no_module_global_memo():
    """The per-call memo contract: no cache survives a call.

    ``FactContext.sources`` is per call for the same reason — a
    process-lifetime cache would hand a second call data from a checkout that no
    longer exists on disk. The resolver must not reintroduce that through a
    module-level dict.
    """
    globals_ = vars(doc_facts)
    suspicious = [
        name
        for name, value in globals_.items()
        if name.startswith("_") and not name.startswith("__")
        and isinstance(value, dict)
        and value
        and name
        not in {
            "_FACT_COMPUTERS",
            "VOLATILE_FACTS",
            "FACT_KEYS",
            "PENDING_FACTS",
            "BLOCK_FACT_KEYS",
            "SCALAR_FACT_KEYS",
            "_STABLE_SCALAR_FACT_KEYS",
            "LANGFASSUNG_RELPATHS",
        }
    ]
    assert not suspicious, f"possible module-global cache: {suspicious}"


def test_resolver_observes_a_change_between_two_calls(tmp_path):
    """Two calls, an annotated page in between — the second must see it.

    The negative control for the memo contract: a module-global cache would
    answer ``missing-derived-from`` here forever, and the suite would stay
    green because the first call is the one being asserted.
    """
    root = _make_project(tmp_path)
    concepts = root / WIKI_ROOT_RELPATH / "concepts"
    page = _wiki_page(concepts, "arch.md", {"type": WIKI_ARCHITECTURE_TYPE})

    first = compute_wiki_staleness(root / WIKI_ROOT_RELPATH, root)
    assert first["concepts/arch.md"] == WIKI_MISSING_DERIVED_FROM

    derived_at = _days_ago(4)
    _derived_page(
        root, "arch.md", derived_at, source_mtime=derived_at - timedelta(days=1)
    )

    second = compute_wiki_staleness(root / WIKI_ROOT_RELPATH, root)
    assert second["concepts/arch.md"] == f"{WIKI_AGE_PREFIX}4d", (
        "a module-global cache leaked across calls — the annotation was ignored"
    )
    assert first["concepts/arch.md"] == WIKI_MISSING_DERIVED_FROM, (
        "the earlier result was mutated"
    )
    assert page.exists()


def test_a_failing_source_is_reported_on_every_call(tmp_path):
    """A failure is never cached: the second call logs again.

    Memoising the *degraded* answer would make the problem invisible after the
    first run — a sync would silently stop reporting a missing source.
    """
    root = _make_project(tmp_path)
    concepts = root / WIKI_ROOT_RELPATH / "concepts"
    _wiki_page(
        concepts,
        "gone.md",
        {
            "type": WIKI_ARCHITECTURE_TYPE,
            DERIVED_FROM_KEY: "docs/does-not-exist.md",
            DERIVED_AT_KEY: _days_ago(2).isoformat(),
        },
    )

    for _ in range(2):
        log = _StubLog()
        states = compute_wiki_staleness(root / WIKI_ROOT_RELPATH, root, log=log)
        assert states["concepts/gone.md"] == WIKI_FRESH
        assert len(log.calls) == 1, f"a cached failure went quiet: {log.calls}"


def test_wiki_relative_derived_from_reaches_the_same_source(tmp_path):
    """Both ``derived-from`` spellings resolve to the same file.

    The migrated pages carry wiki-relative values (``resource: "../../sources/…"``
    — from ``knowledge/wiki/concepts/`` that is ``knowledge/sources/…``). The
    resolver rewrites such a value against the **project root**, so both
    spellings reach the same file. If only the project-relative spelling worked,
    the annotated pages would report a missing source and V7 would alarm on
    pages that are perfectly annotated.
    """
    root = _make_project(tmp_path)
    derived_at = _days_ago(6)
    # ``concepts/`` is three levels below the project root, so the wiki-relative
    # spelling of a project-relative path needs three ``..`` — exactly the shape
    # the real ``resource:`` values have.
    for name, value in (
        ("project-relative.md", "docs/source.md"),
        ("wiki-relative.md", "../../../docs/source.md"),
    ):
        _derived_page(
            root, name, derived_at,
            source_mtime=derived_at - timedelta(days=1), derived_from=value,
        )

    states = compute_wiki_staleness(root / WIKI_ROOT_RELPATH, root)
    assert states["concepts/project-relative.md"] == f"{WIKI_AGE_PREFIX}6d"
    assert states["concepts/wiki-relative.md"] == states[
        "concepts/project-relative.md"
    ], "the two spellings must not disagree"


def test_wiki_relative_derived_from_matches_the_real_resource_convention(tmp_path):
    """The ``knowledge/sources/`` spelling the real pages actually use.

    ``knowledge/wiki/concepts/architecture.md`` carries
    ``resource: "../../sources/ARCHITECTURE.full.md"`` — two levels up from
    ``concepts/`` lands in ``knowledge/``, i.e. **inside** the project root but
    not at its top. A resolver that resolved such a value against the project
    root would look for ``<root>/sources/…``, miss, and report the page as
    having a missing source.
    """
    root = _make_project(tmp_path)
    concepts = root / WIKI_ROOT_RELPATH / "concepts"
    raw = root / "knowledge" / "sources" / "ARCHITECTURE.full.md"
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_text(f"# raw\n\n{STALE_DECLARATION}\n", encoding="utf-8")

    derived_at = _days_ago(8)
    _set_mtime(raw, derived_at - timedelta(days=1))
    _wiki_page(
        concepts,
        "architecture.md",
        {
            "type": WIKI_ARCHITECTURE_TYPE,
            "resource": "../../sources/ARCHITECTURE.full.md",
            DERIVED_FROM_KEY: "../../sources/ARCHITECTURE.full.md",
            DERIVED_AT_KEY: derived_at.isoformat(),
        },
    )

    log = _StubLog()
    states = compute_wiki_staleness(root / WIKI_ROOT_RELPATH, root, log=log)
    assert states["concepts/architecture.md"] == f"{WIKI_AGE_PREFIX}8d", (
        f"the real ``resource:`` shape must resolve; debug said {log.calls}"
    )
    assert log.calls == []


def test_derived_from_pointing_outside_the_project_is_fail_soft(tmp_path):
    """A ``derived-from`` that escapes the project root is unusable, not fresh.

    ``..`` traversal out of the repository has no legitimate reading here: the
    staleness question is "is the source this page was derived from newer than
    the derivation", and a file outside the project cannot answer it for this
    project. Resolving it anyway would let an annotation point at ``/etc`` and
    produce a confident verdict from it.
    """
    root = _make_project(tmp_path)
    _write_source(tmp_path.parent, "outside.md", datetime.now(timezone.utc))

    concepts = root / WIKI_ROOT_RELPATH / "concepts"
    # Four ``..`` from ``concepts/`` leaves the project root entirely.
    _wiki_page(
        concepts,
        "escape.md",
        {
            "type": WIKI_ARCHITECTURE_TYPE,
            DERIVED_FROM_KEY: "../../../../outside.md",
            DERIVED_AT_KEY: _days_ago(1).isoformat(),
        },
    )

    log = _StubLog()
    states = compute_wiki_staleness(root / WIKI_ROOT_RELPATH, root, log=log)
    value = states["concepts/escape.md"]
    assert value in (WIKI_FRESH, WIKI_MISSING_DERIVED_FROM), value
    assert not value.startswith(WIKI_AGE_PREFIX)


def test_symlink_escaping_the_project_root_is_fail_soft(tmp_path):
    """F6: a symlink out of the project root must never be *read*.

    ``_resolve_derived_source`` calls ``.resolve()`` on **both** sides before
    ``relative_to(root.resolve())``. Those two ``.resolve()`` calls are the only
    thing standing between a ``derived-from`` annotation and the whole
    filesystem, and nothing pinned them: a refactor that "simplified" the
    resolution to a plain ``root / relpath`` join would keep every other case in
    this file green and start reporting a confident ``stale-source`` verdict
    derived from a file outside the repository.

    The negative control is built into the fixture. The escape target is stamped
    with **now**, while ``derived-at`` is a day ago — so a resolver that followed
    the link would answer ``stale-source``, and a resolver that reached it by
    any other route would answer ``age-<n>d``. Only the containment check answers
    ``""``. A ``..`` escape is already covered above; this is the spelling that
    *looks* entirely innocent, which is exactly why it needed its own case.
    """
    project = tmp_path / "project"
    root = _make_project(project)

    outside = tmp_path / "outside"
    _write_source(outside, "source.md", datetime.now(timezone.utc))
    (project / SOURCE_RELPATH).symlink_to(outside / "source.md")
    assert (project / SOURCE_RELPATH).is_symlink(), (
        "premise: the fixture target must be reached *through* a symlink"
    )

    _wiki_page(
        root / WIKI_ROOT_RELPATH / "concepts",
        "linked.md",
        {
            "type": WIKI_ARCHITECTURE_TYPE,
            DERIVED_FROM_KEY: SOURCE_RELPATH,
            DERIVED_AT_KEY: _days_ago(1).isoformat(),
        },
    )

    log = _StubLog()
    states = compute_wiki_staleness(root / WIKI_ROOT_RELPATH, root, log=log)

    value = states["concepts/linked.md"]
    assert value == WIKI_FRESH, (
        f"the symlink was followed instead of rejected: {value!r} "
        f"(debug: {log.calls})"
    )
    assert not value.startswith(WIKI_AGE_PREFIX), "no measurement from outside"
    assert len(log.calls) == 1, f"expected exactly one debug call: {log.calls}"
    target, message = log.calls[0]
    assert target == "docs"
    assert "concepts/linked.md" in message
    assert SOURCE_RELPATH in message, "the message must name the rejected target"


# --------------------------------------------------------------------------
# IC-03 — machine-side extraction of ``status:stale-upstream``
# --------------------------------------------------------------------------


def test_stale_upstream_is_extracted_from_the_langfassung(tmp_path):
    """The marker is **read**, not declared: only the Langfassung carries it.

    The wiki page's hand-maintained ``status:stale-upstream`` tag is the thing
    this extraction replaces. The fixture therefore puts the self-declaration in
    the Langfassung and *nowhere else* — no tag, no marker in the stub — so an
    implementation that read the wiki frontmatter or the stub could not answer.
    """
    root = _make_project(tmp_path, langfassung_body=STALE_DECLARATION)
    assert stale_upstream_status(root) == STALE_UPSTREAM_STATUS


def test_stale_upstream_is_fresh_without_the_self_declaration(tmp_path):
    """A Langfassung that does not declare itself stale is fresh."""
    root = _make_project(tmp_path, langfassung_body=FRESH_DECLARATION)
    assert stale_upstream_status(root) == WIKI_FRESH


def test_stale_upstream_never_reads_the_architecture_stub(tmp_path):
    """Spec A12 / M-5: the stub is not a source, even when it holds the line.

    The stub is what the pre-A12 design read. If it were still accepted, W4
    (M-2) would strip its prose and the extraction would silently answer
    ``""`` — the marker would disappear from the repo without any error, and V7
    would lose its carrier. Pinning the rejection here is what keeps W4 from
    reintroducing the circularity.
    """
    root = _make_project(tmp_path, langfassung_body=None)
    stub = root / ARCHITECTURE_STUB_RELPATH
    stub.write_text(f"# stub\n\n{STALE_DECLARATION}\n", encoding="utf-8")

    assert ARCHITECTURE_STUB_RELPATH not in LANGFASSUNG_RELPATHS
    assert doc_facts._langfassung_path(root) is None
    assert stale_upstream_status(root) == WIKI_FRESH, (
        "the stub must not answer the extraction — it is a pointer, not a source"
    )


def test_stale_upstream_prefers_the_post_w4_location(tmp_path):
    """After W4 the declaration lives in ``docs/architecture/`` — and wins.

    Both spellings exist during the wave: the new location and the legacy one
    still on disk. The post-W4 path must take precedence, otherwise a stale
    copy left behind at the old path would keep answering after the migration.
    """
    root = _make_project(tmp_path, langfassung_body=FRESH_DECLARATION)
    legacy = root / LEGACY_LANGFASSUNG_RELPATH
    legacy.write_text(f"# legacy\n\n{STALE_DECLARATION}\n", encoding="utf-8")

    assert doc_facts._langfassung_path(root) == root / LANGFASSUNG_RELPATH
    assert stale_upstream_status(root) == WIKI_FRESH


def test_stale_upstream_accepts_the_legacy_location_before_w4(tmp_path):
    """Between W1-4 and W4-1 the Langfassung still sits at its old path.

    Without the legacy spelling the marker would read ``""`` for the whole
    window — a silent regression that only shows up as "the tag disappeared".
    """
    root = _make_project(tmp_path, langfassung_body=None)
    legacy = root / LEGACY_LANGFASSUNG_RELPATH
    legacy.write_text(f"# legacy\n\n{STALE_DECLARATION}\n", encoding="utf-8")

    assert doc_facts._langfassung_path(root) == legacy
    assert stale_upstream_status(root) == STALE_UPSTREAM_STATUS


def test_stale_upstream_missing_langfassung_is_fail_soft(tmp_path):
    """No Langfassung at all: ``""`` plus one debug, never a raise."""
    log = _StubLog()
    assert stale_upstream_status(tmp_path, log=log) == WIKI_FRESH
    assert len(log.calls) == 1
    target, message = log.calls[0]
    assert target == "docs"
    assert LANGFASSUNG_RELPATH in message, "the message must name what was looked for"


def test_stale_upstream_matches_the_declaration_the_real_wiki_index_cites():
    """The real bundle: the machine extraction agrees with the hand-written tag.

    ``knowledge/wiki/index.md:24`` and the wiki frontmatter carry
    ``status:stale-upstream`` by hand today. Until W5 removes those hand-written
    tags, the extraction must **agree** with them — a disagreement means the
    hand tag or the extraction is wrong, and both are load-bearing for AC-29(c).

    The oracle reads the hand-written tag from the files themselves; the literal
    ``status:stale-upstream`` string is the tag's *name* (a contract value from
    IC-03), not an expected count.
    """
    hand_tagged: set[str] = set()
    for page in sorted((REPO_ROOT / WIKI_ROOT_RELPATH).rglob("*.md")):
        frontmatter = yaml.safe_load(
            _frontmatter_segment(page.read_text(encoding="utf-8")) or "{}"
        )
        for tag in (frontmatter or {}).get("tags") or []:
            if isinstance(tag, str) and tag.startswith("status:"):
                hand_tagged.add(tag)

    assert hand_tagged, "premise: the real wiki still carries hand-written status tags"
    extracted = stale_upstream_status(REPO_ROOT)
    assert extracted in hand_tagged, (
        f"machine extraction {extracted!r} is not among the hand-written tags "
        f"{sorted(hand_tagged)}"
    )


def test_real_wiki_architecture_page_is_reported_missing_derived_from():
    """AC-10's live instance: the real bundle has unannotated Architecture pages.

    This is the observation W2-3 turns into a V7 finding. Asserting it here
    keeps the resolver honest against the real tree (the synthetic fixtures
    prove the logic; this proves the premise that there is something to find).
    """
    states = compute_wiki_staleness(REPO_ROOT / WIKI_ROOT_RELPATH, REPO_ROOT)
    unannotated = {
        relpage for relpage, value in states.items() if value == WIKI_MISSING_DERIVED_FROM
    }
    assert unannotated, (
        "premise broken: no Architecture page lacks derived-from — W5 has "
        "annotated the whole bundle, so the V7 fixture must be re-derived"
    )
    for relpage in unannotated:
        page = REPO_ROOT / WIKI_ROOT_RELPATH / relpage
        frontmatter = yaml.safe_load(
            _frontmatter_segment(page.read_text(encoding="utf-8")) or "{}"
        ) or {}
        assert frontmatter.get("type") == WIKI_ARCHITECTURE_TYPE, relpage
        assert not frontmatter.get(DERIVED_FROM_KEY), relpage


# ---------------------------------------------------------------------------
# W2-1 — V1 ``check_no_manual_counts`` (AC-07, AC-08; spec IC-05 §5.1.1)
# ---------------------------------------------------------------------------
#
# **Fixture reconciliation (plan defect, reported not papered over).** The
# plan's W2-1 acceptance describes one fixture that holds the positive block
# *plus* one case per suppression *plus* the counter-probe, while the same
# task's verification demands ``wc -l < tests/fixtures/docs_v1_fixtures.md``
# → **4**. Both cannot hold in one file. The machine-checkable gate wins: the
# committed fixture is **exactly** the four quoted lines and nothing else, and
# the three suppression cases plus the counter-probe are built as tmp trees
# inside the tests below. The reconciliation is deliberately *not* written into
# the fixture as a comment, because a fifth line would break the very gate the
# fixture exists to satisfy — this comment is the fixture's documentation.
#
# **No expected fact values here (Spec NEW-8).** The four fixture lines are
# *input* text quoted verbatim from the spec (§5.1.1, itself quoted 1:1 from
# ``README.md``) and are contract values, not computed numbers. The numbers
# this test asserts are structural: how many findings a four-line document
# produces, and which line each belongs to. Expected *facts* live in
# ``config/doc-facts-expected.yaml`` (IC-23).
#
# **Line 4 and the spec's own regex.** §5.1.1 writes V1b as
# ``\b\d+\.\d+\.\d+...\b``. That pattern cannot match its own positive fixture
# line ``VERSION   # Current version (v1.0.0)`` — a word character sits in
# front of the leading digit, so ``\b`` fails. The implementation uses a
# lookbehind that tolerates the ``v`` prefix instead; without that the mandated
# line 4 finding is unreachable. See ``_V1_SEMVER_RE``.

V1_FIXTURE_RELPATH = "tests/fixtures/docs_v1_fixtures.md"
V1_FIXTURE = REPO_ROOT / V1_FIXTURE_RELPATH

#: The four lines §5.1.1 mandates, in order, byte for byte.
V1_QUOTED_LINES = (
    "## Agent Roster — 74 Generic Agents",
    "## Hooks (7 hooks, propagated to all providers)",
    (
        "  ai-providers.yaml          # 6 provider configs (Claude, Gemini, "
        "Opencode, Continue, Copilot, Mammouth)"
    ),
    "VERSION                      # Current version (v1.0.0)",
)

#: §5.1.1 negative fixture, one case per suppression, plus the counter-probe.
V1_REGION_CASE = (
    "<!-- agent-meta:docs-begin facts -->\n"
    "| Agents | 74 |\n"
    "<!-- agent-meta:docs-end facts -->\n"
)
V1_EXEMPT_CASE = (
    "## Agent Roster — 74 Generic Agents "
    "<!-- agent-meta:docs-exempt: Beispiel -->\n"
)
V1_FENCE_CASE = "```text\n## Hooks (7 hooks)\n```\n"
V1_COUNTER_PROBE = "| Agents | 74 |\n"

#: IC-05 sites inside the ``README.md`` directory-structure fence, which opens
#: untyped at ``:680`` and closes at ``:737``: ``(line, branch, needle)``.
#: The line numbers are fixed by the plan (W2-1 step 4, K16) and the ``needle``
#: is the premise guard — if the document ever shifts, the test has to say so
#: instead of failing with an unexplained "invisible to V1".
V1_README_DIRECTORY_SITES = (
    (688, "V1a", "# 6 DoD presets"),
    (690, "V1a", "# 6 provider configs"),
    (696, "V1a", "# 5 hook scripts"),
    (734, "V1b", "# Current version (v1.0.0)"),
)


def _v1_findings(monkeypatch, root: Path, relpaths: tuple[str, ...],
                 config: dict | None = None) -> list:
    """Run V1 over exactly ``relpaths`` — the scan list is a module constant so
    the test can point the check at a fixture without a repo-root heuristic."""
    monkeypatch.setattr(docs_lib, "V1_SCAN_RELPATHS", relpaths)
    return docs_lib.check_no_manual_counts(root, config)


def _v1_tree(tmp_path: Path, relpath: str, body: str) -> Path:
    path = tmp_path / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return tmp_path


def test_v1_fixture_is_exactly_the_four_quoted_lines():
    """The plan's hard gate: four lines, verbatim, nothing else in the file.

    ``wc -l`` counts newlines, so the file has to end in one — asserted here
    rather than left to the shell, because a fixture without a trailing
    newline would report 3 and every other assertion in this section would
    still pass.
    """
    text = V1_FIXTURE.read_text(encoding="utf-8")
    assert text.endswith("\n"), "the fixture must be newline-terminated for wc -l"
    assert text.count("\n") == len(V1_QUOTED_LINES)
    assert text.splitlines() == list(V1_QUOTED_LINES)


def test_v1_positive_fixture_yields_exactly_four_findings(monkeypatch):
    """AC-07: four findings, WARNING, correct check, line and branch each.

    Lines 1-3 are the counted-thing branch, line 4 the version branch — the
    heading case the rev-0.1 regex never covered is line 1.
    """
    findings = _v1_findings(monkeypatch, REPO_ROOT, (V1_FIXTURE_RELPATH,))

    assert len(findings) == 4
    assert [f.line for f in findings] == [1, 2, 3, 4]
    assert [f.branch for f in findings] == ["V1a", "V1a", "V1a", "V1b"]
    assert {f.severity for f in findings} == {docs_lib.Severity.WARNING}
    assert {f.check for f in findings} == {"docs.no_manual_counts"}
    assert {f.file for f in findings} == {V1_FIXTURE_RELPATH}
    for finding in findings:
        assert str(finding.line) in finding.message, (
            "the console report has no line column — the number belongs in the "
            "message until Finding grows a line field"
        )


def test_v1_reports_the_number_and_the_noun(monkeypatch):
    """§5.1.1: the finding names the number token and the noun, not the value.

    A V1 finding is about the *absence of a marker region*, so the message has
    to point at the two tokens that made it fire — otherwise the author cannot
    tell a count from a line-number reference without re-reading the regex.
    """
    findings = _v1_findings(monkeypatch, REPO_ROOT, (V1_FIXTURE_RELPATH,))
    counted = [f for f in findings if f.branch == "V1a"]

    assert len(counted) == 3
    for finding, line in zip(counted, V1_QUOTED_LINES[:3], strict=True):
        number = line.split("—")[-1].split("#")[-1].split()[0]
        assert f"{number!r}" in finding.message, finding.message
    assert "v1.0.0" in findings[-1].message


@pytest.mark.parametrize(
    ("body", "why"),
    [
        (V1_REGION_CASE, "marker region"),
        (V1_EXEMPT_CASE, "docs-exempt marker"),
        (V1_FENCE_CASE, "fenced code block"),
    ],
    ids=["marker-region", "docs-exempt", "fenced-code"],
)
def test_v1_suppression_cases_produce_no_finding(monkeypatch, tmp_path, body, why):
    """§5.1.1 suppression rules 1-3, one case each, zero findings.

    Each body carries a *different* counted number, so a suppression that
    works by accident — e.g. by swallowing the whole file — cannot pass all
    three. The bodies are written to ``README.md`` so the check needs no scan
    list override.
    """
    root = _v1_tree(tmp_path, "README.md", body)
    assert _v1_findings(monkeypatch, root, ("README.md",)) == [], why


def test_v1_generated_file_is_suppressed(monkeypatch, tmp_path):
    """§5.1.1 suppression rule 4: a generated file cannot hold a manual count.

    ``docs/INDEX.md`` is written by the generator, so every number in it is
    computed; V1 reporting there would be a permanent false positive. The
    control on the same tree is what makes this a test of the *file* rule and
    not of the line rules: byte-identical content in ``README.md`` must fire.
    """
    generated_body = V1_COUNTER_PROBE
    root = _v1_tree(tmp_path, "docs/INDEX.md", generated_body)
    _v1_tree(tmp_path, "README.md", generated_body)

    assert _v1_findings(monkeypatch, root, ("docs/INDEX.md",)) == []
    control = _v1_findings(monkeypatch, root, ("README.md",))
    assert len(control) == 1, "the control must fire, else the test proves nothing"


def test_v1_counter_probe_outside_every_region_yields_exactly_one(monkeypatch, tmp_path):
    """§5.1.1: ``| Agents | 74 |`` outside every region is exactly one finding.

    The noun stands *before* the number here, which is the half of the token
    gap rule the three positive lines do not exercise.
    """
    root = _v1_tree(tmp_path, "README.md", V1_COUNTER_PROBE)
    findings = _v1_findings(monkeypatch, root, ("README.md",))

    assert len(findings) == 1
    assert findings[0].branch == "V1a"
    assert findings[0].line == 1
    assert findings[0].file == "README.md"


def test_v1_fence_suppression_covers_typed_fences_only(monkeypatch, tmp_path):
    """Rule 3 after the K16 narrowing: typed fence suppresses, untyped one does not.

    Same payload, only the info string differs — that *is* the mechanism, so
    the pair pins it from both sides and neither case can pass by accident. The
    third tree is the state-machine guard: the untyped block is skipped, yet
    the typed fence behind it must still be tracked, or the closing delimiter
    of the untyped block would be read as an opener and rule 3 would lose a
    whole region instead of one.
    """
    payload = "## Hooks (7 hooks, propagated to all providers)\n"
    typed = _v1_tree(tmp_path / "typed", "README.md",
                     "```text\n" + payload + "```\n")
    untyped = _v1_tree(tmp_path / "untyped", "README.md",
                       "```\n" + payload + "```\n")
    chained = _v1_tree(tmp_path / "chained", "README.md",
                       "```\n| Agents | 74 |\n```\n```text\n" + payload + "```\n")

    assert _v1_findings(monkeypatch, typed, ("README.md",)) == [], (
        "AC-08: a fence with a language stays suppressed"
    )

    untyped_findings = _v1_findings(monkeypatch, untyped, ("README.md",))
    assert [f.branch for f in untyped_findings] == ["V1a"]
    assert untyped_findings[0].line == 2

    chained_findings = _v1_findings(monkeypatch, chained, ("README.md",))
    assert [f.line for f in chained_findings] == [2], (
        "the untyped block is visible and the typed block behind it is still "
        f"suppressed, got {[(f.line, f.branch) for f in chained_findings]}"
    )


def test_v1_sees_the_readme_directory_structure_facts(monkeypatch):
    """K16 / B-4 / E-14: negative proof that IC-05's sites are visible again.

    Rule 3 used to suppress *every* fenced line, which hid F2, F3-Site-2 and F4
    inside the ``README.md`` directory-structure fence — rule 3 and IC-05 were
    mutually exclusive. Reverting the narrowing makes this test fail, which is
    the whole point of a negative proof.

    It runs against the real, unmarked document instead of a synthetic tree, so
    the premise guards carry the weight: the fence at ``:680`` must still open
    untyped, each site line must still hold its quoted fact, and no site line
    may carry a ``agent-meta:docs-*`` marker — otherwise the sites would be
    hidden by rule 1 or 2 and the test would pass for the wrong reason.
    """
    findings = _v1_findings(monkeypatch, REPO_ROOT, ("README.md",))
    lines = (REPO_ROOT / "README.md").read_text(encoding="utf-8").splitlines()
    by_line: dict[int, list] = {}
    for finding in findings:
        by_line.setdefault(finding.line, []).append(finding)

    assert lines[679].strip() == "```", (
        "premise: the untyped directory-structure fence no longer opens at "
        f"README.md:680, found {lines[679]!r}"
    )

    for lineno, branch, needle in V1_README_DIRECTORY_SITES:
        line = lines[lineno - 1]
        assert needle in line, (
            f"premise: README.md:{lineno} no longer holds {needle!r}, found {line!r}"
        )
        assert "agent-meta:docs-" not in line, (
            f"premise: README.md:{lineno} is marked — the IC-05 sites must stay "
            "unmarked for this proof to be about suppression rule 3"
        )
        site = by_line.get(lineno, [])
        assert any(f.branch == branch for f in site), (
            f"README.md:{lineno} is invisible to V1 (expected branch {branch}, "
            f"got {[(f.branch, f.message) for f in site]}) — suppression rule 3 "
            "covers the site again"
        )
        for finding in site:
            assert finding.check == "docs.no_manual_counts"
            assert finding.severity == docs_lib.Severity.WARNING


def test_v1_branches_are_disjoint(monkeypatch, tmp_path):
    """V1a and V1b can never claim the same characters.

    The property is structural — ``v1a_count_spans`` drops every bare integer
    that lies inside a dotted numeric token, and every V1b span *is* a dotted
    numeric token — so it is checked as a span overlap over the fixture and
    over every real document the check scans, not on four hand-picked lines.
    """
    root = _v1_tree(tmp_path, "README.md", V1_QUOTED_LINES[-1] + "\n")
    assert _v1_findings(monkeypatch, root, ("README.md",))[0].branch == "V1b", (
        "a version line must not also produce a V1a finding"
    )

    scanned = 0
    for relpath in (*docs_lib.V1_SCAN_RELPATHS, V1_FIXTURE_RELPATH):
        path = REPO_ROOT / relpath
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            scanned += 1
            for a_start, a_end, _a in docs_lib.v1a_count_spans(line):
                for b_start, b_end, _b in docs_lib.v1b_version_spans(line):
                    assert not (a_start < b_end and b_start < a_end), (
                        f"{relpath}: {line!r} — V1a and V1b overlap"
                    )
    assert scanned > 0, "premise: nothing was scanned"


def test_v1_severity_follows_checks_strict(monkeypatch, tmp_path):
    """AC-08: WARNING by default, ERROR once ``checks.strict`` is true.

    Absence and an explicit ``false`` must stay observationally identical
    (IC-22, the ``knowledge.py:127`` precedence) — a check that invented a
    third default would be the one place where that promise breaks.
    """
    root = _v1_tree(tmp_path, "README.md", V1_QUOTED_LINES[0] + "\n")
    strict = {"docs-consolidation": {"enabled": True, "checks": {"strict": True}}}

    for config in (None, {}, {"docs-consolidation": {}},
                   {"docs-consolidation": {"checks": {"strict": False}}}):
        findings = _v1_findings(monkeypatch, root, ("README.md",), config)
        assert [f.severity for f in findings] == [docs_lib.Severity.WARNING], config

    findings = _v1_findings(monkeypatch, root, ("README.md",), strict)
    assert [f.severity for f in findings] == [docs_lib.Severity.ERROR]


def test_v1_strict_leaves_the_finding_count_untouched(monkeypatch):
    """The promotion is a severity change, not a detection change."""
    strict = {"docs-consolidation": {"checks": {"strict": True}}}
    warned = _v1_findings(monkeypatch, REPO_ROOT, (V1_FIXTURE_RELPATH,))
    errored = _v1_findings(monkeypatch, REPO_ROOT, (V1_FIXTURE_RELPATH,), strict)

    assert [(f.line, f.branch) for f in errored] == [
        (f.line, f.branch) for f in warned
    ]


def test_v1_is_not_wired_into_the_runner_yet():
    """AC-38: V1 is a no-op in every scenario until W2-7 registers it.

    The common gate (``docs-consolidation.enabled``) and the registration in
    ``run_checks()`` are W2-7's task. Until then the only way V1 can affect a
    run is a direct call, which is what this file does — and that is exactly
    why scenarios 50-56 cannot regress from W2-1.
    """
    runner = (REPO_ROOT / "scripts" / "consistency-check.py").read_text(encoding="utf-8")
    assert "check_no_manual_counts" not in runner, (
        "W2-1 must not register the check — registration is W2-7"
    )
    scenario_configs = sorted(
        (REPO_ROOT / "tests" / "scenarios" / "configs").glob(
            "5[0-6]-*.project.yaml"
        )
    )
    assert scenario_configs, "premise: the scenario configs are gone"
    for path in scenario_configs:
        assert "docs-consolidation" not in path.read_text(encoding="utf-8"), path


def test_existing_docs_checks_keep_signature_and_severity(tmp_path):
    """W2-7's contract: the three pre-existing checks are untouched.

    IC-05 requires them to keep *signature and severity*; a rename, a new
    required parameter or a demoted severity would silently change what
    ``run_checks()`` collects. Both halves are pinned — the parameter list by
    introspection, the severity by a tree that makes each one fire.
    """
    import inspect

    for func in (docs_lib.check_sync_cli_docs, docs_lib.check_ui_help_mappings,
                 docs_lib.check_readme_docs_index):
        assert list(inspect.signature(func).parameters) == ["root"], func.__name__

    # Three separate roots: each check needs two files, and a shared root
    # would let one check's fixture satisfy another's precondition.
    sync_root = _v1_tree(tmp_path / "cli", "scripts/sync.py", (
        'parser.add_argument("--validate", action="store_true")\n'
    ))
    _v1_tree(sync_root, "docs/api/cli-reference.md", "# CLI reference\n")
    cli = docs_lib.check_sync_cli_docs(sync_root)
    assert [(f.check, f.severity) for f in cli] == [
        ("docs.cli_reference", docs_lib.Severity.ERROR)
    ], cli

    ui_root = _v1_tree(tmp_path / "ui", "docs/ui/admin-ui.html", (
        "const routeMap = {\n"
        '  "/a": "admin-ui-a",\n'
        "};\n"
    ))
    _v1_tree(ui_root, "docs/api/admin-ui-reference.md", "<!-- help-id: other -->\n")
    ui = docs_lib.check_ui_help_mappings(ui_root)
    assert [(f.check, f.severity) for f in ui] == [
        ("docs.ui_help_mappings", docs_lib.Severity.ERROR)
    ], ui

    index_root = _v1_tree(tmp_path / "index", "docs/api/orphan.md", "# orphan\n")
    _v1_tree(index_root, "README.md", "# readme\n")
    index = docs_lib.check_readme_docs_index(index_root)
    assert [(f.check, f.severity) for f in index] == [
        ("docs.readme_index", docs_lib.Severity.ERROR)
    ], index
