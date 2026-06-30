---
name: template-migration-pitfalls
description: Root-cause bugs bei Classic→Modern Template-Port; Prävention via Checkliste
metadata:
  type: feedback
---

# Template-Migration-Pitfalls: Classic → Modern

## Die Regel

Beim Port von `agents/1-generic/<role>.md` (Classic/Markdown) nach `agents/1-generic-modern/<role>.md` (Modern/6-Block-XML) sind **{{#if}}-Conditional-Guards die Hauptfehlerquelle** — gehen leicht verloren und führen zu konkateniertem/statischem Output statt korrekter bedingter Logik.

**Why:** Der Port ist manuell, und es ist leicht zu übersehen, dass bedingte Blocks (z.B. Flags wie SE-Rollen, DoD-Optionen) in {{#if}}-Conditional-Blöcke gehören, nicht einfach angehängt werden dürfen.

## Betroffene Dateien (Session 2026-07-01)

- `agents/1-generic-modern/orchestrator.md` v7.2.0 (Bugs in Commits 42963fe, 139eab7, 3e19c9b, 837587b behoben)
- `agents/1-generic-modern/developer.md` (noch nicht auf denselben Bug-Check untersucht)

## Checkliste für zukünftige Ports

1. **{{#if}}-Guards erhalten**
   - Jeder Platzhalter mit bedingter Logik (`{{CONDITION}}`, `{{FLAG}}`) muss in einem `{{#if CONDITION}}`-Block stehen
   - Niemals direkt konkatenieren: `{{#if SE_ENABLED}}...{{/if}}`
   - Testen: Pro Wert-Kombinatoire den Template-Output prüfen

2. **Dry-Run Diff gegen Classic**
   ```bash
   git diff agents/1-generic/<role>.md agents/1-generic-modern/<role>.md | grep -E '{{|#if' | head -50
   ```
   - Sollten keine neuen ungeschützten Platzhalter eingeführt sein
   - Bedingte Logik sollte klarer sein (explizit in {{#if}}-Blöcken)

3. **6-Block-Struktur validieren**
   ```bash
   python scripts/validate-modern-templates.py --strict agents/1-generic-modern/<role>.md
   ```
   - Exit 0 = OK, Exit 1 = Warning, Exit 2 = Fehler
   - Alle 6 Blöcke vorhanden? Richtige Reihenfolge?

4. **Token-Vergleich aktualisieren** (optional)
   ```bash
   python scripts/token-counter.py --role <role> --before agents/1-generic/<role>.md --after agents/1-generic-modern/<role>.md
   ```
   - Token-Reduktion sollte 30–60% sein
   - Größere/kleinere Differenzen deuten auf Fehler hin

## Auswirkungen wenn ignoriert

| Auswirkung | Symptom | Test |
|------------|--------|------|
| Konkatenation statt Blöcke | Flags erscheinen als "truefalsefalse" statt klarer Struktur | grep "true\|false" im Generated Agent |
| Statischer Output | Bedingte Flags zeigen Wert trotz false-Flag (z.B. "Pflicht" bei `CONDITION: false`) | Prüfe generierte Agent-Datei gegen config |
| {{#if}} in Ausgabe | Prompt enthält noch Raw-Tags statt aufgelöst | grep "{{#if" im Generated Agent |

## Verknüpfte Begriffe

[[singleton-orchestrator-hitp-proxy]] — HITL-Deadlock war zweiter großer Bug dieser Session (gelöst via main_chat-Proxy-Anerkennung)
[[barrier-protocol-active]] — BARRIER-Refactor von passiv zu aktiv formalisiert

---

**Letzter Test:** agents/1-generic-modern/orchestrator.md v7.2.0 (alle Bugs behoben)
**Referenz-Implementierung:** agents/1-generic-modern/_reference-agent.md v1.0.0 (Underscore = nicht generiert, didaktisch)
