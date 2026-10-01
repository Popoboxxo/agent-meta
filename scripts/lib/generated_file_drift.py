"""Generated-file drift detection: warn when a sync.py-owned file
(anything tracked via .agent-meta-managed) was manually edited since the
last sync, and write a timestamped `.sync-backup-<...>` sibling of every
drifted file before the writers overwrite it (issue #734). The edit is
still overwritten in place -- the backup is a safety net, not preservation.

Split into three parts, mirroring context.py's context-hashes.json pattern:
- scan_generated_file_drift(): pure, compares current file content hashes
  against the stored baseline, called BEFORE the per-provider write stage
  so it sees pre-overwrite state.
- backup_drifted_files(): writes one timestamped backup per finding from
  the pre-overwrite content, called right after the scan and before the
  warnings and the writers.
- capture_generated_file_hashes(): writes a fresh baseline from the
  now-written files, called AFTER every writer has run.

Spec: docs/superpowers/specs/2026-09-07-generated-file-drift-detection-design.md
(see its "Post-implementation update (2026-09-11, #734)" note).

W3-5 adds the docs-consolidation half (IC-16, AC-19, AC-37, NFA-05): the two
fully generated index files and the marker regions of the hybrid doc files join
the same baseline. Three properties make that safe, and all three are
load-bearing rather than cosmetic. They are documented in full on the constants
and helpers below (:data:`DOCS_GENERATED_RELS`, :func:`base_path_for_key`,
:func:`_iter_docs_drift_entries`, ``backup_drifted_files``):

* the doc paths are **provider-independent**, so they are handled beside
  :data:`PLATFORM_DEFAULTS_RESOLVED_REL` and NOT inside
  ``_iter_managed_files()``, which is provider-scoped;
* a hybrid doc file is **prose plus generated regions**, so only the extracted
  marker body is hashed -- under the store key ``<rel>#docs:<region>``;
* that key is a **store key, not a path**, so it is neither backed up nor
  silently rewritten, and the allowlist matches it by **base path**.
"""

from __future__ import annotations

import fnmatch
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from .deactivation import get_active_providers

# Module-level on purpose: doc_renderer's rendering layer is a neutral leaf,
# importable from anywhere (doc_renderer.py:3-9); the acyclicity guard is
# tests/test_import_acyclicity.py. A function-local import masks a real cycle,
# it does not prevent one.
from .doc_renderer import DOCS_BLOCK_RE
from .io import content_hash, load_json_file, load_yaml_file, safe_path, write_atomic
from .log import SyncLog
from .pipelines import resolve_pipeline_details_dir
from .rule_index import read_managed_index

GENERATED_FILE_HASHES_DIR = ".meta-config"
GENERATED_FILE_HASHES_FILE = "generated-file-hashes.json"
DRIFT_ALLOWLIST_FILE = "drift-allowlist.yaml"
# Task 6 (platform-project-defaults feature): the resolved platform-preset
# snapshot is a generated file too but lives outside every provider's
# managed-index tree (_iter_managed_files only walks agents_dir/rules_dir/
# hooks_dir/commands_dir/skills_dir/pipeline_details_dir) -- registered
# explicitly here rather than teaching _iter_managed_files a project-root-
# level, non-per-provider file shape for a single caller.
PLATFORM_DEFAULTS_RESOLVED_REL = ".meta-config/platform-defaults.resolved.yaml"

# ---------------------------------------------------------------------------
# W3-5 -- docs-consolidation in the hash baseline (IC-16, AC-19, AC-37, NFA-05)
# ---------------------------------------------------------------------------

#: Pseudo-provider carried by every docs finding. Docs files are not owned by
#: a provider, so the finding needs an attribution that says exactly that --
#: same idea as the existing ``"platform-defaults"`` literal.
DOCS_PSEUDO_PROVIDER = "docs-consolidation"

#: Fully generated docs files: hashed **whole**, because every byte of them is
#: generator-owned. ``docs/INDEX.md`` is written in W3-6 and
#: ``docs/architecture/INDEX.md`` in W4-3; both are listed here from the start so
#: the baseline covers them the moment they exist, and a *missing* file simply
#: contributes no key (absence is not drift).
DOCS_GENERATED_RELS: tuple[str, ...] = ("docs/INDEX.md", "docs/architecture/INDEX.md")

#: Hybrid docs files: hand prose **plus** generated marker regions. Only the
#: extracted marker body is hashed, never the whole file (see the module
#: docstring), so prose edits stay silent.
DOCS_FACT_BLOCK_HOSTS: tuple[str, ...] = ("README.md", "llms.txt", "ARCHITECTURE.md")

#: Separator between the base path and the region name in a marker-body store
#: key: ``<rel>#docs:<region>``. A string that is deliberately **not** a path.
DOCS_MARKER_KEY_SUFFIX = "#docs:"



def _hashes_path(project_root: Path) -> Path:
    return project_root / GENERATED_FILE_HASHES_DIR / GENERATED_FILE_HASHES_FILE


def _load_hashes(project_root: Path) -> dict[str, str]:
    """Read the hash-store sidecar; {} if absent or malformed (fail-soft,
    same contract as context.py's _load_context_hashes)."""
    data = load_json_file(_hashes_path(project_root), on_error="default", default={})
    hashes = data.get("hashes") if isinstance(data, dict) else None
    return hashes if isinstance(hashes, dict) else {}


def _save_hashes(project_root: Path, hashes: dict[str, str], dry_run: bool) -> None:
    """Write the hash-store sidecar (no-op in dry_run)."""
    if dry_run:
        return
    path = _hashes_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": 1, "hashes": hashes}
    write_atomic(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def _allowlist_path(project_root: Path) -> Path:
    return project_root / GENERATED_FILE_HASHES_DIR / DRIFT_ALLOWLIST_FILE


def _load_allowlist_patterns(project_root: Path) -> list[str]:
    """Read .meta-config/drift-allowlist.yaml's `allow-edits` list; []
    if absent or malformed (fail-soft, matching every other optional
    config file in this repo)."""
    data = load_yaml_file(_allowlist_path(project_root), on_error="default", default={})
    patterns = data.get("allow-edits") if isinstance(data, dict) else None
    return [p for p in patterns if isinstance(p, str)] if isinstance(patterns, list) else []


def base_path_for_key(key: str) -> str:
    """The allowlist match target for *key*: the base path, i.e. the key up to
    (excluding) the ``#docs:<region>`` marker suffix.

    ``is_allowlisted()`` matches with ``fnmatch``, which runs against the whole
    string -- so a pattern ``README.md`` does **not** match the store key
    ``README.md#docs:facts``. Left unaddressed, every ``allow-edits`` entry for
    a hybrid doc file would be silently ineffective: the entry is written
    against the *file*, and a user has no way to know they must write
    ``README.md#docs:*`` instead. IC-16 (M8) therefore makes base-path matching
    mandatory, and AC-37 pins it.

    A key without a marker suffix is returned unchanged, so this is a no-op for
    every ordinary file path and for ``PLATFORM_DEFAULTS_RESOLVED_REL``.
    """
    marker_at = key.find(DOCS_MARKER_KEY_SUFFIX)
    return key if marker_at == -1 else key[:marker_at]


def is_allowlisted(rel_path: str, patterns: list[str]) -> bool:
    """True when the **base path** of *rel_path* matches any glob pattern in
    *patterns* (fnmatch semantics).

    For a marker-body store key the base path is the host file without the
    ``#docs:<region>`` suffix -- see :func:`base_path_for_key` for why the
    suffix must not participate in the match (IC-16 M8, AC-37).
    """
    base_path = base_path_for_key(rel_path)
    return any(fnmatch.fnmatch(base_path, pattern) for pattern in patterns)


def _normalize_marker_body(body: str) -> str:
    """The hashed form of a marker region body (IC-16).

    Trailing whitespace per line and blank lines at either end are stripped, so
    a re-indent or a stray trailing space is not reported as drift, while any
    change to the region's actual content still is.
    """
    return "\n".join(line.rstrip() for line in body.splitlines()).strip()


def _docs_marker_bodies(text: str) -> dict[str, str]:
    """Map every ``agent-meta:docs-<region>`` body in *text* to its normalized
    form, first occurrence of a repeated region name winning -- the same
    "count=1" discipline ``apply_fact_blocks()`` applies when it renders.

    An **unbalanced** region contributes no key: a begin marker without its end
    marker leaves no body to hash, and the renderer's all-or-nothing rule means
    the region is left byte-identical by the writer anyway, so a key for it
    would report drift that no write could ever resolve.
    """
    bodies: dict[str, str] = {}
    for match in DOCS_BLOCK_RE.finditer(text):
        region = match.group("region")
        if region in bodies:
            continue
        bodies[region] = _normalize_marker_body(match.group("body"))
    return bodies


def _iter_docs_drift_entries(project_root: Path) -> list[tuple[str, str]]:
    """``(store_key, text_to_hash)`` for every tracked docs artifact.

    The one place that enumerates the docs half of the baseline, so scan and
    capture cannot drift apart: IC-16 requires both directions to be extended
    symmetrically, and a second enumeration would be exactly the kind of
    asymmetry that reports permanent drift.

    Fully generated files contribute their whole content under their own path
    key; hybrid hosts contribute one entry per marker region under
    ``<rel>#docs:<region>``. A file that does not exist (yet) contributes
    nothing -- ``docs/INDEX.md`` only arrives in W3-6.
    """
    entries: list[tuple[str, str]] = []
    for rel in DOCS_GENERATED_RELS:
        path = project_root / rel
        if path.is_file():
            entries.append((rel, path.read_text(encoding="utf-8")))
    for rel in DOCS_FACT_BLOCK_HOSTS:
        path = project_root / rel
        if not path.is_file():
            continue
        bodies = _docs_marker_bodies(path.read_text(encoding="utf-8"))
        entries.extend(
            (f"{rel}{DOCS_MARKER_KEY_SUFFIX}{region}", body)
            for region, body in sorted(bodies.items())
        )
    return entries


def is_drift_detection_enabled(config: dict) -> bool:
    """True unless project.yaml explicitly sets drift-detection.enabled: false."""
    return bool(config.get("drift-detection", {}).get("enabled", True))


def _managed_names(dir_path: Path, *extra_index_names: str) -> set[str]:
    """Union of every managed-index file's entries for dir_path.

    A directory can carry more than one index (rules/ has
    .agent-meta-managed, -mcp, -tools -- one per writer, issue
    extra_index_names lists the sidecar suffixes beyond the base
    .agent-meta-managed.
    """
    names = read_managed_index(dir_path / ".agent-meta-managed")
    for suffix in extra_index_names:
        names |= read_managed_index(dir_path / f".agent-meta-managed-{suffix}")
    return names


# `<file>.sync-backup-<YYYYmmdd-HHMMSS>` siblings written by
# backup_drifted_files(). They are ephemeral safety copies, never generated
# artifacts, so they must never enter the tracked hash baseline -- doing so
# would pin them forever (and scan_generated_file_drift would then flag their
# removal as drift).
_SYNC_BACKUP_PATTERN = "*.sync-backup-*"


def _is_sync_backup_name(name: str) -> bool:
    """True when *name* is a ``.sync-backup-<ts>`` sibling (never managed)."""
    return fnmatch.fnmatch(name, _SYNC_BACKUP_PATTERN)


# The trailing ``.sync-backup-<YYYYmmdd-HHMMSS>`` suffix written by
# backup_drifted_files() above (and its rule-index sibling). Anchored at the
# end of the name so a nested backup-of-a-backup still strips exactly one.
_SYNC_BACKUP_SUFFIX_RE = re.compile(r"\.sync-backup-(\d{8}-\d{6})$")


def _sync_backup_timestamp(name: str) -> Optional[datetime]:
    """Parse the ``YYYYmmdd-HHMMSS`` suffix of a backup *name*; None if absent
    or unparsable (such a name is never a prune candidate -- fail-safe)."""
    match = _SYNC_BACKUP_SUFFIX_RE.search(name)
    if match is None:
        return None
    try:
        return datetime.strptime(match.group(1), "%Y%m%d-%H%M%S")
    except ValueError:
        return None


def _sync_backup_source(name: str) -> str:
    """Source identity of a backup *name* (the name with its backup suffix removed)."""
    return _SYNC_BACKUP_SUFFIX_RE.sub("", name)


def prune_sync_backups(
    target_dir: Path,
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
    max_age_days: int,
    max_per_source: int,
) -> list[str]:
    """Delete ``*.sync-backup-*`` siblings in *target_dir* per retention policy.

    Only direct children of *target_dir* are considered, and only names that
    match ``_is_sync_backup_name`` with a parsable ``YYYYmmdd-HHMMSS`` suffix
    (per the ``backup_drifted_files`` convention). A backup is pruned only when
    **both** thresholds are exceeded: its age is strictly greater than
    *max_age_days* AND strictly more than *max_per_source* newer backups exist
    for the same source. The most recent backup of a source therefore survives
    unconditionally, as do non-backup names and unparsable-timestamp names.

    Recommended default policy (OQ-2): ``max_per_source=3``,
    ``max_age_days=30``; callers pass the values explicitly.

    No-op in ``dry_run`` (returns ``[]``, no filesystem mutation). Fail-soft: a
    per-file ``OSError`` is logged at debug level and iteration continues.
    Returns the pruned project-relative posix paths.
    """
    if dry_run or not target_dir.is_dir():
        return []

    try:
        entries = sorted(target_dir.iterdir())
    except OSError as exc:
        log.debug(
            "sync-backup-prune",
            f"could not list '{target_dir}': {type(exc).__name__}: {exc}",
        )
        return []

    backups: list[tuple[Path, str, datetime]] = []
    for path in entries:
        if not path.is_file() or not _is_sync_backup_name(path.name):
            continue
        stamp = _sync_backup_timestamp(path.name)
        if stamp is None:
            continue
        backups.append((path, _sync_backup_source(path.name), stamp))

    now = datetime.now()
    pruned: list[str] = []
    for path, source, stamp in backups:
        if (now - stamp).days <= max_age_days:
            continue
        newer = sum(
            1 for _other, other_source, other_stamp in backups
            if other_source == source and other_stamp > stamp
        )
        if newer <= max_per_source:
            continue
        try:
            path.unlink()
        except OSError as exc:
            log.debug(
                "sync-backup-prune",
                f"could not delete '{path.name}': {type(exc).__name__}: {exc}",
            )
            continue
        try:
            pruned.append(path.relative_to(project_root).as_posix())
        except ValueError:
            pruned.append(str(path))
    return pruned


def _adapter_file_for_provider(
    config: dict, provider: str, pc: dict
) -> Optional[str]:
    """Project-relative adapter path when ``per-provider`` topology is active.

    An adapter file is a provider's native context file (e.g. Claude's
    ``CLAUDE.md`` at the project root) — outside the per-provider
    managed-index dirs walked below — so it is opted into the drift baseline
    explicitly. Only ``per-provider`` mode opts in, keeping the default
    ``unified`` baseline byte-identical. Purely key-driven (no provider name).
    """
    if not isinstance(config, dict):
        return None
    adapter_file = pc.get("context_adapter_file")
    if not (isinstance(adapter_file, str) and adapter_file.strip()):
        return None
    from .providers import context_topology

    if context_topology(config, provider) != "per-provider":
        return None
    return adapter_file


def _iter_managed_files(
    agent_meta_root: Path, project_root: Path, provider: str, pc: dict,
    config: Optional[dict] = None,
) -> list[Path]:
    """Absolute paths of every file this provider's writers track via a
    .agent-meta-managed index (or its -mcp/-tools sidecars), across
    agents/rules/hooks(+lib+release-gates)/commands/skills/pipeline-details.

    Default literal fallbacks (".claude/hooks" etc.) mirror the same
    established pattern in scan_injection_drift()
    (scripts/lib/external_tools_drift.py) -- correct today because only
    Claude omits these keys from ai-providers.yaml while having the
    capability; any provider without the capability flag never reaches
    the fallback at all.
    """
    files: list[Path] = []

    dir_specs: list[tuple[str, list[str]]] = [
        (pc.get("skills_dir", ".claude/skills"), []),
        (pc.get("agents_dir", ".claude/agents"), []),
    ]
    if pc.get("has_hooks", False):
        dir_specs.append((pc.get("hooks_dir", ".claude/hooks"), []))
    if pc.get("has_rules", False):
        dir_specs.append((pc.get("rules_dir", ".claude/rules"), ["mcp", "tools"]))
    if pc.get("has_commands", False):
        dir_specs.append((pc.get("commands_dir", ".claude/commands"), []))
    if pc.get("has_plugins", False) and pc.get("plugin_dir"):
        # Runtime-gate plugin artifact (SPEC-OPENCODE-RUNTIME-GATE-2026-09-13,
        # IC-14): tracked only when the provider declares the plugin capability.
        dir_specs.append((pc["plugin_dir"], []))
    dir_specs.append((resolve_pipeline_details_dir(pc, provider), []))

    for dir_rel, extra_index_names in dir_specs:
        dir_path = project_root / dir_rel
        if not dir_path.is_dir():
            continue
        for name in sorted(_managed_names(dir_path, *extra_index_names)):
            if _is_sync_backup_name(name):
                continue
            candidate = safe_path(dir_path, name)
            if candidate.is_file():
                files.append(candidate)
            elif candidate.is_dir():
                # Skill-style index entries name a whole subdirectory (e.g.
                # .claude/skills/.agent-meta-managed lists "a2a-delegation-gates",
                # a directory containing SKILL.md and possibly further
                # reference files) rather than a single file -- collect
                # everything inside recursively so drift is caught for all
                # of it, today and as skills grow extra files.
                files.extend(sorted(
                    p for p in candidate.rglob("*")
                    if p.is_file() and not _is_sync_backup_name(p.name)
                ))
        # Nested self-managed subdirectories (hooks/lib/, hooks/release-gates/,
        # issue #558) carry their OWN .agent-meta-managed index -- recurse
        # one level to pick those up too (mirrors scan_injection_drift's
        # "child.is_dir() and (child / '.agent-meta-managed').exists()" check).
        for child in sorted(dir_path.iterdir()):
            if child.is_dir() and (child / ".agent-meta-managed").exists():
                for name in sorted(_managed_names(child)):
                    if _is_sync_backup_name(name):
                        continue
                    nested_candidate = safe_path(child, name)
                    if nested_candidate.is_file():
                        files.append(nested_candidate)

    adapter_file = _adapter_file_for_provider(config, provider, pc)
    if adapter_file:
        adapter_path = project_root / adapter_file
        if adapter_path.is_file():
            files.append(adapter_path)

    return files


def scan_generated_file_drift(
    agent_meta_root: Path, project_root: Path, config: dict, provider_config: dict,
) -> list[dict]:
    """Compare every active provider's managed files against the stored
    hash baseline. Pure -- no writes, no warnings emitted (the caller,
    the sync_pipeline stage, turns findings into log.warning() calls).

    A file with no stored hash yet (first sync, or newly added to a
    managed index) is never a finding -- there is nothing to compare
    against yet.
    """
    stored_hashes = _load_hashes(project_root)
    allowlist = _load_allowlist_patterns(project_root)
    active_providers = set(get_active_providers(config, provider_config))

    findings: list[dict] = []
    for provider, pc in provider_config.items():
        if provider not in active_providers:
            continue
        for abs_path in _iter_managed_files(agent_meta_root, project_root, provider, pc, config):
            rel_path = abs_path.relative_to(project_root).as_posix()
            stored = stored_hashes.get(rel_path)
            if stored is None:
                continue
            current = content_hash(abs_path.read_text(encoding="utf-8"))
            if current == stored:
                continue
            if is_allowlisted(rel_path, allowlist):
                continue
            findings.append({"path": rel_path, "provider": provider})

    resolved_path = project_root / PLATFORM_DEFAULTS_RESOLVED_REL
    stored_resolved = stored_hashes.get(PLATFORM_DEFAULTS_RESOLVED_REL)
    if stored_resolved is not None and resolved_path.is_file():
        current_resolved = content_hash(resolved_path.read_text(encoding="utf-8"))
        if current_resolved != stored_resolved and not is_allowlisted(PLATFORM_DEFAULTS_RESOLVED_REL, allowlist):
            findings.append({"path": PLATFORM_DEFAULTS_RESOLVED_REL, "provider": "platform-defaults"})

    # W3-5 -- the docs half (IC-16). Provider-independent, so it sits beside the
    # PLATFORM_DEFAULTS_RESOLVED_REL block and NOT in _iter_managed_files().
    for store_key, current_text in _iter_docs_drift_entries(project_root):
        stored_docs = stored_hashes.get(store_key)
        if stored_docs is None:
            continue
        if content_hash(current_text) == stored_docs:
            continue
        if is_allowlisted(store_key, allowlist):
            continue
        findings.append({"path": store_key, "provider": DOCS_PSEUDO_PROVIDER})

    return findings


def backup_drifted_files(
    findings: list[dict], project_root: Path, log: SyncLog, dry_run: bool = False,
) -> list[str]:
    """Write a `<file>.sync-backup-<YYYYmmdd-HHMMSS>` sibling for every
    finding, containing exactly the current (pre-overwrite) drifted
    content. One timestamp per invocation, so every backup written by the
    same sync shares the same suffix (mirrors context.py's
    _backup_context_file).

    Fail-soft: a file that cannot be read, or whose backup cannot be
    written, is logged at debug level and skipped -- matching this
    module's optional-config/optional-sidecar style. In dry_run nothing is
    written, but the would-be backup paths are still returned so the
    caller can surface them in its warnings. Returns the project-relative
    posix paths of the backups.

    A marker-body store key (``<rel>#docs:<region>``, W3-5) is never backed
    up: it names a region, not a file, and there is nothing to copy. The
    region is reported by the scan and left untouched **by the store** --
    that is NFA-05's "never rewritten" half as far as this module owns it.
    Whether the docs writer honours a drifted region is a separate, still
    open question (it re-renders its regions unconditionally).
    """
    if not findings:
        return []

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backups: list[str] = []
    for finding in findings:
        rel_path = finding.get("path")
        if not rel_path:
            continue
        # W3-5 / NFA-05 (IC-16): a marker-body store key is not a path. Without
        # this guard the read below would merely fail soft by accident -- the
        # hand-edited region would be reported, but a docs host that happens to
        # carry a legal file of the same composite name would get a backup
        # sibling. A hand-edited region must be *reported*, never materialized.
        if DOCS_MARKER_KEY_SUFFIX in rel_path:
            # Suppressed, not worked around: the call shape stays interchangeable
            # with its three siblings below (same false positive as log.py:80-92).
            log.debug(  # noqa: PLE1205 -- (target, message) is not a logging format call
                "generated-file-drift",
                f"'{rel_path}' is a marker-body key, not a path -- no backup written",
            )
            continue
        target = project_root / rel_path
        try:
            existing_content = target.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            log.debug(
                "generated-file-drift",
                f"could not read '{rel_path}' for backup: {type(exc).__name__}: {exc}",
            )
            continue
        backup = target.with_name(f"{target.name}.sync-backup-{ts}")
        if not dry_run:
            try:
                backup.write_text(existing_content, encoding="utf-8")
            except OSError as exc:
                log.debug(
                    "generated-file-drift",
                    f"could not write backup for '{rel_path}': {type(exc).__name__}: {exc}",
                )
                continue
        try:
            backups.append(backup.relative_to(project_root).as_posix())
        except ValueError:
            backups.append(str(backup))
    return backups


def capture_generated_file_hashes(
    agent_meta_root: Path, project_root: Path, config: dict, provider_config: dict, dry_run: bool,
) -> None:
    """Recompute and persist the complete hash baseline from the CURRENT
    on-disk state of every active provider's managed files. Called once,
    at the very end of the sync pipeline, after every writer has run --
    the on-disk content at this point is exactly what the next sync's
    scan_generated_file_drift() call should compare against.
    """
    active_providers = set(get_active_providers(config, provider_config))
    hashes: dict[str, str] = {}
    for provider, pc in provider_config.items():
        if provider not in active_providers:
            continue
        for abs_path in _iter_managed_files(agent_meta_root, project_root, provider, pc, config):
            rel_path = abs_path.relative_to(project_root).as_posix()
            hashes[rel_path] = content_hash(abs_path.read_text(encoding="utf-8"))
    resolved_path = project_root / PLATFORM_DEFAULTS_RESOLVED_REL
    if resolved_path.is_file():
        hashes[PLATFORM_DEFAULTS_RESOLVED_REL] = content_hash(resolved_path.read_text(encoding="utf-8"))
    # W3-5 -- the docs half (IC-16). Same enumerator as the scan, so the two
    # directions stay symmetric; anything less would report permanent drift.
    for store_key, current_text in _iter_docs_drift_entries(project_root):
        hashes[store_key] = content_hash(current_text)
    _save_hashes(project_root, hashes, dry_run)
