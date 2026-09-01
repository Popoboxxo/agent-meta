---
name: admin-server-god-object-split
description: Wave-5/#572 AdminRequestHandler split — delegation is mandatory (tests bind to handler methods+class-attrs), route-table + AuthService + AuditService done, ServiceContext seam exists for the rest
metadata:
  type: project
---

Issue #572 / Wave 5 splits the ~3450-line `AdminRequestHandler` in `scripts/admin-server.py` into service classes.

**Hard constraint that dictates the whole approach:** `tests/test_admin_server.py` calls handler methods DIRECTLY (`admin_server.AdminRequestHandler.__new__(...)`, then sets class attrs like `.root`/`.config_manager`/`.admin_token` and calls `handler._foo()`), and mocks `handler._send_json`. So business logic CANNOT simply be moved out and deleted — every test-referenced method must stay on the handler (real body or thin delegator). Refactor pattern = Strangler-Fig **delegation**, never wholesale removal.

**Why:** Acceptance criterion #4 requires all existing tests pass UNMODIFIED. Directly-called (must-preserve) methods include: `_check_token`, `_check_origin`, `_handle_error`, `_run_consistency_check`, `_compute_injection_drift`, `_load_models_dev_data`, `_collect_models`, `_apply_pricing_overlay`, `_suggestions_from_models_dev`, `_handle_get_model_suggestions`, `_handle_post_models_dev_import`, `_template_path`, `_write_submodule_protection`, `_handle_get_backups`, `_dispatch_put`; class attrs `_models_dev_cache/_cache_ts/_error`, `_MODELS_DEV_ERROR_TTL_SECONDS`.

**How to apply (state as of this session, branch `refactor/admin-request-handler-split`):**
- DONE: route-table (exact-dict + ordered-prefix-list, criterion #3); `AuthService` (static token/origin logic); `AuditService` (consistency/config-audit/injection-drift/deactivation) + a `ServiceContext` seam (`ServiceContext(handler_cls)` reads root/config_manager/mode LIVE off the handler class so test attr-swaps still work) + module-level `_generic_error_response`.
- REMAINING services (build on `ServiceContext`): Models (LARGEST + riskiest — its cache lives as `AdminRequestHandler` class attrs the tests poke directly; keep cache on handler or have service read it via ctx), Template, Pipeline, Reflection. Pipeline+Reflection SHARE a ~250-line role-defaults-YAML machinery (`_build_role_defaults_section_body`, `_update_role_defaults_section`, `_split_*_children`, `_indent_yaml_dump`…) — extract that shared machinery once, don't duplicate.
- ROUTING QUIRK preserved (now commented in code): `/api/config/submodule-protection` matches the `/api/config/` prefix BEFORE the exact tuple → routes to generic config-read, NOT the status handler. Exact-dict-then-prefix is behavior-equivalent ONLY because that path is deliberately omitted from the exact GET table. `/api/config/` (trailing slash) → 404 after `rstrip("/")`.
- TRY004 ruff findings on extracted `_route_put_*/_route_post_*`: keep `raise ValueError` (NOT TypeError) — `do_PUT`/`do_POST` map `except ValueError → 400`; TypeError would become 500. See [[admin-server-test-run-gotcha]].

Verification tooling used: a route-trace equivalence harness (records first delegated call + outcome per verb/path, diffs before/after = 0). Rebuild it before touching dispatch again.
