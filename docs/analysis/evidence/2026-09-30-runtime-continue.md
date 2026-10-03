# Runtime-/Schema-Evidenz — Continue (H7 Auto-Discovery · H8 SSE-`headers` · H9 `skills` · bare Model-Alias)

- **Datum:** 2026-09-30 · **Repo:** `/home/hermes/repos/agent-meta` · **Branch:** `feat/provider-audit-opencode-v2` @ `65a493ec` (keine git-Mutation).
- **Tools:** `node v22.17.0` · `npm 10.9.2` · `@continuedev/cli (cn) 1.5.47` (lokal installiert) · `@continuedev/config-yaml 1.42.0` (Zod-Schema, lokal installiert).
- **Quellen:** `2026-09-30-provider-audit-docs-part2.md` §4 (CO-1 + 3 HYPOTHESEN) · `2026-09-30-provider-audit-generation.md` D3 · offizielles Repo `continuedev/continue@main` `5522c6f4` (2026-07-21) + npm-Dist-Schema.
- **Isolation:** Scratch `/var/tmp/opencode-audit/continue/{proj,zod,cli,src}/`; Repo-Root nie non-dry-run gesynct. **Verdikt-Key:** VERIFIED / REFUTED / UNVERIFIABLE / STATIC.
- **method:** `command → raw output`, exakte Flags via `--help`, kein bezahlter LLM-Turn.

## 1. Installationsversuch (real)

```
$ command -v code            → (leer), rc=1                 # VS Code nicht installiert
$ ls -la ~/.continue/        → Datei oder Verzeichnis nicht gefunden   # vor Install
$ npm view @continuedev/cli version            → 1.5.47
$ npm install @continuedev/cli@1.5.47 --no-audit --no-fund
  → added 13 packages in 3s, rc=0
$ ./node_modules/.bin/cn --version             → 1.5.47, rc=0
$ npm view @continuedev/config-yaml version    → 1.42.0
$ npm install @continuedev/config-yaml@1.42.0  → added 4 packages in 2s, rc=0
```
Install **erfolgreich** (CLI + Schema-Paket). Source-Pin: `GET api.github.com/repos/continuedev/continue/commits/main`
→ `5522c6f44ca0ac3528b37244818fbfa39b5af470` (2026-07-21); README: *"no longer actively maintained and is read-only"*.
Nebeneffekt außerhalb des Repos: `cn --version/--help` legt `~/.continue/logs/cn.log` an (nicht im Repo, kein Artefakt-Schaden).

## 2. Artefakt-Herkunft (Scratch-Sync)

`.continue/` existiert im Repo-Checkout **nicht**. Generiert mit `ai-providers: [Continue]`:
```
$ python3 <repo>/scripts/sync.py --config /var/tmp/opencode-audit/continue/proj/.meta-config/project.yaml   → rc=0
  .continue/config.yaml (232 Z.) · config.local.yaml · agents/ (58 *.md + .agent-meta-managed)
  prompts/ (80 *.md) · rules/ (36 *.md) · skills/ (LEER) · pipeline-details/ (8)
```

## 3. Zod-Validierungsmatrix (`@continuedev/config-yaml@1.42.0`)

| Artefakt | Schema | Ergebnis | Fehlerpfad / Detail |
|---|---|---|---|
| `.continue/config.yaml` | `configYamlSchema` | **INVALID** | `["models",0]` `invalid_union` → `models[0].roles[2]="agent"` nicht im Enum `chat,autocomplete,embed,rerank,edit,apply,summarize,subagent`. `validateConfigYaml()` → 1 fatal error. |
| `.continue/config.yaml` top-level `agents:` (58 Einträge) | idem | **gestrippt (dead config)** | Schema-Keys = `name,version,schema,metadata,env,requestOptions,models,context,data,mcpServers,rules,prompts,docs`; parse `{name,version,agents:[…]}` → result `["name","version"]`, `agents` verworfen. **CO-1 zod-belegt.** |
| `.continue/config.local.yaml` | idem | **INVALID** | required `name`,`version` fehlen (`["name"]`/`["version"]` `invalid_type Required`). |
| `.continue/config.yaml` `mcpServers` (isoliert) | idem | **VALID, aber `headers` verworfen** | honcho+reqogniloom `parsedKeys=[name,url,type]`, `headersKept=false`. |
| `.continue/agents/*.md` (58) | `parseAgentFile` / `agentFileSchema` | **VALID 58/58** | einheitliches Key-Set `{name,description,model,prompt}`; `version,hint,prompt_mode,based-on,generated-from,alwaysApply,memory` verworfen. |
| `.continue/rules/*.md` (36) | `markdownToRule` | **VALID 36/36** | 36/36 ohne Frontmatter → Fallback-Pfadname (nicht fatal). |
| `.continue/prompts/*.md` (80) | `markdownToRule` | **VALID 80/80** | `invokable=true` 80/80. |
| `.continue/skills/` | (Runtime `skillFrontmatterSchema`) | **0 Artefakte** | Verzeichnis leer → keine Validierung möglich. |

Roh-Belege:
```
configYamlSchema top-level keys: ["name","version","schema","metadata","env","requestOptions","models","context","data","mcpServers","rules","prompts","docs"]
contains 'agents': false   contains 'skills': false   contains 'mcpServers': true
parse {name,version,skills:[...]}: success=true -> keys=["name","version"]   # skills verworfen
parseAgentFile("model: claude-sonnet-5"): model="claude-sonnet-5"           # bare ID akzeptiert
```
**Neuer Befund CO-2:** Default-Template `templates/configs/CONTINUE.config-template.yaml:28` `roles: [chat, edit, agent]` ist schema-invalid (`agent` kein gültiges `ModelRole`).

## 4. H7 — `.continue/agents/` Auto-Discovery → **STATIC-VERIFIED, surface-abhängig**

- IDE-Core `core/config/ConfigHandler.ts:161-179` `getLocalProfiles()` → `getAllDotContinueDefinitionFiles(ide, {…, fileExtType:"yaml"}, "agents")` ⇒ Agent-/Profil-Auto-Discovery lädt **nur `.yaml/.yml`** aus `.continue/agents`.
- `cn 1.5.47` `src/commands/review/resolveReviews.ts:57-89` `resolveFromLocal()` liest `.continue/agents/*.md` + `.continue/checks/*.md` als Fallback-Quelle 3 von `cn review`.
- `cn` `src/services/AgentFileService.ts:55-88` parst `.md` via `parseAgentFile` nur bei **explizitem** `--agent <pfad>.md` (kein Auto-Load).

**Verdikt:** `.continue/agents/*.md` ist **kein** auto-geladener Chat-Agent-Surface (dafür braucht die IDE `.yaml`). Auto-Discovery der `.md` existiert **nur im `cn review`**-Pfad. Der generierte Header-Kommentar „*Agents : .continue/agents/ (auto-discovered by Continue)*" ist für den Chat-Surface **REFUTED**, für `cn review` VERIFIED. Kein Live-Lauf (keine Credentials/Modell) → STATIC.

## 5. H8 — per-Server SSE-`headers` → **REFUTED**

`packages/config-yaml/src/schemas/mcp/index.js:18-23` (`sseOrHttpMcpServerSchema`): Keys `name,serverName,faviconUrl,sourceFile,sourceSlug,connectionTimeout,url,type,apiKey,requestOptions` — **kein top-level `headers`**. Header nur verschachtelt: `requestOptions.headers` (`schemas/models.js:21`, `Record<string,string>`).
Zod-Verhalten: unbekannte Keys werden per Default **gestrippt** (kein Fehler, aber wirkungslos):
```
honcho (type=sse)      parsedKeys=[name,url,type]   headersKept=false
reqogniloom (type=sse) parsedKeys=[name,url,type]   headersKept=false
```
Kontrast (nicht der YAML-Pfad): `schemas/mcp/json.js` `httpOrSseMcpJsonSchema` **hat** top-level `headers` — gilt für das JSON-MCP-Format.
**Verdikt:** die generierte Schreibweise `headers:` auf SSE-MCP-Einträgen in `.continue/config.yaml`/`config.local.yaml` ist nicht schema-konform und wird verworfen ⇒ honcho-/reqogniloom-Auth-Header erreichen den Server nicht. Korrekt wäre `requestOptions.headers`.

## 6. H9 — `skills`-Surface → **VERIFIED (Runtime-Source), aber artefaktlos**

- Schema: `skills` kommt in `@continuedev/config-yaml@1.42.0` **nirgends** vor (Schema-Keys s.o.; Repo-`grep skills` → 0 Treffer). `capabilities` existiert nur auf **Model**-Ebene und nimmt beliebige Strings (`ZodString`), ohne `skills`-Semantik.
- Runtime-Source: `cn` `src/util/loadMarkdownSkills.ts:88-146` liest `.continue/skills/<name>/SKILL.md`, `.claude/skills/…`, `~/.continue/skills/…`; Frontmatter-Contract `{name,description}` (Zod, beide `min(1)`). IDE-Core `core/config/markdown/loadMarkdownSkills.ts` identisch (`SKILLS_DIR="skills"`).

**Verdikt:** `.continue/skills/**/SKILL.md` ist ein **realer Laufzeit-Surface** (Quelle + CLI), aber **keine** `config.yaml`-Option. agent-meta generiert **0** Skill-Artefakte (`.continue/skills/` leer) ⇒ `capabilities: [ …, skills, … ]` in `config/ai-providers.yaml:275` ist artefaktlos (bestätigt part2 §6; kein Fehler, aber Under-Delivery).

## 7. Bare Model-Alias (`claude-sonnet-5`, ohne Provider-Präfix)

`agentFileSchema.model = z.string().optional()` → **jeder** String wird akzeptiert, keine Provider-Präfix-Validierung:
```
$ parseAgentFile("---\nname: x\nmodel: claude-sonnet-5\ntools: Read,Write\n---\nbody")
  → model="claude-sonnet-5"  keys=["name","model","tools","prompt"]   # kein Zod-Fehler
```
**Verdikt:** Schema akzeptiert die bare ID (**VERIFIED**). Semantische Auflösung ist im `cn`-Pfad ein Hub-Lookup (`AgentFileService.doInitialize` → `loadModelFromHub(agentFile.model)`) und ohne Hub/Auth **UNVERIFIABLE** (kein LLM-Turn). Die generierte `config.yaml` selbst nutzt lokale `ollama`-Modelle (Template), nicht Claude-IDs — part2 D3 (Claude-Model-IDs aus dem globalen Tier-Preset) bleibt davon unberührt.

## 8. Offene Punkte

1. **CO-2 (neu):** `templates/configs/CONTINUE.config-template.yaml:28` `roles: [chat, edit, agent]` → `config.yaml` schema-invalid; Default-Config lädt nicht (fatal).
2. **CO-1 (zod-bestätigt):** `agents:`-Block (58 Einträge) ist wirkungslose Dead-Config; zusätzlich existieren die 58 `.continue/agents/*.md` als eigentlicher Surface.
3. **H8:** auf `requestOptions.headers` umstellen, sonst Auth-Verlust (honcho/reqogniloom).
4. **H9:** `skills`-Capability ohne Artefakte — entweder Skill-Generierung nach `.continue/skills/<name>/SKILL.md` oder Flag softenern.
5. **H7:** `config.yaml`-Header-Kommentar korrigieren (`cn review`-Surface ≠ Chat-Agent-Auto-Load).
6. **Drift-Risiko:** `continuedev/continue@main` ist archiviert/read-only; aktueller Träger ist `@continuedev/cli` (1.5.47). Schema-Pin: `@continuedev/config-yaml@1.42.0`.
