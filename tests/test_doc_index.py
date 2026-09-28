"""AC-12 (IC-05, spec §5.1.1) — V2 ``check_docs_index_completeness``, and the V4 generalisation.

Both checks answer the question of the *documentation-build* family (Spec §4.1,
U-1/K18): *is the documentation structure complete and curated?* They read two
different **targets**, which is why they share a module but not a question:

* **V2** ``check_docs_index_completeness`` (AC-12, IC-05) — every in-scope
  ``docs/**/*.md`` must appear in ``docs/INDEX.md``, the **generated** index. It
  is **scheduled red** until W3-6 creates that file (Spec §10, point 5); that is
  a term with an owner, not a defect of the check.
* **V4** ``check_readme_docs_index`` — since W2-6 (**E-5**) it asks whether every
  ``docs/<category>/`` directory the README's ``Documentation Index`` section
  *declares* is **real** and is **represented by a link** in that section. The
  severity (ERROR), the check id (``docs.readme_index``), the ``file``
  (``README.md``) and the one-argument signature are pinned by IC-05 and
  asserted here.

The module under test is ``scripts.lib.consistency.docs_index`` for V2 and
``scripts.lib.consistency.docs_links`` for V4 — the facade re-export of
``check_docs_index_completeness`` is **W2-7's** write-set (K20/K46), so
visibility through ``docs.py`` is deliberately *not* asserted here: a test that
pins it would be red until W2-7 and would make this file a dependency of a task
that does not own it.

**"In scope" means something different for the two checks, and neither meaning is
implicit.** V2's scope is a *page* rule: every non-archived ``docs/**/*.md``
except ``docs/INDEX.md`` itself must be listed in the generated index.
``docs/INDEX.md`` is the index under test — indexing the index would make the
check unsatisfiable by construction, since a generated file cannot contain its
own path before it exists — and ``archive/``/``_archive/`` hold retired documents
by definition. V4's scope is a *category* rule (**E-5**): it never counts pages.
A category that the README names in its index section has to be a real directory
with at least one ``.md`` **page** linked from that section — inline ``](…)`` or
reference definition, but never an image and never a URL; pages *below* a
represented category are V2's business, and
``test_v4_unlinked_pages_below_a_declared_category_are_not_findings`` pins that
separation rather than leaving it to a passing assertion.

**V2 reads "tracked" as "present in the tree".** The spec's word is *getrackt*,
and this check does not shell out to git: the runner must stay stdlib-only and
must behave identically in a fixture directory that is not a repository. Every
page a checkout would track is a file on disk, and a file on disk that the index
does not mention is exactly the drift the check exists to report.
"""

from __future__ import annotations

import inspect
import re
import time
from pathlib import Path

from scripts.lib.consistency import docs_index as docs_index_lib
from scripts.lib.consistency import docs_links as docs_links_lib

REPO_ROOT = Path(__file__).resolve().parent.parent


V2_CHECK_ID = "docs.docs_index_completeness"

V4_CHECK_ID = "docs.readme_index"


INDEX_RELPATH = "docs/INDEX.md"
README_RELPATH = "README.md"

ARCHIVE_DIRNAMES = ("archive", "_archive")
"""Directory names IC-05 excludes from V2's page scope (V4 has no page scope)."""

V4_INDEX_HEADING = "Documentation Index"
"""The ``##`` heading whose text V4 extracts its region from (E-5)."""

_PAGE = "# page\n"


def _tree(root: Path, relpath: str, body: str) -> Path:
    """Write ``relpath`` below ``root``, creating parents; return ``root``."""
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return root


def _index_readme(*body: str) -> str:
    """A README whose ``## Documentation Index`` section carries exactly ``body``.

    The trailing ``## DoD Presets`` heading is what closes the region, so a
    fixture that declares nothing is a *present but empty* region — the
    distinction from a *missing* section is the fail-closed rule (K65) and is
    what keeps the empty-section assertions from passing vacuously.
    """
    return (f"# Project\n\n## {V4_INDEX_HEADING}\n\n"
            + "\n".join(body) + "\n\n## DoD Presets\n")


def _declares(category: str) -> str:
    """A subsection naming ``docs/<category>/`` but linking no page of it."""
    return f"### A Category (`{category}`)\n\nProse that names the directory.\n"


def _declares_with_link(category: str, page: str = "overview.md") -> str:
    """A subsection naming ``docs/<category>/`` **and** linking a page of it."""
    return (f"### A Category (`{category}`)\n\n"
            f"- **[Overview]({category}{page})**: the page that represents it.\n")


def _declares_with_refdef(category: str, page: str = "overview.md") -> str:
    """A subsection naming ``docs/<category>/``, linked by **reference definition**.

    D1 needs the form pinned apart from the inline one, so it gets its own helper.
    """
    return (f"### A Category (`{category}`)\n\n"
            f"- **[Overview][ov]**\n\n[ov]: {category}{page}\n")


def _v2_findings(root: Path) -> list:
    return docs_index_lib.check_docs_index_completeness(root)


def _v4_findings(root: Path) -> list:
    return docs_links_lib.check_readme_docs_index(root)


def _categories(findings: list) -> list[str]:
    """The category each V4 finding names, in report order.

    V4 reports **categories**, so the category is the contract's unit of
    identity here too; parsing it out of the message is what makes an
    accidental regression to a per-page report visible in a single assertion.
    """
    return [finding.message.split("'")[1] for finding in findings]


def _pages(root: Path) -> list[str]:
    """The page paths V2 reports, sorted — the report order is part of the contract."""
    return sorted(f.file for f in _v2_findings(root))


def test_v2_missing_page(tmp_path):
    """AC-12: a page absent from ``docs/INDEX.md`` is an ERROR.

    The acceptance criterion names ``test_v2_missing_page`` and requires a
    ``Finding(severity=ERROR, check="docs.docs_index_completeness")``; the
    fixture is nested two levels deep so the test would also pass against a
    check that only globs the top level of ``docs/``.
    """
    root = _tree(tmp_path, "docs/guides/setup/instantiate-project.md", "# Setup\n")
    _tree(root, INDEX_RELPATH, "# INDEX\n\n- [CLI](api/cli-reference.md)\n")

    findings = _v2_findings(root)

    assert [(f.check, f.severity, f.file) for f in findings] == [
        (V2_CHECK_ID, docs_index_lib.Severity.ERROR,
         "docs/guides/setup/instantiate-project.md")
    ], findings


def test_v2_accepts_the_uniform_runner_signature():
    """The runner calls every check as ``check(root, config)``; V2 opts out of reading config."""
    assert list(inspect.signature(
        docs_index_lib.check_docs_index_completeness).parameters) == ["root", "config"]


def test_v2_indexed_page_is_not_reported(tmp_path):
    """The positive case: a page the index *does* mention produces no finding."""
    root = _tree(tmp_path, "docs/guides/setup/instantiate-project.md", "# Setup\n")
    _tree(root, INDEX_RELPATH,
          "# INDEX\n\n- [Setup](guides/setup/instantiate-project.md)\n")

    assert _v2_findings(root) == []


def test_v2_does_not_index_the_index(tmp_path):
    """``docs/INDEX.md`` is the target, not a page — it must never report itself.

    Without this exclusion a generated index would be permanently unfixable: it
    would have to list its own path, which it cannot know before it is written.
    """
    root = _tree(tmp_path, INDEX_RELPATH, "# INDEX\n")
    _tree(root, "docs/guides/page.md", "# Page\n")

    assert _pages(root) == ["docs/guides/page.md"]


def test_v2_ignores_archived_pages(tmp_path):
    """IC-05 excludes ``archive/`` and ``_archive/``: retired pages are not unindexed.

    Both spellings are exercised because the repository contains both
    (``docs/concepts/archive/``, ``docs/plans/archive/``), and a check that
    handled only one would look correct on either tree alone.
    """
    root = _tree(tmp_path, "docs/plans/archive/retired-plan.md", "# Retired\n")
    _tree(root, "docs/guides/archive/retired-guide.md", "# Retired\n")
    _tree(root, "docs/specs/_archive/retired-spec.md", "# Retired\n")
    _tree(root, INDEX_RELPATH, "# INDEX\n")

    assert _v2_findings(root) == []


def test_v2_missing_index_reports_every_page(tmp_path):
    """A missing index means every page is unindexed — the check stays decidable.

    Returning an empty list here would make the check silently vacuous exactly
    when the drift is largest, which is the state W3-6 resolves.
    """
    root = _tree(tmp_path, "docs/guides/page.md", "# Page\n")
    _tree(root, "docs/api/cli-reference.md", "# CLI\n")

    assert _pages(root) == ["docs/api/cli-reference.md", "docs/guides/page.md"]


def test_v2_api_subset_remains_a_real_subset(tmp_path):
    """The pre-W2 ``docs/api/*.md`` scope is a genuine subset of V2, not a separate rule.

    IC-05 states the subset must stay a *real* subset, so this is pinned
    explicitly instead of being implied by the other cases: an API page missing
    from the index is still a finding after the generalisation.
    """
    root = _tree(tmp_path, "docs/api/cli-reference.md", "# CLI\n")
    _tree(root, INDEX_RELPATH, "# INDEX\n\n- [Guides](guides/page.md)\n")

    assert _pages(root) == ["docs/api/cli-reference.md"]


def test_v2_accepts_the_ic10_canonical_link_form(tmp_path):
    """IC-10 renders the index as ``- [Title](<path relative to docs/>)``.

    The generated form is ``docs/``-**relative** (``(guides/setup/x.md)``), which
    differs from the project-root spelling V2 compares against. Both must count
    as indexed, otherwise the check would report every page of a correctly
    generated index — 100 % false positives against the canonical format the
    W3-6 generator is specified to produce.
    """
    root = _tree(tmp_path, "docs/guides/setup/instantiate-project.md", "# Setup\n")
    _tree(root, "docs/architecture/01-layer-model.md", "# Layer\n")
    _tree(root, INDEX_RELPATH, (
        "# Documentation Index\n\n"
        "## guides\n"
        "- [Instantiate Project](guides/setup/instantiate-project.md)\n\n"
        "## architecture\n"
        "- [Layer Model](architecture/01-layer-model.md)\n"
    ))

    assert _v2_findings(root) == []


def test_v2_accepts_the_project_root_spelling_too(tmp_path):
    """The other spelling — a project-root-relative path — counts as indexed as well.

    IC-10 fixes the generated form, but a human-written or transitional index may
    use the root spelling; both name the same page, and V2 must not force one.
    """
    root = _tree(tmp_path, "docs/guides/page.md", "# Page\n")
    _tree(root, INDEX_RELPATH, "# INDEX\n\n- `docs/guides/page.md`\n")

    assert _v2_findings(root) == []


def test_v2_does_not_count_an_anchor_or_a_foreign_scheme(tmp_path):
    """A link to a *section* of a page still indexes the page; an external URL does not.

    ``docs/guides/page.md#usage`` names the same page, while
    ``https://example.invalid/docs/guides/page.md`` names a different machine's
    file and must not silence the finding.
    """
    anchored = _tree(tmp_path, "docs/guides/page.md", "# Page\n")
    _tree(anchored, INDEX_RELPATH, "# INDEX\n\n- [Usage](guides/page.md#usage)\n")
    assert _v2_findings(anchored) == []

    foreign = _tree(tmp_path / "foreign", "docs/guides/page.md", "# Page\n")
    _tree(foreign, INDEX_RELPATH,
          "# INDEX\n\n- [Ext](https://example.invalid/docs/guides/page.md)\n")
    assert _pages(foreign) == ["docs/guides/page.md"]


def test_v2_absent_docs_tree_is_fail_soft(tmp_path):
    """No ``docs/`` at all is not drift — a project without docs is not broken by V2."""
    root = _tree(tmp_path, "README.md", "# readme\n")

    assert _v2_findings(root) == []


def test_v2_reports_pages_sorted_and_once(tmp_path):
    """Deterministic order, no duplicates: the report is a diff, not a stream."""
    root = _tree(tmp_path, "docs/zeta.md", "# z\n")
    _tree(root, "docs/alpha.md", "# a\n")
    _tree(root, "docs/mid/page.md", "# m\n")
    _tree(root, INDEX_RELPATH, "# INDEX\n")

    findings = _v2_findings(root)

    assert [f.file for f in findings] == [
        "docs/alpha.md", "docs/mid/page.md", "docs/zeta.md"]
    assert len({f.file for f in findings}) == 3


def test_v2_ignores_non_markdown_files(tmp_path):
    """IC-05 bounds V2 to ``docs/**/*.md``; a ``.yaml.example`` is not a page.

    RVW2-8 corrected exactly this in the plan: the W5-2 move of
    ``docs/guides/configs/project.yaml.example`` is irrelevant to V2.
    """
    root = _tree(tmp_path, "docs/guides/configs/project.yaml.example", "a: b\n")
    _tree(root, INDEX_RELPATH, "# INDEX\n")

    assert _v2_findings(root) == []


def test_v2_finding_names_the_index_in_its_suggestion(tmp_path):
    """The remediation points at the generator's output, not at an ad-hoc README edit.

    ``docs/INDEX.md`` is 100 % generated (IC-10, W3-6), so a suggestion telling
    the author to hand-edit it would be wrong advice.
    """
    root = _tree(tmp_path, "docs/guides/page.md", "# Page\n")
    _tree(root, INDEX_RELPATH, "# INDEX\n")

    (finding,) = _v2_findings(root)

    assert INDEX_RELPATH in finding.suggestion
    assert "sync" in finding.suggestion.lower()


# ---------------------------------------------------------------------------
# V4 test set — replaced wholesale by **E-5** (K61 / RVW-7-03, Plan W2-6).
#
# The seven tests below this anchor are the replacements. They were **not**
# adapted from the pre-E-5 set: every one of those seven pinned the *per-page*
# reading that E-5 removes, so carrying an assertion over would have preserved
# the 191/193 blocker under a new name. The mapping, kept here so the history is
# not lost with the code (the plan's §"Akzeptanz V4" carries the same table):
#
#   R1  test_v4_keeps_signature_and_severity
#         -> test_v4_signature_is_one_argument_root_only            (signature)
#         -> test_v4_declared_category_without_link_is_one_error    (severity)
#   R2  test_v4_generalized_to_the_whole_docs_tree
#         -> test_v4_declared_category_needs_a_link                  (acceptance a)
#   R3  test_v4_api_subset_still_fires
#         -> test_v4_declared_category_must_exist                    (acceptance b)
#         -> test_v4_declared_category_with_link_is_silent
#   R4  test_v4_ignores_archived_pages
#         -> test_v4_archived_pages_are_not_declared_categories
#   R5  test_v4_reports_each_page_once
#         -> test_v4_reports_each_unrepresented_category_once
#   R6  test_v4_finding_names_the_page_and_readme
#         -> test_v4_finding_names_the_category_and_readme
#   R7  test_real_repo_pages_are_reported_only_by_v2_until_w3_6
#         -> test_real_repo_readme_index_has_exactly_one_unrepresented_category
#
# Kept and extended rather than replaced: test_v4_absent_docs_tree_is_fail_soft,
# joined by the two precedence tests (K65). Added for the extraction rule:
# test_v4_declares_seven_categories_including_architecture_from_link_only
# (K64), and for the scope proof:
# test_v4_unlinked_pages_below_a_declared_category_are_not_findings.
#
# **Fix-Runde 1 (Review-Iteration 1) — vier Härtungslücken, vier neue Tests:**
#   D1  reference definitions counted only as declarations, never as links →
#       test_v4_reference_definition_counts_as_a_link
#   D2  no left boundary, so a URL path declared a category →
#       test_v4_url_prefix_does_not_declare_a_category
#   D3  an image target satisfied condition (b) →
#       test_v4_image_target_does_not_represent_a_category
#   D4  a non-decodable README raised out of the check →
#       test_v4_undecodable_readme_is_one_finding
# The E-5 scope itself is untouched by that round; only the link recognition
# and the read guard were hardened.
# ---------------------------------------------------------------------------


def test_v4_signature_is_one_argument_root_only():
    """R1a: IC-05 pins the parameter list, and E-5 must not have touched it.

    The ``(root, config=None)`` form belongs to the **nine new** V-checks
    (K59 / RVW-7-01), not to this pre-existing one. Pinned by introspection
    because an added required parameter would break the call in
    ``run_checks()`` silently, at import of the call site rather than here.

    This is the **signature half** of the former
    ``test_v4_keeps_signature_and_severity``; the severity half became its own
    test, because the two pin different contracts and bundling them let the
    vacuous severity half hide behind a true signature half.
    """
    assert list(inspect.signature(
        docs_links_lib.check_readme_docs_index).parameters) == ["root"]


def test_v4_declared_category_without_link_is_one_error(tmp_path):
    """R1b, severity half: a category the section declares but does not link ⇒ 1 ERROR.

    The severity, the check id and the ``file`` are the IC-05 pin. The unit is
    the **category**, so the fixture links a page that exists and still reports:
    what is missing is the *representation of the declared category*, not a page.
    """
    root = _tree(tmp_path, "docs/se-cascade/overview.md", _PAGE)
    _tree(root, README_RELPATH, _index_readme(_declares("docs/se-cascade/")))

    findings = _v4_findings(root)

    assert len(findings) == 1, findings
    finding = findings[0]
    assert (finding.check, finding.severity, finding.file) == (
        V4_CHECK_ID, docs_index_lib.Severity.ERROR, README_RELPATH)


def test_v4_declared_category_needs_a_link(tmp_path):
    """R2 / acceptance (a): a declared category with a real directory needs a link.

    Existence alone is not representation. This is the case the real tree runs
    into with ``docs/se-cascade/``: the directory is there, the subsection names
    it, and nothing links a page of it.
    """
    root = _tree(tmp_path, "docs/guides/setup/instantiate-project.md", _PAGE)
    _tree(root, README_RELPATH, _index_readme(_declares("docs/guides/")))

    findings = _v4_findings(root)

    assert len(findings) == 1, findings
    assert "docs/guides/" in findings[0].message
    assert "links no page" in findings[0].message


def test_v4_declared_category_must_exist(tmp_path):
    """R3 / acceptance (b): a category that is named but not on disk ⇒ ERROR.

    A link into a directory that does not exist is *not* a V3 finding — V3
    resolves file targets, and this target is a category. It is a V4 finding,
    because the README promises a category the tree does not have.
    """
    root = _tree(tmp_path, "docs/guides/page.md", _PAGE)
    _tree(root, README_RELPATH,
          _index_readme(_declares_with_link("docs/nonexistent/")))

    findings = _v4_findings(root)

    assert len(findings) == 1, findings
    assert "docs/nonexistent/" in findings[0].message
    assert "does not exist" in findings[0].message


def test_v4_declared_category_with_link_is_silent(tmp_path):
    """R3, positive half: both conditions met ⇒ silent.

    The counterpart to the three tests above. Without it, "one ERROR" could be
    satisfied by a check that fires unconditionally, and the fail-closed
    precedence below would be untestable.
    """
    root = _tree(tmp_path, "docs/guides/page.md", _PAGE)
    _tree(root, README_RELPATH,
          _index_readme(_declares_with_link("docs/guides/")))

    assert _v4_findings(root) == []


def test_v4_archived_pages_are_not_declared_categories(tmp_path):
    """R4: retired pages never become categories.

    Under the per-page reading this needed an ``archive/`` exclusion. Under
    E-5 the exclusion is *structural*: V4 only ever looks at the index region,
    and an archived page that no subsection names is not a declared category at
    all. The assertion below would also pass for a missing region — so the
    region is asserted **present** in the same body, which is what keeps this
    from being a fail-closed test wearing an archive test's name.
    """
    root = _tree(tmp_path, "docs/plans/archive/retired.md", _PAGE)
    _tree(root, "docs/guides/_archive/retired.md", _PAGE)
    readme = _tree(root, README_RELPATH, _index_readme())

    assert docs_links_lib._v4_index_region(
        readme.joinpath(README_RELPATH).read_text(encoding="utf-8")) is not None
    assert _v4_findings(root) == []


def test_v4_reports_each_unrepresented_category_once(tmp_path):
    """R5: the once-count runs over **categories**, not pages.

    Three categories are declared, one of them is represented, and the two
    unrepresented ones are reported once each. Asserting on the category list
    rather than on ``len(...) == 2`` alone is what distinguishes "once per
    category" from "once per page" — under the old reading the two guide pages
    below would have produced findings with the same count.
    """
    root = _tree(tmp_path, "docs/guides/one.md", _PAGE)
    _tree(root, "docs/api/two.md", _PAGE)
    _tree(root, "docs/ui/three.md", _PAGE)
    _tree(root, README_RELPATH, _index_readme(
        _declares_with_link("docs/guides/"),
        _declares("docs/api/"),
        _declares("docs/ui/")))

    findings = _v4_findings(root)

    assert _categories(findings) == ["docs/api/", "docs/ui/"]
    assert len({f.check for f in findings}) == 1
    for finding in findings:
        assert finding.severity == docs_index_lib.Severity.ERROR
        assert finding.file == README_RELPATH


def test_v4_finding_names_the_category_and_readme(tmp_path):
    """R6: the message names the **category**; the ``file`` names the README.

    The page path is deliberately absent from the message. A finding that named
    a page would be a per-page finding, and the whole point of E-5 is that a
    page below a represented category is not this check's business.
    """
    root = _tree(tmp_path, "docs/se-cascade/overview.md", _PAGE)
    _tree(root, README_RELPATH, _index_readme(_declares("docs/se-cascade/")))

    (finding,) = _v4_findings(root)

    assert finding.file == README_RELPATH
    assert "docs/se-cascade/" in finding.message
    assert "docs/se-cascade/" in finding.suggestion
    assert README_RELPATH in finding.message
    assert "overview.md" not in finding.message


def test_v4_absent_docs_tree_is_fail_soft(tmp_path):
    """Kept and extended: no ``docs/`` tree ⇒ ``[]``, and the guard comes **first**.

    The first fixture has a README *with* an index section, so ``[]`` is the
    fail-soft guard rather than an empty region. The second has neither a README
    nor a ``docs/`` tree — under the fail-closed rule a missing README alone
    would be one finding, so ``[]`` here is only reachable because the
    ``docs/``-missing guard is evaluated **before** it (K65 / RVW-7-07).
    """
    declared = _tree(tmp_path, README_RELPATH,
                     _index_readme(_declares_with_link("docs/guides/")))
    assert _v4_findings(declared) == []

    bare = _tree(tmp_path / "bare", "src/app.py", "x = 1\n")
    assert not bare.joinpath(README_RELPATH).exists()
    assert _v4_findings(bare) == []


def test_v4_docs_tree_without_index_section_is_one_finding(tmp_path):
    """Precedence, first half: ``docs/`` present + no index heading ⇒ exactly **one**.

    Fail-closed, and one finding rather than the sum over pages: without a
    section there are no declared categories, so the defect is a single
    "README declares nothing" and not N per-page complaints.
    """
    root = _tree(tmp_path, "docs/guides/page.md", _PAGE)
    _tree(root, README_RELPATH, "# Project\n\n## DoD Presets\n\nNo index here.\n")

    findings = _v4_findings(root)

    assert len(findings) == 1, findings
    finding = findings[0]
    assert (finding.check, finding.severity, finding.file) == (
        V4_CHECK_ID, docs_index_lib.Severity.ERROR, README_RELPATH)
    assert V4_INDEX_HEADING in finding.message


def test_v4_readme_missing_with_docs_tree_is_one_finding(tmp_path):
    """Precedence, second half: a ``docs/`` tree but no ``README.md`` ⇒ exactly **one**.

    The mirror of :func:`test_v4_absent_docs_tree_is_fail_soft`. The two guards
    are only distinguishable as a *pair*: whichever ran first would decide both
    fixtures, and running fail-closed first would make the fail-soft case red.
    """
    root = _tree(tmp_path, "docs/guides/page.md", _PAGE)

    assert not root.joinpath(README_RELPATH).exists()

    findings = _v4_findings(root)

    assert len(findings) == 1, findings
    assert (findings[0].check, findings[0].severity, findings[0].file) == (
        V4_CHECK_ID, docs_index_lib.Severity.ERROR, README_RELPATH)


def test_v4_reference_definition_counts_as_a_link(tmp_path):
    """D1: a category linked **only** by a reference definition is represented.

    ``[ov]: docs/guides/setup/x.md`` is a link. The plan's acceptance (b) says
    "at least one link" and binds no *form*, so binding it to the inline
    ``](…)`` spelling turned a represented category into a false ERROR.

    The result is non-empty on purpose: ``docs/api/`` is declared and unlinked
    and must still be reported, so ``docs/guides/`` being silent is a real
    outcome of the rule rather than a check that reports nothing.
    """
    root = _tree(tmp_path, "docs/guides/setup/x.md", _PAGE)
    _tree(root, "docs/api/other.md", _PAGE)
    _tree(root, README_RELPATH, _index_readme(
        _declares_with_refdef("docs/guides/", "setup/x.md"),
        _declares("docs/api/")))

    findings = _v4_findings(root)

    assert _categories(findings) == ["docs/api/"], findings
    assert "docs/guides/" not in _categories(findings)


def test_v4_image_target_does_not_represent_a_category(tmp_path):
    """D3: an embedded image is not an index entry — it must not satisfy (b).

    ``![chart](docs/guides/chart.png)`` used to represent ``docs/guides/`` on its
    own. A figure inside a list item is not an entry in the documentation index,
    and V4 is about the *representation of a category*, not about whether the
    README touches a file below it.

    The rule is **structural** (a ``!`` before the link), not extension-based,
    and the difference is measured rather than assumed: ``docs/ui/`` is
    represented in the real README by ``](docs/ui/agent-graph.html)`` and
    ``](docs/ui/admin-ui.html)``, so an ``.md``-only rule would report a category
    the README genuinely links and move the tree value from 1 to 2.

    Both halves are non-vacuous: ``docs/guides/`` must be reported (the image did
    not count) while ``docs/api/`` stays silent (a real link did count).
    """
    root = _tree(tmp_path, "docs/guides/page.md", _PAGE)
    _tree(root, "docs/api/page.md", _PAGE)
    _tree(root, README_RELPATH, _index_readme(
        "### A Category (`docs/guides/`)\n\n![chart](docs/guides/chart.png)\n",
        _declares_with_link("docs/api/")))

    findings = _v4_findings(root)

    assert _categories(findings) == ["docs/guides/"], findings
    assert "docs/api/" not in _categories(findings)


def test_v4_undecodable_readme_is_one_finding(tmp_path):
    """D4: a README that is not decodable is fail-closed, not an exception.

    ``UnicodeDecodeError`` derives from ``ValueError``, not from ``OSError``, so
    the read guard let it escape the check — a crash out of a report, where the
    documented rule promises exactly one finding. The fixture writes raw bytes,
    which ``_tree`` cannot produce.

    Non-vacuous by construction: the single finding is pinned by check id,
    severity and ``file``, so an empty result cannot satisfy it.
    """
    root = _tree(tmp_path, "docs/guides/page.md", _PAGE)
    (root / README_RELPATH).write_bytes(
        f"## {V4_INDEX_HEADING}\n\ndefekt: \xff\n".encode("latin-1"))

    findings = _v4_findings(root)

    assert len(findings) == 1, findings
    finding = findings[0]
    assert (finding.check, finding.severity, finding.file) == (
        V4_CHECK_ID, docs_index_lib.Severity.ERROR, README_RELPATH)


def test_v4_url_prefix_does_not_declare_a_category(tmp_path):
    """D2: a URL path is not a declaration — while a **code span** still is.

    The scan had no left boundary, so ``https://x.invalid/docs/spam/a.md``
    declared a category ``spam`` that exists in no checkout, producing a false
    ERROR on a category the project never claimed.

    This body pins **both** sides of the one rule, because they pull in opposite
    directions. ``docs/guides/`` is declared by a **code span alone**
    (`` `docs/guides/` ``, exactly how the real README declares six of its
    seven), and it **must** appear in the result; ``docs/spam/`` comes from a
    URL and **must not**. A filter blunt enough to kill the URL would also kill
    the code spans and break the K64 count of 7 — that is the trap this test
    exists to close, and
    :func:`test_v4_declares_seven_categories_including_architecture_from_link_only`
    pins the count on the real tree.
    """
    root = _tree(tmp_path, "docs/guides/page.md", _PAGE)
    _tree(root, README_RELPATH, _index_readme(
        "### A Category (`docs/guides/`)\n\n"
        "Mirror: https://x.invalid/docs/spam/a.md\n"))

    findings = _v4_findings(root)

    assert _categories(findings) == ["docs/guides/"], findings
    assert "docs/spam/" not in _categories(findings)


def test_v4_scheme_and_host_prefixes_do_not_declare_a_category(tmp_path):
    """F-3: the remote filter is a **grammar**, not a list of the schemes D2 knew.

    D2 rejected only ``://`` forms, so ``//cdn.invalid/docs/spam/a.md``,
    ``www.example.com/docs/spam/a.md`` and ``mailto:docs/spam/a`` all declared a
    category ``spam``. V3 already classifies inertness with a *scheme grammar*
    (``V3_SCHEME_RE``) instead of an allowlist, and V4 now follows that pattern:
    scheme, protocol-relative ``//``, or host marker ``www.``.

    All five spellings appear in the one region, and ``docs/guides/`` is declared by a
    **code span** in the same breath — the K64 counter-requirement, so a filter blunt
    enough to kill the remote forms would kill the code spans and break the pinned 7.
    """
    root = _tree(tmp_path, "docs/guides/page.md", _PAGE)
    _tree(root, README_RELPATH, _index_readme(
        "### A Category (`docs/guides/`)\n\n"
        "- absolute: https://x.invalid/docs/spam/a.md\n"
        "- protocol-relative: //cdn.invalid/docs/spam/a.md\n"
        "- host-like: www.example.com/docs/spam/a.md\n"
        "- opaque scheme: mailto:docs/spam/a\n"
        "- ftp is already covered: ftp://x.invalid/docs/spam/a.md\n"
        "- in a link: ](//x.invalid/docs/spam/a.md)\n"))

    findings = _v4_findings(root)

    assert _categories(findings) == ["docs/guides/"], findings
    assert "docs/spam/" not in _categories(findings)


def test_v4_url_in_a_heading_is_filtered_in_both_readings():
    """F-2: the heading-only foil applies the same remote filter as the full reading.

    Mutant M-D2b removed the filter from the foil *only* and the suite still reported
    **34 passed** — the docstring's promise that the two readings "differ by *heading*,
    never by disagreeing about what a mention is" was untested. Here a heading *and*
    the prose below it name the same remote path, so the full reading and the foil must
    agree: neither may yield ``docs/spam/``.

    Non-vacuous in the same body: a code-span category in a *second* heading must still
    come back, so the assertion cannot pass by the foil returning nothing at all.
    """
    region = ("### See https://x.invalid/docs/spam/a.md\n\n"
              "Mirror: https://x.invalid/docs/spam/b.md\n\n"
              "### Guides (`docs/guides/`)\n\nProse.\n")

    full = docs_links_lib._v4_declared_categories(region)
    headings = docs_links_lib._v4_declared_heading_categories(region)

    assert "spam" not in full, full
    assert "spam" not in headings, headings
    assert full == ["guides"], full
    assert headings == ["guides"], headings


def test_v4_extraction_scales_linearly_not_quadratically():
    """F-1: the extraction is O(n + m log n), not the O(n·m) D2 left behind.

    D2's remote test located the token start with one backward scan per boundary
    character per match — nine scans, eight typically running to position 0 — which
    is quadratic, on a check that runs on *every* ``consistency-check.py`` invocation
    once W3-6 generates ``docs/INDEX.md``. A functional test cannot see that: the
    mutant is *behaviourally identical*, only slow, which is exactly why the finding
    needed a measurement of its own.

    So this asserts the **shape**, not a wall-clock budget: four times the input must
    not cost sixteen times the time. Measured on the same generator and process,
    ``_v4_declared_categories`` takes 13,3 / 28,0 / 60,8 ms at 263 KB / 533 KB /
    1,08 MB (≈4,6x for 4x the input) where the D2 shape took 116 / 488 / 2 106 ms
    (≈18x). The threshold sits at 8x — far above the linear 4,6x and far below the
    quadratic 18x — and both measurements are best-of-3 so a single scheduling hiccup
    cannot decide it. An absolute millisecond bound is deliberately **not** used: it
    would be a machine-dependent flake, not a property.

    Non-vacuous: the region is asserted to contain many matches, so a run that found
    nothing to classify cannot pass on cheap timings.
    """
    unit = ("### Guides (`docs/guides/`)\n\n"
            "- **[P](docs/guides/setup/x.md)**: text.\n"
            "- Mirror: https://x.invalid/docs/spam/a.md\n\n")
    small = unit * (128 * 1024 // len(unit))
    large = unit * (512 * 1024 // len(unit))

    assert len(docs_links_lib.V4_CATEGORY_RE.findall(large)) > 1000, "zu klein"

    def best(region: str) -> float:
        timings = []
        for _ in range(3):
            start = time.perf_counter()
            docs_links_lib._v4_declared_categories(region)
            timings.append(time.perf_counter() - start)
        return min(timings)

    small_seconds = best(small)
    large_seconds = best(large)

    assert small_seconds > 0, small_seconds
    assert large_seconds < 8 * small_seconds, (
        f"4x input cost {large_seconds / small_seconds:.1f}x the time — "
        f"{small_seconds * 1000:.1f} ms -> {large_seconds * 1000:.1f} ms")


def test_v4_link_grammars_are_shared_with_v3(tmp_path):
    """F-4: V4's two link grammars are V3's, not copies that can drift.

    Asserting the *invariants* is what a DRY change can be held to, and identity alone
    proves nothing here: ``re.compile`` hands back a cached object, so a copy built
    from ``V3_INLINE_LINK_RE.pattern`` compares ``is`` **equal** to the original. The
    load-bearing assertion is therefore at the source level — each grammar must be
    written down **exactly once** in this module — plus the semantic equality and the
    one flag difference V4 needs (``MULTILINE``, because V4 scans a whole region where
    V3 scans line by line). A copy-paste divergence in either direction turns this red.
    """
    source = Path(docs_links_lib.__file__).read_text(encoding="utf-8")

    assert source.count(docs_links_lib.V3_INLINE_LINK_RE.pattern) == 1, "inline doppelt"
    assert source.count(docs_links_lib.V3_REFERENCE_DEF_RE.pattern) == 1, "refdef 2x"
    assert (docs_links_lib.V4_LINK_TARGET_RE.pattern
            == docs_links_lib.V3_INLINE_LINK_RE.pattern)
    assert (docs_links_lib.V4_REFERENCE_DEF_RE.pattern
            == docs_links_lib.V3_REFERENCE_DEF_RE.pattern)
    assert docs_links_lib.V4_REFERENCE_DEF_RE.flags & re.MULTILINE
    assert not docs_links_lib.V3_REFERENCE_DEF_RE.flags & re.MULTILINE


def test_v4_declares_seven_categories_including_architecture_from_link_only():
    """K64 / RVW-7-06: the extraction rule is "every ``docs/<category>/`` path named".

    Pins **7** on the real README and, crucially, pins *where* ``docs/architecture/``
    comes from: it is named **only** inside the link
    ``docs/architecture/01-layer-model.md`` and in **no** ``###`` heading. A
    heading-only extraction returns 6, which is why both readings are asserted
    here — a test that only pinned "7" would still pass against a
    heading-glob that happened to see seven headings later.

    Both readings currently yield the same expected finding *count*, so the
    count is deliberately not what is asserted here: the count would not
    distinguish them. The pin is on the rule, and this test is where the rule
    is observable. A deliberate README restructure must edit this test.
    """
    readme = (REPO_ROOT / README_RELPATH).read_text(encoding="utf-8")

    region = docs_links_lib._v4_index_region(readme)
    assert region is not None

    declared = [f"docs/{name}/"
                for name in docs_links_lib._v4_declared_categories(region)]
    headings_only = [f"docs/{name}/" for name in
                     docs_links_lib._v4_declared_heading_categories(region)]

    assert len(declared) == 7, declared
    assert declared == [
        "docs/guides/", "docs/howto/", "docs/api/", "docs/ui/",
        "docs/architecture/", "docs/plans/", "docs/se-cascade/"], declared
    assert len(headings_only) == 6, headings_only
    assert "docs/architecture/" in declared
    assert "docs/architecture/" not in headings_only


def test_v4_unlinked_pages_below_a_declared_category_are_not_findings(tmp_path):
    """The **negative proof** against the per-page reading, and the non-vacuum twin.

    Fixture ``covered`` carries two pages below a category that *is* declared
    and *is* linked. Under the old reading each page was a finding (that reading
    produced 191/193 on the real tree); under E-5 the category is represented
    and the pages are V2's business — hence ``== []``. That assertion alone
    would also be satisfied by a check that returns nothing at all, so the same
    body adds fixture ``unrepresented``: the same rule, one extra declared
    category, no link — and asserts a **non-empty** result naming **that
    category and neither page**. Both halves together are what make the
    precedence rule and the new scope non-vacuous (K33).
    """
    covered = _tree(tmp_path / "covered", "docs/guides/ungenutzt-a.md", _PAGE)
    _tree(covered, "docs/guides/ungenutzt-b.md", _PAGE)
    _tree(covered, README_RELPATH, _index_readme(
        _declares_with_link("docs/guides/")))

    assert _v4_findings(covered) == []

    unrepresented = _tree(tmp_path / "unrepresented",
                          "docs/guides/ungenutzt-a.md", _PAGE)
    _tree(unrepresented, "docs/guides/ungenutzt-b.md", _PAGE)
    _tree(unrepresented, "docs/se-cascade/overview.md", _PAGE)
    _tree(unrepresented, README_RELPATH, _index_readme(
        _declares_with_link("docs/guides/"),
        _declares("docs/se-cascade/")))

    findings = _v4_findings(unrepresented)

    assert _categories(findings) == ["docs/se-cascade/"], findings
    assert findings[0].severity == docs_index_lib.Severity.ERROR
    assert "ungenutzt-a.md" not in findings[0].message
    assert "ungenutzt-b.md" not in findings[0].message


def test_v2_is_not_registered_in_the_runner_yet():
    """Pin the pre-W2-7 state: V2 has no call site, so it cannot fire in CI yet.

    W2-7 owns ``scripts/consistency-check.py`` and the ``docs.py`` facade
    (K20/K46); this task writes neither. A passing test here means the wave
    cannot have leaked a registration that its owner has not reviewed — and W2-7
    **replaces** this pin with a positive one, exactly as it does for
    ``test_v1_is_not_wired_into_the_runner_yet`` in ``test_doc_freshness.py``.

    The facade is checked on its **export contract** (``__all__``), not on the
    raw text: W2-0 left a comment in ``docs.py`` naming this very check as
    "not yet implemented", and that comment is the *documentation* of the
    pending registration, not a registration.
    """
    runner = (REPO_ROOT / "scripts" / "consistency-check.py").read_text(encoding="utf-8")
    assert "check_docs_index_completeness" not in runner

    from scripts.lib.consistency import docs as docs_facade

    assert "check_docs_index_completeness" not in docs_facade.__all__
    assert not hasattr(docs_facade, "check_docs_index_completeness")


def test_v2_lives_in_docs_index_and_v4_in_docs_links():
    """Spec §4.1: V2 and V4 sit in different family modules — the split is the contract.

    Both checks are about the documentation *build*, but only one of them reads a
    reference target, and §4.1 assigns that question to ``docs_links``. Asserting
    the homes keeps a later refactor from silently merging the two families.
    """
    assert docs_index_lib.__file__.endswith("docs_index.py")
    assert V2_CHECK_ID not in docs_links_lib.__doc__
    assert V4_CHECK_ID not in docs_index_lib.__doc__


def test_real_repo_readme_index_has_exactly_one_unrepresented_category():
    """R7 replacement: real-tree observation, **derived** from disk, not counted.

    The old test parsed ``finding.message.split("'")[1]`` and compared it to the
    README text — an assertion about a **page** message that E-5 removes. The
    replacement re-derives the whole relationship instead of pinning a number:

    * ``expected`` is computed from the same three facts the check uses — the
      categories the region declares, the categories it links, and which of the
      declared directories exist — so the test states the *rule* on the real
      tree and the finding set has to equal it.
    * ``declared - reported == represented`` is the non-vacuum half: it proves
      V4 is **silent** about at least one declared category, so an empty
      finding set cannot pass by construction, and ``declared``/``represented``
      are asserted non-empty so a broken extraction cannot pass either.
    * every reported name ends in ``/`` and has exactly two slashes, which is
      what makes a regression to a per-page report visible here.

    On today's tree the derived set has exactly **one** member,
    ``docs/se-cascade/`` — declared at ``README.md:378``, no page linked from
    the section — tracked as follow-up ``F-DOCS-README-INDEX-SE-2026-09-27``
    (due 2026-10-11). The name keeps that expectation; the body does not freeze
    it, so resolving the follow-up does not require editing this test.

    The V2 half survives unchanged and for the same reason as before: V2 is
    non-empty exactly while ``docs/INDEX.md`` is absent, and W3-6 creates it.
    """
    readme = (REPO_ROOT / README_RELPATH).read_text(encoding="utf-8")
    region = docs_links_lib._v4_index_region(readme)
    assert region is not None

    declared = {f"docs/{name}/"
                for name in docs_links_lib._v4_declared_categories(region)}
    linked = {f"docs/{name}/"
              for name in docs_links_lib._v4_linked_categories(region)}
    missing_dir = {relpath for relpath in declared
                   if not (REPO_ROOT / relpath).is_dir()}

    findings = docs_links_lib.check_readme_docs_index(REPO_ROOT)
    reported = set(_categories(findings))

    represented = (declared & linked) - missing_dir
    expected = (declared - linked) | missing_dir

    assert declared, "the real README's index section declares nothing"
    assert linked, "the real README's index section links no category"
    assert represented, "no declared category is fully represented"
    assert reported == expected, (reported, expected)
    assert declared - reported == represented

    for relpath in reported:
        assert relpath.endswith("/") and relpath.count("/") == 2, relpath

    index_exists = (REPO_ROOT / INDEX_RELPATH).is_file()
    v2_files = {f.file for f in docs_index_lib.check_docs_index_completeness(REPO_ROOT)}
    assert bool(v2_files) is not index_exists
