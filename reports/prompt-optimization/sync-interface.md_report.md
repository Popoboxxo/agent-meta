# Prompt-Engineer Evaluation Report: `_wf-sync-interface.md`

## 1. Current State
- **File:** `agents/1-generic/_wf-sync-interface.md`
- **Purpose:** Reference documentation for the `sync.py` CLI and underlying Python module structure.
- **Size:** 58 lines, ~2.5 KB.
- **Structure:** Uses standard Markdown headings, code blocks with inline comments, and a Markdown table.

## 2. Findings (Token Bloat & Latency Impact)
As a `prompt-engineer`, I evaluated the file based on the Agent-Meta Framework guidelines and Context Engineering best practices (e.g., Structured Prompting, Verbosity Control).
- **Redundancy & Verbosity:** German prose like "Sucht in dieser Reihenfolge (wenn `--config` weggelassen):" or "sync.py selbst ist nur argparse..." is unnecessary for LLM comprehension. LLMs prefer dense, telegraphic syntax.
- **Markdown Table Overhead:** The table for Python modules (`| Modul | Zuständigkeit | ...`) consumes excess tokens for structural formatting characters (`|`, `-`). A dense key-value list is significantly more token-efficient while maintaining perfect readability for LLMs.
- **Visual Alignment in Code Blocks:** Whitespace used to align inline comments (e.g., in the `sync.log` and `Flags` sections) costs extra tokens without adding any semantic value. Models process tokens linearly; visual alignment is for humans only.
- **Actionable Call-outs:** Instructions like "Warnungen sofort beheben" can be integrated directly into the semantic item (e.g., `[WARN] -> FIX IMMEDIATELY`) to reduce separate sentences.

## 3. Specific Optimization Proposals (Actionable Insights)

### Proposal A: Dense Key-Value Structure over Tables
Replace the Markdown table in the Python module section with a simple bulleted list. LLMs parse `agents.py: parse frontmatter, composition, sync` just as efficiently as a formatted table, but at a fraction of the token cost.

### Proposal B: Eliminate Whitespace Alignment
Remove the multi-space alignments in the code blocks. 
*Current:* `py scripts/sync.py                        # Standard-Sync`
*Optimized:* `py scripts/sync.py # Standard-Sync`

### Proposal C: Telegraphic Syntax
Convert conversational sentences to imperative, telegraphic commands to improve generation speed and lower context size.
- *Current:* `Sucht in dieser Reihenfolge (wenn --config weggelassen):`
- *Optimized:* `Config Fallback (if no --config):`
- *Current:* `sync.py selbst ist nur argparse + main-Dispatcher. Bei Änderungen: erst zuständiges lib/-Modul lesen.`
- *Optimized:* `sync.py is only argparse/dispatcher. For logic changes, edit lib/ modules.`

### Proposal D: Streamlined Log Section
Condense the log explanation into a tight, implicit mapping block without arrows or extra descriptions.

## 4. Proposed Refactored Content (Drop-in Replacement)

```markdown
# sync.py Reference

## Config Fallback (if no `--config`)
1. `.meta-config/project.yaml`
2. `agent-meta.config.yaml` (Legacy)
3. `agent-meta.config.json` (Legacy)

## CLI Flags
`py scripts/sync.py` # Standard sync
`py scripts/sync.py --init` # Setup (CLAUDE.md, settings.json, gitignore)
`py scripts/sync.py --dry-run` # Preview changes
`py scripts/sync.py --only-variables` # Replace {{VAR}} only
`py scripts/sync.py --create-ext <role|all>` # Create extension(s)
`py scripts/sync.py --update-ext` # Update managed blocks
`py scripts/sync.py --create-rule <name>` # Create project rule
`py scripts/sync.py --add-skill <url> --skill-name <n> --source <path> --role <r>`
`py scripts/sync.py --fill-defaults` # Inject missing project.yaml fields

## sync.log
[WRITE] target (Generated)
[COPY] target (Copied)
[SKIP] target (Inactive role)
[UPDATE] target (Managed block)
[DELETE] target (Stale removed)
[WARN] msg -> FIX IMMEDIATELY
[INFO] msg

## Architecture (scripts/lib/)
sync.py = argparse + dispatcher. Edit `lib/` modules for logic:
- `agents.py`: Frontmatter, composition (extends/patches), sync_agents
- `config.py`: load_config, build_variables, substitute, fill_defaults
- `context.py`: init_claude_md, sync_context, gitignore
- `dod.py`: load_dod_presets, resolve_dod
- `extensions.py`: create_extension, update_extensions
- `hooks.py`: sync_hooks, create_hook
- `io.py`: YAML/JSON loader
- `log.py`: SyncLog
- `platform.py`: load_platform_config, substitute_platform
- `providers.py`: load_providers_config, resolve_providers
- `roles.py`: load_roles_config, build_role_map, resolver
- `rules.py`: sync_rules, sync_speech_mode, create_rule
- `skills.py`: External skills load, check_pinned, sync, add
```
