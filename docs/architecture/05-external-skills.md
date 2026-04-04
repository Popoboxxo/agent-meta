# External Skills Integration

> [Back to Architecture Overview](../../ARCHITECTURE.md)

```mermaid
flowchart LR
    subgraph sub [Git Submodule]
        NLP[neat-little-package]
    end

    subgraph cfg [external-skills.config.json]
        S1[home-organization enabled false]
        S2[opengrid-openscad enabled false]
    end

    subgraph meta [agent-meta]
        WR[skill-wrapper template]
    end

    subgraph out [target project .claude]
        AG[agents/opengrid-designer.md]
        SK[skills/opengrid-openscad/]
    end

    NLP --> S2
    S2 -->|enabled true + sync| WR
    WR -->|substitutes SKILL content| AG
    S2 -->|COPY| SK
```
