# Artifact-Locations-Matrix für alle Artefakt-Klassen (Issue #1186) — Spec

> Status: **APPROVED** — Approved: 2026-11-09 (User-Freigabe via main_chat).
> Datum: 2026-11-09
> Revision: 2 (Review-Auflösung 2026-11-09)
> Revision: 3 (Szenario-Konflikte K1–K8, 2026-11-09) — K1 (`unmanaged` statt `project-state`),
> K3 (vier Wertequellen + Source-Attribution), K6 (`$defs`-Notiz); K2/K4/K5/K7/K8 betreffen
> dieses Dokument nicht. Details: §11.2.
> Revision: 4 (Entscheidungsprotokoll D1–D4, 2026-11-09) — OQ-5 (Scratch: **eine** Quelle
> statt Doppelsenke), OQ-7 (D-9-Ausnahme bleibt), OQ-3 (Naming konfigurierbar, Token-Kanon),
> OQ-4 (Default `SE`, Regeltext auf `{{ARTIFACT_SE_ROOT}}`). Details: §12.
> Autor: `concept-specifier` (Subagent, Auftrag des Orchestrators)
> Issue: [#1186](https://github.com/Popoboxxo/agent-meta/issues/1186) — „feat(config): configurable
> artifact-locations matrix for all artifact classes (paths, per-class mode, Admin-UI, enforcement)"
> `spec-id`: **SPEC-1186-artifact-locations-matrix** (Trace-Anker für Plan und Validierung)
> Branch: `docs/config-wave-plans-1181-1188` · HEAD `aaed14c2` · Framework-Stand `v2.0.0-beta.8`
> **Klasse: XL** — Begründung §1 (Umfang >20 Dateien in 9 Produktionsbereichen; Querschnitt
> über Config-, Schreib- und Variablen-Vertrag; nicht umkehrbar ohne Migration).
> Bezug: [#1150](https://github.com/Popoboxxo/agent-meta/issues/1150) (Problem-Beschreibung),
> [#1136](https://github.com/Popoboxxo/agent-meta/issues/1136) (tmp-sink, geschlossen),
> [#1187](https://github.com/Popoboxxo/agent-meta/issues/1187)/[#1188](https://github.com/Popoboxxo/agent-meta/issues/1188)/[#1181](https://github.com/Popoboxxo/agent-meta/issues/1181)
> (Wellen-Nachbarn)
> Beleg-Legende: **VERIFIED** = in dieser Session am Code gelesen (`datei:zeile`);
> **CONFIRMED** = zusätzlich durch vorhandenen Test/Guard belegt; **STALE** = Issue-Angabe
> trifft auf HEAD `aaed14c2` nicht mehr zu (siehe §2.6); **(Issue)** = unverifizierte
> Issue-Angabe.
> Diese Spec enthält **keinen Implementierungscode** — nur Verträge, Datenfluss, Kriterien.

---

## 1. Problem & Motivation

Ausgabeorte für Artefakte sind heute **teilweise** konfigurierbar: der Spec/Plan/Spike-Workflow
hat einen `paths`-Block, die SE-Kaskade genau einen Schlüssel (`se_output.base_dir`). Alles
andere — Reviews, Audits, Analysen, Schätzungen, Konzepte, Kritik-Reports — landet an Stellen,
die **kein Config-Key und kein Admin-UI-Feld** steuert. Folge (belegt in §2):

- dieselbe Artefakt-Art wird an bis zu vier Orten geschrieben (`reviews`: tmp-Sink,
  „neben der Quelldatei", „irgendwo als Datei", `{SE_BASE_DIR}/reviews/`);
- persistente Artefakte landen im **ephemeren** tmp-Sink und sind damit per Definition
  nicht versioniert (48 `{{TMP_SINK_PATH}}`-Treffer in `agents/1-generic/*.md`);
- Rollen-Templates tragen Pfad-Literale, die keine Config kennt (`docs/spikes` in
  `explorer.md:71`) oder gar keinen Pfad nennen („write the completed review report as an
  artifact (e.g. `concept-review-<topic>.md`)", `concept-reviewer.md:92`);
- das Admin-UI kann die vorhandenen Pfad-Keys **gar nicht** schreiben: `spec-plan-workflow`
  fehlt in `PROJECT_WRITABLE_SECTIONS` und `docs/ui/admin-ui.html` enthält **null** Treffer
  für `spec-plan` / `se_output` (VERIFIED, grep).

Ziel dieses Issues ist **ein** konsolidiertes Config-Surface — `artifact-locations` — mit
Pfad, Modus (`files | inline | off`), `git`-Behandlung, Naming, `legacy[]`, Retention pro
Klasse, generierten Variablen statt Literalen, Admin-UI-Pflege und technischer Durchsetzung
(Hook blockt, Consistency-Check warnt).

**Klassifizierung: XL.** Begründung (alle drei Kriterien treffen zu):
1. **Umfang:** >20 Dateien in 9 Produktionsbereichen — `config/project-config.schema.json`,
   `scripts/lib/config.py`, Scaffold, `scripts/lib/consistency/`, `hooks/1-generic/`,
   `scripts/admin-server.py` + `docs/ui/admin-ui.html`, `config/routing/reviewers.yaml`,
   Preset-Datei, ≥18 Rollen-Templates, Manager-Rolle, Doku.
2. **Querschnitt:** ändert einen **öffentlichen Config-Vertrag** (Schema + Presets + Präzedenz),
   einen **Laufzeit-Schreibvertrag** (Hook) und den **Variablen-Vertrag** aller Rollen gleichzeitig.
3. **Nicht umkehrbar ohne Migration:** neue Defaults verschieben zukünftige Schreibpfade in
   jedem Consumer-Projekt; `legacy[]` ist der einzige Rückweg.

## 2. Ist-Zustand (Belege)

### 2.1 Was heute konfigurierbar ist

| Artefakt-Klasse | Config-Key heute | Abschaltbar | Admin-UI | Beleg |
|---|---|---|---|---|
| Specs | ✅ `spec-plan-workflow.paths.specs` (Default `docs/specs`) | ✅ `spec-plan-workflow.enabled: false` | ❌ | `config/project-config.schema.json:2233-2236`; `scripts/lib/config.py:2366`; `scripts/lib/spec_plan_scaffold.py:54` (VERIFIED) |
| Plans | ✅ `paths.plans` (Default `docs/plans`) | ✅ derselbe Schalter | ❌ | Schema `:2237-2240`; `config.py:2367` (VERIFIED) |
| Spikes | ✅ `paths.spikes` (Default `docs/spikes`) | ✅ derselbe Schalter | ❌ | Schema `:2241-2244`; `spec_plan_scaffold.py:54-55` (VERIFIED) |
| Reviews (SE) | 🟡 nur `se_output.base_dir` → `{{SE_BASE_DIR}}`; `reviews/` ist darunter fix | 🟡 über `SE_ENABLED` | ❌ | `config.py:2269-2273`; `rules/1-generic/se-cascade-artifact-taxonomy.md:27,56`; `agents/1-generic/se-critic.md:56,110` (VERIFIED) |
| Scratch (tmp-Sink) | ✅ `repo_containment.tmp-sink.path` → `{{TMP_SINK_PATH}}` | ✅ `enabled: false` | ✅ (`repo_containment` ist in der Whitelist) | `config.py:2044-2046`; `scripts/admin-server.py:243` (VERIFIED) |
| Fortschritt/Checkpoints | ✅ `progress.dir`, `progress.checkpoint-dir` | ❌ | ❌ (`progress` fehlt in der Whitelist) | Schema `:2806-2821`; Whitelist `admin-server.py:234-259` (VERIFIED) |
| Event-Log | ✅ `viz.event_log` (Default `.meta-viz/events.jsonl`) | ❌ | ✅ (`viz` ist in der Whitelist) | Schema `:2396-2398` (VERIFIED) |

### 2.2 Was nicht konfigurierbar ist (Literal- und Leerstellen-Inventar)

| Klasse | Zustand heute | Beleg (VERIFIED) |
|---|---|---|
| Concepts | Datei `concept-<topic>.md` **ohne Pfad** | `agents/1-generic/ideation.md:97` |
| Plans (Fallback) | `plan-<topic>.md` **im Projekt-Root** | `agents/1-generic/planner.md:75`; Referenz auch `requirements.md:75` |
| Spikes | Pfad-Literal `docs/spikes/…` trotz Config-Key (keine `SPEC_PLAN_SPIKES_DIR`-Variable) | `explorer.md:71`; `config.py:2366-2367` erzeugt nur SPECS/PLANS |
| Reviews (code/domain) | **kein Pfad** — Vollreport in den tmp-Sink, Rückkanal = Pfad | `security-auditor.md:223`, `ai-security-guardian.md:111`, `app-lifecycle-governor.md:100`, `prompt-governor.md:120`; Konvention `config/routing/reviewers.yaml:23-29` |
| Reviews (concept) | **kein Pfad** („write as artifact (e.g. `concept-review-<topic>.md`)") | `concept-reviewer.md:92` (Schreib-Tool `concept-reviewer.md:139`) |
| Reviews (copyedit/proofread) | **neben der Quelldatei** (`<filename>.copyedit.md`) — schreibt in `src/` | `copyeditor.md:92`; `proofreader.md:89` |
| Audits | kein Key; reale Dateien liegen in `docs/plans/audit-*.md` (2 aktiv, 2 in `archive/`) | `docs/plans/audit-2026-09-detailed-system-audit.md`, `audit-admin-ui-model-loading.md`, `archive/audit-2026-08-refactoring-roadmap.md`, `archive/audit-2026-09-system-concept.md` |
| Analysis | reine Konvention `docs/analysis/` | `docs/analysis/` existiert (u. a. `evidence/`) |
| Conclusions | fixer Pfad `docs/conclusions/conclusions-YYYY-MM-DD.md` | `documenter.md:43,134`; `knowledge-migrator.md:39,50` |
| Estimates | „`<persisted estimate file path>`" — **undefiniert** | `effort-estimator.md:116` |
| Project-Docs | feste Dateien, nicht konfigurierbar | `documenter.md:131-132` (`docs/CODEBASE_OVERVIEW.md`, `docs/ARCHITECTURE.md`); `requirements.md:71` (`docs/REQUIREMENTS.md`) |
| SE-Zellen | nur `base_dir`; Dateinamen im Template fix | `se-requirements.md:184`, `se-architect.md:114`, `se-interface-mgr.md:153`, `se-developer.md:188`, `se-integration-and-test-manager.md:263`, `se-validator.md:177`, `se-verifier.md:191`, `se-termination.md:154` |
| Runbooks/RCA | **kein Pfad** (kein `docs/runbooks/` im Repo) | `docs/`-Verzeichnisliste; `sre-engineer`/`incident-responder` ohne Pfadangabe |

### 2.3 Literalpfad-Inventar (Trefferzahlen, HEAD `aaed14c2`)

| Muster | Scope | Treffer | Bewertung |
|---|---|---|---|
| `/tmp/opencode` | `agents/` | **0** | **STALE** — Issue nennt 8 Zeilen; behoben, zusätzlich durch Test verboten (`tests/test_template_report_paths.py:61`) |
| `{{TMP_SINK_PATH}}` | `agents/1-generic/*.md` | **48** | ephemerer Sink wird für persistente Klassen mitbenutzt |
| `{SE_BASE_DIR}` (**einfache** Klammer) | `agents/1-generic/*.md` | **16** in 12 Dateien | wird von `sync.py` **nie** substituiert (siehe F-1, §8) |
| `{{SE_BASE_DIR}}` (doppelte Klammer) | `agents/1-generic/*.md` | **4** | die einzige substituierbare Form (`placeholders.py:89`) |
| `docs/spikes` | `agents/1-generic` | **1** | `explorer.md:71` |
| `docs/plans/archive` | `agents/1-generic` | **1** | `documenter.md:81` — **Schreib-/Verschiebeziel** (`archive.target`), muss Variable werden (RVW-1186-06) |
| `docs/conclusions` | `agents/1-generic` | **4** | 2 Schreibziele (`documenter.md:43,134`), 2 **Lese**-Literale (`knowledge-migrator.md:39,50` — Bestands-Scan/OKF-Mapping, per Ratchet-Marker zulässig, §4.6) |
| `docs/specs`, `docs/plans` | `placeholders.py` | 2 Variablen | `SPEC_PLAN_SPECS_DIR`, `SPEC_PLAN_PLANS_DIR` (`placeholders.py:97`) |
| `docs/plans/audit-*.md` | `docs/plans` (+ `archive/`) | **4** (2 aktiv, 2 archiviert) | Audits leben faktisch in der Plans-Klasse |

Nicht mehr existent, aber im Issue als „required rewrites" genannt: `orchestrator.md:217` ist
heute eine `{{#if}}`-Zeile ohne Pfadliteral (VERIFIED) — die Zeilenangabe ist **STALE**.

### 2.4 Zählung der Artefakt-Klassen (selbst nachgezählt)

**12 persistente Nicht-SE-Klassen** (D7-konservativ): `specs` · `plans` · `concepts` · `spikes` ·
`reviews` · `audits` · `analysis` · `reports` · `adr` · `traceability` · `runbooks` ·
`project-docs`.

**2 ephemere Nicht-SE-Klassen** (D8): `scratch` · `state`.
→ 12 + 2 = **14 Nicht-SE-Klassen** (deckt AC-1186-12 wörtlich).

**9 SE-Zell-Klassen** (D5) — je eine eigene Klasse, aus den Templates belegt:

| # | Klasse | Leaf-Naming | Producer (Beleg) |
|---|---|---|---|
| 1 | `se-requirements` | `L{level}_{FolderName}_Requirements.md` | `se-requirements.md:43,184`; `se-component-requirements.md:61,281` (L3) |
| 2 | `se-architecture` | `L{level}_{FolderName}_Architecture.md` | `se-architect.md:52,57,114` |
| 3 | `se-decomposition` | `L2_architectural_decomposition_iter-N.md` | `se-cascade-artifact-taxonomy.md:21-22`; `se-architect.md:57` |
| 4 | `se-interfaces` | `L{level}_{FolderName}_Interfaces.md` | `se-interface-mgr.md:153` |
| 5 | `se-implementation` | `implementation/L{level}_{FolderName}_Impl.md` | `se-developer.md:188`; `se-senior-developer.md:144`; `se-junior-developer.md:171` |
| 6 | `se-testplan` | `validation/L{level}_{FolderName}_TestPlan.md` | `se-integration-and-test-manager.md:263` |
| 7 | `se-validation` | `validation/L{level}_{FolderName}_Validation.md` | `se-validator.md:177` |
| 8 | `se-verification` | `validation/L{level}_{FolderName}_Verification.md` | `se-verifier.md:191` |
| 9 | `se-decisions` | `L{level}_{FolderName}_Decisions.md` | `se-termination.md:154` |

`se-root` ist **keine** Klasse, sondern nur der Default-Wert der neun `path`-Felder
(Design-Review-Punkt 4 im Issue, hier als Vertrag übernommen — §4.1).

**SE-globale Klassen (D6), ohne eigene Zeile:** `reviews` · `adr` · `reports` · `traceability` ·
`state` — plus der strittige `vv`-Fall (§7, OQ-1).

### 2.5 Zwei strukturelle Blocker (belegt, Zahlen aktualisiert)

1. **Admin-UI kann Pfad-Keys nicht schreiben.**
   `PROJECT_WRITABLE_SECTIONS` (`scripts/admin-server.py:234-259`) enthält **47** Einträge.
   Das Wurzel-`properties` des Schemas (`config/project-config.schema.json:7-2849`) hat
   **70** Einträge (inkl. `$schema`). Schnittmenge: **40**. Damit fehlen **30** Schema-Sektionen
   in der Whitelist (u. a. `spec-plan-workflow`, `progress`, `quality-pipelines`, `cascades`,
   `delegation`, `analysis`, `release`, `variables`, `memory`, `provider-overrides`) —
   zusätzlich existieren **7** Whitelist-Einträge **ohne** Schema-Pendant
   (`agent-prompts`, `steps-overrides`, `rules`, `environments`, `skills-registry`, `backup`,
   `submodule-protection`; Runtime-Sektionen, siehe `admin-server.py:231-233`).
   Das Issue nennt „29 von 63" — **Zahl STALE**, die Größenordnung stimmt.
   Nicht-schreibbare Sektion → HTTP 400 aus `_assert_project_sections_writable`
   (`admin-server.py:5241-5255`) bzw. `_assert_project_update_writable` (`:5257-5274`).
   `docs/ui/admin-ui.html`: 0 Treffer für `spec-plan` und `se_output` (VERIFIED).

2. **`se_output` ist schema-los.** Gelesen in `config.py:2272-2273`, im Schema **nicht
   deklariert** (grep: kein Treffer). Der Wurzel-Knoten erlaubt es nur, weil
   `additionalProperties: true` gesetzt ist (`schema.json:2851-2854`). Damit ist der einzige
   heute wirksame SE-Pfad-Key unvalidiert, unsichtbar im UI und dokumentiert nur in einer
   Konzept-Notiz (`rules/1-generic/se-cascade-artifact-taxonomy.md:10-11`).

### 2.6 Issue-Angaben, die auf HEAD nicht mehr zutreffen (STALE)

| Issue-Angabe | Ist auf HEAD `aaed14c2` | Konsequenz für die Umsetzung |
|---|---|---|
| 8 × `/tmp/opencode` in Reviewer-/Auditor-Rollen | 0 Treffer; Rollen nutzen `{{TMP_SINK_PATH}}` | Die Rewrite-Liste schrumpft; der zu ersetzende Zustand ist „ephemerer Sink", nicht „/tmp" |
| `scripts/lib/config.py:1607-1610` (`se_output`) | `config.py:2269-2273` | Zeilenangaben im Plan nicht übernehmen |
| `scripts/admin-server.py:230-249` / `:4808-4825` | `:234-259` / `:5241-5274` | dito |
| `placeholders.py:76-82` | Allow-List ab `:89`, `SPEC_PLAN_*` auf `:97` | dito |
| „29 of 63 schema sections" | 30 von 70 fehlen, 7 Whitelist-Einträge ohne Schema | AC-1186-07**b** (Follow-up nach #1141) braucht die Union-Regel (§4.4), sonst Regression |
| `orchestrator.md:217` als Literalpfad | `{{#if}}`-Zeile ohne Pfad | nicht rewriten |
| Code-Default `SE_BASE_DIR = "SE"` vs. Regel-Text „Konzept-Default `docs/se`" | Widerspruch im Bestand: `config.py:2273` (`"SE"`) vs. `se-cascade-artifact-taxonomy.md:10` (`docs/se`) | Default in §3.2 **einmal** festgelegt (`SE`, D4); Regel-Text stellt auf `{{ARTIFACT_SE_ROOT}}` um (Plan T20) |

## 3. Soll-Verhalten

### 3.1 Die Matrix

`artifact-locations` ist **eine** Sektion mit Master-Schalter, Preset-Verweis, Defaults,
pro Klasse einem Eintrag und einer globalen `legacy[]`-Liste.

```
artifact-locations:
  enabled: true|false        # Master-Schalter; Default true (= AC-1186-04-Verhalten),
                             # false = exakt heutiges Verhalten (Escape-Hatch für Bestandsprojekte)
  strict: false              # Hook-Durchsetzung: false = warnen, true = blocken (§4.5)
  preset: default            # Auflösungsstufe 3 (framework-weit), gleiche Mechanik wie rules-preset
  defaults:                  # vererbbare Vorgaben je Klasse
    mode: files              # files | inline | off
    naming: "{date}-{slug}.md"   # Token-Kanon, §3.2.1 (D3); human display form
                                 # "<YYYY-MM-DD>-<slug>.md" nur in Rollen-Prosa
    archive: "<path>/archive"
    git: tracked             # tracked | ignored
    retention: manual        # manual | keep | prune   (nur Deklaration, siehe §3.5)
  classes:
    <klasse>: ClassEntry     # 14 Nicht-SE + 9 SE = 23 Einträge
  legacy: [ "<pfad>", ... ]  # additiv, read-only, Projekt-Einträge ergänzen die Framework-Liste
  unmanaged: [ "<pfad>", ... ]  # D-8: deklariert „nicht Artefakt" — keine Klasse, kein
                                # `mode`, kein Scaffold, nie geblockt/gewarnt (auch unter `docs/**`)
```

`ClassEntry` in zwei Formen (Diskriminator: Vorhandensein von `files`):

```
# A) Verzeichnis-Klasse (20: 11 Nicht-SE-Verzeichnisklassen + 9 SE-Klassen;
#    project-docs/scratch/state haben die Formen B/C/D, §4.1)
path:      string      # relativ, kein "..", kein absoluter Pfad, nicht leer
mode:      files|inline|off
git:       tracked|ignored
naming:    string      # Token-Muster, geschlossene Token-Liste nach §3.2.1
                       # (D3): {class} {date} {slug} {kind} {n} {topic}
                       # {scope} {nnn} {level} {folder}
archive:   string      # optional; Default "<path>/archive"
retention: manual|keep|prune
kind:      enum[]      # nur reviews|audits|analysis|reports; geschlossenes Enum (20 Werte, §4.1)
fallback-parent: <klasse>  # optional; nur sinnvoll/möglich bei mode: off (§4.1)
subdir:    string      # nur SE-Klassen; "" erlaubt, nie "..", nie verschachtelt
subdirs:   {name: path}  # nur scratch|state
event-log: string      # nur state

# B) Datei-Set-Klasse (nur project-docs — kein Verzeichnis, kein path)
files:
  architecture:      string
  codebase-overview: string
  requirements:      string
  issue-labels:      string   # docs/issue-labels.md, generiert von #1188 (§3.2, OQ-6)
mode: files|inline|off
fallback-parent: <klasse>     # optional; wie Form A
```

**`kind` — Kardinalität (Review 2026-11-09, WARN `kind`):** `kind` ist auf **beiden** Ebenen
ein geschlossenes Enum, nie ein freier String:
- **Klassen-Ebene** (dieses Feld): die *erlaubte Menge* — Schema `array` mit
  `items: {"enum": [...]}` + `uniqueItems: true` (20 Werte, §4.1).
- **Artefakt-Ebene** (die einzelne Datei): genau **ein** Enum-Wert (`kind: estimate`).
Grund: AC-1186-13 validiert ein *einzelnes* Dokument gegen seinen `kind`; eine Menge pro
Dokument wäre nicht validierbar. Ein unbekannter Wert ist `artifact-locations.kind-invalid`
(§4.1), kein stiller Durchlauf.

**`mode`-Semantik (verbindlich, sonst erfinden Rollen ihr eigenes Verhalten):**

| `mode` | Datei | Rückkanal | Rollen-Effekt |
|---|---|---|---|
| `files` (Default) | ja, unter `path` | Zusammenfassung + Pfad | Rolle schreibt und nennt den Pfad |
| `inline` | nein | Volltext inline | Rolle schreibt keine Datei; ein im Prompt versprochener Pfad ist ein **Consistency-Verstoß** (§4.6) |
| `off` | nein | Klassen-Ausgabe entfällt | Rolle darf diese Klasse nicht produzieren |

`off` braucht eine **Elternklasse**, sonst geht Audit-Evidenz verloren (Issue-Auflage):
`reviews: off` bei aktiver SE-Kaskade → SE-Review-Befunde dürfen nur noch im
REQ-Frontmatter `review_state` landen; das ist im Resolver-Output als
`fallback_parent: se-requirements` auszuweisen. **Das Feld heißt `fallback-parent`** und ist
Teil der Klasse (Form A und B, §4.1) — es ist ein *Klassen-Enum*, kein freier String, damit
`mode-parent-missing` überhaupt prüfbar ist (Review 2026-11-09, RVW-1186-04). `off` ohne
Elternklasse **und** ohne dokumentierte Frontmatter-Senke → **Config-Fehler** (hard error,
§4.1).

**`unmanaged[]` (D-8, RVW2-X-02):** Eine dritte, von `classes` und `legacy[]` getrennte
Liste. Semantik: der Pfad ist **weder** eine Artefakt-Klasse **noch** eine gesperrte
Altablage — er liegt ausdrücklich außerhalb des Artefakt-Vertrags. Wirkung: kein Scaffold,
kein `mode`, kein Naming, kein `legacy-write`-Fund, kein Hook-Block und keine Hook-Warnung
(auch unterhalb von `docs/**`), keine Zählung in AC-1186-12. Additiv wie `legacy[]`
(Framework-Einträge bleiben immer enthalten, ein Projekt kann nur ergänzen).
Anlass: #1188 legt `.meta-config/issue-labels-state.json` als Zustandsdatei an — #1186 kennt nur
`project-docs` und den `.meta-viz`-`state`; ohne Deklaration wäre die Datei ein unklassifizierter
Schreibpfad. Sie wird deshalb als **`unmanaged`** geführt (Negativ-Deklaration, K1: die von #1188
früher vorgeschlagene dritte Kategorie `project-state` ist **gestrichen**). `docs/issue-labels.md`
bleibt **`project-docs`** (`files.issue-labels`, §3.2) und ist **kein** `unmanaged`-Eintrag.

**Nicht verhandelbar:** `path` ist bei den neun SE-Klassen nur die **Wurzel** der Zell-Hierarchie
(`{parent_path}/L{n}/{FolderName}` inkl. Pflicht-Suffix `System`/`Component`,
`se-cascade-artifact-taxonomy.md:13-36`). Die Hierarchie selbst ist SE-Identitätsmodell und
**nicht** konfigurierbar; konfigurierbar sind Wurzel, Leaf-`subdir` und Naming.

### 3.2 Klassen-Defaults (Soll)

**12 persistente Klassen**

| Klasse | `path` Default | `naming` Default | `kind` | `git` | Herkunft/Beleg |
|---|---|---|---|---|---|
| `specs` | `docs/specs` | `{date}-{slug}.md` | — | tracked | Schema `:2235` (bestehender Default) |
| `plans` | `docs/plans` | `{date}-{slug}.md` | — | tracked | Schema `:2239`; `archive: docs/plans/archive` (`rules/1-generic/plan-ledger.md:76`) |
| `concepts` | `docs/concepts` | `{date}-{slug}.md` | — | tracked | neu (heute Root-Datei, `ideation.md:97`) |
| `spikes` | `docs/spikes` | `{date}-issue-{n}-{topic}-spike.md` | — | tracked | Schema `:2243` + `explorer.md:71` (bestehendes Naming beibehalten) |
| `reviews` | `docs/reviews` | `{kind}-{date}-{slug}.md`; `kind: se` → `REVIEW_{date}_{scope}.md` | code, concept, domain, copyedit, proofread, se | tracked | Naming V1 aus `se-critic.md:56` erhalten; `docs/reviews/` existiert bereits |
| `audits` | `docs/audits` | `{kind}-{date}-{slug}.md` | security, dependency, a11y, lifecycle, prompt, ai-security | tracked | neu; heutige Ablage `docs/plans/audit-*.md` → `legacy[]` |
| `analysis` | `docs/analysis` | `{kind}-{date}-{slug}.md` | analysis, triage, perf, log, research, estimate, conclusion | tracked | `docs/analysis/` existiert |
| `reports` | `docs/reports` | `{date}-{slug}.md` (`kind: vv` → `{date}-vv-{slug}.md`); SE-Kontext: `{SE_ROOT}/reports/` (abgeleitet, §3.4) | vv | tracked | AC-1186-04 verlangt `docs/reports`; SE-Projektion **abgeleitet**, nicht konfigurierbar (D-7, RVW-1186-05) |
| `adr` | `docs/adr` | `ADR-{nnn}_{slug}.md` (**D3, DECIDED 2026-11-09**) | — | tracked | `se-cascade-artifact-taxonomy.md:61`, `se-cascade-adr-standard.md:10` (Unterstrich, nicht Bindestrich); SE-Kontext: `{SE_ROOT}/adr/` (§3.4) |
| `traceability` | `docs/traceability` | `TRACE_{scope}.md` | — | tracked | `se-cascade-artifact-taxonomy.md:58`; SE-Kontext: `{SE_ROOT}/traceability/` (§3.4) |
| `runbooks` | `docs/runbooks` | `{date}-{slug}.md` | — | tracked | neu, heute undefiniert |
| `project-docs` | `files:` `docs/ARCHITECTURE.md`, `docs/CODEBASE_OVERVIEW.md`, `docs/REQUIREMENTS.md`, `docs/issue-labels.md` | — (Datei-Set, kein `naming`) | — | tracked | `documenter.md:131-132`; `requirements.md:71`; `docs/issue-labels.md` = generiert von #1188 (OQ-6) |

Die `naming`-Spalte zeigt den **Token-Kanon** (`{token}`, §3.2.1). Die in Rollen-Templates
sichtbare Anzeigeform (`<YYYY-MM-DD>-<slug>.md`) ist nur Prosa und wird von T10 unverändert
weitergeschrieben.

**ADR-Naming und `legacy[]` (D3, DECIDED 2026-11-09):** Von drei beobachteten Formen ist genau
**eine** kanonisch (`ADR-{nnn}_{slug}.md`, regelkonform nach
`rules/1-generic/se-cascade-adr-standard.md:10`). Die beiden anderen Formen
(`NNNN-{slug}.md`, z. B. `docs/adr/0001-pyyaml-runtime-ausnahme.md`, und
`ADR-{nnn}-{slug}.md` mit Bindestrich) sind **`legacy[]`-Muster** (§3.6): bestehende Dateien
werden beim ersten Sync in die Baseline aufgenommen und einmal gemeldet; **neue** ADRs in
diesen Formen melden `artifact-locations.legacy-write` und werden vom Hook geblockt.
`legacy-intersect` greift nicht, weil die Prüfung auf **Pfad-Gleichheit** beruht, nicht auf
Glob-Überlappung — die Muster liegen *innerhalb* von `docs/adr` und sind gewollt.

**2 ephemere Klassen**

| Klasse | `path` Default | `git` | `subdirs` | `retention` | Beleg/Alias |
|---|---|---|---|---|---|
| `scratch` | `.tmp` | ignored | `logs`, `test-output`, `drafts` | manual | **einzige Quelle** (D1, §3.6): `classes.scratch.path`; `repo_containment.tmp-sink.path` ist nur Migrations-Alias |
| `state` | `.meta-viz` | ignored | `progress`, `checkpoints`, `handoffs` | keep | Aliase auf `progress.dir` (Schema `:2812`), `progress.checkpoint-dir` (`:2817`), `viz.event_log` (`:2398`) |

**9 SE-Klassen** — `path` Default einheitlich `SE` (**D4, DECIDED 2026-11-09**: Code-Wahrheit
`config.py:2273`, keine Migration; der Regel-Text
`rules/1-generic/se-cascade-artifact-taxonomy.md` verweist künftig auf
`{{ARTIFACT_SE_ROOT}}` statt auf ein Literal, und `docs/se` wird als `legacy[]`-Muster
gelesen — es ist kein Default und kein zweiter „richtiger" Pfad mehr), `git: tracked`,
`naming` = die in §2.4 belegten Leaf-Muster, `subdir` wie dort.

**Konsequenz (D4):** `docs/se` ist **kein** empfohlener Klassenpfad mehr. Setzt ein Projekt
`classes.se-*.path: docs/se` trotzdem, ist das kein Config-Fehler (`legacy-intersect` prüft
Pfad-Gleichheit, das Muster ist ein Glob), aber der erste Schreibvorgang meldet
`artifact-locations.legacy-write` — das ist das gewollte Migrationssignal, kein stiller
Durchlauf.


**`unmanaged[]` Default (D-8, RVW2-X-02)** — Framework-Liste, read-only, additiv:

| Pfad | Warum unmanaged | Herkunft |
|---|---|---|
| `.meta-config/issue-labels-state.json` | Zustandsdatei des Label-Syncs, kein Artefakt und kein `project-docs`-File | #1188 erzeugt sie, #1186 klassifiziert sie hier |
| `docs/api/**`, `docs/howto/**`, `docs/guides/**`, `docs/testing/**`, `docs/providers/**`, `docs/issues/**`, `docs/se-cascade/**` | von Menschen/Rollen gepflegte Doku-Unterbäume ohne Artefakt-Klasse | OQ-6 / F-3 |

`docs/superpowers/**`, `docs/conclusions/`, `docs/estimates/`, `docs/research/`,
`SE/VV/**`, `docs/se/**` (D4) sowie `docs/adr/[0-9][0-9][0-9][0-9]-*.md` und
`docs/adr/ADR-[0-9][0-9][0-9]-*.md` (D3) bleiben **`legacy[]`** (gesperrt, nicht unmanaged) —
der Unterschied ist „darf nie Artefakt-Inhalt bekommen" vs. „ist kein Artefakt-Ziel".

### 3.2.1 Naming-Token (D3, DECIDED 2026-11-09)

`naming` ist **pro Klasse** konfigurierbar. Wert = String-Pattern aus geschlossenen Tokens
(`{token}`); ein unbekannter Token, ein nicht klassen-anwendbarer Token, ein Pfadseparator
oder `..` ist ein harter Fehler `artifact-locations.naming-invalid` (§4.1).

| Token | Bedeutung | erlaubt in (Form) |
|---|---|---|
| `{class}` | Klassenname (z. B. `reviews`) | alle Klassen mit `naming` (Form A/B) |
| `{date}` | Artefakt-Datum `YYYY-MM-DD` | alle persistenten Klassen |
| `{slug}` | Kurztitel, lowercase, ASCII, keine Leerzeichen | alle persistenten Klassen |
| `{kind}` | genau **ein** `kind`-Wert der Klasse | nur Klassen mit `kind`-Enum (`reviews`, `audits`, `analysis`, `reports`) |
| `{n}` | Issue-Nummer, ohne Null-Padding | `specs`, `plans`, `concepts`, `spikes`, `runbooks` |
| `{topic}` | Topic-Slug (identisch zu `{slug}`, historischer Name) | `specs`, `plans`, `concepts`, `spikes`, `runbooks`, `analysis` |
| `{scope}` | SE-Scope (`System`/`Component`/`all`) | `reviews` (`kind: se`), `reports`, `traceability` |
| `{nnn}` | laufende Nummer, **3-stellig nullgepolstert** (`007`) | `adr` |
| `{level}` | SE-Level (`L0`…`L3`) | 9 SE-Klassen |
| `{folder}` | FolderName der Zelle (ohne `System`/`Component`-Suffix) | 9 SE-Klassen |

Regeln: (a) die Liste ist **geschlossen** — ein Token außerhalb dieser Tabelle ist
`naming-invalid`; (b) ein Token, der für die Klasse nicht anwendbar ist (z. B. `{level}` in
`audits`), ist ebenfalls `naming-invalid`; (c) persistente Datei-Klassen brauchen eine
Datei-Endung (`.md`); `{kind}`-Klassen dürfen `{kind}` weglassen, dann ist der `kind` nur
Frontmatter-Pflicht; (d) die Anzeigeform `<TOKEN>` (z. B. `<YYYY-MM-DD>`) ist **kein**
Konfigurationswert (Schema-Pattern lehnt sie ab, Migrationshinweis im Fehlertext) — sie bleibt
nur in Rollen-Prosa und in dieser Tabelle als Lesefassung zulässig; (e) Naming erzeugt **keine**
zusätzliche Variable: die 54 Namen aus §3.4 bleiben unverändert, das aufgelöste `naming`
erscheint nur in `--status-artifacts --json` (§4.3).

**`vv`:** siehe OQ-1. Empfohlene Auflösung in §3.6 (D-7).

### 3.3 Auflösungspräzedenz und `source`-Reporting

**Vier Wertequellen (plus Source-Attribution)** — Szenario-Konflikt K3. Jede Klasse wird einzeln
aufgelöst, jede Auflösung trägt ihre Herkunft:

```
1. project.yaml  artifact-locations.classes.<klasse>       → source: "project"
2. config/artifact-locations-presets.yaml presets.<name>   → source: "preset:<name>"
   (wählt das Projekt das Preset explizit:                 → source: "project-preset:<name>")
3. config/project-config.schema.json "default"             → source: "schema-default"
4. DEFAULT_*-Konstanten im Resolver                        → source: "code-fallback"
```

**Die Projekt-Preset-Auswahl ist keine eigene Präzedenzstufe.** Sie zeigt auf dieselbe Datei und
dieselbe Zeile wie die Framework-Preset-Stufe; unterscheidbar ist nur die *Attribution*
(`project-preset:<name>` vs. `preset:<name>`) und damit die Antwort auf „hat das Projekt das Preset
gewählt oder der Framework-Default?" (Szenario B10). Zwei Präzedenzstufen für denselben
Datenzugriff wären nicht beobachtbar und sind deshalb zusammengeführt. Es bleiben **vier**
Wertequellen — genau die Zahl, die AC-1186-15 wörtlich verlangt.

**Drei Zustandswerte/Attributionen, die keine Wertequelle sind:**
- `source: "disabled"` — bei `enabled: false` liefern alle Klassen die heutigen Pfade; nichts wird
  umgeleitet (Regel 5).
- `source: "project-preset:<name>"` — Source-Attribution, siehe oben.
- `field_sources[f] = "project-alias:<alter-key>"` — feldweise Attribution, wenn der Wert aus
  einem Legacy-Alias stammt (`repo_containment.tmp-sink.path` → `classes.scratch.path`,
  `se_output.base_dir` → `classes.se-*.path`, `spec-plan-workflow.paths.*` → `classes.*.path`;
  D1, §3.6). `source` bleibt dabei `"project"`, weil der Wert aus der Projekt-Ebene stammt.

Harte Regeln (sonst wird die Override-Kette zum Ratespiel):

1. **Ein Preset gewinnt nie still gegen einen Projekt-Key.** Jede in beiden Ebenen
   vorhandene Klasse ist projekt-gewonnen; das gilt **feldweise** (`path`, `mode`, `git`,
   `naming`, `kind`, `subdir`, `retention`), nicht nur klassenweise.
2. `defaults` der Projekt-Ebene schlägt `defaults` des Presets; ein fehlendes Feld erbt
   von `defaults` → Preset-Klasse → Schema → Code. Die `defaults`-Ebene ist eine
   Feld-Vererbung innerhalb der Quelle „Projekt", **keine** fünfte Wertequelle.
3. Wo keine Schema-`default` existiert und der Code-Fallback greift, ist
   `source: "code-fallback"` **verpflichtend** zu melden (kein stiller Default).
4. `legacy[]` ist additiv: Framework-Einträge sind immer enthalten; ein Projekt kann sie
   ergänzen, nicht entfernen.
5. `enabled: false` → alle Auflösungen liefern die heutigen Pfade mit
   `source: "disabled"`; es wird nichts umgeleitet (AC-1186-09 bleibt auch dann gültig, weil
   nichts neu geschrieben wird).

### 3.4 Generierte Variablen (Rollen-Contract)

`sync.py` exportiert aus der aufgelösten Matrix — **einmal pro Provider**, nicht pro Rolle.
Die Menge ist **abgeschlossen und gezählt** (Review 2026-11-09, RVW-1186-02): `54` Namen,
weil `check_builder_known_set` (`scripts/lib/consistency/placeholders.py:314-335`) **jede**
vom Builder erzeugte Variable gegen `_BUILTIN_VARS` prüft — ein nicht registrierter Name ist
ein ERROR, nicht eine Warnung.

| Gruppe | Anzahl | Namen (`ARTIFACT_`-Präfix, Suffix `_DIR`/`_MODE`/`_FILE`) |
|---|---|---|
| Nicht-SE-Verzeichnisklassen | 13 | `SPECS, PLANS, CONCEPTS, SPIKES, REVIEWS, AUDITS, ANALYSIS, REPORTS, ADR, TRACEABILITY, RUNBOOKS, SCRATCH, STATE` |
| SE-Zell-Klassen (§2.4) | 9 | `SE_REQUIREMENTS, SE_ARCHITECTURE, SE_DECOMPOSITION, SE_INTERFACES, SE_IMPLEMENTATION, SE_TESTPLAN, SE_VALIDATION, SE_VERIFICATION, SE_DECISIONS` |
| SE-Projektion der SE-globalen Klassen (D-7) | 4 | `SE_REVIEWS, SE_REPORTS, SE_ADR, SE_TRACEABILITY` — **abgeleitet** als `{ARTIFACT_SE_ROOT}/<leaf>`, kein Config-Feld |
| SE-Wurzel | 1 | `SE_ROOT` |
| Datei-Set `project-docs` | 4 | `ARCHITECTURE_FILE, CODEBASE_OVERVIEW_FILE, REQUIREMENTS_FILE, ISSUE_LABELS_FILE` |
| Modus je Klasse | 23 | `_MODE` für alle 14 Nicht-SE- **und** alle 9 SE-Klassen (`files|inline|off`) |
| **Summe** | **54** | 13 + 9 + 4 + 1 + 4 + 23 |

Regeln dazu:

- Form: `{{ARTIFACT_<KLASSE>_DIR}}` (Pfad, ohne Trailing-Slash),
  `{{ARTIFACT_<KLASSE>_MODE}}` (`files|inline|off`), `{{ARTIFACT_<KLASSE>_FILE}}` (Datei-Set).
- `scratch`/`state` haben schema-seitig **kein** `mode`-Feld (`artifactEphemeral`/`artifactState`,
  §4.1); ihre `_MODE`-Variable wird als Konstante `files` exportiert, damit der Vertrag
  „jede Klasse hat einen Modus" lückenlos ist (K-1, im Plan T6).
- **Eine Quelle für den Scratch-Bereich (D1, DECIDED 2026-11-09):** `{{ARTIFACT_SCRATCH_DIR}}`
  ist der aufgelöste Wert von `classes.scratch.path`. `{{TMP_SINK_PATH}}` bleibt als
  Laufzeit-Variable erhalten, wird aber **aus der Matrix gespeist**
  (`TMP_SINK_PATH == ARTIFACT_SCRATCH_DIR`, `config.py:2046` wird entsprechend umgedreht).
  Der Name `ARTIFACT_SCRATCH_PATH` aus dem Entscheidungsprotokoll ist damit **kein** 55. Name,
  sondern die Rollen-Variable `{{ARTIFACT_SCRATCH_DIR}}`; die Menge bleibt bei 54.
- **Kein `_NAMING`-Variable:** `naming` ist Validierungs- und Doku-Vertrag, kein
  Rollen-Platzhalter (§3.2.1 e) — sonst würde `check_builder_known_set`
  (`placeholders.py:314-335`) 23 weitere Namen erzwingen.
- Die vier SE-Projektions-Variablen sind **keine** zusätzlichen Klassen (AC-1186-12 bleibt bei
  14 + 9): sie halten die im Bestand belegten Pfade `{SE_BASE_DIR}/reviews/`,
  `{SE_BASE_DIR}/reports/` (`se-critic.md:110,114`) und die SE-globalen `adr`/`traceability`
  unverändert, ohne `classes.<x>.path` zu verdoppeln (D-7).
- `{{SE_BASE_DIR}}` bleibt als **Alias** auf `{{ARTIFACT_SE_ROOT}}` erhalten (bestehende
  Templates und `placeholders.py:89` bleiben gültig).
- `unmanaged[]` (D-8) erzeugt **keine** Variable und keinen `_MODE`: es ist kein
  Rollen-Ziel, sondern eine Negativ-Deklaration (kein Block, keine Warnung, keine Zählung).
- **Builder-Totalität:** `derive_builder_vars` (`placeholders.py:299-306`) ruft die Builder mit
  **leerem** Config-Dict und `project_root=None` auf. `_build_artifact_variables` muss daher
  auf `{}` vollständig definiert sein (Default-Matrix, keine Exception), sonst bricht
  `check_builder_known_set` für **alle** Rollen.
- Aufnahme in die Allow-List (`scripts/lib/consistency/placeholders.py`, Block ab `:89`) ist
  Pflicht — **alle 54** Namen, nicht als Regex-Familie (`placeholders.py:274` verlangt
  Registrierung; Familien sind dynamischen Mengen vorbehalten).
- **`_MODE` ist ein Datenwert, kein Gate.** `{{#if ARTIFACT_<X>_MODE}}` ist heute nicht
  renderbar: `_conditional_active` (`scripts/lib/variables.py:498-508`) aktiviert einen Block
  nur bei der Zeichenkette `"true"`, und `strip_inactive_conditional_blocks`
  (`:570-598`) whitelistet die Conditional-Variablen statisch — ein Modus-String würde den
  Block **nie** entfernen und als `{{#if …}}` in jeden generierten Agenten lecken. Ein
  template-seitiges Modus-Gating braucht deshalb zwei Boolesche Gate-Variablen je Klasse plus
  Whitelist-Eintrag; das ist ein eigenes Follow-up (§11, AC-Präzisierung §6.3).

### 3.5 Scaffolding, Archive, Retention

- `sync.py` legt für jede Klasse mit `mode: files` das Verzeichnis an und schreibt **ein**
  `.gitkeep` (Muster: `spec_plan_scaffold.py:54-61`).
- **Scaffold-Ausnahme (AC-1186-09, Review 2026-11-09 RVW-1186-01):** ein Verzeichnis-Marker
  (`.gitkeep`, `.gitignore`, `.keep`) ist **kein Artefakt**. Er ist die **einzige** erlaubte
  Schreiboperation in einem `legacy[]`-Baum (z. B. `docs/conclusions/.gitkeep`, D-6) und wird
  von **beiden** Durchsetzungswegen ausgenommen: `artifact-locations.legacy-write` (§4.6)
  ignoriert Marker-Dateien, und der Hook (§4.5) blockt sie nie. Ohne diese Ausnahme würde die
  Spec ihr eigenes AC-1186-09 verletzen.
- Verallgemeinerung: `scripts/lib/spec_plan_scaffold.py` → `scripts/lib/artifact_scaffold.py`;
  `scaffold_spec_plan_dirs` bleibt als dünner Wrapper (bestehender Import in
  `sync_pipeline.py:152` und `knowledge.py:12` bleibt funktionsfähig).
- `git: ignored`-Klassen erhalten einen `.gitignore`-Eintrag über den bestehenden
  `gitignore`-Block-Mechanismus (Schema `:949`), nicht durch direktes Editieren.
- `archive` wird nur **deklariert**; verschieben/archivieren ist Nicht-Ziel (§5).
- `retention` wird für `scratch` als **Deklaration + Report** umgesetzt
  (`--status-artifacts` zeigt Alter/Anzahl), nicht als Daemon (Nicht-Ziel).

### 3.6 Alias- und Migrationsregeln (verbindlich)

| Bestehender Key | Neue Quelle | Regel |
|---|---|---|
| `spec-plan-workflow.paths.{specs,plans,spikes}` | `artifact-locations.classes.*.path` | Bei `enabled: true` gewinnt die Matrix; `paths` wird als **deprecated alias** gelesen und bei Sync-Abweichung einmalig gewarnt. Bei `enabled: false` bleibt `paths` alleinige Quelle. |
| `se_output.base_dir` | `artifact-locations.classes.se-*.path` | Matrix gewinnt; `se_output` deprecated, Sync-Warnung mit Ziel-Key. `SE_BASE_DIR` bleibt Alias. |
| `repo_containment.tmp-sink.path` | `classes.scratch.path` | **Eine Quelle (D1, DECIDED 2026-11-09):** `classes.scratch.path` ist die *einzige* Quelle. `tmp-sink.path` wird nur gelesen, solange `classes.scratch` fehlt (Migrations-Alias, `source: "project"` + Attribution `project-alias:repo_containment.tmp-sink.path`), und löst eine Deprecation-Warnung mit Migrationshinweis aus. Sind **beide** gesetzt, müssen die Werte **gleich** sein — Gleichheit ist zulässig (eine Warnung, Alias entfernen), Divergenz ist ein harter Fehler `artifact-locations.scratch-sink-divergence` (§4.1). `TMP_SINK_PATH` bleibt als Laufzeit-Variable erhalten und wird **aus der Matrix** gespeist (§3.4). |
| `progress.dir`, `progress.checkpoint-dir`, `viz.event_log` | `classes.state.subdirs.*`, `event-log` | Wie oben; `state` ist eine **Projektion** der drei Keys, kein zweiter Speicher. Divergenz → Consistency-Warnung. |
| `docs/superpowers/{specs,plans}`, `docs/plans/audit-*.md`, `docs/conclusions/`, `docs/estimates/`, `docs/research/`, `SE/VV/**`, `.meta-viz/handoffs/**`, `docs/se/**`, `docs/adr/[0-9][0-9][0-9][0-9]-*.md`, `docs/adr/ADR-[0-9][0-9][0-9]-*.md` | `legacy[]` | Framework-Liste, read-only, nie mit Artefakt-Inhalt beschrieben (AC-1186-09); Ausnahme: der eine Scaffold-Marker je Verzeichnis (§3.5). Neu in D3/D4: die beiden Nicht-Kanon-Naming-Formen für ADRs und das alte `docs/se`-Verzeichnis. |

**D1 (DECIDED 2026-11-09) — Alias-Semantik und Reichweite.** Alle Zeilen der Tabelle folgen
demselben Muster: die Matrix ist die Quelle, jeder Alt-Key ist ein **Alias** (nicht eine zweite
Quelle), und Aliase tragen eine Attribution `project-alias:<alter-key>` im Feld
`field_sources` — das ist ausdrücklich **keine** fünfte Wertequelle und ändert AC-1186-15
nicht (§3.3, K3). Drei Ausprägungen:

1. **Ersetzend** (`spec-plan-workflow.paths.*`, `se_output.base_dir`, `state`-Projektion):
   Matrix-Wert gewinnt, Abweichung → Warnung.
2. **Migrations-Alias mit Gleichheitszwang** (`scratch`): Alias wird gelesen, solange die
   Klasse fehlt; beide gesetzt ⇒ Werte müssen gleich sein (sonst harter Fehler); in jedem Fall
   Deprecation-Warnung mit Ziel-Key.
3. **Read-only-Liste** (`legacy[]`): additiv, gesperrt, nie Ziel neuer Inhalte.

**Containment-Hook liest den aufgelösten Wert (D1).** `hooks/1-generic/repo-containment*.sh`
liest den Scratch-Pfad nicht mehr als Roh-Key aus `project.yaml`, sondern die **aufgelöste**
Matrix: Präzedenz (1) exportierte Variable `ARTIFACT_SCRATCH_DIR` (sofern der Harness sie
exportiert), (2) `classes.scratch.path` aus
`.meta-config/artifact-locations.resolved.json` (§4.5, dieselbe Datendatei wie der
`artifact-path-guard`), (3) Fallback `repo_containment.tmp-sink.path` (heutiges Verhalten,
fail-closed), (4) Framework-Default `.tmp`. Der Schalter `repo_containment.tmp-sink.enabled`
bleibt **unverändert** zuständig — `scratch` hat kein `enabled`-Feld (§4.1), und ein fehlender
Pfad darf das Gefängnis nie öffnen. Die lexikalischen Regeln (`tmp_sink_path_error`-Parität,
`tests/fixtures/tmp-sink-path-corpus.json`) bleiben unangetastet.

**D-6 (Auflösung der internen AC-Kollision 04↔12):** AC-1186-04 verlangt, dass die Defaults
`docs/{…,conclusions}` **erzeugen**, AC-1186-12 zählt aber genau 14 Nicht-SE-Klassen, in denen
`conclusions` in `analysis` aufgeht. Auflösung: `docs/conclusions` wird als
**Legacy-Zielverzeichnis** angelegt (leer, `.gitkeep`, in `legacy[]`), **nicht** als Klasse;
neue Conclusion-Dokumente gehen nach `docs/analysis` mit `kind: conclusion`.
Damit sind AC-1186-04 und AC-1186-12 gleichzeitig erfüllt. Das `.gitkeep` ist über die
Scaffold-Ausnahme (§3.5) gedeckt und erzeugt **keinen** `legacy-write`-Fund.

**D-7 (`vv`) — entschieden (Review 2026-11-09, RVW-1186-05):** `vv` wird **nicht** als 24.
Klasse geführt. `classes.reports.path` bleibt statisch **`docs/reports`** — so verlangt es
AC-1186-04, und ein statischer Schema-Default kann nicht „je nach SE-Aktivierung" auf die
Kaskaden-Wurzel zeigen. Die im Bestand belegten SE-Pfade `{SE_BASE_DIR}/reports/` und
`{SE_BASE_DIR}/reviews/` (`se-critic.md:110,114`) bleiben über **abgeleitete**
Projektions-Variablen erhalten (§3.4: `ARTIFACT_SE_REPORTS_DIR`, `ARTIFACT_SE_REVIEWS_DIR`,
`ARTIFACT_SE_ADR_DIR`, `ARTIFACT_SE_TRACEABILITY_DIR` = `{ARTIFACT_SE_ROOT}/<leaf>`); sie sind
**kein** Config-Feld, also entsteht keine zweite konfigurierbare Quelle pro Klasse.
`reports.kind` enthält `vv` für die systemweite V&V-Strategie; bestehende `SE/VV/**`-Dateien
stehen in `legacy[]` (read-only). Explizit **Nicht-Ziel**: ein `reports.se-path`-Feld (§5
Nr. 10).

## 4. Öffentliche Contracts

### 4.1 JSON-Schema (`config/project-config.schema.json`)

Skizze der Sektion — vollständig mit `additionalProperties: false` auf jeder Objektebene,
`pattern` für Pfade, `enum` für `mode`/`git`/`retention`/`kind`:

```json
"artifact-locations": {
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": { "type": "boolean", "default": true },
    "strict":  { "type": "boolean", "default": false },
    "preset": { "type": "string", "default": "default" },
    "defaults": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "mode":      { "enum": ["files", "inline", "off"], "default": "files" },
        "naming":    { "allOf": [{ "$ref": "#/$defs/artifactNaming" }],
                       "default": "{date}-{slug}.md" },
        "archive":   { "type": "string" },
        "git":       { "enum": ["tracked", "ignored"], "default": "tracked" },
        "retention": { "enum": ["manual", "keep", "prune"], "default": "manual" }
      }
    },
    "classes": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "specs": { "$ref": "#/$defs/artifactClass" },
        "...": { "$ref": "#/$defs/artifactClass" },
        "se-validation": { "$ref": "#/$defs/artifactSeClass" },
        "project-docs": { "$ref": "#/$defs/artifactFileSet" },
        "scratch": { "$ref": "#/$defs/artifactEphemeral" },
        "state": { "$ref": "#/$defs/artifactState" }
      }
    },
    "legacy": { "type": "array", "items": { "type": "string" }, "default": [] },
    "unmanaged": { "type": "array", "items": { "type": "string" }, "default": [] }
  }
}
```

```json
"$defs": {
  "artifactKind": {
    "enum": ["code", "concept", "domain", "copyedit", "proofread", "se", "vv",
             "security", "dependency", "a11y", "lifecycle", "prompt", "ai-security",
             "analysis", "triage", "perf", "log", "research", "estimate", "conclusion"]
  },
  "artifactClassName": {
    "enum": ["specs", "plans", "concepts", "spikes", "reviews", "audits", "analysis",
             "reports", "adr", "traceability", "runbooks", "project-docs", "scratch", "state",
             "se-requirements", "se-architecture", "se-decomposition", "se-interfaces",
             "se-implementation", "se-testplan", "se-validation", "se-verification",
             "se-decisions"]
  },
  "artifactNaming": {
    "type": "string",
    "minLength": 1,
    "description": "Closed token pattern (D3). Allowed tokens: {class} {date} {slug} {kind} {n} {topic} {scope} {nnn} {level} {folder}. No path separator, no '..'. Class applicability and the file extension are enforced by the semantic validator (artifact-locations.naming-invalid).",
    "pattern": "^(?!.*\\.\\.)(?:[^{}/]|\\{(?:class|date|slug|kind|n|topic|scope|nnn|level|folder)\\})+$"
  },
  "artifactClass": {
    "type": "object", "additionalProperties": false,
    "properties": {
      "path":   { "type": "string", "minLength": 1, "pattern": "^(?!/)(?!.*(^|/)\\.\\.(/|$)).+$" },
      "mode":   { "enum": ["files", "inline", "off"] },
      "git":    { "enum": ["tracked", "ignored"] },
      "naming": { "$ref": "#/$defs/artifactNaming" },
      "archive":{ "type": "string" },
      "retention": { "enum": ["manual", "keep", "prune"] },
      "kind":   { "type": "array", "items": { "$ref": "#/$defs/artifactKind" }, "uniqueItems": true },
      "fallback-parent": { "$ref": "#/$defs/artifactClassName" }
    }
  },
  "artifactSeClass": {
    "type": "object", "additionalProperties": false,
    "properties": {
      "path":   { "type": "string", "minLength": 1, "pattern": "^(?!/)(?!.*(^|/)\\.\\.(/|$)).+$" },
      "mode":   { "enum": ["files", "inline", "off"] },
      "git":    { "enum": ["tracked", "ignored"] },
      "naming": { "$ref": "#/$defs/artifactNaming" },
      "archive":{ "type": "string" },
      "retention": { "enum": ["manual", "keep", "prune"] },
      "fallback-parent": { "$ref": "#/$defs/artifactClassName" },
      "subdir": { "type": "string", "pattern": "^[^/]*$" }
    }
  },
  "artifactFileSet": {
    "type": "object", "additionalProperties": false,
    "required": ["files"],
    "properties": {
      "files": {
        "type": "object", "additionalProperties": false,
        "properties": {
          "architecture":      { "type": "string" },
          "codebase-overview": { "type": "string" },
          "requirements":      { "type": "string" },
          "issue-labels":      { "type": "string" }
        }
      },
      "mode": { "enum": ["files", "inline", "off"] },
      "fallback-parent": { "$ref": "#/$defs/artifactClassName" }
    }
  },
  "artifactEphemeral": {
    "type": "object", "additionalProperties": false,
    "properties": {
      "path": { "type": "string" },
      "git":  { "enum": ["ignored", "tracked"] },
      "retention": { "enum": ["manual", "keep", "prune"] },
      "subdirs": { "type": "object", "additionalProperties": { "type": "string" } }
    }
  },
  "artifactState": {
    "type": "object", "additionalProperties": false,
    "properties": {
      "path": { "type": "string" },
      "git":  { "enum": ["ignored", "tracked"] },
      "retention": { "enum": ["manual", "keep", "prune"] },
      "subdirs": { "type": "object", "additionalProperties": { "type": "string" } },
      "event-log": { "type": "string" }
    }
  }
}
```

**`fallback-parent` (RVW-1186-04):** Pflicht-*Feld für die Prüfbarkeit*, nicht Pflichtwert.
`mode: off` **ohne** `fallback-parent` **und** ohne dokumentierte Frontmatter-Senke ist
`artifact-locations.mode-parent-missing` (§4.1-Fehlertabelle). Draft-07 kann diese
Bedingung nicht ausdrücken (`if/then` über ein Feld, das bei `mode != off` fehlen darf, wäre
zwar möglich, würde aber die `additionalProperties: false`-Notiz unten verletzen) — die Regel
liegt deshalb im **semantischen** Validator (`config.py`, T5), das Enum selbst im Schema.

> **Schema-Notiz (draft-07, `schema.json:2`):** Die drei Sonderformen sind **vollständig**
> ausgeschrieben statt per `allOf` komponiert. Grund: `additionalProperties: false` wirkt in
> draft-07 nur auf die im *selben* Subschema deklarierten `properties`; eine Komposition
> über `allOf` würde `subdir`/`event-log` fälschlich als „additional" ablehnen. Bestehendes
> Test-Muster für „unbekannter Subkey → Fehler": `tests/test_context_topology_schema.py`
> (`test_topology_unknown_subkey_rejected`).
>
> **`$defs` unter Draft-07 (Review-Auflösung K6):** Die Skizze bleibt bei `$defs`, weil das
> Ist-Schema `draft-07` deklariert (`:2`) und trotzdem `$defs` verwendet (`:2855`). Der
> JSON-Pointer `#/$defs/…` löst auf (Szenario A18); `definitions` wäre nur bei einem
> gleichzeitigen Wechsel des Gesamtschemas richtig. Konsistenz mit dem Ist-Schema hat Vorrang
> vor der strikten Keyword-Wahl.

**Validierungsfehler (hard, vor jedem Schreibvorgang, Muster `config.py:808` `_fail`):**

| Code | Bedingung | Meldung (Form) |
|---|---|---|
| `artifact-locations.path-invalid` | `path` absolut, leer, `..`, außerhalb des Projekt-Roots | `invalid 'artifact-locations.classes.<x>.path': must stay inside the project root` |
| `artifact-locations.mode-parent-missing` | `mode: off` ohne `fallback-parent` **und** ohne dokumentierte Frontmatter-Senke | `invalid 'artifact-locations.classes.<x>.mode': 'off' requires 'fallback-parent' or a frontmatter sink` |
| `artifact-locations.fallback-parent-unknown` | `fallback-parent` nennt keine der 23 Klassen (Schema-Enum deckt den Fall bereits ab; Code nur für die semantische Zweitprüfung) | `invalid 'artifact-locations.classes.<x>.fallback-parent': unknown class '<c>'` |
| `artifact-locations.se-required-off` | `se-requirements: off` bei aktiver Kaskade (`SE_ENABLED` bzw. `systems-engineering.enabled`) | `invalid 'artifact-locations.classes.se-requirements.mode': the cascade cannot start without requirements` |
| `artifact-locations.subdir-invalid` | `subdir` enthält `/`, `..` oder ist keine flache Komponente | `invalid 'artifact-locations.classes.se-validation.subdir': must be a single path segment` |
| `artifact-locations.kind-invalid` | `kind`-Wert nicht im geschlossenen Enum (`$defs/artifactKind`, 20 Werte) oder `kind` bei einer Klasse ohne `kind`-Feld | `invalid 'artifact-locations.classes.<x>.kind': '<v>' is not a known artifact kind` |
| `artifact-locations.unknown-preset` | `preset` nicht in `config/artifact-locations-presets.yaml` | `invalid 'artifact-locations.preset': unknown preset '<name>'` |
| `artifact-locations.legacy-intersect` | `legacy[]`-Eintrag ist mit einem aktiven Klassen-`path` identisch | `invalid 'artifact-locations.legacy': '<p>' is also an active class path` |
| `artifact-locations.unmanaged-intersect` | `unmanaged[]`-Eintrag ist mit einem aktiven Klassen-`path` identisch (D-8) | `invalid 'artifact-locations.unmanaged': '<p>' is also an active class path` |
| `artifact-locations.scratch-sink-divergence` | `classes.scratch.path` **und** `repo_containment.tmp-sink.path` sind gesetzt und **verschieden** (D1) | `invalid 'artifact-locations.classes.scratch.path' vs 'repo_containment.tmp-sink.path': values diverge — keep one source (artifact-locations.classes.scratch.path) and remove the legacy key` |
| `artifact-locations.naming-invalid` | `naming` enthält einen unbekannten Token, einen für die Klasse nicht anwendbaren Token, einen Pfadseparator, `..`, die Anzeigeform `<TOKEN>` oder eine fehlende Datei-Endung bei persistenter Datei-Klasse (§3.2.1, D3) | `invalid 'artifact-locations.classes.<x>.naming': unknown token '{<t>}' (allowed: {class} {date} {slug} {kind} {n} {topic} {scope} {nnn} {level} {folder})` |

**Elf harte Fehlercodes** (Revision 2: `unmanaged-intersect` ergänzt, RVW2-X-02;
Revision 4: `scratch-sink-divergence` und `naming-invalid` ergänzt, D1/D3).
`scratch-sink-divergence` und `naming-invalid` prüft der semantische Validator (T5), das
Schema liefert für `naming` bereits einen lexikalischen `pattern`-Fehler (§4.1, D3).

`se-decomposition: off` ist **ausdrücklich zulässig** (AC-1186-11): die Decomposition darf der
Architekt direkt schreiben; nur `se-requirements` ist startkritisch.

### 4.2 Preset-Datei `config/artifact-locations-presets.yaml` (neu)

Daten, kein Code — Vorbild `config/rules-presets.yaml:47-50` (Top-Level `presets:`).
Pflicht-Presets:

```yaml
version: 1
presets:
  default:    # die Matrix aus §3.2
    classes: { specs: {path: docs/specs}, plans: {path: docs/plans},
               adr: {naming: "ADR-{nnn}_{slug}.md"}, ... }
    legacy:  [docs/superpowers/specs, docs/superpowers/plans, docs/plans/audit-*.md,
              docs/specs/*-review.md, docs/conclusions/, docs/estimates/, docs/research/,
              SE/VV/**, .meta-viz/handoffs/**, docs/se/**,
              docs/adr/[0-9][0-9][0-9][0-9]-*.md, docs/adr/ADR-[0-9][0-9][0-9]-*.md]
  minimal:    # nur specs/plans/reviews/audits aktiv (files); alle anderen inline
  flat:       # alles direkt unter docs/, keine Subfolder
  docs-only:  # ephemeral (scratch, state) = off
```

Regeln: (a) Presets dürfen nur Felder setzen, die das Schema kennt (`additionalProperties: false`
gilt auch hier); (b) ein unbekanntes Preset ist ein harter Fehler (§4.1), kein stiller
`default`-Fallback; (c) Presets werden **nicht** in `project.yaml` kopiert — nur der Name;
(d) `naming`-Werte in Presets folgen dem Token-Kanon (§3.2.1) — ein Preset mit `<TOKEN>`-Form
ist `artifact-locations.naming-invalid`, kein stiller Durchlauf (D3); (e) die beiden
ADR-Legacy-Muster und `docs/se/**` stehen in **jedem** Preset, weil sie Framework-Herkunft
haben (additive `legacy[]`-Regel, §3.3 Regel 4).

### 4.3 CLI `sync.py --status-artifacts [--json]`

```
sync.py --status-artifacts          # Menschen-Tabelle, eine Zeile pro Klasse
sync.py --status-artifacts --json   # Maschinen-Vertrag
Exit 0: alle Klassen aufgelöst
Exit 2: mindestens eine Klasse nicht auflösbar (Key + Grund auf stderr, KEIN Default-Druck)
```

JSON-Vertrag (`schema_version: "1"`, stabil, additiv erweiterbar):

```json
{
  "schema_version": "1",
  "enabled": true,
  "preset": "default",
  "unmanaged": [".meta-config/issue-labels-state.json", "docs/api/**", "docs/howto/**"],
  "classes": {
    "specs": {
      "path": "docs/specs", "mode": "files", "git": "tracked",
      "naming": "{date}-{slug}.md",
      "source": "schema-default",
      "exists": true, "file_count": 12,
      "newest": "2026-11-09-artifact-locations-matrix-spec.md",
      "kinds": [], "subdir": "",
      "legacy_hits": [], "violations": []
    },
    "scratch": {
      "path": ".tmp", "mode": "files", "git": "ignored",
      "source": "project",
      "field_sources": { "path": "project-alias:repo_containment.tmp-sink.path" },
      "exists": true, "file_count": 0, "kinds": [], "subdir": "",
      "legacy_hits": [], "violations": []
    },
    "project-docs": {
      "files": { "architecture": "docs/ARCHITECTURE.md",
                 "codebase-overview": "docs/CODEBASE_OVERVIEW.md",
                 "requirements": "docs/REQUIREMENTS.md",
                 "issue-labels": "docs/issue-labels.md" },
      "mode": "files", "source": "schema-default", "exists": true, "missing": [],
      "legacy_hits": [], "violations": []
    }
  }
}
```

Pflichtfelder pro Klasse laut AC-1186-14: `path`, `mode`, `source`, `exists`.
Additiv (nicht pflichtig): `naming` (Token-Kanon, D3) und `field_sources` (feldweise Herkunft,
inkl. `project-alias:<key>` bei Alias-Auflösung, D1).
`unmanaged` erscheint ausschließlich als **Top-Level-Liste** und **nie** in `classes`
(D-8): es ist keine Klasse, zählt nicht in AC-1186-12 und hat keinen Modus.
`violations[]` enthält Objekte `{code, path, expected}` mit den Codes aus §4.6.
Namenskollision beachten: `--status` existiert bereits mit anderer Bedeutung
(`scripts/sync.py:406`, Plan-Ledger/Checkpoint) — `--status-artifacts` ist ein eigener,
vollständiger Flag-Name und darf nicht zu `--status` abgekürzt werden.

### 4.4 Admin-UI-API

Bestehende Routen werden genutzt, keine neuen Endpunkte:

- **Lesen:** `GET /api/config/artifact-locations` über den Prefix-Router
  `/api/config/` → `_route_get_config` (`scripts/admin-server.py:3696-3697`).
- **Schreiben:** `PUT /api/config/project/section` mit `{"section": "artifact-locations",
  "data": {...}}` → `_write_project_section` (`:3707-3708`, `:5276-5311`).
- **Whitelist (AC-1186-07, präzisiert 2026-11-09):** `artifact-locations` wird in
  `PROJECT_WRITABLE_SECTIONS` (`scripts/admin-server.py:234-259`) **handgepflegt** aufgenommen
  (eine Zeile, T17) — das ist der Teil von AC-1186-07, den **dieses** Issue liefert.
  Die **Ableitung** `_SCHEMA_SECTIONS ∪ _RUNTIME_ONLY_SECTIONS` (damit die Whitelist nicht
  mehr driftet) ist ein **eigenes Follow-up nach #1141** (§9, Plan T22): sie liest das
  Wurzel-`properties`, und solange dort `additionalProperties: true` steht
  (`schema.json:2851-2854`), würde die Ableitung eine noch unvalidierte Wurzel als Wahrheit
  setzen und ohne die Union-Regel 7 Runtime-Sektionen regressieren (F-2 in §8).
  Verboten bleibt eine reine Schema-Ableitung, weil sie `agent-prompts`, `steps-overrides`,
  `rules`, `environments`, `skills-registry`, `backup`, `submodule-protection` entfernt.
- **Pfad-Validierung beim Schreiben:** neuer Guard `_guard_artifact_locations_write`,
  aufgerufen im bestehenden Guard-Block (`:5295-5308`) **vor** jedem Disk-Write:
  relativ, kein `..`, kein absoluter Pfad, `safe_path(project_root, path)` ohne
  `ValueError` (`scripts/lib/io.py:663-678`). Verstoß → `ValueError` → HTTP 400 mit
  Feldnamen im Text (`invalid 'artifact-locations.classes.specs.path': ...`).
- **UI:** neuer Bereich „Artifacts" in `docs/ui/admin-ui.html` — eine Zeile pro Klasse
  (Pfad, Modus-Select, git-Select, Naming), `legacy[]` als **read-only** Liste,
  Resolver-Vorschau „Rolle X schreibt nach Y" auf Basis von `--status-artifacts --json`.

### 4.5 Hook-Enforcement-Vertrag

Neuer Hook `hooks/1-generic/artifact-path-guard.sh` — Kopiervorlage für den Kopf
(`hooks/1-generic/repo-containment.sh:1-8`), Registrierung ist generisch
(`scripts/lib/hooks.py` sammelt `hooks/0-external|1-generic|2-platform`, `:84-95`).

```
# hook: artifact-path-guard
# version: 1.0.0
# event: PreToolUse
# matcher: ""
# description: Route artifact writes into the configured artifact-locations class path.
# enabled_by_default: false        # Opt-in: erst nach einem Release mit Warn-Modus
```

**Datenquelle (IC-H1):** der Hook liest die **aufgelöste** Matrix aus einer von `sync.py`
geschriebenen Datendatei `.meta-config/artifact-locations.resolved.json` (Präzedenzfall:
`sync.py` schreibt `.meta-config/auto-commit-allowlist.json`,
`scripts/lib/sync_pipeline.py:1893-1921`). Der Hook ruft **keinen** Python-Resolver pro
Schreibvorgang auf (Latenz) und liest **kein** YAML.

**Zweiter Konsument derselben Datei (D1):** der bestehende
`hooks/1-generic/repo-containment*.sh` liest den Scratch-Pfad aus derselben Datendatei
(`classes[].name == "scratch"` → `path`), nicht mehr roh aus `project.yaml`. Präzedenz und
Fallback-Kette stehen in §3.6; `repo_containment.tmp-sink.enabled` bleibt der Schalter. Beide
Hooks teilen damit **eine** aufgelöste Wahrheit, ohne einen zweiten Resolver.

**Datenform (IC-H2, stabil):**

```json
{ "schema_version": "1", "enabled": true, "strict": false, "root": "/abs/project",
  "classes": [ {"name": "reviews", "path": "docs/reviews", "mode": "files",
                "naming": "{kind}-{date}-{slug}.md",
                "patterns": ["docs/reviews/**"]} ],
  "legacy": ["docs/superpowers/specs/**", "docs/plans/audit-*.md"],
  "unmanaged": ["docs/api/**", ".meta-config/issue-labels-state.json"],
  "baseline": { "generated_at": "2026-11-09T12:00:00Z",
                "legacy_files": ["docs/plans/audit-2026-09-detailed-system-audit.md"] } }
```

**`baseline` (RVW2-1186-02, deterministische AC-09-Basis):** `legacy_files` ist das
**beim Sync erfasste Inventar** der Artefakt-Dateien in `legacy[]`-Bäumen (Marker-Dateien
ausgenommen). Der Consistency-Check vergleicht ausschließlich gegen diese Liste — **kein**
mtime-Vergleich, keine „nach dem letzten Sync"-Heuristik. `generated_at` dient nur der
Diagnose. `unmanaged` (D-8) wird mitgeschrieben, damit der Hook auch Ziele unterhalb von
`docs/**` durchlässt, die nur als unmanaged deklariert sind.

**Entscheidungstabelle (IC-H3):**
| Fall | `strict: false` (Default) | `strict: true` |
|---|---|---|
| Ziel ist ein Verzeichnis-Marker (`.gitkeep`, `.gitignore`, `.keep`) | allow | allow (Scaffold-Ausnahme, §3.5) |
| Ziel liegt im Projekt-Root, **nicht** in einem verwalteten Baum (`src/`, `tests/`) | allow | allow |
| Ziel liegt unter dem `path` seiner Klasse | allow | allow |
| Ziel liegt unter einem **verwalteten** Baum (`docs/**`, `.tmp/**`, `.meta-viz/**`), aber nicht in seiner Klasse | **warn** (stderr, rc 0) | **block** (rc 2, Meldung nennt erwarteten Pfad) |
| Ziel trifft ein `legacy[]`-Muster (Artefakt-Inhalt, nicht Marker) | **block** (rc 2) | block (rc 2) |
| Ziel trifft ein `unmanaged[]`-Muster (D-8, auch unter `docs/**`) | allow | allow |
| Ziel außerhalb des Projekt-Roots | unverändert `repo-containment` (dieser Hook prüft es nicht) | dito |
| Datei fehlt/unlesbar/kaputtes JSON | allow + eine Warnzeile (fail-open, Convention boundary) | allow + Warnzeile |

**Auswertungsreihenfolge (verbindlich, D3):** Marker → `unmanaged[]` → **`legacy[]`** →
Klassen-`path` → verwalteter Baum → Root. Der `legacy[]`-Schritt steht **vor** der
Klassen-Freigabe, weil die ADR-Legacy-Muster (`docs/adr/[0-9][0-9][0-9][0-9]-*.md`) *innerhalb*
des aktiven Klassenpfads `docs/adr` liegen: nur so bleibt „neue ADRs in Nicht-Kanon-Form werden
geblockt" (D3) mit „Ziel unter seinem Klassenpfad ist erlaubt" widerspruchsfrei.

**Verhältnis zu AC-1186-09 (RVW-1186-01):** Der Hook ist `enabled_by_default: false` und blockt
im Auslieferungszustand **nichts** — die Issue-Formulierung „`legacy[]` paths never receive new
writes" wird deshalb **zweistufig** erfüllt und ehrlich benannt:
1. **sofort, ohne Opt-in:** `artifact-locations.legacy-write` (§4.6) meldet jeden
   Inhalts-Schreibvorgang in einem `legacy[]`-Pfad beim Sync/Consistency-Lauf;
2. **nach Aktivierung:** der Hook blockt Legacy-Ziele in **beiden** `strict`-Zuständen (die
   Zeile ist bewusst `strict`-unabhängig), Marker-Dateien nie.
Der Default `false` bleibt, weil der Hook eine Routing-Konvention und keine Security Boundary
ist; `enabled_by_default: true` würde jedes Bestandsprojekt mit `docs/plans/audit-*.md` beim
ersten Schreibversuch blocken. AC-1186-09 wird in §6.2 entsprechend präzisiert.

Begründung fail-open: der Hook ist **keine** Security Boundary, sondern eine
Routing-Konvention (Terminologie wie `rules/1-generic/repo-containment.md:5`); ein
Routing-Guard darf nie die einzige Reparaturmöglichkeit blockieren (Lehre aus dem
Self-Health-Split, `repo-containment.sh:11-34`). `strict` ist ein eigenes Feld in
`artifact-locations` und wird erst nach einem Release mit Warn-Modus Default.

**Nicht-Zuständigkeit:** der Hook prüft keine Inhalte, keine Dateiendungen, keine
`default-branch`-Policies; er schreibt nichts um und legt keine Verzeichnisse an.

### 4.6 Consistency-Check

Neues Modul `scripts/lib/consistency/artifact_locations.py`, Registrierung analog
`scripts/consistency-check.py:42-68` (Import) und `:238-249` (Aufruf).

| Check-ID | Severity | Bedingung |
|---|---|---|
| `artifact-locations.literal-path` | violation | Rollen-Template enthält einen **aktiven Klassenpfad** als Literal (`docs/specs`, `docs/plans`, `docs/spikes`, `docs/concepts`, `docs/reviews`, `docs/audits`, `docs/analysis`, `docs/reports`, `docs/adr`, `docs/traceability`, `docs/runbooks`, `plan-*.md`, `concept-*.md`) statt `{{ARTIFACT_*_DIR}}` — **in Schreibposition** (siehe Abgrenzung unten) |
| `artifact-locations.legacy-write` | warning | Datei in einem `legacy[]`-Baum, die **nicht** in der Baseline steht (`baseline.legacy_files` aus `.meta-config/artifact-locations.resolved.json`, §4.5) und Artefakt-Inhalt trägt. Baseline = beim Sync erfasstes Inventar, **kein** mtime-Vergleich (RVW2-1186-02). Höchstens **ein** Finding pro Datei und Lauf, nichts wird gelöscht. Verzeichnis-Marker (`.gitkeep`/`.gitignore`/`.keep`) sind ausgenommen (§3.5). Fehlt die Baseline, meldet der Check nichts und schreibt **eine** Warnzeile auf stderr (fail-open, kein neuer Check-Code) |
| `artifact-locations.inline-with-path-promise` | violation | Klasse `inline`/`off`, während das Rollen-Template einen Pfad verspricht (`**Output file:**`, `Persisted to:`, `ARTIFACTS: <path>`) |
| `artifact-locations.missing-dir` | info | Klasse mit `mode: files`, deren Verzeichnis im Projekt fehlt |
| `artifact-locations.alias-divergence` | warning | `state`↔`progress.*`/`viz.event_log` divergieren. **Nicht** hier: `scratch`↔`tmp-sink.path` — diese Divergenz ist ein harter Config-Fehler `artifact-locations.scratch-sink-divergence` (§4.1, D1), weil sie zwei Schreibziele für dieselbe Senke erzeugen würde |

**Lese- vs. Schreib-Literal (RVW-1186-06):** `literal-path` prüft **Schreibpositionen**, nicht
jedes Vorkommen. Ein Literal gilt als Lese-/Scan-Position, wenn die Zeile den Marker
`<!-- artifact-read-ok -->` trägt; der Marker ist eine **schrumpfende** Ausnahme (Ratchet,
Vorbild `_UNREGISTERED_BUILDER_RATCHET`, `placeholders.py:275-284`) und startet mit **genau
zwei** Zeilen: `knowledge-migrator.md:39` und `:50` (Bestands-Scan bzw. OKF-Type-Mapping —
dort sind `docs/conclusions/`, `docs/adr/`, `docs/api/` bewusst Eingabe-Pfade, keine Ziele).
Jede weitere Zeile ist eine Violation; ein Test pinnt die Anzahl auf 2 und verbietet Wachstum.
Schreibpositionen (z. B. `documenter.md:81` `docs/plans/archive`) müssen die Variable nutzen —
Lese-Literale rechtfertigen keine Schreib-Literale.

**Abgrenzung zu bestehenden Checks (Pflicht, sonst Doppelmeldungen):**

- `temp-literal.system-temp` (`scripts/lib/consistency/temp_literals.py:24-27`) bleibt
  zuständig für System-Temp-Literale (`/tmp/`, `%TEMP%`); `artifact-locations` prüft
  **verwaltete Projektpfade**. Überschneidung ist ausgeschlossen, weil die Muster disjunkt sind.
- `context.dangling-pointer` (`context_budget.py`, siehe #1180) bleibt für Skill-Pointer
  zuständig; `artifact-locations` prüft **Artefakt-Ziele**, nicht Doku-Links.
- Alle fünf Checks sind bei `enabled: false` **still** (Issue-Auflage).
- `unmanaged[]`-Ziele (D-8) lösen **keinen** der fünf Checks aus — auch nicht
  `literal-path` oder `missing-dir`; `docs/api/**` ist Doku, kein Artefakt-Ziel.

### 4.7 Platzhalter-Allow-List

`scripts/lib/consistency/placeholders.py` (Allow-List ab `:89`) muss **alle 54**
`ARTIFACT_*`-Namen aus §3.4 kennen. Zwei Tests, in dieser Richtung:

1. `derive_builder_vars(agent_meta_root) ⊆ _BUILTIN_VARS` — genau der Vertrag, den
   `check_builder_known_set` (`:314-335`) erzwingt, mit einer expliziten Menge von 54 Namen
   statt der bisherigen Behauptung „26 Namen" (RVW-1186-02).
2. Jedes in `agents/`, `rules/`, `snippets/` verwendete `{{ARTIFACT_*}}` ist registriert
   (keine unbekannten Platzhalter).

**Bewusst nicht gefordert:** „jedes deklarierte wird mindestens einmal verwendet". Die Menge
ist der *Vertrag der Klassen-Registry*, nicht die Schnittmenge mit den heute umgestellten
Templates (`ARTIFACT_STATE_MODE` oder `ARTIFACT_ISSUE_LABELS_FILE` haben zum
Auslieferungszeitpunkt ggf. keinen Aufrufer). Ein Leichen-Test würde die Registrierung an
Template-Zufälle koppeln und den nächsten Rollen-Rewrite blockieren.

## 5. Nicht-Ziele

1. **Kein Verschieben, Archivieren oder Löschen bestehender Artefakte.** Migration ist
   opt-in und separat; `legacy[]` ist read-only.
2. **Kein Retention-Daemon** für `.tmp/` (nur Deklaration + Report, §3.5).
3. **Keine Änderung der SE-Zellstruktur** (`L{n}`/`System`/`Component`-Hierarchie bleibt
   Identitätsmodell); nur Wurzel, `subdir` und Naming sind konfigurierbar.
4. **Keine Änderung der Knowledge-Engine-Pfade** (`knowledge-engine` besitzt sein Bundle).
5. **Keine neuen Endpunkte** im Admin-Server; nur die bestehenden Routen (§4.4).
6. **Kein neuer always-on-Rule-Kanal** (H-1/AC-1186-16): die Matrix wird als Variablen +
   **ein** Lazy-Skill ausgeliefert.
7. **Keine Provider-Verzweigung im Code** — Unterschiede nur über Config-/Capability-Keys
   (Projektregel `provider-agnostic`).
8. **Keine per-Rollen-Pfad-Overrides** (Klasse ist die kleinste Einheit).
9. **Keine automatische Reparatur** von Verstößen durch Hook oder Consistency-Check.
10. **Keine zweite konfigurierbare Pfad-Quelle je Klasse** — kein `reports.se-path`, kein
    `reviews.se-path`: die SE-Projektion der SE-globalen Klassen ist **abgeleitet**
    (`{ARTIFACT_SE_ROOT}/<leaf>`, §3.4), nicht konfigurierbar (D-7).
11. **Keine Doppelsenke für `scratch`** (D1): `repo_containment.tmp-sink.path` ist ein
    Migrations-Alias und wird nie als gleichwertige Konfiguration dokumentiert, geschrieben oder
    in Beispielen beworben; neue Projekte setzen ausschließlich
    `artifact-locations.classes.scratch.path`.
12. **Keine automatische Umschreibung der Token-Anzeigeform** (D3): `<TOKEN>`-Strings in
    Rollen-Prosa werden nicht nach `{token}` konvertiert — Rollen-Prosa bleibt Lesetext, nur
    Config-Werte folgen dem Token-Kanon.

## 6. Akzeptanzkriterien

Das Issue nummeriert die Punkte 1–20 fortlaufend; die **vier** Punkte 1–4 sind
Hygiene-Vorgaben (Constraints), die **16** Punkte 5–20 sind die Acceptance Criteria
(diese Lesart deckt sich mit #1187, das „acceptance criterion 16" mit dem Wortlaut von
Issue-Punkt 20 zitiert). Nummerierung hier: `AC-1186-01` … `AC-1186-16` in Issue-Reihenfolge.

### 6.1 Hygiene-Vorgaben (Issue-Punkte 1–4, wörtlich — Constraints, keine ACs)

- [ ] **H-1** — „The matrix is delivered as **generated variables** (`{{ARTIFACT_*_DIR}}`, `{{ARTIFACT_*_MODE}}`) plus **one** lazy skill (`channel: skill`), never as an always-on rule embedded in every provider's context file."
- [ ] **H-2** — „`sync.py` renders the variable block once per provider, from the resolved matrix — no per-role literal, no per-role copy."
- [ ] **H-3** — „The lazy-pointer table in `rules/1-generic/use-lazy-rules.md` is **hand-maintained today and already drifts** … New artifact skill names must be generated into that table, or the table must be dropped in favour of a generated index. Tracked as related to #1180."
- [ ] **H-4** — „`{{PROJECT_CONTEXT}}` appears in **70 of 98** role templates … this request only must not add another such duplication."

**Zahlen-Notiz (Revision 2, RVW2-1186-03):** H-4 zitiert „70 of 98" aus dem Issue. Auf HEAD
`aaed14c2` sind es **83 von 98** Rollen-Templates (84 von 101 Dateien,
`docs/specs/2026-11-09-project-context-injection-scope-spec.md:43`). Der Issue-Wortlaut bleibt
als Zitat stehen; als Gate gilt die **relative** Assertion „die Anzahl wächst nicht"
(Plan T13) — keine absolute Zahl.

### 6.2 Acceptance Criteria (Issue-Punkte 5–20, wörtlich)

- [ ] **AC-1186-01** — „`artifact-locations` is declared in `config/project-config.schema.json` (`additionalProperties: false`, per-class `path`/`mode`/`git`/`naming`, `legacy[]`)."
- [ ] **AC-1186-02** — „`sync.py` resolves the matrix, exports the `ARTIFACT_*` variables, and scaffolds every class with `mode: files` (dry-run lists them, `--dry-run` writes nothing)."
- [ ] **AC-1186-03** — „No role template contains a literal managed artifact path; `grep -rn "/tmp/opencode" agents/ rules/` is empty."
  - → Präzisierung: **[§6.3.1 (AC-03)](#ac-03)** — Schreibposition statt „jedes Vorkommen",
    Lese-Literale nur per 2-Zeilen-Ratchet.
- [ ] **AC-1186-04** — „Defaults produce `docs/{specs,plans,concepts,spikes,reviews,audits,analysis,reports,adr,traceability,conclusions}`; `reviews`/`audits` exist after a fresh sync in a project without them."
- [ ] **AC-1186-05** — „Per-class `mode: off` / `inline` changes role behaviour deterministically and is covered by a test per mode."
  - → Präzisierung: **[§6.3.2 (AC-05)](#ac-05)** — deterministisch über Resolver/Scaffold/
    Consistency/Status; **kein** Template-Gate.
- [ ] **AC-1186-06** — „Admin UI can read, edit and save the section; a PUT with `path: "../x"` is rejected (HTTP 400) with a message naming the field."
- [ ] **AC-1186-07** — „`PROJECT_WRITABLE_SECTIONS` no longer drifts from the schema (test asserts set equality or derives it)."
  - → Präzisierung: **[§6.3.3 (AC-07)](#ac-07)** — in #1186 handgepflegt, Ableitung als
    Follow-up nach #1141.
- [ ] **AC-1186-08** — „`consistency-check` reports the new check id; `sync.py --validate` stays green on a clean repo."
- [ ] **AC-1186-09** — „`legacy[]` paths never receive new writes; existing files there are reported once, not deleted."
  - → Präzisierung: **[§6.3.4 (AC-09)](#ac-09)** — Artefakt-Inhalt, Marker-Ausnahme,
    deterministische Baseline.
- [ ] **AC-1186-10** — „All 9 `se-*` classes are individually settable and resolvable: a test pins `se-validation: { path: external-evidence }` while `se-requirements: { path: SE }` and asserts both target paths per cell."
- [ ] **AC-1186-11** — „`se-requirements: off` with an enabled cascade is a hard sync error; `se-decomposition: off` is accepted."
- [ ] **AC-1186-12** — „The matrix resolves to exactly 14 non-SE classes (12 persistent + 2 ephemeral) plus the 9 SE classes; no class name from `legacy[]` is still written."
- [ ] **AC-1186-13** — „Merged classes carry `kind`: a file in `docs/analysis` with `kind: estimate` passes validation, a fresh write to `docs/estimates` is reported as a legacy violation."
  - → Präzisierung: **[§6.3.5 (AC-13)](#ac-13)** — `kind` ist ein geschlossenes Enum
    (Klasse: Menge, Artefakt: Skalar).
- [ ] **AC-1186-14** — „`sync.py --status-artifacts --json` returns `path`, `mode`, `source` and `exists` per class; the manager role references the command."
- [ ] **AC-1186-15** — „Precedence is proven by test at all four levels (project > preset > schema default > code fallback) and the resolved `source` is reported."
- [ ] **AC-1186-16** — „A `rules-preset: lazy` project still has `CLAUDE.md ∩ .claude/rules = 0` after the change (no new always-on rule)."

### 6.3 AC-Präzisierungen (Review 2026-11-09, Revision 2)

Der Issue-Wortlaut in §6.2 bleibt unverändert; die vollständigen Präzisierungstexte stehen
hier und sind von den ACs aus verlinkt (Revision 2: aus §6.2 hierher verschoben, damit die
Checkboxen wörtlich bleiben).

<a id="ac-03"></a>
#### 6.3.1 AC-03 — Schreibposition statt „jedes Vorkommen"

„literal managed path" gilt für **aktive Klassenpfade in Schreibposition** (§4.6).
Lese-/Scan-Positionen sind über den Ratchet-Marker `<!-- artifact-read-ok -->` zulässig und
auf **zwei** Zeilen begrenzt (`knowledge-migrator.md:39,50`). Ein `grep` über alle Vorkommen
ist deshalb **kein** gültiges Kriterium; das Gate ist
`grep -rnE "docs/(specs|plans|spikes|concepts|reviews|audits|analysis|reports|adr|traceability|runbooks)" agents/1-generic/*.md | grep -v "artifact-read-ok" | grep -v "_reference-agent" → 0`.

<a id="ac-05"></a>
#### 6.3.2 AC-05 — Determinismus ohne Template-Gate

„deterministically" heißt: **Resolver-Ergebnis, Scaffold, Status-JSON und
Consistency-Check** verhalten sich je Modus deterministisch und sind je Modus getestet
(§3.1-Modustabelle, Plan §7.3). **Kein** template-seitiger `{{#if}}`-Zweig:
`ARTIFACT_<X>_MODE` ist ein Datenwert, und der Renderer aktiviert Conditionals nur bei der
Zeichenkette `"true"` (`variables.py:498-508`, Whitelist `:570-598`) — ein Modus-Gate
bräuchte zwei Boolesche Variablen je Klasse (46 zusätzliche Namen) und ist als Follow-up
ausgelagert (§11). Die Rolle liest den Modus als Text.

<a id="ac-07"></a>
#### 6.3.3 AC-07 — Zwei Lieferungen

Geteilt in zwei Lieferungen. **In #1186:** `artifact-locations` steht in
`PROJECT_WRITABLE_SECTIONS` (handgepflegt, §4.4) — sonst ist AC-1186-06 nicht testbar.
**Follow-up nach #1141:** Ableitung + Mengengleichheits-Test (§9, Plan T22). Grund: die
Ableitung liest das Wurzel-`properties`; vor #1141 ist die Wurzel
`additionalProperties: true`, und ohne die Union-Regel regressiert sie 7 Runtime-Sektionen.

<a id="ac-09"></a>
#### 6.3.4 AC-09 — Artefakt-Inhalt, Marker-Ausnahme, deterministische Baseline

„new writes" = **Artefakt-Inhalt**. Der eine Verzeichnis-Marker
(`.gitkeep`/`.gitignore`/`.keep`) je Verzeichnis ist ausgenommen (§3.5), sonst verletzt die
Spec ihr eigenes Kriterium (`docs/conclusions/.gitkeep`, D-6). Durchsetzung zweistufig:
`artifact-locations.legacy-write` meldet **immer** (ohne Opt-in); der Hook blockt
Legacy-Ziele **sobald aktiviert** (`enabled_by_default: false`, §4.5) und dann
`strict`-unabhängig.

**Deterministische Basis statt mtime (Revision 2, RVW2-1186-02):** Die Baseline ist das
**beim Sync erfasste Inventar** `baseline.legacy_files` in
`.meta-config/artifact-locations.resolved.json` (Stage 14c, §4.5) — **nicht** „mtime >
letzter Sync" (das war nirgends definiert). `legacy-write` = Datei in `legacy[]`, die
**nicht** in der Baseline steht, mit Artefakt-Inhalt, Marker ausgenommen: höchstens **ein**
Finding pro Datei und Lauf, nichts wird gelöscht. „Reported once" ist damit erfüllt: das
Inventar wird beim ersten Sync **einmal** erfasst und in `--status-artifacts` als
`legacy_hits[]` gezeigt; danach meldet der Check nur Deltas. Fehlt die Baseline, meldet der
Check nichts und gibt **eine** Warnzeile auf stderr aus (fail-open, kein neuer Check-Code).
Gate: ein frischer Sync auf sauberem Repo erzeugt **null** `legacy-write`-Funde.

<a id="ac-13"></a>
#### 6.3.5 AC-13 — `kind` als geschlossenes Enum

`kind` ist ein **geschlossenes Enum** (20 Werte, §4.1), keine freie Stringliste:
Klassen-Ebene = Menge (`array` mit `items.enum`), Artefakt-Ebene = genau ein Wert. Ein
unbekannter Wert ist `artifact-locations.kind-invalid`.

**Zusammenfassung der Neuinterpretationen:**

| AC | Neuinterpretation | Grund | Folge im Plan |
|---|---|---|---|
| AC-03 | Literal-Verbot gilt für **Schreibpositionen**; Lese-/Scan-Literale nur per 2-Zeilen-Ratchet-Marker | `knowledge-migrator.md:39,50` sind Eingabe-Pfade; ein Grep über alle Vorkommen ist mit der Dateiliste nicht erfüllbar | T10 (Grep verengt, `documenter.md:81` ergänzt), T14 (Ratchet-Test) |
| AC-05 | deterministisch über Resolver/Scaffold/Consistency/Status; **kein** Template-Gate | `_MODE` ist ein String; `{{#if}}` aktiviert nur `"true"` (`variables.py:498-508`) | T4/T14/T21 + Testmatrix §7.3; Follow-up #1198–#1200 |
| AC-07 | Sektion in #1186 handgepflegt; Ableitung als Follow-up nach #1141 | Ableitung vor #1141 liest eine unvalidierte Wurzel und regressiert 7 Runtime-Sektionen | T17 (hand-add), T22 (Follow-up) |
| AC-09 | „new writes" = Inhalt; Marker ausgenommen; Baseline = `baseline.legacy_files` aus Stage 14c, kein mtime; Meldung immer, Hook-Block bei Aktivierung | `docs/conclusions/.gitkeep` liegt in `legacy[]`; „nach dem letzten Sync" hatte keine deterministische Basis (RVW2-1186-02) | T8 (Marker-Konstante), T14 (Baseline-Fälle), T15 (Baseline schreiben), T16 |
| AC-13 | `kind` = geschlossenes Enum (Klasse: Menge, Artefakt: Skalar) | AC-13 validiert ein Dokument, nicht eine Menge | T1 (`artifactKind`-Enum), T5 (`kind-invalid`) |
| AC-15 | **Vier** Wertequellen (Projekt > Preset > Schema-Default > Code-Fallback) plus Source-Attributionen `project-preset:<name>`, `project-alias:<key>` (D1) und Zustand `disabled`; weder Preset-Wahl noch Alt-Key-Lesen sind eine eigene Stufe (K3) | §3.3 listete fünf Stufen, davon zwei identische (dieselbe Datei, dasselbe `source`-Literal); AC-15 verlangt wörtlich vier | T4, §7.5 (4 Quellen + `disabled` + 2 Attributionsfamilien) |

## 7. Risiken & offene Fragen

### 7.1 Risiken

| # | Risiko | Gegenmaßnahme |
|---|---|---|
| R1 | **Migration bestehender Ablagen.** Consumer-Projekte haben `docs/superpowers/*`, `docs/plans/audit-*.md`, `docs/conclusions/`; ein Default-Wechsel lässt Altdateien „unerreichbar" wirken | `legacy[]` + `enabled: false` als **Escape-Hatch** für Bestandsprojekte (Default ist `true`, weil AC-1186-04 das Verzeichnis-Set verlangt); keine Datei wird bewegt/gelöscht; Release-Note nennt den Wechsel explizit; `--status-artifacts` zeigt `legacy_hits[]` |
| R2 | **`legacy[]`-Schreibschutz ist nur konventionell.** Dateien in Altablagen können weiter beschrieben werden, solange der Hook nicht aktiviert ist | Zweistufig: Consistency-Warnung **immer** (T14), Hook-Block sobald aktiviert (T16); Test je `legacy[]`-Muster (AC-1186-09) plus Null-Fund-Test auf sauberem Repo (T14, Baseline-basiert). Fehlt die Baseline, ist der Check fail-open (eine stderr-Warnzeile) |
| R3 | **Harter Fehler `se-requirements: off`** kann bestehende Projekte beim Sync-Abbruch treffen (Kaskade aktiv + falsch gesetzt) | Fehlermeldung nennt Key und Alternative (`se-decomposition` ist erlaubt); Pre-Migration: einmalige Warnung mit `--status-artifacts`, Abbruch erst ab `enabled: true` |
| R4 | **Hook löst Fehlalarme** (Menschen schreiben Doku, generierte Dateien) | `strict: false` Default, nur Bäume blocken, die die Matrix selbst deklariert; fail-open bei fehlender Datendatei (§4.5) |
| R5 | **`mode: off` löscht den Audit-Trail** | Elternklassen-Fallback explizit (`fallback-parent`), Config-Fehler ohne Eltern (§4.1) |
| R6 | **Whitelist-Ableitung erzeugt Regression**, wenn sieben schema-lose Runtime-Sektionen wegfallen | Union-Regel + Mengengleichheits-Test — **erst im Follow-up nach #1141** (§4.4, Plan T22); in #1186 nur der handgepflegte Eintrag |
| R7 | **Doppelmeldungen** mit `temp_literals` und #1180-Pointer-Check | disjunkte Muster, dokumentierte Abgrenzung (§4.6) |
| R8 | **Drei Wellen-Issues editieren dieselben Dateien** (Schema, `admin-server.py`, `admin-ui.html`, `placeholders.py`, Stage 14) | Serialisierungstabelle §9; kanonische Reihenfolge **#1187 → #1186 → #1188 → #1181, danach #1141**; die Whitelist-Ableitung läuft als Follow-up **nach** #1141 |
| R17 | **`_MODE` als Template-Gate missverstanden.** Ein `{{#if ARTIFACT_<X>_MODE}}` würde nie entfernt (`variables.py:498-508`) und in jeden Agenten lecken | AC-05 präzisiert (§6.3): Modus ist Datenwert; Gate als Follow-up mit zwei Booleschen Variablen je Klasse |
| R9 | **Eine einzelne große `admin-ui.html`** nimmt drei neue Panes auf | Panes klein halten (Resolver-Vorschau erst serverseitig, `--status-artifacts --json` als Datenquelle); Konfliktfläche in §9 markiert |
| R10 | **SE-Default-Widerspruch** (`SE` vs. `docs/se`) produziert zwei „richtige" Pfade | **D4 (DECIDED 2026-11-09):** ein Default `SE` (§3.2), keine Migration; Regel-Text verweist auf `{{ARTIFACT_SE_ROOT}}`, `docs/se/**` ist `legacy[]` — damit gibt es keinen zweiten „richtigen" Pfad mehr |
| R21 | **Scratch-Alias-Migration bleibt liegen** — Bestandsprojekte setzen nur `tmp-sink.path`; ohne Migration lebt der Alias dauerhaft und die Deprecation-Warnung wird ignoriert | Ein-Quellen-Modell (D1): Alias wird gelesen (kein Bruch), Gleichheitszwang verhindert stille Doppelsenke, `sync.py --migrate-artifact-aliases [--write]` (Plan T23) schreibt die Matrix und bleibt idempotent; Warnung nennt den Ziel-Key |
| R22 | **Naming-Token driften** — Rolle schreibt `<YYYY-MM-DD>`, Config erwartet `{date}`; oder ein Preset nutzt `{level}` in `audits` | Geschlossene Token-Liste (§3.2.1) + Schema-`pattern` + semantischer Code `naming-invalid` (D3); Anzeigeform ist ausdrücklich **kein** Config-Wert; Tests in T1/T2/T4/T5 |
| R23 | **Containment-Hook und Matrix laufen auseinander**, wenn der Hook weiter den Roh-Key liest (zwei Schreibziele, ein davon unsichtbar) | Hook liest die aufgelöste Datendatei mit dokumentierter Fallback-Kette (§3.6); `tmp-sink.enabled` bleibt Schalter; lexikalische Parität unverändert (Plan T24) |

### 7.2 Offene Fragen

| # | Frage | Warum nicht entscheidbar hier | Vorschlag/Empfehlung |
|---|---|---|---|
| **OQ-1** | Ist `vv` (systemweite V&V-Strategie) eine eigene Klasse, eine `kind`-Variante von `reports`, oder eine 24. Zeile? | Issue nennt `vv` im YAML-Beispiel **und** verlangt in AC-1186-12 „genau 14 + 9"; beides zusammen ist arithmetisch unvereinbar | **entschieden (D-7):** `reports.kind: vv`; `reports.path` bleibt `docs/reports`; SE-Pfade über abgeleitete Projektions-Variablen (`ARTIFACT_SE_REPORTS_DIR`), `SE/VV/**` in `legacy[]`; kein `se-path`-Feld (§5 Nr. 10) |
| **OQ-2** | AC-1186-04 verlangt `docs/conclusions` in den Defaults, AC-1186-12 zählt `conclusions` in `analysis` auf | interner Widerspruch im Issue | **entschieden (D-6):** `docs/conclusions` als Legacy-Zielverzeichnis scaffolden, nicht als Klasse; das `.gitkeep` ist über die Scaffold-Ausnahme (§3.5) von `legacy-write` ausgenommen |
| **OQ-3** | ADR-Naming: Issue `ADR-<NNN>-<slug>.md` (Bindestrich) vs. Regel `ADR-NNN_kurztitel.md` (Unterstrich, `se-cascade-adr-standard.md:10`) | beide sind „bestehend", das Repo selbst nutzt `0001-pyyaml-runtime-ausnahme.md` | **DECIDED 2026-11-09 (D3):** Naming ist pro Klasse konfigurierbar (Token-Kanon §3.2.1). Projekt-Default `ADR-{nnn}_{slug}.md` (regelkonform); `legacy[]` akzeptiert zusätzlich `docs/adr/[0-9][0-9][0-9][0-9]-*.md` und `docs/adr/ADR-[0-9][0-9][0-9]-*.md`; unbekannte Tokens sind `naming-invalid` |
| **OQ-4** | SE-Wurzel-Default: `SE` (Code, `config.py:2273`) oder `docs/se` (Regel-Text, `taxonomy:10`)? | Code gewinnt faktisch, Doku widerspricht | **DECIDED 2026-11-09 (D4):** Default bleibt `SE`, **keine** Migration; der Regeltext verweist auf `{{ARTIFACT_SE_ROOT}}` statt auf ein Literal; `docs/se/**` wird `legacy[]`-Muster (Plan T20) |
| **OQ-5** | Wie streng ist `scratch`↔`tmp-sink.path` zu koppeln: Alias, Vorrang-Regel oder Verbot der Doppelkonfiguration? | `repo_containment` ist bereits validiert (`config.py:888-937`), `artifact-locations` wäre zweite Quelle | **DECIDED 2026-11-09 (D1):** **eine** Quelle — `classes.scratch.path`. `tmp-sink.path` ist Migrations-Alias (nur gelesen, solange die Klasse fehlt), beide gesetzt ⇒ Gleichheit Pflicht, sonst harter Fehler `scratch-sink-divergence`; Deprecation-Warnung mit Migrationshinweis; `TMP_SINK_PATH` wird aus der Matrix gespeist; Containment-Hook liest den aufgelösten Wert. Die frühere „Vorrang + ERROR"-Formulierung ist ersetzt (§3.6) |
| **OQ-6** | Gehören `docs/superpowers/*`, `docs/issues/`, `docs/testing/`, `docs/providers/`, `docs/api/`, `docs/howto/`, `docs/guides/`, `docs/se-cascade/` in `legacy[]` oder bleiben sie „unmanaged"? **Zusatz:** Wo lebt `docs/issue-labels.md` aus #1188? | Issue listet nur 7 `legacy[]`-Einträge; das Repo hat 8 weitere `docs/`-Unterbäume ohne Klasse | **entschieden (D-8):** die 7 übrigen Unterbäume werden **`unmanaged[]`** (§3.2) — deklariert, aber weder gesperrt noch gewarnt; `docs/superpowers/*` + `docs/conclusions` bleiben `legacy[]`. **`docs/issue-labels.md` ist ein generiertes Mensch-Dok und gehört in das `project-docs`-Datei-Set** (`files.issue-labels`, §3.2); damit ist es für den Managed-Tree-Hook erlaubt und #1188 braucht keine zweite Schema-Änderung (Reihenfolge #1186 → #1188). `.meta-config/issue-labels-state.json` (Zustandsdatei aus #1188) ist ebenfalls `unmanaged` (RVW2-X-02) |
| **OQ-7** | Datei-Ownership `scripts/lib/standalone.py`: Zielmatrix RVW2-X-01 nennt **nur #1187**, #1186-T6 braucht dort aber die 54 Framework-Defaults | Ohne den Block rendert jede Standalone-Persona der 26 umgestellten Templates `[ARTIFACT_* — not available outside a full agent-meta install]` — ein sichtbarer Regress; #1187 läuft zuerst und kann das Modul noch nicht importieren | **DECIDED 2026-11-09 (D2): die D-9-Ausnahme bleibt.** #1186 behält den additiven Standalone-Fallback in `scripts/lib/standalone.py`; #1187 bleibt Datei-Federführer; die Reihenfolge #1187 → #1186 schließt einen Parallel-Edit aus. Kein Follow-up nötig, kein Reviewer-Vorbehalt mehr |

## 8. Backlog-Bugs & Findings

### 8.1 Bestehende Issues (Zuordnung zu dieser Welle)

| Nr. | Titel | Einordnung | Begründung |
|---|---|---|---|
| **#1150** | improvement: Framework lacks a defined output-location structure for plans, specs, audits, reviews and scratch files | **Vorgänger / teilweise ersetzt** — nach #1186 auf `.tmp`-Lifecycle verengen | #1150 beschreibt das Problem; #1186 liefert den Mechanismus und übernimmt die Matrix als Default-Werte. **Nicht** ersetzt wird #1150-AC-4 (Promotion-/Cleanup-Regel für `.tmp/`) — das ist in #1186 explizit Nicht-Ziel (§5 Nr. 2). Empfehlung: #1150 nach Merge auf Punkt 4 reduzieren, nicht schließen. |
| **#1189** | bug(P1): admin-server start reports success but the detached child dies on tmp-sink env pin vs. system-temp-exception check | **Blocker für Teil 3 dieser Spec** — vorziehen | Ohne funktionierenden `admin-server start` ist der Admin-UI-Teil von #1186 (AC-1186-06/07) nicht testbar. Zusätzlich berührt #1189 `scripts/lib/config.py` (Validierungsblock `:888-937`) — dieselbe Datei wie der Resolver. Reihenfolge: #1189 zuerst. |
| **#1141** | bug: project config schema silently accepts unknown top-level keys | **Nachfolger in der Reihenfolge, nicht Voraussetzung** | #1186 verlangt `additionalProperties: false` **pro Sektion** (Sektion ist self-contained) und deklariert `se_output` in T3, damit #1141 es nicht bricht. Die Wurzel-Regel (`schema.json:2851-2854`, heute `additionalProperties: true`) und die daraus abgeleitete Whitelist laufen **nach** #1186 (kanonische Reihenfolge §9); die Aussage „#1141 vor oder im selben PR" ist **zurückgezogen**. |
| **#1180** | bug: rules reference `docs/concepts/*.md` that sync never delivers to consumer repos | **direkte Wechselwirkung** — gleiche Fehlerklasse, anderer Kanal | #1186-H-3 verlangt, dass die Lazy-Pointer-Tabelle generiert wird; #1180 verlangt, dass **keine** Regel einen consumer-relativen Pfad emittiert, den der Sync nicht erzeugt. Beide brauchen denselben generierten Index; sonst erzeugt #1186 neue tote Pointer. Serialisieren: #1180 (Index-Mechanik) vor #1186-H-3. |
| **#1195** | improvement(sync): bound `*.sync-backup-*` retention globally, not only per source | **orthogonal, aber Zähl-Nebenbedingung** | `--status-artifacts` zählt Dateien pro Klasse; `*.sync-backup-*`-Geschwister (523 Dateien) dürfen `file_count`/`newest`/`legacy_hits` nicht verfälschen → Ausschlussmuster im Resolver nötig. Kein Reihenfolge-Zwang. |
| **#1151** | bug(hooks): NotebookEdit/MultiEdit/PowerShell bypass containment and strict-mode guards; allowlist drift | **bereits weitgehend behoben — verifizieren und schließen** | `hooks/1-generic/repo-containment-impl.sh:3` (v1.6.0) und `orchestrator-guard-impl.sh:3` (v1.11.0) nennen #1151 mit F6-01/03/04/05/06/07/08/12; `hook_common.sh:5` (v1.9.0) mit F6-02/F6-03/F6-07. Der neue Hook (§4.5) darf die dort etablierten Muster (`hook_json_get`, `hook_known_tool_name`) nur nutzen, nicht duplizieren. |

### 8.2 Neue Findings ohne Issue

| # | Finding (Beleg) | Relevanz für #1186 | Titelvorschlag | Labels | Body-Skizze |
|---|---|---|---|---|---|
| **F-1** | SE-Templates nutzen `{SE_BASE_DIR}` mit **einfacher** Klammer (16 Vorkommen in 12 Dateien, z. B. `se-requirements.md:184`, `se-architect.md:114`, `se-validator.md:177`), die `sync.py` nie substituiert; nur 4 Vorkommen nutzen `{{SE_BASE_DIR}}` | **hoch** — die neuen `{{ARTIFACT_SE_*_DIR}}` müssen doppelte Klammern verwenden; sonst entsteht derselbe stille Fehlschlag in 9 Klassen | `bug(agents): SE templates use {SE_BASE_DIR} with single braces — sync never substitutes it` | `bug`, `agents`, `consistency`, `P2` | Symptom: gerenderte Agenten enthalten den literal Token; Erwartung: eine einzige Platzhalterform; Fix: 16 Stellen auf `{{...}}` bzw. `{{ARTIFACT_SE_ROOT}}`; Test: `grep`-Golden „kein `{SE_` in `agents/1-generic`" |
| **F-2** | Eine reine Schema-Ableitung von `PROJECT_WRITABLE_SECTIONS` entfernt **7** Runtime-Sektionen (`agent-prompts`, `steps-overrides`, `rules`, `environments`, `skills-registry`, `backup`, `submodule-protection`), die kein Schema-Pendant haben (`admin-server.py:234-259` vs. `schema.json:7-2849`) | **hoch** — AC-1186-07**b** (Ableitung, Follow-up nach #1141) würde ohne Union 7 Sektionen regressieren | `bug(admin): deriving PROJECT_WRITABLE_SECTIONS from the schema drops 7 runtime-only sections` | `bug`, `config`, `admin-ui`, `P2` | Symptom: nach Ableitung sind `rules`/`backup`/… nicht mehr schreibbar (HTTP 400); Erwartung: Union mit `_RUNTIME_ONLY_SECTIONS`; Test: Mengengleichheit (Plan T22) |
| **F-3** | Acht `docs/`-Unterbäume haben keine Klasse (`superpowers`, `issues`, `testing`, `providers`, `api`, `howto`, `guides`, `se-cascade`) und `docs/plans/audit-*.md` zeigt Audits in der Plans-Klasse (4 Dateien: 2 aktiv, 2 archiviert) | **mittel** — ohne Entscheidung entstehen beim Rollout Dauerwarnungen oder ein unvollständiges `legacy[]` | `chore(docs): classify the 8 unmanaged docs/ subtrees and the audit-*.md files in docs/plans` | `chore`, `docs`, `config` | Kontext: #1186 führt `legacy[]` + `artifact-locations.missing-dir` ein; Aufgabe: je Unterbaum „Klasse / legacy / unmanaged" entscheiden, `docs/plans/audit-*.md` → `audits` migrieren oder `legacy[]` |

**Keine weiteren Findings.** Insbesondere **kein** Finding für `/tmp/opencode`: der Zustand ist
bereits behoben und durch `tests/test_template_report_paths.py:61` geschützt (STALE-Angabe
des Issues, §2.6).

## 9. Cross-Issue-Konfliktflächen

**Kanonische Ausführungsreihenfolge (verbindlich, Review 2026-11-09):**
`#1187 → #1186 → #1188 → #1181`, danach `#1141`. Die **Whitelist-Ableitung aus dem Schema
läuft zuletzt** als eigenes Follow-up nach #1141 (Plan T22). Jede Zeile unten ist damit
eindeutig serialisiert.

| Datei | Betroffene Issues | Konfliktnatur | Serialisierungsbedarf |
|---|---|---|---|
| `config/project-config.schema.json` | #1186, #1187, #1188, #1141 | vier neue Top-Level-Sektionen + Wurzel-`additionalProperties` (#1141) + `$defs`-Erweiterungen; dieselben Einfügepunkte (`properties`-Block, `:7-2849`) | **streng**: #1187 → #1186 → #1188; #1141 danach (Wurzel-Regel), Ableitung als letztes |
| `scripts/lib/config.py` | #1186, #1189, #1187 | #1186 Resolver/Variablen (`:2044`, `:2269`, `:2737-2771`), #1189 Validierungsblock (`:888-937`), #1187 Kontext-Variablen | #1189 zuerst (Blocker für M5), dann #1187 → #1186 |
| `scripts/lib/sync_pipeline.py` — **Stage 14** (`:1893-1924`) | **#1186, #1181** | **beide bauen dieselbe Stage um**: #1181-T9 fasst `_sync_stage_auto_commit_allowlist` an, #1186 hängt die neue Stage 14c (`artifact-locations.resolved.json`) direkt danach in `cli_commands._handle_sync` (`:1613-1616`) | #1186 vor #1181 (Stage-Reihenfolge 13 → 14 → 14b → **14c** → 15); ein Parallel-Edit ist ausgeschlossen |
| `scripts/lib/variables.py` | #1187 | **Konfliktfläche ohne Änderung in #1186** (Zielmatrix RVW2-X-01: nur #1187): `strip_inactive_conditional_blocks`-Whitelist (`:570-598`) ist der Ort, an dem ein späteres `ARTIFACT_*_MODE`-Gate und die übrigen Wellen-Conditionals kollidieren | kein Edit in #1186; nur als Hotspot markiert (Follow-up AC-05) |
| `scripts/lib/standalone.py` | #1187 (Federführung), #1186 (T6, additiver Fallback-Block) | `_standalone_variables` (`:295-336`) muss die 54 `ARTIFACT_*`-Werte mit Framework-Defaults liefern, sonst rendert die Standalone-Persona „not available"-Notizen statt Pfaden | **D2 (DECIDED 2026-11-09):** die Abweichung von RVW2-X-01 **bleibt** — #1186 braucht den Block, sonst regressieren 26 umgestellte Templates sichtbar; #1187 bleibt Datei-Federführer, die Reihenfolge #1187 → #1186 schließt den Parallel-Edit aus (§7.2 OQ-7) |
| `scripts/admin-server.py` | #1186, #1187, #1188, #1189 | alle vier erweitern `PROJECT_WRITABLE_SECTIONS` (`:234-259`) bzw. Guard-Block (`:5295-5308`); #1189 zusätzlich `_start`/`_tmp_sink_env` (`:311`, `:650-671`) | streng sequenziell; #1189 unabhängig zuerst, danach #1187 → #1186 → #1188 |
| `docs/ui/admin-ui.html` (eine Datei) | #1186, #1187, #1188 | drei neue Panes in derselben Datei; jede Änderung ist ein Konflikt-Hotspot | **streng**: nacheinander, kein Parallel-Edit (Reihenfolge wie oben) |
| `docs/issue-labels.md` | #1188 (erzeugt), #1186 (klassifiziert) | #1186 muss die Datei **vor** #1188 in `project-docs.files.issue-labels` deklarieren, sonst blockt der Managed-Tree-Hook die Erzeugung | #1186 vor #1188 |
| `.meta-config/issue-labels-state.json` | #1188 (erzeugt), #1186 (klassifiziert) | #1186 kennt nur `project-docs` und den `.meta-viz`-`state`; die Zustandsdatei wäre sonst unklassifiziert | **RVW2-X-02 / D-8 / K1:** als `unmanaged[]` deklariert (§3.1/§3.2), nicht als Klasse — kein Block, keine Warnung, keine Zählung in AC-1186-12. Die Kategorie `project-state` ist gestrichen |
| `scripts/lib/consistency/placeholders.py` | #1186, #1187, #1188 | drei Erweiterungen derselben Allow-List (`:89-100`); #1186 registriert 54 Namen | sequenziell (Reihenfolge wie oben), nicht parallel |
| `scripts/consistency-check.py` | #1186, #1188, #1180 | neue Check-Registrierungen an denselben Import-/Aufrufstellen (`:42-68`, `:238-249`) | sequenziell |
| `rules/1-generic/use-lazy-rules.md` | #1186 (H-3), #1180 | handgepflegte Pointer-Tabelle driftet; #1186 will Generierung, #1180 will Erreichbarkeit | #1180-Mechanik zuerst, dann generierte Tabelle |
| `agents/1-generic/*.md` (18+ Rollen) | #1186, #1187, #1188 | #1186 rewritet Pfadstellen, #1187 ändert `{{PROJECT_CONTEXT}}` in 70 Templates, #1188 ändert `feedback.md`/`meta-feedback.md`/`bug-feature-analyzer.md` — **Überschneidung genau bei den Feedback-/Triage-Rollen**, die #1186 ebenfalls auf `analysis` umstellt | #1187 → #1186 → #1188 (Reihenfolge macht die Feedback-Rollen konfliktfrei) |
| `config/routing/reviewers.yaml` | #1186 | `notes` verweist heute auf tmp-Sink statt Matrix (`:23-29`) | kein Konflikt, gehört zu #1186 |
| `hooks/1-generic/*` | #1186, #1151 | #1186 legt `artifact-path-guard.sh` an (**neu**) und stellt `repo-containment*.sh` auf die aufgelöste Scratch-Quelle um (D1, Plan T24); #1151 hat die gemeinsamen Helfer (`hook_common.sh`) gerade nachgezogen | #1151 verifizieren/schließen, dann #1186-Hook auf `hook_common.sh` v1.9.0 aufsetzen; `repo-containment*.sh` hat in #1186 **einen** Owner (T24), die lexikalischen Regeln bleiben unverändert |
| `scripts/lib/spec_plan_scaffold.py` → `artifact_scaffold.py` | #1186 | Umbenennung/Verallgemeinerung; Importe in `sync_pipeline.py:152` und `knowledge.py:12` | nur #1186 |
| `tests/scenarios/registry.md` + `tests/scenarios/configs/` | #1186, #1181, #1187 | **Szenario-IDs sind knapp**: `94` = #1181, `95–98` = #1187; #1186 belegt **`99-artifact-locations-matrix`** (+ `asserts/99-…sh`) | ID-Vergabe in dieser Reihenfolge; keine Nachverdichtung |
| `templates/configs/project.yaml.example`, `howto/configs/project.yaml.example` | #1187, #1186, #1188, #1181 | alle vier Wellen erweitern dieselben vollständigen Beispiele; beide Dateien müssen synchron bleiben (`docs/guides/project.yaml.example` ist ein Orchestrator-Teilbeispiel und **nicht** betroffen) | je PR nur eigene Keys, keine Umsortierung; #1186 hält **beide** Dateien im selben Task (T20) synchron |
| `.meta-config/project.yaml` (jedes Consumer-Projekt) | alle | jede Welle fügt Keys hinzu; Key-Reihenfolge und Kommentare kollidieren | je PR nur eigene Keys, keine Umsortierung |
| `agents/1-generic/agent-meta-manager.md` | #1186 (§1-Status), #1187 (Confirmation-Table) | dieselbe Rolle, unterschiedliche Abschnitte | sequenziell, #1186 vor #1187 wäre falsch — es gilt die kanonische Reihenfolge (#1187 zuerst, disjunkte Abschnitte) |

**Zielmatrix-Abgleich (RVW2-X-01, Revision 2):** Die obige Tabelle ist die verbindliche
Datei→Issue-Zuordnung. **Nicht in #1186** (bewusst nicht gelistet, weil ohne Edit):
`scripts/lib/agent_sync.py` (#1187, #1188, #1181), `scripts/lib/variables.py` (#1187).
`scripts/lib/sync_pipeline.py` bleibt bei **#1186, #1181**. `tests/scenarios/registry.md` bei
**#1186, #1181, #1187**. Beide `project.yaml.example` bei **#1187, #1186, #1188, #1181**.
Einzige begründete Abweichung: `scripts/lib/standalone.py` (D-9, §7.2 OQ-7).

## 10. Traceability: AC → Spec-Abschnitt

| AC | Anforderung (Kurz) | Spec-Abschnitt | Vertrags-/Umsetzungsanker |
|---|---|---|---|
| AC-1186-01 | Schema-Sektion mit `additionalProperties: false` | §3.1, §4.1 | `config/project-config.schema.json` (`$defs`: `artifactClass`, `artifactSeClass`, `artifactFileSet`, …) |
| AC-1186-02 | Resolver + `ARTIFACT_*` + Scaffolding, dry-run-safe | §3.4, §3.5 | `config.py` (Resolver), `artifact_scaffold.py`, `sync_pipeline.py:152` |
| AC-1186-03 | Kein Literalpfad **in Schreibposition**; `/tmp/opencode` leer; Lese-Literale = 2-Zeilen-Ratchet | §2.3, §4.6, §6.3 | `consistency/artifact_locations.py` (`literal-path`), Golden-Test + Ratchet-Test |
| AC-1186-04 | Defaults erzeugen 11 `docs/`-Verzeichnisse, `reviews`/`audits` nach frischem Sync | §3.2, D-6 | Scaffold-Liste, `legacy[]` für `docs/conclusions` (Marker-Ausnahme §3.5) |
| AC-1186-05 | `off`/`inline` deterministisch über Resolver/Scaffold/Consistency/Status; Test je Modus | §3.1 (Modus-Tabelle), §3.4, §6.3 | Resolver-Tests `mode × git × legacy`; **kein** Template-Gate (Follow-up) |
| AC-1186-06 | Admin-UI lesen/editieren/speichern; `../x` → 400 | §4.4 | `_write_project_section` + `_guard_artifact_locations_write` |
| AC-1186-07 | `artifact-locations` schreibbar (handgepflegt); Ableitung als Follow-up nach #1141 | §2.5, §4.4, §6.3 | T17 (hand-add), T22 (Union + Mengengleichheit) |
| AC-1186-08 | Neuer Check meldet; `--validate` grün | §4.6 | Registrierung `consistency-check.py:42-68/238-249` |
| AC-1186-09 | `legacy[]` erhält keine neuen **Artefakt-Inhalte**; Marker ausgenommen; Baseline-basiert, einmal gemeldet | §3.3 (Regel 4), §3.5, §3.6, §4.5 (`baseline`), §4.6, §6.3.4 | `legacy-write` (warning) gegen `baseline.legacy_files`, Hook-Regel (opt-in), Null-Fund-Test |
| AC-1186-10 | 9 SE-Klassen einzeln setzbar (Test `se-validation` vs. `se-requirements`) | §2.4, §3.1, §3.2 | `artifactSeClass` (`subdir`), Zell-Pfad-Resolver |
| AC-1186-11 | `se-requirements: off` harter Fehler, `se-decomposition: off` erlaubt | §4.1 (`artifact-locations.se-required-off`) | `_fail`-Muster `config.py:808` |
| AC-1186-12 | 14 + 9 Klassen, keine `legacy[]`-Klasse beschrieben; `unmanaged[]` ist keine Klasse | §2.4, D-7 (OQ-1), D-8 (§3.2) | Klassen-Registry im Resolver (SE-Projektionen und `unmanaged` sind keine Klassen) |
| AC-1186-13 | `kind` in zusammengelegten Klassen (Enum), Legacy-Write gemeldet | §3.1 (`kind`-Kardinalität), §3.2, §4.1, §4.6 | `$defs/artifactKind`, `kind-invalid`; `docs/estimates` in `legacy[]` |
| AC-1186-14 | `--status-artifacts --json` mit `path/mode/source/exists` plus `unmanaged`-Liste; Manager nennt es | §4.3, §3.6 | `sync.py`-Flag, `agent-meta-manager.md:42-49` |
| AC-1186-15 | Präzedenz auf 4 Stufen getestet, `source` gemeldet | §3.3, §6.3 | `source`-Enum `project|preset:<n>|schema-default|code-fallback` plus Attribution `project-preset:<n>` und Zustand `disabled` |
| AC-1186-16 | `rules-preset: lazy` bleibt `CLAUDE.md ∩ .claude/rules = 0` | H-1..H-4, §5 Nr. 6 | Lazy-Skill statt always-on-Rule; Kontext-Golden-Test |
| H-1 | Variablen + **ein** Lazy-Skill | §3.4, §4.6, §5 Nr. 6 | `channel: skill` (Muster `rules-presets.yaml:25-34`) |
| H-2 | Ein Render pro Provider | §3.4 | `build_variables()` einmal pro Provider |
| H-3 | Lazy-Pointer-Tabelle generieren | §9 (#1180) | generierter Index statt Handpflege |
| H-4 | Keine neue `PROJECT_CONTEXT`-Duplizierung | §5 Nr. 6, H-4 | keine Änderung an `{{PROJECT_CONTEXT}}` |
| **D1** (OQ-5) | **Eine** Scratch-Quelle; Alias nur Migrationspfad; Divergenz = harter Fehler; Containment-Hook liest aufgelösten Wert | §3.2, §3.4, §3.6, §4.1 (`scratch-sink-divergence`), §4.5, §4.6 | Plan T4/T5/T9/T23/T24; Tests (a)–(d) in T5/T9 |
| **D2** (OQ-7) | D-9-Ausnahme bleibt (Standalone-Fallback in #1186, #1187 Datei-Federführer) | §7.2 (OQ-7), §9 | Plan T6, §2.3-Konfliktfläche |
| **D3** (OQ-3) | Naming pro Klasse konfigurierbar, geschlossene Token-Liste, ADR-Default `ADR-{nnn}_{slug}.md`, zwei Legacy-Formen | §3.1, §3.2, §3.2.1, §4.1 (`artifactNaming`, `naming-invalid`), §4.2, §4.3 | Plan T1/T2/T4/T5/T15 |
| **D4** (OQ-4) | Default `SE`, Regeltext auf `{{ARTIFACT_SE_ROOT}}`, `docs/se/**` in `legacy[]` | §3.2, §3.6, §4.2 | Plan T2/T20 |

## 11. Review-Auflösung (2026-11-09)

Alle Befunde aus dem Review vom 2026-11-09 sind eingearbeitet; damals `DRAFT`, seit 2026-11-09 `APPROVED`.
Drei Punkte sind als **Follow-up** ausgelagert und im Wave-Overview als Issues **#1198,
#1199, #1200** angelegt (Zuordnung der Nummern zu den drei Punkten trägt das Wave-Overview
nach — hier bewusst keine erfundene Titel-Zuordnung).

| Befund-ID | Änderung | Stelle |
|---|---|---|
| **RVW-1186-01** (BLOCKER) | Scaffold-Ausnahme definiert (Marker-Dateien sind keine Artefakte, in Check **und** Hook ausgenommen); AC-1186-09 präzisiert (Inhalt vs. Marker, Meldung immer / Block bei Aktivierung); Null-Fund-Test „frischer Sync ⇒ 0 `legacy-write`"; `docs/conclusions` bleibt in `legacy[]` | §3.5, §3.6 (D-6), §4.5, §4.6, §6.2 (AC-09), §6.3 |
| **RVW-1186-02** (MAJOR) | Vollständige Variablen-Menge exakt berechnet und tabelliert: **54** Namen (13 DIR + 9 SE-DIR + 4 SE-Projektion + `SE_ROOT` + 4 `_FILE` + 23 `_MODE`); `derive_builder_vars ⊆ _BUILTIN_VARS` als Vertrag; Builder-Totalität auf `{}` dokumentiert | §3.4, §4.7 |
| **RVW-1186-03** (MAJOR) | AC-1186-05 auf „Resolver + Scaffold + Consistency + Status deterministisch" verengt; Begründung aus dem Renderer (`variables.py:498-508`, `:570-598`); Template-Gate als Follow-up | §3.4, §6.2 (AC-05), §6.3, §7.1 R17 |
| **RVW-1186-04** (MAJOR) | `fallback-parent` als Schema-Feld (Enum der 23 Klassen) in `artifactClass`, `artifactSeClass`, `artifactFileSet`; `mode-parent-missing` auf das Feld bezogen; zusätzlicher Code `fallback-parent-unknown` | §3.1 (ClassEntry), §4.1 |
| **RVW-1186-05** (MAJOR) | D-7 entschieden: `reports.path` bleibt `docs/reports` (AC-04), SE-Pfade über **abgeleitete** Projektions-Variablen; `SE/VV/**` in `legacy[]`; `reports.se-path` explizit Nicht-Ziel | §3.2, §3.4, §3.6 (D-7), §5 Nr. 10, §7.2 (OQ-1) |
| **RVW-1186-06** (MAJOR) | Lese-/Schreib-Literal getrennt; `literal-path` prüft Schreibpositionen; Ratchet-Marker `<!-- artifact-read-ok -->` (2 Zeilen: `knowledge-migrator.md:39,50`); `documenter.md:81` als Schreib-Literal in den Rewrite aufgenommen; AC-1186-03 präzisiert | §4.6, §6.2 (AC-03), §6.3 |
| **WARN Header** | `Klasse: XL` in den Spec-Kopf aufgenommen | Kopfblock |
| **WARN `kind`** | Vereinheitlicht auf geschlossenes **Enum** (`$defs/artifactKind`, 20 Werte), Klassen-Ebene = Menge, Artefakt-Ebene = Skalar; `kind-invalid` ergänzt | §3.1, §4.1, §6.2 (AC-13), §6.3 |
| **WARN `docs/codebase_overview.md`** | im Plan auf `docs/CODEBASE_OVERVIEW.md` korrigiert (Plan T10) | Plan §T10 |
| **WARN Create/Modify** | Plan kennzeichnet neue Dateien als `Create` (Datei-Zeile je Task) und listet die neuen Szenario-Dateien in §2.1 | Plan §2.1/§2.2 |
| **Querschnitt: Reihenfolge** | Kanonisch `#1187 → #1186 → #1188 → #1181`, danach `#1141`; Whitelist-Ableitung zuletzt (Follow-up T22); „#1141 vor oder im selben PR" zurückgezogen | §8.1, §9, §4.4, §6.2 (AC-07) |
| **Querschnitt: Konfliktmatrix** | #1181 in die Stage-14-Zeile; neue Zeilen `scripts/lib/variables.py`, `scripts/lib/standalone.py`, `tests/scenarios/registry.md`, beide vollständigen `project.yaml.example`, `docs/issue-labels.md` | §9 |
| **Querschnitt: Szenario-IDs** | `94` = #1181, `95–98` = #1187; #1186 belegt `99-artifact-locations-matrix` | §9 |
| **Querschnitt: `docs/issue-labels.md`** | in `project-docs.files` aufgenommen (`ARTIFACT_ISSUE_LABELS_FILE`), OQ-6 erweitert, damit der Managed-Tree-Hook die #1188-Datei nicht blockt | §3.1, §3.2, §4.1, §4.3, §7.2 (OQ-6), §9 |

### 11.1 Runde 2 — Revision 2 (2026-11-09)

Formale Blocker und fachliche Befunde der zweiten Korrekturrunde. Damals `DRAFT`, seit 2026-11-09 `APPROVED`.

| Befund-ID | Änderung | Stelle |
|---|---|---|
| **Formal `Revision`** | Pflichtfeld im Kopf ergänzt (`Revision: 2 (Review-Auflösung 2026-11-09)`) | Kopfblock |
| **Formal AC-Wortlaut** | Escaped Quotes in AC-1186-03 (`grep -rn "/tmp/opencode"`) und AC-1186-06 (`path: "../x"`) entfernt — die Checkboxen sind jetzt wörtlich | §6.2 |
| **Formal AC-Präzisierungen** | Die „→ Präzisierung"-Unterpunkte sind aus §6.2 nach §6.3 verschoben (eigene Unterabschnitte mit Ankern), die ACs verlinken dorthin | §6.2, §6.3 |
| **RVW2-1186-01** (MAJOR) | Reihenfolge-Defekt: T8 rief `check_artifact_locations` auf, das erst T14 anlegt, und das M2-Gate enthielt `test_artifact_scaffold.py` mit `legacy-write`-Fällen. Fix: Marker-Konstante `MARKER_FILENAMES` in T8, alle `check_artifact_locations`-Fälle in T14; M2-Gate enthält nur scaffold-lokale Assertions | §3.5, §4.6, Plan T8/T14, §4-M2/M4 |
| **RVW2-1186-02** (MAJOR) | AC-09 hatte keine deterministische Basis („mtime > letzter Sync", nirgends definiert). Fix: Baseline = `baseline.legacy_files` aus `.meta-config/artifact-locations.resolved.json` (Stage 14c), **kein** mtime-Vergleich; fail-open bei fehlender Baseline | §4.5, §4.6, §6.3.4, Plan T14/T15 |
| **RVW2-1186-03** (MINOR) | „70/98" ist auf HEAD veraltet (83/98). Als Gate gilt die **relative** Assertion „Anzahl wächst nicht"; die Zahl ist als Zahlen-Notiz dokumentiert | §6.1 (H-4), Plan T13 |
| **RVW2-1186-04** (MINOR) | T20 nannte nur `templates/configs/project.yaml.example`; beide vollständigen Beispiele sind Pflicht | §9, Plan T20 |
| **RVW2-1186-05** (INFO) | „Vier Stufen" → „Fünf Stufen" (die Liste hatte fünf Einträge) — **durch K3 präzisiert:** vier **Wertequellen** plus Source-Attribution (`project-preset`) und Zustand (`disabled`); die zwei identischen Einträge der alten Liste sind zusammengeführt | §3.3 |
| **RVW2-X-02** (MAJOR) | `.meta-config/issue-labels-state.json` (aus #1188) war in #1186 unklassifiziert. Fix: neue `unmanaged[]`-Liste (D-8) — deklariert, aber keine Klasse, kein Scaffold, kein Block/Warn, keine AC-12-Zählung; `docs/issue-labels.md` bleibt `project-docs`. **K1:** die von #1188 vorgeschlagene Kategorie `project-state` ist gestrichen | §3.1, §3.2, §4.1, §4.3, §4.5, §4.6, §7.2 (OQ-6), §9 |

### 11.2 Szenario-Konflikte K1–K8 (2026-11-09)

Auflösung der acht Befunde aus `.tmp/scenario-config-wave/RESULT.md`, konsistent über alle vier
Wave-Specs/-Pläne. Damals `DRAFT`, seit 2026-11-09 `APPROVED`.

| Befund | Änderung | Stelle |
|---|---|---|
| **K1** (BLOCKER) | `.meta-config/issue-labels-state.json` bleibt **`unmanaged`**; die von #1188 geforderte Kategorie `project-state` ist **gestrichen**. `unmanaged[]` ist die Negativ-Deklaration; `classes` bleibt bei **23** (14 + 9), AC-1186-12 unverändert | **§3.1** (`unmanaged`-Absatz), **§3.2** (Default-Liste), §7.2 (OQ-6), §9 (Matrix-Zeile) |
| **K2** | **Nicht betroffen**: #1186 hat keinen Separator-Schlüssel (Artefakt-Pfade, nicht Label-Projektion) | geprüft: §3.1, §4.1 |
| **K3** (MAJOR) | §3.3-Überschrift „Vier Wertequellen (plus Source-Attribution)"; die zwei identischen Preset-Stufen sind zusammengeführt; die Projekt-Preset-Wahl ist **Source-Attribution** `project-preset:<name>`, keine Präzedenzstufe. AC-1186-15 (wörtlich vier Stufen) ist damit erfüllt; die Testmatrix im Plan prüft 4 Quellen + `disabled` + `project-preset`-Attribution | **§3.3** (Tabelle + Absätze + Regeln 2/5), **§6.3** (AC-15-Zeile) |
| **K4** | **Nicht betroffen**: kein `taxonomyAxis` | geprüft: §4.1 |
| **K5** | **Nicht betroffen**: keine Grant-Präzedenztabelle | geprüft: §3.3 |
| **K6** (NIT) | `$defs` bleibt, weil das Ist-Schema `draft-07` deklariert und dennoch `$defs` nutzt; explizite Notiz statt Umbenennung zu `definitions` | **§4.1** (Schema-Notiz) |
| **K7** | **Nicht betroffen**: alle neuen Schlüssel sind kebab-case in der neuen Top-Level-Sektion `artifact-locations` | geprüft: §3.1 |
| **K8** | **Nicht betroffen**: kein bestehender `_KEYS`-Block | geprüft: §4.1 |
| **RVW2-X-01** (MAJOR) | Konfliktmatrix auf die verbindliche Zielmatrix gezogen: `agent_sync.py` (#1187/#1188/#1181), `sync_pipeline.py` (#1186/#1181), `variables.py` (#1187), beide `project.yaml.example` (#1187/#1186/#1188/#1181), `registry.md` (#1186/#1181/#1187), `docs/issue-labels.md` + `.meta-config/issue-labels-state.json` (#1188 erzeugt, #1186 klassifiziert) | §9 |
| **Deviation D-9** | `standalone.py` bleibt in #1186 (T6) — begründete Abweichung von RVW2-X-01, sonst Regress in 26 Standalone-Personas; **D2 (DECIDED 2026-11-09)** bestätigt die Ausnahme, #1187 bleibt Datei-Federführer | §7.2 (OQ-7), §9, Plan §2.2/§13 |

## 12. Entscheidungsprotokoll (2026-11-09)

Vom User entschieden; die Markierung `DECIDED 2026-11-09` steht zusätzlich am jeweiligen
Vertragsabschnitt. Diese vier Entscheidungen sind **Fach-Entscheidungen** und zu
unterscheiden von den internen Design-Entscheidungen `D-6` (conclusions), `D-7` (`vv`),
`D-8` (`unmanaged`) und `D-9` (Standalone-Ausnahme, hier als **D2** bestätigt).

| D-Nr | Frage | Entscheidung | betroffene Stellen |
|---|---|---|---|
| **D1** | OQ-5 — wie streng ist `scratch` an `repo_containment.tmp-sink.path` gekoppelt? | **Eine** Quelle: `artifact-locations.classes.scratch.path`. `repo_containment.tmp-sink.path` ist **Legacy-Alias**, wird nur gelesen, solange `classes.scratch` fehlt; bei Setzung beider Werte muss der Wert **gleich** sein, Divergenz ist ein **Consistency-ERROR**. Deprecation-Warnung mit Migrationshinweis. `TMP_SINK_PATH` bleibt Laufzeit-Variable, wird aber **aus der Matrix** gespeist. Der Containment-Hook liest den **aufgelösten** Matrix-Wert, nicht den Roh-Key. Die frühere „Vorrang + ERROR"-Formulierung ist ersetzt. Migration: `sync.py --migrate-artifact-aliases [--write]`. | §3.2, §3.4, §3.6, §4.1 (`scratch-sink-divergence`), §4.5, §4.6, §5 Nr. 11, §7.1 R21/R23, §7.2 OQ-5; Plan T4, T5, T9, T23, T24 |
| **D2** | OQ-7 — gilt die Datei-Zielmatrix (RVW2-X-01) für `scripts/lib/standalone.py` ausnahmslos? | **Nein, die D-9-Ausnahme bleibt.** #1186 behält den additiven Standalone-Fallback (54 Framework-Defaults); #1187 bleibt Datei-Federführer; die Reihenfolge #1187 → #1186 verhindert Parallel-Edits. Kein Follow-up, kein Reviewer-Vorbehalt. | §7.2 (OQ-7), §9 (`standalone.py`-Zeile), §11.2 (`Deviation D-9`); Plan T6, §2.3 |
| **D3** | OQ-3 — welches ADR-Naming gilt, und ist Naming konfigurierbar? | Naming ist **pro Klasse** konfigurierbar als String-Pattern mit **geschlossener Token-Liste** (`{class}`, `{date}`, `{slug}`, `{kind}`, `{n}`, `{topic}`, `{scope}`, `{nnn}`, `{level}`, `{folder}`). Projekt-Default für ADRs: `ADR-{nnn}_{slug}.md` (regelkonform, `se-cascade-adr-standard.md:10`). `legacy[]` akzeptiert zusätzlich `NNNN-{slug}.md` und `ADR-{nnn}-{slug}.md`. Unbekannte/nicht anwendbare Tokens sind Fehler. | §3.1, §3.2 (ADR-Zeile + Absatz), §3.2.1, §4.1 (`$defs/artifactNaming`, `naming-invalid`), §4.2 (d), §4.3 (`naming` im JSON), §5 Nr. 12, §7.1 R22; Plan T1, T2, T4, T5, T15, T20, T23 |
| **D4** | OQ-4 — `SE` oder `docs/se` als SE-Wurzel-Default? | Default bleibt **`SE`**, keine Migration. Der Regeltext `rules/1-generic/se-cascade-artifact-taxonomy.md` verweist künftig auf `{{ARTIFACT_SE_ROOT}}` statt auf ein Literal. `docs/se/**` wird als `legacy[]`-Muster gelesen (kein Default, kein zweiter „richtiger" Pfad). | §3.2 (SE-Absatz), §3.6, §4.2, §7.1 R10, §7.2 OQ-4; Plan T2, T20 |

**Verbleibende offene Punkte (nicht entschieden, nicht blockierend):**

1. **`ARTIFACT_SE_ADR_DIR`-Leaf-Schreibweise** — §3.4 leitet die SE-Projektion als
   `{ARTIFACT_SE_ROOT}/<leaf>` ab; die Taxonomie (`se-cascade-artifact-taxonomy.md:15,61`)
   führt den Ordner als `ADR/` (Großbuchstaben), die Matrix-Klasse `adr` als `docs/adr`
   (Kleinbuchstaben). Empfehlung für die Umsetzung: Leaf **wörtlich** `<ADR>`/`<reports>`/
   `<reviews>`/`<traceability>` aus der Taxonomie übernehmen und in T4 pinnen; keine
   Entscheidung in diesem Dokument.
2. **Retention für `scratch`** bleibt Deklaration + Report (Nicht-Ziel 2); ein Cleanup ist
   weiterhin #1150 vorbehalten.
3. **Naming-Auflösung zur Laufzeit** (wer erzeugt den Dateinamen: Rolle oder CLI) bleibt
   Rollen-Verantwortung; die Matrix liefert nur Muster + Validierung (§3.2.1 e).
