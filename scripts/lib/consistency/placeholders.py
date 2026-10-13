"""Placeholder validation: {{VAR}} usage in agent templates."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Optional

from .report import Finding, Severity
from ..io import load_yaml_file

# Known built-in variables injected by sync.py / build_variables()
_BUILTIN_VARS: frozenset[str] = frozenset({
    # Core project identifiers
    "PREFIX", "PROJECT_SHORT", "PROJECT_NAME", "PROJECT_DESCRIPTION",
    "PROJECT_CONTEXT", "PROJECT_GOAL", "PROJECT_LANGUAGES", "PROJECT_STRUCTURE",
    "ENTRY_POINT_PATTERN", "KEY_PATTERNS", "PLATFORM", "RUNTIME", "LANGUAGE",
    # Agent-meta metadata
    "AGENT_META_VERSION", "AGENT_META_DATE", "AGENT_META_REPO", "AGENT_META_REL_PATH",
    "AGENT_TABLE", "AGENT_HINTS",
    # README structure standard (issue #682 §3)
    "README_BADGES", "README_WARNINGS_ENABLED", "README_SECTIONS",
    # Provider / AI
    "AI_PROVIDER", "MAX_PARALLEL_AGENTS", "PARALLEL_PATTERN", "FILE_AFFINITY_HINT", "ANALYSIS_ENABLED",
    # DoD flags
    "DOD_REQ_TRACEABILITY", "DOD_TESTS_REQUIRED", "DOD_CODEBASE_OVERVIEW",
    "DOD_SECURITY_AUDIT", "DOD_PRESET",
    "DOD_AI_SECURITY_REVIEW", "DOD_PROMPT_GOVERNANCE", "DOD_LIFECYCLE_OWNERSHIP",
    "DOD_SE_REQUIRED", "DOD_SE_OPTIONAL", "DOD_SE_RECOMMENDED", "DOD_SE_STRICT",
    # Language
    "DOCS_LANGUAGE", "INTERNAL_DOCS_LANGUAGE", "COMMUNICATION_LANGUAGE",
    "USER_INPUT_LANGUAGE", "CODE_LANGUAGE",
    # Dev environment
    "DEV_COMMANDS", "BUILD_COMMAND", "BUILD_COMMANDS",
    "TEST_COMMAND", "TEST_COMMANDS", "DEV_STACK_START", "DEV_STACK_RELOAD",
    # Extensions
    "EXTENSION_DIR",
    # Provider-specific paths/files (injected per provider in sync_agents_for_provider)
    "CONTEXT_FILE", "SKILLS_DIR", "PENDING_TASKS_FILE", "FILE_BASED_AGENTS",
    # Git / platform
    "GIT_PLATFORM", "GIT_REMOTE_URL", "GIT_MAIN_BRANCH",
    # Requirements
    "REQ_CATEGORIES", "REQ_CATEGORIES_LIST",
    # Knowledge Domain
    "KNOWLEDGE_DOMAIN",
    # Code quality
    "CODE_CONVENTIONS", "ARCHITECTURE", "EXTRA_DONTS", "CODE_QUALITY_RULES",
    # Tester / developer snippets
    "TESTER_SNIPPETS_PATH", "DEVELOPER_SNIPPETS_PATH", "SNIPPETS_DIR",
    # Docker / deployment
    "SERVICE_NAME", "CONTAINER_NAME", "PRIMARY_PORT", "EXTRA_PORTS", "PORT",
    "DOCKER_STACKS_OVERVIEW", "EXTRA_VOLUMES", "EXTRA_VOLUME_DEFINITIONS",
    "EXTRA_ENV_VARS", "EXTRA_STARTUP_INFO", "HOST_LAN_IP",
    "APP_URL", "APP_USER", "BASE_IMAGE", "APT_PACKAGES",
    "TEST_BASE_IMAGE", "TEST_APT_PACKAGES", "TEST_BINARY_INSTALL",
    "BINARY_NAME", "BINARY_URL", "INSTALL_COMMAND", "LOCKFILE",
    "DEFAULT_TEST_COMMAND", "SMOKE_TEST_COMMAND", "E2E_TEST_COMMAND", "E2E_ENV_VARS",
    "VOLUME_NAME", "STARTUP_CREDENTIALS",
    # Release
    "BUILD_OUTPUT", "ARTIFACT_ZIP_CMD", "ARTIFACT_TAR_CMD", "GH_ASSETS",
    "REQUIRED_BINARIES_SECTION", "BINARY_INSTALL_STEPS", "REQUIRED_BINARY_NAMES",
    "BUILD_SYSTEM_NOTES", "VERSION_DIST_BEHAVIOUR",
    # Misc
    "SYSTEM_DEPENDENCIES", "SYSTEM_URLS",
    # Orchestrator (injected by build_variables)
    "ORCHESTRATOR_ENABLED", "ORCHESTRATOR_STRICT", "DIRECT_DISPATCH_ENABLED", "DIRECT_DISPATCH_SECTION", "ORCHESTRATOR_OUTCOME_CACHING",
    "ORCHESTRATOR_CACHE_TTL", "ORCHESTRATOR_CACHE_MAX_ENTRIES",
    "A2A_PROTOCOL_ENABLED", "CHECKPOINTING_ENABLED", "AUTO_COMMIT_ENABLED",
    "A2A_HANDOFF_BLOCK", "ANTI_RECURSION_BLOCK", "DOD_REQ_BLOCK", "DOD_TESTS_BLOCK",
    "UNKNOWN_FALLBACK_META_FEEDBACK", "UNKNOWN_FALLBACK_MAIN_CHAT",
    "UNKNOWN_FALLBACK_ASK_USER",

    # Repo-containment ("prison mode") — spec §4.5
    "REPO_CONTAINMENT_ENABLED", "REPO_CONTAINMENT_BLOCK",
    "REPO_CONTAINMENT_TMP_SINK_ENABLED", "REPO_CONTAINMENT_TMP_PATH",

    # Feature flags (injected by build_variables)
    "SE_ENABLED", "SE_BASE_DIR", "VALIDATOR_ENABLED", "REFLECTION_PAIRS_ENABLED",
    "QUALITY_PIPELINES_ENABLED", "MAX_ITERATIONS", "DEVELOPER_TIERS_ENABLED",
    "A2A_T_SIZE_LIMIT", "A2A_T_SIZE_LIMIT_TOKENS", "A2A_MAX_DEPTH",
    # Context density flag (derived from context_file.mode by build_variables, issue #540)
    "COMPACT_MODE",

    "SPEC_PLAN_WORKFLOW_ENABLED", "SPEC_PLAN_SPECS_DIR", "SPEC_PLAN_PLANS_DIR",

    "ENFORCEMENT_TIER", "GATE_ENFORCED", "GATE_PARTIAL", "GATE_ADVISORY",
    "GATE_NEUTRAL",
    "RUNTIME_GATE_PLUGIN_MODE",
    # Orchestrator snippet blocks (loaded from snippets/orchestrator/*.md by build_variables)
    "SE_MODE_BLOCK", "A2A_PROTOCOL_BLOCK", "CHECKPOINTING_BLOCK", "QUALITY_PIPELINES_BLOCK",
    "STATUS_TABLE_BLOCK", "AUTO_COMMIT_BLOCK",
    # Subagent permission policy (Feature A, injected by build_variables / the
    # per-provider bundle in subagent_permissions.py)
    "SUBAGENT_PERMISSIONS_MODE", "SUBAGENT_PERMISSIONS_STRICT",
    "SUBAGENT_PERMISSIONS_WARN", "SUBAGENT_PERMISSIONS_OFF",
    "SUBAGENT_PERMISSIONS_ENABLED", "SUBAGENT_PERMISSIONS_BLOCK",
    # Developer-tier shared blocks (loaded from snippets/developer/*.md by build_variables)
    "BROWSER_VERIFICATION_BLOCK", "LANGUAGE_BEST_PRACTICES_BLOCK",
    # Security shared blocks (loaded from snippets/security/*.md by build_variables)
    "PROMPT_INJECTION_DEFENSE_BLOCK",
    # Convention blocks (rendered from config/conventions-presets.yaml by build_variables)
    "RELEASE_VERSIONING_BLOCK", "RELEASE_CHANGELOG_BLOCK", "GIT_ISSUE_NAMING_BLOCK",
    "RELEASE_CUSTOM_CHECKLIST_BLOCK", "RELEASE_CUTOFF_BLOCK",
    # Issue language for feedback-created GitHub issues (issue #579)
    "ISSUE_LANGUAGE",
    # SE cascade variables (from role-defaults.yaml se_variables)
    "SE_MIN_DEPTH", "SE_MAX_DEPTH", "SE_MAX_CRITIC_ITERATIONS", "SE_MAX_PARALLEL_CELLS",
    "SE_MAX_CELLS", "cost_limit_eur",
    # SE pipeline extension (REQ-SE-01..REQ-SE-22)
    "output_persistence", "resume_pointer_path", "se_pipeline_classifier",
    "se_persistence_schema_dir",
    # Generated tables (injected by build_variables)
    "AGENT_DELEGATION_TABLE", "PROJECT_SPECIFIC_AGENTS",
    # Active-set contract (IC-17, active_set_variables); ROLE_*_ACTIVE is a
    # dynamic family (see _DYNAMIC_PREFIXES)
    "ACTIVE_ROLES",
    "PIPELINE_MATCH_TABLE", "INTENT_ROUTING_TABLE", "PIPELINE_DETAIL_BLOCKS",
    "PIPELINE_DETAILS_DIR",
    # Structured intent-routing tool definition, resolved per provider in
    # agent_sync._build_provider_vars from build_variables' provider-mapped
    # prerender (issue #264)
    "INTENT_ROUTING_TOOLS",

    "ROUTE_INTENT_CALLABLE",
    # Block-inlining variables loaded from snippets/agents/ by
    # config._load_block_snippet_variables (resolved in every sync)
    "OUTPUT_GUARD_BLOCK", "BACKGROUND_PROCESS_GUARD_BLOCK", "PARSE_INPUT_BLOCK",
    "ESCALATE_CARD_BLOCK",
    # Paths
    "AGENTS_DIR",
    # Release / plugin packaging
    "PLUGIN_DIR_NAME",
    # Tmp-sink path (injected by build_variables; was a builder ratchet entry)
    "TMP_SINK_PATH",
})

# Placeholder families resolved downstream, not by build_variables():
# PAL_* by the DelegationSyntaxEngine, PIPELINE_*_BLOCK by inject_pipeline_blocks(),
# SKILL_* by the skills layer (scripts/lib/skills.py:502-509, wrapper variables),
# MCP_GUARDRAILS_LIST at runtime (scripts/lib/rules.py:248 and
# scripts/lib/context.py:1761).
_DYNAMIC_PREFIXES: tuple[re.Pattern, ...] = (
    re.compile(r'^PAL_[A-Z0-9_]+$'),
    re.compile(r'^SKILL_[A-Z0-9_]+$'),
    re.compile(r'^MCP_GUARDRAILS_LIST$'),
    re.compile(r'^ROLE_[A-Z0-9_]+_ACTIVE$'),
    re.compile(r'^PIPELINE_[A-Z0-9_]+_(BLOCK|PROVIDER_BLOCKS)$'),
)

# Known common typos: wrong_name → correct_name
_KNOWN_TYPOS: dict[str, str] = {
    "DOCS_LANGAUGE": "DOCS_LANGUAGE",
    "INTERNAL_DOCS_LANGAUGE": "INTERNAL_DOCS_LANGUAGE",
    "COMUNICATON_LANGUAGE": "COMMUNICATION_LANGUAGE",
    "PROJECT_CONTEX": "PROJECT_CONTEXT",
    "AGENT_META_VESION": "AGENT_META_VERSION",
    "DOD_REQ_TRACEABILTY": "DOD_REQ_TRACEABILITY",
    "EXTENTION_DIR": "EXTENSION_DIR",
    "PREFX": "PREFIX",
}

_PLACEHOLDER_RE = re.compile(r'\{\{([A-Z0-9_]+)\}\}')


def check_placeholders(path: Path, content: str, agent_meta_root: Path,
                        extra_vars: set[str] | None = None) -> list[Finding]:
    """Check {{VAR}} placeholders in an agent template."""
    findings = []
    rel = _rel(path, agent_meta_root)
    known = _BUILTIN_VARS | (extra_vars or set())

    # Strip frontmatter before scanning
    body = re.sub(r'^---.*?---\s*\n', '', content, count=1, flags=re.DOTALL)

    # Strip fenced code blocks (``` ... ```) to avoid false positives on documented examples
    body = re.sub(r'```.*?```', '', body, flags=re.DOTALL)
    # Strip inline code (`...`) as well
    body = re.sub(r'`[^`\n]+`', '', body)

    seen: set[str] = set()
    for match in _PLACEHOLDER_RE.finditer(body):
        var = match.group(1)
        if var in seen:
            continue
        seen.add(var)

        # Check for known typos first
        if var in _KNOWN_TYPOS:
            findings.append(Finding(
                Severity.ERROR, "placeholders.typo", rel,
                f"Placeholder '{{{{{var}}}}}' looks like a typo.",
                f"Did you mean '{{{{{_KNOWN_TYPOS[var]}}}}}' ?",
            ))
        elif var not in known and not any(p.match(var) for p in _DYNAMIC_PREFIXES):
            findings.append(Finding(
                Severity.WARNING, "placeholders.unknown", rel,
                f"Placeholder '{{{{{var}}}}}' is not a known built-in variable.",
                "Add it to project.yaml variables: section, or check for a typo.",
            ))
    return findings


def load_project_vars(agent_meta_root: Path) -> set[str]:
    """Load variable names from .meta-config/project.yaml variables section.

    Canonical single-file loader (Issue #479), fail-soft: absent/malformed
    file or missing PyYAML yields no variables (former broad-except behavior).
    """
    config_path = agent_meta_root / ".meta-config" / "project.yaml"
    data = load_yaml_file(config_path, on_error="default", default={})
    return set((data.get("variables") or {}).keys())


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)


# --- IC-32 placeholders.builder-known-set (AC-66) -------------------------
# A builder maps (config, agent_meta_root, project_root) -> {VAR: value}.
# Extension point: 0b.1 appends ``active_set_variables``, Phase 2 appends
# ``resolve_context_profile``; the derived set follows this list automatically.
Builder = Callable[[dict, Path, Optional[Path]], dict]


def _build_variables_builder(config: dict, agent_meta_root: Path,
                             project_root: Optional[Path] = None) -> dict:
    from ..config import build_variables
    return build_variables(config, agent_meta_root, project_root)[0]


def active_set_variables_builder(config: dict, agent_meta_root: Path,
                                 project_root: Optional[Path] = None) -> dict:
    """Wrap IC-17 ``active_set_variables`` in the builder signature."""
    from ..active_set import active_set_variables, compute_active_set
    return active_set_variables(compute_active_set(
        config, agent_meta_root, project_root or agent_meta_root, warn_sink=[]))


BUILDERS: list[Builder] = [_build_variables_builder, active_set_variables_builder]

# Builder variables resolved per pipeline name (config-dependent family).
# Boundary: any PIPELINE_<NAME>_(ENABLED|DESCRIPTION|STAGES) matches, whether
# or not <NAME> is a configured pipeline; a typo in <NAME> is not detected.
_BUILDER_FAMILIES: tuple[re.Pattern, ...] = (
    re.compile(r'^PIPELINE_[A-Z0-9_]+_(ENABLED|DESCRIPTION|STAGES)$'),
)

# Ratchet (shrink only): builder variables that predate this check and are not
# in _BUILTIN_VARS. New builder variables must be registered, not added here.
_UNREGISTERED_BUILDER_RATCHET: frozenset[str] = frozenset({
    "AGENT_HINTS_CLAUDE", "AGENT_LOCATIONS", "DEVELOPER_SNIPPETS_PATH_SET",
    "DEV_STACK_START_SET", "EFFORT_ESTIMATOR_ENABLED", "KNOWLEDGE_BUNDLE_PATH",
    "KNOWLEDGE_ENGINE_ENABLED", "KNOWLEDGE_SCHEMA_PATH", "KNOWLEDGE_SOURCES_DIR",
    "KNOWLEDGE_WIKI_DIR", "NATIVE_EXTENSIONS_ENABLED",
    "NATIVE_EXTENSIONS_WHITELIST_ACTIVE", "NATIVE_EXTENSIONS_WHITELIST_TABLE",
    "ORCH_MODE_ADVISORY", "ORCH_MODE_DISABLED", "ORCH_MODE_MAIN_CHAT",
    "ORCH_MODE_STRICT", "PROGRESS_CHAT_PUSH_ENABLED", "PROVIDER_ROUTING",
    "TESTER_SNIPPETS_PATH_SET", "WEB_PROJECT_ENABLED",
})

# Builder-internal keys (raw data, not template placeholders), filtered from
# the builder output in addition to every key with a leading underscore.
_BUILDER_INTERNAL_KEYS: frozenset[str] = frozenset({"active_agents"})

# Ratchet (shrink only): template placeholders neither builder-derived nor
# registered. SKILL_* and MCP_GUARDRAILS_LIST are covered by _DYNAMIC_PREFIXES.
# TECH_STACK / AGENT_RULES / EXTERNAL_DOCS_LANGUAGE: no filler found - possible
# defect or reference example (follow-up issue).
_UNKNOWN_TEMPLATE_RATCHET: frozenset[str] = frozenset({
    "TECH_STACK", "AGENT_RULES", "EXTERNAL_DOCS_LANGUAGE",
})


def derive_builder_vars(agent_meta_root: Path) -> set[str]:
    """Run all BUILDERS on an empty config and return the produced keys,
    minus builder internals (leading underscore, _BUILDER_INTERNAL_KEYS)."""
    keys: set[str] = set()
    for builder in BUILDERS:
        keys |= set(builder({}, agent_meta_root, None))
    return {k for k in keys
            if not k.startswith("_") and k not in _BUILDER_INTERNAL_KEYS}


def _is_family(var: str) -> bool:
    return (any(p.match(var) for p in _DYNAMIC_PREFIXES)
            or any(p.match(var) for p in _BUILDER_FAMILIES))


def check_builder_known_set(agent_meta_root: Path) -> list[Finding]:
    """ERROR for builder variables missing from the registered set and for
    template placeholders not supplied by any builder (source repo only).

    Reading: the builder output is compared against _BUILTIN_VARS, the
    project variables and the ratchet (otherwise the check would be
    tautological: the builder validated against itself). Template
    placeholders must be in the builder output or the registered set.
    Scope: agents/*/*.md, rules/*/*.md, snippets/*/*.md."""
    findings: list[Finding] = []
    check = "placeholders.builder-known-set"
    derived = derive_builder_vars(agent_meta_root)
    registered = (_BUILTIN_VARS | _UNREGISTERED_BUILDER_RATCHET
                  | load_project_vars(agent_meta_root))
    for var in sorted(derived):
        if var in registered or _is_family(var):
            continue
        findings.append(Finding(
            Severity.ERROR, check, "scripts/lib/consistency/placeholders.py",
            f"Builder variable '{var}' is not in the known placeholder set.",
            "Add it to _BUILTIN_VARS (and the CLAUDE.md variables table).",
        ))
    known = derived | registered
    for pattern in ("agents/*/*.md", "rules/*/*.md", "snippets/*/*.md"):
        for path in sorted(agent_meta_root.glob(pattern)):
            body = path.read_text(encoding="utf-8")
            body = re.sub(r'```.*?```', '', body, flags=re.DOTALL)
            body = re.sub(r'`[^`\n]+`', '', body)
            for var in sorted(set(_PLACEHOLDER_RE.findall(body))):
                if (var in known or var in _UNKNOWN_TEMPLATE_RATCHET
                        or var in _KNOWN_TYPOS or _is_family(var)):
                    continue
                findings.append(Finding(
                    Severity.ERROR, check, _rel(path, agent_meta_root),
                    f"Placeholder '{{{{{var}}}}}' is not supplied by any variable builder.",
                    "Provide it from a builder in BUILDERS or fix the name.",
                ))
    return findings
