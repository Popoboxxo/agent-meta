#!/bin/bash
# Scenario assert for 47-progress-pipeline-stage-field
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (47-progress-pipeline-stage-field): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (47-progress-pipeline-stage-field): $*"
    exit 1
}

python3 - "$REPO_ROOT" <<'PYEOF' || fail "python check failed"
import sys
from pathlib import Path

repo_root = Path(sys.argv[1])
sys.path.insert(0, str(repo_root / "scripts"))
from lib.checkpoint import Checkpoint, CheckpointStore

store = CheckpointStore(project_root=Path("."), agent_meta_root=repo_root)
# Two concurrently running pipelines dispatched within ONE orchestrator
# session (single session_id) -- tier-B appends both checkpoints, so a user
# tail -f-ing the file can distinguish them by the Pipeline/Stage cell.
# (Distinct session_ids would each trigger the session-start rotation and
# clobber the other -- the acknowledged v1 limitation, spec Risks section;
# concurrent pipelines share the orchestrator session that dispatches them.)
store.save_checkpoint(
    "sess-orch",
    Checkpoint(
        task_id="t1", agent="se-requirements", task_description="L1 REQs",
        status="in_progress", pipeline="se-cascade", stage="l1-requirements",
    ),
)
store.save_checkpoint(
    "sess-orch",
    Checkpoint(
        task_id="t2", agent="concept-specifier", task_description="Spec draft",
        status="in_progress", pipeline="concept-driven-dev", stage="specify",
    ),
)
content = Path(".meta-viz/progress/current.md").read_text(encoding="utf-8")
assert "se-cascade / l1-requirements" in content, "se-cascade entry must carry its Pipeline/Stage cell"
assert "concept-driven-dev / specify" in content, "concept-driven-dev entry must carry its Pipeline/Stage cell"
PYEOF

echo "ASSERT OK (47-progress-pipeline-stage-field): concurrent pipelines distinguishable"
