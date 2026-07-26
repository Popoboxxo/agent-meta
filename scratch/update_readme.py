import re
from pathlib import Path

readme_path = Path("c:/Repositories/agent-meta/README.md")
content = readme_path.read_text(encoding="utf-8")

# 1. Bump version and date
content = re.sub(r"version-0\.84\.0-blue", "version-0.85.0-blue", content)
content = re.sub(r"\*\*Date:\*\* 2026-07-18", "**Date:** 2026-07-26", content)

# 2. Add Architecture diagram after Quick Start / intro
diagram = """
> Supports 6 AI providers: Claude Code, Gemini, Opencode, Continue, GitHub Copilot, Mammouth Code.

## Architecture

```mermaid
graph TD
    subgraph Agent Meta Submodule
        A[agent-meta/1-generic]
        B[agent-meta/2-platform]
        C[agent-meta/0-external]
    end
    
    D[.meta-config/project.yaml] --> S(sync.py)
    A --> S
    B --> S
    C --> S
    
    S -->|Scaffolds| K[Knowledge Engine Bundle]
    S -->|Generates Agents| P1[.claude/agents]
    S -->|Generates Agents| P2[.gemini/agents]
    S -->|Generates Agents| P3[.opencode/agents]
```
"""
content = re.sub(
    r"> Supports 6 AI providers: Claude Code, Gemini, Opencode, Continue, GitHub Copilot, Mammouth Code.",
    diagram,
    content
)

# 3. Update generic agent count
content = re.sub(r"Agent Roster — 44 Generic Agents", "Agent Roster — 51 Generic Agents", content)

# 4. Insert Knowledge Engine section before "Provider Expert Agents"
ke_agents = """
### Knowledge Engine (7 agents)

| Agent | Tier | Version | Description |
|-------|------|---------|-------------|
| **knowledge-curator** | balanced | 1.0.0 | Strategic Knowledge Engine control: schema evolution, domain adaptation |
| **knowledge-gardener** | fast | 1.0.0 | Small-scale wiki maintenance: repair links, harmonize tags |
| **knowledge-indexer** | fast | 1.0.0 | Maintains index.md (content catalog) and log.md (event log) |
| **knowledge-ingestor** | powerful | 1.0.0 | Ingests sources, extracts key info, creates/updates wiki pages |
| **knowledge-linter** | balanced | 1.0.0 | Wiki health check: contradictions, orphans, stale claims, broken links |
| **knowledge-migrator** | balanced | 1.0.0 | Cleans up and migrates existing project content into the OKF Wiki |
| **knowledge-querier** | fast | 1.0.0 | Answers questions against the Knowledge Wiki |

### Provider Expert Agents (5 agents)"""

content = re.sub(r"### Provider Expert Agents \(5 agents\)", ke_agents, content)

readme_path.write_text(content, encoding="utf-8")
print("README updated successfully.")
