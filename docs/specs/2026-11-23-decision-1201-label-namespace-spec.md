---
spec-id: SPEC-1201-label-namespace
status: APPROVED
approval: "User, 2026-11-23, Einzelentscheidung"
issue: 1201
issue-url: "https://github.com/Popoboxxo/agent-meta/issues/1201"
branch: fix/decision-points-bundle-20261123
base-commit: 278ba54f
date: 2026-11-23
class: L
depends-on: SPEC-issue-label-taxonomy-2026-11-09
---

# Issue-Label-Namespace: plattformkonforme Projektion (#1201) — Spec

> Status: APPROVED (User, 2026-11-23, Einzelentscheidung)

## Problem / Ziel / Nicht-Ziele

**Problem (re-gemessen @ `278ba54f`):** `config/conventions-presets.yaml` enthält dreimal den String `namespace: "type: {type}"` — Zeilen **59** (`default`), **96** (`calver`), **128** (`conventional-strict`). `scripts/lib/conventions.py::_render_git_issue_naming()` (Funktion **:277–292**, Namespace-Read **:285**, Emission **:290**) rendert daraus `type: <type>` in `GIT_ISSUE_NAMING_BLOCK`, gelesen nur von `agents/1-generic/git.md:159` (nicht `:151` — alter Stand, vgl. Schwester-Spec #1204). Das Ergebnis `type: bug` trifft keine Zielkonvention: GitHub/Gitea nutzen flache bzw. `/`-g scoped Labels, GitLab Scoped-Labels `type::bug`. Ursache ist die Vermischung von Inhalt (Achse `type`) und Projektion (Separator) — identisch mit der von #1188 dokumentierten Ursache. Der Wert ist heute wirkungslos, beim Aktivieren sofort falsch; es gibt keine Eindeutigkeitsgarantie (ein Issue kann `type: bug` *und* `type: feat` tragen).

**Ziel:** Den Namespace-Default durch die in #1188 (APPROVED) definierte, plattformprojektierte Separator-Form ersetzen und legacy `type: …`-Werte beim Sync mit Warnung migrieren — nie still umbenennen. Betroffene Subsysteme: Convention-Presets, Renderer, Konfigurations-Migration; Projection/Adapter kommen aus #1188.

**Nicht-Ziele:** #1188 selbst implementieren (Taxonomie, Adapter-Executor, CLI, Admin-UI); Tracker-API-Calls, Prune/Delete; die eigenen flachen Label-Tabellen der drei Issue-erstellenden Rollen ändern (das ist #1188 AC-6); neue Schema-Keys erfinden.

## Interface Contracts (Datei:Symbol, Signatur, Fehlerpfade)

**IC-2 — `scripts/lib/issue_conventions.py::project_label(axis: Axis, value: AxisValue, projection: Projection) -> str`**
- Von #1188 gelieferter Resolver mit **exakt dieser Signatur** im APPROVED Plan `docs/plans/2026-11-09-issue-label-taxonomy-plan.md:511` und `:924` (`SPEC-issue-label-taxonomy-2026-11-09`). #1201 pinnt nur seine Namespace-Verwendung — **kein Duplikat, kein neuer Wrapper, keine neue Implementierung**. (Korrektur: #1188-Spec §IC-3 ist die Datendatei `config/issue-adapters.yaml`, nicht dieser Resolver.)
- Projektion: Separator **kardinalitätsbewusst aus dem übergebenen `projection`-Objekt** ableiten statt aus rohem `adapter["defaults"]` — die `single`-Achse `type` verwendet den `single`-Wert der Objektform `separator: {single, multi}` (#1188 K-2, Plan `:147-153`/`:513`; zugehörige `source`-Schlüssel `separator-single`/`separator-multi` in `Projection.sources`, Plan `:938-939`), `multi`-Achsen den `multi`-Wert. Ergebnis `f"{axis}{separator}{value}"`. Präzedenz zwischen Adapter-Default (#1188 IC-3), Framework-Plattform-Default und Projekt-Override folgt der #1188-Siebenstufigkette (Plan T5, `:477-490`).
  - `github`, `gitea` → `separator.single: "/"` → **`type/bug`**
  - `gitlab` (Capability `scoped-labels`) → `separator.single: "::"` → **`type::bug`** (dessen `separator.multi: "-"` betrifft nur `multi`-Achsen wie `area`, AC-2b — hier nicht wirksam)
- Verzweigung ausschließlich über Capability-Flags, nie über Provider-Namen. URL-Kodierung (`quote(name, safe="")`) nur im Executor, nie im projizierten Namen.
- Fehlerpfad: fehlender Separator oder Separator mit Leerzeichen/`": "` → `IssueConfigError`, Exit 2, kein Write, kein API-Call (#1188 IC-4).

**IC-3 — `scripts/lib/conventions.py::_render_git_issue_naming(spec: dict) -> str`**
- Signatur unverändert. `:285` liest künftig den projizierten Namespace (IC-2) statt des rohen Preset-Strings; `:290` emittiert ihn in die `**Labels:**`-Zeile.
- Invariante: kein Emissionspfad erzeugt einen Label-Namen mit `": "`. Ist keine Projektion verfügbar (Legacy-Only-Config), Namespace-Token weglassen und warnen — niemals den Legacy-String ausgeben.
- Fehlerpfad: wie IC-2 (Resolver-Fehler propagiert, kein Fallback auf `type: <type>`).

**IC-4 — `scripts/lib/config.py::_build_convention_variables()` (Migrations-Warnung)**
- Erkennt `conventions.issues.labels.namespace` mit `": "`; emittiert genau eine `log.warning` mit Preset-Name, altem Wert und Verweis auf `issue-conventions`/#1188. Kein stumbles Rewriting, kein Config-Schreibzugriff.
- Fehlerpfad: mehrfaches Vorkommen → eine Warnung pro betroffenem Preset. Bei `enabled: false` wird der Namespace-Token ebenfalls ohne `": "`-Literal emittiert (bzw. weggelassen, IC-3); die Golden-Baseline wird deshalb **bewusst aktualisiert (nur Namespace-Token)** — Phase-F-Plan Task 2 Step 2 (`docs/superpowers/plans/2026-11-11-phase-f-label-taxonomy.md:186`: „Golden-Test bewusst anpassen und die Änderung im Commit-Body/PR benennen") und D-1201-B. Bewusste Abweichung von der Additiv-Klausel des #1188-Plans (`:243-245`, byte-identisch zu `aaed14c2`) bzw. #1188 AC-9 — der #1188-Kern selbst bleibt davon unberührt.

## Datenfluss

`conventions-presets.yaml` (Legacy-String, 3 Anker) → IC-4 erkennt & warnt (read-only) → #1188-Resolver IC-2 löst Achse `type` + Adapter-Separator auf (`type/bug` | `type::bug`) → IC-3 rendert `GIT_ISSUE_NAMING_BLOCK` → `git.md:159`. Kein Write in diesem Change; Persistenz (`.meta-config/issue-labels-state.json`) ausschließlich über #1188 `sync.py --labels --apply`.

## Acceptance Criteria

1. **Given** ein Preset mit Legacy-Namespace, **when** der Sync rendert, **then** enthält kein emittiertes Label `": "` (IC-1, IC-3).
2. **Given** GitHub-Adapter, **when** `type`/`bug` projiziert wird, **then** lautet der Namespace `type/bug` — durch Test gepinnt (IC-2; Default gemäß D-1201-A, Phase-F-Plan `:185` pinnt abweichend `bug` hinter Task-0b-Freigabe).
3. **Given** GitLab-Adapter mit `scoped-labels`, **when** projiziert wird, **then** lautet der Namespace `type::bug` — durch Test gepinnt (IC-2).
4. **Given** eine Legacy-Config, **when** gerendert wird, **then** erscheint genau eine benannte Warnung pro Preset, die Datei bleibt unverändert, und es erfolgt keine stille Umbenennung (IC-1, IC-4).
5. **Given** ein Separator mit `": "`, **when** der Resolver läuft, **then** `IssueConfigError`, Exit 2, kein Write und kein API-Call (IC-2, IC-3).
6. **Given** `issue-conventions.enabled: false`, **when** gerendert wird, **then** ist die Golden-Baseline **bewusst aktualisiert** — ausschließlich der Namespace-Token weicht vom Status quo ab (`": "`-Literal entfernt bzw. Token weggelassen, IC-1/IC-3), alle übrigen Bytes bleiben identisch; die Abweichung wird im Commit-Body/PR benannt (Phase-F-Plan Task 2 Step 2, `docs/superpowers/plans/2026-11-11-phase-f-label-taxonomy.md:186`; D-1201-B) (IC-1, IC-3, IC-4).
7. **Given** zwei `type`-Werte auf einem Issue, **when** GitLab-Scoping bzw. GitHub-Rollenkontract greift, **then** bleibt nur ein Type-Label bzw. die Aktion wird verweigert (per Capability-Flag, #1188 AC-7) (IC-2).

## Offene Fragen + Risiken

**Dependency-Status #1188 (re-geprüft 2026-11-23, REST):** Issue **OPEN**. Spec `docs/specs/2026-11-09-issue-label-taxonomy-spec.md` = **APPROVED**, Plan `docs/plans/2026-11-09-issue-label-taxonomy-plan.md` = **APPROVED** (Trace `SPEC-issue-label-taxonomy-2026-11-09`). Die Taxonomie ist damit **definiert** — kein "undefined-taxonomy"-Blocker. Der Code liegt noch nicht vor; die vollständige Projektion (IC-2) setzt die #1188-Auslieferung voraus, die Legacy-Warnung (IC-4) + Renderer-Guard (IC-3) sind unabhängig. Sequenzierung: #1188 vor #1201 (Folge-Issue F-1, `docs/plans/2026-11-09-config-wave-overview.md:217`).

- **D-1201-A (offen, Default = #1188 folgen):** Der #1188-Spec pinnt GitHub auf `/` → `type/bug` (`config/issue-adapters.yaml`, #1188 IC-3; Plan T7 `:513` `test_github_uses_slash`, F-1 `:1154`); der Issue-Text #1201 fordert flach `bug` (`separator: ""`). Zusätzlich pinnt der Phase-F-Plan GitHub `bug` als „Entscheidung 51" — aber **hinter die User-Freigabe der Referenzplan-Abweichung** gestellt (Task 0b `:118-124`, Task 2 `:181-186`: ohne Freigabe bleibt Task 2 gesperrt). Ein Developer, der diesem Plan folgt, würde ohne diese Freigabe das Gegenteil implementieren (flach `bug`). Diese Spec übernimmt bewusst den APPROVED-Vertrag `type/bug`, solange keine solche Freigabe vorliegt. Soll flach `bug` gewollt sein, ist das ein Projekt-Override — dann muss geprüft werden, ob die Ownership-/Prune-Logik von #1188 ohne Präfix noch trägt. Eskalation: User-Entscheidung (Task 0b); Default ist dokumentiert.
- **D-1201-B (offen, Default = Golden bewusst aktualisiert):** Verhalten bei `enabled: false` — die Golden-Baseline wird bewusst um den Namespace-Token aktualisiert (nur dieser Token weicht ab; IC-1/IC-3), wie vom Phase-F-Plan Task 2 Step 2 (`:186`) verlangt („Golden-Test bewusst anpassen und die Änderung im Commit-Body/PR benennen"). Das weicht von der Additiv-Klausel des #1188-Plans (`:243-245`, byte-identisch zu `aaed14c2`) bzw. #1188 AC-9 für genau diesen Token ab; der #1188-Kern bleibt unangetastet. Verworfene Alternative: Output unverändert + Warnung-only. Eskalation nur bei abweichendem User-Wunsch.
- **Risiko:** #1188-Resolver noch nicht auf Platte → IC-2 ist ein Vertragsbezug auf die APPROVED-Spec bzw. den APPROVED-Plan (Signatur Plan `:511`/`:924`), keine neue Implementierung. Developer darf keine konkurrierende Projektion anlegen.

**ADR (Entscheidung, adr.github.io-Form, kompakt):**
- *Kontext:* Namespace-String vermischt Inhalt und Projektion; #1188 definiert Separator pro Kardinalität als einzige Projektionsquelle.
- *Entscheidung:* #1201 ersetzt den Literal-String durch die #1188-Projektion (`type/bug` | `type::bug`) und warnt bei Legacy-Werten; kein eigener Resolver.
- *Konsequenzen:* Einmalige Warnung für bestehende Configs; GitHub-Labels sind `type/bug` statt `bug`; volle Wirkung erst nach #1188-Merge.

## Trace-Anker

spec-id: SPEC-1201-label-namespace
Upstream: `SPEC-issue-label-taxonomy-2026-11-09` (unverändert übernommen)
