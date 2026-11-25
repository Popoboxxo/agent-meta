# Provider-agnostic Sync/Hooks/MCP — Bundle Wave 5 — Spec
> Status: APPROVED (2026-11-23) — Freigabe: User (Hauptsitzung); gibt den Plan frei.

Klasse: XL (20 Items, **ein Branch `feat/provider-agnostic-sync-hooks-wave-5`, ein PR** — Nutzerentscheidung 2026-11-23, nicht verhandelbar; sequentielle Ausführung, mindestens ein Commit je Item, Rebaseline-Commits separat).
Ablage: `docs/specs/` (Klasse `specs`, Matrix `artifact-locations`). Der zugehörige Plan ist NICHT Teil dieser Spec.

## Problem / Ziel / Nicht-Ziele

**Problem.** Im Syncer (`scripts/lib`), in den Hook-Skripten (`hooks/1-generic`) und in der MCP-/Config-Schicht stehen provider-benannte Sonderpfade, duplizierte Implementierungen und ungetestete Eingebettet-Python-Blöcke. Das widerspricht der Konvention „Provider-Unterschiede über Config-Keys/Capability-Flags, nie über `if provider == "Name"`" (CLAUDE.md, Skill `provider-agnostic`).

**Ziel.** 20 offene Issues in drei Clustern abarbeiten, ohne Verhaltensänderung für bestehende Provider-Ausgaben, ausser dort, wo ein Item sie explizit ändert: #1269 (kein Prepend mehr bei fehlendem Marker, Skip bei Drift, `v=<hash>` im Marker), #1262 (neuer `--validate`-exit 1), #1251 (Projektverzeichnis-Variable im Hook-Adapter), #1263, #1248, #1203, #1275.

**Befund aus der Code-Verifikation (Stand 2026-11-23, Quelle der Scope-Anpassungen unten).** Mehrere Issue-Beschreibungen sind teilweise veraltet: #1198 hat im Repo keine Single-Brace-Fundstellen mehr, #1115 hat bereits einen Helfer (`scripts/measure_context_repin.py`), #1086 a–d sind im Code schon umgesetzt, #1254 ist intern bereits capability-gegated. Diese Items werden daher als **verify-first + Regressionsschutz** spezifiziert (siehe Item), nicht als Neubau.

**Nicht-Ziele.**
- Kein neues Feature jenseits der Item-Scopes; keine Reserve-Items (#1245, #1256, #1209, #1197, #1323, #1341, #1267, #1272) ausser per Fallback-Regel.
- Keine Änderung der Orchestrator-Topologie-Semantik (#1243 ist reine Benennung/Schema).
- **#1086 explizit ausgeschlossen:** (g) tier-presets `max==powerful` (Design-Entscheidung), (h) `active_set_refs.py` Keyword-Überlappungen (Design-Entscheidung), (i) Split von `scripts/lib/context.py` (eigener Task).
- **#1239 explizit ausgeschlossen:** Enum-Drift `scripts/lib/schema.py` (`update_providers_enum`), Defaults-Tabelle `external_tools_drift.py:192-194`.
- Kein Push, Tag, Release; keine Änderung an `.agent-meta/`-Submodul-Inhalten. Keine Reserve-Items.

**Betroffene Subsysteme.** `scripts/sync.py`, `scripts/lib/*`, `hooks/1-generic/**`, `rules/1-generic/*`, `config/ai-providers.yaml`, `config/project-config.schema.json`, `schemas/`, `tests/**`, Hash-/Golden-Baselines.

**Verifikation (global).** `python3 scripts/sync.py --validate` exit 0 und die jeweils genannten pytest-Dateien grün; vor dem PR der volle `pytest`-Lauf. Rebaseline nur, wenn sich generierte Ausgabe tatsächlich ändert (siehe Abschnitt Rebaseline).

## Interface Contracts (Datei:Symbol, Signatur, Fehlerpfade)

Alle Pfade relativ zum Repo-Root; alle genannten Symbole/Dateien wurden gegen den Code geprüft (2026-11-23), Zeilennummern sind Orientierung (driften). Grössen: S = ≤ 3 Dateien; M = 4–8 Dateien oder neue Abstraktion. ⚠ = Likely-M (#1253 #1255 #1268 #1269 #1238 #1239 #1240; dazu #1275 und #1263 als S/M — zusammen die „~9 M-Items").

### Cluster A — scripts/lib Sync

**A1 — #1243 Topologie-Naming** (S)
- Dateien: `config/project-config.schema.json`, `scripts/lib/topology.py` (Resolver für `orchestrator.topology`, Präzedenz `provider-overrides.<P>.topology` > `orchestrator.topology` > Ableitung).
- Contract: `context_file.topology` und `orchestrator.topology` erhalten im Schema unterscheidbare `description`-Texte und im Modul-Docstring von `topology.py` eine Abgrenzung. Kein Key-Rename ohne Alias (Alias bleibt lesbar, Deprecation-Hinweis); unbekannter Wert → bestehende Validierungsmeldung (exit 1).
- AC-1: Given beide Keys gesetzt, When `--validate`, Then exit 0 ohne Mehrdeutigkeitsmeldung. AC-2: Given Alias-Altkey (nur falls ein Rename erfolgt), When sync, Then identische Ausgabe + Deprecation-Hinweis. Tests: bestehende Topology-Tests + 1 neuer Schema-Beschreibungs-/Alias-Test.

**A2 — #1242 One-time-Migration-Stages gaten** (S)
- Datei: `scripts/lib/sync_pipeline.py`: `apply_discovery_migration` (Aufruf in `main`-Flow, ~L815), `apply_provider_migrations` (~L705, Aufruf ~L1761), `migrate_provider_paths` (~L631).
- Contract: Gate-Prädikat statt neuer Persistenz: eine Migrationsstage wird nur betreten, wenn mindestens ein Alt-Pfad/Alt-Artefakt der Migrations-Map (`config/provider-migrations.yaml`) im Projekt existiert; sonst Early-Return ohne Schreib-/Log-Aktion. Fehlerpfad: Prüfung wirft/ist unlesbar → Stage läuft wie bisher (fail-open für Migration, Warnung geloggt), kein Abbruch.
- AC-1: Given bereits migriertes Fixture-Projekt, When sync zweimal, Then zweiter Lauf ruft `migrate_managed_artifact`/Alt-Pfad-Removal nicht auf (Test-Spy) und Ausgabe ist byte-identisch. AC-2: Given Projekt mit Alt-Pfaden, When sync, Then Migration läuft genau einmal.

**A3 — #1254 opencode_v2_config hinter Capability-Prädikat** (S)
- Dateien: `scripts/lib/opencode_v2_config.py` (Prädikate `v2_active:339`, `owns_opencode_surface:357`), `scripts/lib/sync_pipeline.py` (Aufrufe `sync_opencode_v2_managed_keys` ~L1731, `sync_opencode_cli_file` ~L1740). (`scripts/lib/managed_json_surface.py` existiert nicht; die Managed-JSON-Merge-Logik ist `merge_managed_path` in `opencode_v2_config.py:245`.)
- Verifiziert: `sync_pipeline.py` enthält keinen Provider-Namensvergleich; die Writer sind intern über `owns_opencode_surface`/`v2_active` (Config-Keys) gegatet und für Nicht-Owner No-ops. Offene Restarbeit: Gate am Aufrufort sichtbar machen.
- Contract: Aufrufort in `sync_pipeline.py` prüft `owns_opencode_surface(provider_config, provider)`; Nicht-Owner betreten die Writer nicht. **Rollback-Pfad** (aufgezeichneter Rollback bei Nicht-Owner mit State, vgl. Kommentar L1736-1739) muss erreichbar bleiben → Q2.
- AC-1: Given alle Provider, Then Ausgabe byte-identisch. AC-2: Given Provider ohne v2-Surface, Then `sync_opencode_v2_managed_keys` wird (ohne State) nicht aufgerufen (Test-Spy). AC-3: Grep `sync_pipeline.py` nach `== "…"`/`in ("…")`-Provider-Namensvergleichen: 0 Treffer.

**A4 — #1253 Generische Dispatch-Tabellen für Isolation- und MCP-Format-Writer** (⚠ M, verify-first: Provider-Namensvergleiche sind in den In-Scope-Modulen bereits 0; echte Restarbeit ist die `fmt ==`-if/elif-Kette in `scripts/lib/mcp_provider_config.py` ~L88-90, ~L222-227, ~L247, ~L960-984)
- **In-Scope-Module (abschliessend, 6 Dateien):** `scripts/lib/isolation.py` (Isolation-Writer inkl. `_opencode_v2_gate_permissions:1474`, `_sync_opencode_v2_gate_permissions:1586`), `scripts/lib/mcp_provider_config.py` (MCP-Format-Writer), `scripts/lib/mcp.py`, `scripts/lib/opencode_v2_config.py` (`V2_MCP_FORMAT`), `scripts/lib/sync_pipeline.py` (Aufrufe), `scripts/lib/repo_containment.py` (Schlüssel-Auflösung). Alles andere ist **Nicht-Ziel** und zugleich zulässige BAC-5-Ausnahme:
  - `agent_sync.py`, `config_audit_providers.py`, `gitignore.py`, `providers.py`, `context.py`: verifiziert nur Kommentare/Docstrings, die den Namensvergleich verbieten (kein Code).
  - `model_discovery.py` (L609) und `repo_containment.py` (L17): `provider == "…"` steht nur im Docstring (Verbot bzw. Modell-API-Name), kein Code.
  - `external_tools_drift.py`: Defaults-Tabelle je Provider (Daten; Teil des Nicht-Ziels von #1239).
  - `provider_transform.py`: nur der Strip-Pfad ist über #1255 im Scope, übrige Format-Tabellen sind Daten.
- Contract: je Writer-Familie (Isolation, MCP-Format) eine Dispatch-Tabelle `format_key -> writer`, Schlüssel aus Provider-Config/Capability (vorhandenes Beispiel: `opencode_v2_config.V2_MCP_FORMAT`), nicht aus dem Namen. Unbekannter Schlüssel → klarer Fehler mit Liste gültiger Schlüssel (exit 1). Reihenfolge: nach #1254, vor #1239.
- AC-1: Given alle Provider, When sync, Then generierte MCP-/Isolation-Dateien byte-identisch (Golden unverändert). AC-2: Grep nach Provider-Namensvergleichen (Regex siehe BAC-5) in den sechs In-Scope-Modulen: 0 Treffer im Code. AC-3: Test: unbekannter Format-Key → Fehler mit Key-Liste. AC-4: Ausserhalb der Dispatch-Tabelle bleibt in `mcp_provider_config.py` keine `fmt ==`/`fmt in (…)`-if/elif-Kette (Grep `\bfmt\s*(==|in)\b`: nur Tabellen-Lookup), Verhalten byte-identisch.

**A5 — #1255 `strip-claude-lines` durch Capability ersetzen** (⚠ M)
- Verifizierter Ist-Stand: Flag `strip-claude-lines: true` steht in `config/ai-providers.yaml` (7 Provider-Spezifikationen, ~L253, 528, 607, 726, 816, 888, 971); Auswertung in `scripts/lib/provider_transform.py` (`spec.get('strip-claude-lines')` ~L640, ~L783; unbedingte Aufrufe ~L1042, ~L1304; Implementierung `_strip_claude_specific_lines` ~L1356: entfernt Zeilen, die mit `> **Extension:**` beginnen und `.claude/3-project/` enthalten); zusätzlich Aufrufer `scripts/lib/context.py` (Import ~L3670, Nutzung ~L3730).
- Entscheidung (ADR-4): **kein Umbau aller Agent-Templates** (Platzhalter-Variante würde > 8 Dateien/alle Agenten berühren). Stattdessen: Funktion umbenennen in `_strip_extension_hook_lines`; das Flag `strip-claude-lines` entfällt; die Zeilen werden entfernt, wenn dem Provider die Capability `extension_hook_path` fehlt (neuer optionaler String-Key in `config/ai-providers.yaml`, nur beim Provider gesetzt, der `.claude/3-project/` liest; Filter-Bedingung: Zeile enthält diesen Pfad). Fehlerpfad: Key vorhanden aber leer → wie fehlend.
- **Alle Strip-Aufrufstellen** (`provider_transform.py` ~L640, ~L783, ~L1042, ~L1304 und `context.py` ~L3730) müssen dieselbe Capability-Prüfung nutzen. Achtung Opencode: dort steht kein Flag, die Zeilen werden aber an den unbedingten Stellen (~L1042/~L1304) heute immer entfernt; eine Umstellung nur der flag-gesteuerten Stellen würde Opencode-Ausgabe ändern. Die Capability-Prüfung muss daher an jeder Stelle das heutige Ergebnis je Provider reproduzieren (Provider ohne `extension_hook_path` → entfernen, auch Opencode).
- AC-1: Given alle Provider (inkl. Opencode), Then generierte Agenten-Dateien **byte-identisch** (Golden-Diff leer; ein nötiger Rebaseline ist ein Befund, kein Routineschritt). AC-2: Grep `strip-claude-lines`/`_strip_claude_specific_lines` in `config/` und `scripts/`: 0 Treffer. AC-3: Test je Provider-Typ: Extension-Zeile fehlt in Nicht-Claude-Ausgabe (explizit Opencode und ein Flag-Provider), ist in Claude-Ausgabe vorhanden. AC-4: alle fünf Aufrufstellen rufen dieselbe Hilfsfunktion (Test/Grep).

**A6 — #1268 Managed-Block-Implementierungen vereinheitlichen** (⚠ M)
- Verifiziertes Inventar (Schreiber/Ersetzer des `agent-meta:managed-begin/-end`-Blocks): `scripts/lib/extensions.py` (`update_managed_block:90`, `render_managed_block:51`), `scripts/lib/context.py` (Regex-Ersetzer ~L49, ~L679, ~L1070; Continue-Form `_CONTINUE_MANAGED_BEGIN:2032`), `scripts/lib/context_templates/builder.py:29`, `scripts/lib/cli_commands.py` (`MANAGED_BEGIN:109`), `scripts/lib/release_scaffold.py` (`_MANAGED_BEGIN:25`). **Reine Detektoren/Leser, nicht zu vereinheitlichen:** `generated_file_drift.py` (`is_managed_artifact`), `consistency/context_size.py`, `external_tools_drift.py`. (Die im Issue gezählten sechs Implementierungen werden im Plan gegen dieses Inventar abgeglichen; Abweichung → Befund an den Nutzer.)
- Contract: neues Modul `scripts/lib/managed_block.py` (existiert nicht, Name bestätigt): `render_block(marker_id: str, body: str) -> str`, `replace_block(text: str, body: str, marker_id: str = "agent-meta") -> str`; Fehlerpfade: fehlender/doppelter End-Marker → `ManagedBlockError`, Datei unverändert. Bestehende Marker-Syntax unverändert. Reihenfolge: **vor #1269**.
- AC-1: Given Fixtures aller migrierten Anwendungsfälle, Then Ausgabe byte-identisch. AC-2: Given Datei mit kaputtem Marker, Then Fehler, Datei unverändert. AC-3: Alte Regex-Ersetzer ausserhalb von `managed_block.py` sind entfernt (Grep auf `managed-begin\\s*-->\.\*\?` in den Inventar-Dateien: 0 Treffer).

**A7 — #1269 Drift-Protection für Extensions** (M)
- Dateien: `scripts/lib/extensions.py` (`update_extensions:147`, `update_managed_block:90`), `templates/managed-block.md`, `commands/1-generic/update-extensions.md`, `scripts/lib/cli_commands.py` (CLI-Weg), Tests: `tests/test_cli_smoke_multi_provider.py` existiert; neue Datei `tests/test_extensions_drift.py`.
- Contract: (1) Marker trägt Hash: `<!-- agent-meta:managed-begin v=<hash> -->`, Hash über den Block-Body; Parser (aus A6) akzeptiert Altform ohne `v=` rückwärtskompatibel. (2) `update_extensions`: Hash-Mismatch (Block manuell geändert) → WARN + Datei überspringen, ausser `--force`. (3) Fehlender Marker → Warnung statt bisherigem Prepend (`extensions.py:101-102`). (4) `update-extensions --check` (kein Schreiben, exit ≠ 0 bei Drift). (5) Rollenfilter `--role <name>`; Orphan-Rolle (Datei ohne Template-Rolle) → Warnung. **Annahme bis User-Freigabe (Q5):** Drift ist Warnung + Skip; `--validate` schlägt bei Drift nur mit `--strict` fehl. (6) Command-Text (`update-extensions.md`) und Sync-Pfad angleichen.
- AC-1: Given manuell editierter Block, When update, Then WARN mit Dateipfad, Datei unverändert; mit `--force` überschrieben. AC-2: Given unveränderter Block, Then keine Meldung, idempotent. AC-3: Given fehlender Marker, Then Warnung, kein Prepend. AC-4: `--check` ändert nichts, exit ≠ 0 bei Drift. AC-5: Tests: happy, drift, missing marker, orphan role.

**A8 — #1086 UX-Inkonsistenzen im Sync-Output** (S, verify-first, Scope begrenzt)
- Auswahl (nur S-Teilprobleme): (a) `_config_rel_label` (`scripts/lib/mcp_provider_config.py:330`, alle fünf Aufrufer übergeben `project_root`) — **bereits umgesetzt**, nur Test ergänzen; (b) `scripts/lib/hooks.py`: Meldung ~L665 nutzt `pc.get('hooks_config_file')`, aber ~L216, ~L732, ~L748 nennen noch hartkodiert `settings.json` → aus `hooks_config_file` ableiten; (c) `scripts/lib/log.py` `skip` vs `note_unchanged` — **bereits getrennt**, Test pinnen; (d) `SyncLog.warn` dedupliziert bereits (`_seen_warnings`) — Test pinnen; (e) `scripts/lib/consistency/context_budget.py` `check_over_hard_cap` (~L240) nennt nur den Provider, nicht die geteilte Datei (Soft-Cap-Variante berechnet `others` bereits) → Meldung angleichen; (f) `CLAUDE.personal.md`-Legacy: `scripts/lib/context.py` `CLAUDE_PERSONAL_LEGACY_FILE:3192`, `init_claude_personal` — Migrationsverhalten per Test pinnen, nur ändern, wenn Test rot.
- AC-1: je Teilproblem a–f ein Test oder Snapshot-Vergleich. AC-2: Exit-Codes unverändert. AC-3: Nicht-Ziele g, h, i unberührt. Ist ein Teilproblem bereits korrekt, bleibt der Test als einziger Commit-Inhalt.

**A9 — #1203 Backup-Flag `--label`** (S)
- Dateien: `scripts/sync.py:494` (`--label`, metavar TEXT, Help bei `--backup` ~L493), `scripts/lib/cli_commands.py` (Backup-Konsument).
- Verifiziert: ein `--labels`-Flag existiert in `scripts/` **nicht** (anderes `--label`: `scripts/run_role_routing_eval.py:937`, separater Parser). Die im Issue behauptete Kollision ist nicht reproduziert → Q4.
- Contract: neuer kanonischer Name `--backup-label`; `--label` bleibt als deprecated Alias (Hinweis auf stderr), Help nennt beide.
- AC-1: `--label X` und `--backup-label X` erzeugen gleiches Backup; `--label` gibt Deprecation-Hinweis. AC-2: Test: argparse akzeptiert beide Namen. AC-3: `--help` nennt `--backup-label`.

**A10 — #1198 `{SE_BASE_DIR}` Single-Brace** (S, verify-first → Regressionsschutz)
- Verifizierter Ist-Stand: Variable `SE_BASE_DIR` wird über `scripts/lib/config.py:2830/2961` gesetzt; Substitution nur Doppelbrace: `scripts/lib/variables.py:157` `_VAR_PATTERN = r"\{\{([A-Z0-9_]+)\}\}"` (Digest nannte :109, falsch). Grep `(^|[^{])\{SE_BASE_DIR\}` über `agents/`, `rules/`, `scripts/`, `config/`: **0 Treffer** — `rules/1-generic/se-cascade-*.md` nutzen `{{SE_BASE_DIR}}` (korrekt), `ai-providers.yaml` und `provider_transform.py` enthalten `SE_BASE_DIR` gar nicht, die 12 `agents/1-generic/se-*.md` nutzen `{{ARTIFACT_SE_*_DIR}}` (22 Stellen, Doppelbrace). Verbleibende Single-Brace-Muster wie `{parent_path}`, `{FolderName}` in den SE-Agenten sind beabsichtigte Laufzeit-Platzhalter (kein Defekt). Einzig docs/ (Pläne/Specs, nicht generiert) enthalten die Single-Form.
- Contract: kein Template-Umbau erwartet. Neu: Consistency-Check in `scripts/lib/consistency/placeholders.py` (Liste bekannter Variablen ~L106/L201), der Single-Brace `{<bekannte Variable>}` in `agents/`, `rules/`, `templates/` meldet (WARN→`--validate`-Fehler). Falls das Issue (Q1) andere Fundstellen nennt → diese ergänzen.
- AC-1: Grep Single-Brace `{SE_BASE_DIR}` in `agents/ rules/ templates/`: 0. AC-2: `--validate` schlägt bei künstlich eingefügtem `{SE_BASE_DIR}` fehl (Test). AC-3: Laufzeit-Platzhalter (`{parent_path}`) lösen keinen Fehler aus. Rebaseline: nein (keine Ausgabeänderung erwartet).

### Cluster B — Hooks

**B1 — #1248 `# provider: …`-Header durch Protokoll-Header ersetzen** (S)
- Dateien (verifiziert): `hooks/1-generic/dod-push-check.sh`, `hooks/1-generic/lifecycle-check.sh`, `hooks/1-generic/sync-on-config-change.sh` (je 1 Treffer `^# provider:`).
- Contract: Header nennt Protokoll, z.B. `# protocol: tool-hook-v1`; kein 1-generic-Hook deklariert `provider:`; `hooks.py` behält den `provider`-Filter für 0-external.
- AC-1: Grep `^# provider:` in `hooks/1-generic/`: 0 (0-external-graphify-Guards bleiben Claude-only). AC-2: Hook-Tests grün. Rebaseline: ja (Hook-Hashes), eigener Rebaseline-Commit.

**B2 — #1251 Projektverzeichnis aus Adapter-Variable statt `CLAUDE_PROJECT_DIR`** (S)
- Dateien (verifiziert, Treffer): `hooks/1-generic/lib/hook_common.sh`, `artifact-path-guard.sh`, `orchestrator-guard-impl.sh`, `repo-containment-impl.sh`, `lib/kernel/containment.py`, `lib/kernel/model.py`.
- Contract: `hook_common.sh` stellt genau eine Variable `AM_PROJECT_DIR` bereit, die der Provider-Adapter setzt; `CLAUDE_PROJECT_DIR` wird nur noch im Claude-Adapter gelesen. Ungesetzt → Fallback auf bestehende Auflösung (cwd/git root), kein Abbruch; Fixed-Anchor-Verhalten bleibt (`test_fixed_anchor_*`, `test_payload_cwd_cannot_redefine*`).
- AC-1: Grep `CLAUDE_PROJECT_DIR` in `hooks/1-generic/`: nur im Adapter-Pfad. AC-2: Fixed-Anchor-Tests grün.

**B3 — #1238 Eingebettetes Python aus Bash-Heredocs in Module** (⚠ M)
- Dateien (verifiziert, Heredoc-Treffer): `hooks/1-generic/lib/hook_common.sh` (4), `repo-containment-impl.sh` (3), `dod-push-check.sh` (2), `artifact-path-guard.sh`, `orchestrator-guard-impl.sh`, `release-gates/artifact-freshness.sh`, `viz-log.sh` (je 1). Zielort der Module: `hooks/1-generic/lib/` (siehe Q3; Python-Kernel-Muster existiert: `hooks/1-generic/lib/kernel/containment.py`).
- Contract: je Heredoc ein Modul mit `main(argv: list[str], stdin: str) -> int`; Hook ruft `python3 <modul>`; Verhalten und Exit-Codes identisch. Fail-closed ohne `python3` (#595) bleibt.
- AC-1: pro Modul ≥ 1 direkter pytest-Unit-Test. AC-2: bestehende Hook-Integrationstests grün. AC-3: Grep `python3 - <<` / `<<'PY'` in Hooks: 0. Rebaseline: ja, eigener Commit. Reihenfolge: **vor #1275 und #1263**.

**B4 — #1275 Schreibschutz für `external/` und Submodul-Pfade** (S/M)
- Dateien: `hooks/1-generic/lib/kernel/containment.py` (`check_containment:18`; `_META_SUBMODULE = ".agent-meta"` — dort ausdrücklich ausserhalb des Jails, daher separate Prüfung), `hooks/1-generic/repo-containment-impl.sh` (Edit/Write-Zweig; ruft den Kernel `check_containment`; `orchestrator-guard-impl.sh` bleibt unberührt), `scripts/lib/repo_containment.py` (Config-Auflösung), `.claude/skills/submodule-protection/SKILL.md` (nennt `.gitmodules` — Datei existiert im Repo nicht; Text angleichen: „falls vorhanden").
- Contract: konfigurierbare Liste `repo_containment.protected_paths` (Default: `external/`, `.agent-meta/`, dazu alle `path =`-Einträge einer vorhandenen `.gitmodules`); Edit/Write/NotebookEdit und Bash-Redirect-Ziele darunter → Block (exit 2) mit klarer Meldung; expliziter Override: Env `AM_ALLOW_PROTECTED_WRITE=1`. Convention boundary (kein Security-Anspruch). Ohne `.gitmodules` und ohne Config: nur die Defaults.
- AC-1: Given Write `external/foo`, Then Block mit Meldung. AC-2: Given Write `docs/foo`, Then erlaubt. AC-3: Given Override gesetzt, Then erlaubt. AC-4: Given `.gitmodules` mit `path = foo`, Then Write `foo/a` blockt.

**B5 — #1263 MCP-Blocked-Tool-Liste via `permissions.deny`/Hook** (S/M)
- Dateien: `scripts/lib/mcp.py`, `scripts/lib/mcp_deny.py` (existiert), `hooks/1-generic/lib/hook_common.sh`, `rules/1-generic/mcp-guardrails.md`.
- Contract: verbotene MCP-Tools werden aus der MCP-Registry in eine maschinenlesbare Deny-Liste überführt: `permissions.deny` (Provider mit Capability) bzw. Hook-Check (Fallback). Die Prosa-Liste in `mcp-guardrails.md` stammt aus derselben Quelle (ADR-3). Leere Liste → kein Eintrag.
- AC-1: Given Registry mit `playwright`-Verbotsliste, Then Settings enthalten genau diese Tools in `permissions.deny` bzw. der Hook blockt. AC-2: `mcp-guardrails.md` stimmt mit der Deny-Liste überein (Test). AC-3: Aufruf eines verbotenen Tools wird im Hook-Test geblockt. Rebaseline: ja, eigener Commit.

### Cluster C — MCP / Config / Tests

**C1 — #1262 MCP-URLs/Secrets in `--validate` prüfen** (S) — **vor #1274**
- Datei: `scripts/lib/mcp_health.py` (existiert) + Aufruf im Validate-Pfad.
- Contract: pro MCP-Server: URL syntaktisch gültig (`urllib.parse`, http/https/ws/wss); Secrets nur als Env-Referenz (`${VAR}`), Klartext-Token → Fehler; ungesetzte Env-Var → Warnung; kein Netzwerk. Rückgabe `list[tuple[server, severity, message]]`; Fehler-Severity → `--validate` exit 1.
- AC-1: ungültige URL → exit 1 mit Servername. AC-2: Klartext-Secret → exit 1, Wert NICHT in Meldung. AC-3: gültige Config → exit 0. Tests: `tests/test_mcp_health.py` (neu oder erweitert).

**C2 — #1274 Scaffold + Checklisten-Test für neuen MCP-Server** (S) — **nach #1262**
- Dateien: Scaffold `docs/howto/new-mcp-server.md`, Test `tests/test_mcp_server_checklist.py`.
- Contract: Checklisten-Test parametrisiert über alle Registry-Server: Eintrag vollständig, Skill `mcp-<server>/SKILL.md` vorhanden, Guardrail-Eintrag (falls Verbotsliste), #1262-Check besteht.
- AC-1: neuer Server ohne Skill → Test rot mit Servername. AC-2: alle vorhandenen Server grün.

**C3 — #1239 JSON-Schema für Provider-Einträge + Capability-Quellen mergen** (⚠ M) — **nach #1253, #1255, #1254**
- Scope (begrenzt): neues `schemas/provider-entry.schema.json` (`schemas/` enthält bisher nur a2a- und se-Schemas); Validierung in `--validate`, optional via `jsonschema` mit Fallback (Muster `scripts/lib/config.py:130`, keine neue Dependency); Zusammenführung der zwei Quellen — `config/ai-providers.yaml` (Block `capabilities`) und `config/provider-capabilities.yaml` — **über die bereits vorhandene** `merge_provider_mappings` (`scripts/lib/context_report.py:205`) mit Loadern `load_providers_config`/`load_provider_capabilities` (`scripts/lib/providers.py:313/422`); Konflikt → Fehler mit beiden Fundorten; hartkodierte Provider-Liste `scripts/lib/pipelines.py:56` aus der Registry ableiten. Führende Quelle: `config/ai-providers.yaml` (**Annahme bis User-Freigabe**, siehe Q6).
- Schema enthält die neuen Keys aus A3–A5 (`extension_hook_path`, Format-Keys).
- AC-1: alle Einträge → `--validate` exit 0. AC-2: unbekannter Key/Typfehler → exit 1 mit Eintrag + Feld. AC-3: Konflikt zwischen Quellen → Fehler. AC-4: `pipelines.py` enthält keine Provider-Literalliste mehr.

**C4 — #1240 Provider-Enumeration in Tests zentralisieren** (⚠ M)
- Dateien: `tests/conftest.py` (Konstante/Fixture `ALL_PROVIDERS` aus der Registry, Loader aus C3), betroffene Tests per Grep nach Provider-Tupeln (`_PROVIDERS` in `tests/test_context_budgets.py` ist ein bekannter Fall).
- Contract: leere Registry → Fixture schlägt laut fehl. Neuer Provider erscheint automatisch in parametrisierten Tests.
- AC-1: Grep nach hartkodierten Provider-Tupeln in `tests/` (`("Claude", "Gemini"`, `_PROVIDERS =`): 0 ausser Zentraldatei. AC-2: Collect-Count vorher/nachher gleich. Reihenfolge: nach C3.

**C5 — #1115 Re-Pin-Helfer vervollständigen** (S)
- Verifizierter Ist-Stand: `scripts/measure_context_repin.py` (`format_repin_block`, `main`) existiert und `tests/test_context_repin_helper.py`; er deckt nur `_IST_FULL` (`tests/test_context_budgets.py:306`) ab, **nicht** `_IST_COMPACT` (`:609`). `TOLERANCE_MAX_BYTES = 4096` und Ceilings bleiben unverändert.
- Contract: Helfer erhält Argument `--profile {full,compact}` (Default `full`; `compact` misst die Compact-Projekte und druckt den Block gegen `_IST_COMPACT`); Skill `.claude/skills/conventions/SKILL.md` erhält eine Notiz mit dem Befehl. Idempotenz: zweiter Lauf nach Übernahme → kein Block, exit 0.
- AC-1: `--profile compact` gibt einen einfügefertigen `_IST_COMPACT`-Block bei Abweichung aus (exit 1), sonst nichts (exit 0). AC-2: Test in `tests/test_context_repin_helper.py`. AC-3: Skill-Notiz nennt den Befehl wörtlich.

## Datenfluss

Quellen (Templates `agents/**`, `rules/1-generic`, `hooks/1-generic`, `config/*.yaml|json`, Provider-Registry, `project.yaml`) → `sync.py` / `sync_pipeline.py` Stages (Migrations-Gate A2, Capability-Gate A3) → Managed-Block-Modul (A6) und Dispatch-Tabellen (A4) → Provider-Zielverzeichnisse (`.claude/`, `.agents/`, `.gemini/` …) → `--validate` (Schema C3, MCP-Health C1, Platzhalter-Check A10, Extension-Drift A7) → Baselines (Hash-/Golden-Dateien).
Hooks: Provider-Adapter setzt `AM_PROJECT_DIR` (B2) → `hook_common.sh` → Python-Module (B3) → Entscheidung Block/Allow (B4 Pfadliste, B5 Deny-Liste).
Neue Persistenz: Block-Hash im Marker (A7), Schema-Datei (C3); sonst keine.

## Abhängigkeits- und Reihenfolge-Plan (sequentiell, ein Branch)

Harte Abhängigkeiten:
1. #1262 → #1274.
2. #1254 → #1253 (beide `sync_pipeline.py`; #1254 kleiner) → #1255 → #1239.
3. #1268 → #1269.
4. #1238 → #1275, #1263 (gleiche Hook-Dateien).
5. #1239 → #1240.
6. #1255 → #1198 (Überlappung `provider_transform.py`/`ai-providers.yaml`: #1255 ändert beide; #1198 soll sie nicht anfassen, läuft aber danach, um Merge-Konflikte auszuschliessen).
7. #1203 → #1086 (Help-Text in `sync.py`).

**Commit-Reihenfolge (verbindlich, Cluster A → B → C; konsistent mit der File-Overlap-Map):**
`#1243, #1242, #1254, #1253, #1255, #1268, #1269, #1203, #1198, #1086, #1248, #1251, #1238, #1275, #1263, #1262, #1274, #1239, #1240, #1115`.
Je Item ≥ 1 Commit; **Rebaseline-Commits separat** (nach dem auslösenden Item-Commit, nicht in ihn gefaltet), damit jede Baseline-Änderung einzeln reviewbar ist.

## File-Overlap-Map

| Datei | Items | Konsequenz |
|---|---|---|
| `scripts/lib/sync_pipeline.py` | #1242, #1254, #1253 | strikt #1242 → #1254 → #1253 |
| `scripts/lib/opencode_v2_config.py` | #1254 (Prädikate), #1253 (V2_MCP_FORMAT-Nutzung) | #1254 vor #1253 |
| `scripts/lib/provider_transform.py`, `scripts/lib/context.py` (Import ~L3670, Nutzung ~L3730), `config/ai-providers.yaml` | #1255, #1198 (nur Absicherung), #1239 (Schema-Keys) | #1255 → #1198 → #1239 |
| `scripts/lib/repo_containment.py` | #1253 (Schlüssel-Auflösung), #1275 (`protected_paths`) | #1253 → #1275 |
| `scripts/lib/extensions.py`, `templates/managed-block.md` | #1268, #1269 | #1268 → #1269 |
| `scripts/lib/context.py` | #1268, #1086(f) | #1268 vor #1086 |
| `scripts/lib/mcp.py`, `mcp_provider_config.py`, `mcp_deny.py` | #1253, #1086(a), #1263 | #1253 → #1086 → #1263 |
| `scripts/lib/mcp_health.py` | #1262, #1274 | #1262 → #1274 |
| `scripts/sync.py`, `scripts/lib/cli_commands.py` | #1203, #1269, #1086 | #1269 → #1203 → #1086 |
| `scripts/lib/hooks.py` | #1086(b) | allein |
| `config/project-config.schema.json` | #1243, #1239 | #1243 vor #1239 |
| `hooks/1-generic/lib/hook_common.sh` + Hooks | #1248, #1251, #1238, #1275, #1263 | #1248 → #1251 → #1238 → #1275 → #1263 |
| `rules/1-generic/mcp-guardrails.md` | #1263 | allein |
| `tests/conftest.py`, `tests/test_context_budgets.py` | #1240, #1115 | #1240 → #1115 |

## Rebaseline-Regel

- Rebaseline von Hash-/Golden-Dateien (Helfer laut `docs/specs/2026-11-15-rebaseline-helper-spec.md`) **nur**, wenn sich generierte Ausgabe ändert. Erwartet: #1269 (Marker `v=<hash>` ändert generierte Extension-/Managed-Block-Hashes), #1263, #1248, #1251 (nur Adapter-Pfad), #1238, #1275, #1203 (Help-Text, falls gepinnt). Nicht erwartet: #1198 (verify-first). Alle A-Refactors (#1253, #1255, #1268, #1254) sind byte-identisch zu halten — ein nötiger Rebaseline dort ist ein Befund, kein Routineschritt.
- Rebaseline ist ein **eigener Commit** direkt nach dem auslösenden Item-Commit; die Commit-Message begründet den Baseline-Diff kurz.

## Aufwand, 1-PR-Strategie, Risiko und Alternativen

| Item | Grösse | | Item | Grösse |
|---|---|---|---|---|
| #1243 | S | | #1248 | S |
| #1242 | S | | #1251 | S |
| #1254 | S | | #1238 | ⚠ M |
| #1253 | ⚠ M | | #1275 | S/M |
| #1255 | ⚠ M | | #1263 | S/M |
| #1268 | ⚠ M | | #1262 | S |
| #1269 | ⚠ M | | #1274 | S |
| #1086 | S (6 Teilprobleme, begrenzt) | | #1239 | ⚠ M |
| #1203 | S | | #1240 | ⚠ M |
| #1198 | S (verify-first) | | #1115 | S |

**Strategie (Nutzerentscheidung): ein Branch, ein PR, 20+ Commits.**
- Sequenz Cluster A → B → C; innerhalb A zuerst die byte-identischen Refactors (#1254, #1253, #1255, #1268), dann Features (#1269 …), damit ein Byte-Identitäts-Bruch früh auffällt.
- Rebaseline-Commits separat (siehe oben); ein roter Golden-Diff in einem A-Refactor stoppt den Branch, bis er begründet oder behoben ist.
- Mitigation der ~9 M-Items: Plan zerlegt jedes ⚠-Item in Tasks ≤ 8 Dateien; PR-Beschreibung gliedert Review nach Cluster und Commit-Bereich; jeder Commit grün (`--validate` + zugehörige Tests), keine „Fix-up"-Commits über Item-Grenzen.
- **Fallback = Swap mit Reserve** (Regel unten), je Swap Eintrag im PR-Body und in „Änderungen an dieser Spec".
- **Warum nicht 3 PRs:** Nutzerentscheidung (geringerer Koordinations-/Rebase-Aufwand, gemeinsame Baselines). Alternativen und ihr Preis: 3 PRs (je Cluster) würden Review-Last und Baseline-Konflikte senken, aber dreimal Rebaseline/Merge-Warten kosten — verworfen. Rückfall nur auf ausdrücklichen Nutzerwunsch.
- **Hauptrisiken der 1-PR-Wahl:** grosse Review-Fläche (R1), gegenseitige Blockade bei einem roten Item (R2) → Swap-Regel statt PR-Split; Merge-Konflikt mit parallelen main-Änderungen → regelmässiger Rebase auf `main` zwischen Clustern.

**Fallback-Regel (Swap mit Reserve):** Ein Item wird ersetzt, wenn (a) nach dem Inventar-Schritt des Plans mehr als 8 Dateien oder ein nicht byte-identischer Refactor-Diff nötig wären, (b) sein Commit nach 2 Fix-Iterationen `--validate`/pytest nicht grün ist, oder (c) ein Q-Punkt ohne Entscheidung blockiert. Ersatz aus Reserve (#1245, #1256, #1209, #1197, #1323, #1341, #1267, #1272) in dieser Reihenfolge, gleiche oder kleinere Grösse, ohne Datei-Overlap mit offenen Items. Abhängige Items (#1274 ← #1262; #1239 ← #1253/#1255/#1254; #1269 ← #1268; #1240 ← #1239; #1275/#1263 ← #1238; #1198 ← #1255) werden mit dem Blocker zurückgestellt und ebenfalls ersetzt.

## Acceptance Criteria (Bundle-Ebene, nummeriert)

- BAC-1: Given Branch-Ende, When `python3 scripts/sync.py --validate`, Then exit 0.
- BAC-2: Given Branch-Ende, When voller `pytest`-Lauf, Then grün; Testanzahl ≥ Ausgangsstand.
- BAC-3: Given Branch-Ende, Then jedes der 20 Items (bzw. seines Swap-Ersatzes) hat **≥ 1 Commit** (Conventional Commits, englisch, ≤ 72 Zeichen, Trailer laut Projekt-Config); Rebaseline-Commits sind eigene Commits; alles in einem PR.
- BAC-4: Given A-Refactor-Commits (#1253, #1255, #1268, #1254), Then generierte Ausgabe über alle Provider **strikt byte-identisch** (Golden-Diff leer, kein Rebaseline in diesen Commits).
- BAC-5: Given Branch-Ende, Then in den berührten Modulen kein Provider-Namensvergleich: Grep (rg, Kommentar- und Docstring-Zeilen ausgenommen; verbleibende Docstring-Treffer wie `repo_containment.py:17` und `model_discovery.py:609` sind explizite Ausnahmen) mit `^[^#\n]*(provider|provider_name)\s*(==|!=)\s*["']` sowie `^[^#\n]*(==|!=|in)\s*\(?["'](Claude|Gemini|Opencode|OpenCode|Continue|Mammouth)["']` liefert 0 Treffer in den sechs In-Scope-Modulen von A4 und in `sync_pipeline.py`; Ausnahmen sind ausschliesslich die in A4 aufgelisteten Nicht-Ziel-Module (PR-Nachweis); kein `# provider:`-Header in `hooks/`.
- BAC-6: Jeder Item-AC ist einem Interface-Contract desselben Items zugeordnet (Traceability-Tabelle im Plan).
- BAC-7: Keine neue externe Python-Dependency (`pyproject.toml`/`requirements.txt` unverändert; `jsonschema` bleibt optional).
- BAC-8: Kein Secret-Fund im Secret-Scan über alle geänderten Dateien.

## Offene Fragen + Risiken

**Offene Fragen:** keine — Q1–Q6 am 2026-11-23 vom User entschieden (siehe „Entscheidungen").

**Risiken.**
- R1 Hoch: 1 PR, 20+ Commits, ~9 M-Items — Review-Last (Mitigation siehe Strategie).
- R2 Hoch: Byte-Identität der A-Refactors (#1253/#1255/#1268) durch versteckte Provider-Sonderfälle gebrochen → Fallback-Regel (a).
- R3 Mittel: #1263 ändert Deny-Semantik für laufende Sessions (wirkt erst nach Sync/Neustart) → Hinweis im PR.
- R4 Mittel: #1275 Fehlalarm blockiert legitime Submodul-Updates (Convention boundary) → Override `AM_ALLOW_PROTECTED_WRITE=1`.
- R5 Mittel: Hook-Extraktion (#1238) verändert Fail-closed ohne `python3` (#595) → AC + Test.
- R6 Niedrig: `--label`-Deprecation bricht externe Skripte → Alias bleibt.
- R7 Mittel: Python-3.9-Kompatibilität bei neuen Modulen → `from __future__ import annotations`, keine `X | Y`-Laufzeittypen/`match`.
- R8 Mittel: Issue-Beschreibungen teilweise veraltet (#1198, #1115, #1086, #1254) → verify-first-Specs; Items können zu reinen Test-/Check-Commits schrumpfen (zählt als erfüllt).

## Entscheidungen (ADR-Kurzform)

- ADR-1: Capability-Flag statt Provider-Name als Dispatch-Schlüssel. Kontext: Konvention `provider-agnostic`. Konsequenz: Provider-Schema (C3) muss alle Flags kennen → #1239 nach A-Items.
- ADR-2: Deprecated Alias statt Hard-Rename (#1243, #1203). Konsequenz: eine Release-Frist Doppelpflege.
- ADR-3: Eine generierte Deny-Quelle für Prosa und Maschinenliste (#1263). Konsequenz: Rule-Datei wird generiert/geprüft, nicht manuell editiert.
- ADR-4: #1255 über Capability `extension_hook_path` statt Platzhalter in allen Agent-Templates. Kontext: Template-Umbau würde alle Agenten berühren (Review-/Byte-Identitäts-Risiko). Konsequenz: Filter bleibt zeilenbasiert, ist aber provider-agnostisch gesteuert.
- ADR-5: Ein Branch/ein PR (Nutzerentscheidung) mit separaten Rebaseline-Commits und Swap-Regel statt PR-Split.

**Nutzerentscheidungen Q1–Q6 (2026-11-23, aufgelöst):**
- Q1 #1198: nur Regressions-Check umsetzen + Kommentar ans Issue (0 Single-Brace-Treffer im Code).
- Q2 #1254: Rollback für Nicht-Owner mit State bleibt erreichbar (Gate = „owns surface OR State-Datei vorhanden").
- Q3 #1238: Zielort der Hook-Module `hooks/1-generic/lib/`.
- Q4 #1203: `--backup-label` als neuer Name, `--label` bleibt als Alias.
- Q5 #1269: Drift = Warnung + Skip; Fehler nur mit `--strict`.
- Q6 #1239: `config/ai-providers.yaml` ist führende Capability-Quelle.
- Rahmen: ein Branch `feat/provider-agnostic-sync-hooks-wave-5`, ein PR.

## Änderungen an dieser Spec
- 2026-11-25: User-Override für Plan-Task T21: Files-Block exakt `scripts/lib/hooks.py`, `hooks/1-generic/antigravity-json-adapter.sh`, `hooks/1-generic/lib/hook_common.sh`, `hooks/1-generic/artifact-path-guard.sh`, `hooks/1-generic/orchestrator-guard-impl.sh`, `hooks/1-generic/repo-containment-impl.sh`, `hooks/1-generic/lib/kernel/containment.py`, `hooks/1-generic/lib/kernel/model.py`, `tests/test_hook_registration_invariant.py`, `tests/test_antigravity_hooks_registration.py`, `tests/test_repo_containment_hook.py`, `tests/test_orchestrator_guard_hook.py`, `tests/test_artifact_path_guard_hook.py`, `tests/test_hook_kernel.py`, `tests/test_artifact_locations_scenario.py`. Grund: Inventar: mindestens 10 Dateien für den AC-Kern; 15 Dateien für die vollständige Testabdeckung, daher Aufhebung der 8-Datei-Grenze nur für T21; `scripts/lib/hooks.py` wird als explizite Overlap-Ausnahme zugelassen; AC unverändert; kein Swap. Status bleibt APPROVED.
- 2026-11-23: B1 AC-1 auf `hooks/1-generic/` eingegrenzt; Grund: die 0-external-graphify-Guards bleiben Claude-only (Adapter-Verhalten unverifiziert). Status bleibt APPROVED.
- 2026-11-23: APPROVED durch User; Q1–Q6 entschieden und aufgelöst.
- 2026-11-23: Erstentwurf (DRAFT).
- 2026-11-23: Revision 2 — A4-Modulliste abschliessend (6 Dateien, Rest als Nicht-Ziel/BAC-5-Ausnahme), A5 alle Strip-Aufrufstellen inkl. Opencode, Q5/Q6 getrennt mit Default-Annahme, Zielsatz/Rebaseline-Liste um #1269/#1262/#1251, Overlap-Map ergänzt, BAC-5-Regex vollständig.
- 2026-11-23: Revision 1 — Review-Befunde 1–8 eingearbeitet: 1-PR-Entscheidung, `managed_json_surface.py`-Verweis entfernt, Symbole gegen Code verifiziert, #1198/#1255-Reihenfolge und Overlap-Map konsistent, Abschnitt Risiko/Alternativen, Q1/Q6 aufgelöst, Scope #1086/#1115/#1239 festgelegt, BAC-3/4/5 korrigiert.

## Trace-Anker: spec-id: SPEC-provider-agnostic-sync-hooks-wave-5
