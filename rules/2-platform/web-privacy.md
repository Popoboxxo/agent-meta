---
description: Web-Plattform Privacy-Checkliste — DSGVO/GDPR, Consent-first, Consent Mode v2, self-hosted Fonts (gilt für alle Agenten in Web-/Marketing-Site-Projekten)
---

# Privacy-Best-Practices (DSGVO/GDPR, Web)

Anforderungen für Rollen wie `developer`, `ui-reviewer`, `tester`/`qa`. Aktiv, sobald
`platforms:` die Plattform `web` enthält.

> agent-meta-gepflegte Defaults, keine Rechtsberatung. Enforcement und Vorgaben
> (Consent Mode, Font-Handling) ändern sich — vor Verwendung gegen die verlinkten
> Quellen auf Aktualität prüfen.

## Consent-first (aktives Opt-in)

- **Kein Tracking vor Einwilligung:** Analytics-, Marketing- und Fingerprinting-Skripte
  erst nach aktivem Opt-in laden/ausführen.
- **Cookie-Banner:** gleichwertige „Ablehnen"- und „Akzeptieren"-Option, keine Dark Patterns,
  granulare Kategorie-Auswahl, Einwilligung widerrufbar (erneuter Zugriff auf die Einstellungen).
- **Tracking-Delay:** Tags/Pixel bleiben bis zur Zustimmung geblockt (Consent-gesteuertes Laden).

## Google Consent Mode v2

- **Pflicht seit 2024-03** für GA4 / Google Ads bei Nutzern im EWR.
- Default-Consent-State **vor** Tag-Load auf `denied` (`ad_storage`, `analytics_storage`,
  `ad_user_data`, `ad_personalization`), Update nach Einwilligung über die Consent-API / den CMP.
- Integration über Google Tag Manager Consent Mode bzw. einen zertifizierten CMP verifizieren.

## Self-hosted Fonts

- **Keine CDN-geladenen Fonts ohne Einwilligung** (Google Fonts via CDN überträgt die IP —
  DSGVO-relevant, vgl. LG-München-Rechtsprechung).
- Webfonts **lokal selbst hosten** und per `@font-face` einbinden.

## Weitere Pflichtpunkte

- **Datenschutzerklärung** und **Impressum** vorhanden, verlinkt und aktuell.
- Formulardaten nur zweckgebunden und per TLS übertragen; Datensparsamkeit.
- Drittanbieter-Einbettungen (Maps, YouTube, reCAPTCHA) erst nach Consent laden.

## Quellen

- Google Fonts & DSGVO: <https://usercentrics.com/knowledge-hub/google-fonts-gdpr-compliant/>
- GDPR Cookie Consent: <https://www.consenteo.com/knowledge-hub/GDPR/gdpr_cookie_consent_2026>
- Google Consent Mode: <https://support.google.com/analytics/answer/9976101>
