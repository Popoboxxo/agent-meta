---
spec-id: SPEC-TEST-ENVIRONMENTS-2026-10-31
title: Test-Umgebungen (lokal/remote) pro Projekt mit Remote-Freigabemodell
status: APPROVED
revision: 1.2
klasse: L (Bounded, mit Review-Loop) — zusätzlich Architectural-Kriterium F7 (neuer Config-Contract + Schema, Berührung von 6 Basis-Templates und 7 Overrides)
related-spec: SPEC-RELEASE-CHECKLIST-2026-10-31
quellen: .tmp/recon-env-2.md (Datei:Zeile-Belege), .tmp/recon-env.md (Kurzfassung), .tmp/spec-builder-check.md (Builder-Check, eingearbeitet in rev 1.1); hier stichprobenartig verifiziert, siehe §15
---

# Test-Umgebungen — Spec

> Status: APPROVED (2026-10-31, Freigabe durch Nutzer). Der Approval-Marker `Status: APPROVED` wird
> ausschließlich vom Nutzer bzw. `concept-reviewer` gesetzt, nie vom Autor. Diese Datei enthält
> Interface-Contracts und Akzeptanzkriterien, keine Implementierung und keinen Plan.
> Trace-Anker: `spec-id: SPEC-TEST-ENVIRONMENTS-2026-10-31`.
>
> Reihenfolge: 1 = Release-Checkliste (`docs/specs/2026-10-31-release-checklist-spec.md`), **2 = diese Spec**.
> Verweise auf Spec 1 nur in §13.
>
> Markierung: **[Nutzer]** / **Entscheidung des Nutzers** = Entscheidung des Nutzers. **[Call des Autors]** = Vorschlag,
> begründet, im Review zu bestätigen/verwerfen (Sammelliste §21). **Call des Autors (Builder-Check)** = Minor-Entscheidung
> aus `.tmp/spec-builder-check.md` (Stapel b), vom Autor übernommen.

## Änderungshistorie

| Revision | Datum | Änderung |
|---|---|---|
| 1.0 | 2026-10-31 | Erstentwurf. |
| 1.1 | 2026-10-31 | Builder-Check eingearbeitet: Entscheidungen des Nutzers C-3 (Permissions-Erzeugung aus dem MVP gestrichen, Folge-Option F6), C-4 (`token-env` verweist auf `environments:`-Eintrag mit `secret: true`, mcp.py-Erweiterung entfällt), C-5 (Freigabeprotokoll `APPROVAL_REQUEST`/`APPROVED`); Minor-Calls b12-b15, b17-b22; Korrekturen a1-a5, a7, a10, a12-a14, a16, a17; alle 7 Overrides; Folge-Optionen, Aufwand und Review-Hinweise aktualisiert. IDs der entfallenen Elemente (CA7, CA11, IC-9, IC-12, AC-ENV-11, WP3, WP5) bleiben als „ENTFALLEN" stehen. Status bleibt DRAFT. |
| 1.2 | 2026-10-31 | OF-9 als Call des Autors festgeschrieben (CA12: kein `default` für Secret-Einträge in `environments:`, Validator warnt, NZ3); OF-9 entfernt; OF-4 und OF-8 als „für den Implementierer" gekennzeichnet. Status bleibt DRAFT. |
| 1.2 | 2026-10-31 | rev 1.2 — Status APPROVED (Freigabe durch Nutzer, 2026-10-31) |

## 1. Intent / Why

Agenten wissen heute nicht, **wo** getestet werden darf. Beispiele: Eine Home-Assistant-Integration soll erst
nach lokaler Entwicklung auf einem HA-Dev-Server erprobt werden; ein Sharkord-Plugin läuft lokal im Docker-Compose-Stack.
Die vorhandenen Bausteine sind verstreut:

- `{{TEST_COMMANDS}}` (`agents/1-generic/tester.md:48`, `e2e-tester.md:53`, `test-executor.md:29/37`, `documenter.md:65`),
- hacs `dev_instance_url` (`platform-configs/hacs.defaults.yaml:55`, Default `""`; genutzt in `agents/2-platform/hacs-developer.md:31` und `rules/2-platform/hacs-integration-development.md:15`),
- HA `ha_url` (`platform-configs/homeassistant.defaults.yaml:48`, **nicht-leerer Default** `http://homeassistant.local:8123`; laut Recon in keinem Template referenziert),
- `{{DEV_STACK_START}}` nur in `docker.md:84`.

Es gibt keine projektweite, schema-validierte Deklaration von Test-Umgebungen und kein Freigabemodell für Remote-Zugriffe
(`ssh`/`scp`/`curl`/`docker -H` werden von `hooks/1-generic/orchestrator-guard-impl.sh` nicht erkannt).

Ziel: Pro Projekt einstellbar, ob lokale oder globale/remote Testumgebung (oder beide) genutzt werden soll/kann;
das Framework propagiert die Information an die relevanten Agenten; Remote-Zugriff ist pro Umgebung einstellbar.

## 2. Ziele

- Z1: Neuer optionaler Top-Level-Block `test-environments` in `project.yaml` **[Nutzer: Konfiguration pro Projekt; Block-Form = Call des Autors CA1]**.
- Z2: Pro Umgebung `kind: local|remote|both` **[Nutzer]**.
- Z3: Verbindungsoptionen in `project.yaml` oder Secrets **[Nutzer]**; Secrets nur als Env-Var-NAME, der auf einen `environments:`-Eintrag mit `secret: true` verweist (U10, C-4).
- Z4: Pro Umgebung `remote-access: deny|ask|allow` (Default `ask`) und `access: read|deploy` **[Nutzer]**.
- Z5: Propagation an die Agenten (tester, e2e-tester, developer, docker, devops-engineer, test-executor) via Platzhalter-Block.
- Z6: `agent-meta-manager` richtet Umgebungen ein **[Nutzer]**.
- Z7: Admin-UI bietet dieselben Settings, **ohne Secret-Werteingabe** **[Nutzer]**.
- Z8: Unkonfiguriert ⇒ generierte Templates **byte-identisch**.
- Z9: Einheitliches Freigabeprotokoll (`APPROVAL_REQUEST`/`APPROVED`) vor dem ersten Remote-Zugriff **[Entscheidung des Nutzers, C-5]**.

## 3. Nicht-Ziele

- NZ1: Keine Hooks im MVP (Convention boundary, umgehbar; `branch-guard.md` Lücke 4) **[Nutzer-/Auftragsvorgabe]**.
- NZ2: Keine Änderung der bestehenden `environments:`-Definition (`scripts/lib/env.py`) — `test-environments` **referenziert** `environments:`-Einträge nur (U10), siehe §5 Namensverwechslung.
- NZ3: Keine Secret-Werte in `project.yaml`, generierten Dateien oder der Admin-UI.
- NZ4: Kein Provisioning/Start von Umgebungen (kein Docker/SSH-Wrapper), nur Deklaration + Agenten-Konvention.
- NZ5: Kein Editor für `.claude/platform-config.yaml` in der Admin-UI.
- NZ6: Keine Änderung am `test-repo`-Konzept von agent-meta (`scripts/lib/cli_commands.py:121`, Selbsttest-Ziel).
- NZ7: Kein Zusammenspiel-Code mit dem Release-Agenten (nur Verweis, §13).
- NZ8: **Keine Erzeugung von `permissions.ask/deny`-Einträgen** (settings.json o. ä.) im MVP; nur Prompt-Konvention im Block **[Entscheidung des Nutzers, C-3]**. Folge-Option F6.
- NZ9: Keine Erweiterung von `_required_secrets_by_server` (`scripts/lib/mcp.py:196`) und keine Änderung an `secrets.local.yaml` **[Entscheidung des Nutzers, C-4]**.

## 4. Anti-Ziele (Misserfolg trotz Funktion)

- AZ1: Ein Projekt ohne `test-environments`-Block bekommt irgendeine Byte-Änderung in generierten Dateien.
- AZ2: Ein Token oder Passwort landet in `project.yaml`, einem generierten Agenten, einer Provider-Config oder im Chat/Log (Secret-Leck); der Agent liest einen Token-Wert aus einer Datei in seinen Kontext.
- AZ3: `remote-access: deny` wird als technische Sperre verstanden. Es ist Prompt-Konvention, keine Security boundary; Doku darf nichts anderes suggerieren.
- AZ4: Ein Agent greift auf eine Remote-Umgebung zu bzw. deployt, ohne Freigabe, obwohl `ask`/`deny` gilt, weil der Block fehlt oder missverständlich formuliert ist; oder der Worker kontaktiert die Umgebung, bevor er mit `APPROVAL_REQUEST` zurückgekehrt ist.
- AZ5: Patch-Anker in den Developer-/Tester-/DevOps-Overrides brechen oder werden verschoben.
- AZ6: Verwechslung `environments:` (Env-Var-Definitionen) vs. `test-environments:` führt zu falscher Konfiguration.
- AZ7: Provider-spezifischer Code (`if provider == ...`).
- AZ8: YAML-1.1-Bool-Falle: Werte wie `deny: off` / `allow: on` werden als Bool geladen und still falsch interpretiert.

## 5. Constraints

- C1: Stdlib only; Python >= 3.9.
- C2: Provider-Agnostik: Provider-Unterschiede nur über Config-Keys/Capability-Flags (`config/provider-capabilities.yaml`), nie `if provider == "Name"`.
- C3: Unkonfiguriert ⇒ Templates byte-identisch (Migration-Invariante; Mechanik siehe IC-10: `{{#if TEST_ENVIRONMENTS_SET}}\n…{{/if}}\n` entfernt inaktive Blöcke samt Zeilenumbruch, `variables.py:483`).
- C4: **Neues** lib-Modul `scripts/lib/test_environments.py` <= 600 Zeilen. `config.py` hat 2466 Zeilen (`variables.py` 796, `hooks.py` 712, `standalone.py` 537, `mcp.py` 515): Logik nur im neuen Modul; bestehende Module bekommen nur Aufrufzeilen/Registrierungseinträge.
- C5: Neuer Platzhalter `{{TEST_ENVIRONMENT_BLOCK}}` (+ Flag `TEST_ENVIRONMENTS_SET`) nur mit Registrierung nach Regel `rules/2-platform/agent-meta-conventions.md:105-109`: `_SET`-Muster in `scripts/lib/config.py:1442` bzw. `_build_convention_variables` (`config.py:2293`), Eintrag in `scripts/lib/consistency/placeholders.py` (:34/:263), Fallback in `scripts/lib/standalone.py` (`_CONDITIONAL_FALSE_FLAGS`, Block `""`), Doku in `docs/guides/features/sync-concept.md` (Tabelle „Auto-injiziert", ~:280). Eine Variablentabelle in `CLAUDE.md` existiert nicht. Das Suffix `_SET` ist in der Whitelist von `strip_inactive_conditional_blocks` (`variables.py:431-450`) bereits abgedeckt.
- C6: YAML-1.1-Falle: **Jeder Bool in einem Enum-Feld** (`kind`, `access`, `remote-access`) ist ein harter Fehler „quote the value"; keine implizite Abbildung (z. B. `off`→`False`) **[Call des Autors (Builder-Check) b13]**.
- C7: Sprache: Spec/Doku Deutsch; Code/Identifier/Commits Englisch.
- C8: Die JSON-Schema-Validierung warnt nur und läuft nur mit installiertem `jsonschema` (`config.py:388-434`). **Harte Fehler stehen im Python-Validator** (`validate_test_environments`); das Schema ist Zusatz (Autocomplete/Warnung). Auch unbekannte Keys sind im Validator hart (einheitlich mit Spec 1) **[Call des Autors (Builder-Check) b18]**.
- C9: Kein Top-Level-`default` im Schema für `test-environments` (würde von `--fill-defaults` in `project.yaml` geschrieben, `config.py:1060-1069`, Issue #1074); verschachtelte Defaults im Schema sind reine Dokumentation.
- **Namensverwechslung (Pflicht-Doku):** `environments:` = Definitionen von Umgebungsvariablen (`scripts/lib/env.py`: `description/default/required/secret`, erzeugt `env.sh`/`env.ps1`). `test-environments:` = Ziele, auf denen getestet/deployt werden darf. Beide koexistieren; `test-environments.<name>.token-env` **referenziert** einen `environments:`-Eintrag. Doku, Schema-Descriptions, Manager und UI verweisen gegenseitig.

## 6. Ansätze

### A (gewählt): Neuer Top-Level-Block `test-environments` + eigenes Render-Modul

Schema-validierbar, Admin-UI-fähig, plattformunabhängig; Rendering über Platzhalter-Block (Muster `{{RELEASE_CUSTOM_CHECKLIST_BLOCK}}`/`{{WORKER_ROLE_BLOCK}}`); Secrets nur als Verweis auf `environments:`-Einträge mit `secret: true`; Freigabe als Prompt-Konvention mit Stopp-und-Re-Dispatch-Protokoll.

### B (verworfen): `platform-config` erweitern (`platform.<name>.*` / `.claude/platform-config.yaml`)

Verworfen: `platform-config` hat **kein Schema** (nur Laufzeit-Warnungen, `scripts/lib/platform.py` ~:105-160), ist **plattformgebunden** (HA/HACS/Sharkord; generische Templates in `1-generic` nutzen `{{platform.*}}` nicht) und hat keinen Admin-UI-Editor. Typ, Enum und Pflichtfelder wären nicht prüfbar; Projekte ohne diese Plattformen könnten es nicht nutzen. Die Plattform-Keys bleiben als **Fallback-URL** unter engen Bedingungen erhalten (CA4).

### C (verworfen): Durchsetzung per Hook/Gate-Skript oder generierten Permissions

Verworfen: widerspricht der **Nutzerentscheidung**, Freigabe als Prompt-Konvention zu führen (U8, U12). Ein Hook wäre nur **Convention boundary** und umgehbar (`$(...)`, `eval`, `xargs`; `.claude/rules/branch-guard.md`, Lücke 4); `orchestrator-guard-impl.sh` erkennt `ssh/scp/curl/docker -H` bewusst nicht. Permissions-Erzeugung: siehe F6 (Hindernisse dokumentiert). Folge-Optionen in §16.

## 7. Entscheidungen

### 7.1 Entscheidungen des Nutzers (aus dem Auftrag)

| ID | Entscheidung |
|---|---|
| U1 | Pro Projekt einstellbar, ob lokale oder globale/remote Testumgebung (oder beides) genutzt werden soll/kann. |
| U2 | Beispiele: Home-Assistant-Dev-Server (Integrationen erst nach lokaler Entwicklung dorthin) und Sharkord. |
| U3 | Das Framework propagiert die Info an die Agenten. |
| U4 | Verbindungsoptionen in `project.yaml` oder Secrets. |
| U5 | Remote-Zugriff pro Umgebung einstellbar: `remote-access: deny\|ask\|allow` (Default `ask`); `access: read\|deploy`. |
| U6 | `agent-meta-manager` richtet ein. |
| U7 | Admin-UI mit denselben Settings; keine Secret-Werteingabe in der UI. |
| U8 | Hooks im MVP nicht; Freigabe = Prompt-Konvention. |
| U9 | Manager-§3-Bestätigungstabelle: Remote-Aktivierung = Behavior-Change. |

### 7.2 Entscheidungen des Nutzers (aus dem Builder-Check, rev 1.1)

| ID | Entscheidung des Nutzers | Auswirkung (Abschnitte/ACs) |
|---|---|---|
| U10 (C-4) | `token-env` MUSS auf einen Eintrag in `environments:` mit `secret: true` verweisen. Der Wert kommt per `source .meta-config/env.sh` (`scripts/lib/env.py:79-131`, maskiert). Die Erweiterung von `_required_secrets_by_server` (`mcp.py:196`) ENTFÄLLT. Validierung: Existenz und `secret: true` des referenzierten Eintrags (hart). NZ2/CA2 bleibt konsistent (nur Referenz, keine Änderung an `env.py`). Doku: Namensverwechslung `environments` vs. `test-environments`. | NZ2, NZ9, §9, §10.3, IC-2, IC-9 (entfällt), AC-ENV-5, AC-ENV-6, AC-ENV-17, WP3 (entfällt) |
| U11 (C-5) | Einheitliches Freigabeprotokoll: Der Worker stoppt VOR dem ersten Remote-Zugriff und liefert `STATUS: partial` + `APPROVAL_REQUEST: <Aktion/IDs>`; der Orchestrator holt das Okay beim Nutzer (`main_chat`) und dispatcht neu mit `APPROVED: <Aktion/IDs>` im Auftrag; die Freigabe gilt nur für die genannte Aktion. | Z9, AZ4, §10.1, §10.4, AC-ENV-8, AC-ENV-20 |
| U12 (C-3) | `permissions.ask/deny`-Erzeugung (CA7/CA11) wird aus dem MVP GESTRICHEN; nur Prompt-Konvention im Block. Als Folge-Option F6 dokumentiert (Hindernisse: §16). | NZ8, CA7/CA11 (entfallen), IC-12 (entfällt), AC-ENV-11 (entfällt), WP5 (entfällt), F6 |

## 8. Calls des Autors (begründet; siehe §21)

### 8.1 Calls des Autors (Erstentwurf, ggf. angepasst)

| ID | Call | Begründung |
|---|---|---|
| CA1 | Block `test-environments: {<name>: {kind: local\|remote\|both, url, token-env, access, remote-access, notes}}`. | Deckt U1-U5 vollständig; Mapping name→Objekt analog `environments`, dadurch UI-Muster `viewProjectEnvironments` wiederverwendbar. |
| CA2 | `environments:` bleibt unverändert; `token-env` ist nur eine **Referenz** darauf; Namensverwechslung wird dokumentiert (§5). | Kein Breaking Change; nutzt den vorhandenen Secret-Mechanismus (U10). |
| CA3 | Secrets nur als Env-Var-NAME (`token-env`) mit Verweis auf `environments:`-Eintrag (`secret: true`); Wert per `source .meta-config/env.sh`; keine Erweiterung von `mcp.py`/`secrets.local.yaml` (U10). | Nutzt `env.py` (Maskierung); kleinerer Diff als der Erstentwurf. |
| CA4 | Plattform-Defaults als Fallback-URL **nur unter den Bedingungen von §10.2** (genau eine remote/both-Umgebung ohne `url`, Plattformwert vom Projekt gesetzt, nicht der Default; Präzedenz `hacs.dev_instance_url` > `homeassistant.ha_url`) — siehe b15. | `ha_url` hat einen nicht-leeren Default (`homeassistant.defaults.yaml:48`); ohne Einschränkung entstünde ein falsches Ziel. |
| CA5 | Neues Modul `scripts/lib/test_environments.py` rendert `{{TEST_ENVIRONMENT_BLOCK}}` (leer bei unkonfiguriert), **ohne Rollen-Parameter** (b12). | C4; keine Variablen pro Rolle im Sync (`agent_sync.py:712-719`). |
| CA6 | Block-Platzierung in tester, e2e-tester, developer, docker, devops-engineer, test-executor **direkt nach `</constraints>`** (und vor `{{OUTPUT_GUARD_BLOCK}}`, soweit vorhanden), **nicht** innerhalb gepatchter Texte; `based-on` in allen 7 Overrides nachziehen. | Schutz der Patch-Anker (AZ5); §15 Korrektur. |
| CA7 | **ENTFALLEN** (Entscheidung des Nutzers U12/C-3): optionale `permissions.ask/deny`-Erzeugung über neues Capability-Flag. Ersatz: Prompt-Konvention im Block; Folge-Option F6. | — |
| CA8 | `remote-access`-Semantik: `deny` = Remote nie nutzen; `ask` = Stopp + `APPROVAL_REQUEST` vor jedem Remote-Zugriff (U11); `allow` = erlaubt im Rahmen von `access`. `access: read` = nur lesen/abfragen; `deploy` = auch ausrollen. `both` = erst lokal. | Klare, orthogonale Achsen. |
| CA9 | Remote-Aktivierung (`kind: remote\|both`, `remote-access: allow`, `access: deploy`) im Manager = Behavior-Change ⇒ Bestätigung. | U9 konkretisiert. |
| CA10 | Defaults `kind: local`, `access: read` (konservativ), `remote-access: ask` **[Nutzer]**. | Sicherheits-konservativ; Default ask ist Nutzervorgabe. |
| CA11 | **ENTFALLEN** (U12/C-3): Permission-Einträge bei `ask`/`deny`-Umgebungen. Grund: globale Muster sperren auch lokale Aufrufe, kein Capability-Flag, Rollback nötig — siehe F6. | — |
| CA12 | **Kein `default` für Secret-Einträge in `environments:`** (ehem. OF-9): Ein von `token-env` referenzierter Eintrag (`secret: true`) trägt in `project.yaml` keinen `default`; der Validator warnt bei nicht-leerem `default` (NZ3, §9.4 Regel 3). Der Wert kommt ausschließlich aus der Shell-Umgebung bzw. per `source .meta-config/env.sh` (meldet „not set", wenn die Variable fehlt; `env.py:79-131`). | `env.sh` liefert den Wert nur aus `default` oder der bereits gesetzten Shell-Umgebung; ein Secret-Default in `project.yaml` würde NZ3 verletzen. |

### 8.2 Call des Autors (Builder-Check) — Minor-Entscheidungen

| ID | Call des Autors (Builder-Check) | Betrifft |
|---|---|---|
| b12 | Parameter `role` gestrichen; `render_test_environment_block(resolved)`. Die rollenspezifische Zeile steht statisch im jeweiligen Template innerhalb `{{#if TEST_ENVIRONMENTS_SET}}`. | IC-4, IC-10, §10.5 |
| b13 | Bool in einem Enum-Feld = harter Fehler „quote the value"; keine implizite Abbildung. | C6, §9.4, AC-ENV-2 |
| b14 | Alle Umgebungen werden gerendert; es gibt keine Default-Auswahl. Ist das Ziel unklar, fragt der Agent über `APPROVAL_REQUEST` (Rückfrage an `main_chat`). | §10.1, §10.4 |
| b15 | Fallback-URL nur, wenn **genau eine** remote/both-Umgebung ohne `url` existiert und der Plattformwert **vom Projekt gesetzt** (nicht der Default) ist; Präzedenz `hacs.dev_instance_url` > `homeassistant.ha_url`. | CA4, §10.2, IC-3, AC-ENV-4 |
| b17 | Alle 7 Overrides nachziehen (`based-on`/Version); `sharkord-docker` (Standalone) bekommt den Block manuell. AC-ENV-1/10 erweitert. Liste per Grep nach `based-on:`/`extends:` in `agents/2-platform` verifiziert. | IC-11, AC-ENV-1, AC-ENV-10 |
| b18 | Unbekannte Keys sind im Validator hart (Schema-Warnung nur Zusatz); einheitlich mit Spec 1. | C8, §9.4 |
| b19 | `access: deploy` bei `kind: local` ist wirkungslos + Warnung. | §9.4, §10.1 |
| b20 | `test-executor`: Block direkt nach `</constraints>` (Z.125), kein `OUTPUT_GUARD_BLOCK`-Bezug; nur lesende Zusatzzeile (OF-6). | IC-10, CA6 |
| b21 | Ein Satz in `docs/RELEASE_GATES.md` (wird in Spec 1 ohnehin angepasst) deckt AC-ENV-19. | AC-ENV-19, §18.1 |
| b22 | `agent-meta-manager` 1.26.0 gehört Spec 1; diese Spec bumpt auf **1.27.0** (Reihenfolge Spec 1 → 2, R8). | IC-13 |

## 9. Konfig-Schema

### 9.1 YAML-Beispiel (`.meta-config/project.yaml`)

```yaml
environments:                          # bestehender Block (env.py), hier nur als Ziel der Referenz
  HA_DEV_TOKEN:
    description: "Long-lived access token of the HA dev server"
    secret: true                       # Pflicht, wenn von test-environments.token-env referenziert

test-environments:
  ha-dev:
    kind: both                         # local | remote | both    (Default: local)
    url: "http://ha-dev.lan:8123"      # optional; Fallback nur unter den Bedingungen von §10.2
    token-env: HA_DEV_TOKEN            # NUR der NAME; MUSS ein environments-Eintrag mit secret: true sein
    access: deploy                     # read | deploy            (Default: read)
    remote-access: ask                 # deny | ask | allow       (Default: ask)
    notes: "Integration erst nach lokalem Test auf den Dev-Server deployen."
  sharkord-local:
    kind: local
    notes: "Docker-Compose-Stack: docker compose run --rm test"
```

### 9.2 JSON-Schema-Skizze

Das Schema ist Zusatz (C8); harte Prüfung inkl. Referenz auf `environments` im Python-Validator. Kein Top-Level-`default` (C9).

```json
"test-environments": {
  "type": "object",
  "description": "Test/dev targets per project. NOT to be confused with 'environments' (env-var definitions); token-env must reference an 'environments' entry with secret: true.",
  "propertyNames": { "pattern": "^[a-z0-9][a-z0-9-]*$" },
  "additionalProperties": {
    "type": "object",
    "properties": {
      "kind": { "type": "string", "enum": ["local", "remote", "both"], "description": "Quote the value. Default: local." },
      "url": { "type": "string", "minLength": 1 },
      "token-env": { "type": "string", "pattern": "^[A-Z][A-Z0-9_]*$", "description": "Name of an 'environments' entry with secret: true. Never a value." },
      "access": { "type": "string", "enum": ["read", "deploy"], "description": "Default: read." },
      "remote-access": { "type": "string", "enum": ["deny", "ask", "allow"], "description": "Default: ask." },
      "notes": { "type": "string" }
    },
    "additionalProperties": false
  }
}
```

### 9.3 Defaults (Resolver-Ebene, nicht in project.yaml geschrieben)

| Key | Default | Bemerkung |
|---|---|---|
| `test-environments` (fehlt) | `{}` | Block leer ⇒ byte-identisch |
| `kind` | `local` | |
| `access` | `read` | CA10 |
| `remote-access` | `ask` | **[Nutzer]** |
| `url` | — | Fallback nur unter §10.2 |
| `token-env` | — | optional; wenn gesetzt, Referenz auf `environments`-Eintrag (`secret: true`) |
| `notes` | — | freier Text, wird gerendert (keine Secrets!) |

### 9.4 Validierung (Python-Validator im Config-Load, hart)

1. Name der Umgebung passt zu `^[a-z0-9][a-z0-9-]*$`; **unbekannte Keys ⇒ Fehler** (b18).
2. Enum-Felder (`kind`, `access`, `remote-access`) nur gültige Strings; **jeder Bool ⇒ Fehler „quote the value"** (b13).
3. `token-env` passt zu `^[A-Z][A-Z0-9_]*$` (nur Name, nie ein Wert; sonst Fehler „expected env var NAME, not a value") **und** verweist auf einen existierenden Eintrag in `config["environments"]` mit `secret: true`; sonst Fehler (Existenz und `secret: true`, hart; U10). Hat der referenzierte Eintrag einen nicht-leeren `default`, ⇒ Warnung (Secret-Wert in `project.yaml`, widerspricht NZ3; CA12).
4. `kind: local` mit `url` ⇒ Warnung (kein Fehler).
5. `kind: local` mit explizit gesetztem `remote-access` ⇒ Warnung (wirkungslos); `kind: local` mit `access: deploy` ⇒ Warnung (wirkungslos; b19).
6. `url` darf keine Userinfo (`user:pass@`) enthalten ⇒ Fehler (Secret-Leck-Schutz).
7. `access: deploy` + `remote-access: deny` ⇒ Warnung; `deny` gewinnt.

Der Validator hat zwei Einstiege: hart abbrechend für den Config-Load und eine nicht-exitende Variante (`collect_test_environment_errors`, Rückgabe: Fehlerliste), die der Admin-Server-Section-Guard wiederverwendet (IC-2, IC-15b).

## 10. Verhalten / Semantik

### 10.1 Zustandsregeln

| `kind` | Verhalten der Agenten laut Block |
|---|---|
| `local` | Nur lokale Tests/Dev-Stack; kein Remote-Zugriff. |
| `remote` | Nur die Remote-Umgebung ist Testziel; Zugriff nur gemäß `remote-access`/`access`. |
| `both` | Reihenfolge: **erst lokal** testen/entwickeln, danach Remote gemäß Freigabe (entspricht Nutzerbeispiel HA-Dev-Server). |

Bei mehreren Umgebungen werden **alle** gerendert; der Block wählt keine Standardumgebung (b14). Ist das Ziel unklar, liefert der Agent `STATUS: partial` + `APPROVAL_REQUEST: target?` (Rückfrage an `main_chat`).

| `remote-access` | Wirkung |
|---|---|
| `deny` | Agenten dürfen die Remote-Umgebung nicht kontaktieren; Fund ⇒ Hinweis an `main_chat`. |
| `ask` (Default) | **Freigabeprotokoll (U11):** Der Worker stoppt VOR dem ersten Remote-Zugriff (ssh/scp/curl/`docker -H`/Deploy etc.) und liefert `STATUS: partial` + `APPROVAL_REQUEST: env=<name>; action=<read\|deploy: Aktion>`. Der Orchestrator holt das Okay beim Nutzer (`main_chat`) und dispatcht neu mit `APPROVED: env=<name>; action=<…>` im Auftrag. Die Freigabe gilt **nur** für die genannte Umgebung und Aktion; jede weitere Aktion erzeugt eine neue `APPROVAL_REQUEST`. Freigabe im Report vermerken. |
| `allow` | Zugriff im Rahmen von `access` erlaubt; Deploy trotzdem mit Report. |

| `access` | Wirkung |
|---|---|
| `read` | Nur lesen/abfragen (z. B. Status, Logs, Config-Check). Kein Schreiben/Deployen. |
| `deploy` | Zusätzlich ausrollen/ändern erlaubt (nur in Kombination mit `remote-access` ∈ {ask, allow}); bei `kind: local` wirkungslos (Warnung, b19). |

Kombinationsregel: `access: deploy` + `remote-access: deny` ist widersprüchlich ⇒ `deny` gewinnt, Config-Load-Warnung.

### 10.2 Auflösungsreihenfolge Verbindungsdaten

1. `test-environments.<name>.url`.
2. **Fallback aus der Plattform-Konfiguration, nur wenn alle Bedingungen gelten (b15):** (a) genau **eine** Umgebung mit `kind` ∈ {remote, both} hat keine `url`; (b) der Plattformwert ist **vom Projekt gesetzt** (Projekt-Layer von `platform-config`, nicht der gemergte Default — `homeassistant.ha_url` hat den nicht-leeren Default `http://homeassistant.local:8123`, `hacs.dev_instance_url` den Default `""`); (c) Präzedenz bei mehreren gesetzten Plattformwerten: `platform.hacs.dev_instance_url` > `platform.homeassistant.ha_url`.
3. Sonst: Block nennt „URL nicht konfiguriert"; der Agent fragt `main_chat` (über `APPROVAL_REQUEST`, §10.1).

### 10.3 Secrets (U10)

- Der Block nennt ausschließlich `token-env: NAME` und den Hinweis „Wert aus der Shell-Umgebung (`${NAME}`); Bereitstellung per `source .meta-config/env.sh` (aus dem `environments:`-Eintrag `NAME`, `secret: true`, maskiert)".
- `token-env` verweist auf einen `environments:`-Eintrag mit `secret: true` (Validator, §9.4 Regel 3). Das Modul ändert `env.py`, `mcp.py` und `.meta-config/secrets.local.yaml` **nicht** (NZ2, NZ9).
- Agenten dürfen den Token-Wert weder ausgeben noch loggen noch in Dateien schreiben, und lesen ihn nicht aus Dateien in den Kontext; Nutzung nur über `${NAME}` in der Shell.
- Auto-Commit-Rollen: Secret-Scan (`scripts/lib/auto_commit.py`, `hooks/1-generic/lib/hook_common.sh`) bleibt unverändert maßgeblich; URLs sind nicht geheim.

### 10.4 Block-Inhalt (`{{TEST_ENVIRONMENT_BLOCK}}`)

Markdown-Abschnitt „Test environments": Tabelle (Name | kind | URL/Quelle | access | remote-access | notes) für **alle** Umgebungen (b14); Regeln aus §10.1 in Prosa inkl. Freigabeprotokoll (Stopp vor erstem Remote-Zugriff, `STATUS: partial` + `APPROVAL_REQUEST: env=…; action=…`, Re-Dispatch `APPROVED: …`, Freigabe nur für die genannte Aktion; ergänzt das Return-Feld `APPROVAL_REQUEST` zum Output-Contract des Agenten); Satz „Zugriffsfreigabe ist eine Prompt-Konvention (Convention boundary), keine technische Sperre"; Secret-Hinweis (§10.3). Der Block enthält **keine** rollenspezifische Logik (b12).

### 10.5 Rollenspezifische Zeilen (statisch im Template)

Jedes der 6 Basis-Templates enthält direkt hinter `{{TEST_ENVIRONMENT_BLOCK}}` (innerhalb `{{#if TEST_ENVIRONMENTS_SET}}`) eine statische Zeile: tester/e2e-tester: Tests lokal vor remote; developer: erst lokal entwickeln/testen; docker/devops-engineer: Deploy nur bei `access: deploy` und Freigabe; test-executor: nur lesende Zusatzzeile, kein Deploy-Satz (OF-6, b20).

## 11. Interface Contracts

| # | Datei:Symbol | Signatur / Vertrag | Fehlerpfade |
|---|---|---|---|
| IC-1 | `config/project-config.schema.json` → `properties."test-environments"` | Schema §9.2 (Zusatz; kein Top-Level-`default`) | Warnung (nur mit `jsonschema`) |
| IC-2 | `scripts/lib/test_environments.py` → `validate_test_environments(config: dict, config_path: Path) -> None` (hart; Aufruf aus dem Config-Load in `scripts/lib/config.py`, neben `_validate_subagent_permissions` :396) und `collect_test_environment_errors(config: dict) -> list[str]` (nicht-exitend, Basis beider) | Regeln §9.4 inkl. Referenz auf `config["environments"]` (Existenz, `secret: true`) | harter Fehler/Exit nur in `validate_test_environments` |
| IC-3 | `scripts/lib/test_environments.py` → `resolve_test_environments(config: dict, platform_project_vars: dict) -> dict[str, dict]` | liefert je Umgebung alle Felder mit Defaults und aufgelöster URL (§10.2; `platform_project_vars` enthält nur vom Projekt gesetzte Plattformwerte, nicht die Defaults); nie Exception/Exit (kaputt ⇒ `{}` + `log.warning`) | — |
| IC-4 | `scripts/lib/test_environments.py` → `render_test_environment_block(resolved: dict) -> str` (**ohne `role`**, b12) | Leerer String bei `{}`; sonst Block §10.4 | — |
| IC-5 | `scripts/lib/config.py` → Registrierungszeilen (keine neue Logik): `TEST_ENVIRONMENT_BLOCK`, `TEST_ENVIRONMENTS_SET` über das `_SET`-Muster (`config.py:1442`) / `_build_convention_variables` (`config.py:2293`), Regel `agent-meta-conventions.md:105-109` | C5 | — |
| IC-6 | `scripts/lib/consistency/placeholders.py` | Platzhalter bekannt machen (analog :34/:263) | Consistency-Fehler sonst |
| IC-7 | `scripts/lib/standalone.py` → `_CONDITIONAL_FALSE_FLAGS` (:122ff, Kommentar :110-121; Muster :138) | `TEST_ENVIRONMENTS_SET` mit `"false"`; Fallback von `TEST_ENVIRONMENT_BLOCK` = `""` | — |
| IC-8 | `docs/guides/features/sync-concept.md` (Tabelle „Auto-injiziert", ~:280) | Zeilen `TEST_ENVIRONMENT_BLOCK`, `TEST_ENVIRONMENTS_SET` (korrigiert: es gibt keine CLAUDE.md-Variablentabelle; Doku-Beispiele mit `{{TEST_ENVIRONMENT_BLOCK}}` escapen, Berührung Issue #1082) | — |
| IC-9 | **ENTFALLEN** (U10/C-4): `scripts/lib/mcp.py` → `_required_secrets_by_server` wird **nicht** erweitert; `mcp.py` bleibt unverändert. | — | — |
| IC-10 | `agents/1-generic/{tester,e2e-tester,developer,docker,devops-engineer,test-executor}.md` | Je Template direkt nach `</constraints>` (und vor `{{OUTPUT_GUARD_BLOCK}}`, soweit vorhanden; `test-executor` ohne `OUTPUT_GUARD_BLOCK`, Z.125): `{{#if TEST_ENVIRONMENTS_SET}}\n{{TEST_ENVIRONMENT_BLOCK}}\n<statische Rollenzeile>\n{{/if}}\n` (inaktiver Block wird samt Zeilenumbruch entfernt, `variables.py:483`; Baseline-Leerzeilen beachten, `tests/test_conventions_migration_invariant.py:99-105`); minor-Bump je Template (aktuell: tester 2.8.0→2.9.0, developer 4.8.1→4.9.0, docker 1.9.1→1.10.0, devops-engineer 1.7.1→1.8.0, e2e-tester 1.6.1→1.7.0, test-executor 1.2.2→1.3.0) | — |
| IC-11 | **Alle 7** Overrides in `agents/2-platform/`: `homeassistant-developer.md` (extends developer, v2.1.2), `sharkord-developer.md` (extends developer, v3.0.2), `hacs-developer.md` (extends developer, v1.3.1), `agent-meta-developer.md` (extends developer, v2.0.2; wird in diesem Repo genutzt), `hacs-tester.md` (extends tester@2.8.0, v1.0.4), `hacs-devops-engineer.md` (extends devops-engineer@1.7.1, v1.0.1), `sharkord-docker.md` (**Standalone** auf docker@1.9.1, v1.2.4) | `based-on` auf die neue Basisversion, `version` patch-Bump. `extends`-Overrides erben den Block (liegt außerhalb der Anker-Tags). `sharkord-docker.md` erbt nicht: Block + statische Rollenzeile **manuell** einfügen (b17) | — |
| IC-12 | **ENTFALLEN** (U12/C-3): `scripts/lib/hooks.py` (:212, nur Init-Fallback des Hook-Syncs) und Capability-Flag in `config/provider-capabilities.yaml`. Keine `permissions.ask/deny`-Erzeugung; `settings.json` bleibt unberührt. Siehe F6. | — | — |
| IC-13 | `agents/1-generic/agent-meta-manager.md` | Neuer Rezeptabschnitt „Test-Umgebungen" (Recon: z. B. §14d/§17), `version` **1.26.0 (Spec 1) → 1.27.0** (b22); §3-Bestätigungstabelle: Remote-Aktivierung = Behavior-Change | — |
| IC-14 | `commands/1-generic/set-test-environment.md` (optional, neu) | Vorlage `set-preset.md` | — |
| IC-15 | `scripts/admin-server.py` → `PROJECT_WRITABLE_SECTIONS` (:233-252) | `"test-environments"` ergänzen; GET-Route optional (`/api/test-environments`) analog `_route_get_environments` (:3801) | nicht gelistet ⇒ HTTP 400 |
| IC-15b | `scripts/admin-server.py` → `_write_project_section` (:5176-5200), neuer Section-Guard (Muster `_validate_project_provider_options`/`_guard_model_block_write`) | Ruft `collect_test_environment_errors` (nicht-exitend; prüft auch die Referenz auf `environments` im geschriebenen bzw. bestehenden Config-Stand) und lehnt ungültige Payloads mit HTTP 400 ab (Section-Writes werden bisher nicht gegen das Schema validiert, `_route_get_schema_project` :3741 liefert das Schema nur per GET) | Fehlerliste ⇒ 400 |
| IC-16 | `docs/ui/admin-ui.html` → `viewProjectTestEnvironments()` | siehe §12 | — |

## 12. Admin-UI

- View `viewProjectTestEnvironments` nach Muster `viewProjectEnvironments` (`docs/ui/admin-ui.html:8632`): Tabelle + Modal; Save über `saveProjectSection("test-environments", …)` (Muster :8700/:8748); Nav-Eintrag nahe Z.1644; `router.register` (Muster :10868); Help-Eintrag (Quelle `/api/help`); `docs/api/admin-ui-reference.md`.
- Felder: Name, `kind`, `url`, `token-env` (nur NAME; Hinweistext „Name eines Eintrags aus ‚Umgebungsvariablen' mit secret=true; Wert kommt per `source .meta-config/env.sh` bzw. aus der Shell — nie hier eintragen"), `access`, `remote-access`, `notes`. Selects für Enum-Felder senden immer Strings.
- **Keine Secret-Werteingabe**: kein Passwort-/Token-Feld; Client validiert `token-env` gegen `^[A-Z][A-Z0-9_]*$`; Server validiert über den neuen Section-Guard (IC-15b, inkl. Referenz-Check auf `environments` mit `secret: true`).
- Aktivieren von `remote`/`both`/`deploy`/`allow` zeigt einen Bestätigungsdialog (Parität zu Manager §3).
- Whitelist: `"test-environments"` in `PROJECT_WRITABLE_SECTIONS`.
- Parität: UI und Manager schreiben dasselbe Feld; Paritätstest wie in Spec 1 (§12 dort).
- UI-Hinweis auf `environments` (Env-Var-Editor, Z.1644) wegen Namensverwechslung, gegenseitig.

## 13. agent-meta-manager und Berührung mit Spec 1 (Release)

- Rezept: (1) Art erfragen (lokal/remote/beides); (2) falls `token-env`: zuerst den `environments:`-Eintrag (`secret: true`, ohne Wert) anlegen/prüfen, dann den Block in `.meta-config/project.yaml` schreiben, nur `token-env: NAME`; (3) Hinweis „Wert in die Shell-Umgebung bzw. über `source .meta-config/env.sh` bereitstellen — niemals im Chat posten"; (4) Sync + `--validate`; (5) Remote-Aktivierung vorher bestätigen lassen (Behavior-Change, §3-Tabelle).
- **Berührungspunkt Spec 1:** Der Release-Agent kann einen Dry-Check (`MODE: check-only`, Spec 1 §10.4) gegen die Dev-Server-Umgebung als **Checklistenpunkt** (`release-checklist.items`, z. B. `check: script`/`agent`, `phase: precondition`) abbilden. Dabei gelten die `test-environments`-Regeln (`remote-access`, `access`, Freigabeprotokoll) unverändert; ein Dry-Check darf nie `access: deploy`-Aktionen ausführen. Mehr Kopplung ist **nicht** Teil dieser Spec (NZ7). Release-Agent (`agents/1-generic/release.md`) ist bewusst **nicht** in der Template-Liste IC-10. Die Doku-Pflicht (ein Satz in `docs/RELEASE_GATES.md`) wird mit Spec 1 geliefert (b21).

## 14. Datenfluss

1. `project.yaml` (`test-environments`, `environments`) → Config-Load → `validate_test_environments` (hart, inkl. Referenz `token-env` → `environments`-Eintrag mit `secret: true`) → `resolve_test_environments` (weich; Fallback-URL nur unter §10.2 aus dem Projekt-Layer der Plattform-Konfiguration, geladen via `platform.py:34`).
2. Resolver → `render_test_environment_block(resolved)` → Platzhalter `{{TEST_ENVIRONMENT_BLOCK}}` je Agent-Template (`agent_sync.py` Substitution), `TEST_ENVIRONMENTS_SET` steuert `{{#if}}`.
3. Secret-Zustellung: `environments:` (`secret: true`) → `env.py` → `.meta-config/env.sh` → Shell-Umgebung des Nutzers; der Block nennt nur den Namen. Kein Pfad über `mcp.py`/`secrets.local.yaml`.
4. Laufzeit: Agent liest den Block; bei `ask` stoppt er vor dem ersten Remote-Zugriff mit `STATUS: partial` + `APPROVAL_REQUEST`; Orchestrator holt die Freigabe bei `main_chat`/Nutzer und dispatcht neu mit `APPROVED: …`; Token nur über `${NAME}`/Umgebung.
5. Persistenz: nur `project.yaml` und generierte Agenten-Dateien (kein `settings.json`, keine Secret-Datei durch dieses Feature).

## 15. Berührungspunkte (Dateien/Funktionen)

V = verifiziert, N = aus Recon übernommen, nicht erneut geprüft.

| Pfad | Symbol / Zeile | Art | Prüfstatus |
|---|---|---|---|
| `config/project-config.schema.json` | neuer Key | ändern | V (Struktur) |
| `scripts/lib/test_environments.py` | neu (<= 600 Zeilen) | neu | — |
| `scripts/lib/config.py` (2466 Zeilen) | Validierungsaufruf (:396-Muster), `_SET`-Muster :1442, `_build_convention_variables` :2293, Schema-Warnung :388-434, fill_defaults :1060-1069 | nur Aufrufe/Registrierung | V |
| `scripts/lib/variables.py` | :431-450 Whitelist (`_SET` abgedeckt), :483 Block-Entfernung | unverändert (Verifikation) | V |
| `scripts/lib/consistency/placeholders.py` | :34, :263 | ändern | V (:263) |
| `scripts/lib/standalone.py` | :110-121, :122ff `_CONDITIONAL_FALSE_FLAGS`, :138 | ändern | V |
| `scripts/lib/env.py` | :20-24 `environments`-Zugriff, :79-131 Bash-Generator, `_mask` | **unverändert** (Referenzziel, U10) | V |
| `scripts/lib/mcp.py` | :196 `_required_secrets_by_server` | **unverändert** (IC-9 entfällt) | V |
| `scripts/lib/hooks.py` / `config/provider-capabilities.yaml` | :212 Init-Fallback | **unverändert** (IC-12 entfällt; F6) | V |
| `platform-configs/hacs.defaults.yaml` | :55 `dev_instance_url: ""` | unverändert (Fallback) | V |
| `platform-configs/homeassistant.defaults.yaml` | :48 `ha_url` (nicht leer) | unverändert (Fallback nur bei Projektwert) | V |
| `scripts/lib/platform.py` | :34 `load_platform_config` | lesen (Projekt-Layer klären, OF-8) | N |
| `agents/1-generic/{tester,e2e-tester,developer,docker,devops-engineer,test-executor}.md` | Block + Version; Einfügestelle nach `</constraints>` (test-executor Z.125) | ändern | V (Platzierung) |
| `agents/2-platform/{homeassistant,sharkord,hacs,agent-meta}-developer.md`, `hacs-tester.md`, `hacs-devops-engineer.md`, `sharkord-docker.md` | `based-on` + Version; `sharkord-docker` Block manuell | nachziehen | V (Grep `based-on:`/`extends:`) |
| `agents/2-platform/hacs-developer.md:31`, `rules/2-platform/hacs-integration-development.md:15` | `dev_instance_url`-Nutzung | ggf. auf Block verweisen | N |
| `agents/1-generic/agent-meta-manager.md` | Rezept + §3 | ändern | N |
| `scripts/admin-server.py` | :233-252 Whitelist, :3801 Route-Muster, :5176-5200 `_write_project_section` | ändern (Whitelist + Section-Guard) | V |
| `docs/ui/admin-ui.html` | :8632 Muster, Nav ~:1644, Router ~:10868 | ändern | N |
| `docs/api/admin-ui-reference.md`, `scripts/lib/consistency/docs.py:47` | Help-Mapping | ändern/prüfen | N |
| `docs/guides/features/sync-concept.md` | :280 Tabelle „Auto-injiziert" | ändern | V |
| `docs/RELEASE_GATES.md` | ein Satz (AC-ENV-19) | ändern (mit Spec 1) | N |
| `tests/scenarios/{registry.md,configs/,asserts/}`, `run.sh`, `tests/test_conventions_migration_invariant.py` | Szenarien / Baseline-Muster | neu / beachten | V (Invariante :99-105) |
| `hooks/1-generic/orchestrator-guard-impl.sh` | erkennt `ssh/scp/curl/docker -H` nicht | unverändert (Begründung NZ1) | V |
| `docs/*`, `CHANGELOG.md`, `howto/configs/project.yaml.example`, `.claude/skills/{conventions,sync-interface,architecture}` | Doku | ändern | N |

Berührungen: Issue #1082 (Placeholder-Check meldet escaped Doku-Beispiele; betrifft neue Doku mit `{{TEST_ENVIRONMENT_BLOCK}}`), Issue #1074 (fill_defaults ⇒ C9).

Change Checklist (`rules/2-platform/agent-meta-conventions.md:111-123`, verifiziert): `1-generic`-Rolle ⇒ Version bumpen; `2-platform` ⇒ `version`/`based-on` aktuell; Schema ⇒ Autocomplete/jsonschema testen; neue Option ⇒ Szenario + `tests/scenarios/run.sh`.

**Korrektur gegenüber Recon:** Recon env-2 §2 sagt, die Patch-Anker in `homeassistant-developer`/`sharkord-developer` „patchen Step 6". Verifiziert: Die Anker sind **Tag-Anker** (`<persona>`, `<workflow>`, `<context>`, `<constraints>`, `<output_contract>`), nicht Step 6 (`agents/2-platform/homeassistant-developer.md:19/47/68/147`, `sharkord-developer.md:19/27/48/81`). Der Block liegt daher außerhalb dieser Tags (CA6).

## 16. Folge-Optionen (nicht MVP)

- F1: Hook-Erkennung von `ssh/scp/rsync/curl/docker -H` (nur Convention boundary, umgehbar).
- F2: Editor für `.claude/platform-config.yaml`-Fallback-URLs in der Admin-UI.
- F3: Schema↔UI-Coverage-Test.
- F4: Mehrere Umgebungen je Rolle filtern (`roles: [...]`; erfordert einen Mechanismus für Variablen pro Rolle, den es im Sync heute nicht gibt, `agent_sync.py:712-719`).
- F5: Automatisches Health-Check-Kommando je Umgebung.
- F6: **Native `permissions.ask/deny`-Einträge** (aus dem MVP gestrichen, U12/C-3). Gefundene Hindernisse, die eine spätere Umsetzung lösen muss:
  - Globale Muster (`Bash(ssh:*)`, `Bash(scp:*)`, `Bash(curl:*)`, `Bash(docker -H:*)`) sperren bei `deny` jedes `curl`/`ssh` im Projekt — auch localhost-Tests, `kind: local` und Umgebungen mit `allow`; bei `ask` erscheint vor jedem `curl` ein Prompt. Eingrenzung nur host-spezifisch möglich (z. B. `Bash(ssh <host>:*)`, `Bash(curl <url>*)`), und besser nur `ask`, nie `deny`.
  - Es gibt kein Capability-Flag für `ask` (`config/provider-capabilities.yaml`, `config/ai-providers.yaml`); vorhanden sind `isolation-mechanism` (`ai-providers.yaml:75` claude-settings-deny, :181 gemini-toml-policy, :277 opencode-permissions, :449 continue-soft-rule) und `read_only_enforcement: permission-map` (`provider-capabilities.yaml:177/403`). Ein neues Flag wäre nötig.
  - Der richtige Ort ist nicht `hooks.py:212` (nur Init-Fallback des Hook-Syncs), sondern die provider-agnostische Permissions-Verwaltung über `isolation-mechanism` in `ai-providers.yaml` und `scripts/lib/isolation.py` (`_sync_claude_isolation`, :372-406, mit Managed-State und Rollback).
  - Rollback ist nötig: Wird die Umgebung später entfernt oder auf `allow` geändert, müssen die erzeugten Einträge verschwinden (Managed-State), und `settings.json` muss bei `allow`-only-Projekten byte-identisch bleiben.
- F7: Hook-/Tool-gestützte Prüfung der Freigabe (`APPROVED:` im Auftrag) — nur Convention boundary, siehe F1.

## 17. Tests

| Bereich | Datei (neu) | Inhalt |
|---|---|---|
| Schema | `tests/test_test_environments_schema.py` | Enum-Werte, Namensmuster, `token-env`-Pattern, `additionalProperties`, kein Top-Level-`default` |
| Validierung/Resolver | `tests/test_test_environments_lib.py` | Defaults, Fallback-URL (nur bei genau einer url-losen remote/both-Umgebung und Projekt-gesetztem Plattformwert; Präzedenz HACS > HA; Default `ha_url` löst keinen Fallback aus), `deny+deploy`-Konflikt, `deploy` bei `local` ⇒ Warnung, Userinfo-in-URL ⇒ Fehler, Bool in Enum-Feld ⇒ Fehler, unbekannte Keys ⇒ Fehler, `token-env` ohne/mit nicht-secret `environments`-Eintrag ⇒ Fehler, Resolver bricht nie ab; nicht-exitende Variante |
| Render | `tests/test_test_environments_render.py` | **byte-identisch bei unkonfiguriert** für alle 6 Basis-Templates + alle 7 Overrides (inkl. Standalone `sharkord-docker`); Block-Inhalt bei konfigurierter Umgebung (alle Umgebungen, Freigabeprotokoll-Texte `APPROVAL_REQUEST`/`APPROVED`, Convention-boundary-Satz); Block liegt nach `</constraints>`; Patch-Anker lösen auf |
| Secrets | `tests/test_test_environments_secrets.py` | Referenz-Validierung gegen `environments` (`secret: true`); Grep-Assert: kein Token-Wert in generierten Dateien; `env.py`/`mcp.py` unverändert (kein neuer Schreibpfad nach `secrets.local.yaml`) |
| Consistency | `tests/test_test_environments_consistency.py` | Platzhalter in `placeholders.py`, `standalone.py`-Fallback, keine ungelösten `{{TEST_ENVIRONMENT_*}}` |
| Admin-UI | `tests/test_admin_ui_test_environments_section.py` (Muster `tests/test_admin_ui_git_section.py`) | Whitelist, Roundtrip, Section-Guard (ungültige Werte, Bool, unbekannter Key, `token-env` ohne `secret`-Eintrag ⇒ 400), kein Secret-Feld/-Wert im Payload, Parität |
| Szenarien | `tests/scenarios/registry.md` + `configs/<id>.project.yaml` + `asserts/<id>.sh` | „test-env-local", „test-env-remote-ask" (HA-Dev-Server), „test-env-unset" (byte-identisch) |

Der frühere Test `tests/test_test_environments_permissions.py` entfällt (U12).

## 18. Doku, Migration, Risiken

### 18.1 Doku
Neues Kapitel in `docs/` (Test-Umgebungen, inkl. Namensabgrenzung zu `environments` und Referenz-Regel für `token-env`; Freigabeprotokoll; Hinweis „kein `permissions`-Mechanismus, siehe F6"), `docs/api/admin-ui-reference.md`, `CHANGELOG.md`, `howto/configs/project.yaml.example`, `docs/guides/features/sync-concept.md`; Hinweis zu Secrets (`environments:` mit `secret: true`, `env.sh`). Ein Satz in `docs/RELEASE_GATES.md` (Dry-Check gegen eine Umgebung nur `access: read`; wird mit Spec 1 geliefert).

### 18.2 Migration / Kompatibilität
Opt-in. Ohne Block unverändert (AC-ENV-1). `hacs: dev_instance_url`/`ha_url` bleiben gültig und werden nur unter §10.2 als Fallback genutzt. `environments:` unberührt (nur gelesen). Keine Datenmigration.

### 18.3 Risiken
- R1: Template-Bumps propagieren in alle Projekte ⇒ byte-identisch bei unkonfiguriert (Pflichttest, 6 + 7 Dateien).
- R2: Schema-Key optional halten.
- R3: Admin-UI darf keine Secret-Werte annehmen (AC-ENV-12).
- R4: Hook-Bypass-Lücken ⇒ Freigabe nur Convention boundary (AZ3); Doku-Pflicht.
- R5: Auto-Commit-Rolle könnte URLs committen (unkritisch), Tokens nie (Secret-Scan).
- R6: Patch-Anker in den Overrides (siehe §15 Korrektur).
- R7: Der Worker kann mitten im Lauf nicht fragen ⇒ Freigabe nur über Stopp + Re-Dispatch (U11); reine Prompt-Konvention, kein technischer Zwang.
- R8: Mehrere parallel geänderte Templates (6 + 7) ⇒ Merge-Konflikte mit Spec 1 (`agent-meta-manager`, Schema); Reihenfolge Spec 1 → Spec 2 einhalten (Manager 1.26.0 → 1.27.0).
- R9: Dateigrößen: `config.py` 2466 Zeilen ⇒ eigenes Modul, nur Aufrufzeilen in Bestandsmodulen.
- R10: Namensverwechslung `environments` vs. `test-environments` bleibt trotz Referenz-Validierung ein Bedienrisiko ⇒ Doku/UI-Hinweise (AC-ENV-17).

## 19. Offene Fragen

- OF-1 (entschieden, a1): Registrierung über `config.py:1442` (`_SET`-Muster) / `:2293` (`_build_convention_variables`).
- OF-2 (entschieden, b17): 7 Overrides, per Grep verifiziert; `sharkord-docker` manuell.
- OF-3 (entfällt, U12): Capability-Flag — siehe F6.
- OF-4 (offen, **für den Implementierer**, keine Nutzerfrage): Exakte Einfügepositionen je Template (nach `</constraints>`, vor `OUTPUT_GUARD_BLOCK`) und ob `docker.md:84` `{{#if DEV_STACK_START_SET}}` zusammengelegt werden soll (Vorgabe: nein, nur ergänzen).
- OF-5 (entschieden, a3): Doku-Stelle `docs/guides/features/sync-concept.md:280`.
- OF-6 (entschieden, b20): `test-executor` erhält nur eine lesende Zusatzzeile.
- OF-7 (entfällt, U10): Early-Returns in `_required_secrets_by_server`.
- OF-8 (offen, **für den Implementierer**, keine Nutzerfrage): Bietet `scripts/lib/platform.py:34` `load_platform_config` den Projekt-Layer getrennt von den Defaults? Falls nicht, Vergleich gegen die `*.defaults.yaml` oder eigener Lesepfad für `.claude/platform-config.yaml`.

## 20. Acceptance Criteria

| ID | Kriterium | Contract |
|---|---|---|
| AC-ENV-1 | Given ein Projekt ohne `test-environments`, When Sync, Then sind alle generierten Agenten (6 Basis-Templates und **alle 7 Overrides** `homeassistant-developer`, `sharkord-developer`, `hacs-developer`, `agent-meta-developer`, `hacs-tester`, `hacs-devops-engineer`, `sharkord-docker`) **byte-identisch** zum Vorstand (abgesehen vom Frontmatter-`version`/`based-on`, sofern generiert); `settings.json` und `.meta-config/secrets.local.yaml` werden nicht berührt. | IC-3,4,10,11 |
| AC-ENV-2 | Given ungültiges `kind`/`access`/`remote-access`, ein **Bool** in einem dieser Felder (Fehler „quote the value") oder ein unbekannter Key, Then bricht der Sync im Python-Validator mit Pfad-Fehlermeldung ab (unabhängig von `jsonschema`). | IC-1,2 |
| AC-ENV-3 | Given `remote-access` nicht gesetzt, Then löst der Resolver `ask` auf; `access` ⇒ `read`; `kind` ⇒ `local`. | IC-3 |
| AC-ENV-4 | Given genau eine `kind: remote\|both`-Umgebung ohne `url` und ein vom Projekt gesetztes `platform.hacs.dev_instance_url` (bzw. `platform.homeassistant.ha_url`), Then nutzt der Block diese URL (Präzedenz HACS > HA); Given mehrere url-lose remote/both-Umgebungen oder nur der Plattform-**Default** (`ha_url`-Default), Then steht „URL nicht konfiguriert" im Block. | IC-3,4 |
| AC-ENV-5 | Given `url` mit Userinfo (`user:pass@host`), `token-env` mit Nicht-Namen-Zeichen, oder `token-env` ohne passenden `environments:`-Eintrag bzw. mit Eintrag ohne `secret: true`, Then Fehler im Validator. | IC-2 |
| AC-ENV-6 | Given `token-env: HA_DEV_TOKEN` mit passendem `environments.HA_DEV_TOKEN` (`secret: true`), When Sync, Then enthält der Block den Namen und den Hinweis „Wert aus der Shell-Umgebung, bereitgestellt per `source .meta-config/env.sh`"; kein generiertes Artefakt enthält einen Token-Wert; `mcp.py`, `env.py` und `.meta-config/secrets.local.yaml` bleiben unverändert. | IC-2,4 |
| AC-ENV-7 | Given konfigurierte Umgebung, Then enthält `tester`, `e2e-tester`, `developer`, `docker`, `devops-engineer`, `test-executor` den Block mit Tabelle aller Umgebungen, Regeln aus §10.1 und dem Satz zur Convention boundary sowie die statische Rollenzeile (innerhalb `{{#if TEST_ENVIRONMENTS_SET}}`). | IC-4,10 |
| AC-ENV-8 | Given `kind: both`, Then verlangt der Block „erst lokal, dann remote nach Freigabe"; Given `remote-access: ask`, Then enthält der Block das Freigabeprotokoll (Stopp vor erstem Remote-Zugriff, `STATUS: partial` + `APPROVAL_REQUEST: <Aktion/IDs>`, Re-Dispatch mit `APPROVED: <Aktion/IDs>`, Freigabe nur für die genannte Aktion; Template-Text-Asserts). | IC-4 |
| AC-ENV-9 | Given `access: deploy` + `remote-access: deny`, Then wirkt `deny`; Config-Load gibt eine Warnung aus; Given `access: deploy` bei `kind: local`, Then Warnung (wirkungslos). | IC-2 |
| AC-ENV-10 | Given alle 7 Overrides mit neuer Basis, Then rendern sie fehlerfrei, alle Patch-Anker lösen auf, `based-on` verweist auf die neue Basisversion, der Block steht außerhalb der Anker-Tags; `sharkord-docker` (Standalone) enthält Block und statische Rollenzeile manuell eingefügt. | IC-11 |
| AC-ENV-11 | **ENTFALLEN** (U12/C-3). Ersatz-Zusicherung: Given beliebige Konfiguration, Then erzeugt das Feature keine `permissions.ask/deny`-Einträge und ändert `settings.json` nicht; im Code existiert kein `if provider ==`. | IC-12 (entfällt) |
| AC-ENV-12 | Given Admin-UI-Sektion, Then existieren View, Nav, `router.register`, Help-ID; kein Eingabefeld akzeptiert einen Secret-Wert; der Section-Guard (`_write_project_section`) lehnt Payloads ab, die den Validator verletzen (HTTP 400, nichts geschrieben); `PROJECT_WRITABLE_SECTIONS` enthält `"test-environments"`. | IC-15,15b,16 |
| AC-ENV-13 | Given Manager, Then enthält `agent-meta-manager.md` das Rezept (Art erfragen, `environments:`-Eintrag mit `secret: true` anlegen, `token-env`-Referenz, Shell-/`env.sh`-Hinweis, Re-Sync) und die §3-Bestätigung für Remote-Aktivierung; Version 1.27.0. | IC-13 |
| AC-ENV-14 | Given gleiche Eingabe über Manager und UI, Then identisches `test-environments`-Fragment (Parität). | IC-13,16 |
| AC-ENV-15 | Given neue Platzhalter, Then eingetragen über `config.py` (`_SET`-Muster/`_build_convention_variables`), `consistency/placeholders.py`, `standalone.py` (`_CONDITIONAL_FALSE_FLAGS`, Fallback `""`) und `docs/guides/features/sync-concept.md`; `python3 scripts/sync.py --validate` ohne ungelöste Platzhalter. | IC-5..8 |
| AC-ENV-16 | Given Szenarien, When `tests/scenarios/run.sh`, Then bestehen `test-env-local`, `test-env-remote-ask`, `test-env-unset`. | §17 |
| AC-ENV-17 | Given Doku, Then ist die Abgrenzung `environments` vs. `test-environments` (inkl. Referenzregel `token-env` → `environments` mit `secret: true`) im Schema-Description, in `docs/` und in Manager/UI dokumentiert. | §5 |
| AC-ENV-18 | Given alle **neuen** Module (`scripts/lib/test_environments.py`), Then <= 600 Zeilen, Python >= 3.9, stdlib only; bestehende Module wachsen nur um Aufruf-/Registrierungs-/Guard-Zeilen. | C1,C4 |
| AC-ENV-19 | Given Dry-Check-Verweis, Then enthält `docs/RELEASE_GATES.md` einen Satz, dass ein Dry-Check gegen eine Umgebung nur `access: read`-Aktionen ausführt (reiner Verweis, kein Code; geliefert mit Spec 1). | §13 |
| AC-ENV-20 | Given `remote-access: ask` in mindestens einer Umgebung, Then nennt der Block das Return-Feld `APPROVAL_REQUEST` und das Auftragsfeld `APPROVED`; Given `deny`, Then verbietet der Block jeden Kontakt und verlangt einen Hinweis an `main_chat`; Given `allow`, Then verlangt der Block Report über Deploys. Die Aussagen sind per Template-Text-Assert prüfbar. | IC-4 |

## 21. Aufwandsschätzung, Task-Schnitt (nur Liste, kein Plan) und Review-Hinweise

| Paket | Inhalt | Größe |
|---|---|---|
| WP1 | Schema + `validate_test_environments`/`collect_test_environment_errors` (inkl. Referenz auf `environments`) + Tests | S |
| WP2 | `test_environments.py` Resolver/Renderer (Freigabeprotokoll-Texte, Fallback-URL-Regeln) + Platzhalter-Registrierung (IC-3..8) + Tests | M |
| WP3 | **ENTFALLEN** (war: Secrets-Erweiterung `mcp.py`; U10) | — |
| WP4 | 6 Basis-Templates + **7 Overrides** (Block, statische Rollenzeile, Versionen, `based-on`, `sharkord-docker` manuell) + Render-/Byte-Tests | M |
| WP5 | **ENTFALLEN** (war: Capability-Flag + Permissions; U12) | — |
| WP6 | `agent-meta-manager` Rezept (+ optional Command) | S |
| WP7 | Admin-UI (View, Whitelist, Help, Tests) | M |
| WP8 | Szenarien, Doku (inkl. RELEASE_GATES-Satz), CHANGELOG, Skills | S |
| WP9 | Neuer Section-Guard in `_write_project_section` (IC-15b) + Tests | S |

Gesamt: **L** (ca. 28-34 Dateien; weniger Logik als rev 1.0 durch entfallene mcp.py-/Permissions-Pakete, mehr Dateien durch 7 statt 3 Overrides). Vorschlag Task-Folge: WP1 → WP2 → WP4 → WP9 → (WP6 ∥ WP7) → WP8. Reihenfolge nach Spec 1 (Konflikte in `agent-meta-manager.md`/Schema vermeiden).

### Review-Hinweise für den Nutzer (Calls des Autors)

- CA1: Blockform `test-environments: {<name>: {kind, url, token-env, access, remote-access, notes}}`.
- CA2/CA3: `token-env` ist nur eine Referenz auf einen `environments:`-Eintrag mit `secret: true` (setzt Ihre Entscheidung C-4 um).
- CA4/b15: Fallback-URL nur bei genau einer url-losen remote/both-Umgebung und Projekt-gesetztem Plattformwert; Präzedenz HACS > HA.
- CA5/b12: Eigenes Modul, kein Rollen-Parameter; Rollenzeile statisch im Template.
- CA6/b17/b20: Block nach `</constraints>`; alle 7 Overrides nachgezogen, `sharkord-docker` manuell, `test-executor` nur lesend.
- CA8: Semantik `deny|ask|allow` × `read|deploy`; `ask` = Stopp + `APPROVAL_REQUEST` (setzt C-5 um); `both` = erst lokal.
- CA9: Remote-Aktivierung im Manager = Behavior-Change (Bestätigung).
- CA10: Defaults `kind: local`, `access: read`, `remote-access: ask`.
- b13/b18: Bool in Enum-Feld und unbekannte Keys sind harte Validator-Fehler.
- b14/b19: Alle Umgebungen rendern, keine Default-Auswahl; `deploy` bei `local` wirkungslos + Warnung.
- b21/b22: Ein Satz in `docs/RELEASE_GATES.md`; Manager-Version 1.27.0.
- CA7/CA11: entfallen (C-3), Folge-Option F6.
- CA12: Kein `default` für Secret-Einträge in `environments:`; der Validator warnt bei einem Default (NZ3). Der Wert kommt aus der Shell-Umgebung bzw. per `source .meta-config/env.sh`.
- Für den Implementierer (keine Nutzerfrage): OF-4 (Einfügepositionen), OF-8 (Projekt-Layer der Plattform-Konfiguration, `platform.py:34`).

---
Trace-Anker: spec-id: SPEC-TEST-ENVIRONMENTS-2026-10-31
