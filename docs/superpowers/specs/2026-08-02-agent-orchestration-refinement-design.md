# Agent-Orchestrierung: Planner-Rolle, Intent-Tabelle, Cluster-Cleanup, Delegation-Enforcement — Design

**Status:** Entwurf zur Freigabe (Revision 2026-08-04 — konsolidiert Review-Anmerkungen vom 2026-08-03 und ergänzt Delegation-Enforcement)
**Kontext:** Ausgelöst durch die Frage "wie integrieren wir Superpowers-Skills (brainstorming, writing-plans, ...) in agent-meta" — im Brainstorming wurde das verworfen (zu komplex, Provider-Kopplung an Claude widerspricht der Provider-Agnostik-Prämisse von `1-generic/`). Stattdessen: ein neuer, nativer, providerunabhängiger `planner`-Agent, eine Schärfung der Orchestrator-Intent-Tabelle, ein Cleanup-Abschnitt für einen 7-Rollen-Cluster, und (neu in dieser Revision) ein Fix für die stille Delegation-Enforcement-Lücke zwischen Providern.

## Ausgangslage — was existiert bereits

- `ideation.md` → `concept-<topic>.md` (fix im Projekt-Root, kein Knowledge-Engine-Bezug), gefolgt optional von `concept-reviewer` (Generator-Critic-Loop), dann `requirements.md` (REQ-IDs, `docs/REQUIREMENTS.md`).
- `feature.md` orchestriert danach den kompletten Rest (Branch → REQ optional → TDD → Impl → Validate → PR) — **ohne eigenen Planungsschritt**. Der Übergang "Konzept/REQ vorhanden" → "konkrete Umsetzungsschritte" passiert implizit, nirgends als Artefakt.
- Die Intent-Routing-Tabelle in `use-orchestrator.md` ist **generiert**, nicht handgepflegt: `scripts/lib/delegation_table.py::get_intent_routing_table()` liest `workflow_tier` und `routing.{intent_keywords,parallel,orchestrator_only}` aus `config/role-defaults.yaml` pro Rolle. `Tier` wird zusätzlich von `scripts/lib/consistency/crossrefs.py::check_orchestrator_table()` geprüft (jede Rolle mit `tier in (required, recommended)` muss in der Tabelle auftauchen — WARNING sonst). `Parallel` ist **rein informativ**, kein Runtime-Enforcement, keine Hook-Logik dazu.
- Die Knowledge Engine (aktiv in diesem Repo, Domäne `personal`) kennt 5 Concept Types (`knowledge/schema.md`): `Concept`/`Architecture` → `concepts/`, `API Reference` → `entities/`, `Guide` → `topics/` (deckt laut Beschreibung bereits "howto, analysis, audit, or spec" ab), `Session Conclusion` → `sources/`. Additive neue Types sind ohne Sign-off erlaubt (nur Entfernen/Umbenennen bestehender Types braucht laut `knowledge-curator` Freigabe).
- Bestehende Quality-Pipeline `refactor` (`config/role-defaults.yaml → quality_pipelines.refactor`): `analyze` (senior-developer, Blast-Radius) → `implement` (developer) → `review` (Loop developer↔code-reviewer, max 2) → `commit` (git). `signal_keywords` enthalten wörtlich "aufräumen"/"Cleanup".
- Mechanischer `consistency-check` (`scripts/lib/consistency/{crossrefs,frontmatter,placeholders,docs,handoff_contracts}.py`) prüft ausschließlich **strukturelle** Dinge: Orchestrator-Tabellen-Abdeckung, Platzhalter, Anchors, Changelog-Erwähnungen, Schema-Refs, Frontmatter-Gültigkeit (`workflow_tier` ∈ `{required, recommended, optional}`). Er prüft **nicht** Freitext-Cross-Refs in der Prompt-Prosa, nicht Content-Duplikation, nicht Beschreibungsqualität — das bleibt manuelle Review-Arbeit.
- `hooks/1-generic/orchestrator-guard.sh` (v2.1.0, PreToolUse) blockt Write/Edit/Bash im Main-Chat, wenn `orchestrator.strict: true` in `.meta-config/project.yaml` gesetzt ist; Read/Glob/Grep sind bewusst nie blockiert. Git-Mutationen werden zusätzlich auch außerhalb von Strict-Mode geblockt. `Bash`-Delegates (`orchestrator`, `git`) können sich per Sentinel-Kommentarzeile (`#agent-meta:agent=<name>`) selbst deklarieren und so ausnehmen (Fix für Issue #390); für `Write`/`Edit` existiert **keine** äquivalente Ausnahme-Möglichkeit.
- `scripts/lib/hooks.py` verdrahtet PreToolUse-Hooks **ausschließlich für Claude** (`.claude/hooks/`, `.claude/settings.json`). Für keinen anderen Provider (OpenCode, Gemini, Continue, Copilot, Mammouth) existiert eine äquivalente Registrierung.

## Entscheidung 1: Kein Superpowers-Bezug

Ursprünglich diskutiert: ein Provider-Patch-Layer, der Claude-spezifisch auf Superpowers-Skills (`brainstorming`, `writing-plans`, `subagent-driven-development`, `requesting-code-review`, `systematic-debugging`, `finishing-a-development-branch`, `dispatching-parallel-agents`) verweist. Verworfen, weil:

1. Zu viel Komplexität für den Nutzen (7 Rollen betroffen, neue Provider-Patch-Infrastruktur nötig).
2. `feature.md` wurde dabei als das eigentliche Problem erkannt: es übernimmt implizit Planung, obwohl es als reiner Ausführungs-Orchestrator gedacht war — das Problem liegt tiefer als eine fehlende Superpowers-Anbindung.

**Entscheidung:** Kein Provider-Patch-Mechanismus, kein Superpowers-Bezug in `1-generic/`. `planner` bekommt eine eigene, native, providerunabhängige Planungslogik.

## Entscheidung 2: Neue Rolle `planner`

**Position:** Eigenständig, vom Orchestrator direkt ansteuerbar (wie `effort-estimator`) — kein festes Kettenglied zwischen `requirements` und `feature`. Rein ergänzend: `ideation`/`concept-reviewer`/`requirements` bleiben unverändert.

**Aufgabe:** Nimmt eine beliebige Eingabe (Konzept, REQ, Idee, Bug) und erzeugt einen konkreten Schritt-Plan: geordnete Tasks, Abhängigkeiten, Akzeptanzkriterien pro Schritt. Implementiert nichts selbst (wie `feature`). Delegiert Aufwandsschätzung an `effort-estimator` statt sie zu duplizieren (Referenz im Text, kein automatischer Tool-Call — Konsistenz mit dem Delegations-Muster von `developer`/`senior-developer`). Kein automatischer Handoff an `feature` nach Fertigstellung — Nutzer/Orchestrator entscheidet, ob der Plan ausgeführt wird.

**Frontmatter (neu, `agents/1-generic/planner.md`):**
```yaml
name: planner
version: 1.0.0
description: Use when a concept, REQ, or bug needs to be turned into a concrete, ordered implementation plan before work starts.
hint: Nutze planner wenn ein Konzept/REQ/Bug in konkrete, geordnete Umsetzungsschritte übersetzt werden muss.
tools: [Read, Write, Glob, Grep, TodoWrite]
```
`description`/`hint` bewusst als reiner "Use when"-Trigger formuliert (siehe Cleanup-Abschnitt Punkt 1 — gleicher Fehler soll hier nicht neu entstehen).

**`config/role-defaults.yaml` — neuer Eintrag:**
```yaml
planner:
  model: balanced
  workflow_tier: recommended
  description: Erzeugt konkrete, geordnete Umsetzungspläne aus Konzepten/REQs/Bugs
  routing:
    intent_keywords: [Plan, Planung, Schritte, Umsetzungsplan, "wie setzen wir das um"]
    parallel: false
    orchestrator_only: false
  short_desc: Umsetzungsplanung
```
`parallel: false` (Planung ist sequenziell, ein Agent), `orchestrator_only: false` (wie `effort-estimator` auch direkt vom Nutzer ansteuerbar).

## Entscheidung 3: Duale Persistenz-Konvention (`ideation` + `planner`)

Gilt identisch für beide Rollen, ersetzt `ideation`s bisher fixe `concept-<topic>.md`-Ablage:

- **Knowledge Engine aktiv** (`project.yaml` → Knowledge-Engine-Block gesetzt): Rolle schreibt **direkt** ins Wiki — kein Umweg über `knowledge-ingestor`, um Delegations-Overhead zu vermeiden (explizite Nutzerentscheidung). `ideation` legt Seiten vom Typ `Concept` unter `knowledge/wiki/concepts/` an, `planner` vom neuen Typ `Plan` unter `knowledge/wiki/plans/` (siehe Entscheidung 4). Beide pflegen `index.md`/`log.md` selbst nach, exakt wie es `knowledge-ingestor` für andere Quellen tut (gleiches Frontmatter-/OKF-Schema, nur ohne den Zwischenschritt).
- **Knowledge Engine inaktiv:** Fallback auf Flatfile im Projekt-Root — `concept-<topic>.md` (ideation, unverändert, Rückwärtskompatibilität) bzw. neu `plan-<topic>.md` (planner, gleiches Namensschema). Kein Bezug zu Superpowers-Pfaden (`docs/superpowers/...`) — bewusste Trennung, siehe Entscheidung 1.

**Warum nicht `knowledge-ingestor` delegieren:** geprüft und verworfen (Nutzerentscheidung) — der Delegations-Umweg (Rolle produziert Text → `knowledge-ingestor` persistiert) kostet einen zusätzlichen Agent-Aufruf pro Konzept/Plan, ohne dass die OKF-Konventionen komplex genug sind, um eine Trennung zu rechtfertigen.

## Entscheidung 4: Neuer Knowledge-Engine Concept Type `Plan`

Additive Erweiterung `knowledge/schema.md`:

```markdown
| `Plan` | `knowledge/wiki/plans/` | Concrete, ordered implementation plan derived from a concept, REQ, or bug — produced by the planner role |
```

Kein Sign-off nötig (additive Erweiterung, siehe `knowledge-curator`-Regeln). Abgrenzung zu `Guide` (dessen Beschreibung "spec" bereits nominell mit abdeckt): `Plan`-Seiten sind bewusst als eigene, filterbare Kategorie gedacht (Ausführungs-Artefakt mit Task-Liste), nicht als weitere Anleitung/Analyse — das war eine explizite Nutzerentscheidung gegen Wiederverwendung von `Guide`.

## Entscheidung 5: `ideation.md` — Zweck geschärft

Beschreibung wird präzisiert auf den ursprünglich intendierten Zweck: **"hilf mir meine Idee zu scopen und meine Gedanken zu sammeln"** — reine Scoping-/Explorations-Rolle. Explizite Abgrenzung zu `planner` wird ergänzt (ein Satz, z.B. unter den bestehenden "Do not"-Constraints: *"Do not produce an ordered implementation plan — hand off to `planner` for that."*). Funktional sonst unverändert (Fragetechnik, Handoff an `requirements`/`concept-reviewer` bleibt).

## Entscheidung 6: Intent-Tabelle / `config/role-defaults.yaml` schärfen

Zwei mechanische Änderungen an bestehenden Einträgen, um die bei der Analyse gefundene Keyword-Kollision zu entschärfen — **kein Rewrite**, nur gezielte Diffs:

| Rolle | Vorher (`intent_keywords`) | Nachher | Grund |
|---|---|---|---|
| `developer` | `[Feature, Bugfix, Refactoring, Implementierung, Code schreiben]` | `[Bugfix, Refactoring, Implementierung, Code schreiben]` | Bare `Feature` kollidiert direkt mit der Rolle `feature` (`Feature Lifecycle`, `komplexes Feature`). `Bugfix`/`Refactoring`/`Implementierung`/`Code schreiben` decken den direkten Dev-Case bereits ab, ohne den Namensclash. |
| `planner` (neu) | — | `[Plan, Planung, Schritte, Umsetzungsplan, "wie setzen wir das um"]` | Neuer Eintrag (Entscheidung 2) — schließt die Lücke, die dazu führte, dass "plane mir X" bisher diffus bei `developer`/`feature` landete. |

**Nicht verändert (bewusst):** `ideation` (`Architektur`) vs. `senior-developer` (`Architektur`) — beide behalten den Begriff, da er in unterschiedlichem Kontext berechtigt ist (explorativ vs. entscheidungs-/risikofokussiert bei bestehendem Code); eine Textänderung hier wäre Semantik-Rate statt belegter Fix und bleibt Out of Scope (siehe unten).

**Tier/Parallel-Doku-Klarstellung:** Kurzer Hinweis wird in den generierten Tabellenkopf (`scripts/lib/delegation_table.py::get_intent_routing_table()`, Header-Zeile) ergänzt: *"Parallel ist rein informativ — kein Runtime-Enforcement, nur CI-Konsistenzcheck bei required/recommended-Tier-Abdeckung."* Verhindert falsche Erwartungshaltung, dass die Spalte tatsächliches Parallel-Scheduling steuert.

## Entscheidung 7: Delegation-Enforcement-Sichtbarkeit (neu)

**Befund:** In diesem Projekt ist `orchestrator.strict: true` gesetzt (`.meta-config/project.yaml`). Die einzige technische Durchsetzung dieser Einstellung, `hooks/1-generic/orchestrator-guard.sh`, wird laut `scripts/lib/hooks.py` ausschließlich für den Provider Claude verdrahtet (`.claude/hooks/`, registriert in `.claude/settings.json`). Für alle anderen unterstützten Provider (OpenCode, Gemini, Continue, Copilot, Mammouth) existiert keine äquivalente PreToolUse-Registrierung — `strict: true` ist dort ein **stiller No-Op**: der Nutzer konfiguriert eine Sicherheitsgrenze, die auf einem Teil der unterstützten Provider schlicht nicht existiert, ohne jede Warnung. Beobachtetes Symptom (Nutzer-Report): der Orchestrator liest und schreibt bei Recherche- und Implementierungs-Tasks situativ selbst statt zu delegieren — auf Claude teilweise durch den Guard verhindert (Write/Edit/Bash im Main-Chat), auf OpenCode gar nicht.

**Explizit nicht Teil dieser Entscheidung (Abgrenzung):**
- Kein Fix für die fehlende Write/Edit-Subagent-Ausnahme unter Claude-Strict-Mode (der Sentinel-Trick existiert bisher nur für `Bash`/git; legitime Subagenten-Edits könnten unter Strict-Mode theoretisch mitgeblockt werden — separates, tieferes Thema).
- Keine Implementierung eines OpenCode-Hook-Äquivalents.
- Keine Änderung am "Read/Grep wird nie geblockt"-Designprinzip.

Diese drei Punkte sind echte Enforcement-*Implementierungen* und bewusst auf eine spätere Spec verschoben (siehe Out of Scope). Diese Entscheidung behebt ausschließlich die **Intransparenz**: dass eine gesetzte Sicherheitsgrenze unbemerkt wirkungslos sein kann.

**Fix — neue Validierung in `sync.py --validate`:**

1. `scripts/lib/hooks.py` bekommt eine explizite, kleine Konstante mit den Providern, die PreToolUse-Hook-Verdrahtung unterstützen (aktuell: `{"claude"}`). Additive Erweiterung bei künftigem Provider-Support (Ein-Zeilen-Änderung).
2. Neue Check-Funktion (Ort: `scripts/lib/consistency/` — analog zu den bestehenden Cross-Ref-/Frontmatter-Checks): liest `orchestrator.strict` (inkl. `provider-overrides`, siehe bestehende Resolve-Logik in `orchestrator-guard.sh`) und die im Projekt aktiven Provider aus `.meta-config/project.yaml`. Für jeden aktiven Provider ohne Hook-Support bei effektiv aktivem Strict-Mode: **WARNING** (kein Hard-Fail — Sichtbarkeit, keine neue harte Gate-Bedingung), Text z.B.: *"orchestrator.strict is active for provider '<provider>', but this provider has no PreToolUse hook wiring — the setting has no runtime effect there."*
3. Der Check läuft bei jedem `sync.py --validate`-Aufruf mit (kein neues Flag nötig) und ist damit automatisch Teil der bestehenden CI (`validate.yml`, `orchestration-test.yml`).

**Warum WARNING statt Hard-Fail:** Strict-Mode kann bewusst nur für einen Teil der Provider eines Multi-Provider-Projekts gewünscht sein (`provider-overrides` existiert genau dafür). Ein Hard-Fail würde diesen legitimen Fall bestrafen; die Warnung informiert, ohne den Sync-Lauf zu blockieren.

## Cleanup-Abschnitt — 7-Rollen-Cluster

Gefunden bei der Analyse von `ideation`, `concept-reviewer`, `requirements`, `feature`, `effort-estimator`, `developer`, `senior-developer` gegen die Superpowers-`writing-skills`-Qualitätskriterien (SDO: Description = Trigger, nicht Workflow-Zusammenfassung; Token-Effizienz; Tool-Grant-Konsistenz):

| # | Fix | Datei(en) | Typ |
|---|---|---|---|
| 1 | `description`/`hint` auf reinen "Use when..."-Trigger kürzen, Workflow-Details raus | `ideation.md`, `concept-reviewer.md`, `feature.md` (Extremfall: komplette Pipeline in description **und** hint dupliziert), `developer.md` | Semantisch, manuell |
| 2 | Toten Cross-Ref `architect` entfernen/korrigieren (keine Rolle dieses Namens existiert, gemeint ist vermutlich `developer` oder gar nichts) | `concept-reviewer.md` Z.94 | Semantisch, manuell |
| 3 | `senior-developer` als Eskalationspfad in Lifecycle-Tabelle ergänzen (senior-developer kennt die Eskalation von developer bereits, feature.md nicht umgekehrt) | `feature.md` | Semantisch, manuell |
| 4 | `TodoWrite` in Frontmatter-`tools:` ergänzen (wird im Body/Workflow Schritt 5 bereits referenziert) | `effort-estimator.md` | Strukturell, `consistency-check` deckt das NICHT ab (kein Tool-Grant-vs-Body-Check implementiert) |
| 5 | Toten `Agent`-Tool-Grant entfernen (Constraint sagt explizit: nie per Tool-Call delegieren, nur Text-Referenz) | `developer.md` | Strukturell, ebenfalls kein automatischer Check vorhanden |
| 6 | Self-/Browser-Verification-Absatz deduplizieren (fast wortgleich an zwei Stellen) — eine Quelle, Querverweis statt Copy-Paste | `developer.md` ↔ `senior-developer.md` | Semantisch, manuell |

> **Punkt 7 gestrichen** (ursprünglich: verwaiste `</output></output>`-Tags entfernen). Nachprüfung per Grep über alle 39 generischen Agenten (`agents/1-generic/*.md`) findet kein einziges Vorkommen von doppelten `</output></output>`-Tags — nur reguläre, einfache `</output>`-Schließtags als bestehende, korrekte Template-Struktur. Der Befund ist nicht reproduzierbar und wird nicht umgesetzt.

**Pipeline-Einsatz für die Umsetzung:** Die Cleanup-Punkte 1–6 sind reine Text-/Frontmatter-Änderungen an Prompt-Prosa, kein Code-Refactoring. Die `refactor`-Quality-Pipeline (`analyze` mit senior-developer-Blast-Radius-Analyse → `implement` → `review`-Loop developer↔code-reviewer → `commit`) ist dafür **strukturell überdimensioniert** (Blast-Radius-Analyse für eine `description`-Zeile, Code-Reviewer-Loop für Prompt-Text ohne Code-/Logik-Bezug). **Entscheidung:** direkte Einzeldelegation an `developer` (Textänderungen) mit anschließendem `validator`-Check statt Pipeline — kein neuer Pipeline-Typ nötig für diesen einmaligen Cleanup.

**Verifikation:** `consistency-check --file <geänderte Datei>` je Fix als struktureller Regressionsschutz (bestätigt: aktuell PASS auf allen 7 Dateien, d.h. keiner der obigen Findings wird heute schon gemeldet — nach dem Fix muss der Check weiterhin PASS bleiben). Punkte 1/2/3/6 sind semantisch und bleiben manuell verifizierbar (Nachlesen), keine automatische Abdeckung vorhanden oder geplant.

## Planner-Output-Format und Consumer (`planner-output-v1`)

**Problem, das dieser Abschnitt schließt:** `planner` produziert ohne diese Festlegung einen Plan ohne definierten Leser — der naheliegende Consumer `feature` kennt keinen "Plan laden"-Schritt. Ohne diese Kopplung entsteht ein Read-Only-Feature, das Pläne produziert, die niemand ausführt.

**Artefakt-Format** (`plan-<topic>.md` bzw. Knowledge-Wiki-Seite Typ `Plan`):

```markdown
## Plan: <title>

**Source:** <REQ-ID | concept-<topic>.md | Bug-#NNN>
**Estimated effort:** <effort-estimator summary>

| # | Step | Agent | Depends on | Acceptance criteria |
|---|---|---|---|---|
| 1 | <task> | <role> | — | <measurable> |
| 2 | <task> | <role> | 1 | <measurable> |
| N | ... | ... | ... | ... |
```

**Consumer:**
- `feature` (primär): empfängt den Plan als optionalen Input über `payload.plan_ref`, führt die Schritte der Reihe nach aus.
- Orchestrator (sekundär): kann ein Plan-Fragment auch direkt an `developer`/`senior-developer` delegieren, wenn kein Full-Lifecycle nötig ist (z.B. reiner Refactoring-Plan ohne REQ-Traceability).

**Änderung an `feature.md` — neuer optionaler Schritt 0 „Load plan" (vor Schritt 1):**

```markdown
## 0 — Load plan

**Active when:** `payload.plan_ref` is set.

1. Read the referenced plan file/page.
2. Validate plan structure: Tabelle mit Spalten #, Step, Agent, Depends on, Acceptance criteria vorhanden; mindestens eine Zeile; keine zirkulären Abhängigkeiten in "Depends on".
3. Bei fehlenden Pflichtfeldern oder invalidem Plan: Fehler mit Liste der fehlenden Felder melden, **kein Branch, kein Start**. Nur optionale, nicht relevante Schritte dürfen explizit ignoriert werden.
4. Plan-Schritte auf Lifecycle-Phasen mappen (Plan-Step mit `agent: tester` → Schritt 3 "Write tests", `agent: developer` → Schritt 4 "Implementation", `agent: requirements` → Schritt 2, falls noch nicht erledigt).
```

**Payload-Erweiterung (A2A Inbound):** `payload.plan_ref: <relative-path-to-plan-file | null>`.

**Constraint-Ergänzung in `feature.md`:** "When `plan_ref` is set: validate plan before branch creation. Do not create a branch for an invalid plan."

**Output-Contract-Ergänzung:** `PLAN_REF: <path | n/a>`.

## Routing-Regeln: Planner vs. Feature vs. Developer vs. Requirements

| User-Intent | Route zu | Begründung |
|---|---|---|
| "Setze Feature X um" (REQ bereits vorhanden) | `feature` | Keine Planung nötig, REQ-ID liegt vor |
| "Implementiere X" (klar, 1-3 Dateien) | `developer` | Direkter Dev-Case, kein Lifecycle nötig |
| "Erstelle Anforderung für X" | `requirements` | Reine REQ-Erstellung |
| "Plane die Umsetzung von X" | `planner` | Expliziter Planungswunsch |
| "Wie setzen wir X um?" | `planner` | Planungsfrage, kein Implementierungsauftrag |
| "Konzept X ist fertig, was nun?" | `planner` | Übergang Konzept → Plan |
| "X soll umgesetzt werden" (ohne REQ, komplex) | `planner` → `feature` | Erst Plan, dann Ausführung |
| "Analysiere/erkunde X" (vor jedem Code) | `explorer` | Read-Only-Analyse |
| "Sammle meine Gedanken zu X" | `ideation` | Reines Scoping, kein Plan |

## Korrektur: Refactoring-Few-Shot-Pattern in `_wf-orchestrator-reference.md`

**Datei:** `agents/1-generic/_wf-orchestrator-reference.md`, Zeile 18.

**Aktuell (falsch):** `| Refactoring | ideation→dev→tester→review→git |` — `ideation` ist eine explorative Rolle ("hilf mir meine Gedanken zu sammeln"), kein Refactoring-Analyseschritt.

**Korrektur:** `| Refactoring | explorer→dev→tester→review→git |` (minimale Korrektur, ersetzt nur den falschen Agenten, behält das bestehende Pattern bei — vorzuziehen gegenüber einem Pipeline-Verweis, der mehr Zeichen ändert).

## Branch-Hinweis

Umsetzung erfolgt auf dem bereits existierenden Branch `feat/planner-agent-and-cluster-cleanup` (aktueller Branch, von `main` abgezweigt). Vor Implementierungsbeginn prüfen, ob zwischenzeitlich weitere Änderungen an den betroffenen Dateien (7-Rollen-Cluster, `config/role-defaults.yaml`, `scripts/lib/hooks.py`) auf `main` gelandet sind — ggf. rebasen.

## Testing

- **`planner`-Neuanlage:** `sync.py --dry-run` auf einem Testprojekt mit `planner` in `config['roles']` → generierter Agent enthält korrekte `description`/`hint`/`tools`; `sync.py --validate` (Konsistenz-Suite) bleibt PASS.
- **Intent-Tabellen-Diff:** `scripts/lib/consistency/crossrefs.py::check_orchestrator_table()` bleibt grün (neuer `planner`-Eintrag mit `workflow_tier: recommended` muss in der generierten Tabelle auftauchen — automatisch durch den bestehenden Check abgedeckt).
- **KE Concept Type `Plan`:** Testseite mit `type: Plan` anlegen → landet unter `knowledge/wiki/plans/`, `index.md`/`log.md`-Eintrag vorhanden, `knowledge-linter` meldet keinen OKF-Compliance-Fehler.
- **`feature.md` Plan-Input:** `payload.plan_ref` mit validem Plan → Schritte 2–6 folgen der Plan-Tabelle; mit invalidem Plan (fehlende Spalte, zirkuläre Abhängigkeit) → Abbruch vor Branch-Erstellung, Fehlermeldung listet fehlende Felder.
- **Delegation-Enforcement-Sichtbarkeit:** `sync.py --validate` auf Testprojekt mit `orchestrator.strict: true` + Provider `opencode` aktiv → WARNING erscheint mit Providername; gleiches Projekt mit nur Provider `claude` aktiv → kein WARNING.
- **Cleanup Punkte 4/5:** `consistency-check --all` vor und nach dem Fix vergleichen (muss vorher wie nachher PASS bleiben — reine Qualitätsverbesserung, keine Verhaltensänderung).
- **Cleanup Punkte 1/2/3/6:** manuelles Review der geänderten Dateien (kein automatisierter Test vorhanden, wie oben dokumentiert).

## Akzeptanzkriterien

**Planner:**
- [x] `planner.md` generiert via `sync.py` → `description`/`hint` als reiner "Use when"-Trigger
- [x] Planner-Ausgabe enthält Tabelle mit #, Step, Agent, Depends on, Acceptance criteria
- [x] Planner delegiert Aufwandsschätzung als Text-Referenz an `effort-estimator` (kein Tool-Call)
- [x] Planner persistiert gemäß dualer Konvention (Wiki wenn aktiv, sonst `plan-<topic>.md` im Projekt-Root)

**Feature-Kopplung:**
- [x] `feature.md` lädt und validiert `plan_ref`; invalider Plan → Abbruch, kein Branch
- [x] Output-Contract enthält `PLAN_REF`

**Routing:** Strukturell abgesichert (Intent-Keywords korrekt generiert, per Konsistenz-Check verifiziert) — die vier Zeilen unten sind Laufzeit-/Verhaltenskriterien des Orchestrators und wurden nicht live am Provider getestet, nur die zugrundeliegenden Daten:
- [x] `"Plane X"` → Orchestrator routet zu `planner`, nicht zu `feature` oder `developer` (Intent-Keywords vorhanden, kein Clash — Live-Test steht aus)
- [x] `"Wie setzen wir X um?"` → `planner` (Keyword `"wie setzen wir das um"` vorhanden)
- [x] `"Setze X um"` mit vorhandenem Plan → `feature` mit `plan_ref` (Payload-Feld + Load-Plan-Schritt implementiert)
- [x] `"Implementiere X"` (trivial, ≤2 Dateien) → `developer` (unverändert, kein Clash mehr durch entferntes `Feature`-Keyword)
- [x] Keyword `Feature` in `developer`-Intent-Tabelle entfernt (kein Clash mehr)

**Duale Persistenz:**
- [x] Knowledge Engine aktiv → Plan-Seite in `knowledge/wiki/plans/` mit Type=`Plan`, Index/Log aktualisiert (Typ registriert, Verzeichnis existiert, Planner-Workflow beschreibt Index/Log-Pflege — Erstanlage einer echten Plan-Seite durch den Planner-Agenten steht noch aus)
- [x] Knowledge Engine inaktiv → `plan-<topic>.md` im Projekt-Root (im Planner-Workflow implementiert)
- [x] `knowledge-linter` akzeptiert Type=`Plan` ohne Fehler (Typ ist in `knowledge/schema.md` registriert, wovon `knowledge-linter`s OKF-Check liest; kein Live-Agentenlauf durchgeführt)

**Delegation-Enforcement-Sichtbarkeit:**
- [x] `sync.py --validate` warnt bei `orchestrator.strict: true` + Provider ohne Hook-Support (live verifiziert: 2 Warnings für Opencode/Gemini in diesem Repo)
- [x] Kein Warning bei ausschließlich Hook-fähigen Providern aktiv (Testabdeckung in `tests/test_orchestrator_strict_visibility.py`)
- [x] Provider-Capability ist additiv erweiterbar (ein Eintrag pro Provider) — **Umsetzung weicht vom Wortlaut ab:** statt einer neuen Konstante in `scripts/lib/hooks.py` wird das bereits existierende `has_hooks`-Feld aus `config/ai-providers.yaml` wiederverwendet (Single Source of Truth, keine Duplikation zur bestehenden Provider-Konfiguration) — funktional äquivalent und ebenso additiv erweiterbar, aber nicht am ursprünglich benannten Ort. Bewusste, dokumentierte Abweichung (siehe Task 5 im Umsetzungsplan).

**Konsistenz gesamt:**
- [x] Consistency-Check (`crossrefs.py`) meldet `planner` als abgedeckt
- [x] Generierte Intent-Tabelle enthält `planner` mit korrekten Keywords
- [x] `sync.py --validate` bleibt PASS

## Priorisierte Umsetzungsreihenfolge und Freigabekriterien

| Prio | Schritt | Hängt ab von | Freigabekriterium |
|---|---|---|---|
| P1 | Planner-Agent anlegen (`planner.md` + `role-defaults.yaml`) | — | `sync.py --validate` PASS; generierter Agent enthält korrekte `description`/`hint`/`tools` |
| P1 | Planner-Output-Format (`planner-output-v1`) in `planner.md` integrieren | P1 (Agent existiert) | Planner-Ausgabe valide gegen Format-Schema (manuell prüfbar) |
| P1 | Intent-Tabelle: `developer`-Keyword `Feature` entfernen, `planner`-Keywords eintragen | P1 | `crossrefs.py` grün; kein `Feature`-Clash mehr |
| P1 | `_wf-orchestrator-reference.md`: Refactoring-Pattern korrigieren | — | Pattern `ideation→dev→...` ersetzt durch `explorer→dev→...` |
| P1 | Delegation-Enforcement-Sichtbarkeit: Provider-Capability-Konstante + Validate-Check | — | WARNING erscheint korrekt für Nicht-Hook-Provider bei aktivem Strict-Mode |
| P2 | `feature.md` um Plan-Input erweitern (Schritt 0, `plan_ref`-Parsing) | P1 (Planner existiert) | Feature lädt und validiert `plan_ref`; falscher Plan → Abbruch |
| P2 | Orchestrator-Routing-Logik: Plan-Erkennung → `planner`, Plan-Weiterleitung → `feature(plan_ref=...)` | P1, P2 (feature kann plan_ref) | "Plane X" → Planner; "Setze X um" mit Plan → Feature mit Plan |
| P2 | Duale Persistenz in `planner.md` implementieren | P1 | Plan-Seite korrekt in Wiki oder als Root-Flatfile |
| P3 | Cleanup Punkte 1-3, 6 (Textänderungen an 7 Agenten) | — | `description`/`hint` als reiner Trigger; toter Cross-Ref entfernt; Senior-Developer in Feature-Lifecycle-Tabelle; Deduplication developer↔senior-developer |
| P3 | Cleanup Punkte 4-5 (Tool-Grants: `effort-estimator` +`TodoWrite`, `developer` -`Agent`) | — | Tools in Frontmatter korrekt; `consistency-check` bleibt PASS |
| P4 | `consistency-check` final: alle Cleanup-Dateien + Planner gegen Suite | P1-P3 | `sync.py --validate` PASS auf allen betroffenen Dateien |
| P4 | Manuelles Review: semantische Cleanup-Punkte 1/2/3/6 nachlesen | P3 | Alle Punkte optisch verifiziert, keine Verschlechterung |

**Freigabe-Gate Gesamt:**
- Alle P1-Schritte abgeschlossen → Planner ist eigenständig nutzbar (generiert Pläne, persistiert sie, wird korrekt geroutet) UND Delegation-Enforcement-Lücke ist sichtbar gemacht.
- Alle P2-Schritte abgeschlossen → Planner+Feature-Kette ist durchgängig (Plan → Ausführung).
- Alle P3-Schritte abgeschlossen → 7-Rollen-Cluster bereinigt.
- P4-Schritte → Qualitäts-Gate, vor Merge.

## Out of Scope

- Superpowers-Integration in jeglicher Form (Entscheidung 1) — kann bei Bedarf als eigene, spätere Spec wieder aufgegriffen werden, falls sich die Zurückhaltung als zu konservativ erweist.
- Vollständiger Sweep über alle ~40 generischen Agenten — nur der 7-Rollen-Planungs-/Umsetzungs-Cluster war Teil der Analyse.
- Textliche Auflösung der `Architektur`-Keyword-Überlappung zwischen `ideation` und `senior-developer` — bewusst nicht angefasst (siehe Entscheidung 6), da keine belegte Fehlroutung vorliegt, nur eine theoretische Ambiguität.
- Automatisierte Prüfung von Tool-Grant-vs-Body-Konsistenz oder Freitext-Cross-Refs im `consistency-check` — wäre eine sinnvolle Erweiterung des Checks selbst, aber eigenständiges Thema, nicht Teil dieser Spec.
- Migration bestehender Projekte, die bereits `concept-<topic>.md`-Dateien im Root liegen haben, auf die Knowledge-Engine-Struktur — Bestandsdateien bleiben unangetastet, nur neue Konzepte/Pläne nutzen das duale Schema.
- **Echte Delegation-Enforcement-Implementierung über die reine Sichtbarkeit hinaus** (Entscheidung 7): Write/Edit-Subagent-Ausnahme-Mechanismus für Claude-Strict-Mode, OpenCode-Hook-Äquivalent, Read/Grep-Nudge-Logik. Eigenständige, tiefergehende Spec, sobald die Sichtbarkeits-Basis steht.
- **CI-Modernisierung** (Caching, Matrix-Reduktion, Laufzeit, generelle Health-Fragen) — orthogonal zum Orchestrierungs-Thema dieser Spec, wird als eigenes, separates Brainstorming direkt im Anschluss behandelt.
