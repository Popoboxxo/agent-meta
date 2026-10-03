# Runtime-Evidenz — Codex (D1) · KimiCode (H6) · ZCode (H5)

- **Datum:** 2026-09-30 · **Repo:** `/home/hermes/repos/agent-meta` · **Branch:** `feat/provider-audit-opencode-v2` @ `65a493ec` (keine git-Mutation).
- **Tools:** `codex-cli 0.151.0` · `kimi 2.1.1` · `zcode-app-cli 3.14.4-30` / `zcode-runtime 0.16.9` (npm, neu in Scratch installiert) · `node v22.17.0` · Python 3.13 + `tomllib`.
- **Quelle:** `2026-09-30-provider-audit-generation.md` (D1) · `...-docs-part2.md` §1 CX-1 / §2 ZC-1 / §3 KC-1. **Methode:** `command → raw output`, exakte Flags via `--help`, kein LLM-Turn.
- **Isolation:** Scratch `/var/tmp/opencode-audit/{codex,kimi,zcode}/`; Installs nur dort; Repo-Root nie non-dry-run gesynct. **Verdikt-Key:** VERIFIED / REFUTED / UNVERIFIABLE.

## 0. Artefakt-Herkunft (vorab)
`.codex/`, `.kimi-code/`, `.zcode/` existieren im Repo-Checkout **nicht** (`.meta-config/project.yaml` `ai-providers: Claude, Opencode, Gemini`). Alle geprüften Artefakte stammen aus realen Scratch-Syncs (identische `scripts/lib` + `config/` + `agents/` wie HEAD):
```
$ python3 <repo>/scripts/sync.py --config .meta-config/project.yaml   # je Scratch-Root → Codex/KimiCode/ZCode rc=0
  → je 58 Agent-Artefakte + `.agent-meta-managed` Index
```
Keine Repo-Datei außer diesem Report wurde geschrieben (`git status`: nur untracked `docs/analysis/...`).

---

## 1. Codex — D1 (invalides TOML) → **VERIFIED** (erweitert: **2** betroffene Dateien)

### 1.1 Lokaler TOML-Parse (real, `tomllib`)
```
$ python3 -c "import tomllib,pathlib; tomllib.loads(pathlib.Path('.codex/agents/agent-meta-manager.toml').read_text())"
TOMLDecodeError: Invalid statement (at line 467, column 1)
$ # Scan aller .toml in <scratch>/.codex/agents/
total=58 valid=56 invalid=2
INVALID agent-meta-manager.toml: Invalid statement (at line 467, column 1)
INVALID knowledge-curator.toml:  Invalid statement (at line 100, column 1)
non_toml_entries=['.agent-meta-managed']
valid key-set uniformity: [('description','developer_instructions','model','name','sandbox_mode')]   # 56/56 identisch
```
Beide Fehler = dasselbe Muster: `## Singleton-Regel`-Block steht **nach** dem schließenden `"""` von `developer_instructions` (manager ab Z.465, knowledge-curator ab Z.98).

### 1.2 Codex-eigener Parser (real genutzt)
`codex --help` listet **kein** `config`/`validate`; vorhanden: `doctor`, `debug`, `exec`, `mcp`, `agents`. `.codex/agents/*.toml` werden **lazy** (erst beim Subagent-Spawn) geladen — `codex doctor` mit `agents/`-Verzeichnis meldet weiterhin `config loaded`. Der Spawn-Loader ist ohne Model-Turn nicht erreichbar (keine Credentials: `auth: no Codex credentials were found`). Beweis über die **identischen Bytes** durch Codex' eigenen TOML-Parser via Config-Bootstrap:
```
$ CODEX_HOME=<scratch>/invalid-home codex mcp list      # config.toml = agent-meta-manager.toml
Error: failed to load bootstrap configuration
Caused by: 0: <...>/config.toml:467:13: key with no value, expected `=`
           1: TOML parse error at line 467, column 13
              467 | **NIEMALS** `task(subagent_type="orchestrator", ...)` oder `Agent(...)` aufrufen.
                  |             ^   key with no value, expected `=`
$ CODEX_HOME=<scratch>/invalid-home codex doctor --summary   →  ✗ config  config could not be loaded
$ CODEX_HOME=<scratch>/valid-home   codex doctor --summary   →  ✓ config  loaded    # config.toml = developer.toml (Kontrolle)
```
Beide Parser (Rust-`toml` in Codex, `tomllib`) reportern Zeile 467 → die Codex-seitige Ablehnung der identischen Bytes ist real belegt.

### 1.3 Stichprobe ≥5 valide + Root-Cause
5 valide Dateien geparst (`accessibility-specialist`, `agent-meta-scout`, `api-specialist`, `app-lifecycle-governor`, `bug-feature-analyzer`) — alle `{name, description, model, sandbox_mode, developer_instructions}`. Root-Cause unverändert: `agent_sync.py:741-753` appendet `SINGLETON_CONSTRAINT_BLOCK` **nach** `transform_agent_content_for_provider()` (Serialisierung). Betroffen sind genau die nicht-Orchestrator-Rollen mit spawn-fähigem `tools`:
```
$ <scan> spawn-capable templates: _reference-agent, agent-meta-manager, knowledge-curator, orchestrator, homeassistant-log-analyzer
```
`orchestrator` ist ausgeschlossen (`role != "orchestrator"`); aktiv bleiben **agent-meta-manager** + **knowledge-curator** (Letzterer hat `tools: [Read, Write, Agent, TodoWrite]` — die frühere Analyse nannte nur Erstere).

---

## 2. KimiCode — H6 (Model-ID-Präfix) → **VERIFIED**

### 2.1 Discovery der generierten Artefakte (real)
```
$ kimi --help | grep -A2 -- '--agent'
  --agent <name>       Agent profile ... Custom profiles are discovered from agent directories ...
  --agent-file <path>  Load an agent definition from a Markdown file ...
$ strings ~/.local/bin/kimi | grep 'PROJECT_BRAND_DIRS'
  USER_BRAND_DIRS$1 = ["agents"]   USER_GENERIC_DIRS$1 = [".agents/agents"]
  PROJECT_BRAND_DIRS$1 = [".kimi-code/agents"]   PROJECT_GENERIC_DIRS$1 = [".agents/agents"]
```
`.kimi-code/agents/*.md` **ist** ein realer Project-Discovery-Pfad. `kimi doctor` validiert nur `config.toml`/`tui.toml`, keine Agents — daher Model-Auflösung separat geprüft.

### 2.2 Runtime-Modell-Auflösung (ACP-Handshake, **kein** LLM-Turn)
```
$ kimi acp   →  session/new  →  configOptions["model"]
  currentValue: "kimi-code/kimi-for-coding-highspeed"
  options: ["kimi-code/kimi-for-coding", "kimi-code/kimi-for-coding-highspeed",
            "kimi-code/k3-256k", "kimi-code/k3"]          # 4 konfigurierte Aliase, ALLE provider-qualifiziert
$ session/set_config_option {configId:"model", value:"kimi-k2.7-code"}
  → error -32603: Model "kimi-k2.7-code" is not configured in config.toml.
$ session/set_config_option {configId:"model", value:"kimi-code/kimi-for-coding"}
  → result (config_option_update, currentValue="kimi-code/kimi-for-coding")     # Kontrolle OK
```
Bundled Source bestätigt die Alias-Pflicht: `resolveSubagentBinding(config, {modelAlias})` → `this.modelCatalog.get(binding.model)` → `MODEL_NOT_CONFIGURED`. Die generierte bare ID fehlt im Alias-Katalog (`kimi provider list --json`: `models=4`, keys `kimi-code/...`).

### 2.3 Statistik
```
$ <scan> .kimi-code/agents/*.md
agent files: 58 · yaml failures: 0 · missing name: 0 · missing description: 0
models: kimi-k2.7-code: 34 · kimi-k2.6: 24
files whose model is NOT a configured runtime alias: 58 / 58
```
→ **58/58** generierte KimiCode-Agents binden eine zur Laufzeit nicht auflösbare Model-ID (fehlender `provider/`-Präfix + nicht existierender Alias) → H6 real-verifiziert.

---

## 3. ZCode — H5 (`type`-Key im MCP-Server-Block) → **REFUTED**

### 3.1 Installationsversuch (real) → **installierbar via npm**
```
$ npm view zcode-app-cli version dist.tarball bin
  3.14.4-30 · https://registry.npmjs.org/zcode-app-cli/-/zcode-app-cli-3.14.4-30.tgz · bin = { zcode: 'bin/zcode.js' }
$ npm install zcode-app-cli                     # ohne Version
  npm error code ETARGET · No matching version found for zcode-app-cli@*.
$ npm install zcode-app-cli@3.14.4-30           # rc=0, "added 5 packages"
  npm warn EBADENGINE required: { node: '>=22.19.0' } current: { node: 'v22.17.0' }   # Warnung, kein Blocker
$ npm install --prefer-online zcode-app-cli@latest   # rc=0, ebenfalls OK (stale npm-Cache war die ETARGET-Ursache)
$ ./node_modules/.bin/zcode --version           →  zcode-app-cli 3.14.4-30 / zcode-runtime 0.16.9
```
CLI-Commands: `doctor`, `app-server`, `commands|skills|plugins list`, … — kein `mcp`-CLI-Command; `doctor` prüft keine MCP-Konfiguration, `prompt` scheitert vor dem Config-Laden an `Model creation failed` (kein Login).

### 3.2 Runtime-Schema (autoritativ, installiertes Bundle `zcode-app-cli/vendor/zcode.cjs`)
```js
eun = { protocolVersion: enum(["auto","legacy","2026-07-28"]).optional(), enabled: boolean.optional(), timeoutMs: oB.optional() }
H6s = object({...eun, type: literal("stdio"), command: string().min(1), args: array(string).optional(),
              cwd: string().optional(), env: hat.optional()}).strict()
G6s = object({...eun, type: literal("http"), url: string().min(1), headers: hat.optional(), oauth: KVr.optional()}).strict()
J6s = object({...eun, type: literal("sse"),  url: string().min(1), headers: hat.optional(), oauth: KVr.optional()}).strict()
ZVr = preprocess(ljs, discriminatedUnion("type", [H6s, G6s, J6s]))    // ← `type` ist der DISCRIMINATOR
K6s = object({ servers: record(string(), ZVr).optional() })
ljs(obj): type=="remote"→"http"; type kein string → command⇒"stdio", url⇒"http"   // Legacy-Normalisierung
pjs(): ZVr.safeParse(entry); failure → {code:"config_mcp_server_invalid", path:"mcp.servers.<name>"} + Server verworfen
```
`type` ist **kein** ignorierter Zusatzschlüssel, sondern das **Pflicht-Diskriminatorfeld** (Enum `stdio`/`http`/`sse`); `.strict()` verwirft unbekannte Keys. Der generierte Block passt exakt:
```
$ <scratch>/.zcode/config.json
  honcho      {type:"sse",   url:"${MCP_HONCHO_URL}",              headers:{...}}      → J6s ✓
  reqogniloom {type:"sse",   url:"${MCP_REQOGNILOOM_URL}/mcp/sse/", headers:{...}}      → J6s ✓
  playwright  {type:"stdio", command:"npx", args:[...]}                                 → H6s ✓
  viz-logger  {type:"stdio", command:"python", args:["scripts/viz-logger.py","--mcp"]}  → H6s ✓
$ (Kontrolle) .zcode/config.json am CLI geladen → diagnostics: []
```
Negativtest (`bogus_unknown_key` + Extra-Feld / `type:"websocket"`) nur statisch aus dem Schema: `skills list`/`commands list` liefern nur Skill-/Command-Diagnostik; die MCP-`config_mcp_server_invalid`-Diagnostik ist an den (login-pflichtigen) Sessionstart gebunden. Das Schema selbst ist eindeutig.

**Verdikt:** Die Annahme, der `type`-Key sei nicht contract-konform/undokumentiert (H5), ist **REFUTED** — er ist schema-konform und von der Runtime sogar gefordert; die generierten Werte (`sse`/`stdio`) sind gültig.

---

## 4. Statistik je Provider (Scratch-Syncs)

| Provider | Artefakte | Geprüft | Ergebnis |
|---|---|---|---|
| Codex | 58 `.toml` + Index | alle 58 | **56 valide / 2 invalide** (agent-meta-manager, knowledge-curator) |
| KimiCode | 58 `.md` Agents | alle 58 | 58/58 Frontmatter valide; **58/58 Model-ID nicht als Runtime-Alias auflösbar** |
| ZCode | 58 `.md` Agents + `config.json` | config.json | 4/4 MCP-Server schema-konform; Agents nicht erneut geprüft (ZC-1 unverändert) |

## 5. Offene Punkte
1. **D1:** Fix = Singleton-Block **vor** die provider-Serialisierung ziehen (oder `codex-toml`-Body-Builder) + `tomllib`-Round-Trip-Check nach Serialisierung. Zweite Bruchstelle `knowledge-curator` in Fix/Test mitführen (`test_provider_toml_transform.py` prüft nur die pure `_transform`, nie `_finalize_agent_content`).
2. **H6:** KimiCode-`model` muss ein konfigurierter `provider/model`-Alias sein (bzw. `inherit`/weglassen). Der Syncer emittiert bare IDs (`kimi-k2.7-code`, `kimi-k2.6`) → in jeder realen KimiCode-Installation unauflösbar; Quelle in `config/ai-providers.yaml`/`tier-presets.yaml` prüfen.
3. **H5:** Der `type`-Key ist unbedenklich; frühere Formulierung „unverified“ kann auf „schema-verifiziert“ gehoben werden. Fremdbeobachtung bleibt: offizielles Doku-Beispiel zeigt nur `command/args/env`.
4. Codex-Spawn-Loader selbst (nicht nur der Parser) konnte mangels Credentials nicht ausgeführt werden; eine authentifizierte Instanz würde die Agent-Ablehnung direkt zeigen.
