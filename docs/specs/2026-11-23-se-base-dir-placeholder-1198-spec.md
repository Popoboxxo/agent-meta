---
spec-id: SPEC-se-base-dir-placeholder-1198
status: APPROVED
approval: "User, 2026-11-23, generelle Freigabe (Bug-Welle)"
---

# SE_BASE_DIR single-brace placeholder (#1198) — Spec
> Status: APPROVED (User, 2026-11-23, generelle Freigabe)

## Problem / Ziel / Nicht-Ziele

**Problem (Issue #1198, wörtlich):**
> Die SE-Kaskade gibt ihren Ablageort über `SE_BASE_DIR` vor. In den Templates existieren dafür **zwei** Schreibweisen: `{{SE_BASE_DIR}}` (wird von `sync.py` ersetzt) und `{SE_BASE_DIR}` (einfache Klammer, wird **nie** ersetzt).
> `scripts/lib/variables.py:109` definiert den einzigen Platzhalter-Pattern der Template-Engine: `_VAR_PATTERN = re.compile(r"\{\{([A-Z0-9_]+)\}\}")`. Ein Token mit einfacher Klammer kann also konstruktionsbedingt nie getroffen werden. […] der geplante harte Fehler ab 2.1.0 wird diese 18 Stellen **nicht** erwischen. Der Fehler bleibt damit still.

Auswirkung: bei aktiver SE-Kaskade landet das Literal `{SE_BASE_DIR}` in generierten Agenten; Schreibpfade (z. B. `se-architect.md`, `se-validator.md`, `se-verifier.md`) zeigen auf einen wörtlichen Ordner namens `{SE_BASE_DIR}`.

**Ziel:** Einheitliche, substituierbare Platzhalterschreibweise in den 12 SE-Templates; kein stummer Literal-Token im gerenderten Output; Regression durch Consistency-Check/Golden-Test ausgeschlossen.

**Nicht-Ziele:** Keine Änderung an der Template-Engine (`_VAR_PATTERN` bleibt doppel-klammrig), keine neue Variable, keine Änderung an Pfad-Semantik/Zell-Hierarchie, keine SE-Kaskade wird gestartet, kein Code wird in diesem Spec-Schritt geschrieben.

**Re-Messung am lokalen Checkout (Branch `fix/bug-wave1-20261123`, HEAD `e681c792`; abweichend von der task-genannten Referenz `e29381db`):**

| Messung | Ergebnis |
|---|---|
| `(?<!\{)\{SE_BASE_DIR\}(?!\})` in `agents/1-generic/se-*.md` | **0 Treffer** |
| `SE_BASE_DIR` (beliebig) in `agents/1-generic/se-*.md` | **0 Treffer** |
| `{{ARTIFACT_SE_*_DIR}}` in denselben 12 Dateien | **22 Treffer** (18 konvertierte + 4 schon immer doppelt) |
| Golden-Test `test_no_single_brace_se_token` (`tests/test_artifact_locations_templates.py:232`) | vorhanden, regex `(?<!\{)\{SE_[A-Z0-9_]*(?!\})` |

**Befund:** Der Fix ist im Arbeitsbaum bereits umgesetzt (T11/#1186-Arbeitsstand): alle 18 einfachen Token wurden auf doppelte, matrix-konforme Variablen `{{ARTIFACT_SE_*_DIR}}` umgestellt. Der Spec dokumentiert den Soll-Zustand und die Abnahme; eine erneute Code-Änderung ist **nicht** nötig, sofern die AC gegen diesen Stand grün sind. Falls der Patch gegen `e29381db` (wo die 18 Token noch stehen) angewendet werden soll, gilt die untenstehende historische Inventarliste als Fix-Anker.

## Interface Contracts

| Datei:Symbol | Signatur / Typ | Rolle & Fehlerpfad |
|---|---|---|
| `scripts/lib/variables.py:_VAR_PATTERN` | `re.compile(r"\{\{([A-Z0-9_]+)\}\}")` | Einziger substituierbarer Platzhalter; einfache Klamter trifft nie. Kein Fehlerpfad (stilles Übersehen). |
| `scripts/lib/variables.py:substitute()` | `substitute(text: str, variables: dict, source_label: str, log: SyncLog, strict: bool=False) -> str` | Ersetzt `{{VAR}}`; D3(a): warnt bis `_UNRESOLVED_PLACEHOLDER_GRACE_UNTIL=(2,1,0)`, danach `SyncError`. Einfache-Klammer-Token umgehen auch den harten Fehler. |
| `scripts/lib/config.py:build_variables()` (ca. `:2840`, `:2971`) | `variables["SE_BASE_DIR"] = se_output.get("base_dir", "SE")`; später `variables["SE_BASE_DIR"] = variables["ARTIFACT_SE_ROOT"]` | Definiert `SE_BASE_DIR` (Alias). Muss unverändert bleiben — kein Produktionscode ändern. |
| `config/role-defaults.yaml:SE_BASE_DIR` (`:3081`) | `SE_BASE_DIR: SE` | Config-Default des Alias. |
| `tests/test_artifact_locations_templates.py:test_no_single_brace_se_token()` | `-> None` | Golden-Test: 0 Treffer für `SE_SINGLE_BRACE_RE` und kein `SE_BASE_DIR`-Literal in den 12 `T11_TEMPLATES`. |
| `docs/specs/2026-11-09-artifact-locations-matrix-spec.md` | Referenz (Spec §2.4/§3.1/§3.2, F-1) | Legt `ARTIFACT_SE_*_DIR`-Variablen und Zell-Hierarchie fest; nicht verhandelbar. |

**Historische 18/12-Inventarliste (Issue #1198, Stand vor #1186/T11):**

| Datei | Zeilen (Original-Token) | Heutige Variable |
|---|---|---|
| `se-architect.md` | 52, 62, 114, 117 | `ARTIFACT_SE_ARCHITECTURE_DIR` / `_ADR_DIR` / `_ARCHITECTURE_DIR` / `_REPORTS_DIR` |
| `se-requirements.md` | 43, 184 | `ARTIFACT_SE_REQUIREMENTS_DIR` |
| `se-critic.md` | 56, 110, 114 | `ARTIFACT_SE_REVIEWS_DIR` / `_REVIEWS_DIR` / `_REPORTS_DIR` |
| `se-component-requirements.md` | 159 | `ARTIFACT_SE_ARCHITECTURE_DIR` |
| `se-developer.md` | 188 | `ARTIFACT_SE_IMPLEMENTATION_DIR` |
| `se-integration-and-test-manager.md` | 263 | `ARTIFACT_SE_TESTPLAN_DIR` |
| `se-interface-mgr.md` | 153 | `ARTIFACT_SE_INTERFACES_DIR` |
| `se-termination.md` | 154 | `ARTIFACT_SE_DECISIONS_DIR` |
| `se-junior-developer.md` | 171 | `ARTIFACT_SE_IMPLEMENTATION_DIR` |
| `se-senior-developer.md` | 144 | `ARTIFACT_SE_IMPLEMENTATION_DIR` |
| `se-validator.md` | 177 | `ARTIFACT_SE_VALIDATION_DIR` |
| `se-verifier.md` | 191 | `ARTIFACT_SE_VERIFICATION_DIR` |

Summe: 4+2+3+1×9 = **18 Stellen in 12 Dateien**. Vier weitere Stellen nutzten schon `{{SE_BASE_DIR}}` (`se-component-requirements.md:61,142,281`, `se-requirements.md:83`; heute ebenfalls auf `ARTIFACT_SE_*` umgestellt). Pfade präziser: alle unter `agents/1-generic/`.

## Datenfluss

`Issue #1198 / 18 Einfach-Klammer-Token` → (Fix #1186/T11, bereits im Checkout) → `{{ARTIFACT_SE_*_DIR}}` in 12 SE-Templates → `sync.py` → `variables.substitute()` mit `_VAR_PATTERN` → `variables["ARTIFACT_SE_*_DIR"]` aus `config.build_variables()` → gerenderte Agenten in `.claude/agents/` (Consumer-Projekte mit aktiver SE-Kaskade). Persistenz: SE-Artefakte im aufgelösten Kaskadenpfad; kein Literal `{SE_BASE_DIR}`.

## Acceptance Criteria

1. **AC-01 (Golden):** Given die 12 SE-Templates, When `test_no_single_brace_se_token` läuft, Then 0 Offender — kein `SE_SINGLE_BRACE_RE`-Treffer, kein `SE_BASE_DIR`-Literal. *(Karte: Test-Symbol oben.)*
2. **AC-02 (Statisch):** Given `agents/1-generic/se-*.md`, When `grep -rnE '(^|[^{])\{SE_BASE_DIR\}'` läuft, Then 0 Treffer.
3. **AC-03 (Konsistenz):** Given der Consistency-Check, When er gegen den Output läuft, Then kein `placeholder.single-brace`-Finding in `agents/`, `commands/`, `rules/`; bekannte Einfach-Klammer-Namen (z. B. `{SE_BASE_DIR}`) würden als Finding gemeldet (Checker-Fähigkeit via Fixture belegt). *(Wenn der Check noch keinen solchen Finding-Typ kennt: Offene Frage Q2.)*
4. **AC-04 (Substituierbarkeit):** Given ein gerendertes `se-architect`, When der Output geprüft wird, Then kein `{SE_` mehr und der Pfad enthält den aufgelösten `ARTIFACT_SE_*_DIR`-Wert.
5. **AC-05 (Rebaseline):** Given das self-hostete Repo, When `python3 scripts/sync.py --validate`/Consistency-Check laufen, Then grün; falls `generated-file-hashes`/`context-hashes` durch die Umstellung drifteten, ist ein AC01-konformes Rebaseline nötig (nur getrackte Pfade).
6. **AC-06 (Nicht-Regression):** Given Templates, die heute schon doppelte Klammern nutzen, When gesynct wird, Then unverändertes Verhalten.

## Offene Fragen + Risiken

- **Q1 (Product Decision, explizit flaggen):** Namens-/Semantik-Entscheidung `SE_BASE_DIR` (Alias) vs. kanonisches `ARTIFACT_SE_*_DIR` wurde in #1186 getroffen (Matrix gewinnt, Alias bleibt). Der Spec übernimmt diese Entscheidung unverändert; **kein eigener Entwurf**. Soll #1198 isoliert gegen `e29381db` (ohne #1186) gefixt werden, ist zu klären: `{{SE_BASE_DIR}}` (Alias mit Default `SE`) oder direkt `{{ARTIFACT_SE_*_DIR}}`? Empfehlung: direkt die Matrix-Variablen, um doppelten Churn zu vermeiden.
- **Q2:** Consistency-Check-Typ `placeholder.single-brace` — im aktuellen Checkout nur als Test regex (`SE_SINGLE_BRACE_RE`) vorhanden; ob ein eigenes Finding im `consistency`-Modul existieren soll, ist #1186/Phase-E-Design zu entnehmen (Entscheidung 50: `agents/`, `commands/`, `rules/` abdecken). Nicht hier neu erfinden.
- **Q3 (Referenz-Drift):** Task nennt `main e29381db`; lokaler HEAD ist `fix/bug-wave1-20261123` @ `e681c792`. Re-Messung gilt für den lokalen Stand. Gegen `e29381db` sind die 18 Token vermutlich noch vorhanden — Fix ggf. dorthin cherry-picken.
- **Risiko:** Stille Fehlschläge dieser Klasse werden von D3(a)-Härtung nicht erfasst; nur der Consistency-Check/Golden-Test verhindert Wiederkehr.

## Trace-Anker: spec-id: SPEC-se-base-dir-placeholder-1198
