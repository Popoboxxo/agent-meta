---
spec-id: SPEC-GUARD-ROLE-ATTRIBUTION-2026-11-11
title: Rollenbindung im Orchestrator-Guard über ein Payload-Feld (Sentinel-Fälschbarkeit)
status: DRAFT
issue: "#1210"
plan: docs/superpowers/plans/2026-11-11-phase-d-guards-hooks.md (Task 0)
datum: 2026-11-13
autor: concept-specifier (Subagent, Auftrag via orchestrator)
related-spec: SPEC-COMMIT-AUTHORITY-GRANT-2026-11-09 (§3.3.1 Punkt 3, D18)
---

# Rollenbindung im Orchestrator-Guard über ein Payload-Feld — Spec

> **Status: DRAFT — Entwurf, Freigabe durch Nutzer ausstehend.** Nicht `APPROVED`. Kein Reviewer-Lauf,
> keine Nutzerfreigabe. Offene Entscheidungen stehen in §10 und werden hier **nicht** entschieden.
> Diese Datei enthält Contracts und Akzeptanzkriterien, keine Implementierung.
> Trace-Anker: `spec-id: SPEC-GUARD-ROLE-ATTRIBUTION-2026-11-11`.
>
> **Issue:** #1210 — das Guard-Sentinel (`#agent-meta:agent=<role>`) ist von jedem Subagenten mit Bash
> fälschbar; gewünscht ist Rollenbindung über ein Payload-Feld. Optionen laut Issue (vom Aufrufer
> zusammengefasst, Issue-Text nicht eingesehen): (1) Payload-Feld, (2) Secret, (3) als Convention
> boundary dokumentieren.
> **Klasse:** L (Security-Spec, Guard-Contract). **Messstand:** Worktree `wt-phase-d1`, 2026-11-13; alle
> Zeilenanker unten wurden an diesem Stand nachgemessen und stimmen mit den Ankern des Plans
> (`9aa0e0c0`) überein.

## 1. Problem / Ziel / Nicht-Ziele

### 1.1 Problem

Der Guard (`hooks/1-generic/orchestrator-guard-impl.sh`) kennt die **Rolle** eines Bash-Aufrufs nur aus
einer selbst deklarierten Kommentarzeile (Sentinel). Das Harness-Payload liefert im Repo nur das opake
`agent_id`:

- `agent_id` wird gelesen: `orchestrator-guard-impl.sh:269` (`AGENT_ID=$(hook_json_get "$INPUT" "agent_id")`).
- Sentinel-Parse: `:326-350` (Regex `^#agent-meta:agent=([A-Za-z0-9_-]+)(?:\s+id=...)?$` auf der ersten
  nicht-leeren Zeile, `:333`).
- Sentinel-Zuordnung: `:418-481` (`git` -> `IS_GIT_SENTINEL`, `orchestrator` -> `IS_ORCH_SENTINEL`, sonst
  Allowlist `.meta-config/auto-commit-allowlist.json` -> `IS_ALLOWLIST_SENTINEL`).
- Mutations-Gate: `:1527-1547`, Bedingung `:1535`; Reject-Text `:1537`.
- Bestehende Teil-Bindung: auf Providern mit `hook-agent-id` wird ein Sentinel ohne `agent_id` verworfen
  (`:352-366`, Flag `HOOK_AGENT_ID_RELIABLE`, gebacken aus `hook-agent-id`,
  `config/ai-providers.yaml:64`). Das unterscheidet Main-Thread von Subagent, **nicht** Rolle von Rolle.

Folge: Jeder Subagent mit Bash kann sich per erster Zeile `#agent-meta:agent=git` die `git`-Rolle geben
(Fälschung, Hook-Kommentar `:73-75` dokumentiert einen realen Vorfall, #516). Der Hook-Kommentar nennt das
selbst „soft, self-reported convention … not a security boundary" (`:67-71`).

### 1.2 Ziel

Eine vom Harness gesetzte Rollenangabe im Payload (Feld-Name **offen**, Doku nennt `agent_type`) nutzen,
um die Sentinel-Rolle gegenzuprüfen bzw. zu ersetzen, **sofern** das Feld belegt vertrauenswürdig ist.
Providerunterschiede über ein Capability-Flag ausdrücken, nie über Providernamen.

### 1.3 Nicht-Ziele

- Kein Secret-/Token-Verfahren (Option 2 des Issues entfällt laut Plan Task 0, Zeile 121).
- Keine Änderung des Destructive-Gates (`:1383`, gilt unabhängig vom Sentinel) und des Strict-Mode-Pfads
  für den Main-Chat (`:1505-1524`) über die in §3 genannten Punkte hinaus.
- Keine Neufassung des Commit-Authority-Grants (#1181); diese Spec ändert dessen Allowlist-Vertrag nicht.
- Kein Klassifizierer-/Auto-Mode-Eingriff (der Claude-Code-Auto-Mode-Classifier liegt außerhalb des Repos).
- Keine Implementierung (Plan Task 8 nach Freigabe).

## 2. Evidenz

### 2.1 Was belegt ist

| Aussage | Beleg |
|---|---|
| Repo liest nur `agent_id`, kein Rollenfeld | `orchestrator-guard-impl.sh:269`; `agent_type` kommt in der Datei nicht vor (Grep 2026-11-13: keine Treffer für `agent_type`; Grep-Muster in dieser Session `agent_id\|sentinel\|agent=git\|AGENT_ID`) |
| Claude-Code-Doku nennt `agent_id` und `agent_type` als gemeinsame Payload-Felder | `docs/analysis/2026-11-11-hook-api-ask-permission.md` §3.5 (Extraktion eines Recherche-Agenten per WebFetch, Abruf 2026-11-13, **kein Rohtext**); Wortlaut dort: `agent_type` = „Agent name (for example, "Explore" or "security-reviewer"). Present when the session uses --agent or the hook fires inside a subagent." |
| `agent_id` ist laut Hook-Kommentar harness-gesetzt | `orchestrator-guard-impl.sh:51-59`, `:262-268` (zitiert Doku; nicht in dieser Session gegen die Seite geprüft) |
| Capability `hook-agent-id` existiert, wird in den Hook gebacken | `config/ai-providers.yaml:59-64`; Platzhalter `{{AGENT_META_HOOK_AGENT_ID}}` `orchestrator-guard-impl.sh:360` |
| Das `git`-Agent-Template erzeugt die Sentinel-Zeile selbst | `agents/1-generic/git.md:31`, `:42`, `:98` (Beispiele), Pflichtformulierung `:159` („always prefixed with `#agent-meta:agent=git` as the first line") |
| Das Template begründet das Sentinel mit „no provider forwards that in the PreToolUse payload" | `agents/1-generic/git.md:28` — steht im Widerspruch zu `hook-agent-id` (`config/ai-providers.yaml:59-64`) und `orchestrator-guard-impl.sh:51-59`; betrifft nur `agent_id`, nicht Rolle. Doku-Fix s. AC-12 |

### 2.2 Reale Reibung (belegt in dieser Session)

(a) Der Orchestrator-Guard blockt den `git`-Agenten ohne `git`-Sentinel bei jeder Mutation:

```
ORCHESTRATOR_GUARD: Direct git mutations are forbidden for this subagent (no `git` sentinel, or outside its auto-commit scope).
```

Beobachtet am 2026-11-13 bei einem Developer-Subagenten, der `git apply -R --check` ausführte (der Guard
behandelte den Aufruf als Mutation). Quelle der Meldung: `orchestrator-guard-impl.sh:1537`.

(b) Ein Sentinel im Kommando wird vom Claude-Code-Auto-Mode-Classifier als Umgehung abgelehnt:

```
Permission for this action was denied by the Claude Code auto mode classifier. Reason: [Undermining Oversight].
```

Beobachtet am 2026-11-13: Der `git`-Agent des Orchestrators führte `git -C .../wt-phase-d1 add -- <file>`
aus, mit vorangestellter Sentinel-Zeile `#agent-meta:agent=git`, und wurde abgelehnt. Die Sentinel-Zeile
wird vom `git`-Agent-Template selbst erzeugt (`agents/1-generic/git.md:31`, `:42`, `:98`, Pflicht `:159`).

**Konsequenz:** Der legitime `git`-Agent-Pfad und der Fälschungs-Pfad sehen für den Classifier gleich aus
(beide: Bash-Kommando mit Sentinel-Zeile). Ein Rollenfeld im Payload würde dem Guard erlauben, den
`git`-Agenten ohne kommandoeingebettetes Sentinel zu identifizieren.

**Ausdrücklich nicht verifiziert:** Ob die Ablehnung des Classifiers vom Sentinel-Text abhängt. Der
Ablehnungsgrund ist generisch (`[Undermining Oversight]`). Es ist ungeklärt, ob das Entfernen des
Sentinels die Ablehnung beendet.

## 3. Interface Contracts

Alle Contracts sind **bedingt**: sie greifen nur, wenn die Evidenzfrage aus §5 (Feld vertrauenswürdig)
positiv entschieden ist. Bei negativer Evidenz gilt §8 (D-neu-4).

### 3.1 Payload-Feld

| Aspekt | Festlegung |
|---|---|
| Name | **offen** (OQ-1); Kandidat laut Doku-Extraktion: `agent_type` |
| Quelle | Harness-Payload (PreToolUse), Top-Level, neben `agent_id` |
| Lesezugriff | `hook_json_get "$INPUT" "<feld>"` direkt neben `orchestrator-guard-impl.sh:269`; Ergebnis in Variable (Name offen, hier `ROLE_FIELD`) |
| Normalisierung | Kleinschreibung wie beim Sentinel (`orchestrator-guard-impl.sh:424`, `tr '[:upper:]' '[:lower:]'`) |
| Leerer Wert | `ROLE_FIELD=""` = nicht vorhanden; Main-Thread-Aufrufe tragen laut Doku-Extraktion kein Feld (gilt nur „when the session uses --agent or the hook fires inside a subagent") |

### 3.2 Capability-Flag

- Neuer Eintrag in `config/ai-providers.yaml` (Neben-Eintrag zu `hook-agent-id`, `:64`); Name **offen**
  (OQ-1), Arbeitsname `hook-role-field`.
- Wird beim Sync in den Hook gebacken, analog `HOOK_AGENT_ID_RELIABLE="{{AGENT_META_HOOK_AGENT_ID}}"`
  (`orchestrator-guard-impl.sh:360`): Platzhalter, Werte `"true"` / sonstiges. Ungesyncte Quellkopie
  (Platzhalter literal) verhält sich wie `false`.
- Keine Verzweigung nach Providername in `scripts/lib/` oder im Hook (`provider-agnostic`).
- Der konkrete Ort der Backing-Logik (Sync-Seite, `scripts/lib/hooks.py`) wird vom Plan (Task 8)
  gemessen; hier nicht verifiziert.

### 3.3 Entscheidungslogik (Soll)

Gegeben `DECLARED_AGENT` (Sentinel-Rolle, `:347`), `ROLE_FIELD` (§3.1), `AGENT_ID` (`:269`), Flag
`HOOK_ROLE_FIELD_RELIABLE`:

| # | Flag | `AGENT_ID` | `ROLE_FIELD` | Sentinel | Ergebnis |
|---|---|---|---|---|---|
| R1 | true | nicht leer | nicht leer | keiner | Rolle = `ROLE_FIELD` (Zuordnung wie `:426-480`); Verhalten bei `git` siehe OQ-3 |
| R2 | true | nicht leer | nicht leer | gleich `ROLE_FIELD` | Rolle = diese; unverändert |
| R3 | true | nicht leer | nicht leer | **ungleich** `ROLE_FIELD` | **Reject** (rc 2), Meldung §4 (Verhalten bei Mismatch: OQ-4) |
| R4 | true | nicht leer | leer | beliebig | Fallback: Sentinel wie heute (Convention boundary); alternativ Reject (OQ-5) |
| R5 | true | leer | beliebig | beliebig | Main-Thread; bestehender Pfad (`:362-366` verwirft Sentinel, `:1505` Strict-Mode) unverändert |
| R6 | false/Platzhalter | beliebig | beliebig | beliebig | Feld wird nicht gelesen; Sentinel wie heute; ausdrücklich Convention boundary (§7) |

### 3.4 Betroffene Stellen (Ziel-Symbole für Task 8)

| Datei | Stelle | Änderung |
|---|---|---|
| `hooks/1-generic/orchestrator-guard-impl.sh` | neben `:269` | Feld lesen |
| `hooks/1-generic/orchestrator-guard-impl.sh` | nach `:366` | Abgleich Feld vs. Sentinel (R1-R4) |
| `hooks/1-generic/orchestrator-guard-impl.sh` | `:418-481` | Rollenquelle = Feld oder Sentinel |
| `hooks/1-generic/orchestrator-guard-impl.sh` | `:1535-1546` | Reject-Text ergänzen (§4); Bedingung unverändert |
| `config/ai-providers.yaml` | neben `:64` | neues Capability-Flag |
| `agents/1-generic/git.md` | `:28-35` | Aussage „no provider forwards that" korrigieren; Sentinel-Pflicht je Entscheidung OQ-2 |
| `tests/test_orchestrator_guard_hook.py`, `tests/test_hook_drift.py` | — | Testmatrix §6 |
| `rules/1-generic/branch-guard.md`, `rules/1-generic/a2a-delegation-gates.md` | — | Doku (Plan Zeile 72) |

## 4. Fail-Verhalten / Reject-Meldung

- Fail-closed: kein Pfad schwächt bestehende Blocks (`:1535`, Destructive-Gate `:1383`).
- Meldung bei R3 (Wortlaut Vorschlag, auf Stderr, rc 2, wie alle blockierenden Pfade `:48-49`):

```
ORCHESTRATOR_GUARD: role mismatch — payload role field "<feld>" != sentinel role "<sentinel>". The sentinel cannot override the harness-provided role.
```

- Der bestehende Reject-Text `:1537` bleibt für nicht-`git`-Rollen erhalten (AC-3 aus #1210 laut Plan:
  `git`-Sentinel-Pfad unverändert).
- Audit-Log: bei jedem Feld-Mismatch und jedem Rollen-Entscheid über das Feld Eintrag in
  `.claude/hooks/.guard-audit.log` (Funktion `hook_audit_log_append`, `hooks/1-generic/lib/hook_common.sh`;
  Redaktion wie bisher). Aufruf-Stelle `:482ff`.

## 5. Fälschbarkeit / Threat-Model

**Angreifer:** Subagent mit Bash (legitim gespawnt, z. B. durch Prompt-Injection gesteuert).

**Heute (belegt):** Der Angreifer schreibt `#agent-meta:agent=git` als erste Kommandozeile; der Guard
vergibt `IS_GIT_SENTINEL=1` (`:427`) und lässt Nicht-Destructive-Mutationen durch (`:1535`). Es gibt keine
Gegenprüfung. Eine Ausnahme: der Allowlist-Pfad (`:429-480`) prüft die Rolle gegen
`auto-commit-allowlist.json`, aber der Sentinel-Wert selbst bleibt selbstdeklariert.

**Mit Payload-Feld (Hypothese):** Ist das Feld harness-gesetzt aus dem gewählten Agenten-Typ des Spawns, kann
Kommandotext es nicht ändern. Offene Angriffsflächen, **nicht verifiziert**:

1. Kann der Subagent selbst per Agent-Tool einen Subagenten mit `subagent_type: git` spawnen und so ein
   legitimes Feld `git` erzeugen? (Der Guard blockt nur das Spawnen von `orchestrator`, `:274-285`.) Dann
   wäre das Feld eine Rollen-Attribution, aber keine Berechtigungsprüfung.
2. Ist das Feld immer gefüllt (analysis §3.5: „Ob `agent_type` immer gefüllt ist: nicht verifiziert")?
3. Wer bestimmt den Wert bei Custom-Agenten-Definitionen (`.claude/agents/*.md`) — Dateiname, `name:`
   im Frontmatter? Ein Projekt-Agent mit `name: git` ist nicht ausgeschlossen.
4. Gilt das Feld auch für Aufrufe, die ein Subagent über in-process Teammates auslöst
   (`agent_id` kennt „subagent or in-process teammate", analysis §3.5)?

**Einstufung:** Selbst mit belegtem Feld bleibt der Guard Tokenizer-basiert; Indirektion (`eval`, `$(...)`)
umgeht ihn unabhängig von der Rolle (`rules/1-generic/branch-guard.md`, Abschnitt „Bekannte Grenzen",
gemessen als `.claude/rules/branch-guard.md`). Die Rollenbindung verbessert die **Attribution**, macht den
Guard aber nicht zur Security boundary (Terminologie: Convention boundary = fail-closed gegen akzidentellen
Missbrauch; Security boundary = auch gegen deliberate Umgehung; `.claude/rules/branch-guard.md`). Ob und
wie die Einstufung der Orchestrator-Guard-Datei geändert wird, ist OQ-7.

## 6. Datenfluss

```
PreToolUse-Payload (JSON)
  -> hook_json_get agent_id            (:269)  -> AGENT_ID
  -> hook_json_get <Rollenfeld>        (neu)   -> ROLE_FIELD      [nur wenn Flag true]
  -> Sentinel-Parse (:326-350)                 -> DECLARED_AGENT
  -> Main-Thread-Discard (:362-366)
  -> Abgleich ROLE_FIELD vs DECLARED_AGENT (neu, R1-R4)
  -> Rollen-Zuordnung (:418-481) -> IS_GIT / IS_ORCH / IS_ALLOWLIST_SENTINEL
  -> Audit-Log (.claude/hooks/.guard-audit.log)
  -> Destructive-Gate (:1383, unabhängig von Rolle)
  -> Strict-Mode (:1505) -> Mutations-Gate (:1535) -> exit 0 | exit 2 (Stderr)
```

Persistenz: nur Audit-Log (Append). Das Flag entsteht beim Sync (`config/ai-providers.yaml` -> Hook-Quelle
per Platzhalter -> `.claude/hooks/…`).

## 7. Fallback ohne Feld (Convention boundary, ausdrücklich)

Für Provider ohne belegtes Rollenfeld (Flag nicht gesetzt) bleibt das Sentinel das **einzige**
Rollensignal. Dieser Pfad ist **Convention boundary, keine Security boundary**: Er schützt gegen
akzidentellen Missbrauch (Tippfehler, naive Automatisierung), nicht gegen einen Subagenten, der das
Sentinel absichtlich schreibt. Das gilt ausdrücklich auch auf Providern, die das Feld liefern, solange
das Flag nicht gesetzt ist. Die Doku (`rules/1-generic/branch-guard.md`, `a2a-delegation-gates.md`) muss das
aussprechen. Der Hook-Kommentar `:67-71` stützt diese Aussage bereits.

## 8. D-neu-4-Zweig: negative Evidenz

Wenn die Evidenzsammlung (Plan Task 0 Step 1) zeigt, dass **kein** vertrauenswürdiges Rollenfeld
existiert (Feld fehlt, ist nicht immer gesetzt oder ist durch den Agenten beeinflussbar), gilt:

1. Die Spec dokumentiert das Ergebnis; §3.3 R1-R4 entfallen, Flag und Hook-Änderung werden nicht gebaut.
2. Option 3 des Issues wird umgesetzt (Entscheidung 34 / D-neu-4): Der Guard wird ausdrücklich als
   **Convention boundary** dokumentiert (Doku-only: `rules/1-generic/branch-guard.md`,
   `a2a-delegation-gates.md`, `agents/1-generic/git.md:28`-Korrektur). Option 2 (Secret) entfällt.
3. Das Ergebnis ist erst nach Step 1 final und gilt nur bei negativer Evidenz. **Der Nutzer bestätigt
   erneut (Entscheidung 38a)** — diese Spec trifft diese Entscheidung nicht (OQ-8).

**Stand heute:** Die Evidenz ist weder positiv noch negativ entschieden. `agent_type` ist laut
Doku-Extraktion vorhanden (nicht gegen den Rohtext verifiziert); Vollständigkeit und Fälschbarkeit sind
nicht verifiziert (§9). Ohne weitere Prüfung ist daher keiner der beiden Zweige belegt.

## 9. Nicht verifiziert

- Rohtext der Claude-Code-Hook-Doku: Aussagen zu `agent_type` stammen aus einer Fetch-Extraktion
  (analysis, Caveat); die Seite wurde ab Byte-Offset 200000 nicht gelesen.
- Ob `agent_type` für jeden Subagent-Aufruf gefüllt ist (analysis §3.5, §6).
- Ob `agent_type` für Subagenten des Orchestrators, für Custom-Agenten und für den Main-Chat (`--agent`)
  denselben Wert trägt, den das Repo als Rolle erwartet (`git`, `orchestrator`, Allowlist-Rollen).
- Ob der Agent den Wert beeinflussen kann (siehe §5 Punkte 1-4); Fälschbarkeit ist **nicht geprüft**.
- Ob andere Provider (Codex, Gemini, Opencode, …) ein Rollenfeld liefern: keine Repo-Belege; nur
  `hook-agent-id` ist als Capability geführt (`config/ai-providers.yaml:64`).
- Ob die Ablehnung durch den Auto-Mode-Classifier vom Sentinel-Text abhängt (generischer Grund
  `[Undermining Oversight]`); ob ein Rollenfeld die Ablehnung beendet, ist nicht belegt. Der Classifier
  ist nicht Teil des Hooks; ein Hook-Entscheid als Stellhebel ist nicht dokumentiert (analysis §3.6).
- Ort/Mechanik der Capability-Backing-Logik beim Sync (`scripts/lib/hooks.py`) in dieser Session nicht
  nachgemessen.
- `rules/1-generic/branch-guard.md`: Terminologie aus `.claude/rules/branch-guard.md` entnommen, nicht aus
  der 1-generic-Quelle.

## 10. Acceptance Criteria

Voraussetzung: Evidenz positiv (§5/§8) und Spec `APPROVED`. Format Given/When/Then; jedes AC referenziert
Contract (§3/§4).

1. **AC-1 Capability-Flag** (§3.2): Given `config/ai-providers.yaml` mit dem neuen Flag nur für einen
   Provider mit belegtem Feld, When `python3 scripts/sync.py` läuft, Then enthält die gesyncte Hook-Datei
   `HOOK_ROLE_FIELD_RELIABLE="true"` genau dort und `"false"` sonst; ein Test pinnt die Zuordnung
   datengetrieben (kein Providername im Code).
2. **AC-2 Feld lesen** (§3.1): Given Flag true und Payload mit `agent_id` und Rollenfeld, When der Hook
   läuft, Then wird das Feld normalisiert (Kleinschreibung) und für die Rollenentscheidung genutzt; Given
   Flag false, Then wird das Feld nicht gelesen.
3. **AC-3 Mismatch-Reject** (§3.3 R3, §4): Given Flag true, Rollenfeld `developer`, Sentinel
   `#agent-meta:agent=git`, Kommando `git commit -m x`, When der Hook läuft, Then rc 2 und Stderr enthält
   `role mismatch`; kein Mutations-Passieren. (Verhalten bei Mismatch laut OQ-4.)
4. **AC-4 Match unverändert** (R2): Given Rollenfeld `git`, Sentinel `git`, Kommando `git add -- f`,
   When der Hook läuft, Then rc 0, Audit-Eintrag wie heute.
5. **AC-5 Feld ohne Sentinel** (R1): Given Rollenfeld `git`, Kommando `git add -- f` ohne Sentinel,
   When der Hook läuft, Then Ergebnis laut OQ-3 (rc 0 mit Audit-Eintrag oder rc 2); Test deckt die
   freigegebene Variante ab.
6. **AC-6 Fallback bei leerem Feld** (R4): Given Flag true, `agent_id` gesetzt, Rollenfeld leer,
   Sentinel `git`, When der Hook läuft, Then Verhalten laut OQ-5 (Sentinel wie heute oder rc 2).
7. **AC-7 Provider ohne Feld** (R6): Given Flag false, Sentinel `git`, When der Hook läuft, Then
   Verhalten byte-identisch zum Stand vor der Änderung (bestehende Tests in
   `tests/test_orchestrator_guard_hook.py` grün ohne Änderung).
8. **AC-8 Main-Thread unverändert** (R5): Given `agent_id` leer, Sentinel `git`, Flag true, Then wird das
   Sentinel verworfen (`:362-366`) und die Strict-Mode-/Mutations-Meldung unverändert ausgegeben.
9. **AC-9 Destructive-Gate unberührt** (§1.3): Given Rollenfeld `git` und Sentinel `git`, Kommando
   `git reset --hard`, When der Hook läuft, Then rc 2 (Destructive-Gate `:1383`).
10. **AC-10 Audit** (§4): Given ein Feld-Mismatch (AC-3), Then enthält `.claude/hooks/.guard-audit.log` eine
    Zeile mit Feldwert, Sentinel-Rolle und Ergebnis `rejected`; Redaktion greift (kein Command-Klartext
    mit Credentials).
11. **AC-11 Reject-Meldung für Subagent ohne Rolle** (§4): Given Flag true, Rollenfeld `developer`,
    Kommando `git add -- f` ohne Sentinel, Then rc 2 mit bestehendem Text `:1537`.
12. **AC-12 Doku** (§7): Given die Spec ist freigegeben, When Doku-Änderungen gemerged sind, Then nennen
    `rules/1-generic/branch-guard.md` und `a2a-delegation-gates.md` das Sentinel-Fallback als Convention
    boundary und `agents/1-generic/git.md:28` enthält nicht mehr die Aussage „no provider forwards that in
    the PreToolUse payload" (oder qualifiziert sie auf die Rolle).
13. **AC-13 Provider-Agnostik**: Given der Diff der Implementierung, When nach `provider ==` bzw.
    Providernamen im Hook-/Sync-Code gesucht wird, Then kein neuer Treffer.
14. **AC-14 Validierung**: `python3 scripts/sync.py --validate` Exit 0; `python3 -m pytest
    tests/test_orchestrator_guard_hook.py tests/test_hook_drift.py` grün.

**D-neu-4-Variante (nur bei negativer Evidenz):** AC-15: Given negative Evidenz und Nutzerbestätigung
(38a), Then enthalten die Doku-Dateien aus §8 die Convention-boundary-Aussage; kein Hook-/Config-Diff.
AC-1 bis AC-11, AC-13 entfallen.

## 11. Testmatrix

Bezug `tests/test_orchestrator_guard_hook.py` (Muster der bestehenden Sentinel-Tests, z. B.
`test_strict_mode_sentinel_exemption` laut `:1512`-Kommentar); jeweils neue Fälle.

| Fall | Flag | agent_id | Rollenfeld | Sentinel | Kommando | Erwartet |
|---|---|---|---|---|---|---|
| T1 | true | a1 | git | git | `git add -- f` | rc 0 |
| T2 | true | a1 | developer | git | `git commit -m x` | rc 2, `role mismatch` (OQ-4) |
| T3 | true | a1 | git | — | `git add -- f` | je OQ-3 |
| T4 | true | a1 | developer | — | `git add -- f` | rc 2, Text `:1537` |
| T5 | true | a1 | (leer) | git | `git add -- f` | je OQ-5 |
| T6 | true | (leer) | git | git | `git add -- f` | Sentinel verworfen, Strict-Pfad |
| T7 | false | a1 | developer | git | `git add -- f` | rc 0 (Fallback, unverändert) |
| T8 | true | a1 | git | git | `git reset --hard` | rc 2 (Destructive) |
| T9 | true | a1 | Git (Großschreibung) | git | `git add -- f` | rc 0 (Normalisierung) |
| T10 | true | a1 | alleinstehende Allowlist-Rolle | gleiche Rolle | `git commit -m x` | rc 0 (narrow) |
| T11 | true | a1 | alleinstehende Allowlist-Rolle | gleiche Rolle | `git push` | rc 2 (broad) |
| T12 | Platzhalter literal | a1 | developer | git | `git add -- f` | wie T7 |
| T13 | true | a1 | git | git (ungültiges `id=`) | `git add -- f` | Sentinel leer -> wie T3 |

Zusätzlich: Drift-Test `tests/test_hook_drift.py` (Hash/Platzhalter), ein datengetriebener Test, dass das
neue Flag nur über `config/ai-providers.yaml` gesetzt wird (AC-1/AC-13).

## 12. Out-of-scope

- Secret-/Token-Verfahren zwischen Orchestrator und Subagent.
- Änderung der Classifier-/Auto-Mode-Logik oder Beeinflussung des Classifiers; keine Aussage darüber, ob
  ein Rollenfeld die Ablehnung (b) aus §2.2 beendet.
- Schließen der Tokenizer-/Indirektionslücken (`eval`, `$(...)`, `xargs`).
- Hook-Aktivierung/Deaktivierung durch den Agenten (Selbst-Deaktivierung ist Convention boundary).
- Änderung des Auto-Commit-Allowlist-Formats (#1181) und des Destructive-Gates (#1217).
- Rollenbindung auf anderen Providern ohne belegtes Feld.

## 13. Offene Fragen an den Nutzer

Keine ist entschieden; jede ist freigaberelevant.

1. Welcher Feld-Name wird gelesen (`agent_type` laut Doku-Extraktion oder anderes), und wie heißt das
   Capability-Flag (Arbeitsname `hook-role-field`)? Reicht eine Prüfung gegen den Rohtext der Doku, oder
   ist ein Live-Payload-Mitschnitt erforderlich?
2. Bleibt die Sentinel-Zeile in `agents/1-generic/git.md` (`:31`, `:42`, `:98`, `:159`) Pflicht, wird sie
   nur Fallback für Provider ohne Feld, oder entfällt sie bei Providern mit Feld (Folge: Reibung (b) aus §2.2
   nur bei bestätigter Classifier-Wirkung gemindert, nicht verifiziert)?
3. Darf das Rollenfeld `git` **allein** (ohne Sentinel) den `git`-Pfad freischalten (R1)?
4. Bei Mismatch Feld/Sentinel (R3): Reject (rc 2) oder nur Warnung/Audit? Welche Seite gewinnt?
5. Fehlendes Feld bei gesetztem `agent_id` und Flag true (R4): Sentinel-Fallback oder Reject
   (fail-closed)?
6. Ist `agent_type` für vom Orchestrator gespawnte Subagenten, für Custom-Agenten und für den Main-Chat
   vertrauenswürdig genug (siehe §5 Punkte 1-4)? Wie wird das vor Freigabe belegt?
7. Bleibt der Guard bei positiver Evidenz weiterhin als Convention boundary eingestuft (§5 Einstufung), oder
   soll er eine Security-Boundary-Aussage für die Rollenbindung erhalten?
8. Greift bei negativer Evidenz Entscheidung 38a (Nutzer bestätigt D-neu-4 erneut) und wer entscheidet, ab
   wann die Evidenz „negativ" ist (z. B. Feld fehlt bei einem Provider vs. bei Claude)?
9. Umgang mit Providern ohne Feld: nur Doku-Hinweis (Convention boundary), oder zusätzlich eine Sync-WARN
   je Provider, der Grants/Sentinel-Rollen nutzt?
10. Reichen die Testfälle T1-T13 oder soll zusätzlich ein Integrationstest mit echtem Harness-Lauf (Kosten,
    Plan Global Constraints Zeile 32) erfolgen?

## 14. Risiken

- Falsches Vertrauen: Ein Rollenfeld wird als Security boundary gelesen, obwohl Indirektion und Spawn-Pfade
  (§5 Punkt 1) offen bleiben.
- Verhaltensregression bei Providern ohne Feld; mitigiert durch AC-7.
- Template-Änderung (`git.md`) vs. Auto-Mode-Classifier: Wirkung unbekannt (§9).
- Doppelte Wahrheit (Feld vs. Sentinel) erhöht Guard-Komplexität in einer Sicherheitsdatei; Single-Parse-Refactor
  (#1169, Plan Task 7) berührt dieselbe Datei und läuft sequentiell davor.

## 15. Trace-Anker

`spec-id: SPEC-GUARD-ROLE-ATTRIBUTION-2026-11-11`
