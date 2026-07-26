from pathlib import Path

RULES_DIR = Path("rules/1-generic")

REQUIRED_VARIABLES = {
    "a2a-delegation-gates.md": ["{{A2A_MAX_DEPTH}}", "{{A2A_T_SIZE_LIMIT}}"],
    "commit-conventions.md": ["{{CODE_LANGUAGE}}"],
    "dod-criteria.md": [
        "{{#if DOD_REQ_TRACEABILITY}}",
        "{{#if DOD_TESTS_REQUIRED}}",
        "{{#if DOD_CODEBASE_OVERVIEW}}",
        "{{#if DOD_SECURITY_AUDIT}}"
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
