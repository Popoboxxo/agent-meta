# Artefakt-Ausgabeorte (artifact-locations)

> Lazy-Regel — bei Bedarf per `Read` öffnen: `{{SKILLS_DIR}}/artifact-locations/SKILL.md`.

Diese Regel ist die verbindliche Übersicht über die **23 Artefakt-Klassen** der
Matrix `artifact-locations` (Issue #1186). Die Matrix ist die einzige Wahrheits-
quelle für Ausgabeort, Modus, Naming und Git-Behandlung. Rollen schreiben
ausschließlich in die unten genannten Variablen — niemals in ein Pfad-Literal.
Konkrete, aufgelöste Werte liefert `python3 scripts/sync.py --status-artifacts --json`.

## Modus-Semantik

| Modus | Bedeutung |
|---|---|
| `files` | Ausgabe in das klassenbezogene Verzeichnis / die klassenbezogene Datei; das Ziel wird idempotent angelegt. |
| `inline` | Das Artefakt bleibt im Prompt / Chat — kein Datei-Ziel, kein Output-Datei-Versprechen. |
| `off` | Die Klasse ist deaktiviert; ein Schreibziel entfällt (bei Bedarf mit `fallback-parent` umleiten). |

## Klassen-Tabelle — 14 Nicht-SE + 9 SE

### Nicht-SE-Klassen (14)

| Klasse | Variable(n) | Zweck / kind |
|---|---|---|
| specs | `{{ARTIFACT_SPECS_DIR}}` | Spezifikationen |
| plans | `{{ARTIFACT_PLANS_DIR}}` | Implementierungspläne |
| concepts | `{{ARTIFACT_CONCEPTS_DIR}}` | Konzepte |
| spikes | `{{ARTIFACT_SPIKES_DIR}}` | Spikes |
| reviews | `{{ARTIFACT_REVIEWS_DIR}}` | Reviews (kind: code, concept, domain, copyedit, proofread, se) |
| audits | `{{ARTIFACT_AUDITS_DIR}}` | Audits (kind: security, dependency, a11y, lifecycle, prompt, ai-security) |
| analysis | `{{ARTIFACT_ANALYSIS_DIR}}` | Analysen (kind: analysis, triage, perf, log, research, estimate, conclusion) |
| reports | `{{ARTIFACT_REPORTS_DIR}}` | Reports (kind: vv) |
| adr | `{{ARTIFACT_ADR_DIR}}` | Architecture Decision Records |
| traceability | `{{ARTIFACT_TRACEABILITY_DIR}}` | Traceability-Matrizen |
| runbooks | `{{ARTIFACT_RUNBOOKS_DIR}}` | Runbooks |
| project-docs | `{{ARTIFACT_ARCHITECTURE_FILE}}`, `{{ARTIFACT_CODEBASE_OVERVIEW_FILE}}`, `{{ARTIFACT_REQUIREMENTS_FILE}}`, `{{ARTIFACT_ISSUE_LABELS_FILE}}` | Projekt-Dokumente (Datei-Set) |
| scratch | `{{ARTIFACT_SCRATCH_DIR}}` | Ephemere Zwischenstände (ignored) |
| state | `{{ARTIFACT_STATE_DIR}}` | Ephemerer Zustand / Event-Log (ignored) |

### SE-Klassen (9)

Basis ist `{{ARTIFACT_SE_ROOT}}` (Alias `SE_BASE_DIR`); `se-root` ist keine eigene
Klasse, sondern der Default der neun `path`-Felder.

| Klasse | Variable | Leaf-Muster |
|---|---|---|
| se-requirements | `{{ARTIFACT_SE_REQUIREMENTS_DIR}}` | L{level}_Requirements |
| se-architecture | `{{ARTIFACT_SE_ARCHITECTURE_DIR}}` | L{level}_Architecture |
| se-decomposition | `{{ARTIFACT_SE_DECOMPOSITION_DIR}}` | Architektur-Dekomposition |
| se-interfaces | `{{ARTIFACT_SE_INTERFACES_DIR}}` | L{level}_Interfaces |
| se-implementation | `{{ARTIFACT_SE_IMPLEMENTATION_DIR}}` | L{level}_Impl |
| se-testplan | `{{ARTIFACT_SE_TESTPLAN_DIR}}` | L{level}_TestPlan |
| se-validation | `{{ARTIFACT_SE_VALIDATION_DIR}}` | L{level}_Validation |
| se-verification | `{{ARTIFACT_SE_VERIFICATION_DIR}}` | L{level}_Verification |
| se-decisions | `{{ARTIFACT_SE_DECISIONS_DIR}}` | L{level}_Decisions |

SE-globale Reviews, Reports, ADR und Traceability sind keine eigenen Klassen,
sondern abgeleitete Projektionen von `{{ARTIFACT_SE_ROOT}}`:
`{{ARTIFACT_SE_REVIEWS_DIR}}`, `{{ARTIFACT_SE_REPORTS_DIR}}`,
`{{ARTIFACT_SE_ADR_DIR}}`, `{{ARTIFACT_SE_TRACEABILITY_DIR}}`.
`mode`, `git`, `naming`, `legacy[]` und `unmanaged[]` kommen ausschließlich aus
der Matrix — `unmanaged[]` ist keine Klasse.

## Rollen-Anleitung

- Niemals ein Pfad-Literal schreiben; immer die Variable der jeweiligen Klasse
  aus der Tabelle verwenden (`ARTIFACT_*_DIR` bzw. `ARTIFACT_*_FILE`).
- `mode: inline` ⇒ kein Output-Datei-Ziel erwähnen; `mode: off` ⇒ `fallback-parent`
  beachten; Roh-Evidenz verbleibt auf `{{ARTIFACT_SCRATCH_DIR}}` / `{{TMP_SINK_PATH}}`.
- Naming folgt dem Token-Kanon der Matrix; Dateinamen erzeugt die Rolle, das
  Verzeichnis kommt aus der Variable.
- Legacy-Ablagen sind read-only und kein Default; der Default liegt unter
  `{{ARTIFACT_SE_ROOT}}`.
