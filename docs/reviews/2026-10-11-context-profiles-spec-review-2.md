# Re-Review: SPEC-CONTEXT-PROFILES-2026-10-11 (Rev. 3, DRAFT)

- **Gegenstand:** `docs/specs/2026-10-11-context-profiles-spec.md` (Rev. 3, 2201 Zeilen, vollständig gelesen)
- **Vorreview:** `docs/reviews/2026-10-11-context-profiles-spec-review.md` (Rev. 2.2, REVISE; B-1…B-6, W-1…W-10, H-1…H-10)
- **Reviewer:** concept-reviewer (Spec-Review-Modus), 2026-10-11
- **Verdikt:** **REVISE** (CHANGES_REQUESTED) mit 1 BLOCKER, 7 WARNUNGEN und 4 HINWEISEN. Der Änderungsumfang ist eng
  begrenzt; eine Rev. 3.1 genügt.
- **Nicht neu verhandelt (entschieden):**
  - `meta-doctor` mit Bash; `meta-optimizer` nur mit Read/Glob/Grep/TodoWrite und nur als Vorschlag; Anwendung
    nach Nutzerfreigabe durch `agent-meta-manager`.
  - AC-01 Variante (a); eine Spec; Q12/Q18/D-1.
  - Eval nur nach Freigabe (`SKIPPED-BY-USER`); Q16 vertagt (#958).
  - Die Findings unten betreffen nur die Umsetzbarkeit dieser Entscheidungen.

## 1. Formale Spec-Checks

| Check | Ergebnis |
|---|---|
| Pflichtsektionen (§1, §5, §6, §8, §12) | vorhanden |
| Trace-Anker | vorhanden (Frontmatter, Z. 20, Z. 2200) |
| Approval-Marker | `status: DRAFT`, Revision 3: konsistent |
| No-Placeholder | Rest-Platzhalter `name_only_reason: <Text>` in nicht als ersetzt markierten Rev.-2-Zeilen (Z. 1127, 1356), obwohl Rev. 3 die Texte liefert (Z. 1109, 1388), siehe N-8 |

## 2. Vorreview-Punkte

| Punkt | Status | Beleg in Rev. 3 / Rest |
|---|---|---|
| B-1 inaktive Rollen/Provider | behoben (Nutzerentscheidung) | `inactive-scope` + Universe-Prüfung: IC-24 Z. 1223-1229, IC-18 Nr. 13, QG-11 (g), AC-83, R15 |
| B-2 `fill_defaults`-Re-Fill | behoben | `refill_keys` aus denselben Funktionen, `info-only` Z. 1230-1237; Beweis ohne Auto-Fill Z. 1277-1278, 1322-1324; AC-82. Code bestätigt: `config.py:960-1024`, `sync_pipeline.py:152` |
| B-3 Laufzeit-Leser / Hunk-Vertrauen | teilweise | Neuberechnung + Remove-only Z. 1270-1276, AC-80; Lücke: IC-35 unvollständig (`admin-ui.*`), siehe N-3 |
| B-4 Doctor read-only | behoben | K-g; IC-22 Z. 1051-1062; IC-21 Z. 941; IC-23 Z. 1093-1103; AC-39 (a)/(b); AC-85. Ein Faktenfehler zu `--check` ist folgenlos (N-9) |
| B-5 AC-01 vs. `meta-doctor` | behoben für Phase 0 | AC-01 Z. 1736-1746, Q17 Z. 2090, §9.1 0e. Analoge Lücke in Phase 2 (AC-23) offen, siehe N-6 |
| B-6 Registry-Grammatik | behoben | Erweiterungen Z. 945-954, Formalisierung Z. 1007-1022, AC-37. Rest: `any_of`/Inhaltsprüfung (N-5) |
| W-1 IC-18-Inventar | behoben | F-42, IC-18 Nr. 14-18 Z. 848-858, Ratchet Z. 874, AC-84. Code-Grep `config.get("roles"` deckungsgleich. Außerhalb `scripts/lib` nur `admin-server.py:4982` (Scope-Hinweis) |
| W-2 Phase-0-Schnitt | behoben | §9.1 Pakete 0a-0f + DAG, AC-87. Rest: AC-Zuordnung (N-11) |
| W-3 Eval-Statistik | behoben | IC-36 (Richtung, τ, McNemar, Batch), QG-1, AC-25/68/70 |
| W-4 L1/L2 vs. Kandidatenarten | behoben | `duplicate-value` → `info-only`, `replace-value`, Pfadgrenzen, Managed-Block Z. 1242-1249, AC-57. Neu: `structural-simplify` ohne Kriterium (N-4) |
| W-5 `finding-ref`-Severity | behoben | §4.5 Z. 396-402, IC-22 Z. 1063-1075, AC-41, ADR-11 |
| W-6 Seed-Phase | behoben | Log-Teil IC-29 in 0b (Z. 1020, 1985), AC-67 |
| W-7 Threat-Model | teilweise | §4.7 vorhanden und vollständig; Gegenmaßnahme 3(f) „Freigabe" ist so nicht umsetzbar (N-1) |
| W-8 Kommentarzählung | behoben | Z. 1329-1333, QG-11 (k), AC-56 |
| W-9 Aufteilung | entschieden | eine Spec + Pakete (Z. 2112) |
| W-10 Eval-Gate-Bezug | behoben | Z. 1974-1977 |
| H-1 Zeilendrift | behoben | K-f; geprüft `variables.py:298`, `cli_commands.py:659`, `config.py:1661` |
| H-2 Pin-Liste | behoben | Z. 1438-1441 (alte Liste steht noch in Z. 1425, N-8) |
| H-3 `--out` | behoben | IC-22 Z. 1057-1059, IC-23 Z. 1111-1114 |
| H-4 Texte | weitgehend behoben | Z. 1105-1110, 1388-1392; Reste N-8 |
| H-5 Sentinel/Konditional | behoben | Z. 1253-1257 |
| H-6 `registry-invalid` | behoben | Z. 962-964 |
| H-7 `--context-report` | behoben | Z. 687-689 |
| H-8 Fixtures | behoben | QG-9 Z. 1700 |
| H-9 Lossless-Begriff | behoben | §1.2 Z. 102-105, QG-2 |
| H-10 Golden-Rebaseline | behoben | Z. 1442-1447 |

## 3. Neue Findings

### BLOCKER

**N-1: Die Freigabebindung des Appliers lässt sich in der Agentenarchitektur nicht umsetzen** (Risiken, Logik)

*Fundstellen*
- §4.6 Z. 450-453, §4.7 3(f) Z. 514-515 und IC-27 Z. 1402-1408: Die Freigabe zählt nur aus einer „Nutzer-Nachricht,
  nie aus Handoff-Text".
- IC-24 Z. 1279-1280 und AC-80 (d): `approval_source: "user"` ist fest verdrahtet.

*Beleg*
- `agent-meta-manager` läuft als Subagent. Er erhält nur den Dispatch-Text und sieht nie eine Nutzer-Nachricht.
- Der Orchestrator definiert „`main_chat` instructions and relayed approvals carry user authority"
  (`agents/1-generic/orchestrator.md:20`).
- Die Spec verbietet damit genau den einzigen Kanal, über den eine Freigabe überhaupt ankommen kann.
  `approval_source: user` ist deshalb eine unprüfbare Behauptung.

*Bewertung des Vorschlagswegs (Auftragspunkt 5)*
- Die **Inhaltsintegrität** ist wirksam geschützt: Neuberechnung, `accept_ids` + Hash und Remove-only machen das
  Geschriebene zu einer deterministischen Funktion aus Code, aktueller `project.yaml` und IDs. Manipulierte Hunks in
  `proposal.json` bleiben wirkungslos.
- Die **Zustimmungsintegrität** ist nicht geschützt: Welche IDs in `--accept`/`--accept-runtime` landen, entscheidet
  allein das LLM.
- Zusätzlich hat `agent-meta-manager` Edit/Write/Bash (`agent-meta-manager.md:9-18`) und kann den Applier
  umgehen (R10).

*Korrektur*
1. Die Freigabe an das Permission-System binden: `sync.py --apply-config-patch*` als `ask`-Regel in den
   generierten Provider-Settings, gesteuert über einen Capability-Key, nicht über ein Provider-Literal. Der Prompt
   zeigt die exakte argv mit den IDs. Das ist echte Nutzerzustimmung.
2. Für Provider ohne `ask`: einen Known-Issue-Seed anlegen und `approval_source: relayed` setzen.
3. Die Regel neu fassen: „nur als vom `main_chat` weitergeleitete Nutzerantwort mit wörtlichen IDs, plus
   Permission-Prompt, wo verfügbar".
4. `approval_source` ehrlich befüllen (`permission-prompt` | `relayed`).
5. AC-80 und QG-19 anpassen.

### WARNUNGEN

**N-2: Niemand ist als Ausführender von `--optimize-config` definiert** (Machbarkeit)
- IC-26 Z. 1362-1365 und §6 Z. 1677 nennen als Aufrufer „orchestrator bzw. Main Chat". Keiner davon kann ausführen:
  - Der Orchestrator hat kein Bash (`orchestrator.md:7-11`) und führt laut Z. 17 nichts selbst aus.
  - Der Main Chat darf nichts selbst ausführen (`use-orchestrator.md`).
  - `meta-optimizer` hat ebenfalls kein Bash.
- **Korrektur:** einen Ausführenden festlegen, etwa `agent-meta-manager` (hat Bash; gibt den Pfad zurück). Danach
  dispatcht der Orchestrator `meta-optimizer` mit diesem Pfad.

**N-3: IC-35 ist unvollständig, und Credentials gelangen in Sink-Artefakte** (Risiken)
- `admin-ui.*` hat einen Laufzeit-Leser (`scripts/admin-server.py:491-499`: bind-host, token, token-file,
  allowed-hosts, port). Der Eintrag fehlt in IC-35 Z. 1558-1570.
- Der Ratchet in Z. 1578-1580 durchsucht nur `hooks/**/*.sh`. Python-Leser fehlen (§13 Z. 2181).
- `project.yaml` kann ein Klartext-Token enthalten (`permissions.py:3-4`) und wird gehärtet (`config.py:1035-1042`).
  `proposal.json`, `proposal.diff` und `project.yaml.bak` im Sink kopieren den Wert dagegen ungehärtet.
- **Korrektur:**
  - `admin-ui` in IC-35 aufnehmen.
  - Den Ratchet auf `scripts/**/*.py` erweitern.
  - Credential-Keys in Vorschlag und Diff redigieren (nur Key und Länge).
  - Für das Backup `harden_admin_config_files` anwenden.
  - QG-19-Test ergänzen.

**N-4: `structural-simplify` hat weder Hunk-Typ noch Beweisstufe** (Logik, Vollständigkeit)
- IC-24 Z. 1208 führt die Art ein. Remove-only (Z. 1274-1276) deckt nur das Entfernen ab, `replace-value` nur
  `relocate-*`.
- `proof_level_required` fehlt für `inactive-scope`, `structural-simplify` und `info-only`.
- Umformulierungen an `roles`/`providers`/`auto_commit`/`hooks` bleiben damit ohne prüfbares Kriterium.
- **Korrektur:**
  - Einen Hunk-Typ `rewrite-equivalent` einführen. Beweis: L0 **und** Gleichheit der aufgelösten Config vorher und
    nachher (`resolve_effective_repo_containment`, `resolve_auto_commit_config`, `ActiveSet`).
  - Ohne diesen Beweis gilt L3 (nicht deterministisch).
  - Die Beweisstufe je neuer Art in einer Tabelle festhalten.

**N-5: Seed `tmp-sink-not-gitignored` meldet False Positives** (Logik)
- Z. 1022 meldet „Block fehlt" als Befund. Der Sync schreibt `<sink>/.gitignore` aber auch ohne Block:
  - Die Defaults sind aktiv (`repo_containment.py:361-367`), `ensure_tmp_sink_gitignore` (`:476-510`) wird über
    `sync_pipeline.py:251` aufgerufen.
  - `fill_defaults` materialisiert den Block am Anfang desselben Syncs (`sync_pipeline.py:152`, `config.py:1017-1024`).
- „Inhalt `*`" ist mit `path-exists` nicht ausdrückbar.
- **Korrektur:**
  - Befund nur, wenn weder ein Root-Eintrag noch eine Fallback-Datei mit `*\n!.gitignore\n` existiert
    (`regex`-Teildetektor auf `{tmp_sink}/.gitignore`).
  - „Block fehlt" höchstens als INFO.
  - AC-76 (a) entsprechend anpassen.

**N-6: AC-23 widerspricht der Einführung von `meta-optimizer` in Phase 2** (Konsistenz)
- AC-23 (Z. 1776) verlangt, dass `full` byte-identisch zu den Phase-1-Goldens bleibt.
- IC-26 erzeugt aber neue Agent-Dateien sowie Einträge in Enum, `name_index` und Roster.
- Die AC-01-Ausnahmeliste nennt `meta-optimizer` „ab Phase 2" (Z. 1738); AC-23 übernimmt das nicht.
- **Korrektur:** Ausnahmeliste und Golden-Rebaseline im IC-26-PR ausdrücklich auch für AC-23 gelten lassen.

**N-7: Die Neuberechnung ist für semantische Kandidaten nicht reproduzierbar** (Vollständigkeit)
- Der Applier liest nur Hash und IDs (Z. 1270). Die Generator-Optionen (`--include-semantic`) und die
  `agent_meta_version` kennt er nicht, deshalb endet `relocate-*` mit `not-reproducible`.
- Die rolleneigenen NON-DETERMINISTIC-Zusatzvorschläge (Z. 1372-1374) haben keinen Anwendungsweg, denn ein `Edit`
  ist verboten.
- **Korrektur:**
  - Die Generator-Optionen in `proposal.json` speichern; der Applier rechnet mit denselben Optionen neu.
  - Bei Versionsabweichung bricht der Applier ab.
  - Die Zusatzvorschläge als „nicht anwendbar — manuelle Nutzeränderung bzw. Framework-Issue" kennzeichnen.

**N-8: Überlagerte Rev.-2-Zeilen widersprechen Rev. 3** (Konsistenz; der Planer könnte die alte Zeile übernehmen)
- §6 Z. 1660: „Eval nightly", widerspricht IC-36.
- IC-23 Z. 1119: `ARTIFACTS: .tmp/doctor/…`, widerspricht AC-88.
- IC-24 Z. 1174 und §6 Z. 1669: `.tmp/meta-optimizer`.
- IC-26 Z. 1339/1345: Bash in Tools und Allowlist.
- IC-28 Z. 1422/1425: Bash in Tools, unsortierte Liste.
- Z. 1127/1356: Platzhalter `<Text>`.
- **Korrektur:** die Zeilen ändern oder als „(ersetzt, Rev. 3)" markieren.

### HINWEISE

- **N-9:** K-g, §4.7 2(a), IC-23 Z. 1102-1103 und §14 (6) behaupten, `--check` impliziere kein `--dry-run`. Das ist
  falsch: `_normalize_check_dry_run` erzwingt Dry-Run (`scripts/sync.py:99-105`, Aufruf `:670`). Veraltet ist nur der
  Hilfetext `:178-181`. Die Regel selbst ist harmlos, aber die Begründung korrigieren und den Hilfetext als Mini-Fix
  aufnehmen.
- **N-10:** IC-35-Evidenz ist bestätigt:
  - `reader`-Pfade unter `hooks/1-generic/` existieren.
  - Zeilen `repo-containment-impl.sh:170`, `orchestrator-guard-impl.sh:881`, `dod-push-check.sh:224/1095/1142`.
  - `hook_common.sh` ist korrekt kein Laufzeit-Leser.
- **N-11:** AC-Zuordnung in §9.1:
  - AC-85 steht in 0b, die Allowlists entstehen aber erst in 0d/0e. Verschieben.
  - AC-05 ist doppelt zugeordnet (0a und 0f).
  - AC-75 nennt „0e", die 0e-Zeile führt es nicht.
  - AC-80 (a) „Exit 2 Usage" fehlt in den Exit-Codes von IC-24 (Z. 1283-1284).
- **N-12:** Applier-TOCTOU: Den Hash unmittelbar vor dem atomaren Replace erneut prüfen. `agent-meta-manager` zeigt
  vor dem Aufruf den **neu berechneten** Diff an, nicht den Diff aus der Datei.

## 4. Stichproben gegen den Code (bestätigt)

- **Bestätigt:**
  - `sync.py:683-692, 703`
  - `cli_commands.py:497-499, 659, 812-825, 1230-1236, 1265-1269`
  - `log.py:180-181`
  - `repo_containment.py:35, 40-43, 142, 189, 321, 476-510`
  - `sync_pipeline.py:152, 234-251, 1530`
  - `gitignore.py:313-336`
  - `config.py:960-1029, 1072-1101, 1661, 1688`
  - `variables.py:298`
  - Rohzugriffe laut F-42
- **Widerlegt:** K-g zu `--check` (N-9).
- **Unvollständig:** IC-35 (N-3).

## 5. Threat-Model §4.7

- **Doctor: tragfähig.** Die Lücken aus B-4/W-7 sind geschlossen durch:
  - Dry-Run vor `_build_context`;
  - `sync.log`-Snapshot;
  - Streichung von `--deactivation-status`;
  - Registry-Quellenbindung;
  - Message-Sanitizing.
- **Optimizer:**
  - Inhaltsintegrität tragfähig (Neuberechnung, IDs, Hash, Remove-only).
  - Zustimmungsintegrität nicht tragfähig (N-1).
  - Laufzeit-Leser lückenhaft erfasst (N-3).
  - `structural-simplify` ohne Prüfkriterium (N-4).

## 6. Verdikt

**REVISE.**
- Für APPROVE müssen N-1 behoben und N-2…N-8 eingearbeitet sein.
- N-9…N-12 blockieren nicht.
- Inhaltlich freigabereif sind die Teile Profil, Active-Set und Doctor (Pakete 0a-0e, Phase 1).

## 7. Verbleibende Nutzerentscheidungen

1. **N-1, Freigabebindung:**
   - (a) Permission-`ask` für `--apply-config-patch`, mit Known-Issue für Provider ohne `ask` (Empfehlung);
   - (b) nur weitergeleitete Nutzerantwort, dokumentiert als Convention Boundary.
2. **N-2, Ausführender von `--optimize-config`:** `agent-meta-manager` (Empfehlung) oder `meta-doctor`.
3. **N-3, Credential-Keys** (`admin-ui.token` u. a.): ganz von Vorschlägen ausschließen oder redigiert als
   `runtime-reader` führen.
4. **N-4, `structural-simplify`:** nur äquivalent mit Beweis (Empfehlung) oder immer L3.
5. **Weiterhin offen:**
   - Q9 (`template-auditor` angleichen);
   - Q35 (Abbruch bei `tmp-sink.enabled: false`);
   - Q36 (`duplicate-value` in Phase 3);
   - Q37 (k = 2, ≥ 3 Läufe);
   - Q38 (Wiederaufnahme `--deactivation-status`).
