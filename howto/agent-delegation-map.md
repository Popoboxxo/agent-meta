# Agent Delegation Map

Übersicht aller Agent-zu-Agent-Verweise im Framework.
Zeigt wer an wen delegiert (→) und wer an wen verweist (↗).

---

## Delegations-Matrix

| Agent | Delegiert an (→) | Verweist auf (↗) |
|-------|-------------------|-------------------|
| **orchestrator** | `ideation`, `requirements`, `developer`, `tester`, `validator`, `documenter`, `docker`, `git`, `agent-meta-scout`, `agent-meta-manager`, `meta-feedback` | — |
| **feature** | `git`, `requirements`, `tester`, `developer`, `validator`, `documenter` | — |
| **developer** | — | `requirements`, `tester`, `documenter`, `validator` |
| **tester** | — | `requirements`, `developer`, `documenter`, `validator` |
| **validator** | — | `developer`, `tester`, `requirements`, `documenter` |
| **documenter** | — | `developer`, `tester`, `requirements`, `validator` |
| **git** | — | `developer`, `tester`, `release`, `documenter` |
| **release** | — | `tester`, `validator`, `documenter`, `git` |
| **docker** | — | `developer`, `release`, `tester` |
| **ideation** | `requirements` | — |
| **agent-meta-manager** | `meta-feedback`, `agent-meta-scout` | — |
| **meta-feedback** | — | — |
| **agent-meta-scout** | — | `requirements`, `agent-meta-manager`, `meta-feedback` |
| **security-auditor** | — | `developer`, `tester`, `validator`, `requirements` |
| **requirements** | — | `developer`, `tester`, `documenter` |

**Legende:**
- **Delegiert an (→):** Startet den Ziel-Agenten aktiv via Agent-Tool
- **Verweist auf (↗):** Empfiehlt dem User, an diesen Agenten zu wechseln (keine direkte Delegation)

---

## Delegations-Graph (Mermaid)

```mermaid
graph TD
    subgraph "Koordinatoren (delegieren aktiv)"
        ORCH[orchestrator]
        FEAT[feature]
    end

    subgraph "Spezialisten (verweisen nur)"
        DEV[developer]
        TEST[tester]
        VAL[validator]
        DOC[documenter]
        GIT[git]
        REL[release]
        DOCK[docker]
        REQ[requirements]
        IDEA[ideation]
        SEC[security-auditor]
    end

    subgraph "Meta-Agenten"
        MGR[agent-meta-manager]
        FB[meta-feedback]
        SCOUT[agent-meta-scout]
    end

    %% Orchestrator delegiert
    ORCH -->|delegiert| IDEA
    ORCH -->|delegiert| REQ
    ORCH -->|delegiert| DEV
    ORCH -->|delegiert| TEST
    ORCH -->|delegiert| VAL
    ORCH -->|delegiert| DOC
    ORCH -->|delegiert| DOCK
    ORCH -->|delegiert| GIT
    ORCH -->|delegiert| SCOUT
    ORCH -->|delegiert| MGR
    ORCH -->|delegiert| FB

    %% Feature delegiert
    FEAT -->|delegiert| GIT
    FEAT -->|delegiert| REQ
    FEAT -->|delegiert| TEST
    FEAT -->|delegiert| DEV
    FEAT -->|delegiert| VAL
    FEAT -->|delegiert| DOC

    %% Ideation delegiert
    IDEA -->|delegiert| REQ

    %% Manager delegiert
    MGR -->|delegiert| FB
    MGR -->|delegiert| SCOUT

    %% Verweise (gestrichelt)
    DEV -.->|verweist| REQ
    DEV -.->|verweist| TEST
    DEV -.->|verweist| DOC
    DEV -.->|verweist| VAL

    TEST -.->|verweist| REQ
    TEST -.->|verweist| DEV
    TEST -.->|verweist| DOC
    TEST -.->|verweist| VAL

    VAL -.->|verweist| DEV
    VAL -.->|verweist| TEST
    VAL -.->|verweist| REQ
    VAL -.->|verweist| DOC

    DOC -.->|verweist| DEV
    DOC -.->|verweist| TEST
    DOC -.->|verweist| REQ
    DOC -.->|verweist| VAL

    GIT -.->|verweist| DEV
    GIT -.->|verweist| TEST
    GIT -.->|verweist| REL
    GIT -.->|verweist| DOC

    REL -.->|verweist| TEST
    REL -.->|verweist| VAL
    REL -.->|verweist| DOC
    REL -.->|verweist| GIT

    DOCK -.->|verweist| DEV
    DOCK -.->|verweist| REL
    DOCK -.->|verweist| TEST

    SEC -.->|verweist| DEV
    SEC -.->|verweist| TEST
    SEC -.->|verweist| VAL
    SEC -.->|verweist| REQ

    REQ -.->|verweist| DEV
    REQ -.->|verweist| TEST
    REQ -.->|verweist| DOC

    SCOUT -.->|verweist| REQ
    SCOUT -.->|verweist| MGR
    SCOUT -.->|verweist| FB
```

---

## Rollen-Kategorien

### Koordinatoren (haben Agent-Tool, delegieren aktiv)

| Rolle | Tools | Delegiert an |
|-------|-------|-------------|
| `orchestrator` | Agent, Bash, Read, Write, Edit, ... | 11 Rollen |
| `feature` | Agent, Bash, Read | 6 Rollen |
| `agent-meta-manager` | Agent, Bash, Read, Write, Edit, ... | 2 Rollen |
| `ideation` | Agent (nur für requirements-Übergabe) | 1 Rolle |

### Spezialisten (kein Agent-Tool, verweisen nur)

| Rolle | Verweist auf |
|-------|-------------|
| `developer` | requirements, tester, documenter, validator |
| `tester` | requirements, developer, documenter, validator |
| `validator` | developer, tester, requirements, documenter |
| `documenter` | developer, tester, requirements, validator |
| `git` | developer, tester, release, documenter |
| `release` | tester, validator, documenter, git |
| `docker` | developer, release, tester |
| `security-auditor` | developer, tester, validator, requirements |

### Endpunkte (keine aktive Delegation, nur Verweise)

| Rolle | Verweist auf |
|-------|-------------|
| `requirements` | developer, tester, documenter (implizit) |
| `agent-meta-scout` | requirements, agent-meta-manager, meta-feedback |
| `meta-feedback` | — (Terminal-Agent, keine Verweise) |

---

## Parallelisierbare Gruppen

Agenten die im gleichen Workflow-Schritt **keine Abhängigkeit** zueinander haben
und parallel laufen könnten:

| Workflow-Phase | Parallelisierbar | Bedingung |
|----------------|-----------------|-----------|
| Nach Implementierung | `validator` ∥ `documenter` | Beide lesen nur, kein Write-Konflikt |
| Nach Fix | `tester` ∥ `validator` | Nur wenn Tests + Validation unabhängig |
| Nach Scout-Evaluation | `agent-meta-manager` ∥ `meta-feedback` | Verschiedene Aktionen |
| Feature-Lifecycle Ende | `documenter` ∥ `git` (branch) | Doku + Branch-Erstellung parallel |

**Nicht parallelisierbar:**
- `tester` → `developer` (TDD: Test muss vor Implementierung stehen)
- `developer` → `tester` (Code muss vor Test-Ausführung fertig sein)
- `validator` → `git` (Validierung muss vor Commit abgeschlossen sein)
- `requirements` → `tester` (REQ-ID muss vor Test-Schreiben existieren)

---

## Häufigste Delegations-Pfade

```
User → orchestrator → requirements → tester → developer → tester → validator → documenter → git
       └────────────────────────── Workflow A: Neues Feature ───────────────────────────────────┘

User → orchestrator → requirements → tester → developer → tester → validator → git
       └────────────────────────── Workflow B: Bugfix ──────────────────────────┘

User → orchestrator → agent-meta-scout → agent-meta-manager → git
       └────────────────── Workflow N: Skill-Vorschlag ────────┘

User → orchestrator → ideation → requirements
       └────────── Workflow I: Neue Idee ──────┘
```
