# Definition of Done (DoD)

Eine Aufgabe ist erst abgeschlossen wenn alle **aktiven** Kriterien erfüllt sind.
Welche aktiv sind, steuert `dod` in `.meta-config/project.yaml`.

## Immer aktiv (Pflicht)

- [ ] **Code** implementiert die Aufgabe vollständig
- [ ] **Code-Konventionen** eingehalten (s. CLAUDE.md des Projekts)
- [ ] **Commit-Message** im korrekten Conventional-Commits-Format
- [ ] **Keine Regressions** — bestehende Tests brechen nicht

## Wenn `req-traceability: true` (Default: true)

- [ ] **REQ-ID** existiert in `docs/REQUIREMENTS.md`
- [ ] **REQUIREMENTS.md** konsistent (REQ-Text passt zur Implementierung)
- [ ] Commit-Format: `<type>(REQ-xxx): <beschreibung>`

Wenn `false`: Keine REQ-ID nötig. Format: `<type>: <beschreibung>`.

## Wenn `tests-required: true` (Default: true)

- [ ] **Test vorhanden** (mit `[REQ-xxx]` im Namen wenn req-traceability aktiv)
- [ ] **Tests bestehen** (Test-Runner grün)

Wenn `false`: Kein Test als DoD-Kriterium.

## Wenn `codebase-overview: true` (Default: true)

- [ ] **CODEBASE_OVERVIEW.md** aktualisiert (falls Code-Änderungen)

Wenn `false`: Kein Doku-Update als DoD-Kriterium.

## Wenn `security-audit: true` (Default: false)

- [ ] **Security-Audit** vor Release durchgeführt

## Enforcement

- **Keine finale Antwort** ohne dass alle aktiven Punkte geprüft sind
- **Keine Commit-Empfehlung** ohne vorherige Prüfung aller aktiven Kriterien
- Bei Unsicherheit: Default = Validierung durchführen
