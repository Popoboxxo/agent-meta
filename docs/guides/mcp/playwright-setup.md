# Playwright MCP — Setup

Der Playwright-MCP-Server stellt dem `e2e-tester` Browser-Tools bereit
(Navigation, Snapshot, Klicks, Screenshots, Netzwerk- und Konsolen-Inspektion).

## Aktivieren

In `.meta-config/project.yaml`:

```yaml
mcp-servers:
- playwright
```

Danach `python scripts/sync.py` ausführen. Der Sync trägt den Server in die
Provider-Configs ein (`.mcp.json` u.a.) und bindet die freigegebenen Tools als
`mcp__playwright__<tool>` ins Frontmatter von `.claude/agents/e2e-tester.md`.

> `playwright` hat `enabled-by-default: false` in `config/plugin-catalog.yaml` —
> ohne den expliziten Eintrag oben bleibt der Server inaktiv und der
> `e2e-tester` bekommt keine Browser-Tools.

## Browser installieren

```bash
npx playwright install chromium
```

Das genügt. Kein `sudo`, keine Systempakete.

**Warum Chromium und nicht Chrome:** `@playwright/mcp` startet per Default den
Channel `chrome`, der eine systemweit installierte Google-Chrome-Instanz unter
`/opt/google/chrome` erwartet. Ist sie nicht vorhanden, bricht der Browserstart
ab (`Chromium distribution 'chrome' is not found`), und `npx playwright install
chrome` ruft intern `sudo` für Systemabhängigkeiten auf — in CI-Runnern und
Sandboxes ohne Root schlägt das fehl. Die Registry setzt deshalb fest
`--browser chromium`; dieser Build wird von Playwright selbst mitgeliefert und
ohne Root installiert.

Siehe `config/plugin-catalog.yaml` → `playwright.connection.args`.

## Welche Rollen bekommen die Tools

Eine Rolle meldet sich in `config/role-defaults.yaml` an:

```yaml
roles:
  e2e-tester:
    mcp-servers:
    - playwright
```

Projektseitig überschreibbar in `.meta-config/project.yaml`:

```yaml
mcp-role-overrides:
  e2e-tester: []          # Tools für diese Rolle abschalten
  senior-developer:       # oder einer anderen Rolle geben
  - playwright
```

Es werden ausschließlich die Tools unter `tools.allowed` gebunden.
`tools.blocked` (u.a. `browser_evaluate`, `browser_run_code_unsafe`) landet
nie im Frontmatter.

## Troubleshooting

| Symptom | Ursache | Lösung |
|---|---|---|
| Agent meldet, Playwright-Tools seien nicht verfügbar | Server nicht in `mcp-servers`, oder Sync nach der Änderung nicht gelaufen | Eintrag ergänzen, `sync.py` ausführen, **IDE/CLI-Session neu starten** |
| `Chromium distribution 'chrome' is not found` | Alte Config ohne `--browser chromium` | `sync.py` neu ausführen und `.mcp.json` prüfen |
| `sudo: A password is required` | `npx playwright install chrome` statt `chromium` | `npx playwright install chromium` |
