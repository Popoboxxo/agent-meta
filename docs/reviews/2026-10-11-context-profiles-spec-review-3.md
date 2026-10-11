# Drittes Review (begrenzt): SPEC-CONTEXT-PROFILES-2026-10-11 (Rev. 3.3, DRAFT)

- **Gegenstand:** `docs/specs/2026-10-11-context-profiles-spec.md` (Rev. 3.3), gezielt gelesen: Rev. 3.3-Änderungen, IC-15 Nr. 26/27, IC-21/22/23/34/35, §4.7, §8 (AC-92..96, AC-23, AC-89..91), §9/§9.1, §10 (ADR-17..20), §12, §13, §14.
- **Vorreviews:** `…-review.md` (Rev. 2.2), `…-review-2.md` (Rev. 3).
- **Reviewer:** concept-reviewer (Spec-Review-Modus), 2026-10-11.
- **Verdikt:** **APPROVE_WITH_CHANGES** (0 BLOCKER, 5 WARNUNGEN, 3 HINWEISE). Die Änderungen sind lokal (Rev. 3.4); kein Rückbau von Entscheidungen.
- **Nicht neu verhandelt:** Rollenmodell (meta-doctor Bash + tmp-sink-Schreibrecht, meta-optimizer strikt read-only), eine Spec, Q12/Q18/D-1, Eval nur nach Freigabe, Q16 -> #958, N-1 "nur relayed + Protokoll", Credential-Keys ausgeschlossen, `structural-simplify` nur Hinweis.

## 1. Formale Checks

| Check | Ergebnis |
|---|---|
| Pflichtsektionen, Trace-Anker, Status `DRAFT` | vorhanden, konsistent |
| No-Placeholder | keine unaufgelösten Platzhalter in Pflichtsektionen (Rev. 3.1 hat `<Text>` ersetzt, Z. 1242) |
| ID-Serien | lückenlos und eindeutig: AC-01..96, IC-01..36, F-01..46, QG-1..20, ADR-1..20, Q1..38, R1..22; Kopf (Z. 56-57, 85) und §14 nennen die neuen IDs korrekt |

## 2. Vorpunkte

| Punkt | Status | Beleg |
|---|---|---|
| Q9 (template-auditor angleichen) | behoben | IC-15 Nr. 14 (Z. 865), Q9 (Z. 2505), ADR-9, Rev. 3.2. Code bestätigt: `role-defaults.yaml:280` (Rolle), `:288` (`name_only`), `:293` (`routing_patterns`); Assert #5 steht in `76-template-auditor-role.sh:62-77` |
| Q35 (kein Fallback, `tmp-sink.disabled`) | behoben, Folgelücke W-4 | IC-34 Z. 1784-1786, 1794-1796; ADR-20; AC-94 (Abbruch). Offen: Verhalten von Doctor-`command`-Detektoren und `--doctor --out` bei deaktiviertem Sink |
| Q36 (`duplicate-value` Phase 3, `info-only`) | behoben | Q36 Z. 2532, ADR-18, QG-11 (m) |
| Q37 (k = 2, >= 3 Läufe) | behoben | Q37 Z. 2533, IC-36, QG-1 |
| Q38 (`--deactivation-status`, Begründung Messverfälschung) | behoben | Q38 Z. 2534, ADR-19, AC-85, AC-95 |
| tmp-sink Default AN (IC-15 Nr. 26, F-46, AC-92) | behoben | Code bestätigt: `gitignore.py:329-330` (`None` bei Nicht-Mapping), `sync_pipeline.py:319-324` (Claude-Gate) und `:152` (`fill_defaults`; mit `dry_run` kein Schreiben, `config.py:1027`), `config.py:1017-1018`. Aussage "Root-Eintrag nur mit Block" stimmt. Die reale Auswirkung ist nur Dry-Run/`--check` bzw. `None`/Nicht-Mapping; im regulären Sync wird der Block vor `compute_base_gitignore_entries` materialisiert |
| Pfad-Schutz (IC-15 Nr. 27, F-45, AC-93, QG-20, R22) | behoben bis auf W-1 und W-2 | Alle sieben Befunde (1)-(7) stimmen inhaltlich (siehe 3) |
| Arbeitsverzeichnisse nur im Sink (`resolve_work_dir`, AC-94, ADR-20) | behoben bis auf W-3 | IC-34 Z. 1825-1831; Guard-Test AC-94 (Konflikt W-3) |
| Doctor-Rechte konsistent (§1, §4.5, §4.7, IC-22/23, AC-39/95, ADR-19, R16) | behoben bis auf W-4 | Z. 36, 83-84, 147-149, 174-176, 432-433, 543, 1165-1167, 1192-1195, 2141, 2363-2368, 2436, 2581. Kein Text nennt `meta-doctor` oder `--doctor` noch "strikt read-only". Reste: H-1 |
| N-1 (`approval_source: relayed`, R20/ADR-17, Vorschau-Pflicht) | behoben | Grep über alle Stellen: Z. 62, 509-514, 533 (Zukunftsoption), 609, 1448-1453 (alte Zeile durchgestrichen), 1639, 2004, 2266-2267, 2323, 2328, 2434, 2585. Jede Stelle mit "nur aus Nutzer-Nachricht" ist durchgestrichen oder negiert; `approval_source: "user"` kommt nirgends mehr als geltende Aussage vor. AC-90 und QG-19 prüfen `relayed` |
| N-3 (Credential-Ausschluss) | behoben | IC-35 Z. 1861-1893 (`admin-ui`, `viz`, `lifecycle-triggers`, Ratchet `scripts/*.py`, `credentials`-Abschnitt), §4.7 2(j)/3(j), AC-89, R21, QG-19. Negativfall `max-tokens-overrides` vorhanden |
| N-6 (AC-23-Ausnahmeliste) | behoben | AC-23 Z. 2100-2102 ("dieselbe Ausnahmeliste wie AC-01"), §9 Z. 2396-2397, Rev. 3.1 Z. 69 |
| ID-Serien und Querverweise | behoben bis auf W-5 | siehe 1 |
| Phasenplan §9/§9.1 und IC-15 Nr. 26/27 | teilweise | 0a nennt Nr. 26/27 als Voraussetzung (Z. 2403), der DAG ist unverändert. Die §9-Tabelle ist nicht nachgezogen, siehe W-5 |

## 3. Code-Prüfung F-45/F-46 (Auftragspunkt 3)

Alle inhaltlichen Aussagen stimmen. Zeilenabweichungen:

| Spec-Angabe | Code | Bewertung |
|---|---|---|
| Regex `:46` (F-45 (1)) | `_WINDOWS_DRIVE_RE` steht in `:48` (Kommentar `:45-47`) | HINWEIS |
| Root-Gleichheit `:177` | `:179` (Kommentar `:175-178`) | HINWEIS |
| `:187` liefert `Path(target)` | `:186` | HINWEIS |
| `repo_containment.py:14-18` für die Defaults (F-46, IC-34) | `:14-18` ist der Docstring zu `provider-overrides`; die Konstanten stehen in `:34-37`, die Auflösung in `:361-367` | HINWEIS |
| `:205` `isabs`, `:207` Drive-Match, `:211`, `:214`, `:171`, `:174`, `:182`, `:222-228`, `:428`, `config.py:565-572`, `gitignore.py:313-336`/`:329-330`, `sync_pipeline.py:319-324`/`:152`/`:251` | bestätigt | OK |

## 4. Neue Findings

### BLOCKER
Keine.

### WARNUNGEN

**W-1: Die Pfad-Härtung ignoriert die Hook-Kopie der Sink-Validierung** (Konsistenz, Risiken)
- *Fundstelle:* IC-15 Nr. 27 und IC-34 ("alle Prüfungen laufen über eine zentrale Funktion", Z. 1823). Der Code hat weitere Kopien:
  - `hooks/1-generic/repo-containment-impl.sh:37-39, 183-224` spiegelt `tmp_sink_path_error` inline. Er importiert das Python-Modul bewusst nicht, weil die Datei im Zielprojekt nicht ausgeliefert wird. Er prüft nur relativ, nicht leer, Laufwerks-Präfix, `..` und Root-Gleichheit.
  - `scripts/lib/progress_paths.py:92` ist eine weitere Variante der Garantie.
- *Folge:* Python kanonisiert `scratch\out` zu `scratch/out`, der Hook sieht den Pfad weiterhin als einen Dateinamen. Ebenso ablehnende Regeln (Gerätenamen, UNC, case-insensitive Schutzliste) gelten nur in Python. Der Hook ist der Laufzeit-Schreibschutz, nicht der Sync. Divergenz führt zu Sink-Pfaden, die der Sync anlegt, der Hook aber anders bewertet (Carve-out, Z. 16-20, bzw. Block).
- *Korrektur:* Nr. 27 um den Hook erweitern (inline-Spiegel, Hook-Version erhöhen, Drift-Check #630) oder die Hook-Parität ausdrücklich ausschließen und per Paritätstest (AC-93-Fälle gegen den Hook-Python-Block) absichern. `progress_paths.py` im Scope erwähnen.

**W-2: `os.path.isjunction` existiert auf den CI-Versionen 3.9 und 3.11 nicht** (Machbarkeit)
- *Fundstelle:* IC-15 Nr. 27 (c), §13 Z. 2637, AC-93 (monkeypatch von `os.path.isjunction`). Die Begründung "Projekt läuft auf 3.13" ist irreführend.
- *Beleg:* `.github/workflows/orchestration-test.yml:34` testet `['3.9', '3.11', '3.12']`; `validate.yml:19, 32` nutzt 3.11. Q21 (Z. 2517) setzt selbst Python 3.9 voraus. Direkter Aufruf ergibt `AttributeError`, `monkeypatch.setattr` ohne `raising=False` scheitert.
- *Korrektur:* Nr. 27 (c) als `getattr(pathmod, "isjunction", None)` mit `realpath`-Fallback festlegen. Das ist kein Detail, weil `realpath` auf Python < 3.8-Windows-Junctions auflösen kann. In AC-93 `raising=False` vorschreiben und den Fallback-Pfad auf 3.9 testen. §13 und IC-15 Nr. 27 anpassen ("3.13" streichen).

**W-3: Seed `tmp-sink-outside-repo-or-system-temp` ist nicht in IC-21 formalisiert und kollidiert mit dem AC-94-Guard** (Vollständigkeit, Logik)
- *Fundstelle:* IC-34 Z. 1832-1834 behauptet "(IC-21, ERROR, `VERIFIED-SOURCE`)"; die Seed-Tabellen IC-21 (Z. 1112-1127) enthalten keine Zeile, und kein Detektorkind (`regex`, `yaml-key`, `path-exists`, `command`, `any_of`, ...) deckt "realpath außerhalb Root oder unter `tempfile.gettempdir()`".
- *Konflikt:* AC-94 verlangt, dass `grep -E 'tempfile|gettempdir|...' scripts/lib/{doctor,meta_optimizer,context_report}*.py` leer ist. AC-96 braucht `tempfile.gettempdir()` für denselben Seed; `doctor_detectors.py` (IC-22) fällt unter das Glob `doctor*.py`.
- *Korrektur:* Seed-Zeile in IC-21 ergänzen (Prädikat, Detektorkind, Message, Fix-Owner, Phase-Stufe nach ADR-11, Paket 0d) und die Prüfung in `repo_containment.py` implementieren (Funktion `tmp_sink_location_error`), die der Detektor nur aufruft. AC-94 explizit auf diese Funktion beschränken.

**W-4: Doctor-Schreibgrenze "einziges Ziel `doctor/`" widerspricht der Bash-Allowlist** (Konsistenz)
- *Fundstelle:* IC-23 Z. 1193 und AC-95 ("einziges Schreibziel ist `{{TMP_SINK_PATH}}/doctor/`") gegenüber der Allowlist `sync.py --context-report --json` (Z. 1209). IC-11/IC-34 lassen `--context-report` unter `<sink>/context-report/<run>/work/` schreiben und rendern.
- *Weitere Lücken:*
  - AC-39 schließt im Snapshot das Literal `.tmp/` aus (Z. 2141), nicht den konfigurierten Sink (Fixture `scratch/out`, AC-94).
  - Bei `tmp-sink.enabled: false` bricht `--context-report` mit Exit 2 ab (Q35). Für Doctor-`command`-Detektoren und für `meta-doctor` Schritt (2) ist nichts definiert; die Zusage "`--doctor` ohne `--out` läuft weiter" (Z. 1785) deckt das nicht ab.
  - `--doctor --out` bei deaktiviertem Sink: Exit-Code unklar (`out-outside-tmp-sink` oder `tmp-sink.disabled`).
- *Korrektur:*
  - Schreibgrenze neu fassen: "nur Unterverzeichnisse des aufgelösten Sinks (`doctor/`, `context-report/`), keine Projekt-/Sync-Dateien".
  - AC-39/AC-95 und QG-10 auf den aufgelösten Sink ausnehmen.
  - Verhalten bei deaktiviertem Sink festlegen, z. B. `doctor.detector-unavailable` (INFO) für den `command`-Detektor und Exit 2 `doctor.tmp-sink.disabled` für `--out`.

**W-5: Phasenplan und Verhaltensänderung für IC-15 Nr. 26/27 nicht nachgezogen** (Konsistenz, Risiken)
- *Fundstelle §9 (Z. 2378, 2379):* Die Phase-0-Zeile nennt AC-75..78, AC-84..88, nicht AC-92..96 (nur §9.1 Z. 2403-2407 führt sie). Die Phase-1-Zeile führt "IC-15 Nr. 1-24 (+ optional 25)"; Nr. 26/27 stehen nur in 0a als "eigene PRs" (Ausnahme zur Tabellenüberschrift). Phase 0 behauptet "keine Verhaltensänderung" und "nur neue read-only Werkzeuge".
- *Tatsächliche Verhaltensänderung:*
  - Nr. 27 verschärft `tmp_sink_path_error`, und `config.py:568` ruft `_fail`: Eine bisher gültige Konfiguration (z. B. Sink mit Gerätename, case-variantem Schutznamen oder Zwischen-Symlink im Root) bricht den Sync hart ab.
  - Nr. 26 ändert `--check`/Dry-Run-Ausgabe und Fixtures.
  - Die AC-01-Ausnahmeliste deckt beides nicht.
  - Eine Migrationsaussage für Bestandskonfigurationen fehlt.
- *Korrektur:*
  - AC-92..96 in die §9-Zeilen (Phase 0, Phase 2 für AC-94-Optimizer-Teil) aufnehmen.
  - Nr. 26/27 in die Phase-0-Zeile aufnehmen.
  - "Verhaltensänderung" ehrlich benennen und die AC-01-Ausnahme (Nr. 26: nur Dry-Run/`--check`-Vorschau und `None`-Pfad; Nr. 27: neue Ablehnungen mit eindeutiger Fehlermeldung) ausdrücklich formulieren.
  - Entscheiden, ob harter Fehler oder Übergangs-WARN gilt (Nutzerentscheidung 4).

### HINWEISE

- **H-1 (Rest-"read-only"):** Z. 2378 "nur neue read-only Werkzeuge" und QG-10 Z. 2022 "Read-only-Test ... vor/nach `--doctor`" benutzen den Begriff für Werkzeuge, die in den Sink schreiben (`--doctor --out`, `--context-report`, `--optimize-config`). Die AC-95-Szenario-Assertion deckt nur `meta-doctor`/`--doctor` ab. Durch "schreibt nur in den tmp-sink" ersetzen. IC-22 Z. 1154 (CLI-Signatur) enthält `--out` erst in den Folgeabsätzen; Signatur ergänzen. Z. 1203-1204 (alte Allowlist) als "ersetzt" markieren, wie Z. 1205.
- **H-2 (Zeilenangaben F-45/F-46):** siehe 3, nur Zahlen, keine Sachfehler.
- **H-3 (Szenario-Zeilen):** Z. 2047 nennt `76-template-auditor-role.sh:63-76`, Q9/IC-15 `:62-78`; Code `:62-77`. Vereinheitlichen.

## 5. Verdikt

**APPROVE_WITH_CHANGES.** Rev. 3.4 mit W-1 bis W-5 genügt; H-1 bis H-3 nebenbei. Danach ist die Spec freigabefähig für Paket 0a (Pfad-/Default-Fixes) und 0d/0e.

## 6. Nutzerentscheidungen

1. **W-1, Hook-Parität:** (a) Hook-Spiegel in Nr. 27 mitziehen mit Versionsbump und Drift-Check (Empfehlung); (b) nur Python härten, Abweichung dokumentieren und per Paritätstest begrenzen.
2. **W-2, Python-Mindestversion:** (a) `getattr`-Fallback auf `realpath`, CI 3.9 bleibt (Empfehlung); (b) CI-Matrix auf >= 3.12 anheben.
3. **W-4, Doctor-Schreibgrenze:** (a) `doctor/` und `context-report/` als erlaubte Ziele (Empfehlung); (b) `--context-report` aus der `meta-doctor`-Allowlist entfernen.
4. **W-5, Verschärfung Nr. 27 für Bestandskonfigurationen:** (a) harter Fehler mit eindeutiger Meldung (Empfehlung, konsistent mit Q35 "kein Fallback"); (b) einen Zyklus WARN, dann Fehler.
