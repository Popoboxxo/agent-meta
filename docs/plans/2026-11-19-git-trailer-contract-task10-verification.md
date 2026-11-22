# Verifikation Task 10 — git-trailer-contract (#1247)

Datum: 2026-11-19 · Branch `fix/1247-1168-trailer-contract` · Plan: `docs/plans/2026-11-15-git-trailer-contract-plan.md` (Task 10) · Spec: `docs/specs/2026-11-15-git-trailer-contract-spec.md` (AC 1-21)
Nur Ausführung, keine Code-Änderung. Python: System-`python3` (Version nicht 3.9 gepinnt, siehe GAP-1).

## Ergebnisse

| Kommando | Ergebnis |
|---|---|
| `pytest -q` auf `test_commit_trailers.py`, `test_commit_trailers_placeholder_whitelist.py`, `test_admin_ui_commit_section.py`, `test_git_template_commit_trailer_rule.py`, `test_admin_ui_auto_commit_section.py` | **34 passed**, 0 failed (257 s) |
| Ergänzend (nicht beauftragt, für Belege): `pytest -q tests/test_auto_commit_block_render.py tests/test_provider_agnostic_dispatch.py tests/test_admin_server.py -k "commit or provider_agnostic or literal"` | **103 passed**, 207 deselected, 9 subtests passed |
| `python3 scripts/sync.py --validate` | Exit **0**; 0 Fehler; Zusammenfassung `[WARN] 4 warning(s) found` (Config-Audit-Warnungen: repo-containment ohne Hook-Support, progress-dir gitignored x2, temp-literal sink-relative); keine `commit:`-Meldung |
| `python3 scripts/sync.py --check` | Exit **1**: `3 file(s) out of sync` (3 actions, 408 unchanged, 68 skipped). Betroffen laut Log: `AGENTS.md` (managed block, 2x UPDATE) und `.claude/rules/commit-conventions.md` (COPY von `rules/1-generic/commit-conventions.md`). Ursache sichtbar: unversionierte Änderung an `rules/1-generic/commit-conventions.md` (anderer Agent, Working Tree: `M rules/1-generic/commit-conventions.md`). Ursache des `AGENTS.md`-Drifts nicht isoliert. |

## AC-Tabelle

Legende: PASS = durch gelaufenen Test belegt; PASS* = statisch belegt (Datei/Test existiert, aber im Lauf nur indirekt oder nicht einzeln geprüft); GAP = nicht belegt.

| AC | Evidenz | Status |
|---|---|---|
| 1 | `tests/test_git_template_commit_trailer_rule.py::test_git_template_states_trailer_precedence`, `::test_git_template_version_and_precedence_wording`; `agents/1-generic/git.md:3` `version: "2.2.0"` | PASS |
| 2 | `test_git_template_commit_trailer_rule.py::test_git_template_states_trailer_precedence` (Co-Authored-By 1x, `verbatim`) | PASS |
| 3 | `test_commit_trailers.py::test_render`, `::test_core_variables_without_key`; `test_auto_commit_block_render.py::test_default_block_byte_identical_without_trailers`. Byte-Identität des Renders von `developer`/`release`/`orchestrator` nicht per eigenem Test belegt (nur Block-Ebene) | PASS* |
| 4 | `test_git_template_commit_trailer_rule.py::test_git_template_renders_config_trailers_verbatim`. Ob der Test jeden aktiven Provider einzeln rendert, nicht geprüft | PASS* |
| 5 | `test_auto_commit_block_render.py::test_trailers_rendered_once_before_bom_for_each_authority` | PASS |
| 6 | `test_trailers_rendered_once_before_bom_for_each_authority` (Zeilen 250-251: delegate, kein "End your own") | PASS |
| 7 | `test_auto_commit_block_render.py::test_suggest_and_custom_with_trailers` | PASS |
| 8 | `test_auto_commit_block_render.py::test_no_trailer_line_when_disabled_or_misconfigured` | PASS |
| 9 | `test_commit_trailers.py::test_validate_format_violation_is_error` | PASS |
| 10 | `test_commit_trailers.py::test_validate_missing_email_is_warning_only`, `::test_warnings_co_authored_by_without_email` | PASS |
| 11 | `test_commit_trailers.py::test_validate_duplicates_and_unknown_key_fail` (parametrisiert) | PASS |
| 12 | `test_commit_trailers.py::test_violations_empty_for_valid` und `::test_violations_messages`; `None`/fehlender Block-Fall nicht per Testname verifiziert | PASS* |
| 13 | `test_commit_trailers.py::test_core_variables_invalid_commit_block_no_raise`, `::test_core_variables_invalid_auto_commit_branch_empty_list` (Plain-Sync-Exit 0 nicht per CLI-Lauf geprüft) | PASS* |
| 14 | `tests/test_admin_server.py::...::test_commit_whitelisted` (Zeile 3681) | PASS |
| 15 | `tests/test_admin_server.py::...::test_valid_commit_written` (Zeile 3684) | PASS |
| 16 | `tests/test_admin_server.py::...::test_invalid_commit_rejected_without_write` (Zeile 3692) | PASS |
| 17 | `tests/test_admin_ui_commit_section.py::test_route_sidebar_and_help_wired`, `::test_view_saves_commit_section_via_textarea`, `::test_view_is_accessible`. Help-Mappings-Checker nicht separat ausgeführt | PASS* |
| 18 | `tests/test_provider_agnostic_dispatch.py` (inkl. `test_no_provider_literal_usage_in_lib`) im ergänzenden Lauf grün | PASS |
| 19 | Tests grün, aber nicht gegen Python 3.9 ausgeführt (Plan Step 4) | GAP |
| 20 | ac01-, Slimming-, Drift-, Release-Checksum- und Context-Budget-Tests nicht ausgeführt; `--check` Exit 1 (Drift, vermutlich durch fremde Working-Tree-Änderung); "ac01-Hashes ändern sich nur für git" nicht geprüft | GAP |
| 21 | `CHANGELOG.md:15` (`commit.trailers`, Default, auto_commit-Block, Admin-Sektion, "Migration: without the key behaviour is unchanged"); explizites "Nicht-Breaking"/"### Added"-Heading nicht per Test geprüft | PASS* |

Zusammenfassung: 13 PASS (AC 1, 2, 5-11, 14-16, 18), 6 PASS* (AC 3, 4, 12, 13, 17, 21), 2 GAP (AC 19, 20) = 21.

## GAP-Liste (nicht behoben)

1. **AC 19 / Plan Step 4:** Kein Lauf gegen Python 3.9; Gesamtlauf `python3 -m pytest -q` nicht ausgeführt.
2. **AC 20 / Plan Step 2:** Nicht ausgeführt: `test_provider_agnostic_dispatch.py` vollständig (nur gefiltert), `test_context_budgets.py`, `test_ac01_render_identity.py`, opencode-v2-surface-Tests, `test_template_slimming_equivalence.py`, release-gate-checksums-Tests, Drift-Tests.
3. **AC 20 / Plan Step 3:** `--check` Exit 1 (3 Dateien out of sync: `AGENTS.md` x2, `.claude/rules/commit-conventions.md`). Teilursache: uncommitted Edit an `rules/1-generic/commit-conventions.md` (fremder Agent, siehe Task-Rahmen). `AGENTS.md`-Drift nicht analysiert. Nicht ausgeführt: `--validate-spec-plan`, `--render-standalone --check` (Standalone-Entsprechung von `git.md` ungeprüft).
4. **Plan Step 1:** `tests/test_admin_server.py` (komplett), `tests/test_auto_commit_block_render.py` (komplett), `tests/test_admin_ui_git_section.py` nur teilweise/gar nicht laufen gelassen (nur `-k`-gefiltert bzw. nicht).
5. Schwache Belege (PASS*): AC 3 (Rollen-Byte-Identität), AC 4 (alle Provider), AC 12 (`None`-Fall), AC 13 (CLI-Exit 0), AC 17 (Help-Mappings-Checker), AC 21 ("Nicht-Breaking"-Wortlaut).

## Plan-Checkbox

Task-10-Checkbox in `docs/plans/2026-11-15-git-trailer-contract-plan.md` **nicht** gesetzt: AC 19 und 20 sind nicht belegt (GAP 1-3), `--check` ist rot.
