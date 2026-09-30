# Evidence — Entry-/Kontextdatei-Verifikation (Phase B)

- **Datum:** 2026-09-30 · **Repo:** `/home/hermes/repos/agent-meta` · **Branch/HEAD:** `feat/provider-audit-opencode-v2` @ `65a493ec` (read-only, keine git-Mutation).
- **Generator-Hashes:** `scripts/sync.py` `e786b1b9d9733c7d1de65a21877fdd5ac7d84e2862c8e072b8f6385a07e5bf2f`; `scripts/lib/context.py` `faed7f6d4bddb14efe45dd700499526ec37510d724a1532226c3395e998cd350`.
- **Scratch:** `/var/tmp/opencode-audit/entryfiles/single-<Provider>/` (9) + `multi-all/` (alle 9). `sync.py` wurde **nur** dort ausgeführt (nie im Repo-Root). Repo-Schreiboperation: nur diese Datei.
- **Config-Basis:** `01-minimal-claude` (5 Rollen: orchestrator, developer, git, tester, documenter; `dod-preset: standard`), Provider-Aktivierung via `ai-providers:` (analog `02-multi-provider`/`07-new-providers`).
- **Opencode-v2:** kein eigener Config-Fall — `grep -rn "opencode-v2" config/ scripts/lib/` findet **keine** Config-Option; `sync.py` kennt genau einen Provider `Opencode`. „opencode-v2" ist Branch-/Runtime-Name (`docs/analysis/evidence/2026-09-30-runtime-opencode-v2.md`), keine Generator-Achse.
- **Verdikt-Key:** VERIFIED / REFUTED / STATIC (Quelle) .

---

## 1. Existierende Entry-Dateien (Ist-Zustand je Scratch-Projekt)

| Provider | AGENTS.md | CLAUDE.md | .continue/rules/project-context.md | .github/copilot/COPILOT.md | MAMMOUTH.md |
|---|---|---|---|---|---|
| Claude | – | **YES** | – | – | – |
| Gemini | **YES** | – | – | – | – |
| Opencode | **YES** | – | – | – | – |
| Codex | **YES** | – | – | – | – |
| KimiCode | **YES** | – | – | – | – |
| Continue | – | – | **YES** | – | – |
| Copilot | – | – | – | **YES** | – |
| Mammouth | – | – | – | – | **YES** |
| ZCode | **YES** | – | – | – | – |
| multi-all | **YES** | **YES** | **YES** | **YES** | **YES** |

Jedes Single-Provider-Projekt erzeugt **genau eine** Entry-Datei (`resolve_providers` → `context_file`). `multi-all` erzeugt alle 5 (AGENTS.md geteilt von Gemini/Opencode/Codex/KimiCode/ZCode).

---

## 2. Idempotenz (2× real sync, sha256 vor/nach 2. Lauf)

| Datei | run1→run2 | run2==run3 | Befund |
|---|---|---|---|
| single-Claude/CLAUDE.md | byte-identisch | – | IDEMPOTENT |
| single-Gemini/AGENTS.md | byte-identisch | – | IDEMPOTENT |
| single-Opencode/AGENTS.md | byte-identisch | – | IDEMPOTENT |
| single-Codex/AGENTS.md | byte-identisch | – | IDEMPOTENT |
| single-KimiCode/AGENTS.md | byte-identisch | – | IDEMPOTENT |
| single-Copilot/COPILOT.md | byte-identisch | – | IDEMPOTENT |
| single-Mammouth/MAMMOUTH.md | byte-identisch | – | IDEMPOTENT |
| single-Continue/.continue/rules/project-context.md | **DRIFT** | identisch | nicht idempotent ab run1 |
| single-ZCode/AGENTS.md | **DRIFT** | identisch | nicht idempotent ab run1 |
| multi-all/.continue/rules/project-context.md | **DRIFT** | identisch | wie Continue |
| multi-all/AGENTS.md | byte-identisch | identisch | Bytes stabil (Netto 0) |

**Continue-Drift (VERIFIED), Beleg `diff run1 run2`:**
```
run1 sha 8943cff972f55d17 len 1381   run2 sha 511db3753fd6fd1d len 669
-run1: > **AI ROUTING:** Continue -> .continue/rules/project-context.md ... |developer| |documenter| ...
+run2: **Projekt:** entry-continue | **Plattform:** {{PLATFORM}} | **Runtime:** {{RUNTIME}}
```
Ursache: 1. Sync legt die Datei aus `templates/configs/CONTINUE.project-template.md` an (reicher Managed-Block: Routing + DoD + Agent-Hints). Ab dem 2. Sync ersetzt `_sync_continue_context` (context.py:823-824) den Block durch `render_managed_block()` = `templates/managed-block.md` (generisch, **Platzhalter unsubstituiert**). Kein byte-idempotenter Erstlauf; Content-Downgrade.

**ZCode-Drift (VERIFIED):** `Path.write_text`-Instrumentierung (scratch-only) zeigt pro Sync **3 Writes** auf AGENTS.md:
```
write1 len 19116 (managed update, mit \n\n\n)  → write2 len 18165 (cleanup: bootstrap entfernt + \n{3,}→\n\n)
→ write3 len 19066 (= Ausgangszustand f3cb7904)
```
Netto byte-identisch ab run2, aber run1 != run2.

---

## 3. `--check`-Drift

Semantik (`sync.py:99-105`): `--check` erzwingt `--dry-run`, Exit 1 bei ausstehenden Writes (Zieldateien außerhalb Repo → kein D9-Blindspot, `/var/tmp` ist kein Git-Repo).

| Projekt | `--check` direkt nach sauberem Sync | Befund |
|---|---|---|
| Claude, Codex, Continue, Copilot, Gemini, KimiCode, Mammouth, Opencode | rc 0 (`Provider context files are up to date.`) | OK |
| **single-ZCode** | **rc 1 — „2 file(s) out of sync"** | permanenter False-Positive (Bytes stabil, s. §2) |
| **multi-all** | **rc 1 — „1 file(s) out of sync"** | permanenter False-Positive (Bootstrap-Kollision, s. §6) |

**Manuelle Änderung wird erkannt (VERIFIED):** single-Claude/CLAUDE.md, Zeile **im Managed-Block** ergänzt → `--check` rc 1 (`[UPDATE] CLAUDE.md (managed block)`). Ergänzung **außerhalb** des Blocks (User-Notes) → rc 0. Trefferquote also korrekt managed-block-scoped.

**ZCode-False-Positive-Ursache (Instrumentierung):** Pro Sync loggt der reale Lauf `[UPDATE] AGENTS.md (managed block)` **und** `[CLEANUP] AGENTS.md (removed Gemini bootstrap block (Gemini deactivated)))`; im Dry-Run werden genau diese 2 als ausstehend gezählt → rc 1, obwohl der reale Netto-Write 0 ist.

---

## 4. Managed-Block-Erhalt + User-Notes (VERIFIED)

single-Claude/CLAUDE.md und single-Gemini/AGENTS.md: manuell User-Notes **außerhalb** und eine Zeile **innerhalb** des Managed-Blocks eingefügt, real sync:
```
user-notes-outside preserved: True
managed-line removed: True
managed markers count: 1
```
→ Managed-Block wird vollständig ersetzt (genau 1 Marker-Paar), User-Bereich bleibt unangetastet. Kein Content-Verlust außerhalb des Blocks.

---

## 5. Multi-Provider `AGENTS.md`-Konvergenz (VERIFIED mit Einschränkung)

| Datei | managed_blocks | managed_hash | bootstrap |
|---|---|---|---|
| single-Gemini/AGENTS.md | 1 | `5503d3c378f2` | Gemini-roster (28 Z.) |
| single-Opencode/AGENTS.md | 1 | `cd249b630117` | – |
| single-Codex/AGENTS.md | 1 | `5fb710003d5e` | – |
| single-KimiCode/AGENTS.md | 1 | `5fb710003d5e` | – |
| single-ZCode/AGENTS.md | 1 | `befdcdc2a374` | ZCode-static (19 Z.) |
| **multi-all/AGENTS.md** | **1** | **`5fb710003d5e`** | **ZCode-static** |

- **Managed-Block konvergent JA:** `multi-all` hat genau **1** Managed-Block, byte-identisch zum File-Channel-Variant von Codex/KimiCode (`shared_runtime_gate_vars` senkt das Runtime-Gate auf den gemeinsamen Nenner `advisory`, s. Diff Gemini→multi).
- **Keine Provider-Duplikate im Managed-Block JA** (kein doppeltes Marker-Paar).
- **Bootstrap-Block kollidiert NEIN-konvergent:** `multi-all` enthält nur den ZCode-Text; der Gemini-Roster fehlt → §6.

---

## 6. D8 — Bootstrap-Kollision → **VERIFIED** (erweitert)

**Reproduktion (multi-all, ein realer Sync, Schreib-Instrumentierung):**
```
number of AGENTS.md writes for bootstrap during one real sync: 2
  write1 len 19036  bootstrap=Gemini-roster   (define_subagent, 6 Vorkommen)
  write2 len 18911  bootstrap=ZCode-static    ("ZCode lädt Workspace-Level ... NICHT automatisch")
net change vs before: IDENTICAL
log: [UPDATE] AGENTS.md (bootstrap instructions)
log: [UPDATE] AGENTS.md (bootstrap instructions)
```
Finalzustand = **ZCode-static**; `define_subagent` nur noch im Negativsatz des ZCode-Textes („es gibt KEINE define_subagent-API"). Der Gemini-`define_subagent`-Roster ist **verloren** (last writer wins).

**Code-Belege:**
- `config/provider-bootstrap.yaml:16-27` (Gemini) und `:49-75` (ZCode) — beide `action: inject-bootstrap-instructions`, das injiziert denselben Marker `<!-- agent-meta:bootstrap-begin -->` (`scripts/lib/bootstrap.py:152-161`).
- `scripts/lib/context.py:753` — `gemini_active = "Gemini" in active`; `_cleanup_bootstrap_block` (:737-776) entfernt den Marker, sobald **Gemini** nicht aktiv ist. In ZCode-only wird der **von ZCode** stammende Block fälschlich als Gemini-Rest gelöscht → ZCode-`--check` rc 1 (§3).
- `scripts/lib/bootstrap.py:136` — Default `context_file or ".gemini/GEMINI.md"` (hardcoded provider path, D10 #7).

**Verdikt:** D8 **VERIFIED** und erweitert: (a) Gemini+ZCode verlieren den Gemini-Roster; (b) `--check` konvergiert in Gemini+ZCode- **und** ZCode-only-Projekten nie (permanenter False-Positive).

---

## 7. Harness-Laderealität (real/STATIC + Quelle)

| Provider | Geladene Entry-Datei | Nachweis | Quelle |
|---|---|---|---|
| Claude | `CLAUDE.md` (ignoriert `AGENTS.md` ohne `@import`) | VERIFIED | `docs/analysis/evidence/2026-09-30-runtime-claude-antigravity.md` §1.4 (`claude --debug` lädt nur CLAUDE.md; `grep -c '@AGENTS.md'` = 0) |
| Gemini/Antigravity | Rules `GEMINI.md`, `AGENTS.md`, `.agents/rules/*.md` | STATIC (In-Binary-Doc) | ebd. §2.3 |
| Opencode | `AGENTS.md` | STATIC | `...-docs-part2.md:323-324` |
| Codex | `AGENTS.md` | STATIC | `...-docs-part2.md:82-83` |
| KimiCode | `AGENTS.md` (Projekt-Root, auto) | STATIC | `...-docs-part2.md:170` |
| ZCode | Workspace-`AGENTS.md` (Default injiziert) | STATIC | `...-docs-part2.md:135-136` |
| Continue | `.continue/rules/project-context.md` (Rule ohne Frontmatter → Fallback) | STATIC | `...-docs-part2.md:245` |
| Copilot | nativ `.github/copilot-instructions.md` (Config erzeugt `COPILOT.md`, = P-3 HIGH) | STATIC | `...-docs-part1.md:261,272` |
| Mammouth | `AGENTS.md` (liest `MAMMOUTH.md` **nicht**; MM-4 MED, Orphan) | STATIC | `...-docs-part2.md:323-329,349` |

**Ist-Zustand Abgleich:** single-Mammouth enthält **nur** `MAMMOUTH.md`, **kein** `AGENTS.md` → Mammouth lädt nach MM-4 **nichts**. single-Copilot enthält nur `COPILOT.md`, nicht `.github/copilot-instructions.md` → native Datei fehlt. multi-all hat `AGENTS.md` (Mammouth bedient), aber weiterhin kein `.github/copilot-instructions.md`. Claude/Gemini/Opencode/Codex/KimiCode/ZCode/Continue treffen ihre erwartete Datei.

---

## 8. Offene Punkte

- Continue-Managed-Block-Downgrade (run1→run2) verliert Routing/DoD/Agent-Hints: 1-Tages-Bug, Fix erwägen (`_sync_continue_context` sollte das Erst-Template beibehalten statt auf `managed-block.md` zurückfallen). CI: frischer Continue-Sync + `--check` = rc 1.
- ZCode-only `--check`-False-Positive und Gemini+ZCode-Bootstrap-Verlust (D8) erfordern getrennte Sub-Marker oder providerübergreifenden, deduplizierten Bootstrap-Writer.
- Harness-Load für Gemini/Opencode/Codex/Kimi/ZCode/Continue/Copilot/Mammouth nur STATIC (Doku/Binary); keine Runtime-Ausführung in diesem Task.
- Mammouth/Copilot erzeugen Entry-Dateien, die ihr Harness so nicht lädt (MAMMOUTH.md orphan, COPILOT.md nicht-native) — bestätigt MM-4/P-3 aus den Docs-Audits.
