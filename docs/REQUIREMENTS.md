# Anforderungen — agent-meta

> Einzige Quelle der Wahrheit für alle Anforderungen des agent-meta Frameworks.
> Format: `REQ-xxx` (dreistellig) oder thematisch präfixiert (z.B. `REQ-CMD-xx`).
> Einmal vergebene IDs dürfen nie geändert oder wiederverwendet werden.

---

## Commands-System

| ID | Anforderung | Priorität |
|----|-------------|-----------|
| REQ-CMD-01 | sync.py verwaltet Commands über ein Vier-Schichten-Modell mit den Verzeichnissen `commands/0-external/`, `commands/1-generic/` und `commands/2-platform/`. Layer-Priorität (höchste gewinnt): 2-platform überschreibt 1-generic, 0-external liefert eigenständige Commands. Bei 2-platform gilt Naming-Konvention: `<platform>-<name>.md` → Output `<name>.md`. | Must |
| REQ-CMD-02 | sync.py kopiert bei jedem normalen Sync alle aktiven Commands nach `.claude/commands/`. Dabei werden `{{VAR}}`-Platzhalter analog zu Rules substituiert. Veraltete Dateien werden über Stale-Tracking via `.claude/commands/.agent-meta-managed` erkannt und entfernt. Der Sync findet nur statt wenn `"Claude"` in den konfigurierten `ai-providers` des Projekts enthalten ist. | Must |
| REQ-CMD-03 | sync.py kopiert bei jedem normalen Sync alle aktiven Commands nach `.continue/prompts/`. Continue-Frontmatter-Felder `name` und `description` werden unverändert übernommen. Fehlt `invokable: true` im Frontmatter, fügt sync.py es automatisch hinzu. Stale-Tracking via `.continue/prompts/.agent-meta-managed`. Der Sync findet nur statt wenn `"Continue"` in den konfigurierten `ai-providers` des Projekts enthalten ist. | Must |
| REQ-CMD-04 | Die Logik für das Commands-System wird in einem neuen Modul `scripts/lib/commands.py` implementiert. Das Modul enthält mindestens `collect_command_sources()` und `sync_commands_for_provider()`. Es ist analog zu `scripts/lib/rules.py` aufgebaut und darf maximal 600 Zeilen umfassen. | Must |
| REQ-CMD-05 | Commands benötigen keine Enable/Disable-Konfiguration in `.meta-config/project.yaml`. Sie werden automatisch kopiert, sobald der zugehörige Provider (Claude oder Continue) im Projekt aktiv ist. Es ist kein Eintrag in `.claude/settings.json` erforderlich. | Must |
| REQ-CMD-06 | Claude-Commands übernehmen die Frontmatter-Felder `description`, `allowed-tools` und `argument-hint` unverändert aus der Quelldatei. Continue-Commands übernehmen `name` und `description` unverändert; sync.py ergänzt `invokable: true` automatisch, falls das Feld fehlt. Kein anderes Frontmatter-Feld wird von sync.py verändert oder entfernt. | Must |
| REQ-CMD-07 | Das Repository enthält einen generischen Claude-Slash-Command `commands/1-generic/doc-now.md`. Der Command `/doc-now` delegiert an den `documenter`-Agenten und veranlasst diesen, `CODEBASE_OVERVIEW.md` sofort zu aktualisieren. Der Command akzeptiert ein optionales `$ARGUMENTS`-Token, mit dem der Nutzer den zu dokumentierenden Bereich eingrenzen kann. | Should |
| REQ-CMD-08 | `sync.py --create-command <name>` legt eine projektspezifische Command-Datei unter `.claude/commands/<name>.md` an. Die so erstellte Datei wird von sync.py bei späteren Syncs nie überschrieben oder gelöscht. Das Verhalten ist analog zu `--create-rule <name>`. | Should |
| REQ-CMD-09 | Das Commands-System ist vollständig dokumentiert in `howto/commands.md` (Schichten-Modell, Sync-Verhalten, Frontmatter-Felder, Anleitung zum Anlegen eines projektspezifischen Commands). Zusätzlich werden `CLAUDE.md` (Verzeichnisstruktur, Sync-Verhalten-Tabelle) und `howto/instantiate-project.md` (Verweis auf Commands) aktualisiert. | Should |

---

## Agent-Generierung

| ID | Anforderung | Priorität |
|----|-------------|-----------|
| REQ-GEN-01 | Agent-Templates mit `deprecated: true` im YAML-Frontmatter werden von sync.py aus der Generierung ausgeschlossen — sie erzeugen keine Agent-Datei und erscheinen nicht in CLAUDE.md-Tabelle/-Hints oder Visualisierung. Die Filterung erfolgt zentral in `collect_sources()` nach Auflösung der Layer-Override-Kette (1-generic < 2-platform < 3-project), sodass ein nicht-deprecated Override ein deprecated Basis-Template ersetzen kann. Fehlt das Feld oder ist es nicht explizit `true`, gilt das Template als aktiv (rückwärtskompatibler Default). | Must |

---

## SE-Pipeline-Erweiterung — Teilresultat-Protokoll & Rollentrennung

> Quelle: `docs/concepts/se-pipeline-extension.md`

### Lösung A — Teilresultat-Protokoll (Persistence)

| ID | Anforderung | Priorität |
|----|-------------|-----------|
| REQ-SE-01 | Jeder SE-Agent persistiert nach Abschluss seines Schrittes seinen strukturierten Output atomar (write-to-tmp + rename) in die definierte Datei innerhalb `docs/se/<projektname>/`. Das Frontmatter jeder Output-Datei enthält `step`, `agent`, `iteration`, `status`, `timestamp`, `schema_version`. | Must |
| REQ-SE-02 | Iterations-Suffix-Konvention: `*.iter-1.md`, `*.iter-2.md`, ... `*.iter-N.md` für Zwischenstände, `*.final.md` für die vom Critic approved finale Version. Single-Shot-Schritte (Requirements, Interfaces, Termination) ohne Iteration erhalten kein Suffix. | Must |
| REQ-SE-03 | Eine `.se-state.yaml`-Datei dient als Wiederaufnahme-Pointer mit `last_completed_step`, `next_expected_step` und `budget_consumed`. Eine neue Session liest diesen Pointer, identifiziert den letzten abgeschlossenen Schritt und setzt dort auf. | Must |
| REQ-SE-04 | Die `.se-state.yaml` wird atomar geschrieben (write-to-tmp + rename). Beim Lesen wird Schema-Validation durchgeführt; bei Korruption wird auf Verzeichnis-Inspektion als Fallback zurückgefallen. | Should |
| REQ-SE-05 | Die `output_parent_path`- und `FolderName`-Felder im A2A-Envelope-Payload legen den Zielpfad für die Persistenz fest. Die Verzeichnisstruktur folgt: `{SE_BASE_DIR}/{parent_path}/L{level}/{FolderName}/`. | Must |

### Lösung B — Rollentrennung Requirements vs. Architect

| ID | Anforderung | Priorität |
|----|-------------|-----------|
| REQ-SE-10 | Der `se-requirements`-Agent DARF KEINE Architektur-Pattern, Technologien, Deployment-Topologien, interne Schnittstellen oder Protokolle festlegen. Stattdessen signalisiert er Architekturbedarf via `arch_impact: true`-Flag mit `arch_trigger`-Beschreibung. | Must |
| REQ-SE-11 | Das JSON-Output-Schema von `se-requirements` wird um die Felder `arch_impact` (bool, default false), `arch_trigger` (string, nur bei arch_impact=true), `acceptance_criteria` (string[]) und `scope` (enum: system/component/both) erweitert. | Must |
| REQ-SE-12 | Der `se-critic` erhält einen zusätzlichen Prüfschritt "Role Boundary Check" bei `review_target: "requirements"`. Dieser prüft auf verbotene Architektur-Begriffe und lehnt Requirements mit Rollenverstoß ab (status: rejected, correction_hint zur Reformulierung). | Must |
| REQ-SE-13 | Der `se-architect` empfängt mit der Black-Box-Anforderung die Liste aller `arch_impact: true`-Triggers und muss in seinem `architectural_rationale` explizit auf jeden eingehen. | Must |

### Lösung C — Pipeline-Trennung (optional)

| ID | Anforderung | Priorität |
|----|-------------|-----------|
| REQ-SE-20 | Der Orchestrator klassifiziert eingehende SE-Aufträge basierend auf `scope` (system/component/both) und `arch_impact`-Flag in Pipeline A (System-Level, vollständiger Decomposition-Stack) oder Pipeline B (Component-Level, nur Developer + Reviewer + Validator). Default: `scope: system`. | Should |
| REQ-SE-21 | Pipeline A durchläuft: se-requirements → se-critic(req) → se-architect → se-critic(arch) → se-interface-mgr → se-termination. Endpunkt ist entweder leaf (Dispatch zu Pipeline B) oder continue (Spawn L+1). | Should |
| REQ-SE-22 | Pipeline B durchläuft: se-requirements(refinement) → se-developer-tier → se-code-reviewer → se-validator + se-verifier. Kein se-architect, kein se-interface-mgr, kein se-termination. Endpunkt ist V&V-Floor. | Should |
