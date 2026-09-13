"""Guard: spec/plan routing lives in config, not in the source templates.

Implements Spec §A.4 (Revision v6, ``docs/superpowers/specs/2026-09-13-spec-plan-workflow-design.md``):
routing for the spec/plan workflow is declared exclusively in ``config/role-defaults.yaml``
(``quality_pipelines`` / ``reflection_pairs``). The source templates under
``agents/1-generic/*.md`` and ``rules/1-generic/*.md`` must stay free of route tables,
``roleA → roleB`` chains, imperative handoff sentences and role labels inside ``NEXT:``
blocks for that workflow.

Detection
---------
* ``T-ROUTE-COL``  — table header containing a ``Route`` column. Scans the whole scope.
* ``T-ROLE-ARROW`` — ``roleA → roleB`` where BOTH tokens resolve to the dynamic
  role list. Backticks are optional on each side; a construct whose tokens do not
  both resolve to roles is exempted via ``D-NONROLE``. Scans the whole scope.
* ``T-HANDOFF``    — ``hand off to | hand back to | delegiert an | route to |
  dispatch(e) an | weiter(leiten) an`` followed by a role token, optionally
  preceded by a German article (``den|dem|einen|der|die|das``) or ``the``.
  Backticks optional. Scans the whole scope.
* ``T-NEXT``       — ``NEXT: [ ... role ... ]``. Restricted to the spec/plan-workflow
  files listed in the design addendum §A.2 offender list.

Allowed documentation forms (``D-*``)
-------------------------------------
* ``D-BOUNDARY``      — lines inside a ``<context>`` block that carries a
  ``Role and boundary`` heading, or lines starting with ``**Not your job:**``.
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

PyYAML is used when importable; a stdlib-only regex fallback extracts the role list.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Source templates only — generated .claude/.opencode/... copies are out of scope.
_SCOPE_GLOBS = ("agents/1-generic/*.md", "rules/1-generic/*.md")

# Spec/plan-workflow files (design addendum §A.2 offender list). T-NEXT applies here only.
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
_HANDOFF_RE = re.compile(
    r"(?i)(?:hand[ -]?off to|hand back to|delegiert an|route to|"
    r"dispatch(?:e)? an|weiter(?:leiten)? an)"
    r"\s+(?:the\s+|der\s+|die\s+|das\s+|den\s+|dem\s+|einen\s+)?"
    r"`?([A-Za-z0-9_.-]+)`?"
)
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
_FORBIDDEN_REFERENCE_TOKENS = ("background(", "invoke_subagent", "task(subagent_type")

_CONTEXT_OPEN = "<context>"
_CONTEXT_CLOSE = "</context>"
_BOUNDARY_HEADING_RE = re.compile(r"^##\s+Role and boundary\s*$")


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
) -> list[tuple[str, list[str]]]:
    """Return ``[(kind, allowed_reasons), ...]`` for one line.

    An entry with an empty ``reasons`` list is an uncovered routing construct.
    ``D-PIPELINE`` is construct-scoped: it is attached only when the detected
    construct's own token(s) name a pipeline/pair id — never because the line
    happens to mention ``quality_pipelines.`` somewhere.
    """
    constructs: list[tuple[str, list[str]]] = []

    reasons: list[str] = []
    if is_boundary or line.lstrip().startswith(_NOT_YOUR_JOB_PREFIX):
        reasons.append("D-BOUNDARY")
    if line.lstrip().startswith(_REFERENCE_PREFIX):
        reasons.append("D-REFERENCE")
    if is_orchestrator:
        reasons.append("D-ORCHESTRATOR")

    if _ROUTE_COL_RE.search(line):
        constructs.append(("T-ROUTE-COL", list(reasons)))

    for first, second in _ARROW_RE.findall(line):
        arrow_reasons = list(reasons)
        if _pipeline_target(first, pipeline_ids) or _pipeline_target(second, pipeline_ids):
            arrow_reasons.append("D-PIPELINE")
        if not (first in roles and second in roles):
            arrow_reasons.append("D-NONROLE")
        constructs.append(("T-ROLE-ARROW", arrow_reasons))

    match = _HANDOFF_RE.search(line)
    if match:
        target = match.group(1).lower()
        handoff_reasons = list(reasons)
        is_pipeline_target = _pipeline_target(target, pipeline_ids)
        if is_pipeline_target:
            handoff_reasons.append("D-PIPELINE")
        if target in _ESCALATION_TARGETS and _ESCALATION_RE.search(line):
            handoff_reasons.append("D-ESCALATION")
        if target in roles or is_pipeline_target:
            constructs.append(("T-HANDOFF", handoff_reasons))

    if workflow_file:
        next_match = _NEXT_RE.search(line)
        if next_match and any(
            re.search(rf"(?i)(?<![\w-]){re.escape(role)}(?![\w-])", next_match.group(1))
            for role in roles
        ):
            constructs.append(("T-NEXT", list(reasons)))

    return constructs


def find_findings(repo_root: Path = REPO_ROOT) -> list[Finding]:
    roles = load_roles(repo_root)
    pipeline_ids = load_pipeline_ids(repo_root)
    findings: list[Finding] = []
    for path in iter_scope_files(repo_root):
        rel = path.relative_to(repo_root).as_posix()
        text = path.read_text(encoding="utf-8")
        boundary = boundary_lines(text)
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


def test_no_uncovered_role_routes_in_templates():
    findings = find_findings()
    assert findings == [], "Uncovered routing constructs:\n" + "\n".join(
        str(f) for f in findings
    )


def test_delegation_reference_lines_have_no_dispatch_semantics():
    # The former ``"reference only" in line`` assertion was tautological: the
    # marker constant already contains that phrase. Reference-only headings may
    # be bare (the delegated items follow as bullets), so the meaningful
    # invariant is the absence of executable dispatch semantics.
    for rel, number, line in _reference_lines():
        for token in _FORBIDDEN_REFERENCE_TOKENS:
            assert token not in line, f"{rel}:{number}: dispatch token {token!r} in reference line"


def test_next_role_labels_absent_in_spec_plan_workflow_scope():
    findings = [f for f in find_findings() if f.kind == "T-NEXT"]
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
