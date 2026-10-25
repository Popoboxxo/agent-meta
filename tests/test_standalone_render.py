"""AC-27: the standalone export names the framework-default sink ``.tmp``.

Normative source: ``docs/specs/2026-10-24-tmp-sink-injection-spec.md``
AC-27 / IC-15. A standalone persona has no project config, so there is no
``repo_containment.tmp-sink.path`` to resolve. Instead of leaking a raw
placeholder (or the safety-net note
``[TMP_SINK_PATH — not available outside a full agent-meta install]``) the
render must name the documented framework default ``.tmp`` — the same path a
fresh project install uses.

Run: python3 -m pytest tests/test_standalone_render.py -q
"""

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_STANDALONE_ROOT = _REPO_ROOT / "standalone"

# The exact safety-net string ``render_standalone_agent`` produces for any
# unresolved placeholder (``standalone.py::_LEFTOVER_PLACEHOLDER_RE``).
_TMP_SINK_NOTE_RE = re.compile(
    r"\[TMP_SINK_PATH — not available outside a full agent-meta install\]"
)

# Roles whose report/artifact targets are the only place the sink appears in
# the standalone export (AC-27 names exactly these three).
_SINK_ROLES = ("meta-doctor", "meta-optimizer", "agent-meta-manager")

# Expected framework-default sink expressions per role. Pinning the concrete
# sub-path keeps the assertion honest: it fails if the render emits ``.tmp``
# only in passing while the report targets still carry a note.
_EXPECTED_SINK_FRAGMENTS = {
    "meta-doctor": (".tmp/doctor/", ".tmp/context-report/"),
    "meta-optimizer": (".tmp/meta-optimizer/<ts>/", ".tmp/meta-optimizer/<ts>/proposal.json"),
    "agent-meta-manager": (".tmp/meta-optimizer/<ts>/",),
}


def _read(role):
    return (_STANDALONE_ROOT / "agents" / f"{role}.md").read_text(encoding="utf-8")


def test_tmp_sink_path_uses_framework_default():
    """AC-27/IC-15: no placeholder note anywhere, ``.tmp`` in the three roles."""
    offenders = []
    for path in sorted(_STANDALONE_ROOT.rglob("*.md")):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if _TMP_SINK_NOTE_RE.search(line):
                offenders.append(f"{path.relative_to(_REPO_ROOT).as_posix()}:{lineno}: {line.strip()}")
    assert not offenders, (
        "TMP_SINK_PATH rendered as a placeholder note in standalone/** (AC-27, IC-15). "
        "Set TMP_SINK_PATH = '.tmp' in standalone.py::_standalone_variables:\n"
        + "\n".join(offenders)
    )

    for role in _SINK_ROLES:
        text = _read(role)
        assert "{{TMP_SINK_PATH}}" not in text, f"{role}: raw placeholder leaked"
        for fragment in _EXPECTED_SINK_FRAGMENTS[role]:
            assert fragment in text, (
                f"{role}: expected framework-default sink fragment {fragment!r} "
                "in standalone render (AC-27)"
            )
