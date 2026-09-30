"""Read-only recovery resolver for the progress/ledger system (IC-03, G-02).

Merges the two recovery formats that already exist in the repository -- no
third persistence is invented here:

* the machine-readable :class:`~lib.checkpoint.CheckpointStore` session files
  under ``.meta-viz/checkpoints/`` (the authoritative resume source);
* the hand-written legacy ``.meta-viz/checkpoint-<ts>.json`` files documented
  in the orchestrator checkpointing snippet.

This module never mutates anything and never raises for content problems
(malformed files are skipped with a warning). It is the documented production
caller of ``list_sessions`` / ``get_last_checkpoint`` / ``get_completed_steps``.

Provider-agnostic by construction: no ``if provider == ...`` branch, no
provider literal, no model name, no role name and no dispatch instruction
appears in the rendered context.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .checkpoint import Checkpoint, CheckpointStore
from .consistency.spec_plan import parse_plan_ledger, parse_task_ledgers
from .io import SyncError, _load_yaml_or_json
from .plan_identity import derive_plan_id, make_task_ref

#: Config key that switches the read-only rehydrate mode on/off (IC-09).
REHYDRATE_CONFIG_PATH = "spec-plan-workflow.recovery.rehydrate"

_RECOVERY_BLOCK = "recovery"
_WORKFLOW_BLOCK = "spec-plan-workflow"
_DEFAULT_PLANS_DIR = "docs/plans"
_DEFAULT_MAX_AGE_SECONDS = 86400.0
_LEGACY_DIR = ".meta-viz"
_LEGACY_GLOB = "checkpoint-*.json"
_PENDING_REF_PREFIX = "step:"
_MAX_RENDER_CHARS = 4000

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RecoverySource:
    """One resumable progress source, normalized across both formats."""

    session_id: str
    plan_id: Optional[str]
    source_format: str
    updated_at: float
    completed_task_refs: Tuple[str, ...]
    pending_task_refs: Tuple[str, ...]
    last_status: Optional[str]
    note: Optional[str]


@dataclass(frozen=True)
class ResumeContext:
    """Resolved resume view of a single session, plus its plan ledger view."""

    session_id: str
    plan_id: Optional[str]
    source_format: str
    last_checkpoint: Optional[Checkpoint]
    completed_task_refs: Tuple[str, ...]
    next_task_ref: Optional[str]
    plan_path: Optional[str]
    ledger: Optional[dict]
    drift: Tuple[str, ...]


# ---------------------------------------------------------------------------
# Soft project-config access (M4: plans dir is never hard-coded)
# ---------------------------------------------------------------------------


def _load_project_config(project_root: Path) -> dict:
    """Best-effort read of ``.meta-config/project.yaml`` -- never fatal."""
    try:
        data, _ = _load_yaml_or_json(
            project_root / ".meta-config" / "project.yaml",
            project_root / ".meta-config" / "project.json",
        )
    except (SyncError, OSError) as exc:
        _logger.warning("recovery: unreadable project config: %s", exc)
        return {}
    return data if isinstance(data, dict) else {}


def _workflow_block(config: dict) -> dict:
    block = config.get(_WORKFLOW_BLOCK)
    return block if isinstance(block, dict) else {}


def _recovery_block(config: dict) -> dict:
    block = _workflow_block(config).get(_RECOVERY_BLOCK)
    return block if isinstance(block, dict) else {}


def _configured_plans_dir(config: dict) -> str:
    """Plans directory from ``spec-plan-workflow.paths.plans`` (M4)."""
    paths = _workflow_block(config).get("paths")
    if isinstance(paths, dict):
        plans = paths.get("plans")
        if isinstance(plans, str) and plans.strip():
            return plans
    return _DEFAULT_PLANS_DIR


def _configured_max_age(config: dict) -> Optional[float]:
    """Configured age horizon; a negative value disables the age filter."""
    raw = _recovery_block(config).get("max-age-seconds")
    if raw is None:
        return _DEFAULT_MAX_AGE_SECONDS
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return _DEFAULT_MAX_AGE_SECONDS
    return None if value < 0 else value


def _configured_include_legacy(config: dict) -> bool:
    """``include-legacy`` is opt-out: only an explicit ``false`` disables it."""
    return _recovery_block(config).get("include-legacy") is not False


# ---------------------------------------------------------------------------
# Small content helpers
# ---------------------------------------------------------------------------


def _safe_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _parse_timestamp(value) -> Optional[float]:
    """Parse a numeric or ISO-8601 timestamp; ``None`` when unparseable."""
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def _as_list(value) -> list:
    return value if isinstance(value, list) else []


def _task_id_from_ref(task_ref: str) -> str:
    """Extract the bare task id from a ``<plan_id>#<task_id>`` ref."""
    if "#" in task_ref:
        return task_ref.split("#", 1)[1]
    return task_ref


def _checkpoint_ref(checkpoint: Checkpoint, plan_id: Optional[str]) -> Optional[str]:
    """Ref of a checkpoint, falling back to the bare ``task_id`` (F1-safe)."""
    if checkpoint.task_ref:
        return checkpoint.task_ref
    ref = make_task_ref(checkpoint.plan_id or plan_id, checkpoint.task_id)
    if ref:
        return ref
    return checkpoint.task_id or None


def _rel(project_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


# ---------------------------------------------------------------------------
# Legacy format (hand-written ``.meta-viz/checkpoint-<ts>.json``)
# ---------------------------------------------------------------------------


def _legacy_step_ref(item, fallback_index: int) -> str:
    if isinstance(item, dict):
        for key in ("task_ref", "task_id"):
            value = item.get(key)
            if isinstance(value, str) and value:
                return value
        step = item.get("step")
        if step is not None:
            return "{}{}".format(_PENDING_REF_PREFIX, step)
    return "{}{}".format(_PENDING_REF_PREFIX, fallback_index)


def load_legacy_checkpoints(project_root: Path) -> List[RecoverySource]:
    """Read manually written ``.meta-viz/checkpoint-*.json`` files.

    Unknown keys are ignored; malformed files are skipped with a warning.
    Legacy entries carry ``plan_id=None`` (the format has no plan identity),
    and steps without a task id get the synthetic ref ``step:<n>``. A legacy
    checkpoint only exists while a task is unfinished (the snippet deletes it
    on completion), so ``last_status`` is left ``None``.
    """
    project_root = Path(project_root)
    directory = project_root / _LEGACY_DIR
    if not directory.is_dir():
        return []

    sources: List[RecoverySource] = []
    for path in sorted(directory.glob(_LEGACY_GLOB)):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            _logger.warning("skipping malformed legacy checkpoint %s: %s", path, exc)
            continue
        if not isinstance(raw, dict):
            _logger.warning("skipping legacy checkpoint %s: not a JSON object", path)
            continue

        session_id = raw.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            session_id = path.stem

        created = _parse_timestamp(raw.get("created_at"))
        completed = tuple(
            _legacy_step_ref(item, index + 1)
            for index, item in enumerate(_as_list(raw.get("completed_steps")))
        )
        pending = tuple(
            _legacy_step_ref(item, index + 1)
            for index, item in enumerate(_as_list(raw.get("pending_steps")))
        )
        summary = raw.get("task_summary")

        sources.append(RecoverySource(
            session_id=session_id,
            plan_id=None,
            source_format="legacy",
            updated_at=created if created is not None else _safe_mtime(path),
            completed_task_refs=completed,
            pending_task_refs=pending,
            last_status=None,
            note=summary if isinstance(summary, str) and summary else None,
        ))
    return sources


# ---------------------------------------------------------------------------
# Store format (``.meta-viz/checkpoints/<session>.json``)
# ---------------------------------------------------------------------------


def _store_plan_id(session: dict) -> Optional[str]:
    """Newest checkpoint that carries a ``plan_id`` (IC-03)."""
    for raw in reversed(_as_list(session.get("checkpoints"))):
        if isinstance(raw, dict):
            plan_id = raw.get("plan_id")
            if isinstance(plan_id, str) and plan_id:
                return plan_id
    return None


def load_store_sources(store: CheckpointStore) -> List[RecoverySource]:
    """Build one :class:`RecoverySource` per store session, fail-soft."""
    sources: List[RecoverySource] = []
    for session_id in store.list_sessions():
        try:
            sources.append(_store_source(store, session_id))
        except Exception as exc:  # content problems must never propagate
            _logger.warning("skipping unreadable store session %s: %s", session_id, exc)
    return [source for source in sources if source is not None]


def _store_source(store: CheckpointStore, session_id: str) -> Optional[RecoverySource]:
    session = store.load_session(session_id)
    if not session or not isinstance(session, dict):
        return None

    plan_id = _store_plan_id(session)
    last = store.get_last_checkpoint(session_id)
    completed = store.get_completed_steps(session_id)

    completed_refs: List[str] = []
    seen_completed = set()
    for checkpoint in completed:
        ref = _checkpoint_ref(checkpoint, plan_id)
        if ref and ref not in seen_completed:
            seen_completed.add(ref)
            completed_refs.append(ref)

    pending_refs: List[str] = []
    seen_pending = set()
    for raw in _as_list(session.get("checkpoints")):
        if not isinstance(raw, dict) or raw.get("status") == "completed":
            continue
        try:
            checkpoint = Checkpoint.from_dict(raw)
        except (KeyError, TypeError):
            continue
        ref = _checkpoint_ref(checkpoint, plan_id)
        if ref and ref not in seen_pending:
            seen_pending.add(ref)
            pending_refs.append(ref)

    updated_at = session.get("updated_at")
    if not isinstance(updated_at, (int, float)):
        updated_at = last.timestamp if last is not None else session.get("created_at")
    if not isinstance(updated_at, (int, float)):
        updated_at = 0.0

    note = None
    if last is not None:
        note = last.status_summary or last.task_description or None

    return RecoverySource(
        session_id=session_id,
        plan_id=plan_id,
        source_format="store",
        updated_at=float(updated_at),
        completed_task_refs=tuple(completed_refs),
        pending_task_refs=tuple(pending_refs),
        last_status=last.status if last is not None else None,
        note=note if isinstance(note, str) and note else None,
    )


# ---------------------------------------------------------------------------
# Merge, resolve, find
# ---------------------------------------------------------------------------


def _merge_sources(
    project_root: Path, store: CheckpointStore, include_legacy: bool,
) -> List[RecoverySource]:
    """Merge both formats by ``session_id`` -- the store source wins."""
    merged: Dict[str, RecoverySource] = {}
    if include_legacy:
        for source in load_legacy_checkpoints(project_root):
            merged[source.session_id] = source
    for source in load_store_sources(store):
        merged[source.session_id] = source
    return list(merged.values())


def _store_for(project_root: Path, store: Optional[CheckpointStore]) -> CheckpointStore:
    if store is not None:
        return store
    return CheckpointStore.from_config(project_root)


def resolve_recovery_sources(
    project_root: Path,
    *,
    store: Optional[CheckpointStore] = None,
    max_age_seconds: Optional[float] = None,
    include_legacy: bool = True,
) -> List[RecoverySource]:
    """Merge both formats, dedupe by session id, filter by age, newest first.

    ``max_age_seconds=None`` applies the configured
    ``spec-plan-workflow.recovery.max-age-seconds`` horizon (default ``86400``);
    a configured negative value disables the filter. Never raises for content
    problems.
    """
    project_root = Path(project_root)
    config = _load_project_config(project_root)
    if max_age_seconds is None:
        age_limit = _configured_max_age(config)
    else:
        value = float(max_age_seconds)
        age_limit = None if value < 0 else value

    sources = _merge_sources(project_root, _store_for(project_root, store), include_legacy)
    if age_limit is not None:
        now = time.time()
        sources = [s for s in sources if (now - s.updated_at) <= age_limit]
    sources.sort(key=lambda s: (s.updated_at, s.session_id), reverse=True)
    return sources


def _ledger_is_complete(plan_path: Path) -> bool:
    try:
        return bool(parse_plan_ledger(plan_path).get("complete"))
    except OSError:
        return False


def _is_resumable(
    project_root: Path, config: dict, source: RecoverySource,
) -> bool:
    """Decide whether a source still has work to resume (IC-03)."""
    if source.pending_task_refs:
        return True
    if source.last_status != "completed":
        return True
    plan_path = _resolve_plan_path(project_root, config, source.plan_id)
    if plan_path is None:
        return False
    return not _ledger_is_complete(plan_path)


def find_resumable_session(
    project_root: Path,
    *,
    store: Optional[CheckpointStore] = None,
    max_age_seconds: Optional[float] = None,
) -> Optional[RecoverySource]:
    """Newest source whose last status is not ``completed`` and that still
    has open work; ``None`` when everything linked is done."""
    project_root = Path(project_root)
    config = _load_project_config(project_root)
    sources = resolve_recovery_sources(
        project_root,
        store=_store_for(project_root, store),
        max_age_seconds=max_age_seconds,
        include_legacy=_configured_include_legacy(config),
    )
    for source in sources:
        if _is_resumable(project_root, config, source):
            return source
    return None


# ---------------------------------------------------------------------------
# Resume context
# ---------------------------------------------------------------------------


def _resolve_plan_path(
    project_root: Path, config: dict, plan_id: Optional[str],
) -> Optional[Path]:
    """Locate a plan file in the configured plans dir by derived plan id (M4)."""
    if not plan_id:
        return None
    plans_dir = project_root / _configured_plans_dir(config)
    if not plans_dir.is_dir():
        return None
    for path in sorted(plans_dir.glob("*.md")):
        try:
            if derive_plan_id(path) == plan_id:
                return path
        except OSError:
            continue
    return None


def _plan_view(
    plan_path: Path, effective_plan: Optional[str], completed_refs: Tuple[str, ...],
) -> Tuple[Optional[dict], Optional[str], Tuple[str, ...]]:
    """Return ``(ledger, next_task_ref, drift)`` for a resolved plan file."""
    try:
        ledger = parse_plan_ledger(plan_path)
        task_ledgers = parse_task_ledgers(plan_path)
    except OSError as exc:
        _logger.warning("recovery: unreadable plan %s: %s", plan_path, exc)
        return None, None, ()

    completed_ids = {_task_id_from_ref(ref) for ref in completed_refs}
    next_task_ref = None
    for task_id in task_ledgers:
        ref = make_task_ref(effective_plan, task_id)
        if task_id in completed_ids:
            continue
        if ref and ref not in completed_refs:
            next_task_ref = ref
            break

    drift: List[str] = []
    ledger_complete = {
        task_id for task_id, info in task_ledgers.items() if info.get("complete")
    }
    for task_id in sorted(ledger_complete - completed_ids):
        drift.append(
            "ledger marks task done without a completed checkpoint: " + task_id
        )
    for task_id in sorted(completed_ids - ledger_complete):
        drift.append(
            "completed checkpoint without a closed ledger task: " + task_id
        )
    status = (ledger.get("status") or "").strip().lower()
    if status == "complete" and not ledger.get("complete"):
        drift.append("plan status is 'complete' while the ledger is not complete")
    return ledger, next_task_ref, tuple(drift)


def build_resume_context(
    project_root: Path,
    session_id: str,
    *,
    plan_id: Optional[str] = None,
    store: Optional[CheckpointStore] = None,
) -> Optional[ResumeContext]:
    """Build the resume view for ``session_id``; ``None`` when it does not exist.

    The plan file is located via the plan identity and the configured plans
    directory (M4); ``next_task_ref`` is the first ledger task absent from
    ``completed_task_refs``. Read-only, never raises for content problems.
    """
    project_root = Path(project_root)
    store = _store_for(project_root, store)
    config = _load_project_config(project_root)

    merged = {s.session_id: s for s in _merge_sources(project_root, store, True)}
    source = merged.get(session_id)
    if source is None:
        return None

    effective_plan = plan_id or source.plan_id
    plan_path = _resolve_plan_path(project_root, config, effective_plan)

    ledger = None
    next_task_ref = None
    drift: Tuple[str, ...] = ()
    if plan_path is not None:
        ledger, next_task_ref, drift = _plan_view(
            plan_path, effective_plan, source.completed_task_refs,
        )

    last_checkpoint = None
    if source.source_format == "store":
        try:
            last_checkpoint = store.get_last_checkpoint(session_id)
        except Exception as exc:  # defensive: content problems never propagate
            _logger.warning("recovery: unreadable checkpoint for %s: %s", session_id, exc)

    return ResumeContext(
        session_id=session_id,
        plan_id=effective_plan,
        source_format=source.source_format,
        last_checkpoint=last_checkpoint,
        completed_task_refs=source.completed_task_refs,
        next_task_ref=next_task_ref,
        plan_path=_rel(project_root, plan_path) if plan_path is not None else None,
        ledger=ledger,
        drift=drift,
    )


def _bound(text: str, limit: int = _MAX_RENDER_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "\n"


def render_resume_context(context: ResumeContext) -> str:
    """Render a bounded Markdown resume view.

    Contains the session id, the resolved plan/ledger state and drift lines.
    It names no role and sends no dispatch instruction.
    """
    lines = [
        "## Resume context",
        "",
        "- Session: `{}`".format(context.session_id),
    ]
    if context.plan_id:
        lines.append("- Plan: `{}`".format(context.plan_id))
    if context.plan_path:
        lines.append("- Plan file: `{}`".format(context.plan_path))
    lines.append("- Source: {}".format(context.source_format))

    completed = ", ".join("`{}`".format(ref) for ref in context.completed_task_refs)
    lines.append("- Completed tasks: {}".format(completed or "none"))
    next_ref = "`{}`".format(context.next_task_ref) if context.next_task_ref else "none"
    lines.append("- Next open task: {}".format(next_ref))

    if context.ledger:
        lines.append("- Ledger: {}/{} checked, status={}".format(
            context.ledger.get("checked", 0),
            context.ledger.get("checkboxes", 0),
            context.ledger.get("status") or "unknown",
        ))
    if context.drift:
        lines.append("- Drift:")
        lines.extend("  - {}".format(line) for line in context.drift)

    return _bound("\n".join(lines) + "\n")
