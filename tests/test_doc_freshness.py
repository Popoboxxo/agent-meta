"""AC-07/AC-08 (IC-05, spec §5.1.1) — V1a/V1b ``check_no_manual_counts``.

The V1 tests moved here from ``tests/test_doc_facts.py`` in plan task W2-0.
Nothing about the assertions changed in the move — this is a file boundary, not
a behaviour change (Spec §4.1, K19). Two consequences of the move are worth
naming because they are the *point* of it:

* the module under test is now ``scripts.lib.consistency.docs_freshness``
  directly, not the ``docs`` facade. ``_v1_findings`` therefore monkeypatches
  ``docs_freshness.V1_SCAN_RELPATHS`` — the module that *reads* the constant.
  Patching the facade would rebind only the facade's own name and the check
  would keep scanning the real list.
* the V6 tests (W2-5) and the V5 tests (W2-4) land in this same file, which is
  what gives W2-3…W2-7 disjoint write-sets.

The helper ``_v1_tree`` exists in both this file and ``test_doc_facts.py``
because the V3 and alt-check tests there use it too. A shared helper would have
to live in ``conftest.py``, which is outside this task's file set; the two
copies are independent fixtures, not a contract.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lib.consistency import docs_freshness as docs_freshness_lib

REPO_ROOT = Path(__file__).resolve().parent.parent


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
    monkeypatch.setattr(docs_freshness_lib, "V1_SCAN_RELPATHS", relpaths)
    return docs_freshness_lib.check_no_manual_counts(root, config)


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
    assert {f.severity for f in findings} == {docs_freshness_lib.Severity.WARNING}
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
    assert lines[736:737] == ["```"], (
        "premise: the directory-structure block no longer closes untyped at "
        "README.md:737 (a typed fence between :681 and :736 would leave the "
        "four sites visible but prove less than claimed; README.md has "
        f"{len(lines)} lines, found {lines[736:737]!r})"
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
            assert finding.severity == docs_freshness_lib.Severity.WARNING


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
    for relpath in (*docs_freshness_lib.V1_SCAN_RELPATHS, V1_FIXTURE_RELPATH):
        path = REPO_ROOT / relpath
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            scanned += 1
            for a_start, a_end, _a in docs_freshness_lib.v1a_count_spans(line):
                for b_start, b_end, _b in docs_freshness_lib.v1b_version_spans(line):
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
        assert [f.severity for f in findings] == [docs_freshness_lib.Severity.WARNING], config

    findings = _v1_findings(monkeypatch, root, ("README.md",), strict)
    assert [f.severity for f in findings] == [docs_freshness_lib.Severity.ERROR]


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

