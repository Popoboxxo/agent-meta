# Prompt Optimization Report: `_wf-skill-lifecycle.md`

## 1. Context & Objectives
**Target File:** `/home/dduchrow/Repos/agent-meta/agents/1-generic/_wf-skill-lifecycle.md`
**Objective:** Evaluate and streamline the workflow document based on the `prompt-engineer` best practices (OpenAI, Lakera, Context Engineering 2026), specifically focusing on token reduction, structural efficiency, and latency optimization.

## 2. Current State Analysis
- **Size:** 67 lines, ~1942 bytes.
- **Structure:** 7 separate sections for a single domain (External Skills Lifecycle).
- **Inefficiencies Found:**
  - **Redundancy:** The synchronization command (`py .agent-meta/scripts/sync.py --config .meta-config/project.yaml`) is repeated 3 times.
  - **Prose vs. Symbols:** Uses conversational elements and explicit phrasing instead of Chain-of-Symbol (CoS) or dense structures.
  - **Layout:** Spaced-out blocks and repetitive headers (e.g., 7.2 and 7.3 both modify the same config file and run the same sync command).
  
## 3. Optimization Proposals (Actionable Insights)

### 3.1 Instruction Referencing (Alias Pattern)
*Prompt-Engineer Best Practice (3.2 Template-Abstraktion)*
Define the frequently used sync command as a macro/alias at the top of the file to save tokens in every subsequent step.
**Action:** Extract `py .agent-meta/scripts/sync.py --config .meta-config/project.yaml` to a `> **CMD-SYNC:** ...` block at the top.

### 3.2 Chain-of-Symbol (CoS) & Structured Prompting
*Prompt-Engineer Best Practice (4.3 Latency Reduction & Generation Speed)*
Convert prose-heavy decision trees (like section 7.5) into compact symbol-driven lists. Use `->` and `|` instead of full sentences to reduce the parsing and reasoning overhead for the LLM.
**Action:** Rewrite section 7.5 into a minimal Key-Value mapping.

### 3.3 Consolidating Related Operations
*Prompt-Engineer Best Practice (3.1 Strukturiertes Prompting)*
Section 7.2 (Enable) and 7.3 (Disable) perform nearly identical steps with a different boolean flag. They should be merged to avoid duplicating the config path and sync instructions.
**Action:** Merge into "7.2/7.3 Enable/Disable Skill" with a single `true|false` toggle instruction.

### 3.4 Removing Formatting Overhead
Markdown code blocks (` ```bash `) are useful but consume extra tokens and lines. For sequential single-line commands, bullet points with inline code blocks are more token-efficient while still being perfectly parsed by LLMs.

## 4. Proposed Streamlined Version

```markdown
# External Skills — Lifecycle

> **CMD-SYNC:** `py .agent-meta/scripts/sync.py --config .meta-config/project.yaml`

## 7.1 Status
- `cat .agent-meta/config/skills-registry.yaml`
- `cat .meta-config/project.yaml` → Check `external-skills`
- **Matrix:** Skill | Approved | Projekt-Status | Repo@commit

## 7.2/7.3 Enable/Disable Skill
**Req:** `approved: true` in `skills-registry.yaml` (If `false` → delegate `meta-feedback`, label: `external-skill`).
1. **Check:** `ls .agent-meta/external/<repo>/` → If empty: `git submodule update --init --recursive`
2. **Toggle:** `.meta-config/project.yaml` → `external-skills.<name>.enabled: true|false`
3. **Apply:** Run CMD-SYNC. Ensure skill under `[WRITE]` in `sync.log`.

## 7.4 Add Repo
1. **Check:** `SKILL.md` present? Scope clear?
2. **Add:** `py .agent-meta/scripts/sync.py --add-skill <url> --skill-name <name> --source <path> --role <role>`
3. **Note:** Result is `approved: false` (requires manual review).

## 7.5 User Repo Proposal
- **Existing Submodule?** → Enable (7.2)
- **Highly Specific?**    → Add (7.4)
- **Rule/Ext Fit?**       → Inform User + delegate `meta-feedback`
- **Unclear?**            → Delegate `agent-meta-scout`

## 7.6 Update Submodules
- `git submodule update --init --recursive`
- `cd .agent-meta/external/<repo> && git pull && cd ../..`
- `git add .agent-meta/external/<repo>`
- Run CMD-SYNC.

## 7.7 Consistency Check
1. Submodule-Commit == `pinned_commit` (`git submodule status .agent-meta`)
2. `source` / `entry` / `additional_files` exist?
3. Orphaned repos, unregistered SKILL.md?
```

## 5. Resulting Metrics
- **New Size:** 33 lines (approx. 50% reduction in line count).
- **Token Efficiency:** The LLM's context window usage is significantly reduced by eliminating redundant paths and commands.
- **Latency:** Due to higher token density and CoS (`->`), reasoning tasks involving these steps will consume fewer tokens, leading to faster inference and response times.
