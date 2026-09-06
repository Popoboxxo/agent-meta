"""External-tool injection drift scanning + artifact rendering.

Split out of ``external_tools.py`` (module size limit — see CLAUDE.md
"Python (scripts/lib/)" conventions, <= 600 lines per module) to keep the
registry/activation/rule-generation concerns in that module separate from the
drift-detection concern here. Public API (``scan_injection_drift``,
``render_injection_drift_artifacts``) stays importable from
``scripts.lib.external_tools`` via thin re-export wrappers there — this
module is the only thing that actually imports from ``external_tools`` (not
the other way around), so there is no import cycle.
"""
from __future__ import annotations

from pathlib import Path

from .deactivation import get_active_providers
from .external_tools import (
    DEFAULT_RULES_DIR,
    TOOL_RULE_PREFIX,
    resolve_injection_path,
)
from .io import write_checked
from .log import SyncLog
from .registry_query import (
    load_external_tools_registry,
    resolve_active_external_tools,
    resolve_active_mcp_servers,
)
from .rule_index import read_managed_index

DRIFT_FILENAME = "external-tools-drift.md"
_DRIFT_CAP = 10


def _read_managed_index(dir_path: Path) -> set[str]:
    """Read the shared rules.py-owned '.agent-meta-managed' index from dir_path."""
    return read_managed_index(dir_path / ".agent-meta-managed")


# ---------------------------------------------------------------------------
# Drift artifact rendering
# ---------------------------------------------------------------------------

def _generate_drift_content(findings: list[dict]) -> str:
    """Generate Markdown content for external-tools-drift.md from findings."""
    lines = [
        "# External-Tool Injection Drift", "",
        "> Automatisch erkannt von `check_injection_drift` — Fremd-Artefakte, die keinem "
        "aktiven Tool in `config/plugin-catalog.yaml` als `permitted-injections` "
        "deklariert sind. Nur Warnung, kein automatisches Eingreifen.",
        "", "---", "",
    ]
    shown = findings[:_DRIFT_CAP]
    for f in shown:
        tool_label = f["tool"] or "keinem registrierten Tool zugeordnet"
        lines.append(f"- `{f['path']}` ({f['kind']}) — {tool_label}")
    remaining = len(findings) - len(shown)
    if remaining > 0:
        lines.append(f"- … {remaining} weitere, siehe sync.log")
    lines.append("")
    return "\n".join(lines) + "\n"


def render_injection_drift_artifacts(
    findings_by_provider: dict[str, list[dict]],
    project_root: Path,
    provider_config: dict,
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Render sparse external-tools-drift.md files when drift is detected.

    For each provider with has_rules: True, if findings exist, write
    .claude/rules/external-tools-drift.md (capped at 10 items). If no
    findings exist, delete the file if present. Warnings are logged for all
    findings regardless of has_rules setting. Uses write_checked for
    idempotence.
    """
    for provider, findings in findings_by_provider.items():
        pc = provider_config.get(provider, {})

        # Log warnings for all findings unconditionally.
        for f in findings:
            log.warning(
                f"external-tools: undeclared artifact '{f['path']}' ({f['kind']}) for provider "
                f"'{provider}' — not covered by any active tool's permitted-injections"
            )

        # Skip file rendering for providers without has_rules capability.
        if not pc.get("has_rules"):
            continue

        rules_dir = project_root / pc.get("rules_dir", DEFAULT_RULES_DIR)
        target_path = rules_dir / DRIFT_FILENAME

        if not findings:
            if target_path.exists():
                log.action("DELETE", str(target_path.relative_to(project_root)), "no drift found")
                if not dry_run:
                    target_path.unlink()
            continue

        content = _generate_drift_content(findings)
        rel_out = str(target_path.relative_to(project_root))

        if not dry_run:
            target_path.parent.mkdir(parents=True, exist_ok=True)

        if write_checked(target_path, content, log, "external-tools-drift", dry_run=dry_run):
            log.action("WRITE", rel_out, "external-tools-drift")
        else:
            log.skip(rel_out, "unchanged")


# ---------------------------------------------------------------------------
# Injection drift scanning
# ---------------------------------------------------------------------------

# Top-level entries under a provider's infra root that agent-meta itself may
# place there, independent of the four managed subdirs. Keyed by the
# provider_config field that names each one; a field absent from `pc` is
# skipped (not every provider has every capability).
_INFRA_ROOT_KNOWN_KEYS = [
    "agents_dir", "hooks_dir", "rules_dir", "commands_dir", "skills_dir",
    "snippets_dir", "extension_dir", "artifact_dir", "checkpoint_dir",
    "settings_file", "pending_tasks_file", "pipeline_details_dir",
]
# Written by sync_pipeline_detail_files() (scripts/lib/pipelines.py) for
# every active provider unconditionally — not gated by a has_X capability
# like hooks_dir/rules_dir/commands_dir, so it doesn't fit the
# capability_by_key fallback loop below. sync.py derives its path from
# agents_dir's parent when no explicit `pipeline_details_dir` is configured
# in ai-providers.yaml, but the basename is always this constant regardless
# of provider.
_PIPELINE_DETAILS_DIR_NAME = "pipeline-details"
# Per-provider hardcoded fallback dirs for capability-gated keys that some
# providers (Claude, Continue) never store in ai-providers.yaml, relying
# instead on a literal default in the sync code itself (dir_specs above /
# lib.commands.sync_commands_for_provider). Without this, the fallback
# directory is agent-meta's own managed dir, but scan_injection_drift has no
# key to read its name from and misreports it as a top-level foreign "other"
# finding.
#
# Mammouth has `has_commands: true` in ai-providers.yaml but no entry here:
# harmless today because lib.commands.sync_commands_for_provider() doesn't
# implement a Mammouth branch yet (no commands dir is ever written), so
# there's nothing to misreport. The moment a Mammouth commands writer lands,
# add its literal target dir here too, or this same false-positive class
# reappears for it.
_INFRA_ROOT_FALLBACK_DIRS = {
    "hooks_dir": {"Claude": ".claude/hooks"},
    "rules_dir": {"Claude": DEFAULT_RULES_DIR},
    "commands_dir": {"Claude": ".claude/commands", "Continue": ".continue/prompts"},
}


def scan_injection_drift(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    provider_config: dict,
) -> dict[str, list[dict]]:
    """Find files/dirs under each active provider's infra root that neither
    agent-meta itself manages (per-directory .agent-meta-managed indexes) nor
    any active external tool's permitted-injections declares. Pure — no writes.

    get_active_providers and resolve_active_mcp_servers are imported at module
    top level (Issue #478): deactivation is a leaf-side module and the MCP
    activation resolution lives in lib.registry_query, which does not import
    this module (or mcp) back — the former deferred imports carried no cycle
    anymore.
    """
    registry = load_external_tools_registry(agent_meta_root, config, project_root)
    active_tools = resolve_active_external_tools(config, agent_meta_root, project_root, registry=registry)
    active_mcp = set(resolve_active_mcp_servers(config, agent_meta_root, project_root))

    findings_by_provider: dict[str, list[dict]] = {}

    # Only scan providers actually CONFIGURED for this project (resolve_providers)
    # and not deactivated -- get_active_providers() gives exactly that set.
    # is_provider_active() alone was wrong: it only tests deactivation, so every
    # provider merely DEFINED in ai-providers.yaml (Codex/ZCode/... not in the
    # project's `ai-providers` list) was scanned. Harmless for providers whose
    # infra dirs don't exist, but Codex's rules_dir is the project-root `rules/`
    # -- which in agent-meta-self-hosting IS the framework SOURCE tree -- so the
    # scan misread rules/{0-external,1-generic,2-platform} as foreign artifacts
    # and wrote a stray rules/external-tools-drift.md into the source tree.
    active_providers = set(get_active_providers(config, provider_config))

    for provider, pc in provider_config.items():
        if provider not in active_providers:
            continue

        # Permitted set, resolved to absolute paths, keyed by dir-kind.
        permitted_by_kind: dict[str, set[Path]] = {"skill": set(), "hook": set(), "rule": set()}
        permitted_root_extra: set[Path] = set()  # kind: config/other
        for tool_name in active_tools:
            for entry in registry.get(tool_name, {}).get("permitted-injections", []):
                resolved = resolve_injection_path(entry, pc, project_root)
                if entry["kind"] in permitted_by_kind:
                    permitted_by_kind[entry["kind"]].add(resolved)
                else:
                    permitted_root_extra.add(resolved)

        provider_findings: list[dict] = []

        # --- managed subdirs: skill / hook / rule (declarable kinds) ---
        # "skill" is unconditional (no has_skills flag exists in
        # ai-providers.yaml). "hook"/"rule" are gated on the provider's own
        # has_hooks/has_rules capability flags — without the gate, a provider
        # lacking the key (e.g. Opencode: no hooks_dir/rules_dir at all) would
        # silently fall through to Claude's ".claude/hooks"/".claude/rules"
        # defaults and misattribute Claude's own dir content to it.
        dir_specs = [("skill", pc.get("skills_dir", ".claude/skills"))]
        if pc.get("has_hooks", False):
            dir_specs.append(("hook", pc.get("hooks_dir", ".claude/hooks")))
        if pc.get("has_rules", False):
            dir_specs.append(("rule", pc.get("rules_dir", ".claude/rules")))
        for kind, dir_rel in dir_specs:
            dir_path = project_root / dir_rel
            if not dir_path.is_dir():
                continue
            managed = _read_managed_index(dir_path)
            if kind == "rule":
                managed |= {f"{TOOL_RULE_PREFIX}{t}.md" for t in active_tools}
                managed |= {f"mcp-{s}.md" for s in active_mcp}
            for child in sorted(dir_path.iterdir()):
                # ".agent-meta-managed" (rules.py) plus the per-caller
                # ".agent-meta-managed-mcp" / "-tools" sidecar indexes
                # (mcp.py / external_tools.py) are agent-meta's own
                # bookkeeping files, never a foreign injection.
                if child.name == ".agent-meta-managed" or child.name.startswith(".agent-meta-managed-"):
                    continue
                if child.name in managed:
                    continue
                # A subdirectory that carries its OWN '.agent-meta-managed'
                # index (e.g. hooks/release-gates/, sync_release_gates() —
                # issue #558) is a nested, self-managed sync.py output, not a
                # foreign injection — its content is scoped by that sidecar
                # index the same way this dir's own .agent-meta-managed
                # scopes plain files. Deliberately generic (checks for the
                # sentinel file, not a hardcoded dir name) so any future
                # nested-managed hook subdirectory is covered too.
                if child.is_dir() and (child / ".agent-meta-managed").exists():
                    continue
                if child.resolve() in permitted_by_kind[kind]:
                    continue
                provider_findings.append({
                    "path": str(child.relative_to(project_root)),
                    "kind": kind,
                    "tool": None,
                })

        # --- agents_dir: no declarable permitted-injections kind exists for
        # it (per spec — agent files are never legitimately tool-installed).
        # Only an explicit kind: config/other entry (permitted_root_extra)
        # can excuse a finding here; the existing .agent-meta-managed index
        # (agents.py:1498) still excuses agent-meta's own generated roles.
        agents_dir_path = project_root / pc.get("agents_dir", ".claude/agents")
        if agents_dir_path.is_dir():
            managed = _read_managed_index(agents_dir_path)
            for child in sorted(agents_dir_path.iterdir()):
                if child.name == ".agent-meta-managed":
                    continue
                if child.name in managed:
                    continue
                if child.resolve() in permitted_root_extra:
                    continue
                provider_findings.append({
                    "path": str(child.relative_to(project_root)),
                    "kind": "other",
                    "tool": None,
                })

        # --- infra root: loose files/dirs beside the four managed subdirs ---
        # Determined from the provider's own infra root (parent of skills_dir,
        # e.g. ".claude" for Claude) rather than a hardcoded ".claude" literal,
        # so Gemini/.gemini, Opencode/.opencode etc. are covered the same way.
        skills_dir_rel = pc.get("skills_dir")
        if skills_dir_rel:
            infra_root = (project_root / skills_dir_rel).parent
            if infra_root.is_dir() and infra_root != project_root:
                known_names = set()
                for key in _INFRA_ROOT_KNOWN_KEYS:
                    val = pc.get(key)
                    if val:
                        known_names.add(Path(val).name)
                # Capability-gated fallback: the key may be absent from
                # ai-providers.yaml (Claude's hooks_dir/rules_dir/
                # commands_dir, Continue's commands_dir) with sync code
                # falling back to a hardcoded literal instead — only excuse
                # it when the provider actually has the capability, so e.g.
                # Opencode (has_rules: False) doesn't get a same-named
                # directory excused for the wrong reason.
                capability_by_key = {
                    "hooks_dir": "has_hooks", "rules_dir": "has_rules", "commands_dir": "has_commands",
                }
                for key, fallbacks in _INFRA_ROOT_FALLBACK_DIRS.items():
                    if pc.get(capability_by_key[key], False) and provider in fallbacks:
                        known_names.add(Path(fallbacks[provider]).name)
                known_names.add(_PIPELINE_DETAILS_DIR_NAME)
                # settings_local_file's basename varies per provider (e.g.
                # Continue: config.local.yaml, not settings.local.json).
                settings_local_val = pc.get("settings_local_file")
                if settings_local_val:
                    known_names.add(Path(settings_local_val).name)
                known_names.add("settings.local.json")
                # agent-memory/agent-memory-local are a documented agent-meta
                # feature (docs/guides/features/agent-memory.md), not external-
                # tool injections — no dedicated provider_config key exists for
                # them (agent-memory-local only appears buried in Claude's
                # gitignore_entries), so they're excused as literals.
                known_names.add("agent-memory")
                known_names.add("agent-memory-local")
                # Claude Code harness's own session task-scheduler lock —
                # local-machine runtime state (excluded via .git/info/exclude,
                # not a shared gitignore entry), not an external-tool
                # injection or an agent-meta artifact.
                known_names.add("scheduled_tasks.lock")
                for child in sorted(infra_root.iterdir()):
                    if child.name in known_names:
                        continue
                    if child.resolve() in permitted_root_extra:
                        continue
                    provider_findings.append({
                        "path": str(child.relative_to(project_root)),
                        "kind": "other",
                        "tool": None,
                    })

        findings_by_provider[provider] = provider_findings

    return findings_by_provider
