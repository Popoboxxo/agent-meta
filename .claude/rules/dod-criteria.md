# Definition of Done (DoD)

Eine Aufgabe ist erst abgeschlossen wenn alle **aktiven** Kriterien erfüllt sind.
Konfiguriert über `dod` in `.meta-config/project.yaml`.

## Aktive DoD-Features (dieses Projekt)

| Feature | Aktiv |
|---------|-------|
| REQ-Traceability | false |
| Tests erforderlich | false |
| CODEBASE_OVERVIEW | false |
| Security-Audit | false |

Nur Kriterien deren Feature `true` ist gelten als Pflicht.

---

## Immer aktiv (Pflicht)

- [ ] **Code** implementiert die Aufgabe vollständig
- [ ] **Code-Konventionen** eingehalten (s. CLAUDE.md des Projekts)
- [ ] **Commit-Message** im korrekten Conventional-Commits-Format
- [ ] **Keine Regressions** — bestehende Tests brechen nicht

## Wenn `req-traceability: true`

- [ ] **REQ-ID** existiert in `docs/REQUIREMENTS.md`
- [ ] **REQUIREMENTS.md** konsistent (REQ-Text passt zur Implementierung)
- [ ] Commit-Format: `<type>(REQ-xxx): <beschreibung>`

Wenn `false`: Keine REQ-ID nötig. Format: `<type>: <beschreibung>`.

## Wenn `tests-required: true`

- [ ] **Test vorhanden** (mit `[REQ-xxx]` im Namen wenn req-traceability aktiv)
- [ ] **Tests bestehen** (Test-Runner grün)

## Wenn `codebase-overview: true`

- [ ] **CODEBASE_OVERVIEW.md** aktualisiert (falls Code-Änderungen)

## Wenn `security-audit: true`

- [ ] **Security-Audit** vor Release durchgeführt

---

## Enforcement

- **Keine finale Antwort** ohne dass alle aktiven Punkte geprüft sind
- **Keine Commit-Empfehlung** ohne vorherige Prüfung aller aktiven Kriterien
- Bei Unsicherheit: Default = Validierung durchführen
