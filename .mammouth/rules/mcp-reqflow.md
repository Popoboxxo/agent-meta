# MCP: reqflow

> ReqFlow requirements-engineering platform — requirements, architecture, tests, traceability and AI-assisted derivation

---

## Erlaubte Tools

- `requirement.get`
- `requirement.query`
- `requirement.create`
- `requirement.update`
- `requirement.decompose`
- `requirement.validate`
- `requirement.derive`
- `requirement.check_consistency`
- `needs.read`
- `needs.create`
- `needs.update`
- `needs.get_traces`
- `needs.derive_requirements`
- `architecture.get`
- `architecture.query`
- `architecture.create`
- `architecture.update`
- `architecture.link`
- `architecture.decompose`
- `architecture.decompose_commit`
- `test.get`
- `test.query`
- `test.create`
- `test.update`
- `test.link`
- `test.run_create`
- `test.run_get`
- `test.run_report_results`
- `test.derive_from_requirement`
- `traceability.query`
- `traceability.suggest_links`
- `artifact.search`
- `artifact.get_tree`
- `workspace.get_context`
- `adr.read`
- `adr.create`
- `adr.update`
- `adr.delete`
- `risk.read`
- `risk.create`
- `risk.update`
- `risk.delete`
- `issue.read`
- `issue.create`
- `issue.update`
- `issue.delete`
- `glossary.read`
- `glossary.create`
- `glossary.update`
- `glossary.delete`
- `prompt_template.get`
- `ai_derivation.derive_requirements_from_need`
- `ai_derivation.suggest_architecture_for_requirement`
- `ai_derivation.decompose_requirement_next_level`

## Verbotene Tools (ABSOLUT — keine Ausnahmen)

- `workspace.close`
- `workspace.reactivate`
- `workspace.delete`
- `permissions.set_rule`
- `permissions.list`
- `permissions.revoke`
- `permissions.check`
- `admin.backup_create`
- `admin.backup_list`
- `admin.restore`
- `audit.query`
- `audit.ai_review`
- `events.dlq_list`
- `events.dlq_replay`
- `user.create`
- `user.assign_role`
- `user.list`
- `user.deactivate`

## Agent-Hinweise

ReqFlow verwaltet Requirements, Architektur, Tests und Traceability für dieses Projekt.
requirement.query/get: bestehende Requirements durchsuchen.
requirement.create/update/decompose/validate/derive: Requirements anlegen und pflegen (Editor- oder Admin-Rolle nötig).
architecture.*, test.*: Architektur-Elemente und Testfälle anlegen, verknüpfen und Testläufe protokollieren (analoge RBAC-Regeln).
traceability.query/suggest_links: Rückverfolgbarkeit zwischen Requirement/Architecture/Test prüfen bzw. Link-Vorschläge holen.
artifact.search/get_tree: Volltextsuche und Artefakt-Baum.
adr/risk/issue/glossary.*: ADRs, Risiken, Issues und Glossar-Einträge verwalten.
ai_derivation.*: KI-gestützte Ableitung von Requirements und Architektur-Vorschlägen.
prompt_template.get: aktuellen Prompt-Slot-Inhalt abrufen.
Schreibende Tools erfordern Editor- oder Admin-Rolle (RBAC) im ReqFlow-Workspace — sonst PERMISSION_DENIED.
Administrative/destruktive Namespaces (admin.*, user.*, permissions.*, audit.*, events.*, workspace.close/reactivate/delete) sind gesperrt.

## Verbindungstyp

- Typ: `sse`
- URL: `{{MCP_REQFLOW_URL}}/mcp/sse/` — Wert aus `secrets.local.yaml`

---

*Generiert von agent-meta aus `config/mcp-registry.yaml` — nicht manuell bearbeiten.*
