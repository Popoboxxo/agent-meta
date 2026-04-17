# Agent Isolation — `isolation: worktree`

Claude Code unterstützt `isolation: worktree` als Aufruf-Parameter für Agenten.
Der Agent arbeitet dann in einem **isolierten Git-Worktree** — einer separaten
Arbeitskopie des Repositories, die parallel zum Haupt-Workspace existiert.

---

## Wann ist Worktree-Isolation sinnvoll?

**Empfohlen für:**

| Szenario | Warum Isolation hilft |
|----------|-----------------------|
| Parallele Feature-Entwicklung | Mehrere feature-Agenten gleichzeitig, ohne Branch-Konflikte |
| Lange Workflows (feature-Agent) | Branch → REQ → TDD → Dev → Validate → PR läuft isoliert |
| Experimentelle Änderungen | Worktree wird verworfen wenn keine Änderungen entstehen |
| Automatisierte Pipelines | Kein Risiko für den aktiven Workspace |

**Nicht empfohlen wenn:**

- Der Agent den aktuellen Branch-Stand des Hauptworkspaces braucht (z.B. git-Agent)
- Submodule im Repo sind (siehe Fallstricke)
- Der Workflow interaktive Benutzer-Eingaben erfordert (Worktree läuft eigenständig)

---

## Konfiguration

### Option A: Direkt beim Agenten-Aufruf (Claude Code UI / API)

```json
{
  "subagent_type": "feature",
  "isolation": "worktree"
}
```

Oder in Claude Code via Agent-Tool-Parameter:
```
isolation: "worktree"
```

### Option B: Dauerhaft im Agenten-Frontmatter (nur für diese Rolle)

Liegt in `.claude/3-project/<prefix>-feature.md` (Override) oder `.claude/agents/feature.md`:

```yaml
---
name: feature
isolation: worktree
# ... rest of frontmatter
---
```

> **Hinweis:** agent-meta injiziert `isolation:` nicht automatisch via sync.py —
> es ist ein Aufruf-Parameter, kein Rollen-Default.
> Aktiviere es projektspezifisch in einem Override (`.claude/3-project/feature.md`)
> oder setze es beim Agenten-Aufruf.

---

## Verhalten: Was passiert mit dem Worktree?

| Zustand nach Agent-Ende | Verhalten |
|-------------------------|-----------|
| Keine Änderungen gemacht | Worktree wird **automatisch bereinigt** |
| Änderungen vorhanden | Worktree bleibt erhalten — Pfad und Branch werden zurückgegeben |

Wenn der Worktree erhalten bleibt, musst du die Änderungen manuell mergen:

```bash
# Branch aus dem Worktree in den Hauptbranch mergen
git merge <worktree-branch>

# Oder: Worktree manuell bereinigen
git worktree remove <worktree-pfad>
git branch -d <worktree-branch>
```

---

## Bekannte Fallstricke

### 1. Submodule nicht initialisiert

Git-Worktrees erben **keine initialisierten Submodule** automatisch.
Falls dein Projekt `.agent-meta/` oder andere Submodule verwendet:

```bash
# Im Worktree-Verzeichnis ausführen (der Agent muss das ggf. tun):
git submodule update --init --recursive
```

**Empfehlung:** In `.claude/3-project/feature-ext.md` einen Hinweis hinterlegen,
dass der Feature-Agent als erstes `git submodule update --init --recursive` ausführt.

### 2. `agent-meta.config.yaml` nicht gefunden

`sync.py` erwartet die Config-Datei relativ zum Projektroot. Im Worktree ist der
Projektroot korrekt gesetzt — das sollte funktionieren. Aber Hooks (z.B. `dod-push-check`)
suchen die Config auch: diese finden sie über die Parent-Directory-Suche.

### 3. Merge-Konflikte nach dem Workflow

Wenn der Haupt-Branch sich während des Worktree-Workflows weiterbewegt:

```bash
# Vor dem Merge: rebasen
git -C <worktree-pfad> rebase origin/main
# Dann mergen
git merge <worktree-branch>
```

### 4. Worktree-Branch bereits vorhanden

Claude Code erstellt für den Worktree einen temporären Branch. Falls ein gleichnamiger
Branch bereits existiert, schlägt die Erstellung fehl. Sicherstelle dass der Haupt-Branch
sauber ist vor dem Aufruf.

### 5. Windows: Pfade mit Leerzeichen

Auf Windows können Worktree-Pfade mit Leerzeichen Probleme verursachen.
Claude Code wählt den Pfad automatisch — normalerweise kein Problem.

---

## Feature-Agent: Empfohlene Konfiguration

Der `feature`-Agent ist der primäre Kandidat für Worktree-Isolation:

```
feature-Agent mit isolation: worktree
    ↓
Neuer Worktree wird erstellt (isolierter Branch)
    ↓
requirements → tester → developer → tester → validator → documenter → git
    (alle Sub-Agenten arbeiten im Worktree)
    ↓
PR wird erstellt (Branch im Worktree → Remote)
    ↓
Worktree bleibt erhalten (Änderungen vorhanden) → manueller Merge oder PR-Merge
```

**Vorteil:** Mehrere Features können parallel entwickelt werden ohne sich gegenseitig
zu blockieren. Jeder feature-Agent hat seinen eigenen Branch und Arbeitszustand.

---

## Abgrenzung zu anderen Isolation-Ansätzen

| Ansatz | Wo | Vorteil | Nachteil |
|--------|----|---------|----------|
| `isolation: worktree` | Claude Code nativ | Automatisch, sauber | Submodule-Handling |
| Manueller Feature-Branch | git-Agent | Volle Kontrolle | Kein echter Workspace-Schutz |
| Separate Claude-Session | Nutzer | Komplett unabhängig | Kein geteilter Kontext |

---

## Weiterführende Ressourcen

- [Claude Code Dokumentation: Agent Isolation](https://docs.anthropic.com/en/docs/claude-code/sub-agents)
- [Git Worktrees](https://git-scm.com/docs/git-worktree)
- [howto/agent-composition.md](agent-composition.md) — Overrides für den feature-Agenten
