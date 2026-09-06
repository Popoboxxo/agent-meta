# SE-Kaskade: Artefakt-Taxonomie

Verbindliche Taxonomie, Trennregel und Output-Location-Regeln für alle SE-Artefakte
(Issue #339 B3/B4, Issue #334). Normativ nur bei aktiver SE-Kaskade.

{{#if SE_ENABLED}}

## Verzeichnisstruktur

Basis-Verzeichnis: `{{SE_BASE_DIR}}` (Konzept-Default: `docs/se`; tatsächlich gilt der
per `se_output.base_dir` konfigurierte Wert).

```
{{SE_BASE_DIR}}/
├── ADR/                              ← flach: ADR-NNN_kurztitel.md
├── L0/                               ← flach: Stakeholder Needs (SN-*)
├── L1/
│   └── {Name}System/                 ← Postfix "System" Pflicht
│       ├── L1_{System}_Requirements.md
│       ├── L1_{System}_Architecture.md
│       ├── L2_architectural_decomposition_iter-N.md   ← Decomposition-Drafts
│       ├── L2_architectural_decomposition_clarifications_iter-N.md
│       ├── .se-state.yaml            ← cell-local State
│       └── L2/{SubSystem}System/     ← rekursiv verschachtelt
│           └── Components/{Id}Component/   ← Postfix "Component" Pflicht
├── VV/                               ← flach: systemweite V&V-Strategie (VV_Strategy.md)
├── reviews/                          ← flach: REVIEW_<YYYY-MM-DD>_<scope>.md
├── traceability/                     ← flach: TRACE_<scope>.md
└── reports/                          ← Status-, Audit- und Critic-Reports
    └── {System|Component}/           ← System-scoped Critic-Reports (Issue #334)
```

- System-Ordner enden IMMER auf `System`, Component-Ordner IMMER auf `Component`
  (eindeutige Zell-Identifikation ohne Tag-Ebene).
- `implementation/`-Subfolder existieren nur INNERHALB von Zellen, nie auf Root-Ebene.
- Cell-local `.se-state.yaml` pro Zelle (Resume ohne globale Locks).

## Datei-Naming

- Schema: `<TYPE>-<ID>_<kurztitel>.md` bzw. `L{N}_{FolderName}_{Artefakt}.md`
  (lowercase snake_case kurztitel, ASCII, keine Leerzeichen).
- **Versionsnummern im Dateinamen sind VERBOTEN** (`_v6`-Suffix ist die #339-Sünde).
  Versionierung ausschließlich via Git.
- Erlaubte Iterations-Marker NUR für Klärungs-/Decomposition-Dokumente: `_iter-N`.
  Review-Intermediate (`*.iter-N.md`, `*.critic.iter-N.md`, `*.critic.final.md`)
  neben Final-Artefakten sind verboten (Issue #334) — siehe unten.
- YAML-Frontmatter-Pflicht für alle SE-Dokumente, mindestens:
  `type`, `scope`, `status`, `date`, `author_agent`.
  `type` ∈ `ADR | REQ | REVIEW | TRACE | ARCH | VV-DOC | STRATEGY`.

## Output-Location-Regeln (Issue #334)

| Artefakt | Ablageort | Nie daneben |
|----------|-----------|-------------|
| Final-Artefakt (Requirements/Architecture) | Zelle: `L{N}_{FolderName}_{Requirements|Architecture}.md` (ohne Suffix) | Keine `.iter-N`/`.final`/`.critic.*`-Kopien |
| Review-Protokolle | `{{SE_BASE_DIR}}/reviews/REVIEW_<YYYY-MM-DD>_<scope>.md` | REQ-/ARCH-Dateien |
| Critic-Reports (Audit-Trail) | `{{SE_BASE_DIR}}/reports/{FolderName}/` | Zellen-Ordner |
| Traceability-Matrizen | `{{SE_BASE_DIR}}/traceability/TRACE_<scope>.md` | REQ-/ARCH-Dateien |
| Metriken/Zusammenfassungen | `{{SE_BASE_DIR}}/reports/` (zentral) | Jede REQ-/ARCH-Datei |
| V&V-Strategie-Dokumente | `{{SE_BASE_DIR}}/VV/` (flach, z. B. `VV_Strategy.md`) | REQ-/ARCH-Dateien |
| ADRs | `{{SE_BASE_DIR}}/ADR/ADR-NNN_kurztitel.md` | REQ-/ARCH-Dateien (nur `open_adrs`-Referenz) |

Ausnahme (Konzept §7-Zellen): Zell-lokale V&V-Step-Artefakte (`TestPlan`, `Validation`) dürfen im
`validation/`- bzw. `implementation/`-Subfolder **innerhalb** ihrer Zelle liegen — die flache
`VV/`-Ablage ist für systemweite Strategie-Dokumente. Beides nie in REQ-/ARCH-Dateien.

- Iterations-Zustand läuft über den A2A-Loop (Generator ⇄ Critic) und Review-Protokolle —
  nicht als Dateien neben Final-Artefakten. Optionales Iterations-History lebt im
  Critic-Endreport (Issue #334, Punkt 4), nicht in verstreuten Zwischendateien.
- Stale-Intermediate älterer Läufe (`*.iter-N.md`, `*.final.md`, `*.critic.*`) im
  Zellen-Ordner werden nach dem Final-Pass entfernt.

## L2-Trennregel (Issue #339 B4)

REQ-Dateien enthalten **NUR Anforderungen**: messbare Aussagen, Akzeptanzkriterien,
external interfaces, Verifikationsreferenzen, YAML-Frontmatter.

Erlaubte Struktur einer REQ-Datei: max. 1 H1 (Titel), 1× H2 `Beschreibung`,
N× H2 `Akzeptanzkriterien`, YAML-Frontmatter. Alles andere ist ein Taxonomie-Verstoß.

| Artefakt | Ablageort | Erlaubt in REQ-Datei? |
|----------|-----------|----------------------|
| Architecture-Decomposition | `L{N}_{System}_Architecture.md` (Zelle) | ❌ — nie inline |
| Implementation | `implementation/` innerhalb der Zelle | ❌ |
| Review-Befunde | `{{SE_BASE_DIR}}/reviews/` (nur `review_id`-Referenz) | ❌ — nie inline |
| Traceability-Matrizen | `{{SE_BASE_DIR}}/traceability/` | ❌ |
| Metrik-Tabellen/Zusammenfassungen | zentraler Report in `{{SE_BASE_DIR}}/reports/` | ❌ — redundant pro REQ-Datei verboten |
| V&V-Dokumente | `{{SE_BASE_DIR}}/VV/` | ❌ |
| ADR-Inhalte | `{{SE_BASE_DIR}}/ADR/` | ❌ — nur `open_adrs`-Referenz im Frontmatter |

## Geltungsbereich

Diese Taxonomie bindet alle Agenten, die SE-Artefakte erzeugen oder verschieben
(`se-requirements`, `se-component-requirements`, `se-architect`, `se-critic`,
`se-integration-and-test-manager`, `se-verifier`, `se-validator`, `se-developer` und Ableitungen). Beim Anlegen eines
neuen SE-Dokuments gilt: erst Taxonomie-Platz wählen, dann Datei schreiben — nie
umgekehrt.

{{/if}}
