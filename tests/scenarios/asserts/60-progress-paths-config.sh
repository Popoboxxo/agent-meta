#!/usr/bin/env bash
# Scenario assert for 60-progress-paths-config
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
#
# Covers AC-13 of SPEC-PROGRESS-PATHS-CONFIG-2026-09-13: with the progress
# override absent the resolver and store keep the historical .meta-viz layout,
# and with the override present they write under the configured directories.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (60-progress-paths-config): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (60-progress-paths-config): $*"
    exit 1
}

# The DoD presets live in the agent-meta checkout (submodule in real consumer
# projects); emulate the submodule layout so the store can resolve providers.
if [ ! -e ".agent-meta" ]; then
    ln -s "$REPO_ROOT" .agent-meta
fi

[ -f ".meta-config/project.yaml" ] || fail "project config missing in temp dir"

python3 - "$REPO_ROOT" <<'PYEOF' || fail "progress path resolution/store assertions failed"
import sys
from pathlib import Path

repo_root = Path(sys.argv[1])
sys.path.insert(0, str(repo_root / "scripts"))

from lib.checkpoint import Checkpoint, CheckpointStore
from lib.progress_paths import resolve_progress_paths

root = Path(".")

# (a) default resolution (no progress block).
default = resolve_progress_paths(root, {})
assert default.progress_rel == ".meta-viz/progress", default.progress_rel
assert default.checkpoint_rel == ".meta-viz/checkpoints", default.checkpoint_rel
assert default.progress_source == "default", default.progress_source
assert default.checkpoint_source == "default", default.checkpoint_source
assert not default.findings, default.findings

# (b) explicit override resolution.
override_cfg = {"progress": {"dir": ".run/progress", "checkpoint-dir": ".run/checkpoints"}}
override = resolve_progress_paths(root, override_cfg)
assert override.progress_rel == ".run/progress", override.progress_rel
assert override.checkpoint_rel == ".run/checkpoints", override.checkpoint_rel
assert override.progress_source == "project", override.progress_source
assert override.checkpoint_source == "project", override.checkpoint_source
assert not override.findings, override.findings

# The temp project config itself carries the override (best-effort load).
loaded = resolve_progress_paths(root)
assert loaded.progress_rel == ".run/progress", loaded.progress_rel
assert loaded.checkpoint_rel == ".run/checkpoints", loaded.checkpoint_rel
assert loaded.progress_source == "project", loaded.progress_source

# (c) default store writes the historical paths.
default_store = CheckpointStore(project_root=root)
default_store.save_checkpoint(
    "s60-default",
    Checkpoint(task_id="t", agent="developer", task_description="d", status="completed"),
)
assert Path(".meta-viz/progress/current.md").exists(), "default progress file missing"
assert Path(".meta-viz/checkpoints/s60-default.json").exists(), "default checkpoint missing"

# (d) from_config store honours the override and never writes under .meta-viz.
override_store = CheckpointStore.from_config(root, override_cfg)
override_store.save_checkpoint(
    "s60-override",
    Checkpoint(task_id="t", agent="developer", task_description="d", status="completed"),
)
assert Path(".run/progress/current.md").exists(), "override progress file missing"
assert Path(".run/checkpoints/s60-override.json").exists(), "override checkpoint missing"
assert not Path(".meta-viz/checkpoints/s60-override.json").exists(), "override write leaked to .meta-viz"

print("ASSERT OK (60-progress-paths-config): default and override progress/checkpoint paths verified")
PYEOF
