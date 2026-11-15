"""viz-report HTML must escape event-derived text (XSS hardening)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "viz-report.py"


def test_render_html_escapes_event_text():
    spec = importlib.util.spec_from_file_location("viz_report_escape", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    payload = "<script>alert(1)</script>"
    events = [
        {"ts": "2026-01-01T00:00:00Z", "event": "log", "agent": "a",
         "payload": {"level": "info", "message": payload}},
    ]
    out = mod.render_html(events)
    assert payload not in out
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in out
