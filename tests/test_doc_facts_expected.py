"""AC-36 / IC-23 (R14, NFA-11) — the independent expected-value source (W1-5).

This file is the **only** place in the repo where the computed ``DOCS_*``
facts and the hand-maintained ``config/doc-facts-expected.yaml`` meet. That is
the whole point of IC-23 and the reason the meeting place is a test and not a
module: the chain ``doc_facts → renderer → V6`` is a closed circle — V6
compares the rendered block against ``compute_doc_facts()``, i.e. against the
same formula that produced it — and a second, human-maintained source is the
only countermeasure against a systematically wrong factor (spec F19/F22/F14
were three counting errors that no V-check would have found).

**No fact value is hard-coded here.** Per Spec NEW-8 the ``xfail`` snapshot is
gone and ``config/doc-facts-expected.yaml`` is the single place in the repo
tree that may hold an expected *number*. This file therefore never restates a
value: it loads the real oracle, and every negative case works on a *manipulated
copy* of that oracle (a dict, or a file written into ``tmp_path``). What it
does spell out are fact **names** and the **count** eleven — the enumeration of
IC-23, not a number produced by the formula.

Three contracts are pinned here, each of which the refactors that could break
them would break silently:

* **The circle is broken.** :func:`compute_doc_facts` takes no expected-value
  parameter, its body mentions neither the oracle path nor its loader, the
  oracle path is spelled exactly once in the module (the loader), and the
  compute path demonstrably never reads the file. The AC-36 behavioural half —
  "``compute_doc_facts()`` bleibt dabei unverändert (die Sollwerte fließen
  **nicht** in die Berechnung ein)" — is asserted with the computed facts
  compared before and after a manipulated oracle.
* **The comparator's ``kind`` vocabulary is two-valued**
  (``{mismatch, missing-in-expected}`` — IC-23's code block and plan W1-5
  *Interfaces*), and ``expected-mismatch`` is **not** one of them: that
  spelling belongs to the V6 **check** (W2-5), which owns the third axis
  ``handedit`` that this comparator cannot see. The W2-5 check is expected to
  build its ``Finding`` from the entries produced here, so this test is the
  contract's first half; AC-36's *first* clause and the W1-5 acceptance text
  name the check's spelling for this list and are the text to correct (F10 in
  ``scripts/lib/doc_facts.py``).
* **The oracle's key set is a decision, not an accident.** A new pinnable
  scalar fact that nobody pinned turns
  :data:`~scripts.lib.doc_facts.EXPECTED_COMPARABLE_FACT_KEYS` into a
  ``missing-in-expected`` warning; ``DOCUMENTED_UNPINNED`` below is where that
  decision is recorded, so a new fact cannot slip in unreviewed.

W2-5 extends this file with the V6 findings; it does not change the oracle
contract asserted here. The V6 half of ``test_mismatch_is_reported`` is the
acceptance criterion of that task, which is why the test name appears in both
IC-23 and the W2-5 plan row: the first half stays the comparator entry, the
second half is the check's ``Finding``.

The imports therefore grew from ``scripts.lib.doc_facts`` alone to
``scripts.lib.doc_renderer`` (to render a block from the computed facts) and
``scripts.lib.consistency.docs_freshness`` (the check under test). The file
still does **not** import the ``docs`` facade — W2-7 owns that name (K19/K46).
Spec §4.1 states the old, narrower import set in its evidence paragraph
("bindet ausschließlich ``scripts.lib.doc_facts``"); that sentence is about the
*facade* list and stays correct, the W6 documentation pass owns the wording.
"""

from __future__ import annotations

import inspect
from collections.abc import Mapping
from pathlib import Path

import pytest
import yaml

from scripts.lib import doc_facts
from scripts.lib.consistency import docs_freshness as docs_freshness_lib
from scripts.lib.doc_facts import (
    EXPECTED_COMPARABLE_FACT_KEYS,
    EXPECTED_DOC_FACTS_RELPATH,
    EXPECTED_FACTS_META_KEYS,
    FACT_KEYS,
    MISMATCH_KIND,
    MISSING_IN_EXPECTED_KIND,
    compare_expected_doc_facts,
    compute_doc_facts,
    is_volatile,
    load_expected_doc_facts,
)
from scripts.lib.doc_renderer import apply_fact_blocks, render_doc_fact_block

REPO_ROOT = Path(__file__).resolve().parent.parent

#: IC-23: "Schlüsselzahl: elf (11)". The count, not a value.
EXPECTED_ENTRY_COUNT = 11

#: Facts inside :data:`EXPECTED_COMPARABLE_FACT_KEYS` that IC-23 does not pin,
#: with the reason. ``test_expected_values_match`` requires the reported
#: ``missing-in-expected`` set to equal exactly this — so a newly implemented
#: scalar fact makes the suite red until a human records a decision here.
DOCUMENTED_UNPINNED: Mapping[str, str] = {
    "DOCS_AGENTS_NONSE_COUNT": (
        "IC-23: pure difference, SE + NONSE == TEMPLATES, formula-checked in AC-02"
    ),
    # --- F11: not covered by any exclusion IC-23 states. Reported, not
    # --- silently pinned; see the module docstring of scripts/lib/doc_facts.py.
    "DOCS_AGENTS_ACTIVE_COUNT": (
        "F11: absent from IC-23's eleven without a stated reason; plausibly "
        "'rendered as a number' (its 58 vs 53 correction is exactly the R14 "
        "class this file exists for) — owner decision pending"
    ),
    "DOCS_DOCS_FILE_COUNT": (
        "F11: absent from IC-23's eleven without a stated reason; plausibly "
        "'rendered as a number' (it is rendered nowhere today) — owner decision "
        "pending"
    ),
}


class _StubLog:
    """Duck-typed ``SyncLog`` stand-in that records every ``debug`` call."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def debug(self, target: str, message: str) -> None:
        self.calls.append((target, message))


def _project_config() -> dict:
    """The project config the formulas are evaluated against (never invented)."""
    from scripts.lib.io import load_yaml_file

    return load_yaml_file(REPO_ROOT / ".meta-config" / "project.yaml", on_error="raise")


@pytest.fixture(scope="module")
def computed() -> dict[str, str]:
    """The computed side. Plain, no oracle in sight — see the circle tests."""
    return compute_doc_facts(REPO_ROOT, _project_config(), provider_config={})


@pytest.fixture(scope="module")
def expected() -> dict[str, str]:
    """The oracle exactly as it sits in the repository."""
    return load_expected_doc_facts(REPO_ROOT)


def _pinnable(fact: str) -> bool:
    return fact in EXPECTED_COMPARABLE_FACT_KEYS


def _mismatches(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    return [entry for entry in entries if entry["kind"] == MISMATCH_KIND]


def _unpinned(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    return [entry for entry in entries if entry["kind"] == MISSING_IN_EXPECTED_KIND]


def _manipulate(entries: dict[str, str], fact: str) -> dict[str, str]:
    """A copy of the oracle with exactly one value falsified.

    The replacement is derived from the value itself (so no expected number is
    written down in this file) and is guaranteed to differ from it.
    """
    assert fact in entries, f"{fact} is not pinned by the oracle"
    original = entries[fact]
    manipulated = dict(entries)
    manipulated[fact] = original + "-manipulated"
    assert manipulated[fact] != original
    return manipulated


# --- AC-36: the oracle as committed ------------------------------------------


def test_expected_file_has_exactly_eleven_entries(expected):
    """IC-23: eleven entries — the count is the assertion, never a value."""
    assert len(expected) == EXPECTED_ENTRY_COUNT, sorted(expected)


def test_expected_keys_are_known_facts(expected):
    """A typo in the oracle must stay visible, not be dropped silently.

    The loader keeps unknown keys on purpose (a dropped key would reproduce the
    unverified-number class IC-23 exists to remove), so this test is what turns
    "kept" into "reported".
    """
    unknown = sorted(set(expected) - set(FACT_KEYS))
    assert not unknown, f"oracle pins keys that are not IC-02 facts: {unknown}"
    for fact in expected:
        assert not fact.endswith("_BLOCK"), f"{fact}: IC-23 excludes rendered text"
        assert not is_volatile(fact), f"{fact}: volatile facts must not be pinned (R1)"


def test_expected_values_match(computed, expected):
    """AC-36: the unmanipulated oracle produces no mismatch.

    Two halves, because the two kinds mean different things:

    * **no** ``mismatch`` — every one of the eleven hand-maintained values
      equals what the formula computes. This is the R14 assertion: the two
      sources agree, and they agree *without* sharing a formula.
    * the ``missing-in-expected`` set is exactly
      :data:`DOCUMENTED_UNPINNED` — the computable, pinnable facts IC-23 does
      not pin. Recorded as names, not values, so a new scalar fact cannot
      appear unpinned without a decision.
    """
    entries = compare_expected_doc_facts(computed, expected)
    assert _mismatches(entries) == [], _mismatches(entries)
    reported = {entry["fact"]: entry for entry in _unpinned(entries)}
    assert set(reported) == set(DOCUMENTED_UNPINNED), {
        "unreviewed": sorted(set(reported) - set(DOCUMENTED_UNPINNED)),
        "stale": sorted(set(DOCUMENTED_UNPINNED) - set(reported)),
    }
    for fact, entry in reported.items():
        assert entry["computed"] == computed[fact]
        assert entry["expected"] == ""
        assert DOCUMENTED_UNPINNED[fact], fact


def test_mismatch_is_reported(computed, expected, monkeypatch):
    """AC-36, both halves: the comparator entry **and** the V6 finding.

    The comparator half is IC-23's data contract: one entry, both values.

    The V6 half is the acceptance criterion of plan task W2-5 and the whole
    reason IC-23 exists. ``check_docs_facts_fresh`` is run against the **real
    repository** with the **real** project config, so the facts it compares are
    the ones the renderer would have written — and the *only* seam patched is
    ``load_expected_doc_facts``, which hands the check a manipulated dict instead
    of the committed oracle (the oracle file itself is never written). The
    result is exactly one ERROR of kind ``expected-mismatch`` while axis (a) —
    the handedit axis, which compares the rendered documents against those same
    facts — stays silent. That is the proof that the circle
    ``doc_facts -> renderer -> V6`` is broken from the outside: a systematically
    wrong factor still renders self-consistent documentation, and only the human
    oracle catches it (R14; spec F19, F22 and F14 were exactly that).
    """
    fact = sorted(expected)[0]
    manipulated = _manipulate(expected, fact)
    entries = compare_expected_doc_facts(computed, manipulated)

    mismatches = _mismatches(entries)
    assert len(mismatches) == 1, mismatches
    entry = mismatches[0]
    assert entry["fact"] == fact
    assert entry["computed"] == computed[fact]
    assert entry["expected"] == manipulated[fact]
    assert entry["computed"] != entry["expected"]
    # The unpinned findings are unaffected by an oracle value change.
    assert {e["fact"] for e in _unpinned(entries)} == set(DOCUMENTED_UNPINNED)

    # --- the V6 half: the check, on the real tree, with a manipulated oracle ---
    monkeypatch.setattr(
        docs_freshness_lib, "load_expected_doc_facts", lambda root, log=None: manipulated
    )
    findings = docs_freshness_lib.check_docs_facts_fresh(REPO_ROOT, _project_config())

    errors = [f for f in findings if f.severity == docs_freshness_lib.Severity.ERROR]
    assert [f.kind for f in errors] == ["expected-mismatch"], [
        (f.severity, f.kind, f.message) for f in findings
    ]
    finding = errors[0]
    assert finding.check == "docs.docs_facts_fresh"
    assert finding.file == EXPECTED_DOC_FACTS_RELPATH
    assert fact in finding.message
    assert entry["computed"] in finding.message
    assert entry["expected"] in finding.message
    # The only warnings are the documented unpinned facts — the oracle grows
    # (IC-23), so they are a warning axis and not a second error axis.
    assert {
        f.message.split(":", 1)[0]
        for f in findings
        if f.severity == docs_freshness_lib.Severity.WARNING
    } == set(DOCUMENTED_UNPINNED)
    # Premise for the "obwohl": the computed facts are the ones the documents
    # were rendered from, and a rendered block of them is byte-identical to what
    # the renderer produces — so a *handedit* finding would be a false alarm
    # here, and its absence is the meaningful half of the criterion. (The
    # rendered body carries the newline that closes the ``docs-begin`` line,
    # which is why the marker is not followed by one here.)
    rendered = render_doc_fact_block("roster", computed)
    document = (
        "<!-- agent-meta:docs-begin roster -->"
        f"{rendered}"
        "<!-- agent-meta:docs-end roster -->\n"
    )
    assert apply_fact_blocks(document, computed) == document
    # And the handedit axis really did run: it scans the same three entry
    # documents the generator renders into, none of which carries a marker
    # region before W3/W4.
    for relpath in docs_freshness_lib.V6_SCAN_RELPATHS:
        path = REPO_ROOT / relpath
        if path.is_file():
            assert "agent-meta:docs-begin" not in path.read_text(encoding="utf-8")


def test_missing_in_expected_is_reported(computed, expected):
    """The second kind: a pinnable fact the oracle does not carry.

    Removing a key from a copy of the oracle adds exactly one
    ``missing-in-expected`` entry and changes no ``mismatch`` — the file is
    allowed to grow (IC-23), so this is a warning axis, not a second error axis.
    """
    fact = sorted(expected)[0]
    trimmed = {name: value for name, value in expected.items() if name != fact}
    entries = compare_expected_doc_facts(computed, trimmed)

    assert _mismatches(entries) == []
    missing = [entry for entry in entries if entry["fact"] == fact]
    assert len(missing) == 1, missing
    entry = missing[0]
    assert entry["kind"] == MISSING_IN_EXPECTED_KIND
    assert entry["computed"] == computed[fact]
    assert entry["expected"] == ""
    # One more unpinned fact than before, and exactly that one.
    assert {e["fact"] for e in _unpinned(entries)} == set(DOCUMENTED_UNPINNED) | {fact}


def test_comparator_reports_only_pinnable_facts(computed, expected):
    """The comparison scope is a decision: no ``*_BLOCK``, no volatile fact.

    ``*_BLOCK`` facts are rendered text (IC-23), ``DOCS_SCENARIO_COUNT`` is
    volatile (R1). Both are permanently unpinnable, so reporting them would be
    a permanent warning for a decision nobody can take — the F21 false-alarm
    class. A ``mismatch`` for them is still possible if the oracle ever names
    one, but that is the loader's business, not this scope's.
    """
    entries = compare_expected_doc_facts(computed, expected)
    for entry in entries:
        assert _pinnable(entry["fact"]), entry
        assert not entry["fact"].endswith("_BLOCK")
        assert not is_volatile(entry["fact"])
    # Every pinnable fact is either pinned or reported — none is invisible.
    seen = {entry["fact"] for entry in entries} | set(expected)
    assert set(EXPECTED_COMPARABLE_FACT_KEYS) - seen == set()


def test_entries_are_sorted_by_fact_and_deterministic(computed, expected):
    """Determinism: sorted by ``fact``, and independent of dict input order."""
    entries = compare_expected_doc_facts(computed, expected)
    assert entries == sorted(entries, key=lambda entry: entry["fact"])
    reversed_inputs = compare_expected_doc_facts(
        dict(reversed(list(computed.items()))),
        dict(reversed(list(expected.items()))),
    )
    assert reversed_inputs == entries
    assert compare_expected_doc_facts(computed, expected) == entries


def test_every_entry_names_all_four_fields(computed, expected):
    """Shape of a finding: ``fact`` / ``computed`` / ``expected`` / ``kind``."""
    manipulated = _manipulate(expected, sorted(expected)[-1])
    entries = compare_expected_doc_facts(computed, manipulated)
    assert entries
    for entry in entries:
        assert set(entry) == {"fact", "computed", "expected", "kind"}
        assert all(isinstance(value, str) for value in entry.values())


# --- the vocabulary split (F10): comparator vs. V6 check ----------------------


def test_comparator_kind_domain_is_mismatch_not_expected_mismatch(
    computed, expected
):
    """Pin the comparator's own ``kind`` domain, and the boundary to W2-5.

    ``expected-mismatch`` is the **V6 check's** kind (IC-23 *Vertrag* (b), plan
    W2-5): V6 has three comparison axes and therefore three kinds. The
    comparator has two. Emitting the check's spelling here would make the two
    vocabularies indistinguishable at the boundary W2-5 consumes — and the
    check cannot invent the mapping, it has to be told.
    """
    fact = sorted(expected)[0]
    manipulated = _manipulate(expected, fact)
    entries = compare_expected_doc_facts(computed, manipulated)

    kinds = {entry["kind"] for entry in entries}
    assert kinds <= {MISMATCH_KIND, MISSING_IN_EXPECTED_KIND}
    assert "expected-mismatch" not in kinds
    assert "handedit" not in kinds
    # The kind constants are the single source of truth for both spellings.
    assert (MISMATCH_KIND, MISSING_IN_EXPECTED_KIND) == (
        "mismatch",
        "missing-in-expected",
    )


# --- the circle is broken (R14) ---------------------------------------------


def test_compute_doc_facts_has_no_expected_parameter():
    """IC-23 contract: no Sollwert parameter — no coupling, no other direction."""
    parameters = inspect.signature(compute_doc_facts).parameters
    assert not [name for name in parameters if "expect" in name.lower()], parameters
    for banned in ("load_expected_doc_facts", "compare_expected_doc_facts"):
        assert banned not in parameters, parameters


def test_compute_path_never_mentions_the_oracle():
    """Structural: the compute function's body names neither path nor loader.

    A *behavioural* test cannot prove the absence of a read, but the absence of
    the name in the only function that computes is what makes the read
    impossible: the oracle path is a constant, and the constant is read by the
    loader alone (checked for every function of the module below).
    """
    source = inspect.getsource(compute_doc_facts)
    assert EXPECTED_DOC_FACTS_RELPATH not in source
    assert "load_expected_doc_facts" not in source
    assert "EXPECTED_DOC_FACTS_RELPATH" not in source
    # The whole module: no function other than the loader may spell the path or
    # reference the constant, so a fact implementation can only reach the file
    # by being handed the loaded dict — the coupling this task forbids. (The
    # module docstring and the constant's own definition are documentation.)
    def _uses(token: str) -> list[str]:
        return sorted(
            name
            for name, obj in vars(doc_facts).items()
            if inspect.isfunction(obj)
            and name != "load_expected_doc_facts"
            and token in inspect.getsource(obj)
        )

    loader_source = inspect.getsource(load_expected_doc_facts)
    assert EXPECTED_DOC_FACTS_RELPATH in loader_source
    assert "EXPECTED_DOC_FACTS_RELPATH" in loader_source
    assert _uses(EXPECTED_DOC_FACTS_RELPATH) == [], _uses(EXPECTED_DOC_FACTS_RELPATH)
    assert _uses("EXPECTED_DOC_FACTS_RELPATH") == [], _uses("EXPECTED_DOC_FACTS_RELPATH")
    assert _uses("load_expected_doc_facts") == [], _uses("load_expected_doc_facts")


def test_expected_file_is_read_only_by_the_loader(monkeypatch, expected):
    """Behavioural: ``compute_doc_facts`` never opens the oracle file.

    Every YAML read the compute path performs goes through
    ``doc_facts.load_yaml_file`` (the module's only YAML entry point), so
    recording the paths it is asked for is a complete record of what the
    compute side touches. The oracle appears when the loader runs and never
    when the facts are computed.
    """
    reads: list[str] = []
    real_loader = doc_facts.load_yaml_file

    def _recording_loader(path, **kwargs):
        reads.append(str(path))
        return real_loader(path, **kwargs)

    monkeypatch.setattr(doc_facts, "load_yaml_file", _recording_loader)
    compute_doc_facts(REPO_ROOT, _project_config(), provider_config={})
    assert not [r for r in reads if r.endswith("doc-facts-expected.yaml")], reads
    assert reads, "the compute path is expected to read YAML sources at all"

    reads.clear()
    load_expected_doc_facts(REPO_ROOT)
    assert [r for r in reads if r.endswith("doc-facts-expected.yaml")], reads


def test_manipulated_oracle_does_not_change_computed_facts(computed, expected):
    """AC-36: the Sollwerte do not flow into the computation.

    The operational half of "the circle is broken": feeding a falsified oracle
    into the comparator changes the *findings* and leaves the computed facts
    byte-identical.
    """
    fact = sorted(expected)[0]
    before = dict(computed)
    manipulated = _manipulate(expected, fact)

    entries = compare_expected_doc_facts(before, manipulated)
    assert len(_mismatches(entries)) == 1

    after = compute_doc_facts(REPO_ROOT, _project_config(), provider_config={})
    assert after == before
    assert len(_mismatches(compare_expected_doc_facts(after, manipulated))) == 1


def test_compute_works_without_any_oracle_file(tmp_path):
    """The compute side needs no oracle at all — not even an existing one.

    A root that has no ``config/doc-facts-expected.yaml`` still produces the
    full fact key set. Were the coupling in the other direction, this is the
    test that would fail first.
    """
    facts = compute_doc_facts(tmp_path, {}, provider_config={})
    assert set(facts) == set(FACT_KEYS)
    assert load_expected_doc_facts(tmp_path) == {}


# --- the loader: fail-soft, metadata, no caching (IC-01) ---------------------


def test_missing_oracle_file_is_fail_soft(tmp_path):
    """IC-01: absent file → ``{}`` plus exactly one ``log.debug``, no raise."""
    log = _StubLog()
    assert load_expected_doc_facts(tmp_path, log) == {}
    assert len(log.calls) == 1, log.calls
    target, message = log.calls[0]
    assert target == "docs"
    assert EXPECTED_DOC_FACTS_RELPATH in message


def test_unreadable_oracle_file_is_fail_soft(tmp_path):
    """Malformed YAML degrades the same way — and never fabricates a number."""
    _write_oracle(tmp_path, "schema-version: 1\nDOCS_VERSION: [unclosed\n")
    log = _StubLog()
    assert load_expected_doc_facts(tmp_path, log) == {}
    assert len(log.calls) == 1, log.calls
    assert EXPECTED_DOC_FACTS_RELPATH in log.calls[0][1]


def test_non_mapping_oracle_file_is_fail_soft(tmp_path):
    """A YAML list/scalar document is not a fact map either."""
    _write_oracle(tmp_path, "- DOCS_VERSION: \"1\"\n")
    log = _StubLog()
    assert load_expected_doc_facts(tmp_path, log) == {}
    assert len(log.calls) == 1, log.calls


def test_missing_file_without_log_is_silent_and_empty(tmp_path):
    """``log=None`` is legal: fail-soft means fail-soft, not raise."""
    assert load_expected_doc_facts(tmp_path) == {}
    assert load_expected_doc_facts(REPO_ROOT / "does-not-exist") == {}


def test_loader_strips_metadata_keys(tmp_path):
    """``schema-version`` / ``verified-at`` / ``verified-by`` are not facts."""
    _write_oracle(
        tmp_path,
        "schema-version: 1\nverified-at: \"2026-01-01\"\nverified-by: human\n",
    )
    assert load_expected_doc_facts(tmp_path) == {}


def test_loader_coerces_scalar_values_and_drops_containers(tmp_path):
    """Str contract (IC-02) plus one ``log.debug`` per non-scalar value.

    A human may drop the quotes around a number; a nested block is not a fact
    value and is reported instead of being stringified into nonsense.
    """
    _write_oracle(
        tmp_path,
        "schema-version: 1\n"
        "DOCS_VERSION: 1.2.3\n"
        "DOCS_HOOKS_COUNT: [11]\n",
    )
    log = _StubLog()
    result = load_expected_doc_facts(tmp_path, log)
    assert result == {"DOCS_VERSION": "1.2.3"}
    assert all(isinstance(value, str) for value in result.values())
    assert len(log.calls) == 1
    assert "DOCS_HOOKS_COUNT" in log.calls[0][1]


def test_loader_does_not_cache_a_failure(tmp_path):
    """Per-call contract: a failure is retried, never remembered.

    A cached failure would keep reporting "nothing pinned" for the rest of the
    process — the same staleness the per-call ``FactContext.sources`` memo
    avoids for the fact sources.
    """
    assert load_expected_doc_facts(tmp_path) == {}
    _write_oracle(tmp_path, "schema-version: 1\nDOCS_VERSION: \"1.2.3\"\n")
    assert load_expected_doc_facts(tmp_path) == {"DOCS_VERSION": "1.2.3"}


def test_loader_never_writes_the_oracle_file(tmp_path, expected):
    """The oracle is a hand-maintained file: reading it must not touch it.

    The full AC-01 write-invariance digest lives in
    ``tests/test_doc_facts.py``; this is the file-local half for the one file
    W1-5 introduces.
    """
    path = REPO_ROOT / EXPECTED_DOC_FACTS_RELPATH
    before = path.read_bytes()
    load_expected_doc_facts(REPO_ROOT)
    assert path.read_bytes() == before


def test_oracle_file_is_valid_yaml_with_a_verification_stamp():
    """``verified-by: human`` is the IC-23 provenance stamp — keep it checkable."""
    raw = yaml.safe_load(
        (REPO_ROOT / EXPECTED_DOC_FACTS_RELPATH).read_text(encoding="utf-8")
    )
    assert raw["verified-by"] == "human"
    assert isinstance(raw["verified-at"], str) and raw["verified-at"]
    assert raw["schema-version"] == 1
    for key in raw:
        if key in EXPECTED_FACTS_META_KEYS:
            continue
        assert isinstance(raw[key], str), f"{key} must be a quoted string (IC-02)"


def _write_oracle(root: Path, text: str) -> Path:
    """Write an oracle into an isolated root (never the repository's)."""
    path = root / EXPECTED_DOC_FACTS_RELPATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path
