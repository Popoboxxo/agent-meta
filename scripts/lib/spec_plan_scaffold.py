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

from .io import safe_path, write_checked
from .log import SyncLog
from .dod import resolve_spec_plan_enabled

DEFAULT_SPECS_DIR = "docs/specs"
DEFAULT_PLANS_DIR = "docs/plans"
DEFAULT_SPIKES_DIR = "docs/spikes"
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
    if not resolve_spec_plan_enabled(config, agent_meta_root):
        log.skip("spec-plan-workflow", "disabled")
        return
    block = config.get("spec-plan-workflow") or {}
    paths = block.get("paths") or {}
    for key, default in (("specs", DEFAULT_SPECS_DIR), ("plans", DEFAULT_PLANS_DIR),
                         ("spikes", DEFAULT_SPIKES_DIR)):
        rel = paths.get(key, default)
        target = safe_path(project_root, rel)
        if not dry_run:
            target.mkdir(parents=True, exist_ok=True)
        if write_checked(target / ".gitkeep", "", log, f"{rel}/.gitkeep", dry_run=dry_run):
            log.action("CREATE", f"{rel}/.gitkeep", "spec-plan scaffolding")
    mode, fallback = resolve_index_mode(config)
    if mode == "file-index":
        index_path = safe_path(project_root, fallback)
        if not dry_run:
            index_path.parent.mkdir(parents=True, exist_ok=True)
        if write_checked(index_path, _FILE_INDEX_SKELETON, log, fallback, dry_run=dry_run):
            log.action("CREATE", fallback, "spec-plan file-index fallback")
