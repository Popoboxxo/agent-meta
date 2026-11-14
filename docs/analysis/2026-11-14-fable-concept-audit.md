# Grobe Konzeptprüfung agent-meta — 2026-11-14

- **Status:** Analyse (kein Beschluss)
- **Datum:** 2026-11-14
- **Quelle:** Fable-Grobaudit, nicht gegen Code vollständig verifiziert
- **Issues:** #1237–#1276 (Audit-Folgeissues), #1276 (Folge-Audit)
- **Zugehörige Berichte:** docs/analysis/2026-11-14-fable-concept-audit.md, docs/analysis/2026-11-14-fable-provider-hooks-audit.md, docs/analysis/2026-11-14-fable-viz-extensions-audit.md, docs/analysis/2026-11-14-audit-prioritization.md

- Stand: `origin/main` = `3dc03f95` (Haupt-Checkout `chore/main-checkout-parking` unverändert, read-only)
- Methode: `graphify query/explain` → gezielte Reads (offset/limit) → Belege als `Datei:Zeile`
- Fokus: Konzept/Mechanik, nicht Prompt-Texte, nicht Doku-Prosa
- Aufwand-Skala: S (<1 Tag), M (1–3 Tage), L (>3 Tage / mehrere PRs)
- Frühere Grobaudits (nur Kopfzeilen referenziert): `docs/analysis/276-architecture-robustness-audit.md`, `docs/analysis/402-systemaudit-kernziele.md`, `docs/analysis/2026-09-30-provider-audit-*.md`, `docs/analysis/2026-10-11-context-budget-provider-study.md`

## 0. Größenordnung (Kontext für alle Bereiche)

| Messgröße | Wert | Beleg |
|---|---|---|
| `scripts/lib/*.py` | 112 Module, ~56.8k Zeilen | `wc -l scripts/lib/*.py` |
| Größte Module | `context.py` 3838, `config.py` 2907, `meta_optimizer.py` 2365, `isolation.py` 2237, `sync_pipeline.py` 2114 | dito |
| Hooks (Shell) | ~7.0k Zeilen; `dod-push-check.sh` 1628, `orchestrator-guard-impl.sh` 1549, `repo-containment-impl.sh` 1328, `lib/hook_common.sh` 1178 | `wc -l hooks/**` |
| Tests | 468 Dateien unter `tests/` | `ls tests` |
| Provider | 9 (`Claude, Opencode, Gemini, Continue, Copilot, Mammouth, Codex, ZCode, KimiCode`) | `config/ai-providers.yaml`, `config/provider-capabilities.yaml` |
| Agent-Templates | 120 Dateien unter `agents/` (0-external/1-generic/2-platform) | `find agents -type f` |
| Commit-Takt | 697 Commits in 90 Tagen; davon `hooks/` 46, `sync_pipeline.py` 49 | `git log --since=90.days` |

---

## 1. Schichtenmodell & Syncer-Pipeline

### Stärken
- Komposition an einer Stelle: Base + Override-Patches + Frontmatter-Merge (`scripts/lib/agent_sync.py:423-456`), Patches deklarativ (`apply_patch`, `agent_sync.py:402`).
- Pipeline als benannte Stages, Reihenfolge an genau einer Stelle (`scripts/lib/cli_commands.py:1582-1676`).
- Extensions = Managed-Block + freier Teil (`scripts/lib/extensions.py:51,90,147`) → Projektwissen überlebt Re-Sync.
- Transform-Regeln als Daten, kein if/elif (`scripts/lib/provider_transform.py:7-8, 828-840`).

### Schwächen / Risiken
| Befund | Evidenz |
|---|---|
| Monolith-Funktionen: `_sync_stage_per_provider` 348 Z., `_apply_agent_transform` 469 Z., `_finalize_agent_content` 151 Z. | `sync_pipeline.py:1394-1742`, `provider_transform.py:331-800`, `agent_sync.py:1033-1184` |
| Stage-Kopplung über Objekt-Referenzen: Stage 3 gibt Listen zurück, die Stage 11 mutiert | `sync_pipeline.py:316-320` |
| Stage trägt Provider-Namen trotz Capability-Gate (`_sync_stage_claude_base`, `is_claude`) | `sync_pipeline.py:311, 322-326, 340` |
| Stille Degradation: ohne PyYAML wird Override unkomponiert geliefert — Warnung statt Abbruch | `agent_sync.py:432-437` |
| `sync_pipeline.py` importiert 36 lib-Module → zentraler Kopplungspunkt, 49 Commits/90 Tage | `sync_pipeline.py:38-154` |
| Einmal-Migrationslogik als Dauerlast in der Pipeline (discovery-/provider-path-Migrationen, legacy cleanup, converge) | `sync_pipeline.py:385-733, 890-975` |
| Zwei Konfig-Wahrheiten für Provider: `ai-providers.yaml` (29–46 Keys/Provider, heterogen) ohne JSON-Schema (`schemas/` enthält nur a2a/se) | `ls schemas`; YAML-Key-Zählung |

### Single-Points-of-Failure
- PyYAML (ADR-0001) — Ausfall ist weich, nicht hart (s.o.).
- `_handle_sync` als einziger Sequenzer (`cli_commands.py:1568`).
- `.meta-config/generated-file-hashes.json` als persistenter Pipeline-Zustand (s. §4).

### Empfehlung
- PyYAML-Fehlen → harter Fehler (S).
- Migrations-Stages hinter Versions-Gate kapseln bzw. nach Deprecation entfernen (M).
- `_sync_stage_per_provider` in Sub-Stages mit explizitem Kontext-Objekt statt Referenz-Mutation (M).

---

## 2. Provider-Agnostik

### Stärken
- Credo hält auf Namensebene: alle 9 Treffer für `provider ==` in `scripts/lib` sind Kommentare/Docstrings, kein Code-Branch (`grep -rnE "provider\s*(==|!=)"`).
- Capability-Gates statt Namen: `has_dedicated_context_file` (`sync_pipeline.py:322-326`), `hook-agent-id` (`hooks/1-generic/orchestrator-guard-impl.sh:352-360`), `agent-transform`-Block mit explizitem Log bei Fehlen (`provider_transform.py:834-837`).
- Schema-Enums werden aus der Registry generiert (`scripts/lib/schema.py:130-137`).

### Schwächen / Risiken
| Befund | Evidenz |
|---|---|
| Dispatch verschoben, nicht beseitigt: provider-benannte Mechanismen-Strings `opencode-native(-v2)`, Spec-Key `strip-claude-lines` | `provider_transform.py:459, 525, 608, 638, 779` |
| Provider-spezifische Funktionen/Module: `_transform_frontmatter_for_opencode[_v2]`, `_map_claude_tools_to_opencode_permissions`, `_strip_claude_specific_lines`; `opencode_v2_config.py` (1379 Z.); 19 providerbenannte Format-Tags in `mcp_provider_config.py` | `provider_transform.py:885-1368`; `grep -c kimi-json\|opencode-json…` |
| Zwei Capability-Vokabulare: `ai-providers.yaml#capabilities` (Liste, 4–17 Einträge) vs. `provider-capabilities.yaml` (41–43 Keys je Provider) | YAML-Zählung beider Dateien |
| Hartkodierte Provider-Listen im Code | `pipelines.py:56-57`, `external_tools_drift.py:187-189`; Drift bereits dokumentiert `schema.py:136` |
| `provider="Claude"` als Default in ≥9 Signaturen → Claude = impliziter Nullpunkt | `agent_sync.py:182`, `hooks.py:465`, `context.py:655,2085`, `roles.py:355,385`, `rules.py:605`, `hook_plugins.py:34,266` |
| Hook-Verlässlichkeit nur Claude (`hook-agent-id`); Isolation je Provider eigener Mechanismus, Continue nur "soft rule" | `ai-providers.yaml:64`, `isolation.py:7-11` |
| Tests enumerieren alle Provider in 34 Dateien | `grep -rl KimiCode tests/*.py` |

### Aufwand "weiterer Provider" (konkrete Reibungsstellen)
1. `ai-providers.yaml`-Eintrag (~30–46 Keys, keine Schema-Hilfe) + `provider-capabilities.yaml` (~42 Keys).
2. `agent-transform:`-Block; bei abweichendem Frontmatter neue Mechanismus-Strings in `provider_transform.py`.
3. MCP-Format in `mcp_provider_config.py`, Isolation in `isolation.py`, ggf. Hook-Protokoll in `hooks.py`.
4. Hartkodierte Listen (`pipelines.py:56`, `external_tools_drift.py:187`).
5. 34 Testdateien + `test_context_budgets._PROVIDERS`-Assert (`tests/test_context_budgets.py:358`) + AC-01-Baseline + Ceilings.
- Schätzung: M für Minimal-Provider (Agents+Context), L mit Hooks/MCP/Isolation.

### Empfehlung
- JSON-Schema für Provider-Einträge + Zusammenführung der zwei Capability-Quellen (M).
- Provider-Fixture/Parametrisierung zentral statt 34 Enumerationen (M).
- Mechanismen generisch benennen (`native-json-v2` statt `opencode-native-v2`) — kosmetisch, aber hält das Credo ehrlich (S).

---

## 3. Hooks / Guards

### Stärken
- Fail-closed-Disziplin explizit und begründet (`orchestrator-guard-impl.sh:19-40`; `dod-push-check.sh:100-116`).
- Bekannte Lücken im Code und in Rules dokumentiert (`orchestrator-guard-impl.sh:118-141`; `.claude/rules/branch-guard.md`).
- Sentinel-Elevation capability-scoped + Audit-Log; Sentinel verworfen, wenn Harness `agent_id` liefert (`orchestrator-guard-impl.sh:73-86, 352-366`).
- Ein gemeinsamer Tokenizer für Mutations- und Destructive-Gate (`orchestrator-guard-impl.sh:91-95`).

### Schwächen / Risiken
| Befund | Evidenz |
|---|---|
| Python in Bash-Heredocs: 447 Zeilen Python in einer Shell-Funktion; weitere Heredocs (dod-push 2, containment 3) → nicht als Modul testbar/lintbar, Quoting-Risiko | `hooks/1-generic/lib/hook_common.sh:474-921` (`hook_shell_scan_py`), `:1140-1178` |
| Zwei Python-Auflösungen: dod-push hardcodiert `python3`, hook_common erlaubt `python`/`python3` → zwei Fail-Modi | `dod-push-check.sh:106-116`, `hook_common.sh:33-62` |
| Begriff "Security boundary" überdehnt: Identität unverifizierbar, Tokenizer kein Parser, `eval`/`bash -c` strukturell blind | `orchestrator-guard-impl.sh:87-89, 122-130`; `branch-guard.md` ("Security-Eigenschaften nur für Destructive-Gate und DoD-Push-Check") |
| Sentinel = Self-Report in erster Zeile; Vorfall #516 belegt Missbrauch; auf Providern ohne `agent_id` einziges Delegaten-Signal | `agents/1-generic/git.md:31-35`, `orchestrator-guard-impl.sh:73-75, 357-359` |
| Churn/Regressionsfläche: 46 Hook-Commits/90 Tage, je 15 an orchestrator-guard und dod-push; Versionszeilen mit >300-Zeichen-Changelog | `git log --since=90.days -- hooks`; `dod-push-check.sh:3,9` |
| Hooks nur auf Claude verdrahtet; 8 Provider nur Prompt-Konvention | `.claude/settings.json` (5 PreToolUse-Hooks); `.claude/rules/repo-containment.md` |
| Hook-Tests: 29 Dateien, 18 via `subprocess` → langsam, abhängig von bash/python3/realpath | `grep -l subprocess tests/test_*guard*…` |

### Empfehlung
- Python-Kern aus Heredocs nach `hooks/1-generic/lib/*.py`; Shell nur noch Shim (M; größter Wartbarkeitshebel).
- "Security boundary" entweder mit Threat-Model pro Gate belegen oder durchgängig "Convention boundary" (S).
- Eine Python-Resolution für alle Hooks (S).

---

## 4. Drift / Hash / Golden / AC-01

### Stärken
- Drift-Erkennung sichert Nutzer-Edits per Backup vor dem Überschreiben (`scripts/lib/generated_file_drift.py:521-585`).
- AC-01 als Render-Identitätsvertrag, Ausnahmen als Daten, Host-lokale Pfade ausgeschlossen (`tests/test_ac01_render_identity.py:13-30`).
- Ceilings mit dokumentierter Toleranz-Rationale (`tests/test_context_budgets.py:46-48`, Docstring).

### Schwächen / Risiken
| Befund | Evidenz |
|---|---|
| Fünf parallele Drift-/Baseline-Mechanismen: `generated-file-hashes.json` (382 Einträge), `context-hashes.json` (2 Einträge: CLAUDE.md, AGENTS.md), `external_tools_drift.py`, `standalone.check_standalone_drift`, AC-01-Baseline + `compact-golden`/`slimming-golden` + Ceilings | `.meta-config/*.json`; `standalone.py:575`; `tests/fixtures/` |
| Rebaseline-Churn: `generated-file-hashes.json` 95 Commits/90 Tage (= 14 % aller Commits), `ac01-baseline/hashes.json` 62, `compact-golden` 17; eigene Hash-Commits (`29f459cd chore: record regenerated hook hash`) | `git log -- <datei>` |
| Hash-Datei im Projekt versioniert → Zustand, der mit parallelen Branches kollidiert (Konfliktrate nicht gemessen) | `git ls-files .meta-config/generated-file-hashes.json` |
| Umweltabhängiger Render-Output: tmp-sink/TMPDIR fließt in Sync-Ergebnis ein; Toleranz im Ceiling-Test existiert nur wegen Pfad-/Datums-Jitter; 79 Testdateien referenzieren tmp-sink | `sync_pipeline.py:236-291`, `repo_containment.py:611,841`, `tmp_paths.py:35,298`, `test_context_budgets.py` Docstring Z.116-126 |
| Ceilings = eingefrorene Ist-Werte in Bytes (Ratchet, kein Budget) | `test_context_budgets.py:317-320` |
| Rebaseline-Policy ("nur auf cleanem main, mit Begründung") ist Prozess, nicht Mechanik | `test_ac01_render_identity.py:32-37` |

### Nutzen vs. Reibung
- Nutzen real (Schutz vor Überschreiben, Render-Vertrag über 9 Provider).
- Reibung strukturell: jede Template-Änderung → bis zu 4 Rebaseline-Orte; Determinismus-Lücke erzeugt Pseudo-Drift.

### Empfehlung
- Ein Hash-Register (`context-hashes` in `generated-file-hashes` aufgehen lassen) (S).
- Render-Determinismus: env-/datum-/pfadabhängige Werte aus gehashten Artefakten in eine ungehashte Datei auslagern (M).
- Ein `--rebaseline`-Kommando für hashes/AC-01/golden/ceilings mit Pflicht-Begründung in einer Log-Datei (M).
- Policy-Entscheid: Hash-Datei gitignoren oder durch Sync auto-committen (S).

---

## 5. Spec/Plan-Workflow, Orchestrator-Topologie, Delegation

### Stärken
- One-Seed-Prinzip: 9 Aspekte aus einem Seed, keine unabhängige Drift (`config/spec-plan-groups.yaml:24-53`).
- Topologie explizite Achse mit konservativen Fallbacks (`config/project-config.schema.json:2485`; `scripts/lib/topology.py:147-186`).
- Plan-Validierung (Dependency-/Overlap-Checks) und Checkpoints (`scripts/lib/orchestration.py:178-321`; `checkpoint.py`).

### Schwächen / Risiken
| Befund | Evidenz |
|---|---|
| Namenskollision: `context_file.topology` vs. `orchestrator.topology`; Schema warnt selbst davor | `project-config.schema.json:1074, 2485` |
| Hintergrund-Agenten: Sync-Vertrag verlangt `run_in_background:false`; Hinweis dazu ist "in diesem Repo nicht verifiziert"; kein mechanischer Schutz, wenn Orchestrator vor Completion endet | `agents/1-generic/orchestrator.md:240-241` |
| Orchestrator-Pflicht = Prompt-Regel + Hook nur auf Claude → auf 8 Providern reine Konvention | `.claude/rules/use-orchestrator.md`; `.claude/settings.json` |
| S/M/L/XL-Klassifikation durch den Orchestrator selbst, ohne Messung der Gate-Einhaltung | `use-orchestrator.md` (Spec/Plan-Gate) |
| Commit-Trailer (`Co-Authored-By`, `Claude-Session`) nirgends in agents/, config/, scripts/lib, hooks → allein Harness-gesteuert; Abweichungen des git-Agenten ungeprüft | `grep -rl Co-Authored agents config scripts/lib hooks` = leer |
| Overhead: Classify→Spec→Approve→Plan→Execute, jeder Spawn zahlt das Always-on-Budget erneut (§6) | `spec-plan-groups.yaml`; Memory-Messung |

### Empfehlung
- Achse umbenennen (`context_file.layout`) mit Migration (S/M).
- Completion-Guard: Orchestrator darf Turn nicht beenden, solange Hintergrund-Tasks offen; optional Stop-Hook (S–M).
- Trailer-Vertrag in `commit-conventions.md` + `auto_commit.render_auto_commit_block` rendern (`auto_commit.py:340`) (S).

---

## 6. Token-/Kontext-Budget

### Stärken
- Ceiling-Test macht fehlende Ceilings zur Violation (`tests/test_context_budgets.py:323-330`).
- Lazy-Kanal vorhanden (`.claude/rules/use-lazy-rules.md`; `scripts/lib/rules.py:371, 432`); `compact`-Profil als Opt-in.

### Schwächen / Risiken
| Befund | Evidenz |
|---|---|
| Always-on in diesem Repo: 22 Rules + CLAUDE.md = 13.475 Bytes (≈3.4k Tok Proxy); frühere tiktoken-Messung ~11.8k Tok inkl. Agent-Roster (50 Rollen) — Roster nicht über rules-preset steuerbar | `cat .claude/rules/*.md CLAUDE.md \| wc -c`; Memory `agent-meta-token-budget` (2026-08-14) |
| Ceilings in Bytes, pro Provider × Artefakt; kein Summenbudget pro Session (Rules + Roster + Context + Skill-Index) | `test_context_budgets.py:317-330` |
| Budget wird pro Subagent-Spawn erneut gezahlt; Rollenzahl (120 Templates) größter Hebel ohne Guard | `find agents -type f`; Memory-Hebel 3 |
| `compact` "opt-in/unverified" → Hebel nicht Default | `test_context_budgets.py` Docstring Z.112-114 |

### Strukturelle Hebel / Empfehlung
- Session-Summen-Ceiling in Tokens (tiktoken optional, Bytes/4-Fallback) als Test (S).
- Active-Set-Default verkleinern, Rest lazy; Agent-Beschreibungen ≤25 Tok (S + Policy).
- `compact` verifizieren und zum Default machen (M).

---

## Top-10 (Nutzen / Aufwand)

| # | Maßnahme | Nutzen | Aufwand |
|---|---|---|---|
| 1 | Baseline-Konsolidierung: ein `--rebaseline` für hashes/AC-01/golden/ceilings + Render-Determinismus | hoch (14 % Commit-Churn) | M |
| 2 | Hook-Python aus Heredocs in `.py`-Module | hoch (Wartbarkeit, Testbarkeit, 46 Commits/90 T) | M |
| 3 | Provider-JSON-Schema + Merge der zwei Capability-Quellen | hoch (Onboarding, Drift) | M |
| 4 | Test-Provider-Enumeration zentralisieren (34 → 1) | mittel | M |
| 5 | PyYAML-Fehlen → harter Fehler | mittel (SPoF sichtbar machen) | S |
| 6 | Migrations-Stages aus Dauer-Pipeline | mittel (Komplexität) | M |
| 7 | `topology`-Namenskollision auflösen | mittel | S/M |
| 8 | Orchestrator-Completion-Guard für Hintergrund-Agenten | mittel (Fehlermodus) | S–M |
| 9 | Session-Token-Summenbudget + Rollenzahl reduzieren | hoch (jeder Spawn) | S + Policy |
| 10 | "Security boundary" in Hook-Doku präzisieren/zurücknehmen | niedrig–mittel (Erwartungsmanagement) | S |

## Nicht geprüft / Annahmen
- Keine Tests, Syncs oder Hooks ausgeführt; Laufzeitverhalten nur aus Code/Kommentaren abgeleitet.
- Agent-Templates nur punktuell gelesen (`orchestrator.md:238-241`, `git.md:31-35`); validator/documenter/concept-* nicht geprüft.
- `_apply_agent_transform`, `_sync_stage_per_provider`, `hook_shell_scan_py` nur nach Umfang/Signatur bewertet, nicht zeilenweise.
- Merge-Konflikt-Häufigkeit der Hash-Datei nicht gemessen (Schluss aus Commit-Churn).
- TMPDIR-abhängige `--check`-Drift nicht reproduziert; Evidenz indirekt (tmp-sink-Stage, Toleranz-Rationale).
- Token-Zahlen: heute Bytes/4-Proxy; tiktoken-Werte aus Memory vom 2026-08-14, ggf. veraltet.
- `docs/analysis/*` nur per Dateiname referenziert; Überschneidungen mit 276/402 nicht abgeglichen.
- Hook-/Plugin-Protokolle für Gemini/Opencode (`hooks_dir`, `plugin_protocol`) nicht geprüft.
- graphify-Graph laut Hook-Hinweisen teils stale; nur zur Orientierung genutzt.
- Skill `add-provider` nicht unter `.claude/skills/` gefunden — Provider-Onboarding-Checkliste nicht gegengeprüft.
