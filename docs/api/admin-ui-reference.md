# Admin UI & Function Reference

This document provides an exhaustive technical reference for every configuration option and function available within the **Agent Meta Manager**. It serves as the definitive Single Source of Truth for the framework's architecture and is dynamically injected into the Admin UI via the Help System.

---

## 1. Super Admin

### Workspace
<!-- help-id: super_admin-workspace -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
The Workspace configuration defines the absolute filesystem path where the Agent Meta framework is actively operating. This is critical because it establishes the execution context for all underlying Python scripts, Git operations, and agent file generation processes. If you are running the `admin-server.py` from within a parent repository that integrates `agent-meta` as a submodule, this path must point to the parent repository root. Incorrect workspace paths will result in agents being generated in the wrong directory or `sync.py` failing to find the `.meta-config/project.yaml` file.

### Dashboard
<!-- help-id: super_admin-dashboard -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
The Super Admin Dashboard is the central command center for the entire framework ecosystem. It provides immediate, high-level telemetry on the health of your agent configurations. Here you can monitor the total number of instantiated agent roles, quickly verify which project instance configuration is currently active, and check the timestamp of the last successful `sync.py` execution. It serves as a rapid diagnostic tool before diving into specific project or framework overrides.

### Viz Dashboard
<!-- help-id: super_admin-viz_dashboard -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
The Viz Dashboard is an advanced, interactive D3.js visualization suite that maps out your entire agent architecture. It visually represents the inheritance chain (how `3-project` agents override `1-generic` templates) and maps the complex web of delegation paths defined in the Orchestrator. Nodes in the graph can be clicked to reveal individual agent prompts and tools. This visual representation is invaluable for debugging circular dependencies or identifying "orphaned" agents that are never invoked by the Orchestrator.

### Sync
<!-- help-id: super_admin-sync -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
The Sync function is the beating heart of the framework. Triggering a Sync invokes the `scripts/sync.py` engine, which forcefully compiles all abstract templates into concrete Markdown files ready for LLM consumption. During this process, the engine resolves all PAL (Provider Abstraction Layer) variables, applies project-specific YAML overrides, and strictly validates input/output handoff contracts. This process must be run every time you modify a template, a rule, or a role default to ensure your IDE (like Continue or Copilot) is using the latest agent definitions.

### Live events
<!-- help-id: super_admin-live_events -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
The Live Events interface provides a real-time, WebSocket-driven telemetry stream of the framework's internal operations. It surfaces standard output (`stdout`) and error logs (`stderr`) directly from background tasks like the `sync.py` compiler and the Viz logger. When agents are actively running and making tool calls, their lifecycle events (spawn, tool execution, termination, handoff) are streamed here. This is your primary debugging console for diagnosing silent failures or infinite loops during agent execution.

---

## 2. Project instance

### General
<!-- help-id: project_instance-general -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
The General settings define the core identity and namespace of your current active project. Changing these settings ensures that generic agents behave as if they were custom-built exclusively for your specific codebase.

#### Field: Project name
<!-- help-id: field-project_name -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
**Project Name** defines the human-readable title of your application or repository. This exact string is injected into the context of every single agent's system prompt. For example, if set to "E-Commerce Backend", the developer agent will naturally structure code decisions around backend architecture rather than making assumptions.

#### Field: ID prefix
<!-- help-id: field-id_prefix -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
**ID Prefix** (e.g., `REQ-`, `BUG-`, `TASK-`) is highly critical. It strictly dictates how agents like the `requirements` or `feedback` agent format their output issue IDs. If you integrate with Jira and your project key is `SHOP`, you must set this field to `SHOP-` so all agent-generated artifacts match your ticketing system.

### Providers & Platforms
<!-- help-id: project_instance-providers -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
This critical configuration dictates which AI platforms (e.g., Claude Code, Continue, Gemini, GitHub Copilot) are active targets for generation in this project. You can enable multiple platforms simultaneously if your team uses a mixed IDE environment.

#### Field: Active platforms
<!-- help-id: field-active_platforms -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
Check the boxes for the IDE ecosystems you actively use. When you select a provider, the `sync.py` engine will automatically parse the `ai-providers` schema and generate the specific folder structure (e.g., `.claude/agents/` vs `.continue/prompts/`) required by that tool. Deselecting a platform will not delete existing files, it will only prevent future syncs from updating them.

### Provider Deactivation
<!-- help-id: project_instance-deactivation -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
Provider Deactivation allows you to cleanly "pause" an AI provider without permanently deleting its configuration. Reactivating a provider unzips the archive and seamlessly restores the exact previous state.

#### Field: Deactivate provider
<!-- help-id: field-deactivate_provider -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
Clicking this button automatically compresses the provider's active agent folders into a backup `.zip` archive and completely removes the `.md` files from your workspace. This drastically reduces IDE clutter and indexer overhead (e.g., preventing VSCode from scanning thousands of Markdown files) when you temporarily switch to another IDE.

### Backups
<!-- help-id: project_instance-backups -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
The Backups interface provides manual and automated snapshotting of your entire agent configuration state.

#### Field: Backup name
<!-- help-id: field-backup_name -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
Enter an optional label for your backup snapshot (e.g., `pre-orchestrator-refactor`). When you click 'Create Backup', a timestamped ZIP archive containing your `.meta-config/` and provider folders is generated. This acts as a localized version control system specifically for your AI setup, allowing instant rollbacks if an experimental prompt breaks your agents.

### Roles
<!-- help-id: project_instance-roles -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
The Roles panel is the most powerful customization tool for a project. It allows you to fundamentally alter the behavior of a `1-generic` agent without modifying the upstream source code.

#### Field: Role patch
<!-- help-id: field-role_patch -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
The Patch text area expects raw YAML syntax. Patches use a diff-like syntax (append, replace, delete) to surgically inject new Markdown instructions into specific sections of an agent's prompt. For example, you can `append` a paragraph to the `developer` agent's `## Constraints` section to force it to use specific libraries, creating a perfectly tailored `3-project` override.

#### Field: Role active
<!-- help-id: field-role_active -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
Toggle whether this specific sub-agent is active in your project. You can completely disable specific agents (e.g., turning off the `ui-ux-designer` for a purely backend API project). Disabled agents are structurally pruned from the Orchestrator's delegation graph during compilation.

### Orchestrator
<!-- help-id: project_instance-orchestrator -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
The Orchestrator is the apex agent (`orchestrator.md`) responsible for interpreting the user's initial prompt and dynamically delegating work to specialized sub-agents. These settings define its cognitive boundaries.

#### Field: Routing mode
<!-- help-id: field-routing_mode -->
<!-- last-updated: 2026-07-23 -->
<!-- author: Agent Meta Admin -->
Selects the Orchestrator's routing behavior (`orchestrator.mode` in `project.yaml`). `strict` (default) makes the orchestrator mandatory — every dev task is routed through it, no user override. `advisory` still recommends the orchestrator but allows the user to bypass it. `main-chat` removes the orchestrator subagent entirely — the main chat acts as router and worker itself. This field takes precedence over the deprecated `enabled`/`strict` booleans; if left unset, `sync.py` derives it from those legacy fields (`enabled=true` + `strict=true` → `strict`), which matches the framework default.

#### Field: Maximum delegation depth
<!-- help-id: field-maximum_delegation_depth -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
This integer value restricts how deep the sub-agent chain can go (e.g., Orchestrator -> Developer -> Tester -> BugFixer = Depth 3). This is an essential failsafe to prevent infinite looping sub-agents and runaway API costs. A standard setting is 3.

#### Field: Execution mode
<!-- help-id: field-execution_mode -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
Defines whether the Orchestrator runs sub-agents `synchronously` (one after another, blocking) or `asynchronously` (spawning multiple agents in parallel). Asynchronous mode drastically speeds up tasks like multi-file code reviews, but requires an IDE that natively supports parallel sub-agent threading (like Continue).

#### Field: Fallback strategy
<!-- help-id: field-fallback_strategy -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
Defines what the Orchestrator should do if a user requests a task but no specialized sub-agent is available (or they are all disabled). `graceful_decline` forces the Orchestrator to reject the task. `generic_attempt` allows the Orchestrator to try and solve the problem itself using its baseline coding tools.

### Viz & Admin
<!-- help-id: project_instance-viz_admin -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
These settings govern the technical behavior of the local web servers powering the Admin UI and the D3.js visualization graph.

#### Field: TCP port
<!-- help-id: field-tcp_port -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
The port the Admin Server binds to (default: `7420`). Modify this if you experience port conflicts with other local dev servers. If you are running the agent-meta framework inside a Docker container, ensure this port is mapped to your host machine.

#### Field: Hot reload
<!-- help-id: field-hot_reload -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
When enabled, the D3.js Viz Dashboard will establish a WebSocket connection and automatically re-render the agent graph the moment a `sync.py` compilation completes, providing immediate visual feedback on architectural changes.

### Provider Tier Overrides
<!-- help-id: project_instance-tier_overrides -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
The framework uses abstract intelligence tiers (`nano`, `fast`, `balanced`, `powerful`, `max`). This section allows you to override the *global* mapping of these tiers for your specific project.

#### Field: Tier mapping
<!-- help-id: field-tier_mapping -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
Select a specific, concrete model string (e.g., `claude-3-haiku-20240307`) to replace the default model for a given tier. If your project requires maximum speed across all "fast" tasks, mapping the `fast` tier to a smaller model allows for massive, project-wide performance shifts without editing dozens of individual agent templates.

### DoD Overrides
<!-- help-id: project_instance-dod_overrides -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
The "Definition of Done" (DoD) consists of strict criteria an agent must fulfill before concluding its task.

#### Field: DoD requirement
<!-- help-id: field-dod_requirement -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
A text input where you define custom success criteria. For example, you can enforce that every developer agent in this project must "ensure 100% unit test coverage" and "update the CHANGELOG.md". These overrides are physically appended to the end of the agent's instructions during the sync process.

---

## 3. Framework defaults

### Models & Pricing
<!-- help-id: framework_defaults-models -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
This is the foundational database of all known LLM models supported by the framework.

#### Field: Cost per 1m tokens
<!-- help-id: field-cost_per_1m_tokens -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
The exact monetary cost for 1 million input or output tokens for a given model. The Orchestrator agent reads this database at runtime to perform cost-benefit analysis, allowing it to dynamically route simple tasks to cheap models and complex tasks to expensive models. Keeping this updated optimizes your API burn rate.

### role-defaults
<!-- help-id: framework_defaults-role_defaults -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
The `role-defaults.yaml` is the DNA sequence of the agent ecosystem. It strictly defines every valid agent that can exist in the system.

#### Field: Minimum tier
<!-- help-id: field-minimum_tier -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
Enforces the lowest cognitive tier (e.g., `fast`, `balanced`, `powerful`) an agent requires to function correctly. The `tester` agent might only require `fast`, while the `senior-developer` requires `powerful`. The Orchestrator uses this minimum baseline when mapping tasks to models.

#### Field: Input contracts
<!-- help-id: field-input_contracts -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
Defines exactly what JSON schemas, variables, or data formats an agent expects to receive before it can start working. This guarantees type-safe handoffs between autonomous agents, preventing errors where Agent A passes unstructured text to Agent B who expects a JSON array.

### export
<!-- help-id: framework_defaults-export -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
The Export configuration governs the automated routing of structured data produced by agents.

#### Field: Export target
<!-- help-id: field-export_target -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
Defines where the artifact produced by an agent should be sent. Options typically include `file` (append to a local Markdown document), `github-issue` (execute the GitHub CLI to create an issue), or `webhook` (POST the JSON payload to an external server). This seamlessly integrates agent outputs into human workflows.

### Model Overrides
<!-- help-id: project_instance-model_overrides -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
Model Overrides allow you to surgically assign a specific, concrete LLM model string (e.g., `claude-3-opus-20240229` or `gemini-1.5-pro`) to a specific agent role, completely bypassing the abstract Tier mapping system.

### Model Mapping
<!-- help-id: project_instance-model_mapping -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
The Model Mapping matrix is a detailed translation layer that bridges the gap between abstract intelligence Tiers and concrete API model strings across different providers.

### Rules Overrides
<!-- help-id: project_instance-rules_overrides -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
Rules are global architectural constraints. This interface allows you to inject project-specific rules that supplement or replace the framework defaults.

### Conventions Overrides
<!-- help-id: project_instance-conventions_overrides -->
<!-- last-updated: 2026-08-18 -->
<!-- author: Agent Meta Admin -->
Naming and versioning conventions (release versioning/changelog, issue naming) resolved from the selected conventions-preset. This view lets you override individual convention fields per domain on top of the preset. Precedence: convention override > conventions-preset > default. List overrides replace the whole preset list (deep-merge semantics).

### Platform Defaults
<!-- help-id: project_instance-platform_defaults -->
<!-- last-updated: 2026-08-25 -->
<!-- author: Agent Meta Admin -->
Compare/resolve view for the project.yaml defaults contributed by the active platform layers (`platforms:`). Rather than editing values directly, each key is shown with its platform default, active value and status (inherited / overridden / ignored) plus per-status actions: adopt (hand control back to the platform), ignore (pin the current value) and re-track (re-enable drift comparison). Precedence: project-explicit > platform-default > framework-default. Actions apply immediately server-side — there is no batched save.

### Advanced
<!-- help-id: project_instance-advanced -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
The Advanced view provides a raw text editor directly exposing the `.meta-config/project.yaml` file. Changes saved here bypass UI validation.

### Knowledge Engine
<!-- help-id: project_instance-knowledge_engine -->
<!-- last-updated: 2026-07-24 -->
<!-- author: Agent Meta Admin -->
The Knowledge Engine view configures the opt-in knowledge-base bundle for this project. A preset selector applies domain-specific defaults for research, personal, business, book or internal-docs domains (or custom), and five panels let you fine-tune sources, the OKF frontmatter schema, ingest/query/lint operations, migration safety settings, and search behavior.

### Skills
<!-- help-id: framework_defaults-skills -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
Skills are modular, reusable capability blocks (like 'Web Search', 'Database Query') that can be dynamically attached to agents.

### Platform Defaults
<!-- help-id: framework_defaults-platform_defaults -->
<!-- last-updated: 2026-08-25 -->
<!-- author: Agent Meta Admin -->
Raw editor for `config/platform-defaults.yaml`, which lets a platform (activated per project via `platforms:`) supply default values for arbitrary project.yaml keys. Scalar keys follow project-explicit > platform-default > framework-default; list keys (roles, mcp-servers, …) merge additively across all active platforms. This is not a fifth preset system — it fills the selectors of the existing preset systems plus any other key, never their internal per-field override blocks. The file starts empty (`platforms: {}`); populating a platform is a deliberate follow-up step.

### Delegation
<!-- help-id: framework_defaults-delegation -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
The Delegation syntax defines how the abstract intent of "Agent A talking to Agent B" is physically translated into provider-specific syntax (e.g. resolving `{{PAL_DELEGATE}}`).

### MCP Registry
<!-- help-id: framework_defaults-mcp_registry -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
The Model Context Protocol (MCP) registry configures external data connections like Slack, Jira, or internal databases.

### Rules Presets
<!-- help-id: framework_defaults-rules_presets -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
Rules Presets bundle collections of architectural and coding standards. These global presets are injected into the agent context.

### Conventions Presets
<!-- help-id: framework_defaults-conventions_presets -->
<!-- last-updated: 2026-08-18 -->
<!-- author: Agent Meta Admin -->
Conventions Presets define naming and versioning conventions per domain (release versioning/changelog, issue naming). Each preset feeds the `RELEASE_VERSIONING_BLOCK`, `RELEASE_CHANGELOG_BLOCK` and `GIT_ISSUE_NAMING_BLOCK` placeholders in the release/git agent templates. Projects select one via `conventions-preset` and refine it with a `conventions:` override block.

### Provider Tier Mappings
<!-- help-id: framework_defaults-tier_mappings -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
This defines the *global* baseline for the abstraction layer. If a project does not explicitly override a tier, this table dictates the fallback model.

### Tier Presets
<!-- help-id: framework_defaults-tier_presets -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
Tier Presets are convenient, pre-configured bundles of Provider Tier Mappings. Allows you to rapidly shift the entire cognitive power profile of the framework.

### DoD Presets
<!-- help-id: framework_defaults-dod_presets -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
This defines the global templates for "Definition of Done" criteria. Presets provide standardized quality gates.

### AI Providers
<!-- help-id: framework_defaults-ai_providers -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
This schema maps out the diverse directory structures, file extensions, and syntax requirements of different AI IDE plugins.

### Agent Templates
<!-- help-id: workflows-agent_templates -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
Agent Templates are the raw, foundational Markdown files (`1-generic`) from which all concrete agents are born.

### Reflection Pairs
<!-- help-id: workflows-reflection_pairs -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
Reflection Pairs configure dynamic, adversarial critique loops. Defines the pairing rules between a protagonist and an antagonist agent.

### Config Audit
<!-- help-id: workflows-config_audit -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
The Config Audit is a vital diagnostic scanner that cross-references your current `.meta-config/project.yaml` against strict schemas.

### Roles Graph
<!-- help-id: workflows-roles_graph -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
The Roles & Graph configuration defines the strict, static dependency tree of agent communication.

### Pipelines
<!-- help-id: workflows-pipelines -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
Pipelines define rigid, linear sequences of agent execution designed for standardized, repetitive processes.

### Consistency Check
<!-- help-id: workflows-consistency_check -->
<!-- last-updated: 2026-07-19 -->
<!-- author: Agent Meta Admin -->
The Consistency Check is a powerful architectural validation tool. It executes the core `consistency-check.py` script to rigorously scan the entire framework for discrepancies. It verifies that all CLI arguments are documented, that UI routes match their help blocks, that the README.md is up-to-date, and that the XML structures are strictly maintained. Always run this check before committing changes to ensure the framework's integrity.
