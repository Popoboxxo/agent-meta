---
description: Change the release checklist mode of this project
allowed-tools: ["Read", "Edit", "Bash"]
argument-hint: "<off|advisory|strict>"
---

Change the project release checklist mode. $ARGUMENTS

Valid modes: `off` (default), `advisory`, `strict`.
- `off` — no checklist block is rendered.
- `advisory` — mandatory items are reported but do not stop the release.
- `strict` — a failed mandatory item stops the release. This is a prompt convention only, gates stay hard in every mode.

Read `.meta-config/project.yaml`, confirm the change with the user, then update `release-checklist.mode` (create the block if it is missing). Quote the value, e.g. `mode: "off"` — YAML 1.1 parses an unquoted `off` as a boolean, which the loader normalizes back to `"off"`; only an unquoted `on`/`true` is rejected with "quote the value".

For `strict`, explicitly confirm the behaviour change ("prompt convention only, gates stay hard") before writing.

After the edit run sync (project: `python .agent-meta/scripts/sync.py`; agent-meta itself: `python scripts/sync.py`), then validate with `python scripts/sync.py --validate` (project: `python .agent-meta/scripts/sync.py --validate`) and report the result.
