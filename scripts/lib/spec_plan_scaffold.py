"""Sync scaffolding for the native spec/plan/spike paths (R1).

Analogous to ``sync_knowledge_engine`` in ``lib/knowledge.py``: when the
effective ``spec-plan-workflow.enabled`` switch is on, create the neutral
artifact directories (``paths.specs``/``paths.plans``/``paths.spikes``) with a
``.gitkeep`` per directory. When the effective index mode resolves to
``file-index`` (explicit, ``external-system-override.enabled=true`` or a
disabled knowledge engine), the ``index.fallback-index`` skeleton is written
as well (D8). A disabled switch is a no-op.
"""

from __future__ import annotations

from pathlib import Path

from .artifact_scaffold import (
    DEFAULT_PLANS_DIR,
    DEFAULT_SPECS_DIR,
    DEFAULT_SPIKES_DIR,
    scaffold_legacy_spec_plan_dirs,
)
from .io import safe_path, write_checked
from .log import SyncLog
from .dod import resolve_spec_plan_bundle

DEFAULT_FALLBACK_INDEX = "docs/INDEX.md"
_FILE_INDEX_SKELETON = "# INDEX\n\n> File-based index fallback (spec-plan-workflow, D8).\n"


def resolve_index_mode(config: dict) -> tuple[str, str]:
    """Effective index mode and fallback path (D8).

    The `file-index` fallback applies only when the declared `index.mode` is
    `knowledge-engine` and `external-system-override.enabled` is set or the
    knowledge engine is disabled. An explicit `off` is never overridden.
    """
    sp = config.get("spec-plan-workflow") or {}
    index = sp.get("index") or {}
    override = sp.get("external-system-override") or {}
    ke = config.get("knowledge-engine") or {}
    mode = index.get("mode", "knowledge-engine")
    fallback = index.get("fallback-index", DEFAULT_FALLBACK_INDEX)
    if mode == "knowledge-engine" and (
        override.get("enabled", False) or not ke.get("enabled", False)
    ):
        mode = "file-index"
    return mode, fallback


def scaffold_spec_plan_dirs(agent_meta_root: Path, project_root: Path,
                            config: dict, log: SyncLog, dry_run: bool) -> None:
    """Backward-compatible wrapper around the generalized artifact scaffold.

    The three legacy directories are delegated to ``artifact_scaffold``; the
    file-index fallback stays here because it is a spec-plan concern, not an
    artifact-location. Existing imports (``sync_pipeline``, ``knowledge``)
    keep working unchanged.
    """
    if not resolve_spec_plan_bundle(config, agent_meta_root)["scaffold"]:
        log.skip("spec-plan-workflow", "disabled")
        return
    scaffold_legacy_spec_plan_dirs(project_root, config, log, dry_run)
    mode, fallback = resolve_index_mode(config)
    if mode == "file-index":
        index_path = safe_path(project_root, fallback)
        if not dry_run:
            index_path.parent.mkdir(parents=True, exist_ok=True)
        if write_checked(index_path, _FILE_INDEX_SKELETON, log, fallback, dry_run=dry_run):
            log.action("CREATE", fallback, "spec-plan file-index fallback")
