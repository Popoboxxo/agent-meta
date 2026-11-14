---
spec-id: SPEC-GIT-AGENT-MERGE-PERMISSION-2026-11-11
title: Machbarkeit einer Permission-Regel nur für den git-Agenten (Merge)
status: DRAFT
issue: "#1172 (Vorschlag 3)"
plan: docs/superpowers/plans/2026-11-11-phase-d-guards-hooks.md (Task 2a, Entscheidung 47)
datum: 2026-11-13
autor: concept-specifier (Subagent, Auftrag via orchestrator)
related-spec: SPEC-GUARD-ROLE-ATTRIBUTION-2026-11-11 (#1210)
---

# Permission-Regel nur für den git-Agenten (Merge) — Machbarkeits-Spec

> **Status: DRAFT — Entwurf, Freigabe durch Nutzer ausstehend.** Nicht `APPROVED`. Kein Reviewer-Lauf.
> Offene Entscheidungen stehen in §10 und werden hier **nicht** entschieden. Diese Datei enthält einen
> Machbarkeitsbefund und bedingte Contracts, keine Implementierung.
> Trace-Anker: `spec-id: SPEC-GIT-AGENT-MERGE-PERMISSION-2026-11-11`.
>
> **Messstand:** Worktree `wt-phase-d1`, 2026-11-13; alle `datei:zeile`-Anker in dieser Session nachgemessen.
> **Hinweis zum Plan:** Plan Task 2a verlangt diese Datei nur bei positivem Befund (Zeile 171), sonst einen
> Issue-Kommentar-Entwurf. Der Befund ist hier **nicht positiv und nicht negativ entschieden** (§6); die
> Datei ist deshalb als Entscheidungsvorlage angelegt. Ob sie bleibt oder in einen Issue-Kommentar
> umgewandelt wird, ist OQ-2.

## 1. Problem / Ziel / Nicht-Ziele

### 1.1 Problem

Issue #1172 beobachtet: Der Weg `orchestrator -> git` für Merges freigegebener PRs wurde in einem Audit
(2026-11-06) vom Claude-Code-Auto-Mode-Classifier als „Merge Without Review" blockiert, auch nach
User-Freigabe im Main Chat; `main_chat -> git` funktioniert. Ursache liegt außerhalb des Repos und ist
nicht reproduziert (`rules/1-generic/use-orchestrator.md`, Absatz „Merge-Muster (#1172)", Task-2-Text).
Vorschlag 3 des Issues: eine Permission-Regel, die nur dem `git`-Agenten den Merge erlaubt. Entscheidung 47:
bauen, **nur wenn machbar**.

### 1.2 Ziel

Prüfen und belegen, ob das Repo für den `git`-Agenten eine rollengebundene Allow-Regel für Merge
(`gh pr merge` / `git merge`) erzeugen kann, ob ein solches Artefakt den beobachteten Block überhaupt
beeinflussen würde und ob es sicherheitlich vertretbar ist.

### 1.3 Nicht-Ziele

- Keine Implementierung (Task 2b nur bei APPROVED).
- Keine Änderung von Branch-Guard, DoD-Push-Check, Destructive-Gate.
- Keine Merge-Policy (#783, offen, Phase I).
- Keine Beeinflussung oder Konfiguration des Auto-Mode-Classifiers (liegt außerhalb des Repos).
- Der in Task 2 dokumentierte Merge-Pfad (Main Chat -> `git`) bleibt unverändert als Fallback.

## 2. Evidenz Schritt 1: Repo-Mechanismen

### 2.1 Gemessene Fundstellen

| Mechanismus | Fundstelle | Was es belegt |
|---|---|---|
| `permission-mode-overrides` | `config/project-config.schema.json:518-527` | Objekt, Wert je Rolle aus Enum `default`, `acceptEdits`, `bypassPermissions`, `plan` (Enum ab `:523`; weitere Werte hinter `:527` nicht gelesen). Setzt einen **Modus**, keine Regel für ein Kommando-Muster. |
| Auflösung Rolle -> Modus | `scripts/lib/roles.py:565-577` | Präzedenz Projekt-Override > `roles.config.yaml` `permission_mode` > leer (kein Feld). |
| Injektion ins Agent-Frontmatter | `scripts/lib/provider_transform.py:682-688`; Schreiber `scripts/lib/frontmatter.py:351-383` | Pro Rolle wird `permissionMode:` ins Agent-Frontmatter geschrieben, wenn `inject-permission-mode` gesetzt ist. Das ist die **einzige** pro Rolle generierte Berechtigungs-Angabe, die in diesen Dateien gefunden wurde. |
| Capability `inject-permission-mode` | `config/ai-providers.yaml:127` (Claude), `:506` (Continue) | Nur diese beiden Provider-Blöcke setzen das Flag (Grep 2026-11-13 über die ganze Datei). Für Gemini/Opencode/Copilot/Mammouth/Codex/ZCode/KimiCode: Flag nicht gesetzt; `permissionMode` steht dort in einer Liste (`:235`, `:582`, `:864`), Bedeutung der Liste nicht gelesen. |
| `permission_mode` der Rolle `git` | `config/role-defaults.yaml:626-645` | Im gelesenen Block der Rolle `git` **kein** `permission_mode`. Der Resolver liest laut `roles.py:570` `roles.config.yaml`; diese Datei wurde nicht gelesen (Namensabweichung `role-defaults.yaml` vs. `roles.config.yaml` nicht aufgeklärt). |
| `subagent_permissions` | `config/project-config.schema.json:1617-1650`; Auflösung `scripts/lib/subagent_permissions.py:1-8, 31-57` | Nur `strict`/`warn`/`off`; erzeugt **Prosa** („prompt-based on every provider plus a sync-time validator; … deliberately no runtime dispatch gate", `:3-5`). Keine Allow-Regel, kein Kommando-Muster. |
| `scripts/lib/permissions.py` | `scripts/lib/permissions.py:1-62` | Betrifft nur `chmod 0600` für `.meta-config/project.yaml` (`restrict_owner_only`, `harden_admin_config_files`). Keine Harness-Berechtigung. |
| `permissions.additionalDirectories` | `config/ai-providers.yaml:77-82` (Key `settings-allow-dirs-key`, Claude only); Schreiber `scripts/lib/sync_pipeline.py:1612-1620` | Additiver Eintrag in **`.claude/settings.local.json`** (`ai-providers.yaml:76`), zweckgebunden an den pytest-Basetemp (#1079). Verzeichnisfreigabe, keine Kommando-Regel. |
| Settings-Templates | `templates/configs/CLAUDE.settings-template.json:2-10`; `CLAUDE.settings-local-template.json:2-5` | `permissions.allow` ist leer (`[]`), `permissions.deny` enthält `Bash(rm -rf:*)`, `Bash(git push --force:*)`, `Bash(git push -f:*)`, `Bash(git reset --hard:*)`. Das Repo erzeugt also bereits Kommando-Muster-Regeln im `Bash(...)`-Format, aber **nur als `deny`** und **global je Settings-Datei**. |
| Isolation per `permissions.deny` | `scripts/lib/isolation.py:8, 369-392` | Bestehender Schreibpfad für verwaltete `permissions.deny`-Einträge in `.claude/settings.json` (Claude). |

### 2.2 Was daraus folgt und was nicht

Belegt:

1. Das Repo hat **keinen** Generator für `permissions.allow`-Einträge (Template `allow: []`, kein Schreiber
   gefunden, nur `deny` über `isolation.py` und `additionalDirectories` über `sync_pipeline.py:1612-1620`).
   Grep `permissions.allow|"allow"` in `scripts/lib` (head_limit 40) lieferte keinen Schreiber für
   Claude-`permissions.allow`; die Trefferliste war abgeschnitten, vollständig nicht geprüft.
2. Die einzige rollenbezogene Berechtigungs-Stellgröße ist `permissionMode` im Agent-Frontmatter
   (`provider_transform.py:682-688`) mit Enum-Werten aus `project-config.schema.json:523-527`. Sie ist ein
   **Modus**, nicht auf `gh pr merge`/`git merge` begrenzbar. `bypassPermissions` für die Rolle `git`
   wäre breiter als „nur Merge" (Security-Befund, §4).
3. `permissions.allow` in Settings-Dateien gilt **pro Session/Projekt**, nicht pro Subagent. Diese Aussage
   stammt aus dem Auftrag; ein Beleg aus einer Harness-Doku **im Repo** wurde nicht gefunden (nur das
   Repo-Template zeigt, dass `allow`/`deny` Teil von `settings.json` sind, `CLAUDE.settings-template.json:2-10`).
   Ob die Claude-Code-Settings pro Agent einen Bash-Allow kennen: **nicht verifiziert** (§7).
4. Per-Agent-Berechtigung existiert im Repo für Opencode als `permission`-Mapping im Agent-Output
   (`scripts/lib/provider_transform.py:925, 982, 1028-1101`, dort `permission.edit`/Tool-Aktionen mit
   `allow`/`deny`). Ob dieses Mapping Kommando-Muster für Bash (z. B. `gh pr merge`) trägt, wurde **nicht
   gelesen** und ist **nicht verifiziert**.

## 3. Evidenz Schritt 2: Externe Grenze

Der Block kommt vom Auto-Mode-Classifier des Claude-Code-Harness (außerhalb des Repos; Plan Task 2a Step 2).

- Ob eine vom Repo erzeugte Permission-Regel (Allow, `permissionMode`) den Classifier beeinflusst:
  **nicht verifiziert.** Die einzige vorhandene Quelle, `docs/analysis/2026-11-11-hook-api-ask-permission.md`,
  sagt: Regelreihenfolge deny, ask, allow; „PreToolUse hook decisions don't bypass permission rules";
  „Zusammenspiel von Hook-`ask` mit dem Auto-Mode-Classifier: nicht verifiziert (Permission-Modes-Seite
  nicht gelesen)" (`:82-87`). Für Allow-Regeln gegenüber dem Classifier gibt es dort keine Aussage.
- Das Muster der Analyse-Quelle ist eine Fetch-Extraktion (Abruf 2026-11-13), kein Rohtext.
- **Quelle, die es entscheiden würde:** die Claude-Code-Seite „Permission modes" (Auto-Mode-Abschnitt:
  Reihenfolge Regel vs. Classifier, Aussage ob Allow-Regeln den Classifier überspringen) plus die
  Settings-/Permissions-Seite (Per-Subagent-Regeln). Beide Seiten in dieser Session **nicht gelesen**.
  Alternativ ein Live-Probe (Kosten, Nutzer-Ok nötig, OQ-4).

### 3.1 Beobachtete Reibung (belegt in dieser Session, 2026-11-13)

(a) Der Classifier lehnte den `git`-Agenten des Orchestrators bei einer Mutation ab: Kommando
`git -C .../wt-phase-d1 add -- <file>` mit vorangestellter Sentinel-Zeile `#agent-meta:agent=git`;
Meldung `Permission for this action was denied by the Claude Code auto mode classifier. Reason:
[Undermining Oversight].` Die Sentinel-Zeile erzeugt das `git`-Template selbst
(`agents/1-generic/git.md:31`, `:42`, `:98`, Pflichtformulierung `:159`; per Grep 2026-11-13 nachgemessen).

(b) Der Classifier lehnt auch **read-only** Git (z. B. `git status`) des Orchestrator-`git`-Agenten
sporadisch mit `[Undermining Oversight]` ab (beobachtet 2026-11-13).

**Inferenz (nicht verifiziert):** Wenn der Classifier selbst read-only Git und das Sentinel-Kommando der
Template-eigenen Form ablehnt, adressiert eine repo-seitige Allow-Regel für **Merge** die beobachtete
Klasse von Blöcken (`Undermining Oversight`, nicht `Merge Without Review`) voraussichtlich nicht. Die
Ablehnungsgründe unterscheiden sich (`Merge Without Review` in #1172 vs. `Undermining Oversight` hier);
ob beide vom gleichen Mechanismus kommen, ist unbekannt. Ob die Ablehnung vom Sentinel-Text abhängt, ist
**nicht verifiziert** (siehe #1210-Spec §2.2, §9).

## 4. Evidenz Schritt 3: Security-Boundary-Bewertung

Die Regel erweitert Rechte (Merge ohne Review-Gate des Harness). Anforderungen an jede Umsetzung, falls
gebaut:

1. **Rollengebunden:** nur für `git`. Ein globales `permissions.allow` (Settings, `CLAUDE.settings-template.json:3`)
   würde **allen** Rollen und dem Main-Chat den Merge freigeben und scheidet damit aus. `permissionMode:
   bypassPermissions` für `git` (`project-config.schema.json:526`) wäre ebenfalls breiter als Merge
   (würde alle Kommandos der Rolle betreffen) und ist als Mittel für Merge-only ungeeignet.
2. **Provider-agnostisch:** Ausdruck über ein Capability-Flag in `config/ai-providers.yaml` (Muster
   `inject-permission-mode :127`, `hook-agent-id :64`), nie `if provider == ...` (`CLAUDE.md`, Code-Konventionen).
   Provider ohne Flag erhalten keine Regel; Fallback-Doku bleibt.
3. **Merge-Policy #783 nicht unterlaufen:** Die Regel darf keinen Merge ohne die dort (noch offen) festzulegenden
   Gates erlauben. Da #783 offen ist (Phase I), ist der Inhalt der Policy **nicht verifiziert**; eine Regel
   vor #783 könnte ein später verschärftes Gate vorwegnehmen.
4. **Branch-Guard/DoD-Push-Check unberührt** (`.claude/rules/branch-guard.md`: Branch-Guard-Regeln und
   Push-Check bleiben; die Regel adressiert nur Merge).
5. **Einstufung nach `.claude/rules/branch-guard.md`:** Eine generierte Allow-Regel gegenüber dem Classifier
   ist **keine** Security boundary, sofern sie nur eine Freigabe erteilt: Sie schließt nichts ab, sondern
   öffnet. Der schützende Teil (Classifier, `deny`-Regeln) liegt außerhalb. Eine Rollenbindung, die auf
   dem Sentinel (selbst deklariert, #1210) oder auf `agent_type` (Vertrauenswürdigkeit nicht verifiziert,
   Analyse `:81`) beruht, wäre **Convention boundary** (fail-closed nur gegen akzidentellen Missbrauch,
   nicht gegen deliberate Umgehung). Eine belastbare **Security boundary** für „nur `git` darf mergen" ist
   mit dem im Repo belegten Stand **nicht** belegbar (Rollenfeld/Spawn-Pfade offen, #1210 §5).

## 5. Machbarkeitsbefund je Provider

Werte: `ja` | `nein` | `unbekannt`. Frage: Lässt sich eine Allow-Regel erzeugen, die **nur** für den
`git`-Agenten `gh pr merge`/`git merge` freigibt? Zusatzfrage: Würde sie den Classifier-Block beeinflussen?

| Provider | Regel erzeugbar (rollengebunden, nur Merge) | Beeinflusst Classifier | Quelle / Begründung |
|---|---|---|---|
| Claude | **unbekannt** (Frontmatter nur `permissionMode`: Modus, nicht Merge-only, `provider_transform.py:682-688`, `schema :523-527`; `permissions.allow` ist global je Settings-Datei, kein Repo-Schreiber, `CLAUDE.settings-template.json:3`; Per-Agent-Bash-Allow der Harness nicht verifiziert) | **unbekannt** | §2.2 Punkt 1-3, §3 |
| Continue | **unbekannt** (`inject-permission-mode` gesetzt, `ai-providers.yaml:506`; Bedeutung für Merge-Regeln nicht gelesen) | **unbekannt** | nur Flag-Fundstelle |
| Opencode | **unbekannt** (Repo erzeugt `permission`-Mapping, `provider_transform.py:925, 982`; Bash-Kommando-Muster nicht gelesen) | **unbekannt** (kein Auto-Mode-Classifier im Repo belegt) | §2.2 Punkt 4 |
| Gemini | **unbekannt** (`inject-permission-mode` nicht gesetzt, Grep `ai-providers.yaml`; Provider-Doku nicht gelesen) | **unbekannt** | nur negativer Repo-Fund |
| Copilot, Mammouth, Codex, ZCode, KimiCode | **unbekannt** (`inject-permission-mode` nicht gesetzt; keine Repo-Fundstelle für eine rollengebundene Regel) | **unbekannt** | Grep `ai-providers.yaml` |

Keine Zelle ist `ja` oder `nein`: Weder ist ein Mechanismus belegt, der die Regel erzeugen kann, noch ist
einer belegt ausgeschlossen. Der einzige belegt vorhandene Mechanismus (`permissionMode`) ist für „nur Merge"
**zu grob**; das ist eine Aussage über diesen Mechanismus, nicht über die Provider-Fähigkeit insgesamt.

## 6. Vorläufiges Urteil

**Nicht entschieden.** Begründung aus der Evidenz:

- Belegt: kein Repo-Generator für rollengebundene Kommando-Allow-Regeln; `permissionMode` ist für
  Merge-only ungeeignet (§2.2, §4).
- Unbekannt, entscheidungsrelevant: (i) ob die Claude-Code-Harness eine Per-Agent-Bash-Allow-Regel kennt,
  (ii) ob eine Allow-Regel den Classifier überhaupt beeinflusst (§3), (iii) ob `Merge Without Review`
  und `Undermining Oversight` dieselbe Ursache haben.
- Hinweisend, nicht beweisend: die Reibung (a)/(b) in §3.1 spricht dafür, dass eine Merge-Allow-Regel die
  beobachtete Block-Klasse nicht trifft. Das ist eine Inferenz; sie trägt kein Urteil „nein".

Ein Urteil „nicht machbar" oder „machbar" folgt aus der vorliegenden Evidenz **nicht**. Vermutet (nicht
belegt): nein, bis die in §3 genannten Quellen gelesen sind.

## 7. Fallback

Der in Task 2 dokumentierte Merge-Pfad bleibt: Merges freigegebener PRs dispatcht der Main Chat direkt an
den `git`-Agenten (`rules/1-generic/use-orchestrator.md`, Absatz „Merge-Muster (#1172)"; ebenso
`agents/1-generic/orchestrator.md`, `agents/1-generic/git.md`). Er hängt von keinem Ergebnis dieser Spec ab.
Bei Urteil „nicht machbar" oder ohne Freigabe entfällt Task 2b; #1172 bleibt dokumentationsseitig
abgeschlossen (OQ-2).

## 8. Interface Contracts (bedingt, nur bei positivem Urteil und APPROVED)

Nur Kandidaten, kein Verbindlichkeitsanspruch. Alle Ziele für Task 2b müssen vor Bau erneut gemessen werden.

| Datei | Stelle | Inhalt (Entwurf) |
|---|---|---|
| `config/ai-providers.yaml` | `capabilities`-Liste je Provider (Muster `:64`) | neues Flag, Arbeitsname `role-scoped-merge-allow`; nur für Provider mit belegtem Mechanismus |
| `config/project-config.schema.json` | neben `permission-mode-overrides` (`:518`) | optionaler Opt-in-Key (Name offen, Default aus) |
| `scripts/lib/provider_transform.py` | neben Schritt `# --- 3. permissionMode ---` (`:682`) | Erzeugung des rollengebundenen Artefakts nur für Rolle `git`; Fehlerpfad: Flag fehlt -> kein Artefakt, kein Fehler |
| `tests/test_git_agent_merge_permission.py` | neu | Testmatrix §9 |

Das Artefakt selbst (Frontmatter-Feld, Settings-Eintrag oder Provider-`permission`-Mapping) ist **offen**
und hängt vom Beleg in §3/OQ ab.

## 9. Acceptance Criteria

Teil A gilt für diese Spec (Befund). Teil B nur bei positivem Urteil.

**Teil A (Befund)**

1. **AC-1 Evidenz je Fundstelle:** Given diese Spec, When ein Leser §2 prüft, Then hat jede der sechs im Plan
   (Task 2a Step 1) genannten Fundstellen eine `datei:zeile`-Angabe oder die Kennzeichnung „nicht verifiziert".
2. **AC-2 Provider-Tabelle:** Given §5, Then enthält jede Zelle genau einen Wert aus `ja|nein|unbekannt`
   und eine Quelle; keine Zelle `ja`/`nein` ohne `datei:zeile` oder URL mit Abrufdatum.
3. **AC-3 Externe Grenze:** Given §3, Then wird die Classifier-Wirkung als „nicht verifiziert" geführt und
   die entscheidende Quelle (Permission-Modes-Seite) bzw. der Live-Probe genannt.
4. **AC-4 Security-Abschnitt:** Given §4, Then sind Rollenbindung, Provider-Agnostik (Capability-Flag),
   #783, Branch-Guard/DoD-Push-Check und die Einstufung Convention vs. Security boundary je einzeln benannt.
5. **AC-5 Fallback:** Given §7, Then ist der Task-2-Pfad als unverändert genannt.
6. **AC-6 Urteil nur aus Evidenz:** Given §6, Then steht dort „nicht entschieden" bzw. ein Urteil mit
   `datei:zeile`-/URL-Beleg; Inferenzen sind als solche gekennzeichnet.
7. **AC-7 Gate:** Spec-Status bleibt `DRAFT`, bis Nutzerfreigabe vorliegt; Task 2b startet nicht ohne
   `Status: APPROVED` (Plan Task 2a Step 4).

**Teil B (nur bei positivem Urteil und APPROVED, jeweils auf §8 bezogen)**

8. **AC-8 Rollenbindung:** Given aktiviertes Flag, When `python3 scripts/sync.py` läuft, Then enthält das
   generierte Artefakt der Rolle `git` die Merge-Regel und das Artefakt keiner anderen Rolle.
9. **AC-9 Provider ohne Capability:** Given Provider ohne Flag, Then kein Artefakt, Sync Exit 0.
10. **AC-10 Provider-Agnostik:** Given der Diff, When nach `provider ==`/Providernamen im Code gesucht wird,
    Then kein neuer Treffer.
11. **AC-11 Guards unberührt:** Given der Diff, Then keine Änderung an `hooks/1-generic/orchestrator-guard-impl.sh`
    und DoD-Push-Check; bestehende Tests grün.
12. **AC-12 Default aus:** Given Projekt ohne Opt-in, Then Render ohne Diff zur Baseline.
13. **AC-13 Validierung:** `python3 scripts/sync.py --validate` Exit 0;
    `python3 -m pytest tests/test_git_agent_merge_permission.py tests/test_merge_pattern_docs.py` grün.

## 10. Testmatrix (Teil B)

| Fall | Provider-Capability | Rolle | Erwartet |
|---|---|---|---|
| M1 | gesetzt | `git` | Artefakt enthält Merge-Regel (AC-8) |
| M2 | gesetzt | `developer` | kein Artefakt (AC-8) |
| M3 | nicht gesetzt | `git` | kein Artefakt, Exit 0 (AC-9) |
| M4 | gesetzt, Opt-in aus | `git` | Render identisch zur Baseline (AC-12) |
| M5 | beliebig | beliebig | Hook-/Guard-Dateien unverändert (AC-11) |

Ein Test, dass die Regel den **Classifier** beeinflusst, ist im Repo nicht schreibbar (außerhalb);
nur ein Live-Probe könnte das zeigen (OQ-4).

## 11. Datenfluss (bedingt)

`config/ai-providers.yaml` (Capability) + `.meta-config/project.yaml` (Opt-in) -> `scripts/lib/provider_transform.py`
(Agent-Transform je Rolle) -> Artefakt der Rolle `git` (Ort offen) -> Harness. Persistenz: nur generierte
Datei. Keine Laufzeit-Hook-Änderung.

## 12. Out-of-scope

- Classifier-Konfiguration/-Beeinflussung; Aussage, ob ein Rollenfeld oder Template-Änderung die
  Ablehnungen (a)/(b) beendet (siehe #1210).
- Rollenbindung/Fälschbarkeit des Guards (#1210).
- Merge-Policy #783, Destructive-Gate (#1217).
- Provider ohne dokumentierten Mechanismus.

## 13. Nicht verifiziert

- Ob die Claude-Code-Harness Per-Subagent-Bash-Allow-Regeln kennt und wie sie in Agent-Frontmatter/Settings
  ausgedrückt werden (Harness-Doku nicht gelesen; keine Harness-Doku im Repo als Beleg gefunden).
- Ob eine repo-erzeugte Allow-Regel/`permissionMode` den Auto-Mode-Classifier beeinflusst (Permission-Modes-Seite
  nicht gelesen; Analyse-Doc nur Fetch-Extraktion).
- Ob `Merge Without Review` (#1172) und `Undermining Oversight` (§3.1) vom selben Mechanismus stammen.
- Ob die Classifier-Ablehnung vom Sentinel-Text abhängt.
- Enum-Werte hinter `project-config.schema.json:527` und `roles.config.yaml` (Resolver-Quelle, `roles.py:570`);
  `permission_mode` der Rolle `git` dort.
- Bedeutung der `permissionMode`-Listeneinträge `ai-providers.yaml:235, 582, 864`.
- Opencode-`permission`-Mapping (`provider_transform.py:925, 982, 1028-1101`) auf Bash-Kommando-Muster.
- Vollständigkeit der Grep-Suche nach `permissions.allow`-Schreibern in `scripts/lib` (Ausgabe begrenzt).
- Inhalt der Merge-Policy #783.
- graphify wurde nicht befragt (kein Bash verfügbar); Anker per Direktlesen/Grep gemessen.

## 14. Offene Fragen an den Nutzer

Keine ist entschieden.

1. Soll Task 2b bei unbekannter Classifier-Wirkung überhaupt gebaut werden, oder erst nach Beleg (§3)?
2. Wird Urteil „nicht machbar" akzeptiert und #1172 doc-only geschlossen (Plan Task 2a Step 4, negativer
   Zweig: Issue-Kommentar statt Spec)? Bleibt diese Datei dann als Befund-Dokument bestehen?
3. Welcher Provider-Scope: nur Claude (dort tritt der Block auf) oder auch Continue/Opencode?
4. Ist ein Live-Probe (Kosten, Nutzer-Ok) akzeptabel, um die Classifier-Wirkung zu testen, oder reicht das
   Lesen der Permission-Modes- und Settings-Doku?
5. Soll die Sentinel-Zeile aus dem `git`-Template (`agents/1-generic/git.md:31, :42, :98, :159`) für Provider
   mit Rollen-Payload-Feld entfallen (siehe #1210-Spec OQ-2)? Wirkung auf die Ablehnungen (a)/(b) nicht
   verifiziert.
6. Soll #783 (Merge-Policy) vor einer Merge-Allow-Regel entschieden sein?

## 15. Risiken

- Aufwand für eine Regel ohne Wirkung auf den Classifier (Inferenz §3.1).
- Rechte-Erweiterung (`bypassPermissions` o. ä.) breiter als „nur Merge".
- Falsches Sicherheitsgefühl: Rollenbindung über Sentinel/`agent_type` ist Convention boundary (#1210).
- Vorwegnahme von #783.

## 16. Trace-Anker

`spec-id: SPEC-GIT-AGENT-MERGE-PERMISSION-2026-11-11`
