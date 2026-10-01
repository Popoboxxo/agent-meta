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

import importlib.util
from pathlib import Path

import pytest

from scripts.lib.consistency import docs_freshness as docs_freshness_lib
from scripts.lib.doc_facts import EXPECTED_COMPARABLE_FACT_KEYS
from scripts.lib.doc_renderer import REGION_FACT_KEYS, render_doc_fact_block

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


# --- Registration in the runner (W2-7, RVW2-5) -----------------------------
#
# History of this section: it carried ``test_v1_is_not_wired_into_the_runner_yet``
# with the assertion ``"check_no_manual_counts" not in runner``. That pinned the
# state *before* W2-7 — "V1 has no call site, so no scenario can regress from
# W2-1" — and the task that registers V1 therefore made it red by construction.
# RVW2-5 makes replacing it **binding**: the negative pin is not deleted and not
# kept, it is superseded by a positive one that states the same boundary in the
# direction that is now true. Keeping both would assert a contradiction.
#
# The same replacement applies to the V6 pin further down in this file, and to
# the V3 pin in ``tests/test_doc_facts.py``.


def _runner():
    """The runner module, loaded the way ``lib.cli_commands`` loads it.

    The filename contains a hyphen, so it cannot be imported by name —
    ``importlib.util.spec_from_file_location`` is the established route in this
    repo (``cli_commands._run_consistency_checks``), not a test-only trick.
    """
    spec = importlib.util.spec_from_file_location(
        "_consistency_runner", REPO_ROOT / "scripts" / "consistency-check.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _gate_open_tree(tmp_path: Path, name: str = "open") -> Path:
    """A minimal project root with the IC-05 sites and the common gate **on**."""
    root = _v1_tree(tmp_path / name, "README.md", V1_COUNTER_PROBE)
    (root / ".meta-config").mkdir(parents=True, exist_ok=True)
    (root / ".meta-config" / "project.yaml").write_text(
        "docs-consolidation:\n  enabled: true\n", encoding="utf-8"
    )
    return root


def test_v1_is_registered_in_the_runner(tmp_path):
    """AC-13: V1 is imported from the facade **and** reaches ``findings[]``.

    Two halves, because on their own both are vacuous — a name can sit in an
    import without a call, and a call can exist behind a closed gate:

    (a) the import: ``check_no_manual_counts`` is reachable from
        ``scripts/consistency-check.py``, and through the **facade**
        ``lib.consistency.docs`` only (K20) — whose ``__all__`` therefore has
        to carry the name, which is what makes the facade contract (K19) the
        precondition of the registration rather than a style preference;
    (b) the effect: a tree that really contains an IC-05 site, a project config
        with ``docs-consolidation.enabled: true`` and a genuine ``run_checks()``
        call yield ``docs.no_manual_counts`` findings.
    """
    from scripts.lib.consistency import docs as docs_facade

    runner_source = (REPO_ROOT / "scripts" / "consistency-check.py").read_text(
        encoding="utf-8"
    )
    assert "check_no_manual_counts" in runner_source, (
        "the registration must be visible in the runner — the import block is "
        "the only registration site (RVW2-1: a count over the --json report "
        "proves nothing about registration)"
    )
    assert "from lib.consistency.docs import" in runner_source, (
        "K20: registration goes through the facade, never module-wise"
    )
    assert "check_no_manual_counts" in docs_facade.__all__
    assert "check_no_manual_counts" in [
        check.__name__ for check in _runner().DOCS_CHECKS
    ]

    findings = _runner().run_checks(_gate_open_tree(tmp_path))

    assert "docs.no_manual_counts" in {f.check for f in findings}, findings
    v1 = [f for f in findings if f.check == "docs.no_manual_counts"]
    assert [f.branch for f in v1] == ["V1a"], v1
    assert [f.line for f in v1] == [1], v1
    assert {f.file for f in v1} == {"README.md"}, v1


def _docs_tree(tmp_path: Path, name: str, gate: str) -> Path:
    """A project root that *can* produce V1…V4 findings — the control tree.

    The README carries an IC-05 count site (V1), ``docs/guides/page.md`` is an
    unindexed page with a dead link (V2, V3) and the README has no
    ``Documentation Index`` region at all (V4, fail-closed). The only
    difference between the "on" and the "off" tree is the ``gate`` string.
    """
    root = _v1_tree(tmp_path / name, "README.md", V1_COUNTER_PROBE)
    _v1_tree(root, "docs/guides/page.md", "# page\n\n[x](missing.md)\n")
    (root / ".meta-config").mkdir(parents=True, exist_ok=True)
    (root / ".meta-config" / "project.yaml").write_text(gate, encoding="utf-8")
    return root


def test_the_common_gate_is_the_first_condition_of_every_registered_check(
    tmp_path,
):
    """IC-05/IC-22/AC-38: with the switch absent, **every** V-check is a no-op.

    Two runs over two trees that differ in exactly one byte-sequence — the
    ``docs-consolidation`` block — and a truth table on the gate itself. The
    control is what makes the silence mean something: the same ``run_checks``
    over the "on" tree produces four of the seven checks' findings, so the "off"
    run is not vacuously clean.

    Absence, a non-mapping block, a non-boolean value and an explicit ``false``
    must all read as closed (fail-off, IC-22); only the boolean ``true`` opens
    the gate.
    """
    runner = _runner()

    for config in ({}, None, {"docs-consolidation": {}},
                   {"docs-consolidation": {"enabled": False}},
                   {"docs-consolidation": {"enabled": "false"}},
                   {"docs-consolidation": True}):
        assert runner.docs_consolidation_enabled(config) is False, config

    assert runner.docs_consolidation_enabled(
        {"docs-consolidation": {"enabled": True}}) is True

    off = _docs_tree(tmp_path, "off", "systems-engineering:\n  enabled: false\n")
    assert runner.load_project_config(off) == {
        "systems-engineering": {"enabled": False}}, (
        "premise: the closed tree really has no docs-consolidation block"
    )
    assert [f for f in runner.run_checks(off) if f.check.startswith("docs.")] == [], (
        "a project that never set the key collects no documentation finding"
    )

    on = _docs_tree(tmp_path, "on", "docs-consolidation:\n  enabled: true\n")
    opened = {f.check for f in runner.run_checks(on) if f.check.startswith("docs.")}
    assert opened == {"docs.no_manual_counts", "docs.docs_index_completeness",
                      "docs.internal_links", "docs.readme_index"}, opened

    explicit = _docs_tree(tmp_path, "explicit",
                          "docs-consolidation:\n  enabled: false\n")
    assert [f for f in runner.run_checks(explicit)
            if f.check.startswith("docs.")] == [], (
        "an explicit false is observationally identical to an absent block"
    )


def test_the_scenario_configs_never_set_the_common_gate():
    """AC-38's premise, measured over **all** scenario fixtures — not a subset.

    This is the half of the old V1 pin that survives the registration, and it is
    the only **directly** measurable part of AC-38: every scenario fixture must
    leave ``docs-consolidation`` absent, so the fail-off above keeps all seven
    registered checks silent there.

    **Why all of them, not just 50–56.** The plan's acceptance names scenarios
    50–56, but the guarantee is a property of the *fixtures*, and the matrix has
    grown. A fixture that opened the gate would be a documentation regression in
    a scenario nobody is watching, so the pin covers every
    ``*.project.yaml`` that ``tests/scenarios/run.sh`` can feed in.

    Two checks per file, and the difference matters. The substring check is the
    strict one — it also catches the key inside a comment or an example, which a
    parser would happily ignore. The parsed check is the one that speaks the
    runner's language: it proves the config the gate reads has no
    ``docs-consolidation`` key at all, so "absent" and not merely "present but
    falsy" is what is pinned. Both are asserted; the count is not hardcoded, and
    no fixture sets ``enabled`` explicitly (``false`` included) — measured
    **0** of **63**, which is the value this test would break on.

    **What this cannot prove, stated rather than hidden.** The plan's shell line
    ``bash tests/scenarios/run.sh 50 51 52 54 55 56 → 0`` does **not** measure
    this: ``lib.cli_commands._run_consistency_checks(agent_meta_root)`` runs the
    suite over the **agent-meta checkout**, so the fixture config never reaches
    the checks. That line is therefore unreachable for a reason independent of
    this gate — see the W2-7 plan note.
    """
    import yaml

    configs = sorted((REPO_ROOT / "tests" / "scenarios" / "configs").glob(
        "*.project.yaml"))
    assert configs, "premise: the scenario configs are gone"

    for path in configs:
        text = path.read_text(encoding="utf-8")
        assert "docs-consolidation" not in text, (
            f"{path.name}: the common gate must stay absent — a fixture that set "
            "it would put all seven registered checks into a scenario"
        )
        parsed = yaml.safe_load(text) or {}
        assert isinstance(parsed, dict), path
        assert "docs-consolidation" not in parsed, path
        assert "docs-consolidation" not in str(parsed).lower(), path



# ---------------------------------------------------------------------------
# V6 — check_docs_facts_fresh (IC-05, IC-23, AC-36, R14, plan W2-5)
# ---------------------------------------------------------------------------
#
# V6 owns the two comparisons a rendered fact has to pass, and therefore the
# three ``kind`` values of the IC-05 table: ``handedit`` (rendered region !=
# computed facts), ``expected-mismatch`` (computed facts != the hand-maintained
# oracle) and ``missing-in-expected`` (a pinnable fact the oracle does not
# carry). The second axis is the only thing in the initiative that breaks the
# closed circle ``doc_facts -> renderer -> V6`` (R14) — see the acceptance test
# ``test_mismatch_is_reported`` in ``tests/test_doc_facts_expected.py``.

#: The region the handedit axis reads. ``roster`` is one of the six allowed
#: region names (IC-08) and no document in the repository carries a marker
#: region today (that migration is W3/W4), so no test here can depend on the
#: current content of a real entry document.
V6_REGION = "roster"

V6_FACT = REGION_FACT_KEYS[V6_REGION]

#: One synthetic value per pinnable fact, plus the region's own block fact. The
#: values are *derived* from the fact names, never written down: IC-23 makes
#: ``config/doc-facts-expected.yaml`` the only place in the tree that may hold an
#: expected number, and a fixture that restated one would reintroduce the very
#: error class R14 exists to catch. ``<NAME>`` cannot collide with a computed
#: value, so a comparison that fires always fires for the reason under test.
V6_FACTS: dict[str, str] = {
    **{name: f"<{name}>" for name in EXPECTED_COMPARABLE_FACT_KEYS},
    V6_FACT: "<roster-block>",
}

#: The oracle that *agrees* with :data:`V6_FACTS`. Both sides are derived from
#: the same names, so the untouched pair is silent and every test below perturbs
#: exactly one side of it — a finding is always attributable to the perturbation.
V6_EXPECTED: dict[str, str] = {
    name: value for name, value in V6_FACTS.items()
    if name in EXPECTED_COMPARABLE_FACT_KEYS
}

#: A non-empty project config. V6 only needs one to exist: the facts arrive
#: through the patched producer, and the real formulas are somebody else's test.
V6_CONFIG: dict = {"docs-consolidation": {"enabled": True}}


def _v6_region_text(region: str, facts: dict[str, str], body: str | None = None) -> str:
    """A minimal document carrying exactly one marker region.

    ``body`` overrides the rendered block — that is how a *drifted* region is
    built: the markers stay balanced and the region name stays valid, so the
    content is the only thing that differs.

    Note the missing newline after the ``docs-begin`` marker: a rendered body
    already *starts* with the newline that closes the ``docs-begin`` line
    (``doc_renderer.render_doc_fact_block``), so adding one here would build a
    document the renderer would immediately rewrite.
    """
    rendered = render_doc_fact_block(region, facts) if body is None else body
    return (
        f"<!-- agent-meta:docs-begin {region} -->"
        f"{rendered}"
        f"<!-- agent-meta:docs-end {region} -->\n"
    )


def _v6_findings(monkeypatch, root: Path, facts: dict[str, str] | None = None,
                 expected: dict[str, str] | None = None,
                 relpaths: tuple[str, ...] = ()) -> list:
    """Run V6 over *root* with a fixed (computed facts, oracle) pair.

    ``compute_doc_facts`` and ``load_expected_doc_facts`` are the two seams V6
    owns. The formulas are covered by ``tests/test_doc_facts.py`` and the oracle
    loader by ``tests/test_doc_facts_expected.py``, and an isolated tree cannot
    produce a real set of facts — so pinning both sides here is what makes V6's
    *own* contract testable. Everything between them (the comparison, the region
    extraction, the finding construction, the severities) is the real code.
    """
    monkeypatch.setattr(
        docs_freshness_lib,
        "compute_doc_facts",
        lambda agent_meta_root, config, **kwargs: dict(
            V6_FACTS if facts is None else facts
        ),
    )
    monkeypatch.setattr(
        docs_freshness_lib,
        "load_expected_doc_facts",
        lambda agent_meta_root, log=None: dict(
            V6_EXPECTED if expected is None else expected
        ),
    )
    monkeypatch.setattr(docs_freshness_lib, "V6_SCAN_RELPATHS", relpaths)
    return docs_freshness_lib.check_docs_facts_fresh(root, V6_CONFIG)


def _v6_kinds(findings: list) -> list[str]:
    return [finding.kind for finding in findings]


def test_v6_finds_nothing_when_both_axes_agree(monkeypatch, tmp_path):
    """The negative control: agreeing sources and a freshly rendered region.

    Every positive test below perturbs exactly one side of this state, so a
    finding that cannot be attributed to a perturbation fails here first.
    """
    _v1_tree(tmp_path, "README.md", _v6_region_text(V6_REGION, V6_FACTS))

    assert _v6_findings(monkeypatch, tmp_path, relpaths=("README.md",)) == []


def test_v6_handedit_reports_a_drifted_region(monkeypatch, tmp_path):
    """Axis (a): the rendered block differs from what the facts would render.

    The message names the *first* differing body line and the finding's ``line``
    points at it, because a drift finding that only says "differs" costs the
    reader a diff run.
    """
    drifted = "\n- a roster row that no longer exists\n"
    _v1_tree(tmp_path, "README.md", _v6_region_text(V6_REGION, V6_FACTS, drifted))

    findings = _v6_findings(monkeypatch, tmp_path, relpaths=("README.md",))

    assert _v6_kinds(findings) == ["handedit"]
    finding = findings[0]
    assert finding.severity == docs_freshness_lib.Severity.ERROR
    assert finding.check == "docs.docs_facts_fresh"
    assert finding.file == "README.md"
    assert V6_REGION in finding.message
    assert drifted.strip() in finding.message
    lines = (tmp_path / "README.md").read_text(encoding="utf-8").splitlines()
    assert lines[finding.line - 1] == drifted.strip(), (
        "the reported line must be the first line that actually moved"
    )


def test_v6_handedit_is_silent_for_a_freshly_rendered_region(monkeypatch, tmp_path):
    """Axis (a) really compares: byte-identical render output, no finding.

    The counterpart of the test above on the *same* tree shape. Without it, a
    check that never found a handedit at all would satisfy the positive test by
    not running.
    """
    _v1_tree(tmp_path, "README.md", _v6_region_text(V6_REGION, V6_FACTS))

    findings = _v6_findings(monkeypatch, tmp_path, relpaths=("README.md",))

    assert _v6_kinds(findings) == []


def test_v6_expected_mismatch_is_an_error_naming_both_values(monkeypatch, tmp_path):
    """Axis (b): the oracle and the formula disagree — IC-23's whole point.

    The rendered document is *not* part of this test, which is the point: the
    finding is raised by the second axis alone.
    """
    fact = min(V6_EXPECTED)
    manipulated = {**V6_EXPECTED, fact: f"<manipulated {fact}>"}

    findings = _v6_findings(monkeypatch, tmp_path, expected=manipulated)

    assert _v6_kinds(findings) == ["expected-mismatch"]
    finding = findings[0]
    assert finding.severity == docs_freshness_lib.Severity.ERROR
    assert finding.file == "config/doc-facts-expected.yaml"
    assert fact in finding.message
    assert V6_FACTS[fact] in finding.message
    assert manipulated[fact] in finding.message
    # The oracle axis names a key, not a line — `line` stays unset rather than
    # carrying a magic 0 that a console report would print as a location.
    # W2-7 (K15/B-5) promoted `line` from an instance attribute to a declared
    # dataclass field with default ``None``, so "unset" is now the *value* and
    # `hasattr` can no longer express it — the field is always there.
    assert finding.line is None, (
        "a key-addressed finding must not invent a line number"
    )


def test_v6_missing_in_expected_is_a_warning(monkeypatch, tmp_path):
    """Axis (c): a pinnable fact the oracle does not carry — WARNING, not error.

    IC-23 lets the file grow, so this is a warning axis and not a second error
    axis. The document is rendered correctly here, so the finding can only come
    from the oracle side.
    """
    fact = min(V6_EXPECTED)
    trimmed = {name: value for name, value in V6_EXPECTED.items() if name != fact}

    findings = _v6_findings(monkeypatch, tmp_path, expected=trimmed)

    assert _v6_kinds(findings) == ["missing-in-expected"]
    finding = findings[0]
    assert finding.severity == docs_freshness_lib.Severity.WARNING
    assert finding.file == "config/doc-facts-expected.yaml"
    assert fact in finding.message
    assert V6_FACTS[fact] in finding.message


def test_v6_kind_domain_and_severity_are_pinned():
    """IC-05: exactly three kinds, and only ``missing-in-expected`` is a warning.

    Pinned as a data structure rather than through the check, because the two
    facts that matter — no fourth kind, and no severity drift — must hold even
    for a kind this file happens not to exercise yet.
    """
    kinds = docs_freshness_lib.V6_SEVERITY_BY_KIND

    assert set(kinds) == {"handedit", "expected-mismatch", "missing-in-expected"}
    assert kinds["handedit"] == docs_freshness_lib.Severity.ERROR
    assert kinds["expected-mismatch"] == docs_freshness_lib.Severity.ERROR
    assert kinds["missing-in-expected"] == docs_freshness_lib.Severity.WARNING
    # The check renames the comparator's kind; the two vocabularies stay
    # distinct (F10) and the shared spelling has one source of truth.
    assert docs_freshness_lib.V6_KIND_MISSING_IN_EXPECTED == "missing-in-expected"
    assert docs_freshness_lib.V6_KIND_EXPECTED_MISMATCH == "expected-mismatch"
    assert docs_freshness_lib.V6_KIND_HANDEDIT == "handedit"


def test_v6_mirrors_the_renderer_decisions(monkeypatch, tmp_path):
    """A region the renderer would not write is a region V6 does not compare.

    All-or-nothing on an unpaired begin (AC-15), first pair only on a repeated
    region name (AC-16), unknown region names untouched (IC-08). Reporting any
    of them would be a drift the next ``sync.py`` cannot fix — a permanent false
    alarm, the F21 class.
    """
    fresh = render_doc_fact_block(V6_REGION, V6_FACTS)
    unpaired = (
        f"<!-- agent-meta:docs-begin {V6_REGION} -->"
        f"{fresh}"
        "<!-- agent-meta:docs-begin hooks -->\n"
    )
    duplicated = (
        f"<!-- agent-meta:docs-begin {V6_REGION} -->"
        f"{fresh}"
        f"<!-- agent-meta:docs-end {V6_REGION} -->\n"
        f"<!-- agent-meta:docs-begin {V6_REGION} -->"
        "\n- drifted duplicate\n"
        f"<!-- agent-meta:docs-end {V6_REGION} -->\n"
    )
    unknown = (
        "<!-- agent-meta:docs-begin roster-v2 -->"
        "\n- drifted\n"
        "<!-- agent-meta:docs-end roster-v2 -->\n"
    )

    for body in (unpaired, duplicated, unknown):
        root = _v1_tree(tmp_path, "README.md", body)
        assert _v6_findings(monkeypatch, root, relpaths=("README.md",)) == [], body


def test_v6_is_silent_without_a_project_config(monkeypatch, tmp_path):
    """No project config → no facts → no comparison, and no false alarm.

    The facts are formulas over the project config; without one they come back
    as empty strings, and comparing empty strings against a pinned value would
    report every fact in the repository as drifted. The control on the right
    proves the silence is caused by the missing config and not by an inert
    check — same document, same bytes, one config argument apart.
    """
    drifted = _v6_region_text(V6_REGION, V6_FACTS, "\n- drifted\n")
    # Neither root has a .meta-config/project.yaml, so V6 has to load one itself.
    silent = _v1_tree(tmp_path / "silent", "README.md", drifted)
    wired = _v1_tree(tmp_path / "wired", "README.md", drifted)

    assert docs_freshness_lib.check_docs_facts_fresh(silent, None) == []

    monkeypatch.setattr(
        docs_freshness_lib, "compute_doc_facts",
        lambda agent_meta_root, config, **kwargs: dict(V6_FACTS),
    )
    monkeypatch.setattr(docs_freshness_lib, "V6_SCAN_RELPATHS", ("README.md",))
    control = docs_freshness_lib.check_docs_facts_fresh(wired, V6_CONFIG)

    assert _v6_kinds(control) == ["handedit"], (
        "the control must fire — otherwise the silence above proves nothing"
    )


def test_v6_skips_a_region_whose_fact_could_not_be_computed(monkeypatch, tmp_path):
    """An empty fact value is not a drift — IC-01's fail-soft, applied to V6.

    ``doc_facts`` never raises on a missing source; it yields the empty string.
    The renderer would then write the ``docs-empty`` placeholder, so comparing
    the region against that placeholder would report a drift that no config
    source can fix.
    """
    without_fact = {name: value for name, value in V6_FACTS.items() if name != V6_FACT}
    _v1_tree(tmp_path, "README.md", _v6_region_text(V6_REGION, without_fact))

    assert _v6_findings(monkeypatch, tmp_path, facts=without_fact,
                        relpaths=("README.md",)) == []


def test_v6_output_is_deterministic_and_axis_ordered(monkeypatch, tmp_path):
    """Same input, same list — and the expected-value axis comes first.

    The comparator already sorts by ``fact``; V6 only has to keep that order
    when it appends the second axis, otherwise two runs would report the same
    drift in two different orders.
    """
    fact = min(V6_EXPECTED)
    expected = {**V6_EXPECTED, fact: f"<manipulated {fact}>"}
    _v1_tree(tmp_path, "README.md", _v6_region_text(V6_REGION, V6_FACTS, "\n- drifted\n"))

    first = _v6_findings(monkeypatch, tmp_path, expected=expected,
                         relpaths=("README.md",))
    second = _v6_findings(monkeypatch, tmp_path, expected=expected,
                          relpaths=("README.md",))

    assert [str(finding) for finding in first] == [str(finding) for finding in second]
    assert _v6_kinds(first) == ["expected-mismatch", "handedit"]


# --- Registration in the runner (W2-7, RVW2-5) -----------------------------
#
# Superseded here for the same reason as the V1 pin at the top of this section:
# ``test_v6_is_not_wired_into_the_runner_yet`` asserted that the runner does not
# mention ``check_docs_facts_fresh`` and that the facade neither exports nor
# carries the name — the pre-W2-7 state, which W2-7 invalidates by registering
# V6. The positive pin below asserts the same three properties inverted, plus
# the one that actually matters for a gate tool: the check is in the registry
# that the common gate governs.


def test_v6_is_registered_in_the_runner():
    """AC-13: V6 is exported by the facade, imported by the runner, registered."""
    from scripts.lib.consistency import docs as docs_facade

    runner_source = (REPO_ROOT / "scripts" / "consistency-check.py").read_text(
        encoding="utf-8"
    )

    assert "check_docs_facts_fresh" in runner_source, (
        "W2-7 registers V6 — the import block is the only registration site"
    )
    assert "from lib.consistency.docs import" in runner_source, (
        "K20: registration goes through the facade, never module-wise"
    )
    assert "check_docs_facts_fresh" in docs_facade.__all__, (
        "the facade __all__ is the contract (K19) the registration runs on"
    )
    assert hasattr(docs_facade, "check_docs_facts_fresh")
    assert "check_docs_facts_fresh" in [
        check.__name__ for check in _runner().DOCS_CHECKS
    ], "a name in an import is not a registration — it needs an entry in DOCS_CHECKS"

