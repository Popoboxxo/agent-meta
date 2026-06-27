# Prompt-Optimization Report: `_wf-git-ops.md`

## 1. Current State & Findings
- **Target File:** `agents/1-generic/_wf-git-ops.md`
- **Size:** 84 lines, ~2032 bytes.
- **Analysis:** The file is heavily structured with verbose bash examples. While clear and readable for a human, LLMs already possess strong inherent knowledge of standard Git operations. Providing multi-line bash scripts for basic operations (`git checkout -b`, `git tag`) consumes unnecessary tokens and slows down context processing. The tabular presentation of destructive operations also adds unnecessary markdown formatting overhead.

## 2. Optimization Goals (Verschlankung)
Based on the `prompt-engineer.md` best practices:
- **Prompt Compression (Token Reduction):** Compress verbose bash blocks into inline or chained commands.
- **Structured Prompting:** Convert the markdown table into a compact, comma-separated list to save markdown tokens.
- **Relevance Filtering & Verbosity Control:** Remove verbose explanation texts and empty lines where the command itself is self-explanatory to an LLM.

## 3. Specific Optimization Proposals

### Proposal A: Compress Workflow Reference (W1-W7)
Instead of multi-line bash blocks for every workflow, use single-line chained commands or minimal representations. LLMs understand shorthand perfectly.

**Current (W2 Feature-Branch, 8 lines):**
```bash
git checkout -b feat/REQ-042-kurzbeschreibung
# ... commits ...
git checkout {{GIT_MAIN_BRANCH}} && git pull
git merge --no-ff feat/REQ-042-kurzbeschreibung
git push origin {{GIT_MAIN_BRANCH}}
git branch -d feat/REQ-042-kurzbeschreibung
```

**Proposed (1-2 lines):**
```bash
# W2 Feature-Branch:
git checkout -b feat/REQ-<id>-<desc> && ... && git checkout {{GIT_MAIN_BRANCH}} && git pull && git merge --no-ff feat/... && git push origin {{GIT_MAIN_BRANCH}} && git branch -d feat/...
```
*Alternative (Semantic Shorthand):* `W2 Feature: checkout -b feat/REQ... -> commit -> checkout {{GIT_MAIN_BRANCH}} -> pull -> merge --no-ff -> push -> branch -d`

### Proposal B: Minimize Destructive Operations Table
Markdown tables are token-heavy due to alignment and pipes. Convert to a dense string/list.

**Current (6 lines of table overhead):**
```markdown
| Kommando | Risiko | Alternative |
|----------|--------|-------------|
| `git reset --hard` | Verliert changes | `git stash` |
...
```

**Proposed (1 line):**
`⚠️ Destructive (Verify First): reset --hard (prefer stash), push --force (prefer --force-with-lease), branch -D (prefer -d), clean -fd (run -nd first).`

### Proposal C: Condense Platform Hints
Group platform CLIs tighter without dedicated code blocks for each.

**Proposed:**
```markdown
## Platforms
- **GitHub:** `gh auth status`, `gh issue list [--label bug]`, `gh issue view <id>`, `gh pr create --title "..." --body "Closes #<id>"`
- **GitLab:** `glab mr create` (Auth: `git remote set-url origin https://oauth2:<TOKEN>@gitlab.com/...`)
- **Gitea:** Same as GitHub (`.netrc` auth)
```

### Proposal D: Combine Submodule Updates
**Proposed:**
```bash
# Submodules (agent-meta)
git submodule update --init --recursive && cd .agent-meta && git checkout v<version> && cd .. && git commit -am "chore: upgrade agent-meta"
```

## 4. Expected Impact
- **Token Savings:** Estimated 30-40% reduction in tokens by removing Markdown formatting overhead and collapsing newlines.
- **Latency:** Faster prompt processing time and lower inference costs due to reduced context window footprint.
- **Reliability:** No loss in instruction clarity. Utilizing symbols (`->`) and chained commands (`&&`) aligns with the "Chain-of-Symbol" context engineering best practice, keeping the "reasoning buffer" small and fast.
