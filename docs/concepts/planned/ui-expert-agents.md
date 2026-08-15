# Konzept: UI-Experten-Rollen (Design-System & Frontend-Komponenten)

> Status: **Konzept-Entwurf v1.2** (Owner-Override, siehe Abschnitt 10) | 2026-08-15
> Ziel: Die Lücke zwischen reiner UI-Spezifikation (`ui-ux-designer`) und generischer Implementierung (`developer`) schließen. **Owner-Entscheidung (v1.2):** Beide Rollen — `design-system-architect` und `frontend-component-engineer` — werden als vollständige neue Rollen spezifiziert, nicht als Rolle+Extension (die in v1.1 empfohlene Extension-Zwischenstufe für `frontend-component-engineer` wurde vom Owner explizit verworfen, siehe Abschnitt 10) — beide inspiriert durch, aber nicht kopiert von, externen Prompt-Vorlagen.

---

## 1. Kontext & Motivation

Anstoß war das externe Repo [`mustafakendiguzel/claude-code-ui-agents`](https://github.com/mustafakendiguzel/claude-code-ui-agents) (MIT-lizenziert, 623 Stars). Wichtig für die Einordnung: Es handelt sich **nicht** um echte Claude-Code-Subagenten mit Tools/Workflow/Delegationsmodell, sondern um 8 einzelne "Fill-in-the-blank"-Prompt-Vorlagen mit dünnem YAML-Frontmatter (`name`, `description`, `model`), die man manuell in eine Chat-Session einfügt:

1. `accessibility/aria-implementation.md` — ARIA, Keyboard-Nav, Screenreader-Testing, WCAG AA/AAA
2. `animation/micro-interactions.md` — Hover/Loading/Transition-Animationen, <300ms, `prefers-reduced-motion`
3. `components/react-component-generator.md` — React+TS-Komponenten mit Props, A11y, Tests
4. `responsive/mobile-first-layout.md` — Mobile-first Breakpoint-Strategie, Grid/Flexbox
5. `ui-design/design-system-generator.md` — Farbsystem, Typografie-Skala, Spacing, Komponentenspezifikation
6. `ui-design/mobile-design-philosophy.md` — Apple-HIG-inspiriert, Touch-Targets, Micro-Interaction-Prinzipien (Trigger/Rules/Feedback/Loops/Modes)
7. `ui-design/universal-ui-design-methodology.md` — Semantic-Token-Architektur (HSL-CSS-Custom-Properties), Farbharmonie (komplementär/analog/triadisch/monochromatisch), CVA-Variant-Pattern, 8px-Spacing, Branchen-Adaptionen
8. `ux-research/user-persona-generator.md` — Datengetriebene Personas, Empathy-Maps, Journey-Szenarien

**Copyright-Hinweis:** Aus diesen 8 Vorlagen wird an keiner Stelle wörtlich oder strukturell 1:1 zitiert. Übernommen werden nur die zugrunde liegenden fachlichen *Konzepte* (Token-Architektur, Farbtheorie, Variant-Pattern, Micro-Interaction-Framework, Persona-Struktur) — neu erarbeitet im agent-meta-eigenen Rollenformat (`persona`/`workflow`/`context`/`tools`/`output_contract`/`constraints`).

**Handoff-Auflage:** Wer diese Rollen/Extensions später als vollständige Templates ausformuliert, arbeitet ausschließlich aus der abstrahierten Konzeptliste oben (Punkte 1–8) und der fachlichen Zusammenfassung in Abschnitt 4 — nicht aus den Quell-Repo-`.md`-Dateien selbst. Die Original-Dateien werden zu diesem Zweck nicht erneut geöffnet oder zeilenweise paraphrasiert, um jedes Risiko einer strukturellen 1:1-Übernahme auszuschließen, auch ein unbeabsichtigtes.

**Die eigentliche Lücke** liegt nicht in "was das Quell-Repo an Themen abdeckt", sondern darin, dass agent-meta aktuell zwei reine Spec/Audit-Rollen für UI hat, aber **keine Rolle, die Design-Systeme/Komponenten tatsächlich in Code umsetzt**:

- `ui-ux-designer` (v1.1.3) — spezifiziert Screens, Mockups, Design-System-**Schema**, User-Journeys. Implementiert explizit nicht (`<constraints>`: "Never implement code — only specify").
- `accessibility-specialist` (v0.1.0) — auditiert WCAG-Konformität, urteilt nicht über Ästhetik/UX ("das ist `ui-ux-designer`"), implementiert nicht.

Zwischen Schema-Spezifikation und WCAG-Audit klafft der eigentliche Umsetzungsschritt: aus dem Design-System-*Schema* echte Token-Dateien (CSS Custom Properties/Tailwind-Config) und aus den Screen-Specs echte, produktionsreife Komponenten machen. Das übernimmt aktuell entweder `developer` (generisch, ohne UI-Fachwissen zu Token-Architektur/Farbharmonie/Variant-Pattern) oder niemand.

## 2. Abgrenzung zu bestehenden Rollen

| Rolle | Tut | Tut nicht |
|---|---|---|
| `ui-ux-designer` (bestehend) | Screen-Specs, ASCII-Mockups, Design-System-**Schema** (YAML-Skelett), User-Journeys | Kein Code, keine Token-Dateien, keine Komponenten |
| `accessibility-specialist` (bestehend) | WCAG-2.1/2.2-Audit mit A/AA/AAA-Findings | Keine Implementierung, kein Ästhetik-/UX-Urteil |
| `design-system-architect` (**neu, Vollrolle**) | Design-System-Schema → echte Token-Artefakte (CSS/Tailwind), Farbharmonie-Systematik, Component-Variant-Contracts, Breakpoint-/Spacing-Methodik, Motion-Tokens | Keine fertigen UI-Komponenten, keine Screen-Spezifikation (das bleibt `ui-ux-designer`) |
| `frontend-component-engineer` (**neu, Vollrolle**) | Produktionsreife Komponenten (Framework-spezifisch) auf Basis von Screen-Spec + Token-Contract, State-Handling, eingebaute A11y-Grundlagen, Test-Grundgerüst | Kein Design-System-Entwurf (konsumiert nur), kein WCAG-Vollaudit (nur A11y-Grundlagen einbauen, Vollaudit bleibt `accessibility-specialist`) |
| `developer` (bestehend, generisch) | Beliebige Feature-/Bugfix-Implementierung nach REQ-ID | Kein spezialisiertes UI-Fachwissen (Token-Architektur, Farbtheorie, Variant-APIs sind kein generischer Skill) |

Die Abgrenzung `design-system-architect`/`frontend-component-engineer` vs. `developer` folgt demselben Muster wie `api-specialist` vs. `developer`: `api-specialist` erzeugt den Contract (OpenAPI-Spec) als eigenständiges Artefakt mit spezialisiertem Fachwissen (Versionierung, Breaking-Change-Klassifikation), `developer` implementiert generisch dagegen. Hier: `design-system-architect` erzeugt den Token-/Variant-Contract, `frontend-component-engineer` implementiert produktionsreife UI-Komponenten mit spezialisiertem UI-Engineering-Fachwissen (State-Matrix, Compound-Component-Pattern, eingebaute A11y-Baseline) — beides Wissen, das ein generischer `developer`-Prompt nicht strukturell enthält.

> **Hinweis zur Lieferform:** Diese Tabelle beschreibt die fachliche Rollenabgrenzung unverändert aus v1.0. Nach Owner-Entscheidung (Abschnitt 10, ersetzt die Review-Empfehlung aus Abschnitt 4.5/9) wird `frontend-component-engineer` als eigene Vollrolle ausgeliefert, nicht als `developer`-Extension.

## 3. Ziel & Nicht-Ziele

### Ziel

- `design-system-architect` als neue **Vollrolle** definieren (Rollenabgrenzung, Tools, Workflow, Delegationsflüsse).
- `frontend-component-engineer` als neue **Vollrolle** definieren (UI-Engineering-Fachwissen: State-Matrix, A11y-Baseline, Motion-Implementierung, Responsive-Umsetzung, Variant-Contract-Konsum) — Owner-Entscheidung (Abschnitt 10): direkt als eigenständige Rolle, nicht als Zwischenstufe über eine `developer`-Extension.
- Delegationskette schließen: `ideation`/`requirements` → `ui-ux-designer` (Spec) → `design-system-architect` (Token-Contract) → `frontend-component-engineer` (Implementierung) → `accessibility-specialist` (Audit) → `code-reviewer`/`tester`.
- Fachkonzepte aus dem Quell-Repo (Token-Architektur, Farbharmonie, Variant-Pattern, Micro-Interaction-Prinzipien, Mobile-first-Methodik) im agent-meta-Rollenformat neu erarbeiten, ohne Prompt-Text zu übernehmen.

### Nicht-Ziele (bewusst außerhalb dieses Konzepts)

- **`motion-interaction-designer` als eigenständige dritte Rolle** — geprüft und verworfen (Begründung Abschnitt 4.3). Motion-Belange werden auf Token-Ebene (`design-system-architect`) und Implementierungs-Ebene (`frontend-component-engineer`) verteilt.
- **`ux-research`/Persona-Generator als eigene Rolle** — geprüft und verworfen (Begründung Abschnitt 5).
- **Responsive/Mobile-Layout und CSS-Architektur als eigene Rolle(n)** — geprüft und verworfen, gehen in `design-system-architect` (Methodik/Breakpoints) und `frontend-component-engineer` (Umsetzung) auf (Begründung Abschnitt 4.4).
- **Vollständige Template-Dateien** (`agents/1-generic/design-system-architect.md`, `agents/1-generic/frontend-component-engineer.md`) — dieses Konzept liefert Rollenabgrenzung, Verantwortlichkeiten, Tool-Bedarf, Delegationsflüsse und Kern-Workflow-Skizze; die Ausformulierung als vollständiges Template ist ein Folgeschritt (`requirements`/`planner`).
- **Framework-Festlegung** (React vs. Vue vs. Web Components) — `frontend-component-engineer` muss projektagnostisch bleiben (Platzhalter `{{FRONTEND_FRAMEWORK}}` o. ä.), keine Festlegung in diesem Konzept.
- **Storybook/Design-Tooling-Integration** — denkbare Erweiterung, hier nicht spezifiziert.

## 4. Architektur-Vorschlag

### 4.1 `design-system-architect`

**Verantwortlichkeit:** Übersetzt das Design-System-*Schema* aus `ui-ux-designer` (Farbschema, Typografie-Skala, Spacing, Breakpoints als YAML-Skelett) in echte, projektgebundene Token-Artefakte — plus die fachliche Systematik dahinter, die im Schema selbst nicht steht (Farbharmonie-Regeln, Kontrast-sichere Paarungen, semantische Token-Ebenen).

**Tools:** `Read`, `Write`, `Edit`, `Bash` (Token-Build/-Lint, z. B. `npx tailwindcss` Validierung — reiner Build-/Lint-Einsatz zur Design-Zeit, kein Dev-Server/Runtime-Bedarf, daher schmaler geschnitten als bei `developer`), `Glob`, `Grep`, `TodoWrite` (Tracking bei Multi-Komponenten-Variant-Arbeit, z. B. wenn mehrere Komponententypen parallel einen Variant-Contract bekommen — analog zum `TodoWrite`-Einsatz bei `accessibility-specialist` für Multi-View-Audits).

**Kern-Workflow (Skizze):**

1. **Input lesen:** Design-System-Schema von `ui-ux-designer` (oder A2A-Payload mit Anforderungen), bestehende Token-Dateien im Projekt (Glob/Grep — nicht bei null anfangen, falls schon ein Tailwind-Config/CSS-Variablen-System existiert).
2. **Token-Ebenen definieren:** dreistufig — *Primitive* (Rohwerte, z. B. `--blue-500: #3b82f6`) → *Semantic* (Verwendungszweck, z. B. `--color-action-primary: var(--blue-500)`) → *Component* (komponentenspezifisch, z. B. `--button-bg: var(--color-action-primary)`). Nur die semantische Ebene wird von Komponenten referenziert, nie die Primitive direkt — das ist die Kernregel, die Theming/Dark-Mode überhaupt erst robust macht.
3. **Farbharmonie-Systematik + Kontrast-Gate (design-time, kein Audit):** Basisfarbe + Harmonie-Modell (komplementär/analog/triadisch/monochromatisch) ableiten. Beim Anlegen jeder Token-Paarung (Text-/Hintergrund-Kombination) einen Kontrastwert rechnerisch prüfen, um offensichtlich unbrauchbare Paarungen bereits beim Entwurf auszuschließen (z. B. hellgrau auf weiß nicht in den Contract aufnehmen). **Explizite Abgrenzung zu `accessibility-specialist` (Review-Fix M1):** Dieser Check ist ein Gate auf Token-Ebene, kein WCAG-Audit — `design-system-architect` trifft **keinen** A/AA/AAA-Konformitäts-Verdict und prüft nicht die gerenderte Komponente (tatsächliche Schriftgröße, Kontext, Rendering-Eigenheiten können den effektiven Wert verschieben). Die alleinige Autorität für das verbindliche WCAG-Urteil an gerenderten Komponenten bleibt `accessibility-specialist` (dessen `<constraints>`: "No contrast claim without a computed ratio" bezieht sich auf den Audit-Kontext, nicht auf dieses Design-time-Gate). Bei Gate-Fail: Token-Paarung nicht in den Contract aufnehmen, Rückfrage an `ui-ux-designer` statt eigenmächtiger Freigabe.
4. **Spacing/Breakpoint-Methodik:** 8px-Grid (oder projektspezifische Basis) als Skala, responsive Breakpoints als benannte Tokens (`--breakpoint-sm` etc.), dokumentierte Begründung (nicht willkürlich).
5. **Component-Variant-Contract:** pro Komponententyp (Button, Input, Card, ...) eine Variant-Matrix (z. B. `intent: primary|secondary|danger`, `size: sm|md|lg`, `state: default|hover|disabled`) als maschinenlesbarer Contract (YAML/TS-Type) — das ist der Übergabepunkt an `frontend-component-engineer` (siehe 4.2), analog zum OpenAPI-Contract von `api-specialist` an `developer`.
6. **Motion-Tokens** (siehe 4.3): Dauer-/Easing-Skala (`--duration-fast: 150ms`, `--easing-standard: cubic-bezier(...)`) plus verbindliche `prefers-reduced-motion`-Policy als Teil des Token-Sets — kein Extra-Workflow-Schritt, sondern dieselbe Token-Systematik wie Farbe/Spacing.
7. **Dark/Light-Mode:** Umsetzung ausschließlich über Overrides der *semantischen* Ebene (Schritt 2) — Primitive bleiben stabil, nur die Zuordnung Semantic→Primitive wechselt je Modus. Das ist die Testbarkeitsregel: ein Dark-Mode-Fehler ist immer ein Semantic-Mapping-Fehler, nie ein Primitive-Fehler.
8. **Output:** Token-Dateien (`design-tokens.css`/`tailwind.config.*`/`tokens.json`, projektabhängig) + Variant-Contract-Datei + kurzer Begründungs-Report (welche Harmonie, welche Kontrastwerte berechnet).

**Delegationsflüsse:** Input von `ui-ux-designer` (Schema) oder direkt `main_chat`. Output an `frontend-component-engineer` (siehe 4.2) als Token-/Variant-Contract-Konsument. Bei Kontrastproblemen Rückfrage an `ui-ux-designer` statt eigenmächtiger Farbwahl-Änderung am Schema. Für das verbindliche WCAG-Urteil an fertig gerenderten Komponenten: Weiterleitung an `accessibility-specialist` (keine eigene Zuständigkeit, siehe Schritt 3).

### 4.2 `frontend-component-engineer`

> **Lieferform nach Owner-Entscheidung (Abschnitt 10):** Das folgende Fachwissen wird als eigenständiges `agents/1-generic/frontend-component-engineer.md`-Template ausgeliefert — eine vollständige neue Rolle, analog zu `design-system-architect` (Abschnitt 4.1), nicht als `developer`-Extension. Die Workflow-Skizze unten bleibt inhaltlich identisch gegenüber dem ursprünglichen Fachwissens-Entwurf.

**Verantwortlichkeit:** Produktionsreife UI-Komponenten aus Screen-Spec (`ui-ux-designer`) + Token-/Variant-Contract (`design-system-architect`) bauen — inklusive Props-Contract, State-Handling und eingebauter A11y-Baseline. Kein Design-Entwurf, kein WCAG-Vollaudit.

**Tools:** `Bash` (Dev-Server-Start, Test-Runs, Build — analog zu `developer.md` Workflow-Schritt 6 "Self-Verifikation": Dev-Server starten, Feature im Browser beobachten), `Read`, `Write`, `Edit`, `Glob`, `Grep`, `TodoWrite` (Mehrkomponenten-Tracking bei parallelem Ausbau mehrerer Komponententypen). Deckungsgleich mit dem generischen `developer`-Tool-Satz — die Abgrenzung liegt im spezialisierten Fachwissen (State-Matrix, Variant-Contract-Konsum, A11y-Baseline), nicht im Tool-Zugriff.

**Kern-Workflow (Skizze):**

1. **Input lesen:** Screen-Spec (`ui-ux-designer`), Token-/Variant-Contract (`design-system-architect`), bestehende Komponentenbibliothek im Projekt (Glob/Grep — Konsistenz mit vorhandenen Patterns statt Parallelwelt).
2. **Props-Contract:** typisiertes Interface pro Komponente (TS-Interface o. ä.), abgeleitet aus der Variant-Matrix des Contracts — keine Variant "erfinden", die nicht im Contract steht (sonst zurück an `design-system-architect`).
3. **State-Matrix verbindlich:** jede interaktive/datengebundene Komponente MUSS `loading`/`error`/`empty`/`success` explizit behandeln (übernommen aus dem bereits bestehenden `ui-ux-designer`-Feld "States", jetzt tatsächlich implementiert statt nur spezifiziert) — kein Rendern "als ob" Daten immer da wären.
4. **A11y-Baseline einbauen** (nicht auditieren): semantisches HTML vor ARIA-Ersatz, Tastatur-Operabilität (Tab-Reihenfolge, sichtbarer Focus, keine Traps), passende ARIA-Pattern für Komponententyp (z. B. Combobox-Pattern). Grenze zu `accessibility-specialist`: hier wird die Baseline eingebaut, nicht gegen WCAG-Kriterien mit Level A/AA/AAA abgenommen — das bleibt Aufgabe des Audits.
5. **Motion-Implementierung** (siehe 4.3): Übergänge/Transitions nur über GPU-günstige Properties (`transform`/`opacity`), Werte aus den Motion-Tokens von `design-system-architect` (keine Hardcoded-`ms`-Werte in der Komponente), `prefers-reduced-motion`-Media-Query verpflichtend respektiert.
6. **Responsive Umsetzung** (siehe 4.4): Breakpoint-Tokens aus `design-system-architect` konsumieren, Mobile-first (Basis-Styles ohne Media-Query, Erweiterungen via `min-width`).
7. **Test-Grundgerüst:** Grundgerüst pro Komponente (Render-Test, Props-Varianten, State-Übergänge) — kein Vollcoverage-Anspruch, das bleibt `tester`/`e2e-tester`.
8. **Self-Verifikation:** wie im generischen `developer`-Workflow — Komponente tatsächlich rendern/beobachten (Dev-Server, Browser bei `WEB_PROJECT_ENABLED`), nicht nur auf grüne Unit-Tests vertrauen.
9. **Output:** Komponenten-Code + Props-Contract-Datei + Test-Grundgerüst.

**Delegationsflüsse:** Input von `design-system-architect` (Token-/Variant-Contract) + `ui-ux-designer` (Screen-Spec), per A2A-Envelope oder direkter `main_chat`-Delegation. Output an `accessibility-specialist` (WCAG-Vollaudit der implementierten Komponenten), `code-reviewer` (Code-Qualität), `tester`/`e2e-tester` (Testerweiterung). Bei fehlendem Contract-Eintrag zurück an `design-system-architect`, bei unklarem Screen-Verhalten zurück an `ui-ux-designer`.

### 4.3 Motion/Micro-Interactions — keine eigene dritte Rolle

**Bewertung des Vorschlags `motion-interaction-designer`:** verworfen. Begründung:

- Das Quell-Material selbst ist dünn (`animation/micro-interactions.md`: Hover/Loading/Transition, <300ms, `prefers-reduced-motion`) — kein eigenständiges Fachgebiet in der Tiefe von Farbtheorie oder Component-Engineering, eher eine Handvoll verbindlicher Regeln.
- Motion-*Werte* (Dauer, Easing) sind strukturell Tokens — sie gehören in dieselbe Systematik wie Farbe/Spacing/Breakpoints, also in `design-system-architect` (Schritt 6, Abschnitt 4.1).
- Motion-*Implementierung* (welche CSS-Property, welcher Trigger, `prefers-reduced-motion`-Handling im Code) passiert zwangsläufig an der Stelle, wo die Komponente gebaut wird — also im `frontend-component-engineer`-Workflow (Schritt 5, Abschnitt 4.2).
- Eine dritte Rolle nur für Motion würde eine dünne Delegationskette erzeugen (`design-system-architect` → `motion-interaction-designer` → Komponentenbau für denselben Schritt) ohne zusätzlichen fachlichen Mehrwert gegenüber der direkten Verteilung.

**Empfehlung:** keine eigene Rolle für Motion — als Workflow-Unterpunkt in `design-system-architect` und `frontend-component-engineer` mitführen (siehe 4.1/4.2). Falls sich in der Praxis zeigt, dass Motion-Anforderungen regelmäßig eigenständige, umfangreiche Arbeit erzeugen (z. B. komplexe orchestrierte Animationssequenzen, nicht nur Micro-Interactions), kann das später als eigener Vorschlag revisited werden — hier bewusst nicht vorgezogen.

### 4.4 Responsive/Mobile-Layout & CSS-Architektur — keine eigenen Rollen

**Bewertung:** verworfen, wie vom Auftrag vorgeschlagen — bestätigt nach Prüfung:

- Responsive-*Methodik* (welche Breakpoints, Mobile-first vs. Desktop-first, Grid- vs. Flexbox-Strategie als Projektentscheidung) ist eine Systematik-Frage, keine Implementierungsfrage → gehört zu `design-system-architect` (Breakpoint-Tokens, Abschnitt 4.1, Schritt 4).
- Responsive-*Umsetzung* (tatsächliche Media-Queries/Container-Queries pro Komponente) passiert beim Komponentenbau → `frontend-component-engineer` (Abschnitt 4.2, Schritt 6).
- Eine eigene Rolle würde hier künstlich zwischen Methodik und Umsetzung trennen, obwohl beide bereits an `design-system-architect`/`frontend-component-engineer` andocken — keine Lücke, die eine dritte/vierte Rolle rechtfertigt.

### 4.5 Zwei Vollrollen statt Rolle+Extension — Owner-Entscheidung

**Review-Empfehlung (v1.1, zur Nachvollziehbarkeit dokumentiert):** Der `concept-reviewer` empfahl in Runde 1, `frontend-component-engineer` zunächst nur als `developer-ext.md`-Extension auszuliefern, mit folgender Begründung: Kein aktuelles Consumer-Projekt mit Web-Frontend liegt im Repo vor (`agents/2-platform/` deckt `sharkord`, `homeassistant`, `agent-meta` selbst ab — keines ein Web-Frontend-Projekt), ein "wiederkehrender Bedarf" sei damit spekulativ. Zusätzlich sei die Rechtfertigung asymmetrisch: `design-system-architect` erzeugt ein eigenständiges Artefakt (starke `api-specialist`-Analogie), während `frontend-component-engineer` große Teile der `developer`-Maschinerie (Self-Verifikation, Test-Grundgerüst) dupliziert und dünneres Alleinstellungswissen hat.

**Owner-Entscheidung (v1.2, siehe Abschnitt 10):** Diese Empfehlung wird bewusst nicht übernommen. Beide Rollen werden direkt als Vollrollen spezifiziert. Das Argument "kein belegter wiederkehrender Bedarf" bleibt zutreffend, wird vom Owner aber nicht als Blocker gewertet — die Entscheidung, für UI-Implementierung von Anfang an eine eigenständige, klar benannte Rolle statt einer projektgebundenen Extension zu haben, ist eine bewusste Owner-Präferenz (u. a. Auffindbarkeit/Delegierbarkeit: eine Vollrolle erscheint als eigener, ansprechbarer Agent, eine Extension nicht).

**Kostenargument (weiterhin gültig, jetzt bewusst in Kauf genommen):** Jede zusätzliche Vollrolle wird in bis zu **6** Provider-Verzeichnisse gerendert (`.claude/agents/`, `.gemini/agents/`, `.opencode/agents/`, `.continue/agents/`, `.github/copilot/agents/`, `.mammouth/agents/` — Quelle: `config/ai-providers.yaml`; projektabhängig konfigurierbar, nicht zwingend alle 6 gleichzeitig aktiv). Zwei neue Vollrollen statt einer Rolle + einer Extension bedeuten entsprechend höheren Rendering-/Pflegeaufwand über `sync.py` — akzeptiert.

**Revisit-Kriterium entfällt:** Da keine Extension-Zwischenstufe existiert, gibt es keine Promotion-Frage mehr zu überwachen.

### 4.6 Anbindung an die bestehende Intent-Routing-Tabelle

Die Intent-Routing-Tabelle in `use-orchestrator.md` (gespeist aus `config/role-defaults.yaml` → `quality_pipelines[*].signal_keywords`) routet Nutzer-Intents ausschließlich auf **Pipeline-Ebene** (aktuell 6 Pipelines: `feature-lifecycle`, `quick-fix`, `bugfix`, `concept-development`, `refactor`, `docs-update`), nicht auf einzelne Rollen. Weder `ui-ux-designer` noch `api-specialist` — die beiden nächsten strukturellen Vorbilder — haben einen eigenen Eintrag in dieser Tabelle; beide sind laut Tier-Liste in `use-orchestrator.md` "optional"-Tier-Rollen, die `main_chat`/`orchestrator` ad hoc delegiert, wenn eine Aufgabe UI-Spezifikation bzw. API-Contract-Arbeit erfordert.

`design-system-architect` und `frontend-component-engineer` docken nach demselben Muster an — **kein neuer Eintrag** in der Routing-Tabelle. Konkret: Innerhalb der `feature-lifecycle`-Pipeline (`config/role-defaults.yaml:1414-1469`) ist der `implement`-Stage `plan-driven` mit `allowed_agents: [junior-developer, developer, senior-developer]`; dieser Satz müsste um `frontend-component-engineer` erweitert werden, sofern der `planner`-Plan einen UI-Komponentenbau-Schritt enthält. Enthält der Plan zusätzlich einen UI-Design-System-Schritt, delegiert `main_chat`/`orchestrator` vor oder parallel zum `implement`-Stage direkt an `design-system-architect` (analog zur heutigen Ad-hoc-Delegation an `ui-ux-designer`); das Ergebnis (Token-/Variant-Contract) fließt als zusätzlicher Kontext in den `implement`-Stage ein, den `frontend-component-engineer` dann bearbeitet.

Kein Vorschlag in diesem Konzept, `signal_keywords` für UI-Arbeit in die Pipeline-Tabelle aufzunehmen — das würde die Tabelle mit rollenspezifischen statt pipeline-spezifischen Einträgen verwässern (gleiches Muster wie bei den bestehenden UI-nahen Rollen).

## 5. UX-Research/Personas — keine eigene Rolle

**Bewertung des Punkts 8 aus dem Quell-Repo (`ux-research/user-persona-generator.md`):** bewusst nicht als neue Rolle vorgeschlagen, nach Prüfung bestätigt und um einen zusätzlichen kritischen Punkt erweitert:

- **Doppelarbeit vermeiden:** `ideation` deckt bereits "Value & goal" (wer profitiert, was ändert sich) ab, `requirements` formalisiert das. Eine dedizierte Persona-Rolle würde denselben fachlichen Raum (Nutzerbedürfnisse, Zielgruppen) mit einem anderen Artefakt-Format (Persona-Karte statt REQ) parallel bearbeiten — Risiko von Drift zwischen Persona-Aussagen und REQ-Formulierungen.
- **`ui-ux-designer` deckt das Nötige bereits ab:** Das Feld "Audience: Persona, role" existiert schon pro Screen (siehe `agents/1-generic/ui-ux-designer.md:37`) — für den tatsächlichen Bedarf beim UI-Entwurf reicht das.
- **Zusätzliches, bisher nicht genanntes Risiko:** Ein LLM-generierter "datengetriebener" Persona-Report ohne echte Nutzerforschungsdaten (Interviews, Analytics) suggeriert eine empirische Grundlage, die nicht existiert. Das ist beim Quell-Repo-Template selbst schon fraglich ("data-driven" ohne Datenquelle) und würde sich als eigenständige agent-meta-Rolle verschärfen, weil ein Rollen-Artefakt mehr Autorität suggeriert als eine Ad-hoc-Prompt-Antwort. Eine Persona-Rolle bräuchte zwingend eine explizite "Annahme, keine Erhebung"-Kennzeichnung, wenn sie überhaupt existiert.

**Empfehlung:** keine neue Rolle, kein neuer Workflow-Schritt. Falls später ein echter Bedarf entsteht (z. B. Persona-Synthese aus echten Nutzer-Interview-Transkripten), eher als Erweiterung der Knowledge Engine (`knowledge-ingestor` verarbeitet Interview-Quellen → Wiki-Konzept-Seite "Persona: X") denken als als eigene Ideation/Design-Rolle — hier nicht weiter ausgearbeitet.

## 6. Zusammenfassung: 2 neue Vollrollen, statt 3 neue Rollen

| Ursprünglicher Vorschlag | Entscheidung |
|---|---|
| `design-system-architect` | **Übernommen als Vollrolle**, inkl. Motion-Tokens und Breakpoint-Methodik als Workflow-Unterpunkte, Kontrast-Gate klar von `accessibility-specialist`-Audit abgegrenzt (Abschnitt 4.1) |
| `frontend-component-engineer` | **Übernommen als Vollrolle** (Owner-Entscheidung, Abschnitt 4.5/10, überstimmt die Review-Empfehlung einer `developer`-Extension) — inkl. Motion-Implementierung und Responsive-Umsetzung als Workflow-Unterpunkte |
| `motion-interaction-designer` | **Verworfen** — auf die Token-Ebene (`design-system-architect`) und die Implementierungs-Ebene (`frontend-component-engineer`, Abschnitt 4.2) verteilt (Abschnitt 4.3) |
| (nicht vorgeschlagen) Responsive/Mobile-Layout als eigene Rolle | **Verworfen**, wie vorgeschlagen bestätigt (Abschnitt 4.4) |
| (nicht vorgeschlagen) UX-Research/Personas als eigene Rolle | **Verworfen**, wie vorgeschlagen bestätigt, mit zusätzlichem Autoritäts-Risiko-Hinweis (Abschnitt 5) |

## 7. Offene Fragen für Review

| # | Frage | Warum offen |
|---|---|---|
| 1 | Reihenfolge der Ausarbeitung: erst `design-system-architect` (liefert den Contract) oder beide Rollen parallel entwerfen? | Empfehlung: `design-system-architect` zuerst, da `frontend-component-engineer` dessen Contract-Format als Eingabe braucht — Owner-Bestätigung sinnvoll vor Übergabe an `requirements`. |
| 2 | Wie generisch muss `frontend-component-engineer` bezüglich Framework bleiben (React/Vue/Angular/Web-Components)? Ein Platzhalter `{{FRONTEND_FRAMEWORK}}` reicht vermutlich, aber Variant-Pattern-Umsetzung (CVA ist React/Tailwind-geprägt) ist nicht 1:1 auf alle Frameworks übertragbar. | Betrifft, wie stark Abschnitt 4.2 Schritt 2 (Props-Contract) framework-neutral bleiben kann, ohne beliebig vage zu werden. |
| 3 | Token-Ausgabeformat: CSS Custom Properties, Tailwind-Config, JSON (Design-Tokens-Community-Group-Format), oder alle drei parallel mit einer Quelle? | Betrifft Tool-Bedarf/Bash-Nutzung in `design-system-architect` (Abschnitt 4.1) — muss vor Template-Ausformulierung entschieden werden. |
| 4 | Soll `design-system-architect` bestehende Design-System-Skelette (`{{SNIPPETS_DIR}}/design-system-skeleton.yaml`, von `ui-ux-designer` genutzt) direkt als Pflicht-Input lesen, oder eigenständig auch ohne vorherige `ui-ux-designer`-Spec arbeiten können (z. B. bei kleinen Projekten ohne separate Spec-Phase)? | Betrifft, wie strikt die Delegationskette (Abschnitt 3) erzwungen wird vs. Kurzschluss-Modus erlaubt ist. |
| 5 | `frontend-component-engineer` vs. bestehende `senior-developer`/`principal-developer`-Rollen: Gibt es dort bereits UI-Spezialwissen, das dupliziert würde? | Noch nicht geprüft in diesem Konzept — vor Template-Ausformulierung gegenlesen. |

## 8. Nächste Schritte

1. Owner-Review dieses Konzepts, insbesondere Frage 1 (Reihenfolge) und Frage 5 (Abgleich mit `senior-developer`/`principal-developer`) — die frühere Rollen-vs.-Snippet-Frage aus v1.0/v1.1 ist mit der Owner-Entscheidung in Abschnitt 10 entschieden.
2. Bei Freigabe: Übergabe an `requirements` zur Formalisierung — REQ-Formulierung für `design-system-architect` UND `frontend-component-engineer` (beide Vollrollen), Kategorie "Agenten-Templates" gemäß `CLAUDE.md`.
3. Template-Ausformulierung: `agents/1-generic/design-system-architect.md` + `agents/1-generic/frontend-component-engineer.md` inkl. Token-Skelett und Variant-Contract-Skelett — erst nach REQ-Klärung, nicht Teil dieses Konzepts.
4. `feature-lifecycle`-Pipeline-Eintrag prüfen: `implement`-Stage `allowed_agents` ggf. um `frontend-component-engineer` erweitern (Abschnitt 4.6).

## 9. Review-Revision (v1.0 → v1.1)

Änderungen nach `concept-reviewer`-Feedback (STATUS: REVISE, 2 major/4 minor/1 info):

- **M1 (blocking):** Kontrast-Ownership zwischen `design-system-architect` (Design-time-Gate auf Token-Paarungen) und `accessibility-specialist` (alleinige WCAG-Audit-Autorität) explizit getrennt (Abschnitt 4.1, Schritt 3).
- **M2 (blocking):** Vormalige "Frage 5" (Rollen vs. Snippet) als konkrete Sequenzierungs-Entscheidung formuliert statt offen gelassen — in v1.1 zunächst als Rolle+Extension entschieden (durch Owner-Entscheidung v1.2, Abschnitt 10, seither überholt).
- **m1:** Provider-Verzeichnis-Zahl korrigiert (4 → bis zu 6, Quelle `config/ai-providers.yaml`).
- **m2:** Neuer Abschnitt 4.6 zur Anbindung an die Intent-Routing-Tabelle ergänzt.
- **m3:** `TodoWrite` bei `design-system-architect` ergänzt, `Bash`-Bedarf bei beiden knapp begründet.
- **m4:** Messbares Revisit-Kriterium für die Snippet→Vollrolle-Promotion ergänzt (in v1.2 wieder entfernt, da keine Extension-Stufe mehr existiert).
- **info:** Handoff-Auflage ergänzt (Abschnitt 1) — Template-Ausformulierung arbeitet nur aus der abstrahierten Konzeptliste, nicht aus den Quell-Repo-Dateien selbst.

Unverändert gegenüber v1.0 (laut Review als stark bewertet): Rollenabgrenzungs-Tabelle (Abschnitt 2), Alternativen-Analyse Motion/Responsive/Personas (Abschnitte 4.3–4.4, 5), Copyright-Handling (Abschnitt 1).

## 10. Owner-Override (v1.1 → v1.2)

Nach Abschluss des Reviews (v1.1, VERDICT: APPROVE) und Vorlage an den Owner kam die explizite Rückmeldung: **beide Rollen sollen von Anfang an als Vollrollen umgesetzt werden**, nicht `design-system-architect` als Rolle und `frontend-component-engineer`-Wissen nur als `developer`-Extension.

**Was sich ändert:** `frontend-component-engineer` wird wie `design-system-architect` als eigenständiges `agents/1-generic/`-Template spezifiziert (Abschnitt 4.2). Abschnitte 3, 4.2–4.6, 6, 7, 8 entsprechend aktualisiert.

**Was unverändert bleibt:** Die fachliche Rollenabgrenzung (Abschnitt 2), alle Workflow-Skizzen (Abschnitte 4.1–4.2), die Kontrast-Ownership-Trennung (M1), die Alternativen-Analyse (Motion/Responsive/Personas) und das Copyright-Handling. Der Review-Befund selbst (fehlendes Consumer-Projekt, Asymmetrie der Rechtfertigung) wird nicht widerlegt, sondern als bekanntes, akzeptiertes Risiko dokumentiert (Abschnitt 4.5) — die Owner-Präferenz für zwei benannte, delegierbare Vollrollen wiegt hier stärker als das Kosten-/Evidenz-Argument des Reviews.

**Für `requirements`/spätere Umsetzung relevant:** Da kein Revisit-Kriterium mehr existiert (es gibt keine Extension-Zwischenstufe), sollte bei der tatsächlichen Nutzung im Auge behalten werden, ob `frontend-component-engineer` in der Praxis genug eigenständiges Fachwissen trägt, um die Vollrolle zu rechtfertigen — falls nicht, wäre eine spätere Rückstufung zur Extension eine denkbare, aber hier nicht geplante Korrektur.
