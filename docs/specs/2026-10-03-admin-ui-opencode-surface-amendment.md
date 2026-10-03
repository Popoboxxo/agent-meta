# Admin-UI + Project-Level `surface-version` Gap Closure — Spec Amendment

> **Status: APPROVED (2026-10-03)**
> **Type:** Docs-only amendment (addendum) to an APPROVED spec. No code is implemented by this document.
> **Parent spec:** `docs/specs/2026-09-30-provider-audit-opencode-v2.md` (`Status: APPROVED (2026-10-01)`)
> **parent-spec-id:** `SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30`
> **Trace anchor (this amendment):** `spec-id: SPEC-ADMIN-UI-OPENCODE-SURFACE-AMENDMENT-2026-10-03` — a plan derived from this amendment MUST reference this value and the parent `parent-spec-id`.
> **Branch / PR:** `feat/provider-audit-opencode-v2` (PR #845)
> **Scope:** closes the project-channel + Admin-UI gaps G1–G5 for Opencode `surface-version` (v1 default, v2 opt-in). It does not change the parent spec's ACs, does not renumber them, and does not delete any historical decision.

---

## 1. Problem / Ziel / Nicht-Ziele

### 1.1 Problem (live-verified evidence)

The sync/config chain already resolves `surface-version` → `mcp-config.format` and `agent-transform.frontmatter-mechanism` fully and provider-agnostically via `scripts/lib/providers.py::_apply_surface_format_selection` / `_apply_surface_mechanism_selection`, driven by `config/ai-providers.yaml` (Opencode: `surface-version: v1`, `mcp-config.surface-formats {v1,v2}`, `agent-transform.surface-mechanisms {v1,v2}`, `ai-providers.yaml:208-302`). Dispatch is on the **resolved config values only** — never a provider-name literal.

Four verified gaps remain:

| Gap | Evidence (HEAD on `feat/provider-audit-opencode-v2`) | Impact |
|-----|------------------------------------------------------|--------|
| **G4 — no project channel** | `.meta-config/project.yaml::provider-options.Opencode` is `{}` (`:166`); `load_providers_config(agent_meta_root)` never reads/merges `provider-options` (`providers.py:122-206`, `:606-619`). Parent spec §11 states opt-in via `ai-providers.yaml::Opencode.surface-version: v2` (`2026-09-30-provider-audit-opencode-v2.md:567`), but `ai-providers.yaml` is the **framework registry**, not the consumer project — so a submodule consumer cannot opt into v2 without editing the framework. | v2 is unreachable for consumers. |
| **G5 — schema forbids the key** | `config/project-config.schema.json:818-837` sets `provider-options.Opencode.additionalProperties: false` and models only `frontmatter-keep-fields`/`frontmatter-strip-fields`; `surface-version` is rejected by schema validation. Top-level `provider-options` is `additionalProperties: true` (`:861`), but the known provider blocks are closed. | Even a hand-written project key fails validation. |
| **G1 — no server-side validation** | `_handle_post_ai_providers_update` (`scripts/admin-server.py:4545`) and `_route_put_config` (`:3693`, `key == "ai-providers"` via `_PUT_PREFIX_ROUTES` `/api/config/`) blind-write the registry body with `yaml.dump`. | Any string (e.g. `v3`) persists and silently resolves to the v1 fallback. |
| **G2 — no active-surface display** | `_handle_get_ai_providers` (`:4534`) returns the raw registry file; no computed/resolved surface is exposed. | Operators cannot see which surface is actually active. |
| **G3 — free-text + project view missing** | `docs/ui/admin-ui.html::viewAIProviders` (`:1959`) renders `surface-version` through `inferSchema` (`:2036`) which **never emits `enum`**, so the field is a free-text input; `SchemaFormGenerator` already supports enum (`_renderField :1233`, enum branch :1244, `_renderEnum :1298`). `viewProjectProviders` (`:6503`) renders a generic `renderDictEditor` KV editor and never exposes `surface-version`, and its help text (`:6585-6599`) does not list it. | No enum affordance and no project-level editor for the key. |

### 1.2 Ziel

- A consumer project can opt into v2 through `.meta-config/project.yaml → provider-options.<Provider>.surface-version` **without touching the framework registry** (D1/D2).
- The project schema accepts the key (G5).
- The Admin server validates it against the provider's own `surface-formats` and exposes the resolved active surface (D3).
- The Admin UI renders it as a `<select>` and shows an active-surface badge, both in the registry view and the project provider-options view (D4).
- v1 remains the default and byte-frozen; v2 remains opt-in (D5).

### 1.3 Nicht-Ziele

- No new provider, no provider-name branch anywhere; only data-driven lookups (parent ADR-1).
- No change to the parent spec's AC-1…AC-22, no renumbering, no code implementation in this amendment.
- No change to the `surface-formats`/`surface-mechanisms` maps themselves.
- No forced migration of consumers; no default flip to v2 (reserved for a future major; parent §11/OQ-8).
- No new Admin endpoint; only the existing ai-providers endpoints are extended.

---

## 2. Decisions (binding — documented, not re-opened)

### D1 — New project channel (provider-agnostic, allow-listed)

`provider-options.<Provider>.surface-version` and the sibling provider-neutral opt-in flag `provider-options.<Provider>.agent-discovery` override the matching registry entry's same-named key **before** surface resolution. Mechanism: iterate the project's `provider-options` entries, and for each entry whose provider name exists in the registry, copy only the allow-listed surface keys `{surface-version, agent-discovery}` when present. No provider-name literal. The override happens once, in the resolver, so every consumer of the resolved config sees the same values.

### D2 — Integration point

Extend `scripts/lib/providers.py::load_providers_config(agent_meta_root, project_config=None)`. When `project_config` is provided, apply the D1 override before `_apply_surface_format_selection` / `_apply_surface_mechanism_selection`. The generation path (`scripts/lib/sync_pipeline.py::_sync_stage_config_and_presets`, which already holds `config`) and every check/consistency path that must agree MUST pass the same project config so resolution cannot diverge between generation and validation. The call-site matrix in §8 enumerates every `load_providers_config(` caller and marks `MUST-THREAD` vs `SURFACE-IRRELEVANT`.

### D3 — Server validation + active-surface

On PUT/POST of `ai-providers`, reject a `surface-version` value that is not a key of that provider's `mcp-config.surface-formats` (fallback allowed values `{v1, v2}`) with HTTP 400 + a JSON error. Add a read-only computed `active-surface` (resolved format + mechanism) to the GET payload. No provider-name branch — derive from the data. **Clarification (REV-R5):** the `{v1,v2}` fallback is a **UI option-rendering** default only — it is not a server-side acceptance fallback. When a provider declares `surface-formats`, the server accepts exactly its keys. When a provider declares **no** `surface-formats` at all, the server accepts only the implicit default `v1`; any other value is rejected with 400 (no silent fallback), and sync/check emits a WARNING finding.

### D4 — UI

Render `surface-version` as a `<select>` whose options are the keys of the provider's `mcp-config.surface-formats` (fallback `[v1, v2]`; when the provider declares **no** `surface-formats`, options are `[v1]` only — REV-R5); extend the schema inference so the enum reaches `SchemaFormGenerator`. Show an "active surface" badge (resolved format/mechanism). Expose `surface-version` in the project provider-options editor too.

### D5 — v1 default, byte-frozen; v2 opt-in

No behavior change when `provider-options` does not set the key. v1 output stays byte-identical to the pre-change baseline. v2 remains opt-in and ships as a **minor** (parent A1.2/OQ-8).

---

## 3. Interface Contracts

### 3.1 Resolver (`scripts/lib/providers.py`)

```python
_SURFACE_OVERRIDE_KEYS: tuple[str, ...] = ("surface-version", "agent-discovery")

def _apply_project_surface_overrides(provider_config: dict, project_config: dict | None) -> dict:
    """Copy allow-listed provider-options surface keys onto matching registry
    entries BEFORE surface resolution. Provider-agnostic (iterates project
    provider-options; no provider-name literal). Returns the SAME mapping with
    per-entry dicts updated in place.

    Contract:
      - project_config not a dict, or no 'provider-options' dict -> no-op.
      - for each (provider, options) in provider-options.items():
          * skip when provider not in provider_config;
          * skip when options is not a dict;
          * for key in _SURFACE_OVERRIDE_KEYS:
              - surface-version: copy only when isinstance(value, str) and value != "";
              - agent-discovery: copy only when isinstance(value, bool).
      - Non-allow-listed keys are never copied (frontmatter-* remain handled by
        resolve_frontmatter_strip_fields as today).
    """

def load_providers_config(agent_meta_root: Path, project_config: dict | None = None) -> dict:
    """Load config/ai-providers.yaml (unchanged fallbacks), then:
        1. extract the registry (data.get("providers", data), as today);
        2. if project_config is not None: _apply_project_surface_overrides(registry, project_config);
        3. _apply_surface_format_selection(registry);
        4. _apply_surface_mechanism_selection(registry);
        and return the registry.
       Backward compatible: project_config defaults to None -> step 2 is skipped,
       so every existing caller keeps the exact current behavior (D5).
    """
```

Error paths: never raises on malformed `project_config`/`provider-options` — non-dict entries are skipped (fail-safe), mirroring `resolve_frontmatter_strip_fields` (`providers.py:657-703`).

**No-`surface-formats` rule (REV-R5).** A provider may only resolve a surface when it declares `mcp-config.surface-formats` (and `agent-transform.surface-mechanisms`). If a provider carries an explicit `surface-version` but **no** `surface-formats` mapping:
- the **server channel rejects** a value other than the implicit default `"v1"` with HTTP 400 (`_validate_surface_versions`, §3.2) — it must not silently fall back to `{v1,v2}`;
- the **sync/check channel emits a WARNING finding** (never a silent pass) when a non-default `surface-version` is present without `surface-formats`, so a direct YAML edit is visible under `--validate`/`--check`;
- the **resolver stays fail-safe** (no raise): it leaves the statically declared `mcp-config.format`/`frontmatter-mechanism` untouched, i.e. the declared v1 shape. This is the reject-or-warn pair — no silent acceptance.

### 3.2 Server endpoints (`scripts/admin-server.py`)

**Endpoint choice for the UI (REV-R1, option (a)).** `viewAIProviders` (`admin-ui.html:1963`) keeps using **`/api/config/ai-providers`** (`_route_get_config`, `:3543`) for the editable data and PUTs the same object via `saveConfig` (`admin-ui.html:1795-1797`) → `_route_put_config("ai-providers")` (`:3693`). The read-only `active-surface` badge is fetched from the **separate, dedicated** `GET /api/ai-providers` (`_handle_get_ai_providers`, `:4534`). `_route_get_config` stays generic and is **not** special-cased for `ai-providers`.

**Reserved-key stripping (REV-R1).** `active-surface` is a reserved, read-only key and MUST NEVER be persisted by either write handler:
- `_route_put_config` for `key == "ai-providers"` pops `active-surface` from the body (working on a shallow copy; the request body is not mutated in place) before validation and write;
- `_handle_post_ai_providers_update` pops `active-surface` before `yaml.dump`;
- the UI never merges the read-only map into the editable object: it is fetched into a separate `activeSurface` variable, and `viewAIProviders` defensively `delete`s an `active-surface` key from the config object before `state.setConfig("ai-providers", …)` / save.

```python
def _validate_surface_versions(providers: dict, *, allow_no_formats: bool = False) -> None:
    """Fail-loud validator. Raises ValueError (caller maps to HTTP 400) when any
    provider entry's `surface-version` is a string that cannot be resolved:
      - provider declares mcp-config.surface-formats:
          surface-version MUST be a key of it; else 400.
      - provider declares NO surface-formats:
          only the implicit default "v1" is acceptable; any other string -> 400
          (no silent {v1,v2} fallback; REV-R5).
      - non-string surface-version: ignored (the resolver ignores it too).
      - provider without surface-version: skipped.
    No provider-name literal; the allowed set is read from the same data the
    resolver reads.
    """
```

- **PUT** `/api/config/ai-providers` → `_route_put_config("ai-providers")` (`:3693`): strip `active-surface`, then before `config_manager.write`, when the body is a dict, validate `body.get("providers", body)` via `_validate_surface_versions`. On failure return `{"error": "..."}` with `status=400` and write nothing.
- **POST** `/api/ai-providers/update` → `_handle_post_ai_providers_update` (`:4545`): strip `active-surface`, same validation on the incoming dict before `yaml.dump`; 400 + JSON error on failure, no file write.
- **Project channel (REV-R4).** The project provider-options channel is validated **server-side**, not client-side only. `_route_put_config("project")` (`:3693`) and `_write_project_section` (`:4827`) when `section == "provider-options"` (the path the Admin UI actually uses via `saveProjectSections` → `saveProjectSection("provider-options", …)` → PUT `/api/config/project/section`, `admin-ui.html:5830-5832, 6656-6662`) validate `provider-options.<P>.surface-version` membership against the same registry data with the same helper, rejecting with HTTP 400. This closes the gap that the project editor writes through the section endpoint, not through `/api/config/project`.
- **GET** `/api/ai-providers` → `_handle_get_ai_providers` (`:4534`): response body = raw registry file plus a **read-only** top-level sibling `active-surface`:

```jsonc
{
  "providers": { /* unchanged registry content, editable */ },
  "active-surface": {
    "Opencode": { "version": "v2", "format": "opencode-json-v2", "mechanism": "opencode-native-v2" }
    // one entry per provider that declares surface-formats
  }
}
```

`active-surface` is computed with the effective project config via the same resolver (`load_providers_config(agent_meta_root, project_config)`), so the displayed surface equals the generation surface. It lives only on this dedicated GET response; the editable `/api/config/ai-providers` object never contains it (option (a)), and both write handlers strip it defensively (above).

### 3.3 Project schema (`config/project-config.schema.json`)

Additive properties inside every modeled provider block that has `additionalProperties: false` (Claude `:742`, Gemini `:763`, Continue `:784`, Opencode `:818-837`, Mammouth `:839`). Note the top-level `provider-options` description (`:740`) currently names `Copilot`, but Copilot is **not** a modeled provider block — it (like Codex/KimiCode/ZCode) is accepted only via the top-level `additionalProperties: true` (`:861`); the new keys therefore only need to be added to the modeled blocks.

```jsonc
"surface-version": { "type": "string", "description": "Generation surface for this provider. Must be a key of ai-providers.yaml's mcp-config.surface-formats (Opencode: v1|v2). Default: v1 (unchanged)." },
"agent-discovery": { "type": "boolean", "description": "Provider-neutral discovery-surface opt-in (parent spec A1.1). Default: false." }
```

No `enum` is placed in the project schema: the authoritative allowed set lives in `ai-providers.yaml` and is enforced by D3 at write time (the schema cannot read another file). Top-level `provider-options` keeps `additionalProperties: true`.

### 3.4 UI (`docs/ui/admin-ui.html`)

- `viewAIProviders` (`:1959`): fetch the read-only badge map separately — `const activeSurface = (await api.get("/api/ai-providers").catch(() => ({})))["active-surface"] || {}` — and never merge it into the editable config object. For each provider, infer its schema with enum options for `surface-version`:

```js
// options = Object.keys(conf["mcp-config"]?.["surface-formats"] || {});
// if surface-formats is absent/empty -> ["v1"]  (REV-R5: only the implicit default
// is resolvable; the server rejects any other value for such a provider).
const schema = { type: "object", properties: inferSchema(conf, { enumFields: { "surface-version": options } }) };
```

- `inferSchema(obj, opts)` (`:2036`; nested recursion at `:2043`): add the optional `opts.enumFields` map; when a key is present in it emit `{ type: "string", enum: opts.enumFields[key] }` (instead of `{ type: "string" }`). **REV-R7:** the current object branch at `:2043` calls `inferSchema(v)` with **no `opts`**, so the helper MUST forward `opts` through nested recursion (`out[k] = { type: "object", properties: inferSchema(v, opts) }`) to stay future-proof for nested providers. `SchemaFormGenerator._renderField` (`:1233`; enum branch `:1244-1245`) already routes `enum` to `_renderEnum` (`:1298`) → `<select>`.
- Active-surface badge: render `activeSurface[provider].format` / `.mechanism` next to the provider summary (reuse the existing `badge` class; render via `textContent`).
- `viewProjectProviders` (`:6503`): for each provider section, when the provider is present in the `/api/ai-providers` response with `surface-formats`, render a dedicated `surface-version` `<select>` (options = surface-format keys; when `surface-formats` is absent/empty, options = `[v1]`, REV-R5) and an `agent-discovery` checkbox **above** the generic `renderDictEditor`; both write into `providerOptions[provName]` so the existing Save payload (`:6656-6662`, via `saveProjectSection("provider-options", …)` → `_write_project_section`) carries them unchanged. Extend the help text (`:6585-6599`) with `surface-version` / `agent-discovery`. Avoid duplicate keys: the generic KV editor must not also offer these two fields.

Field semantics: `surface-version` ∈ keys(`mcp-config.surface-formats`), or `{v1}` when no map is declared; unset ⇒ resolver default `v1`; `agent-discovery` bool, unset ⇒ `false`.

---

## 4. Datenfluss

```
.meta-config/project.yaml
  provider-options.<Provider>.surface-version  ─┐
  provider-options.<Provider>.agent-discovery  ─┤  (D1 allow-list)
                                                ▼
load_providers_config(agent_meta_root, project_config)   [providers.py]
  registry := ai-providers.yaml providers
  registry := _apply_project_surface_overrides(registry, project_config)
  registry := _apply_surface_format_selection(registry)      # mcp-config.format
  registry := _apply_surface_mechanism_selection(registry)   # frontmatter-mechanism
                                                │
             ┌──────────────────────────────────┼───────────────────────────────┐
             ▼                                   ▼                               ▼
   generation (sync_pipeline)          checks (agent_sync,              Admin UI (REV-R1, option (a))
   emits MCP file + frontmatter        consistency/model_contracts)     editable: /api/config/ai-providers
   per resolved value                  agree (same project_config)      badge:    GET /api/ai-providers
                                                                        -> active-surface (read-only)
```

Persistence: only `.meta-config/project.yaml` (project channel) and `config/ai-providers.yaml` (registry) are written. `active-surface` is computed per request and never persisted; both registry write handlers strip the reserved key and the UI never merges it (REV-R1). No writer reads `surface-version`; writers keep dispatching on `mcp-config.format` / `frontmatter-mechanism` only (parent ADR-1/ADR-2).

---

## 5. Acceptance Criteria

Each AC is Given/When/Then with an observable expected result, and maps to at least one §3 contract.

| ID | Criterion | Contracts |
|----|-----------|-----------|
| **AC-A1** | **Given** a project whose `.meta-config/project.yaml` sets `provider-options.Opencode.surface-version: v2`, **When** `load_providers_config(root, project_config)` is called, **Then** the returned `Opencode` entry has `mcp-config.format == "opencode-json-v2"` AND `agent-transform.frontmatter-mechanism == "opencode-native-v2"`. **Given** the same project without the key, **Then** the entry is byte-identical to the registry defaults (`opencode-json` / `opencode-native`). | §3.1, D1/D2/D5 |
| **AC-A2** | **Given** a project with `surface-version: v2`, **When** a real sync generates Opencode artifacts, **Then** the committed MCP config uses the v2 shape and the emitted agent frontmatter uses the v2 mechanism; **Given** v1/unset, **Then** the generated Opencode artifacts are byte-identical to the pre-change baseline. Covers the end-to-end chain project.yaml → resolver → sync output v1 vs v2 → runtime-readable artifact. | §3.1, D2/D5 |
| **AC-A3** | **Given** the same project, **When** `sync.py --check` / `--validate` and the consistency checks run, **Then** they resolve the same `provider_config` as generation (project config threaded per §8) and report rc 0 for a consistent v2 tree; **Given** a tree generated as v1 while the project opts into v2, **Then** at least one finding reports the mismatch (no silent divergence). | §3.1, D2, §8 |
| **AC-A4** | **Given** a `PUT /api/config/ai-providers` or `POST /api/ai-providers/update` body with `providers.Opencode.surface-version: "v3"` (not a key of its `surface-formats`), **When** the request is handled, **Then** the response is HTTP 400 with a JSON `{"error": ...}` and the file is unchanged; **Given** `"v2"`, **Then** HTTP 200 and the value is persisted. **Given** a project write (`PUT /api/config/project` or `PUT /api/config/project/section` with `section: "provider-options"`) whose `provider-options.Opencode.surface-version` is not resolvable (unknown key, or any value other than `v1` when the provider declares no `surface-formats`), **Then** HTTP 400 and no project write (REV-R4/REV-R5). | §3.2, D3 |
| **AC-A5** | **Given** the Opencode registry with `surface-version: v2` (project-effective), **When** `GET /api/ai-providers` is handled, **Then** the payload contains `active-surface.Opencode == {"version":"v2","format":"opencode-json-v2","mechanism":"opencode-native-v2"}`. **Given** a `PUT /api/config/ai-providers` body that injects an `active-surface` key (or the normal UI save path), **Then** the persisted `config/ai-providers.yaml` contains **no** `active-surface` — both `_route_put_config` and `_handle_post_ai_providers_update` strip the reserved key before `yaml.dump`. | §3.2, D3 |
| **AC-A6** | **Given** the `ai-providers` view and a provider declaring `mcp-config.surface-formats {v1,v2}`, **When** the form renders, **Then** `surface-version` is a `<select>` with options `v1`/`v2` (not free text) and an active-surface badge is shown. **Given** the project Providers view, **Then** each provider with surface-formats exposes a `surface-version` `<select>` that writes `provider-options.<Provider>.surface-version` on Save. | §3.4, D4 |

---

## 6. Offene Fragen + Risiken

> Notation: `R1`–`R7` below are this amendment's own risks. References to the review findings that drove this revision use the distinct prefix `REV-R1`…`REV-R7` (see §3.2/§3.4/§5/§7/§8).

| ID | Risk / open question | Mitigation |
|----|----------------------|------------|
| R1 | **v1 byte-freeze regression.** The override must be a strict no-op when the key is absent. | AC-A1/A2 byte-identity assertion; override guarded by `project_config is not None` and per-key presence; existing `tests/test_surface_version_selection.py` stays green. |
| R2 | **check/generation divergence.** A check path that resolves v1 while generation emits v2 yields a false rc 0 or spurious findings. | The §8 matrix marks every MUST-THREAD site; AC-A3 pins agreement; a test asserts generation-resolved `provider_config == check-resolved provider_config` for a v2 project. |
| R3 | **Computed key leakage.** `active-surface` must never be written back into `config/ai-providers.yaml`. | Option (a): the editable `/api/config/ai-providers` object never carries it; both write handlers strip the reserved key before `yaml.dump`; the UI deletes it defensively; AC-A5 asserts the persisted file has no `active-surface`. |
| R4 | **Schema additivity vs. unknown value.** The project schema cannot enumerate `surface-formats`, so an unknown `surface-version` still passes schema validation. | D3 server validation is the write-time guard on the registry **and** the project/provider-options paths; the resolver ignores unknown values and keeps the declared fallback (fail-safe, parent behavior). REV-R5 additionally warns on a non-default value without `surface-formats`. |
| R5 | **Provider-name coverage.** `provider-options` models only Claude/Gemini/Continue/Opencode/Mammouth; other providers (Codex/KimiCode/ZCode) and Copilot rely on top-level `additionalProperties: true`. | D1 iterates the data; no provider-name branch. Adding the properties only to the modeled blocks is sufficient because unknown provider blocks are already accepted. |
| R6 | **Super-admin vs. project mode.** GET `/api/ai-providers` is super-admin; the effective project config may live in a consumer project whose registry is the submodule. | `active-surface` is computed with `load_providers_config(agent_meta_root, project_config)` using the same `config_manager.read("project")` the other endpoints use. |
| R7 | **Comment stripping on save (pre-existing defect, NOT introduced here).** Both write paths (`_route_put_config`, `_handle_post_ai_providers_update`) serialise with `yaml.dump` and therefore drop YAML comments — `config/ai-providers.yaml:200-309` (Opencode block) and the rest of the file are heavily commented. No external dependency is allowed in agent-meta, so `ruamel.yaml` (round-trip) is unavailable. **Disposition: OUT-OF-SCOPE for this amendment.** Semantic data is preserved byte-for-value (only comments/ordering change on round-trip); D3's read-only `active-surface` is not persisted. Tracked as a **separate finding/issue**: "round-trip comment preservation / round-trip diff guard for `ai-providers.yaml` save paths". | Documented here; do not fix in this change. A follow-up may add a save-time diff guard that warns when a save drops comments, or a stdlib-only round-trip writer. No behavior regression is introduced by this amendment. |

No undecidable point remains; D1–D5 are pre-approved. If implementation finds a call site not listed in §8, it MUST be classified with the same rule (any path whose output depends on `mcp-config.format` or `frontmatter-mechanism` is MUST-THREAD).

---

## 7. Test Plan

| Layer | Test (new/extended) | Asserts |
|-------|--------------------|---------|
| Unit — resolver | extend `tests/test_surface_version_selection.py` | project override v2 sets format+mechanism; absent key → v1 byte-identical; `agent-discovery` copied; non-dict/malformed `provider-options` no-op; unknown override value ignored; `project_config=None` preserves current behavior. Also assert no provider-name literal (generic provider name `FutureProvider`). |
| Unit — schema | extend `tests/test_provider_options_schema.py` | `surface-version`/`agent-discovery` accepted in modeled provider blocks; unknown keys still rejected by `additionalProperties:false`. |
| Unit — server | extend `tests/test_admin_server.py` | `/api/ai-providers/update` + PUT `config/ai-providers`: 400 + JSON error on invalid value (file unchanged); 200 + persisted on valid; GET `active-surface` shape; an injected `active-surface` key is stripped and never persisted (REV-R1); project writes (`PUT /api/config/project` and `/api/config/project/section` with `section: "provider-options"`) return 400 on an unresolvable value and persist nothing (REV-R4/REV-R5); a provider with `surface-version: v2` but no `surface-formats` is rejected (REV-R5). |
| Unit — call-site consistency | new `tests/test_surface_version_consistency.py` | generation and check paths resolve identical `provider_config` for a v2 project (REV-R2 guard); a non-default `surface-version` without `surface-formats` yields a WARNING finding (REV-R5). |
| UI | extend `tests/test_admin_ui_plugins_section.py` / `tests/test_admin_cleanup_endpoint.py` style static assertions on `docs/ui/admin-ui.html`, or a `tests/browser` case if the harness is available | `inferSchema` emits `enum` from `surface-formats` and forwards `opts` through nested recursion (REV-R7); `viewAIProviders` fetches `/api/config/ai-providers` for edit and `/api/ai-providers` for the badge and strips `active-surface` before save (REV-R1); `viewProjectProviders` renders a `surface-version` select writing `provider-options` (AC-A6). |
| Follow-up (REV-R2, not this change) | issue/finding only | round-trip comment preservation / diff guard for `ai-providers.yaml`; asserted out-of-scope by absence, not by a test in this change. |
| Scenario (end-to-end) | extend `tests/scenarios/configs/69-opencode-v2-surface.project.yaml` + `tests/scenarios/asserts/69-opencode-v2-surface.sh` | full project.yaml → resolver → sync → artifact chain for v1 and v2, plus `--check` rc 0 (AC-A2/A3). |

Existing suites that MUST stay green: `tests/test_surface_version_selection.py`, `tests/test_admin_server.py`, `tests/test_provider_options_schema.py`, `python3 scripts/sync.py --validate`, `python3 scripts/sync.py --check` at the repo root.

---

## 8. Exact files / functions to touch + call-site matrix

### 8.1 File map

| File | Change |
|------|--------|
| `scripts/lib/providers.py` | add `_SURFACE_OVERRIDE_KEYS`, `_apply_project_surface_overrides`; extend `load_providers_config(agent_meta_root, project_config=None)` to call it before the two `_apply_surface_*` selectors. |
| `scripts/lib/sync_pipeline.py` | `_sync_stage_config_and_presets` (`:138-183`): pass `config` → `load_providers_config(agent_meta_root, config)` at `:155`. |
| `scripts/lib/agent_sync.py` | `collect_artifact_findings` (`:707`): pass `config` → `load_providers_config(agent_meta_root, config)` at `:728`. |
| `scripts/lib/consistency/artifact_contracts.py` | `check_artifact_contracts(agent_meta_root)` (`:89`): add `project_config` parameter, thread it into `load_providers_config`; update caller. |
| `scripts/lib/consistency/model_contracts.py` | `check_model_contracts(agent_meta_root)` (`:95`): add `project_config` parameter, thread it; update caller. |
| `scripts/consistency-check.py` | `run_checks` (`:142`): load the project config once and pass it to `check_artifact_contracts` (`:195`) and `check_model_contracts` (`:196`). |
| `scripts/sync.py` | cleanup-preview path (`:571`): pass `config` → `load_providers_config(agent_meta_root, config)`. |
| `scripts/lib/cli_commands.py` | test-repo validation (`:220`), activate/deactivate generation (`:806`, `:841`): pass `config`. |
| `scripts/admin-server.py` | add `_validate_surface_versions`; strip the reserved `active-surface` key in `_route_put_config` (`:3693`) and `_handle_post_ai_providers_update` (`:4545`); validate surface-version on the registry write (`key == "ai-providers"`) **and** the project write (`_route_put_config("project")` + `_write_project_section` `:4827` when `section == "provider-options"`, REV-R4); extend `_handle_get_ai_providers` (`:4534`) with the read-only `active-surface`; pass project config where the resolver is used. |
| `config/project-config.schema.json` | add `surface-version` + `agent-discovery` to the modeled provider blocks (Claude `:742`, Gemini `:763`, Continue `:784`, Opencode `:818-837`, Mammouth `:839`). |
| `docs/ui/admin-ui.html` | `viewAIProviders` (`:1959`, config via `/api/config/ai-providers` + badge via `/api/ai-providers`), `inferSchema` (`:2036`, nested `:2043`), `viewProjectProviders` (`:6503` + help text `:6585`), `_renderField` enum branch (`:1233`/`:1244-1245`). |
| Tests | see §7. |
| Follow-up issue (REV-R2, out of scope) | file "round-trip comment preservation / round-trip diff guard for `ai-providers.yaml` save paths" as a separate finding/issue; not implemented here. |

### 8.2 `load_providers_config(` call-site matrix (production call sites)

Rule: **MUST-THREAD** = the path's output depends on the resolved `mcp-config.format` or `frontmatter-mechanism` (generation or its checks) → pass `project_config`. **SURFACE-IRRELEVANT** = the path only uses provider names, `agents_dir`, `context_file`, capabilities/hooks, or is a pure key lookup → may keep the one-arg call.

| # | Call site | Class | Reason |
|---|-----------|-------|--------|
| 1 | `scripts/lib/sync_pipeline.py:155` | **MUST-THREAD** | generation: resolved format/mechanism drive emitted MCP + frontmatter. |
| 2 | `scripts/lib/agent_sync.py:728` (`collect_artifact_findings`) | **MUST-THREAD** | `--check`/`--validate` must validate the same surface generation emitted. |
| 3 | `scripts/lib/consistency/artifact_contracts.py:89` | **MUST-THREAD** | registry-wide artifact contract for the generated tree. |
| 4 | `scripts/lib/consistency/model_contracts.py:95` | **MUST-THREAD** | validates emitted frontmatter/model contract of the generated tree. |
| 5 | `scripts/sync.py:571` (cleanup preview) | **MUST-THREAD** | dry-run cleanup must agree with the real sync's resolved targets. |
| 6 | `scripts/lib/cli_commands.py:220` (test-repo validation) | **MUST-THREAD** | generates + validates a test repo. |
| 7 | `scripts/lib/cli_commands.py:806` (`_handle_deactivate_providers`) | **MUST-THREAD** | calls `sync_context_for_provider` (regenerates content). |
| 8 | `scripts/lib/cli_commands.py:841` (`_handle_activate_providers`) | **MUST-THREAD** | calls `sync_context_for_provider` (regenerates content). |
| 9 | `scripts/lib/cli_commands.py:662` (`only-variables`) | SURFACE-IRRELEVANT | writes `AGENTS_DIR`/routing vars; surface does not change those. |
| 10 | `scripts/lib/cli_commands.py:1218` (sync log) | SURFACE-IRRELEVANT | logs the provider-name list only. |
| 11 | `scripts/lib/config.py:635` | SURFACE-IRRELEVANT | subagent permission-mode resolution. |
| 12 | `scripts/lib/config.py:1373` | SURFACE-IRRELEVANT | routing groups / context-file hints. |
| 13 | `scripts/lib/config.py:1409` | SURFACE-IRRELEVANT | `AGENTS_DIR` auto-injection. |
| 14 | `scripts/lib/config.py:1418` | SURFACE-IRRELEVANT | `AI_PROVIDER` list. |
| 15 | `scripts/lib/config.py:1491` | SURFACE-IRRELEVANT | progress-chat-push gate (hook capability). |
| 16 | `scripts/lib/config.py:2056` | SURFACE-IRRELEVANT | routing tool definitions. |
| 17 | `scripts/lib/checkpoint.py:84` | SURFACE-IRRELEVANT | progress tier from hook capability. |
| 18 | `scripts/lib/config_audit.py:466` | SURFACE-IRRELEVANT | registered-provider key set. |
| 19 | `scripts/lib/setup.py:234` | SURFACE-IRRELEVANT | provider-name choices. |
| 20 | `scripts/lib/viz.py:479` | SURFACE-IRRELEVANT | agent hierarchy build. |
| 21 | `scripts/lib/viz.py:712` | SURFACE-IRRELEVANT | `bash_tool_name` lookup. |
| 22 | `scripts/lib/consistency/context_size.py:80` | SURFACE-IRRELEVANT | context-file size; filename unchanged by surface. |
| 23 | `scripts/lib/consistency/context_topology.py:125` | SURFACE-IRRELEVANT | context topology; unaffected by surface format. |
| 24 | `scripts/lib/providers.py:259` (`registered_provider_names`) | SURFACE-IRRELEVANT | internal: key set only. |
| 25 | `scripts/lib/providers.py:339` (`_framework_provider_entry`) | SURFACE-IRRELEVANT | internal: dedicated-context capability lookup. |
| 26 | `scripts/admin-server.py:1531` (injection drift) | SURFACE-IRRELEVANT | injection paths; not format-dependent. |
| 27 | `scripts/admin-server.py:1547` (deactivation status) | SURFACE-IRRELEVANT | active-provider list. |
| 28 | `scripts/admin-server.py:1585` / `:1608` (deactivate/activate) | SURFACE-IRRELEVANT | directory-level zip/restore, no content regeneration. |
| 29 | `scripts/admin-server.py:4440` (model-inherit check) | SURFACE-IRRELEVANT | provider existence only. |
| 30 | `scripts/admin-server.py:5146` / `:5165` / `:5194` (backup/restore) | SURFACE-IRRELEVANT | archive operations, no content resolution. |
| 31 | `scripts/lib/cli_commands.py:786` (`_handle_deactivation_status`) | SURFACE-IRRELEVANT | active-provider list for status only. |
| 32 | `scripts/lib/cli_commands.py:879` (`_handle_backup`) | SURFACE-IRRELEVANT | archive creation, no content resolution. |
| 33 | `scripts/lib/cli_commands.py:903` (`_handle_restore`) | SURFACE-IRRELEVANT | archive restore, no content resolution. |
| 34 | `scripts/lib/cli_commands.py:924` (`_handle_list_backups`) | SURFACE-IRRELEVANT | lists archives only. |
| 35 | `scripts/lib/cli_commands.py:1025` (`_provider_config = _load_pc(agent_meta_root)`, alias `as _load_pc` at `:1023`) | SURFACE-IRRELEVANT | feeds strict-hook/containment consistency checks that read capabilities, not surface format/mechanism. |

Test call sites under `tests/` are out of scope for the matrix (they construct their own inputs); tests whose expectations depend on the surface must pass the project config explicitly.

---

## 9. Trace-Anker

```
parent-spec-id: SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30
spec-id:        SPEC-ADMIN-UI-OPENCODE-SURFACE-AMENDMENT-2026-10-03
```

The implementation plan derived from this amendment MUST reference both anchors. This amendment does not alter the parent spec's `Status` or AC numbering.

> **Prompt-injection note:** all anchors above were read directly from the repository and verified against HEAD on `feat/provider-audit-opencode-v2`; no fetched/third-party content was consumed for this document.
