{{#if SE_ENABLED}}
## Systems Engineering Mode

Der `se-cascade` implementiert rekursive Zig-Zag-Dekomposition (L0→L{{SE_MAX_DEPTH}}) mit V-Model-Integration.

### Zig-Zag Workflow

```
L0: Stakeholder Needs (SN-xxx)
 ↓
L1: Requirements (REQ-L1-xxx) ←→ Architecture (ARCH-L1-xxx)
 ↓
L2: Requirements (REQ-L2-xxx) ←→ Architecture (ARCH-L2-xxx) → Interface Registry
 ↓
L3..Ln: rekursiv bis {{SE_MAX_DEPTH}}
```

Jedes Requirements↔Architecture-Paar bildet einen REPEAT_UNTIL-Loop (generator + critic, max. {{SE_MAX_CRITIC_ITERATIONS}} Iterationen).

### Rekursive Cells

- `termination` = `continue` → neuer System-Cell auf Level n+1; Context sanitisiert (nur BB-REQ + propagation_map)
- `termination` = `leaf` → Component, Übergabe an Implementierung

### Context-Hygiene

- Kein vollständiger Parent-Context an Kinder
- Jede Cell hat eigenen Critic-Loop
- Interfaces aus `se-interface-mgr` sind einziger Cross-Cell-Kanal
- Max. {{SE_MAX_PARALLEL_CELLS}} parallele Cells pro Level

### Tiefen-Konfiguration

| Variable | Bedeutung |
|---|---|
| `SE_MIN_DEPTH` ({{SE_MIN_DEPTH}}) | Nie vorher terminieren |
| `SE_MAX_DEPTH` ({{SE_MAX_DEPTH}}) | Immer hier terminieren |

### V-Model

- **Left wing:** L0→Ln — Requirements + Architecture
- **Right wing:** V&V nach termination
  - `se-validator`: L1 User-Journey
  - `se-verifier`: Multi-Level-Traceability
  - `se-integration-and-test-manager`: V&V-Orchestration

### Level-ID-Prefixe

| Level | Requirements | Architecture | Designation |
|---|---|---|---|
| L0 | `SN-xxx` | — | Stakeholder Needs |
| L1..Ln (continue) | `REQ-L{n}-xxx` | `ARCH-L{n}-xxx` | System |
| L1..Ln (leaf) | `REQ-L{n}-xxx` | — | Component |

### Verhältnis zu DoD Preset

SE und DoD arbeiten auf unterschiedlichen Ebenen:

| Ebene | SE Cascade | DoD Preset |
|---|---|---|
| Phase | Spezifikation (WHAT) | Implementierung (IS DONE) |
| Output | SN, REQ-Ln, ARCH-Ln | Code, Tests, Reviews |
| Quality Gates | `se-critic` | `code-reviewer`, `tester`, `validator` |
| Traceability | Zig-Zag-Matrix SN→...→leaf | REQ-Traceability via Commits |

Übergabe: Cascade liefert Leaf-Requirements an `developer`; ab dann gilt DoD.

**SE-Required Modi** (`se-required` im DoD preset):
{{#if DOD_SE_OPTIONAL}}
- **spec-optional**: SE verfügbar, nicht zwingend.
{{/if}}
{{#if DOD_SE_RECOMMENDED}}
- **spec-driven**: SE empfohlen für komplexe Features (>1 Datei).
{{/if}}
{{#if DOD_SE_STRICT}}
- **spec-certified**: SE vor jedem Code zwingend; Approval-Gates aktiv.
{{/if}}

### Output-Struktur

Konfigurierbar via `se_output` in `.meta-config/project.yaml`:

```yaml
se_output:
  base_dir: "SE"
  per_level_dirs: true
  per_system_dirs: true
```

Regeln:
- System-Ordner: Postfix `System`; Component-Ordner: Postfix `Component`
- L{n}-Ordner sind rekursiv verschachtelt
- Cross-cutting-Dokumente liegen in `SE/`
- L0 nur Stakeholder-Needs; Leaf-Systeme nur Requirements
- Orchestrator legt Ordnerstruktur vor Delegation an SE-Agenten an

{{/if}}
