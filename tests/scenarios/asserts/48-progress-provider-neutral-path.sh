#!/bin/bash
# Scenario assert for 48-progress-provider-neutral-path
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (48-progress-provider-neutral-path): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (48-progress-provider-neutral-path): $*"
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
    "sess1", Checkpoint(task_id="t1", agent="developer", task_description="path-check", status="completed")
)
assert Path(".meta-viz/progress/current.md").exists(), (
    "progress file must land at the provider-neutral .meta-viz/progress/ path"
)
assert not Path(".claude/progress/current.md").exists(), (
    "must never write the old Claude-specific path for a non-Claude provider"
)
PYEOF

grep -rl ".meta-viz/progress/current.md" . >/dev/null 2>&1 \
    || fail "no generated file references the provider-neutral progress path .meta-viz/progress/current.md"

echo "ASSERT OK (48-progress-provider-neutral-path): provider-neutral path verified"
