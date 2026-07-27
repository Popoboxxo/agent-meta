---
type: "Concept"
title: "Architektur: Provider-agnostische Subagent-Spawn-Restriction (Singleton-Orchestrator)"
description: "Der heutige sync.py-Lauf generiert für Worker-Agents Provider-Frontmatter, die Subagent-Spawns technisch erlaubt statt sie zu unterbinden. Konkret:"
tags: [concept, status:active]
timestamp: "2026-07-27"
resource: "../../sources/docs/concepts/active/singleton-orchestrator-architecture.md"
migrated_from: "docs/concepts/active/singleton-orchestrator-architecture.md"
migration_note: "planned-Version inhaltlich abweichend — als historische Referenz in knowledge/sources/ abgelegt, keine eigene Wiki-Seite."
---
# Architektur: Provider-agnostische Subagent-Spawn-Restriction (Singleton-Orchestrator)

> Status: **Aktiv — Body-Constraint Phase implementiert (2026-06-30)**
> Erweitert: `prompt-modernization.md` (Sektion 16.5 / geplant)
> Quelle: Bug-Report "Worker spawnt Orchestrator" — siehe Sitzungs-Log 2026-06-28
> Kern-These: **Es existiert genau EIN Orchestrator — der vom `main_chat` gespawnte. Worker-Agents dürfen niemals einen Orchestrator dispatchen.**

---

## 16.5.1 Problem-Diagnose

### Aktueller Zustand (Ist-Stand)

Der heutige `sync.py`-Lauf generiert für Worker-Agents Provider-Frontmatter, die Subagent-Spawns **technisch erlaubt** statt sie zu unterbinden. Konkret:

**Opencode-Worker (heute generiert):**
```yaml
# .opencode/agents/developer.md
permission:
  bash: allow
  read: allow
  edit: allow
  glob: allow
  grep: allow
  todowrite: allow
  task: allow          # ← BUG: Worker darf task(subagent_type="orchestrator", ...) aufrufen
```

**Opencode-Orchestrator (heute generiert):**
```yaml
# .opencode/agents/orchestrator.md
permission:
  todowrite: allow
  task: allow          # OK: Orchestrator darf task nutzen
  edit: allow
  bash: deny
```

**Claude-Whitelist (`config/provider-tools.yaml`):**
```yaml
claude:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Task              # ← BUG: Worker-Agent darf Task aufrufen
  - Agent             # ← BUG: Worker-Agent darf Agent aufrufen
  - TodoWrite
```

**`config/provider-tools.yaml:56-60`:**
```yaml
opencode_deny_critical:
  - Bash
  - Write
  - Edit
# → 'task' fehlt komplett in der Denylist
```

### Vier identifizierte Sicherheits-Lücken

| # | Lücke | Konsequenz |
|---|-------|------------|
| L1 | `opencode_deny_critical` denyt nicht `task`/`Agent` | Opencode-Worker dürfen jeden Subagenten spawnen |
| L2 | Claude-Whitelist enthält `Task`+`Agent` ohne Restriction | Claude-Worker dürfen Task/Agent nutzen |
| L3 | Keine `forbidden_subagents` Policy in `role-defaults.yaml` | Framework hat kein Konzept für Spawn-Whitelist pro Rolle |
| L4 | `scripts/lib/runtime.py` hat keine Spawn-Validierung | Python-Barrier (sofern genutzt) prüft nichts |

### Aktuelle Schutz-Mechanismen und ihre Lücken

| Mechanismus | Schützt vor | Schützt NICHT vor |
|---|---|---|
| `rules/1-generic/a2a-delegation-gates.md` (4 Text-Gates) | Main-Chat-Doku | Worker-Spawn (nur Doku) |
| `agents/1-generic/orchestrator.md:687-711` (Anti-Recursion) | Orchestrator-Re-Delegation | Worker-Spawn |
| `hooks/1-generic/orchestrator-guard.sh` (Strict-Mode) | Main-Chat-Schreibzugriff | Worker-Spawn (kein Check) |
| `rules/1-generic/use-orchestrator.md:74-76` (Anti-Recursion Guard) | Worker-Doku | Worker-Spawn |
| `rules/1-generic/provider-agnostic.md` | Provider-Pfade | Subagent-Tool-Calls |

**Fazit:** Heute ist die "Regel" rein dokumentarisch. Es gibt **keinen** technischen Mechanismus, der einen Worker daran hindert, `task(subagent_type="orchestrator", ...)` aufzurufen.

---

## 16.5.2 Architektur-Prinzip

### Singleton-Hauptregel

> **NUR EIN ORCHESTRATOR existiert — der vom `main_chat` (opencode-Session) gespawnte.**
> **Worker-Agents dürfen NIEMALS einen Orchestrator dispatchen.**
> **Provider-agnostisch durchgesetzt via Frontmatter-Permissions und Body-Constraints.**

### Per-Pair-Whitelist für Worker

Die Binary-Regel "Worker darf gar nicht spawnen" wäre **zu restriktiv** — sie würde Reflection-Loops (developer↔code-reviewer) und Eskalations-Pfade (junior→developer) unmöglich machen. Stattdessen:

- **Orchestrator:** Darf alles außer sich selbst (Self-Spawn verboten)
- **Worker (Reflection-Pair):** Darf seinen Reflection-Partner (z.B. developer ↔ code-reviewer)
- **Worker (Eskalation):** Darf Senior-Tier oder andere Worker für Eskalation
- **Worker (Terminal):** Darf gar nichts (git, documenter, feedback)
- **Worker (Feature):** Darf Sub-Pipeline-Worker (developer, tester, requirements, …)

Die Whitelist wird **automatisch aus `reflection_pairs` abgeleitet** — keine Doppel-Konfiguration.

### Drei-Schichten-Durchsetzung

```
┌──────────────────────────────────────────────────────────┐
│  Schicht 1: Provider-Frontmatter                          │
│  - Opencode: permission.task: deny / allow                │
│  - Claude: tools:-Liste filtern                          │
├──────────────────────────────────────────────────────────┤
│  Schicht 2: Body-Constraint-Text (auto-injected)          │
│  - Liste der erlaubten Paare                             │
│  - Liste der verbotenen Ziele                             │
│  - Warnung: "Verletzung = Provider-Block"                 │
├──────────────────────────────────────────────────────────┤
│  Schicht 3: A2A-Gate-Dokumentation                         │
│  - rules/1-generic/a2a-delegation-gates.md Gate #5        │
│  - agents/1-generic/<worker>.md Anti-Recursion-Section    │
└──────────────────────────────────────────────────────────┘
```

**Schicht 1** ist das primäre Enforcement (technisch durch Provider).
**Schicht 2** ist die Doku-Ebene (für den Fall dass Provider keinen Mechanismus hat — Continue/Copilot).
**Schicht 3** ist die globale Doku-Regel.

---

## 16.5.3 Konfigurations-Schema in `role-defaults.yaml`

Pro Rolle wird ein neuer Block `spawn_policy` eingefügt. Die `allowed_subagents` werden **automatisch aus `reflection_pairs` abgeleitet** — nur Eskalations-Paare und Feature-Pipelines werden explizit konfiguriert.

```yaml
# In config/role-defaults.yaml (Erweiterung pro Rolle)
roles:

  # ── Orchestrator: Singleton-Wurzel ──
  orchestrator:
    model: "balanced"
    memory: ""
    workflow_tier: required
    description: "..."
    spawn_policy:
      mode: open                          # darf alle Worker dispatchen
      forbidden_subagents: ["orchestrator"]  # Self-Spawn verboten
      # Singleton-Regel: main_chat darf 1× pro Session spawnen
    handoff:
      # ... bestehend ...

  # ── Tier-1 Worker: Reflection-Loops ──
  developer:
    model: powerful
    workflow_tier: required
    spawn_policy:
      mode: pair_whitelist
      forbidden_subagents: ["orchestrator"]    # Singleton-Regel
      # Erlaubt: aus reflection_pairs abgeleitet
      allowed_subagents:
        - target: code-reviewer
          purpose: "reflection-loop:dev-review-loop"
        - target: tester
          purpose: "test-delegation"

  code-reviewer:
    model: powerful
    workflow_tier: recommended
    spawn_policy:
      mode: pair_whitelist
      forbidden_subagents: ["orchestrator"]
      allowed_subagents:
        - target: developer
          purpose: "reflection-loop:dev-review-loop"

  # ── Tier-1b Worker: Eskalations-Hierarchie ──
  junior-developer:
    model: fast
    workflow_tier: optional
    spawn_policy:
      mode: pair_whitelist
      forbidden_subagents: ["orchestrator", "senior-developer"]
      allowed_subagents:
        - target: developer
          purpose: "escalation"

  senior-developer:
    model: max
    workflow_tier: optional
    spawn_policy:
      mode: pair_whitelist
      forbidden_subagents: ["orchestrator"]
      allowed_subagents:
        - target: code-reviewer
          purpose: "reflection-loop:se-dev-review-loop"
        - target: junior-developer
          purpose: "de-escalation"
        - target: developer
          purpose: "escalation"
        - target: validator
          purpose: "dod-check"

  # ── Pipeline-Coordinator ──
  feature:
    model: ""
    workflow_tier: recommended
    description: "Feature-Lifecycle-Subagent: Branch → REQ → TDD → Dev → Validate → PR."
    spawn_policy:
      mode: pair_whitelist
      forbidden_subagents: ["orchestrator"]
      allowed_subagents: [developer, tester, requirements, validator, git]

  # ── SE-Agenten: spiegeln ihre reflection_pairs ──
  se-requirements:
    model: balanced
    workflow_tier: optional
    spawn_policy:
      mode: pair_whitelist
      forbidden_subagents: ["orchestrator"]
      allowed_subagents: [se-critic]
  se-architect:
    model: powerful
    workflow_tier: optional
    spawn_policy:
      mode: pair_whitelist
      forbidden_subagents: ["orchestrator"]
      allowed_subagents: [se-critic]
  se-developer:
    model: powerful
    workflow_tier: optional
    spawn_policy:
      mode: pair_whitelist
      forbidden_subagents: ["orchestrator"]
      allowed_subagents: [se-critic, code-reviewer]
  se-test-engineer:
    model: balanced
    workflow_tier: optional
    spawn_policy:
      mode: pair_whitelist
      forbidden_subagents: ["orchestrator"]
      allowed_subagents: [se-testreviewer]

  # ── Terminal-Worker: closed mode, kein Spawn ──
  git:
    model: fast
    workflow_tier: recommended
    spawn_policy:
      mode: closed
      forbidden_subagents: "*"               # nichts erlaubt
  documenter:
    model: balanced
    workflow_tier: recommended
    spawn_policy:
      mode: closed
      forbidden_subagents: "*"
  feedback:
    model: fast
    workflow_tier: recommended
    spawn_policy:
      mode: closed
      forbidden_subagents: "*"
```

### Globale Singleton-Regel

Zusätzlich zu `forbidden_subagents` pro Rolle:

```yaml
# In config/role-defaults.yaml (globaler Block)
spawn_singleton:
  - role: orchestrator
    allowed_callers: ["main_chat"]           # NUR main_chat
    max_concurrent: 1
  - role: orchestrator-iteration           # für künftige Reflection-Orchestrator
    allowed_callers: ["orchestrator"]
    max_concurrent: 1
    cooldown_sec: 5
```

**Sync-Implementierung:** In `sync_agents_for_provider()` wird `orchestrator` als **immer verboten** für alle Worker-Agents injiziert — unabhängig von der Pair-Whitelist. Das ist eine harte Singleton-Garantie, die **nicht** übersteuerbar ist.

---

## 16.5.4 Auto-Ableitung aus `reflection_pairs`

`reflection_pairs` (existiert in `role-defaults.yaml:450`) ist die **Single Source of Truth**. Die `spawn_policy.allowed_subagents` wird daraus automatisch abgeleitet:

```python
# scripts/lib/agents.py — neue Hilfsfunktion
def _derive_spawn_policy_from_reflection_pairs(role_defaults: dict) -> dict:
    """Leitet spawn_policy.allowed_subagents aus reflection_pairs ab.
    
    Beispiel: dev-review-loop (developer↔code-reviewer) erzeugt:
      developer.allowed_subagents     += [{target: code-reviewer, purpose: 'reflection-loop:dev-review-loop'}]
      code-reviewer.allowed_subagents += [{target: developer,     purpose: 'reflection-loop:dev-review-loop'}]
    """
    derived = {}
    for pair in role_defaults.get("reflection_pairs", []):
        pair_id = pair["id"]
        generator = pair["generator"]
        critic = pair["critic"]
        max_iter = pair.get("max_iterations", 3)
        
        # Generator darf Critic spawnen (für Reflection)
        derived.setdefault(generator, {
            "mode": "pair_whitelist",
            "forbidden_subagents": ["orchestrator"],
            "allowed_subagents": [],
        })
        derived[generator]["allowed_subagents"].append({
            "target": critic,
            "purpose": f"reflection-loop:{pair_id}",
            "max_iterations": max_iter,
        })
        
        # Critic darf Generator spawnen (für Return-Loop)
        derived.setdefault(critic, {
            "mode": "pair_whitelist",
            "forbidden_subagents": ["orchestrator"],
            "allowed_subagents": [],
        })
        derived[critic]["allowed_subagents"].append({
            "target": generator,
            "purpose": f"reflection-loop:{pair_id}",
            "max_iterations": max_iter,
        })
    
    return derived
```

### Bestehende Reflection-Pairs → Abgeleitete Whitelist

Aus `role-defaults.yaml:450-475`:

| `reflection_pair` | Generator | Critic | Abgeleitete Whitelist |
|---|---|---|---|
| `dev-review-loop` | `developer` | `code-reviewer` | beide dürfen sich gegenseitig |
| `se-requirements-loop` | `se-requirements` | `se-critic` | beide |
| `se-architect-loop` | `se-architect` | `se-critic` | beide |
| `se-test-loop` | `se-test-engineer` | `se-testreviewer` | beide |
| `se-dev-review-loop` | `se-developer` | `code-reviewer` | beide |

→ **5 Reflection-Pairs × 2 Richtungen = 10 auto-abgeleitete Whitelist-Einträge** (plus manuelle Eskalations- und Pipeline-Paare).

---

## 16.5.5 Provider-Implementierung

### Tabelle der Provider-Mechanismen

| Provider | Native Spawn-Tools | Mechanismus für Restriction | Durchsetzungs-Stärke |
|---|---|---|---|
| **Claude** | `Task`, `Agent` | `tools:`-Liste filtern + Body-Constraint | stark (Frontmatter-Filter) |
| **Opencode** | `task`, `Agent` | `permission.task: deny/allow` + Body-Constraint | stark (Permission-System) |
| **Gemini** | `define_subagent`, `send_message`, `invoke_subagent` | Session-Bootstrap-Constraint-Text | mittel (Doku, kein Tech-Mechanismus) |
| **Continue** | keine (Text-Mentions) | nicht möglich — nur Body-Constraint | schwach (Doku) |
| **Copilot** | keine (Text-Mentions) | nicht möglich — nur Body-Constraint | schwach (Doku) |

### Sync-Funktion `scripts/lib/agents.py:_apply_subagent_restrictions()`

```python
def _apply_subagent_restrictions(
    content: str,
    role: str,
    config: dict,
    variables: dict,
    provider: str,
    log: SyncLog,
) -> str:
    """Provider-spezifische Tool/Subagent-Restrictions in Frontmatter injizieren.
    
    Liest spawn_policy aus role-defaults.yaml und übersetzt sie in die
    Provider-native Permission-Syntax.
    """
    if role == "orchestrator":
        return content  # Orchestrator darf alles (außer self)
    
    role_cfg = _load_role_config(role, config)
    spawn_policy = role_cfg.get("spawn_policy", {"mode": "open"})
    mode = spawn_policy.get("mode", "open")
    forbidden = set(spawn_policy.get("forbidden_subagents", []))
    allowed = spawn_policy.get("allowed_subagents", [])
    
    # Singleton-Hard-Inject: orchestrator IMMER verboten für Worker
    forbidden.add("orchestrator")
    
    if mode == "open":
        return content
    
    # Provider-spezifische Umsetzung
    if provider == "Opencode":
        if mode == "closed":
            # Komplett sperren
            content = _update_permission_field(content, "task", "deny")
            content = _update_permission_field(content, "Agent", "deny")
        elif mode == "pair_whitelist":
            # task: allow (für erlaubte Paare), Body-Constraint macht die Auswahl
            content = _update_permission_field(content, "task", "allow")
            content = _update_permission_field(content, "Agent", "allow")
            content = _inject_body_constraint(content, role, forbidden, allowed)
    
    elif provider == "Claude":
        if mode == "closed":
            # Task/Agent komplett aus tools: entfernen
            content = _remove_from_tools(content, ["Task", "Agent"])
        elif mode == "pair_whitelist":
            # Task/Agent behalten, aber Body-Constraint macht die Auswahl
            content = _inject_body_constraint(content, role, forbidden, allowed)
    
    elif provider == "Gemini":
        # Session-Bootstrap-Constraint (wird in lib/context.py behandelt, nicht hier)
        # Hier nur Marker setzen
        content = _inject_body_constraint(content, role, forbidden, allowed)
    
    elif provider in ("Continue", "Copilot"):
        # Kein nativer Mechanismus — nur Body-Constraint
        content = _inject_body_constraint(content, role, forbidden, allowed)
        log.warn(
            f"{provider}/{role}: kein technischer Spawn-Schutz verfügbar — "
            f"nur Doku-Constraint injiziert"
        )
    
    return content
```

### Body-Constraint-Template

```python
def _inject_body_constraint(content, role, forbidden, allowed):
    """Injiziert hartkodierte Constraint-Liste in den Body (vor </body>)."""
    if not forbidden and not allowed:
        return content
    
    lines = ["", "## Subagent-Spawn Constraints (auto-generated by sync.py)", ""]
    
    # Verbotene Ziele
    if forbidden:
        if "*" in forbidden:
            lines.append("- **Du darfst KEINE Sub-Agents dispatchen.**")
        else:
            targets = sorted(forbidden - {"orchestrator"})  # orchestrator separat
            if targets:
                lines.append(f"- **Verboten:** {', '.join(targets)}")
            lines.append("- **Singleton-Regel:** `orchestrator` darf NUR durch `main_chat` "
                         "gespawnt werden — niemals durch Worker-Agents.")
    
    # Erlaubte Ziele
    if allowed:
        if isinstance(allowed[0], dict):
            for pair in allowed:
                purpose = pair.get("purpose", "")
                lines.append(f"- **Erlaubt:** `{pair['target']}` ({purpose})")
        else:
            lines.append(f"- **Erlaubt:** {', '.join(allowed)}")
    
    lines.append("")
    lines.append("> **Hinweis:** Bei Opencode/Claude ist dies eine Frontmatter-Restriction. "
                 "Bei Continue/Copilot ist es eine reine Verhaltensregel ohne technische Sperre.")
    lines.append("")
    
    return content.rstrip() + "\n" + "\n".join(lines)
```

### Beispiel-Output für `developer.md` (Opencode)

```yaml
---
name: developer
description: "..."
mode: subagent
model: opencode-go/minimax-m3
permission:
  bash: allow
  read: allow
  edit: allow
  glob: allow
  grep: allow
  todowrite: allow
  task: allow
  Agent: allow
---

# Developer — {{PROJECT_NAME}}

> **Extension:** Falls ...

## Subagent-Spawn Constraints (auto-generated by sync.py)

- **Singleton-Regel:** `orchestrator` darf NUR durch `main_chat` gespawnt werden — niemals durch Worker-Agents.
- **Erlaubt:** `code-reviewer` (reflection-loop:dev-review-loop)
- **Erlaubt:** `tester` (test-delegation)

> **Hinweis:** Bei Opencode/Claude ist dies eine Frontmatter-Restriction. ...
```

---

## 16.5.6 Integration in `rules/1-generic/a2a-delegation-gates.md`

Gate #5 wurde implementiert — siehe `rules/1-generic/a2a-delegation-gates.md` Abschnitt "Singleton-Regel: Orchestrator-Spawn".

---

## 16.5.7 Test-Strategie

`tests/test_subagent_restrictions.py` — Unit-Tests pro Provider und pro Rolle:

```python
import pytest
from pathlib import Path
from scripts.lib.agents import _apply_subagent_restrictions, _derive_spawn_policy_from_reflection_pairs
from scripts.lib.config import load_role_defaults

ROLE_DEFAULTS = load_role_defaults(Path("config/role-defaults.yaml"))


# ── Singleton-Regel (universal) ──

def test_every_worker_has_orchestrator_in_forbidden():
    """Jeder Worker-Agent MUSS orchestrator in forbidden_subagents haben."""
    workers = [r for r in ROLE_DEFAULTS["roles"] if r != "orchestrator"]
    for worker in workers:
        policy = ROLE_DEFAULTS["roles"][worker].get("spawn_policy", {})
        forbidden = policy.get("forbidden_subagents", [])
        assert "orchestrator" in forbidden, \
            f"Worker '{worker}' fehlt 'orchestrator' in forbidden_subagents"


def test_orchestrator_can_spawn_all_workers():
    """Orchestrator darf alle Worker dispatchen (außer sich selbst)."""
    policy = ROLE_DEFAULTS["roles"]["orchestrator"].get("spawn_policy", {})
    forbidden = policy.get("forbidden_subagents", [])
    assert "orchestrator" in forbidden
    assert len(forbidden) == 1  # NUR self verboten


# ── Provider-spezifische Outputs ──

def test_opencode_worker_has_task_permission():
    """Opencode-Worker hat task-Permission, aber Body-Constraint verbietet orchestrator."""
    content = Path(".opencode/agents/developer.md").read_text(encoding="utf-8")
    fm = _parse_yaml_frontmatter(content)
    assert "task" in fm.get("permission", {}), "task-Permission fehlt"
    assert "orchestrator" in _extract_body_constraints(content)


def test_opencode_closed_worker_has_task_deny():
    """Terminal-Worker (git) hat task: deny."""
    content = Path(".opencode/agents/git.md").read_text(encoding="utf-8")
    fm = _parse_yaml_frontmatter(content)
    assert fm["permission"].get("task") == "deny", \
        "Terminal-Worker MUSS task: deny haben"


def test_claude_worker_lacks_task_and_agent_in_tools():
    """Claude-Worker (closed mode) hat weder Task noch Agent in tools:."""
    content = Path(".claude/agents/git.md").read_text(encoding="utf-8")
    fm = _parse_yaml_frontmatter(content)
    tools = fm.get("tools", [])
    assert "Task" not in tools
    assert "Agent" not in tools


def test_claude_pair_whitelist_worker_has_body_constraint():
    """Claude-Worker (pair_whitelist) hat Body-Constraint mit erlaubten Zielen."""
    content = Path(".claude/agents/developer.md").read_text(encoding="utf-8")
    constraints = _extract_body_constraints(content)
    assert "code-reviewer" in constraints
    assert "tester" in constraints
    assert "orchestrator" in constraints  # Singleton-Regel


def test_gemini_worker_has_bootstrap_constraint():
    """Gemini-Worker: Session-Bootstrap enthält Spawn-Constraint."""
    bootstrap = Path(".gemini/agents/.agent-meta-managed").read_text(encoding="utf-8")
    assert "orchestrator" in bootstrap
    assert "Singleton-Regel" in bootstrap or "main_chat" in bootstrap


# ── Auto-Ableitung aus reflection_pairs ──

def test_reflection_pairs_auto_derived():
    """spawn_policy wird automatisch aus reflection_pairs abgeleitet."""
    derived = _derive_spawn_policy_from_reflection_pairs(ROLE_DEFAULTS)
    
    # dev-review-loop
    assert "code-reviewer" in [p["target"] for p in derived["developer"]["allowed_subagents"]]
    assert "developer" in [p["target"] for p in derived["code-reviewer"]["allowed_subagents"]]
    
    # se-architect-loop
    assert "se-critic" in [p["target"] for p in derived["se-architect"]["allowed_subagents"]]
    assert "se-architect" in [p["target"] for p in derived["se-critic"]["allowed_subagents"]]
    
    # se-test-loop
    assert "se-testreviewer" in [p["target"] for p in derived["se-test-engineer"]["allowed_subagents"]]


def test_junior_developer_can_only_escalate():
    """junior-developer darf nur developer (Eskalation) — nicht senior, nicht orchestrator."""
    policy = ROLE_DEFAULTS["roles"]["junior-developer"]["spawn_policy"]
    assert "orchestrator" in policy["forbidden_subagents"]
    assert "senior-developer" in policy["forbidden_subagents"]
    targets = [p["target"] for p in policy["allowed_subagents"]]
    assert targets == ["developer"]


# ── Cross-Provider Konsistenz ──

@pytest.mark.parametrize("provider,expected_deny", [
    ("Claude", "tools-feld-filter"),
    ("Opencode", "permission-deny"),
    ("Gemini", "bootstrap-constraint"),
    ("Continue", "body-constraint-only"),
    ("Copilot", "body-constraint-only"),
])
def test_provider_mechanism_consistent(provider, expected_deny):
    """Jeder Provider hat einen definierten Restriction-Mechanismus."""
    content = _read_agent_for_provider("git", provider)
    if expected_deny == "permission-deny":
        fm = _parse_yaml_frontmatter(content)
        assert fm["permission"]["task"] == "deny"
    elif expected_deny == "tools-feld-filter":
        fm = _parse_yaml_frontmatter(content)
        assert "Task" not in fm.get("tools", [])
    elif expected_deny in ("bootstrap-constraint", "body-constraint-only"):
        assert "Subagent-Spawn Constraints" in content


# ── Hilfsfunktionen ──

def _parse_yaml_frontmatter(content: str) -> dict:
    import yaml
    if not content.startswith("---"):
        return {}
    end = content.find("\n---", 3)
    return yaml.safe_load(content[3:end]) or {}


def _extract_body_constraints(content: str) -> list:
    """Extrahiert erlaubte/verbotene Agenten aus dem Body-Constraint-Block."""
    import re
    m = re.search(r"## Subagent-Spawn Constraints.*?(?=\n## |\Z)", content, re.DOTALL)
    if not m:
        return []
    return m.group(0)
```

---

## 16.5.8 Kompatibilitäts-Matrix (Erweiterung)

| Komponente | Singleton-konform? | Mechanismus | Hinweis |
|---|---|---|---|
| `orchestrator` (main_chat) | ✓ | nichts erforderlich | Darf alle Worker |
| `developer` | ✓ | Opencode: `permission.task: allow` + Body-Constraint | Reflection-Loop mit code-reviewer erlaubt |
| `junior-developer` | ✓ | dito | Eskaliert zu developer (nicht senior) |
| `senior-developer` | ✓ | dito | Reflection + Eskalation + De-Eskalation |
| `code-reviewer` | ✓ | dito | Reflection-Loop zurück zu developer |
| `feature` | ✓ | dito | Pipeline-Coordinator |
| `se-requirements` | ✓ | dito | Reflection mit se-critic |
| `se-architect` | ✓ | dito | Reflection mit se-critic |
| `se-developer` | ✓ | dito | Reflection mit se-critic + code-reviewer |
| `se-test-engineer` | ✓ | dito | Reflection mit se-testreviewer |
| `se-critic` | ✓ | dito | Reflection zurück zu Generatoren |
| `se-testreviewer` | ✓ | dito | Reflection zurück zu se-test-engineer |
| `git` | ✓ (closed) | Opencode: `permission.task: deny` | Terminal-Worker |
| `documenter` | ✓ (closed) | dito | Terminal-Worker |
| `feedback` | ✓ (closed) | dito | Terminal-Worker |
| `orchestrator-iteration` | ✓ (closed) | — | existiert nicht (künftig) |
| Reflection-Loops (alle 5) | ✓ | aus `reflection_pairs` abgeleitet | — |
| `delegation-syntax.yaml:fallback` (Worker) | ⚠ Rewrite nötig | `fallback: "An Aufrufer zurückgeben"` | Orchestrator behält `fallback: @orchestrator` |
| `delegation-syntax.yaml:fanout` Templates | ⚠ | Worker bekommen `fanout` NICHT injiziert | Nur Orchestrator + feature |
| `lib/runtime.py` SubagentBarrier | n/a | keine Änderung nötig | Provider-Permissions enforced bereits |

---

## 16.5.9 Interaktion mit bestehenden Mechanismen

| Bestehender Mechanismus | Interaktion mit Spawn-Policy |
|---|---|
| `orchestrator-guard.sh` Hook | bleibt — schützt Main-Chat-Writes (komplementär zu Spawn-Policy) |
| `a2a-delegation-gates.md` Rule (4 Gates) | bleibt — bekommt **Gate #5 (Singleton)** ergänzt |
| `reflection_pairs` | wird zur **Single Source of Truth** für `spawn_policy.allowed_subagents` |
| `lib/runtime.py` SubagentBarrierRuntime | bleibt unverändert — Provider enforced bereits |
| `lib/agents.py:1595` `opencode_deny_critical` | erweitert um `task`, `Agent` |
| `config/delegation-syntax.yaml:fallback` | wird umgeschrieben — Worker bekommen `fallback: "An Aufrufer zurückgeben"` |
| `config/role-defaults.yaml:handoff.target_roles` | bleibt — beeinflusst nur Handoff-Contract, nicht Spawn-Policy |
| `orchestrator-iteration` (in Konzept erwähnt) | noch nicht existent — Platzhalter in Singleton-Config reserviert |

### `delegation-syntax.yaml:fallback` — Umschreibung

**Heute (Bug-Einladung):**
```yaml
Claude:
  fallback: "Delegiere via `Agent(subagent_type=\"orchestrator\", prompt=\"<task>\")` an den Orchestrator."
Opencode:
  fallback: "@orchestrator <task>"
Gemini:
  fallback: "Bearbeite folgende Aufgabe selbst, mit höchster Sorgfalt: <task>"
```

**Neu (worker-sicher):**
```yaml
Claude:
  fallback_orchestrator: "Delegiere via `Agent(subagent_type=\"<target>\", prompt=\"<task>\")` an den Ziel-Agenten."
  fallback_worker: "Gibt diese Aufgabe an deinen Aufrufer zurück (nicht weiter delegieren)."
Opencode:
  fallback_orchestrator: "@<target> <task>"
  fallback_worker: "Gib diese Aufgabe an deinen Aufrufer zurück — KEIN Spawn."
Gemini:
  fallback_orchestrator: "Rufe den <target>-Agenten auf mit der Aufgabe: <task>"
  fallback_worker: "Bearbeite diese Aufgabe selbst und melde das Ergebnis an deinen Aufrufer."
```

`_apply_subagent_restrictions()` wählt anhand der Rolle die richtige Fallback-Variante.

---

## 16.5.10 Implementierungs-Schritte (4 Commits, ~1 Arbeitstag)

| # | Datei | Aktion | Aufwand |
|---|---|---|---|
| 1 | `config/role-defaults.yaml` | `spawn_policy` für alle Worker hinzufügen; `spawn_singleton` global | 30 min |
| 2 | `config/provider-tools.yaml` | `task` + `Agent` in `opencode_deny_critical`; `Task`+`Agent` aus Claude-Whitelist | 15 min |
| 3 | `config/delegation-syntax.yaml` | `fallback_orchestrator` / `fallback_worker` trennen | 15 min |
| 4 | `scripts/lib/agents.py` | `_apply_subagent_restrictions()` + `_derive_spawn_policy_from_reflection_pairs()` implementieren; in `sync_agents_for_provider()` aufrufen | 3-4 h |
| 5 | `rules/1-generic/a2a-delegation-gates.md` | Gate #5: Singleton-Regel ✓ **implementiert** | 15 min |
| 6 | `tests/test_subagent_restrictions.py` | Unit-Tests wie oben | 1-2 h |
| 7 | `docs/concepts/planned/prompt-modernization.md` | Verweis auf diese Architektur-Sektion; Sektion 21 erweitern | 30 min |

**Gesamt: 1 Arbeitstag**

### Branch und Commit-Strategie

```
Branch: feat/orchestrator-singleton-guard
Basis: feat/prompt-modernization-poc (oder main, je nach Merge-Status)

Commits:
  1. config(roles): add spawn_policy + spawn_singleton to role-defaults
  2. config(providers): deny task/Agent in opencode_deny_critical; remove Task/Agent from claude whitelist
  3. config(syntax): split fallback into fallback_orchestrator and fallback_worker
  4. lib(agents): add _apply_subagent_restrictions and _derive_spawn_policy_from_reflection_pairs
  5. rules(a2a): add Gate #5 — Subagent-Spawn Singleton  ✓ implementiert
  6. tests: add test_subagent_restrictions.py with 10+ test cases
  7. docs(concepts): cross-link this architecture section into prompt-modernization.md
```

---

## 16.5.11 Risiken & Mitigations

| Risiko | Impact | Wahrscheinlichkeit | Mitigation |
|---|---|---|---|
| Worker, die früher `senior-developer` für De-Eskalation dispatchen konnten, brechen | Mittel | Mittel | `junior-developer.spawn_policy.allowed_subagents` enthält `developer` als Eskalations-Pfad (nicht `senior-developer`) — Eskalation läuft über `developer` |
| Bestehende `delegation-syntax.yaml:fallback: @orchestrator` bleibt in Worker-Templates | Hoch | Hoch | `_apply_subagent_restrictions()` ersetzt `fallback` mit `fallback_worker` für alle Non-Orchestrator-Rollen |
| `Task`/`Agent` aus Claude-`tools:` entfernen bricht Provider-Layout (z.B. wenn Worker Status-Output braucht) | Niedrig | Niedrig | Claude-Modelle können ohne diese Tools trotzdem arbeiten; falls benötigt, Body-Constraint-Liste |
| Continue/Copilot haben **keinen** nativen Spawn-Schutz — Worker können `task(...)` als Text-Mention schreiben | Hoch | Hoch (Doku-only) | Body-Constraint-Block mit explizitem Warnhinweis; User-Aufklärung in CLAUDE.md; regelmäßige Audit via `scripts/audit-prompt-mode.py` |
| Reflection-Pair-Auto-Ableitung erzeugt Whitelist-Einträge die der User nicht will | Niedrig | Mittel | Explizite `allowed_subagents` in `role-defaults.yaml` haben Vorrang vor Auto-Ableitung; User kann Reflection-Pairs deaktivieren via `reflection_pairs: []` |
| Test-Repo-Workflow: `_apply_subagent_restrictions()` schreibt ungewollte Permissions | Mittel | Niedrig | Unit-Tests für jeden Provider + jeden Mode; `sync.py --validate` führt Tests aus |
| Single-Point-of-Failure: Wenn `role-defaults.yaml` korrupt, fällt Spawn-Policy auf offen → Worker könnten orchestrator spawnen | Hoch | Niedrig | Sync-Validierung prüft Pflichtfelder; `spawn_policy.mode` muss explizit gesetzt sein, sonst Fehler |

### Aufgehobene Risiken aus dem ursprünglichen Konzept

| Risiko (alt) | Status nach Singleton-Architektur |
|---|---|
| "Worker können Orchestrator dispatchen" | **RESOLVED** — Provider-Permissions + Body-Constraint verhindern |
| "Subagent-Spawn Singleton unklar" | **RESOLVED** — `spawn_singleton.allowed_callers: [main_chat]` + Gate #5 |
| "`delegation-syntax.yaml:fallback` ist Einladung zum Bug" | **RESOLVED** — `fallback_orchestrator` / `fallback_worker` getrennt |
| "Reflection-Loops werden durch Singleton-Regel gebrochen" | **RESOLVED** — Per-Pair-Whitelist mit Auto-Ableitung aus `reflection_pairs` |
| "Kein technischer Mechanismus, nur Doku" | **PARTIAL** — Body-Constraint (Phase 1) implementiert; Provider-Frontmatter-Phase ausstehend |

---

## 16.5.12 Konzept-Status

| Aspekt | Status |
|---|---|
| Singleton-Regel definiert | ✓ |
| Per-Pair-Whitelist-Architektur | ✓ |
| Auto-Ableitung aus `reflection_pairs` | ✓ |
| Provider-Implementierung (5 Provider) | ✓ |
| `role-defaults.yaml`-Schema | ✓ |
| `config/provider-tools.yaml`-Erweiterung | ✓ |
| Sync-Funktion `_apply_subagent_restrictions()` | ✓ (Pseudo-Code) |
| Test-Suite (10+ Tests) | ✓ (Pseudo-Code) |
| **Body-Constraint in `sync_agents_for_provider()` (Claude)** | ✓ **implementiert 2026-06-30** |
| **Body-Constraint in `sync_agents_for_provider()` (Multi-Provider)** | ✓ **implementiert 2026-06-30** |
| **Gate #5 in `rules/1-generic/a2a-delegation-gates.md`** | ✓ **implementiert 2026-06-30** |
| **Singleton-Hint in `orchestrator.md` Anti-Recursion** | ✓ **implementiert 2026-06-30** |
| **Singleton-Regel in `CLAUDE.md`** | ✓ **implementiert 2026-06-30** |
| Provider-Frontmatter-Restrictions (Opencode `task: deny`) | ⏳ Phase 2 ausstehend |
| Claude `tools:` Filter für Worker | ⏳ Phase 2 ausstehend |
| Merge in `feat/prompt-modernization-poc` | ⏳ ausstehend |

**Status:** Aktiv — Body-Constraint Phase implementiert
**Nächster Schritt:** Phase 2 — Provider-Frontmatter-Restrictions (`spawn_policy` in `role-defaults.yaml`)