{{#if SE_ENABLED}}
## Systems Engineering Mode

The `se-cascade` pipeline implements a recursive Zig-Zag decomposition (L0→L{{SE_MAX_DEPTH}}) with V-Model integration.

### Zig-Zag Workflow

The cascade follows a strict alternating pattern between Requirements and Architecture:

```
L0: Stakeholder Needs (SN-xxx)
 ↓
L1: Requirements (REQ-L1-xxx) ←→ Architecture (ARCH-L1-xxx)
 ↓
L2: Requirements (REQ-L2-xxx) ←→ Architecture (ARCH-L2-xxx) → Interface Registry
 ↓
L3: Requirements (REQ-L3-xxx) ←→ Architecture (ARCH-L3-xxx)
 ↓
L4...Ln: (rekursiv, gleiches Muster bis {{SE_MAX_DEPTH}})
```

Each Requirements↔Architecture pair forms a REPEAT_UNTIL loop (generator + critic, max {{SE_MAX_CRITIC_ITERATIONS}} iterations).

### Recursive Cell Spawns

When the `termination` stage decides `continue` for a system:
1. System is further decomposable — **designated as System** (or Subsystem in parent context)
2. Orchestrator spawns a **new cell** at level n+1
3. Context is **sanitized** — only `BB-REQ` + `propagation_map` row (~800 tokens)
4. New cell starts at the Requirements stage for that level
5. `trace_parent` links to parent cell's handoff_id

When `termination` decides `leaf`:
- Leaf system is final — **designated as Component**
- Handover to implementation discipline (developer, hardware-engineer, etc.)

### Context Hygiene Rules

- **Never** pass full parent context to child cells — only sanitized BB-REQ + propagation row
- Each cell operates independently with its own critic loop
- Interface specs from `se-interface-mgr` are the only cross-cell communication channel
- Max {{SE_MAX_PARALLEL_CELLS}} parallel cells at any level

### Depth Configuration

| Variable | Default | Meaning |
|----------|---------|---------|
| `SE_MIN_DEPTH` | {{SE_MIN_DEPTH}} | Minimum decomposition depth (never terminate before) |
| `SE_MAX_DEPTH` | {{SE_MAX_DEPTH}} | Maximum decomposition depth (always terminate at) |

The `se-termination` agent receives both values in its input envelope and enforces them deterministically.

### V-Model Integration

- **Left wing** (Decomposition): L0→L1→L2→L3 — each level produces requirements + architecture
- **Right wing** (V&V): Validation stage runs after termination
  - `se-validator`: L1 User-Journey validation
  - `se-verifier`: Multi-Level verification (cross-level traceability)
  - `se-integration-and-test-manager`: V&V orchestration

### Level ID Prefixes

| Level | Requirements Prefix | Architecture Prefix | Designation |
|-------|-------------------|-------------------|-------------|
| L0 | `SN-xxx` | — | Stakeholder Needs |
| L1..Ln (continue) | `REQ-L{n}-xxx` | `ARCH-L{n}-xxx` | System (Subsystem) |
| L1..Ln (leaf) | `REQ-L{n}-xxx` | — | Component (final) |

### Relationship to DoD Preset

The SE cascade and the DoD preset operate on **different layers** and do NOT conflict:

| Layer | SE Cascade | DoD Preset |
|-------|-----------|------------|
| **Phase** | Specification (WHAT to build) | Implementation (IS the code done?) |
| **Output** | SN, REQ-L{n}, ARCH-L{n} | Code, Tests, Reviews |
| **Quality Gates** | `se-critic` (own critic loops) | `code-reviewer`, `tester`, `validator` |
| **Traceability** | Own Zig-Zag matrix (SN→REQ-L1→ARCH-L1→REQ-L2→ARCH-L2→...→leaf) | REQ-Traceability via commit messages |

**The handover point:** When the cascade finishes, it hands leaf system requirements to `developer`. From that point on, the DoD preset applies.

**SE-Required modes** (configured via `se-required` in the DoD preset):

{{#if DOD_SE_OPTIONAL}}
| SE mode: **spec-optional** — SE cascade is available but not mandatory. Leaf system requirements are informative. Developer can start without SE output.
{{/if}}
{{#if DOD_SE_RECOMMENDED}}
| SE mode: **spec-driven** — SE cascade recommended for complex features (>1 file). If SE output exists, leaf system requirements become acceptance criteria with REQ-Traceability in commits.
{{/if}}
{{#if DOD_SE_STRICT}}
| SE mode: **spec-certified** — SE cascade MANDATORY before any code. Full traceability SN→REQ-L1→ARCH-L1→...→leaf→Code→Tests required. Approval gates active. For regulated environments.
{{/if}}

**SE cascade does NOT replace the DoD preset** — it adds a specification layer BEFORE implementation. Choose your DoD preset independently, then add SE via the `se-required` field.

### Output Directory Structure

Configurable via `.meta-config/project.yaml` → `se_output`:

```yaml
se_output:
  base_dir: "SE"              # Hauptordner
  per_level_dirs: true        # L1/, L2/, L3/, ... (rekursiv geschachtelt)
  per_system_dirs: true       # .../L1/Gesamtsystem/L2/AuthServiceSystem/, ...
```

**Folder naming:** System folders get `System` postfix, Component folders get `Component` postfix.

Generated structure (example with SE_MAX_DEPTH=4):
```
SE/
├── STRATEGY.md                    # System-Ziel, Constraints
├── traceability-matrix.md         # REQ-L1-001 → ARCH-L1-001 → REQ-L2-001 → ...
├── interface-registry.md          # Zentrale Interface-Tabelle
│
├── L0/
│   └── SN_Stakeholder_Needs.md
│
└── L1/
    └── Gesamtsystem/
        ├── L1_Gesamtsystem_Requirements.md
        ├── L1_Gesamtsystem_Architecture.md
        └── L2/
            ├── AuthServiceSystem/
            │   ├── L2_AuthServiceSystem_Requirements.md
            │   ├── L2_AuthServiceSystem_Architecture.md
            │   └── L3/
            │       ├── TokenValidatorComponent/
            │       │   └── L3_TokenValidatorComponent_Requirements.md
            │       └── JWTHandlerComponent/
            │           └── L3_JWTHandlerComponent_Requirements.md
            └── MCPServerSystem/
                ├── L2_MCPServerSystem_Requirements.md
                ├── L2_MCPServerSystem_Architecture.md
                └── L3/
                    └── CryptoEngineComponent/
                        └── L3_CryptoEngineComponent_Requirements.md
```

**Rules:**
- Jedes System hat genau eine Requirements- und eine Architecture-Datei
- L{level}-Ordner sind **rekursiv geschachtelt**: L2 liegt in `L1/{System}/`, L3 in `L1/{System}/L2/{System}/`, usw.
- System-Ordner erhalten Postfix `System`, Component-Ordner Postfix `Component`
- Cross-cutting Dokumente (STRATEGY, traceability-matrix, interface-registry) liegen direkt in SE/
- L0 hat nur Stakeholder-Needs (keine Architektur)
- Leaf-Systeme (termination=leaf, designation=Component) haben nur Requirements (keine weitere Architecture)
- Der Orchestrator legt die Ordnerstruktur VOR Delegation an die SE-Agenten an und setzt `output_parent_path` und `FolderName` im A2A-Envelope-Payload

{{/if}}
