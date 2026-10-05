# Backlog-Abarbeitungsstatus — 2026-10-05

**STATUS:** in-progress
**Quelle:** `docs/plans/2026-10-04-prioritized-issue-backlog-plan.md`
**Basis:** `main` @ `57107459` (Merge von PR #894)

## Zusammenfassung

- Ursprünglich **39 priorisierte offene Issues** (5× P1, 23× P2, 11× P3).
- **25 abgeschlossen** (merged/closed), **14 offen** (innerhalb des Backlogs).
- Repo-weit: **76 offene Issues** (Stand 2026-10-05).
- Offene PRs: **#839** („docs(repo): consolidate repository documentation", Draft, *conflicting*, CI rot). Alle übrigen unten genannten PRs sind gemergt.

> **Verifikationshinweis:** Dieser Stand wurde aus der Git-Historie verifiziert
> (`git log --oneline --merges`, `gh pr list --state merged`, `gh issue list --state open`).
> Gegenüber dem ersten Snapshot sind **drei weitere Merges** eingeflossen: PR #892 (→ #847),
> PR #893 (→ #848) und PR #894 (→ #851). Auch PR #866 (Plan-Doku) ist gemergt.
> Reale Zahlen daher **25 abgeschlossen / 14 offen** (statt 22/17).

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
| #838 | Mini-Spec gemergt, **Implementierung offen** | PR #890 (`33fbbdba`) — Issue bleibt OPEN |
| #864 | merged/closed | PR #891 (`3e974d14`) |
| #847 | merged/closed | PR #892 (`cb709258`; Branch-Commit `9c45458a`) |
| #848 | merged/closed | PR #893 (`29fc9263`) |

## Abgeschlossen — Phase 3 (Provider-Capabilities, bisher)

| Issue | Status | PR / Commit |
|---|---|---|
| #851 | merged/closed | PR #894 (`57107459`) |

## Offen (14)

- **Phase 2:** #838 (Implementierung)
- **Phase 3:** #852, #853, #854, #855, #856, #857, #858
- **Phase 4:** #863
- **Phase 5:** #844, #552
- **Phase 6:** #859, #860, #603

## Nächste Schritte

1. **#838**-Implementierung nach der gemergten Mini-Spec (PR #890).
2. **#839** auflösen: Draft-PR, `CONFLICTING`, CI rot — rebasen/grün machen oder schließen.
3. Phase 3 (pro Provider ein PR): #852–#858.
4. Phase 4–6: #863, #844/#552, #859/#860/#603.

## Hinweise / Follow-ups

- Untracked bleiben bewusst untracked: `.playwright-mcp/` sowie `issue838-*.yml`.
- Offene PRs Stand 2026-10-05: **#839** (Draft, conflicting, CI rot).
- Verifikationsbasis: `git log --oneline --merges`, `gh pr list --state merged`, `gh issue list --state open`.
