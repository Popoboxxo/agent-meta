# Opencode v2-Support — Ausführungsstatus (Plan B / Issue #1007)

**Zweck:** Ausführungs-Ledger zum Plan `docs/plans/2026-10-22-opencode-v2-support-plan.md` (Phasen C0, B, C1/C2, C3, D) und damit zum Tracking-Issue #1007. Das Dokument hält je Phase und je C0-Task den erreichten Stand, die Beleg-Commits, die Testlage und die substanziellen Befunde fest; es ersetzt weder Plan noch Spec.

**Geltungsbereich:** Branch `feat/1007-c0-spike` (Basis `main` = `9ccc27c8`, Plan A gemergt über PR #1010). Stand: 2026-10-23; Ledger-Commit `52a72a0f`; Evidenz-Nachbesserung `2978753c`.

**Datenquelle:** Commits dieses Branches, die im Plan gesetzten Checkboxen (Tasks 1, 2, 3, 3a, 24) sowie die dort protokollierten Testläufe.

**Legende der Spaltenwerte**

| Spalte | Werte |
|---|---|
| `Status` (Task) | `done` = alle Steps erledigt und committet · `done (Review/PR offen)` = Arbeit abgeschlossen, Review bzw. PR steht aus · `offen` = nicht begonnen |
| `Status` (Phase) | wie oben, auf Phasenebene aggregiert |
| `Tests` | letzter belegter Testlauf; `7 failed` = erwarteter Rot-Lauf (red-before-green) · `—` = im Ledger kein Testlauf überliefert |
| `Abweichungen/Befunde` | substanzielle Ergebnisse, die über den Planwortlaut hinausgehen oder ihn präzisieren |

## Phasenübersicht

| Phase | Tasks | Status |
|---|---|---|
| C0 | 1, 2, 3, 3a, 24 | `done (Review/PR offen)` |
| B | 4–12 | `offen` |
| C1/C2 | 13, 13a, 14–17 | `offen` |
| C3 | 18–19 | `offen` |
| D | 20–33 (ohne 24) | `offen` |

**Entry-Kriterien:** E1 done · E2 done · E3 done · E4 done.

## C0

| Task | Agent | Commit | Tests | Status | Abweichungen/Befunde |
|---|---|---|---|---|---|
| 1 | `tester` | `1c1cc31` | `7 failed` (erwarteter Rot-Lauf) | `done` | Struktur-Test für das Spike-Ergebnisdokument angelegt; bleibt rot bis Task 2. |
| 2 | `provider-expert` | `5eadea26` | — | `done` | `VERDICT-C3: GO` (reale Runtime-Proben auf v2.1.3). `VERDICT-FIELDS: AMEND`, weil `agents.title.model` UNVERIFIED ist. Review-Nachlauf QA-C0-04/RVW-C0-04: `Proben`-Zählweise im Spike präzisiert (je Frage höchstens eine Probe pro Inspektionskommando); die Zahlen bleiben unverändert (Q1 2, Q2 3, Q3 2, Q4 0, Q5 2, Q6 2). |
| 3 | `concept-specifier` | `80302a7` | `7 passed` | `done` | Amendment B1 in die Spec (Rev. 1.5) eingearbeitet: `agents.title.model`/AC-B9 entfällt; `providers`-Innenform korrigiert auf `settings.baseURL` + `env`; in `cli.json` nur `plugins` dokumentiert; verwaltete Deny-Tripel werden jetzt am **Ende** von `permissions[]` angehängt (last-match-wins); `plugins` im Plural; `timeout.startup` ergänzt. C0-Review-Nachlauf: OAuth-Bewusste-Einschränkung, AC-C2-Staging und die Ableitung der Agent-internen Reihenfolge präzisiert. |
| 3a | `tester` | `e340f0f` | `8 passed` | `done` | Der GO-Zweig prüft nur die Implikation „Keys vorhanden ⇒ GO“ (Äquivalenz folgt in Task 19). **Negativprobe reproduzierbar (Review QA-C0-11/RVW-C0-03/QA-C0-10):** in einer Wegwerf-Kopie des Repos (nicht committet) (1) im Spike-Dokument `VERDICT-C3: GO` durch `VERDICT-C3: NO-GO` ersetzen und (2) im Opencode-Eintrag von `config/ai-providers.yaml` `surface-plugin-protocols` **und** `surface-has-plugins` injizieren → `python3 -m pytest tests/test_opencode_v2_spike.py -q -k ac_c2` ergibt `1 failed` (Assertion „NO-GO verdict but the registry declares C3 keys“). Kontrolllauf: dieselbe Kopie ohne injizierte C3-Schlüssel, aber mit dem im Spike-Dokument ergänzten Satz „Fallback = Permissions-Tier“ → `1 passed`. |
| 24 | `provider-expert` | `31001cc1`, `2978753c` | `1 passed` (`-k ac_d8_evidence`), `16 passed` (Datei) | `done` | Evidenz trägt `ERGEBNIS: JSONC-TRAEGT-NICHTS-BEI`. Nachbesserung `2978753c` (`docs: verify opencode v2 jsonc loading behaviour`): v2.1.3 wurde nachträglich geprobt; das `ERGEBNIS` bleibt unverändert (`JSONC-TRAEGT-NICHTS-BEI`). Für den ursprünglichen Lauf wurde nur `opencode 1.19.3` verwendet. |

## Offene Punkte

- **OQ-B12** ist mit `VERDICT-C3: GO` an seinem Entscheidungszeitpunkt angelangt. Der dokumentierte Default „Eigenprüfung genügt (kein Eingriff in Spec A)“ gilt weiter, eine ausdrückliche Entscheidung steht jedoch noch aus.
- Die unabhängigen Stränge B, C1/C2 und D sind durch OQ-B12 nicht blockiert.

## Nächste Schritte

1. Review und PR für Phase C0.
2. Danach Phase B (Tasks 4–12), PR nach grüner CI.
