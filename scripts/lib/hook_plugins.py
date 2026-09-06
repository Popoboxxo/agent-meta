"""Hook plugin-directory sync: release-gates/ and lib/ subdirectories.

Split out of hooks.py (issue #630/#631 wave pushed it past the 600-line
convention limit) — both functions here share the same "always-copy,
.agent-meta-managed-tracked, never-touch-project-owned-files" pattern for a
managed *subdirectory* of a provider's hooks_dir, as opposed to sync_hooks()
itself which manages the top-level hook scripts and their settings.json
registration.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from .hooks import CLAUDE_HOOKS_DIR, collect_hook_sources, parse_hook_metadata
from .io import is_unchanged, safe_path, write_atomic, write_checked
from .log import SyncLog
from .providers import provider_hooks_supported

RELEASE_GATES_SUBDIR = "release-gates"
HOOK_LIB_SUBDIR = "lib"
# Issue #603: SHA-256 checksum manifest next to .agent-meta-managed /
# .allowed-gates. sync.py owns the entries for built-in gates; lines for
# project-owned gates are project-maintained and preserved verbatim.
RELEASE_GATE_CHECKSUMS_NAME = ".sha256-checksums"


def sync_release_gates(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str = "Claude",
    provider_config: dict | None = None,
    release_gates_resolved: dict | None = None,
) -> None:
    """Copy release-gate plugin scripts to <hooks_dir>/release-gates/.

    Plugin architecture (issue #558): hooks/1-generic/pre-release-check.sh is
    a pure dispatcher — at runtime it globs and runs every *.sh file
    alongside it in release-gates/, with no framework-side registry. This
    function only deploys the framework-shipped ("built-in") gate scripts
    from hooks/*/release-gates/ (same 0-external / 1-generic / 2-platform
    layering as collect_hook_sources() uses for regular hooks).

    Projects extend the pipeline by dropping their own *.sh files directly
    into <hooks_dir>/release-gates/ — those are NEVER touched here (not
    added to .agent-meta-managed), exactly like project-owned hooks created
    via create_hook(). The dispatcher picks them up automatically, no
    framework change required.

    Each shipped gate script may reference a single sync-time placeholder,
    ``{{RELEASE_GATE_ENABLED_DEFAULT}}``, baked to "true"/"false" from
    ``release_gates_resolved`` (output of dod.resolve_release_gates()):
    project.yaml `release-gates.<name>.enabled` > dod-preset default > that
    gate script's own `enabled_by_default` header (fallback when the name is
    in neither source).

    Integrity (issue #603): after deploying, this function (re)generates
    ``<target_dir>/.sha256-checksums`` — a sha256sum-compatible manifest of
    the *deployed* (placeholder-substituted) content of every built-in gate.
    The release-gate dispatcher refuses (fail-closed) to execute an
    allowlisted gate whose checksum is missing or stale, so legitimate gate
    changes MUST refresh the manifest — which is exactly what happens here
    on every sync. Lines whose filename was never sync-managed are
    project-owned checksum entries and are preserved verbatim.
    """
    pc = (provider_config or {}).get(provider, {})
    hooks_dir_rel = pc.get("hooks_dir", CLAUDE_HOOKS_DIR)

    platforms = config.get("platforms", [])
    sources = collect_hook_sources(agent_meta_root, platforms, subdir=RELEASE_GATES_SUBDIR)
    # See sync_hooks() (issue #630): has_hooks: true alone doesn't mean the
    # provider's hook_protocol is verified -- deploy nothing new, but still
    # fall through so previously-deployed gates get cleaned up below. Only
    # gated when a real provider_config was supplied -- callers that invoke
    # this directly without one (e.g. low-level unit tests) get the
    # pre-#630 always-deploy behavior, matching the provider="Claude" default.
    if provider_config is not None and not provider_hooks_supported(pc):
        sources = []

    target_dir = project_root / hooks_dir_rel / RELEASE_GATES_SUBDIR
    managed_index_path = target_dir / ".agent-meta-managed"

    previously_managed: set[str] = set()
    if managed_index_path.exists():
        for line in managed_index_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                previously_managed.add(line.strip())

    if not sources and not previously_managed:
        return  # nothing shipped, nothing to clean up — leave any project-owned gates alone

    now_managed: set[str] = set()
    gate_checksums: dict[str, str] = {}
    resolved = release_gates_resolved or {}

    if not dry_run and sources:
        target_dir.mkdir(parents=True, exist_ok=True)

    for source_path, output_name in sources:
        target_path = safe_path(target_dir, output_name)
        source_content = source_path.read_text(encoding="utf-8")
        # Same sync-time-placeholder pattern as {{AGENT_META_PROVIDER}} in
        # sync_hooks() — no-op for scripts that don't reference it.
        source_content = source_content.replace("{{AGENT_META_PROVIDER}}", provider)
        meta = parse_hook_metadata(source_content)
        gate_stem = Path(output_name).stem

        enabled_default = resolved.get(gate_stem)
        if enabled_default is None:
            enabled_default = meta.get("enabled_by_default", "false").lower() == "true"
        source_content = source_content.replace(
            "{{RELEASE_GATE_ENABLED_DEFAULT}}",
            "true" if enabled_default else "false",
        )

        # Provider filter: skip gate script if it declares a specific provider that doesn't match
        gate_provider = meta.get("provider", "")
        if gate_provider and gate_provider != provider:
            log.skip(str(target_path.relative_to(project_root)),
                     f"provider-specific release gate ({gate_provider} only)")
            continue

        now_managed.add(output_name)
        rel_out = str(target_path.relative_to(project_root))
        rel_source = str(source_path.relative_to(agent_meta_root))
        if not dry_run:
            target_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            if write_checked(target_path, source_content, log, rel_source, dry_run=dry_run):
                log.action("COPY", rel_out, rel_source)
            else:
                log.skip(rel_out, "unchanged")
        except Exception as exc:
            log.warning(f"Failed to deploy release gate {rel_out}: {exc}")
            continue
        # Issue #603: checksum of the *deployed* bytes (source_content is
        # exactly what write_atomic persisted / what is already on disk for
        # an unchanged skip). Only successfully deployed gates get an entry —
        # a failed deploy deliberately drops the previous entry so the
        # dispatcher fails closed instead of verifying against a stale hash.
        gate_checksums[output_name] = hashlib.sha256(
            source_content.encode("utf-8")
        ).hexdigest()

    # Remove stale shipped gate scripts — never touches project-owned custom
    # gates (not tracked in .agent-meta-managed in the first place).
    if target_dir.exists():
        for existing in sorted(target_dir.glob("*.sh")):
            if existing.name not in now_managed and existing.name in previously_managed:
                log.action("DELETE", str(existing.relative_to(project_root)),
                           "release gate removed from agent-meta sources")
                if not dry_run:
                    existing.unlink()

    if not dry_run and now_managed:
        managed_index_path.parent.mkdir(parents=True, exist_ok=True)
        managed_index_path.write_text(
            "\n".join(sorted(now_managed)) + "\n", encoding="utf-8"
        )

    # Issue #603: regenerate the checksum manifest so the dispatcher's
    # pre-execution SHA-256 verification stays in step with legitimately
    # (re)deployed built-in gates. Skipped in dry-run like every write; not
    # created when nothing was ever deployed (no manifest, no built-ins —
    # the dispatcher only requires it once allowlisted gates exist).
    checksum_manifest_path = target_dir / RELEASE_GATE_CHECKSUMS_NAME
    if not dry_run and (gate_checksums or checksum_manifest_path.exists()):
        _write_release_gate_checksums(
            target_dir, project_root, gate_checksums, previously_managed, log
        )


def _checksum_entry_name(line: str) -> str | None:
    """Return the filename of a ``<sha256>  <filename>`` manifest line, else None.

    Blank lines, ``#`` comments and anything not shaped like a sha256sum
    entry (64 hex chars, whitespace, bare filename) yield None so callers can
    preserve such lines verbatim (issue #603).
    """
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    parts = stripped.split()
    if len(parts) != 2 or len(parts[0]) != 64:
        return None
    if any(char not in "0123456789abcdef" for char in parts[0]):
        return None
    return parts[1]


def _write_release_gate_checksums(
    target_dir: Path,
    project_root: Path,
    gate_checksums: dict[str, str],
    previously_managed: set[str],
    log: SyncLog,
) -> None:
    """(Re)generate ``release-gates/.sha256-checksums`` for built-in gates (issue #603).

    Sha256sum-compatible format (``<sha256>  <filename>`` per line,
    ``#``-comments allowed) so the manifest can be inspected with standard
    tools. Merge semantics:

    - Entry lines whose filename is in ``previously_managed`` (or freshly
      checksummed) are sync-owned: dropped and regenerated from
      ``gate_checksums`` — stale entries for removed built-ins disappear,
      legitimate gate changes are refreshed.
    - Entry lines for any other filename are project-owned (registered via
      the ``.allowed-gates`` flow) and preserved verbatim — sync.py never
      rewrites project data, matching the never-touch-project-files pattern
      of this module.
    - Comments and blank lines are preserved verbatim.
    """
    manifest_path = target_dir / RELEASE_GATE_CHECKSUMS_NAME
    preserved: list[str] = []
    if manifest_path.exists():
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            name = _checksum_entry_name(line)
            is_project_owned = (
                name is not None
                and name not in previously_managed
                and name not in gate_checksums
            )
            if name is None or is_project_owned:
                preserved.append(line)

    header_lines = [
        "# SHA-256 checksums for release-gate scripts (issue #603).",
        "# Format: <sha256>  <filename>  (sha256sum-compatible, '#'-comments allowed).",
        "# Built-in gates: regenerated by sync.py — do not edit by hand.",
        "# Project-owned gates: replace/add a checksum line, e.g.",
        "#   (cd <hooks_dir>/release-gates && sha256sum my-check.sh >> .sha256-checksums)",
    ]
    lines = header_lines + [
        f"{gate_checksums[name]}  {name}" for name in sorted(gate_checksums)
    ] + preserved
    content = "\n".join(lines) + "\n"

    rel = str(manifest_path.relative_to(project_root))
    if is_unchanged(manifest_path, content):
        log.skip(rel, "unchanged")
        return
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    # write_atomic, not write_checked: hex digests are not secrets, but the
    # secret scanner false-positives on long hex strings — the manifest is
    # fully derived from the gate scripts, nothing user-supplied to scan.
    write_atomic(manifest_path, content)
    log.action("COPY", rel, "release-gate checksum manifest (issue #603)")


def sync_hook_lib(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str = "Claude",
    provider_config: dict | None = None,
) -> None:
    """Copy shared hook helper scripts to <hooks_dir>/lib/.

    Issue #601: several hook scripts duplicated the same JSON-parsing
    Python heredoc. hooks/1-generic/lib/hook_common.sh centralizes the
    common helpers (JSON field extraction, python3/python resolution,
    credential redaction, audit-log append+rotation) as functions the
    individual hook scripts `source`. This is plain library code, not a
    hook — never registered in settings.json, no `event`/`matcher`
    metadata expected on its files.

    Same 0-external / 1-generic / 2-platform layering as
    collect_hook_sources() (via the ``subdir`` parameter), same
    always-copied / .agent-meta-managed-tracked / never-touch-project-owned-
    files pattern as sync_release_gates(). Security-boundary hooks
    (orchestrator-guard.sh, dod-push-check.sh) fail CLOSED if this file is
    missing when they try to source it (issue #595) — so this function
    must run in the same sync pass as sync_hooks(), never independently.
    """
    pc = (provider_config or {}).get(provider, {})
    hooks_dir_rel = pc.get("hooks_dir", CLAUDE_HOOKS_DIR)

    platforms = config.get("platforms", [])
    sources = collect_hook_sources(agent_meta_root, platforms, subdir=HOOK_LIB_SUBDIR)
    # See sync_hooks() (issue #630): no verified hook_protocol -> nothing
    # sources this lib anymore, clean up any previously-deployed copy. Only
    # gated when a real provider_config was supplied -- see sync_release_gates()
    # for why (test/low-level callers without one keep pre-#630 behavior).
    if provider_config is not None and not provider_hooks_supported(pc):
        sources = []

    target_dir = project_root / hooks_dir_rel / HOOK_LIB_SUBDIR
    managed_index_path = target_dir / ".agent-meta-managed"

    previously_managed: set[str] = set()
    if managed_index_path.exists():
        for line in managed_index_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                previously_managed.add(line.strip())

    if not sources and not previously_managed:
        return  # nothing shipped, nothing to clean up

    now_managed: set[str] = set()

    if not dry_run and sources:
        target_dir.mkdir(parents=True, exist_ok=True)

    for source_path, output_name in sources:
        target_path = safe_path(target_dir, output_name)
        source_content = source_path.read_text(encoding="utf-8")

        now_managed.add(output_name)
        rel_out = str(target_path.relative_to(project_root))
        rel_source = str(source_path.relative_to(agent_meta_root))
        if not dry_run:
            target_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            if write_checked(target_path, source_content, log, rel_source, dry_run=dry_run):
                log.action("COPY", rel_out, rel_source)
            else:
                log.skip(rel_out, "unchanged")
        except Exception as exc:
            log.warning(f"Failed to deploy hook lib file {rel_out}: {exc}")
            continue

    # Remove stale shipped lib files — never touches project-owned files
    # dropped directly into <hooks_dir>/lib/ (not tracked here).
    if target_dir.exists():
        for existing in sorted(target_dir.glob("*.sh")):
            if existing.name not in now_managed and existing.name in previously_managed:
                log.action("DELETE", str(existing.relative_to(project_root)),
                           "hook lib file removed from agent-meta sources")
                if not dry_run:
                    existing.unlink()

    if not dry_run and now_managed:
        managed_index_path.parent.mkdir(parents=True, exist_ok=True)
        managed_index_path.write_text(
            "\n".join(sorted(now_managed)) + "\n", encoding="utf-8"
        )
