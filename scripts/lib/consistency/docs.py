"""Documentation and UI cross-reference consistency checks — **facade**.

Since W2-0 this module holds **no** check logic. It is the re-export contract
that the runner (``scripts/consistency-check.py:53-63``, calls at ``:283-284``
for the two ungated alt checks and ``:292-294`` for the gated V1…V7 block) and
the test suite (``tests/test_doc_facts.py``) import, so the cut behind it
stays invisible to every existing caller (K19).

The checks live in two family modules, split by *the question a check asks*
(Spec §4.1, K18):

* :mod:`scripts.lib.consistency.docs_links` — "is every reference
  resolvable?" (V3, V4, the pre-W2 alt checks)
* :mod:`scripts.lib.consistency.docs_freshness` — "does the documentation
  match the computed actual state?" (V1a/V1b today; V5, V6 land in W2-4/W2-5)

The split is behaviour-neutral: every name below is the *same object* the
pre-split module exported, so ``docs.<name>`` keeps resolving to the same
function, constant and enum member it did before. ``__all__`` is the contract
fixed in Spec §4.1. Its ``__all__`` increments have a **single** owner: plan
**W2-7** (``Files:``) is the one task that appends the names of the checks the
later waves implement. W2-3, W2-4, W2-5, W2-6, W6-2 and W8-4 must **not** list
this module in their ``Files:`` — W2-3/W2-5/W2-6 run in **PG-2a**, and a
``docs.py`` write-set there is exactly the ownership collision K20 removed.
"""

from __future__ import annotations

from .docs_freshness import (
    V1_CHECK_ID,
    V1_EXEMPT_MARKER,
    V1_GENERATED_RELPATHS,
    V1_MAX_TOKEN_GAP,
    V1_REGION_BEGIN,
    V1_REGION_END,
    V1_SCAN_RELPATHS,
    V1_SUGGESTION,
    V6_CHECK_ID,
    Span,
    check_docs_facts_fresh,
    check_no_manual_counts,
    v1_strict,
    v1a_count_spans,
    v1b_version_spans,
)
from .docs_freshness_v5 import V5_CHECK_ID, check_role_generation_parity
from .docs_index import V2_CHECK_ID, check_docs_index_completeness
from .docs_links import (
    V3_CHECK_ID,
    V3_DOC_SUFFIXES,
    V3_DOCS_RELDIR,
    V3_ENTRY_RELPATHS,
    V3_INERT_PREFIXES,
    V3_SUGGESTION,
    check_internal_links,
    check_readme_docs_index,
    check_sync_cli_docs,
    check_ui_help_mappings,
)
from .docs_wiki import V7_CHECK_ID, check_wiki_staleness
from .report import Finding, Severity

__all__ = [  # noqa: RUF022 — the order below IS the Spec §4.1 contract, not a
    # sort order: it groups the names by the module that owns them and keeps the
    # W2-3…W8-4 section visibly empty until those tasks land. An isort-style
    # sort would destroy exactly that information.
    # --- Fassaden-Durchreichung an die Tests (heute genutzt) ---
    "Finding", "Severity",          # aus .report — Testreferenz docs_lib.Severity
    # --- V1 (docs_freshness) ---
    "check_no_manual_counts", "V1_CHECK_ID", "V1_SCAN_RELPATHS",
    "V1_GENERATED_RELPATHS", "V1_MAX_TOKEN_GAP", "V1_REGION_BEGIN", "V1_REGION_END",
    "V1_EXEMPT_MARKER", "V1_SUGGESTION", "v1a_count_spans", "v1b_version_spans", "v1_strict",
    "Span",
    # --- V3 (docs_links) ---
    "check_internal_links", "V3_CHECK_ID", "V3_SUGGESTION", "V3_ENTRY_RELPATHS",
    "V3_DOCS_RELDIR", "V3_DOC_SUFFIXES", "V3_INERT_PREFIXES",
    # --- Altchecks (docs_links) ---
    "check_sync_cli_docs", "check_ui_help_mappings", "check_readme_docs_index",
    # --- V2 (docs_index) ---
    "V2_CHECK_ID", "check_docs_index_completeness",
    # --- V5 (docs_freshness_v5) ---
    "V5_CHECK_ID", "check_role_generation_parity",
    # --- V6 (docs_freshness) ---
    "V6_CHECK_ID", "check_docs_facts_fresh",
    # --- V7 (docs_wiki) ---
    "V7_CHECK_ID", "check_wiki_staleness",
    # --- noch offen: `check_spec_plan_path_convention` (V8, W6-2) und
    # `check_stale_backups` (V9, W8-4) ---
    # W2-7 hat die vier oben liegenden Checks eingetragen und registriert;
    # W6-2 und W8-4 tragen ihren Namen hier ein, wenn sie den Check
    # implementieren, und haengen ihn in dieselbe Registrierung in
    # `scripts/consistency-check.py` (Plan W2-7, `Files:`).
]
