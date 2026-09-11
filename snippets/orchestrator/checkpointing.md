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
reset during ongoing delegation.

**When to read:** on session start, check whether checkpoints exist:
1. Scan `.meta-viz/checkpoint-*.json` (newest by `created_at` first)
2. On a hit, inform the user:
   > "There is an unfinished checkpoint from `<created_at>`: `<task_summary>`.
   > Resume from step `<next pending_step>`?"
3. On confirmation, work through `pending_steps` sequentially, skip `completed_steps`
4. After completion, delete the checkpoint file

**Cleanup:** delete checkpoints older than 24h automatically (on next start).
Max checkpoint size: 50 KB — truncate large `context` fields.

**Progress file (issue #682 §6, Tier model — live-progress-channel design, 2026-09-10):** if the
runtime calls `CheckpointStore.save_checkpoint()` (the Python API in `scripts/lib/checkpoint.py`,
distinct from the manually-written checkpoint format above), it writes `.meta-viz/progress/current.md`
— overwritten (non-historized) on Tier-A providers (verified `hook_protocol`, e.g. Claude/Gemini —
see the chat-push instruction in §7), appended with session-start rotation on every Tier-B provider,
since the file is their only live channel. Resume logic still reads the JSON checkpoints; `current.md`
is for a human glancing at the repo, not parsed by any code path — no replacement for the manually
written checkpoint format above.
{{/if}}
