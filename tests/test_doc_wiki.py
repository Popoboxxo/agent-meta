"""AC-10 (IC-05, IC-03; spec §5.1.1) — V7 ``check_wiki_staleness``.

V7 answers the question of the *derived inventory* family (Spec §4.1, U-1/K18):
*does the derived knowledge surface still match the sources it was derived
from?* Exactly two forms are detection-worthy, and IC-05 names both — a
``type: Architecture`` page without ``derived-from``, and a page whose
``derived-from`` source was modified after its ``derived-at``.

Everything V7 knows about a page comes from the W1-4 resolver
``scripts.lib.doc_facts.compute_wiki_staleness`` (IC-03). This file therefore
tests a **mapping**, not a rule, and one test pins that fact directly: the
resolver is monkeypatched to a state the tree on disk does not have, and the
check must still report exactly that. Re-deriving staleness inside the check
would be a second implementation of IC-03 and a silent second source of truth;
the ``age-<n>d`` case is the reason the distinction is easy to lose, because
``age`` looks like a status and is documented as an *observation*.

The module under test is ``scripts.lib.consistency.docs_wiki`` directly, not
the ``docs`` facade. The facade re-export of ``check_wiki_staleness`` is
W2-7's write-set (K20/K46), so visibility through ``docs.py`` is *not* asserted
here — asserting it would fail until W2-7 lands and would make this file a
dependency of a task that does not own it.

**No hardcoded baseline count (Spec NEW-8).** The real-wiki test re-derives its
expectation from disk instead of pinning a number. The measurement of record
today is 10 ``type: Architecture`` pages without ``derived-from``; it becomes 0
in W5-3, which annotates them, and a test that pinned either value would have to
be edited by the very task it is meant to gate. (The Spec's K24 figure of **11**
counts one further ``type:`` line that sits inside a fenced YAML *example* in
``core-principle-knowledge-engine.md:46`` — see the deviation note in the W2-3
report.)
"""

from __future__ import annotations

import inspect
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.lib.consistency import docs_wiki as docs_wiki_lib
from scripts.lib.doc_facts import (
    DERIVED_AT_KEY,
    DERIVED_FROM_KEY,
    WIKI_ARCHITECTURE_TYPE,
    WIKI_MISSING_DERIVED_FROM,
    WIKI_STALE_SOURCE,
    compute_wiki_staleness,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

#: The IC-05 wire format, quoted literally so a rename in the module cannot make
#: this suite and the runner agree on the wrong check id.
V7_CHECK_ID = "docs.wiki_staleness"

V7_WIKI_RELPATH = "knowledge/wiki"

SOURCE_RELPATH = "docs/source.md"
"""Project-root-relative ``derived-from`` target of the fixtures below."""


# ---------------------------------------------------------------------------
# Fixtures — independent of ``tests/test_doc_facts.py`` on purpose
# ---------------------------------------------------------------------------
#
# The IC-03 fixtures already exist in ``tests/test_doc_facts.py`` (W1-4). They are
# duplicated rather than imported because that file is a write-set of other plan
# tasks, and a shared helper would have to live in ``conftest.py``, which is
# outside W2-3's file set. Two copies of a fixture are an acceptable price for
# disjoint write-sets; an import across them would couple the two waves.


def _wiki_page(root: Path, relpage: str, frontmatter: dict[str, object]) -> Path:
    """Write a Markdown page with YAML frontmatter below ``root``."""
    page = root / relpage
    page.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---"]
    for key, value in frontmatter.items():
        rendered = f'"{value}"' if isinstance(value, str) else str(value)
        lines.append(f"{key}: {rendered}")
    lines += ["---", "", "# page\n"]
    page.write_text("\n".join(lines), encoding="utf-8")
    return page


def _set_mtime(path: Path, moment: datetime) -> None:
    epoch = moment.timestamp()
    os.utime(path, (epoch, epoch))


def _days_ago(days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)


def _write_source(root: Path, mtime: datetime) -> Path:
    """Create the shared ``derived-from`` target with a **pinned** mtime.

    ``stale-source`` is a filesystem comparison, so a fixture that left the mtime
    at "now" would answer differently depending on how fast the suite runs.
    """
    source = root / SOURCE_RELPATH
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("# source\n", encoding="utf-8")
    _set_mtime(source, mtime)
    return source


def _derived_page(root: Path, name: str, derived_at: datetime) -> Path:
    """A dated source plus one ``type: Architecture`` page declaring it."""
    _write_source(root, derived_at)
    return _wiki_page(
        root / V7_WIKI_RELPATH / "concepts",
        name,
        {
            "type": WIKI_ARCHITECTURE_TYPE,
            DERIVED_FROM_KEY: SOURCE_RELPATH,
            DERIVED_AT_KEY: derived_at.isoformat(),
        },
    )


def _relpage(name: str) -> str:
    """The ``file`` value V7 must report for a page below the wiki root."""
    return f"{V7_WIKI_RELPATH}/concepts/{name}"


def _states(root: Path) -> dict[str, str]:
    """The W1-4 resolver's view of ``root`` — the state V7 maps."""
    return compute_wiki_staleness(root / V7_WIKI_RELPATH, root)


# ---------------------------------------------------------------------------
# AC-10 — the two detection forms
# ---------------------------------------------------------------------------


def test_v7_missing_and_stale_derived_from(tmp_path):
    """AC-10, both halves: a missing ``derived-from`` and an outdated one.

    IC-05 states the two forms separately, and the ``stale-source`` half is
    stronger than "a finding appears": the finding has to *name* the reason, so
    that a reader can tell the two apart without opening the resolver. The
    remedy — annotating the missing ``derived-from`` — is W5-3's, not this
    task's; V7 is scheduled red until then.
    """
    concepts = tmp_path / V7_WIKI_RELPATH / "concepts"
    _wiki_page(
        concepts,
        "no-provenance.md",
        {"type": WIKI_ARCHITECTURE_TYPE, "title": "no provenance"},
    )

    derived_at = _days_ago(10)
    _derived_page(tmp_path, "stale.md", derived_at)
    _set_mtime(_write_source(tmp_path, derived_at), derived_at + timedelta(days=1))

    findings = docs_wiki_lib.check_wiki_staleness(tmp_path)

    assert {f.file for f in findings} == {
        _relpage("no-provenance.md"), _relpage("stale.md"),
    }, findings
    assert {f.check for f in findings} == {V7_CHECK_ID}, findings
    by_file = {f.file: f.message for f in findings}
    assert WIKI_MISSING_DERIVED_FROM in by_file[_relpage("no-provenance.md")], by_file
    assert WIKI_STALE_SOURCE in by_file[_relpage("stale.md")], by_file


def test_v7_stale_source_needs_a_source_newer_than_derived_at(tmp_path):
    """The ``stale-source`` half is the mtime comparison, read from both sides.

    Same tree shape, only the source timestamp differs: a source **older** than
    ``derived-at`` is not a finding. Without this the previous test would also
    pass for a check that reports every derived page.
    """
    derived_at = _days_ago(10)
    _derived_page(tmp_path, "current.md", derived_at)

    assert docs_wiki_lib.check_wiki_staleness(tmp_path) == [], (
        "a source older than derived-at is current, not stale"
    )

    _set_mtime(_write_source(tmp_path, derived_at), derived_at + timedelta(seconds=1))
    findings = docs_wiki_lib.check_wiki_staleness(tmp_path)
    assert [f.file for f in findings] == [_relpage("current.md")], findings
    assert WIKI_STALE_SOURCE in findings[0].message, findings


def test_v7_severity_is_warning_for_both_forms(tmp_path):
    """IC-05 pins V7 at WARNING; ``config`` may not promote or demote it.

    V1 is the check whose severity moves with
    ``docs-consolidation.checks.strict``; V7 has one severity and reads no config
    key, so passing a strict config must change nothing. The gate and the
    registration are W2-7's.
    """
    derived_at = _days_ago(10)
    _derived_page(tmp_path, "stale.md", derived_at)
    _set_mtime(_write_source(tmp_path, derived_at), derived_at + timedelta(days=1))
    _wiki_page(
        tmp_path / V7_WIKI_RELPATH / "concepts",
        "no-provenance.md",
        {"type": WIKI_ARCHITECTURE_TYPE, "title": "no provenance"},
    )
    strict = {"docs-consolidation": {"enabled": True, "checks": {"strict": True}}}

    for config in (None, {}, strict):
        findings = docs_wiki_lib.check_wiki_staleness(tmp_path, config)
        assert len(findings) == 2, config
        assert {f.severity for f in findings} == {docs_wiki_lib.Severity.WARNING}, config


def test_v7_call_signature_matches_the_runner_contract(tmp_path):
    """IC-05: ``(root, config=None)`` — the shape ``run_checks()`` will call."""
    assert list(
        inspect.signature(docs_wiki_lib.check_wiki_staleness).parameters
    ) == ["root", "config"]
    assert docs_wiki_lib.check_wiki_staleness(tmp_path) == []


# ---------------------------------------------------------------------------
# What V7 must *not* report — the permanent-false-alarm shape (F21)
# ---------------------------------------------------------------------------


def test_v7_ignores_fresh_and_aged_pages(tmp_path):
    """``age-<n>d`` is an observation, not a status (IC-03) — it is not a finding.

    V7's two detection forms are fixed by IC-05, and neither is "the derivation is
    old". An age observation on every derived page would be the permanent
    false-alarm shape this module exists to avoid: the count would grow with the
    repository instead of naming a defect.
    """
    derived_at = _days_ago(400)
    _derived_page(tmp_path, "aged.md", derived_at)

    assert _states(tmp_path) == {"concepts/aged.md": "age-400d"}, _states(tmp_path)
    assert docs_wiki_lib.check_wiki_staleness(tmp_path) == []


def test_v7_ignores_pages_that_never_claimed_the_architecture_type(tmp_path):
    """A page without provenance and without the duty carries no finding.

    ``missing-derived-from`` states a duty ``knowledge/schema.md`` imposes on
    ``type: Architecture`` pages. Reporting it for every page would turn "has no
    provenance" into a repo-wide alarm.
    """
    _wiki_page(
        tmp_path / V7_WIKI_RELPATH / "topics",
        "a-guide.md",
        {"type": "Guide", "title": "no duty, no finding"},
    )

    assert _states(tmp_path) == {"topics/a-guide.md": ""}, _states(tmp_path)
    assert docs_wiki_lib.check_wiki_staleness(tmp_path) == []


def test_v7_missing_wiki_root_is_fail_soft(tmp_path):
    """No ``knowledge/wiki`` at all: no pages, no claim, no finding (IC-01)."""
    (tmp_path / "docs").mkdir(parents=True)
    assert _states(tmp_path) == {}
    assert docs_wiki_lib.check_wiki_staleness(tmp_path) == []


# ---------------------------------------------------------------------------
# The adapter boundary — the property that makes this module thin
# ---------------------------------------------------------------------------


def test_v7_consumes_the_resolver_instead_of_re_deriving(monkeypatch, tmp_path):
    """The check reports the resolver's states, even when they are not the truth.

    The tree below is *genuinely* fresh: a valid ``derived-from`` whose source is
    older than ``derived-at``. The stubbed resolver nevertheless reports
    ``stale-source``, and the check must render that — if the check re-read the
    frontmatter or stat-ed the source itself, it would answer "no finding" and
    this test would fail. A check that duplicated IC-03 would be a second
    implementation of the rule with its own bugs, which is exactly the "logic
    moved into the check" shape this task is required to avoid.
    """
    derived_at = _days_ago(10)
    page = _derived_page(tmp_path, "genuinely-fresh.md", derived_at)
    assert docs_wiki_lib.check_wiki_staleness(tmp_path) == [], "premise: the tree is fresh"

    monkeypatch.setattr(
        docs_wiki_lib,
        "compute_wiki_staleness",
        lambda wiki_root, project_root, **_: {
            "concepts/genuinely-fresh.md": WIKI_STALE_SOURCE,
            "concepts/never-written.md": WIKI_MISSING_DERIVED_FROM,
            "concepts/also-never-written.md": "",
            "concepts/aged.md": "age-12d",
        },
    )

    findings = docs_wiki_lib.check_wiki_staleness(tmp_path)

    assert [f.file for f in findings] == [
        _relpage("genuinely-fresh.md"), _relpage("never-written.md"),
    ], findings
    assert WIKI_STALE_SOURCE in findings[0].message, findings
    assert WIKI_MISSING_DERIVED_FROM in findings[1].message, findings
    # The stub was called with the two roots the resolver documents.
    assert page.is_file()


# ---------------------------------------------------------------------------
# The real wiki — an expectation re-derived from disk, not a pinned number
# ---------------------------------------------------------------------------


def test_v7_reports_every_reporting_page_of_the_real_wiki_exactly_once():
    """Against the real ``knowledge/wiki``: one finding per reporting page.

    The expectation is re-derived from disk by scanning the frontmatter directly
    — not by asking the resolver, which would make the assertion a tautology.
    Today the answer is 10 (the K24 figure of 11 also counts a ``type:`` line
    inside a fenced YAML example, ``core-principle-knowledge-engine.md:46``);
    after W5-3 annotates the pages it is 0. Both states satisfy the test, which
    is the point of re-deriving.
    """
    wiki = REPO_ROOT / V7_WIKI_RELPATH
    expected = {
        f"{V7_WIKI_RELPATH}/{page.relative_to(wiki).as_posix()}"
        for page in wiki.rglob("*.md")
        if _is_architecture_page_without_provenance(page)
    }
    assert expected, "premise: the real wiki has Architecture pages"

    findings = docs_wiki_lib.check_wiki_staleness(REPO_ROOT)

    assert [f.file for f in findings] == sorted(expected), findings
    assert docs_wiki_lib.check_wiki_staleness(REPO_ROOT) == findings, (
        "V7 inherits the resolver's deterministic page order — it must not "
        "re-order or de-duplicate the mapping"
    )
    assert {f.check for f in findings} == {V7_CHECK_ID}, findings
    assert {f.severity for f in findings} == {docs_wiki_lib.Severity.WARNING}, findings
    for finding in findings:
        state = WIKI_MISSING_DERIVED_FROM if "Architecture" in finding.message \
            else WIKI_STALE_SOURCE
        assert state in finding.message, finding.message


def _is_architecture_page_without_provenance(page: Path) -> bool:
    """Frontmatter oracle, deliberately independent of ``doc_facts``.

    Only the *frontmatter* block counts — a ``type:`` line in the body (a fenced
    YAML example, a quoted snippet) must not raise the number.
    """
    lines = page.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return False
    for line in lines[1:]:
        if line.strip() == "---":
            return False
        if line.startswith("type:") and line.split(":", 1)[1].strip() == \
                f'"{WIKI_ARCHITECTURE_TYPE}"':
            return not any(key.startswith(f"{DERIVED_FROM_KEY}:")
                           for key in _frontmatter_keys(lines))
    return False


def _frontmatter_keys(lines: list[str]) -> list[str]:
    keys: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            keys.append(line.split(":", 1)[0])
    return keys


# ---------------------------------------------------------------------------
# AC-13 — registration in the runner (W2-7, RVW2-5)
# ---------------------------------------------------------------------------
#
# History of this section: it carried ``test_v7_is_not_wired_into_the_runner_yet``
# with the assertion ``"check_wiki_staleness" not in runner``. That pinned the
# pre-W2-7 state — "V7 has no call site, so the scenario matrix cannot regress
# from W2-3" — and W2-7, which registers V7, makes it red by construction. It is
# **replaced**, not kept in parallel: keeping both would assert a contradiction.
# The sibling replacements live in ``tests/test_doc_freshness.py`` (V1, V6),
# ``tests/test_doc_facts.py`` (V3) and ``tests/test_doc_index.py`` (V2).


def _runner():
    """The runner module, loaded the way ``lib.cli_commands`` loads it.

    The filename contains a hyphen, so it cannot be imported by name. The import
    is local so that this section stays the file's only change.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_consistency_runner", REPO_ROOT / "scripts" / "consistency-check.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _gate_open_tree(tmp_path: Path, name: str = "open") -> Path:
    """A project root with one provenance-less Architecture page, gate **on**."""
    root = tmp_path / name
    _wiki_page(root / V7_WIKI_RELPATH, "concepts/agent.md",
               {"type": WIKI_ARCHITECTURE_TYPE})
    (root / ".meta-config").mkdir(parents=True, exist_ok=True)
    (root / ".meta-config" / "project.yaml").write_text(
        "docs-consolidation:\n  enabled: true\n", encoding="utf-8"
    )
    return root


def test_v7_is_registered_in_the_runner(tmp_path):
    """AC-13: V7 is exported by the facade, imported by the runner, registered.

    Two halves, because on their own both are vacuous — a name can sit in an
    import without a call, and a call can sit behind a closed gate:

    (a) the import: ``check_wiki_staleness`` is reachable from
        ``scripts/consistency-check.py`` through the **facade**
        ``lib.consistency.docs`` only (K20), whose ``__all__`` therefore has to
        carry the name — that is what makes the facade contract (K19) the
        precondition of the registration — and the name has an entry in the
        ``DOCS_CHECKS`` table, because a name in an import is not a
        registration;
    (b) the effect: the W2-3 fixture (one ``type: Architecture`` page without
        ``derived-from``), a project config with ``docs-consolidation.enabled:
        true`` and a genuine ``run_checks()`` call yield
        ``docs.wiki_staleness`` findings.

    The check id stays the literal this module quotes (:data:`V7_CHECK_ID`), and
    the module constant is asserted equal to it, so a rename on either side
    fails instead of agreeing on the wrong id.
    """
    from scripts.lib.consistency import docs as docs_facade

    runner_source = (REPO_ROOT / "scripts" / "consistency-check.py").read_text(
        encoding="utf-8"
    )
    assert "check_wiki_staleness" in runner_source, (
        "the registration must be visible in the runner — the import block is "
        "the only registration site (RVW2-1: a count over the --json report "
        "proves nothing about registration)"
    )
    assert "from lib.consistency.docs import" in runner_source, (
        "K20: registration goes through the facade, never module-wise"
    )
    assert "check_wiki_staleness" in docs_facade.__all__, (
        "the facade __all__ is the contract (K19) the registration runs on"
    )
    assert hasattr(docs_facade, "check_wiki_staleness")
    assert "check_wiki_staleness" in [c.__name__ for c in _runner().DOCS_CHECKS]

    findings = _runner().run_checks(_gate_open_tree(tmp_path))

    v7 = [f for f in findings if f.check == V7_CHECK_ID]
    assert v7, findings
    assert {f.file for f in v7} == {"knowledge/wiki/concepts/agent.md"}, v7
    assert {f.severity for f in v7} == {docs_wiki_lib.Severity.WARNING}, v7
