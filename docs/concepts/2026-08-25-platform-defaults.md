# Konzept: Platform-Level Config Defaults für `project.yaml`

> Status: Draft für Review-Stufe. Kein REQ-ID vergeben — Ideation-Phase.

## 1. Problem / Motivation

- `platforms:` in `.meta-config/project.yaml` existiert bereits, steuert heute aber **ausschließlich**, welche `agents/2-platform/<platform>-*.md`-Overrides für Agent-Templates gezogen werden (`config/project-config.schema.json:49-56`). Eine Plattform hat keinerlei Einfluss auf die übrigen `project.yaml`-Werte selbst (`dod-preset`, `conventions-preset`, `rules-preset`, `tier-preset`, `roles:`, `mcp-servers:`, `knowledge-engine:`, ...).
- Real beobachtete Lücke: Ein Plattform-Team (z.B. `hacs`) weiß typischerweise besser als jedes einzelne Projekt, welches DoD-Profil, welche Naming-Convention oder welche Rollen-Auswahl für diese Plattform sinnvoll sind — muss das heute aber in jedem einzelnen Projekt manuell und wiederholt in `project.yaml` eintragen. Es gibt kein Vererbungs-Fundament „Plattform gibt Config-Defaults vor, Projekt kann überschreiben".
- Nutzer-Vorgabe für dieses Konzept: das neue System muss vier Dinge leisten, die es heute für einzelne Config-Keys nicht gibt: **Abgleich** (Vergleich Framework-Default vs. Projekt-Wert), **Overrule** (Projekt gewinnt), **Ignorieren** (bewusstes Pinning, kein weiteres Drift-Signal) und **Wieder-Übernehmen** (Re-Adopt). Zusätzlich: Admin-UI-Unterstützung, `agent-meta-manager`-Kenntnis des Mechanismus, und ein Feedback-Loop, der wiederkehrende Abweichungen als `meta-feedback`-Vorschlag zurückspielt.
- Der Nutzer hat im Brainstorming bereits vier bindende Design-Entscheidungen getroffen (Priorisierung bei Mehrfach-Plattformen, kein-Allowlist-Scope, additives Listen-Merging, dedizierte Config-Datei) — dieses Konzept formalisiert sie technisch, stellt sie nicht erneut zur Diskussion.

## 2. Ist-Zustand (verifiziert)

- **`platforms:`-Schema heute:** `config/project-config.schema.json:49-56` — reines String-Array, Beschreibung ausschließlich auf Agent-Template-Overrides bezogen: *"Active platform layers. Agents in agents/2-platform/<platform>-*.md override the generic agents."* Kein Bezug zu anderen `project.yaml`-Keys.
- **`agents/2-platform/`-Inhalt heute:** reine Prosa-Agent-Overrides (`hacs-code-reviewer.md`, `hacs-developer.md`, `hacs-release.md`, `homeassistant-developer.md`, `sharkord-developer.md`, ...) — extends+patches oder Full-Replacement einzelner Rollen-Templates. Keine strukturierten Config-Daten. Composition-Mechanik: 0/1/2/3-Schichtmodell (`1-generic → 2-platform → 3-project/<rolle>.md → 0-external`), siehe `.claude/skills/architecture/SKILL.md`.
- **Präzedenzfall für Compare/Drift/Backup existiert bereits — auf Datei-Ebene, nicht auf Key-Ebene:** `scripts/lib/context.py`. Mechanik: Sidecar-Hash-Store `.meta-config/context-hashes.json` (`_CONTEXT_HASHES_FILE`), `content_hash()` aus `scripts/lib/io.py`. Bei jedem Sync: `user_modified = stored is None or content_hash(norm_existing) != stored` (`context.py:259`) — weicht der aktuelle Inhalt vom zuletzt generierten Hash ab, gilt er als manuell editiert; `_backup_context_file()` sichert statt still zu überschreiben; `_record_static_hash()` schreibt den neuen Referenz-Hash zurück. **Dies ist die Blaupause für den in diesem Konzept benötigten Key-Level-Sidecar-State** — adaptiert von „ganzer Datei-Abschnitt" auf „einzelner `project.yaml`-Key".
- **Vier bestehende Preset-Systeme, identisches Muster** (Preset-Datei + `<preset>-preset`-Selektor + additiver Override-Block, Precedence Override > Preset-Name > Framework-Default): `rules-preset`/`config/rules-presets.yaml`, `dod-preset`/`config/dod-presets.yaml`, `tier-preset`/`config/tier-presets.yaml`, `conventions-preset`/`config/conventions-presets.yaml` (zuletzt eingeführt in `docs/concepts/2026-08-18-convention-profiles.md`). **Wichtige Abgrenzung:** Platform-Defaults ist **kein fünftes Preset-System auf derselben Ebene**, sondern liegt **darüber** — mit zwei getrennt zu haltenden Aussagen: (a) Platform-Defaults befüllen sowohl die *Selektoren* dieser vier Systeme (z.B. `conventions-preset: calver` als Plattform-Default) **als auch beliebige andere direkte `project.yaml`-Keys** (Scalars wie Listen, z.B. `roles:`, `mcp-servers:`, `knowledge-engine:` — siehe Entscheidung 2, Abschnitt 3C) — das ist die eigentliche Breite des Mechanismus; (b) Platform-Defaults greifen **nie** in die interne feldweise Preset-Definition ein, d.h. nie in die `dod:`/`conventions:`-Override-Blöcke, die einzelne Felder INNERHALB eines bereits gewählten Presets überschreiben — nur diese zweite Einschränkung (b) begründet, dass keine 5-stufige Precedence entsteht (siehe Abschnitt 9).
- **Zwei getrennte Feedback-Kanäle:** `agents/1-generic/feedback.md` (v2.0.0) — Issues **im Projekt-Repo** (bug/feat/improvement/docs/security/question). `meta-feedback` — separater Agent für Kritik/Vorschläge **am Framework selbst** (agent-meta-Repo). „Dieser Platform-Default passt nicht, Framework sollte ihn überdenken" gehört fachlich zu `meta-feedback`.
- **`agent-meta-manager.md` HITL-Muster:** bereits zweimal für ähnliche reversible Toggle-Mechanismen etabliert — `model-override-all` (Abschnitt „8b.1") und `model-inherit-main-chat` (Abschnitt „8b.2"). Beide folgen demselben Aufbau: Mechanismus-Erklärung, YAML-Beispiel, nummerierter Toggle-Workflow, Admin-UI-Verweis. Neue Platform-Defaults-Abschnitte sollen sich strukturell an dieses Muster anlehnen — Grundsatz aus `agent-meta-manager.md`: *"Never change configuration without explaining tradeoffs"*.
- **Admin-UI-Präzedenz (3-Teile-Muster), 3x bereits umgesetzt (DoD/Rules/Conventions):**
  1. Super-Admin-Raw-Editor: `SUPER_ADMIN_FILES`-Dict (`scripts/admin-server.py:153-164`) — enthält bereits `"dod-presets"`, `"rules-presets"`, `"conventions-presets"` als Key→Pfad-Mapping, generischer `/api/config/<key>`-Handler (`resolve_path()`, `write()`).
  2. Projekt-Override-Seite: eigene Route pro System (`/project/dod-overrides`, `/project/rules-overrides`, `/project/conventions-overrides`, Router-Registrierung `admin-ui.html:9541-9543`), Funktionen `viewProjectDodOverrides()` (~3657), `viewProjectRulesOverrides()` (~3768), `viewProjectConventionsOverrides()` (~4082) — Dropdown + Vergleichstabelle, `saveProjectSection()`.
  3. Dropdown im kombinierten Projekt-Panel (~5594-5850).
  **Aber:** die neue Seite braucht **keinen** klassischen Preset-Override-Editor (Override läuft ja bereits über die vier bestehenden Override-Seiten + Roles-Seite + rohe `project.yaml`-Felder) — sie braucht eine **Compare/Resolve-Ansicht**: Tabelle `Key | Platform-Default | Aktiver Wert | Status-Badge | Aktionen`. Konzeptionell näher an einem Diff-Resolver als an einem Preset-Editor.

## 3. Architektur-Entscheidungen (Nutzer-verbindlich, hier technisch spezifiziert)

### A) Datenmodell — `config/platform-defaults.yaml`

**Entscheidung (Nutzer-Vorgabe 4):** eigene, dedizierte Datei nach dem etablierten Preset-Datei-Muster — nicht in `agents/2-platform/<platform>-*.md` eingebettet.

**Begründung:** Konsistenz mit den vier bereits etablierten Preset-Dateien (`rules-presets.yaml`, `dod-presets.yaml`, `tier-presets.yaml`, `conventions-presets.yaml`) — gleiches Muster, gleiche Auffindbarkeit (`SUPER_ADMIN_FILES`), keine Vermischung von Prosa-Agent-Templates (die vom Sync-Zeit-Composer als Markdown zusammengesetzt werden) und strukturierten Default-Daten (die vom Config-Resolver als YAML gelesen werden). Zwei völlig unterschiedliche Konsumenten (`sync_agents()` vs. `resolve_config()`) sollten keine gemeinsame Datei teilen.

```yaml
# config/platform-defaults.yaml
# Platform-Defaults — Default-Werte für project.yaml-Keys je Plattform.
# Aktiviert via 'platforms:' in .meta-config/project.yaml (bereits bestehender Key).
#
# WICHTIG: Dies ist KEIN fünftes Preset-System — es befüllt die SELEKTOREN
# der bestehenden vier Preset-Systeme (dod-preset, rules-preset, tier-preset,
# conventions-preset) sowie beliebige andere project.yaml-Keys, greift aber
# nie in deren interne Preset-Definitionen ein.
#
# Precedence Scalar-Keys:  Projekt-expliziter-Wert > Platform-Default > Framework-Hardcoded-Default.
# Precedence List-Keys:    additiv gemerged — alle Plattform-Listen ∪ Projekt-Liste (siehe Abschnitt 3C).
#   Bei mehreren aktiven Plattformen: Scalar-Konflikte werden über die Reihenfolge
#   in 'platforms:' aufgelöst (letzter Eintrag gewinnt, siehe Abschnitt 3B) — Listen
#   brauchen keine Priorisierung, da sie ohnehin vereinigt statt ersetzt werden.

platforms:

  hacs:
    defaults:
      # --- Scalar-Keys: klassische Precedence, kein Merge. ---
      dod-preset: standard
      conventions-preset: default
      rules-preset: minimal
      tier-preset: Advanced

      # --- List-Keys: additiv gemerged (Deduplizierung), siehe Abschnitt 3C. ---
      roles:
        - developer
        - code-reviewer
        - release
      mcp-servers:
        - homeassistant
```

Ein Projekt mit `platforms: [hacs]` erhält automatisch `dod-preset: standard`, `rules-preset: minimal`, `tier-preset: Advanced`, `conventions-preset: default` — diese Scalar-Defaults wirken bereits, wenn das Projekt selbst noch keinen eigenen Wert für diesen Key gesetzt hat (klassische Precedence, kein Merge-Guard nötig, unabhängig davon ob die Projekt-Config sonst leer oder befüllt ist). Bei den beiden List-Keys aus dem Beispiel ist zu unterscheiden:

(a) **Projekt hat gar kein `roles:` gesetzt** (Key fehlt = `None`-Sentinel = „alle Rollen aktiv", siehe `scripts/lib/delegation_table.py:16-17`): Der Platform-Default für `roles:` ist dann ein **No-Op** — es bleibt bei „alle Rollen aktiv", die Plattform-Rollen `developer`/`code-reviewer`/`release` werden **nicht** als explizite (kleinere) Allowlist materialisiert (siehe No-Op-Guard, Abschnitt 3C). Der MCP-Server-Default (`homeassistant`) greift davon unabhängig auch dann, wenn das Projekt noch kein `mcp-servers:` führt — für `mcp-servers:` gibt es kein „fehlt = alle"-Sentinel-Muster, ein fehlender Key wird hier einfach als leere Liste behandelt und additiv befüllt.

(b) **Projekt führt bereits eine eigene, auch andere, `roles:`-Liste** (z.B. `roles: [tester]`): Die Plattform-Rollen `developer`, `code-reviewer`, `release` werden additiv ergänzt — Ergebnis: `[tester, developer, code-reviewer, release]` (dedupliziert).

### B) Priorisierung bei mehreren aktiven Plattformen (Nutzer-Entscheidung 1)

**Entscheidung:** Array-Reihenfolge in `platforms: [a, b]` **ist** die Priorität. Bei Scalar-Konflikten zwischen mehreren Plattform-Defaults für denselben Key gewinnt der **letzte** Eintrag im Array.

```yaml
platforms: [base-tooling, hacs]   # hacs gewinnt bei Scalar-Konflikten
```

**Begründung:**
- **Konsistenz mit der bereits etablierten Layer-Direction des eigenen Composition-Modells:** Das 0/1/2/3-Schichtmodell (`1-generic → 2-platform → 3-project → 0-external`) definiert bereits die Regel „später/spezifischer in der Kette = gewinnt". `2-platform` überschreibt `1-generic`. Würde man mehrere `platforms:`-Einträge nach derselben Logik behandeln, ist die naheliegende, widerspruchsfreie Fortsetzung: die zuletzt genannte Plattform ist die „spezifischere" Schicht und gewinnt — keine neue mentale Regel, sondern dieselbe Regel eine Ebene höher angewendet.
- **Analogie CSS-Cascade / spätere Deklaration gewinnt:** Nutzer, die mehrere Plattformen kombinieren, tendieren dazu, allgemeine/Basis-Plattformen zuerst zu listen und die für dieses Projekt tatsächlich entscheidende Plattform zuletzt — „später deklariert = bewusster, spezifischerer Override" ist eine verbreitete, gut verständliche Konvention (analog `git merge`, CSS, YAML-Anchor-Overrides).
- **Alternative (erster gewinnt) verworfen:** würde bedeuten, dass Nutzer die „wichtigste" Plattform an den Anfang stellen müssten — das kollidiert mit der intuitiven Lesart „ich aktiviere zuerst Basis-Tooling, dann projektspezifisch(er) hacs" und mit der bereits etablierten Schicht-Direction.
- Listen-Keys brauchen laut Nutzer-Entscheidung 3 keine Priorisierung — sie werden ohnehin vereinigt (siehe C). Die Priorisierung aus B betrifft **ausschließlich** Scalar-Konflikte zwischen mehreren Plattform-Defaults, nie den Merge mit dem Projekt-Wert selbst (der bleibt immer aus Sicht des Projekts das letzte Wort, unabhängig von der Plattform-internen Priorität).

### C) Merge-Semantik: Scalar vs. Listen-Keys (Nutzer-Entscheidungen 2 + 3)

**Scope (Entscheidung 2):** **Alle** `project.yaml`-Keys sind platform-defaultable — explizit inklusive `conventions-preset`/`conventions:` und aller anderen Keys (`dod-preset`, `rules-preset`, `tier-preset`, `roles:`, `mcp-servers:`, `knowledge-engine:`, etc.). **Keine kuratierte Allowlist.** Der Resolver behandelt jeden Key strukturell — nicht nach einer Positivliste „diese Keys dürfen, jene nicht".

**Merge-Regel (Entscheidung 3):**

| Key-Typ | Erkennungsmerkmal | Merge-Verhalten |
|---|---|---|
| Scalar (string/bool/int/enum) | Wert im Schema kein Array | Klassische Precedence: Projekt-Wert (falls explizit gesetzt) > Platform-Default (nach Priorität aus B) > Framework-Hardcoded-Default |
| Liste (`roles:`, `mcp-servers:`, `ai-providers:`, ggf. weitere) | Wert im Schema ein Array | Additive Union: alle Plattform-Listen werden **zuerst untereinander** vereinigt (Deduplizierung, keine Priorität nötig — siehe B), das Ergebnis wird dann additiv mit der Projekt-eigenen Liste vereinigt (erneut dedupliziert) — **Ausnahme: `roles:`, siehe No-Op-Guard unten** |

**No-Op-Guard für Fehlt-heißt-alle-Sentinel-Keys (`roles:`):** Für `roles:` gilt eine strukturelle Ausnahme von der additiven Merge-Regel oben. Nach `scripts/lib/delegation_table.py:16-17` gilt heute: `roles:` fehlt in `project.yaml` (`None`) ⇒ **alle** Rollen aktiv; `roles:` gesetzt (auch als leere Liste `[]`) ⇒ harte Schnittmenge auf die gelistete(n) Rolle(n). Ein wörtlich umgesetzter additiver Merge würde bei fehlendem `roles:` den `None`-Sentinel in eine explizite (kleinere!) Liste umwandeln — das widerspricht dem additiven Grundprinzip und würde das aktive Rollen-Set **verkleinern** statt zu erweitern. Geprüft wurde, ob weitere `project.yaml`-Keys dasselbe „fehlt = alles"-Fallback-Muster haben (`config/project-config.schema.json`, alle Array-Keys durchsucht): **`roles:` ist aktuell der einzige Key mit diesem Muster.** `mcp-servers:` z.B. hat ein strukturell anderes Default-Verhalten (Aktivierung pro Server über `enabled-by-default` in der Registry, kein „fehlt = alle" auf Key-Ebene) und braucht daher keinen Guard.

Für `roles:` gilt konkret:

- Projekt führt **kein** `roles:` (Key fehlt, `None`-Sentinel) ⇒ Merge wird **komplett übersprungen**, der `None`-Sentinel bleibt erhalten. Der Platform-Default für `roles:` ist dann wirkungslos (No-Op) — die implizite Alle-Rollen-Menge umfasst die Plattform-Rollen ohnehin bereits vollständig.
- Projekt führt bereits eine **explizite** `roles:`-Liste (auch `roles: []`, siehe Edge-Case unten) ⇒ der additive Merge aus der Tabelle oben greift regulär.

> **Merksatz:** Platform-`roles`-Defaults (und strukturell äquivalente Fehlt-heißt-alle-Keys, aktuell ausschließlich `roles:`) wirken **nur**, wenn das Projekt bereits eine eigene, explizite Liste für diesen Key führt — sonst nie. Diese Einschränkung ist bewusst und kontraintuitiv: sie verhindert, dass ein additiver Mechanismus versehentlich das aktive Rollen-Set verkleinert.

**Edge-Case `roles: []` (explizit leer, nicht fehlend):** `delegation_table.py` behandelt `roles: []` als eigenen Sentinel-Zustand — „null Rollen aktiv", strukturell verschieden von „fehlend" (`active_roles = set(roles_list) if roles_list is not None else None`; `roles_list = []` ergibt ein leeres, aber nicht-`None`-Set, das den harten-Schnittmenge-Pfad auslöst). **Entscheidung:** `roles: []` gilt als „Projekt führt eine explizite (wenn auch leere) Liste" und nimmt regulär am additiven Merge teil — Platform-Rollen werden hineingemergt, `roles: []` bleibt nach dem Merge nicht mehr leer. **Begründung:** Konsistenz mit der einfachen, einheitlichen Guard-Regel „nur der `None`-Fall ist No-Op, jede tatsächliche Liste (auch leer) nimmt am Merge teil" — eine zweite Sonderbehandlung nur für `[]` würde die Guard-Logik um einen weiteren Sentinel-Fall erweitern, obwohl `delegation_table.py` `None` und `[]` bereits sauber unterscheidet. Wer bewusst „null Rollen, explizit auch keine Plattform-Rollen" will, nutzt künftig `--platform-defaults-ignore roles` (macht die Divergenz explizit und pinnt sie, siehe Abschnitt 4).

**Zwei-Stufen-Merge bei mehreren Plattformen + Listen-Key, konkret:**

```
if project.yaml.roles is None:
    final_list = None   # No-Op-Guard: Fehlt-heißt-alle-Sentinel bleibt erhalten
else:
    merged_platform_list = dedupe(platform_a.defaults.roles + platform_b.defaults.roles + ...)
    final_list            = dedupe(merged_platform_list + project.yaml.roles)
```

Kein Gewinner-Konzept für Listen — Priorisierung (B) betrifft ausschließlich Scalars.

**Erkennung Scalar vs. Liste:** rein strukturell aus `config/project-config.schema.json` ableitbar (Key-Typ `array` vs. andere Typen) — kein separates Klassifikations-Feld in `platform-defaults.yaml` nötig. Ein neuer Resolver-Helper (`scripts/lib/platform_defaults.py::_is_list_key(key: str) -> bool`) schlägt im Schema nach; unbekannte/Custom-Keys ohne Schema-Eintrag (z.B. unter `variables:`) werden konservativ als Scalar behandelt (kein Merge-Risiko durch Fehlklassifikation).

## 4. Sidecar-State: Compare / Ignorieren / Re-Adopt

**Entscheidung:** neue Datei `.meta-config/platform-defaults-state.json`, strukturell direkt vom `context-hashes.json`-Muster (`scripts/lib/context.py`) abgeleitet, aber auf Key- statt Datei-Granularität.

```json
{
  "version": 1,
  "keys": {
    "dod-preset": {
      "status": "inherited",
      "source_platform": "hacs",
      "last_platform_value": "standard",
      "last_platform_value_hash": "sha256:3a7f...",
      "last_synced": "2026-08-25T10:00:00Z"
    },
    "conventions-preset": {
      "status": "overridden",
      "source_platform": "hacs",
      "last_platform_value": "calver",
      "last_platform_value_hash": "sha256:9e21...",
      "project_value": "default",
      "last_synced": "2026-08-25T10:00:00Z"
    },
    "rules-preset": {
      "status": "ignored",
      "source_platform": "hacs",
      "last_platform_value": "minimal",
      "last_platform_value_hash": "sha256:c410...",
      "project_value": "default",
      "ignored_at": "2026-08-20T09:12:00Z",
      "last_synced": "2026-08-25T10:00:00Z"
    },
    "tier-preset": {
      "status": "ignored",
      "source_platform": "hacs",
      "last_platform_value": "Advanced",
      "last_platform_value_hash": "sha256:7bd2...",
      "project_value": "Advanced",
      "ignored_at": "2026-08-22T14:30:00Z",
      "last_synced": "2026-08-25T10:00:00Z"
    }
  }
}
```

Die vier Beispiele zeigen bewusst beide `ignored`-Pfade: `dod-preset` = `inherited` (folgt dem Platform-Default live), `conventions-preset` = `overridden` (Projekt hatte bereits einen abweichenden Wert), `rules-preset` = `ignored` **aus `overridden` gepinnt** (`project_value` „default" wich zum Ignore-Zeitpunkt bereits vom Platform-Default „minimal" ab, User pinnt die bestehende Divergenz), `tier-preset` = `ignored` **aus `inherited` gepinnt** (`project_value` „Advanced" entspricht exakt `last_platform_value` zum Ignore-Zeitpunkt — das Projekt folgte dem Default, User friert den damals aktuellen Wert ein; dabei wurde `project_value` durch `--platform-defaults-ignore` explizit in `project.yaml` materialisiert, siehe Abschnitt 5).

**Status-Semantik (drei Zustände):**

- **`inherited`** — Key ist in `project.yaml` nicht explizit gesetzt (oder explizit gesetzt mit exakt demselben Wert wie der aktuelle Platform-Default). Wert kommt live vom Platform-Default; ändert sich der Default zwischen zwei Sync-Läufen, übernimmt das Projekt ihn automatisch (das ist der Sinn von „inherited"). Sync gibt trotzdem eine **Info-Zeile** aus, wenn sich `last_platform_value` gegenüber dem gespeicherten Stand ändert (Transparenz über eine sonst stille Verhaltensänderung, siehe Abschnitt 5).
- **`overridden`** — Key ist in `project.yaml` explizit gesetzt **und** weicht vom aktuellen Platform-Default ab. Das ist die reguläre „Overrule"-Situation aus der Anforderung — kein Fehler, keine Warnung, nur sichtbarer Drift-Status in Diff/Admin-UI.
- **`ignored`** — Key wurde per `--platform-defaults-ignore <key>` (oder Admin-UI-Button „Ignorieren") bewusst gepinnt. Ab diesem Zeitpunkt erzeugt Sync **keine** weiteren Info-/Drift-Meldungen mehr für diesen Key, unabhängig davon, wie oft sich der Platform-Default künftig noch ändert. `ignored` kann sowohl von `overridden` (Projekt hatte bereits einen abweichenden Wert, User will die Abweichung stillstellen) als auch von `inherited` (Projekt folgte dem Default, User will den *aktuellen* Wert jetzt einfrieren) ausgehen — im zweiten Fall materialisiert `--platform-defaults-ignore` den aktuellen Platform-Default-Wert **explizit** in `project.yaml` (sonst gäbe es nichts einzufrieren, der Wert würde ja weiter automatisch mitziehen). **Festlegung zum Refresh-Verhalten:** `last_platform_value`/`last_platform_value_hash` werden zum Zeitpunkt des `ignore`-Aufrufs **eingefroren** und bei künftigen Syncs **nicht** weiter aktualisiert — sie halten fest, gegen welchen Platform-Default-Stand gepinnt wurde, unabhängig davon, wie oft sich der tatsächliche Platform-Default seither ändert. `last_synced` wird davon unabhängig bei jedem Sync-Lauf weiter aktualisiert (reines „zuletzt gesehen"-Zeitstempel des State-Eintrags, kein Drift-Signal).

**Re-Adopt (`--platform-defaults-adopt <key>`):** entfernt den expliziten Key aus `project.yaml` (falls vorhanden) und setzt den State zurück auf `inherited` — das Projekt folgt ab sofort wieder live dem Platform-Default, inklusive aller künftigen Änderungen. Bewusst **nicht** implementiert als „schreibe den aktuellen Platform-Wert explizit rein" (das würde sofort wieder einfrieren, nicht adoptieren) — Adopt bedeutet „gib die Kontrolle an die Plattform zurück", nicht „übernimm einmalig den aktuellen Wert".

**Re-Track (Admin-UI-Button „Re-Track", CLI äquivalent zu erneutem `adopt` bzw. separatem `--platform-defaults-track <key>`):** hebt einen `ignored`-Status auf, ohne den Projekt-Wert zu verändern — Drift-Vergleich wird für diesen Key wieder aktiv (nächster Sync kann wieder `overridden` oder `inherited` melden, je nachdem ob der aktuelle Projekt-Wert zufällig wieder mit dem Platform-Default übereinstimmt). Dabei wird `last_platform_value`/`_hash` auf den aktuellen Platform-Default aktualisiert (Baseline-Reset) — sonst würde der erste Sync nach Re-Track die eingefrorene Ignore-Baseline gegen den inzwischen weitergelaufenen Platform-Default vergleichen und fälschlich eine `inherited`-Änderungs-Info ausgeben, obwohl seit dem Re-Track selbst noch gar keine neue Drift entstanden ist.

## 5. CLI-Oberfläche (`scripts/sync.py`)

| Flag | Verhalten |
|---|---|
| `--platform-defaults-diff` | Read-only. Druckt Tabelle `Key \| Platform-Default (Quelle) \| Projekt-Wert \| Status` für alle Keys, die von mindestens einer aktiven Plattform mit einem Default versorgt werden. Kein Schreibzugriff. |
| `--platform-defaults-adopt <key>` | Entfernt den expliziten Key aus `project.yaml`, Status → `inherited` (siehe Abschnitt 4). |
| `--platform-defaults-ignore <key>` | Materialisiert (falls nötig) den aktuellen Platform-Default-Wert explizit in `project.yaml`, Status → `ignored`. |
| `--platform-defaults-track <key>` | Hebt `ignored` wieder auf (Re-Track), keine Wertänderung. |

**Normaler Sync-Lauf (ohne Flags):** zusätzliche Info-Zeilen im Log für jeden `inherited`-Key, dessen `last_platform_value` sich seit dem letzten Sync geändert hat, z.B.:

```
[INFO] platform-defaults: 'dod-preset' (Plattform 'hacs') geändert: standard → full — automatisch übernommen (inherited, kein Override in project.yaml)
[INFO] platform-defaults: 3 Key(s) weichen von Platform-Defaults ab (overridden). Details: sync.py --platform-defaults-diff
```

Kein Fail/Abort — reine Transparenz, analog zum bestehenden `[WARN] user_modified`-Pfad in `context.py`, aber bewusst als `[INFO]` statt `[WARN]`, weil Overrule ein explizit gewünschtes, legitimes Verhalten ist (kein Fehlerzustand).

## 6. Admin-UI (drei Teile, wie etabliertes Muster)

1. **Super-Admin-Raw-Editor:** `SUPER_ADMIN_FILES`-Dict (`scripts/admin-server.py:153-164`) um `"platform-defaults": "config/platform-defaults.yaml"` erweitern — nutzt den bereits generischen `/api/config/<key>`-Handler (`resolve_path()`/`write()`), keine neue Backend-Logik nötig, exakt wie `dod-presets`/`rules-presets`/`conventions-presets` heute schon eingebunden sind.
2. **Projekt-Compare/Resolve-Seite** (neu, kein Preset-Editor-Klon): Route `/project/platform-defaults`, Router-Registrierung analog `admin-ui.html:9541-9543`, Funktion `viewProjectPlatformDefaults()` analog zu `viewProjectDodOverrides()`/`viewProjectRulesOverrides()`/`viewProjectConventionsOverrides()` im Aufbau, aber inhaltlich ein Diff-Resolver: Tabelle `Key | Platform-Default (mit Quell-Plattform + Priorität falls mehrere) | Aktiver Wert | Status-Badge (inherited/overridden/ignored) | Aktionen (Übernehmen / Ignorieren / Re-Track)`. Braucht **neue, dedizierte Endpunkte** — bewusst **nicht** über den generischen `/api/config/<key>`-Raw-Handler, weil dieser für Ganze-Datei-Overwrite gebaut ist, nicht für semantische Key-Level-Aktionen:
   - `GET /api/platform-defaults/diff` — liefert die o.g. Diff-Tabelle als JSON (liest `config/platform-defaults.yaml` + `.meta-config/project.yaml` + `.meta-config/platform-defaults-state.json`, ruft dieselbe Resolver-Logik wie `sync.py --platform-defaults-diff` auf — ein gemeinsames `scripts/lib/platform_defaults.py`, kein Doppel-Code zwischen CLI und Admin-Server).
   - `POST /api/platform-defaults/adopt {key}`, `POST /api/platform-defaults/ignore {key}`, `POST /api/platform-defaults/track {key}` — dünne Wrapper um dieselben Funktionen wie die CLI-Flags.
3. **Statusanzeige im kombinierten Projekt-Panel** (~5594-5850, wo bereits die vier Preset-Dropdowns sitzen): kleines Badge/Link, z.B. „Platform-Defaults: 3 Keys weichen ab" (Zählung `overridden`, `ignored` nicht mitgezählt — bewusst gepinnt, kein Handlungsbedarf), verlinkt auf Teil 2.

**Schreibziel-Trennung (kein Write-Write-Konflikt):** Der Raw-Editor aus Punkt 1 (generischer `/api/config/<key>`-Handler) schreibt ausschließlich `config/platform-defaults.yaml`; die Resolver-Endpunkte aus Punkt 2 (`adopt`/`ignore`/`track`) schreiben ausschließlich `.meta-config/project.yaml` + `.meta-config/platform-defaults-state.json`. Beide Schreibpfade sind disjunkt — keine Datei wird von beiden Wegen beschrieben. Ein Raw-Edit an `platform-defaults.yaml` über Punkt 1 löst **keine** automatische State-Mutation aus; Konsistenz wird stattdessen dadurch gewahrt, dass `GET /api/platform-defaults/diff` live gegen die aktuelle Datei rechnet (kein gecachter State, der veralten könnte).

## 7. `agent-meta-manager`-Integration + Feedback-Loop

### F) Neuer Workflow-Abschnitt in `agent-meta-manager.md` (Beschreibung, keine Implementierung hier)

Analog zu den bestehenden Abschnitten „8b.1 Model-Override-All" / „8b.2 Model-Inherit-Main-Chat" — neuer Abschnitt „Platform-Defaults":

- **Herkunfts-Erklärung auf Nachfrage:** Fragt der Nutzer „warum ist `dod-preset` auf `standard`?", liest der Agent `config/platform-defaults.yaml` + `.meta-config/platform-defaults-state.json` und erklärt: Quelle (welche Plattform), Priorität (falls mehrere Plattformen aktiv sind und der Key dort mit unterschiedlichen Werten definiert ist), aktueller Status (`inherited`/`overridden`/`ignored`).
- **`--adopt`/`--ignore` nur auf explizite Nutzeranfrage**, mit vorheriger Tradeoff-Erklärung (HITL-Pflicht, wörtlich aus `agent-meta-manager.md`: *"Never change configuration without explaining tradeoffs"*) — z.B. vor `--platform-defaults-adopt dod-preset`: "Das entfernt deinen expliziten `dod-preset`-Wert aus `project.yaml`; du folgst danach automatisch jeder künftigen Änderung, die die Plattform `hacs` an ihrem Default vornimmt. Fortfahren?"
- **Anleitung „neue Plattform mit eigenen Defaults anlegen":** (1) Eintrag unter `platforms.<name>.defaults` in `config/platform-defaults.yaml` ergänzen, (2) Plattform-Namen in `platforms:` (Array) des Zielprojekts ergänzen, (3) `sync.py` erneut laufen lassen, (4) `sync.py --platform-defaults-diff` zur Verifikation, dass die erwarteten Defaults ankommen.

### G) Feedback-Loop (`meta-feedback`)

**Realistische Heuristik (keine Cross-Projekt-Telemetrie, die es im Framework nicht gibt):** `agent-meta-manager` bietet eine `meta-feedback`-Einreichung **proaktiv als Vorschlag** an (nie automatisch), wenn **beide** Bedingungen im selben Gesprächskontext zutreffen:

1. Der Nutzer pinnt einen Key explizit gegen den Platform-Default (`--platform-defaults-ignore` **oder** ein expliziter `overridden`-Wert wird im selben Zug angelegt), **und**
2. der Nutzer äußert im selben Gesprächsverlauf eine wertende/kritische Aussage zum Default selbst (z.B. „der Default passt hier nicht", „das sollte eigentlich X sein", „nervt mich jedes Mal").

Das ist rein konversationell erkennbar (Agent liest den unmittelbaren Chat-Kontext, keine neue Infrastruktur nötig) und bleibt konsistent mit dem HITL-Grundsatz: `agent-meta-manager` **schlägt vor**, reicht aber nie selbstständig ein — der Nutzer bestätigt die `meta-feedback`-Einreichung explizit. Kein Versuch, Häufigkeit über mehrere Projekte hinweg zu tracken (dafür existiert keine zentrale Instanz) — die Heuristik bleibt bewusst auf „ein Signal in einem Gespräch", nicht „N Projekte zeigen dasselbe Muster".

## 8. Migrationspfad

**Invariante:** Kein Projekt ohne aktive Plattform mit Platform-Defaults darf sich durch dieses Feature ändern. Projekte mit `platforms: []` (leer, Default-Zustand vieler Projekte) sind vollständig unberührt — der Resolver findet für sie keinen Eintrag in `config/platform-defaults.yaml` und verhält sich exakt wie heute.

1. `config/platform-defaults.yaml` startet **leer** (`platforms: {}`, keine Einträge für `hacs`, `homeassistant`, `sharkord`, `agent-meta` selbst). Befüllung pro Plattform ist ein bewusster **Folge-Schritt**, kein Teil dieses Konzepts — sonst würde dieses Konzept implizit inhaltliche Entscheidungen treffen (welche Defaults für `hacs` etc. sinnvoll sind), die außerhalb seines Scopes liegen.
2. Rollout-Reihenfolge:
   a. `scripts/lib/platform_defaults.py` (Resolver: Merge-Logik aus Abschnitt 3, Sidecar-State-Verwaltung aus Abschnitt 4) + leere `config/platform-defaults.yaml` einführen, in `build_variables()`/Config-Resolution-Pipeline verdrahten. Mit leerer Datei ist dies bei jedem Projekt ein No-Op (kein Eintrag → keine Defaults → unveränderte bestehende Precedence-Kette).
   b. CLI-Flags (`--platform-defaults-diff`/`-adopt`/`-ignore`/`-track`) + Admin-UI-Integration (Abschnitt 6) ergänzen — wirkungslos ohne befüllte `platform-defaults.yaml`, aber vollständig testbar mit synthetischen Test-Fixtures.
   c. Migrations-Invarianten-Test (analog `tests/test_conventions_migration_invariant.py`, das präzise Variablen wie `variables["RELEASE_VERSIONING_BLOCK"]` gegen eine im Test selbst hinterlegte Baseline-String-Konstante assertet, kein Snapshot-Diff gegen Git-Historie): Resolver-Identität statt Byte-Identität. Konkretes Fixture: Test-Projekt mit `platforms: [hacs]`, `config/platform-defaults.yaml` **ohne** `hacs`-Eintrag (bzw. komplett leer). Assertion: das von `build_variables()` erzeugte `variables`-Dict ist mit und ohne den neuen Resolver-Aufruf identisch — formal `resolve_config(config, empty_platform_defaults) == config`, d.h. der Resolver ist bei leerer/fehlender Platform-Default-Datei ein reines No-Op in der Aufrufkette. Kein Snapshot-Diff gegen den generierten Sync-Output aller Agenten-Dateien nötig — das konkret zu prüfende Artefakt ist das `variables`-Dict aus `build_variables()`, nicht „der Sync-Output" pauschal.
   d. Erst **danach**, als separate Folge-PRs pro Plattform: `config/platform-defaults.yaml` um konkrete Einträge für `hacs`/`homeassistant`/`sharkord` ergänzen — jeweils mit eigenem Minor-Versionsbump und explizitem Vorher/Nachher-Diff-Review gegen betroffene Downstream-Projekte.
3. `project-config.schema.json`: keine neuen Top-Level-Keys nötig (das Feature nutzt den bereits bestehenden `platforms:`-Key als Trigger) — lediglich die Beschreibung von `platforms:` (`project-config.schema.json:51`) um einen Hinweis auf die neue Config-Default-Funktion ergänzen (reine Doku-Präzisierung, kein Breaking Change am Schema selbst).
4. Versionsbump: Minor (rein additives, opt-in Verhalten — kein bestehendes Projekt ändert sich ohne befüllte `platform-defaults.yaml`-Einträge).

## 9. Offene Risiken/Fragen für die Review-Stufe

- **Kollision mit bestehender `roles:`-Allowlist-Semantik:** Heute gilt „`roles:` fehlt in `project.yaml` = ALLE Rollen aktiv, `roles:` gesetzt = harte Schnittmenge" (`scripts/lib/delegation_table.py:16-17`, `roles_list = config.get("roles"); active_roles = set(roles_list) if roles_list is not None else None`). Additives Merging von Platform-Default-Rollen + Projekt-Rollen kollidiert potenziell mit diesem Fallback: Ein additiver Merge, der ein fehlendes `roles:` faktisch in eine explizite (kleinere) Liste umwandeln würde, würde das Rollen-Set **verkleinern** statt zu erweitern — das widerspricht dem additiven Grundprinzip aus Entscheidung 3. **Vorgeschlagene Auflösung (zur Bestätigung in der Requirements-Stufe):** fehlt `roles:` in `project.yaml` (== „alle Rollen aktiv"-Sentinel), ist ein Platform-Default für `roles:` ein No-Op — die implizite Alle-Rollen-Menge umfasst die Plattform-Rollen ohnehin bereits vollständig. Der additive Merge wird erst wirksam, sobald das Projekt selbst (aus anderem Grund) bereits eine explizite `roles:`-Allowlist besitzt. Das ist eine bewusste, dokumentierte Ausnahme von der generellen additiven Merge-Regel — inzwischen direkt im Algorithmus in Abschnitt 3C verankert (No-Op-Guard + Merksatz), muss aber weiterhin vor Requirements-Formalisierung explizit bestätigt werden.
- **Doppelte Precedence-Achse bei Preset-Keys:** Für Preset-Selektor-Keys wie `dod-preset` gibt es künftig eine dreistufige Kette (Projekt-explizit > Platform-Default > Framework-Hardcoded), die **orthogonal** neben der bereits bestehenden `dod:`-Override-Kette (`dod` > `dod-preset` > `default`) steht. Beide Ketten dürfen sich nicht vermischen — das ist Fall (b) aus Abschnitt 2/3 (Platform-Defaults greifen nie in die interne feldweise Preset-Definition ein): Platform-Defaults wirken auf der „welcher Preset-Name wird gewählt"-Ebene (Fall (a): Selektoren UND beliebige andere direkte `project.yaml`-Keys), nie auf der „welches einzelne Feld wird innerhalb eines Presets überschrieben"-Ebene. Dokumentation muss diese (a)/(b)-Unterscheidung explizit klarstellen, um eine gefühlte „5-stufige Precedence" zu vermeiden.
- **Schema-Validierung von `platform-defaults.yaml`:** Was passiert, wenn ein Plattform-Autor versehentlich einen Scalar-Key mit einem Array-Wert befüllt (z.B. `dod-preset: [standard, full]`)? Sollte `_is_list_key()` (Abschnitt 3C) das per Schema-Lookup hart validieren und Sync mit klarer Fehlermeldung abbrechen, statt still einen falschen Merge zu versuchen? Empfehlung: ja, fail-fast — Detailspezifikation für Requirements-Stufe.
- **Test-Impact:** Migrations-Invarianten-Test (siehe Abschnitt 8.2c) nötig; zusätzlich ein Test für die Priorisierungs-Logik (zwei synthetische Plattformen mit widersprüchlichem Scalar-Default, Assertion „letzter Eintrag in `platforms:` gewinnt") und ein Test für additive Listen-Merge inkl. Deduplizierung.
- **Versionsbump-Scope bei Folge-PRs:** Jede Befüllung von `config/platform-defaults.yaml` für eine konkrete Plattform (Schritt 8.2d) verändert generierte Ausgaben für alle Projekte, die diese Plattform bereits aktiv haben — jeweils eigener Minor-Bump plus Downstream-Diff-Review, analog zum in Abschnitt 8 beschriebenen Vorgehen für `release.md`/`git.md` im Convention-Profiles-Konzept.
- **Sidecar-State-Drift bei parallelen Schreibpfaden:** CLI (`sync.py --platform-defaults-*`) und Admin-UI (`/api/platform-defaults/*`) schreiben potenziell dieselbe `.meta-config/platform-defaults-state.json` — beide sollten dieselbe Resolver-Bibliothek (`scripts/lib/platform_defaults.py`) nutzen, um Doppel-Code und inkonsistente Status-Übergänge zu vermeiden (siehe Abschnitt 6, Punkt 2).
- **Feedback-Heuristik ist inhärent unscharf:** Die in Abschnitt 7G vorgeschlagene Heuristik hängt von der Fähigkeit des Agenten ab, „wertende Kritik" im Gesprächsverlauf korrekt zu erkennen — kein deterministischer Trigger, rein beratend/vorschlagend. Akzeptabel im Rahmen des bestehenden HITL-Grundsatzes, aber explizit als weiche, nicht erzwingbare Heuristik zu dokumentieren, damit keine falschen Erwartungen an Zuverlässigkeit entstehen.

## Handoff

Empfohlener nächster Schritt: `requirements` — Kern-Idee, alle vier Nutzer-Design-Entscheidungen sowie Scope v1 (Abschnitte 3-8) sind technisch spezifiziert, keine Blocker-Fragen offen. Alternativ: `concept-reviewer` für eine Review-Schleife vor der Formalisierung, insbesondere wegen der `roles:`-Allowlist-Kollision (Abschnitt 9, erster Punkt) — das ist die einzige Stelle mit echtem Spezifikations-Risiko, alle anderen Punkte in Abschnitt 9 sind Detailfragen für die Requirements-Stufe.
