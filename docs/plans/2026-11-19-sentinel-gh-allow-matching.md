---
pipeline_stages:
  implement: 1
status: APPROVED
date: 2026-11-19
spec: docs/plans/2026-11-19-sentinel-gh-allow-matching.md
spec-status: APPROVED
klasse: M
branch: fix/sentinel-gh-allow-matching
---

# Sentinel-Präfix verhindert Allow-Matching für reine gh-Aufrufe — Spec + Plan

> Status: APPROVED — vom Nutzer am 2026-11-19 freigegeben.
> Kombiniertes Dokument: Teil A = Spec, Teil B = Plan. Plan erst nach `Status: APPROVED` ausführbar.

# Teil A — Spec

## Problem / Ziel / Nicht-Ziele

**Problem:** Das `git`-Agent-Template verlangt den Rollen-Sentinel `#agent-meta:agent=git` als erste Zeile **jedes** Bash-Aufrufs, auch für `gh` (`agents/1-generic/git.md:26-35`, `:163`; weitere Beispielblöcke `:42`, `:98`). In Claude Code ist ein Newline ein Kommando-Trenner; jedes Teilkommando muss eine Allow-Regel treffen (CC-Doku „Compound commands"). Die reine Kommentarzeile trifft keine Regel, daher greift `Bash(gh issue *)` (bzw. die Absolutpfad-Variante) nicht; im Auto-Mode geht der Aufruf an den Classifier und wird geblockt. Derselbe Aufruf ohne Sentinel wurde erlaubt.

**Verifizierte Fakten (Repo):**
- Guard liest den Sentinel nur aus der ersten nicht-leeren Zeile: `hooks/1-generic/orchestrator-guard-impl.sh:308-350` (Regex `:333`).
- Sentinel befreit nur das Git-Mutations-Gate (`:1543`) und den Strict-Mode-Block (`:1523`, nur bei leerem `agent_id` `:1513`).
- Auf Providern mit `hook-agent-id` (Claude, `config/ai-providers.yaml:63-69`) wird ein Sentinel am Main-Thread verworfen (`:361-366`).
- `gh` wird nie gegated (`:91-102`, `is_mutation` `:1032`). Probe am gerenderten Hook ohne Sentinel: `gh pr merge`/`gh issue close` (Subagent) → exit 0; `git commit` (Subagent) → exit 2 (Sentinel für git weiter nötig).

**Nicht verifiziert (inferiert):** Dass Claude Code eine Kommentar-only-Zeile als eigenes, nicht matchendes Teilkommando wertet. Die CC-Doku schweigt dazu; die Beobachtung (Block mit Sentinel, erlaubt ohne) stützt es nur. → AC-9 / Task 6 (Live-Check). Bestätigt sich das nicht, wird der Plan revidiert.

**Ziel:** Auf Providern mit Capability `hook-agent-id` verlangt das gerenderte `git`-Agent-Template für **reine `gh`-Aufrufe** keine Sentinel-Zeile (eigener Bash-Call, nicht mit `git` gemischt). `git`-Aufrufe tragen den Sentinel unverändert als erste Zeile. Provider ohne `hook-agent-id` (Strict-Mode-Pfad, z.B. Gemini) behalten den unbedingten Sentinel — Ausgabe byte-identisch.

**Nicht-Ziele:**
- Keine Änderung an Guard/Hook (`hooks/**`) — Convention boundary bleibt unverändert; Sentinel-Format unverändert (daher **kein F7**).
- Keine Änderung der Sentinel-Semantik oder der Allow-Listen/`settings*.json`.
- Kein Syncer-Feature für `permissions.allow` (separates Thema, siehe Analyse).
- Keine Rebaselines ohne ausdrückliche Nutzerfreigabe; kein `python3 scripts/sync.py` (Voll-Sync) ohne Nutzer-OK; keine lokalen Szenario-Läufe (nur CI).
- Kein `if provider == "<Name>"` im Syncer (`provider-agnostic`).

**Verworfene Optionen:**
- Unbedingtes Entfernen des Sentinels für `gh`: bricht Strict-Mode auf Providern ohne `hook-agent-id` (jeder Subagent-Bash-Call ohne Sentinel wird dort geblockt).
- Trailing Same-Line-Kommentar / andere Position: Hook-Änderung, tokenizer-bewusste Kommentarprüfung, Änderung des öffentlichen Sentinel-Formats (F7) → Klasse L.
- Env-Var-Präfix (`AGENT_META_AGENT=git gh …`): Allow-Regeln matchen laut CC-Doku („Wrappers") nicht an einer führenden Variablenzuweisung vorbei.

**Möglicher Folge-Issue (außer Scope):** Dieselbe Blockade trifft sehr wahrscheinlich auch Allow-Regeln für `git`-Kommandos (Sentinel-Zeile bleibt dort Pflicht). Lösung dort bräuchte Hook-/Formatänderung (z.B. Payload-Attribution, #1210-Spec §3).

## Interface Contracts

**Mechanismus (Korrektur zur Issue-Formulierung):** `PARSE_INPUT_BLOCK` ist ein statischer Snippet-Block (`scripts/lib/config.py:3296`, Registrierung `scripts/lib/consistency/placeholders.py:158`), **nicht** capability-gesteuert. Capability-gesteuerte Template-Werte entstehen pro Provider in `scripts/lib/agent_sync.py:_build_provider_vars` (`:488-607`, `provider_vars`-Dict; Muster `PROGRESS_CHAT_PUSH_ENABLED` `:527`, `provider_has_capability(pc, "hook-agent-id")` wie `scripts/lib/hooks.py:562`). Der neue Wert wird dort erzeugt; Registrierung in `placeholders.py` analog den provider-injizierten Namen (nahe `:158`/`INTENT_ROUTING_TOOLS`).

**Neue Platzhalter (je ein Provider-Variablen-String, kein Block-Snippet):**

1. `{{GIT_SENTINEL_SCOPE_BLOCK}}` — inline am Ende des Absatzes `git.md:35` (hinter „…must not forbid it to the git agent.", **ohne** eigene Zeile, damit der leere Fall byte-identisch bleibt).
   - Capability `hook-agent-id` **fehlt** → `""` (Template rendert byte-identisch zu heute).
   - Capability `hook-agent-id` **vorhanden** → exakt (führendes Leerzeichen gehört zum Wert):
     ` Exception: for Bash calls that run only \`gh\` (no \`git\` in the call), do NOT add the sentinel line — it is not needed for \`gh\`, and the extra line makes allow rules such as \`Bash(gh issue *)\` not match. Run such \`gh\` calls as their own Bash call; never mix \`gh\` and \`git\` in one call. Every call that runs \`git\` keeps the sentinel as its first line.`
2. `{{GIT_SENTINEL_BASH_RULE}}` — inline in `git.md:163` (`<tools>`).
   - fehlt → `always prefixed with \`#agent-meta:agent=git\` as the first line (see workflow step 0)` (= heutiger Text, byte-identisch).
   - vorhanden → `\`git\` calls always prefixed with \`#agent-meta:agent=git\` as the first line, \`gh\`-only calls without it (see workflow step 0)`.

**Template-Zeile `git.md:163` nach Änderung:** `- **Bash** — all git/gh commands, {{GIT_SENTINEL_BASH_RULE}}`.
**Unverändert in git.md:** Überschrift `:26` und Beispiel-Blöcke `:31`, `:42`, `:98` (alle `git`-Aufrufe; Sentinel bleibt korrekt).

**Provider-Variablen-Erzeugung:** Pure Funktion (z.B. `scripts/lib/agent_sync.py:_git_sentinel_scope_vars(pc) -> dict`) liefert beide Werte aus `provider_has_capability(pc, "hook-agent-id")`; Texte als Modul-Konstanten. `_build_provider_vars` mergt das Dict in `provider_vars`. Keine Provider-Namen im Code.

**Konsistenz:** `placeholders.py` kennt beide Namen; `python3 scripts/sync.py --validate` meldet keinen unbekannten/ungenutzten Platzhalter.

## Acceptance Criteria

1. AC-1: Gerendertes Claude-`git.md` (Capability `hook-agent-id`) enthält den Ausnahme-Satz (kein Sentinel für `gh`-only-Calls) und in `<tools>` die Fassung „`git` calls always prefixed … `gh`-only calls without it"; Beispielblöcke mit `git` tragen weiter `#agent-meta:agent=git` als erste Zeile.
2. AC-2: Gerendertes `git.md` für Provider ohne `hook-agent-id` ist **byte-identisch** zu vor der Änderung (Test vergleicht gegen die gespeicherte Vorher-Fassung/ac01-Hash; der Hash wandert nicht).
3. AC-3: `tests/test_git_template_sentinel_doc.py` bleibt grün; die drei exakten Strings (`"The sentinel only declares the role; it bypasses no protection"`, `"blocks git mutations independent of strict mode"`, `"only the narrow auto-commit allowlist (add/commit, declared via its own sentinel) is exempt"`) und die Negativ-Asserts (`"no provider forwards"`, `"always blocks them"` nicht enthalten) bleiben erfüllt. Eine neue Assertion prüft den gh-Ausnahme-Satz im **gerenderten** Claude-Output (Template-Quelltext enthält nur den Platzhalter).
4. AC-4: Guard-Verhalten unverändert: `git diff main -- hooks/` ist leer; `tests/test_orchestrator_guard_hook.py` unverändert und grün (inkl. `:155-161`, `:213ff`, `:444-676`); kein Hook-Hash-Rebaseline.
5. AC-5: `a2a-delegation-gates.md:117` und weitere Regel-/Template-Texte widersprechen der neuen Aussage nicht (Prüfung Task 5); wird eine Regeldatei geändert, wandert sie in die Pin-Liste.
6. AC-6: Kein `if provider ==` im Diff (`tests/test_provider_agnostic_dispatch.py` grün).
7. AC-7: `python3 scripts/sync.py --validate` und `--check` grün (nach Pin-Pass, s. R-1).
8. AC-8: Alle Platzhalter in `git.md` sind registriert; Konsistenz-Check ohne neue Findings.
9. AC-9 (manuell, Nutzer/CI-fern): Auf echtem Claude-Code-Lauf mit `Bash(gh issue *)` in den Allow-Regeln führt der `git`-Agent `gh issue comment` ohne Sentinel ohne Prompt und ohne Classifier-Block aus. Schlägt das fehl → Plan überprüfen (Inferenz widerlegt).
10. AC-10: Rebaselines nur mit ausdrücklicher Nutzerfreigabe (Task 4).

## Pin-Liste (potenziell betroffen — Rebaseline nur nach Nutzer-OK)

- **Erwartet:** `tests/fixtures/ac01-baseline/hashes.json:38` (gerendertes Claude-`git.md`) — ändert sich zwangsläufig; nur dieser Eintrag darf wandern. Alle anderen Provider-Einträge müssen unverändert bleiben (AC-2).
- **Möglich:** Compact-/Golden-Digests (`tests/test_gate_card_compact*`, `tests/test_template_slimming_equivalence*`), falls deren Fixtures das gerenderte Claude-`git.md` abdecken.
- **Möglich:** AC-T4-Digest in `tests/test_opencode_v2_surface.py` (nur falls `git.md` für Opencode betroffen — Opencode hat laut Annahme kein `hook-agent-id`; Annahme in Task 4 verifizieren).
- **Unerwartet:** jeder andere brechende Pin → STOP, Nutzer fragen, kein Selbst-Rebaseline.

## Offene Fragen + Risiken

- **R-1 Pins:** siehe Pin-Liste; ein einziger Pin-Pass am Ende (Task 4) statt Rebaseline pro Task.
- **R-2 Inferenz nicht live getestet:** Kommentar-only-Zeile als eigenes Teilkommando. Mitigation AC-9/Task 6; fällt sie durch, ist die Template-Änderung wirkungslos und der Plan muss revidiert werden.
- **R-3 Gemischte Aufrufe:** Agent könnte `gh` und `git` in einem Call mischen; dann gilt Sentinel-Pflicht (Ausnahme-Satz verbietet Mischen). Kein Hook-Check — Prompt-Konvention.
- **R-4 Konditionale Text-Variablen:** Inline-Werte mit führendem Leerzeichen sind fragil; Test AC-2 (byte-identisch) fängt Whitespace-Drift.
- **OF-1:** Wortlaut des Ausnahme-Satzes (Vorschlag oben, Englisch wie Template). Default: wie vorgeschlagen.
- **OF-2:** Soll auch `a2a-delegation-gates.md:117` angepasst werden, falls es „Sentinel auf jedem Bash-Call" behauptet? Default: nur bei echtem Widerspruch, dann mit eigener Pin-Prüfung.
- **OF-3:** Folge-Issue für git-Allow-Regeln (siehe oben) anlegen? Default: ja, separat, nicht in diesem PR.
- **OF-4:** Capability-Wahl `hook-agent-id` vs. neue dedizierte Capability. Default: `hook-agent-id` (genau die Bedingung, unter der Guard den Sentinel am Main-Thread verwirft).

Klassifikation: M (4–6 Dateien, ein Subsystem, Sentinel-Format/öffentliche API unverändert → kein F7).

## Trace-Anker

spec-id: SPEC-SENTINEL-GH-ALLOW-MATCHING

---

# Teil B — Plan

**Goal:** Reine `gh`-Aufrufe des `git`-Agenten tragen auf `hook-agent-id`-Providern keine Sentinel-Zeile mehr, damit User-Allow-Regeln matchen; `git`-Aufrufe und alle anderen Provider bleiben unverändert.

**Architecture:** Zwei provider-injizierte Text-Variablen (`GIT_SENTINEL_SCOPE_BLOCK`, `GIT_SENTINEL_BASH_RULE`) aus `_build_provider_vars` (Capability `hook-agent-id`); Template `git.md` nutzt sie inline; Guard-Hook unverändert.

**Tech Stack:** Python 3.9 (nur Stdlib), pytest, Markdown-Templates.

**Spec:** docs/plans/2026-11-19-sentinel-gh-allow-matching.md (Teil A, `spec-id: SPEC-SENTINEL-GH-ALLOW-MATCHING`, Status: DRAFT — Ausführung erst nach `Status: APPROVED` durch den Nutzer)

**Estimated effort:** laut `effort-estimator` (Textreferenz, keine eigene Schätzung) — Klasse M, kleiner Umfang.

## Global Constraints

- Nur Stdlib; Python-3.9-kompatibel.
- Provider-Unterschiede nur über Capability-Flags, nie `if provider == "Name"`.
- Guard/Hook (`hooks/**`) wird nicht angefasst.
- Keine Golden-/Pin-/Hash-Rebaselines ohne ausdrückliche Nutzerfreigabe; bricht ein weiterer Pin: STOP und Nutzer fragen.
- Kein `python3 scripts/sync.py` (Voll-Sync) ohne Nutzer-OK; lokale Gates nur `python3 scripts/sync.py --validate`, `--check`, betroffene pytest. Keine Szenario-Läufe (nur CI).
- Kein `print()` in `scripts/lib/`.
- Branch `fix/sentinel-gh-allow-matching`; Push/Tag/Branch nur durch Rolle `git`; Commit-Betreff Englisch, Imperativ, ≤ 72 Zeichen.
- Tasks 1 und 2 sind ownership-disjunkt; Task 2 braucht aber die Registrierung aus Task 1 → sequentiell (1 → 2). Task 5 kann parallel zu 3 laufen (disjunkt).

## File Structure

- Modify: `scripts/lib/agent_sync.py` — `_git_sentinel_scope_vars`, Merge in `_build_provider_vars`
- Modify: `scripts/lib/consistency/placeholders.py` — zwei Namen registrieren
- Create: `tests/test_git_sentinel_gh_scope.py` — Rendering je Capability, Byte-Identität, Guard unverändert
- Modify: `agents/1-generic/git.md` — zwei Platzhalter (`:35` Ende, `:163`)
- Modify: `tests/test_git_template_sentinel_doc.py` — eine neue Assertion (gerenderter Claude-Output)
- Modify (nur nach Nutzer-OK): `tests/fixtures/ac01-baseline/hashes.json` und ggf. weitere Pins (Task 4)
- Modify: `CHANGELOG.md` — Eintrag

## Tasks

### Task 1: Provider-Variablen und Registrierung
**Agent:** developer
**Depends on:** keine
**Files:**
- Modify: `scripts/lib/agent_sync.py`
- Modify: `scripts/lib/consistency/placeholders.py`
- Create: `tests/test_git_sentinel_gh_scope.py`

**Interfaces:** Produces: `provider_vars["GIT_SENTINEL_SCOPE_BLOCK"]`, `provider_vars["GIT_SENTINEL_BASH_RULE"]`; Consumes: `provider_has_capability(pc, "hook-agent-id")`.
- [ ] Step 1: Tests schreiben (fail): Wert je Capability (vorhanden/fehlend) exakt wie in den Interface Contracts; fehlend → `""` bzw. heutiger Satz
- [ ] Step 2: `_git_sentinel_scope_vars(pc)` implementieren, in `_build_provider_vars` mergen; beide Namen in `placeholders.py` registrieren; prüfen, wie `{{VAR}}`-Substitution mit Backticks/Leerzeichen am Wertanfang umgeht
- [ ] Step 3: `python3 -m pytest tests/test_git_sentinel_gh_scope.py` grün
- [ ] Step 4: Commit-Vorschlag `feat: add git sentinel scope provider variables`

**Akzeptanz:** Tests grün; `git diff` enthält kein `provider ==`; Wert fehlend == `""`/Altsatz exakt.

### Task 2: Template-Änderung git.md
**Agent:** developer
**Depends on:** 1
**Files:**
- Modify: `agents/1-generic/git.md`
- Modify: `tests/test_git_template_sentinel_doc.py`
- Modify: `tests/test_git_sentinel_gh_scope.py` (nur Render-Tests; Ownership: Task 1 hat Datei angelegt, Task 2 ergänzt nach Abschluss von 1)

**Interfaces:** Consumes: beide Platzhalter aus Task 1.
- [ ] Step 1: Tests schreiben (fail): AC-1 (Claude-Render enthält Ausnahme + `git`-Beispiele mit Sentinel), AC-2 (Render ohne `hook-agent-id` byte-identisch zum Vorher-Stand), neue Assertion in `test_git_template_sentinel_doc.py` auf gerenderten Claude-Output
- [ ] Step 2: `git.md`: `{{GIT_SENTINEL_SCOPE_BLOCK}}` ans Ende des Absatzes `:35` (selbe Zeile, ohne Zusatz-Leerzeile) und `{{GIT_SENTINEL_BASH_RULE}}` in `:163`; die drei exakten Strings unverändert lassen
- [ ] Step 3: `python3 -m pytest tests/test_git_template_sentinel_doc.py tests/test_git_sentinel_gh_scope.py` grün
- [ ] Step 4: Commit-Vorschlag `fix: skip sentinel for gh-only calls on hook-agent-id providers`

**Akzeptanz:** AC-1, AC-2, AC-3 grün; Template-Diff ≤ 2 Zeilen.

### Task 3: Guard-unverändert-Nachweis
**Agent:** tester
**Depends on:** 2
**Files:**
- Create: (keine) — nur Läufe; Ergebnis im Bericht
- Modify: `tests/test_git_sentinel_gh_scope.py` — Test „Guard-Hook-Datei unverändert" (Hash-Vergleich gegen `main` über `git`-freien Dateivergleich ist nicht möglich; stattdessen vorhandene Hook-Hash-/Guard-Tests laufen lassen)

**Interfaces:** Consumes: bestehende Guard-Tests.
- [ ] Step 1: `python3 -m pytest tests/test_orchestrator_guard_hook.py` und `tests/test_provider_agnostic_dispatch.py` ausführen
- [ ] Step 2: Bericht: grün/rot; `hooks/` im Diff-Stat der Task-Commits leer (Aussage des Callers über `git diff --stat`, Tester führt kein git)
- [ ] Step 3: Commit-Vorschlag nur falls Testdatei ergänzt: `test: pin guard behaviour unchanged for sentinel scope`

**Akzeptanz:** AC-4, AC-6 grün; keine Änderung unter `hooks/`.

### Task 4: Einziger Pin-Pass (STOP-and-ask)
**Agent:** tester
**Depends on:** 2, 3, 5
**Files:**
- Modify (nur nach ausdrücklichem Nutzer-OK): `tests/fixtures/ac01-baseline/hashes.json` (nur Eintrag `:38`, Claude-`git.md`)
- Modify (nur nach Nutzer-OK, falls betroffen): Compact-/Golden-Digests, AC-T4-Digest in `tests/test_opencode_v2_surface.py`

**Interfaces:** Consumes: gesamte Pin-Liste der Spec.
- [ ] Step 1: Betroffene Pin-Tests ohne Änderung laufen lassen (`test_gate_card_compact*`, `test_template_slimming_equivalence*`, ac01-Baseline-Test, `test_opencode_v2_surface.py`); Liste der Brüche erstellen
- [ ] Step 2: STOP — Brüche an Nutzer melden. Erwartet: nur ac01-Eintrag Claude-`git.md`. Jeder andere Bruch (oder ein Bruch eines nicht-Claude-Providers = Verstoß gegen AC-2) → nicht rebaselinen, Ursache klären
- [ ] Step 3: Nach ausdrücklichem OK: nur die genannten Pins neu setzen (vorhandener Rebaseline-Helper, kein Handedit unbekannter Hashes)
- [ ] Step 4: `python3 scripts/sync.py --validate`, `python3 scripts/sync.py --check` und die Pin-Tests grün
- [ ] Step 5: Commit-Vorschlag `test: rebaseline git.md claude pin for sentinel scope (#<issue>)`

**Akzeptanz:** Ohne Nutzer-OK keine Dateiänderung; danach AC-7, AC-10 erfüllt, Diff der Pin-Dateien nur die freigegebenen Einträge.

### Task 5: Doku und Widerspruchsprüfung
**Agent:** documenter
**Depends on:** 2
**Files:**
- Modify: `CHANGELOG.md`
- Prüfen (nur ändern bei echtem Widerspruch, dann Pin-Liste erweitern + Nutzer informieren): `rules/1-generic/a2a-delegation-gates.md:117`

**Interfaces:** Consumes: Spec Teil A.
- [ ] Step 1: `a2a-delegation-gates.md:117` lesen; Widerspruch ja/nein notieren
- [ ] Step 2: CHANGELOG-Eintrag (Englisch): sentinel not required for `gh`-only calls on providers with `hook-agent-id`
- [ ] Step 3: Commit-Vorschlag `docs: changelog for gh-only sentinel scope`

**Akzeptanz:** AC-5; CHANGELOG enthält den Eintrag; keine Regeldatei geändert, außer bei dokumentiertem Widerspruch.

### Task 6: Live-Verifikation (Inferenz-Check)
**Agent:** tester
**Depends on:** 4 (und Nutzer-Sync, s. u.)
**Files:**
- Create: (keine) — nur Beobachtungsbericht

**Interfaces:** Consumes: gerendertes `.claude/agents/<prefix>-git.md` (benötigt Nutzer-OK für Sync).
- [ ] Step 1: Nutzer-OK für Sync einholen (`python3 scripts/sync.py` nur mit OK); gerenderte Claude-`git`-Agent-Datei prüfen (Ausnahme-Satz vorhanden)
- [ ] Step 2: Auf echtem Claude-Code-Lauf (Nutzer führt aus oder bestätigt) `git`-Agent `gh issue comment` ohne Sentinel ausführen lassen; Allow-Regel `Bash(gh issue *)` aktiv
- [ ] Step 3: Ergebnis dokumentieren (erlaubt/geblockt). Geblockt → Plan revidieren (Inferenz widerlegt), kein Weitermachen mit Merge

**Akzeptanz:** AC-9 erfüllt oder Revisions-Entscheidung des Nutzers.

## Self-Review

- Jeder Task mappt auf genau eine Rolle (developer, tester, documenter); Akzeptanzkriterien messbar (Testname/Diff-Bedingung/Hash-Eintrag).
- `Files:`/`Interfaces:` vollständig; Dateiüberlappung nur sequentiell (`tests/test_git_sentinel_gh_scope.py` Tasks 1 → 2 → 3), keine parallelen Überlappungen (Task 3 ∥ 5 disjunkt).
- `pipeline_stages` deckt die `implement`-Stage (Schritt 1).
- Ein einziger Pin-Pass (Task 4) mit STOP-and-ask; Guard/Hook unverändert.
- Offene Prüfpunkte: `{{#if}}`-/Substitutionsdetails und Leerzeichen-Verhalten werden in Task 1 verifiziert (Grep war beim Erstellen nicht verfügbar).

**Re-planning:** Nach Task 4 (Pin-Ergebnis) und Task 6 (Live-Check) Annahmen neu prüfen: Capability-Wahl, Wortlaut, Inferenz zum Kommentar-Trenner; Plan aktualisieren statt einfrieren.
