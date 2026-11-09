# Config-Welle #1187 / #1186 / #1188 / #1181 — Wave-Overview

> **Status: APPROVED** — Approved: 2026-11-09 (User-Freigabe via main_chat)
> **Datum:** 2026-11-09 · **Basis:** Branch `docs/config-wave-plans-1181-1188`, HEAD `aaed14c2`,
> agent-meta `v2.0.0-beta.8`
> **Autor:** `planner` (Subagent der Wave, Auftrag des Orchestrators)
> **Grundlage:** die vier Specs/Pläne dieser Wave, `.tmp/scenario-config-wave/RESULT.md`
> (Szenariotest, 52/52) und `tests/scenarios/registry.md`.
> **Dieses Dokument plant und koordiniert.** Es implementiert nichts, committet nichts und
> aktiviert in `.meta-config/project.yaml` **nichts**.

---

## 1. Zweck und Umfang der Welle

Vier Config-Issues greifen in **dieselben** Dateien (`config/project-config.schema.json`,
`scripts/lib/config.py`, `scripts/lib/agent_sync.py`, `scripts/admin-server.py`,
`docs/ui/admin-ui.html`, beide vollständigen `project.yaml.example`). Ohne eine gemeinsame
Reihenfolge und eine kanonische Konfliktmatrix entstehen Hunk-Kollisionen und widersprüchliche
Teilwahrheiten (z. B. „`project-state`" in drei Dokumenten, ein Separator in zwei Schlüsselformen,
fünf vs. vier Präzedenzstufen).

**Umfang der Welle:**

- **#1187** — Scope der `{{PROJECT_CONTEXT}}`-Injektion (`all | core+orchestrator |
  core+whitelist | core`), Pointer-Zeile statt Duplikat.
- **#1186** — `artifact-locations`-Matrix (14 Nicht-SE- + 9 SE-Klassen, `mode`, `git`, `naming`,
  `legacy[]`, `unmanaged[]`), generierte `ARTIFACT_*`-Variablen, Scaffolding, Hook und
  `--status-artifacts`.
- **#1188** — deklarative Issue-Label-Taxonomie (drei Achsen, siebenstufiger Resolver,
  Tracker-Adapter, `sync.py --labels`, Consistency-Check, generierte Doku).
- **#1181** — projektseitiger Commit-Authority-Grant für Edit-only-Rollen
  (`auto_commit.authority_overrides`), Hook-Härtung, Schrumpf-Warnung.

**Nicht Teil der Welle:** #1189 (Tmp-Sink-Pin, eigener Plan auf demselben Branch), #1141
(top-level-Striktheit, Nachläufer) und die Whitelist-Ableitung (Nachlauf zu #1186).

### 1.1 Status-Tabelle

| Issue | Spec | Plan | Klasse | Umfang (verifiziert) | Status |
|---|---|---|---|---|---|
| **#1187** Project-Context-Injection-Scope | `docs/specs/2026-11-09-project-context-injection-scope-spec.md` | `docs/plans/2026-11-09-project-context-injection-scope-plan.md` | **L** | **15 Tasks / 4 Meilensteine**; T2 ist durch die D5/D6/D8-Validierung auf **L** gewachsen | `APPROVED` |
| **#1186** Artifact-Locations-Matrix | `docs/specs/2026-11-09-artifact-locations-matrix-spec.md` | `docs/plans/2026-11-09-artifact-locations-matrix-plan.md` | **XL** | **24 Tasks / 6 Meilensteine** (T1–T21, T23, T24 im PR; **T22 = Follow-up** nach #1141); T23/T24 sind neu aus D1 | `APPROVED` |
| **#1188** Issue-Label-Taxonomie | `docs/specs/2026-11-09-issue-label-taxonomy-spec.md` | `docs/plans/2026-11-09-issue-label-taxonomy-plan.md` | **XL** | **30 Pflicht-Tasks / 8 Meilensteine** (18 Testdateien); **T30 ist Pflicht-Task** (D12) | `APPROVED` |
| **#1181** Commit-Authority-Grant | `docs/specs/2026-11-09-commit-authority-grant-spec.md` | `docs/plans/2026-11-09-commit-authority-grant-plan.md` | **L** | **16 Tasks / 6 Meilensteine** | `APPROVED` |

**Alle acht Artefakte dieser Welle tragen `Status: APPROVED`** — Freigabe erteilt durch den User am
2026-11-09 (via `main_chat`, §10). **Offene Fragen gibt es keine mehr** — alle 23
Entscheidungen D1–D23 sind am 2026-11-09 gefallen und in die vier Specs/Pläne eingearbeitet (§9).

---

## 2. Empfohlene Ausführungsreihenfolge

```
#1187  →  #1186  →  #1188  →  #1181  →  #1141  →  Whitelist-Ableitung (Nachlauf zu #1186)
```

**Begründung in vier Sätzen:**

1. **#1187 zuerst** — es setzt die Rollen-Schleife in `scripts/lib/agent_sync.py:1444-1468` neu auf,
   auf der #1188 und #1181 aufsetzen; der Eingriff ist der kleinste (eine Enum + eine Liste).
2. **#1186 danach** — es baut die Datenstruktur (`artifact-locations`, 54 `ARTIFACT_*`-Variablen)
   und deklariert `docs/issue-labels.md` bereits als `project-docs`-Datei, damit der Managed-Tree-
   Hook die von #1188 erzeugte Datei nicht blockt.
3. **#1188 danach** — es bringt eigene Module, Panes und den Tracker-Pfad; es setzt die
   Platzhalter in dieselben vier Rollen-Templates, die #1186 vorher auf Variablen umgestellt hat.
4. **#1181 zuletzt** — es hängt an denselben Injektionspunkt (`agent_sync.py:1457-1468`) und
   dieselbe Stage 14 (`sync_pipeline.py:1893-1924`) wie #1186; **#1141** schaltet top-level
   `additionalProperties: false` erst, wenn alle neuen Sektionen als Properties existieren, und
   die Whitelist-Ableitung setzt #1141 und alle Sektionen voraus.

```mermaid
graph LR
  A[#1187 Scope] --> B[#1186 Artefakt-Matrix]
  B --> C[#1188 Label-Taxonomie]
  C --> D[#1181 Commit-Grant]
  D --> E[#1141 top-level strikt]
  E --> F[Whitelist-Ableitung]
  B -. deklariert docs/issue-labels.md .-> C
  D -. teilt Stage 14 .-> B
```

**Harte Randbedingungen:**

- **#1189** (Tmp-Sink-Pin) läuft unabhängig **vor** dem Admin-UI-Teil von #1186; ohne
  funktionierenden `admin-server start` sind AC-1186-06/07 nur In-Process testbar.
- **#1151** wird **vor** dem Hook-Teil von #1181 verifiziert/geschlossen (gleiche Datei
  `hooks/1-generic/orchestrator-guard-impl.sh`).
- **#1180** liefert die generierte Lazy-Pointer-Mechanik; sie blockiert nur #1186-T13 (H-3).
- **#1141** ist Nachläufer, nie Voraussetzung (§5).

---

## 3. Kanonische Konfliktmatrix (gemeinsam berührte Dateien)

Jede Zeile ist eine Datei, die **mehr als ein** Wellen-Issue berührt. Die Spalte
„Serialisierung" ist verbindlich; „seriell" heißt: ein PR nach dem anderen in der Reihenfolge aus
§2, kein Parallel-Edit.

| Datei | Beteiligte Issues | Konfliktnatur | Serialisierung |
|---|---|---|---|
| `config/project-config.schema.json` | #1187, #1186, #1188, #1181 (+ #1141) | Drei neue Top-Level-Sektionen + eine Nested-Erweiterung (`auto_commit`) + `$defs`-Erweiterungen; alle Einfügepunkte liegen im selben `properties`-Block; Zeilennummern aller Folgeänderungen verschieben sich | **zwingend seriell** `#1187 → #1186 → #1188 → #1181`; #1141 (Wurzel-Regel) **danach** |
| `scripts/lib/config.py` | #1187, #1186, #1188, #1181 | Vier Änderungen im selben `build_variables`/`_build_core_variables`-Umfeld (`:1792-1848`, `:2673-2734`, `:2737` ff.); Importe und Aufrufreihenfolge kollidieren | seriell in Wave-Reihenfolge; je Issue ein eigener Resolver-Aufruf statt gemeinsamer Inline-Logik |
| `scripts/admin-server.py` | #1187, #1186, #1188 (+ #1189) | Dieselbe handgepflegte `PROJECT_WRITABLE_SECTIONS` (`:234-259`); #1189 zusätzlich `_start`/`_tmp_sink_env` | seriell; #1186s **Ableitungs-Teil** ist abgespalten und läuft als letzter Schritt (§2) |
| `docs/ui/admin-ui.html` | #1187, #1186, #1188, #1181 | Vier Panes in einer handgebauten Single-File-UI; gemeinsame Helper (`saveProjectSection`) | **zwingend seriell**, Panes nacheinander in Wave-Reihenfolge |
| `scripts/lib/agent_sync.py` | **#1187, #1188, #1181** | Dieselbe Rollen-Schleife (`:1444-1468`) und `_finalize_agent_content` (`:935`): #1187 baut sie um, #1188 setzt `_apply_role_issue_convention_overrides`, #1181 `_apply_role_auto_commit_overrides` + `extra_tools` | **zwingend seriell** `#1187 → #1188 → #1181`; #1181 findet den fertigen Overlay-Punkt vor |
| `scripts/lib/sync_pipeline.py` | **#1186, #1181** | Beide bauen **Stage 14** (`:1893-1924`) um; #1186 hängt Stage 14c („resolved.json") direkt danach (`cli_commands.py:1613-1616`) | seriell `#1186 → #1181` (Stage-Reihenfolge 13 → 14 → 14b → 14c → 15); Parallel-Edit ausgeschlossen |
| `scripts/lib/variables.py` | **#1187** (nur) | `strip_inactive_conditional_blocks`-Whitelist (`:570-598`) ist der Ort, an dem #1187 `PROJECT_CONTEXT_INJECTED` einträgt; #1186/#1188/#1181 editieren die Datei **nicht** | seriell, aber ohne Schreibüberschneidung; #1186 markiert sie nur als Hotspot |
| `scripts/lib/standalone.py` | **#1187** (Federführung), **#1186** (T6) | `_standalone_variables` (`:295-336`) liefert Fallback-Werte; #1187 ergänzt `PROJECT_CONTEXT_*`, #1186 die 54 `ARTIFACT_*`-Defaults | **D-9-Ausnahme dokumentiert:** #1186 hält einen additiven Fallback-Block, obwohl die Zielmatrix die Datei #1187 zuordnet — sonst rendern 26 Standalone-Personas „not available"; #1187 bleibt Datei-Federführer, die Reihenfolge `#1187 → #1186` verhindert den Parallel-Edit |
| `tests/scenarios/registry.md` | **#1181, #1187, #1186** | Katalogzeilen sind zeilenscharf; gemeinsame Nummerierung | IDs vorab vergeben (§4); #1188 schreibt **keine** Zeile |
| `templates/configs/project.yaml.example` **und** `howto/configs/project.yaml.example` | **alle vier** | Beide Beispiele listen jede Config-Option; vier Issues schreiben in dieselbe Doku-Region | je PR nur eigene Keys, keine Umsortierung; beide Dateien immer im selben PR; #1186 hält sie in T20 synchron |
| `scripts/lib/consistency/placeholders.py` | #1186, #1187, #1188 | Dieselbe Allow-List (`:114-123`); drei Autoren, je mehrere Namen; Ratchet ist shrink-only | seriell (jede Zeile ist ein Merge-Konflikt) |
| `scripts/consistency-check.py` | #1186, #1188 (+ #1187, #1180) | Neue Check-Registrierungen an denselben Import-/Aufrufstellen (`:42-70`, `:224-273`) | seriell |
| `agents/1-generic/git.md` | #1188 (`:149-151`), #1181 (Grant-Block), #1168 (Trailer) | Drei Änderungen in derselben Prosa-Region | seriell: #1188 vor #1181; #1168 unabhängig |
| `agents/1-generic/{feedback,meta-feedback,bug-feature-analyzer}.md` | #1186, #1187, #1188 | #1186 stellt Pfade um, #1187 das Prosa-Vorkommen (`bug-feature-analyzer.md:40`), #1188 die Label-Tabellen | seriell `#1187 → #1186 → #1188`; #1186 hat bei den Feedback-Rollen Federführung vor #1188 |
| `hooks/1-generic/orchestrator-guard-impl.sh` | #1181, #1151 | #1151 härtet denselben Hook; #1181 ergänzt `all_git`-Feld + Grant-Gate | seriell: #1151 zuerst, dann #1181 |
| `docs/issue-labels.md` | #1188 (Erzeuger), #1186 (Klassifizierung) | Neue generierte Datei; #1186 deklariert sie als `project-docs.files.issue-labels` | #1186 vor #1188 (sonst blockt der Managed-Tree-Hook) |
| `.meta-config/issue-labels-state.json` | #1188 (Erzeuger), #1186 (Klassifizierung) | Persistiertes Prune-Manifest; **`unmanaged[]`** (K1), keine Klasse | #1186 vor #1188 |
| `README.md`, `AGENTS.md`, `CLAUDE.md`, `docs/CODEBASE_OVERVIEW.md` | alle vier | Dieselben Doku-Dateien, je neue Abschnitte | seriell, Doku zuletzt nach den Code-PRs |

---

## 4. Szenario-IDs (Katalog `tests/scenarios/registry.md`)

| ID | Issue | Form |
|---|---|---|
| `94` | **#1181** | Katalog-Szenario `94-auto-commit-authority-grant` (+ `asserts/94-…sh`) |
| `95`–`98` | **#1187** | vier Katalog-Szenarien (je Modus ein Lauf) |
| `99` | **#1186** | Katalog-Szenario `99-artifact-locations-matrix` (+ `asserts/99-…sh`) |
| keine | **#1188** | **keine** Katalog-ID; der End-to-End-Test ist `tests/test_issue_labels_scenario_1188.py` (gemockter Tracker, pytest) |

Der Katalog endet auf `aaed14c2` bei `93`; `94`–`99` sind frei und in allen vier Plänen
übereinstimmend reserviert (Szenario C5/C6: 52/52 grün).

---

## 5. Backlog-Zuordnung je Plan

Legende: **in-scope** = im PR enthalten · **teilweise** = Teilaspekt enthalten, Rest als Folge-Issue
· **abhängig** = nur Datei-/Reihenfolge-Abhängigkeit, kein Inhalt · **bewusst NICHT** = explizit
außerhalb des PR-Umfangs.

### 5.1 #1187 (Project-Context-Scope)

| Issue | Einordnung | Federführung / Begründung |
|---|---|---|
| **#1161** Token-Reduktion | teilweise | #1187 ist ein zusätzlicher Hebel auf dasselbe Ziel; die Delta-Messung (AC6) übernimmt die dortige Zählweise. Federführung #1161. |
| **#1180** Pointer-Prüfung | teilweise | #1187 erzeugt einen neuen Datei-Pointer; die Prüfmechanik liefert #1180. Federführung #1180. |
| **#1182** `compact` + `orchestrator.mode` | abhängig | Gleiche Orchestrator-Semantik, anderer Codepfad (`context.py`); #1187 verschärft den Abbruch nicht. |
| **#1183** `compact`-Profil | abhängig | Gleiche Metrik, anderer Kanal. |
| **#1141** Unknown-Key | abhängig | Nur der Sektionsname-Tippfehler; intern ist #1187 geschlossen. |
| **#1186** Artefakt-Matrix | abhängig | Nur „kein neuer always-on-Block" + geteilte Dateien. |

### 5.2 #1186 (Artifact-Locations-Matrix)

| Issue | Einordnung | Federführung / Begründung |
|---|---|---|
| **#1150** fehlende Output-Struktur | teilweise (Elternproblem) | #1186 liefert den Mechanismus; **#1150-AC-4** (`.tmp`-Promotion/Cleanup) bleibt Nicht-Ziel. Nach Merge #1150 auf Punkt 2 reduzieren. |
| **#1189** Tmp-Sink-Pin | abhängig (Blocker) | Voraussetzung für den Admin-UI-Teil; eigener Plan. |
| **#1141** top-level-Striktheit | abhängig (Nachläufer) | #1186 ist self-contained pro Sektion; #1141 läuft danach. |
| **#1180** Lazy-Pointer | teilweise | H-3 braucht die generierte Tabelle; **Federführung #1180**. |
| **#1195** Sync-Backup-Retention | abhängig | Nur Zähl-Nebenbedingung (`file_count`/`newest`); Ausschlussmuster im Status-Report. |
| **#1151** Hook-Bypässe | teilweise (verifizieren) | Der neue Hook nutzt `hook_common.sh` v1.9.0, dupliziert nichts. |
| **#1181** Stage-14-Kollision | abhängig | Läuft nach #1186. |
| **#1188** Label-Dateien | abhängig (Klassifikation) | #1186 klassifiziert vorab; **Federführung #1188** für den Generator. |

### 5.3 #1188 (Issue-Label-Taxonomie)

| Issue | Einordnung | Federführung / Begründung |
|---|---|---|
| **#1167** REQ-ID-Format | abhängig (Datei-nah) | Gleiche Dateien (`conventions-presets.yaml`, `bug-feature-analyzer.md`), andere Stellen; nicht parallel editieren. Federführung #1167. |
| **#1141** top-level-Striktheit | abhängig (Nachläufer) | #1188 liefert die Property; #1141 schaltet danach strikt. |
| **#1181** Grant | abhängig (Prosa/Datei) | #1181 folgt nach #1188 (`agent_sync.py`, `git.md`). |
| **#957** PR-Templates | teilweise (Nachbar) | Gemeinsame Ownership-Frage (`generated-file-hashes.json`); T25 nutzt die Marker-Regel. Federführung #957. |
| **#1168** Co-Authored-By | abhängig | Nur Datei-Serialisierung in `git.md`. |
| **#1186** Artefakt-Klassifikation | abhängig | `docs/issue-labels.md` = `project-docs`, State-Datei = `unmanaged` (K1). |

### 5.4 #1181 (Commit-Authority-Grant)

| Issue | Einordnung | Federführung / Begründung |
|---|---|---|
| **#1142** invalid `auto_commit` exit 0 | teilweise (Vorbedingung der Doku-Aussage) | #1181 erbt den #1091-Fail-Safe; harte Exit-Codes/„kein Allowlist-Write" bleiben #1142. T9 pinnt das heutige Verhalten. **Federführung #1142.** |
| **#1151** Hook-Bypässe | abhängig (Sicherheit) | Rollout-/Doku-Reihenfolge; **#1151 vor T16**. Federführung #1151. |
| **#1172** Merge/Push-Blockade | bewusst NICHT | Push/Tag/Merge bleiben `git`-Rolle; kein Task, nur ein Doku-Satz. |
| **#1186/#1187/#1188** | abhängig (Datei-Kollision) | Seriell nach ihnen. |

### 5.5 Federführung bei Überschneidungen (verbindlich)

| Fläche | Federführung | Nachläufer |
|---|---|---|
| top-level-Striktheit, Unknown-Key-Finding | **#1141** | alle vier liefern nur Properties |
| Lazy-Pointer-Tabelle, `docs/`-Auslieferung | **#1180** | #1186-H-3 konsumiert |
| `compact`-Profil, `orchestrator.mode`-Abbruch | **#1182**, **#1183** | #1187 nur abhängig |
| Invalid-`auto_commit`-Exit-Politik | **#1142** | #1181 dokumentiert kompatibel |
| Hook-Härtung, `hook_common.sh` | **#1151** | #1181-T16 setzt darauf auf |
| REQ-ID-Format | **#1167** | #1188 nur Datei-Serialisierung |
| PR-/Issue-Template-Ownership | **#957** | #1188-T25/T30 |
| `{{PROJECT_CONTEXT}}`-Injektion | **#1187** | #1186 fasst die Variable nicht an (H-4) |
| Artefakt-Matrix + Klassifikation | **#1186** | #1188 erzeugt die Dateien |
| Feedback-/Triage-Rollen-Templates | **#1186** (Pfad) vor **#1188** (Labels) | #1187 nur Prosa |
| Commit-Authority-Render + Hook | **#1181** | — |

---

## 6. Neu angelegte Issues #1197–#1211

Alle Nummern sind im Wave-Kontext als real bestätigt; keines der vier Wellen-Dokumente erfindet
eine Nummer.

| Nummer | Titel | Ursprungsplan | Einordnung |
|---|---|---|---|
| **#1197** | `bug(templates): {{PROJECT_CONTEXT}} 2–3× pro Rollen-Prompt (ui-ux-designer 3×)` | #1187 | Folge-Issue; AC2 (Byte-Identität) verbietet die Bereinigung in #1187 |
| **#1198** | `bug(agents): SE templates use {SE_BASE_DIR} with single braces — sync never substitutes it` | #1186 | Folge-Issue (F-1); 16 Vorkommen in 12 Dateien |
| **#1199** | `bug(admin): deriving PROJECT_WRITABLE_SECTIONS from the schema drops 7 runtime-only sections` | #1186 | Follow-up **nach** #1141 (Union-Regel + Mengengleichheits-Test) |
| **#1200** | `chore(docs): classify the 8 unmanaged docs/ subtrees and the audit-*.md files` | #1186 | Folge-Issue (F-3); `unmanaged[]` bereits deklariert, Rest offen |
| **#1201** | `fix(config): conventions.issues.labels.namespace renders 'type: {type}'` | #1188 | Folge-Issue (F-1); Minimal-Fix unabhängig möglich |
| **#1202** | `improvement: carry the triage priority criteria into the label taxonomy` | #1188 | Folge-Issue (F-2); Träger liefert #1188 |
| **#1203** | `chore(cli): disambiguate sync.py --label (backup) and --labels` | #1188 | Folge-Issue (F-3); T21 entschärft nur per Help-Text |
| **#1204** | `bug(admin-ui): conventions editor exposes inert issues.* fields` | #1188 | Folge-Issue (F-4); neues Pane kommt aus T26 |
| **#1205** | `bug(config): auto_commit key allowlist exists twice (schema vs. _KEYS)` | #1181 | Folge-Issue (F-1); T1 hält beide synchron |
| **#1206** | `bug(admin-ui): saving the auto-commit panel drops unknown keys` | #1181 | Folge-Issue (F-2); T10 behebt den Datenverlust, Feld folgt |
| **#1207** | `docs(spec): #1181 cites stale 767 anchors and the dead Gemini mapper` | #1181 | Folge-Issue (F-3/F-4); T11 zieht nur Anker nach |
| **#1208** | `chore(docs): AGENTS.md drift — generated file differs from the committed copy` | **Querschnitt** | Vorbestehender Drift/Ausfall (siehe §7); nicht Teil eines Wellen-PR |
| **#1209** | `improvement(config): template-mode gating needs two boolean variables per artifact class` | #1186 | Folge-Issue zur AC-05-Präzisierung (kein `{{#if ARTIFACT_*_MODE}}`) |
| **#1210** | `bug(hooks): PreToolUse payload carries agent_id but no agent name` | #1181 | Folge-Issue (F-5); Attributionslücke, keine Security-Boundary |
| **#1211** | `chore(config): default issue-conventions.enabled to true and delete the legacy label blocks` | #1188 | Folge-Issue (F-5); Voraussetzung für vollständige AC-6-Wirkung |

---

## 7. Verifikationsprotokoll (Ist-Stand der Welle)

Die folgenden Ergebnisse sind auf `aaed14c2` **vor** jeder Implementierung gemessen; sie sind der
Vergleichspunkt für alle vier PRs.

| Prüfung | Befehl | Erwartet / gemessen |
|---|---|---|
| Konsistenz-Gate | `python3 scripts/sync.py --validate` | **EXIT 0**, `[PASS]`; genau die vorbestehende WARN `repo-containment.no-hook-support` |
| Drift-Gate | `python3 scripts/sync.py --check` | **EXIT 1** mit **exakt** dem vorbestehenden Drift (`generated-file-drift`, `context.over-cap AGENTS.md`) — kein neuer Befund |
| Testsuite | `python3 -m pytest tests -q` | **889/890 grün**; **1 vorbestehender Ausfall** → **#1208** (AGENTS.md-Drift), nicht durch die Welle verursacht |
| Szenariotest | `python3 -m pytest .tmp/scenario-config-wave/test_scenario_config_wave.py -q` | **52/52 grün** (A1–A18, B1–B26, C1–C6, D1–D2) |
| Konflikt-Auflösung | §8 | **K1–K8 aufgelöst**; verbleibende echte Widersprüche: keine |
| Formalgate | Review der vier Specs/Pläne | **PASS** (Templates, Frontmatter, keine leeren Zellen, `pipeline_stages` wo nötig) |
| Branch-Guard | `git branch --show-current` | `docs/config-wave-plans-1181-1188`; jede Umsetzung auf eigenem `feat/…`-Branch |

**Regel:** Kein Wellen-PR darf `--validate` von EXIT 0 weg oder `--check` um einen **neuen**
Befund erweitern. Der eine vorbestehende Testausfall bleibt bis #1208 rot und wird in jedem
PR-Report als „vorbestehend" ausgewiesen.

**Entscheidungen:** Die 23 Entscheidungen D1–D23 (§9) sind am 2026-11-09 in alle vier Specs/Pläne
eingearbeitet; die erneute Verifikation dieses Protokolls (Status-Tabelle, Testzahlen,
`--validate`/`--check`-Baseline) erfolgt nach dem Re-Commit.

---

## 8. Szenario-Validierung (Kurzfassung aus `.tmp/scenario-config-wave/RESULT.md`)

**Gesamturteil vor der Auflösung: `WIDERSPRUCH`** — schema-seitig kombinierbar, aber ein Blocker
und zwei strukturelle Widersprüche.

### 8.1 Vorab validiert (bewiesen, §4.1 der RESULT)

- **Schema-Integration:** Draft-07-Meta-Validierung; positive Fixture mit allen vier Sektionen,
  23 Klassen, 3 Achsen, Grant mit Ack.
- **Schema-Negatives:** unbekannter Top-Level-Key, Pfad-Traversal, ungültiger `mode`,
  fehlendes/falsches Ack, `authority ≠ direct`.
- **Kollisionen:** die drei neuen Top-Level-Keys fehlen im echten Schema; `auto_commit` wird nur
  additiv erweitert; kein doppelter Key; alle neuen Sektionen sind `object`.
- **Präzedenz:** #1187 (2 Ebenen), #1186 (Stufen + `disabled`), #1188 (7 Stufen inkl.
  AC-14-Reihenfolge), #1181 (mode/roles/active-set/Grant/derived/Gate).
- **Querschnitt:** `docs/issue-labels.md` = `project-docs`, State-Datei = `unmanaged`,
  Status-JSON-Form für 23 Klassen, `unmanaged` nur top-level.
- **Szenario-IDs:** Katalog 1–93 vollständig, 94–99 frei, vier Pläne stimmen überein.
- **Ist-Zustand:** `--validate` EXIT 0; nur 8 neue `docs/**`-Dateien; keine Code-/Config-Änderung.

### 8.2 Ohne Implementierung nicht validierbar (§4.2 der RESULT)

Unbekannte Whitelist-Rolle als harter Sync-Fehler; Byte-Identität bei `mode: all`, Pointer-Zeilen
und `context_file` pro Provider; echte `--status-artifacts`-Ausgabe (`exists`, `file_count`,
`newest`, `legacy_hits`); Hook-Enforcement; Admin-UI/`PROJECT_WRITABLE_SECTIONS`/HTTP 400;
Provider-Gate (`provider_hooks_supported`); `_KEYS`-Fail-Safe-Interaktion; semantische Regeln
(`mode: off` ohne Eltern, `legacy`/`unmanaged`-Schnitt, `se-requirements: off`);
Scaffold-Verhalten, Preset-Dateien und generierte Doku. Diese Punkte sind als Tests in den Plänen
verankert, aber erst mit Code beweisbar.

### 8.3 K1–K8-Status (nach Einarbeitung)

| Befund | Entscheidung | Status |
|---|---|---|
| **K1** BLOCKER | `unmanaged` bleibt, `project-state` gestrichen; `classes` bleibt 23 | **aufgelöst** |
| **K2** MAJOR | eine kanonische Form `defaults.separator: {single, multi}`; `label-separator` entfernt | **aufgelöst** |
| **K3** MAJOR | vier Wertequellen + Source-Attribution `project-preset`/`disabled` | **aufgelöst** |
| **K4** MINOR | kein `default`-Feld; Regel 6 = zwei realisierbare Bedingungen; Zwei-Defaults = AC-7-Laufzeitregel | **aufgelöst** |
| **K5** MINOR | Gate ist Wirkbedingung („Post-Grant-Demotion"), keine Präzedenzstufe 7 | **aufgelöst** |
| **K6** NIT | `$defs` bleibt (Ist-Schema nutzt es unter Draft-07), explizit dokumentiert | **aufgelöst** |
| **K7** NIT | `acknowledge_full_shell` (snake_case in `auto_commit`); Stilsatz dokumentiert | **aufgelöst** |
| **K8** Voraussetzung | Schema **und** `_KEYS` im selben PR + Mengengleichheits-Test | **aufgelöst** |

**Scratch-Hinweis:** `.tmp/scenario-config-wave/` (RESULT, Prototyp, Fixtures, 52 Tests) ist
**gitignored** und bleibt als Beleg liegen; es ist **kein** Repo-Artefakt und wird nicht
committet.

---

## 9. Entscheidungsprotokoll (2026-11-09) — D1…D23, alle `DECIDED`

Alle 23 offenen Fragen der vier Specs sind am 2026-11-09 vom User entschieden und in den jeweiligen
Abschnitt „Entscheidungsprotokoll (2026-11-09)" der Specs/Pläne eingearbeitet. Die Nummern sind
wellenweit eindeutig: **D1–D4** → #1186, **D5–D8** → #1187, **D9–D15** → #1188, **D16–D23** → #1181.
Keine Zeile dieser Tabelle ist offen; ein Widerspruch dazu braucht eine Spec-Revision.

| D-Nr | Issue | Frage (kurz) | Entscheidung (`DECIDED 2026-11-09`) | betroffene Tasks |
|---|---|---|---|---|
| **D1** | #1186 | Kopplung `classes.scratch.path` ↔ `repo_containment.tmp-sink.path` | **Eine** Quelle: `artifact-locations.classes.scratch.path`. Der Temp-Mechanismus wandert in den Pfad-Mechanismus: `tmp-sink.path` ist **Legacy-Alias** und wird nur gelesen, solange die Klasse fehlt; sind beide gesetzt, müssen die Werte gleich sein — Divergenz = **harter Fehler** `artifact-locations.scratch-sink-divergence`. `TMP_SINK_PATH` bleibt, wird aber aus der Matrix gespeist; der Containment-Hook liest den **aufgelösten** Wert statt des Roh-Keys. Migration `--migrate-artifact-aliases [--write]` | T4, T5, T9, T15, **T23**, **T24** |
| **D2** | #1186 | Gilt die Zielmatrix für `scripts/lib/standalone.py` ausnahmslos? | **Nein — die D-9-Ausnahme bleibt.** #1186 behält den additiven Standalone-Fallback-Block (54 Framework-Defaults), #1187 bleibt Datei-Federführer; die Reihenfolge `#1187 → #1186` verhindert den Parallel-Edit. Kein Follow-up-Issue | T6 |
| **D3** | #1186 | ADR-Naming und Konfigurierbarkeit von `naming` | Naming ist **pro Klasse** konfigurierbar (String-Pattern mit geschlossener Token-Liste). Projekt-Default ADR: `ADR-<NNN>_<slug>.md`; `legacy[]` akzeptiert zusätzlich `NNNN-<slug>.md` und `ADR-<NNN>-<slug>.md`. Unbekannter/nicht anwendbarer Token = `artifact-locations.naming-invalid` | T1, T2, T4, T5, T15, T20, T23 |
| **D4** | #1186 | `SE` oder `docs/se` als SE-Wurzel-Default | Default bleibt **`SE`**, keine Migration. Der Regeltext verweist auf `{{ARTIFACT_SE_ROOT}}` statt auf ein Literal; `docs/se/**` ist `legacy[]`-Muster (kein Default, kein zweiter Pfad) | T2, T4, T20 |
| **D5** | #1187 | Gehören `providers.<P>.primary-role`-Rollen zur Orchestrator-Achse? | `orchestrator-roles: []` ist konfigurierbar; Default = `{orchestrator} ∪ primary-roles` der aktiven Provider (deterministisch, dedupliziert). Ein Eintrag **ersetzt** den Default vollständig; `[]` ist zulässig; unbekannte Rolle = harter Sync-Fehler | T1, T2, T5, T8, T13, T15 |
| **D6** | #1187 | `mode: all` + `orchestrator: exclude` = Fehler oder stille Verengung? | **Kein Fehler.** `exclude` gewinnt („alle außer Orchestrator"), der Sync läuft weiter und gibt **WARN** `project-context-injection.exclude-overrides-mode` aus. Der `SyncError`-Pfad ist aus T2/T5/T15 entfernt; `core` + `exclude` bleibt ohne WARN gültig | T2, T5, T8, T15 |
| **D7** | #1187 | Was bedeutet AC7 (der genannte „prompt-quality check" existiert nicht)? | AC7 = `sync.py --validate` grün **und** `pointer-missing == 0` **und** keine leeren Pflichtsektionen (bestehende Checks). Kein neuer Check; der Issue-Text wird redaktionell nachgezogen | T8, T11, T15 |
| **D8** | #1187 | Pointer-Text Englisch oder Projektsprache? | Konfigurierbar mit Default **Englisch**: `pointer-language` (`en`\|`de`\|`project`) und `pointer-text` (Token `{context_file}` genau einmal, einzeilig). `project` leitet aus `COMMUNICATION_LANGUAGE` ab; unbekannt/leer → `en` + WARN `pointer-language-fallback`; Fremd-Token/≠ 1 × `{context_file}`/Zeilenumbruch = harter Fehler | T1, T2, T4, T6, T8, T11, T13, T15 |
| **D9** | #1188 | Repository-Identität ohne `git.remote-url` | Präzedenzkette `issue-conventions.repository.{owner,repo}` **>** `git.remote-url` **>** CI-Env (`GITHUB_REPOSITORY`, `CI_PROJECT_PATH`). Harter Fehler erst, wenn **alle drei** leer/unparsbar sind; die Meldung nennt alle drei Wege und gibt nie einen leeren `owner` aus | T1, T15 |
| **D10** | #1188 | Wie wird ein Rename erkannt, wenn der Tracker der einzige Zustand ist? | **Kein Rename in v1.** Neuer Wert ⇒ `create <neu>`; das alte Label bleibt im Tracker, Meldung `info: rename-candidate <alt>`; kein `update.new_name`, keine `rename`-Ausgabezeile. Eine explizite `renames`-Map bleibt einer späteren Spec-Revision vorbehalten | T17 |
| **D11** | #1188 | Drift-Ownership der generierten Doku | `docs/issue-labels.md` kommt in `.meta-config/generated-file-hashes.json` (Root-Level-Registrierung); manuelle Edits werden beim nächsten Sync überschrieben und gemeldet. **#957 spiegelt die Regel** für PR-Templates; dieselbe Registrierung gilt für die T30-Tracker-Templates | T25, T30 |
| **D12** | #1188 | Wo sitzt der Template-Schalter? | `issue-conventions.templates.{mode: off\|scaffold\|manage, force: bool}` als geschlossener Unterabschnitt (Default `off`, `force: false`). **T30 wird Pflicht-Task** (kein bedingter Task, keine Schema-Erfindung) | T1, T30 |
| **D13** | #1188 | Wer committet `.meta-config/issue-labels-state.json` nach `--apply`? | `--apply` **schreibt** und druckt den Pfad in der Ergebnis-Tabelle; kein `git`-Aufruf im CLI. Die **`git`-Rolle committet**; CI-`--apply`-Jobs committen **nie** | T21 |
| **D14** | #1188 | Retry-Policy | Genau **ein** Retry, nur bei `429`, Wartezeit aus `Retry-After` (Cap 30 s, Default 1 s, injizierbarer `sleep`). `5xx`/Timeouts ohne Retry; `401`/`403` brechen nach dem ersten Fehlschlag ab; kein Backoff, keine Konfiguration in `project.yaml` | T16, T18 |
| **D15** | #1188 | Sind Triage-Labels Teil der Taxonomie? | **Nein.** `TRIAGE_LABELS = ("triage", "needs-info")` als Framework-Konstante; `docs/issue-labels.md` führt sie unter „Nicht Teil der Taxonomie"; kein Projekt-Override, kein `prune`-Ziel, Regel 4 nimmt sie von der Literal-Prüfung aus | T9, T13, T25 |
| **D16** | #1181 | Persona-Konflikt (`documenter` bleibt Referenzrolle) | **Akzeptiert, Persona unangetastet.** `agents/1-generic/documenter.md` wird nicht geändert; der Grant wird als **Commit-Recht** in der Grant-Zeile des `AUTO_COMMIT_BLOCK` ausgewiesen und in der Doku erklärt; Byte-Golden der Nicht-Grant-Rollen bleibt unverändert | T5, T11, T14 |
| **D17** | #1181 | Auch Revoke-Werte akzeptieren? | **Nur `direct`, kein Revoke.** Entzug ausschließlich über `roles:`-Entfernung oder Entfernen des Override-Keys; `grant withdrawn` bleibt an die `roles:`-Entfernung gebunden, nur entfernter Key ⇒ `no Bash` | T1, T3, T7, T9, T13 |
| **D18** | #1181 | Kommando-genaue Bash-Permission statt voller Shell? | **Nein: voller Bash + Hook-Härtung + ehrliche Doku** (keine „nur `git`"-Aussage). Der Guard blockt Sentinel-tragende Nicht-`git`-Kommandos; die Attributionslücke ist ausdrücklich als Grenze benannt und als **#1210** erfasst; Ack bleibt Pflicht | T8, T11, T13, T16 |
| **D19** | #1181 | Schrumpf-Warnung als ERROR/CI-Gate? | **Nein, bleibt WARN.** Kein CI-Gate; das exakte Log-Format bleibt gepinnt; #1142 ist nur eine spätere Option | T9, T14 |
| **D20** | #1181 | Grant unter `suggest`? | **Nein.** `resolve_commit_grant` liefert `(derived, False)`: kein `Bash`-Render, keine Grant-Zeile, kein Sentinel; Artefakt und `eligible_roles` bleiben mode-unabhängig | T6, T8, T11 |
| **D21** | #1181 | Hook-loser Provider im gemischten Set = ERROR? | **Nein, WARN je Provider.** Auf Providern mit aktivem Guard wird gerendert, auf den übrigen bleibt die abgeleitete Authority + WARN. **ERROR nur**, wenn der Grant auf **keinem** Ziel-Provider wirken kann | T2, T6, T8, T12 |
| **D22** | #1181 | Rolle außerhalb von `roles:` = Fehler? | **Nein, INFO.** `authority_override_notices` liefert die INFO-Zeile `<role>=direct ignored — role is not active…`; ERROR nur für read-only/unbekannte Templates und nicht durchsetzbare Grants | T2, T13 |
| **D23** | #1181 | Skalar-Kurzform akzeptieren? | **Nein, nur Objektform mit Pflicht-Ack** `{authority: direct, acknowledge_full_shell: true}`. Fehlendes/falsches Ack = Violation + kein Grant | T1, T2, T7, T11 |

### 9.1 Querschnittsnotizen zu den Entscheidungen

- **D1 → neue Datei-Ownership in #1186:** `hooks/1-generic/repo-containment{,-impl}.sh` gehören
  jetzt zu #1186 (T24). Die Pfad-Quelle wird auf die aufgelöste Matrix umgestellt
  (`ARTIFACT_SCRATCH_DIR` → `classes.scratch.path` aus `artifact-locations.resolved.json` →
  `repo_containment.tmp-sink.path` → `.tmp`); die lexikalischen Regeln und `hook_common.sh` bleiben
  unangetastet. **Kein anderes Wellen-Issue editiert diesen Hook.**
- **D3/D4 → Rollen-/Regel-Doku in #1186-T20:** T20 zieht Manager-Rolle, Regeltext
  (`rules/1-generic/se-cascade-artifact-taxonomy.md` nutzt `{{ARTIFACT_SE_ROOT}}`), beide
  `project.yaml.example` und Changelog nach. D3 ändert zusätzlich T1/T2/T4/T5/T15/T23 (Naming-Pattern).
- **D11 → Kopplung an #957:** `generated-file-hashes.json` ist die gemeinsame Ownership-Frage;
  #957 spiegelt die Registrierungs-Regel für PR-Templates. Serialisiert wird bei jeder
  `.github/`-Erzeugung (§3, §5.3/#957).
- **D18 → Verweis auf #1210:** Die Attributionslücke des PreToolUse-Payload (`agent_id` ohne
  Agent-Namen) ist bewusst **nicht** Teil von #1181, sondern als #1210 erfasst und als
  Nicht-Security-Boundary dokumentiert.

---

## 10. Approval-Gate — APPROVED 2026-11-09

1. **Alle vier Specs und alle vier Pläne tragen `Status: APPROVED`** — Freigabe erteilt durch den
   User am 2026-11-09 (via `main_chat`). Die Pläne sind damit **Ausführungsauftrag**, nicht mehr
   nur belastbare Vorarbeit.
2. **Umsetzung autorisiert** (Master-Rule `spec-plan-workflow`): Die Freigabe-Voraussetzung ist
   erfüllt; jede Umsetzung startet auf einem eigenen `feat/…`-Branch.
3. **Es gibt keine offenen OQ mehr.** Alle 23 Entscheidungen D1–D23 sind am 2026-11-09 gefallen und
   in die vier Specs/Pläne eingearbeitet (§9). Es gibt keine inhaltliche Vorbedingung, die noch zu
   klären wäre.
4. **Branch-Guard:** je Issue ein eigener `feat/…`-Branch
   (`feat/1187-project-context-scope`, `feat/1186-artifact-locations-matrix`,
   `feat/1188-issue-label-taxonomy`, `feat/1181-commit-authority-grant`). **Nie** direkt auf
   `main`/`master`; der Branch `docs/config-wave-plans-1181-1188` trägt nur Doku.
5. **Freigabe-/Umsetzungsreihenfolge:** `#1187 → #1186 → #1188 → #1181`; #1141 erst nach #1181.
   Die Freigabe ist für alle vier erteilt, die **Umsetzung** bleibt in dieser Reihenfolge
   serialisiert.
6. **Nach jedem gemergten Issue** wird dieses Overview nachgezogen (Status `IN PROGRESS` bzw.
   `complete`, neue Findings, verschobene Nummern) — es ist nicht eingefroren.
