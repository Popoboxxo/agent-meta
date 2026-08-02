# Agent-Orchestrierung: Planner-Rolle, Intent-Tabelle, Cluster-Cleanup — Design

**Status:** Entwurf zur Freigabe
**Kontext:** Ausgelöst durch die Frage "wie integrieren wir Superpowers-Skills (brainstorming, writing-plans, ...) in agent-meta" — im Brainstorming wurde das verworfen (zu komplex, Provider-Kopplung an Claude widerspricht der Provider-Agnostik-Prämisse von `1-generic/`). Stattdessen: ein neuer, nativer, providerunabhängiger `planner`-Agent, eine Schärfung der Orchestrator-Intent-Tabelle, und ein Cleanup-Abschnitt für einen 7-Rollen-Cluster, der bei der Analyse auffiel.

## Ausgangslage — was existiert bereits

- `ideation.md` → `concept-<topic>.md` (fix im Projekt-Root, kein Knowledge-Engine-Bezug), gefolgt optional von `concept-reviewer` (Generator-Critic-Loop), dann `requirements.md` (REQ-IDs, `docs/REQUIREMENTS.md`).
- `feature.md` orchestriert danach den kompletten Rest (Branch → REQ optional → TDD → Impl → Validate → PR) — **ohne eigenen Planungsschritt**. Der Übergang "Konzept/REQ vorhanden" → "konkrete Umsetzungsschritte" passiert implizit, nirgends als Artefakt.
- Die Intent-Routing-Tabelle in `use-orchestrator.md` ist **generiert**, nicht handgepflegt: `scripts/lib/delegation_table.py::get_intent_routing_table()` liest `workflow_tier` und `routing.{intent_keywords,parallel,orchestrator_only}` aus `config/role-defaults.yaml` pro Rolle. `Tier` wird zusätzlich von `scripts/lib/consistency/crossrefs.py::check_orchestrator_table()` geprüft (jede Rolle mit `tier in (required, recommended)` muss in der Tabelle auftauchen — WARNING sonst). `Parallel` ist **rein informativ**, kein Runtime-Enforcement, keine Hook-Logik dazu.
- Die Knowledge Engine (aktiv in diesem Repo, Domäne `personal`) kennt 5 Concept Types (`knowledge/schema.md`): `Concept`/`Architecture` → `concepts/`, `API Reference` → `entities/`, `Guide` → `topics/` (deckt laut Beschreibung bereits "howto, analysis, audit, or spec" ab), `Session Conclusion` → `sources/`. Additive neue Types sind ohne Sign-off erlaubt (nur Entfernen/Umbenennen bestehender Types braucht laut `knowledge-curator` Freigabe).
- Bestehende Quality-Pipeline `refactor` (`config/role-defaults.yaml → quality_pipelines.refactor`): `analyze` (senior-developer, Blast-Radius) → `implement` (developer) → `review` (Loop developer↔code-reviewer, max 2) → `commit` (git). `signal_keywords` enthalten wörtlich "aufräumen"/"Cleanup".
- Mechanischer `consistency-check` (`scripts/lib/consistency/{crossrefs,frontmatter,placeholders,docs,handoff_contracts}.py`) prüft ausschließlich **strukturelle** Dinge: Orchestrator-Tabellen-Abdeckung, Platzhalter, Anchors, Changelog-Erwähnungen, Schema-Refs, Frontmatter-Gültigkeit (`workflow_tier` ∈ `{required, recommended, optional}`). Er prüft **nicht** Freitext-Cross-Refs in der Prompt-Prosa, nicht Content-Duplikation, nicht Beschreibungsqualität — das bleibt manuelle Review-Arbeit.

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
| 7 | Verwaiste `</output></output>`-Tags am Dateiende entfernen (Render-Artefakt ohne öffnendes Tag) | Alle 7 Dateien | Mechanisch, per Grep auffindbar |

**Pipeline-Einsatz für die Umsetzung:** die bestehende `refactor`-Quality-Pipeline (`analyze` → `implement` → `review` Loop → `commit`) passt strukturell exakt (`signal_keywords` enthalten "aufräumen"/"Cleanup" wörtlich) und kann die Umsetzung tragen, statt sie manuell zu orchestrieren.

**Verifikation:** `consistency-check --file <geänderte Datei>` je Fix als struktureller Regressionsschutz (bestätigt: aktuell PASS auf allen 7 Dateien, d.h. keiner der obigen Findings wird heute schon gemeldet — nach dem Fix muss der Check weiterhin PASS bleiben). Punkte 1/2/3/6 sind semantisch und bleiben manuell verifizierbar (Nachlesen), keine automatische Abdeckung vorhanden oder geplant.

## Testing

- **`planner`-Neuanlage:** `sync.py --dry-run` auf einem Testprojekt mit `planner` in `config['roles']` → generierter Agent enthält korrekte `description`/`hint`/`tools`; `sync.py --validate` (Konsistenz-Suite) bleibt PASS.
- **Intent-Tabellen-Diff:** `scripts/lib/consistency/crossrefs.py::check_orchestrator_table()` bleibt grün (neuer `planner`-Eintrag mit `workflow_tier: recommended` muss in der generierten Tabelle auftauchen — automatisch durch den bestehenden Check abgedeckt).
- **KE Concept Type `Plan`:** Testseite mit `type: Plan` anlegen → landet unter `knowledge/wiki/plans/`, `index.md`/`log.md`-Eintrag vorhanden, `knowledge-linter` meldet keinen OKF-Compliance-Fehler.
- **Cleanup Punkte 4/5/7:** `consistency-check --all` vor und nach dem Fix vergleichen (muss vorher wie nachher PASS bleiben — reine Qualitätsverbesserung, keine Verhaltensänderung).
- **Cleanup Punkte 1/2/3/6:** manuelles Review der geänderten Dateien (kein automatisierter Test vorhanden, wie oben dokumentiert).

## Out of Scope

- Superpowers-Integration in jeglicher Form (Entscheidung 1) — kann bei Bedarf als eigene, spätere Spec wieder aufgegriffen werden, falls sich die Zurückhaltung als zu konservativ erweist.
- Vollständiger Sweep über alle ~40 generischen Agenten — nur der 7-Rollen-Planungs-/Umsetzungs-Cluster war Teil der Analyse.
- Textliche Auflösung der `Architektur`-Keyword-Überlappung zwischen `ideation` und `senior-developer` — bewusst nicht angefasst (siehe Entscheidung 6), da keine belegte Fehlroutung vorliegt, nur eine theoretische Ambiguität.
- Automatisierte Prüfung von Tool-Grant-vs-Body-Konsistenz oder Freitext-Cross-Refs im `consistency-check` — wäre eine sinnvolle Erweiterung des Checks selbst, aber eigenständiges Thema, nicht Teil dieser Spec.
- Migration bestehender Projekte, die bereits `concept-<topic>.md`-Dateien im Root liegen haben, auf die Knowledge-Engine-Struktur — Bestandsdateien bleiben unangetastet, nur neue Konzepte/Pläne nutzen das duale Schema.

## Branch-Hinweis

Aktueller Branch (`feat/auto-prepare-mcp-secrets`) ist inhaltlich unabhängig von diesem Thema (MCP-Secrets-Bootstrapping vs. Agent-Orchestrierung) — vor Implementierungsbeginn einen eigenen Branch (z.B. `feat/planner-agent-and-cluster-cleanup`) von `main` abzweigen.
