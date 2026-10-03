# Runtime-Evidenz — Mammouth (H10 / MM-2 / MM-4) · Copilot (Artefakt-Validierung)

- **Datum:** 2026-09-30 · **Repo:** `/home/hermes/repos/agent-meta` · **Branch:** `feat/provider-audit-opencode-v2` @ `65a493ec` (read-only, **keine** git-Mutation, kein Branch-Wechsel).
- **Quellen:** `...-provider-audit-docs-part2.md` §5 (MM-1…MM-5) · `...-provider-audit-docs-part1.md` §5 (P-1…P-6) · `...-provider-audit-generation.md` (D2/D4).
- **Tools:** `mammouth 1.18.31.1` (offizielles Release-Binary, isoliert installiert) · `node v22.17.0` · `npm` · Python 3.13. **Methode:** `command → raw output`, exakte Flags via `--help`, keine bezahlten LLM-Turns (keine Credentials → Provider-Calls enden vor dem Modell).
- **Verdikt-Key:** VERIFIED (real beobachtet) / REFUTED / STATIC (nur aus offizieller Doku) / UNVERIFIABLE.
- **Isolation:** Installs + Scratch nur `/var/tmp/opencode-audit/{mammouth,copilot-proj}/`; `sync.py` **nie** im Repo-Root (nur mit `--config <scratch>/...`); Repo-Schreiboperation ausschließlich diese Datei.

## 0. Install-Ergebnis (real, isoliert)

| Versuch | Exakter Befehl | Ergebnis |
|---|---|---|
| **Binary (offizieller Installer)** | `HOME=/var/tmp/opencode-audit/mammouth/home VERSION=1.18.31.1 SHELL=/bin/bash bash install.sh` | **rc 0** — `[INFO] Installed to /var/tmp/opencode-audit/mammouth/home/.mammouth/bin/mammouth` |
| Binary-Direkt-Asset | `curl -fsSL .../releases/download/v1.18.31.1/mammouth-linux-x64-baseline.tar.gz` | rc 0, 61 957 007 B (kein AVX2 → `-baseline`) |
| Version | `mammouth --version` | `1.18.31.1` |
| **npm (global)** | `npm view mammouth` / Registry-Suche | **kein offizielles Paket** (Treffer sind unverwandte PHP-Projekte) → Installer ist der einzige Weg |
| **go** | – | N/A: `github.com/mammouth-ai/code` ist ein TypeScript/**Bun**-Projekt (OpenCode-Fork), kein Go-`main` |

Mammouth Code = OpenCode-Fork (`parent/source = anomalyco/opencode`). Runtime-CLI bietet u. a. `agent list`, `models`, `debug config`, `debug agent <name>`, `debug skill` — konfigurationsladende Diagnostics **ohne** Login/LLM-Turn.

## 1. Mammouth — Scratch & Config-Auszug

Scratch-Projekt `/var/tmp/opencode-audit/mammouth/proj/` (`ai-providers: [Mammouth]`, 5 Rollen), erzeugt mit
`python3 scripts/sync.py --config /var/tmp/opencode-audit/mammouth/proj/.meta-config/project.yaml` → **rc 0**.
Erzeugte Artefakte: `.mammouth/agents/{developer,git,orchestrator,security-auditor,tester}.md`, `.mammouth/rules/*` (38),
`.mammouth/skills/` (**0 Dateien**), `.mammouth/settings.json` (`{}`), Root `MAMMOUTH.md` (**kein `AGENTS.md`**).

## 2. Mammouth — Findings

### 2.1 MM-2 (HIGH, `tools:` als YAML-String-Liste) → **VERIFIED (Runtime-Abbruch)**

Original-Artefakt (unverändert, Backup `/var/tmp/opencode-audit/mammouth/original-agents/`) in `proj-orig/`:
```
$ mammouth agent list
Error: Configuration is invalid at /var/tmp/opencode-audit/mammouth/proj-orig/.mammouth/agents/git.md
↳ Expected object | undefined, got ["Bash","Read","Glob","Grep","TodoWrite"] tools
RC=1
```
Schema erwartet `tools: Record<String,Boolean>`; die Liste **bricht das Laden von `.mammouth/agents/` komplett ab** (kein Agent nutzbar).

### 2.2 H10 (Bare-Model-Alias ohne Provider-Präfix) → **REFUTED**

`.mammouth/agents/developer.md:18` → `model: claude-sonnet-5` (bare). Nach lokaler Umwandlung der `tools`-Liste in eine Map
(scratch-only, um das Laden von MM-2 zu entkoppeln) liefert die Runtime:
```
$ mammouth debug agent developer
  "model": { "providerID": "claude-sonnet-5", "modelID": "" }      # bare → als Provider-ID geparst, modelID leer
$ mammouth debug agent control-qualified                             # Kontrolle: model: opencode/big-pickle
  "model": { "providerID": "opencode", "modelID": "big-pickle" }
$ mammouth run --print-logs --log-level ERROR --model claude-sonnet-5 "ping"
  error="ProviderModelNotFoundError: Model not found: claude-sonnet-5/."          # rc 1
$ mammouth run --model opencode/big-pickle "ping"
  error="AI_APICallError: … free tier can only be used from within OpenCode"       # Provider aufgelöst, nur Free-Tier-Block
```
**Verdikt:** Mammouth löst bare Aliase **nicht** auf; erwartet `provider/model-id`. Die generierten Mammouth-Modelle
(`claude-sonnet-5`, `claude-haiku-4-5-20251001`, `claude-opus-4-8`) sind damit **nicht auflösbar** (MM-5 ist real, nicht nur HYPOTHESIS).
**Runtime-Static-Abgrenzung:** beide Befunde sind **RUNTIME** (echtes Release-Binary lädt/gleicht Config ab), kein Doku-Zitat.

### 2.3 MM-4 / Orphan-Check `MAMMOUTH.md` → **VERIFIED: Orphan**

Der Kontext-/Instruktions-Loader des Release-Binaries sucht nur `AGENTS.md`, `CLAUDE.md`, `CONTEXT.md`:
```
$ strings -n 4 <bin> | grep -c MAMMOUTH.md   → 0
$ strings -n 4 <bin> | grep -c AGENTS.md     → 17
$ strings -n 4 <bin> | grep -c CLAUDE.md     → 9
  Loader-Literal (aus dem Binary):  f = ["AGENTS.md", ...["CLAUDE.md"], "CONTEXT.md"]
```
Erzeugt wird ausschließlich `MAMMOUTH.md` (kein `AGENTS.md`) → Mammouth liest in diesem Projekt **gar keine** Projekt-Instruktionen.
Der Routing-Banner in `.github`-Analogie „Mammouth -> MAMMOUTH.md" zeigt auf eine Datei, die die Runtime nie öffnet. **Beleg über das installierte Binary (runtime-nah), nicht nur Doku.**

## 3. Copilot — Scratch-Sync & Artefakte

Scratch `/var/tmp/opencode-audit/copilot-proj/` (`ai-providers: [Copilot]`, Rollen orchestrator/developer/git/tester/documenter),
`python3 scripts/sync.py --config /var/tmp/opencode-audit/copilot-proj/.meta-config/project.yaml` → **rc 0, 43 actions**.

| Generiertes Artefakt | Anzahl |
|---|---|
| `.github/copilot/agents/*.md` (+ `.agent-meta-managed`) | 5 |
| `.github/copilot/COPILOT.md` | 1 |
| `.github/copilot/rules/*.md` | 20 |
| `.github/copilot/pipeline-details/*.md` | 7 |
| `.github/copilot/skills/` | **0 Dateien** (leeres Dir) |
| `.vscode/mcp.json`, `.github/prompts/*`, `.github/skills/`, `.github/agents/`, `.github/copilot-instructions.md`, `AGENTS.md` | **nicht erzeugt** |

## 4. Copilot — Validierungsmatrix gegen offizielle Verträge (STATIC)

Doku-Belege 2026-09-30: GitHub `add-repository-instructions` + `create-custom-agents` + `custom-agents-configuration`; VS Code
`custom-agents` (via WebFetch/WebSearch); Skills `docs.github.com/.../about-agent-skills`.

| Artefakt | Vertrag (offiziell) | Generiert | Verdikt / Fehlpfad |
|---|---|---|---|
| Agenten | `.github/agents/*.agent.md` (VS Code erkennt jede `.md` in `.github/agents`) | `.github/copilot/agents/*.md` | **INVALID** (P-1): falscher Pfad → wird nicht als Custom-Agent erkannt |
| Agent-Extension | `.agent.md` (GitHub cloud); VS Code toleriert `.md` | `.md` | **PARTIAL** (P-2): in VS Code ok, auf GitHub cloud nicht — Pfad (P-1) blockt ohnehin |
| Agent-Frontmatter | `description` **required**, `name` optional; unbekannte Keys toleriert | `name`, `version`, `description`, `hint`, `prompt_mode`, `generated-from` (5/5) | **VALID** (Schema): `description`+`name` vorhanden; `version/hint/prompt_mode/generated-from` sind dokumentfremde, tolerierte Keys |
| Kontextdatei | `.github/copilot-instructions.md` repo-weit, **oder** `AGENTS.md`/root `CLAUDE.md`/`GEMINI.md` | `.github/copilot/COPILOT.md` | **INVALID** (P-3): wird nicht geladen → **kein** Projektkontext |
| Rules | `.github/instructions/NAME.instructions.md` (`applyTo`-Frontmatter) | `.github/copilot/rules/*.md` | **INVALID** (P-4): falscher Pfad/Dateinamen → nicht geladen |
| Skills | `.github/skills/<name>/SKILL.md` | `.github/copilot/skills/` (leer) | **INVALID** (P-5): falscher Pfad **und** 0 Artefakte |
| Commands/Prompts | `.github/prompts/*.prompt.md` (Slash-Commands) | keine | declared `has_commands:false` — **UNDERCLAIM** (P-6) |
| MCP | `.vscode/mcp.json` top-level `servers` | keine (kein MCP konfiguriert) | konform-by-omission; `mcp-config.committed-file` zeigt korrekt auf `.vscode/mcp.json` |

## 5. Copilot — geladene Kontextdatei (STATIC)

**STATIC** (keine Copilot-Runtime im Container, Copilot ist im Repo inaktiv): Nach offizieller Doku lädt Copilot
`.github/copilot-instructions.md` (repo-weit), `AGENTS.md` (nächstgelegen) bzw. root `CLAUDE.md`/`GEMINI.md` — **nicht** `COPILOT.md`.
Zitat: *"These are specified in a `copilot-instructions.md` file in the `.github` directory of the repository."* (GitHub docs, 2026-09-30).
Das generierte Projekt enthält **keinen** dieser Pfade → Copilot lädt **keinen** agent-meta-Kontext. (Konsistent mit
`docs/analysis/evidence/2026-09-30-entry-file-verification.md` §7, P-3.)

## 6. Offene Punkte

1. **Copilot-Laufzeitladung** (welche Datei real injiziert wird) ist ohne installierten/authentifizierten Copilot **STATIC**; P-1/P-3/P-4/P-5 bleiben Doku-Belege.
2. **Mammouth H10** ist mit der Release-Version `1.18.31.1` REFUTED; ein künftiges Alias-Feature könnte das kippen → bei Versionssprung erneut prüfen.
3. `.mammouth/settings.json` (`{}`) und `.mammouth/rules/` sind zusätzlich generiert, aber von der Runtime nicht als Konfig/Rules gelesen (MM-3, MM-rule-note) — hier nicht erneut vertieft.
4. Kein Scratch-/Repo-Artefakt wurde verändert außer dieser Datei; alle Installs/Projekte verbleiben unter `/var/tmp/opencode-audit/`.
