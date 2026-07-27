---
type: "Concept"
title: "Konzept: Instruction Bleed Risk in Text-Level Composition"
description: "Risiko- und Governance-Modell für Text-Level-Composition (extends + patches): Vermeidung ungewollter Verhaltensänderungen und widersprüchlicher Instruktionen."
tags: [concept, governance, composition, status:active]
timestamp: "2026-07-27"
resource: "AGENTS.md"
migrated_from: "AGENTS.md"
---
# Konzept: Instruction Bleed Risk in Text-Level Composition

> Status: **Umgesetzt — aktiv**  
> Verwandt: [Agent Composition — extends & patches](../topics/agent-composition.md), [Agent-Meta Composition System](../entities/composition-system.md)  
> Betroffen: `AGENTS.md`, `CLAUDE.md`, `scripts/lib/composition.py`  

---

## 1. Was ist Instruction Bleed?

Bei der textbasierten Vererbung und Patch-Zusammensetzung (**Text-Level Composition**) via `extends:` und `patches:` (`append-after`, `replace`, `delete`, `append`) in `2-platform/` und `3-project/` Agenten besteht die Gefahr von **Instruction Bleed**.

**Instruction Bleed** bezeichnet das Phänomen, dass Anweisungen oder Verhaltenslogiken aus einer höheren Schicht unbeabsichtigt in andere Abschnitte "überbluten" oder im final generierten Agenten-Prompt widersprüchliche Befehle erzeugen.

> **Empirische Grundlage:** Das Instruction Bleed Paper (arXiv:2606.26356) belegt Cross-Module-Interference bei Text-Level-Composition als eine der häufigsten Ursachen für unerwartetes Agentenverhalten in komplexen Multi-Layer-Architekturen.

---

## 2. Typische Ursachen von Instruction Bleed

1. **Additive Patches (`append-after`)**: Wenn eine Section additiv erweitert wird, die in der übergeordneten Schicht semantisch umdefiniert wurde, entstehen zwei gegensätzliche Handlungsanweisungen im selben Prompt.
2. **Anchor-Shift**: Eine Verschiebung oder Umbenennung der Überschrift (`## Heading`) im Base-Template führt dazu, dass ein Patch an falscher Stelle greift oder fehlschlägt.
3. **Kontextuelle Verwirrung**: Verhaltensanweisungen für eine Plattform überdecken generische Sicherheitsregeln des `1-generic/` Base-Templates.

---

## 3. Governance: Die Pre-Patch Commit-Checkliste

Vor jedem Patch-Commit muss der Entwickler folgende drei Prüfpunkte verifizieren:

- [ ] **Semantik-Prüfung**: Überschreibt oder ergänzt der Patch eine Section, die in der übergeordneten Schicht eine andere Semantik trägt?
- [ ] **Widerspruchs-Check**: Erzeugt `append-after` doppelte oder widersprüchliche Regelaussagen im generierten Enddokument?
- [ ] **Replace vs. Append**: Ist der Override vollständig (`replace`) oder additiv (`append-after`)? *Additiv birgt ein deutlich höheres Bleed-Risiko.*

---

## 4. Debugging & Validierung

`sync.py` unterstützt das Erkennen fehlerhafter Composition-Ergebnisse:
```bash
python scripts/sync.py --dry-run
```
In der `sync.log` werden alle angewendeten Patches protokolliert. Das Zieldokument in `.claude/agents/` (oder `.gemini/agents/`) sollte stets auf logische Konsistenz und Lesbarkeit hin überprüft werden.