# MCP: reqogniloom

> ReqogniLoom requirements-engineering platform — requirements, architecture, tests, traceability and AI-assisted derivation

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

ReqogniLoom ist die Single-Source-of-Truth für Requirements, Architektur und Test-Traceability. Verwende es immer, wenn du Features validieren oder Architekturentscheidungen nachvollziehen musst.
requirement.query/get: Wann nutzen? Zu Beginn jeder Aufgabe, um Anforderungen und deren Kontext zu verstehen. requirement.create/update/decompose/derive: Wann nutzen? Während der Planungsphase, um große Features in überprüfbare Requirements zu zerlegen. architecture.*, test.*: Wann nutzen? Beim Systemdesign (Architecture) und TDD-Prozess (Tests) zur Verknüpfung mit Code. traceability.query/suggest_links: Wann nutzen? Beim Code-Review oder Validator-Gate, um die REQ-Abdeckung zu validieren. artifact.search/get_tree: Wann nutzen? Für tiefgreifende Recherchen über den gesamten Artefakt-Baum. ai_derivation.*: Wann nutzen? Wenn du komplexe, abstrakte Requirements systematisch in technische Sub-Tasks aufschlüsseln musst.
Schreibende Tools erfordern Editor- oder Admin-Rolle. Administrative/destruktive Namespaces (admin.*, user.*, etc.) sind aus Sicherheitsgründen hart blockiert.

## Verbindungstyp

- Typ: `sse`
- URL: `{{MCP_REQOGNILOOM_URL}}/mcp/sse/` — Wert aus `secrets.local.yaml`

---

*Generiert von agent-meta aus `config/mcp-registry.yaml` — nicht manuell bearbeiten.*
