# Audit: Admin-UI — Security + Accessibility (PR 0.5 / P32, Stufe A)

**Branch:** `chore/audit-top5-reports` (verifiziert, kein Wechsel)
**Commit:** `94a740c5` (verifiziert)
**Datum:** 2026-11-20
**REQ-ID:** PR 0.5 / P32 / E-06
**Roadmap:** `docs/plans/2026-11-15-master-roadmap.md` §3.1 PR 0.5 / §1 P32
**Ziel-Konformitätsstufe:** WCAG 2.1/2.2 **Level AA** (entspricht EN 301 549 für öffentliche Beschaffung)
**Methode:** Statische Quellanalyse (Read/Grep), Kontrastberechnung mit der WCAG-2.x-Relativluminanzformel (Python/Stdlib). **Kein** Browser-, Live-Server-, axe-core-/Lighthouse- oder G1-Volltestlauf. **Keine** Exploitation, keine Mutation, kein Commit.
**Gate-Hinweis:** P32-G1 (Voll-Testlauf) wurde durch den Nutzer am 2026-11-20 **explizit übersprungen**. Alle Aussagen sind statisch; dynamische Verifikation steht aus.

---

## 1. Scope

| Artefakt | Umfang | Relevanz |
|---|---|---|
| `scripts/admin-server.py` | 6726 Zeilen | HTTP-Server, Auth/Origin/Host-Bindung, Config-Schreibpfade, Response-Header |
| `docs/ui/admin-ui.html` | 12014 Zeilen | UI-Shell, Design-Tokens/CSS, DOM-Aufbau zur Laufzeit via `el()` und `innerHTML` |

Nicht im Scope: `docs/ui/live-dashboard.html`, `scripts/viz.py`, MCP-Server, `docs/api/admin-ui-reference.md` (nur als Datenquelle für `/api/help` betrachtet).

---

## 2. Zusammenfassung — Top-Findings nach Severity

| ID | Kriterium | Stufe | Severity | Ort (Zeile) |
|---|---|---|---|---|
| A-01 | 4.1.2 Name, Role, Value / 2.4.3 Focus Order | A | **major** | `admin-ui.html:764-773, 820-857` |
| A-02 | 4.1.2 Name, Role, Value | A | **major** | `admin-ui.html:768` |
| A-03 | 3.3.2 Labels or Instructions / 4.1.2 | A | **major** | `admin-ui.html:889-925` |
| A-04 | 2.1.1 Keyboard / 4.1.2 | A | **major** | `admin-ui.html:11838-11873` |
| A-05 | 2.4.7 Focus Visible | A | **major** | `admin-ui.html:304-321` |
| A-06 | 1.4.13 Content on Hover or Focus / 2.1.1 | AA / A | **major** | `admin-ui.html:11846-11849, 11953-11954` |
| A-07 | 1.4.3 Contrast (Minimum) | AA | **major** | `admin-ui.html:19, 108, 191, 257, 338, 444, 691` |
| A-08 | 2.5.8 Target Size (Minimum) | AA | minor | `admin-ui.html:7075-7079, 1395, 6284, 2526` |
| A-09 | 1.4.11 Non-text Contrast | AA | minor | `admin-ui.html:25, 207, 284` |
| A-10 | 3.3.8 Accessible Authentication (Minimum) | AA | minor | `admin-ui.html:896` |
| A-11 | 2.4.11 Focus Not Obscured (Minimum) | AA | minor (offen) | `admin-ui.html:237-239, 11840` |
| S-01 | Fehlende Security-Response-Header | — | minor | `admin-server.py:3619-3647` |
| S-02 | Unescaped `innerHTML` aus `/api/help` | — | minor | `admin-ui.html:11926-11929, 11954, 11959; admin-server.py:6000-6006` |
| S-03 | Absolute Pfade in 404-`detail` | — | minor | `admin-server.py:3824-3825, 6042` |

Höchste Severity: **major** (A-Kriterien). Kein blocker. Keine WCAG-2.2-Konformitätsaussage möglich (siehe §4).

---

## 3. Accessibility-Findings (WCAG 2.1/2.2)

### Finding A-01
**WCAG criterion:** 4.1.2 Name, Role, Value; 2.4.3 Focus Order
**Conformance level:** A
**Severity:** major
**Location:** `docs/ui/admin-ui.html:764-773` (`#modal-overlay`), `:820-836` (`showModal`/`hideModal`), `:854-857`
**Problem:** Das Modal ist ein `<div id="modal-overlay" hidden>` ohne `role="dialog"`, ohne `aria-modal="true"` und ohne `aria-labelledby` auf `#modal-title`. `showModal()` setzt nur `hidden = false`; Fokus wird nicht in den Dialog verschoben, nicht gehalten (kein Trap) und bei `hideModal()` nicht auf den Auslöser zurückgegeben. Screenreader bleiben im Hintergrund-Dokument; Tastaturfokus kann hinter dem Overlay landen.
**Assistive tech:** Screenreader (Dialog-Rolle/Name fehlt), Tastatur (Fokusverlust, kein Trap).
**Recommended fix:** Native `<dialog>` mit `showModal()`/`close()` verwenden (bringt Rolle, Modalität, Fokus-Trap und Fokus-Restore mit). Falls `<div>` bleibt: `role="dialog" aria-modal="true" aria-labelledby="modal-title"`, Fokus auf den ersten interaktiven Nachkommen setzen, `Tab`/`Shift+Tab` zyklisch halten, `Escape` schließen, `inert` auf `#app` während der Öffnung und Fokus-Restore in `hideModal()`. Siehe WAI-ARIA APG „Dialog (Modal) Pattern“. Kein ARIA nötig bei nativem `<dialog>` (First Rule of ARIA).

### Finding A-02
**WCAG criterion:** 4.1.2 Name, Role, Value
**Conformance level:** A
**Severity:** major
**Location:** `docs/ui/admin-ui.html:768`
**Problem:** `<button class="modal-close" id="modal-close">&times;</button>` hat keinen zugänglichen Namen; `&times;` wird je nach Screenreader als „×“, „times“ oder gar nicht angesagt. Der Zweck der Schaltfläche ist nicht erkennbar.
**Assistive tech:** Screenreader, Sprachsteuerung (kein ansprachbarer Name).
**Recommended fix:** `aria-label="Close dialog"` (alternativ sichtbares `<span class="sr-only">Close dialog</span>`) ergänzen; `aria-hidden="true"` auf dem Dekorationszeichen. Besser: `title`-Attribut allein genügt nicht. Mit A-01 gemeinsam lösen (nativer `<dialog>` bietet keine automatische Beschriftung des Close-Buttons — Name trotzdem setzen).

### Finding A-03
**WCAG criterion:** 3.3.2 Labels or Instructions; 4.1.2 Name, Role, Value
**Conformance level:** A
**Severity:** major
**Location:** `docs/ui/admin-ui.html:889-925` (insb. `:896`, `:903`)
**Problem:** Das Token-Eingabefeld hat nur ein `placeholder="Admin token"` und `type="password"`, aber kein zugeordnetes `<label>`; `placeholder` ist kein Ersatz für ein Label und verschwindet bei der Eingabe. Das umgebende `.token-prompt-overlay` (`:903`) ist wie A-01 ohne Dialog-Rolle/Modalität. `input.focus()` (`:923`) setzt den Fokus, es gibt jedoch keinen Trap.
**Assistive tech:** Screenreader (Feld ohne Namen), Tastatur (Fokus kann hinter das Overlay wandern).
**Recommended fix:** `<label for="token-input">Admin token</label>` + eindeutige `id`, `aria-describedby` auf die Fehlermeldung (`:897`); `role="alertdialog" aria-modal="true" aria-labelledby` am Overlay; Fokus-Trap und Fokus-Restore wie in A-01. `autocomplete="current-password"` statt `off` siehe A-10.

### Finding A-04
**WCAG criterion:** 2.1.1 Keyboard; 4.1.2 Name, Role, Value
**Conformance level:** A
**Severity:** major
**Location:** `docs/ui/admin-ui.html:11838-11873` (`:11859-11861`, `:11866-11873`)
**Problem:** Der Hilfe-Umschalter besteht aus drei klickbaren `<div class="help-btn" data-state="…">Help: Off/Icons/Full</div>` mit ausschließlich `click`-Listener. Ohne `tabindex`, Button-Rolle, Tastatur-Handler und `aria-pressed` sind diese Bedienelemente für Tastatur und Screenreader nicht bedienbar bzw. ihr Zustand nicht erkennbar.
**Assistive tech:** Tastatur (nicht fokussierbar), Screenreader (keine Rolle/kein Zustand).
**Recommended fix:** Native `<button type="button" aria-pressed="true|false">` mit `click`-Handler (native Tastaturunterstützung, kein ARIA nötig) oder `<fieldset><legend>` + `<input type="radio">`. `.help-btn.active` bleibt als visueller Zustand, `aria-pressed` ergänzt die Semantik. Position `fixed` beibehalten (siehe 3.2.6 in §4).

### Finding A-05
**WCAG criterion:** 2.4.7 Focus Visible
**Conformance level:** A
**Severity:** major
**Location:** `docs/ui/admin-ui.html:304-321`
**Problem:** Bei den Toggle-Schaltern ist das eigentliche `<input type="checkbox">` per `opacity: 0; width: 0; height: 0;` (`:304`) unsichtbar. Es existiert keine Regel `.toggle input:focus-visible + .slider { … }`; der sichtbare `.slider` (`:305-312`) erhält beim Fokussieren des Checkbox keine Hervorhebung. Tastaturbenutzer sehen nicht, welcher Schalter fokussiert ist.
**Assistive tech:** Tastatur, Low-Vision.
**Recommended fix:** `.toggle input:focus-visible + .slider { outline: 2px solid var(--accent-blue); outline-offset: 2px; }` ergänzen. Das Input nicht aus dem Fokusfluss entfernen (kein `display:none`).

### Finding A-06
**WCAG criterion:** 1.4.13 Content on Hover or Focus; 2.1.1 Keyboard
**Conformance level:** AA (1.4.13) / A (2.1.1)
**Severity:** major
**Location:** `docs/ui/admin-ui.html:11846-11849`, `:11953-11954`, `:11975`
**Problem:** Die Hilfetooltips erscheinen ausschließlich über `:hover` (`.help-icon-wrapper:hover .help-tooltip { display: block; }`, `:11848`). Der Auslöser ist ein nicht fokussierbares `<span class="help-icon-badge">?</span>` (18×18 px, `:11847`), ohne `tabindex`, Button-Rolle oder `aria-describedby`. Der Tooltip ist nicht per Tastatur erreichbar, nicht persistent (verschwindet bei Mausbewegung), nicht dismissible per Escape und nicht hoverbar. In `helpState===2` wird derselbe Inline-HTML-Text in einen Block eingefügt (`:11959`) — dort ist der Inhalt zwar sichtbar, der Icon-Pfad bleibt aber barrierehaft.
**Assistive tech:** Tastatur, Screenreader, mobile Geräte (kein Hover).
**Recommended fix:** Auslöser als `<button type="button" aria-describedby="…">` mit `tabindex`-Standardverhalten umsetzen; Tooltip bei `:focus-visible` **und** `:hover` zeigen, `Escape` zum Schließen, `pointer-events` auf den Tooltip erlauben (hoverbar), bis zum Fokuswechsel persistent. Alternativ Value+Text direkt sichtbar (`helpState===2` als Default) — dann entfällt 1.4.13. Siehe WAI-ARIA APG „Tooltip Pattern“.

### Finding A-07
**WCAG criterion:** 1.4.3 Contrast (Minimum)
**Conformance level:** AA
**Severity:** major
**Location:** `docs/ui/admin-ui.html:19` (`--text-muted: #6e7681`), verwendet u. a. `:108` (`.nav-group-title`), `:191` (`.metric .label`), `:257` (`.field-help`), `:338` (`table.data thead th`), `:444` (`.token-prompt-msg`), `:691` (`.muted`)
**Problem:** `--text-muted` wird für informative Fließtexte, Hilfetexte, Spaltenköpfe und Statusmeldungen verwendet. Berechnete Kontrastverhältnisse (WCAG-Relativluminanz, Python):
- `#6e7681` auf `--bg-primary #0d1117` → **4.12:1**
- `#6e7681` auf `--bg-secondary #161b22` → **3.77:1**
- `#6e7681` auf `--bg-tertiary #21262d` → **3.31:1**
- `#6e7681` auf `--bg-input #0b1220` → **4.08:1**

Alle Werte liegen unter 4.5:1 für normalen Text. Betroffen sind u. a. 11px-Hilfetexte und Tabellenköpfe (`:257`, `:338`) — kein Large-Text-Ausnahmefall.
**Assistive tech:** Low-Vision, alle Nutzer in heller Umgebung.
**Recommended fix:** `--text-muted` auf mindestens `#8b949e` anheben (berechnet: 6.15:1 auf `#0d1117`, 4.95:1 auf `#21262d`) oder für die Verwendung auf `bg-tertiary` einen separaten Token mit ≥4.5:1 definieren. `--text-secondary #8b949e` erfüllt 4.5:1 auf `bg-primary`/`bg-secondary`/`bg-input` (6.15/5.62/6.09:1), knapp aber ausreichend auf `bg-tertiary` (4.95:1).

### Finding A-08
**WCAG criterion:** 2.5.8 Target Size (Minimum)
**Conformance level:** AA
**Severity:** minor
**Location:** `docs/ui/admin-ui.html:7075-7079` (Move-Button), `:1395` und `:6284` (Tag-Entfernen), `:2526` (Reset-to-Default)
**Problem:** Mehrere interaktive Ziele sind kleiner als 24×24 CSS px:
- Move-Button `padding:2px 8px; font-size:14px; line-height:1` (`:7077`) → Höhe ≈ 14 + 4 + 2 (Border) = **20 px**.
- Tag-Button `padding:0 6px; font-size:11px` (`:1395`, `:6284`) → Höhe ≈ 11×1.5 + 2 = **≈18.5 px**, Breite ≈ 21 px.
- Reset `padding:2px 6px; font-size:0.85em` (`:2526`) → Höhe ≈ **≈22 px**.

Keine durchgängige 24px-Mindestfläche; für Touch-Flächen wird 44×44 px empfohlen. Exakte Abstände (Spacing-Ausnahme) wurden nicht im Browser gemessen.
**Assistive tech:** Motorisch eingeschränkte Nutzer, Touch.
**Recommended fix:** `min-width: 24px; min-height: 24px;` (Touch: 44px) auf diesen Buttons, `padding` entsprechend anpassen; Alternatively ausreichenden Abstand ≥24px zwischen Zielen sicherstellen und messtechnisch belegen.

### Finding A-09
**WCAG criterion:** 1.4.11 Non-text Contrast
**Conformance level:** AA
**Severity:** minor
**Location:** `docs/ui/admin-ui.html:25` (`--border-color: #30363d`), `:207` (`.btn`), `:284` (Input-Border)
**Problem:** Die Begrenzung von Eingabefeldern und Standard-Buttons (`1px solid var(--border-color)`) hat berechnete Kontraste von **1.53:1** auf `--bg-input #0b1220` bzw. **1.25:1** auf `--bg-tertiary #21262d` — unter den geforderten 3:1 für die Erkennbarkeit von UI-Komponentengrenzen. Im Fokuszustand wird der Rand blau (7.41:1), im Ruhezustand ist die Komponentengrenze jedoch kaum erkennbar.
**Assistive tech:** Low-Vision.
**Recommended fix:** `--border-strong #444c56` (2.15:1 auf `bg-input`) reicht nicht; Randfarbe auf einen Wert mit ≥3:1 gegenüber `bg-input` anheben (z. B. `#6e7681` → 4.08:1) oder durch eine kontrastreiche Hintergrundfläche/Füllung ersetzen.

### Finding A-10
**WCAG criterion:** 3.3.8 Accessible Authentication (Minimum)
**Conformance level:** AA
**Severity:** minor
**Location:** `docs/ui/admin-ui.html:896`
**Problem:** Das Token-Feld setzt `autocomplete: "off"`. Damit wird Browser-Autofill bzw. Passwortmanagern aktiv die Unterstützung verwehrt, obwohl das Merken/Eingeben einesTokens eine kognitive Funktion ist. Einfügen (Paste) ist nicht blockiert (kein `paste`-Listener gefunden) — das ist der mildernde Faktor, aber keine Autofill-Alternative.
**Assistive tech:** Screenreader-/Passwortmanager-Nutzer, kognitiv eingeschränkte Nutzer.
**Recommended fix:** `autocomplete: "current-password"` (oder `one-time-code`, falls das Token Einmalcharakter hat). `sessionStorage` := Tokenspeicher (`:862-872`) bleibt dabei unangetastet.

### Finding A-11
**WCAG criterion:** 2.4.11 Focus Not Obscured (Minimum)
**Conformance level:** AA
**Severity:** minor (offen — statisch nicht verifiziert)
**Location:** `docs/ui/admin-ui.html:237-239` (`.data-table th { position: sticky; top: 0; }`), `:11840` (`.help-toggle-widget { position: fixed; top: 12px; right: 20px; z-index: 1000; }`)
**Problem:** Ein sticky Tabellenkopf und ein permanent fixes Hilfewidget oben rechts können einen fokussierten Bedienelement ganz oder teilweise verdecken. Statisch vorhanden, aber ohne Browserlauf nicht nachgewiesen, ob beim Fokussieren ein Element vollständig verdeckt wird.
**Assistive tech:** Tastatur, Screenreader (Fokus landet auf verdecktem Element).
**Recommended fix:** `scroll-padding-top` auf `#content` setzen (Höhe des Widgets + Tabellenkopf), `scroll-margin-top` auf interaktiven Elementen in `.data-table`; Widget bei Fokus in dessen Nähe ausblenden oder positionell unterbrechen. Manuell mit Tab-Navigation und `document.activeElement.getBoundingClientRect()` im Browser verifizieren (G1 nachgeholt werden muss).

---

## 4. WCAG-2.2-Delta (sechs neue Kriterien, einzeln)

| Kriterium | Stufe | Urteil | Evidenz / Begründung |
|---|---|---|---|
| **2.5.8 Target Size (Minimum)** | AA | **FAIL** | A-08: Move-Button 20px Höhe (`admin-ui.html:7077`), Tag-Buttons ≈18.5px (`:1395`, `:6284`). <24px, Spacing-Ausnahme nicht belegt. |
| **2.5.7 Dragging Movements** | AA | **PASS** | Drag & Drop der Rollenkarten (`admin-ui.html:7069, 7101-7134`) hat einen Single-Pointer-Alternativweg: der Move-Button (`:7075-7088`) ruft exakt dieselbe Move-Logik auf (`:7096` vs. `:7126-7131`). |
| **2.4.11 Focus Not Obscured (Minimum)** | AA | **OFFEN (nicht PASS)** | A-11: sticky `th` (`:237-239`) + fixed Widget `z-index:1000` (`:11840`). Ohne Browserlauf kein Nachweis; daher kein PASS. |
| **3.2.6 Consistent Help** | AA | **PASS** | Hilfewidget wird einmal erzeugt und an `document.body` gehängt (`admin-ui.html:11837-11864`), `position: fixed; top:12px; right:20px` (`:11840`); `hashchange` aktualisiert nur den Inhalt (`:11990-11991`), nicht die Position. Relative Reihenfolge/Position über alle Routen konstant. |
| **3.3.7 Redundant Entry** | AA | **N-A** | Kein mehrstufiger Formularprozess gefunden, der bereits eingegebene Daten erneut abfragt. Der Token-Prompt (`:889-925`) fragt nur nach **fehlgeschlagener** Authentifizierung erneut — das ist keine Redundanz bereits akzeptierter Daten. Finale Bestätigung wäre dynamisch nötig. |
| **3.3.8 Accessible Authentication (Minimum)** | AA | **FAIL (minor)** | A-10: `autocomplete: "off"` (`admin-ui.html:896`) unterdrückt Autofill/Passwortmanager; Paste ist erlaubt (kein `paste`-Blocker gefunden). Kein CAPTCHA vorhanden. |

**Gate:** Vier der sechs Kriterien sind nicht PASS. **WCAG-2.2-Konformität wird nicht bescheinigt** — `STATUS: partial`.

---

## 5. Security-Findings (statisch, read-only)

### Finding S-01 — Fehlende Security-Response-Header
**Ort:** `scripts/admin-server.py:3619-3647` (`_send_json`, `_send_text`, `_send_bytes`)
**Problem:** Die drei zentralen Response-Helfer setzen nur `Content-Type`, `Content-Length` und `Cache-Control: no-store`. Es gibt **keine** `X-Content-Type-Options: nosniff`, keine `X-Frame-Options` / CSP `frame-ancestors`, kein `Referrer-Policy`. Damit ist die UI potenziell frambar (Clickjacking) und MIME-Sniffing nicht unterbunden.
**Milderung:** Mutationen sind origin-geprüft (`admin-server.py:1212-1260`, `3838-3839`), daher sind Cross-Origin-Writes bereits blockiert; Auth-Token liegt in `sessionStorage`, nicht in Cookies (CSRF-Token-Cookie-Vektor entfällt).
**Severity:** minor (Defense-in-Depth).
**Empfehlung:** In allen drei Helfern `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` (oder CSP `frame-ancestors 'none'`) und `Referrer-Policy: no-referrer` ergänzen.

### Finding S-02 — Unescaped `innerHTML` aus `/api/help`
**Ort:** `docs/ui/admin-ui.html:11926-11929` (`mdToHtml`), `:11954`, `:11959`, `:11975`; Quelle `scripts/admin-server.py:6000-6006`
**Problem:** `mdToHtml()` interpoliert den Markdown-Text unescaped in `<p>…</p>`, und das Ergebnis wird per `innerHTML` in den DOM injiziert. Die Daten stammen aus der lokalen Datei `docs/api/admin-ui-reference.md` (`:6002`), die über `/api/help` token-geschützt ausgelesen wird. Es existiert kein Schreibpfad über die Admin-UI. Dennoch ist ein `innerHTML`-Sink mit serverseitigem Text vorhanden; bei kompromittierter/überschriebener Hilfedatei wäre XSS im Admin-UI-Kontext möglich — und `sessionStorage` enthält das Admin-Token (`:862-872`).
**Severity:** minor (vertrauenswürdige lokale Quelle, token-geschützt; **keine** Ausnutzung versucht).
**Empfehlung:** Hilfetext mit `textContent` einfügen und Markdown-Struktur über DOM-Knoten aufbauen (analog zum `el()`-Helper, `:781-801`, dessen `html`-Branch bereits aus Sicherheitsgründen entfernt wurde), oder eine streng whitelistende Sanitizer-Funktion verwenden. Konsistent mit der bereits dokumentierten XSS-Entscheidung in `:785-788`.

### Finding S-03 — Absolute Pfade in 404-Detail
**Ort:** `scripts/admin-server.py:3824-3825` (`do_GET`), `:3880` (`do_POST`), `:3903` (`do_DELETE`); Auslöser z. B. `:6042` (`path.read_bytes()`)
**Problem:** `except FileNotFoundError as exc` gibt `str(exc)` als `detail` an den Client zurück. Python-Fehlermeldungen von `Path.read_bytes()` enthalten den absoluten Pfad. Das widerspricht dem Ziel von issue #581 (keine internen Pfade an HTTP-Clients, `_handle_error` in `:3674-3689` macht es ansonsten korrekt).
**Severity:** minor (Information Disclosure, kein direkter Zugriff).
**Empfehlung:** `detail` auf eine feste, client-sichere Meldung setzen (`{"error":"not_found"}`) und die Originalexception nur serverseitig loggen. `FileNotFoundError` über `_handle_error` oder einen dedizierten generischen 404-Helfer leiten.

### Verifizierte Sicherheitskontrollen (positiv, statisch)
- Konstante Token-Vergleichszeit via `hmac.compare_digest` (`admin-server.py:1133-1140`, `import hmac` `:44`).
- Fail-closed Host-Bindung: non-loopback ohne Token → `ValueError` (`:6358-6365`); Token-Priorität CLI > Env > Config > Datei (`:1143-1162`).
- Origin-/Host-Prüfung für Mutationen inkl. DNS-Rebinding-Schutz (`:1212-1260`, `:3751-3770`, `:3838-3839`); `do_OPTIONS` ohne CORS-Header (`:3776-3782`).
- Query-Token nur für den read-only SSE-Endpunkt `/api/events` erlaubt (`:1187-1207`, `:3796-3809`, `:3813-3814`); UI entfernt `?token=` per `history.replaceState` (`:877-884`).
- Body-Größenlimit 10 MB vor `read()` (`:98`, `:3649-3668`); generische Fehler responses (`:3674-3689`).
- Pfad-Traversal-/Key-Whitelist und Symlink-Containment in `ConfigManager` (`:1378-1413`), Warnung bei world-readable Token-Datei (`:1263-1284`).
- `el()`-Helper ohne `innerHTML`-Branch (`:781-801`); `showModal()` nutzt `replaceChildren`/`textContent` (`:823-829`).

---

## 6. Priorisierte Remediation-Liste

1. **P1 – A-Kriterien (major):** A-01 Modal-Dialog-Semantik + Fokus-Trap/Restore (nativer `<dialog>`), A-02 Name des Close-Buttons, A-03 Label des Token-Prompts, A-04 Tastaturbedienbarkeit des Hilfe-Umschalters, A-05 sichtbarer Toggle-Fokus.
2. **P2 – AA-Kontrast/Interaktion (major):** A-07 `--text-muted` ≥4.5:1 auf allen verwendeten Hintergründen, A-06 Tooltip per Fokus erreichbar/dismissible.
3. **P3 – WCAG-2.2-Delta (minor/offen):** A-08 Target Size ≥24px, A-10 `autocomplete="current-password"`, A-09 Non-text Contrast ≥3:1, A-11 Fokus-Verdeckung im Browser verifizieren und beheben.
4. **P4 – Security Defense-in-Depth (minor):** S-01 Security-Header, S-02 `innerHTML`-Sink entschärfen, S-03 generische 404-Details.
5. **P5 – Verifikation (nachFreigabe):** axe-core/Lighthouse-Scan + manuelles Screenreader-/Tastatur-Testing; G1-Volltestlauf nur nach expliziter Nutzer-Ja (hier übersprungen).

---

## 7. Manueller Screenreader-Test (nicht ausgeführt — Anleitung für die Nachverifikation)

- **NVDA/JAWS (Windows):** Browse-Mode vs. Focus-Mode prüfen. Dialog (A-01) muss beim Öffnen in den Focus-Mode wechseln und als „Dialog Titel“ angesagt werden; Hilfewidget (A-04) muss mit `Tab` erreichbar und mit `Enter`/`Space` umschaltbar sein; Token-Feld (A-03) muss beim Fokussieren „Admin token, Passwort“ ansagen.
- **VoiceOver (macOS/iOS):** Rotor über Landmarks (`aside`/`nav`/`main`) und Überschriften; prüfen, ob das Modal als Modal erkannt wird (VO: „dialog“) und ob `aria-pressed` am Hilfewidget als „ausgewählt“ ansagt. `aria-hidden`/`sr-only` an den Nav-Icons (`:1719-1723`) auf VoiceOver-Verhalten gegenprüfen.
- **Bekannte Divergenzen:** `aria-modal` und `aria-pressed` werden von NVDA/JAWS und VoiceOver unterschiedlich interpretiert; `<dialog>`-Native-Modalität ist die robusteste Lösung. Tooltip-Verhalten (`:hover` vs. `:focus`) unterscheidet sich zwischen Desktop-VO und iOS-VO erheblich — nicht einen Screenreader als Referenz für alle nehmen.
- **Automatisiert + manuell:** axe-core deckt nur ca. 30–40 % der Kriterien ab; Fokusreihenfolge, Fokus-Trap, Screenreader-Semantik und Lesereihenfolge müssen manuell geprüft werden.

---

## 8. Grenzen / Nicht durchgeführt

- Kein Browser-Run, kein Live-Server, kein axe-core/Lighthouse, kein G1-Volltestlauf (vom Nutzer am 2026-11-20 explizit übersprungen).
- Kontrastwerte sind **berechnet** (WCAG-Relativluminanz, Python/Stdlib), nicht geschätzt; für A-11/Spacing-Ausnahme (2.5.8) fehlen gemessene Pixelwerte.
- Das UI baut seinen DOM überwiegend zur Laufzeit auf (`el()`, `innerHTML`). Statische Zeilenangaben verweisen auf die Erzeugungsstellen; tatsächliche gerenderte Bäume wurden nicht inspiziert.
- Keine Code-Änderungen, keine Commits, kein Push/PR, keine Issue-Änderungen, keine MCP-Tool-Nutzung, kein Worktree/Isolation-Flag. Einzige geschriebene Datei: dieser Bericht.

---

STATUS: partial
RESULT: Statischer Security+A11y-Audit von `scripts/admin-server.py` und `docs/ui/admin-ui.html` (Branch `chore/audit-top5-reports`@`94a740c5`) erstellt; 11 WCAG-Findings (höchste Severity major, 5 A-Kriterien) und 3 Security-Findings (minor), WCAG-2.2-Delta mit 2 FAIL, 1 OFFEN, 2 PASS, 1 N-A. Kein Browser-/Live-/G1-Lauf (vom Nutzer übersprungen) — Konformität daher nicht bescheinigt.
ARTIFACTS: `docs/analysis/2026-11-20-audit-top5-admin-ui-a11y.md`
A11Y_AUDIT: a11y-audit-v1 — Level-A: 5 Findings (Modal-Semantik/Fokus, Close-Button-Name, Token-Feld-Label, Hilfe-Tastatur, Toggle-Fokus); Level-AA: 6 Findings (Kontrast 3.31–4.12:1, Target Size <24px, Non-text Contrast, 3.3.8, Focus Not Obscured offen, Hover-Tooltip). Top-Barrieren: fehlende Dialog-Semantik/Fokussteuerung, nicht tastaturbedienbares Hilfewidget, zu geringer Textkontrast. Security: 3 minor (fehlende Header, innerHTML-Sink, Pfad-Leak), positive Kontrollen dokumentiert.
NEXT: [Developer fix]
