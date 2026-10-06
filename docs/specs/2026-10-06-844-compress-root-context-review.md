---
review-of: SPEC-844-COMPRESS-ROOT-CONTEXT-2026-10-06
reviewer: concept-reviewer
date: 2026-10-06
verdict: APPROVED
---

# Spec-Review — Compress Generated Root Context (#844)

> Trace-Anker (reviewed): `spec-id: SPEC-844-COMPRESS-ROOT-CONTEXT-2026-10-06`
> Verdikt: **APPROVED**

## Scope

Unabhängiges Review der Spec `docs/specs/2026-10-06-844-compress-root-context.md`
(Status vor Review: `proposed`). Geprüft: zentraler Befund (#540-Infrastruktur
bereits gebaut, nur inaktiv), die drei Design-Fragen-Auflösungen, AC-6
("newline-squashing nicht reproduzierbar"), Vollständigkeit der Pflichtsektionen,
Trace-Anker, Approval-Marker, No-Placeholder, Wissensverlust-Gegenprobe.
Alle Zeilenreferenzen gegen den realen Code stichprobengeprüft — nicht auf Zusage
übernommen.

## Verifikationsergebnisse (1 Zeile pro Punkt)

1. **Zentraler Befund (COMPACT_MODE bereits gebaut, inaktiv):** BESTÄTIGT.
   `.meta-config/project.yaml` steht real auf `context_file.mode: full` +
   `oversize_acknowledged: true` (Z. 300-304); aktive Provider Claude/Opencode/Gemini
   (Z. 6-9). Die gesamte Compact-Pipeline existiert und ist verdrahtet.
2. **`config.py::build_variables` COMPACT_MODE-Ableitung:** BESTÄTIGT.
   Z. 1388 `variables["COMPACT_MODE"] = "true" if _context_mode == "compact" else "false"`,
   safe-side-Default auf `false` bei fehlendem/ungültigem Key (Z. 1384-1388). Spec-Zitat
   "1375-1388" trifft (Kommentarblock ab 1375, Logik 1384-1388).
3. **`bootstrap.py:285-314` Gemini-Compact-Pfad:** BESTÄTIGT. `generate_gemini_bootstrap_instructions`
   hat `compact: bool = False` (Z. 286); `compact=True` liefert den kurzen 6-Zeilen-Block
   statt der Pro-Agent-Aufzählung (Z. 300-314).
4. **`agent_sync.py:1316` Wiring:** BESTÄTIGT. `compact=variables.get("COMPACT_MODE") == "true"`
   (Z. 1316); Provider-Konditionalität zusätzlich durch `action != "none"`-Gate (Z. 1311).
5. **`provider-bootstrap.yaml` Provider-Tabelle:** BESTÄTIGT. Claude/Opencode/Copilot/
   Mammouth/Codex/KimiCode = `action: none`; Gemini = `inject-bootstrap-instructions`
   (generated); ZCode = api-based/static; Continue = update-config. Tabelle in §2 F1 korrekt.
6. **`rules-presets.yaml` 8-Kernregel-Taxonomie:** BESTÄTIGT. Kommentar Z. 106-108 listet
   branch-guard, commit-conventions, language, speech-mode, no-worktree-isolation,
   dod-criteria, use-orchestrator (7 preset-exempt) + mcp-guardrails separat (Z. 109-110) = 8.
   Spec-Zitat "104-110" leicht verschoben (real 106-110), inhaltlich korrekt.
7. **`context.py:1503-1569` `_COMPACT_PLATFORM_RULES` / `compact_embedded_rule`:** BESTÄTIGT.
   Genau 4 Einträge (sync-interface, architecture, conventions, admin-ui), KEIN branch-guard.
   Präambel vor erster H2 wird immer behalten (`keep_current = True`, Z. 1562) → `"keep": ()`
   für branch-guard ist korrekt/ausreichend. Unbekannter Stem → content unverändert (Z. 1557-1559).
8. **Design-Frage 1 (Bootstrap provider-konditional):** BESTÄTIGT durch Punkt 4/5 — AC(a)
   bereits erfüllt, nur Dichte (compact) ist der Hebel.
9. **Design-Frage 2 (Agent-Tabelle write-only, 1 Zeile/Agent):** PLAUSIBEL/BESTÄTIGT. Routing
   liest `role-defaults.yaml` (nicht die gerenderte Tabelle); Compact-Branch in
   `agents-table.md` existiert. Keine Re-Parse-Abhängigkeit gefunden.
10. **Design-Frage 3 (Hard-Gate vs. Referenzdetail):** BESTÄTIGT. `branch-guard.md` real =
    H1 + 2-Zeilen-Direktive (Z. 1-3) + genau 2 H2-Abschnitte ("Guard-Terminologie…",
    "Bekannte Grenzen", Z. 5-34). Beide H2 nicht in einem `keep`-Set → werden zu 1 Pointer.
    Konvention wird angewendet, keine neue erfunden.
11. **AC-6 (newline-squashing nicht reproduzierbar):** BESTÄTIGT. Real gerendertes
    `AGENTS.md` (Z. 46-48) und `CLAUDE.md` (Code-Konventionen-Sektion) zeigen Bullets
    mehrzeilig, ein Bullet pro Zeile — kein Collapse. Gegen-Erklärung geprüft:
    `tests/test_platform_defaults_resolver.py:68-72` belegt den `"; "`-Join ausschließlich
    beim additiven `CODE_CONVENTIONS+`-Merge über MEHRERE `platforms:`-Quellen; agent-meta
    hat nur `platforms: [agent-meta]` → Mechanismus greift hier nicht. AC-6 als
    Untersuchungs-Gate (OQ-1) statt Code-Fix ist korrekt begründet.
12. **Schema-Gültigkeit `mode: compact`:** BESTÄTIGT. `project-config.schema.json`
    context_file.mode enum = ["full","compact"] (Z. 1013-1016), default "full". Kein
    Schema-Change nötig — Spec-Aussage korrekt.

## Spec-Review-Pflichtchecks (§7.1 / §8)

| Check | Status |
|-------|--------|
| Pflichtsektionen (Problem/Ziel/Nicht-Ziele, Interface Contracts, Datenfluss, Acceptance Criteria, Offene Fragen + Risiken) | grün — alle vorhanden (§1, §3, §4, §5, §7) |
| Datei-Liste | grün (§6, inkl. explizit markierter "KEINE ÄNDERUNG"-Verifikationen) |
| Test-Plan | grün (§8) |
| Trace-Anker (`spec-id`) | grün — Frontmatter + §9, referenzierbar vom Plan |
| Approval-Marker | grün — konsistent zum Review-Stand (Frontmatter + Body) |
| No-Placeholder | grün — kein TODO/TBD/`<...>`; `{{#if COMPACT_MODE}}` sind zitierte Template-Syntax, keine offenen Platzhalter |

## Findings

### critical: 0
### major: 0

### minor: 0

### info (keine Aktion erforderlich)

- **INFO-1 (Konsistenz, Zeilenreferenzen):** Zwei Zitate leicht verschoben —
  `rules-presets.yaml` "104-110" (real 106-110), `config.py` "1375-1388" (Logik 1384-1388).
  Inhaltlich in beiden Fällen korrekt; kein Handlungsbedarf.
- **INFO-2 (Vollständigkeit, AC-Abdeckung):** Die Compact-Zweige von
  `project-metadata.md` (Verzeichnisbaum → 1-Zeiler, mehrzeilige Build/Dev-Befehle) und die
  Knowledge-/MCP-Hints werden im Datenfluss (§4) genannt, aber nicht per eigenem AC gesperrt.
  Akzeptabel: pre-existing #540-Infrastruktur mit eigenen Tests
  (`test_project_metadata_full_mode_structure.py`). Empfehlung für den Plan: den
  realen Vorher/Nachher-Diff (OQ-4) explizit auch für diese Blöcke sichtbar machen.
- **INFO-3 (Wissensverlust-Gegenprobe):** Genuin adressiert. IC-1 Wirkradius isoliert
  die Änderung auf den Opencode/Gemini-`AGENTS.md`-Pfad; Claudes natives
  `.claude/rules/branch-guard.md` und der Full-Modus bleiben byte-identisch (AC-4 sperrt
  das als Test); kanonischer Quelltext unverändert; Agent-Tabellen-Beschreibung bleibt
  einen `Read` entfernt; Routing liest `role-defaults.yaml`. Verifikationskette
  AC-2 (Zeilenzahl) + AC-4 (Section-Diff) + AC-5 (Validator) + OQ-4 (realer Sync-Lauf)
  ist ausreichend, um "silent drop" auszuschließen.

## Verdikt + Begründung

**APPROVED.**

Der zentrale Befund ist am realen Code vollständig verifiziert: Die #540-Kompressions-
Infrastruktur (COMPACT_MODE-Ableitung, Gemini-Compact-Bootstrap, agents-table Compact-
Branch, `compact_embedded_rule`, context-size-Validator) existiert und ist verdrahtet;
der einzige Grund für die großen Root-Context-Dateien ist `context_file.mode: full` im
eigenen Repo. Die einzige echte Produktionscode-Änderung (ein `branch-guard`-Eintrag in
`_COMPACT_PLATFORM_RULES`) ist durch die H2-Struktur von `branch-guard.md` und die
`"keep": ()`/Präambel-Mechanik korrekt begründet. Alle drei Design-Fragen sind mit
belastbarem Code-Beleg aufgelöst; die Alternativen (Pointer-Ersatz statt 1-Zeile/Agent;
neue Taxonomie statt bestehender Konvention) sind explizit gewogen und verworfen. AC-6
ist mit nachvollziehbarer, am Code belegter Gegen-Erklärung als Untersuchungs-Gate statt
Scheinlösung geführt — kein spekulativer Fix. Pflichtsektionen, Trace-Anker, Approval-
Marker und No-Placeholder sind alle grün. Die Wissensverlust-Risiken sind benannt und
durch die AC-Kette prüfbar abgesichert. Keine major/critical Findings.

**Auflagen für den Plan (keine Blocker):** OQ-4 verlangt einen realen
`python scripts/sync.py && --validate`-Lauf mit protokollierten Vorher/Nachher-
Zeilenzahlen als Beleg für AC-2/AC-5 — dieser Mess-Schritt ist Pflicht im Plan,
da die exakte Zeilenersparnis statisch nicht vorhersagbar ist.

## Nächster Schritt

Pipeline `quality_pipelines.concept-driven-dev`: specify → **review (APPROVED)** →
approve → plan. Der Plan referenziert den Trace-Anker
`SPEC-844-COMPRESS-ROOT-CONTEXT-2026-10-06`.
