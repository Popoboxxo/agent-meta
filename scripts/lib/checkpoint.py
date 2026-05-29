"""Checkpointing für lange Orchestrierungen.

Speichert Task-Fortschritt nach jedem Delegationsschritt.
Ermöglicht Resume nach Session-Unterbrechung.
"""

import json
import time
import uuid
from pathlib import Path

CHECKPOINT_DIR = ".meta-viz/checkpoints"


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
        timestamp: float | None = None,
    ):
        self.id = str(uuid.uuid4())
        self.task_id = task_id
        self.agent = agent
        self.task_description = task_description
        self.status = status
        self.result = result
        self.next_step = next_step
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
            timestamp=data.get("timestamp"),
        )
        cp.id = data.get("id", cp.id)
        return cp


class CheckpointStore:
    """Persistiert und lädt Checkpoints."""

    def __init__(self, project_root: Path | str | None = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.checkpoint_dir = self.project_root / CHECKPOINT_DIR

    def _ensure_dir(self) -> None:
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def _session_file(self, session_id: str) -> Path:
        return self.checkpoint_dir / f"{session_id}.json"

    def save_checkpoint(self, session_id: str, checkpoint: Checkpoint) -> None:
        """Append checkpoint to session file."""
        self._ensure_dir()
        path = self._session_file(session_id)

        checkpoints = []
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            checkpoints = data.get("checkpoints", [])

        checkpoints.append(checkpoint.to_dict())

        session_data = {
            "session_id": session_id,
            "created_at": checkpoints[0].get("timestamp", time.time()) if checkpoints else time.time(),
            "updated_at": time.time(),
            "checkpoints": checkpoints,
        }
        path.write_text(json.dumps(session_data, indent=2), encoding="utf-8")

    def load_session(self, session_id: str) -> dict | None:
        """Load full session data."""
        path = self._session_file(session_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

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
        """Delete sessions older than max_age_seconds. Returns count of deleted sessions."""
        if not self.checkpoint_dir.exists():
            return 0
        now = time.time()
        deleted = 0
        for path in self.checkpoint_dir.glob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            if now - data.get("updated_at", 0) > max_age_seconds:
                path.unlink()
                deleted += 1
        return deleted


def generate_session_id() -> str:
    """Generate a unique session ID for checkpointing."""
    return f"orch-{int(time.time())}-{uuid.uuid4().hex[:8]}"
