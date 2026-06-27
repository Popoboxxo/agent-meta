# Evaluation Report: `_wf-upgrade.md`

## 1. Current State
The file `_wf-upgrade.md` contains a 9-step workflow to upgrade the `agent-meta` framework. The current content is structured inside a markdown code block (` ``` `), with prose descriptions and raw bash commands separated across multiple lines.

**Token- & Structure Issues:**
- **Code Block Abuse:** Using a code block for the entire list disables proper markdown parsing, reducing the LLM's ability to efficiently parse the structure.
- **Redundancy:** The command `python .agent-meta/scripts/sync.py --config .meta-config/project.yaml` is repeated three times across steps 5, 7, and 8.
- **Prose Overhead:** Conversational step descriptions (e.g., "1. Version prüfen:", "2. CHANGELOG lesen (Breaking Changes?):") cost tokens without adding technical value.
- **Directory Hopping:** `cd .agent-meta && ... && cd ..` is repeated.

## 2. Evaluation against `prompt-engineer.md` Best Practices

- **Structured Prompting (3.1):** The list is somewhat structured but trapped in a code block. Converting this to a native Markdown list with bold labels and inline code improves LLM parsing efficiency and reduces tokens.
- **Relevance Filtering & Verbosity Control (3.3 & 3.4):** Explanatory prose like "neue Warnungen = fehlende Variablen" can be shortened using Chain-of-Symbol (`->`).
- **Chain-of-Symbol (CoS) (4.3):** Transitions between actions and expected outcomes can be replaced with `->` to keep the context window small.

## 3. Specific Optimization Proposals

### Proposal A: Direct Markdown Formatting (Token Reduction)
Remove the outer ` ``` ` block. Format the workflow as a dense Markdown list.

### Proposal B: Command Concatenation & Abstraction
Combine related commands. For example, steps 1 & 2 can be merged into a single "Pre-Check" step. Steps 7 & 8 can be merged by noting the flags.

### Proposal C: Chain-of-Symbol Integration
Replace prose with symbols.
*Instead of:*
`sync.log: neue Warnungen = fehlende Variablen`
*Use:*
`Check sync.log -> add missing vars from project.yaml.example`

## 4. Optimized Version (Actionable Insight)

Replace the current contents of `_wf-upgrade.md` with the following optimized version:

```markdown
# Workflow: Upgrade agent-meta

1. **Check**: `cat .agent-meta/VERSION .meta-config/project.yaml` -> `cd .agent-meta && git fetch && git log --oneline HEAD..v<neu> && cat CHANGELOG.md`
2. **Update**: `cd .agent-meta && git checkout v<neu>` -> Set `agent-meta-version` in `.meta-config/project.yaml`
3. **Dry-Run**: `python .agent-meta/scripts/sync.py --config .meta-config/project.yaml --dry-run` -> Fix missing vars via `.agent-meta/howto/project.yaml.example`
4. **Sync**: Run `python .agent-meta/scripts/sync.py --config .meta-config/project.yaml`, then run again with `--update-ext`
5. **Commit**: `chore: upgrade agent-meta to v<neu>` (Include: `.claude/agents/`, `{{EXTENSION_DIR}}/`, `.agent-meta`, `.meta-config/project.yaml`)
```

**Results:**
- **Token Reduction:** Reduces overall length and removes redundant words.
- **Latency Optimization:** The LLM will read and generate references to this workflow faster due to higher information density.
- **Framework Compliance:** Retains all necessary steps for the `agent-meta` framework upgrade without losing functionality.
