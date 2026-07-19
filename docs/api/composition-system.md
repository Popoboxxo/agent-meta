# Agent-Meta Composition System

The Composition System of Agent-Meta allows you to adapt generic agents to platform-specific and project-specific requirements. The execution and generation are handled through a strict inheritance hierarchy.

## Override and Inheritance Order

The configuration of an agent is assembled in the following order (each step overrides the previous one):

1. **`1-generic`**: The universal, provider-agnostic base templates.
2. **`2-platform`**: Platform-specific overrides (e.g., Sharkord, Home Assistant, Agent-Meta itself).
3. **`3-project/<role>.md`**: Project-specific overrides.
4. **`0-external`**: External Git submodules for external skills.

## Two Modes for Overrides

In the `2-platform` and `3-project` directories, you can customize agents in two ways:

### 1. Full-Replacement Mode
Create a file named after the role (e.g., `developer.md`). If this file **does not** contain an `extends:` attribute in its YAML frontmatter, it completely replaces the generic agent.

### 2. Composition Mode (`extends:` + `patches:`)
This is the recommended way to patch agents without duplicating the core code. You specify which agent you are extending in the frontmatter and define patch operations.

**Example `2-platform/developer.md`:**
```yaml
extends: "1-generic/developer.md"
patches:
  - op: append-after
    anchor: "## Section"
    content: |
      ## New Content...
  - op: replace
    anchor: "## Section"
    content: |
      ## Replaced Content...
  - op: delete
    anchor: "## Section"
  - op: append
    content: |
      ## Appended at end...
```

## Runtime Extensions

While `2-platform` is processed during generation (build-time, via `sync.py`), there are also runtime extensions.
Files in the format `3-project/<role>-ext.md` are loaded **additively at runtime** by the providers (Claude, Gemini). They are perfectly suited for short-lived, task-specific instructions to specific agents.

You can create extensions using:
```bash
python scripts/sync.py --create-ext developer
```
