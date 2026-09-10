"""Checkpointing für lange Orchestrierungen.

Speichert Task-Fortschritt nach jedem Delegationsschritt.
Ermöglicht Resume nach Session-Unterbrechung.

Summarization-as-a-Contract (Issue #267): das Session-Layout hat zwei
Ebenen — ``<session-id>.json`` (strukturierte Checkpoints, Summaries) und
``<session-id>/`` (Verzeichnis mit dem VOLLSTÄNDIGEN Roh-Output je
Worker-Task, siehe ``CheckpointStore.save_raw_output``).

**Harness-Grenze (Issue #265):** das Parsen der Worker-Results nach dem
BARRIER-Marker und das Strippen des Roh-Outputs aus dem Orchestrator-
Kontext sind harness-seitig — der Backend ``scripts/lib/orchestration.py``
ist dafür zuständig. Dieses Modul archiviert ausschließlich Bytes: es
parst, filtert und interpretiert niemals Worker-Content.
"""
from __future__ import annotations

import logging
import re
import time
import uuid
from pathlib import Path

from .io import _load_yaml_or_json, write_atomic
from .json_persistence import load_json_document, save_json_document
from .providers import load_providers_config, provider_hooks_supported, resolve_providers

CHECKPOINT_DIR = ".meta-viz/checkpoints"

_RAW_OUTPUT_SUFFIX = ".txt"

_PROGRESS_DIR = ".meta-viz/progress"

_PROGRESS_MAX_BYTES = 200_000  # ~4x the 50 KB JSON-checkpoint budget (checkpointing.md) --
                                # rendered markdown entries run more verbose per checkpoint.
_ENTRY_MARKER = "\n## "

_logger = logging.getLogger(__name__)


def _active_providers(project_root: Path, agent_meta_root: Path) -> list:
    """Resolve active providers for tier detection. Falls back to the same
    "Claude" default resolve_providers() itself uses when no project.yaml
    is found -- matches the pre-existing CheckpointStore test fixtures that
    use a bare tmp_path with no .meta-config/project.yaml (Task 1).
    """
    config, _ = _load_yaml_or_json(project_root / ".meta-config" / "project.yaml")
    provider_config = load_providers_config(agent_meta_root)
    return resolve_providers(config or {}, provider_config)


def _progress_tier(project_root: Path, agent_meta_root: Path) -> str:
    """Tier "A" (overwrite + chat push) only when EVERY active provider has
    a verified hook_protocol (providers.provider_hooks_supported) -- design
    doc 2026-09-10-live-progress-channel-design.md, Architecture §1. A
    mixed Tier-A/Tier-B provider set falls back to Tier B (append) so no
    provider silently loses its only progress signal.
    """
    provider_config = load_providers_config(agent_meta_root)
    active = _active_providers(project_root, agent_meta_root)
    if active and all(provider_hooks_supported(provider_config.get(p, {})) for p in active):
        return "A"
    return "B"


def _sanitize_component(value: str, max_len: int = 64) -> str:
    """Reduce a free-form id (agent name, task id) to a safe filename component.

    Keeps ``[A-Za-z0-9._-]`` and replaces everything else — including path
    separators — with ``_``, so a careless or hostile task id can never
    escape the session directory. Runs of leading/trailing separators are
    stripped; an empty result collapses to ``unnamed``.
    """
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", value)
    cleaned = cleaned.strip("._-")[:max_len].strip("._-")
    return cleaned or "unnamed"


def _render_progress_markdown(session_data: dict) -> str:
    """Render a session's checkpoints as the same status-table format used
    by the orchestrator's mandatory status-table rule (issue #678) --
    human-readable progress snapshot, not the resume-machinery JSON.
    """
    session_id = session_data.get("session_id", "unknown")
    checkpoints = session_data.get("checkpoints", [])
    lines = [f"# Progress — session `{session_id}`", ""]
    latest_summary = next(
        (cp.get("status_summary") for cp in reversed(checkpoints) if cp.get("status_summary")),
        None,
    )
    if latest_summary:
        lines.append(latest_summary)
        lines.append("")
    lines.append("| Agent | Task | Status | Pipeline/Stage |")
    lines.append("|-------|------|--------|----------------|")
    for cp in checkpoints:
        agent = cp.get("agent", "?")
        task = cp.get("task_description", "?")
        status = cp.get("status", "?")
        pipeline = cp.get("pipeline")
        stage = cp.get("stage")
        pipeline_cell = f"{pipeline} / {stage}" if pipeline and stage else (pipeline or "")
        lines.append(f"| `{agent}` | {task} | `{status}` | {pipeline_cell} |")
    lines.append("")
    return "\n".join(lines)


def _render_progress_entry(session_id: str, checkpoint: dict) -> str:
    """Render ONE checkpoint as a Tier-B append block (design doc
    2026-09-10, Architecture §1). Unlike _render_progress_markdown
    (Tier A, whole-session cumulative table), this renders only the
    newest checkpoint so appending it never duplicates entries already
    on disk. Always starts with _ENTRY_MARKER so _trim_oldest_entries
    can split entries unambiguously.
    """
    agent = checkpoint.get("agent", "?")
    task = checkpoint.get("task_description", "?")
    status = checkpoint.get("status", "?")
    pipeline = checkpoint.get("pipeline")
    stage = checkpoint.get("stage")
    pipeline_cell = f"{pipeline} / {stage}" if pipeline and stage else (pipeline or "")
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(checkpoint.get("timestamp") or time.time()))
    return (
        f"{_ENTRY_MARKER}{ts} — session `{session_id}`\n\n"
        f"| Agent | Task | Status | Pipeline/Stage |\n"
        f"|-------|------|--------|----------------|\n"
        f"| `{agent}` | {task} | `{status}` | {pipeline_cell} |\n"
    )


def _trim_oldest_entries(content: str, max_bytes: int) -> str:
    """Drop oldest Tier-B entries (see _render_progress_entry) from the
    front until content fits max_bytes. Always keeps at least the newest
    entry, even if that single entry alone exceeds max_bytes -- never
    truncates mid-entry, which would produce broken markdown.
    """
    if len(content.encode("utf-8")) <= max_bytes:
        return content
    entries = content.split(_ENTRY_MARKER)[1:]  # [0] is the "" prefix before the first marker
    while len(entries) > 1 and len("".join(_ENTRY_MARKER + e for e in entries).encode("utf-8")) > max_bytes:
        entries.pop(0)
    return "".join(_ENTRY_MARKER + e for e in entries)


class Checkpoint:
    """Single checkpoint entry."""

    def __init__(
        self,
        task_id: str,
        agent: str,
        task_description: str,
        status: str,  # "pending", "in_progress", "completed", "failed"
        result: str | None = None,
        next_step: str | None = None,
        status_summary: str | None = None,
        pipeline: str | None = None,
        stage: str | None = None,
        timestamp: float | None = None,
    ):
        self.id = str(uuid.uuid4())
        self.task_id = task_id
        self.agent = agent
        self.task_description = task_description
        self.status = status
        self.result = result
        self.next_step = next_step
        self.status_summary = status_summary
        self.pipeline = pipeline
        self.stage = stage
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "agent": self.agent,
            "task_description": self.task_description,
            "status": self.status,
            "result": self.result,
            "next_step": self.next_step,
            "status_summary": self.status_summary,
            "pipeline": self.pipeline,
            "stage": self.stage,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Checkpoint":
        cp = cls(
            task_id=data["task_id"],
            agent=data["agent"],
            task_description=data["task_description"],
            status=data["status"],
            result=data.get("result"),
            next_step=data.get("next_step"),
            status_summary=data.get("status_summary"),
            pipeline=data.get("pipeline"),
            stage=data.get("stage"),
            timestamp=data.get("timestamp"),
        )
        cp.id = data.get("id", cp.id)
        return cp


class CheckpointStore:
    """Persistiert und lädt Checkpoints."""

    def __init__(self, project_root: Path | str | None = None, agent_meta_root: Path | str | None = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.agent_meta_root = Path(agent_meta_root) if agent_meta_root else self.project_root
        self.checkpoint_dir = self.project_root / CHECKPOINT_DIR

    def _ensure_dir(self) -> None:
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def _session_file(self, session_id: str) -> Path:
        return self.checkpoint_dir / f"{session_id}.json"

    def _session_raw_dir(self, session_id: str) -> Path:
        """Directory holding the archived raw worker outputs of a session."""
        return self.checkpoint_dir / session_id

    def save_raw_output(
        self,
        session_id: str,
        task_id: str,
        agent: str,
        raw_output: str,
    ) -> Path:
        """Archive the COMPLETE raw worker output under ``<session-id>/``.

        Summarization-as-a-Contract (issue #267): the worker's structured
        summary (STATUS/RESULT/ARTIFACTS) travels back as the return value,
        while the full raw output — command logs, diffs, verbose tool output —
        is archived here. The orchestrator context stays lean without losing
        information: details live on disk, retrievable per task.

        The archive is append-only: each call writes a fresh, uniquely
        named file (uuid suffix) so re-running the same task never silently
        overwrites an earlier capture. Returns the written path.

        **Harness-Grenze (Issue #265):** this method archives bytes only.
        Parsing worker results after the BARRIER marker and stripping raw
        output from the orchestrator context is the orchestration backend's
        job (``scripts/lib/orchestration.py``) — NOT implemented here.
        """
        session_dir = self._session_raw_dir(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        stem = (
            f"{_sanitize_component(agent)}"
            f"-{_sanitize_component(task_id)}"
            f"-{uuid.uuid4().hex[:8]}"
        )
        path = session_dir / f"{stem}{_RAW_OUTPUT_SUFFIX}"
        write_atomic(path, raw_output)
        return path

    def load_raw_output(self, session_id: str, filename: str) -> str | None:
        """Load an archived raw output by session id and filename.

        Returns None when the file is missing or unreadable — same
        fail-soft contract as the session JSON loader (#576): a damaged
        archive file must never crash a resume or cleanup pass.
        """
        path = self._session_raw_dir(session_id) / filename
        try:
            return path.read_text(encoding="utf-8")
        except OSError as e:
            _logger.warning(
                "unreadable raw output %s: %s: %s", path, type(e).__name__, e
            )
            return None

    def list_raw_outputs(self, session_id: str) -> list[Path]:
        """List archived raw-output files of a session (sorted, oldest first).

        Empty list when the session has no raw-output directory.
        """
        session_dir = self._session_raw_dir(session_id)
        if not session_dir.is_dir():
            return []
        return sorted(session_dir.glob(f"*{_RAW_OUTPUT_SUFFIX}"))

    def save_checkpoint(self, session_id: str, checkpoint: Checkpoint) -> None:
        """Append checkpoint to session file.

        A corrupt existing session file (#576) is treated as an empty one —
        the new checkpoint still gets saved instead of crashing the whole
        orchestration on a single damaged file.

        Issue #682 §6: also writes .meta-viz/progress/current.md with a
        human-readable snapshot of the same session data (provider-neutral
        path, live-progress-channel design 2026-09-10) -- for a human
        glancing at the repo, not for resume logic.
        """
        self._ensure_dir()
        path = self._session_file(session_id)

        existing = load_json_document(path, default={})
        checkpoints = existing.get("checkpoints", []) if isinstance(existing, dict) else []

        checkpoints.append(checkpoint.to_dict())

        session_data = {
            "session_id": session_id,
            "created_at": checkpoints[0].get("timestamp", time.time()) if checkpoints else time.time(),
            "updated_at": time.time(),
            "checkpoints": checkpoints,
        }
        save_json_document(path, session_data)
        self._write_progress_file(session_data)

    def _write_progress_file(self, session_data: dict) -> None:
        """Write .meta-viz/progress/current.md -- see _render_progress_markdown
        and _render_progress_entry. Tier A: overwrite (unchanged pre-existing
        behavior). Tier B: append the newest checkpoint only, with a rotation
        reset on the first checkpoint of a new session, and a running byte
        cap (design doc 2026-09-10, Architecture §1).

        Provider-neutral path (live-progress-channel design, 2026-09-10) --
        was hardcoded to the Claude-specific .claude/progress/ before.
        """
        progress_path = self.project_root / _PROGRESS_DIR / "current.md"
        progress_path.parent.mkdir(parents=True, exist_ok=True)
        tier = _progress_tier(self.project_root, self.agent_meta_root)
        if tier == "A":
            write_atomic(progress_path, _render_progress_markdown(session_data))
            return
        checkpoints = session_data.get("checkpoints", [])
        latest = checkpoints[-1] if checkpoints else {}
        entry = _render_progress_entry(session_data.get("session_id", "unknown"), latest)
        is_new_session = len(checkpoints) == 1
        existing = "" if is_new_session or not progress_path.exists() else progress_path.read_text(encoding="utf-8")
        combined = existing + entry
        combined = _trim_oldest_entries(combined, _PROGRESS_MAX_BYTES)
        write_atomic(progress_path, combined)

    def load_session(self, session_id: str) -> dict | None:
        """Load full session data. Returns None when missing or corrupt (#576)."""
        return load_json_document(self._session_file(session_id), default=None)

    def get_last_checkpoint(self, session_id: str) -> Checkpoint | None:
        """Get the most recent checkpoint for a session."""
        session = self.load_session(session_id)
        if not session or not session.get("checkpoints"):
            return None
        return Checkpoint.from_dict(session["checkpoints"][-1])

    def get_completed_steps(self, session_id: str) -> list[Checkpoint]:
        """Get all completed checkpoints."""
        session = self.load_session(session_id)
        if not session:
            return []
        return [
            Checkpoint.from_dict(cp)
            for cp in session.get("checkpoints", [])
            if cp.get("status") == "completed"
        ]

    def list_sessions(self) -> list[str]:
        """List all session IDs that have checkpoints."""
        if not self.checkpoint_dir.exists():
            return []
        return [
            p.stem for p in self.checkpoint_dir.glob("*.json")
        ]

    def delete_session(self, session_id: str) -> bool:
        """Delete a session's checkpoint file."""
        path = self._session_file(session_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def cleanup_old_sessions(self, max_age_seconds: float = 86400) -> int:
        """Delete sessions older than max_age_seconds. Returns count of deleted sessions.

        A single corrupt session file (#576) is logged and skipped instead
        of crashing the whole cleanup pass for every other session.
        """
        if not self.checkpoint_dir.exists():
            return 0
        now = time.time()
        deleted = 0
        for path in self.checkpoint_dir.glob("*.json"):
            data = load_json_document(path, default=None)
            if data is None:
                continue
            if now - data.get("updated_at", 0) > max_age_seconds:
                path.unlink()
                deleted += 1
        return deleted


def generate_session_id() -> str:
    """Generate a unique session ID for checkpointing."""
    return f"orch-{int(time.time())}-{uuid.uuid4().hex[:8]}"
