# CLAUDE.md Review & Verbesserung

## Sofort nach einem Fehler

```
1. Read CLAUDE.md
2. Passende Sektion finden
3. Regel im Imperativ formulieren:
   GUT:     "KEIN `any` — Typen explizit"
   SCHLECHT: "Vermeide any wenn möglich"
4. Außerhalb des managed blocks einfügen
5. Verifizieren: "Was steht in deiner CLAUDE.md über [Thema]?"
```

Nie in den `<!-- agent-meta:managed-begin/end -->` Block schreiben.

## Review-Runde (alle 2–3 Wochen)

1. **Fehlermuster:** "Welche Fehler hat Claude wiederholt gemacht?"
   → Konkrete Regeln formulieren + eintragen.

2. **Veraltetes:** "Welche Regeln stimmen nicht mehr?"
   → Entfernen oder aktualisieren.

3. **Fehlende Bereiche:** "Welche häufigen Aufgaben kennt Claude noch nicht gut?"
   → Neue Sektion oder Extension anlegen.

4. **Länge:** Empfehlung ≤500 Wörter.
   → Nebensächliches in Extensions auslagern.

## Qualitätsprinzipien

| Gut | Schlecht |
|-----|---------|
| Imperativ: "KEIN `any`" | "Vermeide any wenn möglich" |
| Konkret: "Tests in `src/__tests__/`" | "Tests gut ablegen" |
| Mit Kontext: "Kein `window` — läuft in Node" | Ohne Grund: "Kein window" |

## Wo hin?

| Inhalt | Ziel |
|--------|------|
| Projektkontext, Tech-Stack, Architektur | `CLAUDE.md` |
| Gilt für alle Agenten | `.claude/rules/` |
| Nur für einen Agent-Typ | `.claude/3-project/<prefix>-<rolle>-ext.md` |
| Gilt für alle Projekte | Feedback → `rules/1-generic/` |
