# Agent-Eval-Plan v2 — Revision zu Concept-Review #523 (promptfoo-basiertes Agent-Eval-Framework)

| | |
|---|---|
| **Date** | 2026-09-06 |
| **Status** | PLAN v2 — Revisions-Artefakt zu Review #523 (REVISE), wartet auf erneuten Concept-Review-Pass |
| **Scope** | Rein dokumentarisch (dieses Dokument selbst); der beschriebene Restscope ist Implementierungsplan, hier ist **kein Code geändert** |
| **Branch** | `feat/issue-674-roadmap` (Working-Tree-Lesebasis; keine Commits/Code-Änderungen durch dieses Artefakt) |
| **Basis** | Issue #523 (Volltext via GitHub-API, 2026-09-06 abgerufen, 0 Kommentare) vs. **aktueller** Repo-State (alle Beweiszeilen 2026-09-06 verifiziert) |
| **Vorgänger** | Draft-Plan `promptfoo-agent-eval-plan.md` (193 Zeilen, Review-Date: 2026-08-21) — Original-Artefakt lag in `/tmp/opencode/` und ist **nicht mehr abrufbar**; Revision stützt sich auf den Review-Text in #523 + Code-Reconciliation (Annahme, siehe §9) |
| **Voraussetzung-Konzept** | `docs/concepts/planned/orchestrator-routing-test-suite.md` (§4 Architektur, §5 Phasen, §6 CI, §7 Owner-Entscheidungen) |
| **Ausführungsreife** | Steps R1–R8 (§6) sind implement-reif; Ausführung unabhängig vom #674-Roadmap-Plan (dort keine agent-eval-Referenz — geprüft per Suche über `docs/plans/2026-09-05-issue-674-roadmap.md`) |

---

## 0. Executive Summary — Issue-vs-Reality Reconciliation

Zentrale Erkenntnis der Revision: **Der Repo-State ist dem Review vom 2026-08-22 bereits voraus.** Die Issues
#535 ("agent-eval framework") und #539 (Isolation + Rollen-Parametrisierung) haben zwischen Review-Datum und
Revision mehrere der geforderten Fixes **im Code** gelandet. Plan v1 wurde als Greenfield-Plan (11 Schritte)
geschrieben; Plan v2 ist daher ein **Reconciliation + Restscope-Plan**: Er (a) dokumentiert für jeden
Review-Fund den aktuellen Stand mit `file:line`-Evidenz, (b) trifft die von B1 geforderte fehlende
Entscheidung (Output-Contract v2), (c) spezifiziert die verbleibenden Lücken als Schritte mit messbaren
Akzeptanzkriterien.

| Fund | Review-Stand (2026-08-22) | Repo-State 2026-09-06 | Disposition |
|---|---|---|---|
| **B1** | Wrapper-Contract misst B2/B3/B5-Asserts nicht; Entscheidung fehlt komplett | **Contract v2 teils gelandet:** strukturierter Sidecar (`EVAL_STRUCTURED_OUTPUT`) mit `final_text`, `event_counts`, `tool_events`, `spawn_attempts` in beiden Wrappern (`provider-opencode.sh:114-160`, `provider-claude.sh:90-106`); **aber:** der Bash-Runner konsumiert den Sidecar noch nicht ( grading liest nur stdout, `run_eval.sh:87`), Claude-Seite ist strukturell blind (`stream: false`) | **Entscheidung getroffen (§2):** Contract v2 verbindlich; keine Rubric-Abschwächung als Primärpfad — Restscope R1a–R1c |
| **W1** | Judge-Spec unbestimmt | Weiter offen, aber **explizit dokumentiert** als Phase-2-Entscheidung (`tests/routing-llm-eval/README.md:34-44`); Behavioral-Katalog enthält bewusst keine llm-rubric-Asserts (`catalog.behavior.yaml:12-14`) | **Vollständige Spec in §4.1** (Modell, Prompt, Temperatur, Schema, Retry, Kosten); Umsetzung = Step R4 |
| **W2** | `PROMPT_TMPL` wrapt jeden Task | **Gelandet:** `prompt_override`-Pfad (`run_eval.sh:73-79`); Behavioral-Cases tragen rohe `prompt:`-Felder (`catalog.behavior.yaml:5-9`); Legacy-Wrap nur noch für Routing-Cases (`test_agent_eval_framework.py:104`) | Erledigt; geschärftes Akzeptanzkriterium (Live-E2E) in R6 |
| **W3** | Kein SoT-Mechanismus Kataloge ↔ Config | **Gelandet:** `scripts/gen_promptfoo_config.py` leitet `promptfooconfig.generated.yaml` aus allen drei Katalogen ab (`gen_promptfoo_config.py:34-38`), `--check`-Freshness (`:93-98`), Idempotenz getestet (`test_agent_eval_framework.py:113-125`) — und läuft **bereits in CI** über `pytest tests/ -q` (`orchestration-test.yml:43-44`) | Erledigt; Neufund N1 (Rollen-Injection, §6) ist der einzige Promptfoo-Restscope |
| **W4** | `{{prompt}}` inline, quoting-fragil; step-5-Kriterium zu schwach | **Gelandet:** Provider-Commands ohne `{{prompt}}` (`gen_promptfoo_config.py:9-12, 40-43`); Bash-Pfad übergibt Prompt korrekt als argv-Argument (`run_eval.sh:87`); Test verbietet `{{prompt}}` (`test_agent_eval_framework.py:122-124`) | Erledigt; Kriterium "end-to-end grün, ≥1 Case je Provider" = R6 |
| **W5** | Phase-1-Aufwand 2–3 PD unterschätzt; Baseline-Kostenmessung fehlt | (Plan-Ebene) | **Restscope neu kalkuliert (§6):** ≈ 5,5–7,5 PD; Baseline-Messung (R7) **vor** Budget-Festlegung, Budget-Default in Q6 |
| **W6** | Silent exit 0 bei fehlender Rolle | **Gelandet:** exit 2 in beiden Wrappern (`provider-opencode.sh:58-62`, `provider-claude.sh:68-72`), getestet (`test_agent_eval_framework.py:37-42`) | Erledigt |
| **W7** | „Repo hat kein `.github/workflows/`" ist falsch | Workflows existieren: `validate.yml` (push/PR `main` + Cron `0 3 * * *`, `sync.py --validate` + Frontmatter-Lint, `validate.yml:3-9, 21-39`) und `orchestration-test.yml` (Push/PR mit Paths-Filter, Pytest-Matrix 3.9/3.11/3.12 + `--validate`, `orchestration-test.yml:6-29, 43-47`) — bereits im Eval-README korrigiert (`README.md:46-52`) | **Integrationspunkte benannt (§4.7);** `agent-eval.yml` = Step R8 |
| **H1** | B4-Parity vergleicht unterschiedliche Artefakte | (Plan-Ebene) | Interpretations-Guideline in §5.1 |
| **H2** | Stabilitäts-Semantik inkonsistent (3/3 vs. >2/3) | Runner-Semantik einheitlich 3/3-PASS, 1..n-1=FLAKY, 0=FAIL (`run_eval.sh:143-155`) | **Vereinheitlicht auf REPEAT/REPEAT (§5.2);** »>2/3« aus Plan v1 gestrichen |
| **H3** | Frontmatter würde als Prompt-Garbage injiziert | **Gelandet:** awk-Stripping für Nicht-Orchestrator-Rollen (`provider-claude.sh:74-77`), Dry-Parse-Test (`test_agent_eval_framework.py:45-51`) | Erledigt |
| **H4** | Paths-Filter unvollständig/redundant | (Plan-Ebene) | Propagations-Map für `agent-eval.yml` in §5.4 |
| **H5** | CI-Prerequisites (CLIs, Auth, committete Agenten-Dateien) | (Plan-Ebene) | Verifiziert: `.gitignore` (1-67) enthält **keinen** Eintrag für `tests/routing-llm-eval/` oder generierte Agenten-Verzeichnisse → Dateien sind committet; CLI-Install/Auth = R8-Spec (§5.5) |
| **H6** | Owner-Liste unvollständig (dual-tables Fix fehlt) | (Plan-Ebene) | Konditionale Folgeentscheidung übernommen (Q7, §5.6) |

**Neufunde über den Review hinaus** (aus der Code-Reconciliation): N1 — Promptfoo-Modus injiziert
`vars.role` nicht in die Provider-Commands, rollenspezifische Behavioral-Cases würden fälschlich gegen
`orchestrator` laufen (§5.1, Step R3); N2 — die Spawn-Erkennungs-Heuristik im Opencode-Sidecar ist gegen die
echte NDJSON-Event-Vokabel noch unverifiziert (§5.2, Teil von R6); N3 — Promptfoo-CLI-Installierbarkeit bleibt
ungelöst (Konzept §7 Punkt 4), Bash-Runner bleibt primär (§5.3).

---

## 1. Ausgangslage, Quellen und Annahmen

1. **Issue #523** („review: promptfoo agent-eval plan — REVISE findings (1 blocker, 7 warnings, 6 hints)“,
   2026-08-22, 0 Kommentare) verlangt: *„fixes for B1 + W1–W7 before approval; then another review pass
   (checking correction_hints only)“*. Dieses Dokument ist das Revisions-Artefakt für genau diesen Pass.
2. **Original-Plan nicht abrufbar.** Der Review prüfte `/tmp/opencode/promptfoo-agent-eval-plan.md`
   (193 Zeilen); diese temporäre Datei existiert nicht mehr. Annahme: Die Review-Findings zitieren die
   relevanten Original-Aussagen hinreichend vollständig (Faktenbehauptungen, Zeilenverweise, Step-Struktur).
   Alle Fakten wurden stattdessen **neu gegen den aktuellen Code** verifiziert — wo Review-Fakt und Code
   divergieren, gilt der Code (Korrekturen in §9).
3. **Case-Bestand korrigiert:** Review bestätigte „45 cases“ (23 `catalog.generated.yaml` + 22
   `catalog.manual.yaml`). Heute sind es **52**: 23 kw-Routing-Cases (`catalog.generated.yaml`, Zeilen
   14–168) + 22 manuelle Routing-Cases (6× mkw, 5× gen, 2× dis, 3× neg, 1× amb, 5× drift,
   `catalog.manual.yaml:24-169`) + **7 Behavioral-Cases** (2× delegation-gate, 1× role-fidelity, 2×
   output-format, 2× interface-knowledge, `catalog.behavior.yaml:17-83`).
4. **Abgrenzung:** `tests/orchestration/` (deterministisch) und `tests/routing-llm-eval/` (LLM-basiert)
   bleiben getrennt — Konzept §2, vom Review positiv verifiziert. Antigravity bleibt gated hinter einem
   Verifikations-Spike (Konzept §5 Phase 3, nicht Teil dieses Restscopes).

---

## 2. B1-Entscheidung: Output-Contract v2 (strukturierter Sidecar)

### 2.1 Die Entscheidung

**Gewählt: Contract v2 — strukturierter Sidecar als verbindlicher Wrapper-Output.** Die Alternative des
Reviews („v1 als Say-Do-Proxy deklarieren und Rubric-Formulierungen abschwächen“) wird **verworfen** als
Primärpfad, weil:

- Der Sidecar ist für Opencode **bereits implementiert und getestet** (`provider-opencode.sh:114-160`,
  Contract-Shape-Test `test_agent_eval_framework.py:128-133`) — ein Abschwächen wäre jetzt ein
 _capability-Rückschritt_ ohne technischen Grund.
- Die Review-Einwendung („ohne Transcript ist korrekt verweigert nicht von versucht-und-gescheitert
  unterscheidbar“) adressiert Contract v2 **in die richtige Richtung**: Für die B3-Politiksemantik ist die
  Unterscheidung gar nicht pass-relevant — *jeder* Spawn-Versuch (`spawn_attempts > 0`) verletzt das
  Delegation-Gate und zählt als FAIL, unabhängig davon, ob die Infrastruktur ihn blockiert hätte. Die
  Unterscheidung bleibt als **Diagnose-Information** im Sidecar erhalten (`event_counts`, `tool_events`).
- Abschwächung bleibt als **dokumentierter Fallback** für strukturell blinde Provider (Claude,
  `stream: false`) — als Capability-Tier, nicht als stiller Rubric-Downgrade (§2.3).

### 2.2 Contract v2 — Schema und Semantik

Beide Wrapper schreiben bei gesetztem `EVAL_STRUCTURED_OUTPUT` eine JSON-Datei mit exakt diesem Shape
(Referenz-Implementierung: `provider-opencode.sh:146-154`, `provider-claude.sh:95-103`):

```json
{
  "provider": "opencode|claude",
  "role": "<rolle unter test>",
  "stream": true|false,
  "final_text": "<letzter text-event bzw. gesamtausgabe>",
  "event_counts": {"<event-type>": <n>, ...},
  "tool_events": [{"type": "<event-type>", "tool": "<tool|null>"}, ...],
  "spawn_attempts": <int>
}
```

Semantik-Vertrag:

| Feld | Opencode (stream: true) | Claude (stream: false) |
|---|---|---|
| `final_text` | letzter Text-Event (`part.text`) | gesamte `claude -p`-Ausgabe |
| `tool_events` | 1 Eintrag je Nicht-Text/Step-Event, mit `part.tool` falls vorhanden | **immer `[]`** — `claude -p` liefert keinen Event-Stream (honest gap, `provider-claude.sh:12-14, 90-106`) |
| `spawn_attempts` | Heuristik: `tool == "task"` oder Event-Type ∈ {`tool_input`, `tool_call`} (`provider-opencode.sh:143-144`) | **immer 0** — nicht beobachtbar |
| stdout | unverändert `final_text` (Rückwärtskompatibilität mit Routing-Grading) | unverändert |

Weiterer Vertragsbestandteil: **exit 2 = Infrastruktur-Fehler** (fehlende/unbekannte Rolle,
Substitutions-Assert `provider-opencode.sh:87-90`) — niemals ein Case-Ergebnis. Ein fehlender oder
unparsbarer Sidecar bei erwartetem strukturellem Assert gilt als **Case-FAIL mit Marker
`struct=infra-error`**, niemals als stilles Pass (gleiche Philosophie wie der False-Green-Guard
`run_eval.sh:161-164`).

### 2.3 Capability-Tiering und Rubric-Konsequenzen

| Assert-Klasse | Betroffene Cases | Opencode (Tier `struct=full`) | Claude (Tier `struct=text-only`) |
|---|---|---|---|
| B3 Delegation-Gate (Text) | `b3-selfspawn-01/02` | erwartete Verweigerungs-Vokabel in `final_text` (Regex `expected_any`, `catalog.behavior.yaml:21-23, 29-32`; Vokabel real im Template, `agents/1-generic/orchestrator.md:19, 263-266`) | identisch (textbasiert, voll messbar) |
| B3 Delegation-Gate (Struktur) | dieselben Cases | **`spawn_attempts == 0`** (Fall > 0 → FAIL) | **nicht verfügbar** → Ergebniszeile trägt Marker `struct=unavailable`, struktureller Assert wird übersprungen (explizit reportet, nicht still bestanden) |
| B2 Rollen-Treue | `b2-dev-docs-01` | `forbidden`-Textmarker in `final_text` (`catalog.behavior.yaml:43-45`) | identisch (textbasiert, voll messbar) |
| B5 Output-Contract | `b5-contract-orch-01/2`, `b5-contract-dev-01` | `expected_all` in `final_text` (`catalog.behavior.yaml:52-55, 61-63`) | identisch |
| B6 Interface-Wissen | `b6-sync-interface-01/2` | `expected_any` mit `isolation: repo-readonly` (`catalog.behavior.yaml:66-83`; Isolation `provider-opencode.sh:67-78`, `provider-claude.sh:51-62`) | identisch |

Konsequenz der Entscheidung: Die **ursprüngliche B2-Rubric-Formulierung „no Write/Edit tool usage“ wird
nicht abgeschwächt, sondern spezifiziert**: Sie ist unter Opencode strukturell prüfbar (via `tool_events`),
unter Claude nur als Text-Level-Proxy. Ein Parity-Vergleich B4 (Claude vs. Opencode) zählt
Fähigkeitsunterschiede der Tiers daher als **Artefakt-, nicht Provider-Differenz** (verschärft H1, §5.1).

### 2.4 Restscope aus B1 (Steps R1a–R1c, Details §6)

- **R1a — Sidecar-Konsum im Bash-Runner:** `run_eval.sh` liest aktuell nur stdout (`run_eval.sh:87`); der
  Runner setzt pro Aufruf `EVAL_STRUCTURED_OUTPUT` auf eine Temp-Datei, parst sie und wertet das
  Katalogfeld `assert_struct` (z. B. `spawn_attempts: 0`) aus. Offline testbar mit einem Fake-Wrapper, der
  einen synthetischen Sidecar mit `spawn_attempts: 1` liefert → B3-Case muss FAILen.
- **R1b — Claude-Seiten-Spike:** Verifizieren, ob die installierte `claude`-CLI-Version strukturierte
  Ausgabe anbietet (z. B. `--output-format stream-json` o. ä.). Bei negativem Befund: Tier `struct=text-only`
  bleibt dokumentierte Endzustand (Q2), keine Annäherungs-Lösung.
- **R1c — NDJSON-Vokabel-Validierung (Neufund N2):** Die Heuristik `provider-opencode.sh:143-144` braucht
  eine Bestätigung gegen reale Event-Shapes der installierten Opencode-Version (Teil des E2E-Laufs R6;
  Ergebnis wird im README festgehalten).

---

## 3. Warnings W1–W7 — je Finding → Fix → Consequence

### 3.1 W1 — Judge-Spec für `llm-rubric` (offen)

**Finding (Review):** Der lokale Langzeit-Runner müsste Judge-Modell, Judge-Prompt, Parsing,
Retry-/Fehlerverhalten und Kosten selbst implementieren; repeat=3 × Judge multipliziert Kosten; der Judge
ist nicht-deterministisch.

**Fix:** Vollständige Spec (Umsetzung als Step R4, **vor** jeder Rubric-Katalog-Erweiterung R5):

| Spec-Punkt | Festlegung |
|---|---|
| Judge-Modell | günstigstes stabiles Claude-Tier, default `haiku` (konsistent mit `CLAUDE_ROUTING_EVAL_MODEL`-Default, `provider-claude.sh:84`); Override via `AGENT_EVAL_JUDGE_MODEL` |
| Judge-Prompt | Template: Rubric-Text + Fall-Task + `final_text` (+ `tool_events`-Auszug bei `stream: true`) → Entscheidung; Festtext-Antwortformat, keine Freitext-Interpretation |
| Temperatur | 0 (Determinismus-Anforderung, s. u.) |
| Output-Schema | striktes JSON `{"pass": <bool>, "reason": "<string>"}` — Parsing mit 2 Retries, danach **fail-closed** (Case = FAIL mit Marker `judge=parse-error`) |
| Stabilität | gleiche Stabilitäts-Semantik wie Text-Asserts: REPEAT/REPEAT = PASS, sonst FLAKY/FAIL (§5.2); Judge-Entscheidung je Wiederholung separat |
| Kosten | Logging je Case ($/Case, $/Lauf); Zielkorridor <$0.01/Case bei repeat=1 (vorläufig, verifiziert durch R7-Baseline) |
| Kalibrierung | 2–3 Iterationsschleifen gegen False-Pass/False-Fail vor Freigabe (Budget in §6 eingeplant) |

**Consequence:** Rubric-Asserts bleiben aus `catalog.behavior.yaml` fern, bis R4+R5 abgeschlossen sind
(so bereits dokumentiert, `catalog.behavior.yaml:12-14`, `README.md:34-44`) — kein Silent-Growl neuer
Judge-Abhängigkeiten in laufende Runs.

### 3.2 W2 — Prompt-Decoupling (erledigt im Code)

**Finding:** `PROMPT_TMPL` wrapt jeden Task in das Ein-Wort-Routing-Prompt (Original-Zeilen 53–56); B2/B3/B6
müssen roh durchgereicht werden; step-3-Kriterium deckte das nicht ab.

**Fix (Implementiert, `#535`):** Behavioral-Cases tragen ein rohes `prompt:`-Feld; der Runner nutzt
`prompt_override` bevorzugt und wrapt nur Legacy-Cases (`run_eval.sh:73-79`, Feld-Semantik
`catalog.behavior.yaml:5-9`). Der Test erzwingt die Trennung: Behavioral-Cases brauchen `role` + Assert +
rohen Prompt (`test_agent_eval_framework.py:78-89`), Legacy-Cases dürfen kein `prompt:` tragen
(`:104`).

**Consequence:** Kein Restscope im Code. Das ursprünglich zu schwache Step-5-Kriterium („parses without
schema error“) wird ersetzt durch R6 (end-to-end grün, ≥1 Case je Provider und Katalog-Klasse).

### 3.3 W3 — Single Source of Truth (erledigt im Code)

**Finding:** §2 behauptete „beide konsumieren denselben Katalog“, aber der Config-Sketch bettete Tests
inline ein — Doppel-Pflege, Drift-Risiko.

**Fix (Implementiert, `#535`):** `scripts/gen_promptfoo_config.py` leitet `promptfooconfig.generated.yaml`
aus allen drei Katalogen ab (`gen_promptfoo_config.py:34-38`; Assert-Mapping `:55-65`), ist idempotent und
hat einen `--check`-Drift-Exit (`:93-98`). Der Freshness-Test läuft **bereits in CI** über die
Pytest-Suite des `orchestration-test.yml` (`orchestration-test.yml:43-44` →
`test_agent_eval_framework.py:113-125`). Der Bash-Runner konsumiert dieselben Kataloge via
`list_cases.py` (Merge + Dedup: `list_cases.py:47-71`).

**Consequence:** Die Drift-Klasse ist geschlossen. Promptfoo-Restscope nur noch N1 (Rollen-Injection, §5.1).

### 3.4 W4 — Quoting-Fragilität + schwaches Kriterium (erledigt im Code)

**Finding:** `{{prompt}}` inline im Command-String bricht bei Multi-Line/Quotes; „parses without schema
error“ lässt diese Bug-Klasse durch.

**Fix (Implementiert, `#535`):** Provider-Commands enthalten bewusst **kein** `{{prompt}}` — Promptfoo
hängt den gerenderten Prompt als letztes argv-Element an (`gen_promptfoo_config.py:9-12, 40-43, 72-77`;
Test-Verbot `test_agent_eval_framework.py:122-124`). Der Bash-Pfad übergibt den Prompt als einzelnes
quoted Argument (`run_eval.sh:87`: `"$PROVIDER_SCRIPT" --agent "$role" "$prompt"`).

**Consequence:** Kein Restscope. Geschärftes Akzeptanzkriterium wandert in R6.

### 3.5 W5 — Aufwand & fehlende Kosten-Baseline

**Finding:** Phase 1 mit 2–3 PD unterschätzt (Wrapper-Generalisierung + Runner-Umbau + Judge-Harness +
Prompt-Decoupling + 10–16 Behavioral-Cases inkl. Rubric-Kalibrierung + Promptfoo-Validierung); realistisch
3–5 PD; Budget-Limits (step 9) ohne je gemessene Kosten.

**Fix:** Restscope-Rekalkulation — der Großteil der originalen Phase 1 ist durch #535/#539 bereits
gelandet (§0). Verbleibend (§6): **R1–R3 ≈ 1,5–2 PD, R4–R5 ≈ 2–3 PD, R6–R7 ≈ 1–1,5 PD, R8 ≈ 1–2 PD,
Summe ≈ 5,5–7,5 PD.** Gegencheck via `effort-estimator` über die Checkliste in §6 empfohlen. Die
Kosten-Baseline-Messung ist eigener Step (R7) und **muss vor** jeder Budget-Festlegung (R8/Q6) laufen.

**Consequence:** Plan v1s „2–3 PD Phase 1“ wird durch den dokumentierten Restscope ersetzt; die
W5-Forderung „document cost baseline per catalog class before step 9“ ist als R7-→-R8-Reihenfolge
eingebaut.

### 3.6 W6 — Silent exit 0 (erledigt im Code)

**Finding:** Exit 0 bei fehlender Quelldatei (Original-Zeile 44) macht nach Rollen-Parametrisierung einen
Tippfehler in der Rolle zu einem komplett-failing statt loudly-failing Run.

**Fix (Implementiert, `#535`):** Beide Wrapper beenden mit **exit 2** bei unbekannter/fehlender
Rollen-Datei (`provider-opencode.sh:58-62`, `provider-claude.sh:68-72`); verifiziert durch Test
(`test_agent_eval_framework.py:37-42`, stderr-Marker „unknown or missing role“).

**Consequence:** Kein Restscope.

### 3.7 W7 — Faktischer CI-Fehler (korrigiert; Integration specifiziert)

**Finding:** „Repo hat aktuell kein `.github/workflows/`“ ist falsch; `agent-eval.yml` muss mit existierender
CI integrieren; der „separate `--check` job“ ist Neubau, nicht Ist-Zustand.

**Fix:** Fakten korrigiert (auch schon im Eval-README, `README.md:46-52`). Aktueller Ist-Zustand:

| Workflow | Trigger | Inhalt | Evidenz |
|---|---|---|---|
| `validate.yml` | push `main`, PR `main`, Cron `0 3 * * *` | `pip install pyyaml`, `sync.py --validate`, Frontmatter-Inline-Lint | `validate.yml:3-9, 19-39` |
| `orchestration-test.yml` | push/PR mit Paths-Filter (`scripts/**`, `tests/**`, `config/**`, `agents/**`, eigener Dateipfad) | Pytest-Matrix 3.9/3.11/3.12 (`pip install -r tests/requirements.txt`), `sync.py --validate` | `orchestration-test.yml:6-29, 40-47` |

**Integrationspunkte für `agent-eval.yml` (Spec, Step R8):**

1. **Cron:** nightly **nicht** auf `0 3 * * *` (Kollision mit `validate.yml:9`) — Vorschlag `0 5 * * *`.
2. **Konkurrenz:** eigenes `concurrency: group: agent-eval, cancel-in-progress: true`.
3. **Deterministischer Teil läuft schon heute in CI:** Die Framework-Hygiene-Tests (W6, H3, SoT-Freshness,
   Katalog-Hygiene, Sidecar-Shape) sind Teil von `pytest tests/ -q` (`orchestration-test.yml:43-44`) —
   `agent-eval.yml` braucht dafür **keinen** „separate `--check` job“; nur die **Live-LLM-Evals** sind neu.
4. **Paths-Filter:** Propagations-Map nach H4 (§5.4), nicht generiertes Output-Verzeichnis.
5. **Kosten:** Report-Artefakt je Lauf; Budget-Default nach R7 (Q6). Nicht-blockierend bis zur
   Stabilitätsphase (analog Konzept §6: Stufung PR-Smoke → Nightly → Required-Check).

**Consequence:** Plan v1s falsche Grundannahme ist durch die obige Tabelle ersetzt; R8 baut
nur noch das Live-Eval-Job-Segment.

---

## 4. Hints H1–H6 — eingearbeitete Fixes

### 4.1 H1 — B4-Parity-Artefakte (Guideline)

Claude wird gegen `.claude/rules/use-orchestrator.md` (Regel-Datei **ohne** Frontmatter, nur eine
Routing-Tabelle) getestet, Opencode gegen die vollständige Agenten-Datei (Frontmatter + `mode: primary`
Flip + Doppel-Tabellen §2/§3). Guideline für Baseline-Doku (R7/R6-Report): Ein Parity-Fail zählt nur dann
als Provider-Differenz, wenn der Case **provider-neutral** ist (Kategorie ∉ {drift} und Assert-Klasse in
beiden Tiers messbar, §2.3). Drift-spezifische Cases (`drift-*`, nur Opencode/Gemini-relevant) sind aus
der Parity-Interpretation ausgeschlossen. Zusätzlich: Tier-Mismatch (`struct=full` vs.
`struct=text-only`) wird je Ergebniszeile reportet.

### 4.2 H2 — Stabilitäts-Semantik vereinheitlicht

Einheitlich über alle Katalog-Klassen (Routing, Behavioral, zukünftige Rubric-Cases):
**PASS = REPEAT/REPEAT** (default 3/3, `run_eval.sh:145-148`), **FLAKY = 1 ≤ n < REPEAT**
(`:153-154`), **FAIL = 0** (`:149-151`). Die Plan-v1-Formulierung „>2/3“ ist **gestrichen**. FLAKY zählt
nicht als Pass; Rubric-Cases (R5) erben dieselbe Semantik. Für CI-Promotion (Stufe Required-Check) gilt:
nur stabile Kataloge, FLAKY-Rate über die Stabilitätsphase dokumentiert (Konzept §6).

### 4.3 H3 — Frontmatter-Stripping (erledigt im Code)

Orchestrator behält Legacy-Quelle `.claude/rules/use-orchestrator.md` (existiert, verifiziert);
Nicht-Orchestrator-Rollen nutzen `.claude/agents/<role>.md` **mit** awk-Frontmatter-Strip
(`provider-claude.sh:64-77`; Dry-Parse-Test `test_agent_eval_framework.py:45-51`). Kein Restscope.

### 4.4 H4 — Paths-Filter über Propagations-Pfade

Der `agent-eval.yml`-Paths-Filter (R8) wird über die Propagationskette gemappt, nicht über generierte
Outputs:

```
config/role-defaults.yaml      → Quelle der Intent-Routing-Tabelle (+ generierter Katalog)
config/skills-registry.yaml    → Template-Variablen
scripts/lib/config.py          → Rendering/Filter (u. a. se-focus-Kriterium)
templates/  rules/             → Template-Layer
agents/**                      → 1-generic/2-platform-Quellen
tests/routing-llm-eval/**      → Kataloge/Wrapper/Runner selbst
scripts/gen_routing_llm_eval_catalog.py, scripts/gen_promptfoo_config.py  → Generatoren
```

`.opencode/agents/**`, `.claude/**` (generierte Outputs) sind **redundant und werden nicht** in den Filter
aufgenommen — jede relevante Änderung propagiert über eine der Quellen oben.

### 4.5 H5 — CI-Prerequisites (verifiziert + specifiziert)

- **Committete Artefakte verifiziert:** `.gitignore` (Zeilen 1–67) enthält keinen Eintrag für
  `tests/routing-llm-eval/` und keinen für generierte Agenten-Verzeichnisse (`.claude/`, `.opencode/`
  etc. sind nur mit lokalen Ausnahmen wie `settings.local.json` ignoriert) → generierte Agenten-Dateien
  und `promptfooconfig.generated.yaml` sind im Repo → Offline-Tests + `--check` laufen auf frischem
  Checkout (bestätigt durch den bestehenden CI-Pytest-Lauf).
- **R8-Spec (offen bis Umsetzung):** Install-Schritte für `claude`- und `opencode`-CLIs im Workflow,
  Auth via Secrets (`ANTHROPIC_API_KEY`; Opencode-Provider-Key) — Beschaffung ist Owner-Entscheidung
  (Q8), konsistent mit Konzept §6 („wichtiger, ungelöster Punkt“) und §7 Punkt 3.

### 4.6 H6 — Owner-Liste vervollständigt

Plan v1s Owner-Entscheidungsliste übernimmt zusätzlich Punkt 5 des Konzepts (§7): **Dual-Tabellen-Fix bei
bestätigtem Drift-Befund** als konditionale Folgeentscheidung — die Drift-Cases (`drift-*`, 5 Stück,
`catalog.manual.yaml:141-169`) sind Teil des Plans; fällt der Befund positiv aus, wird ein separates
Konzept/Issue zum Zusammenführen der Tabellen vorgeschlagen (nicht in diesem Plan gelöst). Aufgenommen als
Q7.

---

## 5. Neufunde der Reconciliation (über Review #523 hinaus)

### 5.1 N1 — Promptfoo-Modus injiziert `vars.role` nicht (Step R3)

**Befund:** `gen_promptfoo_config.py:66-70` erzeugt je Case `vars: {role, prompt}`, aber die
Provider-Commands sind statische Arrays ohne Rollen-Parameter (`gen_promptfoo_config.py:40-43`). Promptfoo
übergibt einem `exec`-Provider nur den (angehängten) Prompt — die Wrapper defaulten auf
`ROLE="orchestrator"` (`provider-opencode.sh:39`, `provider-claude.sh:29`). **Folge:** Im Promptfoo-Modus
würden rollenspezifische Behavioral-Cases (`role: developer`, `role: agent-meta-manager`) gegen den
falschen Agenten laufen — der Bash-Runner (`run_eval.sh:87`: `--agent "$role"`) ist korrekt, der
Promptfoo-Pfad nicht.

**Spec-Fix (R3):** Command-Arrays erweitern zu `["./provider-claude.sh", "--agent", "{{role}}"]` bzw.
analog für Opencode. `{{role}}` wird aus den Case-Vars gerendert; der Prompt bleibt weiterhin angehängtes
letztes Argument (W4-Eigenschaft unberührt). Begleit-Test: generierte Commands **müssen** `{{role}}`
enthalten und **dürfen** kein `{{prompt}}` enthalten (Erweiterung des bestehenden Tests,
`test_agent_eval_framework.py:120-124`). Verifikations-Gate: Var-Rendering in `exec`-Command-Arrays gegen
die tatsächlich genutzte Promptfoo-Version bestätigen (N3) — ge-gated wie der Antigravity-Spike, nicht
angenommen.

### 5.2 N2 — Spawn-Heuristik-Vokabel unverifiziert

`provider-opencode.sh:143-144` klassifiziert Spawn-Versuche über `tool == "task"` oder Event-Type
`tool_input`/`tool_call`. Die NDJSON-Event-Shapes der installierten Opencode-Version sind für diese
Felder nicht verifiziert (das ursprüngliche Spike-Dokument Konzept §5 Phase 2 verifizierte nur
`part.text`). Fix: Validierung im E2E-Lauf (R6) anhand realer Sidecars; Ergebnis + ggf. Korrektur der
Heuristik werden im Eval-README dokumentiert. Bis dahin ist `spawn_attempts` als *best effort* zu
behandeln — das ändert nichts an der B3-Semantik (§2.1), wohl aber an ihrer Verlässlichkeit.

### 5.3 N3 — Promptfoo-CLI-Installierbarkeit unverändert ungelöst

Konzept §7 Punkt 4 (Bash-Runner als Dauerlösung vs. weiterer Promptfoo-Versuch) ist weiter offen. Plan v2
fixiert die Konsequenz: **Der Bash-Runner ist der primäre, verpflichtende Ausführungspfad**; die
generierte Promptfoo-Config bleibt als zweiter Konsumpfad der Kataloge gepflegt (Freshness erzwungen),
promptfoos eigener Live-Betrieb ist optional und hinter Q5/R3-Verifikation gated.

---

## 6. Restscope-Phasenplan und Execution Checklist

Aufwandssumme: ≈ **5,5–7,5 PD** (§3.5); `effort-estimator` sollte als unabhängiger Gegencheck über diese
Checkliste laufen. Reihenfolge = Abhängigkeitsordnung.

### Phase A — Behavioral-Harness abschließen (B1-Restscope + N1)

- [ ] **R1a — Sidecar-Konsum im Bash-Runner (Spec §2.2/§2.4).** Runner setzt je Aufruf
  `EVAL_STRUCTURED_OUTPUT` (Temp-Datei), parst den Sidecar, wertet Katalogfeld `assert_struct` aus.
  Fehlender/unparsbarer Sidecar bei erwartetem strukturellem Assert → Case-FAIL (`struct=infra-error`);
  bei `stream: false` → Skip mit `struct=unavailable`-Marker. Neue Katalogfelder in
  `catalog.behavior.yaml`: `assert_struct: {spawn_attempts: 0}` für beide `b3-*`-Cases.
  *Akzeptanz:* Offline-Test mit Fake-Wrapper (synthetischer Sidecar, `spawn_attempts: 1`) → B3-Case
  FAIL; zweiter Fake-Test (`stream: false`) → Marker `struct=unavailable` in der Ergebniszeile; bestehende
  52 Cases unverändert grün im Hygiene-Testlauf.
- [ ] **R1b — Claude-Structured-Output-Spike (Spec §2.4).** Prüfen, ob die installierte `claude`-CLI
  strukturierte/Event-Ausgabe headless anbietet. Schriftliche Verifikationsnotiz (bestanden/nicht bestanden
  + CLI-Version + Beleg), Ergebnis entscheidet Q2.
  *Akzeptanz:* Notiz existiert; bei negativem Befund ist Tier `struct=text-only` als Endzustand im
  README dokumentiert (keine offene Rubric-Frage mehr).
- [ ] **R1c — NDJSON-Vokabel-Validierung (N2).** Teil des R6-Laufs; Heuristik bestätigt oder korrigiert.
  *Akzeptanz:* README-Absatz „Spawn-Erkennung“ nennt die verifizierten Event-Shapes samt
  Opencode-Version.
- [ ] **R3 — Promptfoo-Rollen-Injection (N1, Spec §5.1).** `{{role}}` in Command-Arrays + Begleit-Test,
  verifikations-gated (Q5).
  *Akzeptanz:* `--check` frisch; neuer Test-Assert (`{{role}}` vorhanden, `{{prompt}}` abwesend) grün;
  Verifikationsnotiz zum Var-Rendering existiert.

### Phase B — Judge-Harness (W1)

- [ ] **R4 — Judge-Spec-Implementierung (Spec-Tabelle §3.1).**
  *Akzeptanz:* Harness über 10 Behavioral-Cases: JSON-Parse-Erfolgsrate ≥95% nach ≤2 Retries (Rest
  fail-closed markiert); Temperatur 0 → zwei identische Eingaben liefern identische Verdicts; $/Case wird
  geloggt; Judge-Modell via `AGENT_EVAL_JUDGE_MODEL` override-bar.
- [ ] **R5 — Behavioral-Katalog-Erweiterung inkl. Rubric-Kalibrierung.** Ausbau 7 → 10–16 Cases
  (alle vier Kategorien; B2-Tool-Nutzungs-Fall mit `assert_struct.tool_events`-Prüfung für
  `struct=full`-Provider), davon ≥2 llm-rubric-Cases; 2–3 Kalibrierungs-Iterationen gegen False-Pass/-Fail.
  *Akzeptanz:* ≥10 Behavioral-Cases; Kalibrierungs-Log je Iteration mit False-Pass/False-Fail-Zählern und
  Rubric-Formulierung je Version; `test_agent_eval_framework.py`-Hygiene (IDs unique, Asserts vorhanden)
  bleibt grün.

### Phase C — Validierung & Baseline (W5)

- [ ] **R6 — End-to-end-Lauf beider Provider (ersetzt Plan-v1-Step-5-Kriterium, W4).** Voller Katalog
  (52+ Cases), `REPEAT=1` Rauchlauf je Provider, dann `REPEAT=3` für Behavioral-Cases.
  *Akzeptanz:* Exit-2-Aufkommen = 0 (kein Infrastruktur-Fehler); je Case nicht-leeres `final_text`
  bzw. dokumentierter, verstandener Leerfall; Sidecar je Behavioral-Case vorhanden; R1c-Ergebnis
  festgehalten. *Voraussetzung:* lokale CLIs + Auth vorhanden (H5) — sonst gated auf R8-Umgebung.
- [ ] **R7 — Kosten-Baseline je Katalog-Klasse (W5-Kernforderung).** Messung: Routing-Klasse,
  Behavioral-Text-Klasse, Rubric-Klasse; je Provider $/Case und $/Voll-Lauf; Ergebnis als Tabelle im
  Eval-README. *Akzeptanz:* Tabelle existiert mit Messdatum, Repeat-Faktor und Modell-Tier; Budget-Default
  (Q6) daraus ableitbar.

### Phase D — CI-Integration (W7, H4, H5)

- [ ] **R8 — `agent-eval.yml` (Spec §3.7).** Nightly Cron ≠ 03:00 (Vorschlag `0 5 * * *`), `workflow_dispatch`,
  Paths-Filter nach §4.4-Map, `concurrency: agent-eval`, CLI-Install + Secrets (Q8), Nicht-blockierend,
  Kosten-Report-Artefakt, Budget-Gate (Q6, erst nach R7).
  *Akzeptanz:* Erster grüner GitHub-Run: deterministische Hygiene-Tests separiert von Live-Eval-Job;
  Cron-Zeit ≠ `0 3 * * *`; Paths-Filter deckt alle Propagationsquellen aus §4.4 ab und enthält **kein**
  generiertes Output-Verzeichnis; Kosten-Artefakt wird hochgeladen.

---

## 7. Offene Fragen für den nächsten Concept-Review-Pass

Jede Frage kommt mit Proposed Default — Review-Pass kann per Akzeptanz/Änderung entscheiden (bewusst keine unentschiedenen Platzhalter):

| # | Frage | Proposed Default |
|---|---|---|
| Q1 | Judge-Modell final (W1) | Günstigstes stabiles Claude-Tier (`haiku`-Klasse), Kostenziel <$0.01/Case @ repeat=1; Verifikation durch R7-Baseline |
| Q2 | Claude-seitige strukturierte Events (B1-Restscope) | R1b-Spike zuerst (≤0,5 PD); bei negativem Befund Tier `struct=text-only` als Endzustand, keine Annäherungs-Lösung |
| Q3 | B3-Politiksemantik: `spawn_attempts > 0` = FAIL unabhängig vom Infra-Ausgang? | Ja — Policy-Verletzung zählt der Versuch, nicht der Ausgang (§2.1); Diagnose bleibt im Sidecar |
| Q4 | FLAKY-Gewichtung bei Rubric-Cases (H2) | FLAKY ≠ PASS; identische REPEAT/REPEAT-Semantik wie Text-Asserts; Promotion auf Required-Check nur aus stabiler Stabilitätsphase |
| Q5 | Promptfoo-Live-Betrieb (N3) | Bash-Runner bleibt primär/verpflichtend; generierte Config bleibt gepflegt (Freshness), Promptfoo-Live hinter R3-Verifikations-Gate |
| Q6 | Budget-Grenze `agent-eval.yml` (W5) | Erst nach R7-Baseline: Limit = 3× gemessener Nightly-Voll-Lauf; Überschreitung → Run bricht nach Report ab |
| Q7 | Owner-Liste Punkt 5 (H6): Dual-Tabellen-Fix bei positivem Drift-Befund | Als konditionale Folgeentscheidung übernommen; separates Konzept/Issue, nicht Teil dieses Plans |
| Q8 | CI-Secrets + CLI-Install (H5) | Beschaffung `ANTHROPIC_API_KEY` + Opencode-Provider-Key als GitHub Secrets (Owner-Entscheidung, Konzept §7 Punkt 3); Install via offizieller Kanäle im R8-Workflow |

---

## 8. Korrigierte Issue-Fakten und Annahmen

Gegenüber Issue #523 (bzw. dessen Review-Basis) korrigierte bzw. präzisierte Fakten:

1. **Case-Zahl:** „45“ → **52** (Behavioral-Katalog `catalog.behavior.yaml` mit 7 Cases ist seit Review
   gelandet, `#535`).
2. **Wrapper-Revision:** Review beschrieb v1-Wrapper („returns only the last text event, lines 96–114“) —
   aktuell v3 mit `--agent <role>`, exit-2-Guard, Isolation (`repo-readonly`, `#539`) und strukturellem
   Sidecar; alle Original-Zeilenverweise sind obsolet (Analogie zur Phase-4c-Methode: Issue-Zeilenangaben
   verfallen, Code gilt).
3. **W6-Fakten:** „exits 0 on missing source file (line 44)“ → exit 2 an `provider-opencode.sh:58-62` und
   `provider-claude.sh:68-72`, testgestützt.
4. **W2-Fakten:** „lines 53–56 wrap every task“ → gilt nur noch für den Legacy-Pfad; Behavioral-Pfad ist
   decoupled (`run_eval.sh:73-79`).
5. **W7-Fakten:** Workflows-Bestand bestätigt und präzisiert (Trigger-Matrizen in §3.7); der
   v1-geforderte „separate `--check` job“ ist redundant — SoT-Freshness läuft bereits im
   Orchestrations-Pytest-Lauf.
6. **Annahme Original-Artefakt:** Der Draft-Plan von 2026-08-21 ist als Datei nicht mehr verfügbar; diese
   Revision rekonstruiert alle Prüfgegenstände aus dem Review-Text und verifiziert sie gegen den Code.
   Falls ein Archiv des Original-Plans existiert, wäre eine Abgleich-Runde im nächsten Review-Pass
   willkommen, blockiert aber nichts (alle Findings sind dateiunabhängig adressiert).
7. **Self-Spawn-Vokabel:** Review-positiv-Verifikation bleibt gültig — `HARD REJECT`/„Self-Spawn erkannt“
   ist real im Template (`agents/1-generic/orchestrator.md:19, 263-266`); die B3-Regexes in
   `catalog.behavior.yaml:21-23, 29-32` greifen darauf zu.

## 9. Nächste Schritte

1. Erneuter Concept-Review-Pass über **dieses Dokument** (korrection_hints-Modus gemäß Issue-Next-steps:
   „checking correction_hints only“) — Entscheidung über Q1–Q8 (Default-Akzeptanz genügt).
2. Nach Approve: Ausführung über `orchestrator`/`feature-lifecycle` mit Steps R1a–R8 (§6) in der
   gegebenen Reihenfolge; Phase A ist dabei teils offline testbar (R1a, R3) und kann parallel zu R1b
   laufen; R4–R8 folgen der Abhängigkeitsordnung.
3. Issue #523 bleibt offen bis zum Approve-Verdict des erneuten Review-Passes.
