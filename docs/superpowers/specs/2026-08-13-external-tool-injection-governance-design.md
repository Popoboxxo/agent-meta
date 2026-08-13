# External-Tool Injection Governance — Design

**Status:** Entwurf zur Freigabe
**Branch:** `feat/external-tools-registry`
**Kontext:** Erweiterung der in PR #490 gebauten External-Tools-Registry (`config/external-tools-registry.yaml`, `scripts/lib/external_tools.py`) um eine provider-agnostische, default-deny Whitelist für alles, was ein lokal installiertes Tool (graphify, künftig weitere) außer Rule-Content und kuratierten Hooks selbst auf die Platte schreibt — plus sichtbare Drift-Erkennung im geladenen Agent-Kontext.

## Ausgangslage

PR #490 kennt zwei Contribution-Arten pro Tool: `rule-content` (Markdown, von agent-meta gerendert) und `hooks` (agent-meta-eigene Wrapper aus `hooks/0-external/`, deployed via `sync_hooks()`). Beides ist voll kuratiert.

Was fehlt: Tools installieren oft **zusätzlich, eigenständig** Inhalte, die agent-meta nicht rendert — z.B. legte graphifys Installer live `.claude/skills/graphify/`, `.opencode/skills/graphify/` an und schrieb testweise direkt in `.claude/CLAUDE.md` / `.claude/settings.json` (Verstoß gegen die Hard-Invariant „CLAUDE.md wird nie manuell editiert", `conventions.md`). Dafür gibt es aktuell keinen Mechanismus — weder Erlaubnis noch Erkennung.

## Abgrenzung zu `orchestrator.native-extensions.whitelist`

Bereits existierend (`docs/superpowers/specs/2026-07-23-native-extensions-whitelist-design.md`, umgesetzt): eine Whitelist, die regelt, welche nativen Skills/Plugins der Orchestrator-Gate zur **Ausführung** passieren lässt (Verhaltensregel im geladenen Kontext, kein technisches Enforcement).

Diese Spec betrifft etwas anderes: nicht *darf ein Skill laufen*, sondern *darf ein Tool eine Datei/ein Verzeichnis an Ort X anlegen* — Installations-Governance, technisch geprüft (Verzeichnis-Scan bei jedem Sync), nicht nur Verhaltensregel. Beide Mechanismen bleiben getrennt, wie schon zwischen `skills-registry.yaml` und der Native-Extensions-Whitelist in der referenzierten Spec festgehalten.

## Schema: `permitted-injections`

Neues optionales Feld pro Tool-Eintrag in `config/external-tools-registry.yaml` (und im Projekt-Override `.meta-config/external-tools-registry.yaml`):

```yaml
external-tools:
  graphify:
    ...
    permitted-injections:
      - kind: skill              # skill | hook | rule | config | other
        name: graphify           # bei kind: skill/hook/rule
        description: "Claude-Code-Skill (SKILL.md + references), vom graphify-Installer selbst verwaltet"
      # - kind: config            # bei kind: config/other zwingend explizit:
      #   path: ".claude/settings.json"
      #   description: "..."
```

**Default-Deny:** Nur was hier deklariert ist, gilt als erlaubt. Alles andere, das im Scan (siehe unten) gefunden wird, ist Drift — unabhängig davon, wo es liegt (auch `.claude/agents/` oder `CLAUDE.md` selbst wären default-verboten, weil dafür niemand einen Eintrag hätte). Kein zusätzliches hartkodiertes Schutzsystem nötig.

JSON-Schema-Erweiterung (`config/project-config.schema.json`, `external-tools-registry.patternProperties.*.properties`):

```json
"permitted-injections": {
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "kind": { "type": "string", "enum": ["skill", "hook", "rule", "config", "other"] },
      "name": { "type": "string" },
      "path": { "type": "string" },
      "description": { "type": "string" }
    },
    "required": ["kind"],
    "additionalProperties": false
  }
}
```
Validierung in `external_tools.py` (nicht nur Schema): `kind` ∈ {skill, hook, rule} erfordert `name` (kein `path`); `kind` ∈ {config, other} erfordert `path` (kein `name`) — sonst `SyncError` in Phase 1, analog zu bestehenden Registry-Validierungen.

## Pfadauflösung

| `kind` | Auflösung |
|---|---|
| `skill` | `pc.get("skills_dir", ...)` (Provider-Config) `+ "/" + name` |
| `hook` | `pc.get("hooks_dir", ".claude/hooks")` `+ "/" + name` |
| `rule` | `pc.get("rules_dir", ".claude/rules")` `+ "/" + name` |
| `config` / `other` | `path` wörtlich, relativ zu `project_root` |

Eine Deklaration gilt für alle aktiven Provider (kein Wiederholen von `.claude/...`, `.opencode/...` etc. pro Plattform) — mit Ausnahme von `provider-skip` (bestehendes Feld), das weiterhin pro Tool greift.

## Drift-Erkennung

Neue Funktion `check_injection_drift(agent_meta_root, project_root, config, provider_config, log)` in `external_tools.py`, **einmal pro Sync-Lauf** aufgerufen (nach Generierung aller Provider), nicht pro Provider dupliziert.

**Scan-Scope — bewusst nicht nur die vier bekannten Unterordner:** Der ursprüngliche graphify-Vorfall (`.claude/CLAUDE.md`, `.claude/settings.json.graphify-bak`) lag als lose Datei direkt unter der Provider-Infrastruktur-Wurzel, nicht in `skills_dir`/`hooks_dir`/`rules_dir`/`agents_dir`. Der Scan läuft deshalb auf der **Provider-Infrastruktur-Wurzel selbst** (z.B. `.claude/`), Tiefe 1:

1. Für jeden aktiven Provider: liste alle Einträge direkt unter der Infrastruktur-Wurzel (Dateien und Verzeichnisse, Tiefe 1) — u.a. `skills_dir`, `hooks_dir`, `rules_dir`, `agents_dir` selbst als Verzeichnis-Einträge, plus lose Dateien wie `settings.json`.
2. Für die vier bekannten Managed-Unterordner zusätzlich eine Ebene tiefer: liste deren Inhalt (z.B. was liegt in `skills_dir`).
3. Erwartete Menge = (a) was `sync.py` in diesem Lauf selbst geschrieben/verwaltet hat (inkl. der vier bekannten Ordnernamen selbst, `settings.json`, `pending-tasks.md` u.ä. Fixliste bereits verwalteter Namen) + (b) aktive `external-skills`-Einträge (bestehende Registry) für Inhalte innerhalb `skills_dir` + (c) aufgelöste `permitted-injections` aller aktiven External-Tools (Ebene-1-Treffer bei `kind: config/other`, Ebene-2-Treffer innerhalb des jeweiligen Verzeichnisses bei `kind: skill/hook/rule`).
4. Differenz (gefunden, nicht erwartet) → Drift-Fund: `{path, provider, vermuteter kind, tool: <name>|null}`. `vermuteter kind` ergibt sich aus dem Verzeichnis, in dem der Fund liegt (`skills_dir` → `skill`, `hooks_dir` → `hook`, `rules_dir` → `rule`, sonst `other` — inkl. `agents_dir`, für das es bewusst **keinen** deklarierbaren `permitted-injections`-kind gibt: Funde dort sind immer Drift, außer explizit über `kind: config`/`path` freigegeben). `tool` ist gesetzt, wenn der Pfad unter einem Verzeichnis liegt, das ein *inaktives* oder *falsch konfiguriertes* Tool plausibel zuordnet (Name-Präfix-Match), sonst `null` (komplett unbekannt).
5. Nur **warnen** (`log.warning(...)`), kein Blocken, kein Löschen/Verschieben — auch nicht bei `--check` (Exit-Code bleibt unberührt).

## Sichtbarkeit im geladenen Kontext

Zwei Bausteine, beide sparsam (kein Overhead für unauffällige Projekte):

1. **Statische Whitelist** — `_generate_tool_rule_content()` bekommt einen neuen Abschnitt `## Erlaubte Injektionen`, nur wenn `permitted-injections` nicht leer ist. Eine Zeile pro Eintrag mit aufgelöstem, konkretem Pfad. Läuft in der bestehenden `.claude/rules/tool-<name>.md` mit, kein neuer Dateityp.
2. **Drift-Befund** — neue Datei `.claude/rules/external-tools-drift.md` (analog je Provider mit `has_rules`), **nur geschrieben, wenn `check_injection_drift` tatsächlich Funde liefert** — sauberes Projekt bekommt gar keine Datei. Eine Zeile pro Fund (Pfad + vermuteter `kind` + zugeordnetes Tool oder „keinem registrierten Tool zugeordnet"), gedeckelt auf 10 Einträge + `„… N weitere, siehe sync.log"`. Existiert die Datei aus einem Vorlauf noch, obwohl aktuell kein Drift mehr vorliegt → wird gelöscht (wie jede andere generierte Datei, die ihre Bedingung verliert).

## sync.py-Integrationspunkt

Aufruf von `check_injection_drift(...)` direkt nach der bestehenden Provider-Schleife, die `generate_external_tool_artifacts(...)` aufruft (`scripts/sync.py`, selbe Stelle wie der existierende `sync_agents_for_provider`-Block) — einmal global, nicht pro Provider-Iteration.

## Admin-UI

Erweiterung von `viewProjectExternalToolsOverrides()` (`docs/ui/admin-ui.html:2785`), im bestehenden Tool-Panel (`renderToolPanel`, analog zum vorhandenen Hooks-`tagEditor` bei Zeile 2925-2932):

- **Neu, `buildEdit`:** Editor für `permitted-injections` — Liste von Zeilen mit `kind`-Dropdown (skill/hook/rule/config/other), `name`-Feld (skill/hook/rule) bzw. `path`-Feld (config/other, per `kind`-Auswahl ein-/ausgeblendet), `description`-Feld, Add/Remove-Buttons. Kein neues generisches Array-Widget wie bei der Native-Extensions-Whitelist möglich (mehrfeldig statt reiner String-Liste) — eigene kleine Komponente, analog zum bestehenden `renderBadgeList`/`tagEditor`-Stil dieser Datei.
- **Neu, `buildReadonly`:** Rendert die aufgelösten `permitted-injections` als Badge-Liste (`kind: name/path`).
- **Neu, oberhalb der Tool-Liste:** Warnbanner „Erkannte Abweichungen", nur sichtbar wenn Drift vorliegt. Datenquelle: neuer Read-Endpoint `GET /api/external-tools/drift`, der `check_injection_drift(...)` im Dry-Run-Modus gegen den aktuellen Projektzustand ausführt (kein Schreibzugriff) und die Fundliste als JSON zurückgibt.
- Speichern über den bestehenden `PUT /api/config/project/section` (`section: "external-tools-registry"`) — `permitted-injections` ist einfach ein weiteres Feld im selben Objekt, kein neuer Endpoint für den Schreibpfad nötig.

## Fehlerbehandlung

- `permitted-injections`-Eintrag ohne `kind` → Schema-Validierung schlägt fehl, Sync stoppt vor Artefakt-Generierung.
- `kind: skill` mit `path` statt `name` (oder umgekehrt bei `config`) → `SyncError` mit klarer Meldung, welches Feld für diesen `kind` erwartet wird.
- Drift-Scan auf einem Provider-Verzeichnis, das nicht existiert (Projekt nutzt den Provider gar nicht) → übersprungen, kein Fehler.
- Tippfehler in `name`/`path` (Whitelist verfehlt den echten Pfad) → führt zu einem False-Positive-Drift-Fund, keine Sync-Fehlfunktion — Nutzerverantwortung, analog zur Fehlerbehandlung der Native-Extensions-Whitelist.

## Testing

- Unit: Pfadauflösung pro `kind` (alle 5 Varianten, inkl. Fehlerfall fehlendes Pflichtfeld).
- Unit: `check_injection_drift` — leer (nichts Unerwartetes), ein Fund einem Tool zugeordnet, ein Fund keinem Tool zuordenbar, Deckelung bei >10 Funden.
- Unit: Rendering `## Erlaubte Injektionen` (leer → kein Abschnitt; gefüllt → korrekte aufgelöste Pfade je Provider).
- Integration: `sync.py --dry-run` auf einem Testprojekt mit undeklariertem Fremd-Artefakt in `skills_dir` → `external-tools-drift.md` wird erzeugt, enthält den Pfad; nach Deklaration in `permitted-injections` → Datei verschwindet beim nächsten Lauf.
- Regression: bestehende `tests/test_external_tools_registry.py` bleibt grün (keine Verhaltensänderung ohne `permitted-injections`).

## Migration: graphify

`config/external-tools-registry.yaml` → `graphify` bekommt:
```yaml
permitted-injections:
  - kind: skill
    name: graphify
    description: "Claude-Code-Skill, vom graphify-Installer selbst verwaltet"
```
Erklärt `.claude/skills/graphify/` und `.opencode/skills/graphify/` (kein Drift mehr). `.claude/CLAUDE.md` (rohe graphify-Injektion) und `.claude/settings.json.graphify-bak` bleiben unerklärt und tauchen nach Umsetzung in `external-tools-drift.md` auf — ihre Bereinigung ist ein **separater, manueller Folgeschritt** (nicht Teil dieser Spec; das Feature soll sie sichtbar machen, nicht automatisch anfassen).

## Out of Scope

- Automatisches Entfernen/Verschieben von Drift-Funden (bewusst nur Warnen, siehe Erfolgskriterium-Entscheidung).
- Inhaltliche Drift-Prüfung *innerhalb* erlaubter Dateien (z.B. ob `.claude/skills/graphify/SKILL.md` sich seit Installation verändert hat) — nur Existenz/Ort wird geprüft, nicht Inhalt.
- Rückwirkende Bereinigung der graphify-Altlasten (`.claude/CLAUDE.md`, `settings.json.graphify-bak`) — wird durch die Drift-Datei sichtbar gemacht, aber hier nicht automatisiert entfernt.
- Honcho-Eintrag in der Registry — läuft über die bestehende MCP-Allow/Deny-Governance, kein zusätzlicher `external-tools`-Eintrag in dieser Iteration.
