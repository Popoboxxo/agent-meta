---
description: Web-Plattform SEO-Checkliste — Local SEO, Technical SEO, Schema Markup (gilt für alle Agenten in Web-/Marketing-Site-Projekten)
---

# SEO-Best-Practices (Web)

Checkliste für Rollen wie `developer`, `ui-reviewer`, `tester`/`qa` in Web- und
Marketing-Site-Projekten. Aktiv, sobald `platforms:` die Plattform `web` enthält.

> Inhalte sind agent-meta-gepflegte Defaults. Standards (Core-Web-Vitals-Metriken,
> Rich-Snippet-Typen) ändern sich — vor jeder Verwendung Aktualität gegen die
> verlinkten Quellen prüfen.

## Local SEO

- **Google Business Profile** vollständig gepflegt (Kategorie, Öffnungszeiten, Fotos, Posts).
- **NAP-Konsistenz** (Name, Address, Phone) zeichengleich über Website, GBP und alle Verzeichnisse.
- **Lokale Keyword-Optimierung** in Titles, H1, Meta-Descriptions und sichtbarem Inhalt.
- Lokale **Structured Data** (`LocalBusiness`, bei Bedarf Subtypen) hinterlegt.

## Technical SEO

- **Mobile-first-Indexing:** mobile Variante ist die maßgebliche; kein Content nur im Desktop-Layout.
- **Core Web Vitals** im grünen Bereich:
  - **LCP** (Largest Contentful Paint) ≤ 2,5 s
  - **INP** (Interaction to Next Paint) ≤ 200 ms — hat FID zum 2024-03 als Core-Web-Vital abgelöst
  - **CLS** (Cumulative Layout Shift) ≤ 0,1
- Saubere `<title>`/`<meta name="description">` pro Seite, keine Duplikate.
- `robots.txt` + XML-Sitemap vorhanden und eingereicht; `canonical`-Tags gesetzt.
- Semantisches HTML, eine `<h1>` pro Seite, logische Heading-Hierarchie.

## Schema Markup (Structured Data)

- **JSON-LD** als Format (von Google empfohlen), im `<head>` oder `<body>`.
- Passende Typen je Seite: `Organization`/`LocalBusiness`, `BreadcrumbList`,
  `Product`, `FAQPage`, `Article` — nur auszeichnen, was sichtbar auf der Seite steht.
- Auf **Rich-Snippet-Eligibility** validieren (Rich Results Test / Schema-Validator).

## Quellen

- Local SEO Guide: <https://backlinko.com/local-seo-guide>
- Core Web Vitals (INP): <https://web.dev/articles/inp>
- Structured Data / JSON-LD: <https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data>
