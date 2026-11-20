# Backlog-Abarbeitungsstatus — 2026-10-05

**STATUS:** complete (Track A final)
**Quelle:** `docs/plans/2026-10-04-prioritized-issue-backlog-plan.md`
**Basis:** `main` @ `57107459` (Merge von PR #894)

## Zusammenfassung

- Ursprünglich **39 priorisierte offene Issues** (5× P1, 23× P2, 11× P3).
- **33 abgeschlossen** (merged/closed), **6 offen/parked** (innerhalb des Backlogs).
- Repo-weit: **76 offene Issues** (Stand 2026-10-05).
- PRs: **#839** („docs(repo): consolidate repository documentation", Draft, *closed*, nicht gemergt) — orchestrator-entschieden. Alle übrigen unten genannten PRs sind gemergt.

> **Verifikationshinweis (Final):** Dieser Stand wurde aus der Git-Historie verifiziert
> (`git log --oneline --merges`, `gh pr list --state merged`, `gh issue list --state open`).
> Track-A-Abschluss am 2026-10-06: Alle ausstehenden PRs gemergt (PR #901, #904, #905, #906,
> #907, #908), Orchestrator entschied über #839 (geschlossen ohne Merge).
> **Finale Zahlen: 33 abgeschlossen / 6 parked/offen** (Track A: 8/14 weitere Merges).

## Abgeschlossen — Phase 0 (Hygiene)

| Issue | Status | PR / Commit |
|---|---|---|
| #826 | merged/closed | PR #867 (`43ca7e1d`) |
| #861 | done (Branch gelöscht, kein PR) | — (per Kommentar geschlossen, Arbeit via PR #846) |
| #842 | merged/closed | PR #868 (`790ef517`) |
| #850 | merged/closed | PR #870 (`dc7e4f21`) |

## Abgeschlossen — Phase 1 (P1-Blocker)

| Issue | Status | PR / Commit |
|---|---|---|
| #831 | merged/closed | PR #871 (`c60a6272`) |
| #862 | merged/closed | PR #872 (`b7d2d8a0`) |
| #802 | merged/closed | PR #873 (`145bb02e`) |
| #767 | merged/closed | PR #874 (`b5bfa2cf`) |
| #843 | merged/closed | PR #875 (`a35c5386`) |

## Abgeschlossen — Phase 2 (Sync-/Gate-Konsistenz)

### F-Serie (#803–#812)

| Issue | Status | PR / Commit |
|---|---|---|
| #803 | merged/closed | PR #876 (`e28f62f5`) |
| #804 | merged/closed | PR #878 (`ca709440`) |
| #805 | merged/closed | PR #879 (`0d1dfb50`) |
| #806 | merged/closed | PR #880 (`2c60fbe6`) |
| #807 | merged/closed | PR #881 (`fae20461`) |
| #808 | merged/closed | PR #882 (`9f102549`) |
| #809 | merged/closed | PR #883 (`35094401`) |
| #810 | merged/closed | PR #884 (`31df9fae`) |
| #811 | merged/closed | PR #886 (`f35cbf32`) |
| #812 | merged/closed | PR #887 (`dbdf433c`) |

### Weitere Phase-2-Issues

| Issue | Status | PR / Commit |
|---|---|---|
| #849 | merged/closed | PR #888 (`3c169f7c`) |
| #834 | merged/closed | PR #889 (`c3648811`) |
| #838 | merged/closed | PR #890 (`33fbbdba`, spec) + PR #901 (implementation) |
| #864 | merged/closed | PR #891 (`3e974d14`) |
| #847 | merged/closed | PR #892 (`cb709258`; Branch-Commit `9c45458a`) |
| #848 | merged/closed | PR #893 (`29fc9263`) |

## Abgeschlossen — Phase 3 (Provider-Capabilities)

| Issue | Status | PR / Commit |
|---|---|---|
| #851 | merged/closed | PR #894 (`57107459`) |
| #852 | merged/closed | PR #904 (mammouth cluster) |
| #853 | merged/closed | PR #904 (mammouth cluster) |
| #855 | merged/closed | PR #905 (copilot) |
| #857 | merged/closed | PR #904 (mammouth cluster) |

## Abgeschlossen — Phase 4 (UI)

| Issue | Status | PR / Commit |
|---|---|---|
| #863 | merged/closed | PR #906 (admin-ui) |

## Abgeschlossen — Phase 5 (Context-Kompression & andere)

| Issue | Status | PR / Commit |
|---|---|---|
| #844 | merged/closed | PR #908 (context compression) |

## Abgeschlossen — Phase 6 (Changelog & Gates)

| Issue | Status | PR / Commit |
|---|---|---|
| #859 | merged/closed | PR #907 (changelog) |

## Offen/Parked (6)

### Parked — Design/Product-Entscheidung erforderlich (2)

- **#854:** Antigravity-Befehls-Kontrakt mehrdeutig — Entscheidung erforderlich, ob Antigravity custom slash commands unterstützt (Option A: emit vs Option B: downscope).
- **#858:** Codex/Continue-Skills mit null Artifacts deklariert — Entscheidung erforderlich (Option A: emit skills, Scope erweitern vs Option B: downscope Deklaration auf Realität).

### Parked — Code-Änderung nicht erforderlich, Schließung empfohlen (3)

- **#856:** ZC-2 bereits via #807 behoben; ZC-1 dokumentiert als „P6 real-repo-test" (ausstehend), kein Code-Fix möglich.
- **#552:** Vollständig bereits gelöst — 88/88 Templates kompatibel seit 2026-09-06, test_contract_labels.py green, keine Abweichungen.
- **#603:** Vollständig bereits implementiert — SHA-256-Checksummen-Verifizierung in pre-release-check.sh + hook_plugins.py, dokumentiert in docs/RELEASE_GATES.md.

### Parked — Blockiert durch externe Infrastruktur (1)

- **#860:** Benötigt pclmul-fähigen Host zur Antigravity-Runtime-Verifikation (nicht verfügbar in dieser Umgebung).

## Geschlossen ohne Merge (1)

- **#839:** („docs(repo): consolidate repository documentation") — Draft-PR, conflicting, CI rot. Orchestrator-Entscheidung: nicht gemergt, per Session-Dokumentation begründet.

## Track B — Bugfix-Wave-Plan

**Status:** `docs/plans/2026-10-06-bugfix-wave-plan.md` ist als Planungsdokument APPROVED und gemergt.
**Implementierungsfortschritt:** 0/52 Issues. Implementierungsphase beginnt nach Abschluss von Track A.

## Nächste Schritte

1. **Track A abgeschlossen:** 33/39 Issues abgearbeitet, 6 parked (Entscheidung/externe Infrastruktur erforderlich).
2. **#854, #858:** Produktentscheidungen erforderlich (Antigravity-Kontrakt, Codex/Continue-Scope).
3. **#856, #552, #603:** Empfehlung: schließen (Code-Änderung nicht erforderlich, bereits erledigt/dokumentiert).
4. **#860:** Ausstehend — pclmul-fähige Infrastruktur erforderlich.
5. **Track B starten:** Nach Abschluss von Track A (33/39): Bugfix-Wave-Plan mit 52 Issues implementieren.

## Hinweise / Follow-ups

- Untracked bleiben bewusst untracked: `.playwright-mcp/` sowie `issue838-*.yml`.
- Offene PRs Stand 2026-10-05: **#839** (Draft, conflicting, CI rot).
- Verifikationsbasis: `git log --oneline --merges`, `gh pr list --state merged`, `gh issue list --state open`.
