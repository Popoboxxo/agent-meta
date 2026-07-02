"""Placeholder validation: {{VAR}} usage in agent templates."""

import re
from pathlib import Path

from .report import Finding, Severity

# Known built-in variables injected by sync.py / build_variables()
_BUILTIN_VARS: frozenset[str] = frozenset({
    # Core project identifiers
    "PREFIX", "PROJECT_SHORT", "PROJECT_NAME", "PROJECT_DESCRIPTION",
    "PROJECT_CONTEXT", "PROJECT_GOAL", "PROJECT_LANGUAGES", "PROJECT_STRUCTURE",
    "ENTRY_POINT_PATTERN", "KEY_PATTERNS", "PLATFORM", "RUNTIME", "LANGUAGE",
    # Agent-meta metadata
    "AGENT_META_VERSION", "AGENT_META_DATE", "AGENT_META_REPO",
    "AGENT_TABLE", "AGENT_HINTS",
    # Provider / AI
    "AI_PROVIDER", "MAX_PARALLEL_AGENTS", "PARALLEL_PATTERN", "FILE_AFFINITY_HINT", "ANALYSIS_ENABLED",
    # DoD flags
    "DOD_REQ_TRACEABILITY", "DOD_TESTS_REQUIRED", "DOD_CODEBASE_OVERVIEW",
    "DOD_SECURITY_AUDIT", "DOD_PRESET",
    "DOD_SE_REQUIRED", "DOD_SE_OPTIONAL", "DOD_SE_RECOMMENDED", "DOD_SE_STRICT",
    # Language
    "DOCS_LANGUAGE", "INTERNAL_DOCS_LANGUAGE", "COMMUNICATION_LANGUAGE",
    "USER_INPUT_LANGUAGE", "CODE_LANGUAGE",
    # Dev environment
    "DEV_COMMANDS", "BUILD_COMMAND", "BUILD_COMMANDS",
    "TEST_COMMAND", "TEST_COMMANDS", "DEV_STACK_START", "DEV_STACK_RELOAD",
    # Extensions
    "EXTENSION_DIR",
    # Git / platform
    "GIT_PLATFORM", "GIT_REMOTE_URL", "GIT_MAIN_BRANCH",
    # Requirements
    "REQ_CATEGORIES", "REQ_CATEGORIES_LIST",
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
    "A2A_PROTOCOL_ENABLED", "CHECKPOINTING_ENABLED",
    "UNKNOWN_FALLBACK_META_FEEDBACK", "UNKNOWN_FALLBACK_MAIN_CHAT",
    "UNKNOWN_FALLBACK_ASK_USER",
    # Feature flags (injected by build_variables)
    "SE_ENABLED", "SE_BASE_DIR", "VALIDATOR_ENABLED", "REFLECTION_PAIRS_ENABLED",
    "QUALITY_PIPELINES_ENABLED", "MAX_ITERATIONS", "DEVELOPER_TIERS_ENABLED",
    "A2A_T_SIZE_LIMIT", "A2A_T_SIZE_LIMIT_TOKENS", "A2A_MAX_DEPTH",
    # Orchestrator snippet blocks (loaded from snippets/orchestrator/*.md by build_variables)
    "SE_MODE_BLOCK", "A2A_PROTOCOL_BLOCK", "CHECKPOINTING_BLOCK", "QUALITY_PIPELINES_BLOCK",
    # SE cascade variables (from role-defaults.yaml se_variables)
    "SE_MIN_DEPTH", "SE_MAX_DEPTH", "SE_MAX_CRITIC_ITERATIONS", "SE_MAX_PARALLEL_CELLS",
    "SE_MAX_CELLS", "cost_limit_eur",
    # SE pipeline extension (REQ-SE-01..REQ-SE-22)
    "output_persistence", "resume_pointer_path", "se_pipeline_classifier",
    "se_persistence_schema_dir",
    # Generated tables (injected by build_variables)
    "AGENT_DELEGATION_TABLE", "PROJECT_SPECIFIC_AGENTS",
    # Paths
    "AGENTS_DIR",
    # Release / plugin packaging
    "PLUGIN_DIR_NAME",
})

# Placeholder families resolved downstream, not by build_variables():
# PAL_* by the DelegationSyntaxEngine, PIPELINE_*_BLOCK by inject_pipeline_blocks().
_DYNAMIC_PREFIXES: tuple[re.Pattern, ...] = (
    re.compile(r'^PAL_[A-Z0-9_]+$'),
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
    """Load variable names from .meta-config/project.yaml variables section."""
    config_path = agent_meta_root / ".meta-config" / "project.yaml"
    if not config_path.exists():
        return set()
    try:
        import yaml
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except (ImportError, Exception):
        return set()
    return set((data.get("variables") or {}).keys())


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)
