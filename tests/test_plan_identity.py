"""IC-01 ``plan_identity``: shared identity primitives for the progress/ledger system.

Covers AC-01 (hyphen-aware ``TASK_HEADER_RE``), AC-02 (deterministic
``derive_plan_id``) and AC-03 (``make_task_ref``).
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.plan_identity import (
    PLAN_ID_RE,
    TASK_HEADER_RE,
    TASK_ID_RE,
    derive_plan_id,
    make_task_ref,
    normalize_task_id,
)


def test_header_regex_hyphen_and_numeric():
    # AC-01: hyphenated id must not be cut at the dash.
    m = TASK_HEADER_RE.search("### Task task-1: Title")
    assert m is not None
    assert m.group(1) == "task-1"
    assert m.group(2) == "Title"

    # AC-01: em-dash separator, numeric id.
    m = TASK_HEADER_RE.search("### Task 1 \u2014 Title")
    assert m is not None
    assert m.group(1) == "1"
    assert m.group(2) == "Title"

    # AC-01: hyphen separator, numeric id.
    m = TASK_HEADER_RE.search("### Task 1 - Title")
    assert m is not None
    assert m.group(1) == "1"
    assert m.group(2) == "Title"

    # Group 1 keeps the full ``-._`` id grammar.
    m = TASK_HEADER_RE.search("### Task a.b_c-2: X")
    assert m is not None
    assert m.group(1) == "a.b_c-2"
    assert m.group(2) == "X"

    # At most one header per line.
    matches = TASK_HEADER_RE.findall("### Task 1: A\n### Task 2: B")
    assert [group1 for group1, _ in matches] == ["1", "2"]


def test_derive_plan_id_explicit_and_slug(tmp_path):
    # AC-02: explicit frontmatter ``plan-id:`` wins over the slug.
    frontmatter = tmp_path / "2026-09-13-whatever.md"
    frontmatter.write_text("---\nplan-id: my-plan\n---\n# T\n", encoding="utf-8")
    assert derive_plan_id(frontmatter) == "my-plan"

    # AC-02: ``> plan-id:`` header line is honoured too.
    header_line = tmp_path / "2026-09-13-whatever.md"
    header_line.write_text("# T\n\n> plan-id: header-plan\n", encoding="utf-8")
    assert derive_plan_id(header_line) == "header-plan"

    # AC-02: explicit text argument is used without touching the filesystem.
    assert derive_plan_id(tmp_path / "missing.md", "> plan-id: from-text") == "from-text"

    # AC-02: no ``plan-id:`` -> deterministic slug of the file stem.
    slug_plan = tmp_path / "2026-09-13-Progress Ledger System.md"
    slug_plan.write_text("# T\n", encoding="utf-8")
    plan_id = derive_plan_id(slug_plan)
    assert plan_id == "2026-09-13-progress-ledger-system"
    assert PLAN_ID_RE.match(plan_id)
    # AC-02: calling it twice returns the same value (never random).
    assert derive_plan_id(slug_plan) == plan_id

    # An explicit value that cannot match PLAN_ID_RE falls back to the slug.
    fallback = tmp_path / "Valid_Stem-Name.md"
    fallback.write_text("---\nplan-id: -bad\n---\n", encoding="utf-8")
    assert derive_plan_id(fallback) == "valid-stem-name"


def test_derive_plan_id_never_raises_on_missing_file(tmp_path):
    missing = tmp_path / "does-not-exist.md"
    assert not missing.exists()
    plan_id = derive_plan_id(missing)
    assert plan_id == "does-not-exist"
    assert PLAN_ID_RE.match(plan_id)

    # A directory raises OSError on read_text; the slug still wins.
    plan_id = derive_plan_id(tmp_path)
    assert plan_id
    assert PLAN_ID_RE.match(plan_id)


def test_normalize_task_id():
    assert normalize_task_id("3") == "task-3"
    assert normalize_task_id("TASK-3") == "task-3"
    assert normalize_task_id("task-3") == "task-3"
    assert normalize_task_id("custom") == "custom"
    assert normalize_task_id("task-") == "task-"

    assert TASK_ID_RE.match("task-3")
    assert not TASK_ID_RE.match("task-")
    assert not TASK_ID_RE.match("3")


def test_make_task_ref_none_and_existing_hash():
    # AC-03: composite reference.
    assert make_task_ref("p", "task-3") == "p#task-3"

    # AC-03: falsy plan_id yields None.
    assert make_task_ref(None, "task-3") is None
    assert make_task_ref("", "task-3") is None

    # Already-composite task ids pass through unchanged.
    assert make_task_ref("p", "p#task-3") == "p#task-3"
    # Falsy plan_id wins over the hash passthrough.
    assert make_task_ref(None, "p#task-3") is None


def test_header_regex_wave_and_task_forms():
    """W2-9 (a): both header forms yield group 1 = task id, group 2 = title.

    Form (i) ``### Task <id>: <title>`` is unchanged; form (ii)
    ``### <W>-<k>: <title>`` is what makes the ledger writer able to address a
    wave-structured plan. Group 1 is the group the ledger path reads --
    ``plan_ledger._task_blocks()`` (``plan_ledger.py:76``) and
    ``spec_plan.parse_task_ledgers()`` (``spec_plan.py:127``) use ``group(1)``
    alone; the only ``group(2)`` consumer is ``spec_plan._parse_plan_tasks()``
    (``spec_plan.py:575``). Both groups must hold for both header forms.
    """

    m = TASK_HEADER_RE.search("### Task task-1: X")
    assert m is not None
    assert m.group(1) == "task-1"
    assert m.group(2) == "X"

    m = TASK_HEADER_RE.search("### W2-0: X")
    assert m is not None
    assert m.group(1) == "W2-0"
    assert m.group(2) == "X"

    m = TASK_HEADER_RE.search("### W1-10: Longer wave title")
    assert m is not None
    assert m.group(1) == "W1-10"
    assert m.group(2) == "Longer wave title"

    m = TASK_HEADER_RE.search("### W2-6 - dash separator")
    assert m is not None
    assert m.group(1) == "W2-6"
    assert m.group(2) == "dash separator"

    # Header without a title at all: the bounded gate accepts end-of-line as the
    # boundary, so the id is found and the title group is empty (not ``None``).
    m = TASK_HEADER_RE.search("### W2-0")
    assert m is not None
    assert m.group(1) == "W2-0"
    assert m.group(2) == ""

    matches = TASK_HEADER_RE.findall(
        "### W2-0: A\n"
        "### W2-1: B\n"
        "### Task task-3: C\n"
    )
    assert matches == [("W2-0", "A"), ("W2-1", "B"), ("task-3", "C")]


def test_header_regex_ignores_non_task_h3_headings():
    """W2-9 (a) / review m4: a plain ``###`` heading must never become a task block.

    Otherwise the parser reads documentation sections as tasks (K53) and the
    ledger writer would happily toggle checkboxes inside them.

    The first two entries are the ``m2`` regression guard: with an unbounded
    ``(?=W[0-9]+-[0-9]+)`` prefix gate they produced the task ids ``W2-0abc``
    and ``W2-0_x``, which ``normalize_task_id`` passes through unchanged --
    self-standing phantom ids that can never be addressed. The last two were
    already rejected and are pinned as such.
    """

    for heading in (
        "### File Structure",
        "### L-1 Checkbox-Abgleich",
        "### 1. Ownership-Matrix W2 (Task x Datei)",
        "### Step-Agent-Map (plan-driven implement, Stufe 3)",
        "### W1-A Insights",
        "## Task task-1: too shallow",
        "### W2-0abc: X",
        "### W2-0_x: X",
        "### W 2-0: X",
        "### Wave 2-0: X",
    ):
        assert TASK_HEADER_RE.search(heading) is None, heading


def test_normalize_task_id_leaves_wave_id_unchanged():
    """W2-9 (f): no-op pin for the wave id.

    ``W2-0`` never matched ``TASK_ID_RE``, so ``normalize_task_id`` takes the
    pass-through branch ``return raw`` -- today and after W2-9. This is a
    plain assertion, deliberately NOT a before/after comparison, and it must
    not be "fixed": a normalization that rewrote ``W2-0`` would break the
    ledger round trip.
    """

    assert normalize_task_id("W2-0") == "W2-0"
    assert normalize_task_id("W1-10") == "W1-10"
    assert TASK_ID_RE.match("W2-0") is None
    assert TASK_ID_RE.match("task-3")
