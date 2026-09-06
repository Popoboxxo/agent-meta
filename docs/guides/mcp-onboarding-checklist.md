# MCP Onboarding-Checkliste

Ein registrierter MCP-Server ist nicht automatisch ein genutzter MCP-Server.
Diese Checkliste stellt sicher, dass aktivierte MCP-Tools für Agenten **sichtbar
und aktiv geroutet** werden — nicht nur technisch verfügbar sind (Issue #661).

## Das Problem: Signal-Hierarchie entscheidet, nicht Capability-Match

Ein frisch registrierter Server hat nur das schwächste Signal: generische
MCP-Server-Instruktionen. Konkurrierende Tools mit expliziter Verdrahtung dominieren
das Routing. Die effektive Signal-Hierarchie (beobachtetes Verhalten, Issue #661):

```
Hook (PreToolUse, immer geladen)
  > Lazy-Rule (Skill-Eintrag via use-lazy-rules.md)
    > Inline-Docs (Satz in CLAUDE.md/AGENTS.md)
      > generisches MCP (nur generische Server-Instruktionen)
```

In der Tool-Auswahl dominiert die Signal-Stärke, nicht die tatsächliche Eignung für
die Aufgabe. Ohne Verdrahtung wird ein neuer Server systematisch deprioritisiert,
bis jemand die Rule/den Hook ergänzt. Beispiel aus Issue #661 (ai-native-reqflow-POC):
`projectatlas` war korrekt registriert und verfügbar, wurde aber nie geroutet —
`graphify` dominierte alle Codebase-Fragen durch Hook + Skill-Eintrag + Inline-Doku.

Ohne die Schritte unten sind neue MCP-Plugins faktisch *dead on arrival* und
jedes Onboarding kostet dieselbe manuelle Arbeit erneut.

## SSOT: `config/plugin-catalog.yaml`

Registrierung und Aktivierung sind zwei getrennte Dinge:

1. **Registrieren:** Eintrag in `config/plugin-catalog.yaml` (`kind: mcp-server`;
   description, tools, connection, secrets) — dieses Katalog-File ist die Single
   Source of Truth. **Migrationshinweis:** Das frühere `config/mcp-registry.yaml`
   wurde in den Plugin-Katalog vereinigt und existiert nicht mehr; ältere Verweise
   (u. a. in generierten Dateien und historischen Dokumenten) sind als veraltet zu
   lesen.
2. **Aktivieren:** `mcp-servers: [...]` in `project.yaml` oder implizit via
   Platform-Bundle.

Grundlagen (Registry-Aktivierung, Secrets, Provider-Konfiguration):
[MCP Setup — Best Practices](mcp-setup.md).

## Die 3 Onboarding-Schritte

### Schritt 1 — Rule-Definition (PFLICHT)

sync.py generiert für jeden aktiven Server automatisch eine generische Rule
(`mcp-<server>.md`) aus dem Katalog-Eintrag — ohne kuratierte Trigger und ohne
Kontrast zu überlappenden Tools. Damit das Tool korrekt geroutet wird, braucht es
eine kuratierte Lazy-Rule an **zwei Stellen**:

**a) lazy-Preset-Eintrag in `config/rules-presets.yaml`** (der Mechanismus):

```yaml
# config/rules-presets.yaml → lazy:
mcp-<server>:
  channel: skill
  skill-description: "Use when <Trigger/Patterns> — <Kontrast zu überlappenden Tools>."
```

Der Eintrag braucht:
- **"Use when"**: explizite Trigger (Queries, File-Types, Agenten-Rollen)
- **Kontrast**: wie sich das Tool von überlappenden Tools unterscheidet
  (z. B. "projectatlas für Multi-Project-Traversal, graphify für
  Single-Codebase-Fragen")
- **Link**: zur SKILL.md bzw. den MCP-Server-Docs

Mit `channel: skill` rendert sync.py die Rule als
`.claude/skills/mcp-<server>/SKILL.md` (Namenskonvention) — nur `name` +
`description` landen im System-Prompt, der Body wird on-demand per `Read` geladen.
Der Skill-Kanal wirkt auf Claude und Opencode; alle anderen Provider behalten die
normale Rule-Datei in ihrem Rules-Verzeichnis.

**b) Tabellenzeile in `rules/1-generic/use-lazy-rules.md`** (die Quelle der
generierten `.claude/rules/use-lazy-rules.md`-Übersichtstabelle):

```markdown
| mcp-<server> | <Kurzer Trigger-Hinweis> |
```

Ohne Tabellenzeile bleibt der Skill für Agenten unsichtbar, auch wenn er
generiert wurde.

### Schritt 2 — CLAUDE.md/AGENTS.md-Referenz (BEDINGT)

Nur wenn das Tool für den **täglichen Workflow** relevant ist: ergänze einen Satz
im "wie man in diesem Repo arbeitet"-Abschnitt (Claude: `CLAUDE.md`, andere
Provider: `AGENTS.md`), der erklärt, wann man es dem konkurrierenden Tool
vorzieht. Kein ganzer Absatz — ein Satz reicht, der hierarchisch unter der
Lazy-Rule liegt.

### Schritt 3 — Hook-Registrierung (OPTIONAL)

Nur wenn das Tool **"always considered"** sein soll (Vorbild: graphify's
graph.json-Check): PreToolUse-Hook ergänzen (Hook-Skript unter `hooks/`,
registriert in `.claude/settings.json`). Die Entscheidung **explizit im
Rule-Eintrag markieren** (Kommentar in der `skill-description`), damit nachvollziehbar
bleibt, warum dieses Tool ein Hook-Signal bekommen hat.

## Mechanik (Vorschlag, noch nicht implementiert)

Issue #661 schlägt eine automatische Erkennung vor: `sync.py` oder ein eigenes
`bootstrap-mcp-rules.py` soll registrierte Server gegen die Rule-Einträge prüfen
und bei Fehlen mit einer Checkliste warnen oder blocken (konfigurierbar,
optional auto-stubbed mit TODOs).

**Aktueller Zustand:** Nicht implementiert. Ein `bootstrap-mcp-rules.py` existiert
bislang nicht, und `sync.py` prüft keine Rule-Coverage für MCP-Server. Bis dahin
gilt diese Checkliste als **manueller Prozess**.

## Checkliste (abhaken)

| Schritt | Was | Verbindlichkeit | Erledigt |
|---|---|---|---|
| 1a | lazy-Preset-Eintrag in `config/rules-presets.yaml` (`channel: skill`, "Use when", Kontrast, Link) | Pflicht | ☐ |
| 1b | Tabellenzeile in `rules/1-generic/use-lazy-rules.md` | Pflicht | ☐ |
| 2 | Ein Satz in `CLAUDE.md`/`AGENTS.md` (nur bei Daily-Workflow-Relevanz) | Bedingt | ☐ |
| 3 | PreToolUse-Hook + explizite Markierung im Rule-Eintrag | Optional | ☐ |

## Referenzen

- [MCP Setup — Best Practices](mcp-setup.md) — Registry-Aktivierung, Secrets, Provider-Konfiguration
- [Playwright MCP Setup](mcp/playwright-setup.md)
- [Honcho MCP Setup](mcp/honcho-setup.md)
- [ReqogniLoom MCP Setup](mcp/reqogniloom-setup.md)
- `config/plugin-catalog.yaml` — SSOT für MCP-Server-Registrierung
- `config/rules-presets.yaml` — lazy-Preset (Mechanismus hinter `.claude/rules/use-lazy-rules.md`)
