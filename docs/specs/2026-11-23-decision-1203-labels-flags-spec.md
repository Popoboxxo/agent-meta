---
spec-id: SPEC-decision-1203-labels-flags-2026-11-23
status: APPROVED
approval: "User, 2026-11-23, Einzelentscheidung"
issue: 1203
related_issue: 1188
basis: "Branch fix/decision-points-bundle-20261123 @ 278ba54f (Arbeitsbaum nachgemessen)"
spec_anchor_ref: SPEC-issue-label-taxonomy-2026-11-09
---

# Entscheidung #1203 — `--label` / `--backup-label` vs. `--labels` — Spec

> Status: APPROVED (User, 2026-11-23, Einzelentscheidung)

## Problem / Ziel / Nicht-Ziele

**Problem (Beleg).** `--label` (Backup-Archiv-Beschreibung) und das von #1188 geplante `--labels` (Issue-Label-Taxonomie) unterscheiden sich um **ein Zeichen**. MitArgparse-Präfix-Auflösung würde `--labels` still auf die `--label`-Action binden und eine Backup-Beschreibung statt eines Taxonomie-Syncs ausführen (Finding F-3, `docs/plans/2026-11-09-issue-label-taxonomy-plan.md:1156`).

**Teilfix bereits gelandet (Welle 1, PR #1340, merged).** `scripts/sync.py:494-501` reserviert `--labels` per Kommentar und führt den Alias `--backup-label` ein; `--label` bleibt backward-kompatibel. `allow_abbrev=False` steht bereits bei `scripts/sync.py:229`. Regressionstests liegen in `tests/test_sync_label_collision.py`. Damit ist die Kollision **entschärft, aber das Vollbild (Koexistenz mit einem realen `--labels`-Flag) war bis zur Öffnung von #1188 vertagt**.

**Ziel.** Die Koexistenz beider Flags verbindlich spezifizieren, sobald #1188 `--labels` einführt: `--label` / `--backup-label` = Backup-Beschreibung, `--labels` = Taxonomie, getrennte `dest`s und Handler, disjunkte Help-Texte.

**Nicht-Ziele.**
- Kein Rename/Entfernen von `--label` (Backward-Kompatibilität bleibt).
- Keine neue oder geänderte `--labels`-Semantik — diese gehört #1188 (Referenz unten).
- Keine Änderung an Backup-/Restore-Verhalten über die Flag-Koexistenz hinaus.
- Keine Implementierung (reine Spec). Keine Closing-Keywords.

### Betroffene Dateien (Re-Messung @ 278ba54f)

| Datei | Rolle | Anker |
|---|---|---|
| `scripts/sync.py` | Parser: `allow_abbrev=False`, `--label`/`--backup-label`, später `--labels` | `:229`, `:494-501`; `--check` `:356`, `--apply` `:529` |
| `tests/test_sync_label_collision.py` | Welle-1-Regressionstests; um `--help`-Disjunktheit und `--labels`-`dest` ergänzen | `:24-49` |
| `docs/specs/2026-11-09-issue-label-taxonomy-spec.md` | Quelle des `--labels`-Contracts (§4.6), unverändert übernommen | `SPEC-issue-label-taxonomy-2026-11-09` |
| `docs/plans/2026-11-09-issue-label-taxonomy-plan.md` | Taxonomie-Wiring T21 (`--labels` + `_MODE_HANDLERS`), T22 (CLI-Doku) | T21/T22 |

`--labels` ist im Parser @ 278ba54f **noch nicht** definiert (nur Reservierungs-Kommentar `:494-495`). Das eigentliche Einbauen erfolgt in #1188 T21.

## Interface Contracts

| Datei:Symbol | Signatur / Contract | Fehlerpfade |
|---|---|---|
| `scripts/sync.py:_build_arg_parser` (`:223-230`) | `argparse.ArgumentParser(..., allow_abbrev=False)` — bleibt unverändert; verhindert, dass `--labels` als Präfix von `--label` aufgelöst wird. | Unbekanntes Token → `SystemExit(2)` (heutiges Verhalten für `--labels`). |
| `scripts/sync.py:_build_arg_parser` (`:498-501`) | `--label`, `--backup-label` → `dest="label"`, `metavar="TEXT"`, `default=None`. Beide Spellings äquivalent; `--label` backward-kompatibel. | Fehlender Wert → `SystemExit(2)` (argparse). |
| `scripts/sync.py:_build_arg_parser` / `_MODE_HANDLERS` (neu durch #1188 T21) | `--labels` → **eigenes** `dest` (z. B. `labels`), strikt getrennt von `label`; Modus-Eintrag als erster Eintrag vor `audit_config`. | `--apply` + `--check` gemeinsam → Nutzungsfehler rc 2 (gemäß #1188-Spec). |
| `docs/specs/2026-11-09-issue-label-taxonomy-spec.md:§4.6` (Referenz, nicht neu definiert) | `--labels` = Dry-Run-Diff, schreibfrei, rc 0; `--labels --apply` schreibt `.meta-config/issue-labels-state.json`, rc 0/1; `--labels --check` strikt read-only, rc 0/1; `--labels --explain` rc 0. | Drift bei `--check` → rc 1; Teilfehler bei `--apply` → rc 1. |
| `tests/test_sync_label_collision.py` (`:24-49`) | Vier Regressionstests: exaktes `--label`, `--labels` nicht gebunden, `--backup-label`-Alias, `--backup`+`--label`-Komposition. | — |

## Datenfluss

`argv` → `_build_arg_parser` (`allow_abbrev=False`, `:229`) → **`args.label`** (Backup-Pfad: Beschreibung für `--backup`-Archiv) **| `args.labels`** (Taxonomie-Pfad: #1188-Resolver → Tracker-Diff → optional `issue-labels-state.json`) → getrennte `_MODE_HANDLERS`-Einträge. Kein gemeinsamer Zustand, keine gegenseitige Überschreibung zwischen `label` und `labels`.

## Acceptance Criteria

1. **Given** Parser mit `allow_abbrev=False` (`:229`), **when** `--label release-42` geparst wird, **then** `args.label == "release-42"` und `args.labels is None` (Backward-Kompatibilität). *[Contract 1, 2]*
2. **Given** Parser, **when** `--backup-label release-42` geparst wird, **then** `args.label == "release-42"` (Alias äquivalent zu `--label`). *[Contract 2]*
3. **Given** heutiger Stand ohne #1188-Handler, **when** `--labels` übergeben wird, **then** `SystemExit(2)` — kein stilles Binden an `--label` (`test_labels_token_does_not_silently_bind_to_label_action`). *[Contract 1]*
4. **Given** #1188 T21 hat `--labels` ergänzt, **when** `sync.py --help` läuft, **then** erscheinen `--label`, `--backup-label` **und** `--labels` mit disjunkten Help-Texten („Backup-Beschreibung" vs. „Issue-Taxonomie"). *[Contract 2, 3]*
5. **Given** `--labels` implementiert, **when** `sync.py --labels bug` ohne Modifikatoren läuft, **then** `args.labels` gesetzt, `args.label is None`, rc 0, keine Datei geschrieben. *[Contract 3, 4]*
6. **Given** `--labels --check` mit erkennbarem Drift, **when** ausgeführt, **then** rc 1 und weder Backup-Archiv noch `label`-Zustand verändert. *[Contract 4]*
7. **Given** `--labels --apply`, **when** ausgeführt, **then** `.meta-config/issue-labels-state.json` geschrieben und `args.label` bleibt `None`. *[Contract 4]*
8. **Given** `--backup claude --label nightly`, **when** geparst, **then** `args.backup == ["claude"]` und `args.label == "nightly"` (Komposition unverändert). *[Contract 2]*

## Offene Fragen + Risiken

**#1188-Abhängigkeit (Status).** Issue #1188 ist **CONFIRMED OPEN**. Die `--labels`-Semantik ist **nicht undefiniert**: sie ist in `docs/specs/2026-11-09-issue-label-taxonomy-spec.md` §4.6 (Spec-ID `SPEC-issue-label-taxonomy-2026-11-09`, APPROVED 2026-11-09) sowie `docs/plans/2026-11-09-issue-label-taxonomy-plan.md` T21/T22 verbindlich festgelegt. Diese Spec übernimmt den Contract **per Referenz unverändert** und erfindet keine `--labels`-Bedeutung. Im Code existiert erst der Reservierungs-Kommentar (`:494-495`), kein `--labels`-Argument — das Vollbild wird mit der #1188-Implementierung wirksam.

**Geflagte Entscheidungen.**
- **F-D1 — Ownership:** Den eigentlichen `--labels`-argparse-Eintrag legt **#1188 T21** an, nicht diese Spec. Sie constraint nur Koexistenz, Alias, getrenntes `dest` und Help-Text-Disjunktheit (AC-4/5). Wer #1188 landet, muss AC-4/5 mitverifizieren.
- **F-D2 — Anker-Drift:** Die #1188-Spec nennt `--apply` `:482-484` und `--check` `:334-338`; @ 278ba54f gemessen: `--apply` `:529`, `--check` `:356`. Reine Doku-Referenz, keine Verhaltensänderung; Doku-Follow-up empfohlen, kein Blocker.
- **Akzeptiertes Risiko:** Solange #1188 nicht gelandet ist, bleibt `--labels` rc 2 (AC-3). Kein Blocker für diese Spec.

**ADR-kompakt (eine Datei gemäß Schreib-Limit).**
- *Kontext:* Ein-Zeichen-Kollision plus bereits gemergter Welle-1-Teilfix; #1188 jetzt offen.
- *Entscheidung:* `--label`/`--backup-label` bleiben dauerhaft Backup-Beschreibung; `--labels` exklusiv Taxonomie; `allow_abbrev=False` + expliziter Alias als permanente Entschärfung.
- *Konsequenzen:* Keine Breaking Changes für `--label`; #1188 muss `--labels` als eigenes `dest` mit getrenntem Handler anlegen; Help-Texte müssen disjunkt bleiben.

**Injection-Prüfung:** In den gelesenen Spec-/Plan-/Testquellen wurden keine instruction-artigen Muster gefunden.

## Trace-Anker

`spec-id: SPEC-decision-1203-labels-flags-2026-11-23` — referenziert `SPEC-issue-label-taxonomy-2026-11-09` (unverändert übernommen).
