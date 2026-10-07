---
description: Web-Plattform Accessibility-Checkliste — WCAG 2.2 AA inkl. Mobile-Kriterien (gilt für alle Agenten in Web-/Marketing-Site-Projekten)
---

# Accessibility-Best-Practices (WCAG 2.2 AA, Web)

Prüfpunkte für Rollen wie `developer`, `ui-reviewer`, `tester`/`qa`. Aktiv, sobald
`platforms:` die Plattform `web` enthält. Zielniveau: **WCAG 2.2 Level AA**.

> agent-meta-gepflegte Defaults. WCAG entwickelt sich weiter — vor Verwendung
> gegen die verlinkte Spezifikation auf Aktualität prüfen.

## Mobile-Kriterien (WCAG 2.2, besonders beachten)

- **Target Size (Minimum) — 2.5.8 (AA):** interaktive Ziele mindestens **24×24 CSS-px**;
  für Touch-Flächen die praktische Empfehlung **44×44 px** anstreben (ausreichender
  Abstand zwischen klickbaren Elementen).
- **Reflow — 1.4.10 (AA):** Inhalt ohne horizontales Scrollen bei 320 CSS-px Breite
  (entspricht 400 % Zoom), kein Informations-/Funktionsverlust.
- **Pointer Gestures — 2.5.1 (A):** jede Multipoint-/Pfad-Geste (Swipe, Pinch) hat
  eine Single-Pointer-Alternative.
- **Dragging Movements — 2.5.7 (AA):** per Drag erreichbare Funktion auch ohne Ziehen bedienbar.

## Allgemeine AA-Pflichtpunkte

- **Kontrast — 1.4.3:** Text ≥ 4,5:1 (großer Text ≥ 3:1); UI-Komponenten/Grafik ≥ 3:1 (1.4.11).
- **Tastaturbedienbarkeit — 2.1.1:** alle Funktionen per Tastatur, keine Keyboard-Traps.
- **Focus Visible — 2.4.7** und **Focus Not Obscured (Minimum) — 2.4.11 (AA, neu in 2.2).**
- **Name/Role/Value — 4.1.2:** korrekte semantische Rollen bzw. ARIA; Formularfelder mit `<label>`.
- **Alt-Texte** für informative Bilder; dekorative Bilder `alt=""`.
- **Seitensprache** (`<html lang>`), aussagekräftige `<title>`, logische Heading-Struktur.
- **Accessible Authentication (Minimum) — 3.3.8 (AA, neu in 2.2):** kein kognitiver
  Funktionstest ohne Alternative (z. B. Passwort-Paste/Passwortmanager erlauben).

## Verifikation

- Automatisiert (axe-core o. ä.) **plus** manuelle Tastatur-/Screenreader-Prüfung —
  automatische Tools decken nur einen Teil der Kriterien ab.

## Quellen

- WCAG 2.2 Mobile: <https://www.w3.org/TR/wcag2mobile-22/>
- WCAG 2.2 Standard: <https://www.w3.org/TR/WCAG22/>
