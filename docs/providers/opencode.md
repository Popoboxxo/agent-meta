# opencode — Provider-Dokumentation

> Stand: agent-meta v2.0.0-beta.2 | Quelle: [sst/opencode](https://github.com/sst/opencode)

---

## Was ist opencode?

Terminal-basierter AI-Coding-Agent von SST (Open Source, MIT).
Vergleichbar mit Claude Code: interaktiver Chat im Terminal, Datei-Operationen, Shell-Integration,
75+ AI-Provider via AI SDK.

Kontext-Datei: **`AGENTS.md`** (analog zu `CLAUDE.md`). Wird via `/init` generiert und ins Git committed.
Unterstützt Legacy: opencode liest auch `CLAUDE.md` direkt — bestehende Projekte bekommen
den Kontext automatisch, ohne explizite opencode-Konfiguration.

---

## Verzeichnis- und Dateistruktur

```
AGENTS.md                  ← Projekt-Kontext + eingebettete Regeln (analog zu CLAUDE.md)
opencode.json              ← Projekt-Konfiguration (JSON; die einzige verwaltete Settings-Datei)
cli.json                   ← CLI-Konfiguration (nur v2 und nur bei gesetzter `cli`-Option)
.opencode/
  agents/                  ← Sub-Agenten (von agent-meta generiert)
    developer.md
    orchestrator.md
    ...
  commands/                ← Slash-Commands als .md-Dateien (von agent-meta generiert)
    doc-now.md             → /doc-now
  plugins/                 ← Gate-Plugin (nur v2); wird ohne Config-Eintrag geladen
  mcp.local.json           ← lokale MCP-Secrets (gitignored, Ersetzungs-Semantik)
  settings.local.json      ← lokale, gitignored Overrides (einmalig angelegt, nie überschrieben)
  agent-meta-state.json    ← Managed-State (Namespaces, kein User-Eigentum)

~/.config/opencode/
  opencode.json            ← User-Level-Konfiguration
  AGENTS.md                ← Globaler Kontext (alle Projekte)
  agents/                  ← User-eigene Agenten
  commands/                ← User-eigene Commands
```

---

## Surface v1 vs. v2

Opencode kennt zwei Konfigurations-Oberflächen. **v1 ist der Default und bleibt byte-stabil**;
v2 ist opt-in und wird über den bestehenden Schalter `surface-version` gewählt. Die Auswahl ist
reine Konfigurationsdaten: agent-meta löst daraus den Frontmatter-Mechanismus und das
MCP-Format auf und verzweigt nie auf einen Provider-Namen.

| Aspekt | v1 (Default) | v2 (opt-in) |
|---|---|---|
| `surface-version` | `v1` | `v2` |
| aufgelöster Frontmatter-Mechanismus | `opencode-native` | `opencode-native-v2` |
| Plugin-Key in `opencode.json` | `plugin` | `plugins` (Plural); Dateien unter `.opencode/plugins/` werden zusätzlich ohne Config-Eintrag geladen |
| Subagent-Tiefe | Top-Level `subagent_depth` (der v2-Parser verwirft den Key) | `experimental.subagent_depth` |
| Agent-Permissions | `permission`-Map | `permissions[]`-Liste aus `{action, resource, effect}` |
| MCP-Server | flaches `mcp` mit `enabled: true` | `mcp.servers`; **kein** `enabled`, optional `disabled`, `timeout`, `oauth` (DOKU) |
| MCP-Managed-Pfade | keine (der `mcp`-Block wird ersetzt) | je Server `mcp.servers.<name>`; fremde Einträge bleiben erhalten |
| `cli.json` | wird nicht erzeugt | nur bei gesetzter `cli`-Option; Top-Level-Keys werden durchgereicht |
| Runtime-Tier (strict) | `permission` | `plugin` (Artefakt nur `observe`) **plus** `permissions[]`-Deny |

**Feldevidenz (Spike C0):** `timeout` (`startup`/`catalog`/`execution`, Millisekunden), `oauth`
(snake_case) und `disabled` sind **DOKU**-belegt, nicht in dieser Umgebung verifiziert.
`system` (Body statt Frontmatter-Feld) und `variant` (`#variant`) sind **VERIFIED**.

---

## Aktivierung

Der Schalter existiert bereits und wird wiederverwendet — es gibt **keinen neuen Key und keinen
Alias**. In `.meta-config/project.yaml`:

```yaml
provider-options:
  Opencode:
    surface-version: v2
```

Ohne diesen Eintrag bleibt `v1` aktiv; das ist der Registry-Default. Die Optionen wirken nur auf
v2. Steht eine v2-Option in einem v1-Projekt, schreibt agent-meta nichts und meldet
`opencode-v2-option-ignored: <key> requires surface-version v2`.

v2-Optionen unter `provider-options.Opencode`:

| Key | Wirkung |
|---|---|
| `experimental-subagent-depth` | schreibt `experimental.subagent_depth`; Default ist `required_depth` aus den Provider-Capabilities |
| `experimental-todo` | schreibt `experimental.todo`; ohne Key wird nichts geschrieben |
| `providers` | Objekt, je Provider-ID als `providers.<id>` durchgereicht (Innenform `settings.baseURL` + `env`) |
| `model-variants` | Rolle → Variante; wird als `#variant` an die Modell-ID gehängt |
| `cli` | Inhalt von `cli.json` (Passthrough); ohne Key wird die Datei nicht erzeugt |

`experimental.subagent_depth`, `experimental.todo` und der Key `providers` sind laut Spike Q6
**DOKU**-belegt (nicht in dieser Umgebung nachgemessen).

`providers` ist Passthrough: agent-meta interpretiert die Innenform nicht und validiert sie nicht
gegen ein v2-Schema. Werte unter Schlüsseln mit `key`/`secret`/`token` im Namen müssen
`{env:VAR}` sein, sonst bricht der Sync ab (auch im dry-run als Finding).

---

## Managed Keys und User-Keys

agent-meta besitzt in `opencode.json` nur die folgenden Pfade:

- `experimental.subagent_depth` — Projekt-Option, sonst Capability-Tiefe
- `experimental.todo` — nur wenn die Projekt-Option gesetzt ist
- `providers.<id>` — je konfigurierter Provider-ID als ganzes Objekt
- `permissions[]` — nur die Gate-Tripel, und nur solange das Gate effektiv aktiv ist
- `permission.edit/bash["**"]` — der v1-Gate-Deny; auf v2 übernimmt `permissions[]`
- `mcp.servers.<name>` — nur Server-Namen aus dem aktiven Katalog
- `default_agent` — nur auf Tier `permission` (v1 und v2 vor C3)

`cli.json` wird je Top-Level-Key des `cli`-Objekts verwaltet. Alles andere bleibt unangetastet:
`plugin`/`plugins`, `instructions`, `model`, `$schema`, `theme`, fremde `mcp`-Server und
User-Einträge in `permissions[]` überleben einen Sync unverändert.

**State und Rollback.** agent-meta merkt sich je verwaltetem Pfad `{value, prior, prior_absent}`
in `.opencode/agent-meta-state.json`, getrennt in den Namespaces `opencode-v2-keys`,
`opencode-v2-permissions`, `opencode-v2-cli` und `opencode-v2-mcp` (dazu die weiteren
Namespaces `isolation-deny`, `default-agent` und `runtime-gate-deny`). Beim Wechsel v2 → v1
stellt der Rollback den `prior` wieder her oder entfernt den Key samt leerem Eltern-Container;
ein vom User geänderter Wert bleibt stehen und erzeugt eine WARNING
(`opencode-v2-managed: <pfad> user value kept`). Ein unverfolgter User-Wert, der dem Zielwert
bereits entspricht, wird still übernommen und beim Rollback nicht entfernt. Ein Parse-Fehler
der Datei führt zu keinem Schreibzugriff.

**Reihenfolge in `permissions[]`.** Die Auswertung ist „last match wins“ (Spike Q3, VERIFIED).
Ein Managed-`deny` am Listenanfang wäre damit die schwächste Position und würde von jeder
späteren Regel überstimmt. agent-meta hängt seine Gate-Tripel deshalb **ans Listenende** an;
User-Einträge und ihre relative Reihenfolge werden nie verändert. Der Rollback identifiziert die
Tripel über ihren exakten Wert, nicht über einen Listenindex, und ist damit positionsunabhängig.

---

## Dateien

- **`opencode.json`** ist die einzige reguläre Projekt-Settings-Datei; eine `.jsonc`-Variante
  gibt es nicht. agent-meta schreibt ausschließlich `opencode.json`. Liegt daneben eine
  `opencode.jsonc`, meldet der Consistency-Check `opencode-config-duplicate` (WARNING); eine
  inhaltstragende JSONC-Datei würde die verwaltete JSON-Datei teilweise überschreiben.
- **`cli.json`** entsteht nur auf v2 und nur, wenn `provider-options.Opencode.cli` gesetzt ist.
  Datei, Name und JSON-Format sind **DOKU**-belegt; dokumentiert ist nur der Top-Level-Key
  `plugins`. `theme` und `autoupdate` sind **nicht dokumentiert** und werden hier nicht als
  unterstützt dargestellt. Der Writer reicht die vom User gesetzten Top-Level-Keys generisch
  durch.
- **`tui.json`** wird von agent-meta weder erzeugt noch verändert noch gelöscht.
- **`.opencode/mcp.local.json`** ist die gitignored Secrets-Datei. Sie behält ihre
  Ersetzungs-Semantik: der Inhalt wird pro Sync neu geschrieben, manuelle Einträge darin gehen
  verloren (R-14).
- **`.opencode/settings.local.json`** wird einmalig als gitignored Skeleton angelegt und danach
  nie überschrieben; sie ist keine verwaltete Settings-Datei.
- **`.opencode/agent-meta-state.json`** gehört agent-meta. Jeder Writer schreibt nur seinen
  eigenen Namespace.

---

## Feature-Vergleich mit Claude Code

| Feature | Claude Code | opencode |
|---------|------------|---------|
| Kontext-Datei | `CLAUDE.md` | `AGENTS.md` (liest auch `CLAUDE.md`) |
| Config-Verzeichnis | `.claude/` | `.opencode/` |
| Sub-Agenten | `.claude/agents/*.md` | `.opencode/agents/*.md` |
| Rules (auto-load) | `.claude/rules/` | **Nicht vorhanden** — in `AGENTS.md` eingebettet |
| Slash-Commands | `.claude/commands/*.md` | `.opencode/commands/*.md` (gleiches Format) |
| Hooks / Plugins | `.claude/hooks/*.sh` + `settings.json` | v1: Plugin-Factory (`server()`-Form) mit `tool.execute.before`; v2: Default-Export-Objekt mit `setup(ctx)` und `ctx.tool.hook(...)` |
| Gate-Durchsetzung | PreToolUse-Hook blockiert den Tool-Call | v2: Plugin nur `observe`; das Gate trägt der `permissions[]`-Deny |
| Frontmatter: `description` | `description:` | `description:` |
| Frontmatter: `mode` | — | `mode: primary \| subagent \| all` |
| Frontmatter: `model` | `model: claude-sonnet-4-6` | `model: provider/model[#variant]` |
| Frontmatter: `permission` | `permissionMode:` | v1: `permission:`-Map |
| Frontmatter: `permissions` | — | v2: Liste aus `{action, resource, effect}` |
| Frontmatter: `memory` | `memory:` | **Nicht unterstützt** |

---

## Sub-Agenten in opencode

Markdown-Dateien in `.opencode/agents/` — Dateiname = Agent-ID.

**agent-meta schreibt natives opencode-Frontmatter (v1):**

```yaml
---
description: "Feature-Implementierung und Bugfixes..."
mode: subagent
model: opencode-go/deepseek-v4.1-flash
generated-from: "1-generic/developer.md@2.1.0"
permission:
  edit: allow
  bash: allow
---
# developer
...
```

**Auf v2 wird daraus eine geschlossene `permissions[]`-Liste:**

```yaml
---
description: "Feature-Implementierung und Bugfixes..."
mode: subagent
model: opencode-go/deepseek-v4.1-flash#high
generated-from: "1-generic/developer.md@2.1.0"
permissions:
  - {action: edit, resource: "*", effect: allow}
  - {action: shell, resource: "*", effect: allow}
  - {action: subagent, resource: "*", effect: allow}
---
# developer
...
```

Die v2-Liste ist **closed-world**: für jede der Aktionen `edit`, `shell`, `subagent` steht genau
ein Eintrag — `allow` bei gemapptem Tool, sonst `deny`. Eine read-only Rolle erbt dadurch keine
Schreibrechte. Der globale Gate-Tripel in `opencode.json` nutzt `resource: "**"` und wird ans
Listenende angehängt; die Agent-Ebene nutzt `resource: "*"`.

`mode: subagent` ist Standard für alle agent-meta Agenten — sie werden explizit delegiert,
nicht als Haupt-Agent gestartet. Die `primary-role` (orchestrator) erhält `mode: primary` und
wird als `default_agent` eingetragen.

---

## Kontextdatei und Rules

**AGENTS.md-only:** `AGENTS.md` ist die einzige von agent-meta verwaltete Kontextdatei für
Opencode; agent-meta erzeugt weder `CLAUDE.md` noch `OPENCODE.md`. Der managed block in
`AGENTS.md` wird bei jedem Sync aktualisiert und enthält die agent hints sowie alle aktiven
Rules.

opencode besitzt kein eigenes Rule-Verzeichnis. Agent-meta generiert deshalb:

- Keine separaten Rule-Dateien für opencode
- `has_rules: false` in `config/ai-providers.yaml`
- Alle aktiven Rules im managed block von `AGENTS.md`
- Die Speech-Mode-Rule wird ebenfalls eingebettet (wenn konfiguriert)

**Rule überspringen:** `opencode: skip` in `config/rules-presets.yaml` oder project.yaml:

```yaml
rules:
  lifecycle-tasks:
    opencode: skip
```

---

## Slash-Commands

opencode Commands sind `.md`-Dateien — **gleiches Format wie Claude Code**:
- Gleiches `$ARGUMENTS` für Argumente
- Gleiche `description:` + Body-Struktur
- Kein Transformationsschritt nötig

opencode scannt `.opencode/commands/` automatisch — kein Eintrag in `opencode.json` nötig.

Optionale Frontmatter-Felder für opencode Commands:

```yaml
---
description: Update CODEBASE_OVERVIEW.md immediately
agent: documenter    # opencode wählt diesen Agenten automatisch
model: opencode-go/deepseek-v4.1-flash
subtask: true        # erzwingt Subagent-Ausführung
---
```

---

## Model-Tiers

opencode Model-IDs folgen dem AI-SDK-Format. Auf v2 gilt zusätzlich
`provider/model[#variant]`; die Variante kommt aus `model-variants`.

| Tier | Modell-ID |
|------|-----------|
| `nano` | `opencode-go/deepseek-v4.1-flash` |
| `fast` | `opencode-go/deepseek-v4.1-flash` |
| `balanced` | `opencode-go/deepseek-v4.1-flash` |
| `powerful` | `opencode-go/deepseek-v4.1-flash` |
| `max` | `opencode-go/deepseek-v4-pro` |

opencode unterstützt 75+ Provider — Tier-Mapping auf andere Provider via `model-overrides`
in `project.yaml`:

```yaml
model-overrides:
  Opencode:
    developer: openai/gpt-4o
    git: google/gemini-2.5-flash
```

---

## agent-meta Konfiguration

### Opencode aktivieren

```yaml
# .meta-config/project.yaml
ai-providers:
  - Opencode
```

Oder zusammen mit anderen Providern:

```yaml
ai-providers:
  - Claude
  - Opencode
```

### Was wird generiert?

| Artefakt | Verhalten |
|----------|-----------|
| `.opencode/agents/*.md` | Überschrieben bei jedem sync, stale gelöscht |
| `AGENTS.md` (managed block) | Aktualisiert bei jedem sync (agent hints + eingebettete rules) |
| `AGENTS.md` (Rest) | Einmalig angelegt, dann manuell gepflegt |
| `opencode.json` | Einmalig als Skeleton angelegt; danach verwalteter Merge (v2-Pfade oben, dazu `default_agent` auf Tier `permission`) |
| `cli.json` | Nur v2 mit gesetzter `cli`-Option; verwalteter Merge je Top-Level-Key |
| `.opencode/commands/*.md` | Aus `commands/` kopiert, stale gelöscht |
| `.opencode/plugins/agent-meta-runtime-gate.js` | Nur v2 (Tier `plugin`), immer `MODE=observe` |
| `.opencode/mcp.local.json` | Pro Sync neu geschrieben (Ersetzungs-Semantik) |
| `.opencode/agent-meta-state.json` | Namespaced Managed-State |
| Rules | In `AGENTS.md` eingebettet (kein eigenes Verzeichnis) |

---

## Bekannte Grenzen

1. **Kein Rules-System** — Regeln nur über `AGENTS.md` einbindbar; agent-meta bettet sie ein
2. **Kein persistentes Agenten-Gedächtnis** — `memory:`-Feld wird entfernt
3. **Kein `permissionMode`-Feld** — Berechtigungen laufen über `permission` (v1) bzw.
   `permissions[]` (v2)
4. **JSONC-Kommentare (R-4)** — eine `opencode.json` mit Kommentaren verliert diese beim
   Rückschreiben, weil agent-meta lenient liest und reines JSON schreibt. Ein Parse-Fehler
   schreibt nichts.
5. **`.opencode/mcp.local.json` (R-14)** — Ersetzungs-Semantik; manuelle Einträge in der
   gitignored Secrets-Datei gehen bei jedem Sync verloren.
6. **v1-MCP-Writer (R-15)** — der eingefrorene v1-Pfad ersetzt den flachen `mcp`-Block
   vollständig; bei aktiven Servern gehen eigene `mcp`-Einträge verloren. Der Migrationspfad ist
   v2 mit verwalteten Pfaden je Server.
7. **`default_agent` auf Tier `plugin` (Amendment B4)** — auf v2 läuft der Managed-Merge für
   `default_agent` nicht mehr (die Spec-A-Aufrufbedingung ist Tier `permission`). `settings-init`
   schreibt den Wert einmalig; ein später gelöschter Wert wird nicht wieder ergänzt und ein
   abweichender User-Wert erzeugt keine Warnung. Der Schutz liegt auf der Agent-Ebene und in den
   `permissions[]`-Tripeln.
8. **Plugin ist observe-only** — das v2-Gate-Plugin protokolliert nur; es blockiert keine
   Tool-Calls. Die Durchsetzung trägt weiterhin der Permission-Deny. `MODE=enforce` bleibt bis
   zum bestandenen P6-Test gesperrt.
9. **Legacy-Kompatibilität** — opencode liest auch `CLAUDE.md`; agent-meta erzeugt für Opencode
   dennoch ausschließlich `AGENTS.md`.
