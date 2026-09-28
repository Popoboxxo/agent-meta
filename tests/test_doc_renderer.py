"""AC-14/AC-15/AC-16/AC-27 (IC-07, IC-08) — the ``docs-*`` marker API.

The unit under test is the *marker contract*, not a rendered document: this plan
task (W1-7) owns ``DOCS_BLOCK_RE``, ``render_doc_fact_block()`` and
``apply_fact_blocks()``, while W3 wires them into the sync path. So the tests
here are written against hand-written marker text, and they pin the three
properties that are hard to restore once a file has been written by them:

* **AC-14** — a single region's body is replaced, its two markers stay
  byte-identical.
* **AC-15** — an unbalanced region is a **byte-identical no-op** with **exactly
  one** warning. Both halves are pinned, because the byte-identity half is the
  one that quietly regresses first: a partial rewrite of a tracked, hand-maintained
  file cannot be undone by the next run.
* **AC-16** — a duplicate region updates the **first** pair only (the ``count=1``
  discipline of ``context.py:42-50``), with a warning naming the region.

**AC-27 (order independence) is a determinism guard, not a style rule.** The
rendered bytes must be a function of ``(region, facts[key])`` alone; if a future
edit ever iterates the fact dict, the output would still *look* right on one
machine and produce an unexplained diff on another. The test renders with several
distinct insertion orders and compares bytes, and pins that the six regions map to
six *distinct* fact keys (a duplicated key would make the order test pass while
two regions rendered the same value).

**IC-08 (namespace) is asserted against the real managed-block regex**, not
against a copy of it: ``DOCS_BLOCK_RE`` must not match a single byte of an
``agent-meta:managed-*`` block, and a file carrying both kinds of markers must
come back with the managed block byte-identical. Importing
``scripts.lib.context._MANAGED_BLOCK_RE`` here is the point — a hand-rolled copy
of that regex would keep passing after the real one changed.

Two further guards belong to this task rather than to W3, because they are
properties of *this module* and W3 will consume it as given: the module is a
**leaf** (no ``scripts.lib`` import at all — it must not import ``config``, or
``config.py`` could not consume it in W3 without a cycle) and it **writes
nothing** (no ``open``, no ``Path.write_*``, no ``os`` — a renderer that touched
the filesystem could not be exercised against a tracked file in a dry run).

**W3-1 re-scopes both guards, and says so explicitly.** The writer entry point
``sync_docs_consolidation`` (IC-13) now lives in ``doc_renderer`` too, so:

* the *rendering* half is still pinned write-free, asserted **per function**
  rather than per module, and
* the writer half may reach the disk only through ``write_checked`` — one
  funnel, so idempotency, the secret scan and ``dry_run`` cannot drift apart,
  and the import set stays ``config``-free for the same reason as before.

The write contract itself (AC-23 dry run, AC-26 no-``docs``-directory, the
``unchanged``-without-``write_checked`` idempotency and the IC-13 ownership
rule) is pinned at the end of this file. The ownership rule is asserted in
**both** directions: a foreign ``docs/INDEX.md`` survives byte-identical, and
an index this generator wrote stays updatable — a fail-closed rule that quietly
froze the index after its first creation would pass the first half and break the
second.
"""

from __future__ import annotations

import ast
import inspect
import json
import os
import re
import sys
from pathlib import Path

import pytest

from scripts.lib import doc_index, doc_renderer, spec_plan_scaffold
from scripts.lib.context import _MANAGED_BLOCK_RE, _has_duplicate_managed_block
from scripts.lib.doc_renderer import (
    ALLOWED_REGIONS,
    DOCS_BLOCK_RE,
    apply_fact_blocks,
    render_doc_fact_block,
)
from scripts.lib.log import SyncLog

_MODULE_PATH = Path(doc_renderer.__file__)

# Region -> fact key, restated here on purpose: the mapping is the public contract
# of IC-08 and a second spelling of it is what makes an accidental remap visible.
_REGION_FACTS = {
    "facts": "DOCS_REPO_FACTS_BLOCK",
    "roster": "DOCS_AGENT_ROSTER_BLOCK",
    "pipelines": "DOCS_PIPELINES_BLOCK",
    "hooks": "DOCS_HOOKS_BLOCK",
    "providers": "DOCS_PROVIDERS_BLOCK",
    "version": "DOCS_VERSION",
}

_FACTS = {
    "DOCS_REPO_FACTS_BLOCK": "| Fact | Value |\n| --- | --- |",
    "DOCS_AGENT_ROSTER_BLOCK": "| Role | Status |",
    "DOCS_PIPELINES_BLOCK": "| Pipeline | Enabled |",
    "DOCS_HOOKS_BLOCK": "| Hook | Path |",
    "DOCS_PROVIDERS_BLOCK": "| Provider | Commands |",
    "DOCS_VERSION": "1.2.0-beta.2",
}


class _RecordingLog:
    """Minimal log double that counts every ``warning`` *call*.

    ``SyncLog`` de-duplicates identical messages, so it cannot prove "exactly one
    warning was emitted" — only that one landed. The call count is the property
    AC-15 asks for, so the count is what is asserted.
    """

    def __init__(self) -> None:
        self.warnings: list[str] = []

    def warning(self, message: str) -> None:
        self.warnings.append(message)


def _region_text(region: str, body: str) -> str:
    return (
        f"<!-- agent-meta:docs-begin {region} -->\n"
        f"{body}\n"
        f"<!-- agent-meta:docs-end {region} -->\n"
    )


def test_apply_fact_block_single_region():
    """AC-14: the body is replaced; both markers stay byte-identical."""
    text = (
        "# Project\n\n"
        "Hand-written prose that must survive.\n\n"
        + _region_text("facts", "stale generated table")
        + "\nHand-written footer.\n"
    )
    log = _RecordingLog()

    result = apply_fact_blocks(text, _FACTS, log)

    # The body is exactly the renderer output (which carries its own leading and
    # trailing newline, so the begin line is not glued to the table row) …
    expected_body = render_doc_fact_block("facts", _FACTS)
    assert _FACTS["DOCS_REPO_FACTS_BLOCK"] in result
    assert "stale generated table" not in result
    assert result == (
        "# Project\n\n"
        "Hand-written prose that must survive.\n\n"
        "<!-- agent-meta:docs-begin facts -->"
        f"{expected_body}"
        "<!-- agent-meta:docs-end facts -->\n"
        "\nHand-written footer.\n"
    )
    # … the marker pair is byte-identical (region name and spacing included) …
    assert "<!-- agent-meta:docs-begin facts -->" in result
    assert "<!-- agent-meta:docs-end facts -->" in result
    # … nothing else moved …
    assert result.startswith("# Project\n\nHand-written prose that must survive.\n")
    assert result.endswith("\nHand-written footer.\n")
    # … and a well-formed file produces no warning at all.
    assert log.warnings == []


def test_unbalanced_marker_is_noop_with_warning():
    """AC-15: byte-identical return plus exactly one warning."""
    text = (
        "# Project\n\n"
        + _region_text("facts", "stale generated table")  # this one IS balanced
        + "\n"
        + "<!-- agent-meta:docs-begin roster -->\n"  # no docs-end follows
        + "half-written prose\n"
    )
    original = str(text)
    log = _RecordingLog()

    result = apply_fact_blocks(text, _FACTS, log)

    # Byte-identity, not just equality of the balanced part.
    assert result == original
    assert result.encode("utf-8") == original.encode("utf-8")
    # The balanced region was NOT rewritten either — all-or-nothing, no half write.
    assert "stale generated table" in result
    # Exactly one warning call, naming the unpaired region on the docs channel.
    assert len(log.warnings) == 1
    assert "unbalanced" in log.warnings[0]
    assert "roster" in log.warnings[0]
    assert log.warnings[0].startswith("docs:")
    # The message must fit the real one-argument SyncLog.warning signature.
    sync_log = SyncLog()
    assert apply_fact_blocks(text, _FACTS, sync_log) == original
    assert len(sync_log.warnings) == 1


def test_multiple_unbalanced_regions_still_emit_one_warning():
    """AC-15, hardened: *one* warning per call, not one per broken region."""
    text = (
        "<!-- agent-meta:docs-begin facts -->\nbody\n"
        "<!-- agent-meta:docs-begin roster -->\nbody\n"
        "<!-- agent-meta:docs-begin hooks -->\nbody\n"
    )
    log = _RecordingLog()

    result = apply_fact_blocks(text, _FACTS, log)

    assert result == text
    assert len(log.warnings) == 1
    assert "facts" in log.warnings[0]


def test_duplicate_region_first_only():
    """AC-16: the first pair is rendered, the duplicate stays byte-identical."""
    first = _region_text("facts", "first body")
    second = _region_text("facts", "second body")
    text = "# Project\n\n" + first + "\n" + second
    log = _RecordingLog()

    result = apply_fact_blocks(text, _FACTS, log)

    head, _, tail = result.partition("<!-- agent-meta:docs-end facts -->\n")
    assert _FACTS["DOCS_REPO_FACTS_BLOCK"] in head
    assert "first body" not in head
    # The duplicate pair is untouched, byte for byte.
    assert tail == "\n" + second
    assert "second body" in result
    # Exactly one warning, naming the duplicate region.
    assert len(log.warnings) == 1
    assert "duplicate" in log.warnings[0]
    assert "facts" in log.warnings[0]


def test_duplicate_and_unbalanced_interaction_still_fails_closed():
    """A duplicate *and* a broken pair must not half-write either of them."""
    text = (
        _region_text("facts", "first body")
        + _region_text("facts", "second body")
        + "<!-- agent-meta:docs-begin version -->\nno end\n"
    )
    log = _RecordingLog()

    result = apply_fact_blocks(text, _FACTS, log)

    assert result == text
    assert len(log.warnings) == 1
    assert "unbalanced" in log.warnings[0]


def test_output_independent_of_dict_order():
    """AC-27: the same facts in any insertion order render identical bytes."""
    readme = "# Project\n\n" + _region_text("facts", "stale") + _region_text("roster", "stale")
    llms_txt = (
        "Agent guide\n\n"
        + _region_text("providers", "stale")
        + _region_text("version", "stale")
    )

    orders = [
        list(_FACTS),
        list(reversed(_FACTS)),
        sorted(_FACTS, key=len, reverse=True),
        sorted(_FACTS),
    ]
    assert len({tuple(order) for order in orders}) == len(orders), "orders must differ"

    for text, present in ((readme, ("facts", "roster")), (llms_txt, ("providers", "version"))):
        outputs = []
        for order in orders:
            facts = {key: _FACTS[key] for key in order}
            outputs.append(apply_fact_blocks(text, facts))
        assert all(output == outputs[0] for output in outputs), "dict order leaked"
        # Re-running with the same facts is a no-op (idempotence of the writer).
        assert apply_fact_blocks(outputs[0], _FACTS) == outputs[0]
        # Exactly the facts of the regions in *this* file were rendered, and no
        # other fact leaked in from the shared dict.
        for region in present:
            assert _FACTS[_REGION_FACTS[region]] in outputs[0]
        for region in set(ALLOWED_REGIONS) - set(present):
            assert _FACTS[_REGION_FACTS[region]] not in outputs[0]

    # Each region renders its own fact — a duplicated key would make the order
    # comparison above pass while two regions showed the same value.
    rendered = {region: render_doc_fact_block(region, _FACTS) for region in ALLOWED_REGIONS}
    assert len(set(rendered.values())) == len(ALLOWED_REGIONS)
    for region, body in rendered.items():
        assert _FACTS[_REGION_FACTS[region]] in body


def test_empty_fact_renders_docs_empty_marker():
    """An uncomputed fact renders the placeholder, not a blank row."""
    # Missing key, empty value and whitespace-only value are the same case.
    for facts in ({}, {key: "" for key in _FACTS}, {key: "\n \n" for key in _FACTS}):
        body = render_doc_fact_block("facts", facts)
        assert body == "\n<!-- agent-meta:docs-empty: DOCS_REPO_FACTS_BLOCK -->\n"

    text = _region_text("pipelines", "stale table")
    result = apply_fact_blocks(text, {"DOCS_PIPELINES_BLOCK": ""})
    assert result == (
        "<!-- agent-meta:docs-begin pipelines -->\n"
        "<!-- agent-meta:docs-empty: DOCS_PIPELINES_BLOCK -->\n"
        "<!-- agent-meta:docs-end pipelines -->\n"
    )
    # No stray blank row between marker and placeholder.
    assert "\n\n" not in result


def test_allowed_regions_exactly_six_and_unknown_rejected():
    """IC-08: the six names are the whole namespace; anything else is refused."""
    assert tuple(_REGION_FACTS) == (
        "facts",
        "roster",
        "pipelines",
        "hooks",
        "providers",
        "version",
    )
    assert ALLOWED_REGIONS == tuple(_REGION_FACTS)
    assert len(set(ALLOWED_REGIONS)) == 6

    # Hard boundary in the renderer …
    for unknown in ("rosters", "tier-presets", "dod", "", "FACTS", "facts "):
        with pytest.raises(ValueError, match="unknown docs region"):
            render_doc_fact_block(unknown, _FACTS)

    # … fail-soft boundary in the file writer: untouched plus one warning.
    text = "# Project\n\n" + _region_text("rosters", "hand-written table")
    log = _RecordingLog()
    result = apply_fact_blocks(text, _FACTS, log)
    assert result == text
    assert len(log.warnings) == 1
    assert "rosters" in log.warnings[0]

    # The computed-but-regionless blocks (W1-6 OPEN GAP) are not region names.
    assert "tier-presets" not in ALLOWED_REGIONS
    assert "dod-presets" not in ALLOWED_REGIONS


def test_docs_namespace_isolated_from_managed_block():
    """IC-08: ``docs-*`` is its own namespace beside ``agent-meta:managed-*``."""
    managed = (
        "<!-- agent-meta:managed-begin -->\n"
        "managed context body\n"
        "<!-- agent-meta:managed-end -->"
    )
    text = (
        "# Project\n\n"
        f"{managed}\n\n"
        + _region_text("facts", "stale generated table")
        + "\n<!-- agent-meta:docs-begin roster -->\nstale roster\n"
        "<!-- agent-meta:docs-end roster -->\n"
    )

    # Before: the docs regex does not see a single byte of the managed block.
    matches = list(DOCS_BLOCK_RE.finditer(text))
    assert [match.group("region") for match in matches] == ["facts", "roster"]
    assert all("managed" not in match.group("body") for match in matches)
    assert _has_duplicate_managed_block(text) is False

    result = apply_fact_blocks(text, _FACTS)

    # The managed block survived byte-identically …
    assert managed in result
    managed_match = _MANAGED_BLOCK_RE.search(result)
    assert managed_match is not None
    assert managed_match.group(0) == managed
    # … and the real managed-block machinery still sees exactly one pair.
    assert len(_MANAGED_BLOCK_RE.findall(result)) == 1
    assert _has_duplicate_managed_block(result) is False
    # … while both docs regions were rendered.
    assert "stale generated table" not in result
    assert "stale roster" not in result
    assert _FACTS["DOCS_REPO_FACTS_BLOCK"] in result
    assert _FACTS["DOCS_AGENT_ROSTER_BLOCK"] in result
    # The two namespaces never overlap in one match.
    for match in DOCS_BLOCK_RE.finditer(result):
        assert "managed-begin" not in match.group("body")
        assert "managed-end" not in match.group("body")


def test_region_marker_shape_and_spellings():
    """The marker regex is the published syntax (IC-08) and stays that way."""
    variants = [
        "<!-- agent-meta:docs-begin facts -->",
        "<!--agent-meta:docs-begin facts-->",
        "<!--  agent-meta:docs-begin   facts  -->",
    ]
    for begin in variants:
        text = f"{begin}\nbody\n<!-- agent-meta:docs-end facts -->\n"
        result = apply_fact_blocks(text, _FACTS)
        assert _FACTS["DOCS_REPO_FACTS_BLOCK"] in result
        assert result.startswith(begin), begin

    # A mismatched end name is not a pair — it must not be consumed.
    crossed = (
        "<!-- agent-meta:docs-begin facts -->\nbody\n"
        "<!-- agent-meta:docs-end roster -->\n"
    )
    log = _RecordingLog()
    assert apply_fact_blocks(crossed, _FACTS, log) == crossed
    assert len(log.warnings) == 1

    # An uppercase region name is outside the documented lowercase syntax and is
    # therefore not a region at all (no silent rendering under a wrong name).
    upper = "<!-- agent-meta:docs-begin FACTS -->\nbody\n<!-- agent-meta:docs-end FACTS -->\n"
    assert DOCS_BLOCK_RE.search(upper) is None


def _called_names(node: ast.AST) -> set[str]:
    """Every called name (attribute or bare) inside the AST *node*."""
    return {
        child.func.attr
        for child in ast.walk(node)
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute)
    } | {
        child.func.id
        for child in ast.walk(node)
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
    }


def _function_node(name: str) -> ast.FunctionDef:
    """The module-level ``def`` node of *name* in ``doc_renderer``."""
    tree = ast.parse(_MODULE_PATH.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"doc_renderer has no function {name!r}")


_FUNCTION_NODES: tuple[type[ast.AST], ...] = (ast.FunctionDef, ast.AsyncFunctionDef)
"""Both function-def node classes — ``AsyncFunctionDef`` must be named.

``ast.AsyncFunctionDef`` is a **sibling** of ``ast.FunctionDef``, not a subclass
(verified against the stdlib grammar), so an enumeration that names only the
sync class is not "almost complete": it is blind. An ``async def`` that calls
``write_text`` is a writer, and before this tuple named both classes such a
function was simply absent from the guard's input — invisible rather than
reported, which is the one failure mode a guard must not have. Every AST
enumeration of functions in this file goes through :func:`_functions_by_name`.
"""


def _functions_by_name(tree: ast.AST) -> dict[str, ast.AST]:
    """Every function def below *tree*, keyed by name (see :data:`_FUNCTION_NODES`)."""
    return {
        node.name: node for node in ast.walk(tree) if isinstance(node, _FUNCTION_NODES)
    }


def _leaks_disk(
    functions: dict[str, ast.AST], forbidden: set[str]
) -> dict[str, list[str]]:
    """Every function in *functions* that calls a *forbidden* name, with the calls.

    The **shared core** of both the real guard and the W3-1 differential. It
    deliberately applies no allowlist and no writer exemption of its own: which
    names are *exempt* is the whole point on which the two guard shapes disagree,
    so the caller states it and the predicate stays neutral. That is what makes
    the differential in :func:`test_module_level_write_free_guard_is_inverted` a
    comparison rather than a restatement — when the differential ran its own copy
    of the comprehension, mutating the real guard's shape (dropping a name from
    ``forbidden``, or reverting to an allowlist of write-free names) left the
    differential green.
    """
    return {
        name: sorted(_called_names(node) & forbidden)
        for name, node in functions.items()
        if _called_names(node) & forbidden
    }


def _write_free_offenders(
    functions: dict[str, ast.AST],
    writers: frozenset[str] | set[str],
    forbidden: set[str],
) -> dict[str, list[str]]:
    """The F-A guard: :func:`_leaks_disk` minus the declared writer set."""
    return {
        name: calls
        for name, calls in _leaks_disk(functions, forbidden).items()
        if name not in writers
    }



def _fold_string(node: ast.AST) -> str | None:
    """Constant-fold *node* to a string, or ``None`` when it is not constant.

    Folding is what makes the literal probe able to see a path that is assembled
    at import time. ``"docs" + "/" + "INDEX.md"`` is three literals, none of
    which is the path, so a scan over ``ast.Constant`` alone reports a clean
    module for exactly the drift the scan exists to catch — that is the second
    half of the W3-1 finding, and this is its fix. A ``JoinedStr`` counts only
    when every part is a constant, so a real format string is not a path.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _fold_string(node.left), _fold_string(node.right)
        return None if left is None or right is None else left + right
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if not (isinstance(value, ast.Constant) and isinstance(value.value, str)):
                return None
            parts.append(value.value)
        return "".join(parts)
    return None


def _literal_strings(tree: ast.AST) -> list[str]:
    """Every constant-folded string in *tree* that is **code**, not prose.

    A docstring is an ``ast.Constant`` like any other, so a naive literal scan
    cannot tell "this module spells the path" from "this module explains which
    path it produces". Only a bare ``Expr``-statement string is treated as prose
    here; every other string constant is reported, which is the strict direction
    to err in.
    """
    prose: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            continue
        for statement in node.body or ():
            if (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Constant)
                and isinstance(statement.value.value, str)
            ):
                prose.add(id(statement.value))
    folded = []
    for node in ast.walk(tree):
        if id(node) in prose:
            continue
        value = _fold_string(node)
        if value is not None:
            folded.append(value)
    return folded


def test_renderer_module_is_a_write_free_leaf():
    """The *rendering* API writes nothing; the module still cannot import config.

    W3-1 adds one writer entry point (``sync_docs_consolidation``) to this
    module, so the W1-7 pin is **re-scoped per function** rather than dropped.
    The rendering half stays a pure transformer — no ``open``, no
    ``Path.write_*`` — because a renderer that touched the filesystem could not
    be exercised against a tracked file in a dry run. The writer half may reach
    the disk only through ``write_checked``, so idempotency, the secret scan and
    ``dry_run`` all stay in one funnel.

    W3-2 widens the import set exactly once, for ``.doc_facts``: the IC-10
    document needs the volatile-fact set and the fact computation, and a second
    copy of either in this module would be a second copy of the truth. The
    ``config`` prohibition is what the set exists to protect and is unchanged —
    ``doc_facts`` imports no ``config`` either, so the IC-11 bridge is intact.

    **``.spec_plan_scaffold`` widens it again, at symbol granularity,** and the
    argument is the same one: the scaffold owns the ``file-index`` placeholder
    on this path, so the writer has to ask *that module* whether the target is
    its skeleton (IC-15) instead of re-implementing the probe. A local copy would
    have kept passing after a change to the F20 marker line — the exact drift the
    allowlist exists to make visible. ``spec_plan_scaffold`` imports no
    ``config`` either, so the prohibition and the IC-11 bridge both hold.

    The second set is per **symbol**, not per module, and that is the point:
    ``spec_plan_scaffold`` is a module that *does* write (it owns
    ``scaffold_spec_plan_dirs``), so a module-name allowlist would wave through
    ``from .spec_plan_scaffold import scaffold_spec_plan_dirs`` and void the
    single-funnel invariant this test exists for. **Granularity, not the number
    of entries, is the signal that should trigger review** on a future widening:
    one more pure helper imported from an already-allowed module is cheap, while
    one more *writer* reaching this module is a new disk path, however small the
    list gets.
    """
    tree = ast.parse(_MODULE_PATH.read_text(encoding="utf-8"))

    imported: set[str] = set()
    symbols: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            # A TYPE_CHECKING block is not an import-time edge, but a lib import
            # would still be an unwanted dependency of a leaf module.
            module = ("." * (node.level or 0)) + (node.module or "")
            imported.add(module)
            symbols.update((module, alias.name) for alias in node.names)
    assert imported <= {
        "__future__",
        "hashlib",
        "re",
        "typing",
        "collections.abc",
        "pathlib",
        ".io",
        ".log",
        ".doc_index",
        ".doc_facts",
        ".spec_plan_scaffold",
    }, imported
    assert symbols <= {
        ("__future__", "annotations"),
        ("typing", "TYPE_CHECKING"),
        ("typing", "Protocol"),
        ("collections.abc", "Mapping"),
        ("pathlib", "Path"),
        (".io", "safe_path"),
        (".io", "write_checked"),
        (".log", "SyncLog"),
        (".doc_index", "DOCS_INDEX_FILENAME"),
        (".doc_index", "DOCS_INDEX_RELPATH"),
        (".doc_index", "KIND_ORDER"),
        (".doc_index", "build_index_model"),
        (".doc_index", "has_docs_tree"),
        (".doc_facts", "VOLATILE_FACTS"),
        (".doc_facts", "compute_doc_facts"),
        (".spec_plan_scaffold", "is_file_index_skeleton"),
        (".spec_plan_scaffold", "resolve_index_mode"),
    }, sorted(symbols)
    # Positive pin: the guard is the scaffold's function *by name*. Without it
    # the allowlist would stay satisfied by an unrelated symbol of that module.
    assert (".spec_plan_scaffold", "is_file_index_skeleton") in symbols
    assert not any("config" in name.split(".")[-1] for name in imported), imported

    forbidden = {"open", "write_text", "write_bytes", "mkdir", "remove", "unlink", "rmtree"}
    for name in ("apply_fact_blocks", "render_doc_fact_block", "is_valid_region"):
        called = _called_names(_function_node(name))
        assert not (called & forbidden), (name, sorted(called & forbidden))

    # The writer half may read the target, but every mutation funnels through
    # write_checked — a second write path would be a second idempotency contract.
    writer_forbidden = (forbidden - {"open"}) | {"rename", "replace", "touch"}
    writer_calls = _called_names(_function_node("sync_docs_consolidation"))
    leaked = writer_calls & writer_forbidden
    assert not leaked, sorted(leaked)
    assert "write_checked" in writer_calls, "every mutation must use write_checked"

    # Determinism of the public surface, restated as an import-time fact.
    assert re is not None and doc_renderer.__doc__


# ==========================================================================
# W1-8 (IC-09, AC-17 model share, NFA-01, NFA-02) — the docs tree model
# ==========================================================================
#
# Plan task W1-8 shares this file with W1-7 (both list it under "Create" in
# `parallel_group: PG-1 / W1-B`); W1-7 created it, so everything below is an
# **append** — the eleven W1-7 tests above are untouched and must stay green.
#
# The unit under test is `scripts.lib.doc_index.build_index_model`, the single
# component that knows documentation-filesystem semantics. The properties that
# are hard to restore once an index has been generated and trusted:
#
# * **No invented description.** A page without a frontmatter `description` gets
#   the placeholder, and its title falls back to the file name. A plausible
#   fabricated one-liner is, in review, indistinguishable from a real one — the
#   exact failure class this initiative exists to remove — so the test pins the
#   *absence* of prose, not merely the presence of a field.
# * **Byte-identical on a second run** (NFA-01). `Path.rglob` yields filesystem
#   order, which is not stable across machines or checkouts; the two-key sort is
#   the only thing making the model deterministic, and it is easy to break
#   silently by "simplifying" it into a path-only sort.
# * **Exclusion and sort order** (NFA-02). `archive/` must not appear, and the
#   sequence must be grouped by `kind` in the fixed order before `path`.
#
# Every test builds its own `tmp_path` tree, so it does not depend on the
# repository's `docs/` composition (that tree is mid-migration). The real tree is
# used exactly once, as a read-only sanity check that the module survives
# contact with the whole documentation corpus without crashing or leaking an
# absolute path.


def _docs_root(tmp_path: Path) -> Path:
    """An empty ``<tmp_path>/docs``; returns the *project root*."""
    (tmp_path / "docs").mkdir()
    return tmp_path


def _write_page(root: Path, relpath: str, text: str) -> None:
    path = root / "docs" / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _page(root: Path, relpath: str, *, description: str, title: str = "Page Title") -> None:
    """Write one page *with* frontmatter carrying *description*."""
    _write_page(root, relpath, f"---\ndescription: {description}\n---\n# {title}\n")


def _by_path(model: dict) -> dict:
    return {entry["path"]: entry for entry in model["entries"]}


def test_index_model_shape_and_published_constants():
    """IC-09: the produced model and its published constants are the contract."""
    assert doc_index.EXCLUDED_DIR_SEGMENTS == frozenset({"archive", "_archive", "local-Inputs"})
    assert doc_index.DESCRIPTION_MAX_CHARS == 120
    assert isinstance(doc_index.EXCLUDED_DIR_SEGMENTS, frozenset)
    assert doc_index.KIND_ORDER == (
        "architecture",
        "api",
        "providers",
        "guides",
        "specs",
        "plans",
        "spikes",
        "concepts",
        "se-cascade",
        "other",
    )
    assert doc_index.KIND_ORDER[-1] == "other", "the residual bucket must sort last"


def test_index_model_entry_shape_and_relative_root(tmp_path: Path):
    """Every entry carries exactly the five published keys; ``root`` stays relative."""
    root = _docs_root(tmp_path)
    _page(root, "architecture/01-layer.md", description="Override priority of the four layers.")
    _page(root, "guides/getting-started.md", description="How to get going.")

    model = doc_index.build_index_model(root)

    assert set(model) == {"root", "entries"}
    assert model["root"] == "docs", "root must be relative — an absolute path leaks the checkout"
    assert not Path(model["root"]).is_absolute()
    assert all(set(entry) == {"path", "title", "description", "kind", "depth"} for entry in model["entries"])
    assert model["entries"] == [
        {
            "path": "architecture/01-layer.md",
            "title": "Page Title",
            "description": "Override priority of the four layers.",
            "kind": "architecture",
            "depth": 1,
        },
        {
            "path": "guides/getting-started.md",
            "title": "Page Title",
            "description": "How to get going.",
            "kind": "guides",
            "depth": 1,
        },
    ]


def test_archive_and_friends_are_excluded_at_any_depth(tmp_path: Path):
    """``archive/``, ``_archive/`` and ``local-Inputs/`` never contribute entries."""
    root = _docs_root(tmp_path)
    _page(root, "specs/live.md", description="kept")
    _page(root, "specs/archive/dead.md", description="dropped")
    _page(root, "archive/specs/deeper.md", description="dropped")
    _page(root, "plans/_archive/old.md", description="dropped")
    _page(root, "guides/local-Inputs/note.md", description="dropped")
    _page(root, "guides/local-Inputs/nested/deep.md", description="dropped")
    _page(root, "concepts/mentions-archive-in-prose.md", description="kept")

    entries = _by_path(doc_index.build_index_model(root))

    assert set(entries) == {"specs/live.md", "concepts/mentions-archive-in-prose.md"}, sorted(entries)
    for excluded in ("archive", "_archive", "local-Inputs"):
        assert excluded in doc_index.EXCLUDED_DIR_SEGMENTS


def test_exclusion_applies_to_directory_segments_only(tmp_path: Path):
    """A *page* named like an excluded segment is still a page, not a directory."""
    root = _docs_root(tmp_path)
    _page(root, "specs/archive.md", description="a page, not a directory")

    assert set(_by_path(doc_index.build_index_model(root))) == {"specs/archive.md"}


def test_page_without_frontmatter_yields_filename_and_placeholder(tmp_path: Path):
    """No frontmatter → file name as title, ``—`` as description, no prose."""
    root = _docs_root(tmp_path)
    _write_page(root, "guides/bare-note.md", "Just prose, no frontmatter, no heading.\n")

    (entry,) = doc_index.build_index_model(root)["entries"]

    assert entry["title"] == "bare-note"
    assert entry["description"] == "—"
    assert entry["description"] == doc_index.EMPTY_DESCRIPTION
    assert "Just prose" not in entry["description"]


def test_no_description_is_ever_invented(tmp_path: Path):
    """Every absent-or-unusable description maps to the placeholder, never to prose.

    This is the load-bearing test of the whole initiative: it enumerates the ways
    a description could plausibly be fabricated (the H1, the first body line, the
    file stem, a YAML list rendered by ``str()``) and asserts none of them leak.
    """
    root = _docs_root(tmp_path)
    _page(root, "guides/with-desc.md", description="A real declared description.", title="Heading One")
    _write_page(
        root,
        "guides/no-frontmatter.md",
        "# Heading One\n\nThe first body line, which must not become the description.\n",
    )
    _write_page(root, "guides/empty-desc.md", "---\ndescription: \"\"\n---\n# Heading Two\n\nBody.\n")
    _write_page(root, "guides/blank-desc.md", "---\ndescription: \"   \"\n---\n# Heading Three\n\nBody.\n")
    _write_page(
        root,
        "guides/list-desc.md",
        "---\ndescription:\n  - one\n  - two\n---\n# Heading Four\n\nBody.\n",
    )

    entries = _by_path(doc_index.build_index_model(root))

    assert entries["guides/with-desc.md"]["description"] == "A real declared description."

    for relpath in (
        "guides/no-frontmatter.md",
        "guides/empty-desc.md",
        "guides/blank-desc.md",
        "guides/list-desc.md",
    ):
        description = entries[relpath]["description"]
        assert description == doc_index.EMPTY_DESCRIPTION, (relpath, description)
        for leak in ("Heading", "first body line", "one", "two", "Body", Path(relpath).stem):
            assert leak not in description, (relpath, leak)


def test_title_prefers_first_h1_and_falls_back_to_filename(tmp_path: Path):
    """IC-09 title rule: first ``# `` heading, else the name without its suffix."""
    root = _docs_root(tmp_path)
    _write_page(root, "guides/real-title.md", "---\ndescription: d\n---\n# Real Title\n\n## Sub\n\n# Later\n")
    _write_page(root, "guides/no-heading.md", "---\ndescription: d\n---\nProse only.\n")
    _write_page(root, "guides/bare-hash.md", "---\ndescription: d\n---\n#\n\nProse.\n")
    _write_page(root, "guides/setext.md", "---\ndescription: d\n---\nSetext Title\n===\n")

    entries = _by_path(doc_index.build_index_model(root))

    assert entries["guides/real-title.md"]["title"] == "Real Title"
    assert entries["guides/no-heading.md"]["title"] == "no-heading"
    assert entries["guides/bare-hash.md"]["title"] == "bare-hash", "a bare '#' is not a title"
    assert entries["guides/setext.md"]["title"] == "setext", "setext headings are not '# ' headings"


def test_description_is_truncated_to_the_published_budget(tmp_path: Path):
    """Descriptions are quoted, not summarised: cut at the budget, ellipsis inside it."""
    root = _docs_root(tmp_path)
    exact = "x" * doc_index.DESCRIPTION_MAX_CHARS
    _page(root, "guides/exact.md", description=exact, title="Exact")
    _page(root, "guides/too-long.md", description="y" * (doc_index.DESCRIPTION_MAX_CHARS + 500), title="Long")
    _write_page(
        root,
        "guides/wrapped.md",
        "---\ndescription: >-\n  " + "  \n  word ".join(["word"] * 60) + "\n---\n# Wrapped\n",
    )

    entries = _by_path(doc_index.build_index_model(root))

    assert entries["guides/exact.md"]["description"] == exact, "at the budget: untouched"
    truncated = entries["guides/too-long.md"]["description"]
    assert len(truncated) == doc_index.DESCRIPTION_MAX_CHARS
    assert truncated.endswith("…")
    assert truncated == "y" * (doc_index.DESCRIPTION_MAX_CHARS - 1) + "…"
    assert all(len(entry["description"]) <= doc_index.DESCRIPTION_MAX_CHARS for entry in entries.values())
    wrapped = entries["guides/wrapped.md"]["description"]
    assert "\n" not in wrapped, "one-line contract"
    assert wrapped.startswith("word word")
    assert "  " not in wrapped, "internal whitespace is folded"


def test_entries_sort_by_kind_then_path(tmp_path: Path):
    """NFA-02: group by ``kind`` in ``KIND_ORDER``, then ``path`` ascending."""
    root = _docs_root(tmp_path)
    for relpath in (
        "specs/b-second.md",
        "specs/a-first.md",
        "architecture/zz-last.md",
        "architecture/aa-first.md",
        "guides/g-one.md",
        "unknown-dir/u-one.md",
        "se-cascade/s-one.md",
        "top-level.md",
    ):
        _page(root, relpath, description="d", title=relpath)

    model = doc_index.build_index_model(root)
    kinds = [entry["kind"] for entry in model["entries"]]
    paths = [entry["path"] for entry in model["entries"]]

    order = [doc_index.KIND_ORDER.index(kind) for kind in kinds]
    assert order == sorted(order), "kinds must be grouped in KIND_ORDER"
    assert kinds[0] == "architecture" and kinds[-1] == "other"

    for kind in set(kinds):
        same_kind = [path for path, entry_kind in zip(paths, kinds) if entry_kind == kind]
        assert same_kind == sorted(same_kind), (kind, same_kind)

    assert paths[:2] == ["architecture/aa-first.md", "architecture/zz-last.md"]
    assert paths[-2:] == ["top-level.md", "unknown-dir/u-one.md"], "the residual bucket is last"

    # A path-only sort would put `architecture` last; the kind grouping is what
    # keeps one new top-level section from reshuffling the whole file, so pin
    # the difference rather than trusting the reader to spot it.
    assert paths != sorted(paths)


def test_two_calls_on_one_tree_are_byte_identical(tmp_path: Path):
    """NFA-01: determinism, proven on bytes, on the root spelling and on mtimes."""
    root = _docs_root(tmp_path)
    for index in range(6):
        _page(root, f"specs/s{index}.md", description=f"desc {index}", title=f"S {index}")
    _page(root, "specs/archive/old.md", description="excluded")
    _page(root, "guides/guide.md", description="d", title="G")

    first = json.dumps(doc_index.build_index_model(root), sort_keys=True, ensure_ascii=False)
    second = json.dumps(doc_index.build_index_model(root), sort_keys=True, ensure_ascii=False)

    assert first == second
    assert first.encode("utf-8") == second.encode("utf-8")

    via_absolute = json.dumps(
        doc_index.build_index_model(root.resolve()), sort_keys=True, ensure_ascii=False
    )
    assert via_absolute == first, "the model must not depend on the spelling of the root"

    for relpath in ("specs/s0.md", "guides/guide.md"):
        os.utime(root / "docs" / relpath, (0, 0))
    after_touch = json.dumps(doc_index.build_index_model(root), sort_keys=True, ensure_ascii=False)
    assert after_touch == first, "mtime is not an input (NFA-02)"


def test_index_model_on_the_real_docs_tree():
    """Read-only sanity check against the real tree: no crash, invariants hold."""
    repo_root = Path(__file__).resolve().parents[1]

    model = doc_index.build_index_model(repo_root)
    entries = model["entries"]

    assert model["root"] == "docs"
    assert entries, "the real docs/ tree must not be empty"
    assert all(entry["path"].endswith(".md") for entry in entries)
    assert all(not Path(entry["path"]).is_absolute() for entry in entries)
    assert not [entry for entry in entries if set(entry["path"].split("/")[:-1]) & doc_index.EXCLUDED_DIR_SEGMENTS]
    assert len({entry["path"] for entry in entries}) == len(entries), "no duplicate paths"
    assert all(entry["kind"] in doc_index.KIND_ORDER for entry in entries)
    assert all(entry["depth"] == entry["path"].count("/") for entry in entries)
    assert all(0 < len(entry["description"]) <= doc_index.DESCRIPTION_MAX_CHARS for entry in entries)
    assert all(entry["title"] for entry in entries), "an entry with an empty title is unroutable"

    kinds = [doc_index.KIND_ORDER.index(entry["kind"]) for entry in entries]
    assert kinds == sorted(kinds)

    # On the real tree a *fabricated* description would do the most damage, so
    # assert the classic fabrication — the file's own stem restated as prose —
    # is absent.
    for entry in entries:
        if entry["description"] != doc_index.EMPTY_DESCRIPTION:
            assert entry["description"] != Path(entry["path"]).stem


def test_missing_docs_tree_degrades_instead_of_raising(tmp_path: Path):
    """No ``docs/`` is an empty model, not an exception — a renderer must survive it."""
    empty = tmp_path / "project"
    empty.mkdir()

    assert doc_index.build_index_model(empty) == {"root": "docs", "entries": []}


def test_index_module_is_a_write_free_leaf():
    """No ``config`` import (W3 wires it) and no write call anywhere in the module."""
    source = Path(doc_index.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(("." * (node.level or 0)) + (node.module or ""))
    assert "__future__" in imported
    assert imported <= {"__future__", "pathlib", ".frontmatter"}, imported
    assert not any("config" in name.split(".")[-1] for name in imported), imported

    called = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    } | {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    forbidden = {
        "open",
        "write_text",
        "write_bytes",
        "mkdir",
        "remove",
        "unlink",
        "rmtree",
        "rename",
        "replace",
        "touch",
    }
    assert not (called & forbidden), called & forbidden

    # No provider-name branching (NFA-03). Checked against string literals and
    # identifiers rather than the raw source: `continue` is a Python keyword, so
    # a substring scan would either false-positive on it or have to drop the
    # check for exactly the provider that matters most here.
    provider_names = {
        "claude",
        "gemini",
        "copilot",
        "continue",
        "opencode",
        "mammouth",
        "zcode",
        "kimi",
        "aider",
        "cursor",
    }
    literals = {
        node.value.lower()
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    identifiers = {
        node.id.lower()
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    } | {
        node.attr.lower()
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
    }
    assert not (literals & provider_names), sorted(literals & provider_names)
    assert not (identifiers & provider_names), sorted(identifiers & provider_names)


# ---------------------------------------------------------------------------
# W1-10 — AC-24 (IC-13, IC-22): the additive ``docs-consolidation`` config keys
# and the *absence default*.
#
# WHAT IS DELIVERED HERE, AND WHAT IS NOT
# ---------------------------------------
# This run delivers the **test half only**. The production half of W1-10 — the
# five additive keys ``docs-consolidation.{enabled, index-mode, checks.strict,
# sources, volatile-facts}`` plus the explicit ``enabled: true`` that NG-9
# requires for agent-meta itself — is **DEFERRED and NOT DELIVERED in this
# run**: writing ``.meta-config/project.yaml`` is outside this task's file
# ownership (the caller's scope constraint forbids touching that file and every
# other file under ``.meta-config/``). Nothing in this block sets, defaults or
# otherwise enables the feature, and no test here may be read as evidence that
# the generator or the V1–V9 checks are active in this repository. They are not.
#
# ``docs-consolidation.checks.strict`` must additionally stay **not-``true``**
# until W3-4 — W1 only ever declares the key, and the promotion of V1 from
# WARNING to ERROR belongs to W3-4. The fixture below deliberately sets
# ``checks.strict: true`` to prove that the master switch dominates every
# sub-key, which is a statement about precedence, not about the value agent-meta
# should carry.
#
# WHY THE ABSENCE CASE IS THE INTERESTING ONE
# -------------------------------------------
# IC-22 resolves its own contradiction (rev. 0.1) by borrowing the repo's
# fail-off precedence: ``scripts/lib/knowledge.py:127`` reads
# ``ke_config.get("enabled", False)``, so "not explicitly true" means "off".
# The same rule is declared per key in ``config/project-config.schema.json``
# (W1-9) and applies equally to the writer (IC-13) and to the checks V1–V9.
# AC-24 therefore has two halves that must be *observationally identical*:
# ``enabled: false`` and "the block is not there at all". Both are asserted here
# against the **real** ``scripts.lib.config.load_config`` funnel — not against a
# hand-rolled parser — so a funnel that normalises, injects or reorders the
# block cannot slip past.
#
# The two fixture configs are built in ``tmp_path``. The absence test never
# reads ``.meta-config/project.yaml`` for its fixture, so it keeps testing
# absence even after the production keys land — and it *proves* that rather than
# claiming it, by pointing the live path at an enabled config for the duration
# (see ``test_absent_block_is_noop``). The live file is observed in exactly one
# separate, self-invalidating test, which *skips* (never silently passes) once
# the block exists.
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LIVE_PROJECT_CONFIG = _REPO_ROOT / ".meta-config" / "project.yaml"
_SCHEMA_PATH = _REPO_ROOT / "config" / "project-config.schema.json"

#: IC-22's "default on absence" column, for the five additive top-level keys.
#: ``checks`` is a block whose only member is ``strict``; the sixth IC-22 row
#: (``knowledge-engine.okf.index-mode``) belongs to W7-2 and is out of scope.
_IC22_ABSENCE_DEFAULTS: dict = {
    "enabled": False,
    "index-mode": "full",
    "checks": {"strict": False},
    "sources": [],
    "volatile-facts": ["DOCS_SCENARIO_COUNT"],
}

#: The one legal outcome of a fail-off gate, spelled out so the assertion is a
#: value comparison rather than a truthiness check: the IC-13 ``log.skip`` tuple,
#: an empty write set and zero executed checks.
_NOOP_PLAN: dict = {
    "generator": {
        "runs": False,
        "writes": [],
        "log": ["skip", "docs-consolidation", "disabled in project.yaml"],
    },
    "checks": {"runs": False, "v1_v9_executed": 0, "strict": False},
    "index-mode": None,
}


def _schema_absence_defaults(block_schema: dict) -> dict:
    """Effective absence default per top-level key, read off the W1-9 schema.

    ``checks`` carries no default of its own — an absent ``checks`` block is
    ``{}`` and ``strict`` then falls back to *its* default — so the nested
    defaults have to be folded in for the comparison to mean anything.
    """
    resolved: dict = {}
    for key, prop in block_schema["properties"].items():
        if key == "checks":
            resolved[key] = {
                nested: nested_prop.get("default")
                for nested, nested_prop in prop.get("properties", {}).items()
            }
        else:
            resolved[key] = prop.get("default")
    return resolved


def _minimal_project_config() -> dict:
    """A schema-valid minimal ``project.yaml`` mapping (``project`` is required)."""
    return {
        "project": {"name": "w1-10-fixture", "prefix": "am", "short": "fixture"},
        "default-provider": "Claude",
        "rules-preset": "default",
    }


def _write_temp_project_config(tmp_path: Path, block: dict | None) -> Path:
    """Write a throwaway ``project.yaml``; ``block=None`` means *no* block at all.

    ``block=None`` is deliberately not "``docs-consolidation: {}``": the absent
    case must be absent at the byte level, otherwise the test would prove
    nothing about a genuinely missing key.
    """
    import yaml

    data = _minimal_project_config()
    if block is not None:
        data["docs-consolidation"] = block
    path = tmp_path / "project.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=True), encoding="utf-8")
    return path


def _load_via_funnel(path: Path) -> dict:
    """Load through the production funnel (``load_config``), not a private parser."""
    from scripts.lib.config import load_config

    return load_config(path)


def _docs_consolidation_plan(config: dict) -> dict:
    """Reference implementation of the IC-13/IC-22 consumer contract.

    Deliberately a *total* function of the config mapping: the gate is read with
    the ``knowledge.py:127`` idiom (``.get("enabled", False)``), so an absent
    block, a non-mapping block and an explicit ``false`` all collapse onto the
    same all-no-op plan. Every consumer (generator and checks V1–V9) is
    represented, because IC-22 requires the switch to govern *both* and a gate
    that only silenced the writer would still be a fail-*open* gate.
    """
    block = config.get("docs-consolidation")
    block = block if isinstance(block, dict) else {}
    checks = block.get("checks")
    checks = checks if isinstance(checks, dict) else {}
    if block.get("enabled", False) is not True:
        return json.loads(json.dumps(_NOOP_PLAN))
    return {
        "generator": {
            "runs": True,
            "writes": ["docs/INDEX.md"],
            "log": None,
        },
        "checks": {
            "runs": True,
            "v1_v9_executed": 9,
            "strict": checks.get("strict", False) is True,
        },
        "index-mode": block.get("index-mode", "full"),
    }


def _tree_dir(tmp_path: Path) -> Path:
    """A throwaway project root holding a small but non-empty ``docs/`` tree."""
    root = tmp_path / "consumer-tree"
    root.mkdir()
    _page(root, "specs/one.md", description="First spec page.")
    _page(root, "guides/two.md", description="Second page.")
    return root


def _tree_snapshot(root: Path) -> dict:
    """``{relative path: sha256}`` for every file under *root* (recursive)."""
    import hashlib

    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _assert_consumer_surface_is_write_free(root: Path, config: dict) -> None:
    """No docs-consolidation consumer writes anything — observed, not assumed.

    Runs the whole consumer surface that exists today — including the W3-1
    generator entry point, now behind the very same gate — against a throwaway
    tree and byte-compares the tree afterwards. The behavioural half is the
    claim; the structural half is what keeps it honest: the two *readers*
    (``doc_facts``, ``doc_index``) must still contain no write call at all, so a
    future edit cannot smuggle a write past a gate that only silences the
    writer.
    """
    from scripts.lib import doc_facts  # noqa: F401 — the facts module is consumer surface too

    before = _tree_snapshot(root)
    assert before, "the fixture tree must not be empty — an empty snapshot proves nothing"

    doc_index.build_index_model(root)
    for region in ALLOWED_REGIONS:
        render_doc_fact_block(region, _FACTS)
    tracked = "<!-- agent-meta:docs-begin FACTS -->\nold\n<!-- agent-meta:docs-end FACTS -->\n"
    apply_fact_blocks(tracked, _FACTS)
    plan = doc_renderer.sync_docs_consolidation(
        root, root, config, {}, SyncLog(), dry_run=False
    )

    after = _tree_snapshot(root)
    assert after == before, "a docs-consolidation consumer wrote to the tree: %r" % (
        sorted(set(after) ^ set(before)) or [k for k in before if after[k] != before[k]]
    )
    assert plan == {"written": [], "unchanged": [], "skipped": []}, plan

    forbidden = {
        "open",
        "write_text",
        "write_bytes",
        "mkdir",
        "remove",
        "unlink",
        "rmtree",
        "rename",
        "touch",
        "write_checked",
    }
    for module in (doc_facts, doc_index):
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        called = _called_names(tree)
        assert not (called & forbidden), (module.__name__, sorted(called & forbidden))


def test_disabled_flag_is_noop(tmp_path: Path):
    """AC-24, second half: ``enabled: false`` makes *every* consumer a no-op.

    The sub-keys are set to the values that would otherwise produce work —
    ``sources`` non-empty (rendering), ``index-mode: full`` (index replacement)
    and ``checks.strict: true`` (V1 as ERROR). The master switch has to dominate
    all of them; a consumer that read ``sources`` or ``strict`` independently
    would produce a plan other than the all-no-op plan and fail here.
    """
    path = _write_temp_project_config(
        tmp_path,
        {
            "enabled": False,
            "index-mode": "full",
            "checks": {"strict": True},
            "sources": ["README.md", "llms.txt", "ARCHITECTURE.md"],
            "volatile-facts": ["DOCS_SCENARIO_COUNT"],
        },
    )

    loaded = _load_via_funnel(path)

    # The funnel must not normalise the flag away — this is the production
    # anchor; without it the assertion below would only describe this file.
    assert loaded["docs-consolidation"]["enabled"] is False
    assert loaded["docs-consolidation"]["checks"]["strict"] is True, (
        "strict stays as written; the master switch, not the funnel, is what "
        "keeps the checks off"
    )

    plan = _docs_consolidation_plan(loaded)
    assert plan == _NOOP_PLAN, plan
    assert plan["generator"]["writes"] == [], "a disabled generator must write nothing"
    assert plan["checks"]["v1_v9_executed"] == 0, "V1–V9 are no-ops while disabled"
    assert plan["generator"]["log"] == ["skip", "docs-consolidation", "disabled in project.yaml"]

    # Anti-tautology: the same plan function must *distinguish* an enabled
    # config, otherwise the no-op assertion above would hold for any default.
    on_dir = tmp_path / "on"
    on_dir.mkdir()
    enabled_plan = _docs_consolidation_plan(
        _load_via_funnel(
            _write_temp_project_config(on_dir, {"enabled": True, "index-mode": "full"})
        )
    )
    assert enabled_plan != _NOOP_PLAN
    assert enabled_plan["generator"]["writes"] == ["docs/INDEX.md"]

    _assert_consumer_surface_is_write_free(_tree_dir(tmp_path), loaded)


def test_absent_block_is_noop(tmp_path: Path, monkeypatch):
    """AC-24, first half: no block at all behaves exactly like ``enabled: false``.

    Absence means ``false`` (IC-22, precedence ``scripts/lib/knowledge.py:127``).
    The fixture is a throwaway config in ``tmp_path`` — the live
    ``.meta-config/project.yaml`` is deliberately **not** consulted, so this test
    keeps proving absence after the production keys land.
    """
    import yaml

    absent_path = _write_temp_project_config(tmp_path / "absent", None)
    disabled_path = _write_temp_project_config(
        tmp_path / "disabled", {"enabled": False, "checks": {"strict": True}}
    )

    # Byte-level absence: not "an empty block", not "a default-filled block".
    absent_text = absent_path.read_text(encoding="utf-8")
    assert "docs-consolidation" not in absent_text
    assert yaml.safe_load(absent_text) == _minimal_project_config()

    # Independence from the live config, *proved* rather than asserted in prose.
    # Point the live path at a config that is switched ON: if any code under test
    # still read it, every absence assertion below would turn into a false green
    # the moment W1-10's production half lands. With this in place the test can
    # only pass by exercising its own absent-block fixture.
    poisoned_live = _write_temp_project_config(
        tmp_path / "poisoned-live", {"enabled": True, "index-mode": "full"}
    )
    monkeypatch.setattr(
        sys.modules[__name__], "_LIVE_PROJECT_CONFIG", poisoned_live, raising=True
    )
    assert absent_path != _LIVE_PROJECT_CONFIG
    assert _docs_consolidation_plan(_load_via_funnel(_LIVE_PROJECT_CONFIG)) != _NOOP_PLAN, (
        "the poisoned live config must actually be enabled — otherwise this guard "
        "proves nothing"
    )

    absent = _load_via_funnel(absent_path)
    disabled = _load_via_funnel(disabled_path)

    assert "docs-consolidation" not in absent, "the funnel must not synthesise the block"
    assert _docs_consolidation_plan(absent) == _NOOP_PLAN
    assert _docs_consolidation_plan(absent) == _docs_consolidation_plan(disabled), (
        "absence and an explicit false must be observationally identical (IC-22)"
    )

    # The absence defaults are *declared*, not merely implied: the schema (W1-9)
    # is the contract a consumer may rely on, and the fail-off idiom it borrows
    # is pinned in the knowledge writer it was taken from.
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    block_schema = schema["properties"]["docs-consolidation"]
    assert block_schema.get("additionalProperties") is False, "the block closes itself"
    assert "required" not in block_schema, "the block must stay optional"
    assert _schema_absence_defaults(block_schema) == _IC22_ABSENCE_DEFAULTS
    knowledge_source = (_REPO_ROOT / "scripts" / "lib" / "knowledge.py").read_text(encoding="utf-8")
    assert 'ke_config.get("enabled", False)' in knowledge_source, (
        "IC-22 borrows this exact idiom; if it changes, the absence default must be re-derived"
    )

    # The additive keys are legal as they stand, so the deferred production half
    # is a pure addition — no schema change is owed by W1-10.
    jsonschema = pytest.importorskip("jsonschema")
    for candidate in (absent, disabled):
        jsonschema.validate(candidate, schema)

    consumer_tree = _tree_dir(tmp_path)
    for gated in (absent, disabled):
        _assert_consumer_surface_is_write_free(consumer_tree, gated)


def test_live_project_config_has_no_docs_consolidation_block_yet():
    """Observation, not a fixture: the live config is still the absent case.

    W1-10's production half is deferred, so ``.meta-config/project.yaml``
    genuinely carries no ``docs-consolidation`` block in this run and the live
    config therefore also gates off. This test exists only to *say* so out loud,
    with a byte-level check, and to invalidate itself loudly once the keys land:
    it skips rather than passing, so the deferred production work cannot be
    mistaken for having been covered here. The two tests above do not depend on
    it — they build their own fixtures — so the skip cannot hollow them out.
    """
    import yaml

    if not _LIVE_PROJECT_CONFIG.exists():
        pytest.skip("no .meta-config/project.yaml in this checkout")

    live = yaml.safe_load(_LIVE_PROJECT_CONFIG.read_text(encoding="utf-8")) or {}
    if "docs-consolidation" in live:
        pytest.skip(
            "the additive docs-consolidation keys now exist in .meta-config/project.yaml "
            "(W1-10 production half / NG-9): the absent-block observation no longer "
            "applies to the live config — re-derive this test before trusting it"
        )

    assert _docs_consolidation_plan(live) == _NOOP_PLAN
    assert "docs-consolidation" not in _LIVE_PROJECT_CONFIG.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# W3-1 — write, idempotency and dry_run contract (IC-13, AC-23, AC-26)
# ---------------------------------------------------------------------------

_ENABLED_CONFIG: dict = {"docs-consolidation": {"enabled": True}}

_EMPTY_PLAN: dict = {"written": [], "unchanged": [], "skipped": []}


def _run_sync(
    root: Path, config: dict, *, dry_run: bool = False
) -> tuple[dict, SyncLog]:
    """Call the W3-1 writer and return ``(plan, log)``.

    ``agent_meta_root`` is a path that does not exist and the call asserts it
    stayed that way: this task consumes no file of the *source* checkout, and a
    test that quietly depended on this repository's state would be a worse test
    than one that depends on nothing.
    """
    sentinel = root / "no-agent-meta-root"
    log = SyncLog()
    plan = doc_renderer.sync_docs_consolidation(
        sentinel, root, config, {}, log, dry_run=dry_run
    )
    assert not sentinel.exists(), "agent_meta_root must stay unread"
    return plan, log


def test_dry_run_no_writes(tmp_path: Path):
    """AC-23: zero filesystem writes, ``written`` lists the write candidates.

    The second half pins the *log*: a dry run has to report intent, not a
    write. ``sync.py --dry-run --check`` is a CI gate, so a line tagged
    ``[CREATE]`` in a dry-run log is a claim that a write happened while the
    gate is supposed to be proving nothing happened.
    """
    root = _docs_root(tmp_path)
    _page(root, "specs/one.md", description="First spec page.")
    _page(root, "guides/two.md", description="Second page.")
    wiki_log = root / "knowledge" / "wiki" / "log.md"
    wiki_log.parent.mkdir(parents=True)
    wiki_before = "2026-09-26 09:00 - index - pre-existing\n"
    wiki_log.write_text(wiki_before, encoding="utf-8")

    before = _tree_snapshot(root)
    plan, log = _run_sync(root, _ENABLED_CONFIG, dry_run=True)

    assert _tree_snapshot(root) == before, "dry_run must not touch the tree at all"
    assert wiki_log.read_text(encoding="utf-8") == wiki_before
    assert not (root / "docs" / "INDEX.md").exists(), "dry_run creates nothing"
    assert plan == {
        "written": [doc_index.DOCS_INDEX_RELPATH],
        "unchanged": [],
        "skipped": [],
    }, plan

    index_actions = [line for line in log.actions if doc_index.DOCS_INDEX_RELPATH in line]
    assert len(index_actions) == 1, log.actions
    # Compare the whole tag field rather than a substring. ``SyncLog.action``
    # pads the tag to width 8, so a real write reads ``[CREATE  ]`` — a plain
    # ``"[CREATE]" not in line`` would be vacuously true for it — and
    # ``"WOULD-CREATE"`` *contains* ``"CREATE"``, so containment would be
    # vacuously satisfied by a real write too. Both failure modes avoided by
    # comparing the delimited field and normalising the padding.
    tag_field = index_actions[0].split("]")[0] + "]"
    assert tag_field == "[WOULD-CREATE]", index_actions
    assert tag_field.strip("[] ") not in ("CREATE", "UPDATE"), index_actions


def test_no_docs_dir_is_skipped_not_created(tmp_path: Path):
    """AC-26: a consumer project without ``docs/`` is skipped, never seeded."""
    root = tmp_path / "foreign-project"
    root.mkdir()

    for dry_run in (False, True):
        log = SyncLog()
        before = _tree_snapshot(root)
        plan = doc_renderer.sync_docs_consolidation(
            root / "no-agent-meta-root", root, _ENABLED_CONFIG, {}, log, dry_run=dry_run
        )

        assert not list(root.iterdir()), "no mkdir in a foreign project"
        assert _tree_snapshot(root) == before
        assert plan == {
            "written": [],
            "unchanged": [],
            "skipped": [doc_index.DOCS_INDEX_RELPATH],
        }, plan
        assert len(log.infos) == 1, log.infos
        assert doc_index.DOCS_INDEX_RELPATH in log.infos[0]
        assert doc_renderer.NO_DOCS_TREE_REASON in log.infos[0]
        assert log.actions == []


def test_identical_content_is_unchanged_without_write_checked(
    tmp_path: Path, monkeypatch
):
    """Zielinhalt == Istinhalt ⇒ ``unchanged``, and ``write_checked`` is not reached.

    The second run is the only proof of idempotency that survives a refactor:
    "the file has the right content" is also true right after a write, so the
    spy is what distinguishes "compared and found no change" from "wrote again".
    """
    root = _docs_root(tmp_path)
    _page(root, "specs/one.md", description="First spec page.")

    first, first_log = _run_sync(root, _ENABLED_CONFIG)
    assert first == {
        "written": [doc_index.DOCS_INDEX_RELPATH],
        "unchanged": [],
        "skipped": [],
    }, first
    assert len(first_log.actions) == 1 and "CREATE" in first_log.actions[0]

    seen: list[Path] = []
    real_write_checked = doc_renderer.write_checked

    def _spy(path, *args, **kwargs):
        seen.append(Path(path))
        return real_write_checked(path, *args, **kwargs)

    monkeypatch.setattr(doc_renderer, "write_checked", _spy)
    before = _tree_snapshot(root)
    second, second_log = _run_sync(root, _ENABLED_CONFIG)

    assert seen == [], "an unchanged target must not reach write_checked"
    assert second == {
        "written": [],
        "unchanged": [doc_index.DOCS_INDEX_RELPATH],
        "skipped": [],
    }, second
    assert _tree_snapshot(root) == before
    assert second_log.actions == []


def test_ownership_rule_never_overwrites_a_foreign_index(tmp_path: Path):
    """IC-13: a file another writer legitimately produced is never overwritten."""
    root = _docs_root(tmp_path)
    _page(root, "specs/one.md", description="First spec page.")
    foreign = "# Index\n\nHand-written index, kept by a maintainer.\n"
    target = root / "docs" / "INDEX.md"
    target.write_text(foreign, encoding="utf-8")

    plan, log = _run_sync(root, _ENABLED_CONFIG)

    assert target.read_text(encoding="utf-8") == foreign, "a foreign index must survive"
    assert plan == {
        "written": [],
        "unchanged": [],
        "skipped": [doc_index.DOCS_INDEX_RELPATH],
    }, plan
    assert len(log.infos) == 1, log.infos
    assert doc_renderer.OWNERSHIP_REASON in log.infos[0]
    assert log.actions == []


def test_undecodable_index_is_skipped_not_raised(tmp_path: Path, monkeypatch):
    """A non-UTF-8 target is reported, not crashed on — fail closed on decode too.

    ``UnicodeDecodeError`` subclasses ``ValueError``, **not** ``OSError``, and it
    is raised by the read rather than the open. With only ``except OSError`` on
    the renderer's read, a single latin-1 byte in an existing ``docs/INDEX.md``
    escaped the hardened path and aborted the whole sync — in the one place the
    comment there promises it cannot. The outcome is the same fail-closed one as
    a permission error: the file cannot be read, so ownership is unprovable and
    it is reported instead of overwritten.

    ``build_index_model`` is stubbed so this pins *this* read and not the
    caller: that helper reads ``docs/INDEX.md`` as an ordinary page before this
    function ever opens it, and it carries its own decode handling. Stubbing it
    is the only way to reach the line under test — and the same
    ``monkeypatch.setattr(doc_renderer, ...)`` seam the idempotency test uses.
    """
    root = _docs_root(tmp_path)
    _page(root, "specs/one.md", description="First spec page.")
    monkeypatch.setattr(
        doc_renderer, "build_index_model", lambda _root: {"root": "docs", "entries": []}
    )
    target = root / "docs" / "INDEX.md"
    # 0xE4 is 'a-umlaut' in latin-1 and an invalid UTF-8 lead byte here: it
    # demands two continuation bytes and gets a newline.
    undecodable = b"# Index\n\nUmlaut: \xe4\n"
    target.write_bytes(undecodable)
    before = _tree_snapshot(root)

    plan, log = _run_sync(root, _ENABLED_CONFIG)

    assert target.read_bytes() == undecodable, "an unreadable index must survive"
    assert _tree_snapshot(root) == before
    assert plan == {
        "written": [],
        "unchanged": [],
        "skipped": [doc_index.DOCS_INDEX_RELPATH],
    }, plan
    assert len(log.infos) == 1, log.infos
    assert doc_index.DOCS_INDEX_RELPATH in log.infos[0]
    assert doc_renderer.UNREADABLE_REASON in log.infos[0]
    # Pins the path actually taken, not just the shape: a report naming some
    # other failure would satisfy every assertion above.
    assert "UnicodeDecodeError" in log.infos[0], log.infos
    assert log.actions == []


def test_undecodable_index_does_not_abort_the_whole_sync(tmp_path: Path):
    """End-to-end: the whole ``sync_docs_consolidation`` call survives latin-1.

    The sibling test above hardens *one* read by stubbing ``build_index_model``,
    and that stub is precisely why it went green while the sync still aborted.
    The real helper treats ``docs/INDEX.md`` as an ordinary page and reads it
    **first**, through ``doc_index._entry_for``; that read carried the same
    ``except OSError``-only hole, so a ``UnicodeDecodeError`` escaped before the
    hardened read was ever reached. The earlier fix had only moved the failure
    one frame earlier — and a stubbed caller cannot see that, by construction.

    No stub here, on purpose. The claim under test is a property of the *call
    chain*, so replacing any link of it would exercise a program that no longer
    exists. Both holes have to be closed for this to pass, which is the point: a
    green suite has to mean "the sync is safe", not "one line of it is safe".
    """
    root = _docs_root(tmp_path)
    _page(root, "specs/one.md", description="First spec page.")
    target = root / "docs" / "INDEX.md"
    undecodable = b"# Index\n\nUmlaut: \xe4\n"
    target.write_bytes(undecodable)
    before = _tree_snapshot(root)

    plan, log = _run_sync(root, _ENABLED_CONFIG)

    assert target.read_bytes() == undecodable, "an unreadable index must survive"
    assert _tree_snapshot(root) == before, "a skipped index must not be rewritten"
    assert plan == {
        "written": [],
        "unchanged": [],
        "skipped": [doc_index.DOCS_INDEX_RELPATH],
    }, plan
    assert len(log.infos) == 1, log.infos
    assert doc_index.DOCS_INDEX_RELPATH in log.infos[0]
    assert doc_renderer.UNREADABLE_REASON in log.infos[0]
    assert "UnicodeDecodeError" in log.infos[0], log.infos
    assert log.actions == []


def test_generator_owned_index_is_updated(tmp_path: Path):
    """A file this generator wrote stays ours: a changed tree ⇒ UPDATE, not skip.

    Without this the ownership rule would freeze the index after its first
    creation — a fail-closed rule that quietly stops regenerating is worse than
    no rule, because it looks like a successful sync.
    """
    root = _docs_root(tmp_path)
    _page(root, "specs/one.md", description="First spec page.")
    _run_sync(root, _ENABLED_CONFIG)
    target = root / "docs" / "INDEX.md"
    first_body = target.read_text(encoding="utf-8")
    assert doc_renderer.DOCS_GENERATOR_ID in first_body, (
        "the generator must sign what it writes"
    )

    _page(root, "specs/two.md", description="Second spec page.")
    plan, log = _run_sync(root, _ENABLED_CONFIG)

    assert plan == {
        "written": [doc_index.DOCS_INDEX_RELPATH],
        "unchanged": [],
        "skipped": [],
    }, plan
    assert len(log.actions) == 1 and "UPDATE" in log.actions[0]
    body = target.read_text(encoding="utf-8")
    assert body != first_body
    assert doc_renderer.DOCS_GENERATOR_ID in body
    assert not (root / "knowledge").exists(), "a real run leaves the bundle alone"


def test_disabled_or_absent_gate_is_a_noop(tmp_path: Path, monkeypatch):
    """``enabled != true`` ⇒ skip log, zero writes, empty plan (IC-22 absence default).

    Four shapes, one behaviour: a missing block, an empty block, an explicit
    ``false`` carrying every sub-key that would otherwise produce work, and a
    block that is not even a mapping. A gate that only handled the third would
    still be fail-*open* for the two shapes every scenario fixture has.

    The three filesystem entry points are replaced by tripwires, so "no write"
    is proven as "not even a read": a byte-identical tree snapshot cannot tell
    a read-only probe from a no-op, and a probe is exactly what an
    "enabled"-blind writer would leave behind.
    """
    root = _docs_root(tmp_path)
    _page(root, "specs/one.md", description="First spec page.")

    def _unreachable(*args, **kwargs):
        raise AssertionError("the gate must short-circuit before any filesystem access")

    for name in ("has_docs_tree", "build_index_model", "write_checked"):
        monkeypatch.setattr(doc_renderer, name, _unreachable)

    for config in (
        {},
        {"docs-consolidation": {}},
        {
            "docs-consolidation": {
                "enabled": False,
                "index-mode": "full",
                "checks": {"strict": True},
                "sources": ["README.md"],
            }
        },
        {"docs-consolidation": "not-a-mapping"},
    ):
        before = _tree_snapshot(root)
        plan, log = _run_sync(root, config)

        assert plan == _EMPTY_PLAN, config
        assert _tree_snapshot(root) == before, config
        assert len(log.skipped) == 1, (config, log.skipped)
        assert doc_renderer.LOG_TARGET in log.skipped[0]
        assert doc_renderer.DISABLED_REASON in log.skipped[0]


def test_sync_entry_point_signature_and_result_shape(tmp_path: Path):
    """IC-13 pins the parameter list; the result is exactly three string lists."""
    params = list(inspect.signature(doc_renderer.sync_docs_consolidation).parameters)
    assert params == [
        "agent_meta_root",
        "project_root",
        "config",
        "provider_config",
        "log",
        "dry_run",
    ], params

    root = _docs_root(tmp_path)
    plan, _log = _run_sync(root, _ENABLED_CONFIG)

    assert set(plan) == {"written", "unchanged", "skipped"}
    for bucket in plan.values():
        assert isinstance(bucket, list)
        assert all(isinstance(item, str) for item in bucket)


def test_docs_index_relpath_is_composed_not_duplicated(tmp_path: Path):
    """The index path is derived from the docs root, so the two cannot drift.

    **The "not duplicated" half is a composed-constant pin, not a source scan.**
    W3-1 asserted ``"docs/INDEX.md" not in _MODULE_PATH.read_text()``, which
    fails on both counts at once: it fires on a mere *mention* in a docstring —
    prose about the document is not a second copy of the truth, and W3-2's
    renderer docstrings have to be able to name the file they produce — while
    missing real drift assembled at runtime as ``"docs" + "/" + "INDEX.md"``,
    which is precisely the kind of second copy the pin exists to catch. The
    literal-level probe now lives in
    :func:`test_index_path_is_not_spelled_as_a_literal`; what is pinned *here*
    is the composition itself.
    """
    assert doc_index.DOCS_RELPATH == "docs"
    assert doc_index.DOCS_INDEX_RELPATH == "docs/INDEX.md"
    assert doc_index.DOCS_INDEX_RELPATH == (
        f"{doc_index.DOCS_RELPATH}/{doc_index.DOCS_INDEX_FILENAME}"
    )
    assert doc_index.DOCS_INDEX_RELPATH.startswith(f"{doc_index.DOCS_RELPATH}/")

    # The renderer reaches the target through the constant, not through a path
    # of its own: observed, not asserted from the source text.
    root = _docs_root(tmp_path)
    _page(root, "specs/one.md", description="First spec page.")
    plan, _log = _run_sync(root, _ENABLED_CONFIG)
    assert plan["written"] == [doc_index.DOCS_INDEX_RELPATH], plan
    assert (root / doc_index.DOCS_INDEX_RELPATH).is_file()
    assert not (root / "docs" / "index.md").exists(), "the spelling is case-exact"

    with_tree = tmp_path / "with"
    with_tree.mkdir()
    _docs_root(with_tree)
    without_tree = tmp_path / "without"
    without_tree.mkdir()

    assert doc_index.has_docs_tree(with_tree) is True
    assert doc_index.has_docs_tree(without_tree) is False
    assert not (without_tree / "docs").exists(), "the predicate creates nothing"


# ==========================================================================
# W3-2 — the full IC-10 document: sections, facts table, volatile section,
# IC-14 footer. The unit under test is `doc_renderer.render_docs_index`,
# a **pure function** of `(index_model, facts)`.
# ==========================================================================
#
# The contracts that are hard to restore once `docs/INDEX.md` has been written
# and trusted:
#
# * **Determinism (NFA-01/AC-17).** Two renderings of one tree are byte-identical,
#   and the bytes depend on nothing but the model and the facts — not on dict
#   iteration order, not on mtime, not on the checkout path.
# * **The self-exclusion stays in the renderer.** `build_index_model` is a
#   faithful description of the tree (W1-8's published contract); the *document*
#   decides what it lists. A model that dropped its own target would change the
#   content the moment the file was created, and every later run would rewrite it.
# * **The footer is a hash, not a clock (AC-18).** No timestamp, no absolute
#   path, no username. A date here would make every sync a diff.
# * **The hash ignores volatile facts (AC-03).** Track A adds scenarios
#   continuously; a hash that moved with `DOCS_SCENARIO_COUNT` would rewrite the
#   footer of every index in the repository for a change that carries no
#   meaning. The value is still *shown*, in the `docs-volatile` section, so a
#   scenario landing is a one-line review diff.
# * **The generator id survives the move into the footer.** `_carries_generator_id`
#   is a substring probe, so an id that vanished from the render output would
#   silently freeze every index as permanently `skipped` while the sync log
#   stays green. Hence a test of its own.
#
# Two carried findings from the closed W3-1 review are fixed and pinned here:
# **F-A** inverts the write-free guard from a three-name allowlist of pure
# functions to an explicit writer set, and **F-B** replaces a raw-source
# substring scan with a literal-level probe. Both have their own negative
# controls, because a guard that cannot be shown to fail is not a guard.


def _facts(**overrides: str) -> dict:
    """A complete, non-degenerate fact dict for the IC-10 facts/volatile split."""
    base = {
        "DOCS_VERSION": "1.2.0-beta.2",
        "DOCS_AGENT_TEMPLATES_COUNT": "80",
        "DOCS_SCENARIO_COUNT": "63",
        "DOCS_REPO_FACTS_BLOCK": (
            "| Fact | Value |\n| --- | --- |\n| DOCS_VERSION | 1.2.0-beta.2 |"
        ),
    }
    base.update(overrides)
    return base


def _rendered(facts: dict | None = None) -> str:
    """The IC-10 document for the *real* repository tree, rendered pure."""
    return doc_renderer.render_docs_index(
        doc_index.build_index_model(_REPO_ROOT), _facts() if facts is None else facts
    )


def _footer_of(text: str) -> str:
    """The IC-14 footer block of *text* (marker to end of document)."""
    begin = doc_renderer.FOOTER_BEGIN_MARKER
    assert text.count(begin) == 1, "exactly one footer marker"
    return text[text.index(begin) :]


def _volatile_section_of(text: str) -> str:
    """The ``docs-volatile`` region of *text*: heading up to the end marker."""
    start = text.index(doc_renderer.VOLATILE_HEADING)
    end = text.index(doc_renderer.VOLATILE_END_MARKER, start) + len(
        doc_renderer.VOLATILE_END_MARKER
    )
    return text[start:end]


def _link_targets(text: str) -> list[str]:
    """Every ``- [title](path) — description`` target in *text*, in order."""
    return re.findall(
        r"^- \[[^\]]*\]\(([^)]+)\) — .*$", text, re.MULTILINE
    )


def _kind_headings(text: str) -> list[str]:
    """The per-kind ``## <kind>`` headings, excluding IC-10's ``## volatile``."""
    return [
        kind
        for kind in re.findall(r"^## (\S+)$", text, re.MULTILINE)
        if kind != "volatile"
    ]


def test_render_docs_index_signature_is_the_published_one():
    """IC-07 pins the parameter list; the result is a ``str``, not a path."""
    params = list(inspect.signature(doc_renderer.render_docs_index).parameters)
    assert params == ["index_model", "facts"], params

    empty = doc_renderer.render_docs_index({"root": "docs", "entries": []}, _facts())
    assert isinstance(empty, str)
    # An empty model is still a valid document — the writer must never be handed
    # a half-rendered string, and `sync_docs_consolidation` renders unconditionally.
    assert empty.startswith(doc_renderer.INDEX_TITLE)
    assert doc_renderer.FOOTER_END_MARKER in empty


def test_index_deterministic_and_archive_excluded(tmp_path: Path):
    """AC-17: byte-identical twice; archives out; no invented description.

    The fixture carries the three ways a page can be *deficient* at once — an
    ``archive/`` page, a page without frontmatter and a page without an ``# ``
    heading — because a renderer that degrades gracefully on the happy path can
    still be wrong on exactly those three.
    """
    root = _docs_root(tmp_path)
    _page(root, "specs/live.md", description="A real declared description.", title="Live")
    _page(root, "specs/archive/dead.md", description="must not be listed", title="Dead")
    _write_page(root, "guides/bare.md", "Just prose.\n")
    _page(root, "guides/no-heading.md", description="A declared description.")
    _write_page(
        root, "guides/archived.md", "---\ndescription: d\n---\n# Archived\n"
    )

    first = doc_renderer.render_docs_index(doc_index.build_index_model(root), _facts())
    second = doc_renderer.render_docs_index(doc_index.build_index_model(root), _facts())

    assert first == second, "two runs on one tree must be byte-identical"
    assert first.encode("utf-8") == second.encode("utf-8")

    links = _link_targets(first)
    assert links == [
        "guides/archived.md",
        "guides/bare.md",
        "guides/no-heading.md",
        "specs/live.md",
    ], links
    assert "specs/archive/dead.md" not in links
    assert "dead.md" not in first

    # The frontmatter-less page: file name as title, placeholder description,
    # and nothing invented out of the body text.
    assert "- [bare](guides/bare.md) — —" in first, first
    assert "Just prose" not in first
    # … and a page with a description but no ``# `` heading keeps the
    # description (its title then falls back to the file name, IC-09).
    assert "- [Page Title](guides/no-heading.md) — A declared description." in first
    # … and the index never lists itself, and never spells an absolute path.
    assert doc_index.DOCS_INDEX_FILENAME not in links
    assert str(tmp_path) not in first


def test_footer_has_no_timestamp():
    """AC-18: ``facts-hash`` + ``generator``, and no clock at all.

    The regex is applied to the **footer block**, not the whole document: page
    titles and descriptions are hand-written prose that may legitimately mention
    a date, and a whole-document scan would then be a test of the corpus rather
    than of the generator. What must be free of a date is the part the generator
    writes.
    """
    footer = _footer_of(_rendered())

    assert re.search(r"^facts-hash: [0-9a-f]{16}$", footer, re.MULTILINE), footer
    assert re.search(r"^generator: .+$", footer, re.MULTILINE), footer

    assert not re.search(r"\d{4}-\d{2}-\d{2}", footer), footer
    assert not re.search(r"\d{2}:\d{2}", footer), footer
    assert str(_REPO_ROOT) not in footer
    assert not any(token in footer for token in ("/home/", "/Users/", "C:\\")), footer

    # The marker pair is intact, and the footer is the last thing in the file.
    assert doc_renderer.FOOTER_END_MARKER in footer
    assert footer.rstrip().endswith(doc_renderer.FOOTER_END_MARKER), footer


def test_facts_hash_is_sha256_over_sorted_non_volatile_facts():
    """IC-14: the algorithm is the contract, so it is re-derived here.

    Re-deriving in the test is the only version of this assertion that survives
    a rewrite: a test that called the module's own helper would pass for any
    helper whatsoever.
    """
    import hashlib

    facts = _facts()
    text = _rendered(facts)
    found = re.search(r"^facts-hash: ([0-9a-f]{16})$", text, re.MULTILINE)
    assert found is not None, text

    stable = {
        name: value for name, value in facts.items() if name != "DOCS_SCENARIO_COUNT"
    }
    expected = hashlib.sha256(
        "\n".join(sorted(f"{name}={value}" for name, value in stable.items())).encode(
            "utf-8"
        )
    ).hexdigest()[:16]
    assert found.group(1) == expected, (found.group(1), expected)

    # Exactly 16 lowercase hex characters — no more, no less.
    assert len(found.group(1)) == doc_renderer.FACTS_HASH_CHARS == 16
    assert found.group(1) == found.group(1).lower()
    assert doc_renderer.compute_facts_hash(facts) == found.group(1)


def test_facts_hash_ignores_volatile_facts_but_shows_them():
    """AC-03: identical hash, and the differing value is in ``docs-volatile``.

    This is the R1/M7 anti-churn contract. The scenario count changes whenever
    Track A lands a scenario; if it entered the hash, every such landing would
    rewrite the footer for no semantic reason. The value is still rendered, so
    the review diff is one line in a section that says it is volatile.
    """
    first = _rendered(_facts(DOCS_SCENARIO_COUNT="63"))
    second = _rendered(_facts(DOCS_SCENARIO_COUNT="64"))

    hash_of = re.compile(r"^facts-hash: ([0-9a-f]{16})$", re.MULTILINE)
    assert hash_of.search(first).group(1) == hash_of.search(second).group(1), (
        "a volatile fact moved the facts-hash"
    )

    # Everything except the volatile row is byte-identical, so the diff of a
    # new scenario is exactly one line.
    differing = [
        (a, b)
        for a, b in zip(first.splitlines(), second.splitlines(), strict=True)
        if a != b
    ]
    assert len(differing) == 1, differing
    assert "63" in differing[0][0] and "64" in differing[0][1], differing

    # The differing value really is in the volatile section …
    volatile = _volatile_section_of(first)
    assert "| DOCS_SCENARIO_COUNT | 63 |" in volatile
    # … which is the **last** section before the footer (IC-10(e)) …
    assert first.index(doc_renderer.VOLATILE_HEADING) < first.index(
        doc_renderer.FOOTER_BEGIN_MARKER
    )
    assert not first[first.index(doc_renderer.FOOTER_BEGIN_MARKER) :].count(
        doc_renderer.VOLATILE_HEADING
    )
    # … and no non-volatile fact leaks into it.
    assert "DOCS_VERSION" not in volatile


def test_facts_hash_ignores_fact_dict_order():
    """AC-27 for the index: the same facts in any insertion order hash the same."""
    facts = _facts()
    orders = [
        list(facts),
        list(reversed(facts)),
        sorted(facts, key=len, reverse=True),
        sorted(facts),
    ]
    rendered = {
        doc_renderer.render_docs_index(
            doc_index.build_index_model(_REPO_ROOT), {key: facts[key] for key in order}
        )
        for order in orders
    }
    assert len(rendered) == 1, "fact dict order leaked into the rendered bytes"


def test_index_lists_every_page_exactly_once():
    """IC-10 (c): one link per page, the index itself never, archives never."""
    text = _rendered()
    model = doc_index.build_index_model(_REPO_ROOT)
    expected = sorted(
        entry["path"]
        for entry in model["entries"]
        if entry["path"] != doc_index.DOCS_INDEX_FILENAME
    )

    links = _link_targets(text)
    assert sorted(links) == expected
    assert len(links) == len(set(links)), "a page is linked twice"
    assert doc_index.DOCS_INDEX_FILENAME not in links
    assert not [
        link for link in links if doc_index.EXCLUDED_DIR_SEGMENTS.intersection(link.split("/"))
    ]

    # Every section the model knows is present, in KIND_ORDER, and each link
    # sits under the heading its own ``kind`` names.
    headings = re.findall(r"^## (?!volatile)(\S+)$", text, re.MULTILINE)
    assert headings == [kind for kind in doc_index.KIND_ORDER if kind in headings]
    for kind in headings:
        block = text.split(f"## {kind}\n", 1)[1].split("\n## ", 1)[0]
        for link in _link_targets(block):
            entry = next(e for e in model["entries"] if e["path"] == link)
            assert entry["kind"] == kind, (kind, link, entry["kind"])

    # A kind with no pages gets no heading at all — an empty section is noise.
    for kind in doc_index.KIND_ORDER:
        if kind not in {e["kind"] for e in model["entries"]}:
            assert f"## {kind}" not in text, kind


def test_empty_kind_gets_no_section(tmp_path: Path):
    """Adding the first page of a kind is the only thing that may add a heading."""
    root = _docs_root(tmp_path)
    _page(root, "guides/one.md", description="d", title="One")
    before = doc_renderer.render_docs_index(doc_index.build_index_model(root), _facts())
    assert "## spikes" not in before
    # Exactly one kind heading (`## guides`); `## volatile` is the IC-10(e)
    # section and is counted separately.
    assert _kind_headings(before) == ["guides"], _kind_headings(before)

    _page(root, "spikes/one.md", description="d", title="Spike")
    after = doc_renderer.render_docs_index(doc_index.build_index_model(root), _facts())
    assert _kind_headings(after) == ["guides", "spikes"], _kind_headings(after)


def test_rendered_index_is_deterministic_on_the_real_tree(
    tmp_path: Path, monkeypatch
):
    """NFA-01 on the real corpus, including a genuinely **relative** root.

    The root-spelling half used to be untestable as written: ``_REPO_ROOT`` is
    already absolute (``Path(__file__).resolve()``), so comparing it with
    ``_REPO_ROOT.resolve()`` compared a path with itself and the assertion could
    not fail no matter what the renderer did. The claim is now made falsifiable
    the only way it can be — by *actually* chdir-ing somewhere else and handing
    ``build_index_model`` a relative path, so a root that leaked into the output
    would show up as a differing document.
    """
    first = _rendered()
    second = _rendered()

    assert first == second
    assert first.encode("utf-8") == second.encode("utf-8")

    # The checkout location is not an input. Asserted twice: over the model's
    # produced *entries* (its actual product) and then over the rendered
    # document. The two roots are a genuinely absolute one and a genuinely
    # relative one, and they must agree.
    absolute_model = doc_index.build_index_model(_REPO_ROOT.resolve())

    monkeypatch.chdir(tmp_path)
    relative_root = Path(os.path.relpath(_REPO_ROOT.resolve(), os.getcwd()))
    assert not relative_root.is_absolute(), relative_root
    assert str(relative_root) != str(_REPO_ROOT)
    assert relative_root.resolve() == _REPO_ROOT, "the relative root must be the real tree"
    relative_model = doc_index.build_index_model(relative_root)

    assert absolute_model["entries"], "the real corpus must be non-empty, else this is vacuous"
    assert relative_model["entries"] == absolute_model["entries"]
    assert relative_model["root"] == absolute_model["root"] == doc_index.DOCS_RELPATH

    via_relative = doc_renderer.render_docs_index(relative_model, _facts())
    assert via_relative == first, (
        "the rendered document must not depend on the spelling of the root"
    )

    # … and a changed fact is: the document is a function of the facts, not a
    # constant string with a hash bolted on.
    changed = _rendered(_facts(DOCS_VERSION="9.9.9"))
    assert changed != first
    assert re.search(r"^facts-hash: ([0-9a-f]{16})$", changed, re.MULTILINE).group(
        1
    ) != re.search(r"^facts-hash: ([0-9a-f]{16})$", first, re.MULTILINE).group(1)


def test_rendered_index_carries_the_generator_id(tmp_path: Path):
    """The ownership anchor must survive the move into the IC-14 footer.

    ``_carries_generator_id`` is a substring probe over the whole document, so
    this is not cosmetic: if the id ever stopped being rendered, every later run
    would classify its own index as a foreign file and report it as ``skipped``
    — permanently, invisibly, with a green sync log. The negative control at the
    end proves the probe is not vacuously true for *any* text.
    """
    text = _rendered()

    assert doc_renderer.DOCS_GENERATOR_ID in text
    assert doc_renderer.DOCS_GENERATOR_ID in _footer_of(text)
    assert doc_renderer._carries_generator_id(text) is True
    assert doc_renderer._carries_generator_id("") is False

    # And the whole loop still works end to end: create, then update in place.
    root = _docs_root(tmp_path)
    _page(root, "specs/one.md", description="First spec page.")
    agent_meta_root = tmp_path / "am-root"
    config = _ENABLED_CONFIG
    log = SyncLog()
    plan = doc_renderer.sync_docs_consolidation(
        agent_meta_root, root, config, {}, log, dry_run=False
    )
    assert plan["written"] == [doc_index.DOCS_INDEX_RELPATH], plan
    target = root / doc_index.DOCS_INDEX_RELPATH
    written = target.read_text(encoding="utf-8")
    assert doc_renderer._carries_generator_id(written) is True

    # The written bytes are exactly what the pure renderer produces for the same
    # inputs — the writer has no second rendering path, so "what would be
    # written" and "what was written" cannot diverge.
    from scripts.lib.doc_facts import compute_doc_facts

    facts = compute_doc_facts(agent_meta_root, config, provider_config={}, log=log)
    assert written == doc_renderer.render_docs_index(
        doc_index.build_index_model(root), facts
    )

    _page(root, "specs/two.md", description="Second spec page.")
    plan = doc_renderer.sync_docs_consolidation(
        agent_meta_root, root, config, {}, log, dry_run=False
    )
    assert plan["written"] == [doc_index.DOCS_INDEX_RELPATH], plan
    assert doc_renderer._carries_generator_id(target.read_text(encoding="utf-8")) is True


def test_index_survives_a_facts_dict_without_any_key():
    """A missing fact degrades to a placeholder, it does not raise or blank out."""
    text = doc_renderer.render_docs_index(doc_index.build_index_model(_REPO_ROOT), {})

    assert text.startswith(doc_renderer.INDEX_TITLE)
    assert doc_renderer.FOOTER_BEGIN_MARKER in text
    assert re.search(r"^facts-hash: [0-9a-f]{16}$", text, re.MULTILINE)
    # The empty-fact placeholder is visible in review rather than a blank row.
    assert doc_renderer.EMPTY_MARKER_TEMPLATE.format(name="DOCS_REPO_FACTS_BLOCK") in text
    # No unrendered placeholder leaked, and no ``None`` from a missing key.
    assert "{{" not in text
    assert "None" not in text


def test_index_footer_generator_id_is_not_duplicated():
    """The id is rendered from :data:`DOCS_GENERATOR_ID`, not from a second literal.

    A second ``"doc-indexer/1"`` literal would let the footer and the ownership
    probe drift apart: the probe looks for the constant, the footer would print
    the copy, and bumping the constant would quietly freeze every index in the
    repository — with a green log, because a freeze looks exactly like success.
    The AST scan is what makes the copy visible *before* that happens; the
    negative control proves the scan is not vacuous.
    """
    tree = ast.parse(_MODULE_PATH.read_text(encoding="utf-8"))
    literals = _literal_strings(tree)
    offenders = [
        value
        for value in literals
        if doc_renderer.DOCS_GENERATOR_ID in value
        and value != doc_renderer.DOCS_GENERATOR_ID
    ]
    assert offenders == [], offenders
    assert literals.count(doc_renderer.DOCS_GENERATOR_ID) == 1, (
        "the id must be spelled exactly once, in the constant"
    )

    injected = ast.parse(f'OTHER = "prefix {doc_renderer.DOCS_GENERATOR_ID} suffix"\n')
    assert [
        value
        for value in _literal_strings(injected)
        if doc_renderer.DOCS_GENERATOR_ID in value
        and value != doc_renderer.DOCS_GENERATOR_ID
    ], "the scan must see a duplicated id"


def test_index_path_is_not_spelled_as_a_literal():
    """F-B: the target path is derived, never spelled — at the **literal** level.

    W3-1's pin scanned the raw source text, which fails twice over: it fires on
    a mere mention in a docstring (prose about the document is not a second copy
    of the truth, and this module's docstrings must be able to name the file they
    produce), and it misses drift assembled at runtime as
    ``"docs" + "/" + "INDEX.md"``. An AST probe sees only a string *literal*, so
    the false positive is gone; the composition check in
    :func:`test_docs_index_relpath_is_composed_not_duplicated` covers the second
    half, and the negative control below proves the probe is not vacuous.

    Docstrings are excluded explicitly, because a docstring *is* an
    ``ast.Constant``. Leaving them in would reintroduce the very false positive
    this test exists to remove — and it would do so silently, since the only way
    to find out would be to try writing prose about the document.
    """
    tree = ast.parse(_MODULE_PATH.read_text(encoding="utf-8"))
    literals = _literal_strings(tree)
    offenders = [value for value in literals if "docs/INDEX" in value]
    assert offenders == [], offenders

    injected = ast.parse('RELPATH = "docs" + "/" + "INDEX.md"\n')
    assert [
        value for value in _literal_strings(injected) if "docs/INDEX" in value
    ], "the probe must see a spelled path"

    # … and it must NOT fire on prose: a docstring naming the file is fine.
    prose = ast.parse('"""We generate docs/INDEX.md."""\n')
    assert not [value for value in _literal_strings(prose) if "docs/INDEX" in value]


def test_module_level_write_free_guard_is_inverted():
    """F-A: every module-level function is write-free except the writer set.

    W3-1's guard listed three function *names* to check write-free. Everything
    else in the module was unchecked, and the closed review proved the hole is
    live: a ``write_text`` injected into ``_carries_generator_id`` passed, and
    the same injection in a future ``render_docs_index`` would have passed too —
    which is exactly the surface W3-2 adds. The guard is therefore inverted: the
    default is write-free and the writer is an explicit, asserted exception.

    The differential at the end is **comparative, not decorative**. It runs the
    shared predicate :func:`_leaks_disk` — the same code that judged the real
    module above — against the W3-1 allowlist *and* against
    :data:`doc_renderer.WRITER_FUNCTIONS`, over one injected sample containing
    one function of each kind, so the two shapes genuinely disagree. The previous
    version ran one predicate over two names that were in neither set: both sides
    returned the same list by construction, which is why its "the old allowlist
    missed it" assertion could never fail. The sample is built so that:

    * ``apply_fact_blocks`` is a name the **old** allowlist listed — the old
      guard caught it, so the inverted guard must catch it too. This is the
      discriminating case: it is what fails if the inversion ever became
      *weaker* than the allowlist it replaced.
    * ``_carries_generator_id`` is a name the old allowlist never listed — the
      F-A hole — so the old guard missed it and the inverted guard must catch it.
    * ``render_docs_index`` writes nothing, so neither shape may flag it: the
      negative control that keeps "flags everything" from passing as a guard.

    An ``async def`` writing to disk is asserted to be *inside* the guard's input
    rather than merely absent from it (:data:`_FUNCTION_NODES`) — the same blind
    spot one class down.
    """
    forbidden = {
        "open",
        "write_text",
        "write_bytes",
        "mkdir",
        "remove",
        "unlink",
        "rmtree",
        "rename",
        "replace",
        "touch",
    }
    tree = ast.parse(_MODULE_PATH.read_text(encoding="utf-8"))
    functions = _functions_by_name(tree)

    assert doc_renderer.WRITER_FUNCTIONS <= set(functions), (
        "the declared writer set must name real functions"
    )
    assert doc_renderer.WRITER_FUNCTIONS == frozenset({"sync_docs_consolidation"}), (
        "a new writer is a deliberate, visible change — not a default"
    )

    offenders = _write_free_offenders(functions, doc_renderer.WRITER_FUNCTIONS, forbidden)
    assert offenders == {}, offenders

    # The guard's *input* must include `async def`. `ast.AsyncFunctionDef` is a
    # sibling of `ast.FunctionDef`, not a subclass, so an enumeration naming only
    # the sync class is blind to an async writer rather than reporting it — the
    # invisible failure mode. The sample below therefore has to be findable AND
    # have to be a real writer, or the assertion would pass for the wrong reason.
    async_tree = ast.parse(
        "async def _hidden_async_writer():\n    Path('y').write_text('z')\n"
    )
    async_functions = _functions_by_name(async_tree)
    assert "_hidden_async_writer" in async_functions, (
        "an async def must be inside the guard's input, not merely absent from it"
    )
    assert _write_free_offenders(async_functions, set(), forbidden) == {
        "_hidden_async_writer": ["write_text"]
    }

    # The writer itself may read, but every mutation funnels through
    # write_checked — one path, so idempotency and the secret scan cannot drift.
    writer_calls = _called_names(functions["sync_docs_consolidation"])
    assert "write_checked" in writer_calls
    assert not (writer_calls & (forbidden - {"open"}))
    assert "open" in writer_calls, "the writer must still be allowed to read its target"

    # Negative control on the guard's own logic, and a **differential**: one
    # injected sample, run through the shared predicate under both guard shapes.
    injected = ast.parse(
        # a name the old allowlist DID list -> the old guard caught it
        "def apply_fact_blocks(text):\n"
        "    Path('y').write_text(text)\n"
        # a name the old allowlist never listed -> the old guard missed it
        "def _carries_generator_id(text):\n"
        "    return Path('y').write_text('z') or ('x' in text)\n"
        # pure -> neither shape may flag it
        "def render_docs_index(model, facts):\n"
        "    return model\n"
    )
    injected_functions = _functions_by_name(injected)
    injected_leaks = _leaks_disk(injected_functions, forbidden)
    assert sorted(injected_leaks) == ["_carries_generator_id", "apply_fact_blocks"], (
        "the shared predicate must see both writers and nothing else"
    )

    # W3-1's guard, kept as the literal it was: a hard-coded list of the function
    # names that were checked write-free, everything else unchecked. A literal
    # rather than an import -- the point is to pin the shape the inversion
    # replaced, and an import would track whatever the module happens to do now.
    old_allowlist = frozenset(
        {"apply_fact_blocks", "render_doc_fact_block", "is_valid_region"}
    )
    old_caught = sorted(set(injected_leaks) & old_allowlist)
    old_missed = sorted(set(injected_leaks) - old_allowlist)
    new_caught = sorted(
        _write_free_offenders(
            injected_functions, doc_renderer.WRITER_FUNCTIONS, forbidden
        )
    )

    assert old_caught == ["apply_fact_blocks"], (
        "the old allowlist checked this name, so it must have caught it"
    )
    assert old_missed == ["_carries_generator_id"], (
        "the old allowlist must demonstrably have missed this -- the F-A hole"
    )
    assert new_caught == ["_carries_generator_id", "apply_fact_blocks"], (
        "the inverted guard must catch both what the allowlist checked and what "
        "it never looked at"
    )
    assert set(old_caught) < set(new_caught), (old_caught, new_caught)
    assert "render_docs_index" not in new_caught, (
        "a pure function must not be reported -- otherwise the guard flags "
        "everything and means nothing"
    )


def test_render_docs_index_is_pure(tmp_path: Path):
    """The renderer half of the inverted guard, asserted on its own function.

    The call-set allowlist is deliberately **not** exhaustive: a new pure helper
    (``str.split``, ``re.sub``) is covered by default under F-A's inverted guard,
    and pinning an exact list here would re-introduce the same brittleness one
    level down. What must hold is that the function reaches no filesystem and no
    clock — the properties the document's determinism rests on.
    """
    called = _called_names(_function_node("render_docs_index"))
    forbidden = {
        "open",
        "write_text",
        "write_bytes",
        "mkdir",
        "unlink",
        "rmtree",
        "rename",
        "replace",
        "touch",
        "read_text",
        "read_bytes",
        "rglob",
        "glob",
        "iterdir",
        "exists",
        "stat",
        "now",
        "today",
        "getmtime",
        "getuser",
        "expanduser",
        "getcwd",
    }
    assert not (called & forbidden), sorted(called & forbidden)

    # Behavioural half: rendering the same model twice, with the tree under a
    # different path spelling, yields the same bytes — no path, no clock.
    root = _docs_root(tmp_path)
    _page(root, "specs/one.md", description="d", title="One")
    model = doc_index.build_index_model(root)
    assert doc_renderer.render_docs_index(model, _facts()) == doc_renderer.render_docs_index(
        model, _facts()
    )


# W3-3 — Scaffold-Guard und Besitzregel (IC-15, IC-13, AC-21, F20)
# ----------------------------------------------------------------
#
# The scaffold writes the ``file-index`` fallback (``docs/INDEX.md``) and this
# writer writes the same path. B2 is a **double writer**, resolved from both
# sides: :func:`is_file_index_skeleton` recognises the skeleton by the one text
# line F20 pins, and this writer consults it **before** the ownership probe.
#
# Two invariants, and only two:
#
# * **Order matters — the mode gate before the ownership block.** A
#   knowledge-engine project then reports its own authoritative-mode note; the
#   other way round, the ownership step's early returns would answer first with
#   a foreign-writer or ``unchanged`` verdict. The order of the two checks
#   *inside* the ownership block does not matter: they are a union of write
#   permissions, and either order reaches the same outcome.
#   :func:`test_scaffold_skeleton_is_owned_and_replaced_under_full_mode` pins the
#   first by its observable consequence: a skeleton becomes an ``UPDATE``, and
#   the note names the scaffold rather than a foreign writer.
# * **The generator never writes a skeleton** — a property of the rendered
#   bytes, not of a branch: the full index is not a skeleton and does not carry
#   the F20 marker. That keeps the reverse of the ownership rule true by
#   construction, so no code path can hand the scaffold's own file back to it.


_KE_AUTHORITATIVE_CONFIG: dict = {
    "docs-consolidation": {"enabled": True},
    "knowledge-engine": {"enabled": True},
}

_SKELETON_MODE_CONFIG: dict = {
    "docs-consolidation": {"enabled": True, "index-mode": "skeleton"},
}

#: The *other* index vocabulary: ``spec-plan-workflow.index.mode`` with its third
#: value ``off``, next to a knowledge engine that is on. See
#: :func:`test_index_mode_off_permits_the_full_index`.
_INDEX_MODE_OFF_CONFIG: dict = {
    "docs-consolidation": {"enabled": True},
    "knowledge-engine": {"enabled": True},
    "spec-plan-workflow": {"enabled": True, "index": {"mode": "off"}},
}


def _scaffold_skeleton() -> str:
    """The scaffold's own bytes, read from the module that writes them.

    Not a copy: a literal here would be a second skeleton that can drift from
    the one the scaffold really writes, and the guard's whole job is to
    recognise *that* file (F20).
    """
    return spec_plan_scaffold._FILE_INDEX_SKELETON


def _scaffolded_root(tmp_path: Path) -> Path:
    """A project root whose ``docs/INDEX.md`` is the real scaffold skeleton.

    Built by calling ``scaffold_spec_plan_dirs`` itself rather than by writing
    the skeleton literal. ``knowledge-engine.enabled: false`` is what makes
    ``resolve_index_mode()`` fall through to ``file-index`` and the scaffold
    write the fallback at all.
    """
    root = _docs_root(tmp_path)
    config = {
        "spec-plan-workflow": {"enabled": True},
        "knowledge-engine": {"enabled": False},
    }
    spec_plan_scaffold.scaffold_spec_plan_dirs(
        _REPO_ROOT, root, config, SyncLog(), dry_run=False
    )
    return root


def test_scaffold_guard_recognises_only_the_skeleton():
    """IC-15/F20: the guard is a marker probe, and it is not vacuous."""
    assert spec_plan_scaffold._FILE_INDEX_SKELETON_MARKER == "File-based index fallback"
    assert spec_plan_scaffold.is_file_index_skeleton(_scaffold_skeleton()) is True
    assert spec_plan_scaffold.is_file_index_skeleton("") is False
    assert spec_plan_scaffold.is_file_index_skeleton("# Index\n\nHand-written.\n") is False
    # A rendered full index is not a skeleton either, or the ownership rule
    # would become self-referential.
    assert spec_plan_scaffold.is_file_index_skeleton(_rendered()) is False


def test_skeleton_marker_is_line_break_tolerant():
    """IC-15's "Zeilen-Brk ein-aus": a trailing line break is not the answer.

    The guard asks a question about a *file*, not about a line, so whether the
    content ends with a newline cannot change the verdict — and F20's "prefix
    detection" means a maintainer's own additions under the scaffold's heading
    keep the stamp, which is the *permissive* direction: such a file still counts
    as the scaffold's and may be replaced. See
    :func:`spec_plan_scaffold.is_file_index_skeleton` for the full radius.
    """
    skeleton = _scaffold_skeleton()
    assert skeleton.endswith("\n")
    assert spec_plan_scaffold.is_file_index_skeleton(skeleton) is True
    assert spec_plan_scaffold.is_file_index_skeleton(skeleton.rstrip("\n")) is True

    extended = skeleton + "\nHand-maintained additions below.\n"
    assert spec_plan_scaffold.is_file_index_skeleton(extended) is True


def test_skeleton_mode_preserves_scaffold(tmp_path: Path):
    """AC-21: ``index-mode: skeleton`` leaves the scaffold skeleton untouched.

    "Always untouched" is asserted as a byte-comparison of the whole tree before
    and after, not as "the right note was logged": a writer that logs the right
    reason and still rewrites the file passes a log-only assertion.
    """
    root = _scaffolded_root(tmp_path)
    _page(root, "specs/one.md", description="First spec page.")
    target = root / doc_index.DOCS_INDEX_RELPATH
    before_text = target.read_text(encoding="utf-8")
    assert spec_plan_scaffold.is_file_index_skeleton(before_text) is True
    before = _tree_snapshot(root)

    plan, log = _run_sync(root, _SKELETON_MODE_CONFIG)

    assert _tree_snapshot(root) == before, "index-mode: skeleton must write nothing"
    assert target.read_text(encoding="utf-8") == before_text
    assert spec_plan_scaffold.is_file_index_skeleton(
        target.read_text(encoding="utf-8")
    ) is True
    assert plan == {
        "written": [],
        "unchanged": [],
        "skipped": [doc_index.DOCS_INDEX_RELPATH],
    }, plan
    assert len(log.infos) == 1, log.infos
    assert doc_renderer.SKELETON_MODE_REASON in log.infos[0]
    assert log.actions == []


def test_skeleton_mode_creates_no_index_at_all(tmp_path: Path):
    """``skeleton`` mode is the scaffold's file to have, so the writer creates none.

    The mode is only meaningful if the generator stays out of the way entirely;
    a mode that merely blocked the *replacement* would still let a first run
    seed a full index into a project that asked for a skeleton.
    """
    root = _docs_root(tmp_path)
    _page(root, "specs/one.md", description="First spec page.")
    before = _tree_snapshot(root)

    plan, log = _run_sync(root, _SKELETON_MODE_CONFIG)

    assert _tree_snapshot(root) == before
    assert not (root / doc_index.DOCS_INDEX_RELPATH).exists()
    assert plan == {
        "written": [],
        "unchanged": [],
        "skipped": [doc_index.DOCS_INDEX_RELPATH],
    }, plan
    assert doc_renderer.SKELETON_MODE_REASON in log.infos[0]
    assert log.actions == []


def test_ke_authoritative_writes_no_index(tmp_path: Path):
    """AC-21 / IC-13 / scenario 52: the KE index is authoritative, so is nothing.

    The starting state is the scaffold's own file-index skeleton, so the two
    gates genuinely compete: the ownership probe would report it as a foreign
    file and log ``OWNERSHIP_REASON``. The knowledge-engine reason must be the
    one that lands, which is only reachable if the mode gate is consulted first.
    """
    root = _scaffolded_root(tmp_path)
    _page(root, "specs/one.md", description="First spec page.")
    target = root / doc_index.DOCS_INDEX_RELPATH
    before_text = target.read_text(encoding="utf-8")
    before = _tree_snapshot(root)

    assert (
        spec_plan_scaffold.resolve_index_mode(_KE_AUTHORITATIVE_CONFIG)[0]
        == "knowledge-engine"
    ), "the fixture must actually be knowledge-engine authoritative"

    plan, log = _run_sync(root, _KE_AUTHORITATIVE_CONFIG)

    assert _tree_snapshot(root) == before, "KE authoritative writes nothing"
    assert target.read_text(encoding="utf-8") == before_text
    assert plan == {
        "written": [],
        "unchanged": [],
        "skipped": [doc_index.DOCS_INDEX_RELPATH],
    }, plan
    assert len(log.infos) == 1, log.infos
    assert doc_renderer.KE_AUTHORITATIVE_REASON in log.infos[0]
    assert doc_renderer.OWNERSHIP_REASON not in log.infos[0], (
        "the wrong gate won: the ownership probe ran before the mode gate"
    )
    assert log.actions == []


def test_ke_authoritative_writes_no_index_even_when_absent(tmp_path: Path):
    """The KE gate is a mode decision, not a reaction to an existing file.

    Scenario 52 asserts ``[ ! -e docs/INDEX.md ]`` on a tree where the scaffold
    never wrote one, so the absent case needs its own unit test: a gate that
    only fired on an existing file would pass the ownership test above and still
    seed an index into a knowledge-engine project.
    """
    root = _docs_root(tmp_path)
    _page(root, "specs/one.md", description="First spec page.")
    before = _tree_snapshot(root)

    plan, log = _run_sync(root, _KE_AUTHORITATIVE_CONFIG)

    assert _tree_snapshot(root) == before
    assert not (root / doc_index.DOCS_INDEX_RELPATH).exists()
    assert plan == {
        "written": [],
        "unchanged": [],
        "skipped": [doc_index.DOCS_INDEX_RELPATH],
    }, plan
    assert doc_renderer.KE_AUTHORITATIVE_REASON in log.infos[0]
    assert log.actions == []


def test_scaffold_skeleton_is_owned_and_replaced_under_full_mode(tmp_path: Path):
    """IC-15: under ``index-mode: full`` the skeleton may be replaced — once.

    This is the positive half of the guard and the proof of its *order*: the
    skeleton carries no ``doc-indexer/1``, so it can only be written if
    ``is_file_index_skeleton()`` is consulted before the ownership probe. The
    "once" is asserted by a second run, not by a comment.

    W3-6 owns the end-to-end variant of this (``test_skeleton_replaced_once``)
    against the real tracked ``docs/INDEX.md``; this is the unit-level guard.
    """
    root = _scaffolded_root(tmp_path)
    _page(root, "specs/one.md", description="First spec page.")
    target = root / doc_index.DOCS_INDEX_RELPATH
    assert spec_plan_scaffold.is_file_index_skeleton(
        target.read_text(encoding="utf-8")
    ) is True

    plan, log = _run_sync(root, _ENABLED_CONFIG)

    assert plan == {
        "written": [doc_index.DOCS_INDEX_RELPATH],
        "unchanged": [],
        "skipped": [],
    }, plan
    assert len(log.actions) == 1 and "UPDATE" in log.actions[0], log.actions
    written = target.read_text(encoding="utf-8")
    assert doc_renderer._carries_generator_id(written) is True
    assert spec_plan_scaffold.is_file_index_skeleton(written) is False, (
        "the generator must never write a skeleton"
    )
    assert doc_renderer.SCAFFOLD_SKELETON_REASON in log.infos[0], log.infos
    assert doc_renderer.OWNERSHIP_REASON not in log.infos[0]

    before = _tree_snapshot(root)
    second, second_log = _run_sync(root, _ENABLED_CONFIG)
    assert second == {
        "written": [],
        "unchanged": [doc_index.DOCS_INDEX_RELPATH],
        "skipped": [],
    }, second
    assert _tree_snapshot(root) == before
    assert second_log.actions == []


def test_unknown_index_mode_is_fail_closed(tmp_path: Path):
    """A typo in ``index-mode`` writes nothing, and says which one it thought it saw.

    The schema closes the enum, so this is the typo path rather than a supported
    value. Treating an unrecognised mode as ``full`` would be fail-*open* on the
    one switch that decides whether another module's file may be overwritten.
    """
    root = _scaffolded_root(tmp_path)
    _page(root, "specs/one.md", description="First spec page.")
    before = _tree_snapshot(root)
    config = {"docs-consolidation": {"enabled": True, "index-mode": "ful"}}

    plan, log = _run_sync(root, config)

    assert _tree_snapshot(root) == before
    assert plan["skipped"] == [doc_index.DOCS_INDEX_RELPATH], plan
    assert doc_renderer.UNKNOWN_INDEX_MODE_REASON in log.infos[0]
    assert log.actions == []


def test_index_mode_off_permits_the_full_index(tmp_path: Path):
    """``index.mode: off`` is not a blocking owner — pinned as a value, not prose.

    Two vocabularies meet in :func:`doc_renderer._index_mode_block_reason`:
    ``spec-plan-workflow.index.mode`` (``knowledge-engine``/``file-index``/
    ``off``) and ``docs-consolidation.index-mode`` (``full``/``skeleton``).
    ``off`` is :func:`resolve_index_mode`'s way of saying the *scaffold* writes
    no fallback index, so it claims no file on this path: a project that switched
    it off has no placeholder to protect, and the full index may own
    ``docs/INDEX.md``. Observed and asserted, both halves:

    * a fresh tree gets its index created, and
    * a *leftover* skeleton is still replaced — that is the scaffold-ownership
      step, not a mode gate.

    Whether ``off`` ought to protect the second case is a spec question (IC-13
    does not name the value), so it is pinned here: any change to it has to come
    through this test instead of arriving unnoticed.
    """
    rel = doc_index.DOCS_INDEX_RELPATH
    assert spec_plan_scaffold.resolve_index_mode(_INDEX_MODE_OFF_CONFIG)[0] == "off"
    assert doc_renderer._index_mode_block_reason(_INDEX_MODE_OFF_CONFIG) is None

    root = _docs_root(tmp_path)
    _page(root, "specs/one.md", description="First spec page.")

    plan, log = _run_sync(root, _INDEX_MODE_OFF_CONFIG)

    assert (root / rel).exists(), "off does not suppress the write"
    assert plan == {"written": [rel], "unchanged": [], "skipped": []}, plan
    assert len(log.actions) == 1 and "CREATE" in log.actions[0], log.actions

    leftover_dir = tmp_path / "leftover"
    leftover_dir.mkdir()
    leftover = _scaffolded_root(leftover_dir)
    _page(leftover, "specs/one.md", description="First spec page.")

    plan, log = _run_sync(leftover, _INDEX_MODE_OFF_CONFIG)

    assert plan == {"written": [rel], "unchanged": [], "skipped": []}, plan
    assert doc_renderer.SCAFFOLD_SKELETON_REASON in log.infos[0], log.infos


def test_skeleton_guard_does_not_generalise_to_a_near_miss(tmp_path: Path):
    """The guard is one case of the ownership rule, not a replacement for it.

    A hand-written index carries neither the generator id nor the F20 marker, so
    a guard that answered "not a skeleton" into an unconditional write would pass
    both new tests above and destroy the file. W3-1's version of this test stays
    in place; this one adds the *near miss* — the ``# INDEX`` heading present,
    the marker absent — which is what a prefix check written by eye would catch.
    """
    root = _docs_root(tmp_path)
    _page(root, "specs/one.md", description="First spec page.")
    near_miss = "# INDEX\n\n> Hand-written index, kept by a maintainer.\n"
    target = root / doc_index.DOCS_INDEX_RELPATH
    target.write_text(near_miss, encoding="utf-8")
    assert spec_plan_scaffold.is_file_index_skeleton(near_miss) is False

    plan, log = _run_sync(root, _ENABLED_CONFIG)

    assert target.read_text(encoding="utf-8") == near_miss
    assert plan == {
        "written": [],
        "unchanged": [],
        "skipped": [doc_index.DOCS_INDEX_RELPATH],
    }, plan
    assert doc_renderer.OWNERSHIP_REASON in log.infos[0]
    assert log.actions == []


def test_generator_never_writes_a_skeleton():
    """The reverse of the ownership rule, asserted on the render itself (IC-15)."""
    rendered = _rendered()
    assert spec_plan_scaffold.is_file_index_skeleton(rendered) is False
    assert spec_plan_scaffold._FILE_INDEX_SKELETON_MARKER not in rendered


def test_writer_decision_follows_the_scaffolds_marker(tmp_path: Path, monkeypatch):
    """Perturb the scaffold's marker and the writer's *decision* must move (F20).

    Behavioural, not identity: what makes importing the scaffold's guard worth
    having is that a change to the marker it keys on *reaches* this writer.
    ``monkeypatch`` rewrites that one module global — the very line such a change
    would touch — while the bytes on disk stay the scaffold's own skeleton, so
    the verdict can only move if the writer asks the scaffold about the file. A
    probe copied into :mod:`doc_renderer` would keep writing the file and this
    test would fail, which is the drift it exists to catch.
    """
    rel = doc_index.DOCS_INDEX_RELPATH

    root = _scaffolded_root(tmp_path)
    _page(root, "specs/one.md", description="First spec page.")

    before, before_log = _run_sync(root, _ENABLED_CONFIG)

    assert before == {"written": [rel], "unchanged": [], "skipped": []}, before
    assert doc_renderer.SCAFFOLD_SKELETON_REASON in before_log.infos[0], (
        before_log.infos
    )

    # A second tree carrying byte-identical skeleton bytes, reached with the
    # marker moved: the on-disk file is the variable-free half of the comparison.
    moved_dir = tmp_path / "marker-moved"
    moved_dir.mkdir()
    moved = _scaffolded_root(moved_dir)
    _page(moved, "specs/one.md", description="First spec page.")
    target = moved / rel
    assert target.read_text(encoding="utf-8") == _scaffold_skeleton()
    monkeypatch.setattr(
        spec_plan_scaffold, "_FILE_INDEX_SKELETON_MARKER", "no such marker here"
    )

    after, after_log = _run_sync(moved, _ENABLED_CONFIG)

    assert target.read_text(encoding="utf-8") == _scaffold_skeleton(), "wrote anyway"
    assert after == {"written": [], "unchanged": [], "skipped": [rel]}, after
    assert doc_renderer.OWNERSHIP_REASON in after_log.infos[0], after_log.infos
    assert after_log.actions == []


def test_skeleton_guard_probe_is_write_free():
    """The guard is a pure string probe inside a module that writes elsewhere.

    :mod:`doc_renderer`'s inverted write-free guard cannot cover a function this
    module now depends on but does not own, so it is pinned here by name: the
    function takes text, returns a bool and reaches no disk. Reusing the shared
    :func:`_called_names` predicate keeps this a third *use*, not a third copy.
    """
    tree = ast.parse(Path(spec_plan_scaffold.__file__).read_text(encoding="utf-8"))
    node = next(
        item
        for item in tree.body
        if isinstance(item, ast.FunctionDef) and item.name == "is_file_index_skeleton"
    )
    forbidden = {
        "open",
        "write_text",
        "write_bytes",
        "mkdir",
        "unlink",
        "rmtree",
        "rename",
        "replace",
        "touch",
        "read_text",
        "read_bytes",
    }
    called = _called_names(node)
    assert not (called & forbidden), sorted(called & forbidden)
    assert isinstance(spec_plan_scaffold.is_file_index_skeleton(""), bool)
