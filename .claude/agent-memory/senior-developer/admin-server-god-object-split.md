---
name: admin-server-god-object-split
description: Wave-5/#572 AdminRequestHandler split — DONE, all 6 services extracted (Auth/Audit/Template/Pipeline/Reflection/Models) + RoleDefaultsEditor + ServiceContext seam, delegation pattern, route tables
metadata:
  type: project
---

Issue #572 / Wave 5 split the ~3450-line `AdminRequestHandler` in `scripts/admin-server.py` into service classes. **COMPLETE** (checkpoint `f693aae5` had Auth+Audit+route-tables; the rest were finished in a follow-up session on branch `refactor/admin-request-handler-split`).

**Final structure (all before `class AdminRequestHandler`):** `AuthService` (static token/origin), `AuditService` (consistency/config-audit/injection-drift/deactivation), `TemplateService` (template discovery/resolve/read/write + agent hierarchy), `PipelineService` + `ReflectionService` (both compose the shared `RoleDefaultsEditor` — the ~320-line formatting-preserving role-defaults.yaml section editor), `ModelsService` (registry+pricing+curation+models.dev catalog cache+suggestions). Wired via `ServiceContext(handler_cls, handler_instance)`.

**Hard constraint that dictated the design — DELEGATION, never removal:** `tests/test_admin_server.py` calls handler methods directly (`AdminRequestHandler.__new__`, set class attrs `.root`/`.config_manager`, call `handler._foo()`, mock `handler._send_json`). So every test-referenced method stays on the handler as a thin delegator; business-logic BODIES moved into services. **Why:** criterion #4 = all existing tests pass UNMODIFIED (they did: 801 passed, 2 skipped throughout).

**ServiceContext seam:** reads `root`/`config_manager`/`mode`/`version` LIVE off `handler_cls` (so per-test attr swaps work); exposes `agent_meta_root()`, `role_defaults_path()`, `ensure_lib_on_path()`, `handler_cls` (models.dev cache store), `handler` (live instance).

**Two subtle Models traps (both solved, keep in mind for future edits):**
1. models.dev cache is process-wide state on the HANDLER CLASS (`_models_dev_cache/_cache_ts/_error/_last_fetch_error`, const `_MODELS_DEV_ERROR_TTL_SECONDS`) that tests seed AND reset via delattr on `AdminRequestHandler`. `ModelsService` reads/writes it via `ctx.handler_cls`; the const stays defined on the handler. Do NOT move those onto the service.
2. Tests monkeypatch `handler._load_models_dev_data` (INSTANCE) then call a suggestions method expecting the internal call to use the mock. Since that logic moved into `ModelsService`, its internal call goes `(self._ctx.handler or self)._load_models_dev_data()` — routing through the live handler instance so the mock is honored. Any future service method that tests hook this way needs the same `ctx.handler` routing.

**Models kept `_underscore` method names in the service** (unlike the other services which use public names) to avoid rewriting ~20 inter-method call sites; handler delegators call `self._models_service()._collect_models()` etc. Each Models method therefore appears twice (delegator + service) — intentional, not a dup bug.

Route tables (exact-dict + ordered-prefix, `_resolve_route`) unchanged; `/api/config/submodule-protection` prefix-shadow quirk still preserved and commented. See [[admin-server-test-run-gotcha]].

**Discovered PRE-EXISTING bug (NOT fixed — out of pure-refactor scope, flagged for a separate issue):** writing a reflection pair via `update_section("reflection_pairs", ...)` produces malformed YAML against this repo's role-defaults.yaml (the list-child path in the formatting-preserving editor). Proven pre-existing: byte-identical broken output from pre- and post-extraction code. Reading reflection pairs works; pipeline (dict) writes work.

Verification tooling (scratchpad, not committed): `route_trace.py` (routing equivalence, 0 diffs guard) + per-service offline byte-equivalence probes. Rebuild before touching dispatch/services again.
