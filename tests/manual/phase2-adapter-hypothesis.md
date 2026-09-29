# Manuelles Prüfprotokoll — Phase-2-Context-Adapter (HYPOTHESIS-Gate)

| | |
|---|---|
| **Bezug** | `SPEC-CONTEXT-FILE-MODES-2026-09-13`, Plan Task 9 (AC-22, AC-26) |
| **Ziel** | Jeden Phase-2-Adapter erst dann aktivieren, wenn die jeweilige HYPOTHESIS in einem **echten** Ziel-Repo bestätigt und hier als `VERIFIED` dokumentiert ist |
| **Typ** | Manueller Real-Repo-Test (nicht automatisierbar — benötigt die jeweilige Provider-Runtime) |
| **Status** | Gate aktiv; **alle Phase-2-Adapter dormant** (Codex/Copilot/Continue/Mammouth/Gemini bleiben Direkt-Leser des Kerns) |
| **Datum** | 2026-09-15 |

---

## 1. Gate-Regel (AC-22)

Ein Provider verwendet **nur dann** einen Context-Adapter, wenn seine Zeile in der
Tabelle in §3 auf `VERIFIED` steht. Automatisierter Wächter:
`tests/test_context_adapters.py::test_no_adapter_without_verified_hypothesis` —
er vergleicht die in `config/ai-providers.yaml` *aktiven* Adapter
(`context_adapter: true` bzw. Capability `context-adapter`) mit der Menge der
`VERIFIED`-Provider in dieser Datei. Damit kann kein Adapter ohne dokumentierte
Real-Repo-Verifikation scharf werden, und eine Verifikation ohne Config-Flip ist
ebenfalls sichtbar.

**Aktivierungs-Reihenfolge (unverändert verbindlich):**
1. Real-Repo-Test durchführen (§4) und die Beobachtung hier eintragen.
2. Status der Zeile auf `VERIFIED` setzen (mit Datum + Repo/Version).
3. Erst dann in `config/ai-providers.yaml` `context_adapter: true` setzen und die
   noch fehlenden Schlüssel ergänzen (siehe Spalte „Enabling change").

Alle Provider ohne `VERIFIED` bleiben **Direkt-Leser des Kerns**
(`context_file.core_file`, Default `AGENTS.md`) und schreiben **keine**
Adapter-Datei — der aktuelle, unveränderte Zustand.

## 2. Schlüssel-Referenz (`config/ai-providers.yaml`, IC-07)

| Schlüssel | Vertrag |
|---|---|
| `context_adapter: true\|false` | Provider kann eine eigene Adapter-Datei lesen. `false` = dokumentierter, dormanter Phase-2-Kandidat. |
| `context_adapter_file: "<rel-path>"` | Provider-nativer Dateipfad des Adapters. |
| `context_adapter_import: "@{core}"` | Provider-native Import-Syntax; `"{core}"` = `context_file.core_file`. Leer = Pointer-Zeile. |
| `context_adapter_import_supported: true\|false` | Expliziter Boolean; `false` rendert immer die Pointer-Zeile. |
| `context_adapter_settings: true\|false` | `true` = die Adapter-Datei wird erst über einen provider-nativen Settings-Key aktiv (capability-/`settings_file`-gated). Default `false`. |
| `context_adapter_settings_key: "<dotted.key>"` | Nur bei `context_adapter_settings: true`: der provider-native Settings-Key, der die Adapter-Datei aktiviert (z. B. `context.fileName`). Fehlt er, wird **nichts** geschrieben. |

## 3. Provider-Matrix (Gate-Status)

| Provider | Status | Candidate channel | Enabling change |
|---|---|---|---|
| Claude | VERIFIED | `context_adapter: true`, `context_adapter_file: CLAUDE.md`, `context_adapter_import: "@{core}"` | bereits scharf (Phase 1); kein Flip nötig |
| Codex | HYPOTHESIS | `context_adapter_file: AGENTS.override.md` (`rules_dir: rules`) | Real-Repo-PASS + `context_adapter: true` + `context_adapter_import_supported` entscheiden (native Override- vs. `project_doc_fallback_filenames`-Semantik) |
| Copilot | HYPOTHESIS | `context_adapter_file: .github/copilot/COPILOT.md` | Real-Repo-PASS + `context_adapter: true`; prüfen, ob die Runtime `.github/copilot-instructions.md` oder den konfigurierten Pfad liest |
| Continue | HYPOTHESIS | `context_adapter_file: .continue/rules/project-context.md` | Real-Repo-PASS + `context_adapter: true`; Pointer- vs. Import-Semantik entscheiden |
| Mammouth | HYPOTHESIS | `context_adapter_file: MAMMOUTH.md` | Real-Repo-PASS + `context_adapter: true`; Pointer-Semantik entscheiden |
| Gemini | FALLBACK (c) | geteilte `AGENTS.md` + nativer Hook (Antigravity, `hook_protocol: antigravity-hooks-json`, `runtime_gate: hook`) | **Kanal (a) `.gemini/rules` ist widerlegt** (Spike F-RULESLOC); kein Flip. Kandidat (b) `context_adapter_settings: true` + `context_adapter_settings_key: context.fileName` in `.gemini/settings.json` bleibt zurückgestellt und wird **nur** nach eigenem Real-Repo-PASS von `context_adapter_settings` gesetzt |

## 4. Durchführung je Provider (Real-Repo)

1. Frisches Ziel-Repo mit dem Provider öffnen und `python scripts/sync.py` mit
   `context_file.topology: per-provider` ausführen.
2. Die Kandidat-Datei (§3) aus dem Kern-Adapter rendern lassen (temporär
   `context_adapter: true`) und die Provider-Session **neu starten**.
3. Beobachten, ob die Runtime die Kandidat-Datei tatsächlich als Kontext lädt
   (unverwechselbarer Marker in der Datei → Modell fragt danach).
4. Beobachtung + Repo/Version + Datum hier eintragen und Status setzen.
   Ergebnis `PASS` → `VERIFIED` + Config-Flip; `FAIL` → Kandidat ×, Status bleibt
   `HYPOTHESIS`, Datei-pfad ggf. korrigieren und erneut testen.

## 5. Gemini/Antigravity — Kanalentscheidung (Fallback (c))

Das Spike-Verdict `docs/spikes/2026-09-14-f-rulesloc-gemini-rules-channel.md`
ist bindend: `.gemini/rules` ist **keine** dokumentierte Antigravity-Workspace-
Rules-Lokation (`.agents/rules`, rückwärtskompatibel `.agent/rules`) und wird
deshalb **nicht** als Tier-Träger beansprucht. Gemini/Antigravity trägt seinen
`hook`-Tier über den nativen Hook; der geteilte Kern bleibt neutral
(`GATE_NEUTRAL`). Es werden **keine** Gemini-Konfigurationsdateien geändert.
Der reproduzierbare Live-Lauf bleibt als Follow-up offen
(`tests/manual/f-rulesloc-gemini-rules-channel.md`).
