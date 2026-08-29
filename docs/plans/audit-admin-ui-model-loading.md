# Audit: Admin-UI Model / Pricing Loading (All Providers)

**Branch:** `fix/admin-ui-model-loading`
**Scope:** `scripts/admin-server.py`, `docs/ui/admin-ui.html`, `config/pricing-overlay.yaml`,
`config/model-curation.yaml`, `config/generated/model-registry.json` (read-only)
**Symptoms audited:** (1) OpenCode models don't load in the Admin-UI, (2) prices don't load
cleanly in the web UI, (3) per-provider datalists deliver wrong/missing models — OpenCode
needs the `opencode-go/` prefix.

---

## 1. Data-flow chain (as audited)

```
Discovery (sync.py --update-models → scripts/lib/model_discovery.py)
  └─> config/generated/model-registry.json                    [VERIFIED OK — 56 models:
       ids: anthropic = bare (claude-sonnet-4-6, anthropic/claude-opus-4.8-fast),
            opencode-go = namespaced (opencode-go/<raw_id>)]
         │
         ├─> admin-server.py _collect_models()                [OK]
         │     ├─ merges config/pricing-overlay.yaml per (provider, model_id)
         │     ├─ applies curation "disabled" via /api/models/active
         │     └─ serves /api/models and /api/models/active
         │
         └─> admin-server.py _load_models_dev_data()          [PROBLEM AREA]
               ├─ 1. SDK snapshot  node_modules/@opencode-ai/models/dist/snapshot.js
               ├─ 2. live API      https://models.dev/catalog.json
               ├─ class-level cache (sdk: forever, api: 1h, failure: not cached)
               └─ _apply_pricing_overlay() (override + curated mammouth/continue)
                     │
                     ├─> /api/models-dev                      [OK online; broken offline]
                     └─> /api/model-suggestions               [BROKEN — see RC1a/RC3a/RC3b]
                           │
                           v
docs/ui/admin-ui.html
  ├─ viewModels(): registry table / models.dev table          [PROBLEM AREA — RC1c/RC2b]
  ├─ per-provider datalists (Provider Tier Overrides #/project/provider-tier-overrides,
  │  ai-providers model-tiers editor, Tier Presets)           [PROBLEM AREA — RC3a/RC3b/RC3c]
  └─ saved ids (provider-tier-overrides / model-tiers / tier-presets)
        │
        v
scripts/lib/roles.py resolve_model() → _resolve_tier_to_model()
  └─ tier values are passed through VERBATIM into the generated
     `model:` frontmatter field → the persisted id MUST be the runnable id
     (for OpenCode: "opencode-go/<raw>", for Claude: bare).
```

Provider mapping is consistent on both sides (verified identical):
`PROVIDER_MODELSDEV_SLUGS` (server) ≡ `PROVIDER_MODELSDEV_MAP` (UI):
Claude→anthropic, Gemini→google, Opencode→opencode-go, Copilot→github-copilot;
registry-only: Mammouth, Continue (= `CURATED_ONLY_PROVIDER_KEYS` ≡
`MODELSDEV_REGISTRY_ONLY_PROVIDERS`).

**Live verification performed** (server started on 127.0.0.1:7491):

| Endpoint | Online result | Offline (proxied-to-dead) result |
|---|---|---|
| `/api/models` | 56 models, overlay prices applied (`claude-fable-5` → 10/50 Overlay) | identical (registry-based, no network) |
| `/api/models-dev` | `source: api`, 208 providers, opencode-go 33 models, overlay patched | `source: error`, `providers: {}` (+ curated mammouth only) |
| `/api/model-suggestions?provider=Opencode` | 33 models, **bare** ids (`kimi-k2.7-code`) | `{"models": []}` — **silently empty** |
| `/api/model-suggestions?provider=Gemini` | **51 mixed models from ALL providers** (anthropic + opencode-go) | same |
| `/api/model-suggestions?provider=Copilot/Continue` | 51 mixed models (all-provider soup) | same |

---

## 2. Root causes per symptom

### Symptom 1 — "Available LLMs for OpenCode don't load"

- **RC1a — no fallback when the models.dev catalog is unavailable.** OpenCode is persisted
  `modelsdev` in `model-source-preference`. `_handle_get_model_suggestions` →
  `_suggestions_from_models_dev()` returns `[]` without any fallback and without surfacing
  the error when `_load_models_dev_data()` yields `{"source": "error"}` or the
  `opencode-go` node is missing. Every OpenCode datalist is silently empty.
- **RC1b — fetch errors are swallowed and re-attempted per request.**
  `_load_from_models_dev_api()` catches **all** exceptions and returns `None` (no reason is
  recorded); a total failure is not negatively cached, so *every* request re-attempts a
  30 s-timeout fetch — against a blackholed network the UI hangs rather than fails.
- **RC1c — UI registry table wipes rows of modelsdev-overridden providers.**
  `modelsDevRowsAsRegistryRows()` returns `[]` when the models.dev payload lacks the
  provider node. With Claude + Opencode overridden to `modelsdev` (both are), an offline
  catalog empties **both** sources: the registry table drops all its rows and shows the
  misleading "No models in registry. Run sync.py --update-models." even though
  model-registry.json is fully populated.

### Symptom 2 — "Prices don't load cleanly"

- **RC2a — models.dev import persists the wrong id form.** `_handle_post_models_dev_import()`
  writes the **bare** models.dev id under the provider key (e.g.
  `opencode-go: { kimi-k2.7-code: ... }`), but `_collect_models()` looks the overlay up by
  the **registry** id (`opencode-go/kimi-k2.7-code`). Imported prices for opencode-go never
  appear in the registry view — a silent pricing no-op.
- **RC2b — offline models.dev table degrades to one provider with no prices.**
  `/api/models-dev` with `source: "error"` serves only the curated mammouth node; the
  models.dev table then shows a single provider with `—` costs, and (via RC1c) the registry
  table empties as well. The error payload carries no human-readable reason
  (`"No data available"`), so nothing explains *why*.
- **RC2c — the ↻ Refresh button cannot refresh SDK-sourced data.** The SDK snapshot is
  cached forever and `_handle_post_models_dev_refresh()` re-reads the same local
  `snapshot.js` — a stale bundled snapshot pins stale pricing for the lifetime of the
  process even after pressing Refresh.
- **RC2d — curation `disabled` ids drifted out of matching range.** Registry id formats
  changed across discovery generations (`claude-opus-4-1` → now
  `anthropic/claude-opus-4.1`). Exact-match disabled checks miss the old ids, so
  `config/model-curation.yaml` entries written against an older registry silently stop
  disabling (currently: `claude-opus-4-1`; its registry counterpart is served as active).

### Symptom 3 — "Autocomplete delivers wrong/missing models; OpenCode needs `opencode-go/`"

- **RC3a — modelsdev suggestions return bare ids where the runnable id is namespaced.**
  `_suggestions_from_models_dev()` deliberately returns raw models.dev ids
  ("never re-applied as a prefix") — but `roles.py::_resolve_tier_to_model()` persists
  whatever is selected verbatim, and the runnable OpenCode id IS `opencode-go/<raw>`
  (see `model_discovery.py:341` and the existing `model-tiers` values). Saving any
  modelsdev-sourced suggestion writes a broken, non-runnable model id.
- **RC3b — registry suggestions degrade to an all-provider soup.**
  `_suggestions_from_registry()` falls back to **all** active models when the provider's
  tier values cannot be mapped to a registry slug. That hits Gemini (bare `gemini-*` tier
  ids are not in this registry), Copilot and Continue (empty tier maps): their datalists
  offer 51 cross-provider models that would corrupt config if selected.
- **RC3c — Provider Tier Overrides datalist omits current values.** The ai-providers tier
  editor and Tier Presets datalists append the provider's *current* tier values as options;
  the Provider Tier Overrides view does not — after a failed suggestions load the user
  cannot even re-select the currently persisted value.

---

## 3. Fixes implemented

### Server (`scripts/admin-server.py`)

1. **Registry-conform suggestion ids (per-model resolution)** — `_registry_model_ids_by_provider()`
   maps each registry provider slug to its registry id set (same source `_collect_models()`
   reads); `_resolve_registry_model_id()` resolves a bare models.dev id per model:
   bare id exists → bare; namespaced `<slug>/<raw>` exists → namespaced; neither →
   namespaced only when EVERY registry id of that provider is namespaced (unanimity
   fallback). This is required because registry id conventions are **per model, not per
   provider**: the real registry carries anthropic with 13 bare canonical ids AND 18
   `anthropic/…`-prefixed OpenRouter extras, so a provider-wide binary heuristic
   (review iteration 1) blanket-prefixed canonical Claude suggestions into non-runnable
   `anthropic/claude-opus-5` ids. No provider names are hardcoded; a not-yet-synced
   opencode-go model stays runnable (`opencode-go/<raw>`) via the unanimity fallback
   while a mixed-convention provider defaults to the canonical bare form.
   `_suggestions_from_models_dev()` applies the resolver to every suggestion.
2. **Honest degradation instead of silent emptiness** — `_handle_get_model_suggestions()`
   degrades `modelsdev` → registry suggestions when the models.dev path yields nothing
   (catalog unavailable, node missing/empty) and reports the *effective* source used —
   mirroring the existing registry-only-provider forcing for Mammouth/Continue.
3. **No more all-provider soup** — `_suggestions_from_registry()` returns `[]` (not all
   models) when no registry slug can be inferred for a provider.
4. **Import writes registry-conform overlay keys (per-model)** — `_handle_post_models_dev_import()`
   persists the overlay key under the EXACT registry id `_collect_models()` looks the
   price up by, using the same `_resolve_registry_model_id()` resolution as the
   suggestions (iteration 1's provider-wide rule wrongly wrote `anthropic/<bare>` keys
   for canonical models, making the imported price permanently invisible in
   `/api/models`). Also fixed a latent first-import crash: the unconditional backup step
   read a possibly nonexistent `pricing-overlay.yaml` (FileNotFoundError → 500); the
   backup now only runs when the file exists.
5. **Resilient models.dev loading** — `_load_models_dev_data(force_refresh=False)`:
   - negative-caches the total-failure payload for 60 s (`_MODELS_DEV_ERROR_TTL_SECONDS`)
     so an unreachable network cannot turn every request into a fresh 30 s blocking fetch;
   - **also stamps the negative cache when serving an expired STALE cache on failure**
     (review iteration 2 / M1: without the stamp, every request re-attempted the fetch
     despite a stale payload being served);
   - records the fetch-failure reason (`_models_dev_last_fetch_error`) and returns it in
     the error payload's `error` field;
   - `force_refresh=True` (used by the ↻ endpoint) tries the **live API first**, then the
     SDK snapshot, so Refresh actually reaches the network even with a stale snapshot.
6. **Drift-tolerant curation matching** — module-level `_normalized_model_id()`
   (lowercase, strip `<provider>/` namespace, dots→dashes) is used for the `disabled`
   check in `_collect_models()`, so ids written against older registry generations still
   match (e.g. `claude-opus-4-1` ≡ `anthropic/claude-opus-4.1`).

### UI (`docs/ui/admin-ui.html`)

7. **Registry-table fallback** — `modelsDevRowsAsRegistryRows()` falls back to the
   provider's registry rows (flagged `_registryFallback`, warn badge "registry fallback")
   when the models.dev node is unavailable, instead of wiping the provider from the table.
8. **models.dev-table fallback** — candidate provider ids now include configured providers
   missing from the catalog; `getEffectiveModelsDevRows()` substitutes registry rows
   (Source badge "registry (models.dev offline)") when the catalog node is
   missing/empty; provider-name resolution in the filter strip / header select no longer
   dereferences a missing catalog node.
9. **Honest empty states** — when `d.source === "error"` the models.dev table shows the
   server-provided failure reason and remediation hints instead of the generic
   "no data for configured providers" message.
10. **Provider Tier Overrides datalist** now appends the provider's existing override
    values (consistent with the tier editor and Tier Presets views).

### Not changed (deliberately)

- `config/generated/model-registry.json` (discovery output verified correct),
  `scripts/lib/model_discovery.py`, `tests/test_model_discovery.py` — discovery behaves
  as designed; the defects are in the serving/UI layer.
- `config/model-curation.yaml` contents (the drifted entry `claude-opus-4-1` is now
  matched by the tolerant comparison; no data migration needed).
- The "exclusive source" architecture: the modelsdev → registry degradation is a
  fail-over that *replaces* the result and reports the honest source, never a mix of both
  catalogs in one response.

---

## 4. Regression coverage added

- `tests/test_admin_server.py` (19 new tests; 51 total in the file):
  - `TestSuggestionsModelsDevPrefix` — prefixed ids for unanimously-namespaced providers
    (incl. not-yet-synced models), bare ids for anthropic.
  - `TestMixedConventionRegistryResolution` — the per-model resolution against a MIXED
    fixture (anthropic bare canonical + `anthropic/…`-prefixed OpenRouter extras):
    canonical Claude suggestions stay bare, OpenRouter extras map to their namespaced
    registry id, unsynced opencode-go models stay prefixed; end-to-end import test
    asserting the imported price actually surfaces via `_collect_models()`.
  - `TestSuggestionsDegradation` — modelsdev→registry fail-over on catalog failure
    (honest `source: registry`), empty node degradation, modelsdev success path keeps
    serving prefixed ids, and registry no-slug → `[]` (no cross-provider soup).
  - `TestModelsDevImportOverlayKey` — import writes registry-conform keys for namespaced
    and bare providers, and creates the overlay file on first-ever import (backup-step
    regression).
  - `TestCollectModelsDisabledNormalization` — drifted disabled id matches current
    registry id; exact ids keep working.
  - `TestLoadModelsDevDataResilience` — negative cache (second failing call does not
    re-fetch within TTL), stale-cache serving **stamps the negative cache** (repeated
    requests without re-fetch, retry after TTL), `force_refresh` prefers the live API
    over an existing SDK snapshot (with urlopen mocked so tests never touch the network),
    successful load clears the negative cache, error payload carries the fetch-failure
    reason.
- `tests/browser/test_models_page.py` (2 new tests):
  - OpenCode datalist candidates are registry-runnable (`opencode-go/`-prefixed) AND
    Claude datalist candidates stay bare (no `anthropic/…` leakage from the mixed
    convention) in the Provider Tier Overrides view — holds in both modelsdev and
    (degraded) registry mode.
  - Registry table renders rows despite modelsdev-overridden providers (no wipe).

### Browser verification performed

- Online: models.dev table renders 47 configured-provider models (Anthropic 13, Google 0,
  Mammouth Code 1, OpenCode Go 33), zero console errors.
- Offline (fetch forced to fail): ERR badge shown; registry table keeps ALL rows with a
  "registry fallback" badge; models.dev table renders 57 rows with
  "registry (models.dev offline)" provenance badges instead of a near-empty table.
- During browser verification a JS TDZ crash
  (`Cannot access 'configuredProviderIds' before initialization`) introduced by an early
  draft of fix 8 was caught via console messages and fixed by reordering the declarations.

---

## 5. Residual observations (out of scope, no action taken)

- The SDK snapshot path (`node_modules/@opencode-ai/models`) does not exist in this repo;
  consumers with a stale snapshot get API data on ↻ Refresh now, but the *initial* load
  still prefers the snapshot by design ("SDK primary").
- `config/model-curation.yaml` contains legacy entries that match nothing
  (`~anthropic/claude-fable-latest`); they remain inert.
- `_suggestions_from_models_dev` for Gemini requires `model-source-preference:
  {Gemini: modelsdev}` to deliver useful suggestions, because the registry contains no
  google models in this project — the per-provider source dropdown is the intended lever.
