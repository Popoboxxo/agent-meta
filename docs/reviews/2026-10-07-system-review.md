# System-Review agent-meta — 2026-10-07/08

> **Zweck:** Konsolidierter Befundbericht eines read-only System-Reviews über fünf Dimensionen von agent-meta, Grundlage für die anschließenden Umsetzungs-Waves.
> **Umfang:** `scripts/sync.py` + `scripts/lib/` (a), Hooks/Guards (b), Agent-Templates/Rules/Skills (c), `scripts/admin-server.py` + `docs/ui/admin-ui.html` (d), `config/`, Schemas, `tests/`, CI (e).
> **Datenquelle:** fünf Einzelberichte `.tmp/review-dim-a.md` … `.tmp/review-dim-e.md` samt ihren angehängten unabhängigen Verifier-Pässen. Alle Zahlen und Schweregrade in diesem Dokument sind **Stand nach Verifikation**.
> **Stand / Baseline:** `main` @ `9190965f`, Discovery 2026-10-07, Verifikation 2026-10-08.
> **Review-Nachweis:** Je Dimension ein unabhängiger Verifier-Pass (code-reviewer bzw. accessibility-specialist, claude-opus-5-5, 2026-10-08), Verdikte pro Befund in Abschnitt 4.
> **Aufbewahrung:** Dieses Dokument bleibt als Review-Stand dauerhaft im Repo; Fortschritt nur in Abschnitt 7 (Umsetzungsstatus) nachtragen, Befundtexte nicht umschreiben. Die Rohberichte unter `.tmp/` sind flüchtig und nicht maßgeblich.
> **Sicherheitshinweis:** Dieses Dokument enthält keine Token- oder Secret-Werte; Admin-Token-Mechanismen werden nur beschrieben.

## Legende

| Kürzel | Bedeutung |
|---|---|
| critical / high / medium / low / info | normalisierte Schweregrade (Mapping siehe Abschnitt 3) |
| CONFIRMED | Verifier hat den Befund unabhängig bestätigt |
| CONFIRMED (partiell/korrigiert) | bestätigt, aber Teilaussage, Beispiel, Zählung oder Zeilennummer korrigiert |
| SEVERITY_ADJUSTED | Schweregrad durch Verifier geändert, Anzeige „final (orig. X)" |
| VERWORFEN (False Positive) | Verifier hat den Befund als Fehlbefund eingestuft; bleibt zur Nachvollziehbarkeit gelistet |
| XS / S / M | Aufwandsschätzung aus dem Originalbericht |
| `SR-<Dim>-NN` | neue Befund-ID dieses Berichts; Original-ID steht in der Spalte „Beleg" |

---

## 1. Executive Summary

Das Review umfasst fünf Dimensionen (Sync-Kern, Hooks/Guards, Templates/Rules/Skills, Admin-Server/-UI, Config/Tests/CI) und listet **139 Befunde**. Davon hat die Verifikation **1 als False Positive verworfen** (SR-D-17, A9), es bleiben **138 gültige Befunde**: 0 critical, 5 high, 39 medium, 79 low, 15 info. Das größte Einzelrisiko ist **SR-D-01 (N1, high, per Repro bestätigt)**: `DELETE /api/backups/<name>` im Admin-Server löscht über absolute Pfade (`//abs/pfad`) oder `../`-Traversal beliebige Dateien des Server-Users außerhalb des Repos. Das gleiche Muster betrifft Restore. Mit dem geplanten Netzwerk-Modus (#896) wird das für jeden Token-Inhaber ausnutzbar, deshalb muss der Fix vor #896 landen. Bei den Hooks bleibt **SR-B-01 (B-01) high**: `--tags` irgendwo im Push-Befehl überspringt den Branch-Guard von `dod-push-check.sh`, z. B. bei `git push origin main --tags`. **SR-B-10 (B-10)** wurde nach Verifikation von high auf **medium** herabgestuft. Strict Mode fällt still aus, wenn das Hook-Python kein PyYAML hat, aber sync.py benötigt PyYAML selbst, sodass das nur bei abweichendem Interpreter auftritt. Die übrigen zwei high-Befunde sind Accessibility-Blocker in der Admin-UI: Sidebar-Navigation (SR-D-09) und Rollen-Aktivierung (SR-D-15) lassen sich nicht per Tastatur bedienen, obwohl #730 geschlossen ist. Zwei Fehlermuster ziehen sich durch mehrere Dimensionen. Erstens ist der Claude-Pfad vollständig, während Nicht-Claude-Pfade nur Teilkopien sind; dadurch fehlen gitignore-Einträge (SR-A-11, SR-A-31). Zweitens enthalten mehrere Guards Fail-open-Pfade, obwohl sie als fail-closed dokumentiert sind (SR-B-08/10/15/17/21).

## 2. Methodik

- **Modelle:** claude-opus-5-5 (Opus 5.5) für alle Discovery-Pässe (senior-developer, Hooks-Reviewer, prompt-engineer, accessibility-specialist, Config/Test-Reviewer) und für alle Verifier-Pässe (code-reviewer bzw. accessibility-specialist). claude-haiku-4-5 für Git-Status-Prüfungen.
- **Baseline:** `main` @ `9190965f`, 2026-10-07 (Discovery) / 2026-10-08 (Verifikation, Stand unverändert).
- **Vorgehen:** Discovery read-only pro Dimension, danach unabhängiger Verifier-Pass, der jede zitierte Stelle neu gelesen und, wo möglich, reproduziert hat (Python-Einzeiler, Hook-Treiber gegen Scratch-Kopien unter `.tmp/`, statische Kontrastberechnung). Dimension (d) hat zwei getrennte Verifier-Pässe (Security, Accessibility).
- **Scope und Ausschlüsse je Dimension:**

| Dim. | In Scope | Ausgeschlossen (laut Originalbericht) |
|---|---|---|
| a | `scripts/sync.py`, `scripts/lib/` (Korrektheit, Provider-Agnostik, toter Code, Duplikate) | bereits gefixt: #751, #476, #746, #753, #899, #780 |
| b | `hooks/1-generic/*.sh`, `hooks/1-generic/release-gates/*.sh`, `scripts/lib/hook_plugins.py` | dokumentierte Grenzen in `branch-guard.md` (#592/#809), #753-Fix |
| c | `agents/1-generic` (Stichprobe + grep über Reviewer-Flotte), `agents/2-platform`, `rules/1-generic`, `rules/2-platform` (Stichprobe), `.claude/skills` (Stichprobe) | #769–#780, #844, #679, #552/#528 |
| d | `scripts/admin-server.py` (Origin-Check #897, Spot-Check), `docs/ui/admin-ui.html` (Netzwerk-Modus-UX #896, A11y #730, Ziel WCAG 2.2 AA) | — |
| e | `.github/workflows`, `config/` + Schemas, `tests/` | #452 Release-Block, #746 Keep-Array, #751 Capability-Flags, #680 Registry-Schema-Ergänzungen selbst, bekannter Flake `test_local_process_partial_line_timeout` |

## 3. Kennzahlen

**Schweregrad-Mapping (einheitlich auf 5 Stufen):**

| Normalisiert | Dim. a (major/minor/info) | Dim. b, c (HIGH/MEDIUM/LOW/INFO) | Dim. d Security (high/medium/low) | Dim. d A11y (blocker/major/minor/advisory) | Dim. e (Medium/Low-Medium/Low) |
|---|---|---|---|---|---|
| critical | — | — | — | — | — |
| high | — | HIGH | high | blocker | — |
| medium | major | MEDIUM | medium | major | Medium, Low/Medium (konservativ aufgerundet) |
| low | minor | LOW (inkl. „LOW/boundary", „LOW/design") | low | minor | Low |
| info | info | INFO (inkl. „INFO/boundary") | Prozess-Hinweis | advisory | — |

Kein Befund erreicht critical. Das hätte unauthentifizierte Ausnutzbarkeit oder großflächigen Datenverlust vorausgesetzt.

| Dimension | Befunde gesamt | davon gültig | critical | high | medium | low | info | bestätigt | False Positive | Schwere angepasst |
|---|---|---|---|---|---|---|---|---|---|---|
| a — sync.py + scripts/lib | 41 | 41 | 0 | 0 | 6 | 27 | 8 | 39 | 0 | 2 |
| b — Hooks/Guards | 33 | 33 | 0 | 1 | 10 | 18 | 4 | 32 | 0 | 1 |
| c — Templates/Rules/Skills | 18 | 18 | 0 | 1 | 6 | 10 | 1 | 16 | 0 | 2 |
| d — Admin-Server/-UI | 23 | 22 | 0 | 3 | 10 | 7 | 2 | 19 | 1 | 3 ¹ |
| e — Config/Schemas/Tests/CI | 24 | 24 | 0 | 0 | 7 | 17 | 0 | 23 | 0 | 1 ² |
| **Summe** | **139** | **138** | **0** | **5** | **39** | **79** | **15** | **129** | **1** | **9** |

¹ N3, A6, A13. Zusätzlich ist der Teilbefund Rules-Matrix in A7 von blocker auf minor gesenkt; A7 insgesamt bleibt blocker.
² E-T-12: Verdikt SEVERITY_ADJUSTED nur im Scope, die Schwere bleibt low.
Die Spalte „bestätigt" zählt CONFIRMED einschließlich partiell bzw. korrigiert bestätigter Befunde. Es gilt bestätigt + False Positive + angepasst = gesamt.

---

## 4. Findings

### 4.a Dimension (a) — scripts/sync.py + scripts/lib

| ID | Beleg | Schwere | Verdikt | Auswirkung | Empfehlung | Aufwand |
|---|---|---|---|---|---|---|
| SR-A-01 | A-01 · `scripts/sync.py:365-366, 462-514`; `scripts/lib/generated_file_drift.py:167-200`; `scripts/lib/sync_pipeline.py:896-897, 962-965` | low | CONFIRMED | `_preview_backups_to_prune` kopiert die Prune-Schleife und die Konstanten; bei Policy-Änderung driften Preview und echter Prune auseinander (IC-07-Vertrag) | Pure-Helper `plan_sync_backup_prune(target_dir, max_age, max_per)` in generated_file_drift, Konstanten importieren | S |
| SR-A-02 | A-02 · `scripts/sync.py:53-56` vs. `:369-622`; `tests/test_cleanup_preview_cli.py:183` | info | CONFIRMED | Struktur-Drift zu #481: ~240 Zeilen `--cleanup-preview`-Handler liegen in sync.py statt in `lib/cli_commands.py` | Handler + Helper nach `cli_commands.py` verschieben | S |
| SR-A-03 | A-03 · `scripts/sync.py:686-690` (korrigiert, orig. 688-692) | low | CONFIRMED | `args.dry_run`-Override bleibt bei Exception in `_build_context` mutiert (relevant für Tests, die `main()` importieren) | try/finally | S |
| SR-A-04 | A-04 · `scripts/sync.py:135, 700`; `scripts/lib/cli_commands.py:1032` | low | CONFIRMED | `_run_artifact_gate` beendet `--validate` per `sys.exit(1)` vor den Konsistenz-Checks; deren Report geht verloren | Gate-Findings in den Validate-Fehlerzähler aufnehmen statt früh zu beenden | S |
| SR-A-05 | A-05 · `scripts/lib/cli_commands.py:694` (1-arg) vs. `:862/:890`, `sync_pipeline.py:156` (2-arg); `config.py:663/1415/1451/1460/1533/2098` | low | CONFIRMED | `--only-variables`/`build_variables` ignorieren `provider-options`-Surface-Overrides → latente Divergenz zur vollen Sync; Registry ~6x pro `build_variables` geparst | `load_providers_config` einheitlich mit `config` aufrufen, einmal laden | S |
| SR-A-06 | A-06 · `scripts/lib/context.py:~2279-2420` (Literal `"Continue"` u. a. ~2310/2314/2329/2359); Aufruf `sync_pipeline.py:1174-1177` | medium | CONFIRMED | Provider-Agnostik-Verstoß, für den Guard unsichtbar: ein zweiter Provider mit `has_prompt_commands` würde Continue-förmige Dateien nach `.continue/prompts` schreiben (heute latent) | `provider` durchreichen, Registry-Key `prompt_commands_dir`, Umbenennung `sync_prompt_commands`; Guard um Provider-Literale in Call-Args, `.get()`-Keys, Subscripts und Default-Parametern erweitern | M |
| SR-A-07 | A-07 · `scripts/lib/providers.py:720-733` | info (orig. low) | SEVERITY_ADJUSTED | Top-Level-`provider-options: null` wird durch `_normalize_null_blocks` (#741) bereits zu `{}`; erreichbar ist nur noch die verschachtelte Form `provider-options: {Claude: null}` | isinstance-Guard beider Ebenen (gemeinsamer `_as_dict`-Helper, siehe SR-A-28) | S |
| SR-A-08 | A-08 · `scripts/lib/providers.py:430-437` | low | CONFIRMED (partiell) | `ai-providers: [Claude, Claude]` → Provider-Sync läuft doppelt (doppelte Writes/Logs); Null-Hälfte via `load_config` nicht erreichbar | order-preserving Dedup oder Fail-loud; `dc.get("providers")` nur einmal | S |
| SR-A-09 | A-09 · `scripts/lib/providers.py:260-315` vs. `config/ai-providers.yaml:102-109` | low | CONFIRMED | Eingebettete Fallback-Registry führt Modell-IDs vor #900 und ist intern inkonsistent | `model-tiers` aus dem Fallback entfernen oder Test „Fallback ⊆ Registry" | S |
| SR-A-10 | A-10 · `scripts/lib/providers.py:373, 453` | info | CONFIRMED | `registered_provider_names`/`_framework_provider_entry` parsen die Registry bei jedem Aufruf neu (Hot-Path) | `lru_cache` auf pfad-keyed Raw-Loader mit `deepcopy` (Normalizer mutieren in place) | S |
| SR-A-11 | A-11 · `scripts/lib/sync_pipeline.py:1414-1426` (+341-343); `cli_commands.py:1233-1234`; `env.py:99-102` | medium (orig. major) | CONFIRMED | Projekte ohne Provider mit `has_dedicated_context_file` (Opencode/Gemini/Codex-only) erhalten keine env/viz/skill-gitignore-Einträge; `.meta-config/env.*` mit unmaskierten Secret-Defaults wird committbar | `env_gitignore` + viz + skills in beiden Zweigen anhängen; nur exakt-vs-additiv unterscheiden | S |
| SR-A-12 | A-12 · `scripts/lib/gitignore.py:213` (Verifier-Ergänzung: `"Claude" not in providers`), `:233`, `:257`; `sync_pipeline.py:309, 1395` | low | CONFIRMED | Basisblock ist namens- statt capability-gesteuert: ein Nicht-Claude-Provider mit dediziertem Kontext erhält einen leeren Basisblock und verliert eigene Einträge (verschärft SR-A-11) | Union der `gitignore_entries` aller aktiven Provider mit `has_dedicated_context_file` | S |
| SR-A-13 | A-13 · `scripts/lib/config.py:839` vs. `roles.py:445` | low | CONFIRMED | Validator-Warnung für flache `model-overrides` hartkodiert `"Claude"`, Resolver nutzt Capability `model-overrides-flat` → falsche Warnung bei Capability-Änderung | über `provider_has_capability(pc, "model-overrides-flat")` iterieren | S |
| SR-A-14 | A-14 · `scripts/lib/sync_pipeline.py:291-312` | info | CONFIRMED | Naming-Debt `is_claude` (bedeutet „dedizierte Kontextdatei aktiv") begünstigt Claude-only-Annahmen (SR-A-11/12) | Umbenennen in `has_dedicated_ctx` samt abhängiger Funktionsnamen | S |
| SR-A-15 | A-15 · `scripts/lib/io.py:338-348` (`write_atomic`); live `.claude/hooks/*.sh` = 0600 | medium (orig. major) | CONFIRMED | `mkstemp` + `os.replace` erzwingt 0600 für jede generierte Datei und entfernt bestehendes `+x`; Hooks laufen nur dank `bash`-Präfix; Gruppen-Checkouts/Container mit anderer UID brechen | vor `os.replace` `chmod` auf bestehenden Modus bzw. `0o666 & ~umask`; 0600 für `project.yaml` (#864) als expliziter Opt-in-Parameter | S |
| SR-A-16 | A-16 · `scripts/lib/io.py:70-73`; `providers.py:248-250` | low | CONFIRMED (per `python3 -I` reproduziert) | Ohne PyYAML stiller Fallback auf Claude-only-Registry → Sync „erfolgreich" mit falscher Registry; Fallback-Kommentar sachlich falsch | Für Framework-Registries fail-loud statt degradieren | S |
| SR-A-17 | A-17 · `scripts/lib/io.py:443-444, 459-468` | low | CONFIRMED | `write_checked(dry_run=True)` überspringt den Secret-Scan → `sync.py --check` (CI) kann grün sein, obwohl die echte Sync abbricht | Scan im Dry-Run als Finding (nicht als Raise) melden | S |
| SR-A-18 | A-18 · `scripts/lib/rules.py:311` (toter Import), `:464`; `sync_pipeline.py:1193` | low (orig. major) | SEVERITY_ADJUSTED | `{{platform.*}}` bleibt in Skill-Channel-Rules roh stehen; nur bei expliziter Projekt-Override (kein Default-Preset) für Opencode/ZCode/KimiCode; zitiertes Beispiel `_wf-sharkord-docker-binaries.md` wird nie gesammelt | `platform_vars` durch `sync_embedded_rule_files` reichen und anwenden | S |
| SR-A-19 | A-19 · `scripts/lib/rules.py:549-554` | low | CONFIRMED | `sync_speech_mode('full')` löscht eine gleichnamige nutzereigene Datei ohne Managed-Index-Prüfung | Löschung an Managed-Index binden | S |
| SR-A-20 | A-20 · `scripts/lib/rules.py:558-561, 580-587` | low | CONFIRMED | Raw `read_text`/`write_text` statt `read_managed_index`/`write_managed_index`; korrupter Index bricht die Sync ab (Klasse IC-01/IC-08); Index wird pro Lauf doppelt geschrieben | Shared-Helper verwenden | S |
| SR-A-21 | A-21 · `scripts/lib/rules.py:284, 377, 386-391`; `roles.py:353, 383` (Verifier-Ergänzung) | low | CONFIRMED | Provider-Literal-Defaults (`"Opencode"`/`"Claude"`), vom Guard nicht gescannt; Docstring verweist auf nicht existierendes `_SKILL_CHANNEL_PROVIDERS` | `provider` zum Pflichtparameter machen, Docstring korrigieren | S |
| SR-A-22 | A-22 · `scripts/lib/rules.py:103-114` | low | CONFIRMED (partiell) | `rules: {foo: skip}` → `ValueError` ohne Datei-/Key-Kontext; `rules: null` via `load_config` nicht erreichbar | isinstance-Guards mit Kontextmeldung | S |
| SR-A-23 | A-23 · `scripts/lib/rules.py:176-184` | info | CONFIRMED (latent) | `rule-gates` nur im 1-generic-Layer ausgewertet; gleichnamige 2-platform-Rule reaktiviert eine gegatete Rule | Gate auch auf Platform-Layer anwenden | S |
| SR-A-24 | A-24 · `scripts/lib/cli_commands.py:287-301`, `:516`, `:1115-1116`, `:1268` | medium (orig. major) | CONFIRMED | `--validate` bewertet ein altes `<test_repo>/sync.log`; Fehler des aktuellen Laufs (`log.errors`) beeinflussen den Exit-Code nicht → False Green | Delta von `log.errors` seit Schleifenbeginn zählen | S |
| SR-A-25 | A-25 · `scripts/lib/cli_commands.py:225-285` vs. `sync_pipeline.py` `_sync_stage_per_provider` (~1100-1260) | medium (orig. major) | CONFIRMED (partiell) | Validate-Loop ist eine driftende Handkopie (ohne `platform_vars`, Prompt-Commands, `sync_embedded_rule_files`, MCP, gitignore, Base-Stage) → `--validate` prüft eine andere Pipeline als Nutzer ausführen; KeyError-Teil heute nicht erreichbar | `_sync_stage_*` mit `project_root=test_repo_path` wiederverwenden | M |
| SR-A-26 | A-26 · `scripts/lib/cli_commands.py:217-219` | info | CONFIRMED | No-op-Zuweisung `PROJECT_NAME`; Kommentar nennt falsche Variable | entfernen bzw. Kommentar korrigieren | S |
| SR-A-27 | A-27 · `scripts/lib/config.py:1415-1416, 1451-1452, 1460-1462, 1533-1534, 2098` | low | CONFIRMED | 5 Registry-Parses + 5 `resolve_providers` pro `build_variables` | einmal in `build_variables` berechnen und durchreichen | S |
| SR-A-28 | A-28 · `scripts/lib/config.py:1568-1578` (Muster auch 1518-1521, 1541-1553) | low | CONFIRMED | Verschachtelte Nulls (`orchestrator: {unknown-fallback: null}`) → `AttributeError`; #741 normalisiert nur Top-Level | kleiner `_as_dict()`-Helper in allen Block-Readern | S |
| SR-A-29 | A-29 · `scripts/lib/config.py:1424-1432` vs. `providers.py:486-498` | low | CONFIRMED | `AGENT_LOCATIONS`/Routing-Gruppen nutzen rohes `context_file` statt `resolve_context_filename` → Abweichung bei Adapter-/Topologie-Setups | `resolve_context_filename` verwenden | S |
| SR-A-30 | A-30 · `scripts/lib/config.py:1440-1445` | info | CONFIRMED | Provider-Name im provider-agnostischen Platzhalter `AGENT_HINTS_CLAUDE`; Umbenennung ist template-facing (Major-Bump) | beim nächsten Major umbenennen | M |
| SR-A-31 | A-31 · `scripts/lib/context.py:792, 975-1002, 1135, 1925-1953`; `config/ai-providers.yaml` `gitignore_entries` | medium (orig. major) | CONFIRMED | `AGENTS.personal.md` wird für Gemini/Codex/Mammouth/ZCode/KimiCode angelegt, aber nur bei Opencode gitignored → landet bei `git add -A` im Commit | Registry-Key `personal_file`/`personal_template`, der auch gitignore speist | S |
| SR-A-32 | A-32 · `scripts/lib/context.py:1898-1953` | low | CONFIRMED | `init_claude_personal`/`init_opencode_personal` sind bis auf Dateinamen identisch; Strategien provider-benannt mit providerspezifischen Seiteneffekten | ein `init_personal_file(pc)` aus Registry-Keys | S |
| SR-A-33 | A-33 · `scripts/lib/context.py:995-999` | low | CONFIRMED | `_shares_context_with_embedded_rules` iteriert die gesamte Registry statt der aktiven Provider → Codex-only-Projekt landet in Embedded-Rules-Strategie (+ SR-A-31) | aktive Provider-Liste übergeben | S |
| SR-A-34 | A-34 · `scripts/lib/context.py:2041-2136`; 51 `.write_text(`-Stellen in 19 Dateien unter `scripts/lib` | low | CONFIRMED | `.gitignore`, `CLAUDE.md` u. a. nicht-atomar, ohne LF-Normalisierung und ohne Secret-Scan (#573) geschrieben | auf `write_atomic`/`write_checked` umstellen; Guard-Test gegen Raw-`write_text` | M |
| SR-A-35 | A-35 · `scripts/lib/context.py:1971-1981, 1999-2002` | info | CONFIRMED | `pc[provider]` → KeyError bei unbekanntem Provider (geringe Erreichbarkeit) | `.get(provider, {})` | S |
| SR-A-36 | A-36 · `scripts/lib/provider_transform.py:549` `_map_claude_tools_to_gemini_tools` | low | CONFIRMED | toter, provider-benannter Code | löschen | S |
| SR-A-37 | A-37 · `scripts/lib/context.py:1464` `_extract_rule_compact_from_content` | low | CONFIRMED | toter Code (~90 Zeilen), Nachfolger `compact_embedded_rule` | löschen | S |
| SR-A-38 | A-38 · `scripts/lib/reflection.py:137/150/165` | low | CONFIRMED | `validate_reflection_pairs`, `inject_loop_config`, `get_reflection_pairs_for_role` ohne Aufrufer | löschen | S |
| SR-A-39 | A-39 · `scripts/lib/pipelines.py:670` `validate_plan_ref`; CHANGELOG l.1029; `docs/guides/quality-pipelines.md:111` | low | CONFIRMED | in CHANGELOG/Guide beworben, aber nicht verdrahtet (Feature-/Doku-Drift) | in `validate_pipelines` einbinden oder entfernen + Doku anpassen | S |
| SR-A-40 | A-40 · `deactivation.py:72`; `config_audit.py:539`; `standalone.py:420`; `viz.py:532` | low | CONFIRMED | vier tote Funktionen, teils Duplikate (`write_event` vs. `viz-logger.py::write_event_safe`) | löschen | S |
| SR-A-41 | A-41 · `scripts/lib/deactivation.py:50-97` vs. `providers.py:430-437` | low | CONFIRMED | Deaktivierungsfilter 4x implementiert; `get_active_providers` filtert doppelt; nur eine Kopie null-safe | `resolve_providers` an `deactivation.is_provider_active` delegieren | S |

### 4.b Dimension (b) — Hooks & Guards

| ID | Beleg | Schwere | Verdikt | Auswirkung | Empfehlung | Aufwand |
|---|---|---|---|---|---|---|
| SR-B-01 | B-01 · `hooks/1-generic/dod-push-check.sh:135-144, 174` | **high** | CONFIRMED (ausgeführt; Teilbeispiel `--tags;` ohne Leerzeichen ist kein Bypass) | `--tags` bzw. `tag <name>` irgendwo im Befehl markiert den ganzen Push als tag-only → Branch-Guard übersprungen, z. B. `git push origin main --tags`, `git push origin tag v1 main`, `--tags && git push origin main`. Einzige Branch-Guard-Schicht für die `git`-Rolle | tag-only nur bei ausschließlich Tag-Refs ohne weitere Positions-Refs; Parsing am ersten Shell-Separator beenden | S |
| SR-B-02 | B-02 · `dod-push-check.sh:164, 174` | medium | CONFIRMED (nur getraced) | Guard prüft aktuellen Branch statt Ziel-Ref: `HEAD:main`, `feat:main`, Push aus detached HEAD erreichen `main`; nicht in den dokumentierten Grenzen | Refspec-Ziel parsen oder „security boundary"-Claim zurücknehmen und auf Remote-Branch-Protection verweisen | M |
| SR-B-03 | B-03 · `dod-push-check.sh:53` | medium | CONFIRMED (ausgeführt) | `git -C . push`, `git --no-pager push`, `/usr/bin/git push` umgehen Branch-Guard und Test-Gate | Tokenizer `parse_git` aus `orchestrator-guard-impl.sh` (#591) wiederverwenden | S |
| SR-B-04 | B-04 · `dod-push-check.sh:53` | low | CONFIRMED (Beispiel korrigiert) | Rohtext-Match: `grep -rn git push docs/` oder `gh pr create --body "... git push ..."` → „Push blocked" bzw. unnötiger Volltestlauf (bis 300 s). Das Originalbeispiel mit Anführungszeichen trifft nicht | wie SR-B-03 | S |
| SR-B-05 | B-05 · `dod-push-check.sh:245, 248` | low | CONFIRMED (rc 127 statt 1) | `set -u` aus dem #753-Fix lässt TEST_COMMANDs mit ungesetzter Variable fehlschlagen; im Changelog nicht erwähnt | `-u` entfernen, nur `-o pipefail` behalten | XS |
| SR-B-06 | B-06 · `dod-push-check.sh:238, 245, 253` | low | CONFIRMED | nicht-numerisches `TEST_TIMEOUT` (rc 125) als „Tests must pass" gemeldet | Config-Fehler separat melden | XS |
| SR-B-07 | B-07 · `dod-push-check.sh:20, 219-229` | info | CONFIRMED | „security boundary"-Label trotz fälschbarem Cache `.git/agent-meta-dod-push-check-cache` und SR-B-01..03 | Wortlaut auf „for THIS check" scopen wie `orchestrator-guard-impl.sh:107` | XS |
| SR-B-08 | B-08 · `hooks/1-generic/orchestrator-guard.sh:47-48` | medium | CONFIRMED (latent) | Wrapper reicht beliebige Exit-Codes durch; ein Runtime-Absturz der Impl (rc 1, 141, 128+n) wird vom Harness als „erlauben" gelesen (fail open) | nur 0 und 2 durchreichen, alle anderen Codes melden und mit 2 beenden | XS |
| SR-B-09 | B-09 · `orchestrator-guard-impl.sh:130-135` | low | CONFIRMED (ausgeführt) | ungültiges JSON-Payload → rc 0, inkonsistent zur #595-Fail-closed-Haltung | fail closed | XS |
| SR-B-10 | B-10 · `orchestrator-guard-impl.sh:788, 826` | medium (orig. high) | SEVERITY_ADJUSTED | Strict Mode still deaktiviert, wenn das Hook-Python kein PyYAML hat (reproduziert rc 2 → rc 0). Da sync.py selbst PyYAML erzwingt (`config.py:279-282`), nur bei abweichendem Interpreter (venv/uv/pipx) | stdlib-Reader für `orchestrator.mode`/`provider-overrides.<P>.mode`/`strict`/`enabled` oder fail closed, wenn Config existiert aber nicht parsebar ist (wie Containment F4). `import yaml` in den `try` verschieben reicht **nicht** | S |
| SR-B-11 | B-11 · `orchestrator-guard-impl.sh:176-179, 774` | medium | CONFIRMED (ausgeführt) | `PROJECT_ROOT` = Payload-`cwd` ohne Walk-up → Strict Mode und Allowlist aus Unterverzeichnis heraus aus | `$CLAUDE_PROJECT_DIR` bevorzugen bzw. Walk-up wie `dod-push-check.sh:61-72` | S |
| SR-B-12 | B-12 · `orchestrator-guard-impl.sh:401-434` | medium | CONFIRMED (ausgeführt) | mit `git`-Sentinel erlaubt: `push origin :main`, `push --prune`, `checkout .`, `checkout -f main`, `update-ref -d`, `reflog expire --expire=now --all`, `stash -q drop` (gleiche Ref-Verlust-Klasse wie das bereits geblockte `--delete`) | Destructive-Set erweitern | S |
| SR-B-13 | B-13 · `orchestrator-guard-impl.sh:285-288` | medium | CONFIRMED (ausgeführt) | Mutation-Gate kennt `pull`, `switch`, `cherry-pick`, `revert`, `am`, `update-ref`, `worktree`, `reflog` nicht; `git switch main` erlaubt, `git checkout main` geblockt | Set `MUTATING` ergänzen | XS |
| SR-B-14 | B-14 · `orchestrator-guard-impl.sh:720-723` | low | CONFIRMED (ausgeführt, auch live getroffen) | jedes Token `git` gilt als Aufruf: `echo git commit done` → Block | nur das Command-Word zählen (wie `is_fs_destructive` `:677-683`) | S |
| SR-B-15 | B-15 · `orchestrator-guard-impl.sh:738-739` (Fail-open selbst dokumentiert `:273-274`) | low | CONFIRMED (theoretisch) | Scan-Fehler (z. B. Python 2 als `python`) → Destructive- und Mutation-Gate aus | fail closed bei leerem `_GIT_SCAN_RAW` | XS |
| SR-B-16 | B-16 · `hooks/1-generic/repo-containment-impl.sh:434-449` | medium | CONFIRMED (live reproduziert) | Heredoc-Inhalt wird zeilenweise als Shell-Befehl gescannt → False-Positive-Blocks bei Markdown mit Redirect-Text oder Blockquote `> /etc/...` | Zeilen zwischen Heredoc-Start und Terminator überspringen | S |
| SR-B-17 | B-17 · `hooks/1-generic/repo-containment.sh:47-48` | medium | CONFIRMED (latent) | gleicher Exit-Code-Fail-open wie SR-B-08 | wie SR-B-08 | XS |
| SR-B-18 | B-18 · `repo-containment-impl.sh:140-169` | low | CONFIRMED (ausgeführt: Write `/tmp/x` mit cwd `/tmp` → rc 0) | Jail-Root folgt Payload-`cwd`; liegt die Shell außerhalb des Projekts, wird dieses Verzeichnis zur Wurzel | fester Anker (`$CLAUDE_PROJECT_DIR` bzw. Skriptpfad) | S |
| SR-B-19 | B-19 · `repo-containment-impl.sh:480-488` | low | CONFIRMED (ausgeführt) | `perl -pi -e`, `sed -Ei`, `sed -ni`, `cp -t DIR`, `cp a /etc/b -v` nicht erkannt | Flag-Cluster und `-t` erkennen | XS |
| SR-B-20 | B-20 · `repo-containment-impl.sh:193-249` vs. `orchestrator-guard-impl.sh:788` | info | CONFIRMED | ohne PyYAML: Containment fail closed, Strict Mode fail open; Nutzer-Opt-out `repo_containment.enabled: false` wird ignoriert | gemeinsamer stdlib-YAML-Subset-Reader in `hook_common.sh` | S |
| SR-B-21 | B-21 · `dod-push-check.sh:11, 53` | medium | CONFIRMED (300 KB: 4/4 Bypass; 70 KB nicht reproduziert, zeitabhängig) | `printf` in `grep -q` unter `pipefail`: Writer bekommt SIGPIPE (141), Pipeline gilt als gescheitert → `exit 0` → Branch-Guard und Test-Gate übersprungen bei großem mehrzeiligen Befehl | Here-String statt Pipe oder `grep -E ... >/dev/null` ohne `-q` | XS |
| SR-B-22 | B-22 · `hooks/1-generic/lifecycle-check.sh:26, 50-51, 55-57, 84, 88` | low | CONFIRMED (+ `:88` toter Zweig) | gleiches SIGPIPE-Muster; `tool_result.exit_code` ist kein Claude-Feld (`tool_response`); `grep -oP` fehlt auf BSD/macOS; Release-Regex trifft Branchnamen mit `vX.Y.Z` | Feldnamen korrigieren, portable Regex | S |
| SR-B-23 | B-23 · `hooks/1-generic/pre-release-check.sh:161` | low | CONFIRMED (kosmetisch) | SIGPIPE-Race zeigt falschen Remediation-Hinweis | Process-Substitution oder Here-String | XS |
| SR-B-24 | B-24 · `pre-release-check.sh:232-260` | low | CONFIRMED (live) | „all release gates passed", obwohl alle 3 Gates nur `[SKIP]` waren | „N passed, M skipped" ausweisen (Marker oder reservierter Exit-Code) | S |
| SR-B-25 | B-25 · `pre-release-check.sh:143-148` | low | CONFIRMED | Binary-Mode-Zeilen von `sha256sum -b` (`*name`) werden abgelehnt | führendes `*` entfernen | XS |
| SR-B-26 | B-26 · `hooks/1-generic/antigravity-json-adapter.sh:122-127, 148` | low | CONFIRMED (theoretisch) | `workspacePaths[0]` vor `args.Cwd` → relative Schreibziele falsch aufgelöst; unbekannte AGY-Tools ungemappt; Absturz des Ziels = erlauben | `args['Cwd']` bevorzugen | XS |
| SR-B-27 | B-27 · `release-gates/docker-image-scan.sh:89-91, 99` | low | CONFIRMED | `FROM --platform=...`, `FROM scratch`, `FROM ${BASE_IMAGE}` → falsche FAILs; Infra-Fehler von trivy nicht von Findings unterscheidbar; `Dockerfile.*` nicht gefunden | robustes FROM-Parsing, Fehlerklassen trennen | S |
| SR-B-28 | B-28 · `release-gates/action-pin-validation.sh:50, 60-62, 64-75` | low | CONFIRMED | Subpath-Actions (`owner/repo/path@ref`) nie validiert, `:60-62` tot; Branch-Pins als „tag not found"; `\s` nur GNU → auf BSD False Pass | Regex erweitern, POSIX-Klassen, Netzwerkfehler separat | S |
| SR-B-29 | B-29 · `release-gates/artifact-freshness.sh:20, 108`; `docker-image-scan.sh:21`; `action-pin-validation.sh:20` | low | CONFIRMED | Gates fail open bei fehlender `hook_common.sh`; Lib nicht im Checksum-Manifest (#603); `max()` über leere Menge → Traceback | Lib mitchecksummen oder in `docs/RELEASE_GATES.md` dokumentieren; `max()` absichern | XS–S |
| SR-B-30 | B-30 · `hooks/1-generic/viz-log.sh:43-45` | low | CONFIRMED | erste 120 Zeichen jedes Bash-Befehls unredigiert in `.meta-viz/events.jsonl` (gitignored, nur lokal) | `hook_redact_secrets` (#596) anwenden | XS |
| SR-B-31 | B-31 · `scripts/lib/hook_plugins.py:150-162, 338-350` | low | CONFIRMED (Auswirkung korrigiert) | `.agent-meta-managed` wird bei leerem Managed-Set nicht aktualisiert → eine später gleichnamig angelegte Projektdatei wird bei der nächsten Sync gelöscht | Index auch bei leerem Set schreiben bzw. entfernen | XS |
| SR-B-32 | B-32 · deployed `.claude/hooks/*.sh`, `release-gates/*.sh` = `-rw-------` | info | CONFIRMED | Querverweis SR-A-15; heute ohne Laufzeitwirkung (alle Aufrufe mit `bash`-Präfix); Checksummen unberührt | über SR-A-15 beheben | — |
| SR-B-33 | B-33 · `lib/hook_common.sh:19`, `lifecycle-check.sh:17`, `sync-on-config-change.sh:17`, `viz-log.sh:16`, `dod-push-check.sh:20` | info | CONFIRMED | Boundary-Labels veraltet („zwei Hooks" vor repo-containment) und inkonsistente Fail-Richtung je Guard | Tabelle pro Guard (Boundary-Typ, Fail-Richtung je Fehlermodus, bekannte Lücken) in `branch-guard.md#guard-terminologie` | XS |

**Zusatzbeobachtungen des Verifiers (ohne eigene ID, für die Fix-Wave):** Der Write-Target-Detektor in `repo-containment-impl.sh:492` endet mit `2>/dev/null || true`. Stürzt er ab, wird der Befehl erlaubt (gleiche Klasse wie SR-B-15). Außerdem ist `lifecycle-check.sh:88` toter Code (siehe SR-B-22).

### 4.c Dimension (c) — Templates / Rules / Skills

| ID | Beleg | Schwere | Verdikt | Auswirkung | Empfehlung | Aufwand |
|---|---|---|---|---|---|---|
| SR-C-01 | C-01 · `agents/1-generic/backend-reviewer.md:64`, `database-reviewer.md:64`, `ui-reviewer.md:64`, `frontend-reviewer.md:66`, `ai-security-guardian.md:111`, `app-lifecycle-governor.md:100`, `prompt-governor.md:120`, `security-auditor.md:217` | **high** | CONFIRMED (Tool-Mismatch nur 4/8) | Long-Report-Pfad `/tmp/opencode/...`: Provider-Name im 1-generic-Layer, Pfad außerhalb des Repos (verletzt Repo-Containment), und für das Reviewer-Quartett ohne Write/Bash unausführbar → Agent halluziniert Pfad oder bricht Contract | read-only Rollen: #514-Wortlaut aus `code-reviewer.md:203-212` (Chunks k/n, Persistenz via Orchestrator); schreibfähige Rollen: `.tmp/<role>-<topic>.md`; idealerweise Snippet-Block | S |
| SR-C-02 | C-02 · `llm-evaluator.md:149`, `rag-engineer.md:144`, `ai-observability-engineer.md:145`, `ai-governance-engineer.md:140`, `code-reviewer.md:202-231` | medium | CONFIRMED | Post-#833-Drift: fünf Templates inlinen den Output-Guard; Snippet-Änderungen erreichen sie nicht | 4x durch `{{OUTPUT_GUARD_BLOCK}}` ersetzen; code-reviewer → #514-Text + `{{BACKGROUND_PROCESS_GUARD_BLOCK}}`; Lint gegen wörtliche Snippet-Bodies | S |
| SR-C-03 | C-03 · `snippets/agents/background-process-guard.md`; `scripts/lib/config.py:1925` (korrigiert, orig. 1924) | low | CONFIRMED | `BACKGROUND_PROCESS_GUARD_BLOCK` hat 0 Nutzer in `agents/` (Plan nannte 49) | in code-reviewer nutzen (SR-C-02) oder Snippet + Variable entfernen | XS |
| SR-C-04 | C-04 · `snippets/agents/output-guard.md`, `background-process-guard.md` | low | CONFIRMED | Guard-Prosa deutsch in englischen Templates (48+ gerenderte Agenten), Sprachmix im System-Prompt | ins Englische übersetzen, Golden-Fixtures `tests/fixtures/slimming-golden/` nachziehen | S |
| SR-C-05 | C-05 · `code-reviewer.md:221, 229`; `docker.md:128, 130`; `devops-engineer.md:202, 204` | low | CONFIRMED | Beispielcode schreibt nach `/tmp`, kollidiert mit Repo-Containment; Modelle kopieren Beispiele wörtlich | `.tmp/` verwenden | XS |
| SR-C-06 | C-06 · `agents/1-generic/senior-developer.md:132-139` vs. `orchestrator.md:107, 117, 122, 133, 140-142` | medium (orig. high) | SEVERITY_ADJUSTED | senior-ESCALATE-Card liefert kein `reason`/`metric`, die Orchestrator-Intake-Regel verlangt beides. Gleichzeitig definiert orchestrator.md den principal-Gate selbst mit „task summary + failure log". Ergebnis ist ein Widerspruch, der eine Nachreichungsrunde erzwingt, aber keinen dauerhaften Block | senior-Contract um `ESCALATE_REASON`/`ESCALATE_METRIC` ergänzen (Feldnamen wie `developer.md:118-119`) **und** `orchestrator.md:117/:133` angleichen | XS |
| SR-C-07 | C-07 · `junior-developer.md:105`, `developer.md:118-119, 125`, `senior-developer.md:136-138` (+ `se-developer:133`, `se-junior-developer:122` ungeprüft) | medium | CONFIRMED | drei Feldnamens-Schemata für dieselbe ESCALATE-Card → Handoff-Contract-Bruch | kanonisches Snippet `snippets/agents/escalate-card.md` (`{{ESCALATE_CARD_BLOCK}}`) in allen Tiers inkl. se-* | S |
| SR-C-08 | C-08 · `agents/1-generic/concept-reviewer.md:157` | low | CONFIRMED | deutscher Text im englischen Output-Contract | übersetzen | XS |
| SR-C-09 | C-09 · `agents/2-platform/*.md` mit `based-on:` (16 von 18 veraltet, z. B. `agent-meta-developer.md` developer@4.0.2 vs. 4.6.0); `scripts/lib/config_audit.py:519` | medium | CONFIRMED (reproduziert) | Section-`replace` friert alte Generic-Inhalte ein; z. B. fehlen „Small, self-contained changes only" und „Never report done…" in sharkord-/agent-meta-developer; Audit meldet nur WARN | pro Override 3-Wege-Abgleich, `replace` → `append-after` wo möglich, `based-on` nachziehen; optional `--validate`-Fehler ab Minor-Abstand ≥ N | M |
| SR-C-10 | C-10 · `agents/2-platform/sharkord-developer.md:84-99` | medium | CONFIRMED | Instruction-Bleed: EN/DE-Duplikate, REQ-Pflicht doppelt, unbedingte Test-Zeile (`:99`) widerspricht leer gerendertem `{{DOD_TESTS_BLOCK}}` | DE-Duplikate und Test-Zeile streichen | XS |
| SR-C-11 | C-11 · `agents/1-generic/developer.md:138`; `agents/2-platform/agent-meta-developer.md:157` | low | CONFIRMED | JS/TS-Regel „No default exports" als universelle Regel, in Python-/YAML-Projekten irreführend | in `LANGUAGE_BEST_PRACTICES_BLOCK` oder Platform-Layer verschieben | XS |
| SR-C-12 | C-12 · `agents/1-generic/developer.md:25, 137, 145-146`; `scripts/lib/config.py:1600-1603`; gerendert `.claude/agents/developer.md:32/209/229-230` | low | CONFIRMED | Anti-Recursion 3x im selben Prompt, teils deutsch; Token-Redundanz | `developer.md:145-146` streichen, Block-Text englisch | XS |
| SR-C-13 | C-13 · `rules/1-generic/a2a-delegation-gates.md` (8208 B; „Bekannte Grenzen" 2715 B, `:20-39` 1396 B); gerendert SKILL.md 6985 B | medium | CONFIRMED | ~50 % des Skills ist Maintainer-Doku ohne Handlungsrelevanz für dispatchende Agenten | Abschnitte auf 1–2 Zeilen + Link auf `docs/concepts/a2a-handoff-protocol.md` kürzen (~900 Tok Ersparnis pro Laden) | S |
| SR-C-14 | C-14 · `rules/1-generic/a2a-delegation-gates.md:33` → gerendert SKILL.md:38 | low | CONFIRMED | Meta-Referenz auf Platzhalternamen wird substituiert („wie der Platzhalter `300`") | Satz ohne `{{}}` umformulieren | XS |
| SR-C-15 | C-15 · `rules/1-generic/a2a-delegation-gates.md:17, 90` | info (orig. low) | SEVERITY_ADJUSTED | „z. B. Claude Code" in einer Rule ist kein provider-spezifischer Prompt; `:90` ist bereits durch SR-C-13 abgedeckt | „z. B. Claude Code" → „die Harness" (optional, nicht blockierend) | XS |
| SR-C-16 | C-16 · `rules/2-platform/agent-meta-conventions.md:6`; `rules/1-generic/*.md` (0/25 mit `version:`) | low | CONFIRMED | „Bump on every content change" deckt render-neutrale Refactors (#833) formal nicht ab; Rules unversioniert | Wortlaut auf „Änderung der gerenderten Ausgabe" präzisieren; Versionierung von Rules bewusst entscheiden | XS / S |
| SR-C-17 | C-17 · `rules/1-generic/use-lazy-rules.md` (Stand 2026-09-07) | low | CONFIRMED | 10 von 25 Skills fehlen im always-on-Index (u. a. `spec-plan-workflow`, auf den `use-orchestrator.md` verweist); `mcp-*` statisch gelistet | Tabelle von sync.py aus `skills_dir` + Description generieren | S |
| SR-C-18 | C-18 · `rules/1-generic/issue-lifecycle.md` (184 B) | low | CONFIRMED | bekannter Fallstrick fehlt: bei Kommaliste nach `Resolves` schließt nur die erste `#N` automatisch | Zeile „ein Keyword pro Issue" ergänzen | XS |

### 4.d Dimension (d) — admin-server.py + admin-ui.html

**Plan-Abgleich #897 (keine eigenen Befund-IDs):** D1–D6 und das argv-Token (Start via `--admin-token`-Argument) bestätigt der Discovery-Pass gegen den Plan `docs/plans/2026-10-07-admin-ui-network-and-manager-plan.md`. U1 ist bestätigt. U2 ist korrigiert: Das Backup-Modal hat einen Schließen-Weg (Header-`×` `admin-ui.html:745`, Overlay-Klick `:834-836`), leer ist nur der Footer. Die Begründung in Plan §2 ist anzupassen, AC-897-7 bleibt sinnvoll. Diese Plan-Bestätigungen wurden von keinem Verifier-Pass erneut geprüft.

#### Security / Korrektheit

| ID | Beleg | Schwere | Verdikt | Auswirkung | Empfehlung | Aufwand |
|---|---|---|---|---|---|---|
| SR-D-01 | N1 · `scripts/admin-server.py:3470-3474` (`do_DELETE`), `:3602`, `:3606-3626` (`_resolve_route`), `:3798-3802`, `:5492-5509`; `scripts/lib/backup.py:608-649` (Kern `:629-643`), Restore `:440-445` | **high** | CONFIRMED (per Repro; Fix-Empfehlung korrigiert) | Path-Traversal/Arbitrary File Delete: `DELETE /api/backups//abs/pfad` und `.../../../x` löschen Dateien außerhalb von `project_root` (Repro mit Wegwerfdateien unter `.tmp/n1-repro/`). Im Netzwerk-Modus (#896) kann jeder Token-Inhaber beliebige Dateien des Server-Users löschen. Restore nimmt `archive_name` aus dem JSON-Body und löst ihn genauso auf | Fix an der Trust-Boundary in den HTTP-Handlern `_handle_delete_backup` und `_handle_restore_backup`: nur nackter Dateiname (`[\w.-]+\.zip`, nicht `.`/`..`), sonst HTTP 400. `Path(archive_name)`-Fallback in `lib/backup.py` **nicht** pauschal entfernen, weil CLI und Tests ihn nutzen. Optional Containment-Check nur im Primärpfad. Handler-Regressionstests | S |
| SR-D-02 | N2 · `scripts/admin-server.py:4258, 4390, 4434, 4775, 4899` (korrigiert, orig. ±3); `_read_body` `:3233-3252` | medium | CONFIRMED (Detail korrigiert) | fünf Handler umgehen `MAX_BODY_SIZE` (#585): großes `Content-Length` → Speicherdruck/`MemoryError`, blockierende Threads (authentifizierter DoS). Negative Werte werden entgegen dem Original geprüft | alle fünf auf `self._read_body()` umstellen | S |
| SR-D-03 | N3 · `scripts/admin-server.py:3225-3231` (`_send_bytes`), `:5049-5053` (`_serve_ui`), `:3368-3378` | low (orig. medium) | SEVERITY_ADJUSTED | Kein Clickjacking-Schutz (`X-Frame-Options`/`frame-ancestors`/`nosniff`/`Referrer-Policy` fehlen). Im Token-Modus praktisch nicht ausnutzbar, weil das Token in `sessionStorage` liegt und Storage im Third-Party-iframe partitioniert ist. Restrisiko besteht im Loopback-Modus ohne Token, abgemildert durch die Zwei-Schritt-Bestätigung und Browser-Schutz für lokale Netze | `X-Frame-Options: DENY`, `Content-Security-Policy: frame-ancestors 'none'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer` in `_send_bytes`/`_serve_ui` | S |
| SR-D-04 | N4 · `scripts/admin-server.py:929-931, 933-937` | low | CONFIRMED (plan-gedeckt 897-1/897-2) | Origin-/Host-Vergleich case-sensitiv → Großbuchstaben in `allowed-hosts` matchen nie (fail closed, nur Usability) | Umsetzung über Plan 897-1/897-2 (Lowercase-Normalisierung) | — |
| SR-D-05 | N5 · `docs/ui/admin-ui.html:8308-8311` (Restore), `:8320` (Delete); Server `admin-server.py:5488`, `backup.py:445, 464, 599-603, 635, 649` | medium | CONFIRMED (Scope korrigiert: Create `:8340` nicht betroffen) | UI meldet Erfolg bzw. schweigt bei HTTP 200 + `{"success": false}`. Kritisch bei Restore mit `force: true`: Das Provider-Verzeichnis wird per `rmtree` geleert, der Extract scheitert, und die UI zeigt trotzdem „Restored successfully" | Server: `success: False` → 4xx, oder UI: `r.success` prüfen und Fehler-Toast | S |
| SR-D-06 | N6 · Issue #730 (`CLOSED` 2026-09-11); `admin-ui.html:1631-1635`, `a11yField` `:5910` (12 Aufrufe, korrigiert) | info | CONFIRMED (Zählung korrigiert) | Prozess-Hinweis: #730 geschlossen, Kern-A11y-Punkte offen (siehe SR-D-09, SR-D-14, SR-D-12) | Folge-Issue anlegen oder #730 wieder öffnen | — |
| SR-D-07 | X1 · `docs/ui/admin-ui.html:7709-7721, 7726` | low | CONFIRMED | Admin-UI-Panel bietet kein `bind-host`/`allowed-hosts`/`token-file`; nur per YAML (keine Datenverluste beim Speichern) | optional Felder nach #896 ergänzen | S |
| SR-D-08 | X2 · `docs/ui/admin-ui.html:1018-1023`; 403-Body z. B. `admin-server.py:3484` | low | CONFIRMED | 403 zeigt rohes `origin not allowed: '…'` ohne Handlungshinweis | in 897-4: Toast um Hinweis auf `--allowed-hosts` ergänzen | S |

#### Accessibility (Ziel WCAG 2.2 AA)

| ID | Beleg | Schwere | Verdikt | Auswirkung | Empfehlung | Aufwand |
|---|---|---|---|---|---|---|
| SR-D-09 | A1 · `docs/ui/admin-ui.html:1631-1640`, Aktiv-Zustand `:1140-1142`, CSS `:122-126` · WCAG 2.1.1, 4.1.2 | **high** (blocker) | CONFIRMED | ~40 `div.nav-item` mit `onclick`, ohne `tabindex`/Rolle/Keydown → außer Dashboard keine Ansicht per Tastatur/Screenreader erreichbar; aktiver Eintrag nur farblich | natives `<a href="#/route">` (Router ist hash-basiert), `aria-current="page"` im Router-Loop, `🔒` als Text „(read-only)" | S |
| SR-D-10 | A2 · `admin-ui.html:743-752`, `showModal`/`hideModal` `:799-815`, Overlay `:834-836` · WCAG 4.1.2, 2.4.3, 1.3.1 | medium (major) | CONFIRMED | Modal ohne Dialog-Semantik, ohne Fokus-Setzen/-Rückgabe, ohne Escape und Fokus-Einschluss; betrifft alle `confirmDestructive`-Dialoge | natives `<dialog>` + `showModal()`/`close()`, `aria-labelledby`, Opener re-fokussieren, Fortschrittstext `role="status"` | S–M |
| SR-D-11 | A3 · `admin-ui.html:747, 1319, 2568, 2717, 2953, 3270, 3627, 4013, 4674, 5023, 6161, 8021, 8234, 8552, 10031` · WCAG 4.1.2, 2.4.6 | medium (major) | CONFIRMED | Icon-only-Buttons heißen „×"/„wastebasket"; ohne `title`: `:747, 2568, 2717, 2953, 8552` | `aria-label` („Close dialog", „Remove <item>"), Glyph in `aria-hidden`-Span | S |
| SR-D-12 | A4 · `labeledTextField` `:6093-6102`, `dropdownField` `:6120-6136`, `checkboxField` `:6139-6150`, `toggleField` `:1947-1954`, SchemaForm `:1233-1236`/`:1289-1297`, `numField` `:7685-7693`, Port `:7712-7718`, Token-Input `:875`; zusätzlich `:3819-3825` · WCAG 1.3.1, 4.1.2, 3.3.2 | medium (major) | CONFIRMED (Aufrufzahlen korrigiert: 13/17/30/3) | Labels nicht programmatisch verknüpft; Checkboxen ohne Namen | `a11yField` (`:5910`) in den alten Helfern wiederverwenden; Toggle per `aria-labelledby`; Token-Input mit Label | M |
| SR-D-13 | A5 · `admin-ui.html:298`, `:5234` · WCAG 2.4.7 | medium (major) | CONFIRMED | Fokus auf ~35 Toggle-Switches unsichtbar; `outline: none` auf `summary` | `.toggle input:focus-visible + .slider`-Outline; `outline: none` entfernen | S |
| SR-D-14 | A6 · `admin-ui.html:6684-6690`, `:6747-6752` · WCAG 2.1.1, 4.1.2 | low (orig. medium/major) | SEVERITY_ADJUSTED | Custom-Accordion ohne `aria-expanded`/Fokus; Default `expanded = true`, Inhalt also erreichbar, nur Zuklappen fehlt | natives `<details>/<summary>` wie an 10+ anderen Stellen | S |
| SR-D-15 | A7 · Rollen-Karten `admin-ui.html:2113, 2137-2142`; Template-Liste `:5074`; Env-Tabelle `:8545`; Rules-Matrix `:6352-6363` · WCAG 2.1.1, 4.1.2 | **high** (blocker) | CONFIRMED (Teilbefund Rules-Matrix blocker → minor, da per `/project/rules-overrides` erreichbar) | Rollen-Aktivierung (einziger Bedienweg), Template-Laden und Env-Bearbeitung nur per Mausklick. Nebenhinweise: aktiver Rollen-Zustand nur über Farbe (1.4.1 grenzwertig), Delegations-Canvas `:2150` ohne Textalternative (NEEDS_MORE_INFO), Shift-Drag `:2102` (2.5.7) ohne Persistenz | Rollen-Karte als `<button aria-pressed>` mit nicht-farbigem Indikator, Template-Zeile als `<button>`, Tabellenzeile mit Button/Link in erster Zelle | M |
| SR-D-16 | A8 · `#toast-container` `admin-ui.html:742`, `toast()` `:787-795`, `renderError` `:1145-1147` · WCAG 4.1.3 (2.2.1) | medium (major) | CONFIRMED | Toasts/Fehler ohne Live-Region, Fehler verschwinden nach 3,5 s; der geplante 403-Toast aus 897-4 bliebe für Screenreader stumm | Container `role="status" aria-live="polite"`, Fehler `role="alert"` und nicht automatisch entfernen; in 897-4 mitnehmen | S |
| SR-D-17 | A9 · `alert` `:8311, 8313, 8322, 8342, 9227`; `prompt` `:2995, 2997, 3217, 3568, 4620, 4745, 8334, 10348`; `confirm` `:1099` | — (orig. minor) | **VERWORFEN (False Positive)** | Verifier: native `alert/prompt/confirm` sind zugänglich und benennen den Fehler als Text, 3.3.1 ist erfüllt. Ohne verletztes Kriterium liegt kein Konformitätsbefund vor | als Konsistenz-/UX-Hinweis an `ui-ux-designer`; für 897-4 `alert` durch Toast ersetzen | (M) |
| SR-D-18 | A10 · `--text-muted` (`.muted :670`, `.field-help :251`, `.nav-group-title :103-110`, `:6689`), `.btn-danger :209`, `.token-prompt-msg :438` · WCAG 1.4.3 | medium (major) | CONFIRMED (Werte nachgerechnet) | Kontrast `--text-muted` 4,12 / 3,77 / 3,31 : 1 (primary/secondary/tertiary), `.btn-danger` in Panels 4,35 : 1, alles unter 4,5 : 1 | `--text-muted` z. B. `#8b949e` (5,62 : 1); Danger-Text `#ff7b72` (5,79 : 1) | S |
| SR-D-19 | A11 · `admin-ui.html:274-286`, `:299-306` · WCAG 1.4.11 | low (minor) | CONFIRMED | Input-Rahmen 1,53–1,55 : 1, Textfelder nur über Rahmen erkennbar | Rahmen ≥ 3 : 1 (z. B. `#6e7681`) | S |
| SR-D-20 | A12 · `admin-ui.html:66-70`, `:46-55`, `:130-134` · WCAG 1.4.10 | medium (major) | CONFIRMED (live zu bestätigen) | feste 240-px-Sidebar, `overflow: hidden`, keine Media-Query → bei 400 % Zoom ~80 px Inhalt | Media-Query < ~640 px: einspaltig, Sidebar oben/ausklappbar | S–M |
| SR-D-21 | A13 · Router `admin-ui.html:~1110-1143`, `<title>` `:6`, Landmarken `:731-738` · WCAG 2.4.1, 2.4.2, 2.4.3 | info (orig. low/minor) | SEVERITY_ADJUSTED (→ advisory) | kein SC verletzt: 2.4.1 über Landmarken, 2.4.2 über statischen Titel erfüllt; Fokus-/Titelführung pro View bleibt Best Practice (nach SR-D-09 ~40 Tab-Stopps) | Skip-Link, `document.title` pro View, `h1` nach Render fokussieren | S |
| SR-D-22 | A14 · Quick-Filter `admin-ui.html:9336-9347, 9571, 9611, 9859`; Tabs `:10329-10330` · WCAG 4.1.2 | low (minor) | CONFIRMED (1.4.1-Teil zurückgezogen) | Filter-/Tab-Zustand ohne `aria-pressed` | `aria-pressed` auf Filter- und Tab-Buttons | S |
| SR-D-23 | A15 · Token-Prompt-Overlay `admin-ui.html:869-905`, `:874-876` · WCAG 4.1.2, 3.3.1, 4.1.3 | medium (major) | CONFIRMED (präzisiert) | im Netzwerk-Modus erster Bildschirm: keine Dialog-Semantik, Input nur mit `placeholder`, Servermeldung „Invalid token" (`.token-prompt-msg`) und lokale Fehlermeldung ohne Live-Region/`aria-describedby`; Escape nur bei Fokus im Input | `<dialog>` wie SR-D-10, Label, Fehler-Element `role="alert"` + `aria-describedby` | S |

### 4.e Dimension (e) — config/, Schemas, tests/, CI

| ID | Beleg | Schwere | Verdikt | Auswirkung | Empfehlung | Aufwand |
|---|---|---|---|---|---|---|
| SR-E-01 | E-CI-1 · `.github/workflows/orchestration-test.yml:28-49`, `validate.yml:24-35`; `tests/requirements.txt` | medium | CONFIRMED | kein `timeout-minutes`, kein `pytest-timeout`; ein hängender Hook verbrennt bis zu 360 min je Matrix-Leg (reale Legs 12:40–14:50 min) | `timeout-minutes: 20` pro Job | S |
| SR-E-02 | E-CI-2 · `orchestration-test.yml:51-52`, `validate.yml:33-34` | low | CONFIRMED | `sync.py --validate` läuft bis zu 4x pro Push (nur bei geänderten Pfaden, da path-gefiltert) | `--validate` nur in validate.yml oder einem Matrix-Leg | S |
| SR-E-03 | E-CI-3 · `validate.yml:35-39` | low | CONFIRMED | veralteter Kommentar „Drift-Gate rot bis #739 Defekt 4"; CI ist grün | Kommentar entfernen | XS |
| SR-E-04 | E-CI-4 · `validate.yml:18, 29`; `orchestration-test.yml:44` | low | CONFIRMED | kein pip-Cache; `validate.yml` installiert ungepinntes `pyyaml` | `cache: pip`, Pinning über `tests/requirements.txt` | XS |
| SR-E-05 | E-CI-5 · `orchestration-test.yml:1-24` vs. `validate.yml` | medium (Low/Medium) | CONFIRMED | Scenario-Suite und Drift-Gate nur auf py3.11, obwohl 3.9 unterstützt wird (wiederkehrende Py3.9-Bugklasse) | 3.9-Leg für `scenarios` | S |
| SR-E-06 | E-CI-6 · `tests/browser/*`; `tests/requirements.txt` | low | CONFIRMED | Playwright-Tests laufen nie in CI (`importorskip`), Admin-UI-Regressionen nur lokal entdeckt; Trade-off undokumentiert | separater Opt-in-/Nightly-Job oder Dokumentation | M |
| SR-E-07 | E-CFG-1 · `config/project-config.schema.json` (root `additionalProperties: true`); Konsumenten u. a. `rules.py:94`, `cli_commands.py:122,130`, `deactivation.py:50`, `roles.py:491`, `admin-server.py:5310, 5359` | medium | CONFIRMED | 9 im eigenen `project.yaml` genutzte Top-Level-Keys (u. a. `rules-preset`, `test-repo`, `provider-deactivation`, `environments`, `backup`) plus `tier-presets` und `submodule-protection` (zwei Schreibweisen) fehlen im Schema; Tippfehler wie `rule-preset` bleiben unentdeckt, Admin-UI-Schemaeditor kennt die Keys nicht | Keys deklarieren; danach Warnung bei unbekannten Top-Level-Keys statt sofort `additionalProperties: false` | M |
| SR-E-08 | E-CFG-2 · `scripts/lib/config.py:196-201` (`_KNOWN_NON_OBJECT_KEYS`); `sync_pipeline.py:166` | low | CONFIRMED | Folge von SR-E-07: `rules-preset: null` wird zu `{}`; Log zeigt `preset '{}'`, künftige Konsumenten ohne `or`-Fallback erhalten ein Dict | `rules-preset` ins Schema oder in `_KNOWN_NON_OBJECT_KEYS` | XS |
| SR-E-09 | E-CFG-3 · `templates/configs/project.yaml.example:40`, `agent-meta.config.example.yaml:39`, `agent-meta.config.example.json:39`; Test `tests/test_config_audit.py:420-432` | low | CONFIRMED | Onboarding-Templates enthalten nicht existierende Rolle `feature` → Schema- und Unknown-Role-Warnung; nur die howto-Kopie ist testgesichert | Zeile entfernen, Schema-Test über alle Templates parametrisieren | XS |
| SR-E-10 | E-CFG-4 · `config/tier-presets.yaml` (`:47, 55, 63`); `scripts/lib/roles.py:28-29, 500-545`; `delegation_syntax.py:385` | medium | CONFIRMED (Teilaussage `ultra` falsch) | Presets Cheap/Advanced/Expensive/„Expensive as Hell" wirken nur für Claude/Gemini/Opencode; bei 6 Providern stiller No-op, Continue/Copilot fallen auf Claude-Modell-IDs zurück. `ultra` ist im Normal-Preset definiert, wird also nur bei anderen Presets/Providern abgelehnt | Warnung, wenn das aktive Preset keinen Eintrag für einen aktiven Provider hat, oder Einschränkung dokumentieren; `ultra`-Teil des Fixes eingrenzen | S |
| SR-E-11 | E-CFG-5 · `config/ai-providers.yaml:270` (`runtime_gate-mechanism`), `planning_mode_hint`; `config/provider-capabilities.yaml` (`handoff_envelope_support`, `structured_handoff`, `text_mentions`, `special_notes`, Header l.3) | low | CONFIRMED | 8 Registry-Keys ohne Leser in Scripts/Hooks, sehen aber wie Vertragsdaten aus | als `# doc-only` kommentieren oder löschen | S |
| SR-E-12 | E-T-1 · `orchestration-test.yml:47-48`; `.gitignore:13, 16`; z. B. `tests/test_opencode_agents.py:178-182`, `test_legacy_registries_removed.py:68`, `test_reference_standards_documented.py:66`, `test_mcp_role_tools.py:144-145` | medium | CONFIRMED (genaue Skip-Zuordnung offen) | pytest läuft vor jeder Sync auf frischem Checkout → Tests generierter Artefakte skippen in CI (19 Skips je Leg, davon ~10 Browser) und sind nur scheinbar grün | `python scripts/sync.py` vor pytest auf einem Matrix-Leg | S |
| SR-E-13 | E-T-2 · `tests/test_orchestrator_guard_hook.py:70-77, 89, 125, 141, 152`; `.meta-config/project.yaml:311`; `orchestrator-guard-impl.sh:249` | medium | CONFIRMED (Zählung korrigiert: 246 statt 123) | Tests hängen am realen Repo (`orchestrator.strict: true`) und schreiben in das lokale `.claude/hooks/.guard-audit.log`: 246 von 1605 Zeilen (~15 %) sind Testrauschen. Die Datei ist nicht git-getrackt, es gibt also keinen Repo-Impact. Bereinigung wurde vom Verifier bewusst nicht vorgenommen | tmp-Projekt-Fixture mit eigener `project.yaml` wie bereits l.470/704; Audit-Log danach einmalig bereinigen (schreibberechtigte Rolle oder Nutzer) | S |
| SR-E-14 | E-T-3 · 74–75 `subprocess.run`/`check_output` ohne `timeout=` in 24–25 Testdateien; risikoreich `test_orchestrator_guard_hook.py` (8), `test_dod_push_check_hook.py` (5), `test_repo_containment_hook.py` (3), `test_graphify_guard_hooks.py` (3), `test_secrets_and_isolation.py` (3) | low | CONFIRMED | Hänger in Hook-Tests blockieren den Lauf (CI-Seite über SR-E-01) | `timeout=30` in den ~6 `_run_hook`-Helpern | XS |
| SR-E-15 | E-T-4 · 157 Dateien mit `sys.path.insert`; 4 mischen `lib.*`/`scripts.lib.*` (`test_se_validate.py`, `test_context_compact_mode.py`, `test_generated_file_drift_pipeline_wiring.py`, `test_knowledge_engine.py`); Workarounds `test_file_affinity.py:28-45`, `test_orchestration_contract.py:30-50` | medium (Low/Medium) | CONFIRMED | doppelte Modulkopien (`lib.roles is scripts.lib.roles` → False): getrennte Caches/Globals, `monkeypatch` wirkt nur auf eine Kopie, Reihenfolgeabhängigkeit | eine Import-Wurzel, einmal in `conftest.py` setzen, per-file `sys.path.insert` entfernen | M |
| SR-E-16 | E-T-5 · `tests/test_artifact_freshness_hook.py:118, 178, 202`; `tests/test_barrier_runtime.py:77, 100` | low | CONFIRMED | 3x `sleep(1.1)` (~3,3 s pro Leg); knappe Wall-Clock-Margen → Flake-Risiko auf belasteten Runnern | `GIT_COMMITTER_DATE`/`GIT_AUTHOR_DATE`; Margen erhöhen | S |
| SR-E-17 | E-T-6 · `tests/test_backup_robustness.py:160-161`; `tests/test_exception_specificity.py:195-197` | low | CONFIRMED | Quelltext-Assertions brechen bei harmlosen Refactors bzw. sind nahezu immer grün | AST-Check auf Zielfunktion oder Verhaltenstest | S |
| SR-E-18 | E-T-7 · `tests/test_release_scaffold.py` vs. `scripts/lib/release_scaffold.py:63-95` (#452) | low | CONFIRMED | ungetestet: `release` als Nicht-Mapping (AttributeError), `dry_run=True`, Datei ohne Managed-Marker, fehlende Warnungs-Assertion, unvalidiertes `distribution` im Template-Pfad | Negativtests ergänzen | S |
| SR-E-19 | E-T-8 · `tests/test_gitignore_keep.py` vs. `scripts/lib/gitignore.py:126-180` (#746) | low | CONFIRMED | `./.claude/3-project/` und `/.claude/3-project/` werden still verworfen; `..`-Segmente landen wörtlich in `.gitignore` | Keep-Pfade normalisieren, `..` ablehnen, 3 parametrisierte Fälle | S |
| SR-E-20 | E-T-9 · `tests/test_recommended_skills_registry.py:18, 27-54` (#680) | low | CONFIRMED | `provider:<x>` nicht gegen Registry geprüft, kein Duplikat-Check, Magic Count `>= 10` | Registry-Abgleich + Duplikat-Check | XS |
| SR-E-21 | E-T-10 · `scripts/lib/agents.py:284`; `delegation_table.py:172`; `config.py:181ff`; `tests/test_routing_tool_definitions.py:226-282` (#780) | low | CONFIRMED (Werte korrigiert: `Deutsch`/`Englisch`) | Produktionsverdrahtung `language=COMMUNICATION_LANGUAGE` ungetestet (überlebende Mutation); Default `"en"` matcht nie und landet immer im Fallback | ein Test via `build_routing_tool_definition` mit `COMMUNICATION_LANGUAGE="Deutsch"` | XS |
| SR-E-22 | E-T-11 · `@lru_cache` in `roles.py:34, 52`, `frontmatter.py:515`, `pipelines.py:76, 153` u. a. | low | CONFIRMED (latent) | gecachte, geteilte mutable Rückgabewerte; „Caller mutieren nie" nur per Kommentar → Reihenfolgeabhängigkeit bei einer einzigen In-place-Mutation | `MappingProxyType`/deepcopy oder Test, der Unveränderlichkeit erzwingt | S |
| SR-E-23 | E-T-12 · `tests/test_config_audit.py:554`; 9x `pytest.raises(SystemExit)` ohne Exit-Code; 5 Dateien `exec`en `admin-server.py`, 3 überschreiben `sys.modules["admin_server"]` | low | SEVERITY_ADJUSTED (nur Scope reduziert, orig. 8 Dateien) | schwache Assertions, mehrfache Klassenkopien und Setup-Kosten | `FrozenInstanceError`, Exit-Code prüfen, Admin-Server-Modul einmal laden | XS–S |
| SR-E-24 | E-T-13 · `scripts/lib/cli_commands.py:113, 178`; einziger Treffer Kommentar `tests/test_platform_hacs_preset.py:28` | low | CONFIRMED | `resolve_test_repo_path`/`validate_test_repo` ohne Test → Drift von SR-A-24/SR-A-25 ohne Regressionsnetz | Tests zusammen mit SR-A-24/25 | — |

---

## 5. Nicht geprüft / Grenzen

**Querschnitt:**
- Kein axe-core- oder Lighthouse-Lauf gegen die Admin-UI.
- Kein manueller Tastatur- und Screenreader-Test (NVDA, JAWS, VoiceOver). Befunde mit dem Vermerk „live zu bestätigen" (SR-D-10, -11, -13, -16, -20, -21, -23) sind vor Fix-Abschluss manuell zu prüfen.
- Kein Volllauf der pytest-Suite: nur statische Analyse, gezielte Einzeltests, Python-Einzeiler und Hook-Treiber gegen Scratch-Kopien.
- Kein Browser-/E2E-Lauf in CI (Playwright-Tests skippen dort, siehe SR-E-06).
- Kein laufender Admin-Server. SR-D-01 wurde gegen die echte `lib.backup.delete_backup` mit nachgebildeter Routing-Logik reproduziert, nicht über HTTP.

**Dimension (a)** (laut eigener Zusammenfassung, aus Budgetgründen): `agent_sync.py`, `provider_transform.py`, `mcp*.py`, `hooks.py`, Interna von `pipelines.py` und der Großteil des Managed-Block-Renderings in `context.py` sind nicht abgedeckt. `agents.py` wurde geprüft und ist ohne Befund. Der AST-Scan nach Provider-Literalen war laut Verifier nicht erschöpfend (Ergänzungen bei SR-A-12 und SR-A-21).

**Dimension (b):** Die dokumentierten Grenzen in `branch-guard.md` (#592 Indirektion, #809 FS-Destructive) und der #753-Fix sind ausgeschlossen. SR-B-02 wurde nur getraced, nicht ausgeführt, weil kein Feature-Branch-Scratch-Repo angelegt werden konnte. Die AGY-Laufzeitsemantik (SR-B-26) ist nicht verifiziert.

**Dimension (c):** Die Prüfung ist stichprobenbasiert: 7 Templates (junior-developer, developer, senior-developer, orchestrator, planner, code-reviewer, concept-reviewer), die Reviewer-Flotte per grep, alle `rules/1-generic` per grep, `rules/2-platform` und `.claude/skills` als Stichprobe. Ausgeschlossen sind #769–#780, #844, #679 und #552/#528. Die ESCALATE-Blöcke in `se-developer`/`se-junior-developer` wurden nicht geprüft.

**Dimension (d):** Der Security-Verifier hat nur N1–N6 und X1–X2 geprüft, der A11y-Verifier nur A1–A15. Die Plan-Bestätigungen D1–D6, U1 und U2 wurden von keinem Verifier erneut geprüft. Offen sind außerdem die Textalternative des Delegations-Canvas (`admin-ui.html:2150`, NEEDS_MORE_INFO) und die manifestgesteuerten Schreib-/`rmtree`-Pfade in `restore_backup` (`backup.py:542-543, 576-579`). Letztere stuft der Verifier als eigenes Follow-up mit Schwere medium ein, ohne eigene ID.

**Dimension (e):** Ausgeschlossen sind der #452-Release-Block, das #746-Keep-Array, die #751-Capability-Flags, die Schema-Ergänzungen aus #680 selbst und der bekannte Flake `test_local_process_partial_line_timeout`. Area 2 (config/Schemas) ist ein Spot-Check und nicht erschöpfend. Area 3 (tests) besteht aus statischer Analyse über 265 Testdateien mit 3764 gesammelten Tests und gezielten Mikro-Checks, ohne Volllauf. Bei SR-E-12 ist die genaue Zuordnung der Skips nicht geprüft (Lauf ohne `-rs`). Ob Continue/Copilot überhaupt `model:` ausgeben (SR-E-10), ist nicht verifiziert.

---

## 6. Issue-Entwürfe

> Nur Entwürfe, es wurde kein Issue angelegt. Labels sind Vorschläge und müssen gegen die vorhandenen Repo-Labels abgeglichen werden.

| # | Titel (Entwurf) | Befunde | Vorgeschlagene Labels |
|---|---|---|---|
| 1 | `fix(admin-server): reject non-bare archive names in backup delete/restore handlers` | SR-D-01 | `security`, `bug`, `admin-ui`, `priority:high` |
| 2 | `fix(backup): validate manifest-driven write and rmtree paths in restore_backup` | Follow-up aus SR-D-01 (ohne eigene ID) | `security`, `bug`, `backup` |
| 3 | `fix(admin-server): enforce body limit, security headers and failure signalling` | SR-D-02, SR-D-03, SR-D-05, SR-D-08 | `security`, `admin-ui`, `bug` |
| 4 | `fix(admin-ui): keyboard access for navigation, role cards, template list and env table (reopen #730)` | SR-D-09, SR-D-15, SR-D-06 | `accessibility`, `admin-ui`, `priority:high` |
| 5 | `fix(admin-ui): dialog semantics, labels, focus visibility, live regions, contrast and reflow` | SR-D-10, -11, -12, -13, -16, -18, -20, -23 (SR-D-16 in 897-4 mitnehmen) | `accessibility`, `admin-ui` |
| 6 | `fix(hooks): close dod-push-check branch-guard bypasses (--tags, refspec, global opts, SIGPIPE)` | SR-B-01, -02, -03, -04, -21, -05, -07 | `security`, `hooks`, `bug`, `priority:high` |
| 7 | `fix(hooks): make orchestrator-guard strict mode and wrappers fail closed` | SR-B-10, -11, -08, -17, -15, -09, -20, -33 | `security`, `hooks`, `bug` |
| 8 | `fix(hooks): extend destructive and mutation git gates` | SR-B-12, -13, -14 | `security`, `hooks` |
| 9 | `fix(hooks): repo-containment heredoc false positives and missed in-place flags` | SR-B-16, -19, -18 (+ Detektor-Fail-open `:492`) | `hooks`, `bug` |
| 10 | `fix(sync): gitignore env/personal files for non-Claude providers` | SR-A-11, SR-A-31, SR-A-12, SR-A-33, SR-A-14 | `bug`, `security`, `provider-agnostic` |
| 11 | `fix(io): preserve file mode in write_atomic` | SR-A-15, SR-B-32 | `bug` |
| 12 | `fix(validate): count current-run errors and reuse production sync stages` | SR-A-24, SR-A-25, SR-A-04, SR-E-24 | `bug`, `testing` |
| 13 | `refactor(guard): detect provider literals in call args, dict keys and defaults` | SR-A-06, SR-A-12, SR-A-13, SR-A-21 | `refactor`, `provider-agnostic` |
| 14 | `fix(agents): repo-local, provider-neutral long-report path for reviewer fleet` | SR-C-01, SR-C-05 | `agents`, `bug`, `provider-agnostic` |
| 15 | `fix(agents): unify ESCALATE card schema across developer tiers` | SR-C-06, SR-C-07 (ein gemeinsames Snippet behebt beide) | `agents`, `orchestration` |
| 16 | `chore(agents): re-centralize inlined snippets and refresh stale based-on pins` | SR-C-02, SR-C-03, SR-C-09, SR-C-10 | `agents`, `chore` |
| 17 | `chore(rules): trim a2a-delegation-gates maintainer prose` | SR-C-13, SR-C-14, SR-C-15 | `rules`, `token-budget` |
| 18 | `ci: add job timeouts, run sync before pytest, isolate guard tests` | SR-E-01, SR-E-14, SR-E-12, SR-E-13 | `ci`, `testing` |
| 19 | `fix(schema): declare undeclared top-level config keys` | SR-E-07, SR-E-08, SR-E-09 | `config`, `schema` |
| 20 | `fix(roles): warn when tier preset has no entry for an active provider` | SR-E-10 | `config`, `bug` |
| 21 | `fix(config): shared null-safe block reader for nested config nulls` | SR-A-28, SR-A-07, SR-A-08, SR-A-22 | `bug`, `config` |

**Empfohlene Reihenfolge:** 1 → 4 → 6 → 10 → 11 → 12 → 7 → 5 → 3. Den Rest nach Kapazität. Issue 1 ist Voraussetzung für #896.

---

## 7. Umsetzungsstatus

> Wird während der Umsetzungs-Waves gepflegt. Ausgangszustand: alle Befunde offen.

| Finding-ID | PR | Status |
|---|---|---|
| SR-A-01 | — | offen |
| SR-A-02 | — | offen |
| SR-A-03 | — | offen |
| SR-A-04 | — | offen |
| SR-A-05 | — | offen |
| SR-A-06 | — | offen |
| SR-A-07 | — | offen |
| SR-A-08 | — | offen |
| SR-A-09 | — | offen |
| SR-A-10 | — | offen |
| SR-A-11 | — | offen |
| SR-A-12 | — | offen |
| SR-A-13 | — | offen |
| SR-A-14 | — | offen |
| SR-A-15 | — | offen |
| SR-A-16 | — | offen |
| SR-A-17 | — | offen |
| SR-A-18 | — | offen |
| SR-A-19 | — | offen |
| SR-A-20 | — | offen |
| SR-A-21 | — | offen |
| SR-A-22 | — | offen |
| SR-A-23 | — | offen |
| SR-A-24 | — | offen |
| SR-A-25 | — | offen |
| SR-A-26 | — | offen |
| SR-A-27 | — | offen |
| SR-A-28 | — | offen |
| SR-A-29 | — | offen |
| SR-A-30 | — | offen |
| SR-A-31 | — | offen |
| SR-A-32 | — | offen |
| SR-A-33 | — | offen |
| SR-A-34 | — | offen |
| SR-A-35 | — | offen |
| SR-A-36 | — | offen |
| SR-A-37 | — | offen |
| SR-A-38 | — | offen |
| SR-A-39 | — | offen |
| SR-A-40 | — | offen |
| SR-A-41 | — | offen |
| SR-B-01 | — | offen |
| SR-B-02 | — | offen |
| SR-B-03 | — | offen |
| SR-B-04 | — | offen |
| SR-B-05 | — | offen |
| SR-B-06 | — | offen |
| SR-B-07 | — | offen |
| SR-B-08 | — | offen |
| SR-B-09 | — | offen |
| SR-B-10 | — | offen |
| SR-B-11 | — | offen |
| SR-B-12 | — | offen |
| SR-B-13 | — | offen |
| SR-B-14 | — | offen |
| SR-B-15 | — | offen |
| SR-B-16 | — | offen |
| SR-B-17 | — | offen |
| SR-B-18 | — | offen |
| SR-B-19 | — | offen |
| SR-B-20 | — | offen |
| SR-B-21 | — | offen |
| SR-B-22 | — | offen |
| SR-B-23 | — | offen |
| SR-B-24 | — | offen |
| SR-B-25 | — | offen |
| SR-B-26 | — | offen |
| SR-B-27 | — | offen |
| SR-B-28 | — | offen |
| SR-B-29 | — | offen |
| SR-B-30 | — | offen |
| SR-B-31 | — | offen |
| SR-B-32 | — | offen |
| SR-B-33 | — | offen |
| SR-C-01 | — | offen |
| SR-C-02 | — | offen |
| SR-C-03 | — | offen |
| SR-C-04 | — | offen |
| SR-C-05 | — | offen |
| SR-C-06 | — | offen |
| SR-C-07 | — | offen |
| SR-C-08 | — | offen |
| SR-C-09 | — | offen |
| SR-C-10 | — | offen |
| SR-C-11 | — | offen |
| SR-C-12 | — | offen |
| SR-C-13 | — | offen |
| SR-C-14 | — | offen |
| SR-C-15 | — | offen |
| SR-C-16 | — | offen |
| SR-C-17 | — | offen |
| SR-C-18 | — | offen |
| SR-D-01 | — | offen |
| SR-D-02 | — | offen |
| SR-D-03 | — | offen |
| SR-D-04 | — | offen |
| SR-D-05 | — | offen |
| SR-D-06 | — | offen |
| SR-D-07 | — | offen |
| SR-D-08 | — | offen |
| SR-D-09 | — | offen |
| SR-D-10 | — | offen |
| SR-D-11 | — | offen |
| SR-D-12 | — | offen |
| SR-D-13 | — | offen |
| SR-D-14 | — | offen |
| SR-D-15 | — | offen |
| SR-D-16 | — | offen |
| SR-D-17 | — | offen |
| SR-D-18 | — | offen |
| SR-D-19 | — | offen |
| SR-D-20 | — | offen |
| SR-D-21 | — | offen |
| SR-D-22 | — | offen |
| SR-D-23 | — | offen |
| SR-E-01 | — | offen |
| SR-E-02 | — | offen |
| SR-E-03 | — | offen |
| SR-E-04 | — | offen |
| SR-E-05 | — | offen |
| SR-E-06 | — | offen |
| SR-E-07 | — | offen |
| SR-E-08 | — | offen |
| SR-E-09 | — | offen |
| SR-E-10 | — | offen |
| SR-E-11 | — | offen |
| SR-E-12 | — | offen |
| SR-E-13 | — | offen |
| SR-E-14 | — | offen |
| SR-E-15 | — | offen |
| SR-E-16 | — | offen |
| SR-E-17 | — | offen |
| SR-E-18 | — | offen |
| SR-E-19 | — | offen |
| SR-E-20 | — | offen |
| SR-E-21 | — | offen |
| SR-E-22 | — | offen |
| SR-E-23 | — | offen |
| SR-E-24 | — | offen |

---

*Erstellt 2026-10-08 vom documenter-Agenten (claude-opus-5-5) als Synthese der fünf Dimensionsberichte und ihrer Verifier-Pässe; inhaltlich kein eigener Neu-Review.*
