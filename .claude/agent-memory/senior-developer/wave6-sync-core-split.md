---
name: wave6-sync-core-split
description: Wave 6 sync-core God-Module-Split (#565/#561/#563) — SCC 8→3, was fertig, was offen, wie #563 sicher zu machen ist
metadata:
  type: project
---

# Wave 6 — sync.py-Core God-Module-Split (Issues #565, #561, #563)

Branch `refactor/sync-core-god-module-split`. Roadmap: `docs/plans/audit-2026-08-refactoring-roadmap.md`.

**Kernfakt zum Import-Zyklus:** Der von #565 beschriebene Zyklus `agents↔config↔context` war ungenau. Real war ein **8-Modul-SCC** {agents, config, mcp, mcp_provider_config, rules, skill_channel, skills, viz}, der NUR durch deferred (function-local) Imports bestand — die Top-Level-Imports waren immer schon azyklisch. `context.py` ist gar nicht im SCC (nichts importiert context; es ist reiner Consumer). Deshalb kann man deferred Imports NICHT blind auf top-level heben — das reaktiviert den Load-Zyklus. Cycle-Breaking geht nur über neutrale Modul-Extraktion.

**Why:** XL/riskanteste Wave; Verhaltenserhalt vor Lehrbuch-Struktur; keine funktionalen Änderungen erlaubt.

**How to apply:** Bei weiterem Entwirren immer den AST-Cycle-Detector nutzen (siehe unten), nicht dem Issue-Text blind folgen.

## Status (Stand Session)

- **#565 DONE + verifiziert (801 passed, 2 skipped, --validate exit 0):** Neues `scripts/lib/variables.py` (substitute, strip_inactive_conditional_blocks, _resolve_orch_mode, _orch_mode_flags, _VALID_ORCH_MODES) — pure resolution helpers, deps nur re/sys/io.SyncError/log.SyncLog. config.py re-exportiert substitute/strip/_orch* top-level (Tests importieren sie aus lib.config). agents/rules/skills/context auf `from .variables import` umgestellt. **Ergebnis: config aus SCC raus.** `io.py` existierte schon (#573 nicht Teil hiervon) — NICHT angefasst.
- **#561 DONE (Test-Bestätigung lief noch beim Schreiben):** agents.py (2094 Z.) gesplittet in:
  - `frontmatter.py` (~536 Z.): Frontmatter-Parsing/-Injection + Konstanten (AGENTS_DIR etc.) + Discovery (collect_sources, role_from_platform_file) + load_provider_tools_config + yaml-Setup. Self-contained (nur stdlib+yaml).
  - `provider_transform.py` (~732 Z.): transform_agent_content_for_provider + Gemini/Opencode-Mappings + wrap_sections_in_xml + debug/bootstrap-Injection + _validate_tools_against_whitelist. Importiert frontmatter; viz deferred.
  - `agent_sync.py` (~677 Z.): sync_agents_for_provider + compose_agent + apply_patch/_patch_* + apply_path_rules + resolve_mcp_tools_for_role. Importiert frontmatter+provider_transform; mcp/rules/skills/viz/etc deferred.
  - `agents.py` (~233 Z.): nur build_agent_hints/build_agent_table/build_knowledge_engine_hints + **Re-Exports aller verschobenen Symbole** (viele Tests + sync.py/context/standalone/extensions/admin-server importieren `from lib.agents import X`). _YAML_AVAILABLE/_yaml müssen manuell re-exportiert werden (im try-block, nicht als Assign klassifiziert → vom Generator übersehen).
  - viz.py + skills.py auf frontmatter/provider_transform umgestellt (raus aus SCC).
  - **Ergebnis: SCC von 8 auf 3 Module {mcp, mcp_provider_config, rules} reduziert.** Gesamtes agents/config/context/skills/viz-Subsystem azyklisch.
  - Extraktion via AST-Generator: `scratchpad/split_agents.py` (klassifiziert Top-Level-Statements per Name → Modul, extrahiert via lineno/end_lineno). 0 Funktionen verloren/dupliziert (verifiziert).
- **#563 DONE (Branch `refactor/sync-main-dispatcher`, verifiziert):** main() von ~490 Z. auf 10 Statements. Struktur: `_build_arg_parser()`, `_SyncContext` (mutable shared-state Objekt), `_build_context()` (=Preamble/Early-Return-Modi verbatim, gibt None zurück wenn Early-Mode gehandhabt), 19 `_handle_*(ctx)`-Handler + `_MODE_HANDLERS` predicate-Table (Reihenfolge = alte if/elif-Kette, first-match-wins), `_dispatch()`, `_run_common_tail(ctx)`. **Kern-Trick für Verhaltenserhalt:** Handler-Bodies wurden VERBATIM (nur re-indented) übernommen — jeder Handler unpackt benötigte ctx-Felder in gleichnamige Locals, führt den unveränderten Body aus, schreibt danach `ctx.mode` (immer) + `ctx.config` (wo reloaded) zurück. Der einzige tail-relevante State, den Branches mutieren, ist `config` + `mode` — deshalb ist der "verflochtene Tail"-Einwand des Vorversuchs über das Context-Objekt lösbar. **Akzeptanzkriterium "--help zeigt Subcommands" NICHT erfüllt (unmöglich ohne CLI-Bruch):** Flag-Interface bleibt, echte Subparser wären Breaking Change → widerspricht "keine Regression" + Repo-Regel "keine Breaking Changes ohne Major-Bump". 4/5 Kriterien erfüllt. **Verifikation:** Baseline-Diff-Harness (`scratchpad/harness.sh`, PYTHONHASHSEED=0 nötig — rules-preset-Log-Zeile nutzt Set-Iteration = nicht-deterministisch) über 14 Modi byte-identisch + 2 Early-Modi (render-standalone/clear-cache) orig-vs-refactored byte-identisch + 801 passed/2 skipped.

## Residual-Zyklen (out of scope #565/#561)

1. `{mcp, mcp_provider_config, rules}` — MCP-Subsystem. mcp↔mcp_provider_config (re-export/Registry) + mcp↔rules (resolve_rules / build_mcp_guardrails_list). Eigenes Follow-up-Issue empfohlen.
2. `{external_tools, external_tools_drift}` — VORBESTEHEND, unabhängig von Wave 6.

**≤500-Zeilen-Kriterium (#561):** frontmatter/provider_transform/agent_sync >500, weil je eine kohäsive Kernfunktion (transform ~270, sync ~290 Z.) drinsteckt, die ohne Logik-Surgery (=Verhaltensrisiko) nicht teilbar ist. Bewusster Trade-off.

## Werkzeug: AST-Cycle-Detector

`scratchpad/depcycle.py <libdir>` — Tarjan-SCC über top-level+deferred relative Imports. Nachweis-Tool für "azyklisch".

## Test-Run

`python3 -m pytest tests/ -q -p no:homeassistant --ignore=tests/test_homeassistant` (~6.5 min). Baseline main@dd0c0f11 = 801 passed, 2 skipped.

NICHT committet — Hauptagent committet nach Review (ideal 3 Commits #565/#561/#563).
