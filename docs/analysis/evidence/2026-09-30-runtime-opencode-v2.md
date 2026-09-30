# Runtime Evidence — Opencode **v2** (installability + schema validation)

- **Date:** 2026-09-30 · **Repo:** `/home/hermes/repos/agent-meta` · **Branch:** `feat/provider-audit-opencode-v2` (no git mutation).
- **Installed harness (v1):** `opencode --version` → `1.18.31` (npm-global `opencode-ai@1.18.31`).
- **v2 candidate:** npm package **`@opencode/cli`** @ dist-tag `latest` → **2.0.20**; binary links referenced in the v2 docs → `2.0.6`.
- **Isolation:** install prefix `/var/tmp/opencode-audit/opencode-v2/`, scratch project `/var/tmp/opencode-audit/scratch-v2/`
  (copy of the generated `.opencode/agents` + adapted `opencode.json`), XDG dirs redirected into the scratch. Repo artifacts **not modified**.
- **Hypotheses source:** `2026-09-30-provider-audit-docs-part1.md` §4 (OC2-1…OC2-5), v2 docs `https://v2.opencode.ai/docs/{,agents/,config/}`.
- **Verdict key:** RUNTIME-OK / RUNTIME-REJECTED / STATIC-OK / STATIC-MISMATCH / UNVERIFIABLE.
- **Scope note (critical):** v2 is **not** a tag of `opencode-ai`. `opencode-ai` dist-tags `latest=1.18.33`, `next`/`beta`/`dev` are
  `0.0.0-*-snapshot` builds **of v1**; v2 ships under a **separate** package `@opencode/cli`.

---

## 1. Installierbarkeit → **JA (RUNTIME)**

```
$ npm view opencode-ai dist-tags
  { latest: '1.18.33', next: '0.0.0-next-202606270058', beta: '0.0.0-beta-202608110357',
    dev: '0.0.0-dev-202609301753', tui-v2: '0.0.0-tui-v2-202606261840', … }   # ← all v1-lineage
$ npm view @opencode/cli version           → 2.0.20
$ npm view @opencode/cli dist-tags         → { latest: '2.0.20', beta: '0.0.0-beta-19507', dev: '0.0.0-dev-20335', reserved: '0.0.0-reserved' }

$ npm install --prefix /var/tmp/opencode-audit/opencode-v2 @opencode/cli@latest     # rc=0
$ /var/tmp/opencode-audit/opencode-v2/node_modules/.bin/opencode --version
  opencode v2.0.20
$ ls node_modules/.bin/                    → opencode -> ../@opencode/cli/bin/opencode.exe ; opencode2 -> (same)
```

Official v2 install channels (fetched `https://v2.opencode.ai/docs/`): `curl -fsSL https://opencode.ai/v2/install | bash`,
`brew install anomalyco/tap/opencode-v2`, `npm install -g @opencode/cli`, AUR `opencode-beta`,
Docker `ghcr.io/anomalyco/opencode:2.0.0`. → v2 is a shipped, installable product; **not** the installed v1.18.31.

**Process caveat:** the first v2 `debug agents` run in a scratch dir **without a git root** returned `[]`; after `git init` + one commit
the project was detected and all agents loaded. v2 project discovery appears to require a VCS/project root.

---

## 2. Schema-Validierung — Verdikt-Matrix (Runtime gegen die generierten Artefakte)

Runtime = v2.0.20 loading the repo's generated `.opencode/agents/*.md` (58 files) + generated `opencode.json`.

| Aspekt | Was generiert ist | Runtime-Beobachtung (v2.0.20) | Status |
|---|---|---|---|
| **agents** (plural) dir/key | `.opencode/agents/*.md` (58), Markdown only; JSON `agents` key unused | `.opencode/agents/` dir: **58/58 geladen**; JSON `agents:{…}` Key: **akzeptiert + geladen** | **RUNTIME-OK** |
| **permissions** als Liste | Agent frontmatter nutzt **`permission:` Map** (v1), Config nutzt **`permission:` Map** | Map wird **akzeptiert und in eine `permissions`-Liste konvertiert** (kein Fehler); native `permissions: [ {action,resource,effect} ]` ebenfalls akzeptiert | **RUNTIME-OK** (Legacy-Compat, doc-nonkonform) |
| **default_agent** | **fehlt** in `opencode.json` | Key wird akzeptiert/erhalten; fehlend → kein Fehler (Fallback). Wert auf einen `mode: subagent` gesetzt → **kein Warning, rc=0** | **RUNTIME-OK** (Feld), aber **Lücke**: generiertes Config setzt ihn nicht |
| **model#variant** | generierte Agents haben **kein `model:`** (0/58) | Synthetisch `model: anthropic/claude-sonnet-4-5#high` → geladen als `{id,providerID,variant:"high"}` | Notation **RUNTIME-OK**; an **generierten Artefakten UNVERIFIABLE** (nicht emittiert) |
| **shell / subagent** actions | generiert `bash: allow/deny`, `task: allow` | `bash`→`shell`, `task`→`subagent`, `todowrite` bleibt; native `{action: shell|subagent, …}` Liste akzeptiert | **RUNTIME-OK** |
| **`subagent_depth`** (Config) | `opencode.json: "subagent_depth": 3` | `debug config` Resolved-Output: **still entfernt** (nicht in v2-Fläche) | **RUNTIME-REJECTED** (silent drop) |
| **flat `mcp`** (Config) | `"mcp": { "<name>": {…} }` (v1) | `debug config`: mcp erscheint **nicht**; nur `mcp.servers` (nested) wird erhalten | **RUNTIME-REJECTED** (silent drop) |
| **Official JSON-Schema** | `$schema: https://opencode.ai/config.json` | Schema = **v1**: `Config` (nur `agent` singular, `permission`, `subagent_depth`, `tools`, `maxSteps`), `additionalProperties:false`; `v2.opencode.ai/config.json` → **301→404** | **STATIC-MISMATCH** (v2-Doku verweist auf v1-Schema) |

### 2.1 Command → Output (Auszüge)

Load of all generated agents (v2):
```
$ opencode debug agents        # in scratch project, env XDG_* redirected
  agent count: 68   = 58 generated + 7 built-ins (build, plan, general, explore, compaction, title, summary) + probes
  generated agents loaded: 58/58   generated agents missing: []
```

Generated `permission:` Map → v2 `permissions` Liste (agent `developer` = `edit: allow`, `orchestrator` = `bash: deny`, `task: allow`):
```
developer    permissions tail: … {"action":"edit","resource":"*","effect":"allow"}   ← edit:allow
code-reviewer permissions tail: … {"action":"edit","resource":"*","effect":"deny"}    ← edit:deny
orchestrator permissions tail: … {"action":"subagent","resource":"*","effect":"allow"},
                                 {"action":"shell","resource":"*","effect":"deny"}     ← task→subagent, bash→shell
```

Native v2 fields (synthetic probe `zz-probe-native.md`):
```
frontmatter: mode: primary; model: anthropic/claude-sonnet-4-5#high;
  permissions: [{action: shell, resource: "git push *", effect: ask}, {action: subagent, resource: "*", effect: deny}];
  steps: 8; hidden: true; color: "#ff6b6b"
result: mode=primary hidden=true color=#ff6b6b steps=8
        model={"id":"claude-sonnet-4-5","providerID":"anthropic","variant":"high"}
        permissions=[… shell/"git push *"/ask, subagent/"*"/deny …]        # unverändert übernommen
```

Config: `subagent_depth` + flat `mcp` + `permission` map (the generated `opencode.json`):
```
$ opencode debug config
  info: { "$schema": "https://opencode.ai/config.json",
          "permissions": [ {"action":"edit","resource":"**","effect":"deny"},
                           {"action":"shell","resource":"**","effect":"deny"} ] }   # permission map→list; bash→shell
  # "subagent_depth" and flat "mcp" are ABSENT from the resolved document
$ (with nested "mcp":{"servers":{…}})  →  "mcp":{"servers":{playwright|reqogniloom|viz-logger}} is retained
```

Schema validation (`jsonschema` 4.26.0, official `https://opencode.ai/config.json`, HTTP 200, 39 039 B):
```
GENERATED opencode.json (v1 shape)              → VALID
V2-NATIVE config (agents + permissions + default_agent) → INVALID
   "Additional properties are not allowed ('agents', 'permissions' were unexpected)"
```

### 2.2 v2 validator is real but silent (rejection evidence)
```
$ cat zz-probe-badperm.md   # permissions: {edit: allow}  (map, wrong type for v2)
$ cat zz-probe-badmode.md   # mode: bogus ; effect: maybe
$ opencode debug agents --print-logs
  rc=0 ; stderr = EMPTY ; zz-probe-badperm + zz-probe-badmode ABSENT from output
```
⇒ Wrong-typed `permissions`, invalid `mode`/`effect` are **dropped silently** — no error, no warning. A generated artifact that stops
matching the v2 surface would disappear from the catalog without any sync-time signal.

---

## 3. Abgrenzung v1 ↔ v2

| | v1 (`opencode-ai` 1.18.31) | v2 (`@opencode/cli` 2.0.20) |
|---|---|---|
| Agent frontmatter | `permission:` Map (native) | `permissions:` Liste (native); Map nur via Compat-Layer |
| Actions | `bash`, `task`, `todowrite`, … | `shell`, `subagent`, `read/edit/glob/grep/webfetch/websearch/skill`; `bash`/`task` werden gemappt |
| Config dir/key | `agent` (singular) evtl., `permission` Map, `subagent_depth`, flat `mcp` | `agents` (plural), `permissions` Liste, `default_agent`, `mcp.servers` |
| Official schema | `https://opencode.ai/config.json` (deckt v1) | **kein** eigenes Schema; v2-Doku zitiert dasselbe v1-Schema |
| Debug | `opencode debug v2` → v2-Katalog `{providers:[225], default:Effect, small:{…}}` (kein Agent-Schema) | `opencode debug agents`/`config`/`paths`; **kein** `debug v2`-Subcommand |

Phase C (`opencode debug v2` via v1, `command → output`):
```
$ opencode debug v2
  {'providers': 225, 'default': {…Effect…}, 'small': {…}}     # v2 provider/model catalog only, no agent-config schema
  (see v1 evidence file for documented non-determinism of this command)
```
⇒ `debug v2` on v1 is **not** a v2 config validator; it prints the v2 model catalog. Real v2 schema validation only via the v2 binary.

---

## 4. Offene Punkte
- `default_agent` pointing at a `mode: subagent` produced **no** warning on `debug agents`; the documented fallback ("must support
  primary use, else fall back to build") is not observable via parse/debug. Confirm at session level (needs a run/turn) — **not run**.
- No published **v2 JSON schema** exists; v2-native config cannot be schema-validated against an official artifact (STATIC-UNVERIFIABLE),
  only against the runtime.
- Generic-markdown `model#variant` is exercised only synthetically — agent-meta emits **no `model:`** for Opencode (0/58), so the
  generated artifacts do not use the notation at all.
- Legacy compat (`permission` map, `tools` map, `maxSteps`→`steps`, `temperature`→`request.body`) is undocumented runtime behaviour;
  it may be removed in v2 without notice (docs: *"Do not use legacy … fields"*).
