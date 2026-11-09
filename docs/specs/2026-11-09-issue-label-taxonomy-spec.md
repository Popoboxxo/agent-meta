# Issue #1188 — Deklarative Issue-Label-Taxonomie mit steckbaren Tracker-Adaptern — Spec

> **Status:** APPROVED — Approved: 2026-11-09 (User-Freigabe via main_chat)
> **Klasse:** **XL / cross-cutting** — neue Config-Sektion, neuer Resolver, deklarativer HTTP-Executor gegen fremde Tracker-APIs, vier Rollen-Templates, neuer Consistency-Check, Admin-UI-Pane, generierte Doku.
> **Datum:** 2026-11-09
> **Autor:** `concept-specifier` (Subagent der Wave `docs/config-wave-plans-1181-1188`)
> **Issue:** <https://github.com/Popoboxxo/agent-meta/issues/1188> — `feat(config): declarative issue-label taxonomy with pluggable tracker adapters (type/area/priority)`, `state: open`, Body 27.927 Zeichen
> **Spec-ID (Trace-Anker):** `SPEC-issue-label-taxonomy-2026-11-09`
> **Basis:** Repo `Popoboxxo/agent-meta`, Branch `docs/config-wave-plans-1181-1188`, HEAD `aaed14c2`, agent-meta `v2.0.0-beta.8`
> **Maßgebliche Quelle:** `.tmp/issue-dump/issue-1188.json` (identisch mit dem GitHub-Body, am 2026-11-09 gegengeprüft)
> **Weitere Quellen:** `issue-1187.json`, `issue-1186.json`, `issue-1181.json` (Konfliktflächen) · `issue-1167/1141/957/1168.json` (Backlog) · `.tmp/issue-dump/baseline-validate.txt`, `baseline-check.txt` (Baseline: `[PASS]`, `EXIT=0`; 1 Warning `repo-containment.no-hook-support`)
> **Verifikations-Legende:** **CONFIRMED** = am Code mit `datei:zeile` belegt · **PARTIAL** = Kernaussage stimmt, Detail weicht ab · **ISSUE-CLAIM** = Aussage aus dem Issue, hier nicht erneut geprüft · **REFUTED** = widerlegt
> **Revision 2 (Review-Einarbeitung 2026-11-09):** RVW-1188-01 (BLOCKER), -02 … -06 (MAJOR) sowie drei WARNs sind eingearbeitet. Auflösungstabelle: §12 „Review-Auflösung (2026-11-09)". Status damals `DRAFT` (Freigabe seit 2026-11-09 `APPROVED`).
> **Revision 3 (Review-Runde 2, 2026-11-09):** RVW2-1188-01 … -04 (Prune-Kandidatenformel, Beispiel-Dateien, Testgüte/Abschlusskriterium, Stufen-Nummerierung) sowie die Querschnittsbefunde RVW2-X-01 (Ziel-Dateimatrix) und RVW2-X-02 (Klassifikation der State-Datei durch #1186 als `unmanaged`) sind eingearbeitet. Status damals `DRAFT` (Freigabe seit 2026-11-09 `APPROVED`).
> **Revision 4 (Szenario-Konflikte K1–K8, 2026-11-09):** K1 (`unmanaged` statt `project-state`), K2 (eine kanonische `separator`-Form, `defaults.label-separator` entfernt), K4 (Regel 6 auf zwei realisierbare Bedingungen), K6 (`$defs`-Notiz) sind eingearbeitet; K3/K5/K7/K8 betreffen dieses Dokument nicht. Auflösungstabelle: §12.1. Status damals `DRAFT` (Freigabe seit 2026-11-09 `APPROVED`).
> **Revision 5 (Nutzer-Entscheidungen D9–D15, 2026-11-09):** Die offenen Fragen Q1, Q2, Q3, Q4, Q7, Q8 und Q9 sind **entschieden und eingearbeitet** (§13 „Entscheidungsprotokoll (2026-11-09)"): Repository-Präzedenzkette (D9/Q1), kein Rename in v1 (D10/Q3), `docs/issue-labels.md` in `generated-file-hashes.json` (D11/Q4), Template-Schalter `templates.{mode,force}` in IC-1 (D12/Q8), `--apply` schreibt / `git` committet (D13/Q9), Retry nur bei `429` mit `Retry-After` (D14/Q2), Triage-Labels als Nicht-Taxonomie (D15/Q7). Status damals `DRAFT`; die Freigabe `Status: APPROVED` wurde am 2026-11-09 durch den User erteilt.

---

## Problem

*(Abschnitt 2 der geforderten Gliederung — Problem & Motivation.)*

Es gibt im Framework **genau eine** Issue-Konvention (`conventions.issues`), sie ist aber **wirkungslos**: sie rendert ausschließlich in `GIT_ISSUE_NAMING_BLOCK`, und dieser Block wird ausschließlich von `git.md` referenziert — der einzigen Rolle, die **keine** Issues anlegt. Die drei Rollen, die tatsächlich Labels vergeben, tragen jeweils eine eigene, hartkodierte Label-Tabelle. Es existiert keine Label-Definition, kein Plattform-Adapter, kein Sync und kein Drift-Check.

### 2.1 Motivation

- **Divergenz skaliert mit jeder Rolle und jedem Tracker.** Drei Vokabulare heute (Abschnitt 3.2); jede vierte Rolle und jeder vierte Tracker multipliziert sie.
- **Fehlkonfiguration ist unsichtbar.** Weil `conventions.issues` von den Issue-Rollen ignoriert wird, ändert ein Projekt die Konvention und beobachtet **keine** Wirkung — dieselbe Fehlerklasse wie #1141 (stille Akzeptanz) und #1091 (schema-invalid ohne rc≠0).
- **Ein Tracker ist eine Projektion, keine zweite Wahrheit.** Best Practice (GitLab-Label-Doku, Traefik `contributors-guide/labels.md`, Apache Burr #690, GitHub Issue Forms) ist ein `labels.yml` als Single Source of Truth; der Tracker ist die Projektion davon.
- **Ohne Sync gibt es keinen Drift-Check**, ohne Drift-Check keinen CI-Gate — und damit keine Möglichkeit, die heutige Divergenz dauerhaft zu verhindern.

---

## Ziel (Soll-Zustand in einem Satz)

Eine deklarative, plattformneutrale Label-Taxonomie mit drei Achsen (`type` single, `area` multi/abschaltbar, `priority` single), siebenstufiger Präzedenz mit gemeldeter `source`, einem rein datengetriebenen Adapter-Registry (`config/issue-adapters.yaml`) für GitHub/GitLab/Gitea plus synthetischem viertem Adapter, einem `sync.py --labels [--apply|--check|--explain]`-Pfad mit Dry-Run als Default, einem Consistency-Check `issue-label-taxonomy`, einer Admin-UI-Sektion und einer generierten `docs/issue-labels.md` — sodass Rollen-Templates aus **einem** Resolver gespeist werden statt aus drei lokalen Tabellen.

---

## 3. Ist-Zustand (verifiziert)

| Layer | Was existiert | Wirksam? | Beleg |
|---|---|---|---|
| Framework-Preset | `issues.title_format`, `types: [feat, fix, docs, chore, refactor, test, perf]`, `labels.namespace: "type: {type}"`, `closing_keywords`, `language` | 🟡 gerendert, aber nur in `GIT_ISSUE_NAMING_BLOCK` | `config/conventions-presets.yaml:50-64` (Issue nennt `52-65`) — **CONFIRMED** |
| Renderer | `_render_git_issue_naming()` erzeugt den Block | 🟡 ein einziger Block | `scripts/lib/conventions.py:277-292` — **CONFIRMED** |
| Domain→Block-Mapping | `issues` → `{"GIT_ISSUE_NAMING_BLOCK": …}` | 🟡 | `scripts/lib/conventions.py:131-132` — **CONFIRMED** |
| Rollen-Gate | `applies_to_roles: [git]`, Gate auf `active_roles`, sonst `log.skip` | 🟡 | `scripts/lib/conventions.py:113-122`, `config/conventions-presets.yaml:51` — **CONFIRMED** |
| einziger Konsument | `git.md` rendert den Block; `git.md` enthält **kein** `gh issue create` | ❌ Rolle legt keine Issues an | `agents/1-generic/git.md:149-151`; `grep "gh issue" git.md` → 0 Treffer (nur Issue-*Erwähnungen* als Regression-Note, `:117`) — **CONFIRMED** |
| Projekt-Override | `conventions` ist ein offenes Objekt (`additionalProperties: true`), `issues.*` unvalidiert | 🟡 derselbe eine Konsument | `config/project-config.schema.json:703-707` — **CONFIRMED** |
| einzig wirklich konsumiertes Feld | `issues.language` → `{{ISSUE_LANGUAGE}}`, **unconditional** (nicht rollen-gegated) | ✅ | `scripts/lib/config.py:2711-2722`; Allow-List `scripts/lib/consistency/placeholders.py:123` — **CONFIRMED** (Issue-Claim #579 bestätigt) |
| `git.platform` | Enum `GitHub｜GitLab｜Gitea｜Codeberg` | ❌ reine Daten/UI: speist nur `GIT_PLATFORM`/Setup-Wizard, **kein** Code zweigt darauf | `config/project-config.schema.json:1742-1752`; `scripts/lib/config.py:1717`; `scripts/lib/setup.py:243,365`; `grep` in `scripts/` → keine Verzweigung — **CONFIRMED** |
| Label-Definition / Sync / Drift | — | ❌ | kein `labels.yml`, kein `.github/ISSUE_TEMPLATE/`, kein `docs/issue-labels.md`, kein `--labels` (`scripts/sync.py` kennt nur `--label` **Singular**, `:456`) — **CONFIRMED** |

### 3.1 Belegkette: warum `conventions.issues` heute wirkungslos ist

1. `resolve_conventions()` merged Projekt-Override über Preset — `scripts/lib/conventions.py:43-92`.
2. `render_convention_block("issues", …)` gibt **nur** `GIT_ISSUE_NAMING_BLOCK` zurück — `scripts/lib/conventions.py:131-132`.
3. `build_variables()` schreibt die Blöcke der Domains `release` und `issues` in die Variablen-Map — `scripts/lib/config.py:2724-2730`.
4. `GIT_ISSUE_NAMING_BLOCK` ist in der Platzhalter-Allow-List registriert — `scripts/lib/consistency/placeholders.py:115`.
5. Der **einzige** Template-Konsument ist `agents/1-generic/git.md:151`. `feedback`, `meta-feedback` und `bug-feature-analyzer` referenzieren den Block **nicht** — statt dessen lokale Tabellen (3.3). Die Renderer-Ausgabe behauptet zudem „identisch zum Commit-Type-Vokabular" (`scripts/lib/conventions.py:289`) — das gilt für Commit-Types, **nicht** für die von den Issue-Rollen verwendeten Werte.

**Ergebnis:** Ein Projekt kann `conventions.issues.types`/`labels.namespace` beliebig ändern; das erzeugte Issue-Label ändert sich **nicht**. Kein Test, kein Check und keine Warnung bemerkt das.

### 3.2 Die drei divergierenden Label-Tabellen (PARTIAL-Korrektur zum Issue)

| Rolle | Vokabular | Beleg | Legt Issues an? |
|---|---|---|---|
| `feedback` | `bug`, `enhancement`, `improvement`, `documentation`, `security`, `question` (Matrix `bug→bug`, `feat→enhancement`, …) | `agents/1-generic/feedback.md:41-48`; Erstellung `:66` (`gh issue create … --label`) | **ja** |
| `meta-feedback` | `bug`, `enhancement`, `improvement`, `documentation`, `design`, `feature-request` + „Severity: P0-P3 (as in the `bug-feature-analyzer` matrix)" | `agents/1-generic/meta-feedback.md:46-48`; Erstellung `:53-56` | **ja** |
| `bug-feature-analyzer` | `triage`, `needs-info`, `bug`/`feature` + P0–P3-Kriterientabelle | `agents/1-generic/bug-feature-analyzer.md:89`, `:91-97` | **nein** (Label-Schema für bestehende Issues) |
| `git` | `type: {type}` (aus dem Preset) | `agents/1-generic/git.md:151` + `config/conventions-presets.yaml:56` | **nein** |

**PARTIAL-Korrektur:** Das Issue schreibt „the three agents that **do** create issues (`feedback`, `meta-feedback`, `bug-feature-analyzer`)". Verifiziert erstellen nur `feedback` und `meta-feedback` Issues; `bug-feature-analyzer` **vergibt** Triage-Labels an bestehenden Issues (`gh issue list` statt `gh issue create`, `:30`). Für den Contract ist das relevant, weil der `single-axis-per-issue`-Zwangsmechanismus (AC-7) genau diese Rolle trifft — also eine **Label-Applierin**, nicht eine Erstellerin.

### 3.3 Was heute vollständig fehlt

- keine Label-**Definition** (Werte, Farben, Beschreibungen) an irgendeiner Stelle,
- keine Plattform-**Projektion** (Separator, Case, Farbformat, Namensgrenzen),
- kein **Adapter** (HTTP-Aufruf gegen eine Tracker-API existiert nirgends im Repo),
- kein **Dry-Run-Diff** und kein **Apply**,
- kein **Consistency-Check** (Registry: `scripts/consistency-check.py:42-70`, `run_checks` `:171`),
- keine **generierte** menschliche Doku,
- `issue-conventions` fehlt in der Admin-UI-Whitelist (`scripts/admin-server.py:234-259`) — **CONFIRMED**; die Behauptung „eine von 29 fehlenden Sektionen" stammt aus #1186 und ist hier **ISSUE-CLAIM** (nicht nachgezählt).
- Die Admin-UI **editiert heute** `conventions`-Overrides inklusive `issues.*` (`docs/ui/admin-ui.html:4160-4166`, Speichern `:4316-4317`, Route `:1644`) — sie verspricht also eine Wirkung, die nicht existiert.

---

## 4. Soll-Verhalten

### 4.1 Drei Achsen

| Achse | Kardinalität | Default | Semantik |
|---|---|---|---|
| `type` | `single` — genau ein Wert pro Issue | `enabled: true` | Klassifikation (bug, feature, improvement, documentation, question, security, maintenance) |
| `area` | `multi` — 0..n | `enabled: false` (nur Projekte mit gepflegter Liste) | Modul-/Subsystemzuordnung, projektdefiniert (`values: {}`) |
| `priority` | `single` — genau ein Wert | `enabled: true` | P0–P3, **getrennt** von Severity |

`status` ist **keine** Achse (D2). Severity ist **keine** vierte Achse (Nicht-Ziel).

### 4.2 Presets (zwei Sektionen, reine Daten)

`config/issue-conventions-presets.yaml`:

- `presets.<name>` — `default` (die drei Achsen wie oben), `minimal` (= nur `type`), `conventional` (= `mapping` nach D5). Inhalts-Ebene, plattformneutral.
- `platform.<adapter>` — Framework-**Plattform**-Defaults (Projektions-Vorschläge), z. B. `platform.gitlab.defaults.separator.single: "::"`.

Es gibt **keinen** Codepfad pro Preset (AC-2): der Resolver liest ausschließlich Daten.

### 4.3 Siebenstufige Präzedenz mit `source`

Stärkste zuerst; jede Stufe meldet ihren `source`-String:

| # | Stufe | Pfad | `source` |
|---|---|---|---|
| 1 | Projekt, plattformspezifisch | `issue-conventions.platform-overrides.<adapter>.<key>` | `project:platform-overrides:<adapter>` |
| 2 | Projekt | `issue-conventions.<key>` | `project` |
| 3 | Projekt-Preset | `issue-conventions.preset` | `project:preset:<name>` |
| 4 | Framework-Plattform-Default | `config/issue-conventions-presets.yaml` → `platform.<adapter>` | `framework:platform:<adapter>` |
| 5 | Framework-Preset | dieselbe Datei → `presets.<name>` | `preset:<name>` |
| 6 | Adapter-Projektions-Default | `config/issue-adapters.yaml` → `adapters.<id>.defaults` | `adapter:<id>` |
| 7 | Schema-Default | `config/project-config.schema.json` | `schema-default` |

**Reihenfolge ist AC-14, nicht umgekehrt (RVW-1188-02).** AC-14 verlangt wörtlich:
„a project `platform-overrides.gitlab` value beats the framework `platform.gitlab` default, which
beats `presets.default`". Stufe 4 ist deshalb der Framework-**Plattform**-Default und Stufe 5 das
Framework-**Preset**; die frühere Fassung hatte 4/5 vertauscht. Da `platform.<adapter>`
ausschließlich Projektionsschlüssel führt (`separator`, `color-format`) und `presets.<name>` den
Inhalt (Achsen, Werte, `mapping`), überlappt die Umstellung keinen Inhaltswert; die
Plattform-Stufe ist für Projektionsschlüssel die einzige Datenquelle oberhalb des
Adapter-Defaults. Die AC-Texte selbst bleiben unverändert (wörtliche Issue-Übernahme, siehe
§„Acceptance Criteria").

**Eine kanonische Separator-Form (Review-Auflösung K2).** Der Separator hat auf **allen drei
Ebenen** dieselbe Schlüsselform: `separator: {single, multi}` als Objekt mit beiden
Kardinalitäten — in `config/issue-adapters.yaml` (`adapters.<id>.defaults.separator`), in
`config/issue-conventions-presets.yaml` (`platform.<adapter>.defaults.separator`) und im Projekt
(`issue-conventions.defaults.separator`). Das frühere String-Feld `defaults.label-separator` ist
**entfernt**; IC-1 ist `additionalProperties: false`, ein String wäre fortan ein
Validierungsfehler. Grund: ein String kann die Kardinalitäts-Trennung aus AC-2b nicht ausdrücken
und erzeugte für dieselbe logische Einstellung zwei nicht ineinander abbildbare Antworten
(`/` aus `preset:default` vs. `::` aus `framework:platform:gitlab`, Szenario B16).

Invarianten (sauber getrennt, sie widersprechen sich nicht):

1. **Projekt-Overrides (Stufe 1) schlagen alles.** Ein Projekt-Schlüssel — auch
   `defaults.separator.single`/`.multi` — gewinnt gegen Framework-Plattform-Default (Stufe 4),
   Framework-Preset (Stufe 5) und Adapter-Default (Stufe 6); Stufe 4 darf nur *vorschlagen*
   (AC-15).
2. **Plattform-Defaults ändern nie still den Inhalt.** Stufe 4 darf einen nicht darstellbaren Wert verwerfen — nur mit `log.warning`, der Achse und dem Grund; niemals durch stilles Umbenennen.
3. **Jede Achse und jeder Wert meldet eigenen `source`** — `--labels --explain` druckt `type/bug ← preset:default`, `area ← project`, `separator ← adapter:gitlab` (AC-14). Ein globaler „resolved config"-Dump genügt nicht.

### 4.4 Achsen-Schalter (`enabled`)

Ausgewertet **vor** der Projektion (kein Separator-Resolve, kein API-Call, kein Drift-Finding für eine inaktive Achse):

| Fall | Verhalten |
|---|---|
| `taxonomy.<axis>.enabled: false` | keine Labels dieser Achse; Template-Block lässt die Achse weg; `--check` ignoriert sie; **bestehende Labels werden nie gelöscht** |
| `enabled: true` + `values: {}` | harter Fehler (AC-12) |
| alle drei Achsen `false` bei `enabled: true` | harter Fehler (AC-12) |
| `taxonomy.type.enabled: false` | erlaubt, aber `log.warning` mit Best-Practice-Begründung (AC-13) |
| Framework-Plattform-Default deaktiviert, Projekt aktiviert | Projekt gewinnt, `--explain` zeigt beide (AC-15) |

### 4.5 Deklarative Adapter + Capability-Flags

`config/issue-adapters.yaml` beschreibt die API **als Daten** (Methode, Pfad, Body-Template); ein kleiner Executor macht daraus HTTP-Aufrufe. Ein vierter Tracker ist damit eine Config-Änderung, kein Python-Code (AC-3, D3).

**Verhaltens-Verzweigung ausschließlich über Capability-Flags**, nie über Provider-Namen:

| Flag | Bedeutung | Konsequenz |
|---|---|---|
| `labels` | Tracker kennt Repo-Labels | Basis-Anforderung |
| `scoped-labels` | Label-Namespace erzwingt Eindeutigkeit | `single`-Achsen mit Scoped-Separator; zweites `type::` **ersetzt** das erste (AC-7) |
| `issue-forms` / `issue-templates` | Pre-Labeling bei Erstellung möglich | optionale Template-Generierung (4.9) |

Regeln: `auth` referenziert **nur** eine Env-Variable; die Datei ist für Projekte erweiterbar (Merge über Framework-Defaults). **Projekt-Overrides für den Adapter-Transport haben genau einen deklarierten Ort (RVW-1188-03):** `issue-conventions.platform-overrides.<adapter>.{base-url, api, ids, pagination, auth.header, defaults}` — geschlossen in IC-1, `auth.header` nur mit `{token}`-Platzhalter, `auth.env` **nicht** überschreibbar. Ein Projekt-Eintrag darf damit Pfade, Pfad-Präfix und Header-Template ändern, **nie** ein Token und **nie** Scheme/Host (§4.12 H-2).

### 4.6 CLI: `sync.py --labels [--apply|--check] [--explain]`

| Aufruf | Verhalten | Exit |
|---|---|---|
| `--labels` | Dry-Run-Diff (`create` / `update` / `no-op`) gegen den Tracker, **schreibt nichts** (D4) | 0 |
| `--labels --apply` | führt die Diffs aus; Ergebnis-Tabelle `created`/`updated`/`failed` **plus** die geänderte Datei (`wrote .meta-config/issue-labels-state.json`) — D13 | 0 = alles ok, 1 = Teilfehler |
| `--labels --check` | strikt read-only; Drift ⇒ rc 1 (CI-Gate) | 0 / 1 |
| `--labels --explain` | zeigt pro Achse/Wert den aufgelösten Wert **und** `source` | 0 |

Wiederverwendung: das globale `--apply` existiert bereits (`scripts/sync.py:482-484`, heute nur für `--audit-config`); `--check` existiert (`:334-338`). Der neue Schalter heißt `--labels` (Plural) und kollidiert bewusst nicht mit `--label` (Singular = Backup-Label, `:456`) — siehe Finding F-3.

### 4.7 Consistency-Check `issue-label-taxonomy`

Sechs Regeln, jede mit eigener ID, registriert in `scripts/consistency-check.py` (Importe `:42-70`, `run_checks` `:171`; aufrufbar über `scripts/lib/cli_commands.py:161-185`):

| # | Regel | Severity | Kontext (RVW-1188-06) |
|---|---|---|---|
| 1 | Label in der Taxonomie, im Tracker **fehlend** | `info` (via `--apply` behebbar) | online — nur mit Tracker (`--labels --check`) |
| 2 | Label im Tracker, in **unserem** Namespace, nicht in der Taxonomie | `warning` (nie auto-gelöscht) | online — nur mit Tracker (`--labels --check`) |
| 3 | Farbe/Beschreibung weicht ab | `warning` mit aufgelöstem `source` | online — nur mit Tracker (`--labels --check`) |
| 4 | Rollen-Template enthält ein hartkodiertes Label-Literal | `error` | offline — auch in `--validate` |
| 5 | Issue-erzeugende Rolle ohne `{{ISSUE_TAXONOMY_TABLE}}` | `error` | offline — auch in `--validate` |
| 6 | Kardinalitätsverletzung in der Definition (aktivierte Achse mit leeren `values`; `enabled: true` ohne aktive Achse) | `error` | offline — auch in `--validate` |

**Kein `default`-Feld in `taxonomyAxis` (Review-Auflösung K4).** `taxonomyAxis` ist
`additionalProperties: false` und kennt kein `default`; die frühere Bedingung „zwei Defaults" war
damit schema-seitig unerreichbar (Szenario A13 lehnt sie nur als *unbekannten Schlüssel* ab).
Regel 6 prüft deshalb ausschließlich die zwei realisierbaren Bedingungen (leere `values` bei
aktivierter Achse; keine aktive Achse). Die Regel „genau ein `single`-Achsenwert pro Issue" ist
eine **Laufzeitregel** eines Issue und gehört zu **AC-7** (`enforcement.single-axis-per-issue`,
§4.5/IC-1) — sie wird dort geprüft und in Plan T18 (`enforce_single_axis`) getestet, nicht im
Schema.

**AC-5 ist als Kontext-Split zu lesen, nicht als „alle sechs Regeln im Offline-Lauf" (RVW-1188-06).**
Der Check `issue-label-taxonomy` ist **ein** Modul mit **sechs** IDs (`check_issue_labels(..., tracker=None|Tracker)`).
`consistency-check` (und damit `--validate`) ruft ihn mit `tracker=None` und meldet ausschließlich 4–6
— netzwerkfrei, wie die Baseline verlangt. `sync.py --labels --check` ruft **dasselbe** Modul mit
einem Tracker und meldet dann alle sechs IDs. Der Nachweis, dass die sechs IDs existieren und über
beide Pfade abgedeckt sind, ist ein Test, der in der Offline-Suite 4–6 und im `--labels --check`-Test
alle sechs IDs sieht (`test_all_six_rule_ids_reported_with_tracker`, Plan T23/T24). Damit ist AC-5
erfüllt, ohne `--validate` Netzwerk zu geben (Q6).

Der Check ist **still**, wenn `issue-conventions.enabled: false` (AC-9).

### 4.8 Admin-UI

Neue Sektion „Issue labels": Achsen-Liste mit `enabled`-Schalter, Wert-Tabelle (Name, Farbe, Beschreibung), Commit-Type-Mapping, Adapter-Auswahl, Button **„Show diff"** (führt den Dry-Run-Resolver aus) und `--explain`-Ansicht mit `source`. `issue-conventions` muss in `PROJECT_WRITABLE_SECTIONS` (`scripts/admin-server.py:234-259`) aufgenommen werden (AC-21); der Schreibpfad ist `PUT /api/config/project/section` (`scripts/admin-server.py:5252,5271`).

### 4.9 Generierte Doku und optionale Tracker-Templates

- `docs/issue-labels.md`: aus **demselben** Resolver erzeugt; enthält alle aktiven Achsenwerte mit Label-Namen, Beispiel und Anwendungsregel (AC-22) sowie einen Abschnitt **„Nicht Teil der Taxonomie"** mit den Triage-Labels (§4.10, D15). Datei-Set: **`project-docs`** (§11.1, für #1186 relevant).
- **DECIDED 2026-11-09 (D11 / Q4) — die Datei ist drift-geprüft.** `docs/issue-labels.md` wird in
  `.meta-config/generated-file-hashes.json` registriert (explizite Root-Level-Registrierung analog
  `PLATFORM_DEFAULTS_RESOLVED_REL`, `scripts/lib/generated_file_drift.py:49`, Scan `:383-393`,
  Capture `:535-537`). Konsequenz: manuelle Edits werden beim nächsten Sync **überschrieben** (mit
  `.sync-backup-*`-Sicherung) und als Drift gemeldet; wer den Inhalt ändern will, ändert die
  Taxonomie, nicht die Datei. Dieselbe Regel wird in #957 für die PR-Templates gespiegelt — **eine**
  Antwort, nicht zwei. Die `project-docs`-Klassifizierung aus #1186 bleibt davon unberührt (Datei-Set
  ≠ Drift-Ownership).
- Optional, `mode: off` per Default: `.github/ISSUE_TEMPLATE/<type>.yml`, `.gitlab/issue_templates/<Type>.md`, `.gitea/ISSUE_TEMPLATE/<type>.md` — nur wenn das Projekt opt-in setzt; handgeschriebene Templates werden nie überschrieben.
- **DECIDED 2026-11-09 (D12 / Q8) — Template-Schalter als geschlossener Unterabschnitt.**
  `issue-conventions.templates: {mode: off|scaffold|manage, force: bool}` (IC-1). Semantik:
  `off` (Default) schreibt nichts; `scaffold` legt **nur fehlende** Dateien an und lässt jede
  bestehende Datei unangetastet; `manage` legt fehlende Dateien an **und** aktualisiert Dateien, die
  unseren Marker tragen. Eine Datei ohne Marker wird nur mit `force: true` überschrieben (Default
  `false`). Erzeugt wird ausschließlich, was die Capability des Adapters deckt (`issue-forms` /
  `issue-templates`, §4.5).

### 4.10 Rollen-Templates

Sechs generierte Platzhalter ersetzen die lokalen Tabellen (drei aus der Achsen-Auflösung, zwei
aus Titel-/Keyword-Feldern, einer als Aktivierungs-Flag):

| Platzhalter | Inhalt |
|---|---|
| `{{ISSUE_TAXONOMY_TABLE}}` | drei Achsen mit Werten, Beschreibungen, projizierten Label-Namen |
| `{{ISSUE_LABEL_MAP}}` | Commit-Type → Issue-Type (D5) + Single-Value-Regel + Create-Policy (IC-6/§4.11) |
| `{{ISSUE_TRIAGE_LABELS}}` | **Nicht-Taxonomie-Labels** (`triage`, `needs-info`) aus der Framework-Konstante `TRIAGE_LABELS`; bewusst keine vierte Achse (D2, D15) |
| `{{ISSUE_TAXONOMY_ENABLED}}` | `"true"`/`"false"` der aufgelösten Sektion — erlaubt Rollen einen bedingten Satz („Labels stammen aus der Taxonomie") ohne Literal; bei `false` rendert der Block den Legacy-Text |
| `{{ISSUE_TITLE_FORMAT}}`, `{{ISSUE_CLOSING_KEYWORDS}}` | aus derselben Auflösung (`{{ISSUE_LANGUAGE}}` bleibt, `scripts/lib/config.py:2720-2722`) |

Alle sechs neuen Variablen (`{{ISSUE_LANGUAGE}}` bleibt unverändert) sind Teil des Spec-Vertrags und **müssen** in der Platzhalter-Allow-List
registriert werden (`scripts/lib/consistency/placeholders.py:114-123`). `ISSUE_TRIAGE_LABELS` und
`ISSUE_TAXONOMY_ENABLED` waren in Revision 1 nur im Plan (T9) genannt — hier nachgezogen (WARN
aus dem Review).

Konsumenten: `feedback.md` (§3-Matrix, `:41-48`), `meta-feedback.md` (§4, `:46-48`), `bug-feature-analyzer.md` (Label-Schema `:89`), `git.md` (bestehender Block `:149-151`). Eine Rolle, die ein Label außerhalb der Taxonomie anwendet, ist ein **Sync-Zeit-Fehler** (Regel 4/5) — genau der Mechanismus, der die heutige Dreiteilung verhindert hätte.

**DECIDED 2026-11-09 (D15 / Q7) — Triage-Labels sind Nicht-Taxonomie.** `render_triage_labels()`
liefert `triage` und `needs-info` aus einer **Framework-Konstante** (`TRIAGE_LABELS`, in
`scripts/lib/issue_conventions.py`), nicht aus der Projekt-Taxonomie und nicht aus einem
Projekt-Override. Sie sind weder eine vierte Achse (D2 bleibt unverändert) noch Teil des
Soll-Label-Sets: der Sync legt sie nie an, `prune` löscht sie nie, und Regel 4 des
Consistency-Checks nimmt sie von der Literal-Prüfung aus, weil sie nicht aus `taxonomy.*` stammen.
`docs/issue-labels.md` führt sie in einem eigenen Abschnitt **„Nicht Teil der Taxonomie"** mit
Begründung (Status/Triage statt Klassifikation). Rolle ist `bug-feature-analyzer` (T13); die
AC-6-Interpretation („kein Taxonomy-Literal im Template") schließt die beiden Triage-Labels
ausdrücklich **ein**, weil sie über den Platzhalter kommen.

### 4.11 Betriebskanten

**DECIDED 2026-11-09 (D9 / Q1) — Präzedenzkette der Repository-Identität.** Die Identität
(`{owner}/{repo}` für GitHub/Gitea, `project_id` für GitLab) wird in genau dieser Reihenfolge
aufgelöst, und die erste **nicht-leere, parsebare** Quelle gewinnt:

1. `issue-conventions.repository.{owner,repo}` (bzw. `project-id`) — Projekt-Override, höchste Priorität,
   deckt Fork-Workflows ab und ist der einzige Weg ohne Git-/CI-Zugriff.
2. `git.remote-url` — die vier Formen `https://…git`, `git@host:owner/repo.git`, GitLab-Subgruppe
   (`project_id` = URL-encoded `group/sub/repo`), Gitea-Pfadform; `owner`/`repo` werden hieraus
   **abgeleitet**, nicht zweitkonfiguriert (AC-16).
3. CI-Env — `GITHUB_REPOSITORY` (`owner/repo`) und `CI_PROJECT_PATH` (GitLab, `group/sub/repo` →
   `project_id`). Eine Env-Quelle, die nicht dem erwarteten `owner/repo`-Muster entspricht, gilt als
   **unparsbar** und wird übersprungen (nicht als halbe Identität akzeptiert).

Erst wenn **alle drei** Quellen leer **oder** unparsbar sind, bricht der Lauf mit **einem** harten
Fehler (`IssueConfigError`, Exit 2, kein API-Call) ab. Die Meldung nennt **alle drei Wege** namentlich
(`issue-conventions.repository.{owner,repo}`, `git.remote-url`, `GITHUB_REPOSITORY`/`CI_PROJECT_PATH`)
und gibt **nie** einen leeren `owner` oder `repo` aus — weder im Text noch in der Diff-/Explain-Ausgabe.
Schema, Parser, Fehlermeldung und Tests liegen zusammen in Plan T15; AC-16 bleibt wörtlich unverändert.
- **`--apply` ist nicht transaktional:** jeder Aufruf ist eigenständig; bei Fehler weiter mit den restlichen Labels, Ergebnis-Tabelle, Exit 1, **kein Rollback**, kein Delete-Versuch. `401/403` bricht nach dem **ersten** Fehlschlag ab (AC-18/AC-19).
- **Label fehlt beim Anlegen:** `create.on-missing-label: warn-and-omit | create | fail`, Default `warn-and-omit` (AC-17).
- **Namensgrenzen vor dem ersten API-Call:** Adapter-Defaults `label-case` (`lower`), `max-length` (`50`), `allowed-pattern`; Verstoß schlägt beim **Resolve** fehl, nicht als 422 mitten im Apply (AC-20).
- **Label-Namen sind URL-Bestandteile, keine URL-Segmente (RVW-1188-01):** `{name}` wird beim Bau der
  Request-URL mit `urllib.parse.quote(name, safe="")` eingesetzt. `type/bug` wird damit zu
  `.../labels/type%2Fbug`; ohne Quoting liefert GitHub/GitLab/Gitea 404 (Pfad-Split) oder 422.
  Umgekehrt bleibt der **projizierte** Name (`type/bug`) unkodiert im Soll-Set, im Diff, im Manifest
  und in allen Meldungen — kodiert wird ausschließlich die URL. Ein Test mit `type/bug` **und**
  `area/core` gegen den Mock-Tracker pinnt beides.
- **Numerische IDs statt Namen, wo die API sie verlangt (RVW-1188-01):** Gitea adressiert
  `PATCH`/`DELETE /repos/{owner}/{repo}/labels/{id}` mit einer Zahl, nicht mit dem Namen. Der Adapter
  deklariert dafür `ids: { op: list, key: "id" }`; der Executor löst die Name→ID-Map **einmal pro Lauf**
  aus dem `list`-Response auf (kein Zusatz-Call pro Label). Ohne diese Auflösung ist `--apply` auf
  Gitea nicht idempotent (jeder Lauf würde neu anlegen) und `--check` meldete Dauer-Drift.
- **`list` wird vollständig gelesen:** Adapter deklarieren `pagination: { param, size-param, size }`;
  der Executor blättert, bis eine Seite weniger Einträge als `size` liefert. Eine abgeschnittene
  erste Seite würde Labels als „fehlend" melden und `--apply` zu Duplikat-`create`-Aufrufen treiben.
- **`prune` braucht ein Manifest (RVW-1188-04):** Löschkandidaten stammen ausschließlich aus dem
  persistierten Soll-/Hash-Manifest früherer Läufe (IC-8) oder aus `sync.prune-allow`. Der eigene
  Präfix ist **kein** Löschkriterium mehr — siehe IC-5.
- **Rate-Limit/HTTP-Robustheit — DECIDED 2026-11-09 (D14 / Q2):** Genau **ein** Retry, und nur bei
  `429`. Die Wartezeit kommt aus `Retry-After` (Sekunden oder HTTP-Datum), ist **gedeckelt** (Cap
  30 s; fehlender/unparsbares Header ⇒ 1 s) und wird über eine injizierbare `sleep`-Funktion
  abgewartet, damit Tests deterministisch bleiben (kein echtes Warten). `5xx` und Timeouts werden
  **nicht** wiederholt: Fehler sammeln, restliche Labels weiter, Ergebnis-Tabelle, Exit 1 (AC-18).
  `401`/`403` brechen unverändert nach dem ersten Fehlschlag ab (AC-19). Kein Backoff, kein Retry
  über Labels hinweg, keine Retry-Konfiguration in `project.yaml`.

### 4.12 Transport-Härtung (Secret-Exfiltration)

Ein Projekt-Override von `base-url`/`api.*`/`auth.header` ist eine Angriffsfläche: wer
`.meta-config/project.yaml` in einem PR ändern darf, könnte `--labels --check` im CI dazu bringen,
den Token an einen fremden Host zu schicken. Deshalb sind die folgenden Regeln **Code, nicht
Konfiguration** (RVW-1188-05):

| # | Regel | Durchsetzung | Fehlerfall |
|---|---|---|---|
| **H-1** | `https` ist Pflicht; `http` nur für Loopback (`127.0.0.1`, `[::1]`, `localhost`) | Resolve-Zeit | `IssueConfigError`, Exit 2, **kein** HTTP-Call |
| **H-2** | Scheme und Host sind durch das Projekt **unveränderlich**: `platform-overrides.<adapter>.base-url` darf nur den Pfad ändern (Vergleich gegen den Framework-Wert, inkl. `GITEA_URL`-Expansion) | Resolve-Zeit | `IssueConfigError`, Meldung nennt beide Hosts, nie einen Token |
| **H-3** | `api.*.path` ist relativ: `^/`, kein Schema, kein `//`-Host-Escape, kein `..` | Adapter-Load | `IssueConfigError` |
| **H-4** | `{name}`/`{id}` werden pro Pfad-Segment mit `quote(..., safe="")` eingesetzt | Transport | — |
| **H-5** | Redirects werden **nicht** verfolgt (jede 3xx-Antwort ist ein Fehler); der Auth-Header geht nur an den gepinnten Host | Transport | `failed`-Eintrag, Exit 1, Auth nie an den Redirect-Zielhost |
| **H-6** | `auth.header` muss den Platzhalter `{token}` enthalten; ein Header ohne `{token}` (literales Credential) ist ein Config-Fehler | Adapter-Load | `IssueConfigError` |
| **H-7** | Manifest, Ausgabe, Log, Doku enthalten keinen Token | Tests | — |

**Warum H-2 ausreicht:** Der Framework-Host ist für `github`/`gitlab` konstant und für `gitea`
env-abhängig (`{GITEA_URL}`). In allen drei Fällen kommt der Host **nicht** aus der
PR-änderbaren Projektdatei. Ein Projekt, das einen anderen Host braucht, ändert die Env-Variable
(Operator-Hand) oder der Adapter wird als Framework-Änderung aufgenommen — nie per PR-Override.
Restrisiko: ein Fork, der `.meta-config/project.yaml` **und** die Env-Variable kontrolliert, ist
ein vertrauenswürdiger Operator, kein Angreifer (siehe Risiko-Tabelle).

---

## Interface Contracts (öffentliche Verträge)

Alle Verträge sind implementierungsbindend; Abweichungen brauchen eine Spec-Revision.

### IC-1 Schema-Sektion (`config/project-config.schema.json`)

```jsonc
"issue-conventions": {
  "type": "object",
  "additionalProperties": false,          // AC-1: geschlossen, Tippfehler sind Fehler
  "description": "Declarative issue-label taxonomy ... (single source of truth)",
  "properties": {
    "enabled": { "type": "boolean", "default": false },
    "preset": { "type": "string", "default": "default" },
    "adapter": { "type": "string", "default": "inherit" },   // inherit → git.platform
    "defaults": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "separator": {
          "type": "object", "additionalProperties": false,   // K2: einzige kanonische Form
          "properties": { "single": { "type": "string" }, "multi": { "type": "string" } }
        },
        "language": { "type": "string", "default": "english" },
        "title-format": { "type": "string", "default": "{type}: {description}" },
        "closing-keywords": { "type": "array", "items": { "type": "string" } }
      }
    },
    "taxonomy": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "type":     { "$ref": "#/$defs/taxonomyAxis" },
        "area":     { "$ref": "#/$defs/taxonomyAxis" },
        "priority": { "$ref": "#/$defs/taxonomyAxis" }
      }
    },
    "platform-overrides": {
      "type": "object",                        // AC-14 Stufe 1 — im Issue-YAML-Sketch NICHT enthalten, hier bewusst deklariert
      "description": "Einziger Ort für Projekt-Overrides pro Adapter: Inhalt (Stufe 1) UND Transport (RVW-1188-03)",
      "additionalProperties": {                // Schlüssel = Adapter-ID (offen: D3, vierter Tracker)
        "type": "object",
        "additionalProperties": false,         // Wert = geschlossen (AC-1)
        "properties": {
          "taxonomy":  { "type": "object", "additionalProperties": false,
                         "properties": { "type":     { "$ref": "#/$defs/taxonomyAxis" },
                                         "area":     { "$ref": "#/$defs/taxonomyAxis" },
                                         "priority": { "$ref": "#/$defs/taxonomyAxis" } } },
          "mapping":   { "type": "object", "additionalProperties": { "type": "string" } },
          "base-url":  { "type": "string" },   // nur Pfad-Änderung erlaubt (§4.12 H-2)
          "api":       { "$ref": "#/$defs/adapterApi" },
          "ids":       { "$ref": "#/$defs/adapterIds" },
          "pagination":{ "$ref": "#/$defs/adapterPagination" },
          "auth": { "type": "object", "additionalProperties": false,
                    "properties": { "header": { "type": "string" } } },   // nur Header-Template, nie `env`/Token
          "defaults":  { "$ref": "#/$defs/adapterDefaults" }
        }
      }
    },
    "mapping": { "type": "object", "additionalProperties": { "type": "string" } },
    "repository": {
      "type": "object", "additionalProperties": false,     // D9: Stufe 0 der Identitäts-Präzedenz
      "description": "Projekt-Override der Repository-Identität; schlägt git.remote-url und CI-Env (D9, §4.11)",
      "properties": {
        "owner": { "type": "string" }, "repo": { "type": "string" },
        "project-id": { "type": "string" }                 // GitLab: URL-encoded group/sub/repo
      }
    },
    "templates": {
      "type": "object", "additionalProperties": false,       // D12: geschlossener Unterabschnitt für §4.9
      "description": "Optionale Tracker-Templates; off = nichts, scaffold = nur fehlende, manage = auch generierte",
      "properties": {
        "mode":  { "enum": ["off", "scaffold", "manage"], "default": "off" },
        "force": { "type": "boolean", "default": false }     // nur nötig, um Dateien ohne Marker zu überschreiben
      }
    },
    "create": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "on-missing-label": { "enum": ["warn-and-omit", "create", "fail"], "default": "warn-and-omit" }
      }
    },
    "sync": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "prune": { "type": "boolean", "default": false },
        "prune-allow": { "type": "array", "items": { "type": "string" }, "default": [] },  // IC-5: explizite Lösch-Erlaubnis
        "create-boards": { "type": "boolean", "default": false }
      }
    },
    "enforcement": {
      "type": "object", "additionalProperties": false,
      "properties": {
        "unknown-label": { "enum": ["error", "warn"], "default": "error" },
        "missing-type": { "enum": ["error", "warn", "off"], "default": "warn" },
        "single-axis-per-issue": { "enum": ["error", "warn", "off"], "default": "error" }
      }
    }
  }
}
```

`#/$defs/taxonomyAxis` = `{ enabled: boolean, cardinality: "single"|"multi", color: string, label-case: string, max-length: integer, allowed-pattern: string, values: { <name>: { color, description } } }` mit `additionalProperties: false`.

`#/$defs/adapterApi` = `{ list|create|update|delete: { method, path, body?, id-from? } }` (geschlossen;
`path` relativ, §4.12 H-3). `#/$defs/adapterIds` = `{ op: string, key: string }`.
`#/$defs/adapterPagination` = `{ param: string, size-param: string, size: integer }`.
`#/$defs/adapterDefaults` = `{ separator: { single, multi }, color-format, label-case, max-length, allowed-pattern }`
— dieselbe Form wie `adapters.<id>.defaults` in IC-3, damit Projekt- und Framework-Wert deckungsgleich sind.

> **`$defs` unter Draft-07 (Review-Auflösung K6).** Die Skizzen dieses Dokuments nutzen `$defs`,
> weil das Ist-Schema `config/project-config.schema.json` selbst `draft-07` deklariert (`:2`) und
> dennoch `$defs` verwendet (`:2855`). Ein JSON-Pointer (`#/$defs/…`) löst in beiden Fällen auf
> (funktional harmlos, Szenario A18); `definitions` wäre nur bei einem gleichzeitigen Wechsel des
> Gesamtschemas richtig. Die neuen Skizzen bleiben deshalb **konsistent mit dem Ist-Schema**.

Vertragsregeln:

1. `additionalProperties: false` gilt **für diese Sektion und alle ihre Untersektionen** (AC-1). Ein unbekannter Schlüssel ist ein Validierungsfehler, kein stiller Default. Einzige Ausnahme: der **Adapter-ID-Schlüssel** unter `platform-overrides` bleibt offen (D3 — ein vierter Tracker ist Daten, kein Schema-Änderungsfall); der Wert je Adapter ist geschlossen.
2. Die Sektion ist **additiv**; top-level bleibt es bis #1141 bei `additionalProperties: true` (`config/project-config.schema.json:2854`) — siehe Konfliktfläche 11.
3. Reaktivierung des Golden-Tests: `enabled: false` (oder Sektion fehlt) ⇒ **byte-identische** Ausgabe zu heute (AC-9).

### IC-2 Preset-Datei (`config/issue-conventions-presets.yaml`)

Pflichtform (Werte aus dem Issue-Body, `Presets`-Abschnitt; Farben/Beschreibungen sind Preset-Daten):

```yaml
presets:
  default:
    taxonomy:
      type:
        enabled: true
        cardinality: single
        color: "ededed"
        values:
          bug:           { color: "d73a4a", description: "Reproducible misbehaviour" }
          feature:       { color: "0e8a16", description: "New capability" }
          improvement:   { color: "a2eeef", description: "Improve an existing capability" }
          documentation: { color: "0075ca", description: "Docs missing, outdated or confusing" }
          question:      { color: "d876e3", description: "Needs clarification" }
          security:      { color: "b60205", description: "Security-relevant" }
          maintenance:   { color: "fef2c0", description: "Chore / tech debt" }
      area:
        enabled: false
        cardinality: multi
        color: "c5def5"
        values: {}                    # ein Projekt füllt diese Achse
      priority:
        enabled: true
        cardinality: single
        color: "fbca04"
        values:
          P0: { color: "b60205", description: "Hotfix — production broken" }
          P1: { color: "d93f0b", description: "Next release" }
          P2: { color: "fbca04", description: "Planned" }
          P3: { color: "0e8a16", description: "Maybe" }
    mapping:
      feat: feature
      fix: bug
      docs: documentation
      chore: maintenance
      refactor: improvement
      perf: improvement
      test: maintenance
  minimal:                            # nur die Achse, die Triage filterbar macht
    taxonomy:
      type: { enabled: true, cardinality: single, values: { bug: { color: "d73a4a", description: "Reproducible misbehaviour" }, feature: { color: "0e8a16", description: "New capability" } } }
      area: { enabled: false, cardinality: multi, values: {} }
      priority: { enabled: false, cardinality: single, values: {} }
  conventional:                       # D5-Mapping ohne eigene Achsen-Definition
    mapping:
      feat: feature
      fix: bug
      docs: documentation
      chore: maintenance
      refactor: improvement
      perf: improvement
      test: maintenance
platform:
  gitlab:  { defaults: { separator: { single: "::", multi: "-" }, color-format: "#{color}" } }
  github:  { defaults: { separator: { single: "/",  multi: "/"  }, color-format: "{color}" } }
  gitea:   { defaults: { separator: { single: "/",  multi: "/"  }, color-format: "#{color}" } }
```

Vertrag: zwei **Sektionen**, `presets` (Inhalt) und `platform` (Projektion). Keine Bedingungslogik, keine Referenzen auf Python-Symbole, kein Preset-Name, der im Code vorkommt.

`platform.<adapter>` steht auf **Stufe 4** der Präzedenz (§4.3) und schlägt damit `presets.<name>`
(Stufe 5) — so verlangt es AC-14. Es führt ausschließlich Projektionsschlüssel
(`separator`, `color-format`); Inhalte (Achsen, Werte, `mapping`) kommen aus `presets`.

### IC-3 Adapter-Datei (`config/issue-adapters.yaml`)

```yaml
adapters:
  github:
    kind: http
    auth: { env: GITHUB_TOKEN, header: "Authorization: Bearer {token}" }
    base-url: "https://api.github.com"
    defaults: { separator: { single: "/", multi: "/" }, color-format: "{color}",
                label-case: lower, max-length: 50, allowed-pattern: "^[a-z0-9][a-z0-9/_-]*$" }
    pagination: { param: page, size-param: per_page, size: 100 }
    api:
      list:   { method: GET,    path: "/repos/{owner}/{repo}/labels" }
      create: { method: POST,   path: "/repos/{owner}/{repo}/labels",
                body: { name: "{name}", color: "{color}", description: "{description}" } }
      update: { method: PATCH,  path: "/repos/{owner}/{repo}/labels/{name}",
                body: { new_name: "{name}", color: "{color}", description: "{description}" } }
      delete: { method: DELETE, path: "/repos/{owner}/{repo}/labels/{name}" }
    capabilities: [labels, issue-labels, issue-forms]
  gitlab:
    kind: http
    auth: { env: GITLAB_TOKEN, header: "PRIVATE-TOKEN: {token}" }
    base-url: "https://gitlab.com/api/v4"
    defaults: { separator: { single: "::", multi: "-" }, color-format: "#{color}" }
    pagination: { param: page, size-param: per_page, size: 100 }
    api:
      list:   { method: GET,    path: "/projects/{project_id}/labels" }
      create: { method: POST,   path: "/projects/{project_id}/labels",
                body: { name: "{name}", color: "#{color}", description: "{description}" } }
      update: { method: PUT,    path: "/projects/{project_id}/labels/{name}" }
      delete: { method: DELETE, path: "/projects/{project_id}/labels/{name}" }
    capabilities: [labels, scoped-labels, issue-templates]
  gitea:                       # deckt Forgejo / Codeberg
    kind: http
    auth: { env: GITEA_TOKEN, header: "Authorization: token {token}" }
    base-url: "{GITEA_URL}/api/v1"     # Host kommt aus der Env, nicht aus project.yaml (§4.12 H-2)
    defaults: { separator: { single: "/", multi: "/" }, color-format: "#{color}" }
    pagination: { param: page, size-param: limit, size: 50 }
    ids: { op: list, key: "id" }       # Gitea adressiert update/delete numerisch (RVW-1188-01)
    api:
      list:   { method: GET,    path: "/repos/{owner}/{repo}/labels" }
      create: { method: POST,   path: "/repos/{owner}/{repo}/labels",
                body: { name: "{name}", color: "#{color}", description: "{description}" } }
      update: { method: PATCH,  path: "/repos/{owner}/{repo}/labels/{id}" }
      delete: { method: DELETE, path: "/repos/{owner}/{repo}/labels/{id}" }
    capabilities: [labels, issue-templates]
```

Vertragsregeln:

1. **Capability-Flags, keine Provider-Namen.** Kein `if adapter == "gitlab"`; die Verzweigung lautet `"scoped-labels" in capabilities`. Der bestehende Check `scripts/lib/consistency/provider_literals.py` gilt auch für den neuen Code.
2. **Separator pro Kardinalität**, nicht global: `single`-Achsen dürfen einen Scoped-Separator nutzen, `multi`-Achsen nie — sonst ersetzt auf GitLab das zweite `area::x` das erste (AC-2b).
3. **Ein neuer Tracker ohne Python.** Ist eine API nicht in dieser Form ausdrückbar (z. B. Jira-Components), ist `kind: plugin` mit Skriptpfad unter `scripts/adapters/` der dokumentierte Ausweg.
4. Ein synthetischer vierter Adapter, **nur** in YAML/Fixture definiert, muss im Test funktionieren (AC-3).
5. **`{name}` in einem Pfad ist immer URL-kodiert** (`quote(name, safe="")`); die Kodierung passiert im Executor, nicht in der Projektion. `{id}` ist nur zulässig, wenn der Adapter `ids` deklariert; der Wert kommt aus der einmal pro Lauf aufgelösten Name→ID-Map des `list`-Response (RVW-1188-01).
6. **`{name}`/`{id}`/`{owner}`/`{repo}`/`{project_id}` sind die einzigen Pfad-Platzhalter.** Ein Pfad mit `{token}` oder einem Env-Namen ist ein Config-Fehler; Env-Expansion ist ausschließlich in `base-url` erlaubt (`{GITEA_URL}`, §4.12 H-2).
7. **`list` muss paginierbar sein** (`pagination`); fehlt der Block, wird genau eine Seite gelesen und `--check` warnt `warning: pagination-undeclared`.
8. **`base-url` ist `https`** (Ausnahme Loopback) und ihr Host ist projektseitig unveränderlich (§4.12 H-1/H-2); `api.*.path` ist relativ (§4.12 H-3); Redirects werden nicht verfolgt (§4.12 H-5).
9. **`auth.header` enthält `{token}`** und sonst kein Credential-Literal (§4.12 H-6); `ids`/`pagination`/`api` dürfen per `platform-overrides.<adapter>` überschrieben werden, `auth.env` nicht (IC-1/IC-6).

### IC-4 CLI-Vertrag

| Aspekt | Vertrag |
|---|---|
| Flags | `--labels`, `--labels --apply`, `--labels --check`, `--labels --explain` (kombinierbar: `--check` + `--explain` zulässig; `--apply` + `--check` ist ein Nutzungsfehler) |
| Dry-Run-Default | ohne `--apply` wird **nie** geschrieben (D4) |
| Exitcodes | `0` = sauber/erfolgreich · `1` = Drift (`--check`) **oder** Teilfehler (`--apply`) · `2` = Resolve-/Config-Fehler (nichts geschrieben, **kein** API-Call) |
| Ausgabe | Diff-Zeilen `create <label>` / `update <label>` / `no-op <label>`, danach Summenzeile; `--explain` zeilenweise `<key> ← <source>` |
| Idempotenz | zweiter `--apply`-Lauf ohne Änderung ⇒ ausschließlich `no-op`, Exit 0 (AC-4). Setzt vollständiges `list` (Pagination) und — wo nötig — die Name→ID-Map voraus; ohne beides wäre der zweite Lauf ein Duplikat-`create` (RVW-1188-01) |
| Zustands-Schreiben | nur `--apply` schreibt `.meta-config/issue-labels-state.json` (IC-8); `--labels`, `--check` und `--explain` sind strikt lesend |
| Commit (D13) | **kein** Auto-Commit aus dem CLI-Pfad. `--apply` schreibt und druckt die geänderte Datei; der Commit bleibt beim `git`-Aufruf (Commit-Authority). CI-`--apply`-Jobs committen **nie** — sie schreiben nur, der nächste Mensch- oder Job-Schritt committet |
| Secret-Freiheit | Ausgabe, Logs und generierte Dateien enthalten **keinen** Token-Wert (AC-8); Transport-Regeln H-1…H-7 (§4.12) sind nicht abschaltbar |

### IC-5 `prune`-Semantik

- Default `sync.prune: false`; **kein** Delete ohne explizites Opt-in (AC-10).
- **Der eigene Präfix ist kein Löschkriterium (RVW-1188-04).** Ein Label wie `type/needs-design`
  liegt im Präfix `type/`, ist aber ein Menschen-Label. Löschkandidat ist ein Tracker-Label nur dann,
  wenn **alle drei** Bedingungen gelten:
  1. `sync.prune: true`,
  2. es ist **nicht** im aktuellen Soll-Set, und
  3. es steht im persistierten Soll-/Hash-Manifest eines früheren Laufs (IC-8) **oder** in
     `sync.prune-allow`.
- Ein Label im eigenen Präfix, das nicht im Manifest und nicht in `prune-allow` steht, erzeugt
  höchstens `info: prune-candidate-unowned <name>` — nie ein `delete`.
- **Deaktivierte Achsen löschen nie** (§4.4): Labels einer Achse mit `enabled: false` sind **nicht**
  Teil der Soll-Menge, aber auch **keine** Löschkandidaten, selbst wenn sie im Manifest stehen. Der
  Executor bildet die Kandidatenmenge deshalb als
  `(Manifest ∖ desired) ∖ labels(inaktiver Achsen)` — nur Manifest-Einträge, die **nicht** im Soll
  liegen **und nicht** zu einer deaktivierten Achse gehören. Die Achsen-Zugehörigkeit dient dabei
  ausschließlich der **Ausnahme** (nie der Auswahl) und wird über den projizierten Achsen-Präfix
  `<axis><separator>` aus dem Adapter-Separator bestimmt; sie braucht **keine** `values`-Auflösung
  der inaktiven Achse. `desired` enthält die inaktive Achse ohnehin nicht (Achsen-Gate §4.4), die
  Subtraktion entfernt also genau den Fall „Manifest-Eintrag einer deaktivierten Achse"
  (RVW2-1188-01).
- Fehlt das Manifest (erster Lauf, neuer Klon, Manifest gelöscht) **und** ist `sync.prune-allow`
  leer, gibt es **null** Löschkandidaten (safe default) und `info: prune-needs-manifest`.
  `sync.prune-allow` wirkt unabhängig vom Manifest (Bedingung 3 oben ist ein ODER): ein dort
  genanntes Label ist auch ohne Manifest löschbar, sofern `sync.prune: true` gilt (RVW2-1188-01).
- **DECIDED 2026-11-09 (D10 / Q3) — kein Rename in v1.** Ein neuer Wert erzeugt `create <neu>`; das
  alte Label bleibt im Tracker **unangetastet** und wird als `info: rename-candidate <alt>` gemeldet
  (die `alt`-Seite liefert das Manifest, IC-8). Es gibt **keinen** `update.new_name`-Aufruf, der aus
  einem Rename-Verdacht entsteht: der alte Wert verschwindet nur aus dem **Soll-Set**, nie aus dem
  Tracker, und `--check` löscht ihn auch nicht. Die Vertragszeile `rename <alt> -> <neu>` bleibt im
  CLI-Vertrag **reserviert** für eine spätere explizite `renames`-Map (eigene Spec-Revision, heute
  nicht in IC-1). Bis dahin ist `rename` ein Ausgabewort, das in v1 **nie** erzeugt wird.
- `--check` löscht nie und meldet gelöschte Kandidaten höchstens als `info`.

### IC-6 Auth-Vertrag

- Auth ausschließlich über `auth.env` (Name einer Env-Variable, Wert aus Environment oder `.env`).
- Ein Projekt-Adapter-Override lebt in `issue-conventions.platform-overrides.<adapter>` und darf
  `base-url` (nur Pfad), `api.*`, `ids`, `pagination`, `auth.header` und `defaults` ändern — **nie**
  `auth.env` und **nie** einen Token-Wert (RVW-1188-03).
- `auth.header` muss `{token}` enthalten. Fehlt der Platzhalter, ist der Wert ein literales
  Credential ⇒ `IssueConfigError` beim Laden (RVW-1188-05, H-6). Ein Test prüft beides: Header ohne
  Platzhalter und Header mit offensichtlichem Token-Literal.
- Der aufgelöste Adapter-Config-Dump enthält nur `auth.env`; ein Test prüft das (AC-8).
- Kein Token in `docs/issue-labels.md`, in Rollen-Templates, in `sync.log`, im Manifest (IC-8) oder
  in Fehlermeldungen.
- Transport-Härtung ist **nicht** konfigurierbar: HTTPS-Zwang (Loopback-Ausnahme), Host-Pinning,
  relative Pfade, keine Redirects, URL-kodierte Pfad-Segmente (§4.12 H-1…H-7).

### IC-7 Ausgabe- und Ownership-Vertrag

- Neu erzeugt: `docs/issue-labels.md` (aus dem Resolver; AC-22) — Datei-Set `project-docs` (§11.1) — sowie optional die drei Template-Familien aus 4.9 (gesteuert über `templates.mode`, IC-1).
- Vorhandene, handgeschriebene Dateien werden **nie** überschrieben; bei Abweichung Warnung, `--force` bzw. `templates.force: true` nur explizit.
- **DECIDED 2026-11-09 (D11 / Q4): `docs/issue-labels.md` gehört in `generated-file-hashes.json`.** Die Datei ist generiert und wird drift-geprüft (Registrierung über eine explizite Root-Level-Ausnahme im Stil von `PLATFORM_DEFAULTS_RESOLVED_REL`, `scripts/lib/generated_file_drift.py:49/383-393/535-537`). Manuelle Edits werden beim nächsten Sync überschrieben und als Drift gemeldet. Dieselbe Regel gilt in #957 für PR-Templates — eine Antwort für beide Ausgabefamilien. Die generierten Tracker-Templates aus 4.9 folgen derselben Regel, sobald `templates.mode` sie erzeugt (Registrierung im selben Baseline-Mechanismus).

### IC-8 Zustands-Manifest (`.meta-config/issue-labels-state.json`)

Einzige lokale Erinnerung des Features — ausschließlich für `prune` (IC-5) und als `alt`-Seite für
Rename-Kandidaten. **Kein** Ist-Zustand des Trackers: der Tracker bleibt die einzige Autorität, der
Diff entsteht weiterhin aus `list` gegen die Soll-Menge.

```jsonc
{
  "version": 1,
  "adapters": {
    "github": {
      "owner/repo": {
        "labels": {
          "type/bug": "sha256:9f2c…",     // hash(name | color | description) nach Projektion
          "area/core": "sha256:1ab…"
        }
      }
    }
  }
}
```

Vertragsregeln:

1. **Schreiben nur bei `--apply`.** Inhalt = die Labels, deren `create`/`update` in diesem Lauf
   erfolgreich war (bei Teilfehler bleiben fehlgeschlagene Einträge aus). `--labels`, `--check`,
   `--explain` schreiben nie.
2. **Versioniert im Repo.** `--check` in CI braucht dasselbe Manifest wie der Produzent; ohne
   Versionierung wäre der CI-Gate blind. Schreibweise: sortierte Schlüssel, eine Zeile pro Label,
   damit Merge-Konflikte auf einzelne Zeilen fallen. Der Commit bleibt beim `git`-Agenten **außerhalb**
   des CLI (D13): `--apply` schreibt und druckt die Datei, committet aber nie selbst; CI-`--apply`-Jobs
   committen ebenfalls nicht.
3. **Keine Secrets, kein Token.** Nur projizierte Namen und Hashes (AC-8).
4. **Additiv pflegbar.** Kein Schema-Zwang für Lesen: fehlt die Datei, gilt „kein Manifest" (IC-5).
5. **Eine Datei pro Projekt**, nicht pro Adapter-Repo — der Repo-Schlüssel (`owner/repo` bzw.
   `project_id`) ist die zweite Ebene.

---

## Datenfluss

```
.git/config / git.remote-url (config)      config/issue-conventions-presets.yaml      config/issue-adapters.yaml
        │                                          │                                        │
        ▼                                          ▼                                        ▼
 [Repository-Identität]  ──►  [Resolver: 7 Stufen + source]  ──►  [Achsen-Gate]  ──►  [Projektion]
        │                            ▲                                                     │
        │                            │  project.yaml: issue-conventions.*                   │
        │                            └─────────────────────────────────────────────────────┤
        │                                                                                  ▼
        │                                                                    ┌─────────────┴─────────────┐
        │                                                                    ▼                           ▼
        │                                                        [Template-Variablen]        [Soll-Label-Set]
        │                                                                    │                           │
        │                                                                    ▼                           ▼
        │                                                     feedback / meta-feedback /      [Diff gegen Tracker]
        │                                                     bug-feature-analyzer / git                │
        │                                                                                     ┌──────────┴─────────┐
        │                                                                                     ▼                    ▼
        │                                                                              Dry-Run-Ausgabe      --apply (HTTP)
        │                                                                                     │                    │
        ▼                                                                                     ▼                    ▼
 [--check in CI] ◄─────────────────────────────────────────────────────────────── [Consistency-Check]   [Tracker = Projektion]
```

Zustands-Eigentümerschaft:

| Zustand | Eigentümer | Persistenz |
|---|---|---|
| Taxonomie-Inhalt | Framework-Preset → Projekt (`project.yaml`) | versioniert im Repo |
| Projektion (Separator, Case, Farbe, Länge) | Adapter-Registry → Projekt-Override | versioniert im Repo |
| Ist-Zustand der Labels | **Tracker** (einzige Autorität) | extern |
| Aufgelöste Werte + `source` | Resolver (berechnet, nicht gespeichert) | flüchtig |
| Prune-Manifest (Soll-Namen + Hashes) | `--apply` (IC-8) | versioniert, `.meta-config/issue-labels-state.json` |
| Rollen-Texte | generierte Templates | versioniert (generiert) |
| Menschliche Doku | `docs/issue-labels.md` | versioniert (generiert) |

**Genau eine State-Datei, und sie ist kein Cache:** `.meta-config/issue-labels-state.json` (IC-8)
enthält ausschließlich die projizierten Label-Namen früherer erfolgreicher `--apply`-Läufe plus
deren Hash. Sie ist die *einzige* lokale Erinnerung, ausschließlich für `prune` maßgeblich, und sie
wird nie zur Diff-Grundlage: der Diff entsteht immer aus `list` gegen die Soll-Menge. Ohne Manifest
gibt es keine **manifest-basierten** Löschkandidaten (IC-5); `sync.prune-allow` wirkt davon
unabhängig. Ein Rename wird in v1 **nicht** durchgeführt (D10): das Manifest liefert nur die
`alt`-Seite für `info: rename-candidate`, die Paarung Alt↔Neu bleibt bis zu einer expliziten
`renames`-Map offen.

---

## 6. Design-Entscheidungen (D1, D2, D4)

### D1 — `type` ist ein Label auf jeder Plattform, kein GitHub Issue-Type

```
DECISION
context: GitHub bietet seit 2025-01 native Issue Types (org-level, REST /orgs/issue-types), die ein Repo-Framework nicht anlegen, nur zuweisen kann.
choice: type wird als Label projiziert (GitHub/Gitea `type/…`, GitLab `type::…`); Issue Types bleiben ungenutzt.
alternatives:
  - Issue Types zusätzlich pflegen → zwei Wahrheiten für dieselbe Klassifikation, org-Rechte nötig, in Consumer-Projekten nicht reproduzierbar (verworfen).
  - Issue Types statt Labels → funktioniert auf GitHub, aber nicht auf GitLab/Gitea; der Adapter-Vertrag bräche auf zwei von drei Plattformen (verworfen).
consequences:
  - einfacher: ein Mechanismus, ein Resolver, ein Drift-Check über alle Tracker; Capability-Erweiterung `issue-types` später ohne Taxonomie-Änderung.
  - schwerer: GitHub-natives "Filter by type", Type-Badge und org-weites Reporting bleiben ungenutzt (dokumentierter Preis).
```

### D2 — Keine `status`-Achse

```
DECISION
context: Best-Practice-Setups führen zusätzlich status/*-Labels, meist bot-verwaltet.
choice: v1 kennt nur type, area, priority; Status bleibt beim Projekt-Board.
alternatives:
  - status als vierte Achse → konkurriert mit dem Board, wird von Hand gesetzt und driftet (Anti-Pattern der recherchierten Quellen, verworfen).
  - status read-only aus dem Board spiegeln → Tracker-API-Abhängigkeit ohne Nutzen für die Rollen-Templates (verworfen).
consequences:
  - einfacher: drei Achsen mit klarer Kardinalität, kleine Oberfläche in Schema, UI und Templates.
  - schwerer: Rollen können den Lifecycle-Zustand nicht aus Labels ableiten; Boards bleiben die Quelle.
```

### D4 — Schreiben nur mit `--apply`, Default ist der Dry-Run-Diff

```
DECISION
context: Ein Label-Sync kann fremde Repos verändern; ein Fehlaufruf darf nicht sofort schreiben.
choice: `sync.py --labels` druckt den Diff und schreibt nichts; `--apply` schreibt; `--check` ist strikt read-only und CI-Gate.
alternatives:
  - Schreiben als Default mit `--dry-run`-Opt-out → widerspricht dem restlichen sync.py-Verhalten und dem Repo-Containment-Prinzip (verworfen).
  - interaktive Bestätigung pro Label → nicht CI-fähig, nicht skriptbar (verworfen).
consequences:
  - einfacher: ein Aufruf ist immer gefahrlos; `--check` ist als Gate nutzbar; Idempotenz ist testbar.
  - schwerer: zwei Aufrufe für einen echten Rollout; `--apply` bleibt nicht transaktional (Teilfehler sind dokumentiert).
```

### D3 / D5 (übernommen, weil AC-2/AC-3 darauf beruhen)

- **D3:** Adapter sind **Daten**; ein vierter Tracker ist Konfiguration. Konsequenz: kein Klassenbaum, keine Provider-Verzweigung, `kind: plugin` als dokumentierter Ausweg.
- **D5:** Das **Commit-Type-Vokabular** bleibt Fundament (`config/conventions-presets.yaml:54`); Issue-Types werden daraus abgeleitet (`mapping`), nicht daneben erfunden.

---

## Nicht-Ziele

- Status-/Lifecycle-Automatisierung, Boards, Milestones.
- Severity als vierte Achse (getrennt von Priority zu halten ist Best Practice).
- Migration bestehender Labels in Consumer-Repos (nur create/update; kein Bulk-Delete).
- Jira in v1 (nur dokumentierter `kind: plugin`-Ausweg).
- GitHub Issue Types (D1).
- Label-Erzwingung auf **Pull Requests** (Taxonomie ist issue-scoped; PR-Labels sind ein Follow-up).
- Provider-spezifische Codepfade (verletzt `provider-agnostic`).

---

## Acceptance Criteria (22)

22 numerierte Kriterien (1–22) plus das im Issue-Body eingeschobene **AC-2b** — zusammen 23 Checkboxen, Text wörtlich aus Issue #1188 übernommen; IDs nur als Trace-Anker ergänzt.

- [ ] **AC-1** — `issue-conventions` is in `config/project-config.schema.json` (`additionalProperties: false`), with `taxonomy.{type,area,priority}`, `mapping`, `adapter`, `sync`, `enforcement`.
- [ ] **AC-2** — `config/issue-conventions-presets.yaml` exists with **two sections**: `presets.<name>` (`default`, `minimal` = type only, `conventional` = D5 mapping) and `platform.<adapter>` (framework platform defaults) — data only, no code paths per preset.
- [ ] **AC-2b** — `config/issue-adapters.yaml` declares `separator: {single, multi}` and `color-format` per adapter, so a `multi` axis on GitLab is projected with `-` while `type`/`priority` use `::` (test asserts no self-replacing scoped label).
- [ ] **AC-3** — `config/issue-adapters.yaml` ships `github`, `gitlab`, `gitea`; a synthetic fourth adapter defined **only** in YAML works in a test fixture (proves D3).
- [ ] **AC-4** — `sync.py --labels` prints a create/update/no-op diff and writes nothing; `--labels --apply` creates the labels; a second run is a no-op (idempotent).
- [ ] **AC-5** — `--labels --check` exits 1 on drift; `consistency-check` reports the six rules above by id.
- [ ] **AC-6** — `feedback`, `meta-feedback`, `bug-feature-analyzer`, `git` all render from `{{ISSUE_TAXONOMY_TABLE}}`/`{{ISSUE_LABEL_MAP}}`; no label literal remains in those templates.
- [ ] **AC-7** — On GitLab (`scoped-labels`) applying a second `type::` label replaces the first; on GitHub/Gitea the same action is refused by the role contract (`single-axis-per-issue: error`) — tested on both capability paths.
- [ ] **AC-8** — No token ever appears in a generated file or log (test asserts the resolved adapter config contains only `auth.env`).
- [ ] **AC-9** — A project with `issue-conventions.enabled: false` renders exactly today's output (golden test).
- [ ] **AC-10** — `prune: false` is the default and a delete requires both `prune: true` and an owned namespace (test).
- [ ] **AC-11** — `taxonomy.area.enabled: false` produces no `area` label, no `area` block in role prompts, an empty diff for that axis, and no drift finding — while `type`/`priority` keep working.
- [ ] **AC-12** — An **enabled axis with empty `values`** is a hard error, as is `issue-conventions.enabled: true` with **no active axis**.
- [ ] **AC-13** — `taxonomy.type.enabled: false` is accepted with a warning naming the best-practice requirement.
- [ ] **AC-14** — Resolution honours all seven levels: a project `platform-overrides.gitlab` value beats the framework `platform.gitlab` default, which beats `presets.default`; `--explain` prints the `source` per axis and value.
- [ ] **AC-15** — A framework platform default that disables an axis is overruled by a project that enables it (project wins, both shown by `--explain`).
- [ ] **AC-16** — Repository identity resolves from `git.remote-url` for all four forms above (https, ssh, `.git` suffix, GitLab subgroup); an unparsable remote fails with the URL in the message and no empty `owner`.
- [ ] **AC-17** — `on-missing-label` works in all three modes; the default `warn-and-omit` creates the issue without the label and emits a warning.
- [ ] **AC-18** — `--apply` with a 500 on the third of five labels: the other four stay applied, a result table is printed, exit code 1, and no delete is attempted.
- [ ] **AC-19** — A 401 aborts after the first failed call (asserted by call count, not by message).
- [ ] **AC-20** — A taxonomy value exceeding `max-length` or violating `allowed-pattern` fails at resolve time, before any API call.
- [ ] **AC-21** — The Admin UI can toggle axes and edit values; "Show diff" runs the dry-run resolver; `issue-conventions` is writable through `PUT /api/config/project/section`.
- [ ] **AC-22** — `docs/issue-labels.md` is generated from the resolver and contains every active axis value with its label name.

### AC-Interpretationen (Review 2026-11-09)

Die AC-Texte bleiben wörtlich (Issue-Übernahme); hier steht, **wie** sie erfüllt werden. Jede
Interpretation ist eine Verschärfung, keine Abschwächung.

| AC | Interpretation | Warum die wörtliche Lesart allein nicht genügt |
|---|---|---|
| **AC-5** | Der Check ist **ein** Modul mit sechs IDs. `consistency-check`/`--validate` ruft ihn mit `tracker=None` (Regeln 4–6, offline); `--labels --check` ruft dasselbe Modul mit Tracker (alle sechs). Nachweis: `test_all_six_rule_ids_reported_with_tracker` sieht sechs IDs über den Tracker-Pfad, die Offline-Suite sieht 4–6. | Wörtlich „consistency-check reports the six rules" wäre nur mit Netzwerk in `--validate` erfüllbar — genau die Verhaltensänderung, die Q6 ausschließt (RVW-1188-06). |
| **AC-6** | Erfüllt ist: **kein Label-Literal mehr im Rollen-Template** — die vier Templates referenzieren ausschließlich Platzhalter, der Alt-Text liegt als `LEGACY_ROLE_BLOCKS` framework-intern (Plan K-1). **Nicht** erfüllt (und bewusst nicht Teil von #1188): die gerenderte Default-Ausgabe enthält weiterhin die Legacy-Tabelle, weil `issue-conventions.enabled` per Default `false` ist. Das ist ein eigenes Folge-Issue **F-5** (§10.2): `enabled`-Default auf `true` + `LEGACY_ROLE_BLOCKS` löschen. Ohne F-5 ist AC-9 (byte-identisch bei `false`) nicht mit AC-6 (kein Literal irgendwo) gleichzeitig erfüllbar. | Wörtlich „no label literal remains in those templates" ist mit K-1 erfüllt, aber die *Wirkung* (niemand sieht je eine hartkodierte Tabelle) erst mit `enabled: true` (RVW-1188-06). |
| **AC-10** | Löschkriterium ist das Manifest (IC-8) bzw. `sync.prune-allow`, **nicht** der eigene Präfix; ein Fremdlabel innerhalb des Präfix (`type/needs-design`) wird nie gelöscht. | Die Präfix-Heuristik war zu grob: sie hätte Menschen-Labels im eigenen Namespace gelöscht (RVW-1188-04). |
| **AC-16** | Reihenfolge wörtlich als Präzedenzkette: `issue-conventions.repository.{owner,repo}` → `git.remote-url` (vier Formen) → CI-Env (`GITHUB_REPOSITORY`, `CI_PROJECT_PATH`). Der harte Fehler greift erst, wenn **alle drei** Quellen leer oder unparsbar sind; die Meldung nennt alle drei Wege und enthält nie einen leeren `owner`. | „derive from `git.remote-url`" allein blockierte den ersten CI-Lauf in genau dem Repo, das den Check einführt (keine `git:`-Sektion, `remote-url` = `""`); die Env-Quelle ist der einzige Weg ohne Shell-Zugriff (D9/Q1). |
| **AC-22** | Die Datei wird nicht nur erzeugt, sondern **drift-geprüft**: Registrierung in `.meta-config/generated-file-hashes.json`; manuelle Edits werden beim nächsten Sync überschrieben und gemeldet. Dieselbe Regel gilt für die PR-Templates aus #957. | „is generated" ohne Baseline hieße: die Datei driftet unbemerkt und die Doku widerspricht dem Resolver (D11/Q4). |
| **AC-6** (Triage) | `triage`/`needs-info` sind **Nicht-Taxonomie-Labels** aus der Framework-Konstante `TRIAGE_LABELS`, gerendert über `{{ISSUE_TRIAGE_LABELS}}`; im Rollen-Template steht kein Literal, und die beiden Werte sind ausdrücklich **nicht** Teil der Taxonomie (keine vierte Achse, D2). | Ohne diese Abgrenzung wäre `bug-feature-analyzer.md:89` entweder ein Regel-4-Verstoß oder eine stille vierte Achse (D15/Q7). |
| **AC-14** | Reihenfolge wörtlich: Projekt-Override → Framework-**Plattform**-Default → Framework-**Preset**; `--explain` zeigt den `source` je Achse und Wert. | §4.3 hatte 4/5 vertauscht und widersprach damit dem AC-Text (RVW-1188-02). |
| **AC-4** | Idempotenz setzt vollständiges `list` (Pagination) und, wo nötig, die Name→ID-Map voraus; ohne beides wäre der zweite Lauf ein Duplikat-`create`. | AC-4 sagt „a second run is a no-op", nicht *warum* es einer ist (RVW-1188-01). |

---

## 9. Risiken

| Risiko | Gegenmaßnahme | Restrisiko |
|---|---|---|
| Löschen von Labels, auf denen Menschen Filter aufgebaut haben | `prune: false` Default; Löschen nur aus Manifest (IC-8) oder `sync.prune-allow`, nie aus dem Präfix (IC-5); Dry-Run zuerst | gering — Manifest-Verlust führt zu **keinem** Löschen |
| Fremdlabel im eigenen Präfix (`type/needs-design`) wird gelöscht | Manifest-/Allowlist-Pflicht (IC-5/IC-8), Test `test_prune_never_deletes_foreign_label_inside_prefix` | sehr gering |
| Manifest ist im Repo nicht versioniert (z. B. `.gitignore`) ⇒ CI-Gate blind, Prune wirkungslos | IC-8/2 (versioniert), Plan T21-Test prüft die Schreib-/Lesekopplung; `.meta-config/` ist nicht ignorierbar (Repo-Containment erlaubt nur `.tmp/`) | gering |
| Merge-Konflikt im Manifest bei parallelen PRs | sortierte Schlüssel, eine Zeile je Label (IC-8/2); Konflikt ist auflösbar durch Neu-Lauf von `--apply` | gering |
| Label-Namen mit `/` erzeugen 404/422 (`type/bug` als Pfadsegmente) | `quote(name, safe="")` im Executor (IC-3/5, §4.12 H-4); Test mit `type/bug` **und** `area/core` | sehr gering |
| Gitea `update`/`delete` braucht numerische ID ⇒ `--apply` nicht idempotent, `--check` Dauer-Drift | `ids: {op: list, key: id}` + Name→ID-Map einmal pro Lauf (IC-3/5, IC-5) | gering |
| Secret-Exfiltration über Projekt-`base-url`, Redirect oder literales `auth.header` | §4.12 H-1…H-7: HTTPS-Zwang, Host-Pinning (Projekt ändert nur den Pfad), keine Redirects, `{token}`-Pflicht im Header; Tests für alle drei Pfade | gering; Restfall = Operator, der Env **und** Projektdatei kontrolliert |
| GitHub Issue Types bleiben ungenutzt (D1) | dokumentierte Abweichung inkl. Preis; Capability `issue-types` später nachrüstbar, Taxonomie unverändert | akzeptiert |
| `multi`-Achse mit Scoped-Separator ⇒ Selbst-Ersetzung auf GitLab | Separator **pro Kardinalität** (IC-3/2); Test in AC-2b | niedrig |
| Framework-Plattform-Default überstimmt still ein Projekt | Stufe 4 schlägt nur vor; Projekt gewinnt (4.3/1), `--explain` zeigt beide; AC-15 pinnt es | niedrig |
| Repo-Identität aus `git.remote-url` ist im eigenen Repo leer (`.meta-config/project.yaml` hat **keine** `git:`-Sektion → `remote-url` = Schema-Default `""`, `config/project-config.schema.json:1753-1757`) | **D9 (entschieden):** Präzedenz `repository.{owner,repo}` → `git.remote-url` → `GITHUB_REPOSITORY`/`CI_PROJECT_PATH`; harter Fehler erst, wenn **alle drei** leer/unparsbar sind, mit einer Meldung, die alle drei Wege nennt und nie einen leeren `owner` ausgibt | gering — lokal genügt `repository.*`, in CI greift die Env |
| Token-Leak in Logs/Artefakten | nur `auth.env` (IC-6), Test AC-8, `_mask` (`scripts/lib/env.py:130`) | gering |
| Adapter-YAML wächst zu einer Programmiersprache | Capability-Flags + `kind: plugin`-Ausweg; keine Bedingungssyntax im Executor | mittel (Design-Disziplin) |
| Rename ohne lokalen Zustand nicht eindeutig erkennbar | **D10 (entschieden):** kein Rename in v1 — neuer Wert ⇒ `create <neu>`, altes Label bleibt, `info: rename-candidate <alt>`; `rename` bleibt für eine spätere explizite `renames`-Map reserviert | gering (kein stilles Umbenennen, kein Löschen) |
| Drift-Baseline für `docs/issue-labels.md` fehlt ⇒ manuelle Edits bleiben unbemerkt | **D11 (entschieden):** Registrierung in `.meta-config/generated-file-hashes.json` (Root-Level-Ausnahme); manuelle Edits werden beim Sync überschrieben und gemeldet; #957 spiegelt die Regel für PR-Templates | gering |
| Kollision `--label`/`--labels` in der CLI | Help-Texte + Finding F-3 | niedrig |

---

## Offene Fragen (alle entschieden — Stand 2026-11-09)

| ID | Frage | Status | Entscheidung (D-Nr) / Stelle |
|---|---|---|---|
| **Q1** | Woher kommt die Repository-Identität, wenn `git.remote-url` leer ist? | **entschieden 2026-11-09** | **D9:** `issue-conventions.repository.{owner,repo}` → `git.remote-url` → CI-Env (`GITHUB_REPOSITORY`, `CI_PROJECT_PATH`); harter Fehler erst, wenn alle drei leer/unparsbar sind (Meldung nennt alle drei Wege, nie leerer `owner`). §4.11, IC-1 `repository`, Plan T15 |
| **Q2** | Retry-/Backoff-Policy bei `429`/`5xx` und Timeout-Wert des Executors. | **entschieden 2026-11-09** | **D14:** genau ein Retry bei `429` mit `Retry-After` (Cap 30 s, injizierbare `sleep`); `5xx`/Timeouts kein Retry, sammeln, Exit 1; `401`-Abbruch unverändert. §4.11, IC-4, Plan T16/T18 |
| **Q3** | Wie wird ein Rename erkannt, wenn der Tracker der einzige Zustand ist? | **entschieden 2026-11-09** | **D10:** kein Rename in v1 — `create <neu>` + altes Label bleibt + `info: rename-candidate <alt>`; `rename`-Zeile bleibt für eine spätere explizite `renames`-Map reserviert (eigene Spec-Revision). IC-5, Plan T17 |
| **Q4** | Gehören `docs/issue-labels.md` und die optionalen Issue-Templates in `generated-file-hashes.json` (Ownership/Drift), oder bleiben sie unmanaged? | **entschieden 2026-11-09** | **D11:** ja — Registrierung in `.meta-config/generated-file-hashes.json`, manuelle Edits werden überschrieben und als Drift gemeldet; dieselbe Regel spiegelt #957 für PR-Templates. IC-7, §4.9, Plan T25 |
| **Q5** | Wo lebt `platform-overrides` in der Sektion — unter `issue-conventions` (Stufe 1 der Präzedenz) oder als Teil von `adapter`? | **entschieden (IC-1)** | Eigener Schlüssel `issue-conventions.platform-overrides.<adapter>`, geschlossen, mit Inhalts- **und** Transport-Schlüsseln (RVW-1188-03) |
| **Q6** | Wird der Check `issue-label-taxonomy` Teil des Standard-Suite-Laufs (`--validate`) oder nur von `--labels --check` aufgerufen? | **entschieden (§4.7, K-5)** | Regeln 4–6 offline in der Suite, Regeln 1–3 nur mit Tracker (`--labels --check`); ein Modul, sechs IDs, zwei Kontexte |
| **Q7** | Sind `triage`/`needs-info` Status-Labels, und wo leben sie? | **entschieden 2026-11-09** | **D15:** Framework-Konstante `TRIAGE_LABELS`, gerendert über `{{ISSUE_TRIAGE_LABELS}}`; in `docs/issue-labels.md` unter „nicht Teil der Taxonomie"; **keine** vierte Achse (D2). §4.10, Plan T13/T25 |
| **Q8** | Wo lebt der `mode`-Schalter für optionale Issue-Templates? IC-1 ist geschlossen und enthält ihn nicht | **entschieden 2026-11-09** | **D12:** `issue-conventions.templates: {mode: off\|scaffold\|manage, force: bool}` als geschlossener Unterabschnitt in IC-1; T30 ist damit Teil der Freigabe. IC-1, §4.9, Plan T1/T30 |
| **Q9** | Wer committet `.meta-config/issue-labels-state.json` nach einem `--apply`-Lauf? | **entschieden 2026-11-09** | **D13:** `--apply` schreibt und druckt die Datei in der Ergebnis-Tabelle, committet nie selbst; der `git`-Schritt committet; CI-`--apply`-Jobs committen **nie**. IC-4/IC-8, Plan T21 |

---

## 10. Backlog-Bugs & Findings

### 10.1 Bestehende Issues — Einordnung

| Issue | Titel (gekürzt) | Einordnung zu #1188 | Begründung |
|---|---|---|---|
| **#1167** | `improvement: unify REQ-ID format across templates and presets and add a format validator` | **unabhängig, aber Datei-nah** | Beide Issues ändern Rollen-Templates (`bug-feature-analyzer.md` ist in #1167 als „ungated REQ wording" gelistet, `:42,84,134`) und `config/conventions-presets.yaml` (`:34`). Kein inhaltlicher Widerspruch; Reihenfolge beliebig, aber nicht parallel editieren. |
| **#1141** | `bug: project config schema silently accepts unknown top-level keys` | **Nachläufer (Wave-Reihenfolge)** | #1141 will top-level `additionalProperties: false` (heute `true`, `config/project-config.schema.json:2854`) bzw. ein Unknown-Key-Finding. AC-1 fordert dasselbe **nur für die neue Sektion**. Beide sind vereinbar; #1141 läuft **nach** #1181 (Reihenfolge `#1187 → #1186 → #1188 → #1181 → #1141`) und muss `issue-conventions` als Property kennen, sonst wird die neue Sektion beim strikten Top-Level abgelehnt. |
| **#957** | `feat: PR-Templates (generic / platform / project override, mit Variablen)` | **Nachbar, gleiche Ausgabefamilie** | #957 Phase 3 nennt „Issue-Templates als Folge-Request" — #1188 ist genau dieser Folge-Request. Beide schreiben unter `.github/` und beide brauchen dieselbe Ownership-/Überschreib-Regel; **D11 entscheidet sie für beide**: Registrierung in `generated-file-hashes.json`. Serialisieren bei jeder `.github/`-Erzeugung und beim Marker-Vertrag. |
| **#1168** | `fix: git agent writes harness Co-Authored-By …` | **unabhängig, gleiche Datei** | Funktional orthogonal (Commit-Trailer vs. Label-Taxonomie), aber beide ändern `agents/1-generic/git.md` (dort Commit-Authority-Block bzw. `:149-151`). Nur Datei-Serialisierung nötig. |

### 10.2 Neue Findings ohne Issue

| Finding | Relevanz | Titelvorschlag | Labels (heutiges Vokabular) | Body-Skizze |
|---|---|---|---|---|
| **F-1** — Die einzige existierende Label-Anweisung des Frameworks ist auf **beiden** Zielplattformen falsch: `labels.namespace: "type: {type}"` (`config/conventions-presets.yaml:56`) wird als `type: <type>` gerendert (`scripts/lib/conventions.py:285,290`). GitHub kennt die Konvention `type/…`, GitLab verlangt für Scoped-Semantik `::`; `type: bug` ist dort ein **gewöhnliches** Label ohne Eindeutigkeitsgarantie. | **hoch** — jedes Projekt, das der einzigen vorhandenen Anweisung folgt, erhält ein Schema, das die gewünschte „genau ein type"-Garantie nicht durchsetzt. | `fix(config): conventions.issues.labels.namespace renders 'type: {type}', which matches neither GitHub nor GitLab label convention` | `bug`, `config`, `P2` | Ist: Preset `:56` → Renderer `conventions.py:285,290` → `git.md:151`. Soll: Namespace pro Adapter projizieren (`type/` bzw. `type::`). Minimal-Fix ohne #1188: Default auf `type/{type}` ändern + Migrationshinweis; vollständig: #1188. Test: gerenderter Block enthält keinen `type: `-Namespace mehr. |
| **F-2** — Die Prioritätsachse hat drei Teildefinitionen und keine kanonische: `meta-feedback.md:48` verweist auf „the `bug-feature-analyzer` matrix", die Matrix (`bug-feature-analyzer.md:91-97`) bewertet **nach Issue-Kategorie** (BUG/FEATURE/USER-ERROR), die Taxonomie kennt diese Kategorien nicht. Repo-Issues tragen `P2` teils, teils nicht (#1141 `P2`, #1167 nichts). | mittel — nach #1188 bleibt die Frage „welche Priority verdient dieser Bug?" unbeantwortet, obwohl das Label dann überall gesetzt wird. | `improvement: carry the triage priority criteria into the label taxonomy (P0-P3 rationale per type)` | `improvement`, `config` | Body: drei Fundstellen mit Zeilenangaben; Vorschlag: `priority.values.<P>.description` aus der Triage-Matrix ableiten und `bug-feature-analyzer.md` auf `{{ISSUE_TAXONOMY_TABLE}}` umstellen (AC-6); Test: P0–P3-Beschreibungen stammen aus einer Quelle. |
| **F-3** — CLI-Namenskollision: `sync.py --label TEXT` (Backup-Label, `scripts/sync.py:456`) und der neue `--labels` (Taxonomie) unterscheiden sich nur im Plural; ein Tippfehler schreibt ein Backup-Label statt Labels zu synchronisieren (und umgekehrt). | mittel — Fehlbedienung ohne Fehlermeldung; Help-Text (`--help`) macht den Unterschied nur bei genauem Lesen klar. | `chore(cli): disambiguate sync.py --label (backup) and --labels (issue taxonomy)` | `chore`, `config`, `P3` | Body: beide Flags mit Zeile; Vorschlag: `--label` als deprecated markieren und `--backup-label` als Alias einführen, oder `--labels` in einen Subcommand verschieben; Test: `--help` enthält beide mit eindeutiger Beschreibung. |
| **F-4** — Die Admin-UI editiert `conventions`-Overrides inklusive `issues.*` (`docs/ui/admin-ui.html:4160-4166`, Speichern `:4316-4317`) und verspricht damit eine Wirkung, die nur für `issues.language` existiert. Nach #1188 bleibt `types`/`labels.namespace` weiterhin wirkungslos, sofern die Sektion nicht als `deprecated` markiert wird. | mittel — UI-gestützte Fehlkonfiguration, gleiche Klasse wie das Issue selbst. | `bug(admin-ui): conventions editor exposes inert issues.* fields without a warning or redirect` | `bug`, `config` | Body: Feldliste, Beleg Renderer-Mapping (`conventions.py:131-132`); Vorschlag: im Conventions-Pane einen Hinweis „wird durch `issue-conventions` ersetzt" plus Link auf die neue Sektion rendern; Test: Pane markiert `issues.types`/`labels.namespace` als abgekündigt. |
| **F-5** — **AC-6-Folge-Issue (RVW-1188-06):** Solange `issue-conventions.enabled` per Default `false` ist, rendert jede Rolle die Legacy-Tabelle aus `LEGACY_ROLE_BLOCKS`; „kein Label-Literal" gilt nur für das Template, nicht für die Ausgabe. Vollständig erfüllt ist AC-6 erst, wenn `enabled` framework-weit `true` ist **und** `LEGACY_ROLE_BLOCKS` gelöscht sind. | **hoch für AC-6**, nicht blockierend für #1188 — #1188 liefert den Mechanismus, F-5 zieht den Schalter. | `chore(config): default issue-conventions.enabled to true and delete the legacy role label blocks` | `chore`, `config`, `P2` | Body: K-1/Löschkriterium, Golden-Test aus T10 als Regressionsanker, Migrationsschritt „Stufe 2" aus dem Plan; Vorbedingung: mindestens ein Pilotprojekt mit `enabled: true` über einen Release-Zyklus. **Als Issue-Entwurf markiert** — Nummer wird bei Anlage im Wave-Overview nachgetragen, hier bewusst nicht erfunden. |

Kein Finding ohne Issue zu: Repo-Containment, Provider-Agnostik, Secret-Handling — in diesen Bereichen wurden beim Verifizieren keine Abweichungen gefunden.

---

## 11. Cross-Issue-Konfliktflächen

Wellen-Kontext: #1181 (Commit-Authority), #1186 (Artifact-Locations-Matrix), #1187 (Project-Context-Scope), #1188 (dieses Issue), #1189 (Tmp-Sink-Pin, bereits als Plan auf diesem Branch).

**Kanonische Ausführungsreihenfolge der Wave (verbindlich, Review 2026-11-09):**

```
#1187  →  #1186  →  #1188  →  #1181   →   #1141   →   Whitelist-Ableitung (Teil von #1186, Nachlauf)
```

Begründung in drei Sätzen: #1187 und #1186 legen die Struktur fest, in die #1188 seine Sektion
einhängt (`project-context-injection`, `artifact-locations` vor `issue-conventions`); #1181 ändert
Commit-Authority-Texte in `agents/1-generic/*.md`, also **nachdem** #1188 die Platzhalter in
denselben Dateien gesetzt hat (sonst zweimal dieselbe Zeilenregion); #1141 schaltet top-level
`additionalProperties: false` erst, wenn alle neuen Sektionen als Properties existieren. Die
Whitelist-Ableitung aus dem Schema ist der Nachlauf zu #1186 und läuft **zuletzt**, weil sie die
Handeinträge von #1188/#1187 überflüssig macht.

**Szenario-IDs (Katalog `tests/scenarios/registry.md`):** `94` = #1181, `95`–`98` = #1187.
**#1188 belegt keine dieser IDs** — der Szenarientest aus Plan T28 lebt als pytest-Datei
(`tests/test_issue_labels_scenario_1188.py`), nicht als Katalog-Szenario, weil er einen
gemockten Tracker und keinen `project.yaml`-Sync-Variantenlauf braucht.

| Datei | Issues | Konfliktnatur | Serialisierungsbedarf |
|---|---|---|---|
| `config/project-config.schema.json` | #1188, #1186, #1187, #1181, #1141 | Vier neue Top-Level-Sektionen + eine grundsätzliche `additionalProperties`-Änderung in **einer** Datei; Einfügeposition und Schlüsselreihenfolge kollidieren mechanisch | **zwingend seriell** (eine Sektion pro PR) in der Reihenfolge #1187 → #1186 → #1188 → #1181; #1141 **zuletzt** |
| `config/project-config.schema.json` (top-level `additionalProperties`, `:2854`) | #1188 (AC-1: nur Sektion strikt) vs. #1141 (global strikt) | Semantischer Zielkonflikt: strikt-global würde `issue-conventions` nur mit Property akzeptieren | #1188 liefert die Property (vor #1181), #1141 schaltet global strikt **danach** |
| `scripts/lib/config.py` (`build_variables`) | #1188, #1186, #1187 | Drei Feature-Flags schreiben in dieselbe Variablen-Map (`:2737` ff.); #1187 will `PROJECT_CONTEXT` rollenabhängig, #1186 `ARTIFACT_*` | seriell in Wave-Reihenfolge; je Issue eigener Resolver-Aufruf statt gemeinsamer Inline-Logik |
| `scripts/lib/variables.py` | #1187 | Gemeinsame Variablen-Infrastruktur (Builder-Registry/Substitution); #1187 fügt die Projekt-Kontext-Builder hinzu. #1188 und #1181 fassen die Datei **nicht** an; #1188 nutzt nur die bestehende Builder-Registry | seriell; keine Überschneidung mit #1188 (RVW2-X-01) |
| `scripts/lib/agent_sync.py` | #1187, #1188, #1181 | Drei Overlay-Funktionen am selben Injektionspunkt (`:92-123` Muster, Aufruf `:1458-1459`): #1187 `PROJECT_CONTEXT`, #1188 `_apply_role_issue_convention_overrides`, #1181 Commit-Authority-Block | **zwingend seriell** `#1187 → #1188 → #1181`; #1188 setzt den Aufruf neben `:1459` (Plan-Task T10, File-Structure-Zeile `:239`), #1181 findet den fertigen Overlay-Punkt vor |
| `scripts/lib/sync_pipeline.py` | #1186, #1181 | Pipeline-Injektion für `artifact-locations` (#1186) und Commit-Authority (#1181). #1188 fasst die Datei **nicht** an (kein Task im Plan, der sie ändert) | seriell nach #1188 bzw. in Wave-Reihenfolge (RVW2-X-01) |
| `scripts/lib/standalone.py` | #1187 | Standalone-/Bootstrap-Pfad, den #1187 erweitert. #1188 und #1181 ändern die Datei **nicht**; #1188 prüft nur, dass die neuen Module im Import-Graph nicht hart geladen werden (Plan T29) | seriell in Wave-Reihenfolge; keine Schreibüberschneidung mit #1188 (RVW2-X-01) |
| `scripts/lib/consistency/placeholders.py` (Allow-List `:114-123`) | #1188, #1186 | Neue Platzhalter (`ISSUE_TAXONOMY_TABLE`, `ISSUE_LABEL_MAP`, `ISSUE_TITLE_FORMAT`, `ISSUE_CLOSING_KEYWORDS`, `ISSUE_TRIAGE_LABELS`, `ISSUE_TAXONOMY_ENABLED` vs. `ARTIFACT_*`); der Builder-Ratchet ist shrink-only (`:70-78` Kommentar) | seriell (jede Zeile ist ein Merge-Konflikt) |
| `scripts/consistency-check.py` (`:42-70`, `run_checks` `:171`) | #1188, #1186 | Zwei neue Check-Module + Registrierung; additive Importe, aber gleiche Zeilenregion | parallel möglich, Konflikt klein — seriell empfohlen |
| `scripts/admin-server.py` (`PROJECT_WRITABLE_SECTIONS`, `:234-259`) | #1188, #1186, #1187 | #1186 will die Handliste **durch Ableitung aus dem Schema ersetzen**; #1188/#1187 ergänzen je einen Handeintrag | **zwingend seriell:** #1186 landet früh (Wave-Position 2), aber ihr **Ableitungs-Teil** wird abgespalten und läuft als **letzter** Wave-Schritt; bis dahin sind #1188/#1187 Handeinträge, danach automatisch No-ops |
| `docs/ui/admin-ui.html` | #1188 (Taxonomie-Pane), #1186 (Artifacts-Pane), #1187 (Whitelist-Feld) | Eine 6.000+ Zeilen Single-File-UI; drei neue Panes + Routen | seriell (Konflikte sonst garantiert) |
| `agents/1-generic/git.md` | #1188 (`:149-151`), #1168 (Commit-Trailer), #1181 (Commit-Authority-Block) | Drei Änderungen in derselben Datei, unterschiedliche Abschnitte | seriell: #1188 vor #1181 (beide in derselben Prosa-Region), #1168 unabhängig |
| `agents/1-generic/bug-feature-analyzer.md` | #1188 (`:89`, `:91-97`), #1167 (`:42,84,134` REQ-Wording) | Dieselbe Datei, teils dieselben Abschnitte (`<context>`) | seriell |
| `agents/1-generic/feedback.md`, `meta-feedback.md` | #1188 (nur) | — | keine |
| `config/conventions-presets.yaml` | #1188 (D5-Mapping/Namespace), #1167 (`:34` REQ-Prefix) | Unterschiedliche Felder derselben Datei, gleiche `presets.default`-Region | parallel möglich, seriell sicherer |
| `howto/configs/project.yaml.example`, `templates/configs/project.yaml.example` | #1187, #1186, #1188, #1181 | Beide Beispiel-Dateien listen **jede** Config-Option; vier Issues schreiben in dieselbe Doku-Region | seriell in Wave-Reihenfolge; die Beispiele sind Doku, nicht Schema (kein Prüf-Gate). #1188 ergänzt die neue Sektion in **beiden** Dateien und pinnt sie mit einem parametrisierten Test (Plan T1, RVW2-1188-02) |
| `tests/scenarios/registry.md` | #1181, #1187, #1186 | Alle drei Issues ergänzen Szenarien; Katalogzeilen sind zeilenscharf. #1188 schreibt **keine** Zeile (pytest-Szenario statt Katalog-ID) | seriell; feste IDs: `94` = #1181, `95`–`98` = #1187, #1188 ohne ID (RVW2-X-01) |
| `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/CODEBASE_OVERVIEW.md` | #1188 (Nr. 11), #1186 (Nr. 10), #1187 | Alle drei Issues listen dieselben vier Doku-Dateien; jede Ergänzung ist ein Merge-Konflikt | **zwingend seriell** (Doku zuletzt, nach den Code-PRs) |
| `.github/ISSUE_TEMPLATE/**` vs `.github/pull_request_template.md` | #1188 (optional), #957 | Gleiche Verzeichnisfamilie, gleiche Ownership-/Überschreib-Frage (`generated-file-hashes.json`, Q4) | **Q4 entschieden (D11):** dieselbe Drift-/Überschreib-Regel für beide Familien; Erzeugung bleibt seriell (#1188 nach #957), damit der Marker-Vertrag nur einmal definiert wird |
| `docs/issue-labels.md` | #1188 (Erzeuger), #1186 (`project-docs`-Datei-Set) | #1188 ist der **einzige** Erzeuger; #1186 klassifiziert die Datei als `project-docs` (Artifact-Locations-Matrix) | keine inhaltliche Konfliktfläche, aber eine **Reihenfolge-Abhängigkeit**: Die `project-docs`-Klassifizierung (Querschnittsnotiz, §11.1) muss in #1186 stehen, bevor #1188 die Datei erzeugt. Zusätzlich drift-geprüft über `.meta-config/generated-file-hashes.json` (D11) |
| `.meta-config/issue-labels-state.json` | #1188 (erzeugt), #1186 (klassifiziert) | #1188 schreibt das Manifest (`--apply`, IC-8); #1186 führt es als **`unmanaged[]`** (Negativ-Deklaration, keine Klasse) in der Artifact-Locations-Matrix — die frühere Forderung einer dritten Kategorie `project-state` ist **gestrichen** (K1) | seriell: die `unmanaged`-Deklaration aus #1186 muss vor dem ersten `--apply` stehen, sonst landet die Datei in keinem Datei-Set (RVW2-X-02) |
| `.meta-config/project.yaml` (dieses Repo) | #1188 (Aktivierung), #1186 (`artifact-locations`), #1187 (`project-context-injection`) | Drei neue Sektionen in derselben Projektdatei; jede Aktivierung ändert die Sync-Ausgabe (Golden-Tests anderer Issues!) | seriell; Golden-Test je Issue getrennt halten; #1188 aktiviert **nichts** (Golden-Grundlage) |

### 11.1 Querschnittsnotizen für die Wave

- **`docs/issue-labels.md` ist ein `project-docs`-Datei-Set.** Die Datei gehört in #1186 in die
  Artifact-Locations-Matrix als `project-docs` (projekt-eigene, generierte Doku unter `docs/`), **nicht**
  als `framework-generated`. Konsequenz für #1188: IC-7/Marker-Regel bleibt. **Q4 ist seit 2026-11-09
  entschieden (D11):** die Datei wird zusätzlich in `.meta-config/generated-file-hashes.json`
  registriert und drift-geprüft; #957 spiegelt dieselbe Regel für PR-Templates. Datei-Set
  (#1186) und Drift-Ownership (D11) sind zwei getrennte Antworten auf zwei getrennte Fragen.
- **`config/issue-adapters.yaml` und `config/issue-conventions-presets.yaml` sind `framework-config`**,
  nicht `project-docs`: sie werden ausschließlich von agent-meta gepflegt und per sync verteilt.
- **Das Manifest `.meta-config/issue-labels-state.json` ist `unmanaged`** — eine
  **Negativ-Deklaration** in der Artifact-Locations-Matrix (#1186, `unmanaged[]`, D-8), **keine**
  dritte Kategorie neben `framework-config` und `project-docs` (Review-Auflösung K1; die frühere
  `project-state`-Kategorie ist gestrichen). Wirkung: kein `mode`, kein Scaffold, keine Zählung in
  AC-1186-12 — `classes` bleibt bei **23**, AC-1186-12 unverändert. **#1188 erzeugt die Datei,
  klassifiziert sie aber nicht selbst; #1186 führt sie in `unmanaged[]`** (RVW2-X-02). Sonst
  landet sie in keinem Datei-Set und wird von Ownership-/Drift-Prüfungen als unbekannter
  Schreibpfad gemeldet.

---

## Trace-Anker & AC-Matrix

- **spec-id:** `SPEC-issue-label-taxonomy-2026-11-09`
- **Issue:** #1188
- **Quelle:** `.tmp/issue-dump/issue-1188.json` (Body 27.927 Zeichen)

| AC | Deckende Spec-Abschnitte |
|---|---|
| AC-1 | §4.1, §4.2, IC-1 (Schema-Skizze inkl. `additionalProperties: false`), Q5 |
| AC-2 | §4.2, IC-2 |
| AC-2b | §4.4, IC-3/2, IC-7, Risiko „multi-Achse + Scoped-Separator" |
| AC-3 | §4.5, IC-3 (inkl. `kind: plugin`), D3 |
| AC-4 | §4.6, IC-3/5+7 (Pagination, Name→ID-Map), IC-4 (Dry-Run-Default, Idempotenz), D4 |
| AC-5 | §4.6, §4.7 (Kontext-Split: 4–6 offline, 1–3 online), IC-4 (Exitcodes), Q6 |
| AC-6 | §4.10 (sechs Platzhalter, D15-Triage-Abgrenzung), IC-1 (`enforcement`), §4.7 Regel 4/5, Folge-Issue F-5 (§10.2) |
| AC-7 | §4.5 (Capability `scoped-labels`), IC-3/1+2, §4.1 |
| AC-8 | IC-6 (Auth nur `auth.env`; H-6 `{token}`-Pflicht), IC-8/3 (Manifest secret-frei), §4.6 (secret-freie Ausgabe), §4.12 |
| AC-9 | IC-1/3 (Golden-Test), §4.4, §4.7 (Check still) |
| AC-10 | IC-5 (Manifest-/Allowlist-Prune, **kein** Rename in v1 — D10), IC-8 (Zustands-Manifest), §4.11 |
| AC-11 | §4.4 (Achsen-Schalter), §4.3 |
| AC-12 | §4.4 (Fehlerfälle), §4.7 Regel 6 |
| AC-13 | §4.4, §4.7 Regel 6 |
| AC-14 | §4.3 (sieben Stufen in AC-14-Reihenfolge + `source`), IC-1 (`platform-overrides`), IC-2 (Stufe 4 vs. 5), Q5 |
| AC-15 | §4.3 Invariante 1, §4.4, IC-1 |
| AC-16 | §4.11 (Präzedenzkette D9: `repository.*` → `git.remote-url` → CI-Env), IC-1 (`repository`), Q1 |
| AC-17 | §4.11 (`on-missing-label`), IC-1 (`create`) |
| AC-18 | §4.11 (`--apply` nicht transaktional), IC-4 (Exit 1), IC-5 (kein Delete) |
| AC-19 | §4.11 (401-Abbruch), Q2 |
| AC-20 | §4.11 (Namensgrenzen), IC-1 (`taxonomyAxis`), IC-3 (`defaults`) |
| AC-21 | §4.8 (Admin-UI), IC-4, Konfliktfläche `PROJECT_WRITABLE_SECTIONS` |
| AC-22 | §4.9 (generierte Doku, Drift-Baseline D11), IC-7 |

**Rückverfolgbarkeit der Entscheidungen:** D1 → §6/AC-1/AC-6 · D2 → §6/§4.1/Nicht-Ziele · D3 → §4.5/IC-3/AC-3 · D4 → §4.6/IC-4/AC-4 · D5 → §4.2 (`conventional`)/§4.10/AC-2/AC-6 · **D9** → §4.11/IC-1 `repository`/AC-16 · **D10** → IC-5/AC-10 · **D11** → §4.9/IC-7/AC-22 · **D12** → §4.9/IC-1 `templates`/AC-22 · **D13** → IC-4/IC-8/AC-4 · **D14** → §4.11/IC-4/AC-18+AC-19 · **D15** → §4.10/AC-6.

**Offene Punkte vor der Freigabe:** keine inhaltlichen mehr. Q1, Q2, Q3, Q4, Q7, Q8 und Q9
sind am 2026-11-09 entschieden und in §13 protokolliert (D9, D14, D10, D11, D15, D12, D13); Q5 und
Q6 waren bereits in Revision 2 entschieden (IC-1 bzw. §4.7/K-5). Der Statuswechsel
`DRAFT → APPROVED` durch den Nutzer ist am 2026-11-09 erfolgt.

---

## 12. Review-Auflösung (2026-11-09)

Alle Befunde aus dem Review zu #1188 (Runde 1: `RVW-1188-*`; Runde 2: `RVW2-*`), mit Änderung und
Fundstelle. Status der Spec damals `DRAFT`, seit 2026-11-09 `APPROVED`.

| Befund-ID | Änderung | Stelle |
|---|---|---|
| **RVW-1188-01** (BLOCKER) | Label-Namen werden beim Bau der Request-URL mit `urllib.parse.quote(name, safe="")` kodiert (projizierter Name bleibt unkodiert im Diff/Manifest); Gitea bekommt `ids: {op: list, key: id}` und eine Name→ID-Map, die **einmal pro Lauf** aus dem `list`-Response aufgelöst wird; `pagination` ist jetzt Pflichtdaten jedes Adapters (sonst Duplikat-`create`); IC-4-Idempotenzzeile benennt die Abhängigkeit; AC-4-Interpretation ergänzt; Tests mit `type/bug` **und** `area/core` sind in Plan T16/T28 verankert | §4.11 (zwei neue Bullets), **IC-3** (YAML: `pagination`, `ids`, Pfade ohne `?per_page=`; Vertragsregeln 5–7), IC-4, §4.12 H-4, „AC-Interpretationen" AC-4, Risiko-Tabelle (zwei neue Zeilen) |
| **RVW-1188-02** (MAJOR) | Stufe 4 = Framework-**Plattform**-Default, Stufe 5 = Framework-**Preset** — exakt die AC-14-Reihenfolge. `source`-Literale bleiben an der Stufe kleben (`framework:platform:<adapter>` jetzt Stufe 4, `preset:<name>` Stufe 5). Invarianten 1/2 und die Risikozeile sprechen von Stufe 4. IC-2 sagt die Stufen explizit. `--explain`-Beispiel unverändert korrekt (`type/bug ← preset:default`, `separator ← adapter:gitlab` = Stufe 6) | §4.3 (Tabelle + Begründungsabsatz + Invarianten 1/2), §4.4, IC-2 (Vertragsabsatz), Risiko „Framework-Plattform-Default überstimmt still ein Projekt", Trace-AC-14, Plan T5/T8 |
| **RVW-1188-03** (MAJOR) | Transport-Overrides haben genau einen deklarierten Ort: `issue-conventions.platform-overrides.<adapter>.{base-url, api, ids, pagination, auth.header, defaults}` — als **geschlossenes** Objekt in IC-1 (`additionalProperties: false`), Adapter-ID-Schlüssel bleibt offen (D3). `auth.env` ist nicht überschreibbar. T3/T28 nennen den konkreten Key | §4.5 (Regelabsatz), **IC-1** (`platform-overrides`-Block + `$defs/adapterApi|adapterIds|adapterPagination|adapterDefaults` + Vertragsregel 1), IC-6, Q5, §4.12 H-2, Plan T3/T16/T28 |
| **RVW-1188-04** (MAJOR) | Löschen nur aus dem persistierten Soll-/Hash-Manifest (IC-8) oder `sync.prune-allow`; der eigene Präfix ist **kein** Löschkriterium mehr und erzeugt höchstens `info: prune-candidate-unowned`. Neues IC-8 (Format, Schreibregeln, Versionierung). Der Satz „keine State-Datei" ist ersetzt. AC-10-Interpretation ergänzt; Test mit Fremdlabel **innerhalb** des Präfix (`type/needs-design`) | **IC-5** (komplett neu), **IC-8** (neu), §4.11 (Bullet), Datenfluss (Eigentümer-Tabelle + Absatz), §4.4 (`enabled:false` löscht nie), AC-Interpretation AC-10, Risiken (Manifest-Verlust, Merge-Konflikt), Q3/Q9, Plan T17/T21/T28 |
| **RVW-1188-05** (MAJOR) | Neue §4.12 „Transport-Härtung" H-1…H-7: HTTPS-Zwang (Loopback-Ausnahme), Host-/Scheme-Pinning (Projekt ändert nur den Pfad), relative Pfade ohne `//`/`..`, keine Redirects (3xx = Fehler, Auth geht nie an einen zweiten Host), `auth.header` nur mit `{token}` (sonst `IssueConfigError`). „Warum H-2 ausreicht" nennt die Gitea-Env-Herkunft des Hosts. IC-6 nennt die Regeln als nicht abschaltbar. Tests für alle drei Pfade in Plan T3/T16 | §4.12 (neu), §4.5, **IC-3** (Vertragsregeln 8/9), **IC-6**, §4.11, Risiko „Secret-Exfiltration", Plan K-8/T3/T16 |
| **RVW-1188-06** (MAJOR, AC-5) | §4.7 hat jetzt eine **Kontext-Spalte**: Regeln 4–6 offline (`--validate`), Regeln 1–3 online (`--labels --check`); ein Modul, sechs IDs, zwei Kontexte; `test_all_six_rule_ids_reported_with_tracker` als Nachweis; AC-5-Interpretation in der AC-Tabelle; Q6 als entschieden markiert | **§4.7** (Tabelle + Absatz), „AC-Interpretationen" AC-5, Q6, Trace-AC-5, Plan T23/T24 |
| **RVW-1188-06** (MAJOR, AC-6) | AC-6-Interpretation trennt „kein Literal im Template" (erfüllt, K-1) von „keine Legacy-Tabelle in der Ausgabe" (erst mit `enabled: true`). Konkretes Folge-Issue **F-5** mit Titelvorschlag `chore(config): default issue-conventions.enabled to true and delete the legacy role label blocks`, markiert als **Issue-Entwurf** (keine Nummer erfunden) | „AC-Interpretationen" AC-6, **§10.2 F-5**, Trace-AC-6, Plan K-1/T10 |
| **WARN `plan:906`** | Leere Tabellenzelle in der AC-8-Traceability gefüllt (Manifest-Ebene + H-6 als vierte Ebene) | Plan „AC→Task-Traceability" AC-8 |
| **WARN `plan:305/320`** | `scripts/lib/issue_conventions.py` (T2) und `scripts/lib/issue_adapters.py` (T3) sind dort als **Create** geführt, nicht als Modify | Plan T2/T3 `Files:` |
| **WARN (Spec §4.10)** | `{{ISSUE_TRIAGE_LABELS}}` und `{{ISSUE_TAXONOMY_ENABLED}}` sind jetzt Spec-Vertrag (Tabellenzeilen + Registrierungspflicht in `_BUILTIN_VARS`) | **§4.10** (Tabelle), §4.10-Schlussparagraph |
| **Querschnitt: Wave-Reihenfolge** | Kanonisch `#1187 → #1186 → #1188 → #1181`, danach `#1141`, Whitelist-Ableitung zuletzt. §10.1 (#1141) und §11 (Schema, `admin-server.py`, `git.md`) sind darauf umgestellt | §11 (Reihenfolge-Block), §11-Tabelle, §10.1 #1141 |
| **Querschnitt: Konfliktmatrix** | Neue Zeilen für `scripts/lib/variables.py`, `scripts/lib/sync_pipeline.py`/`agent_sync.py`, `scripts/lib/standalone.py`, `tests/scenarios/registry.md` und beide `project.yaml.example` (`howto/configs/`, `templates/configs/`) | §11-Tabelle |
| **Querschnitt: Szenario-IDs** | `94` = #1181, `95`–`98` = #1187; #1188 belegt **keine** Katalog-ID (pytest statt Katalog) | §11 (Absatz vor der Tabelle) |
| **Querschnitt: `docs/issue-labels.md`** | Als `project-docs`-Datei-Set für #1186 klassifiziert (Querschnittsnotiz); die Drift-/Ownership-Frage ist mit **D11** entschieden (Registrierung in `generated-file-hashes.json`, #957 spiegelt die Regel) | §11-Tabelle (Zeile `docs/issue-labels.md`), **§11.1**, §13/D11 |
| **RVW2-1188-01** (MAJOR, Sicherheit/Prune) | Kandidatenformel korrigiert: nicht `desired ∪ (Manifest ∖ aktive Achsen)`, sondern `(Manifest ∖ desired) ∖ labels(inaktiver Achsen)` — `desired` enthält die inaktive Achse bereits nicht (Achsen-Gate), die Subtraktion ist reine Ausnahme-Regel über den projizierten Achsen-Präfix, kein Löschkriterium. „Fehlt das Manifest ⇒ null Kandidaten" präzisiert: nur wenn **auch** `sync.prune-allow` leer ist; die Allowlist wirkt unabhängig vom Manifest (Bedingung 3 ist ein ODER). Plan-T17-Tests entsprechend geschärft | **IC-5** (beide Prune-Bullets), §11.1 unverändert, Plan T17 |
| **RVW2-1188-02** (MINOR) | Die neue Sektion steht in **beiden** `project.yaml.example`-Dateien (`howto/configs/`, `templates/configs/`) und wird mit einem parametrisierten Test gepinnt; der Task dafür ist Plan T1 statt nur der Konfliktmatrix | §11-Tabelle (Beispiel-Zeile), Plan T1 (Files + Step 3 + Test) |
| **RVW2-1188-03** (MINOR, Testgüte) | Kein `git diff` als Gate: M3 stützt sich auf den Golden-Test aus T10; das Abschlusskriterium „keine Aktivierung" nutzt den festen Basis-Commit `git diff --name-only aaed14c2..HEAD -- .meta-config/project.yaml` | Plan M3-Gate, Plan „Abschlusskriterien" Nr. 6 |
| **RVW2-1188-04** (MINOR) | Stufen-Nummerierung im Plan korrigiert: Projekt-Preset (Stufe 3) vs. Framework-Preset (Stufe 5); Stufe 4 bleibt `framework:platform:<adapter>` und wird nicht umnummeriert | Plan T5 Step 3 |
| **RVW2-X-01** (MAJOR, Querschnitt) | Verbindliche Zielmatrix in §11 nachgezogen: `agent_sync.py` → #1187/#1188/#1181 (eigene Zeile), `sync_pipeline.py` → #1186/#1181 (eigene Zeile), `variables.py`/`standalone.py` → #1187, `tests/scenarios/registry.md` → #1181/#1187/#1186 (ohne #1188-Zeile), beide `project.yaml.example` → #1187/#1186/#1188/#1181, `docs/issue-labels.md` → #1188 erzeugt / #1186 klassifiziert, `.meta-config/issue-labels-state.json` → #1188 erzeugt / #1186 klassifiziert | §11-Tabelle (sieben geänderte/neue Zeilen), Plan „Backlog-Bugs" (#1181-Zeile) |
| **RVW2-X-02** (Querschnitt) | Die Klassifikation der State-Datei ist eine #1186-Pflicht, nicht nur eine #1188-Notiz: die State-Datei steht als eigene Matrix-Zeile, und §11.1 sagt explizit, dass **#1186** sie klassifizieren muss — als `unmanaged` (K1; die frühere `project-state`-Kategorie ist gestrichen) | §11-Tabelle (neue Zeile `.meta-config/issue-labels-state.json`), **§11.1** (Manifest-Bullet) |

**Nicht geänderte Punkte (bewusst):** Die AC-Texte 1–22 + AC-2b bleiben wörtlich (Issue-Übernahme);
alle Neuinterpretationen stehen ausschließlich im Abschnitt „AC-Interpretationen". `Status` war
damals `DRAFT` und ist seit 2026-11-09 `APPROVED`. Es wurden **keine** Issue-Nummern erfunden: F-5 ist als Entwurf markiert, die im
Wave-Kontext als real bestätigten Nummern #1201–#1204 werden hier **nicht** zugeordnet, solange
die Titel nicht abgeglichen sind.

### 12.1 Szenario-Konflikte K1–K8 (2026-11-09)

Auflösung der acht Befunde aus `.tmp/scenario-config-wave/RESULT.md`, konsistent über alle vier
Wave-Specs/-Pläne. Damals `DRAFT`, seit 2026-11-09 `APPROVED`.

| Befund | Änderung | Stelle |
|---|---|---|
| **K1** (BLOCKER) | `.meta-config/issue-labels-state.json` wird als **`unmanaged`** geführt (Negativ-Deklaration, #1186 `unmanaged[]`); die dritte Kategorie `project-state` ist **gestrichen**, `classes` bleibt bei 23 (AC-1186-12 unverändert) | §11 (Matrix-Zeile), **§11.1** (Manifest-Bullet), Kopf Revision 4 |
| **K2** (MAJOR) | **Eine** kanonische Form `separator: {single, multi}` auf allen drei Ebenen (Adapter-Default, Framework-Plattform, Projekt); `defaults.label-separator` (String) ist entfernt, weil IC-1 `additionalProperties: false` ist. Invarianten getrennt: „Projekt-Overrides (Stufe 1) schlagen alles" und „Framework-Plattform-Default (Stufe 4) schlägt Framework-Preset (Stufe 5)" | **§4.3** (Kanonik-Absatz + Invariante 1), **IC-1** (`defaults.separator` statt `label-separator`) |
| **K3** | **Nicht betroffen**: #1188 hat keine `preset`-Präzedenzstufe; die Source-Attribution `project-preset` existiert hier nicht | geprüft: §4.3, IC-2 |
| **K4** (MINOR) | Regel 6 prüft nur die zwei realisierbaren Bedingungen (aktivierte Achse mit leeren `values`; keine aktive Achse). Es gibt **kein** `default`-Feld in `taxonomyAxis`; die Zwei-Defaults-Prüfung ist eine Laufzeitregel und gehört zu **AC-7** (`single-axis-per-issue`) | **§4.7** (Regel 6 + Absatz), §4.4/IC-1 (`enforcement`) |
| **K5** | **Nicht betroffen**: dieses Issue hat keine Grant-Präzedenztabelle | geprüft: §4.3 |
| **K6** (NIT) | Die Skizzen bleiben bei `$defs`, weil das Ist-Schema `draft-07` deklariert und dennoch `$defs` nutzt; `definitions` wäre nur bei einem Wechsel des Gesamtschemas richtig | **IC-1** (`$defs`-Notiz) |
| **K7** | **Nicht betroffen**: alle Schlüssel liegen in der neuen Top-Level-Sektion `issue-conventions` und sind durchgehend kebab-case — kein snake_case-Bestandsblock berührt | geprüft: IC-1, IC-3 |
| **K8** | **Nicht betroffen**: kein bestehender `_KEYS`-Block wird erweitert; #1188 fügt eine eigene, geschlossene Sektion hinzu | geprüft: IC-1 |

---

## 13. Entscheidungsprotokoll (2026-11-09)

Vom Nutzer entschiedene offene Fragen. Jede Zeile ist **bindend** und im Dokument oben eingearbeitet;
Abweichungen brauchen eine neue Spec-Revision. `Status` war damals `DRAFT`; der Freigabe-Marker wurde am 2026-11-09 gesetzt.

| D-Nr | Frage | Entscheidung (`DECIDED 2026-11-09`) | Stelle |
|---|---|---|---|
| **D9** | **Q1** — Repository-Identität, wenn `git.remote-url` leer ist | Präzedenzkette `issue-conventions.repository.{owner,repo}` → `git.remote-url` → CI-Env (`GITHUB_REPOSITORY`, `CI_PROJECT_PATH`); harter Fehler **erst** wenn alle drei leer/unparsbar sind, mit einer Meldung, die alle drei Wege nennt und **nie** einen leeren `owner` ausgibt. Schema `repository: {owner, repo}` (+ `project-id`) ergänzt; Parser, Fehlermeldung und Tests in T15 | §4.11, IC-1 `repository`, Risiken, AC-16-Trace, Plan T15 |
| **D10** | **Q3** — Rename-Erkennung | Kein Rename in v1: neuer Wert ⇒ `create <neu>`; das alte Label bleibt im Tracker und wird als `info: rename-candidate <alt>` gemeldet; kein `update.new_name`-Aufruf aus Verdacht. Die `rename`-Zeile bleibt im Vertrag **reserviert** für eine spätere explizite `renames`-Map (eigene Spec-Revision). Test: alter Wert verlässt nur das Soll-Set, kein Rename-Call, Info erscheint | IC-5, AC-10-Trace, Risiken, Plan T17 |
| **D11** | **Q4** — Ownership/Drift von `docs/issue-labels.md` | Die Datei kommt in `.meta-config/generated-file-hashes.json` (explizite Root-Level-Registrierung analog `PLATFORM_DEFAULTS_RESOLVED_REL`); sie ist generiert und drift-geprüft, manuelle Edits werden beim nächsten Sync überschrieben (mit `.sync-backup-*`). Dieselbe Regel wird in #957 für PR-Templates gespiegelt — eine Antwort, nicht zwei | §4.9, IC-7, §11.1, AC-22-Trace, Plan T25 |
| **D12** | **Q8** — Ort des Template-Schalters | `issue-conventions.templates: {mode: off\|scaffold\|manage, force: bool}` als **geschlossener** Unterabschnitt der bestehenden Sektion. `off` = nichts, `scaffold` = nur fehlende Dateien, `manage` = zusätzlich marker-tragende Dateien; `force: false` Default. T30 ist damit **innerhalb** der Freigabe | IC-1 `templates`, §4.9, Plan T1/T30 |
| **D13** | **Q9** — Commit des Zustands-Manifests | `--apply` **schreibt** und druckt die geänderte Datei in der Ergebnis-Tabelle; **kein** Auto-Commit aus dem CLI. Der Commit bleibt beim `git`-Schritt (Commit-Authority). CI-`--apply`-Jobs committen **nie** | IC-4 (Commit-Zeile), IC-8/2, Plan T21 |
| **D14** | **Q2** — Retry-Policy | Genau **ein** Retry, nur bei `429`, Wartezeit aus `Retry-After` (Cap 30 s, Default 1 s, injizierbare `sleep`). `5xx` und Timeouts: **kein** Retry, Fehler sammeln, Exit 1 (AC-18). `401`/`403` brechen unverändert nach dem ersten Fehlschlag ab (AC-19). Deterministisch testbar | §4.11, IC-4, Plan T16/T18 |
| **D15** | **Q7** — Triage-Labels | `render_triage_labels()` liefert `triage` und `needs-info` aus der Framework-Konstante `TRIAGE_LABELS`; `docs/issue-labels.md` führt sie unter **„Nicht Teil der Taxonomie"**. **Keine** vierte Achse (D2 bleibt); Regel 4 des Consistency-Checks nimmt sie von der Literal-Prüfung aus | §4.10, AC-6-Interpretation, Plan T13/T25 |
