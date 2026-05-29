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

## MCP-Server (Framework-Feature)

MCP-Server werden zentral in `config/mcp-registry.yaml` verwaltet und per Projekt aktiviert.
sync.py generiert daraus Rule-Dateien, Provider-Configs und Gitignore-Einträge automatisch.

### Aktivierung

```yaml
# .meta-config/project.yaml
mcp-servers:
  - home-assistant   # explizit → immer aktiv
  - influxdb         # explizit → immer aktiv

# Oder implizit über Plattform-Bundle:
# rules/2-platform/<platform>-mcp.yaml
# (nur wenn enabled-by-default: true in mcp-registry.yaml)
```

### Generierte Artefakte (pro aktivem Server + Provider)

Rule-Dateien und Provider-Configs werden für jeden aktiven Provider separat generiert:

| Provider | Rule-Datei | Committed Config | Lokale Config (gitignored) |
|---|---|---|---|
| Claude | `.claude/rules/mcp-<server>.md` | `.claude/settings.json` → `mcpServers` | `.claude/settings.local.json` → `mcpServers` |
| Gemini | `.gemini/rules/mcp-<server>.md` | `.gemini/settings.json` → `mcpServers` | `.gemini/settings.local.json` → `mcpServers` |
| Opencode | *(kein rules-dir)* | `opencode.json` → `mcp` | `.opencode/mcp.local.json` |
| Continue | `.continue/rules/mcp-<server>.md` | `.continue/config.yaml` → `mcpServers` | `.continue/config.local.yaml` → `mcpServers` |

Zusätzlich (provider-übergreifend): `.meta-config/secrets.local.yaml` — Secrets-Template, via `--init` generiert, immer gitignored.

### Secrets

```bash
# 1. Template anlegen (einmalig bei --init oder manuell):
cp .agent-meta/howto/configs/mcp-secrets.local-template.yaml .meta-config/secrets.local.yaml
# 2. Werte eintragen, dann sync ausführen:
py .agent-meta/scripts/sync.py
```

`.meta-config/secrets.local.yaml` ist immer gitignored. Nie committen.

### Neuen MCP-Server hinzufügen

1. Eintrag in `config/mcp-registry.yaml` (description, tools, agent-hint, connection, secrets)
2. Optional: Plattform-Bundle `rules/2-platform/<platform>-mcp.yaml` anpassen
3. `sync.py` ausführen — alles wird automatisch generiert

### Security

`write_checked()` scannt alle generierten Dateien auf Secrets. Bei committed Dateien:
- **Secrets gefunden** → `SyncError` (Sync abbrechend) — nie in VCS committen
- **`allow-committed-secrets: true`** in `project.yaml` → nur Warnung (nicht empfohlen)
- **Lokale/gitignored Dateien** → nur Warnung (korrekt, Secrets gehören dorthin)

Details: [howto/mcp-setup.md](howto/mcp-setup.md)

---

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

## Provider-Isolation (Framework-Feature)

Wenn mehrere AI-Provider in einem Projekt aktiv sind, generiert `sync.py` automatisch Hard-Blocks die verhindern dass ein Provider die Verzeichnisse eines anderen liest oder schreibt.

### Aktivierung

Automatisch aktiv wenn `>1 Provider` in `ai-providers` konfiguriert ist. Keine explizite Aktivierung nötig.

### Deaktivieren (Opt-out)

```yaml
# .meta-config/project.yaml
provider-isolation: disabled
```

Sinnvoll für das agent-meta Meta-Repository selbst, das alle Provider-Verzeichnisse verwalten muss.

### Generierte Artefakte pro Provider

| Provider | Mechanismus | Datei |
|---|---|---|
| Claude | `permissions.deny` (Glob) | `.claude/settings.json` |
| Opencode | `permission.read/edit` deny (Glob) | `opencode.json` |
| Gemini | TOML-Policy-Rules (Regex) | `.gemini/policies/provider-isolation.toml` |
| Continue | Soft-Rule (kein nativer Hard-Block in IDE-Extensions) | `.continue/rules/provider-isolation.md` |

---

<!-- agent-meta:managed-begin -->
<!-- This block is automatically updated by sync.py on every sync. -->
<!-- Manual changes here will be overwritten. -->

Generiert von agent-meta v0.55.2 — `2026-05-29`
DoD-Preset: **rapid-prototyping** | REQ-Traceability: false | Tests: false | Codebase-Overview: false | Security-Audit: false

> **Einstiegspunkt:** Starte mit dem `orchestrator`-Agenten für alle Entwicklungsaufgaben — Ausnahmen siehe Abschnitt »Orchestrator — Universal Router«.

| Agent | Zuständigkeit |
|-------|--------------|
| `agent-meta-manager` | agent-meta verwalten: Upgrade, Sync, Feedback, projektspezifische Agenten anlegen |
| `agent-meta-scout` | KI-Ökosystem scouten: neue Skills, Rollen, Rules und Patterns für agent-meta entdecken |
| `api-specialist` | Verwende diesen Agenten fuer API-Design, OpenAPI-Spezifikationen und Contract-First Development. |
| `bug-feature-analyzer` | Issue-Triage: Bug vs. User-Error vs. Feature vs. Out-of-Scope klassifizieren — vor developer/feature-Delegation |
| `claude-expert` | Claude Code Experte: Funktionsweise, .claude Konfiguration, Best Practices |
| `code-reviewer` | Prüft Code-Qualität, Blast-Radius und Clean Code — nicht funktionale Korrektheit (das macht validator). |
| `continue-expert` | Continue Experte: Funktionsweise, .continue Konfiguration, Best Practices |
| `copilot-expert` | GitHub Copilot Experte: Funktionsweise, .github/copilot Konfiguration, Best Practices |
| `developer` | Feature-Implementierung und Bugfixes im agent-meta Framework (Python, Markdown, YAML) |
| `devops-engineer` | Verwende diesen Agenten fuer CI/CD, IaC, Kubernetes, Monitoring und Infrastructure-Aufgaben. |
| `documenter` | Doku pflegen: CODEBASE_OVERVIEW, ARCHITECTURE, README, Erkenntnisse |
| `export-manager` | Verwende diesen Agenten fuer Export-Routing von strukturierten Daten zu konfigurierten Targets. |
| `feature` | Feature-Lifecycle-Subagent: Branch → REQ → TDD → Dev → Validate → PR. Wird vom Orchestrator gestartet, nicht direkt vom User. |
| `feedback` | Projekt-Feedback: Bugs, Features, Verbesserungen als GitHub Issues standardisiert einreichen — immer vor git |
| `gemini-expert` | Gemini Experte: Funktionsweise, .gemini Konfiguration, Best Practices |
| `git` | Commits, Branches, Tags, Push/Pull und alle Git-Operationen |
| `ideation` | Neue Ideen explorieren, Vision schärfen, Übergabe an requirements |
| `log-analyzer` | Log-Analyse: Fehler clustern, Severity klassifizieren (RFC 5424), Findings als Issues oder Tasks delegieren |
| `meta-feedback` | Verbesserungsvorschläge für agent-meta als GitHub Issues einreichen |
| `opencode-expert` | Opencode Experte: Funktionsweise, .opencode Konfiguration, Best Practices |
| `orchestrator` | Einstiegspunkt für ALLE Entwicklungsaufgaben — zerlegt komplexe Tasks und dispatched parallel |
| `performance-optimizer` | Verwende diesen Agenten fuer Performance-Analyse, Big-O-Optimierung und Bottleneck-Beseitigung. |
| `release` | Versioning, Changelog, Build-Artifact, GitHub Release erstellen |
| `requirements` | Anforderungen aufnehmen, REQ-IDs vergeben, REQUIREMENTS.md pflegen |
| `se-architect` | Use this agent to design L1 and L2 architectures from requirements. |
| `se-critic` | Use this agent to validate requirements before architecture, and audit architectural decompositions. |
| `se-integration-and-test-manager` | Orchestriert den gesamten rechten Flügel der V&V-Kaskade — Bottom-Up, Top-Down, Integrationsplanung. |
| `se-interface-mgr` | Manages generic signal flow, deterministic sync across systems |
| `se-orchestrator` | Coordinates the 6-level recursive breakdown |
| `se-requirements` | Use this agent to clarify requirements and start the SE cascade. |
| `se-termination` | Deterministic termination at L3 (Component Requirement) |
| `se-test-engineer` | Use this agent to create model-based test models and integration test strategies from architectural decompositions. |
| `se-testreviewer` | Use this agent to review and audit test models and integration test strategies before execution. |
| `se-validator` | Validiert das System auf L1-Ebene durch User-Journey-Simulation — ignoriert Code, prüft ob der User-Need erfüllt ist. |
| `se-verifier` | Use this agent to verify integrated systems against their specifications on all architecture levels (L1 through Ln). |
| `ui-ux-designer` | UI-Spezifikation, Mockup-Erstellung und Design-System-Definition — implementiert nicht, spezifiziert. |
<!-- agent-meta:managed-end -->
