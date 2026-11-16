# Arbeitsplan Bug-Backlog (Draft)

Status: DRAFT
Datum: 2026-11-16
Bezug: docs/plans/2026-11-15-master-roadmap.md (DRAFT, Arbeitsgrundlage), docs/superpowers/plans/2026-11-10-backlog-roadmap.md

Quelle: Session-Stand 2026-11-16 (Agent-Berichte). Nicht gegen GitHub-Issues oder `main` nachgeprüft, sofern nicht anders vermerkt.
Legende: `ungeprüft` = Agent-Befund ohne Beleg (Datei:Zeile + gemergter Commit). Klassen: S/M/L/XL (Classify-Route).

## 1. Ziel

- Bugs des Systems über definierte Pläne bzw. GitHub-Issues abarbeiten.

## 2. Vorgehen

- Orchestrator dispatcht. Analyse zuerst read-only.
- Umsetzung erst nach Klassifizierung (S/M/L/XL). Bei M/L/XL erst nach Spec mit `Status: APPROVED`.
- S-Bugs bündeln, dateidisjunkt parallel. `guard-impl`-Datei nie parallel.
- Rebaseline-Kette: #1246 -> #1237 (Helper) -> alle rebaseline-lastigen PRs.
- Issues nur mit Beleg (Datei:Zeile + gemergter Commit) schließen.
- PRs ohne Closing-Keywords; Verweise per "Related" bzw. "Refs".
- Merges: durch Main Chat über den `git`-Agenten, nur bei grüner CI/MERGEABLE, Merge-Commit, kein Admin/Force/Auto. Nutzerdelegation 2026-11-16, direkt im Main Chat. Der Nutzer mergt auch selbst.
- Subagenten-Befunde gelten als `ungeprüft`, bis belegt. Belegcheck vor dem Bauen, weil viele Issues teils schon gefixt waren.

## 3. Stand 2026-11-16

### 3.1 Gemergt auf main

- #1284, #1287
- #1288 (nur Spec)
- #1290 (Spec temp-root, APPROVED)
- #1291 (Impl #1246 / #1261-WARN)
- #1292 (#1289)
- #1293
- #1294 (Helper-Spec, APPROVED)
- #1295 (Docs)
- origin/main = 74383b15

### 3.2 Geschlossen

- #1259, #1266, #1271, #1258, #1246, #1289

### 3.3 Status ungeprüft

- #1142, #1241: sollen mit Beleg geschlossen werden. Status ungeprüft.
- #1261: bewusst offen. Rest: Variablennamen/Auth-Angleichung, Prosa-Ersatz IC-6. Doku-Schritt per #1295 erledigt (ungeprüft).
- #1237 (Rebaseline-Helper): lokaler WIP-Commit 4ab9ab53 auf Branch `feat/rebaseline-helper`. Nicht gepusht, kein PR. Tasks 0-10 ungeprüft. Code-Review und OF-9-Probelauf auf Scratch-Kopie stehen aus (beide wegen API-Limit abgebrochen).

### 3.4 Offen / gated

- #1260: Restlücke. Design-Entscheidung und Rebaseline, hinter #1237.
- IC-6: agent-hint-Prosa. S-PR mit Rebaseline.
- Config-Kette: #1187 -> #1198 -> #1186 -> #1199. #1141 nach #1181. #1198, #1197, #1199, #1141 hängen daran.
- #1203 -> #1188 -> #1204.
- #1201: Spec DRAFT.
- #1180: Lösungsvariante offen.
- Hook-Welle: #1210, #1217, #1169, #1238, #1250. `guard-impl` sequentiell.
- Restpunkte: #1270, #1249, #1252 (Bezug #1257).
- Check-Footer gegen Config fehlt: #1168, #1247.
- #1176, #1172 offen (Status ungeprüft).
- Blocked, nicht anfassen: #860, #854, #1032.

## 4. Nächste Schritte

1. #1237: WIP prüfen. OF-8 (Verhalten von `--validate-spec-plan`) und OF-9 (Probelauf auf Scratch-Kopie vor Task 11) abarbeiten. Code-Review. PR mit "Refs #1237 / #1115". CI grün. Merge.
2. Danach Rebaseline-lastige Welle in Roadmap-Reihenfolge (P6, P8, P12, P17, P19, ...). #1187 muss vom Nutzer wieder geöffnet werden (E-20).
3. Gate-freie S-Kandidaten und Issue-Hygiene (Schließen mit Beleg).
4. Checkbox-Hygiene der Pläne (Phase B/C, Trailer-Plan) als eigener Docs-PR.

## 5. Offene Entscheidungen (Nutzer)

- #1261 Reststücke: Variablennamen `REQOGNILOOM_*` vs. `MCP_REQOGNILOOM_*`, Auth-Schema.
- #1260 Design: `viz.enabled`-Kopplung.
- Helper-Spec OF-2/3/4/7: Vorschlag, den Spec-Empfehlungen zu folgen.
- Löschen des veralteten Remote-Branches `docs/rebaseline-helper-spec`.
- Aufräumen von `.tmp/runs` und `.tmp/pytest-pidfile3` (gitignoriert).

## 6. Betrieb und Grenzen

- 5h-API-Limit hat die Arbeit unterbrochen. Reset 21:30 Europe/Berlin.
- Fortsetzung über den `orchestrator` (Resume per SendMessage).
- Ungeprüft:
  - Testläufe auf `main` nach den letzten Merges.
  - `sync.py --check`-Drift (22 Dateien, nicht von PR3).
  - macOS/Windows-Verhalten von #1246.
