# Konzept — agent-meta Version-Badge

- **Status:** Draft (entschieden: Q1 Offer statt Force, Q2 tag-spezifisches Linkziel mit
  `/releases`-Fallback für den Unknown-Fall, Q4 kein Code-Health-Badge-Typ für Zielprojekte,
  Q5 generisches `version`-Badge bleibt, Q6 `unknown` wird gerendert, Q7 section-driven ohne
  Marker; offen bleibt nur Q3 als dokumentierte Grenze (Offline-/Private-Repos, §8/§9);
  Ownership B1 entschieden: `documenter` ist einziger Badge-Schreiber, §5.3)
- **Betroffener Bereich:** README-Standard (`readme.badges`), `documenter`-Template,
  `agent-meta-manager`-Template, Config-Schema, agent-meta-README, Tests/Szenarien
- **Umfang:** 1 neuer Badge-Typ `agent-meta`, 1 Schema-Enum-Erweiterung, 1 Render-Regel im
  `documenter`, 1 Manager-Integrationsschritt, 1 README-Umbau des Meta-Repos, Test-Erweiterungen
- **Nicht in diesem Dokument:** Implementierung, Code-Änderungen, Commits, `sync.py`-Läufe,
  Änderungen an `.agent-meta/`-Submodul, `external/` oder `.gitmodules`
- **Terminologie:** „Managed-Block-Prinzip" wird so verwendet wie in
  [`templates/configs/README-template.md`](../../templates/configs/README-template.md) (Kopf-Kommentar)
  und [`../../.opencode/skills/architecture/SKILL.md`](../../.opencode/skills/architecture/SKILL.md)
  definiert: bestehende, handgeschriebene README-Inhalte werden nie überschrieben, nur fehlende
  verwaltete Blöcke ergänzt.

---

## 1. Scope & Kontext

### 1.1 Scope

Ein Zielprojekt (Consumer von agent-meta) soll in seiner `README.md` **optional** ein Badge
anzeigen, das die **verwendete agent-meta-Version** nennt (z. B. `agent-meta v1.1.0`). Die
Badge-Anzeige ist:

- **Opt-in** über `readme.badges` — **kein** Default-on, **kein** erzwungenes Rendering,
- ein **neuer Badge-Typ** `agent-meta` (analog zu den bestehenden Typen `version`, `stack`,
  `license`, `ci`),
- gespeist aus der bereits existierenden Variable `AGENT_META_VERSION`
  (`scripts/lib/config.py:1187`, Wert aus `VERSION` via `read_version`,
  `scripts/lib/config.py:1042-1046`; zur Sync-Zeit in generierte Dateien eingebettet),
- **allein gerendert vom `documenter`** aus `README_BADGES` — der `documenter` ist der
  **einzige Schreiber** der Badges-Zeile (Single Source of Truth, §4/§5.3),
- durch den `agent-meta-manager` **nur indirekt** gepflegt: er stößt bei
  `update-meta`/`upgrade-meta` einen Re-Sync und danach einen Re-Render an; die Wertquelle
  ist der sync-eingebettete `{{AGENT_META_VERSION}}`, durch den vorgeschalteten Re-Sync
  (M2) erfrischt — er schreibt **kein** README-Badge selbst (B1),
- **managed-block-konform**: ein handgeschriebenes README wird nie überschrieben.

Zusätzlich wird das README des Meta-Repos selbst angepasst: Badge-Zeile an den Anfang, neues
RepoWise-Code-Health-Badge, Korrektur des veralteten generischen Versions-Badges (`version-1.1.0`,
D4/Q5) **und** Ergänzung des neuen `agent-meta`-Badges (§6).

### 1.2 Nicht-Scope

- **Kein automatisches/defaultmäßiges Anzeigen** des Badges in Zielprojekten. Ohne expliziten
  Eintrag `agent-meta` in `readme.badges` wird das Badge **nie** gerendert.
- **Keine neue Platzhalter-Variable** — `README_BADGES` existiert bereits
  (`scripts/lib/config.py:1259-1268`, `scripts/lib/consistency/placeholders.py:20`,
  `scripts/lib/standalone.py:71`). Es ist **keine** dritte Registrierungsstelle nötig.
- **Kein Runtime-Netzwerk-Check** durch agent-meta, ob das Badge-Bild oder das Link-Ziel
  (tag-spezifische URL, D1/§2.3) tatsächlich erreichbar ist bzw. ob das verlinkte Tag existiert
  (Offline-/Private-Repos, §9/Q3). Das Restrisiko eines (noch) nicht existierenden Tags wird
  dokumentiert und bewusst akzeptiert (§8).
- **Kein generischer Code-Health-Badge-Typ für Zielprojekte** in v1 (entschieden, D3/§9/Q4).
- Keine Änderung an `.agent-meta/`-Submodul, `external/` oder `.gitmodules`; kein Push/Tag/Release.

> **Geltungsbereich:** Projekte **ohne** `readme`-Block oder **ohne** die `documenter`-Rolle
> erhalten weder Badge noch Re-Render-Trigger — das Konzept greift nur dort, wo der
> README-Standard (`readme.badges` + `documenter`) aktiv ist.

### 1.3 Betroffene Subsysteme

| Subsystem | Rolle im Konzept |
|---|---|
| `config/project-config.schema.json:819-867` (`readme`), Enum `:823-840` | **Validierungsstelle**: `badges.items.enum` um `"agent-meta"` erweitern (Draft7, geprüft via `scripts/lib/config.py:354-366`) |
| `scripts/lib/config.py:1187` | `AGENT_META_VERSION` (Wert-Quelle, unverändert) |
| `scripts/lib/config.py:1259-1268` | `README_BADGES` (unverändert — Default bleibt `["version","stack","license"]`) |
| `agents/1-generic/documenter.md` (§5, Badges-Row `:52-61`, agent-meta-Regel `:56-61`) | **Einziger Badge-Schreiber (B1)**: Render-Regel für den neuen Badge-Typ |
| `templates/configs/README-template.md:17-29` | Badge-Kommentar/Skelett um `agent-meta` ergänzen (inkl. Escaping-Hinweis + Pre-Release-Beispiel) |
| `agents/1-generic/agent-meta-manager.md` §4 `:70-87`, §5 `:89-102` | **Kein README-Schreiber (B1)**: nur Re-Sync (erfrischt den sync-eingebetteten `{{AGENT_META_VERSION}}`, M2) + Re-Render-Trigger |
| `templates/configs/project.yaml.example:76-83` | Badge-Typen-Kommentar (`readme.badges`) um `agent-meta` ergänzen (m1) |
| `README.md:1-38`, `README.md:911-916` (Meta-Repo) | Badge-Zeile an den Anfang, RepoWise-Badge, Stale-Version-Fix + neues `agent-meta`-Badge (D4/Q5); Badge-Config-Beispiel um `agent-meta` ergänzen (m1) |
| `tests/test_readme_variables.py`, `tests/test_documenter_readme_section.py`, `tests/test_readme_schema.py`, `tests/test_readme_template.py`, `tests/test_meta_readme_badges.py` (`test_readme_template.py` und `test_meta_readme_badges.py` wurden in diesem Branch **neu angelegt**, die übrigen erweitert), `tests/scenarios/configs/11-readme-standard.project.yaml`, `tests/scenarios/registry.md:58` | Test-/Szenario-Erweiterung (statisch, ohne Netzwerk) |

**Feststellung Validierungsstelle:** Es **existiert** eine Schema-/Validierungsstelle für
`readme.badges`: `config/project-config.schema.json:823-840` (Enum) in Kombination mit der
Draft7-Validierung in `scripts/lib/config.py:354-366`. Die Validierung läuft nur, wenn
`jsonschema` installiert ist; ohne die Dependency wird sie übersprungen
(`scripts/lib/config.py:344-349`). Das Enum ist damit die **verbindliche** Erweiterungsstelle für
einen neuen Badge-Typ.

**Feststellung Meta-Repo-Config (Meta-Repo-Ausnahme, Option B, F8):** Die eigene Config dieses
Repos enthält **keinen** aktiven `readme:`-Block. Das README des Meta-Repos wird also **nicht**
aus Config gerendert, sondern ist handgepflegt — die README-Änderung in §6 ist eine
**manuelle** Dateiänderung, kein Sync-Ergebnis. Das ist eine **bewusste, dokumentierte
Ausnahme** (Option B): agent-meta ist kein normaler Consumer, sondern der Framework-Ursprung,
und hat kein `readme.badges`-Opt-in. Die Badges-Zeile des Meta-README wird daher **manuell**
gepflegt (siehe §6). Der `RepoWise Code health`-Badge ist bewusst **kein** Schema-Typ (D3/Q4)
und bleibt reines Meta-Repo-Markup; für Zielprojekte wird **kein** Code-Health-Badge-Typ
eingeführt. Begründung: RepoWise deckt nur registrierte Repos ab, und die manuelle Pflege
vermeidet einen Config-Zwang im einzigen Repo, das agent-meta selbst nicht als Consumer nutzt.

---

## 2. Badge-Naming & Format

### 2.1 Typname

**Vorschlag:** `agent-meta` (analog zu den bestehenden String-Enum-Werten `version`, `stack`,
`license`, `ci`). Der Name ist identisch mit dem Projektnamen und der bereits etablierten
Variable `AGENT_META_VERSION` / dem Config-Key `agent-meta-version`.

### 2.2 Shields.io-URL-Format

Statischer Shields.io-Endpunkt:
`https://img.shields.io/badge/<LABEL>-<MESSAGE>-<COLOR>.svg`

Escaping-Regeln (shields.io):
- Ein **literaler Bindestrich** in Label oder Message wird als `--` geschrieben.
- Ein **Unterstrich** kodiert ein Leerzeichen (`_` → Space); ein literaler Unterstrich als `__`.
- Punkte (`.`) sind unkritisch.

Für Label `agent-meta` und Message `v1.1.0` gilt daher:
- Label `agent-meta` → `agent--meta`
- Message `v1.1.0` → `v1.1.0` (unverändert)
- Farbe → `blue` (konsistent mit dem bestehenden Versions-Badge,
  `README.md:35`)

**Präfix-/Escaping-Reihenfolge (verbindlich, F4):** `{{AGENT_META_VERSION}}` ist der **blanke**
Versionswert **ohne** `v` (`VERSION` = `1.1.0`, `scripts/lib/config.py:1042-1046`). Das
Escaping wird immer auf diesen blanken Wert angewandt (`-`→`--`), **danach** wird genau **ein**
literales `v` vorangestellt: blank `1.1.0` → `v1.1.0`; blank `1.1.0-beta.6` → escaped
`1.1.0--beta.6` → Message `v1.1.0--beta.6`. Ein `vv`-Präfix ist verboten; der blanke Wert
enthält nie ein `v`.

**Konsequenz für Pre-Release-Versionen (verbindlich, M1):** Die Message wird **vor** dem
URL-Einsatz `-`→`--` gemappt. `1.1.0` bleibt unverändert und wird als `v1.1.0` gerendert;
`0.101.0-beta.6` wird jedoch zu `0.101.0--beta.6` und als Message `v0.101.0--beta.6`.
Ungeescaped liefert Shields.io ein `404: badge not found`-SVG (live verifiziert:
`0.101.0-beta.6` → 404, `0.101.0--beta.6` → korrekt).

### 2.3 Exact example badge line

```markdown
[![agent-meta v1.1.0](https://img.shields.io/badge/agent--meta-v1.1.0-blue.svg)](https://github.com/Popoboxxo/agent-meta/releases/tag/v1.1.0)
```

- **Bild:** `https://img.shields.io/badge/agent--meta-v1.1.0-blue.svg`
- **Link-Ziel (D1/Q2 entschieden, F2):** tagspezifisch
  `https://github.com/Popoboxxo/agent-meta/releases/tag/v<AGENT_META_VERSION>` für echte
  Versionen — das Badge verlinkt direkt das zu seiner Version gehörende Release-Tag. Für den
  **Unknown-Fall** (missing/empty oder Sentinel `"unknown"`/`vunknown`) wird **offiziell** auf
  die immer gültige Releases-Seite `https://github.com/<repo>/releases` zurückgefallen (nie
  `.../releases/tag/vunknown`). Es gibt **keinen** zusätzlichen Netzwerk-Check (Runtime-Check,
  §1.2/Q3); existiert das Tag (noch) nicht, ist das Restrisiko eines toten Links bewusst
  akzeptiert und dokumentiert (§8).

Platzhalter-Form für den `documenter` (Zielprojekt, Wert aus `AGENT_META_VERSION`).
**Der blanke Wert MUSS vor dem Einsetzen in die Bild-URL `-`→`--` gemappt und danach mit genau
einem literalen `v` präfixt werden** — verbindlich auch (und gerade) für Pre-Release-Versionen
(`0.101.0-beta.6` → `0.101.0--beta.6` → `v0.101.0--beta.6`); ungeescaped liefert Shields.io
ein `404: badge not found`-SVG (live verifiziert):

```markdown
[![agent-meta v{{AGENT_META_VERSION}}](https://img.shields.io/badge/agent--meta-v<escaped-version>-blue.svg)](https://github.com/{{AGENT_META_REPO}}/releases/tag/v{{AGENT_META_VERSION}})
```

Unknown-Fall (Message `unknown`, kein `v`-Präfix, `/releases`-Fallback):

```markdown
[![agent-meta unknown](https://img.shields.io/badge/agent--meta-unknown-blue.svg)](https://github.com/{{AGENT_META_REPO}}/releases)
```

> Hinweis: Der generische `{{VERSION}}`-Platzhalter im Badge-Skelett
> (`templates/configs/README-template.md:27`) ist **nicht** `AGENT_META_VERSION`. Laut Kopf-Kommentar
> des Templates (`:1-11`) wird `{{VERSION}}` vom `documenter` selbst aus dem **Zielprojekt**-Manifest
> aufgelöst, während `AGENT_META_VERSION` die eingebettete Framework-Version ist. Beide dürfen nicht
> verwechselt werden.

---

## 3. `readme.badges` — Erweiterung & Validierung

### 3.1 Erlaubte Typen (nach Erweiterung)

`version`, `stack`, `license`, `ci`, **`agent-meta`** (neu).

### 3.2 Änderungsstellen

1. **Schema-Enum** — `config/project-config.schema.json:828-833`:
   `"agent-meta"` ergänzen. Beschreibungstext `:825` um die Semantik erweitern
   („only rendered when `agent-meta` is explicitly opted in via `readme.badges`");
   die Wert-Sentinel `missing | empty | "unknown" | "vunknown"` werden als Message
   `unknown` gerendert (kein `v`-Präfix; `"vunknown"` ist der wörtliche Raw-Wert des
   Sentinels, das `v`-Präfix wird nur bei einer realen Version vorangestellt) — konsistent
   zu §4/Q6.
2. **Default bleibt unverändert** — `config/project-config.schema.json:835-839` und
   `scripts/lib/config.py:1261`: `["version","stack","license"]`. Damit ist der neue Typ
   **nicht** default-on (Opt-in erfüllt).
3. **Template-Kommentar** — `templates/configs/README-template.md:17-29`: `agent-meta` als
   Typ dokumentieren (analog zu `ci` bei `:25`).
4. **Keine** Änderung an `scripts/lib/config.py:1259-1268`, `placeholders.py:20` oder
   `standalone.py:71` — `README_BADGES` bleibt ein kommaseparierter String, der neue Wert
   fließt automatisch mit.

### 3.3 Validierungsverhalten

- Mit installiertem `jsonschema`: unbekannte Badge-Typen (z. B. Tippfehler
  `agentmeta`) werden durch `Draft7Validator` (`scripts/lib/config.py:354-366`) abgelehnt.
- Ohne `jsonschema`: Validierung wird übersprungen (`scripts/lib/config.py:344-349`) — der
  `documenter` darf sich **nicht** auf Schema-Gültigkeit verlassen und prüft den Typ zur
  Laufzeit (§4).

---

## 4. `documenter`-Render-Regel (Ownership B1)

**Änderungsstelle:** `agents/1-generic/documenter.md:52-61` (§5, Punkt 2 „Badges row").

**Ownership (B1):** Der `documenter` ist der **einzige** Schreiber der Badges-Zeile; der
`agent-meta-manager` schreibt **kein** README-Markup (§5.3). Grund: `README_BADGES` ist
bereits die einzige Quelle, und README-Pflege ist die `documenter`-Domäne — zwei Schreiber
auf derselben Region erzeugten einen Doppel-Badge-Konflikt.

Regel:
- **Render nur, wenn** `agent-meta` in `{{README_BADGES}}` enthalten ist (Opt-in).
- **Wert (D5/Q6 entschieden, F1/F3):** Wertquelle ist der **sync-eingebettete**
  `{{AGENT_META_VERSION}}`, durch den vorgeschalteten Re-Sync (M2) erfrischt — **kein**
  separater Live-Read. Fehlt der Wert, ist er leer, oder ist er der **nicht-leere**
  Sentinel-String `"unknown"`/`vunknown` (`read_version` liefert den Literal-String
  `"unknown"`, `scripts/lib/config.py:1046`), wird der Badge-Wert `unknown` gerendert — Label
  `agent-meta`, Message `unknown`, Bild-URL
  `https://img.shields.io/badge/agent--meta-unknown-blue.svg` (kein `v`-Präfix) — das Badge
  wird **nicht** still weggelassen. Nur das fehlende Opt-in in `{{README_BADGES}}` verhindert
  das Badge.
- **Escaping Pflicht (M1/F4):** Zuerst `-`→`--` auf den **blanken** Versionswert anwenden,
  **danach** genau ein literales `v` voranstellen (`1.1.0` → `1.1.0` → `v1.1.0`;
  `0.101.0-beta.6` → `0.101.0--beta.6` → `v0.101.0--beta.6`). Kein `vv`-Präfix; das Label
  `agent--meta` ist bereits escaped und wird **nicht** erneut escaped. Gilt insbesondere für
  Pre-Release-Versionen und ist durch einen Test abzudecken (§7).
- **Guard Link-Ziel (m2):** `{{AGENT_META_REPO}}` nur verwenden, wenn nicht leer **und**
  es ein `/` enthält (sonst entstünde `https://github.com//releases/tag/v...`); andernfalls
  Badge ohne Link rendern.
- **Link-Ziel (D1/Q2 entschieden, F2):** tagspezifisch
  `https://github.com/{{AGENT_META_REPO}}/releases/tag/v<version>` — der **rohe**
  Versionswert **ohne** Shields-Escaping — nur bei einer echten Version; das Badge
  verlinkt das zu seiner Version gehörende Release-Tag (§2.3/D1). Escaping (`-`→`--`)
  gilt ausschließlich für das Badge-Bildsegment, nie für den Link: der reale Git-Tag
  für `0.101.0-beta.6` lautet `v0.101.0-beta.6`, ein escaped
  `.../releases/tag/v0.101.0--beta.6` wäre ein 404. Für den
  Unknown-Fall wird auf die immer gültige Releases-Seite
  `https://github.com/{{AGENT_META_REPO}}/releases` zurückgefallen — **nie**
  `.../releases/tag/vunknown`. Kein Netzwerk-Check; das Tag-Restrisiko ist dokumentiert
  (§1.2, §8).
- Der Badge-Typ ist datengetrieben (kein Provider-/Projekt-Sonderfall), er wird wie
  `version`/`stack` behandelt.

---

## 5. Manager-Integration (B1: kein README-Schreiber)

**Änderungsstellen:** `agents/1-generic/agent-meta-manager.md` §4 Upgrade (`:70-87`) und
§5 Update (`:89-102`).

Der `agent-meta-manager` **besitzt die Badges-Zeile nicht** und schreibt **kein**
README-Markup (B1). Seine Rolle: per Re-Sync den sync-eingebetteten `{{AGENT_META_VERSION}}`
erfrischen (M2) und bei Opt-in einen Re-Render beim `documenter` anstoßen.

### 5.1 §4 — `upgrade-meta` (Versions-Bump)

Heute gesetzt: `agent-meta-version` in `.meta-config/project.yaml` (Kommentar `:76`).

**Verbindliche Reihenfolge (M2):**
1. `git checkout v<TARGET>` im Submodul. Danach ist der in die generierten Agenten-Dateien
   eingebettete Platzhalter `{{AGENT_META_VERSION}}` **stale** — er wird zur Sync-Zeit aus
   `config.py:1187` befüllt und ändert sich erst durch einen neuen Sync.
2. **Re-Sync zuerst:** `sync.py --config .meta-config/project.yaml`. Der Sync schreibt
   `agent-meta-version` aus dem echten `VERSION` in `project.yaml` zurück
   (`scripts/lib/sync_pipeline.py:386-411`) und frische `{{AGENT_META_VERSION}}`-Werte in die
   generierten Dateien.
3. **Dann** Re-Render der Badges-Zeile anstoßen (§5.3). Der `documenter` nutzt den durch den
   Re-Sync (Schritt 2) **erfrischten, sync-eingebetteten** `{{AGENT_META_VERSION}}` — die
   alte, im Manager-Prompt eingebettete Kopie ist zwischen Checkout und Re-Sync stale und darf
   **nicht** als Wertquelle dienen (M2).
4. Prüfen, ob `readme.badges` `agent-meta` enthält: ja → Re-Render; nein → **nicht**
   automatisch hinzufügen, nur anbieten (§5.4/Q1).

### 5.2 §5 — `update-meta` / Re-Sync

Heute: `sync.py --config .meta-config/project.yaml`, danach optional `--validate`
(`:95-102`).

Ergänzung nach erfolgreichem Sync:
1. Re-Render der Badges-Zeile anstoßen (§5.3); Wertquelle ist der sync-eingebettete
   `{{AGENT_META_VERSION}}`, durch den Re-Sync erfrischt.
2. Ergebnis der Badge-Prüfung in die Sync-Zusammenfassung aufnehmen.
3. Ist `agent-meta` nicht in `readme.badges`: kein Schreibvorgang, nur Hinweis (§5.4/Q1).

### 5.3 Ownership & Idempotenz (B1)

**Ownership-Entscheidung:** Der `documenter` **besitzt** die Badges-Zeile und rendert sie
allein aus `README_BADGES` (Single Source of Truth). Der `agent-meta-manager` schreibt
**kein** README — er erfrischt per Re-Sync den sync-eingebetteten `{{AGENT_META_VERSION}}`
(M2) und stößt bei Bedarf einen Re-Render an. Der Wert wird also **nicht** live gelesen,
sondern über den vorgeschalteten Re-Sync aktualisiert.

- **Rationale:** `README_BADGES` existiert bereits als einzige Quelle
  (`scripts/lib/config.py:1259-1268`); README-Pflege ist die `documenter`-Domäne
  (`agents/1-generic/documenter.md:43-61`). Ein zweiter Schreiber derselben Region erzeugt
  je Lauf ein Doppel-Badge bzw. widersprüchliche Inhalte — genau der B1-Befund.
- **Konsequenz für den `manager`:** niemals Badge-Markup erzeugen oder patchen; nur Wert
  pflegen und Re-Render triggern.
- **Konsequenz für den `documenter`:** `agent-meta` wie `ci` als opt-in-Typ behandeln; Render
  nur bei Opt-in in `README_BADGES`; fehlt/ist die Version leer oder ist sie der Sentinel
  `"unknown"`/`vunknown`, wird `unknown` als Badge-Wert gerendert (D5/Q6, F1) und auf die
  `/releases`-Seite verlinkt (F2) — **kein** stilles Weglassen. Ohne Opt-in **kein** Badge.
  Der managed-block-Grundsatz (`:47-49`) schützt handgeschriebenen Text weiterhin.

**Verworfen (war B1-Ursache):** Der frühere Vorschlag, dass der `manager` einen eigenen
managed Block (`agent-meta:version-badge:begin/end`) direkt nach der H1 schreibt, entfällt
ersatzlos. Es gibt **keinen** manager-eigenen Badge-Block; die Badge-Zeile ist Teil der
`documenter`-Badges-Zeile.

**Opt-out:** Entfernt der Nutzer `agent-meta` aus `readme.badges`, entfernt der `documenter`
das Badge beim nächsten Render (kein Waisen-Badge). Es ist **kein** eigener Marker-Block
nötig; die Badges-Zeile wird als Ganzes aus `README_BADGES` neu erzeugt (siehe Q7).

**Idempotenz (Abgrenzung zu M4):** Ein „zweiter Lauf byte-identisch" ist für den
LLM-getriebenen `documenter` **nicht deterministisch testbar**. Als Design-Ziel bleibt: bei
unverändertem Wert keine inhaltliche Änderung. Ein automatisierter Idempotenz-Test wird
**nicht** gefordert (§7).

### 5.4 Verhalten, wenn `readme.badges` den Typ nicht enthält — DECISION (Offer vs. Force)

**Entschieden (Offer, D2/Q1):** Der Manager erkennt, dass das Projekt agent-meta nutzt, und **bietet**
das Badge an: „`readme.badges` um `agent-meta` erweitern?" Die Config-Änderung wird erst nach
expliziter Bestätigung angewandt und löst dann einen `documenter`-Re-Render aus
(Konfig-/Sync-Regeln `:56-68`). Dies erfüllt das geforderte Opt-in (Anforderung 2) ohne
stillen Eingriff.

**Verworfene Alternative (Force):** Badge ungefragt eintragen. Würde Opt-in verletzen und
handgeschriebene READMEs verändern — abgelehnt. Auch im Force-Fall würde unter B1 **der
`documenter`** rendern: der Manager dürfte lediglich `readme.badges` erweitern und den
Re-Render triggern, **nie** README-Markup schreiben. Damit bleibt Q1 orthogonal zur
Ownership-Entscheidung.

---

## 6. Änderung am agent-meta-README

**Änderungsstelle:** `README.md:1-38`.

Ist-Zustand (verifiziert):
- H1 `# agent-meta` in `:1`
- `> [!WARNING]`-Callout ab `:3`, `> [!IMPORTANT]`-Callout ab `:16`
- Badge-Zeile `:35-37`:
  `[![Version](...version-0.101.0--beta.6-blue.svg)]()` (stale), Python, License
- Stray-Zeile `:38` `| **Date:** 2026-09-07` (F12: entfernt — siehe Nebenbefund unten)

Reale Version: `VERSION:1` = **`1.1.0`** (verifiziert). Das Badge zeigt
`0.101.0-beta.6` → **stale**.

**Meta-Repo-Ausnahme (Option B, F8):** Dieses README ist handgepflegt — es gibt **keinen**
aktiven `readme:`-Block in der eigenen Config (§1.3). Die Badge-Zeile inkl. des neuen
`agent-meta`-Badges wird hier daher **manuell** gepflegt (kein Sync-Ergebnis). Der
`RepoWise Code health`-Badge ist bewusst **kein** Schema-Typ und bleibt reines
Meta-Repo-Markup (D3/Q4).

**Staleness-Risiko (manuelle Pflege):** Weil die Badge-Zeile des Meta-README kein
Sync-Ergebnis ist, kann sie bei einem Versions-Bump veralten (z.B. `version-1.1.0` vs.
tatsächliches `VERSION`). Guard dagegen ist der statische Test
`tests/test_meta_readme_badges.py`, der die Badge-Zeile gegen die **zur Laufzeit** aus
`VERSION` gelesene Version prüft und stale `0.101.0*`-Werte verbietet — ein Bump ohne
README-Anpassung wird dadurch rot.

### 6.1 Ziel-Top-Block

```markdown
# agent-meta

[![agent-meta v1.1.0](https://img.shields.io/badge/agent--meta-v1.1.0-blue.svg)](https://github.com/Popoboxxo/agent-meta/releases/tag/v1.1.0)
[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)]()
[![Code health](https://api.repowise.dev/badge/health/popoboxxo/agent-meta.svg)](https://repowise.dev/repo/popoboxxo/agent-meta)
[![Python](https://img.shields.io/badge/python-3.x-green.svg)]()
[![License](https://img.shields.io/badge/license-MIT-gray.svg)]()

> [!WARNING]
> ## VibeCoding Experiment — Read Before Using
> ...(Inhalt unverändert)

> [!IMPORTANT]
> ## AI Agent Setup & Initialization Protocol
> ...(Inhalt unverändert)
```

Änderungen:
1. Badge-Block von `:35-37` direkt hinter H1 (`:1`) verschoben, **vor** die Callouts.
2. RepoWise-Code-Health-Badge ergänzt (exakte Zeile wie oben, Anforderung fix).
3. Stale-Version-Badge `0.101.0--beta.6` **korrigiert behalten** (`version-1.1.0`, D4/Q5:
   Projektversion ≠ Frameworkversion = zwei Informationen) **und** um das neue
   `agent-meta`-Badge (Quelle `AGENT_META_VERSION`, Tag-Link nach D1) **ergänzt**.
   Python-/License-Badges bleiben.
4. Der alte Standort `:35-37` entfällt (keine Doppelung der Badges).

> Nebenbefund (F12, umgesetzt): Die verirrte Tabellenzeile `| **Date:** 2026-09-07` direkt
> hinter dem Badge-Block hatte keinen Tabellenkopf und war reiner Ballast. Sie wurde entfernt
> (risikoloses Mini-Issue, hier mitgenommen); ein eigener Issue ist damit erledigt.

> Hinweis zu 3 (aufgelöst, D4/Q5): Der korrigierte generische `Version`-Badge
> (`version-1.1.0`) bleibt **erhalten** und das `agent-meta`-Badge wird **ergänzt**. Die
> scheinbare Doppelung ist gewollt — Projektversion und Frameworkversion sind zwei
> unterschiedliche Informationen.

---

## 7. Teststrategie

| Test | Inhalt |
|---|---|
| `tests/test_readme_variables.py` (bereits vorhanden) | Erweitern: `badges: ["version","agent-meta"]` → `README_BADGES == "version, agent-meta"`; Default-Test (`:12`) bleibt grün (kein Default-on) |
| `tests/test_documenter_readme_section.py` (in diesem Branch erweitert) | Statische Assertions: `documenter`-§5 nennt den Typ `agent-meta`, den **sync-eingebetteten** `AGENT_META_VERSION` (M2), die Render-nur-bei-Opt-in-Regel, den `unknown`-Fall inkl. Sentinel `"unknown"`/`vunknown` und Bild-URL `agent--meta-unknown-blue.svg` (D5/Q6, F1), den `/releases`-Fallback statt `vunknown` (F2), die Pflicht zum `-`→`--`-Escaping des **blanken** Werts vor dem `v`-Präfix **nur im Bildsegment** (inkl. Pre-Release, kein `vv`, kein Doppel-Escaping), den tag-spezifischen Link mit **rohem** `<version>`-Wert und den `AGENT_META_REPO`-Guard; zudem ist der `documenter` als **einziger** Badge-Schreiber benannt (B1) |
| `tests/test_readme_template.py` (in diesem Branch **neu angelegt**) | Statische Assertions am Template-Artefakt: opt-in, `unknown` (Label `agent-meta`, Message `unknown`, Bild-URL `agent--meta-unknown-blue.svg`), `/releases`-Fallback, `-`→`--`-Escaping des blanken Werts vor dem `v`-Präfix **nur im Bildsegment**, `<escaped-version>`-Platzhalter im Bild und `<version>`-Platzhalter (roh) im Link, Repo-Guard; Negativ: kein `badge/agent----meta` (genau einmal escaped), kein `releases/tag/v<escaped-version>` und `agent-meta` nicht im unkommentierten Default |
| `tests/test_meta_readme_badges.py` (in diesem Branch **neu angelegt**) | Statische Assertions am Meta-README: Badge-Block direkt unter H1, `agent-meta`-Badge mit Tag-Link, RepoWise-Code-Health-Badge, generischer `version`-Badge frisch, keine stale `0.101.0*`-Werte, kein Doppel-Escaping |
| `tests/test_readme_schema.py` (existiert bereits, m1) | `config/project-config.schema.json`: `readme.badges: ["agent-meta"]` akzeptiert, unbekannter Typ abgelehnt (Draft7) |
| `templates/configs/README-template.md` (statisch) | Der Badge-Kommentar dokumentiert `agent-meta` und enthält ein korrekt escapetes Pre-Release-Beispiel (`0.101.0--beta.6`) |
| Link-/Escaping-Check (deterministisch, ohne Netzwerk) | Statische Assertion auf die dokumentierte Regel + Beispiel: `agent--meta` (Label) und `-`→`--` nur im Bildsegment des blanken Versionswerts, dann `v`-Präfix, mit Pre-Release-Fall `0.101.0-beta.6` → `0.101.0--beta.6` → `v0.101.0--beta.6`; zudem real version → `/releases/tag/v<version>` (roh), unknown → `/releases` (F2) |
| Szenario 11 | `tests/scenarios/configs/11-readme-standard.project.yaml:11-14` um `agent-meta` in `badges` erweitern (Config-Akzeptanz). **Keine** README-Marker-Assertion: `tests/scenarios/run.sh:57-65` führt nur `sync.py` aus, und die README wird laut Template-Kopf (`templates/configs/README-template.md:1-11`) **nie** sync-prozessiert — eine Marker-Assertion wäre wirkungslos. `tests/scenarios/asserts/11-readme-standard.sh` bleibt auf Datei-/Provider-Checks beschränkt; `tests/scenarios/registry.md:58` Beschreibung aktualisieren |
| Idempotenz (Manager) | **Nicht** automatisiert (M4): Ein byte-identischer zweiter Lauf ist für einen LLM-Prompt-getriebenen Agenten nicht deterministisch testbar. Design-Ziel bleibt „keine inhaltliche Änderung bei gleichem Wert"; die deterministischen Teile (Opt-in, Opt-out-Regel) werden statisch über die Template-Regeln geprüft |

---

## 8. Threat-/Link-Modell (4 Fragen)

1. **Was bauen wir?** Ein README-Badge, das die verwendete agent-meta-Version sichtbar macht,
   config-getrieben und opt-in.
2. **Was kann schiefgehen?** (a) Badge zeigt eine **falsche** Version (Change ohne
   `agent-meta-version`-Update / stale gecachte Shields-URL); (b) Link führt **ins Nichts**
   (Repo umbenannt, Tag existiert nicht); (c) Bild-Badge in privaten/offline Repos nicht
   ladbar — es gibt **zwei** externe Bild-Abhängigkeiten: Shields.io (Version-Badge) und
   RepoWise (`api.repowise.dev`, Code-Health-Badge, Format/Outage-Risiko, m3); (d)
   handgeschriebenes README wird durch Auto-Insert beschädigt; (e) `AGENT_META_REPO` leer →
   malformtes Link-Ziel `https://github.com//releases/tag/v...` (m2).
3. **Mitigations:** Eine einzige Wert-Quelle (`AGENT_META_VERSION` ← `VERSION`, gespiegelt in
   `agent-meta-version`), sync-eingebettet und per Re-Sync erfrischt (M2); **ein**
   Badge-Schreiber (`documenter`, B1); fehlende/leere Version oder Sentinel
   `"unknown"`/`vunknown` wird als `unknown`-Badge-Wert gerendert statt weggelassen
   (D5/Q6, F1); `-`→`--`-Escaping des blanken Werts vor dem `v`-Präfix (M1/F4);
   tag-spezifisches Link-Ziel `https://github.com/<repo>/releases/tag/v<version>`
   (roher Wert, kein Shields-Escaping im Link — Escaping nur im Bildsegment)
   (D1/Q2) mit dokumentiertem Tag-Restrisiko (§1.2, §8) und `/releases`-Fallback für den
   Unknown-Fall (F2); Guard auf nicht-leeres `AGENT_META_REPO` mit `/` (m2); Opt-in statt
   Force (D2/Q1); managed-block-Grundsatz schützt fremden Text.
4. **Konsequenzen:** Ein falsches oder totes Badge ist ein **Dokumentationsdefekt** und
   untergräbt Vertrauen (analog zur Defekt-Regel in `documenter.md:56`). agent-meta kann die
   Erreichbarkeit **beider** externer Badge-Anbieter (Shields.io, RepoWise) und die Existenz
   eines Tags nicht garantieren (kein Netzwerk-Check, §1.2/Q3); dieses Restrisiko wird bewusst
   akzeptiert und dokumentiert.

---

## 9. Offene Fragen

1. **Force vs. Offer bei fehlendem `agent-meta` in `readme.badges`?** **Entschieden (D2/Q1):**
   Offer (Vorschlag + Bestätigung), kein stilles Eintragen (§5.4).
2. **Link-Ziel:** **Entschieden (D1/Q2, F2):** tag-spezifisches Link-Ziel
   `https://github.com/Popoboxxo/agent-meta/releases/tag/v<version>` (roher
   Versionswert, **kein** Shields-Escaping — Escaping gilt nur für das Bildsegment)
   für **echte** Versionen. Für den **Unknown-Fall** (missing/empty oder Sentinel
   `"unknown"`/`vunknown`) wird **offiziell** auf die immer gültige Releases-Seite
   `https://github.com/<repo>/releases` zurückgefallen — nie `.../releases/tag/vunknown`.
   Das Tag-Restrisiko für echte Versionen (kein Netzwerk-Check, Q3) wird dokumentiert und
   bewusst akzeptiert (§1.2, §2.3, §8).
3. **Offline-/Private-Ziel-Repos:** Shields.io ist extern und kann in privaten/offline Umgebungen
   blockiert sein. Badge trotzdem anbieten, warnen, oder für private Repos gar nicht rendern?
   **Offen — als dokumentierte Grenze (F7):** Es gibt bewusst **keinen** Runtime-Netzwerk-Check
   (§1.2); das Restrisiko eines nicht ladbaren Bildes ist in §8 akzeptiert. Offen bleibt nur
   die UX-Frage „warnen vs. gar nicht rendern" — kein Implementierungsblocker für v1.
4. **Code-Health-Badge für Zielprojekte?** **Entschieden (D3/Q4):** **nein** für v1 —
   RepoWise deckt nur registrierte Repos ab, der Typ bleibt Meta-Repo-spezifisch (§1.2).
5. **Doppelte Versionsinformation:** **Entschieden (D4/Q5):** Das generische `version`-Badge
   bleibt **erhalten** (Projektversion ≠ Frameworkversion = zwei Informationen) und wird im
   Meta-README um das neue `agent-meta`-Badge **ergänzt** (§6.1). Im Meta-README stehen damit
   der korrigierte `version-1.1.0`-Badge **und** das `agent-meta`-Badge.
6. **`unknown`-Verhalten:** **Entschieden (D5/Q6, F1/F2):** Bei fehlendem/leerem `VERSION`
   (`read_version` → `"unknown"`, `scripts/lib/config.py:1046`) wird der Badge-Wert `unknown`
   gerendert (Label `agent-meta`, Message `unknown`, Bild-URL
   `agent--meta-unknown-blue.svg`, kein `v`-Präfix) — das Badge wird **nicht** still
   weggelassen (§4, §5.3). Der Auslöser umfasst die **nicht-leeren** Sentinel-Rohwerte
   `"unknown"` und `"vunknown"` — `"vunknown"` ist dabei der wörtliche Raw-Wert des
   Sentinels, nicht ein aus `unknown` erzeugtes `v`-Präfix (das `v` wird im Badge
   ausschließlich bei einer realen Version vorangestellt); das Link-Ziel fällt auf
   `/releases` zurück (F2).
7. **Marker vs. section-driven:** **Entschieden (F7):** **kein** Marker. Die Badges-Zeile ist
   section-driven — der `documenter` erzeugt sie als Ganzes aus `README_BADGES` (konsistent
   mit dem bestehenden `documenter`-Prinzip `:47-49`). Ein eigener
   `agent-meta:version-badge:begin/end`-Block entfällt ersatzlos (B1, §5.3).

---

## 10. Bezug zu bestehender Doku

| Thema | Referenz |
|---|---|
| README-Standard & Managed-Block-Prinzip | [`templates/configs/README-template.md`](../../templates/configs/README-template.md), [`../guides/`](../guides/) |
| `readme.badges`-Schema | [`../../config/project-config.schema.json`](../../config/project-config.schema.json) (`readme`, Zeile 819-867) |
| `AGENT_META_VERSION` | [`../../scripts/lib/config.py`](../../scripts/lib/config.py) (`:1187`, `read_version` `:1042-1046`) |
| `README_BADGES` | [`../../scripts/lib/config.py`](../../scripts/lib/config.py) (`:1259-1268`), [`../../scripts/lib/consistency/placeholders.py`](../../scripts/lib/consistency/placeholders.py) (`:20`), [`../../scripts/lib/standalone.py`](../../scripts/lib/standalone.py) (`:71`) |
| Renderer-Regel (einziger Badge-Schreiber, B1) | [`../../agents/1-generic/documenter.md`](../../agents/1-generic/documenter.md) (§5, Badges-Row `:52-61`, agent-meta-Regel `:56-61`) |
| Manager Upgrade/Update (Wert-Pflege + Re-Render-Trigger, **kein** README-Schreiber) | [`../../agents/1-generic/agent-meta-manager.md`](../../agents/1-generic/agent-meta-manager.md) (§4 `:70-87`, §5 `:89-102`) |
| `agent-meta-version`-Rückschreibung nach Sync | [`../../scripts/lib/sync_pipeline.py`](../../scripts/lib/sync_pipeline.py) (`:386-411`) |
| Badge-Typen-Kommentar (Config-Beispiel) | [`../../templates/configs/project.yaml.example`](../../templates/configs/project.yaml.example) (`:76-83`) |
| Meta-Repo Badge-Config-Beispiel | [`../../README.md`](../../README.md) (`:911-916`) |
| Szenario README-Standard | [`../../tests/scenarios/registry.md`](../../tests/scenarios/registry.md) (`:58`), [`../../tests/scenarios/configs/11-readme-standard.project.yaml`](../../tests/scenarios/configs/11-readme-standard.project.yaml) |
| Statische README-Schema-Tests (existierend) | [`../../tests/test_readme_schema.py`](../../tests/test_readme_schema.py), [`../../tests/test_readme_variables.py`](../../tests/test_readme_variables.py), [`../../tests/test_documenter_readme_section.py`](../../tests/test_documenter_readme_section.py) |
| 0/1/2/3-Schichten-Modell | [`../../.opencode/skills/architecture/SKILL.md`](../../.opencode/skills/architecture/SKILL.md) |
| Sync-Interface | [`../../.opencode/skills/sync-interface/SKILL.md`](../../.opencode/skills/sync-interface/SKILL.md) |

---

## 11. Kurzlegende der Befund-Codes

- **B1** — Blocker: Ownership-Konflikt Badge-Schreiber (`documenter` allein).
- **D1–D5** — Decision/Design-Entscheidungen (Offer, Link-Ziel, Code-Health, Versions-Dopplung, `unknown`).
- **F1–F12** — Findings/Muss-Punkte aus den Reviews (u.a. `unknown`-Fall, Link-Fallback, Escaping, Meta-Repo-Ausnahme, Testabdeckung).
- **M1–M4** — Major-Punkte (Escaping, Re-Sync-Wertquelle, Doku-Konsistenz, Idempotenz).
- **m1–m3** — Minor-Punkte (Test-Anlage/Doku, Link-Guard, RepoWise-Outage).
- **Q1–Q7** — Offene Fragen mit Entscheid (§9).

> Die Codes sind Review-interne Referenzen; maßgeblich ist jeweils der ausformulierte Text,
> nicht der Code.
