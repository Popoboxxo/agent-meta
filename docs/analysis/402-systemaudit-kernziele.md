# Systemaudit: Kernziele (Issue #402)

**Branch:** `main`
**Datum:** 2026-08-06
**Scope:** Kernziel-Erfüllung des Meta-Repositorys über 5 Dimensionen — Standardisierung/Wiederverwendung
der Agenten-Rollen, Pipeline-Engine (`quality_pipelines`), Provider-Agnostizismus, Governance-/Sicherheits-Hooks,
Dokumentations-Konsistenz.
**Artefakt (Dashboard-Ansicht):** https://claude.ai/code/artifact/e5cfda44-899f-4ec4-adcc-4b23dd7c1f1a
**Issues:** #402–#415, Label `audit-2026-08`

---

## Zusammenfassung

Auslöser war die `feature-lifecycle-migration` (PR #401, 2026-08-06): beim abschließenden Regressionslauf
wurden zwei Config-Drift-Bugs live gefunden und gefixt (stale Pipeline-Override, stale Rollen-Eintrag in
`.meta-config/project.yaml`). Das warf die Frage auf, ob dieses Muster — Refactoring aktualisiert Code und
Primär-Doku, aber nicht Config/Sekundär-Doku/verwaiste Provider-Outputs — noch öfter im System steckt.
Antwort: ja, an mehreren Stellen, mit derselben Grundursache.

**Durchgehendes Muster:** Fehler beim Generieren werden in `build_variables()`
(`scripts/lib/config.py`) an mehreren Stellen mit `except Exception: pass` still verschluckt statt gemeldet.
Genau dieses Muster wurde bereits in Issue #276 (**Framework Architecture & Robustness Audit**, 2026-06-15,
CLOSED) für den Pipeline-Block explizit benannt und mit derselben Empfehlung versehen wie hier in #402 —
der Fix wurde damals offenbar nicht umgesetzt, der Code an `config.py:764-765` ist strukturell unverändert.
Das ist der stärkste Einzelbefund dieses Audits: eine seit sechs Wochen bekannte, aber nicht behobene
Fehlerklasse hat heute tatsächlich eine Regression verursacht.

Baseline zum Audit-Zeitpunkt: `consistency-check.py` PASS, `sync.py --validate` PASS (nach den PR-#401-Fixes),
`pytest -q --ignore=external` 293 passed / 4 failed (3 branch-unabhängig, 1 bekannter Vorbestand).

---

## Kernziele im Überblick

| Dimension | Verdikt |
|---|---|
| Standardisierung & Wiederverwendung (0-external → 3-project) | Teilweise erfüllt |
| Pipeline-Engine (quality_pipelines) | Funktional, aber fragil |
| Provider-Agnostizismus & Konsistenz | Gefährdet |
| Governance & Sicherheits-Hooks | Nur Soft-Enforcement |
| Dokumentations-Konsistenz | Wiederkehrender Drift |

---

## Kritische Befunde

### #402 — Silent exception handling verschluckt Pipeline-Config-Fehler in `build_variables()`

**Dateien:** `scripts/lib/config.py:374-375, 597-598, 716-726, 764-765`

Vier `except Exception: pass`-Blöcke fangen Fehler beim Laden von Pipeline-/Reflection-/SE-Variablen ab,
ohne sie zu loggen oder in die bestehende `unmapped`-Warnings-Liste einzureihen. **Bereits in Issue #276
(2026-06-15) für denselben Codepfad identifiziert und mit derselben Empfehlung versehen — nie gefixt.**
Genau dieser Block hat am 2026-08-06 den Crash aus #403 verschluckt und `PIPELINE_MATCH_TABLE` silent leer
gelassen. Fix: Exception in die vorhandene `unmapped`-Liste einreihen statt `pass`.

### #403 — `validate_pipelines()` prüft `stages`-Struktur nicht, crasht statt sauberem Error

**Dateien:** `scripts/lib/pipelines.py:150, 169`

Kein Typ-Check auf `isinstance(stages, list)` vor der Iteration — ein Dict (z.B. aus einem fehlerhaften
Override-Fragment) crasht mit `AttributeError` statt eines Validierungsfehlers. Fix: expliziter Typ-Check
mit sprechender Fehlermeldung vor der Loop.

### #404 — `orchestrator-guard.sh`: Soft-Identity und Git-Mutation-Parser haben dokumentationsbedürftige Lücken

**Dateien:** `.claude/hooks/orchestrator-guard.sh:18-30, 141-197`

Die Agenten-Identität basiert auf einer Selbstdeklaration (`#agent-meta:agent=git`), im Code selbst als
"not a security boundary" dokumentiert. Der Git-Mutation-Parser erkennt `eval "git commit ..."` oder
direkte `.git/`-Schreibzugriffe nicht. Kein Bug (bewusster Trade-off), aber die Grenzen fehlen in den
nutzerseitigen Governance-Regeln (`a2a-delegation-gates.md`, `branch-guard.md`).

### #405 — A2A `max_depth`/Self-Handoff-Guard nirgends technisch aufgerufen

**Dateien:** `scripts/lib/delegation_syntax.py:157-205`

`validate_envelope(max_depth=10)` ist implementiert, wird aber im aktiven Delegationspfad nie aufgerufen.
Die Regel "Tiefe max 10, kein Self-Handoff" (`a2a-delegation-gates.md`) ist reine Prompt-Instruktion ohne
technische Durchsetzung.

### #406 — `orchestrator.strict` nur auf 2 von 6 Providern durchsetzbar, nicht nutzerseitig dokumentiert

**Dateien:** `config/ai-providers.yaml:8,254`, `scripts/lib/consistency/orchestrator_strict.py`

Nur Claude und Mammouth haben `has_hooks: true` — auf Gemini, Opencode, Continue, Copilot ist
`orchestrator.strict` ein stiller No-op. Nur im Docstring des Consistency-Checks dokumentiert, nicht in
README/CLAUDE.md.

---

## Wichtige Befunde

### #407 — Verwaiste Provider-Outputs `.continue/`, `.mammouth/`, `.github/`

Existieren mit Inhalt, sind aber nicht in der aktiven `ai-providers:`-Liste (`.meta-config/project.yaml:3-6`
listet nur Claude/Opencode/Gemini). `.continue/prompts/orchestrator.md:26` ist seit 2026-07-27 nicht mehr
resynct und zeigt noch den alten Pipeline-Namen `standard-feature`.

### #408 — README.md/quality-pipelines.md referenzieren noch gelöschte Rolle `feature` / alte Pipeline `standard-feature` — ✅ erledigt (verifiziert 2026-08-08)

**Dateien:** `README.md:128,333,674-677`, `docs/guides/quality-pipelines.md:24,33`,
`snippets/orchestrator/quality-pipelines.md:4`

Aus dem `feature-lifecycle-migration`-Sweep (PR #401) herausgefallen, da diese Dateien nicht in dessen
Datei-Liste standen. Keine Treffer für `standard-feature` mehr in den genannten Dateien — behoben in einem
späteren Sweep.

### #409 — `tests/test_pipelines.py`: keine Negativtests, 6 von 7 Pipelines ungetestet

Nur `feature-lifecycle` wird namentlich validiert. `quick-fix`, `bugfix`, `concept-development`, `refactor`,
`docs-update`, `se-cascade` laufen ungetestet mit.

### #410 — Config-Schema-Warnungen bei `model-overrides.knowledge-*.Gemini` (Dict statt String)

7 Warnungen bei `sync.py --audit-config` — unklar, ob Schema oder Config-Struktur die korrekte Absicht ist.

### #411 — Composition-Mechanismus (`extends`+`patches`) in `agents/2-platform/` nirgends real genutzt

Alle 13 Platform-Overrides sind Full-Replacement. Der dokumentierte Composition-Pfad läuft im
Produktivbetrieb nie durch.

---

## Kleinere Befunde

- **#412** — Frontmatter-Naming uneinheitlich: `template-<rolle>` vs. `se-<rolle>`.
- **#413** — Audit-Trail (viz-logger) konfiguriert, aber `viz.enabled: false`.
- **#414** — Doppelte Konzept-Dateien in `docs/concepts/active/` und `planned/` (3 Themen).
- **#415** — `provider-expert` löst bei jedem `--audit-config`-Lauf einen erwarteten Fehlalarm aus.

---

## Korrekturen an Sub-Agent-Befunden

Zwei Behauptungen aus den parallelen Recherche-Agenten wurden vor Aufnahme widerlegt:

- **„.claude/agents/orchestrator.md fehlt — Sync-Bug"** → falsch. Beabsichtigt: Claude läuft für dieses
  Projekt im main-chat-Modus (`orchestrator.provider-overrides.Claude.mode: main-chat`, Commit `4ce74626`).
- **„.continue/, .mammouth/, .github/ existieren nicht"** → falsch. Sie existieren, sind aber verwaist
  (siehe #407).

---

## Methodik

| Check | Ergebnis |
|---|---|
| `python scripts/consistency-check.py` | PASS — keine Findings |
| `python scripts/sync.py --validate` | PASS nach den PR-#401-Fixes |
| `python scripts/sync.py --audit-config` | 1 erwarteter Hinweis (#415), 7 Schema-Warnungen (#410) |
| `pytest -q --ignore=external` | 293 passed, 4 failed (3 branch-unabhängig, 1 bekannter Vorbestand) |
| 5 parallele Recherche-Agenten | 2 Behauptungen korrigiert (siehe oben) |
