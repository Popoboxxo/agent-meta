# Test-Umgebungen (`test-environments`)

`test-environments` deklariert pro Projekt, **wo** getestet und deployt werden darf:
lokal, auf einer entfernten Umgebung oder auf beidem. Der Block ist optional; ohne ihn
bleiben alle generierten Agenten byte-identisch. Er wird durch den Config-Load validiert,
vom Sync in die sechs Test-Rollen gerendert und von `agent-meta-manager` sowie der
Admin-UI mit denselben Regeln geschrieben.

Trace-Anker: `spec-id: SPEC-TEST-ENVIRONMENTS-2026-10-31` (`docs/specs/2026-10-31-test-environments-spec.md`).

---

## Zweck

Ohne Deklaration weiß ein Agent nicht, ob er lokal im Dev-Stack testen soll oder ob ein
Home-Assistant-Dev-Server beziehungsweise ein Sharkord-Stack das eigentliche Ziel ist.
`test-environments` macht das Ziel samt Zugriffsrechten explizit:

- Welche Umgebungen existieren (`kind`: `local`, `remote`, `both`).
- Welche URL beziehungsweise welcher Fallback gilt.
- Ob nur gelesen (`access: read`) oder auch deployt werden darf (`access: deploy`).
- Ob Remote-Zugriffe verboten, freigabepflichtig oder erlaubt sind (`remote-access`).
- Welcher Env-Var-Name das Token liefert — nie der Wert selbst.

Der Block ist opt-in. Fehlt er (oder ist er `null`/`{}`), ist das Feature unkonfiguriert.

---

## Namensabgrenzung: `environments:` vs. `test-environments:`

Beide Blöcke stehen in `.meta-config/project.yaml` und koexistieren, haben aber
verschiedene Aufgaben:

| Block | Bedeutung | Inhalt |
|---|---|---|
| `environments:` | Definitionen von Umgebungsvariablen (`scripts/lib/env.py`) | `description`, `default`, `required`, `secret`; erzeugt `.meta-config/env.sh`/`env.ps1` |
| `test-environments:` | Test-/Deploy-Ziele | `kind`, `url`, `token-env`, `access`, `remote-access`, `notes` |

`test-environments.<name>.token-env` **referenziert** einen Eintrag aus `environments:`
mit `secret: true`. Es ist keine zweite Secret-Definition und kein Wert. Diese Abgrenzung
steht ebenfalls in der Schema-Description (`config/project-config.schema.json`), im Rezept
von `agent-meta-manager` und im Hinweistext der Admin-UI. Eine Verwechslung führt zu
falscher Konfiguration (Anti-Ziel AZ6).

---

## Beispiel

```yaml
# .meta-config/project.yaml
environments:
  HA_DEV_TOKEN:
    description: Long-lived access token of the HA dev server
    secret: true

test-environments:
  ha-dev:
    kind: both                   # local | remote | both   (Default: local)
    url: "http://ha-dev.lan:8123"
    token-env: HA_DEV_TOKEN      # NUR der Name, nie der Wert
    access: deploy               # read | deploy           (Default: read)
    remote-access: ask           # deny | ask | allow      (Default: ask)
    notes: "Integration erst lokal testen, dann auf den Dev-Server."
  sharkord-local:
    kind: local
    notes: "Docker-Compose-Stack: docker compose run --rm test"
```

Alle Enum-Werte müssen gequotet werden, wenn sie wie YAML-Booleans aussehen könnten:
`deny: off` oder `allow: on` laden sonst als Bool und werden als Fehler abgelehnt
(„quote the value").

---

## Schema-Felder und Defaults

| Feld | Typ / Werte | Default | Bemerkung |
|---|---|---|---|
| `<name>` | `^[a-z0-9][a-z0-9-]*$` | — | Mapping-Key; andere Namen sind Fehler |
| `kind` | `local`, `remote`, `both` | `local` | `both` = erst lokal, dann remote |
| `url` | nicht-leerer String | — | optional; Fallback siehe unten; keine Userinfo |
| `token-env` | `^[A-Z][A-Z0-9_]*$` | — | Name eines `environments:`-Eintrags mit `secret: true` |
| `access` | `read`, `deploy` | `read` | `deploy` nur zusammen mit `remote-access` `ask`/`allow` |
| `remote-access` | `deny`, `ask`, `allow` | `ask` | konservativer Default |
| `notes` | String | — | freier Text, wird in die Tabelle gerendert; keine Secrets |

Defaults werden **nicht** in `project.yaml` geschrieben, sondern im Resolver angewendet.
Das Schema hat bewusst kein Top-Level-`default` (sonst würde `--fill-defaults` den Block
in jede Projekt-Config schreiben).

### Validierung

Hart geprüft wird im Python-Validator `scripts/lib/test_environments.py`, nicht im Schema
(das Schema ist Autocomplete-/Warn-Zusatz). Der Config-Load bricht unter anderem ab bei:

- unbekannten Keys oder einem Nicht-Mapping als Block,
- ungültigem Namen oder ungültigen Enum-Werten (inklusive Bool in einem Enum-Feld),
- `url` mit Userinfo (`user:pass@host`) oder mit `{{`/`}}`,
- `token-env`, das kein NAME ist oder auf keinen `environments:`-Eintrag mit
  `secret: true` verweist.

Warnungen (kein Abbruch) gibt es für wirkungslose Kombinationen: `url`/`remote-access` bei
`kind: local`, `access: deploy` bei `kind: local`, `access: deploy` zusammen mit
`remote-access: deny` (`deny` gewinnt) sowie einen nicht-leeren `default` im referenzierten
`environments:`-Eintrag (Secret-Wert in `project.yaml`).

---

## Semantik

### `kind`

| Wert | Verhalten |
|---|---|
| `local` | Nur lokale Tests und Dev-Stack; kein Remote-Zugriff. |
| `remote` | Die Remote-Umgebung ist das Testziel; Zugriff nur gemäß `remote-access`/`access`. |
| `both` | Erst lokal testen/entwickeln, danach Remote gemäß Freigabe. |

Bei mehreren Umgebungen werden alle gerendert; es gibt keine implizite Standardauswahl.

### `access`

| Wert | Wirkung |
|---|---|
| `read` | Nur lesen/abfragen (Status, Logs, Config-Check); kein Schreiben, kein Deploy. |
| `deploy` | Zusätzlich ausrollen/ändern, nur mit `remote-access` `ask` oder `allow`. |

### `remote-access`

| Wert | Wirkung |
|---|---|
| `deny` | Umgebung nie kontaktieren (ssh, scp, curl, `docker -H`, Deploy); Fund an `main_chat` melden. |
| `ask` (Default) | Stopp vor dem ersten Remote-Zugriff; Freigabeprotokoll siehe unten. |
| `allow` | Zugriff im Rahmen von `access` erlaubt; Deploys trotzdem im Ergebnis melden. |

---

## Referenzregel für `token-env`

Ein Token wird ausschließlich über seinen **Env-Var-Namen** referenziert:

```yaml
environments:
  HA_DEV_TOKEN:
    description: "Long-lived access token of the HA dev server"
    secret: true                 # Pflicht für die Referenz
test-environments:
  ha-dev:
    kind: remote
    token-env: HA_DEV_TOKEN      # nur der NAME
```

- Der referenzierte `environments:`-Eintrag muss `secret: true` tragen; nur der Bool
  `true` zählt (`secret: "true"` oder `secret: 1` sind Fehler).
- Der Wert kommt aus der Shell-Umgebung, bereitgestellt per
  `source .meta-config/env.sh` (aus dem `environments:`-Eintrag, maskiert).
- Der generierte Block nennt nur den Namen und den Hinweis auf `${NAME}`. Token-Werte
  dürfen weder ausgegeben noch geloggt noch in Dateien geschrieben werden.
- Ein `default` im referenzierten Secret-Eintrag löst eine Warnung aus — der Wert gehört
  nicht in `project.yaml`.

`env.py`, `mcp.py` und `.meta-config/secrets.local.yaml` bleiben unverändert; das Feature
liest `environments:` nur.

---

## Fallback-URL

Fehlt `url` bei einer Umgebung, greift nur unter engen Bedingungen ein Plattform-Fallback
(Spec §10.2):

1. `test-environments.<name>.url` hat Vorrang.
2. Fallback aus der **Projekt-Ebene** der Plattform-Konfiguration, wenn **genau eine**
   Umgebung mit `kind` `remote`/`both` keine `url` hat und der Plattformwert vom Projekt
   gesetzt ist (nicht der Default). Präzedenz: `platform.hacs.dev_instance_url` vor
   `platform.homeassistant.ha_url`.
3. Sonst nennt der Block „URL not configured"; der Agent fragt `main_chat` über
   `APPROVAL_REQUEST: target?`.

Der HA-Default (`ha_url` = `http://homeassistant.local:8123`) löst allein **keinen**
Fallback aus; `dev_instance_url` hat den leeren Default `""` und ist damit ebenfalls nur
bei einem echten Projektwert relevant.

---

## Freigabeprotokoll (`remote-access: ask`)

Die Freigabe ist ein Prompt-Protokoll, kein technischer Zwang:

1. Der Worker stoppt **vor** dem ersten Remote-Zugriff und liefert
   `STATUS: partial` mit
   `APPROVAL_REQUEST: env=<name>; action=<read|deploy: Aktion>`.
2. Der Orchestrator holt das Okay beim Nutzer (`main_chat`) ein und dispatcht den Auftrag
   erneut mit `APPROVED: env=<name>; action=<…>`.
3. Die Freigabe gilt nur für die genannte Umgebung und Aktion. Jede weitere Aktion erzeugt
   eine neue `APPROVAL_REQUEST`. Die Freigabe wird im Ergebnis vermerkt.
4. Bei `remote-access: deny` wird die Umgebung nie kontaktiert; der Agent meldet den
   Bedarf an `main_chat`. Bei `allow` ist der Zugriff im Rahmen von `access` erlaubt,
   Deploys werden trotzdem berichtet.

Ist das Ziel unklar, gilt dieselbe Rückfrage über `APPROVAL_REQUEST`.

---

## Grenzen: Convention boundary, kein `permissions`-Mechanismus

Die Durchsetzung ist eine **Convention boundary** (Prompt-Konvention), keine Security
boundary: Ein Agent hält sich an den gerenderten Block, es gibt keine technische Sperre,
keinen Hook und keine `permissions.ask`/`permissions.deny`-Einträge. Das Feature erzeugt
bewusst keine Einträge in `settings.json`; `remote-access: deny` ist deshalb keine
technische Blockade.

Native `permissions`-Einträge sind als Folge-Option **F6** dokumentiert und aus dem MVP
gestrichen: Globale Muster wie `Bash(ssh:*)` würden auch lokale Tests sperren, es fehlt ein
Capability-Flag, und ein Rollback müsste verwaltete Einträge wieder entfernen. Bis dahin
gilt ausschließlich das Prompt-Protokoll.

---

## Propagation an die Agenten

Der Sync rendert aus dem Block den Markdown-Abschnitt
`{{%TEST_ENVIRONMENT_BLOCK%}}` und setzt `{{%TEST_ENVIRONMENTS_SET%}}` auf `true`, sobald
mindestens eine Umgebung aufgelöst wurde. Das Gate `{{#if TEST_ENVIRONMENTS_SET}}` steht in
den sechs Rollen-Templates `tester`, `e2e-tester`, `developer`, `docker`,
`devops-engineer` und `test-executor`; die Plattform-Overrides erben den Block, der
Standalone-Override `sharkord-docker` enthält ihn manuell.

Unkonfiguriert bleibt der Block leer und wird samt Zeilenumbruch entfernt — die generierten
Dateien bleiben byte-identisch. Weitere Platzhalter-Details stehen in
[`sync-concept.md`](sync-concept.md).

Die Admin-UI (Sektion „Test Environments") und das Rezept 18 in `agent-meta-manager`
schreiben dasselbe Fragment in `.meta-config/project.yaml`. Beide verlangen für
Remote-Aktivierung eine Bestätigung (Behavior-Change) und akzeptieren niemals einen
Secret-Wert.

Escape in Dokumentation: `{{%VAR%}}` rendert als `{{VAR}}` (Issue #1082).

---

## Prüfen und Weiterführendes

```bash
# Config inklusive test-environments prüfen
python3 scripts/sync.py --validate

# Beispiel-Config mit kommentiertem Block
howto/configs/project.yaml.example
```

- Schema: `config/project-config.schema.json` → `properties."test-environments"`.
- Validator/Resolver/Renderer: `scripts/lib/test_environments.py`.
- Spec: `docs/specs/2026-10-31-test-environments-spec.md`.
