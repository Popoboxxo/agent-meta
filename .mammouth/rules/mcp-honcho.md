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

Honcho bietet persistentes Cross-Session-Memory. Verwende diese Tools immer, wenn du Informationen über frühere Interaktionen, Architektur-Entscheidungen oder Nutzer-Präferenzen über Sessions hinweg benötigst oder speichern musst.
get_context: Wann nutzen? Um den aktuellen Sitzungskontext zu Beginn der Aufgabe zu laden. search: Wann nutzen? Bei Recherchen zu vergangenem Code oder historischen Entscheidungen. create_conclusion: Wann nutzen? Nach Abschluss eines komplexen Tasks, um Learnings für zukünftige Sessions dauerhaft zu speichern. list_conclusions: Wann nutzen? Um bestehende Learnings vor einer Implementierung abzurufen. chat: Wann nutzen? Für direkte Konversation mit dem Honcho-Backend bei Unklarheiten im Kontext. get_representation: Wann nutzen? Um auf personalisierte Nutzer-Einstellungen zuzugreifen.
Destruktive Tools (delete_conclusion, set_config) sind gesperrt.

## Verbindungstyp

- Typ: `sse`
- URL: `{{MCP_HONCHO_URL}}` — Wert aus `secrets.local.yaml`

---

*Generiert von agent-meta aus `config/mcp-registry.yaml` — nicht manuell bearbeiten.*
