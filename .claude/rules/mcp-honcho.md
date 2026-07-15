# MCP: honcho

> Honcho local memory and context server

---

## Erlaubte Tools

- `chat`
- `get_context`
- `get_representation`
- `search`
- `list_conclusions`
- `create_conclusion`

## Verbotene Tools (ABSOLUT — keine Ausnahmen)

- `delete_conclusion`
- `set_config`

## Agent-Hinweise

Honcho bietet persistentes Cross-Session-Memory.
get_context: aktuellen Sitzungskontext abrufen.
search: Wissensdatenbank und frühere Sessions durchsuchen.
create_conclusion: Erkenntnisse dauerhaft speichern.
list_conclusions: gespeicherte Erkenntnisse auflisten.
chat: direkte Interaktion mit dem Honcho-Speicher.
get_representation: personalisierte Nutzer-Darstellung abrufen.
Destruktive Tools (delete_conclusion, set_config) sind gesperrt.

## Verbindungstyp

- Typ: `sse`
- URL: `{{MCP_HONCHO_URL}}` — Wert aus `secrets.local.yaml`

---

*Generiert von agent-meta aus `config/mcp-registry.yaml` — nicht manuell bearbeiten.*
