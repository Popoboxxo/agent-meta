---
description: Add an AI provider to this project or request a new one via GitHub issue
allowed-tools: ["Bash", "Read", "Edit", "Agent"]
argument-hint: "[provider name, e.g. Gemini]"
---

Add an AI provider to this project. $ARGUMENTS

**Step 1 — Discover available providers**

Read `.agent-meta/config/ai-providers.yaml` and extract all provider names listed under `providers:`.
Read `.meta-config/project.yaml` and extract the `ai-providers:` list (currently active providers).

Show the user:
- Already active providers (skip these)
- Available providers from the registry (can be added immediately)

**Step 2 — User decision**

If $ARGUMENTS names a known provider from the registry → proceed to Step 3.
If $ARGUMENTS names an unknown provider (not in registry) → proceed to Step 4.
If no $ARGUMENTS → ask the user which provider they want to add, showing the available list.

**Step 3 — Add known provider**

1. Add the provider name to `ai-providers:` in `.meta-config/project.yaml`
2. Run sync: `python .agent-meta/scripts/sync.py`
3. Check sync output for warnings
4. Report: which new files were generated (agents, rules, settings, isolation artifacts)
5. If the provider requires secrets (e.g. API keys): show the relevant gitignored local config file path and what needs to be filled in

**Step 4 — Request new provider via GitHub issue**

The requested provider is not yet in the agent-meta registry. Before filing the issue, do a brief pre-analysis:

- What is the provider's name and tool/CLI name?
- Does it have a known agents directory convention?
- Does it support rules/hooks/commands natively?
- Does it have a known permission/deny mechanism for file access?
- What model IDs does it use?

Then delegate to the `meta-feedback` agent with this task:

File a GitHub issue titled: "feat: add [ProviderName] as a supported AI provider"

Body should include:
- Provider name and CLI/tool name
- Pre-analysis findings from above
- Links to official docs if known
- Requested capabilities: agents_dir, context_file, has_rules, has_hooks, has_settings, model-tiers
- Label: "enhancement", "new-provider"
