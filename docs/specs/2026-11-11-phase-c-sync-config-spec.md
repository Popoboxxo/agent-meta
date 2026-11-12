# Phase C Sync/Config-Robustheit — Spec
> Status: DRAFT
> Datum: 2026-11-12 | Ist-Anker: `origin/main 53460042` (Worktree `fix/phase-c-sync-config`) | Plan: `docs/superpowers/plans/2026-11-11-phase-c-sync-config.md` (Task 0)
> Issues (M): #1085 b/c, #1155 (Rest: F5 + `--fail-on-p0`, F10), #1195, #1208, #1182, #1183, #1180, #1086 h (`priority`)

## Problem

**Problem.** Mehrere Sync/Config-Pfade enden still falsch oder mit Exit 0 (P0-Warnungen ohne Exit-Signal, unbegrenztes Backup-Wachstum, Compact-Profil verliert Regeln oder bricht ab, Regeln verweisen auf nicht ausgelieferte Docs, `AGENTS.md`-Drift).

## Ziel

**Ziel.** Pro M-Issue ein implementierbarer Vertrag mit testbaren Akzeptanzkriterien (AC). Plain-`sync.py` behält Exit 0 für `[ERROR]`/`[P0]`-Zeilen (Entscheidung 4).

**Scope.**
- Mit eigener Sektion: #1085c, #1085b/#1155-F5 (Flag), #1155-F10 (+F4/F7-Verifikation), #1195, #1208, #1182, #1183, #1180, #1086h.
- Ohne Sektion (S, Plan-Tasks genügen): #1142 (Task 1, Entscheidungen 3, 44), #1086 a-e (Task 11), #1189 (bestehender APPROVED-Plan, Entscheidung 36), #1086g (Entscheidung 24, nur Doku).
- #1000: eigene Mini-Spec `docs/specs/2026-11-11-1000-checkpoint-tracking-spec.md` (Task 0b; Entscheidungen 8, 43, 55).

## Nicht-Ziele

**Nicht-Ziele.**
- Kein neues Flag außer `--fail-on-p0`; `--strict` bleibt `--doctor`-exklusiv (`scripts/sync.py:122-131`, Entscheidungen 4, 38b).
- Kein Exit-Code-Wechsel im Plain-Sync ohne Flag.
- Kein Preset-Umbau (#1086g, Entscheidung 24); #1086f zurückgestellt (Entscheidung 34); #1086i eigener Plan/PR (Entscheidungen 18, 56); #1141 nicht in Phase C (Entscheidung 35).
- Keine Docs-URL-Variable, kein Absolutize/Deliver von `docs/` (Entscheidung 40).
- Kein Reject-Pfad in `build_gate_card` (Entscheidung 41).
- `priority` ändert kein Routing-Verhalten (Entscheidung 45).
- Keine Closing-Keywords in Commit/PR-Texten (Entscheidung 38e); `#1086` bleibt offen (Entscheidung 46).

## Interface Contracts (Datei:Symbol, Signatur, Fehlerpfade)

Zeilenanker gegen `origin/main 53460042` gelesen (Datei:Zeile). Python 3.9-kompatibel, provider-agnostisch (Unterschiede nur über Config-Keys/Capability-Flags).

### S1 — #1085c: Shadowing-Warnung nennt `ignore-provider-dirs`

- Ist: `scripts/lib/gitignore.py:457` `detect_shadowed_provider_roots(project_root: Path, providers: list[str], provider_config: dict, ignore_provider_dirs: bool) -> list[str]`; Text :507-514 endet mit `... gitignore.exceptions in .meta-config/project.yaml.`; Frühausstieg bei `ignore_provider_dirs` oder fehlendem `.git` (:478). Einziger Aufrufer in `scripts/`: `scripts/lib/sync_pipeline.py:1893` (Import :1892).
- Soll: Signatur unverändert. Der Warntext wird um genau diesen Satz ergänzt: `For self-hosting repos set gitignore: {ignore-provider-dirs: true} to silence this warning.`
- Fehlerpfade: keine neuen.

### S2 — #1085b / #1155-F5: opt-in `--fail-on-p0`

- Ist: `--strict` nur mit `--doctor` (`scripts/sync.py:122` `_validate_doctor_flags(parser, args) -> None`). Plain-Sync-Ende: `scripts/lib/cli_commands.py:1726-1727` `log.write(...)`, `--check`-Block :1731-1748 (Exit 1 bei `log.actions` oder `log.errors`, sonst `sys.exit(0)`), danach Admin-Start :1750. `--validate`-Exits :1532/:1534. P0-Stellen: `scripts/lib/sync_pipeline.py:1897` (`log.warning(f"[P0] {shadow_warning}")`) und :1899 (`... {keep_warning}`, aus `detect_invisible_keep_paths`, `gitignore.py:518`); weitere `[P0]`-Stellen in `scripts/` existieren nicht.
- Soll, `scripts/lib/log.py`:
  - `SyncLog.__init__`: neues Feld `self.p0: list[str] = []`.
  - `SyncLog.warn(self, message: str, p0: bool = False) -> None` (heute :39) und Alias `SyncLog.warning(self, message: str, p0: bool = False) -> None` (heute :55) reichen `p0` durch. Die Nachricht wird nur beim ersten Auftreten (nach `_seen_warnings`-Dedup, :49-51) zusätzlich in `self.p0` gespeichert. Der Text trägt weiter selbst das Präfix `[P0] ` (Aufrufer-Format unverändert).
- Soll, `scripts/lib/sync_pipeline.py`: beide Aufrufe :1897 und :1899 setzen `p0=True`.
- Soll, `scripts/sync.py`: neues Argument `--fail-on-p0` (`action="store_true"`, Default False) in `_build_arg_parser` (:217). Kein Eintrag in `_validate_doctor_flags`: das Flag wird in jedem Modus akzeptiert, wirkt aber nur im Plain-Sync-Pfad.
- Soll, `scripts/lib/cli_commands.py`: direkt nach dem `--check`-Block (:1731-1748, endet immer mit `sys.exit`) und vor dem Admin-Start (:1750):
  ```python
  if getattr(args, "fail_on_p0", False) and (log.p0 or log.errors):
      print(f"  X  {len(log.p0)} P0 finding(s), {len(log.errors)} error(s) — failing (--fail-on-p0).", file=sys.stderr)
      sys.exit(1)
  ```
  (Wortlaut der Meldung frei, solange er `--fail-on-p0` und beide Zähler nennt.)
- Soll, `.github/workflows/validate.yml:126`: `python scripts/sync.py` wird `python scripts/sync.py --fail-on-p0` (Schritt "Generate sync output", :125-126). Setzt das Flag in CI die Pipeline selbst (Entscheidung 4).
- Fehlerpfade: Plain-Sync ohne Flag: Exit 0 unabhängig von `log.p0`/`log.errors`. `--check` unverändert (Exit-Pfad liegt vor der neuen Prüfung).

### S3 — #1155-F10: Subprocess-Encoding (+ F4/F7 Verifikation)

- Ist: `scripts/topology-probe.py:229-236`: `runner(list(argv), capture_output=True, text=True, timeout=timeout, check=False, env=env)` ohne `encoding` (Aufruf in `_run(argv, *, timeout, runner, env)` :215). Der bestehende Guard `tests/test_subprocess_encoding_guard.py` (`_offenders()` :16, Test :32) prüft nur Calls mit Receiver `subprocess` (:21-24) und übersieht deshalb den injizierten `runner(...)`.
- Soll: In `scripts/topology-probe.py:229` ergänzt `encoding="utf-8", errors="replace"`.
- Soll, Test (Entscheidung dieser Spec, siehe ADR-S1): **kein** neues `tests/test_subprocess_encoding.py`. Der Guard-Test wird erweitert: die Receiver-Bedingung (:21-24) entfällt, jeder `ast.Call` mit Keyword `text=True` oder `universal_newlines=True` ohne Keyword `encoding` zählt als Verstoß (`ast.Call` mit `**kwargs` bleibt unbeanstandet, nicht prüfbar). Zusätzlich in derselben Datei ein Laufzeit-Test, der `topology-probe._run` mit Fake-`runner` aufruft und `kwargs["encoding"] == "utf-8"` und `kwargs["errors"] == "replace"` prüft. `topology-probe.py` hat einen Bindestrich im Namen, Import per `importlib.util.spec_from_file_location`.
- F4/F7: reine Verifikation (kein Code, falls Laufzeit-Nachweis grün): `sync.py --validate` mit `hooks: {x: true}` und `viz: true` in tmp-Config ohne `AttributeError`; Code-Lesen sagt behoben (`config.py:311`, `hooks.py:447`, `write_atomic` `config.py:1420/1486/1507`, `skill_admin.py:99`, `sync_pipeline.py:883`). Nur bei Fehlschlag neuer Test + Fix.

### S4 — #1195: globale Backup-Retention, Dedup, CLI-Cleanup

- Ist, `scripts/lib/sync_pipeline.py`: `SYNC_BACKUP_MAX_AGE_DAYS = 30` :969, `SYNC_BACKUP_MAX_PER_SOURCE = 3` :970, `_managed_dirs_for_prune(project_root, config, provider_config) -> list[Path]` :981, `_prune_managed_sync_backups(project_root, config, provider_config, args, log) -> None` :1029 (Aufruf :1128, ruft pro Dir `prune_sync_backups(..., max_age_days=..., max_per_source=...)` :1035-1039). `scripts/sync.py:97-98` importiert die beiden Konstanten für die Preview-Parität.
- Ist, `scripts/lib/generated_file_drift.py`: `select_prunable_sync_backups(target_dir: Path, max_per_source: int, log: Optional[SyncLog] = None) -> list[Path]` :147-196 (count-only; neuestes Backup je Quelle überlebt); `prune_sync_backups(target_dir, project_root, log, dry_run, max_age_days, max_per_source) -> list[str]` :199 (`max_age_days` ignoriert, keine gitignore-Prüfung); `backup_drifted_files(findings: list[dict], project_root: Path, log: SyncLog, dry_run: bool = False) -> list[str]` :462 (Schreiben :501-504, ein Zeitstempel je Aufruf :484).
- Soll:
  - `sync_pipeline.py`: neue Konstante `SYNC_BACKUP_MAX_TOTAL_PER_DIR = 30` (Entscheidung 42), neben :970; `_prune_managed_sync_backups` reicht sie durch. `sync.py:97-98`-Import erhält sie ebenfalls (Preview).
  - `select_prunable_sync_backups(target_dir: Path, max_per_source: int, log: Optional[SyncLog] = None, max_total: Optional[int] = None, project_root: Optional[Path] = None) -> list[Path]`. Algorithmus: (1) bisherige Per-Source-Selektion `P1`. (2) Ist `max_total` gesetzt und `len(alle Backups) - len(P1) > max_total`: aus den verbleibenden Backups wird in aufsteigender Reihenfolge `(Zeitstempel, Name)` zusätzlich selektiert, bis die Restzahl `<= max_total` ist oder keine **nicht geschützten** Kandidaten mehr bleiben. Geschützt ist das jeweils neueste Backup jeder Quelle (Entscheidung 56; die Restzahl darf dann `> max_total` bleiben). (3) Jeder in Schritt 2 zusätzlich selektierte Kandidat wird nur übernommen, wenn `run_git_check_ignore(<rel>, str(project_root))` (`scripts/lib/io.py:543`) ihn als ignoriert bestätigt (`returncode == 0`); `None` (kein Git/Fehler), `project_root is None` oder nicht ignoriert: Kandidat bleibt liegen (fail-soft, Entscheidung 42 "nur gitignorierte"). Schritt 1 behält das heutige Verhalten (keine gitignore-Prüfung). `max_total=None` ist exakt das heutige Verhalten.
  - `prune_sync_backups(..., max_total: Optional[int] = None)` reicht `max_total` und `project_root` an `select_prunable_sync_backups` durch.
  - `backup_drifted_files`: vor dem Schreiben wird `existing_content` mit dem Inhalt des neuesten vorhandenen `<target.name>.sync-backup-*`-Geschwisters (gleiche Quelle, über `_sync_backup_source`/`_sync_backup_timestamp` :130-144) verglichen. Bei Gleichheit wird nicht geschrieben und der Pfad des **vorhandenen** Backups in die Rückgabeliste aufgenommen (Warnungen des Aufrufers verweisen weiter auf eine Datei mit dem Nutzerinhalt; ADR-S3). Fehler beim Lesen des Vergleichs-Backups: schreiben wie bisher (fail-safe).
  - `scripts/sync.py`: neues Argument `--prune-sync-backups` (`store_true`, neben `--prune-backups` :472). Handler: ruft `_managed_dirs_for_prune(...)` und `prune_sync_backups(..., max_per_source=SYNC_BACKUP_MAX_PER_SOURCE, max_total=SYNC_BACKUP_MAX_TOTAL_PER_DIR)` je Dir; mit `--dry-run` listet er die Kandidaten über `select_prunable_sync_backups` (dieselbe Funktion, Parität zu `--cleanup-preview`) und löscht nichts; Exit 0. Plain-Sync-Lauf (`_prune_managed_sync_backups`) wendet `max_total` ebenfalls an.
- Fehlerpfade: `OSError` beim Löschen wird weiter debug-geloggt (:233-238); fehlendes Dir liefert `[]`.

### S5 — #1208: `--check`-Blindstelle für `AGENTS.md`

- Ist: `AGENTS.md:140` = `# CRITICAL GATE` liegt im Managed-Block (`AGENTS.md:44` begin, :232 end). Der Managed-Block-Writer (`scripts/lib/context.py:1068-1103`) loggt bei `new_content != existing` `log.action("UPDATE", ...)` (:1099) **auch im Dry-Run**; `--check` zählt `len(log.actions)` (`cli_commands.py:1732`). Die vom Plan (Task 10 Step 3) vermutete Lücke "Writer loggt im Dry-Run keine Action" besteht für den Managed-Block-Pfad damit **nicht**. Die Gate-Überschrift ist variantenabhängig (`rules/1-generic/use-orchestrator.md`: `# CRITICAL GATE` :3 ENFORCED, `(runtime-partially enforced)` :15, `(advisory)` :29, `(neutral)` :42). Der Test `tests/test_context_compact_mode.py::test_committed_agents_md_equals_configured_mode_render` (:505) rendert über Test-Helfer `_render_context` (Gemini-Variablen, :475-481), der echte Sync dagegen je Provider mit geteilter Datei.
- Ursache **nicht verifiziert** (keine Ausführung möglich, siehe Offene Fragen Q1). Verbindlich festgelegt ist nur die Invariante und die Entscheidungsregel:
  - Invariante I-1208: Für `AGENTS.md` widersprechen sich `--check` (Exit 1 bei Abweichung) und der Test `test_committed_agents_md_equals_configured_mode_render` nie.
  - Vertrag: Neuer Test `tests/test_check_context_drift.py` (tmp-Projekt, einmal `sync.py`, dann `AGENTS.md` verfälschen, `sync.py --check` -> Exit 1 und stderr enthält `out of sync`) wird **zuerst** geschrieben. Ist er grün (keine Blindstelle), liegt die Ursache in der Render-Abweichung Test-Helfer vs. echter Sync: Fix dort (Test-Helfer an die Variablen des echten Syncs angleichen **oder** Sync-Render deterministisch machen), nicht im Writer. Ist er rot, wird der Writer-Pfad gefixt, der die Aktion unterschlägt.
  - `AGENTS.md` wird im selben Commit regeneriert (`python3 scripts/sync.py`), danach `python3 scripts/sync.py --check` -> Exit 0.
- Reihenfolge: nach #1182/#1183/#1180 (Render ändert sich, Plan Task 10).

### S6 — #1182: Compact-Profil bricht bei `orchestrator.mode != strict` nicht ab

- Ist: `scripts/lib/context.py:2329` `build_gate_card(agent_meta_root: Path, config: dict, variables: dict, log: SyncLog) -> str`, Aufruf :3077-3079. Fehlende **Regel** wirft `SyncError` (:2355-2359), fehlende **Überschrift** ebenfalls (:2367-2371). `_extract_rule_section(rule_text: str, heading: str) -> str | None` :2300. `use-orchestrator.md`: alle `# CRITICAL GATE`-Varianten stehen in `{{#if ORCH_MODE_STRICT}}` (:1-56); advisory hat `# Orchestrator` (:58), main-chat `# Main-Chat Mode` (:65) -> `None` -> Abbruch. Gate-Sektionsliste: `config/context-anchors.yaml:89-96`.
- Soll (Entscheidung 41): Bei `section is None` und vorhandener Regel: kein `SyncError`, Sektion auslassen, genau eine Warnung über `log.warn(f"context.gate-card: section '{heading}' not rendered for orchestrator.mode={mode} ({rel_source})")`. Fehlende **Regel** (:2355-2359) wirft unverändert. Signatur unverändert.
- Moduswert (ADR-S2): `mode` wird aus den bereits übergebenen `variables` abgeleitet (`ORCH_MODE_STRICT`/`ORCH_MODE_ADVISORY`/`ORCH_MODE_MAIN_CHAT`, Strings `"true"`/`"false"`, `scripts/lib/variables.py:339-355`; Ergebnis `"strict"`, `"advisory"`, `"main-chat"`, sonst `"unknown"`). Das vermeidet einen zweiten Resolver neben `_resolve_orch_mode` (`variables.py:289`) und berücksichtigt Provider-Overrides. Der Default von `orchestrator.mode` ist damit nicht nötig.
- Soll, `scripts/lib/context_profile.py`: neue Funktion `context_profile_override_warnings(config: dict, providers: Iterable[str]) -> List[str]`, die für jeden Provider mit `context-profile: compact` und explizitem `context_file.mode: full` genau eine Zeile `context-profile.mode-override: '<file>' renders context_file.mode=full while context-profile=compact is active; the compact render (gate card, roster, reference skills) still applies` (`<file>` = Kontextdatei des Providers) liefert; der Aufrufer von `context_profile_log_lines` (:184) loggt sie per `log.warn`. Aufrufstelle ist bei der Implementierung zu lokalisieren (nicht verifiziert).

### S7 — #1183: Compact-Profil ohne still verlorene Regeln

- Ist: `templates/context/agents-managed.md:8` ersetzt im Compact-Profil `rules-pointer`/`rules-embedded`/`rules-lazy` (:9-17) vollständig durch `{{> gate-card }}` (Partial `templates/context/partials/gate-card.md` = `{{GATE_CARD}}`). Eingebettete Regeln, die nicht in `gate_card_sections` stehen, fallen damit aus `AGENTS.md`, ohne Skill/Pointer. In `scripts/lib/context.py` existiert schon `context.rule-reference-fallback` (:2958-2962, nur für REFERENCE-Anteile bei fehlendem Skill-Kanal) und `compact_embedded_rule(output_stem: str, content: str, *, profile_compact: bool = False, skills_channel: bool = True) -> str` (:2241, Aufruf :2963). Embed-Schleife in `_build_managed_block` :2911ff (Kanal `rules_file_channel` :2908, lazy `rule_opts_lazy_channel` :2927), `sync_compact_reference_skills(agent_meta_root, project_root, config, variables, log, dry_run, provider, provider_config=None) -> None` :2440.
- Soll: neue Funktion in `scripts/lib/context.py`:
  `rule_reachable_in_compact(rule_stem: str, *, gate_stems: frozenset[str], native_rules: bool, skill_stems: frozenset[str]) -> bool` mit Rückgabe `rule_stem in gate_stems or native_rules or rule_stem in skill_stems`. `gate_stems` = Stems aus `gate_card_sections` (`stem#heading` -> `stem`); `native_rules` = Provider liefert Regeln über den nativen Kanal (`HAS_NATIVE_RULES`); `skill_stems` = Schnitt über alle Sharer aus `lazy_skill_stems(...)` (:2973) plus Reference-Skill-Stems aus `sync_compact_reference_skills`, nur wenn alle Sharer `lazy_skill_channel` haben (:2492).
- Soll, Block-Render (Compact-Profil): Für jede nicht per `all(_opts_skip(...))` (:2925) verworfene Regel `R`:
  - `rule_reachable_in_compact(...) == False` -> `log.warn(f"context.rule-compacted-away: rule '{R}' removed for provider '{provider}' without a skills channel")`, genau einmal je Regel (Dedup über `SyncLog.warn`).
  - Hat `R` einen Skill (`R in skill_stems`), wird `R` in **eine** zusätzliche Pointer-Zeile aufgenommen (Format: `Weitere Regeln als Skills: <stem>, <stem>, ...`, sortiert), die an den `GATE_CARD`-Wert angehängt wird (`local_vars["GATE_CARD"]` :3077); keine Template-Änderung (ADR-S4).
  - `sync_compact_reference_skills` und der Block-Render benutzen dieselbe Menge `skill_stems`, damit jeder geschriebene Reference-Skill im Block genannt wird und kein genannter Skill fehlt.
- Fehlerpfade: Soft-Cap (`context_soft_cap_chars`, 12000) wird nicht erzwungen; überschreitet der Compact-Render ihn, bleibt die bestehende Warnung (Issue-Kriterium 4).

### S8 — #1180: Regeln verweisen auf nicht gelieferte `docs/concepts/*.md`

- Ist (gelesen): `rules/1-generic/branch-guard.md:21` (`docs/concepts/branch-guard-known-limits.md`), `rules/1-generic/repo-containment.md:5` (`docs/concepts/repo-containment-prison-mode.md`), `rules/1-generic/a2a-delegation-gates.md:17` und :29 (`docs/concepts/active/orchestrator-topology.md`), :44 (`docs/concepts/a2a-handoff-protocol.md`). `a2a-delegation-gates.md:31` verweist zusätzlich auf `singleton-orchestrator-architecture.md` (kein `docs/`-Pfad; nicht Teil dieser Spec). `dod-criteria.md:4` nennt `docs/REQUIREMENTS.md` (Projektdatei des Konsumenten, Ausnahme).
- Soll (Entscheidung 40, Self-contain): In den drei Regeldateien entfallen die fünf `docs/concepts/`-Verweise; die Kernaussage steht inline.
  - `branch-guard.md` (Abschnitt `## Bekannte Grenzen`, :18-21): bleibt, die Zeile :21 nennt die bekannten Lücken inline (Tokenizer-Indirektion `eval`/`$(...)`/`xargs` steht bereits :20; ergänzt um die Lücken aus #551/#592/#809 in je einem Halbsatz) und behält `#809`. Quelle des Inhalts: `docs/concepts/branch-guard-known-limits.md`.
  - `repo-containment.md:5`: "Grenzen/Details: `docs/...`" wird durch einen Satz mit den Kerngrenzen ersetzt (Quelle: `docs/concepts/repo-containment-prison-mode.md`); gilt nur im `REPO_CONTAINMENT_ENABLED`-Zweig.
  - `a2a-delegation-gates.md`: :17, :29, :44 verlieren die Verweise; die Aussage "fehlende Provider-Unterstützung degradiert laut auf `subagent`" und die Referenz "Plattform erzwingt Tiefenlimits" stehen schon im Satz davor, es wird nichts Neues inline ergänzt.
  - Je Regeldatei maximal 6 neu hinzugefügte Zeilen (Soft-Cap-Schutz).
- Soll, neuer Check in `scripts/lib/consistency/context_budget.py`: `check_dangling_doc_pointer(project_root: Path, active_providers: Sequence[str], capabilities: Mapping[str, Mapping], active_set) -> list` (Signatur wie `check_dangling_pointer` :293). Findet in den generierten Artefakten (`_pointer_artifacts(root, caps)`, wie :317) Backtick-Pfade `docs/<...>.md`; existiert der Pfad relativ zu `project_root` nicht, ein `Finding(Severity.WARNING, "context.dangling-doc-pointer", rel, ...)`. Eintrag `"context.dangling-doc-pointer": Severity.WARNING` in `SPEC_SEVERITY` (:53-61). Registrierung analog zu den übrigen `context_budget`-Checks (Ort bei Implementierung neben dem Eintrag für `check_dangling_pointer` zu finden; `check_keyword_overlap` ist bei `sync_pipeline.py:2080` registriert).
- Fehlerpfade: unlesbare Artefakte werden übersprungen (wie `_read_text` :318).

### S9 — #1086h: `priority` nur emittieren

- Ist: `scripts/lib/delegation_table.py:289` `get_routing_rules(...)`, Rule-Dict :374-386 (`agent`, `tier`, `parallel`, `orchestrator_only`, `keywords`, `examples`, `output_contract`, `input_contracts`); `routing` je Rolle gelesen :363-364 (`routing.parallel`, `routing.orchestrator_only`). `scripts/lib/consistency/active_set_refs.py:408` `check_keyword_overlap(project_root: Path, active_providers: Sequence[str], capabilities: Mapping[str, Mapping], active_set) -> list` (INFO, :419-423). Es gibt keinen Code-Resolver; das LLM löst Überlappungen auf.
- Soll (Entscheidung 45): optionales `routing.priority: <int>` je Rolle.
  - `get_routing_rules`: das Rule-Dict erhält den Key `"priority": int` **nur**, wenn `routing.priority` ein `int` (kein `bool`) ist; sonst bleibt das Dict byte-identisch zu heute (Rückwärtskompatibilität, Golden-Fixtures).
  - `check_keyword_overlap`: bei Überlappung, an der mindestens eine Rolle mit `priority` beteiligt ist, wird der Message-Text um `; priority: <role>=<n>, ...` (nur Rollen mit gesetzter `priority`, absteigend nach Wert, dann Name) ergänzt. Anzahl und Severity (INFO) der Findings bleiben gleich. Kein Wortlaut "resolved by" (es wird nichts aufgelöst).
  - `config/role-defaults.yaml` erhält **keine** `priority`-Werte (nur der Mechanismus; generierte Ausgaben bleiben unverändert).
- Fehlerpfade: nicht-ganzzahliger Wert -> ignoriert (kein Key, keine Exception).

## Datenfluss

- **Flag `--fail-on-p0`:** `detect_shadowed_provider_roots`/`detect_invisible_keep_paths` (`gitignore.py`) -> `log.warning("[P0] ...", p0=True)` (`sync_pipeline.py:1897/:1899`) -> `SyncLog.p0` -> `log.write` (:1726) -> `--check`-Block -> neue Prüfung -> `sys.exit(1)` nur mit Flag.
- **Backups:** `backup_drifted_files` (Dedup-Vergleich gegen neuestes Backup) -> `*.sync-backup-<ts>` neben der Datei -> nach Drift-Stage `_prune_managed_sync_backups` (:1128) -> `_managed_dirs_for_prune` -> `prune_sync_backups` -> `select_prunable_sync_backups` (Per-Source, dann Total-Cap + gitignore-Filter) -> `unlink`. CLI `--prune-sync-backups` und `--cleanup-preview` benutzen dieselbe Selektion.
- **Compact-Render:** `variables` (`ORCH_MODE_*`, `CONTEXT_PROFILE_COMPACT`) + `config/context-anchors.yaml::gate_card_sections` -> `build_gate_card` -> `GATE_CARD` (+ Pointer-Zeile aus `skill_stems`) -> `agents-managed.md:8` -> `AGENTS.md`-Managed-Block; Warnungen `context.gate-card`/`context.rule-compacted-away` über `SyncLog.warn` -> `sync.log`.
- **#1180-Check:** generierte Artefakte -> Regex `docs/...md` -> Existenzprüfung gegen `project_root` -> `Finding` -> `--validate`-Report.
- **#1208:** `AGENTS.md` (Managed-Block) -> Dry-Run-Render -> `log.actions` -> `--check` Exit 1.

## Acceptance Criteria (nummeriert, testbar)

Test-Orte siehe Plan (Dateinamen im Plan-File-Structure). Given/When/Then verkürzt.

**#1085c** (Vertrag S1)
- AC-1085c-1: Given tmp-Git-Repo mit `.gitignore`-Regel `.claude/agents/` außerhalb des Managed-Blocks, When `detect_shadowed_provider_roots(root, ["Claude"], {"Claude": {"agents_dir": ".claude/agents"}}, False)`, Then genau 1 Warnung, die `ignore-provider-dirs` enthält.
- AC-1085c-2: Given `ignore_provider_dirs=True`, When derselbe Aufruf, Then `[]` (unverändert).

**#1085b / #1155-F5** (Vertrag S2)
- AC-FOP-1: `SyncLog().warn("x", p0=True)` -> `log.p0 == ["x"]`; ein zweiter identischer Aufruf ergänzt weder `warnings` noch `p0` (Dedup).
- AC-FOP-2: `SyncLog().warning("y", p0=True)` verhält sich wie `warn`.
- AC-FOP-3: Given tmp-Projekt mit Shadowing-Regel, When `sync.py --config <cfg>`, Then Exit 0; When zusätzlich `--fail-on-p0`, Then Exit 1 und stderr enthält `[P0]` und `--fail-on-p0`.
- AC-FOP-4: Given tmp-Projekt ohne P0 und ohne `log.errors`, When `--fail-on-p0`, Then Exit 0.
- AC-FOP-5: `sync.py --check --fail-on-p0` wird akzeptiert (kein argparse-Fehler); Exit-Code folgt allein dem `--check`-Pfad (Exit 0 bei sauberem Projekt, auch wenn `log.p0` gesetzt ist).
- AC-FOP-6: `sync.py --fail-on-p0 --strict` (ohne `--doctor`) wird weiter von `_validate_doctor_flags` abgelehnt; `--strict` ist nicht auf Plain-Sync erweitert.
- AC-FOP-7: `.github/workflows/validate.yml` Schritt "Generate sync output" enthält `python scripts/sync.py --fail-on-p0`; Datei parst mit `yaml.safe_load`; `python3 scripts/sync.py --fail-on-p0` auf diesem Repo endet mit Exit 0.
- AC-FOP-8: `python3 -m pytest tests/test_sync_end_checks.py -q` bleibt grün (Plain-Exit-0 gepinnt).

**#1155-F10 / F4 / F7** (Vertrag S3)
- AC-F10-1: Der erweiterte Guard-Test meldet vor dem Fix genau einen Verstoß `scripts/topology-probe.py:229` und danach keinen.
- AC-F10-2: Laufzeit-Test: `_run(["x"], timeout=1, runner=fake, env={})` übergibt `encoding="utf-8"` und `errors="replace"` an `fake`.
- AC-F10-3: `tests/test_subprocess_encoding.py` existiert nicht (aufgegangen im Guard-Test).
- AC-F4F7-1: `sync.py --validate` mit `hooks: {x: true}` und `viz: true` -> kein `AttributeError`; Evidenz im Issue-Kommentar.

**#1195** (Vertrag S4)
- AC-1195-1: 10 Quellen x 3 Backups, `max_per_source=3`, `max_total=12`, alle gitignoriert -> `len(select_prunable_sync_backups(...)) == 18`; das neueste Backup jeder Quelle ist nicht darunter.
- AC-1195-2: 12 Quellen x 3 Backups (36), Default `max_total=30` -> 6 Kandidaten, alle mit den ältesten Zeitstempeln.
- AC-1195-3: 35 Quellen x 2 Backups (70), Default -> genau 35 Kandidaten (alle älteren); die 35 neuesten bleiben (Restzahl 35 > 30 ist erwartet, Entscheidung 56).
- AC-1195-4: Eine nicht gitignorierte Datei `*.sync-backup-*` wird bei der Total-Cap-Selektion nie selektiert; ohne Git-Repo (`run_git_check_ignore` -> `None`) wird durch den Total-Cap nichts selektiert.
- AC-1195-5: `backup_drifted_files` zweimal mit identischem `pre_text` und verschiedenen Zeitstempeln -> eine Datei auf der Platte; der zweite Rückgabewert enthält den Pfad des vorhandenen Backups.
- AC-1195-6: `sync.py --prune-sync-backups --dry-run` listet Kandidaten und löscht nichts (Exit 0); ohne `--dry-run` löscht es bis `<= 30` je Dir (bzw. bis nur geschützte übrig sind).
- AC-1195-7: Parität: Die Kandidatenliste von `--prune-sync-backups --dry-run` ist gleich `select_prunable_sync_backups(...)` mit denselben Argumenten, und `--cleanup-preview` zeigt dieselbe Menge.
- AC-1195-8: Steady-State: 5 Syncs hintereinander mit Drift in derselben Datei -> je Dir `<= 30` Backups.
- AC-1195-9: Bestehende Backup-Tests (`-k "sync_backup or cleanup_preview"`) bleiben grün (`max_total=None` = altes Verhalten).

**#1208** (Vertrag S5)
- AC-1208-1: Given einmal synchronisiertes tmp-Projekt, When `AGENTS.md` verfälscht (`# CRITICAL GATE (runtime-partially enforced)` -> `# CRITICAL GATE`), Then `sync.py --check` Exit 1 und stderr enthält `out of sync`.
- AC-1208-2: `python3 scripts/sync.py` auf dem Repo-Root regeneriert `AGENTS.md`; danach `python3 scripts/sync.py --check` Exit 0.
- AC-1208-3: `test_committed_agents_md_equals_configured_mode_render` ist grün (nach AC-1208-2).
- AC-1208-4: Befund (Blindstelle ja/nein, Ursache) ist im Commit-Body und im Issue-Kommentar dokumentiert; Fix liegt an der belegten Stelle (Entscheidungsregel in S5).

**#1182** (Vertrag S6)
- AC-1182-1: Given `orchestrator.mode: advisory`, When `build_gate_card(...)` mit den Variablen `ORCH_MODE_ADVISORY="true"`, `ORCH_MODE_STRICT="false"`, `ORCH_MODE_MAIN_CHAT="false"`, Then kein `SyncError`; genau 1 Warnung mit `CRITICAL GATE` und `advisory`; Rückgabe enthält `Git Delegation`.
- AC-1182-2: Dasselbe für `main-chat`.
- AC-1182-3: Given fehlende Regel (`gate_card_sections` nennt unbekannten Stem), Then weiter `SyncError` (`context.gate-card: rule '...'`).
- AC-1182-4: End-to-End: tmp-Projekt mit `context-profile: compact` und `orchestrator.mode: advisory` -> `sync.py` Exit 0, `AGENTS.md` vorhanden.
- AC-1182-5: Given `context-profile: compact` und `context_file.mode: full`, Then genau eine Warnung `context-profile.mode-override: ...` je betroffenem Provider.
- AC-1182-6: `python3 -m pytest tests/test_context_compact_mode.py -q` und `python3 scripts/sync.py --validate` bleiben grün.

**#1183** (Vertrag S7)
- AC-1183-1: Given `ai-providers: [Claude, Opencode, Gemini]`, `context-profile: compact`, `orchestrator.mode: strict`: für jede Überschrift in `AGENTS.md` (full), die in `AGENTS.md` (compact) fehlt, gilt: eingebettet, oder Skill existiert und Pointer-Zeile nennt den Stem, oder genau eine `context.rule-compacted-away`-Warnung.
- AC-1183-2: Für jede geschriebene `.opencode/skills/<rule>/SKILL.md` aus dem Compact-Pfad steht `<rule>` in der Pointer-Zeile im Block.
- AC-1183-3: Dasselbe mit `orchestrator.mode: advisory` (setzt #1182 voraus).
- AC-1183-4: `rule_reachable_in_compact("x", gate_stems=frozenset(), native_rules=False, skill_stems=frozenset())` ist `False`; mit `skill_stems={"x"}` ist es `True`.
- AC-1183-5: Überschreitet der Compact-Render `context_soft_cap_chars`, erscheint die bestehende Soft-Cap-Warnung mit Begründung; es wird keine Regel zusätzlich entfernt, um den Cap zu erreichen.
- AC-1183-6: `python3 -m pytest tests -q -k "context or compact"` und `--validate` bleiben grün.

**#1180** (Vertrag S8)
- AC-1180-1: `test_no_unresolvable_relative_doc_pointers` scannt `rules/**/*.md` (Backtick-Pfade `docs/...md`, Ausnahme `docs/REQUIREMENTS.md` in `dod-criteria.md`) und findet 0 Treffer (vorher 5 in 3 Dateien).
- AC-1180-2: `branch-guard.md` enthält weiter `## Bekannte Grenzen` und `#809`.
- AC-1180-3: Check `context.dangling-doc-pointer`: Given generiertes Artefakt mit `` `docs/nicht-vorhanden.md` `` in tmp-Projekt, Then genau 1 `Finding` mit Severity WARNING; mit vorhandener Datei 0 Findings.
- AC-1180-4: `SPEC_SEVERITY` enthält `context.dangling-doc-pointer` -> WARNING.
- AC-1180-5: Keine Docs-URL-Variable wird eingeführt (kein neuer Variablenname mit `DOCS_URL` in `scripts/lib/variables.py`).
- AC-1180-6: `python3 scripts/sync.py --validate` Exit 0 auf diesem Repo.

**#1086h** (Vertrag S9)
- AC-1086h-1: Zwei Fake-Rollen mit Keyword `refactoring`, `routing.priority` 10 bzw. 0 -> `get_routing_rules(...)` liefert Rule-Dicts mit `"priority": 10` bzw. `0`.
- AC-1086h-2: Ohne `priority` enthält das Rule-Dict keinen `priority`-Key; die generierten Ausgaben dieses Repos sind unverändert (Golden-Fixtures grün).
- AC-1086h-3: `check_keyword_overlap` nennt bei gesetzter `priority` `priority: <role>=10, <role>=0` in der Message; Anzahl und Severity der Findings sind gleich wie ohne `priority`.
- AC-1086h-4: `routing.priority: "x"` (Nicht-int) und `true` erzeugen weder Key noch Exception.

Anzahl AC: #1085c 2, #1085b/F5 8, #1155 F10/F4/F7 4, #1195 9, #1208 4, #1182 6, #1183 6, #1180 6, #1086h 4 (gesamt 49).

## Offene Fragen + Risiken

**Offene Fragen** (Optionen, Empfehlung zuerst):

- **Q1 (#1208, Ursache):** Die Blindstelle ist weder im Code belegt (Managed-Block-Writer loggt im Dry-Run, S5) noch reproduziert. Optionen: (A, empfohlen) Repro-Test zuerst; Fix an der Stelle, die der Test belegt (Entscheidungsregel S5). (B) Writer pauschal ändern ohne Repro: nicht empfohlen (würde eine wirkungslose Änderung committen). Keine User-Rückfrage nötig, wenn A gilt; die Spec-Freigabe bestätigt A.
- **Q2 (#1183, Reichweite):** Regel, die weder im Gate noch nativ noch als Skill erreichbar ist. Optionen: (A, empfohlen, Plan-Linie) nur WARN `context.rule-compacted-away`; (B) zusätzlich einen Voll-Regel-Skill schreiben (größerer Eingriff in `sync_compact_reference_skills`, neue Skill-Artefakte). Empfehlung A; B wäre ein eigenes Issue.
- **Q3 (#1182, Warn-Wortlaut): GESCHLOSSEN.** Wortlaut aus Issue #1182 übernommen, siehe S6.

**Risiken.**
- R1: `--fail-on-p0` bricht auch bei `log.errors` (Plan-Semantik "P0 oder Errors"). Das Flag in `validate.yml:126` kann CI rot färben, falls der Plain-Sync heute stille `[ERROR]`-Zeilen produziert. Mitigation: AC-FOP-7 (lokaler Lauf vor dem CI-Commit).
- R2: Dedup in `backup_drifted_files` ändert die Rückgabe (vorhandener statt neuer Pfad). Aufrufer wurden nicht gelesen; vor Implementierung per `Grep` auf `backup_drifted_files(` prüfen, ob sie die Anzahl der Rückgabe zählen.
- R3: Stale `auto-commit-allowlist.json` (#1142, Entscheidung 44) kann veraltete Commit-Rechte behalten; Gegenmaßnahme ist die Warnung, die die Datei nennt. Hingenommen.
- R4: `get_routing_rules` -> `build_routing_tool_definition` kann neue Dict-Keys in generierte Tool-JSON durchreichen; Folge wäre ein Golden-Drift. Mitigation: Key nur bei gesetzter `priority`, keine Werte in `role-defaults.yaml` (AC-1086h-2).
- R5: #1180 entfernt Verweise: der Zusatz-Check `context.dangling-doc-pointer` kann in Konsumentenprojekten Warnungen auf eigene Docs auslösen (nur wenn der Pfad dort fehlt); Severity WARNING begrenzt das.
- R6: #1000-Warnung `progress.checkpoint-dir-ignored` erscheint auf agent-meta selbst (Entscheidungen 8, 43, 55; Mini-Spec), kein Exit-Wechsel.
- R7: Windows-Verhalten der Backup-Löschung nicht geprüft.

**Abweichungen zum Plan / Anker-Drift** (Spec gewinnt für Phase C, Plan nachziehen):
- D1: Plan Task 5 legt `tests/test_subprocess_encoding.py` an; `tests/test_subprocess_encoding_guard.py` existiert bereits -> Test dort erweitert (ADR-S1).
- D2: Plan Task 10 Step 3 unterstellt fehlende Dry-Run-Action im Writer; `context.py:1094-1099` loggt sie bereits (S5).
- D3: Plan Task 8: Pointer "im Gate-Card-Partial"; Spec hängt sie an `GATE_CARD` (gleiche Wirkung, keine Template-Änderung, ADR-S4).
- D4: Plan Task 12 Overlap-Text "resolved by priority"; Spec: "priority: <role>=<n>" (Entscheidung 45: nichts wird aufgelöst).
- D5: Plan Task 6 setzt gitignore-Prüfung "vor dem Löschen" allgemein; Spec beschränkt sie auf den neuen Total-Cap-Pfad (bestehendes Per-Source-Verhalten unverändert, ADR-S3).
- D6: Plan Task 7 "Default von `orchestrator.mode` nicht verifiziert": entfällt, Moduswert kommt aus `variables` (ADR-S2).
- D7: Plan nennt Basis `9aa0e0c0`; gelesene Anker gelten gegen `53460042`. Geprüfte Anker waren unverändert; nicht jeder Plan-Anker wurde neu geprüft (siehe unten).
- D8: Plan-Anker `topology-probe.py:229-236`: der Aufruf `runner(` beginnt :229, `text=True` steht :232 (Roadmap sagt :232); beides konsistent.

**Nicht verifiziert (ehrlich).**
- Keine Tests, kein `sync.py`-Lauf, kein `git`-Befehl ausgeführt (Spec-Worker ohne Shell). Alle FAIL/PASS-Erwartungen sind Planwerte.
- Issue-Texte (`gh issue view`) nicht gelesen; Issue-ACs nur über den Plan referenziert (#1195 "AC 1-4", #1182 Wortlaut).
- Stand von #1213/#1214 (laut Auftrag offen, Code ggf. geliefert) nicht geprüft; #1224/#1205 (Auto-Commit-Allowlist-Schema, `auto_commit.py:170`) nicht geprüft. Betroffen: nur Task 1 (#1142), nicht diese Spec.
- Nicht erneut gelesen: `consistency/report.py`, `hooks.py`, `mcp_provider_config.py`, `checkpoint.py`, `io.py:543`, Registrierung der `context_budget`-Checks, Aufrufer von `backup_drifted_files` und `context_profile_log_lines`, Schema für `role-defaults.yaml`.
- Ursache #1208 (Q1).

**ADR (Kontext / Entscheidung / Konsequenz).**
- ADR-S1 (F10-Test): Kontext: Guard-Test existiert, übersieht `runner(...)`. Entscheidung: Guard erweitern statt zweiten Test anlegen. Konsequenz: eine Stelle für die Konvention; Plan-Datei entfällt.
- ADR-S2 (Moduswert): Kontext: kein Default-Wert verifiziert. Entscheidung: aus `ORCH_MODE_*`-Variablen ableiten. Konsequenz: Provider-Overrides korrekt, kein zweiter Resolver.
- ADR-S3 (Backups): Kontext: Entscheidungen 42/56. Entscheidung: Total-Cap nur mit gitignore-Filter, Dedup liefert vorhandenen Pfad. Konsequenz: Per-Source-Verhalten und Preview-Parität unverändert; Aufrufer-Prüfung (R2).
- ADR-S4 (Pointer): Kontext: Compact-Block hat nur `GATE_CARD`. Entscheidung: Pointer-Zeile in `GATE_CARD`-Wert. Konsequenz: keine Template-Änderung, ein Render-Kanal.

**Entscheidungsverweise.** 3, 44 (#1142); 4, 38b (Flag); 6, 24, 45, 46 (#1086); 8, 43, 55 (#1000); 17, 18, 52, 56 (PR-Schnitt); 25 (Trailer: Task-Prompt gewinnt); 35 (#1141 weg); 36 (#1189); 38e (keine Closing-Keywords); 40 (#1180); 41 (#1182); 42, 56 (#1195).

## Trace-Anker: spec-id: SPEC-PHASE-C-SYNC-CONFIG-2026-11-11
