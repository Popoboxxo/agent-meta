"""Orchestrator permissionMode framework default (roadmap 2.3 / 0.4, E-04).

Claude Code treats ``permissionMode: plan`` as read-only for subagents, which
conflicts with the orchestrator's ``Write`` tool and checkpointing. The
framework default in ``config/role-defaults.yaml`` must therefore be
``default`` so the orchestrator can actually write. Project-level overrides
may still opt into another mode.
"""
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_orchestrator_permission_mode_defaults_to_default():
    data = yaml.safe_load(
        (_REPO_ROOT / "config" / "role-defaults.yaml").read_text(encoding="utf-8")
    )
    mode = data["roles"]["orchestrator"]["permission_mode"]
    assert mode == "default", (
        f"orchestrator permission_mode must be 'default', got {mode!r}"
    )
