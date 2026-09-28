"""Sync scaffolding for the native spec/plan/spike paths (R1).

Analogous to ``sync_knowledge_engine`` in ``lib/knowledge.py``: when the
effective ``spec-plan-workflow.enabled`` switch is on, create the neutral
artifact directories (``paths.specs``/``paths.plans``/``paths.spikes``) with a
``.gitkeep`` per directory. When the effective index mode resolves to
``file-index`` (explicit, ``external-system-override.enabled=true`` or a
disabled knowledge engine), the ``index.fallback-index`` skeleton is written
as well (D8). A disabled switch is a no-op.

:func:`is_file_index_skeleton` is the reader half of that write: the docs index
generator (``doc_renderer``) asks it whether an existing ``docs/INDEX.md`` is
this module's placeholder, so the two writers can share one path without either
silently taking the other's file (IC-15, B2).
"""

from __future__ import annotations

from pathlib import Path

from .io import safe_path, write_checked
from .log import SyncLog
from .dod import resolve_spec_plan_bundle

DEFAULT_SPECS_DIR = "docs/specs"
DEFAULT_PLANS_DIR = "docs/plans"
DEFAULT_SPIKES_DIR = "docs/spikes"
DEFAULT_FALLBACK_INDEX = "docs/INDEX.md"
_FILE_INDEX_SKELETON = "# INDEX\n\n> File-based index fallback (spec-plan-workflow, D8).\n"
_FILE_INDEX_SKELETON_MARKER = "File-based index fallback"
"""The one line of :data:`_FILE_INDEX_SKELETON` a reader may key on (F20).

The skeleton body is deliberately **not** part of the public contract: a second
copy of it is a second copy of the truth, and it would have to be changed in
lockstep with the string above. The marker is the substring F20 identified as
the *recognisable* part — a consumer only has to know "this line is the scaffold's
stamp on the file", not what the rest of the file says.
"""


def is_file_index_skeleton(text: str) -> bool:
    """True iff *text* is the file-index skeleton this module writes (IC-15).

    The second half of the B2 double-writer fix: this module and
    ``doc_renderer`` both write ``docs/INDEX.md``, so the docs generator needs a
    way to tell "the scaffold's placeholder" from "a file another writer owns".
    Its ownership probe is a substring search for ``doc-indexer/1``, and the
    skeleton does not carry that id — so without this function the generator
    would classify its sibling writer's file as foreign and report it as
    ``skipped`` forever.

    Whitespace folding is **not** applied and the whole body is not matched: F20
    identifies the marker as the line the skeleton *contains*, and IC-13 asks for
    prefix detection. That is the **permissive** direction, not the conservative
    one: a file carrying the marker *plus* hand-maintained sections under the
    scaffold's heading still counts as this module's skeleton, so the docs
    generator is allowed to replace it with the full index (unless a mode gate
    forbids every write). The takeover radius is therefore **unbounded** — it
    reaches as far as the marker appears anywhere in the file, not only in the
    block this module wrote. The replacement is not silent: it lands in
    ``written`` and logs ``doc_renderer.SCAFFOLD_SKELETON_REASON`` — but a
    maintainer who appended content to the scaffold's placeholder should expect
    that content to be replaced once, and the file to come back owned by the
    generator.

    Folding would be the wrong tool here anyway: it turns a wrapped
    ``> File-based index`` / ``> fallback`` blockquote into
    ``> File-based index > fallback`` and would *lose* a real skeleton.

    Args:
        text: the current file content, or any text at all.

    Returns:
        True when the scaffold's marker is present; never raises, never touches
        the filesystem — the caller has already read the file it is asking about.
    """
    return _FILE_INDEX_SKELETON_MARKER in text


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
    if not resolve_spec_plan_bundle(config, agent_meta_root)["scaffold"]:
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
