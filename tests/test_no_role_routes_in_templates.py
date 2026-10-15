"""Guard: spec/plan routing lives in config, not in the source templates.

Implements Spec §A.4 (Revision v6, ``docs/superpowers/specs/2026-09-13-spec-plan-workflow-design.md``):
routing for the spec/plan workflow is declared exclusively in ``config/role-defaults.yaml``
(``quality_pipelines`` / ``reflection_pairs``). The source templates under
``agents/1-generic/*.md``, ``rules/1-generic/*.md`` and the snippets under
``snippets/**/*.md`` (Spec A6 — snippets are inlined into prompts) must stay free of
route tables, ``roleA → roleB`` chains, imperative handoff sentences and role labels
inside ``NEXT:`` blocks for that workflow.

Detection
---------
All classes scan the whole scope (every file below), not only the workflow files.

* ``T-ROUTE-COL``  — table header containing a ``Route`` column.
* ``T-ROLE-ARROW`` — (a) ``roleA → roleB`` where BOTH tokens resolve to the dynamic
  role list (backticks optional); (b) ``text? → `role` `` / ``text) → `role` ``;
  (c) list lines ``- text → `role` `` (class B, no ``?``/``)`` needed). A construct
  whose target is not a role is exempted via ``D-NONROLE``.
* ``T-HANDOFF``    — any phrase from ``dispatch_phrases.en|de`` in
  ``config/active-set-references.yaml`` (e.g. ``hand off to``, ``route to``,
  ``delegier*``, ``beauftrag*``, ``übergib``, ``übernimm*``, ``weise X an``)
  followed by a role token, optionally preceded by ``an|zu|to`` and an article
  (``den|dem|einen|der|die|das|the``). Backticks optional.
* ``T-NEXT``       — ``NEXT: [ ... role ... ]`` (AC-71 class D, every scope file).

Allowed documentation forms (``D-*``)
-------------------------------------
* ``D-BOUNDARY``      — lines inside a ``<context>`` block that carries a
  ``Role and boundary`` heading, lines starting with ``**Not your job:**``, and
  list items under a boundary label (``Not this role``, ``Out of scope``,
  ``What you do NOT do``, ``Boundaries``, ``Delegation (reference only)``).
* ``D-REFERENCE``     — lines starting with ``**Delegation (reference only):**``.
* ``D-PIPELINE``      — the detected construct itself names a pipeline/pair id
  (``quality_pipelines.*`` / ``reflection_pairs.*``) instead of a bare role. This
  is a *construct-scoped* rule: a line that merely mentions a pipeline id no
  longer exempts an unrelated role route on the same line.
* ``D-NONROLE``       — the arrow/handoff connects non-role tokens (paths, status
  lifecycles, template variables) instead of two roles.
* ``D-ORCHESTRATOR``  — the whole ``agents/1-generic/orchestrator.md`` file. The
  orchestrator is THE router (spec §A.4, decision A): its task-size routing table
  and tier/escalation routing are intentional and documented.
* ``D-ESCALATION``    — narrow, role-scoped: only a handoff whose target is
  ``principal-developer`` *and* whose line names the escalation policy
  (``escalat``/``last-resort``/``eskalation``). This replaces the former
  line-wide exemption so other role routes on such lines stay covered.
* ``D-CONDITIONAL``   — IC-30 triage option (1) / IC-18 no. 11: the construct's
  target role is rendered only while that role is active, i.e. the target token
  sits inside the positive branch of ``{{#if ROLE_<TARGET>_ACTIVE}}`` — either a
  block conditional (marker lines of their own) or an inline segment on the
  same line (up to the next ``{{else}}``/``{{/if}}``/``{{#if``). A different
  role's flag never covers a target; an ``{{else}}`` branch is not covered.
  Granted only in files whose conditional markers are well-formed
  (``marker_problems``): balanced, block markers on their own lines closed by
  block markers, inline markers opened and closed on the same line. Mixed or
  unbalanced markers would let the stack/segment logic misread a branch.

PyYAML is used when importable; a stdlib-only regex fallback extracts the role list.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Source artifacts only — templates, rules and snippets. Generated
# .claude/.opencode/... copies are out of scope.
_SCOPE_GLOBS = (
    "agents/1-generic/*.md",
    "rules/1-generic/*.md",
    "snippets/**/*.md",
    "agents/2-platform/*.md",
    "rules/2-platform/*.md",
)

# Spec/plan-workflow files (design addendum §A.2 offender list). Kept for the
# ``workflow_file`` flag of ``classify_line``; T-NEXT itself applies to every scope file.
_WORKFLOW_FILES = frozenset(
    {
        "rules/1-generic/spec-plan-workflow.md",
        "rules/1-generic/brainstorming-gate.md",
        "rules/1-generic/plan-ledger.md",
        "rules/1-generic/writing-plans.md",
        "agents/1-generic/ideation.md",
        "agents/1-generic/concept-specifier.md",
        "agents/1-generic/concept-architect.md",
        "agents/1-generic/concept-reviewer.md",
        "agents/1-generic/planner.md",
        "agents/1-generic/orchestrator.md",
        "agents/1-generic/documenter.md",
        "agents/1-generic/knowledge-ingestor.md",
    }
)

_ROUTE_COL_RE = re.compile(r"(?:^|\|)\s*Route\s*(?:\||$)", re.IGNORECASE)
# Generic backticked arrow; D-NONROLE decides whether the two tokens are roles.
# Both sides are matched whether or not they are backticked; a construct only
# counts as a role route when BOTH tokens resolve to the dynamic role list
# (otherwise D-NONROLE exempts it). Backticks are optional on each side.
_ARROW_RE = re.compile(
    r"(?<![A-Za-z0-9_-])`?([A-Za-z0-9_-]+)`?\s*(?:→|->)\s*"
    r"`?([A-Za-z0-9_-]+)`?(?![A-Za-z0-9_-])"
)
_ARROW_TEXT_RE = re.compile(
    # "Write tests? -> `tester`": the left side is prose (ends with ``?``/``)``),
    # so the adjacent-token pattern above cannot see it (IC-30, #885 class B).
    r"[?)]`?\s*(?:→|->)\s*`?([A-Za-z0-9_-]+)`?(?![A-Za-z0-9_-])"
)
_ARROW_LIST_RE = re.compile(r"(?:→|->)\s*`([A-Za-z0-9_-]+)`(?![A-Za-z0-9_-])")
_LIST_ITEM_RE = re.compile(r"^\s*(?:[-*]|\d+\.)\s")
# Header lines that open a boundary list (items below are role boundaries, not routes).
_BOUNDARY_LABEL_RE = re.compile(
    r"not this role|out of scope|do(?:es)? not (?:do|cover|check)|\bnot your job\b"
    r"|boundaries|reference only",
    re.IGNORECASE,
)
_DISPATCH_PHRASES_FILE = Path("config") / "active-set-references.yaml"
_HANDOFF_RE_CACHE: dict[Path, "re.Pattern[str]"] = {}


def load_dispatch_phrases(repo_root: Path = REPO_ROOT) -> list[str]:
    """``dispatch_phrases.de`` + ``.en`` from config (shared with IC-19; never hardcoded)."""
    data = _load_yaml(repo_root / _DISPATCH_PHRASES_FILE)
    phrases = data.get("dispatch_phrases") or {}
    return list(phrases.get("en") or []) + list(phrases.get("de") or [])


def build_handoff_re(phrases: list[str]) -> "re.Pattern[str]":
    alternation = "|".join(f"(?:{phrase})" for phrase in phrases)
    return re.compile(
        rf"(?i)(?:{alternation})"
        r"\s+(?:(?:an|zu|to)\s+)?"
        r"(?:the\s+|der\s+|die\s+|das\s+|den\s+|dem\s+|einen\s+)?"
        r"`?([A-Za-z0-9_.-]+)`?"
    )


def handoff_re(repo_root: Path = REPO_ROOT) -> "re.Pattern[str]":
    if repo_root not in _HANDOFF_RE_CACHE:
        _HANDOFF_RE_CACHE[repo_root] = build_handoff_re(load_dispatch_phrases(repo_root))
    return _HANDOFF_RE_CACHE[repo_root]



_NEXT_RE = re.compile(r"^\s*NEXT:\s*\[([^\]]*)\]")

# Narrow, role-scoped replacement for the former line-wide D-ESCALATION rule:
# only a handoff whose target is the last-resort tier *and* whose line names the
# escalation policy is exempted. All other role routes stay covered.
_ESCALATION_RE = re.compile(r"escalat|last-resort|eskalation", re.IGNORECASE)
_ESCALATION_TARGETS = frozenset({"principal-developer"})

# The orchestrator IS the sanctioned router (spec §A.4, decision A): its
# task-size routing table and tier/escalation routing are legitimate, so its
# whole file is exempt via the documented ``D-ORCHESTRATOR`` rule. Every other
# scope file stays subject to the route guard.
_ORCHESTRATOR_FILE = "agents/1-generic/orchestrator.md"

_REFERENCE_PREFIX = "**Delegation (reference only):**"
_NOT_YOUR_JOB_PREFIX = "**Not your job:**"
_BOUNDARY_PREFIXES = (_NOT_YOUR_JOB_PREFIX, "**Boundary:**", "**Scope:**")
_FORBIDDEN_REFERENCE_TOKENS = ("background(", "invoke_subagent", "task(subagent_type")

_INLINE_ROLE_IF_RE = re.compile(r"\{\{#if ROLE_([A-Z0-9_]+)_ACTIVE\}\}")
_INLINE_SEGMENT_END_RE = re.compile(r"\{\{else\}\}|\{\{/if\}\}|\{\{#if ")
_BLOCK_IF_RE = re.compile(r"^\s*\{\{#if (\w+)\}\}\s*$")
_BLOCK_ELSE_RE = re.compile(r"^\s*\{\{else\}\}\s*$")
_BLOCK_ENDIF_RE = re.compile(r"^\s*\{\{/if\}\}\s*$")

_CONTEXT_OPEN = "<context>"
_CONTEXT_CLOSE = "</context>"
_BOUNDARY_HEADING_RE = re.compile(r"^##\s+Role and boundary\s*$")


# Ratchet registry (IC-30, #885): existing uncovered constructs as "file:class" (no line
# numbers). May only shrink; new hits fail. Emptied by the Phase-1 triage (Task 1.19,
# AC-71): every former entry is now conditional on its target role (D-CONDITIONAL),
# so classes A/D/E and the B/C/F lines no longer need a registry entry.
ROUTE_RATCHET: frozenset[str] = frozenset()


@dataclass
class Finding:
    """One uncovered routing construct."""

    path: str
    line: int
    kind: str
    text: str
    reasons: list[str] = field(default_factory=list)

    def __str__(self) -> str:  # pragma: no cover - diagnostic helper
        return f"{self.path}:{self.line}: {self.kind}: {self.text.strip()}"


def _load_yaml(path: Path) -> dict:
    try:
        import yaml  # noqa: PLC0415 - optional dependency
    except ImportError:  # pragma: no cover - PyYAML present in this repo's test env
        return _parse_role_names_regex(path)
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _parse_role_names_regex(path: Path) -> dict:
    """Stdlib-only fallback: 2-space-indented keys *under* the ``roles:`` block.

    Scoping matters: a bare ``^\\s{2}key:`` scan would also collect 2-space keys
    of every other top-level block (platforms, quality_pipelines, ...) and turn
    them into phantom roles. Only the ``roles:`` block's direct children count.
    """
    names: list[str] = []
    in_roles = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^roles:\s*$", line):
            in_roles = True
            continue
        if in_roles and re.match(r"^\S", line):
            # A new top-level key ends the roles block.
            break
        if in_roles:
            match = re.match(r"^\s{2}([A-Za-z0-9_-]+):\s*$", line)
            if match and match.group(1) not in names:
                names.append(match.group(1))
    return {"roles": {name: {} for name in names}}


def load_roles(repo_root: Path = REPO_ROOT) -> set[str]:
    """Role names from ``config/role-defaults.yaml`` (never hardcoded)."""
    data = _load_yaml(repo_root / "config" / "role-defaults.yaml")
    return set((data.get("roles") or {}).keys())


def load_pipeline_ids(repo_root: Path = REPO_ROOT) -> set[str]:
    """Pipeline + reflection-pair ids (targets for the ``D-PIPELINE`` allow rule)."""
    data = _load_yaml(repo_root / "config" / "role-defaults.yaml")
    pipelines = set((data.get("quality_pipelines") or {}).keys())
    pairs = {entry.get("id") for entry in (data.get("reflection_pairs") or []) if entry}
    return pipelines | pairs


# Module-level default (REPO_ROOT config), kept for the public ``_HANDOFF_RE`` interface.
_HANDOFF_RE = handoff_re(REPO_ROOT)


def iter_scope_files(repo_root: Path = REPO_ROOT) -> list[Path]:
    files: list[Path] = []
    for pattern in _SCOPE_GLOBS:
        files.extend(sorted(repo_root.glob(pattern)))
    return files


def boundary_lines(text: str) -> set[int]:
    """1-based line numbers inside a ``<context>`` block with a ``Role and boundary`` heading."""
    allowed: set[int] = set()
    in_context = False
    has_boundary = False
    block_start = 0
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped == _CONTEXT_OPEN:
            in_context = True
            has_boundary = False
            block_start = number
            continue
        if stripped == _CONTEXT_CLOSE:
            if in_context and has_boundary:
                allowed.update(range(block_start, number + 1))
            in_context = False
            has_boundary = False
            continue
        if in_context and _BOUNDARY_HEADING_RE.match(line):
            has_boundary = True
    return allowed


def boundary_section_lines(text: str) -> set[int]:
    """1-based numbers of list items directly under a boundary label line.

    A label line (``**What you do NOT do:**``, ``## Out of scope`` ...) opens a
    section; it ends at the first non-list text line or heading after the items.
    """
    allowed: set[int] = set()
    active = False
    seen_item = False
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if _BOUNDARY_LABEL_RE.search(stripped) and not _LIST_ITEM_RE.match(line):
            active, seen_item = True, False
            continue
        if not active:
            continue
        if _LIST_ITEM_RE.match(line):
            allowed.add(number)
            seen_item = True
        elif not stripped:
            if seen_item:
                active = False
        elif stripped.startswith("#") or (seen_item and not line.startswith((" ", "\t"))):
            active = False
    return allowed


def _flag_role(flag: str) -> str | None:
    """``ROLE_SENIOR_DEVELOPER_ACTIVE`` -> ``senior-developer`` (else ``None``)."""
    if flag.startswith("ROLE_") and flag.endswith("_ACTIVE"):
        return flag[len("ROLE_"):-len("_ACTIVE")].lower().replace("_", "-")
    return None


_MARKER_RE = re.compile(r"\{\{(#if|#unless) (\w+)\}\}|\{\{(else)\}\}|\{\{/(if|unless)\}\}")


def marker_problems(text: str) -> list[tuple[int, str]]:
    """``(line, problem)`` for unbalanced or mixed block/inline conditional markers.

    A marker alone on its line is a block marker, any other is inline. A block
    open must be continued/closed by block markers; an inline open must be
    continued/closed on the same line; the marker kinds must match; nothing may
    stay open at the end of the file.
    """
    stack: list[tuple[str, str, int]] = []
    problems: list[tuple[int, str]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        markers = list(_MARKER_RE.finditer(line))
        form = "block" if len(markers) == 1 and line.strip() == markers[0].group(0) else "inline"
        for marker in markers:
            if marker.group(1):
                stack.append((marker.group(1)[1:], form, number))
                continue
            top = stack[-1] if stack else None
            same = top is not None and top[1] == form and (form == "block" or top[2] == number)
            if marker.group(3):
                if not (same and top[0] == "if"):
                    problems.append((number, "else-mismatch"))
                continue
            if top is None:
                problems.append((number, "close-without-open"))
                continue
            stack.pop()
            if not same or top[0] != marker.group(4):
                problems.append((number, "close-mismatch"))
    problems += [(number, "unclosed") for _, _, number in stack]
    return problems


def conditional_block_roles(text: str) -> dict[int, frozenset[str]]:
    """1-based line -> roles whose block ``{{#if ROLE_*_ACTIVE}}`` (positive branch) encloses it."""
    stack: list[tuple[str | None, bool]] = []
    covered: dict[int, frozenset[str]] = {}
    for number, line in enumerate(text.splitlines(), start=1):
        opened = _BLOCK_IF_RE.match(line)
        if opened:
            stack.append((_flag_role(opened.group(1)), True))
            continue
        if _BLOCK_ELSE_RE.match(line):
            if stack:
                role, _positive = stack[-1]
                stack[-1] = (role, False)
            continue
        if _BLOCK_ENDIF_RE.match(line):
            if stack:
                stack.pop()
            continue
        roles = frozenset(role for role, positive in stack if role and positive)
        if roles:
            covered[number] = roles
    return covered


def inline_conditional_spans(line: str) -> list[tuple[int, int, str]]:
    """``(start, end, role)`` spans of inline ``{{#if ROLE_*_ACTIVE}}`` positive branches."""
    spans = []
    for match in _INLINE_ROLE_IF_RE.finditer(line):
        end_match = _INLINE_SEGMENT_END_RE.search(line, match.end())
        end = end_match.start() if end_match else len(line)
        spans.append((match.end(), end, match.group(1).lower().replace("_", "-")))
    return spans


def _pipeline_target(token: str, pipeline_ids: set[str]) -> bool:
    """Case-insensitive membership check for a pipeline/pair id token."""
    return token in pipeline_ids or token.lower() in {p.lower() for p in pipeline_ids}


def classify_line(
    line: str,
    *,
    roles: set[str],
    pipeline_ids: set[str],
    is_boundary: bool,
    workflow_file: bool,
    is_orchestrator: bool = False,
    handoff_pattern: "re.Pattern[str] | None" = None,
    block_roles: frozenset = frozenset(),
    allow_conditional: bool = True,
) -> list[tuple[str, list[str]]]:
    """Return ``[(kind, allowed_reasons), ...]`` for one line.

    An entry with an empty ``reasons`` list is an uncovered routing construct.
    ``D-PIPELINE`` is construct-scoped: it is attached only when the detected
    construct's own token(s) name a pipeline/pair id — never because the line
    happens to mention ``quality_pipelines.`` somewhere. ``D-CONDITIONAL`` is
    construct-scoped as well: only the target token's own ``ROLE_*_ACTIVE``
    gate (``block_roles`` of the enclosing block conditionals, or an inline
    segment on this line) covers it.
    """
    constructs: list[tuple[str, list[str]]] = []
    spans = inline_conditional_spans(line)

    def conditional(role: str, pos: int) -> bool:
        if not allow_conditional:
            return False
        return role in block_roles or any(
            start <= pos < end and span_role == role for start, end, span_role in spans)

    reasons: list[str] = []
    if is_boundary or line.lstrip().startswith(_BOUNDARY_PREFIXES):
        reasons.append("D-BOUNDARY")
    if line.lstrip().startswith(_REFERENCE_PREFIX):
        reasons.append("D-REFERENCE")
    if is_orchestrator:
        reasons.append("D-ORCHESTRATOR")

    if _ROUTE_COL_RE.search(line):
        constructs.append(("T-ROUTE-COL", list(reasons)))

    for arrow in _ARROW_RE.finditer(line):
        first, second = arrow.group(1), arrow.group(2)
        arrow_reasons = list(reasons)
        if _pipeline_target(first, pipeline_ids) or _pipeline_target(second, pipeline_ids):
            arrow_reasons.append("D-PIPELINE")
        if not (first in roles and second in roles):
            arrow_reasons.append("D-NONROLE")
        if conditional(second, arrow.start(2)):
            arrow_reasons.append("D-CONDITIONAL")
        constructs.append(("T-ROLE-ARROW", arrow_reasons))

    text_targets = list(_ARROW_TEXT_RE.finditer(line))
    if _LIST_ITEM_RE.match(line):
        text_targets += list(_ARROW_LIST_RE.finditer(line))
    for text_match in text_targets:
        target = text_match.group(1)
        # ``text -> role``: only exempt when the right side is not a role (D-NONROLE).
        text_reasons = list(reasons)
        if _pipeline_target(target, pipeline_ids):
            text_reasons.append("D-PIPELINE")
        if target not in roles:
            text_reasons.append("D-NONROLE")
        if conditional(target, text_match.start(1)):
            text_reasons.append("D-CONDITIONAL")
        constructs.append(("T-ROLE-ARROW", text_reasons))

    pattern = handoff_pattern or _HANDOFF_RE
    for match in pattern.finditer(line):
        target = match.group(1).lower()
        handoff_reasons = list(reasons)
        is_pipeline_target = _pipeline_target(target, pipeline_ids)
        if is_pipeline_target:
            handoff_reasons.append("D-PIPELINE")
        if target in _ESCALATION_TARGETS and _ESCALATION_RE.search(line):
            handoff_reasons.append("D-ESCALATION")
        if conditional(target, match.start(1)):
            handoff_reasons.append("D-CONDITIONAL")
        if target in roles or is_pipeline_target:
            constructs.append(("T-HANDOFF", handoff_reasons))

    # T-NEXT applies to every scope file (AC-71 class D); ``workflow_file`` is
    # retained only for call-site compatibility.
    next_match = _NEXT_RE.search(line)
    if next_match:
        hits = [
            (role, next_match.start(1) + hit.start())
            for role in roles
            for hit in re.finditer(
                rf"(?i)(?<![\w-]){re.escape(role)}(?![\w-])", next_match.group(1))
        ]
        if hits:
            next_reasons = list(reasons)
            if all(conditional(role, pos) for role, pos in hits):
                next_reasons.append("D-CONDITIONAL")
            constructs.append(("T-NEXT", next_reasons))

    return constructs


def find_findings(repo_root: Path = REPO_ROOT) -> list[Finding]:
    roles = load_roles(repo_root)
    pipeline_ids = load_pipeline_ids(repo_root)
    handoff_pattern = handoff_re(repo_root)
    findings: list[Finding] = []
    for path in iter_scope_files(repo_root):
        rel = path.relative_to(repo_root).as_posix()
        text = path.read_text(encoding="utf-8")
        boundary = boundary_lines(text) | boundary_section_lines(text)
        wellformed = not marker_problems(text)
        block_roles = conditional_block_roles(text) if wellformed else {}
        is_workflow = rel in _WORKFLOW_FILES
        is_orchestrator = rel == _ORCHESTRATOR_FILE
        for number, line in enumerate(text.splitlines(), start=1):
            for kind, reasons in classify_line(
                line,
                roles=roles,
                pipeline_ids=pipeline_ids,
                is_boundary=number in boundary,
                workflow_file=is_workflow,
                is_orchestrator=is_orchestrator,
                handoff_pattern=handoff_pattern,
                block_roles=block_roles.get(number, frozenset()),
                allow_conditional=wellformed,
            ):
                if not reasons:
                    findings.append(Finding(rel, number, kind, line))
    return findings


def _reference_lines(repo_root: Path = REPO_ROOT) -> list[tuple[str, int, str]]:
    lines: list[tuple[str, int, str]] = []
    for path in iter_scope_files(repo_root):
        rel = path.relative_to(repo_root).as_posix()
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if line.lstrip().startswith(_REFERENCE_PREFIX):
                lines.append((rel, number, line))
    return lines


def _key(finding: Finding) -> str:
    return f"{finding.path}:{finding.kind}"


def new_findings(repo_root: Path = REPO_ROOT, ratchet: frozenset = ROUTE_RATCHET) -> list[Finding]:
    """Findings not covered by the ratchet registry."""
    return [f for f in find_findings(repo_root) if _key(f) not in ratchet]


def stale_ratchet_entries(
    repo_root: Path = REPO_ROOT, ratchet: frozenset = ROUTE_RATCHET
) -> list[str]:
    """Registry entries without a current hit (must be removed: ratchet only shrinks)."""
    current = {_key(f) for f in find_findings(repo_root)}
    return sorted(ratchet - current)


def test_no_uncovered_role_routes_in_templates():
    findings = new_findings()
    assert findings == [], "Uncovered routing constructs:\n" + "\n".join(
        str(f) for f in findings
    )


def test_route_ratchet_only_shrinks():
    stale = stale_ratchet_entries()
    assert stale == [], (
        "ROUTE_RATCHET entries without a hit - remove them (ratchet may only shrink):\n"
        + "\n".join(stale)
    )


def _fixture_repo(tmp_path: Path, template_body: str, rel: str = "agents/2-platform/x.md") -> Path:
    (tmp_path / "config").mkdir(parents=True)
    for name in ("role-defaults.yaml", "active-set-references.yaml"):
        (tmp_path / "config" / name).write_text(
            (REPO_ROOT / "config" / name).read_text(encoding="utf-8"), encoding="utf-8"
        )
    target = tmp_path / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(template_body, encoding="utf-8")
    return tmp_path


def test_new_german_imperative_in_fixture_template_fails_guard(tmp_path):
    root = _fixture_repo(tmp_path, "# X\n\nDelegiere an `tester`, wenn fertig.\n")
    hits = new_findings(root)
    assert [(h.kind, h.line) for h in hits] == [("T-HANDOFF", 3)]


def test_fixture_in_platform_rules_scope_is_scanned(tmp_path):
    root = _fixture_repo(
        tmp_path, "Bitte beauftrage den `developer` mit dem Fix.\n", "rules/2-platform/r.md"
    )
    assert [h.kind for h in new_findings(root)] == ["T-HANDOFF"]


def test_new_hit_in_ratcheted_file_other_class_still_fails(tmp_path):
    root = _fixture_repo(tmp_path, "Delegiere an `tester`.\n", "agents/1-generic/developer.md")
    assert new_findings(root, ratchet=frozenset({"agents/1-generic/developer.md:T-ROLE-ARROW"}))
    assert not new_findings(root, ratchet=frozenset({"agents/1-generic/developer.md:T-HANDOFF"}))


def test_guard_and_config_share_dispatch_phrases():
    phrases = load_dispatch_phrases()
    assert phrases, "dispatch_phrases.de/en must be configured"
    data = _load_yaml(REPO_ROOT / "config" / "active-set-references.yaml")
    assert set(data["dispatch_phrases"]) == {"de", "en"}
    assert "provider_literal_allow" in data


def test_885_negative_anchors_are_flagged():
    roles = load_roles()
    pipeline_ids = load_pipeline_ids()
    for line in (
        "Delegiere an `knowledge-indexer`.",
        "Delegiere an `tester`.",
        "- Write tests? → `tester`",
        "Übergib an den `developer`.",
        "Leite das weiter: übernimm `validator`.",
    ):
        constructs = classify_line(
            line,
            roles=roles | {"knowledge-indexer"},
            pipeline_ids=pipeline_ids,
            is_boundary=False,
            workflow_file=False,
        )
        assert any(reasons == [] for _, reasons in constructs), f"not flagged: {line!r}"


def test_delegation_reference_lines_have_no_dispatch_semantics():
    # The former ``"reference only" in line`` assertion was tautological: the
    # marker constant already contains that phrase. Reference-only headings may
    # be bare (the delegated items follow as bullets), so the meaningful
    # invariant is the absence of executable dispatch semantics.
    for rel, number, line in _reference_lines():
        for token in _FORBIDDEN_REFERENCE_TOKENS:
            assert token not in line, f"{rel}:{number}: dispatch token {token!r} in reference line"


def test_next_role_labels_absent_in_spec_plan_workflow_scope():
    findings = [f for f in new_findings() if f.kind == "T-NEXT"]
    assert findings == [], "Role labels in NEXT: for spec/plan workflow:\n" + "\n".join(
        str(f) for f in findings
    )


def test_non_role_arrows_are_allowed_by_d_nonrole():
    roles = load_roles()
    constructs = classify_line(
        "- After `up` → `down` → `up`, confirm the schema reproduces deterministically",
        roles=roles,
        pipeline_ids=load_pipeline_ids(),
        is_boundary=False,
        workflow_file=False,
    )
    assert constructs, "expected the generic arrow to be detected"
    assert all("D-NONROLE" in reasons for _, reasons in constructs)


def test_pipeline_named_handoff_is_allowed_by_d_pipeline():
    roles = load_roles()
    constructs = classify_line(
        "- Do not auto-hand-off to the `feature-lifecycle` pipeline",
        roles=roles,
        pipeline_ids=load_pipeline_ids(),
        is_boundary=False,
        workflow_file=False,
    )
    assert constructs, "expected the pipeline handoff to be detected"
    assert all("D-PIPELINE" in reasons for _, reasons in constructs)


def test_d_pipeline_is_construct_scoped_not_line_wide():
    """M2: a pipeline mention elsewhere must not exempt a role route.

    ``D-PIPELINE`` applies only when the *detected construct's own token* names
    a pipeline/pair id. A bare ``concept-specifier`` → ``concept-reviewer``
    arrow on a line that also mentions ``quality_pipelines.*`` stays uncovered.
    """
    line = (
        "Route: `quality_pipelines.concept-driven-dev` — danach "
        "`concept-specifier` → `concept-reviewer`."
    )
    constructs = classify_line(
        line,
        roles=load_roles(),
        pipeline_ids=load_pipeline_ids(),
        is_boundary=False,
        workflow_file=False,
    )
    arrows = [reasons for kind, reasons in constructs if kind == "T-ROLE-ARROW"]
    assert arrows, "expected the role arrow to be detected"
    assert all("D-PIPELINE" not in reasons for reasons in arrows), (
        "a pipeline mention elsewhere on the line must not exempt a role route"
    )
    assert all(reasons == [] for reasons in arrows), (
        "the bare role route must be uncovered"
    )


def test_canonical_offender_lines_are_flagged():
    """L3 negative anchor: canonical offenders must still be uncovered.

    Guards against a future widening of the ``D-*`` rules silently turning the
    whole guard into a no-op.
    """
    roles = load_roles()
    pipeline_ids = load_pipeline_ids()
    cases = {
        "arrow": "Ablauf: `concept-specifier` → `concept-reviewer`, dann Plan.",
        "handoff_article": "Bitte delegiert an den `concept-reviewer` für Review.",
        "handoff_back": "Then hand back to the `developer` for the fix.",
        "arrow_unbackticked": "Ablauf: concept-specifier → concept-reviewer, dann Plan.",
    }
    for label, line in cases.items():
        constructs = classify_line(
            line,
            roles=roles,
            pipeline_ids=pipeline_ids,
            is_boundary=False,
            workflow_file=False,
        )
        assert constructs, f"{label}: offender line was not detected"
        assert any(reasons == [] for _, reasons in constructs), (
            f"{label}: offender line was incorrectly exempted: {line!r}"
        )


def test_d_escalation_allows_escalation_handoff_to_principal_developer():
    """D-ESCALATION: escalation handoff to ``principal-developer`` is allowed."""
    constructs = classify_line(
        "Only as a last-resort escalation: hand off to the `principal-developer`.",
        roles=load_roles(),
        pipeline_ids=load_pipeline_ids(),
        is_boundary=False,
        workflow_file=False,
    )
    handoffs = [reasons for kind, reasons in constructs if kind == "T-HANDOFF"]
    assert handoffs, "expected the escalation handoff to be detected"
    assert all("D-ESCALATION" in reasons for reasons in handoffs)


def test_d_escalation_requires_escalation_keyword():
    """D-ESCALATION: same target without an escalation keyword stays uncovered."""
    constructs = classify_line(
        "Hand off to the `principal-developer` to finish the task.",
        roles=load_roles(),
        pipeline_ids=load_pipeline_ids(),
        is_boundary=False,
        workflow_file=False,
    )
    assert constructs, "expected the handoff to be detected"
    assert any(reasons == [] for _, reasons in constructs), (
        "principal-developer handoff without an escalation keyword must be flagged"
    )


def test_d_escalation_requires_principal_developer_target():
    """D-ESCALATION: escalation keyword with another role stays uncovered."""
    constructs = classify_line(
        "Escalation path: hand off to the `developer` for the fix.",
        roles=load_roles(),
        pipeline_ids=load_pipeline_ids(),
        is_boundary=False,
        workflow_file=False,
    )
    assert constructs, "expected the handoff to be detected"
    assert all("D-ESCALATION" not in reasons for _, reasons in constructs)
    assert any(reasons == [] for _, reasons in constructs), (
        "escalation keyword with a non-escalation role must be flagged"
    )


def test_custom_dispatch_phrase_from_config_is_detected(tmp_path):
    """The guard must derive its phrases from the config file, not a hardcoded list."""
    body = "Please zzhandoff the `tester` now.\n"
    control = tmp_path / "control"
    control.mkdir()
    assert new_findings(_fixture_repo(control, body)) == [], "unconfigured phrase must not hit"
    configured = tmp_path / "configured"
    configured.mkdir()
    root = _fixture_repo(configured, body)
    cfg = root / "config" / "active-set-references.yaml"
    cfg.write_text(
        cfg.read_text(encoding="utf-8").replace("  en:\n", "  en:\n    - 'zzhandoff'\n", 1),
        encoding="utf-8",
    )
    assert [h.kind for h in new_findings(root)] == ["T-HANDOFF"]


def test_next_block_with_role_is_flagged_in_every_scope_file(tmp_path):
    """AC-71 class D: ``NEXT: [... role ...]`` is no longer limited to workflow files."""
    root = _fixture_repo(tmp_path, "# X\n\nNEXT: [Review | tester]\n")
    assert [(h.kind, h.line) for h in new_findings(root)] == [("T-NEXT", 3)]


def test_next_block_without_role_is_allowed(tmp_path):
    root = _fixture_repo(tmp_path, "# X\n\nNEXT: [Review | Tests | Commit]\n")
    assert new_findings(root) == []


def test_list_arrow_route_without_question_mark_is_flagged(tmp_path):
    """#885 class B: ``- text -> `role` `` needs no ``?``/``)`` on the left side."""
    root = _fixture_repo(tmp_path, "# X\n\n- Update the docs → `documenter`\n")
    assert [(h.kind, h.line) for h in new_findings(root)] == [("T-ROLE-ARROW", 3)]


def test_list_arrow_to_non_role_is_allowed(tmp_path):
    root = _fixture_repo(tmp_path, "# X\n\n- retry → fallback → `failed` when exhausted\n")
    assert new_findings(root) == []


def test_list_arrow_under_out_of_scope_label_is_allowed(tmp_path):
    body = (
        "# X\n\n**What you do NOT do:**\n- Code quality → `code-reviewer`\n"
        "- Tests → `tester`\n\nOther text.\n\n- Docs → `documenter`\n"
    )
    root = _fixture_repo(tmp_path, body)
    assert [(h.kind, h.line) for h in new_findings(root)] == [("T-ROLE-ARROW", 9)]


def test_section_label_variants_open_boundary_sections():
    text = "Not this role:\n- a → `tester`\n\n## Out of scope\n\n- b → `tester`\n"
    assert boundary_section_lines(text) == {2, 6}


# --- IC-30 triage (Task 1.19, AC-71): D-CONDITIONAL and the emptied ratchet --------


def test_route_ratchet_is_empty_after_triage():
    """AC-71: classes A (HANDOFF), D (NEXT), E (German) are empty; B/C/F lines are
    conditional, under an allow marker or in data -- so no registry entry remains."""
    assert ROUTE_RATCHET == frozenset()


def test_block_conditional_on_target_role_is_allowed(tmp_path):
    body = "# X\n\n{{#if ROLE_TESTER_ACTIVE}}\n- Write tests? → `tester`\n{{/if}}\n"
    assert new_findings(_fixture_repo(tmp_path, body)) == []


def test_inline_conditional_on_target_role_is_allowed(tmp_path):
    body = "# X\n\n- Write tests?{{#if ROLE_TESTER_ACTIVE}} → `tester`{{else}}{{/if}}\n"
    assert new_findings(_fixture_repo(tmp_path, body)) == []


def test_conditional_on_other_role_does_not_cover(tmp_path):
    body = "# X\n\n{{#if ROLE_DOCUMENTER_ACTIVE}}\nDelegiere an `tester`.\n{{/if}}\n"
    assert [(h.kind, h.line) for h in new_findings(_fixture_repo(tmp_path, body))] == [
        ("T-HANDOFF", 4)]


def test_else_branch_is_not_covered(tmp_path):
    body = ("# X\n\n{{#if ROLE_TESTER_ACTIVE}}\nok\n{{else}}\nDelegiere an `tester`.\n{{/if}}\n")
    assert [(h.kind, h.line) for h in new_findings(_fixture_repo(tmp_path, body))] == [
        ("T-HANDOFF", 6)]


def test_inline_segment_ends_at_else(tmp_path):
    body = "# X\n\n- Tests?{{#if ROLE_TESTER_ACTIVE}} ok{{else}} → `tester`{{/if}}\n"
    assert [h.kind for h in new_findings(_fixture_repo(tmp_path, body))] == ["T-ROLE-ARROW"]


def test_next_block_needs_every_role_conditional(tmp_path):
    covered = ("# X\n\nNEXT: [Review{{#if ROLE_DEVELOPER_ACTIVE}} | Developer fix{{/if}}"
               "{{#if ROLE_DOCUMENTER_ACTIVE}} | Documenter{{/if}}]\n")
    assert new_findings(_fixture_repo(tmp_path / "a", covered)) == []
    partial = "# X\n\nNEXT: [Review{{#if ROLE_DEVELOPER_ACTIVE}} | Developer fix{{/if}} | Documenter]\n"
    assert [h.kind for h in new_findings(_fixture_repo(tmp_path / "b", partial))] == ["T-NEXT"]


# --- review fixes: D-CONDITIONAL bypasses and marker balance ------------------


def test_bypass_block_open_closed_inline_is_not_covered(tmp_path):
    # (a) a block open closed by an inline {{/if}} at the end of a content line
    body = ("# X\n\n{{#if ROLE_TESTER_ACTIVE}}\nok{{/if}}\nDelegiere an `tester`.\n")
    assert [h.kind for h in new_findings(_fixture_repo(tmp_path, body))] == ["T-HANDOFF"]


def test_bypass_inline_else_inside_block_is_not_covered(tmp_path):
    # (b) an inline {{else}} inside a block conditional
    body = ("# X\n\n{{#if ROLE_TESTER_ACTIVE}}\nok {{else}} Delegiere an `tester`.\n{{/if}}\n")
    assert [h.kind for h in new_findings(_fixture_repo(tmp_path, body))] == ["T-HANDOFF"]


def test_bypass_unclosed_inline_open_is_not_covered(tmp_path):
    # (c) an inline {{#if ROLE_X_ACTIVE}} without {{/if}}
    body = "# X\n\n- Tests?{{#if ROLE_TESTER_ACTIVE}} → `tester`\n"
    assert [h.kind for h in new_findings(_fixture_repo(tmp_path, body))] == ["T-ROLE-ARROW"]


def test_marker_problems_detects_each_bypass():
    assert marker_problems("{{#if A}}\nx{{/if}}\n")
    assert marker_problems("{{#if A}}\nx {{else}} y\n{{/if}}\n")
    assert marker_problems("x {{#if A}} y\n")
    assert marker_problems("{{#if A}}\nx\n{{else}}\ny\n{{/if}}\nz {{#if B}}w{{else}}{{/if}}\n") == []


# templates/context/ is rendered by the context engine with handlebars-style
# multi-line inline markers ({{#each}}); it is not an agent/rule source.
_BALANCE_GLOBS = ("agents/**/*.md", "rules/**/*.md", "commands/**/*.md", "snippets/**/*.md",
                  "templates/*.md", "templates/bootstrap/*.md", "templates/configs/*.md",
                  "templates/docs/*.md")


def test_repo_conditional_markers_are_well_formed():
    bad = {}
    for pattern in _BALANCE_GLOBS:
        for path in sorted(REPO_ROOT.glob(pattern)):
            problems = marker_problems(path.read_text(encoding="utf-8"))
            if problems:
                bad[path.relative_to(REPO_ROOT).as_posix()] = problems[:3]
    assert bad == {}, bad
