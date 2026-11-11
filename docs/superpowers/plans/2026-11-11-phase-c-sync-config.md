# Phase C — Sync/Config-Robustheit Implementation Plan

> Status: DRAFT
> Base: `origin/main 9aa0e0c0` (nach PR #1218; vorher `a3d65da4`) | Roadmap: `docs/` Backlog-Roadmap 2026-11-10, Phase C (Welle 2) | Datum: 2026-11-11 | Überarbeitung: Entscheidungen 17-38 und 40-46, 52 eingearbeitet (2026-11-11)
> Issues (11): #1142, #1085, #1086, #1155, #1195, #1208, #1189, #1182, #1183, #1180, #1000
> Verschoben: #1141 nach Phase D, nach #1181 (Entscheidung 35; ersetzt Entscheidung 19), siehe Task 2.
> Abhängigkeiten (Roadmap §3): Welle 2, hängt ab von Phase B (gleiche Dateien `context.py`, `sync_pipeline.py`); #1000 braucht freigegebene Mini-Spec; parallel zu Phase E nur bei disjunkter `Files:`-Liste — **nicht disjunkt** (beide ändern `scripts/lib/sync_pipeline.py`; E zusätzlich `config.py`/`admin-server.py`, die Task 14 berührt; Phase-E-Plan :64 legt "E sequentiell nach C" fest), also C vor E; `#1086i` (`context.py`-Split) hat einen eigenen Plan und wird als eigener Nachfolge-PR **nach dem letzten** Phase-C-PR gemergt (Entscheidung 18, präzisiert durch 56: ist nach 52 ein Nachfolge-PR der Phase nötig, kommt #1086i erst danach).
> Tasks: 16 (Task 0, 0b, 1, 3-15; Task 2 entfernt). Phase-PR plus höchstens ein Nachfolge-PR für gesperrte/spec-gesteuerte Tasks (Entscheidung 52), ein Commit je Task (Entscheidung 17); Task 14 = 16 Commits, je #1189-Plan-Task einer (Entscheidung 36).

**Goal:** Sync/Config-Fehlerklassen "still akzeptiert / still falsch / exit 0" schließen, ohne Plain-Sync-Exit-Codes zu ändern (Entscheidungen 3, 4, 6, 8 sind bindend; 5 betrifft #1141 und wirkt nach Entscheidung 35 nicht mehr in diesem Plan).
**Architecture:** Eine Phase-PR (Branch `fix/phase-c-sync-config`, Vorschlag, von `origin/main`, ein Commit je Task; Entscheidung 17), höchstens ein Nachfolge-PR derselben Phase für zum Schnittzeitpunkt gesperrte Tasks (Entscheidung 52), plus der eigene Nachfolge-PR für #1086i nach dem letzten Phase-C-PR (Entscheidungen 18, 56; siehe Abschnitt "PR-Schnitt"). Fixes bleiben in den bestehenden Modulen (`sync_pipeline.py`, `cli_commands.py`, `config.py`, `log.py`, `context.py`, `generated_file_drift.py`, `progress_paths.py`); keine neue Provider-Verzweigung, Unterschiede nur über Config-Keys.
**Tech Stack:** Python 3.9+ (stdlib, PyYAML-Ausnahme), pytest, JSON-Schema (`config/project-config.schema.json`), GitHub Actions.
**Spec:** keine, siehe Task 0 Spec-Gate (gebündelte Spec für die M-Issues) und Task 0b (Mini-Spec #1000). #1189: bestehender APPROVED-Plan `docs/plans/2026-11-09-1189-tmp-sink-pin-plan.md` (Spec `docs/specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-spec.md`, APPROVED 2026-11-09) — **nicht** dupliziert, nur referenziert (Task 14).

`pipeline_stages`:
```yaml
pipeline_stages:
  implement: 3
```
(Stage-ID `implement` = Schritt-Gruppe Tasks 1-15 ohne Task 2; Tasks 0/0b sind das Spec-Gate davor.)

## Klassifikation (Spec/Plan-Gate)

| Issue | Klasse | Weg |
|---|---|---|
| #1142 | S | direkt (Entscheidung 3 ist die Spec-Aussage) |
| #1141 | M | **nicht in Phase C** — Phase D nach #1181 (Entscheidung 35; ersetzt 19), siehe Task 2 |
| #1085 | S-M | b/c: Spec-Abschnitt Task 0; a: **Entscheidung 34 (C-N2)**: nur dokumentieren, kein Auto-Enable |
| #1086 a-e | S je Punkt | direkt (Task 11) |
| #1086 g | S | **Entscheidung 24, bestätigt 38c**: nur Ist-Zustand dokumentieren, Punkt g per Entscheidungskommentar abschließen (#1086 bleibt offen, Entscheidung 46), kein Preset-Umbau (Task 12) |
| #1086 f | S-M | zurückgestellt (**Entscheidung 34, C-N4; bestätigt 38c**), kein Task in dieser Phase |
| #1086 h | S-M | Phase C, Task 12 (Teil 2; **Entscheidung 38c** bestätigt die Zuordnung). Spec-Abschnitt Task 0: es gibt **keinen** Code-Resolver für Keyword-Überlappungen (Auflösung macht das LLM; `get_routing_rules` `scripts/lib/delegation_table.py:289`, Rule-Dict :374-386, nur Detektor `check_keyword_overlap` `consistency/active_set_refs.py:408`), die `priority`-Semantik ist daher Design, nicht S |
| #1086 i | L | eigener Plan `docs/superpowers/plans/2026-11-11-phase-c-1086i-context-split.md` (anderer Worker), eigener Nachfolge-PR nach dem letzten Phase-C-PR (**Entscheidung 18; 38c; 52; 56**), nur Referenz (Task 15) |
| #1155 | M (Flag) / S (F10) | Flag (F5, Task 4): Spec-Abschnitt Task 0. F10 (Task 5): S, gemessen nur **1** Text-Mode-Aufruf ohne `encoding` (AST-Scan origin/main: `scripts/topology-probe.py:229`), kein Spec-Gate |
| #1195 | M | Spec-Abschnitt Task 0 |
| #1208 | M | Spec-Abschnitt Task 0 |
| #1182, #1183 | M (P1) | Spec-Abschnitt Task 0 |
| #1180 | S-M | Spec-Abschnitt Task 0 (Strategie-Wahl) |
| #1189 | M | existierender APPROVED-Plan, unverändert; Commits in der Phase-C-PR (**Entscheidung 36**, Task 14) |
| #1000 | M | Mini-Spec Task 0b; Implementierung erst nach APPROVED |

Kein Implementierungs-Task mit Klasse M darf vor `Status: APPROVED` der jeweiligen Spec starten. S-Tasks (1, 3, 5, 11) sind sofort ausführbar; Task 12 Teil h erst nach Task 0 (Teil g ist reine Doku/Kommentar).

## Global Constraints

- Python 3.9-kompatibel (`from __future__ import annotations`, kein `match`, kein `X | Y` zur Laufzeit), nur Stdlib + PyYAML.
- Provider-agnostisch: Unterschiede über Config-Keys/Capability-Flags (`pc["hooks_config_file"]` usw.), nie `if provider == "Name"`.
- Commits: Conventional Commits, Englisch, <= 72 Zeichen Subject, ein Commit pro Task; Bodies später als Datei. Trailer (`Co-Authored-By`, `Claude-Session`) sind von der Task-Prompt wörtlich vorgegeben; der `git`-Agent übernimmt sie unverändert (Entscheidung 25).
- Kein `isolation: "worktree"` beim Spawnen von Subagenten.
- Tests: `python3 -m pytest <datei>::<test>`; Gesamtgate: `python3 scripts/sync.py --validate`.
- Plain-`sync.py` behält Exit 0 für `[ERROR]`/`[P0]`-Logzeilen (Entscheidung 4). Test `tests/test_sync_end_checks.py` existiert (verifiziert: Glob-Treffer in W) und pinnt das laut Issue #1155.
- Vor Ausführung: `check_plan_refs.py` gegen `origin/main` (liegt nicht in `origin/main`, sondern im Worktree `.tmp/wt-check-plan-refs/scripts/check_plan_refs.py`; siehe A9).

## PR-Schnitt (Roadmap: "C (Teil-PRs)")

Entscheidung 17: ein PR pro Phase, gelockert durch **Entscheidung 52**: der Phase-C-PR enthält nur Tasks, die zum Schnittzeitpunkt ausführbar sind; gesperrte/spec-gesteuerte Tasks laufen in **einem** Nachfolge-PR derselben Phase (max. 2 PRs je Phase). Die früheren Teil-PRs C-1..C-5 bleiben verworfen (nur Plan-Stand, nichts gepusht). Entscheidung 18: #1086i bleibt eigener PR, zählt nicht zu den 2 Phasen-PRs und folgt als Nachfolge-PR nach dem letzten Phase-C-PR (Entscheidung 56; Tasks 7/8 ändern `context.py`).

Zuordnungsregel: Ein Task gehört in den Phase-C-PR, wenn sein Gate beim Schnitt erfüllt ist (S-Tasks 1, 3, 5, 11 sofort; Task 14 per APPROVED-#1189-Plan; Spec-Tasks erst nach `Status: APPROVED` von Task 0/0b). Ist Task 0 bzw. 0b beim Schnitt schon APPROVED, wandern die davon abhängigen Tasks samt Spec-Commit in den Phase-C-PR; sonst in den Nachfolge-PR. Die Tabelle zeigt den Fall "Specs noch nicht freigegeben".

| PR | Branch (Vorschlag) | Inhalt, ein Commit je Task | Reihenfolge |
|---|---|---|---|
| Phase-C-PR | `fix/phase-c-sync-config` | Commits aus Tasks 1, 3, 5, 11, 14 (16 Commits laut #1189-Plan) | 1. |
| Phase-C-Nachfolge-PR (Entscheidung 52) | `fix/phase-c-sync-config-gated` | Spec-Commits Tasks 0/0b zuerst, dann Tasks 4, 6, 12 (h; g ohne Commit), 13, 7, 8, 9, 10 (in dieser Reihenfolge; Task 10 nach 7-9, da der Render sich ändert) | 2. |
| #1086i-PR | `refactor/1086i-context-split` | Task 15 = eigener Plan `docs/superpowers/plans/2026-11-11-phase-c-1086i-context-split.md` | 3. (nach dem letzten Phase-C-PR, Entscheidungen 18, 56) |

Hinweis Task 14: der bestehende APPROVED-Plan #1189 nennt einen eigenen PR. Nach Entscheidung 17 wird er als Commits in der Phase-C-PR umgesetzt; seine PR-Angabe ist damit überholt. **Entscheidung 36:** #1189 ist keine PR-Ausnahme (Ausnahmen nur #1209 und #1086i); der APPROVED-Plan bleibt unverändert. Konflikt K1 ist damit **aufgelöst** (Abschnitt "Neue Konflikte").

Verworfene Teil-PRs (Historie): C-1 (Tasks 1-6, 11, 12), C-2 (Tasks 7-10), C-3 (Task 14), C-4 (Task 13), C-5 (#1086i) — alle durch Entscheidung 17/18 ersetzt. Die Konfliktstelle `config.py` (Task 2/5) entfällt, da Task 2 entfernt ist und Task 5 `config.py` nicht berührt.

## File Structure

- Modify `scripts/lib/sync_pipeline.py` — #1142 Allowlist-Gate (`_sync_stage_auto_commit_allowlist`, :1974-2005), #1195 Retention-Konstanten (:969-970) und `_prune_managed_sync_backups` (:1029-1039); #1085b P0-Aufrufstellen :1897 und :1899 (Anker origin/main 9aa0e0c0)
- Modify `scripts/lib/cli_commands.py` — #1142 config-audit-`auto_commit` (:1465-1467: `log.warning(f"config-audit [ERROR] auto_commit: ...")` **und** `consistency_errors += 1`, d.h. `--validate` endet schon heute mit rc 1, Exit :1532/:1534); #1085b/#1155 Exit-Pfad (`log.write` :1726-1727, `--check` :1731-1748)
- Summary-Formatter für `--validate` (verifiziert): `scripts/lib/consistency/report.py:102-115` (`_print_summary`, `N error(s)`, `N warning(s) found (M total findings)`), aufgerufen über `print_report` (:44) aus `_run_consistency_checks` `cli_commands.py:162-187`; zählt nur Consistency-Findings, **nicht** den config-audit-Zähler
- Modify `scripts/sync.py` — neue Flags `--fail-on-p0`, `--prune-sync-backups` (in `_build_arg_parser` :217; `--check` :334, `--prune-backups` :472); `_validate_doctor_flags` (:122) bleibt
- Modify `scripts/lib/log.py` — `SyncLog.warn(self, message: str)` (:39), Alias `warning(self, message: str)` (:55), `error(self, target: str, message: str)` (:59), `skip(self, target: str, reason: str)` (:70), `write` (:113) für 1086 c/d, P0-Feld
- Modify `scripts/lib/gitignore.py` — `detect_shadowed_provider_roots` Warntext (:507-514) für #1085c; einziger Aufrufer in `scripts/`: `scripts/lib/sync_pipeline.py:1893` (verifiziert, Import :1892)
- Modify `scripts/lib/hooks.py` — 1086b Text (:648-649)
- Modify `scripts/lib/mcp_provider_config.py` — 1086a Label: `_config_rel_label` :330-338 (verifiziert, siehe A5); Aufrufer :399, :427, :453, :621, :911
- Modify `scripts/lib/generated_file_drift.py` — #1195 Selektion (:147-196), Backup-Schreiben (:462-515)
- (entfällt in Phase C) `config/project-config.schema.json` und `scripts/lib/config.py` — #1141 wandert nach Phase D, nach #1181 (Entscheidung 35; ersetzt 19)
- Modify `scripts/lib/context.py` — #1182 `build_gate_card` (:2329-2373, Aufruf :3077), #1183 Embedded-Rules/Compact-Pfad (`_build_managed_block` ab :2603, Fallback-WARN :2958-2962, `compact_embedded_rule`-Aufruf :2963), #1086f: `init_claude_personal` :3099 (verifiziert; Punkt f zurückgestellt, nur Referenz)
- Modify `rules/1-generic/branch-guard.md` (:21), `rules/1-generic/repo-containment.md` (:5), `rules/1-generic/a2a-delegation-gates.md` (:17, :29, :44) — #1180 (Strategie aus Spec)
- Modify `scripts/lib/consistency/context_budget.py` — #1180 Check für relative Doc-Pfade neben `check_dangling_pointer` (:293, Check-ID `context.dangling-pointer` :56, verifiziert); #1086e `check_over_soft_cap` (:247-286)
- (kein Preset-Umbau) `config/tier-presets.yaml` — #1086g nur Ist-Zustand dokumentieren, Entscheidung 24 (Task 12)
- Modify `config/role-defaults.yaml` — #1086h `priority` (Routing-Block; `routing.priority` existiert nicht, A6); Detektor-Ort verifiziert: `scripts/lib/consistency/active_set_refs.py:408-423` (`check_keyword_overlap`, nur INFO, Registrierung `sync_pipeline.py:2080`); Emission der Routing-Regeln: `scripts/lib/delegation_table.py:289` (`get_routing_rules`)
- Modify `scripts/lib/progress_paths.py` (`ProgressPathFinding` :49, `resolve_progress_paths` :180), `scripts/lib/checkpoint.py` (verifiziert: `checkpoint_dir`-Parameter :338, Default-Zuweisung :367; kein `check-ignore`-Aufruf vorhanden), `snippets/orchestrator/checkpointing.md` — #1000
- Modify `scripts/topology-probe.py` — #1155 F10 (:229-236); laut AST-Scan (origin/main) die **einzige** Text-Mode-Stelle ohne `encoding` in `scripts/` (die "19" aus dem Issue sind überholt)
- Modify `AGENTS.md` (regeneriert) — #1208
- Modify `.github/workflows/validate.yml` — CI setzt `--fail-on-p0` am Plain-Sync-Schritt :126 (`python scripts/sync.py`; verifiziert). Weitere Workflows in W: `orchestration-test.yml` (:367 `--validate`), `scorecard.yml`. Step-Umgebung von :126 gelesen: Schritt "Generate sync output" nach `pip install -r requirements.txt` (:119-120), danach Drift-Gate (:134-141) und `--validate` (:142-143).
- Create `docs/specs/2026-11-11-phase-c-sync-config-spec.md`, `docs/specs/2026-11-11-1000-checkpoint-tracking-spec.md`
- Create Tests: `tests/test_auto_commit_invalid_sync.py`, `tests/test_fail_on_p0.py`, `tests/test_sync_backup_retention.py`, `tests/test_sync_log_output.py`, `tests/test_gate_card_modes.py`, `tests/test_compact_rule_fallback.py`, `tests/test_rule_doc_pointers.py`, `tests/test_check_context_drift.py`, `tests/test_routing_priority.py`, `tests/test_checkpoint_tracking.py`, `tests/test_subprocess_encoding.py` (entfallen: `tests/test_config_unknown_keys.py` → Phase D, #1141; `tests/test_tier_presets_max.py` → Entscheidung 24, kein Test)
- Vorhanden und verifiziert: `tests/test_sync_end_checks.py`, `tests/test_context_compact_mode.py` (Glob-Treffer in W)

## Abweichungen zur Roadmap (in W gegen Code verifiziert)

- **A1 (#1155):** Roadmap "F10 `topology-probe.py:232` offen" meint den Issue-Punkt F10 (Subprocess ohne `encoding`): `scripts/topology-probe.py:229-236` ruft `runner(..., text=True, ...)` ohne `encoding` — bestätigt. Aber F2 (`deactivation.py:279` zweiargig), F3 (`frontmatter.py:103-118` lässt Inhalt unverändert), F6 (`io.py:374-399` erhält Mode), F8 (`config.py:710` warnt), F9 (`pipelines.py:293-296` fängt nicht mehr `BaseException`) sind **bereits behoben** (Code-Kommentare "#1155"). F5 `--check` ist **bereits gebaut**: `cli_commands.py:1731-1748` exit 1 bei `log.errors`. Offen bleibt nur: F10 (AST-Scan origin/main: **1** Stelle, `topology-probe.py:229`; Issue-Zahl 19 überholt), F4/F7 (per Code-Lesen weitgehend behoben: F4 `config.py:311` Typ-Normalisierung, `hooks.py:447` `_strict_enabled`; F7 `write_atomic` in `config.py:1420/1486/1507`, `skill_admin.py:99`, `sync_pipeline.py:883`; Laufzeit-Nachweis bleibt Task 5 Step 5) und die Opt-in-Flag-Policy für Plain-Sync. Hinweis: SYMBOL_MISSING `BaseException` (Checker) ist ein Artefakt — der Plan nennt `pipelines.py:293-296`, der Checker sucht in `topology-probe.py`.
- **A2 (#1085):** `hooks.py:649` ist die Text-Zeile "registered in settings.json" (Roadmap korrekt), Issue nannte :611. `--strict` existiert nur für `--doctor` (`sync.py:122-131`, `_validate_doctor_flags` lehnt es sonst ab) — bestätigt.
- **A3 (#1086d):** Doppelausgabe bestätigt: `log.py:52-53` (Echo auf stderr) plus WARNINGS-Block in `write()` (:159-161, stdout-Print :183).
- **A4 (#1086c):** `log.py:77` (`skip`) und :166 (`{len(self.skipped)} skipped`); `hooks.py:593` ruft `log.skip(rel_out, "unchanged")` — Zähler mischt No-op-Writes und echte Skips, bestätigt.
- **A5 (#1086a):** Anker `mcp_provider_config.py:282-291` ist veraltet. `_config_rel_label` ist **verifiziert** bei `scripts/lib/mcp_provider_config.py:330-338`: Label = `path.relative_to(path.parent.parent)`, also für `<root>/.mcp.json` das Präfix `<checkoutname>/` — genau der Issue-Befund. Fix braucht `project_root` als Parameter; die 5 Aufrufer (:399, :427, :453, :621, :911) müssen angepasst werden.
- **A6 (#1086h):** Anker `active_set_refs.py:346-352` ist `check_dangling_mention`, **nicht** die Überlappungserkennung. Verifiziert: Überlappungs-Detektor ist `check_keyword_overlap` in `scripts/lib/consistency/active_set_refs.py:408-423` (IC-29, Severity INFO, Check-ID `routing.keyword-overlap` :58, registriert `scripts/lib/sync_pipeline.py:2080`). Er **meldet nur**, er löst keine Rolle auf. Einen Code-Resolver gibt es **nicht**: `get_routing_rules` (`scripts/lib/delegation_table.py:289`) baut aus `roles.<R>.routing` / `routing_patterns` neutrale Rule-Dicts (:358-386: `agent`, `tier`, `parallel`, `orchestrator_only`, `keywords`, `examples`, ...), die Auswahl trifft das LLM (Issue #1086 (h): "Resolution is left to the LLM"). `config/role-defaults.yaml` hat `routing` **je Rolle** (z.B. `orchestrator` :19-20, `developer` :27-30) und nirgends ein `priority`-Feld (Grep leer).
- **A7 (#1086g):** `config/tier-presets.yaml` Preset "Normal": top-level `max: claude-fable-5-1` (:39), aber `Claude.tiers.max: claude-opus-5-5` (:47) = `powerful` (:46), `ultra: claude-fable-5-1` (:48). Befund bestätigt für Claude; Gemini `max`=`powerful`=`ultra` = `gemini-3.1-pro-high` (:54-56) ebenfalls identisch. Umgang: Entscheidung 24 (nur dokumentieren, kein Umbau).
- **A12 (#1085c, Aufrufer):** `detect_shadowed_provider_roots` wird in `scripts/` nur von `scripts/lib/sync_pipeline.py:1893` aufgerufen (Import :1892). Die Warnung wird dort als `log.warning(f"[P0] {shadow_warning}")` (:1897) geloggt; eine **zweite** P0-Stelle ist `detect_invisible_keep_paths` (:1899). Weitere `[P0]`-Stellen in `scripts/`: keine (Grep).
- **A13 (#1000, Git-Helfer):** `run_git_check_ignore(target: str, cwd: str, *flags: str) -> "subprocess.CompletedProcess | None"` ist definiert in `scripts/lib/io.py:543` und in `scripts/lib/gitignore.py:29` importiert/benutzt (:496, :537). `checkpoint.py` und `progress_paths.py` enthalten heute **keinen** `check-ignore`-Aufruf: B ist Neubau, kein Teilfortschritt. Import-Zyklus geprüft: `progress_paths.py` importiert bereits `from .io import SyncError, _load_yaml_or_json` (:31), `io.py` importiert nur Stdlib (:4-12) — kein Zyklus.
- **A14 (#1142, Verifikation):** `_sync_stage_auto_commit_allowlist` :1974 gelesen; Verstoß-Warnung `sync_pipeline.py:1993-1996` (`auto_commit is invalid (...)`), danach `resolve_auto_commit_config` :1997 und `write_atomic` :2005 auch bei Verstoß. `auto_commit_violations` ist `scripts/lib/auto_commit.py:167`; Aufrufer `cli_commands.py:1465` (zählt `consistency_errors += 1`, :1467).
- **A8 (#1208):** Roadmap-Anker `context.py:2147` (Stand a41745ed) ist nicht der AGENTS.md-Writer. `AGENTS.md:140` gelesen (origin/main): `# CRITICAL GATE` ohne Suffix — passt zum Issue-Befund. `--check`-Blindstelle nicht reproduziert; `--check` zählt `len(log.actions)` (`cli_commands.py:1732`).
- **A9:** `scripts/check_plan_refs.py` existiert in `origin/main` nicht; der Checker liegt im Worktree `.tmp/wt-check-plan-refs/scripts/check_plan_refs.py` (Lauf 2026-11-11, siehe Review-Fragment).
- **A10 (#1000):** Optionswortlaut gegen `.tmp/issues/1000.md` geprüft: A = tracked location, B = warn/fail bei untracked/missing Referenz, C = Prozessregel (Status im selben PR). Entscheidung 8 "B+C" entspricht exakt der Issue-Empfehlung ("B as enforcement floor, C as process rule"). Keine Abweichung. `progress_paths.py:34-35` bestätigt (`DEFAULT_PROGRESS_DIR`, `DEFAULT_CHECKPOINT_DIR`), `checkpointing.md` nennt `.meta-viz/...` als Resume-Quelle (bestätigt).
- **A11 (#1183):** `context.py` enthält bereits `context.rule-reference-fallback` (:2958-2962) und den `compact_embedded_rule`-Aufruf (:2963, Definition :2241); `templates/context/agents-managed.md:8` gelesen: `{{#if CONTEXT_PROFILE_COMPACT}}{{> gate-card }}` ersetzt `rules-pointer`/`rules-embedded` (:9-13) — Issue-Befund bestätigt. `gate_card_sections` steht in `config/context-anchors.yaml:89-96` (7 Einträge).

**Re-Messung gegen Worktree-Stand 9aa0e0c0 (nach PR #1218; Grep/Read in W, 2026-11-11):**

Abweichung zur Roadmap = Zeilenanker, die sich verschoben haben. Review 2026-11-11: die Task-Texte sind auf diese Anker (origin/main 9aa0e0c0) umgeschrieben; die Spalte "alt" ist Historie.

| Anker (Plan) | Gemessen in 9aa0e0c0 | Status |
|---|---|---|
| `_sync_stage_auto_commit_allowlist` (Task 1; alt :1893) | `sync_pipeline.py:1974` (def) | **verschoben** (+81) |
| `detect_shadowed_provider_roots`-Aufruf (Task 3/4; alt :1811-1812) | `sync_pipeline.py:1893` | **verschoben** (+82) |
| `auto_commit is invalid`-Warnung (Task 1; alt :1912-1914) | `sync_pipeline.py:1995` | **verschoben** (+83) |
| `_prune_managed_sync_backups` (Task 6; alt :1005) | `sync_pipeline.py:1029` | **verschoben** (+24) |
| Retention-Konstanten (Task 6; alt :945-946) | `sync_pipeline.py:969-970` | **verschoben** (+24) |
| `config-audit ... auto_commit` (Task 1; alt :1437-1438) | `cli_commands.py:1466` | **verschoben** (+28) |
| `build_gate_card` (Task 7; alt :2170) | `context.py:2329` | **verschoben** (+159) |
| `_extract_rule_section` (Task 7; alt :2141) | `context.py:2300` | **verschoben** (+159) |
| `init_claude_personal` (Punkt 1086f, zurückgestellt; alt :2844) | `context.py:3099` | **verschoben** (+255) |
| `_config_rel_label` (Task 11 1d; :330-338) | `mcp_provider_config.py:330` | unverändert |
| `check_keyword_overlap` (Task 12 h; :408-423) | `consistency/active_set_refs.py:408` | unverändert |
| `run_git_check_ignore` (Task 13; :543) | `io.py:543` | unverändert |
| `select_prunable_sync_backups` / `backup_drifted_files` (Task 6; :147 / :462) | `generated_file_drift.py:147` / `:462` | unverändert |
| `auto_commit_violations` (Task 1; :167) | `auto_commit.py:167` | unverändert |
| `detect_shadowed_provider_roots` def (Task 3; :457) | `gitignore.py:457` | unverändert |
| `hooks.py` Text "registered in settings.json" (Task 11 1c; :649) | `hooks.py:649` | unverändert |
| `log.py` `warn` / `skip` / `write` (:39 / :70 / :113) | `log.py:39` / `:70` / `:113` | unverändert |
| `_validate_doctor_flags` (Task 4; :122-131) | `sync.py:122` | unverändert |
| CI Plain-Sync-Schritt (Task 4 Step 5; :126) | `.github/workflows/validate.yml:126` | unverändert |
| `topology-probe.py` `text=True` (Task 5; :229-236) | `topology-probe.py:232` | unverändert |

Befunde aus der Re-Messung:
- **Task 1 Step 3 (Summary-Frage) teilweise beantwortet:** `cli_commands.py:1465-1467` zählt den `auto_commit`-Verstoß im `--validate`-Pfad direkt in `consistency_errors` (`+= 1`); die Warnung in Zeile 1466 ist also der Validate-Pfad, nicht nur der Log-Text. Der Test aus Task 1 Step 1 muss trotzdem laufen, um zu bestätigen, dass `1 error(s)` tatsächlich ausgegeben wird (nicht ausgeführt).
- **Task 6 Step 1 (Konstanten):** `SYNC_BACKUP_MAX_PER_SOURCE = 3` und `SYNC_BACKUP_MAX_AGE_DAYS = 30` bei :969-970 bestätigt; `sync.py:97-98` importiert sie bereits (Preview-Parität). Total-Cap (`SYNC_BACKUP_MAX_TOTAL_PER_DIR`) existiert nicht (neu, Wert 30 nach Entscheidung 42).
- **Task 5 (F10, Zählung gemessen):** `git grep text=True` in `scripts/` (origin/main): 23 Zeilen in 15 Dateien. AST-Scan (jeder Call mit Keyword `text=True`/`universal_newlines=True` ohne `encoding`): **1** Treffer, `scripts/topology-probe.py:229` (`runner(...)`). `run_role_routing_eval.py:752` und `admin-server.py:1365` tragen `encoding="utf-8"` auf der Folgezeile (gelesen). Die Issue-Zahl 19 ist überholt.
- **Task 13 / A13:** `io.py:543` unverändert; Import-Zyklus geprüft, keiner (A13).
- Kein Befund zu Task 14 (#1189) in dieser Messung: `admin-server.py`-Anker liegen außerhalb der Re-Messung dieses Plans (Freshness-Pflicht laut Task 14 bleibt offen).

## #1086 — Vollständige Sub-Item-Zuordnung (a..i)

Roadmap: "8 von 9 offen, 1086e unverifiziert". Entscheidung 6 bindet nur g, h, i. a-e sind Kosmetik-S (Entscheidung 34, C-N4: jetzt). f ist zurückgestellt (Entscheidung 34, C-N4). g ist per Entscheidung 24 Doku-only. Acceptance des Issues: "fixed or closed with documented decision".

| Punkt | Status in W | Zuordnung |
|---|---|---|
| a MCP-Label | offen, Ort verifiziert (A5: `_config_rel_label` :330-338) | **dieser Plan**, Task 11 Step 1d (S, Entscheidung 34, C-N4) |
| b Hooks-Text | offen (`hooks.py:648-649` hartkodiert "settings.json") | Task 11 Step 1c |
| c Skip-Zähler | offen (A4) | Task 11 Step 1b |
| d Doppelausgabe | offen (A3) | Task 11 Step 1a |
| e Cap-Meldung | offen per Code-Lesen: `check_over_soft_cap` (`scripts/lib/consistency/context_budget.py:247-286`) meldet je Provider `f"{provider}: entry file has ..."` (:284) ohne Sharer-Liste; Laufzeit nicht reproduziert | Task 11 Step 1e (Test + Fix) |
| f Legacy-Notes | offen laut Roadmap; berührt `context.py` + `.gitignore`-Logik, Verhaltensänderung | **zurückgestellt** (Entscheidung 34, C-N4); Grund: Auto-Migration schreibt Nutzerdateien. Kein Task in Phase C. Ort-Referenz: `context.py` (Init-Pfad `init_claude_personal` :3099) |
| g Tier-Mapping | offen (A7) | **Entscheidung 24**: Ist-Zustand dokumentieren, Punkt g per Kommentar abschließen (#1086 bleibt offen, Entscheidung 46), kein Preset-Umbau (Task 12 Step 4) |
| h `priority` in role-defaults | offen (A6) | Task 12 (Teil 2) |
| i `context.py` splitten | offen | **eigener Nachfolge-PR** nach dem letzten Phase-C-PR (Entscheidungen 18, 52, 56), Task 15, nur Referenz |
| #1085a `hooks-auto-enable` | offen (Issue #1085, nicht #1086) | Entscheidung 34, C-N2: nur dokumentieren, kein Auto-Enable (Task 11 Step 1f) |

---

### Task 0: Spec schreiben + Freigabe-Gate (gebündelt)

**Rolle:** `concept-spec`/`ideation`-Rolle nach Orchestrator-Wahl (ein Agent: `senior-developer` schreibt, `requirements` reviewt).
**Files:** Create `docs/specs/2026-11-11-phase-c-sync-config-spec.md`
**Interfaces:** Produces: Spec mit `Status: APPROVED` und je einem Abschnitt pro M-Issue (#1085b, #1155-Flag, #1195, #1208, #1182, #1183, #1180, #1086h-`priority`-Semantik). Entscheidungen 17-38 sowie 40, 41, 42, 45 (früher U1, U2, U3, U9) sind bereits beantwortet (Abschnitt "Entscheidungen (beantwortet)"); die Spec übernimmt sie, entscheidet sie nicht neu. Die User-Freigabe der Spec (`Status: APPROVED`) bleibt trotzdem Pflicht. #1141 ist nicht Teil der Spec (Entscheidung 35).
**Blockiert:** Tasks 4, 6, 7, 8, 9, 10 (M) und Task 12 Teil h (kein Code-Resolver, A6). Nicht blockiert: Tasks 1, 3, 5, 11 (S); Task 12 Teil g (Doku-only, Entscheidung 24).

- [ ] Step 1: Spec-Entwurf mit Abschnitten und messbaren Akzeptanzkriterien je Issue (aus diesem Plan übernommen, nicht neu entschieden: Entscheidungen 3, 4, 8, 34, 40, 41, 42, 45).
- [ ] Step 2: Spec dem User zur Freigabe vorlegen (`Status: APPROVED`, Datum).
- [ ] Step 3: Verifikation: `python3 scripts/sync.py --validate-spec-plan` (Flag verifiziert: `scripts/sync.py:352`, Handler `_handle_validate_spec_plan` :101/:783). Erwartung: exit 0 (laut Help-Text :353-358: "Exit 0 when clean").
- [ ] Step 4: Commit `docs: add phase C sync/config spec`

**Abnahme:** Datei trägt `Status: APPROVED`; jeder M-Task referenziert den Abschnittsnamen.

### Task 0b: Mini-Spec #1000 Checkpoint-Tracking + Freigabe-Gate

**Rolle:** `senior-developer` (schreiben), User-Freigabe. Entscheidung 8 (B+C) ist beantwortet.
**Files:** Create `docs/specs/2026-11-11-1000-checkpoint-tracking-spec.md`
**Interfaces:** Produces: Spec, die B+C (Entscheidung 8) festschreibt. Consumes: `.tmp/issues/1000.md`.
Pflichtinhalt:
- Optionswortlaut (bestätigt, A10): **A** Referenzierte Checkpoints an getrackten Ort legen; **B** Warnung/Fehler, wenn ein Checkpoint in einen gitignorierten Ordner geschrieben oder ein untracked/fehlender Checkpoint-Pfad in Plan/Handoff zitiert wird; **C** Prozessregel: Umsetzungsstand im **selben PR** wie die dokumentierte Phase committen. Gewählt: B (Durchsetzungsboden) + C (Prozess); A nur optional, **nicht** Teil dieser Runde.
- B konkret: Erweiterung der Pfadauflösung in `scripts/lib/progress_paths.py` (`resolve_progress_paths`, :180) um `git check-ignore`-Prüfung des Checkpoint-/Progress-Verzeichnisses als **Finding** (`ProgressPathFinding`, :49, Level `warning`, Code `progress.checkpoint-dir-ignored`); Modul bleibt Leaf, Finding statt Exception; Git-Aufruf über die bestehende Hilfe `run_git_check_ignore` (definiert `scripts/lib/io.py:543`, in `gitignore.py:29` importiert, Nutzung :496) — kein Import-Zyklus (A13). Hinweis: dieses Repo ignoriert `.meta-viz/` (`.gitignore:54`), Default `DEFAULT_CHECKPOINT_DIR = ".meta-viz/checkpoints"` (`progress_paths.py:35`) → das neue Finding erscheint hier sofort; Opt-out-Weg ist der bestehende Key `progress.checkpoint-dir` (`progress_paths.py:7-9`, :43). Zweite Fläche: Validierung zitierter Checkpoint-Pfade (`--validate-spec-plan`-Pfad), Fehler bei untracked/missing.
- C konkret: Absatz in `snippets/orchestrator/checkpointing.md` + Planvorlage-Hinweis; Akzeptanz: Text benennt ephemer/clone-lokal vs. tracked.
- Akzeptanzkriterien = Issue-DoR 1-4.
- Verhalten ohne Git-Repo (**Entscheidung 43**): fail-soft, kein Fehler, Prüfung wird übersprungen (kein Finding, keine Exception).
- **Entscheidung 55** (beantwortet die Teilfrage aus 43): dieses Repo behält den Default `.meta-viz/` (gitignoriert, `.gitignore:54`), keine Umstellung auf einen getrackten Ort. Unterdrückungs-Key geprüft (origin/main): der `progress`-Block kennt nur `dir` und `checkpoint-dir` (`scripts/lib/progress_paths.py:41-43`); einen Key zum Unterdrücken einzelner Findings gibt es nicht (Grep `suppress`/`ignore-findings` in `scripts/`, `config/`: 0 Treffer). Ein neuer Key wäre nicht verlangte Zusatzfläche; gewählter Weg daher **dokumentiert hingenommen**: die Spec hält fest, dass `progress.checkpoint-dir-ignored` auf agent-meta selbst erwartet ist (Warnung, kein Exit-Wechsel), mit Verweis auf 55. Hinweis: `resolve_progress_paths` wird heute nur in `scripts/lib/checkpoint.py:388` aufgerufen und verwirft dort die Findings; die Ausgabefläche der Warnung (z.B. `--validate`) legt die Spec fest.

- [ ] Step 1: Entwurf (übernimmt Entscheidungen 8 und 43); Step 2: User-Freigabe (`Status: APPROVED`, weiterhin Pflicht); Step 3 Commit `docs: add checkpoint tracking mini-spec (#1000)`

**Abnahme:** `Status: APPROVED`. Task 13 ist vorher nicht ausführbar.

---

### Task 1: #1142 — ungültiges `auto_commit`: fail-soft, Allowlist nicht schreiben, Validate-Summary (Entscheidung 3)

**Klasse S. Rolle:** `developer`.
**Files:** Modify `scripts/lib/sync_pipeline.py` (`_sync_stage_auto_commit_allowlist(agent_meta_root, project_root, config, args, log, active_set) -> None`, :1974-2005; Warnung :1993-1996); Modify `scripts/lib/cli_commands.py` (config-audit-Ausgabe `auto_commit` **verifiziert** :1465-1467, heute `log.warning(f"config-audit [ERROR] auto_commit: ...")` plus `consistency_errors += 1`); Summary `scripts/lib/consistency/report.py:102-115` (`_print_summary`, zählt nur Consistency-Findings) bzw. `SyncLog.write`-Summary `log.py:165-170`; Create `tests/test_auto_commit_invalid_sync.py`.
**Interfaces:** Consumes `auto_commit_violations(config)` (Aufruf :1993), `resolve_auto_commit_config(config, active_roles, agent_meta_root)` (:1997), `write_atomic` (:2005). Produces: unverändert rc 0 in Plain-Sync; bei Verstoß kein Write; Validate-Summary nennt den Fehler.

Ist-Zustand (gelesen, origin/main 9aa0e0c0): Verstoß -> `log.warn(...)` (:1994-1996), danach wird die sanitisierte Allowlist **trotzdem** geschrieben (:2001-2005). `--validate` endet bereits heute mit rc 1 (#1091: `cli_commands.py:1465-1467` → Exit :1532/:1534); offen ist nur, dass der Fehler in keiner Summary als Error erscheint (er läuft über `log.warning`).

- [ ] Step 1 (Test, fail): `tests/test_auto_commit_invalid_sync.py` mit zwei Varianten (A: `mode: off` + `triggers: [task-boundary]`; B: `mode: custom` ohne `custom_script`), tmp-Projekt, `main()` von `sync.py` aufrufen (über `subprocess.run([sys.executable, "scripts/sync.py", "--config", cfg])`, `cwd` tmp). Assertions: `returncode == 0`; `not (proj/".meta-config/auto-commit-allowlist.json").exists()`; stderr enthält `auto_commit is invalid`. Dritte Variante (Entscheidung 44): vorhandene Allowlist mit bekanntem Inhalt vor dem Sync anlegen -> nach dem Sync byte-identisch (`read_bytes()` vorher == nachher). Zweiter Test `--validate`: `returncode == 1` und stdout/stderr-Zusammenfassung enthält `1 error(s)`.
- [ ] Step 2: `python3 -m pytest tests/test_auto_commit_invalid_sync.py -q` -> Erwartung (Plan-Wert, nicht ausgeführt): FAIL in den Plain-Sync-Tests (Allowlist existiert) und in der Summary-Assertion; `--validate`-rc 1 ist schon heute grün (#1091).
- [ ] Step 3 (implementieren): in `_sync_stage_auto_commit_allowlist` bei nicht leerer Verstoßliste `log.warn(...)`, dann **`return` vor dem Write**; eine bereits vorhandene (stale) Allowlist unverändert lassen und in der Warnung nennen (**Entscheidung 44**: nicht löschen, nicht überschreiben). In `cli_commands.py:1466` `log.warning(...)` durch `log.error("config-audit", f"auto_commit: {_ac_violation}")` ersetzen (Signatur `SyncLog.error(self, target: str, message: str)`, `log.py:59`); `consistency_errors += 1` (:1467) bleibt. Ob der `--validate`-Pfad `SyncLog.write` (Summary `log.py:165-170`, `N error(s)` nur bei `log.errors`) vor dem Exit :1532/:1534 erreicht, ist **nicht verifiziert**; `report.py:_print_summary` zählt den config-audit-Fehler nicht. Test in Step 1 entscheidet, welche Ausgabe den String trägt.
- [ ] Step 4: Test erneut -> PASS; `python3 -m pytest tests/test_sync_end_checks.py -q` -> PASS (Exit-0-Pin bleibt); `python3 scripts/sync.py --validate` -> exit 0 auf diesem Repo.
- [ ] Step 5: Commit `fix: skip allowlist write for invalid auto_commit (#1142)`

**Abnahme:** Variante A+B: Plain-Sync rc 0, keine Allowlist-Datei, stale Allowlist unverändert (Entscheidung 44), `--validate` rc 1 mit `1 error(s)` in der Summary.

### Task 2: #1141 — **verschoben nach Phase D, nach #1181** (Entscheidung 35; ersetzt Entscheidung 19)

Kein Task in dieser Phase. #1141 folgt in Phase D als letzter Teil der Phase-D-PR, nach #1181 (Kette #1187 → #1186 (E) → #1188 (F) → #1181 (D, Stream A) → #1141). Der Inhalt (Schema-Keys `rules-preset`/`test-repo`/`backup`/`mcp`, Unknown-Key-Warnung in `scripts/lib/config.py` :661-713, `config/project-config.schema.json`, Test `tests/test_config_unknown_keys.py`) wird dort neu geplant, Klasse M, benötigt eine APPROVED-Spec vorab. Entscheidung 5 (Warnung statt Fehler) bleibt für #1141 bindend. Die Task-Nummer 2 wird nicht neu vergeben.



### Task 3: #1085c — P0-Gitignore-Warnung nennt `ignore-provider-dirs`

**Klasse S. Rolle:** `developer`.
**Files:** Modify `scripts/lib/gitignore.py` (Warntext :507-514); Create `tests/test_fail_on_p0.py` (gemeinsam mit Task 4) oder erweitere bestehenden Gitignore-Test (Name nicht verifiziert).
**Interfaces:** Consumes `detect_shadowed_provider_roots(project_root: Path, providers: list[str], provider_config: dict, ignore_provider_dirs: bool) -> list[str]` (:457-462). Produces: Warntext mit Teilstring `gitignore: {ignore-provider-dirs: true}`.

Hinweis: Der Code-Pfad verhindert die Warnung bereits bei `ignore_provider_dirs=True` (:478), das Issue-Anliegen ist nur der Hinweis im Text.

- [ ] Step 1 (Test, fail): tmp-Git-Repo, `.gitignore` mit `.claude/agents/` außerhalb des Managed-Blocks, `detect_shadowed_provider_roots(root, ["Claude"], {"Claude": {"agents_dir": ".claude/agents"}}, False)`; Assertion: genau 1 Warnung, `"ignore-provider-dirs" in warning`.
- [ ] Step 2: pytest -> FAIL (Text nennt nur `gitignore.exceptions`).
- [ ] Step 3: Satz am Textende ergänzen: `For self-hosting repos set gitignore: {ignore-provider-dirs: true} to silence this warning.` (Englisch, konsistent mit Umgebungstext).
- [ ] Step 4: pytest -> PASS; bestehende Gitignore-Tests (`python3 -m pytest tests -q -k gitignore`) -> PASS.
- [ ] Step 5: Commit `fix: name ignore-provider-dirs in shadowing warning (#1085)`

### Task 4: #1085b / #1155-F5 — opt-in `--fail-on-p0`, CI setzt das Flag (Entscheidung 4)

**Klasse M. Voraussetzung: Task 0 APPROVED. Rolle:** `developer`.
**Files:** Modify `scripts/sync.py` (Parser nach `--check`-nahem Block; `_validate_*`-Hilfen :122-185 unberührt); Modify `scripts/lib/log.py` (`warn` :39 und Alias `warning` :55-57, der `p0` durchreichen muss; neues Feld in `__init__` :12-27); Modify `scripts/lib/sync_pipeline.py` (beide P0-Stellen, verifiziert: :1897 `log.warning(f"[P0] {shadow_warning}")` und :1899 `log.warning(f"[P0] {keep_warning}")`; dort `p0=True` setzen); Modify `scripts/lib/cli_commands.py` (Exit-Pfad: `log.write` :1726-1727, `--check` :1731-1748); Modify `.github/workflows/validate.yml` (Plain-Sync-Schritt :126, verifiziert); Modify `tests/test_fail_on_p0.py`.
**Interfaces:** Produces: `SyncLog.warn(self, message: str, p0: bool = False)` und `SyncLog.warning(self, message: str, p0: bool = False)` mit `self.p0: list[str]`; CLI-Flag `--fail-on-p0` (store_true). Consumes: `log.errors`.
Semantik (Spec-Abschnitt): Mit `--fail-on-p0` endet ein **Plain-Sync** mit Exit 1, wenn `log.p0` oder `log.errors` nicht leer ist; ohne Flag unverändert Exit 0. `--check` unverändert (exit 1 bei Actions oder `log.errors`, :1731-1748). `--strict` bleibt `--doctor`-exklusiv (`sync.py:122-131`, verifiziert in 9aa0e0c0; Entscheidung 34, C-N3, bestätigt durch **Entscheidung 38b**: einziges neues Flag ist `--fail-on-p0`). Der frühere Widerspruch zu Entscheidung 4 (Flag-Name #1085b) ist **aufgelöst**.

- [ ] Step 1 (Test, fail): (a) `SyncLog().warn("x", p0=True)`; `assert log.p0 == ["x"]` und Dedup-Verhalten bleibt (`_seen_warnings`). (b) tmp-Projekt mit Shadowing-Regel: `sync.py --config ...` rc 0; `sync.py --config ... --fail-on-p0` rc 1; stderr enthält `[P0]`. (c) tmp-Projekt ohne P0: mit Flag rc 0. (d) `sync.py --check --fail-on-p0` akzeptiert (kein argparse-Fehler).
- [ ] Step 2: `python3 -m pytest tests/test_fail_on_p0.py -q` -> FAIL.
- [ ] Step 3: Implementierung; beide P0-Warnungen (`sync_pipeline.py:1897`, :1899) mit `p0=True` loggen; Exit-Prüfung in `cli_commands.py` direkt nach `log.write(...)` (:1726-1727) und **nach** dem `--check`-Block (:1731-1748, endet immer mit `sys.exit`), damit `--check` unverändert bleibt.
- [ ] Step 4: pytest -> PASS; `python3 -m pytest tests/test_sync_end_checks.py -q` -> PASS (Plain-Exit-0 unverändert).
- [ ] Step 5: In `.github/workflows/validate.yml` den Plain-Sync-Schritt (:125-126, "Generate sync output", `python scripts/sync.py`) um `--fail-on-p0` ergänzen; vorher lokal `python3 scripts/sync.py --fail-on-p0` auf diesem Repo -> exit 0 (sonst bricht CI an `log.errors`, nicht an P0); YAML mit `python3 -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]))" <datei>` parsen -> kein Fehler.
- [ ] Step 6: ein Commit für Task 4 (Entscheidung 17): `feat: add --fail-on-p0 opt-in exit code (#1085)` (CI-Änderung im selben Commit im Body genannt)

**Abnahme:** Flag gesetzt + P0 vorhanden -> Exit 1; Plain ohne Flag Exit 0; CI-Datei enthält das Flag. Per Code-Lesen: CI dieses Repos erzeugt keine P0 — `ignore-provider-dirs: true` (`.meta-config/project.yaml:293`) schaltet die Shadow-Prüfung ab (`gitignore.py:478`), ohne `gitignore.keep` liefert `detect_invisible_keep_paths` nichts (`gitignore.py:533`). Das Flag wirkt in CI also nur über `log.errors` (nicht ausgeführt).

### Task 5: #1155 — verbleibende Punkte F10 (Subprocess-Encoding), Verifikation F4/F7

**Klasse S (gemessen: 1 Stelle; kein Spec-Gate). Rolle:** `developer`.
**Files:** Modify `scripts/topology-probe.py` (:229-236, `runner(list(argv), capture_output=True, text=True, timeout=timeout, check=False, env=env)`); AST-Scan origin/main: einzige Text-Mode-Stelle ohne `encoding` in `scripts/` (23 `text=True`-Zeilen in 15 Dateien, die übrigen 22 tragen `encoding`); Create `tests/test_subprocess_encoding.py`.
**Interfaces:** Consumes: Calls mit `text=True`. Produces: überall zusätzlich `encoding="utf-8", errors="replace"`.
Bereits behoben (nicht anfassen, nur Regressionstests nicht nötig): F2, F3, F5(`--check`), F6, F8, F9 (siehe A1).

- [ ] Step 1 (Test, fail): statischer Test mit `ast`: parse alle `scripts/**/*.py`; **jeder** `ast.Call` mit Keyword `text=True` (oder `universal_newlines=True`) muss Keyword `encoding` besitzen — nicht nur `subprocess.*`, da die offene Stelle über einen injizierten `runner(...)` läuft (`topology-probe.py:229`); Assertion: Liste der Verstöße leer. Zusätzlich Runtime-Test für `topology-probe._run` mit Fake-`runner`, der die übergebenen kwargs erfasst: `kwargs["encoding"] == "utf-8"`.
- [ ] Step 2: pytest -> FAIL mit genau 1 Verstoß `scripts/topology-probe.py:229` (gemessen per AST-Scan origin/main 9aa0e0c0; Issue-Zahl 19 überholt).
- [ ] Step 3: Die gelistete Stelle ergänzen (`encoding="utf-8", errors="replace"`).
- [ ] Step 4: pytest -> PASS; `python3 -m pytest tests -q -x` (Gesamtlauf oder CI-Shard) -> PASS.
- [ ] Step 5 (F4/F7 verifizieren): `hooks: {x: true}` und `viz: true` in tmp-Config -> `sync.py --validate` ohne `AttributeError` (hooks.py nutzt `_strict_enabled` :447, Aufruf :623-626; `config.py:311` normalisiert Nicht-Mapping-Blöcke zu `{}`); `project.yaml`-Schreibpfade nutzen per Code-Lesen bereits `write_atomic` (`config.py:1420`, :1486, :1507; `skill_admin.py:99`; `sync_pipeline.py:883`). Befund je Punkt: Laufzeit-Nachweis (Kommando oben, exit 0, kein `AttributeError`) als Evidenz im Issue-Kommentar; nur bei Fehlschlag neuer Test + Fix.
- [ ] Step 6: Commit `fix: set utf-8 encoding on text-mode subprocess calls (#1155)` (ein Commit für Task 5, Entscheidung 17)

**Abnahme:** AST-Test grün; F4/F7 mit Evidenz belegt oder behoben.

### Task 6: #1195 — globale Backup-Retention, Content-Dedup, CLI-Cleanup

**Klasse M. Voraussetzung: Task 0 APPROVED. Rolle:** `developer`.
**Files:** Modify `scripts/lib/generated_file_drift.py` (`select_prunable_sync_backups` :147-196, `backup_drifted_files` :462-515); Modify `scripts/lib/sync_pipeline.py` (Konstanten :969-970, `_prune_managed_sync_backups(project_root, config, provider_config, args, log) -> None` :1029-1039, `_managed_dirs_for_prune` :981); Modify `scripts/sync.py` (`--prune-sync-backups`, neben `--prune-backups` :472); Create `tests/test_sync_backup_retention.py`.
**Interfaces:** Consumes: `select_prunable_sync_backups(target_dir: Path, max_per_source: int, log: Optional[SyncLog] = None) -> list[Path]` (:147-151), `prune_sync_backups(target_dir, project_root, log, dry_run, max_age_days, max_per_source, ...)` (:199), `backup_drifted_files(findings: list[dict], project_root: Path, log: SyncLog, dry_run: bool = False) -> list[str]` (:462-464). Produces: erweiterte Signatur `select_prunable_sync_backups(target_dir: Path, max_per_source: int, log: Optional[SyncLog] = None, max_total: Optional[int] = None) -> list[Path]`; Konstante `SYNC_BACKUP_MAX_TOTAL_PER_DIR = 30` (**Entscheidung 42**); bei Überschreitung werden die ältesten Backups gelöscht, das neueste Backup je Quelle aber nie (Entscheidung 56, auch bei >30 Quellen), ausschließlich gitignorierte `*.sync-backup-*`-Dateien; `backup_drifted_files` überspringt Backups mit Inhalt identisch zum neuesten Backup derselben Quelle.
Parität: `--cleanup-preview` nutzt dieselbe Selektionsfunktion (Docstring :160-162) -> automatisch konsistent; Test sichert das.

- [ ] Step 1 (Tests, fail): tmp-Dir mit 10 Quellen x 3 Backups (30 Dateien) und `max_per_source=3`, `max_total=12` -> `len(select_prunable_sync_backups(...)) == 18`, und die jeweils neueste Datei je Quelle bleibt (Invariante: "newest of every source survives" bleibt, daher Total-Limit nur oberhalb `Quellen x 1`). Zusatzfall (Entscheidung 42): 12 Quellen x 3 Backups (36 Dateien), Default `max_total=30` -> 6 Kandidaten, alle aus den ältesten Zeitstempeln; eine nicht gitignorierte Datei `*.sync-backup-*` im Dir wird nie selektiert. Abgleich 42/56: Entscheidung 42 sagt "bei Überlauf von 30 je Dir älteste löschen"; Entscheidung 56 präzisiert, dass das neueste Backup jeder Quelle nie gelöscht wird, auch wenn die Quellenzahl > 30 ist (das Dir bleibt dann über 30). Zusatzfall (Entscheidung 56): 35 Quellen x 2 Backups (70 Dateien), Default `max_total=30` -> genau 35 Kandidaten (alle älteren), alle 35 Neuesten bleiben; Ergebnis 35 > 30 ist erwartet. (b) `backup_drifted_files` zweimal mit identischem `pre_text` und verschiedenen Zeitstempeln (Zeit patchen) -> nur 1 Datei. (c) `sync.py --prune-sync-backups --dry-run` auf tmp-Projekt listet, löscht nichts; ohne `--dry-run` löscht es auf `max_total`. (d) Bestehende Tests des Moduls bleiben grün (Name nicht verifiziert: `python3 -m pytest tests -q -k "sync_backup or cleanup_preview"`).
- [ ] Step 2: -> FAIL.
- [ ] Step 3: Implementieren (Dedup per `content_hash`-Vergleich mit neuestem Backup der Quelle; Total-Cap (30) nach Per-Source-Selektion auf die verbleibenden ältesten anwenden; vor dem Löschen per `run_git_check_ignore` (`scripts/lib/io.py:543`) sicherstellen, dass nur gitignorierte Backups fallen; CLI-Handler ruft `_managed_dirs_for_prune` + `prune_sync_backups`).
- [ ] Step 4: -> PASS; Steady-State-Test: 5 Syncs hintereinander mit Drift -> Anzahl <= 30 je Dir.
- [ ] Step 5: Commit `feat: bound sync-backup retention globally (#1195)`

**Abnahme:** Akzeptanzkriterien 1-4 des Issues je durch einen Test belegt. Verifiziert: Retention-Konstanten `sync_pipeline.py:969-970` (`SYNC_BACKUP_MAX_AGE_DAYS = 30`, `SYNC_BACKUP_MAX_PER_SOURCE = 3`). Nicht verifiziert: Windows-Verhalten.

### Task 7: #1182 — Compact-Profil bricht bei `orchestrator.mode != strict` nicht mehr ab

**Klasse M (P1). Voraussetzung: Task 0 APPROVED. Rolle:** `developer`. **Phase-C-PR.**
**Files:** Modify `scripts/lib/context.py` (`build_gate_card` :2329-2373, Aufrufer `local_vars["GATE_CARD"] = build_gate_card(...)` :3077-3079); Modify `scripts/lib/context_profile.py` (`context_profile_log_lines(config: dict, providers: Iterable[str]) -> List[str]` :184, Override-Warnung); Create `tests/test_gate_card_modes.py`.
**Interfaces:** Consumes: `build_gate_card(agent_meta_root: Path, config: dict, variables: dict, log: SyncLog) -> str` (:2329-2334), `_extract_rule_section(rule_text: str, heading: str) -> str | None` (:2300). Produces: Verhalten: fehlende **Überschrift** (Regel vorhanden) -> `log.warn("context.gate-card: section '<heading>' not rendered for orchestrator.mode=<mode>")` genau einmal, kein `SyncError`; fehlende **Regel** wirft weiter (:2355-2359).

Ist-Zustand (gelesen, origin/main 9aa0e0c0): `rules/1-generic/use-orchestrator.md:1-56` — alle `# CRITICAL GATE`-Varianten (:3, :15, :29, :42) stecken in `{{#if ORCH_MODE_STRICT}}`; der ADVISORY-Zweig (:57-63) hat die Überschrift `# Orchestrator` (:58), der MAIN_CHAT-Zweig (:64-80) `# Main-Chat Mode` (:65), aber keiner eine `CRITICAL GATE`-Überschrift -> `_extract_rule_section` liefert `None` -> `raise SyncError` (:2367-2371). Issue-Aussage bestätigt.
**Entscheidung 41** (früher U2): WARN + Sektion in der Gate-Karte auslassen, kein Reject-Pfad; Option 3 (Überschrift in advisory/main-chat-Branch) ist nicht geplant.

- [ ] Step 1 (Test, fail): `build_gate_card(AGENT_META_ROOT, {"platforms": [...], "orchestrator": {"mode": "advisory"}}, variables_for_mode("advisory"), log)`; `variables_for_mode` = Test-Helfer (neu, nur im Test) auf Basis der echten Quelle `_orch_mode_flags(orch_mode: str) -> dict` (`scripts/lib/variables.py:339`); die Flags sind **Strings** (`"true"`/`"false"`, :351-354), keine Bools — von Hand also `{"ORCH_MODE_ADVISORY": "true", "ORCH_MODE_STRICT": "false", "ORCH_MODE_MAIN_CHAT": "false"}`. Assertions: kein `SyncError`; `len([w for w in log.warnings if "CRITICAL GATE" in w and "advisory" in w]) == 1`; Rückgabe enthält `Git Delegation`. Gleich für `main-chat`. Zusätzlich End-to-End: tmp-Projekt `context-profile: compact` + `orchestrator.mode: advisory`, `sync.py` rc 0, `AGENTS.md` vorhanden.
- [ ] Step 2: pytest -> FAIL (`SyncError`).
- [ ] Step 3: Implementieren (Mode aus `config.get("orchestrator", {}).get("mode")`, Default-Wert **nicht verifiziert**; Mode im Text).
- [ ] Step 4: Zweiter Test (Override-Warnung): `context-profile: compact` + `context_file.mode: full` -> eine Warnung `context-profile.mode-override: ...` (Wortlaut aus Issue). -> FAIL, implementieren, PASS.
- [ ] Step 5: `python3 scripts/sync.py --validate` -> exit 0; `python3 -m pytest tests/test_context_compact_mode.py -q` -> PASS (bis auf bekannten #1208-Test, falls vor Task 10).
- [ ] Step 6: ein Commit für Task 7 (Entscheidung 17): `fix: render gate card per mode and warn on override (#1182)`

### Task 8: #1183 — Compact-Profil: keine still verlorenen Regeln ohne Skill/Pointer

**Klasse M (P1). Voraussetzung: Task 0 APPROVED, nach Task 7. Rolle:** `developer`. **Phase-C-PR.**
**Files:** Modify `scripts/lib/context.py` (Embedded-Rules-Schleife in `_build_managed_block` ab :2603, Compact-Zweig :2950-2970; `sync_compact_reference_skills` :2440; `compact_embedded_rule` :2241 — Issue-Anker :2604-2750/:2281/:2082 sind veraltet); Modify `templates/context/agents-managed.md` (:8 `{{#if CONTEXT_PROFILE_COMPACT}}{{> gate-card }}`, gelesen); Modify `config/context-anchors.yaml` (`gate_card_sections`, :89-96, gelesen); Create `tests/test_compact_rule_fallback.py`.
**Interfaces:** Produces: Warnung `context.rule-compacted-away: rule '<stem>' removed for provider '<p>' without a skills channel` genau einmal je Regel; Prädikat-Funktion `rule_reachable_in_compact(...)` (Name frei), von Block-Render **und** `sync_compact_reference_skills` gemeinsam benutzt.
Teilfortschritt: `context.rule-reference-fallback` existiert bereits (:2958-2962, nur für REFERENCE-Anteile) — Abgrenzung in der Spec.

- [ ] Step 1 (Test, fail): tmp-Projekt `ai-providers: [Claude, Opencode, Gemini]`, `context-profile: compact`, `orchestrator.mode: strict` (nach Task 7 auch advisory). Rendern `full` und `compact`. Assertion A: für jede Überschrift, die in `AGENTS.md`(full) steht, aber nicht in `AGENTS.md`(compact): (eingebettet) oder (Skill existiert **und** Pointer-Zeile im Block) oder (genau eine `context.rule-compacted-away`-WARN). Assertion B: für jede `.opencode/skills/<rule>/SKILL.md` existiert ein Verweis im Block (`<rule>` im AGENTS.md-Text). Assertion C: kein Fix für Soft-Cap erzwungen — nur falls Compact-Render > `context_soft_cap_chars` (12000), dann Warnung mit Begründung (Issue-Kriterium 4).
- [ ] Step 2: pytest -> FAIL.
- [ ] Step 3: Implementieren nach Spec-Entscheidung (Pointer-Zeile im Gate-Card-Partial für Regeln mit Skill-Channel; WARN für Regeln ohne Channel; Skill nur schreiben, wenn Block verweist).
- [ ] Step 4: pytest -> PASS; `python3 scripts/sync.py --validate` -> exit 0; `python3 -m pytest tests -q -k "context or compact"` -> PASS.
- [ ] Step 5: Commit `fix: add pointer or warning for rules dropped by compact (#1183)`

### Task 9: #1180 — Regeln verweisen auf `docs/concepts/*.md`, die Konsumenten nie bekommen

**Klasse S-M. Voraussetzung: Task 0 APPROVED (Strategie durch Entscheidung 40 fest). Rolle:** `developer`. **Phase-C-PR.**
**Files:** Modify `rules/1-generic/branch-guard.md` (:21 `docs/concepts/branch-guard-known-limits.md`), `rules/1-generic/repo-containment.md` (:5 `docs/concepts/repo-containment-prison-mode.md`), `rules/1-generic/a2a-delegation-gates.md` (:17, :29 `docs/concepts/active/orchestrator-topology.md`; :44 `docs/concepts/a2a-handoff-protocol.md`) — per `git grep` origin/main gemessen; Modify `scripts/lib/consistency/context_budget.py` (neuer Check neben `check_dangling_pointer` :293, verifiziert); Create `tests/test_rule_doc_pointers.py`.
**Interfaces:** Produces: Test `test_no_unresolvable_relative_doc_pointers`: scannt alle `rules/**/*.md`, extrahiert Backtick-Pfade `docs/...md`, und lässt keine zu (`docs/` wird nicht geliefert; keine Docs-URL-Variable, Entscheidung 40). Check `context.dangling-doc-pointer` (WARNING) für relative Markdown-Pfade in generierten Artefakten.
**Entscheidung 40** (früher U1): **Self-contain**. Kernlimits kurz inline in die jeweilige Regel; Verweise auf `docs/concepts/` entfallen; keine Docs-URL-Variable (es existiert auch keine, einziger Grep-Treffer `ANTHROPIC_DOCS_URL`, `model_discovery.py:47`, fremder Zweck). Absolutize und Deliver entfallen.

- [ ] Step 1 (Test, fail): Regex über `rules/1-generic/*.md`; Ausnahme: `docs/REQUIREMENTS.md` in `dod-criteria.md:4` (Projektdatei des Konsumenten, kein agent-meta-Doc). Assertion: Liste leer.
- [ ] Step 2: -> FAIL mit 5 Treffern in 3 Dateien (gemessen: `branch-guard.md:21`, `repo-containment.md:5`, `a2a-delegation-gates.md:17/:29/:44`).
- [ ] Step 3: Pointer entfernen und Kernlimits inline schreiben (Entscheidung 40): `branch-guard.md` Abschnitt `## Bekannte Grenzen` (:18-21) um die Lücken-Liste #551/#592/#809 und die Guard-Einstufung aus dem Concept-Doc ergänzen; `repo-containment.md:5` "Grenzen/Details" durch die Kerngrenzen in einem Satz ersetzen; `a2a-delegation-gates.md` :17/:29/:44 Verweis streichen, nötige Aussage inline. Zusatz-Assertion im Test: `branch-guard.md` enthält weiter `## Bekannte Grenzen` und `#809`; Check implementieren (`Finding(Severity.WARNING, "context.dangling-doc-pointer", rel, ...)` analog `active_set_refs.py`-Stil, `Finding` aus `lib.consistency`).
- [ ] Step 4: pytest -> PASS; `python3 scripts/sync.py --validate` -> exit 0.
- [ ] Step 5: ein Commit für Task 9 (Entscheidung 17): `fix: inline core limits instead of docs pointers in rules (#1180)`

### Task 10: #1208 — `--check` Blindstelle für `AGENTS.md`, Render nachziehen

**Klasse M. Voraussetzung: Task 0 APPROVED, **nach** Tasks 7-9 (Render ändert sich). Rolle:** `developer`. **Phase-C-PR (letzter Commit der Phase vor #1086i).**
**Files:** Modify `scripts/lib/context.py` / Schreibpfad der Context-Datei (Fundort der `--check`-Lücke **nicht lokalisiert**: `--check` zählt `len(log.actions)` (`cli_commands.py:1732`); der Context-Writer muss im Dry-Run eine Action loggen); Modify `AGENTS.md` (Regeneration); Create `tests/test_check_context_drift.py`; Bestehend `tests/test_context_compact_mode.py::test_committed_agents_md_equals_configured_mode_render`.
**Interfaces:** Consumes `log.actions`; Produces: Invariante "Test und `--check` widersprechen sich nie für `AGENTS.md`".

- [ ] Step 1 (Repro/Test, fail): tmp-Projekt, einmal `sync.py`, dann `AGENTS.md` im tmp um die Zeile `# CRITICAL GATE (runtime-partially enforced)` -> `# CRITICAL GATE` verfälschen; `sync.py --check --config ...` -> Assertion `returncode == 1` und stderr `out of sync`. (Die Blindstelle ist nicht reproduziert; schlägt der Test **nicht** fehl, ist die Ursache eine andere (z.B. Hash-Baseline-Drift-Logik): Befund festhalten, Task 0-Spec ergänzen, dann Fix in der tatsächlichen Stelle.)
- [ ] Step 2: pytest -> erwartet FAIL (Rc 0).
- [ ] Step 3: Fix: Context-Writer loggt bei abweichendem Inhalt eine Action (auch `dry_run`); Test grün.
- [ ] Step 4: `python3 scripts/sync.py` (Repo-Root) -> `AGENTS.md` regeneriert; `python3 scripts/sync.py --check` -> exit 0; `python3 -m pytest tests/test_context_compact_mode.py::test_committed_agents_md_equals_configured_mode_render -q` -> PASS.
- [ ] Step 5: ein Commit für Task 10 (Entscheidung 17): `fix: report context file drift in --check (#1208)` (regeneriertes `AGENTS.md` im selben Commit)

### Task 11: #1086 a-e — Sync-Ausgabe/Texte (Kosmetik)

**Klasse S je Punkt. Rolle:** `developer`. **Phase-C-PR.** Scope: a-e jetzt, f zurückgestellt (Entscheidung 34, C-N4); #1085a nur Doku (C-N2, Step 1f).
**Files:** Modify `scripts/lib/mcp_provider_config.py` (`_config_rel_label` :330-338, Aufrufer :399, :427, :453, :621, :911), `scripts/lib/hooks.py` (:648-649, :593), `scripts/lib/log.py` (:39-53, :70-77, :159-183), `scripts/lib/consistency/context_budget.py` (e: `check_over_soft_cap` :247-286), die übrigen `log.skip(..., "unchanged")`-Aufrufer (gemessen: 22 Stellen in 15 Dateien unter `scripts/`); Doku-Ort #1085a: Tool-Regeltext, **nicht lokalisiert**; Create `tests/test_sync_log_output.py`.
**Interfaces:** Produces: `SyncLog.skip(target, reason)` bleibt; neue Liste `SyncLog.unchanged` + `SyncLog.note_unchanged(target)`; Summary `N unchanged | M skipped`.

- [ ] Step 1a (1086d Test, fail): `SyncLog.warn("w")`, dann `write(tmp_path/"s.log", ...)` mit `capsys`; Assertion: `"w"` erscheint **einmal** in stderr+stdout zusammen (Ist: zweimal, A3); `sync.log`-Datei enthält es einmal. Fix: in `write()` den WARNINGS-Block im stdout-Print durch `WARNINGS: N (siehe oben)` ersetzen, Datei-Inhalt unverändert (Echo auf stderr bleibt für Abbruchpfade erhalten).
- [ ] Step 1b (1086c Test, fail): `hooks`-Aufruf mit unveränderter Datei -> `log.skipped == []` und `log.unchanged` enthält Eintrag; Summary-Text enthält `unchanged` und `skipped` getrennt. Fix `hooks.py:593` und alle `log.skip(..., "unchanged")`-Aufrufer (gemessen per `git grep -c 'log.skip(.*"unchanged")' origin/main -- scripts`: 22 Stellen in 15 Dateien, u.a. `cli_commands.py:1692`, `commands.py:277`, `context.py:3658`; beim Ausführen neu greppen).
- [ ] Step 1c (1086b Test, fail): Gemini-ähnliche Provider-Config (`hooks_config_file: ".agents/hooks.json"`) -> Note enthält `.agents/hooks.json`, nicht `settings.json`. Fix `hooks.py:648-649` mit `pc.get("hooks_config_file") or settings_file_rel` (verifiziert: `pc` in `sync_hooks` :488 im Scope, `settings_file_rel = pc.get("settings_file", ".claude/settings.json")` :490; Quelle `config/ai-providers.yaml:178` `hooks_config_file: .agents/hooks.json` im Gemini-Block :135-251 — Issue-Anker :156-158 veraltet).
- [ ] Step 1d (1086a Test, fail): `_config_rel_label(Path(root)/".mcp.json")` -> `".mcp.json"` (Ist laut Issue: `<checkout>/.mcp.json`). Funktion ist lokalisiert (`_config_rel_label` :330-338, A5); Label relativ zu `project_root` (neuer Parameter, alle 5 Aufrufer anpassen).
- [ ] Step 1e (1086e Test, fail): `check_over_soft_cap(root, ["Gemini", "Opencode"], caps, active_set, report)` mit zwei Providern, die dieselbe `context_file` `AGENTS.md` teilen (nur Gemini mit `context_soft_cap_chars`); Assertion: genau 1 Finding, Message enthält `shared with: Opencode`. Ist (Code gelesen, :282-285): Message nennt nur `Gemini`. Fix: Sharer je `context_file` sammeln und anhängen.
- [ ] Step 1f (#1085a, Entscheidung 34 C-N2): **nur Dokumentation**, kein `hooks-auto-enable`. Ort des Tool-Regeltexts zum Hook-Aktivieren vor dem Schreiben per `git grep -n "hooks:" rules/ snippets/ docs/` lokalisieren (heute nicht lokalisiert); Issue-Kommentar mit dem begründeten Nicht-Auto-Enable (Acceptance: "documented reason"). Doku-Änderung geht in den **einen** Task-11-Commit (Step 3), kein eigener Commit.
- [ ] Step 2: jeweils `python3 -m pytest tests/test_sync_log_output.py::<test> -q` -> FAIL, dann Fix, dann PASS. Gesamt: `python3 -m pytest tests -q -k "log or hooks or mcp"` -> PASS; `python3 scripts/sync.py --validate` -> exit 0, keine neuen Warnungen (Acceptance 2 des Issues).
- [ ] Step 3: ein Commit für Task 11 (Entscheidung 17): `fix: correct sync log, hook and MCP label texts (#1086)` (Body später als Datei; Punkte a-e und die #1085a-Doku im Body aufzählen)

### Task 12: #1086 h (+ g nur Doku) — `priority`-Tiebreak und Tier-Ist-Zustand

**Klasse g: S (Doku); h: S-M, Voraussetzung Task 0 APPROVED (Spec-Abschnitt `priority`-Semantik). Rolle:** `developer`. **Phase-C-PR.**
**Files:** Modify `config/role-defaults.yaml` (h, `roles.<R>.routing`); Modify `scripts/lib/delegation_table.py` (`get_routing_rules` :289, Rule-Dict :374-386 um `priority` ergänzen); Modify `scripts/lib/consistency/active_set_refs.py` (`check_keyword_overlap(project_root: Path, active_providers: Sequence[str], capabilities: Mapping[str, Mapping], active_set) -> list` :408-423, INFO); einen Code-Resolver gibt es nicht (A6); Create `tests/test_routing_priority.py`. `config/tier-presets.yaml` wird **nicht** geändert (g, Entscheidung 24).
**Interfaces (h):** Consumes `roles.<R>.routing_patterns.keywords` (verifiziert: `active_set_refs.py:416-417`). Produces: optionales `routing.priority` (int).

(g) **Entscheidung 24** (beantwortet, ersetzt die frühere Frage N1): Ist-Zustand dokumentieren und #1086g mit Entscheidungskommentar schließen; kein Tier-Umbau, kein Preset-Test. Ist-Zustand (A7): Preset `Normal` Claude `max` = `powerful` = `claude-opus-5-5`, `ultra` = `claude-fable-5-1`; Gemini `max` = `powerful` = `ultra` = `gemini-3.1-pro-high`. Die Doku-Stelle ist der Issue-Kommentar (kein Commit).

(h) `priority`: neues optionales Feld `routing.priority: <int>` (höher gewinnt) je Rolle in `config/role-defaults.yaml`. Da das LLM auflöst (A6), kann `priority` nur **emittiert** werden: als Feld im Rule-Dict von `get_routing_rules` und als Zusatz in der `check_keyword_overlap`-Message (z.B. "resolved by priority: <role>"); bei Gleichstand bleibt es "detected only". **Entscheidung 45** (früher U9): nur emittieren, kein Verhaltenswechsel; Overlaps werden weiter gemeldet (Severity INFO unverändert). Schema-Pfad für `role-defaults` (falls es ein Schema gibt, **nicht verifiziert**) ergänzen.

- [ ] Step 1 (Test h, fail): zwei Fake-Rollen mit Keyword `refactoring`, `routing.priority` 10 vs 0 -> `get_routing_rules(...)` liefert für beide Rollen ein Rule-Dict mit `"priority"` 10 bzw. 0, und `check_keyword_overlap` nennt die Rolle mit 10 in der Message; ohne `priority` sind Rule-Dict (ohne Key oder Default laut Spec) und Message unverändert (Rückwärtskompatibilität). Zusatz (Entscheidung 45): mit Prioritätsunterschied wird der Overlap weiterhin gemeldet (Anzahl Findings gleich wie ohne `priority`, Severity unverändert).
- [ ] Step 2: -> FAIL; Step 3: Implementierung in `delegation_table.py` und `active_set_refs.py`; `python3 scripts/sync.py --validate` -> exit 0.
- [ ] Step 4 (g, Entscheidung 24): Entscheidungskommentar zu Punkt g in #1086 posten (Ist-Zustand aus A7, Begründung "kein Tier-Umbau"), erst nach Freigabe; g ist ein Unterpunkt, das Issue #1086 selbst wird damit nicht geschlossen. **Kein** Preset-Umbau, **kein** Rendern betroffener Agenten (`principal-developer` bleibt unverändert).
- [ ] Step 5: ein Commit für Task 12 (Entscheidung 17): `feat: add routing priority tiebreak to role defaults (#1086)` (g nur Doku, kein Commit für Preset)

### Task 13: #1000 — Checkpoint-Tracking B+C umsetzen

**Klasse M. Voraussetzung: Task 0b APPROVED. Rolle:** `developer`. **Phase-C-PR.**
**Files:** Modify `scripts/lib/progress_paths.py` (`resolve_progress_paths` :180-237, `ProgressPathFinding` :49-54); Modify `scripts/lib/checkpoint.py` (verifiziert: `checkpoint_dir`-Parameter :338, Default :367; kein `check-ignore` vorhanden; Schreib-Logik nicht vollständig gelesen); Modify `snippets/orchestrator/checkpointing.md` (Absatz zu `.meta-viz/...` :2, :28-31, Prozessregel C); Create `tests/test_checkpoint_tracking.py`.
**Interfaces:** Consumes `resolve_progress_paths(project_root: Path, config: Optional[dict] = None) -> ResolvedProgressPaths` (:180-183), `ProgressPathFinding(level: str, code: str, message: str)` (:49-54), `run_git_check_ignore(target: str, cwd: str, *flags: str)` (`io.py:543`). Produces: neue Findings mit Code `progress.checkpoint-dir-ignored` (Level `warning`), keine Exception; Regressionsfall "untracked/missing Checkpoint-Referenz".

- [ ] Step 1 (Test, fail): tmp-Git-Repo mit `.gitignore` `.meta-viz/`; `resolve_progress_paths(root)` -> `any(f.code == "progress.checkpoint-dir-ignored" for f in result.findings)`; mit `progress: {checkpoint-dir: docs/checkpoints}` (nicht ignoriert) -> kein Finding; ohne `.git` -> kein Finding, keine Exception, kein Fehler im Log (Entscheidung 43: Prüfung übersprungen). Plan-Referenz-Test: Datei `plan.md` zitiert `.meta-viz/checkpoint-x.json` -> Validator meldet Fehler (Oberfläche aus Spec).
- [ ] Step 2: -> FAIL; Step 3: implementieren (`run_git_check_ignore` aus `scripts/lib/io.py:543`, fail-soft: `None` -> kein Finding; kein Import-Zyklus, A13); Snippet-Text ergänzen (ephemer vs. tracked; Regel C: Umsetzungsstand im selben PR).
- [ ] Step 4: pytest -> PASS; `python3 scripts/sync.py --validate` -> exit 0 (dieses Repo ignoriert `.meta-viz/` per `.gitignore:54` und setzt keinen `progress`-Block → **neue Warnung** auf diesem Repo sicher; Finding ist Warnung, kein Exit-Wechsel. **Entscheidung 55:** keine Umstellung, Default `.meta-viz/` bleibt; die Warnung wird dokumentiert hingenommen, da kein Unterdrückungs-Key existiert (`progress_paths.py:41-43`, siehe Task 0b); Erwartung: Warnung vorhanden, `--validate` exit 0).
- [ ] Step 5: ein Commit für Task 13 (Entscheidung 17): `feat: warn when checkpoint dir is gitignored (#1000)` (Snippet-Regeln im selben Commit)

### Task 14: #1189 — admin-server Tmp-Sink-Pin (Referenz, nicht neu geplant)

**Klasse M. Rolle:** laut Plan. **Phase-C-PR** (Entscheidung 36: die #1189-Tasks laufen als Commits im C-PR; der #1189-Plan schreibt "Ein Commit pro Task" vor, `docs/plans/2026-11-09-1189-tmp-sink-pin-plan.md:133` → **16 Commits**, Subjects laut #1189-Plan; nicht mehr eigener PR C-3).
Ausführung exakt nach `docs/plans/2026-11-09-1189-tmp-sink-pin-plan.md` (`status: APPROVED` :4, Spec APPROVED 2026-11-09, 16 Tasks in 2 Einheiten: Tasks 1-10 / 11-15 + Task 16 Doku, :22-23). Stand origin/main: noch nicht umgesetzt (`system_temp_root`, `resolve_sink_absolute`, `_probe_port_bindable` per Grep nicht vorhanden; Issue OPEN). Dieser Plan fügt hinzu:
- **Freshness-Pflicht:** Base des Plans war `main @ 7e52f571` (:6); vor Start gegen `origin/main 9aa0e0c0` re-verifizieren (Zeilenanker `admin-server.py:311`, :650, :659, `config.py:888-937`, `tmp_paths.py:298` neu prüfen). Nicht verifiziert.
- **Reihenfolge:** Commits innerhalb der Phase-C-PR; `config.py` wird in dieser Phase nur hier geändert (Task 2 entfernt, Entscheidung 35), daher kein Konflikt mehr zu anderen Tasks.
- **Kommentar des Issues (2026-11-08):** Pin bricht auch jeden Kindprozess eines laufenden Servers (`_run` :1369, Consistency-Check :1749, Viz/MCP :6032/:6038 laut Issue). Prüfen, ob der APPROVED-Plan diese Aufrufstellen abdeckt (Spec Revision 4 ist laut Plan "RVW"-gereviewt); falls nicht: Lücke als Rückfrage an den User, nicht still erweitern.
- Commit-Subjects: laut bestehendem Plan.

### Task 15: #1086i — `context.py`-Split (Referenz, eigener Plan, zuletzt)

`docs/superpowers/plans/2026-11-11-phase-c-1086i-context-split.md` (anderer Worker, Klasse L, Entscheidung 6). Reihenfolge-Pflicht (Entscheidung 18, präzisiert durch 56): eigener Nachfolge-PR **nach dem letzten** Phase-C-PR (Entscheidung 52: das ist der Nachfolge-PR, falls Tasks 7/8 dort laufen; `context.py` wird in Tasks 7/8 geändert, muss also vorher gemergt sein); Tests vorher grün, kein Verhaltenswechsel. Punkt 1086f ist zurückgestellt (Entscheidung 34, C-N4). Dieser Plan dupliziert nichts davon.

---

## Entscheidungen (beantwortet)

Quelle: Roadmap-Entscheidungen 17-34 (`.tmp/decisions-part2.md`, verbindlich). Originalkennung der Plan-Frage in Klammern.

- **Entscheidung 17 (PR-Schnitt):** eine Phase-PR, ein Commit je Task; Teil-PRs C-1..C-5 verworfen. Umgesetzt im Abschnitt "PR-Schnitt".
- **Entscheidung 18 (#1086i):** eigener PR direkt nach der Phase-C-PR; **Entscheidung 56** löst 18 vs. 52: Nachfolge-PR nach dem **letzten** Phase-C-PR. Umgesetzt in Task 15.
- **Entscheidung 40 (U1, #1180):** Self-contain, Kernlimits inline, keine `docs/concepts/`-Verweise, keine Docs-URL-Variable. Umgesetzt in Task 9.
- **Entscheidung 41 (U2, #1182):** WARN + Sektion in der Gate-Karte auslassen, kein Reject-Pfad, Option 3 nicht geplant. Umgesetzt in Task 7.
- **Entscheidung 42 (U3, #1195):** `SYNC_BACKUP_MAX_TOTAL_PER_DIR = 30`, bei Überschreitung älteste löschen, nur gitignorierte `*.sync-backup-*`. **Entscheidung 56** präzisiert für >30 Quellen: das neueste Backup je Quelle bleibt immer, danach älteste löschen. Umgesetzt in Task 6.
- **Entscheidung 43 (U4, #1000):** ohne Git-Repo fail-soft, Prüfung übersprungen. Umgesetzt in Task 0b und Task 13. Teilfrage `progress.checkpoint-dir` beantwortet durch **Entscheidung 55** (Default bleibt, Warnung dokumentiert hingenommen; Task 0b, Task 13 Step 4).
- **Entscheidung 44 (U5, #1142):** stale Allowlist bei ungültiger Config unverändert liegen lassen. Umgesetzt in Task 1.
- **Entscheidung 45 (U9, #1086h):** `priority` nur emittieren (Rule-Dict + Overlap-Meldung), kein Verhaltenswechsel. Umgesetzt in Task 12.
- **Entscheidung 46 (U11, #1086):** #1086 bleibt OFFEN, bis Punkt f entschieden oder bewusst verworfen ist; kein Schließ-Schritt für #1086 in diesem Plan (auch nicht nach a-e, g, h, i).
- **Entscheidung 52 (PR-Schnitt gesperrter Tasks):** Phase-C-PR nur mit ausführbaren Tasks, gesperrte/spec-gesteuerte in einem Nachfolge-PR (max. 2 PRs je Phase). Umgesetzt im Abschnitt "PR-Schnitt".
- **Entscheidung 19 (#1141):** verschoben nach Phase F, hinter #1188; Task 2 entfernt; Phase C = 11 Issues. **Durch Entscheidung 35 ersetzt** (Phase D, nach #1181); Phase C bleibt 11 Issues.
- **Entscheidung 35 (#1141 → Phase D):** #1141 in Phase D nach #1181 (Kette #1187 → #1186 → #1188 → #1181 → #1141). Umgesetzt in Task 2 (Verweis), Klassifikation, Frische-Check. Phase C = 11 Issues (unverändert).
- **Entscheidung 36 (PR-Ausnahmen):** nur #1209 und #1086i sind PR-Ausnahmen; #1189 ist **keine** Ausnahme und läuft als Commits in der Phase-C-PR. Der APPROVED-Plan #1189 bleibt unverändert. Umgesetzt in Task 14 und PR-Schnitt (ersetzt dort die "eigener PR"-Angabe des #1189-Plans, Entscheidung 17 gilt).
- **Entscheidung 38b (#1085b Flag):** einziges neues Flag `--fail-on-p0`; `--strict` bleibt `--doctor`-exklusiv. Widerspruch zu Entscheidung 4 **aufgelöst**. Umgesetzt in Task 4.
- **Entscheidung 38c (#1086):** g nur Dokumentation/Schließen (24), a-e jetzt (Task 11), f zurückgestellt (34, C-N4), h gehört zur Phase C (Task 12, Teil 2), i eigener PR (Task 15). Alle vier Zuordnungen in der Sub-Item-Tabelle "#1086 — Vollständige Sub-Item-Zuordnung" stimmen damit überein.
- **Nicht Teil dieses Plans (38a, 38d, 38e, 38f):** 38a (#1210), 38d (#329/#330), 38e (Auto-Close Phase A) und 38f (#1190) betreffen andere Phasen; hier nicht umgesetzt. Die Nutzerregel aus 38e (Issues nur mit Evidenz-Kommentar schließen) wird hier übernommen: Commit- und PR-Texte der Phase-C-PR enthalten **keine** Schlüsselwörter `Closes/Fixes/Resolves`; Schließen erfolgt manuell nach Kommentar.
- **Entscheidung 25 (Trailer):** Global Constraint korrigiert; Trailer sind von der Task-Prompt vorgegeben und werden vom `git`-Agenten unverändert übernommen.
- **Entscheidung 3, 4, 8 (Konsistenz geprüft):** Task 1 (#1142 fail-soft, Validate rc 1), Task 4 (Plain-Sync Exit 0, `--fail-on-p0` opt-in), Task 13 (#1000 B+C) stimmen überein. Entscheidung 5 gilt für #1141 und ist mit Entscheidung 35 nicht mehr Teil dieses Plans.

- **N1 (#1086g Tier `max` vs `powerful`/`ultra`) → Entscheidung 24:** Ist-Zustand dokumentieren, Issue mit Entscheidungskommentar schließen, kein Tier-Umbau. Umsetzung: Task 12 Step 4. Optionen (a)/(b) entfallen.

- **N2 (#1085a `hooks-auto-enable`) → Entscheidung 34, C-N2:** nur dokumentieren, kein Auto-Enable. Umsetzung: Task 11 Step 1f.
- **N3 (Flag-Name #1085b) → Entscheidung 34, C-N3, bestätigt 38b:** nur `--fail-on-p0` (neu); `--strict` bleibt `--doctor`-exklusiv (`sync.py:122-131`). Umsetzung: Task 4.
- **N4 (Umfang #1086 a-f) → Entscheidung 34, C-N4, bestätigt 38c:** a-e jetzt (Task 11), f zurückgestellt. Umsetzung: Task 11, Tabelle "#1086 — Vollständige Sub-Item-Zuordnung".

## Offene Entscheidungen (neu, ungeklaert)

Durch Entscheidungen 1-57 nicht gedeckt. Nur echte Entscheidungen (Spec-Wahl mit User-Freigabe in Task 0/0b oder direkte User-Frage); Prüf-/Messpunkte sind Tasks (Liste unten).

- keine (die #1000-Teilfrage ist durch Entscheidung 55 beantwortet).

Beantwortet (siehe "Entscheidungen (beantwortet)"): U1 -> 40, U2 -> 41, U3 -> 42, U4 -> 43 (Teilfrage `progress.checkpoint-dir` -> 55), U5 -> 44, U9 -> 45, U11 -> 46.

In Tasks überführt (keine User-Frage): U6 (#1155 F4/F7) → Task 5 Step 5 (Code-Lesen: weitgehend behoben, Laufzeit-Nachweis offen); U7 (#1208 Ursache) → Task 10 Step 1; U8 (#1086e) → Task 11 Step 1e (Code-Lesen: Befund offen, Test + Fix); U10 (#1085a Ort) → Task 11 Step 1f.

## Nicht verifiziert

Verifiziert in dieser Überarbeitung (Grep/Read/Glob im Worktree W, Evidenz im Text):
- `validate-summary`: config-audit `auto_commit` in `cli_commands.py:1465-1467` (rc 1 schon heute); Summary-Formatter `consistency/report.py:102-115` zählt den Fehler nicht; ob `SyncLog.write` im `--validate`-Pfad läuft, offen (Task 1 Step 3).
- Aufrufer `detect_shadowed_provider_roots`: nur `sync_pipeline.py:1893` in `scripts/`; zweite P0-Stelle :1899.
- `_config_rel_label`: `mcp_provider_config.py:330-338`, 5 Aufrufer (:399, :427, :453, :621, :911).
- Keyword-Überlappungs-Detektor (#1086h): `consistency/active_set_refs.py:408-423`; kein Code-Resolver, Emission über `delegation_table.py:289` (A6).
- CI-Datei: `.github/workflows/validate.yml` (Plain-Sync :126, `--validate` :143); weitere: `orchestration-test.yml` (:367), `scorecard.yml`. CI erzeugt per Code-Lesen keine P0 (Task 4 Abnahme).
- `tests/test_sync_end_checks.py`: vorhanden. `tests/test_context_compact_mode.py`: vorhanden (`test_committed_agents_md_equals_configured_mode_render` :505).
- `checkpoint.py`: `checkpoint_dir` :338/:367; kein `check-ignore`-Aufruf (B ist Neubau). Kein Import-Zyklus (A13).
- `init_claude_personal`: `scripts/lib/context.py:3099`.
- `context_budget.py`: `check_dangling_pointer` :293, `check_over_soft_cap` :247-286 (1086e offen per Code).
- `templates/context/agents-managed.md:8`, `config/context-anchors.yaml:89-96`: gelesen.
- F10: AST-Scan 1 Stelle (`topology-probe.py:229`).
- Zeilenanker dieses Plans: gegen origin/main 9aa0e0c0 per `git grep`/`git show` neu gemessen (Review 2026-11-11), außer den unten genannten.

Nicht verifiziert (Stand nach dieser Überarbeitung):
- F4/F7 (#1155) zur Laufzeit (Code-Lesen sagt: behoben; Task 5 Step 5).
- #1085a-Doku-Ort (Tool-Regeltext) nicht lokalisiert (Task 11 Step 1f).
- #1208: Context-Writer der `AGENTS.md` und Grund der `--check`-Blindstelle nicht lokalisiert (Task 10 Step 1).
- Teststände (Baseline grün/rot) gegen 9aa0e0c0 nicht ausgeführt; erwartete FAIL/PASS-Ergebnisse sind Plan-Werte.
- Ob der `--validate`-Pfad `SyncLog.write` erreicht (Task 1 Step 3).
- `admin-server.py`-/`config.py`-/`tmp_paths.py`-Anker des #1189-Plans (Task 14) gegen 9aa0e0c0.
- Default von `orchestrator.mode` (Task 7 Step 3).
- Schema für `role-defaults.yaml` (Task 12).
- Unbekannt: ob `jsonschema` in CI installiert ist (nur noch für Phase D/#1141 relevant).
- Aufwand: Referenz auf `effort-estimator` (Textverweis), keine eigene Schätzung.

## Neue Konflikte

- **K1 (#1189, PR-Angabe) — AUFGELÖST (Entscheidung 36 + 17):** Der APPROVED-Plan `docs/plans/2026-11-09-1189-tmp-sink-pin-plan.md` nennt einen eigenen PR. Hier ersetzt Entscheidung 17 (ein PR pro Phase) diese Angabe: #1189 läuft als Commits in der Phase-C-PR (Task 14). Der #1189-Plan bleibt unverändert (APPROVED, kein Eingriff in dieser Runde).
- **K2 (Task-Zählung Phase F/D):** durch Entscheidung 35 aufgelöst: #1141 liegt in Phase D nach #1181; Phase F = 6, Phase D = 8, Summe 89. Der Roadmap-Stand ist nicht Teil dieser Datei und muss separat angepasst werden.
- **K3 (#1086g) — AUFGELÖST (Entscheidung 24, bestätigt 38c):** Entscheidung 24 (Doku, kein Umbau) ersetzt die frühere Frage N1 und die Testplanung `test_tier_presets_max.py`; der Roadmap-Eintrag #1086g wird mit Entscheidungskommentar geschlossen.

## Frische-Check-Referenzen

- Issues: #1142, #1085, #1086, #1155, #1195, #1208, #1189, #1182, #1183, #1180, #1000, #1072, #1091, #1186, #739, #977, #1141 (nur Verweis, Phase D nach #1181, Entscheidung 35), #1188 (Verweis, Phase F), #1181 (Verweis, Phase D)
- docs/plans/2026-11-09-1189-tmp-sink-pin-plan.md
- docs/specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-spec.md
- docs/superpowers/plans/2026-11-11-phase-c-1086i-context-split.md
- docs/specs/2026-11-11-phase-c-sync-config-spec.md
- docs/specs/2026-11-11-1000-checkpoint-tracking-spec.md
- scripts/lib/sync_pipeline.py: _sync_stage_auto_commit_allowlist, _prune_managed_sync_backups, _managed_dirs_for_prune, SYNC_BACKUP_MAX_PER_SOURCE, SYNC_BACKUP_MAX_AGE_DAYS
- scripts/lib/cli_commands.py
- scripts/sync.py: _validate_doctor_flags, _build_arg_parser, --prune-backups, --check
- scripts/lib/log.py: SyncLog, warn, skip, write
- scripts/lib/gitignore.py: detect_shadowed_provider_roots
- scripts/lib/sync_pipeline.py: detect_shadowed_provider_roots-Aufruf :1893 (vorher :1811-1812, Re-Messung 9aa0e0c0), check_keyword_overlap-Registrierung :2080, auto_commit-Warnung :1995 (vorher :1912-1914), P0-Stellen :1897/:1899
- scripts/lib/delegation_table.py: get_routing_rules
- scripts/lib/variables.py: _orch_mode_flags
- scripts/lib/auto_commit.py: auto_commit_violations
- scripts/lib/io.py: run_git_check_ignore
- scripts/lib/consistency/report.py: print_report (Summary)
- scripts/lib/consistency/active_set_refs.py: check_keyword_overlap
- scripts/lib/context.py: init_claude_personal
- scripts/lib/hooks.py: _strict_enabled
- scripts/lib/mcp_provider_config.py: _config_rel_label
- .github/workflows/validate.yml
- scripts/lib/generated_file_drift.py: select_prunable_sync_backups, prune_sync_backups, backup_drifted_files, capture_generated_file_hashes, _iter_managed_files
- scripts/lib/config.py (nur Task 14)
- scripts/lib/context.py: build_gate_card, _extract_rule_section, compact_embedded_rule, sync_compact_reference_skills, _build_managed_block
- scripts/lib/context_profile.py: context_profile_log_lines
- scripts/lib/consistency/context_budget.py
- scripts/lib/consistency/active_set_refs.py: check_dangling_mention
- scripts/lib/progress_paths.py: resolve_progress_paths, ProgressPathFinding, DEFAULT_CHECKPOINT_DIR, DEFAULT_PROGRESS_DIR
- scripts/lib/checkpoint.py
- scripts/lib/deactivation.py
- scripts/lib/frontmatter.py
- scripts/lib/io.py: write_atomic
- scripts/lib/pipelines.py
- scripts/topology-probe.py: _run
- scripts/admin-server.py
- config/tier-presets.yaml (nur Lesen, Task 12 g = Doku)
- config/role-defaults.yaml
- config/context-anchors.yaml
- config/ai-providers.yaml
- rules/1-generic/use-orchestrator.md
- rules/1-generic/branch-guard.md
- rules/1-generic/repo-containment.md
- rules/1-generic/a2a-delegation-gates.md
- snippets/orchestrator/checkpointing.md
- templates/context/agents-managed.md
- AGENTS.md
- tests/test_sync_end_checks.py
- tests/test_context_compact_mode.py::test_committed_agents_md_equals_configured_mode_render
- tests/test_auto_commit_invalid_sync.py, tests/test_fail_on_p0.py, tests/test_sync_backup_retention.py, tests/test_sync_log_output.py, tests/test_gate_card_modes.py, tests/test_compact_rule_fallback.py, tests/test_rule_doc_pointers.py, tests/test_check_context_drift.py, tests/test_routing_priority.py, tests/test_checkpoint_tracking.py, tests/test_subprocess_encoding.py

## Self-Review

- Issues der Phase C je genau einmal abgedeckt (11 Issues): 1142 (T1), 1085 (T3, T4; a = T11 Step 1f, Doku), 1086 (T11 a-e, T12 h, g = Doku nach Entscheidung 24, i = T15/eigener PR, f zurückgestellt C-N4; Zuordnung nach 38c geprüft), 1155 (T4 F5-Flag, T5 F10/F4/F7), 1195 (T6), 1208 (T10), 1189 (T14 Referenz, Commits in Phase-C-PR nach 36), 1182 (T7), 1183 (T8), 1180 (T9), 1000 (T0b, T13). #1141 nicht mehr enthalten (T2 = Verweis, Entscheidung 35). Zählung: 11 Issues, 16 Tasks.
- Re-Messung 9aa0e0c0 durchgeführt (Abschnitt "Re-Messung"): 9 Anker-Zeilen verschoben, 11 Zeilen unverändert (Tabelle zählt 20 Zeilen); Task-Texte im Review 2026-11-11 nachgezogen.
- Keine TBD/TODO-Platzhalter; Unbekanntes ist als "nicht verifiziert" oder als U-Eintrag in "Offene Entscheidungen (neu, ungeklaert)" markiert.
- Signaturen mit Evidenz aus origin/main 9aa0e0c0: `build_gate_card` (context.py:2329), `_extract_rule_section` (:2300), `select_prunable_sync_backups` (generated_file_drift.py:147), `backup_drifted_files` (:462), `detect_shadowed_provider_roots` (gitignore.py:457, Aufrufer sync_pipeline.py:1893), `SyncLog.warn/warning/skip/error/write` (log.py:39/55/70/59/113), `resolve_progress_paths` (progress_paths.py:180), `_sync_stage_auto_commit_allowlist` (sync_pipeline.py:1974), `get_routing_rules` (delegation_table.py:289), `_orch_mode_flags` (variables.py:339), `_config_rel_label` (mcp_provider_config.py:330), `check_keyword_overlap` (active_set_refs.py:408), `run_git_check_ignore` (io.py:543), `auto_commit_violations` (auto_commit.py:167).
- Jeder Task mappt auf die Rolle `developer` (Specs: `senior-developer`/`requirements`); M-Tasks und Task 12 h haben Spec-Gate Task 0/0b; Ein Commit je Task (Entscheidung 17), Task 14 = 16 Commits (Entscheidung 36). Höchstens zwei PRs für die Phase (Entscheidung 52; plus #1086i nach 18), Konfliktstellen innerhalb der Phase sind Reihenfolge, kein Parallelbetrieb.
- Entscheidungen 17-38 sowie 40-46, 52, 55 und 56 (#1195 >30 Quellen, #1086i) sind eingearbeitet (Abschnitt "Entscheidungen (beantwortet)"; 35-38 für Phase C: 35, 36, 38b, 38c; 38a/d/e/f nicht Phase C; 39, 47-51, 53 nicht Phase C). U1-U5, U9, U11 beantwortet; die #1000-Teilfrage `progress.checkpoint-dir` ist durch 55 beantwortet (54, 57 nicht Phase C); U6-U8, U10 sind Tasks. Kein Schließ-Schritt für #1086 (Entscheidung 46). K1, K2, K3 sind aufgelöst.
- Frische-Check-Referenz-Änderung: #1141 als Verweis auf Phase D (Entscheidung 35), #1181 ergänzt; Dateien der Task 2 entfernt; `.github/workflows/validate.yml` ergänzt; Anker in sync_pipeline.py aktualisiert.
