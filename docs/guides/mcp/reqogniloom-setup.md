# ReqogniLoom MCP Setup

ReqogniLoom ist eine selbst gehostete Requirements-Engineering-Plattform (Anforderungen, Architektur, Tests, Traceability, ADRs, Risiken, Issues, Glossar, KI-gestützte Ableitungen). Dieser Leitfaden zeigt, wie der `reqogniloom` MCP-Server, der in der Registry von agent-meta (`config/plugin-catalog.yaml`) enthalten ist, aktiviert wird.

> ReqogniLoom ist standardmäßig **nicht** aktiviert (`enabled-by-default: false`). Die Aktivierung ist eine bewusste, projektspezifische Entscheidung (Opt-in).

## 1. ReqogniLoom lokal ausführen

Starten Sie eine lokale, selbst gehostete ReqogniLoom-Instanz (Backend + MCP-Server). Konsultieren Sie die Projektdokumentation von ReqogniLoom für aktuelle Setup- und Ausführungsanweisungen.

Standardmäßig lauscht ein lokales ReqogniLoom-Backend auf `http://localhost:8000` (passen Sie dies an Ihr Setup an). Der MCP-Endpunkt wird über SSE bereitgestellt unter:

```
{ReqogniLoom Basis-URL}/mcp/sse/
```

## 2. API-Schlüssel erstellen und Secrets konfigurieren

Der MCP-Server von ReqogniLoom authentifiziert sich über einen API-Schlüssel, der im `X-API-Key`-Header gesendet wird. Schlüssel müssen mit dem Präfix `rf_` beginnen — jedes andere Format (einschließlich JWT-Bearer-Tokens) wird mit `AUTH_FAILED` abgelehnt. Generieren Sie einen Schlüssel für den Workspace, den Sie bereitstellen möchten, über die ReqogniLoom Admin-UI oder die REST-API.

Fügen Sie die Werte zu Ihrer lokalen Secrets-Datei hinzu (diese wird niemals eingecheckt — sie ist in der `.gitignore` enthalten):

```yaml
# .meta-config/secrets.local.yaml
MCP_REQOGNILOOM_URL: "http://localhost:8000"
MCP_REQOGNILOOM_API_KEY: "rf_xxxxxxxxxxxxxxxx"
```

Alternativ können Sie diese als Umgebungsvariablen in Ihrer Shell exportieren, bevor Sie den Provider starten:

```bash
export MCP_REQOGNILOOM_URL="http://localhost:8000"
export MCP_REQOGNILOOM_API_KEY="rf_xxxxxxxxxxxxxxxx"
```

Die eingecheckten Provider-Konfigurationen referenzieren die Variablen (`${MCP_REQOGNILOOM_URL}` / `{env:MCP_REQOGNILOOM_URL}`, selbes Muster für den API-Schlüssel) — die tatsächlichen Werte bleiben lokal.

## 3. Aktivierung in `project.yaml`

Fügen Sie `reqogniloom` zur expliziten Serverliste hinzu:

```yaml
# .meta-config/project.yaml
mcp-servers:
  - reqogniloom
```

Oder über den Slash-Befehl (sofern unterstützt): `/add-mcp-server reqogniloom`

## 4. sync.py ausführen

```bash
python .agent-meta/scripts/sync.py
```

`sync.py` generiert:

- Die Regeldatei `mcp-reqogniloom.md` in jedem Provider-Verzeichnis, das Regeln unterstützt
- Provider MCP-Konfigurationen (eingecheckt mit Variablen-Referenzen + lokale, ignorierte Dateien mit echten Werten)
- `.gitignore`-Einträge für alle Secrets-Dateien

## Tools

| Tool | Zweck |
|------|---------|
| `requirement.get` / `requirement.query` | Anforderungen abrufen oder suchen |
| `requirement.create` / `.update` / `.decompose` / `.validate` / `.derive` | Anforderungen erstellen und weiterentwickeln (Schreibzugriff) |
| `requirement.check_consistency` | Konsistenzprüfung über den gesamten Anforderungsbaum |
| `needs.read` / `.create` / `.update` | Stakeholder-Bedürfnisse |
| `needs.get_traces` / `.derive_requirements` | Traceability von Bedürfnissen und Ableitung von Anforderungen |
| `architecture.get` / `.query` | Architekturelemente abrufen oder suchen |
| `architecture.create` / `.update` / `.link` / `.decompose` / `.decompose_commit` | Architektur erstellen (Schreibzugriff) |
| `test.get` / `.query` | Tests abrufen oder suchen |
| `test.create` / `.update` / `.link` / `.run_create` / `.run_report_results` | Tests erstellen und Testdurchläufe dokumentieren (Schreibzugriff) |
| `test.run_get` / `.derive_from_requirement` | Testdurchlauf lesen / Tests aus Anforderung ableiten |
| `traceability.query` / `.suggest_links` | Artefaktübergreifende Traceability und Link-Vorschläge |
| `artifact.search` / `.get_tree` | Volltextsuche und Artefaktbaum |
| `workspace.get_context` | Aktiven Workspace-Kontext lesen |
| `adr.read` / `.create` / `.update` / `.delete` | Architecture Decision Records (Schreibzugriff) |
| `risk.read` / `.create` / `.update` / `.delete` | Risiken (Schreibzugriff) |
| `issue.read` / `.create` / `.update` / `.delete` | Issues (Schreibzugriff) |
| `glossary.read` / `.create` / `.update` / `.delete` | Glossareinträge (Schreibzugriff) |
| `prompt_template.get` | Inhalt eines LLM-Prompt-Template-Slots lesen |
| `ai_derivation.derive_requirements_from_need` / `.suggest_architecture_for_requirement` / `.decompose_requirement_next_level` | KI-gestützte Ableitung |

Schreibende Tools erfordern die Rolle **Editor** oder **Admin** im ReqogniLoom Workspace (RBAC) — ein API-Schlüssel mit reinen Leserechten (Viewer) erhält `PERMISSION_DENIED`.

Administrative und destruktive Namespaces sind in der Registry blockiert und erreichen ReqogniLoom niemals über diesen MCP-Server: `admin.*`, `user.*`, `permissions.*`, `audit.*`, `events.*`, `workspace.close` / `.reactivate` / `.delete`.

## Hinweise

- Es existieren noch keine dedizierten `reqogniloom:config` / `reqogniloom:setup` Skill-Dateien. Wenn später externe ReqogniLoom-Skills zu `config/skills-registry.yaml` hinzugefügt werden, verlinken Sie diese hier.
- Siehe `howto/mcp-setup.md` für das generelle MCP-Konzept, die Handhabung von Secrets und das Layout der Provider-Konfigurationen.
