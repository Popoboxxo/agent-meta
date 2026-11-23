---
spec-id: SPEC-1204-ADMINUI-CONVENTIONS
title: "Admin-UI: inerte conventions.issues.* kennzeichnen, issues.language editierbar machen (#1204)"
status: APPROVED
approval: "User, 2026-11-23, Einzelentscheidung"
issue: 1204
issue-url: "https://github.com/Popoboxxo/agent-meta/issues/1204"
branch: fix/decision-points-bundle-20261123
base-commit: 278ba54f
date: 2026-11-23
class: M
depends-on: SPEC-issue-label-taxonomy-2026-11-09
---

# Admin-UI: Conventions-Overrides-Felder (#1204) — Spec

> Status: APPROVED (User, 2026-11-23, Einzelentscheidung)

Bindende Nutzerentscheidung vom 23.11.: #1188 ist offen (Dependency erfüllt), #1204 läuft autonom durch die Pipeline. Diese Spec ist die **Kurzfrist-Variante** aus Issue-Vorschlag 1: Felder kennzeichnen statt löschen, `language` editierbar machen. Keine Implementierung, keine Änderung an Render- oder Config-Pfaden.

## Problem / Ziel / Nicht-Ziele

**Problem (re-gemessen @ `278ba54f`, Branch `fix/decision-points-bundle-20261123`):**

| Anker (verifiziert) | Befund |
|---|---|
| `docs/ui/admin-ui.html:4178-4183` | `viewProjectConventionsOverrides()` verspricht „Override individual convention fields …“; grüne `ok`-Badge suggerieren Wirkung. |
| `:4211-4226` | `DOMAIN_FIELDS.issues` bietet genau 4 Felder: `title_format` (:4221), `types` (:4222), `labels.namespace` (:4223), `closing_keywords` (:4224). `language` fehlt. |
| `:4158-4168` | Per-Preset-Editor `issues` bietet dieselben 4 Felder, kein `language`. |
| `:4260-4268`, `:4286-4326`, `:4323` | `countOverrides()`/`render()` zählen und badgen alle Zeilen mit `badge ${isOverridden ? "warn" : "ok"}`. |
| `:4338-4339` | Save über `saveProjectSection("conventions-preset", …)` + `saveProjectSection("conventions", overrides, status)`; beide Keys bereits in `scripts/admin-server.py:239-246` (`PROJECT_WRITABLE_SECTIONS`) → kein Server-/API-Change nötig. |
| `scripts/lib/conventions.py:131-132`, `:277-292` | Einziger `issues`-Consumer: `_render_git_issue_naming()` liest genau jene 4 Felder → `GIT_ISSUE_NAMING_BLOCK`. |
| `agents/1-generic/git.md:159` | Einziger Verbraucher des Blocks; `git` erzeugt keine Issues → **keine Verhaltenswirkung**, nur Prosa im Prompt. |
| `scripts/lib/config.py:3454`, `:3501-3503` | `ISSUE_LANGUAGE` wird **unconditional** aus `issues.language` gelesen (Default `english`) — das einzige verhaltenswirksame Feld. |
| `scripts/lib/consistency/placeholders.py:140` | `ISSUE_LANGUAGE` allow-gelistet. |
| `agents/1-generic/feedback.md:120`, `prompt-governor.md:137`, `dependency-auditor.md:157`, `app-lifecycle-governor.md:116` | `{{ISSUE_LANGUAGE}}`-Consumer. |
| `config/conventions-presets.yaml:53-67` | `default.issues.language: english` (:67); `calver` (:91-97) und `conventional-strict` (:123-129) ohne `language`. |
| `tests/test_issue_language.py:26-56` | Pinnt Default, Override und Unabhängigkeit von der `git`-Rolle. |

Präzisierung zum Issue-Text: „not consumed by any agent“ ist ungenau — die 4 Felder werden sehr wohl von `git.md:159` konsumiert, aber ausschließlich als Hilfetext. Zutreffend ist: **keine Auswirkung auf Issue-Erzeugung**. Die vom Issue genannten Zeilen (`git.md:151`, `config.py:2720`, `admin-ui.html:4197-4202`) sind ältere Stände; oben stehen die am Checkout gemessenen Werte.

**Ziel:** (1) `conventions.issues.language` in beiden Admin-UI-Editoren editierbar; (2) die 4 wirkungslosen Felder mit einem klaren `documentation-only`-Hinweis plus Badge markieren, damit keine Wirkung suggeriert wird; (3) ein Test pinnt, dass jedes angebotene Feld entweder einen benannten Consumer hat oder explizit als documentation-only markiert ist.

**Nicht-Ziele:** Keine Änderung an `scripts/lib/conventions.py`, `scripts/lib/config.py`, `config/conventions-presets.yaml`, `agents/1-generic/git.md` oder Platzhalter-Allow-Liste; kein #1188-Code (Taxonomie/Adapter/CLI); keine Schema-, API- oder Persistenzänderung; keine Tracker-API-Calls; keine Felder oder bestehende Projektdaten löschen; keine Entfernung der `issues`-Domain aus der Overrides-View in diesem Schritt (siehe D-1204-C); keine Implementierung.

## Interface Contracts (Datei:Symbol, Signatur, Fehlerpfade)

| ID | Datei:Symbol | Signatur / Typ | Rolle & Fehlerpfad |
|---|---|---|---|
| IC-1 | `docs/ui/admin-ui.html:4211-4226` · `DOMAIN_FIELDS.issues` | Array von `[path: string[], label: string, type: "scalar"\|"list", docOnly?: boolean]` (4. Element optional; äquivalente Set-Lösung zulässig) | Ergänzt `[["language"], "language", "scalar"]`. Die 4 bestehenden Zeilen `:4221-4224` erhalten `docOnly: true`; `language` bleibt ohne Marker. `countOverrides()` (`:4260-4268`) und `render()` (`:4286-4326`) destrukturieren weiterhin kompatibel; Zählung bleibt unverändert. |
| IC-2 | `docs/ui/admin-ui.html:4158-4168` · Per-Preset-Editor `issues` | `scalarField(label: string, obj: object, key: string)` | Ergänzt `scalarField("language", issues, "language")`; Typ `scalar`, kein Validierungszwang, kein Default-Schreiben. Save-Pfad `:4338-4339` bleibt unverändert (existierende Keys). |
| IC-3 | `docs/ui/admin-ui.html:4178-4183` · Intro-Text + `:4286-4326` · `render()` | Statischer Hinweistext; Badge-Klasse `badge ok\|warn\|muted` | Hinweis: die 4 markierten Felder wirken nur auf den Hilfetext in `git.md`, nicht auf Issue-Erzeugung; `language` ist das verhaltenswirksame Feld. Für `docOnly`-Zeilen ersetzt `muted` + Label `documentation only` die grüne `ok`-Badge (`:4323`). Kein toter Link auf eine noch nicht ausgelieferte #1188-Sektion (D-1204-B). |
| IC-4 | `scripts/lib/config.py:3454` · `_build_convention_variables()` / `:3501-3503` `ISSUE_LANGUAGE` | `variables["ISSUE_LANGUAGE"]: str` = `(resolved.issues or {}).get("language") or "english"` | **Read-only, unverändert.** Unconditional (nicht an `applies_to_roles: [git]` gekoppelt). Fehlerpfad: fehlender/leerer Wert → `english`, wie heute. |
| IC-5 | `scripts/lib/conventions.py:131-132` · `render_convention_block()` / `:277-292` · `_render_git_issue_naming(spec: dict) -> str` | Liest `title_format`, `types`, `labels.namespace`, `closing_keywords` → `GIT_ISSUE_NAMING_BLOCK` | **Read-only, unverändert.** Einziger Verbraucher `agents/1-generic/git.md:159`. |
| IC-6 | `tests/test_admin_ui_conventions_overrides_section.py` (neu; Stil `tests/test_admin_ui_auto_commit_section.py:1-33`) | pytest, statische HTML-Slices, `-> None` | Pinnt: `language`-Zeile in beiden Editoren, `docOnly`-Marker auf den 4 Feldern, Hinweistext, keine `ok`-Badge für `docOnly`, Save-Pfad unverändert, Consumer-Abbildung je angebotenem Feld (Consumer **oder** `docOnly`). `tests/test_issue_language.py` bleibt grün. |

## Datenfluss

1. **Input:** `config/conventions-presets.yaml` (Preset, `:53-67`) + `project.yaml` → `conventions` / `conventions-preset` → Admin-UI `viewProjectConventionsOverrides()` (`:4178`).
2. **Transformation:** `DOMAIN_FIELDS` (`:4211`) + `getPath`/`setPath`/`delPath` (`:4228-4258`) bauen `overrides`; `render()` (`:4270`) zeigt Preset-Default, Override, Active Value und `docOnly`-Kennzeichnung.
3. **Output:** `saveProjectSection("conventions-preset", …)` + `saveProjectSection("conventions", overrides, …)` (`:4338-4339`) → `PUT /api/config/project/section`; `PROJECT_WRITABLE_SECTIONS` (`scripts/admin-server.py:239-246`) bereits zuständig.
4. **Runtime-Verbrauch (unverändert):** `conventions.issues.language` → `ISSUE_LANGUAGE` (`config.py:3501`) → `feedback.md:120` u. a.; die 4 markierten Felder → `GIT_ISSUE_NAMING_BLOCK` (`conventions.py:277`) → `git.md:159` (Hilfetext).
5. **Persistenz:** ausschließlich bestehende `conventions`/`conventions-preset` in `project.yaml`. Keine neue Datei, kein State, kein API-Vertrag.

## Acceptance Criteria

1. **AC-01 — `language` editierbar (IC-1, IC-2, IC-6):** Gegeben ein geladenes Preset mit `issues.language: english`; wenn der Nutzer in der Overrides-View und im Preset-Editor `language` auf `deutsch` setzt und speichert, dann enthält `conventions.issues.language` den Wert `deutsch` und `ISSUE_LANGUAGE` rendert `deutsch` (`tests/test_issue_language.py:33-38` bleibt grün).
2. **AC-02 — Inert-Felder gekennzeichnet (IC-1, IC-3, IC-6):** Gegeben die Overrides-View; wenn `title_format`, `types`, `labels.namespace` oder `closing_keywords` angezeigt werden, dann trägt die Zeile `documentation only` mit `muted`-Badge und es erscheint kein grünes `ok` als Wirksamkeitsindikator; die Werte bleiben editierbar und gespeichert.
3. **AC-03 — Keine suggerierte Wirkung (IC-3, IC-6):** Gegeben der Intro-Text `:4181-4183`; wenn die View gerendert wird, dann steht dort explizit, dass die markierten Felder nur den `git.md`-Hilfetext betreffen und `language` das verhaltenswirksame Feld ist; kein Link auf eine nicht vorhandene #1188-Sektion.
4. **AC-04 — Consumer-Pin (IC-1, IC-5, IC-6):** Gegeben die Menge der `DOMAIN_FIELDS.issues`-Labels; wenn der Test die Abbildung prüft, dann hat jedes Label entweder einen benannten Consumer im Render-Pfad (`ISSUE_LANGUAGE` bzw. `GIT_ISSUE_NAMING_BLOCK`) oder ist als `docOnly` markiert; ein neu hinzugefügtes Feld ohne beides lässt den Test fehlschlagen.
5. **AC-05 — Regressionsfrei (IC-4, IC-5, IC-6):** Gegeben der Checkout `278ba54f`; wenn `python3 scripts/sync.py --validate` und die Testsuiten laufen, dann sind alle grün; `conventions.py`, `config.py`, `git.md`, `conventions-presets.yaml` und `tests/test_issue_language.py` sind byte-identisch unverändert.

## Offene Fragen + Risiken

- **D-1204-A (entschieden, Kurzfrist):** Markieren statt Entfernen. Markierung erhält bestehende Projektdaten und bleibt kompatibel mit dem laufenden #1188-Plan (Konflikte in der 6.000-Zeilen-UI-Datei vermeiden). Wieder öffnen nur mit neuer User-Entscheidung.
- **D-1204-B (offen, Default = kein toter Link):** Hinweistext mit #1188-Verweis jetzt oder erst nach Auslieferung der neuen Sektion? Default: neutraler Hinweis ohne Link (AC-03); Eskalation an User, falls der Verweis schon jetzt gewünscht ist.
- **D-1204-C (offen, vertagt — #1188-Abhängigkeit):** #1204-AC-3 verlangt nach #1188 nur **einen** Ort für Issue-Konventionen. Der APPROVED-#1188-Spec definiert ein eigenes `issue-conventions`-Pane (AC-21), schreibt aber nicht die Entfernung der alten `issues`-Domain vor; Risiko F-4 (`docs/specs/2026-11-09-issue-label-taxonomy-spec.md:923`) empfiehlt stattdessen einen Deprecation-Hinweis. Default: nach #1188 zuerst Hinweis/Redirect, Entfernung der `issues`-Zeilen nur mit separater Freigabe. Kein Feld-Set aus einer undefinierten Taxonomie erfinden.
- **R-1:** Nur der `default`-Preset hat `language: english` (`:67`); `calver`/`conventional-strict` zeigen in der UI `—`, zur Laufzeit gilt `english`. Hinweistext darf daraus keinen „fehlenden Wert“ ableiten.
- **R-2:** Der Issue-Text nennt veraltete Zeilennummern und die ungenaue Formulierung „not consumed by any agent“; diese Spec korrigiert beides (siehe Re-Messung). Kein Eingriff in den Issue-Text nötig.
- **ADR (eingebettet, adr.github.io-Format; Separate Datei durch Single-File-Scope ausgeschlossen):** **Kontext** — die Admin-UI bot 4 Felder ohne Verhaltenswirkung an, während das einzige wirksame Feld fehlte; #1188 liefert die neue Taxonomie, lässt die alte View aber coexistieren (F-4). **Entscheidung** — kurzfristig markieren statt löschen, `language` in beide Editoren aufnehmen, keine Render-/Config-Pfade antasten; die final Feldmenge bleibt eine vertagte Entscheidung. **Konsequenzen** — keine Datenverluste, kein Konflikt mit dem #1188-Plan, Consumer-Pin als Test; D-1204-B/C bleiben Beobachtungspflicht.

**Coverage-Checkliste:** Pflichtabschnitte vorhanden ✓ · IC-1..IC-6 ohne Platzhalter, Typen und Fehlerpfade benannt ✓ · AC-01..AC-05 in Gegeben/Wenn/Dann, je mindestens einem IC zugeordnet ✓ · Betroffene Dateien, Nicht-Ziele und #1188-Dependency benannt ✓ · Trace-Anker gesetzt ✓.

## Trace-Anker: spec-id: SPEC-1204-ADMINUI-CONVENTIONS
