#!/bin/bash
# Scenario assert for 46-progress-tierb-append-rotation
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (46-progress-tierb-append-rotation): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (46-progress-tierb-append-rotation): $*"
    exit 1
}

python3 - "$REPO_ROOT" <<'PYEOF' || fail "python check failed"
import sys
from pathlib import Path

repo_root = Path(sys.argv[1])
sys.path.insert(0, str(repo_root / "scripts"))
from lib.checkpoint import Checkpoint, CheckpointStore

store = CheckpointStore(project_root=Path("."), agent_meta_root=repo_root)
store.save_checkpoint(
    "sessA", Checkpoint(task_id="t1", agent="developer", task_description="first-entry", status="completed")
)
store.save_checkpoint(
    "sessA", Checkpoint(task_id="t2", agent="tester", task_description="second-entry", status="in_progress")
)
content = Path(".meta-viz/progress/current.md").read_text(encoding="utf-8")
assert "first-entry" in content, "tier-B must append the first checkpoint"
assert "second-entry" in content, "tier-B must append the second checkpoint"
assert content.count("| Agent | Task | Status | Pipeline/Stage |") == 2, (
    "tier-B must render one table per appended entry, not overwrite"
)

store.save_checkpoint(
    "sessB", Checkpoint(task_id="t1", agent="developer", task_description="rotated-entry", status="completed")
)
content = Path(".meta-viz/progress/current.md").read_text(encoding="utf-8")
assert "first-entry" not in content, "a new session's first checkpoint must rotate (clear) the tier-B file"
assert "rotated-entry" in content
PYEOF

echo "ASSERT OK (46-progress-tierb-append-rotation): tier-B append + rotation verified"
