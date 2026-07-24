UI Spec — SCR-MODELS-01: "Models & Pricing" — models.dev-sourced table

> Feeds a `developer` implementation task. Target file: `docs/ui/admin-ui.html`,
> function `viewModels()` → `renderModelsDevTable()` (currently ~L5895–6069) and its
> call site `render()` (~L5705–5764). No new CSS classes unless explicitly listed below
> as "new". Reuse existing classes wherever possible — the goal is 1:1 visual parity
> with `renderRegistryTable()` (~L5769–5892).

---

## 1. Screen / component identity

| Field | Value |
|---|---|
| Screen ID | SCR-MODELS-01 |
| Screen name | Models & Pricing → models.dev source view |
| Purpose | Let the user browse/import model pricing data sourced from models.dev, filtered by default to the providers actually configured in the project, with the same visual language as the curated registry table |
| Audience | Project maintainer configuring `ai-providers` / model pricing in the admin UI |
| Parent screen | `viewModels()` — shared header/source-toggle already rendered once for both sub-views |

## 2. Problem with current state (as-is, for context)

Both `renderRegistryTable()` and `renderModelsDevTable()` already emit a `<table class="data">` — so the two views are not literally "table vs. card-grid" at the DOM level. The perceived inconsistency ("Haufen Scheiße") comes from divergent detail styling that makes the models.dev table look like a different, cheaper component:

1. **Capability tags** (`renderModelsDevTable`, ~L6024–6037): custom inline-styled `<span>`s with ad-hoc `rgba(...)` backgrounds, `border-radius:3px`, `padding:1px 5px`, `font-size:0.7em` — visually unrelated to the `.badge` pill component (`border-radius:10px`, `padding:1px 8px`, mono font) used everywhere else, including the registry table's cost-source badges (`badge ok` / `badge warn`, ~L5860–5861).
2. **Capability filter buttons** (~L5958–5961): use bare `class="badge"` but are **not** wrapped in a `.quick-filter-strip` container, so they don't inherit `.quick-filter-strip .badge` cursor/hover/active-blue styling (CSS ~L662–682) that the provider strip right above them (~L5917) does get. Net effect: two visually different button styles stacked directly on top of each other.
3. **Filtering UX split**: registry table puts provider/model/category filters *inside* the table header cells (`mkSelect`/`mkText` appended via `el("br")` inside `<th>`, ~L5836–5838). The models.dev table instead uses a separate control bar above the table (~L5952–5962) for model-name search and capability filters. Provider filtering itself already correctly reuses `quick-filter-strip` (~L5917), so only the *model name* search input is misplaced relative to the registry convention.
4. **Registry-only / fallback indicator** for providers like Mammouth (~L5737–5741) uses ad-hoc inline `text-decoration:line-through` + opacity, not the `.badge` component the rest of the page uses for source provenance (`badge ok` / `badge warn`).
5. **No default scoping to configured providers** — `allProviderIds` (~L5905) includes every models.dev provider; the "All Providers" quick-filter button (~L5918) shows literally all of them, with configured ones merely sorted first. There is no toggle to collapse the view to configured-only.

None of this requires a new layout paradigm — it requires column/row-level styling parity with the registry table plus a default-scope filter.

## 3. Redesign — column layout

Keep the existing `<table class="data">` structure. Column order changes to mirror the registry table's information hierarchy (identity → classification → cost → provenance → action):

| # | Header | Content | Notes |
|---|--------|---------|-------|
| 1 | *(none, 40px)* | — | **Remove.** Registry table's checkbox column is for bulk enable/disable, which doesn't apply to models.dev rows (they aren't part of the registry yet). Do not add a fake checkbox. |
| 2 | `Provider` | `m._providerName` | New column, was previously folded after Model. Matches registry's Provider-first order. Inline header filter: reuse `mkSelect`-equivalent (see §5). |
| 3 | `Model (Name & ID)` | `<strong>` name + `<br>` + `<small class="muted mono">` id — **exact markup reuse from registry** (~L5855), optionally append the truncated description line already present (~L6015) as a third line inside the same cell | Header label copied verbatim from registry ("Model (Name & ID)") for consistency |
| 4 | `Capabilities` | Badge row, see §4 | Same conceptual slot as registry's "Category" column — classification, not cost |
| 5 | `Input Cost ($/1M)` | `fmtCost(co.input)` in `<td class="mono">` | Header label copied verbatim from registry |
| 6 | `Output Cost ($/1M)` | `fmtCost(co.output)` in `<td class="mono">` | Header label copied verbatim from registry |
| 7 | `Context` | `fmtCtx(limit.context)` in `<td class="mono">` | Unchanged, keep as own column (registry has no equivalent, so no renaming needed) |
| 8 | `Source` | Provenance badge, see §6 | Replaces bare "Import" semantics with a provenance-first framing; import action moves here as secondary content |
| 9 | `Actions / Ref` | Import button **or** "In Registry" badge **or** "No pricing" muted text (existing logic ~L6042–6061, unchanged) | Header label copied verbatim from registry's action column so both tables end on the same visual note |

Rationale for moving cost columns after Capabilities: registry table order is Provider → Model → Category → Input → Output → Cost Factor → Status → Actions. models.dev has no "Status" (enable/disable) or "Cost Factor" concept, so Capabilities takes the classification slot and Source/Actions take the trailing provenance+action slot — same rhythm, different content.

## 4. Capabilities column — redesign

Replace the ad-hoc rgba/emoji spans with `.badge` instances, keeping the emoji glyphs (they carry real information density in a narrow column) but conforming to the badge component's shape/spacing:

```
<span class="badge {modifier}">🧠</span>   reasoning   → badge.modern   (purple, existing modifier, semantically "advanced")
<span class="badge {modifier}">🔧</span>   tool_call   → badge.ok       (green, existing modifier, "capability present/positive")
<span class="badge {modifier}">📎</span>   attachment  → badge.hybrid   (blue, existing modifier)
<span class="badge">📋</span>              structured  → base badge, no modifier (neutral gray, matches "optional" weight)
<span class="badge">👁</span> / 🖼         vision in/out → base badge
<span class="badge">🎤</span>              audio       → base badge
<span class="badge optional">{knowledge}</span>  knowledge cutoff → badge.optional (already the correct modifier for "informational, non-actionable" — registry uses it for Cost Factor's "Calc" tag)
```

Wrap the tag row in the same flex container (`display:flex;gap:2px;flex-wrap:wrap;` — this part is fine, keep it), just swap the child element construction from custom-styled `span` to `el("span", { class: "badge <modifier or none>" }, [glyph])`. No new CSS needed — all modifiers used here (`modern`, `ok`, `hybrid`, `optional`) already exist (CSS ~L345–352).

## 5. Filters — redesign

**Move the model-name search into the table header**, matching the registry's `mkText`/`mkSelect`-inside-`<th>` pattern:

- `Model (Name & ID)` header gets `el("br")` + a text input styled identically to `mkText` (~L5818–5822) bound to `state.filterModel`.
- `Provider` header gets `el("br")` + a `<select>` styled identically to `mkSelect` (~L5811–5817), populated from `configuredFirst` (or all providers when "Show all providers" is on, §7) — this becomes a **second**, exact-match way to filter provider in addition to the quick-filter-strip buttons above the table. Both write to the same `state.filterProvider`; keep them in sync (selecting a strip button should update the select's value and vice versa).

**Capability filter buttons**: fix the styling bug from §2.2 by wrapping them in a `quick-filter-strip`-classed container instead of the bare flex `ctrl` div, e.g.:

```
ctrl (existing flex row, keep for the search-adjacent layout)
  └─ capsStrip = el("div", { class: "quick-filter-strip", style: "margin:0;" })
       └─ 5× el("button", { class: "badge" + (active ? " active" : "") }, [emoji])
```

This gives the capability toggles the same hover/cursor/active-blue treatment the provider strip already has, closing the visual gap between the two adjacent control rows.

Keep the free-text model search where useful as a quick top-of-table affordance too **only if** it's redundant with the header input causes confusion — recommendation: **remove the separate top control-bar text input** (~L5953–5957) entirely once the header input exists, to avoid two search boxes for the same field. Keep only the capability badge row in the top control bar.

## 6. Provenance / fallback indicator ("Source" column, §3 row 8)

Applies to every row, not just Mammouth-style fallbacks — mirrors the registry table's per-cost-cell `badge ok`/`badge warn` provenance tags (~L5860–5861) so both tables communicate data provenance the same way:

| Case | Badge |
|---|---|
| Row's provider has live models.dev data (`d.source === "sdk"` or `"api"`) | `<span class="badge ok">models.dev</span>` |
| Row's provider is in `REGISTRY_ONLY` (e.g. Mammouth, Continue) **or** has no `PROVIDER_MAP` entry — i.e. curated-fallback data, no real models.dev match | `<span class="badge warn">Registry (curated)</span>` |
| models.dev fetch itself errored (`d.source === "error"`) | `<span class="badge" style="color:var(--accent-red);border-color:rgba(248,81,73,0.4);">unavailable</span>` — reuses the red tone already defined for `badge.required`, no new color needed |

This also replaces the ad-hoc strikethrough/opacity styling in the "Per provider" override row (~L5737–5741): swap the custom inline-styled `wrap_el`/label for the same `badge ok` / `badge warn` pair, e.g. `isRegistryOnly ? "badge warn" : "badge ok"`, with the label text becoming `"registry"` / `"models.dev"` respectively (content unchanged, only the visual container changes from a hand-rolled pill to the shared `.badge` component). Keep the `title="Not available in models.dev — registry only"` tooltip.

If real Mammouth data becomes available later (per the parallel "replace hardcoded workaround" task), the *only* change needed here is removing `"Mammouth"` from `REGISTRY_ONLY` and adding a `PROVIDER_MAP` entry — the badge logic above is data-driven and requires no further UI change. Until then, any provider lacking a models.dev match (including a future provider that simply has no data yet) gets the same `badge warn "Registry (curated)"` treatment — the indicator is generic, not Mammouth-specific.

## 7. Default provider filter + "Show all providers" toggle

**Behavior:**
- On load, `state.filterProvider` stays `""` (no single-provider filter) but the **candidate provider set** for the quick-filter-strip, the header `<select>`, and the rendered `allModels` list all default to `configuredFirst` only (currently `Claude`, `Opencode`, `Mammouth`, `Gemini` per `.meta-config/project.yaml` → `ai-providers:`). `otherProviders` (unconfigured) are hidden entirely, not shown in a secondary dropdown, until the toggle is on.
- Add `state.showAllProviders = false` to the view state.
- New toggle placed at the **right end of the provider quick-filter-strip row** (~L5917–5949 area), using the existing reusable `toggleField(value, onChange)` helper (defined ~L1663, already used at 8+ other call sites in this file — e.g. ~L1664, ~L2915, ~L3989) so it renders as the same slider switch used elsewhere on the page:

```
strip.appendChild(el("span", { style: "margin-left:auto;font-size:0.82em;opacity:0.7;" }, ["Show all providers"]));
strip.appendChild(toggleField(state.showAllProviders, v => { state.showAllProviders = v; render(); }));
```

  (`margin-left:auto` on the label pushes the toggle to the far right of the flex strip — `quick-filter-strip` is already `display:flex`, no extra wrapper needed.)

- When `state.showAllProviders === false`:
  - Quick-filter-strip shows: `All Providers` button (label becomes `"All Configured"` for clarity) + one badge per configured provider (unchanged from current `configuredFirst.forEach` loop) + **no** "Other providers" dropdown.
  - `allProviderIds` used for the "All" case is replaced by `configuredFirst` (not the full provider list).
- When `state.showAllProviders === true`:
  - Current behavior is restored verbatim: `configuredFirst` badges + `otherProviders` dropdown (~L5935–5948), and the "All" button's underlying model set is the full `allProviderIds`.
- The toggle state must be preserved across `render()` calls (it already lives on `state`, same lifecycle as `state.filterProvider`).

**Why this placement:** it sits directly adjacent to the provider filter it modifies (discoverable, no separate settings area needed), and reuses the exact same toggle component already used for binary on/off switches elsewhere in this admin UI, so no new interaction pattern is introduced.

## 8. States

| State | Rendering |
|---|---|
| Loading | Shared with registry view — existing `state.loading` block (~L5757–5760), unchanged |
| No models.dev data at all | Existing `.empty` div, unchanged (~L5900) |
| No models match current filters | Existing `.empty` div, unchanged (~L5989–5992) — message stays accurate since it already says "No models match filters" |
| Configured-only view is empty (e.g. all configured providers are registry-only, like a Mammouth+Continue-only project) | New case: show `.empty` with text `"No models.dev data for configured providers. Toggle \"Show all providers\" to browse the full catalog."` — must appear *instead of* the generic "No models match filters" message so the user understands *why* the table is empty and what to do about it |
| Normal / populated | Table as specified in §3–§6 |

## 9. Accessibility

- All new `<select>`/`<input>` header controls: reuse `mkSelect`/`mkText` verbatim (already accessible — native form controls, labelled via adjacent header text).
- `toggleField` checkbox: ensure the visible `"Show all providers"` text is wrapped so it's associated with the control — either place the text and the `toggleField()` output inside the same `<label>` (matching how other `toggleField` call sites in this file already pair a label element, e.g. ~L2265, ~L2375) rather than as a floating sibling `<span>`.
- Badge-based provenance/capability tags are decorative + supplementary; the underlying data (provider name, cost values, capability booleans) must remain reachable via the cell's text content for screen readers — do not convey capability solely through emoji color; keep the emoji as text content (already the case) rather than as CSS `background-image` or icon font.
- Maintain existing `table.data` semantics (`<thead>`/`<tbody>`, real `<th>` header cells) — do not flatten to `<div>`-based rows.

## 10. Non-goals / explicitly out of scope for this spec

- No new CSS classes are introduced. Every visual primitive referenced above (`badge`, `badge.ok/.warn/.modern/.hybrid/.optional`, `quick-filter-strip`, `table.data`, `mono`, `muted`, `toggle`/`toggleField`) already exists in `docs/ui/admin-ui.html`.
- No changes to the Import action logic (~L6042–6061) beyond relocating its column position — the enable/disable/import API calls are unchanged.
- Real Mammouth models.dev data support is a data/backend concern (`PROVIDER_MAP` + `REGISTRY_ONLY` + `/api/models-dev` response shape) — this spec only defines how the UI must react once that data exists (§6), it does not specify the data-fetching change itself.

## 11. Implementation reuse map (quick reference for `developer`)

| Need | Reuse from |
|---|---|
| Table shell | `table.data`, `<thead>`/`<tbody>` — copy structure from `renderRegistryTable` ~L5832–5845 |
| Header inline filter (text) | `mkText()` ~L5818–5822 |
| Header inline filter (select) | `mkSelect()` ~L5811–5817 |
| Model name/id cell markup | `<strong>` + `<br>` + `<small class="muted mono">` ~L5855 |
| Cost cell markup | `<td class="mono">` pattern ~L5858–5861, `fmtCost()` (already local to `viewModels`) |
| Provenance badge | `.badge.ok` / `.badge.warn` pattern ~L5860–5861 |
| Capability badges | `.badge`, `.badge.modern`, `.badge.ok`, `.badge.hybrid`, `.badge.optional` (CSS ~L336–352) |
| Provider quick filter | `quick-filter-strip` + `.badge` buttons, existing loop ~L5917–5949 (extend, don't replace) |
| Show-all-providers switch | `toggleField(value, onChange)` ~L1663, styled via `.toggle`/`.slider` CSS ~L283–305 |
| Empty state | `.empty` class ~L644–650 |

---

STATUS: done
SCREENS: 1
DESIGN_SYSTEM: 0 new components (8 existing components reused: table.data, badge + 5 modifiers, quick-filter-strip, toggleField)
JOURNEYS: 1 (maintainer browses/imports models.dev pricing scoped to configured providers)
SPEC_FILE: docs/ui/specs/models-dev-table-redesign.md
