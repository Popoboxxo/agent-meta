# Conclusions: Audit-Batch #712 / #730–#743 — Provider-Agnostik, Config-Audit & Drift-Backups (docs/audit-batch-730-743-update)
Datum: 2026-09-11

## Zusammenfassung
Der Audit-Batch zu den Issues #712 und #730–#743 (Branch `docs/audit-batch-730-743-update`, Basis `16b030b0`) wurde abgeschlossen: 8 Work Packages (WP0–WP7) plus der `--check`-Nachzügler #752, verteilt auf 9 PRs (#748, #755–#762). Kerninhalte waren die Provider-Agnostik-Härtung (neue `commands`-Capability, Entfernung aller 22 `if provider ==`-Zweige — AST-verifiziert 0), ein read-only `--audit-config`, Drift-Backups vor Overwrites sowie Test- und CI-Härtung. Alle WPs sind committet; #712, #730–#741 (relevant), #739 und #743 sind geschlossen.

## Erkenntnisse & Aktualisierungen

1. **WP0 — `.gitattributes` LF-Zwang für Guard-Hooks (#712, PR #755)**
   - Repo-Root-`.gitattributes` erzwingt LF (`text eol=lf`) für `hooks/1-generic/orchestrator-guard*.sh` — verhindert CRLF-bedingte "bad interpreter"-Fehler bei direkt ausgeführten deployed Hooks.

2. **WP1 — Config-Normalisierung & Provider-Enum (#741/#731/#732, PR #748)**
   - Null-Config-Blöcke werden normalisiert; `agent-meta-version` defaultet aus `VERSION`.
   - Das `ai-providers`-Enum wird aus `config/provider-capabilities.yaml` generiert (9/9 Provider); unbekannte Provider werden abgelehnt — der stille Claude-Fallback entfällt.

3. **WP2 — Provider-agnostischer Dispatch & `commands`-Capability (#735/#743, PR #756)**
   - Neues Capability-Flag `commands` für alle 9 Provider: Claude/Gemini/Opencode/Continue `true`; Copilot/Mammouth/Codex/ZCode/KimiCode explizit `false` (verifizierte Aussage "keine Command-Oberfläche").
   - Alle 22 `if provider ==`-Zweige entfernt (AST-verifiziert 0); Dispatch läuft über Config-Keys/Capability-Flags.
   - `CHECKPOINTING_BLOCK` an `orchestrator.md`/Snippet verdrahtet; Chat-Push über per-Provider `hook_protocol`.

4. **WP3 — Admin-UI: erweiterte writable Sections (#730, PR #759)**
   - Schreibbare Sections in `admin-server.py` erweitert: hooks, debug-mode, tier-overrides, mcp-role-overrides, backup, submodule-protection.
   - Nicht-schreibbare Section liefert jetzt explizit 4xx statt stillem Fehlschlag; `docs/ui/admin-ui.html` erhält die neuen Sections, A11y-Verbesserungen und sichtbare Save-Fehler.

5. **WP4 — Test- und CI-Härtung (#740/#739, PR #757)**
   - Falsches assert in `scenario-21` korrigiert; die Scenario-Suite läuft jetzt in CI.
   - `sync.py --check` in `validate.yml` aufgenommen; VERSION/CHANGELOG in den paths-filter von `orchestration-test.yml` ergänzt.

6. **WP5 — Config-Variablen & `--audit-config` (#733/#737/#736, PR #758)**
   - `_VARIABLE_FALLBACKS` für 8 leckende Variablen; invertierter jsonschema-Hinweis korrigiert; `fill_defaults()` befüllt `project.short`.
   - Stale `feature`-Rolle entfernt; `provider-expert` dokumentiert.
   - Reverse-Drift-Check `role_defaults_without_template` in `--audit-config` ergänzt.

7. **WP6 — Drift-Backup vor Overwrite (#734, PR #760)**
   - `backup_drifted_files()` in `scripts/lib/generated_file_drift.py` schreibt vor dem Overwrite ein `<datei>.sync-backup-<YYYYmmdd-HHMMSS>`-Sibling des Pre-Overwrite-Inhalts; fail-soft, dry-run-noop (liefert aber die geplanten Pfade).
   - `.gitignore`-Managed-Eintrag `*.sync-backup-*` hält die Backups aus dem Repo.

8. **WP7 — Read-only `--audit-config` (#738, PR #761)**
   - `--audit-config` schreibt keine `env.*`-Dateien und kein `sync.log` — reine Diagnose ohne Seiteneffekte.

9. **#752 — `--check`-Fail-open & reproduzierbares Datum (PR #762)**
   - `--check` behandelt legitim fehlende, gitignorierte Provider-Wurzeln als Non-Drift (fail-open).
   - `AGENT_META_DATE` ist reproduzierbar: `SOURCE_DATE_EPOCH` → CHANGELOG-Release-Datum → `now()`.

10. **Dokumentation aktualisiert**
   - `docs/CODEBASE_OVERVIEW.md`: `commands`-Capability in der Flag-Tabelle von §11.2 (`config/provider-capabilities.yaml`) ergänzt inkl. Gate-Hinweis auf `scripts/lib/commands.py`; neuer Sub-Abschnitt zu `scripts/lib/generated_file_drift.py` (§9, Scan/Backup/Baseline-Flow); Header-Datum aktualisiert.

## Nächste Schritte
- Offene Follow-ups: #751, #753, #754.
- Residualrisiken: `commands: false`-Einträge sind verifizierte Aussagen ohne Command-Oberfläche — kein Flippen auf `true` ohne Prüfung von `commands_dir`/`commands_ext`/`commands_format` in `config/ai-providers.yaml` (sonst droht erneut ein stiller Fall-through). Der Drift-Backup ist ein Sicherheitsnetz, keine Preservation — die Datei wird weiterhin in-place überschrieben. `--check` bleibt für legitim fehlende, gitignorierte Provider-Wurzeln bewusst fail-open.
