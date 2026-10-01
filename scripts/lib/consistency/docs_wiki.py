"""Derived-inventory checks — does the derived surface still match its sources?

Family of the file-check cut of Spec §4.1 (U-1, decision U-1 / K18): the cut
follows **the question a check asks**, not file size and not the wave a check
belongs to. This module owns exactly one question — *"Does the derived
knowledge/inventory surface still match the sources it was derived from?"* — and
therefore exactly the checks that compare a generated surface against the
artefact it was generated from:

* **V7** ``check_wiki_staleness`` (AC-10, IC-05) — implemented here (W2-3).
* **V8** ``check_spec_plan_path_convention`` (K28) — W6-2, assigned here by
  Spec §4.1 because it also asks whether a derived documentation surface still
  matches its producer.

No check of any other module answers that question, so none is shared with
``docs_links`` (is a reference resolvable?) or ``docs_freshness`` (does the prose
match the computed state?). The 600-line ceiling is a consequence of the cut,
not its purpose (K18).

**V7 is a thin adapter, not a second implementation of IC-03.** Every statement
about a page comes from the W1-4 resolver
:func:`scripts.lib.doc_facts.compute_wiki_staleness`; this module decides only
*which* of the resolver's states become a finding and how that finding reads.
Two properties make that checkable rather than a matter of taste:

* the resolver's value domain is **closed** (``""``, ``missing-derived-from``,
  ``stale-source``, ``age-<n>d`` — pinned by IC-03 and by
  ``test_resolver_states_are_exactly_the_four_documented_values``), so
  :data:`_V7_REPORTED_REASONS` is a complete table over the two states IC-05
  names as detection-worthy. A state absent from the table is not reported;
* ``age-<n>d`` is documented as an **observation, not a status** and is
  deliberately absent, so V7's finding count grows with *defects* and not with
  the age of the repository.

``Finding`` (``report.py``) carries no ``line`` and no ``branch`` field, so V1
and V3 attach both as instance attributes that ``print_json_report`` drops. V7
does **not**: a wiki page is a whole file, so there is no line to point at, and
the reason a page was reported belongs in the message, where ``--json`` actually
shows it. That is also what AC-10 needs — the ``stale-source`` half requires the
finding to *name* the reason, not to encode it in an attribute the report drops.

``docs.py`` stays the facade the runner and the test suite import (K19). This
module is reached through it, and the re-export of ``check_wiki_staleness`` into
that ``__all__`` is **W2-7's** write-set alone (K20/K46) — W2-3 does not touch
it. Nothing here is stdlib-external.
"""

from __future__ import annotations

from pathlib import Path

from ..doc_facts import (
    DERIVED_AT_KEY,
    DERIVED_FROM_KEY,
    WIKI_ARCHITECTURE_TYPE,
    WIKI_MISSING_DERIVED_FROM,
    WIKI_STALE_SOURCE,
    compute_wiki_staleness,
)
from .report import Finding, Severity

V7_CHECK_ID = "docs.wiki_staleness"

#: The knowledge bundle root, relative to the project root. A module constant
#: (not an inline literal) so a test can point the check at a fixture tree.
V7_WIKI_RELPATH = "knowledge/wiki"

V7_SUGGESTION = (
    f"Declare the provenance (`{DERIVED_FROM_KEY}` plus `{DERIVED_AT_KEY}`) "
    f"and re-derive the page from that source."
)

#: The two states IC-05 names for V7, and how each is reported. Keyed by the
#: ``doc_facts`` constants — never by a copied string literal — so the state the
#: resolver produces and the word the finding prints cannot drift apart.
#:
#: ``WIKI_FRESH`` (``""``) and ``age-<n>d`` are absent on purpose: the first is
#: "no defect", the second an observation (see the module docstring).
_V7_REPORTED_REASONS: dict[str, str] = {
    WIKI_MISSING_DERIVED_FROM: (
        f"type {WIKI_ARCHITECTURE_TYPE} without `{DERIVED_FROM_KEY}` "
        f"({WIKI_MISSING_DERIVED_FROM})"
    ),
    WIKI_STALE_SOURCE: (
        f"source of `{DERIVED_FROM_KEY}` is newer than `{DERIVED_AT_KEY}` "
        f"({WIKI_STALE_SOURCE})"
    ),
}


def check_wiki_staleness(root: Path, config: dict | None = None) -> list[Finding]:
    """V7: a derived wiki page that no longer matches its source (AC-10, IC-05).

    Two forms, and only the two IC-05 names: a ``type: Architecture`` page
    without a usable ``derived-from`` (:data:`WIKI_MISSING_DERIVED_FROM`) and a
    page whose source was modified after its ``derived-at``
    (:data:`WIKI_STALE_SOURCE`). Both are WARNING — V7 has one severity and
    reads no config key, unlike V1 which follows
    ``docs-consolidation.checks.strict``.

    The staleness of a page is **not** computed here. It is read from
    :func:`scripts.lib.doc_facts.compute_wiki_staleness` (IC-03, W1-4), which
    also owns the fail-soft behaviour: a missing ``knowledge/wiki``, an
    unreadable page or a ``derived-from`` target that does not exist answer
    "fresh", so they produce no finding rather than a fabricated one.

    V7 is **scheduled red** until W5-3 annotates the Architecture pages that
    carry no provenance; that is a term with an owner, not a defect of this
    check (Spec §10, point 5).

    ``config`` is accepted for the runner's uniform call signature and is not
    read. The common gate ``docs-consolidation.enabled`` and the registration in
    ``run_checks()`` are W2-7's.
    """
    findings: list[Finding] = []
    for relpage, state in compute_wiki_staleness(
        root / V7_WIKI_RELPATH, root
    ).items():
        reason = _V7_REPORTED_REASONS.get(state)
        if reason is None:
            continue
        findings.append(Finding(
            severity=Severity.WARNING,
            check=V7_CHECK_ID,
            file=f"{V7_WIKI_RELPATH}/{relpage}",
            message=f"{relpage}: {reason}",
            suggestion=V7_SUGGESTION,
        ))
    return findings
