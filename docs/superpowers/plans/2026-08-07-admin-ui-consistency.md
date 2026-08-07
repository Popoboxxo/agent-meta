# Admin-UI Konsistenz-Fahrplan — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Schließt die 13 Befunde aus dem Admin-UI-Konsistenz-Audit (2026-08-07, siehe `## Referenz` unten) — von drei live bestätigten sichtbaren Bugs bis zur strukturellen Konsolidierung dreier unabhängiger Key/Value-Editoren — in vier aufeinander aufbauenden Phasen.

**Architecture:** `docs/ui/admin-ui.html` ist eine einzelne ~9100-Zeilen-Datei (Vanilla JS, kein Build-Schritt), ausgeliefert von `scripts/admin-server.py`. Es gibt kein Component-Framework — jede "Konsolidierung" bedeutet: eine bestehende, bereits gehärtete Implementierung wird zur einzigen Quelle, alle Duplikate rufen sie auf oder werden entfernt. Phasen 0–1 sind reine Bugfixes/Ergänzungen ohne Architekturentscheidung. Phase 2 konsolidiert auf Komponentenebene (Karten, Farben, Empty-States) ohne Verhaltensänderung. Phase 3 ändert Verhalten (ein gemeinsamer KV-Editor, ein gemeinsames Bestätigungs-Modal) und braucht vor der Umsetzung je eine kurze Design-Entscheidung (welche der 3 KV-Editor-Varianten wird kanonisch, welches Bestätigungsmuster gilt für alle destruktiven Aktionen).

**Tech Stack:** Vanilla JS/HTML/CSS in einer Datei, Python-Backend (`scripts/admin-server.py`), Playwright-Browser-Tests unter `tests/browser/`.

## Global Constraints

- Jede Änderung wird live gegen den laufenden Admin-Server verifiziert (`python scripts/admin-server.py --port 7422 --no-viz`), nicht nur am Code gelesen — Pflicht laut `CLAUDE.md` für UI-Änderungen.
- Kein Build-Schritt, keine neuen Dependencies. CSS-Variablen und JS-Helper bleiben inline in `admin-ui.html`.
- DoD-Preset dieses Projekts ist `rapid-prototyping` (Tests: optional) — trotzdem bekommt jeder **Verhaltens**-Fix (Phase 0, Teile von Phase 3) einen Playwright-Regressionstest nach dem in dieser Session etablierten Muster (rot ohne Fix, grün mit Fix via `git stash`-Gegenprobe). Reine Style-/CSS-Konsolidierung (Phase 2) verifiziert visuell, kein Test-Zwang.
- Jede Phase ist ein eigener Branch + PR. Phase *n* setzt auf dem gemergten Ergebnis von Phase *n-1* auf.
- Keine neue Komplexität einführen, die nicht durch einen Audit-Befund gedeckt ist (Rückbezug auf die Ultra-Kürzen-Vorgabe aus der A2A-Aufräumrunde).

---

## File Structure

- **Modify:** `docs/ui/admin-ui.html` — alle Phasen, einziger Zieldatei.
- **Create:** `tests/browser/test_admin_ui_consistency_p0.py` — Phase 0 Regressionstests.
- **Create:** `tests/browser/test_admin_ui_consistency_p3.py` — Phase 3 Regressionstests (KV-Editor, Bestätigungs-Modal).
- **Modify:** `CHANGELOG.md` — je Phase ein Eintrag unter `## [Unreleased]`.

---

## Phase 0 — Sofort (≤30 Min, 3 isolierte Live-Bugs)

### Task 1: HTML-Entity wird als Rohtext gerendert (Rules Presets)

**Files:**
- Modify: `docs/ui/admin-ui.html` (Rules-Presets-View, Tabellen-Überschrift "Preset Matrix …")
- Test: `tests/browser/test_admin_ui_consistency_p0.py`

**Context:** Auf `#/config/rules-presets` zeigt die Tabellenüberschrift wörtlich `&#8212;` statt eines Gedankenstrichs. Ursache: der `el()`-Builder fügt Text als Text-Node ein (bewusste XSS-Policy, siehe Audit-Befund #13) — ein HTML-Entity-String wird dort nie dekodiert. Fix ist **nicht** `innerHTML` zu verwenden (Policy!), sondern das Entity im Quelltext durch das echte Unicode-Zeichen `—` (U+2014) zu ersetzen.

- [ ] **Step 1: Lokalisieren**

`grep -n "8212" docs/ui/admin-ui.html`

- [ ] **Step 2: Failing Test schreiben**

```python
def test_rules_presets_matrix_heading_has_no_raw_html_entity(browser_ctx):
    ctx, base = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{base}/#/config/rules-presets")
        page.wait_for_load_state("networkidle")
        heading = page.get_by_text("Preset Matrix", exact=False)
        text = heading.text_content() or ""
        assert "&#8212;" not in text
        assert "—" in text  # echter Gedankenstrich
    finally:
        page.close()
```

Run: `pytest tests/browser/test_admin_ui_consistency_p0.py::test_rules_presets_matrix_heading_has_no_raw_html_entity -v`
Expected: FAIL.

- [ ] **Step 3: Entity durch echtes Zeichen ersetzen**

Ersetze den literalen String `"Preset Matrix &#8212; all rules vs. all presets"` (oder wo immer die Entity-Schreibweise steht) durch `"Preset Matrix — all rules vs. all presets"` (echtes U+2014 im Quelltext).

- [ ] **Step 4: Test verifizieren**

Run: `pytest tests/browser/test_admin_ui_consistency_p0.py::test_rules_presets_matrix_heading_has_no_raw_html_entity -v`
Expected: PASS.

- [ ] **Step 5: Repo-weit nach weiteren Entity-Leaks suchen**

`grep -noE "&#[0-9]+;" docs/ui/admin-ui.html`
Jeder Treffer bekommt denselben Fix (echtes Unicode-Zeichen statt Entity-String).

---

### Task 2: Badge zeigt wörtlich "Recommended Tag" (External Skills)

**Files:**
- Modify: `docs/ui/admin-ui.html` (External-Skills-View, Skill-Card-Badge)
- Test: `tests/browser/test_admin_ui_consistency_p0.py`

**Context:** Auf `#/project/skills-overrides` hängt der Skill-Card-Renderer das Wort `Tag` fest an den Badge-Text an (vermutlich `` `${label} Tag` `` statt `` `${label}` ``), sodass ein Badge mit Wert `"Recommended"` als `"Recommended Tag"` erscheint.

- [ ] **Step 1: Lokalisieren**

`grep -n "Tag\`" docs/ui/admin-ui.html` bzw. gezielt im Skill-Card-Renderer (siehe Audit: nahe der MCP-/Skill-Card-Duplikat-Stelle) nach der Badge-Text-Konstruktion suchen.

- [ ] **Step 2: Failing Test schreiben**

```python
def test_skill_card_recommended_badge_has_no_literal_tag_suffix(browser_ctx):
    ctx, base = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{base}/#/project/skills-overrides")
        page.wait_for_load_state("networkidle")
        badge = page.get_by_text("Recommended", exact=False).first
        text = (badge.text_content() or "").strip()
        assert text == "Recommended"
    finally:
        page.close()
```

Run: erwartet FAIL (`text == "Recommended Tag"`).

- [ ] **Step 3: Fix**

Badge-Text-Konstruktion korrigieren, sodass nur der eigentliche Label-Wert gerendert wird (kein hartcodiertes `" Tag"`-Suffix).

- [ ] **Step 4: Test verifizieren** — PASS.

---

### Task 3: "Loading…"/"Loading..." Mischung vereinheitlichen

**Files:**
- Modify: `docs/ui/admin-ui.html` (4 Fundstellen laut Audit: 697, 958, 6576, 7520)

**Context:** Kein Verhaltensbug, rein kosmetisch — kein dedizierter Test nötig, nur ein konsistentes Zeichen für alle 4 Stellen (Empfehlung: echtes Ellipsis-Zeichen `…`, da kürzer und bereits an 2 von 4 Stellen verwendet).

- [ ] **Step 1:** `grep -n "Loading\.\.\.\|Loading…" docs/ui/admin-ui.html`
- [ ] **Step 2:** alle 4 Stellen auf `"Loading…"` vereinheitlichen.
- [ ] **Step 3:** live gegenprüfen (View mit Ladezustand kurz aufrufen, z. B. Sync-Seite beim ersten Laden).

---

### Task 4: Phase 0 abschließen

**Files:** keine (Verifikations-Task)

- [ ] **Step 1:** `pytest tests/browser/test_admin_ui_consistency_p0.py -v` — alle 2 neuen Tests PASS.
- [ ] **Step 2:** `pytest -q --ignore=external --ignore=tests/browser` — keine Regression.
- [ ] **Step 3:** CHANGELOG-Eintrag unter `### Fixed`.
- [ ] **Step 4:** Branch `fix/admin-ui-p0-live-bugs`, Commit, Push, PR. Issue(s) referenzieren (vorher anlegen: "Admin UI: HTML-Entity-Leak + Recommended-Tag-Badge-Bug").

---

## Phase 1 — Gezielt (~1–2 Std, isolierte Einzelfixes)

### Task 5: Backups-Tabelle vereinheitlichen + Danger-Styling für "Delete"

**Files:**
- Modify: `docs/ui/admin-ui.html` (Backups-View, `#/project/backups`)

**Context:** Live bestätigt: die Backups-Tabelle nutzt kein `class="data"` (kein Header-Band, keine Zebra-Streifen) und "Delete" ist optisch identisch zu "Restore" — kein Danger-Styling trotz destruktiver Wirkung.

- [ ] **Step 1:** Tabellen-Markup der Backups-View auf `class="data"` umstellen (Referenz: eine bereits korrekt gestylte Tabelle, z. B. Roles- oder MCP-Server-Ansicht, als Vorlage nehmen).
- [ ] **Step 2:** "Delete"-Button auf die im File bereits existierende `btn-danger`-Klasse umstellen (siehe `renderDictEditor`s Lösch-Button als Referenz).
- [ ] **Step 3:** Live verifizieren: `#/project/backups` zeigt jetzt Header-Band + rot abgesetzten Delete-Button.
- [ ] **Step 4:** Bestehende Backup-Funktionalität (Restore/Delete/Create) manuell einmal durchklicken — keine Funktionsänderung, nur Styling.

---

### Task 6: Rohe Config-Key-Labels humanisieren (Providers & Platforms)

**Files:**
- Modify: `docs/ui/admin-ui.html` (`#/project/providers`, Abschnitte "Options"/"PROVIDER-OPTIONS")

**Context:** `PROVIDER-OPTIONS` (Großbuchstaben+Bindestrich) und `provider-isolation` (roher YAML-Key) brechen die sonst durchgehaltene Sentence-Case-Konvention derselben Seite ("AI providers", "Platforms", "Options").

- [ ] **Step 1:** Label `PROVIDER-OPTIONS` → `Provider options` (Sentence Case, konsistent mit Nachbar-Sections).
- [ ] **Step 2:** Label `provider-isolation` → `Provider isolation` (humanisiertes Label vor dem `<select>`, roher YAML-Key bleibt intern als `id`/Datenattribut erhalten, nicht als sichtbarer Text).
- [ ] **Step 3:** Grep nach weiteren rohen Kebab-Case-Labels in Framework-Defaults-Views (`config/ai-providers`, `config/mcp-registry` etc.) — falls das dieselbe Klasse von Befund ist, hier mit erledigen; falls es dort eine **bewusste** Konvention ist (Rohdaten-Editor vs. kuratierte Ansicht), explizit so belassen und in `docs/ui/` dokumentieren statt zu "fixen".

---

### Task 7: `title`-Attribute vereinheitlichen

**Files:**
- Modify: `docs/ui/admin-ui.html` (alle Fundstellen aus Audit: 1151, 5247 vs. 3298, 4037, 6348, 6542)

- [ ] **Step 1:** `grep -n 'title: "remove"' docs/ui/admin-ui.html` und die Title-Case-Gegenstücke (`grep -n 'title: "Remove'`).
- [ ] **Step 2:** alle auf Title-Case-Konvention vereinheitlichen (`"Remove override"`-Stil), da diese die Mehrheit stellt und präziser ist (sagt WAS entfernt wird, nicht nur DASS etwas entfernt wird).

---

### Task 8: Phase 1 abschließen

- [ ] **Step 1:** `pytest -q --ignore=external --ignore=tests/browser` + `pytest tests/browser/ -q` — keine Regression.
- [ ] **Step 2:** CHANGELOG-Eintrag.
- [ ] **Step 3:** Branch `fix/admin-ui-p1-targeted-fixes`, PR.

---

## Phase 2 — Konsolidierung (~1 Tag, kein Verhaltenswechsel)

### Task 9: Warn-/Danger-Farben auf `--accent-red` migrieren

**Files:**
- Modify: `docs/ui/admin-ui.html` (`:root`-Block + ~15 Fundstellen: `#d97706`, `#f59e0b`, `#c9a227`/`#c08b00`, `#553333`/`#ff9999`, `#aa8866`)

**Context:** `--accent-red` existiert bereits im `:root`. Ziel: eine zweite Variable `--accent-warning` (falls die gefundenen Farben tatsächlich zwei semantisch unterschiedliche Zustände meinen — "Warnung" vs. "Gefahr" — statt sie alle blind auf `--accent-red` zu pressen) einführen und alle Fundstellen darauf umstellen. Vor dem Fix: pro Fundstelle kurz prüfen, ob die Farbe wirklich "Warnung/Danger" bedeutet oder zufällig ähnlich aussieht — nicht blind ersetzen.

- [ ] **Step 1:** Für jede der 5 Farbgruppen (siehe Audit) den Verwendungskontext lesen (Zeilen aus dem Audit-Report) und semantisch clustern: "Danger/Delete" vs. "Warnung/Hinweis" vs. zufällig ähnlich, aber unrelated.
- [ ] **Step 2:** `--accent-warning` (amber, z. B. `#f59e0b`) zusätzlich zu `--accent-red` im `:root` definieren, falls Cluster "Warnung" real und von "Danger" verschieden ist.
- [ ] **Step 3:** Alle geclusterten Fundstellen auf die passende Variable umstellen.
- [ ] **Step 4:** Live jede betroffene View kurz aufrufen — Farben dürfen sich nicht sichtbar ändern (reines Refactoring, keine Redesign-Entscheidung in diesem Task).

---

### Task 10: Tabellen-Stil vereinheitlichen (`class="data"` überall)

**Files:**
- Modify: `docs/ui/admin-ui.html` (Zeilen ~3165, ~5346, ~5658 inline gestylt; ~4945 `data-table`)

- [ ] **Step 1:** Die 3 inline gestylten Tabellen auf `class="data"` umstellen (analog Task 5).
- [ ] **Step 2:** Die eine `data-table`-Instanz auf `data` umbenennen (klasse, nicht Konzept — beide meinten dasselbe).
- [ ] **Step 3:** `grep -c 'class="data"' docs/ui/admin-ui.html` vor/nach vergleichen — Anzahl muss um 4 gestiegen sein.
- [ ] **Step 4:** Live: alle 4 betroffenen Views aufrufen, visuell auf Regressionen prüfen (Spaltenbreiten, Wrapping).

---

### Task 11: Empty-State-Pattern vereinheitlichen

**Files:**
- Modify: `docs/ui/admin-ui.html` (6× `class="empty"`, 5× `class="muted"` für denselben Zweck, 2× ganz ohne Klasse)

- [ ] **Step 1:** Entscheiden, welche der beiden Klassen kanonisch wird (Empfehlung: `empty` — der Name beschreibt den Zweck präziser; `muted` ist ein reiner Farb-Utility-Name und wird an anderen Stellen für unrelated Zwecke wiederverwendet, siehe Audit-Fundstellen 2509/2718/6110/6823 — Gefahr von Bedeutungs-Überladung, wenn `muted` DER Empty-State-Standard wird).
- [ ] **Step 2:** Die 5 `muted`-Empty-State-Stellen auf `empty` umstellen (nur die, die wirklich einen leeren Zustand darstellen — nicht generische "gedämpfter Text"-Verwendungen von `muted`).
- [ ] **Step 3:** Die 2 klassenlosen Stellen auf `empty` umstellen.
- [ ] **Step 4:** Live: mind. 3 Views mit leerem Zustand testen (z. B. ein Projekt ohne MCP-Overrides, ohne Backups, ohne Skills).

---

### Task 12: MCP-Server-Card und Skill-Card auf gemeinsame Funktion konsolidieren

**Files:**
- Modify: `docs/ui/admin-ui.html` (Zeilen ~2342–2360 MCP-Card, ~2596–2614 Skill-Card)

**Context:** Identische Struktur, nur Label + evtl. Icon unterscheiden sich.

- [ ] **Step 1:** Beide Renderer nebeneinander lesen, die tatsächlichen Unterschiede (Parameter) exakt auflisten (Label-Text, evtl. unterschiedliche Aktions-Buttons).
- [ ] **Step 2:** Eine gemeinsame `renderConfigurableCard(opts)`-Funktion extrahieren, die beide Unterschiede als Parameter nimmt.
- [ ] **Step 3:** Beide Call-Sites auf die neue Funktion umstellen, alten Duplikat-Code entfernen.
- [ ] **Step 4:** Live: MCP-Servers-View UND External-Skills-View aufrufen, byte-für-byte-identisches Rendering-Verhalten zu vorher sicherstellen (Screenshot-Vergleich vor/nach empfohlen).

---

### Task 13: XSS-Policy-Ausnahmen auf `el()` umstellen

**Files:**
- Modify: `docs/ui/admin-ui.html` (Zeilen 5389, 8972, 9077, 9082, 9098, 9103 laut Audit)

**Context:** Diese Stellen verletzen die im Code selbst dokumentierte "kein `innerHTML`"-Policy (Kommentar bei Zeile 722–725). Zeile 5389 interpoliert einen `${rule}`-Wert direkt in `tr.innerHTML` — die riskanteste Stelle zuerst.

- [ ] **Step 1:** Zeile 5389 (`tr.innerHTML` mit `${rule}`-Interpolation) zuerst fixen — auf `el()`-Aufbau umstellen. Das ist der einzige Fund mit potenziell nutzereinflussbarem Wert; separat und zuerst behandeln.
- [ ] **Step 2:** Failing-Test optional (nur falls `rule`-Wert tatsächlich aus Nutzereingabe stammt — sonst reicht manuelle Live-Prüfung, da statischer Content).
- [ ] **Step 3:** Hilfe-Tooltip-System (Zeilen 8972–9103, `mdToHtml()`-Output) einzeln bewerten: falls der Markdown-Input ausschließlich aus fest im Repo hinterlegten Hilfetexten stammt (kein Nutzer-Input), ist das Risiko gering — trotzdem auf `el()`/DOM-Aufbau umstellen, um die Policy wieder lückenlos zu machen, nicht weil ein akuter Exploit vorliegt.
- [ ] **Step 4:** Nach jeder Umstellung die betroffene View live aufrufen — Tooltips/Regeln müssen weiterhin korrekt gerendert werden (insbesondere Markdown-Formatierung in Tooltips).

---

### Task 14: Phase 2 abschließen

- [ ] **Step 1:** Volle Regression (`pytest -q --ignore=external --ignore=tests/browser` + `pytest tests/browser/ -q`).
- [ ] **Step 2:** CHANGELOG-Eintrag.
- [ ] **Step 3:** Branch `fix/admin-ui-p2-consolidation`, PR.

---

## Phase 3 — Strukturell (größer, eigene Design-Entscheidung nötig)

Diese Phase ändert sichtbares Verhalten, nicht nur Optik. Vor Task 15 und Task 17 je ein kurzer Design-Schritt (kein voller Brainstorming-Prozess nötig, aber eine bewusste, im PR dokumentierte Entscheidung).

### Task 15: Design-Entscheidung — kanonischer KV-Editor

**Files:** keine (Entscheidungs-Task, Ergebnis dokumentiert in Task 16s PR-Beschreibung)

- [ ] **Step 1:** Die 3 Implementierungen (`renderDictEditor` Zeile 2258, `addKVRow` Zeile 5667, Env-Vars-Modal-Variante ~6800) nach folgenden Kriterien vergleichen: (a) hat den #319-Rename-Fix, (b) unterstützt Typen (string/bool) oder nur string, (c) Lösch-Bestätigung ja/nein, (d) Zeilen-Layout (inline vs. Modal).
- [ ] **Step 2:** Entscheiden: `renderDictEditor` (hat den Rename-Fix bereits, per Audit als am stärksten gehärtet markiert) wird um `addKVRow`s Typ-Unterstützung (string/bool-Select) erweitert und zur einzigen Implementierung. Die Modal-basierte Env-Vars-Variante wird auf die erweiterte `renderDictEditor` umgestellt (Modal-Layout kann als optionaler `mode: "modal"`-Parameter erhalten bleiben, falls es dort einen echten UX-Grund gibt — sonst auch vereinheitlichen).
- [ ] **Step 3:** Entscheidung + Begründung in einer kurzen Notiz festhalten (wird Teil der PR-Beschreibung von Task 16).

### Task 16: KV-Editoren konsolidieren

**Files:**
- Modify: `docs/ui/admin-ui.html` (alle 3 Fundstellen aus Task 15)
- Test: `tests/browser/test_admin_ui_consistency_p3.py`

- [ ] **Step 1:** Failing Test: Rename-Kollisions-Schutz (siehe bereits existierendes Muster aus `tests/browser/test_dict_editor_rename_collision.py`) zusätzlich gegen `addKVRow`s bisherigen Aufrufort schreiben — muss heute FAILEN, weil `addKVRow` den Fix nicht hat.
- [ ] **Step 2:** `renderDictEditor` um Typ-Unterstützung (string/bool) erweitern, an `addKVRow`s bisherigen Call-Sites einsetzen, `addKVRow` entfernen.
- [ ] **Step 3:** Env-Vars-Modal-Call-Site auf die konsolidierte Funktion umstellen (Ergebnis aus Task 15 Step 2 anwenden).
- [ ] **Step 4:** Delete-Glyph vereinheitlichen (Empfehlung: `×` U+00D7, da 10 von 12 Stellen es bereits nutzen) — an allen jetzt-konsolidierten Stellen.
- [ ] **Step 5:** Test aus Step 1 muss jetzt PASSEN — Beweis, dass die Kollisions-Sicherheit jetzt überall gilt, nicht nur an einer Stelle.
- [ ] **Step 6:** Live: jede der bisher 3 unterschiedlichen KV-Editor-Stellen aufrufen (MCP-Server-Env-Vars, Provider-Options, Environment-Variables-Seite) — gleiches Verhalten, gleiches Aussehen überall.

### Task 17: Design-Entscheidung — einheitliches Bestätigungsmuster für destruktive Aktionen

**Files:** keine (Entscheidungs-Task)

- [ ] **Step 1:** Bestandsaufnahme: 14× `confirm()`, N× KV-Editor-Löschen ganz ohne Bestätigung (jetzt durch Task 16 vereinheitlicht — betrifft alle konsolidierten KV-Editor-Instanzen gleichermaßen), 1× existierende `showModal()`-Komponente, aktuell nirgends für Löschbestätigungen genutzt.
- [ ] **Step 2:** Entscheiden: alle Löschbestätigungen wandern auf `showModal()` (konsistent mit dem Rest der App-Optik, native `confirm()`-Dialoge brechen aus dem Dark-Theme aus) — inklusive der bisher komplett unbestätigten KV-Editor-Löschungen.
- [ ] **Step 3:** Ein gemeinsames `confirmDestructive(message, onConfirm)`-Helper-Pattern auf Basis von `showModal()` festlegen (Signatur, Button-Beschriftungen "Cancel"/"Delete" konsistent mit Rest der App).

### Task 18: Bestätigungsmuster umsetzen

**Files:**
- Modify: `docs/ui/admin-ui.html` (alle 14 `confirm()`-Stellen + alle bisher unbestätigten KV-Editor-Löschungen)
- Test: `tests/browser/test_admin_ui_consistency_p3.py`

- [ ] **Step 1:** `confirmDestructive()`-Helper implementieren (aus Task 17 Step 3), auf `showModal()` aufbauend.
- [ ] **Step 2:** Failing Test: eine KV-Editor-Löschung muss künftig eine Bestätigung zeigen (heute: sofortiges Löschen ohne jede Rückfrage) — Test simuliert Klick auf Lösch-Icon, erwartet sichtbaren Modal-Text vor dem eigentlichen Entfernen.
- [ ] **Step 3:** Alle 14 `confirm()`-Aufrufe schrittweise auf `confirmDestructive()` umstellen.
- [ ] **Step 4:** Alle KV-Editor-Löschungen (jetzt konsolidiert dank Task 16) mit `confirmDestructive()` absichern.
- [ ] **Step 5:** Test aus Step 2 PASS. Zusätzlich: jede der 14 vormaligen `confirm()`-Stellen einmal live durchklicken — Funktion (Abbrechen behält, Bestätigen löscht) darf sich nicht ändern, nur die Optik.

### Task 19: Spacing-Scale einführen (optional, niedrigste Priorität dieser Phase)

**Files:**
- Modify: `docs/ui/admin-ui.html` (`:root`-Block: `--space-1` … `--space-6` auf 4px-Raster; schrittweise Migration der 58+64 Fundstellen)

**Context:** Größter Umfang, geringste sichtbare Wirkung pro Aufwand — bewusst als letzter, optionaler Task eingeplant. Kann in einem eigenen, späteren Anlauf erfolgen, ohne die anderen Phase-3-Ergebnisse zu blockieren.

- [ ] **Step 1:** `--space-1: 4px` bis `--space-6: 32px` im `:root` definieren (deckt die im Audit gefundenen Werte 4/6/8/10/12/14/16/18/20/24/32 weitgehend ab — 6/10/14/18 werden auf das nächste Raster-Vielfache gerundet).
- [ ] **Step 2:** Migration in kleinen, unabhängig überprüfbaren Batches (pro View), nicht in einem Rutsch — jedes Batch live gegenprüfen.
- [ ] **Step 3:** Kann als eigener Folge-Task/eigenes PR nach Abschluss der restlichen Phase 3 laufen; kein Blocker für Task 15–18.

### Task 20: Phase 3 abschließen

- [ ] **Step 1:** Volle Regression (`pytest -q --ignore=external --ignore=tests/browser` + `pytest tests/browser/ -q`).
- [ ] **Step 2:** Alle neuen Playwright-Tests aus Task 16/18 grün, rot-vor-Fix per `git stash`-Gegenprobe bestätigt (etabliertes Muster dieser Session).
- [ ] **Step 3:** CHANGELOG-Eintrag.
- [ ] **Step 4:** Branch `fix/admin-ui-p3-structural`, PR — PR-Beschreibung enthält die Design-Entscheidungen aus Task 15 und 17 explizit (Begründung, nicht nur Ergebnis).

---

## Self-Review Notes

- **Spec-Abdeckung:** alle 13 Audit-Befunde sind genau einem Task zugeordnet (Befunde #1 Rules-Presets-Entity → Task 1, #2 Recommended-Tag → Task 2, Loading-Mix → Task 3, Backups-Tabelle+Danger-Button → Task 5, rohe Labels → Task 6, title-Case → Task 7, Farbvariablen → Task 9, Tabellen-Stil → Task 10, Empty-States → Task 11, Card-Duplikat → Task 12, XSS-Policy → Task 13, KV-Editor-Duplikat → Task 15/16, Bestätigungsmuster → Task 17/18, Spacing → Task 19).
- **Kein Blind-Refactoring:** Task 9 (Farbvariablen) und Task 11 (Empty-States) enthalten explizit einen "erst clustern/prüfen, dann ersetzen"-Schritt, damit kein zufällig ähnlicher, aber semantisch unabhängiger Farbwert falsch zusammengelegt wird.
- **Phasengrenzen sind Merge-Punkte:** jede Phase ist ein eigener PR, damit ein Revert bei unerwarteten Live-Regressionen nicht die anderen Phasen mitreißt. Phase 3 baut auf Phase 2s Konsolidierung auf (z. B. nutzt Task 16 den in Task 12 etablierten Umgang mit gemeinsamen Renderer-Funktionen als Vorbild), ist aber technisch unabhängig durchführbar, falls Phase 2 zurückgestellt wird.
- **Bewusst nicht geplant:** ein vollständiges CSS-Framework/Design-System einzuführen — das Audit fand Inkonsistenz, keine grundsätzliche technische Sackgasse; die bestehende Single-File-Architektur bleibt erhalten (Ultra-Kürzen-Prinzip: nur beheben, was der Audit als echtes Problem belegt hat).

## Referenz

- Audit: `Admin-UI Konsistenz-Audit`, 2026-08-07 (statischer Code-Audit + Live-Begehung, 13 Befunde, 4/6/3 High/Medium/Low) — als Claude-Artifact an den Nutzer ausgeliefert, nicht separat im Repo abgelegt.
- Vorbild-Testmuster: `tests/browser/test_dict_editor_rename_collision.py` (rot-vor-Fix via `git stash`-Gegenprobe, aus PR #433 dieser Session).
