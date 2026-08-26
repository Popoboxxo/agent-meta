# MCP: playwright

> Playwright MCP Server for browser automation and E2E tests

---

## Erlaubte Tools

- `browser_navigate`
- `browser_navigate_back`
- `browser_snapshot`
- `browser_take_screenshot`
- `browser_click`
- `browser_type`
- `browser_hover`
- `browser_select_option`
- `browser_press_key`
- `browser_fill_form`
- `browser_wait_for`
- `browser_resize`
- `browser_tabs`
- `browser_network_requests`
- `browser_network_request`
- `browser_console_messages`

## Verbotene Tools (ABSOLUT — keine Ausnahmen)

- `browser_run_code_unsafe`
- `browser_evaluate`
- `browser_file_upload`
- `browser_handle_dialog`

## Agent-Hinweise

Browser-Automation für E2E-Flows, visuelle Regression und Accessibility-Audits.
browser_navigate: zur Ziel-URL navigieren.
browser_snapshot: Accessibility-Baum der Seite erfassen (Basis für a11y-Audit und stabile Selektoren).
browser_click/browser_type/browser_fill_form: User-Interaktionen im Flow simulieren.
browser_take_screenshot: visuelle Regression via Screenshot-Vergleich.
browser_network_requests/browser_console_messages: Netzwerk und Konsole inspizieren.
Arbiträre Code-Ausführung (browser_run_code_unsafe, browser_evaluate) ist gesperrt.

## Verbindungstyp

- Typ: `stdio`
- Kommando: `npx @playwright/mcp@latest --browser chromium`

---

*Generiert von agent-meta aus `config/mcp-registry.yaml` — nicht manuell bearbeiten.*
