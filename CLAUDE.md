# agent-meta — Meta-Repository für Agenten-Standards

## Kernprinzipien

1. **`CLAUDE.md` ist die einzige Wahrheit** — beschreibt das Projekt vollständig.
2. **`.claude/agents/` ist generierter Output** — nie manuell bearbeiten, nur via `sync.py`.
3. **Agenten haben generische Namen** — `developer.md`, kein `vwf-developer.md`.
4. **Projektspezifische Erweiterungen** → `.claude/3-project/<rolle>-ext.md`.

## Schichten-Modell

```
0-external/  Externe Skill-Agenten (Git Submodule). Höchste Priorität.
1-generic/   Universell. Immer generiert sofern kein Override existiert.
2-platform/  Plattformspezifisch. Überschreibt 1-generic für eine Plattform.
             Modi: Full-replacement (kein extends:) | Composition (extends: + patches:)
3-project/   Projektspezifisch.
             <rolle>.md     → Override (ersetzt generierten Agent komplett)
             <rolle>-ext.md → Extension (additiv, nie von sync.py berührt)
```

Override-Reihenfolge: `1-generic → 2-platform → 3-project → 0-external`

## Sync

```bash
py scripts/sync.py                        # Standard-Sync
py scripts/sync.py --init                 # Ersteinrichtung
py scripts/sync.py --dry-run              # Was würde sich ändern?
py scripts/sync.py --create-ext developer # Extension anlegen
py scripts/sync.py --update-ext           # Extension managed blocks aktualisieren
py scripts/sync.py --create-rule <thema>  # Projekt-eigene Rule anlegen
```

Vollständige Referenz: [howto/sync-concept.md](howto/sync-concept.md)

## Wenn du etwas änderst

| Was geändert | Was prüfen |
|---|---|
| `1-generic/<rolle>.md` | `version:` erhöhen + Projekte syncen |
| `2-platform/<platform>-<rolle>.md` | `version:` und `based-on:` aktuell? + syncen |
| `config/role-defaults.yaml` (neue Rolle) | Agenten-Tabelle unten + `howto/setup/instantiate-project.md` |
| `hint:` in Agent-Template | Projekte syncen (AGENT_HINTS neu generiert) |
| `config/skills-registry.yaml` | Betroffene Projekte syncen |

Entscheidungsbaum für Änderungen:
- **Einfacher Wert** → Variable in `.meta-config/project.yaml`
- **Projektwissen** → `.claude/3-project/<rolle>-ext.md`
- **Plattformwissen** → `2-platform/<plattform>-<rolle>.md` mit `extends:` + `patches:`
- **Neue Rolle** → `1-generic/<rolle>.md` + `config/role-defaults.yaml`
- **Neuer Skill** → `sync.py --add-skill <url> ...`

Details: [howto/agent-composition.md](howto/agent-composition.md) | [howto/external-skills.md](howto/external-skills.md)

## Release (agent-meta selbst)

Semver: Patch = Bugfix/Doku | Minor = neue Features/Rollen | Major = Breaking Changes

```
1. version: in geänderten Agent-Frontmattern erhöhen
2. CHANGELOG.md aktualisieren
3. VERSION + README.md auf neue Version setzen
4. git commit -m "chore: bump version to x.y.z"
5. git tag vx.y.z && git push origin main vx.y.z
```

Details: [howto/upgrade-guide.md](howto/upgrade-guide.md)

## MCP Tools: code-review-graph

**Immer zuerst graph tools nutzen — schneller und token-effizienter als Grep/Glob/Read.**

| Tool | Wann |
|------|------|
| `detect_changes` | Code-Review — gibt risk-scored Analyse |
| `get_impact_radius` | Blast-Radius einer Änderung verstehen |
| `query_graph` | Caller, Callees, Imports, Tests tracen |
| `semantic_search_nodes` | Funktionen/Klassen nach Name/Keyword finden |
| `get_architecture_overview` | High-Level-Struktur verstehen |

Nur auf Grep/Glob/Read zurückfallen wenn der Graph nicht ausreicht.

---

<!-- agent-meta:managed-begin -->
<!-- This block is automatically updated by sync.py on every sync. -->
<!-- Manual changes here will be overwritten. -->

Generiert von agent-meta v0.28.1 — `2026-04-25`
DoD-Preset: **rapid-prototyping** | REQ-Traceability: false | Tests: false | Codebase-Overview: false | Security-Audit: false

> **Einstiegspunkt:** Starte mit dem `orchestrator`-Agenten für alle Entwicklungsaufgaben.

| Agent | Zuständigkeit |
|-------|--------------|
| `agent-meta-manager` | agent-meta verwalten: Upgrade, Sync, Feedback, projektspezifische Agenten anlegen |
| `agent-meta-scout` | Claude-Ökosystem scouten: neue Skills, Rollen, Rules und Patterns für agent-meta entdecken |
| `developer` | Feature-Implementierung und Bugfixes im agent-meta Framework (Python, Markdown, YAML) |
| `documenter` | Doku pflegen: CODEBASE_OVERVIEW, ARCHITECTURE, README, Erkenntnisse |
| `feature` | Neues Feature end-to-end durchführen: Branch → REQ → TDD → Dev → Validate → PR |
| `git` | Commits, Branches, Tags, Push/Pull und alle Git-Operationen |
| `ideation` | Neue Ideen explorieren, Vision schärfen, Übergabe an requirements |
| `meta-feedback` | Verbesserungsvorschläge für agent-meta als GitHub Issues einreichen |
| `orchestrator` | Einstiegspunkt für alle Entwicklungsaufgaben — koordiniert alle anderen Agenten |
| `release` | Versioning, Changelog, Build-Artifact, GitHub Release erstellen |
| `requirements` | Anforderungen aufnehmen, REQ-IDs vergeben, REQUIREMENTS.md pflegen |
<!-- agent-meta:managed-end -->
