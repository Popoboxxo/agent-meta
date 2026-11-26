# Neuen MCP-Server registrieren und routbar machen

Diese Howto beschreibt den vollständigen Weg vom Katalog-Eintrag bis zum
grünen Checklisten-Test. SSOT ist `config/plugin-catalog.yaml`; generierte
Dateien unter `.claude/skills/` und `.claude/rules/mcp-*` werden **nie**
manuell bearbeitet.

## Kurz-Checkliste

| Schritt | Was | Ort |
|---|---|---|
| 1 | Server registrieren | `config/plugin-catalog.yaml` |
| 2 | Server aktivieren | `.meta-config/project.yaml` (`plugins:`) oder Platform-Bundle |
| 3 | Lazy-Rule anlegen | `config/rules-presets.yaml` → `lazy` |
| 4 | Pointer-Tabelle ergänzen | `rules/1-generic/use-lazy-rules.md` |
| 5 | Guardrail prüfen | automatisch aus `tools.blocked` |
| 6 | Validieren | `sync.py --validate` + Checklisten-Test |

## 1. Registrieren (SSOT)

Eintrag unter `plugins:` in `config/plugin-catalog.yaml`:

```yaml
plugins:
  my-server:
    kind: mcp-server            # oder: cli-tool
    origin-type: local-process  # remote-saas | local-process | repo-owned-process | local-binary
    availability-probe: npx-resolve
    description: Was der Server liefert (Englisch, ein Satz)
    category: database
    enabled-by-default: false
    tools:
      allowed: [query]
      blocked: [write]          # steuert Guardrail + permissions.deny
    agent-hint: |
      query: Wann nutzen? Kurzer Trigger.
      write: VERBOTEN.
    connection:
      type: sse                 # sse | stdio
      url: '{{MCP_MY_URL}}'
      headers:
        Authorization: 'Bearer {{MCP_MY_TOKEN}}'
    secrets:
      - MCP_MY_URL
      - MCP_MY_TOKEN
```

Regeln:

- Jeder `{{VAR}}`-Platzhalter aus `connection` muss unter `secrets:` stehen.
- Keine Klartext-Credentials — nur Env-Referenzen (`{{VAR}}` / `${VAR}`).
- `tools.blocked` ist die einzige Quelle für Verbote; die Prosa in
  `rules/1-generic/mcp-guardrails.md` und `permissions.deny` werden daraus
  generiert.
- CLI-Tools (`kind: cli-tool`) erzeugen den Stem `tool-<name>` statt
  `mcp-<name>` (Beispiel: `graphify` → `tool-graphify`).

## 2. Aktivieren

Bevorzugt über den einheitlichen `plugins:`-Block:

```yaml
# .meta-config/project.yaml
plugins:
  my-server:
    enabled: true
```

Alternativ implizit über ein Platform-Bundle
(`rules/2-platform/<platform>-mcp.yaml`) — dort greift
`enabled-by-default: true`. Ein explizites `enabled: false` gewinnt immer.

## 3. Lazy-Rule / Skill anlegen

`sync.py` generiert für jeden aktiven Server automatisch `mcp-<name>.md`.
Ohne kuratierte Lazy-Rule ist der Server für Agenten aber praktisch unsichtbar
(Signal-Hierarchie: Hook > Lazy-Rule > Inline-Docs > generisches MCP).

Eintrag im `lazy`-Preset (`config/rules-presets.yaml`), Key = generierter Stem:

```yaml
presets:
  lazy:
    mcp-my-server:
      channel: skill
      skill-description: "Use when <Trigger> — <Kontrast zum überlappenden Tool>; details in `config/plugin-catalog.yaml`."
```

Pflichtbestandteile der Description (Englisch, eine Zeile):

- **Use when** — expliziter Trigger,
- **Kontrast** — Abgrenzung zum überlappenden Tool,
- **Link** — `config/plugin-catalog.yaml`.

`channel: skill` rendert die Rule als
`<skills_dir>/mcp-my-server/SKILL.md`; nur `name` + `description` landen im
System-Prompt, der Body wird on demand geladen. Andere Provider behalten die
normale Rule-Datei.

## 4. Pointer-Tabelle ergänzen

Zeile in `rules/1-generic/use-lazy-rules.md`:

```markdown
| mcp-my-server | Kurzer Trigger-Hinweis |
```

Ohne Tabellenzeile bleibt der generierte Skill für Agenten unsichtbar.

## 5. Guardrail

Nichts manuell eintragen: Hat der Server `tools.blocked`, erscheint er
automatisch

- als Bullet in `rules/1-generic/mcp-guardrails.md`
  (`{{MCP_GUARDRAILS_LIST}}`), und
- als `mcp__<server>__<tool>` in der Deny-Liste des Providers
  (`permissions.deny` bzw. Hook-Manifest).

Leere `blocked`-Liste → kein Eintrag.

## 6. Validieren

```bash
python3 scripts/sync.py --validate
python3 -m pytest tests/test_mcp_server_checklist.py -q
```

`--validate` prüft unter anderem MCP-URLs und Secret-Referenzen (#1262):
ungültiges URL-Schema oder Klartext-Credential → exit 1 mit Servername;
ungesetzte Env-Variable → Warnung, kein Fehler.

Der Checklisten-Test (`tests/test_mcp_server_checklist.py`) parametrisiert
über **alle** Katalog-Server und prüft:

- Katalog-Eintrag vollständig (description, category, origin-type,
  connection/tools, deklarierte Secrets),
- `lazy`-Preset-Eintrag mit `channel: skill`, „Use when", Kontrast und Link,
- Tabellenzeile in `use-lazy-rules.md`,
- tatsächlich gerenderte `<skills_dir>/<stem>/SKILL.md` (Temp-Sync, keine
  handgepflegten ignored Dateien),
- Guardrail-Bullet bei gesetzter `blocked`-Liste,
- #1262-Validierung ohne ERROR.

Ein neuer Katalog-Eintrag ohne diese Verdrahtung lässt den Test **mit dem
Servernamen** rot werden — das ist die gewünschte Absicherung.

## Nicht-Ziele

- Keine manuellen Edits an `.claude/skills/**`, `.claude/rules/mcp-*` oder
  anderen generierten Provider-Dateien.
- Kein `if provider == "..."` im Syncer; Routing ausschließlich über
  Config-Keys/Capabilities.

## Siehe auch

- [MCP Setup — Best Practices](../guides/mcp-setup.md)
- [MCP Onboarding-Checkliste](../guides/mcp-onboarding-checklist.md)
- `config/plugin-catalog.yaml` — Registrierung (SSOT)
- `config/rules-presets.yaml` — Lazy-Preset (Mechanik)
