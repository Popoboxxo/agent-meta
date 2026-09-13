{{#if CHECKPOINTING_ENABLED}}
**Checkpoint after >5 steps** — `.meta-viz/checkpoint-<timestamp>.json`:
```json
{
  "session_id": "<YYYYMMDD-HHMMSS>",
  "created_at": "<ISO-8601>",
  "task_summary": "<one-sentence description of the overall task>",
  "completed_steps": [
    { "step": 1, "agent": "<agent>", "result_key": "<key>", "status": "done" }
  ],
  "pending_steps": [
    { "step": 2, "agent": "<agent>", "task": "<task-summary>" }
  ],
  "context": "<summary of relevant intermediate results, max 3 sentences>"
}
```

**When to write:** before every BARRIER point — after all parallel sub-tasks were
started but before their results are awaited. Protects progress against a context
reset during ongoing delegation. The machine-readable store is written by the
`--checkpoint` production mode; the manual JSON format above stays documented for
backward compatibility.

**When to read:** on session start — before any new plan work — run the read-only
rehydrate path `python3 scripts/sync.py --rehydrate` (`scripts/lib/rehydrate.py`).
It resolves the newest unfinished session from the authoritative machine recovery
source, the `CheckpointStore` session files under
`.meta-viz/checkpoints/<session>.json` (`scripts/lib/checkpoint.py`) — the framework
default of the configurable `progress.checkpoint-dir` (override via the top-level
`progress` block in `.meta-config/project.yaml`) — and prints the
resume context. It writes nothing. The manual `.meta-viz/checkpoint-<ts>.json` format
documented above remains readable for backward compatibility, but the runtime does not
write it. On a hit, inform the user:
> "There is an unfinished checkpoint from `<created_at>`: `<task_summary>`.
> Resume from step `<next pending_step>`?"
On confirmation, work through `pending_steps` sequentially, skip `completed_steps`, and
resume exactly at `next_task_ref` — never silently skip or reorder.

**Cleanup:** max checkpoint size: 50 KB — truncate large `context` fields. Checkpoints
are never deleted automatically (neither by age nor on session start).

**Progress file (issue #682 §6, Tier model — live-progress-channel design, 2026-09-10):** if the
runtime calls `CheckpointStore.save_checkpoint()` (the Python API in `scripts/lib/checkpoint.py`,
distinct from the manually-written checkpoint format above), it writes `.meta-viz/progress/current.md`
— the framework default of the configurable `progress.dir` (override via the top-level `progress` block in
`.meta-config/project.yaml`) — overwritten (non-historized) on Tier-A providers (verified `hook_protocol`, e.g. Claude/Gemini —
see the chat-push instruction in §7), appended with session-start rotation on every Tier-B provider,
since the file is their only live channel. Resume logic still reads the JSON checkpoints; `current.md`
is for a human glancing at the repo, not parsed by any code path — no replacement for the manually
written checkpoint format above.
{{/if}}
