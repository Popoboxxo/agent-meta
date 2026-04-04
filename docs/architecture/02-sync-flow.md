# Sync Flow

> [Back to Architecture Overview](../../ARCHITECTURE.md)

flowchart TD
    CFG[agent-meta.config.json]
    ECFG[external-skills.config.json]
    SYNC[sync.py]

    subgraph sources [agent-meta]
        G1[1-generic agents]
        G2[2-platform agents]
        SN[snippets]
        EX[external SKILL.md]
        WR[skill-wrapper template]
    end

    subgraph target [.claude/ in target project]
        AG[agents generated]
        SK[skills copied]
        SNC[snippets copied]
        EXT[3-project ext created once]
    end

    CFG --> SYNC
    ECFG --> SYNC
    G1 --> SYNC
    G2 --> SYNC
    SN --> SYNC
    EX --> SYNC
    WR --> SYNC

    SYNC -->|WRITE| AG
    SYNC -->|COPY| SNC
    SYNC -->|COPY| SK
    SYNC -->|CREATE| EXT
```
