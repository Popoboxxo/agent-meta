"""Spec/Plan-Workflow consistency parser and checks (design §7.3, D9).

Two layers live here:

1. ``parse_plan_ledger`` — reads the human-readable ledger of a plan document
   (checkbox list + ``Status:`` header) and exposes it as structured data. The
   plan/ledger view is the human-readable recovery source; the machine-readable
   recovery source is the :class:`~lib.checkpoint.CheckpointStore` round-trip
   (D2).
2. ``check_spec_plan_workflow`` — the standalone validator behind
   ``sync.py --validate-spec-plan`` (F12). It scans the consumer project's
   spec/plan/spike artifacts and reports findings for required sections,
   placeholders, traceability, approval markers, ledger format and the plan
   dependency graph (F6 — graph validator only, ``execute_plan`` is out of
   scope). When the master switch resolves to ``false`` it is a no-op and
   returns ``[]`` (§10.1).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from .report import Finding, Severity

if TYPE_CHECKING:
    from ..orchestration import FanoutTask

REQUIRED_SPEC_SECTIONS = (
    "## Problem", "## Ziel", "## Nicht-Ziele", "## Interface Contracts",
    "## Datenfluss", "## Acceptance Criteria", "## Offene Fragen",
    "## Trace-Anker",
)
REQUIRED_PLAN_SECTIONS = (
    "**Goal:**", "**Architecture:**", "**Tech Stack:**", "**Spec:**",
    "## Global Constraints", "## File Structure", "pipeline_stages",
)

_WORKFLOW_BLOCK = "spec-plan-workflow"
_DEFAULT_INCLUDE = ("*.md",)
_DEFAULT_SPECS_DIR = "docs/specs"
_DEFAULT_PLANS_DIR = "docs/plans"
_DEFAULT_SPIKES_DIR = "docs/spikes"

# Template name patterns (design §5.1 M6-cr): a file is a workflow artifact only
# when it matches exactly one of these; anything else is legacy (WARNING).
_SPIKE_RE = re.compile(r".*-spike\.md$")
_DESIGN_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-.+-design\.md$")
_DATED_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-.+\.md$")

_TASK_HEADER_RE = re.compile(
    r"(?m)^###[ \t]+Task[ \t]+([^\s:—–-]+)[ \t]*(?:[:—–-][ \t]*(.*?))?[ \t]*$"
)
_AGENT_FIELD_RE = re.compile(
    r"(?im)^[ \t]*(?:\*\*)?Agent:(?:\*\*)?[ \t]*([\w.-]+)"
)
_DEPENDS_RE = re.compile(
    r"(?im)^[ \t]*(?:\*\*)?Depends on:(?:\*\*)?[ \t]*(.+?)[ \t]*$"
)
_FILES_FIELD_RE = re.compile(r"\b(?:Modify|Create):[ \t]*`?([^\s,;`)]+)`?")
_SPEC_FIELD_RE = re.compile(
    r"(?im)^[ \t]*(?:\*\*)?Spec:(?:\*\*)?[ \t]*(.+?)[ \t]*$"
)
_SPEC_ID_RE = re.compile(r"spec-id:[ \t]*([A-Za-z0-9._-]+)")
# Approval marker: `> Status: APPROVED` and bold `**Status:** APPROVED` both
# count (real design docs use the bold form; carry-forward from Task 9 review).
_APPROVED_RE = re.compile(
    r"(?im)^[ \t]*>?[ \t]*\**Status:\**[ \t]*APPROVED\b"
)
_PLACEHOLDER_PATTERNS = (
    ("TODO", re.compile(r"\bTODO\b")),
    ("TBD", re.compile(r"\bTBD\b")),
    ("<platzhalter>", re.compile(re.escape("<platzhalter>"))),
    ("...", re.compile(r"(?m)^[ \t]*\.\.\.[ \t]*$")),
    (
        "empty Interfaces",
        re.compile(r"(?m)^[ \t]*(?:\*\*)?Interfaces:(?:\*\*)?[ \t]*$"),
    ),
)


def parse_plan_ledger(plan_path: Path) -> dict:
    text = plan_path.read_text(encoding="utf-8") if plan_path.exists() else ""
    checkboxes = re.findall(r"^- \[( |x|X)\]", text, flags=re.MULTILINE)
    checked = sum(1 for box in checkboxes if box.lower() == "x")
    match = re.search(r"^\s*>?\s*Status:\s*(.+?)\s*$", text, flags=re.MULTILINE)
    status = match.group(1).strip() if match else None
    return {
        "checkboxes": len(checkboxes),
        "checked": checked,
        "complete": bool(checkboxes) and checked == len(checkboxes),
        "status": status,
    }


def check_spec_plan_workflow(
    project_root: Path,
    config: dict | None = None,
    *,
    agent_meta_root: Path | None = None,
    changed_files: set[str] | None = None,
) -> list[Finding]:
    """Validate the consumer project's spec/plan workflow artifacts.

    Checks: required sections (incl. ``pipeline_stages``), no-placeholder,
    spec↔plan↔task↔test traceability, approval markers, ledger checkbox
    format, and the plan dependency graph (``FanoutPlan``/``validate_plan``).

    Effective activation via ``resolve_spec_plan_enabled(config,
    agent_meta_root)``; when it resolves to ``false`` this is a no-op that
    returns ``[]`` (§10.1).
    """
    project_root = Path(project_root)
    if config is None:
        config = _load_config(project_root)
    if not isinstance(config, dict):
        config = {}

    root = _resolve_agent_meta_root(project_root, agent_meta_root)
    dod = _resolve_dod(config, root)
    if not _spec_plan_enabled(config, root, dod):
        return []

    block = config.get(_WORKFLOW_BLOCK)
    if not isinstance(block, dict):
        block = {}

    required = bool(dod.get("spec-plan-required", False))
    task_test_traceability = bool(dod.get("spec-plan-traceability", False))

    findings: list[Finding] = []
    artifacts = _collect_artifacts(project_root, block, changed_files, findings)
    texts = {path: _read(path) for path, _role in artifacts}

    specs = [path for path, role in artifacts if role == "spec"]
    plans = [path for path, role in artifacts if role == "plan"]

    _check_required_sections(project_root, artifacts, texts, required, findings)
    _check_placeholders(project_root, artifacts, texts, findings)
    _check_traceability(
        project_root, specs, plans, texts, task_test_traceability, findings,
    )
    _check_approval_markers(project_root, plans, texts, findings)
    _check_ledger_format(project_root, plans, findings)
    _check_plan_graph(project_root, plans, texts, findings)
    return findings


def _load_config(project_root: Path) -> dict:
    """Load ``<project_root>/.meta-config/project.yaml`` (lazy import).

    ``load_config`` expects a ``Path`` (not ``str``). A missing config file is
    treated as an empty config so the standalone validator does not abort.
    """
    config_path = project_root / ".meta-config" / "project.yaml"
    if not config_path.exists():
        return {}
    from ..config import load_config

    return load_config(config_path)


def _resolve_agent_meta_root(
    project_root: Path, agent_meta_root: Path | None,
) -> Path:
    if agent_meta_root is not None:
        return Path(agent_meta_root)
    from ..providers import resolve_agent_meta_root

    return resolve_agent_meta_root(project_root)


def _resolve_dod(config: dict, agent_meta_root: Path) -> dict:
    from ..dod import resolve_dod

    return resolve_dod(config, agent_meta_root)


def _spec_plan_enabled(config: dict, agent_meta_root: Path, dod: dict) -> bool:
    from ..dod import resolve_spec_plan_enabled

    return resolve_spec_plan_enabled(config, agent_meta_root, dod=dod)


def _collect_artifacts(
    project_root: Path,
    block: dict,
    changed_files: set[str] | None,
    findings: list[Finding],
) -> list[tuple[Path, str]]:
    """Scan configured dirs and return ``(path, role)`` template artifacts.

    Non-template files (Bestand without the workflow naming pattern) yield a
    WARNING with check ``spec_plan_legacy`` — never an ERROR, and never a move.
    """
    paths_block = block.get("paths")
    paths = paths_block if isinstance(paths_block, dict) else {}
    scan_block = block.get("scan")
    scan = scan_block if isinstance(scan_block, dict) else {}

    include = scan.get("include") or list(_DEFAULT_INCLUDE)
    changed_only = bool(scan.get("changed-files-only", True))

    canonical_dirs = (
        paths.get("specs") or _DEFAULT_SPECS_DIR,
        paths.get("plans") or _DEFAULT_PLANS_DIR,
        paths.get("spikes") or _DEFAULT_SPIKES_DIR,
    )
    legacy_dirs = paths.get("legacy") or []

    def _changed_ok(path: Path) -> bool:
        if changed_files is None or not changed_only:
            return True
        rel = _rel(project_root, path)
        return rel in changed_files or path.as_posix() in changed_files

    artifacts: list[tuple[Path, str]] = []
    seen: set[Path] = set()
    for directory, is_legacy in [
        *((d, False) for d in canonical_dirs),
        *((d, True) for d in legacy_dirs),
    ]:
        for path in _glob(project_root / directory, include):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            if not _changed_ok(path):
                continue
            if not _matches_template(path.name):
                findings.append(
                    Finding(
                        Severity.WARNING,
                        "spec_plan_legacy",
                        _rel(project_root, path),
                        "file does not match a spec/plan/spike template pattern "
                        "— read as legacy, not migrated",
                        suggestion="rename to the workflow template pattern if this "
                                   "file participates in the spec/plan workflow",
                    )
                )
                continue
            artifacts.append((path, _classify(path.name)))
    artifacts.sort(key=lambda entry: _rel(project_root, entry[0]))
    return artifacts


def _glob(directory: Path, include: list[str]) -> list[Path]:
    if not directory.is_dir():
        return []
    matches: list[Path] = []
    for pattern in include:
        matches.extend(directory.glob(pattern))
    return sorted(matches)


def _matches_template(name: str) -> bool:
    return bool(
        _SPIKE_RE.match(name) or _DESIGN_RE.match(name) or _DATED_RE.match(name)
    )


def _classify(name: str) -> str:
    if _SPIKE_RE.match(name):
        return "spike"
    if _DESIGN_RE.match(name):
        return "spec"
    return "plan"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _rel(project_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _check_required_sections(
    project_root: Path,
    artifacts: list[tuple[Path, str]],
    texts: dict[Path, str],
    required: bool,
    findings: list[Finding],
) -> None:
    severity = Severity.ERROR if required else Severity.WARNING
    for path, role in artifacts:
        if role == "spike":
            continue
        sections = REQUIRED_SPEC_SECTIONS if role == "spec" else REQUIRED_PLAN_SECTIONS
        text = texts.get(path, "")
        for section in sections:
            if section not in text:
                findings.append(
                    Finding(
                        severity,
                        "spec_plan_required_sections",
                        _rel(project_root, path),
                        f"missing required section '{section}'",
                        suggestion=f"add the '{section}' section to the template",
                    )
                )


def _check_placeholders(
    project_root: Path,
    artifacts: list[tuple[Path, str]],
    texts: dict[Path, str],
    findings: list[Finding],
) -> None:
    for path, _role in artifacts:
        text = texts.get(path, "")
        for label, pattern in _PLACEHOLDER_PATTERNS:
            if pattern.search(text):
                findings.append(
                    Finding(
                        Severity.ERROR,
                        "spec_plan_no_placeholder",
                        _rel(project_root, path),
                        f"placeholder '{label}' found",
                        suggestion="replace the placeholder with concrete content",
                    )
                )


def _check_traceability(
    project_root: Path,
    specs: list[Path],
    plans: list[Path],
    texts: dict[Path, str],
    task_test_traceability: bool,
    findings: list[Finding],
) -> None:
    # §7.3: traceability findings are ERROR only when the DoD flag
    # ``spec-plan-traceability`` is enabled, otherwise WARNING.
    severity = Severity.ERROR if task_test_traceability else Severity.WARNING
    referenced_plan_text = "\n".join(texts.get(plan, "") for plan in plans)

    for plan in plans:
        match = _SPEC_FIELD_RE.search(texts.get(plan, ""))
        if not match:
            findings.append(
                Finding(
                    severity,
                    "spec_plan_traceability",
                    _rel(project_root, plan),
                    "plan has no '**Spec:**' reference",
                    suggestion="reference the approved spec via '**Spec:** <path>'",
                )
            )
            continue
        ref = match.group(1).strip().strip("`").strip()
        if not ref or not (project_root / ref).exists():
            findings.append(
                Finding(
                    severity,
                    "spec_plan_traceability",
                    _rel(project_root, plan),
                    f"referenced spec '{ref}' does not exist",
                    suggestion="fix the '**Spec:**' path or create the spec",
                )
            )

    for spec in specs:
        match = _SPEC_ID_RE.search(texts.get(spec, ""))
        if not match:
            continue
        spec_id = match.group(1)
        if spec_id not in referenced_plan_text:
            findings.append(
                Finding(
                    severity,
                    "spec_plan_traceability",
                    _rel(project_root, spec),
                    f"spec-id '{spec_id}' is not referenced by any plan",
                    suggestion="reference the spec-id in the plan's Trace-Anker",
                )
            )

    if not task_test_traceability:
        return

    for plan in plans:
        text = texts.get(plan, "")
        tasks = _parse_plan_tasks(text)
        if not tasks:
            continue
        haystack = _test_mapping_haystack(project_root, text, tasks)
        for task in tasks:
            tokens = _id_tokens(task.task_id)
            if not any(token.lower() in haystack.lower() for token in tokens):
                findings.append(
                    Finding(
                        Severity.ERROR,
                        "spec_plan_traceability",
                        _rel(project_root, plan),
                        f"task '{task.task_id}' has no matching test name",
                        suggestion="name the task's test after the task id "
                                   "(spec-plan-traceability is enabled)",
                    )
                )


def _test_mapping_haystack(
    project_root: Path, text: str, tasks: list[FanoutTask],
) -> str:
    names: list[str] = []
    for task in tasks:
        for rel_file in task.files_touched:
            candidate = project_root / rel_file
            if "test" not in candidate.name.lower() or not candidate.exists():
                continue
            names.extend(re.findall(r"(?m)^\s*def\s+(test_\w+)", _read(candidate)))
    names.extend(line for line in text.splitlines() if "test" in line.lower())
    return "\n".join(names)


def _check_approval_markers(
    project_root: Path,
    plans: list[Path],
    texts: dict[Path, str],
    findings: list[Finding],
) -> None:
    for plan in plans:
        text = texts.get(plan, "")
        match = _SPEC_FIELD_RE.search(text)
        if not match:
            continue
        has_tasks = bool(_parse_plan_tasks(text)) or parse_plan_ledger(plan)["checkboxes"] > 0
        if not has_tasks:
            continue
        ref = match.group(1).strip().strip("`").strip()
        spec_path = project_root / ref
        if not ref or not spec_path.exists():
            continue
        if not _APPROVED_RE.search(_read(spec_path)):
            findings.append(
                Finding(
                    Severity.ERROR,
                    "spec_plan_approval_marker",
                    _rel(project_root, plan),
                    f"spec '{ref}' is not APPROVED although the plan has tasks",
                    suggestion="approve the spec ('Status: APPROVED') before "
                               "scheduling plan tasks",
                )
            )


def _check_ledger_format(
    project_root: Path, plans: list[Path], findings: list[Finding],
) -> None:
    for plan in plans:
        ledger = parse_plan_ledger(plan)
        if ledger["checkboxes"] > 0 and ledger["status"] is None:
            findings.append(
                Finding(
                    Severity.WARNING,
                    "spec_plan_ledger_format",
                    _rel(project_root, plan),
                    "plan has checkboxes but no 'Status:' line",
                    suggestion="add a '> Status:' header line to the plan",
                )
            )


def _check_plan_graph(
    project_root: Path,
    plans: list[Path],
    texts: dict[Path, str],
    findings: list[Finding],
) -> None:
    from ..orchestration import (
        FanoutPlan,
        check_plan_file_overlap,
        validate_plan,
    )

    for plan in plans:
        tasks = _parse_plan_tasks(texts.get(plan, ""))
        if not tasks:
            continue
        fanout = FanoutPlan(
            kind="sequential",
            tasks=tuple(tasks),
            max_parallel=len(tasks),
        )
        overlap = check_plan_file_overlap(fanout, project_root)
        for error in validate_plan(fanout, file_overlap=overlap):
            findings.append(
                Finding(
                    Severity.ERROR,
                    "spec_plan_plan_graph",
                    _rel(project_root, plan),
                    error,
                    suggestion="resolve the dependency cycle/deadlock or file "
                               "overlap before dispatching the plan",
                )
            )


def _parse_plan_tasks(text: str) -> list[FanoutTask]:
    """Build one :class:`~lib.orchestration.FanoutTask` per ``### Task`` block.

    Only the graph-relevant fields are populated: ``task_id`` (normalized to
    ``task-<number>``), ``target_agent`` (``Agent:`` field, default
    ``developer``), ``prompt`` (task title), ``files_touched``
    (``Modify:``/``Create:`` paths) and ``dependencies`` (``Depends on:`` ids).
    """
    from ..orchestration import FanoutTask

    headers = list(_TASK_HEADER_RE.finditer(text))
    tasks: list[FanoutTask] = []
    for index, header in enumerate(headers):
        start = header.end()
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        block = text[start:end]
        task_id = _normalize_task_id(header.group(1).strip())
        title = (header.group(2) or "").strip()
        agent_match = _AGENT_FIELD_RE.search(block)
        target_agent = agent_match.group(1) if agent_match else "developer"
        files_touched = tuple(_FILES_FIELD_RE.findall(block))
        dependencies: list[str] = []
        for dep_match in _DEPENDS_RE.finditer(block):
            for token in re.findall(r"task-\d+|\d+", dep_match.group(1)):
                dep = _normalize_task_id(token)
                if dep not in dependencies:
                    dependencies.append(dep)
        tasks.append(
            FanoutTask(
                task_id=task_id,
                target_agent=target_agent,
                prompt=title or task_id,
                files_touched=files_touched,
                dependencies=tuple(dependencies),
            )
        )
    return tasks


def _normalize_task_id(raw: str) -> str:
    if re.fullmatch(r"\d+", raw):
        return f"task-{raw}"
    if re.fullmatch(r"task-\d+", raw, flags=re.IGNORECASE):
        return raw.lower()
    return raw


def _id_tokens(task_id: str) -> tuple[str, ...]:
    normalized = task_id.lower()
    tokens = {normalized, normalized.replace("-", "_")}
    if normalized.startswith("task-"):
        tokens.add("task" + normalized[len("task-"):])
    return tuple(sorted(tokens))
