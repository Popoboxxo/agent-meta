#!/usr/bin/env python3
"""SE-Cascade Runner — provider-agnostic sequential execution.

Generates structured prompt files for each SE stage that can be executed
in any LLM environment (Gemini, Claude, Opencode, etc.).

Usage:
    python scripts/run-cascade.py --input "Stakeholder need description"
    python scripts/run-cascade.py --input-file needs.md
    python scripts/run-cascade.py --resume <session-id>
    python scripts/run-cascade.py --status <session-id>
    python scripts/run-cascade.py --list-sessions
    python scripts/run-cascade.py --clean-old --max-age 7d
"""

import argparse
import hashlib
import json
import shutil
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# SE Cascade Stage Definitions
# ---------------------------------------------------------------------------

SE_STAGES: list[dict[str, Any]] = [
    {
        "id": "l1-requirements",
        "agent": "se-requirements",
        "description": "L1 Stakeholder Needs -> Formal Requirements",
        "input_from": None,
        "output_file": "stage_0_l1_requirements.md",
    },
    {
        "id": "l1-critic",
        "agent": "se-critic",
        "description": "Critique L1 Requirements",
        "input_from": "l1-requirements",
        "output_file": "stage_1_l1_critic_review.md",
    },
    {
        "id": "l2-architecture",
        "agent": "se-architect",
        "description": "L2 White-Box Decomposition",
        "input_from": "l1-requirements",
        "output_file": "stage_2_l2_architecture.md",
    },
    {
        "id": "l2-critic",
        "agent": "se-critic",
        "description": "Critique L2 Architecture",
        "input_from": "l2-architecture",
        "output_file": "stage_3_l2_critic_review.md",
    },
    {
        "id": "interface-sync",
        "agent": "se-interface-mgr",
        "description": "Signal Flow Synchronization",
        "input_from": "l2-architecture",
        "output_file": "stage_4_interfaces.md",
    },
    {
        "id": "termination-check",
        "agent": "se-termination",
        "description": "Leaf or Recurse Decision",
        "input_from": "l2-architecture",
        "output_file": "stage_5_termination_decision.md",
    },
    {
        "id": "validation",
        "agent": "se-validator",
        "description": "L1 User-Journey Validation",
        "input_from": "l1-requirements",
        "output_file": "stage_6_validation.md",
    },
    {
        "id": "verification",
        "agent": "se-verifier",
        "description": "Multi-Level Verification",
        "input_from": "l2-architecture",
        "output_file": "stage_7_verification.md",
    },
    {
        "id": "integration-test",
        "agent": "se-integration-and-test-manager",
        "description": "V&V Orchestration",
        "input_from": "l2-architecture",
        "output_file": "stage_8_integration_test_plan.md",
    },
]

# Build a lookup for stage resolution
_STAGE_INDEX: dict[str, int] = {s["id"]: i for i, s in enumerate(SE_STAGES)}

# ---------------------------------------------------------------------------
# Session Management
# ---------------------------------------------------------------------------

_CASCADE_DIR_NAME = ".se-cascade"
_PROMPTS_DIR_NAME = "prompts"
_SESSION_META_NAME = "session.json"


def _get_cascade_root() -> Path:
    """Return the root directory for all cascade sessions."""
    return Path.cwd() / _CASCADE_DIR_NAME


def generate_session_id(input_text: str) -> str:
    """Generate a unique session ID from timestamp and input hash."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    short_hash = hashlib.sha256(input_text.encode("utf-8")).hexdigest()[:8]
    return f"cascade-{ts}-{short_hash}"


def create_session_dir(session_id: str) -> Path:
    """Create and return the session directory tree."""
    root = _get_cascade_root() / session_id
    (root / _PROMPTS_DIR_NAME).mkdir(parents=True, exist_ok=True)
    return root


def _write_session_meta(session_dir: Path, initial_input: str, session_id: str) -> None:
    """Write session metadata JSON."""
    meta = {
        "session_id": session_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "initial_input": initial_input,
        "current_stage": -1,
        "completed_stages": [],
    }
    meta_path = session_dir / _SESSION_META_NAME
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _read_session_meta(session_dir: Path) -> dict[str, Any]:
    """Read session metadata JSON."""
    meta_path = session_dir / _SESSION_META_NAME
    with meta_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_session_meta_dict(session_dir: Path, meta: dict[str, Any]) -> None:
    """Write updated session metadata JSON."""
    meta_path = session_dir / _SESSION_META_NAME
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
        f.write("\n")


# ---------------------------------------------------------------------------
# Stage I/O
# ---------------------------------------------------------------------------

def save_stage_output(stage: dict[str, Any], output_content: str, session_dir: Path) -> Path:
    """Persist stage output to the session directory."""
    out_path = session_dir / stage["output_file"]
    with out_path.open("w", encoding="utf-8") as f:
        f.write(output_content)
    return out_path


def load_stage_output(stage_id: str, session_dir: Path) -> str | None:
    """Load the output of a completed stage, if present."""
    idx = _STAGE_INDEX.get(stage_id)
    if idx is None:
        return None
    stage = SE_STAGES[idx]
    out_path = session_dir / stage["output_file"]
    if out_path.exists():
        return out_path.read_text(encoding="utf-8")
    return None


def _collect_context(stage: dict[str, Any], session_dir: Path) -> str:
    """Build a context block from previous stage outputs for the prompt."""
    parts: list[str] = []
    dep_id = stage.get("input_from")
    if dep_id is None:
        return ""
    dep_output = load_stage_output(dep_id, session_dir)
    if dep_output:
        dep_stage = SE_STAGES[_STAGE_INDEX[dep_id]]
        parts.append(f"## Input from previous stage: {dep_stage['id']}")
        parts.append(f"(File: `{dep_stage['output_file']}`)")
        parts.append("```")
        # Truncate very long outputs to keep prompt manageable
        if len(dep_output) > 4000:
            parts.append(dep_output[:4000])
            parts.append(f"\n... [truncated, total length: {len(dep_output)} chars]")
        else:
            parts.append(dep_output)
        parts.append("```")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Prompt Generation
# ---------------------------------------------------------------------------

def generate_prompt_file(stage: dict[str, Any], initial_input: str, session_dir: Path) -> Path:
    """Create a structured prompt file for the given stage."""
    prompts_dir = session_dir / _PROMPTS_DIR_NAME
    idx = _STAGE_INDEX[stage["id"]]
    prompt_filename = f"stage_{idx:02d}_{stage['id']}.md"
    prompt_path = prompts_dir / prompt_filename

    context = _collect_context(stage, session_dir)

    lines: list[str] = [
        f"# SE-Cascade Stage {idx}: {stage['description']}",
        "",
        f"**Agent:** `{stage['agent']}`",
        f"**Stage ID:** `{stage['id']}`",
        f"**Session:** `{session_dir.name}`",
        "",
        "---",
        "",
        "## Your Task",
        "",
        textwrap.dedent(
            f"""\
            You are acting as the `{stage['agent']}` agent in a generic Systems Engineering cascade.
            Follow your system instructions (role knowledge) and execute the task described below.
            """
        ).strip(),
        "",
        "### Stage Objective",
        f"{stage['description']}",
        "",
    ]

    if idx == 0:
        lines.extend([
            "### Initial Stakeholder Need",
            "",
            "```",
            initial_input,
            "```",
            "",
        ])
    else:
        if context:
            lines.extend([
                "### Context from Previous Stages",
                "",
                "Use the following outputs as context for your work. Do not modify them.",
                "",
                context,
                "",
            ])
        else:
            lines.extend([
                "### Context from Previous Stages",
                "",
                "_No prior output available. Proceed with available information._",
                "",
            ])

    lines.extend([
        "## Expected Output",
        "",
        "Save your complete result to the file:",
        f"`{stage['output_file']}`",
        f"in the session directory `.se-cascade/{session_dir.name}/`",
        "",
        "Format your output as structured Markdown (sections, tables, JSON blocks where appropriate).",
        "",
        "---",
        "",
        "## Next Steps (for the User)",
        "",
        "1. Copy this prompt into your LLM environment (Gemini, Claude, Opencode, etc.)",
        "2. Execute the task with the agent role specified above.",
        "3. Save the response to the indicated output file.",
        "4. Run the cascade runner again to proceed to the next stage:",
        f"   `python scripts/run-cascade.py --resume {session_dir.name}`",
        "",
    ])

    with prompt_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return prompt_path


# ---------------------------------------------------------------------------
# Session Lifecycle
# ---------------------------------------------------------------------------

def _start_session(initial_input: str) -> Path:
    """Initialize a new cascade session and generate all stage prompts."""
    session_id = generate_session_id(initial_input)
    session_dir = create_session_dir(session_id)
    _write_session_meta(session_dir, initial_input, session_id)

    print(f"Created session: {session_id}")
    print(f"Session directory: {session_dir}")
    print()

    for stage in SE_STAGES:
        prompt_path = generate_prompt_file(stage, initial_input, session_dir)
        print(f"  [{stage['id']}] Prompt -> {prompt_path.relative_to(Path.cwd())}")

    print()
    print("Next step:")
    print(f"  1. Open: {session_dir / _PROMPTS_DIR_NAME / 'stage_00_l1-requirements.md'}")
    print("  2. Copy the prompt into your IDE / LLM.")
    print("  3. Save the response to the indicated output file.")
    print(f"  4. Resume: python scripts/run-cascade.py --resume {session_id}")
    return session_dir


def _resume_session(session_id: str) -> None:
    """Resume a session by finding the next incomplete stage and regenerating its prompt."""
    session_dir = _get_cascade_root() / session_id
    if not session_dir.exists():
        print(f"ERROR: Session not found: {session_id}", file=sys.stderr)
        sys.exit(1)

    meta = _read_session_meta(session_dir)
    initial_input = meta["initial_input"]

    # Determine next stage
    next_stage_idx = 0
    for i, stage in enumerate(SE_STAGES):
        out_path = session_dir / stage["output_file"]
        if out_path.exists():
            next_stage_idx = i + 1

    if next_stage_idx >= len(SE_STAGES):
        print("All stages completed.")
        print(f"Session directory: {session_dir}")
        return

    next_stage = SE_STAGES[next_stage_idx]
    prompt_path = generate_prompt_file(next_stage, initial_input, session_dir)

    # Update meta
    meta["current_stage"] = next_stage_idx
    completed = [SE_STAGES[j]["id"] for j in range(next_stage_idx)]
    meta["completed_stages"] = completed
    _write_session_meta_dict(session_dir, meta)

    print(f"Resuming session: {session_id}")
    print(f"Completed stages: {', '.join(completed) or 'none'}")
    print(f"Next stage: {next_stage['id']} ({next_stage['description']})")
    print()
    print(f"Open prompt: {prompt_path.relative_to(Path.cwd())}")
    print("Copy the prompt into your IDE / LLM and save the result to the indicated file.")
    print(f"Then resume again with: python scripts/run-cascade.py --resume {session_id}")


def _session_status(session_id: str) -> None:
    """Print the status of a session."""
    session_dir = _get_cascade_root() / session_id
    if not session_dir.exists():
        print(f"ERROR: Session not found: {session_id}", file=sys.stderr)
        sys.exit(1)

    meta = _read_session_meta(session_dir)
    print(f"Session: {session_id}")
    print(f"Created: {meta.get('created_at', 'unknown')}")
    print()

    for stage in SE_STAGES:
        out_path = session_dir / stage["output_file"]
        status = "DONE" if out_path.exists() else "PENDING"
        print(f"  [{status:8s}] {stage['id']:20s} - {stage['description']}")


def _list_sessions() -> None:
    """List all cascade sessions."""
    root = _get_cascade_root()
    if not root.exists():
        print("No sessions found.")
        return

    sessions = sorted([d for d in root.iterdir() if d.is_dir()], key=lambda p: p.name)
    if not sessions:
        print("No sessions found.")
        return

    print(f"{'Session ID':<50s} {'Stages':>8s} {'Created':>20s}")
    print("-" * 80)
    for session_dir in sessions:
        meta_path = session_dir / _SESSION_META_NAME
        completed = sum(1 for s in SE_STAGES if (session_dir / s["output_file"]).exists())
        total = len(SE_STAGES)
        created = "unknown"
        if meta_path.exists():
            try:
                meta = _read_session_meta(session_dir)
                created = meta.get("created_at", "unknown")[:19].replace("T", " ")
            except Exception:  # noqa: BLE001, S110
                pass
        print(f"{session_dir.name:<50s} {completed}/{total:<5d} {created:>20s}")


def _clean_old_sessions(max_age_days: int) -> None:
    """Remove sessions older than max_age_days."""
    root = _get_cascade_root()
    if not root.exists():
        print("No sessions to clean.")
        return

    cutoff = datetime.now(timezone.utc).timestamp() - (max_age_days * 86400)
    removed = 0
    for session_dir in root.iterdir():
        if not session_dir.is_dir():
            continue
        try:
            mtime = session_dir.stat().st_mtime
            if mtime < cutoff:
                shutil.rmtree(session_dir)
                removed += 1
        except OSError:
            continue
    print(f"Removed {removed} session(s) older than {max_age_days} day(s).")


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="run-cascade.py",
        description="SE-Cascade Runner — generate structured prompts for sequential SE execution.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--input",
        dest="input_text",
        help="Initial stakeholder need as a string.",
    )
    group.add_argument(
        "--input-file",
        dest="input_file",
        type=Path,
        help="Path to a file containing the stakeholder need.",
    )
    group.add_argument(
        "--resume",
        dest="resume_id",
        help="Resume an existing session by ID.",
    )
    group.add_argument(
        "--status",
        dest="status_id",
        help="Show status of an existing session.",
    )
    group.add_argument(
        "--list-sessions",
        dest="list_sessions",
        action="store_true",
        help="List all cascade sessions.",
    )
    group.add_argument(
        "--clean-old",
        dest="clean_old",
        action="store_true",
        help="Remove sessions older than --max-age days.",
    )
    parser.add_argument(
        "--max-age",
        dest="max_age",
        type=int,
        default=7,
        help="Maximum age in days for --clean-old (default: 7).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the SE-Cascade Runner."""
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if args.input_text:
        _start_session(args.input_text)
    elif args.input_file:
        if not args.input_file.exists():
            print(f"ERROR: Input file not found: {args.input_file}", file=sys.stderr)
            return 1
        text = args.input_file.read_text(encoding="utf-8")
        _start_session(text)
    elif args.resume_id:
        _resume_session(args.resume_id)
    elif args.status_id:
        _session_status(args.status_id)
    elif args.list_sessions:
        _list_sessions()
    elif args.clean_old:
        _clean_old_sessions(args.max_age)
    else:
        parser.print_help()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
