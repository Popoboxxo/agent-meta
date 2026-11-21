"""K-01/K-13 (#1158): verify DoD gating on a rendered project.

K-01: with the ``rapid-prototyping`` preset (``req-traceability: false`` and
``tests-required: false``) the orchestrator must not render the REQ/test
mandates. The template source is gated; this pins the *rendered* output.

K-13: the original issue anchor pointed at a True/False default for
``PROJECT_SPECIFIC_AGENTS``. In the current tree that variable is a hardcoded
empty string in ``config.build_variables`` and does not exist in
``standalone.py``; there is no inconsistent boolean default to reproduce, so
K-13 is documented as not reproducible rather than pinned by a test.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from tests.test_ac01_render_identity import _make_project  # noqa: E402


def test_rapid_prototyping_render_has_no_req_or_test_mandates(tmp_path):
    project = _make_project(tmp_path, "Claude")
    orchestrator = project / ".claude" / "agents" / "orchestrator.md"
    assert orchestrator.is_file()
    text = orchestrator.read_text(encoding="utf-8")
    assert "No feature without REQ-ID" not in text
    assert "No code without tests" not in text
