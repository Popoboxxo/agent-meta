"""Delegation table generation for the orchestrator template.

Auto-generates the agent delegation table from config/role-defaults.yaml
during sync.py runs (Issue #249).
"""

from pathlib import Path

from .roles import load_roles_config


# Parallelism labels per role — matches the heuristic defined in Issue #249.
_PARALLEL_LABELS: dict[str, str] = {
    "ideation": "✅ (Multi-Aspekte)",
    "requirements": "❌ (sequentiell)",
    "developer": "✅ (Multi-Dateien)",
    "feature": "✅ (intern)",
    "git": "❌ (atomar)",
    "documenter": "✅ (Multi-Sections)",
    "release": "❌ (sequentiell)",
    "meta-feedback": "❌ (atomar)",
    "agent-meta-manager": "❌ (atomar)",
    "agent-meta-scout": "✅ (Multi-Quellen)",
    "tester": "✅ (Multi-Suites)",
    "code-reviewer": "✅ (Multi-Prüfungen)",
    "docker": "❌ (sequentiell)",
    "log-analyzer": "✅ (Multi-Quellen)",
    "feedback": "❌ (atomar)",
    "bug-feature-analyzer": "✅ (Multi-Issues)",
    "effort-estimator": "❌ (sequentiell)",
    "se-requirements": "❌ (sequentiell)",
    "se-architect": "✅ (Multi-Systeme)",
    "se-critic": "✅ (Multi-Prüfungen)",
    "se-interface-mgr": "❌ (zentral)",
    "se-termination": "❌ (schnell)",
    "se-test-engineer": "✅ (Multi-Strategien)",
    "se-testreviewer": "✅ (Multi-Reviews)",
    "se-verifier": "✅ (Multi-Ebenen)",
    "se-validator": "❌ (sequentiell)",
    "se-integration-and-test-manager": "❌ (Meta-Orchestrator)",
    "ui-ux-designer": "✅ (Multi-Entwürfe)",
    "api-specialist": "❌ (sequentiell)",
    "devops-engineer": "✅ (Multi-Targets)",
    "performance-optimizer": "❌ (sequentiell)",
    "export-manager": "❌ (sequentiell)",
    "orchestrator": "❌ (Meta-Orchestrator)",
    "validator": "❌ (Abhängigkeiten)",
    "claude-expert": "❌ (sequentiell)",
    "gemini-expert": "❌ (sequentiell)",
    "opencode-expert": "❌ (sequentiell)",
    "continue-expert": "❌ (sequentiell)",
    "copilot-expert": "❌ (sequentiell)",
}


def generate_agent_delegation_table(agent_meta_root: Path, config: dict, variables: dict) -> str:
    """Generate the agent delegation table for the orchestrator template.

    Reads roles from config/role-defaults.yaml and generates a Markdown table.
    Respects workflow_tier, SE_ENABLED, and VALIDATOR_ENABLED flags.

    Tier rules:
      - required      → always included
      - recommended   → always included
      - optional      → only if present in config['roles']
    """
    roles_cfg = load_roles_config(agent_meta_root)
    roles = roles_cfg.get("roles", {})

    # If no roles key in project config, all optional roles are considered active.
    roles_list = config.get("roles")
    active_roles = set(roles_list) if roles_list is not None else None

    se_enabled = variables.get("SE_ENABLED", "false") == "true"
    validator_enabled = variables.get("VALIDATOR_ENABLED", "false") == "true"

    lines: list[str] = []
    for role_name in sorted(roles.keys()):
        # Skip SE roles if SE not enabled
        if role_name.startswith("se-") and not se_enabled:
            continue
        # Skip validator if not enabled
        if role_name == "validator" and not validator_enabled:
            continue

        role_info = roles[role_name]
        tier = role_info.get("workflow_tier", "optional")

        # Optional roles only appear when explicitly listed in config['roles']
        if tier == "optional" and active_roles is not None and role_name not in active_roles:
            continue

        description = role_info.get("description", "")
        parallel = _PARALLEL_LABELS.get(role_name, "✅ (Multi-Tasks)")
        model_tier = role_info.get("model", "") or "—"

        lines.append(f"| `{role_name}` | {description} | {model_tier} | {parallel} |")

    return "\n".join(lines)


def generate_intent_routing_table(agent_meta_root: Path, config: dict, variables: dict) -> str:
    """Generate Intent-Routing table from role configs.

    Reads roles from config/role-defaults.yaml and generates a Markdown table.
    Only roles with a `routing` block are included. Respects feature flags for
    SE_ENABLED, VALIDATOR_ENABLED, DEVELOPER_TIERS_ENABLED, EFFORT_ESTIMATOR_ENABLED
    and DOD_TESTS_REQUIRED.
    """
    roles_cfg = load_roles_config(agent_meta_root)
    roles = roles_cfg.get("roles", {})

    se_enabled = variables.get("SE_ENABLED", "false") == "true"
    validator_enabled = variables.get("VALIDATOR_ENABLED", "false") == "true"
    developer_tiers = variables.get("DEVELOPER_TIERS_ENABLED", "false") == "true"
    effort_estimator = variables.get("EFFORT_ESTIMATOR_ENABLED", "false") == "true"
    tests_required = variables.get("DOD_TESTS_REQUIRED", "false") == "true"

    lines = ["| Intent | Ziel | Tier | Parallel |", "|--------|------|------|----------|"]

    for role_name in sorted(roles.keys()):
        if role_name.startswith("se-") and not se_enabled:
            continue
        if role_name == "validator" and not validator_enabled:
            continue
        if role_name in ("junior-developer", "senior-developer") and not developer_tiers:
            continue
        if role_name == "effort-estimator" and not effort_estimator:
            continue
        if role_name == "tester" and not tests_required:
            continue

        role = roles[role_name]
        routing = role.get("routing")
        if not routing:
            continue  # skip roles without routing hints

        keywords = routing.get("intent_keywords", [role.get("description", role_name)])
        intent = " / ".join(keywords[:4])
        target = f"`{role_name}`"
        tier = role.get("model", "balanced") or "balanced"
        parallel = "Ja" if routing.get("parallel", True) else "Nein"

        lines.append(f"| {intent} | {target} | {tier} | {parallel} |")

    # Special non-role routing rows
    if se_enabled:
        lines.append("| SE-Kaskade | Pipeline `se-cascade` | balanced→powerful | Nein |")
    lines.append("| Reflection-Loop | self (REPEAT_UNTIL) | balanced→powerful | Nein |")

    # Fallback for unknown intents
    lines.append("| Nicht in Tabelle | User fragen | — | — |")

    return "\n".join(lines)
