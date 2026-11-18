---
pipeline_stages: {implement: 1}
status: APPROVED (User, 2026-11-17, Wahl A — nur C3 Issue-Hygiene; E-08 explizit freigegeben)
date: 2026-11-17
trace: [bug-backlog-hygiene]
---

# Issue-Hygiene C3 — Beleggestütztes Schließen bereits gefixter Bugs

> Status: APPROVED (User, 2026-11-17, Wahl A — nur C3 Issue-Hygiene; E-08 explizit freigegeben). Rein prozessualer S-Plan: kein Code, kein Commit, kein Branch, kein `sync.py`, kein Rebaseline, kein Push/Tag.
> Basis: `CHANGELOG.md` §`[2.0.0-beta.9] - 2026-11-16` (PRs #1284/#1287/#1282/#1291–#1295), `.tmp/audit/open-bug-issues-2026-11-17.md`, `.tmp/audit/bug-cluster-hebel-2026-11-17.md` (Cluster C3), `docs/plans/2026-11-16-bug-backlog-working-plan.md` §3.1–3.4, `docs/plans/2026-11-14-bugfix-batch-3-plan.md`.
> Issues: Kandidaten #1249, #1252, #1260, #1270, #1168, #1261 (teilw.), #1197 (Overlap). Blockiert, strikt unangetastet: #854, #860, #1032, #971.
> Spec: S-Klasse (prozessuale Issue-Arbeit, kein Artefakt nötig). Freigabe = E-08 / Wahl A des Nutzers (siehe `status:`). Dieser Plan beschreibt ausschließlich Prüfung + Kommentar + Close — er führt nichts davon selbst aus.

---

## 1. Ziel & Scope

Ziel: Von den 18 offenen Bug-Issues (Inventar `.tmp/audit/open-bug-issues-2026-11-17.md` §3) genau diejenigen **mit Beleg** schließen, die in `2.0.0-beta.9` bereits gefixt wurden und am 17.11. in der GitHub-Ansicht noch `OPEN` sind. Delta CHANGELOG ↔ GitHub ist die Arbeitsliste, nicht ein neuer Fix-Bedarf (Hinweis `.tmp/audit/bug-cluster-hebel-2026-11-17.md` §1/§5).

Scope (Global Constraints — gelten für alle Schritte):
- **Kein Code, kein Commit, kein Branch, kein `sync.py`, kein Rebaseline, kein Push/Tag/Branch-Management.** Reine Issue-/Kommentar-Arbeit.
- **Nur die gelisteten Kandidaten anfassen.** #854, #860, #1032, #971 sind BLOCKED und werden nicht gelesen, nicht kommentiert, nicht geschlossen.
- **Beleg vor Aktion** (Abschnitt 3): ohne Beleg bleibt das Issue offen und wird nur dokumentiert.
- **Keine Closing-Keywords** in Kommentaren (`Fixes`/`Closes`/`Resolves` verboten); stattdessen `Refs #<PR>`. Das Schließen erfolgt ausschließlich über einen expliziten `gh issue close`.
- **Nicht doppelt planen:** Issues mit Rest-Scope (#1261, #1249-Rest bei #1257, #1197) werden nicht als „fixbedürftig" in C1/C2/C4 übernommen; dieser Plan regelt nur die Hygiene.
- Anti-Recursion (kein Worker delegiert an `orchestrator` zurück), **kein** `isolation: "worktree"`, Repo-Containment (Schreiben nur in Projektwurzel / `.tmp/`).
- Falls `gh`/`git` zur Ausführungszeit nicht verfügbar sind (wie in der Audit-Session) → gilt „kein Beleg" → Issue bleibt offen, documentierter Grund „Werkzeug nicht verfügbar".

---

## 2. Kandidaten

Kandidatenliste (aus E-08 / Wahl A; Bewertung teils noch `ungeprüft` laut working plan §3.3/§3.4):

| Issue | Thema | Beleg-Lage laut CHANGELOG beta.9 | Verdikt (vorgesehen) |
|---|---|---|---|
| #1249 | opencode v2 Gate advisory unter `topology: subagent` | Doc-Fix `docs/providers/opencode.md` via #1287 (Zeile 25); Tier-Fold bewusst bei #1257 (E-4) | **schließen mit Beleg** — Kommentar muss Rest bei #1257 explizit nennen |
| #1252 | unbekanntes `hook_protocol` fällt auf Claude-Writer zurück | Code-Fix #1287 (Zeile 20), `scripts/lib/hooks.py` Writer-Tabelle + WARN | **schließen mit Beleg** |
| #1260 | viz-logger trotz `viz.enabled: false` in `.mcp.json` | Code-Fix #1284 (Zeile 27), `scripts/lib/registry_query.py` + `.meta-config/project.yaml` | **schließen mit Beleg** |
| #1270 | 702 Sync-Backups, Retention wirkungslos | Code-Fix #1287 (Zeile 22), `sync_pipeline.py` + `generated_file_drift.py` | **schließen mit Beleg** |
| #1168 | git-Agent schreibt falschen Co-Authored-By-Trailer | Fix via E-19 / `git` 2.2.0, #1282 (Zeile 8); konfigurierbare Trailer, Präzedenz in `git.md` | **schließen mit Beleg** |
| #1261 | ReqogniLoom doppelt eingebunden (Katalog vs. Plugin) | **nur WARN** #1287 (Zeile 17); Rest Env-Namen/Auth/Prosa IC-6 offen (working plan §5) | **teilw. — offen lassen**, Rest dokumentieren, kein Close |
| #1197 | `{{PROJECT_CONTEXT}}` 2–3× gerendert (Overlap C1/C4) | kein Eintrag in beta.9 → Code-Fix nicht belegt | **offen lassen**, „Code-Fix fehlt", Overlap C1/C4 vermerken |

Blockiert — **nicht anfassen**: #854, #860 (extern, Antigravity SIGILL/non-pclmul), #1032 (im working plan als blocked gelistet), #971 (BLOCKED-BY-DECISION, kein Akzeptanzkriterium).

Hinweis: Alle Kandidaten sind in `docs/plans/2026-11-16-bug-backlog-working-plan.md` §3.3/§3.4 als `ungeprüft` markiert. Die CHANGELOG-Zeilen oben sind **Hinweise**, kein Ersatz für den verpflichtenden Belegcheck (Abschnitt 3).

---

## 3. Beleg-Gate (verbindlich)

Ein Issue darf **nur dann** geschlossen werden, wenn **beide** Bedingungen erfüllt sind:

- **(a) Fix im Code mit `Datei:Zeile` belegt.** Bei reinen Doku-Fixes (namentlich #1249) genügt die Doku-`Datei:Zeile` (z. B. `docs/providers/opencode.md`, Absatz zu tier `plugin` + `topology: subagent`). Nicht ausreichend: reine Issue-Kommentare, Plan-Einträge oder „laut Agent-Befund".
- **(b) Gemergter Commit in beta.9 nachgewiesen** — mindestens eines: Commit-Hash (aus `git log`/`git show`) **oder** PR-Nummer (`Merge pull request #NNNN`) **oder** CHANGELOG-Eintrag unter `[2.0.0-beta.9] - 2026-11-16`.

Entscheidungsregel:
- **(a) und (b) erfüllt** → sachlicher Kommentar (Abschnitt 4) + explizites `gh issue close`.
- **nur (a) oder nur (b) oder keines** → Issue bleibt OPEN; kein Close; im Bericht als „weiter offen / Code-Fix fehlt" (bzw. „Beleg unvollständig") dokumentieren.
- **teilweiser Fix** (#1261, #1249-Rest) → kein Close; im Bericht „weiter offen / Rest: …" mit konkreter Restbeschreibung und Verweis auf das zuständige Issue (#1257 bzw. Nutzerentscheidung working plan §5).

Der Beleg wird pro Issue in `.tmp/audit/issue-hygiene-belege-2026-11-17.md` festgehalten (nur `.tmp/`, kein Plan-/Repo-File): Issue-Nr, (a) `Datei:Zeile`, (b) Hash/PR/CHANGELOG-Zeile, Resultat (geschlossen / offen + Grund).

---

## 4. Vorgehen

Reihenfolge: zuerst alle read-only Belegchecks (Batch), danach gebündelt Kommentare + Closes. Pro Kandidat identisch:

**Schritt A — read-only Belegcheck** (Rollen `explorer`/`code-reviewer` für (a), `git` für (b)):
1. Code-/Doku-Beleg suchen: `Datei:Zeile` zum Fix ermitteln (z. B. #1252 `scripts/lib/hooks.py` Writer-Tabelle; #1260 `scripts/lib/registry_query.py` + `plugins.viz-logger.enabled`; #1270 `scripts/lib/sync_pipeline.py`/`generated_file_drift.py`; #1168 `git.md` Trailer-Präzedenz; #1249 `docs/providers/opencode.md`).
2. Merge-Beleg: `git log`/`git show` auf den betreffenden PR (#1284/#1287/#1282) prüfen; CHANGELOG-Zeile als zweiter Beleg notieren.
3. Ergebnis in `.tmp/audit/issue-hygiene-belege-2026-11-17.md` schreiben.

**Schritt B — bei Beleg (Rolle `feedback`):**
4. Sachlicher Kommentar via `gh issue comment <NR> --body "..."` mit: Fix-Beschreibung, `Datei:Zeile`, gemergtem PR/Commit und `Refs #<PR>`. **Keine** Closing-Keywords. Bei #1249 zusätzlich: „Tier-Fold bleibt bei #1257 (E-4)."
5. Explizites Schließen via `gh issue close <NR>`. Kein automatisches Schließen durch Keyword.

**Schritt C — ohne Beleg / teilweise:**
6. Kein Close, kein Kommentar mit Schließabsicht. Nur Belegdatei + Bericht („weiter offen / Code-Fix fehlt" bzw. „weiter offen / Rest: …"). Für #1261: Rest (Env-Namen `REQOGNILOOM_*` vs. `MCP_REQOGNILOOM_*`, Auth-Schema, Prosa IC-6) als offen vermerken. Für #1197: Overlap mit C1/C4 vermerken, nicht hier schließen.

Reihenfolge der Präsentation im Bericht: #1249, #1252, #1260, #1270, #1168, #1261, #1197. Blockierte (#854, #860, #1032, #971) werden nicht geprüft und nicht erwähnt außer als „nicht angefasst (blocked)".

---

## 5. Rollen

| Rolle | Aufgabe in diesem Plan | Grenze |
|---|---|---|
| `explorer` / `code-reviewer` | Code-/Doku-Beleg (a): `Datei:Zeile` des Fixes im Stand beta.9 ermitteln | read-only; kein Edit, kein Close |
| `git` | Merge-Beleg (b): `git log`/`git show` auf #1284/#1287/#1282, Commit-Hash/PR bestätigen | **nur lesend**; kein Commit, kein Push, kein Tag, kein Branch |
| `feedback` | `gh issue comment` (sachlich, `Refs #<PR>`, keine Closing-Keywords) + `gh issue close` | nur für Issues mit erfülltem Beleg-Gate |

- Jeder Schritt mappt auf genau eine Rolle; keine Rolle führt fremde Aktionen aus.
- Anti-Recursion: kein Worker delegiert an `orchestrator` zurück. Kein `isolation: "worktree"`. Repo-Containment: einzig zulässiger Schreibpfad ist `.tmp/audit/issue-hygiene-belege-2026-11-17.md`.
- Kein `git`-Agent-Schreibzugriff, kein `sync.py`, kein Testlauf, kein Rebaseline — dieser Plan erzeugt ausschließlich Issue-Kommentare/-Closes und eine `.tmp/`-Belegdatei.

---

## 6. Erfolgskriterium + Berichtspflicht

Erfolgskriterium (messbar):
- Für jeden der 7 Kandidaten existiert ein Eintrag in `.tmp/audit/issue-hygiene-belege-2026-11-17.md` mit (a) `Datei:Zeile`, (b) PR/Hash/CHANGELOG-Zeile und Resultat.
- Die Anzahl der tatsächlich geschlossenen Issues entspricht genau der Anzahl Kandidaten mit (a) **und** (b) — erwartet: #1249, #1252, #1260, #1270, #1168 (5 Close-Kandidaten, Beleg vorausgesetzt).
- Kein blocked Issue (#854, #860, #1032, #971) wurde kommentiert oder geschlossen.
- Kein Kommentar enthält `Fixes`/`Closes`/`Resolves`; jeder Contains `Refs #<PR>`.

Berichtspflicht (deutscher Abschlussbericht an Nutzer/Orchestrator):
1. **Geschlossen:** Anzahl + Nummern (z. B. „5 geschlossen: #1249, #1252, #1260, #1270, #1168").
2. **Weiter offen:** Anzahl + Nummern + Grund je Issue (z. B. „#1261 — nur WARN gelandet, Rest Env/Auth/Prosa offen"; „#1197 — Code-Fix fehlt, Overlap C1/C4").
3. **Nicht angefasst:** #854, #860, #1032, #971 (blocked).
4. **Planpfad:** `docs/plans/2026-11-17-issue-hygiene-beleg.md`.
5. **Belegdatei:** `.tmp/audit/issue-hygiene-belege-2026-11-17.md`.

---

## File Structure (Referenzen, keine Änderungen)

- Lesend: `.tmp/audit/open-bug-issues-2026-11-17.md` (Inventar 18 Bugs), `.tmp/audit/bug-cluster-hebel-2026-11-17.md` (C3), `docs/plans/2026-11-16-bug-backlog-working-plan.md` §3.1–3.4 (Stand/ungeprüft), `docs/plans/2026-11-14-bugfix-batch-3-plan.md` (Batch-3-Herkunft), `CHANGELOG.md` (beta.9).
- Schreibend (nur zur Laufzeit, nicht durch diesen Plan): `.tmp/audit/issue-hygiene-belege-2026-11-17.md` — Belegnachweis pro Kandidat.
- Extern (GitHub, durch Rolle `feedback`): Issue-Kommentare + Closes der Kandidaten. Kein Repo-File, kein Code, kein Rebaseline.

## Self-Review

- Jeder Task mappt auf genau eine Rolle; jedes Akzeptanzkriterium ist messbar (Anzahlen, Nummern, `Datei:Zeile`, `Refs #<PR>`).
- Kein Code/Commit/Branch/`sync.py`; Beleg-Gate verhindert ungeprüftes Schließen; blocked Issues explizit ausgenommen.
- `pipeline_stages: {implement: 1}` deckt die einzige Stage (`implement`) des S-Plans ab; `Files:`/`Interfaces:` sind über Abschnitt 5/File Structure vollständig beschrieben, keine Dateiüberlappung.
