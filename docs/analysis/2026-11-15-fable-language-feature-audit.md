# Audit: Sprach-Feature (Language / Speech-Mode) — warum es nicht greift

- **Status:** Analyse (kein Beschluss)
- **Datum:** 2026-11-15
- **Quelle:** Fable/Opus-Audit, Verifikationsstand siehe Verifikationsbericht (docs/analysis/2026-11-15-fable-verification-of-unchecked.md)
- **Modellherkunft:** Opus-Fortsetzung nach Fable-Rate-Limit
- **Issues:** #1237–#1276 (Audit-Folgeissues)
- **Zugehörige Berichte:** docs/analysis/2026-11-15-fable-framework-settings-audit.md, docs/analysis/2026-11-15-fable-language-feature-audit.md, docs/analysis/2026-11-15-fable-orchestration-rollout-audit.md, docs/analysis/2026-11-15-fable-verification-of-unchecked.md

> Stand: 2026-11-15, Branch `chore/main-checkout-parking` (= origin/main + Parking-Commit). Read-only-Analyse, keine Änderungen am Repo.
> Autor: Fable-Subagent (Auftrag 2/3). Kurzform, Bullet Points, Belege als `Datei:Zeile`.

## 0. TL;DR

- Das Rendering funktioniert: Die Werte kommen an, Platzhalter werden nicht roh ausgegeben, und die Rules werden auf Claude geladen, auch in Subagenten. Das Problem liegt im **Inhalt und Modell** der Regeln, nicht in der Technik.
- Hauptursache 1: Commit `89d44ddd` (2026-07-25) hat `rules/1-generic/language.md` gekürzt. Dabei gingen der Geltungsbereich („alle Agenten und Hauptchat“) und die Artefakt-Zuordnung verloren (Issues → extern EN, Berichte → intern). Der Fix aus #198 ist damit faktisch zurückgenommen.
- Hauptursache 2: Für Issues (außer `feedback`), PRs, Subagenten-Berichte, A2A-Briefe, Specs und Pläne gibt es weder einen Key noch eine Zeile. Die Sprache wird ad hoc gewählt. Die 60 neuesten Issue-Bodies sind entsprechend gemischt: 27 DE / 27 EN / 6 gemischt.
- Hauptursache 3: Im Orchestrator steht `Documents → {{DOCS_LANGUAGE}}`. Das rendert als „Englisch“ (externe Doku) statt mit der Sprache für interne Doku.
- Weitere Ursachen: 4 widersprüchliche Default-Philosophien; `speech-mode` hart deutsch und nur auf Rules-Providern (fehlt in AGENTS.md); kein Vorrang zwischen Stil, Output-Kontrakt und Plugin-Hooks; keine Durchsetzung oder Verhaltens-Tests.
- Empfehlung: Zwei Achsen trennen, `prompt_language` = en (fix) und `output_language` je Artefakt (typisierte Matrix). PR 1 (S): Rule-Scope und Matrix wiederherstellen, Orchestrator-Platzhalter und speech-Geltung korrigieren. PR 2 (M): Schema `language.*`, Defaults, AGENTS.md, Admin-UI, Brief-Zeile, Lint. 8 Entscheidungen für den Nutzer in §5.

## 1. Konfiguration & Rendering

**Konfig-Keys (`.meta-config/project.yaml`)**
- `variables.COMMUNICATION_LANGUAGE/USER_INPUT_LANGUAGE/DOCS_LANGUAGE/INTERNAL_DOCS_LANGUAGE/CODE_LANGUAGE` — `.meta-config/project.yaml:187-191` (Deutsch/Deutsch/Englisch/Deutsch/Englisch).
- Freitext-Variablen, **nicht im Schema typisiert** (kein Treffer in `config/project-config.schema.json`), keine Enum/Normalisierung („Deutsch“ vs. „de“ vs. „english“).
- `speech-mode: short` — `.meta-config/project.yaml:176`; Schema `config/project-config.schema.json:720-722`.
- `conventions.issues.language` → `ISSUE_LANGUAGE` — `scripts/lib/config.py:2765-2776`, Default **„english“** (kleingeschrieben, anderes Vokabular als „Englisch“); im Projekt nicht gesetzt.
- `knowledge.schema-language: auto` — `.meta-config/project.yaml:54`, Schema `:2054-2057`.
- **Kein** Key für: PR-Sprache, Subagenten-Bericht/Handback, A2A-Brief, Agent-Prompt-Sprache, Spec/Plan-Sprache.

**Defaults — inkonsistent**
- `scripts/lib/config.py:223-228` `_VARIABLE_FALLBACKS`: Deutsch/Deutsch/Englisch/Deutsch/Englisch (spiegelt agent-meta selbst → Konsumentenprojekte ohne Werte bekommen Deutsch).
- `scripts/lib/setup.py:303-310` Wizard-Defaults: **English** für alle.
- `scripts/lib/standalone.py:69-72`: „the language the user writes in“.
- `ISSUE_LANGUAGE` Default „english“ (`config.py:2774`).
- → 4 verschiedene Default-Philosophien für dasselbe Feature.

**Rendering**
- Rule-Quelle `rules/1-generic/language.md` (5-Zeilen-Tabelle, Platzhalter) → .claude/rules/language.md (gerendert, korrekt, keine Leaks).
- Speech: `speech/<mode>.md` 1:1 kopiert → `<rules_dir>/speech-mode.md` (`scripts/lib/rules.py:821-868`); nur aufgerufen wenn `has_rules` (`scripts/lib/sync_pipeline.py:1534-1540`).
- Agent-Templates: Platzhalter-Substitution in 62/101 `agents/1-generic/*.md` (39 ohne jeden `*_LANGUAGE`-Platzhalter, u.a. `devops-engineer`, `docker`, `api-specialist`, `effort-estimator`, `meta-feedback`, alle `se-*`).
- Routing-Beispiele: `COMMUNICATION_LANGUAGE` wählt sprach-getaggte `examples` (`scripts/lib/agents.py:328`, `scripts/lib/delegation_table.py:235-250`).
- CLAUDE.md „## Sprachregeln“ (`CLAUDE.md:106-114`) ist **handgeschrieben, außerhalb des managed-Blocks** (`:68-100`) — Duplikat der Rule, driftet unabhängig.
- Kontext-Anker: nur Überschrift `# Sprachregeln` geprüft (`config/context-anchors.yaml:59,75,94`), nicht die Werte; `speech-mode` gar nicht verankert.

**Provider-Abdeckung** (`config/ai-providers.yaml`, `has_rules`)
| Provider | language-Rule | speech-mode | Agent-Platzhalter |
|---|---|---|---|
| Claude | .claude/rules/language.md (always-on) | .claude/rules/speech-mode.md | ja |
| Continue / Copilot | eigenes `rules_dir` | ja | ja |
| Opencode / Gemini / Mammouth / Codex / ZCode / KimiCode | in `AGENTS.md:75` eingebettet | **nein** (kein Treffer „speech“/„Kommunikationsstil“ in `AGENTS.md`) | ja |
- Memory-Befund bestätigt: `rules-preset` (hier `lazy`, `.meta-config/project.yaml:11`) ist auf Claude wirkungslos — Rules sind immer geladen, d.h. Sprach-Rule **ist** im Hauptkontext präsent; das Problem ist nicht Ladung, sondern Inhalt/Priorität.

## 2. Wirkung auf Subagenten & Artefakte, Widersprüche

**Subagenten (Claude)**
- Claude-Subagenten erhalten CLAUDE.md + `.claude/rules/*` (inkl. `language.md`, `speech-mode.md`) — **empirisch** in diesem Lauf beobachtet (System-Reminder des Subagenten); keine Code-Belegstelle im Repo (Harness-Verhalten).
- Zusätzlich injiziert ein **globaler** SubagentStart-Hook (Ponytail-Plugin, `~/.claude/settings.json`) eigene Stilregeln („End your reply with one or two lines…“) → konkurriert mit `speech-mode` („überschreibt alle anderen Stilanweisungen“, .claude/rules/speech-mode.md:3); Priorität undefiniert.
- Problem ist nicht Ladung, sondern **Zuordnung**: Ein Subagenten-Bericht geht an den Orchestrator/Main-Chat, nicht an den Nutzer → keine Tabellenzeile passt („User-Kommunikation“? „Interne Doku“?). Agent entscheidet ad hoc → gemischte Sprache.
- Opencode/Gemini & Co.: Sprach-Rule via `AGENTS.md:75` vorhanden, `speech-mode` fehlt komplett (s. §1).

**Agent-Templates**
- Prompt-Sprache heterogen (Heuristik, .tmp/audit/scratch/lang-template-classify.txt): 88 EN / 13 DE / 18 gemischt (generic+platform; `orchestrator.md` selbst gemischt 123 DE- vs. 341 EN-Marker).
- Sprachanweisung meist eine Zeile am Ende (`agents/1-generic/developer.md:146`, `git.md:192`) — schwache Position; 39/101 generic-Templates ohne jede Sprachanweisung (§1).
- `orchestrator.md:405` → „Documents → `{{DOCS_LANGUAGE}}`“ = **Englisch** gerendert (.claude/agents/orchestrator.md:570, .opencode/agents/orchestrator.md:573). DOCS_LANGUAGE = *externe* Doku → Specs/Pläne/Briefe des Orchestrators sollen Englisch sein, Rule sagt interne Doku Deutsch. **Falscher Platzhalter.**
- Keine Sprachanweisung für: A2A-Brief, Handback/STATUS-RESULT-Block (nur Feldnamen kanonisch EN, `orchestrator.md:293`; Inhalt offen, vgl. #541), Nutzer-Endbericht des Orchestrators.
- Nicht-substituierte Ad-hoc-Formeln statt Platzhalter: `agent-meta-scout.md:122` („user's language“), `effort-estimator.md:145` („may be bilingual“).

**Artefakte**
- Issues: `feedback.md:120` → `{{ISSUE_LANGUAGE}}` = „english“ (gerendert .claude/agents/feedback.md:126); `meta-feedback` hart EN. Main-Chat/Orchestrator/Subagenten, die direkt `gh issue create` nutzen, sehen nur `language.md` → keine Zeile „Issues“.
  - Beleg: 60 neueste Issues — Titel 100 % EN (Conventional-Format), Bodies **27 DE / 27 EN / 6 gemischt** (Heuristik, .tmp/audit/scratch/lang-issues-recent.txt; z.B. #1271-#1276 „## Befund“ DE, #1278/#1279 EN). DE-Bodies zudem ohne Umlaute („beruehrt“).
- Commits: `CODE_LANGUAGE`=Englisch + `commit-conventions.md` → greift (Commits durchgängig EN, `git log`).
- PR-Texte: kein Key, keine Zeile → undefiniert.
- Docs: `documenter.md:129-134` korrekt differenziert (README=DOCS, Rest=INTERNAL).

**Widersprüche**
- W1 Regression `89d44ddd` (2026-07-25, „fix: resolve variable injection…“): `rules/1-generic/language.md` von 5 erläuterten Zeilen auf Stichworte gekürzt — entfernt: „Diese Regel gilt für alle Agenten und den Hauptchat“, Artefakt-Aufzählung „Externe Dokumente (README, CHANGELOG, Release Notes, **GitHub Issues**)“, „Interne Dokumente (…, **Berichte**)“, „Code-nahe Artefakte (…, Test-Beschreibungen)“, Abschnitt „Rollenspezifische Präzisierungen“. → Seitdem ist die Issue-/Bericht-Zuordnung mehrdeutig (#198 hatte genau das 2026-05 gelöst).
- W2 Issue-Sprache: Rule (heute: unbestimmt) vs. `ISSUE_LANGUAGE`=english vs. Praxis 50/50.
- W3 Orchestrator „Documents → DOCS_LANGUAGE (EN)“ vs. Rule „Interne Doku DE“ vs. CLAUDE.md:110-114 „alle anderen Dokumente → Deutsch“.
- W4 Default-Philosophien: Fallback DE (`config.py:223`) vs. Wizard EN (`setup.py:303`) vs. standalone „user's language“ vs. issues „english“.
- W5 `speech-mode: short` („Keine Zusammenfassung“, „max. 1 Satz pro Punkt“) vs. Templates/Pipelines mit Pflicht-Berichtsformaten (STATUS/RESULT/ARTIFACTS, TL;DR-Report-Kontrakte, #1278) und Ponytail-Hook-Schlusszeilen → kein definiertes Vorrangmodell.
- W6 Always-on-Kontext zweisprachig: Rules deutsch (CRITICAL GATE, Branch-Guard), Templates überwiegend englisch → Modell spiegelt Eingabesprache, keine stabile Ausgabesprache.
- W7 CLAUDE.md:106-114 (handgepflegt) dupliziert .claude/rules/language.md mit abweichender Granularität.

## 3. Defekte / Lücken

**Rendering (funktioniert — kein Render-Bug)**
- .claude/rules/language.md = Quelle mit eingesetzten Werten (diff leer); .claude/rules/speech-mode.md = `speech/short.md` byte-identisch.
- Keine `{{…LANGUAGE…}}`-Leaks in `.claude/`, `CLAUDE.md`, `AGENTS.md`; `ISSUE_LANGUAGE` immer gesetzt (`config.py:2774`), `EXTERNAL_DOCS_LANGUAGE` in `_reference-agent.md:121,175` bewusst escaped `{{%…%}}` (#983).
- Render-Tests vorhanden: `tests/test_rule_variables.py`, `test_config_variable_fallbacks.py`, `test_issue_language.py` (4 Tests), `test_routing_examples_language.py`.

**Defekte / Lücken (Ursachen, nach Gewicht)**
- D1 **Inhaltliche Regression** der Rule (`89d44ddd`, s. W1): Geltungsbereich + Artefakt-Zuordnung gelöscht → Hauptursache für Issue-/Bericht-Sprachmix.
- D2 **Fehlende Artefaktklassen**: Issues (außer `feedback`), PRs, Subagenten-Berichte/Handbacks, A2A-Briefe, Specs/Pläne, Audit-Reports, Agent-Prompts — keine Zeile, kein Key.
- D3 **Falscher Platzhalter** `orchestrator.md:405` (`DOCS_LANGUAGE` statt `INTERNAL_DOCS_LANGUAGE`).
- D4 **speech-mode nur für `has_rules`-Provider** (`sync_pipeline.py:1534-1540`) — 6 AGENTS.md-Provider ohne Stil-Rule, obwohl Schema (`project-config.schema.json:722`) „for all agents“ verspricht.
- D5 **speech/*.md hart deutsch**, ohne Platzhalter (alle 9 Dateien, 0 `LANGUAGE`-Tokens) → EN-Projekte bekommen deutsche Stilregeln; „Kommunikationsstil“ unterscheidet nicht Nutzerantwort vs. Artefakt (Issue-Body „Short“?).
- D6 **Keine Durchsetzung**: kein Hook/Lint für Issue-/PR-/Commit-Sprache (`.claude/hooks/` ohne Sprachprüfung; `commit-conventions` prüft Format, nicht Sprache); Kontext-Anker prüfen nur `# Sprachregeln`-Heading (`context-anchors.yaml:59`), nicht Werte/Zeilen; `speech-mode` unverankert.
- D7 **Kein Vorrangmodell**: `speech-mode.md:3` „überschreibt alle anderen Stilanweisungen“ vs. Output-Kontrakte (STATUS/RESULT/ARTIFACTS, Report-Kontrakte) vs. externe Plugins (Ponytail-SubagentStart-Hook). Ein „Short“-Subagent darf seinen Pflichtbericht formal nicht liefern.
- D8 **Freitext-Werte ohne Schema/Normalisierung**: „Deutsch“, „Englisch“, „english“, „en/de“-Aliasse (`delegation_table.py:235-250`), `examples: {en, de}` im Routing-Plan → drei Vokabulare.
- D9 **Default-Chaos** (W4): Konsumentenprojekt ohne Werte → deutsche Rule (`config.py:223`), Wizard → EN, Issues → EN.
- D10 **Kein Per-Rolle-Override** (z.B. `feedback` EN, Rest DE) außer Sonderfall `ISSUE_LANGUAGE`; Admin-UI kann `issues.language` nicht editieren (#1204 OPEN).
- D11 **Zweisprachiger Always-on-Kontext** (W6) + Duplikat in CLAUDE.md (W7).
- D12 **Keine Verhaltens-Tests/Evals** zur Ausgabesprache (nur Render-Tests); Eval-Korpus #969 ohne Sprachachse (nicht im Detail geprüft).
- Compaction: Rules/CLAUDE.md sind System-Kontext und überleben Compaction (Harness-Annahme, **unverifiziert**); kein SessionStart/compact-Hook im Repo. Eher kein Haupttreiber.

**Issues/Specs zur Sprache — Umsetzungsstand** (.tmp/audit/scratch/lang-issues-search.txt)
- #198 CLOSED (2026-05-24) Issue-Sprache konsistent → Fix später durch `89d44ddd` (2026-07-25) entwertet.
- #262 CLOSED Release-Notes DE statt EN · #541 CLOSED DE-Envelope-Labels · #579 CLOSED `ISSUE_LANGUAGE` · #733 CLOSED Platzhalter-Leaks · #983 CLOSED `EXTERNAL_DOCS_LANGUAGE`.
- OPEN: #1204 (issues.language nicht in UI), #780 (Routing-Sprache Design C), #779 (Routing-Audit inkl. Sprachmatch), #957 (PR-Templates — PR-Sprache dort andocken), #1186 (Artefakt-Locations-Matrix — natürlicher Ort für Sprach-Matrix), #1278 (Report-Kontrakt).
- Muster: 6 Einzelfix-Issues, je ein Symptom; kein Gesamt-Design. Kein Spec/Plan in `docs/specs`/`docs/plans` zur Sprache.

## 4. Konsequenzen für Verbesserungsschleife & Intent-Routing

- Pläne liegen in .tmp/plans/ (nicht `docs/plans/`): `2026-11-14-agent-improvement-loop-plan.md`, `2026-11-14-intent-routing-table-plan.md`.
- Loop-Plan `:75` „Prompt-Sprache EN“ + `:221` E2 → **richtig**, aber `:76` („language.md/speech-mode regeln nur Nutzer-Ausgabe → kein Konflikt; eine Zeile ‚Agent-Prompts: Englisch‘ schließt die Lücke“) ist **zu optimistisch**: D1/D2/D3/D7 bleiben offen. EN-Prompt ohne explizite Ausgabesprache verstärkt EN-Ausgabe in Berichten (Modell spiegelt Prompt-Sprache) — Hypothese, unverifiziert.
- Loop-Plan R11 (`:93`) Lint „DE-Markerquote < 5 %“ prüft Prompt, nicht Ausgabe → ergänzen: Pflicht-Sektion `Language` (Rubrik `:169` hat sie schon als kanonischen Namen) mit **Ausgabe-Platzhaltern je Artefakt**.
- Loop-Plan muss D3 (Orchestrator-Platzhalter) als Korrektur aufnehmen, sonst übernimmt der Rewrite den Fehler.
- Routing-Plan `:143` `examples: {en, de}` vs. `COMMUNICATION_LANGUAGE: Deutsch` → nur über Alias-Logik verbunden; bei normiertem Code (`de`/`en`) diesen Schlüssel übernehmen. Routing-Plan `:305` „keine Änderung der Sprachregel hier“ — kompatibel.

**Saubere Sprach-Architektur (Zielmodell)**
- Zwei Achsen strikt trennen:
  - `prompt_language` = intern, framework-fix **en** (Templates, Rules-Prosa langfristig, Envelope-Feldnamen).
  - `output_language` je Artefaktklasse, projektseitig, ISO-Code.
- Artefakt-Sprachen-Matrix (Vorschlag):

| Artefaktklasse | Key | agent-meta | Framework-Default |
|---|---|---|---|
| Antwort an Nutzer (Main-Chat, Orchestrator-Endbericht) | `user` | de | en |
| Subagenten-Bericht/Handback (Inhalt) | `agent_report` | de | = `user` |
| A2A-Brief Orchestrator→Worker | `agent_brief` | en | en (= Prompt) |
| Interne Doku (Specs, Pläne, Audits, ARCHITECTURE) | `internal_docs` | de | = `user` |
| Externe Doku (README, CHANGELOG, Release Notes) | `external_docs` | en | en |
| Issues (Titel+Body), PR-Texte | `tracker` | **Entscheidung E1** | en |
| Code-Kommentare, Commit-Messages, Test-Namen | `code` | en | en |
| Envelope-Feldnamen (STATUS/RESULT/…) | — (fix) | en | en |

- `speech-mode` gilt nur für `user` + `agent_report`, nicht für Artefakte mit eigenem Format/Kontrakt.

## 5. Empfehlung

**Zielbild**
- Konfig-Schema (`project.yaml`, typisiert in `config/project-config.schema.json`):
  ```yaml
  language:
    user: de            # ISO 639-1
    agent_report: user  # Referenz erlaubt
    internal_docs: de
    external_docs: en
    tracker: en         # Issues + PRs; ersetzt conventions.issues.language (Alias/Migration)
    code: en
  ```
  - Alte 5 `variables.*_LANGUAGE` + `ISSUE_LANGUAGE` werden aus `language.*` **abgeleitet** (Rückwärtskompatibel, Templates unverändert lauffähig); Anzeige-Namen („Deutsch“) per Mapping.
  - Ein Default-Satz (`en` überall, `user` = Eingabesprache) für Fallback, Wizard und standalone (D9).
- Rendering je Provider: eine generierte Rule `language.md` (Matrix aus §4 inkl. Zeile „Gilt für Hauptchat **und alle Subagenten**; Berichte an den Orchestrator → `agent_report`“) — `has_rules`-Provider nativ, AGENTS.md-Provider eingebettet (wie heute). `speech-mode` zusätzlich in AGENTS.md einbetten (D4).
- Vorrang (in Rule, 3 Zeilen): Output-Kontrakt/Format > Sprache-Matrix > speech-mode-Stil; speech-mode nur für `user`/`agent_report` (D7, D5).
- Subagenten-Weitergabe: Pflicht-Zeile im A2A-Brief des Orchestrators „Report language: {{AGENT_REPORT_LANGUAGE}}“ (redundant zur Rule, robust gegen Provider ohne Rules-Vererbung); Rubrik-Sektion `Language` je Template mit Artefakt-Platzhaltern (Loop-Plan R11).
- Durchsetzung (Convention boundary):
  - Lint/Test: jede Template-`Language`-Sektion referenziert nur gültige Platzhalter; kein `DOCS_LANGUAGE` für interne Artefakte (fängt D3); Anker auf Matrix-Zeilen statt nur Heading (D6).
  - Optionaler PreToolUse-Hook auf `gh issue create|gh pr create`: Heuristik DE/EN-Marker im `--body` vs. `tracker` → Warnung (nicht Block). Skip, falls zu teuer.

**PR-Schnitt (max. 2)**
- PR 1 „fix: restore language rule scope and artifact mapping“ — **S**
  - `rules/1-generic/language.md`: Geltungsbereich + Artefakt-Zeilen (Issues/PRs, Berichte, Briefe, Specs/Pläne) zurück, mit bestehenden Platzhaltern (`ISSUE_LANGUAGE` für Tracker).
  - `orchestrator.md:405` → `INTERNAL_DOCS_LANGUAGE` (+ Nutzer-/Bericht-Zeile).
  - `speech/*.md`: Geltung „nur Nutzerantwort/Bericht, nicht Artefakte; Output-Kontrakte gehen vor“.
  - CLAUDE.md-Duplikat (W7) auf Projekt-Abweichungen reduzieren (Nutzer-Bereich, manuell).
  - Kontext-Anker + 1 Test.
- PR 2 „feat: typed language matrix in project.yaml“ — **M**
  - Schema `language.*`, Ableitung alter Variablen, Default-Vereinheitlichung (config/setup/standalone), speech-mode in AGENTS.md, Admin-UI-Felder (#1204), Brief-Zeile im Orchestrator, Lint.
  - Am besten **vor bzw. als Teil** von Loop-Plan Phase „Rubrik“, damit der Template-Rewrite die neuen Platzhalter direkt nutzt.

**Rebaseline-Auswirkung**
- PR 1: ändert gerenderte Rule + Orchestrator → AC-01-Hashes (`tests/fixtures/ac01-baseline/hashes.json`), compact-golden/orchestrator.md, ggf. `topology-golden/*`, `slimming-golden/*` neu; Kontext-Budget-Ceilings marginal (+~0,3 KB Rule, nicht gemessen).
- PR 2: zusätzlich Scenario-Configs (`tests/scenarios/configs/*`) und alle Rollen mit Sprach-Platzhaltern (Werte gleich → Hash-neutral, sofern Anzeige-Namen identisch bleiben).

**Risiken**
- Zweite Rebaseline kurz nach #1236 (Phase D) → Merge-Konflikte mit laufendem Loop-/Routing-Plan; PR 1 klein halten.
- Ableitungs-Mapping „Deutsch“↔`de` bricht Konsumentenprojekte mit exotischen Freitext-Werten → Freitext-Fallback beibehalten.
- Mehr Rule-Zeilen = mehr always-on Tokens (Claude lädt Rules immer; Memory) — Matrix kompakt halten (≤ 12 Zeilen).
- Verhaltenswirkung nicht garantiert (Prompt-Konvention); ohne Eval keine Messung.

**Entscheidungen für den Nutzer**
- E1 Tracker-Sprache (Issues+PRs) für agent-meta: **en** (Empfehlung; konsistent mit Titeln, `ISSUE_LANGUAGE`, #198) vs. de.
- E2 Subagenten-Berichte an Orchestrator/Main-Chat: **= Nutzersprache (de)** (Empfehlung; landen beim Nutzer) vs. en.
- E3 A2A-Briefe Orchestrator→Worker: **en** (Empfehlung; = Prompt-Sprache, token-günstiger) vs. de.
- E4 Specs/Pläne/Audits: **= interne Doku (de)** (Empfehlung) — bestätigt Status quo.
- E5 Rules-Prosa (heute DE) mittelfristig auf **en** umstellen (Empfehlung: ja, mit Loop-Plan; Anker-Rebaseline nötig) vs. DE lassen.
- E6 speech-mode-Vorrang: **Output-Kontrakt > Sprache > Stil** (Empfehlung) vs. Stil absolut.
- E7 Durchsetzung per Hook-Warnung auf `gh issue/pr create`: **nein vorerst** (Empfehlung; erst PR 1 wirken lassen) vs. ja.
- E8 Framework-Default für Konsumentenprojekte: **en / Eingabesprache** (Empfehlung) statt Deutsch-Fallback.

**Quick Wins (ohne PR 2)**
- `orchestrator.md:405` Platzhalter korrigieren (1 Zeile).
- `language.md` Zeilen „Gilt für Hauptchat und alle Subagenten“ + „Issues/PRs → `ISSUE_LANGUAGE`“ + „Berichte/Specs/Pläne → interne Doku“ zurück (3 Zeilen).
- Orchestrator-Briefe: Sprache des erwarteten Berichts explizit nennen (Prompt-Konvention, sofort nutzbar).
- `issues.language` im eigenen `project.yaml` explizit setzen (dokumentiert Entscheidung E1).

## 6. Nicht geprüft

- Tatsächliches Harness-Verhalten Opencode/Gemini-Subagenten (laden sie AGENTS.md?) — nur Claude empirisch.
- Compaction-Verhalten (Rules nach Kompaktierung präsent?) — Annahme.
- Inhalt der gerenderten Agent-Dateien für Continue/Copilot/Gemini im Detail.
- Eval-Korpus #969 und Admin-UI-Code (`docs/ui/admin-ui.html`) auf Sprach-Felder.
- Sprachheuristiken (Issues, Templates) sind Wortmarker-Zählungen, keine Sprach-Erkennung.
- Token-Kosten der Matrix-Rule nicht gemessen (kein tiktoken-Lauf).
- PR-Texte (`gh pr list`) nicht stichprobenartig geprüft.
- `knowledge.schema-language: auto` — Auflösungslogik nicht gelesen.
