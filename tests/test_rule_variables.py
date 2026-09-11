import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.config import build_variables  # noqa: E402
from lib.log import SyncLog  # noqa: E402
from lib.variables import substitute  # noqa: E402

RULES_DIR = Path("rules/1-generic")

# Uppercase {{VAR}} tokens only -- conditional markers ({{#if X}}, {{else}},
# {{/if}}) are resolved separately by strip_inactive_conditional_blocks and
# are intentionally not matched here.
_UNRESOLVED_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")

REQUIRED_VARIABLES = {
    "a2a-delegation-gates.md": ["{{A2A_MAX_DEPTH}}", "{{A2A_T_SIZE_LIMIT}}"],
    "commit-conventions.md": ["{{CODE_LANGUAGE}}"],
    "dod-criteria.md": [
        "{{#if DOD_REQ_TRACEABILITY}}",
        "{{#if DOD_TESTS_REQUIRED}}",
        "{{#if DOD_CODEBASE_OVERVIEW}}",
        "{{#if DOD_SECURITY_AUDIT}}",
        "{{#if DOD_AI_SECURITY_REVIEW}}",
        "{{#if DOD_PROMPT_GOVERNANCE}}",
        "{{#if DOD_LIFECYCLE_OWNERSHIP}}"
    ],
    "language.md": [
        "{{COMMUNICATION_LANGUAGE}}",
        "{{USER_INPUT_LANGUAGE}}",
        "{{DOCS_LANGUAGE}}",
        "{{INTERNAL_DOCS_LANGUAGE}}",
        "{{CODE_LANGUAGE}}"
    ],
    "lifecycle-tasks.md": ["{{PENDING_TASKS_FILE}}"],
    "use-orchestrator.md": [
        "{{#if ORCH_MODE_STRICT}}",
        "{{#if ORCH_MODE_ADVISORY}}",
        "{{#if DIRECT_DISPATCH_ENABLED}}",
        "{{DIRECT_DISPATCH_SECTION}}",
        "{{#if ORCH_MODE_MAIN_CHAT}}",
        "{{INTENT_ROUTING_TABLE}}",
        "{{#if NATIVE_EXTENSIONS_ENABLED}}",
        "{{#if NATIVE_EXTENSIONS_WHITELIST_ACTIVE}}",
        "{{NATIVE_EXTENSIONS_WHITELIST_TABLE}}",
        "{{#unless NATIVE_EXTENSIONS_ENABLED}}",
        "{{#unless ORCH_MODE_MAIN_CHAT}}"
    ]
}

def test_rule_variables_present():
    """Ensure that all required variables and placeholders exist in the rule templates."""
    for filename, variables in REQUIRED_VARIABLES.items():
        filepath = RULES_DIR / filename
        assert filepath.exists(), f"Rule file {filename} is missing!"
        
        content = filepath.read_text(encoding="utf-8")
        for var in variables:
            assert var in content, f"Variable/Placeholder '{var}' missing in {filename}"


def test_rule_placeholders_resolve_in_minimal_project():
    """Issue #733: with only a minimal project.yaml, substituting the
    always-copied rule set must leave no literal ``{{VAR}}`` behind.

    ``--validate`` only scans agent templates, so this is the regression net
    that actually covers ``rules/1-generic/``.
    """
    config = {
        "project": {"name": "smoke-test", "prefix": "sm"},
        "ai-providers": ["Claude"],
        "roles": ["developer"],
    }
    variables, _ = build_variables(config, REPO_ROOT)
    for filename in ("language.md", "commit-conventions.md"):
        filepath = REPO_ROOT / RULES_DIR / filename
        rendered = substitute(
            filepath.read_text(encoding="utf-8"), variables, filename, SyncLog()
        )
        leftovers = _UNRESOLVED_RE.findall(rendered)
        assert leftovers == [], f"{filename} still leaks {leftovers}"
