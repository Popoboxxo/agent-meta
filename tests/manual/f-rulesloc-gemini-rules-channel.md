# Manuelles Prüfprotokoll — F-RULESLOC: Welchen Rules-Kanal liest Antigravity?

| | |
|---|---|
| **Bezug** | `SPEC-CONTEXT-FILE-MODES-2026-09-13`, Plan Task 4 · Spike `docs/spikes/2026-09-14-f-rulesloc-gemini-rules-channel.md` |
| **Ziel** | Feststellen, ob die Antigravity-Runtime `.gemini/rules` (Kanal (a)) oder `.agents/rules` (Doku-Lokation) als **Workspace-Rules** lädt |
| **Typ** | Manueller Real-Repo-Test (nicht automatisierbar — benötigt eine echte Antigravity-Session) |
| **Status** | Protokoll bereit; **Live-Lauf offen** (Follow-up zum Evidenz-Verdict) |
| **Datum** | 2026-09-14 |

---

## 1. Voraussetzungen

- Eine installierte **Antigravity-IDE** (oder Antigravity-CLI) mit Zugriff auf einen
  Workspace, dessen Workspace- bzw. Git-Root das getestete Verzeichnis ist.
- Schreibzugriff auf `.gemini/rules/` und `.agents/rules/` im Workspace.
- Ein **frischer** Test-Workspace (oder zumindest ein Workspace ohne weitere Always-On-Regeln),
  damit kein bestehender Regel-Text die Beobachtung verfälscht.

## 2. Durchführung

1. Im Workspace-Root beide Verzeichnisse anlegen:

   ```bash
   mkdir -p .gemini/rules .agents/rules
   ```

2. **Probe-Regel A** in den Kanal (a) schreiben — `.gemini/rules/zz-f-rulesloc-probe-a.md`:

   ```markdown
   ---
   trigger: always_on
   description: F-RULESLOC probe A (.gemini/rules)
   ---
   F-RULESLOC-PROBE-A: If you can read this rule, reply with the exact token F-RULESLOC-PROBE-A.
   ```

3. **Probe-Regel B** in die Doku-Lokation schreiben — `.agents/rules/zz-f-rulesloc-probe-b.md`:

   ```markdown
   ---
   trigger: always_on
   description: F-RULESLOC probe B (.agents/rules)
   ---
   F-RULESLOC-PROBE-B: If you can read this rule, reply with the exact token F-RULESLOC-PROBE-B.
   ```

   > Falls Antigravity rohe Frontmatter-Trigger ignoriert: dieselben Regeln zusätzlich über die
   > UI anlegen (Customizations → Rules → `+ Workspace`) und die Aktivierung dort auf
   > **Always On** stellen. Die Datei-Lokation bleibt der eigentliche Prüfgegenstand.

4. Eine **neue** Agent-Konversation im Workspace starten (keine Alt-Session wiederverwenden).

5. Ohne vorherige `@`-Mention und ohne den Probe-Dateien selbst zu referenzieren, folgenden
   Prompt senden:

   > List every `F-RULESLOC-PROBE-*` token that is present in your active rules.
   > Reply with the tokens only, or `NONE` if none are present.

6. Optional als Gegenprobe: Im Customizations → Rules-Panel prüfen, welche der beiden
   Probe-Regeln als Workspace-Rule gelistet ist und welchen Aktivierungstyp sie hat.

## 3. Zu protokollieren

- Antigravity-Version / Build.
- Ob die Regel-Dateien beim Session-Start unverändert vorlagen (Hash/Inhalt notieren).
- Die exakte Antwort des Agenten auf den Prompt aus Schritt 5.
- Sichtbarkeit/Aktivierungstyp im Rules-Panel (Schritt 6).

## 4. Auswertung

| Beobachtung | Ergebnis | Folge |
|---|---|---|
| Nur `F-RULESLOC-PROBE-B` geladen | Contradiction **bestätigt**: Antigravity liest `.agents/rules`, nicht `.gemini/rules` | Fallback (c) bleibt; Verdict in `docs/spikes/2026-09-14-f-rulesloc-gemini-rules-channel.md` ist bestätigt |
| Nur `F-RULESLOC-PROBE-A` geladen | Kanal (a) **nutzbar** | Spike-Verdict auf `PASS` heben; Task-5-Doku auf Kanal (a) umstellen |
| Beide Tokens geladen | beide Kanäle lesbar | (a) technisch nutzbar; `.agents/rules` bleibt das von der Doku benannte Ziel |
| `NONE` | Metadaten/Format/Aktivierung falsch | Regeln über die UI anlegen und ab Schritt 4 wiederholen |

Das Ergebnis wird im Spike-Dokument (`§6`) mit Datum, Antigravity-Version und Rohbeobachtung
nachgetragen. Bei „Contradiction bestätigt" ist keine Code-Änderung nötig (Fallback (c) ist
bereits der Phase-1-Stand); bei „Kanal (a) nutzbar" ist die Promotion über den bestehenden
`rules_dir`-Seam ohne neue Keys möglich.

## 5. Cleanup

```bash
rm -f .gemini/rules/zz-f-rulesloc-probe-a.md .agents/rules/zz-f-rulesloc-probe-b.md
rmdir .agents/rules 2>/dev/null || true
```

Bei über die UI angelegten Regeln diese zusätzlich im Rules-Panel entfernen.
